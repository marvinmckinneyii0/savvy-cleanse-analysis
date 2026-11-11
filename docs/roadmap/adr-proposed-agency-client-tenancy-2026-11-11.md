# ADR Proposal — Agency, Client Workspace, Project and Context Ownership

**ADR ID:** CI-ADR-001 (proposal identifier, **not an approved canonical architecture decision**)  
**Date:** 2026-11-11  
**Status:** Proposed; owner/architect/security review required before Story 4.1 schema approval  
**Scope:** SAINT Context Intelligence Option B, agency-first but reusable for non-agency organizations  
**Related draft:** [Option B roadmap](saint-context-intelligence-option-b-proposal-2026-11-11.md) and [candidate story packets](context-intelligence-story-packets-and-evaluation.md).  
**Non-authoritative:** This ADR changes no runtime data model, PRD, sprint-status.yaml, story eligibility, billing, tenancy or access controls.

## Decision recommended for owner review

**Use one tenant per subscribing organization, an optional tenant-owned client workspace for agency customers, and the already planned tenant-owned project as the authoritative configuration/reporting parent.**

This is a **logical client grouping and authorization boundary** within the tenant, not a replacement for Epic 4.1's existing project model. A direct business customer owns a tenant with projects and may have no client workspaces. An agency owns a tenant containing multiple client workspaces, each with multiple projects. The tenant remains the subscription/security perimeter, but **client-level access is not automatically implied by tenant membership**.

    SAINT (platform operator; audited support, no default customer-data browsing)
      |
      +-- tenant / organization (agency or direct business)
          |-- tenant_memberships (role; identity; explicit access policy)
          |-- reusable approved agency-level KPI *templates* (no client observations)
          |
          |-- client workspace A (optional logical account grouping)
          |    |-- client_access_grants (actors, role, purpose, expiry)
          |    +-- project A1 (existing Epic 4.1 project; tenant_id always)
          |         |-- BusinessContextProfile revisions
          |         |-- approved TrustedMetricDefinition versions/mappings
          |         |-- cleaning_policy / baselines / monitoring rules
          |         +-- runs[] / metric results / report / healing manifest
          |
          |-- client workspace B (no implicit access or data sharing with A)
          |    +-- project B1 / project B2 ...
          |
          +-- project G (direct tenant project; no client workspace required)

**Identity/auth keys:** all persistent project, metric, context, report, grant, memory and audit resources carry a validated tenant scope, and all client-owned resources carry or derive their client scope by an integrity-checked project relation. The server computes authorized scope from verified membership/role/grants, never from a user-supplied tenant_id/client_id alone. Prefer immutable opaque internal IDs and database-enforced composite references/constraints after explicit architecture review.

**Preserve:** the canonical `tenant_id → project_id → run_id` ownership path in `schema-extensions-spec.md`, including existing project-scoped baseline, cleaning policy, rule set and history. A client workspace is an **optional organizer/grouping** associated with projects; it never takes over an existing run's configuration parent. Do not require a client workspace for generic / direct business usage.

## Options considered

| Option | Strength | Limitation | Recommendation |
| --- | --- | --- | --- |
| A. One tenant per agency, optional client workspaces (recommended) | Natural subscription model; shared agency-approved templates; client-specific analysis and grants; one agency can oversee multiple customers | Requires client-aware permission model and negative tests within a tenant | **Propose for approval** |
| B. Separate tenant for every agency client | Strong tenant separation, easy direct-owner boundary | Agency-wide billing, analysts, approved template reuse, customer onboarding and cross-client portfolio become difficult; would require carefully managed cross-tenant delegation | Reserve for clients whose contract/security requirements demand separate tenant ownership |
| C. One tenant and projects only; client label is free text | Minimal initial schema | Labels are not security boundaries; easy to mix memory, KPI definitions and reports; future retrofit costly | Reject as production design; acceptable only for a **manual** beta worksheet with no persisted cross-client context |

### Tradeoffs and exclusions

- **Agency-owned client workspace is not a proof of contractual authorization.** Owner must establish who the data controller/processor is, client sharing permission and DPA terms before processing client datasets.
- **An agency is not always a marketing agency.** Direct business tenants and later adapters use the same project + optional client grouping, with no forced marketing-specific columns.
- **A separate legal entity requesting independent control can become its own tenant.** Do not silently move it across tenant borders or use federated cross-tenant account access without a separately approved architecture story.
- **Agency-level templates are policy/definition metadata, not computed client values.** Sharing an approved formula template never shares Client A's observed metrics, facts, raw data or feedback into Client B.
- **Do not promise cross-client rollups or industry benchmarks by default.** They require separately designed consent, aggregation thresholds, legal review and accurate disclosure.

## Minimal proposed logical contracts

These are for architecture discussion, **not database migrations**:

    tenant {
      tenant_id
      kind: agency | direct_business | other  // optional metadata, not access authority
    }

    client_workspace {                        // optional tenant-owned grouping
      client_workspace_id
      tenant_id
      display_name
      status: active | archived
      authorization_reference                  // reviewed contract/permission record, not raw document
    }

    project {                                 // existing canonical Story 4.1 entity
      project_id
      tenant_id
      client_workspace_id: nullable           // every relation must belong to same tenant
      name
      schema_fingerprint
      ...existing owned configuration and runs
    }

    project_access_grant {
      tenant_id
      subject_id
      project_id or client_workspace_id       // specific scope, never arbitrary SQL predicate
      role: agency_owner | agency_admin | analyst | client_reviewer | client_viewer
      granted_by
      expires_at
      revoked_at
    }

    business_context_revision {
      tenant_id
      project_id
      revision_id
      approved_state: draft | approved | revoked | superseded
      objective_id
      declared_facts_and_constraints           // only minimized, approved metadata
      evidence_reference
      approved_by
      approved_at
      retention_policy_id
    }

    trusted_metric_definition_revision {
      tenant_id
      project_id
      metric_definition_id
      definition_version
      formula_reference / typed expression
      numerator / denominator / units / period / timezone / filters / attribution
      mapping_version
      approved_by
      approved_at
      status
    }

**Implementation choice to resolve:** whether client_workspace is a first-class table in Epic 4.1 or introduced as an optional add-on after project/auth. Given migration and permission costs, the recommendation is to **design its identity and relation now**, but phase feature enablement according to Epic 4/6/7 dependencies. No table or column is approved by this ADR alone.

### Permission matrix (proposed policy, subject to business and threat-model review)

| Actor | Own tenant settings | Client workspace list | Read client data/metrics | Approve client KPI | Cross-client portfolio |
| --- | --- | --- | --- | --- | --- |
| Agency owner | Yes, audited | All within authorized tenant | Explicit audited owner privilege | Only if designated metric authority | **Off by default**; metadata/aggregate-only after separate review |
| Agency admin | Delegated | Authorized client scopes | Authorized projects only | Explicit designation | Off by default |
| Agency analyst | No | Explicit grants | Explicit projects only | Suggest/edit draft; designated approver required | Off by default |
| External client reviewer | No | Own explicitly invited scope | Own approved project reports only | According to contractual delegation | Never |
| External client viewer | No | Own invited scope | View-only approved report artifacts | No | Never |
| SAINT support/operator | Platform maintenance only | No implicit access | Deny without time-limited, logged support consent / break-glass | No | No |
| Unauthenticated/other tenant | No | Deny | Deny | Deny | Deny |

All sensitive reads, exports, LLM context retrievals, report generation, cache hits and derived metrics must enforce both tenant and project/client scope. A user who belongs to the agency does not thereby gain read access to every client's private details.

## Metric definition inheritance and conflict policy

Proposed read path:
1. Look for a **project-approved metric revision**; it wins for that project only.
2. If not found, offer an approved **agency template** as a suggested draft, not as an implicitly approved client definition.
3. Before computing a business-labeled metric, require approval from the designated project/client metric authority and a compatible input mapping.
4. If definitions disagree or no authorized approver is available, return **not computable / needs review**; never silently pick whichever formula produces a number.
5. Pin the approved definition version and evidence/provenance on each run. Editing creates a new revision; historical reports retain their original definition.
6. Agent context retrieval uses only approved revisions within current authorized project scope; optional inferred preferences stay advisory and never rewrite metric definitions.

### Example: same label, different denominator

- Client A may define **conversion rate** as *SQLs / qualified leads* over a 30-day sales window.
- Client B may define **conversion rate** as *purchases / sessions* over a seven-day campaign window.
- The two definitions may share the display label but **must not share an unqualified metric ID, denominator assumption or memory result**.
- A report requested without the needed fields or period should disclose missing inputs and withhold the metric rather than fabricate a plausible-looking value.

## Data and context life cycle

1. **Intake (CI-0, manual):** gather only the business objective and minimum data dictionary required for the beta. No required persistent SAINT profile in the public MVP; existing secure-file-sharing and deletion rules govern real data.
2. **Draft context:** a verified, authorized user supplies facts and KPI meanings. Untrusted dataset descriptions and tool outputs are marked as unapproved until reviewed.
3. **Approval:** designated metric owner signs a specific scope and version; identity, reason and timestamp are written to an immutable audit facility only when Epic 7.2 provides it.
4. **Analysis:** server checks tenant/project/client grants, loads only approved context, validates dataset mapping, computes metrics deterministically and logs versioned evidence.
5. **Review:** analyst sees suggested analyses, missing-input warnings and interpretations separate from observed numeric results. Publish only after required human review.
6. **Feedback:** explicit accept/reject/correct event; no automatic model training or cross-client sharing. Future preference memory requires separate approval and erasure capability.
7. **Revocation and deletion:** revoke future use immediately; follow retention/DSAR procedures for cached context, embeddings, derived reports and backups as legally appropriate, while preserving only justified audit metadata.
8. **Support:** no automatic admin impersonation; approved time-bound access and audit trail where necessary.

## Threat model and design invariants

| Threat / failure | Required control and negative test |
| --- | --- |
| Tenant impersonation via URL/body | Reject forged tenant_id, even when project_id is real; verify server-side membership and RLS |
| Same-tenant, wrong-client report access | Deny using explicit project/client grants; tenant membership alone insufficient |
| Stale grant / former employee | Revoked roles and tokens no longer retrieve cached or historical context |
| Ambiguous account linking | Reject project/client relation crossing tenant boundary (DB FK/constraint) |
| Cross-client LLM context leakage | Retrieve bounded, authorized facts only; adversarial prompts cannot alter scope or reveal metadata |
| Embedding/vector store leakage | Scope both index keys and retrieval filters; verify from a separate client account |
| Shared agency KPI template pollution | Templates contain no observed client values; project approval/version required before use |
| Wrong formula / changed denominator | Pin historical formula and mapping; fail closed on missing or conflicting versions |
| Client export/erasure | Include context, analysis artifacts, feedback, cache and any backups per approved retention design |
| Context growth and cost | Cap retrieved fields, versions, tokens and duration; default to generic analysis or human defer |
| Anonymous support access | No uncontrolled break-glass path; all support grants time-limited, owner-approved and audited |

## Dependency gates mapped to current epics

| Canonical epic/story | Proposed responsibility | Hard stop |
| --- | --- | --- |
| 4.1 Database Schema & Auth Foundation | Review optional tenant-owned client workspace ID and scoped context/metric revision ownership alongside existing project | Requires owner-approved schema decision and migration/backward compatibility review; not loop-eligible |
| 4.1a Config-to-Project Migration | Preserve existing config/policy/abstract project references | Must preserve generic CLI runs and old configs, no forced client workspace |
| 4.3 Analysis Configuration and 4.10 Onboarding | Display optional agency/client context and manual KPI approval after authorization; no required new wizard | New tenant can reach first report with defaults, per existing 4.10 DoD |
| 6.1 RLS and 6.4 Security | Tenant + same-tenant client/project isolation, DSAR, security regression | **No customer-facing persistent context before verified scope isolation** |
| 7.1 Roles, 7.2 Audit, 7.4 API Tokens | Implement review roles, immutable metric changes and least-privilege tokens | No use of unapproved metric definitions or unaudited privileged read |
| 8.1, 8.4, 8.5, 8.7 | Context-aware eligible analysis planning using versioned registry; no numeric invention | Preserve 8.5 opportunity-only, 8.7 pull-not-push, generic fallback |
| 11.1–11.5 | Evaluation, confidence, context traceability and human escalation | Tier-4 remediation risk boundary unchanged |
| 12.1 and 12.4, then 13.1 and 13.5 | Optional marketing context mapping and generic mode; agency pack | Existing **pre-vertical gate:** Epics 3, 8, 9, 10 done before Epic 12 |
| Phase 16 | Reviewed preference and outcome memory | Explicit future approval, security and held-out evidence of improvement |

This proposal does **not** change the product monetization tiers, create a paid agency feature, bypass existing story dependencies, or infer readiness from a date.

## Proposed acceptance criteria for a future tenancy architecture story

**T-AC1 — Canonical identity:** project remains parent of runs, configs, baselines and report history. Client workspace is optional and tenant-owned; generic/direct-business path operates without it.

**T-AC2 — Tenant integrity:** every relation and API query enforces tenant scope, and database constraints prevent attaching a client's workspace to another tenant's project.

**T-AC3 — Same-tenant client isolation:** default agency analyst can access zero client projects until granted; Client A's viewer cannot read Client B's context, metric definitions, reports, history, prompts, cache or vectors.

**T-AC4 — Owner/admin audit:** agency owners can manage explicitly authorized client scopes with an auditable elevated role; support access is absent unless time-bound and approved.

**T-AC5 — Metric source-of-truth:** KPI definitions are versioned, approved, project-specific and reproducible; template inheritance is opt-in and context-specific.

**T-AC6 — No context fallback leak:** on missing/expired approval, revoked role, conflicting tenant, missing metric denominator or model outage, return a safe error, noncomputable status or generic analysis only where appropriate and authorized.

**T-AC7 — Historic reproducibility:** past run evidence pins context, metric definition, code/formula version and dataset fingerprint; revisions do not rewrite previously issued reports.

**T-AC8 — Rights and lifecycle:** tenant export/erasure covers client workspaces and all corresponding context/memory; retention policies are enforced with documented backup behavior and no prohibited PII in logs.

**T-AC9 — One-tenant/direct-business case:** a self-serving business user can create a first project/report without creating a placeholder client, and without access to other tenants.

**T-AC10 — Regression and security:** test cross-tenant/same-tenant wrong-client queries, role revocation, malformed authorization IDs, cache reuse, cross-scope concurrency, report links and data deletion. Independent reviewer signs off before any production feature.

### Test matrix for review

| Fixture | Tenant | Client | Membership | Expected |
| --- | --- | --- | --- | --- |
| Owner views assigned agency project | A | A-1 | Owner | Allow with audit |
| Analyst views explicitly granted project | A | A-1 | Project grant | Allow |
| Analyst views ungranted neighboring client | A | A-2 | Tenant member only | Deny |
| External client viewer accesses different client | A | A-2 | Guest A-1 only | Deny |
| Viewer supplies another tenant's ID | B | Any | Tenant A only | Deny |
| Direct business creates generic project | C | None | Tenant C owner | Allow after auth |
| Reuses agency template without approval | A | A-1 | Analyst | Suggest draft; do not compute labeled business KPI |
| Revoked worker opens old report link | A | A-1 | Revoked | Deny |
| Model prompt asks for other clients | A | A-1 | Valid local role | Deny cross-client retrieval |
| Approved metric has missing denominator | A | A-1 | Metric approver | Not computable, never 0 or guessed |

## Unresolved choices requiring explicit human approval

1. Is the *default* agency tenant owner allowed to read raw datasets for every client, or only metadata and explicitly granted projects? **Recommend explicit least-privilege project grants**, with a separately audited owner support/management role.
2. Is a client workspace a first-class table in **4.1** or an optional additive entity introduced afterward? **Recommend deciding the relationship in 4.1 design**, then scheduling storage and role UI only after security dependencies.
3. Who is allowed to approve business metric definitions—the agency owner, a client-designated decision maker, or both? **Recommend each project have a designated metric authority**, including documented delegation.
4. Should agency-level approved KPI templates be available to all analysts within an agency? **Recommend yes for definitions only**, excluding real client values and requiring project-level approval.
5. How are direct consulting customers onboarded? **Recommend one tenant with optional grouping omitted**, keeping the same generic DQA/analysis project.
6. How is client permission/consent captured and deleted? **Recommend references to signed authorization and explicit retention policy**, with an implementation decision when the approved privacy/DSAR model is designed.

## Required governance after human decision

- Marvin approves or revises the ADR explicitly; **merging this draft documentation does not itself approve a database design or promote a story**.
- Future canonical 4.1/6.1/7.1 work is high-judgment and requires narrow story specification, an independent security/architecture review, full `uv run pytest`, `npm test`, `npm run build`, RLS and e2e authorization tests, plus an explicit human merge.
- No change is made to `AGENTS.md`, `_bmad-output/implementation-artifacts/sprint-status.yaml`, `loop_eligible`, `agent-system/completion-policy.yaml`, schema or production deployment.

**Decision summary:** agency/direct customer is a tenant; client workspace is optional tenant-owned logical account; project remains the canonical parent; all metric/context/report data is project-scoped; authorization is tenant **and** client/project scoped; shared templates never inherit customer data; all implementation remains gated by approved stories.
