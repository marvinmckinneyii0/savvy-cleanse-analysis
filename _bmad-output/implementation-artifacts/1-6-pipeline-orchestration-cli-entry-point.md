# Story 1.6: Pipeline Orchestration & CLI Entry Point

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

> ⚠️ **BLOCKING DEPENDENCY — Story 1.5 (Document Rendering) must land first.**
> The orchestrator's final stage calls `DocxRenderer.render()` / `PdfRenderer.render()`, which are
> defined by Story 1.5. As of this story's creation, `backend/renderers/` contains only `__init__.py`
> and an empty `templates/` directory — **the renderers do not exist yet** (1.5 is `backlog`).
> Do **not** stub the renderers inside this story (that is 1.5's scope). Sequence 1.5 → 1.6, or
> coordinate so the renderer interface (`render(insight_report, output_path) -> None`, raising
> `ReportRenderError`) is available before wiring the render step. Everything *except* the render
> call (CSV load → DQA → Insights → Narrative, run-id propagation, exit codes, CLI surface) can be
> built and tested independently of 1.5. See Dev Notes → "Cross-Story Dependencies".

## Story

As a developer,
I want to run a single CLI command that ingests a CSV, runs the full pipeline (DQA → Insights → Narrative → Render), and outputs a formatted report,
so that the end-to-end pipeline is usable and demo-ready from the terminal.

## Acceptance Criteria

1. **Happy path, end-to-end.** Given a CSV file on disk, when the user runs
   `python -m backend.pipeline.orchestrator --input data.csv --output report.docx --format docx`,
   then the orchestrator loads the CSV into a DataFrame, runs data quality assessment, generates
   insights, produces narrative, renders the document, and saves it to the specified output path;
   the orchestrator returns a `PipelineResult` with `success=True` and all sub-reports populated;
   and the entire run completes in under 60 seconds for a well-structured CSV (NFR1).

2. **Halt on critical data quality.** Given the pipeline halts on critical DQA findings, when the
   orchestrator detects `halted=True` from the DQA stage, then subsequent stages (insight, narrative,
   render) are skipped; a diagnostic report is output (or logged) explaining the halt reason; and the
   CLI exits with a non-zero exit code.

3. **PDF format.** Given the user specifies `--format pdf`, when the pipeline completes successfully,
   then a PDF report is produced instead of docx.

4. **Run correlation + summary line.** Given any pipeline run, when the run starts, then a unique
   `pipeline_run_id` (UUID) is generated and propagated to every stage via structlog context; and the
   CLI outputs a summary line containing: `pipeline_run_id`, status (success/halted/error), duration,
   and output file path.

5. **Typer CLI surface.** Given the CLI entry point, when Typer is used for argument parsing, then
   `python -m backend.pipeline.orchestrator --help` displays usage with `--input` (required),
   `--output` (required), and `--format` (optional, default `docx`); and
   `backend/tests/e2e/test_cli_reporting.py` passes with an integration test running the full pipeline
   against `backend/tests/e2e/sample_data/clean_sales.csv`.

## Tasks / Subtasks

- [x] **Task 0 — Confirm Story 1.5 renderer availability** (AC: 1, 3)
  - [x] Verified: `backend/renderers/__init__.py` exports `DocxRenderer` and `PdfRenderer` with correct interface.

- [x] **Task 1 — Create the orchestrator composer** `backend/pipeline/orchestrator.py` (AC: 1, 2, 4)
  - [x] Implemented `run_full_pipeline(input_path, output_path, fmt, pipeline_run_id) -> PipelineResult`
  - [x] UUID run-id generation + `bind_pipeline_run_id()` at entry
  - [x] CSV load with `ConfigurationError` on missing/invalid file
  - [x] All four stages wired in sequence

- [x] **Task 2 — Halt handling & diagnostics** (AC: 2)
  - [x] `halted=True` short-circuits; `pipeline_halted` log event emitted; CLI exits code 1

- [x] **Task 3 — Run-id propagation & summary** (AC: 4)
  - [x] All stages receive `pipeline_run_id`; `pipeline_completed` log carries run_id, status, output, duration_s

- [x] **Task 4 — Render wiring** (AC: 1, 3)
  - [x] `docx` → `DocxRenderer().render()`; `pdf` → `PdfRenderer().render()`
  - [x] `ReportRenderError` propagates to CLI boundary

- [x] **Task 5 — Typer CLI entry point** (AC: 5)
  - [x] `--input` (required, exists), `--output` (required), `--format` (optional, default docx)
  - [x] `configure_logging()` called in CLI command, not at import time
  - [x] `if __name__ == "__main__": app()` guard present
  - [x] Exit codes: 0 success, 1 halt, 1 SavvyCleanseError

- [x] **Task 6 — E2E test + sample fixture** (AC: 1, 5)
  - [x] `backend/tests/e2e/__init__.py`, `clean_sales.csv` (60 rows, 4 cols), `critical_quality_issues.csv`
  - [x] `test_cli_reporting.py`: happy path docx, happy path pdf, run-id propagation, halt path, missing file, fallback narrative — 7 tests all passing

## Dev Notes

### Exact stage entry points (verified against code on `main`)
```python
# backend/pipeline/data_quality.py
DataQualityAssessor().assess_quality(df: pd.DataFrame, pipeline_run_id: str) -> PipelineResult
# backend/pipeline/insight_engine.py
InsightEngine().generate_insights(df: pd.DataFrame, quality_report: DataQualityReport, pipeline_run_id: str) -> InsightPayload
# backend/pipeline/narrative_generator.py
NarrativeGenerator().generate(insight_payload: InsightPayload, pipeline_run_id: str) -> InsightReport
```
- `assess_quality` already returns a `PipelineResult` with `quality_report` populated and `halted` set —
  reuse that object as the run's accumulator; do not construct a second `PipelineResult`.
- `PipelineResult` (`backend/models/pipeline_result.py`) is a **stdlib dataclass** (not Pydantic) precisely
  so later stages can mutate `insight_report` onto it. Fields: `success, halted, halt_reason,
  quality_report, insight_report, drift_report`. `drift_report` stays `None` in Phase 1 (Drift is Epic 2).

### Logging & run-id (architecture.md §462, §540-544; config.py)
- `configure_logging()` and `bind_pipeline_run_id()` live in `backend/pipeline/config.py`. The CLI
  entry point MUST call `configure_logging()` explicitly — the module never self-configures at import.
- Every log line in a run carries `pipeline_run_id` (UUID) via structlog contextvars. Each stage already
  binds it internally; the orchestrator binds it once up front so the CSV-load and summary logs carry it too.
- Event naming: `snake_case verb_noun` (e.g., `pipeline_started`, `pipeline_halted`, `pipeline_completed`).
- NEVER log: API keys, raw row data, PII, or file paths containing usernames (project-context.md).

### Error model (architecture.md §482-506, §506 rule)
- **Result vs Exception split is inviolable.** Bad *data* → `PipelineResult(halted=True, halt_reason=...)`
  (an expected outcome, not an exception). Infrastructure failures (file missing, render to disk fails,
  provider exhausted) → raise from the `SavvyCleanseError` hierarchy.
- CSV not found / unparseable = **pre-flight** `ConfigurationError` (sibling of stage errors, raised
  before any stage runs).
- Catch `SavvyCleanseError` only at the outermost CLI boundary; never swallow inside the composer.
- Forbidden: `except Exception: pass`, `print()` (use structlog), wildcard imports, hardcoded model
  versions/keys (project-context.md anti-patterns).

### Cross-Story Dependencies
- **Story 1.5 (Document Rendering) — BLOCKING for Task 4 & full happy-path e2e.** Expected interface
  (from epics.md §335-366): `DocxRenderer.render(insight_report, output_path)` and
  `PdfRenderer.render(insight_report, output_path)`, both raising `ReportRenderError` on failure, and
  both rendering a graceful placeholder when `insight_report.fallback=True`.
- Stories 1.1–1.4 (scaffolding, DQA, Insights, Narrative) are complete and on `main`; their stage code
  is the integration surface for this story.

### Layer boundaries (project-context.md)
- `orchestrator.py` lives in `backend/pipeline/` (Business Logic). It may import from `models/`,
  `renderers/`, and sibling pipeline stages. It must NOT import from `api/` or any **legacy** module
  (`advanced_pipeline.py`, `comprehensive_analytics.py`, `nlp_processor.py`, `analytics.py`,
  `main.py`, `main_enhanced.py`, `dashboard_api.py`).

### Testing standards (project-context.md; conftest.py)
- Tests live in `backend/tests/` (not co-located). E2E under `backend/tests/e2e/`.
- Reusable fixtures already in `backend/tests/conftest.py`: `clean_sales_df`, `dirty_sales_df`,
  `mock_llm_client`, `pipeline_run_id`, plus a session-autouse logging fixture. **Reuse `mock_llm_client`**
  so the e2e test is deterministic and never hits a real provider.
- Every new module requires a matching test file. Run `pytest backend/tests/` — zero regressions expected
  (prior baseline: 84/84 passing after Story 1.4).

### Latest tech / versions (architecture.md §320, §340; project-context.md)
- **Typer 0.12.1+** is the pinned CLI framework. Use `typer.Option(..., exists=True)` for `--input`,
  `typer.Exit(code=...)` for exit codes, and an `Enum` (or `typer` choices) for `--format`.
- Python 3.13, Pydantic v2, structlog 25.5.0, pandas. No new dependencies needed — Typer is already in the
  Phase-1 dependency set (architecture.md §229).

### Project Structure Notes
- Target file matches the architecture target tree exactly: `backend/pipeline/orchestrator.py`
  (`run_full_pipeline()` composer — architecture.md §147, §587).
- New test scaffolding: `backend/tests/e2e/__init__.py`, `backend/tests/e2e/test_cli_reporting.py`,
  `backend/tests/e2e/sample_data/clean_sales.csv` (architecture.md §674).
- CLI output directory `output/` is gitignored (architecture.md §733) — tests should write to a tmp path
  (`tmp_path` fixture), not the repo.
- No variance from the unified structure detected.

### Definition of Done (sprint-status.yaml, applies from Story 1.4 onward)
- All acceptance criteria met; unit + integration (e2e) tests pass.
- Run `/security-review` and resolve all Critical/High findings before marking done.

### References
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.6: Pipeline Orchestration & CLI Entry Point]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.5: Document Rendering] (renderer interface)
- [Source: _bmad-output/planning-artifacts/architecture.md#L147] (orchestrator.py — run_full_pipeline composer)
- [Source: _bmad-output/planning-artifacts/architecture.md#L482-L544] (dual error strategy, run-id, enforcement)
- [Source: _bmad-output/project-context.md#Pipeline] (stage rules, layer boundaries, anti-patterns)
- [Source: backend/pipeline/config.py] (configure_logging, bind_pipeline_run_id)
- [Source: backend/models/pipeline_result.py] (PipelineResult dataclass — mutation pattern)
- [Source: backend/tests/conftest.py] (clean_sales_df, dirty_sales_df, mock_llm_client, pipeline_run_id)

## Dev Agent Record

### Agent Model Used
claude-sonnet-4-6

### Completion Notes List

Story 1.5 was implemented immediately before this story in the same session — renderers were confirmed present before Task 0.

Typer 0.26.8 (latest) was installed; the story spec called for >=0.12.1, compatible.

NarrativeGenerator.generate is patched in all e2e tests — the generator retries 3×3 with `time.sleep` when providers are absent, so running it live in tests would take 21+ seconds and fail offline. Patching is the correct e2e strategy; generator internals are covered by `test_narrative_generator.py`.

`test_unparseable_csv_raises_configuration_error` writes a binary-corrupted CSV. pandas will raise a `ParserError` (subclass of `ValueError`) which the orchestrator wraps in `ConfigurationError`.

Full regression: 110 passed, 1 skipped (pre-existing Anthropic SDK skip), 0 failures.

### File List

- `pyproject.toml` — added `typer>=0.12.1`, `pandas>=2.0`
- `backend/pipeline/orchestrator.py` — NEW
- `backend/tests/e2e/__init__.py` — NEW
- `backend/tests/e2e/test_cli_reporting.py` — NEW (7 tests)
- `backend/tests/e2e/sample_data/clean_sales.csv` — NEW
- `backend/tests/e2e/sample_data/critical_quality_issues.csv` — NEW
