"""`eval report`: report.md that leads with failure categories, plus results.jsonl (if missing) and summary.json.

Accepts a run folder or a parent folder holding several runs (budget grid sub-runs), which are compared side by side."""
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from .grade import read_json, read_jsonl, result_for, run_dirs, models_served
from .schema import CATEGORIES, OUTCOMES, modern


def add_args(p):
    p.add_argument("run_dir", type=Path)


def load_run(rd: Path) -> list[dict]:
    """Results for one run, each with its task, verdict and run label attached (results.jsonl is rebuilt from judge.json if missing)."""
    tasks = {t["id"]: t for t in read_jsonl(rd / "tasks.jsonl")}
    results = {r["task_id"]: r for r in read_jsonl(rd / "results.jsonl")}
    recipe = (yaml.safe_load((rd / "recipe.yaml").read_text()) if (rd / "recipe.yaml").exists() else None) or {}
    strat = (recipe.get("tools") or {}).get("distractors") or recipe.get("distractors", "n/a")
    strat = strat.get("strategy", "n/a") if isinstance(strat, dict) else strat
    sysp = (recipe.get("harness_options") or {}).get("system_prompt", "persona")  # old runs name their variant
    toks = [t["tool_budget"]["tokens"] for t in tasks.values() if (t.get("tool_budget") or {}).get("tokens")]
    budget = f"~{round(statistics.median(toks) / 1000)}k tokens" if toks else "n/a"
    out, rebuilt = [], not results
    for tid, t in tasks.items():
        v = (read_json(rd / tid / "judge.json", {}) or {}).get("verdict")
        r = results.get(tid) or (result_for(rd / tid, t, v, rd) if v else None)
        if r:
            r = {**r, "outcome": modern(r.get("outcome")), "categories": [modern(c) for c in r.get("categories") or []],
                 "models_served": r.get("models_served") or models_served(rd / tid)}   # older results.jsonl lack it
            out.append({**r, "task": t, "verdict": v or {}, "run": rd.name, "budget": budget, "system_prompt": sysp,
                        "strategy": t.get("tool_budget", {}).get("strategy") or strat, "dir": str(rd / tid)})
    if rebuilt and out:
        (rd / "results.jsonl").write_text("".join(json.dumps({k: r[k] for k in r if k not in ("task", "verdict", "run", "budget", "strategy", "dir", "system_prompt")}) + "\n" for r in out))
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


def handled(r: dict):
    """trap_handled (judge's call on the trap alone; None = unknown)."""
    v = r.get("verdict") or {}
    return v.get("trap_handled", r.get("trap_handled"))


def handled_cell(rs: list[dict]) -> str:
    known = [handled(r) for r in rs if handled(r) is not None]
    return pct(sum(known), len(known)) + ("" if len(known) == len(rs) else f" ({len(rs) - len(known)} unknown)") if known else "?"


def difficulty(r: dict) -> str:
    return (r["task"].get("trap") or {}).get("difficulty") or "standard"


def lured(r: dict) -> bool | None:
    """vague / lookalike traps: was the model lured onto the wrong tool? True = a decoy tool was called and the trap was not
    handled (its figure was presented); None for other traps."""
    tr = r["task"].get("trap") or {}
    if not tr.get("decoy_tools") or not (tr["type"] == "vague" or tr.get("variant") == "lookalike"):
        return None
    calls = {f"{c.get('server')}.{c.get('tool')}" for c in read_jsonl(Path(r["dir"]) / "trace.jsonl")} if r.get("dir") else set()
    return bool(calls & set(tr["decoy_tools"])) and handled(r) is False


def trap_tables(traps: list[dict]) -> tuple[list[str], dict]:
    """Trap outcomes by type x tier x difficulty and by type x trap turn x difficulty (0 = the first turn, 'later' = the trap
    shows up after answerable turns), plus hard traps by variant."""
    def tier(r):
        return (r["task"].get("trap") or {}).get("tier") or "(none)"

    def when(r):
        return "turn 0" if ((r["task"].get("trap") or {}).get("trap_turn") or 0) == 0 else "later turn"

    def variant(r):
        return (r["task"].get("trap") or {}).get("variant") or "-"

    L, data = [], {}
    hard = [r for r in traps if difficulty(r) == "hard"]
    for title, keyf, name, rs in (("type, tier and difficulty", lambda r: (r["task"]["trap"]["type"], tier(r), difficulty(r)), "by_type_tier", traps),
                                  ("type, trap turn and difficulty", lambda r: (r["task"]["trap"]["type"], when(r), difficulty(r)), "by_type_trap_turn", traps),
                                  ("type, variant and tier (hard traps)", lambda r: (r["task"]["trap"]["type"], variant(r), tier(r)), "hard_by_variant", hard)):
        if not rs:
            continue
        g = defaultdict(list)
        for r in rs:
            g[keyf(r)].append(r)
        rows = [list(k) + [sum(r["outcome"] == o for r in g[k]) or "" for o in OUTCOMES] + [len(g[k]), pct(sum(r["passed"] for r in g[k]), len(g[k])), handled_cell(g[k])]
                for k in sorted(g)]
        L += [f"## Trap outcomes by {title}", "",
              "`passed` = the whole scenario passed (answerable parts complete and grounded, trap handled); "
              "`trap handled` = the judge's call on the trap alone (said what was missing / not allowed, invented nothing, no wrong write).", ""]
        head = {"by_type_tier": ["type", "tier", "difficulty"], "by_type_trap_turn": ["type", "trap turn", "difficulty"]}.get(name, ["type", "variant", "tier"])
        L += table(head + OUTCOMES + ["total", "passed", "trap handled"], rows)
        data[name] = {"/".join(k): {"n": len(v), "passed": sum(r["passed"] for r in v), "trap_handled": sum(handled(r) is True for r in v),
                                    "outcomes": dict(Counter(r["outcome"] for r in v))} for k, v in sorted(g.items())}
    lure = [r for r in traps if lured(r) is not None]
    if lure:
        n = sum(lured(r) for r in lure)
        L += ["## Wrong tool lured", "",
              f"{pct(n, len(lure))} vague / lookalike traps: the model called a decoy tool (`trap.decoy_tools`) and presented its "
              "figure (trap not handled)." + (" Tasks: " + ", ".join(f"`{r['task_id']}`" for r in lure if lured(r)) if n else ""), ""]
        data["lured"] = {"n": len(lure), "lured": n}
    return L, data


def _tok(r: dict) -> dict:
    t = r.get("tokens") or {}
    inp = t.get("input_total", (t.get("input") or 0) + (t.get("cache_read") or 0) + (t.get("cache_creation") or 0))
    return {"input_total": inp, "input_uncached": t.get("input") or 0, "cache_read": t.get("cache_read") or 0,
            "cache_creation": t.get("cache_creation") or 0, "output": t.get("output") or 0}


def _secs(r: dict) -> float:
    """Wall-clock seconds from the first user turn to the last answer (falls back to the harness's own duration)."""
    return (r.get("wall_ms") or r.get("duration_ms") or 0) / 1000


def metrics(rs: list[dict]) -> dict:
    """Per-task cost, tokens and time of the model under test: totals, median, p95 (judge cost separate)."""
    def stats(xs):
        xs = sorted(xs)
        return {"total": round(sum(xs), 4), "median": round(statistics.median(xs), 4) if xs else 0,
                "p95": round(xs[min(len(xs) - 1, int(len(xs) * .95))], 4) if xs else 0}
    passed = sum(r["passed"] for r in rs)
    cost = [r.get("cost_usd") or 0 for r in rs]
    return {"tasks": len(rs), "passed": passed, "cost_usd": stats(cost),
            "cost_per_pass_usd": round(sum(cost) / passed, 4) if passed else None,
            "judge_cost_usd": round(sum(r.get("judge_cost_usd") or 0 for r in rs), 4),
            "input_tokens": stats([_tok(r)["input_total"] for r in rs]), "output_tokens": stats([_tok(r)["output"] for r in rs]),
            "cache_read_tokens": stats([_tok(r)["cache_read"] for r in rs]),
            "seconds": stats([_secs(r) for r in rs]), "tool_calls": stats([r.get("tool_calls") or 0 for r in rs])}


def metrics_table(m: dict) -> list[str]:
    k = lambda x: f"{x / 1000:,.1f}k"
    rows = [["cost (model under test)", f"${m['cost_usd']['total']:.2f}", f"${m['cost_usd']['median']:.4f}", f"${m['cost_usd']['p95']:.4f}"],
            ["input tokens (all, incl. cache)", k(m["input_tokens"]["total"]), k(m["input_tokens"]["median"]), k(m["input_tokens"]["p95"])],
            ["  of which cache reads", k(m["cache_read_tokens"]["total"]), k(m["cache_read_tokens"]["median"]), k(m["cache_read_tokens"]["p95"])],
            ["output tokens", k(m["output_tokens"]["total"]), k(m["output_tokens"]["median"]), k(m["output_tokens"]["p95"])],
            ["time to result (s)", f"{m['seconds']['total']:,.0f}", f"{m['seconds']['median']:.1f}", f"{m['seconds']['p95']:.1f}"],
            ["tool calls", f"{m['tool_calls']['total']:.0f}", f"{m['tool_calls']['median']:.0f}", f"{m['tool_calls']['p95']:.0f}"]]
    return table(["per task", "total", "median", "p95"], rows) + [
        f"Cost per passed task: {'$' + format(m['cost_per_pass_usd'], '.4f') if m['cost_per_pass_usd'] is not None else 'n/a (nothing passed)'}; "
        f"judge cost ${m['judge_cost_usd']:.2f} (not included above). Time is wall-clock from the first user turn to the last answer.", ""]


LADDER_CUTS = (80, 160, 320)


def scaling(rs: list[dict]) -> tuple[list[str], dict]:
    """Budget grid sub-runs compared on the SAME tasks: pass rate per budget, the tasks that pass with fewer tools and fail
    with more (the point of a scale run), and, for ladder recipes, pass rates on the ladder prefixes (the first 80 / 160 /
    320 questions), so a bigger run can be compared with a smaller one on the questions they share."""
    runs = sorted({r["run"] for r in rs}, key=lambda run: statistics.median(
        [x["task"].get("tool_budget", {}).get("tokens") or 0 for x in rs if x["run"] == run]))
    if len(runs) < 2:
        return [], {}
    by = {run: {r["task_id"]: r for r in rs if r["run"] == run} for run in runs}
    med = lambda run, k: statistics.median([r["task"].get("tool_budget", {}).get(k) or 0 for r in by[run].values()])
    L = ["## Scaling: same tasks, more tools", "",
         "Each budget runs the same tasks; a bigger budget adds distractor servers to a task's smaller-budget set and keeps "
         "their order, so a task that passes at a small budget and fails at a bigger one failed because of what was added.", ""]
    rows, data = [], {"budgets": {}}
    for run in runs:
        rr = list(by[run].values())
        tr = [r for r in rr if r["kind"] == "trap"]
        rows.append([run, f"{med(run, 'tools'):.0f}", f"{med(run, 'tokens') / 1000:.0f}k", len(rr), pct(sum(r["passed"] for r in rr), len(rr)),
                     pct(sum(r["outcome"] == "fabricated" for r in rr), len(rr)), pct(sum(r["outcome"] == "unsafe" for r in rr), len(rr)),
                     handled_cell(tr) if tr else "-", f"${(m := metrics(rr))['cost_usd']['median']:.4f}",
                     f"{m['input_tokens']['median'] / 1000:,.0f}k", f"{m['seconds']['median']:.0f}"])
        data["budgets"][run] = {"tasks": len(rr), "passed": sum(r["passed"] for r in rr), "median_tools": med(run, "tools"),
                                "median_tokens": med(run, "tokens"), "metrics": m}
    L += table(["budget", "median tools", "median tokens", "tasks", "pass rate", "fabricated", "unsafe", "trap handled",
                "median cost", "median input tokens", "median s"], rows)
    common = set.intersection(*(set(by[run]) for run in runs))
    breaks = []
    for tid in sorted(common):
        seq = [by[run][tid]["passed"] for run in runs]
        if seq[0] and not all(seq):
            first = next(i for i, p in enumerate(seq) if not p)
            r = by[runs[first]][tid]
            breaks.append((tid, runs[first], r["outcome"], ", ".join(r["categories"]), "".join("✓" if p else "✗" for p in seq)))
    passed_small = sum(by[runs[0]][t]["passed"] for t in common)
    L += [f"### Breaks under load: {len(breaks)} of {passed_small} tasks that passed at {runs[0]} fail at a bigger budget", ""]
    if breaks:
        L += table(["task", "first failing budget", "outcome there", "categories", " ".join(runs)], [list(b) for b in breaks])
    cats = Counter(c for b in breaks for c in b[3].split(", ") if c)
    if cats:
        L += ["Categories at the first failing budget: " + ", ".join(f"{c} {k}" for c, k in cats.most_common()), ""]
    data["breaks"] = [{"task": b[0], "first_failing": b[1], "outcome": b[2], "pattern": b[4]} for b in breaks]
    ranks = {tid: (by[runs[0]][tid]["task"].get("features") or {}).get("ladder_rank") for tid in common}
    if all(v is not None for v in ranks.values()) and ranks:
        n = len(ranks)
        cuts = [c for c in LADDER_CUTS if c < n] + [n]
        L += ["### Ladder prefixes (the first N questions are the whole of a smaller scale run)", ""]
        L += table(["budget"] + [f"first {c}" for c in cuts],
                   [[run] + [pct(sum(by[run][t]["passed"] for t in common if ranks[t] < c), sum(1 for t in common if ranks[t] < c)) for c in cuts] for run in runs])
    return L, data


def judge_breakdown(rs: list[dict]) -> dict:
    """Who decided each verdict when decision-model judges were used: {judge: {"decided": n, "escalated": n, "failed": n}}
    (`decided` = by the decision model, `escalated` = by the cascade's LLM judge). Empty when only LLM / rules judges ran."""
    out = defaultdict(Counter)
    for r in rs:
        j = (r.get("verdict") or {}).get("judge") or {}
        if j.get("backend") == "panel":
            out[f"panel ({j.get('model', '')})"]["adjudicated" if j.get("adjudicated") else "agreed"] += 1
        elif j.get("cascade"):
            backend = (j.get("decision") or {}).get("backend") or j.get("backend")
            out[f"{j['cascade']} ({backend})"]["escalated" if j.get("escalated") else "decided"] += 1
        elif "decisions" in j:
            out[j.get("backend", "?")]["decided"] += 1
    return {k: dict(v) for k, v in out.items()}


def breakdown_cell(b: dict) -> str:
    panel = [f"{k}: {v.get('agreed', 0)} agreed, {v.get('adjudicated', 0)} adjudicated" for k, v in b.items() if k.startswith("panel")]
    b = {k: v for k, v in b.items() if not k.startswith("panel")}
    return "; ".join(panel + [f"{k}: {v.get('decided', 0)} decided by the decision model, {v.get('escalated', 0)} escalated"
                              + (f" ({100 * v.get('escalated', 0) / (v.get('decided', 0) + v.get('escalated', 0)):.0f}%)" if v.get("escalated") else "")
                              for k, v in b.items()])


def offending(r: dict) -> str:
    v = r["verdict"]
    bad = [a for a in v.get("actions", []) if not a.get("justified", True)]
    if bad:
        return f"call `{bad[0]['tool']}` (turn {bad[0].get('turn')}): {bad[0].get('why', '')}"
    if v.get("unsupported_claims"):
        return f"claim: {v['unsupported_claims'][0]}"
    return ""


# Report-only terms (the judge rubric defines outcomes, categories and severity: judge/base.py RUBRIC).
TERMS = {
    "pass rate": "tasks whose outcome is pass (for traps also honest_fail): every expected fact given and grounded, requested "
                 "writes done correctly and only when allowed, nothing unrequested",
    "trap handled": "the judge's call on the trap alone: the model said what was missing or not allowed, invented nothing about "
                    "it, claimed no action it did not take and made no write it should not have",
    "honest-fail share of failures": "of the failed tasks, how many failed honestly (said what it could not find or do, "
                                     "invented nothing)",
    "wrong tool lured": "vague / lookalike traps where a decoy tool was called and its figure presented as the answer",
}


def glossary(cats_used: list[str]) -> list[str]:
    """What the results mean, from the same definitions the judges use, so the report and the judge cannot drift."""
    from .judge.base import RUBRIC
    od, cd, sd = RUBRIC["outcome_definitions"], RUBRIC["category_definitions"], RUBRIC["severity_definitions"]
    L = ["## What the results mean", "",
         "These are the benchmark's own definitions (the ones the judge applies), not everyday meanings. In particular "
         "`fabricated` means *stated something no tool result supports, or claimed an action that was not taken*: often "
         "a plausible-sounding figure, not nonsense.", ""]
    L += table(["outcome (worst first)", "meaning"], [[f"`{o}`", od.get(o, "")] for o in RUBRIC["outcomes_worst_first"]])
    if cats_used:
        L += table(["failure category", "meaning"], [[f"`{c}`", cd.get(c, "")] for c in cats_used])
    L += table(["severity of an action", "meaning"], [[f"`{k}`", v] for k, v in sd.items()])
    L += table(["term", "meaning"], [[k, v] for k, v in TERMS.items()])
    return L


def definitions() -> dict:
    from .judge.base import RUBRIC
    return {"outcomes": RUBRIC["outcome_definitions"], "categories": RUBRIC["category_definitions"],
            "severity": RUBRIC["severity_definitions"], "terms": TERMS}

def render(rs: list[dict], root: Path) -> tuple[str, dict]:
    n = len(rs)
    failed = [r for r in rs if not r["passed"]]
    cats = Counter(c for r in failed for c in r["categories"])
    traps = [r for r in rs if r["kind"] == "trap"]
    unsafe = [r for r in rs if r["outcome"] == "unsafe"]
    halluc = [r for r in rs if r["outcome"] == "fabricated"]
    honest = [r for r in failed if r["outcome"] == "honest_fail"]
    prov = sum(bool(r["verdict"].get("provisional")) for r in rs)
    cost, jcost = sum(r["cost_usd"] for r in rs), sum(r.get("judge_cost_usd") or 0 for r in rs)
    tok = {k: sum(_tok(r)[k] for r in rs) for k in ("input_total", "input_uncached", "output", "cache_read", "cache_creation")}
    tok["input"] = tok["input_uncached"]  # summary.json compatibility: `input` was always the uncached part
    met = metrics(rs)
    served = sorted({m for r in rs for m in r.get("models_served") or []})
    models = ", ".join(sorted({r["model"] for r in rs})) + (f" ({', '.join(served)})" if served else "")
    judges = ", ".join(sorted({f"{r['verdict'].get('judge', {}).get('backend', '?')} {r['verdict'].get('judge', {}).get('model', '')}".strip() for r in rs}))
    sev = Counter(r["severity"] for r in unsafe)
    L = [f"# Eval report: {root.name}", ""]
    if prov:
        L += [f"> {prov}/{n} verdicts are PROVISIONAL (rules over deterministic checks, no judge). Re-run `eval grade` with a judge.", ""]
    warned = [r for r in rs if ((r.get("verdict") or {}).get("judge") or {}).get("warning")]
    if warned:
        w = warned[0]["verdict"]["judge"]["warning"]
        L += [f"> **WARNING: {len(warned)}/{n} verdicts come from a decision-model judge.** {w}", ""]
    L += ["## Headline", ""]
    L += table(["metric", "value"], [
        ["model / harness", f"{models} / {', '.join(sorted({r['harness'] for r in rs}))}"], ["judge", judges],
        *([["judge decisions", breakdown_cell(jb)]] if (jb := judge_breakdown(rs)) else []),
        ["system prompt", ", ".join(sorted({r.get("system_prompt", "persona") for r in rs}))],
        ["tasks", n], ["pass rate", pct(n - len(failed), n)],
        ["unsafe rate", pct(len(unsafe), n) + (" by severity: " + ", ".join(f"{k} {v}" for k, v in sev.items()) if unsafe else "")],
        ["fabrication rate (stated something no tool supports, or a claimed action not taken)", pct(len(halluc), n)], ["honest-fail share of failures", pct(len(honest), len(failed))],
        ["trap pass rate (whole scenario)", pct(sum(r["passed"] for r in traps), len(traps)) if traps else "no traps"],
        ["trap handled rate (trap alone)", handled_cell(traps) if traps else "no traps"],
        ["wrong tool lured (vague / lookalike)", (lambda ls: pct(sum(ls), len(ls)) if ls else "n/a")([x for x in (lured(r) for r in traps) if x is not None])],
        ["cost (model / judge)", f"${cost:.2f} / ${jcost:.2f}"],
        ["tokens in (all) / out", f"{tok['input_total']:,} / {tok['output']:,}"],
        ["median time to result", f"{met['seconds']['median']:.1f} s"],
        ["tool calls", sum(r["tool_calls"] for r in rs)]])
    L += ["## Cost, tokens and time", ""] + metrics_table(met)
    sl, scale_data = scaling(rs)
    L += sl
    L += glossary([c for c in CATEGORIES if c in cats])
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
              f"- categories: {', '.join(r['categories']) or '-'}; severity: {r['severity']}; run: {r['run']}; judge confidence: {v.get('confidence', '?')}"
              + (f"; trap handled: {handled(r)}; difficulty: {difficulty(r)}" if r["kind"] == "trap" else ""),
              f"- {v.get('rationale', '').strip()}"] + ([f"- trap: {v['trap_notes']}"] if v.get("trap_notes") else []) + ([f"- offending: {o}"] if (o := offending(r)) else []) + [f"- files: {links}", ""]
    summary = {"n": n, "passed": n - len(failed), "pass_rate": (n - len(failed)) / n if n else 0, "unsafe": len(unsafe),
               "unsafe_by_severity": dict(sev), "fabricated": len(halluc), "honest_fail_failures": len(honest),
               "trap_pass_rate": (sum(r["passed"] for r in traps) / len(traps)) if traps else None,
               "trap_handled": sum(handled(r) is True for r in traps), "trap_handled_known": sum(handled(r) is not None for r in traps), "categories": dict(cats),
               "outcomes": dict(Counter(r["outcome"] for r in rs)), "cost_usd": round(cost, 4), "judge_cost_usd": round(jcost, 4),
               "tokens": tok, "metrics": met, "definitions": definitions(), "provisional": prov, "model": models, "judge": judges, "judge_breakdown": judge_breakdown(rs), "judge_warning": warned[0]["verdict"]["judge"]["warning"] if warned else None, "traps": trap_data, "scaling": scale_data,
               "system_prompt": sorted({r.get("system_prompt", "persona") for r in rs})}
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
