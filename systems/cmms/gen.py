"""Background maintenance data for the CMMS: work orders, stoppages, condition readings, spares, shutdown plans.

Story scope (the DC2 site, the DC1 sorter and the DC1 conveyor network) gets NO generated stoppages, so the
seeded stories are what a correct answer finds. Everything else is plausible background around master assets.
Stoppages and breakdown work orders are generated together (same duration, linked ids), and a stoppage's cost is the
repair cost on its work order plus lost throughput.
"""
import csv
from datetime import datetime, timedelta
from pathlib import Path

STORY_PREFIXES = ("AST-DC2-SHT", "AST-DC1-SRT", "AST-DC1-CNV")
SEED_DIR = Path(__file__).parent / "seed"

# class -> (planned cost, planned hours, run hours per year, lost-throughput GBP per minute)
CLASS = {
    "sorter": (1500, 6.0, 6500, 2.5),
    "shuttle": (350, 2.5, 5200, 6.3),
    "conveyor": (500, 4.0, 6000, 8.0),
    "motor": (320, 2.0, 6000, 6.0),
    "gearbox": (520, 3.0, 6000, 6.0),
    "sensor": (110, 0.75, 8000, 5.0),
    "forklift": (380, 3.0, 2200, 3.0),
    "reach_truck": (360, 3.0, 2000, 3.0),
    "dock_leveller": (300, 2.5, 900, 6.0),
    "sprinkler": (200, 1.5, 0, 2.0),
    "compressor": (650, 4.0, 4500, 4.0),
}
# class -> [(planned task)], [(root cause, component failed, repair description)]
PLANNED_TASKS = {
    "sorter": ["Preventive maintenance and roller inspection", "Sorter tray and sensor inspection"],
    "shuttle": ["Preventive maintenance and lubrication", "Wheel and chain inspection"],
    "conveyor": ["Belt tension and roller inspection", "Preventive maintenance"],
    "motor": ["Preventive maintenance", "Motor alignment check", "Bearing lubrication"],
    "gearbox": ["Oil change and inspection", "Preventive maintenance"],
    "sensor": ["Sensor calibration", "Lens clean and alignment check"],
    "forklift": ["Planned service and safety inspection", "Mast chain lubrication"],
    "reach_truck": ["Planned service and safety inspection", "Mast chain lubrication"],
    "dock_leveller": ["Hydraulic check and lubrication", "Planned service"],
    "sprinkler": ["Annual sprinkler test", "Valve inspection"],
    "compressor": ["Planned service and filter change", "Oil change"],
}
FAILURES = {
    "sorter": [("Mechanical wear", "Sorter roller", "Replace worn sorter rollers"),
               ("Sensor malfunction", "Induction sensor", "Replace faulty induction sensor"),
               ("Lubrication failure", "Gearbox", "Gearbox oil replacement and filter change")],
    "shuttle": [("Bearing failure", "Motor bearing", "Replace motor bearing assembly"),
                ("Seal degradation", "Oil seal", "Replace oil seals")],
    "conveyor": [("Conveyor jam", "Roller", "Clear jam and replace damaged roller"),
                 ("Mechanical wear", "Drive belt", "Replace drive belt")],
    "motor": [("Bearing failure", "Motor bearing", "Replace motor bearing"),
              ("Electrical fault", "Motor winding", "Rewind or replace motor")],
    "gearbox": [("Lubrication failure", "Gearbox oil seal", "Replace oil seal and refill oil"),
                ("Mechanical wear", "Gear set", "Replace worn gear set")],
    "sensor": [("Sensor malfunction", "Photo-eye", "Replace photo-eye sensor"),
               ("Misalignment", "Sensor bracket", "Realign and secure sensor bracket")],
    "forklift": [("Hydraulic fault", "Hydraulic hose", "Replace hydraulic hose"),
                 ("Electrical fault", "Traction battery", "Replace battery cell and test")],
    "reach_truck": [("Hydraulic fault", "Hydraulic hose", "Replace hydraulic hose"),
                    ("Mechanical wear", "Mast chain", "Replace mast chain")],
    "dock_leveller": [("Hydraulic fault", "Hydraulic cylinder", "Replace hydraulic cylinder seals"),
                      ("Electrical fault", "Control panel", "Replace control relay")],
    "sprinkler": [("Mechanical wear", "Valve", "Replace faulty valve")],
    "compressor": [("Lubrication failure", "Compressor oil pump", "Replace oil pump"),
                   ("Electrical fault", "Control board", "Replace control board")],
}
BREAKDOWN_MINUTES = {"sorter": (120, 300), "shuttle": (30, 210), "conveyor": (30, 240), "motor": (45, 240),
                     "gearbox": (60, 300), "sensor": (15, 90), "forklift": (30, 240), "reach_truck": (30, 240),
                     "dock_leveller": (30, 240), "sprinkler": (20, 120), "compressor": (45, 300)}


def _read_seed_assets(name):
    p = SEED_DIR / f"{name}.csv"
    if not p.exists():
        return set()
    with open(p, newline="") as f:
        return {r["asset_id"] for r in csv.DictReader(f)}


def _ts(d, hour=8):
    return datetime(d.year, d.month, d.day, hour, 0, 0)


def generate(g):
    r = g.rng
    as_of = g.as_of
    assets = [a for a in g.master("assets") if a["site_id"].startswith("DC")]
    by_id = {a["asset_id"]: a for a in assets}
    employees = g.master("employees")
    leads = {}
    for e in employees:
        if e["role"] in ("Shift Manager", "Warehouse Manager"):
            leads.setdefault(e["site_id"], []).append(e["employee_id"])

    def tech(site):
        return r.choice(leads[site]) if leads.get(site) else "unassigned"

    work_orders, stoppages, runhrs, parts, shutdowns = [], [], [], [], []
    counters = {"wo": 0, "stp": 0}

    def new_wo(**kw):
        counters["wo"] += 1
        row = {"wo_id": f"WO-{counters['wo']:06d}", "cancel_reason": None, "started_at": None, "completed_at": None,
               "planned_hours": None, "downtime_hours": None, "cost_gbp": None}
        row.update(kw)
        work_orders.append(row)
        return row

    def new_stoppage(asset, occurred, minutes, failure, cost_repair, wo_id):
        counters["stp"] += 1
        cls = asset["asset_class"]
        stoppages.append({
            "stoppage_id": f"STP-{counters['stp']:06d}",
            "asset_id": asset["asset_id"],
            "occurred_at": occurred,
            "duration_minutes": minutes,
            "root_cause": failure[0],
            "component_failed": failure[1],
            "asset_software_version": asset.get("software_version") or None,
            "work_order_id": wo_id,
            "predictable_from_sensor": failure[0] in ("Bearing failure", "Lubrication failure", "Seal degradation",
                                                      "Mechanical wear", "Misalignment") and r.random() < 0.8,
            "unplanned_cost_gbp": round(cost_repair + minutes * CLASS[cls][3], 2),
        })

    def breakdown(asset, occurred, minutes):
        """One breakdown: a completed work order plus the stoppage it fixed."""
        cls = asset["asset_class"]
        failure = r.choice(FAILURES[cls])
        repair = round(CLASS[cls][0] * r.uniform(1.4, 2.6), 2)
        raised = occurred + timedelta(minutes=5)
        hours = round(minutes / 60.0, 2)
        wo = new_wo(asset_id=asset["asset_id"], wo_type="breakdown", status="completed",
                    priority="urgent" if minutes >= 180 else "high", raised_at=raised,
                    planned_date=occurred.date(), started_at=raised,
                    completed_at=raised + timedelta(minutes=minutes), description=failure[2],
                    planned_hours=None, downtime_hours=hours, cost_gbp=repair,
                    assigned_to=tech(asset["site_id"]), updated_at=raised + timedelta(minutes=minutes))
        new_stoppage(asset, occurred, minutes, failure, repair, wo["wo_id"])

    # ---- breakdowns + stoppages (last 90 days), never in story scope -------------------------------------------
    for a in assets:
        cls = a["asset_class"]
        if cls not in CLASS or a["asset_id"].startswith(STORY_PREFIXES) or a["site_id"] == "DC2":
            continue  # DC2 is the shuttle story site: only the seeded 14 stoppages exist there
        if r.random() < 0.12:
            lo, hi = BREAKDOWN_MINUTES[cls]
            occurred = _ts(g.date_between(90, 2), r.randint(6, 20)) + timedelta(minutes=r.randint(0, 59))
            breakdown(a, occurred, r.randint(lo, hi))

    # ---- planned work history (last 6 months, completed) --------------------------------------------------------
    for a in assets:
        cls = a["asset_class"]
        if cls not in CLASS or a["asset_id"] == "AST-DC1-SRT":
            continue
        for _ in range(r.choice([0, 1, 1, 2])):
            raised = _ts(g.date_between(180, 20), 9)
            planned = raised.date() + timedelta(days=r.randint(2, 7))
            hrs = round(CLASS[cls][1] * r.uniform(0.7, 1.3), 2)
            start = _ts(planned, 8)
            new_wo(asset_id=a["asset_id"], wo_type="planned", status="completed",
                   priority=r.choices(["low", "medium", "high"], [30, 50, 20])[0], raised_at=raised,
                   planned_date=planned, started_at=start, completed_at=start + timedelta(hours=hrs),
                   description=r.choice(PLANNED_TASKS[cls]), planned_hours=round(CLASS[cls][1], 2),
                   downtime_hours=hrs, cost_gbp=round(CLASS[cls][0] * r.uniform(0.7, 1.3), 2),
                   assigned_to=tech(a["site_id"]), updated_at=start + timedelta(hours=hrs))

    # ---- the old DC1 sorter: seven years of rising maintenance cost (ends ~100 days ago, seed covers the rest) ----
    srt = by_id.get("AST-DC1-SRT")
    if srt:
        planned_per_year, breakdowns_per_year = 4, [1, 1, 2, 2, 3, 4, 3]
        for i in range(7):
            start_back = 365 * (7 - i)
            end_back = max(100, start_back - 365)
            for k in range(planned_per_year):
                raised = _ts(as_of - timedelta(days=r.randint(end_back, start_back)), 9)
                planned = raised.date() + timedelta(days=r.randint(2, 6))
                hrs = round(r.uniform(4, 7), 2)
                start = _ts(planned, 8)
                new_wo(asset_id="AST-DC1-SRT", wo_type="planned", status="completed", priority="medium",
                       raised_at=raised, planned_date=planned, started_at=start,
                       completed_at=start + timedelta(hours=hrs), description=r.choice(PLANNED_TASKS["sorter"]),
                       planned_hours=6.0, downtime_hours=hrs, cost_gbp=round(700 * (1 + 0.12 * i) * r.uniform(0.9, 1.1), 2),
                       assigned_to=tech("DC1"), updated_at=start + timedelta(hours=hrs))
            for k in range(breakdowns_per_year[i]):
                occurred = _ts(as_of - timedelta(days=r.randint(end_back, start_back)), r.randint(6, 20))
                minutes = int(r.randint(120, 240) * (1 + 0.08 * i))
                failure = r.choice(FAILURES["sorter"])
                repair = round(900 * (1 + 0.25 * i) * r.uniform(0.85, 1.15), 2)
                raised = occurred + timedelta(minutes=5)
                wo = new_wo(asset_id="AST-DC1-SRT", wo_type="breakdown", status="completed", priority="high",
                            raised_at=raised, planned_date=occurred.date(), started_at=raised,
                            completed_at=raised + timedelta(minutes=minutes), description=failure[2],
                            downtime_hours=round(minutes / 60.0, 2), cost_gbp=repair, assigned_to=tech("DC1"),
                            updated_at=raised + timedelta(minutes=minutes))
                new_stoppage(srt, occurred, minutes, failure, repair, wo["wo_id"])

    # ---- shutdown plans (DC1 story shutdown is seeded; generated ones are elsewhere and later) -----------------
    other = [a for a in assets if a["site_id"] != "DC1" and a["asset_class"] in CLASS and a["asset_class"] != "sprinkler"]
    for n in range(1, r.randint(3, 5) + 1):
        main = r.choice(other)
        site_assets = [a for a in other if a["site_id"] == main["site_id"] and a["asset_class"] != "dock_leveller"]
        picks = [main] + r.sample(site_assets, min(len(site_assets), r.randint(1, 3)))
        picks = list({a["asset_id"]: a for a in picks}.values())
        date = as_of + timedelta(days=r.randint(35, 180))
        duration = float(r.choice([8, 12, 16, 24]))
        budget, spent = duration, 0.0
        for a in picks:
            cls = a["asset_class"]
            hrs = round(min(CLASS[cls][1], budget - spent), 2)
            if hrs < 0.5:
                continue
            spent += hrs
            new_wo(asset_id=a["asset_id"], wo_type="planned", status="scheduled", priority="medium",
                   raised_at=_ts(as_of - timedelta(days=r.randint(3, 20)), 10), planned_date=date,
                   description=r.choice(PLANNED_TASKS[cls]) + " (shutdown)", planned_hours=hrs,
                   assigned_to=tech(a["site_id"]), updated_at=_ts(as_of - timedelta(days=2), 10))
        shutdowns.append({
            "shutdown_id": f"SHD-{n:06d}", "shutdown_date": date,
            "description": f"Planned maintenance window for {main['name']} and related equipment at {main['site_id']}",
            "duration_hours": duration, "asset_id": main["asset_id"],
            "related_assets": ",".join(a["asset_id"] for a in picks if a["asset_id"] != main["asset_id"]),
            "estimated_cost_gbp": round(spent * 95 + 400, 2),
            "status": r.choice(["planned", "approved"]), "updated_at": _ts(as_of - timedelta(days=2), 10),
        })

    # ---- condition readings and run hours (12 weekly readings, cumulative hours never go down) -----------------
    seeded = _read_seed_assets("asset_run_hours")
    for a in assets:
        cls = a["asset_class"]
        rate = CLASS.get(cls, (0, 0, 0, 0))[2]
        if not rate or a["asset_id"] in seeded or not a["install_date"]:
            continue
        install = datetime.strptime(a["install_date"], "%Y-%m-%d").date()
        k = r.uniform(0.85, 1.0)
        story = a["asset_id"].startswith(STORY_PREFIXES)
        degraded = a["status"] == "degraded"
        base = "fair" if degraded else ("good" if story else r.choices(["good", "fair", "poor"], [82, 15, 3])[0])
        for week in range(12, -1, -1):
            d = g.days_ago(week * 7)
            if d <= install:
                continue
            cond = "poor" if degraded and week < 4 else base
            vib = {"good": r.uniform(1.0, 2.8), "fair": r.uniform(3.0, 4.2), "poor": r.uniform(4.5, 6.2)}[cond]
            temp = {"good": r.uniform(50, 62), "fair": r.uniform(63, 72), "poor": r.uniform(73, 82)}[cond]
            oil = {"good": "good", "fair": r.choice(["good", "degrading"]), "poor": r.choice(["degrading", "bad"])}[cond]
            runhrs.append({"asset_id": a["asset_id"], "measured_at": d,
                           "run_hours": round((d - install).days / 365.0 * rate * k, 0),
                           "condition_rating": cond, "vibration_level_mm_s": round(vib, 1),
                           "temperature_c": round(temp, 0), "oil_analysis_status": oil})

    # ---- spare parts: background only for classes the seed does not cover --------------------------------------
    catalog = {
        "forklift": [("Forklift battery cell", 420, 14, 480), ("Hydraulic hose assembly", 65, 7, 90), ("Mast chain", 190, 10, 240)],
        "reach_truck": [("Reach truck drive tyre", 150, 12, 180), ("Mast roller set", 210, 14, 260)],
        "dock_leveller": [("Dock leveller hydraulic cylinder", 640, 21, 720), ("Dock leveller control relay", 55, 5, 70)],
        "sprinkler": [("Sprinkler head (pack of 10)", 85, 7, 110), ("Alarm valve gasket kit", 120, 14, 150)],
        "compressor": [("Compressor air filter element", 45, 5, 60), ("Compressor oil (20L)", 160, 5, 190)],
        "racking": [("Racking beam clip (pack of 50)", 40, 4, 55), ("Racking upright guard", 95, 10, 120)],
        "charger": [("Charger power module", 380, 21, 450)],
    }
    n = 0
    for cls, items in catalog.items():
        for name, cost, lead, _ in items:
            n += 1
            on_hand = r.randint(0, 8)
            cost = round(cost * r.uniform(0.95, 1.05), 2)
            parts.append({
                "part_id": f"SPR-{n:06d}", "name": name, "asset_class": cls, "sku": None,
                "supplier_id": r.choice(["SUP-0014", "SUP-0027", "SUP-0067"]),
                "on_hand": on_hand, "reorder_level": r.randint(1, 4), "reorder_qty": r.choice([2, 4, 5, 10]),
                "lead_time_days": lead + r.randint(-2, 4), "unit_cost_gbp": cost,
                "stock_value_gbp": round(on_hand * cost, 2), "last_usage_date": g.date_between(90, 2),
            })

    return {"work_orders": work_orders, "unplanned_stoppages": stoppages, "asset_run_hours": runhrs,
            "spare_parts": parts, "shutdown_plan": shutdowns}
