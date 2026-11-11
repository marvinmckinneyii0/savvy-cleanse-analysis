# SAINT — Project Briefing for Loop Planning

**As of:** Tue 2026-11-10 · **Deadline:** Fri 2026-11-13 (concierge beta launch)
**Your job (Grok):** pick the best execution loop (task order, who does what, parallelism, cut lines) to hit Friday's go/no-go. Constraints and the current state are below. Everything here comes from the GitHub repo, open issues/PRs, CI, and the sprint ledger.

---

## 1. What SAINT is (purpose)

**SAINT (Savvy Analytics Intelligence)** is a data-intelligence product. A business uploads a messy CSV/Excel file. SAINT checks data quality, can optionally clean a working copy, finds insights, and produces a **branded DOCX/PDF report an executive can read**, with recommendations, not just charts.

- **Problem:** organizations have data but can't get decisions out of it. Analysts spend ~80% of their time cleaning and ~20% analyzing.
- **Positioning:** "Operational intelligence infrastructure for decision-making."
- **Long-term arc:** data-cleaning tool → intelligence layer (drift, forecasting, root cause, scenarios) → agentic operating system → industry verticals (marketing first; finance and healthcare are deferred pending research).
- **Core principles that constrain all work:**
  - Every insight shows its evidence.
  - Statistics are deterministic. The LLM only writes the narrative from numbers already computed and never invents numbers.
  - Human in the loop: the system recommends, a person decides.
  - Detect, don't silently fix: cleaning is opt-in, off by default, and runs on a working copy, never the source.
  - Every engine output is checked against a Pydantic schema.
- **Target customers:** SMEs (first adopters), then finance, healthcare and operations-heavy businesses.
- **Product name history:** formerly "SavvyCortex" / "SavvyClean". The repo is still named `savvy-cleanse-analysis`, and the Python error class is still `SavvyCleanseError` (kept on purpose).

## 2. What "launch Friday" means

A **concierge beta**: a done-for-you service built on what already works.

1. A prospect visits the marketing site and submits an **intake request**. The site has no file upload.
2. Marvin (founder, solo) collects their CSV, runs the **SAINT CLI** locally, checks the report, and sends back the DOCX/PDF.
3. Marvin posts Wave 1 directory submissions on Friday.

**Not in this launch:** accounts/login, billing, multi-tenancy, self-serve upload, public API (Epics 4–8). **Site copy must not claim any of these.**

## 3. Where the build is

| Epic | Scope | Status |
|---|---|---|
| 1 | Data-quality assessment, insight engine, LLM narrative, DOCX/PDF rendering, CLI | **Done** |
| 2 | Config layer, LLM client (Claude→OpenAI→Gemini fallback), drift engine, reporting agent, monitoring/alerts | **Done**, reopened only for Story 2.6 |
| 3 | Cleaning engine (Tier 1–2), healing manifest, opt-in gate, Tier-3 "judgment required" boundary, cleaned-data export, cleaning-mode disclosure | **In progress.** 3.1–3.6 and 3.9 done. 3.7 (report charts) and 3.8 (notebook export) are backlog. |
| 4–13 | Web app, Stripe billing, multi-tenant, admin, advanced analytics, advanced drift, simulation, Tier-4 autonomy, adapters, marketing vertical | **Backlog** (none started) |
| 14–15 | Finance / healthcare verticals | Deliberately deferred pending research |

- **Backend tests:** 414 passed / 1 skipped at the last merge (PR #55). CI on GitHub Actions runs pytest, vitest, vite build and CodeQL, and all recent runs are green.
- **Story 2.6 (config-driven LLM model routing):** the story file exists and is marked ready-for-dev, but it is **uncommitted locally** (the story file and the sprint-status edit are not pushed).
- **Not needed for Friday:** 2.6, 3.7 and 3.8. The reports work without charts.

## 4. Codebase structure

Monorepo: React frontend at the root, Python backend in `backend/`.

```
backend/                 Python 3.13, uv, FastAPI, Pydantic v2, Pandera, structlog, Typer
  pipeline/              orchestrator.py (Typer CLI entry), data_quality, insight_engine,
                         narrative_generator (LLM), drift_engine, cleaning_engine,
                         cleaning_primitives, remediation_classifier, config
  rules/                 cleaning_coordinator (opt-in gate + Tier-3 runtime guard), cleaning_policy
  models/                Pydantic contracts (quality_report, insight_report, healing_manifest,
                         judgment_required_finding, cleaning_disclosure, drift_report, alert...)
  renderers/             docx_renderer (docxtpl), pdf_renderer (WeasyPrint), templates/
  agents/                reporting_agent (APScheduler), monitoring_agent (alerts)
  core/                  llm_client (multi-provider fallback), logging, extraction_client (spec only)
  api/                   app.py: minimal FastAPI with ONLY /health + the file-parse router
  tests/                 24 pytest modules + e2e/
  LEGACY (never import): advanced_pipeline.py, comprehensive_analytics.py, nlp_processor.py,
                         analytics.py, main_enhanced.py, dashboard_api.py, main.py, cleaner.py
src/                     React 18 + Vite 5 + TS 5.5 + Tailwind + shadcn/ui (49 components), TanStack Query
  pages/                 Index, Dashboard, features, pricing, testimonials, api, api-reference,
                         documentation, guides, blog, about, careers, contact, savvy-analytics, NotFound
  components/            marketing sections (Hero, Features, Pricing, CTA, SignupForm, Feedback...)
  components/dashboard/  UploadArea, CleaningPreview, AnalysisResults, ChartGrid, ApiKeyManager,
                         LiveDataStream, AdminDashboard, UserDashboard, DatasetManager...
  integrations/supabase/ client reads VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY from env (no hardcoded keys)
agent-system/            completion_loop.py / handoff_loop.py: Claude↔Codex orchestration loops + policy
supabase/                config, migrations, functions (two Supabase projects exist, unification is Epic 4)
_bmad-output/            BMAD planning: PRD, architecture, epics, per-story specs, sprint-status.yaml (SOLE status source of truth)
.github/workflows/ci.yml pytest + vitest + vite build
```

**How a report is produced today:** `uv run` the Typer CLI in `backend/pipeline/orchestrator.py` with `--input file.csv --output report.pdf --format pdf|docx`. Cleaning is optional (`--clean`) and so is a cleaned-data export (`--cleaned-output`). The pipeline runs: parse → DQA → (optional cleaning + healing manifest) → insights → LLM narrative → render. It needs an LLM API key in `.env`.

## 5. Frontend: state and problems (critical path for Friday)

The frontend started as a Lovable/Vite scaffold and is **mostly a marketing site plus a mock dashboard**. It is **not connected** to the real pipeline.

- **The intake form doesn't work.** `contact.tsx`'s `handleSubmit` only does `console.log` and resets the form. `SignupForm.tsx` fakes an API call with a 1-second `setTimeout`. **No lead capture exists today.** This is the #1 functional blocker.
- **The dashboard is a non-functional mock.** `Dashboard.tsx` hardcodes `isAdmin = true`. `src/utils/api.ts` POSTs to `/api/clean`, which **does not exist**: the FastAPI app serves only `/health` and parse. ApiKeyManager, LiveDataStream, AdminDashboard and UserDashboard show features that don't exist. **For the concierge beta, hide or route out `/dashboard`.**
- **Claims that aren't true yet:** pages for API, API reference, testimonials, careers and blog, plus features copy. Testimonials need checking for invented quotes. **Hide or rewrite them, and never invent quotes, logos or metrics.**
- **Pricing is wrong versus the PRD.** The PRD says the frontend's "$29 Pro" tier is incorrect (canonical: Free / Starter $49 / Pro $149 / Enterprise). **Rule: the loop must NOT edit pricing pages or copy. Marvin edits them himself (decision D7).**
- **The README is stale.** It advertises `/upload`, `/clean`, `/analyze`, `/report/summary` and `/export` endpoints and natural-language querying, none of which exist. Fix it or leave it out of anything public.
- **Domain:** API-doc pages referenced `api.savvyclean.com`, and the domain is still undecided (D4).
- **Code quality:** TypeScript runs with relaxed settings (`strictNullChecks: false`, `noImplicitAny: false`). There are only 3 frontend test files (DataPreview, UploadArea, fileParser). Nothing is deployed yet and no host is chosen (D3).

## 6. Backend and codebase issues (known, mostly non-blocking for Friday)

- Legacy modules are still in `backend/` and must never be imported. `main_enhanced.py` once had hardcoded credentials (now removed from the file). **Confirm any keys that were ever committed have been rotated.**
- Dead `extreme_cardinality` detector bug (tracked follow-up from Story 3.5).
- Future Tier-3 detector text needs a client-safety review before it ships.
- `deferred-work.md` holds deferred items from the 3.2 and 3.4 code reviews.
- Open question Q1 from Story 3.4: should the report be generated on the cleaned data or the original? It needs Marvin's answer, which matters if customers choose `--clean`.
- Two Supabase projects exist. Pick one for the intake table if D5 = Supabase.
- `pr_status.yaml`, `story.yaml`, `codex_handoff.yaml`, `daily_ops.log` and `daily_report.txt` sit at the repo root: loop and agent state files, which are clutter.
- The FastAPI layer is minimal on purpose. The real web backend is Epic 4 and is not needed for Friday.

## 7. Blockers: open decisions (GitHub issue #62, all but D2 unanswered)

| ID | Decision | Blocks | Recommendation on file |
|---|---|---|---|
| D1 | Include Story 3.7 (charts) in the launch? | P1/P2 | **Defer.** Reports work without charts. |
| D2 | 3.7 implementer | — | ✅ Codex implements, Claude reviews |
| D3 | Hosting (Vercel / Netlify / Cloudflare Pages) | L7 deploy | Vercel or Netlify (static Vite build) |
| D4 | Launch domain; keep `api.savvyclean.com` refs? | L7, copy | — |
| D5 | Intake form backend (Supabase table / Formspree / mailto) | L4 | Supabase insert-only RLS, or a form service for zero backend |
| D6 | Data handling: how CSVs arrive, retention, max size, refused data (health/financial PII) | L5 privacy/terms, O1 runbook, O3 templates | — |
| D7 | Beta offer: free / paid / contact us | Pricing copy (Marvin only) | — |
| D8 | Which pages to hide | L2, L3 | Proposed by task L1 |
| D9 | Privacy/Terms drafts approved | Go/no-go | Not legal advice |
| D10 | Merge PR #61 (launch checklist) and PR #63 (launch-week plan) | Plan isn't on `main` yet | Merge |
| D11 | PR #58 (shared code memory draft): keep or close | — | — |
| D12 | Friday go/no-go | Wave 1 submissions | — |

**Other blockers and risks:**
- Issue #62 has **0 progress comments**. The launch-week loop either hasn't run or hasn't reported. **Tuesday's plan (L2, L3, O1) is at risk.**
- **D5, D6 and D8 gate most of the critical path.** Unanswered, they block the form, privacy/terms, the runbook and the page cleanup.
- **D3 + D4 gate deployment,** which only Marvin can do.
- **Single human bottleneck:** Marvin answers every decision, merges every PR, deploys, sends every email and submits to directories.

## 8. Open PRs

- **#63:** launch-week plan + loop prompt (docs only, CI green)
- **#61:** later-launch SaaS directory checklist (docs only)
- **#59:** Story 3.7 spec, report visualizations (decisions resolved; stretch)
- **#58:** DRAFT, shared code memory for Claude Code + Codex

## 9. Task list for the remaining week (from the launch-week plan)

**Track L (site, critical path):**
- L1 audit public pages for false claims (keep / rewrite / hide table)
- L2 rewrite home + features for the concierge beta, CTA "Request a data-quality report", pricing untouched (needs L1, D8)
- L3 hide approved pages (D8)
- L4 wire the intake form: validation, honeypot, success/error states, no secrets, no upload (D5)
- L5 draft Privacy + Terms (D6)
- L6 build/preview QA: every route renders, no console errors, mobile, screenshots (L2–L5)
- **L7 deploy (Marvin; needs D3, D4, L6)**

**Track O (operations):**
- O1 concierge runbook with exact CLI commands, QA and data deletion (D6)
- O2 sample DOCX/PDF report from synthetic data
- O3 intake email templates (drafts; Marvin sends)

**Track A (assets):**
- A1 launch copy pack (needs L2)
- A2 screenshots + sample-report images (needs L6, O2)
- A3 Wave 1 directory drafts (needs A1, A2, L7; Marvin submits)

**Track P (stretch):** 3.7 charts (Codex → Claude review). **Recommend cutting it from this week.**

**Friday gate:** site live, intake tested end to end (a real test submission received), privacy/terms published, runbook run once on sample data, no false claims on any page.

**Unblocked right now:** L1, O2, and merging #63/#61 (D10).

## 10. Rules any loop must obey

- One task per run, its own branch, and a PR with checks passing before review: `uv run pytest`, `npm test`, `npm run build`. Report exact results.
- **Agents never:** merge, push to `main`, force-push, deploy, buy or configure domains/hosting, send emails, submit to directories, post on social media, **edit pricing**, or change `sprint-status.yaml` status or `loop_eligible`.
- The launch loop works only in the worktree `C:\Users\marvi\saint-launch-loop`, never in the main checkout.
- Never invent testimonials, metrics, logos or certifications.
- An unanswered decision gets added to issue #62 with options and a recommendation, and the loop moves on to an unblocked task.
- `sprint-status.yaml` is the only status source of truth. Story work follows the story file and `AGENTS.md`.
- Every story runs `/security-review` and resolves Critical/High findings before it is done.
- **Agents available:** Claude Code (planning, review, implementation), Codex (implementation, e.g. 3.7), and the Cowork launch loop. **Human:** Marvin, solo founder, the only approver.

## 11. Questions for Grok

1. What task order and parallelism hits Friday, given that D5, D6 and D8 are the decisions gating the most work?
2. What is the minimum set of decisions Marvin must answer **today (Tue)** to unblock the critical path?
3. What is the cut line if decisions slip (e.g. mailto intake instead of a form backend, hide pages instead of rewriting them)?
4. How should Marvin's review/merge/deploy time be batched (e.g. one merge window Wed evening, deploy Thu)?
5. Should the 3.7 charts be explicitly deferred to avoid splitting attention?
