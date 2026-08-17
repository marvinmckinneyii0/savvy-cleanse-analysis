"""End-to-end tests for Story 3.5's Judgment-Required Findings wiring.

Confirms: judgment_required_findings is populated whenever human_only
findings exist, IDENTICALLY regardless of cleaning-enabled state (AC6);
never populated on a halted run (AC8); and never reaches the LLM-facing
payload (mirrors Story 3.3's verification pattern for healing_manifest).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from backend.models.insight_payload import InsightPayload
from backend.models.insight_report import InsightReport, NarrativeSection
from backend.pipeline.orchestrator import run_full_pipeline

_NARRATIVE_TARGET = "backend.pipeline.orchestrator.NarrativeGenerator.generate"
_SAMPLE_DATA = Path(__file__).parent / "sample_data"
_CRITICAL_CSV = _SAMPLE_DATA / "critical_quality_issues.csv"


def _fresh_canned_report(*_args, **_kwargs) -> InsightReport:
    return InsightReport(
        executive_summary="Offline canned narrative.",
        key_findings=[NarrativeSection(title="t", content="c")],
        anomaly_analysis=None,
        recommendations_narrative="None.",
        metadata={"provider": "mock", "timestamp": "2026-08-17T00:00:00Z"},
        fallback=False,
    )


@pytest.fixture()
def tier3_csv(tmp_path: Path) -> Path:
    """A dataset with a real human_only finding (negative_values in a
    non-negativity-implied column) and nothing else."""
    df = pd.DataFrame(
        {
            "region": ["north"] * 10,
            "quantity": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, -5.0],
        }
    )
    path = tmp_path / "tier3.csv"
    df.to_csv(path, index=False)
    return path


@pytest.mark.integration
def test_judgment_required_findings_populated_when_findings_exist(
    tier3_csv: Path, tmp_path: Path
) -> None:
    with patch(_NARRATIVE_TARGET, side_effect=_fresh_canned_report):
        result = run_full_pipeline(
            input_path=tier3_csv, output_path=tmp_path / "r.docx", enable_cleaning=False
        )
    assert result.insight_report is not None
    findings = result.insight_report.judgment_required_findings
    assert len(findings) >= 1
    assert any(f.affected_columns == ["quantity"] for f in findings)


@pytest.mark.integration
def test_judgment_required_findings_identical_regardless_of_cleaning_state(
    tier3_csv: Path, tmp_path: Path
) -> None:
    """AC6: population never depends on the cleaning opt-in gate."""
    with patch(_NARRATIVE_TARGET, side_effect=_fresh_canned_report):
        off = run_full_pipeline(
            input_path=tier3_csv, output_path=tmp_path / "off.docx", enable_cleaning=False
        )
        on = run_full_pipeline(
            input_path=tier3_csv, output_path=tmp_path / "on.docx", enable_cleaning=True
        )
    assert off.insight_report.judgment_required_findings == on.insight_report.judgment_required_findings
    assert len(off.insight_report.judgment_required_findings) >= 1


@pytest.mark.integration
def test_no_human_only_findings_yields_empty_list_not_none(tmp_path: Path) -> None:
    df = pd.DataFrame({"region": ["north"] * 10, "amount": list(range(10))})
    path = tmp_path / "clean.csv"
    df.to_csv(path, index=False)
    with patch(_NARRATIVE_TARGET, side_effect=_fresh_canned_report):
        result = run_full_pipeline(
            input_path=path, output_path=tmp_path / "r.docx", enable_cleaning=False
        )
    assert result.insight_report.judgment_required_findings == []


@pytest.mark.integration
def test_never_populated_on_a_halted_run() -> None:
    """AC8: a CRITICAL-severity finding halts the pipeline before Stage 3+
    (including this story's new field) ever runs."""
    with patch(_NARRATIVE_TARGET) as narrative:
        result = run_full_pipeline(
            input_path=_CRITICAL_CSV, output_path=Path("unused.docx")
        )
    assert result.halted is True
    assert result.insight_report is None
    narrative.assert_not_called()


@pytest.mark.integration
def test_judgment_required_findings_never_reach_the_llm_payload(
    tier3_csv: Path, tmp_path: Path
) -> None:
    captured_args: list[tuple] = []

    def _capture(*args, **kwargs):
        captured_args.append((args, kwargs))
        return _fresh_canned_report()

    with patch(_NARRATIVE_TARGET, side_effect=_capture):
        run_full_pipeline(
            input_path=tier3_csv, output_path=tmp_path / "r.docx", enable_cleaning=False
        )

    assert captured_args, "NarrativeGenerator.generate was never called"
    payload_arg = captured_args[0][0][0]
    assert isinstance(payload_arg, InsightPayload)
    assert not hasattr(payload_arg, "judgment_required_findings")
