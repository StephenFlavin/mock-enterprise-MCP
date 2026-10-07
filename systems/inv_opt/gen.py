"""Inventory optimisation data, derived from master sales history, products and suppliers.

Demand statistics come from master.sales_weekly (store + online units), lead times and
costs from master.products, so every figure agrees with the demand, PO and IMS systems.
"""
import statistics as st
from collections import defaultdict
from statistics import NormalDist

SEGMENTS = [("SEG-001", "A", "A items (top sellers by value)", 95),
            ("SEG-002", "B", "B items (mid value)", 92),
            ("SEG-003", "C", "C items (long tail)", 90)]
TARGET = {a: t for _, a, _, t in SEGMENTS}


def generate(g):
    r = g.rng
    products = {p["sku"]: p for p in g.master("products")}

    # ---- demand statistics from 52 weeks of master sales ----
    wk = defaultdict(list)
    for s in g.master("sales_weekly"):
        wk[s["sku"]].append((s["week_start"], int(s["store_units"]), int(s["online_units"]), float(s["markdown_gbp"] or 0)))
    stats = {}
    for sku, rows in wk.items():
        if sku not in products or len(rows) < 8:
            continue
        rows.sort()
        u = [a + b for _, a, b, _ in rows]
        mu = st.mean(u)
        if mu <= 0:
            continue
        sd = st.pstdev(u)
        n = len(u)
        peak = max(st.mean(u[i:i + 4]) for i in range(max(1, n - 3)))
        recent, prior = st.mean(u[-13:]), st.mean(u[:-13]) if n > 13 else mu
        chg = (recent - prior) / prior * 100 if prior else 0
        tot = sum(u)
        stats[sku] = {
            "mu": mu, "sd": sd, "cv": sd / mu, "n": n, "peak": peak / mu, "chg": chg,
            "zero": 100.0 * sum(1 for x in u if x == 0) / n,
            "md": 100.0 * sum(1 for *_, m in rows if m > 0) / n,
            "store": 100.0 * sum(a for _, a, _, _ in rows) / tot if tot else 0,
            "annual": mu * 52,
        }

    ranked = sorted(stats, key=lambda k: -stats[k]["annual"])
    top200 = ranked[:200]

    # ---- supplier lead-time drift: a few suppliers got much slower ----
    sup_count = defaultdict(int)
    for k in top200:
        sup_count[products[k]["supplier_id"]] += 1
    planted_sup = [s for s, _ in sorted(sup_count.items(), key=lambda x: (-x[1], x[0]))[:3]]
    sup_shift = {}
    for s in sorted({p["supplier_id"] for p in products.values()}):
        sup_shift[s] = r.uniform(-0.03, 0.03)
    for s, v in zip(planted_sup, (0.45, 0.35, 0.30)):
        sup_shift[s] = v

    # ---- planted mis-set policies among the fastest sellers ----
    pool = top200[:60]
    low_plants = set(r.sample(pool, 6))
    high_plants = set(r.sample([k for k in pool if k not in low_plants], 4))

    z = {p: NormalDist().inv_cdf(p / 100.0) for p in range(50, 100)}
    zrows = [{"service_level_pct": p, "z_score": round(v, 3)} for p, v in z.items()]

    policies, demand, lts = [], [], []
    for sku in sorted(stats):
        s, p = stats[sku], products[sku]
        cls = p["abc_class"]
        sl = TARGET[cls]
        base_lt = int(p["lead_time_days"])
        # policy as it was set at the last review (older demand and baseline lead time)
        mu_p, sd_p = s["mu"] * r.uniform(0.97, 1.03), s["sd"] * r.uniform(0.96, 1.04)
        sig_l = base_lt * 0.08 / 7.0
        ss = z[sl] * ((base_lt / 7.0) * sd_p ** 2 + mu_p ** 2 * sig_l ** 2) ** 0.5
        x = r.random()
        if sku in low_plants:
            ss *= r.uniform(0.40, 0.55)
        elif sku in high_plants:
            ss *= r.uniform(2.0, 2.4)
        elif x < 0.05:
            ss *= r.uniform(0.55, 0.75)
        elif x < 0.10:
            ss *= r.uniform(1.35, 1.7)
        ss = max(1, int(round(ss)))
        rop = int(round(mu_p * base_lt / 7.0 + ss))
        review = r.randint(60, 200)
        policies.append({
            "sku": sku, "reorder_point_units": rop, "safety_stock_units": ss, "service_level_target_pct": sl,
            "lead_time_days": base_lt, "annual_volume_units": int(round(s["annual"])), "cv_demand": round(s["cv"], 3),
            "category": p["category"], "abc_class": cls, "last_review_date": g.days_ago(review),
            "updated_at": g.days_ago(review),
        })

        # demand analysis and the main reason demand is volatile
        status = p["status"]
        if s["n"] < 16:
            why = "Short sales history (recent launch)"
        elif s["md"] >= 25:
            why = "Promotion and markdown driven"
        elif s["zero"] >= 10:
            why = "Intermittent demand (weeks with no sales)"
        elif s["peak"] >= 1.8:
            why = "Strong seasonal peak"
        elif abs(s["chg"]) >= 25:
            why = "Recent trend shift (" + ("up" if s["chg"] > 0 else "down") + ")"
        else:
            why = "General volatility"
        demand.append({
            "sku": sku, "demand_52w_mean": round(s["mu"], 1), "demand_52w_stdev": round(s["sd"], 1),
            "demand_cv": round(s["cv"], 3), "seasonality_factor": round(s["peak"], 2),
            "trend_direction": "up" if s["chg"] > 10 else "down" if s["chg"] < -10 else "stable",
            "high_variability": s["cv"] > 0.40, "last_calculated_date": g.days_ago(r.randint(1, 14)),
            "weeks_of_history": s["n"], "zero_weeks_pct": round(s["zero"], 1), "markdown_weeks_pct": round(s["md"], 1),
            "store_share_pct": round(s["store"], 1), "variability_driver": why,
        })

        # supplier lead time actually observed
        sup = p["supplier_id"]
        act = max(1, int(round(base_lt * (1 + sup_shift[sup]) * r.uniform(0.98, 1.02))))
        sd_frac = r.uniform(0.18, 0.26) if sup in planted_sup else r.uniform(0.07, 0.10)
        lts.append({
            "sku": sku, "supplier_id": sup, "lead_time_days": act, "lead_time_stdev_days": round(act * sd_frac, 1),
            "change_from_baseline_pct": round((act - base_lt) / base_lt * 100, 1), "sample_size": r.randint(6, 24),
            "measurement_date": g.days_ago(r.randint(1, 21)),
        })

    counts = defaultdict(int)
    for pol in policies:
        counts[pol["abc_class"]] += 1
    segs = [{"segment_id": sid, "abc_class": cls, "segment_name": nm, "sku_count": counts[cls],
             "target_service_level_pct": t, "status": "active", "updated_at": g.days_ago(45)}
            for sid, cls, nm, t in SEGMENTS]

    return {"sku_inventory_policies": policies, "sku_demand_analysis": demand, "segment_service_levels": segs,
            "supplier_lead_time_actuals": lts, "service_level_z": zrows}
