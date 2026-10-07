"""Loss prevention data: shrink records, incidents, control programs and high-risk products."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    stores = [s["site_id"] for s in g.master("sites") if s["type"] == "store"]
    products = g.master("products")

    shrink_records = []
    incidents = []
    control_programs = []
    high_risk_products = []
    loss_prevention_cases = []

    # Generate shrink records for all stores (weekly, last 52 weeks)
    for store_id in stores:
        for week_offset in range(52):
            date = g.as_of - timedelta(days=7 * week_offset)
            total_shrink = r.gauss(2000, 800)
            if total_shrink < 0:
                total_shrink = 0

            adjustment = r.gauss(500, 300)
            if adjustment < 0:
                adjustment = 0

            pos_exception = r.gauss(400, 250)
            if pos_exception < 0:
                pos_exception = 0

            theft_est = r.gauss(600, 400)
            if theft_est < 0:
                theft_est = 0

            damage_est = r.gauss(200, 150)
            if damage_est < 0:
                damage_est = 0

            error_est = r.gauss(300, 200)
            if error_est < 0:
                error_est = 0

            shrink_records.append({
                "site_id": store_id,
                "recorded_date": date,
                "shrink_gbp": total_shrink,
                "adjustment_gbp": adjustment,
                "pos_exception_gbp": pos_exception,
                "theft_estimated_gbp": theft_est,
                "damage_estimated_gbp": damage_est,
                "error_estimated_gbp": error_est
            })

    # Generate incidents (approximately 2-3 per store per month)
    incident_types = ["theft_external", "theft_internal", "damage", "system_error", "pos_void", "audit_adjust"]
    reporters = ["EMP-0001", "EMP-0002", "EMP-0003", "EMP-0004", "EMP-0005"]

    for store_id in stores:
        for month_offset in range(12):
            date = g.as_of - timedelta(days=30 * month_offset)
            num_incidents = r.randint(2, 4)

            for _ in range(num_incidents):
                inc_type = r.choice(incident_types)
                product = r.choice(products)

                if inc_type == "theft_external":
                    units = r.randint(1, 5)
                    value = units * product["unit_cost_gbp"] * r.uniform(1.5, 2.5)
                elif inc_type == "theft_internal":
                    units = r.randint(1, 3)
                    value = units * product["unit_cost_gbp"] * r.uniform(1.2, 1.8)
                elif inc_type == "damage":
                    units = r.randint(1, 10)
                    value = units * product["unit_cost_gbp"] * r.uniform(0.5, 0.9)
                elif inc_type == "system_error":
                    units = r.randint(1, 5)
                    value = units * product["unit_cost_gbp"]
                else:
                    units = r.randint(1, 3)
                    value = units * product["unit_cost_gbp"]

                incident_id = f"INC-{len(incidents) + 1:06d}"
                incidents.append({
                    "incident_id": incident_id,
                    "site_id": store_id,
                    "recorded_date": date,
                    "incident_type": inc_type,
                    "sku": product["sku"],
                    "units_involved": units,
                    "value_gbp": value,
                    "description": f"{inc_type} incident",
                    "reported_by": r.choice(reporters),
                    "root_cause": "",
                    "updated_at": datetime.combine(date, datetime.min.time()) + timedelta(hours=r.randint(0, 23))
                })

    # Generate control programs for stores
    control_types = ["tagging", "layout", "staffing", "security_staff", "pos_rules", "self_checkout_monitoring", "cctv", "training"]

    for store_id in stores[:150]:  # Most stores have at least one control
        num_controls = r.randint(1, 3)
        for _ in range(num_controls):
            control_type = r.choice(control_types)
            months_ago = r.randint(1, 24)
            start_date = g.as_of - timedelta(days=30 * months_ago)

            if control_type == "tagging":
                cost = r.gauss(35000, 8000)
                reduction = r.gauss(12000, 3000)
            elif control_type == "staffing":
                cost = r.gauss(95000, 15000)
                reduction = r.gauss(22000, 5000)
            elif control_type == "self_checkout_monitoring":
                cost = r.gauss(65000, 12000)
                reduction = r.gauss(15000, 4000)
            elif control_type == "cctv":
                cost = r.gauss(150000, 30000)
                reduction = r.gauss(18000, 4000)
            elif control_type == "training":
                cost = r.gauss(12000, 3000)
                reduction = r.gauss(8000, 2000)
            else:
                cost = r.gauss(40000, 10000)
                reduction = r.gauss(10000, 3000)

            control_programs.append({
                "control_id": f"CTL-{len(control_programs) + 1:06d}",
                "site_id": store_id,
                "control_type": control_type,
                "start_date": start_date,
                "annual_cost_gbp": max(0, cost),
                "shrink_reduction_gbp": max(0, reduction),
                "status": "active"
            })

    # Generate high-risk products at stores
    high_risk_skus = [p["sku"] for p in products if r.random() < 0.05][:20]

    for store_id in stores[:100]:
        for sku in r.sample(high_risk_skus, min(3, len(high_risk_skus))):
            protection = r.choice(["tagging", "locked_case", "staff_supervised"])
            loss_driver = r.choice(["theft", "damage", "error"])
            added_date = g.as_of - timedelta(days=r.randint(30, 365))

            high_risk_products.append({
                "hrp_id": f"HRP-{len(high_risk_products) + 1:06d}",
                "site_id": store_id,
                "sku": sku,
                "added_date": added_date,
                "risk_level": r.choice(["low", "medium", "high"]),
                "protection_type": protection,
                "loss_driver": loss_driver,
                "notes": "",
                "status": "active",
                "updated_at": datetime.combine(added_date, datetime.min.time())
            })

    return {
        "shrink_records": shrink_records,
        "incidents": incidents,
        "control_programs": control_programs,
        "high_risk_products": high_risk_products,
        "loss_prevention_cases": loss_prevention_cases
    }
