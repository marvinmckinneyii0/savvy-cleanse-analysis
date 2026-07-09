"""Tests for the Monitoring Agent (Story 2.5).

Covers pure threshold evaluation (single/multiple/no breach, drift-based rule
mapping), the ``evaluate`` command end-to-end (breach → JSON log + mocked email,
clean run, first-run no-baseline), SMTP failure isolation, and threshold
hot-reload flipping the outcome.

Discipline: every write is scoped to ``tmp_path``; ``smtplib.SMTP`` is always
mocked (never a real send). Log-event assertions call the command function
directly with ``configure_logging`` neutralised so ``capture_logs`` survives
(the real CLI reconfigures structlog); one ``CliRunner`` test exercises the
actual Typer wiring and exit code.
"""

from __future__ import annotations

import json
import smtplib
from pathlib import Path

import pandas as pd
import pytest
import structlog
from typer.testing import CliRunner

from backend.agents import monitoring_agent as ma
from backend.models.alert import AlertMessage
from backend.models.drift_report import (
    DriftFinding,
    DriftReport,
    NumericColumnDrift,
    SchemaDrift,
    VolumeDrift,
)
from backend.models.quality_report import Severity
from backend.pipeline.drift_engine import DriftEngine

runner = CliRunner()


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------
def _write_csv(path: Path, *, revenue_scale: float = 1.0) -> Path:
    """A clean 15-row sales CSV (mirrors the Reporting Agent test fixture)."""
    rows = 15
    df = pd.DataFrame(
        {
            "date": [f"2026-01-{i + 1:02d}" for i in range(rows)],
            "region": [["north", "south", "east", "west"][i % 4] for i in range(rows)],
            "revenue": [round((1000.0 + i * 25) * revenue_scale, 2) for i in range(rows)],
        }
    )
    df.to_csv(path, index=False)
    return path


def _write_config(tmp_path: Path, out_dir: Path, *, revenue_threshold: float = 0.15) -> Path:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "data_sources:\n"
        f"  - {(tmp_path / 'sales.csv').as_posix()}\n"
        "report_schedule:\n"
        "  interval: weekly\n"
        "output:\n"
        "  format: docx\n"
        f"  output_dir: {out_dir.as_posix()}\n"
        "metric_thresholds:\n"
        f"  revenue: {revenue_threshold}\n"
        "alert_recipients:\n"
        "  - ops@example.com\n",
        encoding="utf-8",
    )
    return cfg


def _seed_baseline(baseline_dir: Path, dataset_key: str, base_df: pd.DataFrame) -> None:
    engine = DriftEngine(baseline_dir=baseline_dir)
    engine._save_baseline(dataset_key, engine._build_profile(base_df, dataset_key))


def _drift_report(mean_shifts: dict[str, float]) -> DriftReport:
    """Build a minimal DriftReport carrying the given per-column mean shifts."""
    numeric: list[NumericColumnDrift] = []
    for col, val in mean_shifts.items():
        severity = (
            Severity.HIGH
            if abs(val) > 0.30
            else Severity.MEDIUM
            if abs(val) > 0.15
            else Severity.LOW
        )
        numeric.append(
            NumericColumnDrift(
                column=col,
                mean_shift=DriftFinding(
                    check="mean_shift",
                    column=col,
                    severity=severity,
                    actual_value=val,
                    detail=f"{col} mean {val:+.1%} vs baseline",
                ),
            )
        )
    return DriftReport(
        pipeline_run_id="test",
        computed_at="2026-07-09T00:00:00Z",
        volume_drift=VolumeDrift(current_row_count=15, baseline_row_count=15, pct_change=0.0),
        numeric_drift=numeric,
        categorical_drift=[],
        schema_drift=SchemaDrift(columns_added=[], columns_removed=[], dtype_changes={}),
        drift_summary="test",
        overall_severity=Severity.HIGH,
        recommendations=[],
    )


def _make_fake_smtp(record: dict):
    class FakeSMTP:
        def __init__(self, host, port):
            record["init"] = (host, port)

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def starttls(self):
            record["starttls"] = True

        def login(self, username, password):
            record["login"] = (username, password)

        def sendmail(self, from_addr, to_addrs, msg):
            record.setdefault("sendmail", []).append((from_addr, to_addrs, msg))

    return FakeSMTP


# ---------------------------------------------------------------------------
# Task 2 — pure threshold evaluation
# ---------------------------------------------------------------------------
class TestEvaluate:
    def test_single_breach(self) -> None:
        report = _drift_report({"revenue": 0.32})
        alerts = ma._evaluate(report, {"revenue": 0.15}, "sales")
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.rule.type == "mean_shift"
        assert alert.rule.column == "revenue"
        assert alert.rule.threshold == 0.15
        assert alert.finding.actual_value == 0.32
        assert alert.finding.severity == Severity.HIGH
        assert alert.dataset == "sales"

    def test_multiple_breach(self) -> None:
        report = _drift_report({"revenue": 0.32, "units": -0.40, "cost": 0.03})
        # cost has a mean_shift finding but a *loose* threshold → not a breach.
        alerts = ma._evaluate(
            report, {"revenue": 0.15, "units": 0.20, "cost": 0.50}, "sales"
        )
        breached = {a.rule.column for a in alerts}
        assert breached == {"revenue", "units"}

    def test_no_breach(self) -> None:
        report = _drift_report({"revenue": 0.10})
        assert ma._evaluate(report, {"revenue": 0.15}, "sales") == []

    def test_negative_shift_breaches_on_magnitude(self) -> None:
        report = _drift_report({"revenue": -0.40})
        alerts = ma._evaluate(report, {"revenue": 0.15}, "sales")
        assert len(alerts) == 1
        assert alerts[0].finding.actual_value == -0.40

    def test_threshold_absent_column_ignored(self) -> None:
        report = _drift_report({"revenue": 0.32})
        # Configured threshold for a column with no mean_shift finding → skipped.
        assert ma._evaluate(report, {"margin": 0.15}, "sales") == []

    def test_drift_based_rule_mapping(self) -> None:
        report = _drift_report({"revenue": 0.32})
        alerts = ma._evaluate(report, {"revenue": 0.15}, "sales")
        assert len(alerts) == 1
        assert alerts[0].rule.type == "mean_shift"
        assert alerts[0].rule.column == "revenue"
        assert alerts[0].finding.actual_value == 0.32


# ---------------------------------------------------------------------------
# Task 3 — delivery (log + email)
# ---------------------------------------------------------------------------
class TestDelivery:
    def _one_alert(self) -> list[AlertMessage]:
        return ma._evaluate(_drift_report({"revenue": 0.40}), {"revenue": 0.15}, "sales")

    def test_write_alert_log_writes_json_array(self, tmp_path: Path) -> None:
        alerts = self._one_alert()
        path = ma._write_alert_log(alerts, tmp_path / "out")
        assert path.parent == tmp_path / "out" / "alerts"
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(payload, list) and len(payload) == 1
        assert payload[0]["rule"]["column"] == "revenue"
        assert payload[0]["finding"]["severity"] == "high"

    def test_send_email_skipped_without_host(self, tmp_path: Path) -> None:
        from backend.models.pipeline_config import PipelineConfig

        cfg = PipelineConfig.load(_write_config(tmp_path, tmp_path / "out"))
        # No SMTP_HOST in env for this config → skip, not failure.
        assert cfg.smtp.host is None
        with structlog.testing.capture_logs() as captured:
            ma._send_email(self._one_alert(), cfg)
        assert any(e["event"] == "alert_email_skipped" for e in captured)
        assert not any(e["event"] == "smtp_delivery_failed" for e in captured)

    def test_send_email_sends_via_smtp(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from backend.models.pipeline_config import PipelineConfig

        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "user")
        monkeypatch.setenv("SMTP_PASSWORD", "pass")
        monkeypatch.setenv("SMTP_FROM", "alerts@example.com")
        cfg = PipelineConfig.load(_write_config(tmp_path, tmp_path / "out"))

        record: dict = {}
        monkeypatch.setattr(smtplib, "SMTP", _make_fake_smtp(record))

        with structlog.testing.capture_logs() as captured:
            ma._send_email(self._one_alert(), cfg)

        assert record["init"] == ("smtp.example.com", 587)
        assert record.get("starttls") is True
        assert len(record["sendmail"]) == 1
        from_addr, to_addrs, body = record["sendmail"][0]
        assert from_addr == "alerts@example.com"
        assert to_addrs == ["ops@example.com"]
        assert "revenue" in body
        assert any(e["event"] == "alert_email_sent" for e in captured)

    def test_send_email_smtp_failure_is_isolated(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from backend.models.pipeline_config import PipelineConfig

        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        cfg = PipelineConfig.load(_write_config(tmp_path, tmp_path / "out"))

        class RaisingSMTP:
            def __init__(self, host, port):
                raise smtplib.SMTPConnectError(421, "server unreachable")

        monkeypatch.setattr(smtplib, "SMTP", RaisingSMTP)

        with structlog.testing.capture_logs() as captured:
            # Must NOT raise — delivery is best-effort.
            ma._send_email(self._one_alert(), cfg)

        failures = [e for e in captured if e["event"] == "smtp_delivery_failed"]
        assert len(failures) == 1
        assert failures[0]["error"] == "SMTPConnectError"


# ---------------------------------------------------------------------------
# Task 2 + 3 — `evaluate` command end-to-end
# ---------------------------------------------------------------------------
class TestEvaluateCommand:
    def _run(self, tmp_path, monkeypatch, out_dir, threshold, *, seed_scale=None):
        """Invoke ``evaluate`` directly with logging capture-safe.

        ``seed_scale`` — when set, seed a baseline whose revenue is scaled by it
        (0.6 → current is ~40% higher → HIGH mean-shift breach). When ``None``,
        no baseline is seeded (first-run path).
        """
        _write_csv(tmp_path / "sales.csv")
        cfg = _write_config(tmp_path, out_dir, revenue_threshold=threshold)
        baselines = tmp_path / "baselines"
        if seed_scale is not None:
            base_df = pd.read_csv(tmp_path / "sales.csv")
            base_df["revenue"] = (base_df["revenue"] * seed_scale).round(2)
            _seed_baseline(baselines, "sales", base_df)

        record: dict = {}
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setattr(smtplib, "SMTP", _make_fake_smtp(record))
        monkeypatch.setattr(ma, "configure_logging", lambda: None)

        with structlog.testing.capture_logs() as captured:
            ma.evaluate(input=tmp_path / "sales.csv", config=cfg, baseline_dir=baselines)
        return captured, record

    def test_breach_writes_log_and_sends_email(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        out_dir = tmp_path / "out"
        captured, record = self._run(tmp_path, monkeypatch, out_dir, 0.15, seed_scale=0.6)

        alert_files = list((out_dir / "alerts").glob("sales_*.json"))
        assert len(alert_files) == 1
        assert record.get("sendmail"), "SMTP.sendmail was not called"
        triggered = [e for e in captured if e["event"] == "alert_triggered"]
        assert len(triggered) == 1
        assert triggered[0]["column"] == "revenue"

    def test_clean_run_no_breach(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        out_dir = tmp_path / "out"
        # Baseline identical to current (scale 1.0) → no mean shift → no breach.
        captured, record = self._run(tmp_path, monkeypatch, out_dir, 0.15, seed_scale=1.0)

        assert not (out_dir / "alerts").exists()
        assert record == {}  # email never attempted
        clean = [e for e in captured if e["event"] == "monitoring_clean"]
        assert len(clean) == 1
        assert clean[0]["reason"] == "no_threshold_breach"

    def test_first_run_no_baseline(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        out_dir = tmp_path / "out"
        captured, record = self._run(tmp_path, monkeypatch, out_dir, 0.15, seed_scale=None)

        assert not (out_dir / "alerts").exists()
        clean = [e for e in captured if e["event"] == "monitoring_clean"]
        assert len(clean) == 1
        assert clean[0]["reason"] == "no_baseline"

    def test_smtp_failure_still_writes_log(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        out_dir = tmp_path / "out"
        _write_csv(tmp_path / "sales.csv")
        cfg = _write_config(tmp_path, out_dir, revenue_threshold=0.15)
        baselines = tmp_path / "baselines"
        base_df = pd.read_csv(tmp_path / "sales.csv")
        base_df["revenue"] = (base_df["revenue"] * 0.6).round(2)
        _seed_baseline(baselines, "sales", base_df)

        class RaisingSMTP:
            def __init__(self, host, port):
                raise OSError("network down")

        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setattr(smtplib, "SMTP", RaisingSMTP)
        monkeypatch.setattr(ma, "configure_logging", lambda: None)

        with structlog.testing.capture_logs() as captured:
            ma.evaluate(input=tmp_path / "sales.csv", config=cfg, baseline_dir=baselines)

        # JSON log is written despite SMTP failure; agent does not crash.
        assert len(list((out_dir / "alerts").glob("sales_*.json"))) == 1
        assert any(e["event"] == "smtp_delivery_failed" for e in captured)

    def test_threshold_hot_reload_flips_outcome(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_csv(tmp_path / "sales.csv")
        baselines = tmp_path / "baselines"
        base_df = pd.read_csv(tmp_path / "sales.csv")
        base_df["revenue"] = (base_df["revenue"] / 1.4).round(2)  # ~+40% shift
        _seed_baseline(baselines, "sales", base_df)

        out_dir = tmp_path / "out"
        cfg = _write_config(tmp_path, out_dir, revenue_threshold=0.15)  # tight → breach
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setattr(smtplib, "SMTP", _make_fake_smtp({}))
        monkeypatch.setattr(ma, "configure_logging", lambda: None)

        with structlog.testing.capture_logs() as run1:
            ma.evaluate(input=tmp_path / "sales.csv", config=cfg, baseline_dir=baselines)
        assert any(e["event"] == "alert_triggered" for e in run1)

        # Loosen the threshold on disk; the next run must re-load and no longer alert.
        _write_config(tmp_path, out_dir, revenue_threshold=0.50)
        with structlog.testing.capture_logs() as run2:
            ma.evaluate(input=tmp_path / "sales.csv", config=cfg, baseline_dir=baselines)
        assert not any(e["event"] == "alert_triggered" for e in run2)
        assert any(e["event"] == "monitoring_clean" for e in run2)


class TestCliWiring:
    def test_cli_evaluate_exit_zero_and_writes_alert(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        out_dir = tmp_path / "out"
        _write_csv(tmp_path / "sales.csv")
        cfg = _write_config(tmp_path, out_dir, revenue_threshold=0.15)
        baselines = tmp_path / "baselines"
        base_df = pd.read_csv(tmp_path / "sales.csv")
        base_df["revenue"] = (base_df["revenue"] * 0.6).round(2)
        _seed_baseline(baselines, "sales", base_df)

        record: dict = {}
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setattr(smtplib, "SMTP", _make_fake_smtp(record))

        result = runner.invoke(
            ma.app,
            [
                "evaluate",
                "--input", str(tmp_path / "sales.csv"),
                "--config", str(cfg),
                "--baseline-dir", str(baselines),
            ],
        )
        assert result.exit_code == 0, result.output
        assert len(list((out_dir / "alerts").glob("sales_*.json"))) == 1
        assert record.get("sendmail"), "SMTP.sendmail was not called"
