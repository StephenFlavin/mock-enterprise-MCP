"""Costing system data generator: product costings, margins, cost drivers and recovery routes."""
from datetime import datetime, timedelta


def generate(g):
    """Generate costing data referencing master products and suppliers."""
    r = g.rng

    # Get relevant master data
    products = g.master("products")
    suppliers = g.master("suppliers")
    factories = g.master("factories")

    # Filter to products with suppliers and factories
    products_with_suppliers = [p for p in products if p.get("supplier_id") and p.get("factory_id")][:100]

    if not products_with_suppliers:
        products_with_suppliers = products[:50]

    # Initialize result tables
    product_costings = []
    material_costs = []
    margin_analyses = []
    cost_variance_drivers = []
    recovery_routes = []
    recovery_rates = []
    scenario_analyses = []
    cost_sheet_details = []
    commodity_exposures = []
    supplier_cost_history = []

    # 1. Generate product costings (one per unique style, not per product SKU)
    costing_id = 1
    seen_styles = set()
    for product in products_with_suppliers[:80]:
        if product.get("style_id") in seen_styles:
            continue
        seen_styles.add(product.get("style_id"))
        style_id = product.get("style_id", f"STY-{product.get('sku', '').replace('SKU-', '')}")
        sku = product.get("sku")

        # Base volume for costing
        base_volume = r.randint(3000, 15000)

        # Generate base costing
        material_cost = r.uniform(3, 20)
        labour_cost = r.uniform(1, 8)
        overhead_cost = r.uniform(0.5, 3)
        freight_cost = r.uniform(0.5, 4)
        tooling_cost = r.uniform(0.1, 2)

        total_cost = material_cost + labour_cost + overhead_cost + freight_cost + tooling_cost
        retail_price = total_cost / (1 - r.uniform(0.45, 0.65))  # 45-65% margin
        gross_margin = retail_price - total_cost

        cid = f"CST-{costing_id:06d}"
        product_costings.append({
            "costing_id": cid,
            "style_id": style_id,
            "sku": sku,
            "season": "AW26",
            "version": 1,
            "origin_country": product.get("country_of_origin", "VN"),
            "supplier_id": product.get("supplier_id", "SUP-0001"),
            "factory_id": product.get("factory_id", "FAC-0001"),
            "quantity_units": base_volume,
            "material_cost_gbp": round(material_cost, 2),
            "labour_cost_gbp": round(labour_cost, 2),
            "overhead_cost_gbp": round(overhead_cost, 2),
            "freight_cost_gbp": round(freight_cost, 2),
            "tooling_cost_gbp": round(tooling_cost, 2),
            "total_cost_gbp": round(total_cost, 2),
            "retail_price_gbp": round(retail_price, 2),
            "gross_margin_gbp": round(gross_margin, 2),
            "gross_margin_pct": round(gross_margin / retail_price * 100, 1),
            "target_margin_pct": r.uniform(45, 65),
            "status": "active",
            "notes": f"FY27 costing at {base_volume} units",
            "created_at": g.as_of - timedelta(days=r.randint(30, 90)),
            "updated_at": g.as_of - timedelta(days=r.randint(0, 30)),
        })
        costing_id += 1

    # 2. Generate material costs (historical)
    materials = [
        ("MAT-COTTON-10OZ", "10oz cotton fabric", "fabric", "meter"),
        ("MAT-POLYESTER-100", "100% polyester", "fabric", "meter"),
        ("MAT-WOOL-MERINO", "Merino wool", "fabric", "meter"),
        ("MAT-NYLON-SPANDEX", "Nylon spandex blend", "fabric", "meter"),
        ("MAT-PACKAGING-BOX", "Corrugated box", "packaging", "unit"),
        ("MAT-PACKAGING-PULP", "Moulded pulp", "packaging", "unit"),
        ("MAT-DYES-CHEM", "Dyes and chemicals", "dyes_chemicals", "kg"),
    ]

    material_id_ctr = 1
    for mat_name, mat_desc, mat_type, unit in materials:
        # Generate 12 weeks of price history
        base_price = r.uniform(2, 15)
        for week in range(12):
            recorded_date = g.days_ago(week * 7)
            # Add realistic price volatility
            price_noise = r.gauss(0, 1)
            cost = max(base_price * (1 + price_noise * 0.1), base_price * 0.7)

            material_costs.append({
                "material_id": mat_name,
                "material_name": mat_desc,
                "material_type": mat_type,
                "supplier_id": r.choice([s["supplier_id"] for s in suppliers[:10]]),
                "unit": unit,
                "cost_per_unit_gbp": round(cost, 3),
                "index_price_gbp": round(cost * r.uniform(0.95, 1.05), 3),
                "currency_conversion": 1.0 if unit != "meter" else r.uniform(0.98, 1.02),
                "recorded_at": recorded_date,
                "notes": None,
            })

    # 3. Generate margin analyses (by SKU, category, channel, period)
    margin_id_ctr = 1
    categories = set(p.get("category", "Other") for p in products_with_suppliers)
    channels = ["store", "online", "outlet"]

    for category in list(categories)[:15]:
        category_products = [p for p in products_with_suppliers if p.get("category") == category][:5]

        for week in range(8):  # Last 8 weeks
            period = g.days_ago(week * 7).strftime("%Y-W%V")

            for channel in channels:
                volume = r.randint(100, 2000)
                avg_price = r.uniform(20, 80)
                cogs_pct = r.uniform(0.35, 0.55)  # 35-55% of retail
                cogs = avg_price * cogs_pct
                gross_margin = avg_price - cogs

                markdown_pct = r.uniform(5, 25)
                markdown = avg_price * (markdown_pct / 100)
                net_margin = gross_margin - markdown

                margin_analyses.append({
                    "margin_id": f"MAR-{margin_id_ctr:06d}",
                    "style_id": category_products[0].get("style_id") if category_products else "STY-0001",
                    "sku": category_products[0].get("sku") if category_products else "SKU-000001",
                    "category": category,
                    "period": period,
                    "channel": channel,
                    "volume_units": volume,
                    "revenue_gbp": round(avg_price * volume, 2),
                    "cost_of_goods_gbp": round(cogs * volume, 2),
                    "gross_margin_gbp": round(gross_margin * volume, 2),
                    "gross_margin_pct": round(gross_margin / avg_price * 100, 1),
                    "markdown_gbp": round(markdown * volume, 2),
                    "net_margin_gbp": round(net_margin * volume, 2),
                    "net_margin_pct": round(net_margin / avg_price * 100, 1),
                    "plan_margin_pct": r.uniform(45, 60),
                    "variance_pct": round(r.gauss(0, 3), 1),
                    "analysed_at": g.as_of - timedelta(days=7 * week),
                })
                margin_id_ctr += 1

    # 4. Generate cost variance drivers
    variance_id_ctr = 1
    category_products_map = {}
    for category in categories:
        category_products_map[category] = [p for p in products_with_suppliers if p.get("category") == category]

    for category in list(categories)[:10]:
        category_products = category_products_map.get(category, products_with_suppliers[:5])
        for week in range(6):
            period = g.days_ago(week * 7).strftime("%Y-%m")

            cost_var = r.gauss(0, 2)
            fx_var = r.gauss(0, 1.5)
            mix_var = r.gauss(0, 1)
            supplier_var = r.gauss(0, 1.5)
            markdown_var = r.gauss(0, 1)

            total_var = cost_var + fx_var + mix_var + supplier_var + markdown_var

            # Use real style_id from category products
            style_id = category_products[0].get("style_id") if category_products else "STY-4012"

            cost_variance_drivers.append({
                "variance_id": f"VAR-{variance_id_ctr:06d}",
                "style_id": style_id,
                "category": category,
                "period": period,
                "total_variance_pct": round(total_var, 2),
                "cost_driver_pct": round(cost_var, 2),
                "fx_driver_pct": round(fx_var, 2),
                "mix_driver_pct": round(mix_var, 2),
                "supplier_driver_pct": round(supplier_var, 2),
                "markdown_driver_pct": round(markdown_var, 2),
                "other_driver_pct": round(r.gauss(0, 0.5), 2),
                "notes": f"Analysis for {category} in {period}",
                "analysed_at": g.as_of - timedelta(days=r.randint(1, 30)),
            })
            variance_id_ctr += 1

    # 5. Generate recovery routes
    recovery_routes_data = [
        ("ROU-RESTOCK", "Restocking", "Return to saleable stock with full retail", "Electronics", 0, 30),
        ("ROU-OUTLET", "Outlet", "Sell through outlet channels at discount", "Apparel", 31, 90),
        ("ROU-LIQUIDATION", "Liquidation", "Sell to liquidator at bulk discount", "General", 91, 180),
        ("ROU-REFURBISH", "Refurbishing", "Refurbish and resell", "Electronics", 0, 60),
        ("ROU-RECYCLING", "Recycling", "Recycle materials", "General", 180, 3650),
    ]

    for route_id, route_name, desc, category, min_age, max_age in recovery_routes_data:
        recovery_routes.append({
            "route_id": route_id,
            "route_name": route_name,
            "description": desc,
            "category_focus": category,
            "min_age_days": min_age,
            "max_age_days": max_age,
            "status": "active" if route_id != "ROU-RECYCLING" else "active",
        })

    # 6. Generate recovery rates
    age_bands = ["0-30d", "31-60d", "61-180d", "180d+"]
    recovery_rate_id = 1

    for route_id, _, _, _, _, _ in recovery_routes_data:
        for category in ["Apparel", "Electronics", "Home"]:
            for age_band in age_bands:
                # Recovery rates decline with age and route type
                age_mult = 1.0 - (age_bands.index(age_band) * 0.2)
                base_rate = r.uniform(50, 95) if route_id in ["ROU-RESTOCK", "ROU-OUTLET"] else r.uniform(20, 60)
                recovery_pct = max(10, base_rate * age_mult)

                recovery_rates.append({
                    "route_id": route_id,
                    "category": category,
                    "age_band": age_band,
                    "recovery_rate_pct": round(recovery_pct, 1),
                    "handling_cost_gbp": round(r.uniform(0.5, 3), 2),
                    "time_to_realise_days": r.randint(7, 60),
                    "risk_rating": "low" if recovery_pct > 70 else "medium" if recovery_pct > 40 else "high",
                    "volume_last_6m": r.randint(100, 2000),
                    "last_updated": g.as_of - timedelta(days=r.randint(1, 60)),
                })

    # 7. Generate scenario analyses
    scenario_id_ctr = 1
    scenario_types = ["freight_mode", "volume", "material_cost", "supplier", "markdown", "lead_time"]
    employees = g.master("employees")
    employee_ids = [e["employee_id"] for e in employees[:20]] if employees else ["EMP-00001"]

    for costing in product_costings[:20]:
        for scenario_type in scenario_types[:3]:
            cost_impact = r.uniform(-2, 4)
            margin_impact = -cost_impact  # Inverse relationship

            scenarios = {
                "freight_mode": "Air vs Sea shipping",
                "volume": "Increase order volume for scale",
                "material_cost": "Material cost increase scenario",
                "supplier": "Switch to lower-cost supplier",
                "markdown": "Additional markdown pressure",
                "lead_time": "Shorten lead time from factory",
            }

            scenario_analyses.append({
                "scenario_id": f"SCN-{scenario_id_ctr:06d}",
                "scenario_name": scenarios.get(scenario_type, "Generic scenario"),
                "base_costing_id": costing["costing_id"],
                "scenario_type": scenario_type,
                "assumption_detail": f"Scenario: {scenario_type}",
                "cost_impact_gbp": round(cost_impact, 2),
                "margin_impact_gbp": round(margin_impact, 2),
                "margin_impact_pct": round(margin_impact / costing["retail_price_gbp"] * 100, 1),
                "volume_impact": r.randint(-500, 2000),
                "financial_impact_gbp": round(cost_impact * costing["quantity_units"], 2),
                "created_by": r.choice(employee_ids),
                "created_at": g.as_of - timedelta(days=r.randint(0, 30)),
            })
            scenario_id_ctr += 1

    # 8. Generate cost sheet details
    line_no_ctr = 1
    for costing in product_costings[:50]:
        components = [
            ("fabric", f"Main fabric", costing["material_cost_gbp"] * 0.7, 1.0, "m", 0.65),
            ("trimming", f"Trimmings/notions", costing["material_cost_gbp"] * 0.3, 0.3, "unit", 0.2),
            ("labour_cut", f"Cutting labour", costing["labour_cost_gbp"] * 0.35, 1.0, "unit", 0.25),
            ("labour_sew", f"Sewing labour", costing["labour_cost_gbp"] * 0.5, 1.0, "unit", 0.35),
            ("labour_finish", f"Finishing labour", costing["labour_cost_gbp"] * 0.15, 1.0, "unit", 0.1),
            ("packing", f"Packaging", costing["freight_cost_gbp"] * 0.3, 1.0, "unit", 0.2),
            ("inbound_freight", f"Inbound freight", costing["freight_cost_gbp"] * 0.7, 1.0, "per_unit", 0.4),
            ("overhead", f"Overhead allocation", costing["overhead_cost_gbp"], 1.0, "unit", 0.5),
        ]

        for comp_type, desc, cost, qty, unit, pct in components:
            cost_sheet_details.append({
                "costing_id": costing["costing_id"],
                "line_no": line_no_ctr,
                "component_type": comp_type,
                "description": desc,
                "quantity": qty,
                "unit": unit,
                "unit_cost_gbp": round(cost, 3),
                "total_cost_gbp": round(cost * qty, 2),
                "as_pct_of_total": round(pct * 100, 1),
            })
            line_no_ctr += 1

    # 9. Generate commodity exposures
    exposure_id_ctr = 1
    commodities = [
        ("cotton", 0.35, "kg"),
        ("polyester", 0.25, "kg"),
        ("nylon", 0.15, "kg"),
        ("steel", 0.2, "kg"),
    ]

    for commodity, exposure, unit in commodities:
        for product in products_with_suppliers[:40]:
            if r.random() > 0.6:  # 40% of products exposed to each commodity
                exposure_pct = exposure * r.uniform(0.8, 1.2)
                commodity_exposures.append({
                    "exposure_id": f"EXP-{exposure_id_ctr:06d}",
                    "sku": product.get("sku"),
                    "category": product.get("category", "General"),
                    "commodity": commodity,
                    "exposure_pct": round(exposure_pct, 2),
                    "exposure_unit": unit,
                    "exposure_quantity": round(r.uniform(0.1, 2), 2),
                    "elasticity": round(r.uniform(0.8, 1.2), 2),
                    "date_from": g.as_of - timedelta(days=180),
                })
                exposure_id_ctr += 1

    # 10. Generate supplier cost history (limit to avoid duplicates)
    period_start = g.as_of - timedelta(days=180)
    seen_histories = set()
    for i in range(8):  # Reduced from 12 to avoid excess data
        period_date = period_start + timedelta(days=i * 21)
        period_str = period_date.strftime("%Y-%m")

        for supplier in suppliers[:5]:  # Reduced from 10
            for product in products_with_suppliers[:20]:  # Reduced from 15
                key = (supplier["supplier_id"], product.get("sku"), period_str)
                if key in seen_histories:
                    continue
                seen_histories.add(key)

                market_idx = 100 + r.gauss(0, 5)
                supplier_idx = market_idx * r.uniform(0.95, 1.05)

                supplier_cost_history.append({
                    "supplier_id": supplier["supplier_id"],
                    "sku": product.get("sku"),
                    "period": period_str,
                    "quoted_cost_gbp": round(r.uniform(8, 25), 2),
                    "actual_cost_gbp": round(r.uniform(8, 25), 2),
                    "index_price_gbp": round(r.uniform(100, 120), 2),
                    "market_price_index": round(market_idx, 1),
                    "supplier_price_index": round(supplier_idx, 1),
                    "pass_through_pct": round(supplier_idx / market_idx * 100, 1),
                    "notes": None,
                })

    return {
        "product_costings": product_costings,
        "material_costs": material_costs,
        "margin_analyses": margin_analyses,
        "cost_variance_drivers": cost_variance_drivers,
        "recovery_routes": recovery_routes,
        "recovery_rates": recovery_rates,
        "scenario_analyses": scenario_analyses,
        "cost_sheet_details": cost_sheet_details,
        "commodity_exposures": commodity_exposures,
        "supplier_cost_history": supplier_cost_history,
    }
