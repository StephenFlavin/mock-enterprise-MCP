"""Store operations data: monthly KPIs and plan vs actual, visits, actions, week tasks, shelf gaps, shrink controls,
take-back pilots, channel options. Story stores (ST214 and its peers, UK North's weakest three) are set explicitly."""
from datetime import date, datetime, timedelta

# 12 monthly values, oldest first
def ramp(a, b, n=12):
    return [round(a + (b - a) * i / (n - 1), 2) for i in range(n)]


def add_months(d, k):
    y, m = d.year + (d.month - 1 + k) // 12, (d.month - 1 + k) % 12 + 1
    return date(y, m, 1)


SEASON = {1: 0.88, 2: 0.85, 3: 0.95, 4: 0.97, 5: 1.0, 6: 1.0, 7: 0.98, 8: 1.0, 9: 1.0, 10: 1.04, 11: 1.12, 12: 1.32}
RATE = {"high_street": 3.0, "retail_park": 4.4, "shopping_centre": 2.8, "outlet": 3.5, "travel": 6.0}
BASE_MARGIN = {"high_street": 34.0, "retail_park": 33.0, "shopping_centre": 35.0, "outlet": 28.0, "travel": 38.0}
CLUSTER = {
    "A": dict(sh=(0.55, 0.85), av=(96.5, 98.0), lb=(9.5, 11.0)),
    "B": dict(sh=(0.70, 0.95), av=(95.3, 97.2), lb=(10.4, 11.9)),
    "C": dict(sh=(0.75, 1.00), av=(95.5, 97.5), lb=(10.5, 12.5)),
    "D": dict(sh=(0.90, 1.30), av=(95.0, 97.0), lb=(11.0, 13.0)),
}

# Explicit stories. Sep (the latest month) values match what bi / ims show for the same stores.
STORY = {
    # Store 214 has been below plan for months while its peers are on plan; availability is its biggest gap
    "ST214": dict(shrink=ramp(0.92, 1.01), avail=ramp(96.1, 94.2), labour=ramp(11.7, 12.2), spv=10.2, plan=80000.0,
                  var=[1.4, 1.1, 0.6, 0.5, 0.3, 0.2, -2.6, -3.9, -5.1, -6.2, -7.0, -7.8], mplan=32.0, mgap=-1.0),
    # UK North's three weakest stores
    "ST143": dict(shrink=ramp(2.0, 2.8), avail=ramp(94.5, 92.3), labour=ramp(11.8, 12.1), spv=9.5, plan=36000.0,
                  var=[-1, -3, -4, -6, -8, -10, -12, -15, -19, -23, -27, -30.8], mplan=32.5, mact=26.1),
    "ST142": dict(shrink=ramp(1.2, 1.9), avail=ramp(95.2, 94.0), labour=ramp(11.5, 11.8), spv=10.0, plan=34900.0,
                  var=[0, -1, -2, -3, -5, -7, -9, -11, -13, -15, -17, -18.6], mplan=31.5, mact=28.2),
    "ST150": dict(shrink=ramp(1.6, 2.2), avail=ramp(95.0, 94.4), labour=ramp(13.6, 14.6), spv=11.0, plan=68900.0,
                  var=[-1.0, -1.5, -2, -2.5, -3, -3.5, -4, -4.5, -5, -5.5, -6, -6.7], mplan=33.0, mact=31.0),
    # cluster B's weakest availability
    "ST215": dict(shrink=ramp(0.84, 0.86), avail=ramp(94.6, 93.5), labour=ramp(11.2, 11.4), spv=11.5, plan=None,
                  var=None, mplan=None),
}
NORTH_MU = 0.35  # mean sales variance of UK North stores outside the three weak ones

AIDED_SKUS = ["SKU-100007", "K-1700", "SKU-100014"]  # ST214's three best-selling lines with shelf gaps

CTRL = [  # prog_id, name, type, description, annual cost per store, business-case shrink reduction %, actual pounds saved per pound
    ("SCP-0001", "Tagging (RFID and EAS)", "Tagging", "RFID/EAS tags on high-theft lines", 2400, 14, 1.53),
    ("SCP-0002", "Enhanced Staffing", "Staffing", "Loss prevention officer on the floor at peak hours", 15300, 9, 0.14),
    ("SCP-0003", "Store Layout Redesign", "Layout", "Clear sightlines, lower shelves, high-risk lines near tills", 5050, 12, 0.54),
    ("SCP-0004", "POS System Rules", "System", "POS exception rules for voids, refunds and no-sale openings", 1000, 8, 1.80),
    ("SCP-0005", "In-store Take-back", "TakeBack", "Customer take-back bins and collection; a circular-economy programme, not a shrink control", 4500, 0, None),
    ("SCP-0006", "Security Guarding", "Security", "One security guard at peak hours", 12300, 7, 0.22),
]
DEPLOYED = {"SCP-0001": 32, "SCP-0002": 37, "SCP-0003": 34, "SCP-0004": 46, "SCP-0006": 41}
MUST_HAVE = {"SCP-0001": ["ST214", "ST001"], "SCP-0002": ["ST214"], "SCP-0003": ["ST001"]}


def generate(g):
    r = g.rng
    sites = g.master("sites")
    stores = [s for s in sites if s["type"] == "store" and s["status"] == "open"]
    by_id = {s["site_id"]: s for s in stores}
    emps = g.master("employees")
    mgr = {e["site_id"]: e["employee_id"] for e in emps if e["role"] == "Store Manager"}
    products = g.master("products")
    pidx = {p["sku"]: p for p in products}
    sample_skus = products[:50]
    as_of = g.as_of
    ts = datetime(as_of.year, as_of.month, as_of.day, 9, 0, 0)
    monday = as_of - timedelta(days=as_of.weekday())
    this_month = date(as_of.year, as_of.month, 1)
    months = [add_months(this_month, -i) for i in range(12, 0, -1)]  # last 12 full months, oldest first

    # peers of ST214 (same rule as the search_peer_stores tool) stay close to plan
    s1 = by_id["ST214"]
    cand = sorted((s for s in stores if s["site_id"] != "ST214" and s["country"] == s1["country"]),
                  key=lambda s: (-((s["format"] == s1["format"]) * 2 + (s["cluster"] == s1["cluster"]) * 2 + (s["region"] == s1["region"])),
                                 abs(int(s["sqft"]) - int(s1["sqft"])), s["site_id"]))
    peers214 = {s["site_id"] for s in cand[:5]}

    # ---------------- store_kpis and plan_vs_actual ----------------
    store_kpis, plan_vs_actual = [], []
    for s in stores:
        sid = s["site_id"]
        st = STORY.get(sid, {})
        prof = CLUSTER.get(s["cluster"] or "C", CLUSTER["C"])
        fmt = s["format"]
        base_plan = st.get("plan") or round(int(s["sqft"]) * RATE.get(fmt, 3.5) * r.uniform(0.85, 1.15), -2)
        base_sh, base_av, base_lb = r.uniform(*prof["sh"]), r.uniform(*prof["av"]), r.uniform(*prof["lb"])
        spv = st.get("spv") or r.uniform(9.5, 14.0)
        mplan = st.get("mplan") or round(BASE_MARGIN.get(fmt, 33.0) + r.uniform(-2, 2), 1)
        for i, mo in enumerate(months):
            seasonal = SEASON[mo.month] / SEASON[months[-1].month]
            plan = round(base_plan * seasonal, 2)
            if st.get("var"):
                var = st["var"][i]
            elif sid in peers214:
                var = round(min(2.0, max(-0.5, r.gauss(0.8, 0.6))), 1)
            elif s["region"] == "UK North":
                var = round(min(3.5, max(-2.5, r.gauss(NORTH_MU, 1.2))), 1)
            else:
                var = round(min(4.0, max(-3.0, r.gauss(0.5, 1.4))), 1)
            actual = round(plan * (1 + var / 100), 2)
            vgbp = round(actual - plan, 2)
            vpct = round(vgbp / plan * 100, 1)
            if st.get("mact") is not None:
                mact = round(mplan + (st["mact"] - mplan) * i / 11, 1)
            elif st.get("mgap") is not None:
                mact = round(mplan + st["mgap"] * (i / 11), 1)
            else:
                mact = round(mplan + r.uniform(-0.6, 0.6), 1)
            if sid in STORY and st.get("shrink"):
                sh, av, lb = st["shrink"][i], st["avail"][i], st["labour"][i]
            else:
                sh = round(base_sh + r.uniform(-0.03, 0.03), 2)
                av = round(base_av + r.uniform(-0.25, 0.25), 1)
                lb = round(base_lb + r.uniform(-0.2, 0.2), 1)
            if sid == "ST215":
                sh, av, lb = st["shrink"][i], st["avail"][i], st["labour"][i]
                plan = round(int(s["sqft"]) * RATE.get(fmt, 3.5) * 1.05 * seasonal, 2)
                actual = round(plan * (1 + r.uniform(-0.01, 0.015)), 2)
                vgbp = round(actual - plan, 2)
                vpct = round(vgbp / plan * 100, 1)
            plan_vs_actual.append({"site_id": sid, "month": mo, "sales_plan_gbp": plan, "sales_actual_gbp": actual,
                                   "variance_gbp": vgbp, "variance_pct": vpct, "margin_plan_pct": mplan, "margin_actual_pct": mact})
            store_kpis.append({"site_id": sid, "month": mo, "shrink_pct": sh, "availability_pct": av, "labour_cost_pct": lb,
                               "footfall": int(actual / (spv * r.uniform(0.97, 1.03))), "sales_gbp": actual, "margin_pct": mact})

    # ---------------- backroom constraints ----------------
    backroom = []
    for s in stores:
        total = 500 + int(int(s["sqft"]) * 0.15)
        backroom.append({"site_id": s["site_id"], "total_backroom_sqft": total,
                         "available_sqft": round(total * r.uniform(0.3, 0.7)),
                         "racking_capacity_pallets": r.randint(50, 200), "bulk_floor_capacity_pallets": r.randint(20, 80),
                         "chilled_space_sqft": round(total * r.uniform(0.1, 0.25)),
                         "hazmat_compliance": r.random() < 0.75, "take_back_space_available": r.random() < 0.8})

    # ---------------- shrink control programmes and results ----------------
    programmes = [{"prog_id": p[0], "programme_name": p[1], "control_type": p[2], "description": p[3],
                   "annual_cost_gbp": p[4], "estimated_shrink_reduction_pct": p[5]} for p in CTRL]
    gb_ids = [s["site_id"] for s in stores if s["country"] == "GB"]
    control_results = []
    last3 = months  # all 12 months of results
    for prog_id, name, ctype, desc, cost, est, target in CTRL:
        if target is None:
            continue
        chosen = list(MUST_HAVE.get(prog_id, []))
        rest = [x for x in gb_ids if x not in chosen]
        chosen += r.sample(rest, DEPLOYED[prog_id] - len(chosen))
        rows = []
        for sid in chosen:
            factor = r.uniform(0.6, 1.4)
            for mo in last3:
                c = round(cost / 12 * r.uniform(0.95, 1.05), 2)
                red = c * target * factor * r.uniform(0.9, 1.1)
                rows.append([sid, prog_id, mo, c, red])
        scale = target * sum(x[3] for x in rows) / sum(x[4] for x in rows)  # overall payback is exactly the programme's
        for sid, pid, mo, c, red in rows:
            red = round(red * scale, 2)
            control_results.append({"site_id": sid, "prog_id": pid, "month": mo, "control_cost_gbp": c,
                                    "shrink_reduction_gbp": red, "payback_ratio": round(red / c, 2)})

    # ---------------- visits, action plans, tasks, counts, gaps, priorities ----------------
    story_stores = {"ST214"}
    region_mgrs = {}
    for s in stores:
        if s["site_id"] in mgr:
            region_mgrs.setdefault(s["region"], []).append(mgr[s["site_id"]])
    visits, actions, tasks, counts, exceptions, priorities = [], [], [], [], [], []
    vid = 1
    for s in stores:
        if s["site_id"] in story_stores:
            continue
        if r.random() < 0.5:
            for _ in range(r.randint(1, 2)):
                visits.append({"visit_id": f"VIS-{vid:06d}", "site_id": s["site_id"],
                               "employee_id": r.choice(region_mgrs[s["region"]]),
                               "visit_date": g.days_ago(r.randint(14, 60)),
                               "visit_purpose": r.choice(["Quarterly performance review", "Shrink investigation", "Staff training",
                                                          "New initiative rollout", "Mystery shopper follow-up"]),
                               "issues_found": r.randint(0, 6), "actions_raised": r.randint(0, 4),
                               "duration_hours": round(r.uniform(2, 6), 1), "status": "completed",
                               "notes": r.choice(["Walked the floor, no major issues.", "Availability on promoted lines needs work.",
                                                  "Good standards in receiving.", "Rota gaps at weekends.", "Tidy stockroom, counts up to date."]),
                               "updated_at": ts - timedelta(days=r.randint(14, 60))})
                vid += 1
    aid = 1
    for s in stores:
        if s["site_id"] in story_stores or r.random() > 0.6:
            continue
        for _ in range(r.randint(1, 3)):
            created = g.days_ago(r.randint(10, 60))
            actions.append({"action_id": f"API-{aid:06d}", "site_id": s["site_id"],
                            "title": r.choice(["Review RFID tagging of high-theft items", "Implement daily floor walk routine",
                                               "Audit stock counts for category", "Staff training on loss prevention",
                                               "Improve receiving process controls", "Enhance front-end POS monitoring",
                                               "Reorganise high-shrink category layout"]),
                            "employee_id": mgr.get(s["site_id"], "EMP-00536"),
                            "due_date": created + timedelta(days=r.randint(21, 60)),
                            "status": r.choice(["open", "open", "in_progress"]), "priority": r.choice(["low", "medium", "high"]),
                            "category": r.choice(["Shrink", "Availability", "Labour", "Safety"]),
                            "created_at": datetime.combine(created, datetime.min.time()), "completed_at": None})
            aid += 1
    tid = 1
    for s in stores:
        if s["site_id"] in story_stores:
            continue
        for wk in (-7, 0, 7):
            ws = monday + timedelta(days=wk)
            for _ in range(r.randint(2, 4)):
                tt = r.choice(["Delivery", "Cycle Count", "Replenishment", "Training", "Receiving"])
                tasks.append({"task_id": f"TSK-{tid:06d}", "site_id": s["site_id"], "week_start": ws,
                              "task_name": {"Delivery": "Delivery from DC", "Cycle Count": "Cycle count", "Replenishment": "Shelf replenishment",
                                            "Training": "Team training", "Receiving": "Receiving and put-away"}[tt],
                              "task_type": tt, "employee_id": mgr.get(s["site_id"], "EMP-00536"),
                              "scheduled_date": ws + timedelta(days=r.randint(0, 5)),
                              "scheduled_start_time": f"{r.choice([6, 7, 14, 18]):02d}:00",
                              "scheduled_duration_hours": round(r.uniform(1, 4), 1),
                              "status": "completed" if wk < 0 else "scheduled", "notes": None})
                tid += 1
    cid = 1
    for s in stores:
        if s["site_id"] in story_stores or r.random() > 0.4:
            continue
        p = r.choice(sample_skus)
        sysq = r.randint(10, 300)
        done = r.random() < 0.6
        cnt = sysq + r.randint(-15, 10)
        counts.append({"cycle_id": f"CYC-{cid:06d}", "site_id": s["site_id"], "sku": p["sku"], "location_id": None,
                       "category": p["category"], "count_date": g.days_ago(r.randint(3, 40)),
                       "reason": r.choice(["Shrink investigation", "Stock taking", "Delivery variance", "Ad-hoc check"]),
                       "status": "completed" if done else "pending", "system_quantity": sysq,
                       "counted_quantity": cnt if done else None, "variance": cnt - sysq if done else None,
                       "created_at": ts - timedelta(days=r.randint(3, 40))})
        cid += 1
    eid = 1
    for s in stores:
        if s["site_id"] in story_stores or r.random() > 0.35:
            continue
        p = r.choice(sample_skus)
        sysq = r.randint(20, 100)
        shelf = r.randint(0, 10)
        cause = r.choice(["Backroom", "Delivery", "Damage", "Stock audit"])
        exceptions.append({"exc_id": f"SAE-{eid:06d}", "site_id": s["site_id"], "sku": p["sku"],
                           "exception_date": g.days_ago(r.randint(0, 5)),
                           "status": r.choice(["open", "resolved"]),
                           "location": f"Aisle {r.randint(1, 12)}", "system_stock": sysq, "observed_on_shelf": shelf,
                           "backroom_units": sysq - shelf if cause == "Backroom" else 0,
                           "likely_cause": cause, "created_at": ts - timedelta(days=r.randint(0, 5))})
        eid += 1
    seen = set()
    for s in stores:
        if s["site_id"] in story_stores or r.random() > 0.9:
            continue
        for _ in range(r.randint(1, 3)):
            p = r.choice(sample_skus)
            if (s["site_id"], p["sku"]) in seen:
                continue
            seen.add((s["site_id"], p["sku"]))
            priorities.append({"site_id": s["site_id"], "sku": p["sku"], "priority_level": r.randint(2, 5),
                               "reason": r.choice(["High demand", "Low availability", "Customer feedback", "Standard rotation"]),
                               "effective_from": g.days_ago(r.randint(10, 60)), "updated_at": ts - timedelta(days=r.randint(10, 60))})

    # ---------------- click and collect ----------------
    cc, seen = [], set()
    k1700 = {"ST001": 14, "ST006": 12, "ST150": 11, "ST214": 9, "ST209": 8, "ST008": 8, "ST202": 7, "ST206": 6}
    for sid, fc in k1700.items():
        for d in range(7):  # last 7 days of data: inside the default window whatever weekday it is run
            f = max(1, fc + r.randint(-2, 2))
            a = int(round(f * r.uniform(1.15, 1.45)))
            cc.append({"site_id": sid, "sku": "K-1700", "date": g.days_ago(d), "forecasted_demand": f, "actual_demand": a,
                       "reserved_quantity": max(0, int(a * 0.6)), "online_allocation": fc * 3})
            seen.add((sid, "K-1700", g.days_ago(d)))
    others = [p for p in sample_skus if p["sku"] != "K-1700"]
    for d in range(3):
        for s in r.sample(stores, 12):
            for p in r.sample(others, 8):
                key = (s["site_id"], p["sku"], g.days_ago(d))
                if key in seen:
                    continue
                seen.add(key)
                f = r.randint(0, 12)
                cc.append({"site_id": s["site_id"], "sku": p["sku"], "date": g.days_ago(d), "forecasted_demand": f,
                           "actual_demand": max(0, f + r.randint(-3, 4)), "reserved_quantity": r.randint(0, 6),
                           "online_allocation": r.randint(0, 30)})

    # ---------------- clearance channel options (every SKU) ----------------
    apparel = {"Dresses", "Outerwear", "Knitwear", "Trousers", "Shirts", "Tops", "Blouses", "Scarves", "T-Shirts", "Nightwear",
               "Babywear", "Schoolwear", "Footwear", "Bags", "Jewellery"}
    bulky = {"Towels", "Bedding", "Cookware", "Storage"}
    chan = []
    for p in products:
        cat = p["category"]
        batt = p["hazmat"] != "none"
        for ch, (pa, pb), (sa, sb), wk in (("Retail", (0.68, 0.80), (45, 62), 10), ("Online", (0.64, 0.76), (40, 58), 12),
                                           ("Outlet", (0.50, 0.60), (62, 80), 6), ("Wholesale", (0.30, 0.40), (92, 100), 3)):
            pr, st = r.uniform(pa, pb) * 100, r.uniform(sa, sb)
            note = ""
            if ch == "Outlet" and cat in apparel:
                pr, st = pr + 4, st + 12
            if ch == "Online" and batt:
                pr, st, note = pr - 4, st - 10, "Lithium battery: courier parcel restrictions, ground only"
            if ch == "Online" and cat in bulky:
                st, note = st - 6, "Bulky: high parcel cost"
            if ch == "Retail":
                note = "Needs a markdown event and shelf space"
            chan.append({"sku": p["sku"], "channel": ch, "price_realisation_pct": round(pr, 1), "sell_through_pct": round(min(st, 100), 1),
                         "weeks_to_clear": wk + r.randint(-1, 3), "constraint_note": note})
    planted = {  # the three biggest lines of stock older than 180 days
        "SKU-105054": {"Retail": (78, 68, 8, "Needs a markdown event and shelf space"), "Online": (74, 55, 10, ""),
                       "Outlet": (55, 75, 6, ""), "Wholesale": (36, 97, 3, "")},
        "SKU-101253": {"Retail": (66, 42, 14, "Needs a markdown event and shelf space"),
                       "Online": (70, 30, 18, "Lithium battery: courier parcel restrictions, ground only"),
                       "Outlet": (58, 88, 6, ""), "Wholesale": (38, 98, 3, "")},
        "SKU-100658": {"Retail": (72, 55, 10, "Needs a markdown event and shelf space"), "Online": (73, 62, 9, ""),
                       "Outlet": (54, 70, 7, ""), "Wholesale": (34, 97, 3, "")},
    }
    for row in chan:
        o = planted.get(row["sku"], {}).get(row["channel"])
        if o:
            row.update(price_realisation_pct=o[0], sell_through_pct=o[1], weeks_to_clear=o[2], constraint_note=o[3])

    return {
        "store_kpis": store_kpis, "plan_vs_actual": plan_vs_actual, "backroom_constraints": backroom,
        "shrink_control_programmes": programmes, "store_control_results": control_results,
        "store_visits": visits, "action_plans": actions, "week_tasks": tasks, "cycle_count_tasks": counts,
        "shelf_availability_exceptions": exceptions, "replenishment_priorities": priorities,
        "click_collect_demand": cc, "take_back_pilot_results": [], "channel_options": chan,
    }
