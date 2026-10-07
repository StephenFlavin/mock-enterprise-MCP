"""Background recruitment data: job requisitions, funnel progression, and agency requests."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    roles = [
        "Warehouse Operative",
        "Picker/Packer",
        "Stock Controller",
        "Forklift Driver",
        "Supervisor",
        "Store Manager",
    ]
    recruitment_channels = ["direct", "agency", "job_board", "referral", "internal"]
    sites = ["DC1", "DC2", "DC3", "DC4", "DC5", "ST001", "ST100", "ST200"]
    shifts = ["early", "late", "night", "days", "office"]

    requisitions = []
    funnel = []
    agency_requests = []
    metrics = []

    # Generate historical recruitment metrics (for cost and lead time lookups)
    for idx, role in enumerate(roles):
        for channel in recruitment_channels:
            metric_id = f"MET-{idx * len(recruitment_channels) + recruitment_channels.index(channel) + 1:06d}"
            # Vary costs and lead times by channel
            if channel == "internal":
                cost = r.gauss(500, 100)
                days = r.gauss(5, 2)
            elif channel == "referral":
                cost = r.gauss(800, 150)
                days = r.gauss(12, 3)
            elif channel == "direct":
                cost = r.gauss(1200, 300)
                days = r.gauss(25, 5)
            elif channel == "job_board":
                cost = r.gauss(500, 100)
                days = r.gauss(28, 6)
            else:  # agency
                cost = r.gauss(2000, 400)
                days = r.gauss(4, 1)

            metrics.append({
                "metric_id": metric_id,
                "role": role,
                "recruitment_channel": channel,
                "cost_per_hire_gbp": max(100, cost),
                "days_to_hire": max(1, int(days)),
                "hires_count": r.randint(2, 15),
                "period": "2026-Q3",
                "recorded_at": g.as_of - timedelta(days=r.randint(7, 60))
            })

    # Generate job requisitions
    for site_idx, site in enumerate(sites[:5]):  # Main sites
        for role_idx, role in enumerate(roles[:4]):  # Main roles
            req_id = f"REQ-{site_idx * len(roles) + role_idx + 1:06d}"

            # Some are open, some filled
            days_old = r.randint(10, 90)
            created_at = g.as_of - timedelta(days=days_old)

            status = r.choices(["open", "in_progress", "filled"], [0.2, 0.3, 0.5])[0]
            filled_date = None
            if status == "filled":
                days_to_fill = r.randint(15, 60)
                filled_date = (created_at + timedelta(days=days_to_fill)).date()

            requisitions.append({
                "requisition_id": req_id,
                "site_id": site,
                "role": role,
                "headcount_required": r.randint(1, 8),
                "status": status,
                "created_at": created_at,
                "filled_date": filled_date,
                "salary_gbp": 20000 + r.randint(0, 25000),
                "updated_at": created_at + timedelta(days=r.randint(1, days_old))
            })

    # Generate recruitment funnel entries for each requisition
    for req_idx, req in enumerate(requisitions):
        # Create a funnel for this requisition with multiple candidates
        num_applicants = r.randint(8, 30)
        for app_idx in range(num_applicants):
            funnel_id = f"FUN-{req_idx * 30 + app_idx + 1:06d}"

            # Determine stage progression - more drop off at each stage
            stage_progression = r.random()
            if stage_progression < 0.2:
                stage = "rejected"
                days_in_stage = r.randint(1, 10)
            elif stage_progression < 0.5:
                stage = "application"
                days_in_stage = r.randint(1, 30)
            elif stage_progression < 0.65:
                stage = "screening"
                days_in_stage = r.randint(2, 20)
            elif stage_progression < 0.80:
                stage = "interview"
                days_in_stage = r.randint(3, 15)
            elif stage_progression < 0.95:
                stage = "offer"
                days_in_stage = r.randint(1, 7)
            else:
                stage = "hired"
                days_in_stage = r.randint(1, 5)

            applied_at = req["created_at"] + timedelta(days=r.randint(0, 10))
            moved_at = applied_at + timedelta(days=days_in_stage)

            offer_date = None
            start_date = None
            if stage in ["offer", "hired"]:
                offer_date = moved_at.date()
                start_date = offer_date + timedelta(days=r.randint(7, 21))

            funnel.append({
                "funnel_id": funnel_id,
                "requisition_id": req["requisition_id"],
                "candidate_name": g.fake.name(),
                "recruitment_channel": r.choice(recruitment_channels),
                "stage": stage,
                "applied_at": applied_at,
                "moved_at": moved_at,
                "offer_date": offer_date,
                "start_date": start_date,
                "days_in_stage": days_in_stage,
                "feedback": None if stage == "application" else f"Stage: {stage}"
            })

    # Generate agency labour requests
    for idx, site in enumerate(sites[:5]):
        for req_idx in range(r.randint(0, 3)):
            alr_id = f"ALR-{idx * 3 + req_idx + 1:06d}"

            # Peak season or off-season
            start_date = g.as_of + timedelta(days=r.randint(0, 60))
            duration = r.randint(7, 56)  # 1-8 weeks
            end_date = start_date + timedelta(days=duration)

            positions = r.randint(3, 25)
            filled = r.randint(int(positions * 0.6), positions)

            status = r.choices(["submitted", "approved", "in_progress", "completed"], [0.1, 0.3, 0.4, 0.2])[0]
            if status == "submitted":
                created_at = g.as_of - timedelta(days=r.randint(0, 5))
            elif status == "approved":
                created_at = g.as_of - timedelta(days=r.randint(3, 15))
            elif status == "in_progress":
                created_at = start_date - timedelta(days=r.randint(1, 10))
            else:  # completed
                created_at = end_date - timedelta(days=r.randint(5, 20))

            agency_requests.append({
                "request_id": alr_id,
                "site_id": site,
                "shift": r.choice(shifts),
                "start_date": start_date.date(),
                "end_date": end_date.date(),
                "positions_requested": positions,
                "positions_filled": filled,
                "role": r.choice(roles),
                "status": status,
                "created_at": created_at,
                "updated_at": created_at + timedelta(days=r.randint(0, 20))
            })

    return {
        "job_requisitions": requisitions,
        "recruitment_funnel": funnel,
        "agency_labour_requests": agency_requests,
        "recruitment_metrics": metrics
    }
