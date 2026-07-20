# Story 3.1: Classification Layer (`remediation_class` taxonomy)

Status: ready-for-dev

Sizing: M · Model: Opus · loop_eligible: false
<!-- Opus + loop_eligible:false because the MAPPING is architecture-defining and
     LOAD-BEARING: a mis-tiered finding is the vector by which Story 3.2/3.4 could auto-touch
     data that must stay human-only. The implementation is a deterministic mapping (easy to
     unit-test); the RISK is choosing the wrong tier, which a passing test cannot catch.
     Prerequisite: Story R.1 (rename) merges first (PR #36). No code path here depends on the
     rename, but it is the documented seam. -->

## Story

As the **SAINT cleaning pipeline**,
I want **every data-quality finding stamped with a `remediation_class` that declares who owns its fix** (agent-autonomous / human-sets-policy / human-only),
so that **the downstream Cleaning Engine (3.2) and Opt-in Gate (3.4) can act ONLY on findings they are permitted to touch, and Tier-3 findings are never auto-modified** — the load-bearing invariant of the entire cleaning epic.

## Context & scope boundary

This story adds the **classification** only. It does **not** clean, impute, dedupe, or modify any data — that is Story 3.2. It introduces the taxonomy that 3.2/3.4/3.5 consume. Concretely:

1. Add an additive, defaulted `remediation_class` field to `DataQualityDefect`.
2. Add a deterministic classifier that stamps each finding based on its `defect_type` (+ `category`).
3. Wire the classifier into the assessment output so every emitted defect carries a class.

Original data is never touched (detect-don't-fix, §2.1). No client-facing surface is produced here (that is 3.9).

## Acceptance Criteria

1. **Field added (additive, backward-compatible).** `DataQualityDefect` (`backend/models/quality_report.py`) gains a `remediation_class` field with values `agent_autonomous | human_policy_agent_execution | human_only`, modeled as a `str, Enum` (mirroring `DefectCategory`/`Severity`). It is **optional with a default**, so every existing Epic 1/2 finding, fixture, and serialized report validates unchanged.

2. **Fail-safe default = `human_only`.** Any finding whose `defect_type` is not explicitly mapped — including future/unknown defect types — classifies as `human_only`. The default must be the most conservative class so an unmapped finding is **never** eligible for autonomous cleaning. This is an explicit, tested property, not an incidental one.

3. **Four-tier ownership model encoded** exactly as specified in `schema-extensions-spec.md §1`:
   - **Tier 1 → `agent_autonomous`** (unconditional): consistency (mixed types, date-format variance, encoding, whitespace, case), uniqueness (exact duplicate rows), structural integrity (column-count / header misalignment, rule-based).
   - **Tier 2 → `human_policy_agent_execution`** (human sets policy once, agent executes): completeness (null imputation per column type), referential integrity (orphaned-FK / ID resolution rule).
   - **Tier 3 → `human_only`** (agent detects & scores, never acts): near-duplicates, statistical red flags (outliers, suspicious distributions), unreadable/ambiguous structure (pipeline halts).
   - **Tier 4** is **out of scope** (Epic 11): it is an opt-in overlay on `human_only` findings, not a fourth `remediation_class` value. Do NOT add a fourth enum value.

4. **Every current `defect_type` classified** per the authoritative mapping in Dev Notes. All 12 emitted defect types are covered (verified against `data_quality.py`), each mapped exactly once. The three formerly-ambiguous types (`negative_values`, `infinite_values`, `duplicate_measurement`) are locked to `human_only` per the Resolved Classification Decisions section.

5. **Classification is centralized and pure.** The `defect_type → remediation_class` mapping lives in exactly one place (a pure, side-effect-free classifier), not scattered across the assessor's detection branches. Re-classifying the same finding is idempotent.

6. **Wired into output.** `DataQualityAssessor.assess_quality` (or the orchestrator immediately after it) stamps `remediation_class` on every `DataQualityDefect` in the returned `DataQualityReport`. No detection logic, severity, or scoring changes.

7. **No client-facing tier exposure.** No "Tier 3" (or any tier number) label is emitted anywhere client-facing. Internal `remediation_class` values are the only artifact. (Descriptive client copy is Story 3.9's job — do not pre-empt it.)

8. **Tests.** Unit tests assert the class for every current `defect_type`, the `human_only` default for an unmapped type, backward-compatible validation of a pre-existing (unclassified) finding, and idempotency. Full suite stays green: `uv run pytest backend/tests/ --ignore=backend/tests/test_parse_file.py` (baseline 181 passed / 1 skipped / 0 regressions).

9. **DoD security gate.** Run `/security-review`; resolve any Critical/High before marking done.

## Tasks / Subtasks

- [ ] **Task 1 — Add `RemediationClass` enum + field (AC: 1, 2, 3)**
  - [ ] Add `class RemediationClass(str, Enum)` to `backend/models/quality_report.py` with the three values (do NOT add a Tier-4 value).
  - [ ] Add `remediation_class: RemediationClass = RemediationClass.HUMAN_ONLY` to `DataQualityDefect` (defaulted → backward compatible + fail-safe).
- [ ] **Task 2 — Build the pure classifier (AC: 4, 5)**
  - [ ] New module `backend/pipeline/remediation_classifier.py` holding the single authoritative `_DEFECT_TYPE_TO_CLASS` mapping (see Dev Notes table) and a pure `classify(defect_type: str) -> RemediationClass` (unmapped → `HUMAN_ONLY`).
  - [ ] Add a helper to stamp a whole report/defect list idempotently.
- [ ] **Task 3 — Wire into assessment (AC: 6)**
  - [ ] Call the classifier at the end of `DataQualityAssessor.assess_quality`, before the `DataQualityReport` is returned, so every defect is stamped. Change nothing else in detection/severity/scoring.
- [ ] **Task 4 — Tests (AC: 8)**
  - [ ] Extend `backend/tests/test_models.py`: a legacy `DataQualityDefect` constructed without `remediation_class` validates and defaults to `human_only`.
  - [ ] New `backend/tests/test_remediation_classifier.py`: parametrized assertion of the expected class for every current `defect_type`; unmapped/unknown → `human_only`; idempotency.
  - [ ] A `data_quality` integration test asserting a produced report has every defect stamped.
- [ ] **Task 5 — Verify + security (AC: 8, 9)**
  - [ ] Run the full backend suite; confirm 0 regressions.
  - [ ] Run `/security-review`; resolve Critical/High.

## Dev Notes

### Authoritative `defect_type → remediation_class` mapping

Derived from the assessor's actual emitted `defect_type` strings (`backend/pipeline/data_quality.py`) cross-referenced with `schema-extensions-spec.md §1`. **This table is the load-bearing artifact of the story.**

| `defect_type` | emitted `category` | `remediation_class` | Tier | Basis |
|---|---|---|---|---|
| `mixed_types` | structural_integrity | `agent_autonomous` | 1 | consistency: mixed types |
| `column_naming` | structural_integrity | `agent_autonomous` | 1 | structural: header/column misalignment (rule-based) |
| `case_inconsistency` | consistency | `agent_autonomous` | 1 | consistency: case |
| `duplicate_rows` | uniqueness | `agent_autonomous` | 1 | uniqueness: exact duplicate rows |
| `null_values` | completeness | `human_policy_agent_execution` | 2 | completeness: null imputation per column type |
| `non_unique_id` | referential_integrity | `human_policy_agent_execution` | 2 | referential: ID/FK resolution rule |
| `zero_variance` | statistical_red_flag | `human_only` | 3 | suspicious distribution |
| `extreme_outliers` | statistical_red_flag | `human_only` | 3 | outliers |
| `extreme_cardinality` | statistical_red_flag | `human_only` | 3 | suspicious distribution |
| `negative_values` | consistency | `human_only` | 3 | domain plausibility red flag (locked — see notes) |
| `infinite_values` | statistical_red_flag | `human_only` | 3 | statistical red flag, fail-safe (locked — see notes) |
| `duplicate_measurement` | referential_integrity | `human_only` | 3 | redundant-column correlation signal, irreversible schema call (locked — see notes) |

> **Do not key classification on `category` alone.** `uniqueness` and `structural_integrity` each split across tiers in the spec (exact duplicates = Tier 1 vs near-duplicates = Tier 3; header misalignment = Tier 1 vs unreadable/ambiguous = Tier 3). The current assessor happens not to emit the Tier-3 variants of those categories yet, so the mapping is keyed on `defect_type`. Keep it keyed on `defect_type` so adding a future `near_duplicate` type cannot silently inherit `duplicate_rows`'s autonomous class.
>
> **`duplicate_rows` ≠ `duplicate_measurement` — they are unrelated findings.** `duplicate_rows` (`data_quality.py:252`, category `uniqueness`) is exact duplicate *records* — the genuine Tier-1 dedup candidate → `agent_autonomous`. `duplicate_measurement` (`data_quality.py:400`, category `referential_integrity`, severity LOW) is a *column-pair* signal: two numeric columns with Pearson |corr| > 0.99, i.e. a redundant-column hint, with action "verify if one is derived from the other." It has nothing to do with duplicate records and is **not** a dedup candidate. Classify each on its own `defect_type`; never let the name similarity conflate them.

### ✅ Resolved Classification Decisions (locked 2026-07-12)

All three resolve to **`human_only`**. Mis-tiering toward autonomy is a data-integrity hazard, so each lands on the conservative class:

1. **`negative_values` → `human_only`.** Emitted as `consistency`, but only for columns whose name implies non-negativity (`_NON_NEGATIVE_KEYWORDS`: revenue, quantity, count, price, amount, volume). This is a *domain/plausibility* red flag ("revenue is negative"), not a mechanical whitespace/case normalization. A human must decide whether a negative value is an error, a refund, or valid. Do NOT auto-fix.
2. **`infinite_values` → `human_only`.** `inf`/`-inf` in numerics. Mechanically coercible (→ null/remove) but usually signals an upstream computation error a human should see. Fail-safe to human review.
3. **`duplicate_measurement` → `human_only`.** Correlation-based redundant-column signal (`data_quality.py:400`, Pearson |corr| > 0.99), **not** a duplicate-record finding. Remediation = dropping/merging one of two correlated columns, which is an irreversible, domain-specific schema decision (which column is canonical cannot be determined mechanically). Tier 3. *The earlier Tier-2 "resolution-rule" framing was based on a misread of the defect semantics (confusing it with row dedup / `duplicate_rows`) and is withdrawn.*

### Where things live / conventions to follow (from Epic 1/2, all `done`)

- **Models:** `backend/models/quality_report.py`. Enums are `class X(str, Enum)` (see `Severity`, `DefectCategory`). Follow that exact pattern for `RemediationClass`.
- **Pipeline stages:** `backend/pipeline/` (e.g., `data_quality.py`, `drift_engine.py`, `insight_engine.py`). Pure, deterministic, no import-time side effects, no logging self-config. The classifier belongs here as a pure module.
- **Tests:** `backend/tests/test_<module>.py`, pytest, parametrized where natural (see `test_data_quality.py`, `test_models.py`). Baseline to preserve: **181 passed, 1 skipped**.
- **Architecture compliance (`architecture.md` §482–506, §745):** pipeline modules may import from `models/` and siblings; must NOT import from `api/` or legacy modules; never self-configure logging at import.
- **`backend/rules/` does not exist yet** — it is introduced in Story 3.4 (Tier-2 policy via the `rules/rule_engine.py` YAML pattern). **Do not build it here.** 3.1 is a static mapping only.

### Invariants (must not drift — from `epic-3-cleaning-engine.md`)

- Working-copy only; original data NEVER modified. 3.1 classifies, does not clean.
- **Tier 3 (`human_only`) findings are NEVER auto-touched, even accidentally. LOAD-BEARING.** The fail-safe default (AC 2) is the primary guard: any finding the classifier doesn't recognize is `human_only`.
- Cleaning is opt-in / default-off (enforced later in 3.4; 3.1 must not enable anything).
- `remediation_class` is internal; client-facing descriptive names are Story 3.9 (do not duplicate/pre-empt).

### Previous-story intelligence

- Epic 1 (DQA/insights/render) and Epic 2 (config/LLM-client/drift/reporting/monitoring) are `done`. This is the **first** story of Epic 3 → mark `epic-3` `in-progress` on pickup.
- The DQA model and six `DefectCategory` values were frozen in Epic 1; 3.1 extends the *finding* model additively without reopening Epic 1's detection logic.
- Recent commits are R.1 rename + roadmap docs (no analytic code precedent for 3.1); the relevant precedent is the enum+model+pure-stage+pytest pattern above.

### References

- [Source: _bmad-output/implementation-artifacts/schema-extensions-spec.md#1-dqa-finding-remediation_class] — authoritative taxonomy, target model, additive/defaulted requirement, Tier-4 is an overlay not a value.
- [Source: _bmad-output/implementation-artifacts/epic-3-cleaning-engine.md#story-notes] — Story 3.1 scope + INVARIANTS (Tier-3 never auto-touched; load-bearing).
- [Source: backend/models/quality_report.py] — `DataQualityDefect`, `DefectCategory`, `Severity` (enum pattern to mirror).
- [Source: backend/pipeline/data_quality.py] — emitted `defect_type` strings + `assess_quality` integration point; `_NON_NEGATIVE_KEYWORDS` (basis for `negative_values` reasoning).
- [Source: _bmad-output/planning-artifacts/saint-master-prd.md#deterministic-computation] — policy selection may be non-deterministic; value computation must be deterministic. Classification here is a static, deterministic map.

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
