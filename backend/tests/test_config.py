"""Tests for the Story 2.1 configuration layer.

Covers backend/models/pipeline_config.py and the re-export in
backend/pipeline/config.py: valid load with defaults, every
ConfigurationError path (missing fields, bad cron, bad threshold, bad
email, secrets in YAML, missing/unparseable file), environment-variable
secret sourcing, stateless reload (FR10), and the secret-free
``config_loaded`` structlog event.

All file I/O goes through ``tmp_path`` — the real repo-root config.yaml
is never touched.
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
    ScheduleConfig,
    SmtpSettings,
)

_SMTP_ENV_VARS = ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM"]


@pytest.fixture(autouse=True)
def _clean_smtp_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate every test from ambient SMTP_* variables and any real .env."""
    for var in _SMTP_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def _valid_config_dict() -> dict:
    return {
        "data_sources": ["data/sales.csv"],
        "report_schedule": {"interval": "weekly"},
        "metric_thresholds": {"revenue": 0.15, "units_sold": 0.20},
        "alert_recipients": ["ops@example.com"],
        "output": {"format": "docx", "output_dir": "output/"},
    }


def _write_config(tmp_path: Path, config: dict) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return path


class TestValidLoad:
    def test_valid_config_returns_typed_instance(self, tmp_path: Path) -> None:
        path = _write_config(tmp_path, _valid_config_dict())

        config = PipelineConfig.load(path)

        assert isinstance(config, PipelineConfig)
        assert config.data_sources == [Path("data/sales.csv")]
        assert config.report_schedule.interval == "weekly"
        assert config.report_schedule.cron is None
        assert config.metric_thresholds == {"revenue": 0.15, "units_sold": 0.20}
        assert config.alert_recipients == ["ops@example.com"]
        assert config.output.format == "docx"
        assert config.output.output_dir == Path("output")

    def test_defaults_applied_when_sections_omitted(self, tmp_path: Path) -> None:
        config_dict = _valid_config_dict()
        del config_dict["metric_thresholds"]
        del config_dict["output"]
        path = _write_config(tmp_path, config_dict)

        config = PipelineConfig.load(path)

        assert config.metric_thresholds == {}
        assert config.output.format == "docx"
        assert config.output.output_dir == Path("output")

    def test_threshold_for_falls_back_to_default(self, tmp_path: Path) -> None:
        path = _write_config(tmp_path, _valid_config_dict())

        config = PipelineConfig.load(path)

        assert config.threshold_for("units_sold") == 0.20
        assert config.threshold_for("unlisted_metric") == DEFAULT_THRESHOLD == 0.15

    def test_cron_schedule_accepted(self, tmp_path: Path) -> None:
        config_dict = _valid_config_dict()
        config_dict["report_schedule"] = {"cron": "0 6 * * 1"}
        path = _write_config(tmp_path, config_dict)

        config = PipelineConfig.load(path)

        assert config.report_schedule.cron == "0 6 * * 1"
        assert config.report_schedule.interval is None

    def test_json_config_parses_as_yaml_subset(self, tmp_path: Path) -> None:
        import json

        path = tmp_path / "config.json"
        path.write_text(json.dumps(_valid_config_dict()), encoding="utf-8")

        config = PipelineConfig.load(path)

        assert config.report_schedule.interval == "weekly"

    def test_repo_root_config_yaml_is_valid(self) -> None:
        """The committed example config at repo root must load (AC1)."""
        repo_root_config = Path(__file__).resolve().parents[2] / "config.yaml"

        config = PipelineConfig.load(repo_root_config)

        assert config.data_sources
        assert config.alert_recipients


class TestInvalidConfig:
    def test_missing_required_field_raises_configuration_error(self, tmp_path: Path) -> None:
        config_dict = _valid_config_dict()
        del config_dict["data_sources"]
        path = _write_config(tmp_path, config_dict)

        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(path)

    def test_empty_data_sources_rejected(self, tmp_path: Path) -> None:
        config_dict = _valid_config_dict()
        config_dict["data_sources"] = []
        path = _write_config(tmp_path, config_dict)

        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(path)

    def test_malformed_cron_raises_configuration_error(self, tmp_path: Path) -> None:
        config_dict = _valid_config_dict()
        config_dict["report_schedule"] = {"cron": "not a cron"}
        path = _write_config(tmp_path, config_dict)

        with pytest.raises(ConfigurationError, match="cron"):
            PipelineConfig.load(path)

    def test_interval_and_cron_together_rejected(self, tmp_path: Path) -> None:
        config_dict = _valid_config_dict()
        config_dict["report_schedule"] = {"interval": "daily", "cron": "0 6 * * 1"}
        path = _write_config(tmp_path, config_dict)

        with pytest.raises(ConfigurationError, match="report_schedule"):
            PipelineConfig.load(path)

    def test_unknown_interval_rejected(self, tmp_path: Path) -> None:
        config_dict = _valid_config_dict()
        config_dict["report_schedule"] = {"interval": "hourly"}
        path = _write_config(tmp_path, config_dict)

        with pytest.raises(ConfigurationError, match="interval"):
            PipelineConfig.load(path)

    @pytest.mark.parametrize("bad_threshold", [-0.15, 0, 0.0])
    def test_nonpositive_threshold_rejected(self, tmp_path: Path, bad_threshold: float) -> None:
        config_dict = _valid_config_dict()
        config_dict["metric_thresholds"] = {"revenue": bad_threshold}
        path = _write_config(tmp_path, config_dict)

        with pytest.raises(ConfigurationError, match="metric_thresholds"):
            PipelineConfig.load(path)

    def test_malformed_email_rejected(self, tmp_path: Path) -> None:
        config_dict = _valid_config_dict()
        config_dict["alert_recipients"] = ["not-an-email"]
        path = _write_config(tmp_path, config_dict)

        with pytest.raises(ConfigurationError, match="alert_recipients"):
            PipelineConfig.load(path)

    def test_unknown_top_level_key_rejected(self, tmp_path: Path) -> None:
        config_dict = _valid_config_dict()
        config_dict["metric_treshold"] = {"revenue": 0.15}  # typo'd key
        path = _write_config(tmp_path, config_dict)

        with pytest.raises(ConfigurationError, match="metric_treshold"):
            PipelineConfig.load(path)

    def test_smtp_section_in_yaml_rejected(self, tmp_path: Path) -> None:
        """Secrets must never live in config.yaml (NFR3)."""
        config_dict = _valid_config_dict()
        config_dict["smtp"] = {"password": "hunter2"}
        path = _write_config(tmp_path, config_dict)

        with pytest.raises(ConfigurationError, match="environment variables"):
            PipelineConfig.load(path)

    def test_missing_file_raises_configuration_error(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="not found"):
            PipelineConfig.load(tmp_path / "nope.yaml")

    def test_unparseable_yaml_raises_configuration_error(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("data_sources: [unclosed", encoding="utf-8")

        with pytest.raises(ConfigurationError, match="not valid YAML"):
            PipelineConfig.load(path)

    def test_non_mapping_yaml_raises_configuration_error(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("- just\n- a\n- list\n", encoding="utf-8")

        with pytest.raises(ConfigurationError, match="mapping"):
            PipelineConfig.load(path)

    def test_validation_error_never_escapes(self, tmp_path: Path) -> None:
        from pydantic import ValidationError

        path = _write_config(tmp_path, {"data_sources": ["x.csv"]})

        try:
            PipelineConfig.load(path)
        except ConfigurationError:
            pass
        except ValidationError:  # pragma: no cover - the failure being asserted
            pytest.fail("pydantic ValidationError escaped PipelineConfig.load()")
        else:  # pragma: no cover
            pytest.fail("invalid config did not raise")


class TestEnvSecrets:
    def test_smtp_secrets_sourced_from_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = _write_config(tmp_path, _valid_config_dict())
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "2525")
        monkeypatch.setenv("SMTP_USERNAME", "mailer")
        monkeypatch.setenv("SMTP_PASSWORD", "s3cret-value")
        monkeypatch.setenv("SMTP_FROM", "alerts@example.com")

        config = PipelineConfig.load(path)

        assert config.smtp.host == "smtp.example.com"
        assert config.smtp.port == 2525
        assert config.smtp.username == "mailer"
        assert config.smtp.password == "s3cret-value"
        assert config.smtp.from_address == "alerts@example.com"
        # The secret exists only in env — never in the YAML on disk.
        assert "s3cret-value" not in path.read_text(encoding="utf-8")

    def test_smtp_defaults_when_env_absent(self, tmp_path: Path) -> None:
        path = _write_config(tmp_path, _valid_config_dict())

        config = PipelineConfig.load(path)

        assert config.smtp == SmtpSettings()
        assert config.smtp.port == 587
        assert config.smtp.password is None


class TestReload:
    def test_reload_reflects_on_disk_changes(self, tmp_path: Path) -> None:
        """FR10: load() is stateless — edits apply on the next call."""
        config_dict = _valid_config_dict()
        path = _write_config(tmp_path, config_dict)
        first = PipelineConfig.load(path)
        assert first.threshold_for("revenue") == 0.15

        config_dict["metric_thresholds"]["revenue"] = 0.25
        config_dict["report_schedule"] = {"interval": "daily"}
        config_dict["alert_recipients"].append("oncall@example.com")
        _write_config(tmp_path, config_dict)
        second = PipelineConfig.load(path)

        assert second.threshold_for("revenue") == 0.25
        assert second.report_schedule.interval == "daily"
        assert len(second.alert_recipients) == 2
        # The previously returned instance is untouched (no shared cache).
        assert first.threshold_for("revenue") == 0.15


class TestObservability:
    def test_config_loaded_event_emitted_without_secrets(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = _write_config(tmp_path, _valid_config_dict())
        monkeypatch.setenv("SMTP_PASSWORD", "s3cret-value")
        monkeypatch.setenv("SMTP_USERNAME", "mailer-user")

        with structlog.testing.capture_logs() as logs:
            PipelineConfig.load(path)

        events = [entry for entry in logs if entry["event"] == "config_loaded"]
        assert len(events) == 1
        event = events[0]
        assert event["schedule"] == "weekly"
        assert event["threshold_keys"] == ["revenue", "units_sold"]
        assert event["recipient_count"] == 1
        assert event["output_format"] == "docx"
        assert event["data_source_count"] == 1
        # No secret values and no recipient addresses anywhere in the payload.
        payload = repr(event)
        assert "s3cret-value" not in payload
        assert "mailer-user" not in payload
        assert "ops@example.com" not in payload


class TestReExport:
    def test_pipeline_config_reexported_from_pipeline_package(self) -> None:
        """Both import paths must resolve to the one Pydantic model."""
        from backend.pipeline.config import PipelineConfig as ReExported

        assert ReExported is PipelineConfig

    def test_schedule_config_describe(self) -> None:
        assert ScheduleConfig(interval="daily").describe() == "daily"
        assert ScheduleConfig(cron="0 6 * * 1").describe() == "cron:0 6 * * 1"
