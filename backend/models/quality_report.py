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
