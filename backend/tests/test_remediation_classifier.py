"""Tests for the Remediation Classifier (Story 3.1).

The mapping these tests guard is load-bearing: the Cleaning Engine (3.2) and
Opt-in Gate (3.4) decide what they may modify from ``remediation_class``, so a
finding mis-tiered toward autonomy is how human-only data gets auto-changed.
The suite therefore pins every mapping explicitly rather than asserting shapes,
and includes a drift guard against the assessor (see
:class:`TestMappingCoversAssessor`).
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

from backend.models.quality_report import (
    DataQualityDefect,
    DefectCategory,
    RemediationClass,
    Severity,
)
from backend.pipeline.data_quality import DataQualityAssessor
from backend.pipeline.remediation_classifier import (
    _DEFECT_TYPE_TO_CLASS,
    classify,
    classify_defect,
    classify_defects,
    classify_report,
)

# Every defect_type the assessor emits today, with the tier it was assigned in
# the Story 3.1 spec. Written out longhand — deriving it from the mapping under
# test would make the test tautological.
EXPECTED: list[tuple[str, RemediationClass]] = [
    # Tier 1 — agent autonomous
    ("mixed_types", RemediationClass.AGENT_AUTONOMOUS),
    ("column_naming", RemediationClass.AGENT_AUTONOMOUS),
    ("case_inconsistency", RemediationClass.AGENT_AUTONOMOUS),
    ("duplicate_rows", RemediationClass.AGENT_AUTONOMOUS),
    # Tier 2 — human sets policy, agent executes
    ("null_values", RemediationClass.HUMAN_POLICY_AGENT_EXECUTION),
    ("non_unique_id", RemediationClass.HUMAN_POLICY_AGENT_EXECUTION),
    # Tier 3 — human only
    ("zero_variance", RemediationClass.HUMAN_ONLY),
    ("extreme_outliers", RemediationClass.HUMAN_ONLY),
    ("extreme_cardinality", RemediationClass.HUMAN_ONLY),
    ("negative_values", RemediationClass.HUMAN_ONLY),
    ("infinite_values", RemediationClass.HUMAN_ONLY),
    ("duplicate_measurement", RemediationClass.HUMAN_ONLY),
]


def _defect(defect_type: str, **overrides: object) -> DataQualityDefect:
    """Build a minimal defect; only ``defect_type`` affects classification."""
    payload: dict[str, object] = {
        "defect_type": defect_type,
        "category": DefectCategory.CONSISTENCY,
        "severity": Severity.LOW,
        "affected_columns": ["col_a"],
        "count": 1,
        "percentage": 1.0,
        "details": "synthetic finding",
        "recommended_action": "none",
    }
    payload.update(overrides)
    return DataQualityDefect(**payload)  # type: ignore[arg-type]


class TestRemediationClassEnum:
    def test_exactly_three_values(self) -> None:
        """Tier 4 is an opt-in overlay (Epic 11), NOT a fourth class."""
        assert len(RemediationClass) == 3

    def test_values(self) -> None:
        assert RemediationClass.AGENT_AUTONOMOUS.value == "agent_autonomous"
        assert (
            RemediationClass.HUMAN_POLICY_AGENT_EXECUTION.value
            == "human_policy_agent_execution"
        )
        assert RemediationClass.HUMAN_ONLY.value == "human_only"


class TestClassify:
    @pytest.mark.parametrize(("defect_type", "expected"), EXPECTED)
    def test_each_defect_type(
        self, defect_type: str, expected: RemediationClass
    ) -> None:
        assert classify(defect_type) == expected

    def test_every_current_defect_type_is_covered(self) -> None:
        assert set(_DEFECT_TYPE_TO_CLASS) == {d for d, _ in EXPECTED}

    @pytest.mark.parametrize(
        "unknown",
        [
            "",
            "not_a_real_defect",
            "near_duplicate",  # plausible future Tier-3 detector
            "DUPLICATE_ROWS",  # case variance must not match
            "duplicate_rows ",  # whitespace variance must not match
        ],
    )
    def test_unmapped_defect_type_fails_safe(self, unknown: str) -> None:
        """The fail-safe: anything unrecognised is never agent-actionable."""
        assert classify(unknown) == RemediationClass.HUMAN_ONLY

    def test_no_tier1_or_tier2_leaks_via_default(self) -> None:
        """Autonomy is only ever granted by an explicit table entry."""
        autonomous = {
            d
            for d, c in _DEFECT_TYPE_TO_CLASS.items()
            if c != RemediationClass.HUMAN_ONLY
        }
        assert autonomous == {
            "mixed_types",
            "column_naming",
            "case_inconsistency",
            "duplicate_rows",
            "null_values",
            "non_unique_id",
        }

    def test_duplicate_rows_and_duplicate_measurement_differ(self) -> None:
        """Similar names, unrelated findings — must not be conflated.

        ``duplicate_rows`` is exact duplicate records (Tier 1).
        ``duplicate_measurement`` is a column-pair correlation signal whose
        remediation is an irreversible schema decision (Tier 3).
        """
        assert classify("duplicate_rows") == RemediationClass.AGENT_AUTONOMOUS
        assert classify("duplicate_measurement") == RemediationClass.HUMAN_ONLY


class TestClassifyDefect:
    def test_stamps_the_class(self) -> None:
        stamped = classify_defect(_defect("duplicate_rows"))
        assert stamped.remediation_class == RemediationClass.AGENT_AUTONOMOUS

    def test_does_not_mutate_input(self) -> None:
        original = _defect("duplicate_rows")
        classify_defect(original)
        assert original.remediation_class == RemediationClass.HUMAN_ONLY

    def test_preserves_all_other_fields(self) -> None:
        original = _defect("null_values", count=42, details="original detail")
        stamped = classify_defect(original)
        assert stamped.model_dump(exclude={"remediation_class"}) == original.model_dump(
            exclude={"remediation_class"}
        )

    def test_idempotent(self) -> None:
        once = classify_defect(_defect("extreme_outliers"))
        twice = classify_defect(once)
        assert once == twice

    def test_corrects_a_wrongly_stamped_defect(self) -> None:
        """Class derives from defect_type, so a bad prior value is overwritten."""
        mis_stamped = _defect(
            "extreme_outliers",
            remediation_class=RemediationClass.AGENT_AUTONOMOUS,
        )
        assert classify_defect(mis_stamped).remediation_class == (
            RemediationClass.HUMAN_ONLY
        )


class TestClassifyCollections:
    def test_classify_defects_stamps_all(self) -> None:
        stamped = classify_defects([_defect(d) for d, _ in EXPECTED])
        assert [s.remediation_class for s in stamped] == [c for _, c in EXPECTED]

    def test_classify_defects_empty(self) -> None:
        assert classify_defects([]) == []

    def test_classify_report_stamps_every_defect(self) -> None:
        assessor = DataQualityAssessor()
        df = pd.DataFrame({"revenue": [1.0, 1.0, None, 5000.0], "name": ["a", "A", "b", "b"]})
        report = assessor.assess_quality(df, "run-classify-report").quality_report
        assert report is not None

        rebuilt = classify_report(report)
        assert len(rebuilt.defects) == len(report.defects)
        for defect in rebuilt.defects:
            assert defect.remediation_class == classify(defect.defect_type)


class TestAssessorStampsFindings:
    """AC 6 — the assessor's output is stamped, not just the classifier's."""

    def test_every_defect_in_a_real_report_is_stamped(self) -> None:
        assessor = DataQualityAssessor()
        df = pd.DataFrame(
            {
                "revenue": [100.0, 100.0, None, -50.0],
                "Name": ["alpha", "ALPHA", "beta", "beta"],
                "flat": [7, 7, 7, 7],
            }
        )
        report = assessor.assess_quality(df, "run-stamped").quality_report

        assert report is not None
        assert report.defects, "fixture should trigger at least one finding"
        for defect in report.defects:
            assert defect.remediation_class == classify(defect.defect_type), (
                f"{defect.defect_type} was not stamped correctly"
            )

    def test_clean_frame_produces_no_unstamped_defects(self) -> None:
        assessor = DataQualityAssessor()
        df = pd.DataFrame({"a": [1, 2, 3, 4], "b": ["w", "x", "y", "z"]})
        report = assessor.assess_quality(df, "run-clean").quality_report

        assert report is not None
        for defect in report.defects:
            assert defect.remediation_class in set(RemediationClass)


class TestMappingCoversAssessor:
    """Drift guard: adding a detector must not silently bypass the mapping.

    A new ``defect_type`` that nobody adds to the table would classify
    ``HUMAN_ONLY`` — safe, but silently un-cleanable and easy to miss. This
    reads the assessor's source and fails loudly instead.
    """

    def test_no_assessor_defect_type_is_missing_from_the_mapping(self) -> None:
        source = Path("backend/pipeline/data_quality.py").read_text(encoding="utf-8")
        emitted = set(re.findall(r'defect_type="([a-z_]+)"', source))

        assert emitted, "failed to parse any defect_type from the assessor"

        missing = emitted - set(_DEFECT_TYPE_TO_CLASS)
        assert not missing, (
            f"defect_type(s) {sorted(missing)} are emitted by DataQualityAssessor "
            "but absent from _DEFECT_TYPE_TO_CLASS. Add them to the mapping in "
            "backend/pipeline/remediation_classifier.py with a deliberate tier."
        )

    def test_mapping_has_no_entries_for_nonexistent_defect_types(self) -> None:
        source = Path("backend/pipeline/data_quality.py").read_text(encoding="utf-8")
        emitted = set(re.findall(r'defect_type="([a-z_]+)"', source))

        stale = set(_DEFECT_TYPE_TO_CLASS) - emitted
        assert not stale, (
            f"mapping entries {sorted(stale)} no longer correspond to any "
            "defect_type emitted by DataQualityAssessor"
        )
