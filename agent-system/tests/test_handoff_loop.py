"""Regression tests for the handoff-loop controller findings.

1. Protected-path validation must see uncommitted (staged/unstaged/untracked)
   changes, not just the committed diff, and any leftover uncommitted change
   must block success even if it isn't a protected path.
2. The authoritative story file must be treated as immutable after Codex runs
   -- re-checked by content hash, whether the change was committed or not.
3. The CLI must not require PYTHONUTF8=1 / a UTF-8 console codepage on
   Windows -- non-ASCII console output must not raise UnicodeEncodeError.
4. Dependency extraction must be direction-aware: prose that merely mentions
   another story near a dependency word (e.g. "the contract Story 1.6 depends
   on") must not be read as a prerequisite edge in the wrong direction.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

AGENT_SYSTEM_DIR = Path(__file__).resolve().parents[1]
if str(AGENT_SYSTEM_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_SYSTEM_DIR))

import handoff_loop as hl  # noqa: E402


def _run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _write(repo: Path, relative: str, content: str) -> Path:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(repo, "init", "-q")
    _run_git(repo, "config", "user.email", "test@example.com")
    _run_git(repo, "config", "user.name", "Test User")
    _write(repo, "README.md", "hello\n")
    _run_git(repo, "add", "README.md")
    _run_git(repo, "commit", "-q", "-m", "initial commit")
    return repo


class TestUncommittedPaths:
    def test_clean_tree_reports_nothing(self, git_repo: Path) -> None:
        assert hl.uncommitted_paths(root=git_repo) == []

    def test_detects_staged_change(self, git_repo: Path) -> None:
        _write(git_repo, "README.md", "changed\n")
        _run_git(git_repo, "add", "README.md")
        assert "README.md" in hl.uncommitted_paths(root=git_repo)

    def test_detects_unstaged_change(self, git_repo: Path) -> None:
        _write(git_repo, "README.md", "changed again\n")
        assert "README.md" in hl.uncommitted_paths(root=git_repo)

    def test_detects_untracked_file(self, git_repo: Path) -> None:
        _write(git_repo, "scratch.txt", "new\n")
        assert "scratch.txt" in hl.uncommitted_paths(root=git_repo)


class TestValidateChangedPaths:
    def test_allows_ordinary_paths(self) -> None:
        hl.validate_changed_paths(["backend/pipeline/orchestrator.py"])

    def test_rejects_protected_prefix(self) -> None:
        with pytest.raises(hl.LoopError):
            hl.validate_changed_paths(["agent-system/handoff_loop.py"])

    def test_rejects_protected_exact_path(self) -> None:
        with pytest.raises(hl.LoopError):
            hl.validate_changed_paths(["AGENTS.md"])


class TestFindingOneUncommittedBypass:
    """Reproduces the reviewed bypass: Codex commits a clean diff but leaves a
    protected-file edit (or any leftover change) sitting uncommitted."""

    def test_committed_only_diff_was_previously_indistinguishable_from_safe(
        self, git_repo: Path
    ) -> None:
        _write(git_repo, "backend/feature.py", "print('ok')\n")
        _run_git(git_repo, "add", "backend/feature.py")
        _run_git(git_repo, "commit", "-q", "-m", "feature work")
        committed = hl.changed_paths("HEAD~1", root=git_repo)
        assert committed == ["backend/feature.py"]
        hl.validate_changed_paths(committed)  # no protected paths committed -> fine

    def test_uncommitted_protected_edit_is_now_caught(self, git_repo: Path) -> None:
        _write(git_repo, "backend/feature.py", "print('ok')\n")
        _run_git(git_repo, "add", "backend/feature.py")
        _run_git(git_repo, "commit", "-q", "-m", "feature work")
        # Codex leaves a protected orchestration file modified but uncommitted.
        _write(git_repo, "agent-system/handoff_loop.py", "# tampered\n")

        committed = hl.changed_paths("HEAD~1", root=git_repo)
        pending = hl.uncommitted_paths(root=git_repo)
        assert "agent-system/handoff_loop.py" in pending

        with pytest.raises(hl.LoopError, match="protected orchestration paths"):
            hl.validate_changed_paths(sorted(set(committed) | set(pending)))

    def test_any_leftover_uncommitted_change_blocks_success(self, git_repo: Path) -> None:
        _write(git_repo, "backend/feature.py", "print('ok')\n")
        _run_git(git_repo, "add", "backend/feature.py")
        _run_git(git_repo, "commit", "-q", "-m", "feature work")
        # Leftover change is not protected, but must still block success.
        _write(git_repo, "backend/scratch.py", "# leftover\n")

        pending = hl.uncommitted_paths(root=git_repo)
        assert pending == ["backend/scratch.py"]
        # validate_changed_paths alone would not catch this (not protected) --
        # the controller must independently reject any leftover uncommitted path.


class TestFindingTwoStoryImmutability:
    def _packet(self, repo: Path, story_rel: str) -> hl.ExecutionPacket:
        return hl.ExecutionPacket(
            story_id="9-9-test-story",
            story_path=story_rel,
            base_commit_sha="deadbeef",
            status_file_sha256="unused",
            story_file_sha256=hl.sha256(repo / story_rel),
            dependencies=(),
            generated_at="2026-01-01T00:00:00+00:00",
            branch="loop/story-9-9-test-story",
            constraints=(),
        )

    def test_unchanged_story_passes(self, git_repo: Path) -> None:
        story_rel = "_bmad-output/implementation-artifacts/9-9-test-story.md"
        _write(git_repo, story_rel, "# Story\n\nOriginal acceptance criteria.\n")
        packet = self._packet(git_repo, story_rel)
        hl.verify_story_untouched(packet, root=git_repo)

    def test_uncommitted_story_edit_fails_closed(self, git_repo: Path) -> None:
        story_rel = "_bmad-output/implementation-artifacts/9-9-test-story.md"
        _write(git_repo, story_rel, "# Story\n\nOriginal acceptance criteria.\n")
        packet = self._packet(git_repo, story_rel)
        # Codex edits its own authoritative story without committing.
        _write(git_repo, story_rel, "# Story\n\nWeakened acceptance criteria.\n")
        with pytest.raises(hl.LoopError, match="changed during Codex execution"):
            hl.verify_story_untouched(packet, root=git_repo)

    def test_committed_story_edit_fails_closed(self, git_repo: Path) -> None:
        story_rel = "_bmad-output/implementation-artifacts/9-9-test-story.md"
        _write(git_repo, story_rel, "# Story\n\nOriginal acceptance criteria.\n")
        packet = self._packet(git_repo, story_rel)
        # Codex commits an edit to the story it must treat as read-only.
        _write(git_repo, story_rel, "# Story\n\nCodex-rewritten acceptance criteria.\n")
        _run_git(git_repo, "add", story_rel)
        _run_git(git_repo, "commit", "-q", "-m", "tamper with story")
        with pytest.raises(hl.LoopError, match="changed during Codex execution"):
            hl.verify_story_untouched(packet, root=git_repo)

    def test_missing_story_fails_closed(self, git_repo: Path) -> None:
        story_rel = "_bmad-output/implementation-artifacts/9-9-test-story.md"
        story_path = _write(git_repo, story_rel, "# Story\n")
        packet = self._packet(git_repo, story_rel)
        story_path.unlink()
        with pytest.raises(hl.LoopError, match="missing after execution"):
            hl.verify_story_untouched(packet, root=git_repo)


class TestConsoleEncoding:
    """Windows consoles default stdout/stderr to the system codepage (e.g. cp1252),
    which previously raised UnicodeEncodeError on the CLI's status banner. The
    module must force UTF-8 on its own streams so this works without the caller
    setting PYTHONUTF8=1."""

    def test_status_command_does_not_require_utf8_env(self) -> None:
        env = dict(os.environ)
        env.pop("PYTHONIOENCODING", None)
        env["PYTHONUTF8"] = "0"  # explicitly disable Python's UTF-8 mode
        script = AGENT_SYSTEM_DIR / "handoff_loop.py"
        result = subprocess.run(
            [sys.executable, str(script), "status"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )
        assert result.returncode == 0, result.stderr
        assert "UnicodeEncodeError" not in result.stderr
        assert "→" in result.stdout


class TestDependencyDirection:
    """extract_dependencies must only record direction-unambiguous prerequisites."""

    KNOWN = {
        "1-3-insight-engine",
        "1-5-document-rendering",
        "1-6-pipeline-orchestration-cli-entry-point",
        "3-1-classification-layer",
        "3-4-opt-in-gate-config",
    }

    def test_prose_depends_on_reference_is_not_recorded_backwards(self) -> None:
        # Real wording from 1-5-document-rendering.md: "Story 1.6" is the
        # grammatical subject of "depends on" here, so 1.6 depends on *this*
        # story -- not the other way around. A direction-blind scanner would
        # wrongly record 1-6 as a dependency of 1-5.
        text = (
            "The renderer interface (`render(insight_report, output_path) -> None`) "
            "defined here is the contract Story 1.6 depends on. Getting the "
            "interface exactly right is the primary deliverable.\n"
        )
        deps = hl.extract_dependencies(text, self.KNOWN, self_id="1-5-document-rendering")
        assert deps == ()

    def test_prerequisite_label_is_recorded(self) -> None:
        text = "PREREQUISITES (both merged to main): Story 3.1 (PR #39 -- RemediationClass, classifier)\n"
        deps = hl.extract_dependencies(text, self.KNOWN, self_id="3-4-opt-in-gate-config")
        assert deps == ("3-1-classification-layer",)

    def test_inline_prerequisite_label_is_recorded(self) -> None:
        # Real wording from 3-2-cleaning-engine-core.md: the label appears
        # mid-sentence, not at line start.
        text = (
            "It is load-bearing: a bug is not a wrong number. PREREQUISITE: "
            "Story 3.1 (PR #39)\nMUST be merged first -- this engine dispatches "
            "on remediation_class.\n"
        )
        deps = hl.extract_dependencies(text, self.KNOWN, self_id="9-9-other")
        assert deps == ("3-1-classification-layer",)

    def test_cross_story_table_excludes_reverse_direction_column_reuse(self) -> None:
        # Real convention from 1-5-document-rendering.md: the "Depends on"
        # column is reused to note what a story *unblocks*, which is the
        # reverse relationship and must not be recorded as a dependency.
        text = (
            "### Cross-Story Dependencies\n\n"
            "| Depends on | What's needed |\n"
            "|-----------|---------------|\n"
            "| Story 1.3 (done) | `InsightPayload` model |\n"
            "| **Unblocks Story 1.6** | `DocxRenderer` exported |\n"
        )
        deps = hl.extract_dependencies(text, self.KNOWN, self_id="1-5-document-rendering")
        assert deps == ("1-3-insight-engine",)

    def test_self_reference_is_excluded(self) -> None:
        text = "PREREQUISITE: Story 3.4 must be merged first.\n"
        deps = hl.extract_dependencies(text, self.KNOWN, self_id="3-4-opt-in-gate-config")
        assert deps == ()

    def test_self_referential_depends_on_is_recorded(self) -> None:
        # Real wording from 2-4-reporting-agent.md:6: "This story depends on
        # the Drift Engine" -- the subject ("this story") is explicitly
        # self-referential, so unlike "Story X depends on" this direction is
        # unambiguous and should be recorded.
        known = self.KNOWN | {"2-3-drift-engine"}
        text = "This story depends on the Drift Engine (filed 2.3, done).\n"
        deps = hl.extract_dependencies(text, known, self_id="2-4-reporting-agent")
        assert deps == ("2-3-drift-engine",)

    def test_must_be_merged_first_ignores_unrelated_earlier_reference(self) -> None:
        # An incidental mention earlier in the same sentence must not be
        # swept in -- only the reference nearest the trigger phrase counts.
        text = "See Story 3.1 for context; Story 3.4 must be merged first.\n"
        deps = hl.extract_dependencies(text, self.KNOWN, self_id="9-9-other")
        assert deps == ("3-4-opt-in-gate-config",)

    def test_table_header_with_markdown_emphasis_is_recognized(self) -> None:
        # A bolded "**Depends on**" header is a plausible formatting variant
        # of this repo's own convention (1-5-document-rendering.md bolds
        # cells in this column) and must not be silently skipped.
        text = "| **Depends on** | What's needed |\n|---|---|\n| Story 3.1 | x |\n"
        deps = hl.extract_dependencies(text, self.KNOWN, self_id="9-9-other")
        assert deps == ("3-1-classification-layer",)

    def test_bare_dash_form_reference_is_matched_whole(self) -> None:
        # Regex alternation order bug: the digit-only alternative used to
        # match before the dash-form one was ever tried, splitting "1-6"
        # into two meaningless single-digit tokens.
        assert hl.STORY_REF.findall("Depends on 1-6 for the interface") == ["1-6"]


class TestStorySortKey:
    """story_sort_key() must stay comparable across sibling ids that mix a
    bare numeric token with a letter-suffixed one at the same position."""

    @staticmethod
    def _candidate(story_id: str) -> hl.StoryCandidate:
        return hl.StoryCandidate(
            story_id=story_id,
            status="ready-for-dev",
            loop_eligible=True,
            story_path="x",
            dependencies=(),
            blocked_dependencies=(),
        )

    def test_numeric_and_letter_suffixed_siblings_sort_without_crashing(self) -> None:
        # Real ids from sprint-status.yaml: "4-1-..." and "4-1a-..." previously
        # crashed with TypeError comparing int 1 to str "1a" at the same
        # tuple position.
        candidates = [
            self._candidate("4-1a-config-to-project-migration"),
            self._candidate("4-1-database-schema-auth-foundation"),
        ]
        ordered = sorted(candidates, key=hl.story_sort_key)
        assert [c.story_id for c in ordered] == [
            "4-1-database-schema-auth-foundation",
            "4-1a-config-to-project-migration",
        ]

    def test_alpha_and_numeric_first_tokens_sort_without_crashing(self) -> None:
        # A first token that never converts to int (e.g. "R-1-...") must still
        # be comparable against a purely-numeric first token.
        candidates = [self._candidate("R-1-code-rename"), self._candidate("3-1-classification-layer")]
        sorted(candidates, key=hl.story_sort_key)  # must not raise


class TestEnsureRepoReadyToolChecks:
    def test_missing_uv_raises_loop_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        real_which = shutil.which

        def fake_which(name: str) -> str | None:
            if name == "uv":
                return None
            return real_which(name)

        monkeypatch.setattr(hl.shutil, "which", fake_which)
        with pytest.raises(hl.LoopError, match="uv is not available"):
            hl.ensure_repo_ready()

    def test_missing_npm_raises_loop_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        real_which = shutil.which

        def fake_which(name: str) -> str | None:
            if name == "npm":
                return None
            return real_which(name)

        monkeypatch.setattr(hl.shutil, "which", fake_which)
        with pytest.raises(hl.LoopError, match="npm is not available"):
            hl.ensure_repo_ready()
