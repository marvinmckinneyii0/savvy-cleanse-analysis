# Story 1.1: Project Scaffolding & Pipeline Foundation

Status: done

<!-- Validation is optional. Run validate-create-story for a quality check before dev-story. -->

---

## Story

**As a** developer on SavvyCortex,
**I want** the backend package structure, test infrastructure, error handling hierarchy, and structured logging in place with Day-1 tech debt fixed,
**So that** all subsequent pipeline stories (DQA, Insight Engine, Narrative Generator, Renderer) build on a clean, tested, properly organized foundation instead of accumulating technical debt on top of legacy flat modules.

### Business Context

This is the first story of Epic 1 — Phase 1 (Foundation). Nothing else in the product can ship without it. The existing `backend/` directory contains legacy flat modules (advanced_pipeline.py, comprehensive_analytics.py, nlp_processor.py, main.py, main_enhanced.py, dashboard_api.py) that silently swallow warnings, hardcode credentials, use global mutable state, and lack any test coverage. Before any production pipeline code is written, the architectural scaffolding and Day-1 debt fixes must be in place so every subsequent story starts from a clean baseline.

Success here is binary: either `pytest backend/tests/` runs green against the conftest fixtures, every directory listed below exists with `__init__.py`, every anti-pattern in the architecture has been eliminated, and structlog emits JSON with correlation IDs — or the story is not done.

---

## Acceptance Criteria

The AC below comes verbatim from [epics.md:218-237](../planning-artifacts/epics.md). Do not reinterpret — implement to the letter.

**Given** the existing repository with legacy flat modules
**When** the scaffolding story is complete
**Then** the following directories exist with `__init__.py`: `backend/pipeline/`, `backend/models/`, `backend/agents/`, `backend/renderers/`, `backend/baselines/`, `backend/errors/`, `backend/tests/`
**And** `pyproject.toml` exists with pytest configuration and project metadata
**And** `backend/tests/conftest.py` exists with shared DataFrame fixtures (clean dataset, dirty dataset with known defects)
**And** `backend/errors/exceptions.py` defines the `SavvyCleanseError` hierarchy (`SavvyCleanseError`, `PipelineStageError`, `LLMProviderError`, `ReportRenderError`, `DriftComputationError`, `ConfigurationError`)
**And** `backend/models/pipeline_result.py` defines `PipelineResult` dataclass (`success`, `halted`, `halt_reason`, `quality_report`, `insight_report`, `drift_report`)
**And** structlog is configured for JSON output with `pipeline_run_id` correlation
**And** the 6 Day-1 tech debt items identified in the Architecture document are fixed
**And** legacy modules (`advanced_pipeline.py`, `comprehensive_analytics.py`, `nlp_processor.py`, `main.py`, `dashboard_api.py`) have STATUS header comments marking them as legacy reference implementations
**And** `pytest backend/tests/` runs successfully with at least the conftest fixtures validated
**And** `.env.example` exists with placeholder values (no secrets committed)

---

## Tasks / Subtasks

- [x] **Task 1 — Directory scaffolding** (AC: directories + `__init__.py`)
  - [x] Create `backend/pipeline/`, `backend/models/`, `backend/agents/`, `backend/renderers/`, `backend/baselines/`, `backend/errors/`, `backend/tests/`
  - [x] Add empty `__init__.py` to every new directory (including `backend/__init__.py` if missing)
  - [x] Add `backend/baselines/.gitkeep` (runtime-populated JSON directory per architecture spec)
  - [x] Add `backend/renderers/templates/` subdirectory with `.gitkeep` (populated in Story 1.5)
  - [x] Confirm `python -m backend.agents.reporting_agent` resolves the module path (architecture minor issue note, [architecture.md:837](../planning-artifacts/architecture.md))

- [x] **Task 2 — pyproject.toml + pytest config** (AC: pyproject.toml)
  - [x] Create `pyproject.toml` at repo root (NOT inside `backend/`) per [architecture.md:574](../planning-artifacts/architecture.md) and [project-context.md](../project-context.md)
  - [x] Include `[project]` metadata (name=`savvycortex`, Python `>=3.13`)
  - [x] Include `[tool.pytest.ini_options]` with `testpaths = ["backend/tests"]`, `python_files = ["test_*.py"]`, `addopts = "-ra -q"`
  - [x] Include `[tool.pytest.ini_options] markers` entries for `integration` and `e2e`
  - [x] Do NOT add `warnings.filterwarnings` in pytest config — legitimate warnings must surface

- [x] **Task 3 — Error hierarchy** (AC: `backend/errors/exceptions.py`)
  - [x] Define `SavvyCleanseError(Exception)` as root
  - [x] Define `PipelineStageError(SavvyCleanseError)`
  - [x] Define `LLMProviderError(PipelineStageError)` accepting `provider: str` + optional `cause: Exception`
  - [x] Define `ReportRenderError(PipelineStageError)`
  - [x] Define `DriftComputationError(PipelineStageError)`
  - [x] Define `ConfigurationError(SavvyCleanseError)` — NOTE: sibling of `PipelineStageError`, NOT a child
  - [x] Add docstrings explaining the Result-vs-Exception split (see [architecture.md:482-506](../planning-artifacts/architecture.md))
  - [x] Add full type hints

- [x] **Task 4 — PipelineResult contract** (AC: `backend/models/pipeline_result.py`)
  - [x] Define `PipelineResult` as a `@dataclass` (per architecture.md:486-494 — NOT a Pydantic model; this is the only structural exception because future stages may populate it post-construction)
  - [x] Fields (exact signature, types via forward refs / `TYPE_CHECKING` import if needed to avoid circular imports):
    - `success: bool`
    - `halted: bool = False`
    - `halt_reason: str | None = None`
    - `quality_report: "DataQualityReport | None" = None`
    - `insight_report: "InsightReport | None" = None`
    - `drift_report: "DriftReport | None" = None`
  - [x] Do NOT import the three Pydantic report models yet — they don't exist. Use string forward references. Add a `TYPE_CHECKING` block importing them so type-checkers still see them.

- [x] **Task 5 — structlog configuration** (AC: structlog JSON + pipeline_run_id)
  - [x] Create `backend/pipeline/config.py` with a `configure_logging()` function and a `PipelineConfig` dataclass stub (full fields land in Story 1.6; this story only needs the hook)
  - [x] `configure_logging()` installs processors: `structlog.contextvars.merge_contextvars`, `structlog.processors.add_log_level`, `structlog.processors.TimeStamper(fmt="iso", utc=True)`, `structlog.processors.StackInfoRenderer()`, `structlog.processors.format_exc_info`, `structlog.processors.JSONRenderer()`
  - [x] Add a helper `bind_pipeline_run_id(run_id: str) -> None` that calls `structlog.contextvars.bind_contextvars(pipeline_run_id=run_id)` so every subsequent log from any stage inherits it
  - [x] Do NOT call `logging.basicConfig()` (anti-pattern per [architecture.md:542](../planning-artifacts/architecture.md))
  - [x] Do NOT call `configure_logging()` at import time — callers (CLI, tests, FastAPI app) invoke it explicitly

- [x] **Task 6 — conftest.py fixtures** (AC: `backend/tests/conftest.py`)
  - [x] Create `backend/tests/conftest.py`
  - [x] Fixture `clean_sales_df` — pandas DataFrame with 3 columns (`date: datetime64`, `region: str`, `revenue: float`), ~50 rows, no nulls, no duplicates, monotonic dates, realistic revenue range
  - [x] Fixture `dirty_sales_df` — same schema, but seeded with KNOWN defects: ≥50% nulls in `revenue` (triggers Critical completeness), duplicate row, non-monotonic date, one negative revenue (statistical red flag), one row with string `"N/A"` in the revenue column for dtype coercion testing
  - [x] Fixture `mock_llm_client` — returns a `unittest.mock.MagicMock` configured so `client.messages.parse(...)` returns a dummy object with `.output_parsed` set; Story 1.4 will flesh this out but a no-op stub is sufficient here
  - [x] Fixture `pipeline_run_id` — generates a `uuid.uuid4().hex` string per test
  - [x] Add a session-scoped autouse fixture that calls `configure_logging()` from Task 5 once per session so every test's log output is JSON-formatted
  - [x] Add a test file `backend/tests/test_conftest.py` that asserts each fixture loads and has expected shape — this satisfies "`pytest backend/tests/` runs successfully with at least the conftest fixtures validated"

- [x] **Task 7 — Six Day-1 tech debt fixes** (AC: 6 Day-1 items fixed)
  - See **"Day-1 Tech Debt Punch List"** below for the exact file-and-line targets. Each item is independently verifiable.

- [x] **Task 8 — Legacy STATUS headers** (AC: legacy STATUS comments)
  - [x] Prepend the exact STATUS block from [architecture.md:117-122](../planning-artifacts/architecture.md) to each of: `backend/advanced_pipeline.py`, `backend/comprehensive_analytics.py`, `backend/nlp_processor.py`, `backend/main.py`, `backend/dashboard_api.py`
  - [x] Note: `backend/main_enhanced.py` is separately labeled "do not use (hardcoded credentials)" in [architecture.md:686](../planning-artifacts/architecture.md) — it gets a **stronger** STATUS header: `# STATUS: DO NOT USE — hardcoded credentials. Replaced by Phase 3 api/ router.`
  - [x] `backend/analytics.py` is labeled "LEGACY — deprecate" in [architecture.md:684](../planning-artifacts/architecture.md) — also gets a STATUS header
  - [x] `backend/cleaner.py` is "EXISTING — reuse as-is (factory refactor only)" — do NOT add a legacy STATUS header; out of scope for this story

- [x] **Task 9 — .env.example** (AC: `.env.example`)
  - [x] Create `.env.example` at repo root with placeholder keys and NO real values:
    ```
    # Anthropic (Phase 1 narrative generator)
    ANTHROPIC_API_KEY=

    # OpenAI fallback (Phase 1 narrative generator)
    OPENAI_API_KEY=

    # Google (Gemini) fallback (Phase 1 narrative generator)
    GOOGLE_API_KEY=

    # Supabase — UNIFIED single project starting Phase 3 (do NOT commit real keys)
    SUPABASE_URL=
    SUPABASE_ANON_KEY=
    SUPABASE_SERVICE_ROLE_KEY=

    # Frontend equivalents (Vite reads VITE_*-prefixed vars)
    VITE_SUPABASE_URL=
    VITE_SUPABASE_ANON_KEY=
    ```
  - [x] Confirm `.env` (actual secrets) is in `.gitignore` — it already is per [.gitignore:32](../../.gitignore)
  - [x] Do NOT commit any real Supabase URLs, anon keys, or service role keys

- [x] **Task 10 — Verification pass** (AC: `pytest backend/tests/` green)
  - [x] Run `pytest backend/tests/` from repo root; all conftest-validation tests pass
  - [x] Run `python -c "from backend.errors.exceptions import SavvyCleanseError, LLMProviderError; raise LLMProviderError('test')"` and confirm the exception type chain is correct
  - [x] Run `python -c "from backend.models.pipeline_result import PipelineResult; print(PipelineResult(success=True))"` and confirm it instantiates
  - [x] Run `python -c "from backend.pipeline.config import configure_logging, bind_pipeline_run_id; configure_logging(); bind_pipeline_run_id('abc'); import structlog; structlog.get_logger().info('scaffolding_verified')"` and confirm the output is JSON with `pipeline_run_id=abc`
  - [x] grep for anti-patterns one more time — zero hits allowed in files NOT marked LEGACY: `warnings.filterwarnings`, `DATA_STORAGE`, bare `print(` (in non-CLI code), hardcoded `https://*.supabase.co`

---

## Day-1 Tech Debt Punch List

The architecture references "6 Day-1 tech debt items" ([architecture.md:111](../planning-artifacts/architecture.md), [architecture.md:957](../planning-artifacts/architecture.md)) but does not enumerate them in one place. They are derived from the Anti-Patterns list at [architecture.md:549-556](../planning-artifacts/architecture.md) and the Cross-Cutting Concerns at [architecture.md:60-65](../planning-artifacts/architecture.md), cross-referenced against [project-context.md:168](../project-context.md). Canonical list — fix all six:

| # | Item | Location (verified) | Fix |
|---|------|---------------------|-----|
| 1 | `warnings.filterwarnings('ignore')` | `backend/advanced_pipeline.py:10`, `backend/comprehensive_analytics.py:17` | Delete the line. These files now have a LEGACY STATUS header, so any warnings they raise are informational only. Do NOT suppress globally. |
| 2 | Hardcoded Supabase URL + anon key | `backend/main_enhanced.py:47-48` AND `src/integrations/supabase/client.ts:5-6` | Replace literal strings with `os.getenv("SUPABASE_URL")` / `os.getenv("SUPABASE_ANON_KEY")` (Python) and `import.meta.env.VITE_SUPABASE_URL` / `import.meta.env.VITE_SUPABASE_ANON_KEY` (TS). Raise `ConfigurationError` (Python) / throw (TS) if unset. NOTE: the Python file is already labeled DO-NOT-USE — still must be de-fanged so a future accidental import doesn't leak keys. |
| 3 | `DATA_STORAGE = {}` global mutable state | `backend/main.py:27`, `backend/main_enhanced.py:61` | Do NOT delete (Phase 3 replaces these files). Add a `# STATUS: LEGACY` header (Task 8) AND a `# DEBT: replaced by backend/db/ in Phase 3; do not import from new code` comment directly above the `DATA_STORAGE` declaration. |
| 4 | `print()` used for debugging | `backend/nlp_processor.py:342-344` | Delete the `if __name__ == "__main__":` demo block entirely — it was never production code and the file is now LEGACY. |
| 5 | Missing `SavvyCleanseError` hierarchy | — (does not exist yet) | Task 3 creates `backend/errors/exceptions.py`. Count this as a debt fix because before this story, any error raised by legacy modules propagates as unclassified `Exception`. |
| 6 | No type hints on legacy-adapted code boundaries | — (nothing to retrofit in this story) | Covered by convention going forward: every NEW function in `backend/pipeline/`, `backend/models/`, `backend/errors/` must have full type hints (Python rule from [project-context.md:58](../project-context.md)). Task 3 + Task 4 + Task 5 already satisfy this for the scaffolding. |

If any of these six are unfixable in the scope of this story (e.g., the hardcoded Supabase key cannot be rotated without access to the Supabase project), leave the file-level anti-pattern in place but:
1. Add an `# UNFIXED DEBT: <reason>` comment at the exact line,
2. Add a blocking item to the story's **Completion Notes List**,
3. Do NOT mark the story done.

---

## Dev Notes

### Developer Context — Why this story looks the way it does

1. **In-place evolution, not rewrite.** The legacy flat modules (`advanced_pipeline.py` et al.) stay where they are. This story adds `pipeline/`, `models/`, `agents/`, `renderers/`, `baselines/`, `errors/`, `tests/` **alongside** them. Do NOT move, rename, or delete legacy files. ([architecture.md:103-122](../planning-artifacts/architecture.md))
2. **Test pyramid before first pipeline stage.** The conftest fixtures are the foundation Stories 1.2–1.6 all consume. Get them right here — every subsequent test (test_data_quality, test_insight_engine, test_narrative_generator, test_renderers) extends these fixtures rather than defining its own. ([architecture.md:112](../planning-artifacts/architecture.md), [architecture.md:952-958](../planning-artifacts/architecture.md))
3. **Result-vs-Exception split is load-bearing.** `PipelineResult` is for business outcomes (bad data, critical halt). `SavvyCleanseError` subclasses are for infrastructure failures (disk full, network down, bad config). A wrong classification here will propagate through every subsequent story — it is cheaper to get it right now than to refactor later. ([architecture.md:482-506](../planning-artifacts/architecture.md))
4. **structlog context binding is the correlation-ID mechanism.** Every log line in a pipeline run will carry the same `pipeline_run_id`. This is how Story 1.6 (orchestrator) and Story 2.4 (monitoring agent) will correlate. Do NOT bake the run ID into logger names or pass it explicitly — use `bind_contextvars`. ([project-context.md:140-144](../project-context.md))
5. **This story has no pipeline logic.** If you find yourself writing a DataFrame transformation, STOP — that is Story 1.2. If you find yourself writing a Pydantic model for a quality report, STOP — that is also Story 1.2. This story's job is structural only.

### Project Structure Notes

- Scaffolding conforms to the **Target State** directory tree in [architecture.md:144-182](../planning-artifacts/architecture.md) — no deviations.
- `pyproject.toml` lives at **repo root**, NOT `backend/pyproject.toml` — per [architecture.md:574](../planning-artifacts/architecture.md) and [project-context.md:126](../project-context.md).
- `config.yaml` is NOT created in this story (Phase 2 concern — Story 2.1).
- `docker-compose.yml` + `Dockerfile` are NOT created in this story (Phase 5 concern — Story 5.5).
- No API routes exist yet — `backend/api/` is deferred to Phase 3 (Story 3.1).

### Architecture Compliance Checklist

| Rule | Source | How this story complies |
|------|--------|-------------------------|
| Three-layer separation (Presentation / Business / Data) | [architecture.md:741-747](../planning-artifacts/architecture.md) | Scaffolding creates directories matching the layer table; no cross-layer imports yet because stages are empty. |
| Pydantic models for all pipeline I/O | [project-context.md:59](../project-context.md) | `PipelineResult` is the only non-Pydantic type permitted (explicitly per architecture pattern). All other models land in Stories 1.2+. |
| structlog for all logging; never `print()` or `logging.basicConfig()` | [architecture.md:542](../planning-artifacts/architecture.md), [project-context.md:64](../project-context.md) | Task 5 configures structlog; Task 7 removes the only `print()` debug block. |
| Every module has a matching test file | [architecture.md:541](../planning-artifacts/architecture.md) | Task 6 adds `test_conftest.py` covering the fixtures; `exceptions.py` + `pipeline_result.py` are exercised by Task 10 verification but formal tests land in Stories 1.2 + 1.6 (reference them in Completion Notes). |
| No `import *`, no `except Exception: pass`, no hardcoded credentials | [project-context.md:148-156](../project-context.md) | Task 7 debt items 1, 2, 4. Enforce by grep in Task 10. |
| Type hints on every function signature | [project-context.md:58](../project-context.md) | All new Python code in this story is fully annotated. |

### Library / Framework Requirements

Use these exact versions — pinned for compatibility per [architecture.md:334-345](../planning-artifacts/architecture.md). Add them to a new `backend/requirements.txt` section (keep existing entries from the legacy file — this story does not remove them):

```
pydantic>=2.7          # Universal contract language
pandera==0.30.1        # DataFrame validation (Phase 1+)
structlog==25.5.0      # JSON structured logging
pytest>=8.2            # Test runner (pinned >= for forward-compat; pyproject pins exact minor)
pytest-cov             # Coverage (optional but helpful here)
python-dotenv>=1.0     # .env loader
```

Not needed in THIS story (referenced for context, introduced in later stories):
- `anthropic==0.79.0`, `docxtpl==0.20.2`, `WeasyPrint==68.1` — Story 1.4 / 1.5
- `typer==0.12.1` — Story 1.6
- `APScheduler`, `scipy.stats` — Phase 2

### File Structure Requirements

This story creates exactly these new files:

```
pyproject.toml                                     NEW (repo root)
.env.example                                       NEW (repo root)
backend/__init__.py                                NEW
backend/pipeline/__init__.py                       NEW
backend/pipeline/config.py                         NEW (stubs + configure_logging)
backend/models/__init__.py                         NEW
backend/models/pipeline_result.py                  NEW
backend/agents/__init__.py                         NEW
backend/renderers/__init__.py                      NEW
backend/renderers/templates/.gitkeep               NEW
backend/baselines/.gitkeep                         NEW
backend/errors/__init__.py                         NEW
backend/errors/exceptions.py                       NEW
backend/tests/__init__.py                          NEW
backend/tests/conftest.py                          NEW
backend/tests/test_conftest.py                     NEW
```

And modifies these existing files (headers/small edits only):

```
backend/advanced_pipeline.py          MODIFIED — STATUS header + remove warnings.filterwarnings
backend/comprehensive_analytics.py    MODIFIED — STATUS header + remove warnings.filterwarnings
backend/nlp_processor.py              MODIFIED — STATUS header + remove __main__ print block
backend/main.py                       MODIFIED — STATUS header + DEBT comment above DATA_STORAGE
backend/main_enhanced.py              MODIFIED — stronger STATUS header + env-var load for Supabase keys
backend/dashboard_api.py              MODIFIED — STATUS header
backend/analytics.py                  MODIFIED — STATUS header (deprecate note)
backend/requirements.txt              MODIFIED — append Phase 1 deps listed above
src/integrations/supabase/client.ts   MODIFIED — env-var load via import.meta.env
```

Do NOT create any file not on these two lists. Do NOT touch `backend/cleaner.py` (reserved for a factory refactor in a later story).

### Testing Requirements

**Framework:** pytest (backend) — this is the first story to set it up. No vitest setup in this story (first frontend story will add it).

**Test location:** `backend/tests/` — mirror source structure (NOT co-located). [architecture.md:388](../planning-artifacts/architecture.md)

**What this story must test:**
- `test_conftest.py`:
  - `clean_sales_df` has expected shape `(50, 3)`, no nulls, dtypes correct
  - `dirty_sales_df` has the seeded defects (≥50% nulls in `revenue`, at least one duplicate row, at least one negative revenue, at least one non-numeric string in revenue)
  - `mock_llm_client` is a `MagicMock` and `client.messages.parse()` returns an object with an `output_parsed` attribute
  - `pipeline_run_id` returns a 32-char hex string and differs across two invocations
  - After the autouse `configure_logging` fixture runs, a call to `structlog.get_logger().info("probe")` writes valid JSON to stderr (capture via `capsys`)

**What this story does NOT need to test:**
- Any pipeline logic (no pipeline logic exists yet)
- `SavvyCleanseError` hierarchy semantics (covered by the verification commands in Task 10; formal unit tests land in Story 1.2 where exceptions are first raised)
- `PipelineResult` serialization (land in Story 1.6 where the orchestrator first returns one)

**Coverage target:** N/A for this story — there's almost nothing to cover. Real coverage enforcement begins Story 1.2.

### Previous Story Intelligence

None — this is the first story of the project.

### Git Intelligence Summary

Recent commits on `main` (pre-scaffolding) show the team has been wiring the React dashboard to a mock Supabase backend:
- `97e3f7f` — Add BMad planning artifacts, project context, and sprint tracking (this session)
- `10519ac` — Connect analytics mock backend
- `113ab67` / `75ab05c` — Remove dead backend proxy
- `7318f01` — Connect analytics backend
- `27d5130` — Add multi-dataset manager

**Implication for this story:** the frontend `src/integrations/supabase/client.ts` is **actively used** by the dashboard. The hardcoded-key fix (Debt item #2) will break the running dashboard if `.env` isn't populated. Ship the fix together with a local `.env` (gitignored) containing real values, and document the required vars in the PR description so other worktrees can replicate.

### Latest Technical Information (verified versions)

| Library | Version | Notes relevant to this story |
|---------|---------|------------------------------|
| structlog | 25.5.0 | `bind_contextvars` is the supported API for correlation IDs. Avoid the older `structlog.threadlocal` API — it's soft-deprecated. |
| Pandera | 0.30.1 | Not used in this story (first use is Story 1.2). Listed so `backend/requirements.txt` includes it now and avoids a follow-up install in the next PR. |
| Pydantic | v2 (>=2.7) | Bundled with FastAPI. `@dataclass` (stdlib) is used for `PipelineResult`, NOT `pydantic.dataclasses.dataclass`, per the architecture pattern at [architecture.md:486-494](../planning-artifacts/architecture.md). |
| pytest | >=8.2 | Use `pyproject.toml`-based config, NOT `pytest.ini`. |
| python-dotenv | >=1.0 | Used to resolve env vars for Debt item #2. Do NOT auto-load at import of `backend/__init__.py`; explicit loading only. |

### References

All technical details cite source paths and sections:
- User story + BDD AC: [epics.md:218-237](../planning-artifacts/epics.md)
- Legacy STATUS header boilerplate: [architecture.md:117-122](../planning-artifacts/architecture.md)
- Error hierarchy shape: [architecture.md:496-504](../planning-artifacts/architecture.md)
- `PipelineResult` shape: [architecture.md:486-494](../planning-artifacts/architecture.md)
- Directory tree (target state): [architecture.md:144-182](../planning-artifacts/architecture.md), extended at [architecture.md:562-688](../planning-artifacts/architecture.md)
- Three-layer boundaries: [architecture.md:741-747](../planning-artifacts/architecture.md)
- Anti-patterns (9 rules): [architecture.md:549-556](../planning-artifacts/architecture.md)
- structlog configuration guidance: [architecture.md:458-464](../planning-artifacts/architecture.md), [project-context.md:30](../project-context.md)
- Phase 1 DoD (context): [prd.md:79-85](../planning-artifacts/prd.md)
- Phase 1 first-commit checklist: [architecture.md:107-112](../planning-artifacts/architecture.md), [architecture.md:952-958](../planning-artifacts/architecture.md)
- AI-agent ruleset (60 rules): [project-context.md](../project-context.md) — read before implementing

---

## Project Context Reference

Load [project-context.md](../project-context.md) before you start. Specifically relevant for this story:
- **Technology Stack & Versions** ([project-context.md:24-49](../project-context.md)) — confirm Python 3.13 and the Phase 1 dep set
- **Language-Specific Rules → Python** ([project-context.md:57-64](../project-context.md)) — type hints required, no `print()`, no `except Exception: pass`, no `warnings.filterwarnings('ignore')`, no wildcard imports
- **Framework-Specific Rules → Pipeline** ([project-context.md:79-84](../project-context.md)) — composable stages returning Pydantic models, `PipelineResult` for expected outcomes, exceptions for unexpected
- **Testing Rules → Backend** ([project-context.md:93-98](../project-context.md)) — tests in `backend/tests/` (NOT co-located), shared fixtures in conftest, every new module needs a matching test file
- **Code Quality & Style Rules → Naming** ([project-context.md:106-110](../project-context.md)) — module `snake_case.py`, classes `PascalCase`, functions `snake_case()`, private `_prefix`
- **Code Quality & Style Rules → Layer boundaries** ([project-context.md:112-118](../project-context.md)) — presentation / business / data separation
- **Critical Don't-Miss Rules → Anti-patterns** ([project-context.md:148-156](../project-context.md)) — Task 7 debt items derived directly from this list
- **Critical Don't-Miss Rules → Security** ([project-context.md:158-161](../project-context.md)) — `main_enhanced.py` + `supabase/client.ts` hardcoded credentials flagged for immediate rotation
- **Critical Don't-Miss Rules → Day-1 tech debt** ([project-context.md:168-169](../project-context.md)) — this story IS that item

---

## Dev Agent Record

### Agent Model Used

_(to be filled by dev-story workflow)_

### Debug Log References

_(to be filled during implementation — include any structlog JSON snippets that verify correlation IDs work)_

### Completion Notes List

_(to be filled on completion — flag any UNFIXED debt items here)_

### File List

_(enumerated on completion — should match the "File Structure Requirements" section above; any deviation requires a note)_

---

## Story Completion Status

- **Status:** done
- **Completion note:** Ultimate context engine analysis completed — comprehensive developer guide created. All 6 Day-1 tech debt items have verified file-and-line targets. No prior story context applies (this is Story 1.1). Scaffolding paths align with the architecture target-state tree without deviations. Verification commands in Task 10 give the dev agent a deterministic done/not-done signal.
