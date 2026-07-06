"""Pipeline configuration Pydantic models (Story 2.1).

Defines the typed contract for the root ``config.yaml`` that every Phase 2
agent consumes: the Drift Engine reads ``metric_thresholds``, the Reporting
Agent reads ``data_sources`` + ``report_schedule`` + ``output`` and calls
:meth:`PipelineConfig.load` at the start of each scheduled run (hot-reload),
and the Monitoring Agent reads ``metric_thresholds`` + ``alert_recipients``
+ the env-sourced SMTP settings.

Secrets discipline (NFR3): SMTP credentials and API keys are sourced from
environment variables only (``.env`` in dev via python-dotenv). They are
NEVER read from ``config.yaml`` — the loader rejects a config file that
tries to define an ``smtp`` section.

``load()`` is stateless: it re-reads and re-validates the file on every
call, so a scheduled agent picks up on-disk edits on its next run without
a process restart (FR10).
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
    ValidationError,
    field_validator,
    model_validator,
)

from backend.errors.exceptions import ConfigurationError

#: Fractional change threshold applied to any metric that has no explicit
#: entry in ``metric_thresholds`` (0.15 == ±15%).
DEFAULT_THRESHOLD = 0.15

#: Repo root — models/pipeline_config.py → models/ → backend/ → root.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"

#: SmtpSettings field → environment variable it is sourced from, so
#: env-var validation failures name the actual offender (the env var),
#: not the innocent config.yaml.
_SMTP_ENV_VARS = {
    "host": "SMTP_HOST",
    "port": "SMTP_PORT",
    "username": "SMTP_USERNAME",
    "password": "SMTP_PASSWORD",
    "from_address": "SMTP_FROM",
}

_logger = structlog.get_logger(__name__)


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
            raise ValueError("report_schedule requires exactly one of 'interval' or 'cron'")
        return self

    def describe(self) -> str:
        """Human-readable schedule summary for logging (never secret)."""
        return self.interval if self.interval is not None else f"cron:{self.cron}"


class OutputConfig(BaseModel):
    """Report output settings."""

    model_config = ConfigDict(extra="forbid")

    format: Literal["docx", "pdf"] = "docx"
    output_dir: Path = Path("output/")


class SmtpSettings(BaseModel):
    """SMTP delivery settings, sourced exclusively from environment variables.

    Every field is optional: alert delivery is a 2.4 concern, and local
    pipeline runs must not fail pre-flight just because SMTP is unset.
    ``password`` and ``username`` are secrets — they must never appear in
    ``config.yaml``, log payloads, or exception messages.
    """

    model_config = ConfigDict(extra="forbid")

    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    from_address: str | None = None

    @classmethod
    def from_env(cls) -> SmtpSettings:
        """Build from ``SMTP_*`` environment variables (unset → None)."""
        return cls(
            host=os.environ.get("SMTP_HOST") or None,
            port=os.environ.get("SMTP_PORT") or None,
            username=os.environ.get("SMTP_USERNAME") or None,
            password=os.environ.get("SMTP_PASSWORD") or None,
            from_address=os.environ.get("SMTP_FROM") or None,
        )


class PipelineConfig(BaseModel):
    """Root configuration contract for the Phase 2 automation pipeline.

    Load via :meth:`load` — never instantiate from a raw YAML dict at call
    sites, and never let a pydantic ``ValidationError`` escape the loader:
    all load-time failures surface as
    :class:`backend.errors.exceptions.ConfigurationError`.
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
    def _thresholds_must_be_positive(cls, value: dict[str, float]) -> dict[str, float]:
        for metric, threshold in value.items():
            # NaN compares False against everything, so a plain `<= 0`
            # check would let it through and silently disable drift
            # detection for that metric downstream.
            if not math.isfinite(threshold) or threshold <= 0:
                raise ValueError(
                    f"metric_thresholds[{metric!r}] must be a finite number > 0, "
                    f"got {threshold}"
                )
        return value

    def threshold_for(self, metric: str) -> float:
        """Fractional change threshold for ``metric`` (default ±15%)."""
        return self.metric_thresholds.get(metric, DEFAULT_THRESHOLD)

    @classmethod
    def load(cls, path: str | Path | None = None) -> PipelineConfig:
        """Read, validate, and return the pipeline configuration.

        Re-reads the file on every call — no caching — so callers that
        re-invoke ``load()`` (e.g. a scheduled agent at the start of each
        run) observe on-disk edits without a restart (FR10).

        :param path: Config file location; defaults to ``config.yaml`` at
            the project root. YAML or JSON (JSON is a strict subset of
            YAML, so ``yaml.safe_load`` parses ``.json`` too — no separate
            JSON branch needed).
        :raises ConfigurationError: file missing, unparseable, or failing
            schema validation. Pydantic ``ValidationError`` never escapes.
        """
        config_path = Path(path) if path is not None else _DEFAULT_CONFIG_PATH

        try:
            raw_text = config_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ConfigurationError(f"config file not found: {config_path}") from exc
        except (OSError, UnicodeDecodeError) as exc:
            # IsADirectoryError, PermissionError, non-UTF-8 content, ... —
            # all pre-flight config failures, so all ConfigurationError.
            raise ConfigurationError(
                f"config file could not be read: {config_path} ({exc})"
            ) from exc

        try:
            data = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            raise ConfigurationError(f"config file is not valid YAML: {config_path} ({exc})") from exc

        if not isinstance(data, dict):
            raise ConfigurationError(
                f"config file must contain a YAML mapping at the top level, "
                f"got {type(data).__name__}: {config_path}"
            )

        # Secrets come from env only (NFR3). A config file that tries to
        # define SMTP settings is a policy violation, not a schema variant.
        if "smtp" in data:
            raise ConfigurationError(
                "config.yaml must not define 'smtp' — SMTP settings are sourced "
                "from environment variables (SMTP_HOST, SMTP_PORT, SMTP_USERNAME, "
                "SMTP_PASSWORD, SMTP_FROM); see .env.example"
            )

        load_dotenv()

        try:
            smtp = SmtpSettings.from_env()
        except ValidationError as exc:
            offenders = sorted(
                {_SMTP_ENV_VARS.get(str(error["loc"][0]), "SMTP_*") for error in exc.errors()}
            )
            # Name the env var, never echo its value (it may be a secret).
            raise ConfigurationError(
                "invalid SMTP environment variable(s): "
                + ", ".join(offenders)
                + " — "
                + "; ".join(error["msg"] for error in exc.errors())
            ) from exc

        try:
            # model_validate (not cls(**data)) so non-string top-level YAML
            # keys surface as ValidationError instead of a raw TypeError.
            config = cls.model_validate({**data, "smtp": smtp})
        except ValidationError as exc:
            fields = ", ".join(
                ".".join(str(loc) for loc in error["loc"]) or "<root>"
                for error in exc.errors()
            )
            raise ConfigurationError(
                f"invalid configuration in {config_path} — offending field(s): "
                f"{fields}. {exc.error_count()} validation error(s): "
                + "; ".join(
                    f"{'.'.join(str(loc) for loc in error['loc']) or '<root>'}: {error['msg']}"
                    for error in exc.errors()
                )
            ) from exc

        # Summary only — never SMTP credentials, never full recipient
        # addresses (PII-adjacent; count is enough).
        _logger.info(
            "config_loaded",
            config_path=str(config_path),
            data_source_count=len(config.data_sources),
            schedule=config.report_schedule.describe(),
            threshold_keys=sorted(config.metric_thresholds),
            recipient_count=len(config.alert_recipients),
            output_format=config.output.format,
            smtp_configured=config.smtp.host is not None,
        )
        return config
