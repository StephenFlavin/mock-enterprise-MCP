"""The report's SVG charts: well-formed standalone SVG, no scripts or external references, no inline colours, unique ids,
deterministic, readable contrast in both themes, and marks that match the data (per-task counts, exact stacks, a
beeswarm without overlaps)."""
import random
import re
import statistics
import xml.etree.ElementTree as ET

import pytest

from mockmcp.eval import charts, svg, tags
from mockmcp.eval.schema import OUTCOMES, SEVERITY_BANDS

NS = "{http://www.w3.org/2000/svg}"
KINDS = ("scenario", "trap", "ask")
TRAP_TYPES = ("missing_system", "lookalike", "vague")


def band_of(outcome, severity):
    if outcome == "unsafe":
        return {"external_or_irreversible": "unsafe_external", "reversible": "unsafe_reversible"}.get(severity, "unsafe_benign")
    return outcome


def task(key, tid, run, outcome, *, kind="scenario", passed=None, severity="none", near=None, rng=None, trap_type=None,
         handled=None, cats=()):
    """One REPORT task entry with plausible effort: passes cheap, partials and over-cautious costly, fabrications fast."""
    rng = rng or random.Random(key)
    base = {"pass": 30e3, "honest_fail": 45e3, "partial": 220e3, "over_cautious": 260e3, "fabricated": 80e3, "unsafe": 140e3}[outcome]
    tok = int(base * rng.lognormvariate(0, .7))
    calls = max(0, int(tok / 18e3 * rng.uniform(.6, 1.4)))
    passed = (outcome == "pass" or (kind == "trap" and outcome == "honest_fail")) if passed is None else passed
    b = band_of(outcome, severity)
    return {"key": key, "task_id": tid, "run": run, "budget": "~33k tokens", "budget_tokens": 33182, "budget_tools": 144,
            "kind": kind, "question_id": tid.split(":", 1)[-1], "domain": "", "strata": [], "features": {},
            "trap": {"type": trap_type or "missing_system", "variant": "", "tier": 1, "difficulty": "", "trap_turn": 1} if kind == "trap" else None,
            "outcome": outcome, "passed": passed, "categories": list(cats), "severity": severity, "band": b,
            "band_rank": SEVERITY_BANDS.index(b),
            "near_miss": bool(near if near is not None else (not passed and (outcome == "partial" or (kind == "trap" and handled)))),
            "trap_handled": handled if kind == "trap" else None,
            "judge": {}, "notes": {},
            "effort": {"class": "typical", "cost_usd": tok / 1e6 * 0.9, "input_tokens": tok, "output_tokens": tok // 40,
                       "cache_read": tok // 2, "seconds": 4 + tok / 6e3 * rng.uniform(.5, 1.5), "tool_calls": calls,
                       "turns_total": 2, "turns_passed": 1 if passed else 0},
            "calls": {"total": calls, "errors": rng.randint(0, 3 if passed else 6), "exact_repeats": rng.randint(0, 1),
                      "same_tool_repeats": rng.randint(0, 4), "distractor": rng.randint(0, 2 if passed else 5),
                      "decoy": rng.randint(0, 2) if kind == "trap" else 0, "writes": 0, "failed_writes": 0,
                      "by_turn": [calls], "servers": {}}, "files": {}}


def report(tasks, run_names, budgets=None):
    """A REPORT dict around task entries (runs in the given order)."""
    runs = []
    for i, run in enumerate(run_names):
        ts = [t for t in tasks if t["run"] == run]
        runs.append({"run": run, "budget": (budgets or {}).get(run, f"~{33 + 40 * i}k tokens"), "median_tools": 144 * (i + 1),
                     "median_tokens": 33000 + 40000 * i, "tasks": len(ts), "passed": sum(t["passed"] for t in ts),
                     "outcomes": {}, "bands": {}, "near_miss": sum(t["near_miss"] for t in ts), "metrics": {},
                     "effort_thresholds": None, "waste": {}})
    return {"report_version": 1, "title": "fixture", "verdict_source": "judge.json", "summary": {}, "definitions": {},
            "runs": runs, "tasks": tasks}


CATS = ("missed_step", "bad_args", "wrong_server", "incomplete", "fabricated_value", "gave_up", "unrequested_write")


def grid(n=160, budgets=("tokens-0", "tokens-25000", "tokens-50000", "tokens-100000"), seed=7):
    """A budget grid where each task's outcome drifts worse with the budget (some recover), deterministic."""
    rng = random.Random(seed)
    weights = {"pass": 58, "partial": 18, "fabricated": 9, "honest_fail": 5, "over_cautious": 4, "unsafe": 6}
    tasks, k = [], 0
    for i in range(n):
        kind = "trap" if i % 4 == 0 else "scenario"
        tid = f"{'trap' if kind == 'trap' else 'scn'}-{i // 10:02d}:{i % 10}:Q{i % 3 + 1}"
        o = rng.choices(list(weights), list(weights.values()))[0]
        sev = rng.choice(["benign", "reversible", "external_or_irreversible"])
        tt = TRAP_TYPES[i % 3]
        for j, run in enumerate(budgets):
            if j and rng.random() < .12 * j:
                o = rng.choice(["partial", "fabricated", "over_cautious", "unsafe"]) if o == "pass" else (
                    "pass" if rng.random() < .3 else o)
            cats = () if o == "pass" else tuple(rng.sample(CATS, rng.randint(1, 2)))
            tasks.append(task(f"t{k}", tid, run, o, kind=kind, severity=sev if o == "unsafe" else "none", rng=random.Random(k),
                              trap_type=tt, handled=(o in ("pass", "honest_fail") or rng.random() < .3) if kind == "trap" else None,
                              cats=cats))
            k += 1
    return report(tasks, list(budgets))


def single(n=80, seed=3):
    rng = random.Random(seed)
    outs = rng.choices(OUTCOMES, [4, 8, 4, 18, 4, 62], k=n)
    tasks = [task(f"t{i}", f"scn-{i:02d}:1:Q1", "smoke", o, kind=KINDS[i % 3], severity="reversible" if o == "unsafe" else "none",
                  rng=random.Random(i), handled=(i % 2 == 0), cats=() if o == "pass" else ("missed_step",))
             for i, o in enumerate(outs)]
    return report(tasks, ["smoke"])


def all_passed():
    return report([task(f"t{i}", f"scn-{i}:1:Q1", "ok", "pass") for i in range(6)], ["ok"])


def nasty():
    """Task ids with markup characters, in a 2-run grid with changing outcomes."""
    ids = ['scn-01:4:Q1 <b>&"x"', "trap-<script>:&amp;:Q2", "scn:a&b<c>:Q3"]
    tasks, k = [], 0
    for j, run in enumerate(["r<0>", "r&1"]):
        for i, tid in enumerate(ids):
            tasks.append(task(f"t{k}", tid, run, ["pass", "fabricated", "partial"][(i + j) % 3], kind="trap" if i == 1 else "scenario",
                              handled=True, cats=("bad_args",)))
            k += 1
    return report(tasks, ["r<0>", "r&1"])


FIXTURES = {"single": single, "grid": grid, "all_passed": all_passed, "nasty": nasty}


@pytest.fixture(scope="module", params=list(FIXTURES))
def rendered(request):
    r = FIXTURES[request.param]()
    return request.param, r, charts.render_all(r)


def test_charts_are_wellformed_standalone_svg(rendered):
    name, r, out = rendered
    assert list(out) == [c for c in charts.CHARTS if c in out]
    for c, s in out.items():
        root = ET.fromstring(s)
        assert root.tag == NS + "svg" and root.get("viewBox") and root.get("role") == "img" and root.get("width") == "100%"
        assert root.get("data-chart") == c and root.get("data-view") == "outcome" and "mm-chart" in root.get("class")
        assert root.find(NS + "title") is not None and root.find(NS + "desc") is not None
        assert root.get("aria-labelledby") == f"{c}-t {c}-d"
        assert root.find(NS + "style") is not None
        body = s.replace('xmlns="http://www.w3.org/2000/svg"', "")
        assert "http" not in body and "<script" not in body.lower() and "foreignObject" not in body and "url(" not in body
        assert not re.search(r'(fill|stroke|stop-color|color)="#', s) and 'style="' not in s
    if name == "grid":
        assert set(out) == set(charts.CHARTS)
    assert charts.chart_effort(r) is None or ET.fromstring(charts.chart_effort(r)).get("data-metric") == "input_tokens"


def test_ids_unique_and_output_deterministic(rendered):
    _, r, out = rendered
    ids = re.findall(r'\bid="([^"]+)"', "".join(out.values()))
    assert len(ids) == len(set(ids))
    assert charts.render_all(r) == out


def test_single_run_and_nothing_failed():
    r = single()
    assert charts.chart_scaling(r) is None and charts.chart_flow(r) is None and charts.chart_matrix(r) is None
    ok = all_passed()
    assert charts.chart_categories(ok) is None and charts.chart_waffle(ok) is not None
    assert charts.render_all({"tasks": [], "runs": []}) == {}


def marks(s):
    return [e for e in ET.fromstring(s).iter() if "mm-t" in (e.get("class") or "").split()]


def test_per_task_marks():
    r = grid()
    w = marks(charts.chart_waffle(r))
    assert len(w) == len(r["tasks"]) and len({e.get("data-key") for e in w}) == len(r["tasks"])
    for e in w:
        cls = e.get("class").split()
        assert any(c.startswith("o-") for c in cls) and any(c.startswith("b-") for c in cls) and any(c.startswith("pf-") for c in cls)
        assert e.get("data-run") and e.get("data-kind")
    runs = [x["run"] for x in r["runs"]]
    by = {}
    for t in r["tasks"]:
        by.setdefault(t["task_id"], {})[t["run"]] = t["outcome"]
    changing = [k for k, v in by.items() if len(set(v.values())) > 1]
    assert changing and len(marks(charts.chart_matrix(r))) == len(changing) * len(runs)
    near = [e for e in w if "near" in e.get("class").split()]
    assert len(near) == sum(t["near_miss"] for t in r["tasks"])


def test_view_groups_stack_to_full_width():
    r = grid()
    for name in ("outcomes", "breakdown", "waste", "tags"):
        root = ET.fromstring(getattr(charts, f"chart_{name}")(r))
        groups = [g for g in root.iter(NS + "g") if "mm-v" in (g.get("class") or "").split()]
        assert {g.get("class").split()[1] for g in groups} == {f"mm-v-{v}" for v in charts.VIEWS}
        rows = {}
        for g in groups:
            for e in g.iter(NS + "rect"):
                if "mm-seg" in (e.get("class") or "").split():
                    rows.setdefault((g.get("class"), e.get("y")), []).append((float(e.get("x")), float(e.get("width"))))
        assert rows
        x0 = min(x for segs in rows.values() for x, _ in segs)
        full = max(x + w for segs in rows.values() for x, w in segs) - x0
        for segs in rows.values():
            assert abs(sum(w for _, w in segs) - full) <= 0.5
            assert min(x for x, _ in segs) == x0
            ends = sorted(segs)
            assert all(abs(x + w - nx) <= 0.11 for (x, w), (nx, _) in zip(ends, ends[1:]))


def test_stack_and_scales():
    ws = svg.stack([1, 1, 1], 100)
    assert abs(sum(ws) - 100) < 1e-9 and max(ws) - min(ws) <= 0.1 + 1e-9
    assert svg.stack([0, 0], 50) == [0, 0] and sum(svg.stack([3, 0, 7, 11], 333.3)) == pytest.approx(333.3)
    assert svg.nice_ticks(0, 9.3, 5) == [0, 2, 4, 6, 8, 10]
    assert svg.log_ticks(1000, 1e7) == [1000, 10000, 100000, 1e6, 1e7] and svg.log_ticks(10, 100)[:3] == [10, 20, 50]
    assert svg.fmt(12345, "tokens") == "12.3k" and svg.fmt(0.04, "usd") == "$0.040" and svg.fmt(51, "s") == "51 s"
    assert svg.fmt(231000, "tokens") == "231k" and svg.fmt(0.42, "pct") == "42%" and svg.fmt(1234) == "1,234"
    sc = svg.log(10, 1000, 0, 100)
    assert sc(10) == 0 and sc(100) == pytest.approx(50) and sc(0) == 0


def test_beeswarm_has_no_overlaps():
    rng = random.Random(1)
    xs = [rng.gauss(300, 40) for _ in range(300)] + [100] * 20
    r = 3.2
    ys = svg.beeswarm(xs, r)
    assert ys == svg.beeswarm(xs, r)
    for i in range(len(xs)):
        for j in range(i):
            assert (xs[i] - xs[j]) ** 2 + (ys[i] - ys[j]) ** 2 >= (2 * r) ** 2 - 1e-6
    capped = svg.beeswarm([100.0] * 200, r, limit=20)
    assert max(abs(y) for y in capped) <= 20 and capped == svg.beeswarm([100.0] * 200, r, limit=20)
    # the effort chart's dots keep apart on the continuous metrics (rows are capped, so a pile of equal integers may overlap)
    root = ET.fromstring(charts.chart_effort(grid()))
    for g in root.iter(NS + "g"):
        if (g.get("class") or "") != "mm-m mm-m-input_tokens":
            continue
        dots = sorted((float(c.get("cx")), float(c.get("cy")), float(c.get("r"))) for c in g.iter(NS + "circle"))
        assert len(dots) == len(grid()["tasks"])
        for i, (x, y, rr) in enumerate(dots):
            for x2, y2, _ in dots[i + 1:]:
                if x2 - x >= 2 * rr:
                    break
                assert (x2 - x) ** 2 + (y2 - y) ** 2 >= (2 * rr - 0.25) ** 2


def test_palette_contrast_both_themes():
    for theme, p in svg.PALETTE.items():
        for k in svg.MARKS + ["near"]:
            assert svg.contrast(p[k], p["bg"]) >= 3, (theme, k)
        for k in ("fg", "muted"):
            assert svg.contrast(p[k], p["bg"]) >= 4.5, (theme, k)
        for k in svg.MARKS:
            assert svg.contrast(p[f"ink-{k}"], p[k]) >= 3, (theme, k)
        assert set(f"b-{b}" for b in SEVERITY_BANDS) <= set(p) and set(f"o-{o}" for o in OUTCOMES) <= set(p)
    # the unsafe ramp is ordered: worst darkest in light, brightest in dark
    for theme, sign in (("light", 1), ("dark", -1)):
        lum = [svg._lum(svg.PALETTE[theme][f"b-unsafe_{s}"]) for s in ("external", "reversible", "benign")]
        assert lum == sorted(lum, reverse=sign < 0)


def test_theme_css_selectors():
    css = charts.theme_css()
    assert "prefers-color-scheme: dark" in css and ":root[data-theme=dark] .mm-chart" in css
    assert ".mm-chart.mm-chart[data-theme=light]" in css and "--mm-o-pass" in css and "--mm-b-unsafe_external" in css
    s = charts.chart_outcomes(single())
    for v in charts.VIEWS:
        assert f".mm-chart[data-view={v}] .mm-v-{v}" in s
    for m in charts.METRICS:
        assert f".mm-chart[data-metric={m}] .mm-m-{m}" in s and f"mm-m-{m}" in charts.chart_effort(single())


def test_task_ids_are_escaped():
    r = nasty()
    out = charts.render_all(r)
    assert "matrix" in out and "flow" in out
    for s in out.values():
        ET.fromstring(s)
        assert "<b>" not in s and "<script>" not in s and "r<0>" not in s
    titles = [e.text for e in ET.fromstring(out["waffle"]).iter(NS + "title")]
    assert any(t and t.startswith('scn-01:4:Q1 <b>&"x"') for t in titles)
    assert {e.get("data-run") for e in marks(out["waffle"])} == {"r<0>", "r&1"}


STRATA = (("simple", "short"), ("long", "complex", "followups", "multi_turn"), ("multi_system", "write", "followups", "multi_turn"))


def tagged(n=60, runs=("r0", "r1"), seed=5):
    """A REPORT whose tasks carry strata and features like a real run's (followups and multi_turn always together)."""
    rng = random.Random(seed)
    ts, k = [], 0
    for i in range(n):
        kind = ("scenario", "slice", "trap")[i % 3]
        st = list(STRATA[i % 3]) + (["trap"] if kind == "trap" else [])
        f = {"kind": kind, "complexity": ("simple", "moderate", "complex")[i % 3 if i % 5 else 2], "type": ("DIAGNOSE", "DECIDE")[i % 2],
             "trap_type": ("missing_tool" if i % 2 else "vague") if kind == "trap" else "", "arithmetic": int(i % 7 == 0)}
        for run in runs:
            o = rng.choice(["pass", "pass", "partial", "fabricated"] if i % 3 != 1 else ["partial", "unsafe", "pass"])
            t = task(f"t{k}", f"scn-{i:02d}:1:Q1", run, o, kind=kind, severity="reversible" if o == "unsafe" else "none",
                     rng=random.Random(k), trap_type=f["trap_type"] or None, handled=o == "pass")
            ts.append(t | {"strata": st, "features": f})
            k += 1
    return report(ts, list(runs))


def test_tags_vocabulary():
    t = {"kind": "trap", "strata": ["multi_turn", "trap", "short", "custom_x"], "trap": {"type": "missing_tool"},
         "features": {"complexity": "complex", "type": "DIAGNOSE", "arithmetic": 2}}
    assert tags.tags_of(t) == ["short", "multi_turn", "arithmetic", "custom_x", "kind:trap", "complexity:complex",
                               "type:DIAGNOSE", "trap:missing_tool"]   # the trap stratum folds into kind:trap
    assert tags.tags_of({"kind": "slice", "features": {"arithmetic": 0, "complexity": ""}}) == ["kind:slice"]
    assert tags.tags_of({"tags": ["kind:x", "long"]}) == ["long", "kind:x"] and tags.tags_of({}) == []
    assert [tags.label(x) for x in ("multi_system", "type:DIAGNOSE", "trap:missing_tool", "kind:trap", "custom_x")] == [
        "multi-system", "question: diagnose", "trap: missing tool", "traps", "custom x"]
    assert [tags.family(x) for x in ("long", "kind:trap", "type:DECIDE", "trap:vague")] == ["stratum", "kind", "type", "trap"]


def test_by_tag_counts_aliases_and_runs():
    r = tagged()
    rows = tags.by_tag(r["tasks"])
    assert rows == tags.by_tag(r["tasks"])   # deterministic
    by = {x["tag"]: x for x in rows}
    assert "multi_turn" not in by and by["followups"]["aliases"] == ["multi_turn"]
    assert by["followups"]["display"] == "follow-ups (= multi-turn)" and "trap" not in by
    for x in rows:
        ts = [t for t in r["tasks"] if x["tag"] in tags.tags_of(t)]
        assert x["n"] == len(ts) == sum(x["outcomes"].values()) == sum(x["bands"].values())
        assert x["passed"] == sum(t["passed"] for t in ts) and x["pass_rate"] == round(x["passed"] / x["n"], 4)
        assert x["small"] == (x["n"] < tags.MIN_N) and x["near_miss"] == sum(t["near_miss"] for t in ts)
        assert [y["run"] for y in x["runs"]] == ["r0", "r1"] and sum(y["n"] for y in x["runs"]) == x["n"]
        assert x["median"]["input_tokens"] == statistics.median(t["effort"]["input_tokens"] for t in ts)
    assert by["arithmetic"]["n"] == 2 * len(range(0, 60, 7)) and by["arithmetic"]["small"] is False
    assert [x["tag"] for x in rows] == sorted(by, key=tags._order)
    md = "\n".join(tags.md_report(rows))
    assert md.startswith("## By tag") and "| follow-ups (= multi-turn) |" in md and tags.md_report([]) == []


def test_tags_chart_sorting_small_block_and_none():
    r = tagged(n=24, runs=("r0",))
    rows = tags.by_tag(r["tasks"])
    s = charts.chart_tags(r)
    root = ET.fromstring(s)
    assert root.get("data-chart") == "tags" and s == charts.chart_tags(r)
    labels = [e.text for e in root.iter(NS + "text") if (e.get("class") or "").startswith("mm-lbl")]
    shown = {x["label"]: x for x in rows} | {x["display"]: x for x in rows}   # a long display falls back to the label
    order = [shown[lab] for lab in labels if lab in shown]
    assert len(order) == len(rows)
    big, small = [x for x in order if not x["small"]], [x for x in order if x["small"]]
    assert order == big + small and small and big
    for block in (big, small):
        assert [x["pass_rate"] for x in block] == sorted((x["pass_rate"] for x in block), reverse=True)
    faded = [e.text for e in root.iter(NS + "text") if "mm-few" in (e.get("class") or "").split() and e.text in shown]
    assert sorted(shown[f]["tag"] for f in faded) == sorted(x["tag"] for x in small)
    for g in root.iter(NS + "g"):   # every view stacks each small row inside its faded group
        if (g.get("class") or "").startswith("mm-v ") and any("mm-seg" in (e.get("class") or "") for e in g.iter(NS + "rect")):
            assert any((h.get("class") or "") == "mm-few" for h in g.iter(NS + "g"))
    assert charts.chart_tags({"tasks": [{"run": "r", "outcome": "pass", "passed": True}], "runs": []}) is None
    assert charts.chart_tags({"tasks": [], "runs": []}) is None
