"""Background maintenance data: work orders, asset condition readings, failures, spare parts, and shutdown plans."""
from datetime import datetime, timedelta


def generate(g):
    """Generate CMMS data referencing master assets."""
    r = g.rng

    # Get DC assets for maintenance
    all_assets = g.master("assets")
    dc_assets = [a for a in all_assets if a["site_id"].startswith("DC")]

    work_orders = []
    unplanned_stoppages = []
    asset_run_hours = []
    spare_parts = []
    shutdown_plan = []

    # Generate work orders (6-month history + future scheduled)
    wo_id = 1
    for asset in dc_assets:
        asset_id = asset["asset_id"]
        site_id = asset["site_id"]

        # 4-8 historical work orders per asset
        for _ in range(r.randint(4, 8)):
            raised = g.date_between(180, 7)
            wo_type = r.choices(["planned", "breakdown"], [70, 30])[0]
            status = r.choices(["completed", "cancelled"], [85, 15])[0] if raised < g.as_of else "scheduled"

            wo = {
                "wo_id": f"WO-{wo_id:06d}",
                "asset_id": asset_id,
                "wo_type": wo_type,
                "status": status,
                "priority": r.choices(["low", "medium", "high", "urgent"], [20, 40, 30, 10])[0],
                "raised_at": raised,
                "planned_date": raised + timedelta(days=r.randint(3, 14)),
                "started_at": raised + timedelta(days=r.randint(4, 15)) if status in ["completed", "in_progress"] else None,
                "completed_at": raised + timedelta(days=r.randint(5, 20)) if status == "completed" else None,
                "description": f"{asset['name']}: {r.choice(['Preventive maintenance', 'Repair bearing', 'Replace seal', 'Oil change', 'Component inspection', 'Motor alignment', 'Sensor calibration'])}",
                "cancel_reason": None if status != "cancelled" else r.choice(["Deferred to shutdown", "Issue resolved", "Duplicate order"]),
                "downtime_hours": r.uniform(0.5, 8) if status == "completed" else None,
                "cost_gbp": r.uniform(200, 2500) if status == "completed" else None,
                "assigned_to": r.choice([e["employee_id"] for e in g.master("employees") if e["site_id"] == site_id][:5]) if [e for e in g.master("employees") if e["site_id"] == site_id] else None,
                "updated_at": raised + timedelta(days=r.randint(1, 5)),
            }
            work_orders.append(wo)
            wo_id += 1

    # Generate unplanned stoppages (3-month history)
    stoppage_id = 1
    for asset in dc_assets:
        # 0-3 failures per asset in last 90 days
        for _ in range(r.randint(0, 3)):
            occurred = g.date_between(90, 1)
            duration = r.randint(15, 480)  # 15 mins to 8 hours

            stoppage = {
                "stoppage_id": f"STP-{stoppage_id:06d}",
                "asset_id": asset["asset_id"],
                "occurred_at": datetime.combine(occurred, datetime.min.time()) + timedelta(hours=r.randint(6, 20)),
                "duration_minutes": duration,
                "root_cause": r.choice([
                    "Bearing failure",
                    "Seal degradation",
                    "Misalignment",
                    "Lubrication failure",
                    "Electrical fault",
                    "Software glitch",
                    "Sensor malfunction",
                    "Conveyor jam",
                    "Power supply issue",
                    "Mechanical wear"
                ]),
                "component_failed": r.choice([
                    "Motor bearing",
                    "Oil seal",
                    "Drive belt",
                    "Coupling",
                    "Sprocket",
                    "Motor winding",
                    "Position sensor",
                    "Pressure valve",
                    "Control board",
                    "Drive shaft"
                ]),
                "asset_software_version": asset.get("software_version", "1.0"),
                "work_order_id": None,
                "predictable_from_sensor": r.choice([True, False]),
                "unplanned_cost_gbp": duration * r.uniform(10, 50),
            }
            unplanned_stoppages.append(stoppage)
            stoppage_id += 1

    # Generate asset run hours and condition readings
    for asset in dc_assets:
        # readings over last 12 weeks
        for week in range(12):
            measured_at = g.days_ago(week * 7)
            readings = {
                "asset_id": asset["asset_id"],
                "measured_at": measured_at,
                "run_hours": r.uniform(1000, 50000),
                "condition_rating": r.choices(["good", "fair", "poor", "critical"], [60, 25, 12, 3])[0],
                "vibration_level_mm_s": r.uniform(0.5, 7.0),
                "temperature_c": r.uniform(40, 85),
                "oil_analysis_status": r.choices(["good", "degrading", "bad"], [70, 25, 5])[0],
            }
            asset_run_hours.append(readings)

    # Generate spare parts inventory
    part_classes = ["motor", "gearbox", "sensor", "conveyor", "shuttle"]
    part_id = 1
    suppliers = g.master("suppliers")
    for _ in range(40):
        part = {
            "part_id": f"SPR-{part_id:06d}",
            "name": f"Spare {r.choice(['motor', 'bearing', 'seal', 'belt', 'coupler', 'sprocket', 'sensor', 'valve', 'gasket', 'relay'])}",
            "asset_class": r.choice(["shuttle", "conveyor", "sorter", "motor", "gearbox", "sensor"]),
            "sku": None,
            "supplier_id": r.choice([s["supplier_id"] for s in suppliers])[:20] if suppliers else None,
            "on_hand": r.randint(0, 15),
            "reorder_level": r.randint(2, 6),
            "reorder_qty": r.randint(5, 20),
            "lead_time_days": r.randint(7, 90),
            "unit_cost_gbp": r.uniform(50, 1500),
            "stock_value_gbp": 0,  # calculated
            "last_usage_date": g.date_between(60, 0),
        }
        part["stock_value_gbp"] = part["on_hand"] * part["unit_cost_gbp"]
        spare_parts.append(part)
        part_id += 1

    # Generate shutdown plans (next 6 months)
    shutdown_id = 1
    for i in range(r.randint(3, 6)):
        shutdown_date = g.as_of + timedelta(days=r.randint(7, 180))
        asset = r.choice(dc_assets)
        shutdown = {
            "shutdown_id": f"SHD-{shutdown_id:06d}",
            "shutdown_date": shutdown_date,
            "description": f"Planned maintenance window for {asset['name']} and related systems",
            "duration_hours": r.uniform(4, 24),
            "asset_id": asset["asset_id"],
            "related_assets": ",".join([a["asset_id"] for a in r.sample(dc_assets, min(3, len(dc_assets)))]),
            "work_orders_included": r.randint(2, 8),
            "estimated_cost_gbp": r.uniform(1000, 10000),
            "status": r.choices(["planned", "approved"], [60, 40])[0],
            "updated_at": g.as_of,
        }
        shutdown_plan.append(shutdown)
        shutdown_id += 1

    return {
        "work_orders": work_orders,
        "unplanned_stoppages": unplanned_stoppages,
        "asset_run_hours": asset_run_hours,
        "spare_parts": spare_parts,
        "shutdown_plan": shutdown_plan,
    }
