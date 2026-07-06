"""Pipeline configuration and logging setup.

Story 1.1 installed the logging hooks; the config schema is defined in
Story 2.1 — see :mod:`backend.models.pipeline_config`. This module
re-exports :class:`PipelineConfig` so the historical import path
``from backend.pipeline.config import PipelineConfig`` keeps working
while the Pydantic contract lives in the models layer alongside the
other pipeline contracts.

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

import structlog

from backend.models.pipeline_config import PipelineConfig

__all__ = ["PipelineConfig", "bind_pipeline_run_id", "configure_logging"]


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
