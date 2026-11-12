"""Story 3.7 orchestrator wiring and LLM-isolation tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from backend.models.insight_report import InsightReport, NarrativeSection
from backend.models.visualization import (
    ChartSpec,
    ChartType,
    NotProducedReason,
    VisualizationConfig,
)
from backend.pipeline.orchestrator import run_full_pipeline

_SAMPLE_DATA = Path(__file__).parent / "sample_data"
_CRITICAL_CSV = _SAMPLE_DATA / "critical_quality_issues.csv"


def _without_run_timestamps(value):
    """Remove only runtime-generated timestamps before payload equality checks."""
    if isinstance(value, dict):
        return {
            key: _without_run_timestamps(item)
            for key, item in value.items()
            if key not in {"generated_at", "computed_at", "assessed_at", "timestamp"}
        }
    if isinstance(value, list):
        return [_without_run_timestamps(item) for item in value]
    return value


def _report() -> InsightReport:
    return InsightReport(
        executive_summary="Offline narrative.",
        key_findings=[NarrativeSection(title="Finding", content="Content")],
        metadata={"provider": "mock", "timestamp": "2026-11-12T00:00:00Z"},
    )


@pytest.fixture()
def chart_csv(tmp_path: Path) -> Path:
    frame = pd.DataFrame(
        {
            "region": ["north", "south", "north", "west", "north", "south"],
            "revenue": [100.0, None, 120.0, 130.0, 140.0, 150.0],
        }
    )
    path = tmp_path / "chart.csv"
    frame.to_csv(path, index=False)
    return path


@pytest.mark.integration
def test_pipeline_attaches_all_four_chart_types_after_narrative(
    chart_csv: Path, tmp_path: Path
) -> None:
    config = VisualizationConfig(
        charts=[
            ChartSpec(chart_type=ChartType.MISSING_VALUES_BEFORE_AFTER),
            ChartSpec(chart_type=ChartType.DISTRIBUTION_BEFORE_AFTER, column="revenue"),
            ChartSpec(chart_type=ChartType.DISTRIBUTION, column="revenue"),
            ChartSpec(chart_type=ChartType.TOP_VALUES, column="region", limit=3),
        ]
    )

    with patch(
        "backend.pipeline.orchestrator.NarrativeGenerator.generate",
        return_value=_report(),
    ):
        result = run_full_pipeline(
            input_path=chart_csv,
            output_path=tmp_path / "report.docx",
            enable_cleaning=True,
            visualization_config=config,
        )

    assert result.success is True
    assert result.insight_report is not None
    assert [item.chart_type for item in result.insight_report.visualizations] == [
        ChartType.MISSING_VALUES_BEFORE_AFTER,
        ChartType.DISTRIBUTION_BEFORE_AFTER,
        ChartType.DISTRIBUTION,
        ChartType.TOP_VALUES,
    ]
    assert result.insight_report.charts_not_produced == []


@pytest.mark.integration
def test_chart_config_never_changes_llm_payload(
    chart_csv: Path, tmp_path: Path
) -> None:
    payloads: list[dict] = []

    def capture(payload, pipeline_run_id):
        payloads.append(
            _without_run_timestamps(
                payload.model_dump(mode="json", exclude={"drift_report"})
            )
        )
        return _report()

    with patch(
        "backend.pipeline.orchestrator.NarrativeGenerator.generate",
        side_effect=capture,
    ):
        run_full_pipeline(
            input_path=chart_csv,
            output_path=tmp_path / "plain.docx",
            visualization_config=VisualizationConfig(),
        )
        run_full_pipeline(
            input_path=chart_csv,
            output_path=tmp_path / "chart.docx",
            visualization_config=VisualizationConfig(
                charts=[ChartSpec(chart_type=ChartType.TOP_VALUES, column="region")]
            ),
        )

    assert len(payloads) == 2
    assert payloads[0] == payloads[1]
    assert "visualization" not in str(payloads[0]).lower()


@pytest.mark.integration
def test_before_after_chart_without_cleaning_is_reported_not_produced(
    chart_csv: Path, tmp_path: Path
) -> None:
    with patch(
        "backend.pipeline.orchestrator.NarrativeGenerator.generate",
        return_value=_report(),
    ):
        result = run_full_pipeline(
            input_path=chart_csv,
            output_path=tmp_path / "report.docx",
            enable_cleaning=False,
            visualization_config=VisualizationConfig(
                charts=[
                    ChartSpec(
                        chart_type=ChartType.DISTRIBUTION_BEFORE_AFTER,
                        column="revenue",
                    )
                ]
            ),
        )

    assert result.insight_report is not None
    assert result.insight_report.visualizations == []
    assert result.insight_report.charts_not_produced[0].reason == (
        NotProducedReason.CLEANING_NOT_ENABLED
    )


@pytest.mark.integration
def test_render_failure_degrades_one_chart_without_failing_pipeline(
    chart_csv: Path, tmp_path: Path
) -> None:
    with patch(
        "backend.pipeline.orchestrator.NarrativeGenerator.generate",
        return_value=_report(),
    ), patch(
        "backend.pipeline.orchestrator.render_chart_png",
        side_effect=RuntimeError("sensitive details must not surface"),
    ):
        result = run_full_pipeline(
            input_path=chart_csv,
            output_path=tmp_path / "report.docx",
            visualization_config=VisualizationConfig(
                charts=[ChartSpec(chart_type=ChartType.TOP_VALUES, column="region")]
            ),
        )

    assert result.success is True
    assert result.insight_report is not None
    assert result.insight_report.visualizations == []
    unavailable = result.insight_report.charts_not_produced[0]
    assert unavailable.reason == NotProducedReason.CHART_RENDER_FAILED
    assert "sensitive details" not in unavailable.reason_text


@pytest.mark.integration
def test_halted_run_never_builds_or_renders_charts(tmp_path: Path) -> None:
    with patch(
        "backend.pipeline.orchestrator.NarrativeGenerator.generate"
    ) as narrative, patch(
        "backend.pipeline.orchestrator.build_visualization_data"
    ) as builder:
        result = run_full_pipeline(
            input_path=_CRITICAL_CSV,
            output_path=tmp_path / "report.docx",
            visualization_config=VisualizationConfig(
                charts=[ChartSpec(chart_type=ChartType.TOP_VALUES, column="region")]
            ),
        )

    assert result.halted is True
    narrative.assert_not_called()
    builder.assert_not_called()
