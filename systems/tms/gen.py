"""Transport management system data: shipments, carriers, lanes, routes, performance, incidents."""
from datetime import date, datetime, timedelta, time


def generate(g):
    r = g.rng
    
    # Master data lookups
    sites = g.master("sites")
    carriers = g.master("carriers")
    orders = g.master("orders")
    purchase_orders = g.master("purchase_orders")
    
    # Extract DCs and stores
    dcs = [s for s in sites if s["type"] == "dc"]
    stores = [s for s in sites if s["type"] == "store"]
    road_carriers = [c for c in carriers if c["carrier_id"] in ("CAR-001", "CAR-002", "CAR-003")]
    parcel_carriers = [c for c in carriers if c["mode"] == "parcel"]
    ocean_carriers = [c for c in carriers if c["mode"] == "ocean"]
    air_carriers = [c for c in carriers if c["mode"] == "air"]
    
    # Lanes: DC1 serves every third UK store; DC3 (Leeds) serves the north and Scotland as a regional cross-dock.
    uk = [x for x in stores if x["country"] == "GB"]
    region = {x["site_id"]: x["region"] for x in uk}
    DISRUPT = ["DC1-ST214", "DC1-ST215"]                           # Glasgow / Dundee: Midshires slips in the last 2 weeks
    NORTH = ["DC1-ST150", "DC1-ST151", "DC1-ST148", "DC1-ST207"]   # Leeds, Manchester, Newcastle, Glasgow drops
    STORY = set(DISRUPT + NORTH)

    def lane_base(origin, dest):
        reg = region.get(dest, "UK South")
        if origin == "DC3":
            return {"UK North": 190, "Scotland": 390}.get(reg, 300)
        return {"UK Midlands": 190, "UK South": 260, "UK North": 330, "Scotland": 560}.get(reg, 260)

    lanes = [f"DC1-{x['site_id']}" for i, x in enumerate(uk) if i % 3 == 0]
    lanes += [f"DC3-{x['site_id']}" for x in uk if x["region"] in ("UK North", "Scotland")]
    lanes = [l for l in lanes if l not in STORY]
    all_lanes = lanes + sorted(STORY)
    shipments = []
    carriers_lanes = []
    carrier_performance = []
    carrier_incidents = []
    air_freight = []
    route_plans = []
    route_hours_breaches = []
    planned_stops = []
    allocation_scenarios = []
    transfer_scenarios = []
    postcodes = []
    reverse_logistics = []
    
    # Generate carriers_lanes (rate card per lane scales with distance; allocation sums to 100)
    ROAD3 = ["CAR-001", "CAR-002", "CAR-003"]
    for lane in all_lanes:
        origin, dest = lane.split("-")
        base = lane_base(origin, dest)
        cs = ROAD3 if lane in STORY else r.sample(ROAD3, 2)
        shares = [40.0, 35.0, 25.0] if lane in STORY else [70.0, 30.0]
        for cid, pct in zip(cs, shares):
            trip = float(round(base * {"CAR-001": 1.0, "CAR-002": 0.97, "CAR-003": 1.04}[cid]))
            big = lane in STORY
            carriers_lanes.append({
                "carrier_id": cid, "lane": lane, "mode": "road",
                "status": "active", "weekly_capacity_trips": int((6 if big else 2) * pct / 25) + 1,
                "weekly_capacity_pallets": int((85 if big else 20) * pct / 25) + (10 if big else 5),
                "rate_per_trip_gbp": trip, "rate_per_pallet_gbp": round(trip / 26 * 1.15, 1),
                "min_pieces": 5, "cutoff_hour": {"CAR-001": 17, "CAR-002": 16, "CAR-003": 15}[cid],
                "cutoff_day_offset": 1, "pct_allocation": pct, "updated_at": g.as_of})

    # Generate shipments
    for i in range(2400):
        lane = r.choice(lanes)
        origin, dest = lane.split("-")
        carrier = r.choice(road_carriers)

        planned_dep = g.date_between(90, -14)
        planned_arr = planned_dep + timedelta(days=r.randint(1, 5))
        is_past = planned_dep < g.as_of

        if is_past:
            delay = int(r.gauss(0, 0.7))
            actual_dep = planned_dep + timedelta(days=max(0, delay))
            actual_arr = planned_arr + timedelta(days=delay)
        else:
            actual_dep = None
            actual_arr = None

        is_split = False
        units = r.randint(100, 2000)
        pallets = max(1, units // 50)
        fill_rate = float(r.randint(60, 98))
        cost = float(round(lane_base(origin, dest) * r.uniform(0.85, 1.15)))

        shipments.append({
            "shipment_id": f"SHP-{len(shipments) + 1:06d}",
            "order_id": r.choice(orders)["order_id"] if r.random() < 0.7 else None,
            "po_id": None,
            "origin_site_id": origin,
            "dest_site_id": dest,
            "carrier_id": carrier["carrier_id"],
            "lane": lane,
            "mode": "road",
            "status": ("delivered" if actual_arr < g.as_of else "in_transit") if is_past else r.choice(["planned", "booked"]),
            "planned_departure": planned_dep,
            "actual_departure": actual_dep,
            "planned_arrival": planned_arr,
            "actual_arrival": actual_arr,
            "lines_count": r.randint(1, 20),
            "volume_cbm": float(r.randint(5, 25)),
            "weight_kg": float(r.randint(500, 5000)),
            "pallets": pallets,
            "cases": r.randint(10, 100),
            "units": units,
            "fill_rate_pct": fill_rate,
            "freight_cost_gbp": cost,
            "delay_minutes": (delay * 1440) if is_past and delay > 0 else None,
            "is_split": is_split,
            "created_at": g.fake.date_time_this_year(),
            "updated_at": g.fake.date_time_this_year()
        })

    # Parcel shipments for a quarter of the last 8 weeks of online orders; split orders rise sharply over the last 4 weeks.
    PARCEL = {"GB": ["CAR-011", "CAR-012", "CAR-013"], "IE": ["CAR-012"], "DE": ["CAR-014"], "NL": ["CAR-014"], "FR": ["CAR-014"], "US": ["CAR-015"]}
    SVC = {"standard": 4.6, "next_day": 7.4, "same_day": 11.5}
    ords = [o for o in orders if o["channel"] in ("web", "app", "marketplace") and o["status"] in ("delivered", "shipped", "returned", "part_returned")
            and date.fromisoformat(o["order_date"]) >= g.as_of - timedelta(days=56)]
    split_p = [0.03, 0.03, 0.03, 0.03, 0.05, 0.07, 0.09, 0.10]
    for k, o in enumerate(ords):
        if k % 4:
            continue
        od = date.fromisoformat(o["order_date"])
        wk = min(7, max(0, (od - (g.as_of - timedelta(days=56))).days // 7))
        svc = o["delivery_service"] if o["delivery_service"] in SVC else "standard"
        cid = r.choice(PARCEL.get(o["country"], ["CAR-012"]))
        if svc != "standard" and cid in ("CAR-013", "CAR-014", "CAR-015"):
            svc = "standard"
        units = int(o["units"])
        split = units >= 2 and r.random() < split_p[wk] * 2.2
        dep = od + timedelta(days=0 if svc != "standard" else 1)
        late = r.random() < {"CAR-011": 0.05, "CAR-012": 0.06, "CAR-013": 0.12, "CAR-014": 0.09, "CAR-015": 0.08}[cid]
        parts = [(o["fulfil_site_id"], (units + 1) // 2 if split else units, dep)]
        if split:
            parts.append(("DC1" if o["fulfil_site_id"] != "DC1" else "DC2", units // 2, dep + timedelta(days=1)))
        for origin, u, d_ in parts:
            transit = {"standard": 3, "next_day": 1, "same_day": 0}[svc] + (2 if o["country"] not in ("GB",) else 0)
            arr = d_ + timedelta(days=transit)
            dly = r.randint(1, 3) if late else 0
            cost = round(SVC[svc] * (1 + 0.1 * (u - 1)) * (1.9 if o["country"] in ("DE", "NL", "FR", "IE") else 3.4 if o["country"] == "US" else 1.0) * r.uniform(0.95, 1.05), 2)
            done = arr + timedelta(days=dly) < g.as_of
            shipments.append({
                "shipment_id": f"SHP-{len(shipments) + 1:06d}", "order_id": o["order_id"], "po_id": None,
                "origin_site_id": origin, "dest_site_id": None, "carrier_id": cid, "lane": f"{origin}-{o['country']}",
                "mode": "parcel", "service_level": svc, "status": "delivered" if done else "in_transit",
                "planned_departure": d_, "actual_departure": d_, "planned_arrival": arr,
                "actual_arrival": arr + timedelta(days=dly) if done else None,
                "lines_count": 1, "volume_cbm": round(0.02 * u, 2), "weight_kg": round(0.6 * u, 1), "pallets": 0, "cases": 1, "units": u,
                "fill_rate_pct": None, "freight_cost_gbp": cost,
                "delay_minutes": dly * 1440 if done else None, "is_split": split,
                "created_at": g.as_of, "updated_at": g.as_of})

    # Generate 2025 shipments for peak capacity analysis
    dc1_st214_lane = "DC1-ST214"
    for i in range(950):
        # Ensure some shipments are on DC1-ST214 lane for test
        lane = r.choice(sorted(STORY)) if i < 900 else r.choice(lanes)
        origin, dest = lane.split("-")
        carrier = r.choice(road_carriers)

        # Generate dates in December 2025 (past peak period)
        # kept inside days 6..34 of the window so a 5-week lookback from any of the next 7 weekdays sees every row (11:Q4-a)
        peak_date = g.as_of - timedelta(days=315) + timedelta(days=6 + r.randint(0, 34) % 29)
        planned_dep = peak_date
        planned_arr = planned_dep + timedelta(days=r.randint(1, 5))

        delay = int(r.gauss(0, 0.7))
        actual_dep = planned_dep + timedelta(days=max(0, delay))
        actual_arr = planned_arr + timedelta(days=delay)

        units = r.randint(100, 2000)
        pallets = max(1, units // 50)
        if i < 900:
            pallets = r.randint(18, 24)
            units = pallets * 50
        fill_rate = float(round(pallets / 26 * 100))
        cost = float(round(lane_base(origin, dest) * (0.45 + 0.55 * pallets / 26)))

        shipments.append({
            "shipment_id": f"SHP-{len(shipments) + 1:06d}",
            "order_id": r.choice(orders)["order_id"] if r.random() < 0.7 else None,
            "po_id": None,
            "origin_site_id": origin,
            "dest_site_id": dest,
            "carrier_id": carrier["carrier_id"],
            "lane": lane,
            "mode": "road",
            "status": "delivered",
            "planned_departure": planned_dep,
            "actual_departure": actual_dep,
            "planned_arrival": planned_arr,
            "actual_arrival": actual_arr,
            "lines_count": r.randint(1, 20),
            "volume_cbm": float(r.randint(5, 25)),
            "weight_kg": float(r.randint(500, 5000)),
            "pallets": pallets,
            "cases": r.randint(10, 100),
            "units": units,
            "fill_rate_pct": fill_rate,
            "freight_cost_gbp": cost,
            "delay_minutes": (delay * 1440) if delay > 0 else None,
            "is_split": False,
            "created_at": g.fake.date_time_this_year(),
            "updated_at": g.fake.date_time_this_year()
        })
    
    lane_fill = {}
    # Generate carrier_performance
    for lane in lanes[:100]:
        for carrier in r.sample([c for c in road_carriers if c["carrier_id"] in ("CAR-001","CAR-002","CAR-003")], min(2, len(road_carriers))):
            for week_offset in range(-12, 0):
                week_start = g.as_of + timedelta(weeks=week_offset)
                week_start = week_start - timedelta(days=week_start.weekday())
                week_end = week_start + timedelta(days=6)
                
                shipments_count = r.randint(5, 20)
                on_time_count = min(shipments_count, int(round(shipments_count * r.gauss(0.92, 0.03))))
                
                carrier_performance.append({
                    "carrier_id": carrier["carrier_id"],
                    "lane": lane,
                    "period_start": week_start.date() if isinstance(week_start, datetime) else week_start,
                    "period_end": week_end.date() if isinstance(week_end, datetime) else week_end,
                    "shipments_count": shipments_count,
                    "on_time_count": max(0, on_time_count),
                    "on_time_pct": round(100.0 * max(0, on_time_count) / shipments_count, 1),
                    "avg_delay_minutes": float(r.randint(-30, 120)) if r.random() < 0.3 else 0.0,
                    "fill_rate_avg_pct": float(round(lane_fill.setdefault(lane, r.randint(76, 90)) + r.randint(-2, 2))),
                    "total_cost_gbp": float(shipments_count * lane_base(*lane.split("-"))),
                    "cost_per_shipment_gbp": float(lane_base(*lane.split("-"))),
                    "updated_at": g.fake.date_time_this_year()
                })
    
    # Story: Midshires (CAR-002) service slips on Glasgow/Dundee lanes in the last 2 weeks; Northline stays strong.
    prof = {"CAR-001": (94, 88), "CAR-002": (90, 88), "CAR-003": (86, 84)}
    for lane in sorted(STORY):
        for cid, (ot, fr) in prof.items():
            for wk in range(-12, 0):
                ws = g.as_of + timedelta(weeks=wk)
                n = r.randint(4, 7)
                o, f = float(ot + r.randint(-2, 2)), float(fr + r.randint(-3, 3))
                if cid == "CAR-002" and wk >= -2 and lane in DISRUPT:
                    o, f = float(60 + r.randint(-4, 4)), float(62 + r.randint(-3, 3))
                elif lane in DISRUPT and wk >= -2:
                    f = f - 14.0
                if lane in DISRUPT and wk < -2:  # steady pre-disruption fill so the prior period reads the same however many weeks it spans (11:Q1-a)
                    f = {"CAR-001": 88.0, "CAR-002": 88.0, "CAR-003": 83.5}[cid]
                carrier_performance.append({
                    "carrier_id": cid, "lane": lane, "period_start": ws, "period_end": ws + timedelta(days=6),
                    "shipments_count": n, "on_time_count": round(n * o / 100), "on_time_pct": round(100 * round(n * o / 100) / n, 1),
                    "avg_delay_minutes": 140.0 if cid == "CAR-002" and wk >= -2 and lane in DISRUPT else 25.0,
                    "fill_rate_avg_pct": f, "total_cost_gbp": float(n * lane_base("DC1", lane.split("-")[1])), "cost_per_shipment_gbp": float(lane_base("DC1", lane.split("-")[1])),
                    "updated_at": g.as_of})
                late_n = n - round(n * o / 100)
                for k in range(n):
                    dep = ws + timedelta(days=k % 6)
                    late = k < late_n
                    dly = (r.randint(90, 240) if cid != "CAR-002" or wk < -2 or lane not in DISRUPT else r.randint(180, 420)) if late else 0
                    shipments.append({
                        "shipment_id": f"SHP-{len(shipments) + 1:06d}", "origin_site_id": "DC1", "dest_site_id": lane.split("-")[1],
                        "carrier_id": cid, "lane": lane, "mode": "road", "status": "delivered",
                        "planned_departure": dep, "actual_departure": dep, "planned_arrival": dep + timedelta(days=1),
                        "actual_arrival": dep + timedelta(days=1), "lines_count": r.randint(5, 15),
                        "volume_cbm": 15.0, "weight_kg": 2500.0, "pallets": max(1, round(f / 100 * 26)), "cases": 60, "units": 600,
                        "fill_rate_pct": f, "freight_cost_gbp": float(lane_base("DC1", lane.split("-")[1])), "delay_minutes": dly or None, "is_split": False,
                        "created_at": g.as_of, "updated_at": g.as_of})

    # Story (warehouse service level): Midshires (CAR-002) trailers left DC1 a day late on 4 in 10 loads over the last 3 weeks.
    for sh in shipments:
        if (sh["origin_site_id"] == "DC1" and sh["carrier_id"] == "CAR-002" and sh["mode"] == "road" and sh["status"] == "delivered"
                and sh["dest_site_id"] and sh["dest_site_id"].startswith("ST")
                and g.as_of - timedelta(days=21) <= sh["planned_departure"] < g.as_of and r.random() < 0.4):
            sh["actual_departure"] = sh["planned_departure"] + timedelta(days=1)
            sh["actual_arrival"] = sh["planned_arrival"] + timedelta(days=1)
            sh["delay_minutes"] = 1440
    for sh in shipments:
        if sh["status"] in ("planned", "booked"):
            sh["actual_departure"] = sh["actual_arrival"] = sh["delay_minutes"] = None
        elif sh["status"] == "in_transit":
            sh["actual_arrival"] = sh["delay_minutes"] = None

    # Generate carrier incidents
    for i in range(150):
        carrier = r.choice(road_carriers)
        incident_date = g.date_between(90, 1)
        
        incident_type = r.choice(["damage_claim", "loss_claim", "delay", "service_failure", "other"])
        claim_value = float(r.randint(50, 5000)) if incident_type in ["damage_claim", "loss_claim"] else 0.0
        
        carrier_incidents.append({
            "incident_id": f"INC-{i + 1:06d}",
            "carrier_id": carrier["carrier_id"],
            "lane": r.choice(lanes),
            "incident_type": incident_type,
            "incident_date": incident_date,
            "shipment_id": r.choice(shipments)["shipment_id"] if r.random() < 0.7 else None,
            "description": g.fake.sentence(),
            "claim_value_gbp": claim_value,
            "recovery_value_gbp": claim_value * float(r.uniform(0, 0.8)),
            "status": r.choice(["open", "resolved", "disputed"]),
            "extra_cost_gbp": float(r.randint(0, 2000)),
            "updated_at": g.fake.date_time_this_year()
        })
    
    # Inbound shipments mirror master.shipments (same PO, carrier, ports, dates); air ones also feed air_freight.
    pos = {p["po_id"]: p for p in g.master("purchase_orders")}
    lines = {}
    for l in g.master("po_lines"):
        lines.setdefault(l["po_id"], []).append(l)
    wt = {p["sku"]: float(p["weight_kg"] or 1) for p in g.master("products")}
    sup_of = {p["po_id"]: p["supplier_id"] for p in pos.values()}
    MODE = {"sea": "ocean", "air": "air", "road": "road", "rail": "rail"}
    RATE_KG = {"INNSA": 4.6, "VNSGN": 6.1, "BDCGP": 5.2, "CNSHA": 5.4, "CNNGB": 5.4, "CNYTN": 5.5, "TRMER": 2.9}
    d0 = g.as_of
    air_rows = []
    for m in g.master("shipments"):
        eta = date.fromisoformat(m["eta"])
        if m["po_id"] not in pos:
            continue
        is_air = m["mode"] == "air"
        if eta < d0 - timedelta(days=(365 if is_air else 130)):
            continue
        ls = lines.get(m["po_id"], [])
        units = sum(int(l["qty_ordered"]) for l in ls) or int(pos[m["po_id"]]["total_units"])
        kg = round(sum(int(l["qty_ordered"]) * wt.get(l["sku"], 1.0) for l in ls) * 1.1, 0) or units * 1.0
        if m["mode"] == "sea":
            cost = max(400.0, round(float(m["teu"] or 0.5) * 2400 * (1.0 if eta < d0 - timedelta(days=90) else 1.18), 2))
        elif is_air:
            cost = max(1200.0, round(kg * RATE_KG.get(m["origin_port"], 4.5) * r.uniform(0.9, 1.1), 2))
        elif m["mode"] == "rail":
            cost = 2700.0
        else:
            cost = float(r.randint(900, 1500))
        ata = date.fromisoformat(m["ata"]) if m["ata"] else None
        delivered = m["status"] == "delivered" and ata is not None
        sid = f"SHP-{len(shipments) + 1:06d}"
        shipments.append({
            "shipment_id": sid, "order_id": None, "po_id": m["po_id"],
            "origin_site_id": m["origin_port"], "dest_site_id": m["dest_port"], "carrier_id": m["carrier_id"],
            "lane": f"{m['origin_port']}-{m['dest_port']}", "mode": MODE[m["mode"]],
            "status": "delivered" if delivered else ("booked" if m["status"] == "booked" else "in_transit"),
            "planned_departure": date.fromisoformat(m["etd"]),
            "actual_departure": date.fromisoformat(m["atd"]) if m["atd"] else None,
            "planned_arrival": eta, "actual_arrival": ata if delivered else None,
            "lines_count": len(ls), "volume_cbm": float(round(units * 0.02, 1)), "weight_kg": float(kg),
            "pallets": max(1, int(kg // 400)), "cases": units // 12, "units": units,
            "fill_rate_pct": float(r.randint(60, 96)), "freight_cost_gbp": cost,
            "delay_minutes": max(0, (ata - eta).days) * 1440 if delivered else None,
            "is_split": False, "reason": None, "created_at": g.as_of, "updated_at": g.as_of})
        if is_air:
            air_rows.append((sid, m, units, kg, cost, ata))

    # air_freight: one row per air shipment, reasons and suppliers from the PO. Last 13 weeks total is scaled to about 420k.
    quarter = [x for x in air_rows if x[1]["eta"] >= str(d0 - timedelta(days=91))]
    qtot = sum(x[4] for x in quarter) or 1.0
    scale = 420000.0 / qtot
    sup_count = {}
    for x in quarter:
        sup_count[sup_of[x[1]["po_id"]]] = sup_count.get(sup_of[x[1]["po_id"]], 0) + 1
    top3 = sorted(sup_count, key=lambda k: -sup_count[k])[:3]
    sea_rolled = [s_ for s_ in shipments if s_["mode"] == "ocean" and s_["carrier_id"] in ("CAR-005", "CAR-006", "CAR-007")
                  and s_["planned_departure"] >= d0 - timedelta(days=130)]
    shp_by_id = {s_["shipment_id"]: s_ for s_ in shipments}
    for i, (sid, m, units, kg, cost, ata) in enumerate(air_rows):
        in_q = m["eta"] >= str(d0 - timedelta(days=91))
        sup = sup_of[m["po_id"]]
        if in_q:
            cost = round(cost * scale, 2)
            shp_by_id[sid]["freight_cost_gbp"] = cost
        rc = r.choices(["supplier_late", "stockout_recovery", "peak_overflow", "demand_forecast_lift", "expedite_order", "customer_request", "other"],
                       [30, 15, 10, 12, 13, 5, 5])[0]
        rolled = None
        if in_q and sup in top3 and r.random() < 0.8:
            rc = "supplier_late"
        elif rc == "other" and r.random() < 0.7 and sea_rolled:
            rc = "carrier_rolled"
        if in_q and i % 4 == 0 and sup not in top3:
            rc = "carrier_rolled"
        if rc == "carrier_rolled":
            rolled = r.choice(sea_rolled + [x_ for x_ in sea_rolled if x_["carrier_id"] == "CAR-006"] * 2)["shipment_id"]
        avoid = rc in ("supplier_late", "demand_forecast_lift") or (rc in ("stockout_recovery", "carrier_rolled") and r.random() < 0.5)
        air_freight.append({
            "air_shipment_id": f"AIR-{i + 1:06d}", "shipment_id": sid, "po_id": m["po_id"], "supplier_id": sup,
            "carrier_id": m["carrier_id"], "origin_site_id": m["origin_port"], "dest_site_id": pos[m["po_id"]]["dest_site_id"],
            "reason_code": rc, "reason_detail": rc.replace("_", " ").capitalize() + " on " + m["po_id"],
            "rolled_shipment_id": rolled, "planned_date": date.fromisoformat(m["eta"]), "actual_date": ata,
            "units": units, "weight_kg": float(kg), "cost_gbp": cost, "avoidable": avoid,
            "avoided_by": ({"supplier_late": "earlier supplier follow-up", "demand_forecast_lift": "better forecast",
                            "stockout_recovery": "earlier booking", "carrier_rolled": "earlier booking"}[rc] if avoid else None)})

    # Keep air rows out of the zones where a 90-day window ending on any of the next 7 days would cut or add them (13:Q2-a).
    for a_ in air_freight:
        if d0 - timedelta(days=90) <= a_["planned_date"] < d0 - timedelta(days=84):
            a_["planned_date"] = d0 - timedelta(days=91)
        elif d0 < a_["planned_date"] <= d0 + timedelta(days=6):
            a_["planned_date"] = d0 + timedelta(days=7)

    # Generate route_plans
    for i in range(200):
        route_date = g.date_between(30, -14)
        lane = r.choice(lanes)
        
        route_plans.append({
            "route_id": f"RTE-{i + 1:06d}",
            "date": route_date,
            "lane": lane,
            "carrier_id": r.choice(road_carriers)["carrier_id"],
            "vehicle_type": r.choice(["articulated", "7.5t", "3.5t", "parcel_van"]),
            "stops_count": r.randint(5, 30),
            "planned_hours": float(r.randint(8, 20)),
            "planned_utilisation_pct": float(r.randint(70, 96)),
            "status": r.choice(["planned", "completed"]) if route_date < g.as_of else "planned",
            "created_at": g.fake.date_time_this_year()
        })
    
    # Generate route_hours_breaches
    for i in range(40):
        route = r.choice(route_plans)
        route_hours_breaches.append({
            "breach_id": f"BRC-{i + 1:06d}",
            "route_id": route["route_id"],
            "driver_id": f"DRV-{r.randint(1, 500):05d}",
            "breach_type": r.choice(["daily_limit_exceeded", "weekly_limit_exceeded"]),
            "hours_breached": round(r.uniform(0.3, 1.4), 1),
            "status": r.choice(["reported", "remediated"]),
            "remediation": g.fake.sentence() if r.random() < 0.7 else None,
            "created_at": g.as_of
        })
    
    # Generate planned_stops with unique composite keys
    stop_id = 0
    for lane in lanes:
        if lane in ("DC3-ST151", "DC3-ST160", "DC3-ST161", "DC3-ST162"):
            continue                      # M62 drops are planted in seed/planned_stops.csv
        origin, dest = lane.split("-")
        planned_stops.append({
            "stop_id": f"STP-{stop_id:06d}",
            "lane": lane,
            "customer_or_store": dest,
            "stop_time_minutes": r.choice([25, 30, 30, 35, 40]),
            "frequency_per_week": float(r.randint(1, 5)),
            "source": "route planning history",
            "updated_at": g.fake.date_time_this_year()
        })
        stop_id += 1
    
    # Generate allocation_scenarios
    for i in range(25):
        allocation_scenarios.append({
            "scenario_id": f"SCN-{i + 1:06d}",
            "scenario_type": r.choice(["trial_allocation", "tender_award", "consolidation"]),
            "description": g.fake.sentence(),
            "lanes_affected": ",".join(r.sample(lanes, r.randint(2, 5))),
            "carriers_involved": ",".join([c["carrier_id"] for c in r.sample(road_carriers, r.randint(1, 3))]),
            "volume_units": r.randint(1000, 10000),
            "share_pct": r.choice([10, 20, 30, 40]),
            "total_cost_gbp": float(r.randint(5000, 30000)),
            "projected_on_time_pct": float(r.randint(85, 98)),
            "projected_fill_rate_pct": float(r.randint(75, 95)),
            "risk_rating": r.choice(["low", "medium", "high"]),
            "status": r.choice(["draft", "approved"]),
            "created_at": g.fake.date_time_this_year()
        })
    
    # Generate transfer_scenarios
    for i in range(20):
        from_dc = r.choice(dcs)["site_id"]
        to_dc = r.choice([dc for dc in dcs if dc["site_id"] != from_dc])
        
        transfer_scenarios.append({
            "transfer_id": f"TRN-{i + 1:06d}",
            "from_site_id": from_dc,
            "to_site_id": to_dc["site_id"],
            "sku": g.master("products")[r.randint(0, len(g.master("products")) - 1)]["sku"],
            "units": r.randint(100, 1000),
            "transport_cost_gbp": float(r.randint(200, 1500)),
            "is_benefit_calculated": r.choice([True, False]),
            "projected_benefit_gbp": float(r.randint(500, 5000)) if r.random() < 0.6 else 0.0,
            "status": r.choice(["planned", "completed"]),
            "created_at": g.fake.date_time_this_year()
        })
    
    # Next-day coverage by postcode area and parcel carrier (cost per drop rises with distance from Daventry)
    AREAS = [("B", "Midlands", 4.8), ("CV", "Midlands", 4.8), ("NN", "Midlands", 4.6), ("LE", "Midlands", 4.8), ("NG", "Midlands", 5.0),
             ("M", "North West", 5.9), ("L", "North West", 6.1), ("LS", "Yorkshire", 6.0), ("S", "Yorkshire", 5.8), ("NE", "North East", 6.8),
             ("G", "Scotland", 7.6), ("EH", "Scotland", 7.6), ("AB", "Scotland", 9.4), ("IV", "Highlands", 12.5), ("KW", "Highlands", 13.5),
             ("SW", "London", 5.2), ("E", "London", 5.2), ("SE", "London", 5.2), ("BN", "South East", 5.7), ("EX", "South West", 7.2),
             ("PL", "South West", 8.0), ("TR", "South West", 9.8), ("CF", "Wales", 6.9), ("LD", "Wales", 9.0)]
    pc = 0
    for area, reg, cost in AREAS:
        for cid in ("CAR-011", "CAR-012"):
            pc += 1
            ok = not (reg in ("Highlands",) or (cid == "CAR-012" and reg in ("Wales", "South West", "Scotland")))
            postcodes.append({"postcode_id": f"PC-{pc:06d}", "postcode": area, "region": reg, "carrier_id": cid,
                              "next_day_available": ok, "next_day_cost_gbp": round(cost * (1.0 if cid == "CAR-011" else 1.07), 2),
                              "standard_cost_gbp": round(cost * 0.62, 2), "coverage_from": g.as_of - timedelta(days=200),
                              "updated_at": g.as_of})

    # Reverse logistics by department: apparel is cheap to move and resells well; Electricals/Home are bulky.
    PROFILE = {"Womenswear": (900, 0.85, 3.2), "Menswear": (700, 0.95, 3.0), "Kids": (600, 1.1, 2.6), "Accessories": (300, 0.7, 4.4),
               "Beauty": (250, 1.5, 0.4), "Home": (350, 3.4, 5.5), "Electricals": (200, 4.1, 9.0)}
    for category, (units, cpu, resale) in PROFILE.items():
        for week in range(-13, 0):
            ps = g.as_of + timedelta(weeks=week)
            n = int(units * r.uniform(0.85, 1.15))
            u = round(cpu * r.uniform(0.95, 1.05), 2)
            reverse_logistics.append({
                "category": category, "period_start": ps, "period_end": ps + timedelta(days=6),
                "return_units": n, "transport_cost_gbp": round(n * u, 2), "cost_per_unit_gbp": u,
                "processing_cost_gbp": round(n * (1.2 if category != "Electricals" else 3.5), 2),
                "resale_value_gbp": round(n * resale * r.uniform(0.9, 1.1), 2), "updated_at": g.as_of})

    # shipment_lines: SKU lines of inbound shipments (from the PO lines), used to allocate freight to SKUs
    shipment_lines = []
    for sh in shipments:
        if sh.get("po_id") and sh["po_id"] in lines:
            for l in lines[sh["po_id"]]:
                shipment_lines.append({"shipment_id": sh["shipment_id"], "line_no": int(l["line_no"]), "sku": l["sku"],
                                       "units": int(l["qty_ordered"])})

    # lane_buffers: planning buffer (days) added to carrier transit times, one row per inbound lane
    lane_buffers = []
    for ln in sorted({sh["lane"] for sh in shipments if sh.get("po_id")}):
        mode = next(sh["mode"] for sh in shipments if sh["lane"] == ln and sh.get("po_id"))
        lane_buffers.append({"buffer_lane": ln, "planning_buffer_days": {"ocean": 2, "air": 1}.get(mode, 1),
                             "basis": "carrier published transit time", "updated_at": g.as_of})

    # node_dwell: weekly average dwell at UK ports; Felixstowe has built up over the last 5 weeks
    node_dwell = []
    for port in ("GBFXT", "GBSOU", "GBLGP"):
        for wk in range(-13, 0):
            ws = g.as_of + timedelta(weeks=wk)
            hrs = (62 if wk >= -5 else 34) if port == "GBFXT" else 30
            node_dwell.append({"node_type": "port", "node": port, "week_start": ws,
                               "visits": r.randint(18, 40), "avg_dwell_hours": round(hrs * r.uniform(0.93, 1.07), 1)})
    for dc in ("DC1", "DC2", "DC3"):
        for wk in range(-13, 0):
            node_dwell.append({"node_type": "dc", "node": dc, "week_start": g.as_of + timedelta(weeks=wk),
                               "visits": r.randint(150, 400), "avg_dwell_hours": round(r.uniform(4, 7), 1)})

    # freight_invoices: one invoice per carrier and week, summed from TMS cost; the last 4 weeks carry a 210k gap
    by = {}
    for sh in shipments:
        if sh.get("actual_departure") and sh["carrier_id"]:
            d = sh["actual_departure"]
            d = d.date() if isinstance(d, datetime) else d
            wk = d - timedelta(days=d.weekday())
            by[(sh["carrier_id"], wk)] = by.get((sh["carrier_id"], wk), 0.0) + sh["freight_cost_gbp"]
    freight_invoices = []
    first = g.as_of - timedelta(weeks=13)
    for (cid, wk), amt in sorted(by.items()):
        if wk < first or wk >= g.as_of:
            continue
        freight_invoices.append({"invoice_id": f"FINV-{len(freight_invoices) + 1:06d}", "carrier_id": cid, "week_start": wk,
                                 "amount_gbp": round(amt, 2), "gl_account": "5110", "posted_to_ledger": True})
    recent = sorted([x for x in freight_invoices if x["week_start"] >= g.as_of - timedelta(weeks=4)], key=lambda x: -x["amount_gbp"])
    gap, k = 0.0, 0
    for inv in recent:                      # first unposted (not accrued), then posted to the wrong account
        if gap + inv["amount_gbp"] <= 210000 and k < 6:
            inv["posted_to_ledger"] = False
            gap += inv["amount_gbp"]; k += 1
    for inv in recent:
        if inv["posted_to_ledger"] and inv["carrier_id"] in ("CAR-001", "CAR-002") and gap + inv["amount_gbp"] <= 210000:
            inv["gl_account"] = "5120"
            gap += inv["amount_gbp"]
    for inv in recent:                      # one short-billed invoice absorbs the remainder so the gap is exactly 210k
        if inv["posted_to_ledger"] and inv["gl_account"] == "5110" and inv["amount_gbp"] > 210000 - gap + 1000:
            inv["amount_gbp"] = round(inv["amount_gbp"] - (210000 - gap), 2)
            break

    return {
        "shipment_lines": shipment_lines, "lane_buffers": lane_buffers, "node_dwell": node_dwell, "freight_invoices": freight_invoices,
        "shipments": shipments,
        "carriers_lanes": carriers_lanes,
        "carrier_performance": carrier_performance,
        "carrier_incidents": carrier_incidents,
        "air_freight": air_freight,
        "route_plans": route_plans,
        "route_hours_breaches": route_hours_breaches,
        "planned_stops": planned_stops,
        "allocation_scenarios": allocation_scenarios,
        "postcodes": postcodes,
        "reverse_logistics": reverse_logistics
    }
