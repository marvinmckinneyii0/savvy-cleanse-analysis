# Epic 3 — Cleaning Engine (Tiers 1–2) + Report Visualizations

<!-- Roadmap restructure 2026-07-09. PRD Phase 9 (self-healing) PULLED FORWARD — data
     cleaning is the core product thesis, not a Phase 9 afterthought. Read-only narrative
     spec; sprint-status.yaml is the status source of truth. Day counts: TBD — requires
     velocity baseline. ~60% Opus. -->

**PRD mapping:** Phase 9 (Pipeline Orchestration + Self-Healing), pulled forward.
**Sizing/model per §13.** Day counts: `TBD — requires velocity baseline`.

## Stories

| # | Story | Size | Model | loop_eligible |
|---|---|---|---|---|
| 3.1 | Classification Layer (`remediation_class` taxonomy) | M | Opus | false |
| 3.2 | Cleaning Engine Core (deterministic only) | L | Opus | false |
| 3.3 | Healing Manifest | M | Opus | false |
| 3.4 | Opt-in Gate & Config (default OFF) | M | Opus | false |
| 3.5 | Judgment-Required Findings Handling | M | Opus | false |
| 3.6 | Cleaned-Data Export | S | Sonnet | true |
| 3.7 | Report Visualizations (manual chart specification) | L | Sonnet | false |
| 3.8 | Notebook Export & Code Generation | M | Sonnet | false (HOLD, see note) |
| 3.9 | Cleaning Mode Definitions & In-Product Disclosure | M | Sonnet | true |

## INVARIANTS (must not drift during implementation)

- Working-copy only. Original data NEVER modified. §2.1 detect-don't-fix.
- Cleaning is opt-in, default off.
- Every remediation logged in the healing manifest.
- Tier 3 findings are NEVER auto-touched, even accidentally. Load-bearing.
- Deterministic remediation set only: null imputation, deduplication, type coercion,
  whitespace normalization, date standardization.

## Story notes

**3.1** — Introduces `remediation_class` on the DQA finding (additive; target
`backend/models/quality_report.py`; see schema-extensions-spec.md). Records the four-tier
ownership model (Tier 1 autonomous / Tier 2 policy-then-execute / Tier 3 human-only /
Tier 4 Enterprise opt-in) as acceptance criteria for the classification layer.

**3.4** — Ship defensible per-column-type imputation defaults (median for skewed numerics,
mode for categoricals, forward-fill for time-indexed). Client MAY override; policy
ownership remains Tier 2. Defaults printed in the healing manifest. An SMB owner who
doesn't know whether nulls in a revenue column should be mean-imputed or forward-filled
either guesses or abandons — defaults must not block a non-expert at step one. Cleaning
policy persists to the `project` entity (Task 4c / schema-extensions-spec.md).

**3.7** — Before/after distribution comparison is unreadable as prose. Extends the Insight
Engine schema (`visualizations` + `analysis_class`, schema-extensions-spec.md) and the
Document Renderer to embed images. Both Epic-1 schemas, extended backward-compatibly.
Analyst specifies which charts appear — NO auto-selection (post-Epic-8 follow-on).
FREE TIER RECEIVES before/after cleaning comparison — a user seeing 340 gaps they CANNOT
fill, beside the whitespace they can, is the entire Starter pitch rendered visually.

**3.8** (Professional+) — Generated pandas MUST be a rendering of the healing manifest, NOT
a parallel artifact (two sources of truth will diverge). The notebook has two structurally
separated halves: (i) provenance — "here is exactly what we did to your data, as executable
code," manifest-derived, pandas/numpy only; (ii) suggested next steps — may reference any
library including sklearn, explicitly downstream, SAINT takes no position on correctness.
Conflating them makes the provenance claim unverifiable. NEVER EXECUTE generated code —
static validation only (`ast.parse()`, import allowlist). Executing it is a sandbox problem
AND would pull sklearn into the environment, breaking Amendment 6.
**HOLD (loop_eligible false regardless of sizing):** held out of the unattended loop for its
FIRST implementation — getting the provenance-vs-suggestion split wrong produces a
client-facing artifact that misrepresents what happened to the client's data, a failure
invisible to a passing test suite. May be retagged true after one human-reviewed
implementation, by explicit human decision only, never automatically.

**3.9** — Client-facing capability descriptions surfaced AT THE ENABLEMENT POINT, not buried
in docs. For Policy Cleaning, each imputation method carries a one-line statement of effect
("median: fills gaps with the middle value; resistant to outliers; may understate
variance"). Client-facing surfaces use descriptive names, NOT tier numbers. Internal
`remediation_class` unchanged. Story 4.11 consumes this copy; do not duplicate it.
