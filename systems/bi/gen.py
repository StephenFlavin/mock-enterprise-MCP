"""BI & Dashboards analytics data: monthly store and product performance vs plan.

Product actuals are rolled up from master sales_weekly (units and revenue per calendar month of week_start), so BI
sales agree with the sales history other systems read. Store units are the master store-channel units for the
month shared out across all open stores by size and cluster, so store totals add up to the master total.
The story stores/products (see seed/*.csv) are not generated here: their rows come from the seed files.
"""
from collections import defaultdict
from datetime import date, timedelta

STORY_STORES = {"ST141", "ST142", "ST143", "ST144", "ST145", "ST150"}
STORY_SKUS = {"SKU-100007", "SKU-100014", "SKU-100021", "K-1700", "PF-220"}
CLUSTER_FACTOR = {"A": 1.25, "B": 1.0, "C": 0.85, "D": 0.6}


def _month_end(y, m):
    return (date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1))


def _clip(x, lo, hi):
    return max(lo, min(hi, x))


def generate(g):
    r = g.rng
    today = g.as_of

    # last four complete calendar months
    months = []
    y, m = today.year, today.month
    for _ in range(4):
        m -= 1
        if m == 0:
            m, y = 12, y - 1
        months.append((y, m))
    months.reverse()

    # master weekly sales rolled up per sku and month, and in total
    sku_m = defaultdict(lambda: [0, 0.0])
    tot_m = defaultdict(lambda: [0, 0.0, 0])  # store units, revenue, all units
    for w in g.master("sales_weekly"):
        key = w["week_start"][:7]
        sku_m[(w["sku"], key)][0] += int(w["store_units"]) + int(w["online_units"])
        sku_m[(w["sku"], key)][1] += float(w["revenue_gbp"])
        tot_m[key][0] += int(w["store_units"])
        tot_m[key][1] += float(w["revenue_gbp"])
        tot_m[key][2] += int(w["store_units"]) + int(w["online_units"])

    stores = [s for s in g.master("sites") if s["type"] == "store" and s["status"] == "open"]
    weights = {s["site_id"]: float(s["sqft"]) ** 0.8 * CLUSTER_FACTOR.get(s["cluster"], 1.0) for s in stores}
    wsum = sum(weights.values())

    store_perf, store_targets, product_perf, product_targets = [], [], [], []

    for (y, m) in months:
        pe = _month_end(y, m)
        key = f"{y}-{m:02d}"
        units_total, rev_total, all_units = tot_m[key]
        avg_price = rev_total / max(all_units, 1)
        for s in stores:
            sid = s["site_id"]
            if sid in STORY_STORES:
                continue
            units = int(units_total * weights[sid] / wsum * r.uniform(0.94, 1.06))
            sales = round(units * avg_price * r.uniform(0.97, 1.03), 2)
            margin = round(_clip(r.gauss(34, 2.0), 27, 41), 1)
            store_perf.append({
                "site_id": sid, "period_end": pe, "sales_units": units, "sales_gbp": sales,
                "margin_pct": margin,
                "availability_pct": round(_clip(r.gauss(96.6, 0.8), 95, 99), 1),
                "shrink_pct": round(_clip(r.gauss(1.2, 0.2), 0.7, 1.7), 1),
                "labour_cost_pct": round(_clip(r.gauss(10.2, 0.7), 8.5, 11.8), 1),
                "updated_at": pe})
            # targets: most stores meet plan; a few miss it by under 1.5%
            f = r.uniform(0.985, 1.04)
            store_targets.append({
                "site_id": sid, "period_end": pe,
                "sales_units_target": int(units / f), "sales_gbp_target": round(sales / f, 2),
                "margin_pct_target": round(margin - r.uniform(-0.2, 1.2), 1), "updated_at": pe})

        for sku in sorted({k[0] for k in sku_m if k[1] == key} - STORY_SKUS):
            units, rev = sku_m[(sku, key)]
            if units <= 0:
                continue
            margin = round(_clip(r.gauss(36, 3.0), 26, 50), 1)
            returns = round(_clip(r.gauss(2.2, 0.5), 0.8, 3.6), 1)
            rating = round(_clip(r.gauss(4.2, 0.25), 3.6, 4.8), 1)
            f = r.uniform(0.97, 1.03)
            product_perf.append({
                "sku": sku, "period_end": pe, "sales_units": units, "sales_gbp": round(rev, 2),
                "margin_pct": margin, "returns_pct": returns, "avg_rating": rating, "updated_at": pe})
            product_targets.append({
                "sku": sku, "period_end": pe,
                "sales_units_target": int(units * f), "sales_gbp_target": round(rev * f, 2),
                "margin_pct_target": round(margin + r.uniform(-1, 1), 1),
                "returns_pct_target": 2.5, "avg_rating_target": 4.2, "updated_at": pe})

    return {
        "store_performance": store_perf,
        "product_performance": product_perf,
        "store_targets": store_targets,
        "product_targets": product_targets,
        "data_quality_issues": [],   # seed/data_quality_issues.csv
        "scheduled_reports": [],     # seed/scheduled_reports.csv
    }
