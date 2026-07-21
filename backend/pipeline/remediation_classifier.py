"""Remediation Classifier — assigns ownership of every DQA finding (Story 3.1).

Stamps each :class:`DataQualityDefect` with the
:class:`~backend.models.quality_report.RemediationClass` that declares *who may
fix it*: the agent unconditionally (Tier 1), the agent under a human-set policy
(Tier 2), or a human only (Tier 3). The Cleaning Engine (Story 3.2) and Opt-in
Gate (3.4) act on this tag — so a mis-classification here is the mechanism by
which a human-only finding could be auto-modified. That is the load-bearing
invariant of Epic 3.

Two design rules protect it:

1. **Keyed on ``defect_type``, never on ``category``.** Categories split across
   tiers in the spec: exact duplicates are Tier 1 while near-duplicates are
   Tier 3, and header misalignment is Tier 1 while an unreadable structure is
   Tier 3 — yet each pair shares a ``DefectCategory``. Keying on the narrower
   ``defect_type`` means a future ``near_duplicate`` type cannot silently
   inherit ``duplicate_rows``'s autonomous class.
2. **Unmapped ⇒ ``HUMAN_ONLY``.** Anything absent from the table below — a new
   detector, a typo, a renamed type — falls back to the most conservative
   class. Adding a detector can therefore never *widen* what the agent may
   touch; that requires a deliberate edit here.

Pure and side-effect-free: no I/O, no logging, no config. Architecture
compliance (architecture.md §745): lives in ``backend/pipeline/``, imports only
from ``models/``, never from ``api/`` or legacy modules.
"""

from __future__ import annotations

from backend.models.quality_report import (
    DataQualityDefect,
    DataQualityReport,
    RemediationClass,
)

# ---------------------------------------------------------------------------
# The authoritative mapping (Story 3.1, schema-extensions-spec.md §1).
#
# Every defect_type emitted by DataQualityAssessor appears here exactly once.
# A test asserts this table stays in sync with the assessor — if you add a
# detector, add its defect_type here, or it silently classifies HUMAN_ONLY.
# ---------------------------------------------------------------------------
_DEFECT_TYPE_TO_CLASS: dict[str, RemediationClass] = {
    # --- Tier 1: agent fixes unconditionally -------------------------------
    # Mechanical, reversible, no domain judgement required.
    "mixed_types": RemediationClass.AGENT_AUTONOMOUS,
    "column_naming": RemediationClass.AGENT_AUTONOMOUS,
    "case_inconsistency": RemediationClass.AGENT_AUTONOMOUS,
    "duplicate_rows": RemediationClass.AGENT_AUTONOMOUS,
    # --- Tier 2: human sets policy once, agent executes --------------------
    # A defensible default exists, but the choice belongs to the client.
    "null_values": RemediationClass.HUMAN_POLICY_AGENT_EXECUTION,
    "non_unique_id": RemediationClass.HUMAN_POLICY_AGENT_EXECUTION,
    # --- Tier 3: agent detects and scores, never acts ----------------------
    "zero_variance": RemediationClass.HUMAN_ONLY,
    "extreme_outliers": RemediationClass.HUMAN_ONLY,
    "extreme_cardinality": RemediationClass.HUMAN_ONLY,
    # negative_values: a domain-plausibility flag, not a formatting nit — it
    # fires only on columns whose name implies non-negativity (revenue, price,
    # quantity...). Whether a negative is an error, a refund, or legitimate is
    # a business question. Never auto-fix.
    "negative_values": RemediationClass.HUMAN_ONLY,
    # infinite_values: mechanically coercible to null, but inf usually signals
    # an upstream computation error a human should see rather than have
    # silently patched.
    "infinite_values": RemediationClass.HUMAN_ONLY,
    # duplicate_measurement: a *column-pair* correlation signal (Pearson
    # |corr| > 0.99) — a redundant-column hint, NOT a duplicate-record finding
    # (that is `duplicate_rows`, above, and is Tier 1). Remediation means
    # dropping or merging one of two correlated columns; which one is
    # canonical cannot be determined mechanically, and the change is
    # irreversible. Tier 3.
    "duplicate_measurement": RemediationClass.HUMAN_ONLY,
}


def classify(defect_type: str) -> RemediationClass:
    """Return the remediation class owning ``defect_type``.

    Unmapped types return :attr:`RemediationClass.HUMAN_ONLY` — the fail-safe.
    Pure: same input always yields the same output, with no side effects.
    """
    return _DEFECT_TYPE_TO_CLASS.get(defect_type, RemediationClass.HUMAN_ONLY)


def classify_defect(defect: DataQualityDefect) -> DataQualityDefect:
    """Return a copy of ``defect`` with ``remediation_class`` set.

    Does not mutate the input. Idempotent: the class is derived solely from
    ``defect_type``, so re-classifying an already-stamped defect is a no-op.
    """
    return defect.model_copy(update={"remediation_class": classify(defect.defect_type)})


def classify_defects(defects: list[DataQualityDefect]) -> list[DataQualityDefect]:
    """Stamp every defect in ``defects``, returning a new list."""
    return [classify_defect(defect) for defect in defects]


def classify_report(report: DataQualityReport) -> DataQualityReport:
    """Return a copy of ``report`` with every defect stamped.

    Convenience for callers holding a whole report (e.g. re-classifying a
    persisted one). The assessor stamps its defect list directly instead.
    """
    return report.model_copy(update={"defects": classify_defects(report.defects)})
