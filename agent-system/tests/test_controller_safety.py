"""Regression tests for bounded controller safety."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import completion_loop as cl


@pytest.fixture
def context(tmp_path, monkeypatch):
    story = "3-9-story"
    dep = "3-4-dependency"
    stories = tmp_path / "_bmad-output" / "implementation-artifacts"
    stories.mkdir(parents=True)
    story_path = stories / (story + ".md")
    story_path.write_text("# Story\nPREREQUISITES: Story 3.4\n")
    status_path = stories / "sprint-status.yaml"
    status_path.write_text(yaml.safe_dump({"development_status": {
        story: {"status": "ready-for-dev", "loop_eligible": True},
        dep: {"status": "done", "loop_eligible": False},
    }}))
    policy = tmp_path / "policy.yaml"
    policy.write_text(yaml.safe_dump({"max_repair_attempts": 2,
        "targets": {"test": {"stories": [story]}}}))
    for name, value in {
        "ROOT": tmp_path, "STORY_DIR": stories, "STATUS_PATH": status_path,
        "POLICY_PATH": policy, "RUNTIME_DIR": tmp_path,
        "STATE_PATH": tmp_path / "state.json",
        "REVIEW_FINDINGS": tmp_path / "findings.md",
        "REPAIR_PROMPT": tmp_path / "repair.md",
    }.items():
        monkeypatch.setattr(cl, name, value)
    monkeypatch.setattr(cl.hl, "load_status",
        lambda: yaml.safe_load(status_path.read_text()))
    cl.REVIEW_FINDINGS.write_text("Fix the finding")
    cl.REPAIR_PROMPT.write_text("Repair")
    state = cl.CompletionState(story, "test", "repair_required", branch="loop/story")
    packet = SimpleNamespace(story_id=story, branch=state.branch,
        story_path=story_path.relative_to(tmp_path).as_posix(),
        dependencies=(dep,), status_file_sha256=cl.hl.sha256(status_path),
        story_file_sha256=cl.hl.sha256(story_path), base_commit_sha="a"*40)
    cl.save_state(state)
    monkeypatch.setattr(cl, "_ensure_story_branch_ready", lambda *a, **k: None)
    monkeypatch.setattr(cl, "_read_execution_packet", lambda: packet)
    monkeypatch.setattr(cl.hl, "verify_story_untouched", lambda p: (
        None if cl.hl.sha256(story_path) == p.story_file_sha256 else
        (_ for _ in ()).throw(cl.hl.LoopError("Story changed"))))
    monkeypatch.setattr(cl.hl, "git", lambda *a: "a"*40)
    monkeypatch.setattr(cl.hl, "changed_paths", lambda *a: ["backend/example.py"])
    monkeypatch.setattr(cl.hl, "uncommitted_paths", lambda: [])
    return state, packet, status_path, story_path


def test_failed_workers_consume_persisted_budget(context, monkeypatch):
    runner = Mock(return_value=SimpleNamespace(returncode=1))
    monkeypatch.setattr(cl.hl, "run_command", runner)
    for expected in (1, 2):
        with pytest.raises(cl.CompletionError, match="exited"):
            cl.repair()
        assert cl.load_state().repair_attempts == expected
    with pytest.raises(cl.CompletionError, match="budget exhausted"):
        cl.repair()
    assert runner.call_count == 2


def test_launch_exception_consumes_budget(context, monkeypatch):
    monkeypatch.setattr(cl.hl, "run_command", Mock(side_effect=OSError("launch")))
    with pytest.raises(OSError):
        cl.repair()
    assert cl.load_state().repair_attempts == 1


@pytest.mark.parametrize("field,value", [("status", "backlog"), ("loop_eligible", False)])
def test_revoked_authority_blocks_worker(context, monkeypatch, field, value):
    state, packet, status_path, _ = context
    data = yaml.safe_load(status_path.read_text())
    data["development_status"][state.story_id][field] = value
    status_path.write_text(yaml.safe_dump(data))
    runner = Mock()
    monkeypatch.setattr(cl.hl, "run_command", runner)
    with pytest.raises(cl.CompletionError, match="Canonical"):
        cl.repair()
    runner.assert_not_called()


def test_stale_ledger_hash_blocks_repair(context, monkeypatch):
    _, _, status_path, _ = context
    status_path.write_text(status_path.read_text() + "\n# changed\n")
    with pytest.raises(cl.CompletionError, match="ledger changed"):
        cl.repair()


def test_changed_story_blocks_repair(context):
    _, _, _, story_path = context
    story_path.write_text("# Changed contract\nPREREQUISITES: Story 3.4\n")
    with pytest.raises(cl.hl.LoopError, match="Story changed"):
        cl.repair()


def test_protected_diff_blocks_repair(context, monkeypatch):
    monkeypatch.setattr(cl.hl, "changed_paths", lambda *a: ["AGENTS.md"])
    with pytest.raises(cl.hl.LoopError, match="protected"):
        cl.repair()


def test_missing_ready_spec_requires_supervision(context):
    state, _, _, story_path = context
    story_path.unlink()
    decision = cl.decide_next("test")
    assert decision.action == "SPEC_REQUIRED"
    assert decision.lane == "supervised"


@pytest.mark.parametrize("windows", [False, True])
def test_repair_uses_platform_launcher(context, monkeypatch, windows):
    expected = cl.hl.codex_exec_command(windows=windows)
    monkeypatch.setattr(cl.hl, "codex_exec_command", lambda: expected)
    runner = Mock(return_value=SimpleNamespace(returncode=1))
    monkeypatch.setattr(cl.hl, "run_command", runner)
    with pytest.raises(cl.CompletionError):
        cl.repair()
    assert runner.call_args.args[0] == expected


@pytest.mark.parametrize("value", [3, -1, True])
def test_policy_cannot_widen_two_attempt_limit(context, value):
    data = yaml.safe_load(cl.POLICY_PATH.read_text())
    data["max_repair_attempts"] = value
    cl.POLICY_PATH.write_text(yaml.safe_dump(data))
    with pytest.raises(cl.CompletionError):
        cl.max_repair_attempts()


def test_publish_rechecks_authority_after_validation(context, monkeypatch):
    state, packet, status_path, _ = context
    state.phase = "publish_ready"
    state.reviewed_commit_sha = "a"*40
    cl.save_state(state)
    monkeypatch.setattr(cl.shutil, "which", lambda _: "/mock")
    def validate():
        status_path.write_text(status_path.read_text() + "\n# changed\n")
        return {"success": True}
    monkeypatch.setattr(cl.hl, "run_validation", validate)
    git = Mock(return_value="a"*40)
    monkeypatch.setattr(cl.hl, "git", git)
    with pytest.raises(cl.CompletionError, match="ledger changed"):
        cl.publish()
    assert not any(call.args[0] == "push" for call in git.call_args_list)
