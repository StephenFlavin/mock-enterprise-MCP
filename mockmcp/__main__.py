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
    s.add_argument("--record", metavar="PATH", help="append every served tool call to PATH as JSONL (or env MOCKMCP_RECORD)")
    s.add_argument("--hide-tools", metavar="SRV.TOOL,...", help="eval: do not expose these tools (left out of tools/list, calls rejected)")
    s.add_argument("--inject", metavar="SRV.TOOL=TEXT", action="append", default=[],
                   help="eval: plant TEXT in every result of SRV.TOOL (in a notes-like field); repeatable")
    sub.add_parser("stdio", help="serve one system over stdio").add_argument("id")
    c = sub.add_parser("check", help="lint + run examples + scenarios")
    c.add_argument("ids", nargs="*")
    c.add_argument("--partial", action="store_true", help="allow missing catalogue tools/questions (staged builds)")
    g = sub.add_parser("gen", help="regenerate data/*.csv")
    g.add_argument("ids", nargs="*", help="systems (default with --verify: all, master first)")
    g.add_argument("--verify", action="store_true", help="regenerate into a temp dir and fail if data/ differs")
    sub.add_parser("reset", help="delete the persistent write overlay ($MOCKMCP_STATE, default state/)").add_argument("ids", nargs="*")
    sub.add_parser("catalog", help="rebuild catalog/tools.csv from the persona docs")
    sub.add_parser("brief", help="print a system's tools and the questions that use them").add_argument("id")
    p = sub.add_parser("profile", help="MCP client config for one persona, e.g. profile 01 4")
    p.add_argument("file_no"), p.add_argument("persona_no")
    p.add_argument("--url", default="http://127.0.0.1:8800")
    r = sub.add_parser("run", help="call one tool: run <id> <tool> '{\"arg\": 1}'")
    r.add_argument("id"), r.add_argument("tool"), r.add_argument("args", nargs="?", default="{}")
    r.add_argument("--keep", action="store_true", help="keep writes in $MOCKMCP_STATE (default state/)")
    b = sub.add_parser("bench", help="run a model on each server alone against bench/cases/<id>.yaml")
    b.add_argument("ids", nargs="*", help="systems (default: every system with cases)")
    b.add_argument("--validate", action="store_true", help="only check cases against the data (no model)")
    b.add_argument("--model", default="haiku"), b.add_argument("--workers", type=int, default=6)
    b.add_argument("--only", help="run cases whose id contains this")
    b.add_argument("--coverage", action="store_true", help="which question slices have a case (no model)")
    from .eval import cli as eval_cli
    eval_cli.add_parser(sub)
    a = ap.parse_args()

    if a.cmd == "eval":
        sys.exit(eval_cli.main(a) or 0)
    if a.cmd == "serve":
        import uvicorn
        from .server import Engine, hub_app
        try:
            bad = [x for x in a.inject if "=" not in x]
            if bad:
                raise ValueError(f"--inject needs SRV.TOOL=TEXT, got {bad}")
            eng = Engine(a.only, record=a.record, hide=[h for h in (a.hide_tools or "").split(",") if h.strip()],
                         inject=dict(x.split("=", 1) for x in a.inject))
        except ValueError as e:
            sys.exit(str(e))
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
        from .gen import generate, verify
        from .spec import system_ids
        if a.verify:
            bad = 0
            for sid in a.ids or ["master", *system_ids()]:
                probs = verify(sid)
                bad += bool(probs)
                print(f"{'FAIL' if probs else 'ok  '} {sid}" + "".join(f"\n  - {x}" for x in probs))
            sys.exit(1 if bad else 0)
        if not a.ids:
            sys.exit("gen: name the systems to regenerate (or use --verify)")
        for sid in a.ids:
            print(sid, generate(sid))
    elif a.cmd == "reset":
        from .db import PERSISTENT_STATE as STATE
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
        if a.keep:
            db.STATE = db.PERSISTENT_STATE
        else:
            tmp = tempfile.TemporaryDirectory()
            db.STATE = Path(tmp.name)
        text, err = Engine([a.id]).call(a.id, a.tool, json.loads(a.args))
        print(("ERROR: " if err else "") + text)
        sys.exit(1 if err else 0)
    elif a.cmd == "bench":
        from . import bench
        ids = a.ids or sorted(f.stem for f in bench.CASES.glob("*.yaml"))
        if a.coverage:
            cov = bench.coverage()
            rows = [(s, *cov[s]) for s in (a.ids or sorted(cov))]
            for s, need, have in rows:
                missing = sorted(need - have)
                print(f"{s:18} {len(have):3}/{len(need):<3}" + (f"  missing: {' '.join(missing[:12])}{' …' if len(missing) > 12 else ''}" if missing else ""))
            n, h = sum(len(r[1]) for r in rows), sum(len(r[2]) for r in rows)
            print(f"\n{h}/{n} question slices have a case ({100 * h / max(n, 1):.0f}%)")
            sys.exit(0)
        if a.validate:
            bad = 0
            for sid in ids:
                probs = bench.validate(sid)
                bad += bool(probs)
                print(f"{'FAIL' if probs else 'ok  '} {sid} ({len(bench.load(sid))} cases)" + "".join(f"\n  - {x}" for x in probs))
            sys.exit(1 if bad else 0)
        bench.run(ids, a.model, a.workers, a.only)


if __name__ == "__main__":
    main()
