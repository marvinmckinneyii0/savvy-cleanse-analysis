# Unattended Development Loop — Specification

<!-- Created 2026-07-09 roadmap restructure (Addition 2). Governs a bounded,
     human-checkpointed loop that develops low-judgment stories without Marvin present.
     The `loop_eligible` flag in sprint-status.yaml is human-set; this loop never changes it. -->

## Purpose
Allow bounded, low-judgment story development to proceed without requiring Marvin
present, while preserving a human checkpoint before any code merges.

## Selection
On each run, select the single next story where ALL are true:
  - status: ready-for-dev
  - loop_eligible: true
  - all upstream dependencies (per story file) are status: done
If no story qualifies, exit. Do not idle-poll or select ineligible work.

## Execution
  1. Implement the story per its story file and acceptance criteria.
  2. Run the full existing test suite, not just new tests.
  3. Run any security/lint checks already configured in CI.
  4. If ANY of the following occur, HALT this story, mark status:
     blocked-needs-review, and STOP the loop entirely (do not proceed to
     another story this run):
       - a test fails and cannot be resolved by code within THIS story's
         stated scope
       - the implementation reveals a gap, contradiction, or ambiguity
         against the master PRD or a locked architectural constraint
       - the story appears to require touching a file, schema, or module
         outside its declared scope
       - anything that would, under the main restructure prompt's HALT
         conditions, require asking Marvin
  5. If clean: commit, push to a story-specific branch
     (loop/story-{id}), open a PR. DO NOT MERGE.
  6. Write a one-paragraph PR summary: what was built, what was tested,
     anything worth a second look even if not blocking.

## Hard limits
  - One story per run. Never chain multiple stories unattended.
  - Never modify sprint-status.yaml's loop_eligible field. That is a
    human-set value.
  - Never touch a story tagged loop_eligible: false, regardless of
    apparent simplicity discovered during execution.
  - Never merge. Every PR from this loop requires Marvin's review and
    manual merge, with no exception.
  - If the loop's own token/credit usage for a single story exceeds a
    reasonable multiple of that story's sizing tier (S/M expectation),
    HALT and flag rather than continuing to spend.

## What this loop is NOT for
  - Anything in Epics 9, 10, 11, 12, 14, 15 — entirely excluded by tag.
  - Any story marked "load-bearing," "invariant," or "must not drift."
  - Anything the moment it turns out to be harder than its sizing tier
    suggested. Difficulty discovered mid-story is itself a signal to
    HALT, not push through.

## Cadence
Recommended: once daily, off-hours. Not continuous. A continuous loop
against a small ready-for-dev queue produces either idle polling or
pressure to loosen loop_eligible criteria to keep it fed — resist both.
