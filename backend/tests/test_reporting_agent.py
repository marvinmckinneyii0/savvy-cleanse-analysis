"""Tests for the Reporting Agent (Story 2.4).

Covers manual generate, drift-included pipeline (baseline present), first-run
(no baseline → no drift section), scheduled-job registration, and scheduled-run
error recovery. All file writes are scoped to ``tmp_path``; the LLM is not
called over the network (no provider key → deterministic fallback narrative).
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd
import pytest
import structlog
from apscheduler.triggers.interval import IntervalTrigger
from typer.testing import CliRunner

from backend.agents import reporting_agent as ra
from backend.models.pipeline_config import PipelineConfig
from backend.pipeline.drift_engine import DriftEngine
from backend.pipeline.orchestrator import OutputFormat

runner = CliRunner()


def _write_csv(path: Path, *, revenue_scale: float = 1.0) -> Path:
    """A clean 15-row sales CSV that passes DQA (no criticals)."""
    rows = 15
    df = pd.DataFrame(
        {
            "date": [f"2026-01-{i + 1:02d}" for i in range(rows)],
            "region": [["north", "south", "east", "west"][i % 4] for i in range(rows)],
            "revenue": [round((1000.0 + i * 25) * revenue_scale, 2) for i in range(rows)],
        }
    )
    df.to_csv(path, index=False)
    return path


def _write_config(tmp_path: Path, out_dir: Path, fmt: str = "docx") -> Path:
    cfg = tmp_path / "config.yaml"
    csv = out_dir  # not used; data_sources filled below
    cfg.write_text(
        "data_sources:\n"
        f"  - {(tmp_path / 'sales.csv').as_posix()}\n"
        "report_schedule:\n"
        "  interval: weekly\n"
        "output:\n"
        f"  format: {fmt}\n"
        f"  output_dir: {out_dir.as_posix()}\n"
        "alert_recipients:\n"
        "  - ops@example.com\n",
        encoding="utf-8",
    )
    return cfg


def _seed_baseline(baseline_dir: Path, dataset_key: str, base_df: pd.DataFrame) -> None:
    engine = DriftEngine(baseline_dir=baseline_dir)
    engine._save_baseline(dataset_key, engine._build_profile(base_df, dataset_key))


class TestDatasetKey:
    @pytest.mark.parametrize(
        "path,expected",
        [
            ("data/sales.csv", "sales"),
            ("/tmp/Weekly Sales.CSV", "weekly_sales"),
            ("...hidden.csv", "hidden"),
            ("data/2026-report.csv", "2026-report"),
        ],
    )
    def test_sanitizes_to_safe_key(self, path: str, expected: str) -> None:
        assert ra._dataset_key_from_path(path) == expected


class TestGenerate:
    def test_manual_generate_writes_report(self, tmp_path: Path) -> None:
        out_dir = tmp_path / "out"
        _write_csv(tmp_path / "sales.csv")
        cfg = _write_config(tmp_path, out_dir)

        result = runner.invoke(
            ra.app,
            [
                "generate",
                "--input", str(tmp_path / "sales.csv"),
                "--config", str(cfg),
                "--baseline-dir", str(tmp_path / "baselines"),
                "--format", "docx",
            ],
        )
        assert result.exit_code == 0, result.output
        written = list(out_dir.glob("sales_*.docx"))
        assert len(written) == 1

    def test_first_run_creates_baseline_and_omits_drift_section(self, tmp_path: Path) -> None:
        out_dir = tmp_path / "out"
        baselines = tmp_path / "baselines"
        _write_csv(tmp_path / "sales.csv")
        cfg = PipelineConfig.load(_write_config(tmp_path, out_dir))

        res = ra._run_once(cfg, tmp_path / "sales.csv", OutputFormat.docx, baseline_dir=baselines)

        assert res.drift_report is None  # no baseline existed → first run
        assert (baselines / "sales.json").exists()
        out_file = next(out_dir.glob("sales_*.docx"))
        doc_xml = zipfile.ZipFile(out_file).read("word/document.xml").decode("utf-8")
        assert "Drift Analysis" not in doc_xml

    def test_drift_included_when_baseline_exists(self, tmp_path: Path) -> None:
        out_dir = tmp_path / "out"
        baselines = tmp_path / "baselines"
        _write_csv(tmp_path / "sales.csv")  # revenue ~1000-1350
        cfg = PipelineConfig.load(_write_config(tmp_path, out_dir))

        # Seed a baseline whose revenue is ~40% lower → HIGH mean-shift drift.
        base_df = pd.read_csv(tmp_path / "sales.csv")
        base_df["revenue"] = (base_df["revenue"] / 1.4).round(2)
        _seed_baseline(baselines, "sales", base_df)

        res = ra._run_once(cfg, tmp_path / "sales.csv", OutputFormat.docx, baseline_dir=baselines)

        assert res.drift_report is not None
        assert res.drift_report.overall_severity.value == "high"
        out_file = next(out_dir.glob("sales_*.docx"))
        doc_xml = zipfile.ZipFile(out_file).read("word/document.xml").decode("utf-8")
        assert "Drift Analysis" in doc_xml


class TestHtmlTemplate:
    """Directly exercise the HTML/PDF template's Drift Analysis branch.

    Renders the Jinja template without WeasyPrint (whose native libs are often
    absent on Windows/CI) so the PDF-path drift section is still covered.
    """

    def _render(self, drift_report) -> str:
        from jinja2 import Environment, FileSystemLoader

        from backend.renderers.pdf_renderer import _TEMPLATE_PATH

        env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_PATH.parent)), autoescape=True
        )
        template = env.get_template(_TEMPLATE_PATH.name)
        return template.render(
            executive_summary="x",
            key_findings=[],
            anomaly_analysis=None,
            recommendations_narrative=None,
            metadata={"timestamp": "2026-07-08", "provider": "test"},
            fallback=False,
            fallback_reason="",
            drift_report=drift_report,
        )

    def test_drift_section_present_when_drift_report_set(self) -> None:
        from backend.models.drift_report import DriftReport, SchemaDrift, VolumeDrift
        from backend.models.quality_report import Severity

        dr = DriftReport(
            pipeline_run_id="r",
            computed_at="2026-07-08T00:00:00Z",
            volume_drift=VolumeDrift(current_row_count=1, baseline_row_count=1, pct_change=0.0),
            numeric_drift=[],
            categorical_drift=[],
            schema_drift=SchemaDrift(columns_added=[], columns_removed=[], dtype_changes={}),
            drift_summary="1 HIGH finding.",
            overall_severity=Severity.HIGH,
            recommendations=["Investigate revenue mean shift."],
        )
        html = self._render(dr)
        assert "Drift Analysis" in html
        assert "Investigate revenue mean shift." in html

    def test_drift_section_absent_when_none(self) -> None:
        assert "Drift Analysis" not in self._render(None)


class TestSchedule:
    def test_schedule_registers_job(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _write_csv(tmp_path / "sales.csv")
        cfg = _write_config(tmp_path, tmp_path / "out")

        class FakeScheduler:
            def __init__(self) -> None:
                self.jobs: list[dict] = []
                self.started = False

            def add_job(self, func, trigger=None, args=None, id=None):  # noqa: A002
                self.jobs.append({"func": func, "trigger": trigger, "args": args, "id": id})

            def start(self) -> None:
                self.started = True

        fake = FakeScheduler()
        monkeypatch.setattr(ra, "BlockingScheduler", lambda: fake)

        ra.schedule(config=cfg, baseline_dir=tmp_path / "baselines")

        assert fake.started
        assert len(fake.jobs) == 1
        assert isinstance(fake.jobs[0]["trigger"], IntervalTrigger)
        assert fake.jobs[0]["func"] is ra._scheduled_run

    def test_scheduled_run_recovers_from_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_csv(tmp_path / "sales.csv")
        cfg = _write_config(tmp_path, tmp_path / "out")

        def boom(*args, **kwargs):
            raise RuntimeError("pipeline exploded")

        monkeypatch.setattr(ra, "_run_once", boom)

        with structlog.testing.capture_logs() as captured:
            # Must NOT raise — the scheduler has to survive a failed run.
            ra._scheduled_run(cfg, baseline_dir=tmp_path / "baselines")

        events = [e for e in captured if e.get("event") == "scheduled_run_failed"]
        assert len(events) == 1
        assert events[0]["error"] == "RuntimeError"
