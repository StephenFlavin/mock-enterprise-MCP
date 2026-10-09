"""`eval compare --html`: one self-contained, offline page over a COMPARE (compare_data.build) and three sets of SVGs:
the comparison charts, and each side's single-report charts (charts.render_all on side A's and side B's REPORT).

Two modes share one toolbar (view, effort metric, kind and run filters): Overview (comparison charts, full width) and
Split screen (A's single-report charts in a left pane, B's in a right pane, chart k of A level with chart k of B). Below
both sits the comparison task table: one `<details id="cmp-<key>">` per common task, with both judges' notes side by
side. Every chart is namespaced (`namespace_svg`) so ids and task keys stay unique when the three sets share a page; a
mark in either pane, or a row's Open button, opens the comparison drawer: the task once, a shared facts table, then each
turn's prompt above both answers with highlighted found facts / fabricated / unverified spans (from each side's
`scenario` block) and each side's "why" box. The drawer's data sits in one `application/json` script (`embed_json`)
and is rendered with DOM calls only. Works without JS (overview, then the panes, rows expand; no drawer)."""
import json
import re
from collections import Counter
from pathlib import Path

import jinja2
from markupsafe import Markup

from . import report_html as RH

TEMPLATE = Path(__file__).parent / "compare_template.html"
COMPARE_ORDER = ("scoreboard", "headtohead", "bytag", "shift", "outcomes", "paired", "spend", "diffs")
CAPTIONS = {   # comparison chart -> (title, the question it answers)
    "scoreboard": ("Pass rate, side against side", "Who passes more, and is the difference more than chance?"),
    "headtohead": ("Head to head", "On the same tasks, who wins?"),
    "bytag": ("By tag: A vs B", "On which kinds of task does each model win?"),
    "shift": ("Where outcomes move", "Where do one side's failures go under the other, and the other way round?"),
    "outcomes": ("Outcome mix, side by side", "How do the two outcome mixes differ?"),
    "paired": ("Effort on the same task", "Which side burns more effort on the same task, and on which tasks?"),
    "spend": ("What it costs", "What does each side spend, and what does a pass cost?"),
    "diffs": ("Tasks that flip", "Which tasks change outcome between the two? Select a cell to open its row."),
}
SPLIT_CAPTIONS = {"tags": ("By tag", "Which kinds of task pass, and which fail?")}   # single-report charts report_html lacks
HL_KINDS = ("fact", "fabricated", "unverified", "derived")
PREFIX = {"cmp": "cmp-", "a": "a-", "b": "b-"}   # namespace of the comparison charts and of each side's charts
# Side colours: svg.PALETTE's --mm-side-a / --mm-side-b when it has them, these otherwise (slate and indigo, >= 3:1 on bg).
SIDE_FALLBACK = {"light": {"side-a": "#5a6b82", "side-b": "#5b54d6"}, "dark": {"side-a": "#94a3b8", "side-b": "#8f8cf5"}}
CHANGE_ORDER = ("b_only", "a_only", "both_fail", "both_pass")
SHIFT_RANK = {"worse": 0, "same": 1, "better": 2}
TERMS = [("head to head", "the common tasks split four ways: both pass, only A passes, only B passes, both fail"),
         ("McNemar p", "exact two-sided binomial test on the tasks only one side passes; below 0.05 the difference in pass "
                       "rate is unlikely to be chance"),
         ("shift", "B's severity band against A's on the same task: better, worse or the same"),
         ("ratio", "B's total over A's total on the common tasks (2.0× = B spent twice as much)"),
         ("common task", "a task both runs graded in the same paired run; tasks on one side only are left out")]


# ---- ids and keys --------------------------------------------------------------------------------------------------

def _prefix_list(m: re.Match, prefix: str) -> str:
    return f'{m.group(1)}="{" ".join(prefix + t for t in m.group(2).split())}"'


def namespace_svg(svg: str, prefix: str) -> str:
    """The chart with every id, `url(#…)`, `href="#…"`, aria-labelledby / aria-describedby reference and data-key value
    prefixed with `prefix`, so several reports' charts can share one page without clashing ids or task keys."""
    if not svg:
        return svg or ""
    svg = re.sub(r'(\sid)="([^"]*)"', lambda m: f'{m.group(1)}="{prefix}{m.group(2)}"', svg)
    svg = re.sub(r"url\(\s*(['\"]?)#", lambda m: f"url({m.group(1)}#{prefix}", svg)
    svg = re.sub(r'(\s(?:xlink:)?href)="#([^"]*)"', lambda m: f'{m.group(1)}="#{prefix}{m.group(2)}"', svg)
    svg = re.sub(r'(aria-(?:labelledby|describedby))="([^"]*)"', lambda m: _prefix_list(m, prefix), svg)
    return re.sub(r'(\sdata-key)="([^"]*)"', lambda m: f'{m.group(1)}="{prefix}{m.group(2)}"', svg)


def _rerun(svg: str, runs: dict[str, str]) -> str:
    """A side's run names on its marks (data-run) renamed to the paired run names, so one run filter drives both panes."""
    if not svg or not any(k != v for k, v in runs.items()):
        return svg
    return re.sub(r'(\sdata-run)="([^"]*)"', lambda m: f'{m.group(1)}="{runs.get(m.group(2), m.group(2))}"', svg)


def _side_runs(cmp: dict, side: str) -> dict[str, str]:
    """{the side's own run name: the paired run name}, from the side's REPORT tasks behind each comparison task."""
    by_key = {t.get("key"): t.get("run") for t in (cmp.get(side) or {}).get("tasks") or []}
    out = {}
    for t in cmp.get("tasks") or []:
        own = by_key.get((t.get(side) or {}).get("key"))
        if own is not None:
            out.setdefault(own, t.get("run"))
    return out


# ---- styles --------------------------------------------------------------------------------------------------------

def vars_css() -> str:
    """The shared palette on :root (report_html.vars_css), plus fallback side colours when the palette has none."""
    pal = RH._palette()
    if all(pal.get(t, {}).get(k) or pal.get(t, {}).get("--mm-" + k) for t in SIDE_FALLBACK for k in SIDE_FALLBACK[t]):
        return RH.vars_css()
    side = lambda theme: ";".join(f"--mm-{k}:{v}" for k, v in SIDE_FALLBACK[theme].items())
    return (RH.vars_css() + f":root{{{side('light')}}}"
            f"@media (prefers-color-scheme: dark){{:root:not([data-theme=light]){{{side('dark')}}}}}"
            f":root[data-theme=dark]{{{side('dark')}}}")


def _order(module: str, fallback: tuple) -> tuple:
    try:
        mod = __import__(f"{__package__}.{module}", fromlist=["CHARTS"])
        return tuple(mod.CHARTS)
    except Exception:   # built in parallel / optional: never fail the page over chart ordering
        return fallback


def _names(charts: dict, order: tuple) -> list[str]:
    charts = charts or {}
    return [c for c in order if charts.get(c)] + sorted(c for c in charts if c not in order and charts[c])


# ---- figures -------------------------------------------------------------------------------------------------------

def mcnemar(a_only: int, b_only: int) -> float:
    """Exact two-sided McNemar p (compare_data.mcnemar when it is importable)."""
    try:
        from .compare_data import mcnemar as m
        return m(a_only, b_only)
    except Exception:
        from math import comb
        n, k = a_only + b_only, min(a_only, b_only)
        return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def fmt_ratio(r) -> str:
    return "n/a" if r is None else f"{r:.2f}×" if r < 0.1 else f"{r:.1f}×" if r < 10 else f"{r:.0f}×"


def fmt_pts(d: float) -> str:
    return f"{100 * d:+.1f} pts".replace("-", "−")


def fmt_p(p) -> str:
    return "n/a" if p is None else "p < 0.001" if p < 0.001 else f"p {p:.3f}" if p < 0.01 else f"p {p:.2f}"


def _ratio(b, a):
    return b / a if a else None


def _eff(s: dict, k: str) -> float:
    return float(((s or {}).get("effort") or {}).get(k) or 0)


def _median(xs: list[float]) -> float:
    xs = sorted(xs)
    n = len(xs)
    return 0.0 if not n else xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def _winner(a, b, higher_better=True) -> str:
    """Tone of the side that does better on a figure ('c-side-a', 'c-side-b' or neutral)."""
    if a == b or a is None or b is None:
        return "c-none"
    return "c-side-b" if (b > a) == higher_better else "c-side-a"


def short(labels: list[str]) -> list[str]:
    """Labels for tight spots (table cells, tile notes): the labels when both are short, else "A" and "B"."""
    return list(labels) if max(len(x) for x in labels) <= 14 else ["A", "B"]


def kpis(tasks: list[dict], labels: list[str]) -> list[dict]:
    """Delta tiles over the common tasks: value 'A → B' (or B/A as ×), a one-line context, and a tone."""
    la, lb = short(labels)
    n = len(tasks)
    a, b = [t.get("a") or {} for t in tasks], [t.get("b") or {} for t in tasks]
    pa, pb = sum(bool(s.get("passed")) for s in a), sum(bool(s.get("passed")) for s in b)
    ch = Counter(t.get("change") for t in tasks)
    p = mcnemar(ch["a_only"], ch["b_only"])
    tot = lambda side, k: sum(_eff(s, k) for s in side)
    unsafe = lambda side: sum(s.get("outcome") == "unsafe" for s in side)
    ext = lambda side: sum(s.get("band") == "unsafe_external" for s in side)
    fab = lambda side: sum(s.get("outcome") == "fabricated" for s in side)
    ca, cb, ta, tb = tot(a, "cost_usd"), tot(b, "cost_usd"), tot(a, "input_tokens"), tot(b, "input_tokens")
    ma, mb = _median([_eff(s, "seconds") for s in a]), _median([_eff(s, "seconds") for s in b])
    cpa, cpb = (ca / pa if pa else None), (cb / pb if pb else None)
    return [
        {"label": "Pass rate", "value": f"{RH.pct(pa, n)} → {RH.pct(pb, n)}",
         "sub": (f"{fmt_pts((pb - pa) / n)} · McNemar {fmt_p(p)}" if n else "no common tasks") + (" · significant" if p < 0.05 else ""),
         "tone": _winner(pa, pb)},
        {"label": "Head to head", "value": f"{ch['a_only']} vs {ch['b_only']}",
         "sub": f"only {la} vs only {lb}; {ch['both_pass']} both pass, {ch['both_fail']} both fail", "tone": _winner(ch["a_only"], ch["b_only"])},
        {"label": "Unsafe", "value": f"{unsafe(a)} → {unsafe(b)}", "sub": f"external or irreversible {ext(a)} → {ext(b)}",
         "tone": _winner(unsafe(a), unsafe(b), False)},
        {"label": "Fabricated", "value": f"{fab(a)} → {fab(b)}", "sub": f"{RH.pct(fab(a), n)} → {RH.pct(fab(b), n)} of tasks",
         "tone": _winner(fab(a), fab(b), False)},
        {"label": "Cost", "value": fmt_ratio(_ratio(cb, ca)), "sub": f"{RH.fmt_usd(ca)} → {RH.fmt_usd(cb)} in all", "tone": _winner(ca, cb, False)},
        {"label": "Cost per pass", "value": f"{RH.fmt_usd(cpa)} → {RH.fmt_usd(cpb)}", "sub": f"{pa} → {pb} passes",
         "tone": _winner(cpa, cpb, False)},
        {"label": "Input tokens", "value": fmt_ratio(_ratio(tb, ta)), "sub": f"{RH.fmt_tokens(ta)} → {RH.fmt_tokens(tb)} in all",
         "tone": _winner(ta, tb, False)},
        {"label": "Median time", "value": f"{RH.fmt_secs(ma)} → {RH.fmt_secs(mb)}",
         "sub": f"per task; {fmt_ratio(_ratio(tot(b, 'seconds'), tot(a, 'seconds')))} in all", "tone": _winner(ma, mb, False)},
    ]


def run_rows(cmp: dict) -> list[dict]:
    """Per paired run: pass rates, delta, McNemar p, head to head and effort ratios."""
    out = []
    for r in cmp.get("runs") or []:
        a, b, h, ratio = r.get("a") or {}, r.get("b") or {}, r.get("head_to_head") or {}, r.get("ratio") or {}
        out.append({"run": r.get("run"), "budget": r.get("budget") or "", "common": r.get("common", 0),
                    "only": f"{r.get('only_a', 0)} / {r.get('only_b', 0)}",
                    "a": f"{100 * (a.get('pass_rate') or 0):.0f}%", "b": f"{100 * (b.get('pass_rate') or 0):.0f}%",
                    "delta": fmt_pts((r.get("delta") or {}).get("pass_rate") or 0), "p": fmt_p(r.get("mcnemar_p")),
                    "sig": (r.get("mcnemar_p") if r.get("mcnemar_p") is not None else 1) < 0.05,
                    "h2h": f"{h.get('a_only', 0)} vs {h.get('b_only', 0)}",
                    **{k: fmt_ratio(ratio.get(k)) for k in ("cost_usd", "input_tokens", "seconds", "tool_calls")}})
    return out


def differs(t: dict) -> bool:
    """Whether the two sides disagree on a task: pass/fail, outcome or severity band."""
    a, b = t.get("a") or {}, t.get("b") or {}
    return bool(a.get("passed")) != bool(b.get("passed")) or a.get("outcome") != b.get("outcome") or a.get("band") != b.get("band")


def _group(t: dict) -> int:
    """Default order: B fixes, A fixes, both fail differently, both pass differently, then the tasks that agree."""
    c = t.get("change")
    return {"b_only": 0, "a_only": 1}.get(c, (2 if c == "both_fail" else 3) + (0 if differs(t) else 2))


def task_row(t: dict, i: int, run_index: dict, reports: dict) -> dict:
    """One comparison row: both sides through report_html.task_view, plus change, shift, sort keys and the task facts."""
    sides = {}
    for s in ("a", "b"):
        side = t.get(s) or {}
        full = reports[s].get(side.get("key")) or {}
        sides[s] = RH.task_view({**full, **side, "task_id": t.get("task_id"), "run": t.get("run"), "kind": t.get("kind"),
                                 "judge": side.get("judge") or full.get("judge") or {}}, i, run_index)
    a, b = sides["a"], sides["b"]
    info = reports["a"].get((t.get("a") or {}).get("key")) or reports["b"].get((t.get("b") or {}).get("key")) or {}
    tok = _ratio(_eff(t.get("b"), "input_tokens"), _eff(t.get("a"), "input_tokens"))
    secs = _ratio(_eff(t.get("b"), "seconds"), _eff(t.get("a"), "seconds"))
    sort = {"task": t.get("task_id", ""), "run": run_index.get(t.get("run"), 0), "kind": t.get("kind", ""),
            "a": a["sort"]["outcome"], "b": b["sort"]["outcome"], "change": CHANGE_ORDER.index(t["change"]) if t.get("change") in CHANGE_ORDER else 9,
            "shift": SHIFT_RANK.get(t.get("shift"), 1), "tokens": round(tok, 4) if tok is not None else -1,
            "secs": round(secs, 4) if secs is not None else -1, "calls": b["n_calls"] - a["n_calls"]}
    return {**t, "i": i, "A": a, "B": b, "sort": sort, "differs": differs(t), "group": _group(t),
            "tok_ratio": fmt_ratio(tok), "secs_ratio": fmt_ratio(secs),
            "tok_title": f"input tokens {a['tokens']} → {b['tokens']}", "secs_title": f"time {a['secs']} → {b['secs']}",
            "question_id": info.get("question_id"), "domain": info.get("domain"), "strata": info.get("strata") or []}


# ---- drawer data ---------------------------------------------------------------------------------------------------

def embed_json(obj) -> str:
    """JSON safe inside a `<script type="application/json">`: `<`, `>` and `&` as `\\u` escapes, so no text in the data
    (a `</script>`, a `<!--`) can end the element; JSON.parse reads it back unchanged."""
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=str)
    return s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _tags_fn():
    try:
        from . import tags as T
        return T.tags_of
    except Exception:   # optional: fall back to the task's strata
        return None


def task_tags(t: dict) -> list[str]:
    """A REPORT task's tags (tags.tags_of when that module is there, else its strata), as unique strings in order."""
    fn = _tags_fn()
    try:
        tags = fn(t) if fn else t.get("strata")
    except Exception:
        tags = t.get("strata")
    return list(dict.fromkeys(str(x) for x in tags or [] if x not in (None, "")))


def _int(v, default=0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def scenario_view(sc) -> dict | None:
    """A side's `scenario` block (report_data contract) trimmed to what the drawer draws, with sorted, clamped,
    non-overlapping highlights (offsets in UTF-16 code units, as JS indexes strings); None when there is none."""
    if not isinstance(sc, dict):
        return None
    turns = []
    for i, tn in enumerate(sc.get("turns") or []):
        if not isinstance(tn, dict):
            continue
        text = str(tn.get("assistant") or "")
        n, end, hls = len(text.encode("utf-16-le")) // 2, 0, []
        for h in sorted((h for h in tn.get("highlights") or [] if isinstance(h, dict)), key=lambda h: _int(h.get("start"))):
            a, b = max(_int(h.get("start")), end), min(_int(h.get("end")), n)
            if b > a and h.get("kind") in HL_KINDS:
                hls.append({"start": a, "end": b, "kind": h["kind"], "note": str(h.get("note") or "")})
                end = b
        turns.append({"turn": _int(tn.get("turn"), i), "user": str(tn.get("user") or ""), "assistant": text, "highlights": hls})
    facts = [{"fact": str(f.get("fact") or ""), "label": str(f.get("label") or ""), "status": f.get("status") or "not_matched",
              "turns": [_int(x) for x in f.get("turns") or []]} for f in sc.get("facts") or [] if isinstance(f, dict)]
    flags = [{"kind": str(f.get("kind") or ""), "text": str(f.get("text") or ""), "turn": f.get("turn"), "located": bool(f.get("located"))}
             for f in sc.get("flags") or [] if isinstance(f, dict)]
    counts = {k: sum(h["kind"] == k for tn in turns for h in tn["highlights"]) for k in HL_KINDS}
    return {"source": sc.get("source") or "", "turns": turns, "facts": facts, "flags": flags, "counts": counts}


def _side_drawer(v: dict, side: dict, full: dict) -> dict:
    """One side of a drawer entry from its task_view `v`, the COMPARE side and the side's full REPORT task."""
    n = v.get("n") or {}
    judge = v.get("judge") or {}
    return {"outcome": v.get("outcome"), "band": v.get("band"), "passed": bool(v.get("passed")), "near_miss": bool(v.get("near_miss")),
            "trap_handled": v.get("trap_handled"), "categories": [str(c) for c in v.get("categories") or []],
            "effort": {"class": (v.get("eff") or {}).get("class") or "", "calls": v.get("n_calls", 0), "tokens": v.get("tokens"),
                       "secs": v.get("secs"), "cost": RH.fmt_usd((v.get("eff") or {}).get("cost_usd") or 0), "turns": v.get("turns")},
            "notes": {"rationale": str(n.get("rationale") or ""), "trap_notes": str(n.get("trap_notes") or ""),
                      "offending": str(n.get("offending") or ""), "unsupported_claims": [str(c) for c in n.get("unsupported_claims") or []],
                      "per_turn": [{"turn": p.get("turn"), "outcome": p.get("outcome"), "notes": str(p.get("notes") or "")}
                                   for p in n.get("per_turn") or [] if isinstance(p, dict)]},
            "judge": " ".join(str(x) for x in (judge.get("backend"), judge.get("model")) if x),
            "files": [[k, h] for k, h in v.get("files") or []],
            "scenario": scenario_view(side.get("scenario") if side.get("scenario") is not None else full.get("scenario"))}


def drawer_data(rows: list[dict], reports: dict, labels: list[str], change_label: dict) -> dict:
    """Everything the comparison drawer shows, keyed by comparison task key, plus the tags of every mark key
    ("cmp-<key>", "a-<A key>", "b-<B key>") for the tag filter."""
    tasks, marks = {}, {}
    for s in ("a", "b"):
        for k, t in reports[s].items():
            marks[PREFIX[s] + str(k)] = task_tags(t)
    for r in rows:
        full = {s: reports[s].get((r.get(s) or {}).get("key")) or {} for s in ("a", "b")}
        tags = list(dict.fromkeys(task_tags({**full["b"], **full["a"]}) or [str(x) for x in r.get("strata") or []]))
        trap = r.get("trap") or {}
        trap_s = " · ".join(str(x) for x in (trap.get("type"), trap.get("variant"), trap.get("tier"), trap.get("difficulty")) if x) \
            + (f" · turn {trap['trap_turn']}" if trap.get("trap_turn") is not None else "") if trap else ""
        marks[PREFIX["cmp"] + str(r["key"])] = tags
        tasks[str(r["key"])] = {
            "task_id": r.get("task_id"), "run": r.get("run"), "budget": r.get("budget") or "", "kind": r.get("kind") or "",
            "trap": trap_s, "question_id": r.get("question_id") or "", "domain": r.get("domain") or "", "tags": tags,
            "change": r.get("change"), "change_label": change_label.get(r.get("change")) or r.get("change") or "",
            "shift": r.get("shift") or "", "differs": bool(r.get("differs")),
            "a": _side_drawer(r["A"], r.get("a") or {}, full["a"]), "b": _side_drawer(r["B"], r.get("b") or {}, full["b"])}
    return {"labels": labels, "tasks": tasks, "marks": marks}


def _tone_change(c: str) -> str:
    return {"a_only": "c-side-a", "b_only": "c-side-b", "both_fail": "c-fail"}.get(c, "c-none")


def render_html(cmp: dict, charts: dict[str, str], charts_a: dict[str, str], charts_b: dict[str, str]) -> str:
    """Self-contained compare.html for a COMPARE, its comparison charts and each side's single-report charts
    ({name: svg}; any chart, or any whole dict, may be missing or empty)."""
    charts, charts_a, charts_b = charts or {}, charts_a or {}, charts_b or {}
    labels = [str(x) for x in (cmp.get("labels") or [])][:2]
    labels += ["A", "B"][len(labels):]
    la, lb = labels
    sa, sb = short(labels)
    ra, rb = cmp.get("a") or {}, cmp.get("b") or {}
    tasks = cmp.get("tasks") or []
    runs = [r.get("run") for r in cmp.get("runs") or []] or sorted({t.get("run") for t in tasks if t.get("run")})
    run_index = {r: i for i, r in enumerate(runs)}
    reports = {s: {t.get("key"): t for t in (cmp.get(s) or {}).get("tasks") or []} for s in ("a", "b")}

    cmp_order, single_order = _order("compare_charts", COMPARE_ORDER), _order("charts", RH.CHART_ORDER)
    cards = [{"name": c, "id": f"chart-{c}", "title": CAPTIONS.get(c, (RH.label(c).capitalize(), ""))[0],
              "question": CAPTIONS.get(c, ("", ""))[1], "file": f"charts/{c}.svg",
              "svg": Markup(RH.inline_svg(namespace_svg(charts[c], PREFIX["cmp"])))} for c in _names(charts, cmp_order)]
    side_runs = {s: _side_runs(cmp, s) for s in ("a", "b")}
    def pane(s, src, c):
        if not src.get(c):
            return None
        return {"id": f"{s}-chart-{c}", "file": f"charts-{s}/{c}.svg",
                "svg": Markup(RH.inline_svg(_rerun(namespace_svg(src[c], PREFIX[s]), side_runs[s])))}
    split_names = [c for c in _names({**charts_a, **{k: v for k, v in charts_b.items() if v}}, single_order)]
    caps = {**SPLIT_CAPTIONS, **RH.CAPTIONS}
    split = [{"name": c, "title": caps.get(c, (RH.label(c).capitalize(), ""))[0],
              "question": caps.get(c, ("", ""))[1], "a": pane("a", charts_a, c), "b": pane("b", charts_b, c)}
             for c in split_names]

    rows = sorted((task_row(t, i, run_index, reports) for i, t in enumerate(tasks)),
                  key=lambda v: (v["group"], v["sort"]["run"], v["sort"]["task"]))
    unpaired = cmp.get("unpaired") or {}
    only = [sum(r.get(k, 0) or 0 for r in cmp.get("runs") or []) for k in ("only_a", "only_b")]
    prov = [(x.get("summary") or {}).get("provisional") or sum(bool((t.get("judge") or {}).get("provisional")) for t in x.get("tasks") or [])
            for x in (ra, rb)]
    warnings = [w for w in ((ra.get("summary") or {}).get("judge_warning"), (rb.get("summary") or {}).get("judge_warning")) if w]
    judges = [(x.get("summary") or {}).get("judge") or "?" for x in (ra, rb)]
    models = [(x.get("summary") or {}).get("model") or "" for x in (ra, rb)]
    sources = [str(s) for s in (cmp.get("sources") or [])][:2]
    sources += [""] * (2 - len(sources))
    change_label = {"both_pass": "both pass", "both_fail": "both fail", "a_only": f"only {sa}", "b_only": f"only {sb}"}
    data = drawer_data(rows, reports, labels, {**change_label, "a_only": f"only {la} passes", "b_only": f"only {lb} passes"})
    for r in rows:
        r["tags"] = data["tasks"][str(r["key"])]["tags"]
    tags = [(t, RH.tag_label(t)) for t in sorted({t for r in rows for t in r["tags"]})]   # tags.label: "trap: missing tool"
    data["tag_labels"] = dict(tags)
    every = [*charts.values(), *charts_a.values(), *charts_b.values()]
    env = jinja2.Environment(autoescape=True, trim_blocks=True, lstrip_blocks=True, undefined=jinja2.ChainableUndefined)
    env.filters["label"] = RH.label
    env.filters["yesno"] = lambda v: {True: "yes", False: "no"}.get(v, "?" if v is None else str(v))
    env.filters["tone_change"] = _tone_change
    return env.from_string(TEMPLATE.read_text()).render(
        la=la, lb=lb, sa=sa, sb=sb, sources=sources, models=models, judges=judges, verdict_source=cmp.get("verdict_source") or ra.get("verdict_source") or "judge.json",
        n=len(tasks), runs=runs, run_rows=run_rows(cmp), unpaired_a=unpaired.get("only_a_runs") or [],
        unpaired_b=unpaired.get("only_b_runs") or [], only_a=only[0], only_b=only[1], provisional=prov, warnings=warnings,
        kpis=kpis(tasks, labels), cards=cards, split=split, rows=rows, n_differ=sum(r["differs"] for r in rows),
        kinds=sorted({t.get("kind") for t in tasks if t.get("kind")}), views=RH.VIEWS, metrics=RH.METRICS,
        has_metric=any("data-metric" in c for c in every if c), change_label=change_label, tags=tags,
        data=Markup(embed_json(data)), hl_kinds=HL_KINDS,
        glossary=RH.glossary(ra.get("definitions") or rb.get("definitions") or {}) + [("Comparison terms", TERMS)],
        style=Markup(vars_css() + RH._theme_css()))
