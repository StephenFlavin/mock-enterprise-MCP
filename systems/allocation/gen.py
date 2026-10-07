"""Allocation data: store allocations, regional summaries, rebalance analysis, and replenishment impact."""
from datetime import timedelta

# Slow movers (network demand <= 20 units a week) that carry the forecast-level comparison story in seed/.
SLOW_MOVERS = ["SKU-102898", "SKU-106034", "SKU-102289", "SKU-104130", "SKU-104053", "SKU-105936", "SKU-105985",
               "SKU-101414", "SKU-100049", "SKU-105054", "SKU-106083", "SKU-100882", "SKU-106139"]


def generate(g):
    r = g.rng
    allocations = []
    regional_summaries = []
    rebalance_analyses = []
    forecast_impacts = []

    stores = [s for s in g.master("sites") if s["type"] == "store"]
    # Story SKUs are planted from seed/*.csv; keep generated noise away from them (style 5520, the seasonal throw SKU-104963, Smart Home
    # lines used in the port-closure plan, and the slow movers used in the forecast-level comparison).
    story_skus = {p["sku"] for p in g.master("products")
                  if p["style_id"] == "STY-5520" or p["sku"] in ("K-1700", "SKU-104963") or p["category"] == "Smart Home"}
    story_skus |= set(SLOW_MOVERS)
    products = [p for p in g.master("products")[:140] if p["sku"] not in story_skus][:100]
    regions = sorted(set(s["region"] for s in stores if s["region"]))
    dcs = [s for s in g.master("sites") if s["type"] == "dc"]

    # Generate store allocations: one or more allocation decisions per store-product combo in past 90 days
    for product in products[:50]:  # Allocate for first 50 products
        sku = product["sku"]
        for store in r.sample(stores, min(15, len(stores))):  # Sample 15 stores per product
            store_id = store["site_id"]
            region = store["region"]
            # 2-4 allocations per store-product in last 90 days
            num_allocs = r.choice([1, 2, 2, 3])
            for i in range(num_allocs):
                days_ago = r.randint(10, 85)
                alloc_date = g.as_of - timedelta(days=days_ago)
                qty = r.choice([50, 100, 150, 200, 250, 300, 500])
                status = r.choices(["received", "partial", "in_transit", "allocated"], [0.6, 0.2, 0.1, 0.1])[0]
                qty_received = int(qty * r.uniform(0, 1)) if status in ["received", "partial"] else 0
                allocation_id = f"ALO-{len(allocations) + 1:06d}"
                allocations.append({
                    "allocation_id": allocation_id,
                    "sku": sku,
                    "store_id": store_id,
                    "qty_allocated": qty,
                    "qty_received": qty_received,
                    "allocation_date": alloc_date,
                    "source_dc": r.choice(dcs)["site_id"],
                    "reason": r.choice(["stock-out prevention", "rebalance", "replenishment", "seasonal demand", "promotion"]),
                    "status": status,
                    "updated_at": alloc_date + timedelta(days=r.randint(0, 20))
                })

    # Generate regional stock summaries: one per region-product per day in last 14 days
    for product in products[:40]:
        sku = product["sku"]
        for region in regions:
            summary_date = g.as_of - timedelta(days=r.randint(0, 6))
            region_stores = [s for s in stores if s["region"] == region]
            weekly_sales = r.randint(50, 500)
            on_hand = r.randint(100, 2000)
            allocated = r.randint(0, on_hand // 3)
            available = on_hand - allocated
            days_cover = available / max(1, weekly_sales / 7)
            regional_summaries.append({
                "sku": sku,
                "region": region,
                "summary_date": summary_date,
                "store_count": len(region_stores),
                "total_on_hand": on_hand,
                "total_allocated": allocated,
                "available_units": available,
                "days_of_cover": round(days_cover, 1),
                "weekly_sales_units": weekly_sales,
                "out_of_stock_count": r.randint(0, min(3, len(region_stores)))
            })

    # Generate rebalance analyses: one or more per product, including port closure scenarios
    scenarios = ["standard", "port_closure_2w", "port_closure_4w"]
    for product in products[:30]:
        sku = product["sku"]
        region_list = [x for x in regions if x != "US"]
        for scenario in scenarios:
            # 1-2 analyses per product-scenario in last 7 days
            for _ in range(r.choice([1, 1, 2])):
                analysis_date = g.as_of - timedelta(days=r.randint(0, 6))
                r1, r2 = r.sample(region_list, 2)
                units = r.randint(500, 5000)
                transfer_cost = r.randint(100, 2000)
                sales_impact = r.randint(1000, 10000)
                net_benefit = sales_impact - transfer_cost
                analysis_id = f"RBA-{len(rebalance_analyses) + 1:06d}"
                rebalance_analyses.append({
                    "analysis_id": analysis_id,
                    "sku": sku,
                    "analysis_date": analysis_date,
                    "scenario_name": scenario,
                    "region_from": r1,
                    "region_to": r2,
                    "units_to_transfer": units,
                    "transfer_cost_gbp": transfer_cost,
                    "potential_sales_impact_gbp": sales_impact,
                    "net_benefit_gbp": net_benefit,
                    "benefit_pct": round((sales_impact / transfer_cost - 1) * 100, 1) if transfer_cost > 0 else 0,
                    "status": r.choices(["proposed", "approved", "executed", "declined"], [0.3, 0.3, 0.3, 0.1])[0],
                    "created_at": analysis_date + timedelta(days=r.randint(0, 3))
                })

    # Generate forecast level impact: one per product-forecast_level
    forecast_levels = ["store_sku", "cluster", "category"]
    for product in products[:35]:
        sku = product["sku"]
        analysis_date = g.as_of - timedelta(days=r.randint(0, 20))
        for i, level in enumerate(forecast_levels):
            # Store-SKU most accurate, Category least accurate
            if level == "store_sku":
                mape = r.uniform(8, 15)  # 8-15% error
                safety = r.randint(100, 300)
                dead = r.randint(20, 100)
                freq = r.randint(1, 7)
            elif level == "cluster":
                mape = r.uniform(12, 20)
                safety = r.randint(300, 600)
                dead = r.randint(50, 150)
                freq = r.randint(3, 14)
            else:  # category
                mape = r.uniform(18, 28)
                safety = r.randint(500, 1000)
                dead = r.randint(100, 300)
                freq = r.randint(7, 21)

            stockouts = r.randint(0, int(mape))
            lost_sales = stockouts * r.randint(100, 500)
            carrying_cost = safety * 0.15  # 15% carrying cost
            impact_id = f"IMP-{len(forecast_impacts) + 1:06d}"
            forecast_impacts.append({
                "impact_id": impact_id,
                "sku": sku,
                "item_type": "fast_mover",
                "forecast_level": level,
                "analysis_date": analysis_date,
                "mape_pct": round(mape, 1),
                "replenishment_frequency_days": freq,
                "total_safety_stock": safety,
                "total_dead_stock": dead,
                "stockout_incidents": stockouts,
                "lost_sales_gbp": lost_sales,
                "carrying_cost_gbp": round(carrying_cost, 2),
                "total_cost_gbp": round(lost_sales + carrying_cost, 2)
            })

    return {
        "store_allocations": allocations,
        "regional_stock_summary": regional_summaries,
        "rebalance_analysis": rebalance_analyses,
        "forecast_level_impact": forecast_impacts
    }
