"""Client-facing cleaning disclosure contract (Story 3.9)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from backend.models.cleaning_disclosure import (
    CLEANING_BEHAVIOR_DISCLOSURE,
    IMPUTATION_METHOD_DESCRIPTIONS,
    get_imputation_method_description,
    iter_imputation_method_descriptions,
)
from backend.models.pipeline_config import _policy_methods
from backend.pipeline.orchestrator import _cleaning_help_text


_PROHIBITED_CLIENT_TERMS = (
    r"\btier[\s_-]*\d+\b",
    r"\bremediation[_\s-]*class\b",
    r"\bhuman[_\s-]*policy[_\s-]*agent[_\s-]*execution\b",
    r"\bhuman[_\s-]*only\b",
    r"\bpolicy\b",
    r"\bpolicy layer\b",
    r"\bexecution primitive\b",
)


def _all_copy() -> str:
    return "\n".join(
        [
            CLEANING_BEHAVIOR_DISCLOSURE,
            *(
                f"{description.label}\n{description.explanation}"
                for description in IMPUTATION_METHOD_DESCRIPTIONS.values()
            ),
        ]
    )


def test_copy_keys_exactly_match_configured_methods() -> None:
    assert set(IMPUTATION_METHOD_DESCRIPTIONS) == set(_policy_methods())
    assert all(
        description.label.strip() and description.explanation.strip()
        for description in IMPUTATION_METHOD_DESCRIPTIONS.values()
    )


@pytest.mark.parametrize(
    ("method", "required_phrases"),
    [
        ("mean", ("column's average", "unusually high or low", "reduce observed variation")),
        ("median", ("middle value", "less affected", "understate variation")),
        ("mode", ("most common value", "overrepresent", "conceal less frequent values")),
        (
            "forward_fill",
            (
                "previous available value",
                "assumes the earlier value",
                "cannot fill leading gaps",
                "no earlier value",
            ),
        ),
        ("leave_as_is", ("preserves missing values", "no values are filled")),
    ],
)
def test_each_method_states_its_effect_and_required_limitation(
    method: str, required_phrases: tuple[str, ...]
) -> None:
    explanation = IMPUTATION_METHOD_DESCRIPTIONS[method].explanation.lower()
    assert all(phrase in explanation for phrase in required_phrases)


def test_cleaning_disclosure_states_the_safety_boundary() -> None:
    disclosure = CLEANING_BEHAVIOR_DISCLOSURE.lower()
    assert "optional and off by default" in disclosure
    assert "supported, deterministic changes" in disclosure
    assert "working copy" in disclosure
    assert "original input unchanged" in disclosure
    assert "healing manifest" in disclosure
    assert "need your judgment are left unchanged" in disclosure


def test_copy_makes_no_suitability_or_accuracy_claim() -> None:
    copy = _all_copy().lower()
    for prohibited_claim in (
        "suitable",
        "appropriate for",
        "best method",
        "improves accuracy",
        "improved accuracy",
        "more accurate",
        "guarantees",
    ):
        assert prohibited_claim not in copy


def test_copy_contains_no_internal_or_tier_terms() -> None:
    copy = _all_copy()
    for pattern in _PROHIBITED_CLIENT_TERMS:
        assert re.search(pattern, copy, flags=re.IGNORECASE) is None


def test_unknown_method_fails_closed_without_rendering_raw_value() -> None:
    unknown = "UNTRUSTED_RAW_METHOD_5c8d"
    assert get_imputation_method_description(unknown) is None

    selected = iter_imputation_method_descriptions([unknown, "mean"])
    assert selected == (("mean", IMPUTATION_METHOD_DESCRIPTIONS["mean"]),)

    rendered = _cleaning_help_text([unknown, "mean"])
    assert unknown not in rendered
    assert "Average (mean)" in rendered


def test_future_surface_interface_reuses_the_canonical_copy_objects() -> None:
    selected = iter_imputation_method_descriptions()
    assert tuple(method for method, _description in selected) == tuple(
        IMPUTATION_METHOD_DESCRIPTIONS
    )
    assert all(
        description is IMPUTATION_METHOD_DESCRIPTIONS[method]
        for method, description in selected
    )


def test_config_cleaning_help_avoids_internal_terminology() -> None:
    config_text = Path("config.yaml").read_text(encoding="utf-8")
    cleaning_help = config_text[config_text.index("# Cleaning is optional") :]
    for pattern in _PROHIBITED_CLIENT_TERMS:
        assert re.search(pattern, cleaning_help, flags=re.IGNORECASE) is None
