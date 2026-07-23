"""End-to-end tests for the Story 3.4 opt-in cleaning gate.

Exercises the gate through the real orchestrator (narrative patched offline):
default-off is a no-op that carries no ``cleaning_result``; explicit enable runs
the Tier-1 + Tier-2 pass and attaches the merged result while the report stages
still run on the ORIGINAL frame; a halted run never cleans; and the CLI
``--clean/--no-clean`` flag drives the same gate (default no-clean).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from typer.testing import CliRunner

from backend.models.cleaning_result import CleaningOperation, CleaningResult, CleaningStatus
from backend.models.insight_report import InsightReport, NarrativeSection
from backend.pipeline.orchestrator import OutputFormat, app, run_full_pipeline

_SAMPLE_DATA = Path(__file__).parent / "sample_data"
_CLEAN_CSV = _SAMPLE_DATA / "clean_sales.csv"
_CRITICAL_CSV = _SAMPLE_DATA / "critical_quality_issues.csv"

_NARRATIVE_TARGET = "backend.pipeline.orchestrator.NarrativeGenerator.generate"


@pytest.fixture()
def canned_insight_report() -> InsightReport:
    return InsightReport(
        executive_summary="Offline canned narrative.",
        key_findings=[NarrativeSection(title="t", content="c")],
        anomaly_analysis=None,
        recommendations_narrative="None.",
        metadata={"provider": "mock", "timestamp": "2026-07-23T00:00:00Z"},
        fallback=False,
    )


@pytest.fixture()
def dirty_csv(tmp_path: Path) -> Path:
    """10-row CSV with one null in a numeric column (10% → MEDIUM, no halt)."""
    df = pd.DataFrame(
        {
            "region": ["north"] * 10,
            "value": [10.0, None, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
        }
    )
    path = tmp_path / "dirty.csv"
    df.to_csv(path, index=False)
    return path


# --------------------------------------------------------------------------
# AC 1 — default OFF: no cleaning component, no cleaning_result
# --------------------------------------------------------------------------
@pytest.mark.integration
def test_default_run_has_no_cleaning_result(
    tmp_path: Path, canned_insight_report: InsightReport
) -> None:
    out = tmp_path / "r.docx"
    with patch(_NARRATIVE_TARGET, return_value=canned_insight_report):
        result = run_full_pipeline(input_path=_CLEAN_CSV, output_path=out)
    assert result.success is True
    assert result.cleaning_result is None  # default off, nothing constructed


@pytest.mark.integration
def test_explicit_disable_has_no_cleaning_result(
    dirty_csv: Path, tmp_path: Path, canned_insight_report: InsightReport
) -> None:
    out = tmp_path / "r.docx"
    with patch(_NARRATIVE_TARGET, return_value=canned_insight_report):
        result = run_full_pipeline(
            input_path=dirty_csv, output_path=out, enable_cleaning=False
        )
    assert result.cleaning_result is None


# --------------------------------------------------------------------------
# AC 1 / AC 8 — enabled: cleaning runs, result attached, report still produced
# --------------------------------------------------------------------------
@pytest.mark.integration
def test_enabled_run_imputes_and_attaches_result(
    dirty_csv: Path, tmp_path: Path, canned_insight_report: InsightReport
) -> None:
    out = tmp_path / "r.docx"
    with patch(_NARRATIVE_TARGET, return_value=canned_insight_report):
        result = run_full_pipeline(
            input_path=dirty_csv, output_path=out, enable_cleaning=True
        )
    assert result.success is True
    assert isinstance(result.cleaning_result, CleaningResult)
    # The report stages still ran (Q1: report is produced on the original frame,
    # independently of cleaning).
    assert result.insight_report is not None
    # The single null was imputed by the Tier-2 policy.
    imputations = [
        a
        for a in result.cleaning_result.actions
        if a.operation == CleaningOperation.NULL_IMPUTATION
        and a.status == CleaningStatus.APPLIED
    ]
    assert len(imputations) == 1
    assert imputations[0].target_columns == ["value"]
    assert out.exists()


@pytest.mark.integration
def test_enabling_does_not_change_the_report(
    dirty_csv: Path, tmp_path: Path, canned_insight_report: InsightReport
) -> None:
    """Report output is identical whether or not cleaning is enabled (Q1)."""
    with patch(_NARRATIVE_TARGET, return_value=canned_insight_report):
        off = run_full_pipeline(
            input_path=dirty_csv, output_path=tmp_path / "off.docx", enable_cleaning=False
        )
        on = run_full_pipeline(
            input_path=dirty_csv, output_path=tmp_path / "on.docx", enable_cleaning=True
        )
    # Same insight report both ways; only cleaning_result differs.
    assert on.insight_report == off.insight_report
    assert off.cleaning_result is None
    assert on.cleaning_result is not None


# --------------------------------------------------------------------------
# AC 1 (halt safety) — cleaning never runs on data a halt flagged
# --------------------------------------------------------------------------
@pytest.mark.integration
def test_halted_run_never_cleans(tmp_path: Path) -> None:
    out = tmp_path / "r.docx"
    with patch(_NARRATIVE_TARGET) as narrative:
        result = run_full_pipeline(
            input_path=_CRITICAL_CSV, output_path=out, enable_cleaning=True
        )
    assert result.halted is True
    assert result.cleaning_result is None
    narrative.assert_not_called()


# --------------------------------------------------------------------------
# AC 1 — CLI surface: --clean/--no-clean drives the gate, default no-clean
# --------------------------------------------------------------------------
@pytest.mark.integration
def test_cli_no_clean_is_default(
    dirty_csv: Path, tmp_path: Path, canned_insight_report: InsightReport
) -> None:
    out = tmp_path / "r.docx"
    runner = CliRunner()
    with patch(_NARRATIVE_TARGET, return_value=canned_insight_report):
        captured: dict[str, object] = {}
        real = run_full_pipeline

        def _spy(*args: object, **kwargs: object):
            captured.update(kwargs)
            return real(*args, **kwargs)

        with patch("backend.pipeline.orchestrator.run_full_pipeline", side_effect=_spy):
            res = runner.invoke(
                app, ["--input", str(dirty_csv), "--output", str(out), "--format", "docx"]
            )
    assert res.exit_code == 0, res.output
    assert captured["enable_cleaning"] is False  # default is no-clean


@pytest.mark.integration
def test_cli_clean_flag_enables_gate(
    dirty_csv: Path, tmp_path: Path, canned_insight_report: InsightReport
) -> None:
    out = tmp_path / "r.docx"
    runner = CliRunner()
    with patch(_NARRATIVE_TARGET, return_value=canned_insight_report):
        captured: dict[str, object] = {}
        real = run_full_pipeline

        def _spy(*args: object, **kwargs: object):
            captured.update(kwargs)
            return real(*args, **kwargs)

        with patch("backend.pipeline.orchestrator.run_full_pipeline", side_effect=_spy):
            res = runner.invoke(
                app, ["--input", str(dirty_csv), "--output", str(out), "--clean"]
            )
    assert res.exit_code == 0, res.output
    assert captured["enable_cleaning"] is True
    assert captured["cleaning_config"] is not None  # policy loaded from config.yaml
