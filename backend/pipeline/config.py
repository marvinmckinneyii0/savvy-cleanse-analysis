"""Pipeline configuration and logging setup.

Story 1.1 installs the logging hook and a stub :class:`PipelineConfig`.
The full config surface (thresholds, LLM provider selection, rendering
options, baseline paths) lands in Story 1.6 when the orchestrator needs
it end-to-end. Do not expand this dataclass ad-hoc — wait for Story 1.6
so the schema is designed as a coherent whole.

Logging discipline (enforced here):

* All log output is JSON on stderr, one event per line.
* Every event carries ``pipeline_run_id`` once :func:`bind_pipeline_run_id`
  has been called — contextvars propagate across threads and async tasks
  without threading the ID through every call site.
* Callers — CLI entrypoints, FastAPI startup, pytest session — MUST call
  :func:`configure_logging` explicitly. This module never self-configures
  at import time; that would make test isolation and library usage
  impossible.
* :mod:`logging.basicConfig` is never called (architecture.md:542
  anti-pattern — the stdlib handler would compete with structlog and
  produce mixed plain-text / JSON output).
"""

from __future__ import annotations

from dataclasses import dataclass

import structlog


@dataclass
class PipelineConfig:
    """Pipeline configuration stub.

    Full schema is defined in Story 1.6 (orchestrator). Intentionally
    empty here so downstream modules can import the symbol without a
    circular dependency on config shape that is not yet designed.
    """


def configure_logging() -> None:
    """Install the structlog processor chain for JSON output.

    Idempotent — safe to call multiple times (for example, once from the
    CLI and again from a pytest session-scoped fixture). Must be invoked
    before any ``structlog.get_logger()`` call that expects JSON output.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
    )


def bind_pipeline_run_id(run_id: str) -> None:
    """Bind ``pipeline_run_id=<run_id>`` to the current context.

    Every subsequent log event emitted on the same thread / asyncio task
    will carry this key until it is explicitly cleared or the context
    ends. Use :func:`structlog.contextvars.clear_contextvars` to reset
    between runs in long-lived processes.
    """
    structlog.contextvars.bind_contextvars(pipeline_run_id=run_id)
