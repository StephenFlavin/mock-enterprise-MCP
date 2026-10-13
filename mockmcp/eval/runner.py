"""`eval run <run_dir>`: run every task through a harness against its own recording hub.

Per task: free port -> `python -m mockmcp serve --only <loaded> --port P --record <task>/trace.jsonl` (fresh process = fresh
ephemeral write state, identical data) -> wait for HTTP -> harness.run_task -> stop hub. Resume-safe: tasks that already have
answers.json are skipped unless --rerun. An answer that measures the account or the harness rather than the model is never
kept (moved to answers.failed.json, so the task runs again on resume): out of credit, a refused key or a harness setup error
stop the whole run at once (run the same command again to resume); overload, rate limits and lost connections only skip that
task. --retry-errors also re-runs tasks whose stored answer failed that way (runs written before this rule)."""
import re
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
from .schema import task_cost
from ..spec import ROOT


def add_args(p):
    p.add_argument("run_dir")
    p.add_argument("--model", default="haiku", help="model under test, as the folder's harness names it "
                   "(claude-code: an alias such as haiku / sonnet / opus, or a full model id); default haiku")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--only", help="tasks whose id contains this")
    p.add_argument("--limit", type=int, help="run at most n tasks")
    p.add_argument("--rerun", action="store_true", help="redo tasks that already have answers.json")
    p.add_argument("--keep-hub", action="store_true", help="leave each hub running afterwards (debugging)")
    p.add_argument("--retry-errors", action="store_true", help="also re-run tasks whose stored answer failed for account or "
                   "infrastructure reasons (credit, auth, overload, rate limit, connection, harness setup); never model timeouts")


# Errors that say nothing about the model. FATAL stops the run (nothing after it can succeed); TRANSIENT only drops that answer.
FATAL = re.compile(r"credit balance|billing|insufficient.{0,20}(credit|fund|quota)|quota exceeded|usage.?limit|session limit|hit your .{0,30}limit|invalid.{0,10}api.?key|"
                   r"authentication|unauthori[sz]ed|permission_error|/login|harness setup", re.I)
TRANSIENT = re.compile(r"overloaded|rate.?limit|\b(429|500|502|503|504|529)\b|connection (error|reset|refused)|ECONNRESET|"
                       r"socket hang up|api_error|internal server error|harness crash", re.I)


def failure_kind(error: str | None) -> str | None:
    """"fatal" / "transient" for errors that are not the model's doing (see FATAL, TRANSIENT), else None."""
    if not error:
        return None
    return "fatal" if FATAL.search(error) else "transient" if TRANSIENT.search(error) else None


def answer_failure(ans: dict) -> str | None:
    """failure_kind of an answer: its own error, else the first turn error that is not the model's doing (a usage-limit
    message comes back as a turn's text, so the turn looks answered and the harness carries on)."""
    return failure_kind(ans.get("error")) or next(filter(None, (failure_kind(t.get("error")) for t in ans.get("turns") or [])), None)


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
        ans = {"turns": [], "error": f"harness crash: {type(e).__name__}: {e}"[:500], "model": model}
        (td / "answers.json").write_text(json.dumps(ans, indent=2))
    finally:
        if hub and not keep_hub:
            stop_hub(hub)
    kind = answer_failure(ans)
    if kind and (td / "answers.json").exists():   # not the model's answer: keep it aside, run the task again next time
        (td / "answers.json").replace(td / "answers.failed.json")
    err = ans.get("error") or next((f"turn {i}: {t['error']}" for i, t in enumerate(ans["turns"]) if failure_kind(t.get("error"))), None)
    return {"id": task["id"], "turns": len(ans["turns"]), "of": len(task["turns"]), "calls": trace_len(td),
            "cost": task_cost(ans["turns"]), "secs": time.time() - t0, "error": err, "failure": kind}


def stored_failure(task_dir: Path) -> str | None:
    """failure_kind of a stored answers.json (None when it is a real answer or missing)."""
    try:
        return answer_failure(json.loads((task_dir / "answers.json").read_text()))
    except (OSError, ValueError):
        return None


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
    h = harnesses.get(recipe.get("harness") or "claude-code")  # the harness the folder was written for (eval recipe --harness)
    opts = recipe.get("harness_options") or {}
    tasks = [t for t in tasks if not a.only or a.only in t["id"]]
    td = lambda t: run / t["id"].replace("/", "_")
    todo = [t for t in tasks if a.rerun or not (td(t) / "answers.json").exists()
            or getattr(a, "retry_errors", False) and stored_failure(td(t))]
    todo = todo[:a.limit] if a.limit else todo
    print(f"{len(todo)} tasks to run ({len(tasks) - len(todo)} skipped) with {h.name} {a.model}, {a.workers} workers", flush=True)
    started, results, stop = datetime.now(timezone.utc).isoformat(), [], []
    def one(t):   # workers check `stop` before starting, so a fatal error ends the run within one task per worker
        if stop:
            return None
        r = run_one(run, t, h, a.model, opts, a.keep_hub)
        if r["failure"] == "fatal":
            stop.append(r["error"])
        return r
    with ThreadPoolExecutor(a.workers) as ex:
        for r in ex.map(one, todo):
            if r is None:
                continue
            results.append(r)
            print(f"{r['id']:32} turns {r['turns']}/{r['of']}  calls {r['calls']:3}  ${r['cost']:.3f}  {r['secs']:.0f}s"
                  + (f"  ERROR {r['error']}" if r["error"] else "")
                  + (f"  [{r['failure']}: answer not kept, runs again on resume]" if r["failure"] else ""), flush=True)
    prev = {}
    if (run / "run.json").exists():
        prev = json.loads((run / "run.json").read_text())
    (run / "run.json").write_text(json.dumps({
        "model": a.model, "harness": h.name, "started": prev.get("started") or started,
        "finished": datetime.now(timezone.utc).isoformat(), "tasks_run": prev.get("tasks_run", 0) + len(results),
        "errors": prev.get("errors", 0) + sum(bool(r["error"]) for r in results),
        "tool_calls": prev.get("tool_calls", 0) + sum(r["calls"] for r in results),
        "cost_usd": round(prev.get("cost_usd", 0) + sum(r["cost"] for r in results), 4)}, indent=2))
    if stop:
        raise SystemExit(f"stopped: {stop[0]}\nNothing after this can succeed. Fix it, then run the same command again: "
                         f"finished tasks are kept and only the rest run.")
