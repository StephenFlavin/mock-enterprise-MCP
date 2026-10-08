"""`eval export <run> [<run> ...] --out results.csv`: one flat table of every graded task, for plotting and analysis.

One row per task per run (a budget grid gives one row per task per budget). Columns: identity (run, budget label, task_id,
kind, question_id, model, harness, judge), the verdict (outcome, passed, severity, trap_handled, categories as `;`-joined
text plus one 0/1 column per category), the metrics (cost_usd, judge_cost_usd, input_total / input / cache_read /
cache_creation / output tokens, wall_s, duration_s, tool_calls), the tool budget (tools, tokens, servers loaded) and every
task feature as `f_<name>` (lists `;`-joined). Filter and plot in any tool, e.g. failures of complex tasks by input tokens:
`df[df.f_complexity == "complex"]` against `input_total`.
"""
import csv
import json
from pathlib import Path

from .grade import read_jsonl
from .report import run_dirs
from .schema import CATEGORIES, modern


def rows_of(run: Path) -> list[dict]:
    tasks = {t["id"]: t for t in read_jsonl(run / "tasks.jsonl")}
    out = []
    for r in read_jsonl(run / "results.jsonl"):
        r = {**r, "outcome": modern(r.get("outcome")), "categories": [modern(c) for c in r.get("categories") or []]}
        t, tok, tb = tasks.get(r["task_id"], {}), r.get("tokens") or {}, r.get("tool_budget") or {}
        feats = r.get("features") or t.get("features") or {}
        row = {"run": run.parent.name if run.name.startswith("tokens-") else run.name, "budget": tb.get("label") or run.name,
               "task_id": r["task_id"], "kind": r.get("kind"), "question_id": r.get("question_id"), "model": r.get("model"),
               "harness": r.get("harness"), "judge": r.get("judge"), "outcome": r.get("outcome"), "passed": int(bool(r.get("passed"))),
               "severity": r.get("severity"), "trap_handled": "" if r.get("trap_handled") is None else int(r["trap_handled"]),
               "categories": ";".join(r.get("categories") or []),
               **{f"cat_{c}": int(c in (r.get("categories") or [])) for c in CATEGORIES},
               "cost_usd": r.get("cost_usd") or 0, "judge_cost_usd": r.get("judge_cost_usd") or 0,
               "input_total": tok.get("input_total", (tok.get("input") or 0) + (tok.get("cache_read") or 0) + (tok.get("cache_creation") or 0)),
               "input_uncached": tok.get("input") or 0, "cache_read": tok.get("cache_read") or 0,
               "cache_creation": tok.get("cache_creation") or 0, "output_tokens": tok.get("output") or 0,
               "wall_s": round((r.get("wall_ms") or r.get("duration_ms") or 0) / 1000, 2), "duration_s": round((r.get("duration_ms") or 0) / 1000, 2),
               "tool_calls": r.get("tool_calls") or 0, "tools_loaded": tb.get("tools"), "tool_tokens_loaded": tb.get("tokens"),
               "servers_loaded": tb.get("servers"), "strata": ";".join(r.get("strata") or [])}
        for k, v in sorted(feats.items()):
            row[f"f_{k}"] = ";".join(map(str, v)) if isinstance(v, (list, tuple)) else ("" if v is None else v)
        out.append(row)
    return out


def add_args(p):
    p.add_argument("runs", nargs="+", help="run folders (or grid parents); rows from all of them go in one table")
    p.add_argument("--out", default="results.csv", help="CSV path (default results.csv); .jsonl writes JSON lines instead")


def main(a):
    rows = [r for x in a.runs for rd in run_dirs(Path(x)) for r in rows_of(rd)]
    cols = list(dict.fromkeys(k for r in rows for k in r))
    out = Path(a.out)
    if out.suffix == ".jsonl":
        out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    else:
        with out.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, restval="")
            w.writeheader()
            w.writerows(rows)
    print(f"{out}: {len(rows)} rows x {len(cols)} columns")
    return 0
