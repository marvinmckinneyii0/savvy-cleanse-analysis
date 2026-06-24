"""Basic model instantiation tests for quality_report.py and insight_payload.py models."""

from __future__ import annotations

from backend.models.insight_report import InsightReport, NarrativeSection
from backend.models.insight_payload import (
    AnomalyRecord,
    ColumnSummary,
    InsightPayload,
    Recommendation,
    SegmentComparison,
    TrendAnalysis,
    TrendPoint,
)
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


# ---- InsightPayload models (Story 1.3) ----


class TestColumnSummary:
    def test_numeric_column(self) -> None:
        cs = ColumnSummary(
            column_name="revenue",
            dtype="numeric",
            count=50,
            null_count=0,
            null_pct=0.0,
            unique_count=50,
            sum_val=50000.0,
            mean_val=1000.0,
            min_val=100.0,
            max_val=5000.0,
            std_val=800.0,
            median_val=900.0,
            q25_val=500.0,
            q75_val=1400.0,
            growth_rate=0.45,
        )
        assert cs.column_name == "revenue"
        assert cs.growth_rate == 0.45

    def test_categorical_column(self) -> None:
        cs = ColumnSummary(
            column_name="region",
            dtype="categorical",
            count=50,
            null_count=0,
            null_pct=0.0,
            unique_count=4,
            top_values=[{"value": "North", "count": 15, "pct": 30.0}],
        )
        assert cs.top_values is not None
        assert cs.sum_val is None

    def test_datetime_column(self) -> None:
        cs = ColumnSummary(
            column_name="date",
            dtype="datetime",
            count=50,
            null_count=0,
            null_pct=0.0,
            unique_count=50,
        )
        assert cs.mean_val is None
        assert cs.top_values is None


class TestTrendAnalysis:
    def test_instantiation(self) -> None:
        tp = TrendPoint(period="2025-01-01", value=100.0, change_pct=5.0)
        ta = TrendAnalysis(
            metric_column="revenue",
            date_column="date",
            trend_direction="increasing",
            trend_points=[tp],
            overall_change_pct=45.0,
            note="Revenue shows an increasing trend",
        )
        assert ta.trend_direction == "increasing"
        assert len(ta.trend_points) == 1

    def test_serialization_round_trip(self) -> None:
        ta = TrendAnalysis(
            metric_column="revenue",
            date_column="date",
            trend_direction="stable",
            trend_points=[],
            note="No significant trend",
        )
        data = ta.model_dump()
        restored = TrendAnalysis.model_validate(data)
        assert restored == ta


class TestSegmentComparison:
    def test_instantiation(self) -> None:
        sc = SegmentComparison(
            segment_column="region",
            metric_column="revenue",
            segments=[{"segment": "North", "mean": 500.0, "sum": 5000.0, "count": 10}],
            note="North leads",
        )
        assert sc.segment_column == "region"
        assert len(sc.segments) == 1


class TestAnomalyRecord:
    def test_instantiation(self) -> None:
        ar = AnomalyRecord(
            column_name="revenue",
            row_indices=[5, 10],
            values=[9999.0, 8888.0],
            mean=500.0,
            std=100.0,
            threshold_sigma=2.0,
            count=2,
            pct=4.0,
            direction="above",
        )
        assert ar.threshold_sigma == 2.0
        assert ar.direction == "above"


class TestRecommendation:
    def test_instantiation(self) -> None:
        rec = Recommendation(
            category="anomaly",
            priority="high",
            message="Review outlier values",
            related_columns=["revenue"],
        )
        assert rec.priority == "high"


class TestInsightPayload:
    def test_instantiation(self) -> None:
        payload = InsightPayload(
            data_quality_findings={"overall_severity": "low"},
            summary=[],
            key_insights=[],
            anomalies=[],
            recommendations=[],
            metadata={"total_rows": 100, "has_temporal_data": False},
        )
        assert payload.metadata["total_rows"] == 100

    def test_json_serialization(self) -> None:
        payload = InsightPayload(
            data_quality_findings={},
            summary=[
                ColumnSummary(
                    column_name="x",
                    dtype="numeric",
                    count=10,
                    null_count=0,
                    null_pct=0.0,
                    unique_count=10,
                    mean_val=5.0,
                )
            ],
            key_insights=[],
            anomalies=[],
            recommendations=[],
            metadata={},
        )
        json_str = payload.model_dump_json()
        assert '"column_name":"x"' in json_str
        assert "NaN" not in json_str


# ---- InsightReport models (Story 1.4) ----


class TestNarrativeSection:
    def test_instantiation(self) -> None:
        section = NarrativeSection(
            title="Revenue Trends",
            content="Revenue increased 45% over the analysis period.",
        )
        assert section.title == "Revenue Trends"
        assert "45%" in section.content

    def test_serialization_round_trip(self) -> None:
        section = NarrativeSection(title="Summary", content="All metrics stable.")
        data = section.model_dump()
        restored = NarrativeSection.model_validate(data)
        assert restored == section


class TestInsightReport:
    def test_full_report(self) -> None:
        report = InsightReport(
            executive_summary="Overall data quality is good with minor anomalies.",
            key_findings=[
                NarrativeSection(title="Growth", content="Revenue grew 12%."),
                NarrativeSection(title="Outliers", content="2 outliers detected."),
            ],
            anomaly_analysis="Two revenue values exceeded 2-sigma threshold.",
            recommendations_narrative="Review outlier transactions for data entry errors.",
            metadata={"provider": "claude", "model": "claude-sonnet-4-20250514", "token_count": 350, "duration_ms": 1200},
        )
        assert report.executive_summary.startswith("Overall")
        assert len(report.key_findings) == 2
        assert report.fallback is False
        assert report.fallback_reason is None

    def test_fallback_report(self) -> None:
        report = InsightReport(
            executive_summary="",
            key_findings=[],
            metadata={"provider": "none", "fallback": True},
            fallback=True,
            fallback_reason="All LLM providers failed after 3 consecutive failures",
        )
        assert report.fallback is True
        assert report.fallback_reason is not None
        assert report.executive_summary == ""
        assert report.key_findings == []

    def test_optional_fields_default_none(self) -> None:
        report = InsightReport(
            executive_summary="Summary text.",
            key_findings=[],
            metadata={},
        )
        assert report.anomaly_analysis is None
        assert report.recommendations_narrative is None
        assert report.fallback is False

    def test_json_serialization(self) -> None:
        report = InsightReport(
            executive_summary="Test summary.",
            key_findings=[NarrativeSection(title="A", content="B")],
            metadata={"provider": "claude"},
        )
        json_str = report.model_dump_json()
        assert '"executive_summary":"Test summary."' in json_str
        restored = InsightReport.model_validate_json(json_str)
        assert restored == report
