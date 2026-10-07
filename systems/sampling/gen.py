"""Sampling system: product samples, test orders, and launch tracking.

Story rows (seed/*.csv) cover SS27 launches, the backpack-style sample rounds and K-1700 pack samples.
Generated background avoids the SS27 season and the planted styles, and never has open fit comments or
pending sample approvals, so the planted rows are what a correct answer finds.
"""
from datetime import timedelta

PLANTED_STYLES = {"STY-4578", "STY-6227", "STY-8286", "STY-4012", "STY-8975", "STY-7763", "STY-K-1700", "STY-PF-220",
                  "STY-5926", "STY-8491"}


def generate(g):
    r = g.rng
    products = [p for p in g.master("products") if p["style_id"] not in PLANTED_STYLES][:30]
    all_products = g.master("products")
    factories = g.master("factories")

    sample_requests, sample_rounds, fit_comments = [], [], []
    launch_products, milestones, signals, lead_times, test_orders = [], [], [], [], []
    seen_styles = set()
    n_req = n_rnd = n_fit = n_prd = n_mls = n_sig = 0

    for product in products:
        sku, style_id, supplier_id = product["sku"], product["style_id"], product["supplier_id"]
        factory_id = product["factory_id"]

        if r.random() < 0.7:
            n_req += 1
            req_date = g.as_of - timedelta(days=r.randint(30, 90))
            status = r.choices(["received", "approved"], [0.4, 0.6])[0]
            received_at = req_date + timedelta(days=r.randint(5, 30))
            approved_at = received_at + timedelta(days=r.randint(1, 14)) if status == "approved" else None
            sample_requests.append({
                "sample_request_id": f"SAM-{n_req:06d}", "sku": sku, "style_id": style_id,
                "supplier_id": supplier_id, "factory_id": factory_id, "pack_material": None,
                "status": status, "created_at": req_date,
                "required_by_date": req_date + timedelta(days=35), "received_at": received_at,
                "approval_deadline": req_date + timedelta(days=45), "approved_at": approved_at,
                "approved_by": "EMP-00024" if approved_at else None,
                "notes": "Sample received" if status == "received" else None,
            })

        if style_id in seen_styles:
            continue
        seen_styles.add(style_id)

        # Finished sample rounds only: earlier rounds rejected, last approved.
        if r.random() < 0.6:
            num = r.randint(1, 3)
            start = g.as_of - timedelta(days=r.randint(150, 220))
            for round_no in range(1, num + 1):
                n_rnd += 1
                deadline = start + timedelta(days=r.randint(21, 35))
                submitted = deadline - timedelta(days=r.randint(0, 5))
                final = round_no == num
                decided = submitted + timedelta(days=r.randint(2, 8))
                sample_rounds.append({
                    "round_id": f"RND-{n_rnd:06d}", "style_id": style_id, "factory_id": factory_id,
                    "round_no": round_no, "status": "approved" if final else "rejected",
                    "created_at": start, "deadline": deadline, "submitted_at": submitted,
                    "approval_status": "approved" if final else "rejected",
                    "approved_at": decided if final else None, "approved_by": "EMP-00024" if final else None,
                    "rejection_reason": None if final else r.choice(["Fit incorrect", "Seam quality", "Colour mismatch"]),
                    "resubmission_requested": False if final else True,
                })
                if r.random() < 0.4:
                    n_fit += 1
                    created = start + timedelta(days=r.randint(1, 10))
                    fit_comments.append({
                        "comment_id": f"FIT-{n_fit:06d}", "style_id": style_id, "supplier_id": supplier_id,
                        "comment_text": r.choice(["Sleeve length needs adjustment", "Waist seam sits too high",
                                                  "Collar fold is too tight", "Shoulder point needs 1cm adjustment"]),
                        "status": "resolved", "created_at": created, "resolved_at": decided,
                    })
                start = decided + timedelta(days=1)

        # Background pipeline in other seasons (SS27 is the planted spring pipeline).
        if r.random() < 0.4:
            n_prd += 1
            season = r.choice(["AW27", "SS28"])
            launch_date = g.as_of + timedelta(days=r.randint(250, 420))
            launch_products.append({
                "product_id": f"PRD-{n_prd:06d}", "sku": sku, "style_id": style_id, "season": season,
                "planned_launch_date": launch_date, "risk_level": r.choices(["low", "medium"], [0.7, 0.3])[0],
                "status": r.choices(["in_development", "sample_phase"], [0.6, 0.4])[0],
                "created_at": g.as_of - timedelta(days=r.randint(10, 60)),
                "supplier_risk_factor": round(r.uniform(0.05, 0.3), 2),
                "approval_risk_factor": round(r.uniform(0.05, 0.3), 2),
            })
            for mtype, weeks in (("sample_submission", 40), ("sample_approval", 36), ("factory_commitment", 28),
                                 ("production_start", 22)):
                n_mls += 1
                milestones.append({
                    "milestone_id": f"MLS-{n_mls:06d}", "style_id": style_id, "milestone_type": mtype,
                    "due_date": launch_date - timedelta(weeks=weeks), "completed_date": None, "status": "on_track",
                })
            for stype in ("trend_validation", "demand_signal", "supplier_risk", "quality_risk"):
                n_sig += 1
                low = stype in ("supplier_risk", "quality_risk")
                signals.append({
                    "signal_id": f"SIG-{n_sig:06d}", "style_id": style_id, "season": season, "signal_type": stype,
                    "signal_value": round(r.uniform(0.1, 0.3) if low else r.uniform(0.5, 0.8), 2),
                    "created_at": g.as_of - timedelta(days=r.randint(5, 40)), "notes": f"{stype} assessment",
                })

    # Standard lead times: derived from master product lead times per category and supplier.
    groups = {}
    for p in all_products:
        groups.setdefault((p["category"], p["supplier_id"]), []).append(int(p["lead_time_days"]))
    n_lt = 0
    for (category, supplier_id), days in sorted(groups.items()):
        n_lt += 1
        lead = max(days)
        lead_times.append({
            "lead_time_id": f"LT-{n_lt:06d}", "category": category, "supplier_id": supplier_id,
            "lead_days": lead, "fast_track_days": max(7, round(lead * 0.6)),
            "updated_at": g.as_of - timedelta(days=r.randint(10, 90)),
        })

    for i in range(4):
        product = r.choice(products)
        created_at = g.as_of - timedelta(days=r.randint(40, 100))
        test_orders.append({
            "test_order_id": f"TST-{i + 1:06d}", "sku": product["sku"], "style_id": product["style_id"],
            "volume_units": r.choice([200, 300, 500, 800]), "status": "completed", "created_at": created_at,
            "approved_at": created_at + timedelta(days=r.randint(1, 5)),
            "purpose": r.choice(["trend_validation", "demand_test", "market_test"]),
        })

    return {
        "sample_requests": sample_requests, "sample_rounds": sample_rounds, "fit_comments": fit_comments,
        "launch_products": launch_products, "critical_path_milestones": milestones,
        "launch_readiness_signals": signals, "lead_times_category": lead_times, "test_orders": test_orders,
    }
