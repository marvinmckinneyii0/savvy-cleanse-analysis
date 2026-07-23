# Claude → Codex PRD Handoff Loop

This loop executes one safe, eligible SAINT story per run.

## Operating model

1. Claude reads the canonical sprint status and selects the next story where:
   - `status: ready-for-dev`
   - `loop_eligible: true`
   - explicit dependencies are `done`
2. The loop writes a SHA-bound execution packet.
3. A fresh `loop/story-*` branch is created from a clean, synchronized `main`.
4. Codex receives the worker contract plus the complete authoritative story.
5. Codex implements and commits the story.
6. The controller rejects changes to protected orchestration paths.
7. The full repository validation suite runs.
8. Claude reviews the diff.
9. After approval, Claude may push and open a draft PR.
10. Marvin reviews and manually merges.
11. Run the loop again after the merge.

The loop never continuously drains the roadmap. Each invocation stops after one story and one human checkpoint.

## Commands

From the repository root in Claude Code:

```bash
python agent-system/handoff_loop.py status
```

Preview the exact handoff without executing Codex:

```bash
python agent-system/handoff_loop.py prepare
```

Execute the next eligible story:

```bash
python agent-system/handoff_loop.py run
```

Execute a specific eligible story:

```bash
python agent-system/handoff_loop.py run --story 3-6-cleaned-data-export
```

## Claude invocation

Use this instruction in Claude Code:

```text
Run the SAINT bounded PRD handoff loop. First execute
`python agent-system/handoff_loop.py status`. If exactly one safe story is
selectable, inspect its BMAD story and dependencies, then execute
`python agent-system/handoff_loop.py run`. After Codex returns, independently
review the committed diff and `.agent-handoff/validation.json`. Halt on any
scope, architecture, security, or acceptance-criteria problem. If clean, push
the story branch and open a draft PR. Never merge.
```

## Runtime artifacts

The local `.agent-handoff/` directory contains:

- `current.json` — immutable execution packet
- `current-prompt.md` — exact prompt sent to Codex
- `validation.json` — independent validation results

These artifacts are local and intentionally ignored by Git.

## Current queue behavior

If no story is currently both ready and eligible, the command exits safely. Claude must not change `loop_eligible` merely to keep the loop active.
