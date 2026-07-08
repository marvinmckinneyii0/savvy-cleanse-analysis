# Story 2.2b: Harden LLMClient for Multi-Caller Use

Status: done

> 🔧 **Corrective story — filed from code review of Story 2.2.** The 2.2 code review
> (scoped question: "does the self-contained `bind_pipeline_run_id` placement create
> hidden coupling for the direct callers 2.3/2.4 will introduce?") confirmed three
> concrete issues in `backend/core/llm_client.py`. Story 2.2's own behavior
> (single caller: `NarrativeGenerator` via `orchestrator.py`) is unaffected and stays
> shipped — this story hardens `LLMClient` before Reporting Agent (2.3) and Monitoring
> Agent (2.4) become direct callers.

## Story

As a developer,
I want `LLMClient` decoupled from `backend/pipeline/` and safe under direct,
repeated, or concurrent invocation,
so that the Reporting Agent (2.3) and Monitoring Agent (2.4) can call it without
inheriting pipeline-package internals, without silently losing JSON log output, and
without leaking `pipeline_run_id` into unrelated log lines on a reused thread/task.

## Acceptance Criteria

1. **`backend/core/llm_client.py` no longer imports from `backend/pipeline/`.**
   The shared logging/context-binding primitives (`configure_logging`,
   `bind_pipeline_run_id`) move to a new `backend/core/logging.py`.
   `backend/pipeline/config.py` retains only `PipelineConfig`. Every existing call
   site (`orchestrator.py`, `llm_client.py`, `conftest.py`, `test_insight_engine.py`,
   `test_narrative_generator.py`) imports from the new location. No change to what
   gets logged or how — this is a pure move.

2. **JSON logging is guaranteed for callers who never call `configure_logging()`,
   without clobbering callers/tests who already configured structlog.** Given
   structlog is already configured (e.g. a test's `LogCapture` fixture, or a caller's
   own prior `configure_logging()` call), when `LLMClient.generate_narrative()` runs,
   then it must NOT reconfigure structlog (existing processor chain — including test
   capture processors — must survive the call untouched). Given structlog is
   unconfigured (a bare direct call with no setup, e.g. a future agent that forgets
   the setup step), when `generate_narrative()` runs, then it must configure JSON
   logging itself so `narrative_generated` / `llm_fallback` / `llm_retry` /
   `llm_client_error` / `llm_circuit_breaker` events are emitted as JSON, not the
   structlog default renderer.

3. **`pipeline_run_id` binding is scoped to the call, not leaked to the ambient
   context.** `LLMClient.generate_narrative()` must restore whatever contextvars
   state existed before the call once it returns (success or exception) — a
   subsequent, unrelated log line on the same thread/asyncio task must never carry a
   stale `pipeline_run_id` from a prior call. This must NOT break the existing
   single-caller pipeline flow: `orchestrator.py` binds `pipeline_run_id` once at the
   top of `run_full_pipeline()` and expects Stage 4 (render) logs, which run *after*
   `NarrativeGenerator.generate()` returns, to still carry that same
   `pipeline_run_id`. The fix must restore the orchestrator's own outer binding, not
   clear it to nothing.

4. **No regressions.** All existing tests pass with only import-path changes — no
   test assertion is added, removed, or altered in `test_narrative_generator.py`,
   `test_insight_engine.py`, or `conftest.py` beyond the import statement. New tests
   added for AC2 and AC3 (see Tasks). Full suite green.

## Tasks / Subtasks

- [x] **Task 1 — Create `backend/core/logging.py`** (AC: 1, 2, 3)
  - [x] Move `configure_logging()` and `bind_pipeline_run_id()` verbatim from
        `backend/pipeline/config.py` (docstrings included).
  - [x] Add `ensure_logging_configured() -> None`: calls `configure_logging()` only
        if `structlog.is_configured()` is `False`. This is the guard that satisfies
        AC2 without clobbering an already-configured caller or test.
  - [x] Add `scoped_pipeline_run_id(run_id: str)` — a `@contextlib.contextmanager`
        wrapping `structlog.contextvars.bound_contextvars(pipeline_run_id=run_id)`.
        `bound_contextvars` snapshots the current contextvars state on entry and
        restores exactly that snapshot on exit (whether the block raises or not) —
        this is what satisfies AC3 without any bespoke restore logic.
  - [x] Module docstring: state this module is the shared logging/context-binding
        primitive for both `pipeline/` and `agents/` — neither layer should import
        logging setup from the other.

- [x] **Task 2 — Trim `backend/pipeline/config.py`** (AC: 1)
  - [x] Remove `configure_logging()` and `bind_pipeline_run_id()` (now in
        `backend/core/logging.py`).
  - [x] Keep `PipelineConfig` dataclass unchanged.
  - [x] Update module docstring: the logging discipline notes now point to
        `backend/core/logging.py`; this file is pipeline-run configuration only.

- [x] **Task 3 — Update `backend/core/llm_client.py`** (AC: 1, 2, 3)
  - [x] Replace `from backend.pipeline.config import bind_pipeline_run_id` with
        `from backend.core.logging import ensure_logging_configured, scoped_pipeline_run_id`.
  - [x] At the top of `generate_narrative()`, call `ensure_logging_configured()`.
  - [x] Wrap the existing method body (from the provider loop through the
        circuit-breaker fallback return) in
        `with scoped_pipeline_run_id(pipeline_run_id):`. Indent only — no logic
        changes.

- [x] **Task 4 — Update `backend/pipeline/orchestrator.py`** (AC: 1)
  - [x] Change `from backend.pipeline.config import bind_pipeline_run_id, configure_logging`
        to `from backend.core.logging import bind_pipeline_run_id, configure_logging`.
        No other change — orchestrator keeps its whole-run (unscoped) binding at line
        ~86; that's correct for a one-shot CLI process and must not become scoped.

- [x] **Task 5 — Update test imports** (AC: 1, 4)
  - [x] `backend/tests/conftest.py`, `backend/tests/test_insight_engine.py`,
        `backend/tests/test_narrative_generator.py`: change
        `from backend.pipeline.config import configure_logging` to
        `from backend.core.logging import configure_logging`. No other changes.

- [x] **Task 6 — New tests: `backend/tests/test_llm_client_hardening.py`** (AC: 2, 3)
  - [x] Test: with structlog already configured via `LogCapture` (mirror the
        `log_capture` fixture pattern in `test_narrative_generator.py`), call
        `LLMClient().generate_narrative(...)` with `_call_claude` mocked to succeed;
        assert `log_capture.entries` contains the `narrative_generated` event —
        proving `ensure_logging_configured()` did not reconfigure structlog and blow
        away the capture processor.
  - [x] Test: reset structlog to unconfigured (`structlog.reset_defaults()` or
        equivalent) before the call; after calling `generate_narrative()`, assert
        `structlog.is_configured()` is `True` — proving the guard configures JSON
        logging when nothing else has.
  - [x] Test: bind an unrelated contextvar (or leave contextvars empty) before
        calling `generate_narrative(..., pipeline_run_id="run-A")`; after the call
        returns, assert `structlog.contextvars.get_contextvars()` no longer contains
        `pipeline_run_id` (or has been restored to its pre-call value) — proving
        AC3's scoped restore.
  - [x] Test: simulate the orchestrator pattern — call
        `bind_pipeline_run_id("run-B")` first (outer, whole-run binding), then call
        `LLMClient().generate_narrative(..., pipeline_run_id="run-B")`; after it
        returns, assert `pipeline_run_id` is STILL `"run-B"` in the ambient
        context — proving the scoped restore does not clear the orchestrator's own
        outer binding (this is the regression guard architecture.md/Stage 4 needs).

- [x] **Task 7 — Full suite regression** (AC: 4)
  - [x] Run `uv run pytest backend/tests/ --ignore=backend/tests/test_parse_file.py`
        (pre-existing `fastapi`-missing collection failure, unrelated).
  - [x] All previously-passing tests still pass; new tests from Task 6 pass; zero
        new failures.

## Dev Notes

### Why not just clear contextvars unconditionally after the call?

`structlog.contextvars.clear_contextvars()` would wipe *all* bound contextvars, not
just `pipeline_run_id` — and it would also break `orchestrator.py`'s existing
single-caller usage, where `pipeline_run_id` is bound once for the whole
`run_full_pipeline()` run and must still be present for Stage 4 (render) logging
after `NarrativeGenerator.generate()` (→ `LLMClient.generate_narrative()`) returns.
`structlog.contextvars.bound_contextvars(...)` is the correct primitive: it snapshots
and restores only the keys it touches, in a `try/finally`, which is exactly "restore
what was there before" rather than "wipe everything."

### Why not just have `LLMClient` unconditionally call `configure_logging()`?

`test_narrative_generator.py`'s `log_capture` fixture calls `structlog.configure()`
itself (with a `LogCapture` processor) specifically so tests can assert on emitted
events. If `generate_narrative()` unconditionally called `configure_logging()`, it
would silently replace that processor chain mid-test and every log-assertion test
would start failing (or silently stop capturing) the moment this story shipped.
`structlog.is_configured()` is the correct guard — it's `True` once *any* caller
(including a test fixture) has called `structlog.configure()`.

### Layering — where `backend/core/` sits

`architecture.md` §751-752: "`backend/pipeline/` is callable from both `api/` and
`agents/` but imports from neither." `backend/core/` (added in Story 2.2, not in the
original architecture target tree) is meant to be usable by both `pipeline/` and
`agents/` — the whole reason `LLMClient` was extracted there. A module in `core/`
importing from `pipeline/` inverts that: it means `agents/` (2.3, 2.4), which will
import `backend.core.llm_client`, transitively depends on `backend.pipeline.config`
for a concern (structured logging setup) that has nothing to do with the CSV
pipeline. Moving `configure_logging`/`bind_pipeline_run_id` to `backend/core/logging.py`
fixes the dependency direction: `pipeline/` and `agents/` both depend on `core/`,
`core/` depends on neither.

### Scope boundary

This story does NOT touch the retry/fallback/circuit-breaker logic, the provider
`_call_*` methods, or any structlog event name/field. Those are unchanged from
Story 2.2. Do not "clean up while you're in there" beyond what the tasks specify.

## Dev Agent Record

### Implementation Plan

Created `backend/core/logging.py` as the shared logging/context-binding primitive
and moved `configure_logging`/`bind_pipeline_run_id` there verbatim, added
`ensure_logging_configured()` (idempotent, guarded by `structlog.is_configured()`)
and `scoped_pipeline_run_id()` (a context manager over
`structlog.contextvars.bound_contextvars`). Trimmed `backend/pipeline/config.py`
to just `PipelineConfig`. Repointed five import sites
(`llm_client.py`, `orchestrator.py`, `conftest.py`, `test_insight_engine.py`,
`test_narrative_generator.py`) at the new module. Wrapped
`LLMClient.generate_narrative()`'s entire body in
`with scoped_pipeline_run_id(pipeline_run_id):` and added an
`ensure_logging_configured()` call at the top. Added
`backend/tests/test_llm_client_hardening.py` with 4 new tests covering AC2 and AC3
directly.

### Completion Notes

- **AC1** — `backend/core/llm_client.py` no longer imports anything from
  `backend/pipeline/`; verified by grep (`select:pipeline` import search returned
  empty for `backend/core/`). `backend/pipeline/config.py` retains only
  `PipelineConfig`. All 5 call sites repointed.
- **AC2** — `ensure_logging_configured()` guards on `structlog.is_configured()`.
  New test `test_generate_narrative_preserves_log_capture` proves an
  already-configured `LogCapture` survives the call; new test
  `test_generate_narrative_configures_json_logging` proves JSON logging is
  installed when nothing configured structlog first.
- **AC3** — `scoped_pipeline_run_id` wraps `structlog.contextvars.bound_contextvars`,
  which restores via `try/finally` on every exit path (including the
  `LLMProviderError` re-raise and the `raise last_exc` inside `_try_provider`).
  New test `test_pipeline_run_id_removed_after_call_with_no_prior_binding` proves
  no leak for a bare direct call; new test
  `test_pipeline_run_id_restored_after_call_with_prior_binding` proves the
  orchestrator's whole-run binding survives Stage 3 (regression guard for Stage 4
  render logging).
- **AC4** — Full suite: 115 passed, 1 skipped (pre-existing `anthropic`-missing
  skip), 0 failures — 111 from the pre-2.2b baseline + 4 new hardening tests.
  `conftest.py`/`test_insight_engine.py`/`test_narrative_generator.py` changed only
  their `configure_logging` import line.
- **Verification:** a follow-up scoped code review of exactly these changes
  (exception-safety of the context manager, completeness of the layering fix,
  correctness of the `is_configured()` guard, orphaned old-import search, test
  validity) returned zero findings.

### File List

- `backend/core/logging.py` (new)
- `backend/core/llm_client.py` (modified — new import, `ensure_logging_configured()`
  call, body wrapped in `scoped_pipeline_run_id`)
- `backend/pipeline/config.py` (modified — trimmed to `PipelineConfig` only)
- `backend/pipeline/orchestrator.py` (modified — import path only)
- `backend/tests/conftest.py` (modified — import path only)
- `backend/tests/test_insight_engine.py` (modified — import path only)
- `backend/tests/test_narrative_generator.py` (modified — import path only)
- `backend/tests/test_llm_client_hardening.py` (new)

## Change Log

| Date | Change |
|---|---|
| 2026-07-05 | Story filed as corrective follow-up to Story 2.2 code review (three findings: core→pipeline layering leak, unguaranteed JSON logging for direct callers, unscoped contextvar binding risking cross-call leakage). |
| 2026-07-05 | Implemented: `backend/core/logging.py` added, `pipeline/config.py` trimmed, `LLMClient` scoped/guarded, 4 new hardening tests. 115 passed / 1 skipped, zero regressions. Follow-up scoped review: 0 findings. Status → done. |
