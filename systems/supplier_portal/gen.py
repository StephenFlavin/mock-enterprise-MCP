"""Supplier Portal: relationships, capacities, stock, quality issues, delays and communications."""
from collections import defaultdict
from datetime import date, datetime, time, timedelta


def generate(g):
    """Generate supplier portal data."""
    r = g.rng
    now_ts = datetime.combine(g.as_of, time(9, 0))

    suppliers = g.master("suppliers")
    factories = g.master("factories")
    products = g.master("products")
    po_lines = g.master("po_lines")
    purchase_orders = g.master("purchase_orders")
    shipments = g.master("shipments")
    employees = g.master("employees")

    supplier_variances = []
    supplier_claims = []
    corrective_actions = []
    supply_position = []
    supplier_delays = []
    factory_operations = []
    material_supply = []
    supplier_esg = []
    supplier_communications = []

    # Receipt-versus-ASN variances (01:4:Q4): master PO lines received short or over in the last 90 days (small ones only).
    # SUP-0013 (the short-shipper in the story) is fully seeded, so it is skipped here.
    po_by_id = {p["po_id"]: p for p in purchase_orders}
    prod_by_sku = {p["sku"]: p for p in products}
    ship_by_po = {sh["po_id"]: sh for sh in shipments}
    variance_id = 1
    for pl in po_lines:
        po = po_by_id.get(pl["po_id"])
        sh = ship_by_po.get(pl["po_id"])
        if not po or not sh or po["status"] not in ("received", "closed") or not sh.get("ata"):
            continue
        if po["supplier_id"] == "SUP-0013":
            continue
        recd = date.fromisoformat(sh["ata"])
        if recd > g.as_of or recd < g.days_ago(90):
            continue
        asn_qty, rec_qty = int(pl["qty_ordered"]), int(pl["qty_received"])
        units = rec_qty - asn_qty
        if units == 0 or pl["sku"] not in prod_by_sku:
            continue
        unit_cost = float(prod_by_sku[pl["sku"]]["unit_cost_gbp"])
        if abs(units) * unit_cost > 1500:  # larger variances are still under dispute and not logged in the portal
            continue
        reason = "over-ship" if units > 0 else r.choices(["short-ship", "damage", "receiving_error"], [70, 15, 15])[0]
        supplier_variances.append({
            "variance_id": f"VAR-{variance_id:06d}",
            "po_id": pl["po_id"],
            "shipment_id": sh["shipment_id"],
            "supplier_id": po["supplier_id"],
            "sku": pl["sku"],
            "asn_quantity": asn_qty,
            "receipt_quantity": rec_qty,
            "variance_units": units,
            "variance_reason": reason,
            "variance_value_gbp": round(abs(units) * unit_cost, 2),
            "is_claimable": units < 0 and reason in ("short-ship", "damage"),
            "claim_window_days": 14,
            "received_at": recd,
            "created_at": datetime.combine(recd, time(10, 0)),
        })
        variance_id += 1

    # Claims already raised, only for variances whose window has closed (the story's open ones are still unclaimed)
    claim_id = 1
    for var in supplier_variances:
        if not var["is_claimable"] or (g.as_of - var["received_at"]).days <= 14 or r.random() > 0.35:
            continue
        status = r.choices(["submitted", "accepted", "settled", "rejected"], [30, 30, 30, 10])[0]
        submitted = var["received_at"] + timedelta(days=r.randint(1, 10))
        supplier_claims.append({
            "claim_id": f"CLM-{claim_id:06d}",
            "po_id": var["po_id"],
            "supplier_id": var["supplier_id"],
            "variance_id": var["variance_id"],
            "claim_type": "damage" if var["variance_reason"] == "damage" else "short_ship",
            "claim_amount_gbp": var["variance_value_gbp"],
            "status": status,
            "raised_at": submitted,
            "submitted_at": submitted,
            "settled_amount_gbp": round(var["variance_value_gbp"] * r.uniform(0.7, 1.0), 2) if status == "settled" else None,
            "notes": "Claim raised from receipt variance",
            "created_by": r.choice(employees)["employee_id"] if employees else "EMP-00001",
            "updated_at": datetime.combine(submitted, time(9, 0)),
        })
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
                "created_by": r.choice(employees)["employee_id"] if employees else "EMP-00001",
                "updated_at": now_ts,
            }
            corrective_actions.append(car)
            car_id += 1

    # Supply position: one latest snapshot per product (plus 4-weekly history), built from each supplier's own master SKUs.
    # Story profiles: (total capacity per SKU, committed % at latest snapshot). Categories keyed by supplier.
    cat_profile = {
        # core trousers range (03:24:Q2): SUP-0008 is the current mill and nearly full; SUP-0036 and SUP-0044 have room
        ("Trousers", "SUP-0008"): (20000, 91), ("Trousers", "SUP-0036"): (35000, 70), ("Trousers", "SUP-0044"): (30000, 65),
        ("Trousers", "SUP-0015"): (24000, 80), ("Trousers", "SUP-0037"): (24000, 96), ("Trousers", "SUP-0043"): (20000, 95),
        ("Trousers", "SUP-0051"): (26000, 88), ("Trousers", "SUP-0058"): (22000, 85), ("Trousers", "SUP-0064"): (30000, 90),
        ("Trousers", "SUP-0065"): (25000, 92), ("Trousers", "SUP-0079"): (20000, 94),
        # bedding range (04:32:Q3): SUP-0039 has headroom, SUP-0011 is nearly full
        ("Bedding", "SUP-0039"): (40000, 52), ("Bedding", "SUP-0011"): (30000, 93), ("Bedding", "SUP-0004"): (30000, 74),
        ("Bedding", "SUP-0074"): (25000, 85), ("Bedding", "SUP-0046"): (20000, 88),
    }
    # Supplier X (03:24:Q1): SUP-0070 capacity filling up over six months, 2,000 units per SKU planned next quarter
    trend_profile = {"SUP-0070": (15000, [72, 76, 81, 86, 91, 96], 2000)}
    stock_story = {  # 03:22:Q2 at-risk SKUs: units the supplier holds now
        "SKU-101260": 6200, "SKU-102884": 0, "SKU-104536": 3100, "SKU-101722": 0, "SKU-100280": 1800,
        "SKU-105341": 4200, "SKU-102338": 0, "SKU-101575": 2500, "SKU-103458": 0, "SKU-101834": 900, "SKU-105159": 0,
    }
    mto_story = {  # 03:28:Q4 long-tail SKUs: (make-to-order lead days, MOQ) or None when not offered
        "SKU-102898": (21, 100), "SKU-106034": (28, 150), "SKU-102289": None, "SKU-104130": (35, 200),
        "SKU-104053": (21, 100), "SKU-101253": None, "SKU-105054": (14, 50), "SKU-101617": (28, 100),
    }
    skus_by_supplier = defaultdict(list)
    for prod in products:
        skus_by_supplier[prod["supplier_id"]].append(prod)
    position_id = 1
    for sup_id in sorted(skus_by_supplier):
        for idx, prod in enumerate(sorted(skus_by_supplier[sup_id], key=lambda x: x["sku"])):
            sku = prod["sku"]
            prof = cat_profile.get((prod["category"], sup_id))
            trend = trend_profile.get(sup_id)
            if trend:
                total_cap, pcts, nq = trend[0], list(trend[1]), trend[2]
            elif prof:
                total_cap = prof[0]
                pcts = [prof[1] - 2 * k for k in (3, 2, 1, 0)]
                nq = r.randint(4, 12) * 500
            else:
                total_cap = r.randint(80, 600) * 100
                base = r.randint(45, 85)
                pcts = []
                for _ in range(4 if idx < 2 else 1):
                    pcts.append(base)
                    base = max(35, min(88, base + r.randint(-4, 5)))
                pcts = pcts[::-1] if len(pcts) > 1 else pcts
                nq = r.randint(1, 10) * 100
            if sku in mto_story:
                mto = mto_story[sku]
            elif r.random() < 0.35:
                mto = (r.choice([14, 21, 28]), r.choice([50, 100, 150, 200]))
            else:
                mto = None
            for k, pct in enumerate(pcts):
                age = (len(pcts) - 1 - k) * 28
                committed = int(total_cap * pct / 100)
                stock = stock_story.get(sku, r.choice([0, 0, r.randint(200, 8000)])) if age == 0 else r.choice([0, r.randint(200, 8000)])
                supply_position.append({
                    "position_id": f"SPP-{position_id:06d}",
                    "supplier_id": sup_id,
                    "sku": sku,
                    "material_id": None,
                    "position_date": g.days_ago(age),
                    "available_stock_units": stock,
                    "available_capacity_units": total_cap - committed,
                    "committed_capacity_units": committed,
                    "total_capacity_units": total_cap,
                    "lead_time_days": int(prod["lead_time_days"]),
                    "moq_units": int(prod["moq"]),
                    "price_gbp_per_unit": float(prod["unit_cost_gbp"]),
                    "currency": "GBP",
                    "updated_at": datetime.combine(g.days_ago(age), time(6, 0)),
                    "next_quarter_units": nq,
                    "mto_lead_time_days": mto[0] if mto else None,
                    "mto_moq_units": mto[1] if mto else None,
                })
                position_id += 1
    # Fabric mills (03:24:Q4): monthly capacity snapshots per material, oldest first; cotton and polyester mills are filling up
    mills = [
        ("SUP-0001", "MAT-900101", 120000, [78, 82, 88, 92, 95, 97], 8),
        ("SUP-0003", "MAT-900102", 90000, [70, 75, 82, 88, 92, 94], 8),
        ("SUP-0015", "MAT-900103", 12000, [55, 58, 60, 62, 63, 64], 12),
        ("SUP-0010", "MAT-900104", 60000, [60, 61, 62, 60, 63, 62], 8),
        ("SUP-0008", "MAT-900105", 40000, [64, 66, 65, 67, 66, 68], 6),
        ("SUP-0012", "MAT-900106", 20000, [72, 75, 79, 83, 86, 89], 10),
    ]
    for sup_id, mat_id, cap, pcts, lead_weeks in mills:
        for k, pct in enumerate(pcts):
            age = (len(pcts) - 1 - k) * 28
            committed = int(cap * pct / 100)
            supply_position.append({
                "position_id": f"SPP-{position_id:06d}",
                "supplier_id": sup_id,
                "sku": None,
                "material_id": mat_id,
                "position_date": g.days_ago(age),
                "available_stock_units": r.randint(1000, 9000),
                "available_capacity_units": cap - committed,
                "committed_capacity_units": committed,
                "total_capacity_units": cap,
                "lead_time_days": lead_weeks * 7,
                "moq_units": 1000,
                "price_gbp_per_unit": None,
                "currency": "GBP",
                "updated_at": datetime.combine(g.days_ago(age), time(6, 0)),
            })
            position_id += 1

    # Supplier delay notices: history only (mitigated or expired); the live notices are seeded
    delay_id = 1
    for supplier in suppliers:
        if r.random() < 0.35:
            sku_pool = skus_by_supplier.get(supplier["supplier_id"]) or []
            if not sku_pool:
                continue
            prod = r.choice(sku_pool)
            notice = g.date_between(120, 30)
            delay_days = r.randint(3, 20)
            orig = notice + timedelta(days=r.randint(5, 20))
            supplier_delays.append({
                "delay_notice_id": f"DLY-{delay_id:06d}",
                "supplier_id": supplier["supplier_id"],
                "po_id": None,
                "sku": prod["sku"],
                "original_ship_date": orig,
                "new_ship_date": orig + timedelta(days=delay_days),
                "delay_days": delay_days,
                "reason": r.choice(["capacity", "materials", "quality", "other"]),
                "impact_assessment": "Late ship date absorbed by buffer stock",
                "notice_received_at": notice,
                "acknowledged": True,
                "contingency_plan": r.choice(["Expedited from alternate source", "Adjusted production schedule"]),
                "status": r.choice(["mitigated", "expired"]),
                "created_at": datetime.combine(notice, time(9, 0)),
                "material_type": "finished_goods",
                "material_id": None,
                "units_delayed": None,
            })
            delay_id += 1

    # Generate factory operations
    fop_id = 1
    for factory in factories:
        if factory["factory_id"] == "FAC-0121":  # seeded story factory
            continue
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
                "created_at": now_ts,
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
                "last_updated": now_ts,
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
                "created_at": now_ts,
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
                "created_at": now_ts,
                "updated_at": now_ts,
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
                "created_at": now_ts,
                "updated_at": now_ts,
            }
            supplier_communications.append(com)
            com_id += 1

    # Ship-date history (03:24:Q1, 02:13:Q4): confirmed ship date (master PO ship date) versus actual departure (master shipment ATD)
    ship_date_history = []
    for po in purchase_orders:
        sh = ship_by_po.get(po["po_id"])
        if not sh or not sh.get("atd") or po["status"] not in ("shipped", "received", "closed"):
            continue
        confirmed, actual = date.fromisoformat(po["ship_date"]), date.fromisoformat(sh["atd"])
        if actual > g.as_of:
            continue
        ship_date_history.append({
            "po_id": po["po_id"],
            "supplier_id": po["supplier_id"],
            "factory_id": po["factory_id"],
            "order_date": po["order_date"],
            "confirmed_ship_date": confirmed,
            "actual_ship_date": actual,
            "days_late": max((actual - confirmed).days, 0),
        })

    # Spare parts quoted by maintenance suppliers (01:10:Q2): the cmms spare parts are seeded; add other equipment classes
    part_supply = []
    mhe_parts = ["Mast chain", "Hydraulic pump", "Drive wheel", "Battery charger", "Control handle", "Lift cylinder"]
    for i, (cls, nm) in enumerate([(c, n) for c in ("forklift", "reach_truck") for n in mhe_parts]):
        part_supply.append({
            "part_id": f"PRT-{i + 1:06d}",
            "part_name": f"{cls.replace('_', ' ').capitalize()} {nm.lower()}",
            "asset_class": cls,
            "supplier_id": r.choice(["SUP-0014", "SUP-0027", "SUP-0067"]),
            "lead_time_days": r.choice([5, 7, 10, 14, 21]),
            "moq_units": r.choice([1, 1, 2, 4]),
            "price_gbp_per_unit": round(r.uniform(60, 1800), 2),
            "stock_units_available": r.randint(0, 20),
            "quoted_at": g.date_between(90, 5),
        })

    return {
        "ship_date_history": ship_date_history,
        "part_supply": part_supply,
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
