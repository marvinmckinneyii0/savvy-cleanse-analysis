# SAINT Epic 4.1 — Organization / Client / Project Schema Design Package

**Status:** DRAFT, documentation only; Option B architectural direction accepted by owner, **physical schema and story scope not yet approved**.  
**Prepared:** 2026-11-11. **Implementation owner:** to be assigned through canonical BMAD Story 4.1 after human review.  
**Related:** [CI-ADR-001](adr-proposed-agency-client-tenancy-2026-11-11.md) · [Option B roadmap](saint-context-intelligence-option-b-proposal-2026-11-11.md) · [review and migration checklist](epic-4-1-schema-migration-security-review.md).  
**Canonical references:** [schema extensions](../../_bmad-output/implementation-artifacts/schema-extensions-spec.md), [Epic 4](../../_bmad-output/implementation-artifacts/epic-4-web-application.md), [Epic 6](../../_bmad-output/implementation-artifacts/epic-6-multitenant-scale.md), [Epic 7](../../_bmad-output/implementation-artifacts/epic-7-admin-control-plane.md), [AGENTS.md](../../AGENTS.md), [sprint status](../../_bmad-output/implementation-artifacts/sprint-status.yaml).

> **Scope boundary:** This document specifies potential schemas, constraints, and tests. It is **not** a database migration, a migration authorization, a change to the PRD, a new canonical BMAD story, or authorization to promote Story 4.1, change loop eligibility, merge, or deploy. The November 13 concierge beta continues to run manually and does not depend on this architecture.

## 1. Decision summary

**Organization = tenant. Client = optional tenant-owned workspace. Project = canonical parent of analysis.**

- Organizations are either agencies or direct business customers. An agency is a kind of organization, **not a separate first-class tenant type**.
- An agency can have multiple client workspaces; a direct business need not create any client workspace to use SAINT.
- A project belongs to **exactly one organization** and may belong to **at most one client workspace in the same organization**. Projects remain the canonical parent of cleaning policy, baselines, rules, source metadata, runs and report artifacts as already required by Epic 4.1 / Task 4c.
- Business context, trusted metric definitions and analysis evidence are scoped to authorized projects. Agency-level **templates** can be reused by explicit selection; client observations and outcomes never inherit across projects automatically.
- Organization membership **does not grant** blanket client/project data access. Read/write/export rights are derived server-side from verified roles and scoped grants; an owner may administer access without implicitly reading raw customer data.
- New persistent tenant-scoped records should have **non-null organization IDs from their introduction**, even if historical architecture notes contemplated nullable tenant IDs before Epic 6. If the existing ORM or Supabase schema cannot enforce this safely, the story must halt for a deliberate design resolution.
- Adopt **Organization** terminology at the domain/API layer, with the existing \`tenant_id\` field or \`organization_id\` relationship mapped explicitly by an approved adapter. Do not create parallel unsynchronized tenant and organization IDs.

### Proposed relational ownership diagram

    auth_principal (verified auth user / service principal)
      |
      +-- organization_membership --> organization / tenant
                                          |
                                          +-- client_workspace (optional; same organization)
                                          |      |
                                          |      +-- project (canonical; org + optional client)
                                          |
                                          +-- project (direct business; client = NULL)
                                                |
                                                +-- cleaning_policy / baselines / rule_sets
                                                +-- dataset metadata + source mapping
                                                +-- analysis_run --> evidence + output artifacts
                                                +-- business_context_revision
                                                +-- metric_definition --> metric_revision
                                                +-- approved analyst feedback (future)
                                          |
                                          +-- organization_metric_template (definition only)
                                          +-- organization audit / retention policy
    explicit grant (principal + organization + project/workspace; expiry/revocation)

The chart is conceptual. Actual RLS, API roles and migration ownership are evaluated in Stories 4.1, 6.1, 7.1 and 7.2; do not infer that model-level foreign keys alone provide authorization.

## 2. Candidate table contracts (architecture proposal, not executable DDL)

Common pattern: UUID primary keys; \`created_at\` UTC timestamptz; \`updated_at\` on mutable rows; immutable revision rows append-only; \`organization_id\` NOT NULL on every scoped entity. All external links and identity IDs are opaque. Exact names/ORM types/indices depend on review.

| Table / aggregate | Key fields and relationships | Constraints / intended guarantees | Canonical ownership |
| --- | --- | --- | --- |
| \`organizations\` | \`id\` UUID PK; \`kind\` = agency/direct_business/other; display name; lifecycle state | Unique stable \`id\`; soft-delete/deactivation policy, no client data in public slug | Story 4.1 for tenant foundation; billing integration later |
| \`organization_memberships\` | \`organization_id\`, \`principal_id\`, organization administrative role, status and grant metadata | Unique active principal/organization membership; authorization requires verified auth principal; membership alone conveys **no project data access** | 4.1 identity links; 7.1 final roles |
| \`client_workspaces\` | \`id\` UUID PK; \`organization_id\`; name; authorization reference; status | Unique (\`organization_id\`, \`id\`); no workspace can belong to two organizations; no mandatory client for direct business | Relationship designed in 4.1; feature rollout gated by 6.1/7.1 |
| \`projects\` | \`id\` UUID PK; \`organization_id\`; nullable \`client_workspace_id\`; name; schema fingerprint | Unique (\`organization_id\`, \`id\`) and composite FK (\`organization_id\`, \`client_workspace_id\`) to same-org workspace when not null; owning project never changes tenants by simple update | **4.1, existing Task 4c** |
| \`project_access_grants\` | \`organization_id\`, \`project_id\`, verified \`principal_id\`, scoped role, expiration/revocation, grant issuer | Must point to same-org project; no blanket implicit access; revocation effective on fresh reads and signed URLs; role capability allowlist | 4.1 interface design; enforcement 6.1/7.1/7.4 |
| \`business_context_revisions\` | \`id\`, \`organization_id\`, \`project_id\`, monotonically increasing \`revision\`, typed minimized goals/constraints, approval actor/time/status, retention policy | Unique (\`project_id\`, \`revision\`); FK same-org project; approval transition audited; no mutation of approved payload; unknown facts marked unknown; no raw CSV stored here | Proposed CI-1; human-filed story for model |
| \`metric_definitions\` | \`id\`, \`organization_id\`, \`project_id\`, stable metric key / display name, active state | Unique stable key **within project**, not globally; same label across projects can mean different formulas | Proposed CI-1 |
| \`metric_definition_revisions\` | \`id\`, \`organization_id\`, \`project_id\`, \`definition_id\`, version; typed formula reference, numerator/denominator, units, attribution, timezone, calendar, mapping and approval | Version immutable once approved; composite FK to same-org definition; approval and effective version must be explicit; invalid denominator => **not computable** | Proposed CI-1 |
| \`organization_metric_templates\` | \`id\`, \`organization_id\`, reviewed template definition and version | No observed customer data or learned preferences; always project-specific approval before business-labeled KPI computation | Proposed CI-1/CI-4, later |
| \`analysis_runs\` / existing run representation | \`id\`, \`organization_id\`, \`project_id\`, pipeline/config version, input fingerprint, context/metric version refs, result status, timestamps | Same-org project FK; record snapshot of pinned versions; never rewrite historical result via later metric edits; immutable provenance pointer | 4.4/report history; Epics 1–3 outputs preserved |
| \`analysis_artifacts\` / object manifest | \`organization_id\`, \`project_id\`, \`run_id\`, object locator, artifact type, retention status, integrity digest | Object key must not itself authorize read; scoped signed-link issuance after server-side access check | Epic 4 upload/history + Epic 6 storage |
| \`audit_events\` | authorized actor, organization/project reference, event, version, time, evidence digest | Append-only via Epic 7.2; audit payload must not contain raw client data or secrets; cannot be silently modified | Epic 7.2 |
| \`analysis_feedback\` (FUTURE) | \`organization_id\`, \`project_id\`, \`run_id\`, suggestion ID, reviewer outcome, approved preference revision | No automatic weight/model training; consented feedback only; no cross-client reuse without explicit legal/security gate | CI-5 / Phase 16 vision, **not** 4.1 deliverable |

**Minimum 4.1 implementation scope recommendation:** tenant identity/membership and existing project record with non-null org ownership, optional client relationship designed but feature gated; leave context/metric revision tables and access UI to separately approved CI-1 stories when dependencies permit. Avoid turning 4.1 into an entire context intelligence implementation.

### Referential integrity invariants

1. Every scoped record identifies the organization responsible for its persistence and is attached to a same-organization project via composite FK or an equally strong reviewed DB constraint.
2. \`client_workspace_id IS NULL\` is valid for a direct tenant project, but a populated \`client_workspace_id\` **must** belong to the project's organization.
3. IDs are immutable where required for ownership; moving a project/client between organizations is an explicit export/import and permission workflow, never a single FK UPDATE.
4. Approved context and metric revisions are append-only; \`current_revision\` (if materialized) changes atomically under authorization with optimistic concurrency (expected version).
5. A metric definition label is not unique meaning: unique identity is \`project_id + metric_id + version\`, with a typed mapping to validated dataset columns and time windows.
6. Each analysis_run's recorded evidence references exactly which context/metric version was used, even when the latest definition changes.
7. If a client-level grant is introduced, the schema and policies must define whether it delegates to newly created projects automatically. **Recommended default: no implicit grant for future projects**; grant visibility explicitly per project.
8. An active role/grant cannot depend solely on a claim supplied by a browser form, CSV field or LLM response.

## 3. Typed metric registry and context contract

### Business Context Profile revision

Expected fields: bounded set of approved \`objective_ids\`, business model (optional), reporting priorities, business constraints, allowed data sources, decision horizon, selected review authority, data classification, provenance of user-supplied facts, expiry/retention policy. Each field has a trust state (\`declared\`, \`verified\`, \`unknown\`); only approved project-scoped facts become available to the analysis planner. **User prose and retrieved customer text are untrusted data, never instructions.**

### Trusted Metric Definition revision

Required: \`metric_id\`, revision, business description, units/currency, numerator, denominator (if applicable), aggregation, null/zero and dedup handling, time window, timezone, attribution policy when needed, dataset schema fingerprint and field mapping version, approving authority and approval timestamp.

Proposed rule: formulas are restricted, typed, deterministic references to approved computation operations; **not arbitrary SQL, Python, eval expressions or model-generated code**. If a needed operand cannot be reconciled, output \`not_computable\` with missing inputs; do not emit zero or a guessed value. Model narrative receives only validated computed results.

Examples:
- Lead-generation agency: cost-per-qualified-lead requires a formally defined *qualified lead* and scope-correct spend; absent qualification => use a **different labeled metric** (all-lead CPL), with approval, or refuse.
- E-commerce agency: ROAS = attributable revenue / attributed ad spend under an approved attribution window; ROAS is **not** profit. Contribution margin requires actual cost/refund definitions. Missing COGS => not computable.
- Same dataset + differing approved goals => different eligible analysis plans; absent goal => honest generic DQA/insights without unapproved personalization.

### Approval workflow

Draft → review → approved version → used by run → superseded/revoked; old issued reports preserve pinned versions and audit evidence. Human owner/client designee approves meanings; an AI agent may suggest changes but not approve them. Reject conflicting template inheritance. Explicit revoke blocks **future use** without silently deleting legally retained reports.

## 4. Authorization and RLS boundary (design, not yet policy SQL)

### Actors

\`organization_owner\` controls account-level administration; \`organization_admin\` manages explicitly delegated resources; \`analyst\` is a project-level worker; \`client_reviewer\` and \`client_viewer\` are invited, scoped principals; \`platform_support\` has **no default access** to customer content. The exact role model is reserved for 7.1 approval.

- Tenant membership permits only tenancy metadata appropriate to that role; it is **not an automatic project content grant**.
- Every content read/write is subject to **verified principal + active tenant membership + project access grant + action permission**, enforced server-side and supported by database policies.
- Do not treat \`organization_id\` or \`project_id\` taken from request params or JWT custom claims as proof of permission. Verify cryptographically trusted identity, active membership/grants and resource ownership using database records.
- For PostgreSQL RLS, plan tenant scope plus project-access constraints in both \`USING\` and \`WITH CHECK\`; enable policies on every scoped table. Prefer \`FORCE ROW LEVEL SECURITY\` for application-owned tables after appropriate role testing; never make the application connection the table owner or a BYPASSRLS role for ordinary user traffic.
- Supabase \`service_role\` can bypass RLS: strictly isolate it from client/user requests, deny arbitrary file/report operations through it, and audit any narrowly authorized backend job path.
- Application server should access DB in a request/transaction-scoped security context; use verified session identity and parameterized calls. If using transaction-local DB claims, they must be derived from trusted server identity, set transaction-locally, and rolled back on pool reuse—not caller text.
- File storage and analysis caches are separate boundaries: never assume database RLS alone protects signed URLs, object keys, embeddings, LLM context fetches, audit exports or background workers.
- Never promote cross-tenant read access through Epic 7.7's administrative customer-journey dashboard; it is not a license to inspect client data.
- Support access: time-bounded just-in-time approval with independent audit and expiry, if authorized in a later security story, never silent impersonation.

### Policy decision matrix (proposed)

| Principal / operation | Organization metadata | Client/project data | Approve KPI | Manage project access |
| --- | --- | --- | --- | --- |
| Org owner (no project grant) | Allowed (appropriate metadata) | **Denied by default** | No, unless designated | Allowed with audit, scoped to tenant |
| Org analyst (project grant) | Minimal | Assigned project only | Draft only, unless designated | Denied |
| Client reviewer (explicit invite) | Minimal | Authorized approved artifacts only | If designated project metric authority | Denied |
| Client viewer | Minimal | Approved reports only | Denied | Denied |
| SAINT support | Platform health metadata only | Denied by default | Denied | Denied |
| Another tenant / revoked principal | Denied | Denied | Denied | Denied |

## 5. Compatibility with current brownfield repository

**Observed, not hypothetical:**
- \`backend/api/app.py\` currently exposes a minimal parse endpoint and health check, not an integrated tenant-aware SAAS API.
- Older Supabase migrations such as \`20250115000001_comprehensive_analytics_schema.sql\` define **user-scoped** \`datasets\`, \`analytics_results\` and \`nlp_queries\`, not the approved organization/project model.
- \`supabase/SUPABASE_ISSUES_ANALYSIS.md\` reports a duplicate-policy creation risk and competing \`live_data_stream\` table structures across the 2024/2025 migrations. A fresh migration replay is therefore **not presumed safe**.
- The current architecture text targets Supabase Auth and unified Supabase for Epic 4, with standalone PostgreSQL under Epic 6. Do not assume a completed backend/database cutover.
- The canonical \`schema-extensions-spec.md\` requires \`tenant → project → run\` and backward-compatible config migration. New client grouping must preserve it.

**Architectural rule:** plan a forward-only, additive, verified migration. Existing \`user_id\` is not automatically a tenant membership and must **not** be guessed into \`organization_id\`; any historical dataset without a verified owner must be quarantined/no-access until reconciled by an authorized human.

## 6. Staged implementation and migration strategy

| Step | Owner / gate | Planned action | Safe rollback |
| --- | --- | --- | --- |
| 0. Inventory reality | Human-supervised 4.1 planning | Reconcile actual deployed DB, checked-in migrations, current Auth project(s), data ownership, collision/duplication defects; fresh replay in isolated DB | No production changes; block work if unknown |
| 1. Schema review | Story 4.1 architect/security reviewers | Approve org, membership and canonical project contracts, composite ownership constraints; optional client FK contract | Documentation only until approved |
| 2. Expand | Approved 4.1 implementation | Add non-destructive canonical entities and constraints; keep legacy read paths behind flags during transition | Feature flag off; no destructive DDL |
| 3. Classify/backfill | 4.1a migration | Verify mapping of each legacy user-scoped row; backfill only provably owned rows; hold unknowns in restricted quarantine | Resume from idempotent checkpoints; preserve original tables |
| 4. Isolate | Epic 6.1 + 7.1/7.2 | Enforce RLS, scoped grants, audit; private object store rules; verify tenant and same-tenant-client negative cases | Deny new context features, not disable RLS |
| 5. Introduce revisions | Separate human-approved CI-1 story | Add optional versioned context and KPI definitions only after schema/security contracts meet gate | Feature disabled; existing generic mode unaffected |
| 6. Cut over | Human-controlled rollout | Canary specific authorized projects; verify links/report reproducibility; promote only after security/functional tests | Keep old version read-only for rollback; restore app version, not owner-scoped data visibility |
| 7. Contract | Later approved story | Retire legacy columns, duplicate Supabase policies and obsolete schemas only after fresh/staging/prod reconciliation and retention decisions | Explicit backup, legal signoff, recoverability test |

**No data deletion or rewriting the migration history in this proposal.** Production cutover demands backup/restore rehearsal, migration idempotency, no missing ownership, dual-read consistency where appropriate, a tested roll-forward path, and a clear kill switch.

## 7. Required negative tests and acceptance criteria

Future Story 4.1 acceptance is subject to human review and potential re-scoping; this packet supplies candidate testable criteria.

- **S-01 Ownership:** a project can be created only under an existing authorized organization, with immutable \`organization_id\`. Same-org workspace FK passes; cross-org workspace FK fails.
- **S-02 Direct mode:** a direct business creates a project with no client workspace and receives the ordinary generic DQA/CSV/report workflow.
- **S-03 Membership:** valid organization membership without a project grant cannot read project data or a report from another agency client.
- **S-04 Revocation:** revoked project grants, expired invites and former tenant members cannot read cached reports, object links, context revisions or future analysis requests.
- **S-05 Forged identities:** changing a URL, body, query string or client-side auth claim to another \`organization_id\`, \`project_id\` or \`client_workspace_id\` returns denial with no metadata leakage.
- **S-06 Composite integrity:** cannot attach an analysis_run, report, metric definition or context revision to a project owned by a different organization.
- **S-07 KPI correctness:** project A and B may label a metric "conversion rate" while using different approved denominators. Each run pins the correct version; a missing denominator produces \`not_computable\`.
- **S-08 Revision replay:** approving revision v2 does not silently modify v1 reports. Conflicting concurrent approvals fail deterministically; writes are audited.
- **S-09 Migration safety:** fresh migration replay and existing-schema upgrade work in disposable/staging DBs; invalid/unowned rows are quarantined and never automatically assigned to a tenant.
- **S-10 Deletion/retention:** policy deletion/export includes client-scoped context, metric maps, derived reports, caches and object artifacts; audit exceptions are explicit and minimized.
- **S-11 Generic backward compatibility:** all Epic 1–3 CLI and legacy config paths retain identical authorized semantics without mandatory business context or clients.
- **S-12 LLM/agent boundary:** untrusted CSV text cannot change authorization, load foreign-client context, mutate metric definitions, or make model-generated numbers authoritative.

### Mandatory evidence before any implementation PR can be merged

A canonical approved story with exact file scope and dependencies; architecture/security review; disposable schema replay; before/after schema diff; unit + integration + RLS negative tests, object-access tests; verified \`uv run pytest\`, \`npm test\`, \`npm run build\`; a security review with no unresolved Critical or High findings; a reviewer signoff at fixed SHA; documented rollback and zero unknown cross-tenant ownership.

## 8. Human-only architectural decisions that remain open

1. Decide exact mapping of conceptual **Organization** to canonical DB \`tenant\` identifier to avoid two competing keys.
2. Choose whether \`client_workspaces\` is physically created in 4.1 or reserved as a reviewed contract and introduced in a later authorized story. **Recommended: model the optional relationship now; build the UI/persistence when isolation and grants are ready.**
3. Decide whether an organization owner has audited, explicit access grants to all client data or must request client/project access. **Recommended: no implicit content grants** for the owner.
4. Select source of truth for auth, DB and migration tooling (unified Supabase now, standalone PG later per architecture); reconcile legacy migration defects first.
5. Define authority for KPI approval (agency owner vs delegated client decision maker), including revocation and conflict handling.
6. Approve client consent, DPA, source file retention, report artifact expiration and lawful audit retention before persistent real customer context.
7. Decide the initial low-risk context fields that can be stored without sensitive content or raw client observations.
8. Agree whether and when a separate CI-1 BMAD story is filed; no self-promotion, no eligibility changes, no release-date promise.

**Decision gate:** This draft package is ready for review, not execution. An approved design direction does not override the \`sprint-status.yaml\` backlog or the human-only merges required by \`AGENTS.md\`.
