"""Alert Pydantic models — Story 2.5 (Monitoring Agent & Alert Delivery).

Defines the structured alert contract the Monitoring Agent emits when a
configured ``metric_thresholds`` entry is breached by a drift finding. The
shape is fixed by architecture.md §469-477: an :class:`AlertMessage` bundles
the triggering ``rule`` and the observed ``finding`` under a stable id and
UTC timestamp, and is both written to ``output/alerts/`` and rendered into the
email body.

Severity is reused from :mod:`backend.models.quality_report` (the same enum the
Drift Engine classifies findings with) so an alert never invents a new severity
scale — it carries through the severity the Drift Engine already assigned.
"""

from __future__ import annotations

from pydantic import BaseModel

from backend.models.quality_report import Severity


class AlertRule(BaseModel):
    """The threshold rule that fired.

    ``type`` is the rule kind (currently only ``"mean_shift"``); ``column`` is
    the metric it applies to; ``threshold`` is the configured fractional bound
    (e.g. ``0.15`` == +-15%) that ``abs(finding.actual_value)`` exceeded.
    """

    type: str
    column: str
    threshold: float


class AlertFinding(BaseModel):
    """The observed drift value that breached the rule.

    ``actual_value`` is the Drift Engine's signed relative change,
    ``severity`` the severity it classified, and ``detail`` its human-readable
    explanation — carried through verbatim from the ``DriftFinding``.
    """

    actual_value: float
    severity: Severity
    detail: str


class AlertMessage(BaseModel):
    """A single delivered alert — the durable record (JSON) and email payload.

    ``triggered_at`` is an ISO 8601 UTC timestamp; ``dataset`` is the dataset
    key the alert pertains to. Fields match architecture.md §469-477.
    """

    alert_id: str
    triggered_at: str
    rule: AlertRule
    finding: AlertFinding
    dataset: str
