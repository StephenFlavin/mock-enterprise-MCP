"""Background data quality issues, checks, pipeline changes and events. Migration scores are all seeded."""
from datetime import timedelta

ANALYSTS = ["EMP-00095", "EMP-00096", "EMP-00097", "EMP-00098", "EMP-00099", "EMP-00100"]

# (dataset, severity, status, days_ago_raised, days_to_resolve, description, root_cause)
# Noise never touches the story: open ones are low/medium on datasets the questions do not use,
# high/critical ones are long closed.
NOISE_ISSUES = [
    ("shipments", "low", "open", 41, None, "Carrier reference blank on a handful of booked shipments", "Manual booking entries skip the carrier field"),
    ("shipments", "medium", "in_progress", 33, None, "Duplicate shipment lines after a feed replay", "Replay of the TMS extract without de-duplication"),
    ("supplier_master", "low", "open", 27, None, "Payment terms stored as text on some supplier records", "Free-text entry in the supplier form"),
    ("supplier_master", "medium", "assigned", 22, None, "Two supplier records share the same bank details", "Duplicate created during onboarding"),
    ("shipments", "high", "closed", 150, 12, "Delivered shipments with no delivery date", "ETL dropped rows with null POD time"),
    ("purchase_orders", "medium", "closed", 120, 9, "PO currency missing on draft orders", "Default currency not applied in the extract"),
    ("sales_actuals", "high", "resolved", 95, 6, "Store 214 sales loaded twice for one trading day", "Retry of a failed load without idempotency"),
    ("inventory_position", "critical", "closed", 210, 18, "DC stock snapshot missing for one site", "Snapshot job timed out"),
    ("cost_centre_actuals", "low", "closed", 180, 4, "Cost centre names truncated in the report extract", "Column width in the extract"),
    ("OTIF_daily", "low", "closed", 160, 3, "Late-night loads left yesterday's OTIF partially populated", "Report refreshed before the load completed"),
    ("ASN_feed", "medium", "closed", 130, 8, "ASN lines with zero quantity", "Supplier test messages reached production"),
    ("demand_forecast", "low", "closed", 140, 5, "Forecast horizon column stored as text", "Type changed in the export"),
]
REOPENED_NOISE = {"Late-night loads left yesterday's OTIF partially populated": 1}


def generate(g):
    r = g.rng
    issues, events, checks, changes = [], [], [], []
    ev = 0

    def event(issue_id, etype, when, actor, note):
        nonlocal ev
        ev += 1
        events.append({"event_id": f"EVT-{ev:06d}", "issue_id": issue_id, "event_type": etype,
                       "event_at": when, "actor": actor, "note": note})

    for i, (ds, sev, status, ago, fix, desc, cause) in enumerate(NOISE_ISSUES, start=1):
        iid = f"DQI-{i:06d}"
        owner = g.pick(ANALYSTS)
        raised = g.days_ago(ago)
        resolved = raised + timedelta(days=fix) if fix else None
        reopen = REOPENED_NOISE.get(desc, 0)
        event(iid, "raised", raised, owner, desc)
        if resolved:
            event(iid, "resolved", resolved, owner, "Fixed and verified")
        issues.append({"issue_id": iid, "dataset": ds, "severity": sev, "description": desc, "root_cause": cause,
                       "status": status, "owner": owner, "raised_at": raised, "resolved_at": resolved,
                       "reopen_count": reopen,
                       "updated_at": resolved or raised + timedelta(days=r.randint(1, 10))})

    # Routine passing checks for datasets outside the stories (story datasets are fully seeded)
    for ds in ("shipments", "supplier_master", "purchase_orders", "sales_actuals"):
        for ctype, metric, thr in (("completeness", 99, 95), ("timeliness", 2, 4), ("consistency", 99, 98)):
            checks.append({
                "check_id": f"CHK-{len(checks) + 1:06d}", "dataset": ds, "check_type": ctype, "result": "pass",
                "metric_value": metric + r.choice([0, 0, -1]) if ctype != "timeliness" else r.choice([1, 2, 3]),
                "threshold": thr, "description": f"{ctype} check for {ds} within threshold",
                "checked_at": g.days_ago(r.randint(1, 10)), "related_issue_id": None})

    # Unrelated pipeline changes on other datasets (older or on datasets the stories do not use)
    other = [("shipments", "pipeline", "Moved shipment extract to hourly schedule", "Fresher shipment data; no definition change"),
             ("shipments", "schema", "Added customs_status column to shipment extract", "New optional column"),
             ("supplier_master", "source", "Supplier master now read from the new MDM hub", "Same fields; ids unchanged"),
             ("supplier_master", "schema", "Widened supplier name column to 120 characters", "No downstream impact"),
             ("inventory_position", "pipeline", "Snapshot job moved to 02:00", "Counts available earlier"),
             ("purchase_orders", "schema", "Added revised_due_date column", "Optional, not yet populated"),
             ("sales_actuals", "source", "Store EPOS feed switched to the new gateway", "Same schema"),
             ("cost_centre_actuals", "pipeline", "Nightly aggregation job rewritten", "Totals unchanged")]
    for i, (ds, ct, d, imp) in enumerate(other, start=6):
        changes.append({"change_id": f"PCH-{i:06d}", "dataset": ds, "change_type": ct, "description": d,
                        "impact": imp, "changed_at": g.days_ago(r.randint(8, 70)),
                        "changed_by": g.pick(ANALYSTS), "rollback_possible": r.random() < 0.6})

    return {"data_quality_issues": issues, "data_quality_issue_events": events, "data_quality_checks": checks,
            "pipeline_changes": changes, "migration_data_quality": []}
