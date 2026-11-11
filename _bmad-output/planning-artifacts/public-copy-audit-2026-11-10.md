# Public Copy Audit — Concierge Beta (2026-11-10)

Loop cycle 4, backlog item 3 (honesty pass). Audit only: no copy has been changed.
Scope: every page still routed after PR #65, the home-page sections, site metadata, and the README.
Not read: the price section and price page (owner-only; a repo hook blocks agent access).

## What is true today (the yardstick)

A person at SAINT runs a command-line pipeline on a customer's **CSV** and sends back a report.

- Data-quality assessment: missing values, duplicates, outliers, type and format problems, each with a severity.
- Optional cleaning on a working copy (off unless the customer asks), with a record of every change made and a list of findings left for human judgment.
- Insights: descriptive statistics and basic drift checks against a baseline.
- A written narrative produced by an LLM from the computed numbers.
- A branded DOCX or PDF report; optionally the cleaned CSV.

Not available: self-serve upload, accounts or sign-in, dashboard, charts in reports, notebook or Python export, forecasting or predictive models, optimization or scenario modelling, natural-language queries, public API, sharing links, formats other than CSV in the report path.

## Verdicts

| # | Where | Verdict | Why |
|---|---|---|---|
| 1 | Home — Hero (`Hero.tsx`) | **Rewrite** | "Python-first platform", "Upload CSV, JSON, XLSX, XML, or TXT files. AI cleaning included." There is no upload and only CSV is supported. The mock file tabs show `analysis.ipynb`, which implies notebook export. |
| 2 | Home — Key Features (`Features.tsx`) | **Rewrite** | Four of six cards describe things that do not exist: Jupyter/Python code export, guided interactive analytics, automatic charts and dashboards, Python code sharing. "Unstructured data" cleaning is not built. |
| 3 | Home — Business Intelligence (`BusinessIntelligence.tsx`) | **Hide** | Four sample charts with made-up sales, market-share and user numbers. They imply a dashboard product and reports with charts; neither exists. |
| 4 | Home — Four Types of Analytics (`AnalysisTypes.tsx`) | **Rewrite** | Predictive (forecasting, classification) and prescriptive (optimization, scenario simulation) are not built. Hypothesis testing and "causal inference flags" are not in the report either. Keep descriptive and basic diagnostic only. |
| 5 | Home — How It Works (`DataFlow.tsx`) | **Rewrite** | Describes self-serve upload, choosing an analysis type, and reusable Python code. Replace with the real flow: request → send your CSV → we run it → you get the report. |
| 6 | Home — price section | **Owner** | Decision D7. Not read, not edited. |
| 7 | Home — Feedback (`Feedback.tsx`) | **Hide** | Asks visitors to rate "your experience" of a product they cannot use, and the form only shows a thank-you without sending anything. |
| 8 | Home — closing CTA (`CTA.tsx`) | **Rewrite** | "Upload your files now and let our AI cleaner prepare your data for advanced analytics." No upload. |
| 9 | Home — signup card (`SignupForm.tsx`) | **Rewrite** | "Join the waitlist… be among the first to experience next-generation data cleaning." The beta is open now as a service; make this the report request. Form itself works after PR #64. |
| 10 | Navbar | **Keep** | After PR #65. "Get Started" scrolls to the signup card. |
| 11 | Footer | **Rewrite (small)** | Remove links to any page hidden below. Tagline is fine. |
| 12 | `/features` | **Rewrite** | Same six features as #2, with more detail that is untrue: p-values and confidence intervals, interactive HTML dashboards, secure sharing links, Excel export, "preferred choice for data professionals worldwide", "validated against… peer-reviewed methodologies", "enterprise security and compliance features". |
| 13 | `/documentation` | **Hide** | Quick start begins with "Sign in with Google"; API examples use a bearer API key and `curl` to `http://localhost:8000/upload` and `/clean`. None of it exists. Section links go nowhere. |
| 14 | `/guides` | **Hide** | The guides are not written ("Read Guide" does nothing). One teaches SAINT's "built-in regression models", which do not exist. "Written by industry experts." The email sign-up does nothing. |
| 15 | `/about` | **Rewrite — needs your facts** | See questions A1–A3. Names three team members with employer and degree claims, a 2023–2025 timeline, and stats: 10K+ active users, 50+ countries, 500M+ rows processed, 99.9% uptime. "Start Free Trial" button. |
| 16 | `/savvy-analytics` | **Hide or rewrite — needs your facts** | See question A4. Claims 50+ projects, 20+ enterprise clients, 95% retention, offices in eight cities, four service lines. "Try SAINT" and "Schedule a Consultation" buttons. |
| 17 | `/contact` | **Rewrite** | FAQ is untrue: "start using SAINT immediately after signing up", "CSV, Excel, JSON, and TSV", "export… as Python/Jupyter notebooks", "encrypted in transit and at rest". "Technical Questions: API documentation… developer support". Three email addresses and a Lisbon location to confirm (A5). Two bottom buttons do nothing. Form works after PR #64. |
| 18 | Not-found page | **Keep** | — |
| 19 | `index.html` title and description | **Rewrite** | "Python-first data cleaning and analytics platform". The social-preview image points at a Lovable placeholder hosted on lovable.dev. |
| 20 | `README.md` | **Rewrite** | Titled "SavvyCortex App". Lists `/upload`, `/clean`, `/analyze`, `/report/summary`, `/export` endpoints, natural-language queries, "ML-powered" cleaning, "Compliance Ready… GDPR/AI Act", and a Testimonials/API/Blog/Careers page list. Clone URL is a placeholder. Should describe the CLI and how to run it. |

## Questions only you can answer

- **A1 — About team.** Are Sarah Rodriguez, Marcus Chen and Elena Vasquez real people on the team? If not, the section is removed.
- **A2 — About stats.** Are 10K+ users, 50+ countries, 500M+ rows and 99.9% uptime real? If not, the stats block is removed.
- **A3 — About timeline.** Which of the 2023–2025 milestones are real?
- **A4 — Savvy Analytics page.** Are the consultancy's figures, offices and services accurate? If you can't confirm them this week, the page is hidden.
- **A5 — Contact details.** Do `support@`, `business@` and `developers@savvyanalytics.info` all receive mail, and is Lisbon the right location?
- **A6 — Excel.** Will you accept Excel files in the beta (converting to CSV yourself), or CSV only?

## Proposed order of work (one PR each)

1. Hide: Business Intelligence and Feedback sections, `/documentation`, `/guides` (and `/savvy-analytics` if A4 is "hide"); footer links to match.
2. Home rewrite: Hero, Key Features, Four Types of Analytics, How It Works, closing CTA, signup card, `index.html` metadata.
3. `/features` and `/contact` rewrite.
4. `/about` rewrite, once A1–A3 are answered.
5. README rewrite.

The new copy must stay consistent with the cleaning wording from Story 3.9 and say nothing about prices.
