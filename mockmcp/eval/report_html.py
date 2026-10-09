"""`eval report --html`: one self-contained, offline page over a REPORT (report_data.build) and its SVG charts.

The page inlines every chart, adds KPI tiles, a sticky toolbar (view, effort metric, kind and run filters), a sortable
per-task table of `<details>` rows with the judge's notes, and the glossary. It needs no network and works without JS
(default view, rows expand natively); the small script only switches attributes, filters, sorts and jumps to rows."""
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import jinja2
from markupsafe import Markup

from .schema import EFFORT_CLASSES, OUTCOMES, SEVERITY_BANDS

TEMPLATE = Path(__file__).parent / "report_template.html"
CHART_ORDER = ("waffle", "outcomes", "effort", "waste", "breakdown", "categories", "scaling", "flow", "matrix")
WIDE = {"waffle", "effort", "scaling", "flow", "matrix"}   # charts that get a full-width card
VIEWS = (("binary", "Pass vs fail"), ("outcome", "Outcome"), ("severity", "Severity"))
METRICS = (("input_tokens", "Input tokens"), ("seconds", "Seconds"), ("tool_calls", "Tool calls"), ("cost_usd", "Cost"))
CAPTIONS = {   # chart name -> (title, the question it answers)
    "waffle": ("Every task, one square", "What does the run look like overall, and how bad are the failures?"),
    "outcomes": ("Outcome mix per run", "What is the pass rate, and what is the failure mix, at each budget?"),
    "effort": ("Fail fast or burn effort", "Do failures fail fast, or waste tokens, time and calls?"),
    "waste": ("Where the spend went", "How much of the budget bought failures, and what are the unproductive calls?"),
    "breakdown": ("By kind and trap type", "Which kinds of task fail, and how?"),
    "categories": ("Why they failed", "Which failure categories come up most, and with which outcome?"),
    "scaling": ("Scaling with tool budget", "Does loading more tools break the model, and into what?"),
    "flow": ("Where tasks go as the budget grows", "Where do the tasks that pass at a small budget go at a bigger one?"),
    "matrix": ("Tasks that change across budgets", "Which tasks break under load, flip or recover? Select a cell to open its task."),
}
# Copy of the shared palette (svg.PALETTE is the source of truth; this is used only when it cannot be imported).
FALLBACK_PALETTE = {
    "light": {"--mm-bg": "#ffffff", "--mm-surface": "#f6f7f9", "--mm-fg": "#1d2025", "--mm-muted": "#5b6472",
              "--mm-grid": "#e6e8ec", "--mm-axis": "#c9cdd4", "--mm-o-pass": "#13866a", "--mm-b-pass": "#13866a",
              "--mm-pass": "#13866a", "--mm-o-honest_fail": "#4a76a8", "--mm-o-partial": "#a86f00",
              "--mm-o-over_cautious": "#7a52c7", "--mm-o-fabricated": "#d0451b", "--mm-o-unsafe": "#b0103f",
              "--mm-b-unsafe_external": "#7a0a2c", "--mm-b-unsafe_reversible": "#b0103f",
              "--mm-b-unsafe_benign": "#d4537a", "--mm-fail": "#c2410c"},
    "dark": {"--mm-bg": "#0f1217", "--mm-surface": "#171b22", "--mm-fg": "#e8eaee", "--mm-muted": "#9aa3b2",
             "--mm-grid": "#252a33", "--mm-axis": "#3a414d", "--mm-o-pass": "#3cc79b", "--mm-b-pass": "#3cc79b",
             "--mm-pass": "#3cc79b", "--mm-o-honest_fail": "#7ba7dc", "--mm-o-partial": "#e6a93a",
             "--mm-o-over_cautious": "#a98cf2", "--mm-o-fabricated": "#f47d55", "--mm-o-unsafe": "#f2557f",
             "--mm-b-unsafe_external": "#ff8fae", "--mm-b-unsafe_reversible": "#f2557f",
             "--mm-b-unsafe_benign": "#d9406b", "--mm-fail": "#f38a5c"},
}
ACTION_TONE = {"external_or_irreversible": "c-unsafe_external", "reversible": "c-unsafe_reversible", "benign": "c-unsafe_benign"}
FONT = 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'


def _palette() -> dict:
    try:
        from .svg import PALETTE
        return PALETTE if PALETTE.get("light") and PALETTE.get("dark") else FALLBACK_PALETTE
    except Exception:   # charts are built in parallel / optional: never fail the page over them
        return FALLBACK_PALETTE


def _var(k: str) -> str:
    return k if k.startswith("--") else "--" + (k if k.startswith("mm-") else "mm-" + k)


def vars_css() -> str:
    """The shared palette as variables on :root (light default, system dark, forced data-theme), so page and charts agree."""
    p = _palette()
    block = lambda theme: ";".join(f"{_var(k)}:{v}" for k, v in p[theme].items())
    extra = f";--mm-near:var(--mm-o-partial);--mm-font:{FONT}"
    return (f":root{{{block('light')}{extra};color-scheme:light}}"
            f"@media (prefers-color-scheme: dark){{:root:not([data-theme=light]){{{block('dark')};color-scheme:dark}}}}"
            f":root[data-theme=dark]{{{block('dark')};color-scheme:dark}}")


def _theme_css() -> str:
    try:
        from .charts import theme_css
        return theme_css()
    except Exception:
        return ""


def _chart_order() -> tuple:
    try:
        from .charts import CHARTS
        return tuple(CHARTS)
    except Exception:
        return CHART_ORDER


def inline_svg(svg: str) -> str:
    """Chart markup ready for inlining in HTML5: no XML prolog or doctype, no namespace declarations (implied in HTML)."""
    svg = re.sub(r"<\?xml[^>]*\?>|<!DOCTYPE[^>]*>", "", svg).strip()
    return re.sub(r'\s+xmlns(?::\w+)?="[^"]*"', "", svg)


def fmt_tokens(n) -> str:
    n = n or 0
    return f"{n / 1e6:.1f}M" if n >= 1e6 else f"{n / 1e3:.1f}k" if n >= 1e3 else f"{n:.0f}"


def fmt_secs(s) -> str:
    s = s or 0
    return f"{s / 60:.1f} min" if s >= 600 else f"{s:.0f} s" if s >= 10 else f"{s:.1f} s"


def fmt_usd(x) -> str:
    return "n/a" if x is None else f"${x:,.2f}" if x >= 1 else f"${x:.4f}" if x < 0.1 else f"${x:.3f}"


def pct(n, d) -> str:
    return f"{100 * n / d:.0f}%" if d else "n/a"


def label(s) -> str:
    return str(s or "").replace("_", " ")


def tone(name: str) -> str:
    """CSS class naming the colour of an outcome or band (all map to palette variables)."""
    return f"c-{name}" if name in OUTCOMES or name in SEVERITY_BANDS else "c-none"


def charts_dir(verdict_source: str) -> str:
    """Folder the standalone SVGs sit in next to the page (report.write_outputs): charts/ or charts.NAME/."""
    m = re.fullmatch(r"judge\.(.+)\.json", verdict_source or "")
    return f"charts.{m.group(1)}" if m else "charts"


def kpis(tasks: list[dict]) -> list[dict]:
    """KPI tiles over every task in the report: value, a one-line context, and a palette tone."""
    n = len(tasks)
    passed = [t for t in tasks if t.get("passed")]
    failed = [t for t in tasks if not t.get("passed")]
    traps = [t for t in tasks if t.get("kind") == "trap"]
    known = [t for t in traps if t.get("trap_handled") is not None]
    unsafe = [t for t in tasks if t.get("outcome") == "unsafe"]
    fab = sum(t.get("outcome") == "fabricated" for t in tasks)
    near = sum(bool(t.get("near_miss")) for t in tasks)
    eff = lambda t, k: (t.get("effort") or {}).get(k) or 0
    cost, tok = sum(eff(t, "cost_usd") for t in tasks), sum(eff(t, "input_tokens") for t in tasks)
    tok_failed = sum(eff(t, "input_tokens") for t in failed)
    sev = Counter(str(t.get("band") or "unsafe").removeprefix("unsafe_") for t in unsafe)
    return [
        {"label": "Pass rate", "value": pct(len(passed), n), "sub": f"{len(passed)} of {n} tasks", "tone": "c-pass"},
        {"label": "Trap handled", "value": pct(sum(t["trap_handled"] is True for t in known), len(known)) if known else "–",
         "sub": f"{sum(t['trap_handled'] is True for t in known)} of {len(known)} traps" if known else "no traps in this run",
         "tone": "c-honest_fail"},
        {"label": "Unsafe", "value": str(len(unsafe)), "sub": (pct(len(unsafe), n) + " of tasks"
         + ("; " + ", ".join(f"{k} {v}" for k, v in sev.items()) if sev else "")), "tone": "c-unsafe"},
        {"label": "Fabricated", "value": str(fab), "sub": pct(fab, n) + " of tasks", "tone": "c-fabricated"},
        {"label": "Near misses", "value": str(near), "sub": f"{pct(near, len(failed))} of {len(failed)} failures", "tone": "c-partial"},
        {"label": "Cost per pass", "value": fmt_usd(cost / len(passed)) if passed else "n/a", "sub": f"{fmt_usd(cost)} in all",
         "tone": "c-none"},
        {"label": "Tokens on failures", "value": pct(tok_failed, tok), "sub": f"{fmt_tokens(tok_failed)} of {fmt_tokens(tok)} input",
         "tone": "c-fail"},
    ]


def _file_href(path: str) -> str:
    return "./" + quote(path)   # "./" so an id with ':' is never read as a URL scheme


def _args(a) -> str:
    s = a if isinstance(a, str) else json.dumps(a, sort_keys=True, default=str)
    return s if len(s) <= 240 else s[:240] + "…"


def task_view(t: dict, i: int, run_index: dict) -> dict:
    """One table row: display strings, sort keys and the expanded notes of a REPORT task."""
    eff, calls, notes = t.get("effort") or {}, t.get("calls") or {}, t.get("notes") or {}
    band = t.get("band") or t.get("outcome") or "?"
    turns_total, turns_passed = eff.get("turns_total") or 0, eff.get("turns_passed") or 0
    n_calls = calls.get("total", eff.get("tool_calls")) or 0
    stats = [(k, calls.get(k)) for k in ("errors", "exact_repeats", "same_tool_repeats", "distractor", "decoy", "writes",
                                         "failed_writes") if k in calls]
    sort = {"task": t.get("task_id", ""), "run": run_index.get(t.get("run"), 0), "kind": t.get("kind", ""),
            "outcome": t.get("band_rank", 99), "effort": EFFORT_CLASSES.index(eff["class"]) if eff.get("class") in EFFORT_CLASSES else -1,
            "turns": turns_passed / turns_total if turns_total else -1, "calls": n_calls,
            "tokens": eff.get("input_tokens") or 0, "secs": eff.get("seconds") or 0}
    return {**t, "i": i, "band": band, "eff": eff, "c": calls, "n": notes, "sort": sort, "n_calls": n_calls,
            "stats": stats, "tone": tone(t.get("outcome")), "band_tone": tone(band),
            "turns": f"{turns_passed}/{turns_total}" if turns_total else "–",
            "tokens": fmt_tokens(eff.get("input_tokens")), "secs": fmt_secs(eff.get("seconds")),
            "actions": [{**a, "args_text": _args(a.get("args")) if a.get("args") else "", "tone": ACTION_TONE.get(a.get("severity"), "c-none")}
                        for a in notes.get("actions") or []],
            "files": [(k, _file_href(v)) for k, v in (t.get("files") or {}).items() if v],
            "servers": ", ".join(f"{k} {v}" for k, v in (calls.get("servers") or {}).items())}


def run_rows(report: dict) -> list[dict]:
    """Per-run summary lines for the runs table."""
    out = []
    for r in report.get("runs") or []:
        m, w = r.get("metrics") or {}, r.get("waste") or {}
        out.append({"run": r.get("run"), "budget": r.get("budget"), "tasks": r.get("tasks", 0),
                    "pass_rate": pct(r.get("passed", 0), r.get("tasks", 0)), "near_miss": r.get("near_miss", 0),
                    "cost_per_pass": fmt_usd(m.get("cost_per_pass_usd")),
                    "share_failed": pct((w.get("share_failed") or {}).get("input_tokens", 0), 1),
                    "median_tokens": fmt_tokens(((m.get("input_tokens") or {}).get("median"))),
                    "median_secs": fmt_secs((m.get("seconds") or {}).get("median"))})
    return out


def glossary(defs: dict) -> list[tuple[str, list[tuple[str, str]]]]:
    """Glossary groups from REPORT.definitions, in reading order."""
    groups = [("Outcomes", "outcomes"), ("Severity bands", "bands"), ("Effort classes", "effort"),
              ("Failure categories", "categories"), ("Severity of an action", "severity"), ("Terms", "terms")]
    out = [(title, [(label(k), str(v)) for k, v in (defs.get(key) or {}).items()]) for title, key in groups if defs.get(key)]
    if defs.get("near_miss"):
        out.insert(3, ("Near miss", [("near miss", str(defs["near_miss"]))]))
    return out


def render_html(report: dict, charts: dict[str, str]) -> str:
    """Self-contained report.html for a REPORT and its {name: svg} charts (any chart may be missing)."""
    summary = report.get("summary") or {}
    tasks = report.get("tasks") or []
    runs = [r.get("run") for r in report.get("runs") or []] or sorted({t.get("run") for t in tasks})
    run_index = {r: i for i, r in enumerate(runs)}
    order = _chart_order()
    names = [c for c in order if charts.get(c)] + sorted(c for c in charts if c not in order and charts[c])
    cards = [{"name": c, "title": CAPTIONS.get(c, (label(c).capitalize(), ""))[0], "question": CAPTIONS.get(c, ("", ""))[1],
              "wide": c in WIDE, "svg": Markup(inline_svg(charts[c])), "has_marks": 'data-key="' in charts[c]} for c in names]
    rows = sorted((task_view(t, i, run_index) for i, t in enumerate(tasks)),
                  key=lambda v: (bool(v.get("passed")), v["sort"]["outcome"], v["sort"]["run"], v["sort"]["task"]))
    prov = summary.get("provisional") or sum(bool((t.get("judge") or {}).get("provisional")) for t in tasks)
    warning = summary.get("judge_warning") or next(((t.get("judge") or {}).get("warning") for t in tasks
                                                    if (t.get("judge") or {}).get("warning")), None)
    env = jinja2.Environment(autoescape=True, trim_blocks=True, lstrip_blocks=True, undefined=jinja2.ChainableUndefined)
    env.filters["label"] = label
    env.filters["yesno"] = lambda v: {True: "yes", False: "no"}.get(v, "?" if v is None else str(v))
    return env.from_string(TEMPLATE.read_text()).render(
        title=report.get("title") or "eval", verdict_source=report.get("verdict_source") or "judge.json",
        model=summary.get("model") or ", ".join(sorted({str((t.get("judge") or {}).get("model", "")) for t in tasks})) or "?",
        judge=summary.get("judge") or "?", n=len(tasks), runs=runs, run_rows=run_rows(report), provisional=prov,
        warning=warning, kpis=kpis(tasks), cards=cards, rows=rows, failures=sum(not t.get("passed") for t in tasks),
        kinds=sorted({t.get("kind") for t in tasks if t.get("kind")}), views=VIEWS, metrics=METRICS,
        has_metric=any("data-metric" in c for c in charts.values() if c), has_marks=any(c["has_marks"] for c in cards),
        charts_dir=charts_dir(report.get("verdict_source")), glossary=glossary(report.get("definitions") or {}),
        style=Markup(vars_css() + _theme_css()))
