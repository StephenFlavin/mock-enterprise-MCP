"""Background health & safety data. The story rows live in seed/ and are overlaid on top.

Background is deliberately quiet around the stories: no forklift-pedestrian wording, no 'Layout change' root
causes, no hotspot locations in the last 100 days, and no fatigue tags at DC1-DC3 in the last 100 days, so the
planted rows are what a correct answer finds.
"""
from datetime import datetime, timedelta

REGIMES = {
    "GB": "HSW Act 1974; PUWER 1998; LOLER 1998; COSHH; DSEAR 2002; Manual Handling Operations Regs 1992; Work at Height Regs 2005",
    "IE": "Safety, Health and Welfare at Work Act 2005; General Application Regs 2007",
    "DE": "ArbSchG; ArbStaettV; BetrSichV; DGUV Vorschrift 68 (industrial trucks); Arbeitszeitgesetz",
    "NL": "Arbowet; Arbobesluit; Arbeidstijdenwet",
    "US": "OSHA 29 CFR 1910.178 (powered industrial trucks); OSHA General Duty Clause",
    "HK": "Occupational Safety and Health Ordinance (Cap. 509)",
    "PL": "Labour Code (Kodeks pracy) Section X; BHP general OHS regulation; UDT technical inspection of industrial trucks; EU Directive 89/391/EEC; Directive 2009/104/EC",
}

TASKS = {
    "Forklift operation": (["Forklift"], ["Forklift struck racking upright", "Load slipped from forks", "Forklift clipped a dock door frame", "Forklift tyre failure in aisle"]),
    "Reach truck operation": (["Reach truck"], ["Reach truck blade caught pallet edge", "Load shifted on raised forks", "Reach truck mast fouled sprinkler pipe"]),
    "Pallet stacking": (["Racking", "Pallet jack"], ["Pallet overhung beam, stack collapse avoided", "Damaged pallet found in stack", "Pallet jack handle trapped hand"]),
    "Order picking": ([None, "Lift"], ["Picker slipped on spilt liquid", "Picker strained shoulder reaching to a top shelf", "Tote dropped from pick station"]),
    "Receiving": (["Pallet jack", None], ["Cage trolley trapped foot at dock", "Pallet dropped during unload", "Cut hand on strapping"]),
    "Loading dock": ([None], ["Carton fell from trailer load", "Dock plate lip caused trip", "Strapping snapped while unloading"]),
    "Equipment maintenance": (["Conveyor", "Sorter"], ["Pinch point on conveyor guard", "Minor electric shock testing sensor", "Cut hand during belt change"]),
}
LOCS = [f"Aisle {n}" for n in range(1, 13)] + ["Dock area", "Mezzanine", "Packing area", "Crossing point A1", "Crossing point B2", "Crossing point C3"]
HOTSPOTS = {"Aisle 7", "Aisle 3", "Crossing point A1", "Crossing point B2"}
ROOTS = ["Inadequate training", "Procedure not followed", "Equipment defect", "Housekeeping"]


def generate(g):
    r = g.rng
    as_of = g.as_of
    sites = [s for s in g.master("sites")]
    dcs = [s["site_id"] for s in sites if s["type"] == "dc"]
    emps = [e for e in g.master("employees") if e["status"] == "active" and e["department"] == "Logistics"]
    by_site = {d: [e["employee_id"] for e in emps if e["site_id"] == d] for d in dcs}
    mgrs = {d: [e["employee_id"] for e in emps if e["site_id"] == d and "Manager" in e["role"]] for d in dcs}

    incidents = []
    weights = {"DC1": 1.0, "DC2": 1.0, "DC3": 0.4, "DC4": 0.7, "DC5": 0.2}
    for _ in range(50):
        site = r.choices(dcs, [weights.get(d, 0.0) for d in dcs])[0]   # DC6-DC8 (3PL overflow, Poland, Germany) have no background incidents
        days = r.randint(1, 365)
        shift = r.choices(["early", "late", "night"], [35, 40, 25])[0]
        hour = {"early": r.randint(6, 13), "late": r.randint(14, 21), "night": r.choice([22, 23, 0, 1, 2, 3, 4, 5])}[shift]
        occurred = datetime.combine(g.days_ago(days), datetime.min.time()).replace(hour=hour, minute=r.choice([0, 10, 25, 40, 50]))
        task = r.choice(list(TASKS))
        equips, descs = TASKS[task]
        loc = r.choice(LOCS)
        while days < 100 and site == "DC1" and loc in HOTSPOTS:
            loc = r.choice(LOCS)
        sev = r.choices(["critical", "high", "medium", "low"], [2, 15, 40, 43])[0]
        typ = r.choices(["accident", "near_miss", "dangerous_occurrence"], [45, 50, 5])[0]
        if typ == "dangerous_occurrence" and sev in ("low", "medium"):
            typ = "near_miss"
        fatigue = shift in ("late", "night") and r.random() < 0.15 and (days > 100 or site in ("DC4", "DC5"))
        incidents.append({
            "incident_id": f"INC-{len(incidents) + 1:06d}", "site_id": site, "occurred_at": occurred,
            "incident_type": typ, "severity": sev, "location": loc, "task": task,
            "description": r.choice(descs), "reported_by": r.choice(by_site[site]),
            "is_fatigue_related": fatigue, "shift_type": shift, "equipment_involved": r.choice(equips),
            "root_cause": "Fatigue" if fatigue else r.choice(ROOTS),
            "created_at": occurred + timedelta(hours=1), "updated_at": occurred + timedelta(days=1, hours=3),
        })

    cas = []
    for site in [d for d in dcs if d in weights]:   # DC6-DC8 have no HSE employees or history in master
        old_site = site in ("DC1", "DC2", "DC3")
        for _ in range(5 if old_site else 8):
            status = r.choice(["completed", "closed"]) if old_site else r.choices(["open", "in_progress", "completed", "closed"], [40, 20, 25, 15])[0]
            done = status in ("completed", "closed")
            if old_site or done:
                due = as_of - timedelta(days=r.randint(30, 200))
            else:
                due = as_of + timedelta(days=r.randint(5, 60))
            comp = due - timedelta(days=r.randint(0, 14)) if done else None
            cands = [i for i in incidents if i["site_id"] == site and i["occurred_at"].date() < due - timedelta(days=10)]
            inc = r.choice(cands) if cands and r.random() < 0.6 else None
            created = (inc["occurred_at"] + timedelta(days=1)) if inc else datetime.combine(due - timedelta(days=r.randint(20, 60)), datetime.min.time())
            cas.append({
                "ca_id": f"CA-{len(cas) + 1:06d}", "site_id": site, "incident_id": inc["incident_id"] if inc else None,
                "status": status, "description": r.choice([
                    "Review and update risk assessment for crossing points", "Install additional safety signage",
                    "Conduct safety training refresher", "Inspect equipment for defects",
                    "Improve dock area layout", "Replace worn racking guards", "Refresh housekeeping audit"]),
                "owner": r.choice(mgrs[site] or by_site[site]), "due_date": due,
                "completed_date": comp, "created_at": created,
                "updated_at": datetime.combine(comp or (as_of - timedelta(days=r.randint(0, 10))), datetime.min.time()) + timedelta(hours=16),
            })

    jurisdictions = [{
        "site_id": s["site_id"], "name": s["name"], "site_type": s["type"], "country": s["country"],
        "applicable_regimes": REGIMES.get(s["country"], ""),
    } for s in sites]

    validations = []
    for a in g.master("assets"):
        if a["site_id"] == "DC2" and a["asset_class"] == "shuttle" and a["asset_id"].split("-")[-1].isdigit() \
                and int(a["asset_id"].split("-")[-1]) >= 4:
            d = g.days_ago(r.randint(110, 300))
            validations.append({
                "validation_id": f"VAL-{len(validations) + 1:06d}", "asset_id": a["asset_id"], "validation_date": d,
                "validation_type": "Safety checks", "status": "pass", "validated_by": r.choice(mgrs["DC2"]),
                "firmware_version": a["software_version"], "notes": "Routine safety checks passed; gates and e-stops verified",
                "updated_at": datetime.combine(d, datetime.min.time()) + timedelta(hours=15),
                "equipment_id": None, "site_id": None, "asset_name": None, "current_firmware": None,
            })

    return {"incidents": incidents, "corrective_actions": cas, "risk_assessments": [],
            "site_safety_procedures": [], "safety_validations": validations, "site_jurisdictions": jurisdictions}
