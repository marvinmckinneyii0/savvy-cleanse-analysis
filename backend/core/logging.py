"""Shared logging / context-binding primitives — Story 2.2b.

Moved out of ``backend/pipeline/config.py`` so that neither ``pipeline/`` nor
``agents/`` (Reporting Agent 2.3, Monitoring Agent 2.4) has to import the other's
package for structured logging setup. Both layers depend on ``backend/core/``;
``backend/core/`` depends on neither.

Logging discipline (enforced here):

* All log output is JSON on stderr, one event per line.
* Every event carries ``pipeline_run_id`` once :func:`bind_pipeline_run_id` (whole
  run) or :func:`scoped_pipeline_run_id` (single call) has bound it — contextvars
  propagate across threads and async tasks without threading the ID through every
  call site.
* Callers — CLI entrypoints, FastAPI startup, pytest session — MUST call
  :func:`configure_logging` explicitly. This module never self-configures at import
  time; that would make test isolation and library usage impossible.
* :mod:`logging.basicConfig` is never called (architecture.md:542 anti-pattern —
  the stdlib handler would compete with structlog and produce mixed plain-text /
  JSON output).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import structlog


def configure_logging() -> None:
    """Install the structlog processor chain for JSON output.

    Idempotent — safe to call multiple times (for example, once from the CLI and
    again from a pytest session-scoped fixture). Must be invoked before any
    ``structlog.get_logger()`` call that expects JSON output.
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


def ensure_logging_configured() -> None:
    """Configure JSON logging only if nothing has configured structlog yet.

    Direct callers (future agents) that skip an explicit ``configure_logging()``
    step still get JSON output. Callers that already configured structlog
    themselves — including test fixtures that install a capture processor — are
    left untouched, so this must never unconditionally call
    :func:`configure_logging`.
    """
    if not structlog.is_configured():
        configure_logging()


def bind_pipeline_run_id(run_id: str) -> None:
    """Bind ``pipeline_run_id=<run_id>`` to the current context, for the run's
    full lifetime.

    Every subsequent log event emitted on the same thread / asyncio task will
    carry this key until it is explicitly cleared or the context ends. Intended
    for whole-process-run callers (e.g. ``orchestrator.run_full_pipeline``) where
    the binding should outlive any single stage. For a single scoped call, use
    :func:`scoped_pipeline_run_id` instead.
    """
    structlog.contextvars.bind_contextvars(pipeline_run_id=run_id)


@contextmanager
def scoped_pipeline_run_id(run_id: str) -> Iterator[None]:
    """Bind ``pipeline_run_id=<run_id>`` for the duration of the ``with`` block only.

    Snapshots whatever contextvars state exists on entry and restores exactly
    that snapshot on exit (success or exception) — a caller that already bound
    ``pipeline_run_id`` (e.g. the orchestrator, for the whole pipeline run) gets
    its own binding restored afterward rather than cleared. A caller with no
    prior binding gets it removed afterward, so it never leaks into unrelated log
    lines on a reused thread/asyncio task.
    """
    with structlog.contextvars.bound_contextvars(pipeline_run_id=run_id):
        yield
