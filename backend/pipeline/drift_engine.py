"""Drift Engine — stateless distributional drift detection.

Compares a current :class:`pandas.DataFrame` against a persisted
:class:`~backend.models.drift_report.BaselineProfile` across 7 checks
(mean/median/variance shift, volume drift, categorical PSI, new/missing
categories, schema drift) and returns a Pydantic-validated
:class:`~backend.models.drift_report.DriftReport`.

Design constraints (architecture.md; story 2.3):

* ``compute_drift`` is a pure function — **no file I/O, no baseline
  mutation**. All persistence lives in ``run``/``_load_baseline``/
  ``_save_baseline``.
* Severity bands are **fixed architecture constants** (see ``_THRESHOLDS``
  below), never read from ``config.yaml``/``PipelineConfig``.
* A HIGH drift finding is a normal outcome carried on
  ``DriftReport.overall_severity`` — never raised. ``DriftComputationError``
  is reserved for infrastructure failures (corrupt baseline, degenerate
  stats).
* The engine never calls an LLM; ``recommendations`` are string templates.

Two spots the story spec left implicit, resolved here and documented:

* ``compute_drift`` accepts ``pipeline_run_id`` with a default of ``""`` so
  the AC-1 two-argument call form works for isolated-check tests, while the
  orchestrating ``run`` still threads the real run id into the report and
  logs.
* Categorical PSI emits a finding only at PSI >= 0.10 (standard "population
  stable below 0.10" convention). Below that the ``psi`` slot is ``None``,
  consistent with the ``DriftFinding | None`` model contract.
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import structlog
from pydantic import ValidationError

from backend.errors.exceptions import DriftComputationError
from backend.models.drift_report import (
    BaselineProfile,
    CategoricalColumnDrift,
    ColumnBaselineStats,
    DriftFinding,
    DriftReport,
    NumericColumnDrift,
    SchemaDrift,
    VolumeDrift,
)
from backend.models.quality_report import Severity

# --- Fixed severity thresholds (architecture.md, Story 2.3 Task 3 table) ---
# These are architecture constants, NOT PipelineConfig.metric_thresholds.
_MEAN_MEDIAN_HIGH = 0.30
_MEAN_MEDIAN_MEDIUM = 0.15
_MEAN_MEDIAN_LOW = 0.05

_VARIANCE_HIGH_HI, _VARIANCE_HIGH_LO = 2.0, 0.5
_VARIANCE_MED_HI, _VARIANCE_MED_LO = 1.5, 0.67

_VOLUME_HIGH = 0.50
_VOLUME_MEDIUM = 0.20
_VOLUME_LOW = 0.10

_PSI_HIGH = 0.25
_PSI_MEDIUM = 0.10  # below this: population considered stable, no finding
_PSI_EPSILON = 0.0001  # standard PSI smoothing for zero-proportion categories

_MISSING_CATEGORY_HIGH_REPR = 0.10  # missing category held >10% of baseline
_NEW_CATEGORY_MEDIUM_REPR = 0.05  # new category holds >5% of current

_ROTATION_THRESHOLD = 4  # consecutive clean runs before auto-rotation

# Baseline filenames are derived from a caller-supplied dataset_key. Constrain it
# to a safe stem so it can never escape baseline_dir via path traversal
# (e.g. "../../etc/x") or absolute paths — defense-in-depth at the I/O boundary.
_SAFE_DATASET_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

_SEVERITY_RANK = {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2, Severity.CRITICAL: 3}


class DriftEngine:
    """Stateless drift computation with scoped baseline file I/O."""

    def __init__(self, baseline_dir: str | Path = "backend/baselines") -> None:
        self.baseline_dir = Path(baseline_dir)

    # ------------------------------------------------------------------
    # Baseline persistence (Task 2)
    # ------------------------------------------------------------------
    def _baseline_path(self, dataset_key: str) -> Path:
        if dataset_key in {".", ".."} or not _SAFE_DATASET_KEY.match(dataset_key):
            raise DriftComputationError(
                f"Unsafe dataset_key {dataset_key!r}: must be a bare filename stem "
                "([A-Za-z0-9._-], no path separators or traversal)."
            )
        return self.baseline_dir / f"{dataset_key}.json"

    def _load_baseline(self, dataset_key: str) -> BaselineProfile | None:
        """Load a baseline profile, or ``None`` on first run.

        A file that exists but fails JSON parse or Pydantic validation is an
        infrastructure failure (corrupt baseline) → ``DriftComputationError``.
        Never uses ``eval``/``pickle`` — only ``json.loads`` + validation.
        """
        path = self._baseline_path(dataset_key)
        if not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return BaselineProfile.model_validate(raw)
        except (json.JSONDecodeError, ValidationError, OSError, UnicodeDecodeError) as exc:
            raise DriftComputationError(
                f"Baseline file for '{dataset_key}' is corrupt or unreadable: {exc}"
            ) from exc

    def _build_profile(
        self,
        df: pd.DataFrame,
        dataset_key: str,
        *,
        consecutive_clean_runs: int = 0,
    ) -> BaselineProfile:
        """Compute per-column stats and wrap them in a ``BaselineProfile``."""
        now = datetime.now(timezone.utc).isoformat()
        columns: dict[str, ColumnBaselineStats] = {}
        for col in df.columns:
            series = df[col]
            null_pct = float(series.isna().mean())
            if pd.api.types.is_numeric_dtype(series):
                columns[col] = ColumnBaselineStats(
                    dtype=str(series.dtype),
                    null_pct=null_pct,
                    mean=_nan_to_none(series.mean()),
                    median=_nan_to_none(series.median()),
                    std=_nan_to_none(series.std()),
                    q25=_nan_to_none(series.quantile(0.25)),
                    q75=_nan_to_none(series.quantile(0.75)),
                )
            else:
                columns[col] = ColumnBaselineStats(
                    dtype=str(series.dtype),
                    null_pct=null_pct,
                    category_distribution=_category_distribution(series),
                )
        return BaselineProfile(
            dataset_key=dataset_key,
            row_count=int(df.shape[0]),
            columns=columns,
            consecutive_clean_runs=consecutive_clean_runs,
            created_at=now,
            updated_at=now,
        )

    def _save_baseline(self, dataset_key: str, profile: BaselineProfile) -> None:
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self._baseline_path(dataset_key).write_text(
            profile.model_dump_json(indent=2), encoding="utf-8"
        )

    # ------------------------------------------------------------------
    # Stateless drift computation (Task 3)
    # ------------------------------------------------------------------
    def compute_drift(
        self,
        current_df: pd.DataFrame,
        baseline_profile: BaselineProfile,
        pipeline_run_id: str = "",
    ) -> DriftReport:
        """Pure comparison of ``current_df`` against ``baseline_profile``.

        No file I/O and no mutation of ``baseline_profile``. Raises
        ``DriftComputationError`` on an empty frame or a degenerate statistic
        (zero-denominator relative change) rather than emitting inf/NaN.
        """
        if current_df.empty:
            raise DriftComputationError("Cannot compute drift on an empty DataFrame.")

        logger = structlog.get_logger()
        findings: list[DriftFinding] = []

        # --- Schema drift (always HIGH if any change) ---
        schema_drift, schema_flagged_cols = self._schema_drift(current_df, baseline_profile)
        if schema_drift.finding is not None:
            findings.append(schema_drift.finding)

        # --- Volume drift ---
        volume_drift = self._volume_drift(current_df, baseline_profile)
        if volume_drift.finding is not None:
            findings.append(volume_drift.finding)

        # --- Per-column numeric & categorical drift ---
        numeric_drift: list[NumericColumnDrift] = []
        categorical_drift: list[CategoricalColumnDrift] = []
        columns_checked = 0

        for col, base_stats in baseline_profile.columns.items():
            if col in schema_flagged_cols or col not in current_df.columns:
                # Column added/removed/dtype-changed is a schema concern only.
                continue
            series = current_df[col]
            base_is_numeric = base_stats.mean is not None
            base_is_categorical = base_stats.category_distribution is not None
            cur_is_numeric = pd.api.types.is_numeric_dtype(series)

            if base_is_numeric and cur_is_numeric:
                col_drift = self._numeric_column_drift(col, series, base_stats)
                numeric_drift.append(col_drift)
                findings.extend(
                    f
                    for f in (col_drift.mean_shift, col_drift.median_shift, col_drift.variance_shift)
                    if f is not None
                )
                columns_checked += 1
            elif base_is_categorical and not cur_is_numeric:
                col_drift_cat = self._categorical_column_drift(col, series, base_stats)
                categorical_drift.append(col_drift_cat)
                if col_drift_cat.psi is not None:
                    findings.append(col_drift_cat.psi)
                findings.extend(col_drift_cat.category_findings)
                columns_checked += 1

        overall_severity = self._max_severity(findings)
        recommendations = [
            self._recommendation(f) for f in findings if f.severity == Severity.HIGH
        ]
        drift_summary = self._summarize(findings, overall_severity)

        report = DriftReport(
            pipeline_run_id=pipeline_run_id,
            computed_at=datetime.now(timezone.utc).isoformat(),
            volume_drift=volume_drift,
            numeric_drift=numeric_drift,
            categorical_drift=categorical_drift,
            schema_drift=schema_drift,
            drift_summary=drift_summary,
            overall_severity=overall_severity,
            recommendations=recommendations,
        )

        logger.info(
            "drift_computed",
            pipeline_run_id=pipeline_run_id,
            stage="drift_engine",
            columns_checked=columns_checked,
            findings_count=len(findings),
            overall_severity=overall_severity.value,
        )
        return report

    # ------------------------------------------------------------------
    # Orchestrating entry point + rotation (Task 4)
    # ------------------------------------------------------------------
    def run(
        self,
        current_df: pd.DataFrame,
        dataset_key: str,
        pipeline_run_id: str,
    ) -> DriftReport | None:
        """Load-or-create baseline, compute drift, and manage rotation.

        Returns ``None`` on first run (baseline created, nothing to compare
        against), otherwise the computed ``DriftReport``.
        """
        logger = structlog.get_logger()
        baseline = self._load_baseline(dataset_key)

        if baseline is None:
            profile = self._build_profile(current_df, dataset_key)
            self._save_baseline(dataset_key, profile)
            logger.info(
                "baseline_created",
                pipeline_run_id=pipeline_run_id,
                stage="drift_engine",
                dataset_key=dataset_key,
            )
            return None

        report = self.compute_drift(current_df, baseline, pipeline_run_id)

        if report.overall_severity == Severity.HIGH:
            # Counter reset only; baseline stats untouched, no rotation.
            baseline.consecutive_clean_runs = 0
            baseline.updated_at = datetime.now(timezone.utc).isoformat()
            self._save_baseline(dataset_key, baseline)
            return report

        # No HIGH finding — a clean run.
        clean_runs = baseline.consecutive_clean_runs + 1
        if clean_runs >= _ROTATION_THRESHOLD:
            rotated = self._build_profile(current_df, dataset_key, consecutive_clean_runs=0)
            self._save_baseline(dataset_key, rotated)
            logger.info(
                "baseline_rotated",
                pipeline_run_id=pipeline_run_id,
                stage="drift_engine",
                dataset_key=dataset_key,
            )
        else:
            baseline.consecutive_clean_runs = clean_runs
            baseline.updated_at = datetime.now(timezone.utc).isoformat()
            self._save_baseline(dataset_key, baseline)
        return report

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------
    def _schema_drift(
        self, current_df: pd.DataFrame, baseline: BaselineProfile
    ) -> tuple[SchemaDrift, set[str]]:
        base_cols = set(baseline.columns)
        cur_cols = set(current_df.columns)
        columns_added = sorted(cur_cols - base_cols)
        columns_removed = sorted(base_cols - cur_cols)
        dtype_changes: dict[str, str] = {}
        for col in sorted(base_cols & cur_cols):
            base_dtype = baseline.columns[col].dtype
            cur_dtype = str(current_df[col].dtype)
            if base_dtype != cur_dtype:
                dtype_changes[col] = f"was {base_dtype}, now {cur_dtype}"

        flagged = set(columns_added) | set(columns_removed) | set(dtype_changes)
        finding: DriftFinding | None = None
        if flagged:
            finding = DriftFinding(
                check="schema_drift",
                column=None,
                severity=Severity.HIGH,
                actual_value=float(len(flagged)),
                detail=(
                    f"Schema drift: added={columns_added}, removed={columns_removed}, "
                    f"dtype_changes={dtype_changes}"
                ),
            )
        return (
            SchemaDrift(
                columns_added=columns_added,
                columns_removed=columns_removed,
                dtype_changes=dtype_changes,
                finding=finding,
            ),
            flagged,
        )

    def _volume_drift(self, current_df: pd.DataFrame, baseline: BaselineProfile) -> VolumeDrift:
        base_rows = baseline.row_count
        cur_rows = int(current_df.shape[0])
        if base_rows == 0:
            raise DriftComputationError("Baseline row_count is zero; volume drift undefined.")
        pct_change = (cur_rows - base_rows) / base_rows
        severity = _band(
            abs(pct_change), high=_VOLUME_HIGH, medium=_VOLUME_MEDIUM, low=_VOLUME_LOW
        )
        finding: DriftFinding | None = None
        if severity is not None:
            finding = DriftFinding(
                check="volume_drift",
                column=None,
                severity=severity,
                actual_value=pct_change,
                detail=f"Row count {_signed_pct(pct_change)} vs baseline ({base_rows} → {cur_rows})",
            )
        return VolumeDrift(
            current_row_count=cur_rows,
            baseline_row_count=base_rows,
            pct_change=pct_change,
            finding=finding,
        )

    def _numeric_column_drift(
        self, col: str, series: pd.Series, base_stats: ColumnBaselineStats
    ) -> NumericColumnDrift:
        mean_shift = self._mean_median_finding(
            col, "mean_shift", _nan_to_none(series.mean()), base_stats.mean
        )
        median_shift = self._mean_median_finding(
            col, "median_shift", _nan_to_none(series.median()), base_stats.median
        )
        variance_shift = self._variance_finding(col, _nan_to_none(series.std()), base_stats.std)
        return NumericColumnDrift(
            column=col,
            mean_shift=mean_shift,
            median_shift=median_shift,
            variance_shift=variance_shift,
        )

    def _mean_median_finding(
        self, col: str, check: str, current: float | None, baseline: float | None
    ) -> DriftFinding | None:
        if current is None or baseline is None:
            return None
        rel = _rel_change(current, baseline, col=col, check=check)
        severity = _band(
            abs(rel), high=_MEAN_MEDIAN_HIGH, medium=_MEAN_MEDIAN_MEDIUM, low=_MEAN_MEDIAN_LOW
        )
        if severity is None:
            return None
        label = "mean" if check == "mean_shift" else "median"
        return DriftFinding(
            check=check,
            column=col,
            severity=severity,
            actual_value=rel,
            detail=f"{col} {label} {_signed_pct(rel)} vs baseline",
        )

    def _variance_finding(
        self, col: str, current_std: float | None, baseline_std: float | None
    ) -> DriftFinding | None:
        if current_std is None or baseline_std is None:
            return None
        if baseline_std == 0:
            if current_std == 0:
                return None  # both constant — no variance change
            raise DriftComputationError(
                f"Variance-shift ratio undefined for '{col}': baseline std is zero "
                f"while current std is {current_std}."
            )
        ratio = current_std / baseline_std
        if ratio > _VARIANCE_HIGH_HI or ratio < _VARIANCE_HIGH_LO:
            severity: Severity | None = Severity.HIGH
        elif ratio > _VARIANCE_MED_HI or ratio < _VARIANCE_MED_LO:
            severity = Severity.MEDIUM
        else:
            severity = None
        if severity is None:
            return None
        return DriftFinding(
            check="variance_shift",
            column=col,
            severity=severity,
            actual_value=ratio,
            detail=f"{col} std ratio {ratio:.2f} vs baseline (current/baseline)",
        )

    def _categorical_column_drift(
        self, col: str, series: pd.Series, base_stats: ColumnBaselineStats
    ) -> CategoricalColumnDrift:
        base_dist = base_stats.category_distribution or {}
        cur_dist = _category_distribution(series) or {}

        psi_finding = self._psi_finding(col, cur_dist, base_dist)

        base_cats = set(base_dist)
        cur_cats = set(cur_dist)
        new_categories = sorted(cur_cats - base_cats)
        missing_categories = sorted(base_cats - cur_cats)

        category_findings: list[DriftFinding] = []
        for cat in missing_categories:
            repr_pct = base_dist[cat]
            if repr_pct > _MISSING_CATEGORY_HIGH_REPR:
                category_findings.append(
                    DriftFinding(
                        check="missing_category",
                        column=col,
                        severity=Severity.HIGH,
                        actual_value=repr_pct,
                        detail=(
                            f"{col}: category '{cat}' held {repr_pct:.1%} of baseline but is "
                            f"absent now"
                        ),
                    )
                )
        for cat in new_categories:
            repr_pct = cur_dist[cat]
            if repr_pct > _NEW_CATEGORY_MEDIUM_REPR:
                category_findings.append(
                    DriftFinding(
                        check="new_category",
                        column=col,
                        severity=Severity.MEDIUM,
                        actual_value=repr_pct,
                        detail=f"{col}: new category '{cat}' at {repr_pct:.1%} of current",
                    )
                )

        return CategoricalColumnDrift(
            column=col,
            psi=psi_finding,
            new_categories=new_categories,
            missing_categories=missing_categories,
            category_findings=category_findings,
        )

    def _psi_finding(
        self, col: str, cur_dist: dict[str, float], base_dist: dict[str, float]
    ) -> DriftFinding | None:
        categories = set(base_dist) | set(cur_dist)
        if not categories:
            return None
        psi = 0.0
        for cat in categories:
            base_pct = base_dist.get(cat, 0.0)
            cur_pct = cur_dist.get(cat, 0.0)
            base_adj = base_pct if base_pct > 0 else _PSI_EPSILON
            cur_adj = cur_pct if cur_pct > 0 else _PSI_EPSILON
            psi += (cur_adj - base_adj) * math.log(cur_adj / base_adj)
        if psi > _PSI_HIGH:
            severity: Severity | None = Severity.HIGH
        elif psi >= _PSI_MEDIUM:
            severity = Severity.MEDIUM
        else:
            severity = None  # population considered stable below 0.10
        if severity is None:
            return None
        return DriftFinding(
            check="categorical_psi",
            column=col,
            severity=severity,
            actual_value=psi,
            detail=f"{col} PSI {psi:.3f} vs baseline distribution",
        )

    # ------------------------------------------------------------------
    # Rollups
    # ------------------------------------------------------------------
    @staticmethod
    def _max_severity(findings: list[DriftFinding]) -> Severity:
        if not findings:
            return Severity.LOW
        return max((f.severity for f in findings), key=lambda s: _SEVERITY_RANK[s])

    @staticmethod
    def _summarize(findings: list[DriftFinding], overall: Severity) -> str:
        if not findings:
            return "No drift detected against baseline."
        high = sum(1 for f in findings if f.severity == Severity.HIGH)
        medium = sum(1 for f in findings if f.severity == Severity.MEDIUM)
        low = sum(1 for f in findings if f.severity == Severity.LOW)
        return (
            f"{len(findings)} drift finding(s) — {high} HIGH, {medium} MEDIUM, {low} LOW; "
            f"overall {overall.value}."
        )

    @staticmethod
    def _recommendation(finding: DriftFinding) -> str:
        target = finding.column or "dataset"
        return (
            f"Investigate {target} {finding.check.replace('_', ' ')} "
            f"({finding.detail}) before trusting this period's report."
        )


# --- Module-level numeric helpers -----------------------------------------
def _nan_to_none(value: object) -> float | None:
    """Coerce a pandas scalar to ``float``, mapping NaN/None → ``None``."""
    if value is None:
        return None
    try:
        f = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def _category_distribution(series: pd.Series) -> dict[str, float]:
    """Value → proportion of non-null rows (sums to ~1.0), keys stringified."""
    counts = series.value_counts(normalize=True, dropna=True)
    return {str(k): float(v) for k, v in counts.items()}


def _rel_change(current: float, baseline: float, *, col: str, check: str) -> float:
    """Signed relative change ``(current - baseline) / baseline``.

    A zero baseline makes the relative change undefined: return ``0.0`` if the
    current value is also zero (no change), otherwise raise
    ``DriftComputationError`` rather than emit ``inf``.
    """
    if baseline == 0:
        if current == 0:
            return 0.0
        raise DriftComputationError(
            f"{check} for '{col}' undefined: baseline value is zero while current is {current}."
        )
    return (current - baseline) / baseline


def _band(value: float, *, high: float, medium: float, low: float) -> Severity | None:
    """Classify a non-negative magnitude into HIGH/MEDIUM/LOW or ``None``."""
    if value > high:
        return Severity.HIGH
    if value > medium:
        return Severity.MEDIUM
    if value > low:
        return Severity.LOW
    return None


def _signed_pct(fraction: float) -> str:
    return f"{fraction:+.1%}"
