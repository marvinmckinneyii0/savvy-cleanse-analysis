# Epic 9 — Advanced Drift + Root-Cause Analysis

<!-- Roadmap restructure 2026-07-09. PRD Phase 7 + §14 root-cause (pulled in). 6 stories,
     ~65% Opus. ALL loop_eligible: false. Read-only narrative; sprint-status.yaml is
     authoritative. Day counts: TBD — requires velocity baseline. Part of the PRE-VERTICAL GATE. -->

**PRD mapping:** Phase 7 (Advanced Drift) + §14 root-cause analysis (pulled in from vision).

## Stories

| # | Story | Size | Model | loop_eligible |
|---|---|---|---|---|
| 9.1 | Kolmogorov-Smirnov Test for Numeric Drift | M | Opus | false |
| 9.2 | Binned PSI for Numeric Columns | M | Opus | false |
| 9.3 | Multivariate Drift (correlation matrix comparison) | L | Opus | false |
| 9.4 | Baseline Versioning & Adaptive Thresholds | L | Opus | false |
| 9.5 | Root-Cause Analysis: Diagnostic Chains | L | Opus | false |
| 9.6 | Root-Cause Narrative Integration | M | Sonnet | false |

ALL false — diagnostic correctness is not unit-test-catchable; Opus-tier throughout.

## Constraints

- Extends `core/drift_engine.py` (Epic 2, Story 2.3, 154 tests passing).
- Drift severity bands remain **ARCHITECTURE CONSTANTS**, not `PipelineConfig` values.
  Adaptive thresholds adjust WITHIN bands; they do not redefine them.
- `scipy.stats` PERMITTED here per Amendment 6. **No sklearn.**

## 9.5–9.6 rationale

§16.2 maps root-cause to diagnostic analytics. Diagnostic must be advanced pre-vertical.
Traces anomalies back to contributing factors — drift + DQA correlation, which Epic 9 already
computes ("bad data in drifting columns is more concerning"). 9.6: the LLM narrates the
computed diagnostic chain; it never computes it (§2.1).
