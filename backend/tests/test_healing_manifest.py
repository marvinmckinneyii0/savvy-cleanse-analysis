"""Tests for Story 3.3's Healing Manifest: classification, sanitization, and
end-to-end manifest construction against every real `CleaningAction` shape
Story 3.2's engine and Story 3.4's policy layer can emit.
"""

from __future__ import annotations

import pandas as pd
import pytest

from backend.models.cleaning_result import (
    CleaningAction,
    CleaningOperation,
    CleaningResult,
    CleaningScope,
    CleaningStatus,
)
from backend.models.healing_manifest import (
    REPORT_SEMANTICS_DISCLOSURE,
    HealingManifest,
    ManifestOutcome,
    build_healing_manifest,
    classify_outcome,
    sanitize_manifest_text,
)
from backend.models.pipeline_config import ImputationPolicyConfig
from backend.models.quality_report import (
    DataQualityDefect,
    DataQualityReport,
    DefectCategory,
    RemediationClass,
    Severity,
)
from backend.pipeline.cleaning_engine import CleaningEngine
from backend.pipeline.data_quality import DataQualityAssessor
from backend.rules.cleaning_coordinator import clean_dataset
from backend.rules.cleaning_policy import apply_imputation_policy


def _action(**overrides) -> CleaningAction:
    defaults: dict = {
        "operation": CleaningOperation.CASE_NORMALIZATION,
        "defect_type": "case_inconsistency",
        "remediation_class": RemediationClass.AGENT_AUTONOMOUS,
        "status": CleaningStatus.APPLIED,
        "scope": CleaningScope.COLUMN,
        "target_columns": ["region"],
        "rows_affected": 0,
        "values_changed": 3,
        "detail": "Normalized casing in 'region': 3 value(s) rewritten.",
    }
    defaults.update(overrides)
    return CleaningAction(**defaults)


class TestClassifyOutcomeTier1Shapes:
    """Every real Tier-1 (`CleaningEngine`) action-emitting path."""

    def test_applied_with_rows_affected_is_applied(self) -> None:
        action = _action(
            operation=CleaningOperation.DEDUPLICATION,
            status=CleaningStatus.APPLIED,
            rows_affected=2,
            values_changed=0,
        )
        assert classify_outcome(action) == ManifestOutcome.APPLIED

    def test_applied_with_values_changed_is_applied(self) -> None:
        action = _action(status=CleaningStatus.APPLIED, rows_affected=0, values_changed=3)
        assert classify_outcome(action) == ManifestOutcome.APPLIED

    def test_applied_dedup_with_zero_rows_removed_is_no_effect(self) -> None:
        action = _action(
            operation=CleaningOperation.DEDUPLICATION,
            status=CleaningStatus.APPLIED,
            rows_affected=0,
            values_changed=0,
        )
        assert classify_outcome(action) == ManifestOutcome.NO_EFFECT

    def test_applied_case_normalization_with_zero_effect_is_no_effect(self) -> None:
        action = _action(status=CleaningStatus.APPLIED, rows_affected=0, values_changed=0)
        assert classify_outcome(action) == ManifestOutcome.NO_EFFECT

    def test_applied_type_coercion_with_zero_effect_is_no_effect(self) -> None:
        action = _action(
            operation=CleaningOperation.TYPE_COERCION,
            status=CleaningStatus.APPLIED,
            rows_affected=0,
            values_changed=0,
        )
        assert classify_outcome(action) == ManifestOutcome.NO_EFFECT

    def test_applied_header_normalization_with_zero_effect_is_no_effect(self) -> None:
        action = _action(
            operation=CleaningOperation.HEADER_NORMALIZATION,
            status=CleaningStatus.APPLIED,
            rows_affected=0,
            values_changed=0,
        )
        assert classify_outcome(action) == ManifestOutcome.NO_EFFECT

    def test_tier1_no_registered_operation_skip_is_skipped(self) -> None:
        action = _action(
            operation=CleaningOperation.NO_OP,
            status=CleaningStatus.SKIPPED,
            rows_affected=0,
            values_changed=0,
        )
        assert classify_outcome(action) == ManifestOutcome.SKIPPED

    def test_tier1_failed_is_failed(self) -> None:
        action = _action(
            status=CleaningStatus.FAILED,
            error="ValueError: boom",
        )
        assert classify_outcome(action) == ManifestOutcome.FAILED


class TestClassifyOutcomeTier2Shapes:
    """Every real Tier-2 (`cleaning_policy`) action-emitting path."""

    def test_imputation_applied_is_applied(self) -> None:
        action = _action(
            operation=CleaningOperation.NULL_IMPUTATION,
            remediation_class=RemediationClass.HUMAN_POLICY_AGENT_EXECUTION,
            status=CleaningStatus.APPLIED,
            values_changed=2,
        )
        assert classify_outcome(action) == ManifestOutcome.APPLIED

    def test_imputation_no_effect_marker_is_no_effect(self) -> None:
        action = _action(
            operation=CleaningOperation.NULL_IMPUTATION,
            remediation_class=RemediationClass.HUMAN_POLICY_AGENT_EXECUTION,
            status=CleaningStatus.SKIPPED,
            values_changed=0,
            parameters={"method": "median", "source": "default", "manifest_outcome_hint": "no_effect"},
        )
        assert classify_outcome(action) == ManifestOutcome.NO_EFFECT

    def test_leave_as_is_skip_is_skipped(self) -> None:
        action = _action(
            operation=CleaningOperation.NO_OP,
            remediation_class=RemediationClass.HUMAN_POLICY_AGENT_EXECUTION,
            status=CleaningStatus.SKIPPED,
            parameters={"method": "leave_as_is", "source": "override"},
        )
        assert classify_outcome(action) == ManifestOutcome.SKIPPED

    def test_non_imputation_tier2_skip_is_skipped(self) -> None:
        action = _action(
            operation=CleaningOperation.NO_OP,
            defect_type="non_unique_id",
            remediation_class=RemediationClass.HUMAN_POLICY_AGENT_EXECUTION,
            status=CleaningStatus.SKIPPED,
        )
        assert classify_outcome(action) == ManifestOutcome.SKIPPED

    def test_imputation_failed_is_failed(self) -> None:
        action = _action(
            operation=CleaningOperation.NULL_IMPUTATION,
            remediation_class=RemediationClass.HUMAN_POLICY_AGENT_EXECUTION,
            status=CleaningStatus.FAILED,
            error="KeyError: 'column not in frame'",
        )
        assert classify_outcome(action) == ManifestOutcome.FAILED


class TestClassifyOutcomeFailsClosed:
    def test_skipped_non_op_without_marker_stays_skipped(self) -> None:
        """The regression test for the rejected design: a future 'declined
        before execution' shape carries the same operation/defect_type/
        remediation_class tuple as the real no-effect case but has no marker
        — it must classify as SKIPPED, never guessed as NO_EFFECT."""
        action = _action(
            operation=CleaningOperation.NULL_IMPUTATION,
            remediation_class=RemediationClass.HUMAN_POLICY_AGENT_EXECUTION,
            status=CleaningStatus.SKIPPED,
            values_changed=0,
            parameters={"method": "median", "source": "default"},  # no hint key
        )
        assert classify_outcome(action) == ManifestOutcome.SKIPPED

    def test_unrelated_marker_value_does_not_trigger_no_effect(self) -> None:
        action = _action(
            operation=CleaningOperation.NULL_IMPUTATION,
            status=CleaningStatus.SKIPPED,
            parameters={"manifest_outcome_hint": "something_else"},
        )
        assert classify_outcome(action) == ManifestOutcome.SKIPPED


class TestSanitizeManifestText:
    def test_short_text_passes_through_unchanged(self) -> None:
        assert sanitize_manifest_text("short detail") == "short detail"

    def test_long_text_is_truncated_with_ellipsis(self) -> None:
        text = "x" * 500
        result = sanitize_manifest_text(text, max_len=300)
        assert len(result) == 300
        assert result.endswith("…")


class TestFailedEntrySanitization:
    def test_raw_cell_value_in_error_never_reaches_manifest_detail(self) -> None:
        action = _action(
            operation=CleaningOperation.TYPE_COERCION,
            status=CleaningStatus.FAILED,
            target_columns=["code"],
            error="ValueError: could not convert string to float: 'super-secret-client-name'",
        )
        result = CleaningResult(
            pipeline_run_id="run-1",
            total_findings=1,
            autonomous_findings=1,
            actions=[action],
            rows_before=10,
            rows_after=10,
            columns_before=3,
            columns_after=3,
            cleaned_at="2026-01-01T00:00:00+00:00",
        )
        manifest = build_healing_manifest(result)
        assert "super-secret-client-name" not in manifest.entries[0].detail
        assert "ValueError" in manifest.entries[0].detail
        assert "code" in manifest.entries[0].detail

    def test_failed_action_without_error_field_still_renders(self) -> None:
        action = _action(status=CleaningStatus.FAILED, error=None)
        result = CleaningResult(
            pipeline_run_id="run-1",
            total_findings=1,
            autonomous_findings=1,
            actions=[action],
            rows_before=1,
            rows_after=1,
            columns_before=1,
            columns_after=1,
            cleaned_at="2026-01-01T00:00:00+00:00",
        )
        manifest = build_healing_manifest(result)
        assert manifest.entries[0].detail  # non-empty, no crash

    def test_error_not_following_type_colon_message_convention_fails_closed(self) -> None:
        """If `action.error` doesn't contain the expected 'Type: message'
        delimiter, the whole string must NOT be trusted as a safe type name —
        it must fall back to the generic label, not leak verbatim."""
        action = _action(
            status=CleaningStatus.FAILED,
            target_columns=["code"],
            error="a raw message with no colon-space delimiter and a value 'super-secret-client-name'",
        )
        result = CleaningResult(
            pipeline_run_id="run-1",
            total_findings=1,
            autonomous_findings=1,
            actions=[action],
            rows_before=1,
            rows_after=1,
            columns_before=1,
            columns_after=1,
            cleaned_at="2026-01-01T00:00:00+00:00",
        )
        manifest = build_healing_manifest(result)
        assert "super-secret-client-name" not in manifest.entries[0].detail
        assert "an error" in manifest.entries[0].detail

    def test_failed_detail_respects_the_length_cap(self) -> None:
        """Altitude-review finding: the FAILED branch used to bypass
        sanitize_manifest_text's length cap entirely (many long target_columns
        could produce an unbounded detail string)."""
        action = _action(
            status=CleaningStatus.FAILED,
            target_columns=[f"column_{i}" for i in range(100)],
            error="ValueError: boom",
        )
        result = CleaningResult(
            pipeline_run_id="run-1",
            total_findings=1,
            autonomous_findings=1,
            actions=[action],
            rows_before=1,
            rows_after=1,
            columns_before=1,
            columns_after=1,
            cleaned_at="2026-01-01T00:00:00+00:00",
        )
        manifest = build_healing_manifest(result)
        assert len(manifest.entries[0].detail) <= 300


class TestBuildHealingManifestOrderingAndProvenance:
    def test_entries_preserve_cleaning_result_actions_order(self) -> None:
        actions = [
            _action(target_columns=["a"], detail="first"),
            _action(operation=CleaningOperation.DEDUPLICATION, target_columns=["b"], detail="second"),
            _action(status=CleaningStatus.FAILED, target_columns=["c"], error="ValueError: x"),
        ]
        result = CleaningResult(
            pipeline_run_id="run-1",
            total_findings=3,
            autonomous_findings=3,
            actions=actions,
            rows_before=10,
            rows_after=10,
            columns_before=3,
            columns_after=3,
            cleaned_at="2026-01-01T00:00:00+00:00",
        )
        manifest = build_healing_manifest(result)
        assert [e.sequence for e in manifest.entries] == [0, 1, 2]
        assert [e.target_columns for e in manifest.entries] == [["a"], ["b"], ["c"]]

    def test_original_status_and_outcome_both_preserved(self) -> None:
        action = _action(
            operation=CleaningOperation.NULL_IMPUTATION,
            remediation_class=RemediationClass.HUMAN_POLICY_AGENT_EXECUTION,
            status=CleaningStatus.SKIPPED,
            parameters={"manifest_outcome_hint": "no_effect"},
        )
        result = CleaningResult(
            pipeline_run_id="run-1",
            total_findings=1,
            autonomous_findings=0,
            actions=[action],
            rows_before=1,
            rows_after=1,
            columns_before=1,
            columns_after=1,
            cleaned_at="2026-01-01T00:00:00+00:00",
        )
        manifest = build_healing_manifest(result)
        entry = manifest.entries[0]
        assert entry.original_status == CleaningStatus.SKIPPED
        assert entry.outcome == ManifestOutcome.NO_EFFECT

    def test_outcome_counts_summarize_without_affecting_order(self) -> None:
        actions = [
            _action(status=CleaningStatus.APPLIED, values_changed=1),
            _action(status=CleaningStatus.APPLIED, values_changed=1),
            _action(operation=CleaningOperation.NO_OP, status=CleaningStatus.SKIPPED),
        ]
        result = CleaningResult(
            pipeline_run_id="run-1",
            total_findings=3,
            autonomous_findings=3,
            actions=actions,
            rows_before=1,
            rows_after=1,
            columns_before=1,
            columns_after=1,
            cleaned_at="2026-01-01T00:00:00+00:00",
        )
        manifest = build_healing_manifest(result)
        assert manifest.outcome_counts["applied"] == 2
        assert manifest.outcome_counts["skipped"] == 1
        assert manifest.outcome_counts["failed"] == 0
        assert manifest.outcome_counts["no_effect"] == 0

    def test_report_semantics_disclosure_is_the_constant(self) -> None:
        manifest = HealingManifest(
            pipeline_run_id="run-1",
            cleaned_at="2026-01-01T00:00:00+00:00",
            rows_before=1,
            rows_after=1,
            columns_before=1,
            columns_after=1,
        )
        assert manifest.report_semantics_disclosure == REPORT_SEMANTICS_DISCLOSURE
        assert "working copy" in REPORT_SEMANTICS_DISCLOSURE
        assert "original data was not modified" in REPORT_SEMANTICS_DISCLOSURE

    def test_empty_actions_yields_empty_manifest_not_error(self) -> None:
        result = CleaningResult(
            pipeline_run_id="run-1",
            total_findings=0,
            autonomous_findings=0,
            actions=[],
            rows_before=5,
            rows_after=5,
            columns_before=2,
            columns_after=2,
            cleaned_at="2026-01-01T00:00:00+00:00",
        )
        manifest = build_healing_manifest(result)
        assert manifest.entries == []
        assert sum(manifest.outcome_counts.values()) == 0


class TestBuildHealingManifestAgainstRealFixture:
    """Integration: build a manifest from a REAL CleaningResult produced by the
    Tier-1+Tier-2 coordinator against `cleaning_dirty_df` (Tier-1/2/3 mixed)."""

    def test_real_coordinator_output_classifies_without_error(
        self, cleaning_dirty_df: pd.DataFrame
    ) -> None:
        quality_report = DataQualityAssessor().assess_quality(
            cleaning_dirty_df, "run-healing-manifest"
        ).quality_report
        _, result = clean_dataset(
            cleaning_dirty_df, quality_report, ImputationPolicyConfig(), "run-healing-manifest"
        )
        manifest = build_healing_manifest(result)

        assert len(manifest.entries) == len(result.actions)
        assert [e.sequence for e in manifest.entries] == list(range(len(result.actions)))
        # Every entry has a valid outcome; nothing raised.
        for entry in manifest.entries:
            assert entry.outcome in set(ManifestOutcome)

    def test_no_tier3_finding_appears_in_manifest(self, cleaning_dirty_df: pd.DataFrame) -> None:
        """Tier-3 `human_only` findings never become CleaningActions at all
        (3.4 AC6) — so they cannot appear in the manifest either. This test
        pins that boundary from the manifest's side."""
        quality_report = DataQualityAssessor().assess_quality(
            cleaning_dirty_df, "run-healing-manifest"
        ).quality_report
        _, result = clean_dataset(
            cleaning_dirty_df, quality_report, ImputationPolicyConfig(), "run-healing-manifest"
        )
        manifest = build_healing_manifest(result)

        assert all(
            entry.remediation_class != RemediationClass.HUMAN_ONLY for entry in manifest.entries
        )


def _null_defect(cols: list[str]) -> DataQualityDefect:
    return DataQualityDefect(
        defect_type="null_values",
        category=DefectCategory.COMPLETENESS,
        severity=Severity.MEDIUM,
        affected_columns=cols,
        count=1,
        percentage=1.0,
        details="test defect",
        recommended_action="test action",
        remediation_class=RemediationClass.HUMAN_POLICY_AGENT_EXECUTION,
    )


def _report(df: pd.DataFrame, defects: list[DataQualityDefect]) -> DataQualityReport:
    return DataQualityReport(
        overall_severity=Severity.MEDIUM,
        has_critical_issues=False,
        defects=defects,
        column_profiles={},
        total_rows=len(df),
        total_columns=len(df.columns),
        overall_quality_score=0.5,
        assessed_at="2026-07-23T00:00:00Z",
    )


class TestRealNoEffectActionClassifiesCorrectly:
    """Drives the REAL `cleaning_policy._no_effect_action` code path (not a
    synthetic marker) end-to-end through `classify_outcome`, closing the gap
    where every other test either hand-builds the marker into a CleaningAction
    or never asserts on it at all — this is the regression test that would
    catch a future refactor of `_no_effect_action` silently dropping the
    marker it's supposed to set."""

    def test_all_null_column_imputation_attempt_classifies_as_no_effect(self) -> None:
        df = pd.DataFrame({"q": pd.Series([None, None, None], dtype=float)})
        _, actions = apply_imputation_policy(
            df, _report(df, [_null_defect(["q"])]), ImputationPolicyConfig(), "run-1"
        )
        assert len(actions) == 1
        assert actions[0].status == CleaningStatus.SKIPPED  # 3.4's own status, unchanged

        outcome = classify_outcome(actions[0])
        assert outcome == ManifestOutcome.NO_EFFECT

    def test_no_effect_action_uses_the_shared_constant_not_a_hardcoded_string(self) -> None:
        """cleaning_policy.py imports NO_EFFECT_HINT_KEY/VALUE from this module
        rather than hardcoding "manifest_outcome_hint"/"no_effect" — this pins
        that the two sides of the contract stay wired together."""
        from backend.models.healing_manifest import NO_EFFECT_HINT_KEY, NO_EFFECT_HINT_VALUE

        df = pd.DataFrame({"q": pd.Series([None, None, None], dtype=float)})
        _, actions = apply_imputation_policy(
            df, _report(df, [_null_defect(["q"])]), ImputationPolicyConfig(), "run-1"
        )
        assert actions[0].parameters.get(NO_EFFECT_HINT_KEY) == NO_EFFECT_HINT_VALUE
