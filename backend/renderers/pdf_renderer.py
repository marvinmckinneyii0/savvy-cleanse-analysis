"""PDF renderer — produces a branded .pdf report from an InsightReport.

Uses Jinja2 to render ``backend/renderers/templates/report_template.html``
to an HTML string, then passes it to WeasyPrint to produce a PDF.

WeasyPrint system dependency note
----------------------------------
WeasyPrint 68.1+ requires native GLib/Pango libraries:
  - Linux/macOS: typically satisfied by system packages (libpango-1.0, libgobject-2.0)
  - Windows: requires GTK for Windows runtime (https://gtk.org/docs/installations/windows/)
  - CI/CD: add ``apt-get install -y libpango-1.0-0`` (Debian/Ubuntu) or equivalent

Raises :class:`backend.errors.exceptions.ReportRenderError` on any
template, WeasyPrint, or IO failure — including missing native libraries.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import structlog

from backend.errors.exceptions import ReportRenderError
from backend.models.insight_report import InsightReport

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "report_template.html"


class PdfRenderer:
    """Render an :class:`InsightReport` to a ``.pdf`` file."""

    def render(self, insight_report: InsightReport, output_path: str | Path) -> None:
        """Render the branded HTML template to PDF and write to *output_path*.

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
            If the HTML template is missing, WeasyPrint native libraries are
            unavailable, the output path is unwritable, or any other
            rendering error occurs.
        """
        log = structlog.get_logger()
        output_path = Path(output_path)
        t0 = time.monotonic()

        # Lazy import: WeasyPrint raises OSError on import if native GLib/Pango
        # libraries are absent. Convert to ReportRenderError so the caller
        # always sees a typed exception with a helpful message.
        try:
            import weasyprint  # noqa: PLC0415
        except OSError as exc:
            raise ReportRenderError(
                "PDF render failed — WeasyPrint native libraries not found. "
                "Install GTK runtime (Windows) or libpango/libgobject (Linux/macOS). "
                f"Details: {exc}"
            ) from exc

        try:
            from jinja2 import Environment, FileSystemLoader  # noqa: PLC0415

            env = Environment(
                loader=FileSystemLoader(str(_TEMPLATE_PATH.parent)),
                autoescape=True,
            )
            template = env.get_template(_TEMPLATE_PATH.name)
        except Exception as exc:
            raise ReportRenderError(
                f"PDF render failed — cannot load HTML template '{_TEMPLATE_PATH}': "
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
            "drift_report": insight_report.drift_report,
        }

        try:
            html_string = template.render(**context)
            weasyprint.HTML(string=html_string).write_pdf(str(output_path))
        except ReportRenderError:
            raise
        except Exception as exc:
            raise ReportRenderError(
                f"PDF render failed — {type(exc).__name__}: {exc}"
            ) from exc

        duration_ms = int((time.monotonic() - t0) * 1000)
        log.info(
            "report_rendered",
            stage="renderer",
            format="pdf",
            output_path=str(output_path),
            duration_ms=duration_ms,
            fallback=insight_report.fallback,
        )
