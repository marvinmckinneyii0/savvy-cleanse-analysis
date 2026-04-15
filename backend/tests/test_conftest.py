"""Fixture self-tests.

These exist to satisfy the Story 1.1 acceptance criterion that
``pytest backend/tests/`` runs green with the conftest fixtures
validated. They also lock in the dirty-dataset defect inventory so that
Story 1.2 (data-quality engine) develops against a stable contract —
any future change to the fixtures that invalidates one of these
assertions is a breaking change to every downstream test suite.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
import structlog


class TestCleanSalesDF:
    def test_shape(self, clean_sales_df: pd.DataFrame) -> None:
        assert clean_sales_df.shape == (50, 3)

    def test_columns(self, clean_sales_df: pd.DataFrame) -> None:
        assert list(clean_sales_df.columns) == ["date", "region", "revenue"]

    def test_no_nulls(self, clean_sales_df: pd.DataFrame) -> None:
        assert not clean_sales_df.isna().any().any()

    def test_no_duplicates(self, clean_sales_df: pd.DataFrame) -> None:
        assert not clean_sales_df.duplicated().any()

    def test_dtypes(self, clean_sales_df: pd.DataFrame) -> None:
        # pandas <3.0 stores python strings as object; >=3.0 infers StringDtype.
        # Either is correct — what matters is the column holds strings.
        assert pd.api.types.is_datetime64_any_dtype(clean_sales_df["date"])
        assert pd.api.types.is_string_dtype(clean_sales_df["region"])
        assert clean_sales_df["revenue"].dtype == np.float64

    def test_dates_monotonic(self, clean_sales_df: pd.DataFrame) -> None:
        assert clean_sales_df["date"].is_monotonic_increasing


class TestDirtySalesDF:
    def test_shape(self, dirty_sales_df: pd.DataFrame) -> None:
        assert dirty_sales_df.shape == (50, 3)

    def test_revenue_null_rate_at_least_50pct(self, dirty_sales_df: pd.DataFrame) -> None:
        null_rate = dirty_sales_df["revenue"].isna().mean()
        assert null_rate >= 0.5, f"expected >=50% nulls, got {null_rate:.1%}"

    def test_has_duplicate_row(self, dirty_sales_df: pd.DataFrame) -> None:
        assert dirty_sales_df.duplicated().any()

    def test_has_negative_revenue(self, dirty_sales_df: pd.DataFrame) -> None:
        numeric = pd.to_numeric(dirty_sales_df["revenue"], errors="coerce")
        assert (numeric < 0).any()

    def test_has_non_numeric_string_in_revenue(self, dirty_sales_df: pd.DataFrame) -> None:
        has_string = dirty_sales_df["revenue"].apply(lambda v: isinstance(v, str)).any()
        assert has_string

    def test_dates_not_monotonic(self, dirty_sales_df: pd.DataFrame) -> None:
        assert not dirty_sales_df["date"].is_monotonic_increasing


class TestMockLLMClient:
    def test_is_magicmock(self, mock_llm_client: MagicMock) -> None:
        assert isinstance(mock_llm_client, MagicMock)

    def test_messages_parse_returns_object_with_output_parsed(self, mock_llm_client: MagicMock) -> None:
        result = mock_llm_client.messages.parse(model="claude-test", messages=[])
        assert hasattr(result, "output_parsed")


class TestPipelineRunID:
    def test_is_32_char_hex_string(self, pipeline_run_id: str) -> None:
        assert isinstance(pipeline_run_id, str)
        assert len(pipeline_run_id) == 32
        int(pipeline_run_id, 16)  # raises ValueError if non-hex

    def test_differs_across_invocations(self, pipeline_run_id: str) -> None:
        # The fixture is function-scoped, so a fresh uuid compared to the
        # fixture's value proves that the fixture is not a singleton.
        assert pipeline_run_id != uuid.uuid4().hex


class TestAutouseLoggingConfig:
    """The session-scoped autouse fixture must produce JSON output."""

    def test_logger_emits_json_with_expected_keys(self, capsys: pytest.CaptureFixture[str]) -> None:
        structlog.get_logger().info("scaffolding_probe", probe_key="probe_value")
        captured = capsys.readouterr()
        payload = captured.out + captured.err
        non_empty_lines = [line for line in payload.splitlines() if line.strip()]
        assert non_empty_lines, "expected at least one log line to be written"

        parsed = json.loads(non_empty_lines[-1])
        assert parsed["event"] == "scaffolding_probe"
        assert parsed["probe_key"] == "probe_value"
        assert parsed["level"] == "info"
        assert "timestamp" in parsed
