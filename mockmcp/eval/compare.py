"""`eval compare A B`: compare two graded runs (two models, or one model under two settings) task by task.

A and B are run folders or grid parents (budget grid sub-runs, paired by sub-run name). Writes compare.md and
compare.json (COMPARE, see compare_data) to a new folder, never into A or B; with --html also charts/*.svg (comparison
charts), charts-a/*.svg and charts-b/*.svg (each side's single-report charts) and compare.html (overview and split screen).
--verdicts NAME reads judge.NAME.json on both sides, as `eval report --verdicts` does."""
import argparse
import json
import webbrowser
from pathlib import Path

from .grade import run_dirs
from .report import load_run, render, should_open, verdict_file
from .tags import by_tag_compare, md_compare


def add_args(p):
    p.add_argument("a_dir", type=Path, metavar="A", help="run folder or grid parent (side A)")
    p.add_argument("b_dir", type=Path, metavar="B", help="run folder or grid parent (side B)")
    p.add_argument("--labels", help='two comma-separated side names, e.g. "haiku,sonnet" (default: the model each side served)')
    p.add_argument("--verdicts", metavar="NAME", help="compare the verdicts in judge.NAME.json on both sides instead of judge.json; "
                   "tasks without that file are left out and counted")
    p.add_argument("--out", type=Path, help="output folder (default: compare-<A>-vs-<B> next to A)")
    p.add_argument("--html", action="store_true", help="also write the charts and a self-contained compare.html")
    p.add_argument("--open", action=argparse.BooleanOptionalAction, default=None,
                   help="open compare.html in a browser (default: only on an interactive terminal with a display, not in CI)")


def default_out(a_dir: Path, b_dir: Path, verdicts: str | None = None) -> Path:
    """compare-<A>-vs-<B> next to A (suffixed .<NAME> for --verdicts)."""
    return a_dir.parent / (f"compare-{a_dir.name}-vs-{b_dir.name}" + (verdict_file(verdicts)[len("judge"):-len(".json")] if verdicts else ""))


def _side(d: Path, verdicts: str | None) -> tuple[list[Path], list[dict], int]:
    """(run folders, rows read without writing anything, graded tasks excluded for lacking the --verdicts file)."""
    rds, skipped = run_dirs(d), []
    if not rds:
        raise ValueError(f"no run folders under {d}")
    rows = [r for rd in rds for r in load_run(rd, verdicts, skipped, write=False)]
    if not rows:
        raise ValueError(f"no graded tasks under {d}" + (f" with {verdict_file(verdicts)}" if verdicts else "; run `eval grade` first"))
    return rds, [{**r, "dir": str(Path(r["dir"]).resolve())} for r in rows], len(skipped)


def default_labels(a_rows: list[dict], b_rows: list[dict], a_dir: Path, b_dir: Path) -> list[str]:
    """Each side's served model (or the recorded model, else the folder name); the folder name is appended when they tie.
    A harness may serve helper models too, so served ids matching the recorded alias (sonnet -> ...-sonnet-...) win."""
    def one(rows, d):
        served = sorted({m for r in rows for m in r.get("models_served") or []})
        named = sorted({r["model"] for r in rows if r.get("model") and r["model"] != "?"})
        main = [m for m in served if any(n in m for n in named)]
        return ", ".join(main or served or named) or d.name
    la, lb = one(a_rows, a_dir), one(b_rows, b_dir)
    return [f"{la} ({a_dir.name})", f"{lb} ({b_dir.name})"] if la == lb else [la, lb]


def _report(rows: list[dict], root: Path, source: str, excluded: int) -> dict:
    """REPORT of one side, exactly as `eval report` builds it (task file paths relative to `root`)."""
    from . import report_data
    _, summary = render(rows, root, None if source == "judge.json" else source, excluded)
    return report_data.build(rows, root, summary, source)


def _shown(p: Path) -> str:
    """A run folder as shown on the page: relative to the current directory when inside it (runs/x), else as given."""
    r, cwd = p.resolve(), Path.cwd().resolve()
    return str(r.relative_to(cwd)) if r.is_relative_to(cwd) else str(p)


def build(a_dir: Path, b_dir: Path, out: Path, labels=None, verdicts=None) -> tuple[dict, dict, dict]:
    """(COMPARE, REPORT A, REPORT B). Runs pair as compare_data pairs them (two single runs
    always; grids by sub-run name). Raises ValueError for a single run against a grid, an output folder inside A or B,
    or a side with no graded tasks."""
    from . import compare_data
    given = [Path(a_dir), Path(b_dir)]
    a_dir, b_dir, out = Path(a_dir).resolve(), Path(b_dir).resolve(), Path(out).resolve()
    for d in (a_dir, b_dir):
        if out == d or out.is_relative_to(d):
            raise ValueError(f"output folder {out} is inside {d}: compare never writes into the runs it reads")
    (ra, a_rows, a_ex), (rb, b_rows, b_ex) = _side(a_dir, verdicts), _side(b_dir, verdicts)
    single_a, single_b = ra == [a_dir], rb == [b_dir]
    if single_a != single_b:
        grid, one = (b_dir, a_dir) if single_a else (a_dir, b_dir)
        raise ValueError(f"{one} is a single run but {grid} is a grid of runs; compare a run with a run, or a grid with a grid "
                         f"(pass one sub-run of {grid} instead)")
    if labels:
        labels = [s.strip() for s in labels.split(",")] if isinstance(labels, str) else list(labels)
        if len(labels) != 2 or not all(labels):
            raise ValueError(f"--labels needs two names separated by a comma, got {labels!r}")
    labels = labels or default_labels(a_rows, b_rows, a_dir, b_dir)
    source = verdict_file(verdicts)
    a_rep, b_rep = _report(a_rows, a_dir, source, a_ex), _report(b_rows, b_dir, source, b_ex)
    cmp = compare_data.build(a_rep, b_rep, labels, out=out, sources=[a_dir, b_dir])   # file links relative to `out`
    cmp["sources"] = [_shown(p) for p in given]
    cmp["excluded"] = [a_ex, b_ex]
    return cmp, a_rep, b_rep


def _pct(x) -> str:
    return "-" if x is None else f"{100 * x:.1f}%"


def _ratio(x) -> str:
    return "-" if x is None else f"{x:.2f}×"


def render_md(cmp: dict) -> str:
    """compare.md: a headline table per paired run, pass rates by tag, then the tasks that flip between the sides, grouped."""
    la, lb = cmp["labels"]
    src = cmp.get("verdict_source") or "judge.json"
    L = [f"# Eval comparison: {la} vs {lb}", "", f"- A: **{la}** ({cmp.get('sources', ['?', '?'])[0]})",
         f"- B: **{lb}** ({cmp.get('sources', ['?', '?'])[1]})", f"- verdicts: {src}"]
    ex = cmp.get("excluded") or [0, 0]
    if any(ex):
        L.append(f"- left out for lacking {src}: {ex[0]} graded tasks in A, {ex[1]} in B")
    un = cmp.get("unpaired") or {}
    for side, key in (("A", "only_a_runs"), ("B", "only_b_runs")):
        if un.get(key):
            L.append(f"- runs only in {side}, not compared: {', '.join(un[key])}")
    L += ["", "## Headline", "", "Δ is B minus A in percentage points; p is McNemar's exact test on the tasks only one side "
          "passed (small p, e.g. under 0.05: the difference is unlikely to be chance). Ratios are B / A totals.", "",
          f"| run | budget | common tasks | {la} pass | {lb} pass | Δ pts | p | both pass | only {la} | only {lb} | both fail "
          "| cost × | input tokens × | time × | tool calls × |", "|" + "---|" * 15]
    for r in cmp.get("runs", []) + ([cmp["all"]] if len(cmp.get("runs", [])) > 1 and cmp.get("all") else []):
        h, ra = r.get("head_to_head") or {}, r.get("ratio") or {}
        d, p = (r.get("delta") or {}).get("pass_rate"), r.get("mcnemar_p")
        L.append(f"| {r['run']} | {r.get('budget') or '-'} | {r.get('common', 0)} | {_pct(r['a'].get('pass_rate'))} | "
                 f"{_pct(r['b'].get('pass_rate'))} | {'-' if d is None else f'{100 * d:+.1f}'} | "
                 f"{'-' if p is None else f'{p:.3g}'} | {h.get('both_pass', 0)} | "
                 f"{h.get('a_only', 0)} | {h.get('b_only', 0)} | {h.get('both_fail', 0)} | {_ratio(ra.get('cost_usd'))} | "
                 f"{_ratio(ra.get('input_tokens'))} | {_ratio(ra.get('seconds'))} | {_ratio(ra.get('tool_calls'))} |")
    odd = [r for r in cmp.get("runs", []) if r.get("only_a") or r.get("only_b")]
    if odd:
        L += ["", "Tasks on one side only are counted, never compared: "
              + "; ".join(f"{r['run']}: {r.get('only_a', 0)} only in {la}, {r.get('only_b', 0)} only in {lb}" for r in odd) + "."]
    if bt := md_compare(by_tag_compare(cmp), la, lb):
        L += [""] + bt[:-1]
    tasks = cmp.get("tasks", [])
    groups = ((f"{lb} passes, {la} fails", lambda t: t["change"] == "b_only"),
              (f"{la} passes, {lb} fails", lambda t: t["change"] == "a_only"),
              ("Both fail, differently", lambda t: t["change"] == "both_fail" and t["a"]["outcome"] != t["b"]["outcome"]),
              ("Both pass, differently", lambda t: t["change"] == "both_pass" and t["a"]["outcome"] != t["b"]["outcome"]))
    L += ["", "## Tasks that flip", ""]
    if not any(f(t) for t in tasks for _, f in groups):
        L.append("Every common task has the same outcome on both sides.")
    for title, f in groups:
        ts = [t for t in tasks if f(t)]
        if ts:
            L += [f"### {title} ({len(ts)})", ""]
            L += [f"- `{t['task_id']}` ({t['run']}, {t.get('kind', '?')}): {t['a']['outcome']} → {t['b']['outcome']}" for t in ts]
            L.append("")
    return "\n".join(L).rstrip() + "\n"


def _write_svgs(d: Path, svgs: dict[str, str]) -> None:
    d.mkdir(exist_ok=True)
    for old in d.glob("*.svg"):
        if old.stem not in svgs:
            old.unlink()   # a chart that no longer applies
    for name, svg in svgs.items():
        (d / f"{name}.svg").write_text(svg)


def write_outputs(a_dir: Path, b_dir: Path, out: Path, labels=None, verdicts=None, html: bool = False,
                  open_: bool | None = None) -> dict[str, Path]:
    """compare.md and compare.json in `out` (created); with `html` also charts/, charts-a/, charts-b/ (*.svg) and
    compare.html (opened when report.should_open(open_)). Nothing is written into A or B. Returns the paths written."""
    out = Path(out)
    cmp, a_rep, b_rep = build(a_dir, b_dir, out, labels, verdicts)
    out.mkdir(parents=True, exist_ok=True)
    paths = {"md": out / "compare.md", "json": out / "compare.json"}
    paths["md"].write_text(render_md(cmp))
    paths["json"].write_text(json.dumps(cmp, indent=1))
    if html:
        from . import charts, compare_charts, compare_html
        svgs, svgs_a, svgs_b = compare_charts.render_all(cmp), charts.render_all(a_rep), charts.render_all(b_rep)
        for key, sub, s in (("charts", "charts", svgs), ("charts_a", "charts-a", svgs_a), ("charts_b", "charts-b", svgs_b)):
            paths[key] = out / sub
            _write_svgs(paths[key], s)
        paths["html"] = out / "compare.html"
        paths["html"].write_text(compare_html.render_html(cmp, svgs, svgs_a, svgs_b))
        if should_open(open_):
            webbrowser.open(paths["html"].resolve().as_uri())
    return paths


def main(a) -> int:
    out = a.out or default_out(a.a_dir, a.b_dir, getattr(a, "verdicts", None))
    try:
        paths = write_outputs(a.a_dir, a.b_dir, out, getattr(a, "labels", None), getattr(a, "verdicts", None),
                              getattr(a, "html", False), getattr(a, "open", None))
    except ValueError as e:
        print(f"eval compare: {e}")
        return 1
    print(paths["md"].read_text().split("## Tasks that flip")[0] + "\n".join(f"{k}: {p}" for k, p in paths.items()))
    return 0
