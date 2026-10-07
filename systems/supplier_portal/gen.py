"""Supplier Portal: relationships, capacities, stock, quality issues, delays and communications."""
import random
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
    # SUP-0072 (the short-shipper in the story, Vaughan Industries) and SUP-0013 (one small claimed short) are fully seeded, so they are skipped here.
    po_by_id = {p["po_id"]: p for p in purchase_orders}
    prod_by_sku = {p["sku"]: p for p in products}
    ship_by_po = {sh["po_id"]: sh for sh in shipments}
    variance_id = 1
    for pl in po_lines:
        po = po_by_id.get(pl["po_id"])
        sh = ship_by_po.get(pl["po_id"])
        if not po or not sh or po["status"] not in ("received", "closed") or not sh.get("ata"):
            continue
        if po["supplier_id"] in ("SUP-0013", "SUP-0072"):
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
    # Commercial terms are a property of the factory, not of the week: one MOQ / lead time set per factory.
    # Story factories: Vietnamese denim shortlist (04:33:Q3), seeded CN factories used by other questions.
    fixed_terms = {"FAC-0066": (3000, 45, 14), "FAC-0070": (5000, 50, 21), "FAC-0017": (2500, 42, 14),
                   "FAC-0107": (1000, 35, 14), "FAC-0108": (1500, 40, 21)}
    # Bangladesh factories (04:33:Q4): (utilisation this peak season, same weeks a year earlier, latest material inbound status)
    bd_story = {
        "FAC-0057": (94, 86, "on_track"), "FAC-0098": (92, 78, "delayed"), "FAC-0136": (91, 74, "on_track"),
        "FAC-0138": (96, 93, "critical"), "FAC-0086": (88, 80, "on_track"), "FAC-0150": (83, 81, "on_track"),
        "FAC-0151": (76, 79, "on_track"), "FAC-0093": (71, 65, "on_track"), "FAC-0094": (64, 70, "on_track"),
        "FAC-0097": (79, 82, "on_track"), "FAC-0137": (35, 85, "delayed"),
    }
    bd_notes = {"delayed": "Greige denim and cotton yarn delayed at port; cutting plan under review",
                "critical": "Yarn shortage: only 5 days of cover on the main denim lines"}
    fop_id = 1
    fac_by_id = {f["factory_id"]: f for f in factories}
    for factory in factories:
        if factory["factory_id"] == "FAC-0121":  # seeded story factory
            continue
        trm = random.Random("fterm-" + factory["factory_id"])
        terms = fixed_terms.get(factory["factory_id"]) or (trm.randint(5, 50) * 100, trm.randint(21, 56), trm.randint(7, 21))
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
            fop["moq_units"], fop["moq_lead_time_days"], fop["sample_lead_time_days"] = terms
            story = bd_story.get(factory["factory_id"])
            if story:
                fop["utilisation_pct"] = story[0]
                fop["production_units"] = int(capacity * story[0] / 100)
                fop["material_inbound_status"] = story[2] if week == 0 else "on_track"
                fop["material_inbound_notes"] = bd_notes.get(story[2], "Materials arriving on schedule") if week == 0 else "Materials arriving on schedule"
            factory_operations.append(fop)
            fop_id += 1
    # Same weeks a year earlier (52 weeks back), so utilisation can be compared year on year
    for factory in factories:
        if factory["factory_id"] == "FAC-0121":
            continue
        fid = factory["factory_id"]
        cur = [x for x in factory_operations if x["factory_id"] == fid]
        trm = random.Random("fyoy-" + fid)
        cur_avg = sum(x["utilisation_pct"] for x in cur) / len(cur)
        trend = trm.uniform(-8, 6)
        for week in range(12):
            period_start = g.days_ago((week + 52) * 7)
            capacity = cur[0]["capacity_units"]
            if fid in bd_story:
                util = bd_story[fid][1]
            else:
                util = max(35, min(88, round(cur_avg - trend + trm.uniform(-7, 7))))
            factory_operations.append({
                "operation_id": f"FOP-{fop_id:06d}", "factory_id": fid, "period_start": period_start,
                "period_end": period_start + timedelta(days=6), "capacity_units": capacity, "utilisation_pct": util,
                "production_units": int(capacity * util / 100), "orders_in_progress": trm.randint(2, 15),
                "material_inbound_status": "on_track", "material_inbound_notes": "Materials arriving on schedule",
                "moq_units": cur[0]["moq_units"], "moq_lead_time_days": cur[0]["moq_lead_time_days"],
                "peak_capacity_units": int(capacity * 1.1), "sample_lead_time_days": cur[0]["sample_lead_time_days"],
                "certification_status": "OEKO-TEX ISO 14001", "data_quality": "verified",
                "reported_at": period_start, "created_at": now_ts,
            })
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
            mat["composition"] = {"Organic cotton": "100% Organic Cotton", "Recycled polyester": "100% Recycled Polyester",
                                  "Cotton blend": "60% Cotton 40% Polyester", "Modal": "100% Modal", "Linen": "100% Linen"
                                  }[mat["material_name"].rsplit(" ", 2)[0]]
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

    # Rows the seed already covers for the same supplier and year are not generated twice
    seeded_esg = {("SUP-0001", 2025), ("SUP-0001", 2026), ("SUP-0013", 2025), ("SUP-0022", 2025), ("SUP-0012", 2025)}
    supplier_esg[:] = [e for e in supplier_esg if (e["supplier_id"], e["submission_year"]) not in seeded_esg]
    for e in supplier_esg:  # evidence must agree with what was submitted
        if e["submission_status"] == "not_submitted":
            e["audit_evidence_provided"], e["evidence_quality"] = False, "missing"
        elif e["audit_evidence_provided"]:
            e["evidence_quality"] = "verified"
        else:
            e["evidence_quality"] = "missing" if e["evidence_quality"] == "missing" else "self_reported"
    # Top 20 active suppliers by spend (05:45:Q2, 05:45:Q3, 05:48:Q3): latest (2025) submission
    # (renewable %, emissions tCO2e, committed reduction % or None, target year, status, quality score, evidence)
    esg_story = {
        "SUP-0044": (62, 18400, 25, 2030, "accepted", 91, "verified"), "SUP-0049": (48, 21000, 20, 2030, "accepted", 88, "verified"),
        "SUP-0057": (8, 52000, None, None, "submitted", 61, "self_reported"), "SUP-0036": (35, 24500, 15, 2030, "accepted", 84, "verified"),
        "SUP-0035": (12, 31000, None, None, "submitted", 58, "missing"), "SUP-0072": (20, 9800, 10, 2030, "low_quality", 52, "self_reported"),
        "SUP-0074": (30, 14200, 18, 2030, "accepted", 79, "self_reported"), "SUP-0027": (5, 17500, None, None, "submitted", 63, "self_reported"),
        "SUP-0014": (85, 6400, 30, 2028, "accepted", 94, "verified"), "SUP-0011": (40, 11800, 20, 2030, "accepted", 86, "verified"),
        "SUP-0038": (10, 15300, None, None, "submitted", 57, "missing"), "SUP-0015": (55, 7200, 25, 2030, "accepted", 90, "verified"),
        "SUP-0033": (92, 3900, 40, 2030, "accepted", 96, "verified"), "SUP-0065": (28, 8800, 12, 2030, "pending_review", 72, "self_reported"),
        "SUP-0060": (70, 4100, 30, 2030, "accepted", 89, "verified"), "SUP-0039": (22, 6900, 15, 2030, "accepted", 77, "self_reported"),
        "SUP-0063": (15, 10400, None, None, "submitted", 60, "missing"), "SUP-0046": (33, 8300, 20, 2030, "accepted", 82, "verified"),
        "SUP-0028": (18, 7600, 10, 2030, "pending_review", 70, "self_reported"), "SUP-0016": (25, 12100, 20, 2030, "accepted", 83, "verified"),
    }
    for e in supplier_esg:
        st = esg_story.get(e["supplier_id"])
        if st and e["submission_year"] == 2025:
            e.update({"renewable_pct": st[0], "emissions_tonnes_co2e": st[1], "emissions_reduction_commitment_pct": st[2],
                      "emissions_reduction_target_year": st[3], "submission_status": st[4], "data_quality_score": st[5],
                      "evidence_quality": st[6], "audit_evidence_provided": st[6] == "verified",
                      "submission_type": "esg_full", "follow_up_needed": st[4] == "low_quality",
                      "notes": "Emissions methodology unclear; scope 2 basis to be confirmed" if st[4] == "low_quality" else "",
                      "submitted_date": g.days_ago(70)})

    # Forecasts shared with suppliers (04:35:Q5): one row per completed four-week period, own RNG per supplier
    supplier_forecasts = []
    fc_id = 1
    story_bias = {"SUP-0012": [4, 6, 11, 17, 22, 26]}  # oldest to newest of the last six periods: we increasingly over-forecast
    for supplier in suppliers:
        if not skus_by_supplier.get(supplier["supplier_id"]):
            continue
        frng = random.Random("fc-" + supplier["supplier_id"])
        base = max(2000, int(float(supplier["annual_spend_gbp"]) / 13 / 18))
        for k in range(12, 0, -1):
            actual = int(base * frng.uniform(0.85, 1.15))
            story = story_bias.get(supplier["supplier_id"])
            if story and k <= 6:
                bias = story[6 - k]
                actual = base
            else:
                bias = round(frng.gauss(3, 6), 1)
            start = g.days_ago(28 * k)
            supplier_forecasts.append({
                "forecast_id": f"FCS-{fc_id:06d}", "supplier_id": supplier["supplier_id"], "period_start": start,
                "period_end": start + timedelta(days=27), "horizon_weeks": 12,
                "forecast_units": int(actual * (1 + bias / 100)), "actual_units": actual,
                "shared_at": start - timedelta(days=84),
            })
            fc_id += 1

    # Where fabric fibre comes from (04:39:Q5): origin mix of each cotton fabric, by the mill's country
    origin_pools = {
        "CN": [("CN", 50), ("US", 20), ("AU", 15), ("BR", 15)], "IN": [("IN", 70), ("US", 15), ("BR", 10), ("AU", 5)],
        "TR": [("TR", 35), ("US", 25), ("UZ", 20), ("BR", 20)], "BD": [("IN", 35), ("US", 30), ("BR", 20), ("AU", 15)],
        "VN": [("US", 40), ("BR", 25), ("AU", 20), ("IN", 15)], "PT": [("US", 35), ("BR", 25), ("EG", 20), ("IN", 20)],
    }
    default_pool = [("US", 35), ("IN", 30), ("BR", 20), ("AU", 15)]
    sup_country = {s["supplier_id"]: s["country"] for s in suppliers}
    material_origins = [
        {"material_id": "MAT-900001", "origin_country": "IN", "share_pct": 70.0},
        {"material_id": "MAT-900001", "origin_country": "US", "share_pct": 20.0},
        {"material_id": "MAT-900001", "origin_country": "AU", "share_pct": 10.0},
        {"material_id": "MAT-900101", "origin_country": "CN", "share_pct": 45.0},
        {"material_id": "MAT-900101", "origin_country": "US", "share_pct": 25.0},
        {"material_id": "MAT-900101", "origin_country": "BR", "share_pct": 15.0},
        {"material_id": "MAT-900101", "origin_country": "AU", "share_pct": 15.0},
    ]
    for mat in material_supply:
        if mat["material_type"] != "fabric" or "cotton" not in mat["composition"].lower():
            continue
        orng = random.Random("orig-" + mat["material_id"])
        pool = origin_pools.get(sup_country.get(mat["supplier_id"]), default_pool)
        weights = [max(3, w + orng.randint(-5, 5)) for _, w in pool]
        weights = weights[: orng.randint(2, len(pool))] if orng.random() < 0.4 else weights
        tot = sum(weights)
        shares = [round(100.0 * w / tot, 1) for w in weights]
        shares[0] = round(shares[0] + 100.0 - sum(shares), 1)
        for (cty, _), sh in zip(pool, shares):
            material_origins.append({"material_id": mat["material_id"], "origin_country": cty, "share_pct": sh})

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

    # Generated comments and corrective actions are about the supplier's own products (SKU chosen deterministically, no RNG)
    sup_skus = defaultdict(list)
    for p in products:
        sup_skus[p["supplier_id"]].append(p["sku"])
    for row in supplier_communications:
        if row["communication_type"] in ("sample_comment", "milestone_update"):
            own = sup_skus.get(row["supplier_id"])
            row["sku"] = own[int(row["communication_id"][4:]) % len(own)] if own else None
    for row in corrective_actions:
        own = sup_skus.get(row["supplier_id"])
        if own:
            row["sku"] = own[int(row["corrective_action_id"][4:]) % len(own)]

    # Low-quality ESG submissions carry a poor score and a specific follow-up note (05:48:Q4)
    for e in supplier_esg:
        if e["submission_status"] == "low_quality" and e["data_quality_score"] is None:
            n = int(e["supplier_id"][4:])
            e["data_quality_score"] = 38 + (n * 7 + e["submission_year"]) % 21
            e["emissions_tonnes_co2e"] = e["emissions_tonnes_co2e"] or 900 + n * 113
            e["notes"] = ["Emissions methodology unclear; scope 2 basis to be confirmed", "Scope 1 and 2 figures incomplete; site list missing",
                          "Water and waste figures inconsistent with prior year"][n % 3]

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
        "supplier_forecasts": supplier_forecasts,
        "material_origins": material_origins,
    }
