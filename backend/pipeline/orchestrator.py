"""Pipeline Orchestrator — Stage composer and CLI entry point.

Wires the four Phase-1 pipeline stages into a single callable:

    CSV → DataQualityAssessor → InsightEngine → NarrativeGenerator → Renderer

The orchestrator owns:
- ``pipeline_run_id`` generation and structlog context binding
- Stage sequencing and halt-on-critical short-circuit
- Error boundary: ``SavvyCleanseError`` is caught here (CLI boundary only)
- Typer CLI surface for ``python -m backend.pipeline.orchestrator``

Architecture compliance (architecture.md §482-506, §745):
- Lives in ``backend/pipeline/`` (Business Logic layer).
- May import from ``models/``, ``renderers/``, and sibling pipeline stages.
- Must NOT import from ``api/`` or legacy modules.
- Never self-configures logging at import time.
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Annotated

import pandas as pd
import structlog
import typer

from backend.errors.exceptions import ConfigurationError, SavvyCleanseError
from backend.models.pipeline_result import PipelineResult
from backend.pipeline.config import bind_pipeline_run_id, configure_logging
from backend.pipeline.data_quality import DataQualityAssessor
from backend.pipeline.insight_engine import InsightEngine
from backend.pipeline.narrative_generator import NarrativeGenerator
from backend.renderers import DocxRenderer, PdfRenderer


class OutputFormat(str, Enum):
    docx = "docx"
    pdf = "pdf"


def run_full_pipeline(
    input_path: str | Path,
    output_path: str | Path,
    fmt: OutputFormat = OutputFormat.docx,
    pipeline_run_id: str | None = None,
) -> PipelineResult:
    """Run the complete DQA → Insights → Narrative → Render pipeline.

    Parameters
    ----------
    input_path:
        Path to the input CSV file.
    output_path:
        Destination path for the rendered report.
    fmt:
        Output format — ``"docx"`` (default) or ``"pdf"``.
    pipeline_run_id:
        Optional pre-generated run ID; one is created if not supplied.

    Returns
    -------
    PipelineResult
        The run envelope. ``success=True`` on full completion;
        ``halted=True`` if critical data-quality findings stopped the run.

    Raises
    ------
    ConfigurationError
        If the input file is missing or cannot be parsed as CSV
        (pre-flight failure — no stages have run).
    ReportRenderError
        If the renderer fails to write the output document.
    """
    log = structlog.get_logger()
    input_path = Path(input_path)
    output_path = Path(output_path)

    if pipeline_run_id is None:
        pipeline_run_id = str(uuid.uuid4())

    bind_pipeline_run_id(pipeline_run_id)
    t0 = time.perf_counter()

    log.info("pipeline_started", input=str(input_path), format=fmt.value)

    # --- Pre-flight: load CSV ---
    if not input_path.exists():
        raise ConfigurationError(f"Input file not found: {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as exc:
        raise ConfigurationError(
            f"Cannot parse CSV '{input_path}': {type(exc).__name__}: {exc}"
        ) from exc

    # --- Stage 1: Data Quality Assessment ---
    result: PipelineResult = DataQualityAssessor().assess_quality(df, pipeline_run_id)

    if result.halted:
        duration = time.perf_counter() - t0
        log.warning(
            "pipeline_halted",
            halt_reason=result.halt_reason,
            duration_s=round(duration, 3),
        )
        return result

    # --- Stage 2: Insight Engine ---
    payload = InsightEngine().generate_insights(
        df, result.quality_report, pipeline_run_id
    )

    # --- Stage 3: Narrative Generator ---
    insight_report = NarrativeGenerator().generate(payload, pipeline_run_id)
    result.insight_report = insight_report

    # --- Stage 4: Render ---
    if fmt == OutputFormat.docx:
        DocxRenderer().render(insight_report, output_path)
    else:
        PdfRenderer().render(insight_report, output_path)

    result.success = True
    duration = time.perf_counter() - t0
    log.info(
        "pipeline_completed",
        status="success",
        output=str(output_path),
        duration_s=round(duration, 3),
        fallback_narrative=insight_report.fallback,
    )
    return result


# ---------------------------------------------------------------------------
# Typer CLI
# ---------------------------------------------------------------------------

app = typer.Typer(add_completion=False)


@app.command()
def cli(
    input: Annotated[
        Path,
        typer.Option("--input", help="Path to input CSV file.", exists=True),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", help="Destination path for the rendered report."),
    ],
    format: Annotated[
        OutputFormat,
        typer.Option("--format", help="Output format: docx or pdf."),
    ] = OutputFormat.docx,
) -> None:
    """Run the SavvyCortex full analysis pipeline on a CSV file."""
    configure_logging()
    pipeline_run_id = str(uuid.uuid4())

    try:
        result = run_full_pipeline(
            input_path=input,
            output_path=output,
            fmt=format,
            pipeline_run_id=pipeline_run_id,
        )
    except SavvyCleanseError as exc:
        structlog.get_logger().error(
            "pipeline_error", error=type(exc).__name__, detail=str(exc)
        )
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if result.halted:
        typer.echo(
            f"Pipeline halted | run_id={pipeline_run_id} | reason={result.halt_reason}",
            err=True,
        )
        raise typer.Exit(code=1)

    typer.echo(
        f"Pipeline complete | run_id={pipeline_run_id}"
        f" | status=success"
        f" | output={output}"
    )


if __name__ == "__main__":
    app()
