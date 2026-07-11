# Epic 7 — Admin Control Plane (+ Pricing Agent)

<!-- Roadmap restructure 2026-07-09. PRD Phase 5 (Admin Control Plane). RENUMBERED from
     Epic 6, + net-new Pricing Agent. 8 stories, ~55% Opus. Read-only narrative;
     sprint-status.yaml is authoritative. Day counts: TBD — requires velocity baseline. -->

**PRD mapping:** Phase 5 (Admin Control Plane). Renumbered from Epic 6.

## Stories

| # | Story | Size | Model | loop_eligible |
|---|---|---|---|---|
| 7.1 | Role Hierarchy & Admin Auth | M | Opus | false (auth surface) |
| 7.2 | Audit Log (immutable, append-only) | M | Opus | false (correct-by-construction) |
| 7.3 | Tenant Management | M | Sonnet | true (CRUD-shaped) |
| 7.4 | User Management & API Tokens | M | Opus | false (token scoping — security) |
| 7.5 | System Health Dashboard | S | Sonnet | true (read-only) |
| 7.6 | Billing Overview | M | Sonnet | true (read-only display) |
| 7.7 | Customer Journey Tracking | M | Sonnet | true (consumes 4.10) |
| 7.8 | Pricing Agent | L | Opus | false (NET-NEW; billing consequence) |

## Story notes

**7.7 SCOPE** — a CROSS-TENANT ANALYTICS VIEW, not an onboarding workflow. Six stages (Signup
→ Activation → Engaged → Expanded → At Risk → Churned), funnel visualization, per-tenant
timeline, cohort analysis. It tells you "37% of tenants stall between Signup and Activation."
It does not onboard. Stage definitions — particularly `activated` — are CONSUMED FROM Story
4.10. Do NOT redefine them here. Defining activation twice, differently, in a customer-facing
flow and an analytics view produces numbers that never reconcile.

**7.8 Pricing Agent (NET-NEW)** — Internal Savvy Analytics use only. Scans SMB analytics/
data-quality market. Models consequences of tier changes: margin impact, churn at current
elasticity, tier-migration risk. Outputs structured recommendation JSON. **RECOMMENDS; NEVER
EXECUTES.** No code path may exist by which the agent mutates a price. Every recommendation
and every resulting human price change writes to 7.2's audit log. Architecturally reuses the
Recommendation Agent pattern (Epic 8) — build the pattern here, Epic 8 reuses it. **No n8n.**
Graduates to a client-facing capability in Epic 13 (Story 13.6; ~60% logic reuse, ~40%
net-new client-data ingestion). Do not assume the Epic 7 build delivers the client version
for free.
