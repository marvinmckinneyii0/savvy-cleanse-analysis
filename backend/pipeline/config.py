"""Pipeline run configuration.

:class:`PipelineConfig` is defined in :mod:`backend.models.pipeline_config`
(Story 2.1) — the models layer, alongside every other Pydantic contract. It is
re-exported here so ``from backend.pipeline.config import PipelineConfig``
(the import path the project's epics doc implies) keeps working.

Logging setup (``configure_logging``, ``bind_pipeline_run_id``,
``scoped_pipeline_run_id``) lives in :mod:`backend.core.logging` as of
Story 2.2b — moved out of this module so that neither ``pipeline/`` nor
``agents/`` has to import the other's package for structured logging.
"""

from __future__ import annotations

from backend.models.pipeline_config import PipelineConfig

__all__ = ["PipelineConfig"]
