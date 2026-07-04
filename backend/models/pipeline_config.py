"""Pipeline configuration Pydantic models (Story 2.1).

Defines the typed contract for the user-facing ``config.yaml`` at the
project root: data sources, report schedule, per-metric drift thresholds,
alert recipients, and output settings. Consumed by every Epic 2 agent —
the Drift Engine reads ``metric_thresholds``, the Reporting Agent reads
``data_sources`` / ``report_schedule`` / ``output``, and the Monitoring
Agent reads ``metric_thresholds`` / ``alert_recipients`` plus the
env-sourced SMTP settings.

Secrets discipline (NFR3): ``config.yaml`` holds only non-secret
structure. SMTP credentials come exclusively from environment variables
(``.env`` in dev via python-dotenv) — :meth:`PipelineConfig.load` rejects
an ``smtp`` block in the YAML outright.

Hot-reload contract (FR10): :meth:`PipelineConfig.load` is stateless —
it re-reads and re-validates the file on every call, so a scheduled
agent picks up on-disk edits on its next run without a process restart.
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

#: Fractional change threshold applied when a metric has no explicit
#: entry in ``metric_thresholds`` (0.15 == ±15%).
DEFAULT_THRESHOLD: float = 0.15

#: Repo root — this file lives at backend/models/, two levels down.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"

_INTERVALS = ("daily", "weekly", "monthly")


class ScheduleConfig(BaseModel):
    """Report schedule: a named interval OR a cron expression, never both."""

    model_config = ConfigDict(extra="forbid")

    interval: Literal["daily", "weekly", "monthly"] | None = None
    cron: str | None = None

    @field_validator("cron")
    @classmethod
    def _cron_must_parse(cls, v: str | None) -> str | None:
        if v is not None and not croniter.is_valid(v):
            raise ValueError(f"invalid cron expression: {v!r}")
        return v

    @model_validator(mode="after")
    def _exactly_one_of_interval_or_cron(self) -> ScheduleConfig:
        if (self.interval is None) == (self.cron is None):
            raise ValueError(
                "report_schedule requires exactly one of 'interval' "
                f"({'/'.join(_INTERVALS)}) or 'cron'"
            )
        return self


class OutputConfig(BaseModel):
    """Report output settings."""

    model_config = ConfigDict(extra="forbid")

    format: Literal["docx", "pdf"] = "docx"
    output_dir: Path = Path("output")


class SmtpSettings(BaseModel):
    """SMTP delivery settings, sourced ONLY from environment variables.

    Every field is optional so the config layer loads cleanly in
    environments that never send mail (CI, local dev without alerts).
    The Monitoring Agent (Story 2.4) is responsible for failing fast if
    it needs SMTP and these are unset.
    """

    model_config = ConfigDict(extra="forbid")

    host: str | None = None
    port: int = 587
    username: str | None = None
    password: str | None = None
    from_addr: str | None = None

    @classmethod
    def from_env(cls) -> SmtpSettings:
        """Build from ``SMTP_*`` environment variables (empty vars count as unset)."""
        env = {k: v for k, v in (
            ("host", os.environ.get("SMTP_HOST")),
            ("port", os.environ.get("SMTP_PORT")),
            ("username", os.environ.get("SMTP_USERNAME")),
            ("password", os.environ.get("SMTP_PASSWORD")),
            ("from_addr", os.environ.get("SMTP_FROM")),
        ) if v}
        return cls(**env)


class PipelineConfig(BaseModel):
    """Root configuration contract, loaded from ``config.yaml`` at project root."""

    model_config = ConfigDict(extra="forbid")

    data_sources: list[Path] = Field(min_length=1)
    report_schedule: ScheduleConfig
    metric_thresholds: dict[str, float] = Field(default_factory=dict)
    alert_recipients: list[EmailStr] = Field(default_factory=list)
    output: OutputConfig = Field(default_factory=OutputConfig)
    smtp: SmtpSettings = Field(default_factory=SmtpSettings)

    @field_validator("metric_thresholds")
    @classmethod
    def _thresholds_positive(cls, v: dict[str, float]) -> dict[str, float]:
        for metric, threshold in v.items():
            if threshold <= 0:
                raise ValueError(
                    f"metric_thresholds[{metric!r}] must be > 0, got {threshold}"
                )
        return v

    def threshold_for(self, metric: str) -> float:
        """Per-metric fractional threshold, falling back to :data:`DEFAULT_THRESHOLD`."""
        return self.metric_thresholds.get(metric, DEFAULT_THRESHOLD)

    @classmethod
    def load(cls, path: str | Path | None = None) -> PipelineConfig:
        """Read, validate, and return the pipeline configuration.

        Stateless by design (FR10): every call re-reads ``path`` (default:
        ``config.yaml`` at project root) and re-validates, so on-disk edits
        are picked up by the next scheduled run. SMTP secrets are merged in
        from the environment (``.env`` honored via ``load_dotenv``) and are
        never accepted from the YAML itself.

        Raises :class:`ConfigurationError` — never a bare pydantic
        ``ValidationError`` — on a missing file, unparseable YAML, or any
        invalid value, with a message naming the offending field.
        """
        config_path = Path(path) if path is not None else _DEFAULT_CONFIG_PATH
        load_dotenv()

        try:
            raw_text = config_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ConfigurationError(f"config file not found: {config_path}") from exc

        try:
            # safe_load only — yaml.load would deserialize arbitrary Python
            # objects (NFR4). JSON is a strict subset of YAML, so .json
            # config files parse through this same call; no separate branch.
            data = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            raise ConfigurationError(f"config file is not valid YAML: {config_path}: {exc}") from exc

        if not isinstance(data, dict):
            raise ConfigurationError(
                f"config file must contain a YAML mapping at the top level, "
                f"got {type(data).__name__}: {config_path}"
            )

        if "smtp" in data:
            raise ConfigurationError(
                "smtp settings must not appear in config.yaml — SMTP credentials "
                "are sourced from environment variables only (see .env.example)"
            )

        try:
            # Inside the try so a malformed env value (e.g. non-numeric
            # SMTP_PORT) also surfaces as ConfigurationError, per AC2.
            data["smtp"] = SmtpSettings.from_env()
            config = cls.model_validate(data)
        except ValidationError as exc:
            fields = "; ".join(
                f"{'.'.join(str(loc) for loc in err['loc']) or '<root>'}: {err['msg']}"
                for err in exc.errors()
            )
            raise ConfigurationError(f"invalid configuration in {config_path}: {fields}") from exc

        # Summary only — never SMTP credentials, API keys, or recipient
        # addresses (PII-adjacent; count is enough).
        structlog.get_logger(__name__).info(
            "config_loaded",
            config_path=str(config_path),
            schedule=config.report_schedule.interval or config.report_schedule.cron,
            threshold_keys=sorted(config.metric_thresholds),
            recipient_count=len(config.alert_recipients),
            output_format=config.output.format,
            data_source_count=len(config.data_sources),
        )
        return config
