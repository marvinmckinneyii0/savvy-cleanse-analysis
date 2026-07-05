"""Tests for the Insight Engine (Story 1.3).

Covers test groups 10a–10j from the story spec: full dataset, numeric-only,
outlier detection, edge cases, graceful degradation, report forwarding,
growth rate edge cases, structlog output, and serialization.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
import structlog

from backend.core.logging import configure_logging
from backend.models.insight_payload import (
    AnomalyRecord,
    ColumnSummary,
    InsightPayload,
    Recommendation,
    SegmentComparison,
    TrendAnalysis,
)
from backend.models.quality_report import (
    DataQualityDefect,
    DataQualityReport,
    DefectCategory,
    Severity,
)
from backend.pipeline.insight_engine import InsightEngine


# ---------------------------------------------------------------------------
# Local fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def clean_quality_report() -> DataQualityReport:
    return DataQualityReport(
        overall_severity=Severity.LOW,
        has_critical_issues=False,
        halt_reason=None,
        defects=[],
        column_profiles={},
        total_rows=100,
        total_columns=4,
        overall_quality_score=100.0,
        assessed_at="2026-01-01T00:00:00Z",
    )


@pytest.fixture
def full_sales_df() -> pd.DataFrame:
    rng = np.random.default_rng(seed=42)
    n = 200
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    regions = rng.choice(["North", "South", "East", "West"], size=n)
    categories = rng.choice(["Electronics", "Clothing", "Food"], size=n)
    revenue = rng.normal(500, 100, size=n).clip(0).round(2)
    quantity = rng.integers(1, 50, size=n)
    return pd.DataFrame(
        {
            "date": dates,
            "region": regions.astype(object),
            "category": categories.astype(object),
            "revenue": revenue,
            "quantity": quantity.astype(float),
        }
    )


@pytest.fixture
def numeric_only_df() -> pd.DataFrame:
    rng = np.random.default_rng(seed=42)
    n = 100
    return pd.DataFrame(
        {
            "col_a": rng.normal(100, 10, size=n).round(2),
            "col_b": rng.normal(50, 5, size=n).round(2),
        }
    )


@pytest.fixture
def outlier_df() -> pd.DataFrame:
    values = [100.0] * 98 + [500.0, 600.0]
    return pd.DataFrame(
        {
            "metric": values,
            "label": (["A"] * 50 + ["B"] * 50),
        }
    )


@pytest.fixture
def numeric_date_df() -> pd.DataFrame:
    rng = np.random.default_rng(seed=42)
    n = 100
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "metric_a": rng.normal(100, 10, size=n).round(2),
            "metric_b": (rng.normal(100, 10, size=n) * 2).round(2),
        }
    )


@pytest.fixture
def engine() -> InsightEngine:
    return InsightEngine()


# ---------------------------------------------------------------------------
# 10a — Full dataset (date + categories + numerics)
# ---------------------------------------------------------------------------


class TestFullDataset:
    def test_full_dataset_all_sections_populated(
        self,
        engine: InsightEngine,
        full_sales_df: pd.DataFrame,
        clean_quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> None:
        result = engine.generate_insights(
            full_sales_df, clean_quality_report, pipeline_run_id=pipeline_run_id
        )

        assert isinstance(result, InsightPayload)
        assert len(result.summary) == 5
        assert result.metadata["has_temporal_data"] is True
        assert any(isinstance(i, TrendAnalysis) for i in result.key_insights)
        assert any(isinstance(i, SegmentComparison) for i in result.key_insights)
        assert isinstance(result.data_quality_findings, dict)

    def test_trends_computed_for_numeric_columns(
        self,
        engine: InsightEngine,
        full_sales_df: pd.DataFrame,
        clean_quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> None:
        result = engine.generate_insights(
            full_sales_df, clean_quality_report, pipeline_run_id=pipeline_run_id
        )

        trend_metrics = {
            i.metric_column
            for i in result.key_insights
            if isinstance(i, TrendAnalysis)
        }
        assert "revenue" in trend_metrics
        assert "quantity" in trend_metrics

    def test_summary_length_matches_columns(
        self,
        engine: InsightEngine,
        full_sales_df: pd.DataFrame,
        clean_quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> None:
        result = engine.generate_insights(
            full_sales_df, clean_quality_report, pipeline_run_id=pipeline_run_id
        )

        assert len(result.summary) == len(full_sales_df.columns)


# ---------------------------------------------------------------------------
# 10b — Numeric-only dataset (no date, no categories)
# ---------------------------------------------------------------------------


class TestNumericOnly:
    def test_numeric_only_no_trends_no_segments(
        self,
        engine: InsightEngine,
        numeric_only_df: pd.DataFrame,
        clean_quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> None:
        result = engine.generate_insights(
            numeric_only_df, clean_quality_report, pipeline_run_id=pipeline_run_id
        )

        assert result.metadata["has_temporal_data"] is False
        assert not any(isinstance(i, TrendAnalysis) for i in result.key_insights)
        assert not any(
            isinstance(i, SegmentComparison) for i in result.key_insights
        )

    def test_numeric_only_summary_populated(
        self,
        engine: InsightEngine,
        numeric_only_df: pd.DataFrame,
        clean_quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> None:
        result = engine.generate_insights(
            numeric_only_df, clean_quality_report, pipeline_run_id=pipeline_run_id
        )

        for s in result.summary:
            assert s.dtype == "numeric"
            assert s.mean_val is not None
            assert s.std_val is not None

    def test_numeric_only_recommends_temporal_data(
        self,
        engine: InsightEngine,
        numeric_only_df: pd.DataFrame,
        clean_quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> None:
        result = engine.generate_insights(
            numeric_only_df, clean_quality_report, pipeline_run_id=pipeline_run_id
        )

        general_recs = [r for r in result.recommendations if r.category == "general"]
        temporal_rec = [r for r in general_recs if "temporal" in r.message.lower()]
        assert len(temporal_rec) >= 1


# ---------------------------------------------------------------------------
# 10c — Dataset with outliers
# ---------------------------------------------------------------------------


class TestOutlierDetection:
    def test_outlier_detection_beyond_2_sigma(
        self,
        engine: InsightEngine,
        outlier_df: pd.DataFrame,
        clean_quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> None:
        result = engine.generate_insights(
            outlier_df, clean_quality_report, pipeline_run_id=pipeline_run_id
        )

        metric_anomalies = [a for a in result.anomalies if a.column_name == "metric"]
        assert len(metric_anomalies) == 1

        anomaly = metric_anomalies[0]
        assert anomaly.threshold_sigma == 2.0
        assert 500.0 in anomaly.values
        assert 600.0 in anomaly.values
        assert anomaly.direction == "above"
        assert anomaly.count == 2

    def test_outlier_detection_handles_non_integer_index(
        self,
        engine: InsightEngine,
        outlier_df: pd.DataFrame,
        clean_quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> None:
        df = outlier_df.copy()
        df.index = [f"row-{i}" for i in range(len(df))]

        result = engine.generate_insights(
            df, clean_quality_report, pipeline_run_id=pipeline_run_id
        )

        anomaly = next(a for a in result.anomalies if a.column_name == "metric")
        assert anomaly.row_indices == [98, 99]
        assert anomaly.values == [500.0, 600.0]


# ---------------------------------------------------------------------------
# 10d — Empty/minimal dataset edge cases
# ---------------------------------------------------------------------------


class TestMinimalDataset:
    def test_minimal_dataset_single_row(
        self,
        engine: InsightEngine,
        clean_quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> None:
        df = pd.DataFrame({"value": [42.0], "name": ["test"]})
        result = engine.generate_insights(
            df, clean_quality_report, pipeline_run_id=pipeline_run_id
        )

        assert isinstance(result, InsightPayload)
        numeric_summaries = [s for s in result.summary if s.dtype == "numeric"]
        for s in numeric_summaries:
            assert s.growth_rate is None

        assert not any(isinstance(i, TrendAnalysis) for i in result.key_insights)

    def test_minimal_dataset_two_columns(
        self,
        engine: InsightEngine,
        clean_quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> None:
        df = pd.DataFrame(
            {
                "amount": [10.0, 20.0, 30.0, 40.0, 50.0],
                "type": ["A", "B", "A", "B", "A"],
            }
        )
        result = engine.generate_insights(
            df, clean_quality_report, pipeline_run_id=pipeline_run_id
        )

        assert len(result.summary) == 2
        numeric_summaries = [s for s in result.summary if s.dtype == "numeric"]
        assert len(numeric_summaries) == 1
        assert numeric_summaries[0].mean_val is not None


# ---------------------------------------------------------------------------
# 10e — No date column graceful handling
# ---------------------------------------------------------------------------


class TestNoDateColumn:
    def test_no_date_column_trends_empty(
        self,
        engine: InsightEngine,
        numeric_only_df: pd.DataFrame,
        clean_quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> None:
        result = engine.generate_insights(
            numeric_only_df, clean_quality_report, pipeline_run_id=pipeline_run_id
        )

        trend_insights = [
            i for i in result.key_insights if isinstance(i, TrendAnalysis)
        ]
        assert len(trend_insights) == 0
        assert result.metadata["has_temporal_data"] is False


# ---------------------------------------------------------------------------
# 10f — No categorical columns graceful handling
# ---------------------------------------------------------------------------


class TestNoCategoricalColumns:
    def test_no_categorical_columns_segments_empty(
        self,
        engine: InsightEngine,
        numeric_date_df: pd.DataFrame,
        clean_quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> None:
        result = engine.generate_insights(
            numeric_date_df, clean_quality_report, pipeline_run_id=pipeline_run_id
        )

        segment_insights = [
            i for i in result.key_insights if isinstance(i, SegmentComparison)
        ]
        assert len(segment_insights) == 0


# ---------------------------------------------------------------------------
# 10g — Data quality report forwarding
# ---------------------------------------------------------------------------


class TestQualityReportForwarding:
    def test_quality_report_forwarded(
        self,
        engine: InsightEngine,
        clean_quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> None:
        df = pd.DataFrame({"x": [1.0, 2.0, 3.0]})
        result = engine.generate_insights(
            df, clean_quality_report, pipeline_run_id=pipeline_run_id
        )

        expected = clean_quality_report.model_dump()
        assert result.data_quality_findings == expected


# ---------------------------------------------------------------------------
# 10h — Growth rate edge cases
# ---------------------------------------------------------------------------


class TestGrowthRate:
    def test_growth_rate_zero_start(
        self,
        engine: InsightEngine,
        clean_quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> None:
        df = pd.DataFrame({"val": [0.0, 10.0, 20.0, 30.0, 40.0, 50.0]})
        result = engine.generate_insights(
            df, clean_quality_report, pipeline_run_id=pipeline_run_id
        )

        val_summary = next(s for s in result.summary if s.column_name == "val")
        assert val_summary.growth_rate is None

    def test_growth_rate_negative_start(
        self,
        engine: InsightEngine,
        clean_quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> None:
        df = pd.DataFrame({"val": [-100.0, -50.0, 0.0, 50.0]})
        result = engine.generate_insights(
            df, clean_quality_report, pipeline_run_id=pipeline_run_id
        )

        val_summary = next(s for s in result.summary if s.column_name == "val")
        assert val_summary.growth_rate is not None
        expected = (50.0 - (-100.0)) / abs(-100.0)
        assert abs(val_summary.growth_rate - expected) < 1e-9


# ---------------------------------------------------------------------------
# 10i — Structlog output
# ---------------------------------------------------------------------------


class TestStructlog:
    def test_structlog_emits_pipeline_run_id(
        self,
        engine: InsightEngine,
        full_sales_df: pd.DataFrame,
        clean_quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> None:
        cap = structlog.testing.LogCapture()
        structlog.configure(
            processors=[structlog.contextvars.merge_contextvars, cap]
        )
        try:
            structlog.contextvars.clear_contextvars()
            engine.generate_insights(
                full_sales_df,
                clean_quality_report,
                pipeline_run_id=pipeline_run_id,
            )

            assert any(
                entry.get("pipeline_run_id") == pipeline_run_id
                and entry.get("stage") == "insight_engine"
                for entry in cap.entries
            )
        finally:
            configure_logging()
            structlog.contextvars.clear_contextvars()


# ---------------------------------------------------------------------------
# 10j — Pydantic serialization
# ---------------------------------------------------------------------------


class TestSerialization:
    def test_insight_payload_serializes_cleanly(
        self,
        engine: InsightEngine,
        full_sales_df: pd.DataFrame,
        clean_quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> None:
        result = engine.generate_insights(
            full_sales_df, clean_quality_report, pipeline_run_id=pipeline_run_id
        )

        json_str = result.model_dump_json()
        assert "NaN" not in json_str
        assert "Infinity" not in json_str

        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert "summary" in parsed
        assert "key_insights" in parsed
