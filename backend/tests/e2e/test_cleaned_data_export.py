"""End-to-end tests for the Story 3.6 cleaned-data export.

These tests exercise the export through the real Typer CLI. Narrative generation
is patched to a canned report so tests do not require live provider calls.

Key requirements:
- Export is explicit-only and requires cleaning enabled.
- Halted runs never export.
- Safe file handling: default no-overwrite; explicit overwrite flag required.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from typer.testing import CliRunner

from backend.models.insight_report import InsightReport, NarrativeSection
from backend.pipeline.orchestrator import app

_SAMPLE_DATA = Path(__file__).parent / "sample_data"
_CRITICAL_CSV = _SAMPLE_DATA / "critical_quality_issues.csv"

_NARRATIVE_TARGET = "backend.pipeline.orchestrator.NarrativeGenerator.generate"


@pytest.fixture()
def canned_insight_report() -> InsightReport:
    return InsightReport(
        executive_summary="Offline canned narrative.",
        key_findings=[NarrativeSection(title="t", content="c")],
        anomaly_analysis=None,
        recommendations_narrative="None.",
        metadata={"provider": "mock", "timestamp": "2026-08-11T00:00:00Z"},
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


@pytest.mark.integration
def test_cli_cleaned_output_requires_cleaning_enabled(
    dirty_csv: Path, tmp_path: Path, canned_insight_report: InsightReport
) -> None:
    runner = CliRunner()
    report_out = tmp_path / "r.docx"
    cleaned_out = tmp_path / "cleaned.csv"

    with patch(_NARRATIVE_TARGET, return_value=canned_insight_report):
        res = runner.invoke(
            app,
            [
                "--input",
                str(dirty_csv),
                "--output",
                str(report_out),
                "--cleaned-output",
                str(cleaned_out),
            ],
        )

    assert res.exit_code != 0
    assert not cleaned_out.exists()


@pytest.mark.integration
def test_cli_cleaned_output_writes_csv_when_enabled(
    dirty_csv: Path, tmp_path: Path, canned_insight_report: InsightReport
) -> None:
    runner = CliRunner()
    report_out = tmp_path / "r.docx"
    cleaned_out = tmp_path / "cleaned.csv"

    with patch(_NARRATIVE_TARGET, return_value=canned_insight_report):
        res = runner.invoke(
            app,
            [
                "--input",
                str(dirty_csv),
                "--output",
                str(report_out),
                "--clean",
                "--cleaned-output",
                str(cleaned_out),
            ],
        )

    assert res.exit_code == 0, res.output
    assert cleaned_out.exists()

    exported = pd.read_csv(cleaned_out)
    assert exported["value"].isna().sum() == 0
    # Deterministic default for numeric imputation is median.
    assert exported.loc[1, "value"] == 60.0


@pytest.mark.integration
def test_cli_halted_run_never_exports(
    tmp_path: Path, canned_insight_report: InsightReport
) -> None:
    runner = CliRunner()
    report_out = tmp_path / "r.docx"
    cleaned_out = tmp_path / "cleaned.csv"

    with patch(_NARRATIVE_TARGET, return_value=canned_insight_report):
        res = runner.invoke(
            app,
            [
                "--input",
                str(_CRITICAL_CSV),
                "--output",
                str(report_out),
                "--clean",
                "--cleaned-output",
                str(cleaned_out),
            ],
        )

    assert res.exit_code != 0
    assert not cleaned_out.exists()


@pytest.mark.integration
def test_cli_cleaned_output_existing_path_requires_overwrite_flag(
    dirty_csv: Path, tmp_path: Path, canned_insight_report: InsightReport
) -> None:
    runner = CliRunner()
    report_out = tmp_path / "r.docx"
    cleaned_out = tmp_path / "cleaned.csv"
    cleaned_out.write_text("sentinel", encoding="utf-8")

    with patch(_NARRATIVE_TARGET, return_value=canned_insight_report):
        res = runner.invoke(
            app,
            [
                "--input",
                str(dirty_csv),
                "--output",
                str(report_out),
                "--clean",
                "--cleaned-output",
                str(cleaned_out),
            ],
        )

    assert res.exit_code != 0
    assert cleaned_out.read_text(encoding="utf-8") == "sentinel"
    assert not report_out.exists()


@pytest.mark.integration
def test_cli_cleaned_output_overwrite_flag_replaces_file(
    dirty_csv: Path, tmp_path: Path, canned_insight_report: InsightReport
) -> None:
    runner = CliRunner()
    report_out = tmp_path / "r.docx"
    cleaned_out = tmp_path / "cleaned.csv"
    cleaned_out.write_text("sentinel", encoding="utf-8")

    with patch(_NARRATIVE_TARGET, return_value=canned_insight_report):
        res = runner.invoke(
            app,
            [
                "--input",
                str(dirty_csv),
                "--output",
                str(report_out),
                "--clean",
                "--cleaned-output",
                str(cleaned_out),
                "--overwrite-cleaned-output",
            ],
        )

    assert res.exit_code == 0, res.output
    exported = pd.read_csv(cleaned_out)
    assert exported["value"].isna().sum() == 0


@pytest.mark.integration
def test_cli_cleaned_output_missing_parent_dir_fails(
    dirty_csv: Path, tmp_path: Path, canned_insight_report: InsightReport
) -> None:
    runner = CliRunner()
    report_out = tmp_path / "r.docx"
    cleaned_out = tmp_path / "missing" / "cleaned.csv"

    with patch(_NARRATIVE_TARGET, return_value=canned_insight_report):
        res = runner.invoke(
            app,
            [
                "--input",
                str(dirty_csv),
                "--output",
                str(report_out),
                "--clean",
                "--cleaned-output",
                str(cleaned_out),
            ],
        )

    assert res.exit_code != 0
    assert not cleaned_out.exists()
    assert not report_out.exists()
