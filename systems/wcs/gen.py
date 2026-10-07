"""WCS data: AMR fleet, equipment versions, fault logs, charging schedules, throughput metrics."""
from datetime import datetime, timedelta, time


def generate(g):
    r = g.rng
    fake = g.fake

    # Get DC sites
    sites = [a["site_id"] for a in g.master("assets") if a["site_id"].startswith("DC")]
    sites = sorted(set(sites))[:3]  # Use DC1, DC2, DC3

    # Get equipment assets by class
    equipment_by_site = {}
    equipment_by_class = {}
    for a in g.master("assets"):
        if a["site_id"] in sites:
            if a["site_id"] not in equipment_by_site:
                equipment_by_site[a["site_id"]] = []
            equipment_by_site[a["site_id"]].append(a)

            cls = a["asset_class"]
            if cls not in equipment_by_class:
                equipment_by_class[cls] = []
            equipment_by_class[cls].append(a)

    # Generate AMR Fleet
    amr_fleet = []
    robot_ids = {}  # Track robots by site for fault logs
    for site in sites:
        # Each site has 5-8 robots
        n_robots = r.randint(5, 8)
        for i in range(n_robots):
            robot_id = f"robot-{len(amr_fleet) + 1:03d}"
            robot_ids.setdefault(site, []).append(robot_id)

            # Firmware versions: mostly 4.6, some 4.7
            firmware = r.choices(["4.6", "4.7"], [7, 3])[0]

            # Generate some realistic battery state
            battery_pct = r.randint(40, 95)
            last_charge = g.as_of - timedelta(hours=r.randint(2, 8))

            amr_fleet.append({
                "robot_id": robot_id,
                "site_id": site,
                "firmware_version": firmware,
                "battery_state_pct": battery_pct,
                "last_charge_completed_at": datetime.combine(last_charge, time(r.randint(5, 22), r.choice([0, 30]))),
                "status": r.choices(["active", "idle", "charging"], [60, 30, 10])[0],
                "location": r.choice([f"zone-{chr(65 + i)}" for i in range(3)] + [f"aisle-{chr(65 + i)}" for i in range(5)]),
                "total_distance_km": round(r.uniform(100, 5000), 1),
                "last_fault_at": g.as_of - timedelta(days=r.randint(1, 30)) if r.random() < 0.4 else None,
                "updated_at": g.as_of - timedelta(hours=r.randint(0, 4)),
            })

    # Generate Equipment Versions
    equipment_versions = []
    for site, assets in equipment_by_site.items():
        for asset in assets:
            # Focus on automation assets
            if asset["asset_class"] in ["shuttle", "conveyor", "sorter", "motor", "gearbox", "sensor"]:
                controller_ver = r.choices(["3.2", "3.3", "3.4"], [2, 5, 3])[0]
                device_ver = r.choices(["1.8", "1.9", "2.0"], [2, 4, 4])[0] if asset["asset_class"] != "shuttle" else None

                equipment_versions.append({
                    "asset_id": asset["asset_id"],
                    "site_id": site,
                    "asset_class": asset["asset_class"],
                    "controller_software_version": controller_ver,
                    "device_firmware_version": device_ver,
                    "installed_date": asset.get("install_date") or (g.as_of - timedelta(days=r.randint(365, 1825))).date(),
                    "last_updated_at": g.as_of - timedelta(days=r.randint(30, 180)),
                    "status": r.choices(["active", "degraded"], [90, 10])[0],
                })

    # Generate Fault Logs (14+ stoppages for Q1)
    fault_log = []
    fault_codes = [
        ("MOTOR-001", "Motor bearing failure"),
        ("GEARBOX-002", "Gearbox oil temperature high"),
        ("SENSOR-001", "Photo-eye sensor blocked"),
        ("BATT-LOW", "Battery level critically low"),
        ("WIFI-ERR", "Network connectivity lost"),
        ("COLLISION", "Collision detection triggered"),
        ("OVERLOAD", "Payload overweight"),
    ]

    # Add stoppages from last 30 days with emphasis on past week (14 in last month)
    for _ in range(14):
        # Most stoppages in last 30 days, clustered in last week
        days_ago = r.choices(range(1, 31), weights=[1.5 if i < 7 else 1 for i in range(1, 31)])[0]
        occurred = g.as_of - timedelta(days=days_ago, hours=r.randint(0, 23))

        # Pick a random asset or robot
        is_robot = r.random() < 0.6
        site = r.choice(sites)

        if is_robot and robot_ids.get(site):
            asset_id = None
            robot_id = r.choice(robot_ids[site])
        else:
            # Pick from equipment
            site_assets = [a for a in equipment_by_site.get(site, [])]
            if site_assets:
                asset_id = r.choice(site_assets)["asset_id"]
            else:
                asset_id = "AST-DC1-CNV"
            robot_id = None

        fault_code, description = r.choice(fault_codes)
        duration = r.randint(10, 240)
        throughput_impact = r.randint(50, 500)

        fault_log.append({
            "fault_id": f"FLT-{len(fault_log) + 1:06d}",
            "asset_id": asset_id,
            "robot_id": robot_id,
            "site_id": site,
            "fault_code": fault_code,
            "fault_description": description,
            "severity": r.choices(["warning", "critical"], [30, 70])[0],
            "occurred_at": occurred,
            "resolved_at": occurred + timedelta(minutes=duration),
            "component_failed": r.choice(["motor bearing", "gearbox", "sensor", "battery", "network", "wheel"]),
            "duration_minutes": duration,
            "root_cause": r.choice(["Normal wear", "Lack of maintenance", "Environmental factor", "Design issue"]),
            "controller_version_at_fault": r.choice(["3.2", "3.3", "3.4"]),
            "throughput_impact_units": throughput_impact,
            "sensor_prediction_possible": r.random() < 0.4,
            "related_work_order": f"WO-{r.randint(900000, 900100)}" if r.random() < 0.5 else None,
        })

    # Add more general faults (warnings, info)
    for _ in range(20):
        days_ago = r.randint(1, 30)
        occurred = g.as_of - timedelta(days=days_ago, hours=r.randint(0, 23))
        site = r.choice(sites)

        is_robot = r.random() < 0.7
        if is_robot and robot_ids.get(site):
            asset_id = None
            robot_id = r.choice(robot_ids[site])
        else:
            site_assets = [a for a in equipment_by_site.get(site, [])]
            asset_id = r.choice(site_assets)["asset_id"] if site_assets else None
            robot_id = None

        fault_code, description = r.choice(fault_codes)
        duration = r.randint(5, 60)

        fault_log.append({
            "fault_id": f"FLT-{len(fault_log) + 1:06d}",
            "asset_id": asset_id,
            "robot_id": robot_id,
            "site_id": site,
            "fault_code": fault_code,
            "fault_description": description,
            "severity": r.choice(["info", "warning"]),
            "occurred_at": occurred,
            "resolved_at": occurred + timedelta(minutes=duration),
            "component_failed": None,
            "duration_minutes": duration,
            "root_cause": None,
            "controller_version_at_fault": r.choice(["3.2", "3.3", "3.4"]),
            "throughput_impact_units": 0,
            "sensor_prediction_possible": False,
            "related_work_order": None,
        })

    # Generate Charging Schedule
    charging_schedule = []
    sched_id = 0
    time_slots = [
        ("06:00", "08:00"),
        ("12:00", "13:00"),
        ("18:00", "20:00"),
        ("22:00", "23:30"),
    ]
    for site in sites:
        for slot_start, slot_end in time_slots:
            sched_id += 1
            n_robots = len(robot_ids.get(site, []))
            robots_charging = max(1, r.randint(n_robots // 3, n_robots // 2))

            charging_schedule.append({
                "schedule_id": f"CHG-{sched_id:06d}",
                "site_id": site,
                "schedule_version": 1,
                "time_slot": f"{slot_start}-{slot_end}",
                "start_time": slot_start,
                "end_time": slot_end,
                "robots_in_slot": robots_charging,
                "battery_avg_start_pct": r.randint(20, 40),
                "battery_avg_end_pct": r.randint(80, 98),
                "active": True,
                "effective_from": g.as_of,
                "updated_at": g.as_of,
            })

    # Generate Throughput by Hour (last 7 days, every hour)
    throughput_by_hour = []
    zones = ["zone-A", "zone-B", "zone-C", "pick-area"]

    for site in sites:
        n_robots_site = len(robot_ids.get(site, []))

        for day_offset in range(7):
            date = g.as_of - timedelta(days=day_offset)

            for hour in range(24):
                hour_end = datetime.combine(date.date(), time(hour, 59, 59))

                for zone in zones:
                    # Throughput drops 2-4pm (14:00-16:00): hour 14 and 15
                    is_afternoon_dip = hour in [14, 15]
                    base_throughput = 150

                    if is_afternoon_dip:
                        throughput_units = int(base_throughput * 0.85 * (0.8 + r.random() * 0.35))  # 15% drop
                    else:
                        throughput_units = int(base_throughput * (0.9 + r.random() * 0.2))

                    # Traffic density also higher 2-4pm
                    if is_afternoon_dip:
                        traffic_density = r.randint(65, 85)
                        congestion_events = r.randint(2, 6)
                        wait_time = r.randint(8, 15)
                    else:
                        traffic_density = r.randint(35, 55)
                        congestion_events = r.randint(0, 2)
                        wait_time = r.randint(2, 6)

                    throughput_by_hour.append({
                        "site_id": site,
                        "zone": zone,
                        "hour_ending": hour_end,
                        "throughput_units": throughput_units,
                        "robots_active": max(1, int(n_robots_site * (traffic_density / 100))),
                        "traffic_density_pct": traffic_density,
                        "congestion_events": congestion_events,
                        "avg_wait_time_seconds": wait_time,
                        "battery_health_avg_pct": r.randint(60, 85),
                    })

    return {
        "amr_fleet": amr_fleet,
        "equipment_versions": equipment_versions,
        "fault_log": fault_log,
        "charging_schedule": charging_schedule,
        "throughput_by_hour": throughput_by_hour,
    }
