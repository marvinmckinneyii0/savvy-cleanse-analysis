"""End-to-end tests for Story 3.3's Healing Manifest wiring.

Exercises the real orchestrator (narrative patched offline, a FRESH
InsightReport instance per call — unlike some of Story 3.4's gate tests,
which reuse one canned fixture across two runs and would trivially pass an
identity comparison). Confirms: healing_manifest is None when cleaning is
off, populated with real entries when cleaning is on, narrative content is
identical either way, no Tier-3 finding is ever referenced, and
healing_manifest content never reaches the LLM-facing payload.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from backend.models.insight_payload import InsightPayload
from backend.models.insight_report import InsightReport, NarrativeSection
from backend.models.quality_report import RemediationClass
from backend.pipeline.orchestrator import run_full_pipeline

_NARRATIVE_TARGET = "backend.pipeline.orchestrator.NarrativeGenerator.generate"


def _fresh_canned_report(*_args, **_kwargs) -> InsightReport:
    """A NEW InsightReport instance per call — mirrors production, where
    NarrativeGenerator.generate() always constructs a fresh object."""
    return InsightReport(
        executive_summary="Offline canned narrative.",
        key_findings=[NarrativeSection(title="t", content="c")],
        anomaly_analysis=None,
        recommendations_narrative="None.",
        metadata={"provider": "mock", "timestamp": "2026-08-17T00:00:00Z"},
        fallback=False,
    )


@pytest.fixture()
def dirty_csv(tmp_path: Path) -> Path:
    df = pd.DataFrame(
        {
            "region": ["north"] * 10,
            "value": [10.0, None, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
        }
    )
    path = tmp_path / "dirty.csv"
    df.to_csv(path, index=False)
    return path


@pytest.mark.integration
def test_healing_manifest_absent_when_cleaning_off(
    dirty_csv: Path, tmp_path: Path
) -> None:
    with patch(_NARRATIVE_TARGET, side_effect=_fresh_canned_report):
        result = run_full_pipeline(
            input_path=dirty_csv, output_path=tmp_path / "off.docx", enable_cleaning=False
        )
    assert result.insight_report is not None
    assert result.insight_report.healing_manifest is None


@pytest.mark.integration
def test_healing_manifest_populated_when_cleaning_on(
    dirty_csv: Path, tmp_path: Path
) -> None:
    with patch(_NARRATIVE_TARGET, side_effect=_fresh_canned_report):
        result = run_full_pipeline(
            input_path=dirty_csv, output_path=tmp_path / "on.docx", enable_cleaning=True
        )
    assert result.insight_report is not None
    manifest = result.insight_report.healing_manifest
    assert manifest is not None
    assert len(manifest.entries) == len(result.cleaning_result.actions)
    assert sum(manifest.outcome_counts.values()) == len(manifest.entries)


@pytest.mark.integration
def test_narrative_content_identical_regardless_of_cleaning(
    dirty_csv: Path, tmp_path: Path
) -> None:
    """AC9: narrative sections must not differ; only healing_manifest presence does."""
    with patch(_NARRATIVE_TARGET, side_effect=_fresh_canned_report):
        off = run_full_pipeline(
            input_path=dirty_csv, output_path=tmp_path / "off.docx", enable_cleaning=False
        )
        on = run_full_pipeline(
            input_path=dirty_csv, output_path=tmp_path / "on.docx", enable_cleaning=True
        )

    assert off.insight_report.executive_summary == on.insight_report.executive_summary
    assert off.insight_report.key_findings == on.insight_report.key_findings
    assert off.insight_report.anomaly_analysis == on.insight_report.anomaly_analysis
    assert (
        off.insight_report.recommendations_narrative
        == on.insight_report.recommendations_narrative
    )
    assert off.insight_report.healing_manifest is None
    assert on.insight_report.healing_manifest is not None


@pytest.mark.integration
def test_no_tier3_finding_referenced_in_wired_manifest(
    dirty_csv: Path, tmp_path: Path
) -> None:
    with patch(_NARRATIVE_TARGET, side_effect=_fresh_canned_report):
        result = run_full_pipeline(
            input_path=dirty_csv, output_path=tmp_path / "on.docx", enable_cleaning=True
        )
    manifest = result.insight_report.healing_manifest
    assert manifest is not None
    assert all(
        entry.remediation_class != RemediationClass.HUMAN_ONLY for entry in manifest.entries
    )


@pytest.mark.integration
def test_healing_manifest_has_no_shaped_attribute_on_insight_payload() -> None:
    """Structural check (AC7): InsightPayload — the LLM-facing schema — has no
    healing_manifest-shaped field, so there is no code path by which manifest
    content could be threaded into the LLM prompt."""
    assert "healing_manifest" not in InsightPayload.model_fields
    assert "cleaning_result" not in InsightPayload.model_fields


@pytest.mark.integration
def test_llm_prompt_payload_excludes_healing_manifest_content(
    dirty_csv: Path, tmp_path: Path
) -> None:
    """Confirms end-to-end: even though healing_manifest ends up on the
    rendered InsightReport, the LLM (mocked here as NarrativeGenerator.generate)
    is invoked with only `(payload, pipeline_run_id)` — payload is an
    InsightPayload, which per the prior test has no cleaning-shaped field."""
    captured_args: list[tuple] = []

    def _capture(*args, **kwargs):
        captured_args.append((args, kwargs))
        return _fresh_canned_report()

    with patch(_NARRATIVE_TARGET, side_effect=_capture):
        run_full_pipeline(
            input_path=dirty_csv, output_path=tmp_path / "on.docx", enable_cleaning=True
        )

    assert captured_args, "NarrativeGenerator.generate was never called"
    payload_arg = captured_args[0][0][0]
    assert isinstance(payload_arg, InsightPayload)
    assert not hasattr(payload_arg, "healing_manifest")
    assert not hasattr(payload_arg, "cleaning_result")
