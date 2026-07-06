"""Tests for the Story 2.1 configuration layer.

Covers :mod:`backend.models.pipeline_config` and the re-export in
:mod:`backend.pipeline.config`: valid loads and defaults, every invalid-value
path raising :class:`ConfigurationError` (never a bare ``ValidationError``),
env-only secret sourcing, stateless reload, and the ``config_loaded``
structlog event carrying no secrets.

All config files are written to ``tmp_path`` — the real repo-root
``config.yaml`` is never touched.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import structlog

from backend.errors.exceptions import ConfigurationError
from backend.models.pipeline_config import (
    DEFAULT_THRESHOLD,
    PipelineConfig,
    ScheduleConfig,
)

VALID_YAML = """\
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

MINIMAL_YAML = """\
data_sources:
  - data/sales.csv
report_schedule:
  interval: daily
alert_recipients:
  - ops@example.com
"""


@pytest.fixture(autouse=True)
def _clean_smtp_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate every test from ambient SMTP_* env vars and any local .env."""
    for var in ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM"):
        monkeypatch.delenv(var, raising=False)


def write_config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(content, encoding="utf-8")
    return path


class TestValidLoad:
    def test_valid_config_returns_typed_instance(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, VALID_YAML))

        assert isinstance(config, PipelineConfig)
        assert config.data_sources == [Path("data/sales.csv")]
        assert config.report_schedule.interval == "weekly"
        assert config.report_schedule.cron is None
        assert config.metric_thresholds == {"revenue": 0.15, "units_sold": 0.20}
        assert config.alert_recipients == ["ops@example.com"]
        assert config.output.format == "docx"
        assert config.output.output_dir == Path("output")

    def test_defaults_applied_for_omitted_sections(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, MINIMAL_YAML))

        assert config.threshold_for("revenue") == DEFAULT_THRESHOLD == 0.15
        assert config.metric_thresholds == {}
        assert config.output.format == "docx"
        assert config.output.output_dir == Path("output")

    def test_threshold_for_prefers_explicit_entry(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, VALID_YAML))

        assert config.threshold_for("units_sold") == 0.20
        assert config.threshold_for("unlisted_metric") == DEFAULT_THRESHOLD

    def test_cron_schedule_accepted(self, tmp_path: Path) -> None:
        yaml_text = MINIMAL_YAML.replace("interval: daily", 'cron: "0 6 * * 1"')
        config = PipelineConfig.load(write_config(tmp_path, yaml_text))

        assert config.report_schedule.cron == "0 6 * * 1"
        assert config.report_schedule.interval is None

    def test_json_config_is_valid_yaml_subset(self, tmp_path: Path) -> None:
        payload = {
            "data_sources": ["data/sales.csv"],
            "report_schedule": {"interval": "monthly"},
            "alert_recipients": ["ops@example.com"],
        }
        path = tmp_path / "config.json"
        path.write_text(json.dumps(payload), encoding="utf-8")

        config = PipelineConfig.load(path)
        assert config.report_schedule.interval == "monthly"

    def test_reexport_via_pipeline_config_module(self) -> None:
        from backend.pipeline.config import PipelineConfig as ReExported

        assert ReExported is PipelineConfig


class TestInvalidConfig:
    def test_missing_file_raises_configuration_error(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="not found"):
            PipelineConfig.load(tmp_path / "does-not-exist.yaml")

    def test_malformed_yaml_raises_configuration_error(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="not valid YAML"):
            PipelineConfig.load(write_config(tmp_path, "data_sources: [unclosed"))

    def test_non_mapping_yaml_raises_configuration_error(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="mapping"):
            PipelineConfig.load(write_config(tmp_path, "- just\n- a\n- list\n"))

    def test_missing_required_field_names_the_field(self, tmp_path: Path) -> None:
        yaml_text = MINIMAL_YAML.replace("data_sources:\n  - data/sales.csv\n", "")
        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(write_config(tmp_path, yaml_text))

    def test_empty_data_sources_rejected(self, tmp_path: Path) -> None:
        yaml_text = MINIMAL_YAML.replace("  - data/sales.csv\n", "  []\n", 1)
        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(write_config(tmp_path, yaml_text))

    def test_invalid_cron_raises_configuration_error(self, tmp_path: Path) -> None:
        yaml_text = MINIMAL_YAML.replace("interval: daily", 'cron: "not a cron"')
        with pytest.raises(ConfigurationError, match="cron"):
            PipelineConfig.load(write_config(tmp_path, yaml_text))

    def test_both_interval_and_cron_rejected(self, tmp_path: Path) -> None:
        yaml_text = MINIMAL_YAML.replace(
            "interval: daily", 'interval: daily\n  cron: "0 6 * * 1"'
        )
        with pytest.raises(ConfigurationError, match="exactly one"):
            PipelineConfig.load(write_config(tmp_path, yaml_text))

    def test_unknown_interval_rejected(self, tmp_path: Path) -> None:
        yaml_text = MINIMAL_YAML.replace("interval: daily", "interval: hourly")
        with pytest.raises(ConfigurationError, match="interval"):
            PipelineConfig.load(write_config(tmp_path, yaml_text))

    @pytest.mark.parametrize("bad_threshold", ["-0.1", "0", "0.0"])
    def test_nonpositive_threshold_rejected(self, tmp_path: Path, bad_threshold: str) -> None:
        yaml_text = MINIMAL_YAML + f"metric_thresholds:\n  revenue: {bad_threshold}\n"
        with pytest.raises(ConfigurationError, match="must be > 0"):
            PipelineConfig.load(write_config(tmp_path, yaml_text))

    def test_malformed_email_rejected(self, tmp_path: Path) -> None:
        yaml_text = MINIMAL_YAML.replace("ops@example.com", "not-an-email")
        with pytest.raises(ConfigurationError, match="alert_recipients"):
            PipelineConfig.load(write_config(tmp_path, yaml_text))

    def test_unknown_top_level_key_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="data_source"):
            PipelineConfig.load(write_config(tmp_path, MINIMAL_YAML + "data_source: typo\n"))

    def test_validation_error_never_escapes(self, tmp_path: Path) -> None:
        from pydantic import ValidationError

        yaml_text = MINIMAL_YAML.replace("ops@example.com", "not-an-email")
        try:
            PipelineConfig.load(write_config(tmp_path, yaml_text))
        except ConfigurationError:
            pass
        except ValidationError:  # pragma: no cover — the regression this guards
            pytest.fail("ValidationError escaped PipelineConfig.load() uncaught")

    def test_bad_config_error_omits_input_values(self, tmp_path: Path) -> None:
        yaml_text = MINIMAL_YAML.replace("ops@example.com", "hunter2-secretvalue")
        with pytest.raises(ConfigurationError) as excinfo:
            PipelineConfig.load(write_config(tmp_path, yaml_text))
        assert "hunter2-secretvalue" not in str(excinfo.value)


class TestSecrets:
    def test_smtp_sourced_from_env_only(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "2525")
        monkeypatch.setenv("SMTP_USERNAME", "mailer")
        monkeypatch.setenv("SMTP_PASSWORD", "s3cret-value")
        monkeypatch.setenv("SMTP_FROM", "alerts@example.com")

        path = write_config(tmp_path, VALID_YAML)
        config = PipelineConfig.load(path)

        assert config.smtp.host == "smtp.example.com"
        assert config.smtp.port == 2525
        assert config.smtp.username == "mailer"
        assert config.smtp.password == "s3cret-value"
        assert config.smtp.from_addr == "alerts@example.com"
        # The secret exists in env only — never on disk.
        assert "s3cret-value" not in path.read_text(encoding="utf-8")

    def test_smtp_defaults_when_env_unset(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, VALID_YAML))

        assert config.smtp.host is None
        assert config.smtp.port == 587
        assert config.smtp.password is None

    def test_smtp_block_in_yaml_rejected(self, tmp_path: Path) -> None:
        yaml_text = MINIMAL_YAML + "smtp:\n  password: never-do-this\n"
        with pytest.raises(ConfigurationError, match="environment variables"):
            PipelineConfig.load(write_config(tmp_path, yaml_text))

    def test_non_numeric_smtp_port_raises_configuration_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_PORT", "not-a-port")
        with pytest.raises(ConfigurationError, match="SMTP"):
            PipelineConfig.load(write_config(tmp_path, VALID_YAML))


class TestReload:
    def test_reload_reflects_on_disk_changes(self, tmp_path: Path) -> None:
        path = write_config(tmp_path, VALID_YAML)
        first = PipelineConfig.load(path)
        assert first.threshold_for("revenue") == 0.15
        assert first.report_schedule.interval == "weekly"

        path.write_text(
            VALID_YAML.replace("revenue: 0.15", "revenue: 0.30").replace(
                "interval: weekly", "interval: daily"
            ),
            encoding="utf-8",
        )
        second = PipelineConfig.load(path)

        assert second.threshold_for("revenue") == 0.30
        assert second.report_schedule.interval == "daily"
        # First instance is untouched — load() returns fresh objects.
        assert first.threshold_for("revenue") == 0.15


class TestObservability:
    def test_config_loaded_event_emitted_without_secrets(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_PASSWORD", "s3cret-value")
        monkeypatch.setenv("SMTP_USERNAME", "mailer-user")

        with structlog.testing.capture_logs() as captured:
            PipelineConfig.load(write_config(tmp_path, VALID_YAML))

        events = [entry for entry in captured if entry["event"] == "config_loaded"]
        assert len(events) == 1
        event = events[0]

        assert event["schedule"] == "weekly"
        assert event["threshold_keys"] == ["revenue", "units_sold"]
        assert event["recipient_count"] == 1
        assert event["output_format"] == "docx"

        payload = json.dumps(event, default=str)
        assert "s3cret-value" not in payload
        assert "mailer-user" not in payload
        # Recipient addresses are PII-adjacent — count only, never the list.
        assert "ops@example.com" not in payload


class TestScheduleConfig:
    def test_describe_interval(self) -> None:
        assert ScheduleConfig(interval="daily").describe() == "daily"

    def test_describe_cron(self) -> None:
        assert ScheduleConfig(cron="0 6 * * 1").describe() == "cron:0 6 * * 1"
