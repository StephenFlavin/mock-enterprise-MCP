"""E-commerce orders, delivery promises, marketing plans, price changes, resale and parcel volumes.

Hand-written story rows live in seed/ (delivery rules and their changes, peak marketing plans, last-week price moves).
This file generates the surrounding data. Everything that a tool aggregates over a rolling window is built from
cycles and constants (not random draws), so answers do not wobble with the window edge.
"""
from datetime import timedelta

UK_AREAS = {  # postcode area -> share weight of UK orders (top ten by orders are well separated from the rest)
    "M1": 30, "B1": 25, "SW1": 21, "LS1": 17, "SE1": 15, "G1": 14, "E1": 13, "N1": 12, "L1": 11, "W1": 10,
    "NW1": 7, "EH1": 7, "BS1": 6, "CF1": 5, "NG1": 5, "S1": 4, "NE1": 3, "LE1": 3, "EC1": 2, "WC1": 2,
}
NEXT_DAY_ON = {"M1", "B1", "SW1", "SE1", "E1", "N1", "W1", "NW1", "BS1", "EC1", "WC1"}  # same as seed/delivery_rules.csv

REGION_SHARE = {"UK": 52, "DE": 14, "FR": 13, "US": 9, "NL": 6, "BE": 4, "ES": 2}
# latest weekly market metrics: conversion %, return rate %, average basket GBP (cross-border baskets are ~GBP 62)
LATEST = {
    "UK": (2.45, 15.2, 48.50), "DE": (1.85, 18.5, 62.00), "FR": (1.92, 17.3, 62.50), "US": (1.65, 16.8, 62.25),
    "NL": (2.10, 16.0, 61.75), "BE": (2.05, 17.8, 62.00), "ES": (1.75, 19.2, 61.50),
}
# daily orders per region: before / since the week starting 2026-09-07 (cross-border grows, UK slips)
DAILY_OLD = {"UK": 2000, "DE": 420, "FR": 380, "US": 210, "NL": 140, "BE": 90, "ES": 70}
DAILY_NEW = {"UK": 1900, "DE": 470, "FR": 430, "US": 250, "NL": 160, "BE": 100, "ES": 80}
UNITS_PER_ORDER = {"UK": 1.2, "DE": 1.55, "FR": 1.5, "US": 1.6, "NL": 1.5, "BE": 1.5, "ES": 1.5}
BASKET = {"UK": 48.0, "DE": 62.0, "FR": 62.0, "US": 62.0, "NL": 62.0, "BE": 62.0, "ES": 62.0}
# parcels per day, average parcel value GBP, share under the customs low-value thresholds
PARCELS = {"GB": (5200, 60.00, 0.99), "DE": (850, 62.00, 0.97), "FR": (700, 62.30, 0.97), "NL": (480, 62.00, 0.97),
           "BE": (300, 62.50, 0.96), "ES": (260, 61.50, 0.97), "US": (330, 62.25, 0.95)}
BASKET_WOBBLE = [-3, -1, 0, 1, 3, 2, -2, 0, 1, -1]  # sums to zero: cross-border averages stay at 62 in any window


def _top_skus(g, n):
    """Top SKUs by revenue over the last 13 weeks, from master sales_weekly (same ranking as get_top_products_by_sales)."""
    cut = g.as_of - timedelta(days=91)
    rev = {}
    for r in g.master("sales_weekly"):
        if r["week_start"] >= cut.isoformat():
            rev[r["sku"]] = rev.get(r["sku"], 0.0) + float(r["revenue_gbp"])
    return [s for s, _ in sorted(rev.items(), key=lambda kv: -kv[1])[:n]]


def _cycle_pool(r, weights):
    pool = [k for k, w in weights.items() for _ in range(w)]
    r.shuffle(pool)
    return pool


def generate(g):
    r = g.rng
    products = {p["sku"]: p for p in g.master("products")}
    customers = g.master("customers")[:400]
    top = _top_skus(g, 150)

    # ---- weekly market metrics (13 weeks per market, newest = LATEST) ----
    market_metrics = []
    for region, (conv, ret, basket) in LATEST.items():
        for k in range(13):
            wob = [0.0, -0.02, 0.01, 0.03, -0.01, 0.02, 0.0, -0.03, 0.01, 0.02, -0.02, 0.01, 0.0][k]
            market_metrics.append({
                "region": region,
                "conversion_rate_pct": round(conv + (0 if k == 0 else wob), 2),
                "return_rate_pct": round(ret + (0 if k == 0 else -wob * 3), 1),
                "avg_basket_gbp": basket,
                "is_cross_border": region != "UK",
                "measured_at": g.as_of - timedelta(weeks=k),
            })

    # ---- daily volumes per market, 120 days ----
    order_daily_volumes = []
    change = g.as_of - timedelta(days=g.as_of.weekday()) - timedelta(weeks=4)  # Monday 4 weeks back
    for region in REGION_SHARE:
        for i in range(120):
            d = g.days_ago(i)
            orders = (DAILY_NEW if d >= change else DAILY_OLD)[region]
            value = round(orders * BASKET[region], 2)
            order_daily_volumes.append({
                "region": region, "date": d, "units": round(orders * UNITS_PER_ORDER[region]), "orders": orders,
                "value_gbp": value, "avg_basket_gbp": BASKET[region],
            })

    # ---- parcels per destination, 120 days ----
    parcel_volumes = []
    for country, (n, avg, low) in PARCELS.items():
        for i in range(120):
            parcel_volumes.append({
                "destination_country": country, "date": g.days_ago(i), "parcels": n, "low_value_parcels": round(n * low),
                "value_gbp": round(n * avg, 2), "avg_parcel_value_gbp": avg,
            })

    # ---- order sample, 90 days (oldest first) ----
    return_rate = {k: v[1] for k, v in LATEST.items()}
    region_pool = _cycle_pool(r, REGION_SHARE)
    area_pool = _cycle_pool(r, UK_AREAS)
    ecommerce_orders = []
    n_region = {}
    n_order = 0
    n_uk = 0
    for i in range(89, -1, -1):
        date = g.days_ago(i)
        for _ in range(r.randint(28, 38)):
            region = region_pool[n_order % len(region_pool)]
            n_order += 1
            sku = r.choice(top)
            units = r.choices([1, 2], [75, 25])[0]
            area = None
            if region == "UK":
                area = area_pool[n_uk % len(area_pool)]
                n_uk += 1
                basket = 48.5 + BASKET_WOBBLE[n_uk % len(BASKET_WOBBLE)] * 3 + r.uniform(-4, 4)  # UK average basket ~GBP 48.50
                if area in NEXT_DAY_ON:
                    promise = ["next-day", "standard", "next-day", "2-3 days"][n_uk % 4]
                else:
                    promise = ["standard", "2-3 days"][n_uk % 2]
                days = {"next-day": 1, "standard": 3, "2-3 days": 2}[promise] + (r.random() < 0.15)
            else:
                k = n_region[region] = n_region.get(region, 0) + 1
                basket = 62 + BASKET_WOBBLE[k % len(BASKET_WOBBLE)]
                promise = "standard"
                days = r.randint(4, 8)
            u = r.random() * 100
            status = "cancelled" if u < 5 else "returned" if u < 5 + return_rate[region] else "delivered"
            ecommerce_orders.append({
                "order_id": f"ECO-{date.year}-{len(ecommerce_orders) + 1:07d}",
                "customer_id": r.choice(customers)["customer_id"],
                "sku": sku,
                "order_date": date,
                "channel": r.choices(["web", "app", "marketplace"], [55, 35, 10])[0],
                "region": region,
                "postcode_area": area,
                "basket_value_gbp": round(basket, 2),
                "units": units,
                "delivery_promise": promise,
                "status": status,
                "returned": status == "returned",
                "delivery_date": None if status == "cancelled" else date + timedelta(days=days),
                "updated_at": date,
            })

    # ---- price changes on top SKUs: older history only; last week's moves are in seed/price_changes.csv ----
    reasons = ["Promotion", "Seasonal", "Competitor match", "Clearance", "New season"]
    price_changes = []
    for sku in top[:100]:
        for _ in range(r.randint(1, 2)):
            old = float(products[sku]["retail_price_gbp"])
            pct = round(r.uniform(-15, 8), 1)
            price_changes.append({
                "sku": sku, "changed_at": g.date_between(120, 40), "old_price_gbp": old,
                "new_price_gbp": round(old * (1 + pct / 100), 2), "change_pct": pct, "reason": r.choice(reasons),
            })

    # ---- resale listings: shallow discounts look expensive and rarely sell, deep ones sell ----
    resale_skus = [s for s in _top_skus(g, 400) if products[s]["department"] in ("Electricals", "Home", "Kids")][:60]
    bands = [(40, 4, 10, 24), (12, 4, 25, 39), (8, 6, 40, 55)]  # listings, sold, discount range
    resale_listings = []
    k = 0
    for count, sold_n, lo, hi in bands:
        for j in range(count):
            sku = resale_skus[k % len(resale_skus)]
            new = float(products[sku]["retail_price_gbp"])
            disc = lo + (j * 7) % (hi - lo + 1)
            deep = lo >= 40
            resale_listings.append({
                "listing_id": f"RSL-{k + 1:06d}", "sku": sku, "new_price_gbp": new,
                "resale_price_gbp": round(new * (1 - disc / 100), 2), "discount_pct": disc,
                "condition": ["like_new", "good", "fair", "poor"][(j + (2 if deep else 0)) % 4],
                "listed_date": g.days_ago(5 + (k * 3) % 50), "sold": j < sold_n,
                "views": (60 + (j * 17) % 120) if deep else (150 + (j * 29) % 250),
            })
            k += 1

    return {
        "ecommerce_orders": ecommerce_orders,
        "order_daily_volumes": order_daily_volumes,
        "market_metrics": market_metrics,
        "price_changes": price_changes,
        "resale_listings": resale_listings,
        "parcel_volumes": parcel_volumes,
    }
