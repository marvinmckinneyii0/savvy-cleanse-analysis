"""NarrativeGenerator — Stage 3: LLM narrative grounded in computed stats.

Transforms an :class:`InsightPayload` (deterministic statistics from the
Insight Engine) into an :class:`InsightReport` (structured prose) using
Claude Structured Outputs.

Resilience layers (architecture.md §525-529):

1. **Retry** — 3 attempts per provider, exponential backoff (1s, 2s, 4s).
2. **Fallback** — Claude → OpenAI → Gemini.
3. **Circuit breaker** — 3 consecutive provider-level failures → skip
   narrative, return a fallback InsightReport so the pipeline continues.
4. **4xx guard** — client errors are never retried (they indicate a code
   bug, not a transient failure).
"""

from __future__ import annotations

import os
import time
from typing import Any

import structlog

from backend.errors.exceptions import LLMProviderError
from backend.models.insight_payload import InsightPayload
from backend.models.insight_report import InsightReport, NarrativeSection

_BACKOFF_DELAYS = [1, 2, 4]
_MAX_ATTEMPTS = 3
_CIRCUIT_BREAKER_THRESHOLD = 3

_SYSTEM_PROMPT = (
    "You are a data analyst writing a professional narrative report. "
    "You will receive a JSON payload of pre-computed statistics. "
    "Your job is to NARRATE these statistics into clear, professional prose. "
    "CRITICAL RULES:\n"
    "- Reference ONLY numbers that appear in the provided data.\n"
    "- Do NOT independently compute, invent, or hallucinate any numerical values.\n"
    "- Do NOT perform any arithmetic on the provided numbers.\n"
    "- Write in third person, professional tone.\n"
    "- Structure your response as an InsightReport with: executive_summary, "
    "key_findings (list of titled sections), anomaly_analysis (if anomalies exist), "
    "and recommendations_narrative (if recommendations exist)."
)


class NarrativeGenerator:
    """Generates narrative prose from computed statistics via LLM."""

    def __init__(self) -> None:
        self._logger = structlog.get_logger().bind(stage="narrative_generator")

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
        structlog.contextvars.bind_contextvars(pipeline_run_id=pipeline_run_id)
        payload_json = insight_payload.model_dump_json()

        providers: list[tuple[str, Any]] = [
            ("claude", self._call_claude),
            ("openai", self._call_openai),
            ("gemini", self._call_gemini),
        ]

        consecutive_failures = 0
        providers_tried: list[str] = []

        for i, (provider_name, call_fn) in enumerate(providers):
            if consecutive_failures >= _CIRCUIT_BREAKER_THRESHOLD:
                break

            providers_tried.append(provider_name)

            try:
                report = self._try_provider(
                    provider_name, call_fn, payload_json,
                )
                self._logger.info(
                    "narrative_generated",
                    provider=provider_name,
                    model=report.metadata.get("model", "unknown"),
                    token_count=report.metadata.get("token_count", 0),
                    duration_ms=report.metadata.get("duration_ms", 0),
                )
                return report

            except LLMProviderError:
                raise

            except Exception:
                consecutive_failures += 1

                if consecutive_failures >= _CIRCUIT_BREAKER_THRESHOLD:
                    break

                if i + 1 < len(providers):
                    next_provider = providers[i + 1][0]
                    self._logger.warning(
                        "llm_fallback",
                        from_provider=provider_name,
                        to_provider=next_provider,
                        reason="all_attempts_exhausted",
                    )

        self._logger.error(
            "llm_circuit_breaker",
            consecutive_failures=consecutive_failures,
            providers_tried=providers_tried,
        )
        return InsightReport(
            executive_summary="",
            key_findings=[],
            metadata={
                "provider": "none",
                "fallback": True,
                "providers_tried": providers_tried,
            },
            fallback=True,
            fallback_reason=(
                f"All LLM providers failed after {consecutive_failures} "
                "consecutive failures"
            ),
        )

    def _try_provider(
        self,
        provider_name: str,
        call_fn: Any,
        payload_json: str,
    ) -> InsightReport:
        """Attempt up to ``_MAX_ATTEMPTS`` calls to a single provider."""
        last_exc: Exception | None = None

        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                start = time.perf_counter()
                report = call_fn(payload_json)
                duration_ms = int((time.perf_counter() - start) * 1000)
                report.metadata["duration_ms"] = duration_ms
                return report

            except Exception as exc:
                if self._is_client_error(exc):
                    self._logger.error(
                        "llm_client_error",
                        provider=provider_name,
                        status_code=getattr(exc, "status_code", None),
                        error=str(exc),
                    )
                    raise LLMProviderError(
                        f"Client error from {provider_name}",
                        provider=provider_name,
                        cause=exc,
                    ) from exc

                last_exc = exc
                self._logger.warning(
                    "llm_retry",
                    provider=provider_name,
                    attempt=attempt,
                    error_type=type(exc).__name__,
                    backoff_seconds=_BACKOFF_DELAYS[attempt - 1] if attempt <= len(_BACKOFF_DELAYS) else _BACKOFF_DELAYS[-1],
                )

                if attempt < _MAX_ATTEMPTS:
                    time.sleep(_BACKOFF_DELAYS[attempt - 1])

        raise last_exc  # type: ignore[misc]

    def _is_client_error(self, exc: Exception) -> bool:
        status = getattr(exc, "status_code", None)
        if status is not None and 400 <= status < 500:
            return True
        return False

    def _call_claude(self, payload_json: str) -> InsightReport:
        import anthropic

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        result = client.messages.parse(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"{_SYSTEM_PROMPT}\n\n"
                        f"Here is the computed data payload:\n{payload_json}"
                    ),
                },
            ],
            output_format=InsightReport,
        )
        report: InsightReport = result.output_parsed  # type: ignore[assignment]
        report.metadata.update({
            "provider": "claude",
            "model": "claude-sonnet-4-20250514",
            "token_count": getattr(result.usage, "output_tokens", 0)
            + getattr(result.usage, "input_tokens", 0),
        })
        return report

    def _call_openai(self, payload_json: str) -> InsightReport:
        import openai

        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        result = client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"{_SYSTEM_PROMPT}\n\n"
                        f"Here is the computed data payload:\n{payload_json}"
                    ),
                },
            ],
            response_format=InsightReport,
        )
        report = result.choices[0].message.parsed  # type: ignore[union-attr]
        report.metadata.update({  # type: ignore[union-attr]
            "provider": "openai",
            "model": "gpt-4o",
            "token_count": getattr(result.usage, "total_tokens", 0),
        })
        return report  # type: ignore[return-value]

    def _call_gemini(self, payload_json: str) -> InsightReport:
        from google import genai

        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        result = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=(
                f"{_SYSTEM_PROMPT}\n\n"
                f"Here is the computed data payload:\n{payload_json}"
            ),
            config={
                "response_mime_type": "application/json",
                "response_schema": InsightReport,
            },
        )
        import json
        report = InsightReport.model_validate(json.loads(result.text))
        report.metadata.update({
            "provider": "gemini",
            "model": "gemini-2.0-flash",
            "token_count": getattr(
                getattr(result, "usage_metadata", None), "total_token_count", 0
            ),
        })
        return report
