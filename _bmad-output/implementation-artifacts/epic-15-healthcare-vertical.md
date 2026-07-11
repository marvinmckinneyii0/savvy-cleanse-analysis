# Epic 15 — Healthcare Vertical

<!-- Roadmap restructure 2026-07-09. PRD Phase 11. Scope per PRD. Read-only narrative;
     sprint-status.yaml is authoritative. Day counts: TBD. Story breakdown per PRD Phase 11
     at story-write time — ALL stories loop_eligible: false (regulated vertical, no exceptions). -->

**PRD mapping:** Phase 11 (Healthcare Vertical — Outcome Scoring + Anonymization).

**Vertical order:** marketing (Epic 13) → financial (Epic 14) → **healthcare (Epic 15)**.
After Epic 15, real estate rejoins the vertical queue (deferred, not cancelled), demand-driven.

## Scope (per PRD Phase 11)

Healthcare adapter (patient flow, readmission, resource utilization → Outcome Score,
Efficiency Index, Capacity Utilization, Readmission Risk, Cost Variance). Anonymization layer
strips PHI before any processing. No PHI in any output. Outcome-based scoring weighted toward
patient outcomes and efficiency.

## Constraints

- **Anonymization layer strips PHI before ANY processing** — HIPAA-aligned data handling
  (formal certification out of scope per §10 / §15).
- Governance advisory (Epic 11) extended here for **HIPAA / PHI.**
- **NO sklearn without an explicit explainability architecture (Amendment 6).**
- All stories `loop_eligible: false` — regulated vertical, no exceptions.

## Status: DEFERRED PENDING RESEARCH (deliberate decision, 2026-07-11)

This epic is intentionally an unscoped placeholder — **no story breakdown, no sizing, no
meaningful loop_eligible values** — until real market research and client validation in the
healthcare sector inform its actual scope. This is a decision, not a gap or oversight; do NOT
story-file it until explicitly told to. It does NOT change sequencing before Epic 13 —
Marketing was already first in the vertical queue regardless.
