# SAINT Context Intelligence — Option B Roadmap Change Proposal

**Status:** PROPOSED / documentation-only / owner selected strategic direction 2026-11-11  
**Repository:** marvinmckinneyii0/savvy-cleanse-analysis  
**Baseline reviewed:** main at 2b2ffb815c34935d2aa5e12c4fe538ea8bdc2df6  
**Decision requested:** approve the *scope and placement* for subsequent canonical story review; this document is NOT a story promotion or implementation authorization.  
**Primary objective:** build a defensible, reusable context-aware analysis capability on SAINT's existing deterministic analytics foundation, first validated with marketing agencies.  
**Priority:** Friday 2026-11-13 concierge beta remains the release-critical path. No new platform obligation blocks that beta.

> Authority boundary: the master PRD controls product scope; prd-epic-reconciliation.md controls the existing epic order; sprint-status.yaml alone controls execution status and loop eligibility; AGENTS.md controls work and human-only merges. All CI-0..CI-5 identifiers below are *proposal labels only*, not canonical BMAD story IDs. No change to authoritative files, billing, production, deployment, or eligibility is made by this proposal.

## 1. Executive decision and product thesis

**Adopt Option B — progressive Context Intelligence across existing epics.** Do not insert a new execution phase ahead of the beta, or deliver a full marketing vertical adapter early. Instead:
1. Collect a small, consented context worksheet during the human-operated concierge service (CI-0).
2. Design a tenant/project-scoped Business Context Profile and a Trusted Metric Registry alongside the existing Epic 4 project foundation (CI-1).
3. Add hard isolation, versioning, retention, permissions, and audit evidence with Epics 6–7 before persistent cross-client SaaS usage (CI-1 governance).
4. Feed approved context/metrics into guided analysis and deterministic planning in Epic 8, with diagnostics and simulation continuing to live in Epics 9 and 10 (CI-2).
5. Apply measurable evaluation, traceability, refusal/defer rules and human review via Epic 11 capabilities before selling broad agent assistance (CI-3).
6. Ship a Marketing Agency Context Pack only after the unchanged pre-vertical gate permits Epics 12–13 (CI-4); graduate organization memory and feedback-informed ranking after evidence, in the existing Phase 16 vision (CI-5).

**What the moat might be:** compounding, permissioned business knowledge that informs *which questions matter* and *which metrics are reliable*. A generic LLM report or free-form chat is readily replicated. Client-approved meanings, consistent metric computation, workflow integration, provenance, evaluated recommendations, and correction history may be harder to replace. This is a hypothesis to test with real agencies, not a verified competitive advantage.

### Core invariant

**Agents may select and explain candidate analyses; validated deterministic code computes the numbers.** Agents may not invent metrics, silently alter a definition, run arbitrary code generated from a prompt, infer a missing denominator as fact, or execute consequential business decisions.

### Two example contexts for the same raw campaign file

| Input | Agency A: lead generation | Agency B: e-commerce |
| --- | --- | --- |
| Goal | Lower cost per qualified customer | Improve profitable repeat purchases |
| Metric focus | Qualified lead definition, CPL, lead-to-customer rate, CAC | ROAS, contribution margin, repeat purchase rate, LTV (only with necessary data) |
| Guardrail | A lead is not necessarily a qualified lead; ad spend alone is not CAC | Revenue is not gross margin; ROAS is not profit; customer IDs may be insufficient to establish repeat purchases |
| Correct SAINT behavior | Ask for or flag missing qualification and customer conversion fields; suppress uncomputable metrics | Ask for or flag COGS/returns/cohort/customer identity; suppress uncomputable profit and retention metrics |
| Acceptable output | Valid metrics, source/period, confidence/limitations, opportunity with human review | Valid metrics, source/period, confidence/limitations, opportunity with human review |

## 2. Side-by-side roadmap placement

The *operative* roadmap is the reconciliation and epic definitions, not the historical 16-phase waterfall retained in the PRD.

| Existing delivery group (ledger 2026-11-11) | Existing canonical scope | Proposed additive context-intelligence placement | Boundary |
| --- | --- | --- | --- |
| Concierge release; Epics 1–2 done; Epic 3 in progress | CSV DQA, opt-in rule cleaning, insight/report, drift and monitoring | **CI-0:** manual context worksheet, analyst review, provenance checklist | No new runtime promise, agent automation or beta blocker |
| Epic 4 backlog | 4.1 project/auth schema; 4.1a config migration; 4.3 configuration UI; 4.4 report history; 4.10 onboarding | **CI-1:** optional versioned Business Context Profile and Trusted Metric Registry owned by tenant/project; UI display and human correction | Any schema/auth change must be approved in an amended or newly filed authoritative story; no new required wizard |
| Epics 5–7 backlog | Billing/gating; tenant RLS; observability, auth, audit/roles, admin | **CI-1 security:** tenant isolation, permission checks, data minimization/retention, immutable definition/version/audit events | No context-based billing mutation; no access until policies are tested |
| Epic 8 backlog | 8.1 advanced statistics; 8.4 deterministic model choice; 8.5 opportunity-only recommendation; 8.7 optional NL query; 8.8 customization | **CI-2:** approved context and metrics constrain which analyses are eligible; evidence-linked analysis plan; explicit missing-input and uncertainty behavior | Preserve 8.5 opportunity-only (no estimated impact) and 8.7 pull-not-push/no goal-refinement wizard |
| Epics 9–10 backlog | Drift/root-cause chains; deterministic scenarios/sensitivity | **CI-2 extension:** contextual diagnostic questions and constraint-aware simulations; hypotheses labeled as hypotheses | Root cause remains evidence-limited; quantitative impact is Epic 10 only |
| Epic 11 backlog | Eval harness, confidence thresholds, Tier-4 remediation governance, decision traceability | **CI-3:** evaluate analysis selection correctness, metric fidelity, citations, abstention and per-tenant safety; link to 11.5 decision trace | Do not conflate context-driven analysis planning with autonomous Tier-4 data remediation; enterprise risk gates remain |
| Epic 12 backlog | Adapter interface, scoring, DQA penalty, generic fallback | **CI-4 generic/vertical interface:** optional context provider and metric mapping contract for adapters | **No Epic 12 implementation until Epics 3, 8, 9 and 10 close** |
| Epic 13 backlog | Marketing adapter, campaign/funnel, scoring, A/B rigor | **CI-4 Marketing Agency Context Pack:** client and channel profiles, agreed funnel stages, conversion denominators, reusable approved playbooks | Marketing is the first vertical; no claim that all agencies share one KPI definition |
| PRD Phases 15–16 vision | Agent workflows and self-improving/organizational memory | **CI-5:** feedback-informed ranking and scoped organization memory, with explicit permissions and replayable evaluations | Vision only; no production self-modifying agent or auto-training approval |

### Explicitly out of scope

No new self-serve features for the November 13 beta; no direct payment/price change; no new permanent customer memory before secure storage and isolation; no cross-tenant learning or benchmark sharing by default; no industry benchmarking without lawful consent/aggregation review; no autonomous external operations; no arbitrary LLM-created pandas execution; no n8n at any SAINT layer; no changes to FlowIQ's document/workflow responsibilities. A/B experimentation remains in Epic 13 with its existing statistical gates.

## 3. Dependency DAG and critical boundaries

The proposed nodes are planning labels; they do **not** change the canonical dependency graph.

    Beta human workflow [CI-0] --no runtime dependency--> context requirements / anonymized test fixtures
       |
       +--> Epic 4.1: tenant/project entity + explicit human-approved scope
             +--> proposed CI-1 profile + metric registry contract
             +--> Epic 4.1a: existing config migration remains owned by 4.1a
             +--> Epic 4.3 / 4.10: optional display, corrections, default setup
                    |
                    +--> Epic 6.1 RLS / 6.4 security + Epic 7.1 roles / 7.2 audit
                           |
                           +--> guarded CI-1 persistence / client-facing rollout
                                      |
    Epic 8.1 statistical foundation -----------+
    Epic 8.4 deterministic selection ----------+--> CI-2 bounded analysis planner
    Epic 8.5 opportunity agent ----------------+       |
    Epic 8.7 optional findings query ---------+       +--> human-reviewed, traceable findings
    Epics 9 + 10 (diagnostics/simulation) -----+       |
                                                      +--> CI-3 evaluation on fixtures + review
    Epic 11.1 / 11.2 / 11.3 / 11.5 -------------+------+
                                                      |
    HARD PRE-VERTICAL GATE: Epic 3 + Epic 8 + Epic 9 + Epic 10 ALL done
                                                      |
                                                      v
                                  Epic 12.1/12.4 adapter contract / generic fallback
                                                      |
                                                      v
                                Epic 13.1/13.5 Marketing Agency Context Pack
                                                      |
                        secure, consented outcomes + reviewed corrections + eval gains
                                                      |
                                                      v
                                  CI-5 organization memory (Phase 16 vision)

**Important non-dependencies:** CI-0 is a *human-delivered template* and does not require an Epic 4 database; CI-1 schema design can be reviewed in parallel with existing project planning but production persistence requires security gates; an offline CI-2 evaluation fixture is not permission to expose an agent to customers; CI-4 does not jump past the pre-vertical gate. Epic 11's full Tier-4 autonomy remains Enterprise-only and is not a prerequisite to merely capturing a client goal manually.

## 4. Milestones, release evidence and planning estimates

These are **target windows, not earned release dates**. The repository deliberately omits duration estimates pending a velocity baseline. After the November beta, estimate and approve work one canonical story at a time. A failed gate moves the target rather than reducing protections.

| Proposed milestone | Earliest planning window | Deliverable | Exit evidence / approval |
| --- | --- | --- | --- |
| **M0 — Manual context pilot (CI-0)** | Nov 13 beta / Nov 16–27 review window | Versioned blank intake worksheet; analyst-run 2–3 contrasting example briefs with approval | Beta checks unaffected; no raw client data or confidential names in Git; owner verifies metric definitions and report limitations |
| **M1 — Foundation contract (CI-1 design)** | After beta, Epic 4 story planning | Project-scoped context schema and trusted metric interface proposal; migration/backward-compat design | Architecture/security review; human-approved changes to 4.1/4.1a or separate filed story; no database writes from this PR |
| **M2 — Secure context persistence** | Conditional on Epic 4 + 6.1 + 7.1/7.2 dependencies | CRUD, versioning, field-level approvals, tenant-scoped reads/writes, redaction/erasure | Negative cross-tenant tests, permission checks, audit validation, retention/deletion tests, security review |
| **M3 — Supervised analysis selection (CI-2)** | Conditional on relevant Epic 8 story acceptance | Candidate analyses ranked by authorized context; abstain on missing inputs; per-result provenance | Deterministic reference fixtures, full regression suite, independent reviewer, human approval; no impact estimates outside Epic 10 |
| **M4 — Eval-gated agent pilot (CI-3)** | Conditional on Epic 11 evaluation/traceability infrastructure and M3 | Benchmarks by agency objective, rubric and failure controls, traceable human override | Measured thresholds approved *before* pilot; no cross-tenant leakage, unsupported KPI claims or unsafe action paths |
| **M5 — Marketing Context Pack (CI-4)** | Only after canonical pre-vertical gate and Epic 12 | Agency/client/channel context mapping and metric templates for Epic 13 | At least two meaningfully different agency examples; generic no-adapter regression; owners approve vertical SKU and consent |
| **M6 — Feedback memory (CI-5)** | Later Phase 16 vision, not scheduled | Approved preference/decision history, feedback learning, revocation and rollback | Demonstrated held-out quality improvement, deletion/revocation, no covert cross-client transfer, owner-controlled activation |

**Forecast discipline:** Previous informal December/January prototype/pilot ideas remain hypotheses, **not commitments** for M2–M5. M0 can be manual almost immediately, but production multi-tenant intelligence has major backlog dependencies. Never present all six milestones as a single short sprint.

## 5. Acceptance criteria for the product behavior

Acceptance criteria below are proposed for human filing into the relevant canonical stories; exact fixtures, thresholds, sizing and ownership must be approved in those stories. More detailed test packets are in [context-intelligence-story-packets-and-evaluation.md](context-intelligence-story-packets-and-evaluation.md).

1. **Client isolation:** an agency may contain multiple client workspaces; each context, metric definition, run and correction is bound to the authorized tenant/project/client scope; cross-client reuse requires an explicit owner decision and security model. Deny access server-side, never trust browser-provided IDs.
2. **Definition truth:** every computed business metric identifies an approved definition version, owner, numerator, denominator, units/currency, timezone/calendar and aggregation rule; missing inputs yield **not computable**, never fabricated zeroes or estimated values presented as observed.
3. **Analysis correctness:** with identical CSV data but different approved business contexts, the system selects meaningfully different eligible analyses; with no approved context it preserves generic-mode outputs and does not claim personalization.
4. **Evidence chain:** every displayed finding includes source dataset fingerprint, run identifier, metric/formula version, window, computation artifact, warnings and whether a recommendation was human-approved. The numeric result must be independently reproducible.
5. **Agent boundary:** any LLM receives validated computed summaries and only approved metadata; it recommends analysis identifiers/parameters from a versioned allowlist, never invents numbers or executes raw expressions.
6. **Abstention and disclosure:** unknown context, ambiguous conversion events, mixed currencies, weak sample sizes, missing business constraints and unsupported causal attribution produce explicit warnings or human-review requests.
7. **Feedback governance:** suggestions, edits, approvals, overrides and observed outcomes are separate records. Corrections do not silently rewrite previously published metric values. No client dataset is repurposed for model training by default.
8. **Performance and safety:** context retrieval and planning must be bounded in cost, latency, payload size and permission scope; errors fall back to honest generic analysis or a human stop, not unauthorized data exposure.
9. **Analytics taxonomy:** descriptive, diagnostic, predictive and prescriptive outputs remain distinct; preserve the current analysis_class capability gate where relevant. A forecast is not a causal fact; a deterministic scenario projection is not a forecast.
10. **UI disclosure:** distinguish *computed result*, *agent suggestion*, *hypothesis*, *simulation*, *missing data*, *human decision* and *future capability*. No misleading autonomous/semantic/white-label claims before release.

## 6. Governance and release policy

- **Source hierarchy:** AGENTS.md, canonical sprint-status.yaml, selected authoritative BMAD story, PRD and reconciliation; this proposal supplies *candidate* acceptance criteria only.
- **Human-only changes:** Marvin approves roadmap scope, all status promotions, loop_eligible flags, schema/auth/tenant decisions, billing/offer changes, privacy commitments, merges and deployments. Strategic approval of Option B does not itself promote a single story.
- **One-story boundary:** each supervised run changes only one approved story. New work affecting 4.1 shared schema, 6.1 tenant access, 7.2 audit or statistical truth is high-judgment and cannot be made loop-eligible by this proposal.
- **Review and CI:** use exact-SHA independent review; uv run pytest, npm test, npm run build, story-specific tests, security review for all stories (resolve Critical/High). Manual UI and client-report review as applicable; record CI, fixture, and source version.
- **Data governance:** data minimization; no raw client CSVs, API keys, credentials, PII, or identifiable client examples in Git, prompts, logs or snapshots. Partition any production memory by client/tenant with RLS, encryption, retention/erasure, per-field consent and role authorization. Avoid raw user rows in embeddings by default.
- **No invisible learning:** initial learning is versioned, approved preferences and feedback ranking—not autonomous weights, unreviewed metric changes or foundation-model fine-tuning. Anonymized cross-tenant benchmarking or model learning is separately gated and opt-in, with legal/privacy review.
- **Agent autonomy boundary:** business recommendations are advisory; human approval for consequential client-facing decisions and all mutations. Tier-4 automated data remediation (Epic 11) remains per-finding explicit opt-in, Enterprise-only, evaluation-gated and working-copy-only.
- **Orchestration:** no n8n; if orchestration becomes necessary, use the repository-approved LangGraph or MIT-licensed equivalent after explicit story approval. Do not import complex agent frameworks into the beta.
- **Launch policy:** PR #82 (About), #83 (pricing), #79 (market research) and #73 (visual brief) are separate change streams; this PR neither merges nor depends on them. M0 must not delay launch readiness, legal review, lead capture, report verification or the existing pricing sign-off.

## 7. Decision record for owner review

| Decision | Proposed default | Needs explicit human confirmation before execution |
| --- | --- | --- |
| Product positioning | Context-intelligent, evidence-backed analysis as a core capability; agency pack is first proof | Approve product description and customer promise |
| Storage model | Extend project-scoped entity in existing 4.1 planning; agency/client hierarchy optional and security-scoped | Exact tenancy boundary, role permissions, schema migration |
| Metric registry | Approved, versioned per-tenant definitions with dataset mappings and conflict policy | Canonical ownership/approval roles, import/export behavior |
| Interrogation | Context-aware report on user invocation, optional findings-query; no unsolicited wizard | Scope of 8.7, evidence contract and queries |
| Evaluation thresholds | Establish benchmark and pre-register thresholds, not guessed launch percentages | Accuracy, abstention, false-positive, leakage and confidence limits |
| Monetization | Do not change the PRD tier table or current concierge price; vertical capability may become future separate SKU | Packaging, pricing, upgrade entitlement and contracts |
| Learning | Approved preference memory only; no automatic retraining or tenant pooling | Consent, deletion, opt-in and model governance |
| Timing | Gate-driven, report realistic forecast after velocity baseline | Story sequencing and staffing after beta |

## 8. Operational next actions (no implementation authorized by this document)

1. **Review this draft PR** for product positioning and governance first; keep it doc-only.
2. After beta, collect **permissioned manual examples** from an agency owner, operations/decision-maker and analyst; ask them to approve their metric definitions and what they would call a useful recommendation.
3. Human decides whether to amend 4.1/4.1a and 4.3/4.10 or file small **CI-1** canonical stories, and which can proceed only after 6.1/7.2. Do not alter the ledger through automation.
4. Have a separate architecture/security reviewer validate the proposed data contract and dependency DAG.
5. Only after human status promotion and dependency checks, implement one approved story at a time on isolated branches; validate and seek an independent fixed-SHA review. Stop at a draft PR for human merge.
6. Revisit quantified economics after 5–10 agency conversations; measure repeat use, approved insight rate and analyst time saved without making unsupported savings claims.

## 9. Existing references (unchanged in this PR)

- Canonical status: [_bmad-output/implementation-artifacts/sprint-status.yaml](../../_bmad-output/implementation-artifacts/sprint-status.yaml)
- Authority and workflow: [AGENTS.md](../../AGENTS.md) and [agent-system/completion-policy.yaml](../../agent-system/completion-policy.yaml)
- Operative epic ordering: [prd-epic-reconciliation.md](../../_bmad-output/implementation-artifacts/prd-epic-reconciliation.md)
- Schema ownership: [schema-extensions-spec.md](../../_bmad-output/implementation-artifacts/schema-extensions-spec.md)
- Master PRD scope: [saint-master-prd.md](../../_bmad-output/planning-artifacts/saint-master-prd.md)
- Epics: [4](../../_bmad-output/implementation-artifacts/epic-4-web-application.md), [6](../../_bmad-output/implementation-artifacts/epic-6-multitenant-scale.md), [7](../../_bmad-output/implementation-artifacts/epic-7-admin-control-plane.md), [8](../../_bmad-output/implementation-artifacts/epic-8-advanced-analytics.md), [9](../../_bmad-output/implementation-artifacts/epic-9-advanced-drift-rootcause.md), [10](../../_bmad-output/implementation-artifacts/epic-10-prescriptive-simulation.md), [11](../../_bmad-output/implementation-artifacts/epic-11-autonomous-judgment-eval-governance.md), [12](../../_bmad-output/implementation-artifacts/epic-12-adapter-scoring.md), [13](../../_bmad-output/implementation-artifacts/epic-13-marketing-vertical-ab.md).

**End state of this proposal:** decision-ready documentation, not a revised canonical sprint plan, implemented code, public feature, or claim of a released moat.
