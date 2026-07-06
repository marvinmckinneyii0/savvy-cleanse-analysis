"""Pipeline configuration contract (Story 2.1).

Defines the typed configuration surface every Phase 2 agent consumes:
``data_sources`` (Reporting Agent), ``report_schedule`` (Reporting Agent),
``metric_thresholds`` (Drift Engine, Monitoring Agent), ``alert_recipients``
and SMTP settings (Monitoring Agent), and ``output`` rendering options.

The user-facing file is ``config.yaml`` at the project root. Secrets are
NEVER read from that file — SMTP credentials come exclusively from
environment variables (``.env`` in dev via python-dotenv).

:meth:`PipelineConfig.load` is stateless: it re-reads and re-validates the
file on every call, which is the hot-reload mechanism scheduled agents use
(FR10) — call ``load()`` at the start of each run and the returned instance
reflects any on-disk edits. No caching, no process restart required.

All load failures — missing file, malformed YAML, schema violations —
surface as :class:`backend.errors.exceptions.ConfigurationError`; a raw
:class:`pydantic.ValidationError` never escapes this module.
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
    ValidationError,
    field_validator,
    model_validator,
)

from backend.errors.exceptions import ConfigurationError

# Fractional change applied to any metric without an explicit entry in
# ``metric_thresholds`` (0.15 == ±15%).
DEFAULT_THRESHOLD = 0.15

# backend/models/pipeline_config.py -> backend/models -> backend -> repo root
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

_DEFAULT_CONFIG_FILENAME = "config.yaml"


class ScheduleConfig(BaseModel):
    """Report schedule: a named interval OR a cron expression, never both."""

    model_config = ConfigDict(extra="forbid")

    interval: Literal["daily", "weekly", "monthly"] | None = None
    cron: str | None = None

    @field_validator("cron")
    @classmethod
    def _cron_must_be_valid(cls, value: str | None) -> str | None:
        if value is not None and not croniter.is_valid(value):
            raise ValueError(f"invalid cron expression: {value!r}")
        return value

    @model_validator(mode="after")
    def _exactly_one_of_interval_or_cron(self) -> ScheduleConfig:
        if (self.interval is None) == (self.cron is None):
            raise ValueError("exactly one of 'interval' or 'cron' must be set")
        return self

    def describe(self) -> str:
        """Human-readable schedule summary for logging (never None)."""
        return self.interval if self.interval is not None else f"cron:{self.cron}"


class OutputConfig(BaseModel):
    """Report rendering options."""

    model_config = ConfigDict(extra="forbid")

    format: Literal["docx", "pdf"] = "docx"
    output_dir: Path = Path("output")


class SmtpSettings(BaseModel):
    """SMTP delivery settings, sourced ONLY from environment variables.

    ``PipelineConfig.load()`` populates this from ``SMTP_*`` env vars
    (``.env`` in dev). A ``smtp`` key in ``config.yaml`` is rejected
    outright — credentials never live in the YAML.
    """

    model_config = ConfigDict(extra="forbid")

    host: str | None = None
    port: int = 587
    username: str | None = None
    password: str | None = None
    from_addr: str | None = None


class PipelineConfig(BaseModel):
    """Root configuration contract for the Phase 2 agent pipeline.

    ``data_sources`` and ``alert_recipients`` are plain validated list
    fields rather than wrapper models — the YAML shape is a top-level
    list for both, and downstream agents read them directly.
    """

    model_config = ConfigDict(extra="forbid")

    data_sources: list[Path] = Field(min_length=1)
    report_schedule: ScheduleConfig
    metric_thresholds: dict[str, float] = Field(default_factory=dict)
    alert_recipients: list[EmailStr] = Field(min_length=1)
    output: OutputConfig = Field(default_factory=OutputConfig)
    smtp: SmtpSettings = Field(default_factory=SmtpSettings)

    @field_validator("metric_thresholds")
    @classmethod
    def _thresholds_must_be_positive(cls, value: dict[str, float]) -> dict[str, float]:
        for metric, threshold in value.items():
            if threshold <= 0:
                raise ValueError(
                    f"threshold for metric {metric!r} must be > 0, got {threshold}"
                )
        return value

    def threshold_for(self, metric: str) -> float:
        """Fractional change threshold for ``metric``.

        Falls back to :data:`DEFAULT_THRESHOLD` (0.15 == ±15%) when the
        metric has no explicit entry in ``metric_thresholds``.
        """
        return self.metric_thresholds.get(metric, DEFAULT_THRESHOLD)

    @classmethod
    def load(cls, path: str | Path | None = None) -> PipelineConfig:
        """Read, validate, and return the pipeline configuration.

        ``path`` defaults to ``config.yaml`` at the project root. Secrets
        (``SMTP_*``) are merged in from environment variables — loaded via
        ``.env`` in dev — never from the YAML. Stateless by design: every
        call re-reads the file, so scheduled agents pick up on-disk edits
        on their next run without a restart.

        Raises :class:`ConfigurationError` on a missing file, malformed
        YAML, or any schema violation. Pydantic's ``ValidationError`` is
        always caught and re-raised as ``ConfigurationError``.
        """
        resolved = Path(path) if path is not None else _PROJECT_ROOT / _DEFAULT_CONFIG_FILENAME

        try:
            raw_text = resolved.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ConfigurationError(f"config file not found: {resolved}") from exc

        try:
            # yaml.safe_load only — arbitrary-object deserialization via
            # yaml.load is an injection vector (NFR4). JSON is a strict
            # subset of YAML, so safe_load parses .json config too — no
            # separate JSON branch needed.
            raw = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            raise ConfigurationError(f"config file {resolved} is not valid YAML: {exc}") from exc

        if not isinstance(raw, dict):
            raise ConfigurationError(
                f"config file {resolved} must contain a YAML mapping, "
                f"got {type(raw).__name__}"
            )

        if "smtp" in raw:
            raise ConfigurationError(
                "'smtp' must not appear in config.yaml — SMTP credentials are "
                "sourced from SMTP_* environment variables only (see .env.example)"
            )

        load_dotenv()

        try:
            smtp = SmtpSettings(
                host=os.environ.get("SMTP_HOST") or None,
                port=int(os.environ.get("SMTP_PORT") or 587),
                username=os.environ.get("SMTP_USERNAME") or None,
                password=os.environ.get("SMTP_PASSWORD") or None,
                from_addr=os.environ.get("SMTP_FROM") or None,
            )
        except ValueError as exc:
            # int() on a non-numeric SMTP_PORT, or SmtpSettings validation.
            raise ConfigurationError(f"invalid SMTP environment settings: {exc}") from exc

        try:
            config = cls(**raw, smtp=smtp)
        except ValidationError as exc:
            raise ConfigurationError(_summarize_validation_error(exc)) from exc

        # Summary only — never secrets, never full recipient addresses
        # (PII-adjacent; the count is enough).
        structlog.get_logger().info(
            "config_loaded",
            schedule=config.report_schedule.describe(),
            threshold_keys=sorted(config.metric_thresholds),
            recipient_count=len(config.alert_recipients),
            output_format=config.output.format,
            data_source_count=len(config.data_sources),
        )
        return config


def _summarize_validation_error(exc: ValidationError) -> str:
    """Flatten a ValidationError into one descriptive message.

    Deliberately excludes input values (``include_input=False``) so a
    mistyped secret can never leak into an error message or log line.
    """
    parts = []
    for error in exc.errors(include_input=False, include_url=False):
        loc = ".".join(str(piece) for piece in error["loc"]) or "<root>"
        parts.append(f"{loc}: {error['msg']}")
    return "invalid pipeline configuration — " + "; ".join(parts)
