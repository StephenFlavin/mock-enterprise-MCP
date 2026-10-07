"""`eval run <run_dir>`: run every task through a harness against its own recording hub.

Per task: free port -> `python -m mockmcp serve --only <loaded> --port P --record <task>/trace.jsonl` (fresh process = fresh
ephemeral write state, identical data) -> wait for HTTP -> harness.run_task -> stop hub. Resume-safe: tasks that already have
answers.json are skipped unless --rerun."""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import harness as harnesses
from ..spec import ROOT


def add_args(p):
    p.add_argument("run_dir")
    p.add_argument("--model", default="haiku")
    p.add_argument("--harness", default=None, help="default: the recipe's harness, else claude-code")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--only", help="tasks whose id contains this")
    p.add_argument("--limit", type=int, help="run at most n tasks")
    p.add_argument("--rerun", action="store_true", help="redo tasks that already have answers.json")
    p.add_argument("--keep-hub", action="store_true", help="leave each hub running afterwards (debugging)")


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def injections(task: dict) -> dict[str, str]:
    """injected traps: {"<server>.<tool>": text} the hub plants in that tool's results (trap.inject: {tool, text, asks})."""
    inj = (task.get("trap") or {}).get("inject")
    return {inj["tool"]: inj["text"]} if inj else {}


def start_hub(task_dir: Path, servers: list[str], port: int, timeout: float = 120, hide: list[str] | None = None,
              inject: dict[str, str] | None = None) -> subprocess.Popen:
    env = {k: v for k, v in os.environ.items() if k not in ("MOCKMCP_STATE", "MOCKMCP_RECORD")}
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    log = open(task_dir / "hub.log", "w")
    cmd = [sys.executable, "-m", "mockmcp", "serve", "--only", *servers, "--port", str(port), "--record", str(task_dir / "trace.jsonl")]
    if hide:  # missing_tool/hidden traps: the tool exists in the system but is not exposed for this task
        cmd += ["--hide-tools", ",".join(hide)]
    for tool, text in (inject or {}).items():  # injected traps: planted instruction inside a tool result
        cmd += ["--inject", f"{tool}={text}"]
    proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=log, stderr=log)
    end = time.time() + timeout
    while time.time() < end:
        if proc.poll() is not None:
            raise RuntimeError(f"hub exited with {proc.returncode}: {(task_dir / 'hub.log').read_text()[-300:]}")
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2).read()
            return proc
        except OSError:
            time.sleep(0.2)
    proc.kill()
    raise RuntimeError("hub did not start in time")


def stop_hub(proc: subprocess.Popen):
    proc.terminate()
    try:
        proc.wait(10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def trace_len(task_dir: Path) -> int:
    f = task_dir / "trace.jsonl"
    return sum(1 for _ in open(f)) if f.exists() else 0


def run_one(run: Path, task: dict, h, model: str, opts: dict, keep_hub: bool) -> dict:
    td = run / task["id"].replace("/", "_")
    t0, hub = time.time(), None
    try:
        (td / "trace.jsonl").unlink(missing_ok=True)
        port = free_port()
        hub = start_hub(td, task["servers"]["loaded"], port, hide=(task.get("trap") or {}).get("hidden_tools") or None,
                        inject=injections(task))
        ans = h.run_task(td, task, port, model, opts)
    except Exception as e:  # harness/hub crash: record it, never lose the other tasks
        ans = {"turns": [], "error": f"{type(e).__name__}: {e}"[:500], "model": model}
        (td / "answers.json").write_text(json.dumps(ans, indent=2))
    finally:
        if hub and not keep_hub:
            stop_hub(hub)
    return {"id": task["id"], "turns": len(ans["turns"]), "of": len(task["turns"]), "calls": trace_len(td),
            "cost": sum(t.get("cost_usd") or 0 for t in ans["turns"]), "secs": time.time() - t0, "error": ans.get("error")}


def main(a):
    root = Path(a.run_dir)
    if not (root / "tasks.jsonl").exists():  # a budget grid: run every sub-run
        subs = sorted(p.parent for p in root.glob("*/tasks.jsonl"))
        if not subs:
            raise SystemExit(f"{root}: no tasks.jsonl (build it with: python -m mockmcp eval recipe ...)")
        for sub in subs:
            print(f"== {sub.name}", flush=True)
            a.run_dir = str(sub)
            main(a)
        return
    run = root
    tasks = [json.loads(l) for l in (run / "tasks.jsonl").read_text().splitlines() if l.strip()]
    recipe = yaml.safe_load((run / "recipe.yaml").read_text()) if (run / "recipe.yaml").exists() else {}
    h = harnesses.get(a.harness or recipe.get("harness") or "claude-code")
    opts = recipe.get("harness_options") or {}
    tasks = [t for t in tasks if not a.only or a.only in t["id"]]
    todo = [t for t in tasks if a.rerun or not (run / t["id"].replace("/", "_") / "answers.json").exists()]
    todo = todo[:a.limit] if a.limit else todo
    print(f"{len(todo)} tasks to run ({len(tasks) - len(todo)} skipped) with {h.name} {a.model}, {a.workers} workers", flush=True)
    started, results = datetime.now(timezone.utc).isoformat(), []
    with ThreadPoolExecutor(a.workers) as ex:
        for r in ex.map(lambda t: run_one(run, t, h, a.model, opts, a.keep_hub), todo):
            results.append(r)
            print(f"{r['id']:32} turns {r['turns']}/{r['of']}  calls {r['calls']:3}  ${r['cost']:.3f}  {r['secs']:.0f}s"
                  + (f"  ERROR {r['error']}" if r["error"] else ""), flush=True)
    prev = {}
    if (run / "run.json").exists():
        prev = json.loads((run / "run.json").read_text())
    (run / "run.json").write_text(json.dumps({
        "model": a.model, "harness": h.name, "started": prev.get("started") or started,
        "finished": datetime.now(timezone.utc).isoformat(), "tasks_run": prev.get("tasks_run", 0) + len(results),
        "errors": prev.get("errors", 0) + sum(bool(r["error"]) for r in results),
        "tool_calls": prev.get("tool_calls", 0) + sum(r["calls"] for r in results),
        "cost_usd": round(prev.get("cost_usd", 0) + sum(r["cost"] for r in results), 4)}, indent=2))
