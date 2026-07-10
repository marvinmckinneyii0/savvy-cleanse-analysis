# Schema Extensions — Specification (SAINT)

<!-- Created 2026-07-09 roadmap restructure (Task 4a/4b). SPECIFICATION ONLY.
     No Epic 1 Pydantic model is edited in this task, and no standalone JSON schema
     file is invented. Each extension below is applied INSIDE its owning story's own
     implementation + review, not here. Both are additive and backward-compatible. -->

This document specifies two additive, backward-compatible schema extensions and the
`project` entity. **No model code is edited by the restructure task** — Epic 1 is done
and is not reopened. Each extension is applied within its owning story's review.

---

## 1. DQA finding — `remediation_class`

- **Target:** `backend/models/quality_report.py` (the `DataQualityDefect` Pydantic model).
- **Applied in:** Story 3.1 (Classification Layer), within that story's review.
- **Change (additive, backward-compatible):** add a `remediation_class` field:

  ```
  remediation_class: "agent_autonomous"
                   | "human_policy_agent_execution"
                   | "human_only"
  ```

  Optional/defaulted so existing Epic 1/2 findings validate unchanged.

### Four-tier ownership model (acceptance criteria for Story 3.1's classification layer)

**TIER 1 — Agent autonomous, unconditional** (`agent_autonomous`):
  - Consistency: mixed types, date format variance, encoding, whitespace, case
  - Uniqueness: exact duplicate rows
  - Structural integrity: column count / header misalignment (rule-based)

**TIER 2 — Human sets policy once, agent executes indefinitely** (`human_policy_agent_execution`):
  - Completeness: null imputation method per column type
    (mean/median/mode/forward-fill/leave-as-is)
  - Referential integrity: orphaned FK resolution rule
    (drop row / null the FK / lookup correction)
  Implementation note: the existing `rules/rule_engine.py` YAML-config pattern extended
  from alerting to cleaning. Not a new mechanism.

**TIER 3 — Human only, per instance** (`human_only`; agent detects and scores, never acts):
  - Uniqueness: near-duplicates (agent scores similarity, ranks candidates; human
    confirms merge/keep)
  - Statistical red flags: outliers, suspicious distributions (agent flags via IQR with
    evidence; human decides cap/remove/keep)
  - Structural integrity: unreadable file, ambiguous structure (pipeline halts)
  TIER 3 IS NOT A PURCHASABLE CAPABILITY. It is default behavior at every tier — what the
  system does when it will NOT act. Do not create a "Tier 3" row in any client-facing
  surface.

**TIER 4 — Agent autonomous judgment, OPT-IN, Enterprise only** (Epic 11):
  - Same findings as Tier 3, when the client explicitly enables per finding type.
  - Granular opt-in. Not a global switch. The `remediation_class` remains `human_only`;
    Tier 4 is the opt-in overlay that permits autonomous action on those findings.

### Seventh DQA category — `extraction_fidelity` (SPEC ONLY, do NOT implement)
For the backlogged extraction epic. Inherently probabilistic — per-field confidence
scores, not pass/fail. Reason: a bad PDF extraction produces structurally valid,
consistently typed, non-duplicated data that passes all six existing categories and is
wrong. Extraction error is the only failure mode in this system invisible to the system
consuming it.

---

## 2. Insight Engine visualizations — `analysis_class`

- **Target:** the Insight Engine payload model (`backend/models/insight_payload.py` /
  `insight_report.py`) — a `visualizations` section.
- **Applied in:** Story 3.7 (Report Visualizations), within that story's review.
- **Change (additive, backward-compatible):** add a `visualizations` section where every
  chart object MUST carry:

  ```
  analysis_class: "descriptive"
                | "diagnostic_basic"
                | "diagnostic_advanced"
                | "predictive"
                | "prescriptive"
                | "decision_trace"
  ```

  Optional/defaulted so existing Epic 1 insight payloads validate unchanged.

**CRITICAL:** Epic 5's gating middleware (Story 5.3) filters on `analysis_class`. It does
NOT maintain a parallel chart allowlist. Without this tag, Epic 5 hardcodes which chart
types belong to which tier — a list that drifts from the analytics ladder the moment
Epic 9 or 10 adds a chart. **Tag the chart with what produced it; gate on the tag.**

---

## 3. `project` entity (Task 4c)

- **Target:** new entity, introduced in **Epic 4 Story 4.1** (Database Schema & Auth
  Foundation), designed alongside `org_id`/`user_id` multi-tenancy.
- **Shape:**

  ```
  tenant
    └── project (name, created_at, schema_fingerprint)
          ├── cleaning_policy (Tier 2 imputation rules per column)
          ├── baseline (statistical profile, rotation state)
          ├── rule_set (monitoring rules)
          └── runs[] (dqa_result, drift_result, healing_manifest,
                      report artifact, decision_trace if Tier 4)
  ```

**Rationale:** the PRD has a latent entity it never named. Baselines, monitoring rules,
drift history, run history, alert history, and Tier 2 cleaning policy ALL scope to a
dataset with no entity behind it. Tier 2 policy in particular has nowhere to live without
this — "human sets policy once, agent executes indefinitely" requires durable storage,
and Epic 3's Story 3.4 currently has nowhere to write.

Design alongside multi-tenancy from the start: `tenant_id → project_id → run_id`.
Retrofitting after Epic 6 is expensive; doing it in 4.1 is nearly free.
