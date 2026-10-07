"""Supply planning data: planning parameters, order proposals, supply plans, and gaps."""
from datetime import datetime, timedelta, date


def generate(g):
    r = g.rng

    # Get SKUs and suppliers from master
    products = g.master("products")
    suppliers = g.master("suppliers")
    sites = [s for s in g.master("sites") if s["type"] == "dc"]

    planning_params = []
    order_proposals = []
    supply_plans = []
    supply_demand_gaps = []
    supply_requests = []
    supplier_lead_times = []
    lead_time_origins = []
    fabric_requirements = []

    # Create planning parameters for each active SKU
    for i, sku_row in enumerate(products):
        if sku_row["status"] == "discontinued":
            continue
        sku = sku_row["sku"]
        param_id = f"SPP-{i + 1:06d}"

        # Vary parameters by product type
        sourcing = r.choice(["stocked", "stocked", "stocked", "make_to_order", "dual_source"])
        lead_time = r.randint(14, 45)

        planning_params.append({
            "planning_param_id": param_id,
            "sku": sku,
            "lead_time_days": lead_time,
            "pack_size": r.choice([100, 250, 500, 1000, 2500, 5000]),
            "lot_size": r.choice([250, 500, 1000, 2500, 5000, 10000]),
            "safety_stock_pct": r.uniform(5.0, 25.0),
            "sourcing_policy": sourcing,
            "reorder_point": r.randint(500, 5000),
            "updated_at": g.as_of - timedelta(days=r.randint(1, 90)),
        })

    # Create order proposals
    for i, sku_row in enumerate(products[:50]):  # Subset for proposals
        if sku_row["status"] == "discontinued":
            continue
        sku = sku_row["sku"]
        supplier_id = sku_row["supplier_id"]

        for j in range(r.randint(0, 3)):  # 0-3 proposals per SKU
            proposal_id = f"ORP-{len(order_proposals) + 1:06d}"
            order_week_offset = r.randint(-2, 8)
            order_date = g.as_of + timedelta(weeks=order_week_offset)
            delivery_offset = r.randint(3, 8)

            qty = r.choice([1000, 2500, 5000, 10000, 12000, 15000, 25000])
            issue = None
            if qty > 10000 and qty % 1000 > 100:
                issue = "pack_size_too_large"

            order_proposals.append({
                "proposal_id": proposal_id,
                "sku": sku,
                "supplier_id": supplier_id,
                "dest_site_id": r.choice([s["site_id"] for s in sites]),
                "quantity": qty,
                "demand_period_weeks": r.randint(1, 6),
                "planned_order_week": order_date.strftime("%Y-W%W"),
                "planned_delivery_week": (order_date + timedelta(weeks=delivery_offset)).strftime("%Y-W%W"),
                "status": r.choice(["draft", "draft", "draft", "approved", "converted"]),
                "conversion_reason": r.choice(["forecast_driven", "promotion", "replenishment", "safety_stock"]),
                "issue_detected": issue,
                "created_at": g.as_of - timedelta(days=r.randint(1, 30)),
                "cancelled_at": None,
                "cancel_reason": None,
            })

    # Create supply plans for recent weeks
    for sku_row in products[:80]:
        if sku_row["status"] == "discontinued":
            continue
        sku = sku_row["sku"]

        # Create plan for last 4 weeks and next 8 weeks
        for week_offset in range(-4, 9):
            plan_date = g.as_of + timedelta(weeks=week_offset)
            week_str = plan_date.strftime("%Y-W%W")

            forecast = r.randint(300, 2500)
            confirmed = int(forecast * r.uniform(0.6, 1.1))
            planned = max(0, int(forecast * r.uniform(0.0, 0.5)))
            gap = forecast - confirmed - planned
            stock_oh = r.randint(100, 5000)
            stock_proj = max(0, stock_oh + confirmed + planned - forecast)
            safety = int(forecast * 0.15)

            supply_plans.append({
                "sku": sku,
                "plan_week": week_str,
                "forecast_units": forecast,
                "confirmed_supply": confirmed,
                "planned_inbound": planned,
                "gap": gap,
                "stock_on_hand": stock_oh,
                "stock_projected": stock_proj,
                "safety_stock": safety,
                "last_updated": g.as_of - timedelta(days=r.randint(0, 7)),
            })

    # Create supply-demand gaps for some SKUs
    for i, sku_row in enumerate(products[10:30]):
        sku = sku_row["sku"]
        if r.random() > 0.6:  # 40% of SKUs have gaps
            continue

        gap_id = f"SDG-{len(supply_demand_gaps) + 1:06d}"
        gap_week_offset = r.randint(0, 6)
        gap_date = g.as_of + timedelta(weeks=gap_week_offset)
        gap_week = gap_date.strftime("%Y-W%W")

        forecast = r.randint(800, 3000)
        confirmed = r.randint(200, 600)
        gap_units = forecast - confirmed

        supply_demand_gaps.append({
            "gap_id": gap_id,
            "sku": sku,
            "gap_week": gap_week,
            "forecast_units": forecast,
            "confirmed_units": confirmed,
            "gap_units": gap_units,
            "category": sku_row["category"],
            "gap_reason": r.choice(["delayed_po", "forecast_spike", "promotion", "supplier_delay"]),
            "first_detected": g.as_of - timedelta(days=r.randint(1, 21)),
            "last_updated": g.as_of - timedelta(days=r.randint(0, 7)),
        })

    # Create supply requests
    for i, sku_row in enumerate(products[5:35]):
        sku = sku_row["sku"]
        if r.random() > 0.5:  # 50% have requests
            continue

        request_id = f"SRP-{len(supply_requests) + 1:06d}"
        req_date = g.as_of + timedelta(days=r.randint(7, 42))

        supply_requests.append({
            "request_id": request_id,
            "sku": sku,
            "site_id": r.choice([s["site_id"] for s in sites]),
            "quantity_requested": r.randint(1000, 10000),
            "requirement_date": req_date,
            "request_type": r.choice(["promotion", "replenishment", "safety_stock"]),
            "promotion_id": None,
            "status": r.choice(["draft", "submitted", "ordered"]),
            "submitted_at": g.as_of - timedelta(days=r.randint(1, 14)),
            "notes": None,
        })

    # Create supplier lead time actuals
    for supplier_row in suppliers[:25]:
        supplier_id = supplier_row["supplier_id"]
        for sku_row in products[0:15]:
            if sku_row["supplier_id"] != supplier_id:
                continue

            sku = sku_row["sku"]
            quoted = r.randint(14, 35)
            actual = quoted + r.randint(-5, 15)

            supplier_lead_times.append({
                "supplier_id": supplier_id,
                "sku": sku,
                "quoted_lead_days": quoted,
                "actual_avg_lead_days": float(actual),
                "sample_size": r.randint(8, 24),
                "gap_days": float(actual - quoted),
                "last_shipment_date": g.as_of - timedelta(days=r.randint(5, 60)),
            })

    # Create lead time by origin
    origins = [
        ("Asia", "SGSIN", "sea", r.randint(25, 40)),
        ("Asia", "SGSIN", "air", r.randint(3, 8)),
        ("Europe", "GBFXT", "sea", r.randint(7, 14)),
        ("Europe", "DEHAM", "road", r.randint(3, 7)),
        ("Americas", "USNYC", "air", r.randint(5, 12)),
    ]

    for i, (region, port, mode, transit) in enumerate(origins):
        for site in sites[:3]:
            origin_id = f"LTO-{i * 10 + sites.index(site) + 1:06d}"
            lead_time_origins.append({
                "origin_id": origin_id,
                "origin_region": region,
                "origin_port": port,
                "dest_dc": site["site_id"],
                "transit_days": transit,
                "transit_variability_days": r.randint(2, 8),
                "mode": mode,
                "rate_gbp_per_unit": r.uniform(0.50, 3.50),
                "last_updated": g.as_of - timedelta(days=r.randint(1, 30)),
            })

    # Create fabric requirements
    categories = set(p["category"] for p in products)
    materials = ["Cotton", "Polyester", "Wool", "Silk", "Linen", "Nylon"]

    for category in list(categories)[:15]:
        for material in r.sample(materials, r.randint(1, 4)):
            fabric_requirements.append({
                "category": category,
                "material": material,
                "annual_requirement_units": r.randint(10000, 100000),
                "monthly_average_units": r.randint(800, 8000),
                "supplier_id": r.choice([s["supplier_id"] for s in suppliers]),
                "lead_time_weeks": r.randint(4, 12),
                "stock_on_hand": r.randint(500, 5000),
                "critical_threshold": r.randint(1000, 2500),
            })

    return {
        "planning_parameters": planning_params,
        "order_proposals": order_proposals,
        "supply_plans": supply_plans,
        "supply_demand_gaps": supply_demand_gaps,
        "supply_requests": supply_requests,
        "supplier_lead_time_actuals": supplier_lead_times,
        "lead_time_by_origin": lead_time_origins,
        "fabric_requirements": fabric_requirements,
    }
