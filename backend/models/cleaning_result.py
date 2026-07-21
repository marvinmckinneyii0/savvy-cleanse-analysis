"""Cleaning-engine Pydantic models (Story 3.2).

Defines the structured record the deterministic Cleaning Engine emits: one
:class:`CleaningAction` per remediation applied (or skipped/failed), aggregated
into a :class:`CleaningResult`.

**This is the single source of provenance for Story 3.3's Healing Manifest.**
Every field a manifest needs to describe *what happened to the data* lives here,
so 3.3 renders from this model and never re-inspects or reconstructs the
mutation. Do not add a parallel manifest format — extend this instead.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from backend.models.quality_report import RemediationClass


class CleaningOperation(str, Enum):
    """The deterministic remediations the engine can apply.

    The four autonomous operations map 1:1 from a Tier-1 ``defect_type`` (see
    :mod:`backend.pipeline.cleaning_engine`). ``NULL_IMPUTATION`` is the
    policy-less primitive Story 3.4 will drive through the Tier-2 policy layer;
    it is **never** reached by the autonomous path.
    """

    DEDUPLICATION = "deduplication"
    CASE_NORMALIZATION = "case_normalization"
    TYPE_COERCION = "type_coercion"
    HEADER_NORMALIZATION = "header_normalization"
    NULL_IMPUTATION = "null_imputation"
    # Sentinel for a recorded action where no remediation ran (a SKIPPED
    # autonomous finding the engine has no operation for). Never an applied fix.
    NO_OP = "no_op"


class CleaningScope(str, Enum):
    """What granularity an action touched — helps the manifest phrase itself."""

    COLUMN = "column"  # one or more named columns
    ROW = "row"  # whole rows (deduplication)
    TABLE = "table"  # table-level structure (header normalization)


class CleaningStatus(str, Enum):
    """Outcome of a single action."""

    APPLIED = "applied"  # remediation ran and changed the working copy
    SKIPPED = "skipped"  # deliberately not applied (fail-closed); no change
    FAILED = "failed"  # a primitive raised; working copy left at last-good state


class CleaningAction(BaseModel):
    """A single remediation the engine attempted, with full provenance.

    Carries everything Story 3.3 needs to render one manifest line without
    touching the data again: which finding drove it, which operation ran, the
    before/after state, how much changed, the deterministic rule used, and —
    on the non-applied paths — a safe reason or error string.
    """

    operation: CleaningOperation
    defect_type: str
    remediation_class: RemediationClass
    status: CleaningStatus
    scope: CleaningScope
    # Columns the action targeted. For ROW scope (dedup) this is the full column
    # list the duplicate spanned; for TABLE scope (header) the columns renamed.
    target_columns: list[str] = Field(default_factory=list)
    # Row-level effect (rows removed by dedup). Cell-level effect (values
    # rewritten by case/coercion). Both default 0 so a manifest can sum them.
    rows_affected: int = 0
    values_changed: int = 0
    # Compact, human/machine-readable snapshots of state either side of the
    # change (e.g. "50 rows" -> "48 rows"; "{North, north, NORTH}" -> "north").
    before_state: str = ""
    after_state: str = ""
    # Structured old->new mapping for the operations whose provenance IS a
    # mapping: case variant->canonical, and header old->new. Empty otherwise.
    value_mapping: dict[str, str] = Field(default_factory=dict)
    # Deterministic parameters that fully determine the result given the input
    # (e.g. dominant_type, uncoerced count, tie_break rule). All stringified so
    # the record stays JSON-safe and manifest-renderable.
    parameters: dict[str, str] = Field(default_factory=dict)
    # The deterministic rule applied, stated so the manifest can cite it.
    rule: str = ""
    # Human-readable one-liner.
    detail: str = ""
    # Safe error information on the FAILED path — exception type + message only,
    # never raw row data or PII. ``None`` on applied/skipped.
    error: str | None = None


class CleaningResult(BaseModel):
    """Aggregate record of one cleaning pass — the manifest's root object.

    Returned alongside the cleaned DataFrame from
    :meth:`backend.pipeline.cleaning_engine.CleaningEngine.clean`. The frame and
    this record travel separately (a DataFrame is not a Pydantic-serializable
    stage boundary type); this object is the durable, serializable half.
    """

    pipeline_run_id: str
    # Findings the engine saw vs. the autonomous subset it was allowed to act on.
    total_findings: int
    autonomous_findings: int
    actions: list[CleaningAction] = Field(default_factory=list)
    # Frame shape either side of the pass — lets the manifest state net effect
    # without recomputing from the data.
    rows_before: int
    rows_after: int
    columns_before: int
    columns_after: int
    # Envelope timestamp (ISO 8601 UTC). The ONLY non-deterministic value in the
    # result; data values never depend on it.
    cleaned_at: str
