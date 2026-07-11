# Story R.1: Code Rename → SAINT

Status: ready-for-dev

Sizing: M (backend-only) / L (if frontend rebrand included) · Model: Sonnet · loop_eligible: false

<!-- Filed 2026-07-09 roadmap restructure (Task 8). CORRECTED 2026-07-11 against the actual
     codebase — the original scope (inherited from the PRD §7.3 ASPIRATIONAL layout) did not
     match reality. NOT executed. Scope is DEFERRED to deliberate human scheduling. -->

## ⚠️ Reality correction (2026-07-11) — read before scoping

The PRD §7.3 file structure, Amendment 8, and the reconciliation NAME MISMATCH note all
describe an **aspirational** `savvycortex/` package layout that was **never implemented**.
Verified against the actual tree on main:

| Original R.1 / Amendment 8 assumption | Actual codebase |
|---|---|
| `savvycortex/` package directory | **Does not exist.** The Python package is `backend/`. |
| `from savvycortex.*` imports | **None.** All imports are `from backend.*`. |
| `backend.api.app:app` entrypoint | Exists (FastAPI title "SavvyCortex API"). Module is `backend.api.app`. |
| Component filename `dqa_engine.py` (keep unchanged) | **Does not exist.** The DQA engine is `backend/pipeline/data_quality.py`. `drift_engine.py` does exist. |
| Landing-page `import savvyclean as sc` code sample | **No such sample.** The frontend is brand-named **"SavvyClean"** in **19 files** (index.html + 18 under src/; verified 2026-07-11). |

**The product name in code is split, and neither half is a `savvycortex/` package:**
- **Backend** carries "SavvyCortex" prose only (docstrings, Typer help, FastAPI title,
  `pyproject.toml name = "savvycortex"`, exception-module docstring, and the alert email
  Subject/from-address in `monitoring_agent.py`). The package directory is the neutral
  name `backend/`, NOT the product name.
- **Frontend** is client-facing branded **"SavvyClean"** across `index.html` (title + og
  meta), `src/components/*` (Hero, Navbar, Footer, AnalysisTypes, Feedback, SignupForm,
  AdminDashboard), and `src/pages/*`. Note: Amendment 8 says "SavvyClean was already
  retired and must not reappear" — yet it is the currently-shipping public name. Retiring
  it is a client-facing change, not a code-internal one.

So R.1 **cannot be executed as originally written** (its targets don't exist). The genuine
rename surface is different and must be scoped deliberately — hence this story stays
`ready-for-dev` and is NOT auto-executed.

## Actual rename surface (by area)

- **A. Backend product-name (Python).** `pyproject.toml` `name`/`description`; "SavvyCortex"
  prose in `backend/agents/reporting_agent.py`, `backend/agents/monitoring_agent.py`
  (Typer help + email Subject/from-address), `backend/api/app.py` (FastAPI title),
  `backend/errors/exceptions.py`, `backend/pipeline/orchestrator.py`, `backend/models/
  pipeline_result.py`, and "NOT part of the SavvyCortex pipeline" comments in the legacy
  modules (`advanced_pipeline.py`, `comprehensive_analytics.py`, `dashboard_api.py`,
  `main.py`, `main_enhanced.py`, `nlp_processor.py`). The `backend/` package directory and
  `from backend.*` imports are NOT the product name — leaving them is defensible.
- **B. Frontend brand (SavvyClean → SAINT).** 19 files (verified 2026-07-11): `index.html`
  (title + og meta), `src/components/{Hero,Navbar,Footer,AnalysisTypes,Feedback,SignupForm}`
  + `src/components/dashboard/AdminDashboard`, and 11 `src/pages/*` (about, api, api-reference,
  blog, careers, contact, documentation, features, guides, savvy-analytics, testimonials).
  Client-facing; wants its own visual/QA pass.
- **C. Repo rename** `savvy-cleanse-analysis` → per Marvin's instruction. A GitHub action a
  human performs; also `README.md` clone URL / `savvycleanse/` references.
- **D. Non-code artifacts.** `README.md` badge, `config.yaml`, `daily_report.txt`,
  `daily_ops.log`, `codex_handoff.yaml`, `pr_status.yaml`, `story.yaml` (as they are next
  touched — not load-bearing).
- **Optional / highest blast radius:** rename the `backend/` package → `saint/` (touches
  every `from backend.*` import, `backend.api.app:app`, and all `python -m backend.*`
  invocations). Not required by the product rename; only if explicitly desired.

## Scheduling (unchanged)

Execute at the clean seam: **AFTER Story 2.5 merges (done), BEFORE Story 3.1 begins**, on its
OWN branch, own test run, own PR, own merge. The blast radius (especially areas B/optional)
is why this is `loop_eligible: false` with a human merge.

## Acceptance Criteria (to be finalized when scope is chosen)

1. Chosen rename scope (A, A+B, or A+B+package) applied; no unintended identifiers changed.
2. `drift_engine.py` and `data_quality.py` filenames unchanged (component filenames stable).
3. **Full suite green post-rename** — 181 passed / 0 regressions (`uv run pytest backend/tests/
   --ignore=backend/tests/test_parse_file.py`). If the frontend is in scope, the frontend
   build/tests are green too.
4. If area C is in scope: the GitHub repo-rename hand-off is flagged for Marvin (human action).
5. Run /security-review; resolve any Critical/High.

## Note

This story's scope is intentionally left open pending a human decision (recorded 2026-07-11:
the maintainer chose to re-file with corrected scope rather than execute now). The PRD
Amendment 8 and reconciliation NAME MISMATCH note should be read in light of this correction —
they describe the intent (documentation says SAINT; code will follow) but their specific
package/filename references reflect the aspirational §7.3 layout, not the implemented tree.
