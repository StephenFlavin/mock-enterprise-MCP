"""Supplier relationship management data: scorecards, issues, improvement plans, engagement."""
from datetime import date, datetime, timedelta
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
    management_costs = []
    relationships = []

    # ------------------------------------------------------------------ shared helpers
    live = [s for s in suppliers if s["status"] in ("active", "blocked")]
    by_id = {s["supplier_id"]: s for s in suppliers}
    sourcing_staff = [e["employee_id"] for e in g.master("employees") if e["department"] == "Sourcing"]
    clamp = lambda v, lo, hi: max(lo, min(hi, v))
    product_live = [s for s in live if s.get("supplier_type", "product") == "product"]   # indirect suppliers have no spend and no scorecard story

    def pick(cands, k, tag):
        """k suppliers chosen by a per-supplier draw, so adding master suppliers never reshuffles the others."""
        return sorted(cands, key=lambda s: (g.rng_for(tag, s["supplier_id"]).random(), s["supplier_id"]))[:k]
    as_of = g.as_of

    months = []                                   # the last 12 completed months, oldest first
    y, m = as_of.year, as_of.month
    for _ in range(12):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        months.append(date(y, m, 1))
    months.reverse()

    # ------------------------------------------------------------------ supplier lead times (from master POs)
    # share of completed POs that ran late, and typical overrun in days (default derives from master OTIF)
    LATE = {
        "SUP-0053": (0.60, 9), "SUP-0012": (0.35, 6), "SUP-0070": (0.25, 5), "SUP-0074": (0.25, 6),
        "SUP-0039": (0.0, 0), "SUP-0004": (0.20, 4), "SUP-0011": (0.40, 9), "SUP-0046": (0.40, 8),
        "SUP-0044": (0.0, 0), "SUP-0040": (0.15, 5), "SUP-0058": (0.35, 9), "SUP-0079": (0.40, 9),
        "SUP-0001": (0.30, 10), "SUP-0008": (0.35, 8), "SUP-0016": (0.25, 7), "SUP-0013": (0.45, 11),
    }
    RAMP = {"SUP-0053", "SUP-0070"}               # getting worse over time: later POs overrun more
    WINDOW_SAFE = {"SUP-0039", "SUP-0004", "SUP-0011", "SUP-0046", "SUP-0044", "SUP-0001"}
    STAGE_SHARE = {"SUP-0046": (0.62, 0.08, 0.30)}
    DELAY_STAGE = {"SUP-0053": (0.85, 0.05, 0.10), "SUP-0046": (0.45, 0.20, 0.35)}
    STAGES = ["order_to_factory", "factory_to_port", "port_to_dc"]
    CAUSES = {
        "order_to_factory": ["Factory capacity shortfall", "Fabric or trim shortage", "Late fabric booking", "Production rework"],
        "factory_to_port": ["Late inland trucking booking", "Missed vessel cut-off", "Export documents late"],
        "port_to_dc": ["Port congestion", "Customs hold", "Late DC appointment"],
    }
    CAUSE_OVERRIDE = {("SUP-0053", "order_to_factory"): "Mill holding fabric release pending payment (supplier cash constraints)"}

    cutoff = str(g.days_ago(400))
    pos_by_sup = {}
    for po in purchase_orders:
        if po["status"] in ("closed", "received") and po["order_date"] >= cutoff:
            pos_by_sup.setdefault(po["supplier_id"], []).append(po)

    agreed_mean, actual_mean = {}, {}
    for sid, plist in sorted(pos_by_sup.items()):
        if sid not in by_id:
            continue
        plist.sort(key=lambda p: p["order_date"])
        if sid in WINDOW_SAFE or by_id[sid]["country"] == "TR":     # keep story POs clear of the 6 / 12 month rolling-window edges
            plist = [p for p in plist if not (170 <= (as_of - date.fromisoformat(p["order_date"])).days <= 195
                                              or 345 <= (as_of - date.fromisoformat(p["order_date"])).days <= 375)]
        otif = float(by_id[sid]["otif_pct_12m"])
        frac, over = LATE.get(sid, (min(0.6, (100 - otif) / 100 * 2.2), 4))
        shares = STAGE_SHARE.get(sid, (0.50, 0.12, 0.38))
        dw = DELAY_STAGE.get(sid, (0.60, 0.15, 0.25))
        n = len(plist)
        ag_sum = ac_sum = 0
        for i, po in enumerate(plist):
            r = g.rng_for("leadtime", po["po_id"])
            odate, ddate = date.fromisoformat(po["order_date"]), date.fromisoformat(po["due_date"])
            agreed = max(14, (ddate - odate).days)
            late = int((i + 1) * frac) > int(i * frac)
            if late:
                scale = (0.7 + 0.6 * i / max(1, n - 1)) if sid in RAMP else 1.0
                var = max(1, round(over * scale) + r.randint(-2, 2))
            else:
                var = r.choice([-3, -2, -1, 0, 0]) if frac > 0 or sid != "SUP-0039" else r.choice([-2, -1, -1])
            if var > 0:
                d1, d2 = round(var * dw[0]), round(var * dw[1])
                dvar = [d1, d2, max(0, var - d1 - d2)]
                dvar[0] = var - dvar[1] - dvar[2]
            else:
                dvar = [var, 0, 0]
            a1, a2 = round(agreed * shares[0]), round(agreed * shares[1])
            ag = [a1, a2, agreed - a1 - a2]
            ac = [max(1, ag[k] + dvar[k]) for k in range(3)]
            upd = min(ddate, as_of)
            for k, stage in enumerate(STAGES):
                cause = ""
                if dvar[k] > 0:
                    cause = CAUSE_OVERRIDE.get((sid, stage)) or r.choice(CAUSES[stage])
                lead_times.append({
                    "po_id": po["po_id"], "supplier_id": sid, "po_date": po["order_date"],
                    "agreed_lead_time_days": ag[k], "actual_lead_time_days": ac[k], "process_stage": stage,
                    "days_variance": ac[k] - ag[k],
                    "status": "delayed" if ac[k] > ag[k] else ("early" if ac[k] < ag[k] else "completed"),
                    "root_cause_delay": cause, "updated_at": upd})
            tvar = sum(ac) - agreed
            main = max(range(3), key=lambda k: dvar[k]) if tvar > 0 else 0
            lead_times.append({
                "po_id": po["po_id"], "supplier_id": sid, "po_date": po["order_date"],
                "agreed_lead_time_days": agreed, "actual_lead_time_days": sum(ac), "process_stage": "total",
                "days_variance": tvar,
                "status": "delayed" if tvar > 0 else ("early" if tvar < 0 else "completed"),
                "root_cause_delay": (CAUSE_OVERRIDE.get((sid, STAGES[main])) or CAUSES[STAGES[main]][0]) if tvar > 0 else "",
                "updated_at": upd})
            ag_sum += agreed
            ac_sum += sum(ac)
        agreed_mean[sid], actual_mean[sid] = ag_sum / n, ac_sum / n

    # ------------------------------------------------------------------ monthly scorecards (12 completed months)
    OTD = {   # explicit 12-month series for the story suppliers (oldest first); averages sit on master otif_pct_12m
        "SUP-0053": [90, 89, 91, 88, 89, 87, 83, 79, 74, 70, 65, 61],
        "SUP-0070": [98, 98, 99, 98, 98, 97, 98, 97, 97, 93, 89, 85],
        "SUP-0012": [85.8, 86.9, 86.1, 85.4, 86.7, 86.0, 86.5, 85.9, 86.4, 88.4, 85.9, 83.2],
        "SUP-0074": [95.1, 94.6, 94.8, 93.9, 94.2, 93.5, 93.0, 93.4, 92.8, 93.6, 92.9, 92.4],
        "SUP-0001": [88.4, 87.9, 88.8, 88.1, 89.0, 87.6, 88.5, 88.2, 88.7, 87.9, 88.3, 88.0],
        "SUP-0055": [86.0, 85.5, 85.2, 84.6, 84.4, 83.8, 83.5, 82.9, 82.4, 82.0, 81.5, 81.0],
    }
    QUALITY = {
        "SUP-0053": [84, 84, 83, 82, 82, 81, 78, 75, 71, 68, 64, 60],
        "SUP-0055": [86, 86, 85, 84, 82, 80, 77, 74, 71, 69, 67, 65],
        "SUP-0012": [83, 83, 82, 83, 82, 82, 81, 81, 80, 79, 77, 75],
    }
    COMPLIANCE = {
        "SUP-0001": [84, 84, 83, 85, 84, 84, 83, 84, 84, 83, 82, 58],
        "SUP-0053": [78, 78, 77, 77, 76, 75, 72, 69, 66, 63, 60, 57],
    }
    # fixed profiles: quality, cost, responsiveness, reaction hours, flexibility, compliance
    PROFILE = {
        "SUP-0053": (84, 74, 84, 30, 60, 78), "SUP-0044": (95, 80, 97, 14, 92, 94), "SUP-0039": (84, 70, 80, 26, 78, 82), "SUP-0058": (79, 72, 80, 29, 76, 84),
        "SUP-0040": (86, 70, 88, 21, 84, 86), "SUP-0079": (76, 68, 76, 34, 72, 82),
        "SUP-0001": (74, 82, 66, 58, 55, 78), "SUP-0008": (80, 80, 70, 52, 58, 82), "SUP-0016": (84, 79, 72, 49, 62, 85),
        "SUP-0013": (78, 83, 64, 61, 52, 80),
        # long-standing weak performers on small spend (the obvious consolidation exits)
        "SUP-0005": (60, 56, 61, 66, 54, 64), "SUP-0048": (58, 55, 58, 72, 50, 62),
        "SUP-0045": (62, 57, 60, 68, 52, 66), "SUP-0043": (61, 58, 62, 64, 55, 67),
    }
    RISK_Q = {"low": 87, "medium": 82, "high": 76, "critical": 68}
    RISK_C = {"low": 88, "medium": 83, "high": 77, "critical": 69}
    for s in live:
        r = g.rng_for("scorecard", s["supplier_id"])
        sid, risk = s["supplier_id"], s["risk_rating"]
        otif = float(s["otif_pct_12m"])
        prof = PROFILE.get(sid)
        if prof:
            bq, bc, br, bh, bf, bcomp = prof
        else:
            bq, bc = RISK_Q[risk] + r.gauss(0, 3), r.gauss(76, 6)
            br, bh, bf, bcomp = r.gauss(80, 5), clamp(r.gauss(42, 8), 22, 64), r.gauss(70, 7), min(93, RISK_C[risk] + r.gauss(0, 3))
            bq = min(94, bq)
        agreed = round(agreed_mean.get(sid, r.randint(28, 80)))
        actual = actual_mean.get(sid, agreed)
        for idx, month in enumerate(months):
            otd = OTD[sid][idx] if sid in OTD else clamp(otif + r.gauss(0, 1.8), 55, 100)
            quality = QUALITY[sid][idx] if sid in QUALITY else clamp(bq + r.gauss(0, 1.5), 40, 100)
            comp = COMPLIANCE[sid][idx] if sid in COMPLIANCE else clamp(bcomp + r.gauss(0, 1.5), 40, 100)
            cost = clamp(bc + r.gauss(0, 1.5), 40, 100)
            resp = clamp(br + r.gauss(0, 1.5), 40, 100)
            flex = clamp(bf + r.gauss(0, 2), 30, 100)
            react = max(6.0, bh + r.gauss(0, 2))
            if sid == "SUP-0053":                  # distress shows up in responsiveness too
                resp = clamp(84 - max(0, idx - 5) * 3.2 + r.gauss(0, 1), 40, 100)
                react = 30 + max(0, idx - 5) * 6 + r.gauss(0, 2)
            lead = round(actual + (otif - otd) * 0.15 + r.gauss(0, 0.8))
            overall = quality * 0.25 + otd * 0.25 + cost * 0.2 + resp * 0.15 + comp * 0.15
            status = ("strategic" if overall >= 80 else "preferred" if overall >= 70 else "standard" if overall >= 60
                      else "at_risk" if overall >= 40 else "probation")
            scorecards.append({
                "supplier_id": sid, "scorecard_month": month,
                "quality_score": round(quality, 1), "on_time_delivery_pct": round(otd, 1),
                "cost_performance_score": round(cost, 1), "lead_time_days": lead, "agreed_lead_time_days": agreed,
                "responsiveness_score": round(resp, 1), "reaction_time_hours": round(react, 1),
                "flexibility_score": round(flex, 1), "compliance_score": round(comp, 1),
                "overall_score": round(overall, 1), "status_category": status,
                "updated_at": month + timedelta(days=45) if month + timedelta(days=45) <= as_of else as_of})

    # ------------------------------------------------------------------ management cost per supplier
    for s in product_live:
        r = g.rng_for("mgmt", s["supplier_id"])
        sid, spend = s["supplier_id"], float(s["annual_spend_gbp"])
        heavy = 1.7 if sid in ("SUP-0005", "SUP-0048", "SUP-0045", "SUP-0043") else 1.0
        hours = int((70 + 26 * (spend / 1e5) ** 0.5 + r.randint(-12, 18)) * heavy)
        audit = round((1800 + 140 * (spend / 1e5) ** 0.5) * (1.8 if heavy > 1 else 1) + r.randint(0, 900), -1)
        far = s["country"] in ("CN", "VN", "IN", "BD")
        travel = round((4200 if far else 1300) * (1.6 if heavy > 1 else 1) + r.randint(0, 1500), -1)
        systems = 1800 + (600 if spend > 3e6 else 0)
        team = hours * 55
        management_costs.append({
            "supplier_id": sid, "team_hours": hours, "team_cost_gbp": team, "audit_cost_gbp": audit,
            "systems_cost_gbp": systems, "travel_cost_gbp": travel, "total_annual_cost_gbp": team + audit + systems + travel,
            "updated_at": as_of})

    # ------------------------------------------------------------------ relationship status
    WATCH = {"SUP-0055": ("watch", "Repeated quality alerts; reviewed monthly", 60),
             "SUP-0061": ("watch", "Late deliveries on last three POs", 35)}
    for s in suppliers:
        if s["status"] == "exited":
            continue
        st, why, ago = WATCH.get(s["supplier_id"], ("blocked", "Blocked in supplier master", 120) if s["status"] == "blocked"
                                 else ("active", "", None))
        relationships.append({"supplier_id": s["supplier_id"], "status": st, "reason": why,
                              "status_changed_date": g.days_ago(ago) if ago else None,
                              "updated_at": g.days_ago(ago) if ago else as_of})

    # ------------------------------------------------------------------ generic issues (story issues are in seed/)
    ISSUE_TEXT = {
        "quality": ["Seam strength failures found at inline inspection", "Colour variation outside tolerance between lots",
                    "Packaging damage found on arrival at the DC", "Measurement out of tolerance on bulk"],
        "delivery": ["Confirmed ship date missed on {po}", "Partial shipment on {po}, balance promised later"],
        "cost": ["Surcharge requested on {po} after raw material price rise", "Unagreed price change on invoice for {po}"],
        "compliance": ["Missing chemical test report for latest lot", "Social audit corrective actions overdue"],
        "responsiveness": ["Change request on {po} not acknowledged for a week", "Slow response to sample approval comments"],
        "other": ["Master data mismatch on supplier bank details", "Order acknowledgement sent in wrong format"],
    }
    ROOT = {"quality": ["Process deviation at cutting", "Inspection sampling too light"], "delivery": ["Capacity constraint", "Late material"],
            "cost": ["Raw material inflation"], "compliance": ["Documentation gap"], "responsiveness": ["Understaffed planning team"],
            "other": ["Master data not refreshed"]}
    issue_no = 0
    STORY_SUPPLIERS = {"SUP-0053", "SUP-0012", "SUP-0001", "SUP-0055", "SUP-0070", "SUP-0046"}
    for s in pick([x for x in product_live if x["supplier_id"] not in STORY_SUPPLIERS], 26, "issue-pick"):
        r = g.rng_for("issues", s["supplier_id"])
        mypos = [p["po_id"] for p in purchase_orders if p["supplier_id"] == s["supplier_id"]] or ["a recent PO"]
        for _ in range(r.randint(1, 2)):
            itype = r.choice(list(ISSUE_TEXT))
            raised = g.days_ago(r.randint(8, 170))
            resolved = raised + timedelta(days=r.randint(5, 45)) if r.random() < 0.65 else None
            if resolved and resolved > as_of:
                resolved = None
            issue_no += 1
            issues.append({
                "issue_id": f"ISS-{issue_no:06d}", "supplier_id": s["supplier_id"], "issue_type": itype,
                "description": r.choice(ISSUE_TEXT[itype]).format(po=r.choice(mypos)),
                "severity": r.choices(["low", "medium", "high", "critical"], [4, 4, 2, 0.3])[0],
                "status": "closed" if resolved else r.choice(["open", "investigating", "in_progress"]),
                "assigned_to": s["account_manager_id"], "raised_date": raised,
                "target_resolution_date": raised + timedelta(days=r.randint(14, 45)), "resolved_date": resolved,
                "root_cause": r.choice(ROOT[itype]) if resolved else "", "updated_at": resolved or as_of})

    # ------------------------------------------------------------------ generic improvement plans (story plans are in seed/)
    PLAN = {"quality": ("First-pass inspection yield", "88%", "95%"), "delivery": ("On-time delivery %", "82%", "92%"),
            "cost": ("Cost per unit vs index", "+4%", "at index"), "capacity": ("Committed capacity headroom", "8%", "15%"),
            "compliance": ("Open audit findings", "7", "0"), "sustainability": ("Renewable energy share", "10%", "40%")}
    plan_no = 0
    for s in pick([x for x in product_live if x["supplier_id"] not in STORY_SUPPLIERS], 10, "plan-pick"):
        r = g.rng_for("plans", s["supplier_id"])
        ptype = r.choice(list(PLAN))
        metric, base, target = PLAN[ptype]
        start = g.days_ago(r.randint(60, 300))
        status = r.choice(["active", "in_progress", "completed", "suspended"])
        done = status == "completed"
        plan_no += 1
        improvement_plans.append({
            "plan_id": f"SIP-{plan_no:06d}", "supplier_id": s["supplier_id"],
            "plan_name": f"{ptype.capitalize()} improvement: {metric.lower()}", "plan_type": ptype, "focus_area": metric,
            "current_baseline": base, "target_metric": metric, "target_value": target, "start_date": start,
            "target_completion_date": start + timedelta(days=r.randint(90, 180)), "status": status,
            "owner_supplier": f"{s['name']} operations manager", "owner_internal": s["account_manager_id"],
            "progress_pct": 100 if done else r.randint(10, 80),
            "result": f"Target met: {target}" if done else "", "updated_at": as_of})

    # ------------------------------------------------------------------ performance reviews
    review_no = 0
    for s in pick(product_live, 15, "review-pick"):
        r = g.rng_for("reviews", s["supplier_id"])
        for r_idx in range(r.randint(1, 2)):
            review_no += 1
            scheduled = as_of + timedelta(days=r.randint(-75, 25))
            done = scheduled < as_of
            performance_reviews.append({
                "review_id": f"SPR-{review_no:06d}", "supplier_id": s["supplier_id"],
                "review_period": f"Q{(scheduled.month - 1) // 3 + 1} {scheduled.year}",
                "scheduled_date": scheduled, "completed_date": scheduled if done else None,
                "status": "completed" if done else "scheduled",
                "meeting_outcome": r.choice(["Positive progress, no actions", "Areas for improvement agreed", "Delivery recovery plan requested"]) if done else "",
                "internal_owner": s["account_manager_id"], "created_at": scheduled - timedelta(days=30), "updated_at": as_of})

    # ------------------------------------------------------------------ engagement programmes (emissions story rows are in seed/)
    eng_no = 0
    for s in pick([x for x in product_live if x["supplier_id"] not in STORY_SUPPLIERS and x["supplier_id"] not in
                   ("SUP-0057", "SUP-0036", "SUP-0074", "SUP-0044", "SUP-0035", "SUP-0011", "SUP-0013", "SUP-0072")], 8, "eng-pick"):
        r = g.rng_for("engagement", s["supplier_id"])
        eng_no += 1
        prog = r.choice(["sustainability", "innovation", "quality"])
        status = r.choice(["active", "completed", "inactive"])
        invited = g.days_ago(r.randint(120, 330))
        accepted = invited + timedelta(days=r.randint(3, 30))
        start = accepted + timedelta(days=r.randint(1, 10))
        engagement_plans.append({
            "engagement_record_id": f"ENG-{eng_no:06d}", "supplier_id": s["supplier_id"], "programme_type": prog,
            "engagement_status": status, "invitation_sent_date": invited, "acceptance_date": accepted,
            "programme_start_date": start, "target_date": start + timedelta(days=365), "has_science_based_target": False,
            "progress_notes": {"active": "On track", "completed": "Programme completed", "inactive": "Paused at supplier request"}[status],
            "updated_at": as_of})

    # Generate factory capacity data
    for i, supplier in enumerate(suppliers[:20]):
        r = g.rng_for("capacity", supplier["supplier_id"])
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
                    "factory_id": "",
                    "country": supplier["country"],
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

    # Alternative factories for Vietnam suppliers (southern Vietnam port closure scenario).
    # Generic rows above named a supplier's own sites as "alternatives"; replace them with real master factories in
    # other countries (same category). Uses its own rng so the draws above and below are unchanged.
    vn_suppliers = {s["supplier_id"]: s for s in suppliers if s["country"] == "VN"}
    factory_capacity[:] = [row for row in factory_capacity if row["supplier_id"] not in vn_suppliers]
    all_factories = g.master("factories")
    cat_of = {s["supplier_id"]: s["category_focus"] for s in suppliers}
    PINNED = {"SUP-0016": ["FAC-0085", "FAC-0096", "FAC-0084"]}   # Menswear: Murphy Mill (PT), Brown Plant (CN), Slater Dyehouse (PT, small)
    for sid in sorted(vn_suppliers):
        cr = g.rng_for("vn-alt", sid)
        cands = [f for f in all_factories if f["country"] != "VN" and f["status"] == "approved" and f["audit_rating"] in ("A", "B")
                 and cat_of.get(f["supplier_id"]) == vn_suppliers[sid]["category_focus"]]
        if sid in PINNED:
            chosen = [f for f in all_factories if f["factory_id"] in PINNED[sid]]
        else:
            chosen = cr.sample(cands, min(2, len(cands)))
        for f in chosen:
            base_lt = {"PT": 30, "TR": 28, "IT": 30, "MX": 40, "IN": 45, "BD": 48, "CN": 50}.get(f["country"], 40)
            unit = round(cr.uniform(4.5, 9.0), 2)
            cap_total = int(f["capacity_units_month"])
            for k in range(0, 4):
                m = (g.as_of.replace(day=1) + timedelta(days=32 * k)).replace(day=1)
                util = cr.randint(62, 88)
                if sid == "SUP-0016" and f["factory_id"] == "FAC-0084":
                    util = 78 + k                      # small factory: under 10,000 spare units
                committed = int(cap_total * util / 100)
                factory_capacity.append({
                    "supplier_id": sid, "factory_id": f["factory_id"], "country": f["country"],
                    "factory_name": f["name"], "capacity_month": m,
                    "total_capacity_units": cap_total, "committed_capacity_units": committed,
                    "available_capacity_units": cap_total - committed, "capacity_utilization_pct": float(util),
                    "is_alternative_source": True, "lead_time_days": base_lt + cr.randint(-3, 5),
                    "cost_per_unit_gbp": unit, "updated_at": g.as_of})

    # Generate 3PL integration capabilities
    providers = [
        {"name": "DHL Supply Chain", "edi": True, "api": False, "file": True},
        {"name": "Kuehne+Nagel", "edi": True, "api": True, "file": True},
        {"name": "DB Schenker", "edi": True, "api": False, "file": True},
        {"name": "Geodis", "edi": False, "api": True, "file": True},
        {"name": "XPO Logistics", "edi": True, "api": True, "file": True},
    ]

    for i, provider in enumerate(providers):
        r = g.rng_for("3pl", provider["name"])
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
        "supplier_management_costs": management_costs,
        "supplier_relationships": relationships,
    }
