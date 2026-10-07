"""`mockmcp check <id>`: everything a system must satisfy before it counts as built."""
import csv
from functools import cache
import re
import tempfile
from collections import Counter
from pathlib import Path

import yaml

from . import catalog, db, spec
from .spec import SYSTEMS, load_system

MAX_DESC_WORDS, MIN_DESC_WORDS, MAX_ARGS = 30, 4, 8
DATE_LIT = re.compile(r"\b20\d\d-[01]\d(?:-[0-3]\d)?\b")
ALL_IDS = set(catalog.systems())


def _sqls(t) -> list[str]:
    if isinstance(t.sql, dict):
        return list(t.sql.values())
    return [t.sql] if t.sql else []


def lint(sid: str, partial: bool = False) -> list[str]:
    p: list[str] = []
    try:
        s = load_system(sid)
    except Exception as e:
        return [f"system.yaml invalid: {e}"]
    if s.id != sid:
        p.append(f"id is '{s.id}', expected '{sid}'")
    from .server import Engine
    master = load_system("master")
    cat = {r["tool"]: r for r in catalog.tools_for(sid)}
    names = Counter(t.name for t in s.tools)
    p += [f"duplicate tool {n}" for n, c in names.items() if c > 1]
    if not partial:
        p += [f"missing catalogue tool {n}" for n in cat if n not in names]
    p += [f"tool {n} is not in the catalogue for {sid}" for n in names if n not in cat]
    if len(s.instructions) > 400:
        p.append("instructions longer than 400 characters")
    from .args import effective_args
    for t in s.tools:
        if t.name in cat and (cat[t.name]["rw"] == "W") != t.writes:
            p.append(f"{t.name}: catalogue says {cat[t.name]['rw']} but kind is {t.kind}")
        words = len(t.desc.split())
        if not MIN_DESC_WORDS <= words <= MAX_DESC_WORDS:
            p.append(f"{t.name}: description has {words} words (want {MIN_DESC_WORDS}-{MAX_DESC_WORDS})")
        try:
            args = effective_args(t, s, master)
        except Exception as e:
            p.append(f"{t.name}: bad args/table reference: {e}")
            continue
        real = {n: a for n, a in args.items() if n != "limit"}
        if len(real) > MAX_ARGS:
            p.append(f"{t.name}: {len(real)} args (max {MAX_ARGS})")
        p += [f"{t.name}: arg '{n}' has no description (add desc, or a desc on the column it names)"
              for n, a in real.items() if not (a.desc or "").strip()]
        missing = [n for n, a in real.items() if a.required and n not in t.example]
        if missing:
            p.append(f"{t.name}: example lacks required args {missing}")
        p += [f"{t.name}: example arg '{n}' is not an argument" for n in t.example if n not in args]
        for q in _sqls(t) + [x for x in (t.from_, t.table) if x]:
            for other in set(re.findall(r'"?\b([a-z_]+)"?\s*\.\s*"?[a-z_]+', q)) & ALL_IDS - {sid, "master"}:
                p.append(f"{t.name}: reads another system's schema '{other}' (only own tables and master.*; also never use a system id such as 'po' as a table alias)")
            if re.search(r"read_(csv|parquet|json)", q):
                p.append(f"{t.name}: read_csv/read_parquet not allowed; declare a table")
            if "read_text" in q and "{files}" not in q:
                p.append(f"{t.name}: read_text must use the {{files}} placeholder")
        literal = DATE_LIT.findall(" ".join(_sqls(t) + [str(t.example), str(t.defaults), str(t.set), str(t.template or "")]
                                            + [str(x.default) for x in {**t.args, **t.filters}.values() if x]))
        if literal:
            p.append(f"{t.name}: hard-coded date {literal[0]} — use $as_of or relative values like -30d/+14d (data moves to today at runtime)")
        if t.writes:
            tsys = master if t.table.startswith("master.") else s
            tbl = tsys.tables.get(t.table.split(".")[-1])
            if tbl is None:
                p.append(f"{t.name}: table {t.table} not declared")
                continue
            p += [f"{t.name}: arg '{n}' is not a column of {t.table} (writes store every arg)"
                  for n in t.args if n not in tbl.cols]
            p += [f"{t.name}: '{c}' is not a column of {t.table}" for c in [*t.set, *t.defaults] if c not in tbl.cols]
        if t.kind == "select" and t.from_.split(".")[-1] not in (master if t.from_.startswith("master.") else s).tables:
            p.append(f"{t.name}: from {t.from_} not declared")
        if t.kind == "py" and not (s.dir / "hooks.py").exists():
            p.append(f"{t.name}: kind py but no hooks.py")
    p += data_problems(s)
    return p


def _keysets(s) -> dict[str, tuple[str, set]]:
    """column name -> (table, set of key values) for every single-key table in master and this system."""
    out = {}
    for sys_ in (load_system("master"), s):
        for name, t in sys_.tables.items():
            if len(t.keys) == 1:
                f = sys_.dir / "data" / f"{name}.csv"
                if f.exists():
                    with open(f, newline="") as fh:
                        out[t.keys[0]] = (f"{'master.' if sys_.id == 'master' else ''}{name}",
                                          {r.get(t.keys[0], "") for r in csv.DictReader(fh)})
    return out


ID_PATTERNS = {  # value pattern -> (master table, column); catches invented ids in any column
    r"SKU-\d{6}": ("products", "sku"), r"STY-[\w-]+": ("products", "style_id"), r"SUP-\d{4}": ("suppliers", "supplier_id"),
    r"FAC-\d{4}": ("factories", "factory_id"), r"CAR-\d{3}": ("carriers", "carrier_id"), r"PO-20\d\d-\d{6}": ("purchase_orders", "po_id"),
    r"EMP-\d{5}": ("employees", "employee_id"), r"AST-[\w-]+": ("assets", "asset_id"), r"SKU-[A-Z][\w-]*": ("products", "sku")}


@cache
def _master_values(table: str, col: str) -> frozenset:
    with open(SYSTEMS / "_master" / "data" / f"{table}.csv", newline="") as fh:
        return frozenset(r[col] for r in csv.DictReader(fh))


def _invented_ids(name: str, rows: list[list[str]]) -> list[str]:
    bad = set()
    pats = [(re.compile(rf"^{pat}$"), t, c) for pat, (t, c) in ID_PATTERNS.items()]
    for r in rows[1:]:
        for v in r:
            for rx, t, c in pats:
                if rx.match(v) and v not in _master_values(t, c):
                    bad.add(v)
    return [f"data/{name}.csv: ids not in master data, e.g. {sorted(bad)[:4]} (use real ids from systems/_master/data)"] if bad else []


def data_problems(s) -> list[str]:
    p = []
    keysets = _keysets(s)
    for name, t in s.tables.items():
        f = s.dir / "data" / f"{name}.csv"
        if not f.exists():
            p.append(f"data/{name}.csv missing (run: python -m mockmcp gen {s.id})")
            continue
        with open(f, newline="") as fh:
            rows = list(csv.reader(fh))
        if not rows or rows[0] != list(t.cols):
            p.append(f"data/{name}.csv header does not match system.yaml cols (re-run gen)")
            continue
        if len(rows) < 2:
            p.append(f"data/{name}.csv has no rows")
        for ci, col in enumerate(rows[0]):
            if col in keysets and [col] != t.keys:
                ref, valid = keysets[col]
                bad = sorted({r[ci] for r in rows[1:] if r[ci] and r[ci] not in valid})
                if bad:
                    p.append(f"data/{name}.csv: {len(bad)} {col} values not in {ref}, e.g. {bad[:3]} (use existing ids)")
        p += _invented_ids(name, rows)
        idx = [rows[0].index(k) for k in t.keys]
        dupes = [k for k, c in Counter(tuple(r[i] for i in idx) for r in rows[1:]).items() if c > 1]
        if dupes:
            p.append(f"data/{name}.csv: {len(dupes)} duplicate keys, e.g. {dupes[0]}")
    return p


def run_examples(sid: str, partial: bool = False) -> list[str]:
    """Call every tool with its example, in a throwaway state dir. Writes are also retried once.
    Runs as if today were 13 weeks and 2 days after the data date, so hard-coded dates fail."""
    from datetime import date, timedelta
    from .server import Engine
    real_today = spec.WORLD["as_of"]
    spec.set_today(date.fromisoformat(spec.WORLD["data_as_of"]) + timedelta(days=93))
    try:
        return _run_examples(sid, Engine, partial)
    finally:
        spec.set_today(date.fromisoformat(real_today))


def _run_examples(sid, Engine, partial=False) -> list[str]:
    p = []
    with tempfile.TemporaryDirectory() as tmp:
        old, db.STATE = db.STATE, Path(tmp)
        try:
            eng = Engine([sid])
            for t in eng.systems[sid].tools:
                text, err = eng.call(sid, t.name, t.example)
                if err:
                    p.append(f"{t.name} example failed: {text[:300]}")
                elif text.startswith("No matching rows") or "\nNo matching rows" in text:
                    p.append(f"{t.name} example returned no rows (seed data so it does)")
                elif t.kind == "insert":
                    again, _ = eng.call(sid, t.name, t.example)
                    if "already created" not in again:
                        p.append(f"{t.name}: repeating the same insert was not idempotent")
        finally:
            db.STATE = old
    with tempfile.TemporaryDirectory() as tmp:  # scenarios get a clean state of their own
        old, db.STATE = db.STATE, Path(tmp)
        try:
            p += run_scenarios(Engine([sid]), sid, partial)
        finally:
            db.STATE = old
    return p


def run_scenarios(eng, sid: str, partial: bool = False) -> list[str]:
    f = SYSTEMS / sid / "scenarios.yaml"
    needed = {q for r in catalog.tools_for(sid) for q in r["used_by"].split(";") if q}
    if not f.exists():
        return [f"scenarios.yaml missing (needs one entry per question: {sorted(needed)[:5]}…)"]
    p, seen = [], set()
    for sc in yaml.safe_load(f.read_text()) or []:
        q = str(sc.get("question", ""))
        seen.add(q)
        if not sc.get("checks"):
            p.append(f"scenario {q}: no checks")
        for c in sc.get("checks") or []:
            if not c.get("expect"):
                p.append(f"scenario {q}: {c['tool']} check has no expect values (expect seeded ids/values, not column names)")
            if lit := DATE_LIT.findall(str(c.get("args")) + str(c.get("expect"))):
                p.append(f"scenario {q}: hard-coded date {lit[0]} in check — use relative dates like -30d")
            text, err = eng.call(sid, c["tool"], c.get("args") or {})
            if err:
                p.append(f"scenario {q}: {c['tool']} errored: {text[:200]}")
                continue
            for e in c.get("expect") or []:
                if str(e).lower() not in text.lower():
                    p.append(f"scenario {q}: {c['tool']} output lacks '{e}'")
    if not partial:
        p += [f"scenarios.yaml has no entry for question {q}" for q in sorted(needed - seen)]
    return p


def check(sid: str, partial: bool = False) -> list[str]:
    """partial=True (multi-builder systems): don't require every catalogue tool / question yet."""
    try:
        return _check(sid, partial)
    except Exception as e:  # never crash: report it as a problem the builder can fix
        return [f"check crashed: {type(e).__name__}: {e} (often a data CSV whose header does not match system.yaml; re-run gen)"]


def _check(sid: str, partial: bool) -> list[str]:
    p = lint(sid, partial)
    if not any(x.startswith("system.yaml invalid") for x in p):
        p += run_examples(sid, partial)
    return p
