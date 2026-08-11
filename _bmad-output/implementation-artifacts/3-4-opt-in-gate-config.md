# Story 3.4: Opt-in Gate & Configuration (default OFF)

Status: done

Sizing: M · Model: Opus · loop_eligible: false
<!-- Opus + loop_eligible:false: this story crosses the Tier-2 policy boundary AND owns
     the opt-in gate that makes the (data-mutating) Cleaning Engine reachable at all.
     Two failure modes here are invisible to a naive passing test suite: (1) the gate
     defaults ON, or is flippable by something other than explicit client policy, shipping
     always-on cleaning; (2) the Tier-2 policy layer touches a finding it must not
     (a human_only Tier-3 finding, or a Tier-2 finding of the wrong kind). Both are the
     same class of load-bearing safety guard 3.2 was gated on. Not loop-eligible: security/
     access-control surface (the enablement boundary) + first Tier-2 execution path.
     PREREQUISITES (both merged to main): Story 3.1 (PR #39 — RemediationClass, classifier)
     and Story 3.2 (PR #42 — CleaningEngine, cleaning_primitives incl. impute_nulls,
     CleaningAction/CleaningResult). Do not start dev until both are on main. -->

## Story

As an **SMB owner running SAINT on my data**,
I want **to opt into automated cleaning and (optionally) set a per-column null-imputation policy once — with defensible defaults chosen for me when I don't — so that the pipeline applies both the Tier-1 autonomous fixes and my Tier-2 imputation policy to a working copy and records exactly what it did**,
so that **cleaning is something I deliberately turn on (never on by default), a non-expert is never blocked at step one by an imputation choice, and every remediation stays fully logged while my original data and every Tier-3 finding are never touched** (Epic 3 INVARIANTS; §2.1 detect-don't-fix; four-tier ownership model).

## Context & scope boundary

Story 3.2 shipped the deterministic engine and the policy-less `impute_nulls` primitive but **deliberately left them unwired** — wiring cleaning unconditionally into `run_full_pipeline` would ship always-on cleaning. This story builds the **gate** that makes the engine safely reachable and the **Tier-2 policy layer** that drives the imputation primitive. Explicitly:

1. **IN — the opt-in gate.** A single default-OFF enablement flag that controls whether *any* cleaning runs. Surfaced at three layers that already exist: `config.yaml` (`cleaning.enabled`, default `false`), the `run_full_pipeline(...)` signature (`enable_cleaning: bool = False`), and the Typer CLI (`--clean/--no-clean`, default no-clean). When off, no cleaning component is constructed and behaviour is byte-identical to today.
2. **IN — the Tier-2 policy layer** (`backend/rules/`): a `CleaningPolicy` model + per-column-type default resolution (median for numerics, mode for categoricals, forward-fill for datetime/time-indexed) + a policy executor that consumes **only** Tier-2 `null_values` findings, resolves a method per column, drives the existing `impute_nulls` primitive, and emits `CleaningAction`s. Client MAY override per column or per type; when they don't, defaults apply so a non-expert is never blocked.
3. **IN — orchestrator wiring** behind the gate: after DQA succeeds, run Tier-1 (`CleaningEngine.clean`) then Tier-2 (policy imputation) on the same working copy, producing one cleaned frame + one merged `CleaningResult`, attached to `PipelineResult.cleaning_result`.
4. **IN — interim persistence:** the policy lives in `config.yaml` via `PipelineConfig` (the real, existing YAML→Pydantic config mechanism). See **Reality corrections** — the `project.cleaning_policy` entity does not exist yet.
5. **OUT — do NOT build:** the Healing Manifest document (3.3 renders it from `CleaningResult`); cleaned-data export / writing the cleaned frame to disk (3.6); report visualizations & before/after comparison (3.7); any client-facing copy or method descriptions (3.9); Tier-3 candidate scoring/handling (3.5); the `project` DB entity, SQLAlchemy, Alembic, or any database (Epic 4 Story 4.1); orphaned-FK / `non_unique_id` resolution (a Tier-2 concern, but FK-rule not imputation — out of this story's imputation-defaults scope).
6. **OUT — do NOT modify `CleaningEngine`'s autonomy.** Story 3.2 AC2 froze it: "There is no parameter, flag, or environment variable that widens [Tier-1-only dispatch]." The Tier-2 policy layer is a **separate** component that calls the `impute_nulls` primitive directly. Do not add imputation, policy, or a Tier-2 branch inside `CleaningEngine`.
7. **OUT — do NOT re-point the report at cleaned data.** In this story the Insight Engine / Narrative / Renderer continue to run on the **original** frame; the cleaned frame + `CleaningResult` are *produced and carried*, not fed back into report generation. Changing what the report describes is a report-semantics decision coupled to 3.7's before/after view — see **Open questions (Q1)**.

## Reality corrections (verified against `main`, 2026-07-22)

These artifacts describe infrastructure that does not exist. Treat the code on `main` as authoritative (same discipline as the R-1 story's `savvycortex/`-package correction).

- **`rules/rule_engine.py` does NOT exist, and there is no `backend/rules/` package.** `epic-3-cleaning-engine.md` (§3.4 note) and `schema-extensions-spec.md` (§1, Tier-2 note) both say to "extend the existing `rules/rule_engine.py` YAML-config pattern … Not a new mechanism." There is no such file and no alerting rule engine. The **real** "existing YAML-config pattern" is `PipelineConfig` (`backend/models/pipeline_config.py`) loading `config.yaml` via `PipelineConfig.load()` — flat YAML sections wrapped into validated Pydantic sub-models (`ThresholdConfig`, `ScheduleConfig`, `AlertConfig`, …). **Model `backend/rules/` on that pattern.** You are creating `backend/rules/` fresh; the "not a new mechanism" claim refers to reusing the YAML→Pydantic *style*, not an actual module.
- **The `project` entity does not exist.** `schema-extensions-spec.md` §3 places `project` (with its `cleaning_policy` child) in **Epic 4 Story 4.1**, designed alongside multi-tenancy. 3.4 must not introduce it. Interim home for the policy is `config.yaml`; the migration to `project.cleaning_policy` is Epic 4's Story 4.1a's job. Add a one-line seam note in the config model docstring so the future migration is obvious.
- **`impute_nulls` has no `leave_as_is` method.** `IMPUTATION_METHODS = {"mean", "median", "mode", "forward_fill"}` (`cleaning_primitives.py:30`). The four-tier model lists "mean/median/mode/forward-fill/**leave-as-is**" as Tier-2 options. Implement `leave_as_is` in the **policy layer** (resolve → skip, record a SKIPPED action, do NOT call the primitive). Do **not** add it to `IMPUTATION_METHODS` or to the primitive.

## Acceptance Criteria

1. **Opt-in gate, default OFF (load-bearing).** Cleaning runs only when explicitly enabled. `config.yaml` `cleaning.enabled` defaults `false`; `run_full_pipeline(..., enable_cleaning: bool = False)`; CLI `--clean/--no-clean` defaults to no-clean. **When disabled, no cleaning component is constructed, `PipelineResult.cleaning_result is None`, and downstream output is byte-identical to today** — proven by (a) the full pre-existing suite passing unchanged (baseline **279 passed / 1 skipped**) and (b) an explicit test that a run with cleaning disabled yields `cleaning_result is None` and the same rendered/insight output as a run of the current pipeline. No environment variable, and nothing other than an explicit enable, turns cleaning on.

2. **Config surface + validation, backward-compatible.** A new `CleaningConfig` sub-model on `PipelineConfig` parses a `cleaning:` section: `enabled: bool = False`, plus optional imputation policy (per-type default overrides and per-column overrides). **The section is fully optional** — every existing `config.yaml` (which has no `cleaning:` key) validates unchanged and yields `enabled=False`. Every method value is validated against the allowlist `{mean, median, mode, forward_fill, leave_as_is}`; an unknown method raises `ConfigurationError` at load time (fail-loud, consistent with `PipelineConfig.load`). `mean`/`median` on a non-numeric column is caught (by the primitive's existing guard) and recorded as a FAILED action, never a crash mid-pipeline.

3. **Per-column-type imputation defaults (core deliverable).** With `cleaning.enabled: true` and **no imputation config at all**, every Tier-2 `null_values` finding still resolves to a defensible method by column type: **numeric → `median`** (robust to the outliers an SMB's revenue/quantity columns carry), **categorical (object/string) → `mode`**, **datetime dtype or `DatetimeIndex` → `forward_fill`**. Resolution precedence (highest first): (i) per-column override → (ii) per-type default override → (iii) built-in default-by-type. An SMB who never touches imputation config is never blocked and gets sensible fills; each applied method and its source (`default` vs `override`) is recorded in the action's `parameters`.

4. **Tier-2 policy execution drives the existing primitive.** The policy executor consumes **only** findings with `remediation_class == HUMAN_POLICY_AGENT_EXECUTION` **and** `defect_type == "null_values"`. For each, it resolves the method (AC3), and — unless the method is `leave_as_is` — calls `cleaning_primitives.impute_nulls(df, column, method)` on the working copy and records one `CleaningAction` (`operation=NULL_IMPUTATION`, `scope=COLUMN`, `remediation_class=HUMAN_POLICY_AGENT_EXECUTION`, `status=APPLIED`, `values_changed` = nulls filled, `parameters={"method", "source"}`, `rule`, `detail`). `leave_as_is` records a SKIPPED action with zero data change and no primitive call. **The primitive is used exactly as shipped — no signature change.**

5. **Non-imputation Tier-2 and all non-Tier-2 findings are never acted on (fail-closed).** `non_unique_id` (also `HUMAN_POLICY_AGENT_EXECUTION`, but FK/ID resolution — out of scope) and any other Tier-2 `defect_type` produce a SKIPPED action and **zero data change** — the executor has an explicit `null_values`-only allowlist, mirroring the engine's registry discipline. No config key or flag widens the policy layer beyond Tier-2 `null_values`.

6. **Tier-3 / `human_only` NEVER touched, even on a shared column (load-bearing).** Proven on the `cleaning_dirty_df` fixture: with cleaning enabled, the two `null_values` nulls in `quantity` (rows 0,1) are imputed **while the Tier-3 `negative_values` finding on the same `quantity` column (row 2, `-5`) is left byte-identical** — the negative value is not "fixed", not nulled, not dropped. A test asserts the `-5` survives and no `CleaningAction` references a `human_only` finding.

7. **Working-copy only, end to end (load-bearing).** The caller's DataFrame is never mutated across the *combined* Tier-1 + Tier-2 pass — asserted by `pd.testing.assert_frame_equal` against a pristine pre-call copy of the maximally-dirty fixture, after a full enabled clean. Tier-1 (`CleaningEngine.clean`) already deep-copies; the Tier-2 executor must also never mutate its input frame (return a new/copied frame, matching `impute_nulls`'s own copy-and-return contract). No path (including FAILED/SKIPPED) writes to the input frame or to any file.

8. **Coordinator + orchestrator wiring, engine autonomy untouched.** A coordinator runs Tier-1 then Tier-2 on one working copy and returns `(cleaned_df, CleaningResult)` whose `actions` list carries **both** tiers, each distinguishable by its `remediation_class`. `run_full_pipeline` calls the coordinator **only** when `enable_cleaning` is true and DQA did not halt, and attaches the result to `PipelineResult.cleaning_result` (new optional field, additive). `CleaningEngine` is imported and used **unchanged** — no Tier-2 code added to it. Structlog events (`cleaning_stage_started`, `cleaning_stage_skipped`, `cleaning_stage_completed`) carry `pipeline_run_id` and log counts/column names only — never raw row data, cell values, or PII.

9. **Deterministic & idempotent.** Same frame + report + policy → identical cleaned frame and identical action list across two runs (no randomness, no iteration-order or dict-order dependence in method resolution). Re-cleaning already-cleaned output against a re-assessed report yields zero further imputation actions for columns already filled.

10. **Tests.** New `backend/tests/test_cleaning_policy.py` (policy resolution + Tier-2 execution), plus additions to `test_config.py` (config parse/validate/backward-compat) and an orchestrator gate test (`test_orchestrator*` or a new `test_cleaning_gate.py`). Cover: default-off no-op + regression (AC1); config validation, allowlist, backward-compat with a `cleaning:`-less YAML (AC2); default-by-type resolution + full precedence chain (AC3); each imputation method correct + `source` recorded (AC4); `leave_as_is` skip (AC4); `non_unique_id`/other Tier-2 skipped (AC5); Tier-3-on-shared-column untouched (AC6); combined working-copy invariant (AC7); coordinator merges both tiers + engine used unchanged (AC8); determinism double-run (AC9). Full suite green via `uv run pytest`; **record the new pass count** (baseline before this story: 279 passed / 1 skipped; frontend unaffected: vitest 18/18, `npm run build` OK).

11. **DoD security gate.** Run `/security-review`; resolve any Critical/High before marking done. This is a security-sensitive story (the enablement boundary + first Tier-2 execution path). Reviewer should specifically probe: can cleaning be enabled by anything other than explicit config/param/flag? can the policy layer ever reach a `human_only` or non-`null_values` finding? are method values validated before use (config injection)? is any raw cell value or PII reachable in logs or in a `CleaningAction`'s `detail`/`error`/`parameters`?

## Tasks / Subtasks

- [x] **Task 0 — Confirm prerequisites (AC: 4, 8)**
  - [x] Verify PR #39 and PR #42 are on `main`; `CleaningEngine`, `cleaning_primitives.impute_nulls`, `IMPUTATION_METHODS`, `CleaningAction`/`CleaningResult`, `RemediationClass.HUMAN_POLICY_AGENT_EXECUTION`, and the classifier's `null_values → HUMAN_POLICY_AGENT_EXECUTION` mapping are all importable. HALT if not.
  - [x] Re-confirm the three reality corrections still hold (no `backend/rules/`, no `project` entity, `leave_as_is` not in `IMPUTATION_METHODS`).
- [x] **Task 1 — Config model (AC: 1, 2)**
  - [x] Add `CleaningConfig` (and nested `ImputationPolicyConfig`) to `backend/models/pipeline_config.py`, following the existing sub-model style (`ThresholdConfig`/`AlertConfig`). Fields: `enabled: bool = False`; `imputation` with `defaults: dict[type→method]` (keys `numeric|categorical|datetime`) and `columns: dict[str, method]`. Validate methods against `{mean, median, mode, forward_fill, leave_as_is}`; raise `ValueError` (surfaced as `ConfigurationError` by `load`) on unknown method.
  - [x] Add `cleaning: CleaningConfig = Field(default_factory=CleaningConfig)` to `PipelineConfig`. Confirm existing `config.yaml` (no `cleaning:` key) still validates → `enabled=False`. Add a commented `cleaning:` example block to the committed `config.yaml`.
  - [x] Docstring seam note: policy lives here interim; migrates to `project.cleaning_policy` in Epic 4 Story 4.1a.
- [x] **Task 2 — Policy layer `backend/rules/` (AC: 3, 4, 5)**
  - [x] Create `backend/rules/__init__.py` and `backend/rules/cleaning_policy.py`.
  - [x] `resolve_method(column, series, policy) -> tuple[str, str]`: precedence per-column → per-type default override → built-in default (numeric→median, categorical→mode, datetime→forward_fill). Column kind from pandas dtype checks (`is_datetime64_any_dtype` first, then `is_numeric_dtype`, else categorical). Returns `(method, source)` where source is `override`/`default`.
  - [x] `apply_imputation_policy(df, quality_report, policy, pipeline_run_id) -> tuple[df, list[CleaningAction]]`: filter to `HUMAN_POLICY_AGENT_EXECUTION` **and** `null_values`; per finding resolve method, call `impute_nulls` (or skip for `leave_as_is`), compute `values_changed` (null count before − after), build the `CleaningAction`. Non-`null_values` Tier-2 → SKIPPED. Never mutate input `df` (always returns a fresh frame).
- [x] **Task 3 — Coordinator (AC: 6, 7, 8, 9)**
  - [x] `backend/rules/cleaning_coordinator.py::clean_dataset` runs `CleaningEngine().clean()` (Tier-1) then `apply_imputation_policy()` (Tier-2) on the same working copy, merging actions into one `CleaningResult` (Tier-1 output frame is the Tier-2 input; shape counters span both passes). `CleaningEngine` imported and used unchanged.
- [x] **Task 4 — Orchestrator + CLI wiring (AC: 1, 8)**
  - [x] `run_full_pipeline`: added `enable_cleaning: bool = False` + `cleaning_config: CleaningConfig | None = None`; when true and not halted, resolves the policy (built-in defaults if `None`), calls the coordinator after Stage 1, attaches `PipelineResult.cleaning_result`. Report continues on the original frame (Q1). Halt path logs `cleaning_stage_skipped`.
  - [x] Added `cleaning_result: "CleaningResult | None" = None` to `PipelineResult` (TYPE_CHECKING import).
  - [x] CLI `cli(...)`: added `--clean/--no-clean` (default off) wired to `enable_cleaning`; policy sourced from `PipelineConfig.load().cleaning` when `--clean` is set. Structlog stage events (`cleaning_stage_started`/`skipped`/`completed`) carry `pipeline_run_id`, counts/columns only.
- [x] **Task 5 — Tests (AC: 10)**
  - [x] `backend/tests/test_cleaning_policy.py` (20 tests), `backend/tests/test_config.py` additions (6 tests), `backend/tests/e2e/test_cleaning_gate.py` orchestrator+CLI gate test (7 tests). Reuse `cleaning_dirty_df` for the Tier-2/Tier-3-shared-column and working-copy assertions.
- [x] **Task 6 — Verify + security (AC: 10, 11)**
  - [x] `uv run pytest` green: **312 passed / 1 skipped** (baseline 279/1 → +33, regressions=0). Frontend unaffected: vitest **36/36**, `npm run build` OK. `/security-review` run — **no HIGH/MEDIUM findings** (enablement boundary, Tier-2 filter, method validation, and log/provenance exposure all cleared).

### Review Findings

- [x] [Review][Decision] `CleaningConfig.enabled` is dead configuration — RESOLVED (Marvin, 2026-07-23): made `enable_cleaning` tri-state (`bool | None = None`). Explicit `True`/`False` (param or CLI `--clean/--no-clean`) always wins; `None` (the default, both at the param and the CLI) defers to `cleaning_config.enabled`; with nothing set anywhere, resolves to `False` (AC1 preserved). CLI loads `config.yaml`'s cleaning section whenever `clean is not False` (i.e. when the default could matter, or to source the imputation policy for an explicit `--clean`) so an explicit `--no-clean` never grows a hard dependency on a valid config file. Both contradictory docstrings (`CleaningConfig`, `run_full_pipeline`) rewritten to describe the real precedence. Added `TestCleaningEnablementPrecedence` (6 tests) covering the full resolution matrix + a CLI test confirming `--no-clean` skips the config load. Full suite: 319 passed / 1 skipped (+7, 0 regressions). [`backend/pipeline/orchestrator.py`, `backend/models/pipeline_config.py`, `config.yaml`, `backend/tests/e2e/test_cleaning_gate.py`]
- [x] [Review][Patch] CLI's `PipelineConfig.load()` call for `--clean` runs outside the `try/except SavvyCleanseError` block — RESOLVED as a side effect of the tri-state rewrite above: the config load now sits inside the `try:` block (verified by re-reading the code post-fix). [`backend/pipeline/orchestrator.py`]
- [x] [Review][Patch] Coordinator passes the pre-Tier-1 `quality_report` (original column names) into `apply_imputation_policy`, causing a false FAILED action for a column with both a `column_naming` and a `null_values` defect — RESOLVED: `clean_dataset` now extracts the Tier-1 `HEADER_NORMALIZATION` action's `value_mapping` and translates the report's `affected_columns` through it (`_header_rename_mapping` / `_remap_report_columns`) before calling Tier-2. New regression test `test_column_with_both_naming_and_null_defects_is_imputed_after_rename`. [`backend/rules/cleaning_coordinator.py`, `backend/tests/test_cleaning_policy.py`]
- [x] [Review][Patch] `apply_imputation_policy` recorded `CleaningStatus.APPLIED` even when `values_changed == 0` — RESOLVED: when the primitive runs without error but `filled == 0` (all-null column; leading nulls before forward_fill's first anchor), the action is now recorded `SKIPPED` via a new `_no_effect_action` builder, never `APPLIED`. 4 new tests in `TestNoEffectImputation` (all-null numeric/categorical, leading-null forward_fill, and a partial-fill case confirming a column that DOES change still records `APPLIED`). [`backend/rules/cleaning_policy.py`, `backend/tests/test_cleaning_policy.py`]
- [x] [Review][Patch] Dev Agent Record's Debug Log References stated the new-test breakdown as 21+6+6 — RESOLVED: corrected to the actual 20+6+7 breakdown, with the review-round test counts appended. [`_bmad-output/implementation-artifacts/3-4-opt-in-gate-config.md`]
- [x] [Review][Patch] `test_cli_clean_flag_enables_gate` only asserted `cleaning_config is not None` — RESOLVED: now asserts `captured["cleaning_config"] == PipelineConfig.load().cleaning`, so a wiring bug substituting a wrong/default config would fail the test. [`backend/tests/e2e/test_cleaning_gate.py`]
- [x] [Review][Defer] No exception handling wraps the `clean_dataset()` call itself in the orchestrator — deferred, pre-existing: matches the existing Tier-1 `CleaningEngineError`-must-surface design precedent (contract violations are meant to propagate, not be swallowed); not a new gap uniquely introduced by this diff. [`backend/pipeline/orchestrator.py`]
- [x] [Review][Defer] The 200-char error-message truncation in FAILED actions doesn't guarantee no raw cell value can appear — deferred, pre-existing: exactly mirrors the Tier-1 `CleaningEngine._failed_action` pattern the spec explicitly instructs this layer to replicate. [`backend/rules/cleaning_policy.py`]
- [x] [Review][Defer] Nullable pandas "boolean" dtype columns classify as numeric via `is_numeric_dtype` and default to `median` (verified: `median()` of such a column returns `0.5`, a nonsensical fill) — deferred, pre-existing/unreachable: the pipeline's actual CSV-read path never produces this dtype for a column with nulls (verified: `pd.read_csv` upcasts bool+null to `object`, which classifies as categorical); only reachable via a caller bypassing the CLI/CSV entry point. [`backend/rules/cleaning_policy.py`]

## Dev Notes

### Config schema (interim home: `config.yaml`)

```yaml
cleaning:
  enabled: false                # THE opt-in gate — default OFF, load-bearing (AC1)
  imputation:
    defaults:                   # optional: override the built-in per-type defaults
      numeric: median           # built-in: median
      categorical: mode         # built-in: mode
      datetime: forward_fill    # built-in: forward_fill
    columns:                    # optional: per-column overrides (highest precedence)
      revenue: median
      signup_date: forward_fill
      region: leave_as_is       # policy-layer skip; primitive never called
```

All of `imputation`, `defaults`, `columns` are optional; absent → built-in defaults. `enabled` absent → `false`. Method allowlist: `{mean, median, mode, forward_fill, leave_as_is}` (`leave_as_is` is policy-only; not a primitive method).

### Imputation default resolution (AC3)

| Column kind | Detection | Built-in default | Rationale |
|---|---|---|---|
| numeric | `pd.api.types.is_numeric_dtype` | `median` | Robust to outliers common in SMB revenue/quantity; won't get skewed by a single huge order. |
| categorical | object / string dtype | `mode` | Most-frequent category is the only defensible non-parametric fill for labels. |
| datetime / time-indexed | datetime dtype or `DatetimeIndex` | `forward_fill` | Carrying the last known value forward is the standard time-series gap fill. |

Precedence: per-column override → per-type default override → built-in. Record the chosen method AND its `source` (`default`/`override`) in `CleaningAction.parameters` so 3.3's manifest can show *why* a fill happened.

Note: the assessor does not compute skewness, and `ColumnProfile` carries no skew field — do **not** try to branch mean-vs-median on skew. `median` is the universal numeric default (the epic's "median for skewed numerics" is satisfied by defaulting numerics to the outlier-robust choice); a client wanting `mean` sets an override.

### Component boundaries (do not cross)

- **`CleaningEngine` is frozen** for Tier-1 only (3.2 AC2). Tier-2 imputation lives in `backend/rules/`, calls `impute_nulls` directly. The coordinator composes the two; the engine never learns about policy.
- **`backend/rules/`** is Business-Logic layer: may import `models/`, `errors/`, `pipeline/` primitives; never `api/`, `agents/`, legacy modules, or a database.
- **Provenance is one model.** Tier-2 actions are `CleaningAction`s in the same `CleaningResult.actions` list as Tier-1, separated by `remediation_class`. Do NOT invent a parallel imputation record — 3.3 renders one manifest from one list.
- **Original data untouched.** Tier-1 deep-copies at entry; `impute_nulls` copies-and-returns; the coordinator must thread frames so the *caller's* frame is never the one written to (AC7).

### Fail-closed discipline (mirror the engine)

The policy executor is the Tier-2 analogue of the engine's Tier-1 registry: an explicit `null_values`-only allowlist, an independent re-check of `remediation_class == HUMAN_POLICY_AGENT_EXECUTION`, and SKIPPED (not silent drop) for anything else. A `human_only` finding must be impossible to reach — the filter is `class == HUMAN_POLICY_AGENT_EXECUTION AND defect_type == "null_values"`, nothing looser.

### `PipelineResult` note

`PipelineResult` is the sanctioned stdlib `@dataclass` envelope (architecture.md §486-494); adding `cleaning_result: "CleaningResult | None" = None` is additive and consistent with how `insight_report`/`drift_report` were added. (Aside, do not fix here: its TYPE_CHECKING block imports `data_quality_report`, but the live DQA model is `quality_report.py`; harmless, out of scope.)

### Previous-story intelligence (3.1 / 3.2)

- 3.1/3.2 key everything on `defect_type`, never `category`, so Tier-3 variants can't inherit a Tier-1/Tier-2 path. Mirror this: the policy allowlist keys on `defect_type == "null_values"` exactly.
- 3.2 added `NO_OP`/`SKIPPED`/`FAILED` to give the manifest honest records for the non-applied paths — reuse them for Tier-2 skips/failures; do not add new statuses.
- 3.2's `cleaning_dirty_df` was built specifically so Tier-2 (`null_values` in `quantity`, rows 0-1) and Tier-3 (`negative_values` in `quantity`, row 2) overlap in one column — it is the exact fixture for AC6.
- The `impute_nulls` guard already raises `ValueError` for `mean`/`median` on non-numeric columns (fixed in 3.2 review) — a mis-configured override surfaces as a FAILED action, not a crash. Test that path.
- 3.2 review's highest-severity bug was an operation touching columns it wasn't scoped to (header normalization over-reaching). The analogous risk here: the policy imputing a column it wasn't asked to, or reaching a non-Tier-2 finding. Pin those as their own tests.

### Invariants (Epic 3 — must not drift)

- Working-copy only; original data NEVER modified (now across Tier-1 **and** Tier-2).
- Cleaning opt-in, default OFF — enforced at config, orchestrator, and CLI; nothing else flips it.
- Every remediation logged as a `CleaningAction`; 3.3 renders the manifest from `CleaningResult`.
- Tier-3 `human_only` NEVER auto-touched, even on a column that also has a Tier-2 finding. LOAD-BEARING.
- Deterministic set only — Tier-1's four ops + Tier-2 null imputation via the four primitive methods (+ policy-layer `leave_as_is` skip). No fuzzy matching, no ML, no LLM.

### References

- [Source: _bmad-output/implementation-artifacts/epic-3-cleaning-engine.md#Story-notes-3.4] — median/mode/forward-fill defaults; policy ownership Tier 2; "must not block a non-expert at step one."
- [Source: _bmad-output/implementation-artifacts/epic-3-cleaning-engine.md#INVARIANTS] — opt-in default-off; Tier-3 never touched; working-copy only.
- [Source: _bmad-output/implementation-artifacts/schema-extensions-spec.md#1-four-tier-ownership-model] — Tier 2 = "human sets policy once, agent executes"; imputation method per column type; the (aspirational) `rules/rule_engine.py` note.
- [Source: _bmad-output/implementation-artifacts/schema-extensions-spec.md#3-project-entity] — `project.cleaning_policy` lands in Epic 4 Story 4.1; 3.4 has "nowhere to write" → interim config home.
- [Source: _bmad-output/implementation-artifacts/3-2-cleaning-engine-core.md] — engine API, `impute_nulls` boundary (method required, no default, not autonomously reachable), AC2 "no flag widens Tier-1-only."
- [Source: backend/pipeline/cleaning_engine.py] — `CleaningEngine.clean(df, quality_report, pipeline_run_id) -> (df, CleaningResult)`; do not modify.
- [Source: backend/pipeline/cleaning_primitives.py:30,282] — `IMPUTATION_METHODS`; `impute_nulls(df, column, method)` signature + guards.
- [Source: backend/models/cleaning_result.py] — `CleaningAction`/`CleaningResult`/`CleaningOperation.NULL_IMPUTATION`/`CleaningStatus`; the one provenance model.
- [Source: backend/pipeline/remediation_classifier.py:53-54] — `null_values`/`non_unique_id → HUMAN_POLICY_AGENT_EXECUTION`.
- [Source: backend/models/pipeline_config.py] — the real YAML→Pydantic pattern to model `CleaningConfig` on; `PipelineConfig.load()`.
- [Source: backend/pipeline/orchestrator.py:47-160] — `run_full_pipeline` stage sequence + halt short-circuit; the `enable_drift`/`dataset_key` gating pattern to mirror for `enable_cleaning`.
- [Source: backend/tests/conftest.py:157-202] — `cleaning_dirty_df` (Tier-2 nulls + Tier-3 negative in `quantity`).

## Open questions (for Marvin — do not block dev; documented decisions taken)

1. **Does the report describe cleaned or original data when cleaning is on?** This story scopes it as **original** — Insight/Narrative/Renderer keep running on the input frame; the cleaned frame + `CleaningResult` are produced and carried for 3.3/3.6/3.7. Re-pointing the report at cleaned data is a semantics change tied to 3.7's before/after view. Confirm this is the intended split, or pull the "report-on-cleaned" decision forward into 3.4.
2. **Interim policy home = `config.yaml`.** Confirmed as the only durable config on the CSV/CLI path pre-Epic-4. The Epic-4 `project.cleaning_policy` migration (Story 4.1a) will move it. Flag if you'd rather a dedicated `cleaning_policy.yaml` under `backend/rules/` instead of a `config.yaml` section.
3. **`non_unique_id` (Tier-2, non-imputation) is out of scope** — recorded SKIPPED. Orphaned-FK / ID-resolution rules are a separate Tier-2 mechanism; confirm they stay out of 3.4.

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (dev-story, high effort)

### Debug Log References

- Baseline before story: `uv run pytest` → 279 passed / 1 skipped.
- After initial implementation: `uv run pytest` → 312 passed / 1 skipped (rc=0); new Story-3.4 tests: 33 (20 `test_cleaning_policy.py` + 6 `test_config.py` + 7 `test_cleaning_gate.py`) — corrected from an earlier inaccurate 21+6+6 breakdown flagged in code review.
- After code review fixes (tri-state enablement, coordinator column-remap, no-effect-imputation SKIPPED status): `uv run pytest` → **324 passed / 1 skipped** (rc=0); +12 more tests over the initial 312 (7 precedence/CLI-load tests + 5 no-effect/column-remap regression tests), 0 regressions.
- Frontend (unaffected by review fixes — no frontend files touched): `npx vitest run` → 36/36; `npm run build` → OK.
- `/security-review` → no HIGH/MEDIUM findings.
- Code review (Sonnet, three-layer adversarial + edge-case + acceptance-audit): 1 decision-needed + 5 patch findings, all resolved; 3 deferred (pre-existing precedent, tracked in `deferred-work.md`); 5 dismissed as noise/refuted/unreachable.

### Completion Notes List

- **Opt-in gate (AC1)** implemented at all three surfaces, default OFF: `CleaningConfig.enabled=False`, `run_full_pipeline(enable_cleaning=False)`, CLI `--clean/--no-clean` default no-clean. Disabled → no cleaning component constructed, `cleaning_result is None`, downstream byte-identical (full pre-existing suite passes unchanged + explicit gate test).
- **Config (AC2)** — `CleaningConfig`/`ImputationPolicyConfig` added to `pipeline_config.py`; the whole `cleaning:` section is optional (backward-compat verified). Method allowlist `{mean,median,mode,forward_fill,leave_as_is}` validated at load (unknown → `ConfigurationError`); the allowlist is derived from `IMPUTATION_METHODS` via a lazy import so the models layer never imports the pipeline layer at module-load time. `mean`/`median` on non-numeric surfaces as a FAILED action (primitive guard), never a crash.
- **Policy layer (AC3-5)** — `backend/rules/cleaning_policy.py`: `resolve_method` (per-column → per-type → built-in, records `source`), `apply_imputation_policy` filters fail-closed to `HUMAN_POLICY_AGENT_EXECUTION` **and** `null_values`; `leave_as_is` is a policy-layer skip (SKIPPED action, primitive never called); non-`null_values` Tier-2 (e.g. `non_unique_id`) → SKIPPED zero-change.
- **Coordinator (AC6-9)** — `backend/rules/cleaning_coordinator.py::clean_dataset` composes Tier-1 engine + Tier-2 policy on one working copy, merges both tiers into one `CleaningResult` (distinguishable by `remediation_class`). `CleaningEngine` used unchanged (no Tier-2 code added to it). Tier-3 `human_only` on a shared column is provably untouched (the `-5` in `quantity` survives while its nulls are imputed). Working-copy invariant holds across the combined pass. Deterministic double-run + idempotent-after-reassess verified.
- **Q1 (report on original data)** left as scoped: report stages run on the original frame; the cleaned frame + `CleaningResult` are produced and carried for 3.3/3.6/3.7. **Confirm with Marvin** whether to keep this split or pull "report-on-cleaned" forward.
- `PipelineResult.cleaning_result` added additively (TYPE_CHECKING import); the pre-existing harmless `data_quality_report` TYPE_CHECKING import was deliberately left as-is (out of scope per Dev Notes).

### File List

- `backend/models/pipeline_config.py` (M) — `ImputationPolicyConfig`, `CleaningConfig`, `cleaning` field, method-allowlist validators; docstring corrected (review) to describe the real tri-state precedence.
- `backend/models/pipeline_result.py` (M) — additive `cleaning_result` field + TYPE_CHECKING import.
- `backend/rules/__init__.py` (A) — new business-logic rules package.
- `backend/rules/cleaning_policy.py` (A/M) — Tier-2 imputation policy layer; review fix added `_no_effect_action` (SKIPPED when `filled == 0`, never a false `APPLIED`).
- `backend/rules/cleaning_coordinator.py` (A/M) — Tier-1 + Tier-2 coordinator; review fix added `_header_rename_mapping`/`_remap_report_columns` to translate stale pre-rename column references before Tier-2 runs.
- `backend/pipeline/orchestrator.py` (M) — `enable_cleaning`/`cleaning_config` params, gated cleaning stage, `--clean/--no-clean` CLI flag, stage events; review fix made `enable_cleaning`/`clean` tri-state (`bool | None`) with config-default precedence, moved the CLI's config load inside the `try:` block.
- `config.yaml` (M) — commented `cleaning:` example block; comment corrected (review) to describe the real precedence.
- `backend/tests/test_cleaning_policy.py` (A/M) — policy + coordinator tests; review fixes added `TestNoEffectImputation` (4 tests) and a coordinator column-remap regression test.
- `backend/tests/test_config.py` (M) — `TestCleaningConfig` additions.
- `backend/tests/e2e/test_cleaning_gate.py` (A/M) — orchestrator + CLI gate tests; review fixes added `TestCleaningEnablementPrecedence` (6 tests), a `--no-clean`-skips-config-load test, and strengthened the `--clean` CLI test's config assertion.

## Change Log

- 2026-07-22: Story drafted (create-story, Opus high effort). Opt-in gate (config/orchestrator/CLI, default OFF) + Tier-2 imputation policy layer (`backend/rules/`) driving the policy-less `impute_nulls` primitive with per-column-type defaults. Flagged three reality corrections (no `rules/rule_engine.py`, no `project` entity yet, `leave_as_is` not in the primitive). Status → ready-for-dev.
- 2026-07-23: Implemented (dev-story, Opus/high). Opt-in gate + Tier-2 policy layer + coordinator + orchestrator/CLI wiring, engine autonomy untouched. 312 passed / 1 skipped (0 regressions), frontend 36/36 + build OK, `/security-review` clean. Status → review.
- 2026-07-23: Code review (Sonnet, three-layer: Blind Hunter + Edge Case Hunter + Acceptance Auditor). 1 decision-needed (config `enabled` field was dead — resolved with Marvin as a tri-state precedence: explicit param/CLI always wins, `None` defers to `cleaning_config.enabled`, nothing set anywhere → OFF) + 5 patch findings, all resolved: CLI config-load moved inside error handling, coordinator now translates stale pre-rename column references between Tier-1 and Tier-2, no-effect imputations now record SKIPPED instead of a false APPLIED, story doc test-count typo fixed, CLI test assertion strengthened. 3 findings deferred to `deferred-work.md` (pre-existing precedent, not introduced by this diff); 5 dismissed as noise/refuted/unreachable. 324 passed / 1 skipped (+12 over initial, 0 regressions). Status → done.
