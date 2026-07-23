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

from backend.models.cleaning_result import CleaningResult
from backend.models.pipeline_config import ImputationPolicyConfig
from backend.models.quality_report import DataQualityReport
from backend.pipeline.cleaning_engine import CleaningEngine
from backend.rules.cleaning_policy import apply_imputation_policy


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
    cleaned_df, tier2_actions = apply_imputation_policy(
        tier1_df, quality_report, policy, pipeline_run_id
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
