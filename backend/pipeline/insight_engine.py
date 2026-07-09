"""Insight Engine — deterministic statistical computation.

Computes aggregations, trends, segment comparisons, and outlier detection
from a quality-assessed DataFrame. No LLM involvement. All numbers are
deterministically computed from the data.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import structlog

from backend.models.drift_report import DriftReport
from backend.models.insight_payload import (
    AnomalyRecord,
    ColumnSummary,
    InsightPayload,
    Recommendation,
    SegmentComparison,
    TrendAnalysis,
    TrendPoint,
)
from backend.models.quality_report import DataQualityReport, Severity


def _safe_float(val: float | None) -> float | None:
    if val is None:
        return None
    fval = float(val)
    if math.isnan(fval) or math.isinf(fval):
        return None
    return fval


class InsightEngine:
    """Second pipeline stage: deterministic insight computation."""

    def generate_insights(
        self,
        df: pd.DataFrame,
        quality_report: DataQualityReport,
        pipeline_run_id: str,
        drift_report: DriftReport | None = None,
    ) -> InsightPayload:
        logger = structlog.get_logger()
        structlog.contextvars.bind_contextvars(pipeline_run_id=pipeline_run_id)

        logger.info(
            "insight_generation_started",
            stage="insight_engine",
            total_rows=len(df),
            total_columns=len(df.columns),
        )

        column_classes = self._classify_columns(df)

        logger.debug(
            "columns_classified",
            stage="insight_engine",
            numeric=len(column_classes["numeric"]),
            categorical=len(column_classes["categorical"]),
            datetime=len(column_classes["datetime"]),
        )

        summary = self._compute_summary(df, column_classes)
        trends = self._detect_trends(df, column_classes)
        segments = self._compute_segments(df, column_classes)
        anomalies = self._detect_anomalies(df, column_classes)
        recommendations = self._generate_recommendations(
            quality_report, trends, segments, anomalies, column_classes
        )

        key_insights: list[TrendAnalysis | SegmentComparison] = []
        key_insights.extend(trends)
        key_insights.extend(segments)

        metadata = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "numeric_columns": len(column_classes["numeric"]),
            "categorical_columns": len(column_classes["categorical"]),
            "datetime_columns": len(column_classes["datetime"]),
            "has_temporal_data": len(column_classes["datetime"]) > 0,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            "insights_generated",
            stage="insight_engine",
            metrics_count=len(summary),
            anomaly_count=len(anomalies),
            trend_count=len(trends),
            segment_count=len(segments),
        )

        return InsightPayload(
            data_quality_findings=quality_report.model_dump(),
            summary=summary,
            key_insights=key_insights,
            anomalies=anomalies,
            recommendations=recommendations,
            metadata=metadata,
            drift_report=drift_report,
        )

    def _classify_columns(self, df: pd.DataFrame) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {
            "numeric": [],
            "categorical": [],
            "datetime": [],
            "other": [],
        }

        numeric_cols = set(
            str(c) for c in df.select_dtypes(include=[np.number]).columns
        )

        datetime_cols: set[str] = set()
        for col in df.columns:
            col_str = str(col)
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                datetime_cols.add(col_str)
            elif col_str not in numeric_cols:
                try:
                    parsed = pd.to_datetime(df[col], errors="coerce", format="mixed")
                    if parsed.notna().mean() >= 0.8:
                        datetime_cols.add(col_str)
                except (ValueError, TypeError):
                    pass

        for col in df.columns:
            col_str = str(col)
            if col_str in numeric_cols:
                result["numeric"].append(col_str)
            elif col_str in datetime_cols:
                result["datetime"].append(col_str)
            elif pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object:
                if len(df) > 0 and df[col].nunique() < 0.5 * len(df):
                    result["categorical"].append(col_str)
                else:
                    result["other"].append(col_str)
            else:
                result["other"].append(col_str)

        return result

    def _compute_summary(
        self, df: pd.DataFrame, column_classes: dict[str, list[str]]
    ) -> list[ColumnSummary]:
        summaries: list[ColumnSummary] = []
        numeric_set = set(column_classes["numeric"])
        categorical_set = set(column_classes["categorical"])
        datetime_set = set(column_classes["datetime"])

        for col in df.columns:
            col_str = str(col)
            non_null = df[col].dropna()
            count = len(non_null)
            null_count = int(df[col].isna().sum())
            null_pct = round((null_count / len(df)) * 100, 2) if len(df) > 0 else 0.0
            unique_count = int(df[col].nunique())

            if col_str in numeric_set:
                dtype_label = "numeric"
            elif col_str in datetime_set:
                dtype_label = "datetime"
            elif col_str in categorical_set:
                dtype_label = "categorical"
            else:
                dtype_label = "other"

            kwargs: dict = {
                "column_name": col_str,
                "dtype": dtype_label,
                "count": count,
                "null_count": null_count,
                "null_pct": null_pct,
                "unique_count": unique_count,
            }

            if col_str in numeric_set:
                numeric_series = df[col].dropna()
                if len(numeric_series) > 0:
                    kwargs["sum_val"] = _safe_float(float(numeric_series.sum()))
                    kwargs["mean_val"] = _safe_float(float(numeric_series.mean()))
                    kwargs["min_val"] = _safe_float(float(numeric_series.min()))
                    kwargs["max_val"] = _safe_float(float(numeric_series.max()))
                    kwargs["std_val"] = _safe_float(float(numeric_series.std()))
                    kwargs["median_val"] = _safe_float(float(numeric_series.median()))
                    kwargs["q25_val"] = _safe_float(
                        float(numeric_series.quantile(0.25))
                    )
                    kwargs["q75_val"] = _safe_float(
                        float(numeric_series.quantile(0.75))
                    )

                    if len(numeric_series) >= 2:
                        first_val = float(numeric_series.iloc[0])
                        last_val = float(numeric_series.iloc[-1])
                        if first_val != 0:
                            kwargs["growth_rate"] = _safe_float(
                                (last_val - first_val) / abs(first_val)
                            )

            elif col_str in categorical_set:
                vc = df[col].value_counts().head(10)
                total_non_null = count
                top_values: list[dict[str, str | int | float]] = []
                for val, cnt in vc.items():
                    pct = (cnt / total_non_null * 100) if total_non_null > 0 else 0.0
                    top_values.append(
                        {
                            "value": str(val),
                            "count": int(cnt),
                            "pct": round(float(pct), 2),
                        }
                    )
                kwargs["top_values"] = top_values

            summaries.append(ColumnSummary(**kwargs))

        return summaries

    def _detect_trends(
        self, df: pd.DataFrame, column_classes: dict[str, list[str]]
    ) -> list[TrendAnalysis]:
        if not column_classes["datetime"]:
            return []

        numeric_cols = column_classes["numeric"]
        if not numeric_cols:
            return []

        date_col = column_classes["datetime"][0]
        df_work = df.copy()

        if not pd.api.types.is_datetime64_any_dtype(df_work[date_col]):
            df_work[date_col] = pd.to_datetime(df_work[date_col], errors="coerce")

        df_work = df_work.dropna(subset=[date_col])
        if df_work.empty:
            return []

        df_work = df_work.sort_values(date_col)

        date_range_days = (
            df_work[date_col].max() - df_work[date_col].min()
        ).days
        if date_range_days <= 90:
            freq = "D"
        elif date_range_days <= 730:
            freq = "W"
        else:
            freq = "MS"

        trends: list[TrendAnalysis] = []

        for num_col in numeric_cols:
            try:
                grouped = (
                    df_work.set_index(date_col)[[num_col]]
                    .resample(freq)
                    .mean()
                    .dropna()
                )
            except (KeyError, ValueError):
                continue

            if grouped.empty or len(grouped) < 2:
                continue

            values = grouped[num_col].tolist()
            periods = grouped.index.tolist()
            trend_points: list[TrendPoint] = []

            for i, (period, value) in enumerate(zip(periods, values)):
                change_pct = None
                if i > 0 and values[i - 1] != 0:
                    change_pct = _safe_float(
                        ((value - values[i - 1]) / abs(values[i - 1])) * 100
                    )
                period_str = (
                    period.isoformat()
                    if hasattr(period, "isoformat")
                    else str(period)
                )
                trend_points.append(
                    TrendPoint(
                        period=period_str,
                        value=_safe_float(float(value)) or 0.0,
                        change_pct=change_pct,
                    )
                )

            if len(trend_points) > 100:
                trend_points = trend_points[:100]

            changes = [
                tp.change_pct for tp in trend_points if tp.change_pct is not None
            ]
            direction = self._determine_trend_direction(changes)

            first_val = values[0]
            last_val = values[-1]
            overall_change: float | None = None
            if first_val != 0:
                overall_change = _safe_float(
                    ((last_val - first_val) / abs(first_val)) * 100
                )

            if overall_change is not None:
                note = (
                    f"{num_col} shows a {direction} trend "
                    f"with {overall_change:.1f}% change over the period"
                )
            else:
                note = f"{num_col} shows a {direction} trend over the period"

            trends.append(
                TrendAnalysis(
                    metric_column=num_col,
                    date_column=date_col,
                    trend_direction=direction,
                    trend_points=trend_points,
                    overall_change_pct=overall_change,
                    note=note,
                )
            )

        return trends

    def _determine_trend_direction(self, changes: list[float]) -> str:
        if not changes:
            return "stable"

        positive_pct = sum(1 for c in changes if c > 0) / len(changes)
        negative_pct = sum(1 for c in changes if c < 0) / len(changes)

        if positive_pct >= 0.7:
            return "increasing"
        if negative_pct >= 0.7:
            return "decreasing"

        abs_changes = [abs(c) for c in changes]
        mean_abs = sum(abs_changes) / len(abs_changes)
        if len(changes) > 1:
            mean_val = sum(changes) / len(changes)
            variance = sum((c - mean_val) ** 2 for c in changes) / len(changes)
            std_changes = variance**0.5
            if mean_abs > 0 and std_changes > mean_abs:
                return "volatile"

        return "stable"

    def _compute_segments(
        self, df: pd.DataFrame, column_classes: dict[str, list[str]]
    ) -> list[SegmentComparison]:
        if not column_classes["categorical"]:
            return []

        numeric_cols = column_classes["numeric"]
        if not numeric_cols:
            return []

        cat_cols = sorted(
            column_classes["categorical"],
            key=lambda c: df[c].nunique(),
        )[:3]

        def _col_std(c: str) -> float:
            if pd.api.types.is_numeric_dtype(df[c]):
                s = df[c].std()
                if s == s:  # not NaN
                    return float(s)
            return 0.0

        num_cols_sorted = sorted(numeric_cols, key=_col_std, reverse=True)[:5]

        segments: list[SegmentComparison] = []

        for cat_col in cat_cols:
            for num_col in num_cols_sorted:
                try:
                    grouped = df.groupby(cat_col)[num_col].agg(
                        ["mean", "sum", "count"]
                    )
                except (KeyError, ValueError, TypeError):
                    continue

                grouped = grouped.nlargest(20, "count")

                total_sum = float(grouped["sum"].sum())
                segment_list: list[dict[str, float | int | str]] = []
                for seg_name, row in grouped.iterrows():
                    segment_list.append(
                        {
                            "segment": str(seg_name),
                            "mean": _safe_float(float(row["mean"])) or 0.0,
                            "sum": _safe_float(float(row["sum"])) or 0.0,
                            "count": int(row["count"]),
                        }
                    )

                if segment_list and total_sum != 0:
                    top_by_mean = max(
                        segment_list, key=lambda s: float(s.get("mean", 0))
                    )
                    top_pct = (float(top_by_mean["sum"]) / abs(total_sum)) * 100
                    note = (
                        f"{cat_col} '{top_by_mean['segment']}' has the highest "
                        f"average {num_col} at {top_by_mean['mean']:.2f} "
                        f"({top_pct:.0f}% of total)"
                    )
                else:
                    note = f"Segment comparison of {num_col} by {cat_col}"

                segments.append(
                    SegmentComparison(
                        segment_column=cat_col,
                        metric_column=num_col,
                        segments=segment_list,
                        note=note,
                    )
                )

        return segments

    def _detect_anomalies(
        self, df: pd.DataFrame, column_classes: dict[str, list[str]]
    ) -> list[AnomalyRecord]:
        anomalies: list[AnomalyRecord] = []

        for col in column_classes["numeric"]:
            numeric_full = pd.to_numeric(df[col], errors="coerce")
            numeric = numeric_full.dropna()

            if len(numeric) < 10:
                continue

            std = float(numeric.std())
            if std == 0:
                continue

            mean = float(numeric.mean())
            mask = (numeric - mean).abs() > 2 * std
            outlier_indices = numeric[mask].index.tolist()
            outlier_values = numeric[mask].tolist()
            full_mask = ((numeric_full - mean).abs() > 2 * std).fillna(False)
            outlier_positions = [
                int(pos)
                for pos, is_outlier in enumerate(full_mask.tolist())
                if is_outlier
            ]

            if not outlier_indices:
                continue

            count = len(outlier_indices)
            pct = (count / len(numeric)) * 100

            above = sum(1 for v in outlier_values if v > mean)
            below = sum(1 for v in outlier_values if v < mean)
            if above > 0 and below > 0:
                direction = "both"
            elif above > 0:
                direction = "above"
            else:
                direction = "below"

            anomalies.append(
                AnomalyRecord(
                    column_name=col,
                    row_indices=outlier_positions[:20],
                    values=[
                        _safe_float(float(v)) or 0.0 for v in outlier_values[:20]
                    ],
                    mean=_safe_float(mean) or 0.0,
                    std=_safe_float(std) or 0.0,
                    threshold_sigma=2.0,
                    count=count,
                    pct=_safe_float(round(pct, 2)) or 0.0,
                    direction=direction,
                )
            )

        return anomalies

    def _generate_recommendations(
        self,
        quality_report: DataQualityReport,
        trends: list[TrendAnalysis],
        segments: list[SegmentComparison],
        anomalies: list[AnomalyRecord],
        column_classes: dict[str, list[str]],
    ) -> list[Recommendation]:
        recs: list[Recommendation] = []

        if quality_report.has_critical_issues:
            recs.append(
                Recommendation(
                    category="data_quality",
                    priority="high",
                    message="Critical data quality issues detected — address before relying on insights",
                    related_columns=[],
                )
            )

        for defect in quality_report.defects:
            if defect.severity == Severity.HIGH:
                recs.append(
                    Recommendation(
                        category="data_quality",
                        priority="medium",
                        message=f"High-severity issue in {', '.join(defect.affected_columns)}: {defect.details}",
                        related_columns=defect.affected_columns,
                    )
                )

        for trend in trends:
            if (
                trend.trend_direction == "decreasing"
                and trend.overall_change_pct is not None
                and trend.overall_change_pct < -20
            ):
                recs.append(
                    Recommendation(
                        category="trend",
                        priority="high",
                        message=(
                            f"Significant decline in {trend.metric_column}: "
                            f"{trend.overall_change_pct:.1f}% change over the period"
                        ),
                        related_columns=[trend.metric_column],
                    )
                )
            elif trend.trend_direction == "volatile":
                recs.append(
                    Recommendation(
                        category="trend",
                        priority="medium",
                        message=f"High volatility detected in {trend.metric_column} — investigate potential instability",
                        related_columns=[trend.metric_column],
                    )
                )

        for anomaly in anomalies:
            if anomaly.pct > 5:
                recs.append(
                    Recommendation(
                        category="anomaly",
                        priority="high",
                        message=f"{anomaly.pct:.1f}% of values in {anomaly.column_name} are outliers — review for data errors",
                        related_columns=[anomaly.column_name],
                    )
                )
            else:
                recs.append(
                    Recommendation(
                        category="anomaly",
                        priority="low",
                        message=f"Minor outliers detected in {anomaly.column_name} ({anomaly.count} values beyond 2σ)",
                        related_columns=[anomaly.column_name],
                    )
                )

        for seg in segments:
            if seg.segments:
                total_sum = sum(float(s.get("sum", 0)) for s in seg.segments)
                if total_sum > 0:
                    top_sum = float(seg.segments[0].get("sum", 0))
                    if top_sum / total_sum > 0.5:
                        recs.append(
                            Recommendation(
                                category="segment",
                                priority="medium",
                                message=(
                                    f"Concentration risk: '{seg.segments[0].get('segment', '')}' "
                                    f"accounts for >{int(top_sum / total_sum * 100)}% of {seg.metric_column}"
                                ),
                                related_columns=[
                                    seg.segment_column,
                                    seg.metric_column,
                                ],
                            )
                        )

        if not column_classes["datetime"]:
            recs.append(
                Recommendation(
                    category="general",
                    priority="low",
                    message="No temporal data detected — consider adding date columns for trend analysis",
                    related_columns=[],
                )
            )

        if not column_classes["categorical"]:
            recs.append(
                Recommendation(
                    category="general",
                    priority="low",
                    message="No categorical columns detected — consider adding segmentation dimensions for comparative analysis",
                    related_columns=[],
                )
            )

        return recs
