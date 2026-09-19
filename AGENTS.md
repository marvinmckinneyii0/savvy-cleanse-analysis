# SAINT Agent Execution Contract

This repository uses a bounded Claude → Codex development handoff, with a project-level
completion controller layered above it.

## Authority

- `_bmad-output/implementation-artifacts/sprint-status.yaml` is the sole status source of truth.
- The selected BMAD story file is the authoritative execution contract.
- `agent-system/completion-policy.yaml` may order a completion target, but it never overrides canonical story status, dependencies, or eligibility.
- `loop_eligible` is human-controlled. Agents must never change it.
- Marvin is the sole merge authority. Agents may open draft pull requests but must never merge.

## Per-run boundary

A run may execute exactly one story. It must stop when:

- no story is both `ready-for-dev` and `loop_eligible: true`;
- an upstream dependency is not done;
- the story is ambiguous or contradicts an architectural invariant;
- implementation requires work outside the story scope;
- authentication, authorization, tenancy, billing, migrations, destructive operations, production deployment, or shared schemas require an unapproved decision;
- required tests fail outside the story scope;
- the story is materially larger or riskier than specified.

## Completion-loop responsibilities

`agent-system/completion_loop.py` is the project-level state machine. It may:

1. discover the next incomplete story for a configured target;
2. prepare a supervised story-spec packet when an authoritative story file is missing;
3. dispatch the existing bounded handoff only when the story is already `ready-for-dev`, dependency-clear, and `loop_eligible: true`;
4. prepare an independent review packet;
5. record a review result and run at most two bounded repair passes;
6. after review passes, re-run validation, push the story branch, and open a **draft** PR.

It must never:

- create or approve its own product/architecture decisions;
- promote `backlog` to `ready-for-dev`;
- change `loop_eligible`;
- dispatch `loop_eligible: false` work unattended;
- chain multiple implementation stories in one invocation;
- merge a PR or treat a pushed/draft PR as done;
- let local `.agent-handoff/` runtime state override the canonical BMAD ledger.

After a human merge, canonical story status must be reconciled separately before the loop can
advance to dependent work.

## Claude responsibilities

Claude is the controller and reviewer:

1. Run `python agent-system/completion_loop.py status` for project-level work, or
   `python agent-system/handoff_loop.py status` for the low-level handoff view.
2. Review any generated story-spec packet against the PRD, architecture, dependencies, and repository reality before approving a status promotion.
3. Allow `completion_loop.py run` only when the selected story is safe and unambiguous.
4. Independently inspect the resulting diff and validation report using the generated review packet.
5. Record `pass` or concrete change findings; do not implement the same story in the same review pass unless Marvin explicitly overrides the separation.
6. Stop at a draft PR and summarize the exact human review focus.

Claude must not implement the same story it reviews unless Marvin explicitly overrides the separation.

## Codex responsibilities

Codex is the implementation worker:

- Modify only files allowed by the story.
- Implement the smallest complete change satisfying every acceptance criterion.
- Preserve all invariants and backward compatibility requirements.
- Add tests for success, failure, boundaries, and regressions.
- Run the full required repository checks.
- Never edit `loop_eligible`, orchestration policy, or this contract.
- Never merge.
- Halt rather than guessing when scope or architecture is unclear.

## Required checks

Every implementation and repair run must pass:

```bash
uv run pytest
npm test
npm run build
```

Run any additional story-specific, lint, security, type, or integration checks required by the story or existing CI.
