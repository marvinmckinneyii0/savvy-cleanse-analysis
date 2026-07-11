# Epic 6 — Multi-Tenant Scale & Production Hardening

<!-- Roadmap restructure 2026-07-09. PRD Phase 5. RENUMBERED from Epic 5. 5 stories.
     Read-only narrative; sprint-status.yaml is authoritative. Day counts: TBD. -->

**PRD mapping:** Phase 5 (Scale). Renumbered from Epic 5.

## Stories

| # | Story | loop_eligible |
|---|---|---|
| 6.1 | Multi-Tenant Data Isolation (RLS) | false |
| 6.2 | Async Processing Pipeline | false |
| 6.3 | Observability & Error Tracking | false |
| 6.4 | Security Hardening & OWASP Review | false |
| 6.5 | Containerized Deployment & CI/CD | false |

All false — security/infra correctness surface.

## Amendment — LATENCY / QUEUEING (6.2)

Epic 6's Celery/Redis async layer is **FIFO with per-tenant fairness. NO priority queuing by
tier.** §3.2's "priority processing" is STRUCK. Priority queuing starves free tenants as paid
load grows, degrading the conversion funnel precisely when the business succeeds. **Gate on
quota, not speed.** Status polling for users; reports and monitoring jobs run asynchronously.

Baseline store migrates from file-based JSON to PostgreSQL here (same interface, different
backend). DSAR/erasure (§14.1 Phase 5) — export and deletion APIs, right-to-erasure, DPA
template — land in this epic; cleaned-data export (Story 3.6) depends on this retention/
erasure coverage.
