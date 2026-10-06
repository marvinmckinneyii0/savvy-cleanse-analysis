"""Reusable client-facing cleaning descriptions (Story 3.9).

This module is the single source of truth for copy shown at cleaning
configuration surfaces. Method identifiers remain lookup keys for config
compatibility; callers render the descriptive labels and explanations.
Unknown identifiers are deliberately omitted by the consuming interface so
untrusted values can never become client-facing text.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class ImputationMethodDescription:
    """Plain-language label and explanation for one configured method."""

    label: str
    explanation: str


CLEANING_BEHAVIOR_DISCLOSURE = (
    "Cleaning is optional and off by default. When enabled, SAINT applies only "
    "supported, deterministic changes to a working copy, keeps the original input "
    "unchanged, and records every action in the Healing Manifest. Findings that need "
    "your judgment are left unchanged."
)


IMPUTATION_METHOD_DESCRIPTIONS: Mapping[str, ImputationMethodDescription] = (
    MappingProxyType(
        {
            "mean": ImputationMethodDescription(
                label="Average",
                explanation=(
                    "Fills gaps with the column's average. Unusually high or low values "
                    "can pull the average, and filling gaps this way can reduce observed "
                    "variation."
                ),
            ),
            "median": ImputationMethodDescription(
                label="Middle value",
                explanation=(
                    "Fills gaps with the middle value. It is less affected by unusually "
                    "high or low values than the average, but it can understate variation."
                ),
            ),
            "mode": ImputationMethodDescription(
                label="Most common value",
                explanation=(
                    "Fills gaps with the most common value. It can overrepresent the common "
                    "category and conceal less frequent values."
                ),
            ),
            "forward_fill": ImputationMethodDescription(
                label="Previous available value",
                explanation=(
                    "Carries the previous available value forward. This assumes the earlier "
                    "value remains a reasonable substitute and cannot fill leading gaps "
                    "when no earlier value exists."
                ),
            ),
            "leave_as_is": ImputationMethodDescription(
                label="Keep missing values",
                explanation="Preserves missing values; no values are filled.",
            ),
        }
    )
)


def get_imputation_method_description(
    method: str,
) -> ImputationMethodDescription | None:
    """Return canonical copy for ``method`` or ``None`` for an unknown key."""

    return IMPUTATION_METHOD_DESCRIPTIONS.get(method)


def iter_imputation_method_descriptions(
    methods: Iterable[str] | None = None,
) -> tuple[tuple[str, ImputationMethodDescription], ...]:
    """Return known method copy in canonical order, omitting unknown keys.

    ``None`` selects every supported description. Supplying identifiers filters
    that canonical set; unknown identifiers fail closed and are never returned
    for rendering.
    """

    if methods is None:
        return tuple(IMPUTATION_METHOD_DESCRIPTIONS.items())

    requested = frozenset(methods)
    return tuple(
        (method, description)
        for method, description in IMPUTATION_METHOD_DESCRIPTIONS.items()
        if method in requested
    )
