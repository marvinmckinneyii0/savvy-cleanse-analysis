# Epic 13 — Marketing Vertical + A/B Testing Intelligence

<!-- Roadmap restructure 2026-07-09. PRD Phase 8/§17 (Marketing as first vertical) + §14 A/B
     intelligence (promoted, Amendment 5). 9 stories, ~60% Opus. Read-only narrative;
     sprint-status.yaml is authoritative. Day counts: TBD — requires velocity baseline. -->

**PRD mapping:** Phase 8 / §17 Marketing Vertical (marketing replaces real estate as first
vertical) + §14 A/B testing intelligence (promoted to implementation WITHIN this epic).

## Stories

| # | Story | Size | Model | loop_eligible |
|---|---|---|---|---|
| 13.1 | Marketing Adapter (→ ES, LS, CS, FV, CR per §17.2) | L | Opus | false |
| 13.2 | MOS Scoring Formula & Default Weights | M | Opus | false |
| 13.3 | Lead Scoring Tiers | S | Sonnet | true |
| 13.4 | CRM / Outreach Pipeline Integration | L | Sonnet | true |
| 13.5 | Campaign Analysis & Funnel Velocity | M | Sonnet | true |
| 13.6 | Pricing Agent → Client-Facing Graduation | L | Opus | false |
| 13.7 | Experiment Schema & Ingestion | M | Opus | false |
| 13.8 | Significance Testing & Multiple-Comparison Correction | L | Opus | false |
| 13.9 | Power Analysis & Result Interpretation | L | Opus | false |

## Scoring

```
MOS = (w1*ES + w2*LS + w3*CS + w4*FV - w5*CR) * (1 - dqa_penalty)
Hot >0.75 | Warm 0.50–0.75 | Cool 0.25–0.50 | Cold <0.25
```

- **13.6 is DISTINCT from 13.2.** MOS scores LEADS. Pricing scores OFFERS. Requires operating
  history from Epic 7's internal pricing agent (Story 7.8); ~60% logic reuse, ~40% net-new
  client-data ingestion.
- **13.7** — variant assignment, exposure, outcome metric, timestamp. Pydantic-validated per
  §8. Must accommodate unequal allocation and multi-variant, not just A/B.

## A/B testing intelligence (13.7–13.9) — statistically load-bearing

Builds on Epic 8's Story 8.1 statistical foundation.

- **13.8** — **Benjamini–Hochberg (FDR) as DEFAULT;** Bonferroni available; correction method
  chosen explicitly and PRINTED in output. FDR is the appropriate error framework for SMB
  marketing experimentation (Bonferroni is overly conservative — 20 comparisons at α=0.05
  demands p<0.0025 per test — and misses commercially meaningful effects; marketers optimize,
  they do not prove safety). **SEQUENTIAL TESTING / PEEKING CORRECTION IS IN SCOPE HERE** —
  peeking is a MORE common failure than multiple comparisons (marketers check daily and stop
  when significant). Alpha spending or always-valid confidence sequences. Split into its own
  story only if it proves large.
- **13.9** — each experiment output MUST carry: minimum detectable effect at achieved sample
  size (stated α, β); achieved power for the effect size actually observed; whether the
  experiment was adequately powered BEFORE it ran (not merely whether it reached significance
  after); a confidence interval on the effect (not only a p-value); and **EXPLICIT LABELING
  when a null result is UNDERPOWERED rather than a true null.** That last item is the point:
  telling an SMB "no significant difference" on an experiment that could not have detected a
  15% lift is actively misleading. §2.1 obligates distinguishing "we found nothing" from "we
  could not have found anything."
- **13.8 and 13.9 are both L and statistically load-bearing.** Errors cascade into client
  decisions and are NOT caught by unit tests. Opus with human review → loop_eligible: false.

All deterministic. **scipy.stats and statsmodels only. No sklearn.**

## Dogfooding (§17)

Savvy Analytics uses this on its own pipeline before selling it. A/B intelligence must be
built against real campaign data from that loop, not synthetic data — power-analysis
miscalibration is undetectable on data generated to satisfy it.

## Note on scope

General hypothesis testing (§14) REMAINS vision scope while A/B intelligence promotes. A/B is
a bounded experimental design; general hypothesis testing is open-ended. One does not imply
the other.
