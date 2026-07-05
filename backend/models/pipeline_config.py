"""Pipeline configuration Pydantic models — Story 2.1.

Defines the typed contract for ``config.yaml`` (data sources, report
schedule, per-metric drift thresholds, alert recipients, output settings)
plus the SMTP settings sourced from environment variables. Secrets never
live in ``config.yaml`` — see :class:`SmtpSettings`.

:class:`PipelineConfig` is the single entry point every agent uses:
``PipelineConfig.load()`` reads, validates, and returns a typed instance.
The loader is stateless (re-reads the file on every call) so a scheduled
agent picks up edits without a process restart (FR10).

Schema note: ``metric_thresholds``, ``data_sources``, and
``alert_recipients`` are flat YAML structures (a dict and two lists — see
the canonical ``config.yaml`` in Dev Notes / Story 2.1). Wrapping them in
their own single-field models would force a nested YAML shape
(``alert_recipients: {recipients: [...]}``) that contradicts the
documented config format, so they are plain typed fields on
:class:`PipelineConfig` with field validators instead.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import structlog
import yaml
from croniter import croniter
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, EmailStr, Field, ValidationError, field_validator, model_validator

from backend.errors.exceptions import ConfigurationError

DEFAULT_THRESHOLD = 0.15
DEFAULT_CONFIG_FILENAME = "config.yaml"

_logger = structlog.get_logger()


class ScheduleConfig(BaseModel):
    """Report schedule — either a named interval or a cron expression.

    Exactly one of ``interval`` / ``cron`` must be set. ``cron`` is
    validated with :mod:`croniter` at load time so a malformed expression
    fails fast as a :class:`ConfigurationError` rather than at the first
    scheduled run.
    """

    model_config = ConfigDict(extra="forbid")

    interval: Literal["daily", "weekly", "monthly"] | None = None
    cron: str | None = None

    @model_validator(mode="after")
    def _validate_exactly_one(self) -> "ScheduleConfig":
        if (self.interval is None) == (self.cron is None):
            raise ValueError(
                "report_schedule must set exactly one of 'interval' or 'cron'"
            )
        if self.cron is not None and not croniter.is_valid(self.cron):
            raise ValueError(f"report_schedule.cron is not a valid cron expression: {self.cron!r}")
        return self


class OutputConfig(BaseModel):
    """Report output settings."""

    model_config = ConfigDict(extra="forbid")

    format: Literal["docx", "pdf"] = "docx"
    output_dir: str = "output/"


class SmtpSettings(BaseModel):
    """SMTP credentials — sourced from environment variables only.

    Never populated from ``config.yaml``; see :meth:`PipelineConfig.load`.
    All fields are optional so a config with no alert delivery configured
    yet does not fail validation.
    """

    model_config = ConfigDict(extra="forbid")

    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    from_addr: str | None = None


class PipelineConfig(BaseModel):
    """Root pipeline configuration — the typed contract for ``config.yaml``.

    Load with :meth:`load`, never by constructing directly from untrusted
    input — the classmethod is what enforces the YAML-safe-parse and
    env-secret-merge discipline.
    """

    model_config = ConfigDict(extra="forbid")

    data_sources: list[str] = Field(min_length=1)
    report_schedule: ScheduleConfig
    metric_thresholds: dict[str, float] = Field(default_factory=dict)
    alert_recipients: list[EmailStr] = Field(default_factory=list)
    output: OutputConfig = Field(default_factory=OutputConfig)
    smtp: SmtpSettings = Field(default_factory=SmtpSettings)

    @field_validator("metric_thresholds")
    @classmethod
    def _validate_thresholds_positive(cls, thresholds: dict[str, float]) -> dict[str, float]:
        for metric, value in thresholds.items():
            if value <= 0:
                raise ValueError(f"metric_thresholds.{metric} must be > 0, got {value}")
        return thresholds

    def threshold_for(self, metric: str) -> float:
        """Return the drift threshold for ``metric``, or the default."""
        return self.metric_thresholds.get(metric, DEFAULT_THRESHOLD)

    @classmethod
    def load(cls, path: str | Path | None = None) -> "PipelineConfig":
        """Read, validate, and return a typed :class:`PipelineConfig`.

        Re-reads and re-validates the file on every call (FR10 — a
        scheduled agent picks up edits with no process restart or module
        reimport). Secrets (SMTP credentials) are sourced exclusively from
        environment variables via ``.env``, never from the YAML file.

        Raises
        ------
        ConfigurationError
            If the file is missing, is not valid YAML, or fails schema
            validation. ``pydantic.ValidationError`` never escapes this
            method uncaught.
        """
        config_path = Path(path) if path is not None else Path(DEFAULT_CONFIG_FILENAME)

        try:
            raw_text = config_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ConfigurationError(f"Configuration file not found: {config_path}") from exc

        try:
            # yaml.safe_load only — never yaml.load, which permits arbitrary
            # object deserialization (NFR4 input sanitization). JSON is a
            # strict subset of YAML so this also parses .json config files.
            raw_data = yaml.safe_load(raw_text) or {}
        except yaml.YAMLError as exc:
            raise ConfigurationError(f"Configuration file is not valid YAML: {config_path}: {exc}") from exc

        if not isinstance(raw_data, dict):
            raise ConfigurationError(f"Configuration file must define a top-level mapping: {config_path}")

        load_dotenv()
        raw_data["smtp"] = {
            "host": os.environ.get("SMTP_HOST"),
            "port": os.environ.get("SMTP_PORT"),
            "username": os.environ.get("SMTP_USERNAME"),
            "password": os.environ.get("SMTP_PASSWORD"),
            "from_addr": os.environ.get("SMTP_FROM"),
        }

        try:
            config = cls.model_validate(raw_data)
        except ValidationError as exc:
            raise ConfigurationError(f"Configuration is invalid: {config_path}: {exc}") from exc

        _logger.info(
            "config_loaded",
            schedule=config.report_schedule.interval or "cron",
            threshold_keys=sorted(config.metric_thresholds.keys()),
            recipient_count=len(config.alert_recipients),
            output_format=config.output.format,
        )
        return config
