# SAINT Context Intelligence — Proposed Story Packets, Contracts and Evaluation

**Status:** DRAFT SPEC PACKETS ONLY — no approved BMAD story, no sprint-status promotion.  
**Companion:** [Option B roadmap proposal](saint-context-intelligence-option-b-proposal-2026-11-11.md).
**Schema packet:** [Epic 4.1 organization/client/project design](epic-4-1-context-intelligence-schema-design-2026-11-11.md) · [migration and security gate](epic-4-1-schema-migration-security-review.md).  
**Review model:** the existing AGENTS.md per-run boundary, human-only story promotion/loop eligibility/merge and independent exact-commit review remain intact.  
**Use:** a human planner may copy the relevant packet into *one* authoritative story and approve its scope, dependencies, and risk before implementation.

## 1. Contract first: concepts and separation

- **Agency**: a consulting/marketing organization (usually a tenant, but **not assumed** until Epic 4/6 tenancy is decided).
- **Client**: an agency's end customer, whose business objectives and data access must be isolated under the agreed organization/project model.
- **Project**: the existing planned Epic 4.1 entity, authoritative parent for configuration, baselines, rules, runs and artifacts. Do not create an incompatible second project concept.
- **Business Context Profile (BCP)**: consented, versioned business facts/preferences/goals at an authorized scope. Facts are not inferred from a model's guess.
- **Trusted Metric Definition (TMD)**: an approved calculation contract with a stable metric ID, definition version, data mapping and validity checks.
- **Analysis Candidate**: a named, allowlisted analysis capability (descriptive, diagnostic, predictive, prescriptive) with required inputs.
- **Analysis Plan**: a proposal choosing eligible analyses, requested parameters, reasons, missing inputs and decision state; it is *not* a computation result.
- **Metric Result**: a deterministic computed value or explicit *not computable*, tied to evidence and a versioned formula.
- **Insight / Recommendation**: explanatory text about computed outputs; opportunity identification belongs to 8.5, quantified impact only to Epic 10.
- **Feedback Event**: an explicitly approved correction, preference, veto, or post-decision outcome; not automatic permission to retrain or share data.
- **Decision Trace**: why an agent recommended something; it is distinct from Epic 3's Healing Manifest, which records what cleaning changed.

### Minimal proposed typed shape (illustrative, NOT a migration or API schema)

    BusinessContextProfile:
      tenant_scope: opaque_authorized_tenant_key
      project_scope: opaque_authorized_project_key
      client_scope: optional_authorized_client_key
      profile_version: immutable_version
      approved_by: human_actor_identifier
      approved_at: timestamp
      objective_ids: [string]
      industry: optional_sanitized_label
      allowed_data_sources: [approved_source_id]
      constraints: [typed_constraint]
      preferences: [approved_preference]
      retention_policy_id: policy_reference
      status: draft | approved | superseded | revoked

    TrustedMetricDefinition:
      metric_id: stable_identifier
      version: immutable_version
      owner_scope: tenant_or_project
      display_label: string
      business_meaning: approved_description
      numerator: typed_expression_reference
      denominator: optional_typed_expression_reference
      aggregation: approved_rule
      units: unit_and_currency
      timezone: iana_timezone
      calendar: configured_reporting_calendar
      attribution_window: optional_interval
      dimensions: [allowlisted_dimension_id]
      null_zero_dedup_policy: explicit_policy
      input_mapping_version: immutable_mapping_version
      approved_by: human_actor_identifier
      status: draft | approved | retired

    AnalysisPlan:
      context_version: version_or_none
      requested_goal_ids: [goal_id]
      candidates:
        - analysis_id: allowlisted_engine_identifier
          input_requirements_met: boolean
          metric_definition_versions: [metric_version]
          rationale: bounded_text
          missing_inputs: [typed_missing_input]
          proposed_parameters: typed_allowlisted_values
      requires_human_review: boolean
      plan_version: immutable_version

    MetricResult:
      run_id: authorized_run_identifier
      input_fingerprint: content_or_schema_digest_as_policy_allows
      metric_id: stable_identifier
      definition_version: immutable_version
      computation_artifact_version: immutable_code_or_formula_ref
      period: start_end_timezone
      value: typed_number_or_not_computable
      data_quality_warnings: [typed_warning]
      evidence_references: [authorized_reference]
      status: computed | not_computable | invalid
      human_review_status: optional_review_state

**Design review required:** choose exact references/field names, UUID strategy, tenant/client hierarchy, mapping validation, raw-data retention, canonical versioning, calculation expression language, and event schema in an authorized Story 4.1 expansion or distinct approved story. No executable arbitrary formula strings, raw SQL or untrusted eval as part of the contract.

### Worked examples for analysis eligibility

| Condition | Correct behavior | Forbidden behavior |
| --- | --- | --- |
| Goal is qualified lead efficiency, but qualified status is absent | Suggest data collection or use a clearly relabeled *all-lead CPL* when approved | Label raw leads as qualified leads |
| Goal is acquisition cost, but only ad spend exists | Show ad-spend-per-new-customer if identities and conversions reconcile; label scope | Claim comprehensive CAC |
| Goal is e-commerce profit, but COGS and returns are absent | Mark contribution margin and profit as not computable | Equate gross revenue or ROAS with profit |
| Duplicated order IDs, mixed currencies/timezones | Block invalid aggregate, request normalization policy and human review | Silently discard duplicates or combine currencies |
| Target context is unspecified | Run supported generic DQA/report, state no business-specific KPI interpretation | Guess industry, goals, data definitions or user intent |
| Client A's context is requested from Client B's session | Server denies; no context metadata or inference leaks | Return cached or embedded context across client boundaries |
| Marketing pack not enabled | Generic mode with existing output and accurate limitations | Force marketing-specific assumptions into generic reports |
| Past recommendation was rejected | Log veto and reduce future *suggestion preference* only where owner approved | Rewrite approved metric formula or claim a causal failure automatically |

## 2. Proposed bounded implementation packets

Each packet is **candidate work**. Story IDs remain the existing canonical IDs; new CI identifiers are descriptions only.

### CI-0 — Human concierge context intake (release-adjacent, not a product feature)

**Possible home:** Friday beta runbook / manual operations documentation; no new software story required unless owner later approves one.  
**Input:** explicit customer goal, audience, dataset column dictionary, known KPIs, decision horizon, preferred report format, consented sharing method, business restrictions.  
**Outputs:** an intake worksheet; analyst approval checklist; completed report with a provenance appendix if possible.

**Proposed acceptance criteria**
- CI0-AC1: intake distinguishes agency owner, decision maker and analyst; identifies who owns KPI approval and who can authorize client data use.
- CI0-AC2: each report references a documented objective, known limitations, permitted time period and reviewed KPI definitions, or explicitly states they were unavailable.
- CI0-AC3: no data sent to agents beyond existing approved data-handling policy; no production system or self-serve claim added for launch.
- CI0-AC4: on two agency-shaped *synthetic* examples, a reviewer can explain why the relevant analyses differ without requiring new model code.
- CI0-AC5: confidential intake and sample uploads are stored only in approved secure locations with the beta's retention/deletion policy, not committed to Git.

**Gate:** owner confirms manual questionnaire and privacy language; beta release remains independent.  
**Tests:** human walkthrough, copy truth review, blank/unknown response path.  
**Suggested outputs:** 1-page worksheet; blank metric-definition review sheet; review rubric. These are proposed, not included as live customer features.

### CI-1a — Business context and trusted metric contract (Epic 4 planning)

**Potential stories:** 4.1 Database Schema & Auth Foundation, 4.1a Config-to-Project Migration, 4.3 Analysis Configuration UI and 4.10 Onboarding Flow.  
**Dependency:** existing project schema design; migration must preserve existing cleaning-policy and baseline semantics.

**Proposed acceptance criteria**
- CI1A-AC1: versioned optional context and metric definitions attach to the existing project/tenant boundary, not a separate conflicting owner graph.
- CI1A-AC2: deterministic validations reject impossible periods, ambiguous units, missing denominators and nonapproved input mappings.
- CI1A-AC3: old CLI/config and generic DQA/report paths remain compatible; context absence does not alter metrics.
- CI1A-AC4: human approval is required before changing a metric formula or cross-client reuse scope.
- CI1A-AC5: approved definition changes produce a new version; prior report evidence continues to resolve to its historical version.
- CI1A-AC6: no required goal-refinement wizard; optional review is compatible with 4.10's first-report-with-sensible-defaults outcome.
- CI1A-AC7: schema threat model includes client role, agency role, data owner, scope, retention, export/erasure and audit event.

**Gate:** human-approved 4.1 or separately filed story; architecture review for new schema/auth/shared models; not loop-eligible by assumption.  
**Tests:** schema-version and migration compatibility, missing fields, metric-denominator refusal, generic-mode parity, backward serialization.

### CI-1b — Secure persistence and governance (Epics 6–7)

**Potential stories:** 6.1 Multi-Tenant Data Isolation, 6.4 Security Hardening, 7.1 Role Hierarchy, 7.2 Audit Log, 7.4 API Tokens.  
**Dependency:** CI-1a approved schema and real authenticated tenant/project identity.

**Proposed acceptance criteria**
- CI1B-AC1: RLS plus server authorization prevents any principal from reading, searching, mutating or inferring another tenant's or client-scope context.
- CI1B-AC2: no frontend-provided tenant/user ID is accepted as authorization.
- CI1B-AC3: all approval/version/revoke/erase events leave the required audit evidence without retaining prohibited raw sensitive values.
- CI1B-AC4: deletion/DSAR and retention jobs include context, metric mapping, derived artifacts and cached context; separately justify immutable audit retention.
- CI1B-AC5: a revoked or superseded context version cannot be selected for new computations without authorized explicit historical replay.
- CI1B-AC6: backups, retrieval caches, search indexes and model prompts preserve the same authorization boundaries.
- CI1B-AC7: wrong-tenant, cross-client, lost-role, revoked-token and concurrent-update security tests fail closed.

**Gate:** RLS/roles/audit independent security review and corresponding canonical story acceptance before customer-facing persistence.  
**Tests:** malicious cross-tenant request attempts, authorization matrix, concurrent update/version pinning, prompt and log leakage, erasure replay.  
**Critical:** do not generalize the existing 7.7 cross-tenant *internal customer journey dashboard* into permission to access customers' source data.

### CI-2 — Context-aware analysis planner (Epic 8; Epic 9/10 consumers)

**Potential stories:** 8.1 Advanced Analytics, 8.4 Deterministic Model Selection, 8.5 Recommendation Agent, 8.7 Natural-Language Querying, 8.8 Report Customization; 9.5 Root Cause and 10.1–10.6 for constrained simulations.  
**Dependency:** validated metric definitions, evidence contracts and relevant underlying analytics capabilities.

**Proposed acceptance criteria**
- CI2-AC1: planner selects only allowlisted analyses whose requirements and entitlements are satisfied.
- CI2-AC2: identical source fixture + different approved goals yields relevant different plans; no-context fixture preserves current generic output.
- CI2-AC3: model outputs contain analysis identifiers, not arbitrary code; actual aggregations and tests run in the deterministic validated engine.
- CI2-AC4: every plan carries context version, metric definitions, rationale, missing-input list and whether approval is needed.
- CI2-AC5: no fabricated CAC, ROAS, LTV, margin, conversion rate or statistical significance; unverifiable inputs are flagged or cause abstention.
- CI2-AC6: client can invoke analytics help from report/findings context, but no unsolicited wizard, smart-prompt push, or unrequested campaign intervention.
- CI2-AC7: quantified impacts and alternative scenarios are computed only through Epic 10's deterministic simulation with explicit assumptions; 8.5 identifies opportunities only.
- CI2-AC8: no result is labeled causal absent an appropriate validated design; correlated observations remain evidence-limited.

**Gate:** Epic 8 relevant canonical story review; independent statistical and prompt-injection test review. Epic 9/10 conclusions become available only upon their separate acceptance.  
**Tests:** metric golden fixtures, parameter boundary fuzzing, no-input fallback, wrong-context and wrong-version handling, unreconciled currencies and attribution, agent output schema rejection.

### CI-3 — Evaluation, traceability and analyst review (Epic 11)

**Potential stories:** 11.1 Eval Harness Infrastructure, 11.2 Benchmark Datasets, 11.3 Confidence Controls, 11.5 Decision Traceability, 11.7 Escalation/Self-Disable; 7.2 audit; 8.7 findings query.  
**Dependency:** CI-2 candidate analysis plans, stable definition and source references; full customer rollout also needs CI-1b secure context.

**Proposed acceptance criteria**
- CI3-AC1: benchmark set includes two materially different agency goals over a common dataset; a generic fallback; missing denominator; mixed currency; inconsistent attribution; intentionally conflicting definitions; tenant-boundary attacks.
- CI3-AC2: each model/version is evaluated against a fixed, versioned, expert-reviewed answer set with at least: plan relevance, false positive analyses, correct abstention, numeric integrity, authorization, evidence completeness and reviewer agreement.
- CI3-AC3: owner and reviewer **pre-register quantitative ship thresholds** and confidence handling in the approved story. Do not assert unmeasured 95%/99% accuracy claims.
- CI3-AC4: each candidate plan records accepted/rejected alternatives, evidence references, model identifier/version, context version, reviewer override and outcome availability.
- CI3-AC5: low confidence, stale definitions, prompt-injection signals, permission failures and schema-validation failures cause safe defer or generic fallback.
- CI3-AC6: replay of historical findings uses pinned versions and produces an identifiable result; corrections never silently overwrite issued reports.
- CI3-AC7: audit covers prompt/context versions and human review without storing raw confidential customer rows or chain-of-thought.

**Gate:** Epic 11 evaluation infrastructure and security governance approved for the feature. This is distinct from Tier-4 *autonomous cleaning*, which remains Enterprise-only with its own consequence-disclosure and precision/recall gates.  
**Tests:** held-out benchmark, permission red team, drift in recommendation quality, adversarial context and misleading column names, audit replay.

### CI-4 — First marketing agency context pack (Epics 12–13)

**Potential stories:** 12.1 Adapter Interface, 12.4 Generic Backward Compatibility, 12.2/12.3 Scoring + DQA Penalty; 13.1 Marketing Adapter, 13.5 Campaign/Funnel, 13.7–13.9 A/B.  
**Hard dependency:** Epics **3, 8, 9 and 10** are all done per current pre-vertical gate, *then* Epic 12; no earlier full vertical adapter.

**Proposed acceptance criteria**
- CI4-AC1: pack accepts approved agency/client profile, attribution approach and KPI registry mapping; does not assume every agency has the same funnel or qualified-lead definition.
- CI4-AC2: creates plan recommendations appropriate to lead generation versus e-commerce, with missing data clearly surfaced.
- CI4-AC3: packs are optional and additive; generic mode remains byte-for-byte or contract-equivalent for existing fixture outputs under 12.4's regression requirement.
- CI4-AC4: MOS/other scores use printable deterministic formulas and DQA penalty per current 12/13 specifications; no silent weight learning.
- CI4-AC5: A/B output respects BH FDR default, sequential-peeking correction, achieved power/MDE and explicit underpowered-null labeling; cross-reference existing 13.7–13.9, not a rewritten alternate test.
- CI4-AC6: each client-scope request enforces approved metrics and roles; no PII is exposed in shared agency benchmarks.
- CI4-AC7: paid-pack entitlement or SKU is *not* assumed to be included in Professional; packaging requires a separate product/billing decision.

**Gate:** canonical pre-vertical gate, adapter security review, exact-SHA independent statistical review and first-customer approval.  
**Tests:** objective-specific golden reports, generic-mode regression, formula tests, multi-client data-leak tests, marketing A/B correctness.

### CI-5 — Evaluated organization memory (PRD Phase 16 vision)

**Potential owner:** vision-phase story after context contracts, tenant security, proven feedback utility and evaluation data. Do **not** assign a new canonical epic number automatically.

**Proposed acceptance criteria**
- CI5-AC1: feedback is recorded as per-tenant/project approved preference or outcome evidence; no silent writes to metrics or clients' configurations.
- CI5-AC2: recommendation-ranking improvements are evaluated on held-out examples versus a frozen baseline, controlling for leakage, selection bias and recent context.
- CI5-AC3: users can inspect, correct, revoke and erase remembered preferences, subject to an explicitly justified audit-retention exception.
- CI5-AC4: no raw tenant datasets used for shared training, inference augmentation across organizations or industry benchmarking without distinct consent and legal review.
- CI5-AC5: feedback from an invalid or later-disputed outcome cannot automatically become a new truth; keep observed outcomes distinct from inferred causation.
- CI5-AC6: a killed/disabled memory layer returns to a deterministic generic/approved-profile baseline without corrupting historical artifacts.
- CI5-AC7: no self-modifying workflows or autonomous operational execution enter scope through a preference-memory feature.

**Gate:** Phase 16 promotion, privacy/security review, pre-registered eval uplift, owner approval and explicit customer-facing consent.

## 3. Milestone scorecard (candidate measures, NOT claims)

| Milestone | Useful test metric | Acceptance approach |
| --- | --- | --- |
| M0 manual pilot | % briefs with verified KPI owner; time to clarify missing context; reviewer usefulness rating | Record baseline on approved synthetic / consented pilot cases, publish no performance claims |
| M1 contract | round-trip/version integrity; invalid definition rejection; generic parity | Exact fixture tests, schema review |
| M2 secure scope | cross-tenant/client denial, revocation, erasure success | **Zero known unauthorized access in tested paths** and no Critical/High security findings |
| M3 planner | plan precision/recall vs analyst reference, appropriate abstentions, compute/semantic mismatch rate | Pre-register owner-approved thresholds and run held-out evaluation |
| M4 agent pilot | correct evidence citations; unsupported numeric claim rate; override rate; time saved | Independent human-scored blind cases and rollback rehearsal |
| M5 agency pack | lead-gen/e-commerce plan differentiation, generic parity, qualified metric accuracy | Real consented pilot examples plus statistical fixtures |
| M6 memory | held-out improvement, deletion completeness, no cross-client transfer, refusal rate | Demonstrate statistically credible uplift and reversible memory |

**No fabricated thresholds:** the repo has no validated agent-planning benchmark or velocity baseline. The first eval story must establish those with a human before an external success claim or production enablement.

## 4. Required review artifacts and Definition of Done additions

Every future CI-related implementation story should attach, as relevant:

1. Exact canonical story ID, branch, base SHA, changes allowed, dependencies in **done** state and human authorization for high-risk work.
2. A data-flow diagram showing tenant/client/project scope, cache/embedding/LLM boundaries and retention.
3. Definition-version migration and rollback procedure with generic-mode compatibility evidence.
4. Computation truth test: source fixture + approved formula → reproducible result; input gaps → noncomputable.
5. Two-context test: same data + different goal → different eligible plan with traceable reasons.
6. Adversarial test: ambiguous column semantics, wrong attribution, prompt injection, cross-tenant access and invalid scope.
7. Human reviewer decision, fixed SHA, required uv run pytest / npm test / npm run build results and task-specific security/statistical tests.
8. User-facing disclosure: what is observed, inferred, projected, not computable, and requires review.
9. Customer data minimization and revocation test; no private files or secrets committed.
10. Final checkpoint: CI status, exact code SHA, approved vs unapproved scope, remaining blockers and human merge decision.

## 5. Questions that must be resolved before story filing

1. **Hierarchy:** Is an agency the tenant, with many client-scoped projects, or do clients each own separate tenants? What does an agency analyst see across clients?
2. **Approval:** Who may define a KPI, approve it for a client, update formula versions and authorize historical replay?
3. **Input taxonomy:** Which first two agency datasets and metrics should be supported reliably, rather than claiming arbitrary data understanding?
4. **Conflicts:** If the same KPI name is defined differently by agency and client, which wins? Suggest explicit client-level overrides with human approval, never silent precedence.
5. **Sources:** Which source types are allowed initially? Current beta supports CSV only; multi-source joins, marketing ad APIs and derived customer identity are **not** implemented.
6. **Memory/retention:** What approved context metadata may be retained beyond beta file deletion, and how do users revoke it?
7. **Usage and packaging:** Is a future Context Intelligence Pack per-agency, per-client, per-project or Enterprise? Avoid retroactively changing current PRD tiers.
8. **Evaluation:** Who curates independent gold-standard analyses and decides the threshold for safe customer-facing recommendations?

## 6. Human decision checklist for this draft PR

- [ ] Approve the *strategic* Option B placement while retaining existing pre-vertical and per-story gates.
- [ ] Agree that M0 remains a human-run concierge operation, not a new beta software requirement.
- [ ] Select the tenancy/client hierarchy for a future 4.1 architecture decision (do not decide by merger alone).
- [ ] Approve separation of proposed metric definitions from unapproved model-generated assumptions.
- [ ] Confirm no unreviewed cross-client learning, raw-data memory or autonomous business decisions.
- [ ] Authorize an architect to create **individual authoritative story proposals** with narrow file scopes (still not automatic sprint promotion).
- [ ] Leave canonical sprint statuses, loop_eligible flags, merges and deployment under Marvin's independent control.

**This spec is not authorization to edit AGENTS.md, the master PRD, canonical epic/story files, sprint-status.yaml, customer database schema, billing rules or runtime code.**
