"""DOCX renderer — produces a branded .docx report from an InsightReport.

Uses docxtpl (Jinja2 over python-docx) to populate
``backend/renderers/templates/report_template.docx``.

Raises :class:`backend.errors.exceptions.ReportRenderError` on any
template, IO, or rendering failure — never bare Exception.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import structlog
from docxtpl import DocxTemplate

from backend.errors.exceptions import ReportRenderError
from backend.models.insight_report import InsightReport

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "report_template.docx"


class DocxRenderer:
    """Render an :class:`InsightReport` to a ``.docx`` file."""

    def render(self, insight_report: InsightReport, output_path: str | Path) -> None:
        """Populate the branded DOCX template and write to *output_path*.

        Parameters
        ----------
        insight_report:
            The report produced by the NarrativeGenerator (Story 1.4).
            Handles ``fallback=True`` gracefully — renders a data-only
            report with a fallback notice instead of narrative sections.
        output_path:
            Destination file path (``str`` or :class:`~pathlib.Path`).
            Parent directory must exist; the file is created or overwritten.

        Raises
        ------
        ReportRenderError
            If the template is missing, the output path is unwritable, or
            docxtpl encounters any rendering error.
        """
        log = structlog.get_logger()
        output_path = Path(output_path)
        t0 = time.monotonic()

        try:
            doc = DocxTemplate(_TEMPLATE_PATH)
        except Exception as exc:
            raise ReportRenderError(
                f"DOCX render failed — cannot load template '{_TEMPLATE_PATH}': "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        context: dict[str, Any] = {
            "executive_summary": insight_report.executive_summary or "",
            "key_findings": insight_report.key_findings,
            "anomaly_analysis": insight_report.anomaly_analysis,
            "recommendations_narrative": insight_report.recommendations_narrative,
            "metadata": insight_report.metadata,
            "fallback": insight_report.fallback,
            "fallback_reason": insight_report.fallback_reason or "",
        }

        try:
            doc.render(context)
            doc.save(output_path)
        except Exception as exc:
            raise ReportRenderError(
                f"DOCX render failed — {type(exc).__name__}: {exc}"
            ) from exc

        duration_ms = int((time.monotonic() - t0) * 1000)
        log.info(
            "report_rendered",
            stage="renderer",
            format="docx",
            output_path=str(output_path),
            duration_ms=duration_ms,
            fallback=insight_report.fallback,
        )
