"""Deterministic cleaning primitives (Story 3.2).

Pure, side-effect-free functions implementing the five PRD Phase-9 remediations.
Each returns a NEW object (never mutates its argument) plus the metadata the
:class:`~backend.pipeline.cleaning_engine.CleaningEngine` needs to build a
:class:`~backend.models.cleaning_result.CleaningAction`.

These functions carry no knowledge of ``remediation_class`` or the DQA report —
they are the mechanical *how*, deliberately separated from the engine's *whether*
(which findings may be touched). That separation lets Story 3.4's Tier-2 policy
layer call :func:`impute_nulls` directly without importing the autonomous engine.

Architecture compliance (architecture.md §482-506, §745): lives in
``backend/pipeline/``; imports only stdlib + pandas/numpy; no ``api``/``agents``
/legacy imports; no import-time side effects; no logging self-config.
"""

from __future__ import annotations

import datetime as _dt
import re
from collections import Counter
from typing import Any, cast

import numpy as np
import pandas as pd

# Imputation methods the policy-less primitive accepts. Story 3.4 selects one
# per column through the Tier-2 policy layer; there is deliberately no default.
IMPUTATION_METHODS: frozenset[str] = frozenset(
    {"mean", "median", "mode", "forward_fill"}
)

# Column-name normalization pattern: any run of characters that is not an ASCII
# letter, digit, or underscore collapses to a single underscore.
_NON_SLUG_CHARS = re.compile(r"[^a-zA-Z0-9_]+")
_MULTI_UNDERSCORE = re.compile(r"_+")


def _cell_changed(before: Any, after: Any) -> bool:
    """True iff a cell's value materially changed (NaN-aware, no NaN!=NaN noise)."""
    before_na = pd.isna(before)
    after_na = pd.isna(after)
    if before_na and after_na:
        return False
    if before_na != after_na:
        return True
    return bool(before != after)


def strip_whitespace(series: pd.Series) -> tuple[pd.Series, int]:
    """Strip leading/trailing whitespace from string cells only.

    Non-string cells (numbers, NaN, datetimes) pass through untouched. Returns
    the new series and the count of cells whose value changed.
    """
    stripped = series.map(lambda v: v.strip() if isinstance(v, str) else v)
    is_str = series.map(lambda v: isinstance(v, str))
    changed = int((is_str & (stripped != series)).sum())
    return stripped, changed


def dominant_python_type(series: pd.Series) -> type | None:
    """Return the most common Python ``type`` among non-null cells.

    Counts via a plain :class:`collections.Counter` rather than
    ``Series.value_counts()`` and breaks ties on ``(module, qualname)`` —
    deterministically, independent of hash-seed or iteration order. An exact
    count tie between two types (e.g. equally many ints and numeric strings)
    is a realistic input; ``value_counts()`` does not guarantee a stable
    tie-break across process runs (dict/hashtable iteration order can vary
    under hash randomization), which would violate this engine's "no
    iteration-order dependence" invariant. ``None`` if all cells are null.
    """
    non_null = series.dropna()
    if non_null.empty:
        return None
    counts = Counter(type(v) for v in non_null)
    max_count = max(counts.values())
    candidates = [t for t, c in counts.items() if c == max_count]
    return sorted(candidates, key=lambda t: (t.__module__, t.__qualname__))[0]


def _is_numeric_type(t: type) -> bool:
    # bool is a subclass of int — exclude it; coercing booleans is not our job.
    if issubclass(t, bool):
        return False
    return issubclass(t, (int, float, np.integer, np.floating))


def _is_datetime_type(t: type) -> bool:
    # pd.Timestamp subclasses datetime.datetime, so this covers it too.
    return issubclass(t, (_dt.datetime, _dt.date))


def coerce_column_type(series: pd.Series) -> tuple[pd.Series, dict[str, Any]]:
    """Coerce a mixed-type column toward its dominant type, non-destructively.

    Steps, in order:

    1. Strip whitespace from string cells.
    2. Determine the dominant Python type among non-null cells.
    3. Coerce minority values toward it:

       * numeric dominant → :func:`pandas.to_numeric` with ``errors="coerce"``,
         but **only adopt values that converted**; a value that fails to convert
         keeps its original (never becomes null).
       * datetime dominant → parse and standardize to ISO-8601 date strings
         (``YYYY-MM-DD``); failures keep their original.
       * otherwise (string/other dominant) → whitespace normalization only.

    Never introduces a new null. Returns the new series and metadata:
    ``kind`` (numeric|datetime|whitespace_only|empty), ``dominant_type``,
    ``values_changed`` (cells rewritten, incl. whitespace), ``uncoerced``
    (non-null cells that could not be coerced and were preserved).
    """
    original = series
    stripped, _ = strip_whitespace(series)
    dominant = dominant_python_type(stripped)

    if dominant is None:
        return stripped, {
            "kind": "empty",
            "dominant_type": "none",
            "values_changed": 0,
            "uncoerced": 0,
        }

    if _is_numeric_type(dominant):
        coerced = pd.to_numeric(stripped, errors="coerce")
        ok_mask = coerced.notna()
        failed_mask = coerced.isna() & stripped.notna()
        result = stripped.astype(object).copy()
        result[ok_mask] = coerced[ok_mask]
        kind = "numeric"
    elif _is_datetime_type(dominant):
        parsed = pd.to_datetime(stripped, errors="coerce")
        ok_mask = parsed.notna()
        failed_mask = parsed.isna() & stripped.notna()
        iso = parsed.dt.strftime("%Y-%m-%d")
        result = stripped.astype(object).copy()
        result[ok_mask] = iso[ok_mask]
        kind = "datetime"
    else:
        # String/other dominant: whitespace normalization is the only safe,
        # deterministic remediation. No type change.
        result = stripped
        failed_mask = pd.Series(False, index=series.index)
        kind = "whitespace_only"

    values_changed = int(
        sum(
            _cell_changed(b, a)
            for b, a in zip(original.tolist(), result.tolist())
        )
    )
    return result, {
        "kind": kind,
        "dominant_type": getattr(dominant, "__name__", str(dominant)),
        "values_changed": values_changed,
        "uncoerced": int(failed_mask.sum()),
    }


def normalize_case(series: pd.Series) -> tuple[pd.Series, dict[str, Any]]:
    """Collapse case variants of string values to a single canonical form.

    Per group of values equal under ``str.lower()``, the canonical form is the
    most frequent original variant; ties break to the lexicographically smallest
    variant (fully deterministic). Non-string cells pass through untouched.

    Returns the new series and metadata: ``mapping`` (variant → canonical, only
    for variants that changed) and ``values_changed``.
    """
    groups: dict[str, Counter] = {}
    for value in series.dropna():
        if not isinstance(value, str):
            continue
        groups.setdefault(value.lower(), Counter())[value] += 1

    mapping: dict[str, str] = {}
    for counter in groups.values():
        max_count = max(counter.values())
        canonical = sorted(v for v, c in counter.items() if c == max_count)[0]
        for variant in counter:
            if variant != canonical:
                mapping[variant] = canonical

    result = series.map(
        lambda v: mapping.get(v, v) if isinstance(v, str) else v
    )
    values_changed = int(
        series.map(lambda v: isinstance(v, str) and v in mapping).sum()
    )
    return result, {"mapping": mapping, "values_changed": values_changed}


def drop_exact_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop exact duplicate rows, keeping the first occurrence.

    Original row order of the surviving rows is preserved; the index is reset.
    Returns the new frame and the number of rows removed.
    """
    before = len(df)
    deduped = df.drop_duplicates(keep="first").reset_index(drop=True)
    return deduped, before - len(deduped)


def _slug(name: Any, position: int) -> str:
    """Deterministic single-name normalization (see :func:`normalize_column_names`)."""
    text = _NON_SLUG_CHARS.sub("_", str(name).strip())
    text = _MULTI_UNDERSCORE.sub("_", text).strip("_").lower()
    if text == "" or text.isdigit():
        return f"column_{position}"
    return text


def normalize_column_names(
    columns: list[Any],
    targets: set[str] | None = None,
) -> tuple[list[str], dict[str, str]]:
    """Normalize column names deterministically, collision-safe.

    Each name in ``targets`` (matched by ``str(name)``) is renamed: strip →
    collapse non-``[A-Za-z0-9_]`` runs to ``_`` → collapse repeats → trim ``_``
    → lowercase; empty or purely-numeric results become ``column_{position}``
    (0-based). Columns NOT in ``targets`` pass through with their original name
    **unchanged** — but still occupy a slot in collision detection, so a
    renamed column can never silently collide with an untouched one.

    ``targets=None`` renames every column (the historical/full-frame
    behavior). Passing an explicit set is how the Cleaning Engine scopes a
    header-normalization action to only the columns a finding actually
    flagged, leaving every other column — including ones with no finding at
    all — byte-identical.

    A normalized name colliding with one already assigned is suffixed ``_2``,
    ``_3``, …. Untouched columns are reserved in a first pass — before any
    renaming — so a rename always de-collides against the FULL untouched set,
    not just the untouched names that happen to appear earlier in the frame.
    Untouched columns are therefore guaranteed byte-identical and never
    suffixed, regardless of column order.

    Returns the new column list and a mapping of old → new for names that
    actually changed.
    """
    new_columns: list[str | None] = [None] * len(columns)
    assigned: set[str] = set()

    # Pass 1: reserve every untouched name so renames can never collide with
    # one, independent of position.
    for position, name in enumerate(columns):
        name_str = str(name)
        if targets is not None and name_str not in targets:
            new_columns[position] = name_str
            assigned.add(name_str)

    # Pass 2: slug + de-collide every targeted (or, with targets=None, every)
    # column against the reserved set plus renames assigned so far.
    mapping: dict[str, str] = {}
    for position, name in enumerate(columns):
        name_str = str(name)
        if targets is not None and name_str not in targets:
            continue

        base = _slug(name, position)
        candidate = base
        suffix = 2
        while candidate in assigned:
            candidate = f"{base}_{suffix}"
            suffix += 1
        assigned.add(candidate)
        new_columns[position] = candidate
        if candidate != name_str:
            mapping[name_str] = candidate

    # Every position is filled by exactly one of the two passes above
    # (untouched vs. targeted are mutually exclusive and exhaustive).
    return cast("list[str]", new_columns), mapping


def impute_nulls(df: pd.DataFrame, column: str, method: str) -> pd.DataFrame:
    """Impute nulls in one column using an explicit method (policy-less primitive).

    **Story 3.2 ships this WITHOUT autonomy and WITHOUT a default.** It is Tier-2
    (``human_policy_agent_execution``): the *choice* of method is a human policy
    decision Story 3.4 will supply. The autonomous cleaning path never calls this
    — it is exposed here purely so 3.4's policy layer can execute a chosen method.

    Parameters
    ----------
    df:
        Source frame (never mutated — a copy is returned).
    column:
        Column to impute.
    method:
        One of :data:`IMPUTATION_METHODS`. **Required** — there is no default,
        so a caller must make the policy choice explicit.

    Raises
    ------
    ValueError
        If ``method`` is not a recognized imputation method, or ``column`` is
        absent. Fail loudly rather than guess a fill.
    """
    if method not in IMPUTATION_METHODS:
        raise ValueError(
            f"unknown imputation method {method!r}; "
            f"expected one of {sorted(IMPUTATION_METHODS)}"
        )
    if column not in df.columns:
        raise ValueError(f"column {column!r} not in frame")
    if method in ("mean", "median") and not pd.api.types.is_numeric_dtype(
        df[column]
    ):
        raise ValueError(
            f"method {method!r} requires a numeric column; "
            f"{column!r} has dtype {df[column].dtype}"
        )

    out = df.copy()
    col = out[column]

    if method == "forward_fill":
        out[column] = col.ffill()
        return out
    if method == "mean":
        fill = col.mean()
    elif method == "median":
        fill = col.median()
    else:  # mode
        modes = col.mode(dropna=True)
        fill = modes.iloc[0] if not modes.empty else None

    out[column] = col.fillna(fill)
    return out
