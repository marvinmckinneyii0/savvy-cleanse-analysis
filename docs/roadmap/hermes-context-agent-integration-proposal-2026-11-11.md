# SAINT — Hermes Context Agent Integration Proposal

**Status:** PROPOSED / documentation-only / owner authorized proposal update on 2026-11-11  
**Product:** SAINT (Savvy Analytics Intelligence) — B2B agency-first, reusable across verticals  
**Implementation readiness:** NOT AUTHORIZED; no package installation, API key, pipeline integration, permissions, runtime service or agent deployed in this PR  
**Related:** [Option B roadmap](saint-context-intelligence-option-b-proposal-2026-11-11.md), [context story packets](context-intelligence-story-packets-and-evaluation.md), [Epic 4.1 schema design](epic-4-1-context-intelligence-schema-design-2026-11-11.md)

## 1. Decision

**Evaluate Hermes Agent as an optional, replaceable Context Analysis Planner and Evidence Review assistant inside SAINT's existing Epic 8 / CI-2 and Epic 11 / CI-3 scopes.** It is **not** the tenant memory store, database, metric engine, production orchestration controller, authentication service or tool that changes client data. Begin with one human-supervised agency-context planning experiment on synthetic data. Adopt only if a held-out eval shows a meaningful improvement over a deterministic/no-agent baseline and a direct-LLM baseline without increasing risk.

**Recommended locus:** SAINT's backend application supplies a constrained, authorized, immutable per-request analysis packet to a sandboxed Hermes adapter; the adapter returns proposed analysis IDs/reasons/missing inputs. SAINT validates the proposal against an allowlist of deterministic engines, computes trusted metrics itself, then displays reviewable results. Hermes may later help inspect evidence records, but cannot be sole signoff.

**Friday November 13 concierge beta: zero Hermes dependency.** The beta remains human-delivered CSV analysis via the existing deterministic pipeline. Keep this proposal out of the critical path.

### Product positioning

- **Buyer:** marketing agency owner, with analysts/operations staff as users and buying influencers. No consumer-first workspace or broad B2C pricing assumptions.
- **Business objective:** distinguish SAINT from commodity dashboards through reviewed business context, agreed KPI definitions, analysis relevance, measurable saved analyst time, verified evidence and a customer-controlled feedback record.
- **First vertical:** marketing agency context pack only after the canonical pre-vertical gate (Epics **3, 8, 9, 10** closed before Epic 12); a generic analytic/context planner may be prototyped before a vertical adapter.
- **Moat thesis:** proprietary **permissioned client-defined context and verified metric history**, not dependence on a single open-source agent framework.

## 2. Architecture and trust boundaries

    Authenticated SAINT request
         |
         v
    Verified organization + client/project grant  (server checked, RLS and object policy)
         |
         v
    SAINT context service
      - retrieves approved business goals / metric definition versions
      - validates dataset schema and source evidence
      - removes/blocks secrets, raw PII and unauthorized data
      - limits context to requested project/version and purpose
         |
         v
    SAINT AnalysisPlannerAdapter interface
       |-- deterministic planner (safe default)
       |-- direct-LLM baseline (offline evaluation only)
       '-- Hermes adapter (feature-flagged, disabled by default)
              |
              v
        isolated ephemeral reasoning task
        - *no* tenant DB credentials, write/terminal/browser/email tools
        - no persistent Hermes memory or project context injection
        - strict egress, resource/time/cost budgets
        - bounded prompt + typed output only
              |
              v
    SAINT server validates suggested analysis IDs/parameters (Pydantic)
         |
         v
    SAINT deterministic stats/DQA/drift/simulation engines
         |
         v
    versioned provenance + human review + published findings

**Database authority:** the approved Business Context Profile and Trusted Metric Registry remain SAINT-owned project-scoped, versioned and authorized as designed in the Epic 4.1 package. Hermes has no direct cross-tenant query permission and may never use its own persistent memory as a substitute.

**Agent responsibility:** select/evaluate *which existing analysis to perform* and explain the rationale; never produce client-facing numeric values, approve metric formulas, modify CSVs, authorize payment, infer missing denominators as facts, diagnose causation without evidence, or take external agency actions. Any analysis request that cannot be satisfied yields an explicit not-computable / requires-review result.

### Candidate interface (illustrative; not code to merge)

    AnalysisPlannerRequest {
      request_id, scoped_project_ref, approved_context_version,
      approved_metric_versions, eligible_analysis_ids,
      allowed_typed_parameters, dataset_schema_summary,
      data_quality_summary, user_question, execution_budget
    }

    AnalysisPlannerResponse {
      candidate_analysis_ids_and_parameters,
      relevance_rationale, missing_inputs,
      unsupported_or_conflicting_metrics,
      human_review_required, provenance,
      agent_model_version_and_provider, status
    }

Only SAINT creates the request and enforces its privileges. Hermes must not be able to mutate or pick a different `scoped_project_ref`; it does not receive raw auth tokens, object-storage keys or a general database connection. All output fields must pass a strict schema and membership/entitlement validation. An invalid or inaccessible suggestion is ignored, audited and escalated.

## 3. Why Hermes is plausible, but not selected yet

Official Nous Research docs confirm an importable Python `AIAgent` entry point with a FastAPI example and flags such as `skip_memory=True`, `skip_context_files=True`, `quiet_mode=True`, `save_trajectories=False`, `max_iterations` and `enabled_toolsets`. The same docs explicitly recommend disabling persistent memory for stateless API endpoints and creating a fresh agent per task. Hermes includes terminal, browsing and MCP capabilities, which introduce a **larger execution surface** than a simple LLM call; provider support and exact tool behavior must be validated against a pinned release.

**Official references**:
- https://hermes-agent.nousresearch.com/docs/guides/python-library
- https://hermes-agent.nousresearch.com/docs/user-guide/security
- https://hermes-agent.nousresearch.com/docs
- https://github.com/NousResearch/hermes-agent/blob/main/LICENSE (MIT, subject to dependency and provider license review)

**Important dependency detail:** current official Python-library documentation describes using Hermes from its source checkout with `uv sync`; it says it does not publish a supported wheel/source distribution for `requirements.txt`. Do **not** casually add `hermes-agent` to SAINT production dependencies or assume an official pip package. Prefer a separately pinned, isolated adapter worker *only if* necessary after evaluation, preserving SAINT's Python environment and deployability.

**Memory control:** use a fresh instance per analysis request and disable Hermes's general cross-session memory and context-file ingestion in the adapter. Avoid trajectory capture of customer prompts by default; never persist client data to Hermes's global skill/memory stores, RAG/FTS caches, Telegram/Discord channels, or third-party connectors.

**Security control:** the docs' command-approval system is useful but **is not a sandbox**. Even with `enabled_toolsets` restrictions, safety requires operating-system/container policy, process isolation, network restrictions, read-only data access and no customer secrets. Unattended approvals must fail closed; no `yolo` or approval-mode `off`.

**Orchestration constraint:** SAINT's existing reconciliation forbids n8n and contemplates LangGraph or an MIT-licensed equivalent for orchestration. The MIT license is potentially compatible with evaluating Hermes as an adapter; it **does not** override the architectural decision, license review or per-story approval of an orchestration change. SAINT retains the loop controller and human merge policy.

## 4. Placement by existing roadmap story

| Candidate | Canonical owner | Allowed proposal | Explicit boundary |
| --- | --- | --- | --- |
| Synthetic spike | CI-0 documentation or separately approved evaluation task after beta | Compare planner outputs for two agency goal profiles and missing-data cases | No Hermes dependency in Nov 13 launch |
| Context foundation | 4.1 project/auth, separate CI-1 spec; 6.1 RLS, 7.1 roles, 7.2 audit | Define versioned authorized context packet and metrics references | No customer-context persistence ahead of tenant/client isolation |
| Context planner | 8.1, 8.4, **8.5**, **8.7** | One optional `AnalysisPlannerAdapter`; Hermes returns allowlisted suggestions and confidence/abstention, not values | 8.5 opportunity-only; 8.7 pull-not-push/no unsolicited goal wizard |
| Diagnostic/simulation | Epic 9 and 10 | Parameterize validated existing methods from plan | Root cause requires evidence; projected impact belongs to Epic 10 only |
| Governance/evals | 11.1, 11.2, 11.3, **11.5**, 11.7 | Evaluate planner relevance, evidence, numeric fidelity, isolation and reviewer overrides | Do not conflate advisory planning with Tier-4 autonomous data remediation |
| First vertical | 12.1/12.4 then 13.1/13.5 | Marketing-agency context templates with direct business generic fallback | All of Epics 3,8,9,10 must close before Epic 12 |
| Memory | Phase 16 vision | Approved preference/outcome feedback in SAINT DB, optional ranking experiments | No global per-client model fine-tuning or memory sharing by default |

Proposed new evaluation/adapter work requires a **human-filed and approved single BMAD story or approved amendment**. No `sprint-status.yaml` edit and no `loop_eligible` promotion in this PR.

## 5. Test-driven evaluation and selection gates

**Minimum fixture set**: one shared sample marketing CSV used under two contradictory goal profiles; missing qualified lead status; mixed currencies; missing profit costs; ambiguous conversion numerator/denominator; changed approved KPI revision; prompt-injected CSV text; user with another client's project ID; revoked grant; no available LLM provider; agent time/cost overrun.

**Pass/fail criteria for a prototype (pre-registered by an owner and reviewer before execution):**

1. **Metric integrity** — zero model-invented numeric values, formula changes or unsupported business metric labels in the test suite.
2. **Authorization** — zero unauthorized client/project context, leaked row content, secrets or tool-mediated access in adversarial fixtures.
3. **Analysis eligibility** — every selected analysis ID belongs to the allowlist and has satisfied inputs/capability tier.
4. **Abstention** — missing key definitions returns an explicit request-for-information or not-computable status; never guesses.
5. **Evidence trace** — each suggestion logs source reference, context version, metric definition version, analysis ID, model/version and review outcome, while excluding raw PII or provider reasoning traces.
6. **Human approval** — all client-facing recommendations remain reviewed during pilot; agent cannot deliver, bill or mutate the customer's data.
7. **Safe fallback** — agent disabled, provider outage, invalid schema, tool attempt or security alert returns the same honest generic capability or a clearly reported manual stop.
8. **Independent benefit** — a held-out, analyst-reviewed comparison finds measurable relevance/time benefit over direct LLM and deterministic planner baselines; numerical thresholds and cost/latency budgets are set *before* evaluation, not invented in this document.
9. **Provider constraints** — pinned license/dependency/provider review, network egress restrictions and concurrency handling are verified.
10. **Kill switch** — an authorized operator can disable Hermes without losing metric definitions, issued report provenance or the ability to run SAINT.

### Guarded pseudo-integration sketch (non-runnable by design)

    # In a future isolated worker, NOT in the public FastAPI route:
    # - Authorize tenant/project and minimize context first (SAINT backend)
    # - Verify Hermes release and actual tool whitelist through sandbox tests
    # - Use one fresh agent per task; disable persistent memory and context files
    # - Provide only typed, validated context and allowlisted analysis candidates
    # - Parse the final response into Pydantic AnalysisPlanProposal
    # - Reject unexpected fields, tool access, fabricated values, wrong-tenant refs
    # - Run numerical analysis only via SAINT deterministic engine
    # - Require human reviewer to approve client-facing conclusions

There is no need to build five agents now. Start with a single bounded context planner; add evidence checker and research assistant only if independent evaluation justifies additional providers, complexity and risk.

## 6. Delivery milestones (dependency-gated, not fixed promises)

| Milestone | Trigger | Deliverable / exit evidence |
| --- | --- | --- |
| H0 architecture / security decision | This draft reviewed | Confirm adapter boundary, provider/version, redaction/retention, implementation owner |
| H1 synthetic spike | After Nov 13 beta work; no sensitive data | Fixed fixtures; Hermes vs deterministic planner vs direct LLM; no side effects |
| H2 internal controlled pilot | Canonical CI-1 authorization + relevant Epic 8 work and held-out evaluation | Typed request/response, isolation, human review, budgeted execution |
| H3 prospective agency pilot | Required CI-2/3 test and customer data policy gates | Opt-in project-scoped authorized customers; validated metrics and traceability; kill switch |
| H4 domain pack | Canonical pre-vertical gate + Epics 12/13 acceptance | Marketing Agency Context Pack with approved template library |
| H5 reviewed memory | Phase 16 individually approved | Evidence-backed preference learning, revoke/delete and held-out lift |

**Scheduling:** no assertion that H2/H3 are ready in December or January; the current canonical backlog shows Epic 4–13 not delivered. Scope/date may only be committed after the dependent stories and validation pass.

## 7. Review decisions

- [ ] Accept one **optional** Hermes adapter rather than Hermes as the product foundation.
- [ ] Confirm an agency-first buyer focus; direct businesses remain supported by the generic project model.
- [ ] Keep BCP and metric definitions in SAINT-controlled secure storage; forbid Hermes global memory of customer facts.
- [ ] Request an isolated, fixture-only Hermes H1 trial after the concierge beta, separate from production code.
- [ ] Approve which provider/model and Hermes release to pin **after** compatibility/license/security tests.
- [ ] Assign human reviewers to evaluate planner quality and scope; select quantitative thresholds before testing.
- [ ] Do not change canonical sprint status, authoritatve story eligibility, billing, auth, migration or release gates through this documentation.

**End state now:** documented future option, **not integrated**. SAINT remains able to operate with no Hermes installed.
