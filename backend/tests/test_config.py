"""Tests for the configuration layer (Story 2.1).

Covers backend/models/pipeline_config.py and the re-export in
backend/pipeline/config.py: valid loads with defaults, every
ConfigurationError path (missing file, bad YAML, missing fields, bad
cron, non-positive thresholds, malformed emails, smtp-in-yaml), env
sourcing of SMTP secrets, stateless reload, and the config_loaded
observability event.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import structlog
import yaml

from backend.errors.exceptions import ConfigurationError
from backend.models.pipeline_config import (
    DEFAULT_THRESHOLD,
    PipelineConfig,
    SmtpSettings,
)


VALID_CONFIG: dict = {
    "data_sources": ["data/sales.csv"],
    "report_schedule": {"interval": "weekly"},
    "metric_thresholds": {"revenue": 0.15, "units_sold": 0.20},
    "alert_recipients": ["ops@example.com"],
    "output": {"format": "docx", "output_dir": "output/"},
}


def write_config(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def _clear_smtp_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate every test from ambient SMTP_* variables and any real .env."""
    for var in ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM"):
        monkeypatch.delenv(var, raising=False)


class TestValidLoad:
    def test_valid_config_returns_typed_instance(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))

        assert isinstance(config, PipelineConfig)
        assert config.data_sources == [Path("data/sales.csv")]
        assert config.report_schedule.interval == "weekly"
        assert config.report_schedule.cron is None
        assert config.metric_thresholds == {"revenue": 0.15, "units_sold": 0.20}
        assert config.alert_recipients == ["ops@example.com"]

    def test_defaults_applied(self, tmp_path: Path) -> None:
        minimal = {
            "data_sources": ["data/"],
            "report_schedule": {"interval": "daily"},
        }
        config = PipelineConfig.load(write_config(tmp_path, minimal))

        assert config.output.format == "docx"
        assert config.output.output_dir == Path("output")
        assert config.metric_thresholds == {}
        assert config.alert_recipients == []
        assert config.threshold_for("anything") == DEFAULT_THRESHOLD

    def test_threshold_for_prefers_explicit_entry(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))

        assert config.threshold_for("units_sold") == 0.20
        assert config.threshold_for("not_configured") == DEFAULT_THRESHOLD

    def test_cron_schedule_accepted(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "report_schedule": {"cron": "0 6 * * 1"}}
        config = PipelineConfig.load(write_config(tmp_path, data))

        assert config.report_schedule.cron == "0 6 * * 1"
        assert config.report_schedule.interval is None

    def test_json_config_parses_via_safe_load(self, tmp_path: Path) -> None:
        # JSON is a strict subset of YAML — same loader, no separate branch.
        import json

        path = tmp_path / "config.json"
        path.write_text(json.dumps(VALID_CONFIG), encoding="utf-8")

        config = PipelineConfig.load(path)
        assert config.report_schedule.interval == "weekly"

    def test_pipeline_config_reexport_is_same_class(self) -> None:
        from backend.pipeline.config import PipelineConfig as ReExported

        assert ReExported is PipelineConfig


class TestInvalidConfig:
    def test_missing_file_raises_configuration_error(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="not found"):
            PipelineConfig.load(tmp_path / "nope.yaml")

    def test_malformed_yaml_raises_configuration_error(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("data_sources: [unclosed", encoding="utf-8")

        with pytest.raises(ConfigurationError, match="not valid YAML"):
            PipelineConfig.load(path)

    def test_non_mapping_top_level_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("- just\n- a\n- list\n", encoding="utf-8")

        with pytest.raises(ConfigurationError, match="mapping"):
            PipelineConfig.load(path)

    def test_missing_required_field_raises_configuration_error(self, tmp_path: Path) -> None:
        data = {k: v for k, v in VALID_CONFIG.items() if k != "data_sources"}

        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_empty_data_sources_raises(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "data_sources": []}

        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_invalid_cron_raises_configuration_error(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "report_schedule": {"cron": "not a cron"}}

        with pytest.raises(ConfigurationError, match="cron"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_interval_and_cron_together_raise(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "report_schedule": {"interval": "daily", "cron": "0 6 * * 1"}}

        with pytest.raises(ConfigurationError, match="exactly one"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_unknown_interval_raises(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "report_schedule": {"interval": "hourly"}}

        with pytest.raises(ConfigurationError, match="interval"):
            PipelineConfig.load(write_config(tmp_path, data))

    @pytest.mark.parametrize("bad_threshold", [-0.15, 0, 0.0])
    def test_non_positive_threshold_raises(self, tmp_path: Path, bad_threshold: float) -> None:
        data = {**VALID_CONFIG, "metric_thresholds": {"revenue": bad_threshold}}

        with pytest.raises(ConfigurationError, match="revenue"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_malformed_email_raises_configuration_error(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "alert_recipients": ["not-an-email"]}

        with pytest.raises(ConfigurationError, match="alert_recipients"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_validation_error_never_escapes(self, tmp_path: Path) -> None:
        import pydantic

        data = {**VALID_CONFIG, "alert_recipients": ["not-an-email"]}
        with pytest.raises(ConfigurationError) as excinfo:
            PipelineConfig.load(write_config(tmp_path, data))
        assert not isinstance(excinfo.value, pydantic.ValidationError)


class TestSecretsFromEnv:
    def test_smtp_sourced_from_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "2525")
        monkeypatch.setenv("SMTP_USERNAME", "mailer")
        monkeypatch.setenv("SMTP_PASSWORD", "s3cr3t-value")
        monkeypatch.setenv("SMTP_FROM", "alerts@example.com")

        path = write_config(tmp_path, VALID_CONFIG)
        config = PipelineConfig.load(path)

        assert config.smtp.host == "smtp.example.com"
        assert config.smtp.port == 2525
        assert config.smtp.username == "mailer"
        assert config.smtp.password == "s3cr3t-value"
        assert config.smtp.from_addr == "alerts@example.com"
        # The secret must not exist anywhere in the YAML on disk.
        assert "s3cr3t-value" not in path.read_text(encoding="utf-8")

    def test_non_numeric_smtp_port_raises_configuration_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_PORT", "not-a-port")

        with pytest.raises(ConfigurationError, match="port"):
            PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))

    def test_smtp_defaults_when_env_unset(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))

        assert config.smtp == SmtpSettings()
        assert config.smtp.port == 587

    def test_smtp_block_in_yaml_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "smtp": {"password": "leaked"}}

        with pytest.raises(ConfigurationError, match="environment variables only"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_repo_root_config_yaml_contains_no_smtp(self) -> None:
        """The committed config.yaml must never grow a secrets section."""
        repo_config = Path(__file__).resolve().parents[2] / "config.yaml"
        data = yaml.safe_load(repo_config.read_text(encoding="utf-8"))
        assert "smtp" not in data
        assert not any("password" in key.lower() for key in data)


class TestReload:
    def test_reload_reflects_on_disk_changes(self, tmp_path: Path) -> None:
        path = write_config(tmp_path, VALID_CONFIG)
        first = PipelineConfig.load(path)
        assert first.metric_thresholds["revenue"] == 0.15
        assert first.report_schedule.interval == "weekly"

        updated = {
            **VALID_CONFIG,
            "metric_thresholds": {"revenue": 0.30},
            "report_schedule": {"interval": "daily"},
            "alert_recipients": ["ops@example.com", "oncall@example.com"],
        }
        write_config(tmp_path, updated)

        second = PipelineConfig.load(path)
        assert second.metric_thresholds["revenue"] == 0.30
        assert second.report_schedule.interval == "daily"
        assert len(second.alert_recipients) == 2
        # The first instance is untouched — load() returns fresh objects.
        assert first.metric_thresholds["revenue"] == 0.15


class TestObservability:
    def test_config_loaded_event_emitted_without_secrets(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_USERNAME", "mailer-user")
        monkeypatch.setenv("SMTP_PASSWORD", "hunter2-secret")

        with structlog.testing.capture_logs() as logs:
            PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))

        events = [entry for entry in logs if entry["event"] == "config_loaded"]
        assert len(events) == 1
        event = events[0]

        assert event["schedule"] == "weekly"
        assert event["threshold_keys"] == ["revenue", "units_sold"]
        assert event["recipient_count"] == 1
        assert event["output_format"] == "docx"

        payload = repr(event)
        assert "hunter2-secret" not in payload
        assert "mailer-user" not in payload
        # Recipient addresses are PII-adjacent — count only, never the list.
        assert "ops@example.com" not in payload
