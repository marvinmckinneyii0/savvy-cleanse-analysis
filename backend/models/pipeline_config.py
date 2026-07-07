"""Pipeline configuration contract (Story 2.1).

Defines the Pydantic v2 models that validate ``config.yaml`` at the
project root, plus :meth:`PipelineConfig.load` — the single entry point
every Phase 2 agent uses to read configuration.

Schema consumers (design constraints, do not break):

* **Drift Engine (2.3)** reads ``metric_thresholds`` — per-column
  fractional change thresholds, resolved via :meth:`PipelineConfig.threshold_for`.
* **Reporting Agent** reads ``data_sources`` + ``report_schedule`` and
  calls :meth:`PipelineConfig.load` at the start of every scheduled run;
  ``load()`` is stateless (re-reads and re-validates on each call) so a
  config edit on disk takes effect on the next run with no restart (FR10).
* **Monitoring Agent** reads ``metric_thresholds`` + ``alert_recipients``
  and the env-sourced :class:`SmtpSettings`.

Secrets discipline (NFR3): ``config.yaml`` holds non-secret structure
only. SMTP credentials come exclusively from environment variables
(``.env`` in dev via python-dotenv). A ``smtp`` key in the YAML is
rejected outright, and the ``config_loaded`` log event carries a summary
(schedule, threshold keys, recipient *count*) — never credentials, never
the recipient list.
"""

from __future__ import annotations

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

#: Fractional change threshold applied to any metric without an explicit
#: entry in ``metric_thresholds`` (0.15 == ±15%).
DEFAULT_THRESHOLD = 0.15

#: Repo root — ``backend/models/pipeline_config.py`` → up 2 → project root.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

#: Default config file, per architecture target tree (config.yaml at root).
DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"

_logger = structlog.get_logger(__name__)


class ScheduleConfig(BaseModel):
    """Report schedule: a named interval OR a cron expression, never both."""

    model_config = ConfigDict(extra="forbid")

    interval: Literal["daily", "weekly", "monthly"] | None = None
    cron: str | None = None

    @model_validator(mode="after")
    def _exactly_one_of_interval_or_cron(self) -> "ScheduleConfig":
        if (self.interval is None) == (self.cron is None):
            raise ValueError(
                "report_schedule requires exactly one of 'interval' "
                "(daily/weekly/monthly) or 'cron'"
            )
        if self.cron is not None and not croniter.is_valid(self.cron):
            raise ValueError(f"report_schedule.cron is not a valid cron expression: {self.cron!r}")
        return self

    def describe(self) -> str:
        """Human/log-friendly one-liner, e.g. ``interval:weekly`` or ``cron:0 6 * * 1``."""
        if self.interval is not None:
            return f"interval:{self.interval}"
        return f"cron:{self.cron}"


class OutputConfig(BaseModel):
    """Report output settings."""

    model_config = ConfigDict(extra="forbid")

    format: Literal["docx", "pdf"] = "docx"
    output_dir: Path = Path("output")


class SmtpSettings(BaseModel):
    """SMTP delivery settings, sourced ONLY from environment variables.

    Never read from ``config.yaml`` — :meth:`PipelineConfig.load` rejects
    a ``smtp`` key in the YAML. All fields are optional because alert
    delivery is not configured in every environment (it is exercised by
    the Monitoring Agent story). ``password`` is a :class:`SecretStr` so
    accidental ``repr``/log output shows ``**********``.
    """

    model_config = ConfigDict(extra="forbid")

    host: str | None = None
    port: int = 587
    username: str | None = None
    password: SecretStr | None = None
    from_addr: str | None = None

    @staticmethod
    def env_values() -> dict[str, str]:
        """Raw ``SMTP_*`` environment values keyed by field name.

        Returned unvalidated so :meth:`PipelineConfig.load` can validate
        them alongside the YAML — a malformed ``SMTP_PORT`` then surfaces
        as a :class:`ConfigurationError` naming ``smtp.port``, not a bare
        ``ValidationError``. Unset/empty vars are omitted (field defaults
        apply).
        """
        raw: dict[str, str] = {}
        for field, env_var in (
            ("host", "SMTP_HOST"),
            ("port", "SMTP_PORT"),
            ("username", "SMTP_USERNAME"),
            ("password", "SMTP_PASSWORD"),
            ("from_addr", "SMTP_FROM"),
        ):
            value = os.environ.get(env_var)
            if value:
                raw[field] = value
        return raw


class PipelineConfig(BaseModel):
    """Root configuration for the Phase 2 pipeline agents.

    Mirrors the shape of ``config.yaml`` exactly (``extra="forbid"`` —
    an unknown or misspelled key is a validation error, not a silent
    no-op), plus the env-sourced ``smtp`` block injected by :meth:`load`.
    """

    model_config = ConfigDict(extra="forbid")

    data_sources: list[Path] = Field(min_length=1)
    report_schedule: ScheduleConfig
    metric_thresholds: dict[str, float] = Field(default_factory=dict)
    alert_recipients: list[EmailStr] = Field(default_factory=list)
    output: OutputConfig = Field(default_factory=OutputConfig)
    smtp: SmtpSettings = Field(default_factory=SmtpSettings)

    @field_validator("metric_thresholds")
    @classmethod
    def _thresholds_positive(cls, value: dict[str, float]) -> dict[str, float]:
        for metric, threshold in value.items():
            if threshold <= 0:
                raise ValueError(
                    f"metric_thresholds[{metric!r}] must be > 0, got {threshold}"
                )
        return value

    def threshold_for(self, metric: str) -> float:
        """Per-metric fractional change threshold, falling back to 0.15."""
        return self.metric_thresholds.get(metric, DEFAULT_THRESHOLD)

    @classmethod
    def load(cls, path: str | Path | None = None) -> "PipelineConfig":
        """Read, validate, and return the pipeline configuration.

        Stateless by design (FR10): every call re-reads ``path`` (default:
        ``config.yaml`` at the project root) and re-validates it, so a
        scheduled agent picks up on-disk edits on its next run without a
        process restart. Keep this cheap and side-effect-free besides the
        ``config_loaded`` log event.

        SMTP secrets are merged from environment variables (``.env`` is
        loaded first via python-dotenv, which never overrides variables
        already set in the process environment).

        Raises:
            ConfigurationError: missing file, malformed YAML, schema
                violations, or secrets found in the YAML. Pydantic's
                ``ValidationError`` never escapes this method.
        """
        config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
        load_dotenv()

        try:
            raw_text = config_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ConfigurationError(f"Config file not found: {config_path}") from exc
        except OSError as exc:
            raise ConfigurationError(f"Config file unreadable: {config_path} ({exc})") from exc

        # JSON is a strict subset of YAML, so safe_load parses .json config
        # too — no separate JSON branch needed. NEVER yaml.load without a
        # safe loader (arbitrary-object deserialization; NFR4).
        try:
            raw = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            raise ConfigurationError(f"Malformed YAML in {config_path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise ConfigurationError(
                f"Config root must be a mapping, got {type(raw).__name__}: {config_path}"
            )

        # Secrets live in env only (NFR3). Reject rather than silently
        # override so a credential committed to config.yaml is caught.
        if "smtp" in raw:
            raise ConfigurationError(
                "config.yaml must not contain an 'smtp' section — SMTP settings "
                "are sourced from environment variables (see .env.example)"
            )

        raw["smtp"] = SmtpSettings.env_values()

        try:
            config = cls.model_validate(raw)
        except ValidationError as exc:
            fields = ", ".join(
                ".".join(str(part) for part in err["loc"]) or "<root>" for err in exc.errors()
            )
            raise ConfigurationError(
                f"Invalid configuration in {config_path} — offending field(s): "
                f"{fields}. Details: {exc}"
            ) from exc

        # Summary only — never SMTP credentials, never recipient addresses
        # (PII-adjacent; count is enough).
        _logger.info(
            "config_loaded",
            config_path=str(config_path),
            schedule=config.report_schedule.describe(),
            threshold_keys=sorted(config.metric_thresholds),
            recipient_count=len(config.alert_recipients),
            output_format=config.output.format,
            data_source_count=len(config.data_sources),
        )
        return config
