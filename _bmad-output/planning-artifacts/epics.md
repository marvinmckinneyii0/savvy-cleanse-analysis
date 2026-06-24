---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
  - '_bmad-output/planning-artifacts/research/technical-insights-agents-layer-research-2026-04-09.md'
  - 'external: savvycortex-dashboard-spec.docx'
---

# SavvyCortex - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for SavvyCortex, decomposing the requirements from the PRD, Architecture, and Dashboard Specification into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Automated data quality assessment scanning 6 detection categories (structural integrity, completeness, consistency, uniqueness, statistical red flags, referential integrity) with severity classification (Critical, High, Medium, Low)
FR2: Pipeline halt on critical findings with diagnostic report; non-critical findings included as dedicated report section
FR3: Insight Engine computing aggregations (sum, avg, growth rate), time-based trend detection, segment comparisons, outlier flagging — producing structured JSON with 5 sections (data quality findings, summary, key insights, anomalies, recommendations)
FR4: LLM Narrative Layer receiving structured JSON as grounding context and generating natural-language narrative (summarizes and contextualizes — does not compute)
FR5: Document Renderer producing professionally formatted docx or PDF with branded styling from a shared output module based on format parameter
FR6: Reporting Agent pulling latest data, invoking full pipeline (DQA → Insight Engine → Renderer), supporting manual trigger (CLI) and scheduled execution (daily, weekly, monthly configurable intervals)
FR7: Monitoring Agent comparing current-period metrics against previous period, evaluating against configurable thresholds (default ±15% week-over-week on primary metrics), emitting structured alert messages
FR8: Alert Delivery via log file output and email (SMTP) when monitoring thresholds are breached
FR9: Configuration Layer — YAML or JSON config file for defining data sources, report schedules, metric thresholds, and alert recipients
FR10: Threshold modification via config file with confirmed changed behavior at runtime
FR11: Drag-and-drop file upload (CSV) with file validation feedback before processing begins
FR12: Configuration UI — form-based setup for key fields (date column, metric columns, category columns), report frequency, and alert thresholds
FR13: Report Viewer — display generated reports in-browser with download option (docx/pdf), report history with timestamps
FR14: Alert Dashboard — view active alerts, alert history, current threshold configuration, acknowledge/dismiss alerts
FR15: Basic email/password authentication — single-user initially, multi-user readiness in schema
FR16: Stripe subscription checkout, billing portal, and webhook handling for payment events (subscription created, payment failed, cancellation)
FR17: Three plan tiers (Starter, Professional, Enterprise) scoped by usage limits — Starter: limited reports, basic thresholds, email alerts; Professional: higher limits, custom thresholds, priority processing; Enterprise: unlimited, API access, custom branding
FR18: Usage tracking — report generation count, data volume processed, alert volume per billing period — enforced at API layer
FR19: Billing UI — plan selection, upgrade/downgrade flow, invoice history, payment method management (via Stripe hosted portal where possible)
FR20: 14-day free trial on Professional tier, no credit card required for trial start
FR21: Multi-tenant data isolation — row-level security in PostgreSQL, every query scoped to authenticated tenant, file storage partitioned by tenant ID
FR22: Async processing — report generation and monitoring jobs via task queue (Celery + Redis), users receive status updates rather than synchronous responses
FR23: Observability — structured logging (JSON format), error tracking (Sentry or equivalent), basic metrics dashboard for system health (queue depth, job rates, response times)
FR24: Security hardening — input sanitization on all upload paths, rate limiting on API endpoints, HTTPS enforcement, secrets management (no hardcoded keys), OWASP top-10 review
FR25: Containerized deployment (Docker), CI/CD pipeline, staging environment mirroring production
FR26: System handles 10 concurrent report generation jobs without degradation
FR27: Advanced analytics — forecasting (Prophet or statsmodels for time-series projection), correlation detection across metrics, cohort analysis for segmented datasets, comparative analysis (period-over-period with statistical significance testing)
FR28: Custom agents — user-defined monitoring rules beyond threshold alerts, composite conditions (e.g., alert when metric A drops AND metric B rises), scheduled digest reports with custom section selection
FR29: Natural language querying — users ask questions about their data in plain language, system translates to analytical operations, returns structured answers with supporting evidence scoped to user's datasets
FR30: Client self-service — report template customization (section ordering, branding, metric selection), saved configurations for recurring analyses, export API for integration with client systems
FR31: RESTful API with authentication for programmatic access, webhook endpoints for alert delivery to external systems (Slack, Teams, custom)
FR32: API documentation published and functional
FR33: Customer pipeline health dashboard — overview cards (last run status/duration, success rate sparkline, DQ score color-coded, active alerts count), run history table with date/status/severity filters, run detail view with expandable DQA/drift/insight sections and report download
FR34: Drift history view — per-dataset drift timeline with severity coloring (green/yellow/red), column-level drill-down showing mean shift, variance ratio, and PSI values, baseline info with clean run count, manual baseline rotation trigger, trend charts (mean over time, volume over time, composite drift score)
FR35: Alert timeline — chronological alert list with severity/rule-type/status/date filters, acknowledge and resolve actions, alert detail showing evidence (specific finding that triggered it), context link to pipeline run, history of previous alerts of same type
FR36: Alert configuration UI — active rules table with CRUD operations, rule types (drift_severity, mean_shift, volume_change, schema_change, completeness_drop, dqa_severity), parameter configuration per rule, delivery channel selection, test rule against most recent pipeline output
FR37: Usage meter — report count vs plan limit with progress bar, data volume vs plan limit, API calls vs limit (Professional+), storage used, billing cycle dates with days remaining, current plan details with upgrade CTA
FR38: Tenant management — list view (name, owner, plan, status, signup date, last active, report count, storage, MRR) with filters/sort, detail view with team members/usage/pipeline history/billing, actions: suspend, reactivate, impersonate, delete, change plan, extend trial, issue credit, export data
FR39: Cross-tenant user management — user list (email, name, tenant, role, status, signup, last login, pipeline runs) with filters/search, detail view with activity log/permissions/API tokens, actions: suspend, reset password, change role, remove from tenant
FR40: API token management — scoped tokens with permissions (read:reports, write:pipeline, read:alerts, write:config), configurable expiry (default 90 days, max 365 days, no non-expiring), prefix format (svc_live_ production, svc_test_ sandbox), token hash storage (SHA-256, never plaintext), revocation and usage tracking
FR41: System health monitoring dashboard — pipeline metrics (total runs 24h/7d/30d, success/failure rate, avg duration, queue depth, longest job), API metrics (request count, error rate 4xx/5xx, avg/p95 response time, rate limit hits), storage metrics (total used, growth rate, largest tenants), task queue (active workers, queue depth, DLQ count, avg wait time, failure rate), database (connection pool utilization, slow queries), overview cards with status indicators and sparklines, time-selectable charts (1h/6h/24h/7d/30d)
FR42: Billing overview — MRR from active subscriptions, active subscription count by plan tier, trial conversion rate (started vs converted), churn rate and churned MRR, failed payment count and amount at risk, revenue per plan breakdown, at-risk tenant list (failed payments, approaching trial expiry, declining usage) sorted by MRR, quick actions (extend trial, apply discount, issue credit forwarded to Stripe)
FR43: Customer journey tracking — 6-stage lifecycle (Signup → Activation → Engaged → Expanded → At Risk → Churned) with defined entry/exit triggers, funnel visualization with click-through to tenant lists, per-tenant journey timeline accessible from tenant detail, cohort analysis grouping tenants by signup period tracking stage progression
FR44: Audit log — immutable append-only log of all admin actions (tenant CRUD, user role changes, token operations, plan changes, impersonation, config changes), entry format includes actor/action/target/details/IP/timestamp, 2-year minimum retention, view with chronological table/filters/full-text search, CSV export for compliance
FR45: Role hierarchy — 5 roles (superadmin → admin → tenant_owner → tenant_member → tenant_viewer) with permission matrix governing: tenant visibility, tenant CRUD, billing management, API token grants, data access, pipeline execution, alert configuration, report viewing, team management, system health, impersonation, admin management

### NonFunctional Requirements

NFR1: Report generation completes in under 60 seconds from any well-structured CSV
NFR2: System sustains 10 concurrent report generation jobs without degradation
NFR3: No hardcoded credentials anywhere in codebase; secrets managed via .env (dev) and Docker secrets (production)
NFR4: Input sanitization on all upload paths and user-facing inputs
NFR5: Rate limiting on all API endpoints
NFR6: HTTPS enforcement on all connections
NFR7: LLM grounding pattern — LLM summarizes and contextualizes but never computes numbers independently; all numbers in narrative must originate from computed statistics
NFR8: Natural language query results validated against actual data before presentation
NFR9: Pipeline halt-on-critical — critical data quality findings halt pipeline with diagnostic report before LLM call
NFR10: Dead letter queue for failed async jobs with structured error capture
NFR11: Structured logging (JSON format) with correlation IDs (pipeline_run_id) for request tracing across all stages
NFR12: Database connection pooling and automated backups
NFR13: Data isolation — two tenants cannot access each other's data under any circumstance, enforced at database level via RLS
NFR14: OWASP top-10 security review completed before production launch
NFR15: Automated reports run on schedule with zero manual intervention for at least 7 consecutive days
NFR16: Non-technical user can upload data and receive a report without reading documentation
NFR17: Containerized deployment via Docker with reproducible builds
NFR18: Global non-goals — no real-time streaming analytics, no autonomous decision execution, no ML model training by users, no white-label infrastructure, no mobile-native apps (responsive web only), no SOC 2/HIPAA certification, no multi-region deployment, no data warehousing
NFR19: Admin routes behind separate middleware stack — standard user tokens cannot access /admin/* endpoints regardless of role claim manipulation
NFR20: Impersonation sessions time-limited to maximum 1 hour, fully audit-logged with both admin identity and impersonated identity on every action
NFR21: IP allowlisting configurable for admin access (disabled by default, recommended for production)
NFR22: Superadmin account provisioned via CLI during deployment only — cannot be created through UI; subsequent superadmins require existing superadmin
NFR23: Audit log append-only — application database user has no DELETE or UPDATE permissions on audit_log table
NFR24: Customer state-modifying actions (rule creation, alert acknowledgment, baseline rotation) logged in tenant-scoped activity log visible to tenant owner and admins

### Additional Requirements

- Hybrid foundation: new architecture incorporating existing components — in-place evolution, not full rewrite
- Starter template: in-place evolution with test-first setup; new packages alongside legacy modules
- Phase 1 first commit (before production code): create backend/pipeline/, backend/models/, backend/agents/, backend/renderers/, backend/baselines/, backend/tests/; add pyproject.toml with pytest config; create tests/conftest.py with shared DataFrame fixtures; fix 6 Day-1 tech debt items (~1.5 hours)
- Legacy module labeling: existing flat modules (advanced_pipeline.py, comprehensive_analytics.py, nlp_processor.py, main.py, dashboard_api.py) receive STATUS header comment marking them as legacy reference implementations
- Pydantic v2 contracts at all pipeline stage boundaries — no raw dicts between stages
- Pipes-and-Filters pipeline pattern: independent processing stages connected by typed data contracts
- Dual error handling strategy: PipelineResult dataclass for expected business outcomes (data quality issues, halts); SavvyCleanseError exception hierarchy for unexpected failures (disk full, network down)
- LLM call pattern: Claude API Structured Outputs via client.messages.parse() with Pydantic models; retry with exponential backoff (1s, 2s, 4s, max 3 attempts); provider fallback chain (Claude → OpenAI → Gemini); circuit breaker after 3 consecutive failures across all providers
- structlog for all logging — never print(), never logging.basicConfig(); JSON structured format
- Pandera for DataFrame validation (data content: nulls, types, ranges); Pydantic v2 for JSON/pipeline contract validation
- Three-layer architectural separation: Presentation (api/, agents/, renderers/), Business Logic (pipeline/, services/, models/), Data Access (db/, baselines/); pipeline never imports from api or agents
- RFC 7807 Problem Details for all API error responses
- tenant_id columns added to all database tables from Phase 3 (nullable until Phase 5 RLS enforcement)
- Drift Engine: stateless computation module with 7 detection checks (mean shift, median shift, variance shift, volume drift, categorical PSI, new/missing categories, schema drift) integrated in Phase 2
- Baseline management: statistical profiles stored as JSON files (Phase 2) migrating to PostgreSQL table (Phase 5); auto-rotation after 4 consecutive clean runs
- Test pyramid: pytest (backend) + vitest (frontend); tests alongside production code; integration tests in tests/integration/; E2E tests in tests/e2e/
- Database: Supabase (unified single project) through Phase 4; standalone PostgreSQL in Phase 5; SQLAlchemy 2.0 with Alembic migrations from Phase 3
- Admin Control Plane and Customer Dashboard share one PostgreSQL backend, separated by RBAC and query scoping at application layer
- Customer dashboard endpoints under /dashboard/v1/ auto-scoped by tenant_id via middleware injection
- Admin endpoints under /admin/v1/ require superadmin or admin role; every call audit-logged

### UX Design Requirements

No UX Design specification document was provided. Dashboard UI patterns are defined in the Dashboard Specification (savvycortex-dashboard-spec.docx) and captured in functional requirements FR33–FR45.

### FR Coverage Map

FR1: Epic 1 — Data quality assessment (6 categories, severity classification)
FR2: Epic 1 — Pipeline halt on critical findings
FR3: Epic 1 — Insight Engine (aggregations, trends, outliers → JSON)
FR4: Epic 1 — LLM Narrative Layer (grounded natural-language generation)
FR5: Epic 1 — Document Renderer (docx/PDF with branded styling)
FR6: Epic 2 — Reporting Agent (CLI + scheduled pipeline invocation)
FR7: Epic 2 — Monitoring Agent (threshold comparison, ±15% default)
FR8: Epic 2 — Alert Delivery (log file + email/SMTP)
FR9: Epic 2 — Configuration Layer (YAML/JSON for sources, schedules, thresholds)
FR10: Epic 2 — Runtime threshold modification via config
FR11: Epic 3 — Drag-and-drop file upload (CSV) with validation
FR12: Epic 3 — Configuration UI (column mapping, frequency, thresholds)
FR13: Epic 3 — Report Viewer (in-browser + download + history)
FR14: Epic 3 — Alert Dashboard (active/history/acknowledge/dismiss)
FR15: Epic 3 — Email/password authentication
FR16: Epic 4 — Stripe checkout, billing portal, webhooks
FR17: Epic 4 — Three plan tiers (Starter/Professional/Enterprise)
FR18: Epic 4 — Usage tracking + limit enforcement at API layer
FR19: Epic 4 — Billing UI (plans, upgrade/downgrade, invoices)
FR20: Epic 4 — 14-day free trial (no credit card)
FR21: Epic 5 — Multi-tenant RLS + tenant-scoped queries + storage
FR22: Epic 5 — Async processing (Celery + Redis + status updates)
FR23: Epic 5 — Observability (structlog + Sentry + health metrics)
FR24: Epic 5 — Security hardening (sanitization, rate limiting, OWASP)
FR25: Epic 5 — Docker + CI/CD + staging environment
FR26: Epic 5 — 10 concurrent jobs without degradation
FR27: Epic 7 — Advanced analytics (forecasting, correlation, cohort, comparative)
FR28: Epic 7 — Custom agents (composite conditions, digest reports)
FR29: Epic 7 — Natural language querying
FR30: Epic 7 — Client self-service (template customization, saved configs, export)
FR31: Epic 7 — REST API + webhooks (Slack, Teams, custom)
FR32: Epic 7 — API documentation
FR33: Epic 3 — Customer pipeline health dashboard
FR34: Epic 3 — Drift history view (timeline, drill-down, trend charts)
FR35: Epic 3 — Alert timeline (chronological, evidence, acknowledge/resolve)
FR36: Epic 3 — Alert configuration UI (rule CRUD, test rule)
FR37: Epic 3 — Usage meter (consumption vs plan limits)
FR38: Epic 6 — Tenant management (list/detail, suspend/impersonate/delete)
FR39: Epic 6 — Cross-tenant user management
FR40: Epic 6 — API token management (scoped, expiry, revocation)
FR41: Epic 6 — System health monitoring dashboard
FR42: Epic 6 — Billing overview (MRR, churn, at-risk)
FR43: Epic 6 — Customer journey tracking (6-stage lifecycle)
FR44: Epic 6 — Audit log (immutable, append-only, 2-year retention)
FR45: Epic 6 — Role hierarchy (5 roles + permission matrix)

## Epic List

### Epic 1: Data Quality & Insight Reports (CLI)
A developer runs a CLI command against a CSV and receives a professionally formatted report with data quality assessment, computed insights, and LLM-generated narrative — the core analytical engine that every subsequent epic builds on.
**FRs covered:** FR1, FR2, FR3, FR4, FR5
**Phase:** 1 — Foundation
**Depends on:** None (standalone)

### Epic 2: Automated Reporting & Data Monitoring
Reports run on a schedule without manual intervention. The system detects when data metrics drift beyond thresholds and delivers alerts via email — turning a manual tool into an autonomous monitoring system.
**FRs covered:** FR6, FR7, FR8, FR9, FR10
**Phase:** 2 — Automation
**Depends on:** Epic 1

### Epic 3: Web Application & Customer Dashboard
Users interact through a browser — upload data, configure analysis parameters, view reports, monitor pipeline health and drift history, manage alert rules, and track usage. No CLI required.
**FRs covered:** FR11, FR12, FR13, FR14, FR15, FR33, FR34, FR35, FR36, FR37
**Phase:** 3 — Interface
**Depends on:** Epic 1, Epic 2

### Epic 4: Subscription Billing
Users subscribe to a tiered plan, manage billing through Stripe, and the system enforces usage limits per tier — making SavvyCortex a paid product.
**FRs covered:** FR16, FR17, FR18, FR19, FR20
**Phase:** 4 — Monetization
**Depends on:** Epic 3

### Epic 5: Multi-Tenant Scale & Production Hardening
Multiple organizations use the platform safely with complete data isolation, async processing handles load, and the system is containerized with CI/CD and observability — production-ready infrastructure.
**FRs covered:** FR21, FR22, FR23, FR24, FR25, FR26
**Phase:** 5 — Scale
**Depends on:** Epic 3, Epic 4

### Epic 6: Admin Control Plane
Platform operators manage tenants, users, API tokens, system health, billing metrics, customer journeys, and audit all administrative actions from a dedicated dashboard — the business operations center.
**FRs covered:** FR38, FR39, FR40, FR41, FR42, FR43, FR44, FR45
**Phase:** 5b — Admin
**Depends on:** Epic 5

### Epic 7: Advanced Analytics & Self-Service API
Users access forecasting, ask natural language questions about their data, create custom monitoring rules with composite conditions, customize report templates, and integrate via a versioned REST API with webhooks.
**FRs covered:** FR27, FR28, FR29, FR30, FR31, FR32
**Phase:** 6 — Intelligence
**Depends on:** Epic 3, Epic 5

---

## Epic 1: Data Quality & Insight Reports (CLI)

A developer runs a CLI command against a CSV and receives a professionally formatted report with data quality assessment, computed insights, and LLM-generated narrative — the core analytical engine that every subsequent epic builds on.

### Story 1.1: Project Scaffolding & Pipeline Foundation

As a developer,
I want the backend package structure, test infrastructure, error handling hierarchy, and structured logging in place with Day-1 tech debt fixed,
So that all subsequent pipeline stories build on a clean, tested, properly organized foundation.

**Acceptance Criteria:**

**Given** the existing repository with legacy flat modules
**When** the scaffolding story is complete
**Then** the following directories exist with __init__.py: backend/pipeline/, backend/models/, backend/agents/, backend/renderers/, backend/baselines/, backend/errors/, backend/tests/
**And** pyproject.toml exists with pytest configuration and project metadata
**And** backend/tests/conftest.py exists with shared DataFrame fixtures (clean dataset, dirty dataset with known defects)
**And** backend/errors/exceptions.py defines the SavvyCleanseError hierarchy (SavvyCleanseError, PipelineStageError, LLMProviderError, ReportRenderError, DriftComputationError, ConfigurationError)
**And** backend/models/pipeline_result.py defines PipelineResult dataclass (success, halted, halt_reason, quality_report, insight_report, drift_report)
**And** structlog is configured for JSON output with pipeline_run_id correlation
**And** the 6 Day-1 tech debt items identified in the Architecture document are fixed
**And** legacy modules (advanced_pipeline.py, comprehensive_analytics.py, nlp_processor.py, main.py, dashboard_api.py) have STATUS header comments marking them as legacy reference implementations
**And** `pytest backend/tests/` runs successfully with at least the conftest fixtures validated
**And** .env.example exists with placeholder values (no secrets committed)

### Story 1.2: Data Quality Assessment Engine

As a developer,
I want to scan a structured dataset across six detection categories and receive a severity-classified quality report that halts the pipeline on critical findings,
So that bad data is caught before expensive LLM calls and downstream analysis.

**Acceptance Criteria:**

**Given** a pandas DataFrame loaded from a CSV file
**When** DataQualityAssessor.assess_quality(df) is called
**Then** the assessment scans all six categories: structural integrity, completeness, consistency, uniqueness, statistical red flags, and referential integrity
**And** each finding is classified by severity (Critical, High, Medium, Low) as a DataQualityDefect Pydantic model
**And** the return type is a Pydantic-validated DataQualityReport containing all defects, an overall severity, and column-level summaries
**And** Pandera schema validation runs before assessment begins, raising ConfigurationError on invalid DataFrame structure

**Given** a dataset with critical data quality issues (e.g., >50% null values in key columns, completely duplicated rows, schema violations)
**When** the assessment detects critical-severity findings
**Then** PipelineResult is returned with halted=True and halt_reason describing the critical findings
**And** the pipeline does not proceed to the Insight Engine or LLM stages
**And** a structured log entry is emitted at level "warning" with event "pipeline_halted", stage "data_quality", and defect details

**Given** a dataset with only non-critical findings (High, Medium, Low)
**When** the assessment completes
**Then** PipelineResult is returned with halted=False and quality_report populated
**And** non-critical findings are preserved for inclusion in the final report

**Given** any assessment run
**When** the assessment completes or halts
**Then** structlog entries are emitted with pipeline_run_id, stage="data_quality", row count, and defect count
**And** backend/tests/test_data_quality.py passes with tests covering: clean data (no defects), each defect category, critical halt, non-critical pass-through, and Pandera validation failure

### Story 1.3: Insight Engine

As a developer,
I want to compute aggregations, time-based trends, segment comparisons, and outlier detection from a quality-assessed DataFrame, producing a structured JSON payload,
So that the LLM narrative layer has deterministic, computed statistics to ground its narrative on.

**Acceptance Criteria:**

**Given** a DataFrame that passed data quality assessment (non-halted PipelineResult) and its DataQualityReport
**When** InsightEngine.generate_insights(df, quality_report) is called
**Then** the engine computes: summary statistics (sum, avg, min, max, growth rate per numeric column), time-based trend detection (if a date column is identified), segment comparisons (if categorical columns exist), and outlier flagging (values beyond 2 standard deviations)
**And** the return type is a Pydantic-validated InsightPayload with five sections: data_quality_findings, summary, key_insights, anomalies, recommendations
**And** all numbers in the InsightPayload are deterministically computed from the DataFrame — no LLM involvement

**Given** a dataset with no date column
**When** insights are generated
**Then** time-based trend sections are populated with an empty list and a note indicating no temporal data was detected
**And** other insight sections are fully computed

**Given** a dataset with no categorical columns
**When** insights are generated
**Then** segment comparison sections are populated with an empty list
**And** other insight sections are fully computed

**Given** any insight generation run
**When** the computation completes
**Then** structlog entries are emitted with pipeline_run_id, stage="insight_engine", computed metrics count, and detected anomaly count
**And** backend/tests/test_insight_engine.py passes with tests covering: full dataset (date + categories + numerics), numeric-only dataset, dataset with outliers, and empty/minimal dataset edge case

### Story 1.4: LLM Narrative Generation

As a developer,
I want to transform the computed InsightPayload into a natural-language InsightReport using Claude Structured Outputs with retry and provider fallback,
So that users receive human-readable narrative grounded entirely in computed statistics.

**Acceptance Criteria:**

**Given** a valid InsightPayload from the Insight Engine
**When** NarrativeGenerator.generate(insight_payload) is called
**Then** the generator calls Claude API via client.messages.parse() with the InsightPayload as grounding context and InsightReport as the output Pydantic model
**And** the returned InsightReport contains narrative sections (executive summary, key findings, anomaly analysis, recommendations) that reference only numbers present in the InsightPayload
**And** the LLM does not independently compute, invent, or hallucinate any numerical values

**Given** the Claude API returns a timeout or 5xx error
**When** the retry logic activates
**Then** up to 3 attempts are made with exponential backoff (1s, 2s, 4s)
**And** if Claude fails after 3 attempts, the generator falls back to OpenAI, then Gemini
**And** each retry and fallback is logged via structlog with provider name, attempt number, and error type

**Given** all LLM providers fail (circuit breaker: 3 consecutive failures across all providers)
**When** the circuit breaker triggers
**Then** narrative generation is skipped gracefully
**And** PipelineResult is returned with success=True but insight_report containing a fallback message indicating narrative was unavailable
**And** the report can still be rendered with computed data only (no narrative sections)

**Given** a 4xx client error from any provider
**When** the error is received
**Then** the request is NOT retried (client errors are not transient)
**And** LLMProviderError is raised with the provider name and error details

**Given** any narrative generation run
**When** generation completes or fails
**Then** structlog entries include pipeline_run_id, stage="narrative_generator", provider used, token count, and duration
**And** backend/tests/test_narrative_generator.py passes with mocked API calls covering: successful generation, retry logic, fallback chain, circuit breaker, and 4xx non-retry

### Story 1.5: Document Rendering

As a developer,
I want to render an InsightReport into professionally formatted docx and PDF documents with branded styling,
So that users receive polished, shareable reports as the pipeline's final output.

**Acceptance Criteria:**

**Given** a valid InsightReport (with or without narrative sections)
**When** DocxRenderer.render(insight_report, output_path) is called
**Then** a .docx file is produced using docxtpl with the branded report template (backend/renderers/templates/report_template.docx)
**And** the report includes sections for: data quality findings, summary statistics, key insights, anomalies, and recommendations
**And** tables and charts are formatted with Savvy brand styling

**Given** a valid InsightReport
**When** PdfRenderer.render(insight_report, output_path) is called
**Then** a .pdf file is produced using WeasyPrint from the HTML template (backend/renderers/templates/report_template.html)
**And** the PDF output matches the same content and styling as the docx output

**Given** an InsightReport where narrative generation was skipped (circuit breaker fallback)
**When** the renderer is called
**Then** the report is rendered with computed data sections only
**And** narrative sections display a graceful placeholder (e.g., "Narrative summary unavailable for this run")

**Given** a rendering failure (disk full, template missing, invalid data)
**When** the renderer encounters an error
**Then** ReportRenderError is raised with descriptive detail
**And** the error is logged via structlog with pipeline_run_id and stage="renderer"

**Given** any rendering run
**When** rendering completes
**Then** backend/tests/test_renderers.py passes with tests covering: docx output validation, PDF output validation, fallback rendering without narrative, and error handling

### Story 1.6: Pipeline Orchestration & CLI Entry Point

As a developer,
I want to run a single CLI command that ingests a CSV, runs the full pipeline (DQA → Insights → Narrative → Render), and outputs a formatted report,
So that the end-to-end pipeline is usable and demo-ready from the terminal.

**Acceptance Criteria:**

**Given** a CSV file on disk
**When** the user runs `python -m backend.pipeline.orchestrator --input data.csv --output report.docx --format docx`
**Then** the orchestrator loads the CSV into a DataFrame, runs data quality assessment, generates insights, produces narrative, renders the document, and saves it to the specified output path
**And** the orchestrator returns a PipelineResult with success=True and all sub-reports populated
**And** the entire run completes in under 60 seconds for a well-structured CSV (NFR1)

**Given** the pipeline halts on critical data quality findings
**When** the orchestrator detects halted=True from the DQA stage
**Then** subsequent stages (insight, narrative, render) are skipped
**And** a diagnostic report is output (or logged) explaining the halt reason
**And** the CLI exits with a non-zero exit code

**Given** the user specifies --format pdf
**When** the pipeline completes successfully
**Then** a PDF report is produced instead of docx

**Given** any pipeline run
**When** the run starts
**Then** a unique pipeline_run_id (UUID) is generated and propagated to every stage via structlog context
**And** the CLI outputs a summary line: pipeline_run_id, status (success/halted/error), duration, and output file path

**Given** the CLI entry point
**When** Typer is used for argument parsing
**Then** `python -m backend.pipeline.orchestrator --help` displays usage with --input (required), --output (required), and --format (optional, default docx)
**And** backend/tests/e2e/test_cli_reporting.py passes with an integration test running the full pipeline against backend/tests/e2e/sample_data/clean_sales.csv

---

## Epic 2: Automated Reporting & Data Monitoring

Reports run on a schedule without manual intervention. The system detects when data metrics drift beyond thresholds and delivers alerts via email — turning a manual tool into an autonomous monitoring system.

### Story 2.1: Configuration Layer

As a developer,
I want a YAML/JSON configuration file that defines data sources, report schedules, metric thresholds, and alert recipients,
So that agents can be configured without code changes and settings can be modified at runtime.

**Acceptance Criteria:**

**Given** a project root directory
**When** the configuration layer is initialized
**Then** a config.yaml file at project root defines: data_sources (list of file paths or directories), report_schedule (cron expression or interval: daily/weekly/monthly), metric_thresholds (per-metric percentage change thresholds with ±15% default), alert_recipients (list of email addresses), and output settings (format, output directory)
**And** backend/pipeline/config.py defines a PipelineConfig Pydantic dataclass that validates and loads the YAML config
**And** invalid config values (missing required fields, invalid cron expressions, negative thresholds) raise ConfigurationError with descriptive messages

**Given** a valid config.yaml exists
**When** any agent or pipeline component calls PipelineConfig.load()
**Then** the configuration is loaded, validated, and returned as a typed PipelineConfig instance
**And** environment variable overrides are supported for secrets (SMTP credentials, API keys) via .env

**Given** a config.yaml is modified on disk
**When** an agent reloads configuration (next scheduled run or explicit reload)
**Then** the updated thresholds, schedules, and recipients take effect without restarting the process (FR10)

**Given** any configuration loading
**When** the config is parsed
**Then** structlog entries are emitted with event="config_loaded" and a summary of active settings (without secrets)
**And** backend/tests/test_config.py passes with tests covering: valid config, missing fields, invalid values, environment variable override, and reload behavior

### Story 2.2: Drift Engine

As a developer,
I want a stateless computation module that compares a current DataFrame against a baseline profile and detects distributional drift across 7 checks,
So that the Reporting Agent can include drift analysis in reports and the Monitoring Agent can trigger drift-based alerts.

**Acceptance Criteria:**

**Given** a current DataFrame and an existing BaselineProfile (Pydantic model with per-column mean, median, std, quartiles, null%, categorical distributions, schema fingerprint)
**When** DriftEngine.compute_drift(current_df, baseline_profile) is called
**Then** the engine runs 7 detection checks: mean shift, median shift, variance shift, volume drift, categorical PSI (Population Stability Index), new/missing categories, and schema drift
**And** each finding is classified by severity (HIGH, MEDIUM, LOW) using the thresholds defined in the Architecture document
**And** the return type is a Pydantic-validated DriftReport with sections: volume_drift, numeric_drift, categorical_drift, schema_drift, drift_summary, overall_severity, recommendations

**Given** a dataset being analyzed for the first time (no baseline exists)
**When** the Drift Engine is invoked
**Then** a BaselineProfile is computed from the current DataFrame and saved as a JSON file in backend/baselines/
**And** drift computation is skipped (no comparison possible) and the pipeline continues without a DriftReport
**And** a structlog entry is emitted with event="baseline_created"

**Given** 4 consecutive pipeline runs with no HIGH-severity drift findings
**When** the 4th clean run completes
**Then** the current DataFrame's profile automatically replaces the existing baseline (auto-rotation)
**And** the consecutive_clean_runs counter resets to 0
**And** a structlog entry is emitted with event="baseline_rotated"

**Given** a HIGH-severity drift finding in any run
**When** the finding is detected
**Then** the consecutive_clean_runs counter resets to 0
**And** the existing baseline is retained

**Given** any drift computation
**When** the computation completes
**Then** the DriftReport is Pydantic-validated before return
**And** the Drift Engine has no side effects beyond baseline file I/O — it does not send alerts, halt the pipeline, or run on a schedule
**And** structlog entries include pipeline_run_id, stage="drift_engine", columns checked, and findings count
**And** backend/tests/test_drift_engine.py passes with tests covering: each of the 7 checks in isolation, first-run baseline creation, baseline auto-rotation after 4 clean runs, rotation counter reset on HIGH finding, and schema drift detection

### Story 2.3: Reporting Agent

As a developer,
I want a CLI agent that pulls the latest data, invokes the full pipeline (DQA → Drift Engine → Insight Engine → Narrative → Render), and can run on a schedule,
So that reports are generated automatically without manual intervention.

**Acceptance Criteria:**

**Given** a configured data source in config.yaml and an output directory
**When** the user runs `python -m backend.agents.reporting_agent generate --input data.csv --format docx`
**Then** the Reporting Agent loads config, invokes the pipeline orchestrator with the specified input, and saves the rendered report to the configured output directory
**And** if a baseline profile exists for this dataset, the Drift Engine is included in the pipeline and the report contains a Drift Analysis section
**And** if no baseline exists, the pipeline runs without drift analysis and creates the initial baseline

**Given** the reporting agent is configured with a schedule (e.g., schedule: weekly)
**When** the user runs `python -m backend.agents.reporting_agent schedule`
**Then** APScheduler starts and triggers pipeline execution at the configured interval
**And** the agent continues running in the foreground, executing on cadence
**And** each scheduled run uses the latest config.yaml values (hot-reload)

**Given** a scheduled reporting agent running for 7+ consecutive days
**When** each scheduled run executes
**Then** reports are generated with zero manual intervention (NFR15)
**And** each run is logged with pipeline_run_id, timestamp, status, and output file path

**Given** a pipeline failure during a scheduled run (e.g., file not found, LLM failure)
**When** the error occurs
**Then** the agent logs the error with full context and continues to the next scheduled run
**And** the agent does not crash or stop scheduling

**Given** any agent invocation
**When** the agent runs
**Then** backend/tests/test_reporting_agent.py passes with tests covering: manual generate, scheduled execution (mocked timer), drift-included pipeline, and error recovery

### Story 2.4: Monitoring Agent & Alert Delivery

As a developer,
I want a CLI agent that compares current metrics against previous period, evaluates configurable thresholds, and delivers structured alerts via log file and email,
So that anomalies are detected proactively and stakeholders are notified automatically.

**Acceptance Criteria:**

**Given** a current dataset and a previous-period dataset (or baseline)
**When** the user runs `python -m backend.agents.monitoring_agent evaluate --input current.csv`
**Then** the Monitoring Agent compares current-period metrics against the previous period using configured thresholds (FR7)
**And** if the Drift Engine has produced a DriftReport for this dataset, drift-based alert rules are also evaluated (e.g., type: mean_shift, column: revenue, threshold: 0.15)
**And** breached thresholds produce structured AlertMessage Pydantic models containing: alert_id, triggered_at, rule (type + column + threshold), finding (actual_value + severity + detail), and dataset name

**Given** one or more thresholds are breached
**When** alerts are generated
**Then** each alert is written to a structured JSON log file in output/alerts/ (FR8)
**And** each alert is sent via email (SMTP) to all recipients configured in config.yaml (FR8)
**And** the email contains: alert severity, rule description, actual vs threshold values, and the dataset name
**And** structlog entries are emitted for each alert with event="alert_triggered", severity, and rule details

**Given** no thresholds are breached
**When** the evaluation completes
**Then** a structlog entry is emitted with event="monitoring_clean" and no alerts are delivered
**And** the agent exits with code 0

**Given** config.yaml thresholds are modified (e.g., changing revenue threshold from 15% to 25%)
**When** the monitoring agent is run again
**Then** the updated thresholds are used for evaluation (FR10)
**And** previously-alerting conditions may no longer trigger if below the new threshold

**Given** SMTP delivery fails (server unreachable, authentication error)
**When** the email send fails
**Then** the alert is still written to the log file (log delivery is not dependent on email)
**And** the SMTP failure is logged as a warning with error details
**And** the agent does not crash

**Given** any monitoring run
**When** the agent executes
**Then** backend/tests/test_monitoring_agent.py passes with tests covering: threshold breach (single and multiple), no breach, drift-based alert rules, email delivery (mocked SMTP), SMTP failure fallback to log-only, and threshold config change

---

## Epic 3: Web Application & Customer Dashboard

Users interact through a browser — upload data, configure analysis parameters, view reports, monitor pipeline health and drift history, manage alert rules, and track usage. No CLI required.

### Story 3.1: Database Schema & Auth Foundation

As a user,
I want to register with email/password and securely access my own data through the web application,
So that I have a personal, authenticated workspace for my analytics.

**Acceptance Criteria:**

**Given** the existing frontend Supabase project and backend configuration
**When** the auth foundation is set up
**Then** frontend and backend are unified to a single Supabase project (frontend project survives; backend switches to frontend project URL/keys)
**And** SQLAlchemy 2.0 async session factory is configured in backend/db/session.py connecting to the unified Supabase PostgreSQL
**And** Alembic is initialized in backend/db/migrations/ with env.py configured for async

**Given** the database schema needs
**When** the initial migration runs
**Then** the following tables are created: users (id UUID PK, email, name, role, status, tenant_id nullable, created_at, updated_at, last_login_at, login_count), datasets (id, user_id FK, filename, file_path, file_size, uploaded_at, tenant_id nullable), reports (id, user_id FK, dataset_id FK, status, format, file_path, created_at, duration_seconds, tenant_id nullable), alerts (id, user_id FK, dataset_id FK, rule_type, severity, status, title, detail, evidence JSON, triggered_at, acknowledged_at, resolved_at, tenant_id nullable), alert_rules (id, user_id FK, rule_type, parameters JSON, delivery_channels JSON, enabled, created_at, last_triggered_at, tenant_id nullable), pipeline_runs (id, user_id FK, dataset_id FK, status, dqa_severity, drift_severity, duration_seconds, pipeline_result JSON, started_at, completed_at, tenant_id nullable), user_configs (id, user_id FK, column_mapping JSON, report_frequency, threshold_config JSON, tenant_id nullable)
**And** all tables include tenant_id (nullable) as per Architecture requirement for future Phase 5 RLS
**And** all tables follow naming conventions: plural snake_case tables, snake_case columns, {table_singular}_id foreign keys

**Given** a new visitor to the application
**When** they register with email and password via the web UI
**Then** Supabase Auth creates the user account and returns a JWT
**And** a corresponding row is created in the users table with role="tenant_owner" and status="active"

**Given** a registered user
**When** they log in with correct credentials
**Then** Supabase Auth returns a valid JWT
**And** last_login_at and login_count are updated in the users table

**Given** an incoming API request to any backend endpoint under /api/
**When** the request is processed
**Then** backend/api/auth.py middleware verifies the Supabase JWT
**And** backend/api/deps.py provides get_current_user dependency that extracts user info from the token
**And** unauthenticated requests receive a 401 response in RFC 7807 format
**And** slowapi rate limiting is applied to all endpoints

**Given** the frontend React application
**When** the Supabase client is configured
**Then** src/integrations/supabase/client.ts points to the single unified Supabase project
**And** authentication state is managed via Supabase Auth hooks
**And** all API requests include the Authorization: Bearer <jwt> header

### Story 3.2: File Upload & Pipeline Integration

As a user,
I want to upload a CSV file through drag-and-drop in my browser and automatically receive a generated report,
So that I can analyze my data without using the command line.

**Acceptance Criteria:**

**Given** an authenticated user on the dashboard
**When** they drag and drop a CSV file onto the upload area (or click to select)
**Then** the file is validated client-side (file type check: .csv, size limit feedback)
**And** the file is uploaded to the backend via POST /api/uploads with multipart form data
**And** a progress indicator is displayed during upload

**Given** a valid CSV file received by the backend
**When** the upload endpoint processes the file
**Then** the file is stored (Supabase Storage or local filesystem) with a unique path scoped to the user
**And** a datasets row is created with filename, file_path, file_size, and user_id
**And** the pipeline orchestrator is invoked synchronously (Phase 3 — async comes in Phase 5)
**And** a pipeline_runs row is created tracking status, DQA severity, drift severity, duration, and pipeline_result JSON

**Given** the pipeline completes successfully
**When** the report is generated
**Then** the rendered report file (docx/pdf) is stored and a reports row is created
**And** the user is redirected to or shown the report viewer with the new report
**And** the upload endpoint returns the report ID and pipeline run status

**Given** the pipeline halts on critical data quality issues
**When** the halt occurs
**Then** the pipeline_runs row is updated with status="halted" and the halt reason
**And** the user sees a clear error message with the DQA findings that caused the halt
**And** no report is generated

**Given** an invalid file upload (wrong type, empty file, corrupt CSV)
**When** the validation fails
**Then** the user receives immediate feedback describing the issue (NFR4 — input sanitization)
**And** no dataset or pipeline_run row is created

### Story 3.3: Analysis Configuration UI

As a user,
I want to configure my analysis parameters through a web form — selecting column roles, report frequency, and alert thresholds,
So that the system analyzes my data the way I need without editing config files.

**Acceptance Criteria:**

**Given** an authenticated user who has uploaded at least one dataset
**When** they navigate to the Settings page
**Then** a form displays with: column mapping (dropdowns to select date column, metric columns, category columns from the dataset's headers), report frequency (dropdown: manual, daily, weekly, monthly), and threshold configuration (numeric inputs per metric with ±15% defaults)

**Given** a user fills out the configuration form
**When** they submit the form
**Then** the configuration is saved via PUT /api/config to the user_configs table
**And** a success toast notification confirms the save
**And** subsequent pipeline runs use the saved configuration for column selection and threshold evaluation

**Given** a user changes their configuration
**When** they update and resubmit the form
**Then** the existing user_configs row is updated (not duplicated)
**And** the next pipeline run reflects the new settings

**Given** no dataset has been uploaded yet
**When** the user navigates to Settings
**Then** the column mapping section shows a message prompting them to upload a dataset first
**And** report frequency and threshold settings are still configurable

### Story 3.4: Report Viewer & History

As a user,
I want to view my generated reports in the browser and download them as docx or PDF, with a history of all past reports,
So that I can access and share my analytical insights at any time.

**Acceptance Criteria:**

**Given** an authenticated user with at least one generated report
**When** they navigate to the Reports page
**Then** a report history table is displayed with columns: timestamp (created_at), dataset name, format (docx/pdf), status, and duration
**And** the table is sorted by most recent first
**And** the table supports pagination

**Given** a report in the history table
**When** the user clicks on a report row
**Then** the report is displayed in-browser (PDF via iframe embed, or HTML-rendered content for docx)
**And** a download button is available that triggers file download in the original format (docx or PDF)

**Given** the user wants a different format
**When** they click a format toggle (docx ↔ PDF)
**Then** the report is re-rendered in the requested format if not already generated
**Or** the existing alternate format is served if previously rendered

**Given** a report was generated from a halted pipeline
**When** the user views the report history
**Then** the halted run appears with status="halted" and a viewable DQA diagnostic summary instead of a full report

**Given** the API endpoint GET /api/reports
**When** called with a valid JWT
**Then** only reports belonging to the authenticated user are returned
**And** GET /api/reports/{id}/download returns the report file with proper Content-Type and Content-Disposition headers

### Story 3.5: Alert Dashboard & Timeline

As a user,
I want to see a chronological timeline of all alerts, view evidence for each alert, and acknowledge or resolve them,
So that I stay informed about data anomalies and can track my response to them.

**Acceptance Criteria:**

**Given** an authenticated user with alerts triggered by the Monitoring Agent
**When** they navigate to the Alerts page
**Then** an alert timeline is displayed with columns: timestamp, rule type, severity (color-coded badge), title, and status (active/acknowledged/resolved)
**And** the list is sorted chronologically descending (newest first)
**And** filters are available for: severity (Critical/High/Medium/Low), rule type, status (active/acknowledged/resolved), and date range

**Given** an active alert in the timeline
**When** the user clicks "Acknowledge"
**Then** the alert status changes to "acknowledged" via PATCH /api/alerts/{id}
**And** acknowledged_at timestamp is recorded
**And** the UI updates immediately without page reload

**Given** an acknowledged alert
**When** the user clicks "Resolve"
**Then** the alert status changes to "resolved" via PATCH /api/alerts/{id}
**And** resolved_at timestamp is recorded

**Given** an alert in the timeline
**When** the user clicks to view detail
**Then** an alert detail panel shows: the evidence (specific DQA or drift finding that triggered the alert, including column name, actual value, threshold, and severity), a context link to the pipeline run that produced the alert (clicking navigates to the run detail view), and a history section showing previous alerts of the same rule type for this dataset

**Given** the API endpoint GET /api/alerts
**When** called with a valid JWT
**Then** only alerts belonging to the authenticated user are returned
**And** query parameters support filtering by severity, rule_type, status, and date range

### Story 3.6: Alert Configuration UI

As a user,
I want to create, edit, disable, and test monitoring rules through the browser,
So that I control what triggers alerts without editing config files.

**Acceptance Criteria:**

**Given** an authenticated user on the Alert Configuration page
**When** the page loads
**Then** an active rules table is displayed with columns: rule type, parameters summary, status (enabled/disabled), delivery channels, and last triggered date
**And** actions are available: edit, disable/enable toggle, delete (with confirmation)

**Given** a user clicks "Add Rule"
**When** the rule creation form opens
**Then** a dropdown offers rule types: drift_severity, mean_shift, volume_change, schema_change, completeness_drop, dqa_severity
**And** after selecting a type, parameter fields appear relevant to that type (e.g., column selector, threshold percentage, severity level)
**And** delivery channel checkboxes are shown (log file, email)
**And** on submit, the rule is saved via POST /api/rules and appears in the table

**Given** an existing rule
**When** the user clicks "Edit"
**Then** the rule form is pre-populated with current values
**And** on submit, the rule is updated via PATCH /api/rules/{id}

**Given** a user wants to verify a rule
**When** they click "Test Rule" on any rule
**Then** the rule is evaluated against the most recent pipeline output for the user
**And** the result shows whether the rule would have triggered or not, with the actual values compared against the thresholds
**And** no actual alert is created or delivered during the test

**Given** a user disables a rule
**When** they toggle the status
**Then** the rule remains in the database but is excluded from future monitoring evaluations
**And** the UI reflects the disabled state immediately

### Story 3.7: Pipeline Health Dashboard

As a user,
I want a landing page showing my pipeline health at a glance — last run status, success rate, data quality score, and active alerts,
So that I immediately know the state of my data when I log in.

**Acceptance Criteria:**

**Given** an authenticated user
**When** they navigate to the dashboard (default landing page after login)
**Then** four overview cards are displayed: Last Run (timestamp, dataset name, status with color indicator, duration), Success Rate (percentage over last 30 days with sparkline trend), Data Quality Score (latest DQA completeness/consistency/uniqueness scores, color-coded green/yellow/red), Active Alerts (count of unacknowledged alerts, clickable to navigate to Alert Timeline)

**Given** the overview cards
**When** data is loaded from GET /dashboard/v1/health
**Then** the endpoint returns aggregated metrics scoped to the authenticated user
**And** loading states use React Query's built-in isLoading/isError/data pattern

**Given** the dashboard page
**When** scrolling below the overview cards
**Then** a Run History Table is displayed with columns: timestamp, dataset name, status (success/failed/halted), DQA severity (badge), drift severity (badge, if baseline existed), duration, and report link
**And** filters are available for: date range, status, and dataset
**And** the table supports pagination

**Given** a row in the Run History Table
**When** the user clicks on a row
**Then** a Run Detail View opens with expandable sections: DQA findings table with severity badges, Drift Analysis (if baseline existed, showing per-column drift details), Insight Summary (key findings and recommendations), and a download button for the docx/PDF report

### Story 3.8: Drift History View

As a user,
I want to see how my datasets have changed over time relative to baselines, with per-column drill-down and trend charts,
So that I can understand whether my data quality is improving or degrading.

**Acceptance Criteria:**

**Given** an authenticated user with datasets that have established baselines (2+ pipeline runs)
**When** they navigate to the Drift History page
**Then** a dataset selector dropdown lists all datasets with baselines
**And** selecting a dataset displays a drift timeline: a horizontal color-coded bar per run (green = no drift, yellow = medium, red = high severity)

**Given** a drift timeline for a selected dataset
**When** the user clicks on a specific run in the timeline
**Then** a column-level drill-down panel opens showing: per-column mean shift percentage, variance ratio, and PSI value, each with severity badges
**And** baseline info is displayed: baseline creation timestamp, consecutive clean run count (toward auto-rotation threshold of 4), and a "Rotate Baseline" button

**Given** the user clicks "Rotate Baseline"
**When** the manual rotation is triggered via POST /dashboard/v1/drift/{dataset_id}/rotate
**Then** the current dataset profile replaces the existing baseline
**And** the consecutive clean run counter resets
**And** a success notification confirms the rotation

**Given** the drift history page for a dataset
**When** trend charts are rendered below the timeline
**Then** three charts are displayed: Mean Trend (line chart showing column means over time with baseline reference line), Volume Trend (bar chart showing row count per run with baseline reference), Drift Score Trend (composite drift severity over time)
**And** chart data is loaded from GET /dashboard/v1/drift/{dataset_id}/trend

**Given** a dataset with only one pipeline run (no baseline yet)
**When** it appears in the dataset selector
**Then** a message indicates "Baseline will be established after first run — drift comparison available from second run onward"

### Story 3.9: Usage Meter

As a user,
I want to see my consumption against plan limits — reports generated, data volume, storage used, and billing cycle — with an upgrade prompt when approaching limits,
So that I understand my usage and can plan for upgrades before hitting caps.

**Acceptance Criteria:**

**Given** an authenticated user
**When** they navigate to the Usage page (or a Usage section on the dashboard)
**Then** the following metrics are displayed with progress bars: reports generated this period / plan limit, data volume processed this period (MB) / plan limit, storage used (total MB for uploaded datasets and generated reports), and API calls this period / limit (shown only for Professional+ plans)

**Given** the usage display
**When** the data loads from GET /dashboard/v1/usage
**Then** billing cycle information is shown: current period start/end dates, and days remaining in the period
**And** current plan details are shown: plan name, price, and included features summary

**Given** a user's usage is above 80% of any plan limit
**When** the usage meter renders
**Then** the progress bar for that metric changes to a warning color (yellow/orange)
**And** an upgrade CTA button is displayed: "Upgrade Plan" linking to the billing page

**Given** a user's usage reaches 100% of a plan limit
**When** the limit is hit
**Then** the progress bar changes to red
**And** a clear message explains the limit has been reached and what actions are restricted
**And** the API layer enforces the limit (returns 429 with RFC 7807 error detail)

**Given** a user on the free trial
**When** they view usage
**Then** trial status is displayed: "Free Trial — X days remaining"
**And** all Professional-tier limits apply during the trial

---

## Epic 4: Subscription Billing

Users subscribe to a tiered plan, manage billing through Stripe, and the system enforces usage limits per tier — making SavvyCortex a paid product.

### Story 4.1: Stripe Integration & Plan Tiers

As a user,
I want to select a subscription plan and complete payment through a secure checkout flow,
So that I can access the features and limits appropriate for my needs.

**Acceptance Criteria:**

**Given** the backend Stripe integration
**When** the Stripe SDK is configured
**Then** stripe-python is initialized with API keys from environment variables (never hardcoded)
**And** three Stripe Products with Prices are defined corresponding to plan tiers: Starter (limited reports/month, basic thresholds, email alerts only), Professional (higher report limits, custom thresholds, priority processing), Enterprise (unlimited reports, API access, dedicated support, custom branding)
**And** backend/services/billing_service.py encapsulates all Stripe API interactions

**Given** a new or existing user without a subscription
**When** they select a plan on the Billing page
**Then** a Stripe Checkout session is created via POST /api/billing/checkout with the selected price ID
**And** the user is redirected to Stripe's hosted Checkout page
**And** on successful payment, the user is redirected back to the application with an active subscription

**Given** an active subscriber
**When** they want to manage their billing (update payment method, view invoices, cancel)
**Then** a Stripe Customer Portal session is created via POST /api/billing/portal
**And** the user is redirected to Stripe's hosted Customer Portal
**And** changes made in the portal (payment method update, cancellation) are reflected via webhooks

**Given** the plan tier definition
**When** a user's subscription is active
**Then** the users table or a subscriptions table stores: stripe_customer_id, stripe_subscription_id, plan_tier, subscription_status (active/trialing/past_due/cancelled), current_period_start, current_period_end

### Story 4.2: Webhook Handling & Subscription Lifecycle

As a platform operator,
I want Stripe webhook events to automatically update subscription state in the database,
So that plan changes, failed payments, and cancellations are handled without manual intervention.

**Acceptance Criteria:**

**Given** the Stripe webhook endpoint at POST /api/webhooks/stripe
**When** a webhook event is received
**Then** the endpoint verifies the Stripe signature using the webhook signing secret
**And** invalid signatures are rejected with 400 status
**And** all event processing is idempotent (reprocessing the same event produces no duplicate side effects)

**Given** a checkout.session.completed event
**When** the webhook processes it
**Then** the user's subscription record is created or updated with stripe_customer_id, stripe_subscription_id, plan_tier, and status="active"
**And** usage counters are initialized for the new billing period

**Given** an invoice.payment_failed event
**When** the webhook processes it
**Then** the user's subscription status is updated to "past_due"
**And** a grace period begins (configurable, default 7 days)
**And** the user receives in-app notification of the failed payment
**And** API access continues during the grace period with a warning banner

**Given** a customer.subscription.updated event (plan change)
**When** the webhook processes an upgrade or downgrade
**Then** the plan_tier is updated to the new tier
**And** usage limits are adjusted to the new plan's limits immediately for upgrades
**And** for downgrades, new limits take effect at the next billing period

**Given** a customer.subscription.deleted event (cancellation)
**When** the webhook processes it
**Then** the subscription status is updated to "cancelled"
**And** the user retains access until current_period_end (paid-through date)
**And** after that date, access is restricted to read-only (can view existing reports but not generate new ones)

**Given** any webhook event
**When** it is processed
**Then** a structlog entry is emitted with event type, customer ID, and outcome
**And** backend/tests/test_webhooks.py passes with tests covering: signature verification, each event type, idempotent reprocessing, and invalid payload handling

### Story 4.3: Usage Tracking & Limit Enforcement

As a platform operator,
I want to track each user's consumption per billing period and enforce plan limits at the API layer,
So that usage stays within plan boundaries and users receive clear feedback when approaching or hitting limits.

**Acceptance Criteria:**

**Given** an active subscriber making API requests
**When** any report-generating, data-uploading, or alert-triggering action is performed
**Then** the corresponding usage counter is incremented: report_count, data_volume_bytes, alert_count for the current billing period
**And** usage is tracked in a usage_records table (or user-scoped counters) keyed by user_id and billing period

**Given** a user approaching a plan limit (80% threshold)
**When** the usage check runs
**Then** the API response includes a warning header (e.g., X-Usage-Warning: reports 80% consumed)
**And** the frontend can display this as a non-blocking notification

**Given** a user who has reached their plan limit for any metric
**When** they attempt an action that would exceed the limit
**Then** the API returns 429 Too Many Requests with an RFC 7807 error body: type, title="Plan Limit Reached", detail describing which limit was hit, and a suggestion to upgrade
**And** the action is not performed
**And** existing data and reports remain accessible (read-only is never blocked)

**Given** a new billing period begins (detected via Stripe webhook or period check)
**When** the period rolls over
**Then** all usage counters reset to zero for the new period
**And** the previous period's usage is retained for historical reference

**Given** the feature gating middleware
**When** a request arrives at any metered endpoint
**Then** backend/api/deps.py checks subscription status (active/trialing) and usage counts before allowing the request
**And** users without an active subscription (expired trial, cancelled past period end) are blocked from metered actions with a 403 and upgrade prompt

### Story 4.4: Billing UI & Free Trial

As a user,
I want to start a free trial without a credit card, view my plan details, and manage my subscription through the web interface,
So that I can try the product risk-free and easily manage my billing.

**Acceptance Criteria:**

**Given** a new user who has registered but has no subscription
**When** they navigate to the Billing page
**Then** a plan comparison table is displayed showing all three tiers with: name, price, included features, and usage limits per tier
**And** a "Start Free Trial" button is prominently displayed for the Professional tier
**And** upgrade buttons are shown for each paid tier

**Given** a user clicks "Start Free Trial"
**When** the trial is initiated via POST /api/billing/trial
**Then** the user's subscription is created in Stripe with a 14-day trial period on the Professional plan
**And** no credit card is required to start the trial (FR20)
**And** subscription status is set to "trialing"
**And** the user immediately has access to Professional-tier features and limits

**Given** a user with an active subscription (paid or trial)
**When** they visit the Billing page
**Then** the page displays: current plan name and status (active/trialing/past_due), usage summary (reports used / limit, data volume / limit), current billing period dates, and a "Manage Billing" button

**Given** a user clicks "Manage Billing"
**When** the Stripe Customer Portal opens
**Then** the user can: view invoice history, update payment method, upgrade or downgrade their plan, and cancel their subscription
**And** all changes are reflected in the application via webhook processing (Story 4.2)

**Given** a trial user with 3 days remaining
**When** they visit the Billing page
**Then** a trial countdown is displayed: "Free Trial — 3 days remaining"
**And** a prompt encourages adding a payment method to continue after trial
**And** if the trial expires without payment, access reverts to read-only

---

## Epic 5: Multi-Tenant Scale & Production Hardening

Multiple organizations use the platform safely with complete data isolation, async processing handles load, and the system is containerized with CI/CD and observability — production-ready infrastructure.

### Story 5.1: Multi-Tenant Data Isolation

As a platform operator,
I want every database query and file access scoped to the authenticated tenant with row-level security enforced at the database level,
So that two tenants can never access each other's data under any circumstance.

**Acceptance Criteria:**

**Given** the existing database tables with nullable tenant_id columns (from Epic 3)
**When** the multi-tenancy migration runs
**Then** tenant_id is made NOT NULL on all tenant-scoped tables (datasets, reports, alerts, alert_rules, pipeline_runs, user_configs, usage_records)
**And** a tenants table is created (id UUID PK, name, owner_id FK, plan_tier, status, created_at, trial_ends_at, stripe_customer_id, stripe_subscription_id, storage_used_bytes, report_count_current_period, last_active_at, settings JSON)
**And** existing users are assigned to a default tenant created via data migration
**And** PostgreSQL row-level security policies are enabled: each table gets a policy `USING (tenant_id = current_setting('app.current_tenant_id')::uuid)` enforcing that queries only return rows matching the session tenant

**Given** an authenticated API request
**When** the request passes through backend/api/middleware/tenant_scope.py
**Then** the middleware extracts tenant_id from the JWT claims and sets PostgreSQL session variable `app.current_tenant_id` on the database connection
**And** all subsequent queries on that connection are automatically filtered by tenant_id via RLS — no application-level WHERE clauses needed for isolation
**And** requests without a valid tenant_id are rejected with 403

**Given** file storage (uploaded datasets and generated reports)
**When** files are stored or retrieved
**Then** file paths are partitioned by tenant_id: `storage/{tenant_id}/datasets/` and `storage/{tenant_id}/reports/`
**And** directory traversal attempts (e.g., `../../other_tenant_id/`) are blocked at the middleware level
**And** the upload and download services validate that the requested file belongs to the authenticated tenant

**Given** two tenants (Tenant A and Tenant B) with separate data
**When** Tenant A makes any API request
**Then** the response contains only Tenant A's data — zero rows from Tenant B are returned
**And** this is verified by integration tests that create two tenants, insert data for each, and assert complete isolation
**And** direct database queries (bypassing the API) with the wrong tenant session variable return zero rows

**Given** the tenant isolation implementation
**When** tested
**Then** backend/tests/integration/test_tenant_isolation.py passes with tests covering: RLS policy enforcement, cross-tenant query blocking, file path partitioning, directory traversal prevention, and middleware tenant injection

### Story 5.2: Async Processing Pipeline

As a user,
I want report generation and monitoring jobs to run asynchronously so I receive status updates instead of waiting on long-running requests,
So that the UI stays responsive and the system handles concurrent load without degradation.

**Acceptance Criteria:**

**Given** the Celery + Redis infrastructure
**When** the async system is set up
**Then** backend/tasks/celery_app.py configures Celery with Redis as the message broker
**And** backend/tasks/report_tasks.py defines an async task for report generation (wrapping the pipeline orchestrator)
**And** backend/tasks/monitoring_tasks.py defines an async task for monitoring evaluation
**And** a dead letter queue is configured for failed tasks that exceed retry limits (NFR10)

**Given** a user triggers report generation via the web UI (POST /api/reports/generate)
**When** the API receives the request
**Then** a Celery task is enqueued and the API immediately returns 202 Accepted with a task_id
**And** the pipeline_runs row is created with status="pending"

**Given** an enqueued report task
**When** the user polls GET /api/reports/status/{task_id}
**Then** the endpoint returns the current task state: `{"status": "pending" | "processing" | "completed" | "failed", "progress": 0.0-1.0}`
**And** on completion, the response includes the report_id for viewing/downloading
**And** on failure, the response includes error details

**Given** the system under load
**When** 10 concurrent report generation tasks are enqueued
**Then** all 10 tasks complete successfully without degradation (FR26, NFR2)
**And** task execution is distributed across available Celery workers
**And** average task wait time remains acceptable (queue depth monitored)

**Given** a task fails after all retries
**When** the task is moved to the dead letter queue
**Then** the pipeline_runs row is updated with status="failed" and error details
**And** a structlog entry is emitted at level "error" with the task_id, error type, and retry count
**And** the user sees the failure in their Run History with actionable error information

**Given** the scheduled reporting and monitoring agents (from Epic 2)
**When** Phase 5 is active
**Then** scheduled runs are enqueued as Celery tasks instead of running synchronously
**And** the scheduling mechanism (APScheduler) enqueues tasks rather than executing directly

### Story 5.3: Observability & Error Tracking

As a platform operator,
I want structured logging with correlation IDs, Sentry error tracking, and a system health metrics endpoint,
So that I can diagnose issues, track error rates, and monitor system health in production.

**Acceptance Criteria:**

**Given** the existing structlog configuration (from Epic 1)
**When** the observability enhancements are applied
**Then** every web request receives a unique request_id via middleware, propagated through structlog context alongside pipeline_run_id
**And** all log entries include: timestamp, level, event, request_id (for web), pipeline_run_id (for pipeline), tenant_id (when available), and module-specific fields
**And** log output is JSON-formatted and written to stdout (containerized logging best practice)

**Given** the Sentry SDK integration
**When** Sentry is initialized in backend/main.py
**Then** unhandled exceptions are automatically captured and reported to Sentry with full context (request details, user info, tenant_id)
**And** SavvyCleanseError hierarchy exceptions include structured breadcrumbs showing the pipeline stage and data context
**And** Sentry is initialized with a DSN from environment variables (not hardcoded)
**And** frontend Sentry (React SDK) is configured in src/main.tsx for client-side error tracking

**Given** the system health endpoint GET /api/system/health
**When** an authenticated admin or monitoring service calls it
**Then** the response includes: pipeline metrics (total runs 24h/7d, success rate, average duration), queue metrics (Celery queue depth, active workers, DLQ count), API metrics (request count, error rates by status code), database metrics (connection pool utilization), and storage metrics (total storage used)
**And** each metric includes a status indicator (healthy/warning/critical) based on configurable thresholds

**Given** the observability system
**When** tested
**Then** correlation IDs are traceable end-to-end from API request through pipeline stages to response
**And** Sentry captures test errors in a staging environment
**And** the health endpoint returns accurate, current metrics

### Story 5.4: Security Hardening & OWASP Review

**Prerequisite Task (should be completed during Story 5.5 or earlier):**
Configure GitHub Actions Anthropic automated security review on PR creation. The action triggers automatically when pull requests are opened, posting inline comments with identified concerns and recommended fixes. This ensures every PR gets a security review before Story 5.4's formal OWASP audit, and provides a safety net for all subsequent development. Reference: https://support.claude.com/en/articles/11932705-automated-security-reviews-in-claude-code

As a platform operator,
I want all user inputs sanitized, API endpoints rate-limited, connections encrypted, and secrets properly managed,
So that the platform meets OWASP top-10 security standards before production launch.

**Acceptance Criteria:**

**Given** all API endpoints that accept user input
**When** a security audit is performed
**Then** all file upload paths validate file type, size, and content (not just extension) — (NFR4)
**And** all string inputs are sanitized against XSS (HTML entities escaped)
**And** all database queries use parameterized statements via SQLAlchemy (no raw SQL string concatenation)
**And** rate limiting via slowapi is configured per endpoint with sensible defaults (e.g., 100 req/min for reads, 20 req/min for writes) — (NFR5)

**Given** the deployment configuration
**When** HTTPS is enforced
**Then** all HTTP requests are redirected to HTTPS (NFR6)
**And** HSTS headers are set with a minimum 1-year max-age
**And** cookies are set with Secure, HttpOnly, and SameSite attributes

**Given** the secrets management audit
**When** the codebase is reviewed
**Then** zero hardcoded credentials exist (NFR3) — all API keys, database URLs, Stripe keys, SMTP credentials, and Sentry DSN are loaded from environment variables
**And** .env.example documents all required variables with placeholder values
**And** Docker secrets are configured for production deployment (docker-compose.yml references secrets, not env vars, for sensitive values)

**Given** the OWASP top-10 review (NFR14)
**When** the review is completed
**Then** each OWASP category is assessed: A01 Broken Access Control (RLS + middleware), A02 Cryptographic Failures (HTTPS + bcrypt + JWT), A03 Injection (parameterized queries + input validation), A04 Insecure Design (threat model reviewed), A05 Security Misconfiguration (default credentials removed, debug mode off), A06 Vulnerable Components (dependency audit), A07 Auth Failures (rate limiting on login, account lockout), A08 Data Integrity (webhook signature verification, CSRF tokens), A09 Logging Failures (structlog + Sentry coverage), A10 SSRF (no user-controlled URL fetching without allowlisting)
**And** findings are documented with severity and remediation status
**And** all Critical and High findings are resolved before production deployment

### Story 5.5: Containerized Deployment & CI/CD

As a platform operator,
I want the application containerized with Docker, automated CI/CD via GitHub Actions, and a staging environment mirroring production,
So that deployments are reproducible, tested, and reliable.

**Acceptance Criteria:**

**Given** the project root
**When** containerization is set up
**Then** a Dockerfile exists that builds the backend (Python 3.13 + dependencies) into a production-ready image with non-root user, health check, and minimal attack surface
**And** docker-compose.yml defines services: backend (FastAPI + Uvicorn), redis (message broker), postgres (database), celery-worker (task processor), and celery-beat (task scheduler)
**And** `docker-compose up` starts all services and the application is functional at localhost

**Given** a pull request to the main branch
**When** GitHub Actions CI runs (.github/workflows/ci.yml)
**Then** the pipeline: installs Python dependencies, runs `pytest backend/tests/` (unit + integration), runs `npx vitest` (frontend tests), runs linting (ruff or flake8 for Python, eslint for TypeScript), and builds the frontend (`npm run build`)
**And** the PR cannot merge if any step fails

**Given** a merge to the main branch
**When** GitHub Actions CD runs (.github/workflows/deploy.yml)
**Then** the Docker image is built and pushed to a container registry
**And** the staging environment is updated with the new image
**And** a smoke test runs against staging to verify the deployment (health endpoint returns 200)

**Given** the staging environment
**When** it is configured
**Then** staging mirrors production: same Docker Compose services, same environment variable structure (different values), same database schema (via Alembic migrations)
**And** staging uses a separate Supabase project (or standalone PostgreSQL) with test data
**And** staging is accessible for QA verification before production promotion

**Given** the deployment infrastructure
**When** tested end-to-end
**Then** `docker-compose down && docker-compose up --build` produces a clean, working environment from scratch
**And** database migrations run automatically on container startup (Alembic upgrade head)
**And** the system recovers gracefully if Redis or the database is temporarily unavailable (Celery retries, connection pool reconnects)

---

## Epic 6: Admin Control Plane

Platform operators manage tenants, users, API tokens, system health, billing metrics, customer journeys, and audit all administrative actions from a dedicated dashboard — the business operations center.

### Story 6.1: Role Hierarchy & Admin Auth

As a platform operator,
I want a 5-role permission system with a dedicated admin middleware stack and CLI-provisioned superadmin,
So that admin access is strictly separated from customer access and cannot be escalated through the UI.

**Acceptance Criteria:**

**Given** the role hierarchy definition
**When** the role system is implemented
**Then** 5 roles are defined: superadmin, admin, tenant_owner, tenant_member, tenant_viewer
**And** the permission matrix is enforced: superadmin has full system access including impersonation and admin management; admin has cross-tenant visibility, tenant CRUD, billing management, and token grants; tenant_owner manages own tenant, team members, and API tokens; tenant_member has read/execute access (run pipelines, configure alerts, view reports); tenant_viewer has read-only access (view reports and alerts only)
**And** the users table role column is validated against this enum

**Given** the admin route protection
**When** any request hits /admin/v1/* endpoints
**Then** backend/api/middleware/admin_guard.py intercepts the request before it reaches the route handler
**And** the middleware validates the JWT and checks that the user's role is superadmin or admin
**And** standard user tokens (tenant_owner, tenant_member, tenant_viewer) are rejected with 403 regardless of any role claim manipulation (NFR19)
**And** the admin middleware stack is completely separate from the customer API middleware

**Given** the superadmin provisioning requirement (NFR22)
**When** the first superadmin needs to be created
**Then** a CLI command `python -m backend.admin create-superadmin --email admin@example.com` creates the account
**And** superadmin accounts cannot be created through any web UI endpoint
**And** subsequent superadmins can only be created by an existing superadmin via POST /admin/v1/admins (not the CLI)

**Given** IP allowlisting configuration (NFR21)
**When** admin access is configured
**Then** an optional IP allowlist can be defined in environment variables or config
**And** when enabled, admin endpoints reject requests from non-allowlisted IPs with 403
**And** IP allowlisting is disabled by default but the infrastructure is in place for production activation

### Story 6.2: Audit Log

As a platform operator,
I want an immutable, append-only log of every admin action with search, filtering, and export,
So that I have a complete compliance trail for security reviews and debugging.

**Acceptance Criteria:**

**Given** the audit log data model
**When** the audit_log table is created
**Then** it contains: id UUID PK, actor_id UUID FK, actor_email (denormalized), actor_role, action (e.g., "tenant.suspend"), target_type (e.g., "tenant", "user", "token"), target_id UUID, target_label (denormalized name/email), details JSON (action-specific payload), ip_address, timestamp
**And** the table is append-only: the application database user has no DELETE or UPDATE permissions on audit_log (NFR23)
**And** a separate migration grants only INSERT and SELECT to the application role

**Given** any action performed through the admin interface
**When** the action is executed
**Then** an AuditLogEntry is automatically created capturing: who (actor_id, email, role), what (action verb, target type and ID), context (details JSON, IP address), and when (timestamp)
**And** the following actions are logged: tenant created/suspended/reactivated/deleted, user role changed/suspended/password reset, API token created/revoked, plan changed/trial extended/credit issued, impersonation started/ended, admin user created/removed/permissions changed, system configuration changed

**Given** the audit log view at GET /admin/v1/audit (superadmin only)
**When** the admin accesses the audit log page
**Then** a chronological table displays: timestamp, actor, action, target, details summary
**And** filters are available: by actor, by action type, by target type, by date range
**And** full-text search is available across action descriptions and target labels

**Given** the compliance export requirement
**When** an admin clicks "Export CSV"
**Then** the filtered audit log entries are exported as a CSV file with all fields
**And** the export itself is audit-logged

**Given** the retention policy
**When** audit log entries are created
**Then** entries are retained for a minimum of 2 years
**And** no automated purge mechanism deletes entries within the retention window

### Story 6.3: Tenant Management

As a platform operator,
I want to view, search, suspend, and impersonate tenants from a centralized management interface,
So that I can manage customer accounts and debug issues efficiently.

**Acceptance Criteria:**

**Given** an admin user on the Admin Control Plane
**When** they navigate to Tenant Management
**Then** a Tenant List View displays a table with columns: tenant name, owner email, plan tier, status (active/suspended/trial/cancelled), signup date, last active, report count (current period), storage used, MRR contribution
**And** filters are available: by plan tier, by status, by signup date range, by last active range
**And** sorting is available on any column with default: last active descending
**And** data is loaded from GET /admin/v1/tenants

**Given** a tenant row in the list
**When** the admin clicks to view detail
**Then** a Tenant Detail View displays: overview (metadata, owner contact, plan details, billing status, signup source), team members (list with roles, last login, invite status), usage (reports generated current + historical, data volume, alerts triggered, API calls, storage consumed), pipeline history (table of all runs with timestamp, dataset, status, DQA severity, drift severity, duration), and billing (current plan, payment history, failed payments, trial status)

**Given** the tenant detail view
**When** the admin performs actions
**Then** the following actions are available: suspend tenant (POST /admin/v1/tenants/{id}/suspend), reactivate tenant, delete tenant (with confirmation modal), change plan, extend trial, issue credit, reset password for any user, revoke API tokens, export tenant data
**And** every action is audit-logged (Story 6.2)

**Given** a superadmin user
**When** they click "Impersonate" on a tenant (POST /admin/v1/tenants/{id}/impersonate)
**Then** an impersonation session is created that is time-limited to a maximum of 1 hour (NFR20)
**And** the admin sees the application as the tenant owner would see it
**And** every action during impersonation is audit-logged with both the admin's identity and the impersonated user's identity
**And** the impersonation session can be ended early by the admin
**And** impersonation is restricted to superadmin role only — admin role cannot impersonate

**Given** an admin suspends a tenant
**When** the suspension takes effect
**Then** the tenant status changes to "suspended"
**And** all users in that tenant are blocked from logging in or making API calls
**And** existing data and reports are preserved (not deleted)
**And** the tenant can be reactivated by an admin to restore access

### Story 6.4: User Management & API Tokens

As a platform operator,
I want to manage all users across tenants and administer API tokens with scoped permissions and expiry,
So that I have full control over access and can support customers who need programmatic integration.

**Acceptance Criteria:**

**Given** an admin on the User Management page
**When** the page loads
**Then** a User List View displays: email, name, tenant, role, status (active/invited/suspended), signup date, last login, total pipeline runs
**And** filters are available: by tenant, by role, by status, by signup date range
**And** search is available: by email and by name (partial match)
**And** data is loaded from GET /admin/v1/users

**Given** a user row in the list
**When** the admin clicks to view detail
**Then** a User Detail View displays: profile (email, name, role, tenant membership, signup date, last login, login count), activity log (chronological list of user actions: pipeline runs, report downloads, config changes, login events), permissions (current role and permission set with ability to modify), and API tokens (list of active tokens with creation date, last used, and scopes)

**Given** admin user management actions
**When** the admin performs changes
**Then** the following are available: suspend user (PATCH /admin/v1/users/{id}/role with status change), reset password, change role (dropdown limited to roles below admin), remove from tenant
**And** every action is audit-logged
**And** role changes take effect immediately on the user's next request

**Given** the API Token Management page (GET /admin/v1/tokens)
**When** an admin views the token list
**Then** a table displays: token name, tenant, created by, created at, last used, scope list, status (active/revoked/expired)
**And** actions available: revoke token (DELETE /admin/v1/tokens/{id}), view usage stats, create token on behalf of a tenant

**Given** token creation (for admin-created tokens or via future customer self-service)
**When** a new token is issued
**Then** scopes are selected from: read:reports, write:pipeline, read:alerts, write:config (additive)
**And** expiry is set: configurable, default 90 days, maximum 365 days, no non-expiring tokens allowed
**And** the token is generated with prefix format: svc_live_ for production, svc_test_ for sandbox
**And** the token value is shown once at creation, then only the token_prefix (first 8 chars) is visible
**And** the token_hash (SHA-256) is stored in the database — plaintext token is never persisted
**And** a usage_count and last_used_at are tracked per token

### Story 6.5: System Health Dashboard

As a platform operator,
I want a real-time system health dashboard showing pipeline, API, storage, queue, and database metrics,
So that I can monitor production health and respond to issues before they affect customers.

**Acceptance Criteria:**

**Given** an admin on the System Health page
**When** the page loads
**Then** 4–6 overview cards display top-level metrics with status indicators (green/yellow/red) and sparkline trends: pipeline success rate, API error rate, queue depth, and storage utilization

**Given** the overview section
**When** any metric enters a critical state (e.g., error rate > 5%, queue depth > 100)
**Then** a persistent alert banner appears at the top of the admin dashboard
**And** the affected metric card turns red

**Given** the detailed metrics section
**When** the admin scrolls below overview cards
**Then** time series charts are displayed for: pipeline volume and success/failure rate, API request count and error rate (4xx/5xx), average and p95 response times, and rate limit hits
**And** charts support selectable time windows: 1h, 6h, 24h, 7d, 30d
**And** data is loaded from GET /admin/v1/system/health

**Given** the system metrics backend
**When** the health endpoint is called
**Then** it returns: pipeline metrics (total runs 24h/7d/30d, success rate, failure rate, average duration, queue depth, longest running job), API metrics (request count, error rate by status code, average response time, p95 response time, rate limit hits), storage metrics (total storage across all tenants, growth rate, top 5 tenants by storage), task queue metrics (active workers, queue depth, DLQ count, average wait time, job failure rate), database metrics (connection pool utilization, slow query count)

### Story 6.6: Billing Overview

As a platform operator,
I want an aggregated revenue and billing health dashboard with quick intervention actions,
So that I can track business metrics and act on at-risk accounts before revenue is lost.

**Acceptance Criteria:**

**Given** an admin on the Billing Overview page
**When** the page loads from GET /admin/v1/billing/overview
**Then** the following metrics are displayed: MRR (monthly recurring revenue computed from active subscriptions), active subscription count broken down by plan tier (Starter/Professional/Enterprise), trial metrics (trials started, trials converted to paid, conversion rate), churn metrics (cancellations this period, churn rate, churned MRR), failed payment metrics (count of failed charges, total dollar amount at risk, number of tenants affected), revenue per plan (MRR breakdown by tier as a bar or pie chart)

**Given** the at-risk section
**When** the billing overview renders
**Then** an "At-Risk Tenants" list displays tenants with: failed payments, approaching trial expiry (< 3 days), or declining usage (no pipeline runs in 14+ days)
**And** the list is sorted by MRR at risk (highest first)
**And** each row shows: tenant name, risk reason, MRR value, and days until action needed

**Given** the at-risk tenant list
**When** the admin clicks a quick action button
**Then** the following actions are available: extend trial (specify days), apply discount (forward to Stripe), and issue credit (forward to Stripe via API)
**And** each action is executed via the Stripe API through backend/services/billing_service.py
**And** every action is audit-logged

### Story 6.7: Customer Journey Tracking

As a platform operator,
I want to track each tenant's lifecycle from signup through activation, engagement, expansion, and churn risk,
So that I can identify patterns, intervene at the right moment, and improve retention.

**Acceptance Criteria:**

**Given** the customer journey model
**When** the journey tracking tables are created
**Then** a journey_events table stores: id UUID PK, tenant_id FK, event_type (signup, first_run, activation, upgrade, downgrade, alert_configured, api_token_created, team_invite, payment_failed, cancellation, reactivation), stage_from (nullable), stage_to, timestamp, metadata JSON
**And** a tenant_journeys table (or view) tracks per-tenant: current_stage, stage_entered_at, days_in_stage, lifetime_pipeline_runs, lifetime_reports, first_run_at, last_run_at, has_configured_alerts, has_api_tokens, has_team_members, plan_upgrades, plan_downgrades

**Given** the 6 lifecycle stages
**When** stage transitions are evaluated
**Then** the stages are: Signup (account created, no pipeline runs), Activation (first successful pipeline run), Engaged (3+ pipeline runs in 7 days), Expanded (plan upgrade, team invite, or API token creation), At Risk (14 days without a run OR failed payment), Churned (cancellation event OR 30 days inactive)
**And** transitions are triggered automatically by the corresponding events (user registration, pipeline completion, subscription change, payment failure)
**And** each transition creates a journey_events row

**Given** the admin Journey page at GET /admin/v1/journey/funnel
**When** the page loads
**Then** a horizontal funnel visualization displays tenant counts at each stage
**And** clicking any stage opens a filtered tenant list showing all tenants currently in that stage

**Given** the Tenant Detail view (Story 6.3)
**When** the admin views a specific tenant's journey
**Then** a per-tenant timeline shows chronological stage transitions with dates via GET /admin/v1/journey/tenants/{id}
**And** each transition includes the event that triggered it and any relevant metadata

**Given** the cohort analysis section
**When** the admin views journey cohorts
**Then** tenants are grouped by signup week or month
**And** each cohort shows progression through stages over time (e.g., "March 2026 cohort: 40 signups → 25 activated → 12 engaged → 5 expanded")
**And** this helps identify which cohorts retain best and correlate with product changes

---

## Epic 7: Advanced Analytics & Self-Service API

Users access forecasting, ask natural language questions about their data, create custom monitoring rules with composite conditions, customize report templates, and integrate via a versioned REST API with webhooks.

### Story 7.1: Advanced Analytics Engine

As a user,
I want to run forecasting, correlation detection, cohort analysis, and comparative analysis on my datasets,
So that I can make data-driven predictions and uncover relationships beyond basic descriptive statistics.

**Acceptance Criteria:**

**Given** a dataset with a time-series column and at least 30 data points
**When** the user requests a forecast via the analytics UI or API
**Then** the system generates a 30-day projection using Prophet or statsmodels
**And** the forecast includes: predicted values, confidence intervals (upper/lower bounds), and trend direction
**And** the forecast is returned as a structured JSON payload and optionally included in the next generated report
**And** the forecast is computed from actual data — no LLM involvement in the numerical projection

**Given** a dataset with multiple numeric columns
**When** the user requests correlation analysis
**Then** the system computes pairwise correlation coefficients across all numeric columns
**And** statistically significant correlations (p-value < 0.05) are highlighted
**And** results are presented as a correlation matrix with strength indicators

**Given** a dataset with a categorical segmentation column
**When** the user requests cohort analysis
**Then** the system groups data by the selected category and computes per-cohort metrics (averages, trends, distributions)
**And** cohort comparison is presented with visualizations showing performance differences

**Given** a dataset with temporal data
**When** the user requests comparative analysis (period-over-period)
**Then** the system compares the current period against the previous period (configurable: week-over-week, month-over-month)
**And** statistical significance testing is applied to determine whether changes are meaningful or within noise range
**And** results include: percentage change, absolute change, p-value, and a significance indicator

**Given** the analytics module
**When** implemented
**Then** backend/services/analytics_service.py (or pipeline extension) encapsulates all advanced analytics
**And** frontend components in src/components/analytics/ include ForecastChart, CohortTable, and correlation visualization
**And** analytics endpoints are available at /api/analytics/forecast, /api/analytics/correlations, /api/analytics/cohort, /api/analytics/comparative

### Story 7.2: Custom Monitoring Rules & Digest Reports

As a user,
I want to define monitoring rules with composite conditions and receive scheduled digest reports summarizing my chosen metrics,
So that I am alerted to complex patterns and receive regular summaries tailored to my needs.

**Acceptance Criteria:**

**Given** the existing alert rule system (from Epic 3 Story 3.6)
**When** the user creates a custom monitoring rule
**Then** composite conditions are supported: the user can combine multiple conditions with AND/OR logic (e.g., "alert when revenue mean_shift > 15% AND transaction volume_change < -10%")
**And** each condition specifies: metric/column, check type (drift_severity, mean_shift, volume_change, schema_change, completeness_drop, dqa_severity), comparison operator, and threshold
**And** the composite rule evaluates all conditions against each pipeline run and triggers only when the combined logic is satisfied

**Given** a triggered composite rule
**When** the alert is generated
**Then** the alert detail shows which individual conditions were met and which were not
**And** the alert is delivered through configured channels (log, email, and — in Story 7.5 — webhooks)

**Given** a user who wants scheduled digest reports
**When** they configure a digest via the UI
**Then** they can select: frequency (daily, weekly, monthly), sections to include (data quality summary, drift summary, alert summary, key metrics, trend charts), and specific datasets or all datasets
**And** the digest configuration is saved as a scheduled task

**Given** a scheduled digest
**When** the scheduled time arrives
**Then** the system compiles the selected sections from the most recent pipeline outputs
**And** the digest is rendered as a report (docx/PDF) and delivered via email to the user
**And** the digest generation is logged and visible in the user's report history

### Story 7.3: Natural Language Querying

As a user,
I want to ask questions about my data in plain language and receive structured answers with supporting evidence,
So that I can explore my datasets without writing code or knowing query syntax.

**Acceptance Criteria:**

**Given** an authenticated user with at least one uploaded dataset
**When** they type a natural language question in the NL Query input (e.g., "What was our highest revenue month?" or "Show me the trend in customer churn")
**Then** the system sends the question plus the dataset schema (column names, types, sample values) to the LLM
**And** the LLM translates the question into one or more pandas operations
**And** the pandas operations are executed against the user's actual dataset
**And** the results are validated before presentation (NFR8)

**Given** the LLM generates pandas operations
**When** the operations are executed
**Then** the operations are sandboxed — only read operations are allowed (no writes, no deletes, no file system access)
**And** the execution is scoped to the user's own datasets only (tenant-isolated)
**And** if the generated operation raises an error, the system returns a graceful message ("I couldn't answer that question — try rephrasing") rather than exposing the error

**Given** a successful NL query
**When** the results are returned
**Then** the response includes: a direct answer in natural language, the supporting data (table or chart), the pandas operation that was executed (for transparency), and a confidence indicator
**And** all numbers in the answer are derived from the actual dataset — the LLM does not invent values

**Given** a question that cannot be answered from the available data
**When** the LLM determines the query is out of scope
**Then** the system responds with: "This question can't be answered from your current datasets" and suggests what data would be needed

**Given** the NL querying endpoint
**When** implemented
**Then** POST /api/analytics/query accepts {"question": "...", "dataset_id": "..."} and returns the structured answer
**And** backend/services/query_service.py handles LLM interaction, operation generation, execution, and validation
**And** src/components/analytics/NLQueryInput.tsx provides the frontend input and results display

### Story 7.4: Client Self-Service & Report Customization

As a user,
I want to customize my report templates and save configurations for recurring analyses,
So that my reports match my brand and my analysis settings persist across sessions.

**Acceptance Criteria:**

**Given** an authenticated user on the Report Customization page
**When** they configure a report template
**Then** they can customize: section ordering (drag-and-drop or numbered list), which sections to include/exclude (quality findings, insights, anomalies, recommendations, drift analysis), branding elements (company name, logo upload, accent color), and metric selection (which metrics appear in summary)
**And** the template configuration is saved per user in the database

**Given** a saved report template
**When** the user generates a new report
**Then** the renderer applies the custom template: sections appear in the specified order, excluded sections are omitted, branding is applied to headers/footers, and only selected metrics appear in the summary
**And** the user can also generate with the default template if preferred

**Given** recurring analysis patterns
**When** the user saves a configuration (column mapping + thresholds + template + schedule)
**Then** the configuration is persisted as a named "saved analysis" that can be selected for future runs
**And** multiple saved configurations can exist per user
**And** saved configs are listed in a dropdown on the upload/analysis page

**Given** the export API requirement
**When** an Enterprise-tier user wants to integrate with external systems
**Then** GET /api/export/reports returns report data as structured JSON (not just file download)
**And** GET /api/export/insights returns the raw InsightPayload for a given report
**And** these endpoints require API key authentication and are rate-limited per plan tier

### Story 7.5: Versioned REST API & Webhooks

As a developer integrating with SavvyCortex,
I want a versioned REST API with API key authentication, rate limiting, and webhook delivery for alerts,
So that I can programmatically trigger pipelines, retrieve results, and receive real-time alert notifications in my existing tools.

**Acceptance Criteria:**

**Given** the API versioning requirement
**When** Phase 6 API is deployed
**Then** all existing endpoints are accessible under /api/v1/ prefix (e.g., /api/v1/reports, /api/v1/alerts)
**And** unversioned paths (/api/reports) become aliases that redirect or route to /api/v1/
**And** the versioning strategy is URL-prefix based as specified in the Architecture document

**Given** API key authentication
**When** a request includes an API key (Authorization: Bearer svc_live_...)
**Then** the API validates the key by hashing it and comparing against stored token_hash
**And** the key's scopes are checked against the requested action (e.g., write:pipeline required for POST /api/v1/reports/generate)
**And** the key's tenant_id is used for tenant scoping (same isolation as JWT-based access)
**And** rate limiting is applied per API key based on the associated plan tier (Starter: lower limits, Enterprise: higher limits)

**Given** the webhook delivery system
**When** an alert is triggered
**Then** if the tenant has configured webhook endpoints, the alert payload is delivered via POST to each configured URL using httpx async
**And** the webhook payload matches the AlertMessage structure: alert_id, triggered_at, rule, finding, dataset
**And** webhook delivery supports: Slack (formatted payload with blocks), Microsoft Teams (adaptive card format), and custom URLs (raw JSON)
**And** failed webhook deliveries are retried up to 3 times with exponential backoff
**And** delivery status (success/failure/retries) is logged and visible in the alert detail

**Given** the API documentation requirement (FR32)
**When** the versioned API is deployed
**Then** OpenAPI documentation is auto-generated by FastAPI and available at /api/v1/docs (Swagger UI) and /api/v1/openapi.json
**And** the documentation includes: all endpoints with request/response schemas, authentication methods (JWT and API key), rate limit details per plan tier, webhook payload schemas, and example requests/responses
**And** the documentation is accurate and functional (tested against actual endpoints)
