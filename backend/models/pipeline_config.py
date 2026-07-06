"""Pipeline configuration contract (Story 2.1).

Defines the Pydantic v2 models for the user-facing ``config.yaml`` at the
project root: data sources, report schedule, per-metric drift thresholds,
alert recipients, and output settings. :meth:`PipelineConfig.load` is the
single entry point every agent uses — it re-reads and re-validates the file
on every call, which is what makes runtime config changes (FR10) visible to
scheduled agents on their next run without a process restart.

Secrets discipline: SMTP credentials and API keys are sourced from the
environment (``.env`` in dev via python-dotenv) and surface on
:class:`SmtpSettings`. They are never read from ``config.yaml`` —
:meth:`PipelineConfig.load` rejects an ``smtp:`` section explicitly, and
``extra="forbid"`` rejects every other unknown key, so the YAML can never
become a silent secret sink.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Literal

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

# Fractional change applied to any metric without an explicit entry in
# ``metric_thresholds`` (0.15 == ±15%). Consumed by the Drift Engine (2.3)
# and Monitoring Agent (2.4) via :meth:`PipelineConfig.threshold_for`.
DEFAULT_THRESHOLD: float = 0.15

_CONFIG_FILENAME = "config.yaml"

# backend/models/pipeline_config.py -> backend/models -> backend -> repo root
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# SmtpSettings field -> environment variable that sources it. Used both to
# read the values and to name the offending variable in error messages.
_SMTP_ENV_VARS: tuple[tuple[str, str], ...] = (
    ("host", "SMTP_HOST"),
    ("port", "SMTP_PORT"),
    ("username", "SMTP_USERNAME"),
    ("password", "SMTP_PASSWORD"),
    ("from_addr", "SMTP_FROM"),
)


class ScheduleConfig(BaseModel):
    """Report cadence: a named interval OR a cron expression, never both."""

    model_config = ConfigDict(extra="forbid")

    interval: Literal["daily", "weekly", "monthly"] | None = None
    cron: str | None = None

    @field_validator("cron")
    @classmethod
    def _cron_must_parse(cls, value: str | None) -> str | None:
        if value is not None and not croniter.is_valid(value):
            raise ValueError(f"invalid cron expression: {value!r}")
        return value

    @model_validator(mode="after")
    def _exactly_one_of_interval_or_cron(self) -> ScheduleConfig:
        if (self.interval is None) == (self.cron is None):
            raise ValueError(
                "report_schedule requires exactly one of 'interval' "
                "(daily|weekly|monthly) or 'cron'"
            )
        return self

    def describe(self) -> str:
        """Loggable one-token summary — the interval name or cron string."""
        return self.cron if self.cron is not None else str(self.interval)


class OutputConfig(BaseModel):
    """Report rendering target."""

    model_config = ConfigDict(extra="forbid")

    format: Literal["docx", "pdf"] = "docx"
    output_dir: Path = Path("output/")


class SmtpSettings(BaseModel):
    """SMTP delivery settings, sourced from environment variables ONLY.

    ``password`` is a :class:`~pydantic.SecretStr` so it renders as
    ``'**********'`` in reprs, logs, and error messages; callers that
    actually send mail (Story 2.4) unwrap it with ``get_secret_value()``.
    """

    model_config = ConfigDict(extra="forbid")

    host: str | None = None
    port: int = 587
    username: str | None = None
    password: SecretStr | None = None
    from_addr: str | None = None

    @classmethod
    def from_env(cls) -> SmtpSettings:
        """Build from ``SMTP_*`` environment variables (unset -> defaults)."""
        values: dict[str, str] = {}
        for field, env_var in _SMTP_ENV_VARS:
            raw = os.environ.get(env_var)
            if raw is not None and raw != "":
                values[field] = raw
        return cls(**values)


class PipelineConfig(BaseModel):
    """Root configuration for the Phase 2 automation agents.

    Consumers: Drift Engine (thresholds), Reporting Agent (data sources,
    schedule, output — reloaded per scheduled run), Monitoring Agent
    (thresholds, recipients, SMTP).
    """

    model_config = ConfigDict(extra="forbid")

    data_sources: list[Path] = Field(min_length=1)
    report_schedule: ScheduleConfig
    metric_thresholds: dict[str, float] = Field(default_factory=dict)
    alert_recipients: list[EmailStr] = Field(default_factory=list)
    output: OutputConfig = Field(default_factory=OutputConfig)
    # Populated from env by load(); excluded from serialization and repr so a
    # round-tripped config never writes credentials to disk and a logged
    # config object never prints SMTP host/username.
    smtp: SmtpSettings = Field(default_factory=SmtpSettings, exclude=True, repr=False)

    @field_validator("data_sources", mode="before")
    @classmethod
    def _sources_must_not_be_blank(cls, value: object) -> object:
        # An empty string would coerce to Path('.') — turning a YAML typo
        # into "ingest the repo root". Reject it before Path conversion.
        if isinstance(value, list):
            for idx, entry in enumerate(value):
                if isinstance(entry, str) and not entry.strip():
                    raise ValueError(f"data_sources[{idx}] must not be empty")
        return value

    @field_validator("metric_thresholds")
    @classmethod
    def _thresholds_must_be_positive(cls, value: dict[str, float]) -> dict[str, float]:
        for metric, threshold in value.items():
            # isfinite guards NaN (every comparison False -> drift alerts for
            # that metric would silently never fire) and inf (never alert).
            if not math.isfinite(threshold) or threshold <= 0:
                raise ValueError(
                    f"metric_thresholds[{metric!r}] must be a positive finite "
                    f"number, got {threshold}"
                )
        return value

    def threshold_for(self, metric: str) -> float:
        """Fractional change threshold for *metric* (default ±15%)."""
        return self.metric_thresholds.get(metric, DEFAULT_THRESHOLD)

    @classmethod
    def load(cls, path: str | Path | None = None) -> PipelineConfig:
        """Read, validate, and return the config as a typed instance.

        Stateless by design: re-reads and re-validates the file on every
        call (FR10 — a scheduled agent picks up on-disk edits on its next
        run). Raises :class:`ConfigurationError` on any failure — Pydantic
        ``ValidationError`` never escapes uncaught.
        """
        config_path = Path(path) if path is not None else _PROJECT_ROOT / _CONFIG_FILENAME

        # Dev convenience: hydrate os.environ from the repo-root .env (no-op
        # when absent; never overrides variables already set in the real
        # environment — which also means editing .env in a long-lived process
        # does not rotate already-loaded credentials; config.yaml hot-reloads,
        # .env does not).
        load_dotenv(_PROJECT_ROOT / ".env")

        try:
            raw_text = config_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ConfigurationError(f"config file not found: {config_path}") from exc
        except OSError as exc:
            raise ConfigurationError(f"config file unreadable: {config_path}: {exc}") from exc

        try:
            # safe_load only — yaml.load without a safe loader deserializes
            # arbitrary Python objects (injection vector, NFR4). JSON is a
            # strict subset of YAML, so a .json config parses here too.
            raw = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            raise ConfigurationError(f"config file is not valid YAML: {config_path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise ConfigurationError(
                f"config root must be a mapping, got {type(raw).__name__}: {config_path}"
            )

        if "smtp" in raw:
            raise ConfigurationError(
                f"'smtp' section is not allowed in {config_path}: SMTP settings "
                "(including credentials) are sourced ONLY from SMTP_* environment "
                "variables (.env in dev), never from the config file"
            )

        try:
            smtp = SmtpSettings.from_env()
        except ValidationError as exc:
            env_vars = dict(_SMTP_ENV_VARS)
            problems = "; ".join(
                f"{env_vars.get(str(err['loc'][0]), err['loc'][0])}: {err['msg']}"
                for err in exc.errors()
            )
            raise ConfigurationError(f"invalid SMTP environment settings: {problems}") from exc

        try:
            config = cls(**raw, smtp=smtp)
        except ValidationError as exc:
            raise ConfigurationError(_describe_validation_error(exc, config_path)) from exc
        except TypeError as exc:
            # cls(**raw) with a non-str key (e.g. YAML `1: x` at root).
            raise ConfigurationError(f"invalid config structure: {config_path}: {exc}") from exc

        # Summary only — never SMTP credentials, API keys, or recipient
        # addresses (PII-adjacent: log the count, not the list).
        structlog.get_logger(__name__).info(
            "config_loaded",
            config_path=str(config_path),
            data_source_count=len(config.data_sources),
            schedule=config.report_schedule.describe(),
            threshold_keys=sorted(config.metric_thresholds),
            recipient_count=len(config.alert_recipients),
            output_format=config.output.format,
        )
        return config


def _describe_validation_error(exc: ValidationError, config_path: Path) -> str:
    """Flatten a Pydantic ValidationError into field-naming prose (AC2)."""
    problems = "; ".join(
        f"{'.'.join(str(part) for part in err['loc']) or '<root>'}: {err['msg']}"
        for err in exc.errors()
    )
    return f"invalid configuration in {config_path}: {problems}"
