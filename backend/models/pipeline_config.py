"""Pipeline configuration Pydantic models (Story 2.1).

Defines the typed contract for the user-facing ``config.yaml`` at project
root: data sources, report schedule, per-metric thresholds, alert
recipients, and output settings. Loaded via :meth:`PipelineConfig.load`,
which re-reads and re-validates the file on every call so scheduled agents
pick up on-disk changes without a process restart (FR10).

Secrets discipline (NFR3): SMTP credentials are sourced exclusively from
environment variables (``.env`` in dev via python-dotenv) and are never
read from — or permitted in — ``config.yaml``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

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

# Applied when a metric has no explicit entry in ``metric_thresholds``.
# 0.15 == ±15% week-over-week, the FR7 default.
DEFAULT_THRESHOLD: float = 0.15

# Repo root: backend/models/pipeline_config.py -> backend/models -> backend -> root.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"

# Top-level YAML keys that would smuggle secrets into version control.
_FORBIDDEN_YAML_KEYS = frozenset({"smtp", "secrets", "credentials", "api_keys"})


class ScheduleConfig(BaseModel):
    """Report schedule: a named interval OR a cron expression, never both."""

    model_config = ConfigDict(extra="forbid")

    interval: Literal["daily", "weekly", "monthly"] | None = None
    cron: str | None = None

    @model_validator(mode="after")
    def _exactly_one_of_interval_or_cron(self) -> ScheduleConfig:
        if (self.interval is None) == (self.cron is None):
            raise ValueError(
                "report_schedule requires exactly one of 'interval' "
                "(daily|weekly|monthly) or 'cron'"
            )
        if self.cron is not None and not croniter.is_valid(self.cron):
            raise ValueError(f"invalid cron expression: {self.cron!r}")
        return self

    def describe(self) -> str:
        """Human-readable schedule summary for logging."""
        return self.interval if self.interval is not None else f"cron:{self.cron}"


class OutputConfig(BaseModel):
    """Report output settings."""

    model_config = ConfigDict(extra="forbid")

    format: Literal["docx", "pdf"] = "docx"
    output_dir: Path = Path("output")


class SmtpSettings(BaseModel):
    """SMTP delivery settings — sourced ONLY from environment variables.

    All fields are optional at load time: alert delivery arrives in
    Story 2.4, and the Monitoring Agent is responsible for rejecting a
    send attempt when credentials are absent.
    """

    model_config = ConfigDict(extra="forbid")

    host: str | None = None
    port: int = 587
    username: str | None = None
    password: str | None = None
    from_address: str | None = None

    @classmethod
    def env_values(cls) -> dict[str, Any]:
        """Raw SMTP values from the environment (unvalidated)."""
        values: dict[str, Any] = {
            "host": os.environ.get("SMTP_HOST") or None,
            "username": os.environ.get("SMTP_USERNAME") or None,
            "password": os.environ.get("SMTP_PASSWORD") or None,
            "from_address": os.environ.get("SMTP_FROM") or None,
        }
        port = os.environ.get("SMTP_PORT")
        if port:
            values["port"] = port
        return values


class PipelineConfig(BaseModel):
    """Root configuration contract for the Phase 2 agents.

    Consumed by the Drift Engine (thresholds), the Reporting Agent
    (``data_sources``, ``report_schedule``, ``output``) and the Monitoring
    Agent (``metric_thresholds``, ``alert_recipients``, ``smtp``).
    """

    model_config = ConfigDict(extra="forbid")

    data_sources: list[Path] = Field(min_length=1)
    report_schedule: ScheduleConfig
    metric_thresholds: dict[str, float] = Field(default_factory=dict)
    alert_recipients: list[EmailStr]
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
        """Fractional change threshold for ``metric`` (default ±15%)."""
        return self.metric_thresholds.get(metric, DEFAULT_THRESHOLD)

    @classmethod
    def load(cls, path: str | Path | None = None) -> PipelineConfig:
        """Read, validate, and return the config from ``path``.

        Stateless by design: re-reads and re-validates the file on every
        call so a scheduled agent's next run reflects on-disk edits (FR10).
        Defaults to ``config.yaml`` at project root. Raises
        :class:`ConfigurationError` on any missing, unparseable, or
        invalid configuration — pydantic ``ValidationError`` never escapes.
        """
        config_path = Path(path) if path is not None else _DEFAULT_CONFIG_PATH
        load_dotenv()

        try:
            raw_text = config_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ConfigurationError(f"config file not found: {config_path}") from exc
        except OSError as exc:
            raise ConfigurationError(f"config file unreadable: {config_path}: {exc}") from exc

        # JSON is a strict subset of YAML, so safe_load parses .json config
        # too — no separate JSON branch needed. NEVER yaml.load (NFR4).
        try:
            raw = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            raise ConfigurationError(
                f"config file is not valid YAML: {config_path}: {exc}"
            ) from exc

        if not isinstance(raw, dict):
            raise ConfigurationError(
                f"config file must contain a mapping of settings, "
                f"got {type(raw).__name__}: {config_path}"
            )

        forbidden = _FORBIDDEN_YAML_KEYS.intersection(raw)
        if forbidden:
            raise ConfigurationError(
                f"secret sections {sorted(forbidden)} are not allowed in "
                f"{config_path.name} — SMTP credentials and API keys belong "
                f"in environment variables (.env)"
            )

        raw["smtp"] = SmtpSettings.env_values()

        try:
            config = cls.model_validate(raw)
        except ValidationError as exc:
            raise ConfigurationError(
                f"invalid configuration in {config_path}: "
                f"{_format_validation_error(exc)}"
            ) from exc

        # Summary only — never SMTP credentials, API keys, or recipient
        # addresses (PII-adjacent: log the count, not the list).
        structlog.get_logger().info(
            "config_loaded",
            config_path=str(config_path),
            data_source_count=len(config.data_sources),
            schedule=config.report_schedule.describe(),
            threshold_keys=sorted(config.metric_thresholds),
            recipient_count=len(config.alert_recipients),
            output_format=config.output.format,
        )
        return config


def _format_validation_error(exc: ValidationError) -> str:
    """Flatten a pydantic ValidationError into 'field: message' pairs."""
    parts = []
    for err in exc.errors(include_url=False, include_input=False):
        loc = ".".join(str(piece) for piece in err["loc"]) or "<root>"
        parts.append(f"{loc}: {err['msg']}")
    return "; ".join(parts)
