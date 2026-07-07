"""Pipeline configuration contract (Story 2.1).

Defines the Pydantic v2 schema for the user-facing ``config.yaml`` at the
project root and the :meth:`PipelineConfig.load` entry point every agent
uses to read it. The schema is consumed across Epic 2: the Drift Engine
reads ``metric_thresholds``, the Reporting Agent reads ``data_sources`` +
``report_schedule`` + ``output`` (re-calling :meth:`PipelineConfig.load`
at the start of each scheduled run for hot-reload), and the Monitoring
Agent reads ``metric_thresholds`` + ``alert_recipients`` + SMTP settings.

Secrets discipline (NFR3): ``config.yaml`` holds non-secret structure
only. SMTP credentials come exclusively from environment variables
(``.env`` in dev via python-dotenv) and are surfaced on
:class:`SmtpSettings`. A ``smtp`` key in the YAML is rejected outright.

All load failures — missing file, malformed YAML, schema violations —
raise :class:`backend.errors.exceptions.ConfigurationError`; a raw
:class:`pydantic.ValidationError` never escapes the loader.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Annotated, ClassVar, Literal

import structlog
import yaml
from croniter import croniter
from dotenv import load_dotenv
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    ValidationError,
    field_validator,
    model_validator,
)

from backend.errors.exceptions import ConfigurationError

#: Fractional change threshold applied to any metric without an explicit
#: entry in ``metric_thresholds`` (0.15 == ±15%).
DEFAULT_THRESHOLD = 0.15

_DEFAULT_CONFIG_FILENAME = "config.yaml"

#: Defense-in-depth cap on config file size. safe_load still expands YAML
#: anchors/aliases, so an adversarial config could balloon in memory; a
#: legitimate config is a few KB.
_MAX_CONFIG_BYTES = 1_000_000

# backend/models/pipeline_config.py -> backend/models -> backend -> repo root.
# Valid for an in-repo checkout (the only supported deployment today);
# callers running elsewhere pass an explicit path to load().
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class OutputFormat(str, Enum):
    """Report output formats the render stage supports.

    Single source of truth shared by the config schema and the pipeline
    orchestrator (which re-exports it for the CLI).
    """

    docx = "docx"
    pdf = "pdf"


class ScheduleConfig(BaseModel):
    """Report schedule: a named interval XOR a cron expression."""

    model_config = ConfigDict(extra="forbid")

    interval: Literal["daily", "weekly", "monthly"] | None = None
    cron: str | None = None

    @model_validator(mode="after")
    def _exactly_one_of_interval_or_cron(self) -> ScheduleConfig:
        if (self.interval is None) == (self.cron is None):
            raise ValueError(
                "report_schedule requires exactly one of 'interval' or 'cron'"
            )
        if self.cron is not None and not croniter.is_valid(self.cron):
            raise ValueError(f"report_schedule.cron is not a valid cron expression: {self.cron!r}")
        return self

    def describe(self) -> str:
        """Loggable one-token summary, e.g. ``weekly`` or ``cron:0 6 * * 1``."""
        return self.interval if self.interval is not None else f"cron:{self.cron}"


class OutputConfig(BaseModel):
    """Report rendering output settings."""

    model_config = ConfigDict(extra="forbid")

    format: OutputFormat = OutputFormat.docx
    output_dir: Path = Path("output")


class SmtpSettings(BaseModel):
    """SMTP delivery settings, sourced from environment variables ONLY.

    Populated by :meth:`from_env` (also the field's default factory, so a
    directly-constructed :class:`PipelineConfig` picks up the environment
    too); never parsed out of ``config.yaml``. ``host``/``username``/
    ``password``/``from_address`` stay ``None`` when the corresponding
    ``SMTP_*`` variables are unset or blank — alert delivery (Story 2.4)
    validates presence at send time, not at config load.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    host: str | None = None
    port: int = Field(default=587, ge=1, le=65535)
    username: str | None = None
    # SecretStr masks the value in repr()/model_dump(), so a config object
    # embedded in a log line or exception can never print the password;
    # Story 2.4 calls .get_secret_value() at SMTP send time.
    password: SecretStr | None = None
    from_address: str | None = None

    @field_validator("host", "username", "from_address")
    @classmethod
    def _blank_to_none(cls, value: str | None) -> str | None:
        # After str_strip_whitespace, a whitespace-only env value is "" —
        # treat it as unset rather than as a configured host/credential.
        return value or None

    _ENV_VARS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("host", "SMTP_HOST"),
        ("port", "SMTP_PORT"),
        ("username", "SMTP_USERNAME"),
        ("password", "SMTP_PASSWORD"),
        ("from_address", "SMTP_FROM"),
    )

    @classmethod
    def from_env(cls) -> SmtpSettings:
        raw = {
            field: value
            for field, var in cls._ENV_VARS
            if (value := os.environ.get(var)) is not None and value.strip()
        }
        try:
            return cls.model_validate(raw)
        except ValidationError as exc:
            # include_input=False in the summary keeps secret values out
            # of the error message.
            raise ConfigurationError(
                f"invalid SMTP_* environment settings: {_summarize_validation_error(exc)}"
            ) from exc


class PipelineConfig(BaseModel):
    """Root configuration for the Phase 2 automation pipeline.

    Load via :meth:`load` — never by parsing YAML ad-hoc. ``load()`` is
    stateless: it re-reads and re-validates the file on every call, which
    is the FR10 runtime-reload mechanism (a scheduled agent picks up disk
    edits on its next run without a process restart).
    """

    model_config = ConfigDict(extra="forbid")

    data_sources: list[Path] = Field(min_length=1)
    report_schedule: ScheduleConfig
    metric_thresholds: dict[str, Annotated[float, Field(gt=0)]] = Field(default_factory=dict)
    alert_recipients: list[EmailStr]
    output: OutputConfig = Field(default_factory=OutputConfig)
    smtp: SmtpSettings = Field(default_factory=SmtpSettings.from_env)

    def threshold_for(self, metric: str) -> float:
        """Fractional change threshold for ``metric`` (falls back to 0.15)."""
        return self.metric_thresholds.get(metric, DEFAULT_THRESHOLD)

    @classmethod
    def load(cls, path: str | Path | None = None) -> PipelineConfig:
        """Read, validate, and return the pipeline configuration.

        ``path`` defaults to ``config.yaml`` at the project root. YAML and
        JSON are both accepted — JSON is a strict subset of YAML, so
        ``yaml.safe_load`` parses ``.json`` files too; no separate branch
        is needed. Raises :class:`ConfigurationError` on any failure.
        """
        config_path = Path(path) if path is not None else _PROJECT_ROOT / _DEFAULT_CONFIG_FILENAME

        # .env for local development; real env vars always win (dotenv
        # does not override variables that are already set). Path is
        # pinned to the project root so a .env planted in an ancestor
        # directory can never be picked up by dotenv's default walk.
        load_dotenv(_PROJECT_ROOT / ".env")

        try:
            raw_text = config_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ConfigurationError(f"config file not found: {config_path}") from exc
        except OSError as exc:
            raise ConfigurationError(f"config file could not be read: {config_path}: {exc}") from exc

        if len(raw_text.encode("utf-8")) > _MAX_CONFIG_BYTES:
            raise ConfigurationError(
                f"config file exceeds {_MAX_CONFIG_BYTES} bytes: {config_path}"
            )

        try:
            raw = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            # Only the parser's problem description and position — never
            # str(exc), which embeds a snippet of the file content.
            position = getattr(exc, "problem_mark", None)
            problem = getattr(exc, "problem", None) or "parse error"
            location = f" (line {position.line + 1}, column {position.column + 1})" if position else ""
            raise ConfigurationError(
                f"config file is not valid YAML/JSON: {config_path}: {problem}{location}"
            ) from exc

        if not isinstance(raw, dict):
            raise ConfigurationError(
                f"config file must contain a mapping of settings, got "
                f"{type(raw).__name__}: {config_path}"
            )
        if "smtp" in raw:
            raise ConfigurationError(
                "smtp settings are environment-only (.env) and must not appear "
                f"in {config_path.name}; remove the 'smtp' key"
            )

        try:
            config = cls.model_validate(raw)
        except ValidationError as exc:
            raise ConfigurationError(
                f"invalid configuration in {config_path}: {_summarize_validation_error(exc)}"
            ) from exc

        # Summary only — never SMTP credentials, API keys, or recipient
        # addresses (PII-adjacent: log the count, not the list).
        structlog.get_logger().info(
            "config_loaded",
            config_path=str(config_path),
            schedule=config.report_schedule.describe(),
            threshold_keys=sorted(config.metric_thresholds),
            recipient_count=len(config.alert_recipients),
            output_format=config.output.format.value,
            data_source_count=len(config.data_sources),
        )
        return config


def _summarize_validation_error(exc: ValidationError) -> str:
    """Flatten a ValidationError into ``field: message`` lines naming each offender."""
    parts = []
    for error in exc.errors(include_input=False, include_url=False):
        location = ".".join(str(loc) for loc in error["loc"]) or "<root>"
        parts.append(f"{location}: {error['msg']}")
    return "; ".join(parts)
