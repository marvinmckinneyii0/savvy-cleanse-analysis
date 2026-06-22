"""Basic model instantiation tests for quality_report.py models."""

from __future__ import annotations

from backend.models.quality_report import (
    ColumnProfile,
    DataQualityDefect,
    DataQualityReport,
    DefectCategory,
    Severity,
)


class TestSeverity:
    def test_values(self) -> None:
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"

    def test_ordering_by_value(self) -> None:
        assert Severity.CRITICAL == Severity("critical")


class TestDefectCategory:
    def test_all_six_categories(self) -> None:
        assert len(DefectCategory) == 6
        assert DefectCategory.STRUCTURAL_INTEGRITY.value == "structural_integrity"
        assert DefectCategory.COMPLETENESS.value == "completeness"
        assert DefectCategory.CONSISTENCY.value == "consistency"
        assert DefectCategory.UNIQUENESS.value == "uniqueness"
        assert DefectCategory.STATISTICAL_RED_FLAG.value == "statistical_red_flag"
        assert DefectCategory.REFERENTIAL_INTEGRITY.value == "referential_integrity"


class TestDataQualityDefect:
    def test_instantiation(self) -> None:
        defect = DataQualityDefect(
            defect_type="null_values",
            category=DefectCategory.COMPLETENESS,
            severity=Severity.HIGH,
            affected_columns=["revenue"],
            count=15,
            percentage=30.0,
            details="30% nulls in revenue column",
            recommended_action="Impute or drop null rows",
        )
        assert defect.defect_type == "null_values"
        assert defect.severity == Severity.HIGH
        assert defect.affected_columns == ["revenue"]

    def test_serialization_round_trip(self) -> None:
        defect = DataQualityDefect(
            defect_type="duplicate_rows",
            category=DefectCategory.UNIQUENESS,
            severity=Severity.LOW,
            affected_columns=[],
            count=2,
            percentage=4.0,
            details="4% duplicate rows",
            recommended_action="Deduplicate",
        )
        data = defect.model_dump()
        restored = DataQualityDefect.model_validate(data)
        assert restored == defect


class TestColumnProfile:
    def test_numeric_column(self) -> None:
        profile = ColumnProfile(
            column_name="revenue",
            dtype="float64",
            null_count=0,
            null_pct=0.0,
            unique_count=50,
            unique_pct=100.0,
            has_mixed_types=False,
            min_val=100.0,
            max_val=5000.0,
            mean_val=2500.0,
            std_val=1200.0,
        )
        assert profile.min_val == 100.0

    def test_non_numeric_column_none_stats(self) -> None:
        profile = ColumnProfile(
            column_name="region",
            dtype="object",
            null_count=0,
            null_pct=0.0,
            unique_count=4,
            unique_pct=8.0,
            has_mixed_types=False,
        )
        assert profile.min_val is None
        assert profile.max_val is None
        assert profile.mean_val is None
        assert profile.std_val is None


class TestDataQualityReport:
    def test_clean_report(self) -> None:
        report = DataQualityReport(
            overall_severity=Severity.LOW,
            has_critical_issues=False,
            halt_reason=None,
            defects=[],
            column_profiles={},
            total_rows=50,
            total_columns=3,
            overall_quality_score=100.0,
            assessed_at="2026-05-07T00:00:00Z",
        )
        assert report.overall_quality_score == 100.0
        assert report.has_critical_issues is False
        assert report.halt_reason is None

    def test_json_serialization(self) -> None:
        report = DataQualityReport(
            overall_severity=Severity.LOW,
            has_critical_issues=False,
            halt_reason=None,
            defects=[],
            column_profiles={},
            total_rows=50,
            total_columns=3,
            overall_quality_score=100.0,
            assessed_at="2026-05-07T00:00:00Z",
        )
        json_str = report.model_dump_json(indent=2)
        assert '"overall_severity": "low"' in json_str
        assert '"overall_quality_score": 100.0' in json_str

    def test_report_with_defects(self) -> None:
        defect = DataQualityDefect(
            defect_type="null_values",
            category=DefectCategory.COMPLETENESS,
            severity=Severity.CRITICAL,
            affected_columns=["revenue"],
            count=30,
            percentage=60.0,
            details="60% nulls in revenue",
            recommended_action="Investigate data source",
        )
        report = DataQualityReport(
            overall_severity=Severity.CRITICAL,
            has_critical_issues=True,
            halt_reason="Critical findings: 60% nulls in revenue",
            defects=[defect],
            column_profiles={},
            total_rows=50,
            total_columns=3,
            overall_quality_score=70.0,
            assessed_at="2026-05-07T00:00:00Z",
        )
        assert report.has_critical_issues is True
        assert len(report.defects) == 1
        assert report.halt_reason is not None
