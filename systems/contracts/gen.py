"""Contracts: one contract per active supplier, one per carrier, three racking-service contracts,
with clauses, rate cards and price lists derived from master data. Customer and franchise
contracts, breaches, disputes, cases, alerts and drafts live in seed/."""
import json
from datetime import timedelta

# ---------------------------------------------------------------------------------------------
# Story overrides (ids are master ids). Each entry replaces the generated clause of that type.
# ---------------------------------------------------------------------------------------------

# 01:4:Q4 supplier that short-ships against ASNs: tight claim window, 2% tolerance, credit-note remedy.
SUP_STORY = {
    "SUP-0013": {
        "claim_window": dict(shortage_claim_days=14, damage_claim_days=14, quality_claim_days=90,
                             summary="Shortage and damage claims must be notified within 14 days of goods receipt; quality claims within 90 days."),
        "short_shipment": dict(tolerance_pct=2.0, penalty_gbp_per_unit=0, remedy="credit note at invoice unit cost for units short beyond tolerance",
                               claim_basis="ASN quantity versus goods receipt quantity",
                               summary="Shortfalls beyond 2% of the ASN quantity are credited at invoice unit cost; no per-unit penalty."),
    },
    # 02:13:Q2 the three suppliers with the most avoidable air freight: three different chargeback positions.
    "SUP-0023": {
        "chargeback": dict(air_freight_recharge_pct=100, recharge_trigger="supplier-caused delay of more than 5 days against the confirmed ex-factory date",
                           quality_chargeback_pct=100,
                           summary="Supplier recharges 100% of the air freight cost when it ships more than 5 days late against the confirmed ex-factory date."),
        "penalty": dict(late_delivery_pct_per_week=1.5, cap_pct=10, max_penalty_gbp=57800,
                        summary="Late delivery penalty 1.5% of PO value per week, capped at 10%."),
    },
    "SUP-0022": {
        "chargeback": dict(air_freight_recharge_pct=50, recharge_trigger="supplier-caused delay of more than 10 days; recharge covers the excess of air over sea freight cost only",
                           quality_chargeback_pct=100,
                           summary="Supplier recharges 50% of the excess air freight cost when it is more than 10 days late."),
        "penalty": dict(late_delivery_pct_per_week=1.0, cap_pct=8, max_penalty_gbp=64300,
                        summary="Late delivery penalty 1% of PO value per week, capped at 8%."),
    },
    "SUP-0021": {
        "chargeback": dict(air_freight_recharge_pct=0, recharge_trigger="none: no air freight recharge in the contract",
                           quality_chargeback_pct=100,
                           summary="No air freight recharge clause; chargebacks cover quality failures only."),
        "penalty": dict(late_delivery_pct_per_week=0.5, cap_pct=5, max_penalty_gbp=109600,
                        summary="Late delivery penalty 0.5% of PO value per week, capped at 5%."),
    },
    # 04:32:Q1 Supplier A for the double-wall stainless bottle.
    "SUP-0004": {
        "price_review": dict(frequency="annual", max_increase_pct=3.0, trigger="stainless steel index move of more than 5% in a quarter", notice_days=60,
                             summary="Prices fixed for 12 months; one annual review capped at 3%, plus a steel-index adjustment if the index moves more than 5% in a quarter."),
        "payment_terms": dict(days=45, basis="from invoice date", early_payment_discount_pct=0,
                              summary="45 days from invoice date."),
    },
    # 04:32:Q7 largest cookware supplier, annual review.
    "SUP-0074": {
        "price_review": dict(frequency="annual", max_increase_pct=4.0, trigger="annual review; increases above 4% need documented cost evidence", notice_days=60,
                             summary="Annual price review capped at 4% without cost evidence; a larger rise needs an open-book cost breakdown."),
        "service_level": dict(otif_target_pct=95, measurement="on time and in full against the confirmed delivery date, per PO line", service_credit_pct=1.0,
                              summary="OTIF target 95% per PO line; 1% service credit on the late lines' value for each month below target."),
        "payment_terms": dict(days=30, basis="from invoice date", early_payment_discount_pct=0,
                              summary="30 days from invoice date."),
        "termination": dict(for_convenience_notice_days=90, for_cause_cure_days=30, exit_support_days=120,
                            summary="Either party may end the agreement for convenience on 90 days' notice; 30-day cure period for material breach."),
        "other": dict(topic="volume rebate", tiers=[{"annual_spend_gbp": 5000000, "rebate_pct": 1.0}, {"annual_spend_gbp": 7500000, "rebate_pct": 2.0}],
                      summary="Volume rebate: 1% of annual spend above GBP 5m, 2% above GBP 7.5m, paid quarterly in arrears."),
    },
    # 04:34:Q7 Portuguese nearshore supplier: priority capacity in return for a minimum commitment.
    "SUP-0044": {
        "volume_commitment": dict(min_annual_commitment_pct=90, take_or_pay_pct=50, capacity_reserved_pct=15, settlement="quarterly",
                                  summary="We commit to buy at least 90% of the agreed annual forecast; the supplier reserves 15% priority capacity. "
                                          "Any shortfall below the commitment is charged at 50% of unit price (take-or-pay), settled quarterly."),
        "force_majeure": dict(max_suspension_days=60, notice_hours=72,
                              summary="Force majeure suspends the commitment for up to 60 days; beyond that either party may terminate the volume commitment."),
        "termination": dict(for_convenience_notice_days=180, for_cause_cure_days=30,
                            summary="Termination for convenience on 180 days' notice; the commitment for the current year still applies."),
    },
}

# 04:32:Q1 price-list terms for Supplier A (SUP-0004) and 04:32:Q7 (SUP-0074)
PRICE_LIST_STORY = {
    "SUP-0004": dict(moq_units=5000, lead_time_days=75, price_validity_days=90, tooling_cost_gbp=24000, tooling_owner="buyer",
                     tooling_amortisation="supplier amortises tooling over the first 100,000 units; buyer owns the tools",
                     freight_terms="DDP delivered duty paid, carrier chosen by supplier", price_basis="ex-works price plus fixed freight per container"),
    "SUP-0074": dict(moq_units=2000, lead_time_days=60, price_validity_days=180, tooling_cost_gbp=0,
                     freight_terms="FOB", price_basis="FOB price list, reviewed annually"),
}

# 02:20:Q4 rate review: maximum annual increase (None = uncapped, market-linked) and month it takes effect.
RATE_REVIEW = {
    "CAR-001": (4.5, "January", 60), "CAR-002": (4.0, "January", 60), "CAR-003": (5.0, "January", 60),
    "CAR-004": (6.0, "April", 60), "CAR-005": (None, "quarterly", 30), "CAR-006": (None, "quarterly", 30),
    "CAR-007": (None, "quarterly", 30), "CAR-008": (None, "monthly", 14), "CAR-009": (None, "quarterly", 30),
    "CAR-010": (None, "quarterly", 30), "CAR-011": (9.0, "January", 30), "CAR-012": (8.5, "January", 30),
    "CAR-013": (7.5, "January", 30), "CAR-014": (6.5, "January", 30), "CAR-015": (4.0, "January", 60),
    "CAR-016": (5.0, "January", 60), "CAR-017": (4.0, "January", 60), "CAR-018": (None, "monthly", 14),
}

LIABILITY_BY_MODE = {  # limit_gbp, basis, deductible
    "road": (25000, "per consignment", 100), "ocean": (20000, "per container", 0), "air": (8000, "per consignment", 0),
    "forwarder": (10000, "per consignment", 0), "parcel": (100, "per parcel", 0), "rail": (12000, "per wagon", 0),
}
RATE_BY_MODE = {  # service_type, rate_unit, low, high
    "road": ("pallet", "per pallet", 15.5, 24.0), "ocean": ("40ft container", "per 40ft container", 1750, 2300),
    "air": ("air freight", "per kg", 3.4, 4.8), "forwarder": ("40ft container", "per 40ft container", 1800, 2400),
    "parcel": ("parcel", "per parcel", 3.2, 6.5), "rail": ("40ft container", "per 40ft container", 2400, 3100),
}
CARRIER_TERMS = {  # carrier_id -> overrides of the generated carrier clauses
    # 02:11:Q2 the three current road carriers on the northern lanes
    "CAR-001": {
        "service_level": dict(on_time_target_pct=95, measurement="delivery inside the booked window, per shipment", service_credit_pct_per_point=1.0,
                              summary="On-time target 95% inside the booked delivery window; 1% service credit on the month's invoices for each point below."),
        "volume_commitment": dict(min_annual_commitment_pct=70, shortfall_charge_pct=40, basis="annual pallets on contracted lanes",
                                  summary="We commit to 70% of the agreed annual pallet volume; a shortfall is charged at 40% of the contract rate."),
        "termination": dict(for_convenience_notice_days=60, summary="Termination for convenience on 60 days' notice."),
    },
    "CAR-002": {
        "service_level": dict(on_time_target_pct=92, measurement="delivery inside the booked window, per shipment", service_credit_pct_per_point=1.0,
                              summary="On-time target 92% inside the booked delivery window; 1% service credit for each point below, monthly."),
        "volume_commitment": dict(min_annual_commitment_pct=80, shortfall_charge_pct=50, basis="annual pallets on contracted lanes",
                                  summary="We commit to 80% of the agreed annual pallet volume; a shortfall is charged at 50% of the contract rate."),
        "termination": dict(for_convenience_notice_days=90, summary="Termination for convenience on 90 days' notice."),
        "claim_window": dict(damage_claim_days=7, shortage_claim_days=7, overcharge_claim_days=180,
                             summary="Damage and shortage claims within 7 days of delivery; invoice overcharges can be disputed within 180 days of the invoice date."),
    },
    "CAR-003": {
        "service_level": dict(on_time_target_pct=90, measurement="delivery inside the booked window, per shipment", service_credit_pct_per_point=0,
                              exit_trigger="on-time below 90% for two consecutive months",
                              summary="On-time target 90%; no service credits, but we may terminate if on-time is below 90% for two consecutive months."),
        "volume_commitment": dict(min_annual_commitment_pct=85, shortfall_charge_pct=60, basis="annual pallets on contracted lanes",
                                  summary="We commit to 85% of the agreed annual pallet volume; a shortfall is charged at 60% of the contract rate."),
        "termination": dict(for_convenience_notice_days=90, summary="Termination for convenience on 90 days' notice."),
    },
    # 02:20:Q5 Carrier B: low per-claim limit, polybag goods excluded
    "CAR-004": {
        "liability": dict(limit_gbp=400, limit_basis="per claim", deductible_gbp=50, subject_to_deductible=True,
                          excluded_package_types=["polybag"],
                          summary="Liability limited to GBP 400 per claim with a GBP 50 deductible; soft goods carried in polybags are excluded."),
        "claim_window": dict(damage_claim_days=30, shortage_claim_days=14, overcharge_claim_days=90,
                             summary="Damage claims within 30 days of delivery, shortages within 14 days, invoice overcharges within 90 days."),
    },
    # 02:12:Q2 Carrier A (forwarder, contract ends in January): reliability target but no roll penalty
    "CAR-010": {
        "service_level": dict(schedule_reliability_target_pct=80, measurement="vessel arrival within 2 days of the booked ETA", roll_penalty="none",
                              roll_rate_target_pct=None, remedy="quarterly review only",
                              summary="Schedule reliability target 80% (arrival within 2 days of booked ETA); no penalty or credit for rolled bookings, quarterly review only."),
        "renewal": dict(auto_renewal=True, renewal_term_months=12, notice_days=90,
                        summary="Renews automatically for 12 months unless either party gives 90 days' notice before expiry."),
        "termination": dict(for_convenience_notice_days=90, for_cause_cure_days=30,
                            summary="Termination for convenience on 90 days' notice; 30-day cure for material breach."),
        "volume_commitment": dict(min_annual_commitment_pct=75, shortfall_charge_pct=30, basis="annual 40ft containers on contracted lanes",
                                  summary="We commit to 75% of the agreed annual container volume; a shortfall is charged at 30% of the lane rate."),
    },
}
CARRIER_RATE_STORY = {
    # (carrier, service_type): (lane, unit, rate, surcharges)
    "CAR-001": [("pallet", "DC1 to UK North", "per pallet", 16.90,
                 dict(fuel_surcharge_cap_pct=12, tail_lift_gbp_per_drop=18, waiting_time_gbp_per_hour=42, waiting_free_minutes=60, redelivery_gbp=55))],
    "CAR-002": [("pallet", "DC1 to UK North", "per pallet", 17.20,
                 dict(fuel_surcharge_cap_pct=12, tail_lift_gbp_per_drop=18, waiting_time_gbp_per_hour=42, waiting_free_minutes=60,
                      redelivery_gbp=55, min_charge_gbp=35, weight_rule="rate covers up to 750kg per pallet; above that 1.25 x rate")),
                ("full load", "DC1 to UK North", "per load", 645.0,
                 dict(fuel_surcharge_cap_pct=12, waiting_time_gbp_per_hour=60, waiting_free_minutes=120, redelivery_gbp=120))],
    "CAR-003": [("pallet", "DC1 to UK North", "per pallet", 17.35,
                 dict(fuel_surcharge_cap_pct=10, tail_lift_gbp_per_drop=20, waiting_time_gbp_per_hour=45, waiting_free_minutes=45, redelivery_gbp=60))],
    "CAR-010": [("40ft container", "Vietnam to UK (Felixstowe)", "per 40ft container", 1890.0,
                 dict(bunker_adjustment="monthly, indexed", terminal_handling_gbp=215, documentation_gbp=45, roll_compensation_gbp=0)),
                ("40ft container", "Vietnam to Rotterdam", "per 40ft container", 1950.0,
                 dict(bunker_adjustment="monthly, indexed", terminal_handling_gbp=215, documentation_gbp=45, roll_compensation_gbp=0))],
}

# Racking inspection and maintenance service contracts (the provider is not a master entity, so it is held by name)
RACKING_SITES = {"DC1": "CTR-000501", "DC2": "CTR-000502", "DC3": "CTR-000503"}

# Suppliers whose contract has lapsed (their later purchase orders are off contract), outside the story categories
EXPIRED_SUPPLIERS = 4


def J(**kw):
    return json.dumps(kw)


def generate(g):
    r = g.rng
    as_of = g.as_of
    suppliers = sorted(g.master("suppliers"), key=lambda s: s["supplier_id"])
    carriers = sorted(g.master("carriers"), key=lambda c: c["carrier_id"])
    employees = g.master("employees")
    planners = [e["employee_id"] for e in employees if e["role"] == "Transport Planner"]
    wh_mgr = {e["site_id"]: e["employee_id"] for e in employees if e["role"] == "Warehouse Manager"}
    pos = g.master("purchase_orders")
    lines = g.master("po_lines")
    prods = {p["sku"]: p for p in g.master("products")}
    po_sup = {p["po_id"]: p["supplier_id"] for p in pos}
    first_po = {}
    for p in pos:
        first_po[p["supplier_id"]] = min(first_po.get(p["supplier_id"], p["order_date"]), p["order_date"])
    knit_suppliers = {po_sup[l["po_id"]] for l in lines if prods.get(l["sku"], {}).get("category") == "Knitwear"}
    story_suppliers = set(SUP_STORY) | {"SUP-0072"}

    contracts, clauses, rate_cards, price_lists = [], [], [], []

    def add_clauses(cid, start, spec):
        for ctype, (title, content) in spec.items():
            clauses.append({"contract_id": cid, "clause_id": f"{ctype}_1", "clause_type": ctype, "title": title,
                            "content": json.dumps(content), "created_at": start})

    # ------------------------------------------------------------------ supplier contracts
    eligible = [s for s in suppliers if s["supplier_id"] not in story_suppliers and s["supplier_id"] not in knit_suppliers
                and s["status"] != "exited"]
    expired = {s["supplier_id"] for s in r.sample(eligible, EXPIRED_SUPPLIERS)}

    for s in suppliers:
        sid = s["supplier_id"]
        n = int(sid[4:])
        cid = f"CTR-{n:06d}"
        pay = int(s["payment_terms_days"])
        spend = float(s["annual_spend_gbp"])
        onboarded = g.as_of.fromisoformat(s["onboarded_date"])
        start = min(onboarded, g.as_of.fromisoformat(first_po[sid]) - timedelta(days=14)) if sid in first_po else onboarded
        term = r.choice([2, 3, 3])
        notice = r.choice([30, 60, 90])
        auto = r.random() < 0.55
        status = "active"
        if s["status"] == "exited":
            status = "terminated"
            last = max((p["order_date"] for p in pos if p["supplier_id"] == sid), default=None)
            end = g.as_of.fromisoformat(last) + timedelta(days=10) if last else as_of - timedelta(days=120)
        elif sid in expired:
            status = "expired"
            end = as_of - timedelta(days=r.randint(30, 200))
            start = min(start, end - timedelta(days=365 * term))
        else:
            end = start + timedelta(days=365 * term)
            while end < as_of + timedelta(days=45):
                end += timedelta(days=365 * term)
        if sid == "SUP-0072":  # probation supplier trading with no signed contract: terms still being negotiated
            status, start, end = "draft", as_of + timedelta(days=21), as_of + timedelta(days=21 + 365 * 2)
        if sid == "SUP-0074":  # annual review is coming up: contract anniversary in the next weeks
            start = as_of - timedelta(days=365 * 2 - 6)
            end = start + timedelta(days=365 * 3)
            notice, auto = 90, True
        contracts.append({
            "contract_id": cid, "contract_type": "supplier", "party_type": "supplier_id", "party_id": sid,
            "party_name": s["name"], "title": f"Supply agreement - {s['name']}", "category": s["category_focus"], "site_id": None,
            "owner_id": s["account_manager_id"], "start_date": start, "end_date": end, "renewal_notice_days": notice,
            "auto_renewal": auto, "status": status, "annual_value_gbp": spend,
            "created_at": start - timedelta(days=r.randint(10, 40)), "updated_at": g.days_ago(r.randint(0, 90)),
        })
        tier = s["tier"]
        otif_t = {"strategic": 97, "preferred": 95}.get(tier, 92)
        cap_pct = r.choice([5, 8, 10])
        spec = {
            "payment_terms": ("Payment Terms", dict(days=pay, basis="from invoice date", early_payment_discount_pct=r.choice([0, 0, 1.5]),
                                                     summary=f"{pay} days from invoice date.")),
            "price_review": ("Price Review", dict(frequency="annual", max_increase_pct=r.choice([0, 2, 3, 5]), trigger="annual review or material cost index move over 5%",
                                                   notice_days=60, summary="Annual price review; increases capped and requiring 60 days' notice.")),
            "renewal": ("Renewal", dict(term_months=term * 12, auto_renewal=auto, renewal_term_months=12, notice_days=notice,
                                         summary=(f"Renews automatically for 12 months unless notice is given {notice} days before expiry." if auto
                                                  else f"Expires at the end of the term unless renewed in writing; {notice} days' notice to start renewal talks."))),
            "termination": ("Termination", dict(for_convenience_notice_days=r.choice([60, 90, 180]), for_cause_cure_days=30,
                                                 summary="Termination for convenience on notice; 30-day cure period for material breach.")),
            "force_majeure": ("Force Majeure", dict(max_suspension_days=r.choice([60, 90]), notice_hours=72,
                                                     summary="Force majeure suspends obligations; either party may terminate after the suspension limit.")),
            "liability": ("Supplier Liability", dict(limit_gbp=r.choice([250000, 500000, 1000000, 2000000]), limit_basis="per claim", deductible_gbp=0,
                                                     summary="Liability capped per claim; product safety and IP claims uncapped.")),
            "claim_window": ("Claim Window", (lambda sh: dict(shortage_claim_days=sh, damage_claim_days=sh, quality_claim_days=90,
                                                            summary=f"Shortage and damage claims within {sh} days of goods receipt; quality claims within 90 days."))(r.choice([14, 21, 30, 45]))),
            "short_shipment": ("Short Shipment", (lambda tol: dict(tolerance_pct=tol, penalty_gbp_per_unit=r.choice([1.0, 2.5, 5.0]),
                                                                    remedy="credit note at invoice unit cost for units short beyond tolerance",
                                                                    summary=f"Shortfalls beyond {tol}% of the ASN quantity are credited at invoice cost plus a per-unit penalty."))(r.choice([1, 2, 3, 5]))),
            "chargeback": ("Chargebacks", (lambda rc: dict(air_freight_recharge_pct=rc, recharge_trigger="supplier-caused delay of more than 7 days", quality_chargeback_pct=100,
                                                           summary=f"Supplier recharges {rc}% of air freight caused by its delays." if rc else "No air freight recharge; chargebacks cover quality failures only."))(r.choice([0, 50, 100] if tier != "strategic" else [50, 100]))),
            "penalty": ("Late Delivery Penalty", dict(late_delivery_pct_per_week=r.choice([0.5, 1.0, 1.5]), cap_pct=cap_pct, max_penalty_gbp=round(spend * cap_pct / 100),
                                                      summary=f"Late delivery penalty per week of delay, capped at {cap_pct}% of PO value.")),
            "service_level": ("Service Level", dict(otif_target_pct=otif_t, measurement="on time and in full against the confirmed delivery date", service_credit_pct=1.0,
                                                      summary=f"OTIF target {otif_t}%; service credits below target.")),
        }
        if r.random() < 0.3:
            own = r.choice(["buyer", "joint", "supplier"])
            spec["ip_protection"] = ("IP Protection", dict(ownership=own, summary=f"Designs and tooling developed jointly are owned by the {own}." if own != "joint" else "Jointly developed designs are jointly owned."))
        for ctype, ov in SUP_STORY.get(sid, {}).items():
            spec[ctype] = ({"chargeback": "Chargebacks", "penalty": "Late Delivery Penalty", "claim_window": "Claim Window",
                            "short_shipment": "Short Shipment", "price_review": "Price Review", "payment_terms": "Payment Terms",
                            "service_level": "Service Level", "termination": "Termination", "force_majeure": "Force Majeure",
                            "volume_commitment": "Volume Commitment", "other": "Volume Rebate"}[ctype], ov)
        if sid == "SUP-0044":
            spec["volume_commitment"] = ("Volume Commitment", SUP_STORY["SUP-0044"]["volume_commitment"])
        add_clauses(cid, start, {k: (v[0], {"summary": v[1].pop("summary"), **v[1]}) for k, v in spec.items()})

        terms = dict(payment_terms_days=pay, incoterm=s["incoterm"], moq_units=r.choice([300, 500, 1000, 2000, 5000]),
                     lead_time_days=r.choice([30, 45, 60, 75, 90]), price_validity_days=r.choice([90, 180]))
        terms |= PRICE_LIST_STORY.get(sid, {}) | ({"incoterm": s["incoterm"], "payment_terms_days": pay} if sid in PRICE_LIST_STORY else {})
        price_lists.append({
            "price_list_id": f"PRL-{n:06d}", "list_type": "supplier_costs", "contract_id": cid, "party_id": sid,
            "effective_from": start, "effective_to": end, "list_currency": s["currency"], "terms_json": json.dumps(terms),
            "status": "active" if status in ("active", "draft") else "superseded", "created_at": start,
        })

    # ------------------------------------------------------------------ carrier contracts
    for i, c in enumerate(carriers):
        cid_ = c["carrier_id"]
        n = int(cid_[4:])
        cid = f"CTR-{n + 99:06d}"
        mode = c["mode"]
        end = g.as_of.fromisoformat(c["contract_end"])
        start = end - timedelta(days=365 * 3)
        notice = 90 if mode in ("ocean", "forwarder", "air", "rail") else 60
        if cid_ in ("CAR-010", "CAR-009"):
            notice = 90
        status = "active"
        contracts.append({
            "contract_id": cid, "contract_type": "carrier", "party_type": "carrier_id", "party_id": cid_,
            "party_name": c["name"], "title": f"Transport agreement - {c['name']}", "category": f"{mode} - {c['scope']}", "site_id": None,
            "owner_id": planners[i % len(planners)], "start_date": start, "end_date": end, "renewal_notice_days": notice,
            "auto_renewal": cid_ != "CAR-003", "status": status,
            "annual_value_gbp": round(r.uniform(0.6, 4.5) * 1e6, -4),
            "created_at": start - timedelta(days=r.randint(10, 40)), "updated_at": g.days_ago(r.randint(0, 90)),
        })
        lim, basis, ded = LIABILITY_BY_MODE.get(mode, (10000, "per consignment", 0))
        mx, month, rnotice = RATE_REVIEW[cid_]
        spec = {
            "liability": ("Carrier Liability", dict(limit_gbp=lim, limit_basis=basis, deductible_gbp=ded, subject_to_deductible=ded > 0,
                                                     summary=f"Liability capped at GBP {lim:,} {basis}" + (f" with a GBP {ded} deductible." if ded else "."))),
            "rate_review": ("Rate Review", dict(review_frequency_months=12 if mx is not None else 3, max_increase_pct=mx, effective_month=month, notice_days=rnotice,
                                                 fuel_surcharge="indexed monthly to the published diesel / bunker index",
                                                 summary=(f"Rates may rise at most {mx}% a year, effective {month}, on {rnotice} days' notice; fuel surcharge indexed monthly."
                                                          if mx is not None else
                                                          f"Rates follow market index with {month} adjustments and {rnotice} days' notice; the increase is uncapped."))),
            "claim_window": ("Claim Window", dict(damage_claim_days=r.choice([14, 30]), shortage_claim_days=14, overcharge_claim_days=r.choice([90, 120]),
                                                   summary="Damage and shortage claims within 14-30 days of delivery; invoice overcharges within 90-120 days.")),
            "service_level": ("Service Level", dict(on_time_target_pct=r.choice([92, 94, 95]), measurement="delivery inside the booked window", service_credit_pct_per_point=1.0,
                                                      summary="On-time target with service credits for each point below.")),
            "termination": ("Termination", dict(for_convenience_notice_days=notice, summary=f"Termination for convenience on {notice} days' notice.")),
            "payment_terms": ("Payment Terms", dict(days=r.choice([30, 45]), basis="from invoice date", summary="Payment within the agreed days of invoice date.")),
            "renewal": ("Renewal", dict(auto_renewal=cid_ != "CAR-003", renewal_term_months=12, notice_days=notice,
                                         summary=f"Renews for 12 months unless notice is given {notice} days before expiry." if cid_ != "CAR-003"
                                         else f"Expires at the end of the term unless renewed in writing; {notice} days' notice to start renewal talks.")),
        }
        for ctype, ov in CARRIER_TERMS.get(cid_, {}).items():
            title = {"service_level": "Service Level", "volume_commitment": "Volume Commitment", "termination": "Termination", "claim_window": "Claim Window",
                     "liability": "Carrier Liability", "renewal": "Renewal"}[ctype]
            spec[ctype] = (title, ov)
        add_clauses(cid, start, {k: (v[0], {"summary": v[1].pop("summary"), **v[1]}) for k, v in spec.items()})

        cards = CARRIER_RATE_STORY.get(cid_)
        if not cards:
            stype, unit, lo, hi = RATE_BY_MODE.get(mode, ("pallet", "per pallet", 15.5, 24.0))
            rate = round(r.uniform(lo, hi), 2 if hi < 100 else 0)
            cards = [(stype, c["scope"], unit, rate, dict(fuel_surcharge_cap_pct=r.choice([8, 10, 12]), redelivery_gbp=r.choice([40, 55, 60])))]
        for j, (stype, lane, unit, rate, sur) in enumerate(cards):
            rate_cards.append({
                "rate_card_id": f"RTC-{n * 10 + j:06d}", "card_type": "freight_forwarder" if mode == "forwarder" else "carrier",
                "party_id": cid_, "contract_id": cid, "service_type": stype, "lane": lane, "rate_unit": unit,
                "effective_from": start, "effective_to": end, "base_rate_gbp": rate, "currency": "GBP",
                "surcharges_json": json.dumps(sur), "notice_period_days": rnotice, "status": "active", "created_at": start,
            })
    # CAR-002 previous rate card, superseded by the April increase (history for invoice checks)
    rate_cards.append({
        "rate_card_id": "RTC-001019", "card_type": "carrier", "party_id": "CAR-002", "contract_id": "CTR-000101", "service_type": "pallet",
        "lane": "DC1 to UK North", "rate_unit": "per pallet", "effective_from": as_of - timedelta(days=700), "effective_to": as_of - timedelta(days=200),
        "base_rate_gbp": 16.55, "currency": "GBP", "surcharges_json": json.dumps(dict(fuel_surcharge_cap_pct=12, tail_lift_gbp_per_drop=18)),
        "notice_period_days": 60, "status": "superseded", "created_at": as_of - timedelta(days=700),
    })

    # ------------------------------------------------------------------ racking service contracts (04:37:Q2)
    for site, cid in RACKING_SITES.items():
        start = as_of - timedelta(days=500)
        end = as_of + timedelta(days=230)
        contracts.append({
            "contract_id": cid, "contract_type": "service", "party_type": "service_provider", "party_id": None,
            "party_name": "Midlands Racking Services Ltd", "title": f"Racking inspection and maintenance - {site}", "category": "Racking inspection and maintenance",
            "site_id": site, "owner_id": wh_mgr[site], "start_date": start, "end_date": end, "renewal_notice_days": 90, "auto_renewal": True,
            "status": "active", "annual_value_gbp": {"DC1": 41000.0, "DC2": 36000.0, "DC3": 33000.0}[site],
            "created_at": start - timedelta(days=20), "updated_at": g.days_ago(30),
        })
        add_clauses(cid, start, {
            "termination": ("Termination", dict(for_convenience_notice_days=90, summary="Termination for convenience on 90 days' notice.")),
            "renewal": ("Renewal", dict(auto_renewal=True, renewal_term_months=12, notice_days=90,
                                         summary="Renews for 12 months unless notice is given 90 days before expiry.")),
            "service_level": ("Service Level", dict(report_within_days=10, remedial_visit_hours=48,
                                                     summary="Inspection report within 10 days; red-rated damage attended within 48 hours.")),
        })
        k = int(cid[-3:]) * 10
        rate_cards.append({
            "rate_card_id": f"RTC-{k:06d}", "card_type": "service", "party_id": None, "contract_id": cid, "service_type": "racking inspection",
            "lane": site, "rate_unit": "per inspector-day", "effective_from": start, "effective_to": end, "base_rate_gbp": 540.0, "currency": "GBP",
            "surcharges_json": json.dumps(dict(report_fee_gbp_per_site=150, out_of_hours_uplift_pct=25, min_visit_days=2, travel_gbp_per_visit=95)),
            "notice_period_days": 90, "status": "active", "created_at": start,
        })
        rate_cards.append({
            "rate_card_id": f"RTC-{k + 1:06d}", "card_type": "service", "party_id": None, "contract_id": cid, "service_type": "racking maintenance",
            "lane": site, "rate_unit": "per labour hour", "effective_from": start, "effective_to": end, "base_rate_gbp": 62.5, "currency": "GBP",
            "surcharges_json": json.dumps(dict(call_out_gbp=185, out_of_hours_uplift_pct=50, materials_markup_pct=12)),
            "notice_period_days": 90, "status": "active", "created_at": start,
        })

    return {
        "contracts": contracts,
        "contract_clauses": clauses,
        "rate_cards": rate_cards,
        "price_lists": price_lists,
    }
