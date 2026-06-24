# Story 1.4: LLM Narrative Generation

Status: review

<!-- Validation is optional. Run validate-create-story for a quality check before dev-story. -->

---

## Story

**As a** developer on SavvyCortex,
**I want** to transform the computed InsightPayload into a natural-language InsightReport using Claude Structured Outputs with retry and provider fallback,
**So that** users receive human-readable narrative grounded entirely in computed statistics.

### Business Context

This is Story 1.4 of Epic 1 — Phase 1 (Foundation). It is the third pipeline stage: the NarrativeGenerator receives the deterministic `InsightPayload` from Story 1.3's Insight Engine and sends it to an LLM (Claude via Anthropic SDK) which narrates the findings into structured prose. The architecture's grounding pattern (NFR7) is critical here — the LLM receives pre-computed statistics as input context and produces narrative text. It never computes, invents, or hallucates numerical values.

The `InsightReport` Pydantic model is the output contract. The renderer (Story 1.5) consumes it to produce docx/PDF files. If narrative generation fails entirely, the pipeline still succeeds — PipelineResult carries a fallback InsightReport with computed data sections but empty narrative sections, so the renderer can still produce a useful (if narrativeless) report.

Resilience is first-class: retry with exponential backoff, provider fallback chain (Claude → OpenAI → Gemini), circuit breaker after 3 consecutive failures, and 4xx non-retry. All calls are wrapped with structlog observability.

---

## Acceptance Criteria

The AC below comes verbatim from [epics.md](../planning-artifacts/epics.md). Do not reinterpret — implement to the letter.

**Given** a valid InsightPayload from the Insight Engine
**When** `NarrativeGenerator.generate(insight_payload)` is called
**Then** the generator calls Claude API via `client.messages.parse()` with the InsightPayload as grounding context and `InsightReport` as the output Pydantic model
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
**And** `LLMProviderError` is raised with the provider name and error details

**Given** any narrative generation run
**When** generation completes or fails
**Then** structlog entries include `pipeline_run_id`, `stage="narrative_generator"`, provider used, token count, and duration
**And** `backend/tests/test_narrative_generator.py` passes with mocked API calls covering: successful generation, retry logic, fallback chain, circuit breaker, and 4xx non-retry

---

## Tasks / Subtasks

- [x] **Task 1 — Pydantic model: `InsightReport`** (AC: InsightReport contains narrative sections)
  - [x] Create `backend/models/insight_report.py`
  - [x] Define `NarrativeSection(BaseModel)` with fields:
    - `title: str` — section heading (e.g., "Executive Summary")
    - `content: str` — narrative prose grounded in computed stats
  - [x] Define `InsightReport(BaseModel)` with fields:
    - `executive_summary: str` — high-level narrative overview
    - `key_findings: list[NarrativeSection]` — detailed findings with section headings
    - `anomaly_analysis: str | None = None` — narrative about detected anomalies (None if no anomalies)
    - `recommendations_narrative: str | None = None` — narrative about recommendations
    - `metadata: dict` — generation metadata (provider, model, token_count, duration_ms, timestamp)
    - `fallback: bool = False` — True when narrative was unavailable and this is a stub report
    - `fallback_reason: str | None = None` — explanation when `fallback=True`
  - [x] Add unit tests in `backend/tests/test_models.py` for InsightReport validation
  - [x] Verify `PipelineResult.insight_report` type annotation resolves against this model

- [x] **Task 2 — NarrativeGenerator class skeleton** (AC: NarrativeGenerator.generate(insight_payload))
  - [x] Create `backend/pipeline/narrative_generator.py`
  - [x] Define `NarrativeGenerator.__init__(self)` — accepts no constructor args; reads API keys from environment at call time
  - [x] Define `generate(self, insight_payload: InsightPayload, pipeline_run_id: str) -> InsightReport`
  - [x] Build grounding prompt: serialize `insight_payload.model_dump_json()` into a system message instructing the LLM to narrate (never compute) the pre-computed stats
  - [x] Use `structlog.get_logger()` with `stage="narrative_generator"` binding

- [x] **Task 3 — Claude provider call via `client.messages.parse()`** (AC: calls Claude API via client.messages.parse())
  - [x] Instantiate `anthropic.Anthropic()` client (reads `ANTHROPIC_API_KEY` from env)
  - [x] Call `client.messages.parse(model="claude-sonnet-4-20250514", max_tokens=4096, messages=[...], output_format=InsightReport)`
  - [x] Extract `result.output_parsed` as the `InsightReport`
  - [x] Populate `InsightReport.metadata` with provider, model, token count from usage, and duration

- [x] **Task 4 — Retry logic with exponential backoff** (AC: up to 3 attempts, 1s/2s/4s)
  - [x] Implement retry loop: max 3 attempts per provider
  - [x] Backoff delays: `[1, 2, 4]` seconds between attempts
  - [x] Retryable conditions: `anthropic.APITimeoutError`, `anthropic.APIStatusError` with `status_code >= 500`
  - [x] Log each retry: `logger.warning("llm_retry", provider=..., attempt=..., error_type=..., backoff_seconds=...)`
  - [x] Use `time.sleep()` for backoff (no async in Phase 1)

- [x] **Task 5 — Provider fallback chain (Claude → OpenAI → Gemini)** (AC: falls back to OpenAI, then Gemini)
  - [x] Define provider config list: `[("claude", _call_claude), ("openai", _call_openai), ("gemini", _call_gemini)]`
  - [x] `_call_claude(...)` — uses `anthropic.Anthropic().messages.parse()` as in Task 3
  - [x] `_call_openai(...)` — uses `openai.OpenAI().beta.chat.completions.parse()` with `response_format=InsightReport`
  - [x] `_call_gemini(...)` — uses `google.genai.Client().models.generate_content()` with `response_schema=InsightReport`
  - [x] Each provider method returns `InsightReport` or raises on failure
  - [x] Log fallback transitions: `logger.warning("llm_fallback", from_provider=..., to_provider=..., reason=...)`

- [x] **Task 6 — Circuit breaker (3 consecutive failures → skip)** (AC: circuit breaker triggers)
  - [x] Track consecutive failure count across all providers in a single generate() call
  - [x] After 3 total provider failures (3 attempts × 3 providers = 9 attempts max, but circuit breaker at 3 total failures across the chain), skip narrative
  - [x] Return fallback `InsightReport(executive_summary="", key_findings=[], fallback=True, fallback_reason="All LLM providers failed after 3 consecutive failures", metadata={...})`
  - [x] Log circuit breaker: `logger.error("llm_circuit_breaker", consecutive_failures=3, providers_tried=[...])`

- [x] **Task 7 — 4xx client error non-retry** (AC: 4xx NOT retried, raises LLMProviderError)
  - [x] Detect 4xx: `anthropic.APIStatusError` with `400 <= status_code < 500`
  - [x] Immediately raise `LLMProviderError(message="Client error from {provider}", provider=provider, cause=exc)`
  - [x] Do NOT retry, do NOT fall back — 4xx indicates a code bug, not transient failure
  - [x] Log: `logger.error("llm_client_error", provider=..., status_code=..., error=...)`

- [x] **Task 8 — Structured logging with observability** (AC: structlog entries with pipeline_run_id, stage, provider, tokens, duration)
  - [x] Bind `pipeline_run_id` via `structlog.contextvars.bind_contextvars()` at entry
  - [x] Log on success: `logger.info("narrative_generated", provider=..., model=..., token_count=..., duration_ms=...)`
  - [x] Log on fallback skip: `logger.warning("narrative_skipped", reason="circuit_breaker", ...)`
  - [x] All log events include `stage="narrative_generator"` via logger binding
  - [x] Measure duration with `time.perf_counter()` around each provider call

- [x] **Task 9 — Test: successful generation** (AC: test_narrative_generator.py passes)
  - [x] Create `backend/tests/test_narrative_generator.py`
  - [x] Mock `anthropic.Anthropic` so `client.messages.parse()` returns a valid InsightReport
  - [x] Assert returned InsightReport has all required fields populated
  - [x] Assert `fallback=False`
  - [x] Assert structlog captured `narrative_generated` event with provider, token_count, duration_ms

- [x] **Task 10 — Test: retry logic** (AC: retry with backoff)
  - [x] Mock Claude to raise `APITimeoutError` on first 2 calls, succeed on 3rd
  - [x] Assert retry count is 3 total attempts
  - [x] Assert structlog captured 2 `llm_retry` events
  - [x] Patch `time.sleep` to verify backoff delays `[1, 2]` (sleep before 2nd and 3rd attempts)

- [x] **Task 11 — Test: fallback chain** (AC: falls back to OpenAI, then Gemini)
  - [x] Mock Claude to fail all 3 attempts, OpenAI to succeed on first attempt
  - [x] Assert InsightReport.metadata["provider"] == "openai"
  - [x] Assert structlog captured `llm_fallback` event from claude to openai
  - [x] Test full chain: Claude fails, OpenAI fails, Gemini succeeds

- [x] **Task 12 — Test: circuit breaker** (AC: 3 consecutive failures → skip)
  - [x] Mock all providers to fail all attempts
  - [x] Assert returned InsightReport has `fallback=True`
  - [x] Assert `fallback_reason` mentions provider failures
  - [x] Assert structlog captured `llm_circuit_breaker` event

- [x] **Task 13 — Test: 4xx non-retry** (AC: 4xx raises LLMProviderError)
  - [x] Mock Claude to raise `APIStatusError` with status_code=400
  - [x] Assert `LLMProviderError` is raised
  - [x] Assert error has `provider="claude"` and original exception as `cause`
  - [x] Assert NO retry attempts (only 1 call to `client.messages.parse`)

---

## Dev Notes

### Architecture Patterns

- **LLM Grounding (NFR7):** The LLM is a narrator, not a calculator. `InsightPayload.model_dump_json()` is sent as grounding context. The system prompt must instruct: "narrate these pre-computed statistics; do not independently compute any numbers."
- **Structured Outputs:** Use `client.messages.parse(output_format=InsightReport)` — Anthropic SDK returns a Pydantic model instance directly. No JSON parsing, no free-form text extraction. [Source: architecture.md, line 289 and 508-523]
- **Dual error strategy:** 4xx → `LLMProviderError` (code bug). 5xx/timeout → retry → fallback → circuit breaker → fallback InsightReport. The pipeline never fails due to LLM unavailability — it degrades gracefully. [Source: architecture.md, lines 525-529]
- **PipelineResult integration:** `PipelineResult.insight_report` is typed as `InsightReport | None`. The orchestrator (Story 1.6) sets this field after narrative generation. [Source: backend/models/pipeline_result.py, line 67]

### Source Tree Components

- **New files:**
  - `backend/models/insight_report.py` — InsightReport Pydantic model
  - `backend/pipeline/narrative_generator.py` — NarrativeGenerator class
  - `backend/tests/test_narrative_generator.py` — test suite
- **Modified files:**
  - `backend/tests/test_models.py` — add InsightReport model validation tests

### Dependencies

- `anthropic>=0.79.0` — already in project; `client.messages.parse()` with `output_format=`
- `openai` — needed for fallback provider; add to requirements if not present
- `google-genai` — needed for Gemini fallback; add to requirements if not present
- Provider SDKs are only imported inside their respective `_call_*` methods to avoid hard dependency when only Claude is configured

### Testing Standards

- All LLM calls are mocked — never call real APIs in tests
- Use `structlog.testing.LogCapture()` with `merge_contextvars` processor for log assertions
- Restore logging config via `configure_logging()` in test teardown
- `time.sleep` is patched to avoid test delays
- Use `pipeline_run_id` fixture from conftest.py

### Project Structure Notes

- `backend/models/insight_report.py` aligns with `architecture.md` file tree (line 599)
- `backend/pipeline/narrative_generator.py` aligns with `architecture.md` file tree (line 151, 591)
- `backend/tests/test_narrative_generator.py` aligns with `architecture.md` file tree (line 172, 665)
- `InsightReport` import in `pipeline_result.py` is already declared under `TYPE_CHECKING` (line 33) — no modification needed there

### References

- [Source: architecture.md, lines 289] — LLM Integration: Direct Anthropic SDK, `client.messages.parse()` with Pydantic models
- [Source: architecture.md, lines 508-523] — LLM Call Pattern code example
- [Source: architecture.md, lines 525-529] — Retry Pattern: 3 attempts, backoff, fallback chain, circuit breaker, 4xx rule
- [Source: architecture.md, lines 536-548] — Enforcement Guidelines (Pydantic, structlog, pipeline_run_id)
- [Source: epics.md, lines 299-333] — Story 1.4 acceptance criteria (verbatim)
- [Source: backend/errors/exceptions.py, lines 64-81] — LLMProviderError(message, provider, cause)
- [Source: backend/models/pipeline_result.py, lines 32-33] — InsightReport TYPE_CHECKING import
- [Source: backend/models/insight_payload.py] — InsightPayload model (input to NarrativeGenerator)

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- All 13 tasks implemented and verified in a single pass
- InsightReport Pydantic model with NarrativeSection, fallback support, metadata dict
- NarrativeGenerator with full resilience stack: retry (3 attempts, 1s/2s/4s backoff), fallback chain (Claude → OpenAI → Gemini), circuit breaker (3 consecutive failures → fallback report), 4xx non-retry (immediate LLMProviderError)
- Provider SDKs imported lazily inside _call_* methods to avoid hard dependency
- Grounding prompt enforces NFR7: LLM narrates pre-computed stats, never computes
- structlog observability: pipeline_run_id, stage="narrative_generator", provider, token_count, duration_ms
- 11 tests in test_narrative_generator.py + 4 model tests in test_models.py = 15 new tests
- Full suite: 84/84 tests pass, zero regressions

### Change Log

- 2026-06-22: Implemented Story 1.4 — all 13 tasks complete, 84/84 tests pass

### File List

- backend/models/insight_report.py (new)
- backend/pipeline/narrative_generator.py (new)
- backend/tests/test_narrative_generator.py (new)
- backend/tests/test_models.py (modified — added InsightReport tests)
- _bmad-output/implementation-artifacts/1-4-llm-narrative-generation.md (modified — status, tasks, dev record)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified — 1-4 status)
