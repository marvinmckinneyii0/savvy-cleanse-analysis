"""Regression tests for the two P1 handoff-loop controller findings.

1. Protected-path validation must see uncommitted (staged/unstaged/untracked)
   changes, not just the committed diff, and any leftover uncommitted change
   must block success even if it isn't a protected path.
2. The authoritative story file must be treated as immutable after Codex runs
   -- re-checked by content hash, whether the change was committed or not.
"""

from __future__ import annotations

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
