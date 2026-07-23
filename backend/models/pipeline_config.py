"""Pipeline configuration Pydantic contract — Story 2.1.

Defines the schema for the project's ``config.yaml`` (data sources, report
schedule, metric thresholds, alert recipients, output settings) plus the SMTP
secrets sourced from environment variables. :meth:`PipelineConfig.load` is the
single entrypoint every agent/pipeline component uses to read configuration —
``backend/pipeline/config.py`` re-exports :class:`PipelineConfig` so both
import paths resolve to this module.

Secrets discipline: SMTP credentials are sourced ONLY from environment
variables (via ``.env`` / ``python-dotenv`` in dev), never from ``config.yaml``
— :meth:`PipelineConfig.load` overwrites any ``smtp`` key present in the YAML
with the environment-sourced values.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import croniter
import structlog
import yaml
from pydantic import BaseModel, EmailStr, Field, ValidationError, field_validator, model_validator

from backend.errors.exceptions import ConfigurationError

DEFAULT_THRESHOLD = 0.15
DEFAULT_CONFIG_PATH = Path("config.yaml")

_VALID_INTERVALS = {"daily", "weekly", "monthly"}
_VALID_FORMATS = {"docx", "pdf"}


class ThresholdConfig(BaseModel):
    """Per-metric fractional change thresholds; 0.15 == +-15%.

    Accepts the flat ``{metric: threshold}`` mapping ``config.yaml`` uses for
    ``metric_thresholds`` directly (wrapped into this model's single field).
    """

    thresholds: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _wrap_bare_mapping(cls, data: Any) -> Any:
        if isinstance(data, dict) and "thresholds" not in data:
            return {"thresholds": data}
        return data

    @field_validator("thresholds")
    @classmethod
    def _positive_thresholds(cls, value: dict[str, float]) -> dict[str, float]:
        for metric, threshold in value.items():
            if threshold <= 0:
                raise ValueError(
                    f"metric_thresholds.{metric} must be > 0, got {threshold}"
                )
        return value

    def get(self, metric: str, default: float = DEFAULT_THRESHOLD) -> float:
        """Return the configured threshold for ``metric``, or the default."""
        return self.thresholds.get(metric, default)


class ScheduleConfig(BaseModel):
    """Report schedule — exactly one of a named interval or a cron expression."""

    interval: str | None = None
    cron: str | None = None

    @field_validator("interval")
    @classmethod
    def _valid_interval(cls, value: str | None) -> str | None:
        if value is not None and value not in _VALID_INTERVALS:
            raise ValueError(
                f"report_schedule.interval must be one of {sorted(_VALID_INTERVALS)}, "
                f"got {value!r}"
            )
        return value

    @field_validator("cron")
    @classmethod
    def _valid_cron(cls, value: str | None) -> str | None:
        if value is not None and not croniter.croniter.is_valid(value):
            raise ValueError(
                f"report_schedule.cron is not a valid cron expression: {value!r}"
            )
        return value

    @model_validator(mode="after")
    def _exactly_one_of_interval_or_cron(self) -> ScheduleConfig:
        if bool(self.interval) == bool(self.cron):
            raise ValueError(
                "report_schedule must set exactly one of 'interval' or 'cron'"
            )
        return self


class DataSourceConfig(BaseModel):
    """File paths or directories the agents pull data from.

    Accepts the flat list ``config.yaml`` uses for ``data_sources`` directly
    (wrapped into this model's single field).
    """

    paths: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _wrap_bare_list(cls, data: Any) -> Any:
        if isinstance(data, list):
            return {"paths": data}
        if isinstance(data, dict) and data and "paths" not in data:
            # Non-empty dict without the expected key means the caller passed
            # a mapping where a list was expected (e.g. a YAML indentation
            # mistake) — reject it. An empty dict is the default-construction
            # path (default_factory=DataSourceConfig with no field present in
            # the parent config) and must fall through unchanged.
            raise ValueError(
                f"data_sources must be a list of file paths, got a mapping: {data!r}"
            )
        return data

    @field_validator("paths")
    @classmethod
    def _non_empty(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("data_sources must be a non-empty list")
        return value


class OutputConfig(BaseModel):
    """Rendered report output settings."""

    format: str = "docx"
    output_dir: str = "output/"

    @field_validator("format")
    @classmethod
    def _valid_format(cls, value: str) -> str:
        if value not in _VALID_FORMATS:
            raise ValueError(
                f"output.format must be one of {sorted(_VALID_FORMATS)}, got {value!r}"
            )
        return value


class AlertConfig(BaseModel):
    """Alert recipient list.

    Accepts the flat list ``config.yaml`` uses for ``alert_recipients``
    directly (wrapped into this model's single field). Email format is
    validated by Pydantic's ``EmailStr``.
    """

    recipients: list[EmailStr] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _wrap_bare_list(cls, data: Any) -> Any:
        if isinstance(data, list):
            return {"recipients": data}
        if isinstance(data, dict) and data and "recipients" not in data:
            # Non-empty dict without the expected key means the caller passed
            # a mapping where a list was expected (e.g. a YAML indentation
            # mistake) — reject it. An empty dict is the default-construction
            # path (default_factory=AlertConfig, field absent from the parent
            # config) and must fall through unchanged.
            raise ValueError(
                f"alert_recipients must be a list of email addresses, got a mapping: {data!r}"
            )
        return data


class SmtpSettings(BaseModel):
    """SMTP credentials — sourced ONLY from environment variables.

    Never populated from ``config.yaml``; see :meth:`PipelineConfig.load`.
    """

    host: str | None = None
    port: int = 587
    username: str | None = None
    password: str | None = None
    from_address: str | None = None


# The methods a Tier-2 imputation policy may name. The four *primitive* methods
# come from ``cleaning_primitives.IMPUTATION_METHODS`` (the single source of
# truth); ``leave_as_is`` is a policy-layer-only choice (resolve → skip, the
# primitive is never called) and is deliberately NOT in that frozenset. Defined
# via a lazy import inside the validator so this models module never imports the
# pipeline layer at load time.
_VALID_COLUMN_KINDS = frozenset({"numeric", "categorical", "datetime"})


def _policy_methods() -> frozenset[str]:
    """Allowlist of imputation methods a policy may name (primitive + leave_as_is)."""
    from backend.pipeline.cleaning_primitives import IMPUTATION_METHODS

    return IMPUTATION_METHODS | {"leave_as_is"}


class ImputationPolicyConfig(BaseModel):
    """Tier-2 null-imputation policy (Story 3.4) — all fields optional.

    ``defaults`` overrides the built-in per-column-*type* default (keys must be
    one of ``numeric | categorical | datetime``); ``columns`` overrides the
    method for a specific column by name (highest precedence). Absent → the
    policy layer's built-in defaults (numeric→median, categorical→mode,
    datetime→forward_fill) apply, so a non-expert is never blocked.

    Every method value is validated against the allowlist
    ``{mean, median, mode, forward_fill, leave_as_is}`` at load time; an unknown
    method raises (surfaced as :class:`ConfigurationError` by
    :meth:`PipelineConfig.load`). Type-appropriateness (e.g. ``mean`` on a
    non-numeric column) is NOT checked here — it surfaces at execution as a
    FAILED action, per AC2.
    """

    defaults: dict[str, str] = Field(default_factory=dict)
    columns: dict[str, str] = Field(default_factory=dict)

    @field_validator("defaults")
    @classmethod
    def _valid_default_keys_and_methods(cls, value: dict[str, str]) -> dict[str, str]:
        methods = _policy_methods()
        for kind, method in value.items():
            if kind not in _VALID_COLUMN_KINDS:
                raise ValueError(
                    f"cleaning.imputation.defaults key {kind!r} is not a column kind; "
                    f"expected one of {sorted(_VALID_COLUMN_KINDS)}"
                )
            if method not in methods:
                raise ValueError(
                    f"cleaning.imputation.defaults.{kind} = {method!r} is not a valid "
                    f"imputation method; expected one of {sorted(methods)}"
                )
        return value

    @field_validator("columns")
    @classmethod
    def _valid_column_methods(cls, value: dict[str, str]) -> dict[str, str]:
        methods = _policy_methods()
        for column, method in value.items():
            if method not in methods:
                raise ValueError(
                    f"cleaning.imputation.columns.{column} = {method!r} is not a valid "
                    f"imputation method; expected one of {sorted(methods)}"
                )
        return value


class CleaningConfig(BaseModel):
    """Opt-in cleaning gate + Tier-2 imputation policy (Story 3.4).

    ``enabled`` is THE opt-in gate — default ``False`` (load-bearing, AC1);
    nothing other than an explicit config/param/flag enable turns cleaning on.
    The whole ``cleaning:`` section is optional: a ``config.yaml`` with no
    ``cleaning:`` key validates unchanged and yields ``enabled=False``.

    Interim home note: this policy lives in ``config.yaml`` only until Epic 4
    Story 4.1a introduces the ``project`` entity, at which point it migrates to
    ``project.cleaning_policy``. Keep this the single interim source.
    """

    enabled: bool = False
    imputation: ImputationPolicyConfig = Field(default_factory=ImputationPolicyConfig)


class PipelineConfig(BaseModel):
    """Root pipeline configuration — the typed contract for ``config.yaml``."""

    data_sources: DataSourceConfig
    report_schedule: ScheduleConfig
    metric_thresholds: ThresholdConfig = Field(default_factory=ThresholdConfig)
    alert_recipients: AlertConfig = Field(default_factory=AlertConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    smtp: SmtpSettings = Field(default_factory=SmtpSettings)
    # Story 3.4 opt-in cleaning gate + Tier-2 imputation policy. Optional and
    # default-off: a config.yaml with no ``cleaning:`` key yields enabled=False.
    cleaning: CleaningConfig = Field(default_factory=CleaningConfig)

    @classmethod
    def load(cls, path: str | Path | None = None) -> PipelineConfig:
        """Load, validate, and return a typed :class:`PipelineConfig`.

        Stateless — re-reads and re-validates ``path`` (default ``config.yaml``
        at the project root) on every call, so a caller that invokes this again
        after the file changes on disk gets the updated values (FR10 hot-reload;
        no process restart or module reimport required). SMTP credentials are
        always sourced from the environment, never from the YAML.
        """
        from dotenv import load_dotenv

        load_dotenv()

        config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH

        try:
            raw_text = config_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ConfigurationError(f"Config file not found: {config_path}") from exc

        try:
            raw_data = yaml.safe_load(raw_text) or {}
        except yaml.YAMLError as exc:
            raise ConfigurationError(
                f"Config file is not valid YAML: {config_path}: {exc}"
            ) from exc

        try:
            smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        except ValueError as exc:
            raise ConfigurationError(
                f"SMTP_PORT environment variable must be an integer: {exc}"
            ) from exc

        raw_data["smtp"] = {
            "host": os.environ.get("SMTP_HOST"),
            "port": smtp_port,
            "username": os.environ.get("SMTP_USERNAME"),
            "password": os.environ.get("SMTP_PASSWORD"),
            "from_address": os.environ.get("SMTP_FROM"),
        }

        try:
            config = cls.model_validate(raw_data)
        except ValidationError as exc:
            raise ConfigurationError(
                f"Invalid configuration in {config_path}: {exc}"
            ) from exc

        structlog.get_logger().info(
            "config_loaded",
            schedule=config.report_schedule.interval or config.report_schedule.cron,
            threshold_keys=sorted(config.metric_thresholds.thresholds.keys()),
            recipient_count=len(config.alert_recipients.recipients),
            output_format=config.output.format,
        )
        return config
