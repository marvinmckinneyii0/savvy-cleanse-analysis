"""Healing Manifest — the client-facing rendering of cleaning provenance (Story 3.3).

Renders :class:`~backend.models.cleaning_result.CleaningResult` (Story 3.2's
`CleaningEngine` output, merged with Story 3.4's Tier-2 imputation actions) into
a structured, report-ready record. This module does **not** re-inspect the
DataFrame or reconstruct what changed — everything here is derived purely from
`CleaningAction` fields already produced by the engine/policy layer. Per
`cleaning_result.py`'s own docstring: do not add a parallel provenance format.

Two responsibilities live here:

1. **Outcome classification** (`classify_outcome`) — a deterministic, fail-closed
   derivation of a 4th presentation category (`NO_EFFECT`) that reconciles a real
   inconsistency between Story 3.2 (a zero-effect Tier-1 op stays `APPLIED`) and
   Story 3.4 (a zero-effect Tier-2 imputation is recorded `SKIPPED`), without
   modifying either story's `CleaningStatus` values.
2. **Sanitization** (`sanitize_manifest_text`, `_failed_entry_detail`) — a
   stricter data-disclosure boundary than 3.2/3.4's existing FAILED-action
   truncation, because this is the first place that content reaches a
   client-facing document. FAILED entries never render the underlying
   exception message, only its type name.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from backend.models.cleaning_result import (
    CleaningAction,
    CleaningOperation,
    CleaningResult,
    CleaningStatus,
)
from backend.models.quality_report import RemediationClass

# The report-semantics disclosure (AC9): must appear, verbatim, in every
# rendered manifest. States plainly that cleaning acted on a separate working
# copy and that the analytical report still describes the ORIGINAL dataset —
# never implying the report was computed from the cleaned export.
REPORT_SEMANTICS_DISCLOSURE = (
    "Cleaning was performed on a separate working copy. The original data was "
    "not modified, and the analytical report continues to use the original "
    "dataset."
)

# The one explicit, additive marker `cleaning_policy._no_effect_action` sets.
# The classifier trusts THIS, not operation/defect_type guessing, to identify
# the Tier-2 "attempted, no effect" shape (see module docstring point 1).
# PUBLIC (not underscore-prefixed): `cleaning_policy.py` imports these rather
# than hardcoding the string literal, so the two sides of the contract can
# never silently drift apart via an independent typo/rename in either file.
NO_EFFECT_HINT_KEY = "manifest_outcome_hint"
NO_EFFECT_HINT_VALUE = "no_effect"

_DEFAULT_MAX_DETAIL_LEN = 300


class ManifestOutcome(str, Enum):
    """The 4 presentation categories a manifest entry renders under.

    Deliberately a DIFFERENT enum from :class:`CleaningStatus` (3 values), not
    a superset/subclass of it — a `ManifestEntry` keeps both `original_status`
    and `outcome` as separate fields so a reader can always see the raw engine
    status alongside the derived presentation category.
    """

    APPLIED = "applied"
    SKIPPED = "skipped"
    FAILED = "failed"
    NO_EFFECT = "no_effect"


def classify_outcome(action: CleaningAction) -> ManifestOutcome:
    """Derive the presentation outcome for one action. Deterministic, fail-closed.

    Priority order (first match wins):

    1. ``status == FAILED`` -> FAILED.
    2. ``status == APPLIED`` and (`rows_affected` or `values_changed` > 0) -> APPLIED.
    3. ``status == APPLIED`` and both counters are 0 -> NO_EFFECT (Tier-1's
       "ran, zero effect" shape, e.g. a dedup pass that removed 0 rows).
    4. ``status == SKIPPED`` and ``operation == NO_OP`` -> SKIPPED (nothing was
       ever attempted — a genuine decline/out-of-scope finding).
    5. ``status == SKIPPED`` and the explicit `manifest_outcome_hint` marker is
       present -> NO_EFFECT (Tier-2's "ran, zero effect" shape).
    6. Any other SKIPPED shape -> SKIPPED.

    Step 5 intentionally does NOT key on "operation != NO_OP" alone: a future
    Tier-2 policy could reject a NULL_IMPUTATION finding BEFORE ever calling
    the primitive (a decline, not a no-effect attempt), and that would carry
    the identical operation/defect_type/remediation_class tuple as the real
    no-effect case. No combination of pre-existing fields can tell those apart
    reliably, so this only trusts the one explicit marker set at the source
    (`cleaning_policy._no_effect_action`). An unrecognized SKIPPED shape —
    including any future skip nobody has taught this function about — falls
    through to plain SKIPPED, never silently becomes NO_EFFECT.
    """
    if action.status == CleaningStatus.FAILED:
        return ManifestOutcome.FAILED

    if action.status == CleaningStatus.APPLIED:
        if action.rows_affected > 0 or action.values_changed > 0:
            return ManifestOutcome.APPLIED
        return ManifestOutcome.NO_EFFECT

    # status == CleaningStatus.SKIPPED
    if action.operation == CleaningOperation.NO_OP:
        return ManifestOutcome.SKIPPED
    if action.parameters.get(NO_EFFECT_HINT_KEY) == NO_EFFECT_HINT_VALUE:
        return ManifestOutcome.NO_EFFECT
    return ManifestOutcome.SKIPPED


def sanitize_manifest_text(text: str, *, max_len: int = _DEFAULT_MAX_DETAIL_LEN) -> str:
    """Defensive length cap applied to every rendered manifest string.

    A second-layer safety net, not the primary defense: the primary defense is
    that non-FAILED `detail`/`rule` text already comes only from controlled
    f-string templates in `cleaning_engine.py`/`cleaning_policy.py` (verified
    by reading every action-builder — none interpolates a raw cell value or a
    caught exception), and FAILED entries never see this function applied to
    the raw error at all (see `_failed_entry_detail`).
    """
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _failed_entry_detail(action: CleaningAction) -> str:
    """Build a FAILED entry's rendered detail WITHOUT the raw exception message.

    `CleaningAction.error` is `f"{type(exc).__name__}: {message}"` (the format
    both `cleaning_engine.py` and `cleaning_policy.py` use consistently) where
    `message` is only length-capped, not content-guaranteed-safe — a pandas
    coercion/parse exception can embed the offending cell's repr. This
    extracts ONLY the exception type name (the substring before the first
    ": ") and discards the message half entirely. The full `error` string
    stays on the underlying `CleaningAction`/in logs for engineering
    debugging; it is simply never surfaced in the client-facing manifest.

    Fail-closed on the split itself: if `error` does NOT follow the expected
    "Type: message" convention (no ": " present), the whole string is treated
    as untrusted rather than assumed to be a safe type name — falling back to
    the generic "an error" label rather than risking the unsplit string (which
    could be the raw message) reaching the manifest.
    """
    error_type = "an error"
    if action.error:
        parts = action.error.split(": ", 1)
        if len(parts) == 2 and parts[0]:
            error_type = parts[0]

    columns = ", ".join(f"'{c}'" for c in action.target_columns) or "the target"
    detail = (
        f"{action.operation.value.replace('_', ' ').capitalize()} for {columns} "
        f"did not complete ({error_type}). The working copy was left unchanged "
        "for this action."
    )
    # Route through the same length cap every other outcome's detail gets —
    # target_columns can be long on a wide dataset, and this must not be the
    # one outcome that bypasses the uniform length guarantee.
    return sanitize_manifest_text(detail)


class ManifestEntry(BaseModel):
    """One rendered line of the Healing Manifest, derived from one `CleaningAction`.

    Preserves full provenance: both the raw `original_status` the engine/policy
    layer recorded AND the derived, presentation-only `outcome`, so nothing is
    lost even if a future author disagrees with the classification.
    """

    sequence: int
    remediation_class: RemediationClass
    original_status: CleaningStatus
    outcome: ManifestOutcome
    operation: CleaningOperation
    target_columns: list[str] = Field(default_factory=list)
    rows_affected: int = 0
    values_changed: int = 0
    detail: str = ""


class HealingManifest(BaseModel):
    """The report-ready aggregate. One per pipeline run that had cleaning enabled.

    `entries` preserves `CleaningResult.actions`' exact order — never regrouped
    or sorted by outcome/operation. `outcome_counts` is a separate aggregate
    summary that does not affect entry ordering.
    """

    pipeline_run_id: str
    cleaned_at: str
    rows_before: int
    rows_after: int
    columns_before: int
    columns_after: int
    entries: list[ManifestEntry] = Field(default_factory=list)
    outcome_counts: dict[str, int] = Field(default_factory=dict)
    report_semantics_disclosure: str = REPORT_SEMANTICS_DISCLOSURE


def build_healing_manifest(result: CleaningResult) -> HealingManifest:
    """Render a `HealingManifest` from a `CleaningResult`. Pure, order-preserving.

    Never inspects a DataFrame; never re-derives what changed. `result.actions`
    is enumerated in its existing order — that order is preserved verbatim in
    `entries`.
    """
    entries: list[ManifestEntry] = []
    counts: dict[str, int] = {outcome.value: 0 for outcome in ManifestOutcome}

    for index, action in enumerate(result.actions):
        outcome = classify_outcome(action)
        counts[outcome.value] += 1

        detail = (
            _failed_entry_detail(action)
            if outcome == ManifestOutcome.FAILED
            else sanitize_manifest_text(action.detail)
        )

        entries.append(
            ManifestEntry(
                sequence=index,
                remediation_class=action.remediation_class,
                original_status=action.status,
                outcome=outcome,
                operation=action.operation,
                target_columns=list(action.target_columns),
                rows_affected=action.rows_affected,
                values_changed=action.values_changed,
                detail=detail,
            )
        )

    return HealingManifest(
        pipeline_run_id=result.pipeline_run_id,
        cleaned_at=result.cleaned_at,
        rows_before=result.rows_before,
        rows_after=result.rows_after,
        columns_before=result.columns_before,
        columns_after=result.columns_after,
        entries=entries,
        outcome_counts=counts,
    )
