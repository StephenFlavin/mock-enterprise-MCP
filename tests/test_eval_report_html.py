"""report_html: the self-contained HTML page over a hand-made REPORT and stub chart SVGs. No model calls, no browser."""
import re

from mockmcp.eval import report_html as RH
from mockmcp.eval.schema import SEVERITY_BANDS

CHARTS = RH.CHART_ORDER
OUTCOME_MIX = [("pass", "none"), ("partial", "none"), ("fabricated", "none"), ("pass", "none"), ("unsafe", "external_or_irreversible"),
               ("honest_fail", "none"), ("over_cautious", "none"), ("pass", "none"), ("unsafe", "reversible"), ("partial", "none")]


def band(outcome, severity):
    return {"external_or_irreversible": "unsafe_external", "reversible": "unsafe_reversible"}.get(severity, "unsafe_benign") \
        if outcome == "unsafe" else outcome


def fixture_task(i, run, n_run, traps=True):
    """One REPORT task; every third is a trap when `traps`. Outcomes cycle through OUTCOME_MIX, shifted per run."""
    outcome, sev = OUTCOME_MIX[(i + 3 * n_run) % len(OUTCOME_MIX)]
    kind = "trap" if traps and i % 3 == 2 else "scenario"
    passed = outcome == "pass" or (kind == "trap" and outcome == "honest_fail")
    b = band(outcome, sev)
    handled = (outcome in ("pass", "honest_fail", "partial")) if kind == "trap" else None
    tid = f"{'trap' if kind == 'trap' else 'scn'}-0{i % 7 + 1}:{i}:Q{i % 4 + 1}"
    inp = 18000 * (1 + i % 5) * (3 if not passed else 1) * (1 + n_run)
    return {
        "key": None, "task_id": tid, "run": run, "budget": f"~{33 * (n_run + 1)}k tokens", "budget_tokens": 33000 * (n_run + 1),
        "budget_tools": 144 * (n_run + 1), "kind": kind, "question_id": f"0{i % 7 + 1}:{i}:Q{i % 4 + 1}", "domain": "Warehouse ops",
        "strata": ["multi_system"] if i % 2 else [], "features": {"systems": 2},
        "trap": {"type": ["missing_system", "vague", "missing_entity"][i % 3], "variant": "lookalike" if i % 2 else None,
                 "tier": "T2", "difficulty": "hard" if i % 4 == 0 else "standard", "trap_turn": i % 2} if kind == "trap" else None,
        "outcome": outcome, "passed": passed, "categories": [] if passed else ["missed_step", "incomplete"][: 1 + i % 2],
        "severity": sev, "band": b, "band_rank": SEVERITY_BANDS.index(b),
        "near_miss": not passed and (outcome == "partial" or (kind == "trap" and handled is True)), "trap_handled": handled,
        "judge": {"backend": "claude-code", "model": "sonnet", "confidence": 0.7, "provisional": False, "cost_usd": 0.1,
                  "escalated": None, "warning": None},
        "notes": {"rationale": f"The answer gave the dock count for {tid} but missed the carrier ETA in turn 2.",
                  "trap_notes": "Said the supplier portal was not loaded." if kind == "trap" else "",
                  "unsupported_claims": [] if outcome != "fabricated" else ["ETA 14:20 for PO-4471"],
                  "per_turn": [{"turn": 0, "outcome": "pass", "notes": "found the dock"},
                               {"turn": 1, "outcome": outcome, "notes": "carrier ETA missing"}],
                  "actions": [{"tool": "tms.cancel_shipment", "args": {"shipment": "SH-1", "reason": "x" * 400}, "turn": 1,
                               "requested": False, "justified": False, "severity": sev, "why": "not asked for"}] if outcome == "unsafe" else [],
                  "offending": "tms.cancel_shipment" if outcome == "unsafe" else ""},
        "effort": {"class": ["fast", "typical", "costly"][i % 3], "cost_usd": 0.01 * (1 + i % 4), "input_tokens": inp,
                   "output_tokens": 900 + 50 * i, "cache_read": inp // 2, "seconds": 9.5 + 4 * i, "tool_calls": 3 + i % 9,
                   "turns_total": 2, "turns_passed": 2 if passed else 1},
        "calls": {"total": 3 + i % 9, "errors": i % 3, "exact_repeats": i % 2, "same_tool_repeats": i % 4, "distractor": n_run * (i % 2),
                  "decoy": int(kind == "trap" and i % 2 == 1), "writes": int(outcome == "unsafe"), "failed_writes": 0,
                  "by_turn": [2, 1 + i % 9], "servers": {"wms": 2, "tms": 1 + i % 9}},
        "files": {k: f"{run}/{tid}/{f}" for k, f in (("answers", "answers.json"), ("trace", "trace.jsonl"),
                                                      ("checks", "checks.json"), ("judge", "judge.json"))},
    }


def fixture_report(runs=("tokens-0", "tokens-50000"), n=10, traps=True, provisional=0, warning=None):
    """A REPORT per the contract: `n` tasks in each run, keys t0, t1, ... unique across runs."""
    tasks = [fixture_task(i, run, k, traps) for k, run in enumerate(runs) for i in range(n)]
    for k, t in enumerate(tasks):
        t["key"] = f"t{k}"
    out = []
    for k, run in enumerate(runs):
        rs = [t for t in tasks if t["run"] == run]
        failed = [t for t in rs if not t["passed"]]
        tok = sum(t["effort"]["input_tokens"] for t in rs)
        out.append({"run": run, "budget": rs[0]["budget"], "median_tools": 144 * k, "median_tokens": 33000 * k, "tasks": len(rs),
                    "passed": len(rs) - len(failed), "outcomes": {}, "bands": {}, "near_miss": sum(t["near_miss"] for t in rs),
                    "metrics": {"cost_per_pass_usd": 0.0412, "input_tokens": {"median": tok / len(rs)}, "seconds": {"median": 31.2}},
                    "effort_thresholds": {"basis": "passes", "n": 4, "input_total": [32000, 140000], "tool_calls": [3, 11]},
                    "waste": {"share_failed": {"input_tokens": sum(t["effort"]["input_tokens"] for t in failed) / tok}}})
    defs = {"outcomes": {"pass": "all facts given", "partial": "some facts right"}, "categories": {"missed_step": "never called a required tool"},
            "severity": {"reversible": "internal record"}, "terms": {"trap": "a question that cannot be answered as asked"},
            "bands": {b: f"band {b}" for b in SEVERITY_BANDS}, "effort": {"fast": "cheap", "typical": "usual", "costly": "≥ p90 of passes"},
            "near_miss": "failed, but partial or the trap was handled"}
    return {"report_version": 1, "title": "scale-demo", "verdict_source": "judge.json",
            "summary": {"model": "haiku", "judge": "claude-code sonnet", "provisional": provisional, "judge_warning": warning},
            "definitions": defs, "runs": out, "tasks": tasks}


def stub_chart(name, report):
    """A tiny SVG carrying the markup contract: root classes and attributes, view groups and per-task marks."""
    metric = ' data-metric="input_tokens"' if name == "effort" else ""
    marks = "".join(f'<rect class="mm-t o-{t["outcome"]} b-{t["band"]} pf-{"pass" if t["passed"] else "fail"}" data-key="{t["key"]}" '
                    f'data-kind="{t["kind"]}" data-run="{t["run"]}" x="{4 * i}" y="0" width="3" height="3"><title>{t["task_id"]}</title></rect>'
                    for i, t in enumerate(report["tasks"]))
    views = "".join(f'<g class="mm-v mm-v-{v}"><rect width="10" height="2"/></g>' for v in ("binary", "outcome", "severity"))
    return (f'<?xml version="1.0" encoding="utf-8"?><svg xmlns="http://www.w3.org/2000/svg" class="mm-chart mm-{name}" data-chart="{name}" '
            f'data-view="outcome"{metric} role="img" aria-labelledby="{name}-t {name}-d" viewBox="0 0 400 40" width="100%">'
            f'<title id="{name}-t">{name}</title><desc id="{name}-d">stub</desc>{views}{marks}</svg>')


def stub_charts(report):
    return {c: stub_chart(c, report) for c in CHARTS}


def test_every_chart_inlined_in_order():
    r = fixture_report()
    html = RH.render_html(r, stub_charts(r))
    pos = [html.index(f'data-chart="{c}"') for c in CHARTS]
    assert pos == sorted(pos)
    for c in CHARTS:
        assert html.count(f'data-chart="{c}"') == 1 and f'id="chart-{c}"' in html and f'download="{c}.svg"' in html
    assert "<?xml" not in html and "xmlns" not in html


def test_rationale_escaped():
    r = fixture_report()
    r["tasks"][0]["notes"]["rationale"] = "Said <b>42</b> & then </script><script>alert(1)</script>"
    r["tasks"][1]["notes"]["unsupported_claims"] = ["<img src=x onerror=alert(1)>"]
    html = RH.render_html(r, {})
    assert "Said &lt;b&gt;42&lt;/b&gt; &amp; then &lt;/script&gt;" in html
    assert "<b>42</b>" not in html and "alert(1)</script>" not in html and "<img src=x" not in html
    assert len(re.findall(r"<script\b", html)) == 2   # the theme bootstrap and the page script, nothing injected


def test_row_per_task_key():
    r = fixture_report(n=12)
    html = RH.render_html(r, stub_charts(r))
    keys = [t["key"] for t in r["tasks"]]
    assert len(keys) == 24
    for k in keys:
        assert html.count(f'<details class="task') and f'id="task-{k}"' in html
    assert html.count('<details class="task') == len(keys)
    assert html.count('data-pass="0"') == sum(not t["passed"] for t in r["tasks"])


def test_failures_listed_first_and_marked():
    r = fixture_report()
    html = RH.render_html(r, {})
    passes = [m.start() for m in re.finditer(r'data-pass="1"', html)]
    fails = [m.start() for m in re.finditer(r'data-pass="0"', html)]
    assert fails and passes and max(fails) < min(passes)
    assert "near miss" in html and "unsafe external" in html


def test_offline_no_urls():
    r = fixture_report()
    html = RH.render_html(r, stub_charts(r))
    assert "http://" not in html and "https://" not in html
    assert not re.search(r'(src|href)="//', html)
    assert 'href="./tokens-0/scn-01%3A0%3AQ1/answers.json"' in html   # ':' never read as a URL scheme


def test_controls_exist():
    r = fixture_report()
    html = RH.render_html(r, stub_charts(r))
    for v in ("auto", "light", "dark"):
        assert f'name="theme" value="{v}"' in html
    for v in ("binary", "outcome", "severity"):
        assert f'name="view" value="{v}"' in html
    assert 'id="metric"' in html and 'id="f-kind"' in html and 'id="f-run"' in html and 'id="f-fail"' in html
    for k in ("task", "outcome", "calls", "tokens", "secs"):
        assert f'data-sort="{k}"' in html
    assert "localStorage" in html and "mm-dim" in html and "data-view" in html and "data-metric" in html
    assert '<option value="trap">' in html and '<option value="tokens-50000">' in html


def test_theme_variables_once():
    r = fixture_report()
    html = RH.render_html(r, stub_charts(r))
    assert ":root[data-theme=dark]{" in RH.vars_css() and "--mm-o-pass:" in html and "prefers-color-scheme: dark" in html
    css = html[html.index("<style>"):html.index("</head>")]
    page_css = css.split("</style>", 1)[1]
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", page_css)   # the page's own styles use palette variables only


def test_renders_empty_charts_one_run_no_traps():
    r = fixture_report(runs=("solo",), n=6, traps=False)
    html = RH.render_html(r, {})
    assert "No charts for this report." in html and 'id="f-run"' not in html and "one-run" in html
    assert "no traps in this run" in html and 'id="metric"' not in html
    assert html.count('<details class="task') == 6
    html = RH.render_html(r, {"waffle": None, "effort": ""})
    assert "No charts for this report." in html


def test_banners_and_minimal_report():
    r = fixture_report(provisional=3, warning="decision model: unreliable per task")
    html = RH.render_html(r, {})
    assert "3 of 20 verdicts are provisional" in html and "decision model: unreliable per task" in html
    bare = RH.render_html({"tasks": [], "runs": []}, {})
    assert "<h1>eval</h1>" in bare and 'id="rows"' in bare


def test_charts_dir_and_formatting():
    assert RH.charts_dir("judge.json") == "charts" and RH.charts_dir("judge.claude-code.json") == "charts.claude-code"
    assert (RH.fmt_tokens(231000), RH.fmt_tokens(1_250_000), RH.fmt_secs(51.2), RH.fmt_usd(0.04123)) == ("231.0k", "1.2M", "51 s", "$0.0412")
