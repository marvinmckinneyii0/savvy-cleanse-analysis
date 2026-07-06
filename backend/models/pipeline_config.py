"""Pipeline configuration contract (Story 2.1).

Defines the Pydantic v2 models for the Phase 2 ``config.yaml`` surface —
data sources, report schedule, per-metric drift thresholds, alert
recipients, and output settings — plus :meth:`PipelineConfig.load`, the
single entry point every agent uses to read configuration.

Secrets discipline (NFR3): SMTP credentials and API keys are sourced from
environment variables only (``.env`` in dev via python-dotenv). They are
NEVER read from ``config.yaml``, and the loader rejects a config file that
tries to smuggle them in. The ``config_loaded`` log event carries a
non-secret summary (counts and keys, no values).

Consumers across Epic 2:

* Drift Engine — per-metric ``metric_thresholds`` via :meth:`threshold_for`.
* Reporting Agent — ``data_sources``, ``report_schedule``, ``output``;
  calls :meth:`PipelineConfig.load` at the start of each scheduled run,
  which re-reads the file so on-disk edits take effect without a restart.
* Monitoring Agent — ``metric_thresholds``, ``alert_recipients``, ``smtp``.
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

# Repo root = parents[2] of backend/models/pipeline_config.py.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"

# Keys the loader rejects if they appear in config.yaml — secrets are
# env-only (SMTP_HOST/PORT/USERNAME/PASSWORD/FROM via .env).
_SECRET_YAML_KEYS = frozenset({"smtp", "smtp_password", "smtp_username", "api_keys"})

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
        """Loggable one-word-ish summary (e.g. ``weekly`` or ``cron:0 6 * * 1``)."""
        return self.interval if self.interval is not None else f"cron:{self.cron}"


class OutputConfig(BaseModel):
    """Report output settings."""

    model_config = ConfigDict(extra="forbid")

    format: Literal["docx", "pdf"] = "docx"
    output_dir: Path = Path("output/")


class SmtpSettings(BaseModel):
    """SMTP delivery settings, sourced from environment variables ONLY.

    Every field is optional because alert delivery is a 2.4 concern —
    Phase 2 stories before it must be able to load config on a machine
    with no SMTP env configured.
    """

    model_config = ConfigDict(extra="forbid")

    host: str | None = None
    port: int = 587
    username: str | None = None
    password: str | None = None
    from_addr: str | None = None

    @classmethod
    def from_env(cls) -> SmtpSettings:
        """Build from ``SMTP_*`` environment variables (post ``load_dotenv``)."""
        raw_port = os.environ.get("SMTP_PORT")
        try:
            port = int(raw_port) if raw_port else 587
        except ValueError:
            raise ConfigurationError(
                f"SMTP_PORT must be an integer, got {raw_port!r}"
            ) from None
        return cls(
            host=os.environ.get("SMTP_HOST") or None,
            port=port,
            username=os.environ.get("SMTP_USERNAME") or None,
            password=os.environ.get("SMTP_PASSWORD") or None,
            from_addr=os.environ.get("SMTP_FROM") or None,
        )


class PipelineConfig(BaseModel):
    """Typed view of ``config.yaml`` plus env-sourced secrets.

    Instances are immutable snapshots: call :meth:`load` again to pick up
    on-disk changes (FR10 runtime modification — ``load()`` is stateless
    and re-reads the file on every call; live watching is 2.3's scope).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

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
            if threshold <= 0:
                raise ValueError(
                    f"metric_thresholds[{metric!r}] must be > 0, got {threshold}"
                )
        return value

    def threshold_for(self, metric: str) -> float:
        """Per-metric fractional change threshold, else :data:`DEFAULT_THRESHOLD`."""
        return self.metric_thresholds.get(metric, DEFAULT_THRESHOLD)

    @classmethod
    def load(cls, path: str | Path | None = None) -> PipelineConfig:
        """Read, validate, and return the pipeline configuration.

        Re-reads and re-validates the file on every call — no caching —
        so a scheduled agent picks up on-disk edits on its next run.
        Secrets are merged from the environment, never from the file.

        Raises :class:`ConfigurationError` on a missing file, malformed
        YAML, secret keys in the file, or any validation failure. A
        pydantic ``ValidationError`` never escapes this method.
        """
        config_path = Path(path) if path is not None else _DEFAULT_CONFIG_PATH

        try:
            raw_text = config_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise ConfigurationError(f"config file not found: {config_path}") from None
        except OSError as exc:  # directory, permission denied, I/O error, ...
            raise ConfigurationError(f"cannot read config file {config_path}: {exc}") from exc
        except UnicodeDecodeError as exc:
            raise ConfigurationError(
                f"config file {config_path} is not valid UTF-8: {exc}"
            ) from exc

        try:
            # safe_load only — yaml.load without a safe loader is an
            # arbitrary-object deserialization vector (NFR4). JSON is a
            # strict subset of YAML, so .json config parses here too.
            raw = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            raise ConfigurationError(f"malformed YAML in {config_path}: {exc}") from exc

        if raw is None:
            raise ConfigurationError(f"config file is empty: {config_path}")
        if not isinstance(raw, dict):
            raise ConfigurationError(
                f"config root must be a mapping, got {type(raw).__name__} in {config_path}"
            )

        smuggled = _SECRET_YAML_KEYS.intersection(raw)
        if smuggled:
            raise ConfigurationError(
                f"secret keys {sorted(smuggled)} must not appear in {config_path}; "
                "SMTP credentials and API keys are read from environment variables only"
            )

        # Explicit path: only the repo-root .env is ever loaded — the no-arg
        # form walks up past the project root and could pick up a foreign .env.
        load_dotenv(_PROJECT_ROOT / ".env")  # no-op when absent
        raw["smtp"] = SmtpSettings.from_env().model_dump()

        try:
            config = cls.model_validate(raw)
        except ValidationError as exc:
            # `from None`: a chained ValidationError repr echoes input values
            # (recipient addresses are PII-adjacent); the summary already
            # names every offending field.
            raise ConfigurationError(
                f"invalid configuration in {config_path}: {_summarize_validation_error(exc)}"
            ) from None

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


def _summarize_validation_error(exc: ValidationError) -> str:
    """Field-by-field summary of a pydantic ValidationError, secrets-safe.

    Names the offending field and pydantic's message but never echoes an
    input value — SMTP credentials must not leak into exception text.
    """
    parts = []
    for err in exc.errors(include_input=False, include_url=False):
        field = ".".join(str(loc) for loc in err["loc"]) or "<root>"
        parts.append(f"{field}: {err['msg']}")
    return "; ".join(parts)
