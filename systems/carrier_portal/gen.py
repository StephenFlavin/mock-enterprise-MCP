"""Carrier portal: rate cards, capacity and background claims, notices and disputes.

Story rows (ocean and pallet-network rates, performance, the carrier B claims surge, this week's disruptions,
blank sailings, surcharges, rate increases, courier commitments) are in seed/*.csv with 9xxxxx ids.
The background here never touches those scopes.
"""
from datetime import timedelta

ROAD = ["CAR-001", "CAR-002", "CAR-003"]
NEAR = ["DC1-ST148", "DC1-ST150", "DC1-ST151"]
FAR = ["DC1-ST207", "DC1-ST214", "DC1-ST215"]
NORTH = NEAR + FAR[:1]
SCOT = FAR[1:]
# GBP per pallet, as in the transport system's lane rates
RATE = {"CAR-001": (14.6, 24.8), "CAR-002": (14.2, 24.0), "CAR-003": (15.2, 25.7)}
TERMS = {
    "CAR-001": "Rate per pallet delivered; fuel surcharge indexed monthly to the diesel price; peak surcharge of 10% in weeks 47 to 52; collection cut-off 17:00.",
    "CAR-002": "Rate per pallet delivered; fuel surcharge capped at 5% of freight; peak surcharge of 12% in weeks 47 to 52; collection cut-off 16:00.",
    "CAR-003": "Rate per pallet delivered; flat 6% fuel surcharge; peak surcharge of 10% in weeks 47 to 52; collection cut-off 15:00.",
}


def generate(g):
    r = g.rng
    A = g.as_of
    products = [p for p in g.master("products") if p["sku"] not in ("K-1700", "PF-220")][:400]

    # Rate cards: current and superseded road rates on the six store lanes
    cards = []
    n = 0
    for car in ROAD:
        for lane in NORTH + SCOT:
            base = RATE[car][0 if lane in NEAR else 1]
            for service, mult in (("standard", 1.0), ("next_day", 1.2)):
                n += 1
                cards.append({"rate_card_id": f"RC-{n:06d}", "carrier_id": car, "lane": lane, "service_type": service,
                               "rate_gbp": round(base * mult, 2), "rate_unit": "per pallet", "min_volume": 0 if service == "standard" else 5,
                               "effective_from": A - timedelta(days=120), "effective_to": A + timedelta(days=245),
                               "status": "active", "contract_terms": TERMS[car]})
            n += 1
            cards.append({"rate_card_id": f"RC-{n:06d}", "carrier_id": car, "lane": lane, "service_type": "standard",
                           "rate_gbp": round(base * 0.96, 2), "rate_unit": "per pallet", "min_volume": 0,
                           "effective_from": A - timedelta(days=485), "effective_to": A - timedelta(days=121),
                           "status": "superseded", "contract_terms": TERMS[car]})

    # Daily parcel capacity from six weeks out to Christmas Eve (BF week = days 49-55, last two weeks before Christmas = days 67-80)
    cap = []
    n = 0
    spec = {  # carrier: (base, bf, december, flex) contracted weekday capacity; headroom fractions (base, bf, dec, last two weeks)
        "CAR-011": ((12000, 14000, 15000), (0.32, 0.18, 0.22, 0.15)),
        "CAR-012": ((15000, 17000, 18000), (0.30, 0.20, 0.24, 0.17)),
        "CAR-013": ((16000, 16000, 16000), (0.28, 0.12, 0.07, 0.02)),
    }
    for car, (caps, fr) in spec.items():
        for off in range(42, 81):
            day = A + timedelta(days=off)
            phase = 0 if off < 49 else 1 if off < 56 else 3 if off >= 67 else 2
            weekday_cap = caps[min(phase, 2)]
            wd = day.weekday()
            factor = 1.0 if wd < 5 else 0.7 if wd == 5 else 0.3
            total = int(round(weekday_cap * factor, -2))
            avail = int(round(total * (fr[phase] + r.uniform(-0.01, 0.01)), -1))
            n += 1
            cap.append({"capacity_id": f"CAP-{n:06d}", "carrier_id": car, "lane": "DC2-GB", "capacity_date": day,
                        "capacity_units": total, "available_units": max(avail, 0)})

    # Background damage claims on other carriers (carrier B's story is seeded)
    claims = []
    n = 0
    for _ in range(46):
        n += 1
        car = r.choice(["CAR-001", "CAR-001", "CAR-003", "CAR-003", "CAR-011", "CAR-012", "CAR-013"])
        prod = r.choice(products)
        if car in ROAD:
            lane = r.choice(NORTH + SCOT)
            site = r.choice(["DC1", "DC1", "DC3"])
            lane = lane.replace("DC1", site)
        else:
            lane, site = "DC2-GB", "DC2"
        price = float(prod["retail_price_gbp"])
        claims.append({"claim_id": f"CLM-{n:06d}", "carrier_id": car, "lane": lane, "site_id": site, "sku": prod["sku"],
                       "package_type": prod["pack_type"], "claim_date": g.date_between(175, 6), "amount_gbp": round(price * r.randint(1, 3), 2),
                       "status": r.choice(["submitted", "accepted", "settled", "settled", "rejected"]),
                       "submitted_date": None, "claim_notes": "Goods damaged in transit: " + r.choice(["crushed", "wet", "torn", "dented", "scuffed"])})
    for c in claims:
        c["submitted_date"] = c["claim_date"] + timedelta(days=3)

    # Old notices (all ended well before the windows the tools look at)
    alerts = []
    n = 0
    kinds = [("service_disruption", "Depot disruption: collections delayed, since recovered."),
             ("delay_notice", "Network delays on collections, since cleared."),
             ("surcharge", "Temporary fuel surcharge, now withdrawn."),
             ("blank_sailing", "Blank sailing, already past."),
             ("rate_increase", "Rate increase already in force.")]
    for _ in range(14):
        n += 1
        typ, text = r.choice(kinds)
        car = r.choice(ROAD + ["CAR-005", "CAR-006", "CAR-007", "CAR-011", "CAR-012"])
        ocean = car in ("CAR-005", "CAR-006", "CAR-007")
        start = r.randint(110, 330)
        alerts.append({"alert_id": f"ALR-{n:06d}", "carrier_id": car, "alert_type": typ,
                       "lane": "Asia-Europe" if ocean else r.choice(NORTH + SCOT) if car in ROAD else "DC2-GB",
                       "port_code": "NLRTM" if (ocean and typ == "blank_sailing") else None,
                       "effective_from": A - timedelta(days=start),
                       "effective_to": None if typ in ("blank_sailing", "rate_increase") else A - timedelta(days=start - r.randint(3, 40)),
                       "description": text, "amount_or_pct": round(r.uniform(2, 9), 1) if typ in ("surcharge", "rate_increase") else None,
                       "amount_unit": "pct" if typ in ("surcharge", "rate_increase") else "none",
                       "published_date": A - timedelta(days=start + r.randint(3, 20))})

    # Earlier invoice disputes
    disputes = []
    for i, car in enumerate(ROAD * 2, 1):
        end = r.randint(60, 300)
        disputes.append({"dispute_id": f"DIS-{i:06d}", "carrier_id": car, "period_from": A - timedelta(days=end + 30),
                         "period_to": A - timedelta(days=end),
                         "dispute_reason": r.choice(["Surcharge not in contract", "Weight discrepancy", "Incorrect service level charged"]),
                         "disputed_amount_gbp": round(r.uniform(150, 2200), 2), "status": r.choice(["resolved", "resolved", "rejected"]),
                         "submission_date": A - timedelta(days=end - 5)})

    # Delivery records for recent customer orders (parcel carriers)
    deliveries = []
    parcel = ["CAR-011", "CAR-012", "CAR-013"]
    for i, order in enumerate(g.master("orders")[:20], 1):
        eta = A - timedelta(days=r.randint(20, 90))
        ata = eta + timedelta(days=r.choice([-1, 0, 0, 0, 1, 2]))
        deliveries.append({"delivery_id": f"DLV-{i:06d}", "order_ref": order["order_id"], "carrier_id": r.choice(parcel), "lane": "DC2-GB", "eta": eta, "ata": ata,
                           "status": "arrived", "delivery_notes": ""})

    return {
        "carrier_rate_cards": cards,
        "pallet_network_rates": [],
        "carrier_performance": [],
        "carrier_damage_rates": [],
        "carrier_capacity_daily": cap,
        "damage_claims": claims,
        "service_alerts": alerts,
        "courier_capacity_peak": [],
        "courier_cut_offs": [],
        "order_delivery_records": deliveries,
        "capacity_requests": [],
        "invoice_disputes": disputes,
    }
