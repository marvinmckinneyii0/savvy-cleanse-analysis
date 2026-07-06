# Story 2.1: Configuration Layer

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

> 🧭 **First story of Epic 2 (Automation).** This is the foundation every other Epic 2 story
> consumes: the Drift Engine (2.2) reads threshold/baseline settings, the Reporting Agent (2.3)
> reads `data_sources` + `report_schedule` and hot-reloads config per scheduled run, and the
> Monitoring Agent (2.4) reads `metric_thresholds` + `alert_recipients` + SMTP secrets. Design the
> schema as a coherent whole now — getting it wrong forces rework across 2.2–2.4.
>
> ⚠️ **Resolve the `PipelineConfig` location conflict before coding** (see Dev Notes →
> "Architectural decision: where PipelineConfig lives"). The epics AC and the architecture target
> tree point at two different files. The prescribed resolution is below — follow it exactly.

## Story

As a developer,
I want a YAML/JSON configuration file that defines data sources, report schedules, metric thresholds, and alert recipients,
so that agents can be configured without code changes and settings can be modified at runtime.

## Acceptance Criteria

1. **Config file + schema exist.** Given a project root directory, when the configuration layer is
   initialized, then a `config.yaml` at project root defines: `data_sources` (list of file paths or
   directories), `report_schedule` (interval `daily`/`weekly`/`monthly` **or** a cron expression),
   `metric_thresholds` (per-metric fractional change thresholds, default `0.15` = ±15%),
   `alert_recipients` (list of email addresses), and `output` settings (format, output directory);
   and `PipelineConfig` is a **Pydantic v2** model that validates and loads this config.

2. **Invalid config raises `ConfigurationError`.** Given invalid config values — missing required
   fields, an invalid cron expression, a negative or zero threshold, or a malformed email — when the
   config is loaded, then `ConfigurationError` is raised with a descriptive message naming the
   offending field. Pydantic `ValidationError` must NOT escape the loader uncaught; it is caught and
   re-raised as `ConfigurationError`.

3. **Typed load.** Given a valid `config.yaml` exists, when any agent or pipeline component calls
   `PipelineConfig.load()` (path optional; defaults to `config.yaml` at project root), then the
   configuration is loaded, validated, and returned as a typed `PipelineConfig` instance.

4. **Env overrides for secrets.** Given the config references secrets (SMTP credentials, API keys),
   when `PipelineConfig.load()` runs, then those secrets are sourced from environment variables
   (loaded via `.env` in dev through python-dotenv) — **never** read from `config.yaml`. `config.yaml`
   contains only non-secret structure. `.env.example` is updated with the new `SMTP_*` placeholders.

5. **Runtime modification / reload (FR10).** Given a `config.yaml` is modified on disk, when a caller
   invokes `PipelineConfig.load()` again (the mechanism a scheduled agent uses on its next run), then
   the returned instance reflects the updated thresholds, schedules, and recipients — no process
   restart and no module reimport required. (`load()` is stateless: it re-reads and re-validates the
   file on every call. A live file-watcher / APScheduler hot-reload loop is **2.3's** scope, not this
   story's.)

6. **Observability + tests.** Given any configuration load, when the config is parsed, then a
   structlog entry is emitted with `event="config_loaded"` and a summary of active settings **with no
   secrets** (recipient count, schedule, threshold keys — never SMTP password or API keys); and
   `backend/tests/test_config.py` passes with tests covering: valid config, missing required fields,
   invalid values (bad cron, negative threshold, bad email), environment-variable override, and
   reload-reflects-changes behavior.

## Tasks / Subtasks

- [ ] **Task 0 — Resolve schema location & read the existing stub** (AC: 1, 3)
  - [ ] Read `backend/pipeline/config.py` — it currently holds `configure_logging()`,
        `bind_pipeline_run_id()`, and a **stub stdlib `@dataclass PipelineConfig`** (empty). Do NOT
        delete the logging functions — `conftest.py:20` imports `configure_logging` from here and the
        whole suite depends on it.
  - [ ] Follow the prescribed resolution in Dev Notes: define the Pydantic models in
        `backend/models/pipeline_config.py`; replace the stub in `pipeline/config.py` with a
        re-export so `from backend.pipeline.config import PipelineConfig` keeps working.

- [ ] **Task 1 — Define the Pydantic config contract** `backend/models/pipeline_config.py` (AC: 1, 2)
  - [ ] `ThresholdConfig` (or a `dict[str, float]` field with a validator) — per-metric fractional
        thresholds; default `DEFAULT_THRESHOLD = 0.15`; every value must be `> 0` (reject negative/zero).
  - [ ] `ScheduleConfig` — accepts either an interval enum (`daily`/`weekly`/`monthly`) or a cron
        string; validate cron via `croniter` (raise on malformed). Exactly one of interval/cron.
  - [ ] `DataSourceConfig` — list of file paths or directories (non-empty list of `str`/`Path`).
  - [ ] `OutputConfig` — `format` (`docx`/`pdf`, default `docx`), `output_dir` (default `output/`).
  - [ ] `AlertConfig` — `recipients: list[EmailStr]` (validate email format via Pydantic `EmailStr`).
  - [ ] Root `PipelineConfig(BaseModel)` composing the above, plus a `@classmethod load(cls, path: str
        | Path | None = None) -> "PipelineConfig"` that reads YAML, merges env-sourced secrets, and
        validates. Use `model_config = ConfigDict(...)` per Pydantic v2.

- [ ] **Task 2 — Implement the loader** `PipelineConfig.load()` (AC: 2, 3, 4, 5, 6)
  - [ ] Default path = `config.yaml` at project root; accept an explicit path for tests.
  - [ ] Parse with `yaml.safe_load` (PyYAML). JSON is a valid subset — `safe_load` reads `.json` too;
        no separate JSON branch needed (note this in a comment).
  - [ ] Call `load_dotenv()` (python-dotenv) then read `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`,
        `SMTP_PASSWORD`, `SMTP_FROM` from `os.environ`. Surface them on the typed config (e.g., an
        `SmtpSettings` sub-object) — but they originate ONLY from env, never from the YAML.
  - [ ] Wrap `pydantic.ValidationError`, `yaml.YAMLError`, and `FileNotFoundError` in
        `ConfigurationError` with a descriptive message (AC2). Re-read on every call (AC5 — no caching).
  - [ ] Emit `structlog.get_logger().info("config_loaded", schedule=..., threshold_keys=...,
        recipient_count=..., output_format=...)` — **assert no secret values are in the log payload.**

- [ ] **Task 3 — Replace the stub & wire exports** `backend/pipeline/config.py` (AC: 3)
  - [ ] Remove the empty `@dataclass PipelineConfig`; add `from backend.models.pipeline_config import
        PipelineConfig` (re-export) so both import paths resolve to the one Pydantic model.
  - [ ] Update the module docstring: the "full config surface lands in Story 1.6" note is stale —
        replace with "config schema defined in Story 2.1; see `backend/models/pipeline_config.py`".
  - [ ] Keep `configure_logging()` and `bind_pipeline_run_id()` exactly as-is.

- [ ] **Task 4 — Author `config.yaml` + update `.env.example` + `pyproject.toml`** (AC: 1, 4)
  - [ ] Create `config.yaml` at repo root with a documented, working example (see Dev Notes for the
        canonical shape). Comment each section. NO secrets in it.
  - [ ] Add to `.env.example`: `SMTP_HOST=`, `SMTP_PORT=587`, `SMTP_USERNAME=`, `SMTP_PASSWORD=`,
        `SMTP_FROM=` under a `# SMTP — Phase 2 alert delivery` header.
  - [ ] Add deps to **both** `pyproject.toml` `dependencies` **and** `backend/requirements.txt`:
        `pyyaml>=6.0`, `croniter>=2.0`, `email-validator>=2.0` (required by Pydantic `EmailStr`), and
        reconcile `python-dotenv>=1.0` (already in `requirements.txt`, **missing from `pyproject.toml`** —
        add it there). The two files are hand-maintained and already drift (`docxtpl`/`weasyprint`/
        `jinja2`/`typer` are in `pyproject.toml` only; `pandera`/`pytest`/`python-dotenv` in
        `requirements.txt` only) — do **not** "fix" that pre-existing drift in this story, just ensure
        the four config deps land in both. Verify with:
        `grep -iE 'pyyaml|croniter|email-validator|python-dotenv' pyproject.toml backend/requirements.txt`

- [ ] **Task 5 — Tests** `backend/tests/test_config.py` (AC: 2, 3, 4, 5, 6)
  - [ ] Valid config → typed `PipelineConfig`, defaults applied (threshold `0.15`, format `docx`).
  - [ ] Missing required field → `ConfigurationError` (not bare `ValidationError`).
  - [ ] Invalid values: malformed cron, negative threshold, bad email → each raises `ConfigurationError`.
  - [ ] Env override: set `SMTP_PASSWORD` via `monkeypatch.setenv`, assert it lands on the config and
        is absent from any YAML on disk.
  - [ ] Reload: write `config.yaml` to `tmp_path`, `load()`, mutate the file, `load()` again, assert
        the second instance reflects the change.
  - [ ] Use `tmp_path` for all file I/O — never write to the real repo-root `config.yaml`.
  - [ ] Capture logs (e.g., `structlog` testing capture or `caplog`) and assert `config_loaded` fires
        and the payload contains no secret values.

## Dev Notes

### Architectural decision: where `PipelineConfig` lives (READ FIRST)

There is a genuine conflict between two source documents — resolve it as prescribed, do not improvise:

- **Epics AC** (epics.md §419): "`backend/pipeline/config.py` defines a PipelineConfig Pydantic
  dataclass that validates and loads the YAML config" and references `PipelineConfig.load()`.
- **Architecture target tree** (architecture.md §600): `models/pipeline_config.py # PipelineConfig,
  ThresholdConfig` — i.e., the Pydantic contract belongs in the **models** layer, alongside every
  other Pydantic contract (`quality_report.py`, `insight_payload.py`, `pipeline_result.py`).
  Architecture.md §592 separately lists `pipeline/config.py # PipelineConfig dataclass` (the
  existing logging-host stub).

**Prescribed resolution (honors both):**
1. Define all Pydantic config models in **`backend/models/pipeline_config.py`** (matches the
   model-layer convention — Pydantic contracts live in `models/`, and the project rule is "Pydantic
   models for all pipeline I/O").
2. Put the `load()` classmethod **on the `PipelineConfig` model** so the `PipelineConfig.load()`
   call surface from the AC is satisfied.
3. In **`backend/pipeline/config.py`**, replace the empty stub dataclass with a re-export
   (`from backend.models.pipeline_config import PipelineConfig`). This keeps `from
   backend.pipeline.config import PipelineConfig` working (the path the epics AC implies) while the
   real definition lives where the architecture says it should. `models/` and `pipeline/` are both
   the **Business Logic** layer, so `pipeline/` importing from `models/` is allowed.

Note the existing stub's docstring claims the schema "lands in Story 1.6". Story 1.6 did **not**
expand it (it only built the orchestrator and left `PipelineConfig` empty — confirmed against the
1.6 story file and current `config.py`). **Story 2.1 is where the schema is actually defined.** Update
the stale docstring.

### Existing code you are extending (verified against `main`)

- `backend/pipeline/config.py` — holds `configure_logging()` (structlog JSON processor chain,
  idempotent) and `bind_pipeline_run_id()` (contextvars), plus the empty stub `PipelineConfig`. The
  logging functions are load-bearing: `backend/tests/conftest.py:20` imports `configure_logging` and a
  session-autouse fixture calls it. **Do not move or rename them.**
- `backend/errors/exceptions.py` — `ConfigurationError(SavvyCleanseError)` already exists and is
  documented for exactly this case: "Configuration is missing or invalid — pre-flight failure …
  `config.yaml` malformed". **Reuse it; do not create a new exception.** It is a *sibling* of
  `PipelineStageError`, not a child — a bad config is pre-flight, not a stage failure.
- `backend/models/__init__.py` is empty (1 line); models are imported by full path, not re-exported
  through the package. Follow that convention — import `from backend.models.pipeline_config import
  PipelineConfig`, don't add package-level re-exports.
- Pydantic style to match (see `backend/models/insight_payload.py`): `from __future__ import
  annotations`, `from pydantic import BaseModel`, module docstring, `X | None = None` optionals,
  PascalCase noun models, snake_case fields.

### Canonical `config.yaml` shape (author this)

```yaml
# SavvyCortex pipeline configuration (Phase 2). Secrets live in .env, NOT here.
data_sources:
  - data/sales.csv            # file path(s) or directory(ies) the agents pull from

report_schedule:
  interval: weekly            # one of: daily | weekly | monthly
  # cron: "0 6 * * 1"         # OR a cron expression (mutually exclusive with interval)

metric_thresholds:            # per-metric fractional change; 0.15 == ±15%
  revenue: 0.15
  units_sold: 0.20

alert_recipients:
  - ops@example.com

output:
  format: docx                # docx | pdf
  output_dir: output/
```

### Dependencies & versions

- **PyYAML `>=6.0`** — `yaml.safe_load` (NEVER `yaml.load` without a safe loader — arbitrary-object
  deserialization is an injection vector; NFR4 input sanitization). JSON is a strict subset of YAML, so
  `safe_load` parses `.json` config too — no separate parser needed.
- **python-dotenv `>=1.0`** — already declared in `backend/requirements.txt` but missing from
  `pyproject.toml`; this story aligns them. Used elsewhere as `os.environ.get(...)`
  (`narrative_generator.py:229`). Call `load_dotenv()` inside `load()`.
- **croniter `>=2.0`** — validates cron expressions (`croniter.is_valid(expr)`). This is the one new
  runtime dep justified by AC2 ("invalid cron expressions … raise ConfigurationError"). APScheduler
  (architecture.md §230) is the *scheduler* and arrives in **2.3** — do not pull it in here just to
  validate a string.
- **email-validator `>=2.0`** — transitive requirement for Pydantic `EmailStr`; declare it explicitly.
- Python 3.13, Pydantic v2 (`>=2.0`, already pinned), structlog (already pinned). No version conflicts.

### Secrets discipline (NFR3, project-context.md anti-patterns)

- **No secrets in `config.yaml`.** SMTP host/port may be non-secret config, but credentials
  (`SMTP_USERNAME`, `SMTP_PASSWORD`) and API keys come from env only. The convention in this repo is
  `os.environ.get("X_API_KEY")` (narrative_generator). Keep SMTP creds in env to match.
- **Never log secrets.** The `config_loaded` event logs a *summary* — schedule, threshold keys,
  recipient count, output format. Never the SMTP password, never API keys, never full recipient
  addresses if you want to be conservative (count is enough). Project rule: "NEVER log: API keys, raw
  row data, PII". Treat recipient emails as PII-adjacent — log the count, not the list.

### Error model (errors/exceptions.py, project-context.md)

- Bad config is a **pre-flight `ConfigurationError`** (raised before any stage runs) — it is an
  *exception*, not a `PipelineResult(halted=True)`. The Result-vs-Exception split: "bad data" → Result;
  "config missing/invalid" → `ConfigurationError`. This story only ever raises the exception.
- Forbidden (project-context.md): `except Exception: pass`, bare `print()` (use structlog), wildcard
  imports, hardcoded keys, untyped dict-in/dict-out at boundaries. The loader must return a typed
  `PipelineConfig`, never a raw dict.

### Layer boundaries (project-context.md)

- `models/pipeline_config.py` and `pipeline/config.py` are both **Business Logic**. They may import
  `errors/`, `models/`, stdlib, and third-party libs. They must **NOT** import from `api/`, `agents/`,
  `renderers/`, or any **legacy** module (`advanced_pipeline.py`, `comprehensive_analytics.py`,
  `nlp_processor.py`, `analytics.py`, `main.py`, `main_enhanced.py`, `dashboard_api.py`).
- `main_enhanced.py` reads SMTP/Supabase env vars but is **legacy with hardcoded creds — do not
  reference it** even though it touches similar concerns.

### Testing standards (project-context.md; conftest.py)

- Tests live in `backend/tests/` (NOT co-located). New file: `backend/tests/test_config.py` (mirror
  rule: tests `models/pipeline_config.py` + `pipeline/config.py`).
- The session-autouse fixture in `conftest.py` already calls `configure_logging()`, so structlog is
  JSON-configured during tests. To assert on the `config_loaded` event, use `structlog`'s capture
  (`structlog.testing.capture_logs()`) rather than `caplog` for reliable structured-event assertions.
- Use the `tmp_path` fixture for every config-file write. Do **not** create or mutate the real
  repo-root `config.yaml` in tests.
- Regression baseline: the suite was green at the end of Epic 1 (1.6 reported 110 passed, 1 skipped).
  Run `pytest backend/tests/` — expect zero regressions plus the new `test_config.py`.

### Cross-story forward-compatibility (design the schema for these consumers)

- **2.2 Drift Engine** — needs threshold semantics for HIGH/MEDIUM/LOW severity and baseline pathing
  (baselines stored as JSON in `backend/baselines/`). Keep `metric_thresholds` generic enough that
  drift checks can read per-column thresholds.
- **2.3 Reporting Agent** — reads `data_sources`, `report_schedule`, `output`; calls `load()` at the
  start of each scheduled run for hot-reload. Keep `load()` cheap and side-effect-free (besides the log).
- **2.4 Monitoring Agent** — reads `metric_thresholds`, `alert_recipients`, and SMTP env settings;
  the `type: mean_shift, column: revenue, threshold: 0.15` rule shape (architecture.md §474) will be
  layered on top later. Don't build alert-rule objects here — just the threshold/recipient surface.

### Project Structure Notes

- New files: `backend/models/pipeline_config.py`, `backend/tests/test_config.py`, root `config.yaml`.
- Modified: `backend/pipeline/config.py` (stub → re-export + docstring), `.env.example` (+SMTP),
  `pyproject.toml` (+4 deps), `backend/requirements.txt` (same 4 deps, mirrored — see Task 4).
- `output/` is gitignored (architecture.md §733); the default `output_dir` pointing there is correct.
  Tests write to `tmp_path`, not `output/`.
- No variance from the architecture target tree — `models/pipeline_config.py` and root `config.yaml`
  both appear in it (architecture.md §571, §600).

### Definition of Done (sprint-status.yaml, applies from Story 1.4 onward)

- All acceptance criteria met; unit tests pass; zero regressions in `pytest backend/tests/`.
- Run `/security-review` and resolve all Critical/High findings before marking done. Pay attention to:
  YAML deserialization safety (`safe_load` only), no secrets in `config.yaml` or logs, and that
  `ConfigurationError` messages don't leak secret values.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.1: Configuration Layer] (AC source)
- [Source: _bmad-output/planning-artifacts/architecture.md#L571] (config.yaml at root — Phase 2)
- [Source: _bmad-output/planning-artifacts/architecture.md#L592-L600] (config.py vs models/pipeline_config.py — the location conflict)
- [Source: _bmad-output/planning-artifacts/architecture.md#L230] (Phase 2 stack: APScheduler/cron, smtplib — APScheduler deferred to 2.3)
- [Source: _bmad-output/planning-artifacts/architecture.md#L400-L401] (pipeline/config.py vs user-facing config.yaml)
- [Source: _bmad-output/project-context.md#Config files] (config.yaml at project root; .env for secrets)
- [Source: backend/pipeline/config.py] (existing stub + configure_logging/bind_pipeline_run_id — do not break)
- [Source: backend/errors/exceptions.py] (ConfigurationError — reuse, pre-flight sibling of PipelineStageError)
- [Source: backend/models/insight_payload.py] (Pydantic v2 style to match)
- [Source: backend/tests/conftest.py] (configure_logging import at :20; session-autouse logging fixture)

## Dev Agent Record

### Agent Model Used

claude-fable-5 (Claude Code, autonomous scheduled run 2026-07-06)

### Debug Log References

- Baseline before implementation: `pytest backend/tests/` → 123 passed, 1 skipped
  (pre-existing skip: `anthropic` not installed in the env).
- After implementation: 152 passed, 1 skipped — 29 new tests in `test_config.py`,
  zero regressions.

### Completion Notes List

- Followed the prescribed `PipelineConfig` location resolution exactly: Pydantic
  models live in `backend/models/pipeline_config.py`; `backend/pipeline/config.py`
  re-exports `PipelineConfig` so both import paths resolve to one class.
  `configure_logging()` / `bind_pipeline_run_id()` untouched.
- Root model uses `ConfigDict(extra="forbid")`, which structurally enforces
  "no secrets in config.yaml": an `smtp:` section (or any typo'd key) is a
  `ConfigurationError`, not silently ignored.
- `SmtpSettings.password` is a Pydantic `SecretStr` and the whole `smtp` field
  is `exclude=True`, so credentials never appear in reprs, validation errors,
  or `model_dump_json()`.
- Per-metric threshold fallback exposed as `PipelineConfig.threshold_for(metric)`
  with module constant `DEFAULT_THRESHOLD = 0.15` for the Drift Engine (2.3)
  and Monitoring Agent (2.4).
- Deps added to BOTH `pyproject.toml` and `backend/requirements.txt`:
  pyyaml>=6.0, croniter>=2.0, email-validator>=2.0; python-dotenv>=1.0 added to
  pyproject (already in requirements.txt). Pre-existing manifest drift left
  as-is per Task 4. `uv.lock` updated via `uv sync`.
- Code review (fresh-context subagent) and security review both completed:
  **zero Critical, zero High**. All Medium findings fixed before commit:
  (a) explicit rejection of an `smtp:` section in config.yaml with a message
  pointing at the env-var mechanism (was an accidental `TypeError` path),
  plus a regression test pinning that YAML smtp values can never win over env;
  (b) threshold validator now rejects NaN/inf (`math.isfinite`), closing the
  "drift alerts silently never fire" hole; (c) invalid SMTP env values now
  raise a `ConfigurationError` naming the env var (e.g. `SMTP_PORT`) instead
  of blaming config.yaml; (d) `smtp` field is `repr=False` so a logged config
  object never prints SMTP host/username; (e) empty-string `data_sources`
  entries rejected (would coerce to `Path('.')`); (f) dotenv anchored to the
  repo root and neutralized in the env-unset test (was dev-machine flaky);
  (g) `[dependency-groups] dev` added so `uv run pytest backend/tests/` works
  out of the box. Accepted as informational: YAML duplicate-key last-wins
  (PyYAML default), safe_load resource bounds, error messages echoing YAML
  parse context — all operator-trusted local-CLI surfaces.
- Final suite: 158 passed, 1 skipped (pre-existing `anthropic` skip).

### File List

- `backend/models/pipeline_config.py` (new)
- `backend/tests/test_config.py` (new)
- `config.yaml` (new, repo root)
- `backend/pipeline/config.py` (modified — stub → re-export, docstring updated)
- `.env.example` (modified — SMTP block)
- `pyproject.toml` (modified — 4 config deps)
- `backend/requirements.txt` (modified — 3 config deps; dotenv pre-existing)
- `uv.lock` (regenerated)
