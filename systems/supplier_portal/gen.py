"""Supplier Portal: relationships, capacities, stock, quality issues, delays and communications."""
from datetime import datetime, timedelta


def generate(g):
    """Generate supplier portal data."""
    r = g.rng

    suppliers = g.master("suppliers")
    factories = g.master("factories")
    products = g.master("products")
    po_lines = g.master("po_lines")
    purchase_orders = g.master("purchase_orders")

    supplier_variances = []
    supplier_claims = []
    corrective_actions = []
    supply_position = []
    supplier_delays = []
    factory_operations = []
    material_supply = []
    supplier_esg = []
    supplier_communications = []

    # Generate supplier variances (ASN vs receipt)
    variance_id = 1
    for po_line in po_lines[:200]:  # Sample of POs
        if r.random() < 0.3:  # 30% have variances
            variance_units = r.randint(-50, 50)
            if variance_units != 0:
                variance = {
                    "variance_id": f"VAR-{variance_id:06d}",
                    "po_id": po_line["po_id"],
                    "shipment_id": f"ASN-{po_line['po_id'].split('-')[1]}",
                    "supplier_id": po_line.get("supplier_id", r.choice([s["supplier_id"] for s in suppliers[:50]])),
                    "sku": po_line.get("sku", ""),
                    "asn_quantity": po_line.get("quantity", 1000),
                    "receipt_quantity": max(0, po_line.get("quantity", 1000) + variance_units),
                    "variance_units": variance_units,
                    "variance_reason": r.choice(["short-ship", "damage", "system_error", "over-ship"]),
                    "variance_value_gbp": abs(variance_units) * r.uniform(5, 25),
                    "is_claimable": variance_units < 0,
                    "claim_window_days": max(0, 30 - r.randint(0, 40)),
                    "received_at": g.date_between(60, 1),
                    "created_at": datetime.now(),
                }
                supplier_variances.append(variance)
                variance_id += 1

    # Generate supplier claims from variances
    claim_id = 1
    for var in supplier_variances[:50]:
        if var["is_claimable"] and var["claim_window_days"] > 0:
            claim = {
                "claim_id": f"CLM-{claim_id:06d}",
                "po_id": var["po_id"],
                "supplier_id": var["supplier_id"],
                "variance_id": var["variance_id"],
                "claim_type": var["variance_reason"].replace("_", "_"),
                "claim_amount_gbp": var["variance_value_gbp"],
                "status": r.choices(["draft", "submitted", "accepted", "settled"], [30, 40, 20, 10])[0],
                "raised_at": var["received_at"],
                "submitted_at": var["received_at"] + timedelta(days=r.randint(1, 5)),
                "settled_amount_gbp": var["variance_value_gbp"] * r.uniform(0.7, 1.0),
                "notes": "Variance from ASN",
                "created_by": "EMP-01234",
                "updated_at": datetime.now(),
            }
            supplier_claims.append(claim)
            claim_id += 1

    # Generate corrective actions
    car_id = 1
    for supplier in suppliers[:80]:
        for _ in range(r.randint(0, 3)):
            raised = g.date_between(90, 1)
            has_response = r.random() < 0.6
            car = {
                "corrective_action_id": f"CAR-{car_id:06d}",
                "supplier_id": supplier["supplier_id"],
                "sku": r.choice([p["sku"] for p in products])[:20] if products else "SKU-001",
                "issue_type": r.choice(["quality", "compliance", "delivery"]),
                "severity": r.choices(["high", "medium", "low"], [20, 50, 30])[0],
                "description": f"Issue with {r.choice(['seam strength', 'colour fastness', 'delivery', 'documentation'])}",
                "root_cause": r.choice([
                    "Equipment miscalibration",
                    "Operator training gap",
                    "Material quality",
                    "Process change",
                    "Under investigation"
                ]) if r.random() < 0.6 else None,
                "corrective_actions": "Will implement corrective actions" if has_response else None,
                "response_received": has_response,
                "response_date": raised + timedelta(days=r.randint(3, 10)) if has_response else None,
                "response_text": "Will resolve within one week" if has_response else None,
                "status": r.choices(["open", "responded", "closed"], [30, 40, 30])[0] if has_response else "open",
                "raised_at": raised,
                "due_date": raised + timedelta(days=14),
                "closed_at": raised + timedelta(days=r.randint(15, 30)) if r.random() < 0.4 else None,
                "created_by": "EMP-01234",
                "updated_at": datetime.now(),
            }
            corrective_actions.append(car)
            car_id += 1

    # Generate supply position (current stock and capacity)
    position_id = 1
    for supplier in suppliers[:80]:
        for prod in r.sample(products[:100], min(5, len(products))):
            pos = {
                "position_id": f"SPP-{position_id:06d}",
                "supplier_id": supplier["supplier_id"],
                "sku": prod.get("sku", "SKU-001"),
                "material_id": None,
                "position_date": g.as_of,
                "available_stock_units": r.randint(0, 10000),
                "available_capacity_units": r.randint(1000, 50000),
                "committed_capacity_units": r.randint(1000, 40000),
                "total_capacity_units": r.randint(20000, 100000),
                "lead_time_days": r.randint(10, 60),
                "moq_units": r.randint(100, 5000),
                "price_gbp_per_unit": r.uniform(2, 50),
                "currency": "GBP",
                "updated_at": datetime.now(),
            }
            supply_position.append(pos)
            position_id += 1

    # Generate supplier delays
    delay_id = 1
    for supplier in suppliers[:50]:
        if r.random() < 0.4:  # 40% have active delays
            delay = {
                "delay_notice_id": f"DLY-{delay_id:06d}",
                "supplier_id": supplier["supplier_id"],
                "po_id": None,
                "sku": r.choice([p["sku"] for p in products])[:20] if products else None,
                "original_ship_date": g.date_between(14, 1),
                "new_ship_date": g.date_between(7, 0) + timedelta(days=r.randint(7, 21)),
                "delay_days": r.randint(3, 30),
                "reason": r.choice(["capacity", "materials", "quality", "other"]),
                "impact_assessment": "May affect production schedule",
                "notice_received_at": g.date_between(7, 0),
                "acknowledged": r.random() < 0.8,
                "contingency_plan": "Expediting from alternate source" if r.random() < 0.5 else "Adjusting production schedule",
                "status": r.choices(["active", "mitigated"], [60, 40])[0],
                "created_at": datetime.now(),
            }
            supplier_delays.append(delay)
            delay_id += 1

    # Generate factory operations
    fop_id = 1
    for factory in factories[:50]:
        for week in range(12):
            period_start = g.days_ago(week * 7)
            period_end = period_start + timedelta(days=6)
            monthly_cap = factory.get("capacity_units_month", "50000")
            monthly_cap = int(monthly_cap) if isinstance(monthly_cap, str) else monthly_cap
            capacity = monthly_cap // 4  # Weekly capacity
            utilisation = r.randint(40, 95)
            production = int(capacity * utilisation / 100)

            fop = {
                "operation_id": f"FOP-{fop_id:06d}",
                "factory_id": factory["factory_id"],
                "period_start": period_start,
                "period_end": period_end,
                "capacity_units": capacity,
                "utilisation_pct": utilisation,
                "production_units": production,
                "orders_in_progress": r.randint(2, 15),
                "material_inbound_status": r.choices(["on_track", "delayed", "critical"], [60, 30, 10])[0],
                "material_inbound_notes": "Materials arriving on schedule" if r.random() < 0.7 else "Some delays in fabric inbound",
                "moq_units": r.randint(500, 5000),
                "moq_lead_time_days": r.randint(21, 56),
                "peak_capacity_units": int(capacity * 1.1),
                "sample_lead_time_days": r.randint(7, 21),
                "certification_status": "OEKO-TEX ISO 14001",
                "data_quality": r.choices(["verified", "estimated"], [70, 30])[0],
                "reported_at": period_start,
                "created_at": datetime.now(),
            }
            factory_operations.append(fop)
            fop_id += 1

    # Generate material supply data
    mat_id = 1
    material_types = ["Organic cotton", "Recycled polyester", "Cotton blend", "Modal", "Linen"]
    for supplier in suppliers[:60]:
        for _ in range(r.randint(1, 4)):
            mat = {
                "material_id": f"MAT-{mat_id:06d}",
                "supplier_id": supplier["supplier_id"],
                "material_name": r.choice(material_types) + f" {r.randint(100, 400)} GSM",
                "material_type": r.choice(["fabric", "trim", "zip"]),
                "lead_time_days": r.randint(14, 56),
                "moq_units": r.randint(500, 10000),
                "price_gbp_per_unit": r.uniform(0.5, 15),
                "stock_units_available": r.randint(0, 50000),
                "stock_as_of": g.as_of,
                "capacity_monthly_units": r.randint(10000, 200000),
                "width_cm": 140 if "fabric" in ["fabric"] else None,
                "composition": "100% Organic Cotton",
                "certifications": "OEKO-TEX GOTS" if r.random() < 0.5 else "OEKO-TEX",
                "sustainability_notes": "Sustainably sourced" if r.random() < 0.4 else "",
                "last_updated": datetime.now(),
            }
            material_supply.append(mat)
            mat_id += 1

    # Generate supplier ESG submissions
    esg_id = 1
    for supplier in suppliers[:100]:
        for year in [2024, 2025]:
            status = r.choices(["not_submitted", "submitted", "accepted", "low_quality"], [25, 40, 30, 5])[0]
            esg = {
                "esg_id": f"ESG-{esg_id:06d}",
                "supplier_id": supplier["supplier_id"],
                "submission_year": year,
                "submission_type": r.choice(["esg_full", "emissions_only"]),
                "submission_status": status,
                "submitted_date": g.date_between(90, 1) if status != "not_submitted" else None,
                "data_quality_score": r.randint(50, 100) if status in ["submitted", "accepted"] else None,
                "emissions_tonnes_co2e": r.randint(100, 10000) if status in ["submitted", "accepted"] else None,
                "renewable_pct": r.randint(0, 100) if r.random() < 0.7 else None,
                "water_usage_m3": r.randint(1000, 100000) if r.random() < 0.5 else None,
                "waste_tonnes": r.randint(10, 1000) if r.random() < 0.5 else None,
                "emissions_reduction_commitment_pct": r.randint(5, 50) if r.random() < 0.6 else None,
                "emissions_reduction_target_year": 2030 if r.random() < 0.6 else None,
                "audit_evidence_provided": r.random() < 0.4,
                "evidence_quality": r.choice(["verified", "self_reported", "missing"]),
                "follow_up_needed": status == "low_quality",
                "notes": "Quality review required" if status == "low_quality" else "",
                "created_at": datetime.now(),
            }
            supplier_esg.append(esg)
            esg_id += 1

    # Generate supplier communications (comments, milestones, access logs)
    com_id = 1
    for supplier in suppliers[:80]:
        # Sample comments
        for _ in range(r.randint(0, 3)):
            com = {
                "communication_id": f"COM-{com_id:06d}",
                "supplier_id": supplier["supplier_id"],
                "sku": r.choice([p["sku"] for p in products[:50]])[:20] if products else "",
                "po_id": None,
                "communication_type": r.choice(["sample_comment", "milestone_update"]),
                "title": r.choice([
                    "Sample approved with minor revisions",
                    "Seam strength needs improvement",
                    "Production milestone update",
                    "Sample rejected - resubmit"
                ]),
                "content": "Please review and confirm",
                "from_party": r.choice(["hv_to_supplier", "supplier_to_hv"]),
                "response_time_hours": r.randint(2, 48) if r.random() < 0.7 else None,
                "status": r.choice(["sent", "responded"]),
                "portal_page": None,
                "accessed_at": None,
                "deadline": g.date_between(30, 1) if r.random() < 0.5 else None,
                "overdue": r.random() < 0.1,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
            supplier_communications.append(com)
            com_id += 1

    # Portal access logs
    for supplier in suppliers[:50]:
        for _ in range(r.randint(2, 8)):
            com = {
                "communication_id": f"COM-{com_id:06d}",
                "supplier_id": supplier["supplier_id"],
                "sku": None,
                "po_id": None,
                "communication_type": "portal_access",
                "title": "Portal access",
                "content": "",
                "from_party": "supplier_to_hv",
                "response_time_hours": None,
                "status": "sent",
                "portal_page": r.choice([
                    "Dashboard",
                    "Orders",
                    "Forecasts",
                    "Performance",
                    "Documents",
                    "Capacity"
                ]),
                "accessed_at": datetime.combine(
                    g.date_between(30, 1),
                    datetime.min.time()
                ) + timedelta(hours=r.randint(6, 22), minutes=r.randint(0, 59)),
                "deadline": None,
                "overdue": False,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
            supplier_communications.append(com)
            com_id += 1

    return {
        "supplier_variances": supplier_variances,
        "supplier_claims": supplier_claims,
        "corrective_actions": corrective_actions,
        "supply_position": supply_position,
        "supplier_delays": supplier_delays,
        "factory_operations": factory_operations,
        "material_supply": material_supply,
        "supplier_esg": supplier_esg,
        "supplier_communications": supplier_communications,
    }
