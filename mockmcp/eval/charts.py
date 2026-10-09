"""The report's charts as standalone SVG, drawn from a REPORT dict (report_data.build / report.json).

Each builder returns one self-contained SVG (own stylesheet, both themes, no scripts, no external references) or None
when it does not apply. Per-task marks carry `mm-t o-<outcome> b-<band> pf-<pass|fail>` plus data-key/kind/run, so a
host page can recolour them with `data-view` and dim them with `mm-dim`; aggregate charts carry one `mm-v-<view>` group
per view. The colour of a mark always follows its outcome or band, never its rank."""
import math
import statistics
from collections import Counter, defaultdict

from . import svg
from .schema import OUTCOMES, SEVERITY_BANDS, modern
from .svg import METRICS, VIEWS, bar, el, esc, fmt, text, title, tw

CHARTS: tuple[str, ...] = ("waffle", "outcomes", "effort", "waste", "breakdown", "categories", "scaling", "flow", "matrix")
__all__ = ["CHARTS", "VIEWS", "METRICS", "theme_css", "render_all"] + [f"chart_{c}" for c in CHARTS]

W, PAD = 760, 24
LABEL = {"pass": "pass", "fail": "fail", "honest_fail": "honest fail", "partial": "partial", "over_cautious": "over-cautious",
         "fabricated": "fabricated", "unsafe": "unsafe", "unsafe_external": "unsafe: external", "unsafe_reversible":
         "unsafe: reversible", "unsafe_benign": "unsafe: benign"}
# Stacking order, left to right (or top to bottom): pass first, the worst last, so failures grow from the far edge.
ORDER = {"binary": ["pass", "fail"], "outcome": [f"o-{o}" for o in reversed(OUTCOMES)],
         "severity": [f"b-{b}" for b in reversed(SEVERITY_BANDS)]}
METRIC = {"input_tokens": ("input tokens", "tokens", True), "seconds": ("time to result", "s", True),
          "tool_calls": ("tool calls", "n", False), "cost_usd": ("cost", "usd", True)}


def theme_css() -> str:
    """The `.mm-chart` theme variables for both themes; a page that inlines several charts includes it once."""
    return svg.theme_css()


# ---- task helpers -------------------------------------------------------------------------------------------------

def outcome(t: dict) -> str:
    return modern(t.get("outcome") or "")


def band(t: dict) -> str:
    """The task's severity band (the report's, or derived as report_data.band_of does)."""
    if t.get("band") in SEVERITY_BANDS:
        return t["band"]
    o = outcome(t)
    if o == "unsafe":
        return {"external_or_irreversible": "unsafe_external", "reversible": "unsafe_reversible"}.get(t.get("severity"), "unsafe_benign")
    return o if o in SEVERITY_BANDS else "partial"


def key_of(t: dict, view: str) -> str:
    """The colour class of a task in a view: pass/fail, o-<outcome> or b-<band>."""
    return ("pass" if t.get("passed") else "fail") if view == "binary" else f"o-{outcome(t)}" if view == "outcome" else f"b-{band(t)}"


def name_of(k: str) -> str:
    return LABEL.get(k.split("-", 1)[-1], k.split("-", 1)[-1].replace("_", " "))


def mark(t: dict, **attrs) -> dict:
    """Attributes of a per-task mark (contract classes + data attributes)."""
    cls = f"mm-t o-{outcome(t)} b-{band(t)} pf-{'pass' if t.get('passed') else 'fail'}" + (" near" if t.get("near_miss") else "")
    return dict(class_=(attrs.pop("class_", "") + " " + cls).strip(), data_key=t.get("key"), data_kind=t.get("kind"),
                data_run=t.get("run"), **attrs)


def eff(t: dict, m: str) -> float:
    return float((t.get("effort") or {}).get(m) or 0)


def runs_of(r: dict) -> list[str]:
    names = [x["run"] for x in r.get("runs") or []]
    return names + sorted({t["run"] for t in r.get("tasks") or []} - set(names))


def by_run(r: dict) -> dict[str, list[dict]]:
    out = {run: [] for run in runs_of(r)}
    for t in r.get("tasks") or []:
        out[t["run"]].append(t)
    return out


def run_info(r: dict) -> dict[str, dict]:
    return {x["run"]: x for x in r.get("runs") or []}


def pctl(xs: list[float], q: float) -> float:
    """Nearest-rank percentile (as report.metrics computes p95)."""
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(len(xs) * q))] if xs else 0.0


def counts(ts: list[dict], view: str) -> Counter:
    return Counter(key_of(t, view) for t in ts)


def present(ts: list[dict], view: str) -> list[str]:
    c = counts(ts, view)
    return [k for k in ORDER[view] if c[k]]


def pct(n, d) -> str:
    return f"{100 * n / d:.0f}%" if d else "–"


# ---- layout pieces ------------------------------------------------------------------------------------------------

def head(h: str, sub: str) -> tuple[list[str], float]:
    """Visible heading (a `mm-head` group a host page may hide) and the y below it."""
    lines = wrap(sub, W - 2 * PAD, 12)
    g = [text(PAD, 30, h, class_="mm-h1")] + [text(PAD, 50 + 16 * i, s, class_="mm-sub") for i, s in enumerate(lines)]
    return [el("g", g, class_="mm-head")], 50 + 16 * (len(lines) - 1) + 22


def wrap(s: str, width: float, size: float) -> list[str]:
    out, cur = [], ""
    for w in s.split():
        if cur and tw(cur + " " + w, size) > width:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return out + [cur] if cur else out


def legend(items: list[tuple[str, str]], x: float, y: float, width: float, extra: list[str] = ()) -> tuple[list[str], float]:
    """Swatch + label items, wrapping; returns markup and the height used."""
    out, cx, cy = [], x, y
    for k, lab in items:
        w = 16 + tw(lab, 12) + 16
        if cx + w > x + width and cx > x:
            cx, cy = x, cy + 20
        out += [bar(cx, cy - 9, 10, 10, 2.5, class_=f"f-{k}"), text(cx + 15, cy, lab, class_="mm-small")]
        cx += w
    for e in extra:
        out.append(e.replace("{x}", svg.num(cx)).replace("{y}", svg.num(cy)))
    return out, cy - y + 20


def view_legends(ts: list[dict], x: float, y: float, width: float, count: bool = False) -> tuple[list[str], float]:
    """One legend per view (only the classes present), each in its own `mm-v` group."""
    groups, h = [], 0
    for v in VIEWS:
        c = counts(ts, v)
        items = [(k, f"{name_of(k)} {c[k]}" if count else name_of(k)) for k in present(ts, v)]
        g, hh = legend(items, x, y, width)
        groups.append(el("g", g, class_=f"mm-v mm-v-{v}"))
        h = max(h, hh)
    return groups, h


def seg_label(k: str, n: float, tot: float, w: float, cx: float, cy: float, min_share: float = .06, count: bool = True) -> str:
    """A count/share label (share only for weights) centred in a stacked segment, only when the segment is big enough
    and the text fits."""
    if not tot or n / tot < min_share:
        return ""
    for s in ((f"{n} · {pct(n, tot)}",) if count else ()) + (pct(n, tot),):
        if tw(s, 11, True) + 10 <= w:
            return text(cx, cy, s, class_=f"mm-in i-{k}", text_anchor="middle", dy="0.35em")
    return ""


def hbar(ts_counts: Counter, order: list[str], x: float, y: float, w: float, h: float, tip: str, labels: bool = True,
         weights: dict | None = None) -> list[str]:
    """A 100% stacked horizontal bar: one rounded segment per class in `order`, a 2 px surface gap between them."""
    vals = [weights[k] if weights is not None else ts_counts[k] for k in order]
    tot = sum(vals)
    out, cx = [], x
    for k, v, sw in zip(order, vals, svg.stack(vals, w)):
        if sw <= 0:
            continue
        lab = tip.format(name=name_of(k), n=ts_counts[k], share=pct(v, tot), v=v)
        out.append(el("rect", title(lab), x=cx, y=y, width=sw, height=h, rx=min(4, sw / 2), class_=f"mm-seg f-{k}"))
        if labels:
            out.append(seg_label(k, ts_counts[k] if weights is None else v, tot, sw, cx + sw / 2, y + h / 2, count=weights is None))
        cx += sw
    return out


def grow(r: dict) -> int:
    return len(runs_of(r))


# ---- 1 waffle ----------------------------------------------------------------------------------------------------

def chart_waffle(r: dict) -> str | None:
    """Every task as one square, a block per run, pass first and the worst failures last (column by column, so a
    block reads like a stacked bar); near misses carry a hollow centre."""
    ts = r.get("tasks") or []
    if not ts:
        return None
    s, gap = 11, 3
    pitch, avail = s + gap, W - 2 * PAD
    cols_max = int((avail + gap) // pitch)
    order = {k.split("-", 1)[1]: i for i, k in enumerate(ORDER["severity"])}
    body, y = head("Every task, one square", "What does the run look like overall, and how bad are the failures? "
                   "Squares run from passes on the left to the worst failures on the right.")
    leg, lh = view_legends(ts, PAD, y + 4, avail - 120)
    nx = W - PAD - 92
    body += leg + [bar(nx, y + 4 - 9, 10, 10, 2.5, class_="mm-key"), el("circle", cx=nx + 5, cy=y, r=2, class_="mm-hole"),
                   text(nx + 15, y + 4, "near miss", class_="mm-small")]
    y += lh + 10
    info = run_info(r)
    for run, rts in by_run(r).items():
        if not rts:
            continue
        rts = sorted(rts, key=lambda t: (order.get(band(t), 99), str(t.get("task_id"))))
        n, passed = len(rts), sum(bool(t.get("passed")) for t in rts)
        rows = max(math.ceil(n / cols_max), min(5, math.ceil(n / 12)))
        nm = sum(bool(t.get("near_miss")) for t in rts)
        bud = (info.get(run) or {}).get("budget") or rts[0].get("budget") or ""
        y += 16
        body += [text(PAD, y, run, class_="mm-lbl"), text(PAD + tw(run, 12, True) + 8, y, bud, class_="mm-small"),
                 el("text", [el("tspan", esc(f"{pct(passed, n)} passed"), class_="mm-num"),
                             el("tspan", esc(f"  {passed} of {n}" + (f" · {nm} near misses" if nm else "")), class_="mm-small")],
                    x=W - PAD, y=y, text_anchor="end")]
        y += 10
        for i, t in enumerate(rts):
            cx, cy = PAD + (i // rows) * pitch, y + (i % rows) * pitch
            body.append(el("rect", title(f"{t.get('task_id')} · {run} · {outcome(t)} · {name_of('b-' + band(t))} · "
                                         f"{fmt(eff(t, 'tool_calls'))} calls · {fmt(eff(t, 'input_tokens'), 'tokens')} tokens"),
                           **mark(t, x=cx, y=cy, width=s, height=s, rx=2.5)))
            if t.get("near_miss"):
                body.append(el("circle", cx=cx + s / 2, cy=cy + s / 2, r=2, class_="mm-hole"))
        y += rows * pitch + 14
    n = len(ts)
    return svg.doc("waffle", W, y + 6, "Every task, one square",
                   f"What does the run look like overall? {n} tasks in {grow(r)} run(s); "
                   f"{sum(bool(t.get('passed')) for t in ts)} passed, {sum(bool(t.get('near_miss')) for t in ts)} near misses.", body)


# ---- 2 outcomes --------------------------------------------------------------------------------------------------

def stacked_rows(rows: list[tuple[str, str, list[dict]]], y: float, right, extra=None) -> tuple[list[str], float]:
    """100% stacked bars, one per (label, sublabel, tasks) row, in all three view groups; `right(tasks)` gives the text
    at the right end, `extra(tasks, x, y, w, h)` optional marks over the bar."""
    lw = min(190, max([tw(a, 12, True) for a, _, _ in rows] + [tw(b, 11) for _, b, _ in rows]) + 16)
    rw = 112
    x, w, h, step = PAD + lw, W - 2 * PAD - lw - rw, 22, 44
    groups = {v: [] for v in VIEWS}
    fixed = []
    for i, (a, b, ts) in enumerate(rows):
        yy = y + i * step
        if a == "all runs":
            fixed.append(el("line", x1=PAD, x2=W - PAD, y1=yy - 11, y2=yy - 11, class_="mm-grid"))
        fixed += [text(PAD, yy + h / 2 - (3 if b else -4), a, class_="mm-lbl")]
        if b:
            fixed.append(text(PAD, yy + h / 2 + 12, b, class_="mm-small"))
        r1, r2 = right(ts)
        fixed += [text(W - PAD, yy + h / 2 - 3, r1, class_="mm-num", text_anchor="end"),
                  text(W - PAD, yy + h / 2 + 12, r2, class_="mm-small", text_anchor="end")]
        for v in VIEWS:
            c = counts(ts, v)
            groups[v] += hbar(c, ORDER[v], x, yy, w, h, "{name}: {n} tasks ({share})")
        if extra:
            fixed += extra(ts, x, yy, w, h)
    return [el("g", groups[v], class_=f"mm-v mm-v-{v}") for v in VIEWS] + fixed, len(rows) * step


def pass_right(ts: list[dict]) -> tuple[str, str]:
    nm = sum(bool(t.get("near_miss")) for t in ts)
    return f"{pct(sum(bool(t.get('passed')) for t in ts), len(ts))} passed", f"n {len(ts)}" + (f" · {nm} near" if nm else "")


def chart_outcomes(r: dict) -> str | None:
    """Outcome mix per run as 100% stacked bars (pass on the left, the worst on the right), plus an 'all runs' bar."""
    ts = r.get("tasks") or []
    if not ts:
        return None
    info, groups = run_info(r), by_run(r)
    rows = [(run, (info.get(run) or {}).get("budget") or "", rts) for run, rts in groups.items() if rts]
    if len(rows) > 1:
        rows.append(("all runs", "", ts))
    body, y = head("Outcome mix", "Pass rate and failure mix per run. Failures grow from the right edge, worst last.")
    leg, lh = view_legends(ts, PAD, y + 4, W - 2 * PAD)
    sr, sh = stacked_rows(rows, y + lh + 18, pass_right)
    return svg.doc("outcomes", W, y + lh + 18 + sh, "Outcome mix per run",
                   "What is the pass rate and the failure mix per run? " + "; ".join(
                       f"{a}: {pct(sum(bool(t.get('passed')) for t in x), len(x))} of {len(x)} passed" for a, _, x in rows),
                   body + leg + sr)


# ---- 3 effort ----------------------------------------------------------------------------------------------------

def thresholds(rts: list[dict], m: str, thr: dict | None) -> tuple[float, float, str]:
    """p50 and p90 of a metric over the run's passes (all tasks when fewer than 5 passed); the run's own
    effort_thresholds win for input tokens and tool calls."""
    src = {"input_tokens": "input_total", "tool_calls": "tool_calls"}.get(m)
    if thr and src and thr.get(src):
        return float(thr[src][0]), float(thr[src][1]), thr.get("basis", "passes")
    ps = [t for t in rts if t.get("passed")]
    basis = "passes" if len(ps) >= 5 else "all"
    xs = [eff(t, m) for t in (ps if basis == "passes" else rts)]
    return pctl(xs, .5), pctl(xs, .9), basis


def scale_for(ts: list[dict], m: str, x0: float, x1: float):
    """Scale and ticks for a metric over all tasks (log for tokens, time and cost; linear for calls)."""
    xs = [eff(t, m) for t in ts]
    if METRIC[m][2]:
        pos = [v for v in xs if v > 0] or [1]
        lo, hi = svg.log_bounds(min(pos), max(pos))
        ticks = svg.log_ticks(lo, hi)
        if len(ticks) < 3:  # a narrow range: widen down a decade so the axis has a scale
            lo /= 10
            ticks = svg.log_ticks(lo, hi)
        return svg.log(lo, hi, x0, x1), ticks
    ticks = svg.nice_ticks(0, max(xs + [1]), 6)
    return svg.linear(0, ticks[-1], x0, x1), ticks


SWARM_LIMIT = 40  # px either side of a row's centre; denser rows overlap instead of growing


def chart_effort(r: dict) -> str | None:
    """Beeswarm of per-task effort by band, one panel per run on a shared x scale; the dashed rule is the median pass,
    the shaded zone the costly region (>= p90 of passes). Four metric groups switched by data-metric."""
    ts = r.get("tasks") or []
    if not ts:
        return None
    rad = 3.2
    bands = [b for b in SEVERITY_BANDS if any(band(t) == b for t in ts)]
    lw = max(tw(LABEL[b], 12) for b in bands) + 44
    x0, x1 = PAD + lw, W - PAD - 8
    body, y = head("Fail fast, or burn effort?", "Do failures fail fast, or waste tokens, time and calls? "
                   "Each dot is a task. Dashed line: the median pass. Shaded: costly, at or above the 90th percentile of passes.")
    leg, lh = view_legends(ts, PAD, y + 4, W - 2 * PAD)
    body += leg
    y += lh + 8
    scales = {m: scale_for(ts, m, x0, x1) for m in METRICS}
    info, groups = run_info(r), by_run(r)
    # layout: offsets per metric, row heights as the max over metrics so every metric shares one geometry
    lay, rows = {}, []
    for run, rts in groups.items():
        if not rts:
            continue
        for b in bands:
            bts = sorted((t for t in rts if band(t) == b), key=lambda t: str(t.get("key")))
            offs = {m: svg.beeswarm([scales[m][0](eff(t, m)) for t in bts], rad, limit=SWARM_LIMIT) for m in METRICS}
            ext = max([abs(o) for m in METRICS for o in offs[m]] + [0])
            rows.append((run, b, bts, offs, max(22, 2 * ext + 2 * rad + 8)))
    top = y + 22
    per_m = {m: [] for m in METRICS}
    fixed = []
    cy = top
    panel_y = {}
    for run, rts in groups.items():
        if not rts:
            continue
        rr = [x for x in rows if x[0] == run]
        ph = sum(x[4] for x in rr)
        panel_y[run] = (cy, cy + 22 + ph)
        bud = (info.get(run) or {}).get("budget") or ""
        fixed += [text(PAD, cy + 14, run, class_="mm-lbl"), text(PAD + tw(run, 12, True) + 8, cy + 14, bud, class_="mm-small")]
        thr = (info.get(run) or {}).get("effort_thresholds")
        for m in METRICS:
            sc = scales[m][0]
            p50, p90, basis = thresholds(rts, m, thr)
            zx, rx = sc(p90), sc(p50)
            per_m[m] += [el("rect", title(f"costly: at or above {fmt(p90, METRIC[m][1])} (p90 of {basis})"),
                            x=zx, y=cy + 20, width=max(0, x1 + 6 - zx), height=ph + 2, class_="mm-zone", rx=3),
                         text(zx + 5, cy + 14, "costly", class_="mm-small"),
                         el("line", title(f"median of {basis}: {fmt(p50, METRIC[m][1])}"), x1=rx, x2=rx, y1=cy + 20,
                            y2=cy + 22 + ph, class_="mm-rule"),
                         text(rx - 5, cy + 14, f"p50 {fmt(p50, METRIC[m][1])}", class_="mm-small", text_anchor="end")]
        ry = cy + 22
        for _, b, bts, offs, rh in rr:
            mid = ry + rh / 2
            fixed += [el("line", x1=x0, x2=x1, y1=mid, y2=mid, class_="mm-grid"),
                      text(PAD + 10, mid + 4, LABEL[b], class_="mm-small"),
                      text(x0 - 10, mid + 4, str(len(bts)) if bts else "–", class_="mm-small", text_anchor="end")]
            for m in METRICS:
                sc, unit = scales[m][0], METRIC[m][1]
                for t, o in zip(bts, offs[m]):
                    per_m[m].append(el("circle", title(f"{t.get('task_id')} · {run} · {outcome(t)} · {fmt(eff(t, m), unit)}"),
                                       **mark(t, cx=sc(eff(t, m)), cy=mid + o, r=rad, class_="mm-dot")))
                if bts:
                    med = statistics.median(eff(t, m) for t in bts)
                    per_m[m].append(el("line", title(f"{LABEL[b]} median: {fmt(med, unit)}"), x1=sc(med), x2=sc(med),
                                       y1=mid - 8, y2=mid + 8, class_="mm-tickmark"))
            ry += rh
        cy = ry + 14
    bottom = cy - 8
    for m in METRICS:
        sc, ticks = scales[m]
        grid = [el("line", x1=sc(v), x2=sc(v), y1=top + 20, y2=bottom, class_="mm-grid") for v in ticks]
        labs = [text(sc(v), bottom + 16, fmt(v, METRIC[m][1]), class_="mm-tick", text_anchor="middle") for v in ticks]
        per_m[m] = grid + per_m[m] + [el("line", x1=x0, x2=x1, y1=bottom, y2=bottom, class_="mm-axis")] + labs + [
            text(x1, bottom + 34, METRIC[m][0] + (" (log scale)" if METRIC[m][2] else "") + " →", class_="mm-small",
                 text_anchor="end"),
            text(x0, bottom + 34, "median of each row: short bar", class_="mm-small")]
    body += fixed + [el("g", per_m[m], class_=f"mm-m mm-m-{m}") for m in METRICS]
    fails = [t for t in ts if not t.get("passed")]
    ps = [t for t in ts if t.get("passed")]
    md = lambda xs: statistics.median(xs) if xs else 0
    return svg.doc("effort", W, bottom + 46, "Fail fast or burn effort",
                   f"Do failures fail fast, or waste tokens, time and calls? Median input tokens: passes "
                   f"{fmt(md([eff(t, 'input_tokens') for t in ps]), 'tokens')}, failures {fmt(md([eff(t, 'input_tokens') for t in fails]), 'tokens')}.",
                   body, data_metric="input_tokens")


# ---- 4 waste -----------------------------------------------------------------------------------------------------

WASTE_SIGNALS = (("errors", "erroring calls"), ("exact_repeats", "exact repeats"), ("distractor", "distractor-server calls"),
                 ("decoy", "decoy calls"))


def chart_waste(r: dict) -> str | None:
    """Where the spend went: the share of cost, tokens, time and calls that bought failures, then the mean
    unproductive calls per task by class."""
    ts = r.get("tasks") or []
    if not ts:
        return None
    body, y = head("Where the spend went", "How much of the effort bought failures, and which unproductive calls "
                   "come with them? Top: share of each total by class. Bottom: mean calls per task.")
    leg, lh = view_legends(ts, PAD, y + 4, W - 2 * PAD)
    body += leg
    y += lh + 18
    rows = []
    for m in ("cost_usd", "input_tokens", "seconds", "tool_calls"):
        tot = sum(eff(t, m) for t in ts)
        failed = sum(eff(t, m) for t in ts if not t.get("passed"))
        rows.append((m, tot, failed))
    lw, rw = 130, 112
    x, w, h, step = PAD + lw, W - 2 * PAD - lw - rw, 22, 44
    groups = {v: [] for v in VIEWS}
    lines = []
    for i, (m, tot, failed) in enumerate(rows):
        yy = y + i * step
        name, unit = METRIC[m][0], METRIC[m][1]
        lines += [text(PAD, yy + h / 2 - 3, name, class_="mm-lbl"), text(PAD, yy + h / 2 + 12, f"{fmt(tot, unit)} total", class_="mm-small"),
                  text(W - PAD, yy + h / 2 - 3, pct(failed, tot) if tot else "–", class_="mm-num", text_anchor="end"),
                  text(W - PAD, yy + h / 2 + 12, "went on failures", class_="mm-small", text_anchor="end")]
        for v in VIEWS:
            wts = defaultdict(float)
            for t in ts:
                wts[key_of(t, v)] += eff(t, m)
            c = counts(ts, v)
            if tot:
                groups[v] += hbar(c, ORDER[v], x, yy, w, h, "{name}: " + "{share} of " + name, weights=wts)
            else:
                groups[v].append(el("rect", x=x, y=yy, width=w, height=h, rx=4, class_="mm-track"))
    y += len(rows) * step + 18
    # panel 2: small multiples of mean signal per task, one column per signal
    lines.append(text(PAD, y, "Unproductive calls, mean per task", class_="mm-lbl"))
    y += 22
    lw2 = 112
    cw = (W - 2 * PAD - lw2) / len(WASTE_SIGNALS)
    for j, (_, lab) in enumerate(WASTE_SIGNALS):
        lines.append(text(PAD + lw2 + j * cw, y, lab, class_="mm-small"))
    y += 12
    hmax = 0
    for v in VIEWS:
        keys = present(ts, v)
        cls = {k: [t for t in ts if key_of(t, v) == k] for k in keys}
        means = {sig: {k: statistics.fmean(float((t.get("calls") or {}).get(sig) or 0) for t in cls[k]) for k in keys}
                 for sig, _ in WASTE_SIGNALS}
        g = []
        for i, k in enumerate(keys):
            yy = y + i * 22
            g.append(text(PAD, yy + 13, name_of(k), class_="mm-small"))
            for j, (sig, lab) in enumerate(WASTE_SIGNALS):
                top, mean = max(means[sig].values()) or 1, means[sig][k]
                bx, bw = PAD + lw2 + j * cw, (cw - 46) * mean / top
                if bw > 0:
                    g.append(el("rect", title(f"{name_of(k)}: {mean:.2f} {lab} per task ({len(cls[k])} tasks)"),
                                x=bx, y=yy + 2, width=max(bw, 2), height=13, rx=min(3, bw / 2), class_=f"f-{k}"))
                g.append(text(bx + max(bw, 0) + 5, yy + 13, f"{mean:.1f}" if mean < 10 else f"{mean:.0f}", class_="mm-small"))
        groups[v] += g
        hmax = max(hmax, len(keys) * 22)
    y += hmax + 8
    body += [el("g", groups[v], class_=f"mm-v mm-v-{v}") for v in VIEWS] + lines
    share = rows[1][2] / rows[1][1] if rows[1][1] else 0
    return svg.doc("waste", W, y, "Where the spend went",
                   f"How much of the budget bought failures? {share * 100:.0f}% of input tokens went on failed tasks.", body)


# ---- 5 breakdown ---------------------------------------------------------------------------------------------------

def handled_rate(ts: list[dict]) -> float | None:
    hs = [t.get("trap_handled") for t in ts if t.get("trap_handled") is not None]
    return sum(bool(h) for h in hs) / len(hs) if hs else None


def chart_breakdown(r: dict) -> str | None:
    """100% stacked bars per task kind, then per trap type; trap rows carry a tick at the trap-handled rate."""
    ts = r.get("tasks") or []
    if not ts:
        return None
    kinds = Counter(t.get("kind") or "?" for t in ts)
    rows = [(k, "", [t for t in ts if (t.get("kind") or "?") == k]) for k, _ in sorted(kinds.items(), key=lambda kv: (-kv[1], kv[0]))]
    traps = [t for t in ts if t.get("kind") == "trap"]
    types = Counter(((t.get("trap") or {}).get("type") or "?") for t in traps)
    trows = [(f"trap: {k}", "", [t for t in traps if ((t.get("trap") or {}).get("type") or "?") == k])
             for k, _ in sorted(types.items(), key=lambda kv: (-kv[1], kv[0]))] if len(types) > 1 or traps else []

    def tick(rts, x, y, w, h):
        hr = handled_rate(rts) if rts and rts[0].get("kind") == "trap" else None
        if hr is None:
            return []
        tx = x + hr * w
        tip = title(f"trap handled: {pct(hr, 1)}")
        return [el("line", tip, x1=tx, x2=tx, y1=y - 7, y2=y + 3, class_="mm-tickmark"),
                el("line", tip, x1=tx, x2=tx, y1=y + h - 3, y2=y + h + 7, class_="mm-tickmark")]

    def right(rts):
        hr = handled_rate(rts) if rts and rts[0].get("kind") == "trap" else None
        p, n = pass_right(rts)
        return p, n if hr is None else f"handled {pct(hr, 1)} · n {len(rts)}"

    body, y = head("By kind and trap type", "Which kinds of task fail, and how? On trap rows, the ticks above and below the bar "
                   "mark the trap-handled rate" + (" (all runs pooled)." if grow(r) > 1 else "."))
    leg, lh = view_legends(ts, PAD, y + 4, W - 2 * PAD)
    sr, sh = stacked_rows(rows + trows, y + lh + 18, right, tick)
    return svg.doc("breakdown", W, y + lh + 18 + sh, "Outcomes by kind and trap type",
                   "Which kinds of task fail, and how? " + "; ".join(
                       f"{a}: {pct(sum(bool(t.get('passed')) for t in x), len(x))} of {len(x)} passed" for a, _, x in rows + trows),
                   body + leg + sr)


# ---- 6 categories ------------------------------------------------------------------------------------------------

def chart_categories(r: dict) -> str | None:
    """Failed tasks per failure category (a task counts once per category), stacked by class, most frequent first."""
    fails = [t for t in r.get("tasks") or [] if not t.get("passed")]
    if not fails:
        return None
    cats = defaultdict(list)
    for t in fails:
        for c in t.get("categories") or ["(no category)"]:
            cats[c].append(t)
    rows = sorted(cats.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    lw = max(tw(c.replace("_", " "), 12) for c, _ in rows) + 18
    x, w = PAD + lw, W - 2 * PAD - lw - 40
    top = max(len(v) for _, v in rows)
    body, y = head("Why they failed", f"Failed tasks per category ({len(fails)} failed; a task can count in several)"
                   + (", all runs pooled." if grow(r) > 1 else "."))
    leg, lh = view_legends(fails, PAD, y + 4, W - 2 * PAD)
    y += lh + 14
    groups = {v: [] for v in VIEWS}
    fixed = []
    for i, (c, cts) in enumerate(rows):
        yy = y + i * 28
        bw = w * len(cts) / top
        fixed += [text(PAD, yy + 13, c.replace("_", " "), class_="mm-lbl"),
                  text(x + bw + 6, yy + 13, str(len(cts)), class_="mm-num")]
        for v in VIEWS:
            cnt = counts(cts, v)
            groups[v] += hbar(cnt, ORDER[v], x, yy + 1, bw, 18, "{name}: {n} of " + str(len(cts)) + f" {c}", labels=False)
    y += len(rows) * 28 + 6
    return svg.doc("categories", W, y, "Why they failed",
                   "Why did the failed tasks fail? " + ", ".join(f"{c} {len(v)}" for c, v in rows[:6]),
                   body + leg + [el("g", groups[v], class_=f"mm-v mm-v-{v}") for v in VIEWS] + fixed)


# ---- 7 scaling ---------------------------------------------------------------------------------------------------

def chart_scaling(r: dict) -> str | None:
    """Outcome mix per budget as 100% stacked columns (pass at the bottom), with the pass rate as a labelled line."""
    groups = {k: v for k, v in by_run(r).items() if v}
    if len(groups) < 2:
        return None
    info = run_info(r)
    body, y = head("More tools, more failures?", "Does loading more tools break the model, and into what? "
                   "One column per budget, smallest first; the line is the pass rate (a trap's honest fail counts as a pass).")
    ts = r.get("tasks") or []
    leg, lh = view_legends(ts, PAD, y + 4, W - 2 * PAD)
    body += leg
    y += lh + 18
    x0, x1, ph = PAD + 40, W - PAD, 240
    band_w = (x1 - x0) / len(groups)
    cw = min(64, band_w * .42)
    sy = svg.linear(0, 1, y + ph, y)
    fixed = []
    for v in (0, .25, .5, .75, 1):
        fixed += [el("line", x1=x0, x2=x1, y1=sy(v), y2=sy(v), class_="mm-grid" if v else "mm-axis"),
                  text(x0 - 8, sy(v) + 4, pct(v, 1), class_="mm-tick", text_anchor="end")]
    cols = {v: [] for v in VIEWS}
    pts = []
    for i, (run, rts) in enumerate(groups.items()):
        cx = x0 + band_w * (i + .5)
        n = len(rts)
        for v in VIEWS:
            c = counts(rts, v)
            hs = svg.stack([c[k] for k in ORDER[v]], ph)
            yy = y + ph
            for k, hh in zip(ORDER[v], hs):
                if hh <= 0:
                    continue
                yy -= hh
                cols[v].append(el("rect", title(f"{run} · {name_of(k)}: {c[k]} of {n} ({pct(c[k], n)})"), x=cx - cw / 2, y=yy,
                                  width=cw, height=hh, rx=min(4, hh / 2), class_=f"mm-seg f-{k}"))
                if hh >= 18 and c[k] / n >= .06 and tw(pct(c[k], n), 11, True) + 6 <= cw:
                    cols[v].append(text(cx, yy + hh / 2, pct(c[k], n), class_=f"mm-in i-{k}", text_anchor="middle", dy="0.35em"))
        ri = info.get(run) or {}
        tok = ri.get("median_tokens")
        fixed += [text(cx, y + ph + 20, run, class_="mm-lbl", text_anchor="middle"),
                  text(cx, y + ph + 36, f"~{tok / 1000:,.0f}k tokens" if tok is not None else ri.get("budget") or "",
                       class_="mm-small", text_anchor="middle")]
        if ri.get("median_tools") is not None:
            fixed.append(text(cx, y + ph + 51, f"{fmt(ri['median_tools'])} tools", class_="mm-small", text_anchor="middle"))
        pr = sum(bool(t.get("passed")) for t in rts) / n
        pts.append((cx, sy(pr), pr))
    line = [el("path", d="M" + " L".join(f"{svg.num(a)},{svg.num(b)}" for a, b, _ in pts), class_="mm-line")]
    for a, b, pr in pts:
        line += [el("circle", title(f"pass rate {pct(pr, 1)}"), cx=a, cy=b, r=4.5, class_="mm-pt"),
                 text(a + cw / 2 + 8, b - 7, pct(pr, 1), class_="mm-num mm-halo")]
    body += fixed + [el("g", cols[v], class_=f"mm-v mm-v-{v}") for v in VIEWS] + line
    return svg.doc("scaling", W, y + ph + 64, "Pass rate and outcome mix by tool budget",
                   "Does loading more tools break the model? Pass rate by budget: " + ", ".join(
                       f"{run} {pct(p, 1)}" for run, (_, _, p) in zip(groups, pts)), body)


# ---- 8 flow ------------------------------------------------------------------------------------------------------

def common_tasks(r: dict) -> tuple[list[str], dict[str, dict[str, dict]]]:
    """Runs in order and, per run, its tasks by task id, restricted to the task ids every run has."""
    groups = {k: v for k, v in by_run(r).items() if v}
    by = {run: {t["task_id"]: t for t in rts} for run, rts in groups.items()}
    common = set.intersection(*(set(d) for d in by.values())) if by else set()
    return list(groups), {run: {k: v for k, v in d.items() if k in common} for run, d in by.items()}


def chart_flow(r: dict) -> str | None:
    """Alluvial: per budget a column of nodes by class; ribbons carry the tasks common to every run from one budget
    to the next, in the source class's colour."""
    runs, by = common_tasks(r)
    if len(runs) < 2 or not by[runs[0]]:
        return None
    ids = sorted(by[runs[0]])
    n = len(ids)
    body, y = head("Where do tasks go as the budget grows?", f"The {n} tasks every run shares, from the smallest budget "
                   "to the largest. Each ribbon is a group of tasks moving between classes.")
    allts = [by[run][i] for run in runs for i in ids]
    leg, lh = view_legends(allts, PAD, y + 4, W - 2 * PAD)
    body += leg
    y += lh + 30
    lm, rm, nw, gap, ph = 128, 128, 12, 8, 300
    xs = [PAD + lm + i * (W - 2 * PAD - lm - rm - nw) / (len(runs) - 1) for i in range(len(runs))]
    fixed = [text(x + nw / 2, y - 12, run, class_="mm-lbl", text_anchor="middle")
             for i, (x, run) in enumerate(zip(xs, runs))]
    groups = {v: [] for v in VIEWS}
    for v in VIEWS:
        order = ORDER[v]
        col = [{k: [i for i in ids if key_of(by[run][i], v) == k] for k in order} for run in runs]
        kmax = max(sum(1 for k in order if c[k]) for c in col)
        unit = (ph - gap * (kmax - 1)) / n
        pos = []  # per column: {k: (y_top, height)}
        g = []
        for ci, c in enumerate(col):
            yy, p = y, {}
            for k in order:
                if not c[k]:
                    continue
                hh = len(c[k]) * unit
                p[k] = (yy, hh)
                yy += hh + gap
            pos.append(p)
        for ci in range(len(runs) - 1):
            a, b = col[ci], col[ci + 1]
            ka = {i: k for k in order for i in a[k]}
            kb = {i: k for k in order for i in b[k]}
            flows = Counter((ka[i], kb[i]) for i in ids)
            out_off = {k: pos[ci][k][0] for k in pos[ci]}
            in_off = {k: pos[ci + 1][k][0] for k in pos[ci + 1]}
            xa, xb = xs[ci] + nw, xs[ci + 1]
            xm = (xa + xb) / 2
            src = sorted(flows, key=lambda f: (order.index(f[0]), order.index(f[1])))
            ys0 = {}
            for f in src:
                ys0[f] = out_off[f[0]]
                out_off[f[0]] += flows[f] * unit
            for f in sorted(flows, key=lambda f: (order.index(f[1]), order.index(f[0]))):
                h = flows[f] * unit
                y0, y1 = ys0[f], in_off[f[1]]
                in_off[f[1]] += h
                d = (f"M{svg.num(xa)},{svg.num(y0)} C{svg.num(xm)},{svg.num(y0)} {svg.num(xm)},{svg.num(y1)} {svg.num(xb)},{svg.num(y1)} "
                     f"L{svg.num(xb)},{svg.num(y1 + h)} C{svg.num(xm)},{svg.num(y1 + h)} {svg.num(xm)},{svg.num(y0 + h)} "
                     f"{svg.num(xa)},{svg.num(y0 + h)} Z")
                g.append(el("path", title(f"{runs[ci]} {name_of(f[0])} → {runs[ci + 1]} {name_of(f[1])}: {flows[f]} tasks"),
                            d=d, class_=f"mm-rib f-{f[0]}"))
        for ci, p in enumerate(pos):
            for k, (yy, hh) in p.items():
                cnt = len(col[ci][k])
                g.append(el("rect", title(f"{runs[ci]} · {name_of(k)}: {cnt} tasks"), x=xs[ci], y=yy, width=nw,
                            height=max(hh, 1), rx=min(3, hh / 2), class_=f"f-{k}"))
                if ci == 0:
                    g.append(text(xs[ci] - 8, yy + hh / 2 + 4, f"{name_of(k)} {cnt}", class_="mm-small", text_anchor="end"))
                elif ci == len(pos) - 1:
                    g.append(text(xs[ci] + nw + 8, yy + hh / 2 + 4, f"{cnt} {name_of(k)}", class_="mm-small"))
                elif hh >= 13:
                    g.append(text(xs[ci] + nw + 4, yy + hh / 2 + 4, str(cnt), class_="mm-small mm-halo"))
        groups[v] = g
    body += fixed + [el("g", groups[v], class_=f"mm-v mm-v-{v}") for v in VIEWS]
    first = sum(bool(by[runs[0]][i].get("passed")) for i in ids)
    kept = sum(bool(by[runs[0]][i].get("passed")) and bool(by[runs[-1]][i].get("passed")) for i in ids)
    return svg.doc("flow", W, y + ph + 16, "Where tasks go as the budget grows",
                   f"Where do the tasks that pass at a small budget go at a bigger one? Of {first} tasks passing at {runs[0]}, "
                   f"{kept} still pass at {runs[-1]}.", body)


# ---- 9 matrix ----------------------------------------------------------------------------------------------------

PATTERNS = (("breaks", "Breaks under load", "passes at the smallest budget, fails at a bigger one"),
            ("shifts", "Changes how it fails", "outcome changes without a clean break or recovery"),
            ("recovers", "Recovers", "fails at the smallest budget, passes at the largest"))


def pattern(seq: list[dict]) -> str:
    p = [bool(t.get("passed")) for t in seq]
    return "breaks" if p[0] and not all(p) else "recovers" if not p[0] and p[-1] else "shifts"


def chart_matrix(r: dict) -> str | None:
    """Task × budget grid of only the tasks whose outcome changes across budgets, grouped by pattern."""
    runs, by = common_tasks(r)
    if len(runs) < 2:
        return None
    ch = [i for i in sorted(by[runs[0]]) if len({outcome(by[run][i]) for run in runs}) > 1]
    if not ch:
        return None
    groups = defaultdict(list)
    for i in ch:
        seq = [by[run][i] for run in runs]
        first_fail = next((j for j, t in enumerate(seq) if not t.get("passed")), len(seq))
        groups[pattern(seq)].append((first_fail, i))
    info = run_info(r)
    lw = min(250, max(tw(i, 11) for i in ch) + 16)
    cw = max(62, max(tw(run, 12, True) for run in runs) + 14)
    x0 = PAD + lw
    body, y = head("Tasks that change with the budget", f"{len(ch)} of {len(by[runs[0]])} shared tasks change outcome "
                   "across budgets. Rows: tasks, grouped by pattern; columns: budgets, smallest first.")
    leg, lh = view_legends([by[run][i] for run in runs for i in ch], PAD, y + 4, W - 2 * PAD)
    body += leg
    y += lh + 22
    for j, run in enumerate(runs):
        cx = x0 + j * cw + cw / 2
        body += [text(cx, y, run, class_="mm-lbl", text_anchor="middle"),
                 text(cx, y + 14, (info.get(run) or {}).get("budget") or "", class_="mm-small", text_anchor="middle")]
    y += 26
    for p, lab, why in PATTERNS:
        rows = sorted(groups.get(p, []))
        if not rows:
            continue
        y += 14
        body += [text(PAD, y, f"{lab} · {len(rows)}", class_="mm-lbl"),
                 text(PAD + tw(f"{lab} · {len(rows)}", 12, True) + 10, y, why, class_="mm-small")]
        y += 8
        for _, i in rows:
            short = i if tw(i, 11) <= lw - 12 else i[:max(8, int((lw - 24) / 6.2))] + "…"
            body.append(text(PAD, y + 10, short, class_="mm-small"))
            for j, run in enumerate(runs):
                t = by[run][i]
                body.append(el("rect", title(f"{i} · {run} · {outcome(t)} · {name_of('b-' + band(t))}"),
                               **mark(t, x=x0 + j * cw + 2, y=y + 1, width=cw - 4, height=12, rx=3)))
            y += 15
    return svg.doc("matrix", W, y + 12, "Tasks that change with the budget",
                   f"Which tasks change outcome as tools are added? " + ", ".join(
                       f"{lab.lower()}: {len(groups.get(p, []))}" for p, lab, _ in PATTERNS), body)


def render_all(report: dict) -> dict[str, str]:
    """{name: svg} for every chart that applies to the report, in CHARTS order."""
    out = {}
    for name in CHARTS:
        s = globals()[f"chart_{name}"](report)
        if s:
            out[name] = s
    return out
