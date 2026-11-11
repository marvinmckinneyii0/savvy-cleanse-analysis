# SAINT

SAINT (Savvy Analytics Intelligence) turns a CSV file into a written data-quality report. It checks the data for problems, optionally cleans a working copy, computes insights, and renders a Word or PDF report with findings and recommendations.

SAINT is made by Savvy Analytics. It was previously called SavvyCortex and SavvyClean; some file and class names still use the old names.

## Status: concierge beta

Today SAINT is a command-line pipeline that a person runs. During the beta, a customer requests a report on the website, sends a CSV, and receives the report by email.

**What works**

- Data-quality assessment: missing values, duplicates, outliers, and type or format problems, each rated by severity.
- Optional cleaning on a working copy, with every change recorded in the report. Off by default.
- Insights: per-column summary statistics, trends over time, segment comparisons, unusual values, and recommendations.
- A written narrative produced by an LLM from the computed numbers. The LLM never computes numbers.
- Reports in Word (`.docx`) or PDF, and an optional export of the cleaned CSV.
- A marketing website with contact and report-request forms.

**What does not exist yet**

- Self-serve upload, accounts, or sign-in.
- A dashboard, or charts in reports.
- Notebook or Python code export.
- Forecasting, optimization, or natural-language queries.
- A public API. The FastAPI app in `backend/api/` serves only a health check and a file-parsing endpoint.
- Input formats other than CSV for the report pipeline.

## Requirements

- Python 3.13 or later and [uv](https://docs.astral.sh/uv/)
- Node.js 22 and npm (for the website only)
- For PDF output: the native libraries WeasyPrint needs (the GTK runtime on Windows; Pango and GObject on Linux or macOS). Word output needs nothing extra.

## Generate a report

Install the Python dependencies once:

```bash
uv sync --dev
```

Run the pipeline on a CSV. This writes a Word report and leaves the data untouched:

```bash
uv run python -m backend.pipeline.orchestrator --input backend/tests/e2e/sample_data/clean_sales.csv --output report.docx
```

Options:

| Option | Meaning |
|---|---|
| `--input PATH` | The CSV file to analyze. Required. |
| `--output PATH` | Where to write the report. Required. |
| `--format docx\|pdf` | Report format. Default `docx`. |
| `--clean` / `--no-clean` | Turn cleaning on or off for this run. Without either, the `cleaning.enabled` value in `config.yaml` decides; if that section is absent, cleaning is off. |
| `--cleaned-output PATH` | Also write the cleaned working copy to this CSV. Requires cleaning to be on. |
| `--overwrite-cleaned-output` | Allow `--cleaned-output` to replace an existing file. |

Run with `--help` to see the full text, including the available missing-value methods.

A report with cleaning and the cleaned data:

```bash
uv run python -m backend.pipeline.orchestrator --input data.csv --output report.docx --clean --cleaned-output data_cleaned.csv
```

### Things to know before you run it

- **The LLM narrative needs an API key.** Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY`. The code tries Anthropic, then OpenAI (`OPENAI_API_KEY`), then Google (`GEMINI_API_KEY`). With no working key the pipeline still completes, but the report uses a plain fallback narrative. Check the last log line: `"fallback_narrative": false` means the LLM wrote it.
- **Critical data problems stop the run.** If the quality check finds a critical problem (for example, a column that is 60% empty), the pipeline halts, prints the reason, exits with an error, and writes no report.
- **PDF needs native libraries.** Without them, `--format pdf` fails with a clear error and no report is written. Use `docx` or install the libraries listed under Requirements.
- **Your input file is never modified.** Cleaning works on a copy.

### Cleaning

Cleaning is optional and off by default. When enabled, SAINT applies only supported, deterministic changes to a working copy, keeps the original input unchanged, and records every action in the report's Healing Manifest. Findings that need human judgment are listed and left unchanged.

How missing values are filled is set in the `cleaning` section of `config.yaml`; the commented example there lists the accepted methods.

## Website

The site is a React, Vite and TypeScript app in `src/`.

```bash
npm ci
```

```bash
npm run dev
```

The dev server runs at http://localhost:8080.

The contact and report-request forms post to [Formspree](https://formspree.io). Set `VITE_FORMSPREE_FORM_ID` in `.env` to your form's ID. Without it, both forms show an error that points visitors to the support email.

To build for production:

```bash
npm run build
```

The static site is written to `dist/`.

## Tests

```bash
uv run pytest
```

```bash
npm test
```

CI runs both, plus the production build, on every pull request.

## Repository layout

```
backend/
  pipeline/     orchestrator (CLI entry point), data quality, cleaning, insights, narrative, drift
  rules/        cleaning policy and the opt-in gate
  models/       Pydantic models passed between pipeline stages
  renderers/    Word and PDF report rendering
  agents/       scheduled reporting and monitoring
  core/         LLM client and logging
  api/          minimal FastAPI app (health check and file parsing)
  tests/        pytest suite, including end-to-end CLI tests and sample data
src/            website (React, Vite, TypeScript, Tailwind, shadcn/ui)
config.yaml     thresholds, schedules and cleaning settings
_bmad-output/   product requirements, architecture, story specs and sprint status
agent-system/   tooling for the AI-assisted development workflow
```

Some older modules in `backend/` (`main.py`, `main_enhanced.py`, `cleaner.py`, `advanced_pipeline.py`, `analytics.py`, `comprehensive_analytics.py`, `nlp_processor.py`, `dashboard_api.py`) are legacy reference code. New code must not import them.

Contributor rules are in `AGENTS.md`. Sprint status lives in `_bmad-output/implementation-artifacts/sprint-status.yaml`.

## License

© 2025 Savvy Analytics LLC. All rights reserved.

## Contact

Savvy Analytics: [savvyanalytics.co](https://www.savvyanalytics.co) · info@savvyanalytics.co
