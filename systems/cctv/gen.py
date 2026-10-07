from datetime import datetime, timedelta


def generate(g):
    """Generate CCTV exception events and incident logs."""

    rng = g.rng
    fake = g.fake
    as_of = g.as_of

    # Sample from master data
    stores = [s for s in g.master("sites") if s["type"] == "store" and s["status"] == "open"]
    dcs = [s for s in g.master("sites") if s["type"] == "dc" and s["status"] == "open"]
    employees = g.master("employees")

    # Filter employees by store/DC (for realistic assignment)
    store_employees = {s["site_id"]: [e for e in employees if e["site_id"] == s["site_id"]] for s in stores}
    dc_employees = {d["site_id"]: [e for e in employees if e["site_id"] == d["site_id"]] for d in dcs}

    event_types = ["person_in_restricted_area", "unusual_activity", "tailgating", "tampering",
                   "unauthorized_access", "scanning_error", "system_fault"]
    incident_types = ["internal_theft", "external_theft", "process_error", "system_fault",
                      "stock_discrepancy", "pos_void", "unauthorized_refund", "equipment_failure"]
    severities = ["low", "medium", "high", "critical"]
    statuses = ["open", "reviewed", "escalated", "resolved"]
    incident_statuses = ["open", "investigating", "evidence_collected", "closed", "dismissed"]

    # Generate exception events
    exception_events = []
    incident_logs = []

    # Generate events across all stores and DCs
    all_sites = stores + dcs

    # ~200-400 exception events over 180 days
    for i in range(rng.randint(200, 400)):
        site = rng.choice(all_sites)
        days_ago = rng.randint(0, 180)
        occurred_at = g.days_ago(days_ago)
        event_type = rng.choice(event_types)
        severity = rng.choice(severities[1:] if rng.random() < 0.3 else severities)  # Skew towards medium/high

        # Camera IDs: CAM-<site>-<number>
        camera_id = f"CAM-{site['site_id']}-{rng.randint(1, 50):03d}"

        # Get employees at this site
        site_emps = store_employees.get(site["site_id"]) or dc_employees.get(site["site_id"]) or []
        employee_id = rng.choice(site_emps)["employee_id"] if site_emps and rng.random() < 0.4 else None

        # Reviewer might be security/loss prevention staff
        reviewed_by = rng.choice([e["employee_id"] for e in employees if "loss" in e.get("role", "").lower() or "security" in e.get("role", "").lower()] or [e["employee_id"] for e in employees[:50]])
        reviewed_at = occurred_at + g.fake.time_delta(seconds=rng.randint(3600, 86400*7))  # Within a week

        event_id = f"EXC-{900001 + i:06d}"

        descriptions = {
            "person_in_restricted_area": f"Unauthorized person detected in {rng.choice(['loading dock', 'staff room', 'security office', 'cash office', 'warehouse area'])}",
            "unusual_activity": f"Unusual activity: {rng.choice(['hovering over fixture', 'repeated shelf scanning', 'attempting door entry', 'tag removal observed'])}",
            "tailgating": "Employee access card used by multiple persons within seconds",
            "tampering": f"Potential tampering detected on {rng.choice(['security camera', 'alarm sensor', 'access control device', 'cash desk'])}",
            "unauthorized_access": f"Unauthorized access to {rng.choice(['secure area', 'storage room', 'inventory system'])}",
            "scanning_error": f"Scanner malfunction or bypass detected at {rng.choice(['POS 01', 'POS 02', 'POS 03', 'POS 04', 'self-checkout unit 5', 'self-checkout unit 6'])}",
            "system_fault": f"Camera system {rng.choice(['offline', 'feed interrupted', 'recording gap detected'])}",
        }

        description = descriptions.get(event_type, "CCTV exception event")

        exception_events.append({
            "event_id": event_id,
            "site_id": site["site_id"],
            "occurred_at": occurred_at,
            "event_type": event_type,
            "severity": severity,
            "description": description,
            "camera_id": camera_id,
            "employee_id": employee_id,
            "reviewed_by": reviewed_by,
            "reviewed_at": reviewed_at,
            "status": rng.choice(statuses),
            "updated_at": reviewed_at,
        })

    # Generate incident logs - subset of exception events that escalated to incidents
    for i in range(rng.randint(50, 100)):
        site = rng.choice(all_sites)
        days_ago = rng.randint(0, 180)
        occurred_at = g.days_ago(days_ago)
        incident_type = rng.choice(incident_types)
        severity = rng.choice(severities)

        # Link to some exception events (comma-separated)
        num_related = rng.randint(0, 3)
        related_events = [rng.choice(exception_events)["event_id"] for _ in range(num_related)]
        related_event_ids = ",".join(related_events) if related_events else None

        # Assign to loss prevention or security staff
        assigned_to = rng.choice([e["employee_id"] for e in employees if "loss" in e.get("role", "").lower() or "security" in e.get("role", "").lower()] or [e["employee_id"] for e in employees[:100]])

        status = rng.choice(incident_statuses)
        suspected_loss_gbp = None
        if incident_type in ["internal_theft", "external_theft", "unauthorized_refund"]:
            suspected_loss_gbp = rng.randint(50, 5000)

        created_at = occurred_at + g.fake.time_delta(seconds=rng.randint(300, 3600))
        closed_at = created_at + g.fake.time_delta(days=rng.randint(1, 30)) if status in ["closed", "dismissed"] else None

        incident_id = f"INC-{900001 + i:06d}"

        descriptions = {
            "internal_theft": f"Suspected internal theft at {site['name']}: {rng.choice(['inventory discrepancy', 'stock shortage', 'till variance', 'missing merchandise'])}",
            "external_theft": f"Suspected external theft at {site['name']}: {rng.choice(['shoplifting incident', 'organized retail crime', 'ORC activity'])}",
            "process_error": f"Process error detected: {rng.choice(['incorrect discount applied', 'wrong price charged', 'duplicate refund', 'void not logged'])}",
            "system_fault": f"System or equipment fault: {rng.choice(['POS system crash', 'cash register malfunction', 'scanner failure', 'access control issue'])}",
            "stock_discrepancy": f"Stock count variance: {rng.choice(['cycle count mismatch', 'inventory variance', 'perpetual vs physical count difference'])}",
            "pos_void": f"Excessive POS voids or returns logged",
            "unauthorized_refund": f"Unauthorized or fraudulent refund processed",
            "equipment_failure": f"Equipment failure affecting security: {rng.choice(['camera failure', 'alarm system down', 'access control outage'])}",
        }

        description = descriptions.get(incident_type, "Incident log entry")

        incident_logs.append({
            "incident_id": incident_id,
            "site_id": site["site_id"],
            "occurred_at": occurred_at,
            "incident_type": incident_type,
            "severity": severity,
            "description": description,
            "related_event_ids": related_event_ids,
            "assigned_to": assigned_to,
            "status": status,
            "suspected_loss_gbp": suspected_loss_gbp,
            "created_at": created_at,
            "closed_at": closed_at,
            "updated_at": closed_at or created_at + g.fake.time_delta(days=rng.randint(0, 10)),
        })

    return {
        "cctv_exception_events": exception_events,
        "incident_logs": incident_logs,
    }
