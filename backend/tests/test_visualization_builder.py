"""Story 3.7 deterministic chart-data builder tests."""

from __future__ import annotations

import pandas as pd
from pandas.testing import assert_frame_equal

from backend.models.visualization import (
    ChartSpec,
    ChartType,
    NotProducedReason,
    VisualizationConfig,
)
from backend.pipeline.visualization_builder import build_visualization_data


def test_missing_values_before_after_uses_original_and_cleaned_frames() -> None:
    original = pd.DataFrame(
        {"a": [1, None, None], "b": ["x", None, "y"], "c": [1, 2, 3]}
    )
    cleaned = pd.DataFrame(
        {"a": [1, 2, None], "b": ["x", "x", "y"], "c": [1, 2, 3]}
    )
    before_copy = original.copy(deep=True)

    charts, unavailable = build_visualization_data(
        original,
        cleaned,
        VisualizationConfig(
            charts=[ChartSpec(chart_type=ChartType.MISSING_VALUES_BEFORE_AFTER)]
        ),
    )

    assert unavailable == []
    chart = charts[0]
    assert chart.labels == ["a", "b"]
    assert chart.series[0].values == [2.0, 1.0]
    assert chart.series[1].values == [1.0, 0.0]
    assert_frame_equal(original, before_copy)


def test_missing_values_default_order_and_cap_is_deterministic() -> None:
    data = {
        f"c{i:02d}": ([None, None, i] if i % 2 == 0 else [None, i, i])
        for i in range(35)
    }
    original = pd.DataFrame(data)
    cleaned = original.fillna(0)

    charts, unavailable = build_visualization_data(
        original,
        cleaned,
        VisualizationConfig(
            charts=[ChartSpec(chart_type=ChartType.MISSING_VALUES_BEFORE_AFTER)]
        ),
    )

    assert unavailable == []
    assert len(charts[0].labels) == 30
    assert charts[0].truncated is True
    expected = sorted(
        original.columns,
        key=lambda col: (-int(original[col].isna().sum()), str(col)),
    )[:30]
    assert charts[0].labels == list(expected)


def test_distribution_before_after_shares_fixed_edges() -> None:
    original = pd.DataFrame({"value": [0.0, 1.0, 2.0, 3.0]})
    cleaned = pd.DataFrame({"value": [0.0, 1.0, 1.0, 3.0]})

    charts, unavailable = build_visualization_data(
        original,
        cleaned,
        VisualizationConfig(
            charts=[
                ChartSpec(
                    chart_type=ChartType.DISTRIBUTION_BEFORE_AFTER,
                    column="value",
                )
            ]
        ),
    )

    assert unavailable == []
    chart = charts[0]
    assert len(chart.bin_edges) == 21
    assert len(chart.series) == 2
    assert sum(chart.series[0].values) == 4.0
    assert sum(chart.series[1].values) == 4.0


def test_top_values_orders_count_desc_then_label_asc() -> None:
    original = pd.DataFrame({"region": ["b", "a", "b", "a", "c"]})

    charts, unavailable = build_visualization_data(
        original,
        None,
        VisualizationConfig(
            charts=[ChartSpec(chart_type=ChartType.TOP_VALUES, column="region", limit=3)]
        ),
    )

    assert unavailable == []
    assert charts[0].labels == ["a", "b", "c"]
    assert charts[0].series[0].values == [2.0, 2.0, 1.0]


def test_before_after_without_cleaning_is_not_produced() -> None:
    original = pd.DataFrame({"value": [1.0, 2.0, 3.0]})

    charts, unavailable = build_visualization_data(
        original,
        None,
        VisualizationConfig(
            charts=[
                ChartSpec(
                    chart_type=ChartType.DISTRIBUTION_BEFORE_AFTER,
                    column="value",
                )
            ]
        ),
    )

    assert charts == []
    assert unavailable[0].reason == NotProducedReason.CLEANING_NOT_ENABLED
    assert unavailable[0].reason_text == "cleaning was not enabled for this run"


def test_missing_column_and_non_numeric_are_client_safe_unavailable() -> None:
    original = pd.DataFrame({"region": ["a", "b"]})
    config = VisualizationConfig(
        charts=[
            ChartSpec(chart_type=ChartType.DISTRIBUTION, column="missing"),
            ChartSpec(chart_type=ChartType.DISTRIBUTION, column="region"),
        ]
    )

    charts, unavailable = build_visualization_data(original, None, config)

    assert charts == []
    assert [item.reason for item in unavailable] == [
        NotProducedReason.COLUMN_NOT_FOUND,
        NotProducedReason.NO_NUMERIC_VALUES,
    ]
    assert [item.reason_text for item in unavailable] == [
        "column not found",
        "column has no numeric values",
    ]


def test_same_input_produces_equal_chart_data() -> None:
    frame = pd.DataFrame({"value": [1.0, 2.0, 3.0, 4.0]})
    config = VisualizationConfig(
        charts=[ChartSpec(chart_type=ChartType.DISTRIBUTION, column="value")]
    )
    first, _ = build_visualization_data(frame, None, config)
    second, _ = build_visualization_data(frame, None, config)
    assert first == second
