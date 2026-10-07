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

    # Generate product_sales_fact
    sales_fact = []
    for week in g.weeks(-26):  # 26 weeks back
        for _ in range(g.rng.randint(20, 40)):  # 20-40 sales records per week
            sku = g.pick(skus)
            product = next((p for p in products if p["sku"] == sku), None)
            market = g.pick(markets)
            store = next((s for s in sites if s["region"].startswith(market[:2].upper())), g.pick([s for s in sites if s["type"] == "store"]))

            units = g.rng.randint(1, 20)
            price = float(product["retail_price_gbp"]) if product else 50.0
            cost = float(product["unit_cost_gbp"]) if product else 20.0

            markdown_pct = g.rng.uniform(0, 0.4)  # 0-40% markdown
            markdown = units * price * markdown_pct
            sales = units * price * (1 - markdown_pct)

            size_options = ["XS", "S", "M", "L", "XL", "6", "8", "10", "12", "14", "16"]
            size = g.pick(size_options)

            sales_fact.append({
                "date": week,
                "sku": sku,
                "style_id": product["style_id"] if product else "STY-0000",
                "category": product["category"] if product else "General",
                "market": market,
                "site_id": store["site_id"],
                "size": size,
                "units_sold": units,
                "sales_gbp": round(sales, 2),
                "cost_gbp": round(units * cost, 2),
                "markdown_gbp": round(markdown, 2),
                "customer_segment": g.pick(["Premium", "Standard", "Budget", "VIP"])
            })

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

    # Generate product_markdown_rate
    markdown_rate = []
    for sku in g.pick(skus, k=100):
        product = next((p for p in products if p["sku"] == sku), None)
        for period_num in range(-12, 0):
            period_str = f"2026-{((10 + period_num) % 12) + 1:02d}"
            units = g.rng.randint(10, 500)
            markdown_pct = g.rng.uniform(0.1, 0.5)

            markdown_rate.append({
                "sku": sku,
                "style_id": product["style_id"] if product else "STY-0000",
                "category": product["category"] if product else "General",
                "period_type": "monthly",
                "period": period_str,
                "units_sold": units,
                "full_price_units": int(units * (1 - markdown_pct)),
                "markdown_units": int(units * markdown_pct),
                "markdown_rate_pct": round(markdown_pct * 100, 1),
                "avg_markdown_depth_pct": round(g.rng.uniform(10, 40), 1),
                "lead_time_days": int(product["lead_time_days"]) if product else g.rng.randint(30, 120),
                "cumulative_markdown_gbp": round(units * g.rng.uniform(5, 30), 2)
            })

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

    # Generate product_performance_metrics
    perf_metrics = []
    for sku in g.pick(skus, k=120):
        product = next((p for p in products if p["sku"] == sku), None)
        units = g.rng.randint(50, 5000)
        sales = units * float(product["retail_price_gbp"]) * g.rng.uniform(0.6, 1.0) if product else units * g.rng.uniform(20, 100)
        cost = units * float(product["unit_cost_gbp"]) if product else units * g.rng.uniform(10, 50)
        margin = sales - cost
        markdown_pct = g.rng.uniform(0.1, 0.5)

        velocity_rank = g.rng.randint(1, 5000)
        strategic_role = g.pick(["core", "growth", "strategic", "clearance"])
        action_map = {
            "core": "extend",
            "growth": "refresh",
            "strategic": "extend",
            "clearance": "delete"
        }

        perf_metrics.append({
            "sku": sku,
            "style_id": product["style_id"] if product else "STY-0000",
            "category": product["category"] if product else "General",
            "period": "2026-Q3",
            "units_sold": units,
            "sales_gbp": round(sales, 2),
            "margin_gbp": round(margin, 2),
            "margin_pct": round(100 * margin / sales, 1) if sales > 0 else 0,
            "markdown_rate_pct": round(markdown_pct * 100, 1),
            "in_stock_rate_pct": round(g.rng.uniform(70, 99), 1),
            "velocity_rank": velocity_rank,
            "strategic_role": strategic_role,
            "recommend_action": action_map[strategic_role],
            "return_rate_pct": round(g.rng.uniform(0.5, 5), 1)
        })

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
