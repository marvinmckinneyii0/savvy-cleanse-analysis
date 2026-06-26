"""End-to-end tests for the Pipeline Orchestration CLI (Story 1.6).

Tests run the full pipeline orchestrator against on-disk CSV fixtures.
The LLM narrative stage is patched so tests are deterministic and offline
(no API keys, no sleeps).  All other stages — DataQualityAssessor,
InsightEngine, DocxRenderer — run against real code.

Fixtures:
- ``sample_data/clean_sales.csv``     — 60-row clean dataset (happy path)
- ``sample_data/critical_quality_issues.csv``  — 60% null revenue → halt
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.errors.exceptions import ConfigurationError
from backend.models.insight_report import InsightReport, NarrativeSection
from backend.models.pipeline_result import PipelineResult
from backend.pipeline.orchestrator import OutputFormat, run_full_pipeline

_SAMPLE_DATA = Path(__file__).parent / "sample_data"
_CLEAN_CSV = _SAMPLE_DATA / "clean_sales.csv"
_CRITICAL_CSV = _SAMPLE_DATA / "critical_quality_issues.csv"


@pytest.fixture()
def canned_insight_report() -> InsightReport:
    """Pre-built InsightReport used to stub the NarrativeGenerator."""
    return InsightReport(
        executive_summary="Data quality is excellent. All 60 records are complete.",
        key_findings=[
            NarrativeSection(
                title="Revenue Completeness",
                content="100% of revenue values are present with no anomalies.",
            ),
        ],
        anomaly_analysis=None,
        recommendations_narrative="No corrective action required.",
        metadata={
            "provider": "mock",
            "model": "mock-model",
            "token_count": 0,
            "duration_ms": 0,
            "timestamp": "2026-06-26T00:00:00Z",
        },
        fallback=False,
    )


# ---------------------------------------------------------------------------
# Happy path — full pipeline, DOCX output
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_happy_path_docx(
    tmp_path: Path, canned_insight_report: InsightReport
) -> None:
    """Full pipeline completes successfully and produces a .docx file."""
    out = tmp_path / "report.docx"

    with patch(
        "backend.pipeline.orchestrator.NarrativeGenerator.generate",
        return_value=canned_insight_report,
    ):
        result = run_full_pipeline(
            input_path=_CLEAN_CSV,
            output_path=out,
            fmt=OutputFormat.docx,
        )

    assert result.success is True, "Expected success=True"
    assert result.halted is False
    assert result.quality_report is not None, "quality_report should be populated"
    assert result.insight_report is not None, "insight_report should be populated"
    assert out.exists(), "Output docx file was not created"
    assert out.stat().st_size > 0


@pytest.mark.integration
def test_happy_path_pdf(
    tmp_path: Path, canned_insight_report: InsightReport
) -> None:
    """Full pipeline with --format pdf writes a PDF stub when WeasyPrint mocked."""
    out = tmp_path / "report.pdf"

    def fake_write_pdf(path: str) -> None:
        Path(path).write_bytes(b"%PDF-1.4 stub")

    pdf_instance = MagicMock()
    pdf_instance.write_pdf = fake_write_pdf
    mock_wp = MagicMock()
    mock_wp.HTML = MagicMock(return_value=pdf_instance)

    with patch(
        "backend.pipeline.orchestrator.NarrativeGenerator.generate",
        return_value=canned_insight_report,
    ), patch.dict("sys.modules", {"weasyprint": mock_wp}):
        result = run_full_pipeline(
            input_path=_CLEAN_CSV,
            output_path=out,
            fmt=OutputFormat.pdf,
        )

    assert result.success is True
    assert out.exists()
    assert out.read_bytes().startswith(b"%PDF")


@pytest.mark.integration
def test_pipeline_run_id_propagated(
    tmp_path: Path, canned_insight_report: InsightReport
) -> None:
    """A caller-supplied pipeline_run_id is accepted and the run still succeeds."""
    out = tmp_path / "report.docx"
    run_id = "test-run-id-1234"

    with patch(
        "backend.pipeline.orchestrator.NarrativeGenerator.generate",
        return_value=canned_insight_report,
    ):
        result = run_full_pipeline(
            input_path=_CLEAN_CSV,
            output_path=out,
            fmt=OutputFormat.docx,
            pipeline_run_id=run_id,
        )

    assert result.success is True


# ---------------------------------------------------------------------------
# Halt path — critical data quality → pipeline stops early
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_halt_on_critical_dqa(tmp_path: Path) -> None:
    """Pipeline halts on >50% null revenue; subsequent stages are skipped."""
    out = tmp_path / "report.docx"

    with patch(
        "backend.pipeline.orchestrator.NarrativeGenerator.generate"
    ) as mock_narrative, patch(
        "backend.pipeline.orchestrator.DocxRenderer.render"
    ) as mock_render:
        result = run_full_pipeline(
            input_path=_CRITICAL_CSV,
            output_path=out,
            fmt=OutputFormat.docx,
        )

    assert result.halted is True, "Expected pipeline to halt on critical DQA"
    assert result.success is False
    assert result.halt_reason is not None
    # Downstream stages must not have been called
    mock_narrative.assert_not_called()
    mock_render.assert_not_called()
    # Output file must NOT exist
    assert not out.exists()


# ---------------------------------------------------------------------------
# Pre-flight error — missing input file
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_missing_input_raises_configuration_error(tmp_path: Path) -> None:
    out = tmp_path / "report.docx"
    with pytest.raises(ConfigurationError, match="not found"):
        run_full_pipeline(
            input_path=tmp_path / "nonexistent.csv",
            output_path=out,
        )


@pytest.mark.integration
def test_unparseable_csv_raises_configuration_error(tmp_path: Path) -> None:
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("not,valid\x00binary\xff\xfe")
    out = tmp_path / "report.docx"
    with pytest.raises(ConfigurationError):
        run_full_pipeline(input_path=bad_csv, output_path=out)


# ---------------------------------------------------------------------------
# Fallback narrative — pipeline still succeeds when LLM unavailable
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_fallback_narrative_still_produces_output(tmp_path: Path) -> None:
    """A fallback InsightReport (narrative=unavailable) still renders a report."""
    out = tmp_path / "report.docx"
    fallback_report = InsightReport(
        executive_summary="",
        key_findings=[],
        metadata={"provider": "none", "timestamp": "2026-06-26T00:00:00Z"},
        fallback=True,
        fallback_reason="All LLM providers exhausted.",
    )

    with patch(
        "backend.pipeline.orchestrator.NarrativeGenerator.generate",
        return_value=fallback_report,
    ):
        result = run_full_pipeline(
            input_path=_CLEAN_CSV,
            output_path=out,
            fmt=OutputFormat.docx,
        )

    assert result.success is True
    assert result.insight_report is not None
    assert result.insight_report.fallback is True
    assert out.exists()
