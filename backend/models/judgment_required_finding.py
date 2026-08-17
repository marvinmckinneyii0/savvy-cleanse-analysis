"""Judgment-Required Findings — the client-facing surfacing of Tier-3 findings
(Story 3.5).

Renders `human_only` DQA defects (`RemediationClass.HUMAN_ONLY`) into a
structured, report-ready list. Purpose-built projection, NOT a re-export of
:class:`~backend.models.quality_report.DataQualityDefect`: that model carries
internal taxonomy (`defect_type`, `category`, `remediation_class`) that must
never reach client-facing text — per schema-extensions-spec.md §1, Tier 3
"is NOT a purchasable capability... do not create a 'Tier 3' row in any
client-facing surface." Mirrors the same reasoning Story 3.3's `ManifestEntry`
applied to `CleaningAction`.

Reuses the DQA detectors' existing `details`/`recommended_action` prose
as-is — already client-safe (column names and counts only, no raw cell
values, no internal jargon; verified against every Tier-3 detector in
`backend/pipeline/data_quality.py`). This module adds no new evidence,
scoring, or reasoning — that class of capability belongs to Epic 11 (Tier 4
autonomous judgment), a deliberately "distinct artifact" per
epic-11-autonomous-judgment-eval-governance.md §11.5.

Unlike `HealingManifest` (populated only when cleaning ran), this list is
populated whenever `human_only` findings exist, independent of the cleaning
opt-in: it describes a property of the data (which findings the agent will
never touch), computed unconditionally during DQA classification (Story
3.1), not an action that may or may not have run.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.models.quality_report import DataQualityReport, RemediationClass, Severity


class JudgmentRequiredFinding(BaseModel):
    """One `human_only` finding, projected to only the fields safe to render."""

    sequence: int
    severity: Severity
    affected_columns: list[str] = Field(default_factory=list)
    count: int
    percentage: float
    # NOTE: sourced from DataQualityDefect.details (plural) -- named `detail`
    # (singular) here to match ManifestEntry's naming convention. A template
    # reference to `finding.details` is an AttributeError, not a silent bug.
    detail: str
    recommended_action: str


def build_judgment_required_findings(
    quality_report: DataQualityReport,
) -> list[JudgmentRequiredFinding]:
    """Project every `human_only` defect in `quality_report` to a
    `JudgmentRequiredFinding`, preserving `quality_report.defects`' order.

    Pure: no DataFrame access, no I/O, no re-derivation of anything the
    classifier (Story 3.1) hasn't already computed.
    """
    findings: list[JudgmentRequiredFinding] = []
    for defect in quality_report.defects:
        if defect.remediation_class != RemediationClass.HUMAN_ONLY:
            continue
        findings.append(
            JudgmentRequiredFinding(
                sequence=len(findings),
                severity=defect.severity,
                affected_columns=list(defect.affected_columns),
                count=defect.count,
                percentage=defect.percentage,
                detail=defect.details,
                recommended_action=defect.recommended_action,
            )
        )
    return findings
