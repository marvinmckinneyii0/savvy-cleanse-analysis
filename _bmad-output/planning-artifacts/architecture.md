---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/research/technical-insights-agents-layer-research-2026-04-09.md'
workflowType: 'architecture'
project_name: 'SavvyCortex'
user_name: 'Marvin'
date: '2026-04-12'
lastStep: 8
status: 'complete'
completedAt: '2026-04-13'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements (32 across 6 phases):**

| Phase | FR Count | Key Capabilities |
|-------|----------|-----------------|
| 1 — Foundation | 5 | Data quality assessment (6 categories), insight engine (aggregations, trends, outliers), LLM narrative generation, document rendering (docx/PDF), halt-on-critical pipeline logic |
| 2 — Automation | 5 | Reporting agent (manual + scheduled), monitoring agent (period-over-period comparison), configurable thresholds (±15% default), email alert delivery (SMTP), YAML/JSON config layer |
| 3 — Interface | 5 | File upload (CSV), configuration UI (columns, frequency, thresholds), in-browser report viewer + download, alert dashboard (active/history/acknowledge), email/password authentication |
| 4 — Monetization | 5 | Stripe subscription checkout + billing portal, 3-tier plans (Starter/Professional/Enterprise), usage tracking + limit enforcement, billing UI (upgrade/downgrade/invoices), 14-day free trial (no CC) |
| 5 — Scale | 6 | Row-level security (PostgreSQL), tenant-scoped queries + file storage, async task queue (Celery + Redis), structured logging + error tracking (Sentry), OWASP security hardening, Docker + CI/CD |
| 6 — Intelligence | 6 | Time-series forecasting (Prophet/statsmodels), correlation + cohort + comparative analysis, composite monitoring rules, NL querying (LLM → pandas), report template customization, versioned REST API + webhooks |

**Non-Functional Requirements:**

- **Performance:** Report generation <60s from CSV; 10 concurrent jobs without degradation
- **Security:** No hardcoded credentials; input sanitization; rate limiting; HTTPS; OWASP top-10 review; secrets management
- **Data Integrity:** LLM never computes independently (grounding pattern); NL query results validated before presentation
- **Reliability:** Pipeline halt-on-critical; async job dead letter queue; structured logging with correlation IDs
- **Scalability:** Multi-tenant RLS; connection pooling; automated backups; containerized deployment
- **Compliance:** Data isolation ("two tenants cannot access each other's data under any circumstance")

**Scale & Complexity:**

- Primary domain: Full-stack (Python backend + React frontend + PostgreSQL + LLM + Stripe)
- Complexity level: High
- Estimated architectural components: 18–22 (pipeline stages, agents, renderers, API layer, auth, billing, async workers, monitoring)

### Technical Constraints & Dependencies

- **Existing codebase:** React 18 + Vite + ShadCN/ui frontend; FastAPI backend with advanced_pipeline.py, comprehensive_analytics.py, nlp_processor.py — all require adaptation, not replacement
- **Phase 3 already built:** Dashboard serves mock data; 2 different Supabase project URLs; in-memory DATA_STORAGE dict; frontend has 15 pages (most marketing/static)
- **Agent philosophy:** "Simple Python scripts. No complex orchestration frameworks." Agents built from scratch, non-agentic infrastructure.
- **LLM constraint:** Claude API Structured Outputs for guaranteed-schema narrative generation; LLM grounding pattern (stats-in → narrative-out)
- **Tech debt (CLI-affecting):** 14 items, ~4.5 hours total — 6 must-fix items on Day 1 of Phase 1 (~1.5 hours)
- **PRD authority:** PRD defines end goals; architecture defines implementation approach

### Cross-Cutting Concerns Identified

1. **Authentication & Authorization** — Evolves across phases: none (Phase 1-2 CLI) → single-user email/password (Phase 3) → multi-tenant RLS (Phase 5) → API key auth per plan tier (Phase 6)
2. **Error Handling** — Dual strategy: Result pattern (PipelineResult) for expected business outcomes; custom exception hierarchy (SavvyCleanseError tree) for unexpected failures; ExceptionGroup for collecting multiple quality defects
3. **Structured Logging** — Replace warnings.filterwarnings('ignore') with structlog JSON; correlation IDs for request tracing; Sentry integration (Phase 5)
4. **Secrets Management** — Hardcoded Supabase credentials in main_enhanced.py and client.ts flagged as urgent; must move to environment variables before any deployment
5. **LLM Resilience** — Retry with exponential backoff; provider fallback chain (Claude → OpenAI → Gemini); circuit breaker after 3 consecutive failures
6. **Configuration** — YAML/JSON config for thresholds, schedules, data sources (Phase 2); extends to plan-tier feature flags (Phase 4) and custom agent rules (Phase 6)

## Starter Template Evaluation

### Primary Technology Domain

Full-stack web application with CLI pipeline — brownfield project with existing React + FastAPI codebase providing component-level reuse, not architectural reuse.

### Foundation Assessment (First Principles)

The existing codebase is a **prototype/MVP**, not an architectural foundation. It validated the UI shell and basic data flow but lacks the structural underpinnings SavvyCortex requires.

**What the codebase provides (component reuse):**
- React + ShadCN dashboard shell (Card, Table, Chart, Form, Dialog, etc.) — UI components reusable in Phase 3
- FastAPI server skeleton — reuse framework, replace endpoints
- Analytics reference implementations (DescriptiveAnalytics, DiagnosticAnalytics, etc.) — adapt after debt remediation. Reuse ratings: 35-55% post-fix. These are reference material for rebuilding, not drop-in modules.
- cleaner.py — 95% reusable as-is (only needs factory refactor for testability)

**What must be built new (architectural scaffolding):**
- Backend package structure: pipeline/, models/, agents/, renderers/
- Pydantic contracts at pipeline stage boundaries
- CLI entry points (Typer) for Phases 1-2
- Test infrastructure (pytest + vitest) — zero tests exist today
- Persistent data layer replacing in-memory DATA_STORAGE dict
- Unified auth (two conflicting Supabase configs must be reconciled)
- Structured logging (structlog), error handling hierarchy, configuration layer
- Report rendering pipeline (docxtpl + PDF conversion)
- Drift Engine (stateless computation module for distributional shift detection)

### Phase 3 Complexity Acknowledgment

Phase 3 is **significant integration**, not light wiring. The existing web app serves mock data for a different product identity ("SavvyClean"). Phase 3 requires: unifying two Supabase projects, replacing DATA_STORAGE with PostgreSQL persistence, rewriting all dashboard API endpoints against real pipeline output, re-wiring frontend components to new response shapes, building end-to-end auth, adding report/upload file storage, and rebranding to SavvyCortex.

### Selected Foundation: Hybrid — New Architecture Incorporating Existing Components

**Rationale:**
The existing codebase provides reusable UI components and reference implementations but not a reusable architecture. Phase 1 builds the new package structure from scratch, cherry-picking analytics logic and adapting it. Phase 3 integrates the existing React dashboard with the new backend — a substantial effort that goes beyond connecting wires.

**Foundation Strategy: In-Place Evolution with Test-First Setup**

The existing backend directory is extended with new sub-packages. Existing flat modules stay in place — they are not moved, renamed, or deleted. New code is built in the new directories. This eliminates restructuring risk while achieving proper organization.

**Phase 1 First Commit (before any production code):**
1. Create `backend/pipeline/`, `backend/models/`, `backend/agents/`, `backend/renderers/`, `backend/baselines/`, `backend/tests/`
2. Create `pyproject.toml` with pytest configuration
3. Create `tests/conftest.py` with shared DataFrame fixtures
4. Fix the 6 Day-1 tech debt items (~1.5 hours)
5. Then build `pipeline/data_quality.py` with tests alongside — test pyramid exists before the first pipeline stage

**Legacy Module Labeling:**
Existing flat modules (`advanced_pipeline.py`, `comprehensive_analytics.py`, `nlp_processor.py`, `main.py`, `dashboard_api.py`) receive a status header comment:

```python
# STATUS: Legacy reference implementation
# This module is NOT part of the SavvyCortex pipeline.
# Reusable logic has been extracted into pipeline/ and models/.
# Retained for web API compatibility until Phase 3 integration.
```

### Architectural Decisions Already Established by Codebase

**Language & Runtime:**
- Backend: Python 3.13 (FastAPI, pandas, scikit-learn)
- Frontend: TypeScript 5.5 (React 18, strict mode)

**Styling Solution:**
- Tailwind CSS 3.4 + ShadCN/ui component library
- PostCSS pipeline, dark/light theme support via next-themes

**Build Tooling:**
- Frontend: Vite 5.4 with React SWC compiler
- Backend: Uvicorn ASGI server, pip for dependency management

**Testing Framework:**
- None currently — test pyramid built starting Phase 1
- Planned: pytest (backend), vitest (frontend)

### Code Organization (Target State)

```
backend/
├── pipeline/              # NEW — core analytical engine
│   ├── orchestrator.py    # run_full_pipeline() composer
│   ├── data_quality.py    # Stage 0: DataQualityAssessor
│   ├── drift_engine.py    # Stage 0b: stateless drift computation
│   ├── insight_engine.py  # Stage 2: wraps analytics classes
│   ├── narrative_generator.py  # Stage 3: Claude Structured Outputs
│   └── config.py          # PipelineConfig dataclass
├── models/                # NEW — Pydantic contracts
│   ├── quality_report.py
│   ├── drift_report.py    # DriftReport, DriftFinding, BaselineProfile
│   ├── insight_payload.py
│   ├── insight_report.py
│   └── pipeline_config.py
├── agents/                # NEW — thin Python wrappers (Typer CLI)
│   ├── reporting_agent.py
│   └── monitoring_agent.py
├── renderers/             # NEW — document output
│   ├── docx_renderer.py
│   ├── pdf_renderer.py
│   └── templates/
├── baselines/             # NEW — baseline profile storage (JSON Phase 2, PostgreSQL Phase 5)
├── tests/                 # NEW — test pyramid
│   ├── conftest.py
│   ├── test_data_quality.py
│   ├── test_drift_engine.py
│   ├── test_insight_engine.py
│   ├── test_narrative_generator.py
│   ├── test_renderers.py
│   └── test_monitoring_agent.py
├── advanced_pipeline.py        # LEGACY — reference implementation
├── comprehensive_analytics.py  # LEGACY — reference implementation
├── nlp_processor.py            # LEGACY — reference implementation
├── cleaner.py                  # EXISTING — reuse as-is (factory refactor only)
├── main.py                     # EXISTING — retain for web API
├── dashboard_api.py            # EXISTING — rewrite endpoints in Phase 3
└── requirements.txt            # UPDATED per phase
```

### Pipeline Stage Inventory

| Stage | Module | Phase | Role |
|-------|--------|-------|------|
| Data Quality Assessment | pipeline/data_quality.py | 1 | Scan 6 categories, classify severity, halt on critical |
| Drift Engine | pipeline/drift_engine.py | 2 | Stateless: 2 DataFrames in → drift JSON out. 7 checks. Informational only — never halts pipeline |
| Insight Engine | pipeline/insight_engine.py | 1 | Aggregations, trends, outliers → structured JSON. Receives drift data as optional parameter |
| Narrative Generator | pipeline/narrative_generator.py | 1 | Claude Structured Outputs; grounded in computed stats + drift context |
| Document Renderer | renderers/docx_renderer.py, pdf_renderer.py | 1 | docxtpl → docx; WeasyPrint or LibreOffice → PDF |

### Agent Inventory (2 agents, plain Python + Typer CLI)

| Agent | Phase | Purpose |
|-------|-------|---------|
| Reporting Agent | 2 | Pulls latest data, invokes full pipeline (DQA → Drift Engine → Insight Engine → Renderer), outputs formatted report. When drift data exists, report includes Drift Analysis section. Manual trigger (CLI) + scheduled execution. |
| Monitoring Agent | 2 | Compares current-period metrics against previous period. Evaluates configurable thresholds (±15% default). Consumes Drift Engine JSON for drift-based alert rules (e.g., `type: mean_shift, column: revenue, threshold: 0.15`). Emits structured alerts via log file and email (SMTP). |

### Drift Engine Specification (pipeline/drift_engine.py)

Stateless computation module. Takes two DataFrames (current + baseline), runs 7 detection checks, returns Pydantic-validated JSON. No side effects — doesn't send alerts, doesn't run on schedule, doesn't decide whether a change matters.

**Baseline management:** Statistical profile per column (mean, median, std, quartiles, null%, categorical distributions, schema fingerprint). Stored as JSON files (Phase 2) → PostgreSQL (Phase 5). On first run: establish baseline, skip drift, continue pipeline. Auto-rotates after 4 consecutive clean runs.

**7 detection checks:**

| Check | Formula | HIGH | MEDIUM | LOW |
|-------|---------|------|--------|-----|
| Mean shift | `(curr_mean - base_mean) / base_mean` | >30% | >15% | >5% |
| Median shift | Same formula on medians | >30% | >15% | >5% |
| Variance shift | `curr_std / base_std` | >2.0 or <0.5 | >1.5 or <0.67 | — |
| Volume drift | `(len(curr) - len(base)) / len(base)` | >50% | >20% | >10% |
| Categorical PSI | `Σ (curr% - base%) × ln(curr% / base%)` | >0.25 | 0.10–0.25 | <0.10 |
| New/missing categories | Set comparison + representation % | Missing >10% repr | New >5% repr | — |
| Schema drift | Column set + dtype comparison | Always HIGH | — | — |

**Output:** Single JSON object with sections: volume_drift, numeric_drift, categorical_drift, schema_drift, drift_summary, overall_severity, recommendations. Validated by Pydantic before return.

**Integration:** Monitoring Agent consumes drift JSON for alert rules. Reporting Agent includes Drift Analysis section in reports. Insight Engine receives drift data as optional parameter for contextualized insights (trend acceleration, drift-anomaly correlation, baseline deviation narratives).

**What it is not:** Not a gate (never halts pipeline). Not predictive. Not self-healing. Not statistically sophisticated in Phase 2 (no KS tests, no multivariate drift, no adaptive thresholds — those are future enhancements).

### New Dependencies Per Phase

| Phase | Backend Additions | Frontend Additions |
|-------|------------------|--------------------|
| 1 | pandera, docxtpl, typer, structlog, pydantic, pytest | vitest |
| 2 | APScheduler (or system cron), smtplib (stdlib), scipy.stats (PSI computation) | — |
| 3 | — (extend existing FastAPI) | — (extend existing React) |
| 4 | stripe | @stripe/stripe-js, @stripe/react-stripe-js |
| 5 | celery, redis, sentry-sdk, docker | — |
| 6 | prophet or statsmodels | — |

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Database strategy: Supabase (unified) through Phase 4, standalone PostgreSQL Phase 5
- Auth: Supabase Auth (unified frontend + backend to one project)
- LLM integration: Direct Anthropic SDK with structured outputs (no frameworks)
- Data validation: Pandera (DataFrame) + Pydantic v2 (pipeline contracts)
- Pipeline architecture: Pipes-and-Filters with typed stage boundaries

**Important Decisions (Shape Architecture):**
- Task queue: Celery 5.6.3 + Redis (Phase 5)
- PDF generation: WeasyPrint 68.1
- Error response format: RFC 7807 Problem Details
- CI/CD: GitHub Actions
- Secrets management: .env files → Docker secrets

**Deferred Decisions (Post-MVP / Phase 5+):**
- Cloud provider selection (AWS ECS vs GCP Cloud Run)
- Standalone PostgreSQL migration details
- Sentry configuration and alert policies
- Auto-scaling strategy

### Data Architecture

| Decision | Choice | Version | Rationale | Affects |
|----------|--------|---------|-----------|---------|
| Database | Supabase (unified) → standalone PostgreSQL | Supabase latest / PostgreSQL 16 | Supabase provides auth + db + file storage. Unify two existing configs to one project. Phase 5 migrates to standalone for RLS control. | All phases |
| ORM | SQLAlchemy 2.0 | 2.0.x | Already a dependency. Async support with asyncpg. Alembic for migrations. | Phase 3+ |
| DataFrame Validation | Pandera | 0.30.1 | Lightweight, pytest-integrated. Validates data content (nulls, types, ranges). | Phase 1+ |
| Contract Validation | Pydantic | v2 (bundled with FastAPI) | Validates data shapes between pipeline stages. Structured outputs from Claude API. | Phase 1+ |
| Migration Tool | Alembic | Latest | SQLAlchemy companion. Auto-generates from model changes. | Phase 3+ |
| Baseline Storage | JSON files → PostgreSQL | N/A | Drift Engine baselines are small statistical profiles. JSON for CLI phase, PostgreSQL table in Phase 5. Same interface, swap backend. | Phase 2+ |
| File Storage | Local → Supabase Storage → S3-compatible | N/A | Reports and uploads need persistence. Local for CLI. Supabase Storage for web. S3-compatible for multi-tenant partitioning. | Phase 1→3→5 |

### Authentication & Security

| Decision | Choice | Version | Rationale | Affects |
|----------|--------|---------|-----------|---------|
| Auth Provider | Supabase Auth | Latest | Already in frontend. Email/password, JWT tokens, RLS policies. Unify frontend + backend to same Supabase project. | Phase 3+ |
| Backend Auth | Supabase JWT verification | via supabase-py | Eliminates split between frontend (Supabase Auth) and backend (python-jose). One auth system. | Phase 3+ |
| Rate Limiting | slowapi | Latest | FastAPI-native rate limiter. No rate limiting Phase 1-2 (CLI only). | Phase 3+ |
| Secrets Management | python-dotenv → Docker secrets | Latest | .env files for development. Docker/cloud secrets for production. Immediate: rotate hardcoded Supabase credentials. | Phase 1→5 |
| Input Sanitization | FastAPI validation + Pydantic | Built-in | Pydantic enforces types. File upload validation added Phase 3. OWASP review Phase 5. | Phase 3→5 |

### API & Communication Patterns

| Decision | Choice | Version | Rationale | Affects |
|----------|--------|---------|-----------|---------|
| API Style | REST | FastAPI native | PRD specifies RESTful. FastAPI excels at REST. Versioned API (v1) in Phase 6. | Phase 3+ |
| API Documentation | OpenAPI (auto-generated) | Built-in | Free with FastAPI. Swagger UI at /docs. Phase 6 publishes versioned docs. | Phase 3+ |
| Error Response Format | RFC 7807 Problem Details | Standard | `{"type": "...", "title": "...", "status": 422, "detail": "..."}`. Consistent across all endpoints. | Phase 3+ |
| LLM Integration | Direct Anthropic SDK | 0.79.0 | `client.messages.parse()` with Pydantic models. Structured outputs GA. No LangChain, no abstraction layers. Provider fallback: Claude → OpenAI → Gemini. | Phase 1+ |
| Email Delivery | smtplib → Resend/SendGrid | stdlib → Phase 4+ | CLI phase uses direct SMTP. Production needs delivery tracking and templates. | Phase 2→4 |
| Webhook Delivery | httpx async | Latest | Phase 6 webhook endpoints for external system alerts (Slack, Teams, custom). | Phase 6 |

### Frontend Architecture

| Decision | Choice | Version | Rationale | Affects |
|----------|--------|---------|-----------|---------|
| State Management | TanStack Query (React Query) | 5.x (installed) | Already in use. Excellent for server state. No client-side store needed until Phase 6 complex state. | Phase 3+ |
| Form Handling | React Hook Form + Zod | Installed | Already configured. Phase 3 config UI, Phase 4 billing forms. | Phase 3+ |
| Report Viewing | Download-first + iframe preview | N/A | Phase 1-2: CLI file output. Phase 3: download links + optional PDF iframe. Don't over-engineer. | Phase 3+ |
| Real-time Updates | Polling → SSE | N/A | Polling for Phase 3-4 report status. Server-Sent Events in Phase 5 for async job streaming. | Phase 3→5 |
| Component Library | ShadCN/ui | Installed (87 components) | Already in project. Use dashboard-relevant subset. Add components as needed. | Phase 3+ |

### Infrastructure & Deployment

| Decision | Choice | Version | Rationale | Affects |
|----------|--------|---------|-----------|---------|
| Containerization | Docker Compose | Latest | PRD specifies Docker. Compose for local/staging. Cloud (ECS/Cloud Run) for production. No K8s. | Phase 5 |
| CI/CD | GitHub Actions | N/A | Repo on GitHub. Native integration. Free tier sufficient. | Phase 5 |
| Task Queue | Celery + Redis | 5.6.3 | PRD specifies Celery + Redis. Memory leak fixes in 5.6.3. Dead letter queue. | Phase 5 |
| Error Tracking | Sentry | Latest | Industry standard. Python + React SDKs. Free tier for small scale. | Phase 5 |
| PDF Generation | WeasyPrint | 68.1 | HTML/CSS → PDF. No system dependency like LibreOffice. Security patch in v68. | Phase 1 |
| Monitoring | structlog + Sentry | structlog 25.5.0 | JSON structured logging from Phase 1. Sentry integration Phase 5. Correlation IDs for request tracing. | Phase 1→5 |

### Decision Impact Analysis

**Implementation Sequence (decisions in order of when they matter):**
1. Pydantic v2 + Pandera 0.30.1 + structlog 25.5.0 (Phase 1, Day 1)
2. Anthropic SDK 0.79.0 structured outputs (Phase 1, narrative generator)
3. docxtpl 0.20.2 + WeasyPrint 68.1 (Phase 1, document renderer)
4. Typer 0.12.1 + smtplib + APScheduler (Phase 2, agents)
5. scipy.stats for PSI computation (Phase 2, drift engine)
6. Supabase Auth unification + SQLAlchemy/Alembic (Phase 3)
7. slowapi rate limiting (Phase 3)
8. stripe-python 15.0.0 (Phase 4)
9. Celery 5.6.3 + Redis + Sentry + Docker (Phase 5)
10. Prophet or statsmodels (Phase 6)

**Cross-Component Dependencies:**
- Pydantic v2 is the universal contract language — used by FastAPI, pipeline stages, Claude structured outputs, and Drift Engine output
- Supabase unification (Phase 3) is prerequisite for auth, file storage, and database access from both frontend and backend
- structlog (Phase 1) provides the logging foundation that Sentry (Phase 5) enriches with error tracking
- SQLAlchemy models (Phase 3) must be designed with Phase 5 RLS in mind — add tenant_id columns from the start even if RLS isn't enforced until Phase 5

### Verified Technology Versions

| Technology | Version | Source |
|-----------|---------|--------|
| Pandera | 0.30.1 | [PyPI](https://pypi.org/project/pandera/) |
| docxtpl | 0.20.2 | [PyPI](https://pypi.org/project/docxtpl/) |
| Typer | 0.12.1+ | [PyPI](https://pypi.org/project/typer/) |
| structlog | 25.5.0 | [PyPI](https://pypi.org/project/structlog/) |
| WeasyPrint | 68.1 | [PyPI](https://pypi.org/project/weasyprint/) |
| Celery | 5.6.3 | [PyPI](https://pypi.org/project/celery/) |
| stripe-python | 15.0.0 | [PyPI](https://pypi.org/project/stripe/) |
| Anthropic SDK | 0.79.0 | [GitHub](https://github.com/anthropics/anthropic-sdk-python) |

## Implementation Patterns & Consistency Rules

### Critical Conflict Points Identified

18 areas where AI agents could make different choices if not specified. The patterns below resolve each one.

### Naming Patterns

**Database Naming (PostgreSQL via SQLAlchemy):**
- Tables: **plural snake_case** — `users`, `reports`, `alert_thresholds`, `drift_baselines`
- Columns: **snake_case** — `created_at`, `tenant_id`, `report_count`
- Foreign keys: **{referenced_table_singular}_id** — `user_id`, `report_id`
- Indexes: **ix_{table}_{column}** — `ix_reports_created_at`
- Constraints: **{table}_{type}_{column}** — `users_uq_email`, `reports_fk_user_id`
- All tables include: `id` (UUID primary key), `created_at`, `updated_at`, `tenant_id` (nullable until Phase 5 RLS)

**API Naming (FastAPI REST):**
- Endpoints: **plural nouns, snake_case** — `/api/v1/reports`, `/api/v1/alert_thresholds`
- Route parameters: **`{report_id}`** (curly braces, snake_case)
- Query parameters: **snake_case** — `?start_date=2026-01-01&page_size=20`
- Versioning: **URL prefix** — `/api/v1/...` starting Phase 6, unversioned before
- HTTP methods: GET (read), POST (create), PUT (full update), PATCH (partial), DELETE

**Python Code Naming:**
- Modules: **snake_case** — `data_quality.py`, `drift_engine.py`
- Classes: **PascalCase** — `DataQualityAssessor`, `DriftReport`, `PipelineResult`
- Functions: **snake_case** — `assess_quality()`, `compute_drift()`, `generate_narrative()`
- Constants: **UPPER_SNAKE** — `DEFAULT_THRESHOLD`, `MAX_RETRIES`
- Private: **single underscore prefix** — `_parse_response()`, `_validate_schema()`
- Pydantic models: **PascalCase, noun-based** — `QualityReport`, `InsightPayload`, `DriftFinding`

**TypeScript/React Naming:**
- Components: **PascalCase files and exports** — `ReportViewer.tsx`, `AlertDashboard.tsx`
- Hooks: **camelCase with `use` prefix** — `useReportData()`, `useAlertHistory()`
- Utilities: **camelCase** — `formatDate()`, `parseApiError()`
- Types/Interfaces: **PascalCase** — `Report`, `AlertThreshold`, `ApiError`
- API response fields: **camelCase** (frontend transforms from backend snake_case)

### Structure Patterns

**Backend Test Organization:**
- Tests live in `backend/tests/` (not co-located)
- Mirror source structure: `tests/test_data_quality.py` tests `pipeline/data_quality.py`
- Naming: `test_{module}.py`, functions `test_{behavior}()`
- Fixtures in `conftest.py` — shared DataFrame fixtures, mock LLM responses
- Integration tests in `tests/integration/` — stage-to-stage wiring
- E2E tests in `tests/e2e/` — CLI invocation with real CSV

**Frontend Test Organization:**
- Co-located: `ReportViewer.test.tsx` next to `ReportViewer.tsx`
- Vitest + React Testing Library

**Configuration Files:**
- Pipeline config: `backend/pipeline/config.py` (PipelineConfig dataclass)
- User-facing config: `config.yaml` or `config.json` at project root (Phase 2 thresholds, schedules)
- Environment: `.env` at project root, `.env.example` committed (no secrets)
- Deployment: `docker-compose.yml` at project root (Phase 5)

### Format Patterns

**API Response Format (all endpoints):**

Success:
```json
{
  "data": { "..." : "..." },
  "meta": { "requestId": "uuid", "timestamp": "2026-04-12T10:30:00Z" }
}
```

Error (RFC 7807):
```json
{
  "type": "https://savvycortex.com/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "Column 'revenue' contains 65% null values, exceeding critical threshold",
  "instance": "/api/v1/reports/generate"
}
```

**Pipeline Stage Output Format (internal):**
Every pipeline stage returns a Pydantic model. No raw dicts between stages.
```python
# Good
def assess_quality(df: pd.DataFrame) -> DataQualityReport: ...
def compute_drift(current: pd.DataFrame, baseline: BaselineProfile) -> DriftReport: ...

# Bad — never return raw dicts
def assess_quality(df: pd.DataFrame) -> dict: ...
```

**Date/Time Format:**
- JSON/API: **ISO 8601 UTC** — `"2026-04-12T10:30:00Z"`
- Database: **timestamptz** (PostgreSQL)
- Display: Frontend formats to user's locale
- Config files: **ISO 8601** — `"2026-04-12"`

**JSON Field Naming:**
- Backend (Python to Database): **snake_case** — `created_at`, `report_count`
- API responses: **snake_case** (FastAPI default from Pydantic)
- Frontend internal: **camelCase** — transform at API boundary

**Null Handling:**
- JSON: explicit `null` (never omit nullable fields)
- Python: `Optional[T]` with explicit `None`
- TypeScript: `T | null` (not `T | undefined`)
- DataFrame: preserve NaN; sanitize to `null` before JSON serialization

### Communication Patterns

**Logging (structlog):**
- Format: JSON structured — `{"event": "stage_completed", "stage": "data_quality", "rows": 1500, "defects": 3}`
- Levels: `debug` (internal detail), `info` (stage transitions), `warning` (non-critical findings), `error` (failures), `critical` (pipeline halt)
- Every log entry includes: `event` (what happened), `stage` (which pipeline stage), context-specific fields
- Correlation: `pipeline_run_id` (UUID) propagated through all stages of a single run
- **Never log:** API keys, raw data values, PII, file paths containing usernames

**Pipeline Events (internal):**
- Naming: **snake_case verb_noun** — `quality_assessed`, `drift_computed`, `narrative_generated`, `report_rendered`
- Not a pub/sub system — direct function calls with structured returns. "Events" are log entries, not messages.

**Alert Messages (Monitoring Agent to email/log):**
```json
{
  "alert_id": "uuid",
  "triggered_at": "2026-04-12T10:30:00Z",
  "rule": { "type": "mean_shift", "column": "revenue", "threshold": 0.15 },
  "finding": { "actual_value": 0.32, "severity": "HIGH", "detail": "Revenue mean shifted 32% from baseline" },
  "dataset": "sales_weekly.csv"
}
```

### Process Patterns

**Error Handling (Dual Strategy):**

Expected business outcomes use the Result pattern:
```python
@dataclass
class PipelineResult:
    success: bool
    halted: bool = False
    halt_reason: str | None = None
    quality_report: DataQualityReport | None = None
    insight_report: InsightReport | None = None
    drift_report: DriftReport | None = None
```

Unexpected failures use the Exception hierarchy:
```python
class SavvyCleanseError(Exception): ...
class PipelineStageError(SavvyCleanseError): ...
class LLMProviderError(PipelineStageError): ...
class ReportRenderError(PipelineStageError): ...
class DriftComputationError(PipelineStageError): ...
class ConfigurationError(SavvyCleanseError): ...
```

Rule: **Exceptions are for the unexpected. Result types are for the expected.** Bad data produces `PipelineResult(halted=True)`. Disk full raises `ReportRenderError`.

**LLM Call Pattern (every LLM interaction):**
```python
try:
    result = client.messages.parse(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": grounding_prompt}],
        output_format=InsightReport,
    )
except anthropic.APITimeoutError:
    logger.warning("llm_timeout", provider="claude", attempt=attempt)
    # Retry with backoff, then fallback to next provider
except anthropic.APIError as e:
    logger.error("llm_api_error", provider="claude", error=str(e))
    raise LLMProviderError("claude", cause=e) from e
```

**Retry Pattern:**
- Max 3 attempts with exponential backoff (1s, 2s, 4s)
- Provider fallback chain: Claude then OpenAI then Gemini
- Circuit breaker: after 3 consecutive failures across all providers, skip narrative generation
- Never retry on 4xx errors (client errors) — only 5xx and timeouts

**Loading States (Frontend, Phase 3+):**
- Use React Query built-in `isLoading`, `isError`, `data` states
- No custom loading state management
- Report generation (long-running): polling endpoint returns `{ "status": "pending" | "processing" | "completed" | "failed", "progress": 0.0-1.0 }`

### Enforcement Guidelines

**All AI Agents MUST:**
1. Use Pydantic models for ALL pipeline stage inputs and outputs — no raw dicts
2. Follow the naming conventions above — database snake_case, Python snake_case, React PascalCase
3. Write tests alongside production code — no module without a corresponding test file
4. Use structlog for ALL logging — never `print()`, never `logging.basicConfig()`
5. Include `pipeline_run_id` in every log entry within a pipeline execution
6. Return `PipelineResult` for expected outcomes, raise from `SavvyCleanseError` hierarchy for unexpected
7. Never hardcode API keys, credentials, or environment-specific values
8. Add type hints to ALL function signatures
9. Validate with Pandera before DataFrame processing, Pydantic before JSON output

**Anti-Patterns (NEVER do these):**
- `except Exception: pass` — silent exception swallowing
- `warnings.filterwarnings('ignore')` — hiding warnings
- `DATA_STORAGE = {}` — global mutable state for data
- `def process(data: dict) -> dict` — untyped dict-in dict-out interfaces
- `print(f"Debug: {value}")` — print-based debugging in production code
- `import *` — wildcard imports
- Hardcoded model versions — use config/constants

## Project Structure & Boundaries

### Complete Project Directory Structure

```
savvy-cleanse-analysis/
├── .env                            # Environment variables (secrets, API keys)
├── .env.example                    # Template with placeholder values (committed)
├── .gitignore
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Phase 5: lint, test, build on PR
│       └── deploy.yml              # Phase 5: deploy on main merge
├── config.yaml                     # Phase 2: user-facing config (thresholds, schedules, recipients)
├── docker-compose.yml              # Phase 5: backend + redis + postgres
├── Dockerfile                      # Phase 5: backend container
├── pyproject.toml                  # Backend: pytest config, project metadata
├── package.json                    # Frontend: React + Vite + dependencies
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── index.html
├── README.md
│
├── backend/
│   ├── __init__.py
│   │
│   ├── pipeline/                   # Phase 1-2: Core analytical engine
│   │   ├── __init__.py
│   │   ├── orchestrator.py         # run_full_pipeline() — composes all stages
│   │   ├── data_quality.py         # Stage 0: DataQualityAssessor (6 categories, halt-on-critical)
│   │   ├── drift_engine.py         # Stage 0b: stateless drift computation (7 checks)
│   │   ├── insight_engine.py       # Stage 1: aggregations, trends, outliers → InsightPayload
│   │   ├── narrative_generator.py  # Stage 2: Claude structured outputs → InsightReport
│   │   └── config.py               # PipelineConfig dataclass
│   │
│   ├── models/                     # Phase 1: Pydantic contracts (shared across all stages)
│   │   ├── __init__.py
│   │   ├── quality_report.py       # DataQualityReport, DataQualityDefect, Severity enum
│   │   ├── drift_report.py         # DriftReport, DriftFinding, BaselineProfile
│   │   ├── insight_payload.py      # InsightPayload (stats JSON for LLM grounding)
│   │   ├── insight_report.py       # InsightReport (LLM narrative output)
│   │   ├── pipeline_config.py      # PipelineConfig, ThresholdConfig
│   │   ├── pipeline_result.py      # PipelineResult (success/halt/reports)
│   │   └── alert.py                # Phase 2: AlertMessage, AlertRule, AlertDelivery
│   │
│   ├── agents/                     # Phase 2: Thin Python wrappers (Typer CLI)
│   │   ├── __init__.py
│   │   ├── reporting_agent.py      # CLI: generate reports (manual + scheduled)
│   │   └── monitoring_agent.py     # CLI: evaluate thresholds, emit alerts
│   │
│   ├── renderers/                  # Phase 1: Document output
│   │   ├── __init__.py
│   │   ├── docx_renderer.py        # docxtpl template population → .docx
│   │   ├── pdf_renderer.py         # WeasyPrint HTML → .pdf
│   │   └── templates/
│   │       ├── report_template.docx    # Branded Word template with Jinja2 placeholders
│   │       └── report_template.html    # HTML template for PDF rendering
│   │
│   ├── baselines/                  # Phase 2: Drift baseline storage
│   │   └── .gitkeep                # JSON files created at runtime; PostgreSQL in Phase 5
│   │
│   ├── errors/                     # Phase 1: Custom exception hierarchy
│   │   ├── __init__.py
│   │   └── exceptions.py           # SavvyCleanseError tree
│   │
│   ├── api/                        # Phase 3: New FastAPI endpoints
│   │   ├── __init__.py
│   │   ├── router.py               # Main API router aggregating sub-routers
│   │   ├── reports.py              # /api/reports — generate, list, download
│   │   ├── alerts.py               # /api/alerts — list, acknowledge, configure
│   │   ├── uploads.py              # /api/uploads — file upload + validation
│   │   ├── config_api.py           # /api/config — get/set analysis parameters
│   │   ├── auth.py                 # /api/auth — Supabase JWT verification middleware
│   │   ├── billing.py              # Phase 4: /api/billing — Stripe checkout, plans, usage
│   │   ├── webhooks.py             # Phase 4: /api/webhooks/stripe — Stripe event handling
│   │   ├── analytics_api.py        # Phase 6: /api/analytics — forecast, NL query
│   │   └── deps.py                 # Shared dependencies (get_current_user, get_db, rate_limit)
│   │
│   ├── db/                         # Phase 3: Database layer
│   │   ├── __init__.py
│   │   ├── session.py              # SQLAlchemy async session factory
│   │   ├── models.py               # SQLAlchemy ORM models (users, reports, alerts, etc.)
│   │   └── migrations/             # Alembic migrations directory
│   │       ├── env.py
│   │       └── versions/
│   │
│   ├── services/                   # Phase 3+: Business logic for web layer
│   │   ├── __init__.py
│   │   ├── report_service.py       # Orchestrates pipeline for web requests
│   │   ├── alert_service.py        # Alert CRUD + threshold management
│   │   ├── upload_service.py       # File validation, storage, metadata
│   │   ├── billing_service.py      # Phase 4: Stripe integration logic
│   │   ├── usage_service.py        # Phase 4: Usage tracking + limit enforcement
│   │   └── query_service.py        # Phase 6: NL query → pandas → response
│   │
│   ├── tasks/                      # Phase 5: Celery async tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py           # Celery configuration + Redis broker
│   │   ├── report_tasks.py         # Async report generation
│   │   └── monitoring_tasks.py     # Async monitoring + alert delivery
│   │
│   ├── tests/                      # All backend tests
│   │   ├── conftest.py             # Shared fixtures (DataFrames, mock LLM, test config)
│   │   ├── test_data_quality.py
│   │   ├── test_drift_engine.py
│   │   ├── test_insight_engine.py
│   │   ├── test_narrative_generator.py
│   │   ├── test_renderers.py
│   │   ├── test_monitoring_agent.py
│   │   ├── test_pipeline_result.py
│   │   ├── test_models.py
│   │   ├── integration/
│   │   │   ├── test_pipeline_e2e.py
│   │   │   └── test_api_endpoints.py
│   │   └── e2e/
│   │       ├── test_cli_reporting.py
│   │       └── sample_data/
│   │           ├── clean_sales.csv
│   │           ├── dirty_sales.csv
│   │           └── drift_sales.csv
│   │
│   ├── advanced_pipeline.py        # LEGACY — reference implementation
│   ├── comprehensive_analytics.py  # LEGACY — reference implementation
│   ├── nlp_processor.py            # LEGACY — reference implementation
│   ├── cleaner.py                  # EXISTING — reuse (factory refactor)
│   ├── analytics.py                # LEGACY — deprecate
│   ├── main.py                     # EXISTING — Phase 3 mounts new api/ router
│   ├── main_enhanced.py            # LEGACY — do not use (hardcoded credentials)
│   ├── dashboard_api.py            # EXISTING — Phase 3 rewrites to real data
│   └── requirements.txt
│
├── src/                            # Frontend: React + TypeScript
│   ├── App.tsx
│   ├── main.tsx
│   ├── index.css
│   ├── pages/
│   │   ├── Index.tsx
│   │   ├── Dashboard.tsx           # Phase 3: wired to real pipeline API
│   │   ├── Reports.tsx             # Phase 3: report history + viewer
│   │   ├── Alerts.tsx              # Phase 3: alert dashboard
│   │   ├── Settings.tsx            # Phase 3: analysis configuration
│   │   ├── Billing.tsx             # Phase 4: plan selection, usage, invoices
│   │   ├── pricing.tsx             # Existing marketing page
│   │   ├── features.tsx            # Existing marketing page
│   │   └── NotFound.tsx
│   ├── components/
│   │   ├── dashboard/              # Existing 16 components (re-wire Phase 3)
│   │   ├── reports/                # Phase 3: ReportViewer, ReportHistory, ReportDownload
│   │   ├── alerts/                 # Phase 3: AlertList, AlertDetail, ThresholdConfig
│   │   ├── billing/                # Phase 4: PlanSelector, UsageBar, InvoiceHistory
│   │   ├── analytics/              # Phase 6: ForecastChart, NLQueryInput, CohortTable
│   │   ├── layout/                 # Existing Navbar, Footer
│   │   └── ui/                     # Existing ShadCN components
│   ├── hooks/
│   │   ├── useReports.ts           # Phase 3
│   │   ├── useAlerts.ts            # Phase 3
│   │   ├── useBilling.ts           # Phase 4
│   │   └── use-toast.ts            # Existing
│   ├── lib/
│   │   ├── api.ts                  # Phase 3: API client with auth
│   │   ├── utils.ts                # Existing
│   │   └── stripe.ts               # Phase 4: Stripe.js init
│   ├── integrations/
│   │   └── supabase/
│   │       ├── client.ts           # Phase 3: unified single Supabase project
│   │       └── types.ts
│   └── types/
│       ├── report.ts               # Phase 3
│       ├── alert.ts                # Phase 3
│       └── billing.ts              # Phase 4
│
├── supabase/                       # Existing Supabase config
│   └── migrations/
│
└── output/                         # CLI output directory (gitignored)
    ├── reports/                    # Generated docx/PDF reports
    ├── logs/                       # structlog JSON output
    └── alerts/                     # Alert log files
```

### Architectural Boundaries

**Three-Layer Separation:**

| Layer | Backend Directories | Responsibility | Never Touches |
|-------|-------------------|----------------|---------------|
| Presentation | api/, agents/, renderers/ | HTTP endpoints, CLI commands, document output | Database directly |
| Business Logic | pipeline/, services/, models/ | Data processing, analytics, LLM interaction | HTTP request/response objects |
| Data Access | db/, baselines/ | Database queries, file I/O, baseline persistence | Business rules |

**API Boundaries:**
- `backend/api/` is the ONLY directory that handles HTTP. Pipeline stages never import from `api/`.
- `backend/agents/` is the ONLY directory with Typer CLI commands. Pipeline stages never import from `agents/`.
- `backend/pipeline/` is callable from both `api/` and `agents/` but imports from neither.

**Data Flow (Pipeline):**
```
CSV File → orchestrator.py
  → data_quality.py (DataFrame → DataQualityReport)
  → [halt check: if critical, return PipelineResult(halted=True)]
  → drift_engine.py (DataFrame + BaselineProfile → DriftReport) [Phase 2, optional]
  → insight_engine.py (DataFrame + QualityReport + DriftReport → InsightPayload)
  → narrative_generator.py (InsightPayload → InsightReport)
  → docx_renderer.py / pdf_renderer.py (InsightReport → file)
  → PipelineResult(success=True, ...)
```

**Data Flow (Web, Phase 3+):**
```
Browser → React (src/) → API fetch (lib/api.ts)
  → FastAPI (backend/api/) → Service (backend/services/)
  → Pipeline (backend/pipeline/) → Database (backend/db/)
  → Response back through layers
```

### Requirements to Structure Mapping

| PRD Phase | Primary Directories | Key Files |
|-----------|-------------------|-----------|
| Phase 1: Foundation | pipeline/, models/, renderers/, errors/, tests/ | data_quality.py, insight_engine.py, narrative_generator.py, docx_renderer.py, pdf_renderer.py |
| Phase 2: Automation | agents/, baselines/, config.yaml | reporting_agent.py, monitoring_agent.py, drift_engine.py |
| Phase 3: Interface | api/, services/, db/, src/pages/, src/components/ | router.py, reports.py, alerts.py, uploads.py, auth.py, session.py |
| Phase 4: Monetization | api/billing.py, api/webhooks.py, services/, src/pages/Billing.tsx | billing_service.py, usage_service.py, PlanSelector.tsx |
| Phase 5: Scale | tasks/, docker-compose.yml, Dockerfile, .github/workflows/ | celery_app.py, report_tasks.py, ci.yml, deploy.yml |
| Phase 6: Intelligence | api/analytics_api.py, services/query_service.py, src/components/analytics/ | ForecastChart.tsx, NLQueryInput.tsx, CohortTable.tsx |

### Cross-Cutting Concerns Locations

| Concern | Files |
|---------|-------|
| Error handling | errors/exceptions.py, models/pipeline_result.py |
| Logging | Every module imports structlog; config in pipeline/config.py |
| Auth | api/auth.py + api/deps.py (backend), integrations/supabase/client.ts (frontend) |
| Configuration | config.yaml (user), .env (secrets), pipeline/config.py (code) |
| Testing | tests/conftest.py (fixtures), tests/e2e/sample_data/ (golden files) |

### Integration Points

| Service | Backend File | Phase |
|---------|-------------|-------|
| Claude API (Anthropic) | pipeline/narrative_generator.py | 1 |
| OpenAI API (fallback) | pipeline/narrative_generator.py | 1 |
| Supabase Auth | api/auth.py, api/deps.py | 3 |
| Supabase Storage | services/upload_service.py | 3 |
| PostgreSQL | db/session.py, db/models.py | 3 |
| Stripe | services/billing_service.py, api/webhooks.py | 4 |
| Redis | tasks/celery_app.py | 5 |
| Sentry | main.py (init), all modules (auto-capture) | 5 |
| SMTP | agents/monitoring_agent.py | 2 |

### Development Workflow

- **Phase 1-2 (CLI):** `python -m backend.agents.reporting_agent generate --input data.csv --output report.docx`
- **Phase 3+ (Web):** `uvicorn backend.main:app --reload` + `npm run dev` (Vite)
- **Phase 5 (Docker):** `docker-compose up` — starts backend, Redis, PostgreSQL, Celery worker
- **Testing:** `pytest backend/tests/` (backend), `npx vitest` (frontend)

## Architecture Validation Results

### Coherence Validation

**Decision Compatibility:** ✅ Pass
- Python 3.13 + FastAPI + SQLAlchemy 2.0 + Pydantic v2 — fully compatible
- React 18 + Vite + ShadCN + TanStack Query — no version conflicts
- Anthropic SDK 0.79.0 structured outputs + Pydantic v2 — designed to work together
- Celery 5.6.3 pins Redis <=5.2.1 — must pin Redis version in Phase 5
- WeasyPrint 68.1 requires Python >=3.10, we're on 3.13 — compatible

**Pattern Consistency:** ✅ Pass
- snake_case everywhere in Python, PascalCase for classes/components, camelCase in frontend — clean boundaries
- RFC 7807 error format aligns with FastAPI validation error handling
- structlog JSON logging consistent across pipeline, API, and agents

**Structure Alignment:** ✅ Pass
- Three-layer separation enforced by directory boundaries
- Pipeline stages only import from models/ — never from api/ or agents/
- Test structure mirrors source structure

**Minor Issue Resolved:** Phase 1 first commit adds `__init__.py` files and verifies `python -m backend.agents.reporting_agent` works as module path.

### Requirements Coverage Validation

**PRD Phase Coverage:**

| Phase | DoD Items | Covered | Status |
|-------|-----------|---------|--------|
| 1: Foundation | 5 | 5/5 | ✅ |
| 2: Automation | 5 | 5/5 | ✅ |
| 3: Interface | 5 | 5/5 | ✅ |
| 4: Monetization | 5 | 5/5 | ✅ |
| 5: Scale | 6 | 6/6 | ✅ |
| 6: Intelligence | 6 | 6/6 | ✅ |

**NFR Coverage:**

| NFR | Status | Architecture Support |
|-----|--------|---------------------|
| Performance (<60s report) | ✅ | Synchronous pure-function pipeline; no message queue overhead in Phase 1-2 |
| Security (no hardcoded creds) | ✅ | .env + python-dotenv; legacy credentials flagged for rotation |
| Data integrity (LLM grounding) | ✅ | narrative_generator.py receives InsightPayload; LLM does not compute |
| Reliability (halt-on-critical) | ✅ | PipelineResult(halted=True) pattern; DQA stops before LLM call |
| Scalability (10 concurrent) | ✅ | Celery + Redis in Phase 5; async task queue with dead letter queue |
| Compliance (tenant isolation) | ✅ | PostgreSQL RLS + tenant_id on all tables from Phase 3 (enforced Phase 5) |

### Implementation Readiness Validation

**Decision Completeness:** ✅ 25 decisions documented with versions, rationale, and affected phases.
**Structure Completeness:** ✅ ~80 files/directories specified. Every PRD phase maps to specific locations.
**Pattern Completeness:** ✅ 18 conflict points resolved. Code examples for error handling, LLM calls, API responses, alerts.

### Gap Analysis Results

**Critical Gaps:** None.

**Important Gaps (resolved):**

1. **Drift Engine baseline rotation counter:** `consecutive_clean_runs` field added to BaselineProfile JSON. Drift Engine increments on clean run, resets on alert. At count 4, current data becomes new baseline.

2. **Phase 3 Supabase unification:** Frontend Supabase project survives (has auth users). Backend switches to frontend project URL/keys. No data migration needed — backend uses in-memory storage currently.

3. **API versioning backwards compatibility:** Phase 3-5 endpoints at `/api/reports`, `/api/alerts`. Phase 6 adds `/api/v1/` prefix. Unversioned paths become aliases to v1.

**Nice-to-Have (deferred):**

4. Database seeding strategy — add `backend/db/seed.py` in Phase 3 sprint.
5. Observability dashboard selection — defer to Phase 5 sprint (Grafana vs Sentry dashboards).

### Architecture Completeness Checklist

**Requirements Analysis**
- [x] Project context thoroughly analyzed (32 FRs, 18 NFRs)
- [x] Scale and complexity assessed (High — full-stack, 6 phases)
- [x] Technical constraints identified (existing codebase, agent philosophy, PRD authority)
- [x] Cross-cutting concerns mapped (auth, errors, logging, secrets, LLM resilience, config)

**Foundation Assessment**
- [x] Existing codebase honestly evaluated (component reuse, not architectural reuse)
- [x] In-Place Evolution strategy selected with test-first setup
- [x] Legacy modules labeled, not deleted
- [x] Phase 3 complexity acknowledged (significant integration, not light wiring)

**Architectural Decisions**
- [x] 25 decisions documented with verified versions
- [x] Technology stack fully specified across all 6 phases
- [x] Integration patterns defined (LLM, Stripe, Supabase, Celery)
- [x] Implementation sequence ordered by phase dependency

**Implementation Patterns**
- [x] Naming conventions established (database, API, Python, TypeScript)
- [x] Structure patterns defined (test organization, config files)
- [x] Format patterns specified (API responses, dates, null handling)
- [x] Process patterns documented (error handling, retry, loading states)
- [x] 9 enforcement rules + 7 anti-patterns

**Drift Engine**
- [x] Stateless computation fully specified (7 checks with formulas and thresholds)
- [x] Baseline management defined (JSON to PostgreSQL migration path)
- [x] Integration with Monitoring Agent, Reporting Agent, and Insight Engine documented
- [x] Explicit scope boundaries (not a gate, not predictive, not self-healing)

**Project Structure**
- [x] Complete directory tree (~80 files/directories)
- [x] Three-layer boundaries enforced
- [x] All 6 PRD phases mapped to specific directories and files
- [x] Cross-cutting concern locations documented
- [x] Integration points with all external services mapped

### Architecture Readiness Assessment

**Overall Status: READY FOR IMPLEMENTATION**

**Confidence Level:** High

**Key Strengths:**
- Every PRD DoD item has a clear architectural home
- First Principles analysis prevented building on a false foundation
- Drift Engine spec is production-grade with concrete formulas and thresholds
- Pattern enforcement rules are specific enough for AI agents to follow mechanically
- Three-layer boundary rules prevent cross-contamination

**Areas for Future Enhancement:**
- Database seeding strategy (Phase 3)
- Observability dashboard selection (Phase 5)
- API versioning backwards-compatibility testing (Phase 6)

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented
- Use implementation patterns consistently across all components
- Respect project structure and layer boundaries
- Refer to this document for all architectural questions
- Legacy modules are reference only — never import them in new code

**First Implementation Priority:**
1. Create directory structure (pipeline/, models/, agents/, renderers/, baselines/, errors/, tests/)
2. Add __init__.py files and pyproject.toml with pytest config
3. Create tests/conftest.py with shared DataFrame fixtures
4. Fix 6 Day-1 tech debt items (~1.5 hours)
5. Begin models/quality_report.py then pipeline/data_quality.py then tests/test_data_quality.py
