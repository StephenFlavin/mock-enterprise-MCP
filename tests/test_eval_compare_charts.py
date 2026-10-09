"""The comparison charts: well-formed standalone SVG, no scripts or external references, no inline colours, unique ids,
deterministic, per-task marks keyed by the compare task, figures that match the tasks, the None rules, escaping, and
side colours that read in both themes and stay apart from each other and from the fail colour."""
import math
import random
import re
import xml.etree.ElementTree as ET
from collections import Counter

import pytest

from mockmcp.eval import compare_charts as cc, svg
from mockmcp.eval.schema import OUTCOMES
from test_eval_charts import grid, report, task

NS = "{http://www.w3.org/2000/svg}"
SIDE_KEYS = ("key", "outcome", "band", "band_rank", "passed", "near_miss", "severity", "categories", "effort", "calls", "notes")


def compare_of(a: dict, b: dict, labels=("haiku", "sonnet")) -> dict:
    """A COMPARE dict from two REPORTs (runs paired by name, tasks by task_id), as compare_data.build shapes it."""
    tasks, runs = [], []
    single = len(a["runs"]) == 1 == len(b["runs"])   # two single runs pair whatever their names
    for ra in a["runs"]:
        rb = b["runs"][0] if single else next((r for r in b["runs"] if r["run"] == ra["run"]), None)
        if not rb:
            continue
        ta = {t["task_id"]: t for t in a["tasks"] if t["run"] == ra["run"]}
        tb = {t["task_id"]: t for t in b["tasks"] if t["run"] == rb["run"]}
        name = ra["run"] if not single or ra["run"] == rb["run"] else "run"
        common = sorted(set(ta) & set(tb))
        h2h = Counter()
        for tid in common:
            ea, eb = ta[tid], tb[tid]
            ch = {(True, True): "both_pass", (True, False): "a_only", (False, True): "b_only", (False, False): "both_fail"}[
                ea["passed"], eb["passed"]]
            h2h[ch] += 1
            shift = "same" if ea["band_rank"] == eb["band_rank"] else "better" if eb["band_rank"] > ea["band_rank"] else "worse"
            tasks.append({"key": f"c{len(tasks)}", "task_id": tid, "run": name, "budget": ra["budget"], "kind": ea["kind"],
                          "trap": ea["trap"], "change": ch, "shift": shift,
                          "a": {k: ea[k] for k in SIDE_KEYS} | {"files": {}}, "b": {k: eb[k] for k in SIDE_KEYS} | {"files": {}}})
        runs.append({"run": name, "budget": ra["budget"], "common": len(common), "only_a": len(set(ta) - set(tb)),
                     "only_b": len(set(tb) - set(ta)), "head_to_head": {k: h2h[k] for k in cc.CHANGES},
                     "mcnemar_p": cc.mcnemar(h2h["a_only"], h2h["b_only"])})
    return {"compare_version": 1, "labels": list(labels), "sources": ["runs/a", "runs/b"], "verdict_source": "judge.json",
            "unpaired": {"only_a_runs": [], "only_b_runs": []}, "a": a, "b": b, "runs": runs, "tasks": tasks}


def improve(r: dict, seed: int, p_fix=.45, p_break=.12) -> dict:
    """A copy of a REPORT where failures sometimes pass and passes sometimes fail (a different model on the same tasks),
    with effort scaled up (the bigger model reads more)."""
    rng = random.Random(seed)
    out = []
    for t in r["tasks"]:
        o = t["outcome"]
        if o != "pass" and rng.random() < p_fix:
            o = "pass"
        elif o == "pass" and rng.random() < p_break:
            o = rng.choice(["partial", "fabricated", "over_cautious"])
        elif o != "pass" and rng.random() < .3:
            o = rng.choice([x for x in OUTCOMES if x not in ("pass", o)])
        n = task(t["key"], t["task_id"], t["run"], o, kind=t["kind"], severity="reversible" if o == "unsafe" else "none",
                 rng=random.Random(seed * 1000 + int(t["key"][1:])), handled=o == "honest_fail" or None)
        for k in ("input_tokens", "seconds", "cost_usd"):
            n["effort"][k] *= rng.uniform(.8, 2.4)
        out.append(n)
    return report(out, [x["run"] for x in r["runs"]], {x["run"]: x["budget"] for x in r["runs"]})


def single_pair():
    a = grid(n=80, budgets=("tokens-25000",), seed=11)
    return compare_of(a, improve(a, 5))


def grid_pair():
    a = grid(n=120, seed=7)
    return compare_of(a, improve(a, 9))


def same_pair():
    a = grid(n=24, budgets=("smoke",), seed=2)
    return compare_of(a, a, labels=("run-1", "run-2"))


def nasty_pair():
    ids = ['scn-01:4:Q1 <b>&"x"', "trap-<script>:&amp;:Q2", "scn:a&b<c>:Q3", "ask:<i>:Q4"]
    outs = (["pass", "fabricated", "partial", "unsafe"], ["partial", "pass", "honest_fail", "pass"])
    sides = []
    for j, os_ in enumerate(outs):
        ts = [task(f"t{i}", tid, "r<0>&", o, kind="trap" if i == 1 else "scenario", severity="reversible" if o == "unsafe" else "none",
                   handled=o == "honest_fail" or None) for i, (tid, o) in enumerate(zip(ids, os_))]
        sides.append(report(ts, ["r<0>&"]))
    return compare_of(*sides, labels=("<haiku> & co", 'son"net'))


FIXTURES = {"single": single_pair, "grid": grid_pair, "same": same_pair, "nasty": nasty_pair}


@pytest.fixture(scope="module", params=list(FIXTURES))
def rendered(request):
    c = FIXTURES[request.param]()
    return request.param, c, cc.render_all(c)


def test_charts_are_wellformed_standalone_svg(rendered):
    name, c, out = rendered
    assert list(out) == [k for k in cc.CHARTS if k in out]
    for k, s in out.items():
        root = ET.fromstring(s)
        assert root.tag == NS + "svg" and root.get("viewBox") and root.get("role") == "img" and root.get("width") == "100%"
        assert root.get("data-chart") == k and root.get("data-view") == "outcome" and f"mm-chart mm-{k}" == root.get("class")
        assert root.find(NS + "title") is not None and root.find(NS + "desc") is not None
        assert root.get("aria-labelledby") == f"{k}-t {k}-d" and root.find(NS + "style") is not None
        body = s.replace('xmlns="http://www.w3.org/2000/svg"', "")
        assert "http" not in body and "<script" not in body.lower() and "foreignObject" not in body and "url(" not in body
        assert not re.search(r'(fill|stroke|stop-color|color)="#', s) and 'style="' not in s
        assert "--mm-side-a" in s and "--mm-side-b" in s
    if name in ("single", "grid"):
        assert set(out) == set(cc.CHARTS)
    assert ET.fromstring(out["paired"]).get("data-metric") == "input_tokens"


def test_ids_unique_and_output_deterministic(rendered):
    _, c, out = rendered
    ids = re.findall(r'\bid="([^"]+)"', "".join(out.values()))
    assert len(ids) == len(set(ids))
    assert cc.render_all(c) == out


def test_none_rules():
    same = same_pair()
    assert cc.chart_diffs(same) is None and cc.chart_scoreboard(same) is not None
    assert cc.render_all({"labels": ["a", "b"], "runs": [], "tasks": []}) == {}
    assert cc.render_all({"runs": [], "tasks": []}) == {}


def marks(s):
    return [e for e in ET.fromstring(s).iter() if "mm-t" in (e.get("class") or "").split()]


def test_paired_marks_one_per_task_per_metric():
    c = grid_pair()
    root = ET.fromstring(cc.chart_paired(c))
    gs = {g.get("class"): g for g in root.iter(NS + "g") if "mm-m" in (g.get("class") or "").split()}
    assert set(gs) == {f"mm-m mm-m-{m}" for m in svg.METRICS}
    keys = {t["key"]: t for t in c["tasks"]}
    for g in gs.values():
        dots = [e for e in g.iter(NS + "circle") if "mm-t" in (e.get("class") or "").split()]
        assert sorted(e.get("data-key") for e in dots) == sorted(keys)
        for e in dots:
            t = keys[e.get("data-key")]
            assert f"ch-{t['change']}" in e.get("class").split() and e.get("data-run") == t["run"] and e.get("data-kind") == t["kind"]
            assert not any(x.startswith(("o-", "b-", "pf-")) for x in e.get("class").split())   # colour follows the change, not the view


def test_diffs_marks_cover_exactly_the_flipped_tasks():
    c = grid_pair()
    m = marks(cc.chart_diffs(c))
    flipped = {t["key"]: t for t in c["tasks"] if t["a"]["outcome"] != t["b"]["outcome"]}
    assert flipped and len(m) == 2 * len(flipped)
    assert {e.get("data-key") for e in m} == set(flipped)
    for e in m:
        t, side = flipped[e.get("data-key")], e.get("data-side")
        cls = e.get("class").split()
        assert f"o-{t[side]['outcome']}" in cls and f"b-{t[side]['band']}" in cls
        assert f"pf-{'pass' if t[side]['passed'] else 'fail'}" in cls and e.get("data-run") == t["run"]
    # B's fixes come before A's
    order = [flipped[e.get("data-key")]["change"] for e in m if e.get("data-side") == "a"]
    first_run = [flipped[e.get("data-key")]["run"] for e in m if e.get("data-side") == "a"][0]
    run_order = [flipped[e.get("data-key")]["change"] for e in m if e.get("data-side") == "a" and flipped[e.get("data-key")]["run"] == first_run]
    assert run_order.index("b_only") < run_order.index("a_only") if {"a_only", "b_only"} <= set(run_order) else order


def test_view_groups_and_aligned_stacks():
    c = grid_pair()
    for name in ("shift", "outcomes"):
        root = ET.fromstring(getattr(cc, f"chart_{name}")(c))
        vs = [g for g in root.iter(NS + "g") if "mm-v" in (g.get("class") or "").split()]
        assert {g.get("class") for g in vs} >= {f"mm-v mm-v-{v}" for v in svg.VIEWS}
    root = ET.fromstring(cc.chart_outcomes(c))
    rows = {}
    for g in root.iter(NS + "g"):
        if "mm-v" in (g.get("class") or "").split():
            for e in g.iter(NS + "rect"):
                if "mm-seg" in (e.get("class") or "").split():
                    rows.setdefault((g.get("class"), e.get("y")), []).append((float(e.get("x")), float(e.get("width"))))
    assert len(rows) == 3 * 2 * (len(c["runs"]) + 1)   # views x sides x (runs + all runs)
    widths = {round(sum(w for _, w in segs), 1) for segs in rows.values()}
    assert len(widths) == 1 and len({min(x for x, _ in segs) for segs in rows.values()}) == 1


def test_headtohead_is_proportional_and_centred():
    c = grid_pair()
    root = ET.fromstring(cc.chart_headtohead(c))
    segs = [e for e in root.iter(NS + "rect") if "mm-seg" in (e.get("class") or "").split()]
    by_y = {}
    for e in segs:
        by_y.setdefault(e.get("y"), []).append(e)
    assert len(by_y) == len(c["runs"]) + 1
    totals = []
    for row in by_y.values():
        totals.append(sum(float(e.get("width")) for e in row))
        a = next((e for e in row if "f-ch-a_only" in e.get("class")), None)
        b = next((e for e in row if "f-ch-b_only" in e.get("class")), None)
        if a is not None and b is not None:
            assert abs(float(a.get("x")) + float(a.get("width")) - float(b.get("x"))) < .2   # they meet on the centre line
        n = sum(int(re.search(r": (\d+) of", e.find(NS + "title").text).group(1)) for e in row)
        for e in row:   # each segment's width is its share of the row's tasks
            k = int(re.search(r": (\d+) of", e.find(NS + "title").text).group(1))
            assert float(e.get("width")) == pytest.approx(totals[-1] * k / n, abs=.2)
    assert max(totals) - min(totals) < .5   # shares: every row spans the same total width


def test_scoreboard_figures_and_mcnemar():
    assert cc.mcnemar(0, 0) == 1.0 and cc.mcnemar(0, 5) == pytest.approx(0.0625) and cc.mcnemar(1, 6) == pytest.approx(0.125)
    assert cc.mcnemar(30, 10) < .01 and cc.mcnemar(7, 7) == 1.0
    c = single_pair()
    ts = c["tasks"]
    pa, pb = sum(t["a"]["passed"] for t in ts) / len(ts), sum(t["b"]["passed"] for t in ts) / len(ts)
    desc = ET.fromstring(cc.chart_scoreboard(c)).find(NS + "desc").text
    assert f"haiku {pa * 100:.0f}%" in desc and f"sonnet {pb * 100:.0f}%" in desc and f"{(pb - pa) * 100:+.1f} pts" in desc
    rows = ET.fromstring(cc.chart_scoreboard(grid_pair())).find(NS + "desc").text
    assert rows.count("p ") >= len(grid_pair()["runs"]) + 1 and "all runs" in rows


def test_spend_ratios_match_totals():
    c = single_pair()
    s = cc.chart_spend(c)
    ts = c["tasks"]
    a, b = (sum(t[x]["effort"]["cost_usd"] for t in ts) for x in "ab")
    assert cc.ratio(b, a) in s and svg.fmt(a, "usd") in s and cc.ratio(1, 0) == "–" and cc.ratio(2, 2) == "1.0×"


def test_escaping_of_ids_runs_and_labels():
    c = nasty_pair()
    out = cc.render_all(c)
    assert "diffs" in out and "paired" in out
    for s in out.values():
        ET.fromstring(s)
        assert "<b>" not in s and "<script>" not in s and "r<0>" not in s and "<haiku>" not in s and "<i>" not in s
    titles = [e.text for e in ET.fromstring(out["diffs"]).iter(NS + "title")]
    assert any(t and t.startswith('scn-01:4:Q1 <b>&"x"') for t in titles)
    assert {e.get("data-run") for e in marks(out["diffs"])} == {"r<0>&"}
    assert any("<haiku> & co" in (e.text or "") for e in ET.fromstring(out["scoreboard"]).iter(NS + "text"))


def _oklab(h):
    lin = lambda x: x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(int(h[i:i + 2], 16) / 255) for i in (1, 3, 5))
    l, m, s = ((0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3),
               (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3),
               (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s, 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def test_side_colours_readable_and_distinct():
    for theme, p in svg.PALETTE.items():
        for k in ("side-a", "side-b"):
            assert svg.contrast(p[k], p["bg"]) >= 3, (theme, k)
            assert svg.contrast(p[f"ink-{k}"], p[k]) >= 3, (theme, k)
        de = lambda x, y: 100 * math.dist(_oklab(p[x]), _oklab(p[y]))
        assert de("side-a", "side-b") >= 15 and de("side-a", "fail") >= 15 and de("side-b", "fail") >= 15, theme
        assert min(de(s, k) for s in ("side-a", "side-b") for k in svg.MARKS if not k.startswith("side")) >= 10, theme
    css = svg.theme_css()
    assert "--mm-side-a" in css and ".mm-chart .f-side-a{fill:var(--mm-side-a)}" in svg.STYLE


def test_long_labels_stay_inside_the_chart():
    a = grid(n=40, budgets=("tokens-0", "tokens-25000"), seed=4)
    c = compare_of(a, improve(a, 3), labels=("claude-haiku-5-5", "claude-sonnet-5-5-with-a-very-long-suffix"))
    for name, s in cc.render_all(c).items():
        width = float(ET.fromstring(s).get("viewBox").split()[2])
        for e in ET.fromstring(s).iter(NS + "text"):
            label = "".join(e.itertext())
            size = 15 if "mm-h1" in (e.get("class") or "") else 12
            w, x = svg.tw(label, size), float(e.get("x"))
            x0 = {"end": x - w, "middle": x - w / 2}.get(e.get("text-anchor"), x)
            assert -1 <= x0 and x0 + w <= width + 1, (name, label)
    head = [e.text for e in ET.fromstring(cc.chart_scoreboard(c)).iter(NS + "text") if e.text == "B − A"]
    assert head   # the gap column names the sides by letter; the key carries the long names
