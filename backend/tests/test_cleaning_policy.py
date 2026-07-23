"""Tests for the Tier-2 imputation policy layer + cleaning coordinator (Story 3.4).

Covers the load-bearing safety invariants (Tier-3/human_only never touched even
on a shared column, fail-closed allowlist, working-copy only across both tiers),
per-column-type default resolution and the full precedence chain, each imputation
method, the ``leave_as_is`` policy skip, out-of-scope Tier-2 skips, the
non-numeric FAILED path, coordinator tier-merging, and determinism/idempotency.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backend.models.cleaning_result import (
    CleaningOperation,
    CleaningStatus,
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
from backend.rules.cleaning_policy import (
    BUILTIN_DEFAULTS,
    apply_imputation_policy,
    column_kind,
    resolve_method,
)

RUN_ID = "test-run-3-4"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _defect(
    defect_type: str,
    remediation_class: RemediationClass,
    affected_columns: list[str],
    *,
    category: DefectCategory = DefectCategory.COMPLETENESS,
    severity: Severity = Severity.MEDIUM,
) -> DataQualityDefect:
    return DataQualityDefect(
        defect_type=defect_type,
        category=category,
        severity=severity,
        affected_columns=affected_columns,
        count=1,
        percentage=1.0,
        details="test defect",
        recommended_action="test action",
        remediation_class=remediation_class,
    )


def _null_defect(cols: list[str]) -> DataQualityDefect:
    return _defect("null_values", RemediationClass.HUMAN_POLICY_AGENT_EXECUTION, cols)


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


# --------------------------------------------------------------------------
# AC 3 — per-column-type default resolution + precedence
# --------------------------------------------------------------------------
class TestMethodResolution:
    def test_column_kind_detection(self) -> None:
        assert column_kind(pd.Series([1, 2, 3])) == "numeric"
        assert column_kind(pd.Series([1.0, np.nan])) == "numeric"
        assert column_kind(pd.Series(["a", "b"])) == "categorical"
        assert column_kind(pd.to_datetime(pd.Series(["2020-01-01", None]))) == "datetime"

    def test_builtin_defaults_by_type(self) -> None:
        empty = ImputationPolicyConfig()
        assert resolve_method("n", pd.Series([1.0, None]), empty) == ("median", "default")
        assert resolve_method("c", pd.Series(["a", None]), empty) == ("mode", "default")
        dt = pd.to_datetime(pd.Series(["2020-01-01", None]))
        assert resolve_method("d", dt, empty) == ("forward_fill", "default")
        # BUILTIN_DEFAULTS is the documented contract.
        assert BUILTIN_DEFAULTS == {
            "numeric": "median",
            "categorical": "mode",
            "datetime": "forward_fill",
        }

    def test_per_type_override_beats_builtin(self) -> None:
        policy = ImputationPolicyConfig(defaults={"numeric": "mean"})
        assert resolve_method("n", pd.Series([1.0, None]), policy) == ("mean", "override")

    def test_per_column_override_beats_everything(self) -> None:
        policy = ImputationPolicyConfig(
            defaults={"numeric": "mean"}, columns={"n": "leave_as_is"}
        )
        # per-column wins over per-type override and built-in.
        assert resolve_method("n", pd.Series([1.0, None]), policy) == (
            "leave_as_is",
            "override",
        )


# --------------------------------------------------------------------------
# AC 4 — Tier-2 execution drives the primitive; each method + source recorded
# --------------------------------------------------------------------------
class TestImputationExecution:
    def test_default_median_fills_numeric_nulls(self) -> None:
        df = pd.DataFrame({"q": [10.0, None, 30.0, None]})
        cleaned, actions = apply_imputation_policy(
            df, _report(df, [_null_defect(["q"])]), ImputationPolicyConfig(), RUN_ID
        )
        assert cleaned["q"].isna().sum() == 0
        assert cleaned["q"].tolist() == [10.0, 20.0, 30.0, 20.0]  # median of {10,30}=20
        assert len(actions) == 1
        act = actions[0]
        assert act.operation == CleaningOperation.NULL_IMPUTATION
        assert act.status == CleaningStatus.APPLIED
        assert act.remediation_class == RemediationClass.HUMAN_POLICY_AGENT_EXECUTION
        assert act.target_columns == ["q"]
        assert act.values_changed == 2
        assert act.parameters == {"method": "median", "source": "default"}

    def test_mean_override_and_source(self) -> None:
        df = pd.DataFrame({"q": [10.0, None, 40.0]})
        policy = ImputationPolicyConfig(columns={"q": "mean"})
        cleaned, actions = apply_imputation_policy(
            df, _report(df, [_null_defect(["q"])]), policy, RUN_ID
        )
        assert cleaned["q"].tolist() == [10.0, 25.0, 40.0]  # mean of {10,40}=25
        assert actions[0].parameters == {"method": "mean", "source": "override"}

    def test_mode_fills_categorical(self) -> None:
        df = pd.DataFrame({"c": ["a", "a", "b", None]})
        cleaned, actions = apply_imputation_policy(
            df, _report(df, [_null_defect(["c"])]), ImputationPolicyConfig(), RUN_ID
        )
        assert cleaned["c"].tolist() == ["a", "a", "b", "a"]
        assert actions[0].parameters["method"] == "mode"

    def test_forward_fill_datetime(self) -> None:
        df = pd.DataFrame({"d": pd.to_datetime(["2020-01-01", None, "2020-03-01", None])})
        cleaned, actions = apply_imputation_policy(
            df, _report(df, [_null_defect(["d"])]), ImputationPolicyConfig(), RUN_ID
        )
        assert cleaned["d"].isna().sum() == 0
        assert cleaned["d"].tolist() == pd.to_datetime(
            ["2020-01-01", "2020-01-01", "2020-03-01", "2020-03-01"]
        ).tolist()
        assert actions[0].parameters["method"] == "forward_fill"

    def test_leave_as_is_skips_without_calling_primitive(self) -> None:
        df = pd.DataFrame({"q": [1.0, None, 3.0]})
        policy = ImputationPolicyConfig(columns={"q": "leave_as_is"})
        cleaned, actions = apply_imputation_policy(
            df, _report(df, [_null_defect(["q"])]), policy, RUN_ID
        )
        assert cleaned["q"].isna().sum() == 1  # null preserved
        assert actions[0].status == CleaningStatus.SKIPPED
        assert actions[0].operation == CleaningOperation.NO_OP
        assert actions[0].values_changed == 0
        assert actions[0].parameters == {"method": "leave_as_is", "source": "override"}


# --------------------------------------------------------------------------
# AC 2 (Dev Notes) — mis-typed method surfaces as FAILED, never a crash
# --------------------------------------------------------------------------
class TestFailClosedOnBadMethod:
    def test_mean_on_non_numeric_records_failed_action(self) -> None:
        df = pd.DataFrame({"c": ["x", None, "y"]})
        policy = ImputationPolicyConfig(columns={"c": "mean"})
        cleaned, actions = apply_imputation_policy(
            df, _report(df, [_null_defect(["c"])]), policy, RUN_ID
        )
        assert actions[0].status == CleaningStatus.FAILED
        assert actions[0].error is not None
        assert "ValueError" in actions[0].error
        assert cleaned["c"].isna().sum() == 1  # unchanged; no crash

    def test_failed_error_carries_no_raw_cell_values(self) -> None:
        df = pd.DataFrame({"c": ["secretvalue", None]})
        policy = ImputationPolicyConfig(columns={"c": "median"})
        _cleaned, actions = apply_imputation_policy(
            df, _report(df, [_null_defect(["c"])]), policy, RUN_ID
        )
        assert actions[0].status == CleaningStatus.FAILED
        assert "secretvalue" not in (actions[0].error or "")


# --------------------------------------------------------------------------
# AC 5 — non-imputation Tier-2 and everything non-Tier-2 never acted on
# --------------------------------------------------------------------------
class TestFailClosedAllowlist:
    def test_non_unique_id_tier2_is_skipped_zero_change(self) -> None:
        df = pd.DataFrame({"id": [1.0, None, 3.0]})
        defect = _defect(
            "non_unique_id",
            RemediationClass.HUMAN_POLICY_AGENT_EXECUTION,
            ["id"],
            category=DefectCategory.UNIQUENESS,
        )
        cleaned, actions = apply_imputation_policy(
            df, _report(df, [defect]), ImputationPolicyConfig(), RUN_ID
        )
        assert len(actions) == 1
        assert actions[0].status == CleaningStatus.SKIPPED
        assert actions[0].defect_type == "non_unique_id"
        assert cleaned["id"].isna().sum() == 1  # untouched

    def test_tier3_and_tier1_findings_never_acted_on(self) -> None:
        df = pd.DataFrame({"q": [1.0, None, -5.0]})
        # A Tier-3 (human_only) null-shaped finding and a Tier-1 finding must be
        # invisible to the policy layer entirely (no action emitted for them).
        tier3 = _defect("negative_values", RemediationClass.HUMAN_ONLY, ["q"])
        tier1 = _defect("case_inconsistency", RemediationClass.AGENT_AUTONOMOUS, ["q"])
        cleaned, actions = apply_imputation_policy(
            df, _report(df, [tier3, tier1]), ImputationPolicyConfig(), RUN_ID
        )
        assert actions == []
        assert cleaned["q"].isna().sum() == 1


# --------------------------------------------------------------------------
# AC 6 — Tier-3 human_only NEVER touched, even on a shared column (LOAD-BEARING)
# AC 7 — working-copy only across the combined Tier-1 + Tier-2 pass
# AC 8 — coordinator merges both tiers; engine used unchanged
# --------------------------------------------------------------------------
class TestSharedColumnAndCoordinator:
    def _assessed(self, df: pd.DataFrame) -> DataQualityReport:
        return DataQualityAssessor().assess_quality(df, RUN_ID).quality_report

    def test_tier3_negative_survives_while_tier2_nulls_imputed(
        self, cleaning_dirty_df: pd.DataFrame
    ) -> None:
        report = self._assessed(cleaning_dirty_df)
        cleaned, result = clean_dataset(
            cleaning_dirty_df, report, ImputationPolicyConfig(), RUN_ID
        )
        # Tier-2: the quantity nulls are gone.
        assert cleaned["quantity"].isna().sum() == 0
        # Tier-3 (LOAD-BEARING): the -5 negative_values cell is byte-identical —
        # not fixed, not nulled, not dropped.
        assert (cleaned["quantity"] == -5.0).sum() == 1
        # No action anywhere references a human_only finding.
        assert all(
            a.remediation_class != RemediationClass.HUMAN_ONLY for a in result.actions
        )

    def test_combined_pass_never_mutates_caller_frame(
        self, cleaning_dirty_df: pd.DataFrame
    ) -> None:
        pristine = cleaning_dirty_df.copy(deep=True)
        report = self._assessed(cleaning_dirty_df)
        clean_dataset(cleaning_dirty_df, report, ImputationPolicyConfig(), RUN_ID)
        pd.testing.assert_frame_equal(cleaning_dirty_df, pristine)

    def test_apply_policy_alone_never_mutates_input(self) -> None:
        df = pd.DataFrame({"q": [1.0, None, 3.0]})
        pristine = df.copy(deep=True)
        cleaned, _ = apply_imputation_policy(
            df, _report(df, [_null_defect(["q"])]), ImputationPolicyConfig(), RUN_ID
        )
        pd.testing.assert_frame_equal(df, pristine)
        assert cleaned is not df  # always a fresh frame

    def test_coordinator_merges_both_tiers(
        self, cleaning_dirty_df: pd.DataFrame
    ) -> None:
        report = self._assessed(cleaning_dirty_df)
        _cleaned, result = clean_dataset(
            cleaning_dirty_df, report, ImputationPolicyConfig(), RUN_ID
        )
        classes = {a.remediation_class for a in result.actions}
        assert RemediationClass.AGENT_AUTONOMOUS in classes  # Tier-1 present
        assert RemediationClass.HUMAN_POLICY_AGENT_EXECUTION in classes  # Tier-2 present
        # Exactly one NULL_IMPUTATION action (quantity), from Tier-2.
        imputations = [
            a for a in result.actions if a.operation == CleaningOperation.NULL_IMPUTATION
        ]
        assert len(imputations) == 1

    def test_engine_output_is_a_prefix_of_merged_actions(
        self, cleaning_dirty_df: pd.DataFrame
    ) -> None:
        # The engine is composed, not modified: running it standalone yields the
        # same Tier-1 actions the coordinator carries.
        report = self._assessed(cleaning_dirty_df)
        _t1_df, t1_result = CleaningEngine().clean(cleaning_dirty_df, report, RUN_ID)
        _cleaned, merged = clean_dataset(
            cleaning_dirty_df, report, ImputationPolicyConfig(), RUN_ID
        )
        tier1_from_merged = [
            a
            for a in merged.actions
            if a.remediation_class == RemediationClass.AGENT_AUTONOMOUS
        ]
        assert [a.model_dump() for a in t1_result.actions] == [
            a.model_dump() for a in tier1_from_merged
        ]


# --------------------------------------------------------------------------
# AC 9 — deterministic & idempotent
# --------------------------------------------------------------------------
class TestDeterminismIdempotency:
    def test_double_run_identical(self, cleaning_dirty_df: pd.DataFrame) -> None:
        report = DataQualityAssessor().assess_quality(
            cleaning_dirty_df, RUN_ID
        ).quality_report
        df1, r1 = clean_dataset(cleaning_dirty_df, report, ImputationPolicyConfig(), RUN_ID)
        df2, r2 = clean_dataset(cleaning_dirty_df, report, ImputationPolicyConfig(), RUN_ID)
        pd.testing.assert_frame_equal(df1, df2)
        assert [a.model_dump() for a in r1.actions] == [a.model_dump() for a in r2.actions]

    def test_idempotent_reclean_after_reassess_yields_no_imputation(
        self, cleaning_dirty_df: pd.DataFrame
    ) -> None:
        report = DataQualityAssessor().assess_quality(
            cleaning_dirty_df, RUN_ID
        ).quality_report
        cleaned, _ = clean_dataset(
            cleaning_dirty_df, report, ImputationPolicyConfig(), RUN_ID
        )
        # Re-assess the cleaned frame: no null_values remain in quantity.
        report2 = DataQualityAssessor().assess_quality(cleaned, RUN_ID).quality_report
        _cleaned2, actions2 = apply_imputation_policy(
            cleaned, report2, ImputationPolicyConfig(), RUN_ID
        )
        assert all(
            a.operation != CleaningOperation.NULL_IMPUTATION
            or a.status != CleaningStatus.APPLIED
            for a in actions2
        )
