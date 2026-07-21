"""Shared pytest fixtures for the backend test suite.

Every backend test inherits from these fixtures. Keep them additive: if a
downstream test needs a variation (e.g., a DataFrame with *only*
date-monotonicity defects), derive a new fixture in that test's module
rather than mutating these. Stories 1.2–1.6 all depend on this file.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from backend.core.logging import configure_logging

# Defect-seeding indices for dirty_sales_df — kept as module constants so
# test assertions can reference the exact positions rather than magic
# numbers. 50-row dataset, 26 null revenues (>=50%), 1 negative, 1 string,
# 1 duplicate row, 1 swapped date pair.
_NULL_REVENUE_COUNT = 26
_NEGATIVE_REVENUE_IDX = 30
_STRING_REVENUE_IDX = 31
_DUP_SRC_IDX = 40
_DUP_DST_IDX = 41
_DATE_SWAP_IDX_A = 10
_DATE_SWAP_IDX_B = 11


@pytest.fixture(scope="session", autouse=True)
def _configure_logging_for_session() -> None:
    """Install the structlog JSON processor chain once per test session.

    Autouse so every test — including ones that do not reference logging
    directly — runs under the same logging configuration that production
    code will run under.
    """
    configure_logging()


@pytest.fixture
def clean_sales_df() -> pd.DataFrame:
    """50-row, 3-column sales DataFrame with zero defects.

    Columns: ``date`` (datetime64[ns], monotonically increasing daily),
    ``region`` (object), ``revenue`` (float64, ~1000-5000 range). No
    nulls, no duplicates.
    """
    rng = np.random.default_rng(seed=42)
    start = datetime(2026, 1, 1)
    return pd.DataFrame(
        {
            "date": pd.to_datetime([start + timedelta(days=i) for i in range(50)]),
            "region": rng.choice(["north", "south", "east", "west"], size=50).astype(object),
            "revenue": rng.uniform(1000.0, 5000.0, size=50).round(2),
        }
    )


@pytest.fixture
def dirty_sales_df() -> pd.DataFrame:
    """50-row sales DataFrame seeded with KNOWN defects.

    Defect inventory (exact positions in module-level constants):

    * ``revenue`` null in rows ``[0, _NULL_REVENUE_COUNT)`` — 26/50 = 52%
      null rate, crosses the Critical completeness threshold.
    * ``revenue[_NEGATIVE_REVENUE_IDX]`` is ``-500.0`` — a numeric
      red flag (sales cannot be negative in this schema).
    * ``revenue[_STRING_REVENUE_IDX]`` is the literal string ``"N/A"`` —
      forces the column to ``object`` dtype and exercises the
      numeric-coercion path.
    * Row ``_DUP_DST_IDX`` is an exact duplicate of row ``_DUP_SRC_IDX``.
    * Rows ``_DATE_SWAP_IDX_A`` and ``_DATE_SWAP_IDX_B`` have their
      dates swapped, breaking strict monotonicity.
    """
    rng = np.random.default_rng(seed=42)
    start = datetime(2026, 1, 1)

    dates: list[datetime] = [start + timedelta(days=i) for i in range(50)]
    dates[_DATE_SWAP_IDX_A], dates[_DATE_SWAP_IDX_B] = (
        dates[_DATE_SWAP_IDX_B],
        dates[_DATE_SWAP_IDX_A],
    )

    regions: list[str] = [str(r) for r in rng.choice(["north", "south", "east", "west"], size=50)]
    revenues: list[Any] = [float(v) for v in rng.uniform(1000.0, 5000.0, size=50).round(2)]

    for i in range(_NULL_REVENUE_COUNT):
        revenues[i] = None
    revenues[_NEGATIVE_REVENUE_IDX] = -500.0
    revenues[_STRING_REVENUE_IDX] = "N/A"

    # Exact duplicate row at (src, dst).
    dates[_DUP_DST_IDX] = dates[_DUP_SRC_IDX]
    regions[_DUP_DST_IDX] = regions[_DUP_SRC_IDX]
    revenues[_DUP_DST_IDX] = revenues[_DUP_SRC_IDX]

    return pd.DataFrame(
        {
            "date": pd.to_datetime(dates),
            "region": regions,
            "revenue": revenues,
        }
    )


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """MagicMock stub for the Anthropic-style LLM client.

    ``client.messages.parse(...)`` returns an object with an
    ``output_parsed`` attribute (defaulting to ``None``). Story 1.4 will
    subclass or replace this fixture with a richer contract once the
    narrative generator is implemented.
    """
    client = MagicMock()
    parsed_stub = MagicMock()
    parsed_stub.output_parsed = None
    client.messages.parse.return_value = parsed_stub
    return client


@pytest.fixture
def pipeline_run_id() -> str:
    """Fresh 32-char hex run ID, one per test invocation."""
    return uuid.uuid4().hex


# --- Story 2.3 (Drift Engine) additive fixtures ---------------------------
@pytest.fixture
def baseline_profile_from_clean(clean_sales_df: pd.DataFrame):
    """A ``BaselineProfile`` computed from ``clean_sales_df``.

    Additive per this file's rule — does not mutate ``clean_sales_df``.
    """
    from backend.pipeline.drift_engine import DriftEngine

    return DriftEngine()._build_profile(clean_sales_df, dataset_key="sales_test")


@pytest.fixture
def drifted_sales_df(clean_sales_df: pd.DataFrame) -> pd.DataFrame:
    """``clean_sales_df`` with ``revenue`` scaled ~40% up — forces HIGH mean shift."""
    drifted = clean_sales_df.copy()
    drifted["revenue"] = (drifted["revenue"] * 1.4).round(2)
    return drifted


# --- Story 3.2 (Cleaning Engine) additive fixture -------------------------
# Row layout (12 rows) — positions chosen so the ONE dedup-removed row does not
# overlap the Tier-2/Tier-3 findings in `quantity`, letting tests assert those
# human-owned findings survive cleaning unchanged.
_CLEAN_DIRTY_NULL_QTY_IDX = (0, 1)  # Tier-2 null_values
_CLEAN_DIRTY_NEG_QTY_IDX = 2  # Tier-3 negative_values (quantity implies >= 0)
_CLEAN_DIRTY_DUP_SRC_IDX = 5  # Tier-1 duplicate_rows source
_CLEAN_DIRTY_DUP_DST_IDX = 6  # exact duplicate of row 5


@pytest.fixture
def cleaning_dirty_df() -> pd.DataFrame:
    """12-row frame seeded with a KNOWN mix of Tier-1/2/3 defects.

    The assessor emits exactly these defect types against it:

    * Tier 1 (``agent_autonomous`` — the engine SHOULD fix):
      - ``case_inconsistency`` in ``region`` (north/North/NORTH collapse).
      - ``mixed_types`` in ``code`` (ints + numeric-as-string — fully coercible,
        so coercion resolves the column and the defect disappears on re-assess).
      - ``duplicate_rows`` (row 6 is an exact duplicate of row 5).
      - ``column_naming`` in the header ``"amount#"`` (special char).
    * Tier 2 (``human_policy_agent_execution`` — the engine must NOT touch):
      - ``null_values`` in ``quantity`` (rows 0, 1).
    * Tier 3 (``human_only`` — the engine must NEVER touch):
      - ``negative_values`` in ``quantity`` (row 2 is ``-5``; ``quantity``
        implies non-negativity).

    The duplicate row (5/6) carries a positive, non-null ``quantity``, so
    removing it leaves the Tier-2/Tier-3 quantity findings intact.
    """
    regions = [
        "north", "North", "NORTH", "south", "south",
        "east", "east", "west", "north", "south",
        "NORTH", "west",
    ]
    quantity: list[Any] = [float(v) for v in (10, 20, -5, 40, 50, 60, 70, 80, 90, 100, 110, 120)]
    quantity[_CLEAN_DIRTY_NULL_QTY_IDX[0]] = None
    quantity[_CLEAN_DIRTY_NULL_QTY_IDX[1]] = None
    quantity[_CLEAN_DIRTY_NEG_QTY_IDX] = -5.0
    # code: object column mixing int and numeric-as-string (all coercible).
    code: list[Any] = [10, 20, "30", 40, "50", 60, 70, "80", 90, 100, "110", 120]
    amount = [float(v) for v in range(100, 220, 10)]  # 12 clean positive floats

    df = pd.DataFrame(
        {
            "region": regions,
            "quantity": quantity,
            "code": code,
            "amount#": amount,  # special char in header -> column_naming
        }
    )
    # Make row DST an exact duplicate of row SRC across every column.
    df.iloc[_CLEAN_DIRTY_DUP_DST_IDX] = df.iloc[_CLEAN_DIRTY_DUP_SRC_IDX]
    return df
