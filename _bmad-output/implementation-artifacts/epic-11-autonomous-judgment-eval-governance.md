# Epic 11 — Autonomous Judgment (Tier 4) + Eval Harness + Governance Advisory

<!-- Roadmap restructure 2026-07-09. NET-NEW (does not exist in the PRD). 10 stories, ~70%
     Opus. ALL loop_eligible: false. Read-only narrative; sprint-status.yaml is authoritative.
     Day counts: TBD — requires velocity baseline. ENTERPRISE ONLY. -->

**PRD mapping:** none — net-new. Autonomous agent judgment on ambiguous data ("Tier 4"),
the eval harness that gates it, and Governance Advisory.

## Stories

| # | Story | Size | Model |
|---|---|---|---|
| 11.1 | Eval Harness Infrastructure | L | Opus |
| 11.2 | Gold-Standard Benchmark Datasets | L | Opus |
| 11.3 | Confidence Scoring & Threshold Config | M | Opus |
| 11.4 | Blast-Radius Cap & Halt Logic | M | Opus |
| 11.5 | Decision Traceability Artifact | L | Opus |
| 11.6 | Consequence Disclosure per Finding Type | M | Sonnet |
| 11.7 | Escalation Trigger & Self-Disable | M | Opus |
| 11.8 | Jurisdiction Detection & Risk Classification | L | Opus |
| 11.9 | Pre-Flight Configuration Warnings | M | Opus |
| 11.10 | Defensible Decision Record | M | Sonnet |

ALL loop_eligible: false — Tier-4/eval/governance correctness is not unit-test-catchable;
Enterprise liability surface.

## Story notes

- **11.2** — labeled near-duplicate pairs with known-correct merge/keep decisions; outlier
  sets with known-correct treatment; orphaned-FK scenarios with known-correct resolution.
- **11.3** — below threshold → auto-defer to Tier 3 human, EVEN WITH TIER 4 ENABLED.
- **11.4** — ceiling on % rows / % column autonomously touched per run. Halt + human
  confirmation to proceed. Prevents a single bad classification cascading across a dataset.
- **11.5** — DISTINCT ARTIFACT from the healing manifest. Manifest logs WHAT changed; this
  logs WHY — evidence considered, confidence score, REJECTED ALTERNATIVES, reasoning chain.
  Different audiences, different artifacts. Queryable in plain language via Story 8.7's
  findings-interrogation.
- **11.6** — specific, per-finding-type, pre-enablement. NOT a generic disclaimer. "Orphaned
  FK auto-nulled" and "outlier auto-capped" carry different downstream risk profiles.
- **11.7** — degrading DECISION quality (not data drift) → auto-disable + notify.

## Governance Advisory (11.8–11.10, Enterprise)

Jurisdiction detection from tenant config and data characteristics, mapped against §15's law
registry (already written, currently underused). Risk classification of the client's own
configuration per EU AI Act §15.1. Pre-flight warnings before consequential actions — Tier 4
enablement, PII-containing datasets fed to LLM narrative, retention configured beyond LGPD's
15-day DSAR window.

**HARD BOUNDARY:** NEVER legal advice. NEVER "you are compliant." Only "this configuration
has characteristics that commonly trigger X — consult counsel." A vendor telling an SMB
they're GDPR compliant and being wrong is a worse liability than the non-compliance. §15's
own header: "a reference for architectural decisions, not legal advice."

## Determinism & tier boundaries

- **Determinism boundary:** the agent selects among deterministically-computed candidate
  remediations. It never generates values (Amendment 2).
- Tier 4 inherits working-copy-only. NO EXCEPTIONS.
- ENTERPRISE ONLY. Liability decision, not pricing.
- **SHIP GATE:** precision/recall tracked CONTINUOUSLY against 11.2's benchmarks per finding
  type — not a one-time pre-launch test. Gated on accuracy thresholds, NOT on a date. No
  client enables Tier 4 without an accepted consequence disclosure recorded per finding type.
- The eval harness built here is reused by the backlogged extraction epic.
- **sklearn PERMITTED here per Amendment 6, narrow scope: near-duplicate similarity detection
  only.** This is where ML genuinely outperforms any rule. Eval-gated. Not for client-facing
  scores.
