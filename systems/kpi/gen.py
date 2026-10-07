"""Generate KPI targets, actuals, variances, site metrics, and circularity data."""
from datetime import datetime, timedelta
import math


def generate(g):
    r = g.rng
    fake = g.fake
    as_of = g.as_of

    # KPI domains and definitions
    kpi_definitions = [
        {"id": "KPI-0001", "name": "On-Time-In-Full (OTIF)", "domain": "service", "unit": "%", "target": 95.5},
        {"id": "KPI-0002", "name": "Cost per Unit Handled", "domain": "cost", "unit": "£", "target": 2.35},
        {"id": "KPI-0003", "name": "Inventory Accuracy", "domain": "inventory", "unit": "%", "target": 98.5},
        {"id": "KPI-0004", "name": "Stock Turnover Days", "domain": "inventory", "unit": "days", "target": 28},
        {"id": "KPI-0005", "name": "Lost Time Injury Frequency", "domain": "safety", "unit": "rate", "target": 0.5},
        {"id": "KPI-0006", "name": "Quality First Pass", "domain": "quality", "unit": "%", "target": 96.5},
        {"id": "KPI-0007", "name": "Supplier OTIF", "domain": "service", "unit": "%", "target": 94.0},
        {"id": "KPI-0008", "name": "GHG Emissions per Unit", "domain": "sustainability", "unit": "kg CO2e", "target": 0.85},
        {"id": "KPI-0009", "name": "Waste Diversion Rate", "domain": "sustainability", "unit": "%", "target": 72.0},
        {"id": "KPI-0010", "name": "DC Throughput", "domain": "service", "unit": "units/hr", "target": 850},
    ]

    sites = [s["site_id"] for s in g.master("sites") if s["type"] in ["dc", "store"]]

    # Generate KPI targets
    kpi_targets = []
    for kpi in kpi_definitions:
        variation = r.uniform(0.95, 1.05)
        kpi_targets.append({
            "kpi_id": kpi["id"],
            "kpi_name": kpi["name"],
            "domain": kpi["domain"],
            "frequency": "monthly",
            "unit": kpi["unit"],
            "target_value": round(kpi["target"] * variation, 2),
            "min_threshold": round(kpi["target"] * 0.90, 2),
            "yellow_threshold": round(kpi["target"] * 0.95, 2),
            "effective_from": datetime.combine(g.as_of, datetime.min.time()),
            "updated_at": datetime.combine(g.as_of, datetime.min.time()),
        })

    # Generate KPI actuals - daily for last 60 days
    kpi_actuals = []
    ytd_accums = {kpi["id"]: 0 for kpi in kpi_definitions}
    for kpi in kpi_definitions:
        for days_ago in range(60, -1, -1):
            mdate = as_of - timedelta(days=days_ago)
            # Generate realistic actuals with some variance
            base_target = next(k["target"] for k in kpi_definitions if k["id"] == kpi["id"])
            if kpi["domain"] == "cost":
                actual = round(base_target * r.uniform(0.95, 1.10), 2)
            elif kpi["domain"] == "safety":
                actual = round(base_target * r.uniform(0.7, 1.4), 2)
            else:
                actual = round(base_target * r.uniform(0.92, 1.05), 1)

            ytd_accums[kpi["id"]] += actual
            kpi_actuals.append({
                "kpi_id": kpi["id"],
                "measured_date": mdate,
                "actual_value": actual,
                "ytd_value": round(ytd_accums[kpi["id"]], 2),
                "vs_target_pct": round((actual / base_target) * 100, 1),
                "data_quality": r.choice(["good", "good", "good", "estimated"]),
                "notes": "" if r.random() > 0.1 else fake.sentence(nb_words=4),
            })

    # Generate variances for last 6 months
    kpi_variances = []
    for idx, kpi in enumerate(kpi_definitions):
        for month_ago in range(6):
            period_end = as_of - timedelta(days=30 * month_ago)
            period_start = period_end - timedelta(days=30)
            target = next(k["target"] for k in kpi_definitions if k["id"] == kpi["id"])

            # Actuals vary around target
            actual = target * r.uniform(0.90, 1.08)
            variance = actual - target
            variance_pct = (variance / target) * 100

            if abs(variance_pct) > 5:
                severity = "severe" if abs(variance_pct) > 10 else "moderate"
            elif abs(variance_pct) > 2:
                severity = "minor"
            else:
                severity = "on_track"

            if severity != "on_track":
                kpi_variances.append({
                    "variance_id": f"VAR-{len(kpi_variances) + 1:06d}",
                    "kpi_id": kpi["id"],
                    "period_start": period_start,
                    "period_end": period_end,
                    "target_value": round(target, 2),
                    "actual_value": round(actual, 2),
                    "variance_value": round(variance, 2),
                    "variance_pct": round(variance_pct, 1),
                    "severity": severity,
                    "status": r.choice(["open", "investigating", "root_cause_identified", "action_raised"]),
                    "updated_at": datetime.combine(as_of, datetime.min.time()),
                })

    # Generate site metrics
    site_metrics = []
    for site in sites:
        # Generate metrics for last 30 days
        for days_ago in range(30, -1, -1):
            mdate = as_of - timedelta(days=days_ago)
            site_metrics.append({
                "site_id": site,
                "measured_date": mdate,
                "service_score": round(r.uniform(85, 99), 1),
                "cost_per_unit_gbp": round(r.uniform(1.8, 3.2), 2),
                "safety_ltif": round(r.uniform(0.2, 1.2), 2),
                "quality_first_pass_pct": round(r.uniform(92, 99), 1),
                "stock_accuracy_pct": round(r.uniform(95, 99.5), 1),
                "oh_es": r.randint(-50, 50),
            })

    # Generate circularity targets
    channels = ["Reuse", "Repair", "Recycle", "Refurbish"]
    circularity_targets = []
    for idx, channel in enumerate(channels):
        circularity_targets.append({
            "channel_id": f"CHN-{idx + 1:06d}",
            "channel_name": channel,
            "units_collected_target": r.randint(5000, 50000),
            "value_recovered_target_gbp": round(r.uniform(10000, 150000), 2),
            "handling_cost_per_unit_gbp": round(r.uniform(0.5, 2.5), 2),
            "effective_from": datetime.combine(as_of, datetime.min.time()),
        })

    # Generate issue root causes
    issue_root_causes = []
    for var in kpi_variances[:10]:  # Root causes for severe variances
        issue_root_causes.append({
            "cause_id": f"CAS-{len(issue_root_causes) + 1:06d}",
            "variance_id": var["variance_id"],
            "kpi_id": var["kpi_id"],
            "root_cause": fake.sentence(nb_words=6),
            "contributing_factors": "; ".join([fake.sentence(nb_words=4) for _ in range(2)]),
            "department_responsible": r.choice(["Supply Chain", "Operations", "Quality", "HR", "Logistics"]),
            "severity": var["severity"],
            "identified_at": datetime.combine(as_of - timedelta(days=7), datetime.min.time()),
            "target_fix_date": (as_of + timedelta(days=r.randint(7, 30))).isoformat(),
            "status": r.choice(["open", "action_raised", "in_progress"]),
            "updated_at": datetime.combine(as_of, datetime.min.time()),
        })

    # Generate alert thresholds
    alert_thresholds = []
    for idx, kpi in enumerate(kpi_definitions):
        target = kpi["target"]
        for level, pct in [("red", 0.85), ("amber", 0.92)]:
            alert_thresholds.append({
                "alert_id": f"ALT-{len(alert_thresholds) + 1:06d}",
                "kpi_id": kpi["id"],
                "alert_level": level,
                "threshold_value": round(target * pct, 2),
                "alert_on": "below",
                "enabled": True,
                "last_breached_at": None if r.random() > 0.3 else datetime.combine(as_of - timedelta(days=r.randint(1, 14)), datetime.min.time()),
                "updated_at": datetime.combine(as_of, datetime.min.time()),
            })

    return {
        "kpi_targets": kpi_targets,
        "kpi_actuals": kpi_actuals,
        "kpi_variances": kpi_variances,
        "site_metrics": site_metrics,
        "circularity_targets": circularity_targets,
        "issue_root_causes": issue_root_causes,
        "alert_thresholds": alert_thresholds,
    }
