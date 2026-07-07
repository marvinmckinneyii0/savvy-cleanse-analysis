"""Tests for the Story 2.1 configuration layer.

Covers ``backend/models/pipeline_config.py`` and the re-export in
``backend/pipeline/config.py``: valid loads with defaults, every
ConfigurationError path (missing file, malformed YAML, missing fields,
bad cron, non-positive thresholds, bad emails, smtp-in-yaml), env-sourced
SMTP secrets, stateless reload, and the secret-free ``config_loaded``
structlog event. All file I/O goes through ``tmp_path`` — the real
repo-root ``config.yaml`` is never touched.
"""

from __future__ import annotations

import json
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


def write_config(tmp_path: Path, data: dict, filename: str = "config.yaml") -> Path:
    path = tmp_path / filename
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def _clean_smtp_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate every test from ambient SMTP_* variables and any dev .env.

    load() calls load_dotenv() internally, which would re-inject a
    developer's real .env values after the delenv below — so it is
    no-op'd here; tests control the environment via monkeypatch only.
    """
    monkeypatch.setattr(
        "backend.models.pipeline_config.load_dotenv", lambda *args, **kwargs: False
    )
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
        assert config.output.format == "docx"
        assert config.output.output_dir == Path("output")

    def test_defaults_applied_when_sections_omitted(self, tmp_path: Path) -> None:
        minimal = {
            "data_sources": ["data/"],
            "report_schedule": {"interval": "daily"},
            "alert_recipients": [],
        }
        config = PipelineConfig.load(write_config(tmp_path, minimal))

        assert config.metric_thresholds == {}
        assert config.threshold_for("revenue") == DEFAULT_THRESHOLD == 0.15
        assert config.output.format == "docx"
        assert config.output.output_dir == Path("output")

    def test_threshold_for_prefers_explicit_entry(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))

        assert config.threshold_for("units_sold") == 0.20
        assert config.threshold_for("unlisted_metric") == DEFAULT_THRESHOLD

    def test_cron_schedule_accepted(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "report_schedule": {"cron": "0 6 * * 1"}}
        config = PipelineConfig.load(write_config(tmp_path, data))

        assert config.report_schedule.cron == "0 6 * * 1"
        assert config.report_schedule.interval is None
        assert config.report_schedule.describe() == "cron:0 6 * * 1"

    def test_json_config_parses_via_safe_load(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text(json.dumps(VALID_CONFIG), encoding="utf-8")

        config = PipelineConfig.load(path)

        assert config.report_schedule.interval == "weekly"

    def test_repo_root_config_yaml_is_loadable(self) -> None:
        """The committed config.yaml example must itself validate (read-only).

        Deliberately asserts nothing about the file's *values* — operators
        edit config.yaml at runtime (FR10), and the suite must not go red
        on a legitimate schedule or threshold change.
        """
        config = PipelineConfig.load()

        assert isinstance(config, PipelineConfig)


class TestInvalidConfig:
    def test_missing_file_raises_configuration_error(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="not found"):
            PipelineConfig.load(tmp_path / "nope.yaml")

    def test_malformed_yaml_raises_configuration_error(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("data_sources: [unclosed", encoding="utf-8")

        with pytest.raises(ConfigurationError, match="not valid YAML"):
            PipelineConfig.load(path)

    def test_non_mapping_document_raises_configuration_error(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("- just\n- a\n- list\n", encoding="utf-8")

        with pytest.raises(ConfigurationError, match="mapping"):
            PipelineConfig.load(path)

    def test_missing_required_field_names_the_field(self, tmp_path: Path) -> None:
        data = {k: v for k, v in VALID_CONFIG.items() if k != "data_sources"}

        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_empty_data_sources_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "data_sources": []}

        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_invalid_cron_expression_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "report_schedule": {"cron": "not a cron"}}

        with pytest.raises(ConfigurationError, match="cron"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_interval_and_cron_together_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "report_schedule": {"interval": "daily", "cron": "0 6 * * 1"}}

        with pytest.raises(ConfigurationError, match="exactly one"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_unknown_interval_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "report_schedule": {"interval": "hourly"}}

        with pytest.raises(ConfigurationError, match="interval"):
            PipelineConfig.load(write_config(tmp_path, data))

    @pytest.mark.parametrize("bad_threshold", [-0.15, 0, 0.0])
    def test_non_positive_threshold_rejected(self, tmp_path: Path, bad_threshold: float) -> None:
        data = {**VALID_CONFIG, "metric_thresholds": {"revenue": bad_threshold}}

        with pytest.raises(ConfigurationError, match="revenue"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_malformed_email_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "alert_recipients": ["not-an-email"]}

        with pytest.raises(ConfigurationError, match="alert_recipients"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_invalid_output_format_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "output": {"format": "xlsx"}}

        with pytest.raises(ConfigurationError, match="output.format"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_unknown_top_level_key_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "tpyo_section": True}

        with pytest.raises(ConfigurationError, match="tpyo_section"):
            PipelineConfig.load(write_config(tmp_path, data))

    def test_validation_error_never_escapes(self, tmp_path: Path) -> None:
        """AC2: a raw pydantic.ValidationError must not leak out of load()."""
        import pydantic

        data = {**VALID_CONFIG, "alert_recipients": ["bad"]}
        with pytest.raises(ConfigurationError) as excinfo:
            PipelineConfig.load(write_config(tmp_path, data))
        assert not isinstance(excinfo.value, pydantic.ValidationError)


class TestSecretsFromEnv:
    def test_smtp_sourced_from_env_not_yaml(
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
        assert config.smtp.password is not None
        assert config.smtp.password.get_secret_value() == "s3cr3t-value"
        assert config.smtp.from_address == "alerts@example.com"
        assert "s3cr3t-value" not in path.read_text(encoding="utf-8")
        # SecretStr masks the password even if the whole config is printed.
        assert "s3cr3t-value" not in repr(config)
        assert "s3cr3t-value" not in str(config.model_dump())

    def test_smtp_defaults_when_env_unset(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))

        assert config.smtp == SmtpSettings()
        assert config.smtp.port == 587

    def test_directly_constructed_config_also_sources_smtp_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Env sourcing is a property of the model, not a load()-only side channel."""
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")

        config = PipelineConfig(
            data_sources=[Path("data/")],
            report_schedule={"interval": "daily"},
            alert_recipients=[],
        )

        assert config.smtp.host == "smtp.example.com"

    def test_whitespace_only_env_values_treated_as_unset(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_HOST", "   ")
        monkeypatch.setenv("SMTP_USERNAME", " mailer ")

        config = PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))

        assert config.smtp.host is None
        assert config.smtp.username == "mailer"

    def test_smtp_key_in_yaml_rejected(self, tmp_path: Path) -> None:
        data = {**VALID_CONFIG, "smtp": {"password": "should-not-be-here"}}

        with pytest.raises(ConfigurationError, match="smtp"):
            PipelineConfig.load(write_config(tmp_path, data))

    @pytest.mark.parametrize("bad_port", ["not-a-port", "0", "-25", "70000"])
    def test_bad_smtp_port_rejected_without_echoing_secrets(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bad_port: str
    ) -> None:
        monkeypatch.setenv("SMTP_PORT", bad_port)
        monkeypatch.setenv("SMTP_PASSWORD", "s3cr3t-value")

        with pytest.raises(ConfigurationError) as excinfo:
            PipelineConfig.load(write_config(tmp_path, VALID_CONFIG))
        assert "SMTP_*" in str(excinfo.value)
        assert "port" in str(excinfo.value)
        assert "s3cr3t-value" not in str(excinfo.value)


class TestReload:
    def test_reload_reflects_disk_changes(self, tmp_path: Path) -> None:
        """FR10: load() is stateless — a second call picks up file edits."""
        path = write_config(tmp_path, VALID_CONFIG)
        before = PipelineConfig.load(path)

        updated = {
            **VALID_CONFIG,
            "metric_thresholds": {"revenue": 0.30},
            "report_schedule": {"interval": "daily"},
            "alert_recipients": ["ops@example.com", "oncall@example.com"],
        }
        write_config(tmp_path, updated)
        after = PipelineConfig.load(path)

        assert before.metric_thresholds["revenue"] == 0.15
        assert after.metric_thresholds["revenue"] == 0.30
        assert after.report_schedule.interval == "daily"
        assert len(after.alert_recipients) == 2


class TestObservability:
    def test_config_loaded_event_emitted_without_secrets(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_PASSWORD", "s3cr3t-value")
        monkeypatch.setenv("SMTP_USERNAME", "mailer-user")
        path = write_config(tmp_path, VALID_CONFIG)

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

        payload = repr(event)
        assert "s3cr3t-value" not in payload
        assert "mailer-user" not in payload
        assert "ops@example.com" not in payload  # recipients logged as count, not list


class TestReExport:
    def test_pipeline_config_reexported_from_pipeline_package(self) -> None:
        """Both historical import paths must resolve to the one Pydantic model."""
        from backend.models.pipeline_config import PipelineConfig as models_config
        from backend.pipeline.config import PipelineConfig as pipeline_config

        assert pipeline_config is models_config

    def test_output_format_shared_with_orchestrator(self) -> None:
        """One format vocabulary: config schema and CLI use the same enum."""
        from backend.models.pipeline_config import OutputFormat as models_fmt
        from backend.pipeline.orchestrator import OutputFormat as orchestrator_fmt

        assert orchestrator_fmt is models_fmt

    def test_logging_helpers_still_importable(self) -> None:
        from backend.pipeline.config import bind_pipeline_run_id, configure_logging

        assert callable(configure_logging)
        assert callable(bind_pipeline_run_id)
