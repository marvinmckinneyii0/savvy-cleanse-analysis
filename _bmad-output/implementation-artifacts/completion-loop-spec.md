# SAINT Completion Loop v2 — Specification

## Purpose

Add a project-level state machine above the existing bounded Claude → Codex handoff. The
completion loop moves the roadmap toward a selected target without weakening any existing
human-control boundary.

## Non-negotiable invariants

- `sprint-status.yaml` remains the sole source of truth for story status.
- `loop_eligible` remains human-set and is never changed by the loop.
- A single invocation may dispatch at most one implementation story.
- Backlog stories are never auto-promoted to `ready-for-dev`.
- `loop_eligible: false` stories are never dispatched unattended.
- Independent review is required before publish.
- At most two automated repair passes are allowed before halting for human review.
- Publish means push + **draft** PR only. The loop never merges.
- Marvin remains the sole merge authority.

## State machine

`DISCOVER → SPEC_REQUIRED → HUMAN SPEC APPROVAL → READY → IMPLEMENT → VALIDATE → REVIEW`

From review:
- pass → `PUBLISH_READY → DRAFT PR → HUMAN MERGE → LEDGER RECONCILIATION`
- changes → `REPAIR → VALIDATE → REVIEW`, maximum two repair passes
- unresolved/ambiguous/out-of-scope → HALT

The controller does not pretend to complete human checkpoints. If the canonical ledger says a
story is backlog, supervised, in review, blocked, or awaiting reconciliation, the controller
reports that state and stops.

## Epic 3 pilot target

`completion-policy.yaml` defines `epic-3-closeout` using the sequence already recorded by the
canonical sprint ledger:

1. 3.9 — Cleaning Mode Definitions & Disclosure
2. 3.7 — Report Visualizations
3. 3.8 — Notebook Export / Code Generation

The three story files do not yet exist at the time this controller is introduced, so the first
expected action is `SPEC_REQUIRED` for 3.9.

## Commands

```bash
python agent-system/completion_loop.py status
python agent-system/completion_loop.py prepare-spec
python agent-system/completion_loop.py run
python agent-system/completion_loop.py prepare-review
python agent-system/completion_loop.py record-review --result pass
python agent-system/completion_loop.py record-review --result changes --findings-file review.md
python agent-system/completion_loop.py repair
python agent-system/completion_loop.py publish
```

Use `--target` to select another configured target, an `epic-N` target, an explicit story id, or
`all`. Configured targets may define order only; they cannot override canonical status or safety
metadata.

## Runtime artifacts

All mutable controller state is local under `.agent-handoff/` and remains gitignored:

- `completion-state.json`
- `spec-prompt.md`
- `review-prompt.md`
- `review-findings.md`
- `pr-body.md`

No runtime file is authoritative over the BMAD ledger or story specification.
