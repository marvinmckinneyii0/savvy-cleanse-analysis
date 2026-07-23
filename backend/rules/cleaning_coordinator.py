"""Cleaning coordinator (Story 3.4).

Runs the two cleaning tiers on a single working copy, in order, and merges their
provenance into one :class:`~backend.models.cleaning_result.CleaningResult`:

    Tier-1  CleaningEngine.clean(df)          -> autonomous mechanical fixes
    Tier-2  apply_imputation_policy(df, ...)   -> human-policy null imputation

The engine's output frame is the policy layer's input, so both tiers act on the
same working copy and the caller's frame is never mutated (Tier-1 deep-copies at
entry; Tier-2 copies-and-returns). The engine is imported and used **unchanged**
— no Tier-2 code lives inside it; composition happens only here.

The merged result carries **both** tiers' actions in one ``actions`` list, each
distinguishable by ``remediation_class`` (``agent_autonomous`` vs
``human_policy_agent_execution``), so Story 3.3 renders one manifest from one
list. Shape counters span both passes (``rows_before``/``columns_before`` from
the original frame; ``rows_after``/``columns_after`` from the final frame).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from backend.models.cleaning_result import CleaningOperation, CleaningResult
from backend.models.pipeline_config import ImputationPolicyConfig
from backend.models.quality_report import DataQualityReport
from backend.pipeline.cleaning_engine import CleaningEngine
from backend.rules.cleaning_policy import apply_imputation_policy


def _header_rename_mapping(tier1_result: CleaningResult) -> dict[str, str]:
    """Old->new column names Tier-1 actually applied (empty if none renamed)."""
    mapping: dict[str, str] = {}
    for action in tier1_result.actions:
        if action.operation == CleaningOperation.HEADER_NORMALIZATION:
            mapping.update(action.value_mapping)
    return mapping


def _remap_report_columns(
    quality_report: DataQualityReport, mapping: dict[str, str]
) -> DataQualityReport:
    """Translate every defect's ``affected_columns`` through a rename mapping.

    A column can carry both a Tier-1 ``column_naming`` finding and a Tier-2
    ``null_values`` finding; Tier-1 renames the header before Tier-2 runs, so
    the report's column references must be translated to match the ACTUAL
    (possibly renamed) working frame Tier-2 receives — otherwise Tier-2's
    column-existence guard misfires on the stale pre-rename name. Names absent
    from ``mapping`` (including everything, if nothing was renamed) pass
    through unchanged; ``quality_report`` itself is never mutated.
    """
    if not mapping:
        return quality_report
    translated_defects = [
        defect.model_copy(
            update={
                "affected_columns": [
                    mapping.get(col, col) for col in defect.affected_columns
                ]
            }
        )
        for defect in quality_report.defects
    ]
    return quality_report.model_copy(update={"defects": translated_defects})


def clean_dataset(
    df: pd.DataFrame,
    quality_report: DataQualityReport,
    policy: ImputationPolicyConfig,
    pipeline_run_id: str,
) -> tuple[pd.DataFrame, CleaningResult]:
    """Run Tier-1 then Tier-2 on one working copy; return ``(cleaned_df, result)``.

    ``df`` is never mutated. The returned :class:`CleaningResult` merges both
    tiers' actions and reports the net shape change across the combined pass.
    """
    # Tier 1 — autonomous engine (deep-copies df at entry, returns a new frame).
    tier1_df, tier1_result = CleaningEngine().clean(df, quality_report, pipeline_run_id)

    # Tier 2 — human-policy imputation on the Tier-1 output (copies-and-returns).
    # The report is translated through any header rename Tier-1 applied, so a
    # column carrying both a column_naming AND a null_values finding resolves
    # under its post-rename name rather than a stale pre-rename one.
    tier2_report = _remap_report_columns(
        quality_report, _header_rename_mapping(tier1_result)
    )
    cleaned_df, tier2_actions = apply_imputation_policy(
        tier1_df, tier2_report, policy, pipeline_run_id
    )

    rows_after, columns_after = cleaned_df.shape
    merged = CleaningResult(
        pipeline_run_id=pipeline_run_id,
        total_findings=tier1_result.total_findings,
        autonomous_findings=tier1_result.autonomous_findings,
        actions=[*tier1_result.actions, *tier2_actions],
        rows_before=tier1_result.rows_before,
        rows_after=rows_after,
        columns_before=tier1_result.columns_before,
        columns_after=columns_after,
        cleaned_at=datetime.now(timezone.utc).isoformat(),
    )
    return cleaned_df, merged
