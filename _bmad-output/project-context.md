---
project_name: 'SavvyCortex'
user_name: 'Marvin'
date: '2026-04-14'
sections_completed:
  - technology_stack
  - language_rules
  - framework_rules
  - testing_rules
  - quality_rules
  - workflow_rules
  - anti_patterns
status: 'complete'
rule_count: 60
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in SavvyCortex. Focus on unobvious details agents might miss. Full rationale in `_bmad-output/planning-artifacts/architecture.md`._

---

## Technology Stack & Versions

### Backend (Python 3.13)
- **FastAPI** + uvicorn
- **Pydantic v2** — universal contract language between pipeline stages, FastAPI, Claude structured outputs
- **Pandera 0.30.1** — DataFrame validation; use BEFORE any DataFrame processing
- **structlog 25.5.0** — JSON logging with correlation IDs; replaces all `print()` and `logging.basicConfig()`
- **Anthropic SDK 0.79.0** — `client.messages.parse` with Pydantic output schemas; no LangChain
- **pandas, scikit-learn, scipy, numpy** — analytics primitives
- **docxtpl 0.20.2 + WeasyPrint 68.1** — document rendering (Phase 1)
- **Typer 0.12.1** — CLI framework (Phase 2 agents)
- **SQLAlchemy 2.0 + Alembic** — ORM + migrations (Phase 3+)
- **supabase-py, python-dotenv** — auth + secrets
- **Celery 5.6.3 + Redis + sentry-sdk + Docker** — Phase 5
- **Prophet or statsmodels** — forecasting (Phase 6)

### Frontend (TypeScript 5.5)
- **React 18.3.1** + **Vite 5.4** (SWC compiler)
- **ShadCN/ui** — 87 Radix-based components already installed; reuse, do not replace
- **Tailwind CSS 3.4** + tailwindcss-animate; next-themes for dark/light
- **TanStack Query 5.56** — server state; no client-side store until Phase 6
- **React Hook Form 7.53 + Zod 3.23** — forms
- **react-router-dom 6.26**, **recharts 3.2**, **papaparse 5.5**, **pdfjs-dist 5.2**

### TypeScript Config Reality
`tsconfig.json` has RELAXED settings (`noImplicitAny: false`, `strictNullChecks: false`, `allowJs: true`). Do not assume strict-mode TS semantics. Use `@/*` path alias for `./src/*`.

---

## Critical Implementation Rules

### Language-Specific Rules

**Python:**
- Type hints REQUIRED on all function signatures
- Pydantic models for all pipeline I/O — no `dict`/`Any` at stage boundaries
- Pandera validation BEFORE DataFrame processing; raise `ConfigurationError` on schema mismatch
- Never `warnings.filterwarnings('ignore')`
- Never `except Exception: pass`
- Never `print()` in backend code — use structlog
- Never wildcard imports (`from x import *`)

**TypeScript/React:**
- API responses are snake_case (FastAPI default); transform to camelCase in `src/lib/api.ts`
- Null handling: `T | null`, not `T | undefined`, for API-sourced data
- File naming: PascalCase components (`ReportViewer.tsx`), camelCase hooks (`useReportData.ts`)

### Framework-Specific Rules

**FastAPI (`backend/api/` only):**
- Only directory with HTTP endpoints; pipeline stages never import from `api/`
- Routes under `/api/v1/*` starting Phase 6; unversioned before
- Error: RFC 7807 Problem Details. Success: `{"data": {...}, "meta": {"requestId", "timestamp"}}`
- Dates: ISO 8601 UTC with trailing `Z`

**Pipeline (`backend/pipeline/`):**
- Composable stages returning Pydantic models — `PipelineResult` for expected outcomes, exceptions for unexpected
- Halt-on-critical: `PipelineResult(halted=True, halt_reason=...)`
- LLM uses `client.messages.parse(output_format=PydanticModel)` — never parse free-form text
- LLM retry: 3 attempts, exp backoff 1s/2s/4s, fallback Claude → OpenAI → Gemini; never retry on 4xx

**React (`src/`):**
- TanStack Query for ALL server state — use built-in `isLoading`/`isError`/`data`
- React Hook Form + Zod for ALL forms
- No client-side global store until Phase 6
- Long-running ops: poll `/api/.../status` returning `{status, progress: 0.0-1.0}`

### Testing Rules

**Backend (pytest — zero tests exist today; start with Phase 1):**
- Tests in `backend/tests/` (NOT co-located)
- Mirror source: `tests/test_data_quality.py` tests `pipeline/data_quality.py`
- Shared fixtures in `backend/tests/conftest.py` (clean + dirty-with-known-defects DataFrames, mock LLM)
- `backend/tests/integration/` — stage-to-stage; `backend/tests/e2e/` — CLI with real CSV
- Every new module requires a matching test file

**Frontend (vitest — Phase 1 setup):**
- Co-located: `ReportViewer.test.tsx` next to `ReportViewer.tsx`
- Vitest + React Testing Library

### Code Quality & Style Rules

**Naming:**
- Database: plural snake_case (`users`, `alert_thresholds`); FK `{ref}_id`; every table has `id` (UUID), `created_at`, `updated_at`, `tenant_id` (nullable until Phase 5 RLS)
- Python: modules `snake_case.py`, classes `PascalCase`, functions `snake_case()`, constants `UPPER_SNAKE`, private `_prefix`; Pydantic models PascalCase noun-based
- React/TS: components/types PascalCase; hooks `useCamelCase`; utilities camelCase
- API: plural snake_case paths; query params snake_case

**Layer boundaries (enforce):**

| Layer | Dirs | Never Touches |
|-------|------|---------------|
| Presentation | `api/`, `agents/`, `renderers/` | Database directly |
| Business Logic | `pipeline/`, `services/`, `models/` | HTTP objects |
| Data Access | `db/`, `baselines/` | Business rules |

**Legacy modules (NEVER IMPORT from new code):**
- `advanced_pipeline.py`, `comprehensive_analytics.py`, `nlp_processor.py`, `analytics.py`, `main_enhanced.py` (hardcoded creds), `dashboard_api.py`
- `main.py` retained; `cleaner.py` needs factory refactor for testability
- Each gets a STATUS header comment marking it as legacy reference

**Config files:**
- `pyproject.toml` at repo root (pytest + project metadata)
- `backend/models/pipeline_config.py` — `PipelineConfig` Pydantic model + `load()` (Story 2.1); re-exported via `backend/pipeline/config.py`, which also hosts `configure_logging()`
- `config.yaml` at project root — Phase 2 thresholds/schedules
- `.env` for secrets; `.env.example` committed with placeholders

### Development Workflow Rules

**Git conventions observed:**
- Feature branches: `claude/<adjective>-<name>` for agent worktrees
- Main: `main`; merge via PR
- Commit style: imperative mood, terse subject
- Worktrees under `.claude/worktrees/` share base `_bmad-output/` with main repo

**Logging discipline:**
- Every log entry in a run includes `pipeline_run_id` (UUID)
- Event naming: `snake_case verb_noun` (`quality_assessed`, `pipeline_halted`)
- Levels: debug/info/warning/error/critical (stage halt)
- NEVER log: API keys, raw row data, PII, file paths with usernames

### Critical Don't-Miss Rules

**Anti-patterns (NEVER):**
- `except Exception: pass`
- `warnings.filterwarnings('ignore')`
- Global mutable state (`DATA_STORAGE = {}`)
- Untyped dict-in/dict-out interfaces
- `print()` debug in production code
- `import *` wildcard
- Hardcoded model versions, API keys, Supabase URLs
- Raw dicts from pipeline stages — always Pydantic
- LLM computing numbers independently — LLM receives pre-computed stats, writes narrative only

**Security:**
- **Immediate:** `main_enhanced.py` and `src/integrations/supabase/client.ts` have hardcoded Supabase credentials — rotate and move to env vars before any deploy
- Two separate Supabase projects exist; Phase 3 unifies to one — don't assume single-project auth yet
- No feature may allow cross-tenant data access (RLS enforced Phase 5)

**Performance:**
- Report generation target: <60s from CSV
- 10 concurrent jobs without degradation
- No synchronous LLM calls on request path Phase 3+ — queue via Celery in Phase 5

**Day-1 tech debt (6 items, fixed in Story 1.1 before any pipeline code):**
Enumerated in architecture.md; includes replacing `warnings.filterwarnings('ignore')`, removing hardcoded credentials, eliminating `DATA_STORAGE` global, adding type hints to legacy-adapted code, removing `print()` debug, establishing `SavvyCleanseError` hierarchy.

**LLM grounding (inviolable):**
LLM narrative generator receives pre-computed statistics from Insight Engine as structured input. Output validated against Pydantic `InsightReport` schema. LLM never executes pandas, never decides whether anomalies are real — it writes narrative about stats computed deterministically.

---

## Reference Documents

- **`_bmad-output/planning-artifacts/prd.md`** — product vision, 6 phases, functional + non-functional requirements
- **`_bmad-output/planning-artifacts/architecture.md`** — complete architectural decisions, patterns, directory tree, integration points
- **`_bmad-output/planning-artifacts/epics.md`** — 7 epics, 40 stories with BDD acceptance criteria
- **`_bmad-output/sprint-status.yaml`** — current sprint/story tracking (generated by sprint-planning workflow)

---

## Usage Guidelines

**For AI Agents:**
- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**
- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-04-14
