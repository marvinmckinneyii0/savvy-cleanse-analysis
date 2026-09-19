"""Regression tests for the project-level SAINT completion controller."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

AGENT_SYSTEM_DIR = Path(__file__).resolve().parents[1]
if str(AGENT_SYSTEM_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_SYSTEM_DIR))

import completion_loop as cl  # noqa: E402


def _entry(status: str, loop_eligible: bool) -> dict[str, object]:
    return {"status": status, "loop_eligible": loop_eligible}


def _status(**entries: dict[str, object]) -> dict[str, object]:
    return {"development_status": entries}


def _policy(stories: list[str], *, repairs: int = 2) -> dict[str, object]:
    return {
        "default_target": "test-target",
        "max_repair_attempts": repairs,
        "targets": {"test-target": {"stories": stories}},
    }


@pytest.fixture()
def story_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "repo"
    stories = root / "_bmad-output" / "implementation-artifacts"
    stories.mkdir(parents=True)
    monkeypatch.setattr(cl, "ROOT", root)
    monkeypatch.setattr(cl, "STORY_DIR", stories)
    return root


def _write_story(root: Path, story_id: str, text: str = "# Story\n") -> Path:
    path = root / "_bmad-output" / "implementation-artifacts" / f"{story_id}.md"
    path.write_text(text, encoding="utf-8")
    return path


class TestDecisionStateMachine:
    def test_configured_target_order_overrides_ledger_order(self, story_root: Path) -> None:
        # The real Epic 3 ledger lists 3.7/3.8 before 3.9, while the recorded
        # closeout sequence explicitly says 3.9 -> 3.7 -> 3.8.
        data = _status(
            **{
                "3-7-report-visualizations": _entry("backlog", False),
                "3-8-notebook-export-code-generation": _entry("backlog", False),
                "3-9-cleaning-mode-definitions-disclosure": _entry("backlog", True),
            }
        )
        policy = _policy(
            [
                "3-9-cleaning-mode-definitions-disclosure",
                "3-7-report-visualizations",
                "3-8-notebook-export-code-generation",
            ]
        )
        decision = cl.decide_next("test-target", status_data=data, policy=policy)
        assert decision.story_id == "3-9-cleaning-mode-definitions-disclosure"
        assert decision.action == "SPEC_REQUIRED"
        assert decision.lane == "supervised"

    def test_backlog_story_with_spec_requires_human_status_promotion(self, story_root: Path) -> None:
        story = "3-9-cleaning-mode-definitions-disclosure"
        _write_story(story_root, story)
        data = _status(**{story: _entry("backlog", True)})
        decision = cl.decide_next("test-target", status_data=data, policy=_policy([story]))
        assert decision.action == "STATUS_PROMOTION_REQUIRED"
        assert decision.lane == "supervised"

    def test_ready_loop_eligible_story_dispatches_autonomously(self, story_root: Path) -> None:
        story = "3-9-cleaning-mode-definitions-disclosure"
        _write_story(story_root, story)
        data = _status(**{story: _entry("ready-for-dev", True)})
        decision = cl.decide_next("test-target", status_data=data, policy=_policy([story]))
        assert decision.action == "DISPATCH_AUTONOMOUS"
        assert decision.lane == "autonomous"

    def test_ready_noneligible_story_stays_supervised(self, story_root: Path) -> None:
        story = "3-7-report-visualizations"
        _write_story(story_root, story)
        data = _status(**{story: _entry("ready-for-dev", False)})
        decision = cl.decide_next("test-target", status_data=data, policy=_policy([story]))
        assert decision.action == "SUPERVISED_IMPLEMENTATION"
        assert decision.lane == "supervised"

    def test_done_story_advances_to_next_target_story(self, story_root: Path) -> None:
        first = "3-9-cleaning-mode-definitions-disclosure"
        second = "3-7-report-visualizations"
        data = _status(**{first: _entry("done", True), second: _entry("backlog", False)})
        decision = cl.decide_next(
            "test-target", status_data=data, policy=_policy([first, second])
        )
        assert decision.story_id == second
        assert decision.action == "SPEC_REQUIRED"

    def test_explicit_unfinished_dependency_blocks_dispatch(self, story_root: Path) -> None:
        dep = "3-1-classification-layer"
        story = "3-9-cleaning-mode-definitions-disclosure"
        _write_story(story_root, story, "# Story\n\nPREREQUISITE: Story 3.1 must be merged first.\n")
        data = _status(**{dep: _entry("backlog", False), story: _entry("ready-for-dev", True)})
        decision = cl.decide_next("test-target", status_data=data, policy=_policy([story]))
        assert decision.action == "BLOCKED_DEPENDENCY"
        assert decision.blocked_dependencies == (dep,)

    def test_all_done_reports_target_complete(self, story_root: Path) -> None:
        story = "3-9-cleaning-mode-definitions-disclosure"
        data = _status(**{story: _entry("done", True)})
        decision = cl.decide_next("test-target", status_data=data, policy=_policy([story]))
        assert decision.action == "TARGET_COMPLETE"
        assert decision.story_id is None

    def test_unknown_story_in_policy_fails_closed(self, story_root: Path) -> None:
        with pytest.raises(cl.CompletionError, match="unknown stories"):
            cl.decide_next(
                "test-target",
                status_data=_status(**{"3-1-known": _entry("done", False)}),
                policy=_policy(["9-9-missing"]),
            )


@pytest.fixture()
def runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    runtime_dir = tmp_path / ".agent-handoff"
    policy_path = tmp_path / "completion-policy.yaml"
    policy_path.write_text(yaml.safe_dump(_policy(["3-9-story"])), encoding="utf-8")
    monkeypatch.setattr(cl, "RUNTIME_DIR", runtime_dir)
    monkeypatch.setattr(cl, "STATE_PATH", runtime_dir / "completion-state.json")
    monkeypatch.setattr(cl, "REVIEW_FINDINGS", runtime_dir / "review-findings.md")
    monkeypatch.setattr(cl, "POLICY_PATH", policy_path)
    return runtime_dir


class TestReviewRepairGate:
    def _state(self, runtime: Path, *, repairs: int = 0) -> cl.CompletionState:
        state = cl.CompletionState(
            story_id="3-9-story",
            target="test-target",
            phase="review_required",
            branch="loop/story-3-9-story",
            repair_attempts=repairs,
        )
        cl.save_state(state)
        return state

    def test_review_pass_is_required_before_publish(self, runtime: Path) -> None:
        self._state(runtime)
        state = cl.record_review("pass", None)
        assert state.phase == "publish_ready"
        saved = json.loads((runtime / "completion-state.json").read_text(encoding="utf-8"))
        assert saved["phase"] == "publish_ready"

    def test_review_changes_records_findings_and_enters_repair(self, runtime: Path, tmp_path: Path) -> None:
        self._state(runtime)
        findings = tmp_path / "findings.md"
        findings.write_text("- High: boundary regression\n", encoding="utf-8")
        state = cl.record_review("changes", str(findings))
        assert state.phase == "repair_required"
        assert (runtime / "review-findings.md").read_text(encoding="utf-8") == findings.read_text(
            encoding="utf-8"
        )

    def test_repair_budget_exhaustion_halts(self, runtime: Path) -> None:
        self._state(runtime, repairs=2)
        with pytest.raises(cl.CompletionError, match="Repair budget exhausted"):
            cl.record_review("changes", __file__)
        state = cl.load_state()
        assert state is not None
        assert state.phase == "halted_repair_budget_exhausted"

    def test_changes_requires_findings_file(self, runtime: Path) -> None:
        self._state(runtime)
        with pytest.raises(cl.CompletionError, match="findings-file"):
            cl.record_review("changes", None)

    def test_publish_without_review_state_fails_closed(self, runtime: Path) -> None:
        with pytest.raises(cl.CompletionError, match="passed independent review"):
            cl.publish()
