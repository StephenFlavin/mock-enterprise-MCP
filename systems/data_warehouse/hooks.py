"""run_sql_query: a guarded, read-only SQL console over this warehouse and the shared master tables."""
import re
from pathlib import Path

from mockmcp.args import ArgError

_BLOCKED = re.compile(
    r"\b(insert|update|delete|drop|create|alter|attach|detach|copy|export|import|install|load|pragma|call|truncate|"
    r"vacuum|checkpoint|use|set|reset|begin|commit|rollback|grant)\b", re.I)
_FILE_FUNCS = re.compile(r"\b(read_\w+|\w+_scan|glob|sniff_csv|query_table|duckdb_\w+|pragma_\w+|"
                         r"information_schema|current_setting|getenv)\b", re.I)
_OTHER_SYSTEMS = {p.name for p in Path(__file__).resolve().parents[1].iterdir()
                  if p.is_dir() and not p.name.startswith("_")} - {"data_warehouse"}


def run_sql_query(ctx, query, limit=100):
    q = query.strip().rstrip(";").strip()
    bare = re.sub(r"/\*.*?\*/|--[^\n]*", " ", q, flags=re.S)
    bare = re.sub(r"'(?:[^']|'')*'", "''", bare)
    bare = re.sub(r'"[^"]*"', '""', bare)
    if not re.match(r"^\(*\s*(select|with)\b", bare, re.I) or ";" in bare:
        raise ArgError("Only a single read-only SELECT (or WITH ... SELECT) query is allowed.")
    if "$" in bare:
        raise ArgError("Query parameters ($name) are not supported; write literal values.")
    m = _BLOCKED.search(bare)
    if m:
        raise ArgError(f"Read-only warehouse: '{m.group(0)}' is not allowed. Use SELECT only.")
    if _FILE_FUNCS.search(bare):
        raise ArgError("File and system functions are not available. Query warehouse tables or master.<table>.")
    for m in re.finditer(r"\b([a-z_][a-z_0-9]*)\.[a-z_]", bare, re.I):
        if m.group(1).lower() in _OTHER_SYSTEMS:
            raise ArgError(f"Schema '{m.group(1)}' is not part of the warehouse. Use warehouse tables or master.<table>.")
    n = max(1, min(int(limit or 100), 100))
    try:
        return ctx.q(f"SELECT * FROM (\n{q}\n) AS q LIMIT {n}")
    except Exception as e:
        msg = str(e).splitlines()[0]
        raise ArgError(f"SQL error: {msg}") from None
