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
from backend.models.cleaning_result import (
    CleaningAction,
    CleaningOperation,
    CleaningResult,
    CleaningScope,
    CleaningStatus,
)
from backend.models.healing_manifest import REPORT_SEMANTICS_DISCLOSURE, build_healing_manifest
from backend.models.insight_report import InsightReport, NarrativeSection
from backend.models.quality_report import RemediationClass
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


@pytest.fixture()
def report_with_healing_manifest(full_report: InsightReport) -> InsightReport:
    """A COPY of `full_report` with a populated Story 3.3 healing_manifest
    attached. Deep-copies rather than mutating `full_report` in place —
    pytest resolves fixture dependencies before the test body runs, so
    mutating the shared `full_report` instance here would make ANY test that
    also requests the plain `full_report` fixture see the manifest attached
    too (fixtures are cached per test call, and both parameters would be the
    same object)."""
    report = full_report.model_copy(deep=True)
    action = CleaningAction(
        operation=CleaningOperation.CASE_NORMALIZATION,
        defect_type="case_inconsistency",
        remediation_class=RemediationClass.AGENT_AUTONOMOUS,
        status=CleaningStatus.APPLIED,
        scope=CleaningScope.COLUMN,
        target_columns=["region"],
        values_changed=3,
        detail="Normalized casing in 'region': 3 value(s) rewritten across 3 variant(s).",
    )
    result = CleaningResult(
        pipeline_run_id="run-renderer-test",
        total_findings=1,
        autonomous_findings=1,
        actions=[action],
        rows_before=12,
        rows_after=12,
        columns_before=4,
        columns_after=4,
        cleaned_at="2026-01-01T00:00:00+00:00",
    )
    report.healing_manifest = build_healing_manifest(result)
    return report


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

    def test_healing_manifest_absent_by_default(
        self, full_report: InsightReport, tmp_path: Path
    ) -> None:
        """Story 3.3 AC5: cleaning off/absent -> no manifest section rendered."""
        out = tmp_path / "report.docx"
        DocxRenderer().render(full_report, out)

        with zipfile.ZipFile(out) as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")

        assert "Data Cleaning" not in doc_xml

    def test_healing_manifest_section_renders_when_present(
        self, report_with_healing_manifest: InsightReport, tmp_path: Path
    ) -> None:
        out = tmp_path / "report.docx"
        DocxRenderer().render(report_with_healing_manifest, out)

        with zipfile.ZipFile(out) as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")

        assert "Data Cleaning" in doc_xml
        assert "Normalized casing in" in doc_xml
        assert "working copy" in doc_xml  # part of REPORT_SEMANTICS_DISCLOSURE

    def test_healing_manifest_entry_shows_operation_and_target_columns(
        self, report_with_healing_manifest: InsightReport, tmp_path: Path
    ) -> None:
        """Story 3.3 AC6: every rendered entry must show operation and target
        columns, not just outcome and detail."""
        out = tmp_path / "report.docx"
        DocxRenderer().render(report_with_healing_manifest, out)

        with zipfile.ZipFile(out) as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")

        assert "case_normalization" in doc_xml
        assert "region" in doc_xml

    def test_narrative_content_unchanged_by_healing_manifest_presence(
        self,
        full_report: InsightReport,
        report_with_healing_manifest: InsightReport,
        tmp_path: Path,
    ) -> None:
        """Story 3.3 AC9: narrative sections must not differ based on whether
        cleaning ran — only the manifest section's presence should differ."""
        out_without = tmp_path / "without.docx"
        out_with = tmp_path / "with.docx"
        DocxRenderer().render(full_report, out_without)
        DocxRenderer().render(report_with_healing_manifest, out_with)

        with zipfile.ZipFile(out_without) as zf:
            xml_without = zf.read("word/document.xml").decode("utf-8")
        with zipfile.ZipFile(out_with) as zf:
            xml_with = zf.read("word/document.xml").decode("utf-8")

        assert "Overall data quality is high" in xml_without
        assert "Overall data quality is high" in xml_with
        assert "Revenue Completeness" in xml_without
        assert "Revenue Completeness" in xml_with

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

    def test_healing_manifest_absent_by_default(
        self, full_report: InsightReport, tmp_path: Path
    ) -> None:
        """Story 3.3 AC5: cleaning off/absent -> no manifest section rendered."""
        out = tmp_path / "report.pdf"
        captured: list[str] = []
        mock_wp = _make_weasyprint_mock(captured)

        with patch.dict("sys.modules", {"weasyprint": mock_wp}):
            PdfRenderer().render(full_report, out)

        html_string = mock_wp.HTML.call_args.kwargs["string"]
        assert "Data Cleaning" not in html_string

    def test_healing_manifest_section_renders_when_present(
        self, report_with_healing_manifest: InsightReport, tmp_path: Path
    ) -> None:
        out = tmp_path / "report.pdf"
        captured: list[str] = []
        mock_wp = _make_weasyprint_mock(captured)

        with patch.dict("sys.modules", {"weasyprint": mock_wp}):
            PdfRenderer().render(report_with_healing_manifest, out)

        html_string = mock_wp.HTML.call_args.kwargs["string"]
        assert "Data Cleaning" in html_string
        assert "Normalized casing in" in html_string
        assert REPORT_SEMANTICS_DISCLOSURE in html_string

    def test_healing_manifest_entry_shows_operation_and_target_columns(
        self, report_with_healing_manifest: InsightReport, tmp_path: Path
    ) -> None:
        """Story 3.3 AC6: every rendered entry must show operation and target
        columns, not just outcome and detail."""
        out = tmp_path / "report.pdf"
        captured: list[str] = []
        mock_wp = _make_weasyprint_mock(captured)

        with patch.dict("sys.modules", {"weasyprint": mock_wp}):
            PdfRenderer().render(report_with_healing_manifest, out)

        html_string = mock_wp.HTML.call_args.kwargs["string"]
        assert "case_normalization" in html_string
        assert "region" in html_string

    def test_narrative_content_unchanged_by_healing_manifest_presence(
        self,
        full_report: InsightReport,
        report_with_healing_manifest: InsightReport,
        tmp_path: Path,
    ) -> None:
        """Story 3.3 AC9: narrative sections must not differ based on whether
        cleaning ran — only the manifest section's presence should differ."""
        captured: list[str] = []
        mock_wp_without = _make_weasyprint_mock(captured)
        mock_wp_with = _make_weasyprint_mock(captured)

        with patch.dict("sys.modules", {"weasyprint": mock_wp_without}):
            PdfRenderer().render(full_report, tmp_path / "without.pdf")
        with patch.dict("sys.modules", {"weasyprint": mock_wp_with}):
            PdfRenderer().render(report_with_healing_manifest, tmp_path / "with.pdf")

        html_without = mock_wp_without.HTML.call_args.kwargs["string"]
        html_with = mock_wp_with.HTML.call_args.kwargs["string"]
        assert "Overall data quality is high" in html_without
        assert "Overall data quality is high" in html_with
        assert "Revenue Completeness" in html_without
        assert "Revenue Completeness" in html_with

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
