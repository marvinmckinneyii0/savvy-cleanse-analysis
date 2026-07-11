# PRD ↔ Epic Reconciliation (SAINT)

<!-- Created 2026-07-09 roadmap restructure. Maps the 16-phase master PRD
     (_bmad-output/planning-artifacts/saint-master-prd.md) onto the operative epic
     structure. This table is the operative delivery ordering; the PRD's §6 Phase
     Overview and §11 Dependency Map are retained for historical phase-reference only
     (see their AMENDED banners). sprint-status.yaml is the sole status source of truth. -->

The master PRD (16 phases) is the single source of truth for *scope*. This document
maps its phases onto the operative *epic* structure and records the strategic
decisions that reorder them. Seven decisions drive the restructure:

- **A.** Data cleaning is the core product thesis. PRD Phase 9 self-healing pulls
  forward to **Epic 3**.
- **B.** Analytics maturity (descriptive → diagnostic → predictive → prescriptive)
  completes at an advanced level **before** any vertical adapter ships. Inverts the
  PRD's Phase-8-before-Phase-12 ordering.
- **C.** Autonomous agent judgment on ambiguous data ("Tier 4") is net-new,
  eval-gated, Enterprise-only. Does not exist in the PRD.
- **D.** Vertical order: marketing → financial → healthcare. Real estate is
  **descoped** from the Phase 8 slot, not cancelled.
- **E.** Governance advisory (jurisdiction-aware risk surfacing) is Enterprise.
  Baseline compliance remains unconditional and base-tier.
- **F.** A `project` entity is introduced — the missing parent for baselines,
  cleaning policy, rule sets, and run history.
- **G.** The product is renamed **SAINT** (Savvy Analytics Intelligence).
  Documentation only in this task; code rename is Story R.1.

## Reconciliation table

| PRD Phase | Epic | Status |
|---|---|---|
| 1 Foundation | Epic 1 | done |
| 2 Automation | Epic 2 | closing |
| 9 Pipeline Orchestration + Self-Healing (PULLED FORWARD) | Epic 3 | new |
| 3 Interface | Epic 4 | renumbered from 3 |
| 4 Monetization | Epic 5 | renumbered from 4 |
| 5 Scale | Epic 6 | renumbered from 5 |
| 5 Scale (Admin Control Plane) | Epic 7 | renumbered from 6 |
| 6 Intelligence + 12-A Forecasting (MERGED) | Epic 8 | renumbered from 7, expanded |
| 7 Advanced Drift + 14 Root-Cause (PULLED IN) | Epic 9 | new |
| 14 Simulation (VISION → IMPLEMENTATION) | Epic 10 | new |
| none — net-new | Epic 11 | new (Tier 4 + Eval Harness + Governance) |
| 8 Adapter + Scoring + 12-B Calibration (MERGED) | Epic 12 | new |
| 8 / §17 Marketing Vertical + 14 A/B Intelligence | Epic 13 | new |
| 10 Financial Vertical | Epic 14 | deferred-pending-research |
| 11 Healthcare Vertical | Epic 15 | deferred-pending-research |
| none | Chart inference (option c) | backlog, post-Epic-8 |
| none | Unstructured / Extraction | backlog, blocked-on: eval-harness |
| 13 Marketplace | — | backlog, unscoped |
| 14 (remaining), 15, 16 | — | vision scope, unchanged |

> **Epic 2 status note.** As of 2026-07-09 Epic 2 is `done` (Story 2.5 merged); the
> "closing" label above reflects the table's authored state at restructure time.
> sprint-status.yaml is authoritative.

## Recorded constraints

### ORCHESTRATION CONSTRAINT
No n8n at any layer of SAINT, including internal-only admin surfaces. LangGraph or an
MIT-licensed equivalent throughout. Stricter than the license requires, deliberately —
internal-only components have a habit of becoming client-facing.

### PRODUCT BOUNDARY (FlowIQ vs SAINT)
Same input formats, orthogonal purposes. FlowIQ ingests documents to understand a
*workflow* (output: workflow map, bottlenecks, automation recommendations). SAINT
ingests documents to extract the *data inside them* (output: structured records into
DQA). No shared extraction component. Do not build one to serve both.

### VERTICAL ORDER
marketing → financial → healthcare. `real_estate_adapter.py` is REMOVED from §7.3's
Phase 8 file structure (superseded by §17). Real estate is DEFERRED, NOT CANCELLED —
it rejoins the vertical queue after Epic 15, alongside additional enterprise-driven
verticals. Adapter order thereafter is demand-driven. `BaseAdapter` (Epic 12) exists
precisely to make this cheap. §13 (Marketplace) already contemplates paid third-party
adapters with revenue share.

### PRE-VERTICAL GATE
Epics 3 (cleaning), 8 (descriptive/predictive/prescriptive), 9 (diagnostic), 10
(simulation) must all close before Epic 12 begins.

### VERTICALS 14–15 DEFERRED PENDING RESEARCH (decision 2026-07-11)
Financial (Epic 14) and Healthcare (Epic 15) are `deferred-pending-research`: no story
breakdown, no sizing, no loop_eligible values until real market research + client
validation in those sectors inform actual scope. This is a deliberate decision, not a
gap to revisit. It does NOT change sequencing before Epic 13 — Marketing (Epic 13) was
already first in the vertical queue regardless.

### A/B TESTING INTELLIGENCE (§14, vision scope)
Promoted to implementation WITHIN Epic 13, not before it. Statistical foundation from
Epic 8's 8.1. Requires Benjamini–Hochberg default correction, Bonferroni available,
sequential-testing/peeking correction, power analysis with minimum detectable effect,
explicit labeling of underpowered null results. All deterministic; scipy.stats and
statsmodels only. NOT a pre-vertical gate item. NOT in the tier table.
NOTE: general hypothesis testing (§14) remains vision scope while A/B intelligence
promotes. A/B is a bounded experimental design; general hypothesis testing is
open-ended. One does not imply the other.

### LATENCY / QUEUEING
Epic 6's Celery/Redis async layer is FIFO with per-tenant fairness. NO priority queuing
by tier. §3.2's "priority processing" is STRUCK. Priority queuing starves free tenants
as paid load grows, degrading the conversion funnel precisely when the business
succeeds. Gate on quota, not speed.

### NAME MISMATCH (TEMPORARY, DOCUMENTED)
Documentation says SAINT; code says `savvycortex`. This is deliberate and time-boxed.
Code rename is filed as Story R.1 (Task 8), executed after Story 2.5 merges and before
Story 3.1 begins. This is not drift — drift is when nobody writes it down.
Retired names: SavvyCortex (retired by this restructure) and the earlier retired name
must not reappear in any documentation surface. Component filenames `dqa_engine.py` and
`drift_engine.py` keep their current names permanently — the previously-held "cosmetic
rename" of those components is VOID.

## Backlog (spec only — not story-filed)

- **Chart inference (option c).** Auto-selection of chart type by data shape and
  analysis type (time series → line; categorical comparison → bar; distribution with
  flagged outliers → annotated histogram; drift → before/after overlay). Blocked on
  Epic 8 — consumes `analysis_class` (see schema-extensions-spec.md).
- **Unstructured data / extraction.** Blocked on the eval harness (Epic 11). Interface
  spec only at `backend/core/extraction_client.py` (provider-agnostic, per-field
  confidence scores). Introduces the seventh DQA category `extraction_fidelity`.
- **Real estate vertical adapter.** Deferred, not cancelled. Rejoins the vertical queue
  after Epic 15. Demand-driven.
- **Marketplace (PRD Phase 13).** Unscoped.

## Unattended development loop (see loop-runner-spec.md)

A bounded, human-checkpointed development loop exists for low-judgment story work
(`loop-runner-spec.md`). Each `sprint-status.yaml` story carries a human-set
`loop_eligible` flag; the loop only ever picks up `ready-for-dev`, `loop_eligible: true`
stories whose dependencies are `done`, implements one, and opens a PR for manual review —
it never merges. As of this restructure, eligible stories are **sparse and
dependency-gated**: almost all `loop_eligible: true` stories sit behind Epic 3/4
foundational work landing first, so the loop has little to pick up until those close.
That is by design — capability ladders through Professional, risk gates at Enterprise,
and the loop is deliberately starved rather than fed by loosening eligibility.
