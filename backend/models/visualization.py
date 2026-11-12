"""Typed visualization contracts for Story 3.7.

Charts are analyst-specified only. Every produced chart carries an
analysis_class tag so later capability enforcement can gate by class
without maintaining a parallel chart allowlist.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AnalysisClass(StrEnum):
    DESCRIPTIVE = "descriptive"
    DIAGNOSTIC_BASIC = "diagnostic_basic"
    DIAGNOSTIC_ADVANCED = "diagnostic_advanced"
    PREDICTIVE = "predictive"
    PRESCRIPTIVE = "prescriptive"
    DECISION_TRACE = "decision_trace"


class ChartType(StrEnum):
    MISSING_VALUES_BEFORE_AFTER = "missing_values_before_after"
    DISTRIBUTION_BEFORE_AFTER = "distribution_before_after"
    DISTRIBUTION = "distribution"
    TOP_VALUES = "top_values"


class ChartSpec(BaseModel):
    """One analyst-selected chart definition."""

    model_config = ConfigDict(extra="forbid")

    chart_type: ChartType
    column: str | None = None
    columns: list[str] | None = None
    limit: int | None = None

    @model_validator(mode="after")
    def _validate_shape(self) -> "ChartSpec":
        if self.chart_type == ChartType.MISSING_VALUES_BEFORE_AFTER:
            if self.column is not None:
                raise ValueError(
                    "visualizations.charts[].column is not allowed for "
                    "missing_values_before_after; use columns"
                )
            if self.limit is not None:
                raise ValueError(
                    "visualizations.charts[].limit is only allowed for top_values"
                )
            if self.columns is not None:
                if not self.columns:
                    raise ValueError(
                        "visualizations.charts[].columns must contain at least one column"
                    )
                if len(self.columns) > 30:
                    raise ValueError(
                        "visualizations.charts[].columns supports at most 30 columns"
                    )
                if len(set(self.columns)) != len(self.columns):
                    raise ValueError(
                        "visualizations.charts[].columns must not contain duplicates"
                    )
            return self

        if self.columns is not None:
            raise ValueError(
                "visualizations.charts[].columns is only allowed for "
                "missing_values_before_after"
            )
        if not self.column:
            raise ValueError(
                f"visualizations.charts[].column is required for {self.chart_type.value}"
            )

        if self.chart_type == ChartType.TOP_VALUES:
            if self.limit is None:
                self.limit = 10
            if not 1 <= self.limit <= 20:
                raise ValueError("visualizations.charts[].limit must be between 1 and 20")
        elif self.limit is not None:
            raise ValueError(
                "visualizations.charts[].limit is only allowed for top_values"
            )

        return self


class VisualizationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    charts: list[ChartSpec] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def _reject_duplicate_specs(self) -> "VisualizationConfig":
        fingerprints = [
            (
                chart.chart_type.value,
                chart.column,
                tuple(chart.columns or ()),
                chart.limit,
            )
            for chart in self.charts
        ]
        if len(set(fingerprints)) != len(fingerprints):
            raise ValueError("visualizations.charts must not contain duplicate chart specs")
        return self


class ChartSeries(BaseModel):
    label: str
    values: list[float]


class ChartData(BaseModel):
    """Deterministic, renderer-independent chart data."""

    chart_type: ChartType
    analysis_class: AnalysisClass
    title: str
    caption: str
    labels: list[str] = Field(default_factory=list)
    series: list[ChartSeries] = Field(default_factory=list)
    bin_edges: list[float] = Field(default_factory=list)
    truncated: bool = False


class NotProducedReason(StrEnum):
    CLEANING_NOT_ENABLED = "cleaning_not_enabled"
    COLUMN_NOT_FOUND = "column_not_found"
    COLUMN_NOT_FOUND_CLEANED = "column_not_found_cleaned"
    NO_NUMERIC_VALUES = "no_numeric_values"
    CHART_RENDER_FAILED = "chart_render_failed"


_CLIENT_REASON_TEXT: dict[NotProducedReason, str] = {
    NotProducedReason.CLEANING_NOT_ENABLED: "cleaning was not enabled for this run",
    NotProducedReason.COLUMN_NOT_FOUND: "column not found",
    NotProducedReason.COLUMN_NOT_FOUND_CLEANED: "column not found in the cleaned working copy",
    NotProducedReason.NO_NUMERIC_VALUES: "column has no numeric values",
    NotProducedReason.CHART_RENDER_FAILED: "chart could not be rendered",
}


class NotProducedChart(BaseModel):
    chart_type: ChartType
    title: str
    reason: NotProducedReason

    @property
    def reason_text(self) -> str:
        return _CLIENT_REASON_TEXT[self.reason]


class Visualization(BaseModel):
    """Report-ready chart populated server-side after narrative generation."""

    chart_type: ChartType
    analysis_class: AnalysisClass
    title: str
    caption: str
    image_base64: str
    data: ChartData

    @property
    def data_uri(self) -> str:
        """Return the only URI form renderers may embed for chart images."""
        return "data:image/png;base64," + self.image_base64
