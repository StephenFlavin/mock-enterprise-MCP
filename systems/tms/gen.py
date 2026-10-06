"""Transport management system data: shipments, carriers, lanes, routes, performance, incidents."""
from datetime import datetime, timedelta, time


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
    road_carriers = [c for c in carriers if c["mode"] == "road"]
    parcel_carriers = [c for c in carriers if c["mode"] == "parcel"]
    ocean_carriers = [c for c in carriers if c["mode"] == "ocean"]
    air_carriers = [c for c in carriers if c["mode"] == "air"]

    # Define lanes: DC to store and store to store
    lanes = []
    for dc in dcs[:3]:  # Use first 3 DCs
        for store in stores[:50]:  # Sample 50 stores per DC
            lanes.append(f"{dc['site_id']}-{store['site_id']}")

    # Lanes for ocean freight
    ocean_lanes = ["GBFXT-FAC-CN", "GBFXT-FAC-VN", "GBFXT-FAC-BD"]

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

    # Generate carriers_lanes allocations
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

    # Add ocean lanes
    for lane in ocean_lanes:
        for carrier in r.sample(ocean_carriers, min(2, len(ocean_carriers))):
            carriers_lanes.append({
                "carrier_id": carrier["carrier_id"],
                "lane": lane,
                "mode": "ocean",
                "status": "active",
                "weekly_capacity_trips": r.randint(1, 4),
                "weekly_capacity_pallets": r.randint(200, 1000),
                "rate_per_trip_gbp": float(r.randint(3000, 8000)),
                "rate_per_pallet_gbp": float(r.randint(50, 150)),
                "min_pieces": 20,
                "cutoff_hour": 17,
                "cutoff_day_offset": 14,
                "pct_allocation": float(r.randint(30, 70)),
                "updated_at": g.fake.date_time_this_year()
            })

    # Generate shipments (last 90 days + future 14 days)
    for i in range(2500):  # Realistic volume of ~25 per day
        lane = r.choice(lanes)
        origin, dest = lane.split("-")
        carrier = r.choice(road_carriers)

        planned_dep = g.date_between(90, -14)  # 90 days ago to 14 days future
        planned_arr = planned_dep + timedelta(days=r.randint(1, 5))

        # Some shipments already happened
        is_past = planned_dep < g.as_of

        if is_past:
            # Actual dates for past shipments
            delay = int(r.gauss(0, 1.5))  # Some early, some late
            actual_dep = planned_dep + timedelta(days=max(0, delay))
            actual_arr = planned_arr + timedelta(days=delay)
        else:
            actual_dep = None
            actual_arr = None

        is_split = r.random() < 0.12  # 12% split rate
        units = r.randint(100, 2000)
        pallets = max(1, units // 50)
        fill_rate = float(r.randint(60, 98))

        cost = float(r.randint(180, 800))

        shipments.append({
            "shipment_id": f"SHP-{len(shipments) + 1:06d}",
            "order_id": r.choice(orders)["order_id"] if r.random() < 0.7 else None,
            "po_id": r.choice(purchase_orders)["po_id"] if r.random() < 0.3 else None,
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

    # Generate carrier_performance (weekly summaries)
    for lane in lanes[:100]:  # Sample lanes for perf data
        for carrier in r.sample(road_carriers, min(2, len(road_carriers))):
            for week_offset in range(-12, 2):
                week_start = g.as_of + timedelta(weeks=week_offset)
                week_start = week_start - timedelta(days=week_start.weekday())  # Monday
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

    # Generate carrier incidents (claims, delays, etc.)
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

    # Generate air_freight
    for i in range(80):
        origin = r.choice(dcs)["site_id"]
        dest = r.choice(stores)["site_id"]
        created_date = g.date_between(90, 1)
        planned_date = created_date + timedelta(days=1)
        actual_date = planned_date + timedelta(days=r.randint(0, 2))

        air_freight.append({
            "air_shipment_id": f"AIR-{i + 1:06d}",
            "shipment_id": r.choice(shipments)["shipment_id"] if r.random() < 0.5 else None,
            "carrier_id": r.choice(air_carriers)["carrier_id"] if air_carriers else None,
            "origin_site_id": origin,
            "dest_site_id": dest,
            "reason_code": r.choice(["stockout_recovery", "peak_overflow", "supplier_late", "carrier_rolled", "demand_forecast_lift"]),
            "reason_detail": g.fake.sentence(),
            "planned_date": planned_date,
            "actual_date": actual_date,
            "units": r.randint(50, 500),
            "weight_kg": float(r.randint(100, 2000)),
            "cost_gbp": float(r.randint(1500, 8000)),
            "avoidable": r.choice([True, False, False]),
            "avoided_by": r.choice(["earlier booking", "better forecast", "split consolidation"]) if r.random() < 0.6 else None,
            "created_at": datetime.combine(created_date, time(hour=r.randint(6, 18)))
        })

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

    # Generate planned_stops
    for lane in lanes[:100]:
        origin, dest = lane.split("-")
        for _ in range(r.randint(1, 3)):
            planned_stops.append({
                "lane": lane,
                "customer_or_store": dest,
                "stop_time_minutes": r.randint(15, 60),
                "frequency_per_week": float(r.randint(1, 5)),
                "source": "route planning history",
                "updated_at": g.fake.date_time_this_year()
            })

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

    # Generate postcodes
    uk_regions = ["North West", "North East", "Yorkshire", "Midlands", "East Anglia", "London", "South East", "South West"]
    postcodes_data = ["M1", "L1", "S1", "B1", "E1", "SW1", "OX1", "EX1"]

    for postcode in postcodes_data * 5:
        carrier = r.choice(parcel_carriers + road_carriers)
        postcodes.append({
            "postcode": postcode,
            "region": r.choice(uk_regions),
            "carrier_id": carrier["carrier_id"],
            "next_day_available": r.choice([True, True, False]),
            "next_day_cost_gbp": float(r.randint(3, 15)) if r.random() < 0.7 else 0.0,
            "standard_cost_gbp": float(r.randint(2, 8)),
            "coverage_from": (g.as_of - timedelta(days=r.randint(30, 365))).date() if isinstance(g.as_of, datetime) else g.as_of - timedelta(days=r.randint(30, 365)),
            "updated_at": g.fake.date_time_this_year()
        })

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
