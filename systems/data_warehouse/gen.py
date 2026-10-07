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
    from collections import defaultdict
    from datetime import date as _date, timedelta as _td

    def _h(s):
        return int(hashlib.md5(s.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF

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
    PREMIUM_SHARE = {"Knitwear": (0.36, 0.17), "Tops": (0.34, 0.18), "T-Shirts": (0.33, 0.20), "Shirts": (0.30, 0.20)}
    SA_COST_LY = {"SUP-0013": 0.80}   # last year's landed cost vs today's, small appliances

    plan = []   # (product, markets)
    for cat, plist in by_cat.items():
        if cat in FASHION or cat == "Small Appliances":
            chosen = plist
            mk = ["UK"]
        elif cat in HOME:
            chosen = g.rng.sample(plist, min(4, len(plist)))
            mk = ["UK", "DE", "US"]
        else:
            chosen = g.rng.sample(plist, min(3, len(plist)))
            mk = ["UK"]
        for p in chosen:
            if p["style_id"] == "STY-T-4410":
                continue
            plan.append((p, mk))
    if "PF-220" not in {p["sku"] for p, _ in plan}:
        plan.append((prod_by_sku["PF-220"], ["UK"]))

    sales_fact = []
    seen_keys = set()

    def add_row(p, d, market, units, md, cost_f=1.0, seg=None, size=None):
        price = float(p["retail_price_gbp"])
        site = g.pick(stores[market])
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
            "customer_segment": seg or g.rng.choices(["Standard", "Budget", "Premium", "VIP"], [50, 22, 20, 8])[0]})

    hero_n = defaultdict(int)
    for p, mk in plan:
        cat, sku = p["category"], p["sku"]
        lead = int(p["lead_time_days"])
        launch = _date.fromisoformat(p["launch_date"])
        base = 8 * (2.718 ** g.rng.gauss(0, 0.6))
        if cat in FASHION and hero_n[cat] < 3:
            hero_n[cat] += 1
            base *= 4
        if cat == "Small Appliances":
            base = 30 * (2.718 ** g.rng.gauss(0, 0.25))
        if sku == "K-1700":
            base = 70
        if cat in HOME:
            base *= 2
        base_md = min(0.45, 0.08 + 0.0022 * lead) + (0.18 if p["status"] == "clearance" else 0)
        for d in fort:
            if d < launch:
                continue
            age_y = (g.as_of - d).days / 365.0
            for market in mk:
                gr = YOY.get(cat, round((_h(cat) - 0.5) * 0.12, 3)) + MKT_ADJ[market]
                units = base * (1 + gr) ** (-age_y) * (0.5 if market != "UK" else 1.0) * g.rng.uniform(0.88, 1.12)
                md = max(0.02, base_md + g.rng.uniform(-0.03, 0.03))
                cost_f = 1.0
                if cat == "Small Appliances":
                    ly = age_y > 0.55
                    if ly:
                        cost_f = SA_COST_LY.get(p["supplier_id"], 0.97)
                    md = (0.12 if ly else 0.30) if sku == "K-1700" else 0.14 + g.rng.uniform(-0.01, 0.01)
                    units = base * (0.92 if (ly and sku == "K-1700") else 1.0) * g.rng.uniform(0.97, 1.03)
                seg = None
                if cat in PREMIUM_SHARE:
                    a, b = PREMIUM_SHARE[cat]
                    share = b + (a - b) * min(1.0, max(0.0, age_y))
                    seg = "Premium" if g.rng.random() < share else g.rng.choices(["Standard", "Budget", "VIP"], [60, 30, 10])[0]
                add_row(p, d, market, max(1, round(units)), md, cost_f, seg)

    # style STY-T-4410 (white trousers): weekly sales for each size, UK and DE
    for p in sorted([x for x in products if x["style_id"] == "STY-T-4410"], key=lambda x: x["sku"]):
        size_w = {"10": 80, "12": 100, "14": 70}.get(p["size"], 60)
        for d in mondays:
            if d < _date.fromisoformat(p["launch_date"]):
                continue
            for market, mult in (("UK", 1.0), ("DE", 0.35)):
                add_row(p, d, market, round(size_w * mult * g.rng.uniform(0.9, 1.1)), 0.14 + g.rng.uniform(-0.02, 0.02))

    # Generate product_kpi_history
    kpi_history = []
    kpi_names = ["OTIF", "markdown_rate", "sell_through", "sell_through_rate", "inventory_turns"]
    for week in g.weeks(-26):
        for kpi_name in kpi_names:
            if kpi_name == "OTIF":
                base_value = 92
                variance = g.rng.uniform(-5, 3)
            elif kpi_name == "markdown_rate":
                base_value = 25
                variance = g.rng.uniform(-8, 8)
            else:
                base_value = 70 + g.rng.randint(-20, 20)
                variance = g.rng.uniform(-5, 5)

            target = 90 if kpi_name == "OTIF" else 20 if kpi_name == "markdown_rate" else 75
            value = max(0, min(100, base_value + variance))

            kpi_history.append({
                "date": week,
                "kpi_name": kpi_name,
                "kpi_value": round(value, 1),
                "period_type": "weekly",
                "target_value": target,
                "variance_pct": round(value - target, 1)
            })

            # Add monthly aggregates
            if week.weekday() == 0:  # Monday
                kpi_history.append({
                    "date": week,
                    "kpi_name": kpi_name,
                    "kpi_value": round(value + g.rng.uniform(-2, 2), 1),
                    "period_type": "monthly",
                    "target_value": target,
                    "variance_pct": round(value - target + g.rng.uniform(-2, 2), 1)
                })

    # Generate otif_metrics
    otif_metrics = []
    for week in g.weeks(-12):
        for supplier in g.pick(suppliers, k=8):
            for category in g.pick(categories, k=3):
                for site in g.pick([s for s in sites if s["type"] == "dc"], k=3):
                    for mode in g.pick(inbound_modes, k=2):
                        for weekday_num in range(5):  # Mon-Fri
                            total = g.rng.randint(500, 3000)
                            on_time_pct = g.rng.uniform(0.85, 0.96)
                            on_time = int(total * on_time_pct)
                            early = int(total * g.rng.uniform(0.02, 0.08))
                            late = total - on_time - early

                            otif_metrics.append({
                                "week": week,
                                "supplier_id": supplier["supplier_id"],
                                "category": category,
                                "site_id": site["site_id"],
                                "inbound_mode": mode,
                                "weekday": ["Mon", "Tue", "Wed", "Thu", "Fri"][weekday_num],
                                "on_time_units": on_time,
                                "total_units": total,
                                "otif_pct": round(on_time_pct * 100, 1),
                                "early_units": early,
                                "late_units": late
                            })

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
            lead = int(p["lead_time_days"])
            base_md = min(0.45, 0.08 + 0.0022 * lead) + (0.18 if p["status"] == "clearance" else 0)
            for mo in months:
                if mo < _date.fromisoformat(p["launch_date"]):
                    continue
                season_bump = 0.07 if mo.month in (1, 7) else 0.0
                rate = min(0.8, max(0.02, base_md + season_bump + g.rng.uniform(-0.03, 0.03)))
                units = int(60 * (2.718 ** g.rng.gauss(0, 0.5)))
                mdu = int(units * rate)
                markdown_rate.append({
                    "sku": p["sku"], "style_id": p["style_id"], "category": cat, "period_type": "monthly",
                    "period": mo, "units_sold": units, "full_price_units": units - mdu, "markdown_units": mdu,
                    "markdown_rate_pct": round(100.0 * mdu / max(units, 1), 1),
                    "avg_markdown_depth_pct": round(100 * rate * 0.9 + 8, 1), "lead_time_days": lead,
                    "cumulative_markdown_gbp": round(mdu * float(p["retail_price_gbp"]) * rate, 2)})

    # Generate product_launch_history
    launches = []
    for i in range(50):
        sku = g.pick(skus)
        product = next((p for p in products if p["sku"] == sku), None)
        launch_date = g.date_between(start_days_ago=365, end_days_ago=30)
        initial_alloc = g.rng.randint(100, 2000)
        week1 = int(initial_alloc * g.rng.uniform(0.3, 0.8))
        month1 = int(initial_alloc * g.rng.uniform(1.2, 2.5))

        launches.append({
            "launch_id": f"LNC-{900001 + i:06d}",
            "sku": sku,
            "style_id": product["style_id"] if product else "STY-0000",
            "category": product["category"] if product else "General",
            "launch_date": launch_date,
            "initial_allocation_units": initial_alloc,
            "units_sold_week1": week1,
            "units_sold_month1": month1,
            "forecast_vs_actual_pct": round(g.rng.uniform(85, 115), 1),
            "sell_through_rate_pct": round((month1 / initial_alloc) * 100, 1),
            "peak_week_demand_units": int(month1 * g.rng.uniform(0.2, 0.4)),
            "status": g.pick(["launched", "evergreen", "discontinued"])
        })

    # Generate inventory_balance_reconciliation
    inventory_recon = []
    for site in g.pick([s for s in sites if s["type"] == "dc"], k=5):
        for sku in g.pick(skus, k=30):
            for week in g.weeks(-4):
                wms = g.rng.randint(0, 2000)
                erp = wms + g.rng.randint(-100, 100)  # Usually close
                finance = erp + g.rng.randint(-50, 50)
                phys = wms + g.rng.randint(-20, 20)

                variance_category = "timing" if abs(wms - erp) < 50 else "definitional" if abs(erp - finance) < 100 else "error"

                inventory_recon.append({
                    "date": week,
                    "site_id": site["site_id"],
                    "sku": sku,
                    "wms_units": wms,
                    "erp_units": erp,
                    "finance_units": finance,
                    "physical_count_units": phys,
                    "wms_erp_variance": wms - erp,
                    "erp_finance_variance": erp - finance,
                    "category": variance_category,
                    "variance_explanation": f"{variance_category.capitalize()} difference" if variance_category != "timing" else "Cut-off timing",
                    "adjustment_required": abs(wms - erp) > 50 or abs(erp - finance) > 100
                })

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

    # Generate warehouse_data_catalogue
    catalogue = []
    tables = [
        ("product_sales_fact", "fact", "Daily product sales by market and size", 500000, "One row per date/sku/site/size", "[date, sku, site_id, size]", "daily"),
        ("product_kpi_history", "fact", "Historical KPI measurements", 5000, "One row per date/kpi_name", "[date, kpi_name]", "daily"),
        ("otif_metrics", "fact", "OTIF metrics by dimensions", 50000, "One row per week/supplier/category/dc/mode", "[week, supplier_id, category, site_id, inbound_mode]", "weekly"),
        ("product_markdown_rate", "fact", "Markdown rates by product and period", 10000, "One row per sku/period", "[sku, period_type, period]", "monthly"),
        ("product_launch_history", "fact", "New product launches", 500, "One row per launch", "launch_id", "as_launched"),
        ("inventory_balance_reconciliation", "fact", "Inventory reconciliation", 100000, "One row per date/site/sku", "[date, site_id, sku]", "daily"),
        ("product_performance_metrics", "fact", "Product performance summary", 10000, "One row per sku/period", "[sku, period]", "monthly"),
        ("warehouse_data_catalogue", "dimension", "Index of warehouse tables", 20, "One row per table", "table_name", "manual"),
        ("warehouse_column_index", "dimension", "Index of warehouse columns", 100, "One row per column", "[table_name, column_name]", "manual"),
        ("saved_warehouse_views", "dimension", "Saved warehouse views", 50, "One row per view", "view_id", "manual")
    ]

    for tbl_name, tbl_type, desc, row_count, grain, key, freq in tables:
        catalogue.append({
            "table_name": tbl_name,
            "table_type": tbl_type,
            "description": desc,
            "row_count": row_count,
            "grain": grain,
            "primary_key": key,
            "last_updated": g.as_of,
            "refresh_frequency": freq
        })

    # Generate warehouse_column_index
    col_index = []
    table_cols = {
        "product_sales_fact": [
            ("date", "date", "Sales transaction date", "sales"),
            ("sku", "str", "Product SKU", "products"),
            ("style_id", "str", "Style identifier", "products"),
            ("category", "str", "Product category", "products"),
            ("market", "str", "Geographic market", "sales"),
            ("site_id", "str", "Store or channel", "sites"),
            ("units_sold", "int", "Units sold", "sales"),
            ("sales_gbp", "float", "Sales revenue", "sales"),
            ("cost_gbp", "float", "Product cost", "finance")
        ],
        "product_kpi_history": [
            ("date", "date", "KPI measurement date", "analytics"),
            ("kpi_name", "str", "KPI identifier", "analytics"),
            ("kpi_value", "float", "KPI value", "analytics"),
            ("target_value", "float", "Target benchmark", "analytics")
        ],
        "otif_metrics": [
            ("week", "date", "Week start date", "supply_chain"),
            ("supplier_id", "str", "Supplier identifier", "suppliers"),
            ("category", "str", "Product category", "products"),
            ("site_id", "str", "Receiving DC", "sites"),
            ("otif_pct", "float", "On-time-in-full %", "supply_chain")
        ]
    }

    for table, cols in table_cols.items():
        for col_name, col_type, desc, source in cols:
            col_index.append({
                "table_name": table,
                "column_name": col_name,
                "column_type": col_type,
                "description": desc,
                "source_system": source
            })

    # Generate saved_warehouse_views (initially empty - will be created via tool)
    views = []

    return {
        "product_sales_fact": sales_fact,
        "product_kpi_history": kpi_history,
        "otif_metrics": otif_metrics,
        "product_markdown_rate": markdown_rate,
        "product_launch_history": launches,
        "inventory_balance_reconciliation": inventory_recon,
        "product_performance_metrics": perf_metrics,
        "warehouse_data_catalogue": catalogue,
        "warehouse_column_index": col_index,
        "saved_warehouse_views": views
    }
