"""`python -m mockmcp eval recipe <recipe.yaml> --out runs/<id>`: sample tasks from the bank, decide which MCP servers
(required + distractors) each task sees, and write the run folder (see schema.py). Every key is documented in
bench/recipes/example.yaml. Deterministic: the same recipe and seed give an identical tasks.jsonl.
"""
import collections
import copy
import json
import random
import re
import statistics
import subprocess
from datetime import date
from pathlib import Path

import yaml

from .. import catalog
from ..spec import WORLD
from . import features as F
from . import tasks as T

ROOT = T.ROOT
SIZES = "tool_sizes.json"
DEFAULTS = {
    "name": "run", "seed": 1, "kind": "scenario", "tasks": 12, "mix": {}, "filter": None, "followups": "all", "traps": 0,
    "trap_types": None, "strict": False, "presets": {},
    "tools": {"budget": None, "distractors": "adjacent", "position": "random", "toolset": "per_task"},
    "harness": "claude-code", "harness_options": {"tool_search": "off", "max_turns": 25, "timeout_s": 600},
}
DISTRACTORS = ("random", "adjacent", "persona", "none")
POSITIONS = ("first", "middle", "last", "random")


# ---------- recipe ----------

def resolve(recipe) -> dict:
    """Recipe path or dict -> full recipe with defaults filled in (what gets written to <run>/recipe.yaml)."""
    if not isinstance(recipe, dict):
        recipe = yaml.safe_load(Path(recipe).read_text()) or {}
    r = copy.deepcopy(DEFAULTS) | {k: v for k, v in recipe.items() if k not in ("tools", "harness_options")}
    r["tools"] = DEFAULTS["tools"] | (recipe.get("tools") or {})
    r["harness_options"] = DEFAULTS["harness_options"] | (recipe.get("harness_options") or {})
    ts = r["harness_options"].get("tool_search")
    if isinstance(ts, bool):  # YAML 1.1 reads an unquoted on/off as true/false
        r["harness_options"]["tool_search"] = "on" if ts else "off"
    t = r["tools"]
    if t["distractors"] not in DISTRACTORS or t["position"] not in POSITIONS or t["toolset"] not in ("per_task", "shared"):
        raise ValueError(f"tools: distractors {DISTRACTORS}, position {POSITIONS}, toolset per_task|shared; got {t}")
    if r["kind"] not in ("slice", "scenario", "any", "trap"):
        raise ValueError(f"kind must be slice | scenario | any, got {r['kind']}")
    if not re.fullmatch(r"all|none|first_n:\d+", str(r["followups"])):
        raise ValueError(f"followups must be all | none | first_n:N, got {r['followups']}")
    return r


def _count(v, total: int) -> float:
    """'25%' -> share of total; int N -> N tasks; float < 1 -> fraction of total."""
    if isinstance(v, str) and v.strip().endswith("%"):
        return total * float(v.strip()[:-1]) / 100
    v = float(v)
    return total * v if v < 1 else v


def _quotas(spec: dict, total: int) -> dict:
    """Largest-remainder rounding so quotas add up; whatever the mix does not claim is left to the natural distribution."""
    raw = {k: _count(v, total) for k, v in spec.items()}
    if sum(raw.values()) > total + 1e-6:
        raise ValueError(f"mix claims {sum(raw.values()):g} of {total} tasks")
    out = {k: int(v) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: (-(raw[k] - out[k]), k))[:round(sum(raw.values())) - sum(out.values())]:
        out[k] += 1
    return out


def budgets(recipe: dict) -> list[dict | None]:
    """tools.budget -> list of budget dicts, one per sub-run (a list of values is a grid); [None] = required servers only."""
    b = recipe["tools"]["budget"]
    if not b:
        return [None]
    if isinstance(b, list):
        return [dict(x) for x in b]
    out = []
    for k, v in b.items():
        if k not in ("tokens", "tools", "servers"):
            raise ValueError(f"budget key must be tokens | tools | servers, got {k}")
        out += [{k: x} for x in (v if isinstance(v, list) else [v])]
    return out


def label(b: dict | None) -> str:
    return "none" if not b else "-".join(f"{k}-{v}" for k, v in b.items())


# ---------- tool measurement ----------

def measure(out_dir: Path | None = None) -> dict:
    """{system: {tools, tokens, write_tools}} from the real MCP tool lists (json size / 4 ~ tokens). Cached in the run folder."""
    cache = out_dir / SIZES if out_dir else None
    if cache and cache.exists():
        return json.loads(cache.read_text())
    from ..server import Engine
    from ..spec import system_ids
    eng, sizes = Engine(system_ids()), {}
    for sid in eng.systems:
        tools = eng.mcp_tools(sid)
        n = sum(len(json.dumps(t.model_dump(mode="json", by_alias=True, exclude_none=True), separators=(",", ":"))) for t in tools)
        sizes[sid] = {"tools": len(tools), "tokens": round(n / 4),
                      "write_tools": sorted(t.name for t in tools if not (t.annotations and t.annotations.read_only_hint))}
    if cache and out_dir.exists():
        cache.write_text(json.dumps(sizes, indent=1))
    return sizes


# ---------- distractor ranking ----------

class Graph:
    """Which servers go together: co-occurrence in questions (catalog used_by) and usage per persona file."""

    def __init__(self):
        self.cooc: dict = collections.defaultdict(collections.Counter)
        self.file_use: dict = collections.defaultdict(collections.Counter)
        by_q = collections.defaultdict(set)
        for r in catalog.load():
            for q in filter(None, r["used_by"].split(";")):
                by_q[q].add(r["system"])
        for q, ss in by_q.items():
            for a in ss:
                self.file_use[q.split(":")[0]][a] += 1
                for b in ss - {a}:
                    self.cooc[a][b] += 1

    def order(self, strategy: str, required: set, file_no: str, candidates: list, rng: random.Random) -> list:
        """Candidate distractors, most relevant first for the strategy."""
        tie = {c: rng.random() for c in candidates}
        if strategy == "random" or strategy == "none":
            return sorted(candidates, key=tie.get) if strategy == "random" else []
        adj = lambda c: (-sum(self.cooc[r][c] for r in required), -self.file_use[file_no][c], tie[c])
        if strategy == "adjacent":
            return sorted(candidates, key=adj)
        used = lambda c: self.file_use[file_no][c]  # persona: whatever that persona file's questions use, then adjacent
        return sorted(candidates, key=lambda c: (-(used(c) > 0), -used(c)) + adj(c))


def _select(required: list, ordered: list, budget: dict | None, sizes: dict) -> list:
    """Add distractors in order until the budget is reached; the server that crosses it is the last one added."""
    chosen, tools, tokens = [], sum(sizes[r]["tools"] for r in required), sum(sizes[r]["tokens"] for r in required)
    if not budget:
        return chosen
    (kind, limit), = budget.items()

    def reached():
        return {"tools": tools, "tokens": tokens, "servers": len(required) + len(chosen)}[kind] >= limit
    for d in ordered:
        if reached():
            break
        chosen.append(d)
        tools, tokens = tools + sizes[d]["tools"], tokens + sizes[d]["tokens"]
    return chosen


def _place(required: list, distractors: list, position: str, rng: random.Random) -> list:
    k = {"first": 0, "last": len(distractors), "middle": len(distractors) // 2,
         "random": rng.randint(0, len(distractors))}[position]
    return distractors[:k] + required + distractors[k:]


# ---------- sampling ----------

def _truncate(task: dict, mode: str, presets: dict) -> dict:
    keep = {"all": None, "none": 0}.get(mode, int(mode.split(":")[1]) if mode.startswith("first_n") else None)
    if keep is not None and len(task["turns"]) > 1 + keep:
        task["turns"] = task["turns"][:1 + keep]
        task["writes"]["expected"] = [w for w in task["writes"]["expected"] if w["turn"] < len(task["turns"])]
    task["features"] = F.features(task)
    task["strata"] = F.strata(task, presets)
    return task


def sample(recipe: dict) -> tuple[list[dict], dict, list[str]]:
    """Stratified draw -> (tasks, counts per stratum {requested, drawn, available}, warnings)."""
    presets = F.merged_presets(recipe["presets"])
    rng, warns, n = random.Random(recipe["seed"]), [], int(recipe["tasks"])
    pool = [] if recipe["kind"] == "trap" else [t for t in T.build_bank() if recipe["kind"] in ("any", t["kind"])]
    traps = T.load_traps()
    if recipe["trap_types"]:
        traps = [t for t in traps if t["trap"]["type"] in recipe["trap_types"]]
    pool = [_truncate(t, recipe["followups"], presets) for t in pool]
    traps = [_truncate(t, recipe["followups"], presets) for t in traps]
    if recipe["filter"]:
        keep = F.compile_filter(recipe["filter"], presets)
        pool, traps = [t for t in pool if keep(t["features"])], [t for t in traps if keep(t["features"])]
    pool.sort(key=lambda t: t["id"]), traps.sort(key=lambda t: t["id"])
    counts: dict = {}

    def short(name, want, got, avail):
        counts[name] = {"requested": want, "drawn": got, "available": avail}
        if got < want:
            msg = f"stratum '{name}': wanted {want}, only {got} available"
            if recipe["strict"]:
                raise ValueError(msg)
            warns.append(msg + " (topped up from the natural distribution)")

    n_traps = int(round(_count(recipe["traps"], n))) if recipe["traps"] else 0
    n_traps, drawn, taken = (n if recipe["kind"] == "trap" else n_traps), [], set()
    # traps: round-robin over trap types so every type is represented
    by_type = collections.defaultdict(list)
    for t in traps:
        by_type[t["trap"]["type"]].append(t)
    trng = random.Random(f"{recipe['seed']}:traps")  # own stream: the trap bank never shifts the other draws
    for v in by_type.values():
        trng.shuffle(v)
    got = []
    while len(got) < n_traps and any(by_type.values()):
        for ty in sorted(by_type):
            if by_type[ty] and len(got) < n_traps:
                got.append(by_type[ty].pop())
    if n_traps:
        short("trap", n_traps, len(got), len(traps))
    drawn += got
    rest = n - len(got)
    quotas = _quotas(recipe["mix"], max(rest, 0)) if recipe["mix"] else {}
    preds = {k: F.compile_filter(k, presets) for k in quotas}
    # scarcest stratum first so overlapping strata do not starve it
    for name in sorted(quotas, key=lambda k: (sum(preds[k](t["features"]) for t in pool), k)):
        cand = [t for t in pool if t["id"] not in taken and preds[name](t["features"])]
        pick = rng.sample(cand, min(quotas[name], len(cand)))
        taken |= {t["id"] for t in pick}
        drawn += pick
        short(name, quotas[name], len(pick), sum(preds[name](t["features"]) for t in pool))
    need = n - len(drawn)
    cand = [t for t in pool if t["id"] not in taken]
    pick = rng.sample(cand, min(need, len(cand)))
    drawn += pick
    counts["natural"] = {"requested": max(rest - sum(quotas.values()), 0), "drawn": len(pick), "available": len(cand)}
    if len(drawn) < n:
        warns.append(f"only {len(drawn)} of {n} tasks available after filtering")
        if recipe["strict"]:
            raise ValueError(warns[-1])
    return sorted(drawn, key=lambda t: t["id"]), counts, warns


def assign(chosen: list[dict], recipe: dict, sizes: dict, budget: dict | None) -> list[dict]:
    """Copy of the tasks with servers, tool budget and write tools filled in for one budget."""
    opts, graph, seed = recipe["tools"], Graph(), recipe["seed"]
    universe = sorted(sizes)
    strategy = "none" if budget is None else opts["distractors"]
    shared = None
    if opts["toolset"] == "shared":
        req = sorted({s for t in chosen for s in t["servers"]["required"] if s in sizes})
        rng = random.Random(f"{seed}|shared")
        order = graph.order(strategy, set(req), "", [u for u in universe if u not in req], rng)
        d = _select(req, order, budget, sizes)
        shared = (req, sorted(d, key=lambda s: random.Random(f"{seed}|shared|{s}").random()))
    out = []
    for task in chosen:
        t = copy.deepcopy(task)
        rng = random.Random(f"{seed}|{t['id']}")
        missing = set((t.get("trap") or {}).get("missing_servers") or [])
        required = [s for s in t["servers"]["required"] if s in sizes and s not in missing]
        if shared:
            req, dist = shared
            required, dist = [s for s in req if s not in missing], [s for s in dist if s not in missing]
            loaded = _place(required, dist, opts["position"], random.Random(f"{seed}|shared|pos"))
        else:
            cands = [u for u in universe if u not in set(required) | missing]
            order = graph.order(strategy, set(t["servers"]["required"]), t["persona"].get("file", ""), cands, rng)
            dist = _select(required, order, budget, sizes)
            key = {s: rng.random() for s in dist}
            dist.sort(key=key.get)
            loaded = _place(required, dist, opts["position"], rng)
        tools, tokens = sum(sizes[s]["tools"] for s in loaded), sum(sizes[s]["tokens"] for s in loaded)
        t["servers"] = {"required": required, "distractors": [s for s in loaded if s not in required], "loaded": loaded}
        t["tool_budget"] = {"tools": tools, "tokens": tokens, "servers": len(loaded), "relevant_position": opts["position"],
                            "target": budget, "label": label(budget)}
        t["writes"]["write_tools_loaded"] = sorted(w for s in loaded for w in sizes[s]["write_tools"])
        out.append(t)
    return out


# ---------- run folder ----------

def _spread(xs: list) -> dict:
    return {"min": min(xs), "median": statistics.median(xs), "max": max(xs)} if xs else {}


def _git() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _harness(name: str):
    from . import harness
    getter = getattr(harness, "get", None)
    return getter(name) if getter else None


def _write_task(d: Path, task: dict, recipe: dict, harness) -> None:
    d.mkdir(parents=True, exist_ok=True)
    from ..bench import SYSTEM
    (d / "prompt.json").write_text(json.dumps({
        "turns": [t["text"] for t in task["turns"]],
        "system": SYSTEM.format(company=WORLD["company"], today=date.today().isoformat())}, indent=1, ensure_ascii=False))
    if harness:
        harness.write_task(d, task, recipe)
    else:
        (d / "TODO.harness").write_text("mockmcp.eval.harness.get(name).write_task(task_dir, task, recipe) is not available "
                                        "yet: mcp.json and run.sh are written by the harness (loaded servers: "
                                        f"{', '.join(task['servers']['loaded'])}).\n")


def build(recipe_or_path, out_dir=None, dry_run: bool = False) -> dict:
    """Write the run folder (or only plan it with dry_run). Returns {recipe, counts, warnings, runs: {label: tasks}}.
    A budget grid writes one full run folder per budget under <out>/<label>/, with identical tasks in each."""
    recipe = resolve(recipe_or_path)
    out = Path(out_dir) if out_dir else None
    if out and not dry_run:
        out.mkdir(parents=True, exist_ok=True)
    chosen, counts, warns = sample(recipe)
    sizes = measure(out if out and out.exists() else None)
    runs = {label(b): (b, assign(chosen, recipe, sizes, b)) for b in budgets(recipe)}
    plan = {"recipe": recipe, "counts": counts, "warnings": warns, "runs": {k: v[1] for k, v in runs.items()}}
    if dry_run or not out:
        return plan
    harness = _harness(recipe["harness"])
    grid = len(runs) > 1
    commit = _git()
    for lab, (b, tasks) in runs.items():
        d = out / lab if grid else out
        d.mkdir(parents=True, exist_ok=True)
        sub = copy.deepcopy(recipe)
        sub["tools"]["budget"] = b
        (d / "recipe.yaml").write_text(yaml.safe_dump(sub, sort_keys=False, allow_unicode=True))
        (d / "tasks.jsonl").write_text("".join(json.dumps(t, ensure_ascii=False) + "\n" for t in tasks))
        for t in tasks:
            _write_task(d / t["id"], t, sub, harness)
        (d / "manifest.json").write_text(json.dumps(_manifest(sub, tasks, counts, warns, commit, lab, b), indent=1))
    if grid:
        (out / "recipe.yaml").write_text(yaml.safe_dump(recipe, sort_keys=False, allow_unicode=True))
        (out / "manifest.json").write_text(json.dumps({**_manifest(recipe, runs[next(iter(runs))][1], counts, warns, commit, "grid", None),
                                                       "subruns": list(runs)}, indent=1))
    return plan


def _manifest(recipe, tasks, counts, warns, commit, lab, budget) -> dict:
    return {"name": recipe["name"], "seed": recipe["seed"], "git_commit": commit, "harness": recipe["harness"],
            "tasks": len(tasks), "kinds": dict(collections.Counter(t["kind"] for t in tasks)),
            "strata": counts, "warnings": warns, "budget": {"label": lab, "target": budget,
                                                             "tools": _spread([t["tool_budget"]["tools"] for t in tasks]),
                                                             "tokens": _spread([t["tool_budget"]["tokens"] for t in tasks]),
                                                             "servers": _spread([t["tool_budget"]["servers"] for t in tasks])}}


# ---------- CLI ----------

def _kv(s: str) -> dict:
    """'tokens=20000' / 'tokens=5000,25000' -> budget spec (a list of values is a grid)."""
    k, v = s.split("=", 1)
    vals = [int(x) for x in v.split(",")]
    return {k.strip(): vals if len(vals) > 1 else vals[0]}


def add_args(p):
    p.add_argument("recipe", help="recipe YAML (see bench/recipes/example.yaml)")
    p.add_argument("--out", help="run folder to write (default runs/<recipe name>)")
    p.add_argument("--seed", type=int), p.add_argument("--tasks", type=int)
    p.add_argument("--mix", help="override the mix, e.g. 'simple: 25%%, write: 25%%, systems>=3: 10%%'")
    p.add_argument("--budget", help="override tools.budget, e.g. tokens=30000, tools=200, servers=10, tokens=5000,25000 (grid)")
    p.add_argument("--distractors", choices=DISTRACTORS)
    p.add_argument("--dry-run", action="store_true", help="print the plan (strata, budgets, servers per task); write nothing")


def main(a):
    recipe = yaml.safe_load(Path(a.recipe).read_text()) or {}
    for k in ("seed", "tasks"):
        if getattr(a, k) is not None:
            recipe[k] = getattr(a, k)
    if a.mix:
        recipe["mix"] = yaml.safe_load(a.mix if a.mix.lstrip().startswith("{") else "{" + a.mix + "}")
    if a.budget or a.distractors:
        recipe["tools"] = dict(recipe.get("tools") or {})
        if a.budget:
            recipe["tools"]["budget"] = _kv(a.budget)
        if a.distractors:
            recipe["tools"]["distractors"] = a.distractors
    resolved = resolve(recipe)
    out = Path(a.out or f"runs/{resolved['name']}")
    plan = build(resolved, out, dry_run=a.dry_run)
    show(plan)
    if not a.dry_run:
        print(f"\nwrote {out} ({len(plan['runs'])} run{'s' if len(plan['runs']) > 1 else ''}); next: python -m mockmcp eval run {out}")
    return 0


def show(plan: dict) -> None:
    r = plan["recipe"]
    print(f"recipe {r['name']}: seed {r['seed']}, {r['tasks']} tasks, kind {r['kind']}, followups {r['followups']}, "
          f"harness {r['harness']}, tools {r['tools']}")
    print("\nstrata (requested / drawn / available in pool):")
    for k, c in plan["counts"].items():
        print(f"  {k:<28}{c['requested']:>4} /{c['drawn']:>4} /{c['available']:>5}")
    for w in plan["warnings"]:
        print(f"  WARNING {w}")
    for lab, tasks in plan["runs"].items():
        tb = [t["tool_budget"] for t in tasks]
        print(f"\nbudget {lab}: tools {_spread([b['tools'] for b in tb])} tokens {_spread([b['tokens'] for b in tb])} "
              f"servers {_spread([b['servers'] for b in tb])}")
        if lab == next(iter(plan["runs"])) or len(plan["runs"]) == 1:
            for t in tasks:
                print(f"  {t['id']:<34}{t['kind']:<9}req={','.join(t['servers']['required']) or '-':<28}"
                      f"+{len(t['servers']['distractors']):>2} dist  {t['tool_budget']['tools']:>4} tools "
                      f"{t['tool_budget']['tokens']:>6} tok  [{','.join(t['strata'])}]")
        else:
            print("  (same tasks as the first budget; only the loaded servers differ)")
