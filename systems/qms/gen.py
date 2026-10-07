"""Quality management data: production lots, inspections, incidents, holds, CARs."""
from datetime import datetime, timedelta, date


def generate(g):
    r = g.rng

    # Get master data
    factories = g.master("factories")
    suppliers = g.master("suppliers")
    products = g.master("products")
    pos = g.master("purchase_orders")

    # Filter to relevant data
    factories = [f for f in factories if f["status"] in ["approved", "conditional"]]
    products = [p for p in products if p["status"] in ["active", "new"]]
    pos = [p for p in pos if p["status"] in ["open", "confirmed", "shipped", "received"] and p["supplier_id"] in [s["supplier_id"] for s in suppliers]]

    lots = []
    inspections = []
    measurements = []
    incidents = []
    holds = []
    investigations = []
    cars = []
    scorecards = []
    pack_damage = []
    reviews = []

    # Generate production lots around POs
    for po in r.sample(pos, min(len(pos), 60)):
        # Get SKUs from this PO (we'll approximate by assuming 1-3 SKUs per PO)
        skus_for_po = r.sample([p["sku"] for p in products], r.randint(1, 3))

        for sku in skus_for_po:
            # Get factory for this supplier
            supplier_factories = [f for f in factories if f["supplier_id"] == po["supplier_id"]]
            if not supplier_factories:
                continue
            factory = r.choice(supplier_factories)

            # Production lot dates around PO timeline
            po_date = datetime.fromisoformat(po["order_date"])
            ship_date = datetime.fromisoformat(po["ship_date"])

            # Lots produced between order and ship date
            if (ship_date.date() - po_date.date()).days > 5:
                prod_date = po_date + timedelta(days=r.randint(1, (ship_date.date() - po_date.date()).days - 2))
            else:
                prod_date = po_date + timedelta(days=1)

            days_ago = (g.as_of - prod_date.date()).days
            if days_ago < 0 or days_ago > 90:  # Only recent lots
                continue

            lot_num = len(lots)
            lot_id = f"LOT-{lot_num + 1:06d}"
            qty = r.randint(100, 2000)

            lot_status = r.choices(["in_inspection", "released", "reworked", "rejected"], [60, 30, 7, 3])[0]
            lot_disposition = {"in_inspection": "pending", "released": "released", "reworked": "rework", "rejected": "reject"}.get(lot_status, "pending")

            lots.append({
                "lot_id": lot_id,
                "sku": sku,
                "factory_id": factory["factory_id"],
                "po_id": po["po_id"],
                "qty_produced": qty,
                "produced_at": prod_date.date(),
                "status": lot_status,
                "lot_disposition": lot_disposition,
                "created_at": prod_date,
                "updated_at": prod_date + timedelta(days=r.randint(1, 10))
            })

    # Generate inspections for lots
    for lot in lots:
        # 80-90% of lots get at least one inspection
        if r.random() > 0.85:
            continue

        # Inline inspection (always)
        num_inspections = r.choices([1, 2, 3], [60, 30, 10])[0]
        for i in range(num_inspections):
            inspection_type = ["inline", "final", "final"][i] if i < num_inspections else "final"

            ins_num = len(inspections)
            inspection_id = f"INS-{ins_num + 1:06d}"

            units_inspected = r.randint(30, min(200, lot["qty_produced"]))
            defect_rate = r.gauss(2, 3)  # Average 2% defects
            defect_rate = max(0, min(20, defect_rate))  # Clamp 0-20%
            defects = max(0, int(units_inspected * defect_rate / 100))

            # Later inspections more likely to pass
            pass_rates = [70, 85, 95]  # inline, next, final
            pass_fail = r.choices(["pass", "fail", "conditional"], [pass_rates[min(i, 2)], 20 - pass_rates[min(i, 2)] // 2, 5])[0]

            prod_date = datetime.fromisoformat(str(lot["produced_at"]))
            inspected_at = prod_date + timedelta(days=r.randint(1, 14))

            inspections.append({
                "inspection_id": inspection_id,
                "lot_id": lot["lot_id"],
                "factory_id": lot["factory_id"],
                "inspection_type": inspection_type,
                "units_inspected": units_inspected,
                "defects_found": defects,
                "pass_fail": pass_fail,
                "scheduled_at": None,
                "inspected_at": inspected_at,
                "created_at": inspected_at
            })

    # Generate measurements for some inspections
    for inspection in r.sample(inspections, min(len(inspections), 30)):
        if inspection["defects_found"] == 0:
            continue  # Only generate measurements when there are defects to measure

        measurement_types = ["chest_width", "inseam", "collar_size", "weight", "colour_value", "shrinkage", "tensile_strength"]
        for mtype in r.sample(measurement_types, r.randint(1, 3)):
            meas_num = len(measurements)
            spec_val = r.uniform(100, 200)
            tolerance = spec_val * 0.05  # 5% tolerance band

            if r.random() < 0.7:  # 70% within tolerance
                actual = spec_val + r.gauss(0, tolerance / 3)
                passed = True
            else:
                actual = spec_val + r.gauss(0, tolerance)
                passed = False

            measurements.append({
                "measurement_id": f"MSR-{meas_num + 1:06d}",
                "inspection_id": inspection["inspection_id"],
                "lot_id": inspection["lot_id"],
                "measurement_type": mtype,
                "actual_value": round(actual, 2),
                "spec_value": round(spec_val, 2),
                "tolerance_lower": round(spec_val - tolerance, 2),
                "tolerance_upper": round(spec_val + tolerance, 2),
                "unit": "mm" if mtype != "colour_value" else "points",
                "pass": passed,
                "created_at": inspection["inspected_at"]
            })

    # Generate incidents from failed inspections
    for inspection in inspections:
        if inspection["pass_fail"] != "fail" or inspection["defects_found"] == 0:
            continue

        # Maybe create an incident
        if r.random() < 0.7:
            inc_num = len(incidents)
            incident_id = f"INC-{inc_num + 1:06d}"

            issue_types = [
                "Defect rate exceeds acceptable level",
                "Colour inconsistency detected",
                "Seam strength failure",
                "Measurement out of tolerance",
                "Visual defects (staining, holes, snags)",
                "Zipper failure",
                "Shrinkage beyond specification"
            ]

            incidents.append({
                "incident_id": incident_id,
                "sku": inspection["lot_id"],
                "factory_id": inspection["factory_id"],
                "lot_id": inspection["lot_id"],
                "issue_description": r.choice(issue_types),
                "severity": r.choices(["low", "medium", "high", "critical"], [20, 50, 25, 5])[0],
                "status": r.choices(["open", "investigating", "resolved", "closed"], [30, 40, 20, 10])[0],
                "created_at": inspection["inspected_at"],
                "updated_at": inspection["inspected_at"] + timedelta(days=r.randint(1, 7))
            })

    # Generate holds from incidents
    for incident in incidents:
        if r.random() < 0.6:  # 60% of incidents result in holds
            hold_num = len(holds)
            hold_id = f"HLD-{hold_num + 1:06d}"

            product = [p for p in products if p["sku"] == incident["sku"]]
            sku = product[0]["sku"] if product else incident["sku"]

            holds.append({
                "hold_id": hold_id,
                "sku": sku,
                "lot_id": incident["lot_id"],
                "hold_reason": f"Quality hold pending investigation: {incident['issue_description']}",
                "status": r.choices(["active", "released", "expired"], [60, 30, 10])[0],
                "related_incident_id": incident["incident_id"],
                "created_at": incident["created_at"],
                "released_at": incident["created_at"] + timedelta(days=r.randint(1, 14)) if r.random() < 0.5 else None,
                "updated_at": incident["updated_at"]
            })

    # Generate investigations from incidents
    for incident in r.sample(incidents, min(len(incidents), 10)):
        inv_num = len(investigations)
        investigation_id = f"INV-{inv_num + 1:06d}"

        investigations.append({
            "investigation_id": investigation_id,
            "related_incident_id": incident["incident_id"],
            "scope": f"Investigating root cause of: {incident['issue_description']}",
            "status": r.choices(["open", "in_progress", "on_hold", "closed"], [10, 40, 20, 30])[0],
            "findings": "Root cause analysis in progress" if r.random() < 0.6 else "Process variation at supplier factory",
            "created_at": incident["created_at"],
            "updated_at": incident["updated_at"] + timedelta(days=r.randint(1, 14))
        })

    # Generate CARs from incidents
    for incident in r.sample(incidents, min(len(incidents), 12)):
        if r.random() < 0.7:  # 70% of incidents trigger CARs
            car_num = len(cars)
            car_id = f"CAR-{car_num + 1:06d}"

            factory = [f for f in factories if f["factory_id"] == incident["factory_id"]]
            supplier_id = factory[0]["supplier_id"] if factory else None

            if not supplier_id:
                continue

            corrective_actions = [
                "Audit supplier process controls and implement corrective measures",
                "Increase inspection frequency to 100% sampling until trend reverses",
                "Conduct supplier training on specification requirements",
                "Review and tighten supplier's acceptance criteria",
                "Request material test certificates from supplier"
            ]

            cars.append({
                "car_id": car_id,
                "supplier_id": supplier_id,
                "factory_id": incident["factory_id"],
                "issue_description": incident["issue_description"],
                "requested_action": r.choice(corrective_actions),
                "status": r.choices(["draft", "sent", "acknowledged", "in_progress", "closed"], [15, 25, 20, 30, 10])[0],
                "created_at": incident["created_at"],
                "sent_at": incident["created_at"] + timedelta(days=r.randint(1, 3)) if r.random() < 0.8 else None,
                "updated_at": incident["updated_at"]
            })

    # Generate factory quality scorecards (weekly)
    for factory in factories[:10]:  # Top 10 factories
        for week_offset in range(-12, 1):  # Last 12 weeks
            week_start = g.weeks(1)[0] + timedelta(weeks=week_offset)
            week_end = week_start + timedelta(days=6)

            # Find inspections in this week for this factory
            week_start_date = week_start if isinstance(week_start, date) else week_start.date()
            week_end_date = week_start_date + timedelta(days=6)
            week_inspections = [i for i in inspections
                              if i["factory_id"] == factory["factory_id"]
                              and week_start_date <= i["inspected_at"].date() <= week_end_date]

            if not week_inspections:
                continue

            scorecard_num = len(scorecards)
            scorecard_id = f"SCD-{scorecard_num + 1:06d}"

            total_units = sum(i["units_inspected"] for i in week_inspections)
            total_defects = sum(i["defects_found"] for i in week_inspections)
            defect_rate = 100.0 * total_defects / total_units if total_units > 0 else 0
            pass_rate = 100.0 if defect_rate < 1.0 else max(50, 100 - defect_rate)
            critical = len([i for i in week_inspections if i["pass_fail"] == "fail"])

            # Risk score: 0-100, higher is worse
            risk_score = min(100, defect_rate * 10 + critical * 5 + r.gauss(0, 5))

            scorecards.append({
                "scorecard_id": scorecard_id,
                "factory_id": factory["factory_id"],
                "period": week_start_date,
                "total_units_inspected": total_units,
                "defects_found": total_defects,
                "defect_rate_pct": round(defect_rate, 1),
                "pass_rate_pct": round(pass_rate, 1),
                "critical_defects": critical,
                "on_time_delivery_pct": round(r.gauss(85, 10), 1),
                "risk_score": round(risk_score, 1),
                "created_at": week_end + timedelta(days=1)
            })

    # Generate pack damage tracking
    for product in r.sample(products, min(len(products), 20)):
        pack_types = ["polybag", "carton", "rigid_box", "hanging", "blister"]

        for week_offset in range(-12, 1):
            week_start_dt = g.weeks(1)[0] + timedelta(weeks=week_offset)
            week_start_date = week_start_dt if isinstance(week_start_dt, date) else week_start_dt.date()

            for pack_type in r.sample(pack_types, r.randint(1, 3)):
                damage_num = len(pack_damage)
                damage_id = f"DMG-{damage_num + 1:06d}"

                units_shipped = r.randint(200, 2000)
                damage_rate_base = {"polybag": 5, "carton": 2, "rigid_box": 0.5, "hanging": 3, "blister": 4}
                damage_rate = damage_rate_base.get(pack_type, 2) + r.gauss(0, 1.5)
                damage_rate = max(0.1, min(10, damage_rate))
                units_damaged = max(0, int(units_shipped * damage_rate / 100))

                pack_damage.append({
                    "damage_id": damage_id,
                    "sku": product["sku"],
                    "pack_type": pack_type,
                    "period": week_start_date,
                    "units_shipped": units_shipped,
                    "units_damaged": units_damaged,
                    "damage_rate_pct": round(damage_rate, 2),
                    "damage_type": r.choice(["crushed", "water_damaged", "punctured", "torn", "leaking"]),
                    "created_at": datetime.combine(week_start_date, datetime.min.time()) + timedelta(days=7)
                })

    # Generate quality reviews
    for style in r.sample([p["style_id"] for p in products], min(len(set(p["style_id"] for p in products)), 8)):
        review_num = len(reviews)
        review_id = f"REV-{review_num + 1:06d}"

        reviews.append({
            "review_id": review_id,
            "style_id": style,
            "review_type": r.choice(["fit", "durability", "appearance", "top_returns"]),
            "status": r.choices(["open", "in_progress", "closed"], [20, 40, 40])[0],
            "findings": "Review in progress" if r.random() < 0.5 else "No significant quality issues detected",
            "created_at": g.as_of - timedelta(days=r.randint(1, 30)),
            "updated_at": g.as_of - timedelta(days=r.randint(0, 15))
        })

    return {
        "production_lots": lots,
        "quality_inspections": inspections,
        "inspection_measurements": measurements,
        "quality_incidents": incidents,
        "quality_holds": holds,
        "quality_investigations": investigations,
        "supplier_corrective_actions": cars,
        "factory_quality_scorecards": scorecards,
        "pack_damage_tracking": pack_damage,
        "quality_reviews": reviews
    }


def calculate_recommended_tolerance(ctx, factory_id, material, measurement_type):
    """Calculate recommended tolerance based on factory data and material properties."""
    # Query factory capability
    rows = ctx.q("""
        SELECT AVG(pass_rate_pct) as avg_pass_rate,
               AVG(defect_rate_pct) as avg_defect_rate
        FROM factory_quality_scorecards
        WHERE factory_id = $fid
        ORDER BY period DESC LIMIT 12
    """, fid=factory_id)

    if not rows:
        rows = [{"avg_pass_rate": 90, "avg_defect_rate": 2.5}]

    pass_rate = rows[0]["avg_pass_rate"]

    # Tolerance bands based on material and capability
    base_tolerance = {"cotton": 2.0, "polyester": 1.5, "silk": 1.0, "wool": 2.5}.get(material, 1.5)

    # Adjust by factory capability
    if pass_rate < 80:
        tolerance = base_tolerance * 1.5
    elif pass_rate > 95:
        tolerance = base_tolerance * 0.8
    else:
        tolerance = base_tolerance

    return {
        "factory_id": factory_id,
        "material": material,
        "measurement_type": measurement_type,
        "recommended_tolerance_mm": round(tolerance, 2),
        "factory_pass_rate_pct": round(pass_rate, 1),
        "basis": "Statistical process control based on factory 12-week pass rate"
    }
