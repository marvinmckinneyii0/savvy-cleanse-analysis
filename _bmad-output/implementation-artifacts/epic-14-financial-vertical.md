# Epic 14 — Financial Vertical

<!-- Roadmap restructure 2026-07-09. PRD Phase 10. Scope per PRD. Read-only narrative;
     sprint-status.yaml is authoritative. Day counts: TBD. Story breakdown per PRD Phase 10
     at story-write time — ALL stories loop_eligible: false (regulated vertical, no exceptions). -->

**PRD mapping:** Phase 10 (Financial Vertical — Banking + Compliance-Aware Scoring).

**Vertical order:** marketing (Epic 13) → **financial (Epic 14)** → healthcare (Epic 15).

## Scope (per PRD Phase 10)

Financial adapter (transaction data, portfolios, loan books → Risk Score, Return Metric,
Compliance Flag, Concentration Index, Liquidity Ratio). Compliance-aware DQA extensions (PII
detection, currency validation, suspicious pattern flagging). Regulatory report templates.
Risk-adjusted scoring.

## Constraints

- Governance advisory (Epic 11) extended here for **GLBA / adverse-action reason codes.**
- **NO sklearn without an explicit explainability architecture (Amendment 6).** Financial
  scores are client-facing and adverse-action reason codes must be defensible — weights must
  print.
- All stories `loop_eligible: false` — regulated vertical, no exceptions.
- Anonymization/PII handling per §14.1 Phase 10 and §15 (GLBA, US financial).

Story-level breakdown is authored per PRD Phase 10 when this epic is scheduled (after Epic 15
in the vertical queue's gating, per the pre-vertical gate and vertical order).
