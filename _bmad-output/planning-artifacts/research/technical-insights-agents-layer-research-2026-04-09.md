---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'Insights & Agents Layer Architecture for SavvyCleanse ETL'
research_goals: 'Full-stack architecture and technology evaluation for Data Quality Assessment, Insight Report (branded docx/PDF), Reporting Agent, and Monitoring Agent layers on existing FastAPI/pandas ETL pipeline'
user_name: 'Marvin'
date: '2026-04-09'
web_research_enabled: true
source_verification: true
---

# Research Report: Technical

**Date:** 2026-04-09
**Author:** Marvin
**Research Type:** Technical

---

## Research Overview

This technical research investigates the architecture, technology stack, integration patterns, and implementation approach for building an **Insights & Agents layer** on top of the existing SavvyCleanse ETL pipeline. The system must accept structured datasets, run automated data quality assessment, compute analytics, generate LLM-grounded narrative reports, and output professionally branded docx/PDF deliverables — all from scratch-built Python agents with no orchestration frameworks.

Research was conducted across six phases: scope confirmation, technology stack analysis (with web-verified library evaluation), integration patterns (pipeline composition and code reuse assessment), architectural patterns (system design, error handling, project structure), implementation research (phased roadmap, testing strategy, cost analysis), and this final synthesis. All technical claims are verified against current (2025-2026) public sources with citations throughout.

**Key finding:** The existing codebase provides ~50% reusable foundation. Four new lightweight dependencies (pandera, docxtpl, typer, structlog) plus Claude API Structured Outputs fill all remaining capability gaps. The full system is achievable in 4-5 weeks using a vertical-slice phased approach, with LLM costs under $0.06 per report. See the Executive Summary below for the complete strategic assessment.

---

## Technical Research Scope Confirmation

**Research Topic:** Insights & Agents Layer Architecture for SavvyCleanse ETL
**Research Goals:** Full-stack architecture and technology evaluation for Data Quality Assessment, Insight Report (branded docx/PDF), Reporting Agent, and Monitoring Agent layers on existing FastAPI/pandas ETL pipeline

**Key Design Constraint:** Non-agentic infrastructure. Only implement agents (Reporting Agent, Monitoring Agent) as lightweight scripts — no orchestration frameworks unless proven necessary.

**Technical Research Scope:**

- Architecture Analysis — pipeline orchestration, stage contracts, layer composition on existing codebase
- Implementation Approaches — pipeline stage design, JSON schemas, LLM grounding patterns, threshold monitoring
- Technology Stack — branded docx/PDF generation, LLM integration, alerting patterns
- Integration Patterns — mapping to existing FastAPI/pandas/Supabase stack, CLI entry points
- Performance Considerations — halt-on-critical logic, LLM token efficiency, demo readiness

**Research Methodology:**

- Current web data with rigorous source verification
- Multi-source validation for critical technical claims
- Confidence level framework for uncertain information
- Comprehensive technical coverage with architecture-specific insights

**Scope Confirmed:** 2026-04-09

---

## Technology Stack Analysis

### Data Quality Assessment Libraries

The existing `advanced_pipeline.py` already provides data profiling (missing %, duplicates, outliers, quality score). The question is whether to extend it natively or adopt a validation framework.

**Option A: Pandera (Recommended for this project)**
- Lightweight, pandas-native schema validation with statistical property checks
- Define column-level expectations (nulls, types, value ranges, cardinality) as declarative schemas
- Returns structured validation results that map directly to the JSON quality report spec
- Low overhead: single `pip install pandera` — no infrastructure dependencies
- Active development; v0.19+ supports pandas 2.x natively
- *Confidence: HIGH* — Well-matched to project scope and existing pandas stack
- _Source: [Pandera SciPy Proceedings](https://proceedings.scipy.org/articles/gerudo-f2bc6f59-010), [Pandera on DZone](https://dzone.com/articles/pandera-open-source-data-validation-framework)_

**Option B: Great Expectations**
- More comprehensive but significantly heavier (data docs, expectation stores, checkpoints)
- Overkill for a single-pipeline CLI tool — designed for enterprise data platforms
- 45s per million rows performance, 2.5GB memory peak
- _Source: [Great Expectations Testing Suites](https://johal.in/data-quality-frameworks-great-expectations-testing-suites-in-python-for-reliable-2025-ingestion/)_

**Option C: Custom pandas-only (Viable fallback)**
- Extend existing `DataProfile` dataclass in `advanced_pipeline.py` with additional checks
- Zero new dependencies; full control over JSON output schema
- Risk: reinventing validation logic that Pandera already handles well

**Recommendation:** Pandera for schema validation + extend existing `DataProfile` for statistical red flags (zero variance, extreme cardinality, suspicious distributions). This hybrid approach gets the structured validation report without framework weight, and the existing quality scoring logic stays intact.

### Report Generation: Branded docx & PDF

**For docx output (Primary — Recommended):**

**docxtpl (python-docx-template) v0.20.x**
- Jinja2 templating directly inside .docx files — design the template in Microsoft Word with logos, headers/footers, branded styles, then fill programmatically
- Supports `InlineImage` for embedding matplotlib/seaborn charts as images with specified dimensions
- Tables rendered via Jinja2 loops — dynamic row counts, conditional sections
- Design teams can modify branding in Word without touching Python code
- Reduces code complexity by 70-80% vs. raw python-docx
- *Confidence: HIGH* — Production-proven, actively maintained, excellent fit
- _Source: [docxtpl PyPI](https://pypi.org/project/docxtpl/), [docxtpl Docs](https://docxtpl.readthedocs.io/), [Holistic AI Report Automation](https://medium.com/@engineering_holistic_ai/how-to-automate-creating-reports-using-docx-templates-bc3cbaae069e)_

**Chart embedding workflow:**
1. Generate charts with matplotlib/seaborn (already in requirements.txt)
2. Save as PNG to temp file
3. Embed via `docxtpl.InlineImage(tpl, image_path, width=Mm(150))`
- _Source: [PyTutorial Charts in DOCX](https://pytutorial.com/add-charts-to-docx-with-python-workarounds/)_

**For PDF output:**

**Option A: WeasyPrint (Recommended)**
- HTML/CSS → PDF conversion — leverage web design skills for layout
- Excellent for branded reports: CSS handles fonts, colors, page breaks, headers/footers
- Good for 90% of use cases; simpler development than ReportLab
- Requires system-level dependencies (cairo, pango) — manageable but adds install complexity
- _Source: [WeasyPrint vs ReportLab](https://dev.to/claudeprime/generate-pdfs-in-python-weasyprint-vs-reportlab-ifi), [8 Tools Compared](https://templated.io/blog/generate-pdfs-in-python-with-libraries/)_

**Option B: docx → PDF conversion via LibreOffice CLI**
- Generate docx first (docxtpl), then `libreoffice --headless --convert-to pdf`
- Single template design serves both formats — significant DX advantage
- Fidelity is good but not pixel-perfect for complex layouts
- Requires LibreOffice installed on the system

**Option C: ReportLab**
- Maximum control but highest development effort — pixel-perfect positioning
- Best for complex data-heavy layouts with custom typography
- Overkill for narrative report with embedded charts
- _Source: [Best PDF Libraries 2025](https://www.analyticsinsight.net/programming/best-python-pdf-generator-libraries-of-2025)_

**Recommendation:** docxtpl for docx (primary format) + WeasyPrint for PDF as a parallel renderer. Alternatively, docxtpl → LibreOffice headless conversion for PDF if you want a single template to serve both formats with less development effort.

### LLM Integration: Narrative Generation from Structured Data

**Claude API with Structured Outputs (Recommended)**

- Anthropic announced Structured Outputs (Nov 2025, now GA) — guarantees JSON schema compliance on first response via constrained decoding
- Use `client.messages.parse()` with Pydantic models to define exact report section schemas
- Pattern: Pass computed stats as grounding context → LLM generates narrative sections → validated against Pydantic schema
- Available on Claude Sonnet 4.5+, Opus 4.5+, Haiku 4.5+
- Eliminates retry/validation logic entirely — schema compliance guaranteed at inference time
- *Confidence: HIGH* — First-party, production-ready, ideal for structured report generation
- _Source: [Anthropic Structured Outputs Docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs), [Hands-On Guide](https://towardsdatascience.com/hands-on-with-anthropics-new-structured-output-capabilities/), [Zero-Error JSON](https://medium.com/@meshuggah22/zero-error-json-with-claude-how-anthropics-structured-outputs-actually-work-in-real-code-789cde7aff13)_

**Grounding Pattern for this project:**
```
Input to LLM:
  - Structured JSON quality report (from Stage 0)
  - Aggregated stats: sums, averages, growth rates, trends (from pandas)
  - Outlier flags and segment comparisons (from pandas)

Prompt structure:
  "Given these verified statistics [JSON], generate a narrative report
   with sections: summary, key_insights, anomalies, recommendations.
   Do NOT compute any numbers — only interpret the provided data."

Output:
  - Pydantic-validated JSON matching InsightReport schema
  - Each section: title, narrative text, supporting_data references
```

**Existing codebase leverage:** `nlp_processor.py` already has multi-LLM support (OpenAI, Anthropic, Gemini). The narrative generation can reuse this provider abstraction while adding the structured output pattern on top.

### CLI Framework

**Typer (Recommended)**
- Built on Click, uses Python type hints for automatic argument inference
- Minimal boilerplate — function signature IS the CLI interface
- Auto-generated `--help`, shell completion, rich error messages
- Perfect for the Reporting Agent and Monitoring Agent CLI entry points
- *Confidence: HIGH* — Modern standard for Python CLIs
- _Source: [Click vs Typer Guide 2026](https://devtoolbox.dedyn.io/blog/python-click-typer-cli-guide), [Building CLI Tools](https://dasroot.net/posts/2025/12/building-cli-tools-python-click-typer-argparse/)_

### Monitoring & Threshold Alerting

**Custom pandas script (Recommended — no framework needed)**
- Period-over-period comparison is a straightforward pandas operation: `current.merge(previous)` → compute `pct_change` → filter by threshold
- Alert logic: `if abs(pct_change) > threshold: emit_alert()`
- Output to stdout (print) and/or append to log file
- Default ±15% WoW threshold stored in config; overridable via CLI flag
- No need for Prometheus/Datadog/external monitoring in V1
- *Confidence: HIGH* — Trivially implementable with existing stack
- _Source: [Metric-Based Alerting in Python](https://www.linkedin.com/pulse/metric-based-alerting-python-andrew-f-1e), [Metrics and Monitoring](https://opensource.com/article/18/4/metrics-monitoring-and-python)_

### Technology Adoption Summary

| Component | Recommended Technology | New Dependency? | Confidence |
|---|---|---|---|
| Data Quality Validation | Pandera + existing DataProfile | Yes (pandera) | HIGH |
| Insight Report (docx) | docxtpl + matplotlib charts | Yes (docxtpl) | HIGH |
| Insight Report (PDF) | WeasyPrint or LibreOffice headless | Yes (one of) | HIGH |
| LLM Narrative | Claude API Structured Outputs | No (anthropic already installed) | HIGH |
| CLI Interface | Typer | Yes (typer) | HIGH |
| Monitoring Agent | Custom pandas script | No | HIGH |
| Pipeline Orchestration | Plain Python functions, no framework | No | HIGH |

---

## Integration Patterns Analysis

### Pipeline Stage Composition Pattern

The new Insights & Agents layer composes as a linear pipeline of pure Python functions. No framework, no DAG engine — just function calls with typed dataclass contracts between stages.

**Pattern: pandas `.pipe()` chaining for data transformations**
- Each stage accepts a DataFrame (or typed result object) and returns the next stage's input
- Stages are independently testable and composable
- No shared mutable state — each function receives inputs explicitly
- _Source: [pandas.DataFrame.pipe docs](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pipe.html), [Pandas Method Chaining](https://medium.com/data-science-collective/pandas-method-chaining-explained-build-fluent-data-pipelines-ae124c7612dc)_

**Pipeline orchestration — plain Python, no framework:**
```python
def run_full_pipeline(input_path: str, config: PipelineConfig) -> PipelineResult:
    df = load_data(input_path)                          # Stage 0a: Ingest
    quality_report = assess_data_quality(df, config)    # Stage 0b: Quality Assessment
    if quality_report.has_critical_issues:
        return PipelineResult(halted=True, quality_report=quality_report)
    cleaned_df = clean_data(df, quality_report)         # Stage 1: Clean
    insights = compute_insights(cleaned_df, config)     # Stage 2: Compute
    narrative = generate_narrative(insights, config)     # Stage 3: LLM Narrative
    report = render_report(narrative, config)            # Stage 4: Format Output
    return PipelineResult(report=report, quality_report=quality_report)
```

### JSON Contract Schemas Between Stages

Each pipeline stage communicates via typed Python dataclasses that serialize to JSON. This ensures contract enforcement without external schema registries.

**Stage 0 → Stage 1: DataQualityReport**
```python
@dataclass
class DataQualityDefect:
    defect_type: str       # "missing", "duplicate", "schema_inconsistency",
                           # "formatting", "statistical_anomaly", "referential_gap"
    severity: str          # "critical", "high", "medium", "low"
    affected_columns: List[str]
    count: int
    percentage: float
    details: str
    recommended_action: str

@dataclass
class DataQualityReport:
    overall_score: float              # 0-100 (extends existing quality_score)
    defects: List[DataQualityDefect]
    has_critical_issues: bool         # Pipeline halt flag
    halt_reason: Optional[str]
    column_profiles: Dict[str, ColumnProfile]
    timestamp: str
```

**Stage 2 → Stage 3: InsightPayload (stats for LLM grounding)**
```python
@dataclass
class InsightPayload:
    summary_stats: Dict[str, Any]        # From DescriptiveAnalytics
    correlations: List[Dict]             # From DiagnosticAnalytics
    outlier_flags: List[Dict]            # Row-level outlier details
    trend_data: Optional[Dict]           # Period-over-period if time columns exist
    segment_comparisons: Optional[Dict]  # Cross-category metrics
    quality_findings: DataQualityReport  # From Stage 0
```

**Stage 3 → Stage 4: InsightReport (LLM output, Pydantic-validated)**
```python
class InsightReport(BaseModel):
    data_quality_section: QualityNarrative
    summary: str
    key_insights: List[InsightItem]
    anomalies: List[AnomalyItem]
    recommendations: List[RecommendationItem]
```

### LLM Integration Pattern: Grounded Narrative Generation

**Pattern:** Stats-in → Narrative-out with Claude Structured Outputs

The LLM receives pre-computed statistics as grounding context and generates narrative text. It does NOT compute independently — all numbers come from pandas.

**Implementation via Claude API Structured Outputs:**
- Define `InsightReport` as a Pydantic model
- Pass to `client.messages.create()` with `response_format` parameter
- Claude guarantees JSON schema compliance on first response — no retry loops needed
- _Source: [Claude Structured Outputs Docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)_

**Prompt grounding template:**
```
System: You are a data analyst writing a professional insight report.
You will receive pre-computed statistics. Your job is to INTERPRET
these statistics into clear business narratives. NEVER compute or
invent numbers — only reference the data provided.

User: [InsightPayload JSON]
Generate the insight report following the provided schema.
```

### CLI Integration Pattern

**Typer-based entry points — two standalone scripts:**

1. **Reporting Agent** (`reporting_agent.py`):
```python
@app.command()
def generate_report(
    input_file: Path,
    output_format: str = "docx",  # or "pdf"
    output_dir: Path = Path("./reports"),
    config_file: Optional[Path] = None,
):
    config = load_config(config_file)
    result = run_full_pipeline(str(input_file), config)
    render_report(result, output_format, output_dir)
```

2. **Monitoring Agent** (`monitoring_agent.py`):
```python
@app.command()
def check_metrics(
    current_file: Path,
    previous_file: Path,
    threshold: float = 0.15,  # ±15% default
    metric_columns: Optional[List[str]] = None,
):
    alerts = compare_periods(current_file, previous_file, threshold, metric_columns)
    for alert in alerts:
        print(alert)  # V1: stdout only
```

### Report Rendering Integration

**docx workflow with docxtpl:**
1. Designer creates branded .docx template in Word (logos, headers/footers, styles)
2. Template uses Jinja2 tags: `{{ summary }}`, `{% for insight in key_insights %}`, `{{ chart_image }}`
3. Python generates matplotlib charts → saves as PNG → embeds via `InlineImage(tpl, path, width=Mm(150))`
4. Context dict populated from `InsightReport` → `tpl.render(context)` → `tpl.save(output.docx)`
- _Source: [docxtpl Docs](https://docxtpl.readthedocs.io/), [InlineImage Usage](https://snyk.io/advisor/python/docxtpl/functions/docxtpl.InlineImage), [Chart Embedding](https://pytutorial.com/add-charts-to-docx-with-python-workarounds/)_

**PDF workflow options:**
- **Option A (Recommended for V1):** docx → PDF via LibreOffice headless (`libreoffice --headless --convert-to pdf output.docx`) — single template serves both formats
- **Option B (Higher fidelity):** WeasyPrint with separate HTML/CSS template — more control but two templates to maintain

---

## Existing Code Reuse Assessment

### Reuse Classification Summary

| Module | File | Reuse | Adapt | New | Verdict |
|--------|------|-------|-------|-----|---------|
| Data Profiling | `advanced_pipeline.py` | `DataProfile`, `profile_data()`, basic/statistical cleaning | Severity levels, halt logic, schema checks | Format detection, referential gaps, statistical red flags | **60% reuse** |
| Analytics Compute | `comprehensive_analytics.py` | `DescriptiveAnalytics.statistical_summary()`, `DiagnosticAnalytics.correlation_analysis()` | Time-based trends, segment comparisons, growth rates | Outlier row flagging, composite scoring | **55% reuse** |
| LLM Provider | `nlp_processor.py` | `LLMProvider` enum, multi-provider init, `_prepare_dataset_context()` | `_call_llm()` for Claude Structured Outputs (model upgrade + response_format) | Narrative template system, confidence scoring | **40% reuse** |
| Data Cleaning | `cleaner.py` | `clean_dataframe(df)` — standalone, no deps | None needed | None | **100% reuse** |
| Thin Analytics | `analytics.py` | Pattern only | Deprecate `LLMDataInterface`, call `ComprehensiveAnalytics` directly | CLI facade function | **20% reuse** |
| API Endpoints | `main.py` / `main_enhanced.py` | Upload/parse logic, auth patterns | Extract pipeline from HTTP cycle | CLI orchestrator, config management, error handling | **15% reuse** |

### Critical Reuse Details

**✅ USE AS-IS (zero changes):**
- `cleaner.clean_dataframe(df)` — perfect standalone function for CLI
- `DescriptiveAnalytics.statistical_summary(df)` — returns JSON-serializable dict with means, medians, std, quantiles, outliers
- `DiagnosticAnalytics.correlation_analysis(df)` — Pearson + Spearman with strong-correlation detection
- `DataCleaner.profile_data(df)` — profiling with missing %, outlier %, quality score

**🔧 ADAPT (modify, don't rewrite):**
- `nlp_processor.py` `_call_llm()` → update Anthropic model from `claude-3-haiku-20240307` (deprecated) to current model + add `response_format` for Structured Outputs
- `advanced_pipeline.py` `recommend_cleaning_method()` → refactor into `assess_data_quality()` returning `DataQualityDefect` list with severity ratings instead of cleaning method names
- `DescriptiveAnalytics` → add time-based trend computation when datetime columns present
- `DiagnosticAnalytics` → add `segment_by_column` parameter for per-segment comparisons

**🆕 BUILD FROM SCRATCH (no existing code covers this):**
- **Data Quality Assessment stage**: Schema inconsistency detection (mixed types within columns), formatting issue detection (date formats, encoding), statistical red flags (zero variance, extreme cardinality), referential gap detection
- **Pipeline orchestrator**: `run_full_pipeline()` — pure function, no HTTP/state dependency
- **Report renderer**: docxtpl template population + chart generation + output formatting
- **Monitoring Agent**: Period comparison + threshold alerting script
- **CLI entry points**: Typer-based commands for both agents
- **Configuration system**: Typed `PipelineConfig` dataclass with thresholds, LLM settings, output preferences

### Code Quality Issues Found

| Severity | Issue | Location |
|----------|-------|----------|
| ⚠️ HIGH | `warnings.filterwarnings('ignore')` masks errors | `advanced_pipeline.py:10`, `comprehensive_analytics.py:17` |
| ⚠️ HIGH | Deprecated Anthropic model hardcoded | `nlp_processor.py:146` (`claude-3-haiku-20240307`) |
| ⚠️ HIGH | In-memory DATA_STORAGE not persistent | `main.py:27`, `main_enhanced.py:61` |
| ⚠️ MEDIUM | No logging anywhere in pipeline | All backend modules |
| ⚠️ MEDIUM | Greedy regex JSON extraction | `nlp_processor.py:164` (`r'\{.*\}'`) |
| ⚠️ MEDIUM | No async LLM calls — blocks event loop | `nlp_processor.py` |
| ⚠️ LOW | Duplicate analytics routing logic | `advanced_pipeline.py` AnalyticsClassifier vs `nlp_processor.py` intent analysis |
| ⚠️ LOW | NaN/Inf not handled in JSON serialization | `comprehensive_analytics.py` result dicts |

### Tech Stack Feasibility Verdict

| Requirement | Can Recommended Stack Deliver? | Notes |
|---|---|---|
| Data Quality Assessment with severity ratings & halt-on-critical | ✅ YES | Pandera schemas for validation + custom `DataQualityDefect` dataclass for structured report |
| Insight Report as structured JSON (5 sections) | ✅ YES | Claude Structured Outputs guarantee schema compliance; Pydantic models define sections |
| LLM narrative from grounded stats (no independent computation) | ✅ YES | Prompt grounding pattern + structured output = stats-in, narrative-out |
| Professional branded docx with logos, charts, tables | ✅ YES | docxtpl Jinja2 templates designed in Word; matplotlib charts via InlineImage |
| PDF output | ✅ YES | LibreOffice headless conversion (V1) or WeasyPrint (V2) |
| CLI-triggered Reporting Agent | ✅ YES | Typer command wrapping `run_full_pipeline()` |
| Monitoring Agent with ±15% WoW threshold | ✅ YES | Pure pandas `pct_change()` + threshold comparison; trivial implementation |
| AI agents built from scratch in Python | ✅ YES | No frameworks — plain Python classes/functions with Typer CLI layer |
| >50% null halt, empty dataset halt | ✅ YES | Pandera `Check.not_null()` threshold + custom halt logic in quality assessment |

---

## Architectural Patterns and Design

### System Architecture: Pipes and Filters (Linear Pipeline)

The recommended architecture is the **Pipes and Filters** pattern — a system structured as a series of independent processing stages (filters) connected by typed data contracts (pipes). Each stage receives a defined input, performs one transformation, and produces a defined output.

**Why this pattern for SavvyCleanse:**
- Maps directly to the spec's linear flow: Ingest → Quality Assessment → Clean → Compute → Narrative → Render
- Each stage is independently testable and replaceable
- No shared mutable state — eliminates the `DATA_STORAGE` dict anti-pattern in the existing codebase
- No orchestration framework needed — plain Python function composition
- _Source: [Pipes and Filters Architecture 2025](https://techshitanshu.com/pipes-and-filters-pattern-architecture/), [Pipeline Pattern in Python](https://pybit.es/articles/a-practical-example-of-the-pipeline-pattern-in-python/), [Data Pipeline Design Patterns](https://www.startdataengineering.com/post/code-patterns/)_

**Anti-patterns this avoids:**
- ❌ Monolithic endpoint handlers (current `main.py` approach — pipeline coupled to HTTP)
- ❌ In-memory global state (`DATA_STORAGE` dict — not persistent, not testable)
- ❌ Implicit stage ordering (current: must call `/upload` before `/clean` before `/analyze`)

### Design Principles Applied

**1. Separation of Concerns — Three Distinct Layers**

```
┌─────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                  │
│  ├── CLI (Typer commands)                           │
│  ├── FastAPI endpoints (existing, optional)          │
│  └── Report renderer (docxtpl / WeasyPrint)         │
├─────────────────────────────────────────────────────┤
│  BUSINESS LOGIC LAYER                                │
│  ├── DataQualityAssessor (Pandera + custom checks)  │
│  ├── InsightEngine (ComprehensiveAnalytics, reused) │
│  ├── NarrativeGenerator (Claude Structured Outputs) │
│  └── MetricMonitor (pandas pct_change + thresholds) │
├─────────────────────────────────────────────────────┤
│  DATA ACCESS LAYER                                   │
│  ├── FileLoader (CSV, Excel, TSV — existing parse)  │
│  ├── ConfigLoader (YAML/JSON pipeline config)       │
│  └── ReportWriter (docx/PDF file output)            │
└─────────────────────────────────────────────────────┘
```

- **Presentation** handles I/O format (CLI args, HTTP requests, file output) — never touches business logic
- **Business Logic** owns computation and transformation — never touches files or HTTP
- **Data Access** handles reading/writing — never computes
- _Source: [Separation of Concerns in Data Pipelines](https://medium.com/the-pythonworld/the-cleanest-way-to-structure-a-python-project-in-2025-4f04ccb8602f), [Structuring Python Projects](https://docs.python-guide.org/writing/structure/)_

**2. Strategy Pattern for Pluggable Components**

Several pipeline components benefit from runtime strategy selection:

| Component | Strategy Interface | Concrete Strategies |
|---|---|---|
| LLM Provider | `NarrativeStrategy` | `ClaudeStrategy`, `OpenAIStrategy`, `GeminiStrategy` |
| Output Format | `ReportRenderer` | `DocxRenderer`, `PdfRenderer` |
| Cleaning Method | `CleaningStrategy` | `BasicStrategy`, `StatisticalStrategy`, `MLStrategy` |

This leverages the existing `recommend_cleaning_method()` pattern in `advanced_pipeline.py` but formalizes it as a proper strategy selection.
- _Source: [Design Patterns for Data Pipelines](https://amsayed.medium.com/coding-data-pipeline-design-patterns-in-python-44a705f0af9e), [Modular Data Processing](https://medium.com/@dkraczkowski/the-elegance-of-modular-data-processing-with-pythons-pipeline-approach-e63bec11d34f)_

**3. Contract-First Design with Pydantic Models**

Every stage boundary enforces a typed contract using Pydantic `BaseModel`:

- **Input validation**: Pydantic validates inputs at stage entry — malformed data fails fast with clear errors
- **Output guarantee**: Each stage returns a validated model — downstream stages can trust the shape
- **Serialization built-in**: All contracts serialize to JSON for logging, debugging, and LLM context
- Pydantic v2.8+ introduced experimental "pipeline" API for composing validation/transformation steps in a type-safe manner
- _Source: [Pydantic Docs](https://docs.pydantic.dev/latest/), [Pydantic Dataclasses](https://docs.pydantic.dev/latest/concepts/dataclasses/), [Data Validation Pipeline with Pydantic and Pandera](https://agentbus.sh/posts/how-to-build-data-validation-with-pydantic-and-pandera/)_

### Recommended Project Structure

```
backend/
├── agents/                          # NEW — from-scratch Python agents
│   ├── __init__.py
│   ├── reporting_agent.py           # Typer CLI: full pipeline → branded report
│   └── monitoring_agent.py          # Typer CLI: period comparison → alerts
│
├── pipeline/                        # NEW — extracted pipeline stages
│   ├── __init__.py
│   ├── orchestrator.py              # run_full_pipeline() composer
│   ├── data_quality.py              # Stage 0: DataQualityAssessor
│   ├── insight_engine.py            # Stage 2: wraps ComprehensiveAnalytics
│   ├── narrative_generator.py       # Stage 3: Claude Structured Outputs
│   └── config.py                    # PipelineConfig dataclass
│
├── models/                          # NEW — typed contracts between stages
│   ├── __init__.py
│   ├── quality_report.py            # DataQualityReport, DataQualityDefect
│   ├── insight_payload.py           # InsightPayload (stats for LLM)
│   ├── insight_report.py            # InsightReport (Pydantic, LLM output)
│   └── pipeline_config.py          # PipelineConfig, thresholds
│
├── renderers/                       # NEW — report output formatting
│   ├── __init__.py
│   ├── docx_renderer.py             # docxtpl template population
│   ├── pdf_renderer.py              # WeasyPrint or LibreOffice conversion
│   └── templates/                   # .docx and .html branded templates
│       ├── insight_report.docx
│       └── insight_report.html
│
├── advanced_pipeline.py             # EXISTING — DataCleaner, DataProfile (adapt)
├── comprehensive_analytics.py       # EXISTING — analytics engine (reuse)
├── nlp_processor.py                 # EXISTING — LLM provider layer (adapt)
├── cleaner.py                       # EXISTING — clean_dataframe() (reuse as-is)
├── main.py                          # EXISTING — FastAPI (keep for web UI)
└── requirements.txt                 # UPDATED — add pandera, docxtpl, typer
```

**Key principle:** New code goes in new directories (`agents/`, `pipeline/`, `models/`, `renderers/`). Existing code stays in place — adapted via imports, never moved or rewritten. The FastAPI layer continues to serve the web UI; the CLI agents bypass it entirely.
- _Source: [ETL Pipeline Project Structure](https://medium.com/@aliakbarhosseinzadeh/structuring-an-etl-pipeline-project-best-practices-5ed1e4d5a601), [Python Project Structure Guide](https://docs.python-guide.org/writing/structure/)_

### Error Handling Architecture

**Halt-on-Critical Pattern for Data Quality:**

The pipeline implements a two-tier error strategy:

1. **Critical halt** — Pipeline stops with diagnostic output, no misleading results generated
   - Triggers: >50% nulls in key metric column, entirely empty dataset, zero rows after dedup
   - Returns: `PipelineResult(halted=True, quality_report=report, halt_reason="...")`
   - No LLM call made, no report rendered — saves cost and prevents garbage output

2. **Graceful degradation** — Pipeline continues with warnings embedded in report
   - Triggers: <50% nulls, minor formatting issues, some outliers
   - Behavior: Quality findings included in report as dedicated section, insights generated with caveats
   - _Source: [Graceful Degradation in Python](https://medium.com/@RampantLions/robust-error-handling-in-python-tracebacks-graceful-degradation-and-suppression-11f7a140720b), [Pipeline Failure Handling](https://leonidasgorgo.medium.com/error-handling-mitigating-pipeline-failures-c28338034d96)_

**LLM API Resilience:**
- Retry with exponential backoff (max 3 attempts) for transient API failures
- Provider fallback chain: Claude → OpenAI → Gemini (leveraging existing multi-provider support in `nlp_processor.py`)
- Circuit breaker: After 3 consecutive failures, skip narrative generation and output stats-only report
- _Source: [AI Agent Error Handling Patterns](https://dev.to/nebulagg/ai-agent-error-handling-4-resilience-patterns-in-python-12of), [API Retry Strategies 2026](https://easyparser.com/blog/api-error-handling-retry-strategies-python-guide)_

### Logging Architecture

**Replace `warnings.filterwarnings('ignore')` with structured logging:**

- Use `structlog` for JSON-structured log output — machine-parseable, context-rich
- Each pipeline stage logs: stage name, input shape, output shape, duration, warnings
- Quality defects logged as structured events with severity, column, count
- LLM calls logged with: provider, model, token count, latency, success/failure
- _Source: [structlog for Python](https://blog.naveenpn.com/pythons-structlog-modern-structured-logging-for-clean-json-ready-logs), [Structured Logging Best Practices](https://uptrace.dev/glossary/structured-logging), [Zero-Dependency Structured JSON Logging](https://johal.in/structlog-24-2-0-context-zero-dependency-structured-json-logging-2025/)_

**Log format example:**
```json
{
  "timestamp": "2026-04-09T14:30:00Z",
  "level": "warning",
  "stage": "data_quality",
  "event": "defect_detected",
  "defect_type": "missing_values",
  "severity": "high",
  "column": "revenue",
  "null_percentage": 23.5,
  "pipeline_run_id": "run-abc123"
}
```

### Architecture Decision Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Pipeline pattern | Pipes and Filters (linear) | Matches spec flow, no DAG complexity needed |
| State management | Immutable pass-through (no global state) | Eliminates DATA_STORAGE anti-pattern |
| Contract enforcement | Pydantic BaseModel at stage boundaries | Type safety + JSON serialization + LLM schema compliance |
| Error strategy | Halt-on-critical + graceful degradation | Prevents misleading output while maximizing useful results |
| Agent implementation | From-scratch Python classes + Typer CLI | No framework overhead, full control, user requirement |
| Logging | structlog (JSON structured) | Replaces `warnings.filterwarnings('ignore')`, machine-parseable |
| Project structure | New dirs alongside existing code | Zero disruption to working web UI; CLI and API coexist |
| LLM resilience | Retry + provider fallback + circuit breaker | Leverages existing multi-provider support |

### Python Error Handling Constructs — Evaluation for This Pipeline

#### The Core Constructs

**`try` / `except` — The Foundation**
Wraps risky code and catches specific exception types. Best practice: keep `try` blocks minimal — only the line(s) that can actually fail. The more code inside `try`, the harder it is to identify what caused the error.
- _Source: [Python Try Except Best Practices](https://python.land/deep-dives/python-try-except), [Real Python Exceptions Guide](https://realpython.com/python-exceptions/)_

**`else` — The Unsung Hero (Recommended for this pipeline)**
Executes only when `try` succeeds with no exception. Critical benefit: it avoids accidentally catching an exception that wasn't raised by the code being protected. This is particularly important for the pipeline because success-path logic (like proceeding to the next stage) should be cleanly separated from error-handling logic.
- _Source: [Python Docs: Errors and Exceptions](https://docs.python.org/3/tutorial/errors.html), [Exception Handling Explained](https://www.rustcodeweb.com/2025/09/exception-handling-in-python-try-except-else-and-finally-explained.html)_

**`finally` — Guaranteed Cleanup**
Always executes regardless of success or failure — even if a `return` statement is encountered in `try` or `except`. Essential for resource cleanup: closing file handles, releasing LLM client connections, flushing log buffers.
- _Source: [GeeksforGeeks Try Except Else Finally](https://www.geeksforgeeks.org/python/try-except-else-and-finally-in-python/)_

#### Recommended Pattern for Each Pipeline Stage

```python
def run_stage(input_data: StageInput, config: PipelineConfig) -> StageOutput:
    """Pattern: try wraps ONLY the risky operation, else handles success path."""
    logger = structlog.get_logger()

    try:
        result = perform_risky_operation(input_data)  # Minimal try block
    except SpecificExpectedError as e:
        logger.error("stage_failed", stage="quality_assessment", error=str(e))
        raise PipelineStageError("quality_assessment", cause=e) from e
    except ExternalAPIError as e:
        logger.warning("api_failed", provider=config.llm_provider, error=str(e))
        return fallback_result(input_data)  # Graceful degradation
    else:
        # Success path — separated from error handling
        logger.info("stage_completed", stage="quality_assessment", rows=len(result))
        return validate_output(result)  # Pydantic validation here
    finally:
        # Cleanup regardless of outcome
        cleanup_temp_files()
```

**Why `else` matters here:** If `validate_output()` raises a `ValidationError`, it should NOT be caught by the `except SpecificExpectedError` handler. Putting it in `else` ensures only `perform_risky_operation()` errors are caught — validation failures propagate naturally as a different error type.

#### Advanced Constructs Evaluation

**`ExceptionGroup` + `except*` (Python 3.11+) — Recommended for Data Quality Stage**

ExceptionGroup wraps multiple unrelated exceptions into a single propagatable group. The `except*` syntax enables selective handling of specific exception types within the group while letting others propagate.

**Perfect fit for Data Quality Assessment:** When scanning a dataset, multiple quality issues occur simultaneously (missing values in column A, schema mismatch in column B, formatting error in column C). Rather than failing fast on the first issue, collect ALL defects and report them together.

```python
def assess_data_quality(df: pd.DataFrame, config: dict) -> DataQualityReport:
    """Collect all quality issues, don't fail on the first one."""
    defects = []
    errors = []

    for check in [check_nulls, check_duplicates, check_schema, check_formatting, check_statistics]:
        try:
            result = check(df, config)
            if result.defects:
                defects.extend(result.defects)
        except DataQualityCheckError as e:
            errors.append(e)

    # If checks themselves failed (not just found defects), raise as group
    if errors:
        raise ExceptionGroup("Multiple quality checks failed", errors)

    return DataQualityReport(defects=defects, has_critical_issues=any_critical(defects))
```

Or using `except*` for the caller:
```python
try:
    quality_report = assess_data_quality(df, config)
except* SchemaCheckError as eg:
    # Handle all schema errors as a group
    log_schema_errors(eg.exceptions)
except* StatisticalCheckError as eg:
    # Handle statistical anomalies separately
    log_statistical_anomalies(eg.exceptions)
```

- _Source: [PEP 654 – Exception Groups](https://peps.python.org/pep-0654/), [ExceptionGroup Practical Guide](https://thelinuxcode.com/exception-groups-in-python-311-a-practical-guide-to-multi-error-handling/), [except* Deep Dive](https://runebook.dev/en/docs/python/library/exceptions/exception-groups)_

**Result Pattern (Functional Alternative) — Recommended for Stage Returns**

Instead of raising exceptions for expected business outcomes (like "data has quality issues"), use a Result-type return that explicitly encodes success or failure as a value. Exceptions should be reserved for truly unexpected situations (disk full, network down).

```python
@dataclass
class PipelineResult:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    quality_report: Optional[DataQualityReport] = None
    halted: bool = False
    halt_reason: Optional[str] = None

def run_full_pipeline(input_path: str, config: PipelineConfig) -> PipelineResult:
    quality_report = assess_data_quality(df, config)

    if quality_report.has_critical_issues:
        # NOT an exception — this is expected business logic
        return PipelineResult(
            success=False,
            halted=True,
            halt_reason=f"Critical data quality issues: {quality_report.critical_summary}",
            quality_report=quality_report
        )

    # Continue pipeline...
    return PipelineResult(success=True, data=final_report, quality_report=quality_report)
```

**Why Result over exceptions for halt-on-critical:** A dataset with >50% nulls is not an "error" — it's a valid business outcome that the pipeline handles deliberately. Using `PipelineResult(halted=True)` makes the halt path explicit and testable, rather than relying on exception propagation.
- _Source: [Result Types in Python](https://www.krython.com/tutorial/python/functional-error-handling-result-types), [Error Handling Result Class](https://aaronluna.dev/blog/error-handling-python-result-class/), [5 Patterns Beyond Try-Except](https://www.kdnuggets.com/5-error-handling-patterns-in-python-beyond-try-except)_

**Custom Exception Hierarchy — Recommended for Unexpected Failures**

Define a domain-specific exception tree so callers can catch at the right granularity:

```python
class SavvyCleanseError(Exception):
    """Base exception for all pipeline errors."""
    pass

class PipelineStageError(SavvyCleanseError):
    """A pipeline stage encountered an unexpected failure."""
    def __init__(self, stage: str, cause: Exception):
        self.stage = stage
        self.cause = cause
        super().__init__(f"Stage '{stage}' failed: {cause}")

class LLMProviderError(SavvyCleanseError):
    """LLM API call failed after retries."""
    def __init__(self, provider: str, attempts: int, last_error: Exception):
        self.provider = provider
        self.attempts = attempts
        super().__init__(f"{provider} failed after {attempts} attempts: {last_error}")

class ReportRenderError(SavvyCleanseError):
    """Report generation (docx/PDF) failed."""
    pass

class DataQualityCheckError(SavvyCleanseError):
    """A quality check itself failed to execute (not a data issue)."""
    pass
```

**Catch granularity at CLI level:**
```python
try:
    result = run_full_pipeline(input_path, config)
except LLMProviderError as e:
    print(f"⚠️  LLM unavailable ({e.provider}). Stats-only report generated.")
except ReportRenderError as e:
    print(f"❌ Report rendering failed: {e}")
    sys.exit(1)
except SavvyCleanseError as e:
    print(f"❌ Pipeline error: {e}")
    sys.exit(1)
```

- _Source: [Custom Exception Hierarchy](https://hrekov.com/blog/python-custom-exceptions), [Custom Exceptions for Domain-Specific Signaling](https://kindatechnical.com/python/lesson-57-custom-exception-classes.html), [How to Create Custom Exceptions](https://oneuptime.com/blog/post/2026-01-22-create-custom-exceptions-python/view)_

#### Error Handling Strategy Summary for This Pipeline

| Construct | Use For | Pipeline Location |
|-----------|---------|-------------------|
| `try/except` (specific types) | Catching expected failure modes | Every stage — file I/O, API calls, pandas operations |
| `else` | Success-path logic separated from error handling | Stage transitions — validate output before passing downstream |
| `finally` | Resource cleanup | File handles, temp chart images, LLM client sessions |
| `ExceptionGroup` + `except*` | Collecting multiple simultaneous quality defects | Data Quality Assessment — scan ALL columns, report ALL issues |
| Result pattern (`PipelineResult`) | Expected business outcomes (halt, warnings) | Pipeline orchestrator — halt-on-critical is NOT an exception |
| Custom exception hierarchy | Unexpected failures with domain context | `SavvyCleanseError` → `PipelineStageError`, `LLMProviderError`, `ReportRenderError` |
| Context managers (`with`) | Auto-cleanup for file operations | `docxtpl` template loading, matplotlib figure creation, temp file management |

**Design principle:** Exceptions are for the *unexpected*. Result types are for the *expected*. A dataset with bad data is expected — return `PipelineResult(halted=True)`. A disk running out of space is unexpected — raise `ReportRenderError`.

---

## Implementation Approaches and Technology Adoption

### Phased Implementation Roadmap

The build should follow a **vertical slice** strategy — each phase delivers a working, demo-able increment rather than building horizontal layers in isolation. Every phase ends with something you can run and show.

**Phase 1: Foundation & Data Quality (Week 1-2)**
- Create `models/` directory with all Pydantic/dataclass contracts (`DataQualityReport`, `DataQualityDefect`, `InsightPayload`, `InsightReport`, `PipelineConfig`)
- Create `pipeline/data_quality.py` — the `DataQualityAssessor` class
  - Reuse `DataCleaner.profile_data()` for baseline metrics
  - Add Pandera schema validation for structural checks
  - Add new detection: schema inconsistencies, formatting issues, statistical red flags
  - Implement halt-on-critical logic (>50% nulls, empty dataset)
  - Implement `ExceptionGroup` pattern to collect ALL defects
- Create `pipeline/orchestrator.py` — `run_full_pipeline()` stub that calls quality assessment only
- Create `pipeline/config.py` — `PipelineConfig` with default thresholds
- **Deliverable:** CLI command that ingests a CSV and outputs a JSON quality report

**Phase 2: Insight Engine + LLM Narrative (Week 2-3)**
- Create `pipeline/insight_engine.py` — wraps `ComprehensiveAnalytics` for compute stage
  - Wire `DescriptiveAnalytics.statistical_summary()` (reuse as-is)
  - Wire `DiagnosticAnalytics.correlation_analysis()` (reuse as-is)
  - Add time-based trend computation (new)
  - Add segment comparison logic (new)
  - Output: `InsightPayload` dataclass
- Create `pipeline/narrative_generator.py` — Claude Structured Outputs integration
  - Adapt `nlp_processor.py` provider pattern, update to current Anthropic model
  - Define `InsightReport` as Pydantic model for `response_format`
  - Implement grounding prompt template (stats-in, narrative-out)
  - Implement provider fallback chain + retry with backoff
- Wire stages into `orchestrator.py`: quality → clean → compute → narrative
- **Deliverable:** CLI command that ingests CSV → outputs structured JSON insight report

**Phase 3: Report Rendering + Reporting Agent (Week 3-4)**
- Create `renderers/docx_renderer.py` — docxtpl template population
  - Design branded .docx template in Word (logos, headers/footers, styles)
  - Chart generation: matplotlib → PNG → `InlineImage` embedding
  - Table rendering via Jinja2 loops for quality findings, key insights
- Create `renderers/pdf_renderer.py` — LibreOffice headless conversion (V1)
- Create `agents/reporting_agent.py` — Typer CLI wrapping `run_full_pipeline()` + renderer
- **Deliverable:** `python -m agents.reporting_agent generate --input data.csv --format docx` → branded report file

**Phase 4: Monitoring Agent + Polish (Week 4-5)**
- Create `agents/monitoring_agent.py` — period-over-period comparison
  - Load current and previous period CSVs
  - Compute `pct_change()` on metric columns
  - Apply ±15% default threshold (configurable via `--threshold`)
  - Emit alerts to stdout and optionally log file
- Add structured logging (`structlog`) across all pipeline stages
- Add custom exception hierarchy (`SavvyCleanseError` tree)
- **Deliverable:** Full system demo — quality assessment → insight report → branded docx/PDF → monitoring alerts

### Testing Strategy

**No tests exist currently.** This is a greenfield opportunity to build testing right from Phase 1.

**Test pyramid for this pipeline:**

```
         ╱ E2E Tests ╲                    (1-2 tests)
        ╱  CLI invoke  ╲                  Full pipeline: CSV in → report out
       ╱───────────────────╲
      ╱ Integration Tests    ╲            (5-10 tests)
     ╱  Stage-to-stage wiring  ╲          Quality → Compute → Narrative chain
    ╱───────────────────────────────╲
   ╱       Unit Tests                ╲    (20-40 tests)
  ╱  Individual functions/classes      ╲  Each check, each analytics method
 ╱─────────────────────────────────────────╲
```

**Unit tests — pytest with DataFrame fixtures:**

```python
# conftest.py
@pytest.fixture
def sample_clean_df():
    """A clean DataFrame with no quality issues."""
    return pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=100),
        "revenue": np.random.uniform(1000, 5000, 100),
        "region": np.random.choice(["North", "South", "East"], 100),
    })

@pytest.fixture
def sample_dirty_df():
    """A DataFrame with known quality issues for testing defect detection."""
    df = pd.DataFrame({
        "date": ["2026-01-01", "bad_date", None] * 33 + ["2026-01-01"],
        "revenue": [1000, None, None] * 33 + [1000],  # 66% nulls → critical
        "region": ["North", "North", "North"] * 33 + ["North"],  # zero variance
    })
    return df
```

**Testing each quality check independently:**
```python
def test_null_detection_flags_critical(sample_dirty_df):
    report = assess_data_quality(sample_dirty_df, default_config)
    revenue_defect = next(d for d in report.defects if d.affected_columns == ["revenue"])
    assert revenue_defect.severity == "critical"
    assert revenue_defect.percentage > 50.0
    assert report.has_critical_issues is True

def test_clean_data_passes_quality(sample_clean_df):
    report = assess_data_quality(sample_clean_df, default_config)
    assert report.has_critical_issues is False
    assert report.overall_score > 80.0
```

**Integration tests — stage chaining:**
```python
def test_full_pipeline_halts_on_critical_data(sample_dirty_df, tmp_path):
    config = PipelineConfig(output_format="json")
    result = run_full_pipeline(sample_dirty_df, config)
    assert result.halted is True
    assert result.halt_reason is not None
    assert result.quality_report.has_critical_issues is True
    # No LLM call should have been made
```

**CLI E2E tests — Typer CliRunner:**
```python
from typer.testing import CliRunner
from agents.reporting_agent import app

runner = CliRunner()

def test_reporting_agent_generates_docx(tmp_path, sample_csv_path):
    result = runner.invoke(app, ["generate", "--input", str(sample_csv_path),
                                  "--format", "docx", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "insight_report.docx").exists()
```

- _Source: [pytest Data Pipeline Fixtures](https://medium.com/capital-fund-management/advanced-testing-techniques-for-your-python-data-pipeline-with-dask-and-pytest-fixtures-622064867ef8), [Integration Tests for Python Pipelines](https://www.startdataengineering.com/post/python-datapipeline-integration-test/), [Typer CLI Testing](https://typer.tiangolo.com/tutorial/testing/), [pytest with Typer and Argparse](https://pytest-with-eric.com/pytest-advanced/pytest-argparse-typer/)_

### Expanded Unit Test Coverage

#### A. Narrative Generator Tests (Mocking Claude API)

The narrative generator calls the Claude API with structured outputs. Tests must verify: (1) the prompt is correctly grounded with stats, (2) the output conforms to the Pydantic schema, and (3) no numbers appear in the narrative that weren't in the input payload. All tests mock the API — no real calls.

```python
# tests/test_narrative_generator.py
from unittest.mock import patch, MagicMock
import json
import pytest
from models.insight_report import InsightReport
from models.insight_payload import InsightPayload
from pipeline.narrative_generator import NarrativeGenerator

@pytest.fixture
def sample_insight_payload():
    """Pre-computed stats that the LLM receives as grounding context."""
    return InsightPayload(
        summary_stats={
            "total_revenue": 125000.50,
            "avg_order_value": 47.32,
            "growth_rate_pct": 12.5,
            "row_count": 2643,
        },
        correlations=[
            {"col_a": "ad_spend", "col_b": "revenue", "pearson": 0.87, "strength": "strong"}
        ],
        outlier_flags=[
            {"row_idx": 142, "column": "order_value", "value": 9999.99, "reason": "IQR"}
        ],
        trend_data={"direction": "upward", "slope": 3.2, "periods": 12},
        segment_comparisons={"North": 52000, "South": 38000, "East": 35000},
        quality_findings=None,
    )

@pytest.fixture
def mock_claude_response():
    """A valid Claude structured output matching InsightReport schema."""
    return {
        "data_quality_section": {"summary": "No critical issues found.", "defect_count": 0},
        "summary": "Revenue of $125,000.50 across 2,643 orders shows 12.5% growth.",
        "key_insights": [
            {"title": "Strong ad-revenue correlation", "detail": "Ad spend and revenue show 0.87 Pearson correlation.", "confidence": "high"},
            {"title": "Regional disparity", "detail": "North region ($52,000) leads South ($38,000) by 37%.", "confidence": "high"},
        ],
        "anomalies": [
            {"title": "Outlier order", "detail": "Row 142: order_value $9,999.99 flagged by IQR method.", "severity": "medium"}
        ],
        "recommendations": [
            {"title": "Increase ad spend", "detail": "Strong 0.87 correlation suggests ROI on ad investment.", "priority": "high"}
        ],
    }

class TestNarrativeGenerator:

    @patch("pipeline.narrative_generator.anthropic.Anthropic")
    def test_generates_valid_insight_report(self, mock_anthropic, sample_insight_payload, mock_claude_response):
        """LLM output conforms to InsightReport Pydantic schema."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=json.dumps(mock_claude_response))]
        )
        mock_anthropic.return_value = mock_client

        generator = NarrativeGenerator(provider="anthropic", model="claude-sonnet-4-5-20241022")
        report = generator.generate(sample_insight_payload)

        assert isinstance(report, InsightReport)
        assert len(report.key_insights) >= 1
        assert len(report.recommendations) >= 1

    @patch("pipeline.narrative_generator.anthropic.Anthropic")
    def test_grounding_no_invented_numbers(self, mock_anthropic, sample_insight_payload, mock_claude_response):
        """Every number in the narrative must exist in the input payload."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=json.dumps(mock_claude_response))]
        )
        mock_anthropic.return_value = mock_client

        generator = NarrativeGenerator(provider="anthropic", model="claude-sonnet-4-5-20241022")
        report = generator.generate(sample_insight_payload)

        # Extract all numbers from the narrative text
        import re
        narrative_text = report.summary + " ".join(i.detail for i in report.key_insights)
        numbers_in_narrative = set(re.findall(r'[\d,]+\.?\d*', narrative_text))

        # All numbers must trace back to input payload
        payload_json = json.dumps(sample_insight_payload.__dict__, default=str)
        payload_numbers = set(re.findall(r'[\d,]+\.?\d*', payload_json))

        for num in numbers_in_narrative:
            clean_num = num.replace(",", "")
            assert clean_num in {n.replace(",", "") for n in payload_numbers}, \
                f"Number '{num}' in narrative not found in input payload — LLM invented data!"

    @patch("pipeline.narrative_generator.anthropic.Anthropic")
    def test_prompt_includes_grounding_context(self, mock_anthropic, sample_insight_payload):
        """Verify the prompt sent to Claude contains the stats payload."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text='{"summary":"test","key_insights":[],"anomalies":[],"recommendations":[],"data_quality_section":{"summary":"ok","defect_count":0}}')]
        )
        mock_anthropic.return_value = mock_client

        generator = NarrativeGenerator(provider="anthropic", model="claude-sonnet-4-5-20241022")
        generator.generate(sample_insight_payload)

        # Inspect what was sent to the API
        call_args = mock_client.messages.create.call_args
        user_message = call_args.kwargs["messages"][0]["content"]
        assert "125000.50" in user_message  # Revenue must be in context
        assert "47.32" in user_message       # Avg order value must be in context
        assert "12.5" in user_message        # Growth rate must be in context

    @patch("pipeline.narrative_generator.anthropic.Anthropic")
    def test_api_failure_raises_llm_provider_error(self, mock_anthropic, sample_insight_payload):
        """API failure after retries raises LLMProviderError, not generic Exception."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("Rate limited")
        mock_anthropic.return_value = mock_client

        generator = NarrativeGenerator(provider="anthropic", model="claude-sonnet-4-5-20241022")
        with pytest.raises(LLMProviderError) as exc_info:
            generator.generate(sample_insight_payload)
        assert exc_info.value.provider == "anthropic"
        assert exc_info.value.attempts == 3  # Verify retry happened

    @patch("pipeline.narrative_generator.anthropic.Anthropic")
    def test_fallback_to_secondary_provider(self, mock_anthropic, sample_insight_payload, mock_claude_response):
        """If primary provider fails, falls back to secondary."""
        mock_client = MagicMock()
        # First provider fails
        mock_client.messages.create.side_effect = [
            Exception("Rate limited"),
            Exception("Rate limited"),
            Exception("Rate limited"),
        ]
        mock_anthropic.return_value = mock_client

        generator = NarrativeGenerator(
            provider="anthropic",
            model="claude-sonnet-4-5-20241022",
            fallback_providers=[("openai", "gpt-4o-mini")]
        )
        # Should attempt fallback — test that fallback path is entered
        # (Full integration test would mock OpenAI too)
```

- _Source: [pytest-mock Tutorial](https://www.datacamp.com/tutorial/pytest-mock), [Python Agent Testing Best Practices](https://dasroot.net/posts/2026/02/python-agent-testing-best-practices-tools/), [Anthropic Structured Outputs with Instructor](https://python.useinstructor.com/integrations/anthropic/)_

#### B. Report Renderer Tests (docxtpl + Charts)

Tests verify that: (1) the docx template is populated correctly, (2) charts are embedded as images, (3) the output file is valid and contains expected sections.

```python
# tests/test_docx_renderer.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from docxtpl import DocxTemplate
from models.insight_report import InsightReport
from renderers.docx_renderer import DocxRenderer

@pytest.fixture
def sample_insight_report():
    """A complete InsightReport ready for rendering."""
    return InsightReport(
        data_quality_section={"summary": "2 minor issues detected.", "defect_count": 2},
        summary="Revenue grew 12.5% to $125K across 2,643 orders.",
        key_insights=[
            {"title": "Ad-revenue link", "detail": "0.87 Pearson correlation.", "confidence": "high"},
        ],
        anomalies=[
            {"title": "Outlier order", "detail": "Row 142: $9,999.99.", "severity": "medium"},
        ],
        recommendations=[
            {"title": "Scale ad spend", "detail": "Strong correlation supports ROI.", "priority": "high"},
        ],
    )

@pytest.fixture
def template_path(tmp_path):
    """Create a minimal docx template for testing."""
    from docxtpl import DocxTemplate
    from docx import Document
    doc = Document()
    doc.add_paragraph("{{ summary }}")
    doc.add_paragraph("{% for insight in key_insights %}{{ insight.title }}{% endfor %}")
    template_file = tmp_path / "test_template.docx"
    doc.save(str(template_file))
    return template_file

class TestDocxRenderer:

    def test_renders_valid_docx_file(self, sample_insight_report, template_path, tmp_path):
        """Output file exists and is a valid .docx."""
        renderer = DocxRenderer(template_path=template_path)
        output_path = tmp_path / "output_report.docx"
        renderer.render(sample_insight_report, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0
        # Verify it's a valid docx (actually a zip file)
        import zipfile
        assert zipfile.is_zipfile(str(output_path))

    def test_summary_appears_in_output(self, sample_insight_report, template_path, tmp_path):
        """The narrative summary text appears in the rendered document."""
        renderer = DocxRenderer(template_path=template_path)
        output_path = tmp_path / "output_report.docx"
        renderer.render(sample_insight_report, output_path)

        from docx import Document
        doc = Document(str(output_path))
        full_text = "\n".join(p.text for p in doc.paragraphs)
        assert "Revenue grew 12.5%" in full_text

    def test_insights_rendered_in_output(self, sample_insight_report, template_path, tmp_path):
        """Each key insight title appears in the rendered document."""
        renderer = DocxRenderer(template_path=template_path)
        output_path = tmp_path / "output_report.docx"
        renderer.render(sample_insight_report, output_path)

        from docx import Document
        doc = Document(str(output_path))
        full_text = "\n".join(p.text for p in doc.paragraphs)
        assert "Ad-revenue link" in full_text

    def test_chart_embedded_as_image(self, sample_insight_report, template_path, tmp_path):
        """Matplotlib chart is saved and embedded via InlineImage."""
        renderer = DocxRenderer(template_path=template_path)

        # Generate a chart and verify the temp image was created
        chart_path = renderer._generate_chart(
            data={"North": 52000, "South": 38000, "East": 35000},
            chart_type="bar",
            title="Revenue by Region",
            output_dir=tmp_path
        )
        assert Path(chart_path).exists()
        assert chart_path.endswith(".png")
        # Verify the image has non-zero size (valid PNG)
        assert Path(chart_path).stat().st_size > 1000  # A real chart is >1KB

    def test_empty_insights_renders_without_crash(self, template_path, tmp_path):
        """Report with zero insights still renders a valid document."""
        empty_report = InsightReport(
            data_quality_section={"summary": "Clean data.", "defect_count": 0},
            summary="No significant findings.",
            key_insights=[],
            anomalies=[],
            recommendations=[],
        )
        renderer = DocxRenderer(template_path=template_path)
        output_path = tmp_path / "empty_report.docx"
        renderer.render(empty_report, output_path)
        assert output_path.exists()

    def test_missing_template_raises_render_error(self, sample_insight_report, tmp_path):
        """Non-existent template path raises ReportRenderError."""
        from models.exceptions import ReportRenderError
        renderer = DocxRenderer(template_path=Path("/nonexistent/template.docx"))
        with pytest.raises(ReportRenderError):
            renderer.render(sample_insight_report, tmp_path / "output.docx")
```

- _Source: [docxtpl Docs](https://docxtpl.readthedocs.io/), [InlineImage Usage](https://snyk.io/advisor/python/docxtpl/functions/docxtpl.InlineImage)_

#### C. Monitoring Agent Tests (Threshold Breach Detection)

Tests verify: (1) pct_change calculation accuracy, (2) threshold breach detection, (3) alert message formatting, (4) edge cases (zero values, missing columns, identical periods).

```python
# tests/test_monitoring_agent.py
import pytest
import pandas as pd
import numpy as np
from agents.monitoring_agent import compare_periods, MetricAlert

@pytest.fixture
def current_period_df():
    return pd.DataFrame({
        "metric": ["revenue", "orders", "avg_order_value", "churn_rate"],
        "value": [125000, 2643, 47.32, 0.05],
    })

@pytest.fixture
def previous_period_df():
    return pd.DataFrame({
        "metric": ["revenue", "orders", "avg_order_value", "churn_rate"],
        "value": [100000, 2500, 40.00, 0.04],
    })

class TestComparePeriodsAccuracy:

    def test_pct_change_calculated_correctly(self, current_period_df, previous_period_df):
        """Verify percentage change math: (current - previous) / previous * 100."""
        alerts = compare_periods(current_period_df, previous_period_df, threshold=1.0)
        # Revenue: (125000 - 100000) / 100000 = 25%
        revenue_alert = next(a for a in alerts if a.metric == "revenue")
        assert abs(revenue_alert.pct_change - 25.0) < 0.01

    def test_threshold_breach_detected(self, current_period_df, previous_period_df):
        """Metrics exceeding ±15% default threshold generate alerts."""
        alerts = compare_periods(current_period_df, previous_period_df, threshold=0.15)
        alert_metrics = {a.metric for a in alerts}
        assert "revenue" in alert_metrics       # +25% > 15%
        assert "avg_order_value" in alert_metrics  # +18.3% > 15%
        assert "churn_rate" in alert_metrics     # +25% > 15%

    def test_within_threshold_no_alert(self, current_period_df, previous_period_df):
        """Metrics within threshold do NOT generate alerts."""
        alerts = compare_periods(current_period_df, previous_period_df, threshold=0.15)
        alert_metrics = {a.metric for a in alerts}
        assert "orders" not in alert_metrics  # +5.7% < 15%

    def test_custom_threshold_respected(self, current_period_df, previous_period_df):
        """Setting threshold to 30% filters out 25% changes."""
        alerts = compare_periods(current_period_df, previous_period_df, threshold=0.30)
        assert len(alerts) == 0  # Nothing exceeds 30%

    def test_negative_change_detected(self):
        """Decreasing metrics trigger alerts too."""
        current = pd.DataFrame({"metric": ["revenue"], "value": [80000]})
        previous = pd.DataFrame({"metric": ["revenue"], "value": [100000]})
        alerts = compare_periods(current, previous, threshold=0.15)
        assert len(alerts) == 1
        assert alerts[0].pct_change == pytest.approx(-20.0, abs=0.01)
        assert alerts[0].direction == "decreased"

class TestComparePeriodsEdgeCases:

    def test_zero_previous_value_no_division_error(self):
        """Zero in previous period doesn't crash with ZeroDivisionError."""
        current = pd.DataFrame({"metric": ["new_metric"], "value": [500]})
        previous = pd.DataFrame({"metric": ["new_metric"], "value": [0]})
        alerts = compare_periods(current, previous, threshold=0.15)
        assert len(alerts) == 1
        assert alerts[0].pct_change == float('inf') or alerts[0].detail == "New metric (was zero)"

    def test_both_zero_no_alert(self):
        """Zero in both periods = no change = no alert."""
        current = pd.DataFrame({"metric": ["dormant"], "value": [0]})
        previous = pd.DataFrame({"metric": ["dormant"], "value": [0]})
        alerts = compare_periods(current, previous, threshold=0.15)
        assert len(alerts) == 0

    def test_identical_periods_no_alerts(self, current_period_df):
        """Comparing period to itself produces zero alerts."""
        alerts = compare_periods(current_period_df, current_period_df, threshold=0.15)
        assert len(alerts) == 0

    def test_missing_metric_in_current_flagged(self, previous_period_df):
        """Metric in previous but not current generates a 'disappeared' alert."""
        current = pd.DataFrame({"metric": ["revenue"], "value": [125000]})
        alerts = compare_periods(current, previous_period_df, threshold=0.15)
        disappeared = [a for a in alerts if a.alert_type == "metric_disappeared"]
        assert len(disappeared) >= 1

    def test_new_metric_in_current_flagged(self, current_period_df):
        """Metric in current but not previous generates a 'new metric' alert."""
        previous = pd.DataFrame({"metric": ["revenue"], "value": [100000]})
        alerts = compare_periods(current_period_df, previous, threshold=0.15)
        new_alerts = [a for a in alerts if a.alert_type == "new_metric"]
        assert len(new_alerts) >= 1

    def test_nan_values_handled_gracefully(self):
        """NaN values don't crash — treated as missing data."""
        current = pd.DataFrame({"metric": ["revenue"], "value": [np.nan]})
        previous = pd.DataFrame({"metric": ["revenue"], "value": [100000]})
        alerts = compare_periods(current, previous, threshold=0.15)
        assert len(alerts) >= 1  # Should flag as issue, not crash

class TestAlertFormatting:

    def test_alert_message_human_readable(self, current_period_df, previous_period_df):
        """Alert output string is clear and actionable."""
        alerts = compare_periods(current_period_df, previous_period_df, threshold=0.15)
        revenue_alert = next(a for a in alerts if a.metric == "revenue")
        msg = str(revenue_alert)
        assert "revenue" in msg.lower()
        assert "25" in msg  # Percentage
        assert "increased" in msg.lower() or "↑" in msg
```

- _Source: [Metric-Based Alerting in Python](https://www.linkedin.com/pulse/metric-based-alerting-python-andrew-f-1e)_

#### D. Snapshot / Golden File Testing (Report JSON Baselines)

Snapshot testing captures the full pipeline JSON output and compares against a committed baseline. Any drift — new fields, changed values, missing sections — is caught automatically.

```python
# tests/test_pipeline_snapshots.py
import pytest
import json
from pathlib import Path
from pipeline.orchestrator import run_full_pipeline
from pipeline.config import PipelineConfig

GOLDEN_DIR = Path(__file__).parent / "golden_files"

@pytest.fixture
def deterministic_config():
    """Config that produces reproducible output (fixed seed, mocked LLM)."""
    return PipelineConfig(
        analysis_type="descriptive",
        llm_provider="mock",  # Uses canned LLM response, no API call
        output_format="json",
        random_seed=42,
    )

@pytest.fixture
def standard_test_csv(tmp_path):
    """A fixed CSV file that never changes — the baseline input."""
    import pandas as pd
    df = pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=50),
        "revenue": [1000 + i * 10 for i in range(50)],
        "region": ["North"] * 25 + ["South"] * 25,
        "orders": [20 + i for i in range(50)],
    })
    path = tmp_path / "standard_test.csv"
    df.to_csv(path, index=False)
    return path

class TestPipelineSnapshots:

    def test_quality_report_matches_golden(self, standard_test_csv, deterministic_config):
        """Data quality report output matches committed baseline."""
        result = run_full_pipeline(str(standard_test_csv), deterministic_config)
        actual = json.loads(result.quality_report.to_json())

        golden_path = GOLDEN_DIR / "quality_report_standard.json"
        if not golden_path.exists():
            # First run: create the golden file (run pytest --update-golden)
            golden_path.parent.mkdir(parents=True, exist_ok=True)
            golden_path.write_text(json.dumps(actual, indent=2, default=str))
            pytest.skip("Golden file created — re-run to validate")

        expected = json.loads(golden_path.read_text())
        assert actual == expected, (
            f"Quality report drifted from golden file.\n"
            f"Diff: {_json_diff(expected, actual)}\n"
            f"Run pytest --update-golden to accept new baseline."
        )

    def test_insight_payload_matches_golden(self, standard_test_csv, deterministic_config):
        """Computed insight stats match committed baseline."""
        result = run_full_pipeline(str(standard_test_csv), deterministic_config)
        actual = json.loads(result.insight_payload.to_json())

        golden_path = GOLDEN_DIR / "insight_payload_standard.json"
        if not golden_path.exists():
            golden_path.parent.mkdir(parents=True, exist_ok=True)
            golden_path.write_text(json.dumps(actual, indent=2, default=str))
            pytest.skip("Golden file created — re-run to validate")

        expected = json.loads(golden_path.read_text())

        # Float comparison with tolerance for platform differences
        _assert_json_approx_equal(expected, actual, rel_tol=1e-6)


def _json_diff(expected, actual, path=""):
    """Utility: find first difference between two JSON-like dicts."""
    diffs = []
    if type(expected) != type(actual):
        return [f"{path}: type {type(expected).__name__} vs {type(actual).__name__}"]
    if isinstance(expected, dict):
        for key in set(list(expected.keys()) + list(actual.keys())):
            if key not in expected:
                diffs.append(f"{path}.{key}: MISSING in expected")
            elif key not in actual:
                diffs.append(f"{path}.{key}: MISSING in actual")
            else:
                diffs.extend(_json_diff(expected[key], actual[key], f"{path}.{key}"))
    elif isinstance(expected, list):
        for i in range(max(len(expected), len(actual))):
            if i >= len(expected):
                diffs.append(f"{path}[{i}]: MISSING in expected")
            elif i >= len(actual):
                diffs.append(f"{path}[{i}]: MISSING in actual")
            else:
                diffs.extend(_json_diff(expected[i], actual[i], f"{path}[{i}]"))
    elif expected != actual:
        diffs.append(f"{path}: {expected!r} → {actual!r}")
    return diffs[:10]  # Limit to first 10 diffs


def _assert_json_approx_equal(expected, actual, rel_tol=1e-6, path=""):
    """Assert JSON equality with float tolerance."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        assert set(expected.keys()) == set(actual.keys()), f"Key mismatch at {path}"
        for key in expected:
            _assert_json_approx_equal(expected[key], actual[key], rel_tol, f"{path}.{key}")
    elif isinstance(expected, list) and isinstance(actual, list):
        assert len(expected) == len(actual), f"Length mismatch at {path}"
        for i, (e, a) in enumerate(zip(expected, actual)):
            _assert_json_approx_equal(e, a, rel_tol, f"{path}[{i}]")
    elif isinstance(expected, float) and isinstance(actual, float):
        assert abs(expected - actual) <= rel_tol * max(abs(expected), abs(actual), 1.0), \
            f"Float mismatch at {path}: {expected} vs {actual}"
    else:
        assert expected == actual, f"Mismatch at {path}: {expected!r} vs {actual!r}"
```

- _Source: [pytest-regressions Golden File Testing 2025](https://johal.in/pytest-regressions-data-golden-file-updates-2025/), [Syrupy Snapshot Testing](https://til.simonwillison.net/pytest/syrupy), [Snapshot Testing in Python](https://dev.to/metahris/snapshot-testing-in-python-with-pytest-verify-1bgo)_

#### E. Pandera Schema Tests (Edge Case Validation)

Tests verify that Pandera schemas correctly accept valid data and reject invalid data across edge cases. Pandera integrates with Hypothesis for property-based test generation from schema definitions.

```python
# tests/test_data_quality_schemas.py
import pytest
import pandas as pd
import numpy as np
import pandera as pa
from pandera import Check, Column, DataFrameSchema
from pipeline.data_quality import get_input_schema, assess_data_quality
from pipeline.config import PipelineConfig

@pytest.fixture
def default_config():
    return PipelineConfig(
        quality_thresholds={"max_null_pct": 50.0, "max_duplicate_pct": 20.0},
    )

class TestSchemaAcceptsValidData:

    def test_clean_numeric_csv_passes(self, default_config):
        """Standard clean DataFrame passes all schema checks."""
        df = pd.DataFrame({
            "date": pd.date_range("2026-01-01", periods=100),
            "revenue": np.random.uniform(100, 5000, 100),
            "region": np.random.choice(["North", "South"], 100),
        })
        report = assess_data_quality(df, default_config)
        assert report.has_critical_issues is False
        assert report.overall_score > 80

    def test_single_row_passes(self, default_config):
        """A single-row DataFrame doesn't crash and produces a valid report."""
        df = pd.DataFrame({"value": [42], "label": ["test"]})
        report = assess_data_quality(df, default_config)
        assert report.has_critical_issues is False

    def test_all_numeric_no_categorical(self, default_config):
        """DataFrame with only numeric columns produces valid report."""
        df = pd.DataFrame({"a": range(50), "b": range(50, 100), "c": np.random.rand(50)})
        report = assess_data_quality(df, default_config)
        assert report.has_critical_issues is False

    def test_all_categorical_no_numeric(self, default_config):
        """DataFrame with only string columns produces valid report (no correlation crash)."""
        df = pd.DataFrame({"name": ["Alice"] * 50, "city": ["NYC", "LA"] * 25})
        report = assess_data_quality(df, default_config)
        assert report.has_critical_issues is False

class TestSchemaRejectsInvalidData:

    def test_empty_dataframe_halts(self, default_config):
        """Empty DataFrame triggers critical halt."""
        df = pd.DataFrame()
        report = assess_data_quality(df, default_config)
        assert report.has_critical_issues is True
        assert "empty" in report.halt_reason.lower()

    def test_all_null_column_flags_critical(self, default_config):
        """Column that is 100% null flagged as critical defect."""
        df = pd.DataFrame({"good_col": range(100), "bad_col": [None] * 100})
        report = assess_data_quality(df, default_config)
        null_defect = next(d for d in report.defects if "bad_col" in d.affected_columns)
        assert null_defect.severity == "critical"
        assert null_defect.percentage == 100.0

    def test_majority_null_key_column_halts(self, default_config):
        """Column with >50% nulls triggers pipeline halt."""
        df = pd.DataFrame({
            "revenue": [None] * 60 + [100.0] * 40,
            "region": ["North"] * 100,
        })
        report = assess_data_quality(df, default_config)
        assert report.has_critical_issues is True

    def test_mixed_types_in_column_flagged(self, default_config):
        """Column with mixed types (int + str) detected as schema inconsistency."""
        df = pd.DataFrame({"value": [1, 2, "three", 4, "five"] * 20})
        report = assess_data_quality(df, default_config)
        schema_defects = [d for d in report.defects if d.defect_type == "schema_inconsistency"]
        assert len(schema_defects) >= 1

    def test_zero_variance_column_flagged(self, default_config):
        """Column with identical values flagged as statistical red flag."""
        df = pd.DataFrame({"constant": [42] * 100, "varying": range(100)})
        report = assess_data_quality(df, default_config)
        stat_defects = [d for d in report.defects if d.defect_type == "statistical_anomaly"]
        flagged_cols = [col for d in stat_defects for col in d.affected_columns]
        assert "constant" in flagged_cols

    def test_extreme_cardinality_flagged(self, default_config):
        """Column where every value is unique flagged as suspicious cardinality."""
        df = pd.DataFrame({"id": range(1000), "value": np.random.rand(1000)})
        report = assess_data_quality(df, default_config)
        stat_defects = [d for d in report.defects if d.defect_type == "statistical_anomaly"]
        flagged_cols = [col for d in stat_defects for col in d.affected_columns]
        assert "id" in flagged_cols

    def test_duplicate_rows_detected(self, default_config):
        """100% duplicate rows flagged and counted."""
        row = {"a": 1, "b": "x", "c": 3.14}
        df = pd.DataFrame([row] * 100)
        report = assess_data_quality(df, default_config)
        dup_defects = [d for d in report.defects if d.defect_type == "duplicate"]
        assert len(dup_defects) >= 1
        assert dup_defects[0].count == 99  # 99 duplicates of 1 original

class TestSchemaPropertyBased:

    @pytest.mark.slow
    def test_hypothesis_generated_data_passes_schema(self):
        """Pandera-generated synthetic data always passes its own schema.
        Uses Hypothesis property-based testing to auto-generate edge cases."""
        schema = DataFrameSchema({
            "revenue": Column(float, Check.greater_than(0), nullable=False),
            "orders": Column(int, Check.greater_than_or_equal_to(0), nullable=False),
            "region": Column(str, Check.isin(["North", "South", "East"]), nullable=False),
        })
        # Pandera generates DataFrames that satisfy the schema
        # Hypothesis will try many edge cases automatically
        from pandera import hypotheses
        strategy = schema.strategy(size=50)

        from hypothesis import given, settings
        @given(df=strategy)
        @settings(max_examples=20)
        def check(df):
            schema.validate(df)  # Must not raise

        check()
```

- _Source: [Pandera Data Synthesis Strategies](https://pandera.readthedocs.io/en/stable/data_synthesis_strategies.html), [Pandera Custom Checks](https://pandera.readthedocs.io/en/stable/checks.html), [pytest-pandera Plugin](https://github.com/pandera-dev/pytest-pandera), [Pandera with Hypothesis](https://khuyentran1401.github.io/reproducible-data-science/testing_data/pandera.html)_

#### Updated Test Count Estimate

| Test Category | Count | Coverage Target |
|---------------|-------|-----------------|
| Data Quality unit tests (Section E) | 12-15 | Schema accepts/rejects, edge cases, property-based |
| Narrative Generator tests (Section A) | 5-7 | Mocked API, grounding verification, fallback paths |
| Report Renderer tests (Section B) | 5-7 | Template population, chart embedding, empty reports |
| Monitoring Agent tests (Section C) | 10-12 | pct_change accuracy, threshold breach, edge cases, formatting |
| Snapshot / Golden File tests (Section D) | 2-4 | Quality report baseline, insight payload baseline |
| Pipeline Integration tests (existing) | 3-5 | Stage chaining, halt-on-critical, full run |
| CLI E2E tests (existing) | 2-3 | Reporting agent, monitoring agent |
| **Total** | **39-53** | **≥80% coverage on new code** |

### Cost Analysis — LLM Usage

**Claude API pricing (current 2026):**

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Best For |
|-------|----------------------|------------------------|----------|
| Haiku 4.5 | $1.00 | $5.00 | High-volume reports, cost-sensitive |
| Sonnet 4.6 | $3.00 | $15.00 | Balanced quality/cost (recommended default) |
| Opus 4.6 | $5.00 | $25.00 | Premium narrative quality |

**Estimated cost per report:**
- Input context (quality report + stats JSON): ~2,000-5,000 tokens
- Output (narrative report): ~1,500-3,000 tokens
- **Per report at Sonnet 4.6: ~$0.01–$0.06** (negligible)
- **Per report at Haiku 4.5: ~$0.002–$0.02** (even cheaper)

**Cost optimization tips:**
- Use **Prompt Caching** (90% discount on cache hits) if running multiple reports on similar data schemas — the system prompt and report template instructions cache across calls
- Use **Batch API** (50% discount) if generating reports in bulk rather than one-at-a-time
- Start with Haiku 4.5 for development/testing; switch to Sonnet for production narrative quality
- _Source: [Claude API Pricing 2026](https://platform.claude.com/docs/en/about-claude/pricing), [Full Cost Breakdown](https://nicolalazzari.ai/articles/claude-api-pricing-breakdown-2026), [Pricing Calculator](https://invertedstone.com/calculators/claude-pricing)_

### Dependency Management

**New dependencies to add to `requirements.txt`:**

```
# Data Quality
pandera>=0.19.0         # DataFrame schema validation

# Report Generation
docxtpl>=0.20.0         # Jinja2 Word templates
weasyprint>=62.0        # HTML/CSS → PDF (optional, Phase 3+)

# CLI
typer[all]>=0.12.0      # CLI framework with rich output

# Logging
structlog>=24.2.0       # Structured JSON logging

# Already installed (verify versions):
# anthropic              # Claude API — update to latest for structured outputs
# pandas>=2.0            # Core data processing
# matplotlib             # Chart generation
# seaborn                # Statistical visualization
# scikit-learn           # ML analytics (existing)
# pydantic>=2.8          # Contract schemas + structured outputs
```

**Total new dependency footprint:** 4 packages (pandera, docxtpl, typer, structlog) + 1 optional (weasyprint). All are well-maintained, actively developed, and have no conflicting transitive dependencies with the existing stack.

### Risk Assessment and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Claude API rate limiting during demo | LOW | HIGH | Provider fallback chain (OpenAI → Gemini); cache system prompt; Batch API for bulk runs |
| docxtpl template complexity exceeds Jinja2 capabilities | LOW | MEDIUM | Keep templates simple — complex formatting handled in Word, not in code. Fallback: raw python-docx for edge cases |
| Pandera validation too strict/too loose for real data | MEDIUM | LOW | Start with permissive schemas; tighten based on real data feedback. Log all validation failures for tuning |
| LibreOffice headless PDF conversion fidelity issues | MEDIUM | MEDIUM | Test with actual branded template early in Phase 3. Fallback: WeasyPrint with separate HTML template |
| Existing `comprehensive_analytics.py` lacks time-trend support | CERTAIN | MEDIUM | Phase 2 planned extension — add `compute_growth_rate()` and `detect_trends()` methods. Scope: 50-100 LOC |
| No tests → regression risk during adaptation of existing code | HIGH | HIGH | Phase 1 starts with test fixtures + data quality unit tests. Never adapt existing code without test coverage first |

### Success Metrics

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Data Quality Assessment completeness | Detects all 6 defect categories (missing, duplicate, schema, formatting, statistical, referential) | Unit tests per category with crafted dirty DataFrames |
| Pipeline halt accuracy | Correctly halts on >50% nulls, empty dataset; passes on clean data | Integration test with critical and non-critical fixtures |
| Report generation time | < 30 seconds for 10K row dataset (excluding LLM latency) | Timed integration test; LLM call mocked for benchmarking |
| LLM narrative quality | Grounded — no invented numbers; all stats traceable to input payload | Manual review of 5 sample reports; automated check that all numbers in narrative exist in input JSON |
| Report formatting | Branded docx opens correctly in Word/LibreOffice; PDF renders all sections | Visual inspection + automated check for expected sections in output file |
| CLI usability | `--help` produces clear usage; invalid input produces actionable error message | Typer CliRunner E2E test for success and error paths |
| Test coverage | ≥80% on new code (pipeline/, models/, agents/, renderers/) | pytest-cov report |

---

## Technical Debt Assessment

### Audit Summary

A comprehensive code-level audit of all backend modules identified **8 BLOCKER, 7 HIGH, 5 MEDIUM, and 1 LOW** severity issues across the existing codebase. The full issue inventory is documented below.

### Verdict: ✅ PROCEED — Debt is Manageable With Conditions

The debt is real but **does not block the Insights & Agents layer build**. Here's why:

The new layer is **CLI-based and bypasses the web layer entirely**. The worst debt clusters in `main.py` and `main_enhanced.py` — code the CLI agents will never call. The pipeline imports directly from `advanced_pipeline.py`, `comprehensive_analytics.py`, and `nlp_processor.py`, skipping the HTTP/state/auth/CORS surface.

**Debt that DOES NOT affect the new CLI layer (web-only):**

| Issue | Severity | Why It Doesn't Block |
|-------|----------|---------------------|
| Global `DATA_STORAGE` dict — race conditions | BLOCKER | CLI passes DataFrames directly, never touches DATA_STORAGE |
| CORS `allow_origins=["*"]` | BLOCKER | CLI has no HTTP layer |
| Hardcoded Supabase credentials | BLOCKER | CLI doesn't authenticate via Supabase — uses local files |
| No file upload validation (size/type) | HIGH | CLI reads files via `pd.read_csv()` directly |
| Error stack traces exposed to HTTP clients | HIGH | CLI controls its own error output |
| Auth validation incomplete | MEDIUM | CLI has no auth |

**Debt that DOES affect the new CLI layer (must fix):**

| Issue | Severity | File | Fix Effort | When to Fix |
|-------|----------|------|-----------|-------------|
| `warnings.filterwarnings('ignore')` | BLOCKER | advanced_pipeline.py:10, comprehensive_analytics.py:17 | 5 min | Phase 1 Day 1 — remove line, replace with targeted `warnings.catch_warnings()` context manager where needed |
| Silent `except Exception: pass` on datetime parsing | BLOCKER | advanced_pipeline.py:65, 201 | 15 min | Phase 1 Day 1 — add logging, catch specific `ValueError`/`TypeError` |
| Empty DataFrame crash in `profile_data()` | BLOCKER | advanced_pipeline.py:56 | 10 min | Phase 1 Day 1 — add `if df.empty: return empty_profile()` guard |
| Greedy JSON regex `r'\{.*\}'` with `re.DOTALL` | BLOCKER | nlp_processor.py:167 | 20 min | Phase 2 — replace with `json.loads()` attempt on full response, fallback to bracket-matching parser |
| Hardcoded model versions (`claude-3-haiku-20240307`, `gpt-4o-mini`, `gemini-pro`) | BLOCKER | nlp_processor.py:135, 147, 156 | 15 min | Phase 2 — move to `PipelineConfig` with defaults, overridable via CLI |
| NaN/Inf in JSON output from analytics | HIGH | comprehensive_analytics.py:50-61 | 20 min | Phase 1 — add `_sanitize_float()` helper: `float('nan') → None`, `float('inf') → None` |
| Correlation crash on constant/categorical-only columns | HIGH | comprehensive_analytics.py:99-108, 162-167 | 30 min | Phase 2 — add variance check before correlation, validate groups non-empty before t-test |
| KNN imputation crash on single numeric column | HIGH | advanced_pipeline.py:188 | 5 min | Phase 1 — add `if len(numeric_cols) < 2: skip KNN` guard |
| No timeout on LLM API calls | HIGH | nlp_processor.py:134-159 | 10 min | Phase 2 — add `timeout=30` parameter to all provider calls |
| API key stored in instance variable (logging risk) | HIGH | nlp_processor.py:32-37 | 15 min | Phase 2 — load from env at call time, don't persist on instance |
| No version pinning in requirements.txt | MEDIUM | requirements.txt | 20 min | Phase 1 Day 1 — pin all current versions |
| Module-level singletons (can't mock for tests) | MEDIUM | cleaner.py:4, analytics.py:6-8 | 15 min | Phase 1 — refactor to factory functions |
| Isolation Forest silently removes ~10% of rows | MEDIUM | advanced_pipeline.py:192 | 10 min | Phase 1 — add logging with row count before/after |
| Memory waste from unnecessary DataFrame copies | MEDIUM | advanced_pipeline.py:156, 169, 184, 196 | 30 min | Phase 3 — optimize when performance-testing large datasets |

### Total Fix Effort for CLI-Affecting Debt

| Priority | Issues | Estimated Effort |
|----------|--------|-----------------|
| Phase 1 Day 1 (must-do before ANY development) | 6 issues | ~1.5 hours |
| Phase 2 (fix when adapting the module) | 6 issues | ~2 hours |
| Phase 3 (performance optimization) | 2 issues | ~1 hour |
| **Total** | **14 issues** | **~4.5 hours** |

**4.5 hours of remediation across the entire build.** That's a rounding error on a 4-5 week project.

### Immediate Action Required (Separate from Build)

⚠️ **Supabase key rotation** — The hardcoded credentials in `main_enhanced.py:47-48` are a security incident regardless of the Insights layer. The anon key and project URL are in source code. If this repo is or has ever been public, **rotate the keys immediately** and move to environment-only variables with no defaults. This is not a build blocker but it IS an urgent security task.

### Impact on Reuse Assessment (Updated)

The original reuse assessment rated modules at 15-100% reusable. After the debt audit, the ratings hold with one adjustment:

| Module | Original Rating | Post-Debt Rating | Change |
|--------|----------------|-------------------|--------|
| `cleaner.py` | 100% reuse | **95% reuse** | Module singleton needs factory refactor |
| `advanced_pipeline.py` | 60% reuse | **55% reuse** | Empty DataFrame guard + warning fix needed before reuse |
| `comprehensive_analytics.py` | 55% reuse | **50% reuse** | NaN sanitization + constant-column guard needed |
| `nlp_processor.py` | 40% reuse | **35% reuse** | Regex fix + model config + timeout all needed |
| `analytics.py` | 20% reuse | **20% reuse** | No change — already planned for deprecation |
| `main.py` / `main_enhanced.py` | 15% reuse | **15% reuse** | No change — CLI bypasses entirely |

**Net impact: ~5% reduction in reuse rate.** The debt adds ~4.5 hours of remediation but does not change the architecture, technology choices, or phased roadmap.

### Verdict Rationale

Proceeding is justified because:

1. **The worst debt is in code the CLI layer doesn't touch** — DATA_STORAGE, CORS, auth, upload validation are web-only concerns
2. **CLI-affecting debt is shallow** — guards, logging, config extraction — not architectural rewrites
3. **Total fix effort is ~4.5 hours** spread across the build phases, not front-loaded
4. **Phase 1 already mandates "write tests before adapting"** — every fix will be test-covered
5. **The architecture isolates new code from old** — `pipeline/`, `models/`, `agents/`, `renderers/` are new directories with no inheritance from debt-laden modules; they import specific functions, not whole classes

**The one condition:** Phase 1 Day 1 must include the 6 must-fix items (~1.5 hours) before ANY development begins. These are the guards that prevent crashes during basic pipeline operation.

---

## Research Synthesis

### Executive Summary

This research establishes the complete technical blueprint for shipping a working **Insights & Agents layer** on the SavvyCleanse ETL pipeline — a system that ingests structured datasets, runs automated data quality assessment, computes analytics, generates LLM-grounded narrative reports, and outputs professionally branded docx/PDF deliverables. All agents are built from scratch in Python with no orchestration frameworks.

The existing codebase provides a strong foundation: `DataCleaner.profile_data()`, `DescriptiveAnalytics.statistical_summary()`, `DiagnosticAnalytics.correlation_analysis()`, and the multi-LLM provider pattern in `nlp_processor.py` are directly reusable or adaptable. The overall code reuse rate across the five backend modules ranges from 15% (API endpoints) to 100% (cleaner.py), averaging approximately 50%. The remaining 50% — quality assessment logic, pipeline orchestration, report rendering, CLI agents, and the monitoring agent — must be built new.

The recommended technology stack adds only four required dependencies (pandera, docxtpl, typer, structlog) to the existing Python/FastAPI/pandas foundation. Claude API Structured Outputs provide guaranteed-schema narrative generation at ~$0.01–$0.06 per report. The entire system is achievable in 4-5 weeks using vertical-slice phased delivery, with each phase producing a runnable demo increment.

**Key Technical Findings:**

- **Architecture: Pipes and Filters** — Linear pipeline of pure Python functions with Pydantic contract enforcement at every stage boundary. No shared mutable state, no framework overhead. Eliminates the existing `DATA_STORAGE` in-memory anti-pattern.
- **Data Quality: Pandera + custom checks** — Pandera handles structural schema validation; custom Python extends detection to formatting issues, statistical red flags, and referential gaps. `ExceptionGroup` collects ALL defects rather than failing fast.
- **LLM Narrative: Claude Structured Outputs** — Stats computed by pandas are passed as grounding context; Claude generates narrative sections validated against a Pydantic schema on the first response. Provider fallback chain (Claude → OpenAI → Gemini) provides resilience.
- **Report Rendering: docxtpl + LibreOffice headless** — Branded Word template designed in Microsoft Word, filled programmatically via Jinja2. Charts rendered by matplotlib and embedded as images. PDF generated via LibreOffice headless conversion from the same template.
- **Error Handling: Dual strategy** — Result pattern (`PipelineResult`) for expected business outcomes (halt-on-critical, warnings). Custom exception hierarchy (`SavvyCleanseError` tree) for unexpected failures. `try/except/else/finally` applied precisely: `else` separates success-path logic from error handling; `finally` guarantees cleanup.
- **No existing tests** — Highest single risk. Mitigated by building test fixtures in Phase 1 before adapting any existing code.
- **Technical debt is manageable** — 8 BLOCKERs found, but 3 are web-only (CLI bypasses). The 5 CLI-affecting BLOCKERs total ~1.5 hours of Day 1 fixes (empty DataFrame guards, warning suppression removal, JSON regex fix, model config extraction). Full remediation: ~4.5 hours across the build.

**Strategic Recommendations:**

1. **Start with models/** — Define all Pydantic contracts first. They serve as the specification for every stage and the LLM output schema.
2. **Write tests before adapting code** — The existing `comprehensive_analytics.py` and `nlp_processor.py` need modification. Cover them with tests first.
3. **Use Haiku 4.5 for development, Sonnet 4.6 for demos** — 10x cheaper iteration; switch model at runtime via config.
4. **Keep the FastAPI web UI untouched** — New CLI agents import from `pipeline/` and `models/` directly. The web UI and CLI coexist without conflict.
5. **Design the docx template early** — It drives the report structure. Don't code the renderer until the template is finalized in Word.

### Table of Contents (Document Navigation)

1. **Technical Research Scope Confirmation** — Research goals, constraints, methodology
2. **Technology Stack Analysis** — Library evaluation for each component (Pandera, docxtpl, WeasyPrint, Claude API, Typer, structlog)
3. **Integration Patterns Analysis** — Pipeline stage composition, JSON contracts, LLM grounding pattern, CLI integration, report rendering workflow
4. **Existing Code Reuse Assessment** — Module-by-module analysis with reuse/adapt/new classification and code quality issues
5. **Tech Stack Feasibility Verdict** — All requirements mapped to confirmed capabilities
6. **Architectural Patterns and Design** — Pipes and Filters pattern, three-layer separation, Strategy pattern, project structure, error handling architecture, logging
7. **Python Error Handling Constructs** — try/except/else/finally evaluation, ExceptionGroup/except*, Result pattern, custom exception hierarchy — all mapped to specific pipeline locations
8. **Implementation Approaches** — Phased roadmap (4-5 weeks), testing strategy (pyramid + fixtures + CliRunner), cost analysis, dependency management, risk assessment, success metrics
9. **Technical Debt Assessment** — Full audit (8 BLOCKER, 7 HIGH, 5 MEDIUM), CLI-impact triage, fix effort estimates, proceed/no-proceed verdict
10. **Research Synthesis** — Executive summary, strategic recommendations, industry context

### Industry Context

This project aligns with a significant 2026 enterprise trend: **AI-driven insight automation**. According to IBM and TDWI, organizations are increasingly building automated analytics pipelines that combine traditional statistical computation with LLM narrative generation. The ETL tools market reached $7.63 billion in 2026, with Python maintaining dominance in enterprise data pipeline deployments. The SavvyCleanse approach — grounding LLM output in pre-computed statistics rather than allowing independent computation — follows the emerging best practice of "verified insight generation" that prevents hallucination in analytics reporting.
- _Source: [IBM Data Trends 2026](https://www.ibm.com/think/news/biggest-data-trends-2026), [TDWI 2026 Predictions](https://tdwi.org/articles/2026/01/14/adv-all-tdwi-2026-ai-data-fellow-predictions.aspx), [Python ETL Framework Trends](https://www.integrate.io/blog/python-etl-framework-usage-trends/), [Data Engineering Trends 2026](https://www.trigyn.com/insights/data-engineering-trends-2026-building-foundation-ai-driven-enterprises)_

### Source Documentation

**Technology Sources:**
- [Pandera Documentation](https://pandera.readthedocs.io/en/stable/dataframe_schemas.html) | [Pandera SciPy Proceedings](https://proceedings.scipy.org/articles/gerudo-f2bc6f59-010)
- [docxtpl Documentation](https://docxtpl.readthedocs.io/) | [docxtpl PyPI](https://pypi.org/project/docxtpl/)
- [Claude API Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) | [Hands-On Guide](https://towardsdatascience.com/hands-on-with-anthropics-new-structured-output-capabilities/)
- [Typer Documentation](https://typer.tiangolo.com/tutorial/testing/) | [Click vs Typer Guide](https://devtoolbox.dedyn.io/blog/python-click-typer-cli-guide)
- [structlog Documentation](https://blog.naveenpn.com/pythons-structlog-modern-structured-logging-for-clean-json-ready-logs)
- [WeasyPrint vs ReportLab](https://dev.to/claudeprime/generate-pdfs-in-python-weasyprint-vs-reportlab-ifi) | [PDF Libraries Compared](https://templated.io/blog/generate-pdfs-in-python-with-libraries/)

**Architecture Sources:**
- [Pipes and Filters Pattern](https://techshitanshu.com/pipes-and-filters-pattern-architecture/) | [Pipeline Pattern in Python](https://pybit.es/articles/a-practical-example-of-the-pipeline-pattern-in-python/)
- [Design Patterns for Data Pipelines](https://amsayed.medium.com/coding-data-pipeline-design-patterns-in-python-44a705f0af9e)
- [Pydantic v2 Docs](https://docs.pydantic.dev/latest/) | [Pydantic + Pandera Validation Pipeline](https://agentbus.sh/posts/how-to-build-data-validation-with-pydantic-and-pandera/)
- [pandas.DataFrame.pipe](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pipe.html)

**Error Handling Sources:**
- [PEP 654 – ExceptionGroup](https://peps.python.org/pep-0654/) | [ExceptionGroup Practical Guide](https://thelinuxcode.com/exception-groups-in-python-311-a-practical-guide-to-multi-error-handling/)
- [Result Types in Python](https://www.krython.com/tutorial/python/functional-error-handling-result-types) | [5 Patterns Beyond Try-Except](https://www.kdnuggets.com/5-error-handling-patterns-in-python-beyond-try-except)
- [Custom Exception Hierarchy](https://hrekov.com/blog/python-custom-exceptions)
- [AI Agent Error Handling](https://dev.to/nebulagg/ai-agent-error-handling-4-resilience-patterns-in-python-12of)

**Implementation Sources:**
- [pytest Data Pipeline Fixtures](https://medium.com/capital-fund-management/advanced-testing-techniques-for-your-python-data-pipeline-with-dask-and-pytest-fixtures-622064867ef8)
- [Integration Tests for Python Pipelines](https://www.startdataengineering.com/post/python-datapipeline-integration-test/)
- [Claude API Pricing 2026](https://platform.claude.com/docs/en/about-claude/pricing)

**Research Confidence Level:** HIGH — All technology recommendations verified against current documentation and multiple independent sources. All libraries confirmed actively maintained as of April 2026.

---

**Technical Research Completion Date:** 2026-04-09
**Research Period:** Comprehensive analysis with 2025-2026 source verification
**Source Verification:** All technical facts cited with current sources
**Confidence Level:** High — based on multiple authoritative technical sources

_This technical research document serves as the authoritative reference for implementing the SavvyCleanse Insights & Agents layer. It provides architecture blueprints, technology evaluations, code reuse maps, error handling patterns, and a phased implementation roadmap with testing strategy — everything needed to move directly into implementation planning._
