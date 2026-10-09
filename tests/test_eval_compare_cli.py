"""`eval compare` CLI: pairing (single runs, grids, unpaired runs, one-sided tasks), labels, --verdicts (never mixes judges),
outputs and the rule that nothing is ever written into A or B. compare_data / compare_charts / compare_html / charts are
stubbed so these tests stand alone; one end-to-end test uses the real modules once they exist. No model calls."""
import importlib.util
import json
import os
import sys
import types

import pytest

import mockmcp.eval
from mockmcp.eval import compare, grade, report
from test_eval_grade import make_run


def args(a, b, **kw):
    return type("A", (), {"a_dir": a, "b_dir": b, "out": None, **kw})


def _pair(a_rep, b_rep, labels, out=None, sources=None):
    """Minimal stand-in for compare_data.build: two single runs pair whatever their names, grids by name; tasks by id;
    file links rewritten relative to `out` from each side's root in `sources`."""
    ra, rb = [r["run"] for r in a_rep["runs"]], [r["run"] for r in b_rep["runs"]]
    pairs = [(ra[0] if ra == rb else "run", ra[0], rb[0])] if len(ra) == len(rb) == 1 else [(r, r, r) for r in ra if r in rb]
    runs, tasks = [], []
    for run, xa, xb in pairs:
        ta = {t["task_id"]: t for t in a_rep["tasks"] if t["run"] == xa}
        tb = {t["task_id"]: t for t in b_rep["tasks"] if t["run"] == xb}
        common = sorted(set(ta) & set(tb))
        runs.append({"run": run, "budget": "n/a", "common": len(common), "only_a": len(set(ta) - set(tb)),
                     "only_b": len(set(tb) - set(ta)), "a": {"pass_rate": 0.5}, "b": {"pass_rate": 0.5},
                     "delta": {"pass_rate": 0.0}, "ratio": {}, "head_to_head": {}, "mcnemar_p": 1.0})
        for tid in common:
            x, y = ta[tid], tb[tid]
            side = lambda t, root: {"key": t["key"], "outcome": t["outcome"], "passed": t["passed"],
                                    "files": {k: os.path.relpath(os.path.join(root, p), out) for k, p in t["files"].items()}}
            tasks.append({"key": f"c{len(tasks)}", "task_id": tid, "run": run, "kind": x["kind"],
                          "change": {(1, 1): "both_pass", (1, 0): "a_only", (0, 1): "b_only", (0, 0): "both_fail"}[(x["passed"], y["passed"])],
                          "a": side(x, sources[0]), "b": side(y, sources[1])})
    if len(ra) == 1 and len(rb) == 1:
        ra = rb = []
    return {"compare_version": 1, "labels": labels, "sources": [str(x) for x in sources], "verdict_source": a_rep["verdict_source"], "a": a_rep, "b": b_rep,
            "unpaired": {"only_a_runs": [r for r in ra if r not in rb], "only_b_runs": [r for r in rb if r not in ra]},
            "runs": runs, "tasks": tasks}


@pytest.fixture
def stubs(monkeypatch):
    """Stand-ins for compare_data.build, compare_charts.render_all, charts.render_all and compare_html.render_html."""
    calls = {"build": [], "html": [], "open": []}

    def build(a_rep, b_rep, labels, *, out=None, sources=None):
        calls["build"].append((a_rep, b_rep, labels, out, sources))
        return _pair(a_rep, b_rep, labels, out, sources)

    def html(cmp, charts, charts_a, charts_b):
        calls["html"].append((charts, charts_a, charts_b))
        return "<!doctype html>" + "".join([*charts.values(), *charts_a.values(), *charts_b.values()])

    svg = lambda names: lambda x: {n: f'<svg class="mm-chart mm-{n}" data-chart="{n}"/>' for n in names}
    for name, fns in (("compare_data", {"build": build}), ("compare_charts", {"render_all": svg(("scoreboard", "diffs"))}),
                      ("charts", {"render_all": svg(("waffle", "outcomes"))}), ("compare_html", {"render_html": html})):
        mod = types.ModuleType(f"mockmcp.eval.{name}")
        mod.__dict__.update(fns)
        monkeypatch.setitem(sys.modules, f"mockmcp.eval.{name}", mod)
        monkeypatch.setattr(mockmcp.eval, name, mod, raising=False)
    monkeypatch.setattr(compare.webbrowser, "open", lambda url: calls["open"].append(url))
    return calls


def graded(d, fix_fab=False):
    """A graded copy of the grade-test run in `d`; `fix_fab` makes the fabricated answer correct (that task flips to pass)."""
    d.mkdir(parents=True)
    make_run(d)
    if fix_fab:
        ans = json.loads((d / "slc-fab:1:Q1" / "answers.json").read_text())
        (d / "slc-fab:1:Q1" / "answers.json").write_text(json.dumps(ans).replace("cost 4,500", "920"))
    grade.grade_run(d, None, workers=2)
    return d


def snapshot(*dirs):
    """Bytes and mtime of every file under `dirs` (to prove compare never writes there)."""
    return {p: (p.read_bytes(), p.stat().st_mtime_ns) for d in dirs for p in sorted(d.rglob("*")) if p.is_file()}


def test_two_single_runs_pair_as_one_and_nothing_is_written_into_them(tmp_path, stubs, capsys):
    a, b = graded(tmp_path / "a"), graded(tmp_path / "b", fix_fab=True)
    (a / "results.jsonl").unlink()   # report would rebuild it; compare must not
    before = snapshot(a, b)
    assert compare.main(args(a, b)) == 0
    assert snapshot(a, b) == before and not (a / "results.jsonl").exists()
    out = tmp_path / "compare-a-vs-b"   # default: next to A
    cmp = json.loads((out / "compare.json").read_text())
    a_rep, b_rep, labels, got_out, sources = stubs["build"][0]
    assert got_out == out.resolve() and sources == [a.resolve(), b.resolve()] and cmp["sources"] == [str(a), str(b)]   # tmp is outside the cwd: as given
    assert [r["run"] for r in a_rep["runs"]] == ["a"] and [r["run"] for r in cmp["runs"]] == ["run"]   # REPORTs unchanged
    assert labels == cmp["labels"] == ["haiku (a)", "haiku (b)"]   # same model on both sides: folder names appended
    by = {t["task_id"]: t for t in cmp["tasks"]}
    assert by["slc-fab:1:Q1"]["change"] == "b_only" and by["slc-ok:1:Q1"]["change"] == "both_pass"
    assert by["slc-ok:1:Q1"]["a"]["files"]["answers"] == os.path.join("..", "a", "slc-ok:1:Q1", "answers.json")
    assert cmp["a"]["tasks"][0]["files"]["answers"] == os.path.join("slc-fab:1:Q1", "answers.json")   # embedded as built
    md = (out / "compare.md").read_text()
    assert "haiku (a) passes, haiku (b) fails" not in md and "haiku (b) passes, haiku (a) fails (1)" in md
    assert "`slc-fab:1:Q1` (run, slice): fabricated → pass" in md
    assert not (out / "compare.html").exists() and not stubs["html"]
    assert str(out / "compare.json") in capsys.readouterr().out


def test_grids_pair_by_sub_run_and_count_unpaired_runs_and_one_sided_tasks(tmp_path, stubs):
    a, b = tmp_path / "ga", tmp_path / "gb"
    for d, runs in ((a, ("b5k", "b25k")), (b, ("b5k", "b50k"))):
        for r in runs:
            graded(d / r)
    tl = (b / "b5k" / "tasks.jsonl").read_text().splitlines()
    (b / "b5k" / "tasks.jsonl").write_text("\n".join(l for l in tl if "trap-missing" not in l) + "\n")
    (b / "b5k" / "results.jsonl").unlink()
    before = snapshot(a, b)
    assert compare.main(args(a, b, labels="small, big")) == 0
    assert snapshot(a, b) == before
    cmp = json.loads((tmp_path / "compare-ga-vs-gb" / "compare.json").read_text())
    assert cmp["labels"] == ["small", "big"] and cmp["unpaired"] == {"only_a_runs": ["b25k"], "only_b_runs": ["b50k"]}
    assert [(r["run"], r["common"], r["only_a"], r["only_b"]) for r in cmp["runs"]] == [("b5k", 2, 1, 0)]
    assert {t["run"] for t in cmp["tasks"]} == {"b5k"}
    md = (tmp_path / "compare-ga-vs-gb" / "compare.md").read_text()
    assert "runs only in A, not compared: b25k" in md and "b5k: 1 only in small, 0 only in big" in md


def test_single_run_against_a_grid_is_an_error(tmp_path, stubs, capsys):
    a, g = graded(tmp_path / "a"), tmp_path / "g"
    graded(g / "b5k")
    assert compare.main(args(a, g)) == 1
    assert "is a single run but" in capsys.readouterr().out and not stubs["build"]
    assert not (tmp_path / "compare-a-vs-g").exists()


def test_bad_labels_and_output_inside_a_run_are_errors(tmp_path, stubs, capsys):
    a, b = graded(tmp_path / "a"), graded(tmp_path / "b")
    before = snapshot(a, b)
    assert compare.main(args(a, b, labels="one")) == 1 and "--labels" in capsys.readouterr().out
    assert compare.main(args(a, b, out=a / "cmp")) == 1 and "never writes into" in capsys.readouterr().out
    assert compare.main(args(a, b, out=b)) == 1
    assert snapshot(a, b) == before and not (a / "cmp").exists()


def test_sources_are_shown_relative_to_the_current_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "runs" / "x").mkdir(parents=True)
    assert compare._shown(tmp_path / "runs" / "x") == os.path.join("runs", "x")
    assert compare._shown(tmp_path.parent) == str(tmp_path.parent)


def test_default_labels_prefer_the_served_model():
    rows = lambda served, model: [{"models_served": served, "model": model}]
    from pathlib import Path
    assert compare.default_labels(rows(["m-1"], "haiku"), rows([], "sonnet"), Path("x"), Path("y")) == ["m-1", "sonnet"]
    assert compare.default_labels(rows([], "?"), rows([], "?"), Path("x"), Path("y")) == ["x", "y"]
    helper = rows(["claude-haiku-9", "claude-sonnet-9"], "sonnet")   # a harness serves a helper model alongside
    assert compare.default_labels(rows(["claude-haiku-9"], "haiku"), helper, Path("x"), Path("y")) == ["claude-haiku-9", "claude-sonnet-9"]


def test_verdicts_on_both_sides_never_mix_judges(tmp_path, stubs):
    a, b = graded(tmp_path / "a"), graded(tmp_path / "b")
    alt = {"judge": "x", "verdict": {"outcome": "partial", "categories": ["incomplete"], "judge": {"backend": "x"}}}
    (a / "slc-ok:1:Q1" / "judge.x.json").write_text(json.dumps(alt))
    for tid in ("slc-ok:1:Q1", "slc-fab:1:Q1"):
        (b / tid / "judge.x.json").write_text(json.dumps(alt))
    for d in (a, b):
        (d / "results.jsonl").unlink()
    before = snapshot(a, b)
    assert compare.main(args(a, b, verdicts="x")) == 0
    assert snapshot(a, b) == before
    out = tmp_path / "compare-a-vs-b.x"
    cmp = json.loads((out / "compare.json").read_text())
    a_rep, b_rep = stubs["build"][0][:2]
    assert a_rep["verdict_source"] == b_rep["verdict_source"] == cmp["verdict_source"] == "judge.x.json"
    assert {t["task_id"] for t in a_rep["tasks"]} == {"slc-ok:1:Q1"}   # left out, never filled in from judge.json
    assert {t["task_id"]: t["outcome"] for t in b_rep["tasks"]} == {"slc-ok:1:Q1": "partial", "slc-fab:1:Q1": "partial"}
    assert cmp["excluded"] == [2, 1] and a_rep["summary"]["excluded"] == 2
    assert all(f.endswith("judge.x.json") for t in cmp["tasks"] for s in ("a", "b") for k, f in t[s]["files"].items() if k == "judge")
    assert "left out for lacking judge.x.json: 2 graded tasks in A, 1 in B" in (out / "compare.md").read_text()
    assert compare.main(args(a, b, verdicts="nobody")) == 1


def test_html_writes_three_chart_folders_and_the_page_without_opening(tmp_path, stubs, capsys):
    a, b = graded(tmp_path / "a"), graded(tmp_path / "b", fix_fab=True)
    out = tmp_path / "cmp"
    (out / "charts").mkdir(parents=True)
    (out / "charts" / "shift.svg").write_text("<svg/>")   # left over from an earlier comparison: must go
    before = snapshot(a, b)
    assert compare.main(args(a, b, out=out, html=True, open=False)) == 0
    assert {p.name for p in (out / "charts").iterdir()} == {"scoreboard.svg", "diffs.svg"}
    assert {p.name for p in (out / "charts-a").iterdir()} == {p.name for p in (out / "charts-b").iterdir()} == {"waffle.svg", "outcomes.svg"}
    page = (out / "compare.html").read_text()
    assert 'data-chart="scoreboard"' in page and 'data-chart="waffle"' in page and not stubs["open"]
    assert str(out / "compare.html") in capsys.readouterr().out and snapshot(a, b) == before
    compare.write_outputs(a, b, out, html=True, open_=True)
    assert stubs["open"] == [(out / "compare.html").resolve().as_uri()]


def test_cli_registers_compare():
    import argparse
    from mockmcp.eval import cli
    p = argparse.ArgumentParser()
    cli.add_parser(p.add_subparsers(dest="cmd"))
    a = p.parse_args(["eval", "compare", "x", "y", "--labels", "p,q", "--html", "--no-open"])
    assert (a.step, str(a.a_dir), str(a.b_dir), a.labels, a.html, a.open) == ("compare", "x", "y", "p,q", True, False)


REAL = all(importlib.util.find_spec(f"mockmcp.eval.{m}") for m in ("compare_data", "compare_charts", "compare_html", "charts"))


@pytest.mark.skipif(not REAL, reason="compare_data / compare_charts / compare_html not built yet")
def test_end_to_end_with_the_real_builders(tmp_path):
    a, b = graded(tmp_path / "a"), graded(tmp_path / "b", fix_fab=True)
    before = snapshot(a, b)
    out = compare.write_outputs(a, b, tmp_path / "cmp", labels="old,new", html=True, open_=False)
    assert snapshot(a, b) == before
    cmp = json.loads(out["json"].read_text())
    assert cmp["labels"] == ["old", "new"] and len(cmp["tasks"]) == 3
    assert {t["task_id"]: t["change"] for t in cmp["tasks"]}["slc-fab:1:Q1"] == "b_only"
    assert all(not os.path.isabs(f) for t in cmp["tasks"] for s in ("a", "b") for f in t[s]["files"].values())
    assert out["html"].read_text().startswith("<!doctype html>") or "<html" in out["html"].read_text()
    assert any(out["charts"].glob("*.svg")) and any(out["charts_a"].glob("*.svg")) and any(out["charts_b"].glob("*.svg"))


@pytest.mark.skipif(not importlib.util.find_spec("mockmcp.eval.compare_data"), reason="compare_data not built yet")
def test_real_compare_data_pairs_grids_and_links_files_from_the_compare_folder(tmp_path):
    a, b = tmp_path / "ga", tmp_path / "gb"
    for d, runs in ((a, ("b5k", "b25k")), (b, ("b5k", "b25k", "b50k"))):
        for r in runs:
            graded(d / r, fix_fab=d == b)
    before = snapshot(a, b)
    assert compare.main(args(a, b)) == 0
    assert snapshot(a, b) == before
    out = tmp_path / "compare-ga-vs-gb"
    cmp = json.loads((out / "compare.json").read_text())
    assert {r["run"] for r in cmp["runs"]} == {"b5k", "b25k"} and cmp["unpaired"]["only_b_runs"] == ["b50k"]
    t = next(t for t in cmp["tasks"] if t["task_id"] == "slc-fab:1:Q1")
    assert t["change"] == "b_only" and (out / t["b"]["files"]["answers"]).resolve() == (b / t["run"] / "slc-fab:1:Q1" / "answers.json")
    assert "| all |" in (out / "compare.md").read_text()
