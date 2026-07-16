"""SAINT exception hierarchy.

The pipeline distinguishes two kinds of failures — this split is
architectural, not cosmetic, and is enforced by the types defined here.

Result-vs-Exception split
-------------------------
* **Business outcomes** — "the data is bad, halt the pipeline", "drift
  detected, block the report" — are carried on
  :class:`backend.models.pipeline_result.PipelineResult` (``halted=True``,
  ``halt_reason="..."``). They are NOT exceptions. A stage that produces
  a :class:`PipelineResult` with ``halted=True`` has *succeeded at its job*
  of reporting a problem.
* **Infrastructure failures** — the LLM provider is down, the renderer
  cannot write to disk, configuration is missing — raise a subclass of
  :class:`SavvyCleanseError`. These bubble up and are caught by the
  orchestrator, which wraps them in an error envelope.

Rule of thumb: if the user would reasonably want the pipeline to tell them
"this is what's wrong with your data", it's a :class:`PipelineResult`.
If the user would reasonably want the pipeline to tell them "something
broke, retry or file a bug", it's one of these exceptions.

Hierarchy
---------
::

    SavvyCleanseError                  (root)
    ├── PipelineStageError             (any stage failed internally)
    │   ├── LLMProviderError           (Claude/OpenAI/Gemini call failed)
    │   ├── ReportRenderError          (DOCX/PDF render failed)
    │   └── DriftComputationError      (baseline vs current stats failed)
    └── ConfigurationError             (bad env / YAML / missing key)

``ConfigurationError`` is intentionally a *sibling* of
``PipelineStageError``, not a child: a missing API key is not a stage
failure, it is a pre-flight failure raised before any stage starts.

See :doc:`architecture.md` sections 482-506 for full rationale.
"""

from __future__ import annotations


class SavvyCleanseError(Exception):
    """Root of the SAINT exception hierarchy.

    Catch this at the outermost orchestrator boundary to ensure no
    SAINT-internal failure escapes as an unclassified
    :class:`Exception`. Never catch this inside a stage — stages should
    catch specific subclasses or let them propagate.
    """


class PipelineStageError(SavvyCleanseError):
    """A pipeline stage failed due to an infrastructure-level problem.

    Stages raise this (or a subclass) when they cannot continue for reasons
    unrelated to the data itself. Data-quality issues go on
    :class:`backend.models.pipeline_result.PipelineResult` instead.
    """


class LLMProviderError(PipelineStageError):
    """A call to an LLM provider failed after retries.

    The narrative generator raises this after Claude → OpenAI → Gemini
    fallback is exhausted. ``provider`` identifies the last provider
    tried; ``cause`` is the underlying transport or SDK exception.
    """

    def __init__(self, message: str, *, provider: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.provider: str = provider
        self.cause: Exception | None = cause

    def __str__(self) -> str:
        base = super().__str__()
        if self.cause is not None:
            return f"{base} [provider={self.provider}, cause={type(self.cause).__name__}: {self.cause}]"
        return f"{base} [provider={self.provider}]"


class ReportRenderError(PipelineStageError):
    """The DOCX or PDF renderer failed to produce output.

    Typical causes: missing Jinja template, disk full, WeasyPrint
    dependency missing, docxtpl template corruption.
    """


class DriftComputationError(PipelineStageError):
    """Drift detection could not compute a valid statistical result.

    Typical causes: baseline file corrupt, insufficient rows for the
    chosen statistical test, scipy raised on degenerate input.
    """


class ConfigurationError(SavvyCleanseError):
    """Configuration is missing or invalid — pre-flight failure.

    Raised before any stage runs. Examples: required env var not set,
    ``config.yaml`` malformed, Pandera schema mismatch against the
    declared contract. Do NOT use this for runtime data problems —
    those go on :class:`PipelineResult`.
    """
