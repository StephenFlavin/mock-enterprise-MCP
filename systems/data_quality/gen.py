"""Background data quality issues, checks, pipeline changes and migration data."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    datasets = ["OTIF_daily", "ASN_feed", "demand_forecast", "sales_actuals", "inventory_position",
                "purchase_orders", "shipments", "supplier_master", "cost_centre_actuals"]
    employees = [e["employee_id"] for e in g.master("employees")][:10]  # sample of employees

    issues = []
    checks = []
    changes = []
    migrations = []

    # Generate data quality issues (background)
    severities = ["low", "medium", "high", "critical"]
    issue_statuses = ["open", "assigned", "in_progress", "resolved", "closed"]

    for i in range(25):
        dataset = r.choice(datasets)
        severity = r.choices(severities, [30, 35, 25, 10])[0]
        status = r.choices(issue_statuses, [30, 25, 20, 15, 10])[0]
        raised_at = g.date_between(-90, -1)
        resolved_at = None
        if status in ["resolved", "closed"]:
            resolved_at = raised_at + timedelta(days=r.randint(1, 30))

        issues.append({
            "issue_id": f"DQI-{i + 1:06d}",
            "dataset": dataset,
            "severity": severity,
            "description": f"{dataset} missing data quality checks",
            "root_cause": f"Pipeline change or source system issue",
            "status": status,
            "owner": r.choice(employees),
            "raised_at": raised_at,
            "resolved_at": resolved_at,
            "reopen_count": r.randint(0, 3) if status == "reopened" else 0,
            "updated_at": resolved_at if resolved_at else raised_at + timedelta(days=r.randint(0, 20))
        })

    # Generate data quality checks (background)
    check_types = ["completeness", "timeliness", "consistency"]
    check_results = ["pass", "warning", "fail"]

    for i in range(40):
        dataset = r.choice(datasets)
        check_type = r.choice(check_types)
        result = r.choices(check_results, [70, 20, 10])[0]
        checked_at = g.date_between(-14, 0)

        # Metric value depends on check type
        if check_type == "completeness":
            metric_value = r.randint(85, 100) if result == "pass" else r.randint(50, 84)
            threshold = 95
        elif check_type == "timeliness":
            metric_value = r.randint(1, 4) if result == "pass" else r.randint(5, 24)
            threshold = 4
        else:  # consistency
            metric_value = r.randint(90, 100) if result == "pass" else r.randint(60, 89)
            threshold = 98

        checks.append({
            "check_id": f"CHK-{i + 1:06d}",
            "dataset": dataset,
            "check_type": check_type,
            "result": result,
            "metric_value": metric_value,
            "threshold": threshold,
            "description": f"{check_type} check for {dataset}",
            "checked_at": checked_at,
            "related_issue_id": f"DQI-{r.randint(1, 25):06d}" if result in ["warning", "fail"] else None
        })

    # Generate pipeline changes (background)
    change_types = ["schema", "pipeline", "source", "definition"]

    for i in range(15):
        dataset = r.choice(datasets)
        change_type = r.choice(change_types)
        changed_at = g.date_between(-60, 0)

        changes.append({
            "change_id": f"PCH-{i + 1:06d}",
            "dataset": dataset,
            "change_type": change_type,
            "description": f"{change_type} change to {dataset}",
            "impact": f"Potential impact on downstream reporting",
            "changed_at": changed_at,
            "changed_by": r.choice(employees),
            "rollback_possible": r.choice([True, False])
        })

    # Generate migration data quality
    object_types = ["purchase_orders", "sales_orders", "shipments", "inventory", "suppliers", "customers"]
    migration_statuses = ["not_started", "in_progress", "complete", "blocked", "remediation"]

    for i, obj_type in enumerate(object_types):
        status = r.choices(migration_statuses, [5, 30, 30, 20, 15])[0]
        completeness = r.randint(75, 100) if status in ["complete", "in_progress"] else r.randint(40, 74)
        timeliness = r.randint(80, 100) if status in ["complete", "in_progress"] else r.randint(50, 79)
        consistency = r.randint(85, 100) if status in ["complete", "in_progress"] else r.randint(55, 84)
        overall = round((completeness + timeliness + consistency) / 3, 1)

        blocking_issue = None
        if status == "blocked":
            blocking_issue = f"Missing reference data or schema mismatch for {obj_type}"

        remediated_at = None
        if status in ["remediation", "complete"]:
            remediated_at = g.date_between(-30, 0)

        migrations.append({
            "migration_id": f"MIG-{i + 1:06d}",
            "object_type": obj_type,
            "status": status,
            "completeness_pct": completeness,
            "timeliness_pct": timeliness,
            "consistency_pct": consistency,
            "overall_score": overall,
            "blocking_issue": blocking_issue,
            "remediated_at": remediated_at,
            "ready_for_cutover": status == "complete" and overall >= 95
        })

    return {
        "data_quality_issues": issues,
        "data_quality_checks": checks,
        "pipeline_changes": changes,
        "migration_data_quality": migrations
    }
