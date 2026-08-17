# Story 3.5: Judgment-Required Findings Handling

Status: done

Sizing: M · Model: Opus · loop_eligible: false
<!-- Opus + loop_eligible:false: locks the Tier-3 human_only boundary — the
     "the agent NEVER auto-touches this, even accidentally" invariant every
     other Epic 3 story depends on. A bug here is invisible to a naive passing
     test suite (nothing crashes; a Tier-3 cell just silently changes) and
     directly contradicts the product's core "detect-don't-fix" trust claim.
     Human-supervised by explicit product decision, not the unattended loop.
     PREREQUISITES (all merged to main): Story 3.1 (PR #39 — RemediationClass,
     classifier), Story 3.2 (PR #42 — CleaningEngine), Story 3.3 (PR #48 —
     Healing Manifest, the sibling artifact this story's report section sits
     beside), Story 3.4 (PR #45 — Tier-2 policy, cleaning_coordinator). Do not
     start dev until all four are on main (they are, as of 2026-08-17). -->

## Story

As an **SMB owner reviewing my data-quality report**,
I want **every finding the agent will never auto-fix — near-duplicates, statistical outliers, implausible negatives, correlated columns — clearly called out as needing MY decision, in plain language, regardless of whether I've turned cleaning on**,
so that **I never mistake "the agent didn't flag it" for "the agent checked and it's fine," and I can trust that these specific findings stay exactly as they are in my original data no matter what I enable** (Epic 3 INVARIANTS: "Tier 3 findings are NEVER auto-touched, even accidentally. Load-bearing."; schema-extensions-spec.md §1: "agent detects and scores, never acts").

## Context & scope boundary

Today, `human_only` (Tier-3) findings are DQA defects like any other — `InsightEngine`/`NarrativeGenerator` don't reference `remediation_class` at all, so nothing in the report currently distinguishes "the agent will never touch this" from an ordinary, potentially-autonomous-fixable finding. This story closes that gap with two halves, matching the epic's own framing ("Judgment-Required Findings Handling" sitting directly on the "NEVER auto-touched" invariant):

1. **IN — report surfacing.** A new, structurally distinct report section listing every `human_only` finding, reusing the DQA detectors' existing `details`/`recommended_action` prose (no new evidence-scoring, no confidence values, no reasoning trail — that class of capability is Epic 11/Tier-4 territory, explicitly a "distinct artifact" per `epic-11-autonomous-judgment-eval-governance.md` §11.5: "Manifest logs WHAT changed; [11.5] logs WHY"). Populated **always** when `human_only` findings exist, independent of whether cleaning is enabled — confirmed with Marvin: Tier-3 findings exist purely from DQA classification (Story 3.1), which always runs, so this section is not gated on the cleaning opt-in the way the Healing Manifest is.
2. **IN — a runtime boundary guard**, not just tests. `cleaning_coordinator.clean_dataset()` gains an explicit, load-bearing assertion at the end of its pass: if ANY produced `CleaningAction` ever carries `remediation_class == HUMAN_ONLY`, raise `CleaningEngineError` immediately rather than let it silently return. This is defense-in-depth matching `CleaningEngine`'s own "independent second guard" philosophy (3.2's private-dispatch re-check) — a coordinator-level guard that fails LOUD in production if the tier-filtering upstream of it is ever broken by a future change, not just in CI.
3. **IN — a consolidated boundary-proof test suite** exercising the ENTIRE Epic 3 pipeline (DQA → classify → CleaningEngine → Tier-2 policy → coordinator → Healing Manifest → cleaned-CSV export) against a fixture covering **every** currently-registered `human_only` `defect_type` (`zero_variance`, `extreme_outliers`, `extreme_cardinality`, `negative_values`, `infinite_values`, `duplicate_measurement`) in one pass, proving none was ever touched anywhere in the chain — not scattered across 3.2/3.4/3.3's individual test files as it is today, but one first-class, explicitly-named guarantee a future reviewer can point to.
4. **OUT — do not add new Tier-3 detectors.** The six `defect_type`s currently mapped to `HUMAN_ONLY` in `remediation_classifier.py` are the complete, fixed set this story works against. Adding a `near_duplicate` detector (mentioned as a future example in the classifier's own docstring) is out of scope.
5. **OUT — do not add structured evidence/confidence scoring** to any Tier-3 finding (IQR bounds as a first-class field, similarity scores, ranked candidates). Epic 11 territory.
6. **OUT — do not use "Tier 3"/"human_only" in any client-facing string.** Per `schema-extensions-spec.md` §1: "TIER 3 IS NOT A PURCHASABLE CAPABILITY... Do not create a 'Tier 3' row in any client-facing surface." The new section's label and all rendered text must be internal-terminology-free.
7. **OUT — do not touch `CleaningEngine`'s or `cleaning_policy`'s dispatch/filtering logic.** Both already correctly exclude `human_only` findings from ever reaching a `CleaningAction`-producing path; this story adds a *guard on their output*, not a change to their *input filtering*.
8. **OUT — do not duplicate Story 3.9's disclosure copy.** 3.9 owns client-facing capability *descriptions* for Policy (Tier-2) Cleaning methods, surfaced at the enablement point ("median: fills gaps with the middle value..."). This story's findings list reuses existing DQA prose, not new explanatory copy about *why* Tier-3 exists as a concept — that framing-level copy, if wanted, is 3.9's call, not this story's.
9. **OUT — do not change halt behavior.** A `CRITICAL`-severity Tier-3 finding that already halts the pipeline (pre-existing DQA logic) continues to halt before any report — including this story's new section — is produced. Not touched.

## Acceptance Criteria

1. **Runtime boundary guard, load-bearing.** `cleaning_coordinator.clean_dataset()` asserts, after merging Tier-1 + Tier-2 actions and before returning, that no `CleaningAction` in the merged result has `remediation_class == RemediationClass.HUMAN_ONLY`. Violation raises `CleaningEngineError` with a message identifying the offending action's `defect_type`/`target_columns` — a hard failure, not a logged warning, not a silently-dropped action. A test proves the guard actually fires: construct a `CleaningResult` (or drive the coordinator with a mocked/monkeypatched Tier-1 or Tier-2 layer) that smuggles in a `HUMAN_ONLY`-classed action, and assert `clean_dataset` raises.

2. **Consolidated boundary-proof test.** One test module (or one clearly-named test class) drives the full chain — DQA assessment → classification → `clean_dataset` (Tier-1 + Tier-2) → `build_healing_manifest` → the cleaned-CSV export path (Story 3.6's `_write_cleaned_csv` or equivalent) — against a single fixture engineered to carry at least one instance of **every** currently-registered `human_only` `defect_type`. Asserts, in one place: (a) no `CleaningAction` has `remediation_class == HUMAN_ONLY`; (b) no `ManifestEntry` has `remediation_class == HUMAN_ONLY`; (c) every cell/column flagged by a Tier-3 finding is byte-identical between the original frame and the final cleaned/exported frame.

3. **`JudgmentRequiredFinding` model.** A new, purpose-built Pydantic model (NOT a direct re-export of `DataQualityDefect`, so a template can never accidentally render `defect_type`/`category`/`remediation_class` internals verbatim) carrying only: `sequence` (stable index), `severity`, `affected_columns`, `count`, `percentage`, `detail` (from the defect's `details` field), `recommended_action`. Built by a pure function `build_judgment_required_findings(quality_report: DataQualityReport) -> list[JudgmentRequiredFinding]` filtering to `remediation_class == HUMAN_ONLY`, preserving `quality_report.defects`' order.

4. **Wiring — always populated when applicable, code-only, never LLM-routed.** `InsightReport` gains `judgment_required_findings: list[JudgmentRequiredFinding] = Field(default_factory=list)` (empty list, not `None`, when there are no Tier-3 findings — distinct from `healing_manifest`'s `None`-when-cleaning-off convention, since this data source, `quality_report`, is unconditionally available). Populated in `orchestrator.py` directly from `result.quality_report`, independent of `resolved_enable_cleaning` — present whether cleaning is on, off, or was never configured. Never routed through `InsightPayload`/`InsightEngine`/`NarrativeGenerator` — structurally verified the same way Story 3.3 verified `healing_manifest`.

5. **Report surfacing in both DOCX and PDF**, gated on `judgment_required_findings` being non-empty (not on cleaning state). A new section, internal-terminology-free label (e.g. "Requires Your Review" — exact wording is implementation's call, but must not contain "Tier 3", "tier three", "human only", or any internal enum spelling), listing each finding's affected columns, count/percentage, and the DQA detector's own `detail`/`recommended_action` text. Positioned distinctly from `key_findings` (the LLM narrative) so a reader cannot mistake it for LLM-generated prose.

6. **Cleaning-state independence proven.** A test asserts `judgment_required_findings` is IDENTICAL (same findings, same order, same content) between a cleaning-enabled run and a cleaning-disabled run of the same input — proving this section's population never depends on the opt-in gate, matching the design decision in **Context & scope boundary** point 1.

7. **No client-facing internal terminology, anywhere in the new section.** A test scans the rendered DOCX/PDF output (or the template + model content) and asserts none of `"tier 3"`, `"tier_3"`, `"human_only"`, `"remediation_class"` (case-insensitive) appear.

8. **Halt behavior unchanged.** A `CRITICAL`-severity Tier-3 finding that halts the pipeline today still halts before Stage 3+ (Insight Engine, Narrative Generator, this story's new section) runs — proven by re-running (not modifying) the existing halt-path test(s) and confirming `judgment_required_findings` is never populated on a halted `PipelineResult`.

9. **Tests, full suite, and security gate.** New test file(s) covering AC1-8. Full suite green via `uv run pytest` (record before/after counts); frontend unaffected (`npx vitest run`, `npm run build` — no frontend files touched). Run `/security-review`; resolve any Critical/High before marking done — reviewer should specifically probe: can the runtime guard ever be bypassed; can any Tier-3 finding's raw column values (not just names) leak into the new section's rendered text; does the boundary-proof test actually exercise every registered `human_only` `defect_type` or silently miss one if the classifier's table grows.

## Tasks / Subtasks

- [x] **Task 0 — Confirm prerequisites (AC: all)**
  - [x] Verify PR #39, #42, #45, #48 are on `main`; `RemediationClass.HUMAN_ONLY`, `remediation_classifier._DEFECT_TYPE_TO_CLASS`, `cleaning_coordinator.clean_dataset`, `build_healing_manifest`, `InsightReport.healing_manifest` (wiring precedent) are all importable. HALT if not.
  - [x] Re-read `backend/pipeline/remediation_classifier.py`'s `_DEFECT_TYPE_TO_CLASS` table in full — enumerate the current complete list of `human_only`-mapped `defect_type`s (this is the fixture checklist for Task 3).
- [x] **Task 1 — Runtime boundary guard (AC: 1)**
  - [x] Add a guard at the end of `cleaning_coordinator.clean_dataset()`, after `merged` is built and before `return`: iterate `merged.actions`, raise `CleaningEngineError` (with `defect_type`/`target_columns` in the message) on the first `remediation_class == RemediationClass.HUMAN_ONLY` found.
  - [x] Test that the guard fires: construct/monkeypatch a scenario producing a smuggled-in `HUMAN_ONLY` action and assert `CleaningEngineError` is raised, with the message identifying the offending action.
- [x] **Task 2 — `JudgmentRequiredFinding` model + builder (AC: 3)**
  - [x] New file `backend/models/judgment_required_finding.py` (or add to an existing models module if a reviewer prefers — Dev Notes recommend a new file, mirroring `healing_manifest.py`'s pattern): `JudgmentRequiredFinding` Pydantic model + `build_judgment_required_findings(quality_report) -> list[JudgmentRequiredFinding]`.
  - [x] Order-preserving, pure function; no DataFrame access, no re-derivation.
- [x] **Task 3 — Consolidated boundary-proof test (AC: 2)**
  - [x] Build (or extend `cleaning_dirty_df`) a fixture carrying at least one instance of every currently-registered `human_only` `defect_type`: `zero_variance`, `extreme_outliers`, `extreme_cardinality`, `negative_values`, `infinite_values`, `duplicate_measurement`.
  - [x] One test class driving DQA → classify → `clean_dataset` → `build_healing_manifest` → cleaned-CSV export, asserting AC2's three properties in one place.
  - [x] A meta-test asserting the fixture/test actually covers every key currently in `remediation_classifier._DEFECT_TYPE_TO_CLASS` mapped to `HUMAN_ONLY` (so a future new Tier-3 `defect_type` that isn't added to this fixture fails loudly, not silently).
- [x] **Task 4 — Wiring (AC: 4, 6, 8)**
  - [x] Add `judgment_required_findings: list[JudgmentRequiredFinding] = Field(default_factory=list)` to `InsightReport`.
  - [x] In `orchestrator.py`, populate it from `result.quality_report` right after Stage 1 (DQA) succeeds — independent of `resolved_enable_cleaning`, unlike the Stage-4b `healing_manifest` wiring.
  - [x] Confirm (by reading) no code path threads this through `InsightPayload`/`InsightEngine`/`NarrativeGenerator`.
  - [x] Confirm (by reading + the existing halt-path test) it is never populated when `result.halted`.
- [x] **Task 5 — Renderers (AC: 5, 7)**
  - [x] `PdfRenderer`/`DocxRenderer`: add `judgment_required_findings` to both template contexts; add a conditional section to `report_template.html` and (via the established one-off `python-docx` script) `report_template.docx`, gated on the list being non-empty, using internal-terminology-free labeling.
- [x] **Task 6 — Verify + security (AC: 9)**
  - [x] `uv run pytest` green; record before/after pass counts.
  - [x] `npx vitest run` + `npm run build` (unaffected, confirm no regression).
  - [x] `/security-review` — resolve Critical/High before marking done.

## Dev Notes

### Why a NEW model file, not reusing `DataQualityDefect` directly

`DataQualityDefect` carries `defect_type`, `category`, `remediation_class` — all internal taxonomy that must never reach client-facing text (AC7, and the explicit "no Tier 3 row" prohibition). Story 3.3 established this exact pattern for the same reason: `ManifestEntry` is a purpose-built projection of `CleaningAction`, not a re-export of it. Mirror that here — `JudgmentRequiredFinding` exposes only fields safe to render.

### Runtime guard placement — exact diff target

`backend/rules/cleaning_coordinator.py::clean_dataset`, current final lines:

```python
    rows_after, columns_after = cleaned_df.shape
    merged = CleaningResult(
        pipeline_run_id=pipeline_run_id,
        ...
    )
    return cleaned_df, merged
```

Insert the guard between building `merged` and the `return`. Reuse `CleaningEngineError` (`backend/errors/exceptions.py`) — it already documents itself as "the independent second guard" for exactly this class of violation; do not invent a new exception type.

### The complete current `human_only` set (verify this hasn't changed before writing the fixture)

From `backend/pipeline/remediation_classifier.py::_DEFECT_TYPE_TO_CLASS`, as of this story's drafting: `zero_variance`, `extreme_outliers`, `extreme_cardinality`, `negative_values`, `infinite_values`, `duplicate_measurement`, plus the fail-safe default for any unmapped `defect_type`. Task 3's meta-test exists specifically so this list drifting (a new Tier-3 type added to the classifier without updating this story's fixture) fails loudly rather than silently under-testing.

### Existing `details`/`recommended_action` text is already client-safe

Spot-checked `backend/pipeline/data_quality.py`'s detectors (e.g. `negative_values`: `f"{neg_count} negative value(s) in '{col_str}' which implies non-negativity"`, `recommended_action="Verify negative values are intentional or correct data entry errors"`) — no raw enum leakage, no internal jargon, no raw cell values embedded (counts/column names/percentages only, same "column names are allowed, cell values are not" boundary Story 3.3 established). This story reuses this text as-is; it does not need to write new copy.

### Why "always populated," not gated on cleaning (locked with Marvin)

`healing_manifest` is `None` when cleaning didn't run because it describes an action that literally didn't happen. `judgment_required_findings` describes a PROPERTY OF THE DATA (which findings are `human_only`), computed unconditionally by Story 3.1's classifier during DQA — it doesn't depend on the cleaning opt-in at all. Gating it on cleaning-enabled would be an arbitrary coupling with no basis in what the data actually is. This DOES mean a dataset with Tier-3 findings gets a materially different (additive) report than it did pre-this-story, **even with cleaning off** — a deliberate, confirmed scope decision, not an oversight to defend against in review.

### Invariants (Epic 3 — must not drift)

- Tier-3 `human_only` NEVER auto-touched, even accidentally — now enforced by BOTH the pre-existing filter-based design (3.2/3.4) AND a new runtime assertion (this story), not filter-design alone.
- No "Tier 3" (or any internal remediation-class terminology) in any client-facing surface (schema-extensions-spec.md §1, restated as AC7 here).
- Working-copy only; original data never modified — unaffected by this story (no new mutation path is added; this story is read-only over `quality_report`).

### References

- [Source: _bmad-output/implementation-artifacts/epic-3-cleaning-engine.md#INVARIANTS] — "Tier 3 findings are NEVER auto-touched, even accidentally. Load-bearing."
- [Source: _bmad-output/implementation-artifacts/schema-extensions-spec.md#1-four-tier-ownership-model] — Tier 3 definition, defect_type examples, "NOT a purchasable capability... do not create a 'Tier 3' row in any client-facing surface."
- [Source: _bmad-output/implementation-artifacts/epic-11-autonomous-judgment-eval-governance.md#11.5] — the manifest/decision-log artifact boundary; this story's findings list is neither — it's the third, simplest artifact (WHAT requires review, no WHY).
- [Source: backend/pipeline/remediation_classifier.py] — the authoritative `defect_type` → `RemediationClass` table; fail-safe-to-`HUMAN_ONLY` default.
- [Source: backend/pipeline/cleaning_engine.py] — the Tier-1 "independent second guard" pattern (`_apply_operation`'s re-check) this story's coordinator-level guard mirrors.
- [Source: backend/rules/cleaning_coordinator.py] — exact guard insertion point.
- [Source: backend/rules/cleaning_policy.py] — Tier-2's existing `HUMAN_POLICY_AGENT_EXECUTION`-and-`null_values`-only filter (the guard this story adds a runtime backstop for, not a replacement).
- [Source: backend/models/healing_manifest.py, backend/tests/test_healing_manifest.py] — the `ManifestEntry`-is-a-projection pattern and the never-reaches-the-LLM verification pattern this story mirrors.
- [Source: backend/pipeline/orchestrator.py] — exact wiring point (after Stage 1 DQA, before the halt check's early return matters for AC8).
- [Source: backend/pipeline/data_quality.py] — the six Tier-3 detectors' actual `details`/`recommended_action` text.
- [Source: backend/tests/conftest.py] — `cleaning_dirty_df`; Task 3 needs a fixture covering ALL SIX Tier-3 types, which `cleaning_dirty_df` alone does not (it only carries `negative_values`) — extend it or build a new fixture.

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (human-supervised implementation, high effort)

### Debug Log References

- Task 1 (runtime guard): `uv run pytest backend/tests/test_cleaning_policy.py backend/tests/e2e/test_cleaning_gate.py` → 39 passed (unmodified, proves the guard addition doesn't disturb existing 3.4 behavior).
- Task 3 (consolidated boundary-proof fixture): building a fixture that actually triggers all six `human_only` `defect_type`s surfaced two real numerical quirks, both resolved empirically rather than assumed: (1) `extreme_outliers` needs a large row count — a single extreme value among otherwise-identical points can only exceed the 5-std-dev threshold once n is large enough (deviation/std approaches `sqrt(n-1)` as the outlier grows; n=12 can never trigger it regardless of magnitude, n=40 does); (2) `extreme_cardinality` requires numeric-coercible column content due to a pre-existing bug in `data_quality.py` sharing a numeric guard across unrelated checks in the same loop — flagged separately as its own follow-up task (`task_86d9e62e`), not fixed here (out of this story's scope).
- Full suite after Tasks 1-3: `uv run pytest backend/tests/test_tier3_boundary.py` → 6 passed; full backend suite → 386 passed / 1 skipped (0 regressions).
- Task 2 (model + unit tests): `uv run pytest backend/tests/test_judgment_required_finding.py` → 6 passed.
- Task 4 (wiring) + Task 5 (renderers): full backend suite → 397 passed / 1 skipped (+41 over the 356 pre-3.3 baseline / +23 over the 374 post-3.3 baseline). Frontend/build unaffected (no frontend files touched): `npx vitest run` → 18/18; `npm run build` → OK.
- `/security-review` (dedicated diff-scoped sub-agent) → zero qualifying findings. Explicitly verified Jinja2 `autoescape=True` still holds, no `|safe`/`Markup()` introduced, `JudgmentRequiredFinding` projects only typed fields (no `dict`/`Any` passthrough), every Tier-3 detector's `details`/`recommended_action` text confirmed to interpolate only column names/counts/percentages (never raw cell values), and the runtime guard's `CleaningEngineError` message traced to confirm it only ever reaches CLI stderr/logs, never the rendered report.

### Completion Notes List

- **Runtime boundary guard (AC1)** — `cleaning_coordinator._verify_tier3_never_touched` raises `CleaningEngineError` naming the offending `defect_type`/`target_columns` if any merged `CleaningAction` ever carries `remediation_class == HUMAN_ONLY`. Proven to actually fire via three tests: direct unit test of the guard function, a "clean result passes" negative test, and an end-to-end test that monkeypatches `CleaningEngine.clean` to smuggle in a bad action and confirms `clean_dataset` itself raises (not just the standalone guard function).
- **Consolidated boundary-proof (AC2)** — one fixture (`all_tier3_types_df`, 40 rows) triggers all six currently-registered `human_only` types simultaneously alongside real Tier-1/Tier-2 activity; one test drives the full `run_full_pipeline` chain (DQA → classify → clean → manifest → cleaned-CSV export) and asserts no `CleaningAction`/`ManifestEntry` ever carries `HUMAN_ONLY`, and every Tier-3-flagged column is byte-identical between the original and exported CSV (compared via re-reading both through the same CSV round-trip, avoiding a dtype-inference false positive on numeric-looking string columns). A meta-test pins the fixture's coverage against the classifier's live `HUMAN_ONLY` set, so a future new Tier-3 type failing to be added to the fixture fails loudly.
- **`JudgmentRequiredFinding` model (AC3)** — purpose-built projection (not a `DataQualityDefect` re-export); order-preserving pure builder; unit tests confirm no `defect_type`/`category`/`remediation_class` attribute exists on the model at all (structurally impossible to leak, not just untested).
- **Wiring (AC4, AC6, AC8)** — `InsightReport.judgment_required_findings` populated in `orchestrator.py` from `result.quality_report` immediately after Stage 4 (unconditionally, not gated on `resolved_enable_cleaning`), never routed through `InsightPayload`. Verified: identical output between cleaning-on/off runs of the same input (AC6); empty list (not error/None-crash) when there are no `human_only` findings; never populated on a halted `PipelineResult` (`result.insight_report is None` on that path, structurally, plus an explicit test); structurally absent from the LLM-facing `InsightPayload` (no such attribute exists).
- **Renderers (AC5, AC7)** — both `report_template.html` (direct edit) and `report_template.docx` (regenerated via the established one-off `python-docx` script) gained a "Requires Your Review" section, rendering `affected_columns`/`count`/`percentage`/`detail`/`recommended_action` per finding (learned from Story 3.3's PR review: show every relevant field, not just outcome+detail). A dedicated test scans rendered output in both formats for `"tier 3"`/`"tier_3"`/`"human_only"`/`"remediation_class"` (case-insensitive) and asserts none appear.
- **Tests + security (AC9)** — 397 passed / 1 skipped (+23 over the post-3.3 baseline), frontend/build unaffected, `/security-review` clean.

### Review Findings

Code review (8-angle: line-by-line, removed-behavior, cross-file, reuse, simplification, efficiency, altitude, conventions; high effort, recall-biased) — 3 confirmed/plausible findings fixed, 1 deferred:

- [x] [Review][Patch] The "Requires Your Review" section rendered an empty `<strong></strong>` for a table-level finding (`affected_columns=[]`), unlike the Data Cleaning section's existing `'table-level'` fallback for the identical case one block above. RESOLVED: both `report_template.html` and `report_template.docx` now use `finding.affected_columns|join(', ') if finding.affected_columns else 'table-level'`. New test `test_judgment_required_findings_with_empty_affected_columns_renders`. [`backend/renderers/templates/report_template.html`, `backend/renderers/templates/report_template.docx`, `backend/tests/test_renderers.py`]
- [x] [Review][Patch] The runtime boundary guard (AC1) was only proven to fire via `clean_dataset()` called directly — no test drove a violation through `run_full_pipeline()` itself, so a future refactor wrapping the cleaning stage in a broad `try/except` (the CLI already does this pattern one layer up) could silently swallow the guard's exception with nothing to catch the regression. RESOLVED: new `test_guard_violation_propagates_unhandled_through_run_full_pipeline` drives the full orchestrator entry point with a smuggled-in violation and asserts `CleaningEngineError` propagates unhandled. [`backend/tests/test_tier3_boundary.py`]
- [x] [Review][Patch] `JudgmentRequiredFinding.detail` is silently sourced from `DataQualityDefect.details` (plural→singular rename, matching `ManifestEntry`'s convention) with no documentation — a future template author copy-pasting a reference pattern could write `finding.details` and hit an `AttributeError` at render time. RESOLVED: added an explicit field comment. Also added `test_real_detector_text_never_uses_internal_terminology`, which sources its terminology-check text from the REAL `DataQualityAssessor` output (not just this test file's hand-picked fixture strings) — addresses the altitude-review observation that the original terminology guard could only ever catch drift in its own fixture, not in the actual DQA detector prose. [`backend/models/judgment_required_finding.py`, `backend/tests/test_renderers.py`]
- [x] [Review][Defer] Story 3.4's pre-existing `test_enabling_does_not_change_the_report` (`test_cleaning_gate.py`) shares one mutated `InsightReport` object between its cleaning-on/off runs (the mock returns the same fixture instance both times), making its equality assertion tautological — a blind spot that predates this story (already true for `healing_manifest`) and this story's `judgment_required_findings` addition inherits it. Deferred, not fixed: this story's own `test_judgment_required_findings_identical_regardless_of_cleaning_state` (in the new `test_judgment_required_findings_wiring.py`) independently and correctly covers the exact same claim using fresh, non-shared `InsightReport` instances per run (`side_effect=_fresh_canned_report`), so the real assertion IS verified — just not by the older, reused 3.4 fixture. Editing a shipped Story 3.4 test file was judged out of this story's locked scope. [`backend/tests/e2e/test_cleaning_gate.py`]
- `/security-review` re-run implicitly covered by the fix set — none of the three patches touch a data-disclosure boundary (template fallback text, test coverage, a code comment); the original review's conclusions stand.

### File List

- `backend/rules/cleaning_coordinator.py` (M) — `_verify_tier3_never_touched`, called at the end of `clean_dataset` before returning.
- `backend/models/judgment_required_finding.py` (A) — `JudgmentRequiredFinding`, `build_judgment_required_findings`.
- `backend/models/insight_report.py` (M) — additive `judgment_required_findings: list[...] = Field(default_factory=list)` field.
- `backend/pipeline/orchestrator.py` (M) — populates `insight_report.judgment_required_findings` from `result.quality_report`, unconditionally, right after Stage 4.
- `backend/renderers/pdf_renderer.py`, `backend/renderers/docx_renderer.py` (M) — `judgment_required_findings` added to both template contexts.
- `backend/renderers/templates/report_template.html` (M) — new conditional "Requires Your Review" section.
- `backend/renderers/templates/report_template.docx` (M, binary) — regenerated via a one-off `python-docx` script; same section appended after the existing Data Cleaning block.
- `backend/tests/test_judgment_required_finding.py` (A) — 6 tests: filtering, order preservation, safe-field projection, empty cases, purity.
- `backend/tests/test_tier3_boundary.py` (A) — 6 tests: the consolidated boundary proof, the fixture-coverage meta-test, and the runtime-guard-fires tests.
- `backend/tests/e2e/test_judgment_required_findings_wiring.py` (A) — 5 tests: population, cleaning-state independence, empty-when-no-findings, halt-path, LLM-payload-shape.
- `backend/tests/test_renderers.py` (M) — +6 tests: section present/absent for both formats, field-content and terminology-free assertions.

## Change Log

- 2026-08-17: Story drafted (Opus, human-supervised). Scope locked with Marvin before drafting via two rounds: (1) confirmed 3.5 = both report-surfacing AND a consolidated/hardened runtime boundary guard, not either alone; (2) confirmed the new report section renders whenever Tier-3 findings exist, independent of the cleaning opt-in state (not paired/gated with the Healing Manifest). Status → ready-for-dev.
- 2026-08-17: Implemented (Opus, human-supervised, high effort). Runtime boundary guard in `cleaning_coordinator.py`; `JudgmentRequiredFinding` model + builder; wiring through `InsightReport`/orchestrator (always populated, never via `InsightPayload`); both DOCX and PDF renderers extended with a "Requires Your Review" section. Discovered and separately flagged (not fixed, out of scope) a pre-existing dead-code bug in `data_quality.py`'s `extreme_cardinality` check. 397 passed / 1 skipped (+23 over post-3.3 baseline, 0 regressions); frontend/build unaffected; `/security-review` clean. Status → review.
- 2026-08-17: Code review (8-angle, high effort). 3 findings fixed (missing table-level fallback for empty affected_columns, missing orchestrator-level test for the runtime guard, undocumented field rename + a real-detector-sourced terminology test), 1 deferred (a pre-existing Story 3.4 test's tautological equality assertion, independently covered by this story's own correctly-designed test). 400 passed / 1 skipped (+3, 0 regressions); frontend/build unaffected. Status → done.
