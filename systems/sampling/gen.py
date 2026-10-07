"""Sampling system: product samples, test orders, and launch tracking."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng

    # Get base products from master data
    products = g.master("products")[:30]  # Use first 30 products
    suppliers = g.master("suppliers")
    factories = g.master("factories")

    sample_requests = []
    sample_rounds = []
    fit_comments = []
    launch_products = []
    critical_path_milestones = []
    launch_readiness_signals = []
    lead_times_category = []
    test_orders = []

    # Track what we've created
    request_count = 0
    round_count = 0
    fit_count = 0
    product_count = 0
    milestone_count = 0
    signal_count = 0
    lead_time_count = 0
    test_order_count = 0

    # Create sample requests and related data
    for product in products:
        sku = product["sku"]
        style_id = product["style_id"]
        category = product.get("category", "General")
        supplier_id = product.get("supplier_id", r.choice([s["supplier_id"] for s in suppliers])[:5])
        factory_id = r.choice([f["factory_id"] for f in factories if f["supplier_id"] == supplier_id])

        # 70% chance a product has a sample request
        if r.random() < 0.7:
            request_count += 1
            request_id = f"SAM-{request_count:06d}"
            req_date = g.as_of - timedelta(days=r.randint(30, 90))
            required_date = g.as_of + timedelta(days=r.randint(5, 45))
            status = r.choices(["requested", "in_progress", "received", "approved"], [0.1, 0.2, 0.3, 0.4])[0]

            received_at = None
            if status in ("received", "approved"):
                received_at = req_date + timedelta(days=r.randint(5, 30))

            approved_at = None
            if status == "approved":
                approved_at = received_at + timedelta(days=r.randint(1, 14))

            sample_requests.append({
                "sample_request_id": request_id,
                "sku": sku,
                "style_id": style_id,
                "supplier_id": supplier_id,
                "factory_id": factory_id,
                "pack_material": r.choice(["corrugated", "moulded_pulp", "recycled_plastic", None]) if r.random() < 0.3 else None,
                "status": status,
                "created_at": req_date,
                "required_by_date": required_date,
                "received_at": received_at,
                "approval_deadline": required_date + timedelta(days=7),
                "approved_at": approved_at,
                "approved_by": "EMP-00001" if approved_at else None,
                "notes": "Sample received" if status == "received" else None,
            })

        # 60% chance a product has sample rounds
        if r.random() < 0.6:
            num_rounds = r.randint(1, 3)
            for round_no in range(1, num_rounds + 1):
                round_count += 1
                round_id = f"RND-{round_count:06d}"
                round_start = g.as_of - timedelta(days=r.randint(60, 180))
                deadline = round_start + timedelta(days=r.randint(14, 42))

                # Probability decreases for later rounds
                prob_approved = 0.8 if round_no == 1 else (0.6 if round_no == 2 else 0.4)
                approval_status = r.choices(["approved", "rejected", "pending"],
                                           [prob_approved, 0.2, 1 - prob_approved - 0.2])[0]

                submitted_at = round_start + timedelta(days=r.randint(7, 28)) if round_no == 1 else deadline
                approved_at = submitted_at + timedelta(days=r.randint(1, 7)) if approval_status == "approved" else None

                status = "approved" if approval_status == "approved" else ("rejected" if approval_status == "rejected" else "submitted")

                sample_rounds.append({
                    "round_id": round_id,
                    "style_id": style_id,
                    "factory_id": factory_id,
                    "round_no": round_no,
                    "status": status,
                    "created_at": round_start,
                    "deadline": deadline,
                    "submitted_at": submitted_at,
                    "approval_status": approval_status,
                    "approved_at": approved_at,
                    "approved_by": "EMP-00002" if approved_at else None,
                    "rejection_reason": r.choice(["Fit incorrect", "Zip strength", "Seam quality", "Color mismatch"]) if approval_status == "rejected" else None,
                })

                # Add fit comments for some rounds
                if r.random() < 0.4:
                    fit_count += 1
                    fit_comments.append({
                        "comment_id": f"FIT-{fit_count:06d}",
                        "style_id": style_id,
                        "supplier_id": supplier_id,
                        "comment_text": r.choice([
                            "Sleeve length needs adjustment",
                            "Waist seam sits too high",
                            "Collar fold is too tight",
                            "Shoulder point needs 1cm adjustment",
                        ]),
                        "status": r.choice(["open", "acknowledged", "resolved"]),
                        "created_at": round_start + timedelta(days=r.randint(1, 20)),
                        "resolved_at": None,
                    })

        # 40% chance a product is in launch pipeline
        if r.random() < 0.4:
            product_count += 1
            season = r.choice(["SS27", "AW27", "SS28"])
            launch_date = g.as_of + timedelta(days=r.randint(30, 180))

            # Create launch product
            launch_products.append({
                "product_id": f"PRD-{product_count:06d}",
                "sku": sku,
                "style_id": style_id,
                "season": season,
                "planned_launch_date": launch_date,
                "risk_level": r.choices(["low", "medium", "high", "critical"],
                                       [0.4, 0.3, 0.2, 0.1])[0],
                "status": r.choices(["in_development", "sample_phase", "approval_phase", "production_ready", "at_risk"],
                                   [0.1, 0.3, 0.3, 0.2, 0.1])[0],
                "created_at": launch_date - timedelta(days=r.randint(120, 240)),
                "supplier_risk_factor": r.uniform(0, 0.8),
                "approval_risk_factor": r.uniform(0, 0.6),
            })

            # Add critical path milestones
            for milestone_type in ["sample_submission", "sample_approval", "factory_commitment", "production_start"]:
                milestone_count += 1
                m_date = launch_date - timedelta(days=r.randint(10, 120))
                m_status = r.choices(["on_track", "at_risk", "delayed", "completed"],
                                    [0.5, 0.2, 0.1, 0.2])[0]
                completed_date = m_date if m_status == "completed" else None
                if m_status == "delayed" and r.random() < 0.5:
                    completed_date = m_date + timedelta(days=r.randint(3, 14))
                    m_status = "delayed"

                critical_path_milestones.append({
                    "milestone_id": f"MLS-{milestone_count:06d}",
                    "style_id": style_id,
                    "milestone_type": milestone_type,
                    "due_date": m_date,
                    "completed_date": completed_date,
                    "status": m_status,
                })

            # Add readiness signals
            for signal_type in ["trend_validation", "demand_signal", "supplier_risk", "quality_risk"]:
                signal_count += 1
                launch_readiness_signals.append({
                    "signal_id": f"SIG-{signal_count:06d}",
                    "style_id": style_id,
                    "season": season,
                    "signal_type": signal_type,
                    "signal_value": r.uniform(0.3, 0.95),
                    "created_at": launch_date - timedelta(days=r.randint(20, 90)),
                    "notes": f"{signal_type} assessment",
                })

    # Create lead times by category
    categories = set(p.get("category", "General") for p in products)
    for category in categories:
        for supplier in r.sample(suppliers, min(3, len(suppliers))):
            lead_time_count += 1
            lead_times_category.append({
                "lead_time_id": f"LT-{lead_time_count:06d}",
                "category": category,
                "supplier_id": supplier["supplier_id"],
                "lead_days": r.randint(21, 90),
                "fast_track_days": r.randint(14, 35),
                "updated_at": g.as_of - timedelta(days=r.randint(1, 60)),
            })

    # Create test orders
    for i in range(5):
        test_order_count += 1
        product = r.choice(products)
        sku = product["sku"]
        style_id = product.get("style_id", "STY-0000")
        status = r.choices(["requested", "approved", "in_production", "completed"],
                          [0.2, 0.3, 0.3, 0.2])[0]
        created_at = g.as_of - timedelta(days=r.randint(10, 60))
        approved_at = created_at + timedelta(days=r.randint(1, 5)) if status != "requested" else None

        test_orders.append({
            "test_order_id": f"TST-{test_order_count:06d}",
            "sku": sku,
            "style_id": style_id,
            "volume_units": r.randint(100, 1000),
            "status": status,
            "created_at": created_at,
            "approved_at": approved_at,
            "purpose": r.choice(["trend_validation", "demand_test", "market_test", "competitor_comparison"]),
        })

    return {
        "sample_requests": sample_requests,
        "sample_rounds": sample_rounds,
        "fit_comments": fit_comments,
        "launch_products": launch_products,
        "critical_path_milestones": critical_path_milestones,
        "launch_readiness_signals": launch_readiness_signals,
        "lead_times_category": lead_times_category,
        "test_orders": test_orders,
    }
