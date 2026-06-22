"""Tests for the Data Quality Assessment Engine (Story 1.2).

Tests call only the public API — ``DataQualityAssessor.assess_quality()``
— and assert on the returned ``PipelineResult``. Private check methods
are never called directly.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
import structlog

from backend.errors.exceptions import ConfigurationError
from backend.models.quality_report import DefectCategory, Severity
from backend.pipeline.data_quality import DataQualityAssessor


# ------------------------------------------------------------------
# Module-local fixtures
# ------------------------------------------------------------------


@pytest.fixture
def assessor() -> DataQualityAssessor:
    return DataQualityAssessor()


@pytest.fixture
def high_null_df() -> pd.DataFrame:
    """DataFrame with 30% nulls — HIGH severity, no halt."""
    n = 100
    revenue = [float(i * 10) if i % 10 not in (0, 1, 2) else None for i in range(n)]
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=n),
            "region": ["North"] * n,
            "revenue": revenue,
        }
    )


@pytest.fixture
def critical_null_df() -> pd.DataFrame:
    """DataFrame with 60% nulls in revenue — CRITICAL, triggers halt."""
    n = 50
    revenue: list[float | None] = [None] * 30 + [float(i * 100) for i in range(20)]
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=n),
            "region": ["North"] * n,
            "revenue": revenue,
        }
    )


@pytest.fixture
def duplicate_heavy_df() -> pd.DataFrame:
    """DataFrame where 90% of rows are duplicates — CRITICAL uniqueness."""
    base_row = {"date": pd.Timestamp("2026-01-01"), "region": "North", "revenue": 100.0}
    rows = [base_row] * 90 + [
        {"date": pd.Timestamp(f"2026-01-{i:02d}"), "region": "South", "revenue": float(i * 10)}
        for i in range(2, 12)
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def minor_duplicate_df() -> pd.DataFrame:
    """DataFrame with ~3% duplicates — LOW severity."""
    rng = np.random.default_rng(seed=99)
    n = 100
    df = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=n),
            "region": rng.choice(["A", "B", "C"], size=n).astype(object),
            "revenue": rng.uniform(100, 5000, size=n).round(2),
        }
    )
    # Insert 3 exact duplicates of row 0
    for idx in [97, 98, 99]:
        df.iloc[idx] = df.iloc[0]
    return df


@pytest.fixture
def mixed_type_df() -> pd.DataFrame:
    """DataFrame with a column containing mixed int/string values."""
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=10),
            "region": ["North"] * 10,
            "revenue": [1, 2, "three", 4, 5, 6, 7, 8, 9, 10],
        }
    )


@pytest.fixture
def zero_variance_df() -> pd.DataFrame:
    """DataFrame with a constant column — statistical red flag."""
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=50),
            "region": ["North"] * 50,
            "revenue": [100.0] * 50,
        }
    )


@pytest.fixture
def extreme_outlier_df() -> pd.DataFrame:
    """DataFrame with a value 10 std devs from the mean."""
    rng = np.random.default_rng(seed=42)
    revenues = rng.normal(1000.0, 100.0, size=100).round(2).tolist()
    revenues[0] = 5000.0  # ~40 std devs from mean
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=100),
            "region": ["North"] * 100,
            "revenue": revenues,
        }
    )


@pytest.fixture
def negative_revenue_df() -> pd.DataFrame:
    """DataFrame with negative values in 'revenue' column."""
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=10),
            "region": ["North"] * 10,
            "revenue": [100.0, 200.0, -500.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0],
        }
    )


@pytest.fixture
def duplicate_id_df() -> pd.DataFrame:
    """DataFrame with a non-unique 'id' column."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 3, 5, 6, 7, 8, 9, 10],
            "region": ["North"] * 10,
            "revenue": [float(i * 100) for i in range(1, 11)],
        }
    )


# ------------------------------------------------------------------
# 6a — Clean data baseline
# ------------------------------------------------------------------


class TestCleanDataBaseline:
    def test_clean_data_no_defects(
        self, assessor: DataQualityAssessor, clean_sales_df: pd.DataFrame, pipeline_run_id: str
    ) -> None:
        result = assessor.assess_quality(clean_sales_df, pipeline_run_id=pipeline_run_id)
        assert result.halted is False
        assert result.success is True
        assert result.quality_report is not None
        assert result.quality_report.defects == []
        assert result.quality_report.overall_quality_score == 100.0


# ------------------------------------------------------------------
# 6b — Completeness category
# ------------------------------------------------------------------


class TestCompleteness:
    def test_critical_null_halts_pipeline(
        self, assessor: DataQualityAssessor, critical_null_df: pd.DataFrame, pipeline_run_id: str
    ) -> None:
        result = assessor.assess_quality(critical_null_df, pipeline_run_id=pipeline_run_id)
        assert result.halted is True
        assert result.success is False
        assert result.halt_reason is not None
        assert result.quality_report is not None
        assert result.quality_report.has_critical_issues is True

        critical_defects = [
            d for d in result.quality_report.defects if d.severity == Severity.CRITICAL
        ]
        assert len(critical_defects) >= 1
        assert any(d.category == DefectCategory.COMPLETENESS for d in critical_defects)

    def test_high_null_does_not_halt(
        self, assessor: DataQualityAssessor, high_null_df: pd.DataFrame, pipeline_run_id: str
    ) -> None:
        result = assessor.assess_quality(high_null_df, pipeline_run_id=pipeline_run_id)
        assert result.halted is False
        assert result.quality_report is not None

        high_defects = [
            d
            for d in result.quality_report.defects
            if d.severity == Severity.HIGH and d.category == DefectCategory.COMPLETENESS
        ]
        assert len(high_defects) >= 1


# ------------------------------------------------------------------
# 6c — Uniqueness category
# ------------------------------------------------------------------


class TestUniqueness:
    def test_fully_duplicate_rows_critical(
        self, assessor: DataQualityAssessor, duplicate_heavy_df: pd.DataFrame, pipeline_run_id: str
    ) -> None:
        result = assessor.assess_quality(duplicate_heavy_df, pipeline_run_id=pipeline_run_id)
        assert result.halted is True
        assert result.quality_report is not None

        dup_defects = [
            d
            for d in result.quality_report.defects
            if d.category == DefectCategory.UNIQUENESS and d.severity == Severity.CRITICAL
        ]
        assert len(dup_defects) >= 1

    def test_minor_duplicates_not_critical(
        self, assessor: DataQualityAssessor, minor_duplicate_df: pd.DataFrame, pipeline_run_id: str
    ) -> None:
        result = assessor.assess_quality(minor_duplicate_df, pipeline_run_id=pipeline_run_id)
        assert result.halted is False
        assert result.quality_report is not None

        dup_defects = [
            d for d in result.quality_report.defects if d.category == DefectCategory.UNIQUENESS
        ]
        assert len(dup_defects) >= 1
        assert all(d.severity != Severity.CRITICAL for d in dup_defects)


# ------------------------------------------------------------------
# 6d — Structural integrity category
# ------------------------------------------------------------------


class TestStructuralIntegrity:
    def test_mixed_type_column_flagged(
        self, assessor: DataQualityAssessor, mixed_type_df: pd.DataFrame, pipeline_run_id: str
    ) -> None:
        result = assessor.assess_quality(mixed_type_df, pipeline_run_id=pipeline_run_id)
        assert result.quality_report is not None

        structural_defects = [
            d
            for d in result.quality_report.defects
            if d.category == DefectCategory.STRUCTURAL_INTEGRITY
        ]
        assert len(structural_defects) >= 1


# ------------------------------------------------------------------
# 6e — Statistical red flags category
# ------------------------------------------------------------------


class TestStatisticalRedFlags:
    def test_zero_variance_column_flagged(
        self, assessor: DataQualityAssessor, zero_variance_df: pd.DataFrame, pipeline_run_id: str
    ) -> None:
        result = assessor.assess_quality(zero_variance_df, pipeline_run_id=pipeline_run_id)
        assert result.quality_report is not None

        zv_defects = [
            d
            for d in result.quality_report.defects
            if d.defect_type == "zero_variance" and d.severity == Severity.HIGH
        ]
        assert len(zv_defects) >= 1

    def test_extreme_outlier_flagged(
        self, assessor: DataQualityAssessor, extreme_outlier_df: pd.DataFrame, pipeline_run_id: str
    ) -> None:
        result = assessor.assess_quality(extreme_outlier_df, pipeline_run_id=pipeline_run_id)
        assert result.quality_report is not None

        outlier_defects = [
            d
            for d in result.quality_report.defects
            if d.defect_type == "extreme_outliers" and d.severity == Severity.MEDIUM
        ]
        assert len(outlier_defects) >= 1


# ------------------------------------------------------------------
# 6f — Consistency category
# ------------------------------------------------------------------


class TestConsistency:
    def test_negative_revenue_flagged(
        self, assessor: DataQualityAssessor, negative_revenue_df: pd.DataFrame, pipeline_run_id: str
    ) -> None:
        result = assessor.assess_quality(negative_revenue_df, pipeline_run_id=pipeline_run_id)
        assert result.quality_report is not None

        neg_defects = [
            d
            for d in result.quality_report.defects
            if d.category == DefectCategory.CONSISTENCY
            and d.defect_type == "negative_values"
            and d.severity == Severity.HIGH
        ]
        assert len(neg_defects) >= 1


# ------------------------------------------------------------------
# 6g — Referential integrity category
# ------------------------------------------------------------------


class TestReferentialIntegrity:
    def test_duplicate_id_column_flagged(
        self, assessor: DataQualityAssessor, duplicate_id_df: pd.DataFrame, pipeline_run_id: str
    ) -> None:
        result = assessor.assess_quality(duplicate_id_df, pipeline_run_id=pipeline_run_id)
        assert result.quality_report is not None

        id_defects = [
            d
            for d in result.quality_report.defects
            if d.category == DefectCategory.REFERENTIAL_INTEGRITY
            and d.defect_type == "non_unique_id"
            and d.severity == Severity.HIGH
        ]
        assert len(id_defects) >= 1


# ------------------------------------------------------------------
# 6h — Pandera validation failures
# ------------------------------------------------------------------


class TestPanderaValidation:
    def test_empty_dataframe_raises_configuration_error(
        self, assessor: DataQualityAssessor, pipeline_run_id: str
    ) -> None:
        with pytest.raises(ConfigurationError, match="empty"):
            assessor.assess_quality(pd.DataFrame(), pipeline_run_id=pipeline_run_id)

    def test_pandera_schema_error_raises_configuration_error(
        self, assessor: DataQualityAssessor, pipeline_run_id: str
    ) -> None:
        with pytest.raises(ConfigurationError):
            assessor.assess_quality("not a dataframe", pipeline_run_id=pipeline_run_id)  # type: ignore[arg-type]


# ------------------------------------------------------------------
# 6i — Non-critical pass-through (dirty_sales_df)
# ------------------------------------------------------------------


class TestDirtySalesIntegration:
    def test_dirty_sales_df_has_known_defects(
        self, assessor: DataQualityAssessor, dirty_sales_df: pd.DataFrame, pipeline_run_id: str
    ) -> None:
        result = assessor.assess_quality(dirty_sales_df, pipeline_run_id=pipeline_run_id)

        assert result.halted is True
        assert result.quality_report is not None
        assert result.quality_report.has_critical_issues is True

        categories_found = {d.category for d in result.quality_report.defects}
        assert DefectCategory.COMPLETENESS in categories_found

        defect_types = {d.defect_type for d in result.quality_report.defects}
        assert "null_values" in defect_types


# ------------------------------------------------------------------
# 6j — Structlog output
# ------------------------------------------------------------------


class TestStructlogOutput:
    def test_structlog_emits_pipeline_run_id(
        self,
        assessor: DataQualityAssessor,
        clean_sales_df: pd.DataFrame,
        pipeline_run_id: str,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        assessor.assess_quality(clean_sales_df, pipeline_run_id=pipeline_run_id)
        captured = capsys.readouterr()
        output = captured.out + captured.err
        non_empty_lines = [line for line in output.splitlines() if line.strip()]
        assert len(non_empty_lines) >= 1

        found_run_id = False
        for line in non_empty_lines:
            try:
                parsed = json.loads(line)
                if parsed.get("pipeline_run_id") == pipeline_run_id:
                    found_run_id = True
                    break
            except json.JSONDecodeError:
                continue
        assert found_run_id, f"pipeline_run_id '{pipeline_run_id}' not found in structlog output"
