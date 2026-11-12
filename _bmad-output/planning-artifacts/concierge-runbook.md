# SAINT Concierge Runbook (Beta)

How to take one customer request from the website form to a delivered report and a deleted file. Written 2026-11-10 for the concierge beta. Commands are for PowerShell on Windows, run from the repository root.

The data rules come from launch decision D6 (issue #62): CSV only, 100 MB maximum, sent by shared link, deleted 7 days after the report is delivered, and no health records, financial account data or government IDs.

## What was tested, and what was not

Tested on 2026-11-10 with the sample files in `backend/tests/e2e/sample_data/`:

- A Word report with `--no-clean`, with no cleaning flag, and with `--clean --cleaned-output`.
- The halt on a file with a critical data problem.
- The two `--cleaned-output` errors described in step 4.
- The PDF failure when the native libraries are missing.

Not tested:

- **A report with an LLM-written narrative.** Every test run used the fallback narrative, because no API key was available. Do the check in "One-time setup" before taking a real request.
- PDF output on a machine that has the native libraries.
- A file near 100 MB. The sample files are 60 rows.
- Anything in steps 1, 2, 6 and 7. Those are manual steps and have never been run.

## One-time setup

1. Confirm the main checkout includes merged PR #70 (LLM libraries and `.env` loading). Do not use a stale checkout.
2. Install the Python dependencies:

   ```powershell
   uv sync --dev
   ```

3. Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY`. `.env` is ignored by git; never commit it.
4. Create a jobs folder **outside the repository**, for example `C:\saint-jobs`. Customer files must never be saved inside the repository.
5. Prove the LLM narrative works. Run:

   ```powershell
   uv run python -m backend.pipeline.orchestrator --input backend/tests/e2e/sample_data/clean_sales.csv --output C:\saint-jobs\setup-check.docx --no-clean
   ```

   The last log line must contain `"fallback_narrative": false`. If it says `true`, the lines above it name each provider and its `error_type`; fix that before going further.
6. For the Friday agency beta, **deliver Word (.docx) only** as the guaranteed format. `--format pdf` remains a separate optional CLI path and must not be offered until a supported runtime completes a real PDF smoke test.

## Per request

Use one folder per request, named by date and a short customer name: `C:\saint-jobs\2026-11-13-acme\`. Everything for that customer goes in it and nothing goes anywhere else.

### 1. Take the request

A form submission arrives by email from Formspree. Reply to the customer and ask for:

- A link to their CSV (Google Drive, Dropbox or OneDrive). No email attachments.
- Whether they want cleaning. If yes, how gaps should be filled (see step 3), or "leave gaps as they are".
- Word (.docx) for the November 13 beta. Do not promise PDF unless the machine and exact output have been separately tested and the customer is explicitly informed.

For the free Agency Diagnostic, confirm a **limited quality snapshot only** (no full report or cleaning) and the sample scope before accepting data. For the $249 Single Client Report or five-for-$999 Founding Agency Bundle, confirm the agency has authority to share each client's data, the exact scope, price, invoice details and payment instructions **in writing before accepting commissioned work**. There is no website checkout or automatic renewal. Use only an owner-approved invoicing provider; this runbook does not create or send invoices.

Tell them in the same reply: CSV only, 100 MB maximum, and do not send health records, financial account data or government IDs.

### 2. Receive and check the file

1. Download the file into the job folder as `input.csv`.
2. Check the size:

   ```powershell
   (Get-Item C:\saint-jobs\2026-11-13-acme\input.csv).Length / 1MB
   ```

   Over 100: stop, and ask for a smaller file.
3. Look at the column headers only:

   ```powershell
   Get-Content C:\saint-jobs\2026-11-13-acme\input.csv -TotalCount 1
   ```

   If any header suggests data you do not accept (for example `ssn`, `passport`, `diagnosis`, `patient`, `iban`, `card_number`, `account_number`), do not run it. Delete the file (step 7) and tell the customer why.

### 3. If the customer wants cleaning, set how gaps are filled

With `--clean` and no settings, SAINT fills missing values by default: numbers with the column's median, categories with the most common value, dates by carrying the previous value forward. Do not let that happen by accident. Confirm the customer's choice first.

Choices are set in the `cleaning` section of `config.yaml` (a commented example is in the file). Accepted methods: `mean`, `median`, `mode`, `forward_fill`, `leave_as_is`. Per-column settings override per-type settings.

`config.yaml` is shared by every run. After the job, put it back the way it was:

```powershell
git checkout -- config.yaml
```

Never set `enabled: true` there. Turn cleaning on per run with `--clean`.

### 4. Run SAINT

Without cleaning:

```powershell
uv run python -m backend.pipeline.orchestrator --input C:\saint-jobs\2026-11-13-acme\input.csv --output C:\saint-jobs\2026-11-13-acme\report.docx --no-clean
```

With cleaning, also writing the cleaned CSV:

```powershell
uv run python -m backend.pipeline.orchestrator --input C:\saint-jobs\2026-11-13-acme\input.csv --output C:\saint-jobs\2026-11-13-acme\report.docx --clean --cleaned-output C:\saint-jobs\2026-11-13-acme\cleaned.csv
```

**PDF is excluded from the Friday beta's guaranteed deliverables.** It remains a CLI option only; enable it for customer delivery after verifying the runtime and updating customer-facing terms.

The run prints one JSON log line per step, then one plain final line. Read the final line:

| Final line | Meaning | What to do |
|---|---|---|
| `Pipeline complete \| ... status=success` | The report was written. | Go to step 5. |
| `Pipeline halted \| ... reason=Critical findings: ...` | The data has a critical problem, for example a column that is mostly empty. **No report was written.** | Tell the customer the reason in plain words and ask whether they can fix or drop that column. There is no option to force a report. |
| `Error: Cleaned export requested but cleaning is disabled.` | `--cleaned-output` was used without `--clean`. | Add `--clean`, or drop `--cleaned-output`. |
| `Error: Cleaned output already exists: ...` | A cleaned file from an earlier run is in the way. | Add `--overwrite-cleaned-output`. |
| `Error: PDF render failed ...` | The PDF libraries are missing. No report was written. | Rerun with Word output, or install GTK. |

The original `input.csv` is never changed. Cleaning works on a copy.

### 5. Check the report before sending

1. In the log, find the line with `"event": "pipeline_completed"`. It must say `"fallback_narrative": false`. If it says `true`, the narrative was not written by the LLM. **Do not send it.** Fix the cause and rerun.
2. Open the report and read it through. Check that:
   - the figures quoted in the narrative match the tables;
   - nothing in it refers to another customer;
   - if cleaning ran, the section headed "Data Cleaning" lists the changes, and the changes match what the customer asked for;
   - if there is a section headed "Requires Your Review", you have read it. It lists findings SAINT left unchanged for the customer to decide. It appears only when there are such findings, so a report without it is not broken.

This check is your own quality step. The website does not promise it to customers.

### 6. Deliver

Reply on the same email thread with the report attached. Attach `cleaned.csv` too if cleaning ran. Note the delivery date: the deletion deadline is 7 days later.

### 7. Delete the customer's data

Within 7 days of delivery, remove every copy:

1. The job folder (`input.csv`, `cleaned.csv`, the report).
2. The downloaded copy in your Downloads folder, if you saved it there first.
3. The Recycle Bin.
4. Any copy you made in your own cloud storage.
5. The email attachments you sent, if your retention answer to customers covers them.

SAINT itself keeps nothing between runs. The CLI writes only the files you name, stores no baseline, and prints its log to the screen without saving it. The log can contain column names, so do not paste it anywhere public.

Keep a simple register outside the repository with one line per job: customer, date received, date delivered, date deleted. It is your proof that the 7-day promise was kept.

## Open points

- **Invoice execution.** The business must select and verify an invoicing account, recipient routing and payment reconciliation before taking paid agency orders. No such account was provisioned by this documentation change.
- **What "the file" covers. The site says the customer's file is deleted after 7 days. Decide whether the report and the cleaned CSV are deleted on the same day, and say so in the privacy policy. Step 7 assumes they are.
- **Halted runs.** A customer with a badly broken file gets no report today. Decide what you offer them.
- **Speed without a key.** If no provider key works, a run spends about 20 seconds retrying before it falls back.
- **Model names.** The code calls fixed model versions. If one has been retired, step 5 of the setup will show it as a provider error.
