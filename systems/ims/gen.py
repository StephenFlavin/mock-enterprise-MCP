"""IMS background data. Quiet by design: ambient rows are healthy so that seeded stories stand out.

DC positions mirror master.dc_stock. Store positions cover ~12 stores per SKU. weekly_demand is the single
basis for every cover calculation (cover weeks = available / weekly_demand).
"""
import math
from collections import defaultdict
from datetime import timedelta

STORY_SKUS_AT_RISK = {}  # filled below
LONG_TAIL_UNITS = 140.0  # chain units/week; master sales are scaled x6.8, so the old 20 is now about 140


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

    def pos(sku, site, on_hand, allocated, demand, age_days, hold=0, cover_floor=None, rr=None):
        rr = rr or r
        pr = products[sku]
        pos_ = {
            "sku": sku, "site_id": site, "location_id": "", "on_hand": int(on_hand), "allocated": int(allocated),
            "available": int(on_hand - allocated), "hold_qty": hold, "reorder_point": 0, "safety_stock": 0,
            "weekly_demand": round(demand, 1), "received_date": g.days_ago(age_days),
            "updated_at": g.days_ago(rr.randint(0, min(age_days, 6))),
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
        dr = g.rng_for("dcpos", sku, d["site_id"])  # per-entity stream: new master rows never shift other positions
        cover = min(40, max(5.0, dr.lognormvariate(math.log(11 * cat_mult.get(cat, 1.0)), 0.4)))
        avail = int(d["available"])
        demand = max(avail / cover, 1.0)
        age = dr.randint(5, 110) if dr.random() > (0.35 if cat in cat_mult else 0.08) else dr.randint(190, 420)
        pos(sku, d["site_id"], int(d["on_hand"]), int(d["allocated"]), demand, age, rr=dr)

    # ---- store positions: each sku ranged in 12 stores
    stories_store = {}  # (sku, site) overrides applied later
    for sku, pr in products.items():
        if sku not in chain_store:
            continue
        cat = pr["category"]
        sr = g.rng_for("storepos", sku)  # per-SKU stream: new master rows never shift other positions
        ranged = sr.sample(store_ids, 12)
        w = [sqft[s] for s in ranged]
        tot = sum(w)
        for s, wi in zip(ranged, w):
            demand = max(chain_store[sku] * wi / tot, 0.5)
            cover = min(20.0, max(4.8, sr.lognormvariate(math.log(7 * cat_mult.get(cat, 1.0)), 0.3)))
            avail = max(int(round(demand * cover)), 3)
            alloc = int(avail * sr.uniform(0, 0.1))
            age = sr.randint(3, 90) if sr.random() > (0.3 if cat in cat_mult else 0.06) else sr.randint(190, 380)
            pos(sku, s, avail + alloc, alloc, demand, age, rr=sr)

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
    story_stores = g.rng_for("story5520").sample([s for s in store_ids if s != "ST214"], 39) + ["ST214"]
    for s in story_stores:
        force("SKU-101904", s, r.randint(25, 45), r.uniform(5, 7), 0, r.randint(5, 20))
    # at risk of stockout in next 4 weeks (list_projected_stockouts)
    risk = [("SKU-105159", "ST150", 14, 40), ("SKU-101834", "ST159", 20, 55), ("SKU-102338", "ST165", 18, 45),
            ("SKU-105341", "ST214", 12, 36), ("SKU-101575", "ST216", 15, 50), ("SKU-101848", "ST215", 9, 30)]
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
                        "available": q - int(base["allocated"] * sh), "hold_qty": 0,
                        "weekly_demand": round(base["weekly_demand"] * sh, 1),
                        "safety_stock": int(base["safety_stock"] * sh), "reorder_point": int(base["reorder_point"] * sh)})
            positions[(sku + "@" + loc, "DC1")] = row
    # PF-220 and K-1700 DC2 demand: DC2 is the e-commerce DC, so it issues the chain's online units (master sales_weekly)
    for sku in ("K-1700", "PF-220"):
        dem = round(chain_online[sku], 1)
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
        sh = g.rng_for("shrink", s)
        base = sh.uniform(0.7, 1.1)
        if s == "ST214":
            base = 1.2  # story 08:71: ST214 shrink is high against its cluster
        for wk in range(0, 40):
            monday = g.as_of - timedelta(days=g.as_of.weekday()) - timedelta(weeks=wk + 1)
            for cat in cats:
                v = sh.uniform(20, 90) * base
                rate = round(sh.uniform(0.5, 1.1) * base, 2)
                peer = round(sh.uniform(-0.15, 0.15), 2)
                cause = sh.choice(["shrink", "theft", "picking error", "receiving error"])
                if cat == "Knitwear" and wk < 5:  # story: knitwear theft spike over the last month
                    v *= 1.45
                    rate = round(rate + 0.45, 2)
                    peer = round(peer + 0.4, 2)
                    cause = "theft" if int(v * 100) % 5 else cause
                shrink.append({"site_id": s, "category": cat, "analysis_week": monday,
                               "shrink_units": max(int(v / 12), 1), "shrink_value_gbp": round(v, 2),
                               "shrink_rate_pct": rate, "vs_peer_avg_pct": peer, "main_cause": cause})

    # UK North patch: every northern store has shrink history (own random stream, so nothing else moves).
    # Region norm is about 1.0-1.1%; Preston High Street 2 (ST143), Preston High Street (ST142) and Leeds Shopping Centre
    # (ST150) run at 2.1% or more. Durham (ST144) is healthy.
    north = [x["site_id"] for x in sites if x["type"] == "store" and x["region"] == "UK North" and x["status"] == "open"]
    have = {x["site_id"] for x in shrink}
    north_bad = {"ST143": 2.6, "ST142": 2.3, "ST150": 2.2}
    for s_ in north:
        if s_ in have:
            continue
        nr = g.rng_for("northshrink", s_)
        base = north_bad.get(s_, 0.8 if s_ == "ST144" else nr.uniform(0.68, 0.86))
        size = min(max(sqft[s_] / 20000.0, 0.5), 1.6)
        for wk in range(0, 40):
            monday = g.as_of - timedelta(days=g.as_of.weekday()) - timedelta(weeks=wk + 1)
            for cat in cats:
                rate = round(base * nr.uniform(0.85, 1.15), 2)
                peer = round(rate - 1.0, 2)
                cause = nr.choice(["shrink", "theft", "picking error", "receiving error"])
                if s_ in north_bad:
                    cause = nr.choice(["theft", "theft", "shrink", "receiving error"])
                if cat == "Knitwear" and wk < 5:
                    rate = round(rate + 0.45, 2)
                    peer = round(peer + 0.4, 2)
                    cause = "theft"
                v = rate * nr.uniform(40, 80) * size
                shrink.append({"site_id": s_, "category": cat, "analysis_week": monday,
                               "shrink_units": max(int(v / 12), 1), "shrink_value_gbp": round(v, 2),
                               "shrink_rate_pct": rate, "vs_peer_avg_pct": peer, "main_cause": cause})

    # ================= availability tracking: weekly panel, quota-driven OOS rate =================
    panel_sites = list(dict.fromkeys(["ST214", "ST215", "ST216", "ST150", "ST159", "ST165", "ST164", "ST181", "ST183"] + store_ids[:30]))
    panel_pairs = []
    by_site = defaultdict(list)
    for (sku, site), p in positions.items():
        if "@" in sku:
            continue
        by_site[site].append(sku)
    for s in panel_sites:
        lst = sorted(k for k in by_site[s] if k not in ("K-1700", "PF-220", "SKU-101904"))
        for k in g.rng_for("panel", s).sample(lst, min(len(lst), 28)):
            panel_pairs.append((k, s))
    for dc in ("DC1", "DC2", "DC3", "DC4", "DC5"):
        lst = sorted(by_site[dc])
        for k in g.rng_for("panel", dc).sample(lst, min(len(lst), 60)):
            panel_pairs.append((k, dc))
    weeks = g.weeks(12)  # Mondays, oldest first
    rate_by_week = [4.0] * 7 + [4.6, 5.4, 6.0, 6.5, 6.5]
    rate_by_week = rate_by_week[-12:]
    # causes per week (extra OOS above baseline)
    base_causes = ["forecast_under", "allocation_shortfall", "supplier_late", "count_error", "stock_record_error"]
    base_w = [0.35, 0.25, 0.2, 0.1, 0.1]
    sup13 = [p for p in panel_pairs if products[p[0]]["supplier_id"] == "SUP-0013"]
    dc2_pairs = [p for p in panel_pairs if p[1] == "DC2"]
    promo_pairs = [p for p in panel_pairs if products[p[0]]["category"] == "Dresses"]
    tracking = {}
    panel_set = {(a, b, w) for (a, b) in panel_pairs for w in weeks}

    def trow(sku, site, d, oos, days, cause, scale=1.0):
        p = positions.get((sku, site))
        dem = p["weekly_demand"] if p else 5.0
        qty = 0 if oos else (p["available"] if p else r.randint(5, 40))
        lost = int(round(dem / 7 * days * scale)) if oos else 0
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
    # Wholesale orders (customer PTN-001): DC1 stock position in the weeks around each order. The first order (800 units
    # of SKU-100469) met only 560 units on hand; later orders were covered.
    def put(sku, site, wk, qty, dem, cause=None, lost=0, days=0):
        story_rows.append({"sku": sku, "site_id": site, "tracking_date": wk, "available": qty > 0, "quantity_available": qty,
                           "demand_units": dem, "lost_sales": lost, "forecast_available": True,
                           "stockout_days": days, "stockout_cause": cause})
    for back, q in ((8, 560), (7, 560), (6, 2400), (5, 2280), (4, 2150), (3, 2100), (2, 2000)):
        put("SKU-100469", "DC1", weeks[1 - back], q, 150)
    for back, q in ((8, 900), (7, 880), (5, 1900), (4, 1800), (3, 1700), (2, 1650)):
        put("SKU-100476", "DC1", weeks[1 - back], q, 120)
    for back, q in ((5, 1550), (4, 1500), (3, 1450), (2, 1400)):
        put("SKU-100483", "DC1", weeks[1 - back], q, 100)
    # Promotion PROMO-900001 (Bedding, 20% off): hero SKU-104949 had only half its stock confirmed and was out of stock in
    # most panel stores during the event; hero SKU-104942 was fully confirmed and stayed in stock.
    promo_stores = ["ST214", "ST215", "ST216", "ST150", "ST159", "ST165", "ST164", "ST181", "ST183", "ST109"]
    promo_out = {-3: {"ST214", "ST215", "ST216", "ST150", "ST159", "ST165", "ST164"},
                 -2: {"ST214", "ST215", "ST150", "ST159", "ST165", "ST181"}}
    for back, outs in promo_out.items():
        for st in promo_stores:
            if st in outs:
                put("SKU-104949", st, weeks[back + 1], 0, 48, "supplier_late", 34, 5)
            else:
                put("SKU-104949", st, weeks[back + 1], 60, 48)
            put("SKU-104942", st, weeks[back + 1], 90, 60)
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
                tracking[key] = trow(p[0], p[1], wk, True, r.randint(1, 7), forced[p],
                                     0.1 if p[1].startswith("DC") else 0.2)  # ambient: keep story stockouts dominant
            else:
                tracking[key] = trow(p[0], p[1], wk, False, 0, None)
    availability = list(tracking.values())

    # Availability story for product comparisons (06:52:Q2): three lines were short of stock about half of the time over the last
    # twelve weeks. The weekly out-of-stock total is unchanged: each added gap is offset by one ambient gap that closes.
    import hashlib as _hl

    def _hh(*a):
        return int(_hl.md5("|".join(map(str, a)).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF

    POOR_AVAIL = {"SKU-100651", "SKU-103297", "SKU-103283"}  # 06:52:Q2: a top-3 and two bottom-10 sellers (data_warehouse SS ranking)
    keep_out = POOR_AVAIL | {"SKU-101904", "K-1700", "PF-220"}
    for wk in weeks:
        flipped = 0
        for key, row in list(tracking.items()):
            if key[2] != wk or key[0] not in POOR_AVAIL or not row["available"]:
                continue
            if _hh("poor", *key) < 0.5:
                tracking[key] = trow(key[0], key[1], wk, True, 1 + int(_hh("d", *key) * 6),
                                     "forecast_under" if _hh("c", *key) < 0.5 else "allocation_shortfall", 0.2)
                flipped += 1
        pool = sorted((k for k, v in tracking.items() if k[2] == wk and not v["available"] and v["stockout_cause"] in base_causes
                       and k[0] not in keep_out), key=lambda k: _hh("heal", *k))
        for k in pool[:flipped]:
            tracking[k] = trow(k[0], k[1], wk, False, 0, None)
    # UK North patch availability: Preston stores (ST142, ST143) are below 95% in stock; Durham (ST144) is strong.
    # Weekly out-of-stock counts follow the network rate so network totals barely move. Deterministic hashing only.
    north_av = {"ST142": [2, 2, 1, 2, 2, 1, 2, 2, 2, 3, 3, 3], "ST143": [1, 2, 2, 1, 2, 2, 2, 2, 3, 2, 2, 2],
                "ST144": [0] * 12}
    for s_, oos_counts in north_av.items():
        lst = sorted((k for k in by_site[s_] if k not in keep_out and "@" not in k), key=lambda k: _hh("north", s_, k))[:28]
        for wi, wk in enumerate(weeks):
            order = sorted(lst, key=lambda k: _hh("nwk", s_, k, wk))
            out = set(order[:oos_counts[wi]])
            for k in lst:
                key = (k, s_, wk)
                if key in tracking:
                    continue
                oos = k in out
                cause = ("allocation_shortfall" if _hh("nc", s_, k, wk) < 0.7 else "forecast_under") if oos else None
                tracking[key] = trow(k, s_, wk, oos, 1 + int(_hh("nd", s_, k, wk) * 6) if oos else 0, cause)
    # 06:52:Q2 pins the in-stock records of five lines (the data_warehouse sales ranking quotes the same rates): best sellers
    # SKU-100637 (all in stock) and SKU-100651 (5 of 12), worst sellers SKU-104186 (all), SKU-103283 (14 of 24) and
    # SKU-103297 (12 of 24). Per week, every gap added or removed here is offset by an ambient gap elsewhere.
    PIN_IN = {"SKU-100637": None, "SKU-104186": None, "SKU-100651": 5, "SKU-103283": 14, "SKU-103297": 12}
    pinned = set(PIN_IN)
    delta = defaultdict(int)  # week -> OOS rows added (+) or removed (-)
    for sku, n_in in PIN_IN.items():
        rows = sorted((k for k in tracking if k[0] == sku), key=lambda k: _hh("pin", *k))
        n_keep = len(rows) if n_in is None else n_in
        for i, k in enumerate(rows):
            want_in = i < n_keep
            if tracking[k]["available"] != want_in:
                tracking[k] = trow(k[0], k[1], k[2], not want_in, 1 + int(_hh("pd", *k) * 6),
                                   "forecast_under" if _hh("pc", *k) < 0.5 else "allocation_shortfall", 0.2)
                delta[k[2]] += -1 if want_in else 1
    for wk, d in sorted(delta.items()):
        if d > 0:
            pool = sorted((k for k, v in tracking.items() if k[2] == wk and not v["available"] and v["stockout_cause"] in base_causes
                           and k[0] not in keep_out and k[0] not in pinned), key=lambda k: _hh("heal2", *k))
            for k in pool[:d]:
                tracking[k] = trow(k[0], k[1], wk, False, 0, None)
        elif d < 0:
            pool = sorted((k for k, v in tracking.items() if k[2] == wk and v["available"] and k in panel_set
                           and k[0] not in keep_out and k[0] not in pinned), key=lambda k: _hh("break2", *k))
            for k in pool[:-d]:
                tracking[k] = trow(k[0], k[1], wk, True, 1 + int(_hh("bd", *k) * 6), "forecast_under", 0.2)
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

    # ================= PF-220 batches (consistent with positions) =================
    batches = []
    for (sku, site), p in positions.items():
        if sku != "PF-220":
            continue
        a = int(round(p["on_hand"] * (0.59 if site == "DC2" else 0.7)))
        for bid, q, age, st in (("BATCH-PF220-2509-A", a, 40, "quarantine"), ("BATCH-PF220-2508-B", p["on_hand"] - a, 70, "released")):
            if q > 0:
                batches.append({"batch_id": bid, "sku": sku, "site_id": site, "location_id": "", "on_hand": q,
                                "received_date": g.days_ago(age), "status": st})

    # ================= story positions applied after all random draws (deterministic, no rng) =================
    import hashlib

    def h(*a):
        return int(hashlib.md5("|".join(map(str, a)).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF

    region = {s["site_id"]: s["region"] for s in sites}

    def mkrow(sku, site, avail, demand, allocated=0, age=14, loc=""):
        pr = products[sku]
        lt = float(pr["lead_time_days"] or 60) / 7
        ss = int(round(demand * 1.5))
        return {"sku": sku, "site_id": site, "location_id": loc, "on_hand": int(avail + allocated), "allocated": int(allocated),
                "available": int(avail), "hold_qty": 0, "reorder_point": int(round(demand * min(lt, 12) + ss)),
                "safety_stock": ss, "weekly_demand": round(demand, 1), "received_date": g.days_ago(age),
                "updated_at": g.days_ago(int(h(sku, site) * 5))}

    # (1) seasonal bedding throw SKU-104963: northern stores nearly sold out, southern stores overstocked
    THROW = "SKU-104963"
    pos_rows = [p for p in pos_rows if not (p["sku"] == THROW and p["site_id"].startswith("ST"))]
    north = sorted(x for x in store_ids if region[x] == "UK North")[:6]
    south = sorted(x for x in store_ids if region[x] == "UK South")[:6]
    for i, st in enumerate(north):
        pos_rows.append(mkrow(THROW, st, 9 + int(h(st) * 9), 24 + int(h(st, 1) * 8), 0, 12))
    for i, st in enumerate(south):
        pos_rows.append(mkrow(THROW, st, 470 + int(h(st) * 120), 13 + int(h(st, 1) * 6), 0, 40))

    # (2) Tops (athleisure) range: size 14 under-bought, size 10 over-bought, Scottish stores over-allocated
    TOPS_STYLES = {"STY-4056", "STY-5079", "STY-5130", "STY-8004", "STY-9033"}
    tops = {p["sku"]: p for p in products.values() if p["style_id"] in TOPS_STYLES}
    scot = ["ST201", "ST204", "ST207", "ST212", "ST214"]
    others = ["ST143", "ST147", "ST144", "ST165", "ST164", "ST003", "ST149", "ST004", "ST181", "ST150",
              "ST148", "ST141", "ST142", "ST145", "ST151"]
    pos_rows = [p for p in pos_rows if not (p["sku"] in tops and p["site_id"].startswith("ST"))]
    for sku, pr in tops.items():
        sz = pr["size"]
        for st in scot + others:
            sc = st in scot
            if sz == "10":
                avail, dem = (70 + int(h(sku, st) * 20), 2.4) if sc else (34 + int(h(sku, st) * 10), 3.0)
            elif sz == "12":
                avail, dem = (55 + int(h(sku, st) * 15), 4.4) if sc else (26 + int(h(sku, st) * 8), 6.0)
            else:
                avail, dem = (11 + int(h(sku, st) * 4), 3.6) if sc else ((0 if h(sku, st, "x") < 0.6 else 2 + int(h(sku, st) * 3)), 5.0)
            pos_rows.append(mkrow(sku, st, avail, dem, 0, 30))

    # (3) policy parameters held in IMS match the inv_opt policy table for the too-low SKUs
    for p in pos_rows:
        k = (p["sku"], p["site_id"], p["location_id"])
        if k == ("SKU-104018", "DC5", ""):
            p["reorder_point"], p["safety_stock"] = 12639, 1949
        if k == ("SKU-103234", "DC2", ""):
            p["reorder_point"], p["safety_stock"] = 34772, 5131

    # (3b) SKU-103227 (container CONT-000078 story): ST186 is the clear first store to run out, 3.9 weeks of cover.
    pos_rows = [p for p in pos_rows if not (p["sku"] == "SKU-103227" and p["site_id"] == "ST186")]
    pos_rows.append(mkrow("SKU-103227", "ST186", int(3.9 * 112.1), 112.1, 0, 20))

    # (4) DC1 stock is held in bins: spread each SKU over one or two bins in aisles A-F
    recent = {"DC1-A-01-01", "DC1-A-02-01"}
    pool = [l["location_id"] for l in g.master("locations")
            if l["site_id"] == "DC1" and l["status"] == "active" and l["aisle"] in "ABCDEF"
            and l["zone"] in ("pick", "reserve", "bulk", "mezzanine") and not l["location_id"].startswith("DC1-C-14")
            and l["location_id"] not in recent]
    pool = sorted(pool, key=lambda x: h("pool", x))[:300]
    out = []
    for p in pos_rows:
        if p["site_id"] != "DC1" or p["location_id"]:
            out.append(p)
            continue
        sh = [1.0] if p["on_hand"] < 2000 else [0.6, 0.4]
        used = set()
        for j, share in enumerate(sh):
            idx = int(h(p["sku"], j) * len(pool))
            while pool[idx] in used:
                idx = (idx + 1) % len(pool)
            used.add(pool[idx])
            row = dict(p)
            q = int(p["on_hand"] * share) if j == 0 else p["on_hand"] - int(p["on_hand"] * sh[0])
            al = int(p["allocated"] * share) if j == 0 else p["allocated"] - int(p["allocated"] * sh[0])
            row.update({"location_id": pool[idx], "on_hand": q, "allocated": al, "available": q - al,
                        "weekly_demand": round(p["weekly_demand"] * share, 1),
                        "safety_stock": int(p["safety_stock"] * share), "reorder_point": int(p["reorder_point"] * share)})
            out.append(row)
    pos_rows = out

    # (5) Men's jacket style STY-4102 after a 30% markdown: stock left is mostly broken size runs in stores.
    JACKET = [("SKU-100154", "S", 2.0), ("SKU-100161", "M", 3.0), ("SKU-100168", "L", 1.8)]
    jk = {x[0] for x in JACKET}
    pos_rows = [p for p in pos_rows if not (p["sku"] in jk and p["site_id"].startswith("ST"))]
    for i, st in enumerate(sorted(store_ids, key=lambda x: h("jacket", x))[:45]):
        if i < 12:
            have = {"S", "M", "L"}          # complete run
        elif i < 32:
            have = {"L"}                    # only the large left
        elif i < 40:
            have = {"S", "L"}               # no medium
        else:
            have = {"S"}                    # only the small left
        for sku, sz, dem in JACKET:
            if sz in have:
                avail = (9 + int(h(sku, st) * 6)) if sz == "L" else (3 + int(h(sku, st) * 3))
            else:
                avail = 0
            pos_rows.append(mkrow(sku, st, avail, dem, 0, 70))

    # (6) Aged lines (aged_lines.xlsx): the DC stock age must match the clearance list.
    AGED = {"SKU-105558|DC5": 180, "SKU-101813|DC3": 120, "SKU-103584|DC4": 260, "SKU-104277|DC3": 315, "SKU-104165|DC4": 285,
            "SKU-105026|DC5": 215, "SKU-104501|DC5": 160, "SKU-100924|DC2": 140, "SKU-102408|DC3": 175, "SKU-102009|DC2": 120,
            "SKU-104781|DC4": 200, "SKU-101008|DC1": 210, "SKU-104977|DC4": 235, "SKU-101827|DC5": 135, "SKU-102156|DC1": 270,
            "SKU-101687|DC1": 315, "SKU-102366|DC2": 130, "SKU-100847|DC1": 180, "SKU-100287|DC2": 310, "SKU-102317|DC5": 245,
            "SKU-103339|DC4": 245, "SKU-103213|DC5": 160, "SKU-101365|DC4": 310, "SKU-103087|DC2": 310, "SKU-102807|DC4": 250,
            "SKU-104088|DC3": 125, "SKU-104746|DC3": 240, "SKU-103311|DC4": 270, "SKU-105243|DC1": 315, "SKU-104795|DC1": 150,
            "SKU-102394|DC5": 140, "SKU-101267|DC5": 305, "SKU-104214|DC2": 205, "SKU-101407|DC1": 200, "SKU-104921|DC5": 185,
            "SKU-105369|DC2": 165, "SKU-101673|DC2": 305, "SKU-105089|DC1": 140, "SKU-101848|DC2": 320, "SKU-102828|DC4": 130}
    for p in pos_rows:
        a = AGED.get(p["sku"] + "|" + p["site_id"])
        if a:
            p["received_date"] = g.days_ago(a)

    # (6b) Aged-stock story (03:29:Q5, quoted by costing): the three biggest lines older than 180 days are SKU-105054 at DC4
    # (about 482k at cost), SKU-101253 at DC5 and SKU-100658 at DC5. Any other big DC line is kept just under 180 days.
    AGED_TOP = {"SKU-105054|DC4": 230, "SKU-101253|DC5": 260, "SKU-100658|DC5": 245}
    for p in pos_rows:
        k = p["sku"] + "|" + p["site_id"]
        if k in AGED_TOP:
            p["received_date"] = g.days_ago(AGED_TOP[k])
        elif (p["site_id"].startswith("DC") and p["on_hand"] * float(products[p["sku"]]["unit_cost_gbp"] or 0) >= 255000
              and k not in AGED):
            p["received_date"] = g.days_ago(min(170, (g.as_of - p["received_date"]).days))

    # (7) Demand rescaling for stories that are about cover (network cover = available / weekly demand).
    def net_cover(sku):
        av = sum(p["available"] for p in pos_rows if p["sku"] == sku)
        dm = sum(p["weekly_demand"] for p in pos_rows if p["sku"] == sku)
        return av / dm if dm else None

    def scale_demand(sku, f):
        for p in pos_rows:
            if p["sku"] == sku:
                p["weekly_demand"] = round(p["weekly_demand"] * f, 1)
                p["safety_stock"] = int(p["safety_stock"] * f)
                p["reorder_point"] = int(p["reorder_point"] * f)

    # Packaging-type supplier SUP-0068 (beauty): a few lines would not last a six-week outage.
    SUP68_COVER = {"SKU-104536": 2.4, "SKU-101022": 3.1, "SKU-105390": 3.8, "SKU-104522": 4.6, "SKU-101967": 5.2, "SKU-101960": 5.7}
    # Vietnam-made lines (southern Vietnam port closure): the lowest-cover ones run out first.
    VN_COVER = {"SKU-101260": 1.8, "SKU-102884": 2.3, "SKU-105964": 2.9, "SKU-100280": 3.4, "SKU-103521": 4.0, "SKU-101722": 4.6}
    for sku, tgt in {**SUP68_COVER, **VN_COVER}.items():
        c = net_cover(sku)
        if c:
            scale_demand(sku, c / tgt)

    # 03:22:Q2: the three lines closest to running out (days of stock at one DC; the network cover above is unchanged because the
    # rest of each SKU's demand is shared out over its other sites).
    def set_site_days(sku, days_by_site):
        rows = [p for p in pos_rows if p["sku"] == sku]
        pinned = {p["site_id"]: p for p in rows if p["site_id"] in days_by_site}
        if len(pinned) != len(days_by_site):
            return
        total = sum(p["weekly_demand"] for p in rows)
        new_d = {site: round(p["available"] * 7.0 / days_by_site[site], 1) for site, p in pinned.items()}
        rest_old = total - sum(p["weekly_demand"] for p in pinned.values())
        f = (total - sum(new_d.values())) / rest_old
        for p in rows:
            old_d = p["weekly_demand"]
            ff = new_d[p["site_id"]] / old_d if p["site_id"] in pinned else f
            p["weekly_demand"] = round(old_d * ff, 1)
            p["safety_stock"] = int(p["safety_stock"] * ff)
            p["reorder_point"] = int(p["reorder_point"] * ff)

    set_site_days("SKU-101260", {"DC2": 10.6})
    set_site_days("SKU-102884", {"DC5": 13.0})
    set_site_days("SKU-104536", {"DC2": 16.0, "DC5": 17.9})

    # Long-tail / slow-moving lines: chain sales of about 140 units a week or less (was 20 before the x6.8 master scaling). DC issues equal the online units, so
    # network demand equals what the chain really sells; the stock held (from master) is then many weeks of cover.
    protected = set(SUP68_COVER) | set(VN_COVER) | {k.split("|")[0] for k in AGED} | {THROW} | set(tops) | jk | set(bay_skus)
    protected |= {"SKU-103486", "SKU-103472", "K-1700", "PF-220", "SKU-101904", "SKU-103892", "SKU-103458", "SKU-104438", "SKU-104445"}
    protected |= {x[0] for x in risk} | set(sa)
    protected |= {"SKU-100007", "SKU-100014", "SKU-100021", "SKU-100056", "SKU-100084", "SKU-100301", "SKU-100441", "SKU-101085",
                  "SKU-101813", "SKU-102100", "SKU-103234", "SKU-104018", "SKU-104032", "SKU-105460", "SKU-105887"}
    for sku in sorted(chain_store):
        if sku in protected or sku not in products or products[sku]["category"] in ("Bedding", "Towels"):
            continue
        if chain_store[sku] + chain_online[sku] > LONG_TAIL_UNITS:
            continue
        dcs = [p for p in pos_rows if p["sku"] == sku and p["site_id"].startswith("DC")]
        sts = [p for p in pos_rows if p["sku"] == sku and not p["site_id"].startswith("DC")]
        if not dcs or not sts:
            continue
        sd = sum(p["weekly_demand"] for p in sts)
        for p in sts:
            p["weekly_demand"] = round(p["weekly_demand"] * chain_store[sku] / sd, 1) if sd and chain_store[sku] else p["weekly_demand"]
        dstock = sum(max(p["available"], 1) for p in dcs)
        for p in dcs:
            new_d = max(round(max(chain_online[sku], 1.0) * max(p["available"], 1) / dstock, 1), 0.1)
            f = new_d / max(p["weekly_demand"], 0.1)
            p["weekly_demand"] = new_d
            p["safety_stock"] = int(p["safety_stock"] * f)
            p["reorder_point"] = int(p["reorder_point"] * f)

    # (7b) 08:78:Q2 haircare promotion (SKU-104599): network stock (DC3 + stores) of 42,000 units covers the base demand of the
    # 13 weeks to the January promotion and the four promotion weeks at base rate (41,676 units); only the promotion uplift is
    # unmet. Network demand equals the demand system's weekly forecast (about 2,630 units before the promotion).
    PROMO_SKU, PROMO_NETWORK_STOCK, PROMO_WEEKLY = "SKU-104599", 42000, 2630.0
    rows = [p for p in pos_rows if p["sku"] == PROMO_SKU]
    st_rows = sorted((p for p in rows if p["site_id"].startswith("ST")), key=lambda p: p["site_id"])
    if rows and st_rows:
        want = PROMO_NETWORK_STOCK - sum(p["available"] for p in rows if not p["site_id"].startswith("ST"))
        f = want / sum(p["available"] for p in st_rows)
        for p in st_rows:
            p["allocated"] = int(p["allocated"] * f)
            p["available"] = int(p["available"] * f)
            p["on_hand"] = p["available"] + p["allocated"]
        st_rows[0]["available"] += want - sum(p["available"] for p in st_rows)
        st_rows[0]["on_hand"] = st_rows[0]["available"] + st_rows[0]["allocated"]
        f = PROMO_WEEKLY / sum(p["weekly_demand"] for p in rows)
        for p in rows:
            p["weekly_demand"] = round(p["weekly_demand"] * f, 1)
            p["safety_stock"] = int(p["safety_stock"] * f)
            p["reorder_point"] = int(p["reorder_point"] * f)

    # (8) Stock by batch for quality holds: failed lots of three products (stores and DCs).
    def add_batch(sku, batch_id, status, age, site, qty, loc_hint=None):
        cands = [p for p in pos_rows if p["sku"] == sku and p["site_id"] == site]
        if not cands:
            return
        row = max(cands, key=lambda p: p["on_hand"])
        qty = min(int(qty), row["on_hand"])
        if qty > 0:
            batches.append({"batch_id": batch_id, "sku": sku, "site_id": site, "location_id": row["location_id"] or "",
                            "on_hand": qty, "received_date": g.days_ago(age), "status": status})

    # blouse lots that failed colourfastness (unshipped stock still in DCs; the rest has already gone to stores)
    add_batch("SKU-100007", "BATCH-POL-PINK-004", "released", 27, "DC4", 240)
    add_batch("SKU-100007", "BATCH-POL-PINK-007", "released", 9, "DC2", 500)
    add_batch("SKU-100014", "BATCH-POL-PINK-005", "released", 20, "DC4", 180)
    # shoe SKU-100301: soles from BATCH-SHOE-002/003/004 separate; 001 is fine
    shoe = [("BATCH-SHOE-002", 70, {"DC3": 400, "DC1": 300}), ("BATCH-SHOE-003", 55, {"DC3": 650, "DC4": 520}),
            ("BATCH-SHOE-004", 40, {"DC4": 700, "DC5": 380}), ("BATCH-SHOE-001", 110, {"DC3": 600, "DC1": 500, "DC5": 450})]
    for bid, age, dcq in shoe:
        for site, q in dcq.items():
            add_batch("SKU-100301", bid, "released" if bid == "BATCH-SHOE-001" else "released", age, site, q)
    shoe_stores = sorted((p["site_id"] for p in pos_rows if p["sku"] == "SKU-100301" and p["site_id"].startswith("ST")),
                         key=lambda x: h("shoe", x))
    for i, st in enumerate(shoe_stores):
        bid = ("BATCH-SHOE-003", "BATCH-SHOE-004", "BATCH-SHOE-002", "BATCH-SHOE-001")[i % 4]
        add_batch("SKU-100301", bid, "released", 45, st, max(int(next(p["on_hand"] for p in pos_rows if p["sku"] == "SKU-100301" and p["site_id"] == st) * 0.6), 1))
    # leather bag SKU-101813: BATCH-LEATHER-002 failed chromium VI, 001 passed
    # (the qms production lot for this SKU from batch 002 is 300 units, so only a few hundred are left across DCs and stores)
    for site, q in {"DC3": 150, "DC5": 60}.items():
        add_batch("SKU-101813", "BATCH-LEATHER-002", "released", 120, site, q)
    for site, q in {"DC2": 1200, "DC4": 900}.items():
        add_batch("SKU-101813", "BATCH-LEATHER-001", "released", 150, site, q)
    leather_stores = sorted((p["site_id"] for p in pos_rows if p["sku"] == "SKU-101813" and p["site_id"].startswith("ST")),
                            key=lambda x: h("leather", x))
    # the failed batch 002 is one 300-unit production lot (qms): 80 units are still in stores, shared out by store stock
    # (batch 001 is the bulk of the store stock)
    l_on = {st: next(p["on_hand"] for p in pos_rows if p["sku"] == "SKU-101813" and p["site_id"] == st) for st in leather_stores}
    l2 = [st for i, st in enumerate(leather_stores) if i % 3 != 2]
    l2_tot = sum(l_on[st] for st in l2)
    left = 80
    for j, st in enumerate(l2):
        q = left if j == len(l2) - 1 else max(int(80 * l_on[st] / l2_tot), 1)
        left -= q
        add_batch("SKU-101813", "BATCH-LEATHER-002", "released", 100, st, q)
    for i, st in enumerate(leather_stores):
        if i % 3 == 2:
            add_batch("SKU-101813", "BATCH-LEATHER-001", "released", 100, st, max(int(l_on[st] * 0.7), 1))

    # (9) Wholesale allocation story: SKU-100035 has 8,000 units sellable across the network (three wholesale customers
    # ordered 15,000). Master dc_stock only has DC1 and DC3, so the balance sits in DC2 (UK e-commerce DC).
    # Stores range this scarf at chain-scale volumes, so cap what the stores hold (the oms allocation story needs 8,000 in all).
    STORE_CAP = 1900
    st_rows = [p for p in pos_rows if p["sku"] == "SKU-100035" and p["site_id"].startswith("ST")]
    st_tot = sum(p["available"] for p in st_rows)
    if st_tot > STORE_CAP:
        for p in st_rows:
            f = STORE_CAP / st_tot
            p["on_hand"] = max(int(p["on_hand"] * f), 1)
            p["allocated"] = int(p["allocated"] * f)
            p["available"] = p["on_hand"] - p["allocated"]
    have = sum(p["available"] - p["hold_qty"] for p in pos_rows if p["sku"] == "SKU-100035")
    need = 8000 - have
    if need > 0:
        row = mkrow("SKU-100035", "DC2", need, round(need / 11.0, 1), 0, 30)
        pos_rows.append(row)

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
        f = 0.68 if cat in cat_mult else g.rng_for("plan", site, cat).uniform(0.95, 1.08)
        plan.append({"site_id": site, "category": cat, "plan_value_gbp": round(val * f, 2),
                     "plan_cover_weeks": 10.7, "plan_closing_units": int(close * f), "period_end": season_end})

    import csv, os
    fr = []
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "franchise", "data", "partner_stock.csv")
    if os.path.exists(f):
        for row in csv.DictReader(open(f)):
            if row["sku"] in products:
                fr.append({"partner_id": row["partner_id"], "sku": row["sku"], "on_hand": int(row["on_hand"]),
                           "available": int(row["available"]), "target_stock": int(row["target_stock"]),
                           "is_core_range": row["is_core_range"] == "true"})
    # Franchise ambient lines are healthy; only the planted partner story lines (franchise seed) are far from target.
    story_f = set()
    sf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "franchise", "seed", "partner_stock.csv")
    if os.path.exists(sf):
        story_f = {(row["partner_id"], row["sku"]) for row in csv.DictReader(open(sf))}
    for row in fr:
        if (row["partner_id"], row["sku"]) in story_f:
            continue
        t = row["target_stock"]
        row["on_hand"] = min(max(row["on_hand"], int(0.75 * t)), int(1.4 * t))
        row["available"] = min(row["available"], row["on_hand"])
        row["available"] = max(row["available"], int(0.6 * row["on_hand"]))
    if not fr:
        fr = [{"partner_id": "PTN-011", "sku": "SKU-100007", "on_hand": 100, "available": 90, "target_stock": 80, "is_core_range": False}]

    return {
        "franchise_stock": fr,
        "stock_plan": plan,
        "stock_batches": batches,
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
