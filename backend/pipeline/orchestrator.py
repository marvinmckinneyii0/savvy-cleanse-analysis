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
from typing import TYPE_CHECKING, Annotated

import pandas as pd
import structlog
import typer

from backend.core.logging import bind_pipeline_run_id, configure_logging
from backend.errors.exceptions import ConfigurationError, SavvyCleanseError
from backend.models.pipeline_result import PipelineResult
from backend.pipeline.data_quality import DataQualityAssessor
from backend.pipeline.drift_engine import DriftEngine
from backend.pipeline.insight_engine import InsightEngine
from backend.pipeline.narrative_generator import NarrativeGenerator
from backend.renderers import DocxRenderer, PdfRenderer

if TYPE_CHECKING:
    from backend.models.pipeline_config import CleaningConfig


class OutputFormat(str, Enum):
    docx = "docx"
    pdf = "pdf"


def run_full_pipeline(
    input_path: str | Path,
    output_path: str | Path,
    fmt: OutputFormat = OutputFormat.docx,
    pipeline_run_id: str | None = None,
    dataset_key: str | None = None,
    enable_drift: bool = True,
    baseline_dir: str | Path = "backend/baselines",
    enable_cleaning: bool = False,
    cleaning_config: "CleaningConfig | None" = None,
) -> PipelineResult:
    """Run the complete DQA → Drift → Insights → Narrative → Render pipeline.

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
    dataset_key:
        Opaque per-dataset key for baseline storage. When ``None`` the drift
        stage is skipped (the orchestrator's own CLI does not supply one — the
        Reporting Agent does). Architecture.md §754-764.
    enable_drift:
        When ``True`` (default) and ``dataset_key`` is set, the Drift Engine
        runs after DQA and feeds the Insight Engine.
    baseline_dir:
        Directory holding baseline JSON files (default ``backend/baselines``).
    enable_cleaning:
        Opt-in cleaning gate (Story 3.4) — **default OFF, load-bearing**. When
        ``False`` no cleaning component is constructed, ``cleaning_result`` stays
        ``None``, and output is byte-identical to the pre-3.4 pipeline. When
        ``True`` and the run did not halt, the Tier-1 engine + Tier-2 imputation
        policy run on a working copy after DQA; the report still describes the
        ORIGINAL frame (see Story 3.4 Q1).
    cleaning_config:
        Cleaning configuration supplying the Tier-2 imputation policy. Used only
        when ``enable_cleaning`` is ``True``; when ``None`` the built-in per-type
        defaults apply (a non-expert is never blocked). Its ``enabled`` flag is
        NOT consulted here — enablement is the ``enable_cleaning`` parameter's
        job, so callers must not double-gate.

    Returns
    -------
    PipelineResult
        The run envelope. ``success=True`` on full completion;
        ``halted=True`` if critical data-quality findings stopped the run.
        ``drift_report`` is populated when drift ran and a baseline existed
        (``None`` on first run / when drift was skipped).

    Raises
    ------
    ConfigurationError
        If the input file is missing or cannot be parsed as CSV
        (pre-flight failure — no stages have run).
    DriftComputationError
        If the drift stage hits a corrupt baseline or degenerate statistic.
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
        if enable_cleaning:
            # Cleaning was opted into but the run stopped at DQA — never run it
            # on data a halt flagged as untrustworthy.
            log.info("cleaning_stage_skipped", reason="pipeline_halted")
        duration = time.perf_counter() - t0
        log.warning(
            "pipeline_halted",
            halt_reason=result.halt_reason,
            duration_s=round(duration, 3),
        )
        return result

    # --- Stage 1b: Cleaning (Story 3.4, opt-in / default-off; gated) ---
    # Runs on a working copy and is carried on the result; the report stages
    # below deliberately continue on the ORIGINAL frame (Story 3.4 Q1).
    if enable_cleaning:
        from backend.models.pipeline_config import ImputationPolicyConfig
        from backend.rules.cleaning_coordinator import clean_dataset

        policy = (
            cleaning_config.imputation
            if cleaning_config is not None
            else ImputationPolicyConfig()
        )
        log.info("cleaning_stage_started")
        _cleaned_df, cleaning_result = clean_dataset(
            df, result.quality_report, policy, pipeline_run_id
        )
        result.cleaning_result = cleaning_result
        log.info(
            "cleaning_stage_completed",
            actions=len(cleaning_result.actions),
            rows_before=cleaning_result.rows_before,
            rows_after=cleaning_result.rows_after,
        )

    # --- Stage 2: Drift Engine (Phase 2, optional; gated on dataset_key) ---
    if enable_drift and dataset_key is not None:
        result.drift_report = DriftEngine(baseline_dir=baseline_dir).run(
            df, dataset_key, pipeline_run_id
        )

    # --- Stage 3: Insight Engine ---
    payload = InsightEngine().generate_insights(
        df, result.quality_report, pipeline_run_id, drift_report=result.drift_report
    )

    # --- Stage 4: Narrative Generator ---
    insight_report = NarrativeGenerator().generate(payload, pipeline_run_id)
    result.insight_report = insight_report

    # --- Stage 5: Render ---
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
    clean: Annotated[
        bool,
        typer.Option(
            "--clean/--no-clean",
            help=(
                "Opt into automated cleaning (Tier-1 fixes + Tier-2 null "
                "imputation). Default: no cleaning. Policy is read from "
                "config.yaml's 'cleaning' section."
            ),
        ),
    ] = False,
) -> None:
    """Run the SAINT full analysis pipeline on a CSV file."""
    configure_logging()
    pipeline_run_id = str(uuid.uuid4())

    # Cleaning is off unless --clean is passed. Only when opted in do we read
    # config.yaml for the imputation policy (built-in defaults apply if absent).
    cleaning_config = None
    if clean:
        from backend.models.pipeline_config import PipelineConfig

        cleaning_config = PipelineConfig.load().cleaning

    try:
        result = run_full_pipeline(
            input_path=input,
            output_path=output,
            fmt=format,
            pipeline_run_id=pipeline_run_id,
            enable_cleaning=clean,
            cleaning_config=cleaning_config,
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
