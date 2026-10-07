def generate(g):
    """
    Generate data warehouse tables.
    - product_sales_fact: daily sales by product/market/size
    - product_kpi_history: monthly KPI time series
    - otif_metrics: weekly OTIF metrics by dimension
    - product_markdown_rate: monthly markdown rates
    - product_launch_history: past new product launches
    - inventory_balance_reconciliation: inventory reconciliation
    - product_performance_metrics: product performance summary
    - warehouse_data_catalogue: table schema index
    - warehouse_column_index: column index
    - saved_warehouse_views: saved views
    """

    # Get master data
    products = g.master("products")
    suppliers = g.master("suppliers")
    sites = g.master("sites")
    carriers = g.master("carriers")
    calendar = g.master("calendar")

    # Get SKUs and styles for stories
    skus = [p["sku"] for p in products]
    styles = list(set(p["style_id"] for p in products))
    categories = list(set(p["category"] for p in products))

    # Markets
    markets = ["UK", "DE", "FR", "US", "IE", "NL"]
    inbound_modes = ["sea", "air", "truck", "rail"]

    # Generate product_sales_fact: fortnightly Monday rows per sku/market (weekly for style STY-T-4410)
    import hashlib
    import random
    from pathlib import Path
    import yaml
    from collections import defaultdict
    from datetime import date as _date, timedelta as _td

    def _h(s):
        return int(hashlib.md5(s.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF

    def _rr(*parts):
        """Random stream private to one entity, so the data does not shift when master rows are added or removed."""
        return random.Random("dw|" + "|".join(str(x) for x in parts))

    cty_market = {"GB": "UK", "DE": "DE", "US": "US", "IE": "IE", "NL": "NL", "PL": "PL"}
    stores = defaultdict(list)
    for s in sites:
        if s["type"] == "store" and s["country"] in cty_market and s["status"] == "open":
            stores[cty_market[s["country"]]].append(s["site_id"])
    prod_by_sku = {p["sku"]: p for p in products}
    by_cat = defaultdict(list)
    for p in sorted(products, key=lambda x: x["sku"]):
        by_cat[p["category"]].append(p)

    mondays = g.weeks(66)
    fort = [d for i, d in enumerate(mondays) if (len(mondays) - 1 - i) % 2 == 0]
    FASHION = ["Trousers", "Tops", "T-Shirts", "Shirts", "Knitwear", "Outerwear"]
    HOME = ["Lighting", "Storage", "Towels", "Bedding", "Cookware", "Drinkware", "Kitchenware"]
    # year-on-year demand growth by category (UK); other markets move with it
    YOY = {"Lighting": 0.38, "Storage": 0.24, "Cookware": 0.15, "Bedding": 0.08, "Drinkware": 0.05,
           "Towels": -0.02, "Kitchenware": 0.0, "Outerwear": 0.42, "Knitwear": 0.06, "Tops": 0.03,
           "T-Shirts": 0.04, "Shirts": 0.0, "Trousers": 0.05, "Small Appliances": 0.0}
    MKT_ADJ = {"UK": 0.0, "DE": -0.08, "US": -0.16}
    PREMIUM_SHARE = {"Knitwear": (0.32, 0.19), "Tops": (0.31, 0.19), "T-Shirts": (0.30, 0.20), "Shirts": (0.28, 0.20)}
    SA_COST_LY = {"SUP-0013": 0.875, "SUP-0062": 0.93}   # last year's landed cost vs today's, small appliances

    COMPLIANCE_GAP = {   # sku: (units per fortnight, base markdown share)
        "SKU-105551": (58, 0.08), "SKU-104732": (28, 0.14), "SKU-101813": (95, 0.35), "SKU-101148": (30, 0.10),
        "SKU-104809": (25, 0.08), "SKU-104354": (55, 0.10), "SKU-103745": (24, 0.10), "SKU-103199": (45, 0.40),
        "SKU-102779": (60, 0.12), "SKU-104060": (14, 0.10), "SKU-100336": (25, 0.10), "SKU-101428": (90, 0.10),
        "SKU-102394": (6, 0.30), "SKU-105943": (18, 0.10), "SKU-104123": (36, 0.08), "SKU-104795": (45, 0.30),
        "SKU-104592": (60, 0.40)}

    plan = []   # (product, markets)
    est_cut = (g.as_of - _td(days=90)).isoformat()
    for cat, plist in by_cat.items():
        plist = [p for p in plist if p["sku"] not in COMPLIANCE_GAP]   # these are generated separately below
        plist = [p for p in plist if p["launch_date"] <= est_cut] or plist   # established lines carry a year of history
        if cat in FASHION or cat == "Small Appliances":
            chosen = plist
            mk = ["UK"]
        elif cat in HOME:
            chosen = sorted(plist, key=lambda p: _h("pick" + p["sku"]))[:4]
            mk = ["UK", "DE", "US"]
        else:
            chosen = sorted(plist, key=lambda p: _h("pick" + p["sku"]))[:3]
            mk = ["UK"]
        for p in chosen:
            if p["style_id"] == "STY-T-4410":
                continue
            plan.append((p, mk))
    if "PF-220" not in {p["sku"] for p, _ in plan}:
        plan.append((prod_by_sku["PF-220"], ["UK"]))

    sales_fact = []
    seen_keys = set()

    BUDGET_SLOPE = {"UK": 0.16, "DE": 0.03, "US": 0.09}   # cost pressure: budget shoppers' share grows fastest in the UK

    def _segment(d, market, rr):
        age_y = min(1.0, max(0.0, (g.as_of - d).days / 365.0))
        b = 0.20 + BUDGET_SLOPE.get(market, 0.06) * (1 - age_y)
        r = rr.random()
        if r < b:
            return "Budget"
        return rr.choices(["Standard", "Premium", "VIP"], [62, 28, 10])[0]

    def add_row(p, d, market, units, md, cost_f=1.0, seg=None, size=None, rr=None):
        price = float(p["retail_price_gbp"])
        rr = rr or _rr("row", p["sku"], d, market)
        site = stores[market][int(_h(f"site|{p['sku']}|{d}|{market}") * len(stores[market]))]
        key = (d, p["sku"], site, size or p["size"])
        if key in seen_keys or units < 1:
            return
        seen_keys.add(key)
        gross = units * price
        sales_fact.append({
            "date": d, "sku": p["sku"], "style_id": p["style_id"], "category": p["category"], "market": market,
            "site_id": site, "size": size or p["size"], "units_sold": units,
            "sales_gbp": round(gross * (1 - md), 2), "cost_gbp": round(units * float(p["unit_cost_gbp"]) * cost_f, 2),
            "markdown_gbp": round(gross * md, 2),
            "customer_segment": seg or _segment(d, market, rr)})

    heroes = set()
    for cat in FASHION:
        cands = sorted([p["sku"] for p, _ in plan if p["category"] == cat], key=lambda k: _h("hero" + k))
        heroes |= set(cands[:3])
    for p, mk in plan:
        cat, sku = p["category"], p["sku"]
        lead = int(p["lead_time_days"])
        launch = _date.fromisoformat(p["launch_date"])
        base = 8 * (2.718 ** _rr("base", sku).gauss(0, 0.6))
        if sku in heroes:
            base *= 4
        if cat == "Small Appliances":
            base = 30 * (2.718 ** _rr("base", sku).gauss(0, 0.25))
        if sku == "K-1700":
            base = 70
        if cat in HOME:
            base *= 2
        base_md = min(0.45, 0.08 + 0.0022 * lead) + (0.18 if p["status"] == "clearance" else 0)
        for d in fort:
            age_y = (g.as_of - d).days / 365.0
            for market in mk:
                rr = _rr("row", sku, d, market)
                gr = YOY.get(cat, round((_h(cat) - 0.5) * 0.12, 3)) + MKT_ADJ[market]
                units = base * (1 + gr) ** (-age_y) * (0.5 if market != "UK" else 1.0) * rr.uniform(0.88, 1.12)
                md = max(0.02, base_md + rr.uniform(-0.03, 0.03))
                cost_f = 1.0
                if cat == "Small Appliances":
                    ly = age_y > 0.55
                    if ly:
                        cost_f = SA_COST_LY.get(p["supplier_id"], 0.97)
                    md = (0.12 if ly else 0.30) if sku == "K-1700" else 0.14 + rr.uniform(-0.01, 0.01)
                    units = base * (0.92 if (ly and sku == "K-1700") else 1.0) * rr.uniform(0.97, 1.03)
                seg = None
                if cat in PREMIUM_SHARE:
                    a, b = PREMIUM_SHARE[cat]
                    share = b + (a - b) * min(1.0, max(0.0, age_y))
                    seg = "Premium" if rr.random() < share else rr.choices(["Standard", "Budget", "VIP"], [60, 30, 10])[0]
                add_row(p, d, market, max(1, round(units)), md, cost_f, seg, rr=rr)

    # style STY-T-4410 (white trousers): weekly sales for each size, UK and DE
    for p in sorted([x for x in products if x["style_id"] == "STY-T-4410"], key=lambda x: x["sku"]):
        size_w = {"10": 80, "12": 100, "14": 70}.get(p["size"], 60)
        for d in mondays:
            for market, mult in (("UK", 1.0), ("DE", 0.35)):
                rr = _rr("row", p["sku"], d, market)
                add_row(p, d, market, round(size_w * mult * rr.uniform(0.9, 1.1)), 0.14 + rr.uniform(-0.02, 0.02), rr=rr)

    # Best sellers that lack EU/Ireland compliance data (see compliance_db): make sure they sell, so their sales
    # rank can be looked up. Own random stream per row.
    planned_skus = {p["sku"] for p, _ in plan}
    for sku, (base_u, md0) in COMPLIANCE_GAP.items():
        p = prod_by_sku.get(sku)
        if not p or sku in planned_skus:
            continue
        launch = _date.fromisoformat(p["launch_date"])
        stop = g.as_of - _td(days=60) if p["status"] == "discontinued" else None
        gr = YOY.get(p["category"], round((_h(p["category"]) - 0.5) * 0.12, 3))
        for d in fort:
            if d < launch + _td(days=7) or (stop and d > stop):
                continue
            age_y = (g.as_of - d).days / 365.0
            xr = _rr("gap", sku, d)
            units = max(1, round(base_u * (1 + gr) ** (-age_y) * xr.uniform(0.9, 1.1)))
            md = max(0.02, md0 + xr.uniform(-0.02, 0.02))
            site = stores["UK"][int(_h(sku + d.isoformat()) * len(stores["UK"]))]
            key = (d, sku, site, p["size"])
            if key in seen_keys:
                continue
            seen_keys.add(key)
            gross = units * float(p["retail_price_gbp"])
            sales_fact.append({
                "date": d, "sku": sku, "style_id": p["style_id"], "category": p["category"], "market": "UK",
                "site_id": site, "size": p["size"], "units_sold": units, "sales_gbp": round(gross * (1 - md), 2),
                "cost_gbp": round(units * float(p["unit_cost_gbp"]), 2), "markdown_gbp": round(gross * md, 2),
                "customer_segment": xr.choices(["Budget", "Standard", "Premium", "VIP"], [24, 46, 22, 8])[0]})

    # OTIF by supplier / category / DC / inbound mode / arrival weekday, weekly. The OTIF definition tightened on the
    # Tuesday of the first September week (no grace day any more), which hits the road (truck) inbound flows hardest.
    OTIF_COMBOS = [  # supplier, category, DC, inbound mode, weekday, units per week, OTIF % before, OTIF % after
        ("SUP-0079", "Outerwear", "DC1", "truck", "Fri", 6200, 95.0, 81.5),
        ("SUP-0037", "Knitwear", "DC3", "truck", "Mon", 4100, 94.5, 82.0),
        ("SUP-0030", "Knitwear", "DC4", "truck", "Fri", 4600, 93.5, 84.5),
        ("SUP-0014", "Footwear", "DC2", "truck", "Wed", 3000, 94.0, 91.0),
        ("SUP-0001", "Dresses", "DC1", "sea", "Tue", 9000, 93.5, 93.0),
        ("SUP-0013", "Small Appliances", "DC1", "air", "Thu", 3200, 96.0, 95.5),
        ("SUP-0028", "Footwear", "DC5", "sea", "Wed", 5400, 94.0, 91.5),
        ("SUP-0064", "Dresses", "DC4", "rail", "Tue", 3300, 93.0, 92.0)]
    otr = random.Random(20260901)
    ot_weeks = g.weeks(8)            # 4 weeks before the change (the last one only partly) and 4 weeks after
    raw = []
    for wi, wk in enumerate(ot_weeks):
        for sup, cat, dc, mode, wd, units, before, after in OTIF_COMBOS:
            frac = 0.0 if wi < 3 else 0.2 if wi == 3 else 1.0
            pct = before + (after - before) * frac + otr.uniform(-0.6, 0.6)
            raw.append([wk, sup, cat, dc, mode, wd, int(units * otr.uniform(0.93, 1.07)), pct, wi])
    for lo, hi, goal in ((0, 3, 94.0), (4, 7, 89.0)):     # calibrate each month to the OTIF the business reported
        rows = [r for r in raw if lo <= r[8] <= hi]
        tot = sum(r[6] for r in rows)
        for _ in range(30):
            cur = sum(r[6] * r[7] for r in rows) / tot
            for r in rows:
                r[7] = min(99.5, r[7] + (goal - cur))
    otif_metrics = []
    for wk, sup, cat, dc, mode, wd, total, pct, _wi in raw:
        on_time = round(total * pct / 100)
        early = round(total * otr.uniform(0.01, 0.04))
        otif_metrics.append({
            "week": wk, "supplier_id": sup, "category": cat, "site_id": dc, "inbound_mode": mode, "weekday": wd,
            "on_time_units": on_time, "total_units": total, "otif_pct": round(100.0 * on_time / total, 1),
            "early_units": early, "late_units": total - on_time - early})

    # KPI history: 18 monthly points (last year's peak included) per KPI, plus the last 8 weeks.
    # name: (target, higher_is_better, unit, monthly values from 17 months ago to last month)
    KPIS = {
        "OTIF": (90.0, True, "%", [93.4, 93.8, 94.1, 93.6, 93.9, 93.2, 92.8, 90.1, 88.2, 92.6, 93.3, 93.7, 94.0, 94.2, 94.1, 93.9, 94.0, 89.0]),
        "markdown_rate": (20.0, False, "%", [21.4, 20.8, 22.1, 26.5, 24.8, 21.2, 20.5, 24.9, 27.8, 31.5, 26.3, 21.9, 21.0, 20.6, 22.4, 27.2, 25.1, 23.4]),
        "sell_through_rate": (75.0, True, "%", [74.8, 75.6, 76.1, 74.2, 75.0, 76.4, 77.1, 72.3, 69.5, 70.8, 73.9, 75.2, 75.8, 76.0, 75.1, 73.6, 74.4, 71.9]),
        "inventory_turns": (6.0, True, "turns", [6.1, 6.2, 6.3, 6.2, 6.1, 6.0, 5.9, 6.4, 6.8, 5.7, 5.8, 5.9, 6.0, 6.1, 6.2, 6.1, 6.0, 5.9]),
        "cost_per_unit_gbp": (2.41, False, "GBP", [2.38, 2.37, 2.36, 2.38, 2.37, 2.39, 2.42, 2.55, 2.63, 2.44, 2.40, 2.38, 2.37, 2.38, 2.36, 2.39, 2.40, 2.42]),
        "inventory_accuracy": (98.5, True, "%", [98.8, 98.9, 98.7, 98.9, 98.8, 98.7, 98.8, 98.4, 98.1, 98.6, 98.8, 98.9, 98.8, 98.9, 99.0, 98.8, 98.9, 98.7]),
    }
    mon0 = _date(g.as_of.year, g.as_of.month, 1)
    month_starts = []
    yy, mm = mon0.year, mon0.month
    for _ in range(18):
        mm -= 1
        if mm == 0:
            mm, yy = 12, yy - 1
        month_starts.append(_date(yy, mm, 1))
    month_starts.reverse()
    wk_otif = {}
    for r in otif_metrics:
        a = wk_otif.setdefault(r["week"], [0, 0])
        a[0] += r["on_time_units"]; a[1] += r["total_units"]

    def _kpi_row(d, name, val, ptype):
        target, hib, unit, _ = KPIS[name]
        dp = 1 if unit == "%" else 2
        return {"date": d, "kpi_name": name, "kpi_value": round(val, dp), "period_type": ptype, "target_value": target,
                "variance_pct": round(100.0 * (val - target) / target, 1), "higher_is_better": hib, "unit": unit}

    kpi_history = []
    for name, (_t, _h_, _u, vals) in KPIS.items():
        for d, v in zip(month_starts, vals):
            kpi_history.append(_kpi_row(d, name, v, "monthly"))
        for wk in ot_weeks:
            mval = vals[month_starts.index(_date(wk.year, wk.month, 1))] if _date(wk.year, wk.month, 1) in month_starts else vals[-1]
            if name == "OTIF":
                v = 100.0 * wk_otif[wk][0] / wk_otif[wk][1]
            else:
                v = mval * (1 + (_h(name + wk.isoformat()) - 0.5) * (0.01 if _u == "%" else 0.04))
            kpi_history.append(_kpi_row(wk, name, v, "weekly"))

    # Generate product_markdown_rate: monthly history for fashion and small-appliance SKUs
    markdown_rate = []
    months = []
    y, m = g.as_of.year, g.as_of.month
    for i in range(12):
        m -= 1
        if m == 0:
            m, y = 12, y - 1
        months.append(_date(y, m, 1))
    months.reverse()
    for cat in FASHION + ["Small Appliances"]:
        for p in by_cat[cat]:
            if p["launch_date"] > est_cut:
                continue
            lead = int(p["lead_time_days"])
            base_md = min(0.45, 0.08 + 0.0022 * lead) + (0.18 if p["status"] == "clearance" else 0)
            for mo in months:
                mr = _rr("md", p["sku"], mo)
                season_bump = 0.07 if mo.month in (1, 7) else 0.0
                rate = min(0.8, max(0.02, base_md + season_bump + mr.uniform(-0.03, 0.03)))
                units = int(60 * (2.718 ** mr.gauss(0, 0.5)))
                mdu = int(units * rate)
                markdown_rate.append({
                    "sku": p["sku"], "style_id": p["style_id"], "category": cat, "period_type": "monthly",
                    "period": mo, "units_sold": units, "full_price_units": units - mdu, "markdown_units": mdu,
                    "markdown_rate_pct": round(100.0 * mdu / max(units, 1), 1),
                    "avg_markdown_depth_pct": round(100 * rate * 0.9 + 8, 1), "lead_time_days": lead,
                    "cumulative_markdown_gbp": round(mdu * float(p["retail_price_gbp"]) * rate, 2)})

    # Generate product_launch_history: every product launched at least 5 weeks ago, with its master launch date
    FASHION_FWD = {"Outerwear", "Knitwear", "Dresses", "Footwear", "Blouses", "Scarves", "Fragrance"}
    launches = []
    cutoff = (g.as_of - _td(days=35)).isoformat()
    for n, p in enumerate(sorted([x for x in products if x["launch_date"] <= cutoff], key=lambda x: (x["launch_date"], x["sku"])), 1):
        lr = random.Random("lnc-" + p["sku"])
        fwd = p["category"] in FASHION_FWD
        alloc = int(300 + 1700 * lr.random())
        month1 = int(alloc * (lr.uniform(0.35, 0.98) if fwd else lr.uniform(0.55, 0.98)))
        week1 = int(month1 * lr.uniform(0.2, 0.38))
        peak = max(week1, int(month1 * lr.uniform(0.3, 0.42)))
        fva = 100 + (8 if fwd else 1) + lr.gauss(0, 22 if fwd else 8)
        days = (g.as_of - _date.fromisoformat(p["launch_date"])).days
        launches.append({
            "launch_id": f"LNC-{n:06d}", "sku": p["sku"], "style_id": p["style_id"], "category": p["category"],
            "launch_date": p["launch_date"], "initial_allocation_units": alloc, "units_sold_week1": week1,
            "units_sold_month1": month1, "forecast_vs_actual_pct": round(min(160, max(55, fva)), 1),
            "sell_through_rate_pct": round(100.0 * month1 / alloc, 1), "peak_week_demand_units": peak,
            "status": "discontinued" if p["status"] == "discontinued" else "launched" if days <= 120 else "evergreen"})

    # Generate product_performance_metrics: one current row per sku with sales (derived from the sales fact)
    perf_metrics = []
    cut = g.as_of - _td(days=90)
    agg = defaultdict(lambda: [0, 0.0, 0.0, 0.0])
    for r in sales_fact:
        if r["date"] >= cut:
            a = agg[r["sku"]]
            a[0] += r["units_sold"]; a[1] += r["sales_gbp"]; a[2] += r["cost_gbp"]; a[3] += r["markdown_gbp"]
    ranked = sorted(agg, key=lambda s: -agg[s][1])
    for rank, sku in enumerate(ranked, 1):
        product = prod_by_sku[sku]
        u, s_, c_, mdv = agg[sku]
        hv = _h(product["style_id"])
        role = "clearance" if product["status"] == "clearance" else ("strategic" if hv < 0.12 else "growth" if hv < 0.35 else "core")
        perf_metrics.append({
            "sku": sku, "style_id": product["style_id"], "category": product["category"], "period": "latest",
            "units_sold": u, "sales_gbp": round(s_, 2), "margin_gbp": round(s_ - c_, 2),
            "margin_pct": round(100 * (s_ - c_) / s_, 1) if s_ else 0,
            "markdown_rate_pct": round(100 * mdv / (s_ + mdv), 1) if s_ else 0,
            "in_stock_rate_pct": round(55 + 44 * _h("is" + sku), 1), "velocity_rank": rank,
            "strategic_role": role, "recommend_action": "",
            "return_rate_pct": round(0.5 + 6 * _h("rr" + sku), 1)})

    # Staging copies of the WMS, TMS and ERP order data (for the cost-per-order model), for a sample of recent orders
    orders = g.master("orders")
    ent_by_country = {"GB": "LE-UK", "IE": "LE-IE", "DE": "LE-DE", "NL": "LE-NL", "US": "LE-US"}
    ent_by_site = {"DC1": "LE-UK", "DC2": "LE-UK", "DC3": "LE-UK", "DC4": "LE-NL", "DC5": "LE-US"}
    cutoff_o = (g.as_of - _td(days=75)).isoformat()
    wms_costs, tms_costs, erp_orders = [], [], []
    ship_n = 800000
    for o in orders:
        if o["order_date"] < cutoff_o or o["status"] in ("cancelled", "placed") or _h("ord" + o["order_id"]) > 0.12:
            continue
        oid, units = o["order_id"], int(o["units"])
        lines = max(1, min(units, 1 + int(_h("ln" + oid) * min(units, 5))))
        pick_min = round(lines * 1.2 + units * 0.3, 1)
        pick, pack = round(pick_min * 0.25, 2), round(units * 0.15, 2)
        handling = round(lines * 0.5 + lines * 0.75, 2)
        wms_costs.append({"order_id": oid, "fulfil_site_id": o["fulfil_site_id"], "order_date": o["order_date"],
                          "order_lines": lines, "units": units, "pick_time_minutes": pick_min, "pick_labour_gbp": pick,
                          "pack_labour_gbp": pack, "handling_cost_gbp": handling, "total_cost_gbp": round(pick + pack + handling, 2)})
        n_ship = 1
        if units >= 2 and _h("sp" + oid) < 0.09:
            n_ship = 2 if units < 4 or _h("sq" + oid) < 0.8 else 3
        carriers_ = ["CAR-011", "CAR-013"] if o["country"] == "GB" else ["CAR-012", "CAR-014"]
        base_u, extra = divmod(units, n_ship)
        for i in range(n_ship):
            su = base_u + (1 if i < extra else 0)
            ship_n += 1
            cost = round((3.4 if o["country"] == "GB" else 7.9) * (1 + 0.8 * _h("fc" + oid + str(i))) + 0.35 * su, 2)
            tms_costs.append({"shipment_id": f"SHP-{ship_n:06d}", "order_id": oid, "carrier_id": carriers_[i % 2],
                              "mode": "parcel", "ship_date": _date.fromisoformat(o["order_date"]) + _td(days=i + (0 if _h("sd" + oid) < 0.6 else 1)),
                              "units": su, "freight_cost_gbp": cost, "is_split": n_ship > 1})
        value = float(o["value_gbp"])
        fr = {"standard": 0.0 if value >= 50 else 3.99, "next_day": 5.99, "same_day": 8.99, "collect": 0.0}[o["delivery_service"]]
        erp_orders.append({"order_id": oid, "entity_id": ent_by_country.get(o["country"], ent_by_site.get(o["fulfil_site_id"], "LE-UK")),
                           "posting_date": o["order_date"], "revenue_gbp": round(value, 2), "freight_charge_gbp": fr,
                           "handling_charge_gbp": 0.95 if value < 25 else 0.0,
                           "discount_gbp": round(value * 0.05, 2) if _h("dc" + oid) < 0.15 else 0.0})

    # Generate warehouse_data_catalogue and warehouse_column_index from the table definitions
    here = Path(__file__).resolve().parent
    own = yaml.safe_load(open(here / "system.yaml"))["tables"]
    mst = yaml.safe_load(open(here.parent / "_master" / "system.yaml"))["tables"]
    import csv as _csv

    def _seed_n(name):
        f = here / "seed" / f"{name}.csv"
        return sum(1 for _ in _csv.DictReader(open(f))) if f.exists() else 0

    counts = {"product_sales_fact": len(sales_fact), "product_kpi_history": len(kpi_history), "otif_metrics": len(otif_metrics),
              "product_markdown_rate": len(markdown_rate), "product_launch_history": len(launches),
              "inventory_balance_reconciliation": _seed_n("inventory_balance_reconciliation"),
              "product_performance_metrics": len(perf_metrics), "wms_order_costs": len(wms_costs) + _seed_n("wms_order_costs"),
              "tms_shipment_costs": len(tms_costs) + _seed_n("tms_shipment_costs"),
              "erp_order_headers": len(erp_orders) + _seed_n("erp_order_headers"),
              "warehouse_data_catalogue": 0, "warehouse_column_index": 0, "saved_warehouse_views": _seed_n("saved_warehouse_views")}
    META = {  # table: (type, description, grain, refresh)
        "product_sales_fact": ("fact", "Daily product sales, cost and markdown by market, store, size and customer segment", "One row per date/sku/site/size", "daily"),
        "product_kpi_history": ("fact", "Monthly and weekly supply-chain and trading KPIs with targets", "One row per period/kpi/period type", "monthly"),
        "otif_metrics": ("fact", "Weekly on-time-in-full by supplier, category, DC, inbound mode and arrival weekday", "One row per week/supplier/category/dc/mode", "weekly"),
        "product_markdown_rate": ("fact", "Markdown rate and lead time by product and month", "One row per sku/period type/period", "monthly"),
        "product_launch_history": ("fact", "New product launches with early-life demand, sell-through and forecast accuracy", "One row per launch", "as_launched"),
        "inventory_balance_reconciliation": ("fact", "Inventory units in WMS, ERP and finance with physical count and variance type", "One row per date/site/sku", "daily"),
        "product_performance_metrics": ("fact", "Trailing 90-day product performance summary", "One row per sku/period", "monthly"),
        "wms_order_costs": ("fact", "Order pick, pack and handling cost replicated from the WMS (one row per order)", "One row per order", "daily"),
        "tms_shipment_costs": ("fact", "Outbound shipment freight cost replicated from the TMS; a split order has several shipments", "One row per shipment", "daily"),
        "erp_order_headers": ("fact", "Order header revenue, delivery charges and discount from the ERP", "One row per order", "daily"),
        "warehouse_data_catalogue": ("dimension", "Index of warehouse tables", "One row per table", "manual"),
        "warehouse_column_index": ("dimension", "Index of warehouse columns", "One row per table/column", "manual"),
        "saved_warehouse_views": ("dimension", "Saved warehouse views", "One row per view", "manual"),
    }
    MASTER_META = {"orders": "Customer orders (master): channel, fulfilling site, country, units, value, status",
                   "shipments": "Inbound PO shipments (master): carrier, mode, ports, ETD/ETA",
                   "products": "Product master: sku, style, category, supplier, cost, price, lead time",
                   "sites": "Sites master: DCs, stores and offices", "carriers": "Carrier master: mode and scope",
                   "suppliers": "Supplier master"}
    catalogue, col_index = [], []

    def _cols(tname, cols, source):
        for i, (cname, c) in enumerate(cols.items(), 1):
            col_index.append({"table_name": tname, "column_name": cname, "ordinal": i, "column_type": c["type"],
                              "description": c.get("desc", ""), "source_system": source})

    SRC = {"wms_order_costs": "wms", "tms_shipment_costs": "tms", "erp_order_headers": "erp"}
    for tname, (ttype, desc, grain, freq) in META.items():
        key = own[tname]["key"]
        catalogue.append({"table_name": tname, "table_type": ttype, "description": desc, "row_count": counts[tname],
                          "grain": grain, "primary_key": "[" + ", ".join(key) + "]" if isinstance(key, list) else key,
                          "last_updated": g.as_of, "refresh_frequency": freq})
        _cols(tname, own[tname]["cols"], SRC.get(tname, "warehouse"))
    for tname, desc in MASTER_META.items():
        key = mst[tname]["key"]
        catalogue.append({"table_name": "master." + tname, "table_type": "master", "description": desc,
                          "row_count": len(g.master(tname)), "grain": "One row per " + (key if isinstance(key, str) else "/".join(key)),
                          "primary_key": "[" + ", ".join(key) + "]" if isinstance(key, list) else key,
                          "last_updated": g.as_of, "refresh_frequency": "daily"})
        _cols("master." + tname, mst[tname]["cols"], "master")

    for c in catalogue:
        if c["table_name"] == "warehouse_data_catalogue":
            c["row_count"] = len(catalogue)
        elif c["table_name"] == "warehouse_column_index":
            c["row_count"] = len(col_index)

    views = []   # saved views are created through create_warehouse_view (one is seeded)
    inventory_recon = []   # seeded: see seed/inventory_balance_reconciliation.csv

    return {
        "product_sales_fact": sales_fact,
        "product_kpi_history": kpi_history,
        "otif_metrics": otif_metrics,
        "product_markdown_rate": markdown_rate,
        "product_launch_history": launches,
        "inventory_balance_reconciliation": inventory_recon,
        "product_performance_metrics": perf_metrics,
        "wms_order_costs": wms_costs,
        "tms_shipment_costs": tms_costs,
        "erp_order_headers": erp_orders,
        "warehouse_data_catalogue": catalogue,
        "warehouse_column_index": col_index,
        "saved_warehouse_views": views,
    }
