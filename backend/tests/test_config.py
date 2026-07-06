"""Tests for the Story 2.1 configuration layer.

Covers backend/models/pipeline_config.py and the re-export in
backend/pipeline/config.py: valid loads with defaults, every
ConfigurationError path (missing file, bad YAML, missing fields, bad
cron, non-positive thresholds, bad email), env-sourced SMTP secrets,
stateless reload, and the no-secrets ``config_loaded`` log event.

All file I/O goes through ``tmp_path`` — the real repo-root config.yaml
is read-only here (one smoke test loads it as shipped).
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

SECRET_MARKER = "hunter2-super-secret"


@pytest.fixture(autouse=True)
def _no_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Neutralize load_dotenv() for every test in this module.

    load_dotenv() walks up from cwd and would re-inject a developer's real
    repo-root .env AFTER monkeypatch.delenv, making SMTP assertions
    environment-dependent (and mutating os.environ outside monkeypatch
    cleanup). Env sourcing itself is still covered via monkeypatch.setenv.
    """
    monkeypatch.setattr("backend.models.pipeline_config.load_dotenv", lambda: None)


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    """A valid config.yaml written to an isolated tmp directory."""
    path = tmp_path / "config.yaml"
    path.write_text(VALID_CONFIG, encoding="utf-8")
    return path


def _write(path: Path, mutate: dict) -> None:
    """Rewrite ``path`` as VALID_CONFIG with top-level keys replaced/removed.

    A value of ``None`` in ``mutate`` deletes the key entirely.
    """
    data = yaml.safe_load(VALID_CONFIG)
    for key, value in mutate.items():
        if value is None:
            data.pop(key, None)
        else:
            data[key] = value
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


class TestValidLoad:
    def test_valid_config_returns_typed_instance(self, config_path: Path) -> None:
        config = PipelineConfig.load(config_path)

        assert isinstance(config, PipelineConfig)
        assert config.data_sources == [Path("data/sales.csv")]
        assert config.report_schedule.interval == "weekly"
        assert config.report_schedule.cron is None
        assert config.metric_thresholds == {"revenue": 0.15, "units_sold": 0.20}
        assert config.alert_recipients == ["ops@example.com"]
        assert config.output.format == "docx"
        assert config.output.output_dir == Path("output/")

    def test_accepts_str_and_path_arguments(self, config_path: Path) -> None:
        assert PipelineConfig.load(str(config_path)).data_sources == [Path("data/sales.csv")]

    def test_defaults_applied_when_sections_omitted(self, config_path: Path) -> None:
        _write(config_path, {"metric_thresholds": None, "output": None, "alert_recipients": None})

        config = PipelineConfig.load(config_path)

        assert config.output.format == "docx"
        assert config.output.output_dir == Path("output/")
        assert config.alert_recipients == []
        assert config.metric_thresholds == {}
        assert config.threshold_for("revenue") == DEFAULT_THRESHOLD == 0.15

    def test_threshold_for_prefers_explicit_metric_entry(self, config_path: Path) -> None:
        config = PipelineConfig.load(config_path)

        assert config.threshold_for("units_sold") == 0.20
        assert config.threshold_for("never_configured") == DEFAULT_THRESHOLD

    def test_cron_schedule_accepted(self, config_path: Path) -> None:
        _write(config_path, {"report_schedule": {"cron": "0 6 * * 1"}})

        config = PipelineConfig.load(config_path)

        assert config.report_schedule.cron == "0 6 * * 1"
        assert config.report_schedule.interval is None
        assert config.report_schedule.describe() == "cron:0 6 * * 1"

    def test_json_config_is_parsed_by_the_same_loader(self, tmp_path: Path) -> None:
        # JSON is a strict subset of YAML — no separate parser branch.
        path = tmp_path / "config.json"
        path.write_text(
            '{"data_sources": ["data/sales.csv"], "report_schedule": {"interval": "daily"}}',
            encoding="utf-8",
        )

        config = PipelineConfig.load(path)

        assert config.report_schedule.interval == "daily"

    def test_repo_root_config_yaml_is_valid_as_shipped(self) -> None:
        config = PipelineConfig.load()

        assert isinstance(config, PipelineConfig)
        assert config.data_sources

    def test_pipeline_config_reexported_from_pipeline_package(self) -> None:
        from backend.pipeline.config import PipelineConfig as ReExported

        assert ReExported is PipelineConfig


class TestInvalidConfig:
    def test_missing_file_raises_configuration_error(self, tmp_path: Path) -> None:
        missing = tmp_path / "nope.yaml"

        with pytest.raises(ConfigurationError, match="not found"):
            PipelineConfig.load(missing)

    def test_directory_path_raises_configuration_error(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigurationError, match="could not be read"):
            PipelineConfig.load(tmp_path)

    def test_non_utf8_file_raises_configuration_error(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_bytes(b"\xff\xfe invalid utf-8 \xff")

        with pytest.raises(ConfigurationError, match="could not be read"):
            PipelineConfig.load(path)

    def test_malformed_yaml_raises_configuration_error(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("data_sources: [unclosed", encoding="utf-8")

        with pytest.raises(ConfigurationError, match="not valid YAML"):
            PipelineConfig.load(path)

    def test_non_mapping_top_level_raises_configuration_error(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("- just\n- a\n- list\n", encoding="utf-8")

        with pytest.raises(ConfigurationError, match="mapping"):
            PipelineConfig.load(path)

    @pytest.mark.parametrize("missing_field", ["data_sources", "report_schedule"])
    def test_missing_required_field_names_the_field(
        self, config_path: Path, missing_field: str
    ) -> None:
        _write(config_path, {missing_field: None})

        with pytest.raises(ConfigurationError, match=missing_field):
            PipelineConfig.load(config_path)

    def test_pydantic_validation_error_never_escapes(self, config_path: Path) -> None:
        import pydantic

        _write(config_path, {"data_sources": None})

        with pytest.raises(ConfigurationError) as excinfo:
            PipelineConfig.load(config_path)
        assert not isinstance(excinfo.value, pydantic.ValidationError)

    def test_empty_data_sources_rejected(self, config_path: Path) -> None:
        _write(config_path, {"data_sources": []})

        with pytest.raises(ConfigurationError, match="data_sources"):
            PipelineConfig.load(config_path)

    def test_invalid_cron_expression_rejected(self, config_path: Path) -> None:
        _write(config_path, {"report_schedule": {"cron": "not a cron"}})

        with pytest.raises(ConfigurationError, match="cron"):
            PipelineConfig.load(config_path)

    def test_interval_and_cron_together_rejected(self, config_path: Path) -> None:
        _write(config_path, {"report_schedule": {"interval": "daily", "cron": "0 6 * * 1"}})

        with pytest.raises(ConfigurationError, match="exactly one"):
            PipelineConfig.load(config_path)

    def test_empty_schedule_rejected(self, config_path: Path) -> None:
        _write(config_path, {"report_schedule": {}})

        with pytest.raises(ConfigurationError, match="report_schedule"):
            PipelineConfig.load(config_path)

    def test_unknown_interval_rejected(self, config_path: Path) -> None:
        _write(config_path, {"report_schedule": {"interval": "hourly"}})

        with pytest.raises(ConfigurationError, match="interval"):
            PipelineConfig.load(config_path)

    @pytest.mark.parametrize("bad_threshold", [-0.15, 0, 0.0])
    def test_non_positive_threshold_rejected(
        self, config_path: Path, bad_threshold: float
    ) -> None:
        _write(config_path, {"metric_thresholds": {"revenue": bad_threshold}})

        with pytest.raises(ConfigurationError, match="metric_thresholds"):
            PipelineConfig.load(config_path)

    @pytest.mark.parametrize("non_finite", [".nan", ".inf", "-.inf"])
    def test_non_finite_threshold_rejected(self, config_path: Path, non_finite: str) -> None:
        # NaN would silently disable drift detection for the metric —
        # every downstream comparison against it evaluates False.
        _write(config_path, {})
        text = config_path.read_text(encoding="utf-8").replace(
            "revenue: 0.15", f"revenue: {non_finite}"
        )
        config_path.write_text(text, encoding="utf-8")

        with pytest.raises(ConfigurationError, match="metric_thresholds"):
            PipelineConfig.load(config_path)

    def test_malformed_email_rejected(self, config_path: Path) -> None:
        _write(config_path, {"alert_recipients": ["not-an-email"]})

        with pytest.raises(ConfigurationError, match="alert_recipients"):
            PipelineConfig.load(config_path)

    def test_unknown_top_level_key_rejected(self, config_path: Path) -> None:
        _write(config_path, {"data_surces": ["typo.csv"]})

        with pytest.raises(ConfigurationError, match="data_surces"):
            PipelineConfig.load(config_path)

    def test_non_string_top_level_key_raises_configuration_error(
        self, config_path: Path
    ) -> None:
        # YAML-1.1 pitfall: `on:`, `no:`, `123:` parse to bool/int keys,
        # which would crash cls(**data) with a raw TypeError.
        with config_path.open("a", encoding="utf-8") as handle:
            handle.write("\n123: oops\n")

        with pytest.raises(ConfigurationError, match="123"):
            PipelineConfig.load(config_path)


class TestSecretsFromEnv:
    def test_smtp_settings_sourced_from_environment(
        self, config_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("SMTP_USERNAME", "alerts@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", SECRET_MARKER)
        monkeypatch.setenv("SMTP_FROM", "alerts@example.com")

        config = PipelineConfig.load(config_path)

        assert config.smtp.host == "smtp.example.com"
        assert config.smtp.port == 587
        assert config.smtp.username == "alerts@example.com"
        assert config.smtp.password == SECRET_MARKER
        assert config.smtp.from_address == "alerts@example.com"
        # The secret exists only in env — never in the YAML on disk.
        assert SECRET_MARKER not in config_path.read_text(encoding="utf-8")

    def test_smtp_unset_yields_none_fields(
        self, config_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        for var in ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM"):
            monkeypatch.delenv(var, raising=False)

        config = PipelineConfig.load(config_path)

        assert config.smtp == SmtpSettings()
        assert config.smtp.password is None

    def test_smtp_section_in_yaml_is_rejected(self, config_path: Path) -> None:
        _write(config_path, {"smtp": {"password": SECRET_MARKER}})

        with pytest.raises(ConfigurationError, match="environment variables") as excinfo:
            PipelineConfig.load(config_path)
        # The refusal message must not echo the secret back.
        assert SECRET_MARKER not in str(excinfo.value)

    def test_non_numeric_smtp_port_raises_configuration_error(
        self, config_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_PORT", "not-a-port")

        # The message must blame the env var, not config.yaml, and must
        # not echo the (potentially secret) env value.
        with pytest.raises(ConfigurationError, match="SMTP_PORT") as excinfo:
            PipelineConfig.load(config_path)
        assert "not-a-port" not in str(excinfo.value)
        assert "config.yaml" not in str(excinfo.value)


class TestReload:
    def test_reload_reflects_on_disk_changes(self, config_path: Path) -> None:
        first = PipelineConfig.load(config_path)
        assert first.threshold_for("revenue") == 0.15
        assert first.report_schedule.interval == "weekly"

        _write(
            config_path,
            {
                "metric_thresholds": {"revenue": 0.30},
                "report_schedule": {"interval": "daily"},
                "alert_recipients": ["ops@example.com", "oncall@example.com"],
            },
        )
        second = PipelineConfig.load(config_path)

        assert second.threshold_for("revenue") == 0.30
        assert second.report_schedule.interval == "daily"
        assert len(second.alert_recipients) == 2
        # First instance is untouched — load() returns fresh instances.
        assert first.threshold_for("revenue") == 0.15


class TestObservability:
    def test_config_loaded_event_emitted_without_secrets(
        self, config_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SMTP_PASSWORD", SECRET_MARKER)
        monkeypatch.setenv("SMTP_USERNAME", "smtp-user-secretish")

        with structlog.testing.capture_logs() as captured:
            PipelineConfig.load(config_path)

        events = [entry for entry in captured if entry["event"] == "config_loaded"]
        assert len(events) == 1
        payload = events[0]

        assert payload["schedule"] == "weekly"
        assert payload["threshold_keys"] == ["revenue", "units_sold"]
        assert payload["recipient_count"] == 1
        assert payload["output_format"] == "docx"

        flattened = repr(payload)
        assert SECRET_MARKER not in flattened
        assert "smtp-user-secretish" not in flattened
        # Recipient addresses are PII-adjacent — count only, never the list.
        assert "ops@example.com" not in flattened


class TestScheduleConfigUnit:
    def test_describe_interval(self) -> None:
        assert ScheduleConfig(interval="daily").describe() == "daily"

    def test_valid_cron_standalone(self) -> None:
        assert ScheduleConfig(cron="*/5 * * * *").cron == "*/5 * * * *"
