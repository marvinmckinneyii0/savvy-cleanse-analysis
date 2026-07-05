"""Tests for the Story 2.1 configuration layer.

Covers :mod:`backend.models.pipeline_config` and the re-export through
:mod:`backend.pipeline.config`: valid loads with defaults, every
invalid-config path raising :class:`ConfigurationError` (never a bare
pydantic ``ValidationError``), env-sourced secrets, stateless reload,
and the secret-free ``config_loaded`` log event.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import structlog
from pydantic import ValidationError

from backend.errors.exceptions import ConfigurationError
from backend.models.pipeline_config import (
    DEFAULT_THRESHOLD,
    PipelineConfig,
    SmtpSettings,
)

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

MINIMAL_CONFIG = """\
data_sources:
  - data/sales.csv
report_schedule:
  interval: daily
"""


def write_config(tmp_path: Path, body: str) -> Path:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(body, encoding="utf-8")
    return config_path


class TestValidLoad:
    def test_valid_config_returns_typed_instance(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))

        assert isinstance(config, PipelineConfig)
        assert config.data_sources == [Path("data/sales.csv")]
        assert config.report_schedule.interval == "weekly"
        assert config.report_schedule.cron is None
        assert config.metric_thresholds == {"revenue": 0.15, "units_sold": 0.20}
        assert config.alert_recipients == ["ops@example.com"]
        assert config.output.format == "docx"
        assert config.output.output_dir == Path("output/")

    def test_defaults_applied_on_minimal_config(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, MINIMAL_CONFIG))

        assert config.metric_thresholds == {}
        assert config.threshold_for("anything") == DEFAULT_THRESHOLD == 0.15
        assert config.alert_recipients == []
        assert config.output.format == "docx"
        assert config.output.output_dir == Path("output/")

    def test_threshold_for_prefers_explicit_entry(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))

        assert config.threshold_for("units_sold") == 0.20
        assert config.threshold_for("not_configured") == DEFAULT_THRESHOLD

    def test_cron_schedule_accepted(self, tmp_path: Path) -> None:
        body = MINIMAL_CONFIG.replace("interval: daily", 'cron: "0 6 * * 1"')
        config = PipelineConfig.load(write_config(tmp_path, body))

        assert config.report_schedule.cron == "0 6 * * 1"
        assert config.report_schedule.describe() == "cron:0 6 * * 1"

    def test_json_config_parses_as_yaml_subset(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config_path.write_text(
            '{"data_sources": ["data/sales.csv"],'
            ' "report_schedule": {"interval": "monthly"}}',
            encoding="utf-8",
        )
        config = PipelineConfig.load(config_path)

        assert config.report_schedule.interval == "monthly"

    def test_reexport_through_pipeline_config_module(self) -> None:
        from backend.pipeline.config import PipelineConfig as ReExported

        assert ReExported is PipelineConfig


class TestInvalidConfig:
    def test_missing_required_field_raises_configuration_error(self, tmp_path: Path) -> None:
        body = "report_schedule:\n  interval: daily\n"  # no data_sources
        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(write_config(tmp_path, body))

    def test_missing_file_raises_configuration_error(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="not found"):
            PipelineConfig.load(tmp_path / "nope.yaml")

    def test_malformed_yaml_raises_configuration_error(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="not valid YAML"):
            PipelineConfig.load(write_config(tmp_path, "data_sources: [unclosed"))

    def test_non_mapping_yaml_raises_configuration_error(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="mapping"):
            PipelineConfig.load(write_config(tmp_path, "- just\n- a\n- list\n"))

    def test_invalid_cron_raises_configuration_error(self, tmp_path: Path) -> None:
        body = MINIMAL_CONFIG.replace("interval: daily", 'cron: "not a cron"')
        with pytest.raises(ConfigurationError, match="cron"):
            PipelineConfig.load(write_config(tmp_path, body))

    def test_interval_and_cron_together_raise(self, tmp_path: Path) -> None:
        body = MINIMAL_CONFIG + '  cron: "0 6 * * 1"\n'
        with pytest.raises(ConfigurationError, match="exactly one"):
            PipelineConfig.load(write_config(tmp_path, body))

    def test_negative_threshold_raises_configuration_error(self, tmp_path: Path) -> None:
        body = MINIMAL_CONFIG + "metric_thresholds:\n  revenue: -0.1\n"
        with pytest.raises(ConfigurationError, match="metric_thresholds.revenue"):
            PipelineConfig.load(write_config(tmp_path, body))

    def test_zero_threshold_raises_configuration_error(self, tmp_path: Path) -> None:
        body = MINIMAL_CONFIG + "metric_thresholds:\n  revenue: 0\n"
        with pytest.raises(ConfigurationError, match="must be > 0"):
            PipelineConfig.load(write_config(tmp_path, body))

    def test_malformed_email_raises_configuration_error(self, tmp_path: Path) -> None:
        body = MINIMAL_CONFIG + "alert_recipients:\n  - not-an-email\n"
        with pytest.raises(ConfigurationError, match="alert_recipients"):
            PipelineConfig.load(write_config(tmp_path, body))

    def test_empty_data_sources_raises_configuration_error(self, tmp_path: Path) -> None:
        body = "data_sources: []\nreport_schedule:\n  interval: daily\n"
        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(write_config(tmp_path, body))

    def test_unknown_top_level_key_raises_configuration_error(self, tmp_path: Path) -> None:
        body = MINIMAL_CONFIG + "metric_treshholds: {}\n"  # typo
        with pytest.raises(ConfigurationError, match="metric_treshholds"):
            PipelineConfig.load(write_config(tmp_path, body))

    def test_validation_error_never_escapes(self, tmp_path: Path) -> None:
        body = MINIMAL_CONFIG + "metric_thresholds:\n  revenue: -1\n"
        try:
            PipelineConfig.load(write_config(tmp_path, body))
        except ConfigurationError:
            pass
        except ValidationError:  # pragma: no cover - the regression this guards
            pytest.fail("pydantic ValidationError escaped PipelineConfig.load()")
        else:  # pragma: no cover
            pytest.fail("invalid config did not raise")


class TestSecretsFromEnv:
    def test_smtp_sourced_from_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "2525")
        monkeypatch.setenv("SMTP_USERNAME", "mailer")
        monkeypatch.setenv("SMTP_PASSWORD", "s3cr3t-value")
        monkeypatch.setenv("SMTP_FROM", "alerts@example.com")

        config_path = write_config(tmp_path, VALID_CONFIG)
        config = PipelineConfig.load(config_path)

        assert config.smtp.host == "smtp.example.com"
        assert config.smtp.port == 2525
        assert config.smtp.username == "mailer"
        assert config.smtp.password == "s3cr3t-value"
        assert config.smtp.from_address == "alerts@example.com"
        # The secret exists only in env — never on disk.
        assert "s3cr3t-value" not in config_path.read_text(encoding="utf-8")

    def test_smtp_defaults_when_env_unset(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        for var in ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM"):
            monkeypatch.delenv(var, raising=False)

        config = PipelineConfig.load(write_config(tmp_path, MINIMAL_CONFIG))

        assert config.smtp == SmtpSettings()
        assert config.smtp.port == 587

    def test_smtp_key_in_yaml_rejected(self, tmp_path: Path) -> None:
        body = MINIMAL_CONFIG + "smtp:\n  password: leaked\n"
        with pytest.raises(ConfigurationError, match="environment variables"):
            PipelineConfig.load(write_config(tmp_path, body))


class TestReload:
    def test_reload_reflects_on_disk_changes(self, tmp_path: Path) -> None:
        config_path = write_config(tmp_path, VALID_CONFIG)
        first = PipelineConfig.load(config_path)
        assert first.threshold_for("revenue") == 0.15

        config_path.write_text(
            VALID_CONFIG.replace("revenue: 0.15", "revenue: 0.30").replace(
                "interval: weekly", "interval: daily"
            ),
            encoding="utf-8",
        )
        second = PipelineConfig.load(config_path)

        assert second.threshold_for("revenue") == 0.30
        assert second.report_schedule.interval == "daily"
        # The first instance is untouched — load() returns fresh objects.
        assert first.threshold_for("revenue") == 0.15


class TestObservability:
    def test_config_loaded_event_emitted_without_secrets(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_PASSWORD", "s3cr3t-value")
        monkeypatch.setenv("SMTP_USERNAME", "mailer-user")

        with structlog.testing.capture_logs() as logs:
            PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))

        events = [entry for entry in logs if entry["event"] == "config_loaded"]
        assert len(events) == 1
        payload = events[0]

        assert payload["schedule"] == "weekly"
        assert payload["threshold_keys"] == ["revenue", "units_sold"]
        assert payload["recipient_count"] == 1
        assert payload["output_format"] == "docx"
        assert payload["data_source_count"] == 1

        # No secrets and no full recipient addresses anywhere in the payload.
        rendered = repr(payload)
        assert "s3cr3t-value" not in rendered
        assert "mailer-user" not in rendered
        assert "ops@example.com" not in rendered
