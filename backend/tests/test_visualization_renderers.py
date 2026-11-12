"""Story 3.7 report renderer integration tests."""

from __future__ import annotations

import base64
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from backend.models.insight_report import InsightReport
from backend.models.visualization import (
    AnalysisClass,
    ChartData,
    ChartSeries,
    ChartType,
    NotProducedChart,
    NotProducedReason,
    Visualization,
)
from backend.renderers.chart_images import render_chart_png
from backend.renderers.docx_renderer import DocxRenderer
from backend.renderers.pdf_renderer import PdfRenderer


def _report_with_chart() -> InsightReport:
    data = ChartData(
        chart_type=ChartType.TOP_VALUES,
        analysis_class=AnalysisClass.DESCRIPTIVE,
        title="Top Values — region",
        caption="Most frequent values in the original data; top 3 shown.",
        labels=["North", "South", "West"],
        series=[ChartSeries(label="Original data", values=[4, 3, 2])],
    )
    png = render_chart_png(data)
    return InsightReport(
        executive_summary="Summary",
        key_findings=[],
        visualizations=[
            Visualization(
                chart_type=data.chart_type,
                analysis_class=data.analysis_class,
                title=data.title,
                caption=data.caption,
                image_base64=base64.b64encode(png).decode("ascii"),
                data=data,
            )
        ],
        charts_not_produced=[
            NotProducedChart(
                chart_type=ChartType.DISTRIBUTION_BEFORE_AFTER,
                title="Distribution — revenue — Original vs Cleaned Working Copy",
                reason=NotProducedReason.CLEANING_NOT_ENABLED,
            )
        ],
    )


def _mock_weasyprint() -> MagicMock:
    def fake_write_pdf(path: str) -> None:
        Path(path).write_bytes(b"%PDF-1.4 stub")

    instance = MagicMock()
    instance.write_pdf = fake_write_pdf
    module = MagicMock()
    module.HTML = MagicMock(return_value=instance)
    return module


def test_docx_contains_charts_image_caption_and_unavailable_reason(tmp_path: Path) -> None:
    out = tmp_path / "charts.docx"
    DocxRenderer().render(_report_with_chart(), out)

    with zipfile.ZipFile(out) as zf:
        document_xml = zf.read("word/document.xml").decode("utf-8")
        media = [name for name in zf.namelist() if name.startswith("word/media/")]

    assert "Charts" in document_xml
    assert "Top Values" in document_xml
    assert "Most frequent values" in document_xml
    assert "cleaning was not enabled for this run" in document_xml
    assert media


def test_pdf_contains_data_uri_caption_and_unavailable_reason(tmp_path: Path) -> None:
    out = tmp_path / "charts.pdf"
    mock_wp = _mock_weasyprint()

    with patch.dict("sys.modules", {"weasyprint": mock_wp}):
        PdfRenderer().render(_report_with_chart(), out)

    html = mock_wp.HTML.call_args.kwargs["string"]
    assert "<h2>Charts</h2>" in html
    assert "data:image/png;base64," in html
    assert "Most frequent values" in html
    assert "cleaning was not enabled for this run" in html


def test_zero_chart_report_has_no_charts_section(tmp_path: Path) -> None:
    report = InsightReport(executive_summary="Summary", key_findings=[])
    out = tmp_path / "plain.pdf"
    mock_wp = _mock_weasyprint()

    with patch.dict("sys.modules", {"weasyprint": mock_wp}):
        PdfRenderer().render(report, out)

    html = mock_wp.HTML.call_args.kwargs["string"]
    assert "<h2>Charts</h2>" not in html
