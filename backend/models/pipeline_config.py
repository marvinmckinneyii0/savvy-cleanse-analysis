"""Pipeline configuration contract (Story 2.1).

Defines the typed configuration surface every Phase 2 agent consumes:
``data_sources`` (what to analyze), ``report_schedule`` (when to run),
``metric_thresholds`` (drift sensitivity), ``alert_recipients`` (who to
notify), and ``output`` settings (how to render). The on-disk source of
truth is ``config.yaml`` at the project root; secrets (SMTP credentials)
are sourced exclusively from environment variables, never from YAML.

:meth:`PipelineConfig.load` is stateless — it re-reads and re-validates
the file on every call, which is the hot-reload mechanism scheduled
agents rely on (FR10): the next run picks up edited thresholds,
schedules, and recipients without a process restart.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import structlog
import yaml
from croniter import croniter
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, EmailStr, ValidationError, field_validator, model_validator

from backend.errors.exceptions import ConfigurationError

# Fractional change applied to any metric without an explicit entry in
# ``metric_thresholds`` (0.15 == ±15%).
DEFAULT_THRESHOLD = 0.15

_DEFAULT_CONFIG_FILENAME = "config.yaml"

# backend/models/pipeline_config.py -> backend/models -> backend -> repo root
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

_SMTP_ENV_VARS = ("SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM")


class ScheduleConfig(BaseModel):
    """When scheduled agents run: a named interval XOR a cron expression."""

    model_config = ConfigDict(extra="forbid")

    interval: Literal["daily", "weekly", "monthly"] | None = None
    cron: str | None = None

    @model_validator(mode="after")
    def _exactly_one_of_interval_or_cron(self) -> ScheduleConfig:
        if (self.interval is None) == (self.cron is None):
            raise ValueError("report_schedule requires exactly one of 'interval' or 'cron'")
        if self.cron is not None and not croniter.is_valid(self.cron):
            raise ValueError(f"report_schedule.cron is not a valid cron expression: {self.cron!r}")
        return self

    def describe(self) -> str:
        """Human-readable schedule summary for logging."""
        return self.interval if self.interval is not None else f"cron:{self.cron}"


class OutputConfig(BaseModel):
    """Report rendering settings."""

    model_config = ConfigDict(extra="forbid")

    format: Literal["docx", "pdf"] = "docx"
    output_dir: Path = Path("output/")


class SmtpSettings(BaseModel):
    """SMTP delivery settings, sourced ONLY from environment variables.

    ``config.yaml`` must never contain these — the loader rejects an
    ``smtp`` key in the YAML outright. All fields are optional because
    alert delivery is Story 2.4's runtime concern; 2.1 only surfaces the
    typed values.
    """

    model_config = ConfigDict(extra="forbid")

    host: str | None = None
    port: int = 587
    username: str | None = None
    password: str | None = None
    from_address: str | None = None

    @classmethod
    def from_env(cls) -> SmtpSettings:
        """Build from ``SMTP_*`` environment variables (unset -> defaults)."""
        values: dict[str, str] = {}
        env_to_field = {
            "SMTP_HOST": "host",
            "SMTP_PORT": "port",
            "SMTP_USERNAME": "username",
            "SMTP_PASSWORD": "password",
            "SMTP_FROM": "from_address",
        }
        for env_var, field in env_to_field.items():
            raw = os.environ.get(env_var)
            if raw is not None and raw != "":
                values[field] = raw
        return cls.model_validate(values)


class PipelineConfig(BaseModel):
    """Root Phase 2 configuration, loaded from ``config.yaml`` + env.

    Consumers: the Drift Engine (2.2) reads ``metric_thresholds``, the
    Reporting Agent (2.3) reads ``data_sources``/``report_schedule``/
    ``output`` and calls :meth:`load` at the start of every scheduled
    run, the Monitoring Agent (2.4) reads ``metric_thresholds``,
    ``alert_recipients`` and ``smtp``.
    """

    model_config = ConfigDict(extra="forbid")

    data_sources: list[Path]
    report_schedule: ScheduleConfig
    metric_thresholds: dict[str, float] = {}
    alert_recipients: list[EmailStr] = []
    output: OutputConfig = OutputConfig()
    smtp: SmtpSettings = SmtpSettings()

    @field_validator("data_sources")
    @classmethod
    def _data_sources_non_empty(cls, value: list[Path]) -> list[Path]:
        if not value:
            raise ValueError("data_sources must list at least one file path or directory")
        return value

    @field_validator("metric_thresholds")
    @classmethod
    def _thresholds_positive(cls, value: dict[str, float]) -> dict[str, float]:
        for metric, threshold in value.items():
            if threshold <= 0:
                raise ValueError(
                    f"metric_thresholds.{metric} must be > 0, got {threshold}"
                )
        return value

    def threshold_for(self, metric: str) -> float:
        """Per-metric fractional threshold, falling back to ``DEFAULT_THRESHOLD``."""
        return self.metric_thresholds.get(metric, DEFAULT_THRESHOLD)

    @classmethod
    def load(cls, path: str | Path | None = None) -> PipelineConfig:
        """Read, validate, and return the pipeline configuration.

        Stateless by design: every call re-reads the file so scheduled
        agents pick up on-disk edits on their next run (FR10). Secrets
        are merged from ``SMTP_*`` environment variables (``.env`` is
        loaded via python-dotenv first); the YAML must not contain them.

        Raises :class:`ConfigurationError` — never a bare pydantic
        ``ValidationError`` — on a missing file, malformed YAML, or any
        invalid value, with a message naming the offending field.
        """
        load_dotenv()
        resolved = Path(path) if path is not None else _PROJECT_ROOT / _DEFAULT_CONFIG_FILENAME

        try:
            text = resolved.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ConfigurationError(f"config file not found: {resolved}") from exc
        except OSError as exc:
            raise ConfigurationError(f"config file unreadable: {resolved} ({exc})") from exc

        try:
            # safe_load only — yaml.load without a safe loader deserializes
            # arbitrary Python objects (NFR4). JSON is a strict subset of
            # YAML, so a .json config parses through this same call.
            raw = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise ConfigurationError(f"config file is not valid YAML: {resolved} ({exc})") from exc

        if not isinstance(raw, dict):
            raise ConfigurationError(
                f"config file must contain a YAML mapping at the top level: {resolved}"
            )

        if "smtp" in raw:
            raise ConfigurationError(
                "smtp settings must come from environment variables (SMTP_*), never config.yaml"
            )

        try:
            config = cls.model_validate({**raw, "smtp": SmtpSettings.from_env()})
        except ValidationError as exc:
            # Re-raise with field locations + messages only. str(exc) would
            # embed offending input values, which for env-sourced fields
            # could leak secrets into logs or tracebacks.
            details = "; ".join(
                f"{'.'.join(str(part) for part in error['loc']) or '<root>'}: {error['msg']}"
                for error in exc.errors()
            )
            raise ConfigurationError(f"invalid configuration in {resolved}: {details}") from exc

        structlog.get_logger().info(
            "config_loaded",
            config_path=str(resolved),
            schedule=config.report_schedule.describe(),
            threshold_keys=sorted(config.metric_thresholds),
            recipient_count=len(config.alert_recipients),
            output_format=config.output.format,
            data_source_count=len(config.data_sources),
        )
        return config
