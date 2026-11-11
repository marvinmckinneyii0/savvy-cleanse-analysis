# SAINT Launch Week — Concierge Beta (target: Fri 2026-11-13)

<!-- Created 2026-11-09. Operating plan for the launch-week Cowork loop.
     Planning artifact only: it does NOT override sprint-status.yaml, story files, or AGENTS.md.
     Decisions live on the pinned GitHub "Launch week: decisions needed" issue. -->

## What "launch" means this week (decided by Marvin, 2026-11-09)

**Concierge beta.** Launch what already works (Epics 1–3: data-quality report, opt-in cleaning on a working copy, DOCX/PDF reports) as a **done-for-you service**:

1. A prospect lands on the site and submits an intake request (no file upload on the site).
2. Marvin receives the request, collects the CSV through the agreed channel, runs the SAINT CLI, and sends back the report.
3. Directory submissions (Wave 1 of `launch-checklist.md`) start Friday — posted by Marvin.

**Not in this launch:** accounts/login, billing, multi-tenancy, self-serve upload, public API (Epics 4–8). Site copy must not claim them.

## Hard rules for the loop (in addition to AGENTS.md)

- One task per run. Work only in the loop worktree (`C:\Users\marvi\saint-launch-loop`), never in `C:\Users\marvi\savvy-cleanse-analysis` (other people/agents work there).
- Never: merge PRs, push to `main`, force-push, amend pushed commits, change `sprint-status.yaml` status or `loop_eligible`, deploy, buy/configure domains or hosting, send emails/messages, submit to directories, post on social media, or edit pricing files/pricing copy.
- Never invent customer quotes, testimonials, logos, metrics, or certifications. Remove or hide anything that looks fabricated; ask before deleting pages.
- Story work (3.7, 3.8, 2.6 …) follows the story file and AGENTS.md exactly. Per the 3.7 decision, **Codex implements 3.7; Claude reviews after**. The loop may prepare/dispatch only through the repository's own mechanisms and only when the ledger allows it.
- If a task needs a decision that isn't answered, add it to the Decisions issue (options + recommendation), mark the task blocked, and move to another unblocked task.
- Every code/docs change: own branch → required checks (`uv run pytest`, `npm test`, `npm run build`) → PR. Report exact results.

## Tasks

Status is tracked on the Decisions issue progress comments, not here. `D#` = decision on the issue.

### Track L — Launch site (critical path)

| ID | Task | Needs | Owner |
|---|---|---|---|
| L1 | Audit every public page/route for claims that aren't true today (features, API, testimonials, careers, blog, security/compliance wording). Produce a table: keep / rewrite / hide, with reasons. Docs-only PR. | — | Loop |
| L2 | Rewrite home + features copy for concierge beta: what SAINT does today, how the beta works (request → we run it → report), honest limits. Primary CTA "Request a data-quality report". Do not touch pricing. | L1, D8 | Loop |
| L3 | Hide/route-out pages Marvin approves hiding (D8). | D8 | Loop |
| L4 | Wire the contact/intake form to the chosen backend (D5). Validate input, no secrets in client code, success/error states, spam honeypot. No file upload. | D5 | Loop |
| L5 | Draft Privacy Policy + Terms (beta) pages from the agreed data-handling answers (D6). Clearly marked drafts for Marvin's review; not legal advice. | D6 | Loop draft → Marvin approves |
| L6 | Build/preview check: production build, every route renders, no console errors, mobile width OK. Screenshots attached to PR. | L2–L5 | Loop |
| L7 | Deploy to chosen host + domain (D3, D4). | D3, D4, L6 | **Marvin** |

### Track O — Concierge operations

| ID | Task | Needs | Owner |
|---|---|---|---|
| O1 | Concierge runbook: intake → receive CSV → run CLI (`--clean` per customer choice, PDF/DOCX) → QA the report → deliver → delete data per retention (D6). Include exact commands. | D6 | Loop |
| O2 | Generate a sample report (DOCX + PDF) from repo sample data for the site and directory listings; commit only if data is synthetic. | — | Loop |
| O3 | Intake checklist/email templates (request received, send-your-file instructions, report delivered). Drafts only — Marvin sends. | D6 | Loop |

### Track P — Product (stretch, not a launch blocker)

| ID | Task | Needs | Owner |
|---|---|---|---|
| P1 | Merge #59 and promote 3.7 to `ready-for-dev`. | D1 | **Marvin** |
| P2 | 3.7 implementation (Codex), then Claude review at the exact SHA, then draft PR. | P1 | Codex → Loop review |
| P3 | 3.8 notebook export — post-launch (HOLD story, human-reviewed first implementation). | — | later |

### Track A — Launch assets

| ID | Task | Needs | Owner |
|---|---|---|---|
| A1 | Launch copy pack: one-liner, short/long descriptions, 3 feature bullets, FAQ — consistent with L2 and with Story 3.9 cleaning wording. | L2 | Loop |
| A2 | Screenshots + sample-report images for listings (from L6/O2). | L6, O2 | Loop |
| A3 | Wave 1 directory submission drafts (per-site fields filled in a doc). | A1, A2, L7 | Loop draft → **Marvin submits** |

### Friday gate (Marvin)

Go/no-go (D12): site live, intake works end-to-end (test submission received), privacy/terms published, runbook tested once on sample data, no false claims on any page. Then Marvin posts Wave 1.

## Suggested day plan

- **Mon 11/09:** L1, O2; Marvin answers D3–D8.
- **Tue 11/10:** L2, L3, O1; P1 if Marvin wants 3.7 in the beta.
- **Wed 11/11:** L4, L5, O3; P2 starts (Codex).
- **Thu 11/12:** L6, A1, A2; Marvin reviews/merges launch PRs and deploys (L7).
- **Fri 11/13:** A3 drafts; go/no-go; Marvin submits Wave 1.
