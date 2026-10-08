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


def _gbp(text):
    m = re.search(r"£\s*([\d,]+(?:\.\d+)?)", text or "")
    return float(m.group(1).replace(",", "")) if m else 0.0


def extract_bids(ctx, bid_file, call_out_per_year=None, term_years=3):
    """One row per bid: headline price, terms, hidden costs and the 3-year cost including them."""
    fn, text = _text(bid_file)
    blocks = re.split(r"(?m)^Bid \d+:\s*", text)[1:]
    if not blocks:
        return {"filename": fn, "content": text}
    m = re.search(r"(\d+) call-outs a year", text)
    calls = int(call_out_per_year) if call_out_per_year else (int(m.group(1)) if m else 0)
    term = int(term_years)
    out = []
    for b in blocks:
        lines = b.strip().splitlines()
        f = {k.strip().lower(): v.strip() for k, v in (ln.split(":", 1) for ln in lines[1:] if ":" in ln)}
        annual = _gbp(f.get("annual price"))
        fee = _gbp(f.get("call-out fee"))
        cons = _gbp(f.get("consumables"))
        uplift = float((re.search(r"(\d+(?:\.\d+)?)%", f.get("price review", "")) or [0, 0])[1])
        price3 = sum(annual * (1 + uplift / 100) ** y for y in range(term))
        hidden = (fee * calls + cons) * term
        out.append({"bidder": lines[0].strip(), "annual_price_gbp": annual, "payment_terms": f.get("payment terms", ""),
                    "call_out_fee_gbp": fee, "consumables_per_year_gbp": cons, "minimum_hours": f.get("minimum hours", ""),
                    "price_review_pct": uplift, "service_level": f.get("service level", ""), "references": f.get("references", ""),
                    "headline_price_gbp": round(annual * term, 2), "hidden_costs_gbp": round(hidden, 2),
                    "total_cost_gbp": round(price3 + hidden, 2),
                    "formula": f"{term}-year cost = annual price with yearly uplift + (call-out fee x {calls} + consumables) x {term}"})
    return sorted(out, key=lambda r: r["total_cost_gbp"])


def get_pl_extract(ctx, pl_file, where=None, exclude=None, group_by=None, sort_by=None, max_rows=200):
    return _table_tool(pl_file, where, exclude, None, group_by, sort_by, max_rows)


def get_po_payment(ctx, file_reference, where=None, exclude=None, min_amount=None, group_by=None, sort_by=None, max_rows=200):
    return _table_tool(file_reference, where, exclude, min_amount, group_by, sort_by, max_rows)


# ---------------------------------------------------------------- drafting helpers

DRAFT_HEAD = "DRAFT (not sent or saved)\n\n"


def _split(s, sep=";"):
    """Items of a ';' or newline separated list."""
    return [p.strip() for p in re.split(r"[;\n]", s or "") if p.strip()]


def _rows(s, n):
    """Parse 'a|b|c' items into lists of exactly n fields (missing fields are blank)."""
    out = []
    for item in _split(s):
        f = [x.strip() for x in item.split("|")]
        out.append((f + [""] * n)[:n])
    return out


def _f(v, default=0.0):
    try:
        return float(str(v).replace(",", "").replace("£", "").replace("%", "").strip())
    except ValueError:
        return default


def _gbp_s(v):
    """£1.80m / £220k / £950 with a leading minus for negatives."""
    sign = "-" if v < 0 else ""
    a = abs(v)
    if a >= 1e6:
        return f"{sign}£{a / 1e6:.2f}m"
    if a >= 1e4:
        return f"{sign}£{a / 1e3:.0f}k"
    return f"{sign}£{a:,.0f}"


def _int(v):
    return f"{v:,.0f}"


def _rag_rank(s):
    return {"RED": 3, "AMBER": 2, "GREEN": 1}.get(str(s).strip().upper(), 0)


# ---------------------------------------------------------------- drafts


def draft_management_accounts_commentary(ctx, period=None, operating_profit_variance_gbp=None,
                                         volume_variance_gbp=0, price_mix_variance_gbp=0, cost_variance_gbp=0,
                                         one_off_variance_gbp=0, timing_gbp=0, unexplained_gbp=0):
    ov = operating_profit_variance_gbp
    parts = {"Volume": _f(volume_variance_gbp), "Price and mix": _f(price_mix_variance_gbp), "Cost": _f(cost_variance_gbp),
             "One-offs": _f(one_off_variance_gbp), "Unexplained": _f(unexplained_gbp)}
    drivers = sum(parts.values())
    ov = _f(ov) if ov is not None else drivers
    timing = _f(timing_gbp)
    unexpl = parts["Unexplained"]
    permanent = ov - timing - unexpl
    L = ["MANAGEMENT ACCOUNTS COMMENTARY", "", f"Period: {period or 'current month'}"]
    L += ["", f"OPERATING PROFIT VARIANCE TO BUDGET: {_gbp_s(ov)} ({'adverse' if ov < 0 else 'favourable'})", "", "BY DRIVER"]
    for k, v in parts.items():
        L.append(f"- {k}: {_gbp_s(v)} ({100 * v / ov:.0f}% of the variance)" if ov else f"- {k}: {_gbp_s(v)}")
    if abs(drivers - ov) > 0.5:
        L.append(f"- Not allocated to a driver: {_gbp_s(ov - drivers)}")
    L += ["", "TIMING VERSUS PERMANENT",
          f"- Timing (reverses in a later period): {_gbp_s(timing)}",
          f"- Permanent, explained: {_gbp_s(permanent)}",
          f"- Not yet explained: {_gbp_s(unexpl)}",
          f"- Variance before one-offs: {_gbp_s(ov - parts['One-offs'])}", "", "COMMENTARY"]
    big = max((kv for kv in parts.items() if kv[0] != "Unexplained"), key=lambda kv: abs(kv[1]))
    L.append(f"Operating profit was {_gbp_s(abs(ov))} {'below' if ov < 0 else 'above'} budget. The largest driver was "
             f"{big[0].lower()} at {_gbp_s(big[1])}. Of the total, {_gbp_s(timing)} is timing and {_gbp_s(permanent)} is permanent.")
    if unexpl:
        L.append(f"{_gbp_s(abs(unexpl))} ({100 * abs(unexpl) / abs(ov):.0f}% of the variance) is not yet explained and is being "
                 "chased with the entity accountants before the accounts are finalised." if ov else "")
    return DRAFT_HEAD + "\n".join(L)


def draft_leadership_summary(ctx, reporting_period=None, revenue_actual_gbp=None, revenue_budget_gbp=None,
                             operating_profit_actual_gbp=None, operating_profit_budget_gbp=None,
                             top_issues=None, risks=None, opportunities=None):
    L = ["LEADERSHIP SUMMARY", "", f"Period: {reporting_period or 'current month'}", "", "HEADLINE PERFORMANCE"]
    worst, perf = 0, []
    for name, a, b in (("Revenue", revenue_actual_gbp, revenue_budget_gbp),
                       ("Operating profit", operating_profit_actual_gbp, operating_profit_budget_gbp)):
        if a is None or b is None:
            continue
        a, b = _f(a), _f(b)
        pct = 100 * (a - b) / b if b else 0.0
        worst = max(worst, 0 if abs(pct) <= 2 else 1 if abs(pct) <= 5 or pct > 0 else 2)
        perf.append(f"- {name}: {_gbp_s(a)} against budget {_gbp_s(b)}, variance {_gbp_s(a - b)} ({pct:+.1f}%)")
    if perf:
        L.append("Overall: " + ["ON PLAN", "WATCH (outside 2% of budget)", "OFF PLAN (more than 5% adverse)"][worst])
        L += perf
    for title, items in (("TOP ISSUES", top_issues), ("RISKS", risks), ("OPPORTUNITIES", opportunities)):
        its = _split(items)
        if its:
            L += ["", title] + [f"{i}. {t}" for i, t in enumerate(its, 1)]
    return DRAFT_HEAD + "\n".join(L)


def draft_dispute_response(ctx, partner_id, invoice_number=None, invoiced_units=None, delivered_units=None,
                           invoiced_unit_price_gbp=None, agreed_unit_price_gbp=None, dispute_amount_gbp=None,
                           offer_valid_days=10):
    cust = ctx.q("SELECT * FROM master.partners WHERE partner_id = $c", c=partner_id)   # wholesale accounts are master partners
    L = ["DISPUTE RESPONSE", "", f"Customer: {partner_id}" + (f" ({cust[0]['name']}, {cust[0]['country']})" if cust else ""),
         f"Invoice: {invoice_number or 'not stated'}"]
    if None in (invoiced_units, delivered_units, invoiced_unit_price_gbp, agreed_unit_price_gbp):
        amt = _f(dispute_amount_gbp, 0)
        L += ["", f"Disputed amount: £{_int(amt)}", "", "SUMMARY OF POSITION",
              "We have reviewed your dispute. To state our position we need the invoiced and delivered units and the invoiced "
              "and agreed unit prices.", "", "PROPOSED RESOLUTION", "To follow once the figures are confirmed."]
        return DRAFT_HEAD + "\n".join(L)
    iu, du, ip, ap = _f(invoiced_units), _f(delivered_units), _f(invoiced_unit_price_gbp), _f(agreed_unit_price_gbp)
    invoiced = iu * ip
    correct = du * ap
    over = du * (ip - ap)
    short = (iu - du) * ip
    credit = invoiced - correct
    disputed = _f(dispute_amount_gbp, invoiced)
    L += ["", f"Invoiced: {_int(iu)} units at £{ip:.2f} = £{_int(invoiced)}",
          f"Disputed amount (withheld by the customer): £{_int(disputed)}",
          "", "OUR ANALYSIS",
          (f"- Agreed price: £{ap:.2f} a unit against £{ip:.2f} invoiced; overcharge on delivered units £{_int(over)}" if over else
           f"- Invoiced price £{ip:.2f} a unit is the agreed price: no price dispute"),
          f"- Delivered {_int(du)} of {_int(iu)} units; {_int(iu - du)} units short, invoiced at £{_int(short)}",
          f"- Correct value of the goods delivered at the agreed price: £{_int(correct)}",
          f"- Total overbilled: £{_int(credit)} ({100 * credit / invoiced:.1f}% of the invoice)",
          "", "OUR POSITION",
          f"The customer is right {'on price and ' if over else ''}on the short delivery. The amount properly due is £{_int(correct)}; "
          f"£{_int(credit)} of the invoice cannot be supported.",
          "", "PROPOSED RESOLUTION",
          f"We will issue a credit note for £{_int(credit)} and ask for payment of £{_int(correct)} within standard terms. "
          f"This offer is valid for {int(_f(offer_valid_days))} business days."]
    return DRAFT_HEAD + "\n".join(L)


_RATING = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def draft_audit_findings_report(ctx, audit_subject=None, findings=None):
    rows = _rows(findings, 6)
    rows.sort(key=lambda r: (_RATING.get(r[1].upper(), 3), -_f(r[3])))
    L = ["AUDIT FINDINGS REPORT", "", f"Subject: {audit_subject or 'Not stated'}", f"Date: {ctx.as_of}", "Prepared By: Internal Audit"]
    if not rows:
        L += ["", "No findings supplied."]
        return DRAFT_HEAD + "\n".join(L)
    for i, (title, rating, obs, amt, owner, test) in enumerate(rows, 1):
        L += ["", f"FINDING #{i}: {title}", f"Risk Rating: {rating.upper()}", f"Observation: {obs}"]
        if amt:
            L.append(f"Value at risk: £{_int(_f(amt))}")
        if test:
            L.append(f"Next-step test: {test}")
        if owner:
            L.append(f"Owner: {owner}")
    tot = sum(_f(r[3]) for r in rows)
    cnt = {k: sum(1 for r in rows if r[1].upper() == k) for k in ("HIGH", "MEDIUM", "LOW")}
    L += ["", "SUMMARY TABLE", "| Finding | Risk | Value at risk |", "|---|---|---|"]
    L += [f"| {r[0]} | {r[1].upper()} | £{_int(_f(r[3]))} |" for r in rows]
    L += ["", f"TOTAL VALUE AT RISK: £{_int(tot)} across {len(rows)} findings "
              f"({cnt['HIGH']} high, {cnt['MEDIUM']} medium, {cnt['LOW']} low)"]
    return DRAFT_HEAD + "\n".join(L)


def draft_board_paper(ctx, topic, options=None, envelope_gbp=None, hurdle_rate_pct=None, revenue_miss_pct=10):
    opts = []
    for n, capex, irr, irr_dn, risk in _rows(options, 5):
        opts.append({"name": n, "capex": _f(capex), "irr": _f(irr), "dn": _f(irr_dn, _f(irr)), "risk": risk or "n/a"})
    L = [f"BOARD PAPER: {topic}", ""]
    if not opts:
        L += ["EXECUTIVE SUMMARY", f"This paper presents {topic.lower()} for board consideration. No options were supplied to compare."]
        return DRAFT_HEAD + "\n".join(L)
    env = _f(envelope_gbp) if envelope_gbp is not None else sum(o["capex"] for o in opts)
    hurdle = _f(hurdle_rate_pct) if hurdle_rate_pct is not None else None
    miss = _f(revenue_miss_pct)
    opts.sort(key=lambda o: -o["irr"])
    left, funded = env, []
    for o in opts:
        o["funded"] = o["capex"] <= left and (hurdle is None or o["irr"] >= hurdle)
        if o["funded"]:
            left -= o["capex"]
            funded.append(o)
    ftot = sum(o["capex"] for o in funded)
    L += ["EXECUTIVE SUMMARY",
          f"{len(opts)} options assessed on one basis (IRR, and IRR after a {miss:.0f}% revenue miss) against an envelope of "
          f"{_gbp_s(env)}. Funding in order of return fills {_gbp_s(ftot)}: " + ", ".join(o["name"] for o in funded) + ".",
          "", "OPTIONS: RISK AND RETURN", "| Option | Capex | IRR | IRR after revenue miss | Change | Risk | Funded |", "|---|---|---|---|---|---|---|"]
    for o in opts:
        L.append(f"| {o['name']} | {_gbp_s(o['capex'])} | {o['irr']:.1f}% | {o['dn']:.1f}% | {o['dn'] - o['irr']:+.1f} pts | {o['risk']} | "
                 f"{'yes' if o['funded'] else ('no, below hurdle' if hurdle is not None and o['irr'] < hurdle else 'no, over envelope')} |")
    L += ["", f"SENSITIVITY: {miss:.0f}% REVENUE MISS"]
    if hurdle is not None:
        fail = sorted((o for o in opts if o["dn"] < hurdle), key=lambda o: o["dn"])
        L.append(f"Hurdle rate {hurdle:.1f}%. Options falling below it in the downside: " +
                 (", ".join(f"{o['name']} ({o['dn']:.1f}%)" for o in fail) if fail else "none") + ".")
    sens = max(opts, key=lambda o: o["irr"] - o["dn"])
    L.append(f"Most sensitive to the miss: {sens['name']} (loses {sens['irr'] - sens['dn']:.1f} points).")
    L += ["", "KEY ASSUMPTIONS TO CHALLENGE", f"- {sens['name']}: return depends most on revenue delivery.",
          f"- Envelope: {_gbp_s(env)}; unfunded demand {_gbp_s(sum(o['capex'] for o in opts if not o['funded']))}."]
    if hurdle is not None and fail:
        L += ["", "DEFER IF THE ECONOMY SOFTENS", f"{fail[0]['name']} has the weakest downside return ({fail[0]['dn']:.1f}% against hurdle {hurdle:.1f}%)."]
    L += ["", "RECOMMENDATION", f"The board is invited to approve {_gbp_s(ftot)} across " + ", ".join(o["name"] for o in funded) +
          (f", leaving {_gbp_s(left)} unallocated." if left > 0 else ".")]
    return DRAFT_HEAD + "\n".join(L)


def _kv(s):
    out = {}
    for part in _split(s):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = _f(v, None)
    return out


def draft_market_entry_brief(ctx, market_country, product_category="home range", requirements=None, consumer_preferences=None,
                             products_needing_modification=None, economics=None):
    e = _kv(economics)
    L = ["MARKET ENTRY BRIEF", "", f"Market: {market_country}", f"Category: {product_category}", "", "REGULATORY AND COMPLIANCE"]
    L += [f"- {x}" for x in _split(requirements)] or ["- None supplied"]
    if "import_duty_pct" in e:
        L.append(f"- Import duty: {e['import_duty_pct']:.1f}%")
    if "vat_pct" in e:
        L.append(f"- VAT: {e['vat_pct']:.1f}%")
    if _split(consumer_preferences) or "price_low_gbp" in e:
        L += ["", "CONSUMER PREFERENCES"] + [f"- {x}" for x in _split(consumer_preferences)]
        if "price_low_gbp" in e and "price_high_gbp" in e:
            L.append(f"- Price points: £{e['price_low_gbp']:.2f} to £{e['price_high_gbp']:.2f}")
    mods = _split(products_needing_modification)
    if mods:
        L += ["", "PRODUCTS NEEDING MODIFICATION"] + [f"- {m}" for m in mods]
    rec = "Supply unit cost, price points, duty, VAT and the typical retail margin to test the margin."
    need = ("unit_cost_gbp", "price_low_gbp", "price_high_gbp", "typical_retail_margin_pct")
    if all(k in e for k in need):
        duty, vat = e.get("import_duty_pct", 0), e.get("vat_pct", 0)
        landed = e["unit_cost_gbp"] * (1 + duty / 100)
        mid = (e["price_low_gbp"] + e["price_high_gbp"]) / 2
        net = mid / (1 + vat / 100)
        margin = 100 * (net - landed) / net
        typ = e["typical_retail_margin_pct"]
        L += ["", "MARGIN TEST",
              f"- Landed unit cost with {duty:.1f}% duty: £{landed:.2f}",
              f"- Mid price point £{mid:.2f}, or £{net:.2f} excluding {vat:.1f}% VAT",
              f"- Implied margin: {margin:.1f}% against a typical retail margin of {typ:.1f}%"]
        rec = ("PROCEED: the implied margin meets the typical retail margin." if margin >= typ else
               f"PROCEED ONLY WITH CHANGES: the implied margin is {typ - margin:.1f} points below the typical retail margin; "
               "cut landed cost or raise the price point.")
    L += ["", "RECOMMENDATION", rec]
    return DRAFT_HEAD + "\n".join(L)


def draft_incident_summary(ctx, incident_type, site_id, what_happened="Details being confirmed", impact="Under assessment",
                           root_cause="Under investigation", next_steps="Complete root cause analysis and confirm the fix with the owning team",
                           audience=None, decisions_needed=None):
    site = ctx.q("SELECT * FROM master.sites WHERE site_id = $s", s=site_id)
    L = ["INCIDENT SUMMARY", "", f"Incident type: {str(incident_type).upper()}"]
    if audience:
        L.append(f"Prepared for: {audience}")
    L += [f"Site: {site[0]['name'] if site else site_id} ({site_id})", f"Date: {ctx.as_of}"]
    L += ["", "WHAT HAPPENED", what_happened, "", "IMPACT", impact, "", "ROOT CAUSE", root_cause, "", "NEXT STEPS"]
    steps = _split(next_steps)
    L += [f"{i}. {x}" for i, x in enumerate(steps, 1)] if len(steps) > 1 else [next_steps]
    d = _split(decisions_needed)
    if d:
        L += ["", "DECISIONS NEEDED"] + [f"- {x}" for x in d]
    L += ["", "Status: OPEN, " + ("under investigation." if root_cause.lower().startswith("under investigation") else "root cause identified, containment in progress.")]
    return DRAFT_HEAD + "\n".join(L)


def draft_executive_briefing(ctx, topic, scorecard=None, issues=None, fix_window_weeks=13):
    L = ["EXECUTIVE BRIEFING", "", f"Topic: {topic}", f"Date: {ctx.as_of}"]
    sc = _rows(scorecard, 4)
    if sc:
        L += ["", "PERFORMANCE AGAINST PLAN", "| Area | Actual | Plan | Gap | Status |", "|---|---|---|---|---|"]
        behind = 0
        for area, a, p, d in sc:
            av, pv = _f(a), _f(p)
            gap = av - pv
            good = gap >= 0 if d.lower().startswith("higher") else gap <= 0
            near = pv and abs(gap) / abs(pv) <= 0.02
            st = "ON PLAN" if near else ("AHEAD" if good else "BEHIND")
            behind += st == "BEHIND"
            L.append(f"| {area} | {a} | {p} | {gap:+.1f} | {st} |")
        L.append(f"{behind} of {len(sc)} areas are behind plan.")
    iss = [{"t": t, "cause": c, "impact": _f(i), "wk": _f(w)} for t, c, i, w in _rows(issues, 4)]
    if iss:
        iss.sort(key=lambda x: -x["impact"])
        L += ["", "TOP ISSUES (largest impact first)"]
        for n, x in enumerate(iss[:5], 1):
            fix = "can be fixed within a quarter" if x["wk"] <= fix_window_weeks else "needs longer than a quarter"
            L.append(f"{n}. {x['t']}: {_gbp_s(x['impact'])} a year; cause {x['cause']}; {x['wk']:.0f} weeks to fix, {fix}")
        quick = [x for x in iss[:5] if x["wk"] <= fix_window_weeks]
        L += ["", f"Most urgent: {iss[0]['t']}.",
              f"Fixable within {int(fix_window_weeks)} weeks: {len(quick)} of {len(iss[:5])} (" + ", ".join(x["t"] for x in quick) + ")."]
    if not sc and not iss:
        L += ["", "SITUATION OVERVIEW", "No findings were supplied."]
    return DRAFT_HEAD + "\n".join(L)


def _plan_initiatives(items, budget):
    ini = {}
    for n, c, r, risk, dep, yrs in _rows(items, 6):
        ini[n] = {"name": n, "cost": _f(c), "ret": _f(r), "risk": risk, "deps": [d.strip() for d in dep.split(",") if d.strip()], "yrs": _f(yrs, 1)}

    def wave(n, seen=()):
        deps = [d for d in ini[n]["deps"] if d in ini and d not in seen]
        return 1 + max((wave(d, seen + (n,)) for d in deps), default=0)

    for n in ini:
        ini[n]["wave"] = wave(n)
    order = sorted(ini.values(), key=lambda x: (x["wave"], -x["ret"]))
    left, funded = budget, set()
    for x in order:
        ok = x["cost"] <= left and all(d in funded or d not in ini for d in x["deps"])
        x["in"] = ok
        if ok:
            left -= x["cost"]
            funded.add(x["name"])
    return ini, order


def draft_investment_roadmap(ctx, investment_theme, budget_million_gbp=None, initiatives=None, reduced_budget_million_gbp=None):
    L = ["INVESTMENT ROADMAP", "", f"Theme: {investment_theme}"]
    if not _split(initiatives):
        L += ["No initiatives were supplied."]
        return DRAFT_HEAD + "\n".join(L)
    total = sum(_f(r[1]) for r in _rows(initiatives, 6))
    budget = _f(budget_million_gbp) if budget_million_gbp is not None else total
    L.append(f"Envelope: £{budget:g}m; initiatives asked for: £{total:g}m")
    ini, order = _plan_initiatives(initiatives, budget)
    for w in sorted({x["wave"] for x in order}):
        grp = [x for x in order if x["wave"] == w]
        L += ["", f"PHASE {w} (£{sum(x['cost'] for x in grp if x['in']):g}m funded)"]
        for x in grp:
            dep = f"; after {', '.join(x['deps'])}" if x["deps"] else ""
            L.append(f"- {x['name']}: £{x['cost']:g}m, return {x['ret']:g}%, risk {x['risk']}, {x['yrs']:g} yr{dep}"
                     + ("" if x["in"] else " [OUTSIDE ENVELOPE]"))
    used = sum(x["cost"] for x in order if x["in"])
    L += ["", f"WITHIN ENVELOPE: £{used:g}m of £{budget:g}m"]
    dependents = {n: [m for m, y in ini.items() if n in y["deps"]] for n in ini}
    top = max(ini, key=lambda n: (len(dependents[n]), ini[n]["cost"]))
    if dependents[top]:
        L.append(f"BIGGEST DEPENDENCY: {top}, which {', '.join(dependents[top])} depend on.")
    if reduced_budget_million_gbp is not None:
        rb = _f(reduced_budget_million_gbp)
        _, o2 = _plan_initiatives(initiatives, rb)
        cut = [x for x in o2 if not x["in"]]
        L += ["", f"IF THE ENVELOPE DROPS TO £{rb:g}m",
              "Cut or deferred: " + (", ".join(f"{x['name']} (£{x['cost']:g}m)" for x in cut) if cut else "nothing"),
              f"Funded: £{sum(x['cost'] for x in o2 if x['in']):g}m"]
    return DRAFT_HEAD + "\n".join(L)


def draft_sponsor_challenge_brief(ctx, project_name, total_investment_gbp=None, portfolio=None, envelope_gbp=None, hurdle_irr_pct=None):
    rows = [{"p": p, "sp": s, "cap": _f(c), "irr": _f(i), "risk": r, "dec": d.lower(), "y1": _f(y1, None) if y1 else None}
            for p, s, c, i, r, d, y1 in _rows(portfolio, 7)]
    L = ["SPONSOR CHALLENGE BRIEF", "", f"Project/Portfolio: {project_name}", f"Date: {ctx.as_of}"]
    if not rows:
        L.append(f"Investment: £{_int(_f(total_investment_gbp))}" if total_investment_gbp is not None else "No portfolio supplied.")
        return DRAFT_HEAD + "\n".join(L)
    ask = sum(r["cap"] for r in rows)
    env = _f(envelope_gbp) if envelope_gbp is not None else _f(total_investment_gbp, ask)
    funded = [r for r in rows if r["dec"] == "fund"]
    ftot = sum(r["cap"] for r in funded)
    rank = {r["p"]: i for i, r in enumerate(sorted(rows, key=lambda r: -r["irr"]), 1)}
    L += [f"Projects: {len(rows)}; total ask £{_int(ask)}; envelope £{_int(env)}; funded in full £{_int(ftot)}"]
    hurdle = _f(hurdle_irr_pct) if hurdle_irr_pct is not None else None
    y1 = sum(r["y1"] or 0 for r in rows if r["dec"] == "phase")
    if y1:
        L.append(f"Year-one spend on phased projects £{_int(y1)}; committed in year one £{_int(ftot + y1)}, leaving £{_int(env - ftot - y1)} of the envelope")
    for r in sorted((r for r in rows if r["dec"] != "fund"), key=lambda r: -r["irr"]):
        L += ["", f"{r['p'].upper()} ({r['sp']}): {r['dec'].upper()}",
              f"Ask: £{_int(r['cap'])}, IRR {r['irr']:g}% (rank {rank[r['p']]} of {len(rows)} on return), risk {r['risk']}"]
        obj = f"Likely objection: why is a {r['irr']:g}% project not fully funded?"
        if hurdle is not None and r["irr"] >= hurdle:
            obj += f" It clears the {hurdle:g}% hurdle."
        L.append(obj)
        better = [x for x in funded if x["irr"] >= r["irr"]]
        resp = f"Response: the £{_int(env)} envelope cannot hold the £{_int(ask)} asked; {len(better)} of the {len(funded)} fully funded projects return at least as much"
        if r["dec"] == "phase" and r["y1"] is not None:
            resp += f"; phasing limits year-one spend to £{_int(r['y1'])}"
        if r["risk"].lower() == "high":
            resp += "; delivery risk is rated high"
        L.append(resp + ".")
    return DRAFT_HEAD + "\n".join(L)


def draft_highlight_report(ctx, programme_name, status=None, budget_gbp=None, forecast_gbp=None, go_live_date=None,
                           schedule_slip_weeks=None, top_risks=None, decisions_needed=None):
    st = {}
    for part in _split(status):
        if ":" in part:
            k, v = part.split(":", 1)
            st[k.strip().lower()] = v.strip().upper()
    overall = max(st.values(), key=_rag_rank) if st else "NOT ASSESSED"
    L = ["HIGHLIGHT REPORT", "", f"Programme: {programme_name}", f"Date: {ctx.as_of}", f"Overall status: {overall}", "", "STATUS BY DIMENSION"]
    for k, v in st.items():
        extra = ""
        if k == "schedule" and (schedule_slip_weeks is not None or go_live_date):
            extra = " (" + ", ".join(x for x in [f"{_f(schedule_slip_weeks):g} weeks slip" if schedule_slip_weeks is not None else "",
                                                  f"go-live {go_live_date}" if go_live_date else ""] if x) + ")"
        if k == "budget" and budget_gbp is not None and forecast_gbp is not None:
            b, fc = _f(budget_gbp), _f(forecast_gbp)
            extra = f" (budget {_gbp_s(b)}, forecast {_gbp_s(fc)}, {_gbp_s(fc - b)} / {100 * (fc - b) / b:+.1f}%)"
        L.append(f"- {k.capitalize()}: {v}{extra}")
    r = _rows(top_risks, 3)
    if r:
        L += ["", "TOP RISKS AND ISSUES"] + [f"{i}. {t} [{s}]: {im}" for i, (t, s, im) in enumerate(r, 1)]
    d = _split(decisions_needed)
    if d:
        L += ["", "DECISIONS REQUIRED"] + [f"{i}. {x}" for i, x in enumerate(d, 1)]
    return DRAFT_HEAD + "\n".join(L)
