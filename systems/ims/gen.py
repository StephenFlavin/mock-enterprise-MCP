"""IMS background data. Quiet by design: ambient rows are healthy so that seeded stories stand out.

DC positions mirror master.dc_stock. Store positions cover ~12 stores per SKU. weekly_demand is the single
basis for every cover calculation (cover weeks = available / weekly_demand).
"""
import math
from collections import defaultdict
from datetime import timedelta

STORY_SKUS_AT_RISK = {}  # filled below


def generate(g):
    r = g.rng
    products = {p["sku"]: p for p in g.master("products")}
    sites = g.master("sites")
    stores = [s for s in sites if s["type"] == "store" and s["status"] == "open"]
    store_ids = [s["site_id"] for s in stores]
    sqft = {s["site_id"]: float(s["sqft"] or 10000) for s in sites}
    dc_stock = g.master("dc_stock")
    cat_mult = {"Bedding": 1.7, "Towels": 1.5}

    # chain weekly sales per sku (last 8 weeks)
    sw = defaultdict(list)
    for row in g.master("sales_weekly"):
        sw[row["sku"]].append((row["week_start"], int(row["store_units"]), int(row["online_units"])))
    chain_store, chain_online = {}, {}
    for k, v in sw.items():
        v.sort()
        last = v[-8:]
        chain_store[k] = sum(x[1] for x in last) / len(last)
        chain_online[k] = sum(x[2] for x in last) / len(last)

    positions = {}  # (sku, site) -> dict

    def pos(sku, site, on_hand, allocated, demand, age_days, hold=0, cover_floor=None):
        pr = products[sku]
        pos_ = {
            "sku": sku, "site_id": site, "location_id": "", "on_hand": int(on_hand), "allocated": int(allocated),
            "available": int(on_hand - allocated), "hold_qty": hold, "reorder_point": 0, "safety_stock": 0,
            "weekly_demand": round(demand, 1), "received_date": g.days_ago(age_days),
            "updated_at": g.days_ago(r.randint(0, min(age_days, 6))),
        }
        lt = float(pr["lead_time_days"] or 60) / 7
        pos_["safety_stock"] = int(round(demand * 1.5))
        pos_["reorder_point"] = int(round(demand * min(lt, 12) + pos_["safety_stock"]))
        positions[(sku, site)] = pos_
        return pos_

    # ---- DC positions mirror master.dc_stock
    for d in dc_stock:
        sku = d["sku"]
        if sku not in products:
            continue
        cat = products[sku]["category"]
        cover = min(40, max(5.0, r.lognormvariate(math.log(11 * cat_mult.get(cat, 1.0)), 0.4)))
        avail = int(d["available"])
        demand = max(avail / cover, 1.0)
        age = r.randint(5, 110) if r.random() > (0.35 if cat in cat_mult else 0.08) else r.randint(190, 420)
        pos(sku, d["site_id"], int(d["on_hand"]), int(d["allocated"]), demand, age)

    # ---- store positions: each sku ranged in 12 stores
    stories_store = {}  # (sku, site) overrides applied later
    for sku, pr in products.items():
        if sku not in chain_store:
            continue
        cat = pr["category"]
        ranged = r.sample(store_ids, 12)
        w = [sqft[s] for s in ranged]
        tot = sum(w)
        for s, wi in zip(ranged, w):
            demand = max(chain_store[sku] * wi / tot, 0.5)
            cover = min(20.0, max(4.8, r.lognormvariate(math.log(7 * cat_mult.get(cat, 1.0)), 0.3)))
            avail = max(int(round(demand * cover)), 3)
            alloc = int(avail * r.uniform(0, 0.1))
            age = r.randint(3, 90) if r.random() > (0.3 if cat in cat_mult else 0.06) else r.randint(190, 380)
            pos(sku, s, avail + alloc, alloc, demand, age)

    def force(sku, site, avail, demand, allocated=0, age=10, hold=0):
        p = pos(sku, site, avail + allocated, allocated, demand, age, hold)
        return p

    # ======= story positions =======
    # K-1700 / PF-220 at stores (DC2 comes from master.dc_stock)
    for sku, dem in (("K-1700", 8.0), ("PF-220", 7.0)):
        for s in ("ST214", "ST215", "ST216"):
            force(sku, s, 40, dem * (0.9 if s != "ST214" else 1.0), 4, 20)
    # store ST214: K-1700 system shows stock but shelf gaps
    force("K-1700", "ST214", 8, 8.0, 4, 12)
    force("PF-220", "ST214", 18, 7.0, 2, 15)
    force("SKU-101904", "ST214", 10, 6.0, 2, 10)
    force("SKU-103892", "ST214", 12, 5.0, 2, 10)

    # STY-5520 stockout story: SKU-101904 in 40 stores
    story_stores = r.sample([s for s in store_ids if s != "ST214"], 39) + ["ST214"]
    for s in story_stores:
        force("SKU-101904", s, r.randint(25, 45), r.uniform(5, 7), 0, r.randint(5, 20))
    # at risk of stockout in next 4 weeks (list_projected_stockouts)
    risk = [("SKU-105159", "ST150", 14, 40), ("SKU-101834", "ST159", 20, 55), ("SKU-102338", "ST165", 18, 45),
            ("SKU-105341", "ST214", 12, 36), ("SKU-100644", "ST216", 15, 50), ("SKU-101848", "ST215", 9, 30)]
    for sku, s, avail, dem in risk:
        force(sku, s, avail, dem, 0, 20)
    # shipment SHP-0000102 (PO-2026-004121) SKUs are low in stores
    for sku, s, avail, dem in (("SKU-103458", "ST214", 6, 28), ("SKU-103458", "ST150", 5, 24), ("SKU-104438", "ST159", 4, 20),
                               ("SKU-104438", "ST165", 3, 18), ("SKU-104445", "ST215", 5, 22)):
        force(sku, s, avail, dem, 0, 25)
    # EU stores low on Smart Home / Small Appliances (port closure story)
    eu = [s["site_id"] for s in stores if s["region"] == "EU Central"][:6]
    sa = [k for k, p in products.items() if p["category"] == "Smart Home"][:4]
    for i, s in enumerate(eu):
        for sku in sa:
            force(sku, s, 14 + i, 9.0, 0, 30)
    # Bay C-14 story SKUs at DC1 are held in bins (location level rows)
    bay_skus = ["SKU-100084", "SKU-100028", "SKU-100035"]
    for sku in bay_skus:
        base = positions.pop((sku, "DC1"))
        tot = base["on_hand"]
        shares = [0.45, 0.35, 0.20]
        for loc, sh in zip(("DC1-C-14-01", "DC1-C-14-02", "DC1-C-14-03"), shares):
            q = int(tot * sh)
            row = dict(base)
            row.update({"location_id": loc, "on_hand": q, "allocated": int(base["allocated"] * sh),
                        "available": q - int(base["allocated"] * sh), "hold_qty": 0})
            positions[(sku + "@" + loc, "DC1")] = row
    # PF-220 and K-1700 DC2 demand (master stock; chain sales ~ 240/week)
    for sku, dem in (("K-1700", 240.0), ("PF-220", 260.0)):
        p = positions[(sku, "DC2")]
        p["weekly_demand"] = dem
        p["safety_stock"] = int(dem * 1.5)
        p["reorder_point"] = int(dem * 15 + p["safety_stock"])
    # website variance (DC2 only): small ambient drift, K-1700 story
    # (web columns are not stored; see tool)

    pos_rows = list(positions.values())
    # held / ageing story: Bedding aged stock already via cat_mult

    # ================= adjustments (quiet ambient, small values) =================
    adjustments = []
    causes = ["shrink", "damage", "receiving_variance", "cycle_count_variance", "picking_error", "receiving_error"]
    pos_keys = [k for k in positions if "@" not in k[0]]
    n = 0
    window_stores = store_ids[:60]
    for _ in range(420):
        n += 1
        sku, site = r.choice(pos_keys)
        if r.random() < 0.15:
            site = r.choice(["DC1", "DC2", "DC3"])
            sku = r.choice([k[0] for k in pos_keys if k[1] == site])
        if site in ("ST165", "ST214"):
            continue
        qty = -r.randint(1, 6) if r.random() < 0.8 else r.randint(1, 4)
        cost = float(products[sku]["unit_cost_gbp"] or 10)
        age = r.randint(0, 95)
        c = g.days_ago(age)
        posted = r.random() < 0.85
        adjustments.append({
            "adjustment_id": f"INV-ADJ-{n:06d}", "sku": sku, "site_id": site, "location_id": None,
            "quantity_delta": qty, "cause_code": r.choice(causes), "reference_id": None,
            "status": "posted" if posted else "pending", "user_id": None,
            "reason_notes": "Variance found during count" if r.random() < 0.5 else "",
            "value_impact_gbp": round(qty * cost, 2),
            "created_at": f"{c} {r.randint(7, 20):02d}:{r.randint(0, 59):02d}",
            "posted_at": f"{c} 23:00" if posted else None, "reversed_at": None, "reversal_reason": None,
            "updated_at": f"{c} 23:00",
        })

    # ================= shrink analysis aggregated from adjustments + synthetic history =================
    shrink = []
    shrink_causes = {"shrink": "shrink", "theft": "theft", "loss": "shrink", "picking_error": "picking error",
                     "receiving_error": "receiving error", "damage": "damage"}
    cats = ["Knitwear", "Dresses", "Outerwear", "Bedding", "Small Appliances", "Fragrance"]
    for s in store_ids[:60] + ["ST165", "ST214"]:
        if s in [x["site_id"] for x in shrink]:
            continue
    seen = set()
    for s in dict.fromkeys(store_ids[:60] + ["ST165", "ST214", "ST215", "ST216"]):
        base = r.uniform(0.7, 1.1)
        for wk in range(0, 40):
            monday = g.as_of - timedelta(days=g.as_of.weekday()) - timedelta(weeks=wk + 1)
            for cat in cats:
                v = r.uniform(20, 90) * base
                shrink.append({"site_id": s, "category": cat, "analysis_week": monday,
                               "shrink_units": max(int(v / 12), 1), "shrink_value_gbp": round(v, 2),
                               "shrink_rate_pct": round(r.uniform(0.5, 1.1) * base, 2),
                               "vs_peer_avg_pct": round(r.uniform(-0.15, 0.15), 2),
                               "main_cause": r.choice(["shrink", "theft", "picking error", "receiving error"])})

    # ================= availability tracking: weekly panel, quota-driven OOS rate =================
    panel_sites = list(dict.fromkeys(["ST214", "ST215", "ST216", "ST150", "ST159", "ST165", "ST164", "ST181", "ST183"] + store_ids[:30]))
    panel_pairs = []
    by_site = defaultdict(list)
    for (sku, site), p in positions.items():
        if "@" in sku:
            continue
        by_site[site].append(sku)
    for s in panel_sites:
        lst = [k for k in by_site[s] if k not in ("K-1700", "PF-220", "SKU-101904")]
        for k in r.sample(lst, min(len(lst), 28)):
            panel_pairs.append((k, s))
    for dc in ("DC1", "DC2", "DC3", "DC4", "DC5"):
        lst = by_site[dc]
        for k in r.sample(lst, min(len(lst), 60)):
            panel_pairs.append((k, dc))
    weeks = g.weeks(12)  # Mondays, oldest first
    rate_by_week = [4.0] * 7 + [4.6, 5.4, 6.0, 6.5, 6.5]
    rate_by_week = rate_by_week[-12:]
    # causes per week (extra OOS above baseline)
    base_causes = ["forecast_under", "allocation_shortfall", "supplier_late", "dc_receiving_delay", "count_error"]
    base_w = [0.35, 0.25, 0.2, 0.1, 0.1]
    sup13 = [p for p in panel_pairs if products[p[0]]["supplier_id"] == "SUP-0013"]
    dc2_pairs = [p for p in panel_pairs if p[1] == "DC2"]
    promo_pairs = [p for p in panel_pairs if products[p[0]]["category"] == "Dresses"]
    tracking = {}

    def trow(sku, site, d, oos, days, cause):
        p = positions.get((sku, site))
        dem = p["weekly_demand"] if p else 5.0
        qty = 0 if oos else (p["available"] if p else r.randint(5, 40))
        lost = int(round(dem / 7 * days)) if oos else 0
        return {"sku": sku, "site_id": site, "tracking_date": d, "available": not oos, "quantity_available": qty,
                "demand_units": int(round(dem)), "lost_sales": lost, "forecast_available": True if not oos else (cause != "forecast_under"),
                "stockout_days": days if oos else 0, "stockout_cause": cause if oos else None}

    story_rows = []
    # STY-5520: SKU-101904 out in 40 stores for 9 days starting Tuesday of week 4 ago
    ev_start = weeks[-4] + timedelta(days=1)
    for s in story_stores:
        row = trow("SKU-101904", s, ev_start, True, 9, "allocation_shortfall")
        row["forecast_available"] = True
        story_rows.append(row)
    # K-1700 ST214 gaps (weekly rows)
    for wk, days in ((weeks[-3], 2), (weeks[-2], 3), (weeks[-1], 2)):
        story_rows.append(trow("K-1700", "ST214", wk + timedelta(days=2), True, days, "back_room_stock"))
    story_rows.append(trow("PF-220", "ST214", weeks[-1], False, 0, None))
    for s in ("ST215", "ST216"):
        for wk in weeks[-6:]:
            story_rows.append(trow("K-1700", s, wk, False, 0, None))
    for wk in weeks[-8:-3]:
        story_rows.append(trow("K-1700", "ST214", wk, False, 0, None))
    for row in story_rows:
        tracking[(row["sku"], row["site_id"], row["tracking_date"])] = row
    for wi, wk in enumerate(weeks):
        story_oos = sum(1 for k, v in tracking.items() if not v["available"] and wk <= k[2] < wk + timedelta(days=7))
        story_all = sum(1 for k in tracking if wk <= k[2] < wk + timedelta(days=7))
        total_rows = len(panel_pairs) + story_all
        target = int(round(rate_by_week[wi] / 100 * total_rows)) - story_oos
        target = max(target, 0)
        oos_idx = set()
        extra = []
        if wi >= 7:  # rising: supplier SUP-0013 persists; DC2 backlog and promo spike are one-offs
            e = wi - 6
            extra += [("supplier_late", p) for p in r.sample(sup13, min(len(sup13), 6 * e))]
            if wi in (9, 10):
                extra += [("dc_receiving_delay", p) for p in r.sample(dc2_pairs, min(len(dc2_pairs), 18))]
            if wi == 10:
                extra += [("promo_demand_spike", p) for p in r.sample(promo_pairs, min(len(promo_pairs), 15))]
        forced = {}
        for cause, p in extra:
            if len(forced) < target:
                forced.setdefault(p, cause)
        rest = [p for p in panel_pairs if p not in forced]
        need = target - len(forced)
        for p in r.sample(rest, max(need, 0)):
            forced[p] = r.choices(base_causes, base_w)[0]
        for p in panel_pairs:
            key = (p[0], p[1], wk)
            if key in tracking:
                continue
            if p in forced:
                tracking[key] = trow(p[0], p[1], wk, True, r.randint(1, 7), forced[p])
            else:
                tracking[key] = trow(p[0], p[1], wk, False, 0, None)
    availability = list(tracking.values())

    # ================= lost products: two years, ambient small =================
    losses = []
    n = 0
    ambient_sites = store_ids[:80] + ["DC1", "DC2", "DC3"]
    for _ in range(420):
        n += 1
        sku = r.choice(list(chain_store))
        site = r.choice(ambient_sites)
        qty = r.randint(1, 8)
        cost = float(products[sku]["unit_cost_gbp"] or 10)
        losses.append({
            "loss_id": f"LOSS-{n:06d}", "sku": sku, "site_id": site,
            "loss_type": r.choice(["damage", "expiry", "shrink", "theft", "markdown", "damage"]),
            "quantity": qty, "value_gbp": round(qty * cost, 2), "identified_date": g.days_ago(r.randint(0, 700)),
            "batch_or_serial": None, "notes": "Inventory loss"})

    # ================= cycle counts (quiet ambient) =================
    counts, results = [], []
    # completed history for DCs is seeded; ambient: scheduled counts at stores
    for i in range(1, 9):
        s = r.choice(store_ids)
        counts.append({"cycle_count_id": f"CC-{i:06d}", "site_id": s, "category": r.choice(["Dresses", "Bedding", "Knitwear"]),
                       "location_id": None, "scheduled_date": g.days_ago(-r.randint(1, 30)), "status": "scheduled",
                       "reason": "Regular inventory check", "counted_by": None, "counted_at": None,
                       "result_summary": None, "created_at": g.days_ago(r.randint(5, 30))})

    # ================= stock plan (normal value, cover target, closing plan) =================
    from datetime import date
    season_end = date(g.as_of.year + 1 if g.as_of.month >= 8 else g.as_of.year, 1 if g.as_of.month >= 8 else 7, 31)
    wks_left = (season_end - g.as_of).days / 7
    agg = defaultdict(lambda: [0.0, 0.0, 0.0])
    for p in pos_rows:
        pr = products[p["sku"]]
        a = agg[(p["site_id"], pr["category"])]
        a[0] += p["on_hand"] * float(pr["unit_cost_gbp"] or 0)
        a[1] += max(p["on_hand"] - p["weekly_demand"] * wks_left, 0)
        a[2] += 1
    plan = []
    for (site, cat), (val, close, _) in agg.items():
        f = 0.68 if cat in cat_mult else r.uniform(0.95, 1.08)
        plan.append({"site_id": site, "category": cat, "plan_value_gbp": round(val * f, 2),
                     "plan_cover_weeks": 10.7, "plan_closing_units": int(close * f), "period_end": season_end})

    return {
        "stock_plan": plan,
        "inventory_positions": pos_rows,
        "inventory_adjustments": adjustments,
        "cycle_count_tasks": counts,
        "cycle_count_results": results,
        "stock_reservations": [],
        "store_transfers": [],
        "stock_release_plans": [],
        "shrink_analysis": shrink,
        "availability_tracking": availability,
        "lost_products": losses,
    }
