# Story 2.3: Drift Engine

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

> 🔢 **Numbering reconciliation — epics.md sequence vs. actually-filed stories (READ FIRST for future
> story creation).** epics.md's Epic 2 numbering has diverged from the real story history because an
> LLM-client story was filed out-of-band (on 2026-07-02) as a hard prerequisite for the agents, taking
> the `2.2` slot and pushing everything after it down by one. The **filed** numbering below is
> authoritative — `sprint-status.yaml` and the story files on disk follow it, and epics.md's original
> numbers should be read through this map, not literally:
>
> | epics.md original | Filed story (authoritative) | Status | Note |
> |---|---|---|---|
> | Story 2.1 — Configuration Layer | `2-1-configuration-layer` | done | 1:1 |
> | — (no epics.md entry) | `2-2-llm-client-abstraction` | done | Inserted out-of-band 2026-07-02: LLM resilience extracted so 2.4/2.5 agents can call an LLM through one abstraction |
> | — (no epics.md entry) | `2-2b-harden-llm-client-multi-caller-use` | done | Corrective follow-up from 2-2's code review (multi-caller hardening) |
> | Story 2.2 — Drift Engine | **`2-3-drift-engine` (this story)** | ready-for-dev | Renumbered 2.2 → 2.3 |
> | Story 2.3 — Reporting Agent | `2-4-reporting-agent` (not yet filed) | backlog | Renumbered 2.3 → 2.4 |
> | Story 2.4 — Monitoring Agent & Alert Delivery | `2-5-monitoring-agent-alert-delivery` (not yet filed) | backlog | Renumbered 2.4 → 2.5 |
>
> When these ACs or Dev Notes cite "epics.md Story 2.2", that is **this** Drift Engine story. Citations
> to the Reporting/Monitoring agents use their **filed** numbers (2.4 / 2.5) with the epics.md original
> in parentheses where it aids traceability.
>
> 🧭 **Sequencing rationale — Drift Engine (2.3) before Reporting Agent (2.4).** This is a PRD pipeline
> dependency, not a numbering artifact. architecture.md's pipeline data-flow places the drift stage
> (`drift_engine.py … [Phase 2, optional]`) *inside* the sequence the Reporting Agent orchestrates
> (DQA → **Drift** → Insights → Narrative → Render), and epics.md's Reporting Agent AC hard-depends on
> it: "if a baseline profile exists for this dataset, the Drift Engine is included in the pipeline and
> the report contains a Drift Analysis section." The Reporting Agent (2.4) cannot be implemented or
> tested against its ACs until `DriftEngine` exists — so Drift Engine ships first.
>
> ⚠️ **Scope clarification — read before coding.** There are two *different* threshold concepts in this
> codebase; do not conflate them:
> - `PipelineConfig.metric_thresholds` (`backend/models/pipeline_config.py`, Story 2.1) — **user-configurable**
>   per-metric fractional thresholds (e.g. `revenue: 0.15`), consumed by the **Monitoring Agent (2.5)**
>   for period-over-period alert rules.
> - The Drift Engine's HIGH/MEDIUM/LOW severity bands (mean shift >30%/>15%/>5%, etc.) are **fixed
>   constants defined in architecture.md** (table below), per epics.md AC: "classified by severity …
>   using the thresholds defined in the Architecture document." They are **not** read from
>   `config.yaml` and the Drift Engine must **not** import `PipelineConfig`.

## Story

As a developer,
I want a stateless computation module that compares a current DataFrame against a baseline profile and detects distributional drift across 7 checks,
so that the Reporting Agent can include drift analysis in reports and the Monitoring Agent can trigger drift-based alerts.

## Acceptance Criteria

1. **Core computation.** Given a current DataFrame and an existing `BaselineProfile` (Pydantic model
   with per-column mean, median, std, quartiles, null%, categorical distributions, schema fingerprint),
   when `DriftEngine.compute_drift(current_df, baseline_profile)` is called, then the engine runs 7
   detection checks — mean shift, median shift, variance shift, volume drift, categorical PSI
   (Population Stability Index), new/missing categories, and schema drift — each finding is classified
   HIGH/MEDIUM/LOW using the fixed thresholds in architecture.md (table in Dev Notes), and the return
   type is a Pydantic-validated `DriftReport` with sections: `volume_drift`, `numeric_drift`,
   `categorical_drift`, `schema_drift`, `drift_summary`, `overall_severity`, `recommendations`.

2. **First-run baseline creation.** Given a dataset being analyzed for the first time (no baseline
   exists), when the Drift Engine is invoked, then a `BaselineProfile` is computed from the current
   DataFrame and saved as a JSON file in `backend/baselines/`, drift computation is skipped (no
   comparison possible, no `DriftReport` produced), and a structlog entry is emitted with
   `event="baseline_created"`.

3. **Auto-rotation after 4 clean runs.** Given 4 consecutive pipeline runs with no HIGH-severity drift
   findings, when the 4th clean run completes, then the current DataFrame's profile replaces the
   existing baseline (auto-rotation), `consecutive_clean_runs` resets to 0, and a structlog entry is
   emitted with `event="baseline_rotated"`.

4. **Counter reset on HIGH finding.** Given a HIGH-severity drift finding in any run, when the finding
   is detected, then `consecutive_clean_runs` resets to 0 and the existing baseline is retained
   (unchanged on disk except for the counter reset).

5. **Stateless, side-effect-scoped, observable.** Given any drift computation, when it completes, then
   the `DriftReport` is Pydantic-validated before return; the Drift Engine has no side effects beyond
   baseline file I/O (it does not send alerts, halt the pipeline, or run on a schedule); structlog
   entries include `pipeline_run_id`, `stage="drift_engine"`, columns checked, and findings count; and
   `backend/tests/test_drift_engine.py` passes with tests covering: each of the 7 checks in isolation,
   first-run baseline creation, baseline auto-rotation after 4 clean runs, rotation counter reset on a
   HIGH finding, and schema drift detection.

## Tasks / Subtasks

- [ ] **Task 0 — Verify assumptions against the current tree before writing any code** (all ACs)
  - [ ] Confirm these files do **not** yet exist: `backend/models/drift_report.py`,
        `backend/pipeline/drift_engine.py`. Confirm `backend/baselines/` exists but is empty (only
        `.gitkeep`).
  - [ ] Confirm `backend/models/pipeline_result.py:31-32` already has a `TYPE_CHECKING`-guarded forward
        reference `from backend.models.drift_report import DriftReport` and a
        `drift_report: "DriftReport | None" = None` field — your new module's class name and path
        **must** match this exactly (`DriftReport` in `backend.models.drift_report`), or the forward
        reference stays broken.
  - [ ] Confirm `backend/errors/exceptions.py:92-97` already defines `DriftComputationError(PipelineStageError)`
        — reuse it; do not create a new exception class.
  - [ ] Confirm `backend/models/quality_report.py:16-22` already defines a `Severity(str, Enum)` with
        `CRITICAL/HIGH/MEDIUM/LOW`. Reuse this enum for drift severity (do not define a parallel
        `DriftSeverity` enum) — the Drift Engine only ever produces `HIGH`/`MEDIUM`/`LOW` (never
        `CRITICAL`; drift is informational, never a halt condition).
  - [ ] Confirm `backend/pipeline/insight_engine.py`'s `generate_insights()` does **not** currently
        accept a drift parameter, and `backend/pipeline/orchestrator.py`'s `run_full_pipeline()` does
        **not** currently call a drift stage. **Both are out of scope for this story** — wiring
        `drift_engine.py` into the orchestrator/insight-engine data flow is the Reporting Agent's job
        (filed 2.4; epics.md Story 2.3), per architecture.md's data-flow diagram which marks the drift
        stage `[Phase 2, optional]` and the Reporting Agent AC ("Reporting Agent … invokes the pipeline
        orchestrator … if a baseline
        profile exists … the Drift Engine is included in the pipeline"). This story delivers the
        `DriftEngine` class and its models only.
  - [ ] Confirm `scipy` is present in `backend/requirements.txt` but **absent** from `pyproject.toml`
        `dependencies` (same pre-existing pyproject/requirements.txt drift pattern Story 2.1 partially
        reconciled for other deps — see Dev Notes).

- [ ] **Task 1 — Define Pydantic models** `backend/models/drift_report.py` (AC: 1, 2)
  - [ ] `ColumnBaselineStats(BaseModel)` — per-column statistical snapshot: `dtype: str`,
        `null_pct: float`, and for numeric columns `mean: float | None`, `median: float | None`,
        `std: float | None`, `q25: float | None`, `q75: float | None`; for categorical/object columns
        `category_distribution: dict[str, float] | None` (value → proportion of non-null rows, sums to
        ~1.0).
  - [ ] `BaselineProfile(BaseModel)` — `dataset_key: str`, `row_count: int`,
        `columns: dict[str, ColumnBaselineStats]`, `consecutive_clean_runs: int = 0`,
        `created_at: str` (ISO 8601 UTC), `updated_at: str` (ISO 8601 UTC).
  - [ ] `DriftFinding(BaseModel)` — one classified observation: `check: str` (e.g. `"mean_shift"`),
        `column: str | None` (None for dataset-level checks like volume/schema drift),
        `severity: Severity` (reused from `quality_report.py` — HIGH/MEDIUM/LOW only, never CRITICAL),
        `actual_value: float`, `detail: str`.
  - [ ] `VolumeDrift(BaseModel)` — `current_row_count: int`, `baseline_row_count: int`,
        `pct_change: float`, `finding: DriftFinding | None` (None if below LOW threshold).
  - [ ] `NumericColumnDrift(BaseModel)` — `column: str`, `mean_shift: DriftFinding | None`,
        `median_shift: DriftFinding | None`, `variance_shift: DriftFinding | None`.
  - [ ] `CategoricalColumnDrift(BaseModel)` — `column: str`, `psi: DriftFinding | None`,
        `new_categories: list[str]`, `missing_categories: list[str]`,
        `category_findings: list[DriftFinding]` (new/missing-category findings, if any crossed a
        threshold).
  - [ ] `SchemaDrift(BaseModel)` — `columns_added: list[str]`, `columns_removed: list[str]`,
        `dtype_changes: dict[str, str]` (column → `"was X, now Y"`), `finding: DriftFinding | None`
        (always HIGH if `columns_added`/`columns_removed`/`dtype_changes` is non-empty, per
        architecture's "Always HIGH" rule).
  - [ ] `DriftReport(BaseModel)` — `pipeline_run_id: str`, `computed_at: str` (ISO 8601 UTC),
        `volume_drift: VolumeDrift`, `numeric_drift: list[NumericColumnDrift]`,
        `categorical_drift: list[CategoricalColumnDrift]`, `schema_drift: SchemaDrift`,
        `drift_summary: str` (one-line human-readable rollup), `overall_severity: Severity` (max
        severity across all findings; `LOW` if none), `recommendations: list[str]`.
  - [ ] Match existing Pydantic style (`backend/models/quality_report.py`,
        `backend/models/insight_payload.py`): `from __future__ import annotations`, module docstring,
        PascalCase noun models, snake_case fields, `X | None = None` optionals.

- [ ] **Task 2 — Baseline persistence** `backend/pipeline/drift_engine.py` (AC: 2, 3, 4)
  - [ ] `DriftEngine.__init__(self, baseline_dir: str | Path = "backend/baselines")` — accept an
        override so tests can point at `tmp_path` instead of the real repo-root `backend/baselines/`.
  - [ ] `_baseline_path(dataset_key: str) -> Path` → `{baseline_dir}/{dataset_key}.json`. `dataset_key`
        is an opaque caller-supplied string (e.g. a sanitized filename stem) — **do not** derive it from
        a file path inside this module; that derivation belongs to the caller (Reporting Agent, 2.4).
  - [ ] `_load_baseline(dataset_key) -> BaselineProfile | None` — return `None` if the file doesn't
        exist (first-run case). If the file exists but fails JSON parse or Pydantic validation, raise
        `DriftComputationError` (corrupt baseline is an infrastructure failure per
        `errors/exceptions.py:92-97`'s own docstring example — "baseline file corrupt").
  - [ ] `_build_profile(df: pd.DataFrame, dataset_key: str, *, consecutive_clean_runs: int = 0) -> BaselineProfile`
        — compute the per-column stats (numeric: mean/median/std/q25/q75/null_pct; categorical:
        value_counts normalized to proportions/null_pct) and `row_count`.
  - [ ] `_save_baseline(dataset_key, profile: BaselineProfile) -> None` — write pretty-printed JSON
        (`model_dump_json(indent=2)` or equivalent) to `_baseline_path(dataset_key)`, creating
        `baseline_dir` if it doesn't exist.

- [ ] **Task 3 — Stateless drift computation** `DriftEngine.compute_drift` (AC: 1, 5)
  - [ ] Pure function of `(current_df, baseline_profile) -> DriftReport` — **no file I/O, no baseline
        mutation inside this method.** Raise `DriftComputationError` if `current_df` is empty or a
        stats computation degenerates (e.g. `baseline_std == 0` making variance-shift ratio undefined —
        treat as a defined edge case, not a silent `inf`/`NaN` in the output).
  - [ ] Implement the 7 checks per architecture.md's table (reproduced below) — apply each threshold to
        the **absolute value** of the relative change for mean/median shift (drift can go either
        direction):

        | Check | Formula | HIGH | MEDIUM | LOW |
        |-------|---------|------|--------|-----|
        | Mean shift | `abs((curr_mean - base_mean) / base_mean)` | >30% | >15% | >5% |
        | Median shift | Same formula on medians | >30% | >15% | >5% |
        | Variance shift | `curr_std / base_std` | >2.0 or <0.5 | >1.5 or <0.67 | — |
        | Volume drift | `abs((len(curr) - len(base)) / len(base))` | >50% | >20% | >10% |
        | Categorical PSI | `Σ (curr% - base%) × ln(curr% / base%)` | >0.25 | 0.10–0.25 | <0.10 |
        | New/missing categories | Set comparison + representation % | Missing >10% repr | New >5% repr | — |
        | Schema drift | Column set + dtype comparison | Always HIGH | — | — |

  - [ ] **PSI edge case:** categories present in only one of curr/base produce `curr% = 0` or
        `base% = 0`, which breaks `ln(0)` / division-by-zero. Apply a small epsilon (e.g. `0.0001`) to
        both proportions before the formula — standard PSI practice, not a novel design choice, so use
        the same epsilon convention across all category pairs for reproducible test assertions.
  - [ ] Numeric checks (mean/median/variance) run only on columns that are numeric in **both** baseline
        and current and are not already flagged by schema drift as added/removed/dtype-changed.
        Categorical checks (PSI, new/missing) run only on columns categorical in both. A column present
        in one but not the other is a schema-drift concern only — do not also emit a numeric/categorical
        finding for it.
  - [ ] `overall_severity` = the highest severity present across `volume_drift`, all `numeric_drift`,
        all `categorical_drift`, and `schema_drift` findings; `Severity.LOW` if nothing crossed any
        threshold. (Never `CRITICAL` — see Task 0.)
  - [ ] `recommendations`: 1 short actionable string per HIGH finding (e.g. `"Investigate revenue mean
        shift (+32% vs baseline) before trusting this period's report"`) — keep it data-driven text
        generation (string templates), **not** an LLM call. The Drift Engine never touches
        `backend.core.llm_client`.
  - [ ] Emit `structlog.get_logger().info("drift_computed", pipeline_run_id=..., stage="drift_engine",
        columns_checked=<int>, findings_count=<int>, overall_severity=...)` on every `compute_drift`
        call.

- [ ] **Task 4 — Orchestrating entry point + rotation** `DriftEngine.run` (AC: 2, 3, 4, 5)
  - [ ] `DriftEngine.run(self, current_df: pd.DataFrame, dataset_key: str, pipeline_run_id: str) -> DriftReport | None`
        — the one method a future caller (Reporting Agent, 2.4) invokes:
        1. `_load_baseline(dataset_key)`. If `None` (first run): build a fresh profile via
           `_build_profile`, `_save_baseline`, log `event="baseline_created"` with `pipeline_run_id`
           and `dataset_key`, **return `None`** (no `DriftReport` — nothing to compare against).
        2. Otherwise: call `compute_drift(current_df, baseline)`.
        3. If `overall_severity == Severity.HIGH`: reset `baseline.consecutive_clean_runs = 0`,
           `_save_baseline` (counter change only, profile stats untouched), do **not** rotate.
        4. Else (no HIGH finding): increment `baseline.consecutive_clean_runs`. If it reaches `4`:
           rebuild the profile from `current_df` via `_build_profile(..., consecutive_clean_runs=0)`,
           `_save_baseline`, log `event="baseline_rotated"` with `pipeline_run_id` and `dataset_key`
           (counter reset to 0 as part of the new profile). Otherwise just `_save_baseline` the
           incremented counter on the **existing** profile (no rotation yet).
        5. Return the computed `DriftReport`.
  - [ ] This is the only method that performs baseline file I/O outside of first-run creation — keep
        `compute_drift` itself free of it (Task 3).

- [ ] **Task 5 — Dependency reconciliation** `pyproject.toml` (Task 0 finding)
  - [ ] Add `"scipy>=1.11"` to `pyproject.toml` `dependencies` (already present in
        `backend/requirements.txt`; this closes the same kind of pre-existing drift Story 2.1 partially
        reconciled — do not touch any other pre-existing pyproject/requirements.txt mismatches, out of
        scope here same as it was for 2.1). Verify with:
        `grep -in scipy pyproject.toml backend/requirements.txt`.
  - [ ] Using `scipy.stats` is optional — the PSI/variance formulas above are simple enough for
        `math`/`numpy` directly. Add the dependency regardless, since architecture.md §230 names it as
        the Phase 2 addition "for PSI computation" and a future story may rely on it being declared.

- [ ] **Task 6 — Tests** `backend/tests/test_drift_engine.py` (AC: all)
  - [ ] Add net-new fixtures to `backend/tests/conftest.py` (additive only, per its own docstring rule —
        do not mutate `clean_sales_df`/`dirty_sales_df`): a baseline-profile fixture built from
        `clean_sales_df`, and a "drifted" DataFrame variant (e.g. `revenue` scaled up ~40% to force a
        HIGH mean-shift) for exercising each severity band deterministically.
  - [ ] Cover each of the 7 checks in isolation (construct minimal current-df/baseline pairs that
        isolate exactly one check crossing a threshold at a time).
  - [ ] Cover first-run baseline creation: no existing file at `tmp_path`-scoped `baseline_dir` →
        `run()` returns `None`, a JSON file is written, `event="baseline_created"` fires (assert via
        `structlog.testing.capture_logs()`, matching the pattern `test_config.py` established for
        `config_loaded`).
  - [ ] Cover auto-rotation: seed a baseline JSON with `consecutive_clean_runs=3`, run a clean current
        df, assert the baseline file now reflects the **new** profile (built from the just-run current
        df) with `consecutive_clean_runs=0`, and `event="baseline_rotated"` fires.
  - [ ] Cover counter reset on HIGH finding: seed `consecutive_clean_runs=2`, run a heavily-drifted
        current df (HIGH finding), assert the baseline file's **stats are unchanged** but
        `consecutive_clean_runs` is back to `0`.
  - [ ] Cover schema drift: current df with a column added/removed/dtype-changed vs. baseline → always
        HIGH, and confirm numeric/categorical checks are skipped for the mismatched column(s) (Task 3).
  - [ ] Cover the `DriftComputationError` path: corrupt baseline JSON on disk → `run()` raises
        `DriftComputationError`, not a raw `json.JSONDecodeError`/`ValidationError`.
  - [ ] Use `tmp_path` for every baseline file write — never touch the real repo-root
        `backend/baselines/` in tests (same rule Story 2.1 enforced for `config.yaml`).
  - [ ] Run `uv run pytest backend/tests/test_drift_engine.py -v`, then the full regression command
        `uv run pytest backend/tests/ --ignore=backend/tests/test_parse_file.py` and confirm zero
        regressions against the Story 2.1 baseline (133 passed, 1 pre-existing skip) plus your new
        tests.

## Dev Notes

### Architecture compliance

- **Layer:** `backend/pipeline/drift_engine.py` and `backend/models/drift_report.py` are both Business
  Logic layer (`pipeline/`, `models/` per architecture.md:743-747). May import `errors/`, `models/`,
  stdlib, pandas/numpy/scipy. Must **not** import from `api/`, `agents/`, `renderers/`, or any legacy
  module (`advanced_pipeline.py`, `comprehensive_analytics.py`, `nlp_processor.py`, `analytics.py`,
  `main.py`, `main_enhanced.py`, `dashboard_api.py`). Must **not** import `backend.pipeline.config` /
  `PipelineConfig` — see the scope clarification banner at the top of this story.
- **Stateless-with-scoped-I/O:** epics.md AC5 is explicit — "no side effects beyond baseline file I/O
  — it does not send alerts, halt the pipeline, or run on a schedule." `compute_drift` itself must have
  zero I/O (Task 3); all file I/O lives in `run`/`_load_baseline`/`_save_baseline` (Task 2/4).
- **Result-vs-Exception split** (`backend/errors/exceptions.py` docstring): a HIGH drift finding is a
  normal, expected outcome — it is carried on `DriftReport.overall_severity`, never raised as an
  exception. `DriftComputationError` is reserved for infrastructure failures (corrupt baseline file,
  degenerate stats) per its existing docstring.
- **Pydantic for all pipeline I/O:** `DriftReport` and `BaselineProfile` are Pydantic `BaseModel`s
  (not the `PipelineResult` dataclass exception — that exception is documented in
  `backend/models/pipeline_result.py` and applies only to `PipelineResult` itself).

### Existing code you are extending (verified against current tree, 2026-07-05)

- `backend/models/pipeline_result.py:26-33,58-60` already has the `drift_report: "DriftReport | None"`
  field wired up under `TYPE_CHECKING`, forward-referencing exactly
  `backend.models.drift_report.DriftReport` — this story's Task 1 fulfills that forward reference. No
  changes to `pipeline_result.py` are needed or in scope.
- `backend/errors/exceptions.py:92-97` — `DriftComputationError(PipelineStageError)` already exists
  with a docstring naming this exact use case. Reuse it; do not add a new exception.
- `backend/models/quality_report.py:16-22` — `Severity(str, Enum)` with `CRITICAL/HIGH/MEDIUM/LOW`
  already exists. Reuse it for `DriftFinding.severity` / `DriftReport.overall_severity` (never emit
  `CRITICAL` from the Drift Engine).
- `backend/pipeline/orchestrator.py` and `backend/pipeline/insight_engine.py` are **not** touched by
  this story (Task 0) — their drift integration is the Reporting Agent's scope (filed 2.4), confirmed against
  architecture.md's data-flow diagram (`drift_engine.py … [Phase 2, optional]`).
- `backend/baselines/` already exists (empty, `.gitkeep` only) — this is where baseline JSON files land
  (architecture.md:166, :617).
- `backend/tests/conftest.py` already provides `clean_sales_df`/`dirty_sales_df`/`pipeline_run_id`
  fixtures and a session-autouse `configure_logging()` fixture; extend it additively (its own docstring
  rule) rather than duplicating fixtures in the new test file.

### Baseline JSON shape (illustrative)

```json
{
  "dataset_key": "sales_weekly",
  "row_count": 500,
  "columns": {
    "revenue": {
      "dtype": "float64",
      "null_pct": 0.0,
      "mean": 2500.0,
      "median": 2400.0,
      "std": 350.0,
      "q25": 2100.0,
      "q75": 2800.0,
      "category_distribution": null
    },
    "region": {
      "dtype": "object",
      "null_pct": 0.0,
      "mean": null,
      "median": null,
      "std": null,
      "q25": null,
      "q75": null,
      "category_distribution": {"north": 0.25, "south": 0.25, "east": 0.25, "west": 0.25}
    }
  },
  "consecutive_clean_runs": 2,
  "created_at": "2026-06-01T00:00:00Z",
  "updated_at": "2026-07-01T00:00:00Z"
}
```

### Testing standards (project-context.md; conftest.py)

- Tests live in `backend/tests/` (not co-located) — new file `backend/tests/test_drift_engine.py`
  (mirror rule: tests `pipeline/drift_engine.py` + `models/drift_report.py`).
- Use `structlog.testing.capture_logs()` to assert on `baseline_created`/`baseline_rotated`/
  `drift_computed` events — same pattern `test_config.py` established for `config_loaded` (Story 2.1).
- Regression baseline: Story 2.1 left the suite at 133 passed, 1 pre-existing skip (`test_parse_file.py`,
  unrelated `anthropic`-missing skip). Run
  `uv run pytest backend/tests/ --ignore=backend/tests/test_parse_file.py` and confirm zero regressions
  plus your new `test_drift_engine.py` tests passing.
- `uv` only — `uv run pytest ...`. No bare `pytest`, no `pip install`.

### Project Structure Notes

- New files: `backend/models/drift_report.py`, `backend/pipeline/drift_engine.py`,
  `backend/tests/test_drift_engine.py`.
- Modified: `backend/tests/conftest.py` (additive fixtures only), `pyproject.toml` (+`scipy`).
- No variance from the architecture target tree — both new files appear in it verbatim
  (architecture.md:149, :155, :589, :597).
- `backend/baselines/` is the fixed storage root in production; tests must override via
  `DriftEngine(baseline_dir=tmp_path)` and never touch the real directory.

### Definition of Done (sprint-status.yaml, applies from Story 1.4 onward)

- All acceptance criteria met; unit tests pass; zero regressions in `uv run pytest backend/tests/`.
- Run `/security-review` and resolve all Critical/High findings before marking done. Pay attention to:
  baseline JSON deserialization safety (use `json.loads` + Pydantic validation, never `eval`/`pickle`),
  and that baseline files never capture PII beyond what the source CSV already contained (category
  values are stored verbatim — flag if source columns could contain free-text PII, but no new PII
  surface is introduced by this story beyond what Story 1.2's DQA already reads).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2: Drift Engine] (AC source, lines 436-472)
- [Source: _bmad-output/planning-artifacts/architecture.md#L149,L155] (target file locations:
  `pipeline/drift_engine.py`, `models/drift_report.py`)
- [Source: _bmad-output/planning-artifacts/architecture.md#L189,L198-L199,L201-L223] (Drift Engine
  specification, 7-check threshold table, integration notes, explicit non-goals)
- [Source: _bmad-output/planning-artifacts/architecture.md#L230] (scipy.stats — Phase 2 new dependency)
- [Source: _bmad-output/planning-artifacts/architecture.md#L433,L486-L506] (compute_drift signature;
  Result-vs-Exception dual strategy)
- [Source: _bmad-output/planning-artifacts/architecture.md#L743-L747,L754-L764] (three-layer boundaries;
  pipeline data-flow diagram — drift stage marked Phase 2/optional, wired by the Reporting Agent, filed 2.4)
- [Source: _bmad-output/planning-artifacts/architecture.md#L875] (consecutive_clean_runs rotation
  counter — gap-analysis resolution)
- [Source: backend/models/pipeline_result.py#L26-L33,L58-L60] (existing forward reference this story
  fulfills)
- [Source: backend/errors/exceptions.py#L92-L97] (DriftComputationError — reuse, do not recreate)
- [Source: backend/models/quality_report.py#L16-L22] (Severity enum — reuse for drift severity)
- [Source: backend/tests/conftest.py] (existing fixtures to extend additively)
- [Source: _bmad-output/implementation-artifacts/2-1-configuration-layer.md] (previous Epic 2 story —
  established the pyproject.toml/requirements.txt reconciliation pattern this story follows for scipy,
  and the tmp_path-only file-write testing discipline)

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
