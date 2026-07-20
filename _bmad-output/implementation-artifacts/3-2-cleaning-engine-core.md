# Story 3.2: Cleaning Engine Core (deterministic only)

Status: ready-for-dev

Sizing: L · Model: Opus · loop_eligible: false
<!-- Opus + loop_eligible:false because this is the first code path in the product that
     MODIFIES data. Every guard specified here (working-copy, Tier-1-only dispatch,
     fail-closed on anything else) is load-bearing: a bug is not a wrong number in a
     report, it is silent mutation of a client's data. PREREQUISITE: Story 3.1 (PR #39)
     MUST be merged first — this engine dispatches on `remediation_class` and imports
     `backend/pipeline/remediation_classifier.py`, both introduced there. Do not start
     dev until PR #39 is on main. -->

## Story

As the **SAINT pipeline**,
I want **a deterministic Cleaning Engine that applies the five rules-based remediations to a working copy of the data — acting autonomously ONLY on Tier-1 (`agent_autonomous`) findings — and returns the cleaned copy plus a structured record of every action taken**,
so that **downstream stories can gate it (3.4), render its record as the healing manifest (3.3), and export its output (3.6), while the original data is never modified and Tier-3 findings are never touched** (§2.1 detect-don't-fix; Epic 3 INVARIANTS).

## Context & scope boundary

This story builds the **engine and its action record** — nothing else. Explicitly:

1. **IN:** `backend/pipeline/cleaning_engine.py` — a pure pipeline stage that takes `(df, DataQualityReport, pipeline_run_id)` and returns `(cleaned_df, CleaningResult)`.
2. **IN:** `backend/models/cleaning_result.py` — Pydantic `CleaningAction` + `CleaningResult` (the record 3.3 renders into the Healing Manifest).
3. **IN:** The five deterministic remediation primitives (PRD Phase 9 set): whitespace normalization, type coercion, date standardization, exact-row deduplication, null imputation. All five ship as pure functions; **only the Tier-1 subset is dispatched autonomously**.
4. **OUT — do NOT build:** orchestrator/CLI wiring (3.4 — there is no opt-in gate yet, and cleaning is default-OFF; wiring the engine into `run_full_pipeline` here would ship always-on cleaning), imputation **defaults** (3.4), the Healing Manifest document artifact (3.3), Tier-3 candidate scoring/ranking (3.5), export (3.6), any client-facing copy (3.9), `backend/rules/` (3.4).
5. **OUT:** no new DQA detectors. The assessor currently emits no standalone whitespace/date-variance defect types; whitespace stripping and date standardization run as sub-steps of `mixed_types` coercion (see Dev Notes). Do not add detectors to "feed" the engine.

## Acceptance Criteria

1. **Working-copy only (load-bearing).** The engine operates on a deep copy taken at entry. The caller's DataFrame object is **never mutated** — asserted by test comparing the input frame to a pristine pre-call copy with `pd.testing.assert_frame_equal` after cleaning a maximally-dirty fixture. No code path (including error paths) writes to the input frame or to any file.

2. **Tier-1-only autonomous dispatch, fail-closed.** The engine applies remediations **only** to findings with `remediation_class == RemediationClass.AGENT_AUTONOMOUS`. Findings classed `human_policy_agent_execution` or `human_only` — and findings with any unknown/future class value — produce **zero actions and zero data changes**. The internal per-finding dispatch raises `CleaningEngineError` if invoked with a non-autonomous finding (defense in depth: the public path filters, the private path refuses). There is no parameter, flag, or environment variable that widens this.

3. **The four Tier-1 operations implemented deterministically** (specs in Dev Notes, keyed by `defect_type` exactly like the classifier — never by `category`):
   - `duplicate_rows` → drop exact duplicate rows (`keep="first"`, original row order preserved).
   - `case_inconsistency` → per column: collapse case variants to the most frequent original variant; ties break lexicographically (deterministic).
   - `mixed_types` → coerce column to its dominant type (whitespace-strip first; numeric via `pd.to_numeric`; datetimes standardized to ISO 8601 date strings). Values that fail coercion are **left unchanged and counted** — never nulled, never dropped (nulling is imputation = Tier 2).
   - `column_naming` → deterministic header normalization (strip → collapse whitespace/specials to `_` → lowercase; empty/numeric names → `column_{i}`; collisions suffixed `_2`, `_3`, …).

4. **Null-imputation primitive ships WITHOUT autonomy and WITHOUT defaults.** `impute_nulls(df, column, method)` exists as a pure function (`mean | median | mode | forward_fill`) with `method` **required** — no default argument, not reachable from the autonomous dispatch, not in the operation registry. It is the execution primitive Story 3.4's policy layer will call. A test asserts a report containing only `null_values` findings yields zero actions.

5. **Every action recorded.** The engine returns a `CleaningResult` whose `actions: list[CleaningAction]` records one entry per applied remediation: `operation`, `defect_type`, `affected_columns`, `rows_affected` / `values_changed`, deterministic parameters used (e.g. dominant type, canonical case variants count), and a human-readable `detail`. Zero-action runs return an empty list (never `None`). This model is the **single source the Healing Manifest (3.3) renders from** — design its fields for that consumer, do not add a parallel record.

6. **Deterministic and idempotent.** Same input frame + report → byte-identical cleaned output and identical action list, asserted by running the engine twice. Cleaning an already-clean frame (or re-cleaning engine output against a re-assessed report) produces zero further Tier-1 actions for the operations applied. No randomness, no time-dependence in data values (timestamps allowed only in the result envelope), no iteration-order dependence.

7. **Pipeline stage compliance.** Lives in `backend/pipeline/`; imports only from `models/`, `errors/`, siblings; never from `api/`, `agents/`, or legacy modules — **especially not legacy `backend/cleaner.py`** (superficially similar name and purpose; it is unfactored legacy, do not import, extend, or delete it here). No import-time side effects; no logging self-configuration; structlog events (`cleaning_started`, `cleaning_action_applied`, `cleaning_completed`) carry `pipeline_run_id` and **never log raw row data or PII** (log counts and column names only). New `CleaningEngineError(PipelineStageError)` added to `backend/errors/exceptions.py`.

8. **Tests** (`backend/tests/test_cleaning_engine.py` + model tests in `test_models.py`; conftest gains a maximally-dirty fixture with known Tier-1/2/3 defects):
   - working-copy invariant (AC 1); fail-closed dispatch incl. the `CleaningEngineError` guard (AC 2);
   - per-operation specs incl. tie-breaks, collision suffixes, uncoercible-value counting (AC 3);
   - imputation primitive: each method correct, `method` required, not autonomously reachable (AC 4);
   - action record completeness — every change traceable to exactly one `CleaningAction` (AC 5);
   - determinism double-run + idempotency (AC 6);
   - integration: assess → clean → re-assess on the dirty fixture shows Tier-1 defect types gone, Tier-2/3 findings byte-identical;
   - full suite green: `uv run pytest` (baseline after PR #39 + PR #40 merge: **193 passed / 1 skipped**; if running pre-#40, `--ignore=backend/tests/test_parse_file.py`, 181/1).

9. **DoD security gate.** Run `/security-review`; resolve any Critical/High before marking done. This story is the epic's highest-risk surface (first data-mutating code path) — reviewer should specifically probe for paths that touch non-Tier-1 data.

## Tasks / Subtasks

- [ ] **Task 0 — Confirm prerequisite (AC: 2)**
  - [ ] Verify PR #39 (Story 3.1) is merged to main; `RemediationClass` and `remediation_classifier.classify` importable. HALT if not.
- [ ] **Task 1 — Models (AC: 5)**
  - [ ] `backend/models/cleaning_result.py`: `CleaningOperation(str, Enum)` (five values), `CleaningAction`, `CleaningResult` (Pydantic, PascalCase noun pattern per `quality_report.py`).
- [ ] **Task 2 — Error type (AC: 7)**
  - [ ] Add `CleaningEngineError(PipelineStageError)` to `backend/errors/exceptions.py`.
- [ ] **Task 3 — Primitives (AC: 3, 4)**
  - [ ] Pure functions: `normalize_whitespace`, `coerce_column_type` (incl. ISO-8601 date standardization), `drop_exact_duplicates`, `normalize_case`, `normalize_column_names`, `impute_nulls` (method required).
- [ ] **Task 4 — Engine (AC: 1, 2, 5, 6, 7)**
  - [ ] `CleaningEngine.clean(df, quality_report, pipeline_run_id) -> tuple[pd.DataFrame, CleaningResult]`: deep-copy at entry; filter to `AGENT_AUTONOMOUS`; registry `defect_type → operation` (four entries); fail-closed private dispatch; stable operation order (registry order, then column order); structlog events.
- [ ] **Task 5 — Tests (AC: 8)**
  - [ ] Dirty fixture in `conftest.py`; unit + integration tests per AC 8; full suite green, 0 regressions.
- [ ] **Task 6 — Verify + security (AC: 8, 9)**
  - [ ] Full backend suite; `/security-review`; resolve Critical/High.

## Dev Notes

### Operation specs (deterministic, keyed on `defect_type`)

| `defect_type` | Operation | Deterministic rule |
|---|---|---|
| `duplicate_rows` | deduplication | `df.drop_duplicates(keep="first")`, index reset; `rows_affected` = rows removed. Exact duplicates only — near-duplicates are Tier 3 (3.5) and have no autonomous path. |
| `case_inconsistency` | case normalization | Per affected column: group non-null string values by `str.lower()`; replace every variant with the group's most frequent original form; tie → lexicographically smallest variant. Counts replaced values. |
| `mixed_types` | type coercion (+ whitespace + date standardization) | (1) strip leading/trailing whitespace on string values; (2) determine dominant type exactly as the assessor does (`non_null.apply(type).value_counts().index[0]`, `data_quality.py:96`); (3) coerce minority values: numeric dominant → `pd.to_numeric(errors="coerce")` but **only adopt values that converted** — failures keep originals and increment an `uncoerced` count in the action detail; datetime-like dominant → standardize to ISO 8601 (`YYYY-MM-DD`). Never introduce new nulls. |
| `column_naming` | header normalization | `strip()` → replace `[^a-zA-Z0-9_]+` runs with `_` → collapse repeats → strip `_` ends → lowercase; empty or purely-numeric result → `column_{position}` (0-based); collision with an existing header → append `_2`, `_3`, … in column order. Record old→new names in the action detail. |

**Why whitespace/date standardization have no registry rows:** the assessor emits no `whitespace` or `date_format_variance` defect types today (verified against `data_quality.py`). They execute as sub-steps of `mixed_types` coercion. If future detectors add those types, the classifier's fail-safe (`human_only` default) means they are untouched until deliberately mapped in `remediation_classifier.py` AND given a registry row here — two explicit edits, by design.

### Story 3.1 API surface this story consumes (PR #39 — merged code is authoritative)

- `RemediationClass(str, Enum)`: `AGENT_AUTONOMOUS | HUMAN_POLICY_AGENT_EXECUTION | HUMAN_ONLY` — `backend/models/quality_report.py`. No Tier-4 value exists; never add one.
- `DataQualityDefect.remediation_class` — defaulted `HUMAN_ONLY` (fail-safe). Every defect emitted by `assess_quality` arrives stamped (`data_quality.py` calls `classify_defects` once, post-detection).
- `backend/pipeline/remediation_classifier.py`: `classify`, `classify_defect`, `classify_defects`, `classify_report` — pure, keyed on `defect_type`. **Do not re-derive classes in the engine; trust the stamp on the finding.** The engine's own registry is about *how* to fix, the stamp is *whether it may*.

### Engine API decision (pre-made — do not redesign)

`clean()` returns `tuple[pd.DataFrame, CleaningResult]`. A DataFrame cannot live inside a Pydantic model without `arbitrary_types_allowed` (prohibited: raw frames at stage boundaries are the exact anti-pattern the contract rules exist for), and `PipelineResult` is the **only** sanctioned non-Pydantic envelope (architecture.md §486–494) — do not add another dataclass envelope. The tuple keeps the data and its record separable: 3.4 threads the frame onward, 3.3 consumes the record.

### Where things live / conventions (Epics 1–3.1, all merged)

- **Models:** `backend/models/` — Pydantic v2, `class X(str, Enum)` pattern (`Severity`, `DefectCategory`, `RemediationClass`).
- **Stage pattern:** class with a single public verb method taking `(df, …, pipeline_run_id)` (see `DataQualityAssessor.assess_quality`, `DriftEngine.run`). Pure, no import-time side effects, structlog only (`snake_case verb_noun` events).
- **Errors:** `backend/errors/exceptions.py` — `SavvyCleanseError` → `PipelineStageError` → stage-specific. Expected outcomes are results; exceptions are infrastructure/contract violations. A non-autonomous finding reaching the dispatch is a contract violation → raise.
- **Tests:** `backend/tests/test_<module>.py`, parametrized; shared fixtures in `conftest.py`. Type hints required everywhere; no `print`, no `except Exception: pass`, no wildcard imports.
- **Legacy hazard:** `backend/cleaner.py` is untested legacy with overlapping intent. New engine is `cleaning_engine.py`; zero imports from legacy modules (project-context.md legacy list).

### Invariants (Epic 3 — must not drift)

- Working-copy only; original data NEVER modified.
- Cleaning opt-in, default OFF → **therefore no orchestrator wiring in this story** (the gate that makes wiring safe is 3.4).
- Every remediation logged (here: `CleaningAction`; 3.3 renders the manifest from it).
- **Tier 3 findings NEVER auto-touched, even accidentally. LOAD-BEARING.** Enforced twice: public filter + fail-closed private dispatch (AC 2).
- Deterministic remediation set only — exactly the five PRD Phase-9 operations, nothing more (no fuzzy matching, no ML, no LLM anywhere in this stage).

### Previous-story intelligence (3.1 / PR #39)

- 3.1 deliberately keyed classification on `defect_type`, not `category`, so future Tier-3 variants can't inherit autonomous classes — mirror that exact reasoning in the operation registry.
- `duplicate_rows` (Tier 1, row dedup) vs `duplicate_measurement` (Tier 3, correlated-*column* signal) are unrelated despite the names; the engine must have **no** registry row for `duplicate_measurement`.
- 3.1's tests parametrize per `defect_type` and pin the fail-safe default explicitly — same style here (parametrize per operation; pin the fail-closed guard as its own test, not a side effect).
- Suite baseline at 3.1: 181/1 ignoring `test_parse_file.py`; PR #40 (CI) makes the full `uv run pytest` run 193/1 — use whichever baseline matches what is merged when dev starts, and record the number.

### References

- [Source: _bmad-output/implementation-artifacts/epic-3-cleaning-engine.md#INVARIANTS] — the five-operation deterministic set; opt-in default-off; Tier-3 never touched.
- [Source: _bmad-output/implementation-artifacts/schema-extensions-spec.md#1-dqa-finding-remediation_class] — four-tier ownership; Tier 4 is an overlay, not a class.
- [Source: _bmad-output/planning-artifacts/saint-master-prd.md §467, §793] — "automated rules-based remediation on a working copy… Healing is off by default… Every remediation logged… Original data untouched."
- [Source: backend/pipeline/remediation_classifier.py] — classifier API + design rationale (PR #39).
- [Source: backend/pipeline/data_quality.py] — dominant-type derivation (`:96`), emitted defect shapes the engine consumes.
- [Source: backend/pipeline/orchestrator.py] — stage composition the engine will join in 3.4 (not now).
- [Source: _bmad-output/planning-artifacts/architecture.md §482–506, §745] — layer boundaries; PipelineResult exception; error dual-strategy.

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
