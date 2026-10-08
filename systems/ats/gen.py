"""Background recruitment data: requisitions, per-candidate funnel history, agency requests, channel metrics.

Story: DC2 (Daventry) is the hiring outlier. Its interview stage takes ~3x as long as at the other DCs
(interviewer rota gaps on nights) and fewer candidates survive it, so time to hire is roughly double.
"""
from datetime import datetime, timedelta

ROLES = ["Warehouse Operative", "Picker/Packer", "Stock Controller", "Forklift Driver"]
CHANNELS = ["direct", "agency", "job_board", "referral", "internal"]
SHIFTS = ["early", "late", "night", "days", "office"]
STAGES = ["application", "screening", "interview", "offer"]

# mean days spent in each stage, and probability of passing it, per site
PROFILE = {
    "DC1": ([4, 6, 7, 4], [0.75, 0.65, 0.60, 0.88]),
    "DC2": ([5, 7, 22, 6], [0.72, 0.62, 0.50, 0.80]),
    "DC3": ([4, 5, 6, 4], [0.75, 0.65, 0.62, 0.88]),
    "DC4": ([4, 6, 8, 5], [0.72, 0.64, 0.58, 0.85]),
    "DC5": ([4, 6, 7, 4], [0.74, 0.65, 0.60, 0.87]),
}


def generate(g):
    r = g.rng
    requisitions, funnel, agency_requests, metrics = [], [], [], []

    # channel metrics for earlier quarters (current quarter is seeded); lead times were a little shorter earlier
    base = {"internal": (500, 5, 5), "referral": (800, 12, 10), "direct": (1200, 25, 14),
            "job_board": (500, 29, 14), "agency": (2000, 4, 2)}
    mid = 0
    for period, drift, rec in (("2026-Q1", 0.88, 120), ("2026-Q2", 0.94, 40)):
        for role in ROLES:
            for ch in CHANNELS:
                mid += 1
                cost, days, onb = base[ch]
                metrics.append({
                    "metric_id": f"MET-{mid:06d}", "role": role, "recruitment_channel": ch,
                    "cost_per_hire_gbp": round(max(100, r.gauss(cost * drift, cost * 0.08)), 2),
                    "days_to_hire": max(1, round(r.gauss(days * drift, 1.5))),
                    "onboarding_days": onb, "hires_count": r.randint(2, 15), "period": period,
                    "recorded_at": g.as_of - timedelta(days=rec),
                })

    n_fun = 0
    n_req = 0
    for site, (means, passp) in PROFILE.items():
        for role in ROLES:
            for _ in range(3):
                n_req += 1
                age = r.randint(25, 160)
                created = g.as_of - timedelta(days=age)
                req_id = f"REQ-{n_req:06d}"
                cands = []
                for _c in range(r.randint(10, 16)):
                    cage = max(1, age - r.randint(0, 22))   # days since application
                    applied = datetime.combine(g.as_of - timedelta(days=cage), datetime.min.time()) + timedelta(hours=r.randint(8, 17))
                    elapsed = 0
                    days = [None] * 4
                    stage = "hired"
                    furthest = "hired"
                    for i, st in enumerate(STAGES):
                        d = max(1, round(r.gauss(means[i], means[i] * 0.3)))
                        if elapsed + d > cage:          # still sitting in this stage
                            days[i] = cage - elapsed
                            stage = furthest = st
                            break
                        days[i] = d
                        elapsed += d
                        if r.random() > passp[i]:       # drops out here
                            stage, furthest = "rejected", st
                            break
                    moved = applied + timedelta(days=elapsed)   # when it entered its current (or final) stage
                    last = [d for d in days if d is not None][-1]
                    offer_date = start = None
                    if furthest in ("offer", "hired"):
                        offer_date = (applied + timedelta(days=sum(days[:3]))).date()
                    if stage == "hired":
                        start = moved.date() + timedelta(days=r.randint(7, 21))
                    n_fun += 1
                    cands.append({
                        "funnel_id": f"FUN-{n_fun:06d}", "requisition_id": req_id,
                        "candidate_name": g.fake.name(), "recruitment_channel": r.choice(CHANNELS),
                        "stage": stage, "applied_at": applied, "moved_at": moved,
                        "offer_date": offer_date, "start_date": start, "days_in_stage": last,
                        "furthest_stage": furthest,
                        "application_days": days[0], "screening_days": days[1],
                        "interview_days": days[2], "offer_days": days[3],
                        "feedback": {"rejected": f"Not progressed after {furthest}", "hired": "Offer accepted"}.get(stage, f"In {stage}"),
                    })
                funnel.extend(cands)
                hires = [c for c in cands if c["stage"] == "hired"]
                if hires and age > 70:
                    status, headcount = "filled", len(hires)
                    filled = max(c["moved_at"] for c in hires).date()
                else:
                    status = "open" if age < 45 else "in_progress"
                    headcount, filled = r.randint(len(hires) + 1, len(hires) + 5), None
                requisitions.append({
                    "requisition_id": req_id, "site_id": site, "role": role,
                    "headcount_required": headcount, "status": status,
                    "created_at": datetime.combine(created, datetime.min.time()) + timedelta(hours=9),
                    "filled_date": filled, "salary_gbp": 21000 + 500 * r.randint(0, 12),
                    "updated_at": datetime.combine(g.as_of - timedelta(days=r.randint(0, 10)), datetime.min.time()) + timedelta(hours=11),
                })

    # background agency labour requests (story requests are seeded)
    for idx, site in enumerate(PROFILE):
        for k in range(r.randint(1, 2)):
            start = g.as_of + timedelta(days=r.randint(-30, 60))
            end = start + timedelta(days=r.randint(7, 56))
            positions = r.randint(3, 15)
            status = "completed" if end < g.as_of else r.choice(["approved", "in_progress"])
            created = datetime.combine(start - timedelta(days=r.randint(7, 20)), datetime.min.time()) + timedelta(hours=10)
            agency_requests.append({
                "request_id": f"ALR-{idx * 2 + k + 1:06d}", "site_id": site, "shift": r.choice(SHIFTS),
                "start_date": start, "end_date": end, "positions_requested": positions,
                "positions_filled": positions if status == "completed" else r.randint(positions // 2, positions),
                "role": r.choice(ROLES), "status": status, "created_at": created,
                "updated_at": created + timedelta(days=r.randint(1, 5)),
            })

    return {"job_requisitions": requisitions, "recruitment_funnel": funnel,
            "agency_labour_requests": agency_requests, "recruitment_metrics": metrics}
