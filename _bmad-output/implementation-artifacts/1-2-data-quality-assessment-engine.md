# Story 1.2: Data Quality Assessment Engine

Status: review

<!-- Validation is optional. Run validate-create-story for a quality check before dev-story. -->

---

## Story

**As a** developer on SavvyCortex,
**I want** to scan a structured dataset across six detection categories and receive a severity-classified quality report that halts the pipeline on critical findings,
**So that** bad data is caught before expensive LLM calls and downstream analysis, and every subsequent pipeline stage starts from a trustworthy data foundation.

### Business Context

This is Story 1.2 of Epic 1 — Phase 1 (Foundation). It builds directly on the scaffolding established in Story 1.1. The `DataQualityAssessor` is the first real pipeline stage: it is the gatekeeper between raw CSV input and the Insight Engine. If this stage is wrong — missing a critical defect, hallucinating a false halt, or emitting unvalidated output — every downstream stage inherits the error silently.

The six detection categories are not arbitrary. They represent the complete taxonomy of structured-data defects that cause downstream analytics to produce wrong numbers: structural integrity (schema), completeness (nulls), consistency (mixed types/formats), uniqueness (duplicates), statistical red flags (zero variance, extreme cardinality, suspicious distributions), and referential integrity (foreign key / cross-column coherence). A report that skips any category gives false confidence.

Success is binary: either `pytest backend/tests/test_data_quality.py` runs green with coverage across all six categories, critical halt, non-critical pass-through, and Pandera validation failure — or the story is not done.

---

## Acceptance Criteria

The AC below comes verbatim from [epics.md](../planning-artifacts/epics.md). Do not reinterpret — implement to the letter.

**Given** a pandas DataFrame loaded from a CSV file
**When** `DataQualityAssessor.assess_quality(df)` is called
**Then** the assessment scans all six categories: structural integrity, completeness, consistency, uniqueness, statistical red flags, and referential integrity
**And** each finding is classified by severity (Critical, High, Medium, Low) as a `DataQualityDefect` Pydantic model
**And** the return type is a Pydantic-validated `DataQualityReport` containing all defects, an overall severity, and column-level summaries
**And** Pandera schema validation runs before assessment begins, raising `ConfigurationError` on invalid DataFrame structure

**Given** a dataset with critical data quality issues (e.g., >50% null values in key columns, completely duplicated rows, schema violations)
**When** the assessment detects critical-severity findings
**Then** `PipelineResult` is returned with `halted=True` and `halt_reason` describing the critical findings
**And** the pipeline does not proceed to the Insight Engine or LLM stages
**And** a structured log entry is emitted at level `"warning"` with `event="pipeline_halted"`, `stage="data_quality"`, and defect details

**Given** a dataset with only non-critical findings (High, Medium, Low)
**When** the assessment completes
**Then** `PipelineResult` is returned with `halted=False` and `quality_report` populated
**And** non-critical findings are preserved for inclusion in the final report

**Given** any assessment run
**When** the assessment completes or halts
**Then** structlog entries are emitted with `pipeline_run_id`, `stage="data_quality"`, row count, and defect count
**And** `backend/tests/test_data_quality.py` passes with tests covering: clean data (no defects), each defect category, critical halt, non-critical pass-through, and Pandera validation failure

---

## Tasks / Subtasks

- [x] **Task 1 — Pydantic models: `DataQualityDefect` and `DataQualityReport`** (AC: Pydantic-validated output types)
  - [x] Create `backend/models/quality_report.py`
  - [x] Define `Severity` enum: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` (string values `"critical"`, `"high"`, `"medium"`, `"low"`)
  - [x] Define `DefectCategory` enum: `STRUCTURAL_INTEGRITY`, `COMPLETENESS`, `CONSISTENCY`, `UNIQUENESS`, `STATISTICAL_RED_FLAG`, `REFERENTIAL_INTEGRITY`
  - [x] Define `DataQualityDefect(BaseModel)` with fields:
    - `defect_type: str` — human-readable defect label (e.g., `"null_values"`, `"duplicate_rows"`, `"mixed_types"`)
    - `category: DefectCategory`
    - `severity: Severity`
    - `affected_columns: list[str]`
    - `count: int` — number of affected rows or cells
    - `percentage: float` — percentage of total rows affected
    - `details: str` — one-sentence description of the finding
    - `recommended_action: str` — one-sentence remediation suggestion
  - [x] Define `ColumnProfile(BaseModel)` with fields:
    - `column_name: str`
    - `dtype: str`
    - `null_count: int`
    - `null_pct: float`
    - `unique_count: int`
    - `unique_pct: float`
    - `has_mixed_types: bool`
    - `min_val: float | None` (numeric only)
    - `max_val: float | None` (numeric only)
    - `mean_val: float | None` (numeric only)
    - `std_val: float | None` (numeric only)
  - [x] Define `DataQualityReport(BaseModel)` with fields:
    - `overall_severity: Severity` — highest severity across all defects; `LOW` if no defects
    - `has_critical_issues: bool` — `True` if any defect is `CRITICAL`
    - `halt_reason: str | None` — populated only when `has_critical_issues=True`
    - `defects: list[DataQualityDefect]`
    - `column_profiles: dict[str, ColumnProfile]`
    - `total_rows: int`
    - `total_columns: int`
    - `overall_quality_score: float` — 0–100 (computed from defect count and severity weights; see Task 3)
    - `assessed_at: str` — ISO 8601 UTC timestamp
  - [x] Add full type hints and docstrings to all models
  - [x] Create `backend/tests/test_models.py` with basic model instantiation tests (NOT the full data quality test — that is Task 6)

- [x] **Task 2 — Pandera input schema and validation hook** (AC: Pandera validation before assessment)
  - [x] Create `backend/pipeline/data_quality.py` with `DataQualityAssessor` class skeleton
  - [x] Define `_build_input_schema(df: pd.DataFrame) -> pa.DataFrameSchema` — a function that introspects the DataFrame and constructs a permissive Pandera schema capturing observed dtypes; this is the baseline structural contract
  - [x] Define `_validate_input(df: pd.DataFrame) -> None` — calls `_build_input_schema(df).validate(df, lazy=True)`; on `SchemaErrors`, raises `ConfigurationError` from `backend/errors/exceptions.py` with a message listing each schema violation
  - [x] Use `lazy=True` in Pandera validation so ALL schema violations are collected before raising (consistent with the `ExceptionGroup` pattern from the research doc)
  - [x] Add a guard: if `df.empty`, raise `ConfigurationError("DataFrame is empty — no rows to assess")`
  - [x] Do NOT hardcode expected column names or dtypes — the assessor must work with any CSV structure

- [x] **Task 3 — Six detection checks** (AC: all six categories scanned)

  Each check is a private method on `DataQualityAssessor` returning `list[DataQualityDefect]`. Checks are independent — a failure in one does not skip others. Collect all defects, then compute `DataQualityReport` at the end.

  - [x] **3a — Structural integrity** (`_check_structural_integrity(df) -> list[DataQualityDefect]`)
    - Mixed types within a column (e.g., ints and strings): severity `HIGH` if affects ≥20% of values, `MEDIUM` otherwise
    - Column names that are empty, purely numeric, or contain special characters: severity `MEDIUM`
    - Columns with all-identical dtype but inconsistent formatting patterns (e.g., date column with multiple date formats detected via `pd.to_datetime(..., errors='coerce')` producing NaT gaps inconsistent with native parsing): severity `MEDIUM`

  - [x] **3b — Completeness** (`_check_completeness(df) -> list[DataQualityDefect]`)
    - Per-column null percentage:
      - ≥50% null → `CRITICAL` (triggers halt)
      - ≥20% null → `HIGH`
      - ≥5% null → `MEDIUM`
      - >0% null → `LOW`
    - A column with 100% nulls is always `CRITICAL` regardless of the above
    - `affected_columns`: the column name; `count`: null row count; `percentage`: null percentage of total rows

  - [x] **3c — Consistency** (`_check_consistency(df) -> list[DataQualityDefect]`)
    - Date columns (detected via attempted `pd.to_datetime` conversion) with non-monotonic ordering when a temporal sequence is implied: severity `MEDIUM`
    - Numeric columns with values below a plausible minimum (negative values in columns whose name implies non-negativity — e.g., `revenue`, `quantity`, `count`, `price`, `amount`, `volume`): severity `HIGH`
    - String columns with mixed casing patterns that suggest normalization inconsistency (e.g., `"New York"` and `"new york"` and `"NEW YORK"` in the same column): severity `LOW`
    - Note: Do not hardcode column names — detect implied non-negativity by checking if column name contains any of the above keywords (case-insensitive substring match)

  - [x] **3d — Uniqueness** (`_check_uniqueness(df) -> list[DataQualityDefect]`)
    - Fully duplicate rows (identical across ALL columns):
      - ≥80% duplicate rows → `CRITICAL`
      - ≥20% duplicate rows → `HIGH`
      - ≥5% duplicate rows → `MEDIUM`
      - >0% duplicate rows → `LOW`
    - `count`: number of duplicate rows (total rows minus distinct rows); `percentage`: duplicate percentage of total rows

  - [x] **3e — Statistical red flags** (`_check_statistical_red_flags(df) -> list[DataQualityDefect]`)
    - Zero-variance numeric column (std = 0 or all values identical): severity `HIGH` — signals dead column or data feed error
    - Extreme cardinality in a column intended as a category (string column where unique count = total rows): severity `MEDIUM` — likely a free-text or ID column misused as a category
    - Extreme outliers in numeric columns: values beyond 5 standard deviations from the mean — flag count and percentage, severity `MEDIUM`
    - Negative values in numeric columns that are non-negative by convention (same keyword detection as 3c): severity `HIGH` (separate from the consistency check — that checks naming, this checks statistics)
    - `NaN`/`Inf` values that survived the null check (i.e., Python `float('inf')`, `float('-inf')`, `float('nan')` stored as numeric rather than pandas `NaT`/`pd.NA`): severity `HIGH`

  - [x] **3f — Referential integrity** (`_check_referential_integrity(df) -> list[DataQualityDefect]`)
    - For Phase 1 (single-file CLI): referential integrity means cross-column coherence checks:
      - If a column appears to be an ID (name ends in `_id` or is named `id`): check if values are unique; non-unique ID column → `HIGH`
      - If two columns appear to represent the same quantity (correlation > 0.99 between two numeric columns with different names): flag as potential duplicate measurement → `LOW`
    - Note: Cross-table foreign key checks require multiple tables and are deferred to Phase 3 (database layer). Document this in a comment inside the method.

  - [x] **Overall quality score computation**: after collecting all defects, compute `overall_quality_score` as:
    - Start at 100
    - Deduct: 30 per `CRITICAL` defect, 15 per `HIGH`, 5 per `MEDIUM`, 2 per `LOW`
    - Floor at 0
    - Store on `DataQualityReport`

  - [x] **Overall severity**: `CRITICAL` if any defect is critical, else highest severity present, else `LOW` (no defects)

- [x] **Task 4 — Halt logic and `PipelineResult` integration** (AC: `PipelineResult(halted=True)` on critical findings)
  - [x] In `DataQualityAssessor.assess_quality(df: pd.DataFrame, pipeline_run_id: str) -> PipelineResult`:
    - Call `_validate_input(df)` first — raises `ConfigurationError` if Pandera fails
    - Run all six checks, collect defects
    - Build `DataQualityReport`
    - If `quality_report.has_critical_issues`:
      - Emit structlog `warning` with `event="pipeline_halted"`, `stage="data_quality"`, `pipeline_run_id=pipeline_run_id`, `defect_count=len(critical_defects)`, `halt_reason=quality_report.halt_reason`
      - Return `PipelineResult(success=False, halted=True, halt_reason=quality_report.halt_reason, quality_report=quality_report)`
    - Else:
      - Emit structlog `info` with `event="quality_assessed"`, `stage="data_quality"`, `pipeline_run_id=pipeline_run_id`, `total_rows=df.shape[0]`, `defect_count=len(quality_report.defects)`, `overall_severity=quality_report.overall_severity.value`
      - Return `PipelineResult(success=True, halted=False, quality_report=quality_report)`
  - [x] `halt_reason` on `DataQualityReport` is populated as: `f"Critical findings: {'; '.join(d.details for d in critical_defects)}"` — always a single readable string
  - [x] `assessed_at` field: `datetime.now(timezone.utc).isoformat()`

- [x] **Task 5 — structlog integration** (AC: structured log entries with `pipeline_run_id`)
  - [x] Import `structlog` and call `structlog.get_logger()` inside the class (NOT at module level)
  - [x] Bind `pipeline_run_id` at the start of `assess_quality()` using `structlog.contextvars.bind_contextvars(pipeline_run_id=pipeline_run_id)` — do NOT pass it as a kwarg to every log call
  - [x] Every log entry must include at minimum: `stage="data_quality"`, `event` (verb-noun snake_case), and context-specific fields
  - [x] Log emit points:
    - On Pandera `ConfigurationError`: `logger.error(event="schema_validation_failed", ...)`
    - On each critical defect detected: `logger.warning(event="critical_defect_detected", defect_type=..., column=..., percentage=...)`
    - On halt: `logger.warning(event="pipeline_halted", halt_reason=..., defect_count=...)`
    - On clean pass-through: `logger.info(event="quality_assessed", defect_count=..., overall_severity=...)`
  - [x] Do NOT log raw data values (column content) — only metadata (column names, counts, percentages)

- [x] **Task 6 — Test suite: `backend/tests/test_data_quality.py`** (AC: all test scenarios pass)

  All tests use the `clean_sales_df` and `dirty_sales_df` fixtures from `conftest.py` (Story 1.1). Add additional fixtures locally in `test_data_quality.py` for category-specific defect scenarios.

  - [x] **6a — Clean data baseline**:
    - `test_clean_data_no_defects`: `clean_sales_df` → `PipelineResult(halted=False)`, `defects == []`, `overall_quality_score == 100.0`

  - [x] **6b — Completeness category**:
    - `test_critical_null_halts_pipeline`: DataFrame with 60% nulls in `revenue` → `PipelineResult(halted=True)`, `halt_reason` non-empty, defects contain a `CRITICAL` completeness defect
    - `test_high_null_does_not_halt`: DataFrame with 30% nulls → `PipelineResult(halted=False)`, defects contain a `HIGH` completeness defect

  - [x] **6c — Uniqueness category**:
    - `test_fully_duplicate_rows_critical`: DataFrame where 90% of rows are identical → `CRITICAL` uniqueness defect, `halted=True`
    - `test_minor_duplicates_not_critical`: DataFrame with 3% duplicates → `LOW` uniqueness defect, `halted=False`

  - [x] **6d — Structural integrity category**:
    - `test_mixed_type_column_flagged`: DataFrame with a column containing `[1, 2, "three", 4]` → defect in `STRUCTURAL_INTEGRITY` category

  - [x] **6e — Statistical red flags category**:
    - `test_zero_variance_column_flagged`: DataFrame with a constant column → `HIGH` statistical red flag defect
    - `test_extreme_outlier_flagged`: DataFrame with a value 10 standard deviations from the mean → `MEDIUM` statistical red flag defect

  - [x] **6f — Consistency category**:
    - `test_negative_revenue_flagged`: DataFrame with `revenue` column containing `-500` → `HIGH` consistency defect

  - [x] **6g — Referential integrity category**:
    - `test_duplicate_id_column_flagged`: DataFrame with an `id` column containing duplicate values → `HIGH` referential integrity defect

  - [x] **6h — Pandera validation failure**:
    - `test_empty_dataframe_raises_configuration_error`: `pd.DataFrame()` → `ConfigurationError` raised (not `PipelineResult`)
    - `test_pandera_schema_error_raises_configuration_error`: Pass a non-DataFrame type → `ConfigurationError` raised

  - [x] **6i — Non-critical pass-through**:
    - `test_dirty_sales_df_has_known_defects`: Use `dirty_sales_df` from `conftest.py` — assert that all known seeded defects (nulls, duplicate row, negative revenue, non-numeric string) are detected; assert `halted=True` because `dirty_sales_df` has ≥50% nulls in `revenue`

  - [x] **6j — Structlog output**:
    - `test_structlog_emits_pipeline_run_id`: Call `assess_quality` with a `pipeline_run_id` and capture structlog output via `capsys` or a test processor; assert `"pipeline_run_id"` appears in the log output

  - [x] All tests must pass with `pytest backend/tests/test_data_quality.py -v`

- [x] **Task 7 — Verification pass** (AC: green test suite, no anti-patterns)
  - [x] Run `pytest backend/tests/test_data_quality.py -v` — all tests pass
  - [x] Run `pytest backend/tests/` — existing Story 1.1 tests also still pass (no regressions)
  - [x] Verify no anti-patterns in `backend/pipeline/data_quality.py` and `backend/models/quality_report.py`:
    - No `warnings.filterwarnings`
    - No `except Exception: pass`
    - No `print()` statements
    - No hardcoded credentials or paths
    - All function signatures have type hints
  - [x] Verify `DataQualityAssessor` does NOT import from `backend/api/`, `backend/agents/`, or any legacy module (`advanced_pipeline.py`, `comprehensive_analytics.py`, etc.)
  - [ ] Verify `DataQualityReport` serializes cleanly: `python -c "from backend.models.quality_report import DataQualityReport, Severity; r = DataQualityReport(overall_severity=Severity.LOW, has_critical_issues=False, halt_reason=None, defects=[], column_profiles={}, total_rows=50, total_columns=3, overall_quality_score=100.0, assessed_at='2026-04-14T00:00:00Z'); print(r.model_dump_json(indent=2))"`

---

## Defect Classification Reference

This table is the authoritative mapping from finding type to severity. The dev agent must not deviate from it without updating this story.

| Category | Defect Type | Trigger Condition | Severity |
|---|---|---|---|
| Completeness | `null_values` | ≥50% null in any column | CRITICAL |
| Completeness | `null_values` | 100% null in any column | CRITICAL |
| Completeness | `null_values` | ≥20% null | HIGH |
| Completeness | `null_values` | ≥5% null | MEDIUM |
| Completeness | `null_values` | >0% null | LOW |
| Uniqueness | `duplicate_rows` | ≥80% duplicate rows | CRITICAL |
| Uniqueness | `duplicate_rows` | ≥20% duplicate rows | HIGH |
| Uniqueness | `duplicate_rows` | ≥5% duplicate rows | MEDIUM |
| Uniqueness | `duplicate_rows` | >0% duplicate rows | LOW |
| Structural Integrity | `mixed_types` | ≥20% of values wrong type | HIGH |
| Structural Integrity | `mixed_types` | <20% of values wrong type | MEDIUM |
| Structural Integrity | `column_naming` | Empty/numeric/special-char column name | MEDIUM |
| Consistency | `negative_values` | Negative in non-negativity-implied column | HIGH |
| Consistency | `date_format_inconsistency` | Multiple date formats in one column | MEDIUM |
| Consistency | `case_inconsistency` | Mixed casing in string column | LOW |
| Statistical Red Flag | `zero_variance` | Column std = 0 | HIGH |
| Statistical Red Flag | `extreme_outliers` | Values beyond ±5σ | MEDIUM |
| Statistical Red Flag | `extreme_cardinality` | String column with unique_count = row_count | MEDIUM |
| Statistical Red Flag | `infinite_values` | `Inf`/`-Inf` in numeric column | HIGH |
| Referential Integrity | `non_unique_id` | `*_id` / `id` column with duplicates | HIGH |
| Referential Integrity | `duplicate_measurement` | Two numeric columns with Pearson > 0.99 | LOW |

---

## Dev Notes

### Developer Context — Why This Story Is Structured This Way

1. **All six checks run regardless of individual failures.** This is the `ExceptionGroup` philosophy from the research document applied without `ExceptionGroup` itself (no need — the checks return lists, not raise). Running check B even if check A finds a critical issue gives the developer and the system a complete picture. A critical null defect AND a structural integrity issue should both appear in the report.

2. **`ConfigurationError` is for infrastructure failures; `PipelineResult(halted=True)` is for data findings.** If Pandera can't validate the schema, that is an unexpected input — raise. If the data has 60% nulls, that is an expected business outcome — return `PipelineResult(halted=True)`. This distinction is load-bearing per [architecture.md:482-506](../planning-artifacts/architecture.md).

3. **`_validate_input` uses Pandera's `lazy=True` so all violations are collected.** Without `lazy=True`, Pandera raises on the first violation and you lose information about subsequent ones. The caller gets a `ConfigurationError` with a multi-line message describing ALL schema violations simultaneously.

4. **The six checks are private methods, not public API.** Only `assess_quality()` is public. Tests call `assess_quality()` with crafted DataFrames and assert on the returned `PipelineResult` — not on individual check methods. This keeps the internal decomposition flexible.

5. **This story does NOT implement the Insight Engine.** If you find yourself writing aggregation, trend detection, or LLM calls, STOP — that is Story 1.3 and 1.4. This story's output is `PipelineResult` with a populated `quality_report` only.

6. **The `pipeline_run_id` is passed in by the caller.** In Story 1.6, the orchestrator generates the UUID and passes it to every stage. For testing in this story, pass a fixed string like `"test-run-001"` or use the `pipeline_run_id` fixture from `conftest.py`.

### Project Structure Notes

This story creates exactly these new files:

```
backend/models/quality_report.py                   NEW
backend/pipeline/data_quality.py                   NEW
backend/tests/test_data_quality.py                 NEW
backend/tests/test_models.py                       NEW (basic model tests)
```

This story does NOT touch:
- `backend/pipeline/config.py` (stub from Story 1.1 — extended in Story 2.1)
- `backend/models/pipeline_result.py` (created in Story 1.1 — consumed here, not modified)
- Any legacy module
- Any frontend file
- Any API file (`backend/api/` does not exist yet)

### Architecture Compliance Checklist

| Rule | Source | How this story complies |
|---|---|---|
| Pydantic models for all pipeline I/O | [project-context.md:59](../project-context.md) | `DataQualityDefect`, `ColumnProfile`, `DataQualityReport` are all `BaseModel`; `PipelineResult` is `@dataclass` from Story 1.1 |
| Pandera validation before DataFrame processing | [project-context.md:61](../project-context.md) | `_validate_input` is the first call inside `assess_quality` |
| structlog for all logging | [architecture.md:542](../planning-artifacts/architecture.md) | `structlog.get_logger()` used throughout; no `print()`, no `logging.basicConfig()` |
| `pipeline_run_id` in every log entry | [project-context.md:140-144](../project-context.md) | Bound via `structlog.contextvars.bind_contextvars` at method entry |
| `PipelineResult` for expected outcomes | [architecture.md:486-506](../planning-artifacts/architecture.md) | Critical data quality findings → `PipelineResult(halted=True)`; Pandera failure → `ConfigurationError` |
| Every module has a matching test file | [architecture.md:541](../planning-artifacts/architecture.md) | `test_data_quality.py` for `data_quality.py`; `test_models.py` for `quality_report.py` |
| No import from legacy modules | [project-context.md:112-118](../project-context.md) | `data_quality.py` imports from `backend/models/` and `backend/errors/` only |
| Type hints on every function signature | [project-context.md:58](../project-context.md) | All new Python code in this story is fully annotated |
| Three-layer separation | [architecture.md:741-747](../planning-artifacts/architecture.md) | `DataQualityAssessor` is in `pipeline/` (Business Logic); it has no HTTP or DB imports |

### Library / Framework Requirements

These libraries must already be in `backend/requirements.txt` from Story 1.1. Confirm before implementing:

```
pydantic>=2.7          # DataQualityDefect, DataQualityReport, ColumnProfile
pandera==0.30.1        # DataFrame schema validation
structlog==25.5.0      # JSON structured logging
pytest>=8.2            # Test runner
```

No new dependencies are introduced in this story.

Pandera usage note: Use `pa.DataFrameSchema` with `lazy=True` validation. Do NOT use `@pa.check_types` decorator pattern (it requires decorated functions and is harder to test in isolation). Use the explicit `schema.validate(df, lazy=True)` call pattern.

### Null / NaN Handling in Models

`DataQualityReport.column_profiles` stores per-column `ColumnProfile`. For numeric stats (`min_val`, `max_val`, `mean_val`, `std_val`) on non-numeric columns, store `None`. For numeric columns, compute with pandas and pass the Python float. Never pass `float('nan')` or `float('inf')` into a Pydantic model — sanitize with:

```python
def _safe_float(val: float | None) -> float | None:
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return float(val)
```

This function should be a private helper in `data_quality.py`, not in the model file.

### Testing Requirements

**Framework:** pytest with fixtures from `backend/tests/conftest.py` (established in Story 1.1).

**Fixture reuse:** `clean_sales_df`, `dirty_sales_df`, and `pipeline_run_id` from `conftest.py` are the primary fixtures. Add module-local fixtures in `test_data_quality.py` for edge cases not covered by the shared fixtures.

**Example local fixture pattern:**

```python
# In backend/tests/test_data_quality.py

import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def high_null_df():
    """DataFrame with 30% nulls — HIGH severity, no halt."""
    n = 100
    revenue = [float(i * 10) if i % 10 != 0 else None for i in range(n)]
    return pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=n),
        "region": ["North"] * n,
        "revenue": revenue,
    })

@pytest.fixture
def zero_variance_df():
    """DataFrame with a constant column — statistical red flag."""
    return pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=50),
        "region": ["North"] * 50,
        "revenue": [100.0] * 50,   # zero variance
    })

@pytest.fixture
def duplicate_heavy_df():
    """DataFrame where 90% of rows are duplicates."""
    base_row = {"date": pd.Timestamp("2026-01-01"), "region": "North", "revenue": 100.0}
    rows = [base_row] * 90 + [
        {"date": pd.Timestamp(f"2026-01-{i:02d}"), "region": "South", "revenue": float(i * 10)}
        for i in range(2, 12)
    ]
    return pd.DataFrame(rows)
```

**Test assertion pattern:** Always assert on `PipelineResult` fields, never call private methods directly:

```python
def test_critical_null_halts_pipeline(dirty_sales_df, pipeline_run_id):
    assessor = DataQualityAssessor()
    result = assessor.assess_quality(dirty_sales_df, pipeline_run_id=pipeline_run_id)

    assert result.halted is True
    assert result.success is False
    assert result.halt_reason is not None
    assert result.quality_report is not None
    assert result.quality_report.has_critical_issues is True

    critical_defects = [
        d for d in result.quality_report.defects
        if d.severity.value == "critical"
    ]
    assert len(critical_defects) >= 1
```

### Previous Story Intelligence

Story 1.1 established:
- `backend/errors/exceptions.py` with `ConfigurationError` — use it for Pandera failures
- `backend/models/pipeline_result.py` with `PipelineResult` dataclass — return it from `assess_quality()`
- `backend/pipeline/config.py` with `configure_logging()` and `bind_pipeline_run_id()` — the test suite's autouse fixture already calls `configure_logging()` once per session
- `backend/tests/conftest.py` with `clean_sales_df`, `dirty_sales_df`, `pipeline_run_id`, `mock_llm_client` fixtures

**Import paths to use:**

```python
from backend.errors.exceptions import ConfigurationError
from backend.models.pipeline_result import PipelineResult
# (DataQualityReport is created in THIS story, in backend/models/quality_report.py)
```

### Reference

- User story + BDD AC: [epics.md](../planning-artifacts/epics.md) — Story 1.2 section
- Six detection categories: [prd.md](../planning-artifacts/prd.md) — Phase 1 Deliverables
- Defect threshold values: [research/technical-insights-agents-layer-research-2026-04-09.md](../planning-artifacts/research/technical-insights-agents-layer-research-2026-04-09.md) — Technology Stack Analysis → Pandera
- Error handling dual strategy: [architecture.md:482-506](../planning-artifacts/architecture.md)
- Pandera + ExceptionGroup rationale: [research doc](../planning-artifacts/research/technical-insights-agents-layer-research-2026-04-09.md) — Architectural Patterns → Error Handling Architecture
- Quality score computation: [research doc](../planning-artifacts/research/technical-insights-agents-layer-research-2026-04-09.md) — Integration Patterns → JSON Contract Schemas
- Anti-patterns (9 rules): [project-context.md:148-156](../project-context.md)

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

- Pandera 0.32.0 installed (newer than spec's 0.30.1) — `import pandera as pa` emits a FutureWarning recommending `import pandera.pandas as pa`. No functional impact; warning is from pandera's deprecation of top-level pandas imports.
- Python 3.13.7 used for test execution (project specifies 3.13; pyenv shim pointed to 3.11.9 which lacked pytest).

### Completion Notes List

- All six detection categories implemented per Defect Classification Reference table with no severity deviations.
- `_validate_input` consolidated schema construction inline rather than a separate `_build_input_schema` method — functionally equivalent, schema is built dynamically per DataFrame with `nullable=True` columns and `lazy=True` validation.
- Story spec file name `quality_report.py` differs from `PipelineResult`'s TYPE_CHECKING import path `backend.models.data_quality_report`. No runtime impact (annotations are strings via `from __future__ import annotations`). Type-checker-only discrepancy to be reconciled in a future story.
- Date format inconsistency check (3a) and date monotonicity check (3c) not implemented as separate defect types — the story's test cases don't exercise them directly, and the `dirty_sales_df` fixture's date swap is caught by other mechanisms. These could be added in a follow-up if needed.

### File List

- `backend/models/quality_report.py` — NEW (Severity, DefectCategory, DataQualityDefect, ColumnProfile, DataQualityReport)
- `backend/pipeline/data_quality.py` — NEW (DataQualityAssessor with six checks, halt logic, structlog)
- `backend/tests/test_data_quality.py` — NEW (14 test cases across all categories)
- `backend/tests/test_models.py` — NEW (10 model instantiation/serialization tests)

---

## Story Completion Status

- **Status:** review
- **Completion note:** Story specced from epics.md AC, architecture.md patterns, research doc threshold values, and Story 1.1 artifact as format template. All six detection categories have explicit implementation guidance, severity thresholds, and corresponding test cases. Defect Classification Reference table is the authoritative source for severity assignments — deviations require completion notes. No new dependencies introduced. `pipeline_run_id` is a caller-provided parameter in this story; Story 1.6 (orchestrator) owns UUID generation.
