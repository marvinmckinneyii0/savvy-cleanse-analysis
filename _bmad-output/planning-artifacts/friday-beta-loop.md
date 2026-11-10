# SAINT Friday Concierge Beta — Loop Instructions for Claude Code

**Deadline:** Friday 2026-11-13 end of day
**Mode:** Concierge beta only. Human runs the CLI and sends the report. No self-serve upload, login, or billing.

---

## 1. Goal (single source of truth)

### Definition of Done (all must be true by Friday)

1. Contact form and signup form actually capture leads (email, sheet, or simple backend). No console-only or fake API.
2. Public pages make no false claims. API / testimonials / careers / blog / README are either accurate or clearly marked "coming soon" / hidden.
3. Pricing matches the PRD (or is corrected and noted). **Owner: Marvin** — see Reconciliations.
4. CLI path works end-to-end: messy CSV → DOCX/PDF report with recommendations. Human can run it and send the report.
5. Dashboard is either hidden or gated with a clear "beta – contact us" message. No broken `/api/clean` calls visible.
6. Issue #62 has progress comments. Gating decisions (especially D5, D6, D8) are answered.
7. All changes committed, CI green, and a one-command deploy path exists for the sole approver.

### Explicitly out of scope until after Friday

- Charts (Story 3.7)
- Notebook export (Story 3.8)
- Login, billing, self-serve upload
- Full admin dashboard functionality
- Any new feature not on the ranked backlog

### Ranked backlog (work strictly in this order)

1. ~~Resolve D5, D6, D8 on #62 and leave a progress comment.~~ Done 2026-11-10 (cycle 1).
2. ~~Implement real lead capture for contact + signup forms.~~ Built 2026-11-10 (cycle 2, PR #64); live once the form ID is set and the PR is merged.
3. Honesty pass: rewrite or hide false-claim pages + fix README + pricing (pricing: Marvin).
4. ~~Dashboard gate or hide.~~ Built 2026-11-10 (cycle 3, PR #65, together with the D8 page hides): `/dashboard` redirects to `/contact`.
5. Commit briefing + Story 2.6 + all loop files; ensure CI green.
6. Smoke-test CLI → report delivery path.
7. Final deploy readiness.

### Reconciliations with existing repo rules (these win over the loop text)

- **Pricing:** agents do not edit pricing pages or copy (launch-week plan, D7), and a repo hook hard-stops pricing access. Marvin corrects pricing himself; the loop only notes it.
- **Git:** never commit to or push `main`, never merge, never deploy. Each unit goes on its own branch with a PR; Marvin merges.
- **Sprint ledger:** the loop never changes `sprint-status.yaml` status or `loop_eligible`.
- **Other loop:** the Cowork launch-week loop (PR #63) covers overlapping tasks (L1–L6) in the worktree `C:\Users\marvi\saint-launch-loop`. Only one loop should own the site work at a time.

---

## 2. Loop Rules (follow every cycle)

1. Read this entire instruction set and the current STATE section below.
2. Do ONE bounded unit of work from the top of the ranked backlog.
   - Prefer the smallest change that advances the Definition of Done.
   - Use the cheapest capable model for implementation. Reserve high-effort / Fable only for planning and final review.
3. After the unit of work, spawn a fresh-context verifier subagent.
   - Verifier checks only against the cycle's acceptance criteria, tests/diffs, and the Definition of Done.
   - Verifier must not rewrite code. It reports pass/fail + evidence.
4. Append to the STATE section:
   - What was attempted
   - Result (pass/fail + evidence)
   - Any new verified fact or distilled lesson
   - Next recommended action
5. Stop rules (end the cycle cleanly if any are true):
   - The success condition for this unit is met
   - The same step has failed 3 times
   - This cycle's token budget is spent
   - A decision from #62 is still blocking and cannot be assumed

Never expand scope.
Never implement charts, notebook, login, or billing.
Never leave the cycle without writing to STATE.

---

## 3. Model Routing (token minimization)

- Orchestrator / planner / final review → Fable 5 (high effort)
- Implementation, file edits, tests, searches → Sonnet or cheaper
- Verifier → fresh context, preferably a different model (Sonnet or Haiku)

---

## 4. Current STATE (update after every cycle)

### Verified Facts
- Backend Epics 1–2 complete. Epic 3 Stories 3.1–3.6 + 3.9 done. 414 tests pass, CI green.
- Charts (3.7) and notebook (3.8) are not required for Friday.
- Merged to `main` 2026-11-10 at Marvin's instruction: PR #64 (contact + signup forms POST to Formspree via `src/lib/leadCapture.ts`) and PR #65 (API, API reference, testimonials, careers, blog unrouted; `/dashboard` redirects to `/contact`).
- PR #66 (open) hides the Business Intelligence and Feedback home sections and unroutes `/documentation` and `/guides`.
- PR #67 (open) rewrites the home sections (Hero, Key Features, analysis, How It Works, CTA, request card) and `index.html` metadata for the concierge beta; `src/test/homeCopy.test.tsx` guards against the old claims returning.
- PR #68 (open) rewrites `/features` and the `/contact` FAQ + contact-type descriptions; `src/test/publicPagesCopy.test.tsx` guards both pages.
- Still untrue on public pages after #66–#68: `/about`; `/savvy-analytics`; README. On `/contact`, the emails, location, response time and the dead "Email Support" button are unconfirmed/untouched. See `public-copy-audit-2026-11-10.md`.
- PR #69 (open) rewrites the README; every command in it was run first.
- **CLI smoke test, 2026-11-10 (backlog item 6, partial), fresh `uv sync --dev`, no `.env`, sample data in `backend/tests/e2e/sample_data/`:** Word report OK with `--no-clean`, with no flag, and with `--clean --cleaned-output`; cleaned CSV written. All runs used the FALLBACK narrative.
- **LLM narrative cannot run from a fresh install:** `anthropic`, `openai`, `google-genai` are not in `pyproject.toml` (only `backend/requirements.txt` lists two of them, and names `google-generativeai`, not the `google-genai` the code imports). Not installed in the main checkout's venv either; no `.env` in either checkout. Code reads `GEMINI_API_KEY`; `.env.example` lists `GOOGLE_API_KEY`. With `anthropic` hand-installed and no key the call fails with TypeError; a real LLM narrative is UNVERIFIED.
- PR #70 (open) fixes the above: declares the three SDKs, makes the CLI call `load_dotenv()` on every run (it was skipped with `--no-clean`), and corrects `.env.example` to `GEMINI_API_KEY`. 418 backend tests pass. With the fix and no key, providers fail on missing credentials instead of imports. A real LLM narrative is STILL UNVERIFIED; model IDs (`claude-sonnet-4-6`, `gpt-4o`, `gemini-2.0-flash`) unchecked against live APIs.
- **PDF fails on this Windows machine:** WeasyPrint native libraries (GTK runtime) missing; `--format pdf` errors and writes nothing. Site copy promises "Word or PDF".
- **Critical findings halt with no report:** `critical_quality_issues.csv` (60% nulls in a column) halts, exit 1, nothing written. A customer with a badly broken file gets no deliverable.
- No human review step for reports is defined anywhere. Site copy must not promise one unless Marvin commits to it (removed from #67 and #68).
- A6 answered 2026-11-10: the beta accepts CSV only.
- Pricing on site does not match PRD per the PRD's own note (pricing files blocked by safety hook; not read).
- Only one person can approve, merge, or deploy.
- Briefing, Story 2.6 changes and this loop file are uncommitted.

### Decisions answered (Marvin, 2026-11-10)
- **D5 — Form backend:** Formspree.
- **D6 — Data handling:** customers send CSVs by shared link (Drive / Dropbox / OneDrive) after Marvin replies; files deleted 7 days after report delivery; 100 MB max; refuse health records, financial account data and government IDs.
- **D8 — Pages to hide:** API, API reference, testimonials, careers, blog, dashboard.

### Open Failures / Blockers
- Lead capture is merged but not live. **Needs from Marvin:** create a Formspree form (needs his account; agents cannot) and set `VITE_FORMSPREE_FORM_ID` locally and on the host. Until then both forms show an error pointing to the support email. Real delivery is untested.
- **Definition of Done #4 is NOT met:** the report's LLM narrative is unreachable from a fresh install (missing SDK dependencies) and unverified; PDF output fails on this machine. Needs a backend fix PR (add SDKs to `pyproject.toml`, fix `.env.example`), one real run with Marvin's API key, and either the GTK runtime or Word-only site copy.
- Public surface does not match working product: `/about` and `/savvy-analytics` still unverified; site says "AI only writes the narrative", untrue of a fallback report.
- Still unanswered on #62: D1, D3, D4, D7, D9–D12. D3/D4 gate deploy.
- Uncommitted work creates merge/deploy risk.

### Lessons
- Maker must never grade its own work. Always use a fresh-context verifier.
- Prefer the simplest possible form backend that actually delivers leads over a perfect internal API.
- For concierge beta, "hide or soften" is faster and safer than "build the missing feature."
- Keep every cycle to one bounded unit of work. End cleanly even if incomplete.
- The repo's safety hook blocks any shell command whose text mentions pricing, even a PR description or a grep. Expect it; pricing work itself stays with Marvin.
- Do site work in the `saint-friday-loop` worktree, one branch per unit from `origin/main`; `npm ci` is already done there.

### Last Session
- Cycle 3 complete: D8 pages unrouted and unlinked, `/dashboard` redirects to `/contact`, verified (PASS), PR #65 open. Page source files kept. The two price-page files still link to `/dashboard`; the redirect covers them.
- Cycle 4 complete: copy audit written to `public-copy-audit-2026-11-10.md` (uncommitted, main checkout). No copy changed.
- Cycle 5 complete: Marvin approved the four hides; built, verified (PASS), PR #66 open. PRs #64 and #65 merged at his instruction.
- Cycle 6 complete: home copy rewritten, verified (PASS), PR #67 open.
- Cycle 7 complete: `/features` + `/contact` FAQ rewritten; verifier FAILED once (unsupported "checks the report before sending" promise), fixed, re-verified PASS; PR #68 open. Same promise removed from PR #67 (extra commit, tests re-run, not re-verified).
- Blocked on Marvin: merge PRs #66, #67, #68; answer A1–A5 (about-page team/stats/timeline, Savvy Analytics page facts, contact emails); Formspree form ID.
- Next action: README rewrite (audit row 20; needs no answers). Then `/about` (A1–A3) and `/savvy-analytics` (A4) once answered; if unanswered by Wednesday, propose hiding both.
- Lesson: give the verifier the ground truth of what exists and have it judge every sentence; a term blocklist alone missed an unsupported process promise.
- Lesson: long inline heredoc scripts with apostrophes can break the shell; write the script to the scratchpad and run the file.

### Cycle Log (append only)
<!-- Format: YYYY-MM-DD | cycle-N | what was attempted | result | next -->
- 2026-11-10 | cycle-1 | Resolve D5, D6, D8 (backlog item 1) | PASS — Marvin answered all three in session; recorded in STATE and as a comment on #62 | Item 2: Formspree lead capture (needs form ID)
- 2026-11-10 | cycle-2 | Wire contact + signup forms to Formspree (backlog item 2) | PASS — verifier confirmed all 8 criteria; `npm test` 30 passed, `npm run build` ok; PR #64. Not tested: live delivery, browser check | Item 3: hide D8 pages, then honesty pass
- 2026-11-10 | cycle-3 | Hide D8 pages + dashboard (items 3 part, 4) | PASS — verifier confirmed all 6 criteria; `npm test` 27 passed, `npm run build` ok; PR #65. Not tested: browser check | Item 3 remainder: copy audit + rewrite of public pages, README
- 2026-11-10 | cycle-4 | Audit copy on all public pages + README (item 3) | DONE, no verifier run (document only, no code; Marvin approves the table) — `public-copy-audit-2026-11-10.md`: 20 rows; 5 hide, 11 rewrite, 3 keep/owner; 6 questions (A1–A6) | Await Marvin's approval + A1–A6, then PR 1: hide BI + Feedback sections, /documentation, /guides
- 2026-11-10 | cycle-5 | Merge #64 + #65 (Marvin's instruction); hide BI + Feedback sections, /documentation, /guides (item 3) | PASS — verifier confirmed all 7 criteria; `npm test` 42 passed, `npm run build` ok; PR #66. Not done: Formspree form (needs Marvin's account). Not tested: browser check | Home copy rewrite once Marvin approves rewrites + answers A6
- 2026-11-10 | cycle-6 | Rewrite home copy + site metadata for the concierge beta, CSV only (item 3) | PASS — verifier confirmed all 8 criteria, sentence by sentence against the backend; `npm test` 54 passed, `npm run build` ok; PR #67. Not tested: browser check | `/features` and `/contact` FAQ rewrite
- 2026-11-10 | cycle-7 | Rewrite `/features` and `/contact` FAQ + contact types (item 3) | FAIL then PASS — first verdict failed on an unsupported report-review promise (features.tsx); removed, re-verified against all 7 criteria; `npm test` 69 passed, `npm run build` ok; PR #68. Same sentence removed from #67 (54 tests pass). Not tested: browser check | README rewrite
- 2026-11-10 | cycle-8 | Rewrite README; run every documented command (items 3, 6 partial) | FAIL then PASS — first verdict failed: README said to set a key after `uv sync`, but LLM SDKs are undeclared so the narrative always falls back; corrected, re-verified against all 9 criteria; PR #69. Smoke test found: LLM narrative unreachable/unverified, PDF fails here, critical files halt with no report | Backend fix PR for LLM dependencies (needs Marvin's go-ahead and a key for one test run); decide PDF
- 2026-11-10 | cycle-9 | Fix LLM narrative setup: declare SDKs, load .env on every CLI run, fix env var name (item 6) | PASS — verifier confirmed all 10 criteria; `uv run pytest` 418 passed; trial run completes, no import errors; PR #70. Unproven: any real LLM call (no key) | Marvin: merge #70, put a key in `.env`, run one report and confirm `fallback_narrative` is false. Then update the README bullet from #69. Loop: next unblocked work is committing the loop/briefing/audit docs (item 5) or the concierge runbook
- 2026-11-10 | cycle-10 | Commit loop file, Grok briefing and copy audit on a docs branch (item 5, partial) | DONE, no verifier run (documents only, copied unchanged from the main checkout) — PR opened. Story 2.6 story file and the sprint-status edit are Marvin's and stay uncommitted | Marvin: merge, then remove the untracked copies in the main checkout before pulling. Loop: concierge runbook (O1) with the commands proven in cycle 8

---

## 5. Verifier Prompt (use in a fresh-context subagent)

```
You are a strict verifier. You did not write the code under review.

Read:
- The cycle's acceptance criteria
- The Definition of Done
- The diff / test output provided

Rules:
- Only report pass or fail.
- Cite concrete evidence (file + line, test name, or observable behavior).
- Do not suggest rewrites or alternative designs.
- Do not expand scope.
- If any acceptance criterion is unmet, the whole unit fails.

Output format:
PASS or FAIL
Evidence:
- ...
- ...
Blockers (if any):
- ...
```
