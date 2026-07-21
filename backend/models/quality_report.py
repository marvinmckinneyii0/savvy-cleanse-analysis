"""Data-quality Pydantic models.

Defines the output contract for :class:`DataQualityAssessor`: every
finding is a :class:`DataQualityDefect`, every column gets a
:class:`ColumnProfile`, and the aggregate report is a
:class:`DataQualityReport`.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class Severity(str, Enum):
    """Defect severity — drives halt-on-critical logic."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DefectCategory(str, Enum):
    """The six detection categories scanned by the quality assessor."""

    STRUCTURAL_INTEGRITY = "structural_integrity"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    UNIQUENESS = "uniqueness"
    STATISTICAL_RED_FLAG = "statistical_red_flag"
    REFERENTIAL_INTEGRITY = "referential_integrity"


class RemediationClass(str, Enum):
    """Who owns the fix for a finding — the four-tier ownership model.

    Set by :mod:`backend.pipeline.remediation_classifier`, which is the single
    authoritative ``defect_type`` → class mapping. Consumed by the Cleaning
    Engine (Story 3.2) and the Opt-in Gate (3.4) to decide what may be touched.

    * ``AGENT_AUTONOMOUS`` — Tier 1. Agent fixes unconditionally
      (whitespace/case/type normalization, exact duplicate rows, header
      misalignment).
    * ``HUMAN_POLICY_AGENT_EXECUTION`` — Tier 2. Human sets the policy once
      (e.g. null-imputation method per column); the agent then executes it
      indefinitely.
    * ``HUMAN_ONLY`` — Tier 3. The agent detects and scores but NEVER acts.
      Also the fail-safe default (see :class:`DataQualityDefect`).

    There is deliberately **no Tier 4 value**. Tier 4 (Epic 11) is an opt-in
    overlay permitting autonomous action on ``HUMAN_ONLY`` findings; the
    ``remediation_class`` itself stays ``HUMAN_ONLY``.

    These are internal identifiers. Client-facing surfaces use descriptive
    names (Story 3.9) and must never expose tier numbers.
    """

    AGENT_AUTONOMOUS = "agent_autonomous"
    HUMAN_POLICY_AGENT_EXECUTION = "human_policy_agent_execution"
    HUMAN_ONLY = "human_only"


class DataQualityDefect(BaseModel):
    """A single data-quality finding."""

    defect_type: str
    category: DefectCategory
    severity: Severity
    affected_columns: list[str]
    count: int
    percentage: float
    details: str
    recommended_action: str
    # Defaulted for two independent reasons, both load-bearing:
    #   1. Backward compatibility — Epic 1/2 findings and any serialized report
    #      predating this field still validate.
    #   2. Fail-safe — an unmapped or future defect_type must never be eligible
    #      for autonomous cleaning, so the default is the most conservative
    #      class. Never relax this default.
    remediation_class: RemediationClass = RemediationClass.HUMAN_ONLY


class ColumnProfile(BaseModel):
    """Per-column statistical summary."""

    column_name: str
    dtype: str
    null_count: int
    null_pct: float
    unique_count: int
    unique_pct: float
    has_mixed_types: bool
    min_val: float | None = None
    max_val: float | None = None
    mean_val: float | None = None
    std_val: float | None = None


class DataQualityReport(BaseModel):
    """Aggregate quality report — the payload inside PipelineResult."""

    overall_severity: Severity
    has_critical_issues: bool
    halt_reason: str | None = None
    defects: list[DataQualityDefect]
    column_profiles: dict[str, ColumnProfile]
    total_rows: int
    total_columns: int
    overall_quality_score: float
    assessed_at: str
