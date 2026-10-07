"""Returns data: one row per returned item, built from master orders that are 'returned' / 'part_returned'.

Background: every item of a returned order, with category-specific reasons, route rules and costs.
Stories (explicit row counts, windows kept inside the last 13 weeks):
  - top returned styles: STY-5520 (sizing), STY-T-4410 (hip fit, skinny), STY-4171 (sole separation, rising),
    STY-4042 (not as described), K-1700 (defects)
  - Audio disposition: items older than 60 days are recycled although liquidating pays
  - weekly history with a January peak, returns centre capacity below the January need
"""
from datetime import timedelta, date
from collections import defaultdict, Counter
import bisect

WINDOW_DAYS = 91  # full weeks of record-level data: 13 weeks ending the day before as_of

REASONS = [
    ("WRONG_SIZE", "Too large or too small", "Customer"),
    ("TOO_TIGHT_HIP", "Too tight at the hip", "Customer"),
    ("WRONG_COLOUR", "Not the colour expected", "Customer"),
    ("DAMAGE", "Damaged on arrival", "Logistics"),
    ("DEFECT", "Quality defect", "Quality"),
    ("SOLE_SEPARATION", "Sole separating from the upper", "Quality"),
    ("WRONG_ITEM", "Wrong item sent", "Logistics"),
    ("NOT_AS_DESCRIBED", "Not as shown online", "Customer"),
    ("CHANGED_MIND", "Customer changed mind", "Customer"),
    ("DUPLICATE", "Duplicate order", "Customer"),
]
FAULTY = {"DAMAGE", "DEFECT", "SOLE_SEPARATION"}

# (0-30, 31-60, 61+) route per category; default by department
DEPT_RULES = {
    "Womenswear": ("restocked", "refurbished", "liquidated"),
    "Menswear": ("restocked", "refurbished", "liquidated"),
    "Kids": ("restocked", "refurbished", "liquidated"),
    "Accessories": ("restocked", "restocked", "refurbished"),
    "Beauty": ("restocked", "liquidated", "recycled"),
    "Electricals": ("restocked", "refurbished", "liquidated"),
    "Home": ("restocked", "refurbished", "liquidated"),
}
CAT_RULES = {
    "Outerwear": ("restocked", "restocked", "refurbished"),
    "Knitwear": ("restocked", "restocked", "refurbished"),
    "Footwear": ("restocked", "refurbished", "liquidated"),
    "Audio": ("restocked", "refurbished", "recycled"),  # rules are in seed/disposition_rules.csv
}
LIQ_RATE = {"Electricals": 0.38, "Home": 0.28, "Womenswear": 0.16, "Menswear": 0.16, "Kids": 0.15,
            "Accessories": 0.18, "Beauty": 0.12}
# share of non-faulty returns that pass inspection and go back on sale as new
RESTOCK_OK = {"Outerwear": 0.93, "Knitwear": 0.9, "Footwear": 0.55, "Small Appliances": 0.5, "Smart Home": 0.55,
              "Personal Care": 0.5, "Audio": 0.65, "Womenswear": 0.8, "Menswear": 0.8, "Kids": 0.78,
              "Accessories": 0.75, "Beauty": 0.5, "Electricals": 0.6, "Home": 0.7}
COUNTRY_SHIP = {"GB": 0.0, "IE": 2.4, "DE": 3.6, "NL": 3.4, "FR": 3.8, "US": 6.5}
HANDLING = {"restocked": 4.5, "refurbished": 11.0, "liquidated": 7.0, "recycled": 5.5, "destroyed": 3.0}
GRADE_BY_ROUTE = {"restocked": (("A", 70), ("B", 30)), "refurbished": (("B", 40), ("C", 60)),
                  "liquidated": (("C", 45), ("D", 55)), "recycled": (("D", 30), ("E", 70)),
                  "destroyed": (("E", 100),)}
DAYS_TO_SALE = {"restocked": (3, 8), "refurbished": (14, 28), "liquidated": (6, 12)}

# damage share of returns by category (rest of the profile is scaled around it)
DAMAGE_W = {"Small Appliances": 10.0, "Audio": 6.0, "Smart Home": 6.5, "Personal Care": 5.5, "Lighting": 10.0,
            "Cookware": 9.0, "Drinkware": 12.0, "Storage": 4.5, "Towels": 1.5, "Bedding": 1.5,
            "Haircare": 5.0, "Skincare": 5.0, "Bodycare": 5.5, "Fragrance": 6.0}


def reason_profile(dept, cat):
    if cat == "Footwear":
        w = {"WRONG_SIZE": 34, "CHANGED_MIND": 22, "NOT_AS_DESCRIBED": 12, "WRONG_COLOUR": 6, "DEFECT": 10,
             "DAMAGE": 2, "WRONG_ITEM": 5, "DUPLICATE": 3, "SOLE_SEPARATION": 1}
    elif cat in ("Outerwear", "Knitwear"):
        w = {"WRONG_SIZE": 30, "CHANGED_MIND": 34, "NOT_AS_DESCRIBED": 14, "WRONG_COLOUR": 9, "DEFECT": 2,
             "DAMAGE": 1, "WRONG_ITEM": 3, "DUPLICATE": 3}
    elif dept in ("Womenswear", "Menswear", "Kids"):
        w = {"WRONG_SIZE": 34, "CHANGED_MIND": 22, "NOT_AS_DESCRIBED": 10, "WRONG_COLOUR": 9, "DEFECT": 8,
             "DAMAGE": 3, "WRONG_ITEM": 5, "DUPLICATE": 4}
    elif dept == "Accessories":
        w = {"CHANGED_MIND": 34, "NOT_AS_DESCRIBED": 20, "WRONG_COLOUR": 12, "DEFECT": 10, "DAMAGE": 6,
             "WRONG_ITEM": 8, "DUPLICATE": 6, "WRONG_SIZE": 4}
    elif dept == "Beauty":
        w = {"CHANGED_MIND": 30, "NOT_AS_DESCRIBED": 20, "DEFECT": 8, "DAMAGE": 12, "WRONG_ITEM": 14,
             "DUPLICATE": 6, "WRONG_COLOUR": 10}
    elif dept == "Electricals":
        w = {"DEFECT": 30, "CHANGED_MIND": 22, "NOT_AS_DESCRIBED": 14, "DAMAGE": 7, "WRONG_ITEM": 6,
             "DUPLICATE": 6, "WRONG_COLOUR": 3}
    else:
        w = {"CHANGED_MIND": 30, "NOT_AS_DESCRIBED": 18, "DEFECT": 12, "DAMAGE": 6, "WRONG_ITEM": 8,
             "DUPLICATE": 6, "WRONG_COLOUR": 8}
    if cat in DAMAGE_W:
        w["DAMAGE"] = DAMAGE_W[cat]
    return list(w), list(w.values())


def seasonal(d):
    """Weekly returns index (1.0 = autumn baseline); January peak, December build-up."""
    anchors = [(-3, 2.4), (4, 3.1), (11, 2.5), (18, 1.7), (25, 1.3), (32, 1.1), (46, 1.0), (273, 1.0), (306, 1.0),
               (313, 1.05), (320, 1.15), (327, 1.35), (334, 1.45), (341, 1.7), (348, 1.9), (355, 1.25),
               (362, 2.4), (369, 3.1)]
    x = (d - date(d.year, 1, 1)).days
    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return 1.0


def generate(g):
    r = g.rng
    as_of = g.as_of
    win_start = as_of - timedelta(days=WINDOW_DAYS)  # a Monday
    win_end = as_of - timedelta(days=1)

    products = g.master("products")
    orders = g.master("orders")
    pmap = {p["sku"]: p for p in products}
    for p in products:
        p["_cost"] = float(p["unit_cost_gbp"])

    # ---- rules -------------------------------------------------------------------------------------------
    cats = sorted({p["category"] for p in products})
    cat_dept = {p["category"]: p["department"] for p in products}
    # Accessories/Kids/Womenswear share category names across departments only for Outerwear/Knitwear/Trousers
    def rule_for(cat):
        return CAT_RULES.get(cat) or DEPT_RULES[cat_dept[cat]]

    disposition_rules = []
    n = 0
    for cat in cats:
        if cat == "Audio":
            continue  # Audio rules are hand-written in seed/disposition_rules.csv
        for (lo, hi), route in zip(((0, 30), (31, 60), (61, 365)), rule_for(cat)):
            n += 1
            disposition_rules.append({
                "rule_id": f"DIS-{n:06d}", "product_category": cat, "min_age_days": lo, "max_age_days": hi,
                "disposition_route": route, "status": "active", "effective_from": as_of - timedelta(days=120),
                "updated_at": as_of - timedelta(days=r.randint(20, 100))})

    def band_route(cat, age):
        rr = rule_for(cat)
        return rr[0] if age <= 30 else rr[1] if age <= 60 else rr[2]

    # ---- products eligible for background returns ----------------------------------------------------------
    story_skus = set()
    story_styles = {"STY-5520", "STY-T-4410", "STY-4171", "STY-4042", "STY-K-1700"}
    for p in products:
        if p["style_id"] in story_styles or p["sku"] == "K-1700":
            story_skus.add(p["sku"])
    bg = [p for p in products if p["sku"] not in story_skus and p["status"] != "new"]
    bg.sort(key=lambda p: p["launch_date"])
    launch_dates = [p["launch_date"] for p in bg]
    abc_w = {"A": 1.5, "B": 1.0, "C": 0.7}

    def pick_product(order_date):
        k = bisect.bisect_right(launch_dates, order_date)
        pool = bg[:k]
        ws = [abc_w.get(p["abc_class"], 1.0) * (0.5 if p["status"] == "discontinued" else 1.0) for p in pool]
        return r.choices(pool, ws)[0]

    # ---- order pool ------------------------------------------------------------------------------------------
    pool_by_date = defaultdict(list)
    returned_orders = []
    for o in orders:
        if o["status"] in ("returned", "part_returned"):
            od = date.fromisoformat(o["order_date"])
            o["_d"] = od
            pool_by_date[od].append(o)
            returned_orders.append(o)

    def order_near(order_date):
        for off in (0, 1, -1, 2, -2, 3, -3, 4, -4):
            lst = pool_by_date.get(order_date + timedelta(days=off))
            if lst:
                return r.choice(lst)
        return None

    rows = []

    def add_item(order, p, rdate, reason, delay=None, fit=None, defect=None, route=None):
        cat = p["category"]
        dept = p["department"]
        age = delay if delay is not None else (rdate - order["_d"]).days
        faulty = reason in FAULTY
        if route is None:
            route = band_route(cat, age)
            if faulty and route == "restocked":
                route = r.choices(["refurbished", "liquidated", "recycled"], [60, 25, 15])[0]
            elif route == "restocked" and r.random() > RESTOCK_OK.get(cat, RESTOCK_OK.get(dept, 0.8)):
                route = r.choices(["refurbished", "liquidated"], [70, 30])[0]  # fails inspection for resale as new
            if age > 60 and r.random() < 0.12:
                route = "liquidated"
            if route == "recycled" and order["country"] in ("DE", "FR") and r.random() < 0.3:
                route = "destroyed"
        grades, gw = zip(*GRADE_BY_ROUTE[route])
        grade = r.choices(grades, gw)[0]
        cost = p["_cost"]
        if route == "restocked":
            rec = cost * (0.97 if grade == "A" else 0.9)
        elif route == "refurbished":
            rec = cost * (0.58 if grade == "B" else 0.42)
        elif route == "liquidated":
            rec = cost * LIQ_RATE[dept] * r.uniform(0.92, 1.08)
        elif route == "recycled":
            rec = cost * 0.03
        else:
            rec = 0.0
        ship = COUNTRY_SHIP.get(order["country"], 3.0)
        if order["channel"] == "click_collect":
            ship = 0.8
        handling = HANDLING[route] * r.uniform(0.85, 1.15) + ship
        dts = r.randint(*DAYS_TO_SALE[route]) if route in DAYS_TO_SALE else None
        ddate = min(rdate + timedelta(days=r.randint(1, 4)), as_of)
        rows.append({
            "order_id": order["order_id"], "sku": p["sku"], "style_id": p["style_id"], "return_date": rdate,
            "return_reason_code": reason, "defect_code": defect,
            "pack_type": p["pack_type"], "item_age_days": age, "condition_grade": grade,
            "damage_code": ("CRUSH" if r.random() < 0.7 else "TORN") if reason == "DAMAGE" else None,
            "category": cat, "fit": fit, "country": order["country"], "channel": order["channel"],
            "disposition_route": route, "disposition_date": ddate, "recovery_gbp": round(rec, 2),
            "handling_cost_gbp": round(handling, 2), "unit_cost_gbp": cost, "days_to_sale": dts,
            "outcome": route, "updated_at": min(ddate + timedelta(days=1), as_of),
        })

    # ---- background rows -------------------------------------------------------------------------------------
    late_p = {"Electricals": 0.16, "Home": 0.08, "Accessories": 0.03, "Beauty": 0.02}
    for o in returned_orders:
        units = int(o["units"])
        k = units if o["status"] == "returned" else r.randint(1, max(1, units - 1))
        for _ in range(k):
            p = pick_product(o["order_date"])
            dept = p["department"]
            reasons, ws = reason_profile(dept, p["category"])
            reason = r.choices(reasons, ws)[0]
            delay = r.randint(3, 24)
            if r.random() < late_p.get(dept, 0.02):
                delay = r.randint(61, 115)
            rd = o["_d"] + timedelta(days=delay)
            if not (win_start <= rd <= win_end):
                delay = r.randint(3, 24)
                rd = o["_d"] + timedelta(days=delay)
                if not (win_start <= rd <= win_end):
                    continue
            add_item(o, p, rd, reason, delay=delay)

    # ---- story helpers -----------------------------------------------------------------------------------------
    def story_rows(skus, n, reason_fn, date_fn, delay_fn=None, fit_fn=None, defect_fn=None, route_fn=None):
        made = 0
        guard = 0
        while made < n and guard < n * 40:
            guard += 1
            rd = date_fn(made)
            delay = delay_fn(made) if delay_fn else r.randint(3, 24)
            o = order_near(rd - timedelta(days=delay))
            if o is None:
                continue
            delay = (rd - o["_d"]).days
            if delay < 2:
                continue
            p = pmap[skus[made % len(skus)] if isinstance(skus, list) else skus]
            if o["order_date"] < p["launch_date"]:
                continue  # not on sale yet when ordered
            reason = reason_fn(p, made)
            add_item(o, p, rd, reason, delay=delay, fit=fit_fn(p, reason) if fit_fn else None,
                     defect=defect_fn(p, reason) if defect_fn else None,
                     route=route_fn(p, reason, delay) if route_fn else None)
            made += 1

    def flat_date(_):
        return win_start + timedelta(days=r.randint(2, WINDOW_DAYS - 2))

    def binned(counts):
        """counts = [(from_days_ago, to_days_ago, n), ...]; returns date_fn consuming bins in order."""
        seq = []
        for a, b, c in counts:
            seq += [r.randint(a, b) for _ in range(c)]
        r.shuffle(seq)
        return lambda i: as_of - timedelta(days=seq[i % len(seq)])

    def choose(weights):
        keys = list(weights)
        return lambda *_: r.choices(keys, list(weights.values()))[0]

    # STY-5520: sizing story (three sizes, size 14 worst)
    sk5520 = ["SKU-101897"] * 30 + ["SKU-101904"] * 38 + ["SKU-101911"] * 50
    r.shuffle(sk5520)
    pick5520 = choose({"WRONG_SIZE": 52, "CHANGED_MIND": 14, "NOT_AS_DESCRIBED": 12, "WRONG_COLOUR": 8,
                       "DEFECT": 6, "DAMAGE": 4, "WRONG_ITEM": 2, "DUPLICATE": 2})
    story_rows(sk5520, len(sk5520), lambda p, i: pick5520(), flat_date)

    # STY-T-4410: size 14 too tight at the hip, skinny fit worst
    t_sizes = ["SKU-100651"] * 62 + ["SKU-100637"] * 28 + ["SKU-100644"] * 14
    r.shuffle(t_sizes)
    fit_for = {}

    def t_fit(p, reason):
        return fit_for.pop(id(p), None)

    def t_reason(p, i):
        if p["sku"] == "SKU-100651":
            fit = r.choices(["skinny", "regular", "comfort"], [60, 28, 12])[0]
            w = {"skinny": {"TOO_TIGHT_HIP": 72, "WRONG_SIZE": 8, "CHANGED_MIND": 10, "NOT_AS_DESCRIBED": 5, "DEFECT": 5},
                 "regular": {"TOO_TIGHT_HIP": 25, "WRONG_SIZE": 15, "CHANGED_MIND": 35, "NOT_AS_DESCRIBED": 10, "DEFECT": 5, "WRONG_COLOUR": 10},
                 "comfort": {"TOO_TIGHT_HIP": 6, "WRONG_SIZE": 10, "CHANGED_MIND": 50, "NOT_AS_DESCRIBED": 14, "DEFECT": 10, "WRONG_COLOUR": 10}}[fit]
        else:
            fit = r.choices(["skinny", "regular", "comfort"], [40, 40, 20])[0]
            w = {"CHANGED_MIND": 40, "WRONG_SIZE": 20, "NOT_AS_DESCRIBED": 15, "DEFECT": 10, "WRONG_COLOUR": 10,
                 "TOO_TIGHT_HIP": 5}
        fit_for[id(p)] = fit
        return r.choices(list(w), list(w.values()))[0]

    story_rows(t_sizes, len(t_sizes), t_reason, flat_date, fit_fn=t_fit)

    # STY-4171 footwear: sole separation rising month on month (SKU-100301)
    sole_items = []
    for a, b, c in [(61, 88, 6), (31, 60, 22), (1, 30, 57)]:
        sole_items += [("SOLE_SEPARATION", as_of - timedelta(days=r.randint(a, b))) for _ in range(c)]
    for _ in range(15):
        sole_items.append((r.choice(["WRONG_SIZE", "CHANGED_MIND", "NOT_AS_DESCRIBED", "WRONG_COLOUR"]), flat_date(0)))
    r.shuffle(sole_items)
    story_rows("SKU-100301", len(sole_items), lambda p, i: sole_items[i][0], lambda i: sole_items[i][1],
               defect_fn=lambda p, reason: "SOLE_PEEL" if reason == "SOLE_SEPARATION" else None)

    # STY-4042 knitwear: not as described / colour
    k_skus = sorted(p["sku"] for p in products if p["style_id"] == "STY-4042")
    pickk = choose({"NOT_AS_DESCRIBED": 40, "WRONG_COLOUR": 22, "CHANGED_MIND": 20, "WRONG_SIZE": 8, "DEFECT": 6, "DAMAGE": 4})
    story_rows(k_skus, 90, lambda p, i: pickk(), flat_date)

    # K-1700 kettle: defects rising
    kd = binned([(61, 88, 10), (31, 60, 26), (1, 30, 48)])
    pickkt = choose({"DEFECT": 70, "NOT_AS_DESCRIBED": 12, "CHANGED_MIND": 10, "DAMAGE": 5, "WRONG_ITEM": 3})
    pickdef = choose({"LID_LEAK": 55, "ELEMENT_FAIL": 30, "SWITCH_FAIL": 15})
    story_rows("K-1700", 84, lambda p, i: pickkt(), kd,
               defect_fn=lambda p, reason: pickdef() if reason == "DEFECT" else None)

    # Audio disposition story: old items are recycled, a few manual liquidations show what liquidating pays
    audio = [p["sku"] for p in products if p["category"] == "Audio" and p["status"] != "new"
             and p["launch_date"] <= "2026-05-31"]
    pa = choose({"CHANGED_MIND": 35, "DEFECT": 30, "NOT_AS_DESCRIBED": 15, "DAMAGE": 10, "WRONG_ITEM": 10})
    story_rows(audio, 100, lambda p, i: pa(), lambda i: win_start + timedelta(days=r.randint(30, WINDOW_DAYS - 2)),
               delay_fn=lambda i: r.randint(3, 30),
               route_fn=lambda p, reason, d: ("restocked" if reason not in FAULTY else
                                              r.choices(["refurbished", "liquidated", "recycled"], [55, 25, 20])[0]))
    story_rows(audio, 30, lambda p, i: pa(), lambda i: win_start + timedelta(days=r.randint(40, WINDOW_DAYS - 2)),
               delay_fn=lambda i: r.randint(31, 60),
               route_fn=lambda p, reason, d: r.choices(["refurbished", "liquidated"], [80, 20])[0])
    story_rows(audio, 60, lambda p, i: pa(), lambda i: win_start + timedelta(days=r.randint(62, WINDOW_DAYS - 2)),
               delay_fn=lambda i: r.randint(61, 105),
               route_fn=lambda p, reason, d: r.choices(["recycled", "liquidated"], [75, 25])[0])

    # ---- order and number ------------------------------------------------------------------------------------
    rows.sort(key=lambda x: (x["return_date"], x["order_id"], x["sku"]))
    for i, row in enumerate(rows, 1):
        row["return_id"] = f"RET-{i:06d}"

    # ---- weekly history before the record-level window -----------------------------------------------------
    by_week = Counter()
    by_cat = Counter()
    for x in rows:
        by_week[x["return_date"] - timedelta(days=x["return_date"].weekday())] += 1
        by_cat[x["category"]] += 1
    wk_counts = [by_week[w] for w in sorted(by_week)]
    base = sum(wk_counts) / len(wk_counts)
    total_cat = sum(by_cat.values())
    cat_share = {c: by_cat[c] / total_cat for c in by_cat}
    avg_handling = {c: sum(x["handling_cost_gbp"] for x in rows if x["category"] == c) / by_cat[c] for c in by_cat}
    hist = []
    for k in range(104, 0, -1):
        wk = win_start - timedelta(weeks=k)
        f = seasonal(wk) * (0.9 if wk < date(2026, 1, 1) else 0.97) * r.uniform(0.96, 1.04)
        for c, sh in cat_share.items():
            uplift = 1 + (f - 1) * (0.7 if cat_dept[c] in ("Beauty", "Home", "Electricals") else 1.0)
            cnt = max(0, round(base * uplift * sh * r.uniform(0.9, 1.1)))
            hist.append({"week_start": wk, "category": c, "returns_count": cnt,
                         "handling_cost_gbp": round(cnt * avg_handling[c] * r.uniform(0.95, 1.05), 2)})

    # ---- returns centre capacity ---------------------------------------------------------------------------------
    dow = [1.35, 1.2, 1.05, 1.0, 0.95, 0.85, 0.6]
    per_staff = 12
    capacity_units = int(base / 7 * 1.35 * 1.1)
    daily_actual = Counter(x["return_date"] for x in rows)
    capacity = []
    for off in range(-90, 131):
        d = as_of + timedelta(days=off)
        wk = d - timedelta(days=d.weekday())
        fc = round(base / 7 * dow[d.weekday()] * seasonal(wk))
        staff_plan = 9 if (date(d.year, 11, 20) <= d <= date(d.year, 12, 24)) else 6
        capacity.append({
            "capacity_id": f"CAP-{off + 91:04d}", "date": d, "capacity_units_per_day": capacity_units,
            "target_throughput_units": fc,
            "actual_throughput_units": daily_actual.get(d, 0) if off < 0 else None,
            "staffing_needed": -(-fc // per_staff), "planned_staff": staff_plan,
            "peak_day": fc > capacity_units,
        })

    # ---- liquidators ------------------------------------------------------------------------------------------
    liquidators = []
    n = 0
    for name, mult, terms in (("Brightstock Liquidations", 1.0, 30), ("ReSell Direct", 0.88, 45), ("Pallet & Partners", 0.8, 60)):
        for cat in cats:
            n += 1
            liquidators.append({"liquidator_id": f"LQD-{n:06d}", "name": name, "product_category": cat,
                                "recovery_rate_pct": round(LIQ_RATE[cat_dept[cat]] * 100 * mult, 1),
                                "payment_terms_days": terms, "effective_date": as_of - timedelta(days=30)})

    # ---- pack damage: current packs from the returns above, trials hand-set ---------------------------------------
    grp = defaultdict(lambda: [0, 0])
    for x in rows:
        k = (x["pack_type"], x["category"])
        grp[k][0] += 1
        grp[k][1] += x["return_reason_code"] == "DAMAGE"
    material = {"carton": "corrugated board", "polybag": "LDPE polybag", "hanging": "garment on hanger with polybag"}
    pack = []
    for (pt, cat), (tot, dmg) in sorted(grp.items()):
        if tot >= 30:
            pack.append({"pack_type": pt, "category": cat, "material": material[pt], "basis": "current pack, returns data",
                         "damage_rate_pct": round(100.0 * dmg / tot, 1), "sample_size": tot, "measured_from_date": win_start})
    pack += [
        {"pack_type": "moulded_pulp", "category": "Small Appliances", "material": "moulded pulp tray and sleeve",
         "basis": "supplier pilot shipments", "damage_rate_pct": 4.6, "sample_size": 640,
         "measured_from_date": as_of - timedelta(days=56)},
        {"pack_type": "recycled_plastic", "category": "Small Appliances", "material": "recycled PET clamshell",
         "basis": "supplier pilot shipments", "damage_rate_pct": 3.1, "sample_size": 420,
         "measured_from_date": as_of - timedelta(days=56)},
    ]

    # ---- circularity pilots -----------------------------------------------------------------------------------------
    def pil(i, t, cat, s, e, st, col, reu, rep, rec, recov, hand):
        return {"pilot_id": f"PIL-{i:06d}", "pilot_type": t, "product_category": cat,
                "start_date": as_of + timedelta(days=s), "end_date": as_of + timedelta(days=e), "status": st,
                "units_collected": col, "units_reused": reu, "units_repaired": rep, "units_recycled": rec,
                "recovery_gbp": recov, "handling_cost_gbp": hand, "updated_at": as_of - timedelta(days=3)}

    pilots = [
        pil(1, "take_back", "Outerwear", -540, -360, "completed", 1450, 820, 140, 380, 21300, 9800),
        pil(2, "resale", "Knitwear", -500, -330, "completed", 2100, 1720, 0, 210, 28900, 8400),
        pil(3, "take_back", "Small Appliances", -300, -120, "completed", 960, 310, 290, 310, 14800, 11200),
        pil(4, "repair", "Audio", -200, 30, "active", 740, 120, 410, 150, 9600, 8900),
        pil(5, "resale", "Outerwear", -150, 30, "active", 1880, 1430, 60, 250, 38400, 10900),
        pil(6, "take_back", "Footwear", -90, 60, "active", 520, 90, 40, 330, 2700, 4900),
    ]

    # ---- charge trials: one finished test in IE is our own evidence ---------------------------------------------------
    trials = [{"trial_id": "TRL-000001", "market": "IE", "charge_gbp": 2.99, "start_date": as_of - timedelta(days=170),
               "end_date": as_of - timedelta(days=86), "status": "completed", "units_returned": 631,
               "baseline_units_returned": 700, "impact_on_rate_pct": -9.9, "impact_on_conversion_pct": -0.6,
               "updated_at": as_of - timedelta(days=80)}]

    outcomes = [
        {"route": "restocked", "brand_risk": "low", "brand_risk_note": "Sold as new in the original range; grade A/B only"},
        {"route": "refurbished", "brand_risk": "medium", "brand_risk_note": "Sold as refurbished under our brand; warranty and quality complaints land on us"},
        {"route": "liquidated", "brand_risk": "high", "brand_risk_note": "Pallets enter unmanaged resale channels; brand dilution and product safety exposure"},
        {"route": "recycled", "brand_risk": "low", "brand_risk_note": "No resale; material recovery only"},
        {"route": "destroyed", "brand_risk": "high", "brand_risk_note": "Destruction of usable goods is restricted in DE and FR and draws press attention"},
    ]

    return {
        "returns": rows,
        "return_reasons": [{"reason_code": c, "description": d, "category": k} for c, d, k in REASONS],
        "disposition_rules": disposition_rules,
        "liquidator_rates": liquidators,
        "returns_centre_capacity": capacity,
        "circularity_pilots": pilots,
        "returns_charge_trials": trials,
        "pack_type_damage": pack,
        "disposition_outcomes": outcomes,
        "weekly_returns_history": hist,
    }
