"""Data Quality Assessment Engine.

Scans a DataFrame across six detection categories and produces a
severity-classified :class:`DataQualityReport`. The only public method
is :meth:`DataQualityAssessor.assess_quality`.
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pandera as pa
import structlog

from backend.errors.exceptions import ConfigurationError
from backend.models.pipeline_result import PipelineResult
from backend.models.quality_report import (
    ColumnProfile,
    DataQualityDefect,
    DataQualityReport,
    DefectCategory,
    Severity,
)

_NON_NEGATIVE_KEYWORDS = ("revenue", "quantity", "count", "price", "amount", "volume")

_SEVERITY_WEIGHTS = {
    Severity.CRITICAL: 30,
    Severity.HIGH: 15,
    Severity.MEDIUM: 5,
    Severity.LOW: 2,
}


def _safe_float(val: float | None) -> float | None:
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return float(val)


def _implies_non_negative(column_name: str) -> bool:
    lower = column_name.lower()
    return any(kw in lower for kw in _NON_NEGATIVE_KEYWORDS)


class DataQualityAssessor:
    """Gatekeeper between raw CSV input and downstream pipeline stages."""

    def _validate_input(self, df: pd.DataFrame) -> None:
        if not isinstance(df, pd.DataFrame):
            raise ConfigurationError(
                f"Expected a pandas DataFrame, got {type(df).__name__}"
            )
        if df.empty or df.shape[1] == 0:
            raise ConfigurationError("DataFrame is empty — no rows to assess")

        columns: dict[str, pa.Column] = {}
        for col in df.columns:
            columns[str(col)] = pa.Column(nullable=True)
        schema = pa.DataFrameSchema(columns=columns, coerce=False)
        try:
            schema.validate(df, lazy=True)
        except pa.errors.SchemaErrors as exc:
            violations = "; ".join(
                str(err) for err in exc.schema_errors
            )
            raise ConfigurationError(
                f"Pandera schema validation failed: {violations}"
            ) from exc

    # ------------------------------------------------------------------
    # Six detection checks
    # ------------------------------------------------------------------

    def _check_structural_integrity(
        self, df: pd.DataFrame
    ) -> list[DataQualityDefect]:
        defects: list[DataQualityDefect] = []
        total_rows = len(df)

        for col in df.columns:
            col_str = str(col)

            # Mixed types within a column
            if df[col].dtype == object:
                non_null = df[col].dropna()
                if len(non_null) > 0:
                    types = non_null.apply(type).unique()
                    if len(types) > 1:
                        dominant_type = non_null.apply(type).value_counts().index[0]
                        mixed_count = int(
                            (non_null.apply(type) != dominant_type).sum()
                        )
                        mixed_pct = (mixed_count / total_rows) * 100
                        severity = (
                            Severity.HIGH if mixed_pct >= 20 else Severity.MEDIUM
                        )
                        defects.append(
                            DataQualityDefect(
                                defect_type="mixed_types",
                                category=DefectCategory.STRUCTURAL_INTEGRITY,
                                severity=severity,
                                affected_columns=[col_str],
                                count=mixed_count,
                                percentage=round(mixed_pct, 2),
                                details=f"{mixed_pct:.1f}% of values in '{col_str}' have inconsistent types",
                                recommended_action="Standardize column to a single data type",
                            )
                        )

            # Column naming issues
            if col_str.strip() == "" or col_str.isdigit() or re.search(
                r"[^a-zA-Z0-9_ ]", col_str
            ):
                defects.append(
                    DataQualityDefect(
                        defect_type="column_naming",
                        category=DefectCategory.STRUCTURAL_INTEGRITY,
                        severity=Severity.MEDIUM,
                        affected_columns=[col_str],
                        count=total_rows,
                        percentage=100.0,
                        details=f"Column name '{col_str}' is empty, purely numeric, or contains special characters",
                        recommended_action="Rename column to a descriptive alphanumeric name",
                    )
                )

        return defects

    def _check_completeness(
        self, df: pd.DataFrame
    ) -> list[DataQualityDefect]:
        defects: list[DataQualityDefect] = []
        total_rows = len(df)

        for col in df.columns:
            null_count = int(df[col].isna().sum())
            if null_count == 0:
                continue
            null_pct = (null_count / total_rows) * 100

            if null_pct == 100.0:
                severity = Severity.CRITICAL
            elif null_pct >= 50:
                severity = Severity.CRITICAL
            elif null_pct >= 20:
                severity = Severity.HIGH
            elif null_pct >= 5:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW

            defects.append(
                DataQualityDefect(
                    defect_type="null_values",
                    category=DefectCategory.COMPLETENESS,
                    severity=severity,
                    affected_columns=[str(col)],
                    count=null_count,
                    percentage=round(null_pct, 2),
                    details=f"{null_pct:.1f}% null values in column '{col}'",
                    recommended_action="Impute missing values or investigate data source",
                )
            )

        return defects

    def _check_consistency(
        self, df: pd.DataFrame
    ) -> list[DataQualityDefect]:
        defects: list[DataQualityDefect] = []
        total_rows = len(df)

        for col in df.columns:
            col_str = str(col)

            # Negative values in non-negativity-implied columns
            if _implies_non_negative(col_str):
                numeric = pd.to_numeric(df[col], errors="coerce")
                neg_count = int((numeric < 0).sum())
                if neg_count > 0:
                    neg_pct = (neg_count / total_rows) * 100
                    defects.append(
                        DataQualityDefect(
                            defect_type="negative_values",
                            category=DefectCategory.CONSISTENCY,
                            severity=Severity.HIGH,
                            affected_columns=[col_str],
                            count=neg_count,
                            percentage=round(neg_pct, 2),
                            details=f"{neg_count} negative value(s) in '{col_str}' which implies non-negativity",
                            recommended_action="Verify negative values are intentional or correct data entry errors",
                        )
                    )

            # Mixed casing in string columns
            if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object:
                str_vals = df[col].dropna().astype(str)
                if len(str_vals) > 0:
                    lower_unique = str_vals.str.lower().nunique()
                    actual_unique = str_vals.nunique()
                    if lower_unique < actual_unique:
                        diff_count = actual_unique - lower_unique
                        defects.append(
                            DataQualityDefect(
                                defect_type="case_inconsistency",
                                category=DefectCategory.CONSISTENCY,
                                severity=Severity.LOW,
                                affected_columns=[col_str],
                                count=diff_count,
                                percentage=round(
                                    (diff_count / total_rows) * 100, 2
                                ),
                                details=f"Mixed casing patterns in '{col_str}' ({actual_unique} unique vs {lower_unique} case-insensitive unique)",
                                recommended_action="Normalize string casing for consistency",
                            )
                        )

        return defects

    def _check_uniqueness(
        self, df: pd.DataFrame
    ) -> list[DataQualityDefect]:
        defects: list[DataQualityDefect] = []
        total_rows = len(df)
        if total_rows == 0:
            return defects

        dup_count = int(df.duplicated().sum())
        if dup_count == 0:
            return defects

        dup_pct = (dup_count / total_rows) * 100

        if dup_pct >= 80:
            severity = Severity.CRITICAL
        elif dup_pct >= 20:
            severity = Severity.HIGH
        elif dup_pct >= 5:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        defects.append(
            DataQualityDefect(
                defect_type="duplicate_rows",
                category=DefectCategory.UNIQUENESS,
                severity=severity,
                affected_columns=list(df.columns.astype(str)),
                count=dup_count,
                percentage=round(dup_pct, 2),
                details=f"{dup_pct:.1f}% of rows are exact duplicates ({dup_count}/{total_rows})",
                recommended_action="Deduplicate rows or investigate data ingestion",
            )
        )
        return defects

    def _check_statistical_red_flags(
        self, df: pd.DataFrame
    ) -> list[DataQualityDefect]:
        defects: list[DataQualityDefect] = []
        total_rows = len(df)

        for col in df.columns:
            col_str = str(col)
            numeric = pd.to_numeric(df[col], errors="coerce")
            non_null_numeric = numeric.dropna()

            if len(non_null_numeric) == 0:
                continue

            # Zero variance
            std_val = non_null_numeric.std()
            if std_val == 0 or non_null_numeric.nunique() == 1:
                defects.append(
                    DataQualityDefect(
                        defect_type="zero_variance",
                        category=DefectCategory.STATISTICAL_RED_FLAG,
                        severity=Severity.HIGH,
                        affected_columns=[col_str],
                        count=len(non_null_numeric),
                        percentage=100.0,
                        details=f"Column '{col_str}' has zero variance (all values identical)",
                        recommended_action="Investigate if column is a dead data feed or misconfigured",
                    )
                )

            # Extreme outliers (beyond 5 standard deviations)
            if std_val is not None and std_val > 0:
                mean_val = non_null_numeric.mean()
                outlier_mask = (non_null_numeric - mean_val).abs() > 5 * std_val
                outlier_count = int(outlier_mask.sum())
                if outlier_count > 0:
                    outlier_pct = (outlier_count / total_rows) * 100
                    defects.append(
                        DataQualityDefect(
                            defect_type="extreme_outliers",
                            category=DefectCategory.STATISTICAL_RED_FLAG,
                            severity=Severity.MEDIUM,
                            affected_columns=[col_str],
                            count=outlier_count,
                            percentage=round(outlier_pct, 2),
                            details=f"{outlier_count} value(s) in '{col_str}' beyond 5 standard deviations from the mean",
                            recommended_action="Review outlier values for data entry errors or legitimate extremes",
                        )
                    )

            # Inf values
            if pd.api.types.is_numeric_dtype(df[col]):
                inf_mask = np.isinf(df[col].to_numpy(dtype=float, na_value=0.0))
                inf_count = int(inf_mask.sum())
                if inf_count > 0:
                    inf_pct = (inf_count / total_rows) * 100
                    defects.append(
                        DataQualityDefect(
                            defect_type="infinite_values",
                            category=DefectCategory.STATISTICAL_RED_FLAG,
                            severity=Severity.HIGH,
                            affected_columns=[col_str],
                            count=inf_count,
                            percentage=round(inf_pct, 2),
                            details=f"{inf_count} infinite value(s) in column '{col_str}'",
                            recommended_action="Replace Inf values with NaN or investigate data source",
                        )
                    )

            # Extreme cardinality (string column where unique count = row count)
            if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object:
                str_non_null = df[col].dropna()
                if len(str_non_null) > 0 and str_non_null.nunique() == len(str_non_null):
                    defects.append(
                        DataQualityDefect(
                            defect_type="extreme_cardinality",
                            category=DefectCategory.STATISTICAL_RED_FLAG,
                            severity=Severity.MEDIUM,
                            affected_columns=[col_str],
                            count=len(str_non_null),
                            percentage=100.0,
                            details=f"String column '{col_str}' has unique count equal to row count — likely an ID or free-text column",
                            recommended_action="Verify column is not being misused as a categorical field",
                        )
                    )

        return defects

    def _check_referential_integrity(
        self, df: pd.DataFrame
    ) -> list[DataQualityDefect]:
        # Cross-table foreign key checks require multiple tables and are
        # deferred to Phase 3 (database layer). This method checks
        # cross-column coherence within a single DataFrame.
        defects: list[DataQualityDefect] = []
        total_rows = len(df)

        id_columns: list[str] = []
        numeric_columns: list[str] = []

        for col in df.columns:
            col_str = str(col)

            # Non-unique ID column
            if col_str.endswith("_id") or col_str == "id":
                id_columns.append(col_str)
                non_null = df[col].dropna()
                if len(non_null) > 0 and non_null.nunique() < len(non_null):
                    dup_count = len(non_null) - non_null.nunique()
                    dup_pct = (dup_count / total_rows) * 100
                    defects.append(
                        DataQualityDefect(
                            defect_type="non_unique_id",
                            category=DefectCategory.REFERENTIAL_INTEGRITY,
                            severity=Severity.HIGH,
                            affected_columns=[col_str],
                            count=dup_count,
                            percentage=round(dup_pct, 2),
                            details=f"ID column '{col_str}' contains {dup_count} duplicate value(s)",
                            recommended_action="Ensure ID column values are unique or review data relationships",
                        )
                    )

            # Collect numeric columns for correlation check
            if pd.api.types.is_numeric_dtype(df[col]):
                numeric_columns.append(col_str)

        # Duplicate measurement check (correlation > 0.99)
        if len(numeric_columns) >= 2:
            for i, col_a in enumerate(numeric_columns):
                for col_b in numeric_columns[i + 1 :]:
                    try:
                        corr = df[col_a].corr(df[col_b])
                        if corr is not None and abs(corr) > 0.99:
                            defects.append(
                                DataQualityDefect(
                                    defect_type="duplicate_measurement",
                                    category=DefectCategory.REFERENTIAL_INTEGRITY,
                                    severity=Severity.LOW,
                                    affected_columns=[col_a, col_b],
                                    count=total_rows,
                                    percentage=100.0,
                                    details=f"Columns '{col_a}' and '{col_b}' have Pearson correlation > 0.99 — potential duplicate measurement",
                                    recommended_action="Verify if both columns are needed or if one is derived from the other",
                                )
                            )
                    except (ValueError, TypeError):
                        pass

        return defects

    # ------------------------------------------------------------------
    # Column profiling
    # ------------------------------------------------------------------

    def _build_column_profiles(
        self, df: pd.DataFrame
    ) -> dict[str, ColumnProfile]:
        profiles: dict[str, ColumnProfile] = {}
        total_rows = len(df)

        for col in df.columns:
            col_str = str(col)
            null_count = int(df[col].isna().sum())
            unique_count = int(df[col].nunique())

            # Detect mixed types
            non_null = df[col].dropna()
            has_mixed = False
            if df[col].dtype == object and len(non_null) > 0:
                types = non_null.apply(type).unique()
                has_mixed = len(types) > 1

            min_v = max_v = mean_v = std_v = None
            if pd.api.types.is_numeric_dtype(df[col]):
                min_v = _safe_float(float(df[col].min()))
                max_v = _safe_float(float(df[col].max()))
                mean_v = _safe_float(float(df[col].mean()))
                std_v = _safe_float(float(df[col].std()))

            profiles[col_str] = ColumnProfile(
                column_name=col_str,
                dtype=str(df[col].dtype),
                null_count=null_count,
                null_pct=round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0.0,
                unique_count=unique_count,
                unique_pct=round((unique_count / total_rows) * 100, 2) if total_rows > 0 else 0.0,
                has_mixed_types=has_mixed,
                min_val=min_v,
                max_val=max_v,
                mean_val=mean_v,
                std_val=std_v,
            )

        return profiles

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assess_quality(
        self, df: pd.DataFrame, pipeline_run_id: str
    ) -> PipelineResult:
        """Run all quality checks and return a PipelineResult."""
        logger = structlog.get_logger()
        structlog.contextvars.bind_contextvars(pipeline_run_id=pipeline_run_id)

        self._validate_input(df)

        all_defects: list[DataQualityDefect] = []
        all_defects.extend(self._check_structural_integrity(df))
        all_defects.extend(self._check_completeness(df))
        all_defects.extend(self._check_consistency(df))
        all_defects.extend(self._check_uniqueness(df))
        all_defects.extend(self._check_statistical_red_flags(df))
        all_defects.extend(self._check_referential_integrity(df))

        # Overall severity
        if not all_defects:
            overall_severity = Severity.LOW
        else:
            severity_order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]
            overall_severity = Severity.LOW
            for sev in severity_order:
                if any(d.severity == sev for d in all_defects):
                    overall_severity = sev
                    break

        has_critical = overall_severity == Severity.CRITICAL
        critical_defects = [d for d in all_defects if d.severity == Severity.CRITICAL]

        halt_reason: str | None = None
        if has_critical:
            halt_reason = f"Critical findings: {'; '.join(d.details for d in critical_defects)}"

        # Quality score
        score = 100.0
        for d in all_defects:
            score -= _SEVERITY_WEIGHTS[d.severity]
        score = max(score, 0.0)

        report = DataQualityReport(
            overall_severity=overall_severity,
            has_critical_issues=has_critical,
            halt_reason=halt_reason,
            defects=all_defects,
            column_profiles=self._build_column_profiles(df),
            total_rows=df.shape[0],
            total_columns=df.shape[1],
            overall_quality_score=score,
            assessed_at=datetime.now(timezone.utc).isoformat(),
        )

        if has_critical:
            for cd in critical_defects:
                logger.warning(
                    "critical_defect_detected",
                    stage="data_quality",
                    defect_type=cd.defect_type,
                    column=cd.affected_columns,
                    percentage=cd.percentage,
                )
            logger.warning(
                "pipeline_halted",
                stage="data_quality",
                halt_reason=report.halt_reason,
                defect_count=len(critical_defects),
            )
            return PipelineResult(
                success=False,
                halted=True,
                halt_reason=report.halt_reason,
                quality_report=report,
            )

        logger.info(
            "quality_assessed",
            stage="data_quality",
            total_rows=df.shape[0],
            defect_count=len(report.defects),
            overall_severity=report.overall_severity.value,
        )
        return PipelineResult(
            success=True,
            halted=False,
            quality_report=report,
        )
