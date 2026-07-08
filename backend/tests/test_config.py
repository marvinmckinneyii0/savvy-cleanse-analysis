"""Tests for the Configuration Layer (Story 2.1).

Covers: valid config, missing required fields, invalid values (bad cron,
negative threshold, bad email), environment-variable override for secrets,
reload-reflects-changes behavior, and the config_loaded log event.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import structlog

from backend.errors.exceptions import ConfigurationError
from backend.models.pipeline_config import PipelineConfig

VALID_CONFIG = """
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


def _write_config(tmp_path: Path, content: str) -> Path:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(content, encoding="utf-8")
    return config_path


class TestValidConfig:
    def test_loads_typed_config_with_declared_values(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, VALID_CONFIG)

        config = PipelineConfig.load(config_path)

        assert isinstance(config, PipelineConfig)
        assert config.data_sources.paths == ["data/sales.csv"]
        assert config.report_schedule.interval == "weekly"
        assert config.report_schedule.cron is None
        assert config.metric_thresholds.thresholds == {
            "revenue": 0.15,
            "units_sold": 0.20,
        }
        assert config.alert_recipients.recipients == ["ops@example.com"]
        assert config.output.format == "docx"

    def test_defaults_applied_when_optional_sections_omitted(
        self, tmp_path: Path
    ) -> None:
        minimal = """
data_sources:
  - data/sales.csv
report_schedule:
  interval: daily
"""
        config = PipelineConfig.load(_write_config(tmp_path, minimal))

        assert config.metric_thresholds.thresholds == {}
        assert config.metric_thresholds.get("revenue") == 0.15
        assert config.alert_recipients.recipients == []
        assert config.output.format == "docx"
        assert config.output.output_dir == "output/"

    def test_missing_config_file_raises_configuration_error(
        self, tmp_path: Path
    ) -> None:
        with pytest.raises(ConfigurationError):
            PipelineConfig.load(tmp_path / "does-not-exist.yaml")

    def test_malformed_yaml_raises_configuration_error(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, "data_sources: [unterminated")

        with pytest.raises(ConfigurationError):
            PipelineConfig.load(config_path)


class TestMissingRequiredFields:
    def test_missing_data_sources_raises_configuration_error(
        self, tmp_path: Path
    ) -> None:
        content = """
report_schedule:
  interval: daily
"""
        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(_write_config(tmp_path, content))

    def test_missing_report_schedule_raises_configuration_error(
        self, tmp_path: Path
    ) -> None:
        content = """
data_sources:
  - data/sales.csv
"""
        with pytest.raises(ConfigurationError, match="report_schedule"):
            PipelineConfig.load(_write_config(tmp_path, content))

    def test_empty_data_sources_list_raises_configuration_error(
        self, tmp_path: Path
    ) -> None:
        content = """
data_sources: []
report_schedule:
  interval: daily
"""
        with pytest.raises(ConfigurationError):
            PipelineConfig.load(_write_config(tmp_path, content))


class TestInvalidValues:
    def test_invalid_cron_expression_raises_configuration_error(
        self, tmp_path: Path
    ) -> None:
        content = """
data_sources:
  - data/sales.csv
report_schedule:
  cron: "not a cron expression"
"""
        with pytest.raises(ConfigurationError, match="cron"):
            PipelineConfig.load(_write_config(tmp_path, content))

    def test_interval_and_cron_both_set_raises_configuration_error(
        self, tmp_path: Path
    ) -> None:
        content = """
data_sources:
  - data/sales.csv
report_schedule:
  interval: daily
  cron: "0 6 * * 1"
"""
        with pytest.raises(ConfigurationError):
            PipelineConfig.load(_write_config(tmp_path, content))

    def test_negative_threshold_raises_configuration_error(
        self, tmp_path: Path
    ) -> None:
        content = """
data_sources:
  - data/sales.csv
report_schedule:
  interval: daily
metric_thresholds:
  revenue: -0.15
"""
        with pytest.raises(ConfigurationError, match="revenue"):
            PipelineConfig.load(_write_config(tmp_path, content))

    def test_zero_threshold_raises_configuration_error(self, tmp_path: Path) -> None:
        content = """
data_sources:
  - data/sales.csv
report_schedule:
  interval: daily
metric_thresholds:
  revenue: 0
"""
        with pytest.raises(ConfigurationError):
            PipelineConfig.load(_write_config(tmp_path, content))

    def test_malformed_email_raises_configuration_error(self, tmp_path: Path) -> None:
        content = """
data_sources:
  - data/sales.csv
report_schedule:
  interval: daily
alert_recipients:
  - not-an-email
"""
        with pytest.raises(ConfigurationError):
            PipelineConfig.load(_write_config(tmp_path, content))

    def test_data_sources_as_mapping_raises_configuration_error(
        self, tmp_path: Path
    ) -> None:
        """A YAML indentation mistake (mapping instead of a list) must be
        rejected, not silently accepted as an empty data_sources list.
        """
        content = """
data_sources:
  file: data/sales.csv
report_schedule:
  interval: daily
"""
        with pytest.raises(ConfigurationError):
            PipelineConfig.load(_write_config(tmp_path, content))

    def test_alert_recipients_as_mapping_raises_configuration_error(
        self, tmp_path: Path
    ) -> None:
        """A YAML indentation mistake (mapping instead of a list) must be
        rejected, not silently accepted as an empty alert_recipients list.
        """
        content = """
data_sources:
  - data/sales.csv
report_schedule:
  interval: daily
alert_recipients:
  primary: ops@example.com
"""
        with pytest.raises(ConfigurationError):
            PipelineConfig.load(_write_config(tmp_path, content))


class TestEnvironmentOverride:
    def test_smtp_password_sourced_from_env_not_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "alerts@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "super-secret-value")
        monkeypatch.setenv("SMTP_FROM", "alerts@example.com")

        config_path = _write_config(tmp_path, VALID_CONFIG)
        config = PipelineConfig.load(config_path)

        assert config.smtp.password == "super-secret-value"
        assert config.smtp.host == "smtp.example.com"
        # The secret never appears anywhere in the YAML on disk.
        assert "super-secret-value" not in config_path.read_text(encoding="utf-8")

    def test_smtp_settings_absent_from_yaml_are_still_populated_from_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_PASSWORD", "another-secret")
        config_path = _write_config(tmp_path, VALID_CONFIG)

        config = PipelineConfig.load(config_path)

        assert config.smtp.password == "another-secret"


class TestReload:
    def test_second_load_reflects_file_changes(self, tmp_path: Path) -> None:
        content_v1 = """
data_sources:
  - data/sales.csv
report_schedule:
  interval: daily
metric_thresholds:
  revenue: 0.15
"""
        content_v2 = """
data_sources:
  - data/sales.csv
report_schedule:
  interval: monthly
metric_thresholds:
  revenue: 0.30
"""
        config_path = _write_config(tmp_path, content_v1)

        first = PipelineConfig.load(config_path)
        assert first.report_schedule.interval == "daily"
        assert first.metric_thresholds.thresholds["revenue"] == 0.15

        config_path.write_text(content_v2, encoding="utf-8")
        second = PipelineConfig.load(config_path)

        assert second.report_schedule.interval == "monthly"
        assert second.metric_thresholds.thresholds["revenue"] == 0.30


class TestObservability:
    def test_config_loaded_event_emitted_with_no_secrets(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_PASSWORD", "should-never-be-logged")
        config_path = _write_config(tmp_path, VALID_CONFIG)

        with structlog.testing.capture_logs() as captured:
            PipelineConfig.load(config_path)

        events = [e for e in captured if e.get("event") == "config_loaded"]
        assert len(events) == 1

        event = events[0]
        assert event["schedule"] == "weekly"
        assert event["threshold_keys"] == ["revenue", "units_sold"]
        assert event["recipient_count"] == 1
        assert event["output_format"] == "docx"

        payload_str = str(event)
        assert "should-never-be-logged" not in payload_str
        assert "ops@example.com" not in payload_str
