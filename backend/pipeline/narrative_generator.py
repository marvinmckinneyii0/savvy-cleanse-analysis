"""NarrativeGenerator — Stage 3: LLM narrative grounded in computed stats.

Transforms an :class:`InsightPayload` (deterministic statistics from the
Insight Engine) into an :class:`InsightReport` (structured prose).

As of Story 2.2 this class is a thin Stage-3 adapter: the retry / fallback /
circuit-breaker resilience logic lives in :class:`backend.core.llm_client.LLMClient`
so the Reporting Agent (2.3) and Monitoring Agent (2.4) can reuse it without
duplication. This file only serializes the payload and delegates.
"""

from __future__ import annotations

from backend.core.llm_client import LLMClient
from backend.models.insight_payload import InsightPayload
from backend.models.insight_report import InsightReport


class NarrativeGenerator:
    """Generates narrative prose from computed statistics via LLM."""

    def __init__(self) -> None:
        self._client = LLMClient()

    def generate(
        self,
        insight_payload: InsightPayload,
        pipeline_run_id: str,
    ) -> InsightReport:
        """Serialize the payload and delegate to :class:`LLMClient`.

        The public call surface is unchanged — the orchestrator still calls
        ``NarrativeGenerator().generate(payload, run_id)`` as Stage 3.
        """
        payload_json = insight_payload.model_dump_json()
        return self._client.generate_narrative(payload_json, pipeline_run_id)
