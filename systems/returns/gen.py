"""Background returns data: one return per 5-10 orders randomly selected, with conditions and disposition."""
from datetime import datetime, timedelta
from collections import defaultdict


def generate(g):
    r = g.rng
    fake = g.fake

    # Reference data
    reason_codes = [
        ("WRONG_SIZE", "Too large or too small"),
        ("WRONG_COLOUR", "Not the colour expected"),
        ("DAMAGE", "Damaged on arrival"),
        ("DEFECT", "Quality defect"),
        ("WRONG_ITEM", "Wrong item sent"),
        ("NOT_AS_DESCRIBED", "Not as shown online"),
        ("CHANGED_MIND", "Customer changed mind"),
        ("DUPLICATE", "Duplicate order"),
    ]

    disposition_routes = ["restocked", "refurbished", "liquidated", "recycled", "destroyed"]
    condition_grades = ["A", "B", "C", "D", "E"]
    channels = ["web", "app", "click_collect", "store"]

    # Get master order and PO data
    orders = g.master("orders")
    products = g.master("products")
    suppliers = g.master("suppliers")

    # Build lookup: sku -> product info
    sku_map = {p["sku"]: p for p in products}

    # Generate return reasons reference
    return_reasons = [
        {"reason_code": code, "description": desc, "category": "Logistics" if code in ["WRONG_ITEM", "DAMAGE", "WRONG_COLOUR"] else "Quality" if code == "DEFECT" else "Customer"}
        for code, desc in reason_codes
    ]

    # Generate disposition rules - sample rules for different categories/ages
    disposition_rules = [
        {"rule_id": f"DIS-{i+1:06d}", "product_category": cat, "min_age_days": min_age, "max_age_days": max_age,
         "disposition_route": route, "status": "active", "effective_from": g.as_of - timedelta(days=90),
         "updated_at": g.as_of - timedelta(days=r.randint(1, 60))}
        for i, (cat, min_age, max_age, route) in enumerate([
            ("Apparel", 0, 30, "restocked"),
            ("Apparel", 31, 60, "refurbished"),
            ("Apparel", 61, 365, "liquidated"),
            ("Electronics", 0, 30, "restocked"),
            ("Electronics", 31, 60, "liquidated"),
            ("Electronics", 61, 365, "recycled"),
            ("Home", 0, 30, "restocked"),
            ("Home", 31, 60, "refurbished"),
            ("Home", 61, 365, "liquidated"),
        ])
    ]

    # Generate liquidator rates
    liquidator_rates = [
        {"liquidator_id": f"LQD-{i+1:06d}", "name": f"Liquidator {chr(65+i)}", "product_category": cat,
         "recovery_rate_pct": rate, "payment_terms_days": terms, "effective_date": g.as_of - timedelta(days=30)}
        for i, (cat, rate, terms) in enumerate([
            ("Electronics", 40, 30),
            ("Electronics", 35, 30),
            ("Apparel", 15, 45),
            ("Apparel", 12, 45),
            ("Home", 25, 30),
        ])
    ]

    # Generate returns centre capacity by date (past and future)
    capacity_data = []
    for days_offset in range(-90, 90):
        date = g.as_of + timedelta(days=days_offset)
        is_peak = (date.month in [11, 12]) or (date.weekday() >= 4)  # November/December or weekends
        capacity_id = f"CAP-{days_offset+91:04d}"
        capacity_data.append({
            "capacity_id": capacity_id,
            "date": date,
            "capacity_units_per_day": 2000 if is_peak else 1200,
            "target_throughput_units": 1800 if is_peak else 1000,
            "actual_throughput_units": r.randint(1600, 1900) if days_offset < 0 else None,
            "staffing_needed": 25 if is_peak else 15,
            "peak_day": is_peak
        })

    # Generate returns from orders
    returns_list = []
    sku_returns_by_category = defaultdict(lambda: defaultdict(int))

    for order in orders:
        # ~20% of orders have a return
        if r.random() > 0.20:
            continue

        order_date = datetime.fromisoformat(order["order_date"])
        return_date = order_date + timedelta(days=r.randint(3, 30))

        # Skip if return date is too far in future
        if return_date.date() > g.as_of + timedelta(days=7):
            continue
        if return_date.date() < g.as_of - timedelta(days=365):
            continue

        # Pick a random reason
        reason_code, _ = r.choice(reason_codes)

        # Get SKU info for category
        skus_in_order = [p["sku"] for p in products if p["sku"] in order.get("sku", "").split(";") if p["sku"] in sku_map] if order.get("sku") else []
        if not skus_in_order:
            skus_in_order = [r.choice(products)["sku"]]

        sku = r.choice(skus_in_order)
        prod = sku_map.get(sku, {})
        category = prod.get("category", "Apparel")  # Default to Apparel which we have rules for

        # Item age when returned
        item_age_days = (return_date.date() - order_date.date()).days

        # Condition typically worse for older items or damage reasons
        if reason_code == "DAMAGE":
            condition = r.choices(["C", "D", "E"], [40, 40, 20])[0]
        elif item_age_days > 60:
            condition = r.choices(["B", "C", "D"], [30, 40, 30])[0]
        else:
            condition = r.choices(["A", "B", "C"], [50, 35, 15])[0]

        # Assign disposition
        matching_rules = [d for d in disposition_rules
                         if d["product_category"] == category
                         and d["min_age_days"] <= item_age_days <= d["max_age_days"]]
        if not matching_rules:
            # Fallback: assign based on age if no exact category match
            disposition = "restocked" if item_age_days <= 30 else "refurbished" if item_age_days <= 60 else "liquidated"
        else:
            rule = r.choice(matching_rules)
            disposition = rule["disposition_route"]
        disposition_date = return_date + timedelta(days=r.randint(1, 5))

        # Calculate recovery and cost
        handling_cost = r.gauss(8, 2) if disposition != "restocked" else r.gauss(3, 1)
        handling_cost = max(1, handling_cost)

        if disposition == "restocked":
            recovery = float(prod.get("unit_cost_gbp", 20)) * 0.95
        elif disposition == "refurbished":
            recovery = float(prod.get("unit_cost_gbp", 20)) * (0.60 if condition in ["B", "C"] else 0.40)
        elif disposition == "liquidated":
            liq_rate = next((l["recovery_rate_pct"] for l in liquidator_rates
                           if l["product_category"] == category), 30) / 100.0
            recovery = float(prod.get("unit_cost_gbp", 20)) * liq_rate
        else:
            recovery = 0

        outcome = disposition

        returns_list.append({
            "return_id": f"RET-{len(returns_list) + 1:06d}",
            "order_id": order["order_id"],
            "sku": sku,
            "style_id": prod.get("style_id", "STY-0000"),
            "return_date": return_date.date(),
            "return_reason_code": reason_code,
            "pack_type": prod.get("pack_type", "carton"),
            "item_age_days": item_age_days,
            "condition_grade": condition,
            "damage_code": "CRUSH" if reason_code == "DAMAGE" else None,
            "category": category,
            "channel": order["channel"],
            "disposition_route": disposition,
            "disposition_date": disposition_date,
            "recovery_gbp": recovery,
            "handling_cost_gbp": handling_cost,
            "outcome": outcome,
            "updated_at": disposition_date + timedelta(days=1),
        })

        sku_returns_by_category[category][sku] += 1

    # Generate disposition outcomes reference
    disposition_outcomes = [
        {"route": "restocked", "condition_grade": "A", "avg_handling_cost_gbp": 3, "avg_recovery_gbp": 95, "avg_days_to_sale": 3},
        {"route": "restocked", "condition_grade": "B", "avg_handling_cost_gbp": 5, "avg_recovery_gbp": 75, "avg_days_to_sale": 5},
        {"route": "refurbished", "condition_grade": "B", "avg_handling_cost_gbp": 12, "avg_recovery_gbp": 60, "avg_days_to_sale": 14},
        {"route": "refurbished", "condition_grade": "C", "avg_handling_cost_gbp": 15, "avg_recovery_gbp": 40, "avg_days_to_sale": 21},
        {"route": "liquidated", "condition_grade": "C", "avg_handling_cost_gbp": 8, "avg_recovery_gbp": 30, "avg_days_to_sale": 7},
        {"route": "liquidated", "condition_grade": "D", "avg_handling_cost_gbp": 8, "avg_recovery_gbp": 15, "avg_days_to_sale": 7},
        {"route": "recycled", "condition_grade": "E", "avg_handling_cost_gbp": 6, "avg_recovery_gbp": 2, "avg_days_to_sale": 5},
    ]

    # Generate pack type damage rates
    pack_type_damage = [
        {"pack_type": "carton", "category": "Electronics", "damage_rate_pct": 8.5, "sample_size": 500, "measured_from_date": g.as_of - timedelta(days=60)},
        {"pack_type": "polybag", "category": "Electronics", "damage_rate_pct": 14.2, "sample_size": 480, "measured_from_date": g.as_of - timedelta(days=60)},
        {"pack_type": "carton", "category": "Apparel", "damage_rate_pct": 3.2, "sample_size": 600, "measured_from_date": g.as_of - timedelta(days=60)},
        {"pack_type": "hanging", "category": "Apparel", "damage_rate_pct": 2.1, "sample_size": 550, "measured_from_date": g.as_of - timedelta(days=60)},
        {"pack_type": "carton", "category": "Home", "damage_rate_pct": 6.1, "sample_size": 400, "measured_from_date": g.as_of - timedelta(days=60)},
    ]

    # Generate returns handling practices by country
    practices = [
        {"practice_id": "PRC-001", "country": "GB", "practice_description": "Free returns within 30 days", "regulatory_reference": "Consumer Rights Act"},
        {"practice_id": "PRC-002", "country": "DE", "practice_description": "14-day return right, consumer pays return shipping", "regulatory_reference": "German Distance Selling Law"},
        {"practice_id": "PRC-003", "country": "FR", "practice_description": "14-day returns, seller pays shipping", "regulatory_reference": "French Consumer Code"},
        {"practice_id": "PRC-004", "country": "NL", "practice_description": "14-day returns, free within EU", "regulatory_reference": "Dutch Civil Code"},
        {"practice_id": "PRC-005", "country": "GB", "practice_description": "EPR packaging compliance required", "regulatory_reference": "Extended Producer Responsibility"},
    ]

    # Generate circularity pilots
    pilots = [
        {"pilot_id": f"PIL-{i+1:06d}", "pilot_type": ptype, "product_category": cat, "start_date": g.as_of - timedelta(days=60),
         "end_date": g.as_of + timedelta(days=30), "status": "active", "units_collected": r.randint(100, 500),
         "units_outcome_a": r.randint(20, 100), "units_outcome_b": r.randint(20, 100), "units_outcome_c": r.randint(10, 50),
         "recovery_gbp": r.randint(500, 2000), "handling_cost_gbp": r.randint(200, 800),
         "updated_at": g.as_of}
        for i, (ptype, cat) in enumerate([
            ("take_back", "Electronics"),
            ("repair", "Apparel"),
            ("resale", "Home"),
        ])
    ]

    # Generate returns charge trials
    trials = [
        {"trial_id": f"TRL-{i+1:06d}", "market": market, "charge_gbp": charge, "start_date": g.as_of - timedelta(days=30),
         "end_date": g.as_of + timedelta(days=60), "status": "active", "units_returned": r.randint(500, 2000),
         "baseline_units_returned": r.randint(600, 2200), "impact_on_rate_pct": -12.5, "impact_on_conversion_pct": 0.8,
         "updated_at": g.as_of}
        for i, (market, charge) in enumerate([("GB", 3.99), ("DE", 4.99)])
    ]

    return {
        "returns": returns_list,
        "return_reasons": return_reasons,
        "disposition_rules": disposition_rules,
        "liquidator_rates": liquidator_rates,
        "returns_centre_capacity": capacity_data,
        "circularity_pilots": pilots,
        "returns_charge_trials": trials,
        "pack_type_damage": pack_type_damage,
        "returns_handling_practices": practices,
        "disposition_outcomes": disposition_outcomes,
    }
