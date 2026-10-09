"""compare_html: the self-contained comparison page over a hand-built COMPARE, stub comparison charts and each side's real
single-report charts. No model calls, no browser."""
import copy
import re
from collections import Counter

from mockmcp.eval import charts as CH
from mockmcp.eval import compare_html as CMP

from test_eval_charts import grid, single

COMPARE_CHARTS = CMP.COMPARE_ORDER


def _change(a, b):
    return {(True, True): "both_pass", (True, False): "a_only", (False, True): "b_only", (False, False): "both_fail"}[
        bool(a["passed"]), bool(b["passed"])]


def fixture_compare(a, b, labels=("haiku", "sonnet"), rename=None):
    """A COMPARE per the contract from two REPORTs: runs paired by name (or `rename` {A run: B run}), tasks by task_id."""
    rename = rename or {}
    tasks, runs = [], []
    for r in a["runs"]:
        rb = rename.get(r["run"], r["run"])
        ta = {t["task_id"]: t for t in a["tasks"] if t["run"] == r["run"]}
        tb = {t["task_id"]: t for t in b["tasks"] if t["run"] == rb}
        common = sorted(set(ta) & set(tb))
        h2h = Counter(_change(ta[k], tb[k]) for k in common)
        n = len(common) or 1
        side = lambda ts: {"passed": sum(t["passed"] for t in ts), "pass_rate": sum(t["passed"] for t in ts) / n,
                           "cost_usd": sum(t["effort"]["cost_usd"] for t in ts)}
        sa, sb = side([ta[k] for k in common]), side([tb[k] for k in common])
        runs.append({"run": r["run"], "budget": r["budget"], "common": len(common), "only_a": len(set(ta) - set(tb)),
                     "only_b": len(set(tb) - set(ta)), "a": sa, "b": sb, "delta": {"pass_rate": sb["pass_rate"] - sa["pass_rate"]},
                     "ratio": {"cost_usd": sb["cost_usd"] / sa["cost_usd"] if sa["cost_usd"] else None, "input_tokens": 1.25,
                               "seconds": 0.8, "tool_calls": None},
                     "head_to_head": {k: h2h[k] for k in ("both_pass", "a_only", "b_only", "both_fail")}, "mcnemar_p": 0.0312,
                     "transitions": [], "band_transitions": []})
        for k in common:
            ea, eb = ta[k], tb[k]
            shift = "same" if ea["band_rank"] == eb["band_rank"] else "better" if eb["band_rank"] > ea["band_rank"] else "worse"
            side_task = lambda e: {f: e.get(f) for f in ("key", "outcome", "band", "band_rank", "passed", "near_miss", "severity",
                                                          "categories", "trap_handled", "judge", "effort", "calls", "notes", "files")}
            tasks.append({"key": f"c{len(tasks)}", "task_id": k, "run": r["run"], "budget": r["budget"], "kind": ea["kind"],
                          "trap": ea.get("trap"), "change": _change(ea, eb), "shift": shift, "a": side_task(ea), "b": side_task(eb)})
    return {"compare_version": 1, "labels": list(labels), "sources": ["runs/x-haiku", "runs/x-sonnet"], "verdict_source": "judge.json",
            "unpaired": {"only_a_runs": [], "only_b_runs": []}, "a": a, "b": b, "runs": runs, "tasks": tasks}


def with_notes(rep, tag):
    for t in rep["tasks"]:
        t["notes"] = {"rationale": f"{tag} judge on {t['task_id']}", "trap_notes": "", "unsupported_claims": [], "per_turn": [],
                      "actions": [], "offending": ""}
        t["judge"] = {"backend": "claude-code", "model": "sonnet", "confidence": 0.8}
        t["files"] = {"trace": f"../{tag}/{t['run']}/{t['task_id']}/trace.jsonl"}
    return rep


def sides(n=40):
    """Two 4-run grids over the same task ids with different outcome draws (A seed 7, B seed 11)."""
    return with_notes(grid(n, seed=7), "A"), with_notes(grid(n, seed=11), "B")


def stub_chart(name, cmp):
    """A comparison chart SVG carrying the contract: root attributes, view groups, a gradient referenced by url(#),
    and per-task marks keyed by comparison key."""
    marks = "".join(f'<rect class="mm-t o-{t["b"]["outcome"]} b-{t["b"]["band"]} pf-{"pass" if t["b"]["passed"] else "fail"}" '
                    f'data-key="{t["key"]}" data-kind="{t["kind"]}" data-run="{t["run"]}" x="{4 * i}" y="20" width="3" height="3"/>'
                    for i, t in enumerate(cmp["tasks"]) if name in ("paired", "diffs"))
    metric = ' data-metric="input_tokens"' if name == "paired" else ""
    views = "".join(f'<g class="mm-v mm-v-{v}"><rect width="10" height="2"/></g>' for v in ("binary", "outcome", "severity"))
    return (f'<?xml version="1.0" encoding="utf-8"?><svg xmlns="http://www.w3.org/2000/svg" class="mm-chart mm-{name}" '
            f'data-chart="{name}" data-view="outcome"{metric} role="img" aria-labelledby="{name}-t {name}-d" viewBox="0 0 760 60" '
            f'width="100%"><title id="{name}-t">{name}</title><desc id="{name}-d">stub</desc><defs><linearGradient id="{name}-g"/>'
            f'</defs><rect fill="url(#{name}-g)" width="1" height="1"/><use href="#{name}-g"/>{views}{marks}</svg>')


def build(n=40):
    a, b = sides(n)
    cmp = fixture_compare(a, b)
    return cmp, {c: stub_chart(c, cmp) for c in COMPARE_CHARTS}, CH.render_all(a), CH.render_all(b)


def test_namespace_svg_prefixes_ids_refs_and_keys():
    s = stub_chart("paired", fixture_compare(*sides(4)))
    out = CMP.namespace_svg(s, "x-")
    assert 'id="x-paired-t"' in out and 'id="x-paired-d"' in out and 'id="x-paired-g"' in out
    assert 'aria-labelledby="x-paired-t x-paired-d"' in out and 'url(#x-paired-g)' in out and 'href="#x-paired-g"' in out
    assert 'data-key="x-c0"' in out and 'data-key="c0"' not in out
    assert 'data-chart="paired"' in out and 'class="mm-chart mm-paired"' in out   # nothing else touched
    assert CMP.namespace_svg("", "x-") == "" and CMP.namespace_svg(None, "x-") == ""


def test_every_chart_inlined_and_ids_unique():
    cmp, c, ca, cb = build()
    html = CMP.render_html(cmp, c, ca, cb)
    assert set(ca) == set(CH.CHARTS) and set(cb) == set(CH.CHARTS)
    pos = [html.index(f'id="chart-{n}"') for n in COMPARE_CHARTS]
    assert pos == sorted(pos)
    for n in CH.CHARTS:
        assert f'id="a-chart-{n}"' in html and f'id="b-chart-{n}"' in html
        assert html.count(f'data-chart="{n}"') == 2 + (n in COMPARE_CHARTS)   # "outcomes" is in both sets
    ids = re.findall(r'\sid="([^"]*)"', html)
    dup = [k for k, v in Counter(ids).items() if v > 1]
    assert not dup, dup[:5]
    assert "<?xml" not in html and "xmlns" not in html
    # every aria reference resolves to an element on the page
    for refs in re.findall(r'aria-labelledby="([^"]*)"', html):
        assert all(r in set(ids) for r in refs.split()), refs


def test_split_rows_level_and_ordered():
    cmp, c, ca, cb = build()
    del cb["matrix"]
    html = CMP.render_html(cmp, c, ca, cb)
    split = html[html.index('id="split"'):html.index('id="tasks-section"')]
    rows = re.findall(r'data-row="([^"]+)"', split)
    assert rows == [n for n in CH.CHARTS for _ in (0, 1)]        # A then B, chart by chart, in charts.CHARTS order
    assert split.index('id="a-chart-waffle"') < split.index('id="b-chart-waffle"') < split.index('id="a-chart-outcomes"')
    assert "No “Tasks that change across budgets” chart for sonnet." in split
    assert split.count('class="pane-h c-side-a"') == 1 and split.count('class="pane-h c-side-b"') == 1
    assert 'data-key="a-t0"' in split and 'data-key="b-t0"' in split and 'data-key="t0"' not in split


def test_row_per_common_task_with_side_keys():
    cmp, c, ca, cb = build()
    html = CMP.render_html(cmp, c, ca, cb)
    assert html.count('<details class="task') == len(cmp["tasks"]) == 160
    for t in cmp["tasks"]:
        assert f'id="cmp-{t["key"]}" data-i=' in html
        assert f'data-key="{t["key"]}" data-a="{t["a"]["key"]}" data-b="{t["b"]["key"]}"' in html
    assert html.count('data-differ="1"') == sum(CMP.differs(t) for t in cmp["tasks"])
    changes = [m for m in re.findall(r'<details class="task ([\w-]+)"', html)]
    first = [x for x in changes if x != "c-side-b"]
    assert changes[0] == "c-side-b" and changes.index(first[0]) == sum(t["change"] == "b_only" for t in cmp["tasks"])
    assert 'data-key="cmp-c0"' in html   # comparison chart marks map straight to row ids


def test_both_judges_notes_side_by_side():
    cmp, *_ = build(8)
    html = CMP.render_html(cmp, {}, {}, {})
    t = cmp["tasks"][3]
    row = html[html.index(f'id="cmp-{t["key"]}"'):]
    row = row[:row.index("</details>")]
    a, b = row.index(f"A judge on {t['task_id']}"), row.index(f"B judge on {t['task_id']}")
    assert row.index('class="sidecol c-side-a"') < a < row.index('class="sidecol c-side-b"') < b
    assert 'href="./../A/' in row and 'href="./../B/' in row


def test_escaping():
    cmp, *_ = build(8)
    cmp["labels"] = ["<b>haiku</b>", 'son"net&']
    cmp["tasks"][0]["a"]["notes"]["rationale"] = "Said <b>42</b> & then </script><script>alert(1)</script>"
    cmp["tasks"][0]["b"]["notes"]["unsupported_claims"] = ["<img src=x onerror=alert(1)>"]
    html = CMP.render_html(cmp, {}, {}, {})
    assert "Said &lt;b&gt;42&lt;/b&gt; &amp; then &lt;/script&gt;" in html and "&lt;b&gt;haiku&lt;/b&gt;" in html
    assert "<b>42</b>" not in html and "alert(1)</script>" not in html and "<img src=x" not in html and "<b>haiku" not in html
    assert len(re.findall(r"<script\b", html)) == 2


def test_offline_no_urls():
    cmp, c, ca, cb = build()
    html = CMP.render_html(cmp, c, ca, cb)
    assert "http://" not in html and "https://" not in html and not re.search(r'(src|href)="//', html)


def test_controls_and_modes():
    cmp, c, ca, cb = build()
    html = CMP.render_html(cmp, c, ca, cb)
    for v in ("auto", "light", "dark"):
        assert f'name="theme" value="{v}"' in html
    for v in ("binary", "outcome", "severity"):
        assert f'name="view" value="{v}"' in html
    assert 'name="mode" value="overview" checked' in html and 'name="mode" value="split"' in html
    assert 'id="overview"' in html and 'id="split"' in html and 'data-mode="overview"' in html
    assert 'id="metric"' in html and 'id="f-kind"' in html and 'id="f-run"' in html and 'id="f-differ" checked' in html
    for k in ("task", "a", "b", "change", "shift", "tokens", "secs", "calls"):
        assert f'data-sort="{k}"' in html
    assert "localStorage" in html and "mm-dim" in html and '<option value="tokens-25000">' in html
    assert html.index('id="overview"') < html.index('id="split"') < html.index('id="rows"')   # no JS: overview, panes, table


def test_side_runs_renamed_to_paired_names():
    a, b = with_notes(single(12), "A"), with_notes(single(12, seed=5), "B")
    for t in b["tasks"]:
        t["run"] = "other"
    b["runs"][0]["run"] = "other"
    cmp = fixture_compare(a, b, rename={"smoke": "other"})
    html = CMP.render_html(cmp, {}, CH.render_all(a), CH.render_all(b))
    split = html[html.index('id="split"'):html.index('id="tasks-section"')]
    assert 'data-run="other"' not in split and 'data-run="smoke"' in split
    assert 'id="f-run"' not in html and "one-run" in html


def test_renders_empty_and_minimal():
    cmp, *_ = build(8)
    html = CMP.render_html(cmp, {}, {}, {})
    assert "No comparison charts." in html and "No single-report charts for either side." in html and 'id="metric"' not in html
    html = CMP.render_html(cmp, {"scoreboard": None, "paired": ""}, None, {"waffle": ""})
    assert "No comparison charts." in html
    bare = CMP.render_html({}, {}, {}, {})
    assert "A</span><span class=\"and\">vs</span><span class=\"side c-side-b\">B" in bare and 'id="rows"' in bare
    assert "No common tasks" in bare


def test_banners():
    cmp, *_ = build(8)
    cmp = copy.deepcopy(cmp)
    cmp["unpaired"] = {"only_a_runs": ["tokens-200000"], "only_b_runs": []}
    cmp["runs"][0]["only_b"] = 3
    cmp["b"]["summary"] = {"provisional": 4, "judge_warning": "decision model: unreliable per task"}
    html = CMP.render_html(cmp, {}, {}, {})
    assert "Runs on one side only, left out." in html and "<code>tokens-200000</code>" in html
    assert "3 tasks ran on one side only" in html and "4 on sonnet" in html and "decision model: unreliable per task" in html


def test_kpis_and_theme():
    cmp, *_ = build()
    k = {x["label"]: x for x in CMP.kpis(cmp["tasks"], cmp["labels"])}
    pa = sum(t["a"]["passed"] for t in cmp["tasks"])
    pb = sum(t["b"]["passed"] for t in cmp["tasks"])
    n = len(cmp["tasks"])
    assert k["Pass rate"]["value"] == f"{100 * pa / n:.0f}% → {100 * pb / n:.0f}%"
    ch = Counter(t["change"] for t in cmp["tasks"])
    assert k["Head to head"]["value"] == f"{ch['a_only']} vs {ch['b_only']}"
    assert CMP.mcnemar(0, 0) == 1.0 and abs(CMP.mcnemar(1, 9) - 0.021484375) < 1e-9
    assert (CMP.fmt_ratio(3.14), CMP.fmt_ratio(None), CMP.fmt_pts(-0.062), CMP.fmt_p(0.2134)) == ("3.1×", "n/a", "−6.2 pts", "p 0.21")
    css = CMP.vars_css()
    assert css.count("--mm-side-a:") >= 3 and css.count("--mm-side-b:") >= 3 and ":root[data-theme=dark]{" in css
    html = CMP.render_html(cmp, {}, {}, {})
    page_css = html[html.index("<style>"):html.index("</head>")].split("</style>", 1)[1]
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", page_css)
