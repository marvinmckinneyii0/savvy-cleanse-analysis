"""Insight Engine Pydantic models.

Defines the output contract for :class:`InsightEngine`: per-column summaries,
trend analyses, segment comparisons, anomaly records, recommendations, and the
aggregate :class:`InsightPayload` envelope.
"""

from __future__ import annotations

from pydantic import BaseModel


class ColumnSummary(BaseModel):
    """Per-column aggregation summary."""

    column_name: str
    dtype: str
    count: int
    null_count: int
    null_pct: float
    unique_count: int
    sum_val: float | None = None
    mean_val: float | None = None
    min_val: float | None = None
    max_val: float | None = None
    std_val: float | None = None
    median_val: float | None = None
    q25_val: float | None = None
    q75_val: float | None = None
    growth_rate: float | None = None
    top_values: list[dict[str, str | int | float]] | None = None


class TrendPoint(BaseModel):
    """A single data point in a time-based trend."""

    period: str
    value: float
    change_pct: float | None = None


class TrendAnalysis(BaseModel):
    """Time-based trend detection result for a numeric metric."""

    metric_column: str
    date_column: str
    trend_direction: str
    trend_points: list[TrendPoint]
    overall_change_pct: float | None = None
    note: str


class SegmentComparison(BaseModel):
    """Cross-segment comparison of a numeric metric by a categorical column."""

    segment_column: str
    metric_column: str
    segments: list[dict[str, float | int | str]]
    note: str


class AnomalyRecord(BaseModel):
    """Outlier detection result for a numeric column (2-sigma threshold)."""

    column_name: str
    row_indices: list[int]
    values: list[float]
    mean: float
    std: float
    threshold_sigma: float
    count: int
    pct: float
    direction: str


class Recommendation(BaseModel):
    """Data-driven recommendation based on computed insights."""

    category: str
    priority: str
    message: str
    related_columns: list[str]


class InsightPayload(BaseModel):
    """Aggregate insight payload — the single output of the Insight Engine."""

    data_quality_findings: dict
    summary: list[ColumnSummary]
    key_insights: list[TrendAnalysis | SegmentComparison]
    anomalies: list[AnomalyRecord]
    recommendations: list[Recommendation]
    metadata: dict
