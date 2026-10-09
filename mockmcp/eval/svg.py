"""Small SVG toolkit for the report charts: an element builder, scales, ticks, number formats, a beeswarm and an
exact-sum stack, plus the theme (PALETTE) and the shared stylesheet (STYLE).

Colours live only in CSS custom properties on `.mm-chart`, light by default, dark under `prefers-color-scheme`, and a
`data-theme="light|dark"` on `<html>` or on the `<svg>` itself wins over both. Marks never carry inline colours: they
take classes (`f-o-<outcome>`, `f-b-<band>`, `f-pass`, `f-fail`, or the per-task `mm-t o-… b-… pf-…`) that STYLE maps
to the variables, so one SVG can be re-themed and re-viewed by setting attributes."""
import math
from html import escape

from .schema import OUTCOMES, SEVERITY_BANDS

FONT = 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'

# Checked with the dataviz palette validator (OKLab ΔE, Machado CVD simulation): in stacking order (pass … unsafe) every
# adjacent outcome pair clears ΔE 15 for normal vision and 8 under protan/deutan in both themes, every colour sits in the
# theme's lightness band with chroma >= 0.1, and the three unsafe bands form a one-hue ordinal ramp (worst darkest in
# light, brightest in dark). Every mark colour is >= 3:1 against --mm-bg (tests/test_eval_charts.py keeps it so).
_LIGHT = {"bg": "#ffffff", "surface": "#f6f7f9", "fg": "#1d2025", "muted": "#5b6472", "grid": "#e6e8ec", "axis": "#c9cdd4",
          "o-pass": "#008966", "o-honest_fail": "#4a71b1", "o-partial": "#a97000", "o-over_cautious": "#7b57c8",
          "o-fabricated": "#d54600", "o-unsafe": "#a8004c",
          "b-unsafe_external": "#701030", "b-unsafe_reversible": "#a8004c", "b-unsafe_benign": "#c06099",
          "pass": "#008966", "fail": "#c2410c"}
_DARK = {"bg": "#0f1217", "surface": "#171b22", "fg": "#e8eaee", "muted": "#9aa3b2", "grid": "#252a33", "axis": "#3a414d",
         "o-pass": "#00ae83", "o-honest_fail": "#6295d4", "o-partial": "#c68400", "o-over_cautious": "#9a7de3",
         "o-fabricated": "#e16c10", "o-unsafe": "#f1498d",
         "b-unsafe_external": "#fc85ad", "b-unsafe_reversible": "#f1498d", "b-unsafe_benign": "#b54879",
         "pass": "#00ae83", "fail": "#e06623"}
MARKS = [f"o-{o}" for o in OUTCOMES] + [f"b-{b}" for b in SEVERITY_BANDS] + ["pass", "fail"]


def _full(t: dict) -> dict:
    """Theme dict with every band (the non-unsafe bands share their outcome's colour) and an ink for text on each mark."""
    t = dict(t)
    for b in SEVERITY_BANDS:
        t.setdefault(f"b-{b}", t.get(f"o-{b}"))
    t["near"] = t["o-partial"]
    for k in MARKS:
        t[f"ink-{k}"] = max(("#ffffff", "#111418"), key=lambda ink: contrast(ink, t[k]))
    return t


def _lum(h: str) -> float:
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = (x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """WCAG contrast ratio of two #rrggbb colours."""
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


PALETTE = {"light": _full(_LIGHT), "dark": _full(_DARK)}


def _vars(theme: str) -> str:
    return "".join(f"--mm-{k}:{v};" for k, v in PALETTE[theme].items()) + f"color-scheme:{theme};"


def theme_css() -> str:
    """The theme variables for `.mm-chart` in both themes. Specificity: forced (data-theme on the svg or on <html>) >
    prefers-color-scheme > the light default."""
    light, dark = _vars("light"), _vars("dark")
    return (f".mm-chart{{{light}--mm-font:{FONT};}}\n"
            f"@media (prefers-color-scheme: dark){{.mm-chart:not([data-theme=light]){{{dark}}}}}\n"
            f":root[data-theme=light] .mm-chart:not([data-theme=dark]),.mm-chart.mm-chart[data-theme=light]{{{light}}}\n"
            f":root[data-theme=dark] .mm-chart:not([data-theme=light]),.mm-chart.mm-chart[data-theme=dark]{{{dark}}}\n")


VIEWS = ("binary", "outcome", "severity")
METRICS = ("input_tokens", "seconds", "tool_calls", "cost_usd")


def _rules() -> str:
    fills = [f".mm-chart .f-{k}{{fill:var(--mm-{k})}}.mm-chart .s-{k}{{stroke:var(--mm-{k})}}"
             f".mm-chart .i-{k}{{fill:var(--mm-ink-{k})}}" for k in MARKS]
    per_task = ([f".mm-chart[data-view=outcome] .mm-t.o-{o}{{fill:var(--mm-o-{o})}}" for o in OUTCOMES]
                + [f".mm-chart[data-view=severity] .mm-t.b-{b}{{fill:var(--mm-b-{b})}}" for b in SEVERITY_BANDS]
                + [".mm-chart[data-view=binary] .mm-t.pf-pass{fill:var(--mm-pass)}",
                   ".mm-chart[data-view=binary] .mm-t.pf-fail{fill:var(--mm-fail)}"])
    views = [f".mm-chart[data-view={v}] .mm-v-{v}{{display:inline}}" for v in VIEWS]
    metrics = [f".mm-chart[data-metric={m}] .mm-m-{m}{{display:inline}}" for m in METRICS]
    return "\n".join(fills + per_task + views + metrics)


STYLE = theme_css() + """.mm-chart{font-family:var(--mm-font);font-size:12px;fill:var(--mm-fg)}
.mm-chart .mm-num,.mm-chart .mm-tick,.mm-chart .mm-in{font-variant-numeric:tabular-nums}
.mm-chart text{fill:var(--mm-fg);dominant-baseline:auto}
.mm-chart .mm-bg{fill:var(--mm-bg)}
.mm-chart .mm-h1{font-size:15px;font-weight:600;letter-spacing:-.01em}
.mm-chart .mm-sub{fill:var(--mm-muted);font-size:12px}
.mm-chart .mm-lbl{font-size:12px;font-weight:500}
.mm-chart .mm-num{font-size:12px;font-weight:600}
.mm-chart .mm-small,.mm-chart .mm-tick{font-size:11px;fill:var(--mm-muted)}
.mm-chart .mm-muted{fill:var(--mm-muted)}
.mm-chart .mm-in{font-size:11px;font-weight:600;pointer-events:none}
.mm-chart .mm-grid{stroke:var(--mm-grid);stroke-width:1;shape-rendering:crispEdges}
.mm-chart .mm-axis{stroke:var(--mm-axis);stroke-width:1;shape-rendering:crispEdges}
.mm-chart .mm-rule{stroke:var(--mm-fg);stroke-width:1.5;stroke-dasharray:3 3;fill:none}
.mm-chart .mm-tickmark{stroke:var(--mm-fg);stroke-width:2;stroke-linecap:round}
.mm-chart .mm-zone{fill:var(--mm-fg);opacity:.06}
.mm-chart .mm-track{fill:var(--mm-surface)}
.mm-chart .mm-seg{stroke:var(--mm-bg);stroke-width:2px}
.mm-chart .mm-dot{stroke:var(--mm-bg);stroke-width:1px}
.mm-chart .mm-line{fill:none;stroke:var(--mm-fg);stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
.mm-chart .mm-pt{fill:var(--mm-fg);stroke:var(--mm-bg);stroke-width:2px}
.mm-chart .mm-halo{paint-order:stroke;stroke:var(--mm-bg);stroke-width:3px;stroke-linejoin:round}
.mm-chart .mm-rib{opacity:.35}
.mm-chart .mm-rib:hover{opacity:.6}
.mm-chart .mm-t{fill:var(--mm-muted)}
.mm-chart .mm-t:hover{stroke:var(--mm-fg);stroke-width:1.5px}
.mm-chart .mm-key{fill:var(--mm-muted)}
.mm-chart .mm-hole{fill:var(--mm-bg);pointer-events:none}
.mm-chart .mm-v,.mm-chart .mm-m{display:none}
.mm-chart .mm-dim{opacity:.12}
""" + _rules() + "\n"


def esc(s) -> str:
    """Text or attribute value escaped for XML (&, <, >, quotes)."""
    return escape(str(s), quote=True)


def num(v) -> str:
    """A coordinate rounded to 0.1, without a trailing .0."""
    v = round(float(v), 1)
    return str(int(v)) if v == int(v) else f"{v:.1f}"


def el(tag: str, children=(), **attrs) -> str:
    """An element. `class_` gives `class`; other underscores become hyphens; None and False attributes are dropped;
    numbers are rounded by `num`. String children are trusted markup (escape text with `esc` or use `text`)."""
    a = "".join(f' {k.rstrip("_").replace("_", "-")}="{num(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else esc(v)}"'
                for k, v in attrs.items() if v is not None and v is not False)
    body = children if isinstance(children, str) else "".join(c for c in children if c)
    return f"<{tag}{a}>{body}</{tag}>" if body else f"<{tag}{a}/>"


def text(x, y, s, **attrs) -> str:
    """A <text> element with escaped content."""
    return el("text", esc(s), x=x, y=y, **attrs)


def title(s) -> str:
    """A <title> tooltip child."""
    return el("title", esc(s))


def tw(s, size: float = 12, bold: bool = False) -> float:
    """Approximate rendered width of `s` in px (system sans; good enough to decide whether a label fits)."""
    w = sum(.36 if c in "il.,:;|!'1 ()" else .62 if c.isdigit() else .82 if c in "mwMW%@" else .56 for c in str(s))
    return w * size * (1.05 if bold else 1)


def linear(d0: float, d1: float, r0: float, r1: float):
    """A linear scale from domain [d0, d1] to range [r0, r1]."""
    k = (r1 - r0) / ((d1 - d0) or 1)
    return lambda v: r0 + (v - d0) * k


def log(d0: float, d1: float, r0: float, r1: float):
    """A log10 scale; values <= d0 clamp to r0 (so zeros sit on the left edge)."""
    d0 = max(d0, 1e-9)
    a, b = math.log10(d0), math.log10(max(d1, d0 * 10))
    k = (r1 - r0) / ((b - a) or 1)
    return lambda v: r0 + (math.log10(max(v, d0)) - a) * k


def nice_step(span: float, n: int) -> float:
    raw = span / max(n, 1)
    mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
    return next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)


def nice_ticks(lo: float, hi: float, n: int = 5) -> list[float]:
    """Round tick values covering [lo, hi], about n of them (the last tick is >= hi)."""
    if hi <= lo:
        hi = lo + 1
    s = nice_step(hi - lo, n)
    t, out = math.floor(lo / s) * s, []
    while t < hi + s * 0.999:
        out.append(round(t, 10))
        if t >= hi:
            break
        t += s
    return out


def log_ticks(lo: float, hi: float) -> list[float]:
    """Ticks for a log scale: 1-2-5 per decade when it spans few decades, powers of ten otherwise."""
    a, b = math.floor(math.log10(max(lo, 1e-9))), math.ceil(math.log10(max(hi, lo * 10)))
    mults = (1, 2, 5) if b - a <= 3 else (1,)
    return [m * 10 ** e for e in range(a, b + 1) for m in mults if lo * .9999 <= m * 10 ** e <= hi * 1.0001]


def log_bounds(lo: float, hi: float) -> tuple[float, float]:
    """The nearest 1-2-5 values at or below lo and at or above hi (a snug log domain)."""
    steps = lambda e: [m * 10 ** e for m in (1, 2, 5)]
    e0, e1 = math.floor(math.log10(lo)), math.floor(math.log10(hi))
    return (max(v for v in steps(e0) if v <= lo * 1.0001), min(v for v in steps(e1) + [10 ** (e1 + 1)] if v >= hi * .9999))


def fmt(v, unit: str = "n") -> str:
    """Compact numbers: tokens 12.3k / 1.2M, usd $0.04 / $12, s 51 s / 4.2 min, pct 42%, n 1,234."""
    if v is None:
        return "–"
    if unit == "usd":
        return "$0" if v == 0 else f"${v:,.2f}" if v >= .1 else f"${v:.3f}" if v >= .001 else "<$0.001"
    if unit == "s":
        return f"{v:.0f} s" if v < 90 else f"{v / 60:.1f} min" if v < 5400 else f"{v / 3600:.1f} h"
    if unit == "pct":
        return f"{v * 100:.0f}%"
    if unit == "tokens":
        a = abs(v)
        return f"{v / 1e6:.1f}M" if a >= 1e6 else f"{v / 1e3:.0f}k" if a >= 1e5 else f"{v / 1e3:.1f}k" if a >= 1e3 else f"{v:.0f}"
    return f"{v:,.0f}" if float(v).is_integer() or abs(v) >= 100 else f"{v:,.1f}"


def beeswarm(xs: list[float], r: float, gap: float = 0.6, limit: float | None = None) -> list[float]:
    """Vertical offsets so circles of radius r at xs do not overlap: in x order, each takes the free offset nearest 0
    (0, +s, -s, +2s, … with s = r/2). With `limit`, offsets stay within ±limit and a dot with no free place there takes
    the least crowded one (so dense rows overlap rather than grow without bound). Deterministic; ties keep input order."""
    d, step = 2 * r + gap, r / 2
    order = sorted(range(len(xs)), key=lambda i: (xs[i], i))
    ys, placed = [0.0] * len(xs), []
    cands = lambda k: (k + 1) // 2 * step * (1 if k % 2 else -1)
    for i in order:
        near = [j for j in placed if xs[i] - xs[j] < d]
        k, best = 0, None
        while True:
            y = cands(k)
            if limit is not None and abs(y) > limit:
                y = min((cands(q) for q in range(k)), key=lambda c: (-min(((xs[i] - xs[j]) ** 2 + (c - ys[j]) ** 2 for j in near),
                                                                          default=d * d), abs(c)))
                break
            if all((xs[i] - xs[j]) ** 2 + (y - ys[j]) ** 2 >= d * d for j in near):
                break
            k += 1
        ys[i] = y
        placed = near + [i]
    return ys


def stack(shares: list[float], width: float, unit: float = 0.1) -> list[float]:
    """Segment widths for shares (any non-negative weights) that add up to `width` exactly, rounded to `unit` by the
    largest-remainder method."""
    tot = sum(shares)
    if tot <= 0:
        return [0.0] * len(shares)
    n = round(width / unit)
    raw = [s / tot * n for s in shares]
    base = [math.floor(x) for x in raw]
    for i in sorted(range(len(raw)), key=lambda i: (-(raw[i] - base[i]), i))[:n - sum(base)]:
        base[i] += 1
    return [round(b * unit, 6) for b in base]


def bar(x, y, w, h, r: float = 3, **attrs) -> str:
    """A rect with rounded corners (r capped to fit)."""
    r = min(r, w / 2, h / 2) if w > 0 and h > 0 else 0
    return el("rect", x=x, y=y, width=max(w, 0), height=max(h, 0), rx=r or None, **attrs)


def doc(name: str, w: float, h: float, head: str, desc: str, body: list[str], **attrs) -> str:
    """A standalone chart: root <svg> with the contract attributes, <title>, <desc>, the stylesheet and a background."""
    return el("svg", [el("title", esc(head), id=f"{name}-t"), el("desc", esc(desc), id=f"{name}-d"),
                      el("style", STYLE), el("rect", class_="mm-bg", x=0, y=0, width=w, height=h)] + body,
              xmlns="http://www.w3.org/2000/svg", class_=f"mm-chart mm-{name}", data_chart=name, data_view="outcome",
              role="img", aria_labelledby=f"{name}-t {name}-d", viewBox=f"0 0 {num(w)} {num(h)}", width="100%",
              **attrs) + "\n"
