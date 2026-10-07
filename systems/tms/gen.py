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
    
    # Define lanes: DC to store
    lanes = []
    for dc in dcs[:3]:
        for store in stores[:50]:
            lanes.append(f"{dc['site_id']}-{store['site_id']}")
    
    STORY = {"DC1-ST214", "DC1-ST215", "DC1-ST001", "DC1-ST050", "DC1-ST100", "DC1-ST150"}
    all_lanes = lanes
    lanes = [l for l in all_lanes if l not in STORY]   # story lanes are fully planted from seed/story code
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
    
    # Generate carriers_lanes
    for lane in lanes:
        for carrier in r.sample(road_carriers, min(3, len(road_carriers))):
            carriers_lanes.append({
                "carrier_id": carrier["carrier_id"],
                "lane": lane,
                "mode": "road",
                "status": r.choice(["active", "active", "active", "paused"]),
                "weekly_capacity_trips": r.randint(5, 20),
                "weekly_capacity_pallets": r.randint(50, 200),
                "rate_per_trip_gbp": float(r.randint(120, 400)),
                "rate_per_pallet_gbp": float(r.randint(15, 40)),
                "min_pieces": r.randint(1, 10),
                "cutoff_hour": r.choice([8, 12, 16, 17]),
                "cutoff_day_offset": r.choice([0, 1, 1, 2]),
                "pct_allocation": float(r.randint(20, 80)),
                "updated_at": g.fake.date_time_this_year()
            })
    
    # Generate shipments
    for i in range(2400):
        lane = r.choice(lanes)
        origin, dest = lane.split("-")
        carrier = r.choice(road_carriers)

        planned_dep = g.date_between(90, -14)
        planned_arr = planned_dep + timedelta(days=r.randint(1, 5))
        is_past = planned_dep < g.as_of

        if is_past:
            delay = int(r.gauss(0, 1.5))
            actual_dep = planned_dep + timedelta(days=max(0, delay))
            actual_arr = planned_arr + timedelta(days=delay)
        else:
            actual_dep = None
            actual_arr = None

        is_split = r.random() < 0.12
        units = r.randint(100, 2000)
        pallets = max(1, units // 50)
        fill_rate = float(r.randint(60, 98))
        cost = float(r.randint(180, 800))

        shipments.append({
            "shipment_id": f"SHP-{len(shipments) + 1:06d}",
            "order_id": r.choice(orders)["order_id"] if r.random() < 0.7 else None,
            "po_id": None,
            "origin_site_id": origin,
            "dest_site_id": dest,
            "carrier_id": carrier["carrier_id"],
            "lane": lane,
            "mode": "road",
            "status": r.choice(["delivered", "delivered", "in_transit", "planned", "booked"]) if is_past else r.choice(["planned", "booked", "in_transit"]),
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

    # Generate parcel shipments
    for i in range(100):
        lane = r.choice(lanes)
        origin, dest = lane.split("-")
        carrier = r.choice(parcel_carriers) if parcel_carriers else r.choice(road_carriers)

        planned_dep = g.date_between(90, -14)
        planned_arr = planned_dep + timedelta(days=r.randint(1, 3))
        is_past = planned_dep < g.as_of

        if is_past:
            delay = int(r.gauss(0, 0.5))
            actual_dep = planned_dep + timedelta(days=max(0, delay))
            actual_arr = planned_arr + timedelta(days=delay)
        else:
            actual_dep = None
            actual_arr = None

        units = r.randint(10, 200)
        fill_rate = float(r.randint(50, 85))
        cost = float(r.randint(10, 150))

        shipments.append({
            "shipment_id": f"SHP-{len(shipments) + 1:06d}",
            "order_id": r.choice(orders)["order_id"] if r.random() < 0.8 else None,
            "po_id": None,
            "origin_site_id": origin,
            "dest_site_id": dest,
            "carrier_id": carrier["carrier_id"],
            "lane": lane,
            "mode": "parcel",
            "status": "delivered" if is_past else r.choice(["planned", "booked"]),
            "planned_departure": planned_dep,
            "actual_departure": actual_dep,
            "planned_arrival": planned_arr,
            "actual_arrival": actual_arr,
            "lines_count": 1,
            "volume_cbm": float(r.randint(1, 5)),
            "weight_kg": float(r.randint(10, 100)),
            "pallets": 0,
            "cases": r.randint(1, 10),
            "units": units,
            "fill_rate_pct": fill_rate,
            "freight_cost_gbp": cost,
            "delay_minutes": (delay * 1440) if is_past and delay > 0 else None,
            "is_split": False,
            "created_at": g.fake.date_time_this_year(),
            "updated_at": g.fake.date_time_this_year()
        })

    # Generate 2025 shipments for peak capacity analysis
    dc1_st214_lane = "DC1-ST214"
    for i in range(200):
        # Ensure some shipments are on DC1-ST214 lane for test
        lane = dc1_st214_lane if i < 100 else r.choice(lanes)
        origin, dest = lane.split("-")
        carrier = r.choice(road_carriers)

        # Generate dates in December 2025 (past peak period)
        peak_date = datetime(2025, 12, r.randint(1, 31)).date()
        planned_dep = peak_date
        planned_arr = planned_dep + timedelta(days=r.randint(1, 5))

        delay = int(r.gauss(0, 1.5))
        actual_dep = planned_dep + timedelta(days=max(0, delay))
        actual_arr = planned_arr + timedelta(days=delay)

        units = r.randint(100, 2000)
        pallets = max(1, units // 50)
        fill_rate = float(r.randint(80, 98))
        cost = float(r.randint(200, 800))

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
    
    # Generate carrier_performance
    for lane in lanes[:100]:
        for carrier in r.sample([c for c in road_carriers if c["carrier_id"] in ("CAR-001","CAR-002","CAR-003")], min(2, len(road_carriers))):
            for week_offset in range(-12, 2):
                week_start = g.as_of + timedelta(weeks=week_offset)
                week_start = week_start - timedelta(days=week_start.weekday())
                week_end = week_start + timedelta(days=6)
                
                shipments_count = r.randint(5, 20)
                on_time_count = int(shipments_count * r.gauss(0.92, 0.05))
                
                carrier_performance.append({
                    "carrier_id": carrier["carrier_id"],
                    "lane": lane,
                    "period_start": week_start.date() if isinstance(week_start, datetime) else week_start,
                    "period_end": week_end.date() if isinstance(week_end, datetime) else week_end,
                    "shipments_count": shipments_count,
                    "on_time_count": max(0, on_time_count),
                    "on_time_pct": float(max(0, min(100, r.gauss(90, 8)))),
                    "avg_delay_minutes": float(r.randint(-30, 120)) if r.random() < 0.3 else 0.0,
                    "fill_rate_avg_pct": float(r.randint(70, 96)),
                    "total_cost_gbp": float(r.randint(2000, 6000)),
                    "cost_per_shipment_gbp": float(r.randint(250, 450)),
                    "updated_at": g.fake.date_time_this_year()
                })
    
    # Story: Midshires (CAR-002) service slips on Glasgow/Dundee lanes in the last 2 weeks; Northline stays strong.
    prof = {"CAR-001": (94, 88), "CAR-002": (90, 88), "CAR-003": (86, 84)}
    for lane in ("DC1-ST214", "DC1-ST215"):
        for cid, (ot, fr) in prof.items():
            for wk in range(-12, 0):
                ws = g.as_of + timedelta(weeks=wk)
                n = r.randint(14, 20)
                o, f = float(ot + r.randint(-2, 2)), float(fr + r.randint(-3, 3))
                if cid == "CAR-002" and wk >= -2:
                    o, f = float(60 + r.randint(-4, 4)), float(66 + r.randint(-3, 3))
                carrier_performance.append({
                    "carrier_id": cid, "lane": lane, "period_start": ws, "period_end": ws + timedelta(days=6),
                    "shipments_count": n, "on_time_count": round(n * o / 100), "on_time_pct": round(100 * round(n * o / 100) / n, 1),
                    "avg_delay_minutes": 140.0 if cid == "CAR-002" and wk >= -2 else 25.0,
                    "fill_rate_avg_pct": f, "total_cost_gbp": float(n * 270), "cost_per_shipment_gbp": 270.0,
                    "updated_at": g.as_of})
                late_n = n - round(n * o / 100)
                for k in range(n):
                    dep = ws + timedelta(days=k % 6)
                    late = k < late_n
                    dly = (r.randint(90, 240) if cid != "CAR-002" or wk < -2 else r.randint(180, 420)) if late else 0
                    shipments.append({
                        "shipment_id": f"SHP-{len(shipments) + 1:06d}", "origin_site_id": "DC1", "dest_site_id": lane.split("-")[1],
                        "carrier_id": cid, "lane": lane, "mode": "road", "status": "delivered",
                        "planned_departure": dep, "actual_departure": dep, "planned_arrival": dep + timedelta(days=1),
                        "actual_arrival": dep + timedelta(days=1), "lines_count": r.randint(5, 15),
                        "volume_cbm": 15.0, "weight_kg": 2500.0, "pallets": max(1, round(f / 100 * 26)), "cases": 60, "units": 600,
                        "fill_rate_pct": f, "freight_cost_gbp": 270.0, "delay_minutes": dly or None, "is_split": False,
                        "created_at": g.as_of, "updated_at": g.as_of})

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
        if rc == "carrier_rolled":
            rolled = r.choice(sea_rolled)["shipment_id"]
        avoid = rc in ("supplier_late", "demand_forecast_lift") or (rc in ("stockout_recovery", "carrier_rolled") and r.random() < 0.5)
        air_freight.append({
            "air_shipment_id": f"AIR-{i + 1:06d}", "shipment_id": sid, "po_id": m["po_id"], "supplier_id": sup,
            "carrier_id": m["carrier_id"], "origin_site_id": m["origin_port"], "dest_site_id": pos[m["po_id"]]["dest_site_id"],
            "reason_code": rc, "reason_detail": rc.replace("_", " ").capitalize() + " on " + m["po_id"],
            "rolled_shipment_id": rolled, "planned_date": date.fromisoformat(m["eta"]), "actual_date": ata,
            "units": units, "weight_kg": float(kg), "cost_gbp": cost, "avoidable": avoid,
            "avoided_by": ({"supplier_late": "earlier supplier follow-up", "demand_forecast_lift": "better forecast",
                            "stockout_recovery": "earlier booking", "carrier_rolled": "earlier booking"}[rc] if avoid else None)})

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
            "hours_breached": float(r.randint(1, 6)),
            "status": r.choice(["reported", "remediated"]),
            "remediation": g.fake.sentence() if r.random() < 0.7 else None,
            "created_at": g.fake.date_time_this_year()
        })
    
    # Generate planned_stops with unique composite keys
    stop_id = 0
    for lane in lanes:
        origin, dest = lane.split("-")
        planned_stops.append({
            "stop_id": f"STP-{stop_id:06d}",
            "lane": lane,
            "customer_or_store": dest,
            "stop_time_minutes": r.randint(15, 60),
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
    
    # Generate postcodes with unique keys
    postcodes_data = ["M1", "L1", "S1", "B1", "E1", "SW1", "OX1", "EX1"]
    postcode_id = 0
    for postcode in postcodes_data:
        carrier = r.choice(parcel_carriers + road_carriers)
        postcodes.append({
            "postcode_id": f"PC-{postcode_id:06d}",
            "postcode": postcode,
            "region": r.choice(["North West", "North East", "Yorkshire", "Midlands", "East Anglia", "London", "South East", "South West"]),
            "carrier_id": carrier["carrier_id"],
            "next_day_available": r.choice([True, True, False]),
            "next_day_cost_gbp": float(r.randint(3, 15)) if r.random() < 0.7 else 0.0,
            "standard_cost_gbp": float(r.randint(2, 8)),
            "coverage_from": (g.as_of - timedelta(days=r.randint(30, 365))).date() if isinstance(g.as_of, datetime) else g.as_of - timedelta(days=r.randint(30, 365)),
            "updated_at": g.fake.date_time_this_year()
        })
        postcode_id += 1
    
    # Generate reverse_logistics
    categories = ["Womenswear", "Menswear", "Home", "Accessories", "Clearance"]
    for category in categories:
        for week in range(-12, 1):
            period_start = g.as_of + timedelta(weeks=week)
            period_start = period_start - timedelta(days=period_start.weekday()) if isinstance(period_start, datetime) else period_start - timedelta(days=period_start.weekday())
            period_end = period_start + timedelta(days=6)
            
            reverse_logistics.append({
                "category": category,
                "period_start": period_start.date() if isinstance(period_start, datetime) else period_start,
                "period_end": period_end.date() if isinstance(period_end, datetime) else period_end,
                "return_units": r.randint(100, 1000),
                "transport_cost_gbp": float(r.randint(200, 1500)),
                "cost_per_unit_gbp": float(r.randint(1, 5)),
                "processing_cost_gbp": float(r.randint(500, 3000)),
                "resale_value_gbp": float(r.randint(1000, 8000)),
                "updated_at": g.fake.date_time_this_year()
            })
    
    return {
        "shipments": shipments,
        "carriers_lanes": carriers_lanes,
        "carrier_performance": carrier_performance,
        "carrier_incidents": carrier_incidents,
        "air_freight": air_freight,
        "route_plans": route_plans,
        "route_hours_breaches": route_hours_breaches,
        "planned_stops": planned_stops,
        "allocation_scenarios": allocation_scenarios,
        "transfer_scenarios": transfer_scenarios,
        "postcodes": postcodes,
        "reverse_logistics": reverse_logistics
    }
