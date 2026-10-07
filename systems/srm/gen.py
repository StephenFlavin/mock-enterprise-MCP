"""Supplier relationship management data: scorecards, issues, improvement plans, engagement."""
from datetime import datetime, timedelta
import random


def generate(g):
    r = g.rng
    suppliers = g.master("suppliers")
    purchase_orders = g.master("purchase_orders")
    products = g.master("products")

    scorecards = []
    issues = []
    improvement_plans = []
    performance_reviews = []
    engagement_plans = []
    lead_times = []
    factory_capacity = []
    integrations = []

    # Generate 12 months of supplier scorecards for each supplier
    for supplier in suppliers[:30]:  # Focus on top 30 suppliers
        for month_offset in range(-12, 1):
            month_date = g.as_of + timedelta(days=month_offset * 30)
            month_date = month_date.replace(day=1)

            # Performance varies with some trends
            quality = max(50, min(100, int(r.gauss(75, 15))))
            otd = max(50, min(100, int(r.gauss(82, 12))))
            cost_perf = max(50, min(100, int(r.gauss(72, 18))))
            responsiveness = max(50, min(100, int(r.gauss(78, 14))))
            compliance = max(50, min(100, int(r.gauss(80, 12))))

            lead_time = r.randint(14, 56)
            agreed_lead_time = max(14, lead_time - r.randint(-5, 10))

            overall = (quality * 0.25 + otd * 0.25 + cost_perf * 0.2 + responsiveness * 0.15 + compliance * 0.15)

            if overall >= 80:
                status = "strategic"
            elif overall >= 70:
                status = "preferred"
            elif overall >= 60:
                status = "standard"
            elif overall >= 40:
                status = "at_risk"
            else:
                status = "probation"

            scorecards.append({
                "supplier_id": supplier["supplier_id"],
                "scorecard_month": month_date,
                "quality_score": quality,
                "on_time_delivery_pct": otd,
                "cost_performance_score": cost_perf,
                "lead_time_days": lead_time,
                "agreed_lead_time_days": agreed_lead_time,
                "responsiveness_score": responsiveness,
                "compliance_score": compliance,
                "overall_score": round(overall, 1),
                "status_category": status,
                "updated_at": month_date + timedelta(days=5),
            })

    # Generate supplier issues
    for i, supplier in enumerate(suppliers[:20]):
        num_issues = r.randint(0, 3)
        for _ in range(num_issues):
            issue_types = ["quality", "delivery", "cost", "compliance", "responsiveness", "other"]
            severities = ["low", "medium", "high", "critical"]
            statuses = ["open", "investigating", "in_progress", "resolved", "closed"]

            raised = g.days_ago(r.randint(5, 150))
            resolved = None if r.random() > 0.6 else raised + timedelta(days=r.randint(5, 60))
            status = "closed" if resolved else r.choice(["open", "investigating", "in_progress"])

            issues.append({
                "issue_id": f"ISS-{i * 3 + len(issues) + 1:06d}",
                "supplier_id": supplier["supplier_id"],
                "issue_type": r.choice(issue_types),
                "description": f"Issue with {supplier['name']}",
                "severity": r.choice(severities),
                "status": status,
                "assigned_to": r.choice(g.master("employees"))["employee_id"],
                "raised_date": raised,
                "target_resolution_date": raised + timedelta(days=r.randint(14, 60)),
                "resolved_date": resolved,
                "root_cause": "Process deviation" if r.random() > 0.5 else "Capacity constraint",
                "updated_at": resolved or g.as_of,
            })

    # Generate improvement plans
    for i, supplier in enumerate(suppliers[:15]):
        num_plans = r.randint(0, 2)
        for p_idx in range(num_plans):
            plan_types = ["quality", "delivery", "cost", "capacity", "compliance", "sustainability"]
            statuses = ["planned", "active", "in_progress", "completed", "suspended"]

            start = g.days_ago(r.randint(10, 200))
            target_completion = start + timedelta(days=r.randint(60, 180))

            improvement_plans.append({
                "plan_id": f"SIP-{i * 2 + p_idx + 1:06d}",
                "supplier_id": supplier["supplier_id"],
                "plan_name": f"{supplier['name']} improvement",
                "plan_type": r.choice(plan_types),
                "focus_area": "Lead time" if r.random() > 0.5 else "Quality",
                "current_baseline": f"75%",
                "target_metric": "On-time delivery %",
                "target_value": "90%",
                "start_date": start,
                "target_completion_date": target_completion,
                "status": r.choice(statuses),
                "owner_supplier": supplier["name"],
                "owner_internal": r.choice(g.master("employees"))["employee_id"],
                "progress_pct": r.randint(0, 100),
                "updated_at": g.as_of,
            })

    # Generate performance reviews
    review_count = 0
    for i, supplier in enumerate(suppliers[:15]):
        num_reviews = r.randint(1, 3)
        for r_idx in range(num_reviews):
            review_count += 1
            scheduled = g.as_of + timedelta(days=r.randint(-60, 30))
            completed = scheduled if scheduled < g.as_of else None
            status = "completed" if completed else "scheduled"

            performance_reviews.append({
                "review_id": f"SPR-{review_count:06d}",
                "supplier_id": supplier["supplier_id"],
                "review_period": f"Q{(g.as_of.month - 1) // 3 + 1} 2026",
                "scheduled_date": scheduled,
                "completed_date": completed,
                "status": status,
                "meeting_outcome": "Positive progress" if r.random() > 0.3 else "Areas for improvement",
                "internal_owner": r.choice(g.master("employees"))["employee_id"],
                "created_at": scheduled - timedelta(days=30),
                "updated_at": g.as_of,
            })

    # Generate engagement plans
    engagement_count = 0
    programmes = ["emissions", "sustainability", "innovation", "quality"]
    for i, supplier in enumerate(suppliers[:12]):
        for prog_type in r.sample(programmes, k=r.randint(1, 3)):
            engagement_count += 1
            statuses = ["invited", "active", "inactive", "completed"]
            status = r.choice(statuses)

            invited = g.days_ago(r.randint(20, 180)) if status != "invited" else g.as_of
            acceptance = None if status == "invited" else invited + timedelta(days=r.randint(3, 30))
            start = None if status in ["invited", "inactive"] else acceptance + timedelta(days=r.randint(1, 10))

            engagement_plans.append({
                "engagement_record_id": f"ENG-{engagement_count:06d}",
                "supplier_id": supplier["supplier_id"],
                "programme_type": prog_type,
                "engagement_status": status,
                "invitation_sent_date": invited,
                "acceptance_date": acceptance,
                "programme_start_date": start,
                "target_date": start + timedelta(days=365) if start else None,
                "has_science_based_target": r.choice([True, False]),
                "progress_notes": "On track" if status == "active" else "",
                "updated_at": g.as_of,
            })

    # Generate supplier lead time data
    po_count = 0
    for po in purchase_orders[:200]:
        if po["supplier_id"] not in [s["supplier_id"] for s in suppliers[:30]]:
            continue
        if po["status"] in ("cancelled", "draft"):
            continue

        agreed_lead = r.randint(14, 56)
        variance = int(r.gauss(0, 8))
        actual_lead = max(1, agreed_lead + variance)
        delay_days = actual_lead - agreed_lead

        # Process stages
        for stage in ["order_to_factory", "factory_to_port", "port_to_dc"]:
            lead_times.append({
                "po_id": po["po_id"],
                "supplier_id": po["supplier_id"],
                "po_date": po["order_date"],
                "agreed_lead_time_days": agreed_lead,
                "actual_lead_time_days": actual_lead,
                "process_stage": stage,
                "days_variance": delay_days,
                "status": "completed" if po["due_date"] < str(g.as_of) else "on_track",
                "root_cause_delay": "Factory delay" if delay_days > 5 else "",
                "updated_at": g.as_of,
            })
            po_count += 1
            if po_count > 500:
                break

        if po_count > 500:
            break

    # Generate factory capacity data
    for i, supplier in enumerate(suppliers[:20]):
        num_factories = r.randint(1, 3)
        for factory_idx in range(num_factories):
            for month_offset in range(-3, 4):
                month_date = g.as_of + timedelta(days=month_offset * 30)
                month_date = month_date.replace(day=1)

                total_capacity = r.randint(10000, 100000)
                utilization = r.randint(40, 95)
                committed = int(total_capacity * utilization / 100)
                available = total_capacity - committed

                factory_capacity.append({
                    "supplier_id": supplier["supplier_id"],
                    "factory_name": f"{supplier['name']} Factory {factory_idx + 1}",
                    "capacity_month": month_date,
                    "total_capacity_units": total_capacity,
                    "committed_capacity_units": committed,
                    "available_capacity_units": available,
                    "capacity_utilization_pct": round(utilization, 1),
                    "is_alternative_source": factory_idx > 0,
                    "lead_time_days": r.randint(14, 42),
                    "cost_per_unit_gbp": round(r.uniform(1.5, 8.0), 2),
                    "updated_at": month_date,
                })

    # Generate 3PL integration capabilities
    providers = [
        {"name": "DHL Supply Chain", "edi": True, "api": False, "file": True},
        {"name": "Kuehne+Nagel", "edi": True, "api": True, "file": True},
        {"name": "DB Schenker", "edi": True, "api": False, "file": True},
        {"name": "Geodis", "edi": False, "api": True, "file": True},
        {"name": "XPO Logistics", "edi": True, "api": True, "file": True},
    ]

    for i, provider in enumerate(providers):
        integrations.append({
            "provider_id": f"3PL-{i + 1:03d}",
            "provider_name": provider["name"],
            "edi_supported": provider["edi"],
            "api_supported": provider["api"],
            "file_transfer_supported": provider["file"],
            "edi_standards": "EDIFACT, X12" if provider["edi"] else "",
            "api_documentation_url": "https://api.example.com/docs" if provider["api"] else "",
            "file_formats_supported": "CSV, XML, JSON",
            "setup_cost_gbp": r.randint(5000, 30000),
            "monthly_cost_gbp": r.randint(2000, 10000),
            "integration_time_weeks": r.randint(2, 12),
            "technical_contact": g.fake.email(),
            "updated_at": g.as_of,
        })

    return {
        "supplier_scorecards": scorecards,
        "supplier_issues": issues,
        "supplier_improvement_plans": improvement_plans,
        "supplier_performance_reviews": performance_reviews,
        "supplier_engagement_plans": engagement_plans,
        "supplier_lead_times": lead_times,
        "supplier_factory_capacity": factory_capacity,
        "provider_integrations": integrations,
    }
