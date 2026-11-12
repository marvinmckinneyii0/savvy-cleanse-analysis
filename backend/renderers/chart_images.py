"""Headless PNG rendering for Story 3.7 visualizations."""

from __future__ import annotations

from io import BytesIO

import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from backend.models.visualization import ChartData, ChartType

_MAX_LABEL_LEN = 40


def _label(text: str) -> str:
    if len(text) <= _MAX_LABEL_LEN:
        return text
    return text[: _MAX_LABEL_LEN - 1].rstrip() + "…"


def render_chart_png(chart: ChartData) -> bytes:
    """Render one deterministic chart with no pyplot/global figure state."""

    with matplotlib.rc_context({"text.parse_math": False, "text.usetex": False}):
        figure = Figure(figsize=(8.0, 4.5), dpi=120, tight_layout=True)
        canvas = FigureCanvasAgg(figure)
        axis = figure.add_subplot(1, 1, 1)
        axis.set_title(_label(chart.title))

        labels = [_label(value) for value in chart.labels]

        if chart.chart_type == ChartType.MISSING_VALUES_BEFORE_AFTER:
            positions = list(range(len(labels)))
            width = 0.38
            original = chart.series[0].values
            cleaned = chart.series[1].values
            axis.bar(
                [position - width / 2 for position in positions],
                original,
                width=width,
                label="Original data",
                color="#7f7f7f",
                hatch="//",
            )
            axis.bar(
                [position + width / 2 for position in positions],
                cleaned,
                width=width,
                label="Cleaned working copy",
                color="#1f77b4",
                alpha=0.85,
            )
            axis.set_xticks(positions, labels, rotation=45, ha="right")
            axis.set_ylabel("Missing values")
            axis.legend()

        elif chart.chart_type in {
            ChartType.DISTRIBUTION,
            ChartType.DISTRIBUTION_BEFORE_AFTER,
        }:
            positions = list(range(len(labels)))
            if chart.chart_type == ChartType.DISTRIBUTION_BEFORE_AFTER:
                width = 0.42
                axis.bar(
                    [position - width / 2 for position in positions],
                    chart.series[0].values,
                    width=width,
                    label="Original data",
                    color="#7f7f7f",
                    hatch="//",
                )
                axis.bar(
                    [position + width / 2 for position in positions],
                    chart.series[1].values,
                    width=width,
                    label="Cleaned working copy",
                    color="#1f77b4",
                    alpha=0.85,
                )
                axis.legend()
            else:
                axis.bar(
                    positions,
                    chart.series[0].values,
                    width=0.8,
                    label="Original data",
                    color="#7f7f7f",
                )
            tick_step = max(1, len(labels) // 8)
            tick_positions = positions[::tick_step]
            tick_labels = labels[::tick_step]
            axis.set_xticks(tick_positions, tick_labels, rotation=35, ha="right")
            axis.set_ylabel("Count")

        elif chart.chart_type == ChartType.TOP_VALUES:
            positions = list(range(len(labels)))
            axis.barh(
                positions,
                chart.series[0].values,
                color="#1f77b4",
            )
            axis.set_yticks(positions, labels)
            axis.invert_yaxis()
            axis.set_xlabel("Count")

        axis.grid(axis="y", alpha=0.2)
        output = BytesIO()
        canvas.print_png(output, metadata={"Software": None})
        return output.getvalue()
