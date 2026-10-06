"""Generate contract, clause, breach and negotiation data."""
import json
from datetime import datetime, timedelta

def generate(g):
    """Generate contracts and related data."""
    r = g.rng

    contracts = []
    clauses = []
    breaches = []
    disputes = []
    cases = []
    rate_cards = []
    price_lists = []
    alerts = []
    positions = []
    drafts = []

    # Get master data
    suppliers = g.master("suppliers")
    carriers = g.master("carriers")
    customers = g.master("customers")

    # Generate contracts for suppliers
    for i, sup in enumerate(suppliers[:15]):  # 15 supplier contracts
        ctr_id = f"CTR-{i+1:06d}"
        start = g.date_between(730, 90)
        end = start + timedelta(days=365 * r.randint(1, 3))

        contracts.append({
            "contract_id": ctr_id,
            "contract_type": "supplier",
            "party_type": "supplier_id",
            "party_id": sup["supplier_id"],
            "owner_id": r.choice([e["employee_id"] for e in g.master("employees")[:10]]),
            "start_date": start,
            "end_date": end,
            "renewal_notice_days": r.choice([30, 60, 90]),
            "auto_renewal": r.choice([True, False]),
            "status": "active" if end >= g.as_of else "expired",
            "created_at": start - timedelta(days=r.randint(5, 30)),
            "updated_at": g.days_ago(r.randint(0, 60))
        })

        # Add clauses to each contract
        clause_types = ["payment_terms", "price_review", "renewal"]
        for j, ct in enumerate(clause_types):
            clauses.append({
                "contract_id": ctr_id,
                "clause_id": f"{ct}_{j}",
                "clause_type": ct,
                "title": f"{ct.replace('_', ' ').title()} Clause",
                "content": json.dumps({
                    "limit_gbp": 10000,
                    "penalty_gbp_per_unit": 5.0,
                    "notice_days": 30
                }),
                "created_at": start
            })

    # Generate contracts for carriers
    for i, car in enumerate(carriers[:8]):  # 8 carrier contracts
        ctr_id = f"CTR-{i+100:06d}"
        start = g.date_between(730, 90)
        end = start + timedelta(days=365 * r.randint(1, 3))

        contracts.append({
            "contract_id": ctr_id,
            "contract_type": "carrier",
            "party_type": "carrier_id",
            "party_id": car["carrier_id"],
            "owner_id": r.choice([e["employee_id"] for e in g.master("employees")[:10]]),
            "start_date": start,
            "end_date": end,
            "renewal_notice_days": 60,
            "auto_renewal": True,
            "status": "active" if end >= g.as_of else "expired",
            "created_at": start - timedelta(days=r.randint(5, 30)),
            "updated_at": g.days_ago(r.randint(0, 60))
        })

        # Add carrier clauses
        for j, ct in enumerate(["liability", "rate_review", "claim_window"]):
            clauses.append({
                "contract_id": ctr_id,
                "clause_id": f"{ct}_{j}",
                "clause_type": ct,
                "title": f"{ct.replace('_', ' ').title()} Clause",
                "content": json.dumps({
                    "limit_gbp": r.randint(5000, 50000),
                    "deductible_gbp": r.randint(500, 2000),
                    "subject_to_deductible": True,
                    "claim_window_days": r.choice([30, 60, 90])
                }),
                "created_at": start
            })

    # Generate some breaches for active contracts
    for i in range(5):
        ctr = r.choice(contracts)
        if ctr["status"] == "active":
            breaches.append({
                "breach_id": f"BRH-{i+1:06d}",
                "contract_id": ctr["contract_id"],
                "breach_date": g.days_ago(r.randint(1, 60)),
                "description": r.choice([
                    "Late delivery by 2 days",
                    "Incomplete shipment",
                    "Quality issue detected",
                    "Rate charged not per contract",
                    "Surcharge applied without notice"
                ]),
                "impact": r.choice([
                    "Store stockout", "Production delay", "Customer complaint", "Margin impact"
                ]),
                "status": r.choice(["logged", "under_review", "remediated"]),
                "created_at": g.days_ago(r.randint(1, 30)),
                "updated_at": g.days_ago(r.randint(0, 30))
            })

    # Generate disputes
    for i in range(3):
        ctr = r.choice(contracts)
        disputes.append({
            "dispute_id": f"DSP-{i+1:06d}",
            "contract_id": ctr["contract_id"],
            "account_id": ctr["party_id"],
            "dispute_type": r.choice(["penalty", "overcharge", "claim"]),
            "amount_gbp": float(r.randint(500, 5000)),
            "description": "Disputed charge - under review",
            "status": r.choice(["raised", "under_review"]),
            "created_at": g.days_ago(r.randint(1, 30)),
            "updated_at": g.days_ago(r.randint(0, 15))
        })

    # Generate negotiation cases
    for i in range(2):
        ctr = r.choice(contracts)
        cases.append({
            "case_id": f"NGT-{i+1:06d}",
            "contract_id": ctr["contract_id"],
            "case_type": r.choice(["renewal", "rate_review", "amendment"]),
            "description": r.choice([
                "Rate review - seek 5% discount",
                "Contract renewal negotiation",
                "Service level amendment"
            ]),
            "status": r.choice(["open", "in_progress"]),
            "opened_at": g.days_ago(r.randint(5, 30)),
            "closed_at": None
        })

    # Generate rate cards
    for i, car_contract in enumerate([c for c in contracts if c["contract_type"] == "carrier"][:5]):
        rate_cards.append({
            "rate_card_id": f"RTC-{i+1:06d}",
            "card_type": "carrier",
            "party_id": car_contract["party_id"],
            "contract_id": car_contract["contract_id"],
            "effective_from": car_contract["start_date"],
            "effective_to": car_contract["end_date"],
            "base_rate_gbp": float(r.uniform(2.0, 10.0)),
            "currency": "GBP",
            "surcharges_json": json.dumps({
                "fuel": r.uniform(0.1, 0.5),
                "distance": 0.05,
                "weight": 0.02
            }),
            "notice_period_days": 30,
            "status": "active",
            "created_at": car_contract["created_at"]
        })

    # Generate price lists
    for i, sup_contract in enumerate([c for c in contracts if c["contract_type"] == "supplier"][:5]):
        price_lists.append({
            "price_list_id": f"PRL-{i+1:06d}",
            "list_type": "supplier_costs",
            "contract_id": sup_contract["contract_id"],
            "party_id": sup_contract["party_id"],
            "effective_from": sup_contract["start_date"],
            "effective_to": sup_contract["end_date"],
            "list_currency": "GBP",
            "terms_json": json.dumps({
                "payment_terms_days": r.choice([30, 45, 60]),
                "moq_units": r.randint(100, 1000),
                "lead_time_days": r.randint(7, 90)
            }),
            "status": "active",
            "created_at": sup_contract["created_at"]
        })

    # Generate renewal alerts
    for i, ctr in enumerate(contracts[:5]):
        if ctr["status"] == "active":
            alert_date = ctr["end_date"] - timedelta(days=ctr["renewal_notice_days"])
            alerts.append({
                "alert_id": f"ALR-{i+1:06d}",
                "contract_id": ctr["contract_id"],
                "alert_date": alert_date,
                "status": "scheduled" if alert_date >= g.as_of else "triggered",
                "created_at": ctr["created_at"],
                "sent_at": None
            })

    # Generate negotiation positions
    for case in cases:
        positions.append({
            "position_id": f"POS-{len(positions)+1:06d}",
            "contract_id": case["contract_id"],
            "case_id": case["case_id"],
            "position_type": "offer",
            "terms": "5% rate reduction, volume commitment 50k units annually",
            "notes": "Initial ask before counterparty response",
            "recorded_at": case["opened_at"]
        })

    # Generate contract drafts
    for i in range(2):
        if r.choice([True, False]):
            party = r.choice(suppliers)
            party_id = party["supplier_id"]
        else:
            party = r.choice(carriers)
            party_id = party["carrier_id"]

        drafts.append({
            "draft_id": f"DRF-{i+1:06d}",
            "draft_type": r.choice(["new_supplier", "new_carrier", "renewal"]),
            "template_id": "TMT-001",
            "selected_clauses": json.dumps(["payment_terms", "price_review", "liability"]),
            "counterparty_id": party_id,
            "created_at": g.days_ago(r.randint(1, 30)),
            "status": "draft"
        })

    return {
        "contracts": contracts,
        "contract_clauses": clauses,
        "contract_breaches": breaches,
        "contract_disputes": disputes,
        "negotiation_cases": cases,
        "rate_cards": rate_cards,
        "price_lists": price_lists,
        "renewal_alerts": alerts,
        "contract_negotiation_positions": positions,
        "contract_drafts": drafts
    }
