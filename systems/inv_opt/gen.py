"""Inventory optimisation data: SKU policies, demand analysis, and service level targets."""
from datetime import datetime, timedelta


def generate(g):
    """Generate inventory optimisation data for SKUs."""
    r = g.rng

    # Get products from master to base policies on
    products = g.master("products")
    suppliers = g.master("suppliers")

    # Filter to active products with reasonable lead times
    active_products = [p for p in products if p["status"] == "active" and p.get("lead_time_days")]

    # Sort by revenue proxy (volume * price)
    sorted_products = sorted(
        active_products,
        key=lambda p: float(p.get("unit_cost_gbp", 10)) * 100 if p.get("unit_cost_gbp") else 1000,
        reverse=True
    )

    # Generate for top 300 SKUs (covers fast sellers, high value, and long tail)
    policies = []
    demand_stats = []
    supplier_lt = []

    for idx, product in enumerate(sorted_products[:300]):
        sku = product["sku"]
        category = product.get("category", "Unclassified")
        lead_time = int(product.get("lead_time_days", 30))

        # ABC classification: top 10% = A, next 20% = B, rest = C
        if idx < 30:
            abc_class = "A"
        elif idx < 90:
            abc_class = "B"
        else:
            abc_class = "C"

        # Generate demand pattern
        base_weekly_demand = r.randint(50, 5000) if abc_class == "A" else r.randint(20, 500)
        demand_mean = base_weekly_demand

        # Vary demand variability by category
        if "clearance" in category.lower() or "seasonal" in category.lower():
            cv = r.uniform(0.6, 0.95)  # High variability
        elif abc_class == "A":
            cv = r.uniform(0.15, 0.35)  # Low variability for fast sellers
        elif abc_class == "B":
            cv = r.uniform(0.30, 0.55)
        else:
            cv = r.uniform(0.50, 0.90)  # High variability for slow movers

        demand_stdev = demand_mean * cv
        annual_volume = demand_mean * 52

        # Calculate safety stock using formula: z * stdev * sqrt(LT)
        z_95 = 1.645
        z_97 = 1.96
        z_99 = 2.326

        safety_stock_95 = int(z_95 * demand_stdev * ((lead_time / 7.0) ** 0.5))
        safety_stock_97 = int(z_97 * demand_stdev * ((lead_time / 7.0) ** 0.5))
        reorder_point = int(lead_time * demand_mean / 7.0)

        # Service level target: higher for A items
        if abc_class == "A":
            sl_target = r.choice([95, 97, 99])
        elif abc_class == "B":
            sl_target = r.choice([92, 95, 97])
        else:
            sl_target = r.choice([85, 90, 92])

        # Use appropriate safety stock
        if sl_target >= 97:
            safety_stock = safety_stock_97
        elif sl_target >= 95:
            safety_stock = safety_stock_95
        else:
            safety_stock = int(safety_stock_95 * 0.7)

        # Create policy entry (some will be intentionally wrong for testing)
        # About 15% have "wrong" safety stock that's too high or too low
        if r.random() < 0.15:
            if r.random() < 0.5:
                safety_stock = int(safety_stock * r.uniform(0.5, 0.8))  # Too low
            else:
                safety_stock = int(safety_stock * r.uniform(1.3, 1.6))  # Too high

        policy = {
            "sku": sku,
            "reorder_point_units": reorder_point,
            "safety_stock_units": max(1, safety_stock),
            "service_level_target_pct": sl_target,
            "lead_time_days": lead_time,
            "annual_volume_units": int(annual_volume),
            "cv_demand": round(cv, 3),
            "category": category,
            "abc_class": abc_class,
            "last_review_date": g.days_ago(r.randint(30, 180)),
            "updated_at": g.as_of - timedelta(days=r.randint(1, 90)),
        }
        policies.append(policy)

        # Demand analysis
        seasonality = r.uniform(0.9, 1.2) if abc_class == "A" else r.uniform(0.8, 1.3)
        trend = r.choice(["up", "down", "stable"])
        high_var = cv > 0.5

        demand_analysis = {
            "sku": sku,
            "demand_52w_mean": round(demand_mean, 1),
            "demand_52w_stdev": round(demand_stdev, 1),
            "demand_cv": round(cv, 3),
            "seasonality_factor": round(seasonality, 2),
            "trend_direction": trend,
            "high_variability": high_var,
            "last_calculated_date": g.days_ago(r.randint(7, 60)),
        }
        demand_stats.append(demand_analysis)

        # Supplier lead times
        if product.get("supplier_id"):
            supplier = product["supplier_id"]
            baseline_lt = lead_time
            actual_lt = baseline_lt + r.randint(-7, 14)
            lt_stdev = max(1, int(baseline_lt * r.uniform(0.05, 0.2)))
            change_pct = round((actual_lt - baseline_lt) / baseline_lt * 100, 1) if baseline_lt > 0 else 0

            lt_entry = {
                "sku": sku,
                "supplier_id": supplier,
                "lead_time_days": actual_lt,
                "lead_time_stdev_days": round(lt_stdev, 1),
                "change_from_baseline_pct": change_pct,
                "sample_size": r.randint(5, 20),
                "measurement_date": g.days_ago(r.randint(1, 30)),
            }
            supplier_lt.append(lt_entry)

    # Create segments
    segments = [
        {
            "segment_id": "SEG-001",
            "segment_name": "A Items (Top 10%)",
            "sku_count": 30,
            "target_service_level_pct": 97,
            "status": "active",
            "updated_at": g.as_of,
        },
        {
            "segment_id": "SEG-002",
            "segment_name": "B Items (20%)",
            "sku_count": 60,
            "target_service_level_pct": 95,
            "status": "active",
            "updated_at": g.as_of,
        },
        {
            "segment_id": "SEG-003",
            "segment_name": "C Items (Long Tail)",
            "sku_count": 210,
            "target_service_level_pct": 90,
            "status": "active",
            "updated_at": g.as_of,
        },
    ]

    return {
        "sku_inventory_policies": policies,
        "sku_demand_analysis": demand_stats,
        "segment_service_levels": segments,
        "supplier_lead_time_actuals": supplier_lt,
    }
