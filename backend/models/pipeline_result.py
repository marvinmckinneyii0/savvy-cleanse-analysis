"""The PipelineResult contract.

This is the single return envelope emitted by the top-level pipeline
orchestrator. It is intentionally a stdlib ``@dataclass`` rather than a
Pydantic model — unlike every other pipeline I/O type — because downstream
stages may populate its fields *after* construction (e.g., the narrative
generator adds ``insight_report`` onto a result originally produced by the
data-quality stage). Pydantic's "immutable until validated" stance fights
that pattern; the stdlib dataclass does not.

This exception to the "Pydantic for all I/O" rule is explicitly sanctioned
in architecture.md (section 486-494) and nowhere else. Every other
cross-stage type MUST be a Pydantic model.

See :mod:`backend.errors.exceptions` for the companion concept:
:class:`PipelineResult` carries *business outcomes* (good data, bad data,
halt-on-critical); the ``SavvyCleanseError`` hierarchy carries
*infrastructure failures*.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # These models land in later stories (1.2 DQA, 1.3 Insight Engine, 2.2
    # Drift Engine). Imported under TYPE_CHECKING so type-checkers resolve
    # the forward references below without a runtime import cycle and
    # without requiring the modules to exist yet at import time.
    from backend.models.cleaning_result import CleaningResult
    from backend.models.data_quality_report import DataQualityReport
    from backend.models.drift_report import DriftReport
    from backend.models.insight_report import InsightReport


@dataclass
class PipelineResult:
    """Envelope returned by the pipeline orchestrator.

    Attributes
    ----------
    success:
        ``True`` iff the pipeline completed without halting. A ``success``
        result may still carry warnings — downstream consumers should
        inspect the nested reports for severity.
    halted:
        ``True`` iff a stage invoked the halt-on-critical path. ``success``
        is always ``False`` when ``halted`` is ``True``.
    halt_reason:
        Human-readable explanation of why the pipeline halted. ``None``
        when ``halted`` is ``False``.
    quality_report:
        Output of the data-quality stage (Story 1.2). ``None`` until that
        stage runs.
    insight_report:
        Output of the insight-generation + narrative stages (Stories 1.3
        and 1.4). ``None`` if the pipeline halted before reaching them.
    drift_report:
        Output of the drift-detection stage (Story 2.2). ``None`` on
        first-ever runs (no baseline) and when drift is skipped.
    cleaning_result:
        Output of the opt-in cleaning stage (Story 3.4). ``None`` unless
        cleaning was explicitly enabled AND the run did not halt; carries the
        merged Tier-1 + Tier-2 :class:`CleaningResult`. Additive and default-
        off — a run with cleaning disabled leaves this ``None`` and every other
        field byte-identical to the pre-3.4 pipeline.
    """

    success: bool
    halted: bool = False
    halt_reason: str | None = None
    quality_report: "DataQualityReport | None" = None
    insight_report: "InsightReport | None" = None
    drift_report: "DriftReport | None" = None
    cleaning_result: "CleaningResult | None" = None
