"""Tests for the Story 2.1 configuration layer.

Covers ``backend/models/pipeline_config.py`` and the re-export in
``backend/pipeline/config.py``: valid load with defaults, every AC2
rejection path (missing field, bad cron, non-positive threshold, bad
email) raising :class:`ConfigurationError` (never a bare Pydantic
``ValidationError``), env-only SMTP secrets, stateless reload, and the
secret-free ``config_loaded`` log event.

All config files are written under ``tmp_path`` — the real repo-root
``config.yaml`` is only ever *read* (default-path test), never mutated.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import structlog
import yaml
from pydantic import ValidationError

from backend.errors.exceptions import ConfigurationError
from backend.models.pipeline_config import (
    DEFAULT_THRESHOLD,
    PipelineConfig,
    ScheduleConfig,
    SmtpSettings,
)

SECRET_SENTINEL = "s3cr3t-smtp-password"  # noqa: S105 — test-only sentinel

VALID_CONFIG: dict = {
    "data_sources": ["data/sales.csv"],
    "report_schedule": {"interval": "weekly"},
    "metric_thresholds": {"revenue": 0.15, "units_sold": 0.20},
    "alert_recipients": ["ops@example.com"],
    "output": {"format": "docx", "output_dir": "output/"},
}


@pytest.fixture(autouse=True)
def _clean_smtp_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate every test from real SMTP_* env vars (and any local .env)."""
    for var in ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM"):
        monkeypatch.delenv(var, raising=False)


def write_config(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


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
        assert config.output.output_dir == Path("output")

    def test_defaults_applied_when_sections_omitted(self, tmp_path: Path) -> None:
        minimal = {
            "data_sources": ["data/"],
            "report_schedule": {"interval": "daily"},
        }
        config = PipelineConfig.load(write_config(tmp_path, minimal))

        assert config.output.format == "docx"
        assert config.output.output_dir == Path("output")
        assert config.metric_thresholds == {}
        assert config.threshold_for("anything") == DEFAULT_THRESHOLD == 0.15
        assert config.alert_recipients == []

    def test_threshold_for_prefers_explicit_entry(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))

        assert config.threshold_for("units_sold") == 0.20
        assert config.threshold_for("not_configured") == DEFAULT_THRESHOLD

    def test_cron_schedule_accepted(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "report_schedule": {"cron": "0 6 * * 1"}}
        config = PipelineConfig.load(write_config(tmp_path, data))

        assert config.report_schedule.cron == "0 6 * * 1"
        assert config.report_schedule.interval is None

    def test_default_path_loads_repo_root_config(self) -> None:
        # Read-only check of the shipped config.yaml; nothing is written.
        config = PipelineConfig.load()

        assert isinstance(config, PipelineConfig)
        assert config.data_sources

    def test_reexport_path_is_same_class(self) -> None:
        from backend.pipeline.config import PipelineConfig as ReExported

        assert ReExported is PipelineConfig


class TestInvalidConfig:
    def test_missing_file_raises_configuration_error(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="not found"):
            PipelineConfig.load(tmp_path / "nope.yaml")

    def test_malformed_yaml_raises_configuration_error(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("data_sources: [unclosed", encoding="utf-8")

        with pytest.raises(ConfigurationError, match="Malformed YAML"):
            PipelineConfig.load(path)

    def test_non_mapping_root_raises_configuration_error(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("- just\n- a\n- list\n", encoding="utf-8")

        with pytest.raises(ConfigurationError, match="mapping"):
            PipelineConfig.load(path)

    def test_missing_required_field_names_it(self, tmp_path: Path) -> None:
        data = {k: v for k, v in VALID_CONFIG.items() if k != "data_sources"}

        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_empty_data_sources_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "data_sources": []}

        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_invalid_cron_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "report_schedule": {"cron": "not a cron"}}

        with pytest.raises(ConfigurationError, match="cron"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_interval_and_cron_together_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "report_schedule": {"interval": "daily", "cron": "0 6 * * 1"}}

        with pytest.raises(ConfigurationError, match="exactly one"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_schedule_with_neither_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "report_schedule": {}}

        with pytest.raises(ConfigurationError, match="exactly one"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_unknown_interval_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "report_schedule": {"interval": "hourly"}}

        with pytest.raises(ConfigurationError, match="interval"):
            PipelineConfig.load(write_config(tmp_path, data))

    @pytest.mark.parametrize("bad_threshold", [-0.15, 0.0, 0])
    def test_non_positive_threshold_rejected(self, tmp_path: Path, bad_threshold: float) -> None:
        data = {**VALID_CONFIG, "metric_thresholds": {"revenue": bad_threshold}}

        with pytest.raises(ConfigurationError, match="metric_thresholds"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_malformed_email_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "alert_recipients": ["not-an-email"]}

        with pytest.raises(ConfigurationError, match="alert_recipients"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_invalid_output_format_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "output": {"format": "xlsx"}}

        with pytest.raises(ConfigurationError, match="output"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_unknown_top_level_key_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "metric_treshholds": {"revenue": 0.1}}  # typo on purpose

        with pytest.raises(ConfigurationError, match="metric_treshholds"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_validation_error_never_escapes(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "alert_recipients": ["not-an-email"]}
        path = write_config(tmp_path, data)

        try:
            PipelineConfig.load(path)
        except ConfigurationError:
            pass
        except ValidationError:  # pragma: no cover — the regression this guards
            pytest.fail("Pydantic ValidationError escaped PipelineConfig.load()")
        else:
            pytest.fail("invalid config did not raise")


class TestSecretsFromEnv:
    def test_smtp_sourced_from_env_not_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "2525")
        monkeypatch.setenv("SMTP_USERNAME", "mailer")
        monkeypatch.setenv("SMTP_PASSWORD", SECRET_SENTINEL)
        monkeypatch.setenv("SMTP_FROM", "alerts@example.com")

        path = write_config(tmp_path, VALID_CONFIG)
        config = PipelineConfig.load(path)

        assert config.smtp.host == "smtp.example.com"
        assert config.smtp.port == 2525
        assert config.smtp.username == "mailer"
        assert config.smtp.password is not None
        assert config.smtp.password.get_secret_value() == SECRET_SENTINEL
        assert config.smtp.from_addr == "alerts@example.com"
        # The secret exists only in env — never in the YAML on disk.
        assert SECRET_SENTINEL not in path.read_text(encoding="utf-8")

    def test_smtp_defaults_when_env_unset(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))

        assert config.smtp.host is None
        assert config.smtp.port == 587
        assert config.smtp.password is None

    def test_smtp_section_in_yaml_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "smtp": {"password": "oops"}}

        with pytest.raises(ConfigurationError, match="smtp"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_malformed_smtp_port_env_raises_configuration_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_PORT", "not-a-port")

        with pytest.raises(ConfigurationError, match="smtp.port"):
            PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))

    def test_password_repr_is_masked(self) -> None:
        settings = SmtpSettings(password=SECRET_SENTINEL)

        assert SECRET_SENTINEL not in repr(settings)
        assert SECRET_SENTINEL not in str(settings)


class TestReload:
    def test_reload_reflects_on_disk_changes(self, tmp_path: Path) -> None:
        path = write_config(tmp_path, VALID_CONFIG)
        first = PipelineConfig.load(path)
        assert first.threshold_for("revenue") == 0.15
        assert first.report_schedule.interval == "weekly"

        updated = {
            **VALID_CONFIG,
            "metric_thresholds": {"revenue": 0.30},
            "report_schedule": {"interval": "daily"},
            "alert_recipients": ["ops@example.com", "oncall@example.com"],
        }
        write_config(tmp_path, updated)
        second = PipelineConfig.load(path)

        assert second.threshold_for("revenue") == 0.30
        assert second.report_schedule.interval == "daily"
        assert len(second.alert_recipients) == 2
        # First instance is untouched — load() returns fresh objects.
        assert first.threshold_for("revenue") == 0.15


class TestObservability:
    def test_config_loaded_event_emitted_without_secrets(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_USERNAME", "mailer")
        monkeypatch.setenv("SMTP_PASSWORD", SECRET_SENTINEL)
        path = write_config(tmp_path, VALID_CONFIG)

        with structlog.testing.capture_logs() as logs:
            PipelineConfig.load(path)

        events = [entry for entry in logs if entry["event"] == "config_loaded"]
        assert len(events) == 1
        event = events[0]

        assert event["schedule"] == "interval:weekly"
        assert event["threshold_keys"] == ["revenue", "units_sold"]
        assert event["recipient_count"] == 1
        assert event["output_format"] == "docx"

        payload = repr(logs)
        assert SECRET_SENTINEL not in payload
        # Recipient addresses are PII-adjacent — count only, never the list.
        assert "ops@example.com" not in payload


def test_schedule_describe_shapes() -> None:
    assert ScheduleConfig(interval="monthly").describe() == "interval:monthly"
    assert ScheduleConfig(cron="0 6 * * 1").describe() == "cron:0 6 * * 1"
