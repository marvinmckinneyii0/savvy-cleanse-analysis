"""Tests for the Drift Engine (Story 2.3).

Covers each of the 7 detection checks in isolation, first-run baseline
creation, auto-rotation after 4 clean runs, counter reset on a HIGH finding,
schema drift, and the ``DriftComputationError`` corrupt-baseline path.

All baseline file writes are scoped to ``tmp_path`` — the real repo-root
``backend/baselines/`` is never touched.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import structlog

from backend.errors.exceptions import DriftComputationError
from backend.models.drift_report import BaselineProfile, DriftReport
from backend.models.quality_report import Severity
from backend.pipeline.drift_engine import DriftEngine


def _profile(df: pd.DataFrame, engine: DriftEngine | None = None) -> BaselineProfile:
    """Build a baseline profile from ``df`` (pure, no I/O)."""
    return (engine or DriftEngine())._build_profile(df, dataset_key="t")


# =========================================================================
# The 7 checks in isolation (compute_drift — pure, no file I/O)
# =========================================================================
class TestChecksInIsolation:
    def test_mean_shift_high(self) -> None:
        # Translation by +40% of the mean moves mean (and median) but leaves std unchanged.
        base = pd.DataFrame({"x": [10.0, 20.0, 30.0, 40.0, 50.0]})
        curr = pd.DataFrame({"x": [22.0, 32.0, 42.0, 52.0, 62.0]})  # +12 == +40% of mean 30
        report = DriftEngine().compute_drift(curr, _profile(base))
        finding = report.numeric_drift[0].mean_shift
        assert finding is not None
        assert finding.severity == Severity.HIGH
        assert report.overall_severity == Severity.HIGH
        # Translation leaves variance untouched.
        assert report.numeric_drift[0].variance_shift is None

    def test_median_shift_high(self) -> None:
        base = pd.DataFrame({"x": [10.0, 20.0, 30.0, 40.0, 50.0]})
        curr = pd.DataFrame({"x": [22.0, 32.0, 42.0, 52.0, 62.0]})
        report = DriftEngine().compute_drift(curr, _profile(base))
        finding = report.numeric_drift[0].median_shift
        assert finding is not None
        assert finding.severity == Severity.HIGH

    def test_variance_shift_high_with_stable_mean(self) -> None:
        # Spread the distribution around the SAME mean/median (30) → variance only.
        base = pd.DataFrame({"x": [20.0, 25.0, 30.0, 35.0, 40.0]})
        curr = pd.DataFrame({"x": [5.0, 17.5, 30.0, 42.5, 55.0]})
        report = DriftEngine().compute_drift(curr, _profile(base))
        col = report.numeric_drift[0]
        assert col.variance_shift is not None
        assert col.variance_shift.severity == Severity.HIGH
        assert col.mean_shift is None  # mean unchanged (30 → 30)
        assert col.median_shift is None

    def test_volume_drift_high(self) -> None:
        pattern = [1000.0, 2000.0, 3000.0, 4000.0]
        base = pd.DataFrame({"x": np.tile(pattern, 25)})  # 100 rows
        curr = pd.DataFrame({"x": np.tile(pattern, 40)})  # 160 rows == +60%
        report = DriftEngine().compute_drift(curr, _profile(base))
        assert report.volume_drift.finding is not None
        assert report.volume_drift.finding.severity == Severity.HIGH
        assert report.volume_drift.pct_change == pytest.approx(0.60)
        # Identical distribution — no numeric finding.
        assert report.numeric_drift[0].mean_shift is None

    def test_categorical_psi_high(self) -> None:
        base = pd.DataFrame({"region": ["north"] * 90 + ["south"] * 10})
        curr = pd.DataFrame({"region": ["north"] * 10 + ["south"] * 90})
        report = DriftEngine().compute_drift(curr, _profile(base))
        psi = report.categorical_drift[0].psi
        assert psi is not None
        assert psi.severity == Severity.HIGH
        assert report.categorical_drift[0].new_categories == []
        assert report.categorical_drift[0].missing_categories == []

    def test_new_and_missing_categories(self) -> None:
        base = pd.DataFrame({"region": ["a"] * 50 + ["b"] * 50})
        curr = pd.DataFrame({"region": ["a"] * 50 + ["c"] * 50})
        report = DriftEngine().compute_drift(curr, _profile(base))
        cat = report.categorical_drift[0]
        assert cat.new_categories == ["c"]
        assert cat.missing_categories == ["b"]
        checks = {(f.check, f.severity) for f in cat.category_findings}
        assert ("missing_category", Severity.HIGH) in checks  # 'b' held 50% > 10%
        assert ("new_category", Severity.MEDIUM) in checks  # 'c' at 50% > 5%

    def test_schema_drift_always_high_and_skips_mismatched_columns(self) -> None:
        base = pd.DataFrame(
            {
                "revenue": [1000.0, 2000.0, 3000.0, 4000.0],
                "region": ["a", "b", "a", "b"],
            }
        )
        curr = pd.DataFrame(
            {
                "revenue": ["1000", "2000", "3000", "4000"],  # dtype change object
                "discount": [1.0, 2.0, 3.0, 4.0],  # added column
                # 'region' removed
            }
        )
        report = DriftEngine().compute_drift(curr, _profile(base))
        assert report.schema_drift.finding is not None
        assert report.schema_drift.finding.severity == Severity.HIGH
        assert report.schema_drift.columns_added == ["discount"]
        assert report.schema_drift.columns_removed == ["region"]
        assert "revenue" in report.schema_drift.dtype_changes
        assert report.overall_severity == Severity.HIGH
        # revenue (dtype-changed) and discount (added) are schema concerns only —
        # no numeric/categorical drift emitted for them; region is gone.
        assert report.numeric_drift == []
        assert report.categorical_drift == []


# =========================================================================
# Degenerate-input guards (compute_drift)
# =========================================================================
class TestComputeDriftGuards:
    def test_empty_current_df_raises(self) -> None:
        base = _profile(pd.DataFrame({"x": [1.0, 2.0, 3.0]}))
        with pytest.raises(DriftComputationError):
            DriftEngine().compute_drift(pd.DataFrame({"x": []}), base)

    def test_zero_baseline_mean_with_nonzero_current_raises(self) -> None:
        base = _profile(pd.DataFrame({"x": [0.0, 0.0, 0.0, 0.0]}))
        curr = pd.DataFrame({"x": [5.0, 6.0, 7.0, 8.0]})
        with pytest.raises(DriftComputationError):
            DriftEngine().compute_drift(curr, base)

    def test_drift_computed_event_emitted(self) -> None:
        base = _profile(pd.DataFrame({"x": [10.0, 20.0, 30.0]}))
        curr = pd.DataFrame({"x": [10.0, 20.0, 30.0]})
        with structlog.testing.capture_logs() as captured:
            DriftEngine().compute_drift(curr, base, pipeline_run_id="run-xyz")
        events = [e for e in captured if e.get("event") == "drift_computed"]
        assert len(events) == 1
        assert events[0]["stage"] == "drift_engine"
        assert events[0]["pipeline_run_id"] == "run-xyz"


# =========================================================================
# run() — baseline lifecycle (file I/O, tmp_path scoped)
# =========================================================================
class TestRunLifecycle:
    def test_first_run_creates_baseline_and_returns_none(
        self, clean_sales_df: pd.DataFrame, tmp_path: Path, pipeline_run_id: str
    ) -> None:
        engine = DriftEngine(baseline_dir=tmp_path)
        with structlog.testing.capture_logs() as captured:
            result = engine.run(clean_sales_df, dataset_key="sales", pipeline_run_id=pipeline_run_id)
        assert result is None
        assert (tmp_path / "sales.json").exists()
        events = [e for e in captured if e.get("event") == "baseline_created"]
        assert len(events) == 1
        assert events[0]["dataset_key"] == "sales"

    def test_second_run_computes_drift(
        self,
        clean_sales_df: pd.DataFrame,
        drifted_sales_df: pd.DataFrame,
        tmp_path: Path,
        pipeline_run_id: str,
    ) -> None:
        engine = DriftEngine(baseline_dir=tmp_path)
        engine.run(clean_sales_df, dataset_key="sales", pipeline_run_id=pipeline_run_id)
        report = engine.run(drifted_sales_df, dataset_key="sales", pipeline_run_id=pipeline_run_id)
        assert isinstance(report, DriftReport)
        assert report.overall_severity == Severity.HIGH  # revenue +40%

    def test_auto_rotation_after_four_clean_runs(
        self, clean_sales_df: pd.DataFrame, tmp_path: Path, pipeline_run_id: str
    ) -> None:
        engine = DriftEngine(baseline_dir=tmp_path)
        # Seed a baseline with counter=3 built from the original clean df.
        seeded = engine._build_profile(clean_sales_df, "sales", consecutive_clean_runs=3)
        engine._save_baseline("sales", seeded)
        original_mean = seeded.columns["revenue"].mean
        assert original_mean is not None

        # A clean run (+3% revenue is below the 5% LOW band → no finding) → 4th clean → rotate.
        current = clean_sales_df.copy()
        current["revenue"] = (current["revenue"] * 1.03).round(2)

        with structlog.testing.capture_logs() as captured:
            report = engine.run(current, dataset_key="sales", pipeline_run_id=pipeline_run_id)
        assert report is not None
        assert report.overall_severity != Severity.HIGH

        rotated = json.loads((tmp_path / "sales.json").read_text())
        assert rotated["consecutive_clean_runs"] == 0
        # Profile now reflects the just-run (rotated) data, not the seed.
        assert rotated["columns"]["revenue"]["mean"] > original_mean
        assert [e for e in captured if e.get("event") == "baseline_rotated"]

    def test_counter_resets_on_high_finding_without_rotating(
        self,
        clean_sales_df: pd.DataFrame,
        drifted_sales_df: pd.DataFrame,
        tmp_path: Path,
        pipeline_run_id: str,
    ) -> None:
        engine = DriftEngine(baseline_dir=tmp_path)
        seeded = engine._build_profile(clean_sales_df, "sales", consecutive_clean_runs=2)
        engine._save_baseline("sales", seeded)
        original_mean = seeded.columns["revenue"].mean

        report = engine.run(drifted_sales_df, dataset_key="sales", pipeline_run_id=pipeline_run_id)
        assert report is not None
        assert report.overall_severity == Severity.HIGH

        after = json.loads((tmp_path / "sales.json").read_text())
        assert after["consecutive_clean_runs"] == 0  # reset
        # Stats unchanged — baseline NOT rotated on a HIGH finding.
        assert after["columns"]["revenue"]["mean"] == pytest.approx(original_mean)

    def test_corrupt_baseline_raises_drift_computation_error(
        self, clean_sales_df: pd.DataFrame, tmp_path: Path, pipeline_run_id: str
    ) -> None:
        (tmp_path / "sales.json").write_text("{ this is not valid json ]", encoding="utf-8")
        engine = DriftEngine(baseline_dir=tmp_path)
        with pytest.raises(DriftComputationError):
            engine.run(clean_sales_df, dataset_key="sales", pipeline_run_id=pipeline_run_id)

    @pytest.mark.parametrize("bad_key", ["../evil", "..", "sub/dir", "a\\b", "/abs", ""])
    def test_path_traversal_dataset_key_rejected(
        self, clean_sales_df: pd.DataFrame, tmp_path: Path, pipeline_run_id: str, bad_key: str
    ) -> None:
        engine = DriftEngine(baseline_dir=tmp_path)
        with pytest.raises(DriftComputationError):
            engine.run(clean_sales_df, dataset_key=bad_key, pipeline_run_id=pipeline_run_id)
