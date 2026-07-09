# Story 2.5: Monitoring Agent & Alert Delivery

Status: done

<!-- Numbering: epics.md "Story 2.4: Monitoring Agent & Alert Delivery" == filed 2.5 (renumbered
     per the Epic 2 reconciliation in 2-3-drift-engine.md). Final Epic 2 story. -->

## Story

As a developer,
I want a CLI agent that compares current metrics against the previous period, evaluates configurable
thresholds, and delivers structured alerts via log file and email,
so that anomalies are detected proactively and stakeholders are notified automatically.

## Acceptance Criteria

1. **Evaluate & alert.** Given a current dataset and an existing baseline (the previous period), when
   the user runs `python -m backend.agents.monitoring_agent evaluate --input current.csv`, then the
   agent obtains drift findings for the dataset (current vs baseline) and evaluates each configured
   `metric_thresholds` entry as a `mean_shift` rule; each breached threshold produces a Pydantic
   `AlertMessage` containing `alert_id`, `triggered_at`, `rule` (type + column + threshold), `finding`
   (actual_value + severity + detail), and `dataset`.

2. **Drift consumption (no side effects).** Given the evaluation, when drift is obtained, then the
   agent uses the Drift Engine's **pure** comparison (`compute_drift` against the loaded baseline) — it
   does **not** rotate or mutate the baseline (monitoring is read-only w.r.t. baselines; rotation is
   the Reporting Agent's pipeline concern). When no baseline exists for the dataset, there is no
   previous period to compare: the agent logs `monitoring_clean`, delivers no alerts, and exits 0.

3. **Dual delivery.** Given one or more breached thresholds, when alerts are generated, then each alert
   is written to a structured JSON file under `output/alerts/` (FR8), and all alerts are sent via email
   (SMTP, stdlib `smtplib`) to every recipient in `config.alert_recipients`; the email body includes
   alert severity, rule description, actual-vs-threshold values, and the dataset name; and a structlog
   entry `event="alert_triggered"` (with severity + rule details) is emitted per alert.

4. **Clean run.** Given no thresholds are breached, when evaluation completes, then a structlog entry
   `event="monitoring_clean"` is emitted, no alerts are delivered, and the agent exits 0.

5. **Threshold hot-reload.** Given `config.yaml` thresholds are modified between runs, when the agent
   runs again, then the updated thresholds are used (each run re-loads config via `PipelineConfig.load`),
   so a previously-alerting condition may no longer trigger under a looser threshold.

6. **SMTP failure isolation.** Given SMTP delivery fails (server unreachable / auth error), when the
   send fails, then the alert JSON file is still written (log delivery is independent of email), the
   SMTP failure is logged as a **warning** (`smtp_delivery_failed`) with error details, and the agent
   does not crash (exits 0 — the evaluation itself succeeded).

7. **Tests.** `backend/tests/test_monitoring_agent.py` passes with tests covering: single-threshold
   breach, multiple-threshold breach, no breach (clean), drift-based rule mapping, email delivery
   (mocked SMTP), SMTP failure → log-only fallback, and a threshold config change altering the outcome.

## Tasks / Subtasks

- [ ] **Task 0 — Verify assumptions against the current tree** (all ACs)
  - [ ] Confirm `backend/agents/monitoring_agent.py` and `backend/models/alert.py` do **not** exist;
        `backend/agents/reporting_agent.py` (2.4) does.
  - [ ] Confirm `DriftEngine` (2.3) exposes `compute_drift(current_df, baseline_profile, pipeline_run_id="")`
        (pure) and can load a baseline. If no public baseline loader exists, add a thin public
        `load_baseline(dataset_key) -> BaselineProfile | None` wrapping `_load_baseline` (additive; does
        not modify existing behaviour). Numeric findings live on `DriftReport.numeric_drift[].mean_shift`
        with `actual_value` = signed relative change and `severity` (Severity enum).
  - [ ] Confirm `PipelineConfig` exposes `metric_thresholds.thresholds: dict[str, float]` (+ `.get`),
        `alert_recipients.recipients: list[EmailStr]`, and `smtp` (`host`, `port`, `username`,
        `password`, `from_address`, sourced from env). Confirm `Severity` is in `models/quality_report.py`.
  - [ ] Confirm `smtplib` (stdlib) — no new third-party dependency is required.

- [ ] **Task 1 — Alert models** `backend/models/alert.py` (AC: 1) — match architecture.md §469-477.
  - [ ] `AlertRule(BaseModel)`: `type: str` (e.g. `"mean_shift"`), `column: str`, `threshold: float`.
  - [ ] `AlertFinding(BaseModel)`: `actual_value: float`, `severity: Severity` (reuse the enum),
        `detail: str`.
  - [ ] `AlertMessage(BaseModel)`: `alert_id: str`, `triggered_at: str` (ISO 8601 UTC),
        `rule: AlertRule`, `finding: AlertFinding`, `dataset: str`.
  - [ ] Match existing Pydantic style (`from __future__ import annotations`, module docstring,
        PascalCase models, snake_case fields).

- [ ] **Task 2 — Threshold evaluation** `backend/agents/monitoring_agent.py` (AC: 1, 2, 4, 5)
  - [ ] `_evaluate(drift_report, thresholds, dataset) -> list[AlertMessage]`: for each `(column,
        threshold)` in `thresholds`, find that column's `mean_shift` finding in
        `drift_report.numeric_drift`; if present and `abs(actual_value) > threshold`, emit an
        `AlertMessage` (`rule.type="mean_shift"`, `finding` from the drift finding). Pure function —
        no I/O — so it is unit-testable. **Note (documented limitation):** the Drift Engine only emits
        a `mean_shift` finding above its fixed LOW band (>5%), so a configured threshold below 5% cannot
        trigger via drift consumption; the default thresholds (±15/20%) are well above this.
  - [ ] `_load_drift(config-independent inputs) -> DriftReport | None`: derive `dataset_key` (reuse the
        Reporting Agent's `_dataset_key_from_path` — import it, do not duplicate), load the baseline via
        `DriftEngine`; return `None` if no baseline (first period). Use `compute_drift` (pure) — never
        `run` (no rotation).
  - [ ] `evaluate` Typer command: `configure_logging()`, load config (hot-reload), read CSV, obtain
        drift, evaluate thresholds. On no baseline or empty alert list → log `monitoring_clean`, exit 0.

- [ ] **Task 3 — Alert delivery** `backend/agents/monitoring_agent.py` (AC: 3, 6)
  - [ ] `_write_alert_log(alerts, output_dir) -> Path`: write the alerts as a structured JSON file under
        `{output_dir}/alerts/` (e.g. `{dataset}_{UTC-timestamp}.json`, a JSON array of
        `AlertMessage.model_dump()`); create the directory if needed. This always happens first.
  - [ ] `_send_email(alerts, config) -> None`: build a plain-text body (per-alert: severity, rule
        description, actual vs threshold, dataset) and send via `smtplib.SMTP` to
        `config.alert_recipients.recipients` using `config.smtp`. If recipients or SMTP host are not
        configured, skip email with an info log (not a failure). Wrap the send in try/except: on any
        exception log `smtp_delivery_failed` (warning, with error type/detail) and return — the agent
        must not crash and the JSON log is already written.
  - [ ] Emit `alert_triggered` (severity + rule) per alert. Order: write log file → emit per-alert
        structlog → attempt email. Exit 0.
  - [ ] Thin agent: threshold rule-evaluation and delivery only; no analytical computation (drift is
        the engine's). No LLM calls.

- [ ] **Task 4 — Tests** `backend/tests/test_monitoring_agent.py` (AC: 7)
  - [ ] `_evaluate` unit tests: single breach, multiple breaches, no breach — construct minimal
        `DriftReport`s with `NumericColumnDrift.mean_shift` findings at chosen `actual_value`s and assert
        the emitted `AlertMessage`s (rule/finding/dataset) and counts.
  - [ ] Drift-based rule mapping: a `mean_shift` of 0.32 on `revenue` with threshold 0.15 → one alert
        with `rule.type=="mean_shift"`, `rule.column=="revenue"`, `finding.actual_value==0.32`.
  - [ ] End-to-end `evaluate` via `typer.testing.CliRunner`: tiny current CSV in `tmp_path`, a seeded
        baseline (revenue ~40% lower → breach) in a `tmp_path` baseline dir, config in `tmp_path`;
        monkeypatch `smtplib.SMTP`; assert an alert JSON file is written under `output/alerts/` and
        `SMTP.sendmail` was called; exit code 0.
  - [ ] No-breach clean run: current == baseline distribution → no alerts, `monitoring_clean` logged,
        exit 0, no alert file.
  - [ ] SMTP failure fallback: monkeypatch `smtplib.SMTP` to raise on connect/send; assert the alert
        JSON file is still written, `smtp_delivery_failed` warning logged, exit 0.
  - [ ] Threshold config change: same data, run with threshold 0.15 (breach) then 0.50 (no breach) —
        assert the outcome flips (hot-reload).
  - [ ] All writes scoped to `tmp_path`; SMTP always mocked (never a real send). Run
        `uv run pytest backend/tests/ --ignore=backend/tests/test_parse_file.py` — confirm zero
        regressions vs. the Story 2.4 baseline (165 passed, 1 pre-existing skip) plus new tests.

## Dev Notes

### Architecture compliance
- `backend/agents/monitoring_agent.py` is Presentation layer (arch §745, §751, §807 — SMTP lives here).
  It may import `pipeline/`, `models/`, `config`, `core/`, stdlib `smtplib`; pipeline stages never
  import from `agents/`.
- **Consumes drift, decides materiality** (arch §199, §203, §221): the Drift Engine computes and
  "doesn't decide whether a change matters" — the Monitoring Agent applies `metric_thresholds` to the
  drift findings to make that decision. This keeps the agent thin (rule evaluation, not analytics).
- **Read-only on baselines:** use `DriftEngine.compute_drift` (pure), never `run` — monitoring must not
  rotate/mutate baselines (that is the Reporting Agent's pipeline concern, 2.4).
- **Result-vs-Exception:** a breached threshold is an expected outcome carried as an `AlertMessage`
  (never raised). SMTP failure is caught and downgraded to a warning (delivery is best-effort; the JSON
  log is the durable record). Corrupt baseline still raises `DriftComputationError` from the engine.
- **AlertMessage shape** is fixed by architecture.md §469-477 (alert_id / triggered_at / rule / finding
  / dataset).
- LLM only via `backend.core.llm_client` — the monitoring agent makes no LLM calls (grep gate must pass).
- No new dependency (smtplib is stdlib). Do not add scipy/sklearn (Phase-12 constraint).

### Existing code (verify against tree during Task 0)
- `backend/pipeline/drift_engine.py` (2.3): `DriftEngine`, `compute_drift`, `_load_baseline`,
  `_SAFE_DATASET_KEY`; `DriftReport.numeric_drift[].mean_shift` carries `actual_value`/`severity`.
- `backend/agents/reporting_agent.py` (2.4): `_dataset_key_from_path` (reuse for the same key derivation).
- `backend/models/pipeline_config.py` (2.1): `metric_thresholds`, `alert_recipients`, `smtp`.
- `backend/models/quality_report.py`: `Severity` enum (reuse for `AlertFinding.severity`).

### Testing standards
- Tests in `backend/tests/`; `structlog.testing.capture_logs()` for `alert_triggered`/`monitoring_clean`/
  `smtp_delivery_failed`; `tmp_path` for all writes; mock `smtplib.SMTP` (never send). `uv` only.
- Regression baseline: 165 passed, 1 pre-existing skip (`test_parse_file.py` excluded — pre-existing
  fastapi gap; fastapi is not a pyproject dep).

### References
- [Source: epics.md#Story 2.4: Monitoring Agent & Alert Delivery] (AC source; filed as 2.5)
- [Source: architecture.md#L199,L221] (Monitoring Agent consumes drift JSON for alert rules)
- [Source: architecture.md#L469-L477] (AlertMessage JSON shape)
- [Source: architecture.md#L602,L607,L807] (models/alert.py, monitoring_agent.py, SMTP location)
- [Source: backend/pipeline/drift_engine.py] (compute_drift — pure; reuse, no rotation)
- [Source: backend/agents/reporting_agent.py] (_dataset_key_from_path — reuse)
- [Source: backend/models/pipeline_config.py] (metric_thresholds / alert_recipients / smtp)

## Dev Agent Record

### Agent Model Used

claude-opus-4-8 (Epic 2 build loop, 2026-07-09).

### Debug Log References

- New tests: `uv run pytest backend/tests/test_monitoring_agent.py` → 16 passed.
- Full regression: `uv run pytest backend/tests/ --ignore=backend/tests/test_parse_file.py`
  → 181 passed, 1 skipped (pre-existing `anthropic`-missing skip), 0 regressions
  (Story 2.4 baseline was 165 passed; +16 new monitoring tests).
- `test_parse_file.py` excluded as before (imports `fastapi`, not a `pyproject.toml`
  dep; pre-existing collection gap, unrelated to this story).
- Gates: LLM grep gate PASS (agent makes no LLM calls); no scipy/sklearn added.
- Security review (branch diff): 0 HIGH / 0 MEDIUM findings. Alert-log filename is
  built from the sanitized `_dataset_key_from_path` stem (no traversal); baseline
  load is json+Pydantic only; SMTP creds env-sourced; email body via
  `EmailMessage.set_content` with a fixed Subject (no header injection).

### Completion Notes List

- All 7 ACs met.
- **Task 0 additive change:** added a public `DriftEngine.load_baseline(dataset_key)`
  thin wrapper over the private `_load_baseline`, so the Monitoring Agent can run a
  pure `compute_drift` against the persisted baseline without any of `run`'s
  rotation/persistence side effects (AC2 read-only-on-baselines). No existing
  behaviour changed.
- `_evaluate` is a pure, I/O-free function mapping breached `metric_thresholds`
  onto `AlertMessage`s via each column's `mean_shift` drift finding — directly
  unit-tested (single/multiple/no breach, negative-magnitude breach, absent-column
  skip, drift-based rule mapping).
- Delivery order per AC3/AC6: durable JSON alert log written FIRST, then per-alert
  `alert_triggered` structlog, then best-effort email. SMTP failure is caught,
  downgraded to an `smtp_delivery_failed` warning, and never crashes the agent
  (the JSON log is already on disk); exit 0.
- **Typer single-command note:** added a no-op `@app.callback()` so Typer keeps
  `evaluate` as an explicit subcommand — a single-command Typer app would otherwise
  drop the verb, breaking the AC-1 `... monitoring_agent evaluate --input` form.
- Documented limitation (from Task 2, retained): the Drift Engine only emits a
  `mean_shift` finding above its fixed LOW band (>5%), so a configured threshold
  below 5% cannot trigger via drift consumption; the default thresholds (±15/20%)
  sit well above this floor.
- `_dataset_key_from_path` reused from the Reporting Agent (imported, not duplicated);
  no rotation path invoked; no new third-party dependency (smtplib is stdlib).

### File List

- `backend/models/alert.py` (new) — `AlertRule`, `AlertFinding`, `AlertMessage`.
- `backend/agents/monitoring_agent.py` (new) — Typer `evaluate` command, `_evaluate`,
  `_load_drift`, `_write_alert_log`, `_build_email_body`, `_send_email`, `_read_csv`.
- `backend/pipeline/drift_engine.py` (modified) — additive public `load_baseline`.
- `backend/tests/test_monitoring_agent.py` (new) — 16 tests.
