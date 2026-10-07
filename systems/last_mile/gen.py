import datetime as dt

WEEKS_OF_DATA = 12

# city, country, region, postcode areas, weight
CITIES = [
    ("London", "GB", "London", ["N1", "N4", "N7", "N15", "N16", "NW1", "E1", "E8", "SE1", "SE15", "SW1", "SW9", "W1", "W6", "WC1"], 29),
    ("Manchester", "GB", "UK North", ["M1", "M4"], 7),
    ("Liverpool", "GB", "UK North", ["L1"], 4.5),
    ("Leeds", "GB", "UK North", ["LS1", "LS6"], 6),
    ("Sheffield", "GB", "UK North", ["S1"], 3),
    ("Newcastle", "GB", "UK North", ["NE1"], 3),
    ("Birmingham", "GB", "UK Midlands", ["B1", "B13"], 7),
    ("Nottingham", "GB", "UK Midlands", ["NG1"], 2.5),
    ("Leicester", "GB", "UK Midlands", ["LE1"], 2),
    ("Coventry", "GB", "UK Midlands", ["CV1"], 1.5),
    ("Bristol", "GB", "UK South", ["BS1"], 4.5),
    ("Brighton", "GB", "UK South", ["BN1"], 2.5),
    ("Southampton", "GB", "UK South", ["SO14"], 2.5),
    ("Reading", "GB", "UK South", ["RG1"], 2.5),
    ("Cardiff", "GB", "UK South", ["CF10"], 2.5),
    ("Glasgow", "GB", "Scotland", ["G1"], 4),
    ("Edinburgh", "GB", "Scotland", ["EH1"], 3),
]
EU_CITIES = {
    "IE": [("Dublin", "Ireland", ["IE-D01", "IE-D02"], 70), ("Cork", "Ireland", ["IE-T12"], 14),
           ("Galway", "Ireland", ["IE-H91"], 9), ("Limerick", "Ireland", ["IE-V94"], 7)],
    "NL": [("Amsterdam", "Netherlands", ["NL-1011", "NL-1012"], 50), ("Rotterdam", "Netherlands", ["NL-3011"], 25),
           ("Utrecht", "Netherlands", ["NL-3511"], 15), ("Eindhoven", "Netherlands", ["NL-5611"], 10)],
    "DE": [("Hamburg", "Germany", ["DE-20095"], 35), ("Munich", "Germany", ["DE-80331"], 30),
           ("Cologne", "Germany", ["DE-50667"], 20), ("Dusseldorf", "Germany", ["DE-40213"], 15)],
}

# Courier mix (courier_id -> weight) by region. CAR-011 SwiftParcel (Courier A), CAR-012 ParcelPoint Express (Courier B),
# CAR-013 DoorStep Couriers, CAR-014 ContinentalPost (EU only).
MIX = {
    "London": {"CAR-011": 65, "CAR-012": 15, "CAR-013": 20},
    "UK North": {"CAR-011": 25, "CAR-012": 25, "CAR-013": 50},
    "UK Midlands": {"CAR-011": 40, "CAR-012": 30, "CAR-013": 30},
    "UK South": {"CAR-011": 40, "CAR-012": 35, "CAR-013": 25},
    "Scotland": {"CAR-011": 50, "CAR-012": 50},
    "Ireland": {"CAR-012": 100},
    "Netherlands": {"CAR-014": 70, "CAR-012": 30},
    "Germany": {"CAR-014": 70, "CAR-012": 30},
}
# first-attempt lateness probability, damage, complaint, cost per drop (before region factor)
COURIER = {
    "CAR-011": dict(late=0.025, damage=0.009, complaint=0.014, cost=3.45),
    "CAR-012": dict(late=0.045, damage=0.018, complaint=0.020, cost=2.95),
    "CAR-013": dict(late=0.055, damage=0.013, complaint=0.026, cost=3.10),
    "CAR-014": dict(late=0.035, damage=0.010, complaint=0.015, cost=5.30),
}
REGION_COST = {"London": 1.12, "UK North": 0.98, "UK Midlands": 1.0, "UK South": 1.0, "Scotland": 1.15,
               "Ireland": 1.05, "Netherlands": 1.0, "Germany": 1.0}
SVC_DAYS = {"standard": 3, "next_day": 1, "same_day": 0}
OPTIONS = ["door", "safe_place", "locker", "collect_point"]
OPTION_W = [55, 20, 12, 13]
CUSTOMER_FAIL = {"door": 0.036, "safe_place": 0.012, "locker": 0.006, "collect_point": 0.004}
PLANT_PC_ISSUES = {"M4": 0.34, "L1": 0.24, "M1": 0.14}  # extra address-validation issue rate at full effect
EVENTS_OUT = ["Collected from depot", "Out for delivery"]


def weeks_back(as_of, d):
    """Calendar weeks between d and the latest full data week (0 = the week before as_of's week)."""
    monday = d - dt.timedelta(days=d.weekday())
    return (as_of - monday).days // 7 - 1


def ramp(wb):
    """Share of the late-period deterioration in effect, by weeks back from as_of (0 = latest week)."""
    return {0: 1.0, 1: 1.0, 2: 0.85, 3: 0.7, 4: 0.5, 5: 0.35, 6: 0.2, 7: 0.1}.get(wb, 0.0)


def add_days(d, n):
    d = d + dt.timedelta(days=n)
    while d.weekday() == 6:  # no Sunday deliveries
        d += dt.timedelta(days=1)
    return d


def wchoice(g, items, weights):
    return g.rng.choices(items, weights=weights, k=1)[0]


def generate(g):
    as_of = g.as_of
    last_day = as_of - dt.timedelta(days=2)  # latest delivery day (Saturday)
    first_day = as_of - dt.timedelta(weeks=WEEKS_OF_DATA)

    # ---- SKUs: PF-220 / K-1700 plus a spread of real products; some bulky cartons
    products = g.master("products")
    by_sku = {p["sku"]: p for p in products}
    storage = [p["sku"] for p in products if p["category"] == "Storage" and p["pack_type"] == "carton"][:2]
    lighting = [p["sku"] for p in products if p["category"] == "Lighting"][:2]
    base_skus = [p["sku"] for p in products if p["sku"].startswith("SKU-") and p["status"] == "active"]
    skus = ["PF-220", "K-1700"] + storage + lighting + g.rng.sample(base_skus, 24)
    sku_w = [14, 8] + [5] * 4 + [3] * 24
    sku_extra = {"PF-220": 0.20}  # lithium-battery fan: signature at the door, customer often out
    for s in storage:
        sku_extra[s] = 0.06
    assert all(s in by_sku for s in skus)

    # ---- city weights
    uk_w = [c[4] for c in CITIES]

    attempts, scans, issues, complaints = [], [], [], []
    n_att = n_scan = n_issue = n_cmp = 0

    orders = [o for o in g.master("orders")
              if o["country"] in ("GB", "IE", "NL", "DE") and o["status"] != "cancelled"
              and o["delivery_service"] in SVC_DAYS and o["order_date"] >= first_day.isoformat()]

    for o in orders:
        oid, country, svc = o["order_id"], o["country"], o["delivery_service"]
        odate = dt.date.fromisoformat(o["order_date"])
        if country == "GB":
            city, _, region, pcs, _ = wchoice(g, CITIES, uk_w)
            pc = g.pick(pcs)
        else:
            lst = EU_CITIES[country]
            city, region, pcs, _ = wchoice(g, lst, [x[3] for x in lst])
            pc = g.pick(pcs)
        mix = MIX[region]
        courier = wchoice(g, list(mix), list(mix.values()))
        cp = COURIER[courier]
        sku = wchoice(g, skus, sku_w)
        option = wchoice(g, OPTIONS, OPTION_W)
        promised = add_days(odate, SVC_DAYS[svc])
        north13 = courier == "CAR-013" and region == "UK North"
        c13 = courier == "CAR-013"

        # address validation at checkout (deterioration in planted postcodes)
        wb_p = max(weeks_back(as_of, promised), 0)
        fp = ramp(wb_p)
        p_issue = 0.02 + fp * PLANT_PC_ISSUES.get(pc, 0.0)
        had_issue = g.rng.random() < p_issue
        if had_issue:
            n_issue += 1
            issues.append({
                "issue_id": f"AVI-{n_issue:06d}", "order_id": oid, "postcode_area": pc,
                "issue_type": wchoice(g, ["no_match", "partial_match", "invalid_postcode", "ambiguous", "undeliverable"],
                                      [30, 30, 12, 24, 4] if pc in PLANT_PC_ISSUES and fp > 0.3 else [18, 40, 18, 22, 2]),
                "validation_timestamp": dt.datetime.combine(odate, dt.time(10, g.rng.randint(0, 59))),
                "resolved": g.rng.random() < (0.35 if pc in PLANT_PC_ISSUES else 0.7),
            })

        # first attempt date (late = slips 1-2 days)
        att_date = promised
        p_late = cp["late"] + fp * (0.20 if north13 else 0.03 if c13 else 0.012)
        if g.rng.random() < p_late:
            att_date = add_days(promised, g.rng.randint(1, 2))
        num = 0
        prev_failed = False
        while True:
            num += 1
            if att_date > last_day:
                break
            wb = weeks_back(as_of, att_date)
            f = ramp(wb)
            att_time = dt.datetime.combine(att_date, dt.time(g.rng.randint(9, 19), g.rng.randint(0, 59)))
            status, reason, addr, cust = "delivered", "", False, False
            if num == 1:
                p_addr = 0.008 + (0.40 if had_issue else 0.0)
                p_cust = CUSTOMER_FAIL[option] + f * (0.010 if option == "door" else 0.0) + (f * sku_extra.get(sku, 0.0) if option == "door" else 0.0)
                if sku == "PF-220":
                    p_cust += 0.008
                p_courier = 0.008 + f * (0.17 if north13 else 0.03 if c13 else 0.0)
                p_access = 0.010
                r = g.rng.random()
                if r < p_addr:
                    status, reason, addr = "failed", "Address not found", True
                elif r < p_addr + p_cust:
                    status, reason, cust = "failed", "Customer not available", True
                elif r < p_addr + p_cust + p_courier:
                    status, reason = "failed", "Courier ran out of time"
                elif r < p_addr + p_cust + p_courier + p_access:
                    status, reason = "failed", "Access issue (gated site or no safe place)"
            else:
                if g.rng.random() > 0.88:
                    status, reason = "failed", g.pick(["Customer not available", "Access issue (gated site or no safe place)"])
                    cust = reason.startswith("Customer")
            delivered = status == "delivered"
            late = att_date > promised
            damage = delivered and g.rng.random() < cp["damage"] * (1.0 + (0.35 if option == "door" else 0))
            p_c = cp["complaint"] + (0.08 if late else 0) + (0.45 if damage else 0) + (0.03 if not delivered else 0)
            complaint = g.rng.random() < p_c

            # tracking scans: collected, out for delivery, delivered/failed (missed scans drop events)
            p_miss = 0.015 + f * (0.30 if north13 else 0.06 if c13 else 0.01)
            events = [EVENTS_OUT[0], EVENTS_OUT[1], "Delivered" if delivered else "Delivery attempted - not delivered"]
            if g.rng.random() < p_miss:
                events.pop(1 if g.rng.random() < 0.8 else 2)
            lat_late = g.rng.random() < (f * 0.65 if north13 else f * 0.06 if c13 else f * 0.02)
            latency = g.rng.uniform(8, 22) if lat_late else g.rng.uniform(0.1, 1.6)
            n_att += 1
            aid = f"ATT-{n_att:06d}"
            for i, ev in enumerate(events, 1):
                final = ev in ("Delivered", "Delivery attempted - not delivered")
                at = att_time + dt.timedelta(hours=latency) if final else (
                    att_time - dt.timedelta(hours=14 if ev == EVENTS_OUT[0] else 5, minutes=g.rng.randint(0, 40)))
                n_scan += 1
                scans.append({"attempt_id": aid, "scan_number": i, "scanned_at": at,
                              "location": "Depot" if ev == EVENTS_OUT[0] else "On vehicle" if ev == EVENTS_OUT[1] else f"{city} drop",
                              "event": ev})
            cost = round(cp["cost"] * REGION_COST[region] * g.rng.uniform(0.88, 1.12), 2)
            attempts.append({
                "attempt_id": aid, "order_id": oid, "courier_id": courier, "sku": sku, "postcode_area": pc,
                "city": city, "country": country, "region": region,
                "delivery_service": svc, "delivery_option": option, "attempt_number": num,
                "promised_delivery_date": promised, "actual_delivery_date": att_date if delivered else None,
                "attempt_time": att_time, "delivery_time": att_time if delivered else None,
                "status": status, "failure_reason": reason, "address_issue": addr, "customer_availability": cust,
                "damage_reported": damage, "complaint_raised": complaint, "has_tracking_scans": len(events),
                "cost_gbp": cost, "updated_at": att_time,
            })
            if complaint:
                n_cmp += 1
                complaints.append({
                    "complaint_id": f"CMPLT-{n_cmp:06d}", "order_id": oid, "courier_id": courier,
                    "complaint_date": att_time + dt.timedelta(hours=g.rng.randint(1, 30)),
                    "issue_type": "Damaged parcel" if damage else "Missed delivery" if not delivered else
                    "Late delivery" if late else "Tracking not updated" if len(events) < 3 else "Other",
                    "resolved": g.rng.random() < 0.7,
                })
            if delivered:
                break
            if num >= 3:
                break
            att_date = add_days(att_date, 1)

    # ---- couriers + regional peak capacity (parcels per week)
    daily = daily_performance(g)
    last_week = {}
    for r in daily:
        if r["peak_season"] != "last_peak":
            continue
        wk = r["perf_date"] - dt.timedelta(days=r["perf_date"].weekday())
        last_week[(r["region"], wk)] = last_week.get((r["region"], wk), 0) + r["parcels"]
    peak_week = {}
    for (region, wk), v in last_week.items():
        peak_week[region] = max(peak_week.get(region, 0), v)
    # capacity vs last peak's busiest week: tight in UK North and Scotland
    cap_factor = {"London": 1.18, "UK South": 1.12, "UK Midlands": 1.08, "UK North": 0.90, "Scotland": 0.86}
    cap_rows = []
    for region, pw in peak_week.items():
        mix = MIX[region]
        tot = sum(mix.values())
        for cid, w in mix.items():
            cap_rows.append({"courier_id": cid, "region": region,
                             "peak_weekly_capacity": int(round(pw * cap_factor[region] * w / tot, -1))})
    master_car = {c["carrier_id"]: c for c in g.master("carriers")}
    ratings = {"CAR-011": 4.4, "CAR-012": 4.1, "CAR-013": 3.7, "CAR-014": 4.2}
    prim = {"CAR-011": "London", "CAR-012": "London", "CAR-013": "UK North", "CAR-014": "Germany"}
    couriers = []
    for cid in ["CAR-011", "CAR-012", "CAR-013", "CAR-014"]:
        m = master_car[cid]
        weekly = sum(r["peak_weekly_capacity"] for r in cap_rows if r["courier_id"] == cid)
        couriers.append({"courier_id": cid, "name": m["name"], "mode": m["mode"], "scope": m["scope"],
                         "region": prim[cid], "peak_capacity_units_month": int(weekly * 4.3) if weekly else 4000,
                         "rating": ratings[cid], "contract_end": m["contract_end"]})

    return {
        "delivery_attempts": attempts, "delivery_scans": scans, "address_validation_issues": issues,
        "delivery_complaints": complaints, "couriers": couriers, "courier_region_capacity": cap_rows,
        "daily_performance": daily,
    }


def daily_performance(g):
    """Daily parcel rollups for the two most recent peak seasons (Nov-Dec)."""
    base_daily = {"London": 32, "UK North": 25, "UK South": 24, "UK Midlands": 15, "Scotland": 8}
    base_on_time = {"London": 0.935, "UK South": 0.915, "UK Midlands": 0.905, "UK North": 0.89, "Scotland": 0.875}
    stress = {"London": 0.7, "UK South": 1.0, "UK Midlands": 1.1, "UK North": 1.5, "Scotland": 1.6}
    week_ramp = [1.2, 1.3, 1.5, 2.4, 2.8, 2.6, 3.0, 2.2]
    dow = {0: 1.15, 1: 1.0, 2: 0.95, 3: 0.95, 4: 1.05, 5: 0.6}
    seasons = {
        "last_peak": (dt.date(2025, 11, 3), 1.0, {dt.date(2025, 11, 28): 0.09, dt.date(2025, 12, 1): 0.17,
                                                  dt.date(2025, 12, 2): 0.08, dt.date(2025, 12, 15): 0.12,
                                                  dt.date(2025, 12, 22): 0.15, dt.date(2025, 12, 23): 0.10}),
        "prior_peak": (dt.date(2024, 11, 4), 0.86, {dt.date(2024, 11, 29): 0.06, dt.date(2024, 12, 2): 0.09,
                                                    dt.date(2024, 12, 16): 0.07, dt.date(2024, 12, 23): 0.08}),
    }
    out = []
    for season, (start, scale, spikes) in seasons.items():
        for i in range(8 * 7):
            d = start + dt.timedelta(days=i)
            if d.weekday() == 6 or d.month == 12 and d.day in (25, 26):
                continue
            ramp_v = week_ramp[i // 7]
            for region, mix in MIX.items():
                if region not in base_daily:
                    continue
                tot = sum(mix.values())
                for cid, w in mix.items():
                    parcels = base_daily[region] * ramp_v * dow[d.weekday()] * scale * w / tot
                    parcels = max(1, int(round(parcels * g.rng.uniform(0.93, 1.07))))
                    on_time = base_on_time[region] - 0.035 * (ramp_v - 1.0) * stress[region] * (1.0 if season == "last_peak" else 0.7)
                    on_time -= spikes.get(d, 0.0) * stress[region]
                    if cid == "CAR-013":
                        on_time -= 0.03 * (ramp_v - 1.0) / 1.0 * (1.0 if season == "last_peak" else 0.6)
                    on_time = min(0.985, max(0.40, on_time + g.rng.uniform(-0.015, 0.015)))
                    ontime_n = int(round(parcels * on_time))
                    failed = int(round(parcels * (0.065 + 0.4 * (1 - on_time - 0.08) * 0.5 + g.rng.uniform(-0.01, 0.01))))
                    out.append({"perf_date": d, "courier_id": cid, "region": region, "parcels": parcels,
                                "delivered_on_time": ontime_n, "delivered_late": parcels - ontime_n,
                                "failed_first_attempt": max(0, min(failed, parcels)), "peak_season": season})
    return out
