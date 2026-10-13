"""Task tags: the labels a task carries for slicing results (strata plus a few features), and pass rates per tag for a
single report (REPORT tasks, or report rows) and for a comparison (COMPARE tasks, A against B on the same tasks).

Vocabulary, in this order (`tags_of`):
    <stratum>            every stratum the recipe matched (features.PRESETS: simple, short, long, complex, multi_system,
                         write, followups, multi_turn, arithmetic; or a recipe's own presets), plus `arithmetic` when the
                         `arithmetic` feature counts a fact got by arithmetic. The stratum `trap` is left out: it is the
                         same set as `kind:trap`.
    kind:<kind>          scenario, slice or trap
    complexity:<c>       the persona question's complexity tag (simple, moderate, complex)
    type:<TYPE>          the persona question's type (DIAGNOSE, DECIDE, FORECAST, MONITOR, RESEARCH)
    trap:<trap_type>     the trap's type (missing_tool, approval_flow, ...)

Tags whose tasks are exactly the same set (follow-ups and multi-turn always are) collapse into one row: the first in
vocabulary order keeps the row and lists the others as `aliases`. A row with fewer than MIN_N tasks is flagged `small`:
its rate moves a lot with one task. No model calls; reads only what the REPORT or COMPARE dict holds."""
import statistics
from collections import Counter

from .compare_data import mcnemar
from .schema import OUTCOMES, SEVERITY_BANDS, modern

MIN_N = 10   # fewer tasks than this: "small sample"
FAMILIES = ("stratum", "kind", "complexity", "type", "trap")
STRATA = ("simple", "short", "long", "complex", "multi_system", "write", "followups", "multi_turn", "arithmetic")
LABELS = {
    "simple": "simple", "short": "short prompt", "long": "long", "complex": "complex", "multi_system": "multi-system",
    "write": "writes", "followups": "follow-ups", "multi_turn": "multi-turn", "arithmetic": "arithmetic", "trap": "trap",
    "kind:scenario": "scenarios", "kind:slice": "slices", "kind:trap": "traps",
}
FAMILY_LABEL = {"complexity": "complexity", "type": "question", "trap": "trap"}
EFFORT = ("input_tokens", "tool_calls", "seconds", "cost_usd")
CHANGES = ("both_pass", "a_only", "b_only", "both_fail")


def family(tag: str) -> str:
    """The tag's family: stratum, kind, complexity, type or trap."""
    f = tag.split(":", 1)[0] if ":" in tag else "stratum"
    return f if f in FAMILIES else "stratum"


def label(tag: str) -> str:
    """Human label: `multi_system` → "multi-system", `type:DIAGNOSE` → "question: diagnose", `trap:missing_tool` →
    "trap: missing tool"."""
    if tag in LABELS:
        return LABELS[tag]
    f, _, v = tag.partition(":")
    if not v:
        return tag.replace("_", " ")
    return f"{FAMILY_LABEL.get(f, f)}: {v.lower().replace('_', ' ')}"


def _order(tag: str) -> tuple:
    f = family(tag)
    return FAMILIES.index(f), STRATA.index(tag) if tag in STRATA else len(STRATA), tag


def tags_of(t: dict) -> list[str]:
    """The tags of a REPORT task entry (or a report row, or anything with strata / features / kind / trap), in vocabulary
    order. A dict that already carries `tags` keeps them."""
    if t.get("tags") is not None:
        return sorted(dict.fromkeys(t["tags"]), key=_order)
    f = t.get("features") or {}
    out = [s for s in t.get("strata") or [] if s != "trap"]
    if (f.get("arithmetic") or 0) >= 1:
        out.append("arithmetic")
    kind = t.get("kind") or f.get("kind")
    tt = f.get("trap_type") or (t.get("trap") or {}).get("type")
    out += ([f"kind:{kind}"] if kind else []) + ([f"complexity:{f['complexity']}"] if f.get("complexity") else []) \
        + ([f"type:{f['type']}"] if f.get("type") else []) + ([f"trap:{tt}"] if tt else [])
    return sorted(dict.fromkeys(out), key=_order)


def _groups(items: list, tagf, idf) -> list[tuple[str, list[str], list]]:
    """[(tag, aliases, items)] in vocabulary order, tags with identical item sets collapsed into the first."""
    by = {}
    for x in items:
        for g in tagf(x):
            by.setdefault(g, []).append(x)
    out, seen = [], {}
    for g in sorted(by, key=_order):
        sig = frozenset(idf(x) for x in by[g])
        if sig in seen:
            out[seen[sig]][1].append(g)
            continue
        seen[sig] = len(out)
        out.append((g, [], by[g]))
    return out


def _band(t: dict) -> str:
    if t.get("band") in SEVERITY_BANDS:
        return t["band"]
    o = modern(t.get("outcome") or "")
    if o == "unsafe":
        return {"external_or_irreversible": "unsafe_external", "reversible": "unsafe_reversible"}.get(t.get("severity"), "unsafe_benign")
    return o if o in SEVERITY_BANDS else "honest_fail"


def _near(t: dict) -> bool:
    if "near_miss" in t:
        return bool(t["near_miss"])
    return not t.get("passed") and (modern(t.get("outcome") or "") == "partial" or (t.get("kind") == "trap" and t.get("trap_handled") is True))


def _eff(t: dict, k: str) -> float:
    e = t.get("effort")
    if e:
        return float(e.get(k) or 0)
    if k == "input_tokens":
        return float((t.get("tokens") or {}).get("input_total") or 0)
    if k == "seconds":
        return float(t.get("wall_ms") or t.get("duration_ms") or 0) / 1000
    return float(t.get(k) or 0)


def _rate(p: int, n: int) -> float:
    return round(p / n, 4) if n else 0.0


def _row(tag: str, aliases: list[str]) -> dict:
    return {"tag": tag, "label": label(tag), "family": family(tag), "aliases": aliases,
            "display": label(tag) + (f" (= {', '.join(label(a) for a in aliases)})" if aliases else "")}


def by_tag(tasks: list[dict]) -> list[dict]:
    """Per tag (vocabulary order), over the tasks of every run pooled: n, passed, pass_rate, outcomes, bands, near_miss,
    median effort, `small` (n < MIN_N), and `runs` (per-run n / passed / pass_rate, in first-seen run order).
    `passed` is the tasks' own flag, never recomputed."""
    rows = []
    runs = list(dict.fromkeys(str(t.get("run")) for t in tasks))
    for tag, aliases, ts in _groups(list(range(len(tasks))), lambda i: tags_of(tasks[i]), lambda i: i):
        ts = [tasks[i] for i in ts]
        n, p = len(ts), sum(bool(t.get("passed")) for t in ts)
        oc, bc = Counter(modern(t.get("outcome") or "") for t in ts), Counter(_band(t) for t in ts)
        per = [(run, [t for t in ts if str(t.get("run")) == run]) for run in runs]
        rows.append(_row(tag, aliases) | {
            "n": n, "passed": p, "pass_rate": _rate(p, n), "small": n < MIN_N,
            "outcomes": {o: oc[o] for o in OUTCOMES} | {o: k for o, k in oc.items() if o not in OUTCOMES},
            "bands": {b: bc[b] for b in SEVERITY_BANDS}, "near_miss": sum(_near(t) for t in ts),
            "median": {k: statistics.median(_eff(t, k) for t in ts) for k in EFFORT},
            "runs": [{"run": run, "n": len(x), "passed": sum(bool(t.get("passed")) for t in x),
                      "pass_rate": _rate(sum(bool(t.get("passed")) for t in x), len(x))} for run, x in per if x]})
    return rows


def compare_tasks(cmp: dict) -> list[dict]:
    """The COMPARE tasks, each with `tags`: its own when it carries tags / strata / features, else those of its entries in
    the embedded REPORTs (A's and B's tags joined; the same task normally has the same tags on both sides)."""
    idx = {(s, e.get("key")): e for s in "ab" for e in (cmp.get(s) or {}).get("tasks") or []}
    out = []
    for t in cmp.get("tasks") or []:
        if t.get("tags") is not None or t.get("strata") or t.get("features"):
            tg = tags_of(t)
        else:
            src = [idx.get((s, (t.get(s) or {}).get("key"))) for s in "ab"]
            tg = sorted({g for e in src if e for g in tags_of(e)} or tags_of(t), key=_order)
        out.append({**t, "tags": tg})
    return out


def _change(t: dict) -> str:
    if t.get("change") in CHANGES:
        return t["change"]
    a, b = bool(t["a"].get("passed")), bool(t["b"].get("passed"))
    return "both_pass" if a and b else "a_only" if a else "b_only" if b else "both_fail"


def by_tag_compare(cmp) -> list[dict]:
    """Per tag (vocabulary order) over the common tasks of every paired run pooled: n, A's and B's passed and pass rate,
    delta_pts (B − A in percentage points), head_to_head counts, the exact McNemar p on the tasks only one side passed,
    `significant` (p < 0.05), `small` (n < MIN_N) and per-run detail. Takes a COMPARE dict (tags resolved through its
    embedded REPORTs) or a list of COMPARE tasks that carry `tags`."""
    ts_all = compare_tasks(cmp) if isinstance(cmp, dict) else list(cmp)
    runs = list(dict.fromkeys(str(t.get("run")) for t in ts_all))
    rows = []
    for tag, aliases, idx in _groups(list(range(len(ts_all))), lambda i: tags_of(ts_all[i]), lambda i: i):
        ts = [ts_all[i] for i in idx]
        n, h = len(ts), Counter(_change(t) for t in ts)
        pa, pb = h["both_pass"] + h["a_only"], h["both_pass"] + h["b_only"]
        p = mcnemar(h["a_only"], h["b_only"])
        per = []
        for run in runs:
            x = [t for t in ts if str(t.get("run")) == run]
            if x:
                c = Counter(_change(t) for t in x)
                per.append({"run": run, "n": len(x), "a_passed": c["both_pass"] + c["a_only"],
                            "b_passed": c["both_pass"] + c["b_only"], "a_only": c["a_only"], "b_only": c["b_only"]})
        rows.append(_row(tag, aliases) | {
            "n": n, "a_passed": pa, "b_passed": pb, "a_rate": _rate(pa, n), "b_rate": _rate(pb, n),
            "delta_pts": round(100 * (pb - pa) / n, 1) if n else 0.0, "head_to_head": {k: h[k] for k in CHANGES},
            "mcnemar_p": round(p, 6), "significant": p < .05, "small": n < MIN_N, "runs": per})
    return rows


def md_report(rows: list[dict]) -> list[str]:
    """report.md's "By tag" section (lines) from by_tag rows; empty when there are none."""
    if not rows:
        return []
    L = ["## By tag", "", f"Tags slice the same tasks several ways (a task has several tags). Pooled over every run; "
         f"rows with fewer than {MIN_N} tasks are marked *small* (one task moves the rate a lot).", "",
         "| tag | tasks | pass rate | " + " | ".join({"over_cautious": "over-cautious"}.get(o, o.replace("_", " ")) for o in reversed(OUTCOMES)) + " | near misses |",
         "|" + "---|" * (4 + len(OUTCOMES))]
    for r in rows:
        L.append(f"| {r['display']}{' *small*' if r['small'] else ''} | {r['n']} | {100 * r['pass_rate']:.0f}% | "
                 + " | ".join(str(r["outcomes"].get(o) or "") for o in reversed(OUTCOMES)) + f" | {r['near_miss'] or ''} |")
    return L + [""]


def md_compare(rows: list[dict], la: str, lb: str) -> list[str]:
    """compare.md's "By tag" section (lines) from by_tag_compare rows; empty when there are none."""
    if not rows:
        return []
    L = ["## By tag", "", f"Pass rates on the common tasks of each tag, all runs pooled; a task has several tags. Δ is B minus A "
         f"in percentage points, p McNemar's exact test within the tag. Rows with fewer than {MIN_N} tasks are marked "
         "*small*: read their gap as a hint, not a finding.", "",
         f"| tag | tasks | {la} pass | {lb} pass | Δ pts | p | wins {la} | wins {lb} |", "|" + "---|" * 8]
    for r in rows:
        p = r["mcnemar_p"]
        L.append(f"| {r['display']}{' *small*' if r['small'] else ''} | {r['n']} | {100 * r['a_rate']:.1f}% | "
                 f"{100 * r['b_rate']:.1f}% | {r['delta_pts']:+.1f} | {'**' if r['significant'] else ''}{p:.3g}"
                 f"{'**' if r['significant'] else ''} | {r['head_to_head']['a_only']} | {r['head_to_head']['b_only']} |")
    return L + [""]
