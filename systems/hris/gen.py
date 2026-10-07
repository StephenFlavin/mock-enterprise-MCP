"""HR data: headcount requisitions, absence records, leavers with exit interviews, skills, commute and market rates."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    employees = g.master("employees")
    sites = [s for s in g.master("sites") if s["type"] == "dc"]

    # Filter to active employees
    active_emps = [e for e in employees if e["status"] == "active"]
    leaver_emps = [e for e in employees if e["status"] == "leaver"]

    requisitions, pay_reviews, absences = [], [], []
    leavers_list, skills, commutes, market_rates_list = [], [], [], []

    # Generate headcount requisitions
    roles = ["Warehouse Operative", "Picker", "Packer", "Forklift Operator", "Team Lead", "Supervisor"]
    req_counter = 0
    for site in sites[:3]:  # DC1, DC2, DC3
        for _ in range(r.randint(1, 3)):
            req_counter += 1
            days_out = r.randint(7, 90)
            requisitions.append({
                "req_id": f"REQ-{req_counter:06d}",
                "site_id": site["site_id"],
                "role": r.choice(roles),
                "headcount": r.randint(5, 30),
                "employment_type": r.choice(["permanent", "agency", "temporary"]),
                "shift": r.choice(["early", "late", "night"]),
                "required_by": g.as_of + timedelta(days=days_out),
                "status": r.choices(["draft", "approved", "filled"], [0.2, 0.4, 0.4])[0],
                "created_at": g.as_of - timedelta(days=r.randint(1, 30)),
                "filled_count": r.randint(0, 15) if r.random() > 0.5 else 0,
                "required_skills": r.choice([
                    "forklift certification",
                    "forklift certification; CSCS",
                    "CSCS; manual handling",
                    "team leadership",
                    ""
                ])
            })

    # Generate pay review requests
    prr_counter = 0
    for site in sites[:3]:
        for _ in range(r.randint(1, 3)):
            prr_counter += 1
            pay_reviews.append({
                "review_id": f"PRR-{prr_counter:06d}",
                "site_id": site["site_id"],
                "role": r.choice(roles),
                "shift": r.choice(["early", "late", "night", None]),
                "reason": r.choice([
                    "market rate gap identified",
                    "retention risk - high turnover",
                    "competitive pressure from local employers",
                    "employee grievance on pay equity",
                    "retention strategy for key roles"
                ]),
                "created_at": g.as_of - timedelta(days=r.randint(1, 60)),
                "created_by": r.choice([e["employee_id"] for e in active_emps if "manager" in e["role"].lower()])[:1] or [active_emps[0]["employee_id"]][0] if active_emps else "EMP-00001",
                "status": r.choices(["submitted", "under_review", "approved", "implemented"], [0.3, 0.3, 0.2, 0.2])[0]
            })

    # Generate absence records
    abs_counter = 0
    for site in sites:
        site_emps = [e for e in active_emps if e["site_id"] == site["site_id"]]
        for _ in range(r.randint(5, 15)):
            emp = r.choice(site_emps) if site_emps else active_emps[0]
            abs_counter += 1
            abs_date = g.as_of - timedelta(days=r.randint(1, 90))
            absences.append({
                "absence_id": f"ABS-{abs_counter:06d}",
                "employee_id": emp["employee_id"],
                "site_id": emp["site_id"],
                "shift_pattern": emp["shift"],
                "absence_date": abs_date,
                "hours_absent": r.choice([4, 8, 8, 8, 8]),  # Bias towards full days
                "reason": r.choices(["sickness", "annual_leave", "unpaid_leave", "other"], [0.4, 0.4, 0.1, 0.1])[0]
            })

    # Generate leavers with exit interview data
    lvr_counter = 0
    exit_themes_options = [
        "Pay; Commute distance",
        "Management; Shift pattern",
        "Career development",
        "Work-life balance",
        "Overtime expectations",
        "Health and safety concerns",
        "Better offer elsewhere",
        "Relocation",
        "Family circumstances",
        "Pay; Limited progression"
    ]
    exit_reasons = [
        "Better opportunity",
        "Pay and benefits",
        "Commute",
        "Management style",
        "Work-life balance",
        "Career development",
        "Health",
        "Personal reasons",
        "Relocation",
        "Shift pattern"
    ]

    for leaver in leaver_emps[:len(leaver_emps)]:
        lvr_counter += 1
        tenure = (datetime.fromisoformat(leaver["start_date"]).date() - datetime.fromisoformat(leaver["start_date"]).date()) if leaver.get("start_date") else None
        if not tenure:
            tenure = (g.as_of - (g.as_of - timedelta(days=r.randint(30, 730)))).days // 30
        else:
            tenure = (g.as_of - datetime.fromisoformat(leaver["start_date"]).date()).days // 30

        end_date = g.as_of - timedelta(days=r.randint(1, 180))
        leavers_list.append({
            "leaver_id": f"LVR-{lvr_counter:06d}",
            "employee_id": leaver["employee_id"],
            "name": leaver["name"],
            "role": leaver["role"],
            "site_id": leaver["site_id"],
            "shift_pattern": leaver["shift"],
            "employment_type": r.choices(["permanent", "agency", "temporary"], [0.6, 0.3, 0.1])[0],
            "start_date": datetime.fromisoformat(leaver["start_date"]).date() if leaver.get("start_date") else g.as_of - timedelta(days=r.randint(60, 730)),
            "end_date": end_date,
            "tenure_months": max(1, tenure),
            "exit_reason": r.choice(exit_reasons),
            "exit_themes": r.choice(exit_themes_options),
            "exit_interview_date": end_date + timedelta(days=r.randint(1, 14))
        })

    # Generate employee skills
    skills_list = [
        "forklift certification",
        "CSCS card",
        "manual handling",
        "team leadership",
        "system administration",
        "customer service",
        "inventory management",
        "quality control",
        "health and safety rep",
        "first aid certificate"
    ]

    for emp in active_emps:
        num_skills = r.randint(0, 3)
        selected_skills = r.sample(skills_list, min(num_skills, len(skills_list)))
        for skill in selected_skills:
            skills.append({
                "employee_id": emp["employee_id"],
                "skill": skill,
                "proficiency": r.choices(["beginner", "intermediate", "expert"], [0.3, 0.5, 0.2])[0],
                "verified_date": g.as_of - timedelta(days=r.randint(30, 365))
            })

    # Generate commute distances
    cities = ["Manchester", "Leeds", "Sheffield", "Nottingham", "East Midlands", "Coventry", "Birmingham"]
    for emp in active_emps[:min(len(active_emps), 100)]:
        distance = r.gauss(15, 8)
        distance = max(1, min(60, distance))  # 1-60km
        commutes.append({
            "employee_id": emp["employee_id"],
            "home_location": r.choice(cities),
            "site_id": emp["site_id"],
            "distance_km": round(distance, 1),
            "commute_method": r.choices(["car", "public_transport", "bike", "other"], [0.6, 0.25, 0.1, 0.05])[0]
        })

    # Generate market rates by site and role
    base_rates = {
        "Warehouse Operative": {"early": 12.50, "late": 13.00, "night": 15.00},
        "Picker": {"early": 12.50, "late": 13.00, "night": 15.00},
        "Packer": {"early": 12.50, "late": 13.00, "night": 15.00},
        "Forklift Operator": {"early": 14.50, "late": 15.00, "night": 17.50},
        "Team Lead": {"early": 17.00, "late": 17.50, "night": 20.00},
        "Supervisor": {"early": 20.00, "late": 20.50, "night": 23.00}
    }

    for site in sites:
        for role in roles:
            for shift in ["early", "late", "night"]:
                our_rate = base_rates.get(role, {}).get(shift, 12.50)
                # Market rate is higher in some sites
                market_variance = 1.05 if site["site_id"] in ["DC2", "DC3"] else 1.0
                market_rate = our_rate * market_variance * r.gauss(1.0, 0.08)
                gap_pct = round((our_rate / market_rate) * 100, 1)

                market_rates_list.append({
                    "site_id": site["site_id"],
                    "role": role,
                    "our_hourly_gbp": round(our_rate, 2),
                    "market_hourly_gbp": round(market_rate, 2),
                    "market_date": g.as_of - timedelta(days=r.randint(1, 30)),
                    "gap_pct": gap_pct
                })

    return {
        "headcount_requisitions": requisitions,
        "pay_review_requests": pay_reviews,
        "absence_records": absences,
        "employee_leavers": leavers_list,
        "employee_skills": skills,
        "employee_commute": commutes,
        "market_rates": market_rates_list
    }
