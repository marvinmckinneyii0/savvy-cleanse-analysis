"""Tests for the deterministic Cleaning Engine (Story 3.2).

Covers the load-bearing safety invariants (working-copy only, Tier-1-only
fail-closed dispatch, human-owned findings never touched), each Tier-1
operation's deterministic rule, the policy-less imputation boundary, action-
record provenance, determinism/idempotency, and an assess→clean→re-assess
integration pass.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backend.errors.exceptions import CleaningEngineError
from backend.models.cleaning_result import (
    CleaningOperation,
    CleaningResult,
    CleaningStatus,
)
from backend.models.quality_report import (
    DataQualityDefect,
    DataQualityReport,
    DefectCategory,
    RemediationClass,
    Severity,
)
from backend.pipeline import cleaning_primitives as prim
from backend.pipeline.cleaning_engine import CleaningEngine
from backend.pipeline.data_quality import DataQualityAssessor

RUN_ID = "test-run-3-2"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _defect(
    defect_type: str,
    remediation_class: RemediationClass,
    affected_columns: list[str],
    *,
    category: DefectCategory = DefectCategory.STRUCTURAL_INTEGRITY,
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


def _report(df: pd.DataFrame, defects: list[DataQualityDefect]) -> DataQualityReport:
    return DataQualityReport(
        overall_severity=Severity.MEDIUM,
        has_critical_issues=False,
        defects=defects,
        column_profiles={},
        total_rows=len(df),
        total_columns=len(df.columns),
        overall_quality_score=0.5,
        assessed_at="2026-07-20T00:00:00Z",
    )


def _autonomous(defect_type: str, cols: list[str]) -> DataQualityDefect:
    return _defect(defect_type, RemediationClass.AGENT_AUTONOMOUS, cols)


# --------------------------------------------------------------------------
# AC 1 — working-copy invariant
# --------------------------------------------------------------------------
class TestWorkingCopyInvariant:
    def test_original_frame_never_mutated(self, cleaning_dirty_df: pd.DataFrame) -> None:
        pristine = cleaning_dirty_df.copy(deep=True)
        report = DataQualityAssessor().assess_quality(cleaning_dirty_df, RUN_ID).quality_report

        CleaningEngine().clean(cleaning_dirty_df, report, RUN_ID)

        pd.testing.assert_frame_equal(cleaning_dirty_df, pristine)

    def test_returns_a_distinct_object(self, cleaning_dirty_df: pd.DataFrame) -> None:
        report = DataQualityAssessor().assess_quality(cleaning_dirty_df, RUN_ID).quality_report
        cleaned, result = CleaningEngine().clean(cleaning_dirty_df, report, RUN_ID)
        assert cleaned is not cleaning_dirty_df
        assert isinstance(result, CleaningResult)

    def test_no_op_report_returns_deep_copy(self, clean_sales_df: pd.DataFrame) -> None:
        report = _report(clean_sales_df, [])
        cleaned, result = CleaningEngine().clean(clean_sales_df, report, RUN_ID)
        assert result.actions == []
        assert cleaned is not clean_sales_df
        pd.testing.assert_frame_equal(cleaned, clean_sales_df)


# --------------------------------------------------------------------------
# AC 2 — Tier-1-only, fail-closed dispatch
# --------------------------------------------------------------------------
class TestFailClosedDispatch:
    def test_tier2_and_tier3_findings_produce_no_change(self) -> None:
        df = pd.DataFrame({"quantity": [1.0, None, -5.0, 4.0]})
        defects = [
            _defect("null_values", RemediationClass.HUMAN_POLICY_AGENT_EXECUTION, ["quantity"]),
            _defect("negative_values", RemediationClass.HUMAN_ONLY, ["quantity"]),
        ]
        cleaned, result = CleaningEngine().clean(df, _report(df, defects), RUN_ID)
        assert result.actions == []
        pd.testing.assert_frame_equal(cleaned, df)

    def test_unknown_defect_type_defaults_human_only_and_is_ignored(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 2]})
        # Default remediation_class is HUMAN_ONLY (fail-safe) — filtered out.
        d = DataQualityDefect(
            defect_type="some_future_defect",
            category=DefectCategory.STRUCTURAL_INTEGRITY,
            severity=Severity.LOW,
            affected_columns=["a"],
            count=1,
            percentage=1.0,
            details="x",
            recommended_action="y",
        )
        assert d.remediation_class == RemediationClass.HUMAN_ONLY
        cleaned, result = CleaningEngine().clean(df, _report(df, [d]), RUN_ID)
        assert result.actions == []
        pd.testing.assert_frame_equal(cleaned, df)

    def test_autonomous_but_unregistered_type_fails_closed_with_skip_record(self) -> None:
        df = pd.DataFrame({"quantity": [1.0, None, None]})
        # A mis-stamped finding: autonomous class on a type the engine can't handle.
        d = _autonomous("null_values", ["quantity"])
        cleaned, result = CleaningEngine().clean(df, _report(df, [d]), RUN_ID)
        # Fail-closed: data unchanged, and a visible SKIPPED / NO_OP record emitted.
        pd.testing.assert_frame_equal(cleaned, df)
        assert len(result.actions) == 1
        assert result.actions[0].status == CleaningStatus.SKIPPED
        assert result.actions[0].operation == CleaningOperation.NO_OP
        assert not any(a.operation == CleaningOperation.NULL_IMPUTATION for a in result.actions)

    def test_private_dispatch_rejects_non_autonomous_finding(self) -> None:
        df = pd.DataFrame({"a": ["x", "y"]})
        d = _defect("case_inconsistency", RemediationClass.HUMAN_ONLY, ["a"])
        with pytest.raises(CleaningEngineError, match="non-autonomous"):
            CleaningEngine()._apply_operation(
                d, CleaningOperation.CASE_NORMALIZATION, df, _stub_log()
            )

    def test_private_header_dispatch_rejects_non_autonomous_finding(self) -> None:
        df = pd.DataFrame({"bad$": [1, 2]})
        d = _defect("column_naming", RemediationClass.HUMAN_POLICY_AGENT_EXECUTION, ["bad$"])
        with pytest.raises(CleaningEngineError, match="non-autonomous"):
            CleaningEngine()._normalize_headers([d], df, _stub_log())

    def test_mixed_list_processes_only_autonomous_findings(self) -> None:
        df = pd.DataFrame(
            {"region": ["a", "A", "a"], "quantity": [1.0, None, -5.0]}
        )
        defects = [
            _autonomous("case_inconsistency", ["region"]),  # Tier 1 -> act
            _defect("null_values", RemediationClass.HUMAN_POLICY_AGENT_EXECUTION, ["quantity"]),
            _defect("negative_values", RemediationClass.HUMAN_ONLY, ["quantity"]),
        ]
        cleaned, result = CleaningEngine().clean(df, _report(df, defects), RUN_ID)
        applied = [a for a in result.actions if a.status == CleaningStatus.APPLIED]
        assert len(applied) == 1
        assert applied[0].operation == CleaningOperation.CASE_NORMALIZATION
        # quantity (Tier-2/3) untouched: null still null, negative still negative.
        assert cleaned["quantity"].isna().sum() == 1
        assert (cleaned["quantity"] == -5.0).sum() == 1


# --------------------------------------------------------------------------
# AC 3 — Tier-1 operation specs
# --------------------------------------------------------------------------
class TestDeduplication:
    def test_removes_exact_duplicates_keep_first_preserve_order(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 2, 3], "b": ["x", "y", "y", "z"]})
        d = _autonomous("duplicate_rows", ["a", "b"])
        cleaned, result = CleaningEngine().clean(df, _report(df, [d]), RUN_ID)
        assert list(cleaned["a"]) == [1, 2, 3]
        action = result.actions[0]
        assert action.operation == CleaningOperation.DEDUPLICATION
        assert action.rows_affected == 1
        assert action.before_state == "4 rows" and action.after_state == "3 rows"


class TestCaseNormalization:
    def test_collapses_to_most_frequent_variant(self) -> None:
        # "north" appears 3x, "North" 1x -> canonical "north".
        df = pd.DataFrame({"region": ["north", "North", "north", "north"]})
        d = _autonomous("case_inconsistency", ["region"])
        cleaned, result = CleaningEngine().clean(df, _report(df, [d]), RUN_ID)
        assert list(cleaned["region"]) == ["north", "north", "north", "north"]
        assert result.actions[0].value_mapping == {"North": "north"}
        assert result.actions[0].values_changed == 1

    def test_tie_breaks_to_lexicographically_smallest(self) -> None:
        # "North" 1x, "north" 1x -> tie -> lexicographically smallest "North".
        df = pd.DataFrame({"region": ["North", "north"]})
        d = _autonomous("case_inconsistency", ["region"])
        cleaned, _ = CleaningEngine().clean(df, _report(df, [d]), RUN_ID)
        assert list(cleaned["region"]) == ["North", "North"]

    def test_non_string_cells_untouched(self) -> None:
        series = pd.Series(["a", "A", 5, None], dtype=object)
        out, meta = prim.normalize_case(series)
        assert out.iloc[2] == 5
        assert pd.isna(out.iloc[3])


class TestTypeCoercion:
    def test_coerces_numeric_strings_to_numbers(self) -> None:
        df = pd.DataFrame({"code": [1, 2, "3", 4, "5"]})
        d = _autonomous("mixed_types", ["code"])
        cleaned, result = CleaningEngine().clean(df, _report(df, [d]), RUN_ID)
        assert list(pd.to_numeric(cleaned["code"])) == [1, 2, 3, 4, 5]
        assert result.actions[0].parameters["uncoerced"] == "0"

    def test_uncoercible_value_preserved_not_nulled(self) -> None:
        df = pd.DataFrame({"code": [1, 2, "oops", 4, 5]})
        d = _autonomous("mixed_types", ["code"])
        cleaned, result = CleaningEngine().clean(df, _report(df, [d]), RUN_ID)
        # The uncoercible string is kept, NOT replaced with null.
        assert "oops" in list(cleaned["code"])
        assert cleaned["code"].isna().sum() == 0
        assert result.actions[0].parameters["uncoerced"] == "1"

    def test_whitespace_stripped_during_coercion(self) -> None:
        out, meta = prim.coerce_column_type(pd.Series([" 1 ", "2", " 3"]))
        assert list(pd.to_numeric(out)) == [1, 2, 3]

    def test_datetime_standardized_to_iso(self) -> None:
        # Dominant type datetime (2 timestamps) + 1 string -> ISO date strings.
        series = pd.Series(
            [pd.Timestamp("2026-01-05"), pd.Timestamp("2026-01-06"), "2026-01-07"],
            dtype=object,
        )
        out, meta = prim.coerce_column_type(series)
        assert meta["kind"] == "datetime"
        assert list(out) == ["2026-01-05", "2026-01-06", "2026-01-07"]

    def test_never_introduces_new_null(self) -> None:
        df = pd.DataFrame({"code": [1, "x", 3, "y", 5]})
        d = _autonomous("mixed_types", ["code"])
        cleaned, _ = CleaningEngine().clean(df, _report(df, [d]), RUN_ID)
        assert cleaned["code"].isna().sum() == 0

    def test_dominant_type_tie_break_is_deterministic(self) -> None:
        # Exact 3-vs-3 split between int and numeric-string: value_counts()'s
        # tie-break can depend on hash/iteration order; ours must not.
        series = pd.Series([1, 2, 3, "4", "5", "6"], dtype=object)
        results = {prim.dominant_python_type(series) for _ in range(20)}
        assert len(results) == 1  # same winner every call, no flapping

    def test_dominant_type_tie_break_matches_qualname_order(self) -> None:
        # int vs str tie: sorted by (module, qualname) -> ('builtins', 'int')
        # sorts before ('builtins', 'str').
        series = pd.Series([1, 2, "a", "b"], dtype=object)
        assert prim.dominant_python_type(series) is int


class TestHeaderNormalization:
    def test_normalizes_special_and_numeric_names(self) -> None:
        cols, mapping = prim.normalize_column_names(["Unit Price ($)", "2024", "  ok_col  "])
        assert cols == ["unit_price", "column_1", "ok_col"]
        assert mapping["2024"] == "column_1"

    def test_collision_suffixing_is_deterministic(self) -> None:
        cols, _ = prim.normalize_column_names(["A", "a", "a!"])
        assert cols == ["a", "a_2", "a_3"]

    def test_targets_none_renames_every_column(self) -> None:
        cols, mapping = prim.normalize_column_names(["Bad Name", "2024"])
        assert cols == ["bad_name", "column_1"]
        assert mapping == {"Bad Name": "bad_name", "2024": "column_1"}

    def test_targets_scopes_rename_to_only_named_columns(self) -> None:
        cols, mapping = prim.normalize_column_names(
            ["amount#", "Region", "2024"], targets={"amount#"}
        )
        # Only "amount#" renamed; "Region" and "2024" pass through untouched
        # even though "2024" would itself be re-slugged under targets=None.
        assert cols == ["amount", "Region", "2024"]
        assert mapping == {"amount#": "amount"}

    def test_engine_renames_flagged_headers_in_one_action(self) -> None:
        df = pd.DataFrame({"amount#": [1.0, 2.0], "clean": [3, 4]})
        d = _autonomous("column_naming", ["amount#"])
        cleaned, result = CleaningEngine().clean(df, _report(df, [d]), RUN_ID)
        assert list(cleaned.columns) == ["amount", "clean"]
        header_actions = [
            a for a in result.actions
            if a.operation == CleaningOperation.HEADER_NORMALIZATION
        ]
        assert len(header_actions) == 1
        assert header_actions[0].value_mapping == {"amount#": "amount"}

    def test_header_normalization_does_not_touch_unflagged_columns(self) -> None:
        # "Region" would itself be re-slugged (lowercased) by a blanket rename,
        # but it carries no column_naming finding — only "amount#" does. Only
        # the flagged column may change; "Region" must survive byte-identical.
        df = pd.DataFrame({"amount#": [1.0], "Region": ["north"]})
        d = _autonomous("column_naming", ["amount#"])
        cleaned, result = CleaningEngine().clean(df, _report(df, [d]), RUN_ID)
        assert list(cleaned.columns) == ["amount", "Region"]
        header_actions = [
            a for a in result.actions
            if a.operation == CleaningOperation.HEADER_NORMALIZATION
        ]
        assert header_actions[0].value_mapping == {"amount#": "amount"}
        assert "Region" not in header_actions[0].value_mapping

    def test_header_normalization_renamed_column_avoids_untouched_collision(self) -> None:
        # "amount#" slugifies to "amount", which already exists untouched.
        # Collision detection must still fire even though "amount" itself has
        # no finding and is never renamed.
        df = pd.DataFrame({"amount#": [1.0], "amount": [2.0]})
        d = _autonomous("column_naming", ["amount#"])
        cleaned, _ = CleaningEngine().clean(df, _report(df, [d]), RUN_ID)
        assert list(cleaned.columns) == ["amount_2", "amount"]

    def test_header_normalization_failure_degrades_to_failed_action(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        df = pd.DataFrame({"amount#": [1.0]})
        d = _autonomous("column_naming", ["amount#"])

        def _boom(_columns, targets=None):
            raise RuntimeError("header primitive exploded")

        monkeypatch.setattr(prim, "normalize_column_names", _boom)
        cleaned, result = CleaningEngine().clean(df, _report(df, [d]), RUN_ID)
        # clean() must not raise — the failure degrades to a FAILED action.
        pd.testing.assert_frame_equal(cleaned, df)
        failed = [a for a in result.actions if a.status == CleaningStatus.FAILED]
        assert len(failed) == 1
        assert failed[0].scope.value == "table"
        assert "RuntimeError" in failed[0].error


# --------------------------------------------------------------------------
# AC 4 — imputation boundary (policy-less primitive)
# --------------------------------------------------------------------------
class TestImputationPrimitive:
    def test_mean_median_mode_forward_fill(self) -> None:
        df = pd.DataFrame({"x": [1.0, None, 3.0, None, 3.0]})
        assert prim.impute_nulls(df, "x", "mean")["x"].isna().sum() == 0
        assert prim.impute_nulls(df, "x", "median")["x"].tolist()[1] == pytest.approx(3.0)
        assert prim.impute_nulls(df, "x", "mode")["x"].tolist()[1] == pytest.approx(3.0)
        ff = prim.impute_nulls(df, "x", "forward_fill")["x"].tolist()
        assert ff == [1.0, 1.0, 3.0, 3.0, 3.0]

    def test_method_argument_is_mandatory(self) -> None:
        df = pd.DataFrame({"x": [1.0, None]})
        with pytest.raises(TypeError):
            prim.impute_nulls(df, "x")  # type: ignore[call-arg]

    def test_unknown_method_raises(self) -> None:
        df = pd.DataFrame({"x": [1.0, None]})
        with pytest.raises(ValueError, match="unknown imputation method"):
            prim.impute_nulls(df, "x", "magic")

    def test_mean_median_reject_non_numeric_column(self) -> None:
        df = pd.DataFrame({"x": ["a", None, "c"]})
        with pytest.raises(ValueError, match="requires a numeric column"):
            prim.impute_nulls(df, "x", "mean")
        with pytest.raises(ValueError, match="requires a numeric column"):
            prim.impute_nulls(df, "x", "median")

    def test_mode_and_forward_fill_accept_non_numeric_column(self) -> None:
        df = pd.DataFrame({"x": ["a", None, "a"]})
        assert prim.impute_nulls(df, "x", "mode")["x"].tolist() == ["a", "a", "a"]
        assert prim.impute_nulls(df, "x", "forward_fill")["x"].tolist() == ["a", "a", "a"]

    def test_impute_does_not_mutate_input(self) -> None:
        df = pd.DataFrame({"x": [1.0, None, 3.0]})
        pristine = df.copy(deep=True)
        prim.impute_nulls(df, "x", "mean")
        pd.testing.assert_frame_equal(df, pristine)

    def test_autonomous_path_never_imputes(self) -> None:
        # Even a null_values finding mis-stamped autonomous yields no imputation.
        df = pd.DataFrame({"quantity": [1.0, None, None, 4.0]})
        d = _autonomous("null_values", ["quantity"])
        cleaned, result = CleaningEngine().clean(df, _report(df, [d]), RUN_ID)
        assert cleaned["quantity"].isna().sum() == 2  # nulls preserved
        assert not any(
            a.operation == CleaningOperation.NULL_IMPUTATION for a in result.actions
        )


# --------------------------------------------------------------------------
# AC 5 — action record provenance
# --------------------------------------------------------------------------
class TestActionRecord:
    def test_result_shape_fields_populated(self, cleaning_dirty_df: pd.DataFrame) -> None:
        report = DataQualityAssessor().assess_quality(cleaning_dirty_df, RUN_ID).quality_report
        _, result = CleaningEngine().clean(cleaning_dirty_df, report, RUN_ID)
        assert result.pipeline_run_id == RUN_ID
        assert result.rows_before == 12
        assert result.rows_after == 11  # one duplicate removed
        assert result.columns_before == result.columns_after == 4
        assert result.total_findings == 6
        assert result.autonomous_findings == 4

    def test_every_applied_action_is_traceable(self, cleaning_dirty_df: pd.DataFrame) -> None:
        report = DataQualityAssessor().assess_quality(cleaning_dirty_df, RUN_ID).quality_report
        _, result = CleaningEngine().clean(cleaning_dirty_df, report, RUN_ID)
        applied = [a for a in result.actions if a.status == CleaningStatus.APPLIED]
        # One per Tier-1 finding: dedup, case, coercion, header.
        ops = {a.operation for a in applied}
        assert ops == {
            CleaningOperation.DEDUPLICATION,
            CleaningOperation.CASE_NORMALIZATION,
            CleaningOperation.TYPE_COERCION,
            CleaningOperation.HEADER_NORMALIZATION,
        }
        for a in applied:
            assert a.remediation_class == RemediationClass.AGENT_AUTONOMOUS
            assert a.rule  # deterministic rule always stated
            assert a.detail

    def test_failed_action_carries_safe_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        df = pd.DataFrame({"region": ["a", "A"]})
        d = _autonomous("case_inconsistency", ["region"])

        def _boom(_series: pd.Series):
            raise RuntimeError("primitive exploded")

        monkeypatch.setattr(prim, "normalize_case", _boom)
        cleaned, result = CleaningEngine().clean(df, _report(df, [d]), RUN_ID)
        # Original preserved; failure captured as a FAILED action with safe info.
        pd.testing.assert_frame_equal(cleaned, df)
        failed = [a for a in result.actions if a.status == CleaningStatus.FAILED]
        assert len(failed) == 1
        assert failed[0].error is not None and "RuntimeError" in failed[0].error
        assert failed[0].scope.value == "column"  # case normalization is column-scoped

    def test_failed_action_scope_matches_the_failed_operation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        df = pd.DataFrame({"a": [1, 1]})
        d = _autonomous("duplicate_rows", ["a"])

        def _boom(_df: pd.DataFrame):
            raise RuntimeError("dedup primitive exploded")

        monkeypatch.setattr(prim, "drop_exact_duplicates", _boom)
        cleaned, result = CleaningEngine().clean(df, _report(df, [d]), RUN_ID)
        pd.testing.assert_frame_equal(cleaned, df)
        failed = [a for a in result.actions if a.status == CleaningStatus.FAILED]
        assert len(failed) == 1
        assert failed[0].scope.value == "row"  # NOT the old hardcoded "column"

    def test_failed_action_error_message_is_truncated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        df = pd.DataFrame({"region": ["a", "A"]})
        d = _autonomous("case_inconsistency", ["region"])
        long_message = "x" * 5000

        def _boom(_series: pd.Series):
            raise RuntimeError(long_message)

        monkeypatch.setattr(prim, "normalize_case", _boom)
        _, result = CleaningEngine().clean(df, _report(df, [d]), RUN_ID)
        failed = [a for a in result.actions if a.status == CleaningStatus.FAILED]
        assert len(failed) == 1
        assert failed[0].error is not None
        assert len(failed[0].error) < 300


# --------------------------------------------------------------------------
# AC 6 — determinism & idempotency
# --------------------------------------------------------------------------
class TestDeterminismIdempotency:
    def test_two_runs_identical(self, cleaning_dirty_df: pd.DataFrame) -> None:
        report = DataQualityAssessor().assess_quality(cleaning_dirty_df, RUN_ID).quality_report
        c1, r1 = CleaningEngine().clean(cleaning_dirty_df, report, RUN_ID)
        c2, r2 = CleaningEngine().clean(cleaning_dirty_df, report, RUN_ID)
        pd.testing.assert_frame_equal(c1, c2)
        assert r1.model_dump(exclude={"cleaned_at"}) == r2.model_dump(exclude={"cleaned_at"})

    def test_recleaning_output_makes_no_tier1_changes(
        self, cleaning_dirty_df: pd.DataFrame
    ) -> None:
        report = DataQualityAssessor().assess_quality(cleaning_dirty_df, RUN_ID).quality_report
        cleaned, _ = CleaningEngine().clean(cleaning_dirty_df, report, RUN_ID)
        # Re-assess the cleaned frame and clean again — no Tier-1 defects remain,
        # so no autonomous actions and the frame is unchanged.
        report2 = DataQualityAssessor().assess_quality(cleaned, RUN_ID).quality_report
        recleaned, result2 = CleaningEngine().clean(cleaned, report2, RUN_ID)
        applied2 = [a for a in result2.actions if a.status == CleaningStatus.APPLIED]
        assert applied2 == []
        pd.testing.assert_frame_equal(recleaned, cleaned)


# --------------------------------------------------------------------------
# AC 8 — integration: assess -> clean -> re-assess
# --------------------------------------------------------------------------
class TestIntegration:
    def test_tier1_gone_tier2_tier3_preserved(self, cleaning_dirty_df: pd.DataFrame) -> None:
        assessor = DataQualityAssessor()
        report = assessor.assess_quality(cleaning_dirty_df, RUN_ID).quality_report
        cleaned, _ = CleaningEngine().clean(cleaning_dirty_df, report, RUN_ID)

        re_report = assessor.assess_quality(cleaned, RUN_ID).quality_report
        types_after = {d.defect_type for d in re_report.defects}

        # Every Tier-1 defect type is gone.
        assert "mixed_types" not in types_after
        assert "case_inconsistency" not in types_after
        assert "duplicate_rows" not in types_after
        assert "column_naming" not in types_after

        # Human-owned findings survive: nulls and the negative value untouched.
        assert "null_values" in types_after
        assert "negative_values" in types_after
        assert cleaned["quantity"].isna().sum() == 2
        assert (cleaned["quantity"] == -5.0).sum() == 1


# --------------------------------------------------------------------------
# small helper
# --------------------------------------------------------------------------
def _stub_log():
    import structlog

    return structlog.get_logger().bind(pipeline_run_id=RUN_ID)
