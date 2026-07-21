#!/usr/bin/env python3
"""Bounded Claude → Codex handoff loop for SAINT.

The loop executes at most one eligible BMAD story per invocation. It never merges,
never edits loop_eligible, and treats sprint-status.yaml as authoritative.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "_bmad-output" / "implementation-artifacts" / "sprint-status.yaml"
STORY_DIR = STATUS_PATH.parent
PROMPT_PATH = ROOT / "agent-system" / "prompts" / "codex-worker.md"
RUNTIME_DIR = ROOT / ".agent-handoff"
CURRENT_PACKET = RUNTIME_DIR / "current.json"
CURRENT_PROMPT = RUNTIME_DIR / "current-prompt.md"
VALIDATION_REPORT = RUNTIME_DIR / "validation.json"

READY_STATUS = "ready-for-dev"
DONE_STATUS = "done"
PROTECTED_PATH_PREFIXES = (
    "agent-system/",
    ".github/workflows/",
)
PROTECTED_EXACT_PATHS = {
    "AGENTS.md",
    "_bmad-output/implementation-artifacts/sprint-status.yaml",
    "_bmad-output/implementation-artifacts/loop-runner-spec.md",
}


class LoopError(RuntimeError):
    """Expected, user-actionable loop failure."""


@dataclass(frozen=True)
class StoryCandidate:
    story_id: str
    status: str
    loop_eligible: bool
    story_path: str
    dependencies: tuple[str, ...]
    blocked_dependencies: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionPacket:
    story_id: str
    story_path: str
    base_commit_sha: str
    status_file_sha256: str
    story_file_sha256: str
    dependencies: tuple[str, ...]
    generated_at: str
    branch: str
    constraints: tuple[str, ...]


def run_command(
    command: list[str],
    *,
    cwd: Path = ROOT,
    check: bool = True,
    capture: bool = True,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        input=input_text,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )
    if check and result.returncode != 0:
        output = result.stdout or ""
        raise LoopError(f"Command failed ({result.returncode}): {' '.join(command)}\n{output}")
    return result


def git(*args: str, check: bool = True) -> str:
    return (run_command(["git", *args], check=check).stdout or "").strip()


def sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_status() -> dict[str, Any]:
    if not STATUS_PATH.exists():
        raise LoopError(f"Missing canonical status file: {STATUS_PATH}")
    data = yaml.safe_load(STATUS_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("development_status"), dict):
        raise LoopError("sprint-status.yaml has no development_status mapping")
    return data


def story_entries(status_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for key, value in status_data["development_status"].items():
        if not isinstance(value, dict):
            continue
        if "status" not in value or "loop_eligible" not in value:
            continue
        entries[str(key)] = value
    return entries


def find_story_file(story_id: str) -> Path:
    matches = sorted(STORY_DIR.glob(f"{story_id}*.md"))
    if not matches:
        raise LoopError(f"No BMAD story file found for {story_id}")
    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise LoopError(f"Ambiguous story files for {story_id}: {names}")
    return matches[0]


def extract_dependencies(story_text: str, known_story_ids: set[str]) -> tuple[str, ...]:
    """Conservatively extract explicit story prerequisites from markdown.

    Only references near prerequisite/dependency language count. Incidental references
    in broader prose do not become execution dependencies.
    """

    found: set[str] = set()
    dependency_words = re.compile(
        r"(?i)(prerequisite|required before|depends? on|blocked[-_ ]on|upstream|must be merged first)"
    )
    story_ref = re.compile(r"\b(?:Story\s+)?([Rr]?\.?\d+(?:\.\d+)?|\d+-\d+[a-z]?)\b")

    for line in story_text.splitlines():
        if not dependency_words.search(line):
            continue
        for raw in story_ref.findall(line):
            normalized = raw.lower().replace(".", "-")
            for story_id in known_story_ids:
                numeric_prefix = story_id.split("-", 2)[:2]
                candidate_prefix = "-".join(numeric_prefix)
                if normalized == story_id.lower() or normalized == candidate_prefix.lower():
                    found.add(story_id)
    return tuple(sorted(found))


def collect_candidates() -> tuple[list[StoryCandidate], list[StoryCandidate]]:
    status_data = load_status()
    entries = story_entries(status_data)
    known_ids = set(entries)
    eligible: list[StoryCandidate] = []
    blocked: list[StoryCandidate] = []

    for story_id, metadata in entries.items():
        if metadata.get("status") != READY_STATUS or metadata.get("loop_eligible") is not True:
            continue
        story_path = find_story_file(story_id)
        dependencies = extract_dependencies(
            story_path.read_text(encoding="utf-8"),
            known_ids,
        )
        blocked_dependencies = tuple(
            dep for dep in dependencies if entries.get(dep, {}).get("status") != DONE_STATUS
        )
        candidate = StoryCandidate(
            story_id=story_id,
            status=str(metadata.get("status")),
            loop_eligible=True,
            story_path=str(story_path.relative_to(ROOT).as_posix()),
            dependencies=dependencies,
            blocked_dependencies=blocked_dependencies,
        )
        (blocked if blocked_dependencies else eligible).append(candidate)

    eligible.sort(key=story_sort_key)
    blocked.sort(key=story_sort_key)
    return eligible, blocked


def story_sort_key(candidate: StoryCandidate) -> tuple[Any, ...]:
    parts: list[Any] = []
    for token in re.split(r"[-.]", candidate.story_id):
        parts.append(int(token) if token.isdigit() else token)
    return tuple(parts)


def ensure_repo_ready() -> None:
    if shutil.which("git") is None:
        raise LoopError("git is not available")
    if shutil.which("codex") is None:
        raise LoopError("Codex CLI is not available. Run /codex:setup in Claude Code.")

    repo_root = Path(git("rev-parse", "--show-toplevel")).resolve()
    if repo_root != ROOT:
        raise LoopError(f"Run from the SAINT repository. Expected {ROOT}, found {repo_root}")

    branch = git("branch", "--show-current")
    if branch != "main":
        raise LoopError(f"Start the handoff from main; current branch is {branch!r}")

    status = git("status", "--porcelain")
    if status:
        raise LoopError("Working tree is not clean. Commit, stash, or discard unrelated changes first.")

    git("fetch", "origin", "main")
    local = git("rev-parse", "main")
    remote = git("rev-parse", "origin/main")
    if local != remote:
        raise LoopError("Local main is not equal to origin/main. Pull or reconcile before dispatch.")


def select_candidate(requested_story: str | None = None) -> StoryCandidate:
    eligible, blocked = collect_candidates()
    if requested_story:
        for candidate in eligible:
            if candidate.story_id == requested_story:
                return candidate
        for candidate in blocked:
            if candidate.story_id == requested_story:
                deps = ", ".join(candidate.blocked_dependencies)
                raise LoopError(f"Story {requested_story} is blocked by incomplete dependencies: {deps}")
        raise LoopError(
            f"Story {requested_story} is not both {READY_STATUS!r} and loop_eligible:true"
        )
    if not eligible:
        if blocked:
            details = "; ".join(
                f"{item.story_id} blocked by {', '.join(item.blocked_dependencies)}"
                for item in blocked
            )
            raise LoopError(f"No selectable story. Dependency-blocked candidates: {details}")
        raise LoopError("No story is currently ready-for-dev and loop_eligible:true. Exiting safely.")
    return eligible[0]


def create_packet(candidate: StoryCandidate) -> ExecutionPacket:
    branch = f"loop/story-{candidate.story_id}"
    story_path = ROOT / candidate.story_path
    return ExecutionPacket(
        story_id=candidate.story_id,
        story_path=candidate.story_path,
        base_commit_sha=git("rev-parse", "HEAD"),
        status_file_sha256=sha256(STATUS_PATH),
        story_file_sha256=sha256(story_path),
        dependencies=candidate.dependencies,
        generated_at=datetime.now(timezone.utc).isoformat(),
        branch=branch,
        constraints=(
            "one story per run",
            "never modify loop_eligible",
            "never merge",
            "halt on ambiguity or scope expansion",
            "full pytest, frontend test, and production build required",
        ),
    )


def prepare_handoff(candidate: StoryCandidate) -> ExecutionPacket:
    packet = create_packet(candidate)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    CURRENT_PACKET.write_text(json.dumps(asdict(packet), indent=2) + "\n", encoding="utf-8")

    worker_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    story_text = (ROOT / packet.story_path).read_text(encoding="utf-8")
    rendered = (
        f"{worker_prompt}\n\n"
        "# Execution packet\n\n"
        f"```json\n{json.dumps(asdict(packet), indent=2)}\n```\n\n"
        f"# Authoritative story: `{packet.story_path}`\n\n"
        f"{story_text}\n"
    )
    CURRENT_PROMPT.write_text(rendered, encoding="utf-8")
    return packet


def verify_packet_fresh(packet: ExecutionPacket) -> None:
    if git("rev-parse", "HEAD") != packet.base_commit_sha:
        raise LoopError("Base commit moved after handoff preparation")
    if sha256(STATUS_PATH) != packet.status_file_sha256:
        raise LoopError("sprint-status.yaml changed after handoff preparation")
    if sha256(ROOT / packet.story_path) != packet.story_file_sha256:
        raise LoopError("Story file changed after handoff preparation")


def changed_paths(base_sha: str) -> list[str]:
    output = git("diff", "--name-only", f"{base_sha}...HEAD")
    return [line.strip() for line in output.splitlines() if line.strip()]


def validate_changed_paths(paths: list[str]) -> None:
    violations: list[str] = []
    for path in paths:
        if path in PROTECTED_EXACT_PATHS or any(path.startswith(prefix) for prefix in PROTECTED_PATH_PREFIXES):
            violations.append(path)
    if violations:
        raise LoopError("Codex modified protected orchestration paths: " + ", ".join(violations))


def run_validation() -> dict[str, Any]:
    checks = [
        ("backend", ["uv", "run", "pytest"]),
        ("frontend", ["npm", "test"]),
        ("build", ["npm", "run", "build"]),
    ]
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": [],
        "success": True,
    }
    for name, command in checks:
        result = run_command(command, check=False)
        passed = result.returncode == 0
        report["checks"].append(
            {
                "name": name,
                "command": command,
                "returncode": result.returncode,
                "passed": passed,
                "output_tail": (result.stdout or "")[-4000:],
            }
        )
        report["success"] = bool(report["success"] and passed)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def execute(candidate: StoryCandidate) -> int:
    ensure_repo_ready()
    packet = prepare_handoff(candidate)
    verify_packet_fresh(packet)

    existing = git("branch", "--list", packet.branch)
    if existing:
        raise LoopError(f"Local branch already exists: {packet.branch}")
    remote_existing = git("ls-remote", "--heads", "origin", packet.branch)
    if remote_existing:
        raise LoopError(f"Remote branch already exists: {packet.branch}")

    git("checkout", "-b", packet.branch)
    try:
        prompt = CURRENT_PROMPT.read_text(encoding="utf-8")
        result = run_command(
            ["codex", "exec", "--ephemeral", "-"],
            check=False,
            capture=False,
            input_text=prompt,
        )
        if result.returncode != 0:
            raise LoopError(f"Codex exited with status {result.returncode}")

        paths = changed_paths(packet.base_commit_sha)
        if not paths:
            raise LoopError("Codex completed without producing a committed diff")
        validate_changed_paths(paths)

        report = run_validation()
        if not report["success"]:
            print(f"Validation failed. Report: {VALIDATION_REPORT.relative_to(ROOT)}")
            return 2

        print("\nHandoff implementation is ready for Claude review.")
        print(f"Story: {packet.story_id}")
        print(f"Branch: {packet.branch}")
        print("Changed paths:")
        for path in paths:
            print(f"  - {path}")
        print(f"Validation report: {VALIDATION_REPORT.relative_to(ROOT)}")
        print("Do not merge. Claude must review the diff before a draft PR is presented to Marvin.")
        return 0
    except Exception:
        print(f"\nLoop halted on branch {packet.branch}. Changes were preserved for inspection.")
        raise


def print_status() -> int:
    eligible, blocked = collect_candidates()
    print("SAINT Claude → Codex handoff status")
    print(f"Canonical status: {STATUS_PATH.relative_to(ROOT)}")
    if eligible:
        print("\nSelectable stories:")
        for item in eligible:
            deps = ", ".join(item.dependencies) or "none"
            print(f"  {item.story_id}: {item.story_path} (dependencies: {deps})")
        print(f"\nNext story: {eligible[0].story_id}")
    else:
        print("\nNo selectable stories.")
    if blocked:
        print("\nDependency-blocked eligible stories:")
        for item in blocked:
            print(f"  {item.story_id}: {', '.join(item.blocked_dependencies)}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="show selectable and blocked stories")

    prepare_parser = subparsers.add_parser("prepare", help="write a handoff packet without running Codex")
    prepare_parser.add_argument("--story", help="explicit story id; default selects the next eligible story")

    run_parser = subparsers.add_parser("run", help="execute one bounded Codex handoff")
    run_parser.add_argument("--story", help="explicit story id; default selects the next eligible story")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "status":
            return print_status()
        candidate = select_candidate(getattr(args, "story", None))
        if args.command == "prepare":
            ensure_repo_ready()
            packet = prepare_handoff(candidate)
            print(json.dumps(asdict(packet), indent=2))
            print(f"Prompt: {CURRENT_PROMPT.relative_to(ROOT)}")
            return 0
        if args.command == "run":
            return execute(candidate)
        raise LoopError(f"Unknown command: {args.command}")
    except LoopError as exc:
        print(f"HALT: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
