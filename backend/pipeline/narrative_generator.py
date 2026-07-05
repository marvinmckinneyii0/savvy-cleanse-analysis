"""NarrativeGenerator — Stage 3: LLM narrative grounded in computed stats.

Transforms an :class:`InsightPayload` (deterministic statistics from the
Insight Engine) into an :class:`InsightReport` (structured prose). As of
Story 2.2 the retry/fallback/circuit-breaker resilience chain lives in
:class:`backend.core.llm_client.LLMClient`; this class is a thin Stage 3
delegator that binds the pipeline run id and serializes the payload.
"""

from __future__ import annotations

import structlog

from backend.core.llm_client import LLMClient
from backend.models.insight_payload import InsightPayload
from backend.models.insight_report import InsightReport
from backend.pipeline.config import bind_pipeline_run_id


class NarrativeGenerator:
    """Generates narrative prose from computed statistics via LLM."""

    def __init__(self) -> None:
        self._logger = structlog.get_logger().bind(stage="narrative_generator")
        self._client = LLMClient()

    def generate(
        self,
        insight_payload: InsightPayload,
        pipeline_run_id: str,
    ) -> InsightReport:
        """Transform an InsightPayload into a narrated InsightReport.

        Delegates the resilience chain (retry, provider fallback, circuit
        breaker) to :class:`LLMClient`.
        """
        bind_pipeline_run_id(pipeline_run_id)
        payload_json = insight_payload.model_dump_json()
        return self._client.generate_narrative(payload_json, pipeline_run_id)
