"""Story 3.5: the consolidated Tier-3 (human_only) boundary-proof test.

Exercises the ENTIRE Epic 3 pipeline in one pass — DQA assessment,
classification, Tier-1 CleaningEngine, Tier-2 policy, the coordinator's
runtime guard, the Healing Manifest, and the cleaned-CSV export — against a
fixture engineered to carry at least one instance of EVERY currently
registered `human_only` `defect_type`, proving none was ever touched
anywhere in the chain. Not scattered across 3.2/3.4/3.3's individual test
files as it is today: one first-class, explicitly-named guarantee.

Also directly unit-tests `cleaning_coordinator._verify_tier3_never_touched`,
the runtime guard itself, proving it actually fires on a violation.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from backend.errors.exceptions import CleaningEngineError
from backend.models.cleaning_result import (
    CleaningAction,
    CleaningOperation,
    CleaningResult,
    CleaningScope,
    CleaningStatus,
)
from backend.models.insight_report import InsightReport, NarrativeSection
from backend.models.pipeline_config import ImputationPolicyConfig
from backend.models.quality_report import RemediationClass
from backend.pipeline.data_quality import DataQualityAssessor
from backend.pipeline.orchestrator import run_full_pipeline
from backend.pipeline.remediation_classifier import _DEFECT_TYPE_TO_CLASS
from backend.rules.cleaning_coordinator import _verify_tier3_never_touched, clean_dataset

_NARRATIVE_TARGET = "backend.pipeline.orchestrator.NarrativeGenerator.generate"

# The complete, currently-registered human_only defect_type set. Task 3's
# meta-test (below) proves this constant stays in sync with the classifier —
# if a future defect_type is added to remediation_classifier.py without
# updating this list, the meta-test fails loudly rather than silently
# under-testing the fixture.
_EXPECTED_HUMAN_ONLY_TYPES = frozenset(
    {
        "zero_variance",
        "extreme_outliers",
        "extreme_cardinality",
        "negative_values",
        "infinite_values",
        "duplicate_measurement",
    }
)


def test_expected_human_only_types_match_the_classifier_table():
    """Meta-test: if remediation_classifier.py's HUMAN_ONLY set ever changes,
    this fails loudly so the fixture below gets updated to match, instead of
    the boundary-proof test silently drifting out of full coverage."""
    actual = {
        defect_type
        for defect_type, cls in _DEFECT_TYPE_TO_CLASS.items()
        if cls == RemediationClass.HUMAN_ONLY
    }
    assert actual == _EXPECTED_HUMAN_ONLY_TYPES


@pytest.fixture()
def all_tier3_types_df() -> pd.DataFrame:
    """40-row frame triggering all six currently-registered human_only
    defect_types simultaneously, plus one Tier-1 and one Tier-2 finding so
    the boundary proof runs alongside real cleaning activity, not in a
    vacuum.

    outlier_col needs a large row count: a single extreme value among n
    otherwise-identical points can only exceed the detector's 5-std-dev
    threshold once n is large enough (the deviation/std ratio approaches
    sqrt(n-1) as the outlier grows, so n=12 can never trigger it regardless
    of magnitude — verified empirically while building this fixture).

    record_ref uses numeric-looking strings, not free text: the
    extreme_cardinality detector shares a numeric-coercibility guard with the
    other statistical checks in the same loop, so a purely non-numeric string
    column is currently skipped before that check ever runs (a pre-existing
    DQA bug, out of this story's scope — flagged separately). Numeric strings
    satisfy both "is a string/object column" and "has coercible content".
    """
    n = 40
    return pd.DataFrame(
        {
            # Tier 1 (agent_autonomous): case variants -> case_inconsistency.
            "region": ["north", "North", "NORTH"] + ["south"] * (n - 3),
            # Tier 2 (human_policy_agent_execution): nulls -> null_values.
            "value": [10.0, None] + [float(30 + 10 * i) for i in range(n - 2)],
            # Tier 3: zero_variance -- every value identical.
            "constant_col": [5.0] * n,
            # Tier 3: extreme_outliers -- one value far beyond 5 std devs.
            "outlier_col": [10.0] * (n - 1) + [1e6],
            # Tier 3: infinite_values.
            "inf_col": [1.0, 2.0, 3.0, np.inf] + [float(i) for i in range(n - 4)],
            # Tier 3: extreme_cardinality -- every value unique (numeric-string,
            # see docstring note on the detector's numeric-coercibility guard).
            "record_ref": [str(9000 + i) for i in range(n)],
            # Tier 3: negative_values -- column name implies non-negativity.
            "quantity": [float(10 * i + 10) for i in range(n - 1)] + [-5.0],
            # Tier 3: duplicate_measurement -- near-perfectly correlated with quantity.
            "quantity_copy": [
                float(10 * i + 10) + 0.1 for i in range(n - 1)
            ]
            + [-4.9],
        }
    )


@pytest.fixture()
def canned_insight_report() -> InsightReport:
    return InsightReport(
        executive_summary="Offline canned narrative.",
        key_findings=[NarrativeSection(title="t", content="c")],
        anomaly_analysis=None,
        recommendations_narrative="None.",
        metadata={"provider": "mock", "timestamp": "2026-08-17T00:00:00Z"},
        fallback=False,
    )


class TestConsolidatedTier3BoundaryProof:
    """AC2: one place proving the boundary across the WHOLE Epic 3 chain."""

    def test_full_pipeline_never_touches_any_tier3_finding(
        self,
        all_tier3_types_df: pd.DataFrame,
        canned_insight_report: InsightReport,
        tmp_path: Path,
    ) -> None:
        csv_path = tmp_path / "input.csv"
        all_tier3_types_df.to_csv(csv_path, index=False)
        report_out = tmp_path / "report.docx"
        cleaned_out = tmp_path / "cleaned.csv"

        with patch(_NARRATIVE_TARGET, return_value=canned_insight_report):
            result = run_full_pipeline(
                input_path=csv_path,
                output_path=report_out,
                enable_cleaning=True,
                cleaned_output_path=cleaned_out,
            )

        assert result.success is True
        assert result.cleaning_result is not None

        # (a) No CleaningAction ever carries a human_only remediation_class.
        assert all(
            a.remediation_class != RemediationClass.HUMAN_ONLY
            for a in result.cleaning_result.actions
        )

        # (b) No ManifestEntry ever carries a human_only remediation_class.
        manifest = result.insight_report.healing_manifest
        assert manifest is not None
        assert all(
            e.remediation_class != RemediationClass.HUMAN_ONLY for e in manifest.entries
        )

        # (c) Every Tier-3-flagged column is byte-identical, original vs
        # exported cleaned CSV -- not fixed, not nulled, not dropped. Compare
        # against the ORIGINAL CSV re-read the same way (not the in-memory
        # DataFrame), so a CSV round-trip dtype inference quirk (e.g. numeric-
        # looking strings becoming ints) isn't mistaken for a data change.
        original_reread = pd.read_csv(csv_path)
        exported = pd.read_csv(cleaned_out)
        for col in ("constant_col", "outlier_col", "inf_col", "record_ref"):
            assert exported[col].tolist() == original_reread[col].tolist(), col
        assert exported["quantity"].tolist() == original_reread["quantity"].tolist()
        assert (
            exported["quantity_copy"].tolist() == original_reread["quantity_copy"].tolist()
        )

        # Sanity: real cleaning activity actually happened alongside the
        # Tier-3 findings (Tier-1 case normalization, Tier-2 imputation),
        # proving this isn't a vacuous "nothing ran" pass.
        assert any(
            a.operation == CleaningOperation.CASE_NORMALIZATION
            and a.status == CleaningStatus.APPLIED
            for a in result.cleaning_result.actions
        )
        assert any(
            a.operation == CleaningOperation.NULL_IMPUTATION
            and a.status == CleaningStatus.APPLIED
            for a in result.cleaning_result.actions
        )

    def test_all_six_tier3_types_are_actually_present_in_the_fixture(
        self, all_tier3_types_df: pd.DataFrame
    ) -> None:
        """Guards the guard: if the fixture stops actually triggering one of
        the six detector types (e.g. a future DQA threshold change), this
        fails instead of the boundary-proof test silently passing on a
        narrower set than intended."""
        report = DataQualityAssessor().assess_quality(
            all_tier3_types_df, "run-tier3-boundary"
        ).quality_report
        present_types = {d.defect_type for d in report.defects}
        missing = _EXPECTED_HUMAN_ONLY_TYPES - present_types
        assert not missing, f"Fixture no longer triggers: {missing}"


class TestRuntimeGuardFires:
    """AC1: the coordinator-level guard is not dead code -- it actually raises."""

    def _human_only_action(self) -> CleaningAction:
        return CleaningAction(
            operation=CleaningOperation.NULL_IMPUTATION,
            defect_type="negative_values",
            remediation_class=RemediationClass.HUMAN_ONLY,
            status=CleaningStatus.APPLIED,
            scope=CleaningScope.COLUMN,
            target_columns=["quantity"],
            values_changed=1,
        )

    def test_verify_tier3_never_touched_raises_on_violation(self) -> None:
        result = CleaningResult(
            pipeline_run_id="run-1",
            total_findings=1,
            autonomous_findings=0,
            actions=[self._human_only_action()],
            rows_before=1,
            rows_after=1,
            columns_before=1,
            columns_after=1,
            cleaned_at="2026-01-01T00:00:00+00:00",
        )
        with pytest.raises(CleaningEngineError, match="Tier-3 boundary violation"):
            _verify_tier3_never_touched(result)

    def test_verify_tier3_never_touched_passes_clean_result(self) -> None:
        action = self._human_only_action()
        action = action.model_copy(update={"remediation_class": RemediationClass.AGENT_AUTONOMOUS})
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
        _verify_tier3_never_touched(result)  # must not raise

    def test_guard_is_wired_into_the_real_coordinator_call_path(self) -> None:
        """Proves the guard isn't just a standalone function that happens to
        exist -- clean_dataset() itself raises when the merged result would
        contain a human_only action."""
        df = pd.DataFrame({"quantity": [10.0, 20.0, -5.0]})
        report = DataQualityAssessor().assess_quality(df, "run-guard-wiring").quality_report

        with patch(
            "backend.rules.cleaning_coordinator.CleaningEngine.clean",
            return_value=(
                df.copy(),
                CleaningResult(
                    pipeline_run_id="run-guard-wiring",
                    total_findings=1,
                    autonomous_findings=0,
                    actions=[self._human_only_action()],
                    rows_before=3,
                    rows_after=3,
                    columns_before=1,
                    columns_after=1,
                    cleaned_at="2026-01-01T00:00:00+00:00",
                ),
            ),
        ):
            with pytest.raises(CleaningEngineError, match="Tier-3 boundary violation"):
                clean_dataset(df, report, ImputationPolicyConfig(), "run-guard-wiring")

    def test_guard_violation_propagates_unhandled_through_run_full_pipeline(
        self, tmp_path: Path
    ) -> None:
        """Closes a real gap flagged by review: the guard was only proven to
        fire via clean_dataset() directly, never through the orchestrator's
        own call site. A future refactor that wraps the cleaning stage in a
        broad try/except (the CLI already does this pattern one layer up)
        could start silently swallowing this "must never happen" violation --
        this test would catch that regression."""
        df = pd.DataFrame({"quantity": [10.0, 20.0, -5.0]})
        csv_path = tmp_path / "input.csv"
        df.to_csv(csv_path, index=False)

        with patch(
            "backend.rules.cleaning_coordinator.CleaningEngine.clean",
            return_value=(
                df.copy(),
                CleaningResult(
                    pipeline_run_id="run-e2e-guard",
                    total_findings=1,
                    autonomous_findings=0,
                    actions=[self._human_only_action()],
                    rows_before=3,
                    rows_after=3,
                    columns_before=1,
                    columns_after=1,
                    cleaned_at="2026-01-01T00:00:00+00:00",
                ),
            ),
        ):
            with pytest.raises(CleaningEngineError, match="Tier-3 boundary violation"):
                run_full_pipeline(
                    input_path=csv_path,
                    output_path=tmp_path / "report.docx",
                    enable_cleaning=True,
                )
