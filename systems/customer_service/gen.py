"""Background customer service data: contacts, damage claims, complaints, and notification rules."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng

    # Get master orders to base contacts on
    orders = g.master("orders")
    products = g.master("products")

    # Create references for lookups
    sku_to_product = {p["sku"]: p for p in products}
    all_skus = [p["sku"] for p in products]
    glass_skus = [p["sku"] for p in products if p.get("category", "").lower() in ["glassware", "tableware"] or "glass" in p.get("name", "").lower()]
    # If no glass SKUs found by category, use kettle and small appliances
    if not glass_skus:
        glass_skus = [p["sku"] for p in products if "kettle" in p.get("name", "").lower() or "glass" in p.get("name", "").lower()]
    if not glass_skus:
        glass_skus = [p["sku"] for p in products if p.get("category", "").lower() == "small appliances"][:5]

    # All tables
    contacts = []
    damage_claims = []
    complaints = []
    notification_rules = []

    # Generate notification rules first
    rule_types = [
        ("missed_scan_alert", "Alert on missed tracking scans"),
        ("delivery_promise_alert", "Alert on missed delivery promises"),
        ("tracking_gap_alert", "Alert on tracking information gaps"),
    ]

    for idx, (rule_type, rule_name) in enumerate(rule_types):
        rule_id = f"NTF-{idx + 1:06d}"
        notification_rules.append({
            "rule_id": rule_id,
            "rule_name": rule_name,
            "rule_type": rule_type,
            "status": "inactive",  # Will be activated in seed data for story
            "enabled_at": None,
            "estimated_contacts_prevented": 0,
            "last_modified": g.as_of,
        })

    # Generate customer service contacts
    # Base contacts on orders from last 90 days
    contact_reasons = ["wismo", "damage", "complaint", "return", "other"]
    wismo_issues = ["Missed scan", "Delayed delivery", "Tracking gap", "Wrong tracking info", "No tracking update"]
    contact_types = ["email", "chat", "phone"]

    contact_id_counter = 0
    claim_id_counter = 0
    complaint_id_counter = 0

    for order in orders:
        order_date = datetime.fromisoformat(order["order_date"])
        days_since = (g.as_of - order_date.date()).days

        # Only generate contacts for recent orders (within 60 days)
        if not 0 <= days_since <= 60:
            continue

        # ~5-8% of orders generate a customer service contact
        if r.random() > 0.07:
            continue

        # Generate 1-3 contacts per order that does have an issue
        num_contacts = r.randint(1, 3) if r.random() > 0.7 else 1

        for _ in range(num_contacts):
            contact_id_counter += 1
            contact_id = f"CSC-{contact_id_counter:06d}"

            # Most are WISMO (70%), then damage (15%), complaint (10%), other (5%)
            if r.random() < 0.70:
                reason = "wismo"
                issue = r.choice(wismo_issues)
            elif r.random() < 0.15:
                reason = "damage"
                issue = "Item arrived damaged"
            elif r.random() < 0.10:
                reason = "complaint"
                issue = "Product quality issue"
            else:
                reason = "return"
                issue = "Return inquiry"

            # Contact date is 2-14 days after order (when they notice the issue)
            days_after_order = r.randint(2, 14)
            contact_dt = datetime.combine(order_date.date(), datetime.min.time()) + timedelta(days=days_after_order)
            contact_dt += timedelta(hours=r.randint(0, 23), minutes=r.randint(0, 59))

            # First response typically 1-48 hours
            response_hours = r.uniform(0.5, 48)

            status = r.choices(["resolved", "open", "escalated"], [0.85, 0.10, 0.05])[0]
            resolved_at = None
            if status == "resolved":
                resolved_at = contact_dt + timedelta(hours=response_hours + r.uniform(1, 72))

            contacts.append({
                "contact_id": contact_id,
                "contact_date": contact_dt,
                "order_id": order["order_id"],
                "reason": reason,
                "issue": issue,
                "contact_type": r.choice(contact_types),
                "status": status,
                "response_time_hours": round(response_hours, 1),
                "resolved_at": resolved_at,
            })

            # If damage reason, create a damage claim
            if reason == "damage":
                claim_id_counter += 1
                claim_id = f"CLM-{claim_id_counter:06d}"

                # Pick a random SKU, preferring glass/appliance items for damage claims
                sku = r.choice(glass_skus if glass_skus else all_skus)
                product = sku_to_product.get(sku, {})

                damage_types = ["Broken glass", "Dented packaging", "Water damage", "Torn seams", "Cracked item"]
                claim_amount = r.uniform(15, 150)

                damage_claims.append({
                    "claim_id": claim_id,
                    "order_id": order["order_id"],
                    "contact_id": contact_id,
                    "sku": sku,
                    "item_name": product.get("name", "Product"),
                    "damage_type": r.choice(damage_types),
                    "claim_amount_gbp": round(claim_amount, 2),
                    "claim_date": contact_dt,
                    "status": r.choices(["new", "investigating", "approved", "paid"], [0.3, 0.4, 0.2, 0.1])[0],
                })

            # If complaint reason, create a complaint
            if reason == "complaint":
                complaint_id_counter += 1
                complaint_id = f"CMP-{complaint_id_counter:06d}"

                # Pick a random SKU for complaints
                sku = r.choice(all_skus)
                product = sku_to_product.get(sku, {})

                defect_types = ["Zip strength", "Colour mismatch", "Fit issue", "Material quality", "Stitching defect"]
                severity_dist = r.choices(["low", "medium", "high", "critical"], [0.4, 0.35, 0.2, 0.05])[0]

                complaints.append({
                    "complaint_id": complaint_id,
                    "complaint_date": contact_dt,
                    "order_id": order["order_id"],
                    "contact_id": contact_id,
                    "sku": sku,
                    "defect_type": r.choice(defect_types),
                    "description": f"Customer reported {issue.lower()} with product.",
                    "severity": severity_dist,
                    "status": r.choices(["new", "investigating", "resolved"], [0.4, 0.4, 0.2])[0],
                })

    return {
        "customer_service_contacts": contacts,
        "damage_claims": damage_claims,
        "complaints": complaints,
        "notification_rules": notification_rules,
    }
