# Story 3.7: Report Visualizations (Manual Chart Specification)

Status: backlog <!-- Story file drafted 2026-10-16. Promotion to ready-for-dev is a HUMAN decision (AGENTS.md); Q1 (charting dependency) must be answered first. -->

Sizing: L · Model: Sonnet per epic table (Opus recommended for dev — multi-file, renderer + orchestrator + new dependency; see Dev Notes) · loop_eligible: false (L sizing + schema-extending; must stay false)
PREREQUISITES: Story 3.3 (done), Story 3.4 (done), Story 3.5 (done), Story 3.9 (done)
<!-- Sources: epic-3-cleaning-engine.md §3.7 note + INVARIANTS; schema-extensions-spec.md §2; saint-master-prd.md §3.2 tier table ("Visualizations: descriptive + before/after"); prd-epic-reconciliation.md backlog (chart inference = post-Epic-8); Story 3.3/3.4/3.5 story files; current code on main @ 41a32f6. -->

## Story

As an **analyst producing a SAINT report**,
I want **to specify which charts appear in the report — including a before/after comparison of the original data and the cleaned working copy**,
so that **distribution changes and the gaps cleaning did and did not fill are readable at a glance instead of buried in prose**.

## Context and scope

The report today is text-only (DOCX via docxtpl, PDF via Jinja2 + WeasyPrint). Story 3.4 produces a cleaned working copy (`cleaned_df`) and a `CleaningResult`, but the report deliberately describes the ORIGINAL frame (3.4 Q1) — the cleaned frame is "produced and carried" for 3.3/3.6/3.7. This story is the first consumer that compares the two visually.

The epic note is explicit: **the analyst specifies which charts appear — NO auto-selection** (chart inference is a post-Epic-8 backlog item). The free tier receives the before/after cleaning comparison: "340 gaps they CANNOT fill, beside the whitespace they can" is the Starter pitch rendered visually. Tier gating itself is NOT built here (Epic 5 / Story 5.3) — but every chart MUST carry `analysis_class` so 5.3 can gate on the tag instead of a hardcoded chart allowlist (schema-extensions-spec.md §2, CRITICAL).

**In scope**

- An optional, default-empty `visualizations:` section in `config.yaml` (typed in `PipelineConfig`) where the analyst lists chart specs.
- A small, closed set of chart types (below), each tagged `analysis_class: "descriptive"`.
- A deterministic chart-data builder (pure pandas → Pydantic) and a headless image renderer (PNG bytes).
- Additive, backward-compatible `visualizations` field on `InsightReport`, populated server-side AFTER the NarrativeGenerator returns (same pattern as `healing_manifest` / `judgment_required_findings`).
- A conditional "Charts" section in BOTH `report_template.html` and `report_template.docx`.
- A CLI/API-level seam so `run_full_pipeline` accepts the visualization config (mirroring how `cleaning_config` is passed).

**Out of scope**

- Auto-selection / chart inference (post-Epic-8 backlog).
- Tier gating / capability enforcement (Story 5.3). Do not add any tier checks.
- Drift, diagnostic-advanced, predictive, prescriptive, or decision-trace charts (later epics add their own chart types with their own `analysis_class`).
- Re-pointing the report narrative at cleaned data (3.4 Q1 stays as-is).
- Web dashboard charts (Recharts, Epic 4). Frontend is untouched.
- Brand styling beyond a fixed neutral palette (Story 4.12 owns design tokens).
- Notebook export (Story 3.8).

## Chart types (v1 — closed allowlist)

| `chart_type` | Input | Requires cleaning | What it shows |
|---|---|---|---|
| `missing_values_before_after` | `columns` (optional; default = all columns with ≥1 missing value in the ORIGINAL, capped) | yes | Grouped bar per column: missing count in original vs. cleaned working copy. Gaps left unfilled (incl. judgment-required columns) remain visible. |
| `distribution_before_after` | exactly one numeric `column` | yes | Overlaid histograms, original vs. cleaned, **shared bin edges** computed from the original's non-null values. |
| `distribution` | exactly one numeric `column` | no | Histogram of the original column. |
| `top_values` | exactly one `column`, optional `limit` (1–20, default 10) | no | Horizontal bar of the most frequent values in the original (ties broken deterministically by value string). |

All four are `analysis_class: "descriptive"` (PRD §3.2: free tier = "descriptive + before/after"). Adding a chart type later = add an enum member + builder + its `analysis_class`; never a parallel tier list.

## Acceptance Criteria

1. **Schema: every chart carries `analysis_class`.** A new model module `backend/models/visualization.py` defines `AnalysisClass` (Literal or `StrEnum`) with exactly `descriptive | diagnostic_basic | diagnostic_advanced | predictive | prescriptive | decision_trace`, a `ChartType` enum (the four types above), the chart-spec config model, and a `Visualization` output model. `Visualization.analysis_class` is **required** (no default) and validated against the six values. `InsightReport` gains `visualizations: list[Visualization] = Field(default_factory=list)` — existing payloads/reports validate unchanged. `InsightPayload` and `NarrativeContent` are NOT modified.

2. **Analyst-specified only; default produces no charts.** `PipelineConfig` gains an optional `visualizations` section (e.g. `VisualizationConfig` with `charts: list[ChartSpec] = []`). A `config.yaml` with no `visualizations:` key validates unchanged, and a run with no chart specs produces **no Charts section** and a report whose rendered text content is identical to today's (existing renderer/e2e tests pass unmodified). No code path selects charts on its own.

3. **Config validation fails closed at load time.** Unknown `chart_type`, missing/extra column arguments for a type, `limit` outside 1–20, more than **12** chart specs, or duplicate identical specs raise at `PipelineConfig.load` (surfaced as `ConfigurationError`, consistent with Story 3.4 imputation validation). Error messages name the offending config key and allowed values; they never echo dataset content.

4. **Runtime unavailability is reported, not crashed and not silently dropped.** When a valid spec cannot be produced for this run — column not present in the dataset, `distribution*` on a non-numeric or all-null column, or a `*_before_after` chart when cleaning did not run — that chart is omitted and the Charts section lists it as **not produced** with a fixed, client-safe reason from a closed set (e.g. "cleaning was not enabled for this run", "column not found", "column has no numeric values"). Reasons never include exception text, row values, or internal enum/tier names. The pipeline still succeeds.

5. **Before/after reads from the right frames.** `*_before_after` charts compute "before" from the ORIGINAL `df` and "after" from the Story 3.4 `cleaned_df` working copy. The original frame is never mutated (assert in tests). Report narrative/insight stages continue on the original frame (3.4 Q1 unchanged). Columns renamed or dropped by cleaning are handled explicitly (shown as not produced with a client-safe reason, never a KeyError).

6. **Deterministic chart data.** Chart data (bins, counts, ordering, labels) is a pure function of the input frames + spec: identical inputs produce equal `Visualization` data objects. Histogram bin count is fixed (e.g. Freedman–Diaconis is NOT used; use a fixed `bins=20` or a documented deterministic rule) and bin edges are shared between before/after. Category ordering: count desc, then value string asc. No randomness, no wall-clock in chart content.

7. **Headless, bounded, safe image rendering.** Images are rendered to PNG bytes using the approved library (Q1) via its object-oriented API (`Figure` + Agg canvas) — **never `pyplot` global state** (the Reporting Agent runs repeatedly under APScheduler; pyplot leaks figures). Fixed figure size and DPI (≤150); PNG metadata stripped of version/timestamp fields. Bounds: ≤12 charts per report, ≤30 bars/categories per chart (`missing_values_before_after` caps columns at 30 and notes truncation), labels truncated to 40 chars with an ellipsis. Text from the dataset (column names, category values) is rendered **literally**: math-text/TeX parsing is disabled (a column named `$x^2$` renders as those characters, not as math), and no label is ever used to build a file path or URL.

8. **Both formats render the Charts section.** A conditional "Charts" section is added after the existing Data Cleaning / Judgment-Required blocks in BOTH templates. PDF: each chart embedded as `<img src="data:image/png;base64,...">` with a caption (title + "Original data" / "Cleaned working copy" legend wording) — Jinja autoescape stays on; the data URI is built in Python, not from dataset strings; WeasyPrint is never given an external or file URL. DOCX: `docxtpl.InlineImage` from an in-memory buffer at a fixed width; template edited via a one-off `python-docx` script using the established one-Jinja-tag-per-paragraph convention (see Story 3.3 Dev Notes). Not-produced charts are listed in both formats with their reason.

9. **Never reaches the LLM.** `visualizations` is populated in a new orchestrator stage strictly AFTER `NarrativeGenerator().generate(...)` returns and is never routed through `InsightPayload`. A test proves the narrative prompt/payload is unchanged when charts are configured.

10. **Client-safe captions.** Captions and section text use descriptive names. No tier numbers, `remediation_class`, `analysis_class` values, or internal enum names in rendered output. Before/after captions reuse Story 3.9's disclosure language where relevant (working copy; original untouched) by importing from `backend/models/cleaning_disclosure.py` — do not fork that copy.

11. **Typed errors.** Image-rendering failure for one chart → that chart is listed as not produced ("chart could not be rendered") and a structured log event `visualization_render_failed` records chart_type + exception type name (not message, not data). A template/IO failure of the whole report still raises `ReportRenderError` as today. No bare `except Exception: pass`.

12. **Meaningful tests.** At minimum:
    - Model: `analysis_class` required and constrained; `InsightReport` without `visualizations` validates; config without `visualizations:` validates; each AC3 invalid config raises `ConfigurationError`.
    - Builders: exact counts/bins for small hand-computed frames; shared bin edges; deterministic ordering incl. ties; truncation caps; original `df` unchanged after building.
    - Unavailability: each AC4/AC5 reason path, including cleaning-off before/after and a cleaning-dropped column.
    - Rendering: PNG bytes start with the PNG signature; same input twice → same chart data; math-text column name renders without exception; no pyplot import in the module (grep-style test or import check).
    - Both renderers: a configured run produces a Charts section with an embedded image (DOCX: an `InlineShape`/image part present; PDF: render succeeds and HTML contains a `data:image/png;base64,` img); not-produced reasons appear; zero-spec run has no Charts section.
    - Orchestrator/e2e: CLI run with a config containing all four chart types + `--clean` on the existing sample data succeeds; LLM-isolation test (AC9); halted run produces no charts.
    - Existing suites pass unmodified.

13. **Definition of Done.** `uv run pytest`, `npm test`, `npm run build` pass. Run `/security-review` and resolve Critical/High findings. Record test totals, the dependency/licence decision (Q1), and review outcome in the PR. Do not change `loop_eligible` or any ledger field.

## Tasks / Subtasks

- [ ] **Task 0 — Confirm Q1 (dependency) is answered before writing code.** If not, HALT.
- [ ] **Task 1 — Models (AC1, AC3)**
  - [ ] `backend/models/visualization.py`: `AnalysisClass`, `ChartType`, `ChartSpec` (with per-type validator), `VisualizationConfig` (≤12, no duplicates), `ChartData`/`Visualization` output, `NotProducedChart` (closed reason enum + client-safe text map).
  - [ ] `backend/models/pipeline_config.py`: `visualizations: VisualizationConfig = Field(default_factory=VisualizationConfig)` on `PipelineConfig`.
  - [ ] `backend/models/insight_report.py`: `visualizations` (+ `charts_not_produced`) with a comment matching the 3.3/3.5 "populated server-side, never via InsightPayload" style.
- [ ] **Task 2 — Chart-data builder (AC4–AC6)** — `backend/pipeline/visualization_builder.py`: pure functions `(df_original, df_cleaned | None, VisualizationConfig) -> (list[ChartData], list[NotProducedChart])`. No I/O, no plotting.
- [ ] **Task 3 — Image renderer (AC7, AC11)** — `backend/renderers/chart_images.py`: `ChartData -> bytes` via OO API, Agg canvas, fixed palette (colour-blind-safe pair, e.g. grey `#7f7f7f` original / blue `#1f77b4` cleaned, also distinguished by hatch or alpha so it reads in greyscale print), `text.parse_math=False` / `usetex=False` via per-figure rcParams context, PNG metadata stripped.
- [ ] **Task 4 — Orchestrator wiring (AC5, AC9)** — `run_full_pipeline(..., visualization_config: VisualizationConfig | None = None)`; new **Stage 4d** after 4c: build + render, attach to `insight_report`. Halt path returns before this (no charts). CLI: load from `config.yaml` via the existing config path; no new CLI flags required (state in PR if a flag was added and why).
- [ ] **Task 5 — Templates (AC8, AC10)** — `report_template.html` (direct edit, `{% if visualizations or charts_not_produced %}` block) and `report_template.docx` (one-off `python-docx` script, append after the last existing block, one Jinja tag per paragraph). Renderers add the new context keys; DOCX renderer converts PNG bytes → `InlineImage(doc, BytesIO(png), width=Mm(160))` at render time (the model holds bytes or base64, not docxtpl objects).
- [ ] **Task 6 — Config docs** — commented example `visualizations:` block in `config.yaml` (all four types, commented out so default behaviour is unchanged).
- [ ] **Task 7 — Tests (AC12)** — `backend/tests/test_visualization_models.py`, `test_visualization_builder.py`, `test_chart_images.py`; extend `test_renderers.py`; `backend/tests/e2e/test_visualizations_wiring.py`.
- [ ] **Task 8 — DoD (AC13).**

## Dev Notes

### Architecture compliance
- Layering (architecture.md §482-506, §745): models in `backend/models/`, pure builder in `backend/pipeline/`, image rendering in `backend/renderers/`. Pipeline must not import `api/`. Orchestrator may import models/renderers/pipeline.
- Pydantic at every stage boundary; no `dict`/`Any` for chart data (project-context.md). Use structlog; never `print()`.
- Follow the 3.3/3.5 server-side-population pattern exactly — `InsightReport` fields filled after the narrative stage, never through `InsightPayload` (see comments in `backend/models/insight_report.py`).
- Story 3.4 Q1: report stages stay on the ORIGINAL frame. Charts are the only place the cleaned frame is visualised.
- Epic 3 INVARIANTS: original data never modified; cleaning default OFF (charts must not turn it on — a before/after spec with cleaning off is "not produced", never an implicit enable).

### Library / dependency (see Q1)
- No Python plotting library is installed today (`pyproject.toml`). Architecture "New Dependencies Per Phase" has none for charts. Recommendation: **matplotlib 3.11.x** (latest 3.11.2 on PyPI as of 2026-10-16; requires Python ≥3.11; Matplotlib License, PSF-based/BSD-compatible). Headless via Agg; pulls numpy (already transitive via pandas), pillow (already a direct dep), contourpy, cycler, fonttools, kiwisolver, pyparsing, python-dateutil, packaging.
- Alternative with **zero new deps**: hand-emit SVG (WeasyPrint renders SVG natively) — but python-docx cannot embed SVG, so DOCX would need a Pillow-drawn PNG path; two renderers, more code, worse output. Not recommended.
- Do NOT use plotly/kaleido (headless Chrome dependency) or seaborn (unnecessary).
- matplotlib writes a font cache under `MPLCONFIGDIR` (default user home). In tests/CI this is fine; do not set it to a repo path.

### Security / hostile input
- Column names and category values are client-controlled. Disable math-text and TeX; truncate; render as text only. Never interpolate them into HTML outside Jinja autoescape — captions go through the template, only the base64 PNG is built in Python.
- WeasyPrint 70 (PR #57) — keep `HTML(string=...)` with no `base_url`; the only embedded resources are `data:` PNGs we produced.
- Cap work: ≤12 charts, ≤30 categories, fixed bins, fixed DPI — a 500 MB file must not produce an unbounded figure.

### Docx template editing
- `report_template.docx` is binary; cannot be edited with `Edit`. Inspect and append with `python-docx` exactly as Story 3.3 Dev Notes describe (`_bmad-output/implementation-artifacts/3-3-healing-manifest.md` §Dev Notes). Image insertion in docxtpl: put `{{ chart.image }}` alone in a run/paragraph; build `InlineImage` objects in `DocxRenderer` from the model's bytes.

### Testing standards
- pytest under `backend/tests/` (unit) and `backend/tests/e2e/` (CLI/wiring, `@pytest.mark.e2e` where existing tests do). PDF tests already tolerate WeasyPrint native-lib absence on Windows the same way existing `test_renderers.py` does — mirror it.
- Don't assert PNG byte-equality across platforms; assert chart *data* equality and PNG validity.

### Previous story intelligence
- 3.3 review found renderers omitting required per-entry fields (blocking) — assert specific content lands in BOTH formats, not just "section present".
- 3.3 found a fail-open exception path and raw-exception leakage into client output — AC4/AC11 reasons are a closed set for this reason.
- 3.6 found validation ordered AFTER expensive work — validate chart config at load time (AC3), before the pipeline runs.
- 3.9 created the canonical client copy in `backend/models/cleaning_disclosure.py`; import, don't duplicate.

### Project Structure Notes
- New: `backend/models/visualization.py`, `backend/pipeline/visualization_builder.py`, `backend/renderers/chart_images.py`, tests as listed.
- Modified: `backend/models/insight_report.py`, `backend/models/pipeline_config.py`, `backend/pipeline/orchestrator.py`, `backend/renderers/docx_renderer.py`, `backend/renderers/pdf_renderer.py`, both templates, `config.yaml` (comments only), `pyproject.toml` + `uv.lock` (if Q1 approved), `backend/tests/test_renderers.py`.
- Not touched: `backend/models/insight_payload.py`, narrative generator, cleaning engine/policy/coordinator, frontend, `agent-system/`, ledger.

### References
- [Source: _bmad-output/implementation-artifacts/epic-3-cleaning-engine.md#Story notes — 3.7; #INVARIANTS]
- [Source: _bmad-output/implementation-artifacts/schema-extensions-spec.md#2. Insight Engine visualizations — analysis_class]
- [Source: _bmad-output/planning-artifacts/saint-master-prd.md §3.2 tier table — "Visualizations: descriptive + before/after"]
- [Source: _bmad-output/implementation-artifacts/prd-epic-reconciliation.md#Backlog — chart inference (option c), post-Epic-8]
- [Source: _bmad-output/implementation-artifacts/3-4-opt-in-gate-config.md — Q1 report-on-original]
- [Source: _bmad-output/implementation-artifacts/3-3-healing-manifest.md#Dev Notes — DOCX template editing]
- [Source: backend/models/insight_report.py; backend/pipeline/orchestrator.py Stages 4–5; backend/renderers/*]

## Open questions (resolve before promotion to ready-for-dev)

- **Q1 — Charting dependency (BLOCKING).** Approve adding `matplotlib>=3.11,<3.12` as a runtime dependency (architecture "New Dependencies Per Phase" would gain an Epic 3 row)? If no, the zero-dep SVG + Pillow path is the fallback and sizing grows.
- **Q2 — Default columns for `missing_values_before_after`.** Proposed: all columns with ≥1 missing value in the original, capped at 30 (sorted by missing count desc, then name). Confirm or require explicit columns.
- **Q3 — Dev model.** Epic table says Sonnet; given new dependency + both renderers + orchestrator stage, Opus/high is recommended for dev with Sonnet for review (per model-selection guidance). Your call.

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
