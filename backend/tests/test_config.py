"""Tests for the Story 2.1 configuration layer.

Covers ``backend/models/pipeline_config.py`` and the re-export in
``backend/pipeline/config.py``: valid load with defaults, every invalid-value
path raising :class:`ConfigurationError`, env-only SMTP secrets (process env
over ``.env``), stateless reload, path anchoring, and the secret-free
``config_loaded`` log event.

All file I/O goes through ``tmp_path`` — the real repo-root ``config.yaml``
and ``.env`` are never touched (the autouse fixture points the module's
dotenv path into ``tmp_path``).
"""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest
import structlog
from pydantic import ValidationError

import backend.models.pipeline_config as pipeline_config_module
from backend.errors.exceptions import ConfigurationError
from backend.models.pipeline_config import (
    _SMTP_ENV_VARS,
    DEFAULT_THRESHOLD,
    PipelineConfig,
    ThresholdConfig,
)

VALID_YAML = dedent(
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
      format: docx
      output_dir: output/
    """
)


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Isolate every test from ambient SMTP_* variables AND the real .env.

    ``load()`` reads the project ``.env`` via the module-level
    ``_DOTENV_PATH``; pointing it into ``tmp_path`` means a developer's
    filled-in repo ``.env`` can never leak into these tests. Tests that
    exercise .env behavior write to this same path.
    """
    for env_var in _SMTP_ENV_VARS.values():
        monkeypatch.delenv(env_var, raising=False)
    monkeypatch.setattr(pipeline_config_module, "_DOTENV_PATH", tmp_path / ".env")


def write_config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    return path


class TestValidLoad:
    def test_valid_config_returns_typed_instance(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, VALID_YAML))

        assert isinstance(config, PipelineConfig)
        assert config.data_sources == [tmp_path / "data/sales.csv"]
        assert config.report_schedule.interval == "weekly"
        assert config.report_schedule.cron is None
        assert config.metric_thresholds.root == {"revenue": 0.15, "units_sold": 0.20}
        assert config.alert_recipients == ["ops@example.com"]
        assert config.output.format == "docx"
        assert config.output.output_dir == tmp_path / "output"

    def test_defaults_applied_when_sections_omitted(self, tmp_path: Path) -> None:
        minimal = dedent(
            """\
            data_sources:
              - data/sales.csv
            report_schedule:
              interval: daily
            """
        )
        config = PipelineConfig.load(write_config(tmp_path, minimal))

        assert config.output.format == "docx"
        assert config.output.output_dir == tmp_path / "output"
        assert config.alert_recipients == []
        assert config.metric_thresholds.threshold_for("anything") == DEFAULT_THRESHOLD
        assert DEFAULT_THRESHOLD == 0.15

    def test_commented_out_sections_fall_back_to_defaults(self, tmp_path: Path) -> None:
        # A section header whose entries are all commented out parses to
        # None — it must behave like an omitted section, not an error.
        yaml_text = dedent(
            """\
            data_sources:
              - data/sales.csv
            report_schedule:
              interval: daily
            metric_thresholds:
              # revenue: 0.15
            alert_recipients:
            """
        )
        config = PipelineConfig.load(write_config(tmp_path, yaml_text))

        assert config.metric_thresholds.root == {}
        assert config.alert_recipients == []

    def test_threshold_for_falls_back_to_default(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, VALID_YAML))

        assert config.metric_thresholds.threshold_for("units_sold") == 0.20
        assert config.metric_thresholds.threshold_for("unlisted") == DEFAULT_THRESHOLD

    def test_absolute_paths_not_reanchored(self, tmp_path: Path) -> None:
        absolute_source = (tmp_path / "elsewhere" / "sales.csv").resolve()
        yaml_text = VALID_YAML.replace("data/sales.csv", absolute_source.as_posix())
        config = PipelineConfig.load(write_config(tmp_path, yaml_text))

        assert config.data_sources == [absolute_source]

    def test_cron_schedule_accepted(self, tmp_path: Path) -> None:
        yaml_text = VALID_YAML.replace("  interval: weekly", '  cron: "0 6 * * 1"')
        config = PipelineConfig.load(write_config(tmp_path, yaml_text))

        assert config.report_schedule.cron == "0 6 * * 1"
        assert config.report_schedule.interval is None
        assert config.report_schedule.describe() == "cron(0 6 * * 1)"

    def test_json_config_parses_via_safe_load(self, tmp_path: Path) -> None:
        # JSON is a strict subset of YAML — one loader handles both (AC1).
        payload = {
            "data_sources": ["data/sales.csv"],
            "report_schedule": {"interval": "monthly"},
        }
        path = tmp_path / "config.json"
        path.write_text(json.dumps(payload), encoding="utf-8")

        config = PipelineConfig.load(path)
        assert config.report_schedule.interval == "monthly"

    def test_pipeline_config_reexport_is_same_class(self) -> None:
        from backend.pipeline.config import PipelineConfig as ReExported

        assert ReExported is PipelineConfig


class TestInvalidConfig:
    def test_missing_required_field_raises_configuration_error(self, tmp_path: Path) -> None:
        no_sources = dedent(
            """\
            report_schedule:
              interval: weekly
            """
        )
        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(write_config(tmp_path, no_sources))

    def test_validation_error_never_escapes(self, tmp_path: Path) -> None:
        # AC2: if a bare ValidationError escaped load(), it would propagate
        # here and fail the raises block.
        with pytest.raises(ConfigurationError):
            PipelineConfig.load(write_config(tmp_path, "data_sources: []\n"))

    def test_invalid_cron_raises(self, tmp_path: Path) -> None:
        yaml_text = VALID_YAML.replace(
            "  interval: weekly", '  cron: "not a cron expr"'
        )
        with pytest.raises(ConfigurationError, match="cron"):
            PipelineConfig.load(write_config(tmp_path, yaml_text))

    def test_interval_and_cron_together_raise(self, tmp_path: Path) -> None:
        yaml_text = VALID_YAML.replace(
            "  interval: weekly", '  interval: weekly\n  cron: "0 6 * * 1"'
        )
        with pytest.raises(ConfigurationError, match="exactly one"):
            PipelineConfig.load(write_config(tmp_path, yaml_text))

    def test_unknown_interval_raises(self, tmp_path: Path) -> None:
        yaml_text = VALID_YAML.replace("interval: weekly", "interval: hourly")
        with pytest.raises(ConfigurationError, match="interval"):
            PipelineConfig.load(write_config(tmp_path, yaml_text))

    @pytest.mark.parametrize("bad_value", ["-0.15", "0", "0.0", ".nan"])
    def test_nonpositive_threshold_raises(self, tmp_path: Path, bad_value: str) -> None:
        yaml_text = VALID_YAML.replace("revenue: 0.15", f"revenue: {bad_value}")
        with pytest.raises(ConfigurationError, match="metric_thresholds"):
            PipelineConfig.load(write_config(tmp_path, yaml_text))

    def test_malformed_email_raises(self, tmp_path: Path) -> None:
        yaml_text = VALID_YAML.replace("ops@example.com", "not-an-email")
        with pytest.raises(ConfigurationError, match="alert_recipients"):
            PipelineConfig.load(write_config(tmp_path, yaml_text))

    def test_bad_output_format_raises(self, tmp_path: Path) -> None:
        yaml_text = VALID_YAML.replace("format: docx", "format: xlsx")
        with pytest.raises(ConfigurationError, match="output"):
            PipelineConfig.load(write_config(tmp_path, yaml_text))

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="not found"):
            PipelineConfig.load(tmp_path / "does-not-exist.yaml")

    def test_directory_path_raises_configuration_error(self, tmp_path: Path) -> None:
        # IsADirectoryError is an OSError, not FileNotFoundError — it must
        # still surface as ConfigurationError, never a bare OSError.
        with pytest.raises(ConfigurationError, match="could not be read"):
            PipelineConfig.load(tmp_path)

    def test_malformed_yaml_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="YAML"):
            PipelineConfig.load(write_config(tmp_path, "data_sources: [unclosed\n"))

    def test_non_mapping_root_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="mapping"):
            PipelineConfig.load(write_config(tmp_path, "- just\n- a\n- list\n"))

    def test_unknown_top_level_key_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="typo_key"):
            PipelineConfig.load(write_config(tmp_path, VALID_YAML + "typo_key: 1\n"))


class TestSecrets:
    def test_smtp_sourced_from_process_env(
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
        assert config.smtp.password is not None
        assert config.smtp.password.get_secret_value() == "s3cret-value"
        assert config.smtp.from_address == "alerts@example.com"
        # The secret exists only in env — never on disk (AC4).
        assert "s3cret-value" not in path.read_text(encoding="utf-8")

    def test_smtp_sourced_from_dotenv_file(self, tmp_path: Path) -> None:
        (tmp_path / ".env").write_text(
            "SMTP_HOST=smtp.dotenv.example\nSMTP_PASSWORD=dotenv-s3cret\n",
            encoding="utf-8",
        )
        config = PipelineConfig.load(write_config(tmp_path, VALID_YAML))

        assert config.smtp.host == "smtp.dotenv.example"
        assert config.smtp.password is not None
        assert config.smtp.password.get_secret_value() == "dotenv-s3cret"

    def test_process_env_wins_over_dotenv(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / ".env").write_text("SMTP_HOST=from-dotenv\n", encoding="utf-8")
        monkeypatch.setenv("SMTP_HOST", "from-process-env")

        config = PipelineConfig.load(write_config(tmp_path, VALID_YAML))
        assert config.smtp.host == "from-process-env"

    def test_dotenv_edit_picked_up_on_reload(self, tmp_path: Path) -> None:
        # Secret rotation in .env must reach the next load() — no process
        # restart, no stale os.environ copy (FR10 for the secrets half).
        dotenv = tmp_path / ".env"
        dotenv.write_text("SMTP_PASSWORD=old-secret\n", encoding="utf-8")
        path = write_config(tmp_path, VALID_YAML)

        first = PipelineConfig.load(path)
        assert first.smtp.password is not None
        assert first.smtp.password.get_secret_value() == "old-secret"

        dotenv.write_text("SMTP_PASSWORD=new-secret\n", encoding="utf-8")
        second = PipelineConfig.load(path)
        assert second.smtp.password is not None
        assert second.smtp.password.get_secret_value() == "new-secret"

    def test_load_does_not_mutate_os_environ(self, tmp_path: Path) -> None:
        import os

        (tmp_path / ".env").write_text("SMTP_HOST=smtp.dotenv.example\n", encoding="utf-8")
        PipelineConfig.load(write_config(tmp_path, VALID_YAML))

        assert "SMTP_HOST" not in os.environ

    def test_smtp_defaults_when_env_unset(self, tmp_path: Path) -> None:
        config = PipelineConfig.load(write_config(tmp_path, VALID_YAML))

        assert config.smtp.host is None
        assert config.smtp.port == 587
        assert config.smtp.password is None

    def test_empty_env_placeholders_treated_as_unset(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A copied-but-unfilled .env exports empty strings; they must not
        # become host="" / port="".
        for env_var in _SMTP_ENV_VARS.values():
            monkeypatch.setenv(env_var, "")
        config = PipelineConfig.load(write_config(tmp_path, VALID_YAML))

        assert config.smtp.host is None
        assert config.smtp.port == 587

    def test_smtp_in_yaml_rejected(self, tmp_path: Path) -> None:
        yaml_text = VALID_YAML + "smtp:\n  password: leaked\n"
        with pytest.raises(ConfigurationError, match="environment variables only"):
            PipelineConfig.load(write_config(tmp_path, yaml_text))

    def test_bare_smtp_header_in_yaml_rejected(self, tmp_path: Path) -> None:
        # Even an empty `smtp:` header signals the wrong intent — reject it
        # before the None-pruning step can silently drop it.
        with pytest.raises(ConfigurationError, match="environment variables only"):
            PipelineConfig.load(write_config(tmp_path, VALID_YAML + "smtp:\n"))

    def test_secret_masked_in_repr(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SMTP_PASSWORD", "s3cret-value")
        config = PipelineConfig.load(write_config(tmp_path, VALID_YAML))

        assert "s3cret-value" not in repr(config)
        assert "s3cret-value" not in str(config.smtp)

    def test_invalid_env_value_error_does_not_leak_input(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_PORT", "not-a-port-s3cret")
        with pytest.raises(ConfigurationError) as excinfo:
            PipelineConfig.load(write_config(tmp_path, VALID_YAML))

        assert "smtp.port" in str(excinfo.value)
        assert "not-a-port-s3cret" not in str(excinfo.value)


class TestReload:
    def test_reload_reflects_on_disk_changes(self, tmp_path: Path) -> None:
        path = write_config(tmp_path, VALID_YAML)
        first = PipelineConfig.load(path)
        assert first.metric_thresholds.root["revenue"] == 0.15
        assert first.report_schedule.interval == "weekly"

        updated = VALID_YAML.replace("revenue: 0.15", "revenue: 0.30").replace(
            "interval: weekly", "interval: daily"
        )
        path.write_text(updated, encoding="utf-8")

        second = PipelineConfig.load(path)
        assert second.metric_thresholds.root["revenue"] == 0.30
        assert second.report_schedule.interval == "daily"
        # The first instance is untouched — load() returns fresh objects.
        assert first.metric_thresholds.root["revenue"] == 0.15


class TestObservability:
    def test_config_loaded_event_emitted_without_secrets(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_PASSWORD", "s3cret-value")
        monkeypatch.setenv("SMTP_USERNAME", "mailer-user")
        path = write_config(tmp_path, VALID_YAML)

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
        assert "s3cret-value" not in flattened
        assert "mailer-user" not in flattened
        # Recipient addresses are PII-adjacent — count only, never the list.
        assert "ops@example.com" not in flattened
        # Project rule: never log file paths with usernames — only the
        # config file's name may appear, not its absolute directory.
        assert str(tmp_path) not in flattened


def test_threshold_config_direct_validation() -> None:
    with pytest.raises(ValidationError):
        ThresholdConfig({"revenue": -1.0})
    assert ThresholdConfig({"revenue": 0.5}).root["revenue"] == 0.5
