"""POS data: hourly-grain sales lines, voids/refunds/discounts, self-checkout rules and weekly scan stats.

Story scopes (everything else is generated background that avoids them):
  ST159 Leeds Retail Park (UK North): voids/refunds surge on till T02 by EMP-00481 in the afternoons (07:68:Q5, 08:79:Q1).
  ST183 (UK North): a smaller refund spike on high-value items (08:79:Q1 secondary signal).
  ST214 Glasgow Retail Park (Scotland): store manager questions (08:71:Q1, Q2, Q4): refunds at till T03 by cover staff
        EMP-00529, three best-selling blouses SKU-100007/14/21 losing availability in the last 72 hours,
        a festival boost 37 days ago and roadworks drag from 20 days ago.
  ST150, ST159, ST165, ST181, ST183 (all Leeds): self-checkout exception rates up (08:79:Q5).
  Tops: size curve skewed to larger sizes and Scottish stores over-allocated (03:25:Q5).
  Small Appliances: a 4-week promotion about 4 months ago (10% deeper discount, volume up) to show price response (08:77:Q2). Home: mix shift to low-margin lines (08:77:Q3).
"""
from datetime import datetime, timedelta, time
from itertools import accumulate

N_HOME_NEW = 28        # days: Home mix shift applies to the last 28 days
SA_PROMO = (126, 98)   # days back: Small Appliances promotion (deeper discount, higher volume) for four weeks
FESTIVAL_DAY = 37      # ST214 festival Saturday
ROADWORKS_FROM = 20    # ST214 roadworks start

CAT_W = {"Tops": 9, "Small Appliances": 6, "Lighting": 3, "Bedding": 3, "Cookware": 3, "Drinkware": 3,
         "Storage": 3, "Towels": 3}
HOME_NEW = {"Storage": 9, "Bedding": 7, "Cookware": 3, "Towels": 2, "Drinkware": 1.5, "Lighting": 1.5}
TOPS_SIZE_W = {"10": 0.22, "12": 0.42, "14": 0.36}
TOPS_EXPECTED = {"10": 35.0, "12": 40.0, "14": 25.0}
ABC_W = {"A": 2.5, "B": 1.0, "C": 0.5}
STORY_SKUS = {"SKU-100007", "SKU-100014", "SKU-100021"}
LEEDS_SC = ["ST150", "ST159", "ST165", "ST181", "ST183"]
CLUSTER_MULT = {"A": 1.25, "B": 1.0, "C": 0.8, "D": 0.6}
REASONS = {
    "void": ["wrong till", "duplicate", "customer request", "operator error"],
    "refund": ["damaged", "wrong item", "customer satisfaction", "fit issue"],
    "discount": ["price match", "loyalty", "floor burn", "promotion"],
}


def generate(g):
    r = g.rng
    sites = {s["site_id"]: s for s in g.master("sites")}
    products = g.master("products")
    mgr = {e["site_id"]: e["employee_id"] for e in g.master("employees") if e["role"] == "Store Manager"}

    # ---- stores in the POS extract ----
    leeds = ["ST150", "ST159", "ST164", "ST165", "ST181", "ST183"]
    north_other = [s for s in sorted(sites) if sites[s]["region"] == "UK North" and sites[s]["type"] == "store"
                   and s not in leeds][:10]
    scot = ["ST214", "ST207", "ST201", "ST204", "ST212"]
    south = ["ST001"] + [s for s in sorted(sites) if sites[s]["region"] == "UK South" and sites[s]["type"] == "store"
                         and s != "ST001"][:4]
    stores = leeds + north_other + scot + south

    # ---- product weights ----
    ncat = {}
    for p in products:
        ncat[p["category"]] = ncat.get(p["category"], 0) + 1
    avail_base, avail_mult = {}, {}
    for p in products:
        u = r.random()
        forced_high = p["category"] == "Tops" or p["sku"] in STORY_SKUS
        if forced_high or u < 0.80:
            avail_base[p["sku"]], avail_mult[p["sku"]] = r.randint(93, 100), 1.0
        elif u < 0.95:
            avail_base[p["sku"]], avail_mult[p["sku"]] = r.randint(73, 87), 0.6
        else:
            avail_base[p["sku"]], avail_mult[p["sku"]] = r.randint(46, 65), 0.35

    cum_cache = {}

    def cum_for(home_new, sa_promo, exclude_story):
        key = (home_new, sa_promo, exclude_story)
        if key not in cum_cache:
            ws = []
            for p in products:
                cat = p["category"]
                cw = CAT_W.get(cat, 1.0)
                if home_new and cat in HOME_NEW:
                    cw = HOME_NEW[cat]
                w = cw / ncat[cat] * ABC_W[p["abc_class"]] * avail_mult[p["sku"]]
                if cat == "Tops":
                    w *= TOPS_SIZE_W[p["size"]] * 3
                if cat == "Small Appliances" and sa_promo:
                    w *= 1.35
                if exclude_story and p["sku"] in STORY_SKUS:
                    w = 0.0
                ws.append(w)
            cum_cache[key] = list(accumulate(ws))
        return cum_cache[key]

    sales = []
    n_txn = [0]

    def add_sale(store, p, when, qty, avail, lo=0.95, hi=1.0):
        price = float(p["retail_price_gbp"] or 50)
        cost = float(p["unit_cost_gbp"] or 20)
        disc = r.uniform(lo, hi)
        rev = qty * price * disc
        n_txn[0] += 1
        sales.append({
            "transaction_id": f"TXN-{n_txn[0]:06d}", "store_id": store, "sku": p["sku"], "quantity": qty,
            "revenue_gbp": round(rev, 2), "margin_gbp": round(rev - qty * cost, 2), "transaction_time": when,
            "availability_pct": avail, "size": p["size"], "channel": r.choices(["store", "self_checkout"], [85, 15])[0],
        })

    by_sku = {p["sku"]: p for p in products}
    dow_mult = [0.9, 0.85, 0.9, 1.0, 1.15, 1.35, 1.0]  # Mon..Sun
    hour_w = [2, 4, 6, 8, 8, 7, 6, 6, 7, 7, 5, 3]       # hours 9..20

    for d in range(182, 0, -1):
        day = g.as_of - timedelta(days=d)
        home_new, sa_promo = d <= N_HOME_NEW, SA_PROMO[1] <= d <= SA_PROMO[0]
        for st in stores:
            s = sites[st]
            mult = CLUSTER_MULT.get(s["cluster"], 1.0) * dow_mult[day.weekday()]
            if st == "ST214":
                if d == FESTIVAL_DAY:
                    mult *= 2.5
                if d <= ROADWORKS_FROM:
                    mult *= 0.8
            recent = d <= 56
            n_rows = 16 if (recent and st == "ST214") else (6 if recent else 3)
            if st == "ST214" and d in (1, 2, 3):
                n_rows = 12
            cum = cum_for(home_new, sa_promo, st == "ST214")
            for _ in range(n_rows):
                p = r.choices(products, cum_weights=cum)[0]
                base = (r.randint(1, 3) if st == "ST214" else r.randint(1, 7)) if recent else r.randint(4, 12)
                qty = max(1, round(base * mult))
                hour = r.choices(range(9, 21), weights=hour_w)[0]
                when = datetime.combine(day, time(hour, r.randint(0, 59)))
                avail = max(0, min(100, avail_base[p["sku"]] + r.randint(-3, 3)))
                lo, hi = (0.88, 0.92) if (p["category"] == "Small Appliances" and sa_promo) else (0.95, 1.0)
                add_sale(st, p, when, qty, avail, lo, hi)

    # ---- ST214 story: three best-selling blouses lose availability in the last 72 hours ----
    for sku in sorted(STORY_SKUS):
        p = by_sku[sku]
        for d in range(35, 3, -1):
            day = g.as_of - timedelta(days=d)
            for hour in (11, 15):
                mult = 0.8 if d <= ROADWORKS_FROM else 1.0
                add_sale("ST214", p, datetime.combine(day, time(hour, r.randint(0, 59))),
                         max(1, round(r.randint(1, 2) * mult * dow_mult[day.weekday()])), r.randint(93, 99))
    # (day offset, hour, qty, availability) per SKU: morning rush then gaps from lunchtime, worsening each day
    plan = {
        "SKU-100007": [(3, 10, 2, 92), (3, 11, 3, 91), (3, 12, 2, 88), (3, 14, 1, 84), (3, 16, 1, 80),
                       (2, 10, 3, 80), (2, 11, 3, 78), (2, 12, 2, 70),
                       (1, 10, 2, 66), (1, 11, 2, 62), (1, 12, 1, 55)],
        "SKU-100014": [(3, 10, 2, 90), (3, 11, 2, 89), (3, 13, 2, 85), (3, 15, 1, 80),
                       (2, 10, 2, 78), (2, 11, 3, 75), (2, 12, 1, 68),
                       (1, 10, 2, 64), (1, 11, 1, 58), (1, 12, 1, 52)],
        "SKU-100021": [(3, 10, 2, 94), (3, 11, 2, 93), (3, 14, 2, 90), (3, 16, 1, 88),
                       (2, 10, 2, 90), (2, 11, 2, 89), (2, 13, 1, 86),
                       (1, 10, 2, 87), (1, 11, 2, 85), (1, 14, 1, 84)],
    }
    for sku, rows in plan.items():
        for d, hour, qty, av in rows:
            add_sale("ST214", by_sku[sku],
                     datetime.combine(g.as_of - timedelta(days=d), time(hour, r.randint(0, 59))), qty, av)

    # ---- allocation and plan for sell-through (units bought/allocated per store and category) ----
    cutoff = g.as_of - timedelta(days=29)
    units30 = {}
    cat_of = {p["sku"]: p["category"] for p in products}
    for t in sales:
        if t["transaction_time"].date() >= cutoff:
            k = (t["store_id"], cat_of[t["sku"]])
            units30[k] = units30.get(k, 0) + t["quantity"]
    alloc = []
    cats = sorted({p["category"] for p in products})
    tops_rate = {st: (0.31 + r.uniform(-0.03, 0.03) if sites[st]["region"] == "Scotland" else 0.50 + r.uniform(-0.05, 0.05))
                 for st in stores}
    raw = {}
    for st in stores:
        for c in cats:
            u = units30.get((st, c), 0)
            if u == 0:
                continue
            rate = tops_rate[st] if c == "Tops" else 0.55 + r.uniform(-0.06, 0.06)
            raw[(st, c)] = u / rate
    tops_units = sum(units30.get((st, "Tops"), 0) for st in stores)
    tops_alloc = sum(v for (st, c), v in raw.items() if c == "Tops")
    scale = (tops_units / 0.44) / tops_alloc          # range as a whole sells through 44% against a 55% plan
    for (st, c), v in sorted(raw.items()):
        a = v * (scale if c == "Tops" else 1.0)
        alloc.append({"store_id": st, "category": c, "allocated_units": int(round(a)), "plan_sell_through_pct": 55.0})

    # ---- size curves (how each category was bought) ----
    curves = []
    sizes_of = {}
    for p in products:
        sizes_of.setdefault(p["category"], set()).add(p["size"])
    for c in cats:
        if c == "Tops":
            for sz, pct in TOPS_EXPECTED.items():
                curves.append({"category": c, "size": sz, "expected_pct": pct})
            continue
        sz = sorted(sizes_of[c])
        shares = [30.0, 40.0, 30.0] if len(sz) == 3 else [round(100.0 / len(sz), 1)] * len(sz)
        for s_, pct in zip(sz, shares):
            curves.append({"category": c, "size": s_, "expected_pct": pct})

    # ---- last-year daily sales by region (same-day comparator, 364 days back) ----
    daily = {}
    for t in sales:
        k = (sites[t["store_id"]]["region"], t["transaction_time"].date())
        a = daily.setdefault(k, [0, 0.0, 0.0])
        a[0] += t["quantity"]; a[1] += t["revenue_gbp"]; a[2] += t["margin_gbp"]
    ly = []
    for (reg, day), (u, rev, mar) in sorted(daily.items()):
        if (g.as_of - day).days > 84:
            continue
        f = (1.07 + r.uniform(-0.03, 0.03)) if reg == "UK North" else (1.0 + r.uniform(-0.06, 0.06))
        ly.append({"region": reg, "sale_date": day - timedelta(days=364), "units": int(round(u * f)),
                   "revenue_gbp": round(rev * f, 2), "margin_gbp": round(mar * f * (1.012 if reg == "UK North" else 1.0), 2)})

    # ---- POS exceptions ----
    exc = []
    eid = [0]

    def add_exc(st, day, hour, minute, etype, emp, till, amount, reason, sku=None):
        eid[0] += 1
        exc.append({
            "exception_id": f"EXC-{eid[0]:06d}", "store_id": st, "till_id": till, "employee_id": emp,
            "exception_type": etype, "sku": sku or "", "amount_gbp": round(amount, 2),
            "quantity": 0 if etype == "discount" else r.randint(1, 3), "reason": reason,
            "exception_time": datetime.combine(day, time(hour, minute)), "region": sites[st]["region"],
        })

    amt = {"void": (5, 60), "refund": (10, 90), "discount": (3, 25)}
    for d in range(182, 0, -1):
        day = g.as_of - timedelta(days=d)
        for st in stores:
            n = 1 if r.random() < 0.45 else 0
            for _ in range(n):
                etype = r.choices(["void", "refund", "discount"], [30, 40, 30])[0]
                lo, hi = amt[etype]
                tills = ["T01", "T03", "T04", "T05", "T06"] if st in ("ST159", "ST214") else ["T01", "T02", "T03", "T04", "T05", "T06"]
                add_exc(st, day, r.randint(9, 19), r.randint(0, 59), etype, mgr[st], r.choice(tills),
                        r.uniform(lo, hi), r.choice(REASONS[etype]), r.choice(products)["sku"] if r.random() < 0.7 else None)

    # ST159: voids/refunds surge on till T02 by EMP-00481, mostly 14:00-16:00, ramping over the last six weeks
    week_counts = [2, 3, 5, 7, 9, 11]
    for w, cnt in enumerate(week_counts):
        for _ in range(cnt):
            d = 42 - 7 * w - r.randint(0, 6)
            day = g.as_of - timedelta(days=max(d, 1))
            etype = r.choices(["void", "refund", "discount"], [60, 28, 12])[0]
            lo, hi = {"void": (30, 75), "refund": (35, 90), "discount": (10, 25)}[etype]
            reason = (r.choice(["operator error", "operator error", "duplicate", "wrong till"]) if etype == "void"
                      else r.choice(["no receipt", "wrong item", "damaged"]) if etype == "refund" else "price match")
            hour = r.choice([14, 14, 15, 15, 15, 14, 16 - 1, r.randint(9, 19)])
            add_exc("ST159", day, hour, r.randint(0, 59), etype, "EMP-00481", "T02", r.uniform(lo, hi), reason,
                    r.choice(products)["sku"])
    for _ in range(4):  # a little legitimate cover from the neighbouring Leeds store manager
        d = r.randint(1, 40)
        add_exc("ST159", g.as_of - timedelta(days=d), r.randint(10, 18), r.randint(0, 59), "void", "EMP-00472", "T01",
                r.uniform(8, 30), "customer request")
    # ST183: refund spike on high-value items across tills (weaker signal, organised-looking)
    for i in range(9):
        d = 38 - 4 * i
        add_exc("ST183", g.as_of - timedelta(days=max(d, 1)), r.choice([11, 12, 17, 18]), r.randint(0, 59), "refund",
                mgr["ST183"], r.choice(["T01", "T03", "T04"]), r.uniform(110, 160), "wrong item", r.choice(products)["sku"])
    # ST214: refunds 'wrong item' at till T03 by cover staff EMP-00529, mostly Saturdays, last four weeks
    for i in range(14):
        d = 27 - 2 * i
        add_exc("ST214", g.as_of - timedelta(days=max(d, 1)), r.choice([13, 14, 15]), r.randint(0, 59), "refund",
                "EMP-00529", "T03", r.uniform(40, 85), r.choice(["wrong item", "wrong item", "fit issue"]),
                r.choice(products)["sku"])

    # ---- self-checkout rules and weekly scan stats ----
    weeks = g.weeks(12)
    base = {"weight_tolerance": 2.0, "unexpected_item": 1.6, "age_verification": 0.8}
    # rule_type -> store -> function(week index 0..11) -> rate
    story = {
        ("ST150", "unexpected_item"): lambda i: 1.7 if i < 10 else 4.6,                   # step: scanner fault
        ("ST159", "unexpected_item"): lambda i: 1.6 if i < 9 else 4.5,                    # step: scanner fault
        ("ST181", "unexpected_item"): lambda i: 1.7 if i < 11 else 4.8,                   # step: scanner fault
        ("ST165", "unexpected_item"): lambda i: 1.6 if i < 7 else 1.6 + 0.6 * (i - 6),    # gradual ramp: deliberate
        ("ST183", "unexpected_item"): lambda i: 1.7 if i < 7 else 1.7 + 0.55 * (i - 6),
    }
    weekly, rules = [], []
    chain = {}
    rid = [0]
    for rt in base:
        rid[0] += 1
        chain[rt] = f"SCR-{rid[0]:06d}"
    scr_story = {s: f"SCR-90000{i + 1}" for i, s in enumerate(LEEDS_SC)}
    latest = {rt: [] for rt in base}
    for st in stores:
        for rt in base:
            store_off = r.uniform(-0.3, 0.3)
            rates = []
            for i, wk in enumerate(weeks):
                fn = story.get((st, rt))
                target = fn(i) if fn else base[rt] + store_off + r.uniform(-0.2, 0.2)
                scans = r.randint(1800, 3200)
                ex = int(round(scans * (target + r.uniform(-0.1, 0.1)) / 100))
                rate = round(100.0 * ex / scans, 2)
                rates.append(rate)
                weekly.append({"store_id": st, "rule_type": rt, "week_start": wk, "scans": scans, "exceptions": ex,
                               "exception_rate_pct": rate})
            avg4 = round(sum(rates[-4:]) / 4, 2)
            latest[rt].append(avg4)
            if rt == "unexpected_item" and st in scr_story:
                rule_id, thr = scr_story[st], 0.15
            else:
                rid[0] += 1
                rule_id, thr = f"SCR-{rid[0]:06d}", None
            thr = thr or (round(r.uniform(0.4, 0.7), 2) if rt == "weight_tolerance" else round(r.uniform(0.08, 0.2), 2))
            rules.append({
                "rule_id": rule_id, "store_id": st, "rule_name": f"{sites[st]['name']} {rt.replace('_', ' ')}",
                "rule_type": rt, "threshold_value": thr, "threshold_unit": "kg" if rt == "weight_tolerance" else "percent",
                "status": "active", "scan_exception_rate_pct": avg4,
                "updated_at": datetime.combine(g.as_of - timedelta(days=r.randint(20, 90)), time(9, 0)),
            })
    for rt, rule_id in chain.items():
        rules.append({
            "rule_id": rule_id, "store_id": "", "rule_name": f"Chain-wide {rt.replace('_', ' ')}", "rule_type": rt,
            "threshold_value": 0.5 if rt == "weight_tolerance" else 0.1 if rt == "unexpected_item" else 1.0,
            "threshold_unit": "kg" if rt == "weight_tolerance" else "percent", "status": "active",
            "scan_exception_rate_pct": round(sum(latest[rt]) / len(latest[rt]), 2),
            "updated_at": datetime.combine(g.as_of - timedelta(days=45), time(9, 0)),
        })

    return {
        "sales_transactions": sales, "pos_exceptions": exc, "self_checkout_rules": rules,
        "self_checkout_weekly": weekly, "size_curves": curves, "store_range_allocation": alloc,
        "region_sales_ly": ly,
    }
