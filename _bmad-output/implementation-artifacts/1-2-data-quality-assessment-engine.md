# Story 1.2: Data Quality Assessment Engine

Status: ready-for-dev

<!-- Validation is optional. Run validate-create-story for quality check before dev-story. -->

---

## Story

**As a** developer,
**I want** to scan a structured dataset across six detection categories and receive a severity-classified quality report that halts the pipeline on critical findings,
**So that** bad data is caught before expensive LLM calls and downstream analysis.

### Business Context

This is the second story of Epic 1 (Phase 1 Foundation) and the first to contain production pipeline logic. Story 1.1 built the scaffolding (directories, error hierarchy, PipelineResult, structlog, conftest fixtures). This story fills `backend/pipeline/data_quality.py` and `backend/models/quality_report.py` with the Data Quality Assessment (DQA) engine — Stage 0 of the pipeline that gates all downstream processing.

DQA is the pipeline's safety net: if data is too broken (Critical severity), the pipeline halts before the LLM is called (saving API costs and preventing garbage-in/garbage-out reports). Non-critical findings flow through as context for the Insight Engine (Story 1.3) and appear in the final report.

The six detection categories (FR1) are: structural integrity, completeness, consistency, uniqueness, statistical red flags, and referential integrity. Each finding is a `DataQualityDefect` Pydantic model with a `Severity` classification. The overall assessment produces a `DataQualityReport` — a Pydantic model consumed by every downstream pipeline stage.

---

## Acceptance Criteria

Verbatim from [epics.md:239-268](../planning-artifacts/epics.md). Implement to the letter.

**AC1: Six-category assessment with severity classification**

**Given** a pandas DataFrame loaded from a CSV file
**When** `DataQualityAssessor.assess_quality(df)` is called
**Then** the assessment scans all six categories: structural integrity, completeness, consistency, uniqueness, statistical red flags, and referential integrity
**And** each finding is classified by severity (Critical, High, Medium, Low) as a `DataQualityDefect` Pydantic model
**And** the return type is a Pydantic-validated `DataQualityReport` containing all defects, an overall severity, and column-level summaries
**And** Pandera schema validation runs before assessment begins, raising `ConfigurationError` on invalid DataFrame structure

**AC2: Critical halt**

**Given** a dataset with critical data quality issues (e.g., >50% null values in key columns, completely duplicated rows, schema violations)
**When** the assessment detects critical-severity findings
**Then** `PipelineResult` is returned with `halted=True` and `halt_reason` describing the critical findings
**And** the pipeline does not proceed to the Insight Engine or LLM stages
**And** a structured log entry is emitted at level "warning" with event `"pipeline_halted"`, stage `"data_quality"`, and defect details

**AC3: Non-critical pass-through**

**Given** a dataset with only non-critical findings (High, Medium, Low)
**When** the assessment completes
**Then** `PipelineResult` is returned with `halted=False` and `quality_report` populated
**And** non-critical findings are preserved for inclusion in the final report

**AC4: Logging and testing**

**Given** any assessment run
**When** the assessment completes or halts
**Then** structlog entries are emitted with `pipeline_run_id`, `stage="data_quality"`, row count, and defect count
**And** `backend/tests/test_data_quality.py` passes with tests covering: clean data (no defects), each defect category, critical halt, non-critical pass-through, and Pandera validation failure

---

## Tasks / Subtasks

- [ ] **Task 1 — Severity enum and DataQualityDefect model** (AC: 1)
  - [ ] Create `backend/models/quality_report.py`
  - [ ] Define `Severity` as a `str` enum: `CRITICAL = "critical"`, `HIGH = "high"`, `MEDIUM = "medium"`, `LOW = "low"` — use `str, Enum` mixin (not `StrEnum`) for Pydantic v2 JSON serialization compatibility
  - [ ] Define `DataQualityDefect(BaseModel)` with fields:
    - `category: str` — one of `"structural_integrity"`, `"completeness"`, `"consistency"`, `"uniqueness"`, `"statistical_red_flags"`, `"referential_integrity"`
    - `severity: Severity`
    - `column: str | None = None` — column name if column-specific, `None` for row/table-level defects
    - `description: str` — human-readable explanation
    - `detail: dict[str, Any] | None = None` — optional numeric detail (e.g., `{"null_pct": 52.0, "threshold": 50.0}`)
  - [ ] Full type hints on all fields

- [ ] **Task 2 — DataQualityReport model** (AC: 1)
  - [ ] In same file `backend/models/quality_report.py`
  - [ ] Define `ColumnSummary(BaseModel)` with fields:
    - `column: str`
    - `dtype: str`
    - `null_count: int`
    - `null_pct: float`
    - `unique_count: int`
    - `defect_count: int`
  - [ ] Define `DataQualityReport(BaseModel)` with fields:
    - `total_rows: int`
    - `total_columns: int`
    - `defects: list[DataQualityDefect]`
    - `overall_severity: Severity` — the max severity across all defects; `LOW` if no defects
    - `column_summaries: list[ColumnSummary]`
    - `halted: bool = False` — mirrors PipelineResult.halted for report self-containment
    - `halt_reason: str | None = None`
  - [ ] Add a `@property` or Pydantic `@computed_field` for `critical_defects` → filters `defects` where `severity == Severity.CRITICAL`
  - [ ] Pydantic v2 `model_config = ConfigDict(strict=False)` to allow coercion

- [ ] **Task 3 — Pandera input schema** (AC: 1)
  - [ ] In `backend/pipeline/data_quality.py`, define a minimal Pandera `DataFrameSchema` that validates:
    - DataFrame has at least 1 row
    - DataFrame has at least 1 column
    - No completely empty DataFrame (all NaN)
  - [ ] This is intentionally a loose schema — the DQA *assesses* data quality rather than enforcing a fixed schema. Pandera catches structural precondition violations (zero rows, zero columns) that would make assessment meaningless.
  - [ ] On schema failure, raise `ConfigurationError` (from `backend.errors.exceptions`) with a message describing the structural violation
  - [ ] Do NOT enforce column names or dtypes in the Pandera schema — the six detection categories handle dtype/naming issues as defects

- [ ] **Task 4 — DataQualityAssessor: structural integrity** (AC: 1)
  - [ ] Create `DataQualityAssessor` class in `backend/pipeline/data_quality.py`
  - [ ] Method `assess_quality(df: pd.DataFrame) -> DataQualityReport` as the public entry point
  - [ ] **Structural integrity checks:**
    - Empty columns (100% null): `CRITICAL` — column has no usable data
    - Mixed dtypes within a column (object column with both numeric and string values): `HIGH` — ambiguous parsing
    - Unnamed columns (auto-generated like `Unnamed: 0`): `MEDIUM` — likely an index artifact
  - [ ] Each check produces a `DataQualityDefect` with `category="structural_integrity"`

- [ ] **Task 5 — DataQualityAssessor: completeness** (AC: 1, 2)
  - [ ] **Completeness checks:**
    - Column with >50% null values: `CRITICAL` — key column unusable
    - Column with >20% null values: `HIGH`
    - Column with >5% null values: `MEDIUM`
    - Column with >0% null values (but <=5%): `LOW`
  - [ ] Use `df[col].isna().sum() / len(df) * 100` for null percentage
  - [ ] Emit one defect per column that has nulls (with `detail={"null_pct": float, "null_count": int}`)

- [ ] **Task 6 — DataQualityAssessor: consistency** (AC: 1)
  - [ ] **Consistency checks:**
    - Inconsistent date formats in a column (some parseable, some not): `HIGH`
    - Numeric column containing non-numeric strings (coercion failures): `HIGH`
    - Mixed whitespace patterns (leading/trailing spaces in string columns): `LOW`
  - [ ] For numeric detection: use `pd.to_numeric(df[col], errors='coerce')` and compare NaN counts before/after
  - [ ] For date detection: heuristic — if column name contains "date" or dtype is datetime64, check for non-parseable values

- [ ] **Task 7 — DataQualityAssessor: uniqueness** (AC: 1)
  - [ ] **Uniqueness checks:**
    - Exact duplicate rows: `HIGH` if >0 duplicates (report count in detail)
    - Constant columns (only one unique non-null value): `MEDIUM` — adds no analytical value
  - [ ] Use `df.duplicated().sum()` for row duplicates
  - [ ] Use `df[col].nunique() == 1` for constant detection (exclude all-null columns which are caught by completeness)

- [ ] **Task 8 — DataQualityAssessor: statistical red flags** (AC: 1)
  - [ ] **Statistical red flag checks:**
    - Extreme outliers via IQR method (values beyond 3x IQR from Q1/Q3): `HIGH` — possible data entry errors
    - Negative values in columns with `>90%` positive values: `MEDIUM` — possible sign errors
    - Zero-variance numeric columns (std dev = 0): `MEDIUM`
  - [ ] Only apply to numeric columns (use `df.select_dtypes(include=[np.number])`)
  - [ ] IQR calculation: `Q1 = col.quantile(0.25)`, `Q3 = col.quantile(0.75)`, `IQR = Q3 - Q1`, outlier if `< Q1 - 3*IQR` or `> Q3 + 3*IQR`
  - [ ] Report outlier count and percentage in `detail`
  - [ ] NOTE: The legacy `advanced_pipeline.py:71-81` uses 1.5x IQR — this story uses 3x IQR to reduce false positives in an automated pipeline where humans don't verify each flag

- [ ] **Task 9 — DataQualityAssessor: referential integrity** (AC: 1)
  - [ ] **Referential integrity checks:**
    - Non-monotonic date columns (dates go backwards): `MEDIUM` — possible data ordering issue
    - Temporal gaps in date columns (missing expected dates in a daily/weekly series): `LOW`
  - [ ] For monotonicity: check if `df[col].is_monotonic_increasing` or `is_monotonic_decreasing` for datetime columns
  - [ ] For temporal gaps: if datetime column is detected and roughly evenly spaced, flag significant gaps (>2x the median interval)
  - [ ] Only apply to columns detected as datetime dtype

- [ ] **Task 10 — Severity aggregation and halt logic** (AC: 1, 2, 3)
  - [ ] After all six category checks, compute `overall_severity` as the maximum severity across all defects
  - [ ] Build `column_summaries` by iterating all columns and aggregating null_count, unique_count, defect_count
  - [ ] If `overall_severity == Severity.CRITICAL`:
    - Set `DataQualityReport.halted = True`
    - Set `halt_reason` to a summary of critical defects (e.g., "3 critical defects: revenue has 52% nulls, column 'Unnamed: 0' is empty, ...")
    - Return `PipelineResult(success=False, halted=True, halt_reason=halt_reason, quality_report=report)`
    - Log at `warning` level: `event="pipeline_halted"`, `stage="data_quality"`, `defect_count=N`, `critical_defects=[...]`
  - [ ] If `overall_severity != Severity.CRITICAL`:
    - Return `PipelineResult(success=True, halted=False, quality_report=report)`
  - [ ] Always log: `event="quality_assessed"`, `stage="data_quality"`, `total_rows=N`, `total_columns=N`, `defect_count=N`, `overall_severity=str`

- [ ] **Task 11 — Tests** (AC: 4)
  - [ ] Create `backend/tests/test_data_quality.py`
  - [ ] Tests use `clean_sales_df` and `dirty_sales_df` fixtures from conftest.py
  - [ ] Required test cases:
    - `test_clean_data_no_critical_defects` — clean_sales_df returns non-halted result with no CRITICAL defects
    - `test_dirty_data_triggers_critical_halt` — dirty_sales_df (52% nulls in revenue) returns halted PipelineResult
    - `test_structural_integrity_empty_column` — DataFrame with all-null column gets CRITICAL structural defect
    - `test_completeness_thresholds` — verify 50%/20%/5% threshold classification
    - `test_consistency_mixed_types` — column with both numbers and strings flagged
    - `test_uniqueness_duplicates` — DataFrame with duplicate rows gets HIGH uniqueness defect
    - `test_statistical_outliers` — DataFrame with extreme values flagged
    - `test_referential_non_monotonic_dates` — non-monotonic datetime column flagged
    - `test_pandera_validation_empty_df` — empty DataFrame raises ConfigurationError
    - `test_pandera_validation_no_columns` — DataFrame with no columns raises ConfigurationError
    - `test_logging_emits_pipeline_run_id` — verify structlog output includes pipeline_run_id and stage
    - `test_report_pydantic_validation` — DataQualityReport serializes to/from JSON correctly
  - [ ] Use `structlog.contextvars.bind_contextvars(pipeline_run_id=pipeline_run_id)` in tests that verify logging, with `capsys` or log capture
  - [ ] Bind `pipeline_run_id` fixture before calling `assess_quality` to test correlation ID propagation

- [ ] **Task 12 — Verification pass**
  - [ ] Run `pytest backend/tests/test_data_quality.py -v` — all green
  - [ ] Run `pytest backend/tests/` — no regressions in existing conftest tests
  - [ ] Verify: `from backend.models.quality_report import DataQualityReport, DataQualityDefect, Severity` imports cleanly
  - [ ] Verify: `DataQualityReport` round-trips through `.model_dump_json()` / `.model_validate_json()`
  - [ ] Grep for anti-patterns in new files: no `print()`, no `except Exception: pass`, no `warnings.filterwarnings`, no `import *`

---

## Day-1 Detection Category Reference

The six categories are defined in FR1 ([prd.md:64](../planning-artifacts/prd.md)) and the architecture maps them to Stage 0 ([architecture.md:188](../planning-artifacts/architecture.md)). This table details exactly what each category checks and how severity is assigned:

| Category | Check | Critical | High | Medium | Low |
|----------|-------|----------|------|--------|-----|
| Structural integrity | Empty column (100% null) | Yes | | | |
| Structural integrity | Mixed dtypes in column | | Yes | | |
| Structural integrity | Unnamed/auto-generated columns | | | Yes | |
| Completeness | Null % per column | >50% | >20% | >5% | >0% |
| Consistency | Non-numeric strings in numeric column | | Yes | | |
| Consistency | Inconsistent date formats | | Yes | | |
| Consistency | Leading/trailing whitespace | | | | Yes |
| Uniqueness | Duplicate rows | | Yes (if >0) | | |
| Uniqueness | Constant columns (1 unique value) | | | Yes | |
| Statistical | Extreme outliers (3x IQR) | | Yes | | |
| Statistical | Unexpected negatives (>90% positive) | | | Yes | |
| Statistical | Zero-variance numeric columns | | | Yes | |
| Referential | Non-monotonic dates | | | Yes | |
| Referential | Temporal gaps (>2x median interval) | | | | Yes |

---

## Dev Notes

### Developer Context

1. **This is the first pipeline stage.** `assess_quality()` takes a raw DataFrame and returns a `PipelineResult`. Story 1.3 (Insight Engine) receives the `DataQualityReport` from this result. Story 1.6 (orchestrator) calls this as Stage 0 and checks `halted` before proceeding. Design the API surface with this downstream chain in mind.

2. **Pandera validates preconditions, not data quality.** A common mistake: using Pandera to enforce column names or dtypes, which turns the assessor into a rigid schema validator. Pandera's role here is limited to catching structural impossibilities (zero rows, zero columns, all-NaN). The six detection categories do the actual assessment and produce defects as findings — not exceptions.

3. **PipelineResult is a stdlib dataclass, not Pydantic.** Import it from `backend.models.pipeline_result`. The assessor builds a `DataQualityReport` (Pydantic), then wraps it in a `PipelineResult` (dataclass). This is the only place in the pipeline where these two types interact directly — get the wrapping right.

4. **pandas 3.0.2 uses StringDtype.** Story 1.1 discovered that `df["region"].dtype == object` fails on pandas 3.x because string columns infer as `StringDtype`. Use `pd.api.types.is_string_dtype()`, `pd.api.types.is_numeric_dtype()`, and `pd.api.types.is_datetime64_any_dtype()` for type checks — never compare `.dtype` against raw strings or Python types.

5. **Legacy code is reference only.** `advanced_pipeline.py:59-92` has basic quality scoring (null%, outlier%, duplicate count, quality score). It uses 1.5x IQR and a flat scoring formula. DO NOT import from it. Use it as conceptual reference for what checks to run, but implement from scratch following the architecture patterns (Pydantic models, structlog, proper severity classification).

6. **The dirty_sales_df fixture has known defects.** See `conftest.py:25-31` for exact defect positions: 26/50 nulls in revenue (52% — triggers Critical completeness), one negative revenue (-500.0), one string "N/A" in revenue, one duplicate row, swapped dates at indices 10/11. Your tests should verify each of these triggers the correct category and severity.

### Project Structure Notes

- New files align with the target directory tree in [architecture.md:144-182](../planning-artifacts/architecture.md)
- `quality_report.py` goes in `backend/models/` — it is a Pydantic contract, not pipeline logic
- `data_quality.py` goes in `backend/pipeline/` — it is a pipeline stage
- Test file goes in `backend/tests/test_data_quality.py` — mirrors `pipeline/data_quality.py`
- No API routes, no CLI commands, no renderers — those are later stories

### Architecture Compliance Checklist

| Rule | Source | How this story complies |
|------|--------|-------------------------|
| Pydantic models for all pipeline I/O | [project-context.md:59](../project-context.md) | `DataQualityReport` and `DataQualityDefect` are Pydantic `BaseModel` subclasses. `PipelineResult` is the only stdlib dataclass (sanctioned exception). |
| Pandera validation before DataFrame processing | [project-context.md:61](../project-context.md) | Pandera `DataFrameSchema` validates structural preconditions before any category checks run. |
| structlog for all logging | [project-context.md:64](../project-context.md) | All log output uses `structlog.get_logger()` with `pipeline_run_id` context. No `print()`. |
| Result-vs-Exception split | [architecture.md:482-506](../planning-artifacts/architecture.md) | Critical data quality = `PipelineResult(halted=True)` (business outcome). Empty DataFrame = `ConfigurationError` (infrastructure failure). |
| Every module has a matching test file | [architecture.md:541](../planning-artifacts/architecture.md) | `test_data_quality.py` covers `data_quality.py`; `quality_report.py` is exercised through the assessor tests. |
| Type hints on every function signature | [project-context.md:58](../project-context.md) | All functions fully annotated. |
| No raw dicts between stages | [architecture.md:437-438](../planning-artifacts/architecture.md) | `assess_quality()` returns `PipelineResult` wrapping `DataQualityReport`. No dicts. |
| Three-layer separation | [architecture.md:741-747](../planning-artifacts/architecture.md) | `pipeline/data_quality.py` is Business Logic layer. Does not import from `api/` or `agents/`. |

### Library / Framework Requirements

**Used in this story:**

| Library | Version | Role |
|---------|---------|------|
| pydantic | >=2.7 | `DataQualityReport`, `DataQualityDefect`, `ColumnSummary` models |
| pandera | 0.30.1 | DataFrame structural precondition validation |
| pandas | 3.0.2 (installed) | DataFrame operations — use `pd.api.types.*` for dtype checks |
| numpy | 2.4.4 (installed) | IQR computation via `np.number` dtype selection |
| structlog | 25.5.0 | Logging with `pipeline_run_id` correlation |
| pytest | >=8.2 | Test runner |

**NOT introduced in this story:**
- `anthropic`, `docxtpl`, `WeasyPrint` — Stories 1.4/1.5
- `typer` — Story 1.6
- `scipy.stats` — Story 2.2 (Drift Engine PSI computation)

### File Structure Requirements

**New files (3):**

```
backend/models/quality_report.py     NEW — Severity, DataQualityDefect, ColumnSummary, DataQualityReport
backend/pipeline/data_quality.py     NEW — DataQualityAssessor class
backend/tests/test_data_quality.py   NEW — comprehensive test coverage
```

**Modified files (0):**
No existing files need modification. Story 1.1's scaffolding is consumed as-is.

### Testing Requirements

**Framework:** pytest (configured in `pyproject.toml` by Story 1.1)
**Location:** `backend/tests/test_data_quality.py`
**Fixtures:** Reuse `clean_sales_df`, `dirty_sales_df`, `pipeline_run_id` from `conftest.py`

**Required tests (minimum 12):**

| Test | Fixture | Verifies |
|------|---------|----------|
| `test_clean_data_no_critical_defects` | `clean_sales_df` | Returns non-halted PipelineResult; no CRITICAL defects |
| `test_dirty_data_triggers_critical_halt` | `dirty_sales_df` | Returns `PipelineResult(halted=True)`; halt_reason mentions revenue nulls |
| `test_structural_integrity_empty_column` | Custom (all-null column) | CRITICAL structural defect emitted |
| `test_structural_integrity_mixed_dtypes` | Custom (object col with mixed int+str) | HIGH structural defect emitted |
| `test_completeness_thresholds` | Custom (columns at 6%, 25%, 55% null) | LOW/HIGH/CRITICAL severity respectively |
| `test_consistency_mixed_numeric_strings` | Custom (numeric col with "N/A") | HIGH consistency defect |
| `test_uniqueness_duplicates` | `dirty_sales_df` | HIGH uniqueness defect with count in detail |
| `test_uniqueness_constant_column` | Custom (single-value column) | MEDIUM uniqueness defect |
| `test_statistical_outliers_iqr` | Custom (col with extreme values) | HIGH statistical defect with outlier count |
| `test_referential_non_monotonic_dates` | `dirty_sales_df` | MEDIUM referential defect (swapped dates) |
| `test_pandera_empty_dataframe` | `pd.DataFrame()` | Raises `ConfigurationError` |
| `test_report_serialization` | `clean_sales_df` | `DataQualityReport.model_dump_json()` round-trips |
| `test_logging_pipeline_run_id` | `clean_sales_df` + `pipeline_run_id` | structlog output contains `pipeline_run_id` and `stage="data_quality"` |

**Coverage target:** All 6 detection categories exercised, both halt and non-halt paths covered, Pandera validation failure path covered.

### Previous Story Intelligence

**From Story 1.1 ([1-1-project-scaffolding-pipeline-foundation.md](1-1-project-scaffolding-pipeline-foundation.md)):**

- **pandas 3.0.2 StringDtype:** `clean_sales_df["region"].dtype == object` fails. Use `pd.api.types.is_string_dtype()` instead. This affects every dtype check in all six categories.
- **Conftest fixture positions:** Dirty dataset defect positions are in module constants (`_NULL_REVENUE_COUNT = 26`, `_NEGATIVE_REVENUE_IDX = 30`, etc.). Import these in `test_data_quality.py` to write precise assertions rather than magic numbers.
- **structlog verified working:** JSON output with `pipeline_run_id=abc` confirmed. No additional structlog config needed — just `import structlog` and `structlog.get_logger()`.
- **PipelineResult instantiation:** `PipelineResult(success=True)` works with all optional fields defaulting to `None`/`False`. The assessor must set `quality_report=report` explicitly.
- **pytest runs from repo root:** `pytest backend/tests/` is the canonical command. Tests import via absolute paths (`from backend.pipeline.data_quality import ...`).
- **No dedicated test files for exceptions/pipeline_result yet:** Story 1.1 noted these would get formal unit tests in "Story 1.2 (exceptions, where stages first raise them)". Add at least one test that verifies `ConfigurationError` is raised for Pandera failures.

### Git Intelligence Summary

Recent commits show Story 1.1 was implemented across 4 merged PRs (#13-#16) and the scaffolding commit (`3affe04`). The implementation pattern:
- Feature branches named `claude/<adjective>-<noun>`
- PRs merged to main
- Single-story-per-branch

Files created by Story 1.1 that this story depends on:
- `backend/pipeline/config.py` — `configure_logging()`, `bind_pipeline_run_id()`
- `backend/errors/exceptions.py` — `ConfigurationError`, `SavvyCleanseError` hierarchy
- `backend/models/pipeline_result.py` — `PipelineResult` dataclass
- `backend/tests/conftest.py` — `clean_sales_df`, `dirty_sales_df`, `pipeline_run_id` fixtures

### References

- User story + BDD AC: [epics.md:239-268](../planning-artifacts/epics.md)
- Six detection categories (FR1): [prd.md:64](../planning-artifacts/prd.md)
- Pipeline stage inventory — data_quality.py is Stage 0: [architecture.md:188](../planning-artifacts/architecture.md)
- Pydantic model naming (PascalCase, noun-based): [architecture.md:376](../planning-artifacts/architecture.md)
- DataQualityReport listed in models/: [architecture.md:597](../planning-artifacts/architecture.md)
- Pandera before DataFrame processing rule: [project-context.md:61](../project-context.md)
- Result-vs-Exception split: [architecture.md:482-506](../planning-artifacts/architecture.md)
- Pipeline data flow diagram: [architecture.md:756-764](../planning-artifacts/architecture.md)
- Anti-patterns (9 rules): [architecture.md:549-556](../planning-artifacts/architecture.md)
- Legacy advanced_pipeline.py quality scoring reference: `backend/advanced_pipeline.py:59-92`
- Conftest fixture defect positions: `backend/tests/conftest.py:25-31`
- Story 1.1 completion notes (pandas 3.x dtype discovery): [1-1-project-scaffolding-pipeline-foundation.md:350](1-1-project-scaffolding-pipeline-foundation.md)

---

## Project Context Reference

Load [project-context.md](../project-context.md) before implementation. Key sections for this story:
- **Technology Stack** ([project-context.md:24-49](../project-context.md)) — confirm Pandera 0.30.1, Pydantic v2, pandas 3.x
- **Language-Specific Rules -> Python** ([project-context.md:57-64](../project-context.md)) — type hints required, Pydantic models for I/O, Pandera before DataFrame processing
- **Framework-Specific Rules -> Pipeline** ([project-context.md:79-84](../project-context.md)) — composable stages returning Pydantic models, `PipelineResult` for business outcomes
- **Testing Rules -> Backend** ([project-context.md:93-98](../project-context.md)) — tests in `backend/tests/`, mirror source structure
- **Anti-patterns** ([project-context.md:148-156](../project-context.md)) — no `print()`, no `except Exception: pass`, no raw dicts, no untyped interfaces

---

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

---

## Story Completion Status

- **Status:** ready-for-dev
- **Completion note:** Comprehensive developer guide created — 6 detection categories specified with severity thresholds, previous story intelligence integrated, architecture compliance verified, all AC mapped to tasks.
