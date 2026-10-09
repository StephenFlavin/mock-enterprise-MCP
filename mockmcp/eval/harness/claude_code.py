"""Headless Claude Code (`claude -p`) as the harness under test.

Each task is a conversation: turn 0 is `claude -p <text> --session-id <uuid>`, every follow-up `claude -p <text> --resume <uuid>`
(verified on 2.1.293: both work together with -p; the system prompt is re-sent on each resume). The model sees only the system
prompt and the turn texts; MCP servers come from mcp.json (HTTP, one per loaded server, in load order). `--system-prompt`
REPLACES Claude Code's built-in agent prompt, so the model gets no instructions beyond base.SYSTEM_PROMPT.

Tool search: Claude Code defers MCP tool definitions behind a search tool when many are loaded. It is controlled by the env var
ENABLE_TOOL_SEARCH (found in the 2.1.x binary and the settings docs): `false` = every tool definition is in context,
`true`/`auto`/`auto:N` = deferral (auto: only when definitions exceed N% of the window, default 10). Recipe option
harness_options.tool_search: off (default, ENABLE_TOOL_SEARCH=false) | on (true: always deferred) | auto (auto).
Deferral needs Claude Code's own ToolSearch tool: `--tools ''` (no built-in tools, used so the model only has the MCP tools)
removes it too and silently keeps every definition in context (measured on 2.1.295: "hi" with all 96 servers is 493k input
tokens either way). So with tool search on, the harness allows exactly `--tools ToolSearch` (59.9k tokens for the same "hi"),
and every turn records whether ToolSearch was really offered (`tool_search_active`, from the stream's init event).
"""
import json
import os
import shlex
import subprocess
import tempfile
import time
import uuid
from datetime import date
from pathlib import Path

from .base import Harness, register, system_prompt as _system_prompt

SETUP_ERROR = "harness setup"   # an answer that measures the harness, not the model: the runner stops and keeps no answer
TOOL_SEARCH = {"off": "false", "on": "true", "auto": "auto"}
DEFAULTS = {"tool_search": "off", "max_turns": 25, "timeout": 900, "fake_clock": False}
# Claude Code adds its own "Today's date is <real date>" reminder even with --system-prompt, and CLAUDE_CODE_OVERRIDE_DATE has no
# effect in -p mode (tested on 2.1.x), so the model can see two dates when the world's today (spec.today(), a Wednesday) differs
# from the real one. fake_clock: true runs claude under libfaketime set to the world's today, which removes the second date. It is
# off by default: it needs libfaketime, and TLS fails where a proxy mints certificates dated today (as in sandboxes).
FAKETIME_LIBS = ("/usr/lib/x86_64-linux-gnu/faketime/libfaketime.so.1", "/usr/lib/faketime/libfaketime.so.1",
                 "/usr/local/lib/faketime/libfaketime.so.1", "/opt/homebrew/lib/faketime/libfaketime.1.dylib")


def clock_env(world_today: str) -> dict:
    """Environment that makes claude's clock read the world's today (same time of day); {} if libfaketime is missing."""
    lib = next((p for p in FAKETIME_LIBS if os.path.exists(p)), None)
    if not lib:
        return {}
    key = "DYLD_INSERT_LIBRARIES" if lib.endswith(".dylib") else "LD_PRELOAD"
    return {key: lib, "FAKETIME": f"@{world_today} {time.strftime('%H:%M:%S')}", "FAKETIME_DISABLE_SHM": "1",
            "DONT_FAKE_MONOTONIC": "1"}


def system_prompt(task: dict) -> str:
    """The full system prompt (replaces Claude Code's own; see base.SYSTEM_PROMPT)."""
    return _system_prompt(task)


def _cmd(task: dict, mcp: Path, model: str, prompt: str, sid: str, first: bool, max_turns: int, system: str,
         tool_search: str = "off") -> list[str]:
    servers, search = task["servers"]["loaded"], tool_search != "off"
    return ["claude", "-p", prompt, "--session-id" if first else "--resume", sid, "--model", model,
            "--mcp-config", str(mcp), "--strict-mcp-config", "--tools", "ToolSearch" if search else "",
            "--allowedTools", *[f"mcp__{s}" for s in servers], *(["ToolSearch"] if search else []), "--setting-sources", "",
            "--output-format", "stream-json", "--verbose", "--max-turns", str(max_turns),
            "--system-prompt", system]  # replaces Claude Code's built-in agent prompt: no hints


def _world_today(task_dir: Path) -> str:
    """The date the model is told (prompt.json), which is the world's today when the recipe was built."""
    import re
    m = re.search(r"\d{4}-\d\d-\d\d", json.loads((task_dir / "prompt.json").read_text()).get("system", ""))
    return m.group() if m else date.today().isoformat()


def _session_id(task: dict) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "mockmcp-eval/" + task["id"]))


def parse_turn(stream: str) -> dict:
    """One turn's stream-json -> {"text","usage","cost_usd","duration_ms","num_turns","error","calls"}."""
    out = {"text": "", "usage": {}, "cost_usd": 0.0, "duration_ms": 0, "num_turns": 0, "error": None, "calls": 0,
           "tool_search_active": None}
    seen_result = False
    for line in stream.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        msg = ev.get("message")
        if ev.get("type") == "system" and ev.get("subtype") == "init" and isinstance(ev.get("tools"), list):
            out["tool_search_active"] = "ToolSearch" in ev["tools"]
        if ev.get("type") == "assistant" and isinstance(msg, dict) and isinstance(msg.get("content"), list):
            out["calls"] += sum(p.get("type") == "tool_use" for p in msg["content"])
        if ev.get("type") == "result":
            seen_result = True
            u = ev.get("usage") or {}
            out.update(text=ev.get("result") or "", cost_usd=ev.get("total_cost_usd") or 0.0,
                       duration_ms=ev.get("duration_ms") or 0, num_turns=ev.get("num_turns") or 0,
                       usage={"input": u.get("input_tokens", 0), "output": u.get("output_tokens", 0),
                              "cache_read": u.get("cache_read_input_tokens", 0),
                              "cache_creation": u.get("cache_creation_input_tokens", 0)})
            sub = ev.get("subtype")
            if ev.get("is_error") or (sub and sub != "success"):
                out["error"] = f"{sub or 'error'}: {str(ev.get('result') or ev.get('errors') or '')[:300]}"
            out["stop_reason"] = ev.get("stop_reason")
    if not seen_result:
        out["error"] = "no result event (timeout or crash)"
    elif not out["text"] and not out["error"]:
        out["error"] = "empty answer"
    return out


@register
class ClaudeCode(Harness):
    name = "claude-code"

    def write_task(self, task_dir: Path, task: dict, recipe: dict) -> None:
        task_dir.mkdir(parents=True, exist_ok=True)
        opts = {**DEFAULTS, **(recipe.get("harness_options") or {})}
        system = system_prompt(task)
        turns = [t["text"] for t in task["turns"]]
        (task_dir / "prompt.json").write_text(json.dumps({"system": system, "turns": turns}, indent=2))
        servers = {s: {"type": "http", "url": f"http://127.0.0.1:{{PORT}}/{s}/mcp"} for s in task["servers"]["loaded"]}
        (task_dir / "mcp.json").write_text(json.dumps({"mcpServers": servers}, indent=2))
        sid = _session_id(task)
        trap = task.get("trap") or {}
        hub = " ".join(["python -m mockmcp serve --only", *task["servers"]["loaded"], "--port $PORT"]
                       + (["--hide-tools", ",".join(trap["hidden_tools"])] if trap.get("hidden_tools") else [])
                       + (["--inject", shlex.quote(f"{trap['inject']['tool']}={trap['inject']['text']}")] if trap.get("inject") else []))
        lines = ["#!/usr/bin/env bash",
                 f"# Re-run one task by hand. Needs a hub:  {hub}",
                 "# Usage: PORT=8800 MODEL=haiku ./run.sh   (conversation turns run in order, resumed by session id)",
                 "set -u", 'cd "$(dirname "$0")"', 'PORT="${PORT:-8800}"', 'MODEL="${MODEL:-haiku}"',
                 f"export ENABLE_TOOL_SEARCH={TOOL_SEARCH[opts['tool_search']]}",
                 *([f"export {k}={shlex.quote(v)}" for k, v in clock_env(_world_today(task_dir)).items()] if opts.get("fake_clock") else []),
                 'WORK="$(mktemp -d)"; trap \'rm -rf "$WORK"\' EXIT',
                 'sed "s/{PORT}/$PORT/g" mcp.json > "$WORK/mcp.json"',
                 f"SYSTEM={shlex.quote(system)}", ""]
        for i, text in enumerate(turns):
            c = _cmd(task, Path("$WORK/mcp.json"), "$MODEL", text, sid, i == 0, opts["max_turns"], "$SYSTEM", opts["tool_search"])
            q = [shlex.quote(x) if x not in ("$WORK/mcp.json", "$MODEL", "$SYSTEM") else f'"{x}"' for x in c]
            lines.append(f'(cd "$WORK" && {" ".join(q)}) | tee -a transcript.run.jsonl')
        sh = task_dir / "run.sh"
        sh.write_text("\n".join(lines) + "\n")
        sh.chmod(0o755)

    def run_task(self, task_dir: Path, task: dict, port: int, model: str, opts: dict) -> dict:
        opts = {**DEFAULTS, **(opts or {})}
        opts.setdefault("timeout", opts.get("timeout_s", DEFAULTS["timeout"]))
        if "timeout_s" in opts:
            opts["timeout"] = opts["timeout_s"]
        sid, system = _session_id(task), json.loads((task_dir / "prompt.json").read_text())
        turns, answers, err = system["turns"], [], None
        env = {**os.environ, "ENABLE_TOOL_SEARCH": TOOL_SEARCH[opts["tool_search"]]}
        if opts.get("fake_clock"):
            fake = clock_env(_world_today(task_dir))
            if not fake:
                raise RuntimeError("harness_options.fake_clock is on but libfaketime is not installed (e.g. apt install faketime)")
            env.update(fake)
        with tempfile.TemporaryDirectory(prefix="eval-") as work, open(task_dir / "transcript.jsonl", "w") as tf:
            mcp = Path(work) / "mcp.json"
            mcp.write_text((task_dir / "mcp.json").read_text().replace("{PORT}", str(port)))
            for i, text in enumerate(turns):
                cmd = _cmd(task, mcp, model, text, sid, i == 0, opts["max_turns"], system["system"], opts["tool_search"])
                t0 = time.time()
                try:
                    p = subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True, timeout=opts["timeout"])
                    stream, stderr = p.stdout, p.stderr
                except subprocess.TimeoutExpired as e:
                    dec = lambda b: b.decode(errors="replace") if isinstance(b, bytes) else (b or "")
                    stream, stderr = dec(e.stdout), f"timeout after {opts['timeout']}s"
                t1 = time.time()
                for line in stream.splitlines():
                    try:
                        ev = json.loads(line)
                        ev = ev if isinstance(ev, dict) else {"raw": line}
                    except ValueError:
                        ev = {"raw": line}
                    tf.write(json.dumps({"turn": i, **ev}) + "\n")
                r = parse_turn(stream)
                if r["tool_search_active"] is not None and r["tool_search_active"] != (opts["tool_search"] != "off"):
                    r["error"] = (f"{SETUP_ERROR}: tool_search {opts['tool_search']} but ToolSearch was "
                                  f"{'offered' if r['tool_search_active'] else 'not offered'} (Claude Code version or flags)")
                if r["error"] and stderr.strip():
                    r["error"] += f" [{stderr.strip()[-200:]}]"
                answers.append({**r, "started_at": t0, "finished_at": t1})
                if r["error"] and (not r["text"] or r["error"].startswith(SETUP_ERROR)):
                    err = f"turn {i}: {r['error']}"
                    break  # a failed turn leaves nothing to resume from
        res = {"turns": answers, "error": err, "model": model, "session_id": sid}
        (task_dir / "answers.json").write_text(json.dumps(res, indent=2))
        return res
