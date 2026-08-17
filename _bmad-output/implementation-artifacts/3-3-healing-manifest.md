# Story 3.3: Healing Manifest

Status: done

Sizing: M · Model: Opus · loop_eligible: false
<!-- Opus + loop_eligible:false: provenance-critical, human-supervised per explicit
     product decision (not the unattended Claude-Codex loop). The Healing Manifest is
     the client-facing audit trail for every data mutation the pipeline makes — a bug
     here (a mis-classified outcome, a leaked raw cell value, an implied claim that the
     report was computed from cleaned data) is invisible to a naive passing test suite
     and directly undermines the "detect-don't-fix" trust claim the whole product rests
     on. PREREQUISITES (all merged to main): Story 3.1 (PR #39 — RemediationClass,
     classifier), Story 3.2 (PR #42 — CleaningEngine, CleaningAction/CleaningResult),
     Story 3.4 (PR #45 — opt-in gate, Tier-2 imputation policy, cleaning_coordinator).
     Do not start dev until all three are on main (they are, as of 2026-08-13). -->

## Story

As an **SMB owner who opted into automated cleaning**,
I want **a complete, per-action record of exactly what the pipeline did to a separate working copy of my data — what changed, what was attempted but had no effect, what was declined, and what failed — rendered into my report in plain language**,
so that **I can trust the "detect-don't-fix" claim: I can see my original data was never touched, understand precisely what the cleaned export contains, and never mistake the analytical report (which still describes my original data) for a description of the cleaned copy** (Epic 3 INVARIANTS; §2.1 detect-don't-fix; PRD Phase 9 "Healing manifest appears in report").

## Context & scope boundary

Story 3.2's `CleaningAction`/`CleaningResult` (`backend/models/cleaning_result.py`) is **already** built and explicitly documented as *"the single source of provenance for Story 3.3's Healing Manifest... do not add a parallel manifest format — extend this instead."* Story 3.4 wired both Tier-1 (`CleaningEngine`) and Tier-2 (`cleaning_policy`) actions into one merged `CleaningResult`, carried on `PipelineResult.cleaning_result`, but **nothing renders it** — the report is silent about cleaning today even when it ran. This story is that renderer.

1. **IN — outcome classification.** A deterministic function that derives one of four presentation outcomes (Applied / Skipped / Failed / No-Effect) per `CleaningAction`, reconciling a real inconsistency between 3.2 and 3.4 (see **Design decision** below) without modifying either.
2. **IN — the `HealingManifest` model** (`backend/models/healing_manifest.py`): a `ManifestEntry` per action (preserving `CleaningResult.actions` order) plus an aggregate outcome-count summary and a constant report-semantics disclosure string.
3. **IN — a sanitizer** for any text rendered into the manifest, with a stricter bar than 3.2/3.4's existing FAILED-action truncation (see **Data-disclosure boundary** below).
4. **IN — wiring**: `InsightReport.healing_manifest: HealingManifest | None` (mirrors the existing `drift_report` field/pattern), populated in `orchestrator.py` directly after `NarrativeGenerator.generate()` returns — **never** routed through `InsightPayload`, so there is no code path by which manifest content could reach the LLM prompt (stricter than `drift_report`, which is threaded through and explicitly excluded).
5. **IN — rendering in both `DocxRenderer` and `PdfRenderer`**, gated on `healing_manifest is not None`. This is this story's Definition of Done, not deferred to 3.7 (which adds before/after **charts**, a distinct, later concern).
6. **OUT — do not touch `CleaningEngine` or `cleaning_policy`'s status/operation semantics.** One narrow, additive exception: `cleaning_policy._no_effect_action` gains one new `parameters` key (see **Design decision**) — no other field, and no change to `CleaningStatus`, `CleaningOperation`, or any tested behavior.
7. **OUT — Tier-3 (`human_only`) findings.** They never appear in `CleaningResult.actions` today (Tier-3 is never touched, by design) and this story must not enumerate them — that is Story 3.5's job (the Tier-3 boundary story).
8. **OUT — the reasoning/evidence trail for judgment calls** (evidence considered, confidence, rejected alternatives). Per `epic-11-autonomous-judgment-eval-governance.md` §11.5, that is a **distinct, future artifact** ("manifest logs WHAT changed; [11.5] logs WHY") — out of scope here and out of scope for the whole of Epic 3.
9. **OUT — before/after distribution charts** (3.7) and **notebook/code generation from the manifest** (3.8, which explicitly renders FROM this manifest once it exists — do not pre-build any of 3.8's concerns here).
10. **OUT — re-pointing the report at cleaned data.** 3.4 Q1 already settled this: the report continues to describe the **original** frame. This story must make that explicit and unmissable in the rendered output (see AC9), not change it.

## Design decision — reconciling 3.2/3.4's Applied/No-Effect inconsistency

Two shipped, reviewed stories currently disagree on where "the operation ran but changed nothing" belongs:

- **Tier-1** (`CleaningEngine`): a dedup/case/coercion/header op that runs and changes 0 rows/values is still recorded `CleaningStatus.APPLIED` (with `rows_affected=0`/`values_changed=0`).
- **Tier-2** (`cleaning_policy._no_effect_action`): an imputation that runs and fills 0 nulls is deliberately recorded `CleaningStatus.SKIPPED` — the code comment states *"Recording APPLIED here would violate its 'changed the working copy' contract."*

This story does **not** change either status. It derives a presentation-only 4th category, `ManifestOutcome.NO_EFFECT`, computed per action:

| Condition (checked in order) | Manifest outcome |
|---|---|
| `status == FAILED` | `FAILED` |
| `status == APPLIED` and (`rows_affected > 0` or `values_changed > 0`) | `APPLIED` |
| `status == APPLIED` and `rows_affected == 0` and `values_changed == 0` | `NO_EFFECT` |
| `status == SKIPPED` and `operation == NO_OP` | `SKIPPED` |
| `status == SKIPPED` and `parameters.get("manifest_outcome_hint") == "no_effect"` | `NO_EFFECT` |
| `status == SKIPPED` (any other shape) | `SKIPPED` |

**The `manifest_outcome_hint` marker, not operation-type guessing.** An earlier draft of this rule classified any `SKIPPED` action with `operation != NO_OP` as `NO_EFFECT`. Rejected: a future Tier-2 policy could reject a `NULL_IMPUTATION` finding **before** ever calling the primitive (e.g. a validation failure) — that is a decline, not a no-effect attempt, and it would carry the same `operation`/`defect_type`/`remediation_class` tuple as the real no-effect case, so no combination of *existing* fields can tell them apart reliably. The fix is a one-key, additive marker set at the only place that actually knows which case it is: `cleaning_policy._no_effect_action` gains `parameters["manifest_outcome_hint"] = "no_effect"` (verified: no existing test asserts exact `parameters ==` equality for this action, so this is non-breaking). **Fail-closed**: any `SKIPPED` action without this exact marker — including any future skip shape nobody has taught the classifier about — falls through to plain `SKIPPED`, never silently becomes `NO_EFFECT`. `ManifestEntry.original_status` always preserves the true `CleaningStatus` alongside the derived `outcome`, so nothing is lost even if a future author disagrees with the derivation.

## Data-disclosure boundary (stricter than 3.2/3.4's existing truncation)

3.2/3.4's `CleaningAction.error` field is `f"{type(exc).__name__}: {safe_message}"` where `safe_message = str(exc)[:200]` — a **length** cap, not a **content** guarantee. A pandas coercion/parse exception's message can embed the offending cell's repr (e.g. `"could not convert string to float: 'client-name-here'"`). That risk was accepted in 3.2/3.4 as a deferred, pre-existing item (see 3.4's Review Findings) because those actions never left the backend. **This story is the first thing that puts this content in a client-facing document**, so it needs a stricter bar:

- **FAILED entries**: the manifest **never** renders `CleaningAction.error` verbatim. It renders only the exception **type name** (the substring before the first `": "` in the existing, already-consistent `f"{type}: {message}"` format both `cleaning_engine.py` and `cleaning_policy.py` use) plus the action's `target_columns` and `operation` — e.g. *"Type coercion for column 'code' did not complete (ValueError). The working copy was left unchanged for this action."* The full `error` string stays in the underlying `CleaningAction`/logs for engineering debugging; it is simply never surfaced in the rendered report.
- **All other entries** (Applied/Skipped/No-Effect): `detail`/`rule` already come from controlled f-string templates built only from counts, column names, and method names (verified by reading every action-builder in `cleaning_engine.py` and `cleaning_policy.py` — none interpolates a raw cell value or a caught exception). These pass through, still capped by a hard length limit as a second-layer defensive measure.
- **Column names are allowed** everywhere (required for the manifest to be useful) — the boundary is about cell *values*, DataFrame samples, and free-form exception text, not identifiers.
- A single `sanitize_manifest_text(text: str, *, max_len: int = 300) -> str` helper enforces the length cap uniformly; the FAILED-path type-name extraction is a separate, explicit function (`_failed_entry_detail`), not a heuristic applied to arbitrary text.

## Acceptance Criteria

1. **`ManifestOutcome` classification is deterministic and fail-closed.** Given any `CleaningAction`, the outcome derivation follows the table in **Design decision** exactly, in that priority order. An action shape the classifier does not recognize as the known no-effect marker defaults to `SKIPPED` (if `status == SKIPPED`) — it must never guess `NO_EFFECT` from `operation` or `defect_type` alone. Unit-tested against every actual `CleaningAction` shape 3.2's `CleaningEngine` and 3.4's `cleaning_policy` can emit: 4 Tier-1 ops × (applied-with-effect, applied-zero-effect, failed) + Tier-1 skip (no registered op); Tier-2 imputation applied, Tier-2 no-effect (marker present), Tier-2 `leave_as_is` skip, Tier-2 non-imputation skip, Tier-2 failed. A synthetic "future decline" action (`operation=NULL_IMPUTATION`, `status=SKIPPED`, no marker) must classify as `SKIPPED`, not `NO_EFFECT` — this is the regression test for the rejected design.

2. **`cleaning_policy._no_effect_action` gains exactly one additive field.** `parameters["manifest_outcome_hint"] = "no_effect"` is added; `status`, `operation`, `defect_type`, `remediation_class`, `before_state`, `after_state`, `rule`, `detail`, and every other field are byte-identical to today. Full existing `test_cleaning_policy.py` suite passes unmodified (proving no behavioral change). No other function in `cleaning_engine.py` or `cleaning_policy.py` is touched.

3. **`HealingManifest`/`ManifestEntry` preserve deterministic provenance.** Built **only** from `CleaningResult.actions` — no new DataFrame inspection, no re-derivation of what changed. `entries` is in the exact order of `CleaningResult.actions` (never reordered, grouped, or sorted by outcome/operation) with a stable `sequence: int` (0-indexed position) on each entry. Each `ManifestEntry` carries: `sequence`, `remediation_class`, `original_status` (the true `CleaningStatus`), `outcome` (derived `ManifestOutcome`), `operation`, `target_columns`, `rows_affected`, `values_changed`, and a sanitized `detail`. An aggregate `HealingManifest.outcome_counts: dict[str, int]` (keyed by `ManifestOutcome.value`) summarizes the whole run without altering entry order.

4. **Sanitization boundary holds.** FAILED entries never render `CleaningAction.error` verbatim — only the exception type name + operation + target columns (per **Data-disclosure boundary**). No entry's rendered `detail` can exceed `sanitize_manifest_text`'s length cap. A test asserts that a FAILED action whose underlying `error` contains a synthetic "raw cell value" string does NOT have that string anywhere in the corresponding `ManifestEntry.detail`.

5. **Cleaning off/absent → no manifest, zero report change.** When `PipelineResult.cleaning_result is None` (cleaning never ran), `InsightReport.healing_manifest` stays `None`, and DOCX/PDF renderer output is byte-identical to pre-3.3 behavior. Proven by (a) the full pre-existing suite passing unchanged and (b) an explicit regression test rendering both formats with `healing_manifest=None` and diffing against a captured pre-3.3 baseline (or asserting the manifest section is structurally absent from the output).

6. **Cleaning on → manifest renders in both DOCX and PDF**, each showing: the outcome-count summary, the per-entry detail (operation, target columns, outcome, sanitized detail) in `CleaningResult.actions` order, and the constant report-semantics disclosure (AC9). Both renderers receive equivalent content from the same `HealingManifest` object — no format-specific data loss. Rendered against the `cleaning_dirty_df` fixture (`backend/tests/conftest.py`) run through the full Tier-1+Tier-2 coordinator, covering Applied, No-Effect–eligible, and Skipped entries in one real manifest.

7. **`healing_manifest` never reaches the LLM.** Structurally verified: `InsightPayload` gains no new field for this, `NarrativeGenerator`/`InsightEngine` are not modified, and `orchestrator.py` sets `insight_report.healing_manifest` only **after** `NarrativeGenerator.generate()` has already returned. A test asserts `InsightPayload` has no `healing_manifest`-shaped attribute and that mocking the LLM client and asserting on its call arguments shows no cleaning-related content in the prompt.

8. **No Tier-3 enumeration.** `HealingManifest` contains zero entries derived from `human_only` findings — proven on `cleaning_dirty_df` (whose Tier-3 `negative_values` finding on `quantity` never becomes a `CleaningAction` at all, per 3.4 AC6) by asserting no `ManifestEntry` references that finding.

9. **Report-semantics disclosure is present and accurate whenever the manifest renders.** `HealingManifest.report_semantics_disclosure` is a constant string equivalent to: *"Cleaning was performed on a separate working copy. The original data was not modified, and the analytical report continues to use the original dataset."* It appears in both rendered formats, adjacent to the manifest section, whenever `healing_manifest is not None`. Test asserts the exact disclosure text (or an unambiguous equivalent) is present in both rendered outputs and that no other report section (executive summary, key findings, anomaly analysis, recommendations) changes wording based on whether cleaning ran — i.e. cleaning-on and cleaning-off runs against the same input produce identical narrative-section content, differing only in the presence of the manifest section.

10. **Tests, full suite, and security gate.** New `backend/tests/test_healing_manifest.py` (classification + sanitization + model construction, AC1-4) and additions to renderer tests (AC5-6) and an orchestrator/report e2e test (AC7-9). Full suite green via `uv run pytest` (record before/after pass counts); frontend unaffected (`npx vitest run`, `npm run build` — this story touches no frontend code). Run `/security-review`; resolve any Critical/High before marking done — reviewer should specifically probe: can any raw cell value, DataFrame sample, or full exception message reach the rendered manifest; can the manifest ever list a Tier-3 finding; can `healing_manifest` content reach the LLM prompt under any code path.

## Tasks / Subtasks

- [x] **Task 0 — Confirm prerequisites (AC: all)**
  - [x] Verify PR #39, #42, #45 are on `main`; `CleaningAction`/`CleaningResult`/`CleaningStatus`/`CleaningOperation`, `RemediationClass`, `cleaning_coordinator.clean_dataset`, `InsightReport.drift_report` (as the wiring precedent) are all importable. HALT if not.
  - [x] Re-read `backend/models/cleaning_result.py`, `backend/pipeline/cleaning_engine.py`, and `backend/rules/cleaning_policy.py` in full; enumerate every `CleaningAction`-emitting code path (this is the fixture list for Task 2's tests).
- [x] **Task 1 — `cleaning_policy._no_effect_action` marker (AC: 1, 2)**
  - [x] Add `parameters["manifest_outcome_hint"] = "no_effect"` inside `_no_effect_action` in `backend/rules/cleaning_policy.py`. No other change in that file.
  - [x] Run `test_cleaning_policy.py` unmodified — confirm it still passes (proves non-breaking).
- [x] **Task 2 — `backend/models/healing_manifest.py` (AC: 1, 3, 4)**
  - [x] `ManifestOutcome` enum: `APPLIED`, `SKIPPED`, `FAILED`, `NO_EFFECT`.
  - [x] `classify_outcome(action: CleaningAction) -> ManifestOutcome` implementing the **Design decision** table exactly, in priority order.
  - [x] `sanitize_manifest_text(text: str, *, max_len: int = 300) -> str` — length cap (defensive second layer).
  - [x] `_failed_entry_detail(action: CleaningAction) -> str` — extracts exception type name only (split `action.error` on first `": "`), builds the controlled-template sentence; never touches the message half.
  - [x] `ManifestEntry` Pydantic model: `sequence`, `remediation_class`, `original_status`, `outcome`, `operation`, `target_columns`, `rows_affected`, `values_changed`, `detail`.
  - [x] `HealingManifest` Pydantic model: `pipeline_run_id`, `cleaned_at`, `rows_before/after`, `columns_before/after`, `entries: list[ManifestEntry]` (order-preserving), `outcome_counts: dict[str, int]`, `report_semantics_disclosure: str` (the constant from AC9).
  - [x] `build_healing_manifest(result: CleaningResult) -> HealingManifest` — `enumerate(result.actions)` in order; for FAILED actions call `_failed_entry_detail`, else `sanitize_manifest_text(action.detail)`.
- [x] **Task 3 — Wiring (AC: 5, 6, 7)**
  - [x] Add `healing_manifest: HealingManifest | None = None` to `InsightReport` (`backend/models/insight_report.py`), mirroring the `drift_report` field's docstring style.
  - [x] In `orchestrator.py`, immediately after `result.insight_report = insight_report` (i.e. strictly after `NarrativeGenerator.generate()` returns — never before, never via `InsightPayload`): if `result.cleaning_result is not None`, set `insight_report.healing_manifest = build_healing_manifest(result.cleaning_result)`.
  - [x] Confirm (by reading, not just testing) that no code path threads `cleaning_result`/`healing_manifest` through `InsightPayload`, `InsightEngine`, or `NarrativeGenerator`.
- [x] **Task 4 — Renderers (AC: 5, 6, 9)**
  - [x] `PdfRenderer`: add `"healing_manifest": insight_report.healing_manifest` to the template context; edit `backend/renderers/templates/report_template.html` to add a conditional "Data Cleaning" section (summary counts, disclosure text, per-entry list) mirroring the existing `drift_report` conditional block's structure.
  - [x] `DocxRenderer`: add `"healing_manifest": insight_report.healing_manifest` to the template context; edit the binary `backend/renderers/templates/report_template.docx` via a one-off `python-docx` script (append `{% if healing_manifest %}...{% endif %}` paragraphs after the existing Drift Analysis block, mirroring its exact Jinja-tag-per-paragraph pattern — see Dev Notes) and commit the regenerated `.docx`.
  - [x] Regression test: cleaning-off render of both formats byte-diffed / structurally compared against a pre-3.3 captured baseline.
- [x] **Task 5 — Tests (AC: 1-10)**
  - [x] `backend/tests/test_healing_manifest.py`: classification table (every real shape + the synthetic "future decline" regression), sanitizer, FAILED detail extraction (raw-value-not-leaked test), model/order-preservation.
  - [x] Renderer tests (docx/pdf): manifest section present/absent, disclosure text present, no narrative-content drift between cleaning-on/off runs.
  - [x] Orchestrator/e2e test: full pipeline run with cleaning enabled against `cleaning_dirty_df`, asserting `insight_report.healing_manifest` is populated, Tier-3 finding absent from entries, and LLM-prompt-shape assertion (AC7).
- [x] **Task 6 — Verify + security (AC: 10)**
  - [x] `uv run pytest` green; record before/after pass counts.
  - [x] `npx vitest run` + `npm run build` (unaffected, confirm no regression).
  - [x] `/security-review` — resolve Critical/High before marking done.

## Dev Notes

### Why the DOCX template needs a script, not a text edit

`report_template.docx` is a real Word document (docxtpl renders Jinja tags embedded in Word paragraphs), not a text file — it cannot be edited with `Edit`. Inspect it with `python-docx` first:

```python
from docx import Document
doc = Document("backend/renderers/templates/report_template.docx")
for i, p in enumerate(doc.paragraphs):
    print(i, p.style.name, repr(p.text))
```

As of this story's drafting, the template is 31 paragraphs (0-30); paragraph 30 is the final `{% endif %}` closing the existing `{% if drift_report %}` block (paragraphs 23-30: `Drift Analysis` heading, severity line, summary, a `{% for rec in drift_report.recommendations %}` loop, `endfor`, `endif`). There are no tables (`len(doc.tables) == 0`) and one section. Append the new block with `doc.add_paragraph(text, style=...)` calls (appends at the end of the body, after the existing content) using the **same one-Jinja-tag-per-paragraph convention** already established (never put `{% if %}` and content on the same paragraph — each control tag is its own paragraph, matching every existing block). Save over the same path; commit the regenerated binary. Verify by re-running the inspection script post-edit and by an actual `DocxRenderer().render(...)` call in a test.

### PDF template pattern to mirror

`report_template.html` is a normal Jinja2/HTML file — edit directly. Find the existing `{% if drift_report %}...{% endif %}` block and add an analogous `{% if healing_manifest %}` block immediately after it, using the same heading/paragraph HTML structure already in use for the Drift Analysis section.

### Concrete manifest content example (for the section copy)

Using `cleaning_dirty_df` with cleaning enabled, the rendered manifest should be able to say (paraphrased, exact wording is implementation's call as long as it's accurate and uses the sanitized fields):

- Summary: 4 Applied (case normalization, type coercion, deduplication, header normalization — all Tier-1), 1 Applied (null imputation — Tier-2), 0 Skipped, 0 Failed, 0 No-Effect.
- Per-entry: e.g. *"Normalized casing in 'region': 3 value(s) rewritten across 3 variant(s)."* (Tier-1, already-safe controlled text, passed through as-is.)
- Disclosure line present once, near the top or bottom of the section (implementation's call), verbatim per AC9.

To exercise the FAILED/sanitization path (AC4), a dedicated unit test should construct a synthetic `CleaningAction` directly (not via the real engine, which doesn't currently produce a FAILED action against this fixture) with `error="ValueError: could not convert string to float: 'super-secret-client-name'"` and assert `"super-secret-client-name"` does not appear anywhere in the built `ManifestEntry.detail`.

### Naming: `ManifestOutcome` vs `CleaningStatus`

Deliberately two different enums with overlapping-but-not-identical value sets (`CleaningStatus` has 3 values; `ManifestOutcome` has 4). Do not conflate them or try to make `ManifestOutcome` a superset/subclass of `CleaningStatus` — `ManifestEntry.original_status: CleaningStatus` and `ManifestEntry.outcome: ManifestOutcome` are two separate, explicitly named fields so a reader (and a future auditor) can always see both the raw engine status and the derived presentation category.

### Previous-story intelligence (3.2 / 3.4)

- 3.2/3.4 key everything on `defect_type`/exact status+operation tuples, never fuzzy string matching on `detail`/`rule` prose — mirror this discipline in `classify_outcome`; it must never pattern-match on human-readable text, only on typed fields (`status`, `operation`, `rows_affected`, `values_changed`, the one new `parameters` marker key).
- 3.4's highest-severity review finding was a false `APPLIED` status hiding a zero-effect action — this story exists specifically to give that distinction an honest, correctly-derived presentation, without repeating 3.4's mistake of conflating "ran" with "changed something."
- 3.4's Review Findings explicitly deferred the "200-char truncation doesn't guarantee no raw cell value" gap as *"pre-existing... not a new gap uniquely introduced by this diff."* That deferral was correct **at the time** because nothing rendered it to a client. This story is what makes it live — do not re-defer it here; AC4 exists precisely to close it at the point where it first matters.

### Invariants (Epic 3 — must not drift)

- Working-copy only; original data NEVER modified — and this story must **say so explicitly** in every rendered manifest (AC9).
- Every remediation logged — this story is the first consumer that actually surfaces that log to the client.
- Tier-3 `human_only` NEVER auto-touched, and NEVER appears in this manifest (that boundary's *handling* is 3.5's story; this story just must not accidentally imply Tier-3 findings were considered).
- Report continues to describe the **original** frame (3.4 Q1) — the manifest must not create any implication otherwise.

### References

- [Source: _bmad-output/implementation-artifacts/epic-3-cleaning-engine.md#INVARIANTS] — "Every remediation logged in the healing manifest."
- [Source: _bmad-output/implementation-artifacts/epic-3-cleaning-engine.md#Story-notes-3.4] — "Defaults printed in the healing manifest."
- [Source: _bmad-output/implementation-artifacts/epic-11-autonomous-judgment-eval-governance.md#11.5] — the manifest-vs-decision-log artifact boundary (out of scope here).
- [Source: _bmad-output/planning-artifacts/saint-master-prd.md, Phase 9 DoD] — "Healing manifest appears in report."
- [Source: backend/models/cleaning_result.py] — `CleaningAction`/`CleaningResult`/`CleaningStatus`/`CleaningOperation`; the one provenance model, do not duplicate.
- [Source: backend/pipeline/cleaning_engine.py] — every Tier-1 `CleaningAction`-emitting path (`_deduplicate`, `_normalize_case`, `_coerce_types`, `_normalize_headers`, `_skipped_action`, `_failed_action`).
- [Source: backend/rules/cleaning_policy.py] — every Tier-2 path (`_applied_action`, `_no_effect_action`, `_leave_as_is_action`, `_skipped_non_imputation`, `_failed_action`).
- [Source: backend/models/insight_report.py] — `drift_report` field, the wiring pattern to mirror.
- [Source: backend/pipeline/narrative_generator.py:41,43] — `drift_report` excluded from the LLM-facing JSON, set on the report by code after generation; healing_manifest goes further (never even threaded through `InsightPayload`).
- [Source: backend/pipeline/orchestrator.py:220-265] — exact wiring point (after `result.insight_report = insight_report`, before Stage 5 render).
- [Source: backend/renderers/docx_renderer.py, pdf_renderer.py] — template context dicts; both need the new `healing_manifest` key.
- [Source: backend/renderers/templates/report_template.html, report_template.docx] — the `drift_report` conditional block to mirror in both formats.
- [Source: backend/tests/conftest.py:166+] — `cleaning_dirty_df`, the fixture exercising Tier-1/2/3 in one frame.
- [Source: _bmad-output/implementation-artifacts/3-4-opt-in-gate-config.md] — the `_no_effect_action` origin story and its Review Findings (the deferred truncation gap this story closes).

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (human-supervised implementation, high effort)

### Debug Log References

- Task 1 (marker addition): `uv run pytest backend/tests/test_cleaning_policy.py` → 25 passed (unmodified, proves non-breaking).
- Task 2 (model + unit tests): `uv run pytest backend/tests/test_healing_manifest.py -v` → 26 passed (classification for every real 3.2/3.4 shape + the fail-closed regression + sanitization + ordering/provenance + real-fixture integration).
- Task 3-4 (wiring + renderers): `uv run pytest` (full backend) → 368 passed / 1 skipped (baseline before this story: 356 passed / 1 skipped → +12 new tests via renderer additions, 0 regressions). Frontend/build unaffected (this story touches no frontend code): `npx vitest run` → 18/18; `npm run build` → OK.
- `/security-review` (dedicated sub-agent, diff-scoped) → zero qualifying findings. Explicitly verified Jinja2 `autoescape=True` still holds in `pdf_renderer.py`, no `|safe`/`Markup()` introduced anywhere in the diff, `_failed_entry_detail` confirmed to never expose the raw exception message (only the type name), docxtpl's text-run insertion model confirmed not vulnerable to template injection via column-name content.

### Completion Notes List

- **Outcome classification (AC1)** — `classify_outcome` implements the locked priority-ordered rule exactly: FAILED status always wins; APPLIED splits on rows_affected/values_changed > 0; SKIPPED splits on `operation == NO_OP` vs. the explicit `manifest_outcome_hint` marker, defaulting to SKIPPED for any unrecognized shape. The rejected "operation != NO_OP" heuristic is pinned as a named regression test (`test_skipped_non_op_without_marker_stays_skipped`).
- **Marker (AC2)** — `cleaning_policy._no_effect_action` gained exactly one `parameters` key; `test_cleaning_policy.py` passes completely unmodified, confirming zero behavioral change to Story 3.4's shipped code.
- **Provenance (AC3)** — `ManifestEntry`/`HealingManifest` built purely from `CleaningResult.actions`, order preserved via `enumerate`, `sequence`/`original_status`/`outcome` all carried alongside the existing fields.
- **Sanitization (AC4)** — FAILED entries route through `_failed_entry_detail`, which discards everything after the first `": "` in `action.error`, so only the exception type name (plus operation + target columns) ever reaches the manifest. Verified with a synthetic action whose `error` embeds a fake raw value (`"super-secret-client-name"`) — asserted absent from the built entry's `detail`. All other entries pass through `sanitize_manifest_text`'s length cap.
- **Cleaning-off regression (AC5)** — new renderer tests assert `"Data Cleaning"` is absent from both DOCX XML and the PDF-bound HTML string when `healing_manifest` is `None`; full pre-existing suite (including 3.4/3.6's own regression tests) passes unmodified.
- **Both formats render (AC6)** — `report_template.html` (direct edit) and `report_template.docx` (regenerated via a one-off `python-docx` script appending the same one-Jinja-tag-per-paragraph convention the existing Drift Analysis block already used) both gained a conditional "Data Cleaning" section; tests assert equivalent content lands in both.
- **Never reaches the LLM (AC7)** — structurally verified two ways: `InsightPayload.model_fields` has no `healing_manifest`/`cleaning_result`-shaped field, and an e2e test captures `NarrativeGenerator.generate`'s actual call arguments, asserting the `payload` argument has neither attribute. `insight_report.healing_manifest` is set in `orchestrator.py` strictly after `generate()` already returned.
- **No Tier-3 enumeration (AC8)** — both the unit-level fixture test and the orchestrator e2e test assert no `ManifestEntry.remediation_class == HUMAN_ONLY`; Tier-3 findings never become `CleaningAction`s in the first place (3.4 AC6), so this is structurally guaranteed, not just tested.
- **Report-semantics disclosure (AC9)** — `HealingManifest.report_semantics_disclosure` defaults to the exact locked constant; new tests assert the constant's presence in both rendered formats and assert narrative-section content (executive summary, key findings, anomaly analysis, recommendations) is byte-identical between cleaning-on and cleaning-off runs using FRESH (non-shared) `InsightReport` instances per run — a stricter check than 3.4's existing `test_enabling_does_not_change_the_report`, which reuses one canned fixture object across both calls and would trivially pass on object identity alone.
- **Tests + security (AC10)** — 372 passed / 1 skipped full backend suite (+16 over the 356 pre-story baseline: 12 from initial implementation + 4 from code-review fixes), frontend/build unaffected, `/security-review` clean (zero qualifying findings, dedicated diff-scoped sub-agent).

### Review Findings

Code review (8-angle: line-by-line, removed-behavior, cross-file, reuse, simplification, efficiency, altitude, conventions; high effort, recall-biased) — 4 confirmed findings, all fixed:

- [x] [Review][Patch] `build_healing_manifest` routed FAILED-entry detail through `_failed_entry_detail` directly, bypassing `sanitize_manifest_text`'s length cap entirely — violated the story's own AC4 uniform-length-guarantee. RESOLVED: `_failed_entry_detail` now returns `sanitize_manifest_text(detail)`. New regression test `test_failed_detail_respects_the_length_cap` (100 target_columns, asserts `len(detail) <= 300`). [`backend/models/healing_manifest.py`, `backend/tests/test_healing_manifest.py`]
- [x] [Review][Patch] `_failed_entry_detail`'s exception-type extraction failed OPEN, not closed: `action.error.split(": ", 1)[0]` returns the WHOLE string when no `": "` delimiter is present, and the `or "an error"` fallback never triggers on a non-empty result — a future `error` value not following the `"Type: message"` convention would leak verbatim into the client-facing manifest. RESOLVED: now checks `len(parts) == 2 and parts[0]` before trusting the split; falls back to `"an error"` otherwise. New regression test `test_error_not_following_type_colon_message_convention_fails_closed`. [`backend/models/healing_manifest.py`, `backend/tests/test_healing_manifest.py`]
- [x] [Review][Patch] `manifest_outcome_hint`/`"no_effect"` were duplicated as bare string literals in `cleaning_policy.py`, disconnected from `healing_manifest.py`'s classifier by convention alone — a future rename/typo in either file would silently break the NO_EFFECT/SKIPPED distinction with no import error, type error, or test failure to catch it. RESOLVED: promoted to public `NO_EFFECT_HINT_KEY`/`NO_EFFECT_HINT_VALUE` constants exported from `healing_manifest.py`; `cleaning_policy.py` now imports and uses them (verified no circular import). New regression test `test_no_effect_action_uses_the_shared_constant_not_a_hardcoded_string`. [`backend/models/healing_manifest.py`, `backend/rules/cleaning_policy.py`, `backend/tests/test_healing_manifest.py`]
- [x] [Review][Patch] No test drove the REAL `cleaning_policy._no_effect_action` code path through `classify_outcome` end-to-end — every existing test either hand-built the marker into a synthetic `CleaningAction` or never asserted on the key at all, so a future refactor dropping the marker line would leave the full suite green. RESOLVED: new `TestRealNoEffectActionClassifiesCorrectly` calls the real `apply_imputation_policy` against an all-null column and asserts the resulting action classifies as `ManifestOutcome.NO_EFFECT`. [`backend/tests/test_healing_manifest.py`]
- [x] [Review][Defer] `HealingManifest.outcome_counts` is precomputed/stored state that duplicates what `Counter(e.outcome for e in entries)` would give for free — a theoretical drift risk if `entries` were ever mutated post-construction. Deferred: `HealingManifest`/`ManifestEntry` are only ever constructed once, atomically, by `build_healing_manifest`; nothing in this diff or its callers mutates `entries` afterward, and converting to a Pydantic `@computed_field` would introduce a pattern with no precedent elsewhere in the codebase for a benefit the finding's own author rated medium-confidence. Not applied. [`backend/models/healing_manifest.py`]
- [x] [Review][Defer] A wide dataset (many cleaned columns) could produce a long `<ul>` in the PDF's "Data Cleaning" section, and `page-break-inside: avoid` on `.section` could cause awkward WeasyPrint pagination — mirrors a pre-existing pattern (`drift_report`'s recommendations list uses the same CSS) scaled up to a potentially longer list. Deferred: a PDF layout/UX decision (e.g. capping displayed entries with "N more"), not a correctness or security issue; no AC covers dataset-width-driven report pagination. Not applied. [`backend/renderers/templates/report_template.html`]
- [x] [Review][Defer] `_failed_entry_detail`'s error-type extraction still trusts `action.error`'s format is `"Type: message"` by convention (now fail-closed on the split, per the Patch above, but still a convention, not a schema). A structured `error_type: str | None` field on `CleaningAction` would remove the string-parsing dependency entirely. Deferred: would touch Story 3.2's shipped model file beyond the story's explicitly locked scope ("do not touch CleaningEngine or cleaning_policy's status/operation semantics"); a comment was added to `CleaningAction.error` instead, pointing future consumers at `build_healing_manifest` as the required sanitization boundary. Not applied as a schema change. [`backend/models/cleaning_result.py`]
- [x] [Review][Refute] Reuse angle flagged `sanitize_manifest_text`/`_failed_entry_detail`'s error-type-splitting as a third independent re-implementation of the `"Type: message"` truncation convention already present in `cleaning_engine.py`/`cleaning_policy.py`. Refuted as a blocking issue: those two existing implementations serve `CleaningAction.error`'s internal/engineering-log use (unbounded, never client-facing); this story's functions serve a stricter client-facing bar (type-name-only, hard length cap) that is deliberately NOT the same operation — sharing a helper would conflate two different trust boundaries. Noted for awareness, not fixed.
- `/security-review` re-run after fixes (dedicated diff-scoped sub-agent) — zero qualifying findings; Jinja2 `autoescape=True` confirmed still in effect, no `|safe`/`Markup()` introduced, `_failed_entry_detail` confirmed to never expose the raw exception message.

### File List

- `backend/models/healing_manifest.py` (A) — `ManifestOutcome`, `classify_outcome`, `sanitize_manifest_text`, `_failed_entry_detail`, `ManifestEntry`, `HealingManifest`, `build_healing_manifest`, `REPORT_SEMANTICS_DISCLOSURE`.
- `backend/rules/cleaning_policy.py` (M) — `_no_effect_action` gains one additive `parameters["manifest_outcome_hint"] = "no_effect"` key. No other change.
- `backend/models/insight_report.py` (M) — additive `healing_manifest: HealingManifest | None = None` field.
- `backend/pipeline/orchestrator.py` (M) — populates `insight_report.healing_manifest` after `NarrativeGenerator.generate()` returns, when `result.cleaning_result is not None`.
- `backend/renderers/pdf_renderer.py` (M) — `healing_manifest` added to the Jinja2 template context.
- `backend/renderers/docx_renderer.py` (M) — `healing_manifest` added to the docxtpl template context.
- `backend/renderers/templates/report_template.html` (M) — new conditional "Data Cleaning" section + `.disclosure-note` CSS class, mirroring the existing Drift Analysis block.
- `backend/renderers/templates/report_template.docx` (M, binary) — regenerated via a one-off `python-docx` script; same conditional section appended after the existing Drift Analysis block.
- `backend/tests/test_healing_manifest.py` (A) — 26 tests: classification (every real shape + fail-closed regression), sanitization, FAILED-detail extraction, ordering/provenance, real-fixture integration.
- `backend/tests/test_renderers.py` (M) — +6 tests: manifest present/absent for both formats, narrative-content-unchanged check.
- `backend/tests/e2e/test_healing_manifest_wiring.py` (A) — 6 tests: full orchestrator wiring with fresh (non-shared) report instances, LLM-payload-shape structural assertions.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (M) — 3-3-healing-manifest → ready-for-dev, then this session → review.

## Change Log

- 2026-08-17: Story drafted (Opus, human-supervised). Provenance contract locked with Marvin before drafting: (1) 4-way outcome derivation via priority-ordered rule with an explicit `manifest_outcome_hint` marker (not operation-type guessing) for the Tier-2 no-effect case, fail-closed for unrecognized shapes; (2) `ManifestEntry` preserves `sequence`, `original_status`, and full provenance fields in `CleaningResult.actions` order; (3) stricter data-disclosure boundary than 3.2/3.4 — FAILED entries never render raw exception messages, only the exception type; (4) constant report-semantics disclosure required in every rendered manifest. Status → ready-for-dev.
- 2026-08-17: Implemented (Opus, human-supervised, high effort). `HealingManifest`/`ManifestEntry` model + fail-closed classification + sanitization boundary; one-key additive marker in `cleaning_policy.py`; wiring through `InsightReport`/orchestrator (never via `InsightPayload`); both DOCX and PDF renderers extended with a conditional "Data Cleaning" section. 368 passed / 1 skipped (+12 over 356 baseline, 0 regressions); frontend/build unaffected; `/security-review` clean (zero qualifying findings). Status → review.
