"""Sourcing and RFQ data: RFQs, responses, awards and tender events."""
from datetime import datetime, time, timedelta


def generate(g):
    r = g.rng
    products = g.master("products")[:100]
    suppliers = g.master("suppliers")
    factories = g.master("factories")
    carriers = [c for c in g.master("carriers") if c["mode"] in ("ocean", "road")]

    rfqs = []
    rfq_responses = []
    rfx_events = []
    rfx_responses = []
    scorecard_templates = []
    sourcing_awards = []
    rfq_clarifications = []

    # Generate RFQs for products
    for i, prod in enumerate(products[:30]):
        rfq_id = f"RFQ-{i+1:06d}"
        req_date = g.as_of + timedelta(days=r.randint(30, 90))
        rfqs.append({
            "rfq_id": rfq_id,
            "sku": prod["sku"],
            "required_qty": r.choice([50000, 100000, 150000, 200000]),
            "destination_site_id": r.choice(["DC1", "DC2", "DC3"]),
            "required_date": req_date,
            "specification": f"{prod['name']} - {prod['size']} - Quality: {prod['category']}",
            "status": r.choice(["draft", "sent", "responses_received", "evaluated"]),
            "created_at": g.days_ago(r.randint(7, 30)),
            "sent_at": g.days_ago(r.randint(3, 25)) if r.random() > 0.3 else None,
            "updated_at": g.days_ago(r.randint(0, 20))
        })

        # Generate responses for each RFQ
        num_responses = r.choice([2, 3, 4])
        for j in range(num_responses):
            resp_id = f"RFR-{len(rfq_responses)+1:06d}"
            supplier = r.choice(suppliers)
            factory = next((f for f in factories if f["supplier_id"] == supplier["supplier_id"]), None)

            rfq_responses.append({
                "response_id": resp_id,
                "rfq_id": rfq_id,
                "supplier_id": supplier["supplier_id"],
                "status": r.choice(["submitted", "received", "evaluated", "accepted"]),
                "unit_cost_gbp": round(r.uniform(3, 20), 2),
                "total_cost_gbp": None,  # Calculated
                "lead_time_days": r.choice([30, 45, 60, 75, 90]),
                "minimum_order_qty": r.choice([10000, 25000, 50000]),
                "tooling_cost_gbp": r.choice([0, 500, 1000, 2500, 5000]) if r.random() > 0.6 else 0,
                "payment_terms": r.choice(["30 net", "60 net", "45 net"]),
                "quality_certification": r.choice(["ISO 9001", "OEKO-TEX", "GOTS", "None"]),
                "compliance_score": round(r.uniform(70, 100), 1),
                "capacity_units_available": r.randint(100000, 500000),
                "factory_id": factory["factory_id"] if factory else None,
                "submitted_at": g.days_ago(r.randint(0, 15)),
                "notes": f"Quote for {prod['sku']} delivery by {req_date}",
                "updated_at": g.days_ago(r.randint(0, 10))
            })

    # Generate RFX events for carrier tenders
    for i in range(5):
        rfx_id = f"RFX-{i+1:06d}"
        rfx_events.append({
            "rfx_id": rfx_id,
            "event_type": r.choice(["carrier_tender", "3pl_tender"]),
            "description": f"{'Ocean freight' if i < 3 else '3PL warehouse'} tender {2026 + i//2}",
            "status": r.choice(["draft", "invitation_sent", "responses_received", "evaluated"]),
            "criteria_template_id": f"TST-{i+1:06d}",
            "created_at": g.days_ago(r.randint(10, 40)),
            "invitation_sent_at": g.days_ago(r.randint(0, 30)) if r.random() > 0.4 else None,
            "response_deadline": g.as_of + timedelta(days=r.randint(10, 45)),
            "updated_at": g.days_ago(r.randint(0, 20))
        })

        # Generate responses for RFX
        num_rfx_responses = r.choice([2, 3, 4])
        for j in range(num_rfx_responses):
            carrier = r.choice(carriers)
            rfx_resp_id = f"RXR-{len(rfx_responses)+1:06d}"

            rfx_responses.append({
                "rfx_response_id": rfx_resp_id,
                "rfx_id": rfx_id,
                "supplier_id": carrier["carrier_id"],
                "status": r.choice(["submitted", "received", "evaluated", "accepted"]),
                "annual_cost_gbp": round(r.uniform(500000, 2000000), 2),
                "transition_cost_gbp": round(r.uniform(50000, 150000), 2),
                "service_level_commitment": r.choice([
                    "92% on-time delivery, 24hr response time",
                    "95% on-time delivery, 12hr response time",
                    "90% on-time delivery, 48hr response time"
                ]),
                "weighted_score": round(r.uniform(60, 95), 1) if r.random() > 0.3 else None,
                "submitted_at": g.days_ago(r.randint(0, 20)),
                "notes": f"Proposal for {['Ocean freight', '3PL service'][i % 2]} with service level guarantees",
                "updated_at": g.days_ago(r.randint(0, 15))
            })

    # Generate scorecard templates
    for i in range(5):
        tst_id = f"TST-{i+1:06d}"
        scorecard_templates.append({
            "template_id": tst_id,
            "name": r.choice([
                "Carrier Reliability 2026",
                "3PL Cost & Service",
                "Product Sourcing Evaluation",
                "Packaging Supplier",
                "Raw Materials"
            ]),
            "description": f"Scorecard for {'carrier' if i < 3 else 'supplier'} evaluation",
            "purpose": r.choice([
                "carrier reliability and cost",
                "3PL service quality and price",
                "product quality and lead time",
                "packaging sustainability",
                "material alternative sourcing"
            ]),
            "status": "approved" if r.random() > 0.3 else "draft",
            "created_at": g.days_ago(r.randint(30, 90)),
            "updated_at": g.days_ago(r.randint(0, 30))
        })

    # Generate scorecard criteria
    scorecard_criteria = []
    criteria_names = ["Price/Cost", "Quality/Compliance", "Delivery Performance", "Capacity", "Service Level", "Sustainability"]
    for tst_id in [f"TST-{i+1:06d}" for i in range(5)]:
        for idx, crit in enumerate(r.sample(criteria_names, 4)):
            scorecard_criteria.append({
                "template_id": tst_id,
                "criterion_id": f"C-{idx+1:03d}",
                "criterion_name": crit,
                "weight_pct": round(25.0 + r.uniform(-5, 5), 1),
                "description": f"{crit} evaluation criteria",
                "minimum_threshold": round(r.uniform(60, 80), 1)
            })

    # Generate sourcing awards
    for i, prod in enumerate(products[:15]):
        awd_id = f"AWD-{i+1:06d}"
        supplier = r.choice(suppliers)
        total_vol = r.choice([100000, 150000, 200000, 300000])

        sourcing_awards.append({
            "award_id": awd_id,
            "rfq_id": f"RFQ-{r.randint(1, 30):06d}",
            "supplier_id": supplier["supplier_id"],
            "sku": prod["sku"],
            "category": prod["category"],
            "volume_units": total_vol,
            "volume_split_pct": r.choice([50.0, 60.0, 70.0, 100.0]),
            "unit_cost_gbp": round(r.uniform(5, 25), 2),
            "status": r.choice(["draft", "approved", "active"]),
            "effective_date": g.as_of + timedelta(days=r.randint(30, 90)),
            "created_at": g.days_ago(r.randint(10, 40)),
            "updated_at": g.days_ago(r.randint(0, 20))
        })

    # Generate RFQ clarifications
    for i in range(8):
        rfc_id = f"RFC-{i+1:06d}"
        rfq_responses.append({
            "response_id": f"RFR-{r.randint(1, len(rfq_responses)):06d}"
        }) if i < len(rfq_responses) else None

        rfq_clarifications.append({
            "clarification_id": rfc_id,
            "rfq_id": f"RFQ-{r.randint(1, 30):06d}",
            "response_id": f"RFR-{r.randint(1, len(rfq_responses)):06d}" if r.random() > 0.3 else None,
            "question": r.choice([
                "Can you provide detailed cost breakdown?",
                "What is your capacity for Q3?",
                "Do you have ISO certifications?",
                "What are your payment terms?",
                "Can you meet the lead time requirement?"
            ]),
            "context": r.choice(["pricing", "capacity", "compliance", "terms", "lead_time"]),
            "status": r.choice(["sent", "answered", "closed"]),
            "sent_at": g.days_ago(r.randint(0, 15)),
            "answered_at": g.days_ago(r.randint(0, 10)) if r.random() > 0.4 else None,
            "answer": "Response provided as requested" if r.random() > 0.4 else None,
            "updated_at": g.days_ago(r.randint(0, 10))
        })

    return {
        "rfq": rfqs,
        "rfq_responses": rfq_responses,
        "rfx_events": rfx_events,
        "rfx_responses": rfx_responses,
        "tender_scorecard_templates": scorecard_templates,
        "scorecard_criteria": scorecard_criteria,
        "sourcing_awards": sourcing_awards,
        "rfq_clarifications": rfq_clarifications
    }
