"""Copy docs/examples into public/examples (archives extracted in place, so the reports' per-task links resolve) and
write src/data/examples.json, the figures the site's pages show, read from each example's report.json.gz /
compare.json.gz. Standard library only; run from site/ as `python3 -I scripts/prepare_examples.py`.

Every number comes from the reports. Where a report has no aggregate for a figure the script derives it, and names
the field in examples.json's `computed` list. Output is deterministic: running it twice gives identical files."""
import gzip
import json
import math
import os
import shutil
import sys
import tarfile
from collections import Counter
from pathlib import Path, PurePosixPath

SITE = Path(__file__).resolve().parents[1]
ROOT = SITE.parent
SRC = ROOT / "docs/examples"
PUBLIC = SITE / "public/examples"
OUT = SITE / "src/data/examples.json"

# What each folder is: docs/examples/README.md and runs/examples.sh (the report files carry neither the folder name nor
# the harness options). `source` is the run folder each example was made from, as compare.json's `sources` name it.
SINGLE = {
    "haiku": {"title": "Haiku, tool search off", "source": "runs/ts-off", "tool_search": False},
    "haiku-toolsearch": {"title": "Haiku, tool search on", "source": "runs/ts-on", "tool_search": True},
    "sonnet": {"title": "Sonnet, tool search off", "source": "runs/s160-sonnet", "tool_search": False},
}
PAIRS = {
    "haiku-vs-haiku-toolsearch": {"title": "Haiku: tool search off vs on"},
    "haiku-vs-sonnet": {"title": "Haiku vs Sonnet"},
}
# Comparison rows by task family, as `eval compare`'s "By tag" table (mockmcp/eval/tags.py) labels them.
KIND_LABEL = {"scenario": "scenarios", "slice": "slices", "trap": "traps"}
MIN_N = 10   # tags.MIN_N: fewer tasks than this is a small sample
# The reports link task folders such as `scn-01:4:Q1` as `scn-01%3A4%3AQ1`. GitHub Pages decodes the whole path and
# finds the `:` name; Vite's server (`npm run preview`) decodes with decodeURI, which leaves `%3A` alone, and looks for
# the literal name. SITE_ENCODED_ALIASES=1 gives each such folder a `%3A`-named twin (hard links in public/, about
# 113 MB more in dist/) so those links work in a local preview; the deployed site doesn't need it.
ENCODED_ALIASES = os.environ.get("SITE_ENCODED_ALIASES") == "1"
COMPUTED = [
    "budgets[].label: the report's budget label without the trailing ' tokens'",
    "runs.*.pass_rate.by_budget: runs[].passed / runs[].tasks (the report has no per-budget rate), rounded to 4 places",
    "comparisons.*.by_kind: pass rates and McNemar p per task kind and question type over the common tasks, all budgets"
    " pooled, as mockmcp/eval/tags.by_tag_compare does (compare.json does not store them)",
    "*.files[].bytes: file sizes on disk",
]


def die(msg: str):
    sys.exit(f"prepare_examples: {msg}")


def need(d: dict, *path):
    """d[path[0]][path[1]]...; exits naming the missing field."""
    cur = d
    for i, k in enumerate(path):
        if not isinstance(cur, (dict, list)) or (isinstance(cur, dict) and k not in cur):
            die(f"missing field {'.'.join(map(str, path[:i + 1]))}")
        cur = cur[k]
    return cur


def load(p: Path) -> dict:
    if not p.is_file():
        die(f"missing {p.relative_to(ROOT)}")
    with gzip.open(p, "rt", encoding="utf-8") as f:
        return json.load(f)


def mcnemar(a_only: int, b_only: int) -> float:
    """Exact two-sided McNemar p, as mockmcp/eval/compare_data.mcnemar."""
    n, k = a_only + b_only, min(a_only, b_only)
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def safe_extract(archive: Path, dest: Path):
    """Extract a .tar.gz into dest, refusing absolute paths, `..`, links and anything but files and folders."""
    with tarfile.open(archive, "r:gz") as tf:
        members = tf.getmembers()
        for m in members:
            p = PurePosixPath(m.name)
            if p.is_absolute() or ".." in p.parts or not (m.isfile() or m.isdir()):
                die(f"refusing {m.name!r} in {archive.relative_to(ROOT)}")
            if p.name == "index.html":
                die(f"{archive.relative_to(ROOT)} holds an index.html, which would shadow the docs page")
        kw = {"filter": "data"} if hasattr(tarfile, "data_filter") else {}
        tf.extractall(dest, members=members, **kw)


def copy_public():
    """public/examples/<name>/ = docs/examples/<name>/ with every archive extracted beside it; no index.html."""
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir(parents=True)
    for src in sorted(SRC.iterdir()):
        if src.is_dir():
            shutil.copytree(src, PUBLIC / src.name)
    for archive in sorted(PUBLIC.glob("*/*.tar.gz")):
        safe_extract(archive, archive.parent)
    if ENCODED_ALIASES:
        for d in sorted(PUBLIC.glob("*/tokens-*/*:*")):
            alias = d.with_name(d.name.replace(":", "%3A"))
            alias.mkdir()
            for f in sorted(d.iterdir()):
                try:
                    os.link(f, alias / f.name)
                except OSError:
                    shutil.copy2(f, alias / f.name)
    if bad := sorted(PUBLIC.rglob("index.html")):
        die(f"public copy holds {bad[0]}, which would clash with the docs page")


def files(name: str, names: list[str]) -> list[dict]:
    out = []
    for n in names:
        p = SRC / name / n
        if not p.is_file():
            die(f"missing docs/examples/{name}/{n}")
        out.append({"name": n, "path": f"examples/{name}/{n}", "bytes": p.stat().st_size})
    return out


def charts(name: str, folder: str) -> list[str]:
    return [f"examples/{name}/{folder}/{p.name}" for p in sorted((SRC / name / folder).glob("*.svg"))]


def budget_label(b: str) -> str:
    if not b.endswith(" tokens"):
        die(f"unexpected budget label {b!r}")
    return b[: -len(" tokens")]


def single(name: str, meta: dict) -> tuple[dict, list[dict]]:
    rep = load(SRC / name / "report.json.gz")
    if need(rep, "report_version") != 1:
        die(f"{name}: report_version {rep['report_version']} (expected 1)")
    s = need(rep, "summary")
    runs = need(rep, "runs")
    budgets = [{"key": need(r, "run"), "label": budget_label(need(r, "budget")), "budget": r["budget"],
                "median_tokens": need(r, "median_tokens"), "median_tools": need(r, "median_tools")} for r in runs]
    tasks = need(s, "n")
    if sum(need(r, "tasks") for r in runs) != tasks or sum(need(r, "passed") for r in runs) != need(s, "passed"):
        die(f"{name}: per-budget tasks/passed do not add up to the summary")
    by = lambda f: {r["run"]: f(r) for r in runs}
    out = {
        "title": meta["title"], "source": meta["source"], "tool_search": meta["tool_search"],
        "model": need(s, "model"), "judge": need(s, "judge"), "tasks": tasks, "passed": need(s, "passed"),
        "pass_rate": {"all": need(s, "pass_rate"), "by_budget": by(lambda r: round(r["passed"] / r["tasks"], 4))},
        "passed_by_budget": by(lambda r: r["passed"]), "tasks_by_budget": by(lambda r: r["tasks"]),
        "cost_usd": {"all": need(s, "cost_usd"), "by_budget": by(lambda r: need(r, "metrics", "cost_usd", "total"))},
        "cost_per_pass_usd": {"all": need(s, "metrics", "cost_per_pass_usd"),
                              "by_budget": by(lambda r: need(r, "metrics", "cost_per_pass_usd"))},
        "judge_cost_usd": need(s, "judge_cost_usd"),
        "outcomes": dict(need(s, "outcomes")),
        "outcomes_by_budget": by(lambda r: dict(need(r, "outcomes"))),
        "trap_pass_rate": need(s, "trap_pass_rate"),
        "trap_handled": need(s, "trap_handled"), "trap_handled_known": need(s, "trap_handled_known"),
        "unsafe": need(s, "unsafe"), "fabricated": need(s, "fabricated"),
        "tool_calls": need(s, "metrics", "tool_calls", "total"),
        "input_tokens": need(s, "metrics", "input_tokens", "total"),
        "report": f"examples/{name}/report.html",
        "files": files(name, ["report.html", "report.md", "report.json.gz", "answers.tar.gz", "grading.tar.gz"]),
        "charts": charts(name, "charts"),
    }
    return out, budgets, rep


def by_kind(cmp: dict) -> list[dict]:
    """Per task kind and question type over the common tasks (all budgets pooled), as tags.by_tag_compare: kind from the
    comparison task, question type from side A's embedded report entry (B's must agree)."""
    feats = {s: {need(t, "key"): need(t, "features") for t in need(cmp, s, "tasks")} for s in "ab"}
    groups: dict[tuple, list] = {}
    for t in need(cmp, "tasks"):
        fa, fb = feats["a"][need(t, "a", "key")], feats["b"][need(t, "b", "key")]
        if fa.get("type") != fb.get("type"):
            die(f"task {t['task_id']} has question type {fa.get('type')} in A, {fb.get('type')} in B")
        groups.setdefault(("kind", need(t, "kind")), []).append(t)
        if fa.get("type"):
            groups.setdefault(("question", fa["type"]), []).append(t)
    order = lambda k: (k[0] != "kind", list(KIND_LABEL).index(k[1]) if k[0] == "kind" else 0, k[1])
    rows = []
    for fam, v in sorted(groups, key=order):
        ts = groups[fam, v]
        h = Counter(need(t, "change") for t in ts)
        n, pa, pb = len(ts), h["both_pass"] + h["a_only"], h["both_pass"] + h["b_only"]
        rows.append({"family": fam, "kind": v.lower(),
                     "label": KIND_LABEL[v] if fam == "kind" else f"question: {v.lower()}",
                     "n": n, "a_passed": pa, "b_passed": pb, "a": round(pa / n, 4), "b": round(pb / n, 4),
                     "delta": round((pb - pa) / n, 4), "p": round(mcnemar(h["a_only"], h["b_only"]), 6),
                     "small": n < MIN_N})
    return rows


def side(r: dict) -> dict:
    return {"pass_rate": need(r, "pass_rate"), "passed": need(r, "passed"), "tasks": need(r, "tasks"),
            "cost_usd": need(r, "cost_usd"), "cost_per_pass_usd": need(r, "cost_per_pass_usd"),
            "outcomes": dict(need(r, "outcomes"))}


def row(r: dict) -> dict:
    return {"a": need(r, "a", "pass_rate"), "b": need(r, "b", "pass_rate"), "delta": need(r, "delta", "pass_rate"),
            "p": need(r, "mcnemar_p"), "common": need(r, "common"), "head_to_head": dict(need(r, "head_to_head")),
            "cost_ratio": need(r, "ratio", "cost_usd"), "side_a": side(r["a"]), "side_b": side(r["b"])}


def pair(name: str, meta: dict, by_source: dict, single_reps: dict) -> tuple[dict, list[str]]:
    cmp = load(SRC / name / "compare.json.gz")
    if need(cmp, "compare_version") != 1:
        die(f"{name}: compare_version {cmp['compare_version']} (expected 1)")
    sources, labels = need(cmp, "sources"), need(cmp, "labels")
    ab = []
    for i, s in enumerate(sources):
        if s not in by_source:
            die(f"{name}: source {s} is not one of the single-run examples")
        ex = by_source[s]
        emb, own = need(cmp, "ab"[i], "summary"), need(single_reps[ex], "summary")
        if any(emb.get(k) != own.get(k) for k in ("n", "passed", "pass_rate", "cost_usd", "outcomes")):
            die(f"{name}: side {'ab'[i]} does not match docs/examples/{ex}/report.json.gz")
        ab.append(ex)
    if any(need(cmp, "unpaired", k) for k in ("only_a_runs", "only_b_runs")):
        die(f"{name}: unpaired runs")
    runs = need(cmp, "runs")
    out = {
        "title": meta["title"], "a": ab[0], "b": ab[1], "labels": {"a": labels[0], "b": labels[1]},
        "pass_rate": {"all": row(need(cmp, "all")), "by_budget": {need(r, "run"): row(r) for r in runs}},
        "by_kind": by_kind(cmp),
        "report": f"examples/{name}/compare.html",
        "files": files(name, ["compare.html", "compare.md", "compare.json.gz"]),
        "charts": charts(name, "charts"),
    }
    return out, [need(r, "budget") for r in runs]


def screenshots() -> list[str]:
    return [f"examples/screenshots/{p.name}" for p in sorted((SRC / "screenshots").glob("*.png"))]


def build() -> dict:
    runs, reps, budgets = {}, {}, None
    for name, meta in SINGLE.items():
        runs[name], b, reps[name] = single(name, meta)
        if budgets is None:
            budgets = [{k: x[k] for k in ("key", "label", "budget")} for x in b]
        elif [x["key"] for x in b] != [x["key"] for x in budgets] or [x["budget"] for x in b] != [x["budget"] for x in budgets]:
            die(f"{name}: budget ladder differs from {next(iter(SINGLE))}")
        runs[name]["budgets"] = {x["key"]: {"median_tokens": x["median_tokens"], "median_tools": x["median_tools"]} for x in b}
    if [int(x["key"].removeprefix("tokens-")) for x in budgets] != sorted(int(x["key"].removeprefix("tokens-")) for x in budgets):
        die("budgets are not in ladder order")
    by_source = {m["source"]: n for n, m in SINGLE.items()}
    comps = {}
    for name, meta in PAIRS.items():
        comps[name], cb = pair(name, meta, by_source, reps)
        if cb != [x["budget"] for x in budgets]:
            die(f"{name}: budget labels differ from the single reports")
    return {"generated_from": "docs/examples", "computed": COMPUTED, "budgets": budgets, "runs": runs,
            "comparisons": comps, "screenshots": screenshots(),
            "outcome_order": list(need(reps[next(iter(SINGLE))], "summary", "definitions", "outcomes"))[::-1],
            "outcome_definitions": dict(need(reps[next(iter(SINGLE))], "summary", "definitions", "outcomes"))}


def main():
    if not SRC.is_dir():
        die(f"missing {SRC}")
    data = build()
    copy_public()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} and {PUBLIC.relative_to(ROOT)}/ ({len(data['runs'])} runs, "
          f"{len(data['comparisons'])} comparisons)")


if __name__ == "__main__":
    main()
