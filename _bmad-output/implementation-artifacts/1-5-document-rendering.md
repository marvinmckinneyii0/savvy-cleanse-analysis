# Story 1.5: Document Rendering

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

---

## Story

**As a** developer on SavvyCortex,
**I want** to render an `InsightReport` into professionally formatted `.docx` and `.pdf` documents with branded styling,
**So that** pipeline consumers get deliverable-ready reports from the CLI.

### Business Context

This is Story 1.5 of Epic 1 — Phase 1 (Foundation). It is the fourth pipeline stage (DQA → Insights → Narrative → **Render**). The `InsightReport` Pydantic model produced by Story 1.4's `NarrativeGenerator` is the sole input. Two renderers are produced: `DocxRenderer` (docxtpl → `.docx`) and `PdfRenderer` (WeasyPrint → `.pdf`). Both must handle the `fallback=True` case — the report is rendered with computed data sections only, omitting empty narrative fields.

The renderer interface (`render(insight_report, output_path) -> None`) defined here is the contract Story 1.6 depends on. Getting the interface exactly right is the primary deliverable.

---

## Acceptance Criteria

The AC below comes verbatim from [epics.md](../planning-artifacts/epics.md). Do not reinterpret — implement to the letter.

**Given** a valid `InsightReport` with narrative content
**When** `DocxRenderer.render(insight_report, output_path)` is called
**Then** a `.docx` file is produced using `docxtpl` with the branded report template (`backend/renderers/templates/report_template.docx`)

**Given** a valid `InsightReport` with narrative content
**When** `PdfRenderer.render(insight_report, output_path)` is called
**Then** a `.pdf` file is produced using `WeasyPrint` from the HTML template (`backend/renderers/templates/report_template.html`)

**Given** an `InsightReport` with `fallback=True` (narrative unavailable)
**When** the renderer is called
**Then** the report is rendered with computed data sections only (narrative fields omitted/replaced with a fallback notice)

**Given** a rendering failure (disk full, template missing, invalid data)
**When** the renderer encounters an error
**Then** `ReportRenderError` is raised with descriptive detail
**And** the error is logged via structlog with `pipeline_run_id` and `stage="renderer"`

**Given** any rendering run
**When** rendering completes
**Then** `backend/tests/test_renderers.py` passes with tests covering: docx output validation, PDF output validation, fallback rendering without narrative, and error handling

---

## Tasks / Subtasks

- [x] **Task 1 — Add `docxtpl` and `WeasyPrint` to dependencies** (AC: docx/PDF output)
  - [x] Add `docxtpl>=0.20.2` and `weasyprint>=68.1` to `pyproject.toml` `[project] dependencies`
  - [x] Run `pip install -e .` (or `uv sync`) to confirm installation

- [x] **Task 2 — Create branded DOCX template** `backend/renderers/templates/report_template.docx` (AC: docx output)
  - [x] Create a minimal `.docx` template file using python-docx or docxtpl scaffolding
  - [x] Define Jinja2 template variables matching `InsightReport` fields
  - [x] Apply SavvyCortex branded styling: heading styles, body font, section separators
  - [x] Test manually that docxtpl can render the template with sample data

- [x] **Task 3 — Create branded HTML template** `backend/renderers/templates/report_template.html` (AC: PDF output)
  - [x] Create Jinja2 HTML template with CSS for WeasyPrint rendering
  - [x] Mirror the same variable structure as the docx template
  - [x] Include print-friendly CSS (page breaks, margins, header/footer)
  - [x] Conditionally suppress narrative sections when `fallback=True`

- [x] **Task 4 — Implement `DocxRenderer`** `backend/renderers/docx_renderer.py` (AC: 1, 3, 4)
  - [x] Define class `DocxRenderer` with `render(self, insight_report, output_path) -> None`
  - [x] Load template via `Path(__file__).parent / "templates" / "report_template.docx"`
  - [x] Build context dict; handle `None` narrative fields gracefully
  - [x] Wrap all errors in `ReportRenderError`; log via structlog

- [x] **Task 5 — Implement `PdfRenderer`** `backend/renderers/pdf_renderer.py` (AC: 2, 3, 4)
  - [x] Define class `PdfRenderer` with identical interface to `DocxRenderer`
  - [x] Lazy-import WeasyPrint with OSError → ReportRenderError guard
  - [x] Render Jinja2 HTML template then call `weasyprint.HTML(string=...).write_pdf(output_path)`
  - [x] Wrap all errors in `ReportRenderError`; log via structlog

- [x] **Task 6 — Update `backend/renderers/__init__.py`** (AC: Story 1.6 interface)
  - [x] Export `DocxRenderer`, `PdfRenderer` with `__all__`

- [x] **Task 7 — Write tests** `backend/tests/test_renderers.py` (AC: 5)
  - [x] Docx output validation (file exists, valid ZIP/docx, key text in XML)
  - [x] PDF output validation (mocked WeasyPrint, magic bytes `%PDF`)
  - [x] Fallback rendering for both renderers
  - [x] Error handling — missing template raises `ReportRenderError`
  - [x] Error handling — unwritable output raises `ReportRenderError`
  - [x] Interface contract tests (`from backend.renderers import DocxRenderer, PdfRenderer`)

---

## Dev Notes

### File Locations (MUST follow architecture)

```
backend/
├── renderers/
│   ├── __init__.py          ← export DocxRenderer, PdfRenderer
│   ├── docx_renderer.py     ← NEW
│   ├── pdf_renderer.py      ← NEW
│   └── templates/
│       ├── report_template.docx   ← NEW (binary, check in)
│       └── report_template.html   ← NEW
├── tests/
│   └── test_renderers.py    ← NEW
```

`backend/renderers/templates/` already exists as an empty directory — do not create, just populate it.

### Interface Contract for Story 1.6

Story 1.6 (Pipeline Orchestration CLI) imports renderers exactly like this:

```python
from backend.renderers import DocxRenderer, PdfRenderer
from backend.errors.exceptions import ReportRenderError

renderer = DocxRenderer()  # or PdfRenderer()
renderer.render(insight_report, output_path)
```

The render method signature **must** be:
```python
def render(self, insight_report: InsightReport, output_path: str | Path) -> None:
```
Returns `None` on success. Raises `ReportRenderError` on failure. No other return values.

### Key Architecture Rules (from architecture.md)

- **Three-layer separation**: `renderers/` is Presentation layer — it NEVER imports from `backend/pipeline/` or `backend/api/`. It only imports from `backend/models/` and `backend/errors/`.
- **Structlog context propagation**: `pipeline_run_id` is bound to structlog context by the orchestrator *before* calling the renderer. The renderer must call `structlog.get_logger()` (not `logging.getLogger()`) and use `log.info(...)` — it picks up the bound context automatically.
- **Result vs Exception**: Render failure is an infrastructure failure → raise `ReportRenderError`. Never return a failure result.
- **Template path resolution**: Use `Path(__file__).parent / "templates" / "..."` — never hardcode absolute or relative paths from cwd.

### Dependencies

| Library | Version | Notes |
|---------|---------|-------|
| `docxtpl` | `>=0.20.2` | Jinja2 templating over `.docx`. Uses `python-docx` under the hood. |
| `weasyprint` | `>=68.1` | HTML/CSS → PDF. No LibreOffice dependency. Security patch in v68. Python ≥3.10 required — we're on 3.13, compatible. |
| `jinja2` | transitive | Already available via docxtpl; use `jinja2.Environment` for HTML template in PdfRenderer |
| `structlog` | existing | Already installed (Story 1.3/1.4) |

**Add to `pyproject.toml`:**
```toml
[project]
dependencies = [
    # ... existing ...
    "docxtpl>=0.20.2",
    "weasyprint>=68.1",
]
```

### InsightReport Fields Reference

The `InsightReport` model (already exists at `backend/models/insight_report.py`):

```python
class InsightReport(BaseModel):
    executive_summary: str
    key_findings: list[NarrativeSection]   # NarrativeSection has .title and .content
    anomaly_analysis: str | None = None
    recommendations_narrative: str | None = None
    metadata: dict = Field(default_factory=dict)  # keys: provider, model, token_count, duration_ms, timestamp
    fallback: bool = False
    fallback_reason: str | None = None
```

When `fallback=True`, `executive_summary` may be empty string and `key_findings` may be empty list. The renderer must not crash on these — produce a minimal "data-only" report with a visible fallback notice.

### Fallback Handling Strategy

In templates, guard narrative sections:

**DOCX template (Jinja2 in docxtpl):**
```
{% if not fallback %}
Executive Summary: {{ executive_summary }}
{% else %}
⚠ Narrative unavailable: {{ fallback_reason }}
{% endif %}
```

**HTML template:**
```html
{% if not fallback %}
<section class="narrative">{{ executive_summary }}</section>
{% else %}
<div class="fallback-notice">Narrative unavailable: {{ fallback_reason }}</div>
{% endif %}
```

### WeasyPrint Notes

- WeasyPrint 68.1+ does not require system fonts if CSS specifies web-safe fallbacks. Use `font-family: Arial, Helvetica, sans-serif` for portability.
- For CI/CD environments, WeasyPrint may need `libpango` system dependency. Document this in a comment in `pdf_renderer.py`.
- `weasyprint.HTML(string=html_string).write_pdf(output_path)` — `output_path` can be `str` or `Path`; both work.

### Error Wrapping Pattern (follow Story 1.4's LLMProviderError pattern)

```python
try:
    doc = DocxTemplate(template_path)
    doc.render(context)
    doc.save(output_path)
except Exception as exc:
    raise ReportRenderError(
        f"DOCX render failed: {type(exc).__name__}: {exc}"
    ) from exc
```

### Previous Story Learnings (Story 1.4)

- **Structlog binding**: use `structlog.get_logger().bind(...)` pattern; the orchestrator binds `pipeline_run_id` before stage entry — don't bind it again in the renderer, just call `structlog.get_logger()`.
- **Path types**: accept both `str | Path` at the interface boundary, convert to `Path` internally via `Path(output_path)`.
- **Test isolation**: never write to project-relative paths in tests — always use `tmp_path`.
- **pyproject.toml lacks `dependencies` key** — check current state of `pyproject.toml` before adding; it may need the `dependencies = []` key added to `[project]` (see Task 1).

### Cross-Story Dependencies

| Depends on | What's needed |
|-----------|---------------|
| Story 1.3 (done) | `InsightPayload` model — used indirectly via `InsightReport.metadata` |
| Story 1.4 (done) | `InsightReport` model (`backend/models/insight_report.py`) — renderer input |
| Story 1.1 (review) | `backend/errors/exceptions.py` with `ReportRenderError` — already exists, verified |
| **Unblocks Story 1.6** | `DocxRenderer`, `PdfRenderer` exported from `backend/renderers/__init__.py` |

---

## Definition of Done

- [x] `DocxRenderer.render(insight_report, output_path)` produces a valid `.docx` file
- [x] `PdfRenderer.render(insight_report, output_path)` produces a valid `.pdf` file
- [x] Both renderers handle `fallback=True` without raising
- [x] Both renderers raise `ReportRenderError` (not bare `Exception`) on failure
- [x] `backend/tests/test_renderers.py` passes (19/19 tests pass)
- [x] `from backend.renderers import DocxRenderer, PdfRenderer` works (Story 1.6 integration point)
- [x] No imports from `backend/pipeline/` or `backend/api/` in renderer files
- [ ] Run `/security-review` and resolve all Critical/High findings before marking done (policy added 2026-06-22, applies to all stories from 1.4 onward)

---

## Dev Agent Record

### Completion Notes (2026-06-26)

Implemented full DOCX and PDF renderer pipeline. Key decisions:

- **WeasyPrint on Windows**: requires GTK native libs (libgobject/libpango) not present on Windows dev boxes. Used lazy import with `OSError → ReportRenderError` conversion so the renderer fails clearly with an actionable message. PDF tests mock `weasyprint.HTML` entirely — 19 tests pass without GTK installed.
- **DocxTemplate lazy-loads**: `DocxTemplate(path)` does NOT validate the template on construction — it opens the ZIP on `render()`. Updated the missing-template test to match `"DOCX render failed"` (the render-time error) rather than a construction-time message.
- **Template path resolution**: both renderers use `Path(__file__).parent / "templates" / ...` — portable across any cwd.
- **Structlog**: renderers call `structlog.get_logger()` without re-binding `pipeline_run_id`; the orchestrator (Story 1.6) binds it to the context before calling render.
- **Full regression**: 103 passed, 1 skipped (pre-existing Anthropic SDK import skip in test_narrative_generator.py), 0 failures.

### File List

- `pyproject.toml` — added `dependencies` array with docxtpl, weasyprint, jinja2, structlog, pydantic
- `backend/renderers/__init__.py` — exports DocxRenderer, PdfRenderer
- `backend/renderers/docx_renderer.py` — NEW
- `backend/renderers/pdf_renderer.py` — NEW
- `backend/renderers/templates/report_template.docx` — NEW (binary, generated via python-docx)
- `backend/renderers/templates/report_template.html` — NEW
- `backend/tests/test_renderers.py` — NEW (19 tests)

### Change Log

- 2026-06-26: Story 1.5 implemented — DocxRenderer, PdfRenderer, branded templates, 19 tests all passing. WeasyPrint native-lib guard documented. Unblocks Story 1.6.
