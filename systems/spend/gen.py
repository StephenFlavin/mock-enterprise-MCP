"""Spend analytics: supplier spend, savings initiatives, price benchmarks."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    categories = ["Home", "Womenswear", "Menswear", "Kids", "Accessories"]
    suppliers = [s["supplier_id"] for s in g.master("suppliers") if s["status"] == "active"][:40]
    countries = set(s["country"] for s in g.master("suppliers") if s["status"] == "active")

    # Generate supplier_spend: monthly spend by supplier and category for last 13 months
    supplier_spend = []
    for _ in range(400):
        supplier_id = r.choice(suppliers)
        category = r.choice(categories)
        month_offset = r.randint(0, 12)
        period_date = g.as_of - timedelta(days=30 * month_offset)
        period = period_date.strftime("%Y-%m")
        spend = r.randint(10000, 500000)
        units = r.randint(100, 5000)

        supplier_spend.append({
            "supplier_id": supplier_id,
            "category": category,
            "period": period,
            "spend_gbp": float(spend),
            "units": units,
            "invoice_count": r.choice([1, 2, 3, 4, 5, 6]),
            "avg_unit_cost_gbp": float(spend / max(units, 1)),
            "is_preferred": r.choices([True, False], [0.7, 0.3])[0]
        })

    # Generate savings_initiatives
    initiatives = []
    init_types = ["consolidation", "renegotiation", "spec_change", "nearshore", "other"]
    statuses = ["planned", "in_progress", "completed", "abandoned"]
    for i in range(80):
        reported = r.randint(50000, 500000)
        # Realised is typically 60-90% of reported
        realised = int(reported * r.uniform(0.6, 0.95)) if r.choice([True, False]) else 0
        status = r.choice(statuses)
        start_date = g.days_ago(r.randint(30, 300))
        target_date = start_date + timedelta(days=r.randint(60, 180))
        actual_date = target_date + timedelta(days=r.randint(-30, 60)) if status == "completed" else None

        initiatives.append({
            "initiative_id": f"INIT-{i+1:06d}",
            "name": f"Initiative {i+1}",
            "category": r.choice(categories),
            "supplier_id": r.choice([None] + suppliers),
            "initiative_type": r.choice(init_types),
            "reported_saving_gbp": float(reported),
            "realised_saving_gbp": float(realised) if status == "completed" else None,
            "status": status,
            "start_date": start_date,
            "target_completion_date": target_date,
            "actual_completion_date": actual_date,
            "created_at": start_date,
            "updated_at": start_date + timedelta(days=r.randint(1, 90))
        })

    # Generate savings_realisation_rates: historical completion data
    realisation_rates = []
    for init_type in init_types:
        for month_offset in range(0, 12, 3):
            period_date = g.as_of - timedelta(days=30 * month_offset)
            period = period_date.strftime("%Y-%m")
            # Rate improves over time
            rate = 60 + month_offset * 3 + r.randint(-5, 5)
            rate = min(rate, 95)
            reported = r.randint(200000, 1000000)
            realised = int(reported * rate / 100)

            realisation_rates.append({
                "initiative_type": init_type,
                "period": period,
                "realisation_rate_pct": float(rate),
                "initiatives_count": r.randint(3, 10),
                "reported_total_gbp": float(reported),
                "realised_total_gbp": float(realised)
            })

    # Generate payment_terms_benchmark
    payment_terms = []
    for category in categories:
        for country in list(countries)[:15]:
            payment_terms.append({
                "category": category,
                "supplier_country": country,
                "market_standard_days": r.choice([30, 45, 60, 90]),
                "typical_min_days": r.choice([15, 30, 45]),
                "typical_max_days": r.choice([60, 90, 120]),
                "observations_count": r.randint(5, 30)
            })

    # Generate preferred_supplier_tracking: monthly tracking
    pref_tracking = []
    for category in categories:
        for month_offset in range(0, 13):
            period_date = g.as_of - timedelta(days=30 * month_offset)
            period = period_date.strftime("%Y-%m")
            total_spend = r.randint(1000000, 5000000)
            # Preferred share increases over time (consolidation working)
            base_share = 60 + month_offset * 1.5
            share = min(base_share + r.uniform(-3, 3), 95)
            pref_spend = int(total_spend * share / 100)

            pref_tracking.append({
                "category": category,
                "period": period,
                "total_category_spend_gbp": float(total_spend),
                "preferred_spend_gbp": float(pref_spend),
                "preferred_share_pct": float(share),
                "preferred_supplier_count": r.randint(3, 8)
            })

    # Generate nearshore_forecast: nearshore supplier data
    nearshore_suppliers = suppliers[:8]
    nearshore_data = []
    for supplier_id in nearshore_suppliers:
        for month_offset in range(0, 13):
            period_date = g.as_of - timedelta(days=30 * month_offset)
            period = period_date.strftime("%Y-%m")
            spend = r.randint(50000, 300000)
            forecast = r.randint(2000, 10000)
            actual = int(forecast * r.uniform(0.8, 1.1))
            commitment = r.uniform(0.7, 1.0)

            nearshore_data.append({
                "supplier_id": supplier_id,
                "period": period,
                "actual_spend_gbp": float(spend),
                "forecasted_volume_units": forecast,
                "actual_volume_units": actual,
                "commitment_level_pct": float(commitment * 100)
            })

    # Generate price_variance_data: price paid vs benchmark
    price_variance = []
    pos = [p["po_id"] for p in g.master("purchase_orders") if p["status"] in ("received", "closed")][:50]
    for idx, po_id in enumerate(pos):
        for line_no in range(1, r.randint(2, 4)):
            po_lines = [p for p in g.master("po_lines") if p["po_id"] == po_id]
            if not po_lines or line_no > len(po_lines):
                continue
            line = po_lines[line_no - 1]
            sku = line["sku"]
            po = next((p for p in g.master("purchase_orders") if p["po_id"] == po_id), None)
            if not po:
                continue

            unit_cost = float(line["unit_cost"])
            contract_price = unit_cost * r.uniform(0.95, 1.0)
            actual_price = unit_cost * r.uniform(0.95, 1.08)
            volume = int(line["qty_received"])
            variance_pct = (actual_price - contract_price) / contract_price * 100
            variance_gbp = actual_price - contract_price

            product = next((p for p in g.master("products") if p["sku"] == sku), None)
            category = product["category"] if product else "Unknown"

            price_variance.append({
                "po_id": po_id,
                "line_no": line_no,
                "sku": sku,
                "supplier_id": po["supplier_id"],
                "category": category,
                "contract_price_gbp": float(contract_price),
                "actual_price_gbp": float(actual_price),
                "volume_units": volume,
                "variance_pct": float(variance_pct),
                "variance_gbp": float(variance_gbp),
                "source": r.choice(["contract", "benchmark", "market"])
            })

    # Generate supplier_input_costs: cost index data
    input_costs = []
    cost_components = ["raw materials", "labour", "shipping", "energy", "packaging"]
    for supplier_id in suppliers[:20]:
        for component in cost_components:
            for month_offset in range(0, 12):
                period_date = g.as_of - timedelta(days=30 * month_offset)
                period = period_date.strftime("%Y-%m")
                # Index increases over time (inflation scenario)
                base_index = 100
                trend = month_offset * 1.5
                index = base_index + trend + r.uniform(-2, 2)

                input_costs.append({
                    "supplier_id": supplier_id,
                    "cost_component": component,
                    "period": period,
                    "index_value": float(index),
                    "pct_of_total": float(100 / len(cost_components) + r.uniform(-5, 5))
                })

    return {
        "supplier_spend": supplier_spend,
        "savings_initiatives": initiatives,
        "savings_realisation_rates": realisation_rates,
        "payment_terms_benchmark": payment_terms,
        "preferred_supplier_tracking": pref_tracking,
        "nearshore_forecast": nearshore_data,
        "price_variance_data": price_variance,
        "supplier_input_costs": input_costs
    }
