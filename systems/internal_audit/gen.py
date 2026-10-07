def generate(g):
    """Generate audit data realistic for a retail company."""

    # Get reference data
    sites = g.master("sites")
    dc_sites = [s for s in sites if s["site_id"].startswith("DC")]
    employees = g.master("employees")

    # Common audit areas
    audit_areas = [
        "Vendor controls",
        "Purchase order approvals",
        "Bank detail changes",
        "Stock count accuracy",
        "Inventory valuation",
        "Cash handling",
        "Payment authorization",
        "Fixed asset management",
        "Travel and expenses",
        "Journal entries"
    ]

    fraud_types = [
        "Duplicate invoice",
        "Vendor collusion",
        "Order splitting to bypass limits",
        "Fictitious vendor",
        "Unauthorized discount",
        "Invoice manipulation",
        "Ghost employee"
    ]

    # Generate audit_actions (open and completed)
    audit_actions = []
    for i in range(1, 31):
        action_date = g.date_between(540, 90)
        due_date = g.date_between(90, 0) if action_date < g.as_of else g.date_between(0, -60)
        status = g.pick(["open", "completed", "reopened"], [0.5, 0.35, 0.15])
        audit_actions.append({
            "action_id": f"ACT-{i:06d}",
            "description": f"{g.pick(audit_areas)} - {g.fake.sentence(nb_words=4)}",
            "audit_area": g.pick(audit_areas),
            "owner_employee_id": g.pick([e["employee_id"] for e in employees[:20]]),
            "due_date": due_date,
            "status": status,
            "opened_at": g.fake.date_time_this_year(),
            "closed_at": g.fake.date_time_this_year() if status == "completed" else None,
            "evidence": g.fake.paragraph() if status == "completed" else None,
            "updated_at": g.fake.date_time_this_year(),
        })

    # Generate audit_cases (findings from data anomalies)
    audit_cases = []
    for i in range(1, 21):
        opened_date = g.date_between(180, 30)
        audit_cases.append({
            "case_id": f"CASE-{i:06d}",
            "finding_area": g.pick(["Purchase orders", "Vendor payments", "Inventory", "Cash", "Expenses"]),
            "description": g.fake.paragraph(),
            "risk_score": g.rng.randint(20, 95),
            "opened_at": g.fake.date_time(tzinfo=None),
            "status": g.pick(["open", "in_progress", "closed", "escalated"]),
            "assigned_to": g.pick([e["employee_id"] for e in employees[:20]]) if g.rng.random() > 0.3 else None,
            "site_id": g.pick([s["site_id"] for s in dc_sites]) if g.rng.random() > 0.4 else None,
            "estimated_impact_gbp": g.rng.uniform(1000, 150000) if g.rng.random() > 0.5 else None,
            "updated_at": g.fake.date_time_this_year(),
        })

    # Generate audit_engagements (planned and completed)
    audit_engagements = []
    engagement_ids = []
    from datetime import timedelta
    for i in range(1, 16):
        start_date = g.date_between(180, -90)
        end_date = start_date + timedelta(days=g.rng.randint(14, 45))
        engagement_ids.append(f"ENG-{i:06d}")
        audit_engagements.append({
            "engagement_id": f"ENG-{i:06d}",
            "audit_area": g.pick(audit_areas),
            "scope": g.fake.paragraph(nb_sentences=2),
            "site_id": g.pick([s["site_id"] for s in dc_sites]) if g.rng.random() > 0.4 else None,
            "planned_start": start_date,
            "planned_end": end_date,
            "status": g.pick(["planned", "in_progress", "completed", "cancelled"]),
            "lead_auditor": g.pick([e["employee_id"] for e in employees[:20]]),
            "estimated_hours": g.rng.randint(40, 200),
            "created_at": g.fake.date_time_this_year(),
            "updated_at": g.fake.date_time_this_year(),
        })

    # Generate control_test_results
    control_test_results = []
    for i in range(1, 51):
        test_date = g.date_between(120, 1)
        result = g.pick(["pass", "fail", "partial"], [0.65, 0.25, 0.10])
        control_test_results.append({
            "test_id": f"TST-{i:06d}",
            "site_id": g.pick([s["site_id"] for s in dc_sites]),
            "control_area": g.pick([
                "Stock count verification",
                "Payment authorization",
                "Vendor master changes",
                "Cycle counting",
                "Goods receipt matching",
                "Bank reconciliation"
            ]),
            "test_description": g.fake.sentence(nb_words=8),
            "result": result,
            "tested_date": test_date,
            "sample_size": g.rng.randint(20, 200),
            "exceptions_found": g.rng.randint(0, 15) if result != "pass" else 0,
            "root_cause": g.fake.sentence(nb_words=6) if result != "pass" else None,
            "audit_action_id": g.pick(audit_actions)["action_id"] if g.rng.random() > 0.7 else None,
            "created_at": g.fake.date_time_this_year(),
        })

    # Generate audit_findings
    audit_findings = []
    for i in range(1, 31):
        audit_date = g.date_between(365, 30)
        audit_findings.append({
            "finding_id": f"FND-{i:06d}",
            "site_id": g.pick([s["site_id"] for s in dc_sites]),
            "audit_area": g.pick(audit_areas),
            "description": g.fake.paragraph(),
            "severity": g.pick(["high", "medium", "low"], [0.2, 0.4, 0.4]),
            "audit_date": audit_date,
            "status": g.pick(["open", "in_remediation", "resolved", "accepted_risk"]),
            "related_action_id": g.pick(audit_actions)["action_id"] if g.rng.random() > 0.6 else None,
            "created_at": g.fake.date_time_this_year(),
        })

    # Generate fraud_cases
    fraud_cases = []
    for i in range(1, 21):
        detected_date = g.date_between(730, 30)
        fraud_cases.append({
            "fraud_case_id": f"FRD-{i:06d}",
            "case_type": g.pick(fraud_types),
            "description": g.fake.paragraph(),
            "detected_date": detected_date,
            "site_id": g.pick([s["site_id"] for s in dc_sites]) if g.rng.random() > 0.4 else None,
            "estimated_loss_gbp": g.rng.uniform(500, 75000),
            "status": g.pick(["reported", "under_investigation", "closed", "referred_to_authorities"]),
            "created_at": g.fake.date_time_this_year(),
        })

    # Generate assurance_findings (ESG related)
    assurance_findings = []
    esg_categories = ["Scope 2 emissions", "Scope 3 emissions", "Energy efficiency", "Water management", "Waste management"]
    finding_types = ["Data quality", "Methodology", "Boundary change", "Verification issue"]
    for i in range(1, 11):
        audit_date = g.date_between(180, 30)
        assurance_findings.append({
            "assurance_finding_id": f"ASSU-{i:06d}",
            "esg_category": g.pick(esg_categories),
            "description": g.fake.paragraph(),
            "audit_date": audit_date,
            "status": g.pick(["open", "addressed", "under_review"]),
            "finding_type": g.pick(finding_types),
            "created_at": g.fake.date_time_this_year(),
        })

    # Generate audit_universe
    audit_universe = []
    for i, area in enumerate(audit_areas, 1):
        last_audit = g.date_between("-730d", "-30d")
        audit_universe.append({
            "audit_area_id": f"UA-{i:06d}",
            "audit_area": area,
            "description": f"Audit of {area.lower()}",
            "risk_rating": g.pick(["high", "medium", "low"], [0.2, 0.5, 0.3]),
            "last_audit_date": last_audit,
            "audit_frequency_months": g.pick([12, 24, 36]),
            "created_at": g.fake.date_time_this_year(),
        })

    # Generate audit_resource_plan
    audit_resource_plan = []
    current_month = g.as_of.strftime("%Y-%m")
    for emp in employees[:10]:
        for month_offset in range(-2, 4):
            import datetime
            month_date = g.as_of.replace(day=1) + datetime.timedelta(days=32*month_offset)
            month_str = month_date.strftime("%Y-%m")
            audit_resource_plan.append({
                "resource_plan_id": f"RES-{len(audit_resource_plan)+1:06d}",
                "auditor_employee_id": emp["employee_id"],
                "planned_hours_month": g.rng.randint(80, 180),
                "utilization_pct": g.rng.randint(60, 95),
                "planned_areas": ", ".join(g.pick(audit_areas, 2)),
                "plan_month": month_str,
                "created_at": g.fake.date_time_this_year(),
            })

    return {
        "audit_actions": audit_actions,
        "audit_cases": audit_cases,
        "audit_engagements": audit_engagements,
        "control_test_results": control_test_results,
        "audit_findings": audit_findings,
        "fraud_cases": fraud_cases,
        "assurance_findings": assurance_findings,
        "audit_universe": audit_universe,
        "audit_resource_plan": audit_resource_plan,
    }
