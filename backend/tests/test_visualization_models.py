"""Story 3.7 visualization model/config tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.errors.exceptions import ConfigurationError
from backend.models.insight_report import InsightReport
from backend.models.pipeline_config import PipelineConfig
from backend.models.visualization import (
    AnalysisClass,
    ChartSpec,
    ChartType,
    Visualization,
    VisualizationConfig,
)


def test_insight_report_visualizations_default_empty() -> None:
    report = InsightReport(executive_summary="", key_findings=[])
    assert report.visualizations == []
    assert report.charts_not_produced == []


def test_analysis_class_is_required_on_visualization() -> None:
    with pytest.raises(ValidationError):
        Visualization.model_validate(
            {
                "chart_type": "distribution",
                "title": "Distribution",
                "caption": "caption",
                "image_base64": "abc",
                "data": {
                    "chart_type": "distribution",
                    "analysis_class": "descriptive",
                    "title": "Distribution",
                    "caption": "caption",
                },
            }
        )


def test_analysis_class_closed_allowlist() -> None:
    assert {item.value for item in AnalysisClass} == {
        "descriptive",
        "diagnostic_basic",
        "diagnostic_advanced",
        "predictive",
        "prescriptive",
        "decision_trace",
    }


def test_chart_spec_shapes_and_limits() -> None:
    top = ChartSpec(chart_type=ChartType.TOP_VALUES, column="region")
    assert top.limit == 10

    with pytest.raises(ValidationError):
        ChartSpec(chart_type=ChartType.TOP_VALUES, column="region", limit=21)
    with pytest.raises(ValidationError):
        ChartSpec(chart_type=ChartType.DISTRIBUTION)
    with pytest.raises(ValidationError):
        ChartSpec(chart_type=ChartType.DISTRIBUTION, column="revenue", limit=3)
    with pytest.raises(ValidationError):
        ChartSpec(
            chart_type=ChartType.MISSING_VALUES_BEFORE_AFTER,
            columns=[f"c{i}" for i in range(31)],
        )


def test_visualization_config_rejects_duplicates_and_more_than_twelve() -> None:
    spec = {"chart_type": "distribution", "column": "revenue"}
    with pytest.raises(ValidationError):
        VisualizationConfig(charts=[spec, spec])
    with pytest.raises(ValidationError):
        VisualizationConfig(
            charts=[
                {"chart_type": "distribution", "column": f"metric_{i}"}
                for i in range(13)
            ]
        )


def test_pipeline_config_without_visualizations_is_backward_compatible(
    tmp_path: Path,
) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        """
data_sources:
  - data/sales.csv
report_schedule:
  interval: weekly
""",
        encoding="utf-8",
    )
    config = PipelineConfig.load(path)
    assert config.visualizations.charts == []


@pytest.mark.parametrize(
    "visualizations",
    [
        "charts:\n    - chart_type: not_a_chart",
        "charts:\n    - chart_type: distribution",
        "charts:\n    - chart_type: distribution\n      column: revenue\n      limit: 4",
        "charts:\n    - chart_type: top_values\n      column: region\n      limit: 0",
    ],
)
def test_invalid_visualization_config_fails_closed(
    tmp_path: Path, visualizations: str
) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        f"""
data_sources:
  - data/sales.csv
report_schedule:
  interval: weekly
visualizations:
  {visualizations}
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigurationError, match="visualizations"):
        PipelineConfig.load(path)
