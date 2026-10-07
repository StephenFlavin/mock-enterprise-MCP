"""Background health & safety data: incidents, corrective actions, risk assessments by site."""
from datetime import datetime, timedelta, date


def generate(g):
    r = g.rng
    sites = [s["site_id"] for s in g.master("sites") if s["type"] == "dc"]
    employees = [e["employee_id"] for e in g.master("employees") if e["status"] == "active"]

    incidents = []
    corrective_actions = []
    risk_assessments = []
    site_procedures = []
    safety_validations = []
    site_jurisdictions = []

    # Build site jurisdictions (DC sites with their countries)
    for site in g.master("sites"):
        if site["type"] == "dc":
            site_jurisdictions.append({
                "site_id": site["site_id"],
                "country": site["country"],
                "applicable_regimes": "COSHH; PUWER; HSW Act; DSEAR" if site["country"] == "GB" else
                                     "ArbStättV; TRGS; BetrSichV" if site["country"] == "DE" else
                                     "Kodeks pracy; Rozporzadzenie; PNHP"
            })

    # Generate incidents across the 365 days + history, across all DCs
    for i in range(120):  # ~120 incidents across all 5 DCs
        site_id = r.choice(sites)
        incident_date = g.days_ago(r.randint(1, 365))
        occurred_at = datetime.combine(incident_date, datetime.min.time()).replace(
            hour=r.randint(6, 22), minute=r.choice([0, 15, 30, 45]))

        incident_type = r.choices(["accident", "near_miss", "dangerous_occurrence"], [60, 35, 5])[0]
        severity = r.choices(["critical", "high", "medium", "low"], [5, 20, 40, 35])[0]

        # Pick a location (aisle or area)
        location = r.choice(["Aisle A", "Aisle B", "Aisle C", "Aisle D", "Aisle E", "Aisle F",
                            "Aisle G", "Dock area", "Mezzanine", "Crossing point A1", "Crossing point B2"])

        task = r.choice(["Forklift operation", "Reach truck operation", "Pallet stacking",
                        "Order picking", "Receiving", "Loading dock", "Equipment maintenance"])

        equipment = r.choice(["Forklift", "Reach truck", "Conveyor", "Sorter", "Pallet jack",
                             "Racking", "Lift", None])

        shift = r.choice(["early", "late", "night", "days"])
        is_fatigue = r.choices([True, False], [20, 80])[0] if shift in ["night", "late"] else r.choices([True, False], [5, 95])[0]

        incidents.append({
            "incident_id": f"INC-{len(incidents) + 1:06d}",
            "site_id": site_id,
            "occurred_at": occurred_at,
            "incident_type": incident_type,
            "severity": severity,
            "location": location,
            "task": task,
            "description": f"{task} incident: {r.choice(['slip hazard', 'struck by', 'crush risk', 'fall hazard', 'near miss with equipment'])}",
            "reported_by": r.choice(employees),
            "is_fatigue_related": is_fatigue,
            "shift_type": shift,
            "equipment_involved": equipment,
            "root_cause": r.choice(["Inadequate training", "Fatigue", "Procedure not followed",
                                    "Equipment defect", "Housekeeping", "Layout change"]),
            "created_at": occurred_at + timedelta(hours=r.randint(0, 24)),
            "updated_at": occurred_at + timedelta(hours=r.randint(24, 72))
        })

    # Generate corrective actions - some linked to incidents, many open
    for i in range(60):
        site_id = r.choice(sites)

        # Link some to incidents
        linked_incident = r.choice([None] * 7 + [incidents[j]["incident_id"] for j in range(min(10, len(incidents)))])

        status = r.choices(["open", "in_progress", "completed", "closed"], [40, 20, 25, 15])[0]

        # g.as_of is a date object
        as_of_date = g.as_of if isinstance(g.as_of, date) else g.as_of.date()
        due_date = as_of_date + timedelta(days=r.randint(-30, 60))
        completed_date = None
        if status in ["completed", "closed"]:
            completed_date = due_date - timedelta(days=r.randint(0, 30))

        corrective_actions.append({
            "ca_id": f"CA-{len(corrective_actions) + 1:06d}",
            "site_id": site_id,
            "incident_id": linked_incident,
            "status": status,
            "description": r.choice([
                "Review and update risk assessment for crossing points",
                "Install additional safety signage",
                "Replace worn racking in aisle " + r.choice(["A", "B", "C", "D", "E"]),
                "Conduct safety training refresher",
                "Inspect equipment for defects",
                "Review shift patterns for fatigue management",
                "Improve dock area layout",
                "Install proximity sensors on equipment"
            ]),
            "owner": r.choice(employees),
            "due_date": due_date,
            "completed_date": completed_date,
            "created_at": datetime.combine(as_of_date - timedelta(days=r.randint(10, 180)), datetime.min.time()),
            "updated_at": datetime.combine(as_of_date - timedelta(days=r.randint(0, 10)), datetime.min.time())
        })

    # Generate risk assessments for various activities by site
    activities = ["Reach truck operation", "Forklift operation", "Battery charging", "Order picking",
                 "Equipment maintenance", "Pallet stacking", "Dock operations", "Mezzanine work"]

    for site_id in sites:
        for activity in r.sample(activities, r.randint(4, 8)):
            risk_level = r.choices(["critical", "high", "medium", "low"], [5, 20, 45, 30])[0]

            as_of_date = g.as_of if isinstance(g.as_of, date) else g.as_of.date()
            date_assessed = as_of_date - timedelta(days=r.randint(30, 365))

            risk_assessments.append({
                "ra_id": f"RA-{len(risk_assessments) + 1:06d}",
                "site_id": site_id,
                "activity": activity,
                "risk_level": risk_level,
                "hazards": r.choice([
                    "Collision with other equipment; pedestrians",
                    "Battery hazards; fire risk; chemical exposure",
                    "Struck-by incidents; crushing hazards",
                    "Fall from height; dropped objects",
                    "Electrical hazards; shock risk"
                ]),
                "controls": r.choice([
                    "Speed limiters; proximity sensors; operator training",
                    "Dedicated charging area; ventilation; fire suppression",
                    "High-visibility clothing; exclusion zones; signage",
                    "Edge protection; hard hats; PPE",
                    "Lockout/tagout; warning signs; maintenance logs"
                ]),
                "residual_risk": r.choices(["high", "medium", "low"], [20, 50, 30])[0],
                "date_assessed": date_assessed,
                "updated_at": datetime.combine(as_of_date - timedelta(days=r.randint(0, 90)), datetime.min.time())
            })

    # Generate site safety procedures by site
    procedure_types = ["Forklift operation", "Reach truck operation", "Battery charging",
                      "Dock operations", "Confined spaces", "Working at height", "Equipment maintenance"]

    for site_id in sites:
        for ptype in r.sample(procedure_types, r.randint(3, 6)):
            as_of_date = g.as_of if isinstance(g.as_of, date) else g.as_of.date()

            site_procedures.append({
                "procedure_id": f"PROC-{len(site_procedures) + 1:06d}",
                "site_id": site_id,
                "procedure_name": f"{ptype} - {site_id}",
                "procedure_type": ptype,
                "status": r.choices(["active", "inactive", "draft"], [85, 10, 5])[0],
                "last_updated": as_of_date - timedelta(days=r.randint(0, 180))
            })

    # Generate safety validation records for automation assets
    assets = [a for a in g.master("assets") if a["asset_class"] in ["shuttle", "sorter", "conveyor"]]

    for asset in r.sample(assets, min(15, len(assets))):
        for _ in range(r.randint(1, 3)):
            as_of_date = g.as_of if isinstance(g.as_of, date) else g.as_of.date()
            validation_date = as_of_date - timedelta(days=r.randint(1, 90))

            safety_validations.append({
                "validation_id": f"VAL-{len(safety_validations) + 1:06d}",
                "asset_id": asset["asset_id"],
                "validation_date": validation_date,
                "validation_type": r.choice(["Firmware update", "Safety checks", "Integration test", "Functional test"]),
                "status": r.choices(["pass", "fail", "needs_review"], [80, 10, 10])[0],
                "validated_by": r.choice(employees),
                "notes": r.choice(["All checks passed", "Minor discrepancy in sensor calibration",
                                 "Requires follow-up testing", "Documentation review needed"]),
                "updated_at": datetime.combine(validation_date, datetime.min.time()) + timedelta(hours=r.randint(1, 48))
            })

    return {
        "incidents": incidents,
        "corrective_actions": corrective_actions,
        "risk_assessments": risk_assessments,
        "site_safety_procedures": site_procedures,
        "safety_validations": safety_validations,
        "site_jurisdictions": site_jurisdictions
    }
