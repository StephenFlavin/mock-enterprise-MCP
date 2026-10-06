"""Argument resolution (inherit from columns), JSON Schema, and forgiving coercion for small models."""
import calendar
import difflib
import re
from datetime import date, datetime, timedelta

from .spec import WORLD, Arg, System, ToolSpec

AS_OF = date.fromisoformat(str(WORLD["as_of"]))
JSON_TYPES = {"str": "string", "text": "string", "enum": "string", "date": "string", "timestamp": "string",
              "int": "integer", "float": "number", "bool": "boolean", "list": "array"}
END_SUFFIX = ("_to", "_end", "_until", "_before", "end_date", "to_date")


class ArgError(Exception):
    pass


def _find_col(name: str, system: System, master: System, prefer: list[str]):
    tables = [(system, t) for t in prefer if t in system.tables]
    tables += [(system, t) for t in system.tables] + [(master, t) for t in master.tables]
    for s, t in tables:
        if name in s.tables[t].cols:
            return s.tables[t].cols[name]
    return None


def effective_args(tool: ToolSpec, system: System, master: System) -> dict[str, Arg]:
    """Final argument set for a tool, with type/desc/values inherited from same-named columns."""
    prefer = [x.split(".")[-1] for x in (tool.from_, tool.table) if x]
    raw: dict[str, Arg | None] = {}
    if tool.kind == "select":
        raw |= tool.filters
    if tool.kind == "update":
        tsys = master if (tool.table or "").startswith("master.") else system
        keys = tsys.tables[tool.table.split(".")[-1]].keys
        if tool.key_arg:
            raw[tool.key_arg] = Arg(required=True, col=keys[0])
        else:
            raw |= {k: Arg(required=True) for k in keys}
    raw |= tool.args
    out = {}
    for name, a in raw.items():
        a = (a or Arg()).model_copy()
        c = _find_col(a.col or name, system, master, prefer)
        if c:
            a.type = a.type or ("date" if c.type == "timestamp" and a.op != "=" else c.type)
            a.values = a.values or c.values
            if not a.desc:
                a.desc = c.desc if a.op in ("=", "like", "in") else f"{a.col or name} {a.op} this (YYYY-MM-DD or e.g. -90d, Q3, 2026-08)"
        a.type = a.type or "str"
        if a.type == "enum" and not a.values:
            a.type = "str"
        out[name] = a
    if tool.kind == "select":
        out["limit"] = Arg(type="int", desc=f"Max rows (default {tool.limit})", default=tool.limit)
    return out


def json_schema(args: dict[str, Arg]) -> dict:
    props = {}
    for n, a in args.items():
        p = {"type": JSON_TYPES[a.type]}
        if a.type == "list":
            p["items"] = {"type": "string"}
        if a.values:
            p["enum"] = a.values
        desc = a.desc or ""
        if a.type in ("date", "timestamp") and "YYYY" not in desc:
            desc += " (YYYY-MM-DD)"
        if a.default is not None and n != "limit":
            desc += f" Default {a.default}."
        if desc.strip():
            p["description"] = desc.strip()
        props[n] = p
    return {"type": "object", "properties": props, "required": [n for n, a in args.items() if a.required]}


# ---------- coercion ----------

def parse_date(v, end: bool = False) -> str:
    s = str(v).strip().lower()
    t = AS_OF

    def rng(a: date, b: date) -> str:
        return (b if end else a).isoformat()

    if m := re.fullmatch(r"(\d{4}-\d{2}-\d{2})([ t].*)?", s):
        return m.group(1)
    if m := re.fullmatch(r"(\d{4})-(\d{1,2})", s):
        y, mo = int(m.group(1)), int(m.group(2))
        return rng(date(y, mo, 1), date(y, mo, calendar.monthrange(y, mo)[1]))
    if re.fullmatch(r"\d{4}", s):
        return rng(date(int(s), 1, 1), date(int(s), 12, 31))
    if s in ("today", "now"):
        return t.isoformat()
    if s == "yesterday":
        return (t - timedelta(1)).isoformat()
    if s == "tomorrow":
        return (t + timedelta(1)).isoformat()
    units = {"d": 1, "day": 1, "days": 1, "w": 7, "week": 7, "weeks": 7, "m": 30, "month": 30, "months": 30,
             "y": 365, "year": 365, "years": 365}
    if m := re.fullmatch(r"([+-])\s*(\d+)\s*([a-z]+)", s):
        if m.group(3) in units:
            n = int(m.group(2)) * units[m.group(3)]
            return (t + timedelta(n if m.group(1) == "+" else -n)).isoformat()
    if m := re.fullmatch(r"(last|past|next)\s+(\d+)\s+([a-z]+)", s):
        if m.group(3) in units:
            n = int(m.group(2)) * units[m.group(3)]
            return (t + timedelta(n) if m.group(1) == "next" else t - timedelta(n)).isoformat()
    if m := re.fullmatch(r"q([1-4])\s*(\d{4})?", s) or re.fullmatch(r"(\d{4})\s*q([1-4])", s):
        g = m.groups()
        q, y = (int(g[0]), int(g[1] or t.year)) if not s[0].isdigit() else (int(g[1]), int(g[0]))
        a = date(y, 3 * q - 2, 1)
        b = date(y, 3 * q, calendar.monthrange(y, 3 * q)[1])
        return rng(a, b)
    if m := re.fullmatch(r"(this|last|next) (week|month|quarter|year)", s):
        which, unit = m.groups()
        shift = {"this": 0, "last": -1, "next": 1}[which]
        if unit == "week":
            a = t - timedelta(t.weekday()) + timedelta(7 * shift)
            return rng(a, a + timedelta(6))
        if unit == "month":
            y, mo = t.year, t.month + shift
            y, mo = y + (mo - 1) // 12, (mo - 1) % 12 + 1
            return rng(date(y, mo, 1), date(y, mo, calendar.monthrange(y, mo)[1]))
        if unit == "quarter":
            q = (t.month - 1) // 3 + shift
            y, q = t.year + q // 4, q % 4 + 1
            return parse_date(f"q{q} {y}", end)
        return rng(date(t.year + shift, 1, 1), date(t.year + shift, 12, 31))
    months = {n.lower(): i for i, n in enumerate(calendar.month_name) if n}
    months |= {n.lower(): i for i, n in enumerate(calendar.month_abbr) if n}
    if m := re.fullmatch(r"([a-z]+)\s*(\d{4})?", s):
        if m.group(1) in months:
            mo = months[m.group(1)]
            y = int(m.group(2)) if m.group(2) else (t.year if mo <= t.month else t.year - 1)
            return rng(date(y, mo, 1), date(y, mo, calendar.monthrange(y, mo)[1]))
    try:
        return datetime.fromisoformat(str(v)).date().isoformat()
    except ValueError:
        raise ArgError(f"Can't read date '{v}'. Use YYYY-MM-DD, YYYY-MM, Q3, -90d or 'last 30 days'.")


def _num(v, cast):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return cast(v)
    s = re.sub(r"[£$€,%\s]", "", str(v)).lower()
    mult = 1
    if s.endswith(("k", "m", "bn")):
        mult = {"k": 1e3, "m": 1e6, "n": 1e9}[s[-1]]
        s = s.rstrip("kmbn")
    try:
        return cast(float(s) * mult)
    except ValueError:
        raise ArgError(f"Expected a number, got '{v}'.")


def coerce(name: str, a: Arg, v):
    if v is None or v == "":
        return None
    t = a.type
    if t in ("date", "timestamp"):
        return parse_date(v, end=name.endswith(END_SUFFIX))
    if t == "int":
        return _num(v, lambda x: int(round(x)))
    if t == "float":
        return _num(v, float)
    if t == "bool":
        return str(v).strip().lower() in ("true", "yes", "y", "1")
    if t == "list":
        items = v if isinstance(v, list) else re.split(r"\s*[,;]\s*", str(v))
        return [str(i).strip() for i in items if str(i).strip()]
    if t == "enum":
        s = str(v).strip().lower().replace(" ", "_")
        for val in a.values:
            if val.lower() == s or val.lower().replace(" ", "_") == s:
                return val
        raise ArgError(f"{name} must be one of: {', '.join(a.values)} (got '{v}').")
    return str(v).strip()


# ---------- id / name resolution ----------

NAME_COLS = ("name", "title")


def ref_table(name: str, system: System, master: System):
    """(schema, table, name_col) for an arg that names a table's single key column, if any."""
    for s in (system, master):
        for tn, t in s.tables.items():
            if t.keys == [name]:
                nc = next((c for c in t.cols if c in NAME_COLS or c.endswith("_name")), None)
                return s.id, tn, nc
    return None


def resolve(db, system_id: str, name: str, value: str, ref) -> tuple[str, str | None]:
    """Resolve an id or name to a key. Returns (key, note)."""
    sid, tn, nc = ref
    cols = f'"{name}"' + (f', "{nc}"' if nc else ", NULL")
    rows = db.query(system_id, f'SELECT {cols} FROM "{sid}"."{tn}"')[1]
    v = value.strip().lower()
    for k, n in rows:
        if str(k).lower() == v:
            return k, None
    for k, n in rows:
        if n and str(n).lower() == v:
            return k, f'matched "{n}" ({k})'
    hits = sorted((k, n) for k, n in rows if v in str(k).lower() or (n and v in str(n).lower()))
    if len(hits) == 1:
        k, n = hits[0]
        return k, f'matched "{n or k}" ({k})'
    if hits:
        show = ", ".join(f"{k}" + (f" ({n})" if n else "") for k, n in hits[:8])
        raise ArgError(f"'{value}' matches {len(hits)} {name} values: {show}{' …' if len(hits) > 8 else ''}. Pass one exactly.")
    pool = {str(k): k for k, _ in rows} | {str(n): k for k, n in rows if n}
    close = difflib.get_close_matches(value, list(pool), n=3, cutoff=0.5)
    hint = f" Closest: {', '.join(f'{c} ({pool[c]})' if c != str(pool[c]) else c for c in close)}." if close else ""
    raise ArgError(f"Unknown {name} '{value}'.{hint}")


def prepare(db, system: System, master: System, tool: ToolSpec, args: dict[str, Arg], given: dict) -> tuple[dict, list[str]]:
    """Validate and normalise call arguments. Returns (values, notes)."""
    notes, out = [], {}
    given = {k: v for k, v in (given or {}).items()}
    extra = [k for k in given if k not in args]
    if extra:
        notes.append(f"ignored unknown args: {', '.join(extra)}")
    for n, a in args.items():
        v = given.get(n)
        if v in (None, "") and a.default is not None:
            v = a.default
        if v in (None, "", []):
            if a.required:
                ex = tool.example.get(n)
                raise ArgError(f"Missing required argument '{n}'" + (f" (e.g. {n}={ex!r})." if ex is not None else "."))
            out[n] = None
            continue
        v = coerce(n, a, v)
        if isinstance(v, str) and a.type == "str" and a.op == "=" and (ref := ref_table(a.col or n, system, master)):
            if not (tool.kind == "insert" and ref[1] == tool.table):
                v, note = resolve(db, system.id, a.col or n, v, ref)
                if note:
                    notes.append(note)
        out[n] = v
    return out, notes
