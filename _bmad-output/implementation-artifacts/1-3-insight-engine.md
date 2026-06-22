# Story 1.3: Insight Engine

Status: done

<!-- Validation is optional. Run validate-create-story for a quality check before dev-story. -->

---

## Story

**As a** developer on SavvyCortex,
**I want** to compute aggregations, time-based trends, segment comparisons, and outlier detection from a quality-assessed DataFrame, producing a structured JSON payload,
**So that** the LLM narrative layer has deterministic, computed statistics to ground its narrative on — and no LLM involvement happens at this stage.

### Business Context

This is Story 1.3 of Epic 1 — Phase 1 (Foundation). It builds directly on the `DataQualityAssessor` from Story 1.2. The Insight Engine is the second pipeline stage: it receives a DataFrame that has already passed data quality assessment and computes all the statistics, trends, and anomalies that the LLM will later narrate. The architecture's grounding pattern (NFR7) is enforced here — every number in the final report originates from this stage's deterministic computation, not from the LLM.

The InsightPayload output contains five sections (FR3): `data_quality_findings` (forwarded from DQA), `summary` (per-column aggregations), `key_insights` (trends, comparisons), `anomalies` (outliers), and `recommendations` (data-driven suggestions). This JSON contract is the single source of truth for Story 1.4 (Narrative Generator) — if InsightPayload is wrong or incomplete, the narrative will hallucinate or omit critical findings.

The engine must gracefully handle datasets that lack date columns (no trends) or categorical columns (no segment comparisons) without failing. The output is always a valid InsightPayload, just with empty sections where data doesn't support the computation.

---

## Acceptance Criteria

The AC below comes verbatim from [epics.md](../planning-artifacts/epics.md). Do not reinterpret — implement to the letter.

**Given** a DataFrame that passed data quality assessment (non-halted PipelineResult) and its DataQualityReport
**When** `InsightEngine.generate_insights(df, quality_report)` is called
**Then** the engine computes: summary statistics (sum, avg, min, max, growth rate per numeric column), time-based trend detection (if a date column is identified), segment comparisons (if categorical columns exist), and outlier flagging (values beyond 2 standard deviations)
**And** the return type is a Pydantic-validated `InsightPayload` with five sections: `data_quality_findings`, `summary`, `key_insights`, `anomalies`, `recommendations`
**And** all numbers in the InsightPayload are deterministically computed from the DataFrame — no LLM involvement

**Given** a dataset with no date column
**When** insights are generated
**Then** time-based trend sections are populated with an empty list and a note indicating no temporal data was detected
**And** other insight sections are fully computed

**Given** a dataset with no categorical columns
**When** insights are generated
**Then** segment comparison sections are populated with an empty list
**And** other insight sections are fully computed

**Given** any insight generation run
**When** the computation completes
**Then** structlog entries are emitted with `pipeline_run_id`, `stage="insight_engine"`, computed metrics count, and detected anomaly count
**And** `backend/tests/test_insight_engine.py` passes with tests covering: full dataset (date + categories + numerics), numeric-only dataset, dataset with outliers, and empty/minimal dataset edge case

---

## Tasks / Subtasks

- [x] **Task 1 — Pydantic models: `InsightPayload` and supporting types** (AC: Pydantic-validated output with 5 sections)
  - [x] Create `backend/models/insight_payload.py`
  - [x] Define `ColumnSummary(BaseModel)` with fields:
    - `column_name: str`
    - `dtype: str` — `"numeric"`, `"categorical"`, `"datetime"`, `"other"`
    - `count: int` — non-null count
    - `null_count: int`
    - `null_pct: float`
    - `unique_count: int`
    - Numeric-only (all `float | None`): `sum_val`, `mean_val`, `min_val`, `max_val`, `std_val`, `median_val`, `q25_val`, `q75_val`
    - `growth_rate: float | None` — `(last_val - first_val) / first_val` if numeric column has ≥2 non-null values and first_val ≠ 0; `None` otherwise
    - Categorical-only: `top_values: list[dict[str, int | float]] | None` — top 10 value counts as `[{"value": "X", "count": 50, "pct": 25.0}]`
  - [x] Define `TrendPoint(BaseModel)` with fields:
    - `period: str` — ISO date string for the period start
    - `value: float`
    - `change_pct: float | None` — period-over-period percentage change
  - [x] Define `TrendAnalysis(BaseModel)` with fields:
    - `metric_column: str`
    - `date_column: str`
    - `trend_direction: str` — `"increasing"`, `"decreasing"`, `"stable"`, `"volatile"`
    - `trend_points: list[TrendPoint]`
    - `overall_change_pct: float | None` — first-to-last percentage change
    - `note: str` — one-sentence description of the trend
  - [x] Define `SegmentComparison(BaseModel)` with fields:
    - `segment_column: str` — the categorical column used for grouping
    - `metric_column: str` — the numeric column being compared
    - `segments: list[dict[str, float | int | str]]` — `[{"segment": "North", "mean": 500.0, "sum": 5000.0, "count": 10}]`
    - `note: str` — one-sentence comparison summary (e.g., "North leads with 35% of total revenue")
  - [x] Define `AnomalyRecord(BaseModel)` with fields:
    - `column_name: str`
    - `row_indices: list[int]` — indices of outlier rows (cap at first 20 to keep payload manageable)
    - `values: list[float]` — the outlier values (same cap)
    - `mean: float`
    - `std: float`
    - `threshold_sigma: float` — always `2.0` for this story
    - `count: int` — total number of outlier values
    - `pct: float` — percentage of column values that are outliers
    - `direction: str` — `"above"`, `"below"`, or `"both"`
  - [x] Define `Recommendation(BaseModel)` with fields:
    - `category: str` — `"data_quality"`, `"trend"`, `"anomaly"`, `"segment"`, `"general"`
    - `priority: str` — `"high"`, `"medium"`, `"low"`
    - `message: str` — one-sentence actionable recommendation
    - `related_columns: list[str]`
  - [x] Define `InsightPayload(BaseModel)` with fields:
    - `data_quality_findings: dict` — forwarded from `DataQualityReport.model_dump()` (the full DQA output, serialized)
    - `summary: list[ColumnSummary]` — per-column aggregation summaries
    - `key_insights: list[TrendAnalysis | SegmentComparison]` — trends and segment comparisons
    - `anomalies: list[AnomalyRecord]` — outlier detection results
    - `recommendations: list[Recommendation]` — data-driven suggestions
    - `metadata: dict` — `{"total_rows": int, "total_columns": int, "numeric_columns": int, "categorical_columns": int, "datetime_columns": int, "has_temporal_data": bool, "computed_at": str}`
  - [x] Sanitize all floats with the `_safe_float` helper pattern from Story 1.2 — no `NaN`/`Inf` in serialized Pydantic models
  - [x] Create basic model instantiation tests in `backend/tests/test_models.py` (append to existing if present, or create if not)

- [x] **Task 2 — `InsightEngine` class skeleton and column classification** (AC: engine receives DataFrame + DataQualityReport)
  - [x] Create `backend/pipeline/insight_engine.py` with `InsightEngine` class
  - [x] Define `generate_insights(df: pd.DataFrame, quality_report: DataQualityReport, pipeline_run_id: str) -> InsightPayload`
  - [x] Implement `_classify_columns(df: pd.DataFrame) -> dict[str, list[str]]`:
    - Returns `{"numeric": [...], "categorical": [...], "datetime": [...], "other": [...]}`
    - Numeric: `df.select_dtypes(include=[np.number])`
    - Datetime: columns that are `datetime64` dtype OR successfully parse via `pd.to_datetime(col, errors='coerce')` with ≥80% non-NaT results
    - Categorical: string/object columns with `unique_count < 0.5 * row_count` (heuristic: if more than half the values are unique, it's likely an ID, not a category)
    - Other: anything else
  - [x] Import structlog and bind `pipeline_run_id` via `structlog.contextvars.bind_contextvars` at method entry (same pattern as Story 1.2)

- [x] **Task 3 — Summary statistics computation** (AC: sum, avg, min, max, growth rate per numeric column)
  - [x] Implement `_compute_summary(df: pd.DataFrame, column_classes: dict) -> list[ColumnSummary]`:
    - For each column in the DataFrame, produce a `ColumnSummary`
    - **Numeric columns:** compute `sum`, `mean`, `min`, `max`, `std`, `median`, `q25` (25th percentile), `q75` (75th percentile) using pandas `.describe()` or individual calls
    - **Growth rate:** `(last_non_null - first_non_null) / abs(first_non_null)` where first/last are the first and last non-null values in column order; `None` if fewer than 2 non-null values or if `first_non_null == 0`
    - **Categorical columns:** compute `top_values` as top 10 by `value_counts()`, each entry `{"value": str(val), "count": int, "pct": float}`
    - **All columns:** `count`, `null_count`, `null_pct`, `unique_count`
    - Sanitize all float outputs with `_safe_float()` — never emit `NaN`/`Inf`

- [x] **Task 4 — Time-based trend detection** (AC: trend detection if date column exists; empty list if not)
  - [x] Implement `_detect_trends(df: pd.DataFrame, column_classes: dict) -> list[TrendAnalysis]`:
    - If `column_classes["datetime"]` is empty, return `[]` (caller adds metadata note)
    - Use the first datetime column as the time axis
    - For each numeric column, group by the detected time granularity:
      - Auto-detect granularity: if date range ≤ 90 days → daily; ≤ 730 days → weekly; else → monthly
      - Aggregate using `.resample()` or `.groupby(pd.Grouper(freq=...))` with `mean()` as the aggregation
    - Compute `TrendPoint` for each period: `value` (period mean), `change_pct` (vs previous period)
    - Determine `trend_direction`:
      - `"increasing"` if ≥70% of period-over-period changes are positive
      - `"decreasing"` if ≥70% of changes are negative
      - `"volatile"` if std of changes > mean of absolute changes
      - `"stable"` otherwise
    - `overall_change_pct`: `(last_period_value - first_period_value) / abs(first_period_value)`
    - `note`: auto-generated sentence like `"Revenue shows an increasing trend with 45% growth over the period"`
    - Cap at 100 trend points per metric to keep payload size manageable

- [x] **Task 5 — Segment comparisons** (AC: segment comparisons if categorical columns exist; empty list if not)
  - [x] Implement `_compute_segments(df: pd.DataFrame, column_classes: dict) -> list[SegmentComparison]`:
    - If `column_classes["categorical"]` is empty, return `[]`
    - For each categorical column × each numeric column, compute per-segment aggregates:
      - `groupby(categorical_col).agg({numeric_col: ["mean", "sum", "count"]})`
    - Cap at top 20 segments per categorical column (by count) to avoid explosion on high-cardinality columns
    - Limit total comparisons: at most 3 categorical columns × 5 numeric columns = 15 comparisons max; prioritize categorical columns with lower cardinality and numeric columns with higher variance
    - `note`: auto-generated, e.g., `"Region 'North' has the highest average revenue at $523.40 (35% of total)"`
    - Sanitize all floats

- [x] **Task 6 — Outlier detection** (AC: outlier flagging beyond 2 standard deviations)
  - [x] Implement `_detect_anomalies(df: pd.DataFrame, column_classes: dict) -> list[AnomalyRecord]`:
    - For each numeric column with `std > 0` (skip zero-variance — already flagged by DQA):
      - Compute `mean` and `std`
      - Flag values where `|value - mean| > 2 * std`
      - Record `row_indices` (first 20), `values` (first 20), `count`, `pct`
      - `direction`: `"above"` if all outliers are above mean, `"below"` if all below, `"both"` if mixed
    - Only emit `AnomalyRecord` if `count > 0` (no empty records)
    - Skip columns with fewer than 10 non-null values (insufficient data for meaningful outlier detection)

- [x] **Task 7 — Recommendations engine** (AC: recommendations section populated)
  - [x] Implement `_generate_recommendations(quality_report, summary, trends, segments, anomalies) -> list[Recommendation]`:
    - **Data quality recommendations** (from `quality_report`):
      - If `quality_report.has_critical_issues`: high-priority recommendation to address critical findings
      - For each HIGH-severity defect: medium-priority recommendation
    - **Trend recommendations** (from trends):
      - If any trend shows `"decreasing"` with `overall_change_pct < -20%`: high-priority alert about significant decline
      - If any trend shows `"volatile"`: medium-priority recommendation to investigate instability
    - **Anomaly recommendations** (from anomalies):
      - If any anomaly has `pct > 5%`: high-priority recommendation to review outlier values
      - If anomalies exist but are minor (<5%): low-priority informational note
    - **Segment recommendations** (from segments):
      - If the top segment accounts for >50% of a metric's total: medium-priority note about concentration risk
    - **General recommendations:**
      - If no date column exists: low-priority recommendation to add temporal data for trend analysis
      - If no categorical columns exist: low-priority recommendation to add segmentation dimensions

- [x] **Task 8 — Orchestrate `generate_insights` and build `InsightPayload`** (AC: complete InsightPayload returned)
  - [x] In `InsightEngine.generate_insights()`:
    1. Classify columns via `_classify_columns(df)`
    2. Compute summary via `_compute_summary(df, column_classes)`
    3. Detect trends via `_detect_trends(df, column_classes)`
    4. Compute segments via `_compute_segments(df, column_classes)`
    5. Detect anomalies via `_detect_anomalies(df, column_classes)`
    6. Generate recommendations via `_generate_recommendations(...)`
    7. Build metadata dict
    8. Construct and return `InsightPayload`
  - [x] Forward `quality_report.model_dump()` as `data_quality_findings`
  - [x] Set `metadata.has_temporal_data = len(column_classes["datetime"]) > 0`
  - [x] Set `metadata.computed_at` to `datetime.now(timezone.utc).isoformat()`
  - [x] If no date column: add a note to metadata or key_insights indicating temporal data was not detected

- [x] **Task 9 — structlog integration** (AC: structured logs with pipeline_run_id)
  - [x] Import `structlog` and call `structlog.get_logger()` inside the class
  - [x] Bind `pipeline_run_id` via `structlog.contextvars.bind_contextvars(pipeline_run_id=pipeline_run_id)` at method entry
  - [x] Log emit points:
    - On entry: `logger.info(event="insight_generation_started", stage="insight_engine", total_rows=..., total_columns=...)`
    - On column classification: `logger.debug(event="columns_classified", stage="insight_engine", numeric=len(...), categorical=len(...), datetime=len(...))`
    - On completion: `logger.info(event="insights_generated", stage="insight_engine", metrics_count=len(summary), anomaly_count=len(anomalies), trend_count=len(trends), segment_count=len(segments))`
  - [x] Do NOT log raw data values — only metadata (column names, counts, percentages)

- [x] **Task 10 — Test suite: `backend/tests/test_insight_engine.py`** (AC: all test scenarios pass)

  All tests use fixtures from `conftest.py` where applicable. Add module-local fixtures for specific scenarios.

  - [x] **10a — Full dataset (date + categories + numerics):**
    - `test_full_dataset_all_sections_populated`: DataFrame with date column, 2+ categorical columns, 3+ numeric columns → InsightPayload has non-empty `summary`, `key_insights` (trends + segments), `anomalies` or empty anomalies if no outliers, and `recommendations`
    - Assert `metadata.has_temporal_data == True`
    - Assert `len(summary) == total_columns`
    - Assert trends were computed for numeric columns

  - [x] **10b — Numeric-only dataset (no date, no categories):**
    - `test_numeric_only_no_trends_no_segments`: DataFrame with only numeric columns → `key_insights` contains no `TrendAnalysis` and no `SegmentComparison`
    - Assert `metadata.has_temporal_data == False`
    - Assert `summary` is fully populated with numeric stats
    - Assert `recommendations` contains note about missing temporal data

  - [x] **10c — Dataset with outliers:**
    - `test_outlier_detection_beyond_2_sigma`: DataFrame with known extreme values (e.g., column with mean=100, std=10, one value=200) → `anomalies` contains an `AnomalyRecord` for that column
    - Assert `AnomalyRecord.threshold_sigma == 2.0`
    - Assert outlier values are captured in `values` list
    - Assert `direction` is correct

  - [x] **10d — Empty/minimal dataset edge case:**
    - `test_minimal_dataset_single_row`: DataFrame with 1 row → InsightPayload is valid (no crash), growth_rate is `None`, trends empty, segments empty
    - `test_minimal_dataset_two_columns`: DataFrame with 1 numeric and 1 string column, 5 rows → summary populated, no trends (no date), segment attempted if string column qualifies

  - [x] **10e — No date column graceful handling:**
    - `test_no_date_column_trends_empty`: DataFrame with no datetime-parseable columns → `key_insights` has no `TrendAnalysis` entries, metadata notes temporal absence

  - [x] **10f — No categorical columns graceful handling:**
    - `test_no_categorical_columns_segments_empty`: DataFrame with only numeric + date columns → `key_insights` has no `SegmentComparison` entries

  - [x] **10g — Data quality report forwarding:**
    - `test_quality_report_forwarded`: Assert `InsightPayload.data_quality_findings` is the serialized `DataQualityReport` from the input

  - [x] **10h — Growth rate edge cases:**
    - `test_growth_rate_zero_start`: Column with first value 0 → `growth_rate` is `None` (avoid division by zero)
    - `test_growth_rate_negative_start`: Column with first value -100, last 50 → `growth_rate` computed correctly using `abs(first)`

  - [x] **10i — Structlog output:**
    - `test_structlog_emits_pipeline_run_id`: Call `generate_insights` with a `pipeline_run_id` and capture structlog output; assert `"pipeline_run_id"` and `"insight_engine"` appear in log

  - [x] **10j — Pydantic serialization:**
    - `test_insight_payload_serializes_cleanly`: Call `generate_insights` and then `result.model_dump_json()` — assert no serialization errors, no `NaN`/`Inf` in the JSON string

  - [x] All tests must pass with `pytest backend/tests/test_insight_engine.py -v`

- [x] **Task 11 — Verification pass** (AC: green test suite, no anti-patterns)
  - [x] Run `pytest backend/tests/test_insight_engine.py -v` — all tests pass
  - [x] Run `pytest backend/tests/` — existing Story 1.1 and 1.2 tests also still pass (no regressions)
  - [x] Verify no anti-patterns in `backend/pipeline/insight_engine.py` and `backend/models/insight_payload.py`:
    - No `warnings.filterwarnings`
    - No `except Exception: pass`
    - No `print()` statements
    - No hardcoded credentials or paths
    - All function signatures have type hints
  - [x] Verify `InsightEngine` does NOT import from `backend/api/`, `backend/agents/`, or any legacy module
  - [x] Verify `InsightPayload` serializes cleanly: `result.model_dump_json()` produces valid JSON with no `NaN`/`Inf`

---

## Dev Notes

### Developer Context — Why This Story Is Structured This Way

1. **This stage is purely computational — no LLM calls.** The Insight Engine computes statistics deterministically from the DataFrame. If you find yourself calling any LLM API, STOP — that is Story 1.4 (Narrative Generator). This boundary is load-bearing: NFR7 mandates that the LLM never computes numbers independently. Every number in the final report must originate from this stage.

2. **The `InsightPayload` is the LLM grounding contract.** Story 1.4's `NarrativeGenerator` receives this payload as structured input and writes narrative about it. If a number appears in the final report narrative, it must exist in `InsightPayload`. If `InsightPayload` omits a computed stat, the LLM cannot invent it.

3. **`DataQualityReport` is forwarded, not recomputed.** The `data_quality_findings` section of `InsightPayload` is the serialized output of Story 1.2's `DataQualityAssessor`. Do not re-run quality checks — just call `quality_report.model_dump()` and include it.

4. **Graceful degradation, not failure.** A dataset with no date column doesn't fail — it produces an InsightPayload with empty trend sections. Same for no categorical columns. The engine must always return a valid InsightPayload. The only failure mode is an exception from genuinely unexpected errors (disk, memory), which propagates as `PipelineStageError`.

5. **Outlier threshold is 2σ, not 5σ.** Story 1.2's DQA uses 5σ for statistical red flags (extreme outliers). This story's Insight Engine uses 2σ for general outlier detection. These are different purposes: DQA flags data quality defects (extreme), Insight Engine flags analytical outliers (broader). Do not confuse the two thresholds.

6. **The `pipeline_run_id` is passed in by the caller.** Same pattern as Story 1.2 — the orchestrator (Story 1.6) generates the UUID and passes it through. For testing, use the `pipeline_run_id` fixture from `conftest.py`.

7. **Cap output sizes.** Trend points capped at 100, outlier indices at 20, segments at 20 per category, total segment comparisons at 15. These caps prevent InsightPayload from growing unboundedly on large datasets, which would waste LLM tokens in Story 1.4.

### Project Structure Notes

This story creates exactly these new files:

```
backend/models/insight_payload.py                NEW
backend/pipeline/insight_engine.py               NEW
backend/tests/test_insight_engine.py             NEW
```

This story may append to:
- `backend/tests/test_models.py` — add InsightPayload model instantiation tests (if file exists from Story 1.2)

This story does NOT touch:
- `backend/models/quality_report.py` (created in Story 1.2 — consumed here, not modified)
- `backend/models/pipeline_result.py` (created in Story 1.1 — not used directly in this stage)
- `backend/pipeline/data_quality.py` (Story 1.2 — consumed, not modified)
- Any legacy module
- Any frontend file
- Any API file

### Architecture Compliance Checklist

| Rule | Source | How this story complies |
|---|---|---|
| Pydantic models for all pipeline I/O | [architecture.md] | `InsightPayload`, `ColumnSummary`, `TrendAnalysis`, `SegmentComparison`, `AnomalyRecord`, `Recommendation` are all `BaseModel` |
| All numbers computed deterministically | [architecture.md] NFR7 | InsightEngine uses pandas only — no LLM calls, no randomness |
| structlog for all logging | [architecture.md:542] | `structlog.get_logger()` used throughout; no `print()` |
| `pipeline_run_id` in every log entry | [project-context.md:140-144] | Bound via `structlog.contextvars.bind_contextvars` at method entry |
| Every module has a matching test file | [architecture.md:541] | `test_insight_engine.py` for `insight_engine.py` |
| No import from legacy modules | [project-context.md:112-118] | `insight_engine.py` imports from `backend/models/` only |
| Type hints on every function signature | [project-context.md:58] | All new Python code fully annotated |
| Three-layer separation | [architecture.md:741-747] | `InsightEngine` is in `pipeline/` (Business Logic); no HTTP or DB imports |
| No raw dicts between pipeline stages | [architecture.md:430] | Returns `InsightPayload` Pydantic model, not `dict` |

### Library / Framework Requirements

These libraries must already be in `backend/requirements.txt` from Story 1.1. Confirm before implementing:

```
pydantic>=2.7          # InsightPayload and all sub-models
pandas>=2.2            # DataFrame analytics, groupby, resample
numpy>=1.26            # Numeric computation, std/mean
structlog==25.5.0      # JSON structured logging
pytest>=8.2            # Test runner
```

No new dependencies are introduced in this story.

Key pandas operations:
- `df.select_dtypes(include=[np.number])` for numeric column detection
- `pd.to_datetime(col, errors='coerce')` for datetime detection
- `df.groupby(col).agg(...)` for segment comparisons
- `df.set_index(date_col).resample(freq)` for time-based trends
- `df[col].describe()` for summary statistics
- `df[col].value_counts()` for categorical top values

### Float Sanitization

Reuse the `_safe_float` pattern from Story 1.2:

```python
import math

def _safe_float(val: float | None) -> float | None:
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return float(val)
```

Apply this to EVERY float that goes into a Pydantic model. pandas `.mean()`, `.std()`, etc. return `np.nan` for empty series — these must be sanitized to `None`.

### Testing Requirements

**Framework:** pytest with fixtures from `backend/tests/conftest.py` (established in Story 1.1).

**Fixture reuse:** `clean_sales_df` and `pipeline_run_id` from `conftest.py`. The `dirty_sales_df` is NOT suitable for Insight Engine tests because it would halt at DQA. Create local fixtures with clean data.

**DataQualityReport fixture:** Tests need a `DataQualityReport` to pass to `generate_insights`. Create a local fixture that builds a minimal clean report:

```python
@pytest.fixture
def clean_quality_report():
    """A DataQualityReport representing a clean dataset (no critical issues)."""
    from backend.models.quality_report import DataQualityReport, Severity
    return DataQualityReport(
        overall_severity=Severity.LOW,
        has_critical_issues=False,
        halt_reason=None,
        defects=[],
        column_profiles={},
        total_rows=100,
        total_columns=4,
        overall_quality_score=100.0,
        assessed_at="2026-01-01T00:00:00Z",
    )
```

**Full dataset fixture for trend/segment testing:**

```python
@pytest.fixture
def full_sales_df():
    """DataFrame with date, categorical, and numeric columns for complete testing."""
    import pandas as pd
    import numpy as np
    np.random.seed(42)
    n = 200
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    regions = np.random.choice(["North", "South", "East", "West"], size=n)
    categories = np.random.choice(["Electronics", "Clothing", "Food"], size=n)
    revenue = np.random.normal(500, 100, size=n).clip(0)
    quantity = np.random.randint(1, 50, size=n)
    return pd.DataFrame({
        "date": dates,
        "region": regions,
        "category": categories,
        "revenue": revenue,
        "quantity": quantity,
    })
```

**Outlier fixture:**

```python
@pytest.fixture
def outlier_df():
    """DataFrame with known outlier values beyond 2 sigma."""
    import pandas as pd
    import numpy as np
    values = [100.0] * 98 + [500.0, 600.0]  # mean ~104, std ~50; 500/600 are >2σ
    return pd.DataFrame({
        "metric": values,
        "label": ["A"] * 50 + ["B"] * 50,
    })
```

**Test assertion pattern:** Assert on `InsightPayload` fields:

```python
def test_full_dataset_all_sections_populated(full_sales_df, clean_quality_report, pipeline_run_id):
    engine = InsightEngine()
    result = engine.generate_insights(full_sales_df, clean_quality_report, pipeline_run_id=pipeline_run_id)

    assert isinstance(result, InsightPayload)
    assert len(result.summary) == 5  # date + region + category + revenue + quantity
    assert result.metadata["has_temporal_data"] is True
    assert any(isinstance(i, TrendAnalysis) for i in result.key_insights)
    assert any(isinstance(i, SegmentComparison) for i in result.key_insights)
    assert isinstance(result.data_quality_findings, dict)
```

### Previous Story Intelligence

**Story 1.2 established:**
- `backend/models/quality_report.py` with `DataQualityReport`, `DataQualityDefect`, `ColumnProfile`, `Severity`, `DefectCategory`
- `backend/pipeline/data_quality.py` with `DataQualityAssessor`
- `backend/tests/conftest.py` with `clean_sales_df`, `dirty_sales_df`, `pipeline_run_id` fixtures
- structlog pattern: `structlog.get_logger()` inside class, `bind_contextvars` for `pipeline_run_id`
- `_safe_float()` helper for NaN/Inf sanitization
- Pandera 0.32.0 installed (newer than spec's 0.30.1)
- Python 3.13.7 used for test execution

**Story 1.2 completion notes (relevant learnings):**
- Date format inconsistency and date monotonicity checks were partially implemented — Story 1.3 should not assume these checks exist in DQA output
- Model file is `quality_report.py` (not `data_quality_report.py`)
- `PipelineResult` uses `@dataclass`, not `BaseModel` — it's a dataclass from Story 1.1

**Import paths to use:**

```python
from backend.models.quality_report import DataQualityReport, Severity
from backend.models.insight_payload import InsightPayload  # Created in THIS story
from backend.errors.exceptions import PipelineStageError    # For unexpected failures
```

### Git Intelligence

Recent commits are focused on frontend/dashboard work (analytics mock backend, dataset manager, download support). No commits relevant to pipeline backend. The pipeline code from Stories 1.1 and 1.2 is in `review` status and may exist on a separate branch — the dev agent should verify that Story 1.1/1.2 code exists at `backend/models/quality_report.py` and `backend/pipeline/data_quality.py` before implementing. If these files don't exist on the current branch, the dev agent must either merge/rebase from the story branches or create the necessary imports with appropriate stubs.

### Reference

- User story + BDD AC: [epics.md](../planning-artifacts/epics.md) — Story 1.3 section
- FR3 specifics: [prd.md](../planning-artifacts/prd.md) — Phase 1 Deliverables → Insight Engine
- InsightPayload model: [architecture.md](../planning-artifacts/architecture.md) — Pipeline Stage Inventory, models/insight_payload.py
- LLM grounding pattern (NFR7): [architecture.md](../planning-artifacts/architecture.md) — Non-Functional Requirements
- Pipeline data flow: [architecture.md](../planning-artifacts/architecture.md) — Data Flow (Pipeline) diagram
- 2σ outlier threshold: [epics.md](../planning-artifacts/epics.md) — Story 1.3 AC ("values beyond 2 standard deviations")
- 5σ threshold (DQA, different purpose): [epics.md](../planning-artifacts/epics.md) — Story 1.2 AC
- Anti-patterns (9 rules): [project-context.md](../project-context.md) — Anti-patterns section
- Error handling strategy: [architecture.md](../planning-artifacts/architecture.md) — Error Handling (Dual Strategy)

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — all tests passed on first complete run.

### Completion Notes List

- All 7 Pydantic models created in `backend/models/insight_payload.py`
- `InsightEngine` with all 7 private methods implemented in `backend/pipeline/insight_engine.py`
- `_safe_float` sanitization applied to every float entering Pydantic models
- 2σ outlier detection (distinct from DQA's 5σ) with caps: 20 indices, 100 trend points, 20 segments, 15 comparisons
- Graceful degradation: empty trends/segments when datetime/categorical columns absent
- structlog with `pipeline_run_id` via `bind_contextvars`, 3 emit points (started, classified, generated)
- Growth rate uses `abs(first_non_null)` denominator per spec
- `pd.to_datetime(format="mixed")` to suppress pandas format inference warning
- Full test suite: 16 tests across 10 groups (10a–10j), all passing
- 67 total backend tests pass with zero regressions

### File List

- `backend/models/insight_payload.py` — NEW (7 Pydantic models)
- `backend/pipeline/insight_engine.py` — NEW (InsightEngine class)
- `backend/tests/test_insight_engine.py` — NEW (16 tests)
- `backend/tests/test_models.py` — MODIFIED (added InsightPayload model tests)
