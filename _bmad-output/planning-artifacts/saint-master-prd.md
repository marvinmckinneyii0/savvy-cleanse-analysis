<!-- CANONICAL SOURCE OF TRUTH (2026-07-10). Sharded to markdown from
     savvycortex-master-prd (2).docx and amended per the 2026-07-09 roadmap
     restructure. The original .docx is retained read-only at
     _bmad-output/planning-artifacts/saint-master-prd-original.docx as a
     historical snapshot. This markdown is authoritative going forward.
     Eight amendments applied (Task 3): 1 §10 Non-Goals · 2 §2.1 Determinism ·
     3 Phase ordering (§6/§7.3/§11/Phase-12 split) · 4 §14.3 Governance Advisory ·
     5 Phases 14–16 scope promotion (most consequential) · 6 §8 ML constraint ·
     7 §3.2 monetization tiers · 8 product rename → SAINT (docs only). -->


SAINT
Savvy Analytics Intelligence
Unified Master PRD
From Data Cleaning Tool to Cognitive Operating System

> **RENAMED (Amendment 8, documentation scope only).** The product is SAINT
> (Savvy Analytics Intelligence). SAINT is retired (the earlier retired
> name must not reappear either). This rename is DOCUMENTATION ONLY — the
> `savvycortex/` package directory, `from savvycortex.*` imports, the
> `backend.api.app:app` entrypoint, and the `savvy-cleanse-analysis` repo are
> NOT renamed here (that is Story R.1). Component filenames `dqa_engine.py` and
> `drift_engine.py` keep their current names permanently.

16 Phases  |  Two-Week Sprints  |  Agile Delivery
Implementation Spec (Phases 1–13)  +  Vision Roadmap (Phases 14–16)

Version 1.0  |  May 2026
Savvy Analytics  |  Lisbon, Portugal
INTERNAL — STRATEGIC PLANNING DOCUMENT

I. PRODUCT VISION
# 1. What SAINT Is
SAINT is an AI-powered data intelligence and operational decision platform. It transforms messy, fragmented, or underutilized data into structured intelligence, automated insights, monitoring systems, agentic workflows, and eventually autonomous operational decision support.
The platform evolves through three macro stages: Data Cleaning Tool → Intelligence Layer → Agentic Operating System. Each phase ships a usable increment. Complete one, then begin the next.
Core positioning: “Operational intelligence infrastructure for decision-making.”
## 1.1 The Problem
Most organizations have data but cannot reliably extract decisions from it. Data exists in spreadsheets, databases, and reports but is not actionable. Manual reporting is slow. No proactive alerts exist. Analysts spend 80% of their time cleaning data and 20% analyzing it. The ratio should be inverted.
## 1.2 The Solution Arc
Ingest and structure data (ETL foundation)
Assess data quality and detect drift (DQA + Drift Engine)
Analyze data and generate insights (Insight Engine + LLM narrative)
Automate reporting and monitoring (Agents)
Package into a sellable web platform with billing (UI + Stripe)
Specialize by industry vertical (Adapters + Scoring)
Orchestrate intelligent operational agents (Agentic Workflows)
Evolve into a self-optimizing cognitive platform (Long-term vision)

# 2. Design Philosophy
## 2.1 Core Principles
Clarity over complexity. Every output should be immediately understandable by a non-technical executive.
Actionable intelligence over dashboards. Dashboards display data. SAINT delivers decisions. Reports include recommendations, not just charts.
Modular architecture. Every component is independently deployable, testable, and replaceable. No monolith.
Human-in-the-loop by default. The system recommends. Humans decide. No autonomous execution without explicit opt-in.
Explainable outputs. Every insight includes the evidence trail. Every score shows its formula. Every alert cites the threshold that triggered it.
Detect, don’t fix. The DQA identifies issues. It never modifies source data. Remediation is a human decision (until self-healing pipelines are introduced in Phase 9).
Deterministic computation. All statistical computation is deterministic given the same input. The LLM narrative layer is the only non-deterministic component, and it receives computed data—it never generates numbers. Where an agent selects among remediation options (Epic 11, Tier 4), it selects among deterministically-computed candidates. It never generates values. The non-deterministic component is policy selection, not numeric invention.
Schema enforcement. Every engine output validates against its Pydantic model before leaving the function. No unstructured outputs.
## 2.2 UX Philosophy
SAINT should feel like a strategic analyst, operations monitor, and intelligence layer combined into one system.
Visual direction: Clean enterprise UI. Apple-meets-DARPA aesthetic. Minimal, tactical, information-dense. Executive-grade outputs.
Dark/light modes: Both supported. Default to dark for analyst workflows, light for executive-facing reports.
Information density: Prioritize density over whitespace. Analysts need data, not decoration. But density must be organized—grid-based layouts, consistent typography hierarchy, color-coded severity indicators.
Report aesthetics: Generated reports (docx/pdf) are branded, professionally formatted, and client-presentable without manual cleanup.

# 3. Target Markets
## 3.1 Primary
SMEs: Operations teams with data but no analytics infrastructure. First adopters. Price-sensitive but high-volume.
Banking and financial services: Portfolio analysis, risk assessment, regulatory reporting. Compliance-sensitive. High willingness to pay.
Healthcare organizations: Patient flow optimization, readmission analysis, resource utilization. Anonymization-critical.
Operations-heavy businesses: Supply chain, logistics, manufacturing. Need monitoring agents and anomaly detection.
## 3.2 Monetization Tiers

> **AMENDED (Amendment 7 — replaces the §3.2 table entirely).**
> Vertical adapters (Epics 12–15) are NOT in this table; when they ship they are
> Enterprise or a vertical-specific SKU (§13 Marketplace already contemplates
> paid adapters with revenue share). Do not retrofit them into Professional.

|  | Free | Starter $49 | Pro $149 | Enterprise |
| --- | --- | --- | --- | --- |
| Reports/month | 3 | 25 | 100 | unlimited |
| Projects | 5 | 15 | 50 | unlimited |
| Storage | 50 MB | 500 MB | 2 GB | custom |
| Max file size | 10 MB | 100 MB | 500 MB | custom |
| Cleaning Tier 1 | ✓ | ✓ | ✓ | ✓ |
| Cleaning Tier 2 | ✗ | ✓ | ✓ | ✓ |
| Cleaning Tier 4 | ✗ | ✗ | ✗ | ✓ |
| Descriptive | ✓ | ✓ | ✓ | ✓ |
| Diagnostic — basic (Epic 2) | ✓ | ✓ | ✓ | ✓ |
| Diagnostic — advanced (Epic 9) | ✗ | ✗ | ✓ | ✓ |
| Predictive (Epic 8) | ✗ | ✗ | ✓ | ✓ |
| Prescriptive (Epic 10) | ✗ | ✗ | ✓ | ✓ |
| Visualizations | descriptive + before/after | + drift | + advanced | + decision-trace |
| CSV export | ✓ | ✓ | ✓ | ✓ |
| Cleaned-data export | ✗ | ✓ | ✓ | ✓ |
| Jupyter export | ✗ | ✗ | ✓ | ✓ |
| Monitoring rules | 1 | 5 | unlimited | unlimited |
| API access | ✗ | ✗ | ✗ | ✓ |
| Governance advisory | ✗ | ✗ | ✗ | ✓ |
| Multi-user | ✗ | ✗ | ✗ | ✓ |
| Watermark | yes | no | no | no |

Annual discount 20% (Starter $39, Professional $119). 14-day trial on Starter and
Professional. Free requires no credit card, no expiry.

**Ladder shape.** Free proves cleaning works. Starter makes cleaning useful.
Professional adds the analytics maturity stack. Enterprise adds autonomy, API,
governance, scale. CAPABILITY ladders through Professional; RISK gates at Enterprise.

**Tier 2 cleaning and cleaned-data export move together, both at Starter.**
Exporting a cleaned working copy requires RETAINING that copy; §14.1 Phase 1
requires input files not be persisted after pipeline completion unless explicitly
opted in. Cleaned-data export therefore carries a retention obligation, storage
accounting, and DSAR/erasure coverage (§14.1 Phase 5, Epic 6). Granting Tier 2
cleaning without export means a client can clean data they cannot retrieve —
incoherent. They ship together or not at all.

**Tier 4 on Enterprise only is a liability decision, not a pricing one.** It
requires a contract, a DPA, and a named human who accepted the per-finding-type
consequence disclosure. It does not belong behind a self-serve card form.

The frontend's $29 "Pro" tier is INCORRECT and must be corrected to match this table.

# 4. Operating Model
## 4.1 Sprint Cadence
Each phase maps to a single two-week sprint. The structure is consistent across all phases.
Days 1–2: Architecture and scaffolding. Schemas, interfaces, module structure.
Days 3–8: Core implementation. Build the primary deliverables.
Days 9–10: Integration and testing. Wire components, run against sample data.
Days 11–12: Hardening. Edge cases, error handling, logging.
Days 13–14: Demo preparation and Definition of Done validation. Sprint extends if DoD fails.
## 4.2 Phase Gating
Every phase has a binary Definition of Done checklist. A phase is complete only when every item passes. Scope is fixed per phase; time is the variable.
## 4.3 Tooling
Bolt.new: Initial MVP scaffold and frontend generation.
Claude Code: Primary implementation tool for backend modules, engine logic, and integration.
Claude.ai: Planning, document generation, architecture decisions, PRD maintenance.
BMad Method: Structured development framework for epics, stories, and agent workflows.
GitHub: Version control. Branch-per-story workflow. Commit after each story completion.

# 5. Technology Stack
## 5.1 Backend
Language: Python 3.11+
Framework: FastAPI (API-first design)
Data processing: Pandas (primary), Polars (performance-critical paths)
Statistics: NumPy, SciPy (Phase 7+). No scikit-learn until Phase 12.
LLM integration: Anthropic Claude API for narrative generation. Structured JSON grounding.
Task queue: Celery + Redis (Phase 5+). APScheduler for Phase 2.
Document generation: python-docx (Word), reportlab or weasyprint (PDF).
## 5.2 Frontend
Framework: React / Next.js
Styling: Tailwind CSS with custom design tokens for the Apple-meets-DARPA aesthetic.
Charts: Recharts or D3 for data visualization.
State management: React Query for server state, Zustand for client state.
## 5.3 Database
Primary: PostgreSQL with row-level security for tenant isolation (Phase 5+).
Baseline storage: File-based JSON (Phase 2), PostgreSQL JSON columns (Phase 5+).
File storage: Local filesystem (Phase 1–4), S3-compatible object storage (Phase 5+).
## 5.4 Infrastructure
Containerization: Docker (Phase 5+).
CI/CD: GitHub Actions → automated deployment pipeline.
Monitoring: Structured JSON logging. Sentry for error tracking.

II. IMPLEMENTATION ROADMAP
# 6. Phase Overview
> **AMENDED (Amendment 3).** The operative delivery ordering is now the epic
> structure in `_bmad-output/implementation-artifacts/prd-epic-reconciliation.md`,
> not this phase table. Key inversions: Phase 9 self-healing pulls forward to
> Epic 3 (cleaning is the core thesis); analytics maturity (Epics 8/9/10)
> completes BEFORE any vertical adapter (Epic 12+); Phase 12 is dissolved —
> 12-A forecasting merges into Epic 8, 12-B scoring calibration into Epic 12.
> The table below is retained verbatim for historical phase-reference only.

| # | Phase Name | Core Deliverable | Sprint | Depends On |
| --- | --- | --- | --- | --- |
| 1 | Foundation | DQA + Insight Engine + docx/pdf reports | Wk 1–2 | — |
| 2 | Automation | Drift Engine + Monitoring Agent + Reporting Agent + Alerts | Wk 3–4 | Phase 1 |
| 3 | Interface | Web UI + customer monitoring dashboard + alert config | Wk 5–6 | Phase 2 |
| 4 | Monetization | Stripe + tiered plans + usage tracking + trial | Wk 7–8 | Phase 3 |
| 5 | Scale | Multi-tenant + async + admin dashboard + security | Wk 9–10 | Phase 4 |
| 6 | Intelligence | Forecasting + NL querying + API + recommendation agent | Wk 11–12 | Phase 5 |
| 7 | Advanced Drift | KS test + multivariate drift + adaptive thresholds | Wk 13–14 | Phase 6 |
| 8 | Adapter + Scoring | Adapter layer + scoring engine + real estate vertical | Wk 15–16 | Phase 7 |
| 9 | Pipeline Orchestration | Configurable pipelines + batch + self-healing | Wk 17–18 | Phase 8 |
| 10 | Financial Vertical | Banking adapter + compliance scoring + regulatory templates | Wk 19–20 | Phase 9 |
| 11 | Healthcare Vertical | Healthcare adapter + anonymization + outcome scoring | Wk 21–22 | Phase 9 |
| 12 | Predictive Layer | ML-lite forecasting + scoring calibration + confidence intervals | Wk 23–24 | Ph 10/11 |
| 13 | Marketplace | Adapter SDK + marketplace + partner revenue share | Wk 25–26 | Phase 12 |
| 14 | Research Layer | Root-cause analysis + simulation + hypothesis testing | Wk 27–28 | Phase 12 |
| 15 | Agentic Workflows | Multi-agent orchestration + autonomous chains | Wk 29–30 | Phase 14 |
| 16 | Cognitive Platform | Self-optimization + swarm intelligence + org memory | Wk 31+ | Phase 15 |


# 7. System Architecture
## 7.1 Core Pipeline (Phases 1–2)
Input (CSV / DB table)
  │
  ├─ Data Quality Assessment (Phase 1)
  │    │ 6 detection categories, 4 severity levels
  │    ├─ CRITICAL → HALT → Diagnostic Report (docx/pdf)
  │    └─ PASS/WARNING → continue
  │
  ├─ Baseline Check (Phase 2)
  │    ├─ No baseline → Establish baseline → skip drift
  │    └─ Baseline exists → Drift Engine
  │         │ Mean/median/variance shift, volume drift
  │         │ Categorical PSI, schema drift
  │         └─ Drift Report JSON
  │
  ├─ Insight Engine (Phase 1, extended Phase 2)
  │    └─ Aggregations + trends + outliers + drift context
  │
  ├─ LLM Narrative Layer
  │    └─ Structured JSON → natural language narrative
  │
  ├─ Document Renderer → Report (docx/pdf)
  │
  ├─ Monitoring Agent → Rules → Alerts
  └─ Reporting Agent → Scheduled pipeline invocation
## 7.2 Extended Pipeline (Phases 7–12)
ETL → Structured Data
  → DQA (Phase 1, unchanged)
  → Adapter Transform (Phase 8, optional)
      │ Raw data → standardized feature set
  → Drift Engine (Phase 2 base + Phase 7 advanced)
  → Scoring Engine (Phase 8, optional)
      │ OS = (w1*LS + w2*DS - w3*SP + w4*FV + w5*SS) * (1 - dqa_penalty)
  → Insight Engine (extended with drift + scores)
  → Self-Healing (Phase 9, opt-in)
  → LLM Narrative → Document Renderer → Report
## 7.3 Full File Structure
savvycortex/
├── core/
│   ├── dqa_engine.py              # Phase 1
│   ├── insight_engine.py           # Phase 1 (extended Phase 2, 8)
│   ├── drift_engine.py             # Phase 2 (enhanced Phase 7)
│   ├── scoring_engine.py           # Phase 8
│   └── utils.py
├── adapters/
│   ├── base_adapter.py             # Phase 8
│   │   # real_estate_adapter.py — DEFERRED (Amendment 3): superseded by the
│   │   # marketing vertical (§17); rejoins the queue after Epic 15. Not cancelled.
│   ├── financial_adapter.py        # Phase 10
│   └── healthcare_adapter.py       # Phase 11
├── agents/
│   ├── reporting_agent.py          # Phase 2
│   ├── monitoring_agent.py         # Phase 2
│   └── recommendation_agent.py     # Phase 6
├── baselines/
│   └── baseline_store.py           # Phase 2 (file) → Phase 5 (PostgreSQL)
├── rules/
│   └── rule_engine.py              # Phase 2
├── schemas/
│   ├── dqa_schema.json             # Phase 1
│   ├── insight_schema.json         # Phase 1
│   ├── drift_schema.json           # Phase 2
│   ├── alert_schema.json           # Phase 2
│   └── scoring_schema.json         # Phase 8
├── verticals/                         # Phase 10+
├── api/
│   ├── main.py                     # Phase 3
│   └── routes/                     # Phase 3+
├── frontend/                          # Phase 3+
├── models/                            # Phase 3+
├── config/                            # Phase 2
└── tests/                             # All phases

PHASE 1
Foundation — DQA + Insight Engine + Report Generation
Sprint 1  |  Weeks 1–2
### Objective
Ship a working pipeline that ingests structured data, assesses quality, generates insights, and produces professional reports in docx or PDF. This is the core analytical engine.
### Deliverables
Data Quality Assessment (Stage 0): Automated scan across six detection categories: structural integrity, completeness, consistency, uniqueness, statistical red flags, referential integrity. Each finding classified by severity (Critical, High, Medium, Low). Critical findings halt the pipeline with a diagnostic report.
Insight Engine: Computation layer using pandas for aggregations (sum, avg, growth rate), time-based trend detection, segment comparisons, outlier flagging (IQR method). Produces structured JSON with five sections: data quality findings, summary, key insights, anomalies, recommendations.
LLM Narrative Layer: Receives structured JSON as grounding context. Generates natural-language narrative. Does not compute independently.
Document Renderer: Shared output module accepting insight JSON, producing docx or PDF with branded professional formatting.
### DQA Detection Categories
Structural integrity: file readability, header detection, row consistency, column count
Completeness: null/missing values per column, empty columns, row completeness, sparse regions
Consistency: mixed types, date format variance, encoding issues, whitespace, case inconsistency
Uniqueness: duplicate rows, near-duplicates, zero-variance columns, extreme cardinality
Statistical red flags: outliers (IQR), suspicious distributions, negative values in positive-expected fields, range anomalies
Referential integrity: orphaned foreign keys, orphaned categories, ID gaps (multi-table only)
### DQA Severity Schema
CRITICAL: Data unusable. Pipeline HALTS. Diagnostic report only. Triggers: empty dataset, >50% nulls in key metric, no parseable date column, <2 usable columns, 100% duplicates.
HIGH: Data usable but unreliable. Pipeline continues with warnings in report header.
MEDIUM: Issues may affect specific analyses. Documented in report. Analyst review suggested.
LOW: Minor/cosmetic. Logged for completeness.
### Pipeline Flow
ETL → Structured Data → DQA → Insight Engine (compute + LLM) → Document Renderer (docx/pdf) → Output. Halts at DQA if critical.
### Technical Approach
Data processing: Python, pandas, basic statistics. No ML.
Insight generation: Step 1: compute metrics (deterministic). Step 2: structure as JSON. Step 3: LLM narrative.
Document output: python-docx for Word, reportlab or weasyprint for PDF.
### Definition of Done
Ingest a dataset and receive a structured DQA JSON
Pipeline halts with diagnostics when critical issues detected
Generate full insight JSON (quality + summary + insights + anomalies + recommendations)
Produce professionally formatted report in both docx and PDF
Demo-ready output against a sample dataset
### Out of Scope
No scheduling, no alerts, no UI, no payment, no multi-tenancy. Engine only.

PHASE 2
Automation — Drift Engine + Monitoring + Reporting Agents
Sprint 2  |  Weeks 3–4
### Objective
Add drift detection and automated execution on top of Phase 1. The Drift Engine detects what changed. The Monitoring Agent decides if it matters. The Reporting Agent produces scheduled reports.
### Drift Engine (core/drift_engine.py)
Stateless computation module. Two DataFrames in, drift report JSON out. No side effects, no scheduling, no alerting.
### Detection Formulas
Mean shift: mean_shift_pct = (current_mean - baseline_mean) / baseline_mean. HIGH: >30%, MEDIUM: >15%, LOW: >5%.
Median shift: Same formula on medians. Skew-resistant complement to mean shift.
Variance shift: variance_ratio = current_std / baseline_std. HIGH: ratio >2.0 or <0.5. MEDIUM: >1.5 or <0.67.
Volume drift: volume_change_pct = (current_rows - baseline_rows) / baseline_rows. HIGH: >50%, MEDIUM: >20%, LOW: >10%.
Categorical PSI: psi_i = (current_pct - baseline_pct) * ln(current_pct / baseline_pct). Sum across categories. HIGH: PSI ≥ 0.25, MEDIUM: 0.10–0.25.
New/missing categories: Set difference between current and baseline. HIGH if missing category had >10% baseline representation.
Schema drift: Column additions, removals, type changes. Always HIGH.
### Baseline Store (baselines/baseline_store.py)
Manages persistent baseline snapshots. Stores statistical profiles (not raw data). File-based JSON in Phase 2, migrates to PostgreSQL in Phase 5. Auto-rotates after 4 consecutive clean runs.
### Monitoring Agent (agents/monitoring_agent.py)
Thin orchestrator. Invokes DQA and Drift Engine, evaluates outputs against user-configured rules via Rule Engine, fires alerts. Computes nothing itself. Scheduled via APScheduler.
### Rule Engine (rules/rule_engine.py)
Evaluates DQA and drift outputs against user-defined rules. Supported rule types: drift_severity, dqa_severity, mean_shift, volume_change, schema_change, completeness_drop. Each rule returns structured alert JSON.
### Reporting Agent (agents/reporting_agent.py)
Wraps full pipeline into single invocation. DQA → Drift → Insights → Render → Output. Reports now include Drift Analysis section when baseline exists. Manual trigger + scheduled (APScheduler). YAML config for schedules, thresholds, recipients.
### Alert Delivery
V1: log file output and email (SMTP). No Slack/SMS/webhook.
### Definition of Done
Establish baseline from sample dataset (first run behavior)
Detect mean shift, volume drift, categorical PSI, and schema drift
Monitoring Agent triggers alert when rule fires
Alert delivered via email
Reporting Agent produces report with Drift Analysis section
Modify thresholds via YAML config and confirm changed behavior
Baseline rotation after 4 consecutive clean runs
Schedule reporting agent and confirm cadence execution

PHASE 3
Interface — Web Application + Customer Dashboard
Sprint 3  |  Weeks 5–6
### Objective
Web interface for upload, configuration, report viewing, and alert management. Includes customer monitoring dashboard for tenant-scoped operational visibility.
### Deliverables
Data upload: Drag-and-drop CSV upload with pre-processing validation feedback.
Configuration UI: Form-based setup for key fields, report frequency, alert thresholds. Replaces YAML config.
Report viewer: In-browser report display with docx/pdf download. Report history with timestamps.
Customer monitoring dashboard: Pipeline health cards (last run, success rate, DQA score, active alerts). Run history table with DQA/drift severity. Drift history timeline with per-column drill-down. Alert timeline with acknowledge/resolve actions. Alert rule configuration UI. Usage meter showing consumption against plan limits.
Authentication: Email/password. Single-user initially, multi-user ready in schema.
### Technical Approach
Frontend: React/Next.js. Clean functional UI. Apple-meets-DARPA aesthetic.
Backend API: FastAPI wrapping existing engines. RESTful endpoints.
Database: PostgreSQL for user data, report metadata, alert history, configuration.
### Definition of Done
Upload CSV through browser and receive generated report
Configure analysis parameters through UI
View report in-browser and download as docx/PDF
Pipeline health overview visible after login
Drift history timeline renders with column drill-down
Alert timeline with acknowledge/resolve actions
Create, edit, and disable monitoring rules through UI
Usage meter shows consumption against plan limits

PHASE 4
Monetization — Stripe + Tiered Plans
Sprint 4  |  Weeks 7–8
### Objective
Make SAINT a paid product with subscription billing, tiered plans, and usage limits.
### Deliverables
Stripe integration: Checkout, billing portal, webhook handling (subscription created, payment failed, cancellation).
Plan tiers: Starter (limited reports, basic thresholds, email alerts). Professional (higher limits, custom thresholds, priority processing). Enterprise (unlimited, API access, custom branding).
Usage tracking: Report count, data volume, alert volume per billing period. Limits enforced at API layer.
Trial: 14-day free trial on Professional. No credit card required.
### Definition of Done
New user signs up, selects plan, completes Stripe payment
Usage limits enforced with clear feedback
Subscription lifecycle: create, upgrade, downgrade, cancel
Failed payments handled with grace period and notification
14-day trial functions without credit card

PHASE 5
Scale — Multi-Tenancy + Admin Dashboard + Production Hardening
Sprint 5  |  Weeks 9–10
### Objective
Production-grade infrastructure with tenant isolation, async processing, admin control plane, and security hardening.
### Multi-Tenant Infrastructure
Data isolation: Row-level security in PostgreSQL. Every query scoped to tenant_id. File storage partitioned by tenant.
Async processing: Celery + Redis task queue. Reports and monitoring jobs run asynchronously. Status polling for users.
Baseline migration: Baseline store moves from file-based JSON to PostgreSQL. Same interface, different backend.
### Admin Control Plane
Your operational command center. Cross-tenant visibility. Separate auth path.
Tenant management: List, create, suspend, reactivate, impersonate. Detail view with usage, billing, pipeline history, team members.
User management: Cross-tenant user list. Activity logs. Role changes. Password resets.
Token management: Issue, track, revoke API tokens. Scoped permissions (read:reports, write:pipeline, read:alerts, write:config). Prefix-based (svc_live_, svc_test_). Max 365-day expiry.
System health: Pipeline metrics, API metrics, storage, queue depth, DB health. Time-series charts with selectable windows.
Billing overview: MRR, active subscriptions by tier, trial conversions, churn rate, failed payments, at-risk tenants.
Customer journey: Six stages (Signup → Activation → Engaged → Expanded → At Risk → Churned). Funnel visualization, per-tenant timeline, cohort analysis.
Audit log: Immutable, append-only log of all admin actions. Actor, action, target, IP, timestamp. CSV export. 2-year retention minimum.
### Access Control (5-Role Hierarchy)
superadmin    → Full system. Creates admins. Impersonation.
  admin       → Scoped admin. Cannot create admins.
    owner     → Manages own tenant. Team, billing, config.
      member  → Read/execute within tenant.
        viewer → Read-only. Reports and dashboards.
### Security
Input sanitization on all upload paths
Rate limiting on API endpoints
HTTPS enforcement
Secrets management (no hardcoded keys)
OWASP top-10 review
Containerized deployment (Docker)
CI/CD pipeline with staging environment
### Definition of Done
Two tenants cannot access each other’s data
Report generation runs asynchronously with status polling
10 concurrent jobs without degradation
Admin can view, suspend, and impersonate tenants
Audit log records every admin action
Customer journey funnel renders correctly
Deployment automated via CI/CD
Security review completed against OWASP top-10

PHASE 6
Intelligence — Forecasting + NL Querying + Recommendation Agent
Sprint 6  |  Weeks 11–12
### Objective
Elevate analytical capability beyond descriptive statistics. Add forecasting, natural language data querying, and a standalone Recommendation Agent.
### Deliverables
Forecasting: Simple time-series projection (Prophet or statsmodels). Period-over-period with statistical significance testing.
NL querying: Users ask questions about their data in plain language. LLM translates to pandas operations. Results validated before presentation.
Recommendation Agent: Proactively identifies optimization opportunities beyond report recommendations. Scans datasets for high-performing segments, underutilized resources, and cost reduction opportunities. Runs alongside monitoring, outputs structured recommendation JSON.
Report customization: Section ordering, branding, metric selection. Saved configurations.
API access: Versioned REST API (v1). API key auth. Rate limiting per tier. Webhook endpoints for alert delivery.
### Definition of Done
30-day forecast generated from historical data
NL question returns accurate, evidence-backed answer
Recommendation Agent surfaces at least one actionable opportunity from sample data
Custom report template generates branded report
External system receives alert via webhook
API documentation published and functional

PHASE 7
Advanced Drift — Statistical Testing + Adaptive Thresholds
Sprint 7  |  Weeks 13–14
### Scope
Enhances Phase 2 Drift Engine with Kolmogorov-Smirnov test for numeric distributions, binned PSI for numeric columns, multivariate drift (correlation matrix comparison), baseline versioning with trend-of-drift analysis, and adaptive thresholds that adjust based on historical patterns.
### Definition of Done
KS test produces p-values for numeric drift significance
Multivariate drift detects relationship changes between stable columns
Baseline versioning with comparison across versions

PHASE 8
Adapter Layer + Scoring Engine — First Vertical (Real Estate)
Sprint 8  |  Weeks 15–16
### Scope
Introduces domain-specific data transformation and composite scoring. BaseAdapter abstract interface. Real estate adapter maps to 5 features (LS, DS, SP, FV, SS). Scoring engine: OS = (w1*LS + w2*DS - w3*SP + w4*FV + w5*SS) * (1 - dqa_penalty). DQA penalty bridges Phase 1 quality scores into scoring. Pipeline remains backward-compatible—no adapter configured means generic mode.
### Definition of Done
Real estate adapter transforms CSV into 5-feature standardized output
Scoring engine computes OS with correct formula and DQA penalty
Generic mode (no adapter) works with zero regressions

PHASE 9
Pipeline Orchestration — Configurable Composition + Self-Healing
Sprint 9  |  Weeks 17–18
### Scope
YAML-based pipeline configuration (select stages, parameters). Batch processing (multiple files, parallel via Celery). Pipeline validation before execution. Self-healing pipelines: automated rules-based remediation on a working copy (null imputation, deduplication, type coercion, whitespace normalization, date standardization). Healing is off by default, opt-in per pipeline. Every remediation logged in a healing manifest included in the report. Original data untouched.
### Definition of Done
Custom pipeline via YAML executes correctly
Batch of 5 CSVs processed with consolidated report
Self-healing fixes nulls and duplicates on working copy, logs all changes
Healing manifest appears in report

PHASE 10
Financial Vertical — Banking + Compliance-Aware Scoring
Sprint 10  |  Weeks 19–20
### Scope
Financial adapter (transaction data, portfolios, loan books → Risk Score, Return Metric, Compliance Flag, Concentration Index, Liquidity Ratio). Compliance-aware DQA extensions (PII detection, currency validation, suspicious pattern flagging). Regulatory report templates. Risk-adjusted scoring. Phases 10 and 11 can run in parallel.

PHASE 11
Healthcare Vertical — Outcome Scoring + Anonymization
Sprint 11  |  Weeks 21–22
### Scope
Healthcare adapter (patient flow, readmission, resource utilization → Outcome Score, Efficiency Index, Capacity Utilization, Readmission Risk, Cost Variance). Anonymization layer strips PHI before any processing. No PHI in any output. Outcome-based scoring weighted toward patient outcomes and efficiency.

PHASE 12
Predictive Layer — ML-Lite Forecasting + Calibration
> **AMENDED (Amendment 3).** Phase 12 no longer exists as a discrete unit.
> 12-A (forecasting, confidence intervals, auto model selection, accuracy
> scoring) merges into Epic 8. 12-B (scoring backtesting, weight optimization,
> adapter-specific predictions) merges into Epic 12 (Adapter + Scoring).
Sprint 12  |  Weeks 23–24
### Scope
Confidence intervals on forecasts (80%/95% bands). Forecast accuracy scoring. Auto model selection (Prophet vs ARIMA vs exponential smoothing). Scoring model backtesting and weight optimization. Adapter-specific predictions (real estate price trajectory, financial risk trends, healthcare readmission probability). All deterministic. No stochastic models.

PHASE 13
Marketplace — Adapter SDK + Partner Ecosystem
Sprint 13  |  Weeks 25–26
### Scope
Published Python SDK with BaseAdapter interface, testing harness, documentation. Adapter marketplace with versioning and installation. Sandboxed execution. Automated certification pipeline. Paid adapters with Stripe revenue share. SAINT becomes a platform.

III. VISION ROADMAP (Phases 14–16)
Phases 14–16 are defined at vision scope, not implementation spec — with one amendment (Amendment 5, the most consequential of this restructure). THREE of §14's six capabilities PROMOTE to implementation scope: simulation / what-if scenario modeling (Epic 10), root-cause analysis (Epic 9), and A/B testing intelligence (Epic 13, within the marketing vertical). THREE remain vision scope: dataset interrogation, hypothesis testing, industry benchmarking. The remainder of Phases 14–16 will be specced in detail when the pre-vertical analytics gate (Epics 3, 8, 9, 10) nears completion.
PHASE 14
Research & Analysis Layer
Vision  |  Weeks 27–28
### Capabilities
Dataset interrogation: Multi-source correlation across uploaded datasets.
Root-cause analysis: Automated diagnostic chains that trace anomalies back to contributing factors.
Hypothesis testing: User defines hypothesis, system tests against data with statistical rigor.
Simulation: What-if scenario modeling. Change input parameters, see projected impact.
Industry benchmarking: Compare tenant metrics against anonymized aggregate benchmarks.
A/B testing intelligence: Ingest experiment data, compute significance, recommend decisions.

PHASE 15
Agentic Workflow System
Vision  |  Weeks 29–30
### Capabilities
Multi-agent orchestration: Agents collaborate on complex analytical tasks. Financial Analyst Agent + Risk Agent + Compliance Agent working in concert.
Task orchestration: Define multi-step analytical workflows. Each step can invoke different engines, adapters, or agents.
Autonomous research chains: Agent decomposes a research question into sub-queries, executes them, and synthesizes results.
Intelligent pipeline optimization: Agents that monitor pipeline performance and suggest configuration improvements.
Example agents: Financial Analyst Agent, Marketing Intelligence Agent, Operations Monitoring Agent, Data Quality Agent, Forecasting Agent.

PHASE 16
Cognitive Platform — Self-Optimizing Intelligence
Vision  |  Weeks 31+
### Capabilities
Self-healing pipelines (advanced): Beyond Phase 9 rule-based healing. Learns from historical remediation patterns.
Self-improving insight generation: Feedback loop from user engagement with insights. Insights that get acted on are weighted higher in future reports.
Adaptive workflows: Workflows that modify their own structure based on results.
Swarm intelligence: Multiple specialized agents coordinating without central orchestration.
Organizational memory: Persistent knowledge base across all analyses. “The last time revenue dropped like this, it was caused by...”
Predictive operational modeling: Not just forecasting metrics—forecasting which operational decisions to make.
Human-AI collaborative decision systems: Structured decision frameworks where the AI presents options with evidence and the human selects with full context.

IV. EXECUTION CONSTRAINTS
# 8. Global Execution Rules
Schema enforcement: Every engine output validates against Pydantic before leaving the function. No unstructured outputs.
Determinism: All computation is deterministic. LLM is the only non-deterministic component, receives computed data, never generates numbers.
Backward compatibility: No phase breaks previous phases. Generic mode always works. New stages are additive and skippable.
ML constraint (amended): No fitted models in SAINT's execution path whose outputs cannot be presented to a non-technical user as an inspectable formula or decomposable component structure.
PERMITTED: deterministic statistical methods (scipy.stats) from Epic 9. Inspectable time-series decompositions (statsmodels, Prophet — trend, seasonality, changepoints) from Epic 8.
PERMITTED, NARROW SCOPE: scikit-learn in Epic 11 (Tier 4 near-duplicate similarity detection, eval-gated) and internal diagnostic exploration only. NOT permitted for client-facing scores (Epic 12 scoring weights must print). NOT permitted in financial (Epic 14, GLBA adverse-action reason codes) or healthcare (Epic 15) verticals without an explicit explainability architecture.
EXCLUDED: ensemble methods, gradient boosting, neural approaches in any client-facing output path.
CODE GENERATION IS UNRESTRICTED. Emitting Python that references any library for downstream user execution does not constitute a dependency. Generated code is NEVER executed by SAINT — static validation only (ast.parse, import allowlist). No sklearn in pyproject.toml. No sklearn resolved by uv.
Note: this resolves an internal inconsistency. §8's original 'no fitted parameters, no training steps' was already violated by §5.1's Phase 6 Prophet specification. Prophet.fit() is a training step. The operative line is not fitted-vs-unfitted but 'can you show the client the math.'
Test coverage: Every engine function has tests validating schema compliance and logic correctness.
Commit cadence: One commit per story. Context reset between stories.
# 9. Risk Register

| Risk | Phase | Mitigation | Severity |
| --- | --- | --- | --- |
| Insights feel generic | 1 | Ground LLM in computed stats. Never let LLM generate numbers. | High |
| Agent overbuilding | 2 | Agents are thin wrappers. No orchestration frameworks until Phase 15. | Medium |
| UI scope creep | 3 | Functional UI only. No design system, animations, or mobile optimization. | High |
| Stripe complexity | 4 | Use Stripe Checkout + Customer Portal (hosted). Minimize custom billing UI. | Medium |
| Tenant data leaks | 5 | Row-level security at database level. Penetration testing. | Critical |
| NL query hallucination | 6 | LLM generates pandas ops, not answers. Results from actual data. | High |
| Self-healing masking issues | 9 | Healing is opt-in. Every change logged. Original data untouched. | Medium |


# 10. Global Non-Goals
Real-time streaming analytics or event processing
Autonomous execution of operational and business decisions (pricing, billing, contractual, or customer-facing actions). The system recommends; humans decide. Data remediation under explicit opt-in, within guardrails, is governed separately under the Cleaning Engine tier model (Epics 3 and 11).
Deep ML model training or custom model deployment by users
White-label reselling infrastructure
Mobile-native applications (responsive web only)
SOC 2 / HIPAA certification (security hardening in scope, formal certification not)
Multi-region deployment
Data warehousing / data lake (consumes structured data, not long-term storage)
# 11. Dependency Map
> **AMENDED (Amendment 3).** Superseded by the epic dependency ordering in
> prd-epic-reconciliation.md. Pre-vertical gate: Epics 3 (cleaning), 8
> (descriptive/predictive/prescriptive), 9 (diagnostic), 10 (simulation) all
> close before Epic 12 (adapters) begins. Retained below for reference.
Phase 1 (Foundation)
  └→ Phase 2 (Automation + Drift)
      └→ Phase 3 (Interface + Customer Dashboard)
          └→ Phase 4 (Monetization)
              └→ Phase 5 (Scale + Admin Dashboard)
                  └→ Phase 6 (Intelligence + Recommendation Agent)
                      └→ Phase 7 (Advanced Drift)
                          └→ Phase 8 (Adapter + Scoring)
                              └→ Phase 9 (Pipeline Orchestration + Self-Healing)
                                  ├→ Phase 10 (Financial)  ─┐
                                  └→ Phase 11 (Healthcare) ┤  [parallel]
                                                           │
                                  └→ Phase 12 (Predictive) ┘
                                      └→ Phase 13 (Marketplace)
                                          ├→ Phase 14 (Research)
                                          └→ Phase 15 (Agentic)
                                              └→ Phase 16 (Cognitive)

V. BOLT.NEW MASTER PROMPT
# 12. Bolt.new Scaffold Prompt
The following prompt generates the initial frontend and API scaffold for Phases 1–3. It is designed to be pasted directly into Bolt.new. It does not generate engine logic—that is built via Claude Code against the schemas defined in this PRD.

BUILD A PRODUCTION-GRADE WEB APPLICATION CALLED 'SAINT'

SAINT is an AI-powered operational intelligence platform.
It ingests structured data (CSV), assesses data quality, detects
data drift, generates insights, produces professional reports
(docx/pdf), and monitors datasets with configurable alerts.

=== TECH STACK ===
Frontend: React + Next.js 14 (App Router)
Styling: Tailwind CSS
UI Components: shadcn/ui
Charts: Recharts
State: React Query (server) + Zustand (client)
Auth: NextAuth.js with email/password credentials provider
Backend: FastAPI (Python 3.11+)
Database: PostgreSQL (via Prisma or SQLAlchemy)
File Upload: react-dropzone
HTTP Client: axios

=== DESIGN LANGUAGE ===
Apple-meets-DARPA aesthetic. Clean, minimal, information-dense.
Dark mode default for analyst views. Light mode for reports.
Color palette: Navy primary (#1B3A5C), Blue accent (#2E75B6),
dark backgrounds (#0F172A), surface (#1E293B), border (#334155).
Typography: Inter or system fonts. Monospace for data values.
Severity colors: Critical=#C0392B, High=#E67E22, Medium=#F1C40F,
Low=#27AE60, Info=#3498DB.
Grid-based layouts. Consistent spacing (4px base). Status badges
with severity-coded colors. Metric cards with sparkline trends.

=== PAGES TO BUILD ===

1. LOGIN PAGE (/login)
   - Email/password form
   - Clean centered card layout
   - SAINT logo + tagline

2. DASHBOARD (/dashboard)
   - 4 metric cards: Last Run (status + timestamp),
     Success Rate (30d % with sparkline),
     Data Quality Score (color-coded), Active Alerts (count + badge)
   - Pipeline Run History table:
     Columns: timestamp, dataset name, status (success/failed/halted),
     DQA severity badge, drift severity badge, duration, report link
   - Filters: date range, status, dataset
   - Click row to expand run detail

3. UPLOAD & ANALYZE (/analyze)
   - Drag-and-drop CSV upload zone (react-dropzone)
   - Pre-upload file validation (size, type, encoding)
   - Configuration form:
     - Date column selector (dropdown from detected columns)
     - Metric columns (multi-select from numeric columns)
     - Category columns (multi-select from string columns)
     - Output format toggle: DOCX | PDF
   - 'Analyze' button triggers pipeline via POST /api/analyze
   - Processing state: progress indicator with stage names
     (DQA -> Drift -> Insights -> Rendering)
   - Results: inline report preview + download button

4. DRIFT HISTORY (/drift)
   - Dataset selector dropdown
   - Timeline visualization: color-coded severity per run
     (green=none, yellow=medium, red=high)
   - Click run to see per-column drift table:
     column, mean_shift_pct, variance_ratio, severity badge
   - Trend charts: column mean over time, row count over time
   - Baseline info card: timestamp, clean run count, rotate button

5. ALERTS (/alerts)
   - Alert timeline: timestamp, rule type icon, severity badge,
     title, status (active/acknowledged/resolved)
   - Filters: severity, rule type, status, date range
   - Click alert for detail panel: evidence data, link to
     triggering run, previous alerts of same type
   - Action buttons: Acknowledge, Resolve

6. ALERT RULES (/alerts/rules)
   - Active rules table: type, parameters, enabled/disabled,
     last triggered date
   - Add rule modal: type dropdown (drift_severity, mean_shift,
     volume_change, schema_change, completeness_drop, dqa_severity),
     parameter fields (column selector, threshold input),
     delivery channel checkboxes (email, log)
   - Edit/disable/delete per rule
   - Test rule button (runs against latest output)

7. REPORTS (/reports)
   - Report history table: timestamp, dataset, format, size,
     download link
   - Click to preview report content inline
   - Re-generate button (re-run pipeline for same dataset)

8. USAGE (/usage)
   - Progress bars: reports generated / limit,
     data volume processed / limit
   - Plan details card: name, price, features
   - Billing cycle dates + days remaining
   - Upgrade CTA button when approaching limits

9. SETTINGS (/settings)
   - Profile: name, email, password change
   - Notification preferences: email alerts on/off
   - Default output format: DOCX | PDF
   - Theme toggle: dark / light

=== API ENDPOINTS TO STUB ===
(Return mock JSON data. Actual engine logic built separately.)

POST   /api/auth/login
POST   /api/auth/register
GET    /api/dashboard/health
GET    /api/dashboard/runs
GET    /api/dashboard/runs/{id}
POST   /api/analyze              (accepts file upload)
GET    /api/drift/{dataset_id}
GET    /api/drift/{dataset_id}/trend
POST   /api/drift/{dataset_id}/rotate
GET    /api/alerts
PATCH  /api/alerts/{id}/acknowledge
PATCH  /api/alerts/{id}/resolve
GET    /api/rules
POST   /api/rules
PATCH  /api/rules/{id}
DELETE /api/rules/{id}
GET    /api/reports
GET    /api/reports/{id}/download
GET    /api/usage

=== MOCK DATA ===
Generate realistic mock data for all endpoints. Include:
- 15+ pipeline runs with varied statuses and severities
- 8+ alerts across different rule types and severities
- 5+ monitoring rules (2 enabled, 3 disabled)
- 10+ reports with varied datasets and formats
- Usage data showing ~60% of limits consumed

=== CRITICAL REQUIREMENTS ===
- Dark mode by default. Toggle in settings.
- ALL severity indicators use consistent color coding.
- Tables must be sortable and filterable.
- Responsive layout but optimize for desktop (1440px+).
- Loading skeletons for all async data fetches.
- Error states for failed API calls.
- Empty states with helpful messaging.
- No placeholder Lorem Ipsum anywhere.
- Every button must do something or show a toast.
- Use TypeScript throughout.

=== DO NOT BUILD ===
- No admin dashboard (separate Phase 5 build)
- No Stripe integration (Phase 4)
- No actual data processing logic (built in Claude Code)
- No file storage system (mock file handling)
- No real authentication (mock auth with hardcoded user)

Prioritize: working navigation, realistic mock data, polished UI,
responsive tables, and the Apple-meets-DARPA visual identity.


VI. AI MODEL ALLOCATION
# 13. Model Selection Guide
SAINT development uses three Claude models, each matched to the cognitive demand of the task. The wrong model on the wrong task either wastes cost (Opus on config files) or produces errors that cascade (Sonnet on schema design).
## 13.1 Model Roles
Opus (~35% of work): Architecture, engine logic, schema design, security-critical code, cross-module integration, complex debugging, statistical algorithms, PRD writing. Use Opus when the task’s output constrains downstream work or when getting it wrong means rework across multiple files.
Sonnet (~55% of work): UI components, API routes, CRUD operations, test writing, agent wrappers, documentation, report templates, standard patterns. Use Sonnet when the architectural decisions are already made and the schema contracts are defined. This is the workhorse.
Haiku (~10% of work): Config files, mock data generation, boilerplate, simple edits, commit messages, directory scaffolds. Use Haiku for anything that doesn’t require reasoning.
## 13.2 Sprint Day Mapping
Days 1–2 (Architecture): Opus for schemas, interfaces, and module structure. Haiku for directory setup and config files.
Days 3–8 (Core Build): Opus for engine logic and algorithms. Sonnet for API endpoints, UI components, and agent wrappers.
Days 9–10 (Integration): Opus for cross-module wiring and debugging. Sonnet for integration tests.
Days 11–12 (Hardening): Opus for edge case handling and error recovery. Sonnet for logging and validation.
Days 13–14 (Demo): Haiku for sample data and seed scripts. Opus for final bug fixes.
## 13.3 Phase-Level Tilt
Phase 1 (Foundation): ~60% Opus — schema design and engine logic dominate.
Phase 2 (Automation): ~50% Opus — drift formulas and baseline architecture.
Phase 3 (Interface): ~70% Sonnet — UI-heavy. Opus for API architecture and DB schema only.
Phase 4 (Monetization): ~50/50 — Stripe webhooks need Opus; billing UI is Sonnet.
Phase 5 (Scale): ~55% Opus — security, RLS, tenant isolation, audit log.
Phase 6 (Intelligence): ~50% Opus — forecasting algorithms and NL query safety.
Phases 7–13: New engines and adapters tilt Opus; UI and templates tilt Sonnet.
bolt.new scaffold: 100% Sonnet — frontend generation from detailed prompt.
The companion document “SAINT Model Allocation Guide” contains the complete story-level breakdown with model recommendations and rationale for every epic across all 13 phases.

VII. GOVERNANCE, COMPLIANCE & DATA LAWS
# 14. Governance Layer
SAINT processes customer data across multiple jurisdictions. Compliance is not a feature—it is a constraint that shapes architecture, data handling, storage, and output generation from Phase 1 onward. This section defines the regulatory landscape, SAINT’s obligations, and the phased approach to compliance readiness.
## 14.1 When Compliance Gets Built
Compliance requirements are not deferred to a single phase. They are embedded incrementally as capabilities arrive.
Phase 1 (Foundation): DQA engine must never store or log raw PII in outputs. Reports redact or mask sensitive fields when detected. Data processing is ephemeral by default—input files are not persisted after pipeline completion unless explicitly opted in.
Phase 2 (Automation): Baseline profiles store statistical summaries, never raw data. Alert messages must not contain PII. Email delivery uses TLS.
Phase 3 (Interface): Privacy policy and terms of service links required at registration. Cookie consent banner for EU visitors. Data retention settings exposed in UI.
Phase 4 (Monetization): Stripe handles PCI compliance for payment data. SAINT never touches card numbers.
Phase 5 (Scale): Row-level security for tenant isolation. Audit log for all data access. Data export and deletion APIs for DSAR (Data Subject Access Requests). Right-to-erasure implementation. Data Processing Agreement (DPA) template for enterprise clients.
Phase 9 (Pipeline Orchestration): Self-healing operates on working copies only. Original data untouched. Healing manifest provides full audit trail of any data modification.
Phase 10 (Financial): PII detection in DQA. Compliance flags in scoring. Regulatory report templates aligned with financial oversight requirements.
Phase 11 (Healthcare): Anonymization layer strips PHI before any processing. HIPAA-aligned data handling (but no formal certification in scope).
## 14.2 Sustainability Score
SAINT will include a Sustainability Score as a future governance capability, tracking the environmental impact of data processing operations. This includes compute cost per pipeline run (measured in processing seconds and estimated carbon equivalent), data storage efficiency (redundancy ratio, compression effectiveness), and reporting on aggregated sustainability metrics per tenant. This is scoped as a governance add-on, not a core pipeline stage—it measures the platform’s own resource consumption, not the customer’s business sustainability.
Implementation target: Phase 9 (Pipeline Orchestration), as a configurable governance output alongside the healing manifest. No separate phase required.

## 14.3 Governance Advisory (Amendment 4 — new subsection)
Baseline compliance obligations (§14.1 phase requirements) are unconditional and
delivered at base tier. Governance advisory — jurisdiction-aware risk surfacing,
pre-flight configuration warnings, defensible decision records — is an Enterprise
capability, delivered in Epic 11 for core/EU scope and extended within Epics 14–15
for vertical-specific regimes.
Advisory surfaces risk characteristics against the §15 registry. It never certifies
compliance and never constitutes legal advice. All output must be framed as 'this
configuration has characteristics that commonly trigger X — consult counsel,' never
'you are compliant' or 'this is permitted.'

# 15. Data Compliance Law Registry
The following table catalogs every data protection and privacy regulation that SAINT must consider when processing data for customers in the listed jurisdictions. This is a reference for architectural decisions, not legal advice.
## 15.1 European Union

| Law | Status | SAINT Impact |
| --- | --- | --- |
| GDPR | Active since 2018. Core framework. | Consent management, data minimization, right to erasure, DPA for enterprise clients, data portability, 72-hour breach notification. Fines up to €20M or 4% global turnover. |
| EU AI Act | Full enforcement Aug 2026 | SAINT uses AI for narrative generation and NL querying. Must classify risk level of AI components. Transparency obligations: users must know when output is AI-generated. Activity logging required for high-risk AI systems. Up to 7% global turnover for violations. |
| EU Data Act | Effective Sep 2025 | Data portability rights extend beyond personal data to industrial/IoT data. Relevant if SAINT ingests connected-device data. Anti-vendor-lock-in provisions apply to SaaS platforms. |
| ePrivacy Directive | Active, reform pending | Cookie consent for web application. Email alert delivery must comply with e-marketing rules. Tracking pixels in reports require consent. |


## 15.2 United Kingdom

| Law | Status | SAINT Impact |
| --- | --- | --- |
| UK GDPR | Active. Post-Brexit fork. | Substantially mirrors EU GDPR. UK ICO enforcement. EU-UK adequacy renewed through 2031. Same obligations as EU GDPR for UK-based customers. |
| Data Use and Access Act (DUAA) | Royal assent Jun 2025 | Simplifies some compliance burdens. Greater flexibility for automated decision-making. Enhanced children’s data protections. Simplified cookie rules. New lawful bases for processing. |
| UK AI Regulation | Sector-specific approach | No single AI Act like EU. Regulated through existing sector regulators (FCA, ICO, Ofcom). Lighter-touch than EU AI Act but still requires transparency for AI-generated outputs. |


## 15.3 United States

| Law | Status | SAINT Impact |
| --- | --- | --- |
| No Federal Privacy Law | State patchwork | No single standard. Must comply with each state’s law where customers are located. 20+ state laws active by 2026. |
| CCPA/CPRA (California) | Active. Most stringent. | Right to know, delete, opt-out of sale. Data minimization. 45-day DSAR response. Automated decision-making disclosure. Applies if processing data of CA residents. |
| HIPAA | Active. Healthcare sector. | Applies when processing PHI for healthcare clients. Requires BAA (Business Associate Agreement). Minimum necessary standard. Breach notification within 60 days. SAINT’s Phase 11 anonymization layer addresses this but formal HIPAA certification is out of scope. |
| GLBA | Active. Financial sector. | Safeguards Rule for financial data. Relevant for Phase 10 financial vertical. Requires written security plan, risk assessments, vendor oversight. |
| SOC 2 | Voluntary standard | Not legally required but expected by enterprise clients. Trust Services Criteria: security, availability, processing integrity, confidentiality, privacy. Target for post-Phase 13 compliance maturity. |
| State Privacy Laws (20+ states) | Expanding. 3 new in 2026. | Generally require: privacy notices, opt-out rights, data protection assessments, vendor contracts. Thresholds vary by state. Must track via IAPP state tracker. |
| FTC Act (Section 5) | Active federal enforcement | Prohibits unfair/deceptive practices. FTC enforces even without specific privacy law. Data practices must match privacy policy disclosures. |
| DOJ Bulk Data Rule | Effective Apr 2025 | Restricts sharing sensitive personal data with designated countries of concern. Affects data hosting and processing location decisions. |


## 15.4 Latin America

| Law / Country | Status | SAINT Impact |
| --- | --- | --- |
| Brazil — LGPD | Active since 2020. GDPR-aligned. | Most comprehensive in region. 15-day DSAR response (tighter than GDPR’s 30 days). DPO required. ANPD enforcement active. EU adequacy decision pending—once finalized, simplifies EU-Brazil data flows. |
| Mexico — LFPDPPP | Active since 2010. INAI enforcement. | Consent-based. Privacy notice required before processing. INAI has imposed $16.7M+ in fines. Opt-out for general data, opt-in for sensitive. Separate law for public sector data. |
| Argentina — Law 25,326 | Active since 2000. Reform pending. | First LatAm data protection law. EU adequacy holder since 2003. Reform bill aligns with GDPR (genetic/biometric data, DPO, portability). Constitutional habeas data rights. |
| Colombia — Law 1581 | Active since 2012. Reform pending. | Habeas data constitutional right. SIC enforcement. Reform seeks GDPR alignment: right to be forgotten, DPO, automated decision restrictions. Adequacy list for cross-border transfers. |
| Chile — Law 21,719 | Enacted Dec 2024. Effective Dec 2026. | Major GDPR-aligned reform. Creates new Personal Data Protection Agency. Fines up to ~€1.5M, tripled for repeat offenses. Constitutional right to data protection. Anonymization/pseudonymization recommended. |
| Peru — Law 29733 | Active since 2011. | Consent-based. National Authority for Personal Data (ANPD). Cross-border transfer restrictions. Habeas data rights in constitution. |


## 15.5 Global / Cross-Cutting

| Framework | Scope | SAINT Impact |
| --- | --- | --- |
| EU-US Data Privacy Framework | Active since Jul 2023 | Enables US-EU personal data transfers without SCCs for certified organizations. SAINT should self-certify once processing EU customer data from US infrastructure. |
| Global CBPR Forum | Expanding 2025–2026 | Cross-Border Privacy Rules across 6 continents. Streamlines multi-jurisdiction compliance. Monitor for SAINT applicability as customer base grows. |
| ISO 27001 | Voluntary standard | Information security management system. Expected by enterprise clients. Demonstrates security posture. Target for post-Phase 13. |
| PCI DSS | Mandatory for payment data | Handled by Stripe. SAINT never processes card data directly. Stripe’s PCI compliance covers payment flow. |
| Children’s Data (COPPA, etc.) | Multiple jurisdictions | SAINT is a B2B analytics platform. Not directed at children. If customer data contains minors’ data, DQA should flag it and the anonymization layer should handle it. |


## 15.6 Compliance Implementation Checklist
Ordered by priority and mapped to phases where each capability must be delivered.
P1 — Data minimization: Process only what’s needed. Don’t persist input files after pipeline completion unless opted in.
P1 — PII detection: DQA flags columns that appear to contain PII (names, emails, SSNs, phone numbers). Report includes warning.
P3 — Privacy policy + ToS: Required at registration. Link to savvyanalytics.info legal pages.
P3 — Cookie consent: Banner for EU/UK visitors. Configurable consent preferences.
P5 — Data Subject Access Requests: API endpoint for export and deletion. Tenant owners can trigger for their own data.
P5 — Right to erasure: Delete all tenant data (reports, baselines, alerts, config) on request. Audit log entry retained.
P5 — Data Processing Agreement: Template DPA for enterprise clients. Available for download in admin portal.
P5 — Breach notification: Incident response process. 72-hour notification for GDPR, 60-day for HIPAA, 15-day for LGPD.
P10 — Financial compliance flags: PII detection, currency validation, suspicious pattern detection in DQA extensions.
P11 — PHI anonymization: Strip all protected health information before processing. Verify no PHI in any output.
Post-P13 — SOC 2 / ISO 27001: Formal certification. Not in current scope but architecture should not preclude it.

VIII. ANALYTICS MATURITY MODEL
# 16. Four Levels of Analytics
SAINT delivers value at four progressive levels of analytical maturity. Each level builds on the previous. Every phase in the roadmap maps to at least one level.
## 16.1 Descriptive Analytics — “What happened?”
Aggregations, summaries, and visualizations of historical data. This is the foundation—you cannot diagnose, predict, or prescribe without first describing accurately.
SAINT delivery: DQA findings, insight summaries, metric aggregations (sum, avg, growth rate), segment breakdowns, report generation.
Phase mapping: Phase 1 (Insight Engine), Phase 3 (Dashboard visualizations).
Example output: “Revenue was $4.2M last quarter, up 12% from Q3. Segment A contributed 58% of total.”
## 16.2 Diagnostic Analytics — “Why did it happen?”
Root-cause identification, anomaly investigation, and correlation analysis. Moves beyond observation to explanation.
SAINT delivery: Drift detection (what changed and by how much), anomaly flagging with context, DQA-to-insight correlation (bad data in drifting columns is more concerning), segment drill-downs.
Phase mapping: Phase 2 (Drift Engine), Phase 6 (Recommendation Agent), Phase 14 (Root-cause analysis).
Example output: “Revenue dropped 14.4% in Region B. This correlates with a 32% shift in price distribution detected by the drift monitor. Data completeness in Region B is 78% vs 96% in Region A.”
## 16.3 Predictive Analytics — “What will happen?”
Forecasting, trend projection, and probability estimation. Uses historical patterns to project future outcomes.
SAINT delivery: Time-series forecasting (Phase 6 basic, Phase 12 ML-lite), confidence intervals, scoring model calibration, adapter-specific predictions (price trajectories, risk trends, readmission probability).
Phase mapping: Phase 6 (basic forecasting), Phase 12 (ML-lite with confidence bands).
Example output: “Revenue is projected to reach $4.8M next quarter (80% confidence: $4.3M–$5.2M). Region B recovery depends on resolving the price distribution anomaly.”
## 16.4 Prescriptive Analytics — “What should we do?”
Actionable recommendations, optimization suggestions, and decision support. The system doesn’t just describe or predict—it advises.
SAINT delivery: Recommendation Agent (Phase 6), report recommendations section, lead scoring (Marketing vertical), simulation and scenario modeling (Phase 14), agentic decision support (Phase 15).
Phase mapping: Phase 6 (Recommendation Agent), Phase 8 (Scoring Engine), Phase 14 (Simulation), Phase 15 (Agentic Workflows).
Example output: “Recommendation: Reallocate 20% of Region B marketing spend to Region A, where ROI is 3.2x higher. If Region B’s price anomaly is resolved within 30 days, revert allocation. Estimated impact: +$380K revenue.”

IX. FIRST VERTICAL: MARKETING + CRM
# 17. Marketing as First Vertical
The first vertical adapter is marketing, not real estate. This decision is strategic: SAINT will be used internally by Savvy Analytics to research, outreach, and convert its own customers. We build the tool, then use the tool to sell the tool. This creates a proof loop—every customer demo shows real data from real outreach powered by SAINT.
## 17.1 Why Marketing First
Dogfooding: Savvy Analytics uses SAINT to analyze its own lead pipeline, score prospects, and generate outreach reports. Every bug and UX friction point surfaces before customers ever see it.
Proof of concept: When pitching to potential customers, the demo is real data from real campaigns. “This report was generated by the same system you’re evaluating.”
Revenue acceleration: The CRM and lead scoring capabilities directly support sales activity while the product is being built. Building and selling happen in parallel.
Transferable patterns: Marketing analytics (segmentation, scoring, campaign analysis, funnel tracking) translates directly to the patterns needed for financial and healthcare verticals later.
## 17.2 Marketing Adapter (Phase 8, replaces Real Estate)
The marketing adapter maps campaign and lead data into standardized features for scoring and insight generation.
### Required Input Columns
Lead/contact identifiers (company, name, email, source)
Engagement metrics (opens, clicks, replies, meetings, conversions)
Campaign metadata (campaign name, channel, date, spend)
Firmographic data (industry, company size, region, revenue range)
Pipeline stage (prospect, qualified, opportunity, customer, churned)
### Output Features (Standardized)
ES (Engagement Score): Composite of open rates, click rates, reply rates, and meeting conversion weighted by recency.
LS (Lead Score): Firmographic fit + engagement score + behavioral signals. Predictive of conversion likelihood.
CS (Campaign Score): ROI per campaign. Spend efficiency. Attribution weighting.
FV (Funnel Velocity): Speed of progression through pipeline stages. Days per stage, conversion rates per transition.
CR (Churn Risk): For existing customers. Usage decline signals, payment history, support ticket frequency.
### Scoring Formula
# Marketing Opportunity Score
MOS = (w1*ES + w2*LS + w3*CS + w4*FV - w5*CR) * (1 - dqa_penalty)

# Default weights
w1=0.20  # Engagement
w2=0.30  # Lead quality
w3=0.15  # Campaign efficiency
w4=0.20  # Funnel velocity
w5=0.15  # Churn risk (subtracted)
## 17.3 CRM / Lead Scoring for Outreach
SAINT’s marketing adapter powers an internal CRM workflow for Savvy Analytics customer acquisition.
### Pipeline
Research (web search, industry lists)
  → Import leads (CSV with firmographic + contact data)
  → DQA (validate data quality of lead list)
  → Marketing Adapter (compute ES, LS, CS, FV, CR)
  → Scoring Engine (compute MOS per lead)
  → Insight Engine (segment analysis, top opportunities)
  → Report (prioritized lead list with scores and recommendations)
  → Outreach (email campaigns tracked in SAINT)
  → Monitoring Agent (track engagement drift, conversion rates)
### Lead Scoring Tiers
Hot (MOS > 0.75): High engagement + strong firmographic fit. Immediate outreach. Personal email or call.
Warm (MOS 0.50–0.75): Good fit but lower engagement. Nurture sequence. Automated follow-up.
Cool (MOS 0.25–0.50): Partial fit. Add to newsletter. Monitor for engagement signals.
Cold (MOS < 0.25): Low fit or no engagement. Archive. Re-evaluate quarterly.
## 17.4 Analytics Maturity Applied to Marketing
Descriptive: “247 leads generated from LinkedIn campaign. 18% open rate. 3 meetings booked.”
Diagnostic: “Open rate dropped 12% vs previous campaign. Subject line change correlated with decline. Segment B had 2x higher engagement than Segment A.”
Predictive: “Based on current funnel velocity, expect 8 qualified opportunities by month-end (80% CI: 5–12). Segment B conversion rate trending toward 22%.”
Prescriptive: “Recommendation: Shift 30% of budget from LinkedIn to email nurture for Segment A (higher CAC but 4x lifetime value). Prioritize the 12 hot leads for personal outreach this week.”

This is the single source of truth for SAINT. It supersedes all previous spec documents. All architectural decisions, schemas, phase boundaries, model allocations, compliance requirements, and vertical definitions defined here are authoritative.