"""Tests for the Story 2.1 configuration layer.

Covers: valid config with defaults, missing required fields, invalid
values (bad cron, negative threshold, bad email), env-variable secret
override, stateless reload, secret-key rejection, and the non-secret
``config_loaded`` log event. All file I/O goes through ``tmp_path`` —
the real repo-root ``config.yaml`` is never touched.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import structlog

from backend.errors.exceptions import ConfigurationError
from backend.models.pipeline_config import (
    DEFAULT_THRESHOLD,
    PipelineConfig,
    ScheduleConfig,
    SmtpSettings,
)

VALID_CONFIG = textwrap.dedent(
    """\
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
      format: pdf
      output_dir: reports/
    """
)

MINIMAL_CONFIG = textwrap.dedent(
    """\
    data_sources:
      - data/sales.csv
    report_schedule:
      interval: daily
    """
)


def write_config(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(body, encoding="utf-8")
    return path


class TestValidLoad:
    def test_valid_config_returns_typed_instance(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))

        assert isinstance(config, PipelineConfig)
        assert config.data_sources == [Path("data/sales.csv")]
        assert config.report_schedule.interval == "weekly"
        assert config.metric_thresholds == {"revenue": 0.15, "units_sold": 0.20}
        assert config.alert_recipients == ["ops@example.com"]
        assert config.output.format == "pdf"
        assert config.output.output_dir == Path("reports/")

    def test_defaults_applied_for_minimal_config(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, MINIMAL_CONFIG))

        assert config.output.format == "docx"
        assert config.output.output_dir == Path("output/")
        assert config.metric_thresholds == {}
        assert config.alert_recipients == []
        # Unlisted metrics fall back to the 0.15 default.
        assert config.threshold_for("revenue") == DEFAULT_THRESHOLD == 0.15

    def test_threshold_for_prefers_explicit_entry(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))

        assert config.threshold_for("units_sold") == 0.20
        assert config.threshold_for("not_configured") == DEFAULT_THRESHOLD

    def test_cron_schedule_accepted(self, tmp_path: Path) -> None:
        body = MINIMAL_CONFIG.replace("interval: daily", 'cron: "0 6 * * 1"')
        config = PipelineConfig.load(write_config(tmp_path, body))

        assert config.report_schedule.cron == "0 6 * * 1"
        assert config.report_schedule.interval is None
        assert config.report_schedule.describe() == "cron:0 6 * * 1"

    def test_json_config_parses_as_yaml_subset(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text(
            '{"data_sources": ["data/sales.csv"], "report_schedule": {"interval": "monthly"}}',
            encoding="utf-8",
        )
        config = PipelineConfig.load(path)

        assert config.report_schedule.interval == "monthly"


class TestInvalidConfig:
    def test_missing_file_raises_configuration_error(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="not found"):
            PipelineConfig.load(tmp_path / "nope.yaml")

    def test_malformed_yaml_raises_configuration_error(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="malformed YAML"):
            PipelineConfig.load(write_config(tmp_path, "data_sources: [unclosed"))

    def test_non_mapping_root_raises_configuration_error(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="mapping"):
            PipelineConfig.load(write_config(tmp_path, "- just\n- a\n- list\n"))

    def test_empty_file_raises_configuration_error(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="empty"):
            PipelineConfig.load(write_config(tmp_path, ""))

    def test_non_utf8_file_raises_configuration_error(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_bytes(b"\xff\xfe not utf-8")
        with pytest.raises(ConfigurationError, match="not valid UTF-8"):
            PipelineConfig.load(path)

    def test_missing_required_field_raises_configuration_error(self, tmp_path: Path) -> None:
        body = "report_schedule:\n  interval: daily\n"  # no data_sources
        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(write_config(tmp_path, body))

    def test_empty_data_sources_rejected(self, tmp_path: Path) -> None:
        body = MINIMAL_CONFIG.replace("data_sources:\n  - data/sales.csv", "data_sources: []")
        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(write_config(tmp_path, body))

    def test_invalid_cron_raises_configuration_error(self, tmp_path: Path) -> None:
        body = MINIMAL_CONFIG.replace("interval: daily", 'cron: "99 99 * * *"')
        with pytest.raises(ConfigurationError, match="cron"):
            PipelineConfig.load(write_config(tmp_path, body))

    def test_interval_and_cron_together_rejected(self, tmp_path: Path) -> None:
        body = MINIMAL_CONFIG.replace("interval: daily", 'interval: daily\n  cron: "0 6 * * 1"')
        with pytest.raises(ConfigurationError, match="exactly one"):
            PipelineConfig.load(write_config(tmp_path, body))

    def test_unknown_interval_rejected(self, tmp_path: Path) -> None:
        body = MINIMAL_CONFIG.replace("interval: daily", "interval: hourly")
        with pytest.raises(ConfigurationError, match="interval"):
            PipelineConfig.load(write_config(tmp_path, body))

    @pytest.mark.parametrize("bad_threshold", ["-0.1", "0"])
    def test_nonpositive_threshold_raises_configuration_error(
        self, tmp_path: Path, bad_threshold: str
    ) -> None:
        body = MINIMAL_CONFIG + f"metric_thresholds:\n  revenue: {bad_threshold}\n"
        with pytest.raises(ConfigurationError, match="must be > 0"):
            PipelineConfig.load(write_config(tmp_path, body))

    def test_malformed_email_raises_configuration_error(self, tmp_path: Path) -> None:
        body = MINIMAL_CONFIG + "alert_recipients:\n  - not-an-email\n"
        with pytest.raises(ConfigurationError, match="alert_recipients"):
            PipelineConfig.load(write_config(tmp_path, body))

    def test_unknown_output_format_rejected(self, tmp_path: Path) -> None:
        body = MINIMAL_CONFIG + "output:\n  format: xlsx\n"
        with pytest.raises(ConfigurationError, match="output"):
            PipelineConfig.load(write_config(tmp_path, body))

    def test_validation_error_does_not_escape(self, tmp_path: Path) -> None:
        import pydantic

        body = MINIMAL_CONFIG + "alert_recipients:\n  - not-an-email\n"
        try:
            PipelineConfig.load(write_config(tmp_path, body))
        except pydantic.ValidationError:  # pragma: no cover - the failure being asserted
            pytest.fail("pydantic.ValidationError escaped the loader uncaught")
        except ConfigurationError:
            pass
        else:  # pragma: no cover - the failure being asserted
            pytest.fail("expected ConfigurationError for a malformed email")


class TestSecrets:
    def test_smtp_sourced_from_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "2525")
        monkeypatch.setenv("SMTP_USERNAME", "mailer")
        monkeypatch.setenv("SMTP_PASSWORD", "s3cret-pw")
        monkeypatch.setenv("SMTP_FROM", "alerts@example.com")

        path = write_config(tmp_path, VALID_CONFIG)
        config = PipelineConfig.load(path)

        assert config.smtp.host == "smtp.example.com"
        assert config.smtp.port == 2525
        assert config.smtp.username == "mailer"
        assert config.smtp.password == "s3cret-pw"
        assert config.smtp.from_addr == "alerts@example.com"
        # The secret came from env, never from any YAML on disk.
        assert "s3cret-pw" not in path.read_text(encoding="utf-8")

    def test_smtp_defaults_when_env_absent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        for var in ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM"):
            monkeypatch.delenv(var, raising=False)
        # A developer's real repo-root .env would repopulate the vars just
        # deleted (and a failing assert would echo real credentials) —
        # neutralize dotenv for this test only.
        monkeypatch.setattr(
            "backend.models.pipeline_config.load_dotenv", lambda *a, **kw: False
        )

        config = PipelineConfig.load(write_config(tmp_path, MINIMAL_CONFIG))

        assert config.smtp == SmtpSettings()
        assert config.smtp.port == 587

    def test_non_integer_smtp_port_raises_configuration_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_PORT", "not-a-port")
        with pytest.raises(ConfigurationError, match="SMTP_PORT"):
            PipelineConfig.load(write_config(tmp_path, MINIMAL_CONFIG))

    def test_smtp_key_in_yaml_rejected(self, tmp_path: Path) -> None:
        body = MINIMAL_CONFIG + "smtp:\n  password: leaked\n"
        with pytest.raises(ConfigurationError, match="environment variables only"):
            PipelineConfig.load(write_config(tmp_path, body))

    def test_repo_root_config_yaml_contains_no_secrets(self) -> None:
        repo_config = Path(__file__).resolve().parents[2] / "config.yaml"
        text = repo_config.read_text(encoding="utf-8").lower()
        for needle in ("password", "api_key", "secret_key", "token:"):
            assert needle not in text


class TestDefaultPath:
    def test_no_arg_load_reads_repo_root_config(self) -> None:
        # Read-only: validates the committed repo-root config.yaml and the
        # default-path computation (AC3) without writing anything.
        config = PipelineConfig.load()

        assert isinstance(config, PipelineConfig)
        assert len(config.data_sources) >= 1


class TestReload:
    def test_reload_reflects_on_disk_changes(self, tmp_path: Path) -> None:
        path = write_config(tmp_path, VALID_CONFIG)
        first = PipelineConfig.load(path)
        assert first.threshold_for("revenue") == 0.15

        path.write_text(
            VALID_CONFIG.replace("revenue: 0.15", "revenue: 0.30").replace(
                "interval: weekly", "interval: daily"
            ),
            encoding="utf-8",
        )
        second = PipelineConfig.load(path)

        assert second.threshold_for("revenue") == 0.30
        assert second.report_schedule.interval == "daily"
        # The previously returned instance is an unchanged snapshot.
        assert first.threshold_for("revenue") == 0.15


class TestObservability:
    def test_config_loaded_event_emitted_without_secrets(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_PASSWORD", "s3cret-pw")
        monkeypatch.setenv("SMTP_USERNAME", "mailer-user")
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")

        with structlog.testing.capture_logs() as logs:
            PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))

        events = [entry for entry in logs if entry["event"] == "config_loaded"]
        assert len(events) == 1
        event = events[0]

        assert event["schedule"] == "weekly"
        assert event["threshold_keys"] == ["revenue", "units_sold"]
        assert event["recipient_count"] == 1
        assert event["output_format"] == "pdf"
        assert event["smtp_configured"] is True

        payload = repr(event)
        assert "s3cret-pw" not in payload
        assert "mailer-user" not in payload
        # Recipient addresses are PII-adjacent — count only, never the list.
        assert "ops@example.com" not in payload


class TestReExport:
    def test_pipeline_config_importable_from_both_paths(self) -> None:
        from backend.models.pipeline_config import PipelineConfig as from_models
        from backend.pipeline.config import PipelineConfig as from_pipeline

        assert from_pipeline is from_models

    def test_logging_helpers_still_exported(self) -> None:
        from backend.pipeline.config import bind_pipeline_run_id, configure_logging

        assert callable(configure_logging)
        assert callable(bind_pipeline_run_id)


class TestScheduleConfigUnit:
    def test_describe_interval(self) -> None:
        assert ScheduleConfig(interval="daily").describe() == "daily"

    def test_neither_interval_nor_cron_rejected(self) -> None:
        with pytest.raises(ValueError, match="exactly one"):
            ScheduleConfig()


class TestUnreadablePath:
    def test_directory_path_raises_configuration_error(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="cannot read config file"):
            PipelineConfig.load(tmp_path)
