# Story 3.5: Judgment-Required Findings Handling

Status: ready-for-dev

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

- [ ] **Task 0 — Confirm prerequisites (AC: all)**
  - [ ] Verify PR #39, #42, #45, #48 are on `main`; `RemediationClass.HUMAN_ONLY`, `remediation_classifier._DEFECT_TYPE_TO_CLASS`, `cleaning_coordinator.clean_dataset`, `build_healing_manifest`, `InsightReport.healing_manifest` (wiring precedent) are all importable. HALT if not.
  - [ ] Re-read `backend/pipeline/remediation_classifier.py`'s `_DEFECT_TYPE_TO_CLASS` table in full — enumerate the current complete list of `human_only`-mapped `defect_type`s (this is the fixture checklist for Task 3).
- [ ] **Task 1 — Runtime boundary guard (AC: 1)**
  - [ ] Add a guard at the end of `cleaning_coordinator.clean_dataset()`, after `merged` is built and before `return`: iterate `merged.actions`, raise `CleaningEngineError` (with `defect_type`/`target_columns` in the message) on the first `remediation_class == RemediationClass.HUMAN_ONLY` found.
  - [ ] Test that the guard fires: construct/monkeypatch a scenario producing a smuggled-in `HUMAN_ONLY` action and assert `CleaningEngineError` is raised, with the message identifying the offending action.
- [ ] **Task 2 — `JudgmentRequiredFinding` model + builder (AC: 3)**
  - [ ] New file `backend/models/judgment_required_finding.py` (or add to an existing models module if a reviewer prefers — Dev Notes recommend a new file, mirroring `healing_manifest.py`'s pattern): `JudgmentRequiredFinding` Pydantic model + `build_judgment_required_findings(quality_report) -> list[JudgmentRequiredFinding]`.
  - [ ] Order-preserving, pure function; no DataFrame access, no re-derivation.
- [ ] **Task 3 — Consolidated boundary-proof test (AC: 2)**
  - [ ] Build (or extend `cleaning_dirty_df`) a fixture carrying at least one instance of every currently-registered `human_only` `defect_type`: `zero_variance`, `extreme_outliers`, `extreme_cardinality`, `negative_values`, `infinite_values`, `duplicate_measurement`.
  - [ ] One test class driving DQA → classify → `clean_dataset` → `build_healing_manifest` → cleaned-CSV export, asserting AC2's three properties in one place.
  - [ ] A meta-test asserting the fixture/test actually covers every key currently in `remediation_classifier._DEFECT_TYPE_TO_CLASS` mapped to `HUMAN_ONLY` (so a future new Tier-3 `defect_type` that isn't added to this fixture fails loudly, not silently).
- [ ] **Task 4 — Wiring (AC: 4, 6, 8)**
  - [ ] Add `judgment_required_findings: list[JudgmentRequiredFinding] = Field(default_factory=list)` to `InsightReport`.
  - [ ] In `orchestrator.py`, populate it from `result.quality_report` right after Stage 1 (DQA) succeeds — independent of `resolved_enable_cleaning`, unlike the Stage-4b `healing_manifest` wiring.
  - [ ] Confirm (by reading) no code path threads this through `InsightPayload`/`InsightEngine`/`NarrativeGenerator`.
  - [ ] Confirm (by reading + the existing halt-path test) it is never populated when `result.halted`.
- [ ] **Task 5 — Renderers (AC: 5, 7)**
  - [ ] `PdfRenderer`/`DocxRenderer`: add `judgment_required_findings` to both template contexts; add a conditional section to `report_template.html` and (via the established one-off `python-docx` script) `report_template.docx`, gated on the list being non-empty, using internal-terminology-free labeling.
- [ ] **Task 6 — Verify + security (AC: 9)**
  - [ ] `uv run pytest` green; record before/after pass counts.
  - [ ] `npx vitest run` + `npm run build` (unaffected, confirm no regression).
  - [ ] `/security-review` — resolve Critical/High before marking done.

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

## Change Log

- 2026-08-17: Story drafted (Opus, human-supervised). Scope locked with Marvin before drafting via two rounds: (1) confirmed 3.5 = both report-surfacing AND a consolidated/hardened runtime boundary guard, not either alone; (2) confirmed the new report section renders whenever Tier-3 findings exist, independent of the cleaning opt-in state (not paired/gated with the Healing Manifest). Status → ready-for-dev.
