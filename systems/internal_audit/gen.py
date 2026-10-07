from datetime import timedelta

AUDITORS = ["EMP-00101", "EMP-00102", "EMP-00103", "EMP-00104"]


def generate(g):
    """Background for the audit system. The question stories live in seed/*.csv."""
    A = g.as_of
    r = g.rng
    dcs = ["DC1", "DC2", "DC3"]

    def ts(d, h=10):
        return f"{d.isoformat()} {h:02d}:00:00"

    # ---- older, unrelated findings and actions (cash, fixed assets, other areas; all > 18 months old)
    old_findings = [
        ("DC1", "Cash handling", "Safe counts at the DC canteen float not independently witnessed.", "low", 640, "resolved"),
        ("DC2", "Fixed asset management", "Three forklifts missing from the asset register after a lease swap.", "medium", 610, "resolved"),
        ("DC3", "Fixed asset management", "Asset tags missing on racking installed in the returns hall.", "low", 590, "resolved"),
        ("DC1", "Journal entries", "Manual journals posted by preparer who also approved them (two cases).", "medium", 575, "resolved"),
        ("DC2", "Cash handling", "Petty cash reimbursed without receipts above the 50 limit.", "low", 560, "accepted_risk"),
        ("DC3", "Journal entries", "Accrual journals lacked supporting calculation.", "low", 545, "resolved"),
    ]
    findings = []
    for i, (site, area, desc, sev, ago, st) in enumerate(old_findings, 1):
        d = A - timedelta(days=ago)
        findings.append({"finding_id": f"FND-{i:06d}", "site_id": site, "audit_area": area, "description": desc,
                         "severity": sev, "audit_date": d, "status": st, "related_action_id": None,
                         "created_at": ts(d + timedelta(days=5))})

    old_actions = [
        ("Witness and sign off canteen float counts weekly", "Cash handling", "EMP-00108", 600, 520),
        ("Reconcile forklift lease register to the asset register", "Fixed asset management", "EMP-00181", 570, 480),
        ("Tag all racking and add to the asset register", "Fixed asset management", "EMP-00239", 550, 470),
        ("Block self-approval of manual journals in the ledger", "Journal entries", "EMP-00088", 540, 450),
    ]
    actions = []
    for i, (desc, area, owner, opened_ago, closed_ago) in enumerate(old_actions, 1):
        o, c = A - timedelta(days=opened_ago), A - timedelta(days=closed_ago)
        actions.append({"action_id": f"ACT-{i:06d}", "description": desc, "audit_area": area, "owner_employee_id": owner,
                        "due_date": c + timedelta(days=7), "status": "completed", "opened_at": ts(o), "closed_at": ts(c, 15),
                        "evidence": "Change implemented and confirmed by the action owner; reviewed by internal audit at the follow-up visit.",
                        "updated_at": ts(c, 15), "status_changed_at": ts(c, 15), "status_note": None})

    # ---- routine control tests in the last two months that pass (background for the stock and valuation tests)
    tests = []
    n = 0
    for site in dcs:
        for area, desc, size in [("Bank reconciliation", "Monthly bank reconciliation tested for completeness and timeliness.", 1),
                                 ("Goods receipt matching", "Goods receipts tested for three-way match (PO, receipt, invoice).", 45)]:
            n += 1
            d = A - timedelta(days=r.randint(25, 70))
            tests.append({"test_id": f"TST-{n:06d}", "site_id": site, "control_area": area, "test_description": desc,
                          "result": "pass", "tested_date": d, "sample_size": size, "exceptions_found": 0,
                          "root_cause": None, "audit_action_id": None, "created_at": ts(d + timedelta(days=1))})

    # ---- a few closed investigation cases from earlier years
    cases = []
    for i, (area, desc, score, site, imp, ago) in enumerate([
        ("Purchase orders", "Two POs raised after the invoice date for the same carton supplier; regularised by procurement.", 38, "DC2", 2100, 400),
        ("Expenses", "Duplicate taxi claims by a shift manager; repaid.", 30, "DC1", 340, 380),
        ("Vendor payments", "Payment run released twice for one supplier; recovered by credit note.", 55, "DC3", 8800, 330),
        ("Inventory", "Pallet write-offs without second signature at one DC; controls reminded.", 44, "DC1", 5600, 300),
    ], 1):
        d = A - timedelta(days=ago)
        cases.append({"case_id": f"CASE-{i:06d}", "finding_area": area, "description": desc, "risk_score": score,
                      "opened_at": ts(d), "status": "closed", "assigned_to": AUDITORS[i % 4], "site_id": site,
                      "estimated_impact_gbp": imp, "updated_at": ts(d + timedelta(days=30))})

    # ---- resource plan: four auditors, 4-week planning periods from two periods ago to a year ahead
    period0 = A - timedelta(days=A.weekday())
    plan = []
    committed = {-2: 90, -1: 90, 0: 88, 1: 85, 2: 70, 3: 55}
    areas = {-2: "Payment authorization", -1: "Payment authorization", 0: "Stock count accuracy; Vendor controls",
             1: "Stock count accuracy; Inventory valuation", 2: "Follow-ups on last year's actions", 3: "Carry-over and report writing"}
    for k in range(-2, 14):
        for j, aud in enumerate(AUDITORS):
            cap = 140
            pct = committed.get(k, 30 + 5 * ((k + j) % 3))
            note = areas.get(k, "Unallocated" if pct <= 35 else "Reserved for ad-hoc requests")
            if aud == "EMP-00103" and k >= 5:
                cap, note = 70, "Half-time: secondment to ESG reporting project"
            if aud == "EMP-00104" and k == -2:
                cap = 80  # joined part way through the period
            if k in (8, 9):  # summer leave
                cap = round(cap * 0.75)
            plan.append({"resource_plan_id": f"RES-{len(plan) + 1:06d}", "auditor_employee_id": aud,
                         "period_start": period0 + timedelta(weeks=4 * k), "capacity_hours": cap,
                         "committed_pct": pct, "planned_areas": note,
                         "created_at": ts(A - timedelta(days=45))})

    return {
        "audit_actions": actions,
        "audit_cases": cases,
        "audit_engagements": [],
        "control_test_results": tests,
        "audit_findings": findings,
        "fraud_cases": [],
        "assurance_findings": [],
        "audit_universe": [],
        "audit_resource_plan": plan,
    }
