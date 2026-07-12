"""Reporting Agent — Presentation-layer Typer CLI (Phase 2, Story 2.4).

A thin wrapper that invokes the pipeline orchestrator either once
(``generate``) or on a schedule (``schedule``). It computes nothing
analytical itself — all analysis lives in ``backend/pipeline/`` — and makes no
LLM calls (the narrative stage inside the pipeline uses ``LLMClient``).

    python -m backend.agents.reporting_agent generate --input data.csv --format docx
    python -m backend.agents.reporting_agent schedule

Architecture: ``backend/agents/`` is the only place besides ``api/`` allowed to
host CLI commands (architecture.md §745, §751); pipeline stages never import
from here. Drift is threaded through the orchestrator (DQA → Drift → Insights →
Narrative → Render) and gated on baseline existence.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

import structlog
import typer
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from backend.core.logging import configure_logging
from backend.errors.exceptions import SavvyCleanseError
from backend.models.pipeline_config import PipelineConfig
from backend.models.pipeline_result import PipelineResult
from backend.pipeline.orchestrator import OutputFormat, run_full_pipeline

_DEFAULT_BASELINE_DIR = "backend/baselines"

app = typer.Typer(add_completion=False, help="SAINT Reporting Agent.")


def _dataset_key_from_path(input_path: str | Path) -> str:
    """Derive a safe baseline key from an input file path.

    Lower-cases the filename stem and replaces anything outside
    ``[a-z0-9._-]`` with ``_``, then trims leading ``._-`` so the result
    satisfies ``DriftEngine``'s ``_SAFE_DATASET_KEY`` (must start with an
    alphanumeric). This is the caller-side derivation Story 2.3 deferred here.
    """
    stem = Path(input_path).stem.lower()
    key = re.sub(r"[^a-z0-9._-]", "_", stem).lstrip("._-")
    return key or "dataset"


def _timestamped_output_path(output_dir: str | Path, dataset_key: str, fmt: OutputFormat) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path(output_dir) / f"{dataset_key}_{stamp}.{fmt.value}"


def _run_once(
    config: PipelineConfig,
    input_path: str | Path,
    fmt: OutputFormat,
    *,
    baseline_dir: str | Path = _DEFAULT_BASELINE_DIR,
) -> PipelineResult:
    """Invoke the full pipeline once and log the outcome."""
    log = structlog.get_logger()
    dataset_key = _dataset_key_from_path(input_path)
    output_dir = Path(config.output.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = _timestamped_output_path(output_dir, dataset_key, fmt)
    pipeline_run_id = uuid.uuid4().hex

    result = run_full_pipeline(
        input_path=input_path,
        output_path=output_path,
        fmt=fmt,
        pipeline_run_id=pipeline_run_id,
        dataset_key=dataset_key,
        baseline_dir=baseline_dir,
    )

    log.info(
        "report_generated",
        pipeline_run_id=pipeline_run_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        status="halted" if result.halted else ("success" if result.success else "incomplete"),
        output=str(output_path),
        drift_included=result.drift_report is not None,
    )
    return result


def _build_trigger(config: PipelineConfig) -> IntervalTrigger | CronTrigger:
    """Map ``report_schedule`` to an APScheduler trigger."""
    sched = config.report_schedule
    if sched.cron:
        return CronTrigger.from_crontab(sched.cron)
    if sched.interval == "daily":
        return IntervalTrigger(days=1)
    if sched.interval == "weekly":
        return IntervalTrigger(weeks=1)
    # "monthly" — first of each month at 00:00 (IntervalTrigger has no months).
    return CronTrigger(day=1, hour=0, minute=0)


def _scheduled_run(
    config_path: str | Path | None,
    baseline_dir: str | Path = _DEFAULT_BASELINE_DIR,
) -> None:
    """One scheduled iteration: hot-reload config, run, swallow any failure.

    Reloads ``config.yaml`` on every fire so edits take effect without a
    restart (FR10). Any exception is logged and swallowed so the scheduler
    keeps running to the next fire (AC4).
    """
    log = structlog.get_logger()
    try:
        config = PipelineConfig.load(config_path)
        input_path = config.data_sources.paths[0]
        fmt = OutputFormat(config.output.format)
        _run_once(config, input_path, fmt, baseline_dir=baseline_dir)
    except Exception as exc:  # noqa: BLE001 — scheduled runs must never crash the loop
        log.error(
            "scheduled_run_failed",
            error=type(exc).__name__,
            detail=str(exc),
        )


@app.command()
def generate(
    input: Annotated[
        Path,
        typer.Option("--input", help="Path to input CSV file.", exists=True),
    ],
    format: Annotated[
        OutputFormat | None,
        typer.Option("--format", help="Output format (overrides config)."),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option("--config", help="Path to config.yaml (default: ./config.yaml)."),
    ] = None,
    baseline_dir: Annotated[
        Path | None,
        typer.Option("--baseline-dir", help="Baseline storage directory."),
    ] = None,
) -> None:
    """Generate a single report now."""
    configure_logging()
    try:
        cfg = PipelineConfig.load(config)
        fmt = format or OutputFormat(cfg.output.format)
        result = _run_once(
            cfg,
            input,
            fmt,
            baseline_dir=str(baseline_dir) if baseline_dir else _DEFAULT_BASELINE_DIR,
        )
    except SavvyCleanseError as exc:
        structlog.get_logger().error(
            "reporting_agent_error", error=type(exc).__name__, detail=str(exc)
        )
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if result.halted:
        typer.echo(f"Pipeline halted | reason={result.halt_reason}", err=True)
        raise typer.Exit(code=1)

    typer.echo("Report generated.")


@app.command()
def schedule(
    config: Annotated[
        Path | None,
        typer.Option("--config", help="Path to config.yaml (default: ./config.yaml)."),
    ] = None,
    baseline_dir: Annotated[
        Path | None,
        typer.Option("--baseline-dir", help="Baseline storage directory."),
    ] = None,
) -> None:
    """Run the pipeline on the configured schedule (foreground, blocking)."""
    configure_logging()
    cfg = PipelineConfig.load(config)
    trigger = _build_trigger(cfg)
    resolved_baseline = str(baseline_dir) if baseline_dir else _DEFAULT_BASELINE_DIR

    scheduler = BlockingScheduler()
    scheduler.add_job(
        _scheduled_run,
        trigger=trigger,
        args=[config, resolved_baseline],
        id="reporting_agent_pipeline",
    )
    structlog.get_logger().info(
        "reporting_agent_scheduled",
        schedule=cfg.report_schedule.interval or cfg.report_schedule.cron,
    )
    scheduler.start()


if __name__ == "__main__":
    app()
