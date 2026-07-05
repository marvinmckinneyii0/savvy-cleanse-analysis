"""Tests for Story 2.2b — LLMClient hardening for multi-caller use.

Covers the three findings from the Story 2.2 code review:
- AC2: JSON logging is guaranteed for callers who never call configure_logging(),
  without clobbering a caller/test that already configured structlog.
- AC3: pipeline_run_id binding is scoped to the call and does not leak into (or
  clear) the ambient contextvars state.
"""

from __future__ import annotations

from unittest.mock import patch

import structlog
from structlog.testing import LogCapture

from backend.core.llm_client import LLMClient
from backend.core.logging import bind_pipeline_run_id, configure_logging
from backend.models.insight_report import InsightReport, NarrativeSection


def _sample_report() -> InsightReport:
    return InsightReport(
        executive_summary="Summary.",
        key_findings=[NarrativeSection(title="A", content="B")],
        metadata={"provider": "claude", "model": "claude-sonnet-4-6", "token_count": 10},
    )


class TestDoesNotClobberExistingConfig:
    def test_generate_narrative_preserves_log_capture(self) -> None:
        """A caller/test that already configured structlog (e.g. a LogCapture
        fixture) must still see its own events after generate_narrative() runs —
        ensure_logging_configured() must not reconfigure structlog out from under it.
        """
        cap = LogCapture()
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                cap,
            ],
        )
        try:
            client = LLMClient()
            with patch.object(client, "_call_claude", return_value=_sample_report()):
                client.generate_narrative("{}", "run-cap")

            events = [e for e in cap.entries if e.get("event") == "narrative_generated"]
            assert len(events) == 1
        finally:
            configure_logging()


class TestConfiguresWhenUnconfigured:
    def test_generate_narrative_configures_json_logging(self) -> None:
        """A caller that never calls configure_logging() itself still gets JSON
        output — generate_narrative() must configure it when nothing else has.
        """
        structlog.reset_defaults()
        assert not structlog.is_configured()
        try:
            client = LLMClient()
            with patch.object(client, "_call_claude", return_value=_sample_report()):
                client.generate_narrative("{}", "run-unconf")

            assert structlog.is_configured()
        finally:
            configure_logging()


class TestScopedBindingDoesNotLeak:
    def test_pipeline_run_id_removed_after_call_with_no_prior_binding(self) -> None:
        """A direct caller with no ambient pipeline_run_id must not leak one into
        later log lines on the same thread/task after the call returns.
        """
        configure_logging()
        structlog.contextvars.clear_contextvars()

        client = LLMClient()
        with patch.object(client, "_call_claude", return_value=_sample_report()):
            client.generate_narrative("{}", "run-A")

        assert "pipeline_run_id" not in structlog.contextvars.get_contextvars()

    def test_pipeline_run_id_restored_after_call_with_prior_binding(self) -> None:
        """The orchestrator pattern: pipeline_run_id is bound once for the whole
        run before Stage 3 runs, and must still be present (not cleared) for
        Stage 4 logging after generate_narrative() returns.
        """
        configure_logging()
        structlog.contextvars.clear_contextvars()
        bind_pipeline_run_id("run-outer")

        client = LLMClient()
        with patch.object(client, "_call_claude", return_value=_sample_report()):
            client.generate_narrative("{}", "run-outer")

        assert (
            structlog.contextvars.get_contextvars().get("pipeline_run_id")
            == "run-outer"
        )
