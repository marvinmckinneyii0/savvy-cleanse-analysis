"""Tier-2 null-imputation policy layer (Story 3.4).

The Tier-2 analogue of the Tier-1 Cleaning Engine: where the engine acts
*autonomously* on a frozen registry of mechanical fixes, this layer executes a
**human-supplied policy** — but only over the single Tier-2 defect it is scoped
to, ``null_values``. It resolves an imputation *method* per column (built-in
default-by-type unless the client overrode it), drives the policy-less
:func:`~backend.pipeline.cleaning_primitives.impute_nulls` primitive, and emits
one :class:`~backend.models.cleaning_result.CleaningAction` per finding — the
same provenance model Tier-1 uses, so Story 3.3 renders one manifest from one
list.

Fail-closed discipline (mirrors the engine, load-bearing — Epic 3 invariant):

* The executor filters to findings that are **both**
  ``remediation_class == HUMAN_POLICY_AGENT_EXECUTION`` **and**
  ``defect_type == "null_values"``. A ``human_only`` (Tier-3) finding — even on
  a column that also carries a Tier-2 null finding — is therefore unreachable.
* Any other Tier-2 ``defect_type`` (e.g. ``non_unique_id``) is recorded SKIPPED
  with zero data change; there is no config key that widens this allowlist.
* The caller's DataFrame is never mutated: :func:`impute_nulls` copies-and-
  returns, this executor only ever rebinds its working frame to those copies,
  and it always returns a fresh frame.

``leave_as_is`` is a policy-layer-only method: it resolves to a SKIPPED action
with no primitive call (the primitive has no such method by design).
"""

from __future__ import annotations

import pandas as pd
import structlog

from backend.models.cleaning_result import (
    CleaningAction,
    CleaningOperation,
    CleaningScope,
    CleaningStatus,
)
from backend.models.pipeline_config import ImputationPolicyConfig
from backend.models.quality_report import (
    DataQualityDefect,
    DataQualityReport,
    RemediationClass,
)
from backend.pipeline.cleaning_primitives import impute_nulls

# Policy-layer-only method: resolve → skip, never call the primitive.
LEAVE_AS_IS = "leave_as_is"

# The single Tier-2 defect this layer is scoped to act on.
_IMPUTATION_DEFECT_TYPE = "null_values"

# Built-in method per column kind — the defensible default an SMB who never
# touches imputation config gets, so they are never blocked "at step one".
BUILTIN_DEFAULTS: dict[str, str] = {
    "numeric": "median",  # robust to the outliers SMB revenue/quantity carry
    "categorical": "mode",  # most-frequent label is the only defensible fill
    "datetime": "forward_fill",  # carry last known value forward (time-series)
}

# Truncate any primitive error before it reaches a provenance record — pandas
# messages can embed a column's dtype/name; cap to keep the record bounded and
# ensure no raw cell value could ever ride along.
_MAX_ERROR_LEN = 200


def column_kind(series: pd.Series) -> str:
    """Classify a column as ``numeric | categorical | datetime`` for defaulting.

    Datetime is checked first (a datetime column is not "numeric"). Everything
    that is neither datetime nor numeric — object/string/category — is treated
    as categorical (``mode`` fill). Pure and deterministic.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    return "categorical"


def resolve_method(
    column: str, series: pd.Series, policy: ImputationPolicyConfig
) -> tuple[str, str]:
    """Resolve the imputation method for ``column`` and report its source.

    Precedence (highest first): per-column override → per-type default override
    → built-in default-by-type. Returns ``(method, source)`` where ``source`` is
    ``"override"`` (the client's explicit config chose it) or ``"default"`` (the
    built-in per-type default). Deterministic: plain dict lookups, no ordering
    dependence.
    """
    if column in policy.columns:
        return policy.columns[column], "override"
    kind = column_kind(series)
    if kind in policy.defaults:
        return policy.defaults[kind], "override"
    return BUILTIN_DEFAULTS[kind], "default"


def apply_imputation_policy(
    df: pd.DataFrame,
    quality_report: DataQualityReport,
    policy: ImputationPolicyConfig,
    pipeline_run_id: str,
) -> tuple[pd.DataFrame, list[CleaningAction]]:
    """Execute the Tier-2 imputation policy over a working copy of ``df``.

    Acts **only** on findings that are both ``HUMAN_POLICY_AGENT_EXECUTION`` and
    ``null_values``; every other Tier-2 finding is recorded SKIPPED with zero
    change. ``df`` is never mutated — a fresh frame is always returned. Returns
    ``(cleaned_df, actions)``; the coordinator merges ``actions`` into the
    combined :class:`CleaningResult`.
    """
    log = structlog.get_logger().bind(pipeline_run_id=pipeline_run_id)

    tier2 = [
        d
        for d in quality_report.defects
        if d.remediation_class == RemediationClass.HUMAN_POLICY_AGENT_EXECUTION
    ]

    working = df
    actions: list[CleaningAction] = []

    # Deterministic order: by defect_type then first affected column.
    for defect in sorted(
        tier2,
        key=lambda d: (d.defect_type, d.affected_columns[0] if d.affected_columns else ""),
    ):
        # Fail-closed: anything Tier-2 that is not null-imputation is skipped.
        if defect.defect_type != _IMPUTATION_DEFECT_TYPE:
            actions.append(_skipped_non_imputation(defect))
            log.info(
                "cleaning_policy_skipped",
                defect_type=defect.defect_type,
                reason="tier2_not_null_imputation",
            )
            continue

        for column in defect.affected_columns:
            if column not in working.columns:
                # Report/frame drift — record FAILED, never crash the pipeline.
                actions.append(
                    _failed_action(
                        column, KeyError(f"column {column!r} not in frame")
                    )
                )
                log.warning(
                    "cleaning_policy_failed",
                    column=column,
                    error_type="KeyError",
                )
                continue

            method, source = resolve_method(column, working[column], policy)

            if method == LEAVE_AS_IS:
                actions.append(_leave_as_is_action(column, source))
                log.info(
                    "cleaning_policy_skipped",
                    column=column,
                    method=LEAVE_AS_IS,
                    source=source,
                    reason="policy_leave_as_is",
                )
                continue

            try:
                before_nulls = int(working[column].isna().sum())
                working = impute_nulls(working, column, method)
                after_nulls = int(working[column].isna().sum())
            except Exception as exc:  # noqa: BLE001 - captured as safe provenance
                actions.append(_failed_action(column, exc, method=method, source=source))
                log.warning(
                    "cleaning_policy_failed",
                    column=column,
                    method=method,
                    error_type=type(exc).__name__,
                )
                continue

            filled = before_nulls - after_nulls
            actions.append(
                _applied_action(column, method, source, filled, before_nulls, after_nulls)
            )
            log.info(
                "cleaning_policy_applied",
                column=column,
                method=method,
                source=source,
                values_changed=filled,
            )

    # Working-copy contract: return a fresh frame even when nothing was imputed,
    # so a caller can never mutate our return and reach the input frame.
    if working is df:
        working = df.copy()
    return working, actions


# ---------------------------------------------------------------------------
# CleaningAction builders — one provenance shape per outcome.
# ---------------------------------------------------------------------------


def _applied_action(
    column: str, method: str, source: str, filled: int, before_nulls: int, after_nulls: int
) -> CleaningAction:
    return CleaningAction(
        operation=CleaningOperation.NULL_IMPUTATION,
        defect_type=_IMPUTATION_DEFECT_TYPE,
        remediation_class=RemediationClass.HUMAN_POLICY_AGENT_EXECUTION,
        status=CleaningStatus.APPLIED,
        scope=CleaningScope.COLUMN,
        target_columns=[column],
        values_changed=filled,
        before_state=f"{before_nulls} null(s)",
        after_state=f"{after_nulls} null(s)",
        parameters={"method": method, "source": source},
        rule=f"impute nulls in '{column}' via {method} ({source} policy)",
        detail=(
            f"Imputed {filled} null value(s) in '{column}' using {method} "
            f"({source} policy)."
        ),
    )


def _leave_as_is_action(column: str, source: str) -> CleaningAction:
    return CleaningAction(
        operation=CleaningOperation.NO_OP,
        defect_type=_IMPUTATION_DEFECT_TYPE,
        remediation_class=RemediationClass.HUMAN_POLICY_AGENT_EXECUTION,
        status=CleaningStatus.SKIPPED,
        scope=CleaningScope.COLUMN,
        target_columns=[column],
        parameters={"method": LEAVE_AS_IS, "source": source},
        rule="policy method 'leave_as_is' — nulls preserved, primitive not called",
        detail=f"Left null value(s) in '{column}' unchanged per policy ({source}).",
    )


def _skipped_non_imputation(defect: DataQualityDefect) -> CleaningAction:
    """SKIPPED record for a Tier-2 finding that is not null-imputation."""
    return CleaningAction(
        operation=CleaningOperation.NO_OP,
        defect_type=defect.defect_type,
        remediation_class=defect.remediation_class,
        status=CleaningStatus.SKIPPED,
        scope=CleaningScope.COLUMN,
        target_columns=list(defect.affected_columns),
        rule="Tier-2 policy layer acts only on null_values — failing closed",
        detail=(
            f"Finding '{defect.defect_type}' is Tier-2 but not null-imputation; "
            "skipped without modifying data."
        ),
    )


def _failed_action(
    column: str,
    exc: Exception,
    *,
    method: str | None = None,
    source: str | None = None,
) -> CleaningAction:
    """FAILED record with safe error info (type + truncated message only)."""
    safe_message = str(exc)[:_MAX_ERROR_LEN]
    parameters: dict[str, str] = {}
    if method is not None:
        parameters["method"] = method
    if source is not None:
        parameters["source"] = source
    return CleaningAction(
        operation=CleaningOperation.NULL_IMPUTATION,
        defect_type=_IMPUTATION_DEFECT_TYPE,
        remediation_class=RemediationClass.HUMAN_POLICY_AGENT_EXECUTION,
        status=CleaningStatus.FAILED,
        scope=CleaningScope.COLUMN,
        target_columns=[column],
        parameters=parameters,
        rule="imputation raised; working copy left at last-good state",
        detail=f"Imputation for '{column}' did not complete.",
        error=f"{type(exc).__name__}: {safe_message}",
    )
