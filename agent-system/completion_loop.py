#!/usr/bin/env python3
"""Project-level completion controller for SAINT.

This wraps the existing one-story Claude -> Codex handoff without weakening it.
It decides the next project action, prepares spec/review packets, dispatches only
already-approved loop-eligible stories, allows at most two bounded repair passes,
and publishes reviewed work as a draft PR. It never merges and never changes
``loop_eligible`` or promotes backlog stories by itself.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

import handoff_loop as hl

ROOT = hl.ROOT
STATUS_PATH = hl.STATUS_PATH
STORY_DIR = hl.STORY_DIR
RUNTIME_DIR = hl.RUNTIME_DIR
POLICY_PATH = ROOT / "agent-system" / "completion-policy.yaml"
STORY_PLANNER_PROMPT = ROOT / "agent-system" / "prompts" / "story-planner.md"
REVIEWER_PROMPT = ROOT / "agent-system" / "prompts" / "reviewer.md"
REPAIR_PROMPT = ROOT / "agent-system" / "prompts" / "repair-worker.md"
STATE_PATH = RUNTIME_DIR / "completion-state.json"
SPEC_PACKET = RUNTIME_DIR / "spec-prompt.md"
REVIEW_PACKET = RUNTIME_DIR / "review-prompt.md"
REVIEW_FINDINGS = RUNTIME_DIR / "review-findings.md"
PR_BODY = RUNTIME_DIR / "pr-body.md"

DONE_STATUS = "done"
BACKLOG_STATUS = "backlog"
READY_STATUS = "ready-for-dev"
ACTIVE_STATUSES = {"in-progress", "review", "blocked-needs-review"}


class CompletionError(RuntimeError):
    """Expected, user-actionable completion-loop failure."""


@dataclass(frozen=True)
class CompletionDecision:
    target: str
    story_id: str | None
    status: str | None
    loop_eligible: bool | None
    action: str
    lane: str
    story_path: str | None
    dependencies: tuple[str, ...]
    blocked_dependencies: tuple[str, ...]
    reason: str


@dataclass
class CompletionState:
    story_id: str
    target: str
    phase: str
    branch: str | None = None
    repair_attempts: int = 0
    updated_at: str = ""

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()


def load_policy() -> dict[str, Any]:
    if not POLICY_PATH.exists():
        raise CompletionError(f"Missing completion policy: {POLICY_PATH}")
    data = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CompletionError("completion-policy.yaml must contain a mapping")
    return data


def load_state() -> CompletionState | None:
    if not STATE_PATH.exists():
        return None
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return CompletionState(**data)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CompletionError(f"Invalid completion state: {STATE_PATH}: {exc}") from exc


def save_state(state: CompletionState) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    state.touch()
    STATE_PATH.write_text(json.dumps(asdict(state), indent=2) + "\n", encoding="utf-8")


def story_entries(status_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return hl.story_entries(status_data)


def _target_story_ids(
    target: str,
    *,
    status_data: dict[str, Any],
    policy: dict[str, Any],
) -> list[str]:
    entries = story_entries(status_data)
    targets = policy.get("targets", {})
    configured = targets.get(target) if isinstance(targets, dict) else None
    if isinstance(configured, dict):
        stories = configured.get("stories")
        if isinstance(stories, list) and stories:
            unknown = [str(item) for item in stories if str(item) not in entries]
            if unknown:
                raise CompletionError(
                    f"Target {target!r} references unknown stories: {', '.join(unknown)}"
                )
            return [str(item) for item in stories]

    if target == "all":
        return list(entries)

    epic_match = re.fullmatch(r"epic-(\d+)", target)
    if epic_match:
        prefix = epic_match.group(1) + "-"
        stories = [story_id for story_id in entries if story_id.startswith(prefix)]
        if not stories:
            raise CompletionError(f"No stories found for {target}")
        return stories

    if target in entries:
        return [target]

    raise CompletionError(f"Unknown completion target: {target}")


def _story_file(story_id: str) -> Path | None:
    matches = sorted(STORY_DIR.glob(f"{story_id}*.md"))
    if not matches:
        return None
    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise CompletionError(f"Ambiguous story files for {story_id}: {names}")
    return matches[0]


def decide_next(
    target: str,
    *,
    status_data: dict[str, Any] | None = None,
    policy: dict[str, Any] | None = None,
) -> CompletionDecision:
    status_data = status_data or hl.load_status()
    policy = policy or load_policy()
    entries = story_entries(status_data)
    story_ids = _target_story_ids(target, status_data=status_data, policy=policy)
    known_ids = set(entries)

    for story_id in story_ids:
        metadata = entries[story_id]
        status = str(metadata.get("status"))
        if status == DONE_STATUS:
            continue

        loop_eligible = metadata.get("loop_eligible") is True
        story_path = _story_file(story_id)
        dependencies: tuple[str, ...] = ()
        blocked_dependencies: tuple[str, ...] = ()
        if story_path is not None:
            dependencies = hl.extract_dependencies(
                story_path.read_text(encoding="utf-8"), known_ids, self_id=story_id
            )
            blocked_dependencies = tuple(
                dep for dep in dependencies if entries.get(dep, {}).get("status") != DONE_STATUS
            )

        relative_story_path = (
            str(story_path.relative_to(ROOT).as_posix()) if story_path is not None else None
        )

        if blocked_dependencies:
            return CompletionDecision(
                target=target,
                story_id=story_id,
                status=status,
                loop_eligible=loop_eligible,
                action="BLOCKED_DEPENDENCY",
                lane="halt",
                story_path=relative_story_path,
                dependencies=dependencies,
                blocked_dependencies=blocked_dependencies,
                reason="Upstream dependencies are not done.",
            )

        if status == BACKLOG_STATUS:
            if story_path is None:
                return CompletionDecision(
                    target=target,
                    story_id=story_id,
                    status=status,
                    loop_eligible=loop_eligible,
                    action="SPEC_REQUIRED",
                    lane="supervised",
                    story_path=None,
                    dependencies=(),
                    blocked_dependencies=(),
                    reason="No authoritative BMAD story file exists yet.",
                )
            return CompletionDecision(
                target=target,
                story_id=story_id,
                status=status,
                loop_eligible=loop_eligible,
                action="STATUS_PROMOTION_REQUIRED",
                lane="supervised",
                story_path=relative_story_path,
                dependencies=dependencies,
                blocked_dependencies=(),
                reason="The story spec exists, but only a human/controller may promote backlog to ready-for-dev.",
            )

        if status == READY_STATUS:
            if loop_eligible:
                return CompletionDecision(
                    target=target,
                    story_id=story_id,
                    status=status,
                    loop_eligible=True,
                    action="DISPATCH_AUTONOMOUS",
                    lane="autonomous",
                    story_path=relative_story_path,
                    dependencies=dependencies,
                    blocked_dependencies=(),
                    reason="Approved, dependency-clear, and loop-eligible.",
                )
            return CompletionDecision(
                target=target,
                story_id=story_id,
                status=status,
                loop_eligible=False,
                action="SUPERVISED_IMPLEMENTATION",
                lane="supervised",
                story_path=relative_story_path,
                dependencies=dependencies,
                blocked_dependencies=(),
                reason="Story is ready, but loop_eligible is false.",
            )

        if status in ACTIVE_STATUSES:
            return CompletionDecision(
                target=target,
                story_id=story_id,
                status=status,
                loop_eligible=loop_eligible,
                action="HUMAN_CHECKPOINT",
                lane="supervised",
                story_path=relative_story_path,
                dependencies=dependencies,
                blocked_dependencies=(),
                reason=f"Story is already in {status!r}; reconcile that work before starting another story.",
            )

        return CompletionDecision(
            target=target,
            story_id=story_id,
            status=status,
            loop_eligible=loop_eligible,
            action="UNKNOWN_STATUS",
            lane="halt",
            story_path=relative_story_path,
            dependencies=dependencies,
            blocked_dependencies=(),
            reason=f"Unsupported story status: {status!r}.",
        )

    return CompletionDecision(
        target=target,
        story_id=None,
        status=None,
        loop_eligible=None,
        action="TARGET_COMPLETE",
        lane="complete",
        story_path=None,
        dependencies=(),
        blocked_dependencies=(),
        reason="Every story in the target is done.",
    )


def print_decision(decision: CompletionDecision) -> None:
    print("SAINT completion loop")
    print(f"Target: {decision.target}")
    print(f"Action: {decision.action}")
    print(f"Lane: {decision.lane}")
    if decision.story_id:
        print(f"Story: {decision.story_id}")
        print(f"Status: {decision.status}")
        print(f"Loop eligible: {str(decision.loop_eligible).lower()}")
    if decision.story_path:
        print(f"Story file: {decision.story_path}")
    if decision.dependencies:
        print("Dependencies: " + ", ".join(decision.dependencies))
    if decision.blocked_dependencies:
        print("Blocked by: " + ", ".join(decision.blocked_dependencies))
    print(f"Reason: {decision.reason}")


def prepare_spec_packet(decision: CompletionDecision) -> Path:
    if decision.action != "SPEC_REQUIRED" or not decision.story_id:
        raise CompletionError("prepare-spec is only valid when the next action is SPEC_REQUIRED")
    if not STORY_PLANNER_PROMPT.exists():
        raise CompletionError(f"Missing story planner prompt: {STORY_PLANNER_PROMPT}")
    status_data = hl.load_status()
    policy = load_policy()
    target_config = policy.get("targets", {}).get(decision.target, {})
    rendered = (
        STORY_PLANNER_PROMPT.read_text(encoding="utf-8")
        + "\n\n# Planning packet\n\n"
        + f"- target: `{decision.target}`\n"
        + f"- story: `{decision.story_id}`\n"
        + f"- current status: `{decision.status}`\n"
        + f"- loop_eligible (human-set, immutable here): `{decision.loop_eligible}`\n"
        + f"- target configuration: `{json.dumps(target_config, sort_keys=True)}`\n\n"
        + "## Canonical sprint-status snapshot\n\n"
        + "```yaml\n"
        + yaml.safe_dump(status_data, sort_keys=False)
        + "```\n"
    )
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    SPEC_PACKET.write_text(rendered, encoding="utf-8")
    return SPEC_PACKET


def _read_execution_packet() -> hl.ExecutionPacket:
    if not hl.CURRENT_PACKET.exists():
        raise CompletionError("No handoff execution packet exists")
    try:
        raw = json.loads(hl.CURRENT_PACKET.read_text(encoding="utf-8"))
        return hl.ExecutionPacket(**raw)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CompletionError(f"Invalid handoff execution packet: {exc}") from exc


def dispatch(decision: CompletionDecision) -> int:
    if decision.action != "DISPATCH_AUTONOMOUS" or not decision.story_id:
        raise CompletionError("run may dispatch only DISPATCH_AUTONOMOUS stories")
    candidate = hl.select_candidate(decision.story_id)
    result = hl.execute(candidate)
    if result == 0:
        packet = _read_execution_packet()
        state = CompletionState(
            story_id=decision.story_id,
            target=decision.target,
            phase="review_required",
            branch=packet.branch,
            repair_attempts=0,
        )
        save_state(state)
    return result


def prepare_review_packet() -> Path:
    state = load_state()
    if state is None or state.phase != "review_required":
        raise CompletionError("No implementation is currently awaiting review")
    if not REVIEWER_PROMPT.exists():
        raise CompletionError(f"Missing reviewer prompt: {REVIEWER_PROMPT}")
    packet = _read_execution_packet()
    if packet.story_id != state.story_id:
        raise CompletionError("Completion state and handoff packet refer to different stories")
    story_text = (ROOT / packet.story_path).read_text(encoding="utf-8")
    validation = (
        hl.VALIDATION_REPORT.read_text(encoding="utf-8")
        if hl.VALIDATION_REPORT.exists()
        else "{}"
    )
    diff = hl.git("diff", f"{packet.base_commit_sha}...HEAD")
    rendered = (
        REVIEWER_PROMPT.read_text(encoding="utf-8")
        + "\n\n# Review packet\n\n"
        + f"Story: `{state.story_id}`\n\n"
        + "## Authoritative story\n\n"
        + story_text
        + "\n\n## Validation report\n\n```json\n"
        + validation
        + "\n```\n\n## Diff\n\n```diff\n"
        + diff
        + "\n```\n"
    )
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_PACKET.write_text(rendered, encoding="utf-8")
    return REVIEW_PACKET


def max_repair_attempts() -> int:
    value = load_policy().get("max_repair_attempts", 2)
    if not isinstance(value, int) or value < 0:
        raise CompletionError("max_repair_attempts must be a non-negative integer")
    return value


def record_review(result: str, findings_file: str | None) -> CompletionState:
    state = load_state()
    if state is None or state.phase != "review_required":
        raise CompletionError("No implementation is currently awaiting review")
    if result == "pass":
        state.phase = "publish_ready"
        save_state(state)
        return state
    if result != "changes":
        raise CompletionError("Review result must be 'pass' or 'changes'")
    if state.repair_attempts >= max_repair_attempts():
        state.phase = "halted_repair_budget_exhausted"
        save_state(state)
        raise CompletionError("Repair budget exhausted; human architecture review required")
    if not findings_file:
        raise CompletionError("--findings-file is required when review result is 'changes'")
    source = Path(findings_file).expanduser().resolve()
    if not source.exists():
        raise CompletionError(f"Review findings file does not exist: {source}")
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_FINDINGS.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    state.phase = "repair_required"
    save_state(state)
    return state


def _ensure_story_branch_ready(
    state: CompletionState, *, executables: tuple[str, ...] = ("git", "uv", "npm")
) -> None:
    for executable in executables:
        if shutil.which(executable) is None:
            raise CompletionError(f"{executable} is not available on PATH")
    repo_root = Path(hl.git("rev-parse", "--show-toplevel")).resolve()
    if repo_root != ROOT:
        raise CompletionError(f"Expected repository root {ROOT}, found {repo_root}")
    branch = hl.git("branch", "--show-current")
    if state.branch is None or branch != state.branch:
        raise CompletionError(f"Expected story branch {state.branch!r}, found {branch!r}")
    pending = hl.uncommitted_paths()
    if pending:
        raise CompletionError("Working tree is not clean: " + ", ".join(sorted(pending)))


def repair() -> int:
    state = load_state()
    if state is None or state.phase != "repair_required":
        raise CompletionError("No reviewed implementation currently requires repair")
    if state.repair_attempts >= max_repair_attempts():
        state.phase = "halted_repair_budget_exhausted"
        save_state(state)
        raise CompletionError("Repair budget exhausted; human architecture review required")
    if not REVIEW_FINDINGS.exists():
        raise CompletionError("Review findings are missing")
    if not REPAIR_PROMPT.exists():
        raise CompletionError(f"Missing repair prompt: {REPAIR_PROMPT}")
    _ensure_story_branch_ready(state, executables=("git", "codex", "uv", "npm"))
    packet = _read_execution_packet()
    if packet.story_id != state.story_id:
        raise CompletionError("Completion state and handoff packet refer to different stories")

    base_sha = hl.git("rev-parse", "HEAD")
    prompt = (
        REPAIR_PROMPT.read_text(encoding="utf-8")
        + "\n\n# Execution context\n\n"
        + f"Story: `{state.story_id}`\n"
        + f"Repair pass: `{state.repair_attempts + 1}` of `{max_repair_attempts()}`\n\n"
        + "## Authoritative story\n\n"
        + (ROOT / packet.story_path).read_text(encoding="utf-8")
        + "\n\n## Review findings\n\n"
        + REVIEW_FINDINGS.read_text(encoding="utf-8")
    )
    result = hl.run_command(
        ["codex", "exec", "--ephemeral", "-"],
        check=False,
        capture=False,
        input_text=prompt,
    )
    if result.returncode != 0:
        raise CompletionError(f"Codex repair exited with status {result.returncode}")

    hl.verify_story_untouched(packet)
    changed = hl.changed_paths(base_sha)
    pending = hl.uncommitted_paths()
    hl.validate_changed_paths(sorted(set(changed) | set(pending)))
    if pending:
        raise CompletionError("Codex left uncommitted repair changes: " + ", ".join(sorted(pending)))
    if not changed:
        raise CompletionError("Repair pass produced no committed diff")

    report = hl.run_validation()
    state.repair_attempts += 1
    if not report["success"]:
        state.phase = "repair_required"
        save_state(state)
        return 2
    state.phase = "review_required"
    save_state(state)
    return 0


def _story_title(packet: hl.ExecutionPacket) -> str:
    first_heading = ""
    for line in (ROOT / packet.story_path).read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            first_heading = line[2:].strip()
            break
    return first_heading or packet.story_id


def publish() -> None:
    state = load_state()
    if state is None or state.phase != "publish_ready":
        raise CompletionError("publish requires a passed independent review")
    if shutil.which("gh") is None:
        raise CompletionError("GitHub CLI (gh) is required to publish the reviewed draft PR")
    _ensure_story_branch_ready(state)
    packet = _read_execution_packet()
    if packet.story_id != state.story_id:
        raise CompletionError("Completion state and handoff packet refer to different stories")
    report = hl.run_validation()
    if not report["success"]:
        raise CompletionError("Validation failed immediately before publish")

    title = _story_title(packet)
    changed = hl.changed_paths(packet.base_commit_sha)
    body = (
        f"## Completion-loop handoff\n\n"
        f"Story: `{state.story_id}`\n\n"
        f"Independent review: passed after {state.repair_attempts} repair pass(es).\n\n"
        "### Validation\n"
        "- `uv run pytest`\n"
        "- `npm test`\n"
        "- `npm run build`\n\n"
        "### Changed paths\n"
        + "\n".join(f"- `{path}`" for path in changed)
        + "\n\nThis PR was prepared by the bounded SAINT completion loop. It is intentionally draft and must not be auto-merged.\n"
    )
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    PR_BODY.write_text(body, encoding="utf-8")
    hl.git("push", "-u", "origin", state.branch or "")
    result = hl.run_command(
        [
            "gh",
            "pr",
            "create",
            "--draft",
            "--base",
            "main",
            "--head",
            state.branch or "",
            "--title",
            f"{state.story_id}: {title}",
            "--body-file",
            str(PR_BODY),
        ],
        check=False,
    )
    if result.returncode != 0:
        raise CompletionError("Branch pushed, but draft PR creation failed:\n" + (result.stdout or ""))
    state.phase = "awaiting_human_merge"
    save_state(state)
    print((result.stdout or "").strip())
    print("HALT: Marvin remains the sole merge authority.")


def default_target() -> str:
    value = load_policy().get("default_target", "all")
    if not isinstance(value, str) or not value:
        raise CompletionError("default_target must be a non-empty string")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", help="completion target; defaults to completion-policy.yaml")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="show the next project-level action")
    sub.add_parser("prepare-spec", help="prepare a supervised story-spec drafting packet")
    sub.add_parser("run", help="dispatch exactly one approved loop-eligible story")
    sub.add_parser("prepare-review", help="prepare an independent review packet for the current implementation")
    review = sub.add_parser("record-review", help="record the independent review gate result")
    review.add_argument("--result", choices=("pass", "changes"), required=True)
    review.add_argument("--findings-file")
    sub.add_parser("repair", help="run one bounded repair pass from recorded review findings")
    sub.add_parser("publish", help="revalidate, push, and open a draft PR after review passes")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        target = args.target or default_target()
        if args.command == "record-review":
            state = record_review(args.result, args.findings_file)
            print(json.dumps(asdict(state), indent=2))
            return 0
        if args.command == "repair":
            return repair()
        if args.command == "prepare-review":
            path = prepare_review_packet()
            print(f"Review packet: {path.relative_to(ROOT)}")
            return 0
        if args.command == "publish":
            publish()
            return 0

        decision = decide_next(target)
        if args.command == "status":
            print_decision(decision)
            state = load_state()
            if state:
                print("\nRuntime state:")
                print(json.dumps(asdict(state), indent=2))
            return 0
        if args.command == "prepare-spec":
            path = prepare_spec_packet(decision)
            print_decision(decision)
            print(f"Spec packet: {path.relative_to(ROOT)}")
            return 0
        if args.command == "run":
            print_decision(decision)
            return dispatch(decision)
        raise CompletionError(f"Unknown command: {args.command}")
    except (CompletionError, hl.LoopError) as exc:
        print(f"HALT: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
