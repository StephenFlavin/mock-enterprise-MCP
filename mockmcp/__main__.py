"""CLI. python -m mockmcp <command> — see README."""
import argparse
import json
import shutil
import sys


def main():
    ap = argparse.ArgumentParser(prog="mockmcp")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve", help="host every built system at http://HOST:PORT/<id>/mcp")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8800)
    s.add_argument("--only", nargs="*", help="system ids to host (default: all)")
    sub.add_parser("stdio", help="serve one system over stdio").add_argument("id")
    c = sub.add_parser("check", help="lint + run examples + scenarios")
    c.add_argument("ids", nargs="*")
    c.add_argument("--partial", action="store_true", help="allow missing catalogue tools/questions (staged builds)")
    sub.add_parser("gen", help="regenerate data/*.csv").add_argument("ids", nargs="+")
    sub.add_parser("reset", help="delete write overlay (state/)").add_argument("ids", nargs="*")
    sub.add_parser("catalog", help="rebuild catalog/tools.csv from the persona docs")
    sub.add_parser("brief", help="print a system's tools and the questions that use them").add_argument("id")
    p = sub.add_parser("profile", help="MCP client config for one persona, e.g. profile 01 4")
    p.add_argument("file_no"), p.add_argument("persona_no")
    p.add_argument("--url", default="http://127.0.0.1:8800")
    r = sub.add_parser("run", help="call one tool: run <id> <tool> '{\"arg\": 1}'")
    r.add_argument("id"), r.add_argument("tool"), r.add_argument("args", nargs="?", default="{}")
    r.add_argument("--keep", action="store_true", help="keep writes (default: discard)")
    a = ap.parse_args()

    if a.cmd == "serve":
        import uvicorn
        from .server import Engine, hub_app
        eng = Engine(a.only)
        print(f"{len(eng.systems)} systems on http://{a.host}:{a.port}/<id>/mcp", file=sys.stderr)
        uvicorn.run(hub_app(eng, a.host), host=a.host, port=a.port, log_level="warning")
    elif a.cmd == "stdio":
        import anyio
        from .server import Engine, run_stdio
        anyio.run(run_stdio, Engine([a.id]), a.id)
    elif a.cmd == "check":
        from .check import check
        from .spec import system_ids
        bad = 0
        for sid in a.ids or system_ids():
            probs = check(sid, a.partial)
            bad += bool(probs)
            print(f"{'FAIL' if probs else 'ok  '} {sid}" + "".join(f"\n  - {x}" for x in probs))
        sys.exit(1 if bad else 0)
    elif a.cmd == "gen":
        from .gen import generate
        for sid in a.ids:
            print(sid, generate(sid))
    elif a.cmd == "reset":
        from .db import STATE
        for d in ([STATE / i for i in a.ids] if a.ids else [STATE]):
            shutil.rmtree(d, ignore_errors=True)
    elif a.cmd == "catalog":
        from .catalog import write
        write()
    elif a.cmd == "brief":
        from .catalog import brief
        print(brief(a.id))
    elif a.cmd == "profile":
        from .catalog import profile
        ids = profile(a.file_no, a.persona_no)
        print(json.dumps({"mcpServers": {i: {"type": "http", "url": f"{a.url}/{i}/mcp"} for i in ids}}, indent=2))
    elif a.cmd == "run":
        import tempfile
        from pathlib import Path
        from . import db
        from .server import Engine
        tmp = None
        if not a.keep:
            tmp = tempfile.TemporaryDirectory()
            db.STATE = Path(tmp.name)
        text, err = Engine([a.id]).call(a.id, a.tool, json.loads(a.args))
        print(("ERROR: " if err else "") + text)
        sys.exit(1 if err else 0)


if __name__ == "__main__":
    main()
