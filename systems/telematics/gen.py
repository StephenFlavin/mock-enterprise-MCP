"""Fleet telematics: route runs, driver hours compliance, and vehicle operating costs.

Story (02:11:Q5): the M62 Leeds-Manchester routes RTE-900001..900008 (same ids as tms route plans) run past the
driver hours limit because planned stop time (15 min per drop) is far below the real dwell + unload time. The
runs, compliance logs and these routes are hand-written in seed/*.csv; this file generates background:
non-M62 routes, a 60-vehicle fleet with realistic ages and costs, and 13 weeks of routine runs.
"""
from datetime import datetime, time, timedelta

FUEL_GBP_PER_LITRE = 1.50

# type: (make, model, new cost, annual km, l/100km, maint base, licence+insurance, payload kg)
VEHICLE_TYPES = {
    "parcel_van": ("Peugeot", "Boxer", 28000, 35000, 8.5, 1500, 1300, 1200),
    "box_van": ("Ford", "Transit Custom", 35000, 45000, 9.0, 1800, 1400, 1300),
    "curtainside": ("Volvo", "FL", 85000, 80000, 28.0, 6000, 3500, 10000),
    "flatbed": ("Scania", "P280", 95000, 70000, 30.0, 6500, 3800, 14000),
    "refrigerated": ("Mercedes", "Actros", 110000, 70000, 33.0, 8500, 4200, 14000),
    "articulated": ("DAF", "XF", 130000, 120000, 32.0, 9500, 4800, 26000),
}


def vehicle_costs(vtype, age_years):
    make, model, cost, km, l100, maint, tax, payload = VEHICLE_TYPES[vtype]
    return {
        "manufacturer": make, "model": model, "purchase_cost_gbp": cost,
        "current_value_gbp": round(cost * max(0.12, 0.84 ** age_years), -2),
        "annual_maint_cost_gbp": round(maint * (1 + 0.12 * age_years), -1),
        "annual_fuel_cost_gbp": round(km * l100 / 100 * FUEL_GBP_PER_LITRE, -1),
        "annual_licence_tax_gbp": tax,
        "annual_miles_km": km, "payload_capacity_kg": payload, "fuel_consumption_l_per_100km": l100,
    }


def make_run(r, route, vehicle_id, driver_id, run_date):
    """One routine run: on duty close to planned hours, stop time close to the assumption."""
    stops = route["planned_stops"]
    on_duty = round(route["planned_hours"] * r.uniform(0.92, 1.04), 2)
    if r.random() < 0.03:
        on_duty = round(11 + r.uniform(0.1, 0.8), 2)
    stop_total = stops * route["stop_time_assumption_minutes"] * r.uniform(0.85, 1.15)
    drive = round(on_duty - stop_total / 60, 2)
    dwell = int(stop_total * 0.4)
    unload = int(stop_total * 0.6)
    dep = datetime.combine(run_date, time(r.randint(5, 8), r.choice([0, 30])))
    ok = on_duty <= 11.0
    return {
        "route_id": route["route_id"], "vehicle_id": vehicle_id, "driver_id": driver_id, "run_date": run_date,
        "actual_distance_km": round(route["distance_km"] * r.uniform(0.97, 1.03), 1), "actual_stops": stops,
        "total_stop_time_minutes": dwell, "total_unload_time_minutes": unload,
        "departure_time": dep, "arrival_time": dep + timedelta(hours=on_duty),
        "actual_drive_hours": drive, "total_on_duty_hours": on_duty, "hours_available": 11.0,
        "traffic_delay_minutes": r.randint(0, 20),
        "fuel_used_litres": round(route["distance_km"] * 0.3 * r.uniform(0.9, 1.1), 1),
        "tachograph_compliant": ok, "violations": "" if ok else "EXCEEDS_DAILY_LIMIT",
        "updated_at": datetime.combine(run_date, time(23, 0)),
    }


def generate(g):
    r = g.rng

    # Routine (non-M62) routes. The M62 routes RTE-900001..900008 come from seed/routes.csv.
    route_defs = [
        ("RTE-000001", "London to Birmingham", "DC1", "ST001", 160, 4.5, 2, 45, None),
        ("RTE-000004", "London to Southampton", "DC4", "ST215", 120, 3.5, 2, 50, None),
        ("RTE-000005", "Northern Circuits", "DC2", "DC3", 180, 4.0, 3, 35, None),
        ("RTE-000006", "Midlands Loop", "DC1", "ST050", 200, 5.0, 4, 30, None),
        ("RTE-000007", "South Coast Delivery", "DC4", "ST214", 280, 6.5, 5, 40, "CAR-003"),
        ("RTE-000008", "Wales Service", "DC1", "ST100", 320, 7.0, 3, 50, "CAR-004"),
        ("RTE-000009", "East Anglia Route", "DC3", "ST025", 210, 5.0, 4, 35, None),
        ("RTE-000010", "Scotland Express", "DC2", "ST150", 400, 9.0, 5, 45, "CAR-001"),
    ]
    routes = [{
        "route_id": rid, "name": name, "origin_site_id": o, "destination_site_id": d, "distance_km": dist,
        "planned_hours": hrs, "planned_stops": stops, "stop_time_assumption_minutes": ass,
        "carrier_id": car, "status": "active",
    } for rid, name, o, d, dist, hrs, stops, ass, car in route_defs]

    # Fleet: 60 vehicles, ages 0.3 to 9 years, costs rising with age.
    weights = [("parcel_van", 11), ("box_van", 14), ("curtainside", 10), ("flatbed", 5), ("refrigerated", 8), ("articulated", 12)]
    types = [t for t, n in weights for _ in range(n)]
    vehicles = []
    for i, vtype in enumerate(types, 1):
        age = round(0.3 + (i * 7 % 60) / 60 * 8.7, 2)
        pdate = g.as_of - timedelta(days=int(age * 365.25))
        v = vehicle_costs(vtype, age)
        v["current_value_gbp"] = round(v["current_value_gbp"] * r.uniform(0.92, 1.08), -2)
        reg = f"{r.choice('LMNOPRSTV')}{r.choice('ABCDEFGHJKLMNOPRSTUVWXY')}{pdate.year % 100 + (50 if pdate.month > 8 else 0):02d} {''.join(r.choice('ABCDEFGHJKLMNPRSTUVWXY') for _ in range(3))}"
        status = r.choices(["active", "maintenance", "sold"], [88, 8, 4])[0] if age > 5 else r.choices(["active", "maintenance"], [92, 8])[0]
        vehicles.append({
            "vehicle_id": f"VEH-{i:06d}", "registration": reg, "vehicle_type": vtype, "purchase_date": pdate,
            "service_hours": int(age * 1500 * r.uniform(0.8, 1.2)), "status": status, "notes": "", **v,
        })

    # Routine runs: each active vehicle runs one non-M62 route on most weekdays for 13 weeks.
    runs, logs = [], []
    drivers = [f"DRV-{i:03d}" for i in range(7, 41)]
    seeded = [{"vehicle_id": f"VEH-9000{n:02d}", "vehicle_type": "articulated", "status": "maintenance" if n == 5 else "active"}
              for n in range(1, 13)]  # seed/fleet_vehicles.csv: also do routine runs
    for v in vehicles + seeded:
        if v["status"] in ("sold", "decommissioned"):
            continue
        route = routes[int(v["vehicle_id"][4:]) % len(routes)]
        p = 0.78 if v["vehicle_type"] in ("articulated", "curtainside", "refrigerated") else 0.65
        if v["status"] == "maintenance":
            p = 0.15
        for d in range(1, 92):
            day = g.as_of - timedelta(days=d)
            if day.weekday() >= 5 or r.random() > p:
                continue
            runs.append(make_run(r, route, v["vehicle_id"], r.choice(drivers), day))
    for n, run in enumerate(runs, 1):
        run["run_id"] = f"RUN-{n:06d}"
        over = run["total_on_duty_hours"] - run["hours_available"]
        logs.append({
            "log_id": f"DCL-{n:06d}", "driver_id": run["driver_id"], "route_id": run["route_id"], "run_date": run["run_date"],
            "hours_worked": run["total_on_duty_hours"], "weekly_hours": round(r.uniform(38, 52), 1),
            "hours_available_working_time": 11.0, "rest_period_hours": round(r.uniform(10, 14), 1),
            "tachograph_reading": "compliant" if over <= 0 else "non_compliant",
            "violation_type": "none" if over <= 0 else "exceeded_daily_hours",
            "severity": "none" if over <= 0 else "warning", "resolved": True,
        })

    return {"routes": routes, "route_runs": runs, "fleet_vehicles": vehicles, "driver_compliance_logs": logs}
