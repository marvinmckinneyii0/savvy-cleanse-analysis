"""NarrativeGenerator — Stage 3: LLM narrative grounded in computed stats.

Transforms an :class:`InsightPayload` (deterministic statistics from the
Insight Engine) into an :class:`InsightReport` (structured prose) using
Claude Structured Outputs.

As of Story 2.2 the retry / fallback / circuit-breaker machinery lives in
:mod:`backend.core.llm_client` so the Phase 2 agents can reuse it. This
class remains Stage 3 of the pipeline with an unchanged public surface —
it binds the run id, serializes the payload, and delegates to
:class:`~backend.core.llm_client.LLMClient`.
"""

from __future__ import annotations

from backend.core.llm_client import LLMClient
from backend.models.insight_payload import InsightPayload
from backend.models.insight_report import InsightReport
from backend.pipeline.config import bind_pipeline_run_id


class NarrativeGenerator:
    """Generates narrative prose from computed statistics via LLM."""

    def __init__(self) -> None:
        self._client = LLMClient()

    def generate(
        self,
        insight_payload: InsightPayload,
        pipeline_run_id: str,
    ) -> InsightReport:
        """Transform an InsightPayload into a narrated InsightReport.

        Tries Claude first, then OpenAI, then Gemini. Each provider gets
        up to 3 retry attempts with exponential backoff. If all providers
        fail, returns a fallback InsightReport.
        """
        bind_pipeline_run_id(pipeline_run_id)
        payload_json = insight_payload.model_dump_json()
        return self._client.generate_narrative(payload_json, pipeline_run_id)
