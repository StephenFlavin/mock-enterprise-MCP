"""Compact, small-model-friendly output: summary line, then key: value (one row) or CSV (many rows)."""
import csv
import io
from datetime import date, datetime

MAX_CHARS = 12000
CELL = 300


def cell(v, full=False) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        s = f"{v:.2f}".rstrip("0").rstrip(".")  # never scientific notation: small models misread 5.25e+06
        return "0" if s == "-0" else s
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M") if (v.hour or v.minute) else v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, (list, tuple)):
        return "; ".join(map(cell, v))
    s = str(v)
    return s if full or len(s) <= CELL else s[: CELL - 1] + "…"


def render(rows, total=None, notes=(), narrow=()) -> str:
    head = list(notes)
    if isinstance(rows, str):
        return "\n".join(head + [rows])
    if not rows:
        return "\n".join(head + ["No matching rows. Try a wider date range or fewer filters."])
    shown = len(rows)
    if total and total > shown:
        hint = f" Narrow with: {', '.join(f'{n}=' for n in narrow)}." if narrow else ""
        head.append(f"Showing {shown} of {total} rows.{hint}")
    elif shown > 1:
        head.append(f"{shown} rows.")
    if shown == 1:
        body = "\n".join(f"{k}: {cell(v, full=True)}" for k, v in rows[0].items())
    else:
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(rows[0].keys())
        for r in rows:
            w.writerow([cell(v) for v in r.values()])
        body = buf.getvalue().rstrip()
    out = "\n".join(head + [body])
    if len(out) > MAX_CHARS:
        cut = out[:MAX_CHARS].rsplit("\n", 1)[0]
        out = cut + "\n… output truncated; use filters or a smaller limit."
    return out
