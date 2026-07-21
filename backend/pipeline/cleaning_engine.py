"""Deterministic Cleaning Engine — core (Story 3.2).

The first code path in SAINT that MODIFIES data. It applies the four Tier-1
rules-based remediations to a **working copy** of the input, acting autonomously
ONLY on findings the classifier stamped ``agent_autonomous``, and returns the
cleaned copy plus a :class:`~backend.models.cleaning_result.CleaningResult`
recording every action (the single source Story 3.3 renders the healing manifest
from).

Safety invariants (Epic 3, load-bearing — a bug here silently mutates a client's
data, a failure a passing report would not reveal):

* **Working-copy only.** A deep copy is taken at entry; the caller's frame is
  never mutated, on any path including errors.
* **Tier-1-only, fail-closed twice.** The public path filters to
  ``agent_autonomous`` findings; the private per-finding dispatch independently
  re-checks and raises :class:`CleaningEngineError` on anything else. There is no
  flag that widens this.
* **Not wired to the orchestrator.** Cleaning is opt-in / default-off; the gate
  that makes wiring safe is Story 3.4. This module is callable but unwired.

Architecture compliance (architecture.md §482-506, §745): ``backend/pipeline/``;
imports only ``models``/``errors``/siblings; never ``api``/``agents``/legacy
(notably NOT legacy ``backend/cleaner.py``); no import-time side effects;
structlog events carry ``pipeline_run_id`` and never log raw row data or PII.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import structlog

from backend.errors.exceptions import CleaningEngineError
from backend.models.cleaning_result import (
    CleaningAction,
    CleaningOperation,
    CleaningResult,
    CleaningScope,
    CleaningStatus,
)
from backend.models.quality_report import (
    DataQualityDefect,
    DataQualityReport,
    RemediationClass,
)
from backend.pipeline import cleaning_primitives as prim


class CleaningEngine:
    """Applies Tier-1 deterministic remediations to a working copy of a frame."""

    # Authoritative defect_type -> operation registry. Keyed on ``defect_type``
    # (never ``category``), mirroring the classifier: a future Tier-3 variant
    # sharing a category cannot inherit an autonomous operation, and any
    # defect_type absent here has no autonomous path at all.
    _OPERATION_BY_DEFECT_TYPE: dict[str, CleaningOperation] = {
        "mixed_types": CleaningOperation.TYPE_COERCION,
        "case_inconsistency": CleaningOperation.CASE_NORMALIZATION,
        "duplicate_rows": CleaningOperation.DEDUPLICATION,
        "column_naming": CleaningOperation.HEADER_NORMALIZATION,
    }

    # Deterministic processing order. Column-name-keyed ops (coercion, case) run
    # before header normalization so they resolve against the ORIGINAL names;
    # deduplication runs on the transformed frame (normalization can expose new
    # exact duplicates); header renaming is last.
    _PROCESSING_ORDER: tuple[CleaningOperation, ...] = (
        CleaningOperation.TYPE_COERCION,
        CleaningOperation.CASE_NORMALIZATION,
        CleaningOperation.DEDUPLICATION,
        CleaningOperation.HEADER_NORMALIZATION,
    )

    def clean(
        self,
        df: pd.DataFrame,
        quality_report: DataQualityReport,
        pipeline_run_id: str,
    ) -> tuple[pd.DataFrame, CleaningResult]:
        """Clean a working copy of ``df`` per the autonomous findings in the report.

        Returns ``(cleaned_df, result)``. ``df`` itself is never modified. Only
        ``agent_autonomous`` findings are acted on; everything else is left
        exactly as-is. An empty or all-non-autonomous report yields the frame
        deep-copied and a result with no actions.
        """
        log = structlog.get_logger().bind(pipeline_run_id=pipeline_run_id)

        # --- Working-copy invariant: deep copy at the boundary. ---
        working = df.copy(deep=True)
        rows_before, columns_before = working.shape

        defects = quality_report.defects
        autonomous = [
            d
            for d in defects
            if d.remediation_class == RemediationClass.AGENT_AUTONOMOUS
        ]
        log.info(
            "cleaning_started",
            total_findings=len(defects),
            autonomous_findings=len(autonomous),
            rows=rows_before,
            columns=columns_before,
        )

        actions: list[CleaningAction] = []

        for operation in self._PROCESSING_ORDER:
            bucket = [
                d
                for d in autonomous
                if self._OPERATION_BY_DEFECT_TYPE.get(d.defect_type) == operation
            ]
            if not bucket:
                continue

            if operation == CleaningOperation.HEADER_NORMALIZATION:
                # Frame-level op: one action for all flagged columns at once so
                # collision suffixing is consistent across the whole header row.
                working, action = self._normalize_headers(bucket, working, log)
                actions.append(action)
                continue

            # Per-column / per-finding ops, sorted for deterministic order.
            for defect in sorted(
                bucket,
                key=lambda d: (d.affected_columns[0] if d.affected_columns else ""),
            ):
                try:
                    working, action = self._apply_operation(
                        defect, operation, working, log
                    )
                except CleaningEngineError:
                    # Contract violation — must surface, not be swallowed. The
                    # working copy for THIS op was not assigned, so the frame is
                    # at its last-good state and the original is untouched.
                    raise
                except Exception as exc:  # noqa: BLE001 - captured as safe provenance
                    actions.append(
                        self._failed_action(defect, operation, exc)
                    )
                    log.warning(
                        "cleaning_action_failed",
                        operation=operation.value,
                        defect_type=defect.defect_type,
                        error_type=type(exc).__name__,
                    )
                    continue
                actions.append(action)

        # Fail-closed provenance: any autonomous finding whose defect_type has no
        # registered operation is recorded as SKIPPED (zero data change) rather
        # than silently ignored. With the current classifier this cannot happen
        # (only the four registered types are autonomous); a SKIPPED entry here
        # is a visible signal of classifier/engine drift.
        for defect in sorted(
            (
                d
                for d in autonomous
                if self._OPERATION_BY_DEFECT_TYPE.get(d.defect_type) is None
            ),
            key=lambda d: (d.defect_type, d.affected_columns[0] if d.affected_columns else ""),
        ):
            actions.append(self._skipped_action(defect))
            log.warning(
                "cleaning_action_skipped",
                defect_type=defect.defect_type,
                reason="no_registered_autonomous_operation",
            )

        rows_after, columns_after = working.shape
        log.info(
            "cleaning_completed",
            actions=len(actions),
            rows_before=rows_before,
            rows_after=rows_after,
            columns_before=columns_before,
            columns_after=columns_after,
        )

        result = CleaningResult(
            pipeline_run_id=pipeline_run_id,
            total_findings=len(defects),
            autonomous_findings=len(autonomous),
            actions=actions,
            rows_before=rows_before,
            rows_after=rows_after,
            columns_before=columns_before,
            columns_after=columns_after,
            cleaned_at=datetime.now(timezone.utc).isoformat(),
        )
        return working, result

    # ------------------------------------------------------------------
    # Private per-finding dispatch — the independent second guard (AC 2).
    # ------------------------------------------------------------------

    def _apply_operation(
        self,
        defect: DataQualityDefect,
        operation: CleaningOperation,
        working: pd.DataFrame,
        log: structlog.stdlib.BoundLogger,
    ) -> tuple[pd.DataFrame, CleaningAction]:
        """Apply one column/row operation; refuse anything non-autonomous.

        Independently re-checks the finding's class (defense in depth: even if a
        caller bypasses :meth:`clean`'s filter, a non-``agent_autonomous`` finding
        raises here rather than mutating data). Also refuses a ``defect_type``
        with no registered autonomous operation.
        """
        if defect.remediation_class != RemediationClass.AGENT_AUTONOMOUS:
            raise CleaningEngineError(
                "refusing to clean a non-autonomous finding: "
                f"defect_type={defect.defect_type!r}, "
                f"remediation_class={defect.remediation_class.value!r}"
            )
        if self._OPERATION_BY_DEFECT_TYPE.get(defect.defect_type) is None:
            raise CleaningEngineError(
                "no autonomous operation registered for "
                f"defect_type={defect.defect_type!r}"
            )

        if operation == CleaningOperation.DEDUPLICATION:
            return self._deduplicate(defect, working, log)
        if operation == CleaningOperation.CASE_NORMALIZATION:
            return self._normalize_case(defect, working, log)
        if operation == CleaningOperation.TYPE_COERCION:
            return self._coerce_types(defect, working, log)
        # HEADER_NORMALIZATION is handled at the batch level in clean();
        # reaching here means a single-finding dispatch was requested for it.
        raise CleaningEngineError(
            f"operation {operation.value!r} is not dispatched per-finding"
        )

    def _deduplicate(
        self,
        defect: DataQualityDefect,
        working: pd.DataFrame,
        log: structlog.stdlib.BoundLogger,
    ) -> tuple[pd.DataFrame, CleaningAction]:
        deduped, removed = prim.drop_exact_duplicates(working)
        log.info(
            "cleaning_action_applied",
            operation=CleaningOperation.DEDUPLICATION.value,
            rows_removed=removed,
        )
        action = CleaningAction(
            operation=CleaningOperation.DEDUPLICATION,
            defect_type=defect.defect_type,
            remediation_class=defect.remediation_class,
            status=CleaningStatus.APPLIED,
            scope=CleaningScope.ROW,
            target_columns=[str(c) for c in working.columns],
            rows_affected=removed,
            before_state=f"{len(working)} rows",
            after_state=f"{len(deduped)} rows",
            rule="drop exact duplicate rows, keep first occurrence, preserve order",
            detail=f"Removed {removed} exact duplicate row(s).",
        )
        return deduped, action

    def _normalize_case(
        self,
        defect: DataQualityDefect,
        working: pd.DataFrame,
        log: structlog.stdlib.BoundLogger,
    ) -> tuple[pd.DataFrame, CleaningAction]:
        column = defect.affected_columns[0]
        new_series, meta = prim.normalize_case(working[column])
        updated = working.copy()
        updated[column] = new_series
        mapping: dict[str, str] = meta["mapping"]
        log.info(
            "cleaning_action_applied",
            operation=CleaningOperation.CASE_NORMALIZATION.value,
            column=column,
            values_changed=meta["values_changed"],
            variants_collapsed=len(mapping),
        )
        action = CleaningAction(
            operation=CleaningOperation.CASE_NORMALIZATION,
            defect_type=defect.defect_type,
            remediation_class=defect.remediation_class,
            status=CleaningStatus.APPLIED,
            scope=CleaningScope.COLUMN,
            target_columns=[column],
            values_changed=meta["values_changed"],
            value_mapping=mapping,
            before_state=f"{len(mapping)} non-canonical case variant(s)",
            after_state="canonical case per value group",
            rule=(
                "collapse case variants to the most frequent original variant; "
                "ties break to the lexicographically smallest variant"
            ),
            detail=(
                f"Normalized casing in '{column}': "
                f"{meta['values_changed']} value(s) rewritten across "
                f"{len(mapping)} variant(s)."
            ),
        )
        return updated, action

    def _coerce_types(
        self,
        defect: DataQualityDefect,
        working: pd.DataFrame,
        log: structlog.stdlib.BoundLogger,
    ) -> tuple[pd.DataFrame, CleaningAction]:
        column = defect.affected_columns[0]
        before_dtype = str(working[column].dtype)
        new_series, meta = prim.coerce_column_type(working[column])
        updated = working.copy()
        updated[column] = new_series
        after_dtype = str(updated[column].dtype)
        log.info(
            "cleaning_action_applied",
            operation=CleaningOperation.TYPE_COERCION.value,
            column=column,
            kind=meta["kind"],
            values_changed=meta["values_changed"],
            uncoerced=meta["uncoerced"],
        )
        action = CleaningAction(
            operation=CleaningOperation.TYPE_COERCION,
            defect_type=defect.defect_type,
            remediation_class=defect.remediation_class,
            status=CleaningStatus.APPLIED,
            scope=CleaningScope.COLUMN,
            target_columns=[column],
            values_changed=meta["values_changed"],
            before_state=f"dtype={before_dtype}",
            after_state=f"dtype={after_dtype}",
            parameters={
                "kind": str(meta["kind"]),
                "dominant_type": str(meta["dominant_type"]),
                "uncoerced": str(meta["uncoerced"]),
            },
            rule=(
                "strip whitespace, then coerce minority values toward the "
                "dominant type; values that fail to coerce keep their original "
                "(never nulled)"
            ),
            detail=(
                f"Coerced '{column}' toward {meta['dominant_type']} "
                f"({meta['kind']}): {meta['values_changed']} value(s) rewritten, "
                f"{meta['uncoerced']} left unchanged (uncoercible)."
            ),
        )
        return updated, action

    def _normalize_headers(
        self,
        defects: list[DataQualityDefect],
        working: pd.DataFrame,
        log: structlog.stdlib.BoundLogger,
    ) -> tuple[pd.DataFrame, CleaningAction]:
        """Normalize ALL flagged headers in one pass (collision-safe across frame)."""
        # Independent guard applies here too — every finding in the batch must be
        # autonomous (clean() only ever passes autonomous ones, but assert it).
        for defect in defects:
            if defect.remediation_class != RemediationClass.AGENT_AUTONOMOUS:
                raise CleaningEngineError(
                    "refusing to normalize a header for a non-autonomous finding: "
                    f"defect_type={defect.defect_type!r}, "
                    f"remediation_class={defect.remediation_class.value!r}"
                )

        new_columns, mapping = prim.normalize_column_names(list(working.columns))
        updated = working.copy()
        updated.columns = new_columns
        log.info(
            "cleaning_action_applied",
            operation=CleaningOperation.HEADER_NORMALIZATION.value,
            columns_renamed=len(mapping),
        )
        action = CleaningAction(
            operation=CleaningOperation.HEADER_NORMALIZATION,
            defect_type="column_naming",
            remediation_class=RemediationClass.AGENT_AUTONOMOUS,
            status=CleaningStatus.APPLIED,
            scope=CleaningScope.TABLE,
            target_columns=list(mapping.keys()),
            rows_affected=0,
            values_changed=len(mapping),
            value_mapping=mapping,
            before_state=f"{len(mapping)} non-conforming header(s)",
            after_state="normalized snake_case headers",
            rule=(
                "strip, collapse non-[A-Za-z0-9_] runs to '_', lowercase; "
                "empty/numeric -> column_{position}; collisions suffixed _2, _3, …"
            ),
            detail=f"Renamed {len(mapping)} column header(s).",
        )
        return updated, action

    def _skipped_action(self, defect: DataQualityDefect) -> CleaningAction:
        """Build a SKIPPED action for an autonomous finding with no registered op."""
        return CleaningAction(
            operation=CleaningOperation.NO_OP,  # nothing ran
            defect_type=defect.defect_type,
            remediation_class=defect.remediation_class,
            status=CleaningStatus.SKIPPED,
            scope=CleaningScope.COLUMN,
            target_columns=list(defect.affected_columns),
            rule="no registered autonomous operation for this defect_type — failing closed",
            detail=(
                f"Finding '{defect.defect_type}' was classified autonomous but the "
                "engine has no operation for it; skipped without modifying data."
            ),
        )

    def _failed_action(
        self,
        defect: DataQualityDefect,
        operation: CleaningOperation,
        exc: Exception,
    ) -> CleaningAction:
        """Build a FAILED action with safe error info (type + message only)."""
        return CleaningAction(
            operation=operation,
            defect_type=defect.defect_type,
            remediation_class=defect.remediation_class,
            status=CleaningStatus.FAILED,
            scope=CleaningScope.COLUMN,
            target_columns=list(defect.affected_columns),
            rule="operation raised; working copy left at last-good state",
            detail=f"Cleaning action for '{defect.defect_type}' did not complete.",
            error=f"{type(exc).__name__}: {exc}",
        )
