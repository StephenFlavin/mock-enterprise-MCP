"""Merchandise Financial Planning data: planned buys, sell-through, OTB, forecasts and scenarios."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    categories = ["Knitwear", "Dresses", "Footwear", "Activewear", "Accessories", "Bedding", "Lighting"]
    regions = ["UK North", "UK South", "Ireland", "EU Central", "US"]

    # Get master data for realistic sourcing
    products = g.master("products")
    suppliers = g.master("suppliers")

    # Extract unique countries and categories from products
    countries_set = set(p.get("country_of_origin", "VN") for p in products if p.get("country_of_origin"))
    countries = list(countries_set)[:10]
    if not countries:
        countries = ["VN", "IN", "CN", "ID", "PK", "TH", "BD", "MM"]

    planned_buys = []
    sell_through = []
    otb_records = []
    markdown_shrink = []
    sales_forecasts = []
    otb_scenarios = []
    period_forecasts = []

    # Generate planned buys for seasons and periods
    for season in ["SS", "AW"]:
        for fy_period in range(1, 5):  # First 4 periods per season
            for cat in categories:
                for country in r.sample(countries, min(3, len(countries))):
                    planned_units = r.randint(1000, 15000)
                    unit_cost = r.uniform(5, 35)
                    retail_price = unit_cost * r.uniform(2.5, 4.0)

                    pb_id = f"PB-{len(planned_buys) + 1:06d}"
                    planned_buys.append({
                        "planned_buy_id": pb_id,
                        "category": cat,
                        "country_of_origin": country,
                        "fy_period": fy_period,
                        "season": season,
                        "planned_units": planned_units,
                        "planned_cost_gbp": round(planned_units * unit_cost, 2),
                        "retail_value_gbp": round(planned_units * retail_price, 2),
                        "status": r.choice(["approved", "confirmed", "received"]),
                        "created_at": g.days_ago(r.randint(30, 90)),
                        "updated_at": g.days_ago(r.randint(0, 30))
                    })

    # Generate sell-through data for recent periods
    for season in ["SS", "AW"]:
        for fy_period in range(1, 4):
            for cat in categories:
                for region in regions:
                    planned_units = r.randint(500, 8000)
                    # Sell-through varies: 70-95%
                    sell_through_pct = r.uniform(0.70, 0.95)
                    actual_units = int(planned_units * sell_through_pct)

                    retail_price = r.uniform(15, 80)

                    st_id = f"ST-{len(sell_through) + 1:06d}"
                    sell_through.append({
                        "sell_through_id": st_id,
                        "category": cat,
                        "sku": "",  # Optional field
                        "fy_period": fy_period,
                        "season": season,
                        "region": region,
                        "planned_units": planned_units,
                        "actual_units": actual_units,
                        "planned_retail_gbp": round(planned_units * retail_price, 2),
                        "actual_retail_gbp": round(actual_units * retail_price, 2),
                        "sell_through_pct": round(sell_through_pct * 100, 1),
                        "recorded_at": g.days_ago(r.randint(7, 60))
                    })

    # Generate OTB allocations
    for fy_period in range(1, 4):
        for season in ["SS", "AW"]:
            for cat in categories:
                total_budget = r.uniform(500000, 3000000)
                allocated_pct = r.uniform(0.75, 0.95)
                allocated = total_budget * allocated_pct
                reserve = total_budget - allocated

                otb_id = f"OTB-{len(otb_records) + 1:06d}"
                otb_records.append({
                    "otb_id": otb_id,
                    "category": cat,
                    "fy_period": fy_period,
                    "season": season,
                    "total_budget_gbp": round(total_budget, 2),
                    "allocated_gbp": round(allocated, 2),
                    "unallocated_gbp": round(reserve * 0.5, 2),
                    "chase_reserve_gbp": round(reserve * 0.5, 2),
                    "status": "active",
                    "last_updated_at": g.days_ago(r.randint(0, 30))
                })

    # Generate markdown/shrink rates
    for fy_period in range(1, 4):
        for season in ["SS", "AW"]:
            for cat in categories:
                markdown_pct = r.uniform(5, 25)
                shrink_pct = r.uniform(1, 8)

                mr_id = f"MR-{len(markdown_shrink) + 1:06d}"
                markdown_shrink.append({
                    "rate_id": mr_id,
                    "category": cat,
                    "fy_period": fy_period,
                    "season": season,
                    "markdown_pct": round(markdown_pct, 1),
                    "shrink_pct": round(shrink_pct, 1),
                    "markdown_gbp_per_unit": round(r.uniform(2, 15), 2),
                    "write_off_gbp_per_unit": round(r.uniform(0.5, 5), 2),
                    "basis": r.choice(["last year", "trend", "forecast"]),
                    "recorded_at": g.days_ago(r.randint(0, 20))
                })

    # Generate sales forecasts
    for region in regions:
        for fy_period in range(1, 4):
            for season in ["SS", "AW"]:
                for cat in categories:
                    base_units = r.randint(1000, 10000)
                    base_value = base_units * r.uniform(20, 60)

                    fc_id = f"FC-{len(sales_forecasts) + 1:06d}"
                    sales_forecasts.append({
                        "forecast_id": fc_id,
                        "region": region,
                        "category": cat,
                        "fy_period": fy_period,
                        "season": season,
                        "pessimistic_units": int(base_units * 0.85),
                        "pessimistic_gbp": round(base_value * 0.85, 2),
                        "base_forecast_units": base_units,
                        "base_forecast_gbp": round(base_value, 2),
                        "optimistic_units": int(base_units * 1.15),
                        "optimistic_gbp": round(base_value * 1.15, 2),
                        "forecast_date": g.days_ago(r.randint(1, 20))
                    })

    # Generate OTB scenarios (optimistic, cautious, base)
    for fy_period in range(1, 4):
        for cat in categories:
            base_budget = r.uniform(500000, 2500000)

            for scenario_idx, (scenario_type, alloc_mult) in enumerate([
                ("base", 1.0),
                ("optimistic", 1.2),
                ("cautious", 0.8)
            ]):
                allocated = base_budget * alloc_mult * 0.8
                reserve = base_budget * alloc_mult * 0.2

                sc_id = f"SC-{len(otb_scenarios) + 1:06d}"
                otb_scenarios.append({
                    "scenario_id": sc_id,
                    "scenario_name": f"{scenario_type.title()} case",
                    "category": cat,
                    "fy_period": fy_period,
                    "scenario_type": scenario_type,
                    "allocated_gbp": round(allocated, 2),
                    "chase_reserve_gbp": round(reserve, 2),
                    "expected_sell_through_pct": round(r.uniform(75, 92), 1),
                    "expected_margin_pct": round(r.uniform(35, 50), 1),
                    "created_at": g.days_ago(r.randint(5, 25))
                })

    # Generate period forecasts
    for region in regions:
        for fy_period in range(1, 4):
            pf_id = f"PF-{len(period_forecasts) + 1:06d}"
            base_forecast = r.randint(50000, 200000)
            variance = r.uniform(-10, 15)

            period_forecasts.append({
                "period_forecast_id": pf_id,
                "region": region,
                "fy_period": fy_period,
                "forecast_date": g.days_ago(r.randint(1, 15)),
                "forecast_units": base_forecast,
                "forecast_value_gbp": round(base_forecast * r.uniform(30, 80), 2),
                "forecast_vs_plan_pct": round(variance, 1),
                "status": "published",
                "recorded_at": g.days_ago(r.randint(0, 10))
            })

    return {
        "planned_buys": planned_buys,
        "sell_through_data": sell_through,
        "open_to_buy": otb_records,
        "markdown_shrink_rates": markdown_shrink,
        "sales_forecasts": sales_forecasts,
        "otb_scenarios": otb_scenarios,
        "period_forecasts": period_forecasts
    }
