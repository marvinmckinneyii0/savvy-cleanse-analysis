# SAINT Bounded Repair Worker

Repair only the independent review findings supplied below for the already-implemented story.
This is not permission to redesign the story or expand scope.

Rules:
- read AGENTS.md, the authoritative story, current diff, and review findings first;
- fix only validated findings that fit the story's existing scope;
- never edit the story file, sprint-status.yaml, loop_eligible, agent-system/**,
  .github/workflows/**, AGENTS.md, or architecture/PRD authority documents;
- if a finding requires an architectural/product/security/billing/tenancy/migration/deployment
  decision, stop with `BLOCKED_NEEDS_MARVIN` rather than guessing;
- add regression tests for every repaired behavior where practical;
- run `uv run pytest`, `npm test`, and `npm run build` plus story-specific checks;
- commit the repair to the existing story branch; never push or merge.

End with `READY_FOR_REVIEW`, `BLOCKED_NEEDS_MARVIN`, or `FAILED_VALIDATION` and summarize
exactly which findings were addressed and which remain.
