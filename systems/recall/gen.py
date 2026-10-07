"""Background recall data: incidents, recall cases, regulatory notifications and communications."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng

    # Get some SKUs for incidents (particularly hazmat ones like batteries, flammable items)
    hazmat_products = [p for p in g.master("products") if p.get("hazmat") and p["hazmat"] != "none"]
    if not hazmat_products:
        hazmat_products = g.master("products")[:20]

    incidents = []
    recall_cases = []
    regulatory_notifications = []
    store_instructions = []
    draft_communications = []
    incident_history = []

    # Generate 8-12 incidents over past 180 days
    for i in range(r.randint(8, 12)):
        product = r.choice(hazmat_products)
        sku = product["sku"]
        days_ago = r.randint(5, 180)
        reported_at = g.days_ago(days_ago)

        severity = r.choices(["minor", "moderate", "severe", "critical"], [40, 35, 20, 5])[0]
        status = r.choices(["open", "investigating", "resolved", "recalled"], [20, 30, 30, 20])[0]

        incident_id = f"INC-{len(incidents) + 1:06d}"
        incidents.append({
            "incident_id": incident_id,
            "sku": sku,
            "reported_at": reported_at,
            "customer_id": r.choice(g.master("customers"))["customer_id"],
            "description": r.choice([
                "Product overheating during normal use",
                "Battery swelling and potential fire risk",
                "Product failing under normal conditions",
                "Potential electrical hazard detected",
                "Component separation during use",
                "Smoke and burnt smell observed",
                "Damage from defective component",
                "Risk of injury from sharp edge",
            ]),
            "severity": severity,
            "status": status,
        })

    # Generate 3-5 recall cases (some from incidents, some standalone)
    countries_list = ["GB", "DE", "FR", "IT", "ES", "NL", "BE", "AT"]

    for i in range(r.randint(3, 5)):
        # Use an incident or random product
        if i < len(incidents) and r.random() > 0.3:
            incident = r.choice(incidents)
            incident_id = incident["incident_id"]
            sku = incident["sku"]
            reason = incident["description"]
        else:
            incident = r.choice(incidents)
            incident_id = incident["incident_id"]
            sku = incident["sku"]
            reason = incident["description"]

        days_ago = r.randint(1, 90)
        opened_at = g.days_ago(days_ago)

        # Pick a factory for this SKU
        factory = r.choice(g.master("factories"))

        recall_id = f"REC-{len(recall_cases) + 1:06d}"
        units_affected = r.choices([1000, 5000, 10000, 18000, 25000, 50000], [20, 25, 20, 15, 12, 8])[0]

        status = r.choices(["open", "approved", "in_progress", "closed", "withdrawn"], [15, 25, 35, 20, 5])[0]

        # Estimate costs: refunds + logistics + legal + comms
        products_for_sku = [p for p in g.master("products") if p["sku"] == sku]
        retail_price = float(products_for_sku[0]["retail_price_gbp"]) if products_for_sku else 35
        refund_cost = units_affected * retail_price
        logistics_cost = units_affected * r.choice([2, 2.5, 3, 3.5])
        legal_fees = r.choice([10000, 15000, 20000, 25000])
        comms_cost = r.choice([5000, 8000, 10000, 15000])

        total_cost = refund_cost + logistics_cost + legal_fees + comms_cost

        batch_id = f"{sku}-{g.as_of.strftime('%b').upper()}-{g.as_of.year}-{r.randint(1, 5):02d}"

        recall_cases.append({
            "recall_id": recall_id,
            "sku": sku,
            "incident_id": incident_id,
            "reason": reason,
            "batch_id": batch_id,
            "factory_id": factory["factory_id"],
            "status": status,
            "units_affected": units_affected,
            "cost_estimate_gbp": total_cost,
            "opened_at": opened_at,
            "updated_at": opened_at + timedelta(days=r.randint(1, 30)),
        })

    # Generate regulatory notifications for approved/in_progress recalls
    for recall in recall_cases:
        if recall["status"] in ["approved", "in_progress", "closed"]:
            # Notify 1-3 countries
            num_countries = r.randint(1, 3)
            for _ in range(num_countries):
                country = r.choice(countries_list)

                regulators = {
                    "GB": "Trading Standards Service",
                    "DE": "Produktüberwachung",
                    "FR": "DGCCRF",
                    "IT": "Ministero della Salute",
                    "ES": "Agencia de Seguridad",
                    "NL": "IGJ",
                    "BE": "SPF Santé",
                    "AT": "Bundesamt für Verbraucherschutz",
                }

                notif_id = f"RGN-{len(regulatory_notifications) + 1:06d}"
                sent_at = recall["opened_at"] + timedelta(days=r.randint(1, 7))

                # sent_at should be a datetime, but might be converted to date by timestamp handling
                if isinstance(sent_at, datetime):
                    deadline_date = sent_at.date() + timedelta(days=r.choice([5, 7, 10, 14]))
                else:
                    deadline_date = sent_at + timedelta(days=r.choice([5, 7, 10, 14]))

                regulatory_notifications.append({
                    "notification_id": notif_id,
                    "recall_id": recall["recall_id"],
                    "country": country,
                    "regulator": regulators.get(country, "Local Authority"),
                    "notification_type": "recall",
                    "status": r.choices(["draft", "submitted", "acknowledged"], [10, 45, 45])[0],
                    "sent_at": sent_at,
                    "deadline": deadline_date,
                    "content": f"Safety recall notification for {recall['sku']} batch {recall['batch_id']}. Reason: {recall['reason']}",
                    "updated_at": sent_at + timedelta(days=r.randint(0, 10)) if isinstance(sent_at, datetime) else datetime.combine(sent_at, datetime.min.time()) + timedelta(days=r.randint(0, 10)),
                })

    # Generate store instructions for in_progress recalls
    for recall in recall_cases:
        if recall["status"] in ["in_progress", "closed"]:
            instr_id = f"STI-{len(store_instructions) + 1:06d}"
            published_at = recall["opened_at"] + timedelta(days=r.randint(2, 10))

            store_instructions.append({
                "instruction_id": instr_id,
                "recall_id": recall["recall_id"],
                "sku": recall["sku"],
                "batch_id": recall["batch_id"],
                "action": r.choices(["pull", "quarantine", "destroy"], [50, 30, 20])[0],
                "status": r.choices(["published", "executed"], [40, 60])[0],
                "published_at": published_at,
                "content": f"Pull and quarantine {recall['sku']} batch {recall['batch_id']} from all stores. Reason: {recall['reason']}",
                "updated_at": published_at + timedelta(days=r.randint(1, 30)),
            })

    # Generate draft communications (some deleted)
    for recall in recall_cases:
        if recall["status"] in ["open", "approved", "in_progress"]:
            # Draft customer notice
            draft_id = f"DRF-{len(draft_communications) + 1:06d}"
            draft_communications.append({
                "draft_id": draft_id,
                "recall_id": recall["recall_id"],
                "communication_type": "customer_notice",
                "content": f"Customer notice for {recall['sku']} recall",
                "created_at": recall["opened_at"] + timedelta(days=1),
                "deleted_at": None,
                "status": "draft",
            })

            # Draft press statement (maybe deleted)
            if r.random() > 0.4:
                draft_id = f"DRF-{len(draft_communications) + 1:06d}"
                created = recall["opened_at"] + timedelta(days=2)
                draft_communications.append({
                    "draft_id": draft_id,
                    "recall_id": recall["recall_id"],
                    "communication_type": "press_statement",
                    "content": f"Press statement for {recall['sku']} safety recall",
                    "created_at": created,
                    "deleted_at": created + timedelta(hours=r.randint(1, 48)) if r.random() > 0.6 else None,
                    "status": "deleted" if r.random() > 0.6 else "draft",
                })

    # Generate incident history (aggregate view)
    seen_skus = set()
    for incident in incidents:
        if incident["sku"] not in seen_skus:
            seen_skus.add(incident["sku"])
            product = next((p for p in g.master("products") if p["sku"] == incident["sku"]), None)

            product_type = product["category"] if product else "Unknown"

            # Count incidents for this SKU
            sku_incidents = [i for i in incidents if i["sku"] == incident["sku"]]

            # Count recalls for this SKU
            sku_recalls = [r for r in recall_cases if r["sku"] == incident["sku"]]

            incident_history.append({
                "sku": incident["sku"],
                "reported_at": max(i["reported_at"] for i in sku_incidents),
                "product_type": product_type,
                "incident_count": len(sku_incidents),
                "most_common_issue": "Battery overheating" if "battery" in incident["description"].lower() else "Product defect",
                "previous_recalls": len([r for r in sku_recalls if r["status"] in ["approved", "in_progress", "closed"]]),
            })

    return {
        "incidents": incidents,
        "recall_cases": recall_cases,
        "regulatory_notifications": regulatory_notifications,
        "store_instructions": store_instructions,
        "draft_communications": draft_communications,
        "incident_history": incident_history,
    }
