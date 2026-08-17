# SAINT Agent Execution Contract

This repository uses a bounded Claude → Codex development handoff.

## Authority

- `_bmad-output/implementation-artifacts/sprint-status.yaml` is the sole status source of truth.
- The selected BMAD story file is the authoritative execution contract.
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

## Claude responsibilities

Claude is the controller and reviewer:

1. Run `python agent-system/handoff_loop.py status`.
2. Review the selected story, PRD, dependencies, and repository state.
3. Run `python agent-system/handoff_loop.py run` only when the selected story is safe and unambiguous.
4. Independently inspect the resulting diff and validation report.
5. Stop at a draft PR and summarize the exact human review focus.

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

Every implementation run must pass:

```bash
uv run pytest
npm test
npm run build
```

Run any additional story-specific, lint, security, type, or integration checks required by the story or existing CI.
