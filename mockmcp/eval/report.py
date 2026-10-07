"""`eval report`: report.md that leads with failure categories, plus results.jsonl (if missing) and summary.json.

Accepts a run folder or a parent folder holding several runs (budget grid sub-runs), which are compared side by side."""
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from .grade import read_json, read_jsonl, result_for, run_dirs
from .schema import CATEGORIES, OUTCOMES


def add_args(p):
    p.add_argument("run_dir", type=Path)


def load_run(rd: Path) -> list[dict]:
    """Results for one run, each with its task, verdict and run label attached (results.jsonl is rebuilt from judge.json if missing)."""
    tasks = {t["id"]: t for t in read_jsonl(rd / "tasks.jsonl")}
    results = {r["task_id"]: r for r in read_jsonl(rd / "results.jsonl")}
    recipe = (yaml.safe_load((rd / "recipe.yaml").read_text()) if (rd / "recipe.yaml").exists() else None) or {}
    strat = (recipe.get("tools") or {}).get("distractors") or recipe.get("distractors", "n/a")
    strat = strat.get("strategy", "n/a") if isinstance(strat, dict) else strat
    toks = [t["tool_budget"]["tokens"] for t in tasks.values() if (t.get("tool_budget") or {}).get("tokens")]
    budget = f"~{round(statistics.median(toks) / 1000)}k tokens" if toks else "n/a"
    out, rebuilt = [], not results
    for tid, t in tasks.items():
        v = (read_json(rd / tid / "judge.json", {}) or {}).get("verdict")
        r = results.get(tid) or (result_for(rd / tid, t, v, rd) if v else None)
        if r:
            out.append({**r, "task": t, "verdict": v or {}, "run": rd.name, "budget": budget,
                        "strategy": t.get("tool_budget", {}).get("strategy") or strat, "dir": str(rd / tid)})
    if rebuilt and out:
        (rd / "results.jsonl").write_text("".join(json.dumps({k: r[k] for k in r if k not in ("task", "verdict", "run", "budget", "strategy", "dir")}) + "\n" for r in out))
    return out


def pct(n, d) -> str:
    return f"{n}/{d} ({100 * n / d:.0f}%)" if d else "0/0"


def table(head: list[str], rows: list[list]) -> list[str]:
    return ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows] + [""]


def cross(rs: list[dict], keyf, cats: list[str]) -> list[str]:
    """category x group table: count of tasks in the group carrying the category, plus group size and pass rate."""
    groups = defaultdict(list)
    for r in rs:
        for k in keyf(r):
            groups[k].append(r)
    keys = sorted(groups)
    rows = [[c] + [sum(c in r["categories"] for r in groups[k]) or "" for k in keys] for c in cats]
    rows.append(["**tasks (pass rate)**"] + [f"{len(groups[k])} ({100 * sum(r['passed'] for r in groups[k]) / len(groups[k]):.0f}%)" for k in keys])
    return table(["category"] + keys, rows)


def trap_tables(traps: list[dict]) -> tuple[list[str], dict]:
    """Trap outcomes by type x tier and by type x trap turn (0 = the first turn, 'later' = the trap shows up after answerable turns)."""
    def tier(r):
        return (r["task"].get("trap") or {}).get("tier") or "(none)"

    def when(r):
        return "turn 0" if ((r["task"].get("trap") or {}).get("trap_turn") or 0) == 0 else "later turn"

    L, data = [], {}
    for title, keyf, name in (("type and tier", lambda r: (r["task"]["trap"]["type"], tier(r)), "by_type_tier"),
                              ("type and trap turn", lambda r: (r["task"]["trap"]["type"], when(r)), "by_type_trap_turn")):
        g = defaultdict(list)
        for r in traps:
            g[keyf(r)].append(r)
        rows = [[ty, ti] + [sum(r["outcome"] == o for r in g[(ty, ti)]) or "" for o in OUTCOMES] + [len(g[(ty, ti)]), pct(sum(r["passed"] for r in g[(ty, ti)]), len(g[(ty, ti)]))]
                for ty, ti in sorted(g)]
        L += [f"## Trap outcomes by {title}", ""] + table(["type", title.split(" and ")[1]] + OUTCOMES + ["total", "passed"], rows)
        data[name] = {f"{ty}/{ti}": {"n": len(v), "passed": sum(r["passed"] for r in v), "outcomes": dict(Counter(r["outcome"] for r in v))} for (ty, ti), v in sorted(g.items())}
    return L, data


def offending(r: dict) -> str:
    v = r["verdict"]
    bad = [a for a in v.get("actions", []) if not a.get("justified", True)]
    if bad:
        return f"call `{bad[0]['tool']}` (turn {bad[0].get('turn')}): {bad[0].get('why', '')}"
    if v.get("unsupported_claims"):
        return f"claim: {v['unsupported_claims'][0]}"
    return ""


def render(rs: list[dict], root: Path) -> tuple[str, dict]:
    n = len(rs)
    failed = [r for r in rs if not r["passed"]]
    cats = Counter(c for r in failed for c in r["categories"])
    traps = [r for r in rs if r["kind"] == "trap"]
    unsafe = [r for r in rs if r["outcome"] == "unsafe"]
    halluc = [r for r in rs if r["outcome"] == "hallucinated"]
    honest = [r for r in failed if r["outcome"] == "honest_fail"]
    prov = sum(bool(r["verdict"].get("provisional")) for r in rs)
    cost, jcost = sum(r["cost_usd"] for r in rs), sum(r.get("judge_cost_usd") or 0 for r in rs)
    tok = {k: sum(r["tokens"].get(k, 0) for r in rs) for k in ("input", "output", "cache_read")}
    models = ", ".join(sorted({r["model"] for r in rs}))
    judges = ", ".join(sorted({f"{r['verdict'].get('judge', {}).get('backend', '?')} {r['verdict'].get('judge', {}).get('model', '')}".strip() for r in rs}))
    sev = Counter(r["severity"] for r in unsafe)
    L = [f"# Eval report: {root.name}", ""]
    if prov:
        L += [f"> {prov}/{n} verdicts are PROVISIONAL (rules over deterministic checks, no judge). Re-run `eval grade` with a judge.", ""]
    L += ["## Headline", ""]
    L += table(["metric", "value"], [
        ["model / harness", f"{models} / {', '.join(sorted({r['harness'] for r in rs}))}"], ["judge", judges],
        ["tasks", n], ["pass rate", pct(n - len(failed), n)],
        ["unsafe rate", pct(len(unsafe), n) + (" by severity: " + ", ".join(f"{k} {v}" for k, v in sev.items()) if unsafe else "")],
        ["hallucination rate", pct(len(halluc), n)], ["honest-fail share of failures", pct(len(honest), len(failed))],
        ["trap pass rate", pct(sum(r["passed"] for r in traps), len(traps)) if traps else "no traps"],
        ["cost (model / judge)", f"${cost:.2f} / ${jcost:.2f}"],
        ["tokens (in / out / cache read)", f"{tok['input']:,} / {tok['output']:,} / {tok['cache_read']:,}"],
        ["tool calls", sum(r["tool_calls"] for r in rs)]])
    L += ["## Failures by category", ""]
    if cats:
        L += table(["category", "tasks", "% of tasks", "examples"], [
            [c, k, f"{100 * k / n:.0f}%", ", ".join(f"`{r['task_id']}`" for r in [x for x in failed if c in x["categories"]][:3])]
            for c, k in sorted(cats.items(), key=lambda kv: (-kv[1], CATEGORIES.index(kv[0])))])
    else:
        L += ["No failed tasks.", ""]
    used = [c for c in CATEGORIES if c in cats]
    if used:
        L += ["## Categories by stratum", ""] + cross(rs, lambda r: r["strata"] or ["(none)"], used)
        runs = sorted({r["run"] for r in rs})
        if len(runs) > 1:
            order = {run: next(r["budget"] for r in rs if r["run"] == run) for run in runs}
            L += ["## Categories by tool budget", ""] + cross(rs, lambda r: [f"{order[r['run']]} ({r['run']})"], used)
        else:
            L += ["## Categories by tool budget", ""] + cross(rs, lambda r: [r["budget"] + f" ({r['run']})"], used)
        L += ["## Categories by distractor strategy", ""] + cross(rs, lambda r: [str(r["strategy"])], used)
    for title, keyf in (("kind", lambda r: [r["kind"]]), ("stratum", lambda r: r["strata"] or ["(none)"])):
        g = defaultdict(Counter)
        for r in rs:
            for k in keyf(r):
                g[k][r["outcome"]] += 1
        L += [f"## Outcomes by {title}", ""] + table([title] + OUTCOMES + ["total"], [[k] + [g[k][o] or "" for o in OUTCOMES] + [sum(g[k].values())] for k in sorted(g)])
    trap_data = {}
    if traps:
        tl, trap_data = trap_tables(traps)
        L += tl
    L += ["## Failed tasks", ""]
    for r in sorted(failed, key=lambda r: (OUTCOMES.index(r["outcome"]) if r["outcome"] in OUTCOMES else 99, r["task_id"])):
        v = r["verdict"]
        rel = Path(r["dir"]).relative_to(root) if Path(r["dir"]).is_relative_to(root) else Path(r["dir"])
        links = " ".join(f"[{f}]({rel / f})" for f in ("answers.json", "trace.jsonl", "checks.json", "judge.json"))
        L += [f"### `{r['task_id']}`: {r['outcome']}", "",
              f"- categories: {', '.join(r['categories']) or '-'}; severity: {r['severity']}; run: {r['run']}; judge confidence: {v.get('confidence', '?')}",
              f"- {v.get('rationale', '').strip()}"] + ([f"- offending: {o}"] if (o := offending(r)) else []) + [f"- files: {links}", ""]
    summary = {"n": n, "passed": n - len(failed), "pass_rate": (n - len(failed)) / n if n else 0, "unsafe": len(unsafe),
               "unsafe_by_severity": dict(sev), "hallucinated": len(halluc), "honest_fail_failures": len(honest),
               "trap_pass_rate": (sum(r["passed"] for r in traps) / len(traps)) if traps else None, "categories": dict(cats),
               "outcomes": dict(Counter(r["outcome"] for r in rs)), "cost_usd": round(cost, 4), "judge_cost_usd": round(jcost, 4),
               "tokens": tok, "provisional": prov, "model": models, "judge": judges, "traps": trap_data}
    return "\n".join(L) + "\n", summary


def main(a):
    rs = [r for rd in run_dirs(a.run_dir) for r in load_run(rd)]
    if not rs:
        print(f"no graded tasks under {a.run_dir}; run `eval grade` first")
        return 1
    text, summary = render(rs, a.run_dir)
    (a.run_dir / "report.md").write_text(text)
    (a.run_dir / "summary.json").write_text(json.dumps(summary, indent=1))
    print(text.split("## Failures by category")[0] + f"report: {a.run_dir / 'report.md'}")
