# Epic 12 — Adapter Layer, Scoring Engine & Scoring Calibration

<!-- Roadmap restructure 2026-07-09. PRD Phase 8 + 12-B (calibration merged in). 6 stories,
     ~60% Opus. ALL loop_eligible: false. Read-only narrative; sprint-status.yaml is
     authoritative. Day counts: TBD. Begins ONLY after the PRE-VERTICAL GATE (Epics 3, 8, 9, 10) closes. -->

**PRD mapping:** Phase 8 (Adapter + Scoring) + Phase 12-B (scoring backtesting, weight
optimization, adapter-specific predictions, merged in).

**PRE-VERTICAL GATE:** Epics 3 (cleaning), 8 (descriptive/predictive/prescriptive), 9
(diagnostic), 10 (simulation) must ALL close before Epic 12 begins.

## Stories

| # | Story | Size | Model |
|---|---|---|---|
| 12.1 | BaseAdapter Abstract Interface | M | Opus |
| 12.2 | Scoring Engine Core | L | Opus |
| 12.3 | DQA Penalty Bridge | M | Opus |
| 12.4 | Generic Mode / Backward Compatibility | M | Opus |
| 12.5 | Scoring Backtesting & Weight Optimization | L | Opus |
| 12.6 | Adapter-Specific Predictions | M | Opus |

ALL false — scoring correctness is client-facing and Opus-tier.

## Constraints

- Real estate adapter is DEFERRED (see prd-epic-reconciliation.md), not cancelled. 12.1's
  BaseAdapter is what makes adding it (and demand-driven verticals after Epic 15) cheap.
- **12.4** — no adapter configured → zero regressions. §8 backward-compat rule.
- **12.5** — deterministic optimization (grid search, convex solve) ONLY. Weights must PRINT.
  If it requires gradient-based fitting with regularization, it does not ship. §2.1 — every
  score shows its formula. **No sklearn for client-facing scores** (Amendment 6).
