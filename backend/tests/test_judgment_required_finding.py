"""Tests for Story 3.5's JudgmentRequiredFinding model and builder."""

from __future__ import annotations

from backend.models.judgment_required_finding import (
    JudgmentRequiredFinding,
    build_judgment_required_findings,
)
from backend.models.quality_report import (
    DataQualityDefect,
    DataQualityReport,
    DefectCategory,
    RemediationClass,
    Severity,
)


def _defect(
    defect_type: str,
    remediation_class: RemediationClass,
    *,
    affected_columns: list[str] | None = None,
    severity: Severity = Severity.MEDIUM,
    count: int = 1,
    percentage: float = 1.0,
    details: str = "test defect",
    recommended_action: str = "test action",
) -> DataQualityDefect:
    return DataQualityDefect(
        defect_type=defect_type,
        category=DefectCategory.STATISTICAL_RED_FLAG,
        severity=severity,
        affected_columns=affected_columns or ["col"],
        count=count,
        percentage=percentage,
        details=details,
        recommended_action=recommended_action,
        remediation_class=remediation_class,
    )


def _report(defects: list[DataQualityDefect]) -> DataQualityReport:
    return DataQualityReport(
        overall_severity=Severity.MEDIUM,
        has_critical_issues=False,
        defects=defects,
        column_profiles={},
        total_rows=10,
        total_columns=3,
        overall_quality_score=0.5,
        assessed_at="2026-08-17T00:00:00Z",
    )


class TestBuildJudgmentRequiredFindings:
    def test_filters_to_human_only_defects_only(self) -> None:
        defects = [
            _defect("extreme_outliers", RemediationClass.HUMAN_ONLY),
            _defect("case_inconsistency", RemediationClass.AGENT_AUTONOMOUS),
            _defect("null_values", RemediationClass.HUMAN_POLICY_AGENT_EXECUTION),
            _defect("negative_values", RemediationClass.HUMAN_ONLY),
        ]
        findings = build_judgment_required_findings(_report(defects))
        assert len(findings) == 2

    def test_preserves_defect_order(self) -> None:
        defects = [
            _defect("negative_values", RemediationClass.HUMAN_ONLY, affected_columns=["a"]),
            _defect("extreme_outliers", RemediationClass.HUMAN_ONLY, affected_columns=["b"]),
            _defect("infinite_values", RemediationClass.HUMAN_ONLY, affected_columns=["c"]),
        ]
        findings = build_judgment_required_findings(_report(defects))
        assert [f.affected_columns for f in findings] == [["a"], ["b"], ["c"]]
        assert [f.sequence for f in findings] == [0, 1, 2]

    def test_projects_only_safe_fields(self) -> None:
        defect = _defect(
            "negative_values",
            RemediationClass.HUMAN_ONLY,
            severity=Severity.HIGH,
            count=5,
            percentage=12.5,
            details="5 negative value(s) in 'quantity'",
            recommended_action="Verify negatives are intentional",
        )
        findings = build_judgment_required_findings(_report([defect]))
        finding = findings[0]
        assert finding.severity == Severity.HIGH
        assert finding.count == 5
        assert finding.percentage == 12.5
        assert finding.detail == "5 negative value(s) in 'quantity'"
        assert finding.recommended_action == "Verify negatives are intentional"
        # No defect_type/category/remediation_class attribute exists at all —
        # a template can never accidentally render internal taxonomy.
        assert not hasattr(finding, "defect_type")
        assert not hasattr(finding, "category")
        assert not hasattr(finding, "remediation_class")

    def test_empty_report_yields_empty_list(self) -> None:
        findings = build_judgment_required_findings(_report([]))
        assert findings == []

    def test_no_human_only_defects_yields_empty_list(self) -> None:
        defects = [
            _defect("case_inconsistency", RemediationClass.AGENT_AUTONOMOUS),
            _defect("null_values", RemediationClass.HUMAN_POLICY_AGENT_EXECUTION),
        ]
        findings = build_judgment_required_findings(_report(defects))
        assert findings == []

    def test_is_pure_and_deterministic(self) -> None:
        defects = [_defect("extreme_outliers", RemediationClass.HUMAN_ONLY)]
        report = _report(defects)
        first = build_judgment_required_findings(report)
        second = build_judgment_required_findings(report)
        assert first == second
        # Report itself is untouched.
        assert report.defects == defects
