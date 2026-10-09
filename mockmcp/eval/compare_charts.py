"""The comparison charts of `eval compare` as standalone SVG, drawn from a COMPARE dict (compare_data.build / compare.json).

Same visual system and contract as charts.py (its helpers and svg.py's palette, imported): each builder returns one
self-contained SVG or None when it does not apply. Side A and side B wear `--mm-side-a` / `--mm-side-b`; the four
head-to-head classes (both pass, only A, only B, both fail) wear a pass tint, the two side colours and a fail tint.
Per-task marks carry `mm-t` plus data-key (the compare task key), data-kind, data-run and data-side where a mark belongs
to one side: the diffs cells also carry `o-… b-… pf-…` of their side so `data-view` recolours them; the paired dots are
coloured by `ch-<change>` and keep that colour in every view. Aggregate charts carry one `mm-v-<view>` group per view
where the view changes them, the paired scatter one `mm-m-<metric>` group per effort metric. Every figure is computed
from the common tasks in `cmp["tasks"]`, so a chart and the table under it can never disagree."""
import math
import statistics
from collections import Counter

from . import svg
from .charts import LABEL, METRIC, ORDER, PAD, W, counts, head, hbar, key_of, legend, name_of, pct, view_legends
from .svg import METRICS, VIEWS, el, esc, fmt, text, title, tw

CHARTS: tuple[str, ...] = ("scoreboard", "headtohead", "shift", "outcomes", "paired", "spend", "diffs")
__all__ = ["CHARTS", "render_all", "mcnemar"] + [f"chart_{c}" for c in CHARTS]

CHANGES = ("both_pass", "a_only", "b_only", "both_fail")
# Change classes: the two sides' wins in their own colours, the agreements as tints of pass and fail (context, not news).
# The tint is stronger in dark, where a faint fill sinks into the background; its selectors mirror svg.theme_css.
CSS = """.mm-chart{--mm-tint:.3}
@media (prefers-color-scheme: dark){.mm-chart:not([data-theme=light]){--mm-tint:.55}}
:root[data-theme=light] .mm-chart:not([data-theme=dark]),.mm-chart.mm-chart[data-theme=light]{--mm-tint:.3}
:root[data-theme=dark] .mm-chart:not([data-theme=light]),.mm-chart.mm-chart[data-theme=dark]{--mm-tint:.55}
.mm-chart .f-ch-both_pass,.mm-chart .mm-t.ch-both_pass{fill:var(--mm-pass);fill-opacity:var(--mm-tint)}
.mm-chart .f-ch-both_fail,.mm-chart .mm-t.ch-both_fail{fill:var(--mm-fail);fill-opacity:var(--mm-tint)}
.mm-chart .f-ch-a_only,.mm-chart .mm-t.ch-a_only{fill:var(--mm-side-a)}
.mm-chart .f-ch-b_only,.mm-chart .mm-t.ch-b_only{fill:var(--mm-side-b)}
.mm-chart .mm-link{stroke-width:4px;stroke-linecap:round;stroke-opacity:.5;fill:none}
.mm-chart .mm-diag{stroke:var(--mm-muted);stroke-width:1.25;stroke-dasharray:4 4;fill:none}
.mm-chart .mm-sig{font-weight:600}
"""


# ---- data helpers -------------------------------------------------------------------------------------------------

def mcnemar(a_only: int, b_only: int) -> float:
    """Exact two-sided McNemar p on the discordant pairs (binomial, p = 1/2); 1.0 when there are none."""
    n, k = a_only + b_only, min(a_only, b_only)
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def labels(cmp: dict) -> tuple[str, str]:
    """The two side labels (A, B), defaulting to "A" and "B"."""
    lab = list(cmp.get("labels") or []) + ["A", "B"]
    return str(lab[0] or "A"), str(lab[1] or "B")


def short(s: str, width: float, size: float = 12) -> str:
    """`s` cut with an ellipsis to fit `width` px."""
    s = str(s)
    if tw(s, size) <= width:
        return s
    while s and tw(s + "…", size) > width:
        s = s[:-1]
    return s + "…"


def groups(cmp: dict) -> list[tuple[str, str, list[dict]]]:
    """[(run, budget, common tasks)] in the order of cmp.runs (runs without common tasks left out)."""
    by = {}
    for t in cmp.get("tasks") or []:
        by.setdefault(t["run"], []).append(t)
    info = {r["run"]: r for r in cmp.get("runs") or []}
    order = [r["run"] for r in cmp.get("runs") or []] + sorted(set(by) - set(info))
    return [(run, (info.get(run) or {}).get("budget") or (by[run][0].get("budget") or ""), by[run]) for run in order if by.get(run)]


def with_all(gs: list[tuple[str, str, list[dict]]]) -> list[tuple[str, str, list[dict]]]:
    """The groups plus an "all runs" group when there are two or more."""
    return gs + [("all runs", "", [t for _, _, ts in gs for t in ts])] if len(gs) > 1 else gs


def change(t: dict) -> str:
    c = t.get("change")
    if c in CHANGES:
        return c
    a, b = bool(t["a"].get("passed")), bool(t["b"].get("passed"))
    return "both_pass" if a and b else "a_only" if a else "b_only" if b else "both_fail"


def h2h(ts: list[dict]) -> Counter:
    return Counter(change(t) for t in ts)


def eff(side: dict, m: str) -> float:
    return float((side.get("effort") or {}).get(m) or 0)


def passed(ts: list[dict], s: str) -> int:
    return sum(bool(t[s].get("passed")) for t in ts)


def side_ts(ts: list[dict], s: str) -> list[dict]:
    """One side's entries of compare tasks, shaped enough like REPORT tasks for charts.key_of / counts."""
    return [{**t[s], "task_id": t.get("task_id"), "run": t.get("run"), "kind": t.get("kind")} for t in ts]


def pts(d: float) -> str:
    """A pass-rate difference in percentage points, signed."""
    v = round(d * 100, 1)
    return "±0 pts" if v == 0 else f"{v:+.1f} pts"


def pval(p: float) -> str:
    return "p < 0.001" if p < .001 else f"p {p:.3f}" if p < .01 else f"p {p:.2f}"


def ratio(b: float, a: float) -> str:
    if not a:
        return "–"
    r = b / a
    return "1.0×" if abs(r - 1) < .005 else f"{r:.2f}×" if r < 1 else f"{r:.1f}×" if r < 10 else f"{r:.0f}×"


def side_key(cmp: dict, x: float, y: float, r: float = 5) -> tuple[list[str], float]:
    """The A / B key: a dot in each side's colour and its label; returns markup and the width used."""
    out, cx = [], x
    for s, lab in zip("ab", labels(cmp)):
        lab = f"{short(lab, 220)} ({s.upper()})"
        out += [el("circle", cx=cx + r, cy=y - 4, r=r, class_=f"f-side-{s}"), text(cx + 2 * r + 6, y, lab, class_="mm-lbl")]
        cx += 2 * r + 6 + tw(lab, 12, True) + 22
    return out, cx - x


def doc(name: str, h: float, head_: str, desc: str, body: list[str], **attrs) -> str:
    return svg.doc(name, W, h, head_, desc, [el("style", CSS)] + body, **attrs)


def run_label(run: str, budget: str, x: float, y: float, sub: str = "") -> list[str]:
    """A run's name (bold) over its budget and an optional extra (small)."""
    out = [text(x, y, short(run, 110), class_="mm-lbl")]
    s = " · ".join(v for v in (budget, sub) if v)
    return out + ([text(x, y + 15, short(s, 116, 11), class_="mm-small")] if s else [])


# ---- 1 scoreboard -------------------------------------------------------------------------------------------------

def chart_scoreboard(cmp: dict) -> str | None:
    """Dumbbell per paired run (plus all runs): A's and B's pass rate on the common tasks, the bar between them in the
    winner's colour, the gap in points and the exact McNemar p."""
    gs = with_all(groups(cmp))
    if not gs:
        return None
    la, lb = labels(cmp)
    body, y = head("Who passes more?", "Pass rate on the tasks both runs share, one row per run. The bar joins the two dots "
                   "in the winner's colour. p is an exact McNemar test on the tasks only one side passed: below 0.05 the gap "
                   "is unlikely to be chance.")
    key, _ = side_key(cmp, PAD, y + 6)
    body += key
    y += 30
    lw, rw = 132, 128
    x0, x1 = PAD + lw, W - PAD - rw
    sx = svg.linear(0, 1, x0, x1)
    step = 46
    top, bottom = y + 16, y + 16 + len(gs) * step
    fixed = []
    for v in (0, .25, .5, .75, 1):
        fixed += [el("line", x1=sx(v), x2=sx(v), y1=top - 4, y2=bottom - 8, class_="mm-grid"),
                  text(sx(v), top - 10, pct(v, 1), class_="mm-tick", text_anchor="middle")]
    rows, notes = [], []
    for i, (run, bud, ts) in enumerate(gs):
        cy = top + i * step + 18
        n, c = len(ts), h2h(ts)
        ra, rb = passed(ts, "a") / n, passed(ts, "b") / n
        p = mcnemar(c["a_only"], c["b_only"])
        if run == "all runs":
            rows.append(el("line", x1=PAD, x2=W - PAD, y1=cy - 23, y2=cy - 23, class_="mm-grid"))
        rows += run_label(run, bud, PAD, cy - 2, f"n {n}")
        win = "b" if rb > ra else "a" if ra > rb else None
        lo, hi = sorted((ra, rb))
        if win:
            rows.append(el("line", title(f"{pts(rb - ra)} for {lb if win == 'b' else la}"), x1=sx(lo), x2=sx(hi), y1=cy - 4,
                           y2=cy - 4, class_=f"mm-link s-side-{win}"))
        for s, r, lab in (("a", ra, la), ("b", rb, lb)):   # on a tie A's dot is drawn larger, so B's sits inside it
            rows.append(el("circle", title(f"{lab}: {pct(r, 1)} ({passed(ts, s)} of {n}) · {run}"), cx=sx(r), cy=cy - 4,
                           r=9 if s == "a" and not win else 6.5, class_=f"mm-dot f-side-{s}"))
        if win:
            rows += [text(sx(lo) - 11, cy, pct(lo, 1), class_="mm-num", text_anchor="end"),
                     text(sx(hi) + 11, cy, pct(hi, 1), class_="mm-num")]
        else:
            rows.append(text(sx(hi) + 14, cy, f"{pct(hi, 1)} both", class_="mm-num"))
        sig = p < .05
        rows += [text(W - PAD, cy - 6, pts(rb - ra), class_="mm-num", text_anchor="end"),
                 el("text", esc(pval(p) + (" · significant" if sig else "")), x=W - PAD, y=cy + 10, text_anchor="end",
                    class_="mm-small" + (" mm-sig" if sig else ""))]
        notes.append(f"{run}: {la} {pct(ra, 1)}, {lb} {pct(rb, 1)} ({pts(rb - ra)}, {pval(p)})")
    body += fixed + rows
    body.append(text(W - PAD, top - 10, "B − A", class_="mm-tick", text_anchor="end"))   # the names are in the key
    return doc("scoreboard", bottom + 8, "Pass rate, A vs B", "Who passes more on the same tasks, and is the gap real? "
               + "; ".join(notes) + ".", body)


# ---- 2 head to head -----------------------------------------------------------------------------------------------

def chart_headtohead(cmp: dict) -> str | None:
    """Per run a diverging bar centred on the tasks only one side passed (A's wins to the left, B's to the right), with
    the tasks both passed and both failed as tinted end caps."""
    gs = with_all(groups(cmp))
    if not gs:
        return None
    la, lb = labels(cmp)
    body, y = head("Head to head on the same tasks", "Every shared task falls in one of four boxes. In the middle: tasks "
                   "only one side passed, A's wins to the left of the centre line, B's to the right. Tinted ends: tasks both "
                   "passed (left) or both failed (right). Lengths are shares of each row's tasks.")
    names = {"both_pass": "both pass", "a_only": f"only {short(la, 150)} passes", "b_only": f"only {short(lb, 150)} passes",
             "both_fail": "both fail"}
    leg, lh = legend([(f"ch-{k}", names[k]) for k in CHANGES], PAD, y + 4, W - 2 * PAD)
    body += leg
    y += lh + 26
    lw, rw = 132, 150
    x0, x1 = PAD + lw, W - PAD - rw
    cx = (x0 + x1) / 2
    cs = [h2h(ts) for _, _, ts in gs]
    # shares, not counts, so the pooled row and the runs read on one scale
    half = max(max(c["both_pass"] + c["a_only"], c["b_only"] + c["both_fail"]) / max(1, sum(c.values())) for c in cs) or 1
    h, step = 24, 50
    y += 10
    out = []
    for i, ((run, bud, ts), c) in enumerate(zip(gs, cs)):
        unit = (cx - x0) / half / len(ts)
        yy = y + i * step
        if run == "all runs":
            out.append(el("line", x1=PAD, x2=W - PAD, y1=yy - 11, y2=yy - 11, class_="mm-grid"))
        out += run_label(run, bud, PAD, yy + h / 2 - 2, f"n {len(ts)}")
        segs = [("both_pass", cx - (c["a_only"] + c["both_pass"]) * unit), ("a_only", cx - c["a_only"] * unit),
                ("b_only", cx), ("both_fail", cx + c["b_only"] * unit)]
        for k, sx in segs:
            w = c[k] * unit
            if w <= 0:
                continue
            out.append(el("rect", title(f"{run} · {names[k]}: {c[k]} of {len(ts)} ({pct(c[k], len(ts))})"), x=sx, y=yy, width=w,
                          height=h, rx=min(4, w / 2), class_=f"mm-seg f-ch-{k}"))
            s = str(c[k])
            if tw(s, 11, True) + 8 <= w:
                out.append(text(sx + w / 2, yy + h / 2, s, class_="mm-in" + (" i-side-a" if k == "a_only" else " i-side-b"
                                                                              if k == "b_only" else ""),
                                text_anchor="middle", dy="0.35em"))
            elif k in ("a_only", "b_only"):   # a sliver: its count sits just outside, above the bar
                out.append(text(sx + w / 2, yy - 4, s, class_="mm-small", text_anchor="middle"))
        a, b = c["a_only"], c["b_only"]
        verdict = f"{short(lb, 70)} +{b - a}" if b > a else f"{short(la, 70)} +{a - b}" if a > b else "even"
        out += [text(W - PAD, yy + h / 2 - 3, verdict, class_="mm-num", text_anchor="end"),
                text(W - PAD, yy + h / 2 + 12, f"wins {a} vs {b} · {pval(mcnemar(a, b))}", class_="mm-small", text_anchor="end")]
    bottom = y + len(gs) * step - 14
    out = [el("line", x1=cx, x2=cx, y1=y - 16, y2=bottom, class_="mm-axis"),
           text(cx - 6, y - 22, f"← {short(la, 140)} wins", class_="mm-small", text_anchor="end"),
           text(cx + 6, y - 22, f"{short(lb, 140)} wins →", class_="mm-small")] + out
    tot = h2h([t for _, _, ts in groups(cmp) for t in ts])
    return doc("headtohead", bottom + 12, "Head to head on the same tasks",
               f"On the same tasks, who wins? Over all runs: both pass {tot['both_pass']}, only {la} {tot['a_only']}, "
               f"only {lb} {tot['b_only']}, both fail {tot['both_fail']}.", body + out)


# ---- 3 shift ------------------------------------------------------------------------------------------------------

def _alluvial(ts: list[dict], view: str, y: float, ph: float, xa: float, xb: float, nw: float, run: str,
              la: str, lb: str) -> list[str]:
    """One two-column alluvial of the tasks' class under A (left) and under B (right) in a view."""
    order = ORDER[view]
    ka = [key_of(t["a"], view) for t in ts]
    kb = [key_of(t["b"], view) for t in ts]
    ca, cb = Counter(ka), Counter(kb)
    n, gap = len(ts), 7
    kmax = max(sum(1 for k in order if c[k]) for c in (ca, cb))
    unit = (ph - gap * (kmax - 1)) / n

    def nodes(c):
        p, yy = {}, y
        for k in order:
            if c[k]:
                p[k] = (yy, c[k] * unit)
                yy += c[k] * unit + gap
        return p

    pa, pb = nodes(ca), nodes(cb)
    flows = Counter(zip(ka, kb))
    out_off, in_off = {k: v[0] for k, v in pa.items()}, {k: v[0] for k, v in pb.items()}
    ys0 = {}
    for f in sorted(flows, key=lambda f: (order.index(f[0]), order.index(f[1]))):
        ys0[f] = out_off[f[0]]
        out_off[f[0]] += flows[f] * unit
    g, x0, x1 = [], xa + nw, xb
    xm = (x0 + x1) / 2
    for f in sorted(flows, key=lambda f: (order.index(f[1]), order.index(f[0]))):
        hh = flows[f] * unit
        y0, y1 = ys0[f], in_off[f[1]]
        in_off[f[1]] += hh
        n_ = svg.num
        d = (f"M{n_(x0)},{n_(y0)} C{n_(xm)},{n_(y0)} {n_(xm)},{n_(y1)} {n_(x1)},{n_(y1)} L{n_(x1)},{n_(y1 + hh)} "
             f"C{n_(xm)},{n_(y1 + hh)} {n_(xm)},{n_(y0 + hh)} {n_(x0)},{n_(y0 + hh)} Z")
        g.append(el("path", title(f"{run} · {la} {name_of(f[0])} → {lb} {name_of(f[1])}: {flows[f]} tasks"), d=d,
                    class_=f"mm-rib f-{f[0]}"))
    for x, p, c, lab, side in ((xa, pa, ca, la, "left"), (xb, pb, cb, lb, "right")):
        for k, (yy, hh) in p.items():
            g.append(el("rect", title(f"{lab} · {name_of(k)}: {c[k]} tasks"), x=x, y=yy, width=nw, height=max(hh, 1.5),
                        rx=min(3, hh / 2), class_=f"f-{k}"))
            s = f"{name_of(k)} {c[k]}" if side == "left" else f"{c[k]} {name_of(k)}"
            g.append(text(x - 8 if side == "left" else x + nw + 8, yy + hh / 2 + 4, s, class_="mm-small",
                          text_anchor="end" if side == "left" else None))
    return g


def chart_shift(cmp: dict) -> str | None:
    """Alluvial of each common task's class under A (left) and under B (right): per run when there are at most two,
    all runs pooled otherwise; one group per view."""
    gs = groups(cmp)
    if not gs:
        return None
    panels = gs if len(gs) <= 2 else [("all runs", "", [t for _, _, ts in gs for t in ts])]
    la, lb = labels(cmp)
    body, y = head("Where do outcomes move?", "Each shared task's outcome under A (left) and under B (right); ribbons "
                   "carry groups of tasks and keep A's colour, so a ribbon ending in another class is a task that changed.")
    allts = [t for _, _, ts in panels for t in ts]
    leg, lh = view_legends(side_ts(allts, "a") + side_ts(allts, "b"), PAD, y + 4, W - 2 * PAD)
    body += leg
    y += lh - 4
    nw, lm, rm = 12, 150, 150
    xa, xb = PAD + lm, W - PAD - rm - nw
    ph = 230 if len(panels) == 1 else 190
    per_v = {v: [] for v in VIEWS}
    fixed = []
    for run, bud, ts in panels:
        moved = sum(t["a"].get("outcome") != t["b"].get("outcome") for t in ts)
        y += 18
        fixed += [text(PAD, y, run, class_="mm-lbl"),
                  text(PAD + tw(run, 12, True) + 8, y, " · ".join(v for v in (bud, f"{moved} of {len(ts)} tasks change outcome") if v),
                       class_="mm-small")]
        y += 26
        for s, x, anchor in (("a", xa + nw, "end"), ("b", xb, None)):
            lab = short(labels(cmp)[s == "b"], (W - PAD - x - 22) if s == "b" else (x - PAD - 22), 12.6)
            wl = tw(lab, 12, True)
            dx = x - wl - 16 if anchor == "end" else x
            fixed += [el("circle", cx=dx + 5, cy=y - 4, r=5, class_=f"f-side-{s}"), text(dx + 16, y, lab, class_="mm-lbl")]
        y += 14
        for v in VIEWS:
            per_v[v] += _alluvial(ts, v, y, ph, xa, xb, nw, run, la, lb)
        y += ph + 14
    body += fixed + [el("g", per_v[v], class_=f"mm-v mm-v-{v}") for v in VIEWS]
    ts = [t for _, _, x in panels for t in x]
    fa = [t for t in ts if not t["a"].get("passed")]
    return doc("shift", y + 4, "Outcome shift from A to B",
               f"Where do A's failures go under B, and B's under A? Of {len(fa)} tasks {la} failed, {lb} passed "
               f"{sum(bool(t['b'].get('passed')) for t in fa)}; of {passed(ts, 'a')} {la} passed, {lb} failed "
               f"{sum(not t['b'].get('passed') for t in ts if t['a'].get('passed'))}.", body)


# ---- 4 outcomes ---------------------------------------------------------------------------------------------------

def chart_outcomes(cmp: dict) -> str | None:
    """Per run, A's outcome mix above B's as aligned 100% bars over the common tasks, in all three views."""
    gs = with_all(groups(cmp))
    if not gs:
        return None
    la, lb = labels(cmp)
    body, y = head("Outcome mix, A over B", "The same shared tasks under each side: pass on the left, failures grow from the "
                   "right edge, worst last. Bars of one run are aligned, so a longer segment is more of that outcome.")
    allts = [t for _, _, ts in groups(cmp) for t in ts]
    leg, lh = view_legends(side_ts(allts, "a") + side_ts(allts, "b"), PAD, y + 4, W - 2 * PAD)
    body += leg
    y += lh + 16
    lw, rw = min(170, max(tw(la, 12), tw(lb, 12)) + 34), 104
    x, w, h = PAD + lw, W - 2 * PAD - lw - rw, 20
    per_v = {v: [] for v in VIEWS}
    fixed = []
    for run, bud, ts in gs:
        if run == "all runs":
            fixed.append(el("line", x1=PAD, x2=W - PAD, y1=y - 2, y2=y - 2, class_="mm-grid"))
        y += 16
        fixed += [text(PAD, y, run, class_="mm-lbl"),
                  text(PAD + tw(run, 12, True) + 8, y, " · ".join(v for v in (bud, f"{len(ts)} shared tasks") if v), class_="mm-small")]
        y += 10
        for s, lab in zip("ab", (la, lb)):
            st = side_ts(ts, s)
            fixed += [el("circle", cx=PAD + 5, cy=y + h / 2, r=5, class_=f"f-side-{s}"),
                      text(PAD + 16, y + h / 2 + 4, short(lab, lw - 24), class_="mm-small"),
                      text(W - PAD, y + h / 2 + 4, "passed", class_="mm-small", text_anchor="end"),
                      text(W - PAD - 46, y + h / 2 + 4, pct(passed(ts, s), len(ts)), class_="mm-num", text_anchor="end")]
            for v in VIEWS:
                per_v[v] += hbar(counts(st, v), ORDER[v], x, y, w, h, f"{lab} · {run} · " + "{name}: {n} tasks ({share})")
            y += h + 6
        y += 10
    body += [el("g", per_v[v], class_=f"mm-v mm-v-{v}") for v in VIEWS] + fixed
    return doc("outcomes", y + 4, "Outcome mix, A vs B",
               "How do the two outcome mixes differ on the same tasks? " + "; ".join(
                   f"{run}: {la} {pct(passed(ts, 'a'), len(ts))}, {lb} {pct(passed(ts, 'b'), len(ts))} passed" for run, _, ts in gs),
               body)


# ---- 5 paired -----------------------------------------------------------------------------------------------------

def _pscale(vals: list[float], m: str, r0: float, r1: float):
    """One scale for both axes of a metric: log (zeros clamp to the low edge) for tokens, time and cost; linear for calls."""
    if METRIC[m][2]:
        pos = [v for v in vals if v > 0] or [1]
        lo, hi = svg.log_bounds(min(pos), max(pos))
        if len(svg.log_ticks(lo, hi)) < 3:
            lo /= 10
        return svg.log(lo, hi, r0, r1), svg.log_ticks(lo, hi)
    ticks = svg.nice_ticks(0, max(vals + [1]), 5)
    return svg.linear(0, ticks[-1], r0, r1), ticks


def chart_paired(cmp: dict) -> str | None:
    """Per-task scatter of A's effort (x) against B's (y) on one shared scale, the diagonal y = x and the "B costlier"
    side shaded; dots coloured by who passed. One group per effort metric."""
    ts = [t for _, _, x in groups(cmp) for t in x]
    if not ts:
        return None
    la, lb = labels(cmp)
    body, y = head("Effort on the same task", "Each dot is one shared task: A's effort across, B's up, on one scale. Above "
                   "the dashed diagonal B spent more, below it A did. Colour says who passed.")
    key, _ = side_key(cmp, PAD, y + 6)
    body += key
    y += 34
    size = 400
    x0, yb = PAD + 52, y + size + 6
    x1, yt = x0 + size, yb - size
    px = x1 + 36
    c = h2h(ts)
    names = {"both_pass": "both pass", "a_only": f"only {short(la, 130)} passes", "b_only": f"only {short(lb, 130)} passes",
             "both_fail": "both fail"}
    fixed = [text(px, yt + 4, "Who passed", class_="mm-lbl")]
    for i, k in enumerate(CHANGES):
        fixed += [el("circle", cx=px + 5, cy=yt + 22 + i * 20 - 4, r=5, class_=f"mm-dot f-ch-{k}"),
                  text(px + 16, yt + 22 + i * 20, names[k], class_="mm-small"),
                  text(W - PAD, yt + 22 + i * 20, str(c[k]), class_="mm-num", text_anchor="end")]
    zorder = {"both_pass": 0, "both_fail": 1, "a_only": 2, "b_only": 3}
    dots = sorted(ts, key=lambda t: (zorder[change(t)], str(t.get("key"))))
    per_m = {m: [] for m in METRICS}
    for m in METRICS:
        lab, unit, _ = METRIC[m]
        sx, ticks = _pscale([eff(t[s], m) for t in ts for s in "ab"], m, x0, x1)
        sy = lambda v, sx=sx: yb - (sx(v) - x0)
        g = [el("path", d=f"M{x0},{yb} L{x1},{yt} L{x0},{yt} Z", class_="mm-zone")]
        for v in ticks:
            g += [el("line", x1=sx(v), x2=sx(v), y1=yt, y2=yb, class_="mm-grid"),
                  el("line", x1=x0, x2=x1, y1=sy(v), y2=sy(v), class_="mm-grid"),
                  text(sx(v), yb + 16, fmt(v, unit), class_="mm-tick", text_anchor="middle"),
                  text(x0 - 8, sy(v) + 4, fmt(v, unit), class_="mm-tick", text_anchor="end")]
        g += [el("line", x1=x0, x2=x1, y1=yb, y2=yb, class_="mm-axis"), el("line", x1=x0, x2=x0, y1=yt, y2=yb, class_="mm-axis"),
              el("line", x1=x0, x2=x1, y1=yb, y2=yt, class_="mm-diag"),
              text(x0 + 10, yt + 18, f"{short(lb, 160)} spent more", class_="mm-small"),
              text(x1 - 10, yb - 10, f"{short(la, 160)} spent more", class_="mm-small", text_anchor="end"),
              text(x1, yb + 34, f"{short(la, 200)}: {lab}" + (" (log)" if METRIC[m][2] else "") + " →", class_="mm-small",
                   text_anchor="end"),
              text(x0 - 40, yt - 10, f"↑ {short(lb, 200)}: {lab}", class_="mm-small")]
        for t in dots:
            a, b = eff(t["a"], m), eff(t["b"], m)
            g.append(el("circle", title(f"{t.get('task_id')} · {t.get('run')} · {la} {fmt(a, unit)} ({t['a'].get('outcome')}) · "
                                        f"{lb} {fmt(b, unit)} ({t['b'].get('outcome')})"),
                        class_=f"mm-dot mm-t ch-{change(t)}", cx=sx(a), cy=sy(b), r=4, data_key=t.get("key"),
                        data_kind=t.get("kind"), data_run=t.get("run")))
        ta, tb = sum(eff(t["a"], m) for t in ts), sum(eff(t["b"], m) for t in ts)
        more_b = sum(eff(t["b"], m) > eff(t["a"], m) for t in ts)
        more_a = sum(eff(t["a"], m) > eff(t["b"], m) for t in ts)
        rs = [eff(t["b"], m) / eff(t["a"], m) for t in ts if eff(t["a"], m) > 0 and eff(t["b"], m) > 0]
        sy0 = yt + 22 + 4 * 20 + 18
        stats = [("total, A vs B", f"{fmt(ta, unit)} vs {fmt(tb, unit)}"), ("B ÷ A", ratio(tb, ta)),
                 ("B ÷ A, median task", f"{statistics.median(rs):.2f}×" if rs else "–"),
                 ("B spent more", f"{more_b} tasks"), ("A spent more", f"{more_a} tasks")]
        g.append(text(px, sy0, lab.capitalize(), class_="mm-lbl"))
        for i, (k, v) in enumerate(stats):
            g += [text(px, sy0 + 20 + i * 18, k, class_="mm-small"), text(W - PAD, sy0 + 20 + i * 18, v, class_="mm-num", text_anchor="end")]
        per_m[m] = g
    body += fixed + [el("g", per_m[m], class_=f"mm-m mm-m-{m}") for m in METRICS]
    tok = lambda s: sum(eff(t[s], "input_tokens") for t in ts)
    return doc("paired", yb + 44, "Effort per task, A vs B",
               f"Which side burns more effort on the same task? Input tokens: {la} {fmt(tok('a'), 'tokens')}, {lb} "
               f"{fmt(tok('b'), 'tokens')} over {len(ts)} shared tasks; {lb} spent more on "
               f"{sum(eff(t['b'], 'input_tokens') > eff(t['a'], 'input_tokens') for t in ts)}.", body, data_metric="input_tokens")


# ---- 6 spend ------------------------------------------------------------------------------------------------------

SPEND = (("cost_usd", "cost", "usd"), ("input_tokens", "input tokens", "tokens"), ("seconds", "time", "s"),
         ("tool_calls", "tool calls", "n"), ("cost_per_pass", "cost per pass", "usd"))


def _spend(ts: list[dict], s: str, m: str) -> float | None:
    if m == "cost_per_pass":
        p = passed(ts, s)
        return sum(eff(t[s], "cost_usd") for t in ts) / p if p else None
    return sum(eff(t[s], m) for t in ts)


def chart_spend(cmp: dict) -> str | None:
    """Small multiples, one column per spend metric and one row per run: A's and B's totals over the common tasks as
    paired bars with B/A as a ratio, plus the cost per passed task."""
    gs = with_all(groups(cmp))
    if not gs:
        return None
    la, lb = labels(cmp)
    body, y = head("What does each side cost?", "Totals over the shared tasks, A's bar over B's, each column on its own scale. "
                   "The figure under each pair is B's total as a multiple of A's.")
    key, _ = side_key(cmp, PAD, y + 6)
    body += key
    y += 36
    lw = 118
    cw = (W - 2 * PAD - lw) / len(SPEND)
    vals = {(run, m, s): _spend(ts, s, m) for run, _, ts in gs for m, _, _ in SPEND for s in "ab"}
    top = {m: max([v for (r, mm, _), v in vals.items() if mm == m and v is not None and r != "all runs"] or [0])
           or max([v for (_, mm, _), v in vals.items() if mm == m and v is not None] or [1]) or 1 for m, _, _ in SPEND}
    out = []
    for j, (m, lab, _) in enumerate(SPEND):
        out.append(text(PAD + lw + j * cw, y, lab, class_="mm-lbl"))
    y += 12
    rh = 62
    for i, (run, bud, ts) in enumerate(gs):
        yy = y + i * rh
        if run == "all runs":
            out.append(el("line", x1=PAD, x2=W - PAD, y1=yy - 2, y2=yy - 2, class_="mm-grid"))
        out += run_label(run, bud, PAD, yy + 16) + [text(PAD, yy + 52, "B ÷ A", class_="mm-small")]
        for j, (m, lab, unit) in enumerate(SPEND):
            cx = PAD + lw + j * cw
            bw_max = cw - 58
            for k, s in enumerate("ab"):
                v = vals[run, m, s]
                by = yy + 6 + k * 16
                # the all-runs row can exceed the per-run maximum: its bars share the column scale, capped at full width
                bw = 0 if v is None else bw_max * min(1, v / top[m])
                bw = max(bw, 3) if v else 0
                out.append(el("rect", title(f"{(la, lb)[k]} · {run} · {lab}: {fmt(v, unit)}"), x=cx, y=by, width=bw, height=12,
                              rx=min(3, bw / 2), class_=f"f-side-{s}") if v else
                           el("line", x1=cx, x2=cx, y1=by, y2=by + 12, class_="mm-axis"))
                out.append(text(cx + bw + 5, by + 10, fmt(v, unit) if v is not None else "–", class_="mm-small"))
            a, b = vals[run, m, "a"], vals[run, m, "b"]
            out.append(text(cx, yy + 52, ratio(b, a) if a is not None and b is not None else "–", class_="mm-num"))
    y += len(gs) * rh
    tot = gs[-1][2]
    ca, cb = _spend(tot, "a", "cost_usd"), _spend(tot, "b", "cost_usd")
    return doc("spend", y + 4, "Spend, A vs B",
               f"What does each side cost on the same tasks? Cost {la} {fmt(ca, 'usd')}, {lb} {fmt(cb, 'usd')} ({ratio(cb, ca)}); "
               f"cost per pass {la} {fmt(_spend(tot, 'a', 'cost_per_pass'), 'usd')}, {lb} {fmt(_spend(tot, 'b', 'cost_per_pass'), 'usd')}.",
               body + out)


# ---- 7 diffs ------------------------------------------------------------------------------------------------------

DIFF_GROUPS = (("b_fix", "Only {b} passes", "{a} fails these"), ("a_fix", "Only {a} passes", "{b} fails these"),
               ("fail_diff", "Both fail, differently", "less severe under {b} first"),
               ("pass_diff", "Both pass, differently", "a trap's honest fail against a pass"))


def diff_group(t: dict) -> str | None:
    """The diffs group of a compare task, or None when its outcome is the same on both sides."""
    if t["a"].get("outcome") == t["b"].get("outcome"):
        return None
    return {"b_only": "b_fix", "a_only": "a_fix", "both_fail": "fail_diff", "both_pass": "pass_diff"}[change(t)]


def side_mark(t: dict, s: str, **attrs) -> dict:
    """Attributes of a per-task mark for one side of a compare task (charts.py's classes, the compare key)."""
    e = t[s]
    o = e.get("outcome") or ""
    b = e.get("band") or o
    cls = f"mm-t o-{o} b-{b} pf-{'pass' if e.get('passed') else 'fail'}" + (" near" if e.get("near_miss") else "")
    return dict(class_=cls, data_key=t.get("key"), data_side=s, data_kind=t.get("kind"), data_run=t.get("run"), **attrs)


def chart_diffs(cmp: dict) -> str | None:
    """Task × side grid of only the shared tasks whose outcome differs, per run, grouped: B fixes, A fixes, both fail
    differently (and both pass differently)."""
    gs = groups(cmp)
    rows = [(run, bud, [t for t in ts if diff_group(t)]) for run, bud, ts in gs]
    rows = [r for r in rows if r[2]]
    if not rows:
        return None
    la, lb = labels(cmp)
    nd, nt = sum(len(r[2]) for r in rows), sum(len(ts) for _, _, ts in gs)
    body, y = head("Tasks that flip", f"{nd} of {nt} shared tasks end differently under the two sides. One row per task: "
                   "A's outcome, then B's.")
    allts = [t for _, _, ts in rows for t in ts]
    leg, lh = view_legends(side_ts(allts, "a") + side_ts(allts, "b"), PAD, y + 4, W - 2 * PAD)
    key, _ = side_key(cmp, PAD, y + lh + 10)
    body += leg + key
    y += lh + 44
    lw, cw = 270, 84
    xa = PAD + lw
    for k, s in enumerate("ab"):
        cx = xa + k * cw + cw / 2
        body += [el("circle", cx=cx - 9, cy=y - 4, r=4, class_=f"f-side-{s}"), text(cx + 2, y, s.upper(), class_="mm-lbl")]
    body.append(text(xa + 2 * cw + 16, y, "outcome change", class_="mm-small"))
    y += 8
    sub = {k: (lab.format(a=short(la, 200), b=short(lb, 200)), why.format(a=short(la, 200), b=short(lb, 200)))
           for k, lab, why in DIFF_GROUPS}
    counts_ = Counter()
    for run, bud, ts in rows:
        if len(gs) > 1:
            y += 22
            body += [text(PAD, y, run, class_="mm-lbl"), text(PAD + tw(run, 12, True) + 8, y, bud or "", class_="mm-small")]
        for k, _, _ in DIFF_GROUPS:
            gts = sorted((t for t in ts if diff_group(t) == k),
                         key=lambda t: (t.get("shift") != "better", -abs((t["b"].get("band_rank") or 0) - (t["a"].get("band_rank") or 0)),
                                        str(t.get("task_id"))))
            if not gts:
                continue
            counts_[k] += len(gts)
            lab, why = sub[k]
            y += 20
            body += [text(PAD, y, f"{lab} · {len(gts)}", class_="mm-lbl"),
                     text(PAD + tw(f"{lab} · {len(gts)}", 12, True) + 10, y, why, class_="mm-small")]
            y += 8
            for t in gts:
                body.append(text(PAD, y + 10, short(t.get("task_id"), lw - 14, 11), class_="mm-small"))
                for j, s in enumerate("ab"):
                    e = t[s]
                    body.append(el("rect", title(f"{t.get('task_id')} · {run} · {(la, lb)[j]}: {e.get('outcome')} · "
                                                 f"{name_of('b-' + (e.get('band') or ''))}"),
                                   **side_mark(t, s, x=xa + j * cw + 2, y=y + 1, width=cw - 4, height=12, rx=3)))
                body.append(text(xa + 2 * cw + 16, y + 10, f"{LABEL.get(t['a'].get('outcome'), t['a'].get('outcome'))} → "
                                 f"{LABEL.get(t['b'].get('outcome'), t['b'].get('outcome'))}", class_="mm-small"))
                y += 16
    return doc("diffs", y + 14, "Tasks that flip between A and B",
               "Which tasks flip between the two sides? " + ", ".join(f"{sub[k][0].lower()}: {counts_[k]}" for k, _, _ in DIFF_GROUPS),
               body)


def render_all(cmp: dict) -> dict[str, str]:
    """{name: svg} for every comparison chart that applies, in CHARTS order."""
    out = {}
    for name in CHARTS:
        s = globals()[f"chart_{name}"](cmp)
        if s:
            out[name] = s
    return out
