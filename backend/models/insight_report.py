"""InsightReport Pydantic models — LLM narrative output contract.

The :class:`InsightReport` is produced by the NarrativeGenerator (Story 1.4)
and consumed by the document renderers (Story 1.5). It carries structured
narrative sections grounded in the pre-computed :class:`InsightPayload`.

When narrative generation fails entirely (circuit breaker), the pipeline
returns a fallback ``InsightReport`` with ``fallback=True`` and empty
narrative sections so the renderer can still produce a data-only report.

Separation of concerns
----------------------
:class:`NarrativeContent` is the *LLM-facing* schema — it contains ONLY the
fields the model generates. :class:`InsightReport` is the *full output
contract* the renderer consumes; it adds ``metadata`` (telemetry) and
``fallback``/``fallback_reason`` (pipeline control), all of which are
populated by code, never by the model. Sending the model a schema that
includes those fields would let a hallucination corrupt pipeline state
(e.g. an LLM-set ``fallback=True`` masking a perfectly good narrative).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.models.drift_report import DriftReport


class NarrativeSection(BaseModel):
    """A titled narrative section grounded in computed statistics."""

    title: str
    content: str


class NarrativeContent(BaseModel):
    """LLM-facing narrative output.

    Contains only fields the model generates. This is the schema handed to
    the provider as the structured-output target — it deliberately excludes
    telemetry and pipeline-control fields so the model cannot set them.
    """

    executive_summary: str
    key_findings: list[NarrativeSection]
    anomaly_analysis: str | None = None
    recommendations_narrative: str | None = None


class InsightReport(BaseModel):
    """Aggregate narrative report — the single output of the NarrativeGenerator.

    Composed server-side from the model's :class:`NarrativeContent` plus
    code-populated ``metadata`` and ``fallback`` fields.
    """

    executive_summary: str
    key_findings: list[NarrativeSection]
    anomaly_analysis: str | None = None
    recommendations_narrative: str | None = None
    metadata: dict = Field(default_factory=dict)
    fallback: bool = False
    fallback_reason: str | None = None
    # Phase 2 (Story 2.4): populated server-side (never by the LLM) so the
    # renderer can emit a deterministic Drift Analysis section. None when no
    # baseline existed for the dataset.
    drift_report: DriftReport | None = None
