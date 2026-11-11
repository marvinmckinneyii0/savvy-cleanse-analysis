# SAINT Data Source Roadmap

**Written:** 2026-11-11 · **Status:** proposed order for owner review. It does not change `sprint-status.yaml`, and no item is scheduled.

Order: **CSV (now) → Excel → JSON → API connections → documents and RAG.**

Each step reuses what the previous one built, and the risk rises down the list. The public "Data Sources Roadmap" section on the home page (`src/lib/dataSources.ts`) shows the same order without dates.

| # | Source | Status | What exists today | What it needs |
|---|---|---|---|---|
| 1 | CSV | **Available** | The CLI reads CSV with `pd.read_csv` (`backend/pipeline/orchestrator.py`). The whole pipeline (quality checks, cleaning, insights, report) runs on it. | Nothing. |
| 2 | Excel (`.xlsx`, `.xlsm`) | Next | A server-side reader exists: `backend/api/parse_file.py` (openpyxl) handles `.xlsx`/`.xlsm` and rejects legacy `.xls`. It reports formulas and unsupported cell types per cell. | A step that turns the parsed rows into the same DataFrame the CSV path produces, a `--input` that accepts `.xlsx`, sheet choice when a workbook has several, and tests. Legacy `.xls` stays out. |
| 3 | JSON | Planned | Nothing. | Accept table-shaped JSON (an array of flat objects) first. Nested JSON needs a flattening rule and a quality finding when flattening loses structure. Same size limits as CSV. |
| 4 | API connections | Planned | Nothing. | Accounts and per-customer credential storage (Epic 4, story 4.1), secure secret handling and tenant isolation (Epic 6), scheduled pulls (the reporting agent from Epic 2 already schedules runs), and rate-limit and failure handling per connector. Start with one connector chosen from customer demand. |
| 5 | Documents and RAG | Later | `backend/core/extraction_client.py` is an interface specification only. It requires per-field confidence scores because extraction errors look like valid data. | The evaluation harness (Epic 11) to measure extraction accuracy, an extraction provider that meets the confidence-score contract, the planned `extraction_fidelity` quality category, then retrieval and question answering on top. |

## Why this order

1. **Excel before JSON.** The reader is already written and tested, and spreadsheets are what small-business customers have. It is mostly wiring.
2. **JSON before APIs.** Most APIs return JSON. Solving "turn JSON into a table and check its quality" first means a connector only has to fetch data, not also interpret it.
3. **APIs after accounts.** A connection stores a customer's credentials and runs without them present. That needs accounts, secret storage and tenant isolation, which arrive with the web app (Epics 4 and 6). Building connectors earlier would mean storing credentials with no safe place to keep them.
4. **RAG last.** Every earlier source has detectable failures: a bad file fails quality checks. Document extraction can produce clean-looking data that is wrong. The project's own rule is to block it until the evaluation harness can measure that.

## Interest list and reservations

The home page now collects interest in items 2–5 and the self-serve app (Formspree, `source: interest`). Use the counts to pick the first API connector and to decide whether JSON or Excel demand changes the order.

A "Reserve Your Spot" deposit option appears once `VITE_STRIPE_PAYMENT_LINK` is set to a Stripe Payment Link (refundable deposit, owner decision 2026-11-11). Reservations are for the self-serve version, so they are a commitment to items 4 and the web app.

## Open questions for the owner

- Which tools do early customers most want connected first?
- Should the reservation deposit apply to a first bill when the self-serve version launches, or only be refunded?
- When does the self-serve web app (Epic 4) start, so reserved customers can be told what they are waiting for?
