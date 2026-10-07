"""Spend analytics: supplier spend (reconciled to master annual spend), savings tracker, price variance, input costs."""
import math
import random
from collections import defaultdict
from datetime import date, timedelta

NEARSHORE = {"PT", "TR", "PL"}

# service (indirect) spend of the indirect suppliers in master (supplier_type indirect, master annual spend 0): supplier -> [(category, 12m gbp, kind)]
#   SUP-0085 BrightSpace Cleaning (cleaning), SUP-0087 Hartley MRO (maintenance), SUP-0086 Sentinel Facilities Management (roof project),
#   SUP-0083 Midlands Power & Light and SUP-0084 Pennine Gas (energy), SUP-0081 Calder Corrugated and SUP-0082 Northern Film & Wrap (packaging)
INDIRECT = {
    "SUP-0085": [("Facilities", 1220000, "recurring")],
    "SUP-0087": [("Facilities", 400000, "recurring")],
    "SUP-0086": [("Facilities", 900000, "project")],
    "SUP-0083": [("Energy", 550000, "recurring")],
    "SUP-0084": [("Energy", 200000, "recurring")],
    "SUP-0082": [("Packaging", 600000, "recurring")],
    "SUP-0081": [("Packaging", 700000, "recurring")],
}
SERVICE_RATE = {"Facilities": 35.0, "Energy": 190.0, "Packaging": 0.42}

# monthly slope of a supplier's spend profile over the last 12 months (negative = losing volume)
SLOPE = {"SUP-0023": -0.9, "SUP-0027": -0.55, "SUP-0013": -0.35, "SUP-0055": 0.9, "SUP-0062": 0.7, "SUP-0074": 0.15}

SEASON = {"Home": [1, 1, 1, 1, 1, 1, 1, 1.05, 1.1, 1.2, 1.25, 1.1], "Kids": [1, 1, 1, 1, 1, 1.05, 1.2, 1.3, 1.1, 1, 1, 1],
          "Womenswear": [1, 1, 1.1, 1.15, 1.1, 1, 1, 1.05, 1.15, 1.1, 1, 1], "Menswear": [1, 1, 1.05, 1.1, 1.05, 1, 1, 1.05, 1.15, 1.1, 1, 1]}

# annual input-cost inflation by component (default) and overrides
LABOUR = {"TR": 0.22, "CN": 0.05, "IN": 0.07, "VN": 0.06, "BD": 0.08, "PT": 0.05, "MX": 0.06}
MIX = {"Home": (40, 20, 15, 15, 10), "Womenswear": (45, 30, 8, 12, 5), "Menswear": (45, 30, 8, 12, 5), "Kids": (45, 30, 8, 12, 5),
       "Accessories": (50, 25, 8, 12, 5), "Beauty": (45, 15, 10, 15, 15), "Electricals": (55, 15, 8, 12, 10)}
COMPONENTS = ("raw materials", "labour", "energy", "shipping", "packaging")
OVERPAY_BENCH = {"Knitwear": 0.085, "Shirts": 0.055, "Outerwear": 0.04, "Footwear": 0.02, "Jewellery": -0.012}
SUP_CONTRACT_VAR = {"SUP-0055": 0.07, "SUP-0062": 0.05, "SUP-0013": 0.045}


def generate(g):
    r = g.rng
    sup = {s["supplier_id"]: s for s in g.master("suppliers")}
    prods = g.master("products")
    cat_dept = {p["category"]: p["department"] for p in prods}
    # products that have been bought (or are no longer 'new'): the not-yet-launched master products have no spend, so they must not
    # dilute a supplier's category split
    bought = {l["sku"] for l in g.master("po_lines")}
    live_prods = [p for p in prods if p["status"] != "new" or p["sku"] in bought]
    live_cat_dept = {p["category"]: p["department"] for p in live_prods}
    sup_cats = defaultdict(lambda: defaultdict(int))
    ucost = defaultdict(list)
    for p in live_prods:
        sup_cats[p["supplier_id"]][p["category"]] += 1
        ucost[(p["supplier_id"], p["category"])].append(float(p["unit_cost_gbp"]))
    dept_cats = defaultdict(list)
    for c, d in live_cat_dept.items():
        dept_cats[d].append(c)

    # 24 months, mid-month dates, oldest first; last full month is the one before as_of
    first = date(g.as_of.year, g.as_of.month, 1)
    months = []
    y, m = first.year, first.month
    for _ in range(24):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        months.append(date(y, m, 15))
    months.reverse()

    def profile(sid, kind="product"):
        s = sup[sid]
        r = g.rng_for("profile", sid)
        slope = SLOPE.get(sid, r.uniform(-0.1, 0.1))
        out = []
        for i, d in enumerate(months):
            t = (i - 12) / 11.0 if i >= 12 else 0.0
            sea = SEASON.get(s["category_focus"], [1] * 12)[d.month - 1] if kind == "product" else 1.0
            w = max(0.05, 1 + slope * (t - 0.5)) * sea * r.uniform(0.95, 1.05)
            if i < 12:
                w *= r.uniform(0.86, 0.98)
            if d < date.fromisoformat(s["onboarded_date"]):
                w = 0
            if s["status"] == "exited" and i >= 19:
                w = 0
            out.append(w)
        return out

    def scale(ws, total):
        tail = sum(ws[12:])
        return [w * total / tail for w in ws] if tail else ws

    spend_rows = []
    cell = {}  # (sid, cat) -> monthly spend list
    cell_target = {}  # (sid, cat) -> exact last-12-month total, so a category figure never depends on the random monthly shape
    for sid, s in sup.items():
        extra = INDIRECT.get(sid, [])
        if s.get("supplier_type") == "indirect":  # no products and no master spend: only the service spend below
            if not extra:
                continue
            ir = random.Random("spend-indirect-" + sid)
            cats, product_annual, n, base = {}, 0.0, 1, None
        else:
            ir = g.rng_for("extra", sid)
            product_annual = float(s["annual_spend_gbp"])
            cats = dict(sup_cats.get(sid) or {})
            if not cats:
                cs = dept_cats[s["category_focus"]]
                cats = {c: 1 for c in cs[:3]}
            n = sum(cats.values())
            base = scale(profile(sid), 1.0)
        for c, k in cats.items():
            vals = [v * product_annual * k / n for v in base]
            cell[(sid, c)] = vals
            cell_target[(sid, c)] = product_annual * k / n
        for cat, total, kind in extra:
            ws = [0.0] * 24
            if kind == "project":  # one-off refurbishment: three big months plus a small run-rate
                for i in range(24):
                    ws[i] = ir.uniform(0.9, 1.1) * (1 if i >= 12 else 0.8)
                tot12 = sum(ws[12:])
                ws = [w * 230000 / tot12 for w in ws]  # run-rate base ~ 230k a year
                for i, amt in ((18, 270000), (19, 240000), (20, 160000)):
                    ws[i] += amt
                ws[:12] = [w * 0.8 for w in ws[:12]]
            else:
                for i in range(24):
                    ws[i] = ir.uniform(0.96, 1.04) * (1 if i >= 12 else ir.uniform(0.82, 0.92)) * (1 + (0.01 * (i - 12) if cat == "Energy" else 0))
                if sid == "SUP-0085":
                    ws[21] += 0.12 * 1.0 * sum(ws[12:]) / 12 * 1.0  # one extra deep-clean month
                tot12 = sum(ws[12:])
                ws = [w * total / tot12 for w in ws]
            cell[(sid, cat)] = ws
            cell_target[(sid, cat)] = float(total)

    # round to pounds, fix the last-12-month total to the master annual spend
    for sid, s in sup.items():
        keys = [k for k in cell if k[0] == sid]
        if not keys:
            continue
        for k in keys:
            cell[k] = [round(v) for v in cell[k]]
        target = sum(x[1] for x in INDIRECT[sid]) if s.get("supplier_type") == "indirect" else round(float(s["annual_spend_gbp"]))
        tg = {k: round(cell_target[k]) for k in keys}
        big = max(keys, key=lambda k: tg[k])
        tg[big] += target - sum(tg.values())  # the pound or two of rounding goes to the biggest category
        for k in keys:
            j = max(range(12, 24), key=lambda i: cell[k][i])
            cell[k][j] += tg[k] - sum(cell[k][12:])
    for (sid, c), vals in cell.items():
        s = sup[sid]
        pref = s["tier"] in ("strategic", "preferred")
        if c in SERVICE_RATE:
            dept, base_uc = "Indirect", SERVICE_RATE[c]
        else:
            dept = cat_dept.get(c, s["category_focus"])
            ul = ucost.get((sid, c)) or [30.0]
            base_uc = sum(ul) / len(ul)
        ir = g.rng_for("invoices", sid, c)
        for i, v in enumerate(vals):
            if v <= 0:
                continue
            uc = base_uc * (1 + 0.004 * (i - 12))
            units = max(1, round(v / uc))
            spend_rows.append({"supplier_id": sid, "category": c, "department": dept, "period": months[i], "spend_gbp": float(v),
                               "units": units, "invoice_count": ir.randint(2, 9) if c not in SERVICE_RATE else ir.randint(1, 3),
                               "avg_unit_cost_gbp": round(v / units, 2), "is_preferred": pref})

    # supplier sales (for share of wallet)
    last12 = defaultdict(float)
    for row in spend_rows:
        last12[row["supplier_id"]] += row["spend_gbp"] if row["period"] >= months[12] else 0
    explicit = {"SUP-0074": 0.253}
    supplier_volume = []
    for sid in sup:
        if sup[sid].get("supplier_type") == "indirect":  # service suppliers: fixed share, no random draw (keeps the stream of the others)
            share = 0.35
        else:
            share = explicit.get(sid, g.rng_for("share", sid).uniform(0.04, 0.4))
        supplier_volume.append({"supplier_id": sid, "annual_sales_gbp": float(round(last12[sid] / share, -3))})

    # payment terms benchmark
    base_days = {"CN": 60, "IN": 60, "VN": 60, "TR": 60, "BD": 60, "PT": 45, "IT": 60, "MX": 60, "GB": 30, "DE": 45, "PL": 45, "FR": 45}
    payment = []
    for c in sorted(cat_dept):
        for ctry, d in base_days.items():
            r = g.rng_for("payment", c, ctry)
            std = d + r.choice([-15, 0, 0, 15])
            payment.append({"category": c, "supplier_country": ctry, "market_standard_days": std, "typical_min_days": max(15, std - 30),
                            "typical_max_days": std + 30, "observations_count": r.randint(6, 40)})

    # nearshore forecast
    units_by = defaultdict(float)
    for row in spend_rows:
        units_by[(row["supplier_id"], row["period"])] += row["units"]
    near = []
    fut = [date(months[-1].year + (months[-1].month + k - 1) // 12, (months[-1].month + k - 1) % 12 + 1, 15) for k in range(1, 7)]
    for sid, s in sup.items():
        if s["country"] not in NEARSHORE or s["status"] != "active":
            continue
        r = g.rng_for("nearshore", sid)
        acc = 0.87 if sid == "SUP-0044" else r.uniform(0.9, 1.04)
        com = 0.90 if sid == "SUP-0044" else r.uniform(0.7, 0.95)
        for i, d in enumerate(months[12:], 12):
            act = units_by[(sid, d)]
            if act:
                near.append({"supplier_id": sid, "period": d, "forecasted_volume_units": round(act / (acc * r.uniform(0.97, 1.03))),
                             "commitment_level_pct": round(com * 100, 1)})
        avg = sum(units_by[(sid, d)] for d in months[18:]) / 6
        for d in fut:
            near.append({"supplier_id": sid, "period": d, "forecasted_volume_units": round(avg * r.uniform(1.0, 1.12)),
                         "commitment_level_pct": round(com * 100, 1)})

    # price variance from master PO lines (actual price = master product cost; volume = received qty)
    po = {p["po_id"]: p for p in g.master("purchase_orders")}
    pmap = {p["sku"]: p for p in prods}
    pv = []
    lines = []
    for l in g.master("po_lines"):
        p = po.get(l["po_id"])
        if not p or p["status"] not in ("closed", "received") or int(l["qty_received"] or 0) <= 0:
            continue
        lines.append((p["order_date"], l["po_id"], int(l["line_no"]), l, p))
    lines.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    used = defaultdict(float)
    for _, _, _, l, p in lines:
        prod = pmap[l["sku"]]
        actual = float(prod["unit_cost_gbp"])
        sid = p["supplier_id"]
        vol = int(l["qty_received"])
        # keep the sampled PO lines within the supplier's master annual spend
        if used[sid] + actual * vol > 0.95 * float(sup[sid]["annual_spend_gbp"]):
            continue
        used[sid] += actual * vol
        r = g.rng_for("pricevar", l["po_id"], l["line_no"])
        cv = SUP_CONTRACT_VAR.get(sid, r.uniform(-0.01, 0.02))
        contract = actual / (1 + cv + r.uniform(-0.01, 0.01))
        bv = OVERPAY_BENCH.get(prod["category"], r.uniform(-0.01, 0.03)) + r.uniform(-0.015, 0.015)
        bench = actual / (1 + bv)
        pv.append({"po_id": l["po_id"], "line_no": int(l["line_no"]), "po_date": p["order_date"], "sku": l["sku"], "supplier_id": sid,
                   "category": prod["category"], "contract_price_gbp": round(contract, 2), "benchmark_price_gbp": round(bench, 2),
                   "actual_price_gbp": actual, "volume_units": vol})

    # input costs
    ic = []
    for sid, s in sup.items():
        if s["status"] in ("exited",) or s.get("supplier_type") == "indirect":
            continue
        r = g.rng_for("inputcost", sid)
        dept = s["category_focus"]
        mix = list(MIX[dept])
        k = 0 if sid == "SUP-0074" else r.choice([-2, 0, 2])
        mix[0] += k
        mix[1] -= k
        rates = {"raw materials": r.uniform(0.01, 0.05), "labour": LABOUR.get(s["country"], 0.05) + r.uniform(-0.01, 0.01),
                 "energy": r.uniform(0.02, 0.08), "shipping": r.uniform(-0.02, 0.05), "packaging": r.uniform(0.01, 0.04)}
        if sid == "SUP-0074":
            rates = {"raw materials": 0.12, "labour": 0.07, "energy": 0.15, "shipping": 0.04, "packaging": 0.05}
        for comp, pct in zip(COMPONENTS, mix):
            for i, d in enumerate(months):
                idx = 100 * (1 + rates[comp]) ** ((i - 11) / 12.0) + (0 if sid == "SUP-0074" else r.uniform(-0.4, 0.4))
                ic.append({"supplier_id": sid, "cost_component": comp, "period": d, "index_value": round(idx, 1), "pct_of_total": float(pct)})

    # price increase history
    inc = []
    n = 0
    for sid, s in sup.items():
        if s["status"] != "active" or s.get("supplier_type") == "indirect":
            continue
        r = g.rng_for("increase", sid)
        cats = list(sup_cats.get(sid) or {}) or dept_cats[s["category_focus"]][:1]
        for _ in range(r.choice([0, 0, 1, 1, 2])):
            n += 1
            c = r.choice(cats)
            inc.append({"increase_id": f"PRI-{n:06d}", "supplier_id": sid, "category": c, "department": cat_dept.get(c, s["category_focus"]),
                        "effective_date": g.days_ago(r.randint(60, 900)), "increase_pct": round(r.uniform(1.5, 6.0), 1),
                        "reason": r.choice(["Raw material costs", "Labour cost rise", "Energy costs", "Freight costs", "Annual uplift"]),
                        "outcome": r.choice(["accepted", "accepted", "negotiated", "rejected"])})

    # savings initiatives (older, completed history; recent story rows come from seed)
    initiatives = []
    rate = {"consolidation": 0.82, "renegotiation": 0.66, "spec_change": 0.55, "nearshore": 0.72, "other": 0.70}
    cats_all = sorted(live_cat_dept)
    for i in range(48):
        r = g.rng_for("initiative", i)
        t = r.choice(list(rate))
        c = r.choice(cats_all)
        rep = float(r.randrange(30, 400, 5) * 1000)
        comp = g.days_ago(r.randint(420, 1300))
        start = comp - timedelta(days=r.randint(90, 240))
        initiatives.append({"initiative_id": f"INIT-{i + 1:06d}", "name": f"{c} {t.replace('_', ' ')}", "category": c,
                            "supplier_id": r.choice([None] + [x for x, v in sup_cats.items() if c in v] or [None]),
                            "initiative_type": t, "reported_saving_gbp": rep, "realised_saving_gbp": float(round(rep * rate[t] * r.uniform(0.85, 1.15), -3)),
                            "status": "completed", "start_date": start, "target_completion_date": comp - timedelta(days=r.randint(0, 30)),
                            "actual_completion_date": comp, "created_at": start, "updated_at": comp})

    return {"supplier_spend": spend_rows, "supplier_volume": supplier_volume, "payment_terms_benchmark": payment,
            "nearshore_forecast": near, "price_variance_data": pv, "supplier_input_costs": ic, "supplier_price_increases": inc,
            "savings_initiatives": initiatives}
