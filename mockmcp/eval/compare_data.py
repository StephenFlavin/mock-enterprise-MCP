"""The data behind compare.json: two REPORTs (report_data.build) side by side, paired by run and task, with per-run
pass rates, head-to-head counts, an exact McNemar p, outcome and band transitions, effort deltas and ratios, and one
entry per common task. No model calls; works only on what the two REPORTs hold.

Pairing rule (the same in `pair_runs`, on rows, and in `build`, on REPORTs): runs pair by name (a grid's tokens-0 with
the other grid's tokens-0); when each side holds exactly one run they pair whatever their names, under the common name
or "run" when the names differ. Runs on one side only are listed as unpaired and left out. Within a paired run, tasks
pair by task_id; tasks on one side only are counted (`only_a`, `only_b`) and never mixed into any figure."""
import math
import os
import statistics
from collections import Counter
from pathlib import Path

from .schema import OUTCOMES, SEVERITY_BANDS

COMPARE_VERSION = 1
EFFORT_KEYS = ("cost_usd", "input_tokens", "seconds", "tool_calls")
SIDE_TASK_KEYS = ("key", "outcome", "band", "band_rank", "passed", "near_miss", "severity", "categories", "trap_handled",
                  "judge", "effort", "calls", "notes")
ROUND = {"cost_usd": 6, "input_tokens": 0, "output_tokens": 0, "seconds": 3, "tool_calls": 0}


def _pairing(a_names: list[str], b_names: list[str]) -> tuple[list[tuple[str, str, str]], dict]:
    """[(paired name, A's run name, B's run name)] in A's order, plus the unpaired run names of each side."""
    if len(a_names) == 1 and len(b_names) == 1:
        a, b = a_names[0], b_names[0]
        return [(a if a == b else "run", a, b)], {"only_a_runs": [], "only_b_runs": []}
    common = [n for n in a_names if n in b_names]
    return [(n, n, n) for n in common], {"only_a_runs": [n for n in a_names if n not in common],
                                         "only_b_runs": [n for n in b_names if n not in common]}


def pair_runs(a_rows: list[dict], b_rows: list[dict]) -> tuple[list[tuple[str, list, list]], dict]:
    """Pair two sides' rows (report.load_run) by run: [(run name, A's rows of it, B's rows of it)] in sorted name order,
    and {"only_a_runs", "only_b_runs"}. Two single runs pair whatever their names (named by the common name or "run");
    rows are returned unchanged (their `run` keeps the folder name)."""
    names = lambda rows: sorted({r["run"] for r in rows})
    pairs, unpaired = _pairing(names(a_rows), names(b_rows))
    return [(n, [r for r in a_rows if r["run"] == a], [r for r in b_rows if r["run"] == b]) for n, a, b in pairs], unpaired


def mcnemar(a_only: int, b_only: int) -> float:
    """Exact two-sided McNemar p: binomial(n = a_only + b_only, 1/2) on the discordant pairs; 1.0 when there are none."""
    n, k = a_only + b_only, min(a_only, b_only)
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def _ordered(counter: Counter, order: list[str]) -> list[tuple[str, str]]:
    idx = lambda x: (order.index(x), x) if x in order else (len(order), x)
    return sorted(counter, key=lambda ft: (idx(ft[0]), idx(ft[1])))


def _transitions(pairs: list[tuple[dict, dict]], field: str, order: list[str]) -> list[dict]:
    c = Counter((a[field], b[field]) for a, b in pairs)
    return [{"from": f, "to": t, "n": c[f, t]} for f, t in _ordered(c, order) if c[f, t]]


def _side(es: list[dict]) -> dict:
    """One side's figures over the common tasks of a run (or of all runs)."""
    n, passed = len(es), sum(e["passed"] for e in es)
    oc, bc = Counter(e["outcome"] for e in es), Counter(e["band"] for e in es)
    traps = [e for e in es if e["kind"] == "trap"]
    tot = {k: round(sum(e["effort"].get(k) or 0 for e in es), ROUND[k]) for k in EFFORT_KEYS + ("output_tokens",)}
    med = {k: round(statistics.median([e["effort"].get(k) or 0 for e in es]), ROUND[k] or 1) if es else 0 for k in EFFORT_KEYS}
    return {"tasks": n, "passed": passed, "pass_rate": round(passed / n, 4) if n else 0.0,
            "outcomes": {o: oc[o] for o in OUTCOMES} | {o: k for o, k in oc.items() if o not in OUTCOMES},
            "bands": {b: bc[b] for b in SEVERITY_BANDS}, "near_miss": sum(e["near_miss"] for e in es),
            **{k: int(v) if not ROUND[k] else v for k, v in tot.items()}, "median": med,
            "cost_per_pass_usd": round(tot["cost_usd"] / passed, 6) if passed else None,
            "trap_handled": [sum(e["trap_handled"] is True for e in traps), sum(e["trap_handled"] is not None for e in traps)]}


def _run_entry(run: str, budget, pairs: list[tuple[dict, dict]], only_a: int, only_b: int) -> dict:
    a, b = _side([p[0] for p in pairs]), _side([p[1] for p in pairs])
    h2h = Counter(_change(x, y) for x, y in pairs)
    h2h = {k: h2h[k] for k in ("both_pass", "a_only", "b_only", "both_fail")}
    return {"run": run, "budget": budget, "common": len(pairs), "only_a": only_a, "only_b": only_b, "a": a, "b": b,
            "delta": {"pass_rate": round(b["pass_rate"] - a["pass_rate"], 4)}
            | {k: round(b[k] - a[k], ROUND[k]) for k in EFFORT_KEYS},
            "ratio": {k: (round(b[k] / a[k], 4) if a[k] else None) for k in EFFORT_KEYS},
            "head_to_head": h2h, "mcnemar_p": round(mcnemar(h2h["a_only"], h2h["b_only"]), 6),
            "transitions": _transitions(pairs, "outcome", OUTCOMES),
            "band_transitions": _transitions(pairs, "band", SEVERITY_BANDS)}


def _change(a: dict, b: dict) -> str:
    return {(True, True): "both_pass", (True, False): "a_only", (False, True): "b_only", (False, False): "both_fail"}[
        bool(a["passed"]), bool(b["passed"])]


def _files(files: dict, root: Path | None, out: Path | None) -> dict:
    """A REPORT task's file links, rewritten relative to the compare output dir when both the side's root and `out` are known."""
    if out is None or root is None:
        return dict(files)
    return {k: os.path.relpath(Path(root) / p, out) for k, p in files.items()}   # an absolute p stays absolute under /


def _side_task(e: dict, root, out) -> dict:
    return {k: e.get(k) for k in SIDE_TASK_KEYS} | {"files": _files(e.get("files") or {}, root, out)}


def build(a_report: dict, b_report: dict, labels: list[str], *, out: Path | None = None,
          sources: list | None = None) -> dict:
    """COMPARE (compare.json) from two REPORTs (report_data.build output, embedded unchanged as `a` and `b`).

    Runs pair by `REPORT.runs[].run` (see the module docstring; two single runs pair whatever their names), ordered as in
    A's REPORT. Side figures cover the common tasks of each paired run only. `passed` is copied from the REPORT tasks,
    never recomputed. `sources` are the two run folders (as given; default the REPORT titles); with both `sources` and
    `out`, each task's file links are rewritten relative to `out`, otherwise kept as the REPORTs hold them.
    Raises ValueError when the two REPORTs were built from different verdict files (never mix judges)."""
    if len(labels) != 2:
        raise ValueError(f"need two labels, got {labels!r}")
    if a_report.get("verdict_source") != b_report.get("verdict_source"):
        raise ValueError(f"verdict sources differ: {a_report.get('verdict_source')} vs {b_report.get('verdict_source')}")
    roots = [Path(s) for s in sources] if sources else [None, None]
    out = Path(out) if out is not None else None
    pairs, unpaired = _pairing([r["run"] for r in a_report["runs"]], [r["run"] for r in b_report["runs"]])
    budget = {r["run"]: r.get("budget") for r in a_report["runs"]}
    runs, tasks, everything = [], [], []
    for name, ra, rb in pairs:
        ta = {e["task_id"]: e for e in a_report["tasks"] if e["run"] == ra}
        tb = {e["task_id"]: e for e in b_report["tasks"] if e["run"] == rb}
        common = sorted(set(ta) & set(tb))
        ps = [(ta[t], tb[t]) for t in common]
        everything += ps
        runs.append(_run_entry(name, budget[ra], ps, len(set(ta) - set(tb)), len(set(tb) - set(ta))))
        for ea, eb in ps:
            shift = "same" if ea["band_rank"] == eb["band_rank"] else "better" if eb["band_rank"] > ea["band_rank"] else "worse"
            tasks.append({"key": f"c{len(tasks)}", "task_id": ea["task_id"], "run": name, "budget": budget[ra],
                          "kind": ea["kind"], "trap": ea.get("trap"), "change": _change(ea, eb), "shift": shift,
                          "a": _side_task(ea, roots[0], out), "b": _side_task(eb, roots[1], out)})
    allrun = _run_entry("all", None, everything, sum(r["only_a"] for r in runs), sum(r["only_b"] for r in runs))
    return {"compare_version": COMPARE_VERSION, "labels": list(labels),
            "sources": [str(s) for s in sources] if sources else [a_report.get("title"), b_report.get("title")],
            "verdict_source": a_report.get("verdict_source"), "unpaired": unpaired, "a": a_report, "b": b_report,
            "runs": runs, "all": allrun, "tasks": tasks}
