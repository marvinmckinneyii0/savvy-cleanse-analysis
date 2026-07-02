# Story 2.2: LLM Client Abstraction

Status: ready-for-dev

> 🔌 **Inserted story — not yet in epics.md.** Filed out-of-band between 2.1
> (Configuration Layer) and the original 2.2 (Drift Engine, now effectively 2.3 in
> execution order). Rationale: Story 2.3 (Reporting Agent) and 2.4 (Monitoring Agent)
> both require LLM calls. Without this story, each would duplicate the
> retry/fallback/circuit-breaker machinery that currently lives inline in
> `backend/pipeline/narrative_generator.py`. This extraction is a prerequisite for
> DRY agent implementation.

> ⚠️ **Read the architecture tension note in Dev Notes before coding.** The
> architecture doc says "no abstraction layers" for LLM. This story is *not* a
> framework layer — it is an internal code-reuse extraction. The distinction matters
> and the dev must understand it before making any design decisions.

## Story

As a developer,
I want the LLM retry/fallback/circuit-breaker logic extracted from
`narrative_generator.py` into a single reusable `backend/core/llm_client.py` module,
so that the Reporting Agent (2.3) and Monitoring Agent (2.4) can invoke LLM calls
without duplicating resilience logic, and so that provider SDK imports are
consolidated in one place rather than scattered across pipeline stages.

## Acceptance Criteria

1. **`backend/core/llm_client.py` exists.** Given a caller provides an
   `InsightPayload`-style JSON string, when `LLMClient.generate_narrative(payload_json,
   pipeline_run_id)` is called, then it applies the full resilience chain (retry ×3,
   exponential backoff 1s/2s/4s, provider fallback Claude → OpenAI → Gemini, circuit
   breaker at 3 consecutive failures) and returns an `InsightReport`. The public
   interface must match the current `NarrativeGenerator.generate()` call surface so
   `narrative_generator.py` can delegate with a one-line change.

2. **`NarrativeGenerator` becomes a thin delegator.** `narrative_generator.py` retains
   its class and public `generate()` method signature — it remains Stage 3 of the
   pipeline — but its implementation delegates to `LLMClient`. The `_call_claude`,
   `_call_openai`, `_call_gemini`, `_try_provider`, and resilience fields
   (`_BACKOFF_DELAYS`, `_MAX_ATTEMPTS`, `_CIRCUIT_BREAKER_THRESHOLD`) move to
   `backend/core/llm_client.py`. `NarrativeGenerator.__init__` may retain a
   `self._client = LLMClient()` or use a module-level singleton — see Dev Notes.

3. **All existing `test_narrative_generator.py` tests continue to pass.** The test
   file mocks at the provider-method level (`_call_claude`, etc.) — after refactor,
   those mocks must target `backend.core.llm_client.LLMClient._call_claude` (or
   equivalent new path). Update mock targets; do not add or remove test cases in this
   story.

4. **Provider constants are defined once.** `_CLAUDE_MODEL`, `_OPENAI_MODEL`,
   `_GEMINI_MODEL` live in `backend/core/llm_client.py`. No duplication in
   `narrative_generator.py` or any future caller.

5. **`backend/core/__init__.py` exists** (empty, 1 line) — the directory is a proper
   Python package.

6. **Structlog events are unchanged.** Log event keys (`narrative_generated`,
   `llm_fallback`, `llm_retry`, `llm_client_error`, `llm_circuit_breaker`) and their
   fields remain byte-for-byte identical. Tests that assert log output must not need
   updating beyond mock-target paths.

7. **No new external dependencies.** This is pure internal restructuring. `anthropic`,
   `openai`, `google-genai` remain lazy imports inside their respective `_call_*`
   methods. No new package is added to `pyproject.toml`.

## Tasks / Subtasks

- [ ] **Task 0 — Read the current implementation in full** (no AC, mandatory pre-work)
  - [ ] Read `backend/pipeline/narrative_generator.py` completely — every method, every
        constant, every import. The file is 287 lines. Do not skim.
  - [ ] Read `backend/tests/test_narrative_generator.py` completely — identify every
        mock target path that will change after the move. List them before writing
        a single line of new code.
  - [ ] Read `backend/models/insight_payload.py`, `backend/models/insight_report.py`
        — confirm the type contracts `LLMClient` will receive and return.
  - [ ] Read `backend/errors/exceptions.py` — confirm `LLMProviderError` signature
        (takes `message: str`, `provider: str`, `cause: Exception`).

- [ ] **Task 1 — Create `backend/core/__init__.py`** (AC: 5)
  - [ ] Single line: `# backend/core — shared utilities (LLM client, future: cost tracking)`
  - [ ] This is the only change to directory structure.

- [ ] **Task 2 — Create `backend/core/llm_client.py`** (AC: 1, 4, 6, 7)
  - [ ] Move verbatim from `narrative_generator.py`:
        - Constants: `_BACKOFF_DELAYS`, `_MAX_ATTEMPTS`, `_CIRCUIT_BREAKER_THRESHOLD`,
          `_CLAUDE_MODEL`, `_OPENAI_MODEL`, `_GEMINI_MODEL`, `_SYSTEM_PROMPT`
        - Methods: `_call_claude`, `_call_openai`, `_call_gemini`, `_try_provider`,
          `_is_client_error`, `_build_report`, `_build_prompt`
        - All imports those methods require
  - [ ] Define `class LLMClient:` with `__init__(self) -> None` that binds
        `self._logger = structlog.get_logger().bind(stage="narrative_generator")`.
        **Keep `stage="narrative_generator"` in the logger binding** — changing it
        would alter structlog event payloads and break AC6.
  - [ ] Public method: `def generate_narrative(self, payload_json: str, pipeline_run_id:
        str) -> InsightReport:` — this is the loop-and-fallback method currently named
        `generate()` in `NarrativeGenerator`, adapted to accept `payload_json` directly
        (the caller no longer passes an `InsightPayload` object — `narrative_generator.py`
        serializes it before calling).
  - [ ] Module docstring: explain the resilience layers (copy from `narrative_generator.py`
        docstring, update file reference).

- [ ] **Task 3 — Refactor `backend/pipeline/narrative_generator.py`** (AC: 2, 6)
  - [ ] Add import: `from backend.core.llm_client import LLMClient`
  - [ ] In `__init__`: add `self._client = LLMClient()`
  - [ ] Replace `generate()` body with:
        ```python
        bind_pipeline_run_id(pipeline_run_id)
        payload_json = insight_payload.model_dump_json()
        return self._client.generate_narrative(payload_json, pipeline_run_id)
        ```
  - [ ] Delete all moved constants and methods from this file.
  - [ ] The remaining file should be ~25 lines: module docstring, imports
        (`InsightPayload`, `InsightReport`, `LLMClient`, `bind_pipeline_run_id`),
        `NarrativeGenerator` class with `__init__` and `generate()` only.
  - [ ] Update module docstring: note that resilience logic lives in
        `backend/core/llm_client.py` as of Story 2.2.

- [ ] **Task 4 — Update mock targets in `backend/tests/test_narrative_generator.py`**
      (AC: 3)
  - [ ] Find every `@patch` or `mocker.patch` call. Current targets are of the form
        `backend.pipeline.narrative_generator.NarrativeGenerator._call_claude` (or
        similar). Update each to
        `backend.core.llm_client.LLMClient._call_claude` (or the new path).
  - [ ] Run `uv run pytest backend/tests/test_narrative_generator.py -v` — all tests
        must pass before proceeding to Task 5.
  - [ ] **Do not add, remove, or rewrite any test case.** Only update mock targets
        and import paths.

- [ ] **Task 5 — Full suite regression** (AC: 3, 6)
  - [ ] Run `uv run pytest backend/tests/ -v`
  - [ ] All 111 previously-passing tests must still pass (1 skip for `anthropic`
        missing from env is expected and acceptable).
  - [ ] Zero new failures. If any test fails, fix the mock target — do not alter
        the test's assertions.

## Dev Notes

### Architecture tension: "no abstraction layers" vs. this story (READ FIRST)

`architecture.md §289` states:

> `"No LangChain, no abstraction layers. Provider fallback: Claude → OpenAI → Gemini."`

This sentence prohibits **framework adoption** (LangChain, LiteLLM, etc.) and
**external routing layers**. It does NOT prohibit moving the retry/fallback logic
from one internal Python file to another. The distinction:

| Prohibited (architecture.md intent) | What this story does |
|---|---|
| Add LiteLLM as a dependency | No new packages added |
| Route calls through an external orchestration layer | Logic stays in-process, in-repo |
| Wrap provider SDKs so callers don't know which SDK is used | Callers still pass JSON, get `InsightReport` — same as today |
| Abstract away structured outputs | `NarrativeContent` schema stays unchanged |

`LLMClient` is a private internal module, not a public interface boundary. The
provider SDK imports (`anthropic`, `openai`, `google.genai`) remain as lazy imports
inside the same `_call_*` methods — they just live in `backend/core/` instead of
`backend/pipeline/`. The architecture constraint is fully respected.

If in doubt: **do not add any new import to `pyproject.toml`**. If you feel tempted
to pull in a new package for this story, stop and re-read the scope.

### `backend/core/` is a new directory (not in the architecture target tree)

`architecture.md` does not include a `backend/core/` entry in its target directory
tree (§587–665). This is an intentional addition, filed as Story 2.2 out-of-band.
The directory follows the same conventions as `backend/pipeline/` and `backend/models/`:
- `__init__.py` required (empty, 1 comment line)
- Full type hints on all functions
- `from __future__ import annotations` at top of every file
- Module docstring on every file

Do NOT add `backend/core/` to any documentation or architecture file in this story —
that is out of scope.

### What moves vs. what stays

**Moves to `backend/core/llm_client.py`:**
```
_BACKOFF_DELAYS, _MAX_ATTEMPTS, _CIRCUIT_BREAKER_THRESHOLD
_CLAUDE_MODEL, _OPENAI_MODEL, _GEMINI_MODEL
_SYSTEM_PROMPT
LLMClient._call_claude()
LLMClient._call_openai()
LLMClient._call_gemini()
LLMClient._try_provider()
LLMClient._is_client_error()
LLMClient._build_report()
LLMClient._build_prompt()
LLMClient.generate_narrative()   ← renamed from NarrativeGenerator.generate()
```

**Stays in `backend/pipeline/narrative_generator.py`:**
```
NarrativeGenerator class (shell — __init__ + generate() only)
NarrativeGenerator.generate() → delegates to self._client.generate_narrative()
```

**Unchanged (zero edits):**
```
backend/models/insight_payload.py
backend/models/insight_report.py
backend/errors/exceptions.py
backend/pipeline/config.py
backend/pipeline/orchestrator.py   ← calls NarrativeGenerator.generate(), interface unchanged
```

### Current model identifiers (keep these, do not update)

```python
_CLAUDE_MODEL = "claude-sonnet-4-6"       # retired claude-sonnet-4-20250514 on 2026-06-15
_OPENAI_MODEL = "gpt-4o"
_GEMINI_MODEL = "gemini-2.0-flash"
```

The comment about the retired snapshot is intentional — leave it in `llm_client.py`.

### `max_retries=0` pattern — preserve exactly

Both `_call_claude` and `_call_openai` construct clients with `max_retries=0`:

```python
client = anthropic.Anthropic(api_key=..., max_retries=0)
client = openai.OpenAI(api_key=..., max_retries=0)
```

This is load-bearing: the SDK's default of 2 internal retries would compound with
`_try_provider`'s own retry loop, producing up to 9 actual API calls per provider
instead of 3. Do not remove it.

### Structlog `stage` binding — do not change

`LLMClient.__init__` must bind:
```python
self._logger = structlog.get_logger().bind(stage="narrative_generator")
```

Changing `stage=` to `"llm_client"` or anything else would alter the JSON log
output that monitoring and alerting infrastructure reads. The event names
(`narrative_generated`, `llm_fallback`, `llm_retry`, `llm_client_error`,
`llm_circuit_breaker`) must also be preserved verbatim.

### Singleton vs. instance — choose instance

`NarrativeGenerator` creates `self._client = LLMClient()` in `__init__`. Do not
make `LLMClient` a module-level singleton — the per-instance pattern is consistent
with how `NarrativeGenerator`, `InsightEngine`, and `DataQualityAssessor` are
all instantiated by the orchestrator. Future agents will instantiate their own
`LLMClient()`.

### Test mock target update pattern

Before (current paths in `test_narrative_generator.py`):
```python
@patch("backend.pipeline.narrative_generator.NarrativeGenerator._call_claude")
```

After (new paths):
```python
@patch("backend.core.llm_client.LLMClient._call_claude")
```

Grep the test file for every occurrence of `narrative_generator` in a `@patch`
decorator before touching anything. There may also be `mocker.patch(...)` calls —
update those too.

### Coding conventions (match existing codebase)

- `from __future__ import annotations` — first non-comment line in every new `.py`
- Type hints on every function signature, including `-> None`
- No bare `except:` — always `except SomeSpecificError`
- `LLMProviderError` is imported from `backend.errors.exceptions` (not re-exported
  via `backend.errors.__init__`)
- Pydantic style: `from pydantic import BaseModel` — but there are no new Pydantic
  models in this story; `InsightReport` and `NarrativeContent` are already defined
  in `backend/models/`

## Change Log

| Date | Change |
|---|---|
| 2026-07-02 | Story filed out-of-band between 2.1 and original 2.2 (Drift Engine). Rationale: 2.3 Reporting Agent and 2.4 Monitoring Agent require LLM calls; extraction prevents duplication. |
