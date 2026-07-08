"""Drift-detection Pydantic models.

Defines the contract for :class:`~backend.pipeline.drift_engine.DriftEngine`:
a persisted :class:`BaselineProfile` snapshot per dataset, and a
:class:`DriftReport` produced when a current DataFrame is compared against
that baseline. Every classified observation is a :class:`DriftFinding`
carrying a reused :class:`~backend.models.quality_report.Severity` (drift
only ever emits HIGH/MEDIUM/LOW — never CRITICAL, since drift is
informational and never a halt condition).

This module fulfils the ``TYPE_CHECKING`` forward reference in
:mod:`backend.models.pipeline_result` (``drift_report: "DriftReport | None"``).
"""

from __future__ import annotations

from pydantic import BaseModel

from backend.models.quality_report import Severity


class ColumnBaselineStats(BaseModel):
    """Per-column statistical snapshot stored in a :class:`BaselineProfile`.

    Numeric columns populate ``mean``/``median``/``std``/``q25``/``q75`` and
    leave ``category_distribution`` ``None``; categorical/object columns do the
    inverse. ``null_pct`` is always populated.
    """

    dtype: str
    null_pct: float
    mean: float | None = None
    median: float | None = None
    std: float | None = None
    q25: float | None = None
    q75: float | None = None
    category_distribution: dict[str, float] | None = None


class BaselineProfile(BaseModel):
    """Persisted per-dataset baseline the Drift Engine compares against."""

    dataset_key: str
    row_count: int
    columns: dict[str, ColumnBaselineStats]
    consecutive_clean_runs: int = 0
    created_at: str
    updated_at: str


class DriftFinding(BaseModel):
    """One classified drift observation.

    ``column`` is ``None`` for dataset-level checks (volume, schema).
    ``severity`` is HIGH/MEDIUM/LOW only (never CRITICAL).
    """

    check: str
    column: str | None
    severity: Severity
    actual_value: float
    detail: str


class VolumeDrift(BaseModel):
    """Row-count drift between current and baseline."""

    current_row_count: int
    baseline_row_count: int
    pct_change: float
    finding: DriftFinding | None = None


class NumericColumnDrift(BaseModel):
    """Numeric-column drift across mean/median/variance checks."""

    column: str
    mean_shift: DriftFinding | None = None
    median_shift: DriftFinding | None = None
    variance_shift: DriftFinding | None = None


class CategoricalColumnDrift(BaseModel):
    """Categorical-column drift across PSI and new/missing category checks."""

    column: str
    psi: DriftFinding | None = None
    new_categories: list[str]
    missing_categories: list[str]
    category_findings: list[DriftFinding]


class SchemaDrift(BaseModel):
    """Column-set and dtype changes between baseline and current.

    ``finding`` is always HIGH when any of ``columns_added``/
    ``columns_removed``/``dtype_changes`` is non-empty (architecture's
    "schema drift is always HIGH" rule).
    """

    columns_added: list[str]
    columns_removed: list[str]
    dtype_changes: dict[str, str]
    finding: DriftFinding | None = None


class DriftReport(BaseModel):
    """Aggregate drift report — the payload the Reporting Agent embeds.

    ``overall_severity`` is the max severity across all findings, ``LOW`` if
    nothing crossed a threshold. Never ``CRITICAL``.
    """

    pipeline_run_id: str
    computed_at: str
    volume_drift: VolumeDrift
    numeric_drift: list[NumericColumnDrift]
    categorical_drift: list[CategoricalColumnDrift]
    schema_drift: SchemaDrift
    drift_summary: str
    overall_severity: Severity
    recommendations: list[str]
