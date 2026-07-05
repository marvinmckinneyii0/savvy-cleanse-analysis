"""Tests for the Story 2.1 configuration layer.

Covers: valid config load with defaults, missing required fields, invalid
values (bad cron, negative threshold, bad email), environment-variable
secret override, and reload-reflects-changes behavior. All file I/O uses
``tmp_path`` — never the real repo-root ``config.yaml``.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import structlog

from backend.errors.exceptions import ConfigurationError
from backend.models.pipeline_config import DEFAULT_THRESHOLD, PipelineConfig

VALID_CONFIG = """\
data_sources:
  - data/sales.csv

report_schedule:
  interval: weekly

metric_thresholds:
  revenue: 0.15
  units_sold: 0.20

alert_recipients:
  - ops@example.com

output:
  format: docx
  output_dir: output/
"""


def _write_config(tmp_path: Path, text: str) -> Path:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(text, encoding="utf-8")
    return config_path


def test_valid_config_loads_with_defaults(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path, VALID_CONFIG)

    config = PipelineConfig.load(config_path)

    assert isinstance(config, PipelineConfig)
    assert config.data_sources == ["data/sales.csv"]
    assert config.report_schedule.interval == "weekly"
    assert config.metric_thresholds["revenue"] == 0.15
    assert config.alert_recipients == ["ops@example.com"]
    assert config.output.format == "docx"
    assert config.threshold_for("unconfigured_metric") == DEFAULT_THRESHOLD


def test_missing_required_field_raises_configuration_error(tmp_path: Path) -> None:
    text = """\
report_schedule:
  interval: daily
"""
    config_path = _write_config(tmp_path, text)

    with pytest.raises(ConfigurationError):
        PipelineConfig.load(config_path)


def test_malformed_cron_raises_configuration_error(tmp_path: Path) -> None:
    text = """\
data_sources:
  - data/sales.csv
report_schedule:
  cron: "not a cron expression"
"""
    config_path = _write_config(tmp_path, text)

    with pytest.raises(ConfigurationError):
        PipelineConfig.load(config_path)


def test_negative_threshold_raises_configuration_error(tmp_path: Path) -> None:
    text = """\
data_sources:
  - data/sales.csv
report_schedule:
  interval: daily
metric_thresholds:
  revenue: -0.1
"""
    config_path = _write_config(tmp_path, text)

    with pytest.raises(ConfigurationError):
        PipelineConfig.load(config_path)


def test_bad_email_raises_configuration_error(tmp_path: Path) -> None:
    text = """\
data_sources:
  - data/sales.csv
report_schedule:
  interval: daily
alert_recipients:
  - not-an-email
"""
    config_path = _write_config(tmp_path, text)

    with pytest.raises(ConfigurationError):
        PipelineConfig.load(config_path)


def test_env_override_populates_smtp_and_is_absent_from_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = _write_config(tmp_path, VALID_CONFIG)
    monkeypatch.setenv("SMTP_PASSWORD", "super-secret")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")

    config = PipelineConfig.load(config_path)

    assert config.smtp.password == "super-secret"
    assert config.smtp.host == "smtp.example.com"
    assert "super-secret" not in config_path.read_text(encoding="utf-8")


def test_reload_reflects_changes(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path, VALID_CONFIG)

    first = PipelineConfig.load(config_path)
    assert first.report_schedule.interval == "weekly"

    updated = VALID_CONFIG.replace("interval: weekly", "interval: daily")
    config_path.write_text(updated, encoding="utf-8")

    second = PipelineConfig.load(config_path)
    assert second.report_schedule.interval == "daily"


def test_config_loaded_log_event_has_no_secrets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = _write_config(tmp_path, VALID_CONFIG)
    monkeypatch.setenv("SMTP_PASSWORD", "super-secret")

    with structlog.testing.capture_logs() as captured:
        PipelineConfig.load(config_path)

    events = [entry for entry in captured if entry.get("event") == "config_loaded"]
    assert len(events) == 1
    payload = events[0]
    assert payload["recipient_count"] == 1
    assert "super-secret" not in str(payload)
