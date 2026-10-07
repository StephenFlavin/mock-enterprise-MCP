"""Headless Claude Code (`claude -p`) as the harness under test.

Each task is a conversation: turn 0 is `claude -p <text> --session-id <uuid>`, every follow-up `claude -p <text> --resume <uuid>`
(verified on 2.1.293: both work together with -p; the system prompt is re-sent on each resume). The model sees only the system
prompt and the turn texts; MCP servers come from mcp.json (HTTP, one per loaded server, in load order).

Tool search: Claude Code defers MCP tool definitions behind a search tool when many are loaded. It is controlled by the env var
ENABLE_TOOL_SEARCH (found in the 2.1.x binary and the settings docs): `false` = every tool definition is in context,
`true`/`auto`/`auto:N` = deferral (auto: only when definitions exceed N% of the window, default 10). Recipe option
harness_options.tool_search: off (default, ENABLE_TOOL_SEARCH=false) | auto (ENABLE_TOOL_SEARCH=auto).
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

from ...bench import SYSTEM
from ...spec import WORLD
from .base import Harness

TOOL_SEARCH = {"off": "false", "auto": "auto"}
DEFAULTS = {"tool_search": "off", "max_turns": 25, "timeout": 900}


def system_prompt() -> str:
    return SYSTEM.format(company=WORLD["company"], today=date.today().isoformat())


def _cmd(task: dict, mcp: Path, model: str, prompt: str, sid: str, first: bool, max_turns: int, system: str) -> list[str]:
    servers = task["servers"]["loaded"]
    return ["claude", "-p", prompt, "--session-id" if first else "--resume", sid, "--model", model,
            "--mcp-config", str(mcp), "--strict-mcp-config", "--tools", "",
            "--allowedTools", *[f"mcp__{s}" for s in servers], "--setting-sources", "",
            "--output-format", "stream-json", "--verbose", "--max-turns", str(max_turns),
            "--append-system-prompt", system]


def _session_id(task: dict) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "mockmcp-eval/" + task["id"]))


def parse_turn(stream: str) -> dict:
    """One turn's stream-json -> {"text","usage","cost_usd","duration_ms","num_turns","error","calls"}."""
    out = {"text": "", "usage": {}, "cost_usd": 0.0, "duration_ms": 0, "num_turns": 0, "error": None, "calls": 0}
    seen_result = False
    for line in stream.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        msg = ev.get("message")
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


class ClaudeCode(Harness):
    name = "claude-code"

    def write_task(self, task_dir: Path, task: dict, recipe: dict) -> None:
        task_dir.mkdir(parents=True, exist_ok=True)
        opts = {**DEFAULTS, **(recipe.get("harness_options") or {})}
        system = system_prompt()
        turns = [t["text"] for t in task["turns"]]
        (task_dir / "prompt.json").write_text(json.dumps({"system": system, "turns": turns}, indent=2))
        servers = {s: {"type": "http", "url": f"http://127.0.0.1:{{PORT}}/{s}/mcp"} for s in task["servers"]["loaded"]}
        (task_dir / "mcp.json").write_text(json.dumps({"mcpServers": servers}, indent=2))
        sid = _session_id(task)
        lines = ["#!/usr/bin/env bash",
                 f"# Re-run one task by hand. Needs a hub:  python -m mockmcp serve --only {' '.join(task['servers']['loaded'])} --port $PORT",
                 "# Usage: PORT=8800 MODEL=haiku ./run.sh   (conversation turns run in order, resumed by session id)",
                 "set -u", 'cd "$(dirname "$0")"', 'PORT="${PORT:-8800}"', 'MODEL="${MODEL:-haiku}"',
                 f"export ENABLE_TOOL_SEARCH={TOOL_SEARCH[opts['tool_search']]}",
                 'WORK="$(mktemp -d)"; trap \'rm -rf "$WORK"\' EXIT',
                 'sed "s/{PORT}/$PORT/g" mcp.json > "$WORK/mcp.json"',
                 f"SYSTEM={shlex.quote(system)}", ""]
        for i, text in enumerate(turns):
            c = _cmd(task, Path("$WORK/mcp.json"), "$MODEL", text, sid, i == 0, opts["max_turns"], "$SYSTEM")
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
        with tempfile.TemporaryDirectory(prefix="eval-") as work, open(task_dir / "transcript.jsonl", "w") as tf:
            mcp = Path(work) / "mcp.json"
            mcp.write_text((task_dir / "mcp.json").read_text().replace("{PORT}", str(port)))
            for i, text in enumerate(turns):
                cmd = _cmd(task, mcp, model, text, sid, i == 0, opts["max_turns"], system["system"])
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
                if r["error"] and stderr.strip():
                    r["error"] += f" [{stderr.strip()[-200:]}]"
                answers.append({**r, "started_at": t0, "finished_at": t1})
                if r["error"] and not r["text"]:
                    err = f"turn {i}: {r['error']}"
                    break  # a failed turn leaves nothing to resume from
        res = {"turns": answers, "error": err, "model": model, "session_id": sid}
        (task_dir / "answers.json").write_text(json.dumps(res, indent=2))
        return res
