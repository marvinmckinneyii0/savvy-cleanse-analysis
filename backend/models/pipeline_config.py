"""Pipeline configuration contract (Story 2.1).

Defines the Pydantic models for the user-facing ``config.yaml`` at the
project root: data sources, report schedule, per-metric drift thresholds,
alert recipients, and output settings. :meth:`PipelineConfig.load` is the
single entry point every Phase 2 agent uses to read configuration.

Secrets discipline (NFR3): SMTP credentials and API keys are sourced from
the environment only — process environment variables first, then the
project ``.env`` (read via python-dotenv without mutating ``os.environ``).
They are NEVER read from ``config.yaml``, and the ``config_loaded`` log
event emits a summary without secret values.

``load()`` is stateless — it re-reads and re-validates ``config.yaml``
AND ``.env`` on every call, which is how scheduled agents pick up runtime
config changes (FR10), including secret rotation, without a process
restart. Live file-watching is Story 2.3's scope.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Literal

import structlog
import yaml
from croniter import croniter
from dotenv import dotenv_values
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    RootModel,
    SecretStr,
    ValidationError,
    model_validator,
)

from backend.errors.exceptions import ConfigurationError

#: Fractional change threshold applied to any metric that has no explicit
#: entry in ``metric_thresholds`` (0.15 == ±15%).
DEFAULT_THRESHOLD: float = 0.15

# Repo root, assuming this file sits at backend/models/pipeline_config.py.
# Valid for in-repo / editable installs only; a packaged CLI entrypoint
# must pass an explicit path to load().
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

_DOTENV_PATH = _PROJECT_ROOT / ".env"

_SMTP_ENV_VARS: dict[str, str] = {
    "host": "SMTP_HOST",
    "port": "SMTP_PORT",
    "username": "SMTP_USERNAME",
    "password": "SMTP_PASSWORD",
    "from_address": "SMTP_FROM",
}

# Config sections that are populated exclusively from the environment.
# Drives BOTH the reject-if-in-yaml check and the env merge in load() —
# add future env-sourced sections (e.g. api_keys) here, in one place.
_ENV_ONLY_SECTIONS: tuple[str, ...] = ("smtp",)


class ScheduleConfig(BaseModel):
    """Report schedule: an interval keyword OR a cron expression.

    Exactly one of ``interval`` / ``cron`` must be set. Cron expressions
    are validated with :func:`croniter.is_valid`; the scheduler itself
    (APScheduler) arrives in Story 2.3.
    """

    model_config = ConfigDict(extra="forbid")

    interval: Literal["daily", "weekly", "monthly"] | None = None
    cron: str | None = None

    @model_validator(mode="after")
    def _exactly_one_and_valid(self) -> ScheduleConfig:
        if (self.interval is None) == (self.cron is None):
            raise ValueError(
                "report_schedule requires exactly one of 'interval' "
                "(daily | weekly | monthly) or 'cron'"
            )
        if self.cron is not None and not croniter.is_valid(self.cron):
            raise ValueError(f"invalid cron expression: {self.cron!r}")
        return self

    def describe(self) -> str:
        """Loggable one-word summary, e.g. ``weekly`` or ``cron(0 6 * * 1)``."""
        return self.interval if self.interval is not None else f"cron({self.cron})"


class ThresholdConfig(RootModel[dict[str, Annotated[float, Field(gt=0)]]]):
    """Per-metric fractional change thresholds (0.15 == ±15%).

    Values must be > 0 (``gt=0`` also rejects NaN). Metrics without an
    explicit entry fall back to :data:`DEFAULT_THRESHOLD` via
    :meth:`threshold_for` — the lookup the Drift Engine (2.2) and
    Monitoring Agent (2.4) use per column. For anything else, work with
    the plain dict at ``.root``.
    """

    root: dict[str, Annotated[float, Field(gt=0)]] = {}

    def threshold_for(self, metric: str) -> float:
        return self.root.get(metric, DEFAULT_THRESHOLD)


class OutputConfig(BaseModel):
    """Report output settings."""

    model_config = ConfigDict(extra="forbid")

    format: Literal["docx", "pdf"] = "docx"
    output_dir: Path = Path("output")


class SmtpSettings(BaseModel):
    """SMTP delivery settings — sourced from the environment ONLY.

    Populated by :meth:`PipelineConfig.load` from ``SMTP_HOST``,
    ``SMTP_PORT``, ``SMTP_USERNAME``, ``SMTP_PASSWORD``, ``SMTP_FROM``
    (process env first, then the project ``.env``). Never read from
    ``config.yaml``. ``password`` is a :class:`SecretStr` so accidental
    ``repr``/log output is masked.
    """

    model_config = ConfigDict(extra="forbid")

    host: str | None = None
    port: int = Field(default=587, ge=1, le=65535)
    username: str | None = None
    password: SecretStr | None = None
    from_address: str | None = None


class PipelineConfig(BaseModel):
    """Root configuration for the Phase 2 automation agents.

    Load via :meth:`load` — never construct from a raw dict at call sites.
    Relative ``data_sources`` and ``output.output_dir`` entries are
    anchored to the config file's directory by ``load()``, so consumers
    never depend on the process working directory.
    """

    model_config = ConfigDict(extra="forbid")

    data_sources: list[Path] = Field(min_length=1)
    report_schedule: ScheduleConfig
    metric_thresholds: ThresholdConfig = Field(default_factory=ThresholdConfig)
    alert_recipients: list[EmailStr] = Field(default_factory=list)
    output: OutputConfig = Field(default_factory=OutputConfig)
    smtp: SmtpSettings = Field(default_factory=SmtpSettings)

    @classmethod
    def load(cls, path: str | Path | None = None) -> PipelineConfig:
        """Read, validate, and return the pipeline configuration.

        ``path`` defaults to ``config.yaml`` at the project root. Raises
        :class:`ConfigurationError` (never a bare pydantic
        ``ValidationError``) on a missing/unreadable file, malformed YAML,
        or any invalid value. Stateless: re-reads ``config.yaml`` and
        ``.env`` on every call so a scheduled agent picks up on-disk edits
        at its next run.
        """
        config_path = Path(path) if path is not None else _PROJECT_ROOT / "config.yaml"

        try:
            raw_text = config_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ConfigurationError(f"config file not found: {config_path}") from exc
        except OSError as exc:
            # IsADirectoryError, PermissionError, locked file on Windows, …
            raise ConfigurationError(
                f"config file could not be read ({config_path}): {exc}"
            ) from exc

        try:
            # JSON is a strict subset of YAML, so safe_load parses .json
            # configs too — no separate JSON branch needed. NEVER yaml.load
            # without a safe loader (arbitrary-object deserialization).
            raw = yaml.safe_load(raw_text)
        except yaml.YAMLError as exc:
            raise ConfigurationError(
                f"config file is not valid YAML ({config_path}): {exc}"
            ) from exc

        if not isinstance(raw, dict):
            raise ConfigurationError(
                f"config root must be a mapping ({config_path}), "
                f"got {type(raw).__name__}"
            )
        for section in _ENV_ONLY_SECTIONS:
            if section in raw:
                raise ConfigurationError(
                    f"{section!r} must not appear in config.yaml — its settings "
                    "are sourced from environment variables only (see .env.example)"
                )

        # A section header with every entry commented out parses to None;
        # drop those keys so the model defaults apply instead of failing
        # with "input should be a valid dict/list".
        raw = {key: value for key, value in raw.items() if value is not None}

        merged = {**raw, "smtp": _smtp_settings_from_env()}
        try:
            config = cls.model_validate(merged)
        except ValidationError as exc:
            raise ConfigurationError(
                f"invalid configuration ({config_path}): "
                f"{_format_validation_error(exc)}"
            ) from exc

        # Anchor relative paths to the config file's directory so agents
        # scheduled with an arbitrary cwd (cron, systemd) resolve the same
        # files a developer running from the repo root does.
        base_dir = config_path.resolve().parent
        config = config.model_copy(
            update={
                "data_sources": [_anchored(src, base_dir) for src in config.data_sources],
                "output": config.output.model_copy(
                    update={"output_dir": _anchored(config.output.output_dir, base_dir)}
                ),
            }
        )

        # Summary only — never SMTP credentials, API keys, recipient
        # addresses (PII-adjacent; the count is enough), or the absolute
        # config path (may embed a username; project logging rule).
        structlog.get_logger(__name__).info(
            "config_loaded",
            config_file=config_path.name,
            schedule=config.report_schedule.describe(),
            threshold_keys=sorted(config.metric_thresholds.root),
            recipient_count=len(config.alert_recipients),
            output_format=config.output.format,
        )
        return config


def _anchored(path: Path, base: Path) -> Path:
    return path if path.is_absolute() else base / path


def _smtp_settings_from_env() -> dict[str, str]:
    """Collect SMTP settings from the environment.

    Process environment variables take precedence over the project
    ``.env``, which is re-read on every call (no ``os.environ`` mutation)
    so rotating a secret in ``.env`` is picked up by the next scheduled
    run. Empty strings (the ``.env.example`` placeholder state) are
    treated as unset so a copied-but-unfilled ``.env`` does not produce
    ``host=""``.
    """
    dotenv: dict[str, str | None] = dotenv_values(_DOTENV_PATH)
    return {
        field: value
        for field, env_var in _SMTP_ENV_VARS.items()
        if (value := os.environ.get(env_var) or dotenv.get(env_var))
    }


def _format_validation_error(exc: ValidationError) -> str:
    """Flatten a pydantic ValidationError to ``field: message`` pairs.

    Deliberately excludes the offending *input values* so a bad secret
    passed via env can never leak into the error message or logs.
    """
    parts: list[str] = []
    for error in exc.errors(include_input=False, include_url=False):
        loc = ".".join(str(item) for item in error["loc"]) or "<root>"
        parts.append(f"{loc}: {error['msg']}")
    return "; ".join(parts)
