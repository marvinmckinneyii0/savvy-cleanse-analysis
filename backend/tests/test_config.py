"""Tests for the Story 2.1 configuration layer.

Covers ``backend/models/pipeline_config.py`` and the re-export in
``backend/pipeline/config.py``: valid load with defaults, every invalid-value
path raising :class:`ConfigurationError` (never a bare Pydantic
``ValidationError``), env-sourced secrets, stateless reload, and the
``config_loaded`` log event carrying no secret values.

All file I/O goes through ``tmp_path`` — the real repo-root ``config.yaml``
is only ever *read* (default-path test), never written.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

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


def _valid_config_dict() -> dict[str, Any]:
    """Fresh copy of a minimal-but-complete valid config mapping."""
    return {
        "data_sources": ["data/sales.csv"],
        "report_schedule": {"interval": "weekly"},
        "metric_thresholds": {"revenue": 0.15, "units_sold": 0.20},
        "alert_recipients": ["ops@example.com"],
        "output": {"format": "docx", "output_dir": "output/"},
    }


def _write_config(tmp_path: Path, mapping: dict[str, Any]) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(mapping), encoding="utf-8")
    return path


class TestValidLoad:
    def test_valid_config_returns_typed_instance(self, tmp_path: Path) -> None:
        path = _write_config(tmp_path, _valid_config_dict())
        config = PipelineConfig.load(path)
        assert isinstance(config, PipelineConfig)
        assert config.data_sources == [Path("data/sales.csv")]
        assert config.report_schedule.interval == "weekly"
        assert config.report_schedule.cron is None
        assert config.metric_thresholds["units_sold"] == 0.20
        assert config.alert_recipients == ["ops@example.com"]

    def test_defaults_applied_when_optional_sections_omitted(self, tmp_path: Path) -> None:
        path = _write_config(
            tmp_path,
            {"data_sources": ["data/"], "report_schedule": {"interval": "daily"}},
        )
        config = PipelineConfig.load(path)
        assert config.output.format == "docx"
        assert config.output.output_dir == Path("output/")
        assert config.metric_thresholds == {}
        assert config.alert_recipients == []
        # Per-metric fallback: anything without an explicit entry gets 0.15.
        assert config.threshold_for("revenue") == DEFAULT_THRESHOLD == 0.15

    def test_threshold_for_prefers_explicit_entry(self, tmp_path: Path) -> None:
        path = _write_config(tmp_path, _valid_config_dict())
        config = PipelineConfig.load(path)
        assert config.threshold_for("units_sold") == 0.20
        assert config.threshold_for("never_configured") == DEFAULT_THRESHOLD

    def test_cron_schedule_accepted(self, tmp_path: Path) -> None:
        mapping = _valid_config_dict()
        mapping["report_schedule"] = {"cron": "0 6 * * 1"}
        config = PipelineConfig.load(_write_config(tmp_path, mapping))
        assert config.report_schedule.cron == "0 6 * * 1"
        assert config.report_schedule.describe() == "0 6 * * 1"

    def test_json_config_is_a_yaml_subset(self, tmp_path: Path) -> None:
        import json

        path = tmp_path / "config.json"
        path.write_text(json.dumps(_valid_config_dict()), encoding="utf-8")
        config = PipelineConfig.load(path)
        assert config.report_schedule.interval == "weekly"

    def test_default_path_loads_repo_root_config(self) -> None:
        # The committed config.yaml must itself be valid — this is the path
        # every agent takes when calling load() with no argument.
        config = PipelineConfig.load()
        assert isinstance(config, PipelineConfig)
        assert config.data_sources

    def test_reexport_from_pipeline_config_is_same_class(self) -> None:
        from backend.pipeline.config import PipelineConfig as ReExported

        assert ReExported is PipelineConfig


class TestInvalidConfig:
    def test_missing_required_field_raises_configuration_error(self, tmp_path: Path) -> None:
        mapping = _valid_config_dict()
        del mapping["data_sources"]
        path = _write_config(tmp_path, mapping)
        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(path)

    def test_validation_error_never_escapes(self, tmp_path: Path) -> None:
        mapping = _valid_config_dict()
        del mapping["report_schedule"]
        path = _write_config(tmp_path, mapping)
        try:
            PipelineConfig.load(path)
        except ConfigurationError:
            pass
        except ValidationError:  # pragma: no cover - the regression we guard against
            pytest.fail("Pydantic ValidationError escaped PipelineConfig.load()")
        else:  # pragma: no cover
            pytest.fail("invalid config did not raise")

    def test_invalid_cron_raises(self, tmp_path: Path) -> None:
        mapping = _valid_config_dict()
        mapping["report_schedule"] = {"cron": "not a cron"}
        with pytest.raises(ConfigurationError, match="cron"):
            PipelineConfig.load(_write_config(tmp_path, mapping))

    @pytest.mark.parametrize("bad_value", [-0.15, 0, 0.0, float("nan"), float("inf")])
    def test_nonpositive_or_nonfinite_threshold_raises(
        self, tmp_path: Path, bad_value: float
    ) -> None:
        mapping = _valid_config_dict()
        mapping["metric_thresholds"] = {"revenue": bad_value}
        with pytest.raises(ConfigurationError, match="metric_thresholds"):
            PipelineConfig.load(_write_config(tmp_path, mapping))

    def test_malformed_email_raises(self, tmp_path: Path) -> None:
        mapping = _valid_config_dict()
        mapping["alert_recipients"] = ["not-an-email"]
        with pytest.raises(ConfigurationError, match="alert_recipients"):
            PipelineConfig.load(_write_config(tmp_path, mapping))

    def test_interval_and_cron_together_raises(self, tmp_path: Path) -> None:
        mapping = _valid_config_dict()
        mapping["report_schedule"] = {"interval": "daily", "cron": "0 6 * * 1"}
        with pytest.raises(ConfigurationError, match="exactly one"):
            PipelineConfig.load(_write_config(tmp_path, mapping))

    def test_neither_interval_nor_cron_raises(self, tmp_path: Path) -> None:
        mapping = _valid_config_dict()
        mapping["report_schedule"] = {}
        with pytest.raises(ConfigurationError, match="exactly one"):
            PipelineConfig.load(_write_config(tmp_path, mapping))

    def test_unknown_interval_raises(self, tmp_path: Path) -> None:
        mapping = _valid_config_dict()
        mapping["report_schedule"] = {"interval": "hourly"}
        with pytest.raises(ConfigurationError, match="report_schedule"):
            PipelineConfig.load(_write_config(tmp_path, mapping))

    def test_empty_data_sources_raises(self, tmp_path: Path) -> None:
        mapping = _valid_config_dict()
        mapping["data_sources"] = []
        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(_write_config(tmp_path, mapping))

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="not found"):
            PipelineConfig.load(tmp_path / "does-not-exist.yaml")

    def test_malformed_yaml_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("data_sources: [unclosed", encoding="utf-8")
        with pytest.raises(ConfigurationError, match="YAML"):
            PipelineConfig.load(path)

    def test_non_mapping_root_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("- just\n- a\n- list\n", encoding="utf-8")
        with pytest.raises(ConfigurationError, match="mapping"):
            PipelineConfig.load(path)

    def test_smtp_section_in_yaml_is_rejected(self, tmp_path: Path) -> None:
        # Secrets never live in config.yaml — the loader rejects the key
        # outright rather than silently ignoring (or worse, honoring) it,
        # and the message points the user at the env-var mechanism.
        mapping = _valid_config_dict()
        mapping["smtp"] = {"password": "hunter2"}
        with pytest.raises(ConfigurationError, match="not allowed") as excinfo:
            PipelineConfig.load(_write_config(tmp_path, mapping))
        assert "environment" in str(excinfo.value)
        # The YAML-supplied secret value must not be echoed back.
        assert "hunter2" not in str(excinfo.value)

    def test_yaml_smtp_values_can_never_win_over_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Pins the security invariant against refactors of load()'s merge
        # order: a config file carrying smtp values errors out — it can
        # never override (or be merged with) the env-sourced settings.
        monkeypatch.setenv("SMTP_PASSWORD", "env-wins")
        mapping = _valid_config_dict()
        mapping["smtp"] = {"password": "yaml-tries-to-win"}
        with pytest.raises(ConfigurationError):
            PipelineConfig.load(_write_config(tmp_path, mapping))

    def test_empty_string_data_source_raises(self, tmp_path: Path) -> None:
        # "" would coerce to Path('.') and ingest the repo root downstream.
        mapping = _valid_config_dict()
        mapping["data_sources"] = ["data/sales.csv", ""]
        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(_write_config(tmp_path, mapping))

    def test_invalid_smtp_env_value_names_the_env_var(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A bad env value must not be misattributed to config.yaml — the
        # error names SMTP_PORT so the user looks in the right place.
        monkeypatch.setenv("SMTP_PORT", "not-a-number")
        path = _write_config(tmp_path, _valid_config_dict())
        with pytest.raises(ConfigurationError, match="SMTP_PORT") as excinfo:
            PipelineConfig.load(path)
        assert "SMTP environment" in str(excinfo.value)

    def test_unknown_top_level_key_rejected(self, tmp_path: Path) -> None:
        mapping = _valid_config_dict()
        mapping["metric_thersholds"] = {"revenue": 0.1}  # typo'd key
        with pytest.raises(ConfigurationError, match="metric_thersholds"):
            PipelineConfig.load(_write_config(tmp_path, mapping))


class TestEnvSecrets:
    def test_smtp_secrets_come_from_env_not_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "2525")
        monkeypatch.setenv("SMTP_USERNAME", "mailer")
        monkeypatch.setenv("SMTP_PASSWORD", "s3cr3t-value")
        monkeypatch.setenv("SMTP_FROM", "alerts@example.com")

        path = _write_config(tmp_path, _valid_config_dict())
        config = PipelineConfig.load(path)

        assert config.smtp.host == "smtp.example.com"
        assert config.smtp.port == 2525
        assert config.smtp.username == "mailer"
        assert config.smtp.password is not None
        assert config.smtp.password.get_secret_value() == "s3cr3t-value"
        assert config.smtp.from_addr == "alerts@example.com"
        # The secret is nowhere on disk.
        assert "s3cr3t-value" not in path.read_text(encoding="utf-8")

    def test_smtp_defaults_when_env_unset(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Neutralize dotenv so a developer's real repo-root .env can't
        # re-hydrate the vars we just cleared (would fail only on machines
        # with a populated .env, never in CI).
        import backend.models.pipeline_config as config_module

        monkeypatch.setattr(config_module, "load_dotenv", lambda *a, **k: None)
        for var in ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM"):
            monkeypatch.delenv(var, raising=False)
        config = PipelineConfig.load(_write_config(tmp_path, _valid_config_dict()))
        assert config.smtp.host is None
        assert config.smtp.port == 587
        assert config.smtp.password is None

    def test_secretstr_masks_password_in_repr(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SMTP_PASSWORD", "s3cr3t-value")
        smtp = SmtpSettings.from_env()
        assert "s3cr3t-value" not in repr(smtp)
        assert "s3cr3t-value" not in str(smtp)

    def test_smtp_hidden_from_config_repr(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # repr=False on the smtp field: a logged/interpolated config object
        # must not print SMTP host or username (half a credential pair).
        monkeypatch.setenv("SMTP_HOST", "smtp.internal.example.com")
        monkeypatch.setenv("SMTP_USERNAME", "mailer-account")
        config = PipelineConfig.load(_write_config(tmp_path, _valid_config_dict()))
        for rendered in (repr(config), str(config)):
            assert "smtp.internal.example.com" not in rendered
            assert "mailer-account" not in rendered

    def test_smtp_excluded_from_serialization(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_PASSWORD", "s3cr3t-value")
        config = PipelineConfig.load(_write_config(tmp_path, _valid_config_dict()))
        assert "s3cr3t-value" not in config.model_dump_json()


class TestReload:
    def test_reload_reflects_on_disk_changes(self, tmp_path: Path) -> None:
        mapping = _valid_config_dict()
        path = _write_config(tmp_path, mapping)
        first = PipelineConfig.load(path)
        assert first.threshold_for("revenue") == 0.15
        assert first.report_schedule.interval == "weekly"

        mapping["metric_thresholds"]["revenue"] = 0.30
        mapping["report_schedule"] = {"interval": "daily"}
        mapping["alert_recipients"].append("oncall@example.com")
        _write_config(tmp_path, mapping)

        second = PipelineConfig.load(path)
        assert second.threshold_for("revenue") == 0.30
        assert second.report_schedule.interval == "daily"
        assert len(second.alert_recipients) == 2
        # And the first instance is untouched — load() returns fresh objects.
        assert first.threshold_for("revenue") == 0.15


class TestObservability:
    def test_config_loaded_event_emitted_without_secrets(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_PASSWORD", "s3cr3t-value")
        monkeypatch.setenv("SMTP_USERNAME", "mailer-user")
        path = _write_config(tmp_path, _valid_config_dict())

        with structlog.testing.capture_logs() as logs:
            PipelineConfig.load(path)

        events = [entry for entry in logs if entry["event"] == "config_loaded"]
        assert len(events) == 1
        payload = events[0]
        assert payload["schedule"] == "weekly"
        assert payload["threshold_keys"] == ["revenue", "units_sold"]
        assert payload["recipient_count"] == 1
        assert payload["output_format"] == "docx"

        flattened = repr(payload)
        assert "s3cr3t-value" not in flattened
        assert "mailer-user" not in flattened
        # Recipient addresses are PII-adjacent — count only, never the list.
        assert "ops@example.com" not in flattened
