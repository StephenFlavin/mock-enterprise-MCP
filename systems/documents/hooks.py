"""Document readers: parse the attached files into rows, filter, group and total them."""
import csv
import io
import re
from pathlib import Path

FILES = Path(__file__).parent / "files"
SUM_COL = re.compile(r"(_gbp$|^amount|^pallets|^loads|^qty|^units|^current_qty|^headcount|^hours|_hours$|^volume)")
NO_SUM = re.compile(r"(rate|per_|_pct|price|^unit_|retail|contracted|run_hours|aged_days|vibration)")


def _resolve(name):
    """Find a file in files/ by exact, case-insensitive or partial name."""
    name = Path(str(name).strip()).name
    avail = sorted(p.name for p in FILES.iterdir() if p.is_file())
    for cand in avail:
        if cand == name:
            return cand
    low = name.lower()
    hits = [a for a in avail if a.lower() == low] or [a for a in avail if low and (low in a.lower() or Path(a).stem.lower() == Path(low).stem)]
    if len(hits) == 1:
        return hits[0]
    raise ValueError(f"No document '{name}'. Available: {', '.join(avail)}")


def _text(name):
    fn = _resolve(name)
    return fn, (FILES / fn).read_text(errors="replace")


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def _csv_table(text):
    """Return (comments, header, rows) for a comma-separated table, or None."""
    notes, block = [], []
    for ln in text.splitlines():
        if ln.startswith("#"):
            notes.append(ln.lstrip("# ").strip())
        elif ln.strip() == "":
            if block:
                break
        elif ln.lstrip().startswith("|"):
            return None
        elif block or ln.count(",") >= 2:
            block.append(ln)
    if len(block) < 2:
        return None
    rd = list(csv.reader(io.StringIO("\n".join(block))))
    header = [h.strip() for h in rd[0]]
    rows = [dict(zip(header, [c.strip() for c in r])) for r in rd[1:] if len(r) == len(header)]
    return (notes, header, rows) if rows else None


def _pipe_table(text):
    """Return (terms, header, rows) for a | pipe | table with 'Key: value' lines above it."""
    terms, tbl = [], []
    for ln in text.splitlines():
        if ln.lstrip().startswith("|"):
            tbl.append([c.strip() for c in ln.strip().strip("|").split("|")])
        elif ":" in ln and not tbl:
            terms.append(tuple(s.strip() for s in ln.split(":", 1)))
    if len(tbl) < 2:
        return terms, [], []
    header = tbl[0]
    rows = [dict(zip(header, r)) for r in tbl[1:] if len(r) == len(header)]
    return terms, header, rows


def _money_col(header):
    for h in header:
        if h.endswith("_gbp") or h in ("amount", "amount_gbp"):
            return h
    return None


def _pairs(spec):
    out = []
    for part in re.split(r"[;]", spec or ""):
        part = part.strip()
        if not part:
            continue
        if "~" in part:
            c, v = part.split("~", 1)
            out.append((c.strip(), "~", v.strip().lower()))
        elif "=" in part:
            c, v = part.split("=", 1)
            out.append((c.strip(), "=", v.strip().lower()))
    return out


def _match(row, pairs):
    for c, op, v in pairs:
        cell = str(row.get(c, "")).lower()
        if (op == "=" and cell != v) or (op == "~" and v not in cell):
            return False
    return True


def _table_tool(name, where, exclude, min_amount, group_by, sort_by, limit):
    fn, text = _text(name)
    tbl = _csv_table(text)
    if tbl is None:
        return {"filename": fn, "content": text}
    notes, header, rows = tbl
    for c, _, _ in _pairs(where) + _pairs(exclude):
        if c not in header:
            raise ValueError(f"No column '{c}' in {fn}. Columns: {', '.join(header)}")
    mcol = _money_col(header)
    if where:
        rows = [r for r in rows if _match(r, _pairs(where))]
    if exclude:
        ex = _pairs(exclude)
        rows = [r for r in rows if not _match(r, ex)]
    if min_amount is not None and mcol:
        rows = [r for r in rows if abs(_num(r[mcol]) or 0) >= float(min_amount)]
    sumcols = [h for h in header if SUM_COL.search(h) and not NO_SUM.search(h)
               and all(_num(r[h]) is not None for r in rows)]
    n = len(rows)
    if group_by:
        gcols = [g.strip() for g in group_by.split(",") if g.strip()]
        for g in gcols:
            if g not in header:
                raise ValueError(f"No column '{g}' in {fn}. Columns: {', '.join(header)}")
        groups = {}
        for r in rows:
            k = tuple(r[g] for g in gcols)
            gr = groups.setdefault(k, {**{g: r[g] for g in gcols}, "rows": 0, **{s: 0.0 for s in sumcols}})
            gr["rows"] += 1
            for s in sumcols:
                gr[s] += _num(r[s])
        out = list(groups.values())
        key = (sort_by or "").split()[0] if sort_by else (mcol if mcol in sumcols else (sumcols[0] if sumcols else "rows"))
        out.sort(key=lambda g: g.get(key, 0) if isinstance(g.get(key, 0), (int, float)) else str(g.get(key)), reverse=not (sort_by and sort_by.endswith(" asc")))
        total = sum(g.get(mcol, 0) for g in out) if mcol in sumcols else None
        for g in out:
            for s in sumcols:
                g[s] = round(g[s], 2)
            if total:
                g["share_pct"] = round(100 * g.get(mcol, 0) / total, 1)
        shown = out[: int(limit)]
        tot = {gcols[0]: f"TOTAL of {n} rows in {len(out)} groups", "rows": n}
        for s in sumcols:
            tot[s] = round(sum(_num(r[s]) for r in rows), 2)
        shown.append(tot)
        return shown
    if sort_by:
        col = sort_by.split()[0]
        if col not in header:
            raise ValueError(f"No column '{col}' in {fn}. Columns: {', '.join(header)}")
        desc = not sort_by.endswith(" asc")
        rows.sort(key=lambda r: (_num(r[col]) if _num(r[col]) is not None else 0, r[col]), reverse=desc)
    elif mcol and sumcols and mcol in sumcols:
        rows.sort(key=lambda r: -abs(_num(r[mcol])))
    shown = rows[: int(limit)]
    if sumcols:
        tot = {h: "" for h in header}
        tot[header[0]] = f"TOTAL of {n} matching rows" + (f" (first {len(shown)} shown)" if n > len(shown) else "")
        for s in sumcols:
            tot[s] = round(sum(_num(r[s]) for r in rows), 2)
        shown.append(tot)
    return shown


def read_document(ctx, path, where=None, exclude=None, min_amount=None, group_by=None, sort_by=None, max_rows=150):
    return _table_tool(path, where, exclude, min_amount, group_by, sort_by, max_rows)


def read_spreadsheet(ctx, filename, where=None, exclude=None, min_amount=None, group_by=None, sort_by=None, max_rows=150):
    return _table_tool(filename, where, exclude, min_amount, group_by, sort_by, max_rows)


def get_table_document(ctx, file_reference):
    return _table_tool(file_reference, None, None, None, None, None, 200)


def extract_quote_lines(ctx, quote_file):
    fn, text = _text(quote_file)
    terms, header, rows = _pipe_table(text)
    if not rows:
        raise ValueError(f"No line-item table found in {fn}")
    out = []
    for r in rows:
        out.append({"component": r.get("component", ""), "qty": r.get("qty", ""), "unit_price_gbp": r.get("unit_price_gbp", ""),
                    "total_gbp": r.get("total_gbp", ""), "note": r.get("note", "")})
    skip = ("supplier", "product", "unit price", "moq", "incoterm", "lead time", "material grade", "wall thickness", "tooling", "payment terms")
    for k, v in terms:
        if k.lower() in skip:
            out.append({"component": f"Term - {k}", "qty": "", "unit_price_gbp": "", "total_gbp": "", "note": v})
    return out


def extract_bids(ctx, bid_file):
    fn, text = _text(bid_file)
    out, cur = [], None
    for ln in text.splitlines():
        m = re.match(r"\s*-\s*(.+?) bid:\s*£?([\d,\.]+) total,\s*(?:Net\s*)?(\d+)\s*(?:days)?\s*terms?", ln, re.I)
        if m:
            cur = {"supplier": m.group(1), "total_price_gbp": float(m.group(2).replace(",", "")), "payment_terms": f"Net {m.group(3)}",
                   "service": "", "scope": ""}
            out.append(cur)
        elif cur and ln.strip().lower().startswith("service:"):
            cur["service"] = ln.split(":", 1)[1].strip()
        elif cur and ln.strip().lower().startswith("scope:"):
            cur["scope"] = ln.split(":", 1)[1].strip()
    if not out:
        return {"filename": fn, "content": text}
    return sorted(out, key=lambda r: r["total_price_gbp"])


def get_pl_extract(ctx, pl_file):
    return _table_tool(pl_file, None, None, None, None, None, 200)


def get_po_payment(ctx, file_reference):
    return _table_tool(file_reference, None, None, None, None, None, 200)
