"""Tax & Duty system: duty rates by HS heading/origin/market, customs entries built from master POs,
tariff scenarios sized from those entries, and VAT returns built from VAT postings.

Hand-written reference data (transfer pricing, incentives, tasks, market rules) lives in seed/*.csv.
"""
from datetime import date, timedelta

EU_ORIGINS = {"PT", "IT", "FR", "DE", "PL"}
ORIGINS = ["CN", "VN", "BD", "TR", "IN", "ID", "MX", "PT", "IT", "FR", "DE", "PL", "GB"]
MARKETS = ["UK", "EU", "US"]
# heading -> standard rate % into (UK, EU, US). Headings are the first four digits of master product hs codes,
# plus the story headings 6110 (cotton knit tops), 6202 (padded gilets) and 6403 (footwear).
BASE = {
    "6110": (12, 12, 16.5), "6202": (14, 14, 16.5), "6203": (12, 12, 16.5), "6204": (12, 12, 16.5),
    "6209": (12, 12, 12), "6302": (12, 12, 6), "4202": (3, 3, 8), "3304": (0, 0, 0),
    "8516": (8, 8, 4), "6403": (8, 12, 10),
}
FREIGHT = {"sea": 0.05, "air": 0.14, "road": 0.03, "rail": 0.04}
IMPORT_VAT = {"UK": 20, "EU": 21, "US": 0}
# (heading, origin, market) -> (points added by the change, days ago it took effect)
CHANGES = {
    ("6110", "VN", "US"): (5, 120), ("6110", "BD", "US"): (5, 120), ("6110", "CN", "US"): (10, 160),
    ("6203", "CN", "UK"): (3, 100), ("6204", "CN", "UK"): (3, 100), ("6209", "CN", "UK"): (3, 100),
}
STORY_SUPPLIER = "SUP-0052"   # Bangladesh kids' supplier: 11 recent entries held, preference claimed without proof
HISTORY_DAYS = 540            # days of customs history


def _rule(heading, origin, market):
    """(duty %, preferential %, scheme) or None when the route is not an import."""
    base = BASE[heading][MARKETS.index(market)]
    if market == "UK" and (origin == "GB"):
        return None
    if market == "EU" and origin in EU_ORIGINS:
        return None
    if origin in EU_ORIGINS and market == "UK":
        return (0, None, None)
    if origin == "GB" and market == "EU":
        return (0, None, None)
    lo = lambda x: max(round(x, 1), 0)
    if origin == "CN":
        if market == "US":
            return (lo(base + 8.5) if base else 0, None, None)
        return (lo(base + 3) if base else 0, None, None)
    if origin == "VN":
        if market == "UK":
            return (lo(base - 2), lo(base - 4), "CPTPP") if base else (0, None, None)
        if market == "EU":
            return (lo(base - 2), lo(base - 4), "EVFTA") if base else (0, None, None)
        return (lo(base - 1.5), None, None)
    if origin == "BD":
        if market == "UK":
            return (base, 0, "DCTS (LDC)") if base else (0, None, None)
        if market == "EU":
            return (base, 0, "EBA") if base else (0, None, None)
        return (base, None, None)
    if origin == "TR":
        if market == "UK":
            return (base, lo(base - 3), "UK-Turkey FTA") if base else (0, None, None)
        if market == "EU":
            return (base, lo(base - 4), "EU-Turkey CU") if base else (0, None, None)
        return (base, None, None)
    if origin == "IN":
        if market == "US":
            return (base, None, None)
        return (base, lo(base - 2), "DCTS" if market == "UK" else "GSP") if base else (0, None, None)
    if origin == "ID":
        if market == "US":
            return (base, None, None)
        return (base, lo(base - 3), "DCTS" if market == "UK" else "GSP") if base else (0, None, None)
    if origin == "MX":
        if market == "UK":
            return (base, None, None)
        return (base, 0, "EU-Mexico MA" if market == "EU" else "USMCA") if base else (0, None, None)
    return (base, None, None)    # remaining origins into the US (EU members, GB)


def _rates(g):
    rows = []
    long_ago = g.as_of - timedelta(days=900)
    for heading in BASE:
        for origin in ORIGINS:
            for market in MARKETS:
                rule = _rule(heading, origin, market)
                if rule is None:
                    continue
                duty, pref, scheme = rule
                vat = IMPORT_VAT[market]
                row = {"hs_code": heading, "origin_country": origin, "destination_market": market,
                       "duty_rate_pct": duty, "vat_rate_pct": vat, "preferential_rate_pct": pref,
                       "preference_scheme": scheme, "effective_date": long_ago, "end_date": None,
                       "last_updated": g.as_of}
                change = CHANGES.get((heading, origin, market))
                if change:
                    pts, days = change
                    start = g.as_of - timedelta(days=days)
                    rows.append(dict(row, duty_rate_pct=round(duty - pts, 1), end_date=start - timedelta(days=1)))
                    row = dict(row, effective_date=start)
                rows.append(row)
    return rows


def _rate_at(rates, heading, origin, market, day):
    for r in rates:
        if (r["hs_code"], r["origin_country"], r["destination_market"]) == (heading, origin, market) \
                and r["effective_date"] <= day and (r["end_date"] is None or r["end_date"] >= day):
            return r
    return None


def _entries(g, rates):
    r = g.rng
    P = {p["sku"]: p for p in g.master("products")}
    S = {s["supplier_id"]: s for s in g.master("suppliers")}
    PO = {p["po_id"]: p for p in g.master("purchase_orders")}
    cands = []
    for ln in g.master("po_lines"):
        po = PO[ln["po_id"]]
        if po["status"] not in ("closed", "received"):
            continue
        origin = S[po["supplier_id"]]["country"]
        market = {"DC4": "EU", "DC5": "US"}.get(po["dest_site_id"], "UK")
        if (origin == "GB" and market == "UK") or (origin in EU_ORIGINS and market == "EU"):
            continue
        entry_date = date.fromisoformat(po["due_date"]) - timedelta(days=3)
        if entry_date > g.as_of or entry_date < g.as_of - timedelta(days=HISTORY_DAYS):
            continue
        cands.append((entry_date, ln, po, origin, market))
    cands.sort(key=lambda c: (c[0], c[1]["po_id"], int(c[1]["line_no"])))

    # the story supplier's most recent 11 entries (within two months) are held
    story = [c for c in cands if c[2]["supplier_id"] == STORY_SUPPLIER and c[0] >= g.as_of - timedelta(days=60)]
    held_ids = {(c[1]["po_id"], c[1]["line_no"]) for c in sorted(story, key=lambda c: c[0])[-11:]}
    out = []
    for entry_date, ln, po, origin, market in cands:
        prod = P[ln["sku"]]
        heading = prod["hs_code"][:4]
        qty = int(ln["qty_ordered"])
        value = round(qty * float(prod["unit_cost_gbp"]), 2)   # master unit cost, already in GBP
        rate = _rate_at(rates, heading, origin, market, entry_date)
        is_story = po["supplier_id"] == STORY_SUPPLIER and entry_date >= g.as_of - timedelta(days=365)
        claims_pref = rate["preferential_rate_pct"] is not None and (is_story or r.random() < 0.9)
        paid_rate = rate["preferential_rate_pct"] if claims_pref else rate["duty_rate_pct"]
        duty = round(value * paid_rate / 100.0, 2)
        vat = round((value + duty) * IMPORT_VAT[market] / 100.0, 2)
        status, notes, exposure = "cleared", "", 0.0
        if is_story:
            status = "held" if (ln["po_id"], ln["line_no"]) in held_ids else "cleared"
            notes = ("Held by customs: preference claimed without valid proof of origin"
                     if status == "held" else "Preference claimed; origin statement not on file")
            exposure = round(value * (rate["duty_rate_pct"] - paid_rate) / 100.0, 2)
        else:
            x = r.random()
            if x < 0.03 and entry_date >= g.as_of - timedelta(days=60):
                status, notes = "held", "Held for classification query"
            elif x < 0.06:
                status, notes = "amended", "Amended after clearance: classification corrected"
            elif x < 0.12:
                notes = "Valuation query: assists not declared"
                exposure = round(duty * 0.15, 2) if duty else round(value * 0.005, 2)
        held = status == "held"
        out.append({
            "entry_id": f"ENT-{len(out) + 1:06d}", "po_id": ln["po_id"], "sku": ln["sku"],
            "supplier_id": po["supplier_id"], "origin_country": origin, "destination_market": market,
            "declared_value_gbp": value, "hs_code_used": heading, "quantity": qty,
            "duty_paid_gbp": None if held else duty, "vat_paid_gbp": None if held else vat,
            "insurance_gbp": round(value * 0.005, 2), "freight_gbp": round(value * FREIGHT[po["mode"]], 2),
            "entry_date": entry_date,
            "cleared_date": None if held else min(g.as_of, entry_date + timedelta(days=r.randint(1, 4))),
            "status": status, "reassessment_exposure_gbp": exposure, "notes": notes, "updated_at": g.as_of})
    return out


def _scenarios(g, entries):
    def volume(origin, heading):
        return sum(e["declared_value_gbp"] for e in entries
                   if e["origin_country"] == origin and e["status"] in ("cleared", "amended")
                   and e["entry_date"] >= g.as_of - timedelta(days=365)
                   and (heading is None or e["hs_code_used"] == heading))
    spec = [
        ("TSC-900001", "Proposed 10% additional tariff on Turkey-origin goods", "TR", "All goods", None, 10, 50,
         "Shift volume to Portugal (zero duty) or Vietnam; negotiate cost-sharing with Turkish suppliers; selective price increases", 40),
        ("TSC-900002", "New tariffs on southern China-origin goods", "CN", "All goods", None, 15, 40,
         "Shift volume to Vietnam, Indonesia or Bangladesh; dual-source key styles; accept air freight premium during transition", 60),
        ("TSC-900003", "Safeguard duty on Vietnam-origin goods", "VN", "All goods", None, 20, 35,
         "Indonesia or Bangladesh as alternatives; reduce SKU count; premium pricing", 30),
        ("TSC-900004", "Additional 10% tariff on China-origin electricals", "CN", "8516", "8516", 10, 30,
         "Mexico or Vietnam sourcing; product redesign", 45),
    ]
    rows = []
    for sid, name, origin, rng_, heading, chg, prob, mitig, created in spec:
        vol = volume(origin, heading)
        rows.append({"scenario_id": sid, "scenario_name": name, "base_period": "2027", "origin_country": origin,
                     "hs_code_range": rng_, "duty_rate_change_pct": chg, "estimated_volume_gbp": round(vol, 2),
                     "estimated_duty_impact_gbp": round(vol * chg / 100.0, 2), "probability_pct": prob,
                     "mitigation_options": mitig, "created_date": g.as_of - timedelta(days=created),
                     "updated_at": g.as_of})
    return rows


# ---------------------------------------------------------------- VAT
ENTITIES = {"LE-UK": 20, "LE-PL": 23}
PERIODS = {"2026-Q1": (277, 187), "2026-Q2": (186, 96), "2026-Q3": (95, 5)}
OUT_S = ["Store sales settlement", "Online sales settlement", "Wholesale invoice", "Concession income"]
OUT_Z = ["Export sales - non-EU wholesale", "Export sales - non-EU marketplace"]
OUT_E = ["Exempt - insurance recharge", "Exempt - property rental income"]
IN_S = ["Supplier invoice - goods for resale", "Import VAT - customs entry", "Freight and logistics services",
        "Professional fees", "Store fit-out"]


def _vat(g):
    r = g.rng
    pos = [p["po_id"] for p in g.master("purchase_orders")]
    txns, returns = [], []

    def add(entity, period, code, direction, amount, desc, rate, day, invoice=None, tax_point=None, po=None):
        vat = round(amount * rate / 100.0, 2) if code == "S" else 0.0
        txns.append({"vat_txn_id": f"VTX-{len(txns) + 1:06d}", "entity_id": entity, "period": period,
                     "transaction_date": day, "invoice_number": invoice or f"INV-{r.randint(100000, 999999)}",
                     "vat_code": code, "amount_gbp": amount, "vat_gbp": vat, "description": desc,
                     "po_id": po, "status": "posted", "corrected_to_code": None, "direction": direction,
                     "tax_point_period": tax_point or period, "updated_at": g.as_of})

    for entity, rate in ENTITIES.items():
        for period, (a, b) in PERIODS.items():
            day = lambda: g.as_of - timedelta(days=r.randint(b, a))
            ins = [(round(r.uniform(10000, 180000), 2), r.choice(IN_S)) for _ in range(16)]
            in_vat = sum(x for x, _ in ins) * rate / 100.0
            outs = [round(r.uniform(15000, 250000), 2) for _ in range(14)]
            target = in_vat + r.uniform(90000, 220000)          # a normal quarter: modest net VAT payable
            k = target / (sum(outs) * rate / 100.0)
            for x in outs:
                add(entity, period, "S", "output", round(x * k, 2), r.choice(OUT_S), rate, day())
            for _ in range(3):
                add(entity, period, "Z", "output", round(r.uniform(20000, 120000), 2), r.choice(OUT_Z), rate, day())
            add(entity, period, "E", "output", round(r.uniform(5000, 40000), 2), r.choice(OUT_E), rate, day())
            for x, desc in ins:
                add(entity, period, "S", "input", x, desc, rate, day(),
                    po=r.choice(pos) if desc.startswith(("Supplier", "Import")) else None)
            if (entity, period) == ("LE-PL", "2026-Q3"):
                # the story: three non-EU export sales posted at the standard rate (should be zero-rated)
                d = lambda n: g.as_of - timedelta(days=n)
                add(entity, period, "S", "output", 900000.0, "Export sales - non-EU wholesale (Ukraine)", rate, d(40), "INV-480121")
                add(entity, period, "S", "output", 450000.0, "Export sales - non-EU marketplace", rate, d(33), "INV-480377")
                add(entity, period, "S", "output", 300000.0, "Export sales - non-EU wholesale (Serbia)", rate, d(21), "INV-480902")
                # a manual accrual adjustment posted twice
                for n in (14, 13):
                    add(entity, period, "S", "output", 654347.83, "Manual adjustment - sales accrual", rate, d(n), "INV-ADJ-0917")
                # an October invoice booked into September
                add(entity, period, "S", "output", 304347.83, "Sales invoiced early for October delivery", rate, d(6),
                    "INV-481260", tax_point="2026-Q4")
        # each return is the sum of its postings
    for entity, rate in ENTITIES.items():
        prev = None
        for period, (a, b) in PERIODS.items():
            mine = [t for t in txns if t["entity_id"] == entity and t["period"] == period]
            box1 = round(sum(t["vat_gbp"] for t in mine if t["direction"] == "output"), 2)
            box5 = round(sum(t["vat_gbp"] for t in mine if t["direction"] == "input"), 2)
            box6 = round(box1 - box5, 2)
            if (entity, period) == ("LE-PL", "2026-Q3"):
                expected = round(box6 - 600000.0, 2)
            else:
                expected = round(box6 * (1 + r.uniform(-0.02, 0.02)), 2)
            submitted = period != "2026-Q3"
            returns.append({
                "entity_id": entity, "period": period, "box_1_gbp": box1, "box_2_gbp": 0.0, "box_4_gbp": box1,
                "box_5_gbp": box5, "box_6_gbp": box6,
                "box_7_gbp": round(sum(t["amount_gbp"] for t in mine if t["direction"] == "output"), 2),
                "box_8_gbp": round(sum(t["amount_gbp"] for t in mine if t["direction"] == "input"), 2),
                "expected_box_6_gbp": expected, "variance_gbp": round(box6 - expected, 2),
                "submitted": submitted,
                "submitted_date": g.as_of - timedelta(days=b - 38) if submitted else None,
                "updated_at": g.as_of})
    return txns, returns


def generate(g):
    rates = _rates(g)
    entries = _entries(g, rates)
    txns, returns = _vat(g)
    return {
        "duty_rates": rates,
        "import_entries": entries,
        "tariff_scenarios": _scenarios(g, entries),
        "vat_transactions": txns,
        "vat_returns": returns,
    }
