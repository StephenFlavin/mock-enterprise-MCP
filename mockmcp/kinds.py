"""One function per tool kind. Each returns (rows | text, total | None, notes)."""
import importlib.util
import json
import re

import jinja2

from .args import ArgError
from .db import DUCK_TYPES
from .fmt import cell
from .spec import WORLD

AUTO_STAMP = ("created_at", "created_date", "created_on", "raised_at", "raised_date", "requested_at",
              "submitted_at", "sent_at", "updated_at")
_jinja = jinja2.Environment(undefined=jinja2.ChainableUndefined, trim_blocks=True, lstrip_blocks=True)
_jinja.filters["money"] = lambda v, cur="£": f"{cur}{float(v or 0):,.0f}"
_jinja.filters["num"] = lambda v, dp=0: f"{float(v or 0):,.{dp}f}"
_hooks: dict[str, object] = {}


def _q(name: str) -> str:
    return f'"{name}"'


def run_select(eng, system, tool, args, vals):
    where, params = [], {}
    sid, t = eng.db.table(system.id, tool.from_)
    for n, a in args.items():
        v = vals.get(n)
        if n == "limit" or v is None:
            continue
        col = a.col or n
        coltype = t.cols[col].type if col in t.cols else a.type
        params[n] = v
        if a.op == "like":  # every word must appear, in any order
            words = re.findall(r"\w[\w.-]*", str(v)) or [str(v)]
            del params[n]
            for i, w in enumerate(words):
                params[f"{n}_{i}"] = f"%{w}%"
                where.append(f"CAST({_q(col)} AS VARCHAR) ILIKE ${n}_{i}")
        elif a.op == "in" or a.type == "list":
            where.append(f"list_contains(${n}, CAST({_q(col)} AS VARCHAR))")
        elif a.type in ("date", "timestamp"):
            where.append(f"CAST({_q(col)} AS DATE) {a.op} CAST(${n} AS DATE)")
        elif coltype in ("str", "text", "enum"):
            where.append(f"lower(CAST({_q(col)} AS VARCHAR)) {a.op} lower(${n})")
        else:
            where.append(f"{_q(col)} {a.op} CAST(${n} AS {DUCK_TYPES[coltype]})")
    frm = f'"{sid}"."{tool.from_.split(".")[-1]}"'
    w = f" WHERE {' AND '.join(where)}" if where else ""
    total = eng.db.query(system.id, f"SELECT count(*) FROM {frm}{w}", params)[1][0][0]
    cols = ", ".join(_q(c) for c in tool.columns) if tool.columns else "*"
    order = f" ORDER BY {tool.order}" if tool.order else ""
    params["_lim"] = vals.get("limit") or tool.limit
    rows = eng.db.rows(system.id, f"SELECT {cols} FROM {frm}{w}{order} LIMIT $_lim", params)
    return rows, total, []


def run_sql(eng, system, tool, args, vals):
    rows = eng.db.rows(system.id, tool.sql, vals)
    return rows[: tool.limit], len(rows), []


def _template(v, vals):
    if isinstance(v, str):
        if v == "$as_of":
            return WORLD["as_of"]
        return re.sub(r"\{(\w+)\}", lambda m: str(vals.get(m.group(1)) or ""), v)
    return v


def run_insert(eng, system, tool, args, vals):
    sid, t = eng.db.table(system.id, tool.table)
    tname = tool.table.split(".")[-1]
    sig = (system.id, tool.name, json.dumps(vals, sort_keys=True, default=str))
    if sig in eng.created:
        return [eng.created[sig]], None, ["already created by an identical earlier call; nothing new written"]
    key = t.keys[0]
    row = {c: None for c in t.cols}
    row |= {c: _template(v, vals) for c, v in tool.defaults.items()}
    row |= {n: v for n, v in vals.items() if n in t.cols and v is not None}
    for c in AUTO_STAMP:
        if c in row and row[c] is None:
            row[c] = WORLD["as_of"]
    last = eng.db.query(system.id, f"""SELECT max(TRY_CAST(regexp_extract({_q(key)}, '(\\d+)$', 1) AS BIGINT))
                                      FROM "{sid}"."{tname}" WHERE starts_with({_q(key)}, $p)""",
                        {"p": tool.id_prefix})[1][0][0]
    row[key] = f"{tool.id_prefix}{(last or 0) + 1:06d}"
    eng.db.append(system.id, tool.table, row, "insert")
    eng.created[sig] = row
    return [row], None, [f"Done. Created {tname} {row[key]}."]


def run_update(eng, system, tool, args, vals):
    sid, t = eng.db.table(system.id, tool.table)
    tname = tool.table.split(".")[-1]
    keyvals = {k: vals[tool.key_arg] for k in t.keys} if tool.key_arg else {k: vals[k] for k in t.keys}
    cond = " AND ".join(f"CAST({_q(k)} AS VARCHAR) = CAST(${k} AS VARCHAR)" for k in keyvals)
    cur = eng.db.rows(system.id, f'SELECT * FROM "{sid}"."{tname}" WHERE {cond}', keyvals)
    if not cur:
        raise ArgError(f"No {tname} with {', '.join(f'{k}={v}' for k, v in keyvals.items())}.")
    old, new = cur[0], dict(cur[0])
    new |= {c: _template(v, vals) for c, v in tool.set.items()}
    new |= {n: v for n, v in vals.items() if n in t.cols and n not in keyvals and v is not None}
    if "updated_at" in new:
        new["updated_at"] = WORLD["as_of"]
    eng.db.append(system.id, tool.table, new, "delete" if tool.delete else "update")
    label = ", ".join(map(str, keyvals.values()))
    if tool.delete:
        return f"Done. Deleted {tname} {label}.", None, []
    changes = [f"{c}: {cell(old[c]) or '(blank)'} → {cell(new[c])}" for c in t.cols
               if cell(old[c]) != cell(new[c]) and c != "updated_at"]
    return f"Done. Updated {tname} {label}.\n" + ("\n".join(changes) or "No fields changed."), None, []


def run_draft(eng, system, tool, args, vals):
    ctx = {"args": vals, "as_of": WORLD["as_of"], "company": WORLD["company"]}
    if isinstance(tool.sql, str):
        ctx["rows"] = eng.db.rows(system.id, tool.sql, vals)
        ctx["row"] = ctx["rows"][0] if ctx["rows"] else {}
    elif isinstance(tool.sql, dict):
        for name, q in tool.sql.items():
            ctx[name] = eng.db.rows(system.id, q, vals)
    ctx |= vals
    text = _jinja.from_string(tool.template).render(**ctx).strip()
    return "DRAFT (not sent or saved)\n\n" + text, None, []


class Ctx:
    """Passed to hooks.py functions."""

    def __init__(self, eng, system):
        self.eng, self.system_id, self.world, self.as_of = eng, system.id, WORLD, WORLD["as_of"]

    def q(self, sql: str, **params) -> list[dict]:
        return self.eng.db.rows(self.system_id, sql, params)


def run_py(eng, system, tool, args, vals):
    mod = _hooks.get(system.id)
    if mod is None:
        spec = importlib.util.spec_from_file_location(f"hooks_{system.id}", system.dir / "hooks.py")
        mod = _hooks[system.id] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    out = getattr(mod, tool.fn.split(".")[-1])(Ctx(eng, system), **vals)
    if isinstance(out, dict):
        out = [out]
    if isinstance(out, list):
        return out[: max(tool.limit, 50)], len(out), []
    return str(out), None, []


RUNNERS = {"select": run_select, "sql": run_sql, "insert": run_insert, "update": run_update,
           "draft": run_draft, "py": run_py}
