# Epic 4.1 Schema Package — Migration, Security and Review Gate

**Status:** Proposed verification protocol, not an executable migration or approved story.  
**Companion design:** [Epic 4.1 context schema design](epic-4-1-context-intelligence-schema-design-2026-11-11.md).  
**Owner authority:** only Marvin promotes canonical stories or merges; \`sprint-status.yaml\` / \`loop_eligible\` unchanged.  
**Beta release independence:** 2026-11-13 concierge beta requires none of this functionality.

## A. Brownfield truth-check BEFORE implementation

The repository contains legacy Supabase schema artifacts. Do **not** assume they are the live production source of truth:

| Finding to reconcile | Evidence in repository | Gate |
| --- | --- | --- |
| Multiple existing user-centric tables | \`supabase/migrations/20250115000001_comprehensive_analytics_schema.sql\` (\`datasets\`, \`analytics_results\`, \`nlp_queries\` with \`user_id\`) | Document mapping to the new org/project model. Never convert user_id to tenant membership without verified ownership. |
| Duplicate live-stream policy names | \`supabase/SUPABASE_ISSUES_ANALYSIS.md\`, 2024 security migration and 2025 UUID migration | Fresh schema replay must succeed; do not hand-edit historical production migrations blindly. |
| Competing \`live_data_stream\` schemas | Initial 2024 live data stream vs \`20250714001951-0ddb6f34-f4bc-4e09-9123-d8075eac9a14.sql\` | Confirm canonical columns and affected edge functions; explicit forward transform and compatibility test. |
| Current minimal HTTP backend | \`backend/api/app.py\` only assembles parser and health endpoint | Do not claim a tenant-aware production API already exists. |
| Planned DB/auth evolution | \`_bmad-output/planning-artifacts/architecture.md\` proposes unified Supabase Phase 3, standalone PostgreSQL later | Choose actual authoritative environment, ORM/Alembic vs Supabase SQL migration boundary, and rollout cutover before writing DDL. |
| Canonical project parent | \`schema-extensions-spec.md\` requires \`tenant_id → project_id → run_id\` | Add optional client grouping without replacing project, breaking old pipeline or changing other entities' owners. |

**Stop conditions:** missing DB inventory; unknown user ownership; unverified authentication principal mapping; migration replay failure; unresolved service-role bypass; uncertain API access boundary; nonnullable project ownership cannot be established without data loss; absent backup/restore test.

## B. Implementation packets: separate human approval per story

| Packet | Candidate canonical story | Allowed implementation after approval | Not allowed as a side effect |
| --- | --- | --- | --- |
| P-4.1 identity | 4.1 | Organizations/memberships, canonical project, same-org key constraints, no client UI | New full context agent, billing, API tokens or unbounded access |
| P-4.1a migration | 4.1a | Deterministic config-to-project ownership mapping and migration fixtures | Guessing owner, destructive backfill, automatic client sharing |
| P-CI1 data contract | Future separately filed story or human-amended 4.1 | Proposed Business Context Profile / Trusted Metric Definitions, reviewed after 4.1 identity contract | Unapproved schema expansion, self-serve promise or metric hallucination |
| P-6.1 isolation | 6.1 | RLS, same-tenant client/project grants, storage/object authorization, DSAR dependencies | Cross-client access via tenant membership or service-role shortcut |
| P-7.1/7.2 roles & audit | 7.1 and 7.2 separately | Delegated permission roles, signed KPI approvals and append-only audit evidence | Rewriting past approvals/metrics; platform-support default content access |

Treat these as review packet labels, not canonical story identifiers or newly promoted items. Never dispatch 4.1, 4.1a, 6.1, 7.1, 7.2 unattended: their canonical \`loop_eligible\` flags are false.

## C. Security policy design review (not executable SQL)

- **Auth source:** a verified Supabase/JWT identity (or reviewed replacement) maps to server-side principal; no authorization from frontend-supplied user or tenant ID.
- **Organization restriction:** principal must have active relationship with organization plus scoped resource grant. Admin ownership may grant rights but must not silently grant all read rights.
- **Row and write policies:** evaluate authorization on \`USING\` and \`WITH CHECK\`, not only a UI filter; harden INSERT, SELECT, UPDATE, DELETE and object storage separately. Examine RLS bypass/owner roles/SECURITY DEFINER functions.
- **Index design:** composite unique index on (\`organization_id\`, \`id\`) of parent resources supports composite foreign keys. Scoped run and metric lookups index (\`organization_id\`, \`project_id\`, time/version); avoid leaking result counts through unprotected endpoints.
- **Storage:** object keys are private and scope-tagged; signed URL minting requires server authorization and short expiry; verify revocation and direct-link behavior; service workers impersonate only verified scope.
- **Embeddings/cache:** no raw client data embedding by default; cache/index keys include organization+project+approval version, with second server-side scope check on retrieval.
- **LLM:** untrusted CSV content does not become system instruction; only approved bounded metadata and computed results may enter analysis prompts; do not cache private prompts across clients.
- **Audit:** append-only metadata includes actor/action/scope/definition version, without raw client data or secrets; break-glass access requires explicit time-bound approval if ever implemented.
- **Retention:** define how backups, derived reports, signed URLs, analysis history, metric definitions, context revisions and revocation are handled before persistent client use.

## D. Acceptance-test matrix for the future implementation

Each case needs a fixed anonymized or synthetic fixture, API/database request, expected denial/approval, and audit assertion. Failure must not leak object names, project existence, row counts or client identifiers.

| ID | Test | Expected |
| --- | --- | --- |
| SEC-01 | Actor A changes URI \`organization_id\` to B | Deny without revealing B's metadata |
| SEC-02 | Analyst belongs to agency but has no client/project grant | Deny client contents |
| SEC-03 | Client A reviewer requests Client B's report within same agency | Deny despite same tenant |
| SEC-04 | Org owner has account admin permission but no content grant | Permit allowed admin functions, deny raw content by default |
| SEC-05 | Valid principal with expired/revoked project grant | Deny new reads, exports, future processing and signed link minting |
| SEC-06 | Forged client ID in project insert/update | Composite FK or authorization rejection |
| SEC-07 | Alter revision 1 after report was generated | Reject; create version 2 and preserve report link to v1 |
| SEC-08 | Metric label 'conversion rate' with different project denominators | Produce correct project-scoped formula/version, no automatic cross-project inheritance |
| SEC-09 | Missing qualified-lead flags, costs or denominator | Return not computable or truthful alternative label; no guessed number |
| SEC-10 | Cache/index query made using different client scope | Deny; no result even when key exists |
| SEC-11 | LLM prompt in CSV demands other-client context or raw SQL | No access, no execution, safe refusal/defer |
| SEC-12 | Migrate legacy record with unknown owner | Quarantine without assigning organization |
| SEC-13 | Fresh migration replay from zero | Idempotent and all policy definitions consistent |
| SEC-14 | Upgrade test from documented legacy variant A and B | Safe forward migration, no shadow schema mismatch |
| SEC-15 | Direct business makes project without client workspace | Allowed after authorization, generic pipeline unaffected |
| SEC-16 | Deactivate tenant / withdraw consent / request erasure | Block new processing; delete/retain data according to documented policy; report all residual backups |
| SEC-17 | Service-role or background processing path is invoked with forged scope | No user-driven bypass, logged and bounded approved job only |
| SEC-18 | Parallel approvals / context edits | No lost update or silent formula replacement; reject stale version |
| SEC-19 | Site user creates first report without goal wizard | Normal 4.10 guided default flow still succeeds |
| SEC-20 | Old CLI config is loaded after project migration | Same supported semantics and no forced client context |

## E. Deterministic migration rehearsal

1. Snapshot the current schema and validate source-of-truth environments. Prepare *disposable* database(s) only. Do not include customer records in test fixtures.
2. Replay all committed migrations **in order** on empty DB. Record failures and conflicts before adding any new migrations.
3. Rehearse from each known legacy schema variant; generate a forward migration with versioned checkpoints and explicit orphan quarantine.
4. Create organizations/memberships and projects, but only backfill where verified ownership exists. Validate row counts, foreign keys, zero cross-org links, and retention obligations.
5. Apply least-privilege grants/policies; ensure service app roles do not own tables or bypass RLS for ordinary requests.
6. Run the full SEC suite from both valid and malicious identities; verify logging does not include sensitive records.
7. Run \`uv run pytest\`, \`npm test\`, \`npm run build\` and story-specific E2E/security cases at the fixed PR SHA. Include production build artifacts' digest.
8. Prepare deployment rehearsal: backup/restore, feature flags default OFF, smoke probes, roll-forward procedure, and transaction/connection-pool isolation.
9. Obtain independent architecture/security review and human merge/deploy approval. **Do not interpret a green CI run as permission to turn on persistent client context.**

### Migration rollback strategy

Use additive/expand-then-contract migrations. After writing real data in the new schema, prefer **feature disable + roll-forward repair** rather than rolling back to an unsafe old schema. Never disable RLS as a rollback. Never remove a column/table before all readers and retention constraints are migrated with owner signoff. For beta, there is no new context schema to roll back.

## F. Review checklist / sign-off

- [ ] Authorized product owner confirms Organization = Tenant, optional Client Workspace, Project = canonical analysis parent.
- [ ] Architect approves exact FK paths, composite constraints, tenancy identifier and Pydantic/SQLAlchemy/SQL contracts.
- [ ] Security lead approves threat model, grant/owner semantics and client-scope RLS.
- [ ] Privacy/legal reviewer agrees on retention/consent/DPA and data processing roles.
- [ ] Data lead approves metric formula versioning, definition authority and correct missing-data behavior.
- [ ] Migration reviewer reconciles 2024/2025 Supabase defects with observed live DB, not assumptions.
- [ ] Story owner files one bounded BMAD story; only Marvin can mark it ready or set loop eligibility.
- [ ] Independent fixed-SHA reviewer signs off on the implementation, with tests/security gate.
- [ ] Marvin authorizes merge; later, separately authorizes any deployment.

**Status now:** architecture-review input; no schema changes, no migrations, no auth/role writes, no deployment and no sprint ledger updates.
