"""Background audits, findings and corrective actions for every master factory.

Each factory's latest completed audit matches its master audit_rating (and last_audit_date when it is in the
past), so scores agree with master data. Factories with a hand-written story in seed/ get no generated audits.
Background findings are never open-critical, so planted critical findings are the only ones to find.
"""
from datetime import datetime, timedelta

STORY = {"FAC-0001", "FAC-0121", "FAC-0087", "FAC-0107", "FAC-0137", "FAC-0097", "FAC-0098",
         "FAC-0035", "FAC-0042", "FAC-0024", "FAC-0028"}
ORDER = ["A", "B", "C", "D"]
CATS = ["working hours", "wage calculation", "fire safety", "safe working conditions",
        "freedom of association", "discrimination", "documentation", "waste handling"]


def _ts(d):
    return datetime.combine(d, datetime.min.time()) + timedelta(hours=9)


def generate(g):
    r = g.rng
    factories = g.master("factories")
    auditors = [e for e in g.master("employees")
                if any(k in e.get("role", "").lower() for k in ("audit", "compliance", "quality", "sustainab"))]
    if not auditors:
        auditors = g.master("employees")[:10]
    audits, findings, caps, requests = [], [], [], []

    for f in factories:
        fid = f["factory_id"]
        if fid in STORY:
            continue
        rating = f["audit_rating"] or "B"
        try:
            latest = datetime.strptime(f["last_audit_date"][:10], "%Y-%m-%d").date()
        except ValueError:
            latest = g.days_ago(300)
        if latest > g.as_of:
            latest = g.days_ago(30)
        n = r.choice([1, 2, 2, 3])
        dates = [latest - timedelta(days=364 * k) for k in range(n)][::-1]
        scores = []
        idx = ORDER.index(rating)
        for k in range(n - 1):
            scores.append(ORDER[max(0, min(3, idx + r.choice([-1, 0, 0, 1])))])
        scores.append(rating)
        for i, (d, sc) in enumerate(zip(dates, scores)):
            aid = f"AUD-{len(audits) + 1:06d}"
            audits.append({
                "audit_id": aid, "factory_id": fid, "supplier_id": f["supplier_id"], "audit_date": d,
                "auditor_id": r.choice(auditors)["employee_id"], "audit_type": r.choice(["social", "ethical", "quality"]),
                "overall_score": sc, "status": "completed",
                "notes": f"Audit at {f['name']}. " + ("Good compliance overall." if sc in "AB" else "Several areas for improvement noted."),
                "created_at": _ts(d + timedelta(days=1)),
            })
            nf = {"A": r.choice([0, 1]), "B": r.choice([1, 2]), "C": r.choice([2, 3]), "D": r.choice([3, 4])}[sc]
            for _ in range(nf):
                fnd = f"FND-{len(findings) + 1:06d}"
                cat = r.choice(CATS)
                sev = r.choices(["major", "minor"], [0.3, 0.7])[0]
                is_last = i == n - 1
                if is_last and sc in "CD" and r.random() < 0.5:
                    status = r.choice(["open", "in_progress"])
                else:
                    status = "closed"
                findings.append({
                    "finding_id": fnd, "audit_id": aid, "factory_id": fid, "category": cat, "severity": sev,
                    "description": f"{cat.capitalize()}: {sev} gap identified during audit",
                    "status": status, "is_repeat": False, "found_date": d, "created_at": _ts(d + timedelta(days=1)),
                })
                due = d + timedelta(days=r.randint(30, 75))
                if status == "closed":
                    if sev == "minor" and r.random() < 0.5:
                        continue
                    cs, comp = "closed", min(due, g.as_of) - timedelta(days=r.randint(0, 6))
                else:
                    cs = "overdue" if due < g.as_of else r.choice(["open", "in_progress"])
                    comp = None
                caps.append({
                    "corrective_action_id": f"CAP-{len(caps) + 1:06d}", "finding_id": fnd, "factory_id": fid,
                    "supplier_id": f["supplier_id"], "description": f"Corrective action for {cat}",
                    "assigned_to": r.choice(auditors)["employee_id"], "due_date": due, "status": cs,
                    "completed_date": comp, "created_at": _ts(d + timedelta(days=1)),
                    "updated_at": _ts(comp or min(due, g.as_of)),
                })

    pool = [f for f in factories if f["factory_id"] not in STORY]
    for i in range(10):
        f = r.choice(pool)
        d = g.days_ago(r.randint(5, 60))
        requests.append({
            "audit_request_id": f"AUR-{i + 1:06d}", "factory_id": f["factory_id"], "supplier_id": f["supplier_id"],
            "requested_date": d, "audit_type": r.choice(["social", "ethical", "quality"]),
            "status": r.choices(["pending", "scheduled", "completed", "cancelled"], [0.3, 0.3, 0.3, 0.1])[0],
            "requested_by": r.choice(auditors)["employee_id"], "created_at": _ts(d),
        })
    return {"audits": audits, "audit_findings": findings, "corrective_actions": caps,
            "audit_requests": requests, "corrective_action_reminders": []}
