"""Tests for NarrativeGenerator — Story 1.4.

All LLM provider calls are mocked. Tests cover:
- Successful generation (Task 9)
- Retry logic with exponential backoff (Task 10)
- Provider fallback chain (Task 11)
- Circuit breaker (Task 12)
- 4xx client error non-retry (Task 13)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import structlog
from structlog.testing import LogCapture

from backend.errors.exceptions import LLMProviderError
from backend.models.insight_payload import InsightPayload
from backend.models.insight_report import (
    InsightReport,
    NarrativeContent,
    NarrativeSection,
)
from backend.pipeline.config import configure_logging
from backend.pipeline.narrative_generator import NarrativeGenerator


@pytest.fixture
def insight_payload() -> InsightPayload:
    return InsightPayload(
        data_quality_findings={"overall_severity": "low"},
        summary=[],
        key_insights=[],
        anomalies=[],
        recommendations=[],
        metadata={"total_rows": 100},
    )


@pytest.fixture
def sample_report() -> InsightReport:
    return InsightReport(
        executive_summary="Revenue grew 12% over the period.",
        key_findings=[
            NarrativeSection(title="Growth", content="Revenue grew steadily."),
        ],
        anomaly_analysis="Two outliers detected in Q3.",
        recommendations_narrative="Review outlier transactions.",
        metadata={"provider": "claude", "model": "claude-sonnet-4-20250514", "token_count": 350},
    )


@pytest.fixture
def log_capture():
    cap = LogCapture()
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            cap,
        ],
    )
    yield cap
    configure_logging()


def _make_api_status_error(status_code: int, message: str = "error") -> Exception:
    """Create a mock exception that behaves like anthropic.APIStatusError."""
    exc = Exception(message)
    exc.status_code = status_code  # type: ignore[attr-defined]
    return exc


def _make_timeout_error() -> Exception:
    """Create a mock exception that behaves like anthropic.APITimeoutError."""
    exc = Exception("Request timed out")
    return exc


class TestSuccessfulGeneration:
    """Task 9 — successful generation via Claude."""

    def test_returns_insight_report(
        self,
        insight_payload: InsightPayload,
        sample_report: InsightReport,
        pipeline_run_id: str,
        log_capture: LogCapture,
    ) -> None:
        gen = NarrativeGenerator()

        mock_result = MagicMock()
        mock_result.output_parsed = sample_report
        mock_result.usage.output_tokens = 200
        mock_result.usage.input_tokens = 150

        with patch.object(gen._client, "_call_claude", return_value=sample_report):
            result = gen.generate(insight_payload, pipeline_run_id)

        assert isinstance(result, InsightReport)
        assert result.executive_summary == "Revenue grew 12% over the period."
        assert len(result.key_findings) == 1
        assert result.fallback is False

    def test_logs_narrative_generated(
        self,
        insight_payload: InsightPayload,
        sample_report: InsightReport,
        pipeline_run_id: str,
        log_capture: LogCapture,
    ) -> None:
        gen = NarrativeGenerator()

        with patch.object(gen._client, "_call_claude", return_value=sample_report):
            gen.generate(insight_payload, pipeline_run_id)

        events = [e for e in log_capture.entries if e.get("event") == "narrative_generated"]
        assert len(events) == 1
        assert events[0]["provider"] == "claude"


class TestRetryLogic:
    """Task 10 — retry with exponential backoff."""

    def test_retries_on_timeout_then_succeeds(
        self,
        insight_payload: InsightPayload,
        sample_report: InsightReport,
        pipeline_run_id: str,
        log_capture: LogCapture,
    ) -> None:
        gen = NarrativeGenerator()

        call_count = 0

        def _mock_claude(payload_json: str) -> InsightReport:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise _make_timeout_error()
            return sample_report

        with (
            patch.object(gen._client, "_call_claude", side_effect=_mock_claude),
            patch("backend.core.llm_client.time.sleep") as mock_sleep,
        ):
            result = gen.generate(insight_payload, pipeline_run_id)

        assert result.fallback is False
        assert call_count == 3

        sleep_calls = [c.args[0] for c in mock_sleep.call_args_list]
        assert sleep_calls == [1, 2]

    def test_logs_retry_events(
        self,
        insight_payload: InsightPayload,
        sample_report: InsightReport,
        pipeline_run_id: str,
        log_capture: LogCapture,
    ) -> None:
        gen = NarrativeGenerator()

        call_count = 0

        def _mock_claude(payload_json: str) -> InsightReport:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise _make_timeout_error()
            return sample_report

        with (
            patch.object(gen._client, "_call_claude", side_effect=_mock_claude),
            patch("backend.core.llm_client.time.sleep"),
        ):
            gen.generate(insight_payload, pipeline_run_id)

        retry_events = [e for e in log_capture.entries if e.get("event") == "llm_retry"]
        assert len(retry_events) == 2
        assert retry_events[0]["provider"] == "claude"
        assert retry_events[0]["attempt"] == 1
        assert retry_events[1]["attempt"] == 2


class TestFallbackChain:
    """Task 11 — fallback Claude → OpenAI → Gemini."""

    def test_falls_back_to_openai(
        self,
        insight_payload: InsightPayload,
        pipeline_run_id: str,
        log_capture: LogCapture,
    ) -> None:
        gen = NarrativeGenerator()

        openai_report = InsightReport(
            executive_summary="OpenAI generated this.",
            key_findings=[],
            metadata={"provider": "openai", "model": "gpt-4o", "token_count": 200},
        )

        with (
            patch.object(gen._client, "_call_claude", side_effect=_make_timeout_error()),
            patch.object(gen._client, "_call_openai", return_value=openai_report),
            patch("backend.core.llm_client.time.sleep"),
        ):
            result = gen.generate(insight_payload, pipeline_run_id)

        assert result.metadata["provider"] == "openai"
        assert result.fallback is False

        fallback_events = [e for e in log_capture.entries if e.get("event") == "llm_fallback"]
        assert len(fallback_events) == 1
        assert fallback_events[0]["from_provider"] == "claude"
        assert fallback_events[0]["to_provider"] == "openai"

    def test_full_chain_claude_openai_gemini(
        self,
        insight_payload: InsightPayload,
        pipeline_run_id: str,
        log_capture: LogCapture,
    ) -> None:
        gen = NarrativeGenerator()

        gemini_report = InsightReport(
            executive_summary="Gemini generated this.",
            key_findings=[],
            metadata={"provider": "gemini", "model": "gemini-2.0-flash", "token_count": 180},
        )

        with (
            patch.object(gen._client, "_call_claude", side_effect=_make_timeout_error()),
            patch.object(gen._client, "_call_openai", side_effect=_make_timeout_error()),
            patch.object(gen._client, "_call_gemini", return_value=gemini_report),
            patch("backend.core.llm_client.time.sleep"),
        ):
            result = gen.generate(insight_payload, pipeline_run_id)

        assert result.metadata["provider"] == "gemini"
        assert result.fallback is False


class TestCircuitBreaker:
    """Task 12 — 3 consecutive provider failures → skip."""

    def test_returns_fallback_report(
        self,
        insight_payload: InsightPayload,
        pipeline_run_id: str,
        log_capture: LogCapture,
    ) -> None:
        gen = NarrativeGenerator()

        with (
            patch.object(gen._client, "_call_claude", side_effect=_make_timeout_error()),
            patch.object(gen._client, "_call_openai", side_effect=_make_timeout_error()),
            patch.object(gen._client, "_call_gemini", side_effect=_make_timeout_error()),
            patch("backend.core.llm_client.time.sleep"),
        ):
            result = gen.generate(insight_payload, pipeline_run_id)

        assert result.fallback is True
        assert "failed" in result.fallback_reason.lower()
        assert result.executive_summary == ""
        assert result.key_findings == []

    def test_logs_circuit_breaker_event(
        self,
        insight_payload: InsightPayload,
        pipeline_run_id: str,
        log_capture: LogCapture,
    ) -> None:
        gen = NarrativeGenerator()

        with (
            patch.object(gen._client, "_call_claude", side_effect=_make_timeout_error()),
            patch.object(gen._client, "_call_openai", side_effect=_make_timeout_error()),
            patch.object(gen._client, "_call_gemini", side_effect=_make_timeout_error()),
            patch("backend.core.llm_client.time.sleep"),
        ):
            gen.generate(insight_payload, pipeline_run_id)

        cb_events = [e for e in log_capture.entries if e.get("event") == "llm_circuit_breaker"]
        assert len(cb_events) == 1
        assert cb_events[0]["consecutive_failures"] >= 3


class TestClientErrorNonRetry:
    """Task 13 — 4xx client errors are NOT retried."""

    def test_raises_llm_provider_error(
        self,
        insight_payload: InsightPayload,
        pipeline_run_id: str,
        log_capture: LogCapture,
    ) -> None:
        gen = NarrativeGenerator()

        with (
            patch.object(gen._client, "_call_claude",
                side_effect=_make_api_status_error(400, "Bad request"),
            ),
            pytest.raises(LLMProviderError) as exc_info,
        ):
            gen.generate(insight_payload, pipeline_run_id)

        assert exc_info.value.provider == "claude"
        assert exc_info.value.cause is not None

    def test_no_retry_on_4xx(
        self,
        insight_payload: InsightPayload,
        pipeline_run_id: str,
        log_capture: LogCapture,
    ) -> None:
        gen = NarrativeGenerator()

        call_count = 0
        original_exc = _make_api_status_error(400, "Bad request")

        def _mock_claude(payload_json: str) -> InsightReport:
            nonlocal call_count
            call_count += 1
            raise original_exc

        with (
            patch.object(gen._client, "_call_claude", side_effect=_mock_claude),
            pytest.raises(LLMProviderError),
        ):
            gen.generate(insight_payload, pipeline_run_id)

        assert call_count == 1

    def test_logs_client_error(
        self,
        insight_payload: InsightPayload,
        pipeline_run_id: str,
        log_capture: LogCapture,
    ) -> None:
        gen = NarrativeGenerator()

        with (
            patch.object(gen._client, "_call_claude",
                side_effect=_make_api_status_error(422, "Unprocessable"),
            ),
            pytest.raises(LLMProviderError),
        ):
            gen.generate(insight_payload, pipeline_run_id)

        error_events = [e for e in log_capture.entries if e.get("event") == "llm_client_error"]
        assert len(error_events) == 1
        assert error_events[0]["provider"] == "claude"
        assert error_events[0]["status_code"] == 422


class TestClaudeProviderBody:
    """Guards the real `_call_claude` body — the path mocked out everywhere else.

    These lock the two failures that broke the Claude provider in production:
    a retired model snapshot (404) and reading the wrong SDK response
    attribute (`output_parsed` instead of `parsed_output`).
    """

    def test_uses_current_model_and_parsed_output(self) -> None:
        anthropic = pytest.importorskip("anthropic")

        gen = NarrativeGenerator()
        parsed = NarrativeContent(
            executive_summary="Grounded summary.",
            key_findings=[NarrativeSection(title="A", content="B")],
        )
        mock_result = MagicMock()
        mock_result.parsed_output = parsed
        mock_result.usage.input_tokens = 100
        mock_result.usage.output_tokens = 50

        mock_client = MagicMock()
        mock_client.messages.parse.return_value = mock_result

        with patch.object(anthropic, "Anthropic", return_value=mock_client) as mock_ctor:
            report = gen._client._call_claude("{}")

        # The provider was asked for the current Sonnet, not a retired snapshot.
        _, parse_kwargs = mock_client.messages.parse.call_args
        assert parse_kwargs["model"] == "claude-sonnet-4-6"
        # The LLM schema is the narrative-only model, never the full contract.
        assert parse_kwargs["output_format"] is NarrativeContent
        # The SDK's own retries are disabled so they don't compound our loop.
        _, ctor_kwargs = mock_ctor.call_args
        assert ctor_kwargs.get("max_retries") == 0

        # The narrative is read from the correct attribute and wrapped with telemetry.
        assert isinstance(report, InsightReport)
        assert report.executive_summary == "Grounded summary."
        assert report.metadata == {
            "provider": "claude",
            "model": "claude-sonnet-4-6",
            "token_count": 150,
        }
        assert report.fallback is False
