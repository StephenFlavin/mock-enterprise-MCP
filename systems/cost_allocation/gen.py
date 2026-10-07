"""Cost allocation: warehouse cost pools, drivers, channel costs, SKU costs."""
from datetime import datetime


def generate(g):
    r = g.rng
    fake = g.fake
    as_of = g.as_of

    # Helper: get DC sites
    sites = [s for s in g.master("sites") if s["type"] == "dc"]
    site_ids = [s["site_id"] for s in sites]

    # Helper: get SKUs and channels
    skus = g.master("products")[:200]  # use first 200
    sku_ids = [s["sku"] for s in skus]

    # ============ COST POOLS ============
    cost_pools = []
    pool_idx = 1
    cost_types = ["labour", "space", "equipment", "overhead"]

    # Site-specific pools
    for site_id in site_ids:
        for cost_type in cost_types:
            pool_id = f"POOL-{cost_type[:3].upper()}-{site_id}"
            base_amount = {"labour": 150000, "space": 80000, "equipment": 120000, "overhead": 50000}
            pool_amount = base_amount[cost_type] + r.randint(-10000, 10000)

            driver_names = {
                "labour": "units_handled",
                "space": "pallet_spaces",
                "equipment": "units_handled",
                "overhead": "orders"
            }

            cost_pools.append({
                "pool_id": pool_id,
                "name": f"{site_id} {cost_type.title()}",
                "cost_type": cost_type,
                "site_id": site_id,
                "driver_name": driver_names[cost_type],
                "current_amount_gbp": pool_amount,
                "updated_at": as_of
            })

    # Network-wide pools
    for cost_type in ["transport", "packaging", "returns"]:
        pool_id = f"POOL-{cost_type[:3].upper()}-NET"
        base_amount = {"transport": 250000, "packaging": 120000, "returns": 80000}
        pool_amount = base_amount[cost_type] + r.randint(-15000, 15000)

        driver_names = {
            "transport": "weight",
            "packaging": "units",
            "returns": "items_per_order"
        }

        cost_pools.append({
            "pool_id": pool_id,
            "name": f"Network {cost_type.title()}",
            "cost_type": cost_type,
            "site_id": None,
            "driver_name": driver_names[cost_type],
            "current_amount_gbp": pool_amount,
            "updated_at": as_of
        })

    # ============ ALLOCATION DRIVERS ============
    drivers = []
    driver_bases = {
        "units_handled": ("units", 2.50),
        "pallet_spaces": ("pallet_spaces", 85.00),
        "orders": ("orders", 15.50),
        "weight": ("weight", 0.45),
        "items_per_order": ("items_per_order", 3.20)
    }

    for driver_name, (base, rate) in driver_bases.items():
        driver_id = f"DRV-{driver_bases[driver_name][0].upper()}-001"
        drivers.append({
            "driver_id": f"DRV-{len(drivers) + 1:06d}",
            "driver_name": driver_name,
            "pool_id": cost_pools[r.randint(0, len(cost_pools)-1)]["pool_id"],
            "allocation_base": base,
            "rate_gbp_per_unit": rate + r.uniform(-0.1, 0.1),
            "status": "active",
            "updated_at": as_of
        })

    # ============ SCENARIOS ============
    scenarios = []
    scenarios.append({
        "scenario_id": "SCEN-000001",
        "scenario_name": "FY26 Actuals",
        "base_scenario_id": None,
        "assumptions": "Current allocation drivers as of October 2026",
        "created_at": datetime.fromisoformat(str(g.days_ago(30))),
        "created_by": "EMP-01234"
    })

    # Alternative scenario: free returns removed
    scenarios.append({
        "scenario_id": "SCEN-000002",
        "scenario_name": "Free Returns Removed",
        "base_scenario_id": "SCEN-000001",
        "assumptions": "Returns allocation pool reduced 30% (free returns removed)",
        "created_at": datetime.fromisoformat(str(g.days_ago(7))),
        "created_by": "EMP-01234"
    })

    # ============ DC COST COMPONENTS ============
    components_dc = []
    for site_id in site_ids:
        total_units = r.randint(500000, 2000000)
        for component_type in cost_types:
            base_costs = {"labour": 150000, "space": 80000, "equipment": 120000, "overhead": 50000}
            cost = base_costs[component_type] + r.randint(-10000, 10000)

            components_dc.append({
                "site_id": site_id,
                "component_type": component_type,
                "units_handled": total_units,
                "total_cost_gbp": cost,
                "cost_per_unit_gbp": round(cost / total_units, 4),
                "as_of_date": as_of
            })

    # ============ CHANNEL COSTS ============
    channels_data = [
        ("store", 2000000, 500),
        ("online", 3500000, 1200),
        ("wholesale", 1200000, 300)
    ]

    channel_costs = []
    for channel, sales, base_orders in channels_data:
        for cost_type in ["warehousing", "outbound_transport", "returns", "packaging"]:
            cost_pcts = {
                "store": {"warehousing": 0.05, "outbound_transport": 0.02, "returns": 0.01, "packaging": 0.01},
                "online": {"warehousing": 0.08, "outbound_transport": 0.06, "returns": 0.03, "packaging": 0.02},
                "wholesale": {"warehousing": 0.03, "outbound_transport": 0.01, "returns": 0.005, "packaging": 0.005}
            }

            pct = cost_pcts[channel][cost_type]
            cost = sales * pct
            units = base_orders

            channel_costs.append({
                "channel": channel,
                "cost_type": cost_type,
                "cost_gbp": round(cost, 2),
                "units": units,
                "sales_gbp": sales,
                "cost_per_order_gbp": round(cost / units, 2),
                "cost_per_unit_gbp": round(cost / (units * 3), 2),  # assume 3 units per order
                "pct_of_sales": round(pct * 100, 2),
                "as_of_date": as_of
            })

    # ============ E-COMMERCE COSTS ============
    ecom_costs = []
    for days_back in [0, 7, 14, 21, 28]:
        period = g.days_ago(days_back)
        orders = r.randint(1000, 2000)
        labour = r.randint(5000, 8000)
        system = r.randint(2000, 3500)
        transport = r.randint(8000, 12000)
        returns = r.randint(1500, 3000)
        total = labour + system + transport + returns

        ecom_costs.append({
            "cost_period": period,
            "orders_count": orders,
            "total_cost_gbp": total,
            "labour_cost_gbp": labour,
            "system_cost_gbp": system,
            "transport_cost_gbp": transport,
            "returns_cost_gbp": returns,
            "cost_per_order_gbp": round(total / orders, 2)
        })

    # ============ SKU COSTS ============
    sku_costs = []
    for sku_rec in g.pick(skus, min(50, len(skus))):
        sku = sku_rec["sku"]
        annual_units = r.randint(1000, 100000)
        unit_price = float(sku_rec["retail_price_gbp"])
        annual_sales = annual_units * unit_price

        # Cost to serve: labour (0.4x), transport (0.3x), handling (0.2x)
        warehouse_cost = annual_units * r.uniform(0.3, 0.8)
        transport_cost = annual_units * r.uniform(0.2, 0.5)
        handling_cost = annual_units * r.uniform(0.1, 0.3)
        total_cost = warehouse_cost + transport_cost + handling_cost
        cost_per_unit = total_cost / annual_units
        margin_per_unit = unit_price - cost_per_unit

        sku_costs.append({
            "sku": sku,
            "annual_units_sold": annual_units,
            "annual_sales_gbp": round(annual_sales, 2),
            "warehousing_cost_gbp": round(warehouse_cost, 2),
            "transport_cost_gbp": round(transport_cost, 2),
            "handling_cost_gbp": round(handling_cost, 2),
            "total_cost_to_serve_gbp": round(total_cost, 2),
            "cost_per_unit_gbp": round(cost_per_unit, 2),
            "margin_per_unit_gbp": round(margin_per_unit, 2),
            "as_of_date": as_of
        })

    # ============ LOGISTICS BENCHMARKS ============
    logistics_benchmarks = [
        ("total_logistics_cost_pct_sales", 0.125, 0.110, 0.095, "2", 13.6),
        ("warehousing_cost_pct_sales", 0.055, 0.050, 0.042, "2", 10.0),
        ("transport_cost_pct_sales", 0.048, 0.042, 0.035, "3", 14.3),
        ("returns_cost_pct_sales", 0.018, 0.015, 0.010, "3", 20.0),
        ("packaging_cost_pct_sales", 0.008, 0.009, 0.006, "1", -11.1),
    ]

    benchmarks = []
    for metric, our, median, best, quartile, variance in logistics_benchmarks:
        benchmarks.append({
            "benchmark_id": f"BENCH-{len(benchmarks) + 1:06d}",
            "metric_name": metric,
            "our_value": our,
            "industry_median": median,
            "best_in_class": best,
            "our_quartile": quartile,
            "variance_pct": variance,
            "as_of_date": as_of
        })

    return {
        "cost_pools": cost_pools,
        "allocation_drivers": drivers,
        "scenarios": scenarios,
        "cost_components_dc": components_dc,
        "channel_costs": channel_costs,
        "ecom_costs": ecom_costs,
        "sku_costs": sku_costs,
        "logistics_benchmarks": benchmarks
    }
