"""Eval runner pieces that need no model: recording, hub subprocess, claude-code task files, stream parsing."""
import json
import threading
import urllib.request

import pytest

from mockmcp import db
from mockmcp.eval import harness, runner
from mockmcp.eval.harness import claude_code
from mockmcp.eval.record import Recorder
from mockmcp.server import Engine

TASK = {"id": "slc-cmms:10:Q1", "kind": "slice", "servers": {"loaded": ["cmms", "ap"]},
        "turns": [{"text": "Which stoppages did AST-DC2-SHT-03 have in the last 40 days?"}, {"text": "And the cost?"}]}
STOPPAGES = ("list_unplanned_stoppages", {"asset_id": "AST-DC2-SHT-03", "date_from": "-40d"})


@pytest.fixture(autouse=True)
def tmp_state(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "STATE", tmp_path / "state")


def lines(f):
    return [json.loads(x) for x in f.read_text().splitlines()]


def test_engine_records_trace_calls(tmp_path):
    f = tmp_path / "t" / "trace.jsonl"
    eng = Engine(["cmms"], record=str(f))
    text, err = eng.call("cmms", *STOPPAGES)
    eng.call("cmms", "no_such_tool", {})
    a, b = lines(f)
    assert (a["server"], a["tool"], a["args"], a["rw"], a["is_error"], a["result"]) == ("cmms", STOPPAGES[0], STOPPAGES[1], "R", err, text)
    assert a["ts"] > 1e9 and b["is_error"] and b["tool"] == "no_such_tool"
    w = next(r for r in Recorder(tmp_path / "x").rw.items() if r[1] == "W")
    assert Recorder(tmp_path / "y").rw[w[0]] == "W"


def test_recording_is_thread_safe(tmp_path):
    f = tmp_path / "trace.jsonl"
    eng = Engine(["cmms"], record=str(f))
    ts = [threading.Thread(target=lambda: [eng.call("cmms", *STOPPAGES) for _ in range(5)]) for _ in range(6)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(lines(f)) == 30


def test_env_enables_recording(tmp_path, monkeypatch):
    monkeypatch.setenv("MOCKMCP_RECORD", str(tmp_path / "e.jsonl"))
    Engine(["cmms"]).call("cmms", *STOPPAGES)
    assert len(lines(tmp_path / "e.jsonl")) == 1


def rpc(port, sid, method, params, n=1):
    req = urllib.request.Request(f"http://127.0.0.1:{port}/{sid}/mcp", method="POST",
                                 data=json.dumps({"jsonrpc": "2.0", "id": n, "method": method, "params": params}).encode(),
                                 headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def test_hub_subprocess_serves_and_records(tmp_path):
    port = runner.free_port()
    proc = runner.start_hub(tmp_path, ["cmms"], port)
    try:
        init = rpc(port, "cmms", "initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                                "clientInfo": {"name": "t", "version": "0"}})
        assert init["result"]["serverInfo"]["name"] == "cmms"
        r = rpc(port, "cmms", "tools/call", {"name": STOPPAGES[0], "arguments": STOPPAGES[1]}, 2)
        assert "Bearing failure" in r["result"]["content"][0]["text"]
    finally:
        runner.stop_hub(proc)
    assert proc.poll() is not None
    assert [c["tool"] for c in lines(tmp_path / "trace.jsonl")] == [STOPPAGES[0]]


def test_claude_code_write_task(tmp_path):
    h = harness.get("claude-code")
    h.write_task(tmp_path, TASK, {"harness_options": {"tool_search": "auto"}})
    p = json.loads((tmp_path / "prompt.json").read_text())
    assert p["turns"] == [t["text"] for t in TASK["turns"]]
    assert p["system"].startswith("You are an assistant at ") and "tool" not in p["system"].lower() and "trap" not in p["system"].lower()
    mcp = json.loads((tmp_path / "mcp.json").read_text())["mcpServers"]
    assert list(mcp) == ["cmms", "ap"] and mcp["ap"] == {"type": "http", "url": "http://127.0.0.1:{PORT}/ap/mcp"}
    sh = (tmp_path / "run.sh").read_text()
    assert "ENABLE_TOOL_SEARCH=auto" in sh and "--session-id" in sh and "--resume" in sh and "mcp__cmms mcp__ap" in sh
    assert (tmp_path / "run.sh").stat().st_mode & 0o100
    import subprocess
    assert subprocess.run(["bash", "-n", str(tmp_path / "run.sh")]).returncode == 0
    with pytest.raises(KeyError):
        harness.get("nope")


def test_parse_turn():
    stream = "\n".join(json.dumps(x) for x in [
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "1", "name": "mcp__cmms__x", "input": {}}]}},
        {"type": "result", "subtype": "success", "is_error": False, "result": "Two stoppages.", "total_cost_usd": 0.01,
         "duration_ms": 1234, "num_turns": 2, "usage": {"input_tokens": 5, "output_tokens": 7, "cache_read_input_tokens": 9}}])
    r = claude_code.parse_turn(stream)
    assert (r["text"], r["calls"], r["cost_usd"], r["usage"]["cache_read"], r["error"]) == ("Two stoppages.", 1, 0.01, 9, None)
    assert claude_code.parse_turn("garbage")["error"].startswith("no result")
    bad = claude_code.parse_turn(json.dumps({"type": "result", "subtype": "error_max_turns", "is_error": True, "num_turns": 9}))
    assert "error_max_turns" in bad["error"]


def test_run_task_records_harness_failure(tmp_path, monkeypatch):
    h = harness.get("claude-code")
    h.write_task(tmp_path, TASK, {})
    monkeypatch.setenv("PATH", "/nonexistent")
    with pytest.raises(FileNotFoundError):  # runner.run_one turns this into answers.json "error"
        h.run_task(tmp_path, TASK, 1, "haiku", {})


def test_harness_registry_and_recipe_flag(tmp_path):
    from mockmcp.eval import harness, recipe as R
    assert "claude-code" in harness.available()
    assert harness.get("claude-code").name == "claude-code"
    with pytest.raises(KeyError):
        harness.get("nope")
    with pytest.raises(ValueError):
        R.resolve({"harness": "nope"})


def test_custom_harness_registers_and_is_selectable():
    from mockmcp.eval import harness
    from mockmcp.eval.harness.base import _REGISTRY

    @harness.register
    class Dummy(harness.Harness):
        name = "dummy-test"
    try:
        assert "dummy-test" in harness.available() and isinstance(harness.get("dummy-test"), Dummy)
    finally:
        _REGISTRY.pop("dummy-test")
