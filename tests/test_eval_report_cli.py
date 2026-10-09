"""`eval report` outputs: report.json always, --html charts and page, the auto-open rule and --verdicts (another judge's
verdicts, never mixed with judge.json). The JSON, chart and page builders are stubbed so these tests stand alone. No model calls."""
import json
import sys
import types

import pytest

import mockmcp.eval
from mockmcp.eval import grade, report
from test_eval_grade import make_run


def args(rd, **kw):
    return type("A", (), {"run_dir": rd, **kw})


@pytest.fixture
def stubs(monkeypatch):
    """Stand-ins for report_data.build, charts.render_all and report_html.render_html; records the calls."""
    calls = {"build": [], "charts": [], "html": [], "open": []}

    def build(rows, root, summary, verdict_source="judge.json"):
        calls["build"].append(verdict_source)
        return {"report_version": 1, "title": root.name, "verdict_source": verdict_source, "summary": summary,
                "runs": [{"run": r} for r in sorted({x["run"] for x in rows})],
                "tasks": [{"key": f"t{i}", "task_id": x["task_id"], "run": x["run"], "outcome": x["outcome"], "passed": x["passed"]}
                          for i, x in enumerate(rows)]}

    def render_all(rep):
        calls["charts"].append(rep)
        return {n: f'<svg class="mm-chart mm-{n}" data-chart="{n}"/>' for n in ("waffle", "outcomes", "effort")}

    def render_html(rep, charts):
        calls["html"].append(charts)
        return "<!doctype html>" + "".join(charts.values())

    for name, fns in (("report_data", {"build": build}), ("charts", {"render_all": render_all}),
                      ("report_html", {"render_html": render_html})):
        mod = types.ModuleType(f"mockmcp.eval.{name}")
        mod.__dict__.update(fns)
        monkeypatch.setitem(sys.modules, f"mockmcp.eval.{name}", mod)
        monkeypatch.setattr(mockmcp.eval, name, mod, raising=False)
    monkeypatch.setattr(report.webbrowser, "open", lambda url: calls["open"].append(url))
    return calls


def graded(tmp_path):
    rd = make_run(tmp_path)
    grade.grade_run(rd, None, workers=2)
    return rd


def test_report_json_always_written_and_no_html_by_default(tmp_path, stubs):
    rd = graded(tmp_path)
    report.main(args(rd))
    rep = json.loads((rd / "report.json").read_text())
    assert rep["summary"] == json.loads((rd / "summary.json").read_text())
    assert len(rep["tasks"]) == len(grade.read_jsonl(rd / "results.jsonl")) == 3
    assert not (rd / "report.html").exists() and not (rd / "charts").exists() and not stubs["charts"] and not stubs["open"]


def test_html_writes_charts_and_page_without_opening(tmp_path, stubs, capsys):
    rd = graded(tmp_path)
    (rd / "charts").mkdir()
    (rd / "charts" / "flow.svg").write_text("<svg/>")   # left over from an earlier grid report: must go
    report.main(args(rd, html=True, open=False))
    assert {p.name for p in (rd / "charts").iterdir()} == {"waffle.svg", "outcomes.svg", "effort.svg"}
    page = (rd / "report.html").read_text()
    assert 'data-chart="waffle"' in page and not stubs["open"]
    assert str(rd / "report.html") in capsys.readouterr().out
    report.main(args(rd, html=True, open=True))
    assert stubs["open"] == [(rd / "report.html").resolve().as_uri()]


def test_should_open_only_on_an_interactive_display(monkeypatch):
    assert report.should_open(True) and not report.should_open(False)
    monkeypatch.setattr(report.sys, "platform", "linux")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setattr(report.sys, "stdout", type("T", (), {"isatty": lambda self: False})())
    assert not report.should_open(None)   # not a TTY (tests, pipes)
    monkeypatch.setattr(report.sys, "stdout", type("T", (), {"isatty": lambda self: True})())
    assert report.should_open(None)
    monkeypatch.setenv("CI", "1")
    assert not report.should_open(None)
    monkeypatch.delenv("CI")
    monkeypatch.delenv("DISPLAY")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    assert not report.should_open(None)   # headless Linux
    monkeypatch.setattr(report.sys, "platform", "darwin")
    assert report.should_open(None)


def test_verdicts_reads_another_judge_and_never_mixes(tmp_path, stubs, capsys):
    rd = graded(tmp_path)
    report.main(args(rd))
    before = {f: (rd / f).read_bytes() for f in ("report.md", "summary.json", "report.json", "results.jsonl")}
    mtime = (rd / "results.jsonl").stat().st_mtime_ns
    # the other judge calls the clean task partial and claims it passed; the trap task has no verdict from it
    (rd / "slc-ok:1:Q1" / "judge.x.json").write_text(json.dumps(
        {"judge": "x", "verdict": {"outcome": "partial", "passed": True, "categories": ["incomplete"], "judge": {"backend": "x"}}}))
    (rd / "slc-fab:1:Q1" / "judge.x.json").write_text(json.dumps(
        {"judge": "x", "verdict": {"outcome": "pass", "categories": [], "judge": {"backend": "x", "cost_usd": 0.5}}}))
    report.main(args(rd, verdicts="x"))
    rep = json.loads((rd / "report.x.json").read_text())
    by = {t["task_id"]: t for t in rep["tasks"]}
    assert set(by) == {"slc-ok:1:Q1", "slc-fab:1:Q1"}   # the trap is left out, not filled in from judge.json
    assert by["slc-ok:1:Q1"]["outcome"] == "partial" and not by["slc-ok:1:Q1"]["passed"]   # passed recomputed by finish
    assert by["slc-fab:1:Q1"]["passed"] and rep["verdict_source"] == "judge.x.json"
    s = json.loads((rd / "summary.x.json").read_text())
    assert s == rep["summary"] and s["excluded"] == 1 and s["n"] == 2 and s["judge_cost_usd"] == 0.5
    assert "1 graded tasks without that file are left out" in (rd / "report.x.md").read_text()
    assert {f: (rd / f).read_bytes() for f in before} == before and (rd / "results.jsonl").stat().st_mtime_ns == mtime
    (rd / "results.jsonl").unlink()
    report.main(args(rd, verdicts="x"))
    assert not (rd / "results.jsonl").exists()   # --verdicts never writes results.jsonl
    assert report.main(args(rd, verdicts="nobody")) == 1 and "judge.nobody.json" in capsys.readouterr().out


def test_verdicts_html_outputs_are_suffixed(tmp_path, stubs):
    rd = graded(tmp_path)
    for tid in ("slc-ok:1:Q1", "slc-fab:1:Q1", "trap-missing_entity-1"):
        (rd / tid / "judge.x.json").write_text(json.dumps({"verdict": {"outcome": "pass"}}))
    report.main(args(rd, verdicts="x", html=True, open=False))
    assert (rd / "report.x.html").exists() and (rd / "charts.x" / "waffle.svg").exists()
    assert not (rd / "report.html").exists() and not (rd / "charts").exists() and not (rd / "summary.json").exists()


def test_report_json_on_grid_parent(tmp_path, stubs):
    for name in ("b5k", "b25k"):
        (tmp_path / name).mkdir()
        graded(tmp_path / name)
    report.main(args(tmp_path))
    rep = json.loads((tmp_path / "report.json").read_text())
    assert [r["run"] for r in rep["runs"]] == ["b25k", "b5k"] and len(rep["tasks"]) == 6


def test_html_end_to_end_with_real_builders(tmp_path):
    """The real report_data, charts and report_html modules together (skipped until they exist)."""
    for m in ("report_data", "charts", "report_html"):
        pytest.importorskip(f"mockmcp.eval.{m}")
    rd = graded(tmp_path)
    report.main(args(rd, html=True, open=False))
    rep = json.loads((rd / "report.json").read_text())
    assert rep["summary"] == json.loads((rd / "summary.json").read_text()) and len(rep["tasks"]) == 3
    assert (rd / "report.html").exists() and (rd / "charts" / "waffle.svg").exists()
