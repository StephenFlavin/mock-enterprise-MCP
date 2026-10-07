"""Generate audit records and findings for factories over the past 2 years."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    factories = g.master("factories")
    employees = g.master("employees")

    # Filter to employees in relevant roles for auditors
    auditors = [e for e in employees if "audit" in e.get("role", "").lower() or
                "compliance" in e.get("role", "").lower() or
                "quality" in e.get("role", "").lower()]
    if not auditors:
        auditors = employees[:10]  # fallback

    audits = []
    audit_findings = []
    corrective_actions = []
    audit_requests = []

    # Generate audits: 2-4 per factory over past 100 weeks (2 years)
    for factory in factories[:30]:  # Sample of factories
        supplier_id = factory["supplier_id"]
        factory_id = factory["factory_id"]
        audit_count = r.randint(2, 4)

        for i in range(audit_count):
            # Spread audits over time
            weeks_ago = 100 - (i * (100 // audit_count)) + r.randint(-2, 2)
            audit_date = g.days_ago(weeks_ago * 7).date()

            audit_id = f"AUD-{len(audits) + 1:06d}"
            audit_score = r.choices(["A", "B", "C", "D"], [0.4, 0.35, 0.2, 0.05])[0]
            auditor = r.choice(auditors)

            audit_record = {
                "audit_id": audit_id,
                "factory_id": factory_id,
                "supplier_id": supplier_id,
                "audit_date": audit_date,
                "auditor_id": auditor["employee_id"],
                "audit_type": r.choice(["social", "ethical", "quality"]),
                "overall_score": audit_score,
                "status": "completed",
                "notes": f"Audit conducted at {factory['name']}. {'Good compliance overall.' if audit_score in ['A', 'B'] else 'Several areas for improvement noted.'}",
                "created_at": datetime.combine(audit_date, datetime.min.time()) + timedelta(days=1)
            }
            audits.append(audit_record)

            # Generate findings: 0-8 per audit, more for lower scores
            finding_count = r.choices([0, 1, 2, 3, 4, 5, 6, 7, 8],
                                     [0.05, 0.1, 0.15, 0.15, 0.2, 0.15, 0.1, 0.08, 0.02])[0]
            if audit_score == "C":
                finding_count = min(8, finding_count + 2)
            elif audit_score == "D":
                finding_count = min(8, finding_count + 4)

            for j in range(finding_count):
                finding_id = f"FND-{len(audit_findings) + 1:06d}"
                category = r.choice(["working hours", "wage calculation", "fire safety",
                                    "child labor", "forced labor", "discrimination",
                                    "freedom of association", "safe working conditions"])

                finding_status = r.choices(["open", "in_progress", "closed", "reopened"],
                                          [0.3, 0.2, 0.4, 0.1])[0]
                is_repeat = r.choice([True, False]) if i > 0 and finding_status in ["reopened"] else False

                finding = {
                    "finding_id": finding_id,
                    "audit_id": audit_id,
                    "factory_id": factory_id,
                    "category": category,
                    "severity": r.choices(["critical", "major", "minor"], [0.15, 0.35, 0.5])[0],
                    "description": f"Finding: {category} issue identified during audit",
                    "status": finding_status,
                    "is_repeat": is_repeat,
                    "found_date": audit_date,
                    "created_at": datetime.combine(audit_date, datetime.min.time()) + timedelta(days=1)
                }
                audit_findings.append(finding)

                # Generate corrective actions for open/in_progress findings
                if finding_status in ["open", "in_progress"]:
                    cap_id = f"CAP-{len(corrective_actions) + 1:06d}"
                    assigned = r.choice(auditors)
                    due_offset = r.randint(14, 90)
                    due_date = audit_date + timedelta(days=due_offset)

                    cap_status = "overdue" if due_date < g.as_of else r.choice(["open", "in_progress"])

                    cap = {
                        "corrective_action_id": cap_id,
                        "finding_id": finding_id,
                        "factory_id": factory_id,
                        "supplier_id": supplier_id,
                        "description": f"Corrective action for: {category}",
                        "assigned_to": assigned["employee_id"],
                        "due_date": due_date,
                        "status": cap_status,
                        "completed_date": None if cap_status != "closed" else due_date + timedelta(days=1),
                        "created_at": datetime.combine(audit_date, datetime.min.time()) + timedelta(days=1),
                        "updated_at": datetime.combine(audit_date, datetime.min.time()) + timedelta(days=1)
                    }
                    corrective_actions.append(cap)

    # Generate audit requests
    for i in range(15):
        factory = r.choice(factories[:20])
        aur_id = f"AUR-{i + 1:06d}"
        requested_date = g.days_ago(r.randint(5, 60)).date()
        auditor = r.choice(auditors)

        audit_request = {
            "audit_request_id": aur_id,
            "factory_id": factory["factory_id"],
            "supplier_id": factory["supplier_id"],
            "requested_date": requested_date,
            "audit_type": r.choice(["social", "ethical", "quality"]),
            "status": r.choices(["pending", "scheduled", "completed", "cancelled"], [0.2, 0.3, 0.4, 0.1])[0],
            "requested_by": auditor["employee_id"],
            "created_at": datetime.combine(requested_date, datetime.min.time())
        }
        audit_requests.append(audit_request)

    return {
        "audits": audits,
        "audit_findings": audit_findings,
        "corrective_actions": corrective_actions,
        "audit_requests": audit_requests
    }
