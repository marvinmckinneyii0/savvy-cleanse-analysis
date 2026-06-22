

**SAVVYCORTEX**
Product Roadmap PRD
Phased Delivery  |  Two-Week Sprints  |  Agile Method

Version 1.0  |  April 2026
Classification: Internal — Strategic Planning Document

**Each phase ships a usable increment. Complete one, then begin the next.**

# 1. Executive Summary

SavvyCortex transforms structured data into decision-ready insights, automated reports, and proactive alerts. Built on top of an existing ETL layer, it packages analytical capability into a sellable, demonstrable system.
This roadmap defines six phases of delivery, each scoped to a two-week sprint. Phases are sequential—each one ships a usable increment that builds on the last. No phase begins until its predecessor passes its Definition of Done. This enforces discipline: every two weeks, something works that didn’t before.
Core positioning: “SavvyCortex turns your data into weekly decision reports and alerts—automatically.”

# 2. Operating Model

## 2.1 Sprint Cadence

Each phase maps to a single two-week sprint. The sprint structure follows a consistent pattern across all phases.
- Days 1–2: Architecture and scaffolding. Set up the structures, schemas, and interfaces for the phase.
- Days 3–8: Core implementation. Build the primary deliverables.
- Days 9–10: Integration and testing. Wire components together, run against sample data.
- Days 11–12: Hardening. Edge cases, error handling, logging.
- Days 13–14: Demo preparation and Definition of Done validation. If DoD fails, the sprint extends—the next phase does not start.

## 2.2 Phase Gating

Every phase has a binary Definition of Done checklist. A phase is complete only when every item on the checklist passes. If a phase cannot meet its DoD within the sprint, the sprint is extended (not the scope). Scope is fixed per phase; time is the variable.

## 2.3 Tooling

- Claude Code: Primary implementation tool (filesystem access, BMad method integration).
- Claude.ai: Planning, document generation, architecture decisions.
- BMad Method: Structured development framework. Architect and PM agents for epics/stories.
- GitHub: Version control. Commit after each story completion.

# 3. Roadmap Overview

The six phases below represent the full path from raw data ingestion to a production-grade, client-facing analytics platform. Each phase is self-contained and delivers demonstrable value.

| Phase | Name | Core Deliverable | Sprint | Depends On |
| --- | --- | --- | --- | --- |
| 1 | Foundation | Data Quality Assessment + Insight Engine + Report Generation (docx/pdf) | Weeks 1–2 | — |
| 2 | Automation | Reporting Agent + Monitoring Agent + Alert System | Weeks 3–4 | Phase 1 |
| 3 | Interface | Web UI (upload, configure, view reports, manage alerts) | Weeks 5–6 | Phase 2 |
| 4 | Monetization | Stripe integration + tiered plans + usage tracking | Weeks 7–8 | Phase 3 |
| 5 | Scale | Multi-tenant architecture + async processing + production hardening | Weeks 9–10 | Phase 4 |
| 6 | Intelligence | Advanced analytics + custom agents + client self-service | Weeks 11–12 | Phase 5 |

**PHASE 1**

**Foundation — Data Quality + Insights + Reports**
Sprint 1  |  Weeks 1–2

### Objective

Ship a working pipeline that ingests structured data, assesses its quality, generates insights, and produces a professionally formatted report in docx or PDF. This is the core analytical engine that every subsequent phase builds on.

### Deliverables

- Data Quality Assessment (Stage 0): Automated scan of every ingested file across six detection categories: structural integrity, completeness, consistency, uniqueness, statistical red flags, and referential integrity. Each finding is classified by severity (Critical, High, Medium, Low). Critical findings halt the pipeline with a diagnostic report. Non-critical findings are included as a dedicated section in the final report.
- Insight Engine: Computation layer using pandas for aggregations (sum, avg, growth rate), time-based trend detection, segment comparisons, and basic outlier flagging. Produces a structured JSON object with five sections: data quality findings, summary, key insights, anomalies, and recommendations.
- LLM Narrative Layer: Receives the structured JSON as grounding context and generates natural-language narrative. The LLM summarizes and contextualizes—it does not compute.
- Document Renderer: Shared output module that accepts the insight JSON and produces either docx or PDF based on a format parameter. Reports are professionally formatted with branded styling.

### Pipeline Flow

ETL → Structured Data → Data Quality Assessment → Insight Engine (compute + LLM) → Document Renderer (docx/pdf) → Output. Pipeline halts at DQA stage if critical issues are detected.

### Technical Approach

- Data processing: Python, pandas, basic statistics (no ML).
- Insight generation: Step 1: compute metrics (deterministic). Step 2: structure as JSON. Step 3: pass to LLM for narrative.
- Document output: python-docx for Word documents, reportlab or weasyprint for PDF.

### Definition of Done

- Ingest a dataset and receive a structured data quality assessment JSON
- Pipeline halts with clear diagnostics when critical data issues are detected
- Generate a full insight JSON (quality + summary + insights + anomalies + recommendations)
- Produce a professionally formatted report in both docx and PDF
- Produce a demo-ready output against a sample dataset

### Out of Scope

No scheduled execution, no alerts, no UI, no payment, no multi-tenancy. This phase is the engine only.

**PHASE 2**

**Automation — Reporting Agent + Monitoring Agent**
Sprint 2  |  Weeks 3–4

### Objective

Add automated execution on top of the Phase 1 engine. The system should be able to generate reports on a schedule and detect anomalies proactively without manual intervention.

### Deliverables

- Reporting Agent: A lightweight wrapper that pulls the latest data, invokes the full pipeline (DQA → Insight Engine → Renderer), and outputs a formatted report. Supports both manual trigger (CLI) and scheduled execution (cron or task scheduler). Configurable time interval (daily, weekly, monthly).
- Monitoring Agent: Compares current-period metrics against previous period. Evaluates against configurable thresholds (default: ±15% week-over-week on primary metrics). Emits structured alert messages when thresholds are breached.
- Alert Delivery: V1 delivers alerts via log file output and email (SMTP). No Slack/SMS/webhook integrations yet.
- Configuration Layer: YAML or JSON config file for defining data sources, report schedules, metric thresholds, and alert recipients.

### Technical Approach

- Agents: Simple Python scripts. No complex orchestration frameworks.
- Scheduling: System cron (Linux) or APScheduler (Python) for embedded scheduling.
- Alert thresholds: Percentage change and absolute value comparisons. Configurable per metric.

### Definition of Done

- Run the reporting agent manually and receive a complete report document
- Schedule the reporting agent and confirm it executes on cadence
- Trigger at least one monitoring alert from sample data
- Receive an alert via email delivery
- Modify thresholds via config file and confirm changed behavior

### Out of Scope

No web UI, no user authentication, no payment, no webhook integrations.

**PHASE 3**

**Interface — Web Application**
Sprint 3  |  Weeks 5–6

### Objective

Put a web interface in front of the engine and agents. Users should be able to upload data, configure analysis parameters, view reports, and manage alerts through a browser—no CLI required.

### Deliverables

- Data Upload: Drag-and-drop file upload (CSV initially). File validation feedback before processing begins.
- Configuration UI: Form-based setup for key fields (date column, metric columns, category columns), report frequency, and alert thresholds.
- Report Viewer: Display generated reports in-browser with download option (docx/pdf). Report history with timestamps.
- Alert Dashboard: View active alerts, alert history, and current threshold configuration. Acknowledge/dismiss alerts.
- Authentication: Basic user authentication (email/password). Single-user initially, multi-user readiness in schema.

### Technical Approach

- Frontend: React (or Next.js) with clean, functional UI. No over-engineering—forms, tables, and status indicators.
- Backend API: FastAPI (Python) wrapping the existing engine and agent modules. RESTful endpoints.
- Database: PostgreSQL for user data, report metadata, alert history, and configuration. File storage for uploaded datasets and generated reports.

### Definition of Done

- Upload a CSV through the browser and receive a generated report
- Configure analysis parameters through the UI
- View a report in-browser and download as docx or PDF
- View alert history and current threshold settings
- Log in with email/password and access only own data

### Out of Scope

No payment integration, no multi-tenant isolation, no team/org features.

**PHASE 4**

**Monetization — Stripe + Tiered Plans**
Sprint 4  |  Weeks 7–8

### Objective

Make SavvyCortex a paid product. Integrate Stripe for subscription billing, define tiered plans with usage limits, and gate features accordingly.

### Deliverables

- Stripe Integration: Subscription checkout, billing portal, webhook handling for payment events (subscription created, payment failed, cancellation).
- Plan Tiers: Three tiers scoped by usage limits. Starter: limited reports per month, basic thresholds, email alerts only. Professional: higher report limits, custom thresholds, priority processing. Enterprise: unlimited reports, API access, dedicated support channel, custom branding on reports.
- Usage Tracking: Track report generation count, data volume processed, and alert volume per billing period. Enforce limits at the API layer.
- Billing UI: Plan selection, upgrade/downgrade flow, invoice history, payment method management (all via Stripe’s hosted portal where possible).
- Trial Period: 14-day free trial on Professional tier. No credit card required for trial start.

### Technical Approach

- Stripe SDK: stripe-python for backend integration. Stripe Checkout for payment flow. Stripe Customer Portal for billing management.
- Webhook handling: Endpoint for Stripe webhook events. Idempotent processing. Signature verification.
- Feature gating: Middleware layer that checks subscription status and usage counts before allowing API calls.

### Definition of Done

- New user can sign up, select a plan, and complete payment via Stripe
- Usage limits enforced—user hitting report cap receives clear feedback
- Subscription lifecycle works: create, upgrade, downgrade, cancel
- Failed payments handled gracefully (grace period, user notification)
- 14-day trial functions without credit card

### Out of Scope

No annual billing, no custom enterprise contracts, no usage-based pricing (per-report). Fixed tiers only.

**PHASE 5**

**Scale — Multi-Tenancy + Production Hardening**
Sprint 5  |  Weeks 9–10

### Objective

Prepare SavvyCortex for real production load. Isolate tenant data, handle concurrent processing, and ensure the system is reliable, observable, and secure.

### Deliverables

- Multi-Tenant Data Isolation: Row-level security in PostgreSQL. Every query scoped to the authenticated tenant. File storage partitioned by tenant ID.
- Async Processing: Report generation and monitoring jobs run asynchronously via a task queue (Celery + Redis or equivalent). Users receive status updates rather than waiting on synchronous responses.
- Observability: Structured logging (JSON format). Error tracking (Sentry or equivalent). Basic metrics dashboard for system health (queue depth, job success/failure rates, response times).
- Security Hardening: Input sanitization on all upload paths. Rate limiting on API endpoints. HTTPS enforcement. Secrets management (no hardcoded keys). OWASP top-10 review.
- Infrastructure: Containerized deployment (Docker). CI/CD pipeline. Staging environment that mirrors production.

### Technical Approach

- Task queue: Celery with Redis broker for async job processing. Dead letter queue for failed jobs.
- Deployment: Docker Compose for local/staging. Cloud deployment target (AWS ECS, GCP Cloud Run, or equivalent).
- Database: PostgreSQL with row-level security policies. Connection pooling. Automated backups.

### Definition of Done

- Two separate tenants cannot access each other’s data under any circumstance
- Report generation runs asynchronously with status polling
- System handles 10 concurrent report generation jobs without degradation
- All errors are captured in structured logs with correlation IDs
- Deployment is automated via CI/CD from a single branch merge
- Security review completed against OWASP top-10

### Out of Scope

No auto-scaling, no multi-region deployment, no SOC 2 compliance (yet). Focus is on functional isolation and reliability.

**PHASE 6**

**Intelligence — Advanced Analytics + Self-Service**
Sprint 6  |  Weeks 11–12

### Objective

Elevate the analytical capability beyond basic statistics and make the platform self-service for clients. This is where SavvyCortex transitions from a reporting tool to an intelligence platform.

### Deliverables

- Advanced Analytics: Forecasting (simple time-series projection using Prophet or statsmodels). Correlation detection across metrics. Cohort analysis for segmented datasets. Comparative analysis (period-over-period with statistical significance testing).
- Custom Agents: User-defined monitoring rules beyond threshold alerts. Composite conditions (e.g., “alert when metric A drops AND metric B rises”). Scheduled digest reports with custom section selection.
- Natural Language Querying: Users ask questions about their data in plain language. The system translates to analytical operations and returns structured answers with supporting evidence. Scoped to the user’s uploaded datasets.
- Client Self-Service: Report template customization (section ordering, branding, metric selection). Saved configurations for recurring analyses. Export API for integration with client systems.
- API Access: RESTful API with authentication for programmatic access. Webhook endpoints for alert delivery to external systems (Slack, Teams, custom).

### Technical Approach

- Forecasting: Prophet or statsmodels for time-series projection. No deep learning.
- NL Querying: LLM translates natural language to pandas operations against the user’s dataset. Results are validated before presentation.
- API: Versioned REST API (v1). API key authentication. Rate limiting per plan tier.

### Definition of Done

- Generate a 30-day forecast from historical data and include in report
- User creates a custom composite monitoring rule and receives an alert
- User asks a natural language question and receives an accurate, evidence-backed answer
- User customizes report template and generates a branded report
- External system receives an alert via webhook
- API documentation published and functional

### Out of Scope

No real-time streaming analytics, no ML model training by users, no white-label reselling infrastructure.

# 4. Risk Register

| Risk | Phase Affected | Mitigation | Severity |
| --- | --- | --- | --- |
| Insights feel generic or shallow | Phase 1 | Ground LLM output in computed statistics. Never let the LLM generate numbers independently. Include raw metrics alongside narrative. | High |
| Overbuilding agents / premature orchestration | Phase 2 | Agents are thin wrappers around the Insight Engine. No orchestration frameworks until Phase 5 at earliest. | Medium |
| UI becomes scope sink | Phase 3 | Functional UI only. No design system, no animations, no mobile optimization. Ship forms and tables. | High |
| Stripe integration complexity | Phase 4 | Use Stripe Checkout and Customer Portal (hosted). Minimize custom billing UI. Lean on Stripe’s tested flows. | Medium |
| Multi-tenancy data leaks | Phase 5 | Row-level security enforced at database level, not application level. Penetration testing before launch. | Critical |
| NL query hallucination | Phase 6 | LLM generates pandas operations, not answers. Results are computed from actual data. Confidence scoring on responses. | High |

# 5. Global Non-Goals

The following items are explicitly out of scope for the entire roadmap as defined. They may be considered in future planning cycles but are not part of the current six-phase plan.
- Real-time streaming analytics or event processing
- Autonomous decision execution (system recommends, humans decide)
- Deep ML model training or custom model deployment by end users
- White-label reselling or multi-brand infrastructure
- Mobile-native applications (responsive web only)
- SOC 2 or HIPAA compliance certification (security hardening is in scope; formal certification is not)
- Multi-region or geo-distributed deployment
- Data warehousing or data lake functionality (SavvyCortex consumes structured data; it does not store raw data long-term)

# 6. Success Metrics

These metrics are evaluated at the completion of each phase to determine whether the product is on track for market viability.
- Phase 1: Can generate a demo-ready report from any well-structured CSV within 60 seconds.
- Phase 2: Automated reports run on schedule with zero manual intervention for at least 7 consecutive days.
- Phase 3: A non-technical user can upload data and receive a report without reading documentation.
- Phase 4: At least one paying customer completes a subscription within 30 days of launch.
- Phase 5: System sustains 10 concurrent tenants with zero data cross-contamination.
- Phase 6: Users engage with NL querying at least 3 times per session on average.

This is a living document. It is updated at the end of each phase based on learnings from the completed sprint. Scope within a phase is fixed; scope of future phases adapts.