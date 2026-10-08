"""`python -m mockmcp eval recipe <recipe.yaml> --out runs/<id>`: sample tasks from the bank, decide which MCP servers
(required + distractors) each task sees, and write the run folder (see schema.py). Every key is documented in
bench/recipes/example.yaml. Deterministic: the same recipe and seed give an identical tasks.jsonl.
"""
import collections
import copy
import hashlib
import json
import random
import re
import statistics
import subprocess
from datetime import date
from pathlib import Path

import yaml

from .. import catalog
from . import features as F
from . import tasks as T

ROOT = T.ROOT
SIZES = "tool_sizes.json"
# Calibrated on claude-code + haiku (2026-10): a "reply OK" call with a task's servers loaded at three budgets gave real input
# tokens = 1.48 x (compact json chars / 4) + ~3.7k fixed overhead, i.e. ~2.7 chars per token for these tool definitions
# (ids, enums and JSON schema punctuation tokenise densely). Budgets are therefore real context tokens of tool definitions.
CHARS_PER_TOKEN = 2.7
DEFAULTS = {
    "name": "run", "seed": 1, "kind": "scenario", "tasks": 12, "mix": {}, "filter": None, "followups": "all", "traps": 0,
    "trap_types": None, "strict": False, "presets": {}, "ladder": None,
    "tools": {"budget": None, "distractors": "adjacent", "position": "random", "toolset": "per_task"},
    "harness": "claude-code", "harness_options": {"tool_search": "off", "max_turns": 25, "timeout_s": 600, "system_prompt": "default"},
}
DISTRACTORS = ("random", "adjacent", "persona", "none")
POSITIONS = ("first", "middle", "last", "random")


# ---------- recipe ----------

def load(path) -> dict:
    """Read a recipe file, following `extends: <base.yaml>` (relative to the file); the file's own keys win, and `tools` /
    `harness_options` are merged key by key. `extends` keeps recipe families (e.g. scale-80 / scale-320 / scale-all) on one
    base so they cannot drift apart."""
    path = Path(path)
    r = yaml.safe_load(path.read_text()) or {}
    base = r.pop("extends", None)
    if not base:
        return r
    b = load(path.parent / base)
    out = b | {k: v for k, v in r.items() if k not in ("tools", "harness_options")}
    for k in ("tools", "harness_options"):
        if k in b or k in r:
            out[k] = (b.get(k) or {}) | (r.get(k) or {})
    return out


def resolve(recipe) -> dict:
    """Recipe path or dict -> full recipe with defaults filled in (what gets written to <run>/recipe.yaml)."""
    if not isinstance(recipe, dict):
        recipe = load(recipe)
    r = copy.deepcopy(DEFAULTS) | {k: v for k, v in recipe.items() if k not in ("tools", "harness_options")}
    r["tools"] = DEFAULTS["tools"] | (recipe.get("tools") or {})
    r["harness_options"] = DEFAULTS["harness_options"] | (recipe.get("harness_options") or {})
    ts = r["harness_options"].get("tool_search")
    if isinstance(ts, bool):  # YAML 1.1 reads an unquoted on/off as true/false
        r["harness_options"]["tool_search"] = "on" if ts else "off"
    from .harness.base import SYSTEM_PROMPTS
    if r["harness_options"].get("system_prompt") not in SYSTEM_PROMPTS:
        raise ValueError(f"harness_options.system_prompt must be one of {sorted(SYSTEM_PROMPTS)}, got {r['harness_options'].get('system_prompt')!r}")
    t = r["tools"]
    if t["distractors"] not in DISTRACTORS or t["position"] not in POSITIONS or t["toolset"] not in ("per_task", "shared"):
        raise ValueError(f"tools: distractors {DISTRACTORS}, position {POSITIONS}, toolset per_task|shared; got {t}")
    if r["kind"] not in ("slice", "scenario", "any", "trap"):
        raise ValueError(f"kind must be slice | scenario | any, got {r['kind']}")
    if not (r["tasks"] == "all" or str(r["tasks"]).isdigit()):
        raise ValueError(f"tasks must be a number or 'all', got {r['tasks']!r}")
    if r["tasks"] == "all" and not r["ladder"]:
        raise ValueError("tasks: all needs a ladder (the whole ordered bank); see bench/recipes/scale.yaml")
    if r["ladder"] and (r["mix"] or r["traps"]):
        raise ValueError("ladder replaces mix and traps: put the trap share in the ladder cells")
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
    """{system: {tools, tokens, per_tool, write_tools}} from the real MCP tool lists (compact json chars / CHARS_PER_TOKEN, calibrated
    against Claude Code's real prompt size). Cached in the run folder."""
    cache = out_dir / SIZES if out_dir else None
    if cache and cache.exists():
        cached = json.loads(cache.read_text())
        if all("per_tool" in v for v in cached.values()):  # older caches lack per-tool sizes (needed for hidden tools)
            return cached
    from ..server import Engine
    from ..spec import system_ids
    eng, sizes = Engine(system_ids()), {}
    for sid in eng.systems:
        tools = eng.mcp_tools(sid)
        each = {t.name: len(json.dumps(t.model_dump(mode="json", by_alias=True, exclude_none=True), separators=(",", ":"))) for t in tools}
        sizes[sid] = {"tools": len(tools), "tokens": round(sum(each.values()) / CHARS_PER_TOKEN),
                      "per_tool": {k: round(v / CHARS_PER_TOKEN) for k, v in each.items()},
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


def without_hidden(sizes: dict, hidden: list[str]) -> dict:
    """sizes with the trap's hidden tools ("server.tool") taken out of their server's tool count, tokens and write tools."""
    if not hidden:
        return sizes
    out = dict(sizes)
    for h in hidden:
        sid, name = h.split(".", 1)
        z = out[sid] = dict(out[sid])
        z["tokens"] -= z["per_tool"].get(name, 0)
        z["tools"] -= name in z["per_tool"]
        z["write_tools"] = [w for w in z["write_tools"] if w != name]
    return out


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


def _unit(seed, key: str) -> float:
    return int(_h(seed, key)[:12], 16) / 16 ** 12


def _place_stable(required: list, distractors: list, position: str, seed, task_id: str) -> list:
    """Like _place, but every distractor has a fixed key in [0, 1) and the required block sits at a fixed key too, so a
    bigger budget only inserts servers: the loaded order at a small budget is a subsequence of the order at a bigger one."""
    at = {"first": -1.0, "last": 2.0, "middle": 0.5, "random": _unit(seed, f"{task_id}|pos")}[position]
    keyed = [(_unit(seed, f"{task_id}|place|{s}"), 1, s) for s in distractors] + [(at, 0, None)]
    out = []
    for _, _, s in sorted(keyed):
        out += required if s is None else [s]
    return out


# ---------- sampling ----------

def _truncate(task: dict, mode: str, presets: dict) -> dict:
    keep = {"all": None, "none": 0}.get(mode, int(mode.split(":")[1]) if mode.startswith("first_n") else None)
    if keep is not None and len(task["turns"]) > 1 + keep:
        task["turns"] = task["turns"][:1 + keep]
        task["writes"]["expected"] = [w for w in task["writes"]["expected"] if w["turn"] < len(task["turns"])]
    task["features"] = F.features(task)
    task["strata"] = F.strata(task, presets)
    return task


# ---------- ladder (nested sampling) ----------

def _h(seed, key: str) -> str:
    return hashlib.sha1(f"{seed}|{key}".encode()).hexdigest()


def ladder_order(recipe: dict) -> tuple[list[dict], dict, list[str]]:
    """The whole bank in one deterministic order whose every prefix keeps the ladder's mix, so a run of N tasks is exactly
    the first N of any bigger run with the same seed and ladder (80 ⊂ 160 ⊂ 320 ⊂ all).

    - `ladder` maps cell filters to weights, e.g. {"kind=slice&calls=1&writes=0": 15, "trap&difficulty=hard": 10, ...};
      cells are disjoint: a task belongs to the first cell it matches (tasks that match none are left out).
    - Inside a cell, tasks are ordered by a hash of (seed, task id), so adding a question to the bank does not reshuffle the
      others, and domains take turns so that even a small prefix spreads across them.
    - The order interleaves cells by deficit: the next task comes from the cell furthest below weight x position.
      When a cell runs out, the others share its weight.
    - Slices: at most one per persona question (the first one reached), so a short ladder does not repeat a question as
      several near-identical single-system lookups.
    Returns (ordered tasks with features.ladder_rank / ladder_cell, counts per cell, warnings)."""
    presets = F.merged_presets(recipe["presets"])
    seed, cells = recipe["seed"], dict(recipe["ladder"])
    bank = [t for t in T.build_bank() if recipe["kind"] in ("any", t["kind"])] + T.load_traps()
    bank = [_truncate(t, recipe["followups"], presets) for t in bank]
    if recipe["filter"]:
        keep = F.compile_filter(recipe["filter"], presets)
        bank = [t for t in bank if keep(t["features"])]
    preds = {c: F.compile_filter(c, presets) for c in cells}
    members = {c: [] for c in cells}
    left_out = 0
    for t in bank:
        c = next((c for c in cells if preds[c](t["features"])), None)
        if c is None:
            left_out += 1
        else:
            members[c].append(t)
    queues = {}
    for c, ts in members.items():
        by_dom = collections.defaultdict(list)
        for t in sorted(ts, key=lambda t: _h(seed, t["id"])):
            by_dom[t.get("domain") or ""].append(t)
        doms = sorted(by_dom, key=lambda d: _h(seed, f"{c}|{d}"))
        q, i = [], 0
        while any(by_dom.values()):
            d = doms[i % len(doms)]
            if by_dom[d]:
                q.append(by_dom[d].pop(0))
            i += 1
        queues[c] = collections.deque(q)
    total_w = {c: float(w) for c, w in cells.items()}
    taken = collections.Counter()
    seen_q, order = set(), []
    while any(queues.values()):
        live = [c for c in cells if queues[c]]
        w = sum(total_w[c] for c in live)
        pos = sum(taken[c] for c in live) + 1
        c = max(live, key=lambda c: (total_w[c] / w * pos - taken[c], -list(cells).index(c)))
        t = queues[c].popleft()
        if t["kind"] == "slice":
            if t.get("question_id") in seen_q:
                continue
            seen_q.add(t.get("question_id"))
        taken[c] += 1
        t["features"]["ladder_rank"], t["features"]["ladder_cell"] = len(order), c
        order.append(t)
    counts = {c: {"weight": cells[c], "available": taken[c], "members": len(members[c])} for c in cells}
    warns = [f"{left_out} bank tasks match no ladder cell and are left out"] if left_out else []
    return order, counts, warns


def sample_ladder(recipe: dict) -> tuple[list[dict], dict, list[str]]:
    order, cell_counts, warns = ladder_order(recipe)
    n = len(order) if recipe["tasks"] == "all" else int(recipe["tasks"])
    if n > len(order):
        warns.append(f"only {len(order)} tasks in the ladder, wanted {n}")
        if recipe["strict"]:
            raise ValueError(warns[-1])
    head = order[:n]
    got = collections.Counter(t["features"]["ladder_cell"] for t in head)
    counts = {c: {"requested": round(len(head) * v["weight"] / sum(x["weight"] for x in cell_counts.values())),
                  "drawn": got[c], "available": v["available"]} for c, v in cell_counts.items()}
    return sorted(head, key=lambda t: t["id"]), counts, warns


def sample(recipe: dict) -> tuple[list[dict], dict, list[str]]:
    """Stratified draw -> (tasks, counts per stratum {requested, drawn, available}, warnings)."""
    if recipe["ladder"]:
        return sample_ladder(recipe)
    presets = F.merged_presets(recipe["presets"])
    rng, warns, n = random.Random(recipe["seed"]), [], int(recipe["tasks"])
    pool = [] if recipe["kind"] == "trap" else [t for t in T.build_bank() if recipe["kind"] in ("any", t["kind"])]
    traps = T.load_traps()
    if recipe["kind"] == "trap" and recipe["mix"]:  # a mix over the trap bank: strata like `trap&multi_turn` or `trap_type=missing_tool`
        pool, traps = list(traps), []
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
    n_traps, drawn, taken = (n if recipe["kind"] == "trap" and not recipe["mix"] else n_traps), [], set()
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
    taken |= {t["id"] for t in got}
    rest = n - len(got)
    quotas = _quotas(recipe["mix"], max(rest, 0)) if recipe["mix"] else {}
    preds = {k: F.compile_filter(k, presets) for k in quotas}
    # scarcest stratum first so overlapping strata do not starve it
    # (a stratum that names trap features, e.g. `trap&multi_turn`, may also draw from the trap bank when kind is not trap)
    cands = {k: pool + (traps if recipe["mix"] and re.search(r"trap|tier|variant|difficulty", k) and recipe["kind"] != "trap" else []) for k in quotas}
    for name in sorted(quotas, key=lambda k: (sum(preds[k](t["features"]) for t in cands[k]), k)):
        cand = [t for t in cands[name] if t["id"] not in taken and preds[name](t["features"])]
        pick = rng.sample(cand, min(quotas[name], len(cand)))
        taken |= {t["id"] for t in pick}
        drawn += pick
        short(name, quotas[name], len(pick), sum(preds[name](t["features"]) for t in cands[name]))
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
        hidden = list((t.get("trap") or {}).get("hidden_tools") or [])
        sizes_t = without_hidden(sizes, hidden)  # hidden tools are not exposed, so they do not count toward the budget
        required = [s for s in t["servers"]["required"] if s in sizes and s not in missing]
        if shared:
            req, dist = shared
            required, dist = [s for s in req if s not in missing], [s for s in dist if s not in missing]
            loaded = _place(required, dist, opts["position"], random.Random(f"{seed}|shared|pos"))
        else:
            cands = [u for u in universe if u not in set(required) | missing]
            order = graph.order(strategy, set(t["servers"]["required"]), t["persona"].get("file", ""), cands, rng)
            dist = _select(required, order, budget, sizes_t)
            # placement depends only on (seed, task, server), never on the budget: a bigger budget adds servers around
            # the same relative arrangement instead of reshuffling, so budgets of one task differ only in what was added
            loaded = _place_stable(required, dist, opts["position"], seed, t["id"])
        tools, tokens = sum(sizes_t[s]["tools"] for s in loaded), sum(sizes_t[s]["tokens"] for s in loaded)
        t["servers"] = {"required": required, "distractors": [s for s in loaded if s not in required], "loaded": loaded}
        t["tool_budget"] = {"tools": tools, "tokens": tokens, "servers": len(loaded), "relevant_position": opts["position"],
                            "target": budget, "label": label(budget)}
        t["writes"]["write_tools_loaded"] = sorted(w for s in loaded for w in sizes_t[s]["write_tools"])
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
    from .harness.base import system_prompt
    variant = recipe["harness_options"].get("system_prompt", "default")
    (d / "prompt.json").write_text(json.dumps({
        "turns": [t["text"] for t in task["turns"]], "system": system_prompt(variant, date.today()), "system_prompt": variant},
        indent=1, ensure_ascii=False))
    if harness:
        harness.write_task(d, task, recipe)
        trap = task.get("trap") or {}
        if trap.get("hidden_tools") or trap.get("inject"):  # hub-side trap settings: tell whoever runs run.sh by hand
            with open(d / "run.sh", "a") as fh:
                if trap.get("hidden_tools"):
                    fh.write(f"# NOTE: this task needs a hub started with  --hide-tools {','.join(trap['hidden_tools'])}\n")
                if trap.get("inject"):
                    fh.write(f"# NOTE: this task needs a hub started with  --inject '{trap['inject']['tool']}=<trap.inject.text>' (see tasks.jsonl)\n")
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
            "system_prompt": recipe["harness_options"].get("system_prompt", "default"),
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
    p.add_argument("--seed", type=int), p.add_argument("--tasks", help="number of tasks, or 'all' (ladder recipes)")
    p.add_argument("--mix", help="override the mix, e.g. 'simple: 25%%, write: 25%%, systems>=3: 10%%'")
    p.add_argument("--budget", help="override tools.budget, e.g. tokens=30000, tools=200, servers=10, tokens=5000,25000 (grid)")
    p.add_argument("--distractors", choices=DISTRACTORS)
    p.add_argument("--dry-run", action="store_true", help="print the plan (strata, budgets, servers per task); write nothing")


def main(a):
    recipe = load(a.recipe)
    if a.seed is not None:
        recipe["seed"] = a.seed
    if a.tasks is not None:
        recipe["tasks"] = a.tasks if a.tasks == "all" else int(a.tasks)
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
          f"harness {r['harness']}, system prompt {r['harness_options'].get('system_prompt', 'default')}, tools {r['tools']}")
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
