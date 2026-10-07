"""Fleet telematics: route runs, driver hours compliance, and vehicle operating costs."""
from datetime import datetime, time, timedelta


def generate(g):
    r = g.rng

    # Generate routes
    routes = []
    route_names = [
        ("London-Birmingham", "ST001", "DC1", 160, 4.5, 2, 45, None),
        ("M62-Route-East", "DC1", "DC3", 240, 5.5, 3, 40, "CAR-002"),
        ("M62-Route-West", "DC1", "DC2", 280, 6.0, 4, 35, "CAR-002"),
        ("London-Southampton", "ST215", "DC4", 120, 3.5, 2, 50, None),
        ("Northern-Circuits", "DC2", "DC3", 180, 4.0, 3, 35, None),
        ("Midlands-Loop", "DC1", "ST050", 200, 5.0, 4, 30, None),
        ("South-Coast-Delivery", "DC4", "ST214", 280, 6.5, 5, 40, "CAR-003"),
        ("Wales-Service", "DC1", "ST100", 320, 7.0, 3, 50, "CAR-004"),
        ("East-Anglia-Route", "DC3", "ST025", 210, 5.0, 4, 35, None),
        ("Scotland-Express", "DC2", "ST150", 400, 9.0, 5, 45, "CAR-001"),
    ]

    for i, (name, origin, dest, dist, hours, stops, assumption, carrier) in enumerate(route_names, 1):
        routes.append({
            "route_id": f"RTE-{i:06d}",
            "name": name,
            "origin_site_id": origin,
            "destination_site_id": dest,
            "distance_km": dist,
            "planned_hours": hours,
            "planned_stops": stops,
            "stop_time_assumption_minutes": assumption,
            "carrier_id": carrier,
            "status": "active",
        })

    # Generate fleet vehicles
    vehicles = []
    vehicle_configs = [
        ("box_van", "Ford", "Transit Custom", 35000, 22000, 800, 1200, 350, 45000, 7.8),
        ("curtainside", "Volvo", "FH16", 85000, 55000, 2000, 2800, 600, 80000, 25.0),
        ("flatbed", "Scania", "R450", 95000, 62000, 2200, 3200, 700, 90000, 26.5),
        ("refrigerated", "Mercedes", "Actros", 110000, 72000, 2400, 3500, 750, 95000, 28.0),
        ("articulated", "DAF", "XF", 130000, 85000, 2800, 4200, 900, 120000, 32.0),
        ("parcel_van", "Peugeot", "Boxer", 28000, 18000, 600, 900, 250, 35000, 6.5),
    ]

    vehicles_data = []
    vehicle_id = 1
    for purchase_offset in [30, 60, 90, 120, 180, 240, 300, 365, 450, 600]:
        for vtype, make, model, purchase_cost, current_value, maint, fuel, tax, annual_km, fuel_cons in vehicle_configs:
            purchase_date = g.as_of - timedelta(days=purchase_offset)
            if vehicle_id > 60:  # cap at 60 vehicles
                break
            vehicles_data.append({
                "vehicle_id": f"VEH-{vehicle_id:06d}",
                "registration": g.fake.license_plate(),
                "vehicle_type": vtype,
                "manufacturer": make,
                "model": model,
                "purchase_date": purchase_date,
                "purchase_cost_gbp": purchase_cost,
                "current_value_gbp": current_value,
                "service_hours": r.randint(1000, 50000),
                "annual_maint_cost_gbp": maint,
                "annual_fuel_cost_gbp": fuel,
                "annual_licence_tax_gbp": tax,
                "annual_miles_km": annual_km,
                "payload_capacity_kg": r.randint(1500, 25000),
                "fuel_consumption_l_per_100km": fuel_cons,
                "status": r.choices(["active", "maintenance"], [90, 10])[0],
                "notes": "",
            })
            vehicle_id += 1
        if vehicle_id > 60:
            break

    # Generate route runs (individual journeys)
    route_runs = []
    drivers = [emp["employee_id"] for emp in g.master("employees") if "Driver" in emp.get("role", "")]
    if not drivers:
        drivers = [f"EMP-{i:05d}" for i in range(1, 21)]

    run_id_counter = 1
    for route in routes:
        # Generate 15-30 runs per route over the last 60 days
        num_runs = r.randint(15, 30)
        for _ in range(num_runs):
            days_ago = r.randint(1, 60)
            run_date = g.as_of - timedelta(days=days_ago)

            # For M62 routes, sometimes they exceed hours
            is_m62 = "M62" in route["name"]

            base_hours = route["planned_hours"]
            # Add variance: some runs take longer, especially M62 with traffic
            if is_m62:
                variance = r.gauss(0.5, 0.8)  # higher variance for M62
                hours_breach_chance = 0.35
            else:
                variance = r.gauss(0, 0.3)
                hours_breach_chance = 0.05

            actual_drive_hours = round(base_hours + variance, 2)

            # Calculate stop times - actual vs planned
            planned_stop_total = route["planned_stops"] * (route["stop_time_assumption_minutes"] / 60.0)
            actual_stop_time_minutes = r.randint(
                int(route["stop_time_assumption_minutes"] * route["planned_stops"] * 0.8),
                int(route["stop_time_assumption_minutes"] * route["planned_stops"] * 1.6)
            )
            stop_hours = actual_stop_time_minutes / 60.0

            # Unload time
            unload_minutes = r.randint(15, 120)

            total_on_duty = actual_drive_hours + stop_hours + (unload_minutes / 60.0)
            hours_available = 11.0  # standard working day

            # For M62 routes, sometimes exceed
            if is_m62 and r.random() < hours_breach_chance:
                total_on_duty = min(total_on_duty + r.uniform(0.5, 2.0), 14.0)

            compliant = total_on_duty <= hours_available
            violations = ""
            if not compliant:
                violations = "EXCEEDS_DAILY_LIMIT"

            departure = datetime.combine(run_date, time(r.randint(5, 8), r.choice([0, 30])))
            arrival = departure + timedelta(hours=total_on_duty)

            route_runs.append({
                "run_id": f"RUN-{run_id_counter:06d}",
                "route_id": route["route_id"],
                "vehicle_id": r.choice(vehicles_data)["vehicle_id"],
                "driver_id": r.choice(drivers),
                "run_date": run_date,
                "actual_distance_km": round(route["distance_km"] * r.uniform(0.95, 1.05), 1),
                "actual_stops": r.randint(max(1, route["planned_stops"] - 1), route["planned_stops"] + 2),
                "total_stop_time_minutes": actual_stop_time_minutes,
                "total_unload_time_minutes": unload_minutes,
                "departure_time": departure,
                "arrival_time": arrival,
                "actual_drive_hours": actual_drive_hours,
                "total_on_duty_hours": round(total_on_duty, 2),
                "hours_available": hours_available,
                "traffic_delay_minutes": r.randint(0, 60) if is_m62 else r.randint(0, 20),
                "fuel_used_litres": round(route["distance_km"] * 0.25 * r.uniform(0.9, 1.1), 1),
                "tachograph_compliant": compliant,
                "violations": violations,
                "updated_at": datetime.combine(run_date, time(23, 0)),
            })
            run_id_counter += 1

    # Generate driver compliance logs (one per route run)
    driver_compliance = []
    log_id_counter = 1
    for rr in route_runs:
        log_entry = {
            "log_id": f"DCL-{log_id_counter:06d}",
            "driver_id": rr["driver_id"],
            "route_id": rr["route_id"],
            "run_date": rr["run_date"],
            "hours_worked": rr["total_on_duty_hours"],
            "weekly_hours": round(r.uniform(35, 50), 1),
            "hours_available_working_time": 11.0,
            "rest_period_hours": round(r.uniform(8, 14), 1),
            "tachograph_reading": "compliant" if rr["tachograph_compliant"] else "non_compliant",
            "violation_type": "none" if rr["tachograph_compliant"] else "exceeded_daily_hours",
            "severity": "none" if rr["tachograph_compliant"] else r.choice(["warning", "minor", "major"]),
            "resolved": r.choices([True, False], [70, 30])[0] if rr["violations"] else True,
        }
        driver_compliance.append(log_entry)
        log_id_counter += 1

    return {
        "routes": routes,
        "route_runs": route_runs,
        "fleet_vehicles": vehicles_data,
        "driver_compliance_logs": driver_compliance,
    }
