"""InsightReport Pydantic models — LLM narrative output contract.

The :class:`InsightReport` is produced by the NarrativeGenerator (Story 1.4)
and consumed by the document renderers (Story 1.5). It carries structured
narrative sections grounded in the pre-computed :class:`InsightPayload`.

When narrative generation fails entirely (circuit breaker), the pipeline
returns a fallback ``InsightReport`` with ``fallback=True`` and empty
narrative sections so the renderer can still produce a data-only report.
"""

from __future__ import annotations

from pydantic import BaseModel


class NarrativeSection(BaseModel):
    """A titled narrative section grounded in computed statistics."""

    title: str
    content: str


class InsightReport(BaseModel):
    """Aggregate narrative report — the single output of the NarrativeGenerator."""

    executive_summary: str
    key_findings: list[NarrativeSection]
    anomaly_analysis: str | None = None
    recommendations_narrative: str | None = None
    metadata: dict
    fallback: bool = False
    fallback_reason: str | None = None
