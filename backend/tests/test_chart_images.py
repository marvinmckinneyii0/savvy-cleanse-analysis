"""Story 3.7 chart image renderer tests."""

from __future__ import annotations

from pathlib import Path

from backend.models.visualization import (
    AnalysisClass,
    ChartData,
    ChartSeries,
    ChartType,
)
from backend.renderers.chart_images import render_chart_png

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chart(chart_type: ChartType) -> ChartData:
    if chart_type == ChartType.MISSING_VALUES_BEFORE_AFTER:
        return ChartData(
            chart_type=chart_type,
            analysis_class=AnalysisClass.DESCRIPTIVE,
            title="Missing $x^2$ values",
            caption="caption",
            labels=["$x^2$", "region"],
            series=[
                ChartSeries(label="Original data", values=[3, 1]),
                ChartSeries(label="Cleaned working copy", values=[1, 0]),
            ],
        )
    if chart_type == ChartType.TOP_VALUES:
        return ChartData(
            chart_type=chart_type,
            analysis_class=AnalysisClass.DESCRIPTIVE,
            title="Top Values",
            caption="caption",
            labels=["$x^2$", "very-long-" + "x" * 80],
            series=[ChartSeries(label="Original data", values=[4, 2])],
        )
    return ChartData(
        chart_type=chart_type,
        analysis_class=AnalysisClass.DESCRIPTIVE,
        title="Distribution $x^2$",
        caption="caption",
        labels=["0–1", "1–2"],
        series=[
            ChartSeries(label="Original data", values=[2, 3]),
            *(
                [ChartSeries(label="Cleaned working copy", values=[1, 4])]
                if chart_type == ChartType.DISTRIBUTION_BEFORE_AFTER
                else []
            ),
        ],
        bin_edges=[0.0, 1.0, 2.0],
    )


def test_all_chart_types_render_valid_png_bytes() -> None:
    for chart_type in ChartType:
        png = render_chart_png(_chart(chart_type))
        assert png.startswith(PNG_SIGNATURE)
        assert len(png) > len(PNG_SIGNATURE)


def test_hostile_mathtext_like_label_renders_literally_without_error() -> None:
    png = render_chart_png(_chart(ChartType.TOP_VALUES))
    assert png.startswith(PNG_SIGNATURE)


def test_renderer_does_not_import_pyplot() -> None:
    source = Path("backend/renderers/chart_images.py").read_text(encoding="utf-8")
    assert "import matplotlib.pyplot" not in source
    assert "from matplotlib import pyplot" not in source
