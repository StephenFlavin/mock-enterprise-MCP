"""DuckDB over CSV. Each table is a view: base CSV ∪ append-only overlay, latest row per key wins."""
import csv
import os
import re
import threading
import time
from pathlib import Path

import duckdb

from . import spec
from .spec import ROOT, WORLD, System, Table

STATE = Path(os.environ.get("MOCKMCP_STATE", ROOT / "state"))
DUCK_TYPES = {"str": "VARCHAR", "text": "VARCHAR", "enum": "VARCHAR", "list": "VARCHAR", "int": "BIGINT",
              "float": "DOUBLE", "bool": "BOOLEAN", "date": "DATE", "timestamp": "TIMESTAMP"}
PARAM = re.compile(r"\$([A-Za-z_]\w*)")


def _cols_sql(t: Table, extra: dict | None = None) -> str:
    cols = {c: DUCK_TYPES[v.type] for c, v in t.cols.items()} | (extra or {})
    return "{" + ", ".join(f"'{c}': '{ty}'" for c, ty in cols.items()) + "}"


def _q2(c: str) -> str:
    return f'"{c}"'


def _q(p: Path) -> str:
    return str(p).replace("'", "''")


class DB:
    def __init__(self):
        self.con = duckdb.connect(":memory:", config={"memory_limit": "256MB", "threads": 2})
        self.systems: dict[str, System] = {}
        self._lock = threading.Lock()

    def add(self, s: System):
        """Create one schema of views for a system (master included)."""
        self.systems[s.id] = s
        self.con.execute(f'CREATE SCHEMA IF NOT EXISTS "{s.id}"')
        for name, t in s.tables.items():
            base = s.dir / "data" / f"{name}.csv"
            over = STATE / s.id / f"{name}.csv"
            for path, extra in ((base, []), (over, ["_seq", "_op"])):
                if not path.exists():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with open(path, "w", newline="") as fh:
                        csv.writer(fh).writerow(list(t.cols) + extra)
            keys = ", ".join(f'"{k}"' for k in t.keys)
            moved = [c for c, v in t.cols.items() if v.type in ("date", "timestamp")] if t.shift else []
            shift = (f"REPLACE ({', '.join(f'{_q2(c)} + INTERVAL {spec.SHIFT_DAYS} DAY AS {_q2(c)}' if t.cols[c].type == 'timestamp' else f'CAST({_q2(c)} + INTERVAL {spec.SHIFT_DAYS} DAY AS DATE) AS {_q2(c)}' for c in moved)})"
                     if moved and spec.SHIFT_DAYS else "")
            opts = "header=true, delim=',', quote='\"', escape='\"', nullstr='', auto_detect=false"
            self.con.execute(f"""
                CREATE OR REPLACE VIEW "{s.id}"."{name}" AS
                SELECT * EXCLUDE (_seq, _op) FROM (
                  SELECT * {shift}, 0::BIGINT AS _seq, 'base' AS _op
                    FROM read_csv('{_q(base)}', {opts}, columns={_cols_sql(t)})
                  UNION ALL BY NAME
                  SELECT * FROM read_csv('{_q(over)}', {opts},
                                         columns={_cols_sql(t, {'_seq': 'BIGINT', '_op': 'VARCHAR'})})
                ) QUALIFY row_number() OVER (PARTITION BY {keys} ORDER BY _seq DESC) = 1 AND _op <> 'delete'""")

    def query(self, system_id: str, sql: str, params: dict | None = None) -> tuple[list[str], list[tuple]]:
        sql = sql.replace("{files}", _q(self.systems[system_id].dir / "files"))
        params = dict(params or {}) | {"as_of": WORLD["as_of"]}
        used = set(PARAM.findall(sql))
        cur = self.con.cursor()
        try:
            cur.execute(f"SET search_path = '{system_id},master'")
            cur.execute(sql, {k: v for k, v in params.items() if k in used})
            cols = [d[0] for d in cur.description]
            return cols, cur.fetchall()
        finally:
            cur.close()

    def rows(self, system_id: str, sql: str, params: dict | None = None) -> list[dict]:
        cols, rows = self.query(system_id, sql, params)
        return [dict(zip(cols, r)) for r in rows]

    def append(self, system_id: str, table: str, row: dict, op: str):
        """Append a full row to the overlay. table may be 'master.<name>' to write shared data."""
        sid, name = table.split(".", 1) if "." in table else (system_id, table)
        t = self.systems[sid].tables[name]
        with self._lock:
            with open(STATE / sid / f"{name}.csv", "a", newline="") as fh:
                csv.writer(fh).writerow([_cell(row.get(c)) for c in t.cols] + [time.time_ns(), op])

    def table(self, system_id: str, table: str) -> tuple[str, Table]:
        sid, name = table.split(".", 1) if "." in table else (system_id, table)
        return sid, self.systems[sid].tables[name]


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (list, tuple)):
        return ";".join(map(str, v))
    return v
