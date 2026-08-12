# Story 3.6: Cleaned-Data Export

Status: ready-for-dev

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

Today the orchestrator produces a cleaned DataFrame internally (`_cleaned_df`) but discards it, carrying only `PipelineResult.cleaning_result` (the provenance model). This story adds **an explicit export path** for that cleaned frame.

1. **IN — CLI export surface (primary).** Add a `--cleaned-output <path>` option to `python -m backend.pipeline.orchestrator` to write the cleaned DataFrame to disk as CSV.
2. **IN — core API seam.** `run_full_pipeline(...)` gains an optional parameter (e.g. `cleaned_output_path: Path | None`) so non-CLI callers (Reporting Agent later, web API later) can reuse the export behavior without shelling out.
3. **OUT — do NOT build:** Healing Manifest rendering (3.3); any new cleaning operations or policy logic (3.2/3.4 are authoritative); report visualizations or before/after comparisons (3.7); notebook export/code generation (3.8); client-facing cleaning copy (3.9); any database persistence of the cleaned file (Epic 4+); API endpoints for download (Phase 3 web integration).
4. **OUT — do NOT change report semantics.** The report (Insight/Narrative/Renderer) continues to run on the ORIGINAL frame as in Story 3.4; exporting cleaned data does not re-point report generation.

## Acceptance Criteria

1. **Explicit export only.** No cleaned-data file is written unless the caller explicitly requests it (CLI `--cleaned-output`, or the new `run_full_pipeline` parameter). Default behavior is unchanged.

2. **Export requires cleaning enabled (fail loud).**
   - If `--cleaned-output` is provided while cleaning is not enabled (resolved gate is OFF), the CLI exits non-zero with a clear message and **does not write any file**.
   - If the pipeline halts at DQA (`result.halted == True`), no export file is written even if requested.

3. **CSV export correctness.** When cleaning is enabled and the run completes successfully:
   - The exported CSV is written with `index=False`.
   - The exported data matches the cleaned working copy produced by the coordinator for that run.
   - Exported columns reflect Tier-1 header normalization (if it ran) and Tier-2 imputation results (if configured / defaults applied).

4. **Provenance pairing.** When a cleaned export is written, the run must also have `PipelineResult.cleaning_result` populated (non-None). The export does not invent a parallel provenance format.

5. **No mutation of original input.** Export logic never mutates the caller's DataFrame. (This must remain true end-to-end across Tier-1 + Tier-2 + export.)

6. **Safe file handling.**
   - If the target path already exists, behavior is explicit: either (a) the CLI errors by default, or (b) a dedicated `--overwrite` flag is required to replace it. (Pick one and test it.)
   - Parent directories are created only if explicitly intended by the existing repo conventions; otherwise fail with a clear error.

7. **Tests.** Add tests that cover:
   - `--cleaned-output` with cleaning OFF errors and writes nothing.
   - `--cleaned-output` with cleaning ON writes a CSV.
   - Exported CSV content equals the in-run cleaned DataFrame for a fixed fixture (deterministic).
   - Halted pipeline does not export.
   - Existing-path behavior (no overwrite unless explicitly allowed).

All tests pass via `uv run pytest`.

## Tasks / Subtasks

- Add `cleaned_output` option to the Typer CLI.
- Extend `run_full_pipeline` to accept an optional `cleaned_output_path` and write `_cleaned_df` when present.
- Add an export helper (small pure function) to centralize CSV writing and path/overwrite behavior.
- Add/extend tests under `backend/tests/e2e/` (CLI path) and/or unit tests for the export helper.

## Dev Notes

- Export should be a pure side effect at the orchestrator boundary: the cleaning stage already produces the cleaned frame deterministically.
- Do not store DataFrames inside Pydantic models; keep the existing `PipelineResult.cleaning_result` provenance-only contract.
- Keep logging safe: log file paths and counts, never raw cell values.

## References

- `_bmad-output/implementation-artifacts/epic-3-cleaning-engine.md` (Story 3.6 row; Epic 3 invariants)
- `_bmad-output/implementation-artifacts/3-2-cleaning-engine-core.md` (working-copy invariant; determinism)
- `_bmad-output/implementation-artifacts/3-4-opt-in-gate-config.md` (tri-state enablement gate; coordinator wiring; report-on-original decision)
- `backend/pipeline/orchestrator.py` (cleaning stage produces `_cleaned_df` but currently discards it)

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

## Change Log

- 2026-08-11: Story 3.6 filed as ready-for-dev (cleaned-data export).