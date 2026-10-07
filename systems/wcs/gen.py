"""WCS data: AMR fleet and charging schedules (seeded), equipment versions, background faults, hourly throughput."""
from datetime import datetime, timedelta

AUTOMATION = ("shuttle", "conveyor", "sorter", "motor", "gearbox", "sensor")
SITES = ("DC1", "DC2", "DC3")
ZONES = ("zone-A", "zone-B", "zone-C", "pick-area")
NOISE_FAULTS = [
    ("SENSOR-001", "Photo-eye intermittent blocked signal", "Photo-eye sensor"),
    ("MOTOR-VIB", "Motor vibration above alarm threshold", "Motor bearing"),
    ("GEARBOX-002", "Gearbox oil temperature high", "Gearbox"),
]


def generate(g):
    r = g.rng
    assets = [a for a in g.master("assets") if a["site_id"] in SITES and a["asset_class"] in AUTOMATION]

    # Equipment versions: copy the master software version where master has one (shuttles 4.x, sorters 7.1)
    equipment = []
    for a in assets:
        cls = a["asset_class"]
        ctrl = a.get("software_version") or r.choices(["3.2", "3.3", "3.4"], [2, 5, 3])[0]
        dev = None if cls in ("shuttle", "sorter") else r.choices(["1.8", "1.9", "2.0"], [2, 4, 4])[0]
        degraded = a["site_id"] == "DC3" and cls in ("motor", "gearbox", "sensor") and r.random() < 0.08
        equipment.append({
            "asset_id": a["asset_id"], "site_id": a["site_id"], "asset_class": cls,
            "controller_software_version": ctrl, "device_firmware_version": dev,
            "installed_date": a["install_date"],
            "last_updated_at": datetime.combine(g.as_of - timedelta(days=r.randint(60, 240)), datetime.min.time()) + timedelta(hours=r.randint(8, 16)),
            "status": "degraded" if degraded else "active",
        })

    # Background faults: harmless alerts (no throughput lost) on non-shuttle equipment, so stoppage lists stay clean
    pool = [a for a in assets if a["asset_class"] in ("motor", "gearbox", "sensor") and a["site_id"] in ("DC1", "DC3")]
    story = {"AST-DC1-CNV-M08", "AST-DC1-CNV-G01", "AST-DC1-CNV-G02", "AST-DC1-CNV-M03", "AST-DC1-CNV-S09"}
    pool = [a for a in pool if a["asset_id"] not in story]
    versions = {e["asset_id"]: e["controller_software_version"] for e in equipment}
    faults = []
    for i in range(24):
        a = r.choice(pool)
        code, desc, comp = r.choice(NOISE_FAULTS)
        occ = datetime.combine(g.as_of - timedelta(days=r.randint(2, 75)), datetime.min.time()) + timedelta(hours=r.randint(0, 23), minutes=r.randint(0, 59))
        faults.append({
            "fault_id": f"FLT-{800000 + i}", "asset_id": a["asset_id"], "robot_id": None, "site_id": a["site_id"],
            "fault_code": code, "fault_description": desc, "severity": r.choice(["info", "info", "warning"]),
            "occurred_at": occ, "resolved_at": occ + timedelta(minutes=5), "component_failed": comp,
            "duration_minutes": 0, "root_cause": None, "controller_version_at_fault": versions[a["asset_id"]],
            "throughput_impact_units": 0, "sensor_prediction_possible": False, "related_work_order": None,
            "location": a["location"],
        })

    # Hourly throughput per zone, 28 days to yesterday. Only DC1 dips 14:00-16:00 (4 of 8 robots on charge then).
    base = {"DC1": 150, "DC2": 190, "DC3": 120}
    throughput = []
    for site in SITES:
        for day_back in range(1, 29):
            day = datetime.combine(g.as_of - timedelta(days=day_back), datetime.min.time())
            for h in range(24):
                dip = site == "DC1" and h in (15, 16)  # hour_ending 15:00 and 16:00 = the 14:00-16:00 window
                for z in ZONES:
                    units = base[site] * (0.85 if dip else 1.0) * (0.96 + 0.08 * r.random())
                    if dip:
                        density, events, wait, robots = r.randint(66, 80), r.randint(3, 6), r.randint(9, 14), r.choice([1, 1, 1, 2])
                    else:
                        density, events, wait, robots = r.randint(35, 55), r.choice([0, 0, 1, 1, 2]), r.randint(2, 6), r.choice([2, 2, 2, 1])
                    throughput.append({
                        "site_id": site, "zone": z, "hour_ending": day + timedelta(hours=h), "throughput_units": int(units),
                        "robots_active": robots, "traffic_density_pct": density, "congestion_events": events,
                        "avg_wait_time_seconds": wait, "battery_health_avg_pct": r.randint(74, 84) if not dip else r.randint(70, 78),
                    })

    return {"amr_fleet": [], "equipment_versions": equipment, "fault_log": faults,
            "charging_schedule": [], "throughput_by_hour": throughput}
