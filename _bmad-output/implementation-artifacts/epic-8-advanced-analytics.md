# Epic 8 — Advanced Analytics, Predictive Layer & Self-Service API

<!-- Roadmap restructure 2026-07-09. PRD Phase 6 + 12-A (forecasting merged in). RENUMBERED
     from Epic 7, expanded. 9 stories, ~50% Opus. Read-only narrative; sprint-status.yaml is
     authoritative. Day counts: TBD — requires velocity baseline. -->

**PRD mapping:** Phase 6 (Intelligence) + Phase 12-A (forecasting/confidence intervals/auto
model selection/accuracy scoring, merged in). Renumbered from Epic 7, expanded.

**EPIC 8 DoD IS THE PRE-VERTICAL GATE (with Epics 3, 9, 10).**

## Stories

| # | Story | Size | Model | loop_eligible |
|---|---|---|---|---|
| 8.1 | Advanced Analytics Engine (correlation, cohort, significance) | L | Opus | false |
| 8.2 | Forecasting Core (Prophet/statsmodels) | L | Opus | false |
| 8.3 | Confidence Intervals & Forecast Accuracy Scoring | L | Opus | false |
| 8.4 | Auto Model Selection (deterministic rule over fit metrics) | M | Opus | false |
| 8.5 | Recommendation Agent | L | Opus | false |
| 8.6 | Custom Monitoring Rules & Digest Reports | M | Sonnet | true |
| 8.7 | Natural Language Querying | L | Opus | false |
| 8.8 | Client Self-Service & Report Customization | M | Sonnet | true |
| 8.9 | Versioned REST API & Webhooks | M | Sonnet | true |

## Story notes

**8.1** provides the statistical foundation Epic 13's A/B intelligence builds on.

**8.4** — deterministic selection rule over statistical fit metrics. **No sklearn.**

**8.5 SCOPE NARROWED** — opportunity identification ONLY. Quantified impact estimation moves
to Epic 10 (simulation). §16.4's example — "Reallocate 20% of Region B spend... Estimated
impact: +$380K" — is a SIMULATION output, not a Recommendation Agent output. Do not build
impact estimation twice. Reuses the Recommendation Agent pattern first built in Story 7.8.

**8.7 GUIDED ANALYTICS SCOPE** — automated report + optional NL assist. PULL, NOT PUSH. No
goal-refinement wizard. No smart prompts. User invokes help when they want it. NL querying
must be reachable from report and dashboard contexts (not standalone only), and must
interrogate FINDINGS ("why was this column flagged?") as well as underlying data.
Findings-querying pairs with Epic 11's decision-traceability artifact (Story 11.5) — same
infrastructure, different consumer. Safety-critical (LLM generates pandas ops, not answers;
results from actual data).

**Forecasting (12-A merged):** Prophet/statsmodels time-series decompositions are PERMITTED
per Amendment 6 (inspectable — trend/seasonality/changepoints). All deterministic.
