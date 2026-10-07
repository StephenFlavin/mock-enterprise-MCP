"""Carrier portal: rate cards, performance metrics, capacity and alerts."""
from datetime import datetime, timedelta, time
import random


def generate(g):
    r = g.rng

    # Get master data
    carriers = [c for c in g.master("carriers") if c["mode"] in ("road", "ocean")]
    road_carriers = [c for c in carriers if c["mode"] == "road"]
    ocean_carriers = [c for c in carriers if c["mode"] == "ocean"]

    # Define lanes
    road_lanes = [
        "Leeds-Manchester", "Leeds-Newcastle", "Manchester-London",
        "Newcastle-Birmingham", "Birmingham-London", "Manchester-Glasgow",
        "London-Southampton", "Bristol-London", "Liverpool-Manchester"
    ]

    ocean_lanes = [
        "Asia-Europe", "Asia-UK", "Far East-Europe", "China-UK",
        "Vietnam-Rotterdam", "Shanghai-Felixstowe"
    ]

    courier_regions = ["UK North", "UK South", "UK Midlands", "UK East", "Scotland"]
    courier_names = ["Courier Express", "ParcelMax", "Swift Delivery", "Regional Post"]

    # Containers for all tables
    rate_cards = []
    pallet_rates = []
    performance = []
    capacity_daily = []
    damage_claims = []
    alerts = []
    courier_capacity = []
    courier_cut_offs = []
    delivery_records = []
    capacity_requests = []
    disputes = []

    # Counter for IDs
    rc_count = 0
    pnr_count = 0
    perf_count = 0
    cap_count = 0
    claim_count = 0
    alert_count = 0
    cc_count = 0
    cco_count = 0
    dlv_count = 0
    req_count = 0
    dis_count = 0

    # 1. Generate road carrier rate cards
    for carrier in road_carriers[:5]:  # 5 road carriers
        for lane in road_lanes[:7]:  # 7 lanes
            for service in ["standard", "next_day", "express"]:
                rc_count += 1
                base_rate = r.uniform(0.5, 2.0)
                if service == "express":
                    base_rate *= 1.5
                elif service == "next_day":
                    base_rate *= 1.2

                rate_cards.append({
                    "rate_card_id": f"RC-{rc_count:06d}",
                    "carrier_id": carrier["carrier_id"],
                    "lane": lane,
                    "service_type": service,
                    "rate_gbp": round(base_rate, 2),
                    "min_volume": r.choice([0, 10, 50, 100]),
                    "effective_from": g.as_of - timedelta(days=r.randint(60, 180)),
                    "effective_to": g.as_of + timedelta(days=r.randint(60, 365)),
                    "status": "active" if r.random() > 0.1 else "expired"
                })

    # 2. Generate pallet network rates
    pallet_networks = ["Pallet Exchange", "National Pallet", "Euro Logistics"]
    for network in pallet_networks:
        for lane in road_lanes[:5]:
            for service in ["standard", "express"]:
                pnr_count += 1
                rate = round(r.uniform(15.0, 60.0), 2)
                pallet_rates.append({
                    "pallet_rate_id": f"PNR-{pnr_count:06d}",
                    "network_name": network,
                    "lane": lane,
                    "service_type": service,
                    "rate_gbp": rate,
                    "on_time_pct": round(r.uniform(92.0, 99.0), 1),
                    "effective_from": g.as_of - timedelta(days=180),
                    "contract_terms": f"Standard pallet ({network}) with {service} service. 48h notice for cancellation."
                })

    # 3. Generate carrier performance
    for carrier in carriers[:8]:
        lanes = ocean_lanes if carrier["mode"] == "ocean" else road_lanes
        for lane in lanes[:4]:
            perf_count += 1
            performance.append({
                "perf_id": f"CP-{perf_count:06d}",
                "carrier_id": carrier["carrier_id"],
                "lane": lane,
                "period": "last_12m",
                "reliability_pct": round(r.uniform(85.0, 98.0), 1),
                "on_time_pct": round(r.uniform(82.0, 97.0), 1),
                "roll_rate_pct": round(r.uniform(1.0, 18.0), 1),
                "damage_rate_pct": round(r.uniform(0.5, 4.5), 2),
                "volume_share_pct": round(r.uniform(10.0, 40.0), 1),
                "avg_eta_days": round(r.uniform(1.0 if "road" in carrier["mode"] else 14.0,
                                               2.5 if "road" in carrier["mode"] else 28.0), 1)
            })

    # 4. Generate daily capacity
    for carrier in road_carriers[:3]:
        for lane in road_lanes[:4]:
            for day_offset in range(0, 60, 7):  # Weekly for 60 days
                cap_count += 1
                total_cap = r.randint(100, 500)
                capacity_daily.append({
                    "capacity_id": f"CAP-{cap_count:06d}",
                    "carrier_id": carrier["carrier_id"],
                    "lane": lane,
                    "capacity_date": g.as_of + timedelta(days=day_offset),
                    "capacity_units": total_cap,
                    "available_units": r.randint(10, total_cap)
                })

    # 5. Generate damage claims
    for _ in range(15):
        claim_count += 1
        carrier = r.choice(carriers)
        lane = r.choice(ocean_lanes if carrier["mode"] == "ocean" else road_lanes)
        damage_claims.append({
            "claim_id": f"CLM-{claim_count + 900000:06d}",
            "carrier_id": carrier["carrier_id"],
            "lane": lane,
            "depot": r.choice(["Leeds DC", "Manchester Depot", "London Hub", "Glasgow Terminal"]),
            "sku": r.choice(["SKU-100234", "K-1700", "PF-220", "STY-5520", "SKU-100456"]),
            "package_type": r.choice(["carton", "polybag", "hanging"]),
            "claim_date": g.date_between(g.days_ago(90), g.as_of),
            "amount_gbp": round(r.uniform(50.0, 2000.0), 2),
            "status": r.choice(["filed", "accepted", "settled"]),
            "claim_notes": "Goods damaged in transit - " + r.choice(["crushed", "wet", "torn", "broken"])
        })

    # 6. Generate service alerts
    for carrier in carriers[:6]:
        # Blank sailings
        for _ in range(2):
            alert_count += 1
            alerts.append({
                "alert_id": f"ALR-{alert_count + 900000:06d}",
                "carrier_id": carrier["carrier_id"],
                "alert_type": "blank_sailing",
                "lane": r.choice(ocean_lanes if carrier["mode"] == "ocean" else road_lanes),
                "effective_from": g.as_of + timedelta(days=r.randint(5, 30)),
                "effective_to": None,
                "description": f"Blank sailing announced for {carrier['name']}",
                "amount_or_pct": None,
                "published_date": g.as_of - timedelta(days=r.randint(1, 14))
            })

        # Surcharges
        for _ in range(2):
            alert_count += 1
            alerts.append({
                "alert_id": f"ALR-{alert_count + 900000:06d}",
                "carrier_id": carrier["carrier_id"],
                "alert_type": "surcharge",
                "lane": r.choice(ocean_lanes if carrier["mode"] == "ocean" else road_lanes),
                "effective_from": g.as_of + timedelta(days=r.randint(1, 7)),
                "effective_to": g.as_of + timedelta(days=r.randint(60, 120)),
                "description": f"Fuel surcharge increase - {r.randint(5, 15)}%",
                "amount_or_pct": round(r.uniform(5.0, 15.0), 1),
                "published_date": g.as_of - timedelta(days=r.randint(1, 7))
            })

        # Rate increases
        for _ in range(1):
            alert_count += 1
            alerts.append({
                "alert_id": f"ALR-{alert_count + 900000:06d}",
                "carrier_id": carrier["carrier_id"],
                "alert_type": "rate_increase",
                "lane": None,
                "effective_from": g.as_of + timedelta(days=r.randint(30, 60)),
                "effective_to": None,
                "description": "General rate increase",
                "amount_or_pct": round(r.uniform(2.5, 8.0), 1),
                "published_date": g.as_of - timedelta(days=r.randint(10, 30))
            })

    # 7. Generate courier capacity commitments for peak
    for region in courier_regions:
        for courier in courier_names[:2]:
            cc_count += 1
            courier_capacity.append({
                "courier_capacity_id": f"CCP-{cc_count:06d}",
                "courier_name": courier,
                "region": region,
                "peak_capacity_units": r.randint(5000, 25000),
                "commitment_from": g.as_of + timedelta(days=r.randint(30, 60)),
                "commitment_to": g.as_of + timedelta(days=r.randint(70, 90))
            })

    # 8. Generate courier cut-off times
    for region in courier_regions:
        for courier in courier_names[:2]:
            cco_count += 1
            hour = r.randint(15, 18)
            minute = r.choice([0, 30])
            courier_cut_offs.append({
                "cut_off_id": f"CCO-{cco_count:06d}",
                "courier_name": courier,
                "region": region,
                "collection_time": f"{hour+2}:00",
                "cut_off_time": f"{hour}:{minute:02d}",
                "effective_from": g.as_of - timedelta(days=180)
            })

    # 9. Generate order delivery records
    orders = g.master("orders")
    for order in orders[:20]:
        dlv_count += 1
        eta = datetime.fromisoformat(order["order_date"]) + timedelta(days=r.randint(2, 7))
        ata = eta + timedelta(days=r.choice([-1, 0, 0, 0, 1, 2]))
        delivery_records.append({
            "delivery_id": f"DLV-{dlv_count:06d}",
            "order_id": order["order_id"],
            "carrier_id": r.choice([c["carrier_id"] for c in carriers[:5]]),
            "eta": eta.date(),
            "ata": ata.date() if order["status"] in ("shipped", "delivered") else None,
            "status": r.choice(["in_transit", "arrived", "delayed"]) if order["status"] in ("shipped", "delivered") else "in_transit",
            "delivery_notes": "" if r.random() > 0.1 else "Item delayed due to carrier disruption"
        })

    # 10. Generate capacity requests
    for carrier in road_carriers[:3]:
        for _ in range(2):
            req_count += 1
            capacity_requests.append({
                "request_id": f"REQ-{req_count:06d}",
                "carrier_id": carrier["carrier_id"],
                "lane": r.choice(road_lanes[:4]),
                "weeks_needed": f"weeks {r.randint(40, 52)}-{r.randint(45, 53)}",
                "units_requested": r.randint(200, 1000),
                "request_date": g.date_between(g.days_ago(30), g.as_of),
                "status": r.choice(["confirmed", "requested"])
            })

    # 11. Generate invoice disputes
    for carrier in carriers[:4]:
        for month_offset in range(-3, 0):
            dis_count += 1
            invoice_month = (datetime.fromisoformat(f"{g.as_of.year}-{g.as_of.month:02d}-01") + timedelta(days=30*month_offset)).strftime("%Y-%m")
            disputes.append({
                "dispute_id": f"DIS-{dis_count:06d}",
                "carrier_id": carrier["carrier_id"],
                "invoice_month": invoice_month,
                "dispute_reason": r.choice(["Surcharge not in contract", "Weight discrepancy", "Incorrect service level"]),
                "disputed_amount_gbp": round(r.uniform(100.0, 5000.0), 2),
                "status": r.choice(["submitted", "under_review"]),
                "submission_date": g.date_between(g.days_ago(30), g.as_of)
            })

    return {
        "carrier_rate_cards": rate_cards,
        "pallet_network_rates": pallet_rates,
        "carrier_performance": performance,
        "carrier_capacity_daily": capacity_daily,
        "damage_claims": damage_claims,
        "service_alerts": alerts,
        "courier_capacity_peak": courier_capacity,
        "courier_cut_offs": courier_cut_offs,
        "order_delivery_records": delivery_records,
        "capacity_requests": capacity_requests,
        "invoice_disputes": disputes
    }
