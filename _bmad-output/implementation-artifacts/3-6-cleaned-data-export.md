# Story 3.6: Cleaned-Data Export

Status: done

Sizing: S · Model: Sonnet · loop_eligible: true
<!-- Sonnet + loop_eligible:true because this is a mechanical extension: emit an export
     artifact from an already-produced deterministic cleaned DataFrame. It must preserve
     Epic 3 invariants (default-off cleaning; working-copy only; Tier-3 untouched) but does
     not introduce new remediation logic, new schema, or new policy decisions. -->

## Story
As an **SMB owner using SAINT's cleaning pipeline**,
I want **to export the cleaned working copy to a CSV file when (and only when) I have explicitly opted into cleaning**,
so that **I can use the cleaned data downstream while still keeping my original data unchanged and having a complete provenance record of what was done** (Epic 3 INVARIANTS).

## Context & scope boundary
Story 3.4 introduced the opt-in cleaning gate (default OFF) and the Tier-1 + Tier-2 coordinator (`clean_dataset(...)`) inside `run_full_pipeline(...)`.

This story adds:
- A CLI option to write the cleaned working copy to disk as CSV.
- A `run_full_pipeline(...)` seam so non-CLI callers can request the same export.

Out of scope:
- Healing Manifest rendering (3.3)
- Any new cleaning operations or policy logic (3.2/3.4 are authoritative)
- Report visualizations / before-after comparisons (3.7)
- Notebook export/code generation (3.8)
- Client-facing cleaning copy (3.9)
- Any DB-backed persistence or download endpoints (Epic 4+)
- Any change to report semantics (report continues to run on the ORIGINAL frame)

## Acceptance Criteria
1. Explicit export only: no cleaned-data file unless requested.
2. Export requires cleaning enabled: if export requested while cleaning resolves OFF → fail loud, write nothing.
3. No export on halted run.
4. Export writes CSV with `index=False` and matches the cleaned working copy.
5. Provenance pairing: when export is written, `PipelineResult.cleaning_result` is populated.
6. Safe file handling: default no-overwrite; explicit overwrite flag required.

## Dev Notes
- Implemented by extending `backend/pipeline/orchestrator.py`:
  - `--cleaned-output` + `--overwrite-cleaned-output` CLI flags.
  - `run_full_pipeline(..., cleaned_output_path, overwrite_cleaned_output)` parameters.
  - Centralized CSV write + path validation in a helper.

## Dev Agent Record
### Debug Log References
- `uv run pytest` → 330 passed / 1 skipped (warnings only).

### File List
- `backend/pipeline/orchestrator.py`
- `backend/tests/e2e/test_cleaned_data_export.py`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/3-6-cleaned-data-export.md`

## Change Log
- 2026-08-11: Implemented cleaned CSV export via orchestrator seam + CLI flags; E2E coverage added; status → done.