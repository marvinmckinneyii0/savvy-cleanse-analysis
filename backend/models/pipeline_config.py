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
only. SMTP credentials come exclusively from the process environment and
``.env`` (read fresh on every ``load()`` — see :data:`_DOTENV_PATH` — so
a credential rotation takes effect on the next run, same as a
``config.yaml`` edit). Env-only keys in the YAML are rejected outright,
and neither the ``config_loaded`` log event nor a
:class:`ConfigurationError` message ever carries credential values,
recipient addresses, or raw invalid input.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Any, Literal, Mapping

import structlog
import yaml
from croniter import croniter
from dotenv import dotenv_values
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    ValidationError,
    model_validator,
)

from backend.errors.exceptions import ConfigurationError

#: Fractional change threshold applied to any metric without an explicit
#: entry in ``metric_thresholds`` (0.15 == ±15%).
DEFAULT_THRESHOLD = 0.15

#: Repo root — this file sits at backend/models/pipeline_config.py, so
#: parents[0]=models, parents[1]=backend, parents[2]=repo root.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

#: Default config file, per architecture target tree (config.yaml at root).
DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"

#: The .env file read (without mutating ``os.environ``) on every load().
#: Module-level so tests can point it at a nonexistent file for isolation.
_DOTENV_PATH = _PROJECT_ROOT / ".env"

#: SmtpSettings field name → environment variable. Single source of truth
#: for env sourcing — .env.example and the test-isolation fixture derive
#: from this mapping.
SMTP_ENV_VARS: dict[str, str] = {
    "host": "SMTP_HOST",
    "port": "SMTP_PORT",
    "username": "SMTP_USERNAME",
    "password": "SMTP_PASSWORD",
    "from_addr": "SMTP_FROM",
}

#: Top-level config keys whose values come exclusively from the
#: environment. load() rejects them in the YAML (they are declared model
#: fields, so ``extra="forbid"`` alone cannot catch them) and injects the
#: env-sourced values itself. Future env-only blocks (e.g. LLM settings)
#: must be added here alongside their injection.
_ENV_ONLY_KEYS = frozenset({"smtp"})

_logger = structlog.get_logger(__name__)


class _UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate mapping keys.

    Plain ``safe_load`` silently applies last-wins to duplicated keys, so
    a second ``metric_thresholds:`` block would discard the first with no
    error — breaking the fail-fast contract that ``extra="forbid"``
    provides for misspelled keys.
    """

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict:
        seen: set[Any] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in seen:
                raise yaml.YAMLError(
                    f"duplicate key {key!r} (line {key_node.start_mark.line + 1})"
                )
            seen.add(key)
        return super().construct_mapping(node, deep)


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
    """Report output settings.

    ``format`` must stay in sync with the vocabulary of
    :class:`backend.pipeline.orchestrator.OutputFormat` (models must not
    import pipeline, so the coupling is enforced by a test instead:
    ``test_output_format_vocabulary_matches_orchestrator``).
    """

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
    port: int = Field(default=587, ge=1, le=65535)
    username: str | None = None
    password: SecretStr | None = None
    from_addr: str | None = None

    @staticmethod
    def env_values(env: Mapping[str, str]) -> dict[str, str]:
        """Raw ``SMTP_*`` values from ``env``, keyed by field name.

        Returned unvalidated so :meth:`PipelineConfig.load` can validate
        them alongside the YAML — a malformed ``SMTP_PORT`` then surfaces
        as a :class:`ConfigurationError` naming ``smtp.port``, not a bare
        ``ValidationError``. Unset/empty vars are omitted (field defaults
        apply).
        """
        return {
            field: env[env_var]
            for field, env_var in SMTP_ENV_VARS.items()
            if env.get(env_var)
        }


class PipelineConfig(BaseModel):
    """Root configuration for the Phase 2 pipeline agents.

    Mirrors the shape of ``config.yaml`` exactly (``extra="forbid"`` —
    an unknown or misspelled key is a validation error, not a silent
    no-op), plus the env-sourced ``smtp`` block injected by :meth:`load`.
    """

    model_config = ConfigDict(extra="forbid")

    data_sources: list[Path] = Field(min_length=1)
    report_schedule: ScheduleConfig
    # gt=0 rejects negative/zero AND NaN (NaN compares False against
    # everything); allow_inf_nan=False closes the +inf hole — either
    # would otherwise silently disable drift detection for that metric.
    metric_thresholds: dict[str, Annotated[float, Field(gt=0, allow_inf_nan=False)]] = Field(
        default_factory=dict
    )
    alert_recipients: list[EmailStr] = Field(default_factory=list)
    output: OutputConfig = Field(default_factory=OutputConfig)
    smtp: SmtpSettings = Field(default_factory=SmtpSettings)

    def threshold_for(self, metric: str) -> float:
        """Per-metric fractional change threshold, falling back to 0.15."""
        return self.metric_thresholds.get(metric, DEFAULT_THRESHOLD)

    @classmethod
    def load(cls, path: str | Path | None = None) -> "PipelineConfig":
        """Read, validate, and return the pipeline configuration.

        Stateless by design (FR10): every call re-reads ``path`` (default:
        ``config.yaml`` at the project root) and re-validates it, so a
        scheduled agent picks up on-disk edits on its next run without a
        process restart. That statelessness covers secrets too: ``.env``
        is re-read per call via :func:`dotenv.dotenv_values` — never
        ``load_dotenv()``, which would bake values into ``os.environ``
        once and ignore rotations for the life of the process. Real
        process environment variables take precedence over ``.env``.
        Keep this cheap and side-effect-free besides the ``config_loaded``
        log event.

        Relative ``data_sources`` and ``output.output_dir`` entries are
        anchored to the config file's directory, so agents launched with
        an arbitrary working directory (cron/systemd) resolve the same
        files a developer running from the repo root does.

        Raises:
            ConfigurationError: missing/unreadable file, malformed or
                duplicate-key YAML, schema violations, or env-only keys
                found in the YAML. Pydantic's ``ValidationError`` never
                escapes this method.
        """
        config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH

        try:
            raw_text = config_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ConfigurationError(f"Cannot read config file {config_path}: {exc}") from exc

        # JSON is a strict subset of YAML, so this parses .json config
        # too — no separate JSON branch needed. NEVER yaml.load with the
        # default loader (arbitrary-object deserialization; NFR4) —
        # _UniqueKeyLoader extends SafeLoader.
        try:
            raw = yaml.load(raw_text, Loader=_UniqueKeyLoader)  # noqa: S506
        except yaml.YAMLError as exc:
            raise ConfigurationError(f"Malformed YAML in {config_path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise ConfigurationError(
                f"Config root must be a mapping, got {type(raw).__name__}: {config_path}"
            )

        # Secrets live in env only (NFR3). Reject rather than silently
        # override so a credential committed to config.yaml is caught.
        for key in sorted(_ENV_ONLY_KEYS & raw.keys()):
            raise ConfigurationError(
                f"config.yaml must not contain an {key!r} section — its values "
                "are sourced from environment variables (see .env.example)"
            )

        # Fresh .env read per call, without mutating os.environ; process
        # env wins over .env, matching python-dotenv's own precedence.
        dotenv = {k: v for k, v in dotenv_values(_DOTENV_PATH).items() if v is not None}
        raw["smtp"] = SmtpSettings.env_values({**dotenv, **os.environ})

        try:
            config = cls.model_validate(raw)
        except ValidationError as exc:
            problems = "; ".join(
                f"{'.'.join(str(part) for part in err['loc']) or '<root>'}: {err['msg']}"
                for err in exc.errors()
            )
            # `from None`: the ValidationError repr embeds raw input
            # values (recipient addresses, env-sourced credentials), so
            # chaining it would leak them into logged tracebacks (DoD:
            # ConfigurationError must not leak secret values).
            raise ConfigurationError(
                f"Invalid configuration in {config_path} — {problems}"
            ) from None

        base_dir = config_path.resolve().parent
        config = config.model_copy(
            update={
                "data_sources": [
                    p if p.is_absolute() else base_dir / p for p in config.data_sources
                ],
                "output": config.output.model_copy(
                    update={
                        "output_dir": config.output.output_dir
                        if config.output.output_dir.is_absolute()
                        else base_dir / config.output.output_dir
                    }
                ),
            }
        )

        # Summary only — never SMTP credentials, never recipient addresses
        # (PII-adjacent; count is enough), never absolute paths (they can
        # carry usernames — project logging discipline).
        try:
            log_path = str(config_path.resolve().relative_to(_PROJECT_ROOT))
        except ValueError:
            log_path = config_path.name
        _logger.info(
            "config_loaded",
            config_path=log_path,
            schedule=config.report_schedule.describe(),
            threshold_keys=sorted(config.metric_thresholds),
            recipient_count=len(config.alert_recipients),
            output_format=config.output.format,
            data_source_count=len(config.data_sources),
        )
        return config
