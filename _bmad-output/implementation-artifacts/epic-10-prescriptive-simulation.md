# Epic 10 — Prescriptive Layer (Simulation & Scenario Modeling)

<!-- Roadmap restructure 2026-07-09. §14 Simulation: VISION → IMPLEMENTATION (Amendment 5).
     6 stories, ~75% Opus. ALL loop_eligible: false. Read-only narrative; sprint-status.yaml
     is authoritative. Day counts: TBD. Part of the PRE-VERTICAL GATE. -->

**PRD mapping:** §14 Simulation / what-if scenario modeling, promoted from vision to
implementation (Amendment 5).

## Stories

| # | Story | Size | Model | loop_eligible |
|---|---|---|---|---|
| 10.1 | Scenario Definition Schema | M | Opus | false |
| 10.2 | Deterministic Projection Engine | L | Opus | false |
| 10.3 | Sensitivity Analysis | L | Opus | false |
| 10.4 | Constraint Modeling | M | Opus | false |
| 10.5 | Scenario Comparison & Ranking | M | Opus | false |
| 10.6 | Prescriptive Narrative Integration | M | Sonnet | false |

ALL false — deterministic-projection correctness is load-bearing; Opus-tier.

## LOAD-BEARING CONSTRAINT (state in story files; must not drift)

Simulation projects DETERMINISTICALLY from stated assumptions. It does NOT predict.
**Monte Carlo and stochastic sampling are EXCLUDED — they break §2.1.** Every output carries
its assumptions as an explicit artifact, exactly as §2.1 requires evidence trails for
insights. A projection is "if you change X by 20%, the model computes Y." Anything else sells
forecasting dressed as certainty.

## Story rationale

- **10.4** — without constraint modeling the engine confidently recommends impossible things
  (allocating 130% of budget).
- **10.3** is the highest-value story: sensitivity analysis is what makes prescriptive
  recommendations justified rather than asserted.
- **10.6** — the LLM narrates the computed projection; it never computes it (§2.1).
- Epic 10 owns quantified impact estimation (the §16.4 "+$380K" example), NOT Epic 8's
  Recommendation Agent (which does opportunity identification only).
