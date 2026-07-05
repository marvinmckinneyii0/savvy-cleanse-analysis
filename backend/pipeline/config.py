"""Pipeline run configuration.

Story 1.1 installs a stub :class:`PipelineConfig`. The full config surface
(thresholds, LLM provider selection, rendering options, baseline paths) lands
in Story 1.6 when the orchestrator needs it end-to-end. Do not expand this
dataclass ad-hoc — wait for Story 1.6 so the schema is designed as a coherent
whole.

Logging setup (``configure_logging``, ``bind_pipeline_run_id``,
``scoped_pipeline_run_id``) lives in :mod:`backend.core.logging` as of
Story 2.2b — moved out of this module so that neither ``pipeline/`` nor
``agents/`` has to import the other's package for structured logging.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PipelineConfig:
    """Pipeline configuration stub.

    Full schema is defined in Story 1.6 (orchestrator). Intentionally
    empty here so downstream modules can import the symbol without a
    circular dependency on config shape that is not yet designed.
    """
