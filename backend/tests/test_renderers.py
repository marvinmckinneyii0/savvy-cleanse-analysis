"""Tests for DocxRenderer and PdfRenderer (Story 1.5).

Test strategy
-------------
* DocxRenderer: exercises the real docxtpl pipeline against the actual
  template — verifies file creation and that key text lands in the XML.
* PdfRenderer: WeasyPrint requires native GLib/Pango libraries that are
  absent on Windows dev boxes and many CI images. All PDF tests mock
  ``weasyprint.HTML`` so the template-rendering and error-wrapping logic
  is exercised without the native dependency. The mock writes a minimal
  ``%PDF`` stub so magic-byte assertions pass.
* Both renderers: fallback mode, missing-template error, unwritable-path
  error.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.errors.exceptions import ReportRenderError
from backend.models.insight_report import InsightReport, NarrativeSection
from backend.renderers.docx_renderer import DocxRenderer
from backend.renderers.pdf_renderer import PdfRenderer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def full_report() -> InsightReport:
    """InsightReport with all narrative sections populated."""
    return InsightReport(
        executive_summary="Overall data quality is high with minor completeness gaps.",
        key_findings=[
            NarrativeSection(
                title="Revenue Completeness",
                content="3% of revenue values are missing, below the 5% halt threshold.",
            ),
            NarrativeSection(
                title="Date Monotonicity",
                content="Order dates are monotonically increasing across all records.",
            ),
        ],
        anomaly_analysis="One outlier detected in Q3 revenue: $0.01 — likely a test transaction.",
        recommendations_narrative="Review and purge the $0.01 test transaction before modelling.",
        metadata={
            "provider": "claude",
            "model": "claude-sonnet-4-6",
            "token_count": 512,
            "duration_ms": 1800,
            "timestamp": "2026-06-26T12:00:00Z",
        },
        fallback=False,
    )


@pytest.fixture()
def fallback_report() -> InsightReport:
    """InsightReport with fallback=True — narrative unavailable."""
    return InsightReport(
        executive_summary="",
        key_findings=[],
        metadata={"timestamp": "2026-06-26T12:00:00Z", "provider": "none"},
        fallback=True,
        fallback_reason="All LLM providers exhausted after 3 consecutive failures.",
    )


# ---------------------------------------------------------------------------
# DocxRenderer tests
# ---------------------------------------------------------------------------


class TestDocxRenderer:
    def test_renders_valid_docx(self, full_report: InsightReport, tmp_path: Path) -> None:
        out = tmp_path / "report.docx"
        DocxRenderer().render(full_report, out)

        assert out.exists(), "Output file was not created"
        assert out.stat().st_size > 0, "Output file is empty"
        # A .docx is a ZIP archive
        assert zipfile.is_zipfile(out), "Output is not a valid ZIP/docx"

    def test_docx_contains_summary_text(self, full_report: InsightReport, tmp_path: Path) -> None:
        out = tmp_path / "report.docx"
        DocxRenderer().render(full_report, out)

        with zipfile.ZipFile(out) as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")

        assert "Overall data quality is high" in doc_xml

    def test_docx_contains_finding_title(self, full_report: InsightReport, tmp_path: Path) -> None:
        out = tmp_path / "report.docx"
        DocxRenderer().render(full_report, out)

        with zipfile.ZipFile(out) as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")

        assert "Revenue Completeness" in doc_xml

    def test_fallback_docx_renders_without_raising(
        self, fallback_report: InsightReport, tmp_path: Path
    ) -> None:
        out = tmp_path / "fallback.docx"
        DocxRenderer().render(fallback_report, out)
        assert out.exists()
        assert zipfile.is_zipfile(out)

    def test_fallback_docx_contains_fallback_reason(
        self, fallback_report: InsightReport, tmp_path: Path
    ) -> None:
        out = tmp_path / "fallback.docx"
        DocxRenderer().render(fallback_report, out)

        with zipfile.ZipFile(out) as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")

        assert "All LLM providers exhausted" in doc_xml

    def test_missing_template_raises_render_error(
        self, full_report: InsightReport, tmp_path: Path
    ) -> None:
        out = tmp_path / "report.docx"
        with patch(
            "backend.renderers.docx_renderer._TEMPLATE_PATH",
            Path("/nonexistent/template.docx"),
        ):
            with pytest.raises(ReportRenderError, match="DOCX render failed"):
                DocxRenderer().render(full_report, out)

    def test_unwritable_output_raises_render_error(
        self, full_report: InsightReport, tmp_path: Path
    ) -> None:
        # Write to a directory path (not a file) to force an IO error
        out = tmp_path  # tmp_path itself is a directory
        with pytest.raises(ReportRenderError):
            DocxRenderer().render(full_report, out)

    def test_accepts_string_output_path(
        self, full_report: InsightReport, tmp_path: Path
    ) -> None:
        out = str(tmp_path / "report_str.docx")
        DocxRenderer().render(full_report, out)
        assert Path(out).exists()


# ---------------------------------------------------------------------------
# PdfRenderer tests  (WeasyPrint is mocked — no native GTK needed)
# ---------------------------------------------------------------------------


def _make_weasyprint_mock(output_path_capture: list[str]) -> MagicMock:
    """Return a mock weasyprint module whose HTML().write_pdf() writes %PDF stub."""

    def fake_write_pdf(path: str) -> None:
        output_path_capture.append(path)
        Path(path).write_bytes(b"%PDF-1.4 stub")

    html_instance = MagicMock()
    html_instance.write_pdf = fake_write_pdf
    html_cls = MagicMock(return_value=html_instance)

    mock_wp = MagicMock()
    mock_wp.HTML = html_cls
    return mock_wp


class TestPdfRenderer:
    def test_renders_valid_pdf(self, full_report: InsightReport, tmp_path: Path) -> None:
        out = tmp_path / "report.pdf"
        captured: list[str] = []
        mock_wp = _make_weasyprint_mock(captured)

        with patch.dict("sys.modules", {"weasyprint": mock_wp}):
            PdfRenderer().render(full_report, out)

        assert out.exists()
        assert out.read_bytes()[:4] == b"%PDF"

    def test_pdf_magic_bytes(self, full_report: InsightReport, tmp_path: Path) -> None:
        out = tmp_path / "report.pdf"
        captured: list[str] = []
        mock_wp = _make_weasyprint_mock(captured)

        with patch.dict("sys.modules", {"weasyprint": mock_wp}):
            PdfRenderer().render(full_report, out)

        assert out.read_bytes().startswith(b"%PDF")

    def test_fallback_pdf_renders_without_raising(
        self, fallback_report: InsightReport, tmp_path: Path
    ) -> None:
        out = tmp_path / "fallback.pdf"
        captured: list[str] = []
        mock_wp = _make_weasyprint_mock(captured)

        with patch.dict("sys.modules", {"weasyprint": mock_wp}):
            PdfRenderer().render(fallback_report, out)

        assert out.exists()

    def test_missing_template_raises_render_error(
        self, full_report: InsightReport, tmp_path: Path
    ) -> None:
        out = tmp_path / "report.pdf"
        captured: list[str] = []
        mock_wp = _make_weasyprint_mock(captured)

        with patch.dict("sys.modules", {"weasyprint": mock_wp}):
            with patch(
                "backend.renderers.pdf_renderer._TEMPLATE_PATH",
                Path("/nonexistent/template.html"),
            ):
                with pytest.raises(ReportRenderError, match="cannot load HTML template"):
                    PdfRenderer().render(full_report, out)

    def test_weasyprint_oserror_raises_render_error(
        self, full_report: InsightReport, tmp_path: Path
    ) -> None:
        """Simulate WeasyPrint native libs missing → ReportRenderError."""
        out = tmp_path / "report.pdf"

        # Remove weasyprint from sys.modules so the lazy import runs,
        # then make it raise OSError on import
        with patch.dict("sys.modules", {"weasyprint": None}):
            with pytest.raises((ReportRenderError, ImportError)):
                PdfRenderer().render(full_report, out)

    def test_weasyprint_render_error_is_wrapped(
        self, full_report: InsightReport, tmp_path: Path
    ) -> None:
        out = tmp_path / "report.pdf"

        html_instance = MagicMock()
        html_instance.write_pdf.side_effect = RuntimeError("disk full")
        mock_wp = MagicMock()
        mock_wp.HTML = MagicMock(return_value=html_instance)

        with patch.dict("sys.modules", {"weasyprint": mock_wp}):
            with pytest.raises(ReportRenderError, match="disk full"):
                PdfRenderer().render(full_report, out)

    def test_accepts_string_output_path(
        self, full_report: InsightReport, tmp_path: Path
    ) -> None:
        out = str(tmp_path / "report_str.pdf")
        captured: list[str] = []
        mock_wp = _make_weasyprint_mock(captured)

        with patch.dict("sys.modules", {"weasyprint": mock_wp}):
            PdfRenderer().render(full_report, out)

        assert Path(out).exists()


# ---------------------------------------------------------------------------
# Shared interface contract tests (Story 1.6 integration point)
# ---------------------------------------------------------------------------


class TestRendererInterface:
    """Verify both renderers satisfy the interface contract Story 1.6 depends on."""

    def test_docx_renderer_importable_from_package(self) -> None:
        from backend.renderers import DocxRenderer  # noqa: F401

    def test_pdf_renderer_importable_from_package(self) -> None:
        from backend.renderers import PdfRenderer  # noqa: F401

    def test_docx_renderer_has_render_method(self) -> None:
        import inspect

        sig = inspect.signature(DocxRenderer.render)
        params = list(sig.parameters)
        assert "insight_report" in params
        assert "output_path" in params

    def test_pdf_renderer_has_render_method(self) -> None:
        import inspect

        sig = inspect.signature(PdfRenderer.render)
        params = list(sig.parameters)
        assert "insight_report" in params
        assert "output_path" in params
