# Story 2.4: Reporting Agent

Status: done

<!-- Numbering: epics.md "Story 2.3: Reporting Agent" == filed 2.4 (renumbered per the
     Epic 2 reconciliation documented in 2-3-drift-engine.md). This story depends on the
     Drift Engine (filed 2.3, done). -->

## Story

As a developer,
I want a CLI agent that pulls the latest data, invokes the full pipeline (DQA → Drift → Insight
→ Narrative → Render), and can run on a schedule,
so that reports are generated automatically without manual intervention.

## Acceptance Criteria

1. **Manual generate.** Given a configured data source in `config.yaml` and an output directory,
   when the user runs `python -m backend.agents.reporting_agent generate --input data.csv --format docx`,
   then the agent loads config (`PipelineConfig.load`), invokes the pipeline orchestrator with the
   specified input, and saves the rendered report to the configured output directory
   (`output.output_dir`), with a filename that includes the dataset key and a UTC timestamp.

2. **Drift inclusion, gated on baseline existence.** Given the manual/scheduled run, when a baseline
   profile already exists for the dataset (`backend/baselines/{dataset_key}.json`), then the Drift
   Engine is included in the pipeline, a `DriftReport` is attached to `PipelineResult.drift_report`,
   and the rendered report contains a **Drift Analysis** section. And when no baseline exists, the
   pipeline runs without drift analysis, `DriftEngine.run` creates the initial baseline (returns
   `None`), and the report omits the Drift Analysis section.

3. **Scheduled execution.** Given `report_schedule` in `config.yaml` (e.g. `interval: weekly` or a
   `cron` expression), when the user runs `python -m backend.agents.reporting_agent schedule`, then a
   scheduler (APScheduler `BlockingScheduler`) starts, triggers pipeline execution at the configured
   cadence, runs in the foreground, and **each scheduled run re-loads `config.yaml`** so edits take
   effect without a restart (hot-reload).

4. **Error recovery (scheduled).** Given a pipeline failure during a scheduled run (file not found,
   LLM failure, render error), when the error occurs, then the agent logs the error with full context
   (`pipeline_run_id`, error type, detail) and the scheduler continues to the next run — the agent
   does not crash or stop scheduling. (A failure in the `generate` one-shot command still exits
   non-zero, matching the existing orchestrator CLI.)

5. **Observability + tests.** Given any agent invocation, when the agent runs, then each run logs
   `pipeline_run_id`, timestamp, status, and output file path; and `backend/tests/test_reporting_agent.py`
   passes with tests covering: manual generate, scheduled execution (mocked scheduler/timer),
   drift-included pipeline (baseline present → Drift Analysis section rendered), first-run (no baseline
   → no drift section, baseline created), and scheduled-run error recovery.

## Tasks / Subtasks

- [ ] **Task 0 — Verify assumptions against the current tree** (all ACs)
  - [ ] Confirm `backend/agents/__init__.py` exists and `backend/agents/reporting_agent.py` does **not**.
  - [ ] Confirm `backend/pipeline/orchestrator.py` `run_full_pipeline(input_path, output_path, fmt, pipeline_run_id)`
        currently runs DQA → Insights → Narrative → Render with **no** drift stage, and that
        `PipelineResult` already has a `drift_report: "DriftReport | None"` field (2.3).
  - [ ] Confirm `InsightEngine.generate_insights(df, quality_report, pipeline_run_id)` does not yet take
        a drift argument, and `NarrativeGenerator.generate(payload, run_id)` returns an `InsightReport`.
  - [ ] Confirm `DriftEngine.run(current_df, dataset_key, pipeline_run_id) -> DriftReport | None` exists
        (2.3), that `_SAFE_DATASET_KEY` constrains `dataset_key`, and that `baseline_dir` defaults to
        `backend/baselines`.
  - [ ] Confirm `PipelineConfig.load(path)` exists and exposes `report_schedule` (interval|cron),
        `output.format`, `output.output_dir`, and `data_sources` (Story 2.1).
  - [ ] Confirm APScheduler is absent from `pyproject.toml` (Task 5 adds it) and that the renderers are
        `DocxRenderer`/`PdfRenderer` in `backend/renderers/` consuming an `InsightReport`, with Jinja/
        docxtpl templates in `backend/renderers/templates/`.

- [ ] **Task 1 — Thread drift through the pipeline data flow** (AC: 2) — per architecture.md §754-764
      (`drift_engine → insight_engine(DataFrame + QualityReport + DriftReport) → …`).
  - [ ] Extend `InsightEngine.generate_insights` with a **new optional** param
        `drift_report: DriftReport | None = None` (backward-compatible; existing callers unaffected).
  - [ ] Extend `InsightPayload` with a **new optional** field `drift_report: DriftReport | None = None`
        (allowed: additive optional field; do not modify/remove existing fields). `generate_insights`
        stores the passed drift report there.
  - [ ] Extend `InsightReport` with a **new optional** field `drift_report: DriftReport | None = None`,
        populated **server-side** by `NarrativeGenerator.generate` (copied from the payload, like
        `metadata` — never LLM-set), so the renderer can access it. Do **not** add drift to
        `NarrativeContent` (the LLM-facing schema) — the drift section is deterministic, not generated.
  - [ ] `NarrativeGenerator.generate(insight_payload, pipeline_run_id)` copies
        `insight_payload.drift_report` onto the returned `InsightReport` (both the normal and the
        `fallback` path).

- [ ] **Task 2 — Deterministic Drift Analysis rendering** (AC: 2)
  - [ ] Add a "Drift Analysis" section to both templates (`report_template.html`,
        `report_template.docx`) that renders **only when `drift_report` is present**: show
        `overall_severity`, `drift_summary`, and the `recommendations` list. Keep it deterministic
        (no LLM text) — sourced entirely from `DriftReport`.
  - [ ] Update `DocxRenderer`/`PdfRenderer` context construction to pass `drift_report` to the template.
        No change when `drift_report is None` (section absent) — preserves Story 1.5 output for the
        no-baseline path.

- [ ] **Task 3 — Orchestrator drift stage** (AC: 2) `backend/pipeline/orchestrator.py`
  - [ ] Add optional params to `run_full_pipeline`: `dataset_key: str | None = None`,
        `enable_drift: bool = True`, `baseline_dir: str | Path = "backend/baselines"`.
  - [ ] After DQA passes (not halted) and before Insights: if `enable_drift` and `dataset_key` is set,
        call `DriftEngine(baseline_dir=baseline_dir).run(df, dataset_key, pipeline_run_id)`; attach the
        result to `result.drift_report` (may be `None` on first run). Pass it into
        `generate_insights(..., drift_report=result.drift_report)`.
  - [ ] Existing CLI (`python -m backend.pipeline.orchestrator`) behavior is unchanged when
        `dataset_key` is not supplied (drift skipped) — the Reporting Agent is the caller that supplies
        `dataset_key`. Do not change the orchestrator's own Typer CLI surface.
  - [ ] `DriftComputationError` (corrupt baseline / degenerate stats) is a `SavvyCleanseError`
        subclass — it propagates to the agent's error boundary (Task 4), it does not silently pass.

- [ ] **Task 4 — Reporting Agent CLI** `backend/agents/reporting_agent.py` (AC: 1, 3, 4, 5)
  - [ ] Typer app with two commands: `generate` and `schedule`.
  - [ ] `_dataset_key_from_path(input_path) -> str`: sanitized filename stem (lower-cased, non
        `[A-Za-z0-9._-]` → `_`), guaranteed to satisfy `DriftEngine`'s `_SAFE_DATASET_KEY`. This is the
        caller-side derivation 2.3 deferred here.
  - [ ] `_run_once(config, input_path, fmt) -> PipelineResult`: derive dataset_key + output path
        (`{output_dir}/{dataset_key}_{UTC-timestamp}.{ext}`), call `run_full_pipeline(...)`, log
        `report_generated` with `pipeline_run_id`, status, and `output`. Return the result.
  - [ ] `generate(--input, --format)`: `configure_logging()`, load config, resolve format
        (CLI flag overrides `config.output.format`), call `_run_once`. On `SavvyCleanseError`, log +
        `typer.Exit(1)` (matches orchestrator CLI). On halt, `Exit(1)`.
  - [ ] `schedule()`: `configure_logging()`, build an APScheduler `BlockingScheduler`, add a job from
        `report_schedule` (interval → `IntervalTrigger`; cron → `CronTrigger.from_crontab`). The job
        **re-loads `config.yaml`** each fire (hot-reload) and wraps `_run_once` in try/except so any
        `Exception` is logged (`scheduled_run_failed`) and swallowed — the scheduler keeps running.
        Use the first entry of `config.data_sources` as the input.
  - [ ] Agents are thin: no computation here beyond path/format plumbing and scheduler wiring. All
        analysis stays in the pipeline (hard constraint). No LLM calls in the agent (drift/narrative
        LLM use is inside the pipeline behind `LLMClient`).

- [ ] **Task 5 — Dependency** `pyproject.toml`
  - [ ] Add `"apscheduler>=3.10"` to `dependencies` (architecture.md §230, §320 — the prescribed Phase 2
        scheduler; it is a scheduler, not a workflow/orchestration framework, so it is permitted under
        the "no orchestration frameworks" constraint). `uv sync`. Do **not** add scipy/sklearn.

- [ ] **Task 6 — Tests** `backend/tests/test_reporting_agent.py` (AC: 5)
  - [ ] Manual generate happy path: use `typer.testing.CliRunner` (or call the command fn) with a tiny
        CSV fixture written to `tmp_path`, a `config.yaml` in `tmp_path`, and `baseline_dir=tmp_path`;
        assert an output file is written and `report_generated` is logged. Mock the `LLMClient`/
        narrative so no network call occurs (reuse `mock_llm_client` pattern; assert `fallback` path is
        acceptable).
  - [ ] Drift-included pipeline: seed a baseline JSON for the dataset in `tmp_path`, run generate, and
        assert the rendered report contains the Drift Analysis section (assert on the `InsightReport`/
        renderer context carrying `drift_report`, or on rendered HTML text — do not assert on LLM prose).
  - [ ] First run (no baseline): assert `run_full_pipeline` returns a result with `drift_report is None`,
        baseline JSON is created in `tmp_path`, and no Drift Analysis section renders.
  - [ ] Scheduled execution: monkeypatch `BlockingScheduler` (or inject a fake scheduler) so no real
        blocking occurs; assert a job is registered with the interval/cron derived from config and that
        invoking the job calls `_run_once`.
  - [ ] Error recovery: make `_run_once` raise inside a scheduled job; assert the exception is caught,
        `scheduled_run_failed` is logged, and the scheduler is not stopped (job callable returns
        normally).
  - [ ] Every file write scoped to `tmp_path`; never touch the real `backend/baselines/` or `output/`.
        Run `uv run pytest backend/tests/ --ignore=backend/tests/test_parse_file.py` — confirm zero
        regressions vs. the Story 2.3 baseline (154 passed, 1 pre-existing skip) plus the new tests.

## Dev Notes

### Architecture compliance
- `backend/agents/reporting_agent.py` is Presentation layer (architecture.md §745, §751): the ONLY
  place besides `api/` allowed Typer CLI commands. It may import `pipeline/`, `models/`, `config`,
  `core/`; pipeline stages never import from `agents/`.
- Data flow is fixed by architecture.md §754-764: `drift_engine (…→ DriftReport)` →
  `insight_engine (DataFrame + QualityReport + DriftReport → InsightPayload)` → narrative → render.
  Drift is `[Phase 2, optional]` — gated on baseline existence via `DriftEngine.run` returning `None`
  on first run.
- **Design decision (documented):** the guaranteed "Drift Analysis section" (AC2) renders
  **deterministically** from `DriftReport.drift_summary`/`overall_severity`/`recommendations`, which
  2.3 already produces as human-readable text. Drift is still threaded into `InsightPayload` per §760
  (so future stories may let the LLM reference it), but the rendered section does not depend on
  non-deterministic LLM output — this makes AC2/AC5 assertions stable.
- Thin agents (hard constraint): the agent computes nothing analytical; it plumbs paths/format and
  wires the scheduler. No orchestration framework (APScheduler is a scheduler, arch-prescribed).
- LLM only via `backend.core.llm_client` (already true — the agent makes no LLM calls; the narrative
  stage inside the pipeline uses `LLMClient`).

### Contract changes (all additive-optional — permitted; no existing field modified/removed)
- `InsightEngine.generate_insights` gains `drift_report: DriftReport | None = None`.
- `InsightPayload`, `InsightReport` each gain `drift_report: DriftReport | None = None`.
- `run_full_pipeline` gains `dataset_key`, `enable_drift`, `baseline_dir` (all defaulted;
  existing callers/CLI unaffected).

### Existing code (verified against current tree, 2026-07-08)
- `backend/pipeline/orchestrator.py`: `run_full_pipeline` + Typer `app` (do not alter the CLI surface).
- `backend/models/pipeline_result.py`: `drift_report: "DriftReport | None" = None` already present.
- `backend/pipeline/drift_engine.py`: `DriftEngine.run` + `_SAFE_DATASET_KEY` (2.3).
- `backend/pipeline/insight_engine.py`, `narrative_generator.py`, `models/insight_payload.py`,
  `models/insight_report.py`: current signatures captured in Task 1.
- `backend/renderers/`: `DocxRenderer`, `PdfRenderer`, `templates/report_template.{html,docx}`.
- `backend/models/pipeline_config.py`: `PipelineConfig.load`, `report_schedule`, `output`, `data_sources`.

### Testing standards
- Tests in `backend/tests/`; use `structlog.testing.capture_logs()` for event assertions and
  `tmp_path` for all file writes (Story 2.1/2.3 discipline). Mock the LLM (no network). `uv` only.
- Regression baseline: 154 passed, 1 pre-existing skip (`test_parse_file.py` excluded — pre-existing
  fastapi gap on main).

### References
- [Source: epics.md#Story 2.3: Reporting Agent] (AC source; filed as 2.4)
- [Source: architecture.md#L754-L764] (pipeline data flow — drift → insight_engine)
- [Source: architecture.md#L230,L320] (APScheduler as the Phase 2 scheduler)
- [Source: architecture.md#L745,L751] (agents/ = Presentation layer, Typer CLI only)
- [Source: backend/pipeline/orchestrator.py] (run_full_pipeline to extend)
- [Source: backend/pipeline/drift_engine.py] (DriftEngine.run, _SAFE_DATASET_KEY — 2.3)
- [Source: _bmad-output/implementation-artifacts/2-3-drift-engine.md] (drift models + wiring deferral)

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (autonomous Epic 2 build loop, 2026-07-08/09).

### Debug Log References

- Full regression: `uv run pytest backend/tests/ --ignore=backend/tests/test_parse_file.py`
  → 165 passed, 1 skipped, 0 regressions (11 new reporting-agent tests).
- DOCX template drift block verified via a render smoke (drift present, present on
  fallback path, absent when no `drift_report`).

### Completion Notes List

- All 5 ACs met. Drift is wired into the orchestrator (DQA → Drift → Insights →
  Narrative → Render) per architecture.md §754-764 and gated on baseline existence
  via `DriftEngine.run` returning `None` on first run.
- **Design decision (as specced):** the guaranteed Drift Analysis section renders
  deterministically from `DriftReport` (severity/summary/recommendations); drift is
  still threaded into `InsightPayload` per §760 but excluded from the JSON sent to
  the LLM (`model_dump_json(exclude={"drift_report"})`) — the model never sees/sets it.
- All contract changes are additive-optional (`InsightPayload`, `InsightReport`,
  `generate_insights`, `run_full_pipeline`) — no existing field/param modified or
  removed. The orchestrator's own Typer CLI surface is unchanged (drift skipped when
  no `dataset_key`).
- **DOCX template** was hand-patched (Jinja `{% if drift_report %}` block inserted
  into `word/document.xml` before `<w:sectPr>`) since it is a binary template; the
  HTML template got an equivalent section. Both are covered by tests.
- **Environment reconciliation (important, out-of-band but necessary):** `uv run
  pytest` was previously executing under a **pip-populated global Python 3.13.7**
  because `.venv` (uv-managed, 3.14) had no `pytest`. `uv add apscheduler` installs
  into `.venv`, so tests could not see it. Fix: added `pytest`/`pytest-cov` as uv
  **dev deps** and declared `pandera` (used by `data_quality.py` but only ever in
  `requirements.txt`) so `.venv` is self-sufficient and `uv run pytest` now uses it
  (all 154 prior tests still pass under 3.14). → **Backlog note:** `backend/requirements.txt`
  still lists Phase-1 deps (pandera, etc.) not mirrored in `pyproject.toml`; a fuller
  requirements.txt→pyproject reconciliation is worth a dedicated chore.
- APScheduler is a scheduler (not a workflow/orchestration framework) — permitted and
  arch-prescribed (§230, §320). Agent stays thin: no analytical computation, no LLM calls.
- Regression baseline for the next story: **165 passed, 1 pre-existing skip**
  (`anthropic` optional dep), `test_parse_file.py` excluded (pre-existing fastapi gap;
  fastapi is not a pyproject dep).

### File List

- `backend/agents/reporting_agent.py` (new)
- `backend/tests/test_reporting_agent.py` (new)
- `backend/pipeline/orchestrator.py` (drift stage + params)
- `backend/pipeline/insight_engine.py` (drift_report param)
- `backend/pipeline/narrative_generator.py` (server-side drift passthrough)
- `backend/models/insight_payload.py`, `backend/models/insight_report.py` (optional drift_report)
- `backend/renderers/docx_renderer.py`, `backend/renderers/pdf_renderer.py` (drift context)
- `backend/renderers/templates/report_template.docx`, `report_template.html` (Drift Analysis section)
- `pyproject.toml` (+apscheduler, +pandera, +dev pytest/pytest-cov), `uv.lock`
