"""Pure chart-data construction for Story 3.7."""

from __future__ import annotations

import numpy as np
import pandas as pd

from backend.models.healing_manifest import REPORT_SEMANTICS_DISCLOSURE
from backend.models.visualization import (
    AnalysisClass,
    ChartData,
    ChartSeries,
    ChartSpec,
    ChartType,
    NotProducedChart,
    NotProducedReason,
    VisualizationConfig,
)

_HISTOGRAM_BINS = 20
_MAX_MISSING_COLUMNS = 30


def _title(spec: ChartSpec) -> str:
    if spec.chart_type == ChartType.MISSING_VALUES_BEFORE_AFTER:
        return "Missing Values — Original vs Cleaned Working Copy"
    if spec.chart_type == ChartType.DISTRIBUTION_BEFORE_AFTER:
        return f"Distribution — {spec.column} — Original vs Cleaned Working Copy"
    if spec.chart_type == ChartType.DISTRIBUTION:
        return f"Distribution — {spec.column}"
    return f"Top Values — {spec.column}"


def _not_produced(spec: ChartSpec, reason: NotProducedReason) -> NotProducedChart:
    return NotProducedChart(chart_type=spec.chart_type, title=_title(spec), reason=reason)


def _numeric_values(df: pd.DataFrame, column: str) -> np.ndarray | None:
    if column not in df.columns:
        return None
    if not pd.api.types.is_numeric_dtype(df[column]):
        return np.array([], dtype=float)
    values = pd.to_numeric(df[column], errors="coerce").dropna().to_numpy(dtype=float)
    return values


def _fixed_edges(values: np.ndarray) -> np.ndarray:
    low = float(values.min())
    high = float(values.max())
    if low == high:
        padding = 0.5 if low == 0 else max(abs(low) * 0.05, 0.5)
        low -= padding
        high += padding
    return np.linspace(low, high, _HISTOGRAM_BINS + 1)


def _distribution(
    original: pd.DataFrame,
    cleaned: pd.DataFrame | None,
    spec: ChartSpec,
) -> tuple[ChartData | None, NotProducedChart | None]:
    assert spec.column is not None
    if spec.column not in original.columns:
        return None, _not_produced(spec, NotProducedReason.COLUMN_NOT_FOUND)

    before = _numeric_values(original, spec.column)
    assert before is not None
    if before.size == 0:
        return None, _not_produced(spec, NotProducedReason.NO_NUMERIC_VALUES)

    after: np.ndarray | None = None
    if spec.chart_type == ChartType.DISTRIBUTION_BEFORE_AFTER:
        if cleaned is None:
            return None, _not_produced(spec, NotProducedReason.CLEANING_NOT_ENABLED)
        if spec.column not in cleaned.columns:
            return None, _not_produced(spec, NotProducedReason.COLUMN_NOT_FOUND_CLEANED)
        after = _numeric_values(cleaned, spec.column)
        assert after is not None
        if after.size == 0:
            return None, _not_produced(spec, NotProducedReason.NO_NUMERIC_VALUES)

    edges = _fixed_edges(before)
    before_counts, _ = np.histogram(before, bins=edges)
    series = [ChartSeries(label="Original data", values=before_counts.astype(float).tolist())]
    caption = "Histogram of the original data using 20 fixed bins."
    if after is not None:
        after_counts, _ = np.histogram(after, bins=edges)
        series.append(
            ChartSeries(label="Cleaned working copy", values=after_counts.astype(float).tolist())
        )
        caption = (
            "Original data and cleaned working copy use shared bin edges. "
            + REPORT_SEMANTICS_DISCLOSURE
        )

    labels = [
        f"{edges[i]:.4g}–{edges[i + 1]:.4g}" for i in range(len(edges) - 1)
    ]
    return (
        ChartData(
            chart_type=spec.chart_type,
            analysis_class=AnalysisClass.DESCRIPTIVE,
            title=_title(spec),
            caption=caption,
            labels=labels,
            series=series,
            bin_edges=edges.astype(float).tolist(),
        ),
        None,
    )


def _missing_before_after(
    original: pd.DataFrame,
    cleaned: pd.DataFrame | None,
    spec: ChartSpec,
) -> tuple[ChartData | None, NotProducedChart | None]:
    if cleaned is None:
        return None, _not_produced(spec, NotProducedReason.CLEANING_NOT_ENABLED)

    if spec.columns is None:
        missing = [
            (str(column), int(original[column].isna().sum()))
            for column in original.columns
            if int(original[column].isna().sum()) > 0
        ]
        missing.sort(key=lambda item: (-item[1], item[0]))
        selected = [column for column, _ in missing]
    else:
        selected = list(spec.columns)

    if any(column not in original.columns for column in selected):
        return None, _not_produced(spec, NotProducedReason.COLUMN_NOT_FOUND)
    if any(column not in cleaned.columns for column in selected):
        return None, _not_produced(spec, NotProducedReason.COLUMN_NOT_FOUND_CLEANED)

    truncated = len(selected) > _MAX_MISSING_COLUMNS
    selected = selected[:_MAX_MISSING_COLUMNS]

    before = [float(original[column].isna().sum()) for column in selected]
    after = [float(cleaned[column].isna().sum()) for column in selected]
    caption = REPORT_SEMANTICS_DISCLOSURE
    if truncated:
        caption += " Display is limited to the first 30 columns by missing-value count."

    return (
        ChartData(
            chart_type=spec.chart_type,
            analysis_class=AnalysisClass.DESCRIPTIVE,
            title=_title(spec),
            caption=caption,
            labels=selected,
            series=[
                ChartSeries(label="Original data", values=before),
                ChartSeries(label="Cleaned working copy", values=after),
            ],
            truncated=truncated,
        ),
        None,
    )


def _top_values(
    original: pd.DataFrame,
    spec: ChartSpec,
) -> tuple[ChartData | None, NotProducedChart | None]:
    assert spec.column is not None
    if spec.column not in original.columns:
        return None, _not_produced(spec, NotProducedReason.COLUMN_NOT_FOUND)

    limit = spec.limit or 10
    values = original[spec.column].astype("string").fillna("<missing>")
    counts = values.value_counts(dropna=False)
    ordered = sorted(
        ((str(value), int(count)) for value, count in counts.items()),
        key=lambda item: (-item[1], item[0]),
    )[:limit]

    return (
        ChartData(
            chart_type=spec.chart_type,
            analysis_class=AnalysisClass.DESCRIPTIVE,
            title=_title(spec),
            caption=f"Most frequent values in the original data; top {limit} shown.",
            labels=[value for value, _ in ordered],
            series=[
                ChartSeries(
                    label="Original data",
                    values=[float(count) for _, count in ordered],
                )
            ],
        ),
        None,
    )


def build_visualization_data(
    df_original: pd.DataFrame,
    df_cleaned: pd.DataFrame | None,
    config: VisualizationConfig,
) -> tuple[list[ChartData], list[NotProducedChart]]:
    """Build deterministic chart data without mutating either input frame."""

    charts: list[ChartData] = []
    not_produced: list[NotProducedChart] = []

    for spec in config.charts:
        if spec.chart_type == ChartType.MISSING_VALUES_BEFORE_AFTER:
            chart, unavailable = _missing_before_after(df_original, df_cleaned, spec)
        elif spec.chart_type in {
            ChartType.DISTRIBUTION,
            ChartType.DISTRIBUTION_BEFORE_AFTER,
        }:
            chart, unavailable = _distribution(df_original, df_cleaned, spec)
        else:
            chart, unavailable = _top_values(df_original, spec)

        if chart is not None:
            charts.append(chart)
        if unavailable is not None:
            not_produced.append(unavailable)

    return charts, not_produced
