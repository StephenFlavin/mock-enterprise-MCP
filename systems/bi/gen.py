"""BI & Dashboards analytics data: store and product performance vs plan."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng

    # Get stores and products from master
    sites = [s for s in g.master("sites") if s["type"] == "store"]
    products = [p for p in g.master("products") if p["status"] in ("active", "new")][:100]
    employees = g.master("employees")

    store_perf = []
    product_perf = []
    store_targets = []
    product_targets = []
    dq_issues = []
    reports = []

    # Generate store performance for last 4 periods (months)
    for months_back in range(4, 0, -1):
        period_date = g.days_ago(months_back * 30)
        period = f"{period_date.year}-{period_date.month:02d}"

        for site in sites[:50]:  # Top 50 stores
            region = site["region"]
            cluster = site["cluster"]

            # More sales for cluster A, less for D
            cluster_factor = {"A": 1.2, "B": 1.0, "C": 0.85, "D": 0.6}.get(cluster, 1.0)

            # Base sales
            base_sales_units = int(r.gauss(500 * cluster_factor, 100 * cluster_factor))
            sales_gbp = base_sales_units * r.gauss(45, 5)

            # Margin varies by store
            margin_pct = r.gauss(32, 4)

            # Availability typically 95-98%
            availability_pct = r.gauss(96, 2)

            # Shrink 1-3%
            shrink_pct = r.gauss(1.5, 0.5)

            # Labour cost 8-12% of sales
            labour_cost_pct = r.gauss(10, 1)

            store_perf.append({
                "site_id": site["site_id"],
                "period": period,
                "sales_units": max(100, base_sales_units),
                "sales_gbp": max(4500, sales_gbp),
                "margin_pct": max(18, margin_pct),
                "availability_pct": min(99, max(92, availability_pct)),
                "shrink_pct": max(0.5, min(3, shrink_pct)),
                "labour_cost_pct": max(7, min(14, labour_cost_pct)),
                "updated_at": datetime.combine(period_date, datetime.min.time())
            })

            # Add target
            store_targets.append({
                "site_id": site["site_id"],
                "period": period,
                "sales_units_target": int(store_perf[-1]["sales_units"] * r.uniform(0.95, 1.05)),
                "sales_gbp_target": store_perf[-1]["sales_gbp"] * r.uniform(0.95, 1.05),
                "margin_pct_target": store_perf[-1]["margin_pct"] * r.uniform(0.95, 1.0),
                "updated_at": datetime.combine(period_date, datetime.min.time())
            })

    # Generate product performance for last 4 periods
    for months_back in range(4, 0, -1):
        period_date = g.days_ago(months_back * 30)
        period = f"{period_date.year}-{period_date.month:02d}"

        for prod in products[:40]:  # Top 40 products
            # ABC velocity
            velocity_factor = {"A": 1.3, "B": 1.0, "C": 0.6}.get(prod.get("abc_class", "B"), 1.0)

            sales_units = int(r.gauss(300 * velocity_factor, 60 * velocity_factor))
            sales_gbp = sales_units * float(prod["retail_price_gbp"]) * r.uniform(0.7, 0.95)  # Net of markdown

            margin_pct = r.gauss(35, 5)
            returns_pct = r.gauss(2, 1)
            avg_rating = r.gauss(4.2, 0.4)

            product_perf.append({
                "sku": prod["sku"],
                "period": period,
                "sales_units": max(10, sales_units),
                "sales_gbp": max(500, sales_gbp),
                "margin_pct": max(15, margin_pct),
                "returns_pct": max(0.5, min(5, returns_pct)),
                "avg_rating": max(2, min(5, avg_rating)),
                "updated_at": datetime.combine(period_date, datetime.min.time())
            })

            # Add target
            product_targets.append({
                "sku": prod["sku"],
                "period": period,
                "sales_units_target": int(product_perf[-1]["sales_units"] * r.uniform(0.90, 1.10)),
                "sales_gbp_target": product_perf[-1]["sales_gbp"] * r.uniform(0.90, 1.10),
                "margin_pct_target": product_perf[-1]["margin_pct"] * r.uniform(0.95, 1.0),
                "updated_at": datetime.combine(period_date, datetime.min.time())
            })

    # Data quality issues
    dq_datasets = ["store_performance", "product_performance", "sales_weekly", "dc_stock"]
    dq_types = ["missing_data", "duplicate", "incorrect_value", "late_update", "schema_mismatch"]

    for i in range(8):
        created_days_ago = r.randint(5, 45)
        resolved = r.choice([True, False, False, False])  # 25% resolved
        dq_issues.append({
            "dq_issue_id": f"DQ-{900000 + i + 1:06d}",
            "dataset": r.choice(dq_datasets),
            "issue_type": r.choice(dq_types),
            "description": f"Data inconsistency in {r.choice(dq_datasets)} affecting reporting",
            "owner_id": r.choice(employees)["employee_id"],
            "severity": r.choices(["critical", "high", "medium", "low"], [0.2, 0.3, 0.3, 0.2])[0],
            "affected_reports": "store_performance_summary;regional_analysis",
            "created_at": g.days_ago(created_days_ago),
            "resolved_at": g.days_ago(created_days_ago - 3) if resolved else None
        })

    # Scheduled reports
    report_types = [
        "Store Performance Summary",
        "Range Review Report",
        "Regional Analysis",
        "Product Performance",
        "Data Quality Dashboard"
    ]

    for i, rtype in enumerate(report_types):
        reports.append({
            "report_id": f"RPT-{900000 + i + 1:06d}",
            "report_type": rtype,
            "recipient_emails": "manager@company.com;director@company.com",
            "frequency": r.choice(["daily", "weekly", "monthly", "quarterly"]),
            "active": True,
            "created_at": g.days_ago(60)
        })

    return {
        "store_performance": store_perf,
        "product_performance": product_perf,
        "performance_targets": targets,
        "data_quality_issues": dq_issues,
        "scheduled_reports": reports
    }
