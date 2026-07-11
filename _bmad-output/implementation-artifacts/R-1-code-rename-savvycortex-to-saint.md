# Story R.1: Code Rename — savvycortex → saint

Status: ready-for-dev

Sizing: M · Model: Sonnet · loop_eligible: false

<!-- Filed 2026-07-09 roadmap restructure (Task 8). NOT executed here. This story aligns
     the CODE to the SAINT documentation rename (Amendment 8, which was docs-only). -->

## Story

As the SAINT maintainer,
I want the `savvycortex` code package and its references renamed to `saint`,
so that the codebase matches the SAINT product name established in documentation
(Amendment 8) — closing the deliberate, time-boxed doc-vs-code name mismatch.

## Scheduling (LOAD-BEARING)

Execute at the clean seam: **AFTER Story 2.5 merges, BEFORE Story 3.1 begins.**
- Story 2.5 has merged (Epic 2 complete) — the "after 2.5" precondition is met.
- Doing it during Story 2.5 means merge conflicts on `feat/story-2.5-monitoring-agent`.
- Doing it during Epic 3 means renaming a package while writing a nine-story cleaning
  engine into it. Both are avoided by executing now, with nothing in flight.

## Scope

- `savvycortex/` package directory → `saint/`
- All `from savvycortex.*` imports across the codebase
- `backend.api.app:app` entrypoint reference, if affected
- Repo `savvy-cleanse-analysis` → renamed per Marvin's instruction (requires Marvin —
  GitHub repo rename is a human action, not an in-repo edit)
- Landing page code sample `import savvyclean as sc` → correct package name (`saint`)

## Explicitly OUT of scope (must NOT change)

- Component filenames `dqa_engine.py` and `drift_engine.py` — UNCHANGED, permanently.
  The previously-held "cosmetic rename" of these components is VOID; SAINT is the
  product name, the components keep their current names. (Recorded so it does not
  resurface.)
- Any documentation rename — already done in the restructure (Amendment 8).

## Acceptance Criteria

1. `savvycortex/` package directory is renamed to `saint/`; the package imports and
   runs under the new name.
2. Every `from savvycortex.*` / `import savvycortex` reference across the codebase is
   updated to `saint`. No `savvycortex` code identifier remains (documentation
   references may remain historical, e.g. archived files and this story).
3. The `backend.api.app:app` entrypoint (and any CLI `-m backend.*` invocations)
   resolve under the renamed package.
4. The landing-page code sample `import savvyclean as sc` is corrected to the real
   package name.
5. Component filenames `dqa_engine.py` and `drift_engine.py` are unchanged.
6. **All tests pass post-rename before merge.** 181 tests currently pass (Epic 1: 6
   stories; Epic 2: 2.3 = 154, 2.4 = 165, 2.5 = 181). The full suite must be 181
   passed / 0 regressions after the rename (`uv run pytest backend/tests/
   --ignore=backend/tests/test_parse_file.py`).

## Constraints

- OWN BRANCH (e.g. `chore/R1-code-rename-saint`). Own test run. Own PR. Own merge.
- Execute at the clean seam (see Scheduling): nothing else in flight.
- The GitHub repo rename (`savvy-cleanse-analysis` → per Marvin's instruction) is a
  human step Marvin performs; the story updates in-repo references and the story
  should flag the repo-rename hand-off explicitly.

## Tasks / Subtasks

- [ ] Create branch `chore/R1-code-rename-saint` from a clean main (2.5 merged, Epic 3
      not yet started).
- [ ] `git mv savvycortex/ saint/` (preserve history). Confirm `dqa_engine.py` /
      `drift_engine.py` filenames unchanged.
- [ ] Update every `from savvycortex.*` / `import savvycortex` → `saint` (codebase-wide;
      exclude archived docs and this story file).
- [ ] Update `backend.api.app:app` entrypoint reference and any `python -m backend.*`
      invocations / packaging metadata (pyproject, etc.) as affected.
- [ ] Correct the landing-page `import savvyclean as sc` sample.
- [ ] Full suite green (181 passed / 0 regressions). Run /security-review; resolve any
      Critical/High.
- [ ] Open PR. In the PR, flag the GitHub repo-rename hand-off for Marvin.

## Dev Notes

- This is a mechanical, high-blast-radius rename — hence `loop_eligible: false` and a
  human merge. It touches every import; execute it as one atomic change at the clean
  seam, not incrementally alongside feature work.
- Documentation already says SAINT (canonical PRD, epics.md, sprint-status.yaml,
  reconciliation, story files). This story removes the last remaining, deliberately
  documented divergence — the code identifiers.
