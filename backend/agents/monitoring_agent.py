"""Monitoring Agent — Presentation-layer Typer CLI (Phase 2, Story 2.5).

A thin agent that compares a current dataset against the previous period's
baseline, applies the configured ``metric_thresholds`` to the resulting drift
findings, and delivers structured alerts via a JSON log file and email. It
computes nothing analytical itself — drift is the Drift Engine's job (Story
2.3); this agent only decides *materiality* by evaluating thresholds against
findings (architecture.md §199, §203, §221) — and it makes no LLM calls.

    python -m backend.agents.monitoring_agent evaluate --input current.csv

Read-only on baselines: it uses ``DriftEngine.compute_drift`` (pure) against a
loaded baseline and never ``run`` — rotation/mutation of baselines is the
Reporting Agent's pipeline concern (Story 2.4). SMTP delivery is best-effort:
the JSON alert file is the durable record and is always written first; an SMTP
failure is downgraded to a warning and never crashes the agent
(architecture.md §469-477, §745, §751, §807).
"""

from __future__ import annotations

import json
import smtplib
import uuid
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Annotated

import pandas as pd
import structlog
import typer

from backend.agents.reporting_agent import _dataset_key_from_path
from backend.core.logging import configure_logging
from backend.errors.exceptions import ConfigurationError, SavvyCleanseError
from backend.models.alert import AlertFinding, AlertMessage, AlertRule
from backend.models.drift_report import DriftReport
from backend.models.pipeline_config import PipelineConfig
from backend.pipeline.drift_engine import DriftEngine

_DEFAULT_BASELINE_DIR = "backend/baselines"

app = typer.Typer(add_completion=False, help="SavvyCortex Monitoring Agent.")


@app.callback()
def _main() -> None:
    """SavvyCortex Monitoring Agent.

    Present so Typer keeps ``evaluate`` as an explicit subcommand (a single-
    command Typer app would otherwise drop the verb) — the AC-1 invocation is
    ``python -m backend.agents.monitoring_agent evaluate --input ...``.
    """


# ---------------------------------------------------------------------------
# Threshold evaluation (Task 2) — pure, unit-testable, no I/O
# ---------------------------------------------------------------------------
def _evaluate(
    drift_report: DriftReport,
    thresholds: dict[str, float],
    dataset: str,
) -> list[AlertMessage]:
    """Map breached ``metric_thresholds`` onto ``AlertMessage``s.

    For each configured ``(column, threshold)`` pair, find that column's
    ``mean_shift`` drift finding; when present and
    ``abs(actual_value) > threshold`` it is a breach → one ``AlertMessage``.

    Pure function — no I/O — so it is directly unit-testable.

    Documented limitation: the Drift Engine only emits a ``mean_shift`` finding
    above its fixed LOW band (>5%), so a configured threshold below 5% cannot
    trigger via drift consumption. The default thresholds (+-15/20%) sit well
    above this floor.
    """
    mean_shift_by_column = {
        col_drift.column: col_drift.mean_shift
        for col_drift in drift_report.numeric_drift
        if col_drift.mean_shift is not None
    }

    alerts: list[AlertMessage] = []
    for column, threshold in thresholds.items():
        finding = mean_shift_by_column.get(column)
        if finding is None:
            continue
        if abs(finding.actual_value) > threshold:
            alerts.append(
                AlertMessage(
                    alert_id=uuid.uuid4().hex,
                    triggered_at=datetime.now(timezone.utc).isoformat(),
                    rule=AlertRule(type="mean_shift", column=column, threshold=threshold),
                    finding=AlertFinding(
                        actual_value=finding.actual_value,
                        severity=finding.severity,
                        detail=finding.detail,
                    ),
                    dataset=dataset,
                )
            )
    return alerts


def _load_drift(
    current_df: pd.DataFrame,
    dataset_key: str,
    baseline_dir: str | Path,
    pipeline_run_id: str = "",
) -> DriftReport | None:
    """Compute drift for ``current_df`` against its persisted baseline.

    Returns ``None`` when no baseline exists (the first period — nothing to
    compare against). Uses the *pure* ``compute_drift`` against a read-only
    ``load_baseline`` — never ``run`` — so monitoring never rotates or mutates
    a baseline. A corrupt baseline propagates ``DriftComputationError`` from the
    engine unchanged.
    """
    engine = DriftEngine(baseline_dir=baseline_dir)
    baseline = engine.load_baseline(dataset_key)
    if baseline is None:
        return None
    return engine.compute_drift(current_df, baseline, pipeline_run_id)


# ---------------------------------------------------------------------------
# Delivery (Task 3)
# ---------------------------------------------------------------------------
def _write_alert_log(alerts: list[AlertMessage], output_dir: str | Path) -> Path:
    """Write the alerts as a JSON array under ``{output_dir}/alerts/`` (FR8).

    This is the durable record and always happens first — before any structlog
    emission or email attempt — so delivery survives an SMTP failure.
    """
    alerts_dir = Path(output_dir) / "alerts"
    alerts_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = alerts_dir / f"{alerts[0].dataset}_{stamp}.json"
    payload = [alert.model_dump(mode="json") for alert in alerts]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _build_email_body(alerts: list[AlertMessage]) -> str:
    """Plain-text body: per-alert severity, rule, actual-vs-threshold, dataset."""
    lines = [f"{len(alerts)} monitoring alert(s) triggered.", ""]
    for alert in alerts:
        lines.extend(
            [
                f"- [{alert.finding.severity.value.upper()}] {alert.rule.type} "
                f"on '{alert.rule.column}' (dataset: {alert.dataset})",
                f"    actual {alert.finding.actual_value:+.1%} vs threshold "
                f"+-{alert.rule.threshold:.1%}",
                f"    {alert.finding.detail}",
                "",
            ]
        )
    return "\n".join(lines)


def _send_email(alerts: list[AlertMessage], config: PipelineConfig) -> None:
    """Send all alerts to every configured recipient via SMTP (best-effort).

    Skipped with an info log (not a failure) when no recipients or no SMTP host
    is configured. The send is wrapped in try/except: any failure is logged as
    an ``smtp_delivery_failed`` warning and swallowed — the JSON alert log is
    already written, so email is never allowed to crash the agent (AC6).
    """
    log = structlog.get_logger()
    recipients = [str(r) for r in config.alert_recipients.recipients]
    smtp = config.smtp

    if not recipients or not smtp.host:
        log.info(
            "alert_email_skipped",
            reason="no recipients or SMTP host configured",
            recipient_count=len(recipients),
            smtp_configured=bool(smtp.host),
        )
        return

    from_address = smtp.from_address or smtp.username or "savvycortex@localhost"
    message = EmailMessage()
    message["Subject"] = f"[SavvyCortex] {len(alerts)} monitoring alert(s)"
    message["From"] = from_address
    message["To"] = ", ".join(recipients)
    message.set_content(_build_email_body(alerts))

    try:
        with smtplib.SMTP(smtp.host, smtp.port) as server:
            if smtp.username and smtp.password:
                server.starttls()
                server.login(smtp.username, smtp.password)
            server.sendmail(from_address, recipients, message.as_string())
        log.info("alert_email_sent", recipient_count=len(recipients))
    except Exception as exc:  # noqa: BLE001 — delivery is best-effort; never crash
        log.warning(
            "smtp_delivery_failed",
            error=type(exc).__name__,
            detail=str(exc),
            recipient_count=len(recipients),
        )


def _read_csv(input_path: str | Path) -> pd.DataFrame:
    """Read the current dataset, wrapping parse errors as ``ConfigurationError``."""
    try:
        return pd.read_csv(input_path)
    except Exception as exc:  # noqa: BLE001 — normalize to a pre-flight config error
        raise ConfigurationError(
            f"Cannot parse CSV '{input_path}': {type(exc).__name__}: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# CLI command
# ---------------------------------------------------------------------------
@app.command()
def evaluate(
    input: Annotated[
        Path,
        typer.Option("--input", help="Path to the current-period CSV file.", exists=True),
    ],
    config: Annotated[
        Path | None,
        typer.Option("--config", help="Path to config.yaml (default: ./config.yaml)."),
    ] = None,
    baseline_dir: Annotated[
        Path | None,
        typer.Option("--baseline-dir", help="Baseline storage directory."),
    ] = None,
) -> None:
    """Evaluate current metrics against the previous period and deliver alerts.

    Re-loads config on every run (FR10 hot-reload), so a threshold edited
    between runs takes effect without a restart.
    """
    configure_logging()
    log = structlog.get_logger()
    resolved_baseline = str(baseline_dir) if baseline_dir else _DEFAULT_BASELINE_DIR

    try:
        cfg = PipelineConfig.load(config)
        current_df = _read_csv(input)
        dataset_key = _dataset_key_from_path(input)
        drift_report = _load_drift(current_df, dataset_key, resolved_baseline)
    except SavvyCleanseError as exc:
        log.error("monitoring_agent_error", error=type(exc).__name__, detail=str(exc))
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    # No baseline → no previous period to compare against (AC2).
    if drift_report is None:
        log.info("monitoring_clean", dataset=dataset_key, reason="no_baseline", alert_count=0)
        typer.echo("No baseline for this dataset — nothing to compare. Monitoring clean.")
        return

    alerts = _evaluate(drift_report, cfg.metric_thresholds.thresholds, dataset_key)

    # No breach → clean run (AC4).
    if not alerts:
        log.info(
            "monitoring_clean", dataset=dataset_key, reason="no_threshold_breach", alert_count=0
        )
        typer.echo("No thresholds breached. Monitoring clean.")
        return

    # Delivery order (AC3): durable JSON log → per-alert structlog → email.
    log_path = _write_alert_log(alerts, cfg.output.output_dir)
    for alert in alerts:
        log.info(
            "alert_triggered",
            alert_id=alert.alert_id,
            severity=alert.finding.severity.value,
            rule_type=alert.rule.type,
            column=alert.rule.column,
            threshold=alert.rule.threshold,
            actual_value=alert.finding.actual_value,
            dataset=alert.dataset,
        )
    _send_email(alerts, cfg)

    typer.echo(f"{len(alerts)} alert(s) delivered → {log_path}")


if __name__ == "__main__":
    app()
