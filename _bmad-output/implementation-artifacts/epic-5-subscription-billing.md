# Epic 5 — Subscription Billing

<!-- Roadmap restructure 2026-07-09. PRD Phase 4. RENUMBERED from Epic 4. 4 stories.
     Read-only narrative; sprint-status.yaml is authoritative. Day counts: TBD. -->

**PRD mapping:** Phase 4 (Monetization). Renumbered from Epic 4.

## Stories

| # | Story | loop_eligible |
|---|---|---|
| 5.1 | Stripe Integration & Plan Tiers | false |
| 5.2 | Webhook Handling & Subscription Lifecycle | false |
| 5.3 | Usage Tracking & Capability Gating (SCOPE WIDENED) | false |
| 5.4 | Billing UI & Free Trial | false |

All false — billing/security surface.

## Amendments

**5.3 SCOPE WIDENED:** usage tracking AND capability gating. Middleware checks tier before
allowing an API call. Capability flags alongside quota flags — same code path. Filters
visualizations on `analysis_class` (schema-extensions-spec.md), NEVER on a hardcoded chart
allowlist. Without the `analysis_class` tag, Epic 5 hardcodes which chart types belong to
which tier — a list that drifts from the analytics ladder the moment Epic 9 or 10 adds a
chart. Tag the chart with what produced it; gate on the tag.

**Tiers:** the monetization table is PRD §3.2 as replaced by Amendment 7 (see
saint-master-prd.md). The frontend's $29 "Pro" tier is INCORRECT and must be corrected to
match ($149 Professional). Tier 2 cleaning and cleaned-data export ship together (both
Starter). Tier 4 is Enterprise-only (liability, not pricing). Vertical adapters (Epics
12–15) are NOT in the tier table.
