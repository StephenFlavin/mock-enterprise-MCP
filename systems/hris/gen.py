"""HRIS data for the DC workforce: leavers with exit interviews, absence, skills, commute, market pay, requisitions.

Story: DC2 (Daventry) has ~45% annual turnover against ~28% at the other DCs, worst on the night shift. Pay is the
most-cited exit theme (night market gap ~12%), then commute (night staff live far away) and management (late shift
manager has left, early shift manager is agency cover). DC2 absence is roughly double the other sites.
Turnover = leavers in the period / current headcount (active + agency) at the site and shift in master.employees.
"""
from datetime import date, timedelta

SHIFTS = ["early", "late", "night", "office"]

# our hourly rate by role: (early, late, night)
OUR_RATES = {
    "Picker/Packer": (13.10, 13.55, 14.60),
    "Despatch Operative": (13.10, 13.55, 14.60),
    "Goods-in Clerk": (13.30, 13.75, 14.80),
    "Forklift Operator": (14.60, 15.05, 16.30),
    "Inventory Controller": (14.40, 14.85, 16.00),
    "Shift Manager": (19.80, 20.30, 22.20),
}
# market / our, by site and shift (early, late, night)
MARKET_MULT = {"DC1": (1.01, 1.01, 1.03), "DC2": (1.05, 1.06, 1.14), "DC3": (1.00, 1.00, 1.02)}

HOME_AREAS = {  # area -> typical km to site
    "DC1": {"Northampton": 8, "Wellingborough": 19, "Kettering": 27, "Daventry": 19, "Towcester": 14, "Milton Keynes": 32},
    "DC2": {"Daventry": 6, "Northampton": 19, "Rugby": 21, "Towcester": 23, "Banbury": 33, "Coventry": 38,
            "Leicester": 47, "Milton Keynes": 43},
    "DC3": {"Leeds": 8, "Bradford": 14, "Wakefield": 15, "Harrogate": 24, "Huddersfield": 26, "York": 40},
    "DC4": {"Venlo": 5, "Tegelen": 4, "Horst": 12, "Venray": 15, "Roermond": 22},
    "DC5": {"Columbus": 12, "Grove City": 17, "Dublin OH": 20, "Westerville": 22, "Newark OH": 45},
}
DC2_FAR = ["Banbury", "Coventry", "Leicester", "Milton Keynes"]

BASE_TURNOVER = {"DC1": 0.28, "DC3": 0.29, "DC4": 0.27, "DC5": 0.28}
SHIFT_MULT = {"early": 0.85, "late": 1.0, "night": 1.2, "office": 0.0}
# DC2 leavers to generate on top of the two master leavers (EMP-00184 early, EMP-00201 late; both in seed)
DC2_EXTRA = {"night": 12, "late": 6, "early": 5}
SEEDED_LEAVERS = {"EMP-00184", "EMP-00201"}

BASE_P_UNPLANNED = {"DC1": 0.030, "DC3": 0.032, "DC4": 0.028, "DC5": 0.027}
DC2_P_UNPLANNED = {"early": 0.052, "late": 0.060, "night": 0.085, "office": 0.02}


def _wchoice(r, pairs):
    return r.choices([p[0] for p in pairs], [p[1] for p in pairs])[0]


def generate(g):
    r = g.rng
    emps = g.master("employees")
    dc_sites = [s["site_id"] for s in g.master("sites") if s["type"] == "dc"]
    dc_emps = [e for e in emps if e["site_id"] in dc_sites]
    heads = [e for e in dc_emps if e["status"] in ("active", "agency")]
    by_id = {e["employee_id"]: e for e in emps}
    managers = {}
    for e in dc_emps:
        if e["role"] == "Shift Manager":
            managers.setdefault((e["site_id"], e["shift"]), e["employee_id"])
    wh_mgr = {e["site_id"]: e["employee_id"] for e in dc_emps if e["role"] == "Warehouse Manager"}

    return {
        "headcount_requisitions": _requisitions(g, dc_sites),
        "pay_review_requests": [],
        "absence_records": _absences(g, heads),
        "employee_leavers": _leavers(g, dc_sites, dc_emps, heads, by_id, managers, wh_mgr),
        "employee_skills": _skills(g, heads),
        "employee_commute": _commute(g, heads),
        "market_rates": _market(g),
    }


def _requisitions(g, dc_sites):
    r = g.rng
    roles = list(OUR_RATES)[:5]
    rows, n = [], 100
    for site in ["DC1", "DC3", "DC4", "DC5"]:
        for _ in range(r.randint(1, 2)):
            n += 1
            hc = r.randint(2, 8)
            status = r.choices(["draft", "approved", "filled"], [0.2, 0.4, 0.4])[0]
            rows.append({
                "req_id": f"REQ-{n:06d}", "site_id": site, "role": r.choice(roles), "headcount": hc,
                "employment_type": r.choice(["permanent", "permanent", "agency"]),
                "shift": r.choice(["early", "late", "night"]),
                "required_by": g.as_of + timedelta(days=r.randint(14, 90)),
                "status": status, "created_at": g.as_of - timedelta(days=r.randint(5, 40)),
                "filled_count": hc if status == "filled" else (r.randint(0, hc // 2) if status == "approved" else 0),
                "required_skills": r.choice(["manual handling", "forklift certification", "manual handling; RF scanning (WMS)"]),
            })
    return rows


def _absences(g, heads):
    r = g.rng
    rows, n = [], 0
    days = [g.as_of - timedelta(days=d) for d in range(182, 0, -1)]
    days = [d for d in days if d.weekday() < 5]
    for e in heads:
        site, shift = e["site_id"], e["shift"]
        if site == "DC2":
            p = DC2_P_UNPLANNED[shift]
        else:
            p = BASE_P_UNPLANNED[site] * (1.15 if shift == "night" else 1.0)
        for d in days:
            x = r.random()
            if x < p:
                reason = _wchoice(r, [("sickness", 0.80), ("other", 0.10), ("unpaid_leave", 0.10)])
            elif x < p + 0.06:
                reason = "annual_leave"
            else:
                continue
            n += 1
            rows.append({"absence_id": f"ABS-{n:06d}", "employee_id": e["employee_id"], "site_id": site,
                         "shift_pattern": shift, "absence_date": d,
                         "hours_absent": 4 if r.random() < 0.12 else 8, "reason": reason})
    return rows


REASONS_DC2 = {
    "night": [("Pay and benefits", 45), ("Commute", 22), ("Shift pattern", 12), ("Management style", 8),
              ("Better opportunity", 5), ("Work-life balance", 4), ("Personal reasons", 4)],
    "late": [("Pay and benefits", 36), ("Management style", 30), ("Commute", 12), ("Shift pattern", 8),
             ("Better opportunity", 8), ("Personal reasons", 6)],
    "early": [("Pay and benefits", 40), ("Management style", 18), ("Commute", 15), ("Better opportunity", 10),
              ("Shift pattern", 7), ("Personal reasons", 10)],
}
REASONS_BASE = [("Better opportunity", 20), ("Pay and benefits", 20), ("Personal reasons", 15), ("Relocation", 12),
                ("Career development", 13), ("Commute", 6), ("Health", 6), ("Management style", 5),
                ("Work-life balance", 3)]
THEME_OF = {
    "Pay and benefits": "Pay", "Commute": "Commute distance", "Management style": "Management",
    "Shift pattern": "Shift pattern", "Better opportunity": "Better offer elsewhere",
    "Career development": "Career development", "Work-life balance": "Work-life balance", "Health": "Health",
    "Personal reasons": "Family circumstances", "Relocation": "Relocation",
}


def _tenure(r, etype, route, site, shift):
    if etype == "agency":
        lo, hi = r.choices([(1, 3), (4, 6), (7, 12)], [0.65, 0.25, 0.10])[0]
    elif etype == "temporary":
        lo, hi = 2, 7
    elif etype == "fixed_term":
        lo, hi = 6, 11
    elif site == "DC2" and shift == "night":
        lo, hi = r.choices([(1, 5), (6, 11), (12, 23), (24, 60)], [0.35, 0.35, 0.2, 0.1])[0]
    else:
        lo, hi = r.choices([(1, 5), (6, 11), (12, 23), (24, 60), (61, 120)], [0.22, 0.2, 0.25, 0.23, 0.10])[0]
    t = r.randint(lo, hi)
    if route == "referral":
        t = max(t, 9) + r.randint(0, 10)
    elif route == "temp_to_perm":
        t = max(t, 6) + r.randint(0, 6)
    return t


def _leavers(g, dc_sites, dc_emps, heads, by_id, managers, wh_mgr):
    r = g.rng
    rows, n = [], 0
    head_n, role_w = {}, {}
    for e in heads:
        head_n[(e["site_id"], e["shift"])] = head_n.get((e["site_id"], e["shift"]), 0) + 1
        if "Manager" not in e["role"]:
            role_w.setdefault((e["site_id"], e["shift"]), {}).setdefault(e["role"], 0)
            role_w[(e["site_id"], e["shift"])][e["role"]] += 1
    master_leavers = {}
    for e in dc_emps:
        if e["status"] == "leaver" and e["employee_id"] not in SEEDED_LEAVERS:
            master_leavers.setdefault((e["site_id"], e["shift"]), []).append(e)

    def make(site, shift, emp):
        nonlocal n
        n += 1
        if site == "DC2":
            etype = _wchoice(r, [("permanent", 0.62), ("agency", 0.28), ("temporary", 0.07), ("fixed_term", 0.03)]) \
                if shift == "night" else _wchoice(r, [("permanent", 0.72), ("agency", 0.17), ("temporary", 0.08), ("fixed_term", 0.03)])
        else:
            ag = 0.28 if shift == "night" else 0.20
            etype = _wchoice(r, [("permanent", 0.97 - ag - 0.07), ("agency", ag), ("temporary", 0.07), ("fixed_term", 0.03)])
        if emp and emp["role"] in ("Shift Manager", "Warehouse Manager"):
            etype = "permanent"
        if etype == "agency":
            route = "agency"
        elif etype == "permanent":
            route = _wchoice(r, [("direct_advert", 0.60), ("referral", 0.25), ("temp_to_perm", 0.15)])
        else:
            route = "direct_advert"
        if site == "DC2" and shift == "night":
            days_ago = int(r.triangular(10, 340, 40))
        else:
            days_ago = r.randint(10, 340)
        end = g.as_of - timedelta(days=days_ago)
        if emp:
            start = date.fromisoformat(emp["start_date"])
            if start >= end - timedelta(days=30):
                end = start + timedelta(days=r.randint(60, 200))
                if end > g.as_of - timedelta(days=10):
                    start = end - timedelta(days=r.randint(60, 200))
            tenure = max(1, round((end - start).days / 30.4))
            role, name, emp_id, mgr = emp["role"], emp["name"], emp["employee_id"], emp["manager_id"]
        else:
            tenure = _tenure(r, etype, route, site, shift)
            start = end - timedelta(days=int(tenure * 30.4) + r.randint(0, 20))
            tenure = max(1, round((end - start).days / 30.4))
            roles = role_w.get((site, shift)) or {"Picker/Packer": 1}
            role = _wchoice(r, list(roles.items()))
            name, emp_id = g.fake.name(), ""
            mgr = managers.get((site, shift), wh_mgr.get(site, ""))
        if site == "DC2":
            reason = _wchoice(r, REASONS_DC2.get(shift, REASONS_DC2["early"]))
        else:
            reason = _wchoice(r, REASONS_BASE)
        themes = [THEME_OF[reason]]
        if site == "DC2":
            if reason != "Pay and benefits" and r.random() < 0.25:
                themes.append("Pay")
            if reason != "Commute" and shift == "night" and r.random() < 0.10:
                themes.append("Commute distance")
            if reason != "Management style" and shift == "late" and r.random() < 0.15:
                themes.append("Management")
        elif reason == "Better opportunity" and r.random() < 0.35:
            themes.append("Pay")
        interview_p = {"permanent": 0.92, "temporary": 0.8, "fixed_term": 0.8, "agency": 0.45}[etype]
        interviewed = r.random() < interview_p
        rows.append({
            "leaver_id": f"LVR-{n:06d}", "employee_id": emp_id, "name": name, "role": role, "site_id": site,
            "shift_pattern": shift, "employment_type": etype, "hire_route": route, "manager_id": mgr,
            "start_date": start, "end_date": end, "tenure_months": tenure,
            "exit_reason": reason,
            "exit_themes": "; ".join(themes) if interviewed else "",
            "exit_interview_date": min(end + timedelta(days=r.randint(2, 14)), g.as_of - timedelta(days=1)) if interviewed else "",
        })

    for site in dc_sites:
        for shift in ("night", "late", "early"):
            hc = head_n.get((site, shift), 0)
            if site == "DC2":
                target_new = DC2_EXTRA[shift]
                pool = list(master_leavers.get((site, shift), []))
            else:
                total = round(hc * BASE_TURNOVER[site] * SHIFT_MULT[shift])
                pool = list(master_leavers.get((site, shift), []))
                target_new = max(0, total - len(pool))
            for emp in pool:
                make(site, shift, emp)
            for _ in range(target_new):
                make(site, shift, None)
    return rows


def _skills(g, heads):
    r = g.rng
    P = {  # skill -> role -> probability (default key "*")
        "forklift certification": {"Forklift Operator": 1.0, "Goods-in Clerk": 0.25, "Despatch Operative": 0.10,
                                   "Picker/Packer": 0.08, "Inventory Controller": 0.05, "*": 0.0},
        "manual handling": {"*": 0.95},
        "RF scanning (WMS)": {"Picker/Packer": 0.9, "Goods-in Clerk": 0.9, "Despatch Operative": 0.8,
                              "Inventory Controller": 0.95, "Forklift Operator": 0.6, "Shift Manager": 0.8, "*": 0.3},
        "first aid certificate": {"Shift Manager": 0.5, "*": 0.12},
        "team leadership": {"Shift Manager": 1.0, "Warehouse Manager": 1.0, "*": 0.06},
        "inventory management": {"Inventory Controller": 1.0, "Goods-in Clerk": 0.2, "*": 0.0},
        "health and safety rep": {"*": 0.05},
    }
    rows = []
    for e in heads:
        for skill, pm in P.items():
            p = pm.get(e["role"], pm.get("*", 0.0))
            if r.random() < p:
                high = skill == "team leadership" and "Manager" in e["role"] or \
                    (skill == "forklift certification" and e["role"] == "Forklift Operator")
                prof = r.choices(["intermediate", "expert"], [0.4, 0.6])[0] if high else \
                    r.choices(["beginner", "intermediate", "expert"], [0.3, 0.5, 0.2])[0]
                rows.append({"employee_id": e["employee_id"], "skill": skill, "proficiency": prof,
                             "verified_date": g.as_of - timedelta(days=r.randint(30, 700))})
    return rows


def _commute(g, heads):
    r = g.rng
    rows = []
    for e in heads:
        site = e["site_id"]
        areas = HOME_AREAS[site]
        if site == "DC2" and e["shift"] == "night" and r.random() < 0.8:
            area = r.choice(DC2_FAR)
        elif site == "DC2":
            area = r.choice([a for a in areas if a not in DC2_FAR])
        else:
            area = r.choice(list(areas))
        dist = round(max(1.5, r.gauss(areas[area], areas[area] * 0.12)), 1)
        far = dist > 25
        method = _wchoice(r, [("car", 0.92 if far else 0.6), ("public_transport", 0.03 if far else 0.25),
                              ("bike", 0.0 if far else 0.1), ("other", 0.05 if far else 0.05)])
        rows.append({"employee_id": e["employee_id"], "home_location": area, "site_id": site,
                     "distance_km": dist, "commute_method": method})
    return rows


def _market(g):
    r = g.rng
    rows = []
    for site, mult in MARKET_MULT.items():
        for role, rates in OUR_RATES.items():
            for i, shift in enumerate(("early", "late", "night")):
                our = rates[i]
                market = round(our * (mult[i] + r.gauss(0, 0.01)), 2)
                rows.append({"site_id": site, "role": role, "shift": shift, "our_hourly_gbp": our,
                             "market_hourly_gbp": market, "market_date": g.as_of - timedelta(days=r.randint(10, 30)),
                             "gap_pct": round(our / market * 100, 1)})
    return rows
