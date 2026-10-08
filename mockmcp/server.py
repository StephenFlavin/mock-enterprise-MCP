"""Engine (load systems, call tools) and MCP wiring: one low-level Server per system, hosted by one hub."""
import contextlib
import logging
import re
import time

import anyio
from mcp import types
from mcp.server import Server

from . import args as A
from .db import DB
from .kinds import RUNNERS
from .spec import WORLD, load_system, system_ids

log = logging.getLogger("mockmcp")


class Engine:
    def __init__(self, ids: list[str] | None = None, record: str | None = None, hide: list[str] | None = None,
                 inject: dict[str, str] | None = None):
        from .eval.record import Recorder
        self.rec = Recorder.make(record)  # eval: append every served call to a TraceCall JSONL
        self.db = DB()
        self.master = load_system("master")
        self.db.add(self.master)
        self.systems, self.tools, self.args = {}, {}, {}
        self.created: dict = {}
        for sid in ids or system_ids():
            self.add(sid)
        # eval: tools deliberately not exposed ("<server>.<tool>"): left out of tools/list and rejected when called
        self.hidden = {tuple(h.split(".", 1)) for h in hide or []}
        unknown = sorted(".".join(h) for h in self.hidden if h not in self.tools)
        if unknown:
            raise ValueError(f"--hide-tools: unknown tool(s) {unknown} (is the server loaded?)")
        # eval (injected traps): text planted in one tool's result ({"<server>.<tool>": text}), inside a notes-like field
        self.inject = {tuple(k.split(".", 1)): v for k, v in (inject or {}).items()}
        unknown = sorted(".".join(k) for k in self.inject if k not in self.tools)
        if unknown:
            raise ValueError(f"--inject: unknown tool(s) {unknown} (is the server loaded?)")

    def add(self, sid: str):
        s = load_system(sid)
        self.db.add(s)
        self.systems[sid] = s
        for t in s.tools:
            self.tools[(sid, t.name)] = t
            self.args[(sid, t.name)] = A.effective_args(t, s, self.master)

    def instructions(self, sid: str) -> str:
        return (self.systems[sid].instructions.strip() +
                f" Today is {WORLD['as_of']}. Money is {WORLD['currency']} unless a column says otherwise.")

    def mcp_tools(self, sid: str) -> list[types.Tool]:
        out = []
        for t in self.systems[sid].tools:
            if (sid, t.name) in self.hidden:
                continue
            ann = types.ToolAnnotations(read_only_hint=not t.writes,
                                        destructive_hint=t.writes and (t.delete or t.name.split("_")[0] in
                                                                       ("cancel", "delete", "block", "archive", "remove")),
                                        idempotent_hint=not t.writes)
            out.append(types.Tool(name=t.name, description=t.desc,
                                  input_schema=A.json_schema(self.args[(sid, t.name)]), annotations=ann))
        return out

    def call(self, sid: str, name: str, given: dict | None) -> tuple[str, bool]:
        """Run a tool. Returns (text, is_error). Never raises."""
        ts = time.time()
        text, err = self._call(sid, name, given)
        if self.rec:
            tool = self.tools.get((sid, name))
            self.rec.add(sid, name, given or {}, text, err, ts, bool(tool and tool.writes))
        return text, err

    def _call(self, sid: str, name: str, given: dict | None) -> tuple[str, bool]:
        from .fmt import render
        tool = self.tools.get((sid, name))
        if not tool or (sid, name) in self.hidden:
            return f"Unknown tool '{name}' in {sid}.", True
        s, args = self.systems[sid], self.args[(sid, name)]
        try:
            vals, notes = A.prepare(self.db, s, self.master, tool, args, given or {})
            rows, total, more = RUNNERS[tool.kind](self, s, tool, args, vals)
            if (sid, name) in self.inject:
                rows, more = embed(rows, self.inject[(sid, name)], more)
            narrow = [n for n, a in args.items() if n != "limit" and vals.get(n) is None]
            return render(rows, total, notes + more, narrow[:4]), False
        except A.ArgError as e:
            return f"{e}", True
        except Exception as e:  # a bug in the tool definition or data; tests should catch these
            log.exception("tool %s.%s failed", sid, name)
            return f"Internal error in {name}: {type(e).__name__}: {str(e).splitlines()[0][:300]}", True


NOTE_COLS = re.compile(r"note|comment|remark|message|description|detail|reason|text|summary", re.I)


def embed(rows, text: str, notes: list) -> tuple:
    """Plant `text` in a result the way real free text arrives: appended to the first row's notes-like column (a new
    `notes` column when there is none); a text result gets it as a trailing line, an empty one as a note."""
    if isinstance(rows, str):
        return rows.rstrip() + "\n" + text, notes
    if not rows:
        return rows, list(notes) + [text]
    rows = [dict(r) for r in rows]
    col = next((c for c in rows[0] if NOTE_COLS.search(c) and len(str(rows[0][c] or "")) + len(text) < 290), None)  # CSV cells cut at 300
    if col is None:
        col = next(n for n in ("notes", "comment", "remarks", "free_text") if n not in rows[0])
        for r in rows:
            r[col] = ""
    old = rows[0].get(col)
    rows[0][col] = f"{old} {text}" if old not in (None, "") else text
    return rows, notes


def build_server(eng: Engine, sid: str) -> Server:
    tools = eng.mcp_tools(sid)

    async def list_tools(ctx, params):
        return types.ListToolsResult(tools=tools)

    async def call_tool(ctx, params):
        text, err = await anyio.to_thread.run_sync(eng.call, sid, params.name, params.arguments)
        return types.CallToolResult(content=[types.TextContent(type="text", text=text)], is_error=err)

    return Server(sid, version="0.1", title=eng.systems[sid].name, instructions=eng.instructions(sid),
                  on_list_tools=list_tools, on_call_tool=call_tool)


def hub_app(eng: Engine, host: str = "127.0.0.1"):
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Mount, Route

    servers = {sid: build_server(eng, sid) for sid in eng.systems}
    routes = [Mount(f"/{sid}", app=srv.streamable_http_app(json_response=True, stateless_http=True, host=host))
              for sid, srv in servers.items()]
    index = "\n".join(f"/{sid}/mcp  {eng.systems[sid].name}  ({len(eng.mcp_tools(sid))} tools)" for sid in servers)
    routes.append(Route("/", lambda r: PlainTextResponse(index + "\n")))

    @contextlib.asynccontextmanager
    async def lifespan(app):
        async with contextlib.AsyncExitStack() as stack:
            for srv in servers.values():
                await stack.enter_async_context(srv.session_manager.run())
            yield

    return Starlette(routes=routes, lifespan=lifespan)


async def run_stdio(eng: Engine, sid: str):
    from mcp.server.stdio import stdio_server
    srv = build_server(eng, sid)
    async with stdio_server() as (r, w):
        await srv.run(r, w, srv.create_initialization_options())
