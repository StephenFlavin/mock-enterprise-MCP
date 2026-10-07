"""Generate pricing data: category reference data (elasticity, positioning, clearance options) for every master
category, plus background promotions, markdowns, price changes and tests in categories that carry no story.
Story rows (outerwear, kitchenware, knitwear, trousers, bags, bedding ...) live only in seed/*.csv."""
from datetime import timedelta

# category: (department, price elasticity, income elasticity, 95% CI +/-, data points, target position,
#            min/max price index vs category median, full-price cannibalisation % per 10 points of markdown depth)
CATS = {
    "Bags": ("Accessories", -1.35, 1.25, 0.27, 38, "mid_market", 0.6, 1.4, 3.8),
    "Footwear": ("Accessories", -1.30, 1.00, 0.22, 72, "mid_market", 0.7, 1.4, 4.6),
    "Jewellery": ("Accessories", -1.65, 1.55, 0.25, 60, "premium", 0.7, 1.6, 2.9),
    "Scarves": ("Accessories", -1.45, 0.90, 0.30, 33, "value", 0.6, 1.3, 3.5),
    "Bodycare": ("Beauty", -1.10, 0.25, 0.20, 88, "value", 0.7, 1.3, 2.2),
    "Fragrance": ("Beauty", -1.25, 1.10, 0.24, 64, "premium", 0.7, 1.5, 2.5),
    "Haircare": ("Beauty", -1.05, 0.30, 0.19, 91, "value", 0.7, 1.3, 2.0),
    "Skincare": ("Beauty", -1.15, 0.40, 0.21, 80, "mid_market", 0.7, 1.4, 2.4),
    "Audio": ("Electricals", -1.18, 1.30, 0.25, 75, "mid_market", 0.7, 1.4, 4.2),
    "Personal Care": ("Electricals", -1.48, 0.70, 0.21, 62, "mid_market", 0.7, 1.4, 4.0),
    "Small Appliances": ("Electricals", -1.25, 0.65, 0.18, 85, "mid_market", 0.7, 1.4, 4.1),
    "Smart Home": ("Electricals", -1.30, 1.45, 0.26, 57, "premium", 0.7, 1.5, 4.4),
    "Bedding": ("Home", -1.40, 0.70, 0.23, 68, "mid_market", 0.7, 1.4, 3.6),
    "Cookware": ("Home", -1.32, 0.60, 0.20, 70, "mid_market", 0.7, 1.4, 3.9),
    "Drinkware": ("Home", -1.30, 0.55, 0.30, 31, "value", 0.6, 1.3, 3.4),
    "Lighting": ("Home", -1.35, 0.95, 0.24, 52, "mid_market", 0.7, 1.4, 3.3),
    "Storage": ("Home", -1.20, 0.60, 0.22, 66, "value", 0.6, 1.3, 3.0),
    "Towels": ("Home", -1.15, 0.35, 0.21, 74, "value", 0.7, 1.3, 2.8),
    "Babywear": ("Kids", -1.00, 0.20, 0.19, 83, "value", 0.7, 1.3, 2.1),
    "Nightwear": ("Kids", -1.15, 0.45, 0.22, 59, "value", 0.7, 1.3, 2.6),
    "Outerwear": ("Menswear", -1.52, 0.85, 0.34, 41, "mid_market", 0.7, 1.4, 4.8),
    "Schoolwear": ("Kids", -0.95, 0.15, 0.18, 96, "value", 0.7, 1.2, 1.8),
    "Knitwear": ("Womenswear", -1.40, 0.90, 0.24, 61, "mid_market", 0.7, 1.4, 4.3),
    "Shirts": ("Menswear", -1.30, 0.80, 0.23, 70, "mid_market", 0.7, 1.4, 3.7),
    "T-Shirts": ("Menswear", -1.45, 0.75, 0.25, 63, "value", 0.6, 1.3, 3.2),
    "Trousers": ("Menswear", -1.45, 0.80, 0.22, 77, "mid_market", 0.7, 1.4, 4.0),
    "Blouses": ("Womenswear", -1.38, 1.00, 0.25, 55, "mid_market", 0.7, 1.4, 3.9),
    "Dresses": ("Womenswear", -1.55, 1.20, 0.27, 58, "mid_market", 0.7, 1.5, 4.5),
    "Tops": ("Womenswear", -1.42, 0.95, 0.23, 69, "value", 0.6, 1.3, 3.4),
}

# category-specific price elasticity of the latest measurement at product level for story SKUs
SKU_ELASTICITY = {
    "SKU-100168": ("Outerwear", -2.10, 0.85, 0.45, 18),    # men's jacket L: clearance of a broken size run
    "SKU-104277": ("Footwear", -1.90, 1.00, 0.38, 27),
    "SKU-105558": ("Drinkware", -1.30, 0.55, 0.30, 31),
    "K-1700": ("Small Appliances", -1.25, 0.65, 0.18, 28),
    "PF-220": ("Personal Care", -1.48, 0.62, 0.21, 32),
}

# clearance option profiles: recovery % of current price, sell-through %, weeks to clear, channel,
# handling cost per unit (GBP), effect on full-price sales of similar items (%)
OPTIONS = {
    "markdown": (62, 72, 8, "stores and online", 0.60, 5.5),
    "outlet": (45, 80, 10, "outlet stores", 1.10, 1.5),
    "bundle": (68, 55, 6, "online", 0.80, 3.0),
    "donate": (0, 100, 3, "charity partner", 0.90, 0.0),
    "liquidate": (18, 100, 2, "liquidation broker", 0.35, 0.5),
}
# a few categories where a different option is clearly best
OPTION_TWEAKS = {
    ("Footwear", "outlet"): (52, 85, 9, "outlet stores", 1.10, 1.5),
    ("Footwear", "markdown"): (60, 66, 8, "stores and online", 0.60, 5.8),
    ("Drinkware", "bundle"): (72, 78, 5, "online", 0.80, 3.0),
    ("Drinkware", "markdown"): (60, 70, 8, "stores and online", 0.60, 5.0),
}

ALIASES = {
    "Cookware": "kitchenware, pans, pots", "Outerwear": "jackets, coats", "Trousers": "denim, jeans",
    "Knitwear": "knits, jumpers, cardigans", "Small Appliances": "kettles, toasters, small kitchen appliances",
    "Bags": "backpacks, handbags", "Bedding": "duvets, bed linen", "Drinkware": "mugs, glasses, bottles",
    "Footwear": "shoes, boots, trainers", "Scarves": "scarfs", "Tops": "tees", "Personal Care": "personal care electricals",
    "Audio": "headphones, speakers", "Dresses": "dress", "Towels": "bath towels",
}

NOISE_CATS = ["Dresses", "Tops", "Shirts", "Audio", "Smart Home", "Lighting", "Storage", "Towels", "Jewellery",
              "Babywear", "Fragrance", "Skincare", "Haircare", "Blouses"]


def generate(g):
    r = g.rng
    D = timedelta
    products = g.master("products")
    by_cat = {}
    for p in products:
        if p["status"] in ("active", "clearance") and p["sku"].startswith("SKU-1"):
            by_cat.setdefault(p["category"], []).append(p)

    def day(n):
        return g.as_of + D(days=n)

    # ---- elasticity: every master category, a recent and an older measurement, plus story SKUs
    elasticity, n = [], 0
    for cat, (dept, pe, ie, ci, pts, *_rest) in CATS.items():
        for back, wob in ((3, 0.0), (92, 0.04)):
            n += 1
            elasticity.append({
                "elasticity_id": f"EL-{n:06d}", "category": cat, "sku": None, "measure_date": day(-back),
                "elasticity_to_price": round(pe * (1 + wob), 2), "elasticity_to_income": round(ie * (1 - wob), 2),
                "elasticity_confidence_interval": round(ci * (1 + 2 * wob), 2),
                "data_points": pts - (6 if back > 10 else 0), "last_updated": day(-back)})
    for sku, (cat, pe, ie, ci, pts) in SKU_ELASTICITY.items():
        n += 1
        elasticity.append({
            "elasticity_id": f"EL-{n:06d}", "category": cat, "sku": sku, "measure_date": day(-5),
            "elasticity_to_price": pe, "elasticity_to_income": ie, "elasticity_confidence_interval": ci,
            "data_points": pts, "last_updated": day(-5)})

    # ---- positioning and clearance options: every master category
    positioning = []
    for cat, (dept, pe, ie, ci, pts, pos, lo, hi, cann) in CATS.items():
        positioning.append({
            "category": cat, "title": f"{cat} ({ALIASES[cat]})" if cat in ALIASES else cat, "target_position": pos, "min_price_index": lo, "max_price_index": hi,
            "markdown_policy_min_depth_pct": 20 if pos != "premium" else 15,
            "markdown_policy_max_depth_pct": 50 if pos != "premium" else 40,
            "full_price_cannibalisation_pct_per_10pts": cann, "updated_at": day(-30)})
    options = []
    for cat in CATS:
        for opt, base in OPTIONS.items():
            rec, st, wk, ch, hand, fp = OPTION_TWEAKS.get((cat, opt), base)
            options.append({"category": cat, "option": opt, "recovery_pct_of_price": rec, "sell_through_pct": st,
                            "weeks_to_clear": wk, "best_channel": ch, "handling_cost_per_unit_gbp": hand,
                            "fp_cannibalisation_pct": fp})

    # ---- background promotions (story categories have none here; their rows are in seed/)
    promotions, promo_hist = [], []
    for i in range(30):
        cat = r.choice(NOISE_CATS)
        start = day(r.randint(-300, 70))
        end = start + D(days=r.randint(7, 21))
        if end < day(-10):
            status = r.choice(["completed", "completed", "completed", "cancelled"])
        elif start <= day(0):
            status = "active" if end >= day(0) else "completed"
        else:
            status = r.choice(["scheduled", "scheduled", "draft"])
        done = status in ("completed", "active")
        depth = r.choice([10, 15, 20, 25, 30])
        planned_up = round(depth * r.uniform(1.8, 2.8), 1)
        promotions.append({
            "promotion_id": f"PROMO-{1000 + i:06d}", "event_name": None, "category": cat,
            "department": CATS[cat][0], "promotion_type": r.choice(["percentage_discount", "bundle", "bogo"]),
            "discount_depth_pct": depth, "start_date": start, "end_date": end, "status": status,
            "planned_uplift_pct": planned_up, "planned_margin_gbp": round(r.uniform(2500, 9000), -1),
            "actual_uplift_pct": round(planned_up * r.uniform(0.7, 1.15), 1) if done else None,
            "actual_margin_gbp": round(r.uniform(2000, 9000), -1) if done else None,
            "supplier_funded_pct": r.choice([0, 0, 10, 20, 25, 30]),
            "cannibalisation_pct": round(r.uniform(25, 45), 1) if done else None,
            "post_promo_dip_pct": round(r.uniform(8, 22), 1) if status == "completed" else None,
            "post_promo_dip_weeks": r.choice([1, 2, 3]) if status == "completed" else None,
            "created_at": start - D(days=14), "updated_at": min(start, day(0)),
            "cancel_reason": "Demand lower than expected" if status == "cancelled" else None})
        if done:
            k = 0
            while start + D(days=7 * k) <= min(end, day(0)):
                base = r.uniform(900, 2200)
                promo_hist.append({
                    "promotion_id": f"PROMO-{1000 + i:06d}", "history_date": start + D(days=7 * k),
                    "daily_sales_gbp": round(base * (1 + planned_up / 100), 2), "units_sold": r.randint(80, 400),
                    "baseline_daily_sales_gbp": round(base, 2),
                    "uplift_gbp": round(base * planned_up / 100, 2), "margin_gbp": round(r.uniform(200, 800), 2),
                    "stock_outs": r.randint(0, 3)})
                k += 1

    # ---- background markdown events with weekly history
    markdowns, md_hist = [], []
    for i in range(36):
        cat = r.choice(NOISE_CATS)
        prod = r.choice(by_cat[cat])
        depth = r.choice([20, 30, 30, 40, 50])
        start = day(r.randint(-120, 25))
        end = start + D(days=r.randint(14, 35))
        stock = r.randint(300, 2500)
        if start > day(0):
            status, sold = r.choice(["scheduled", "draft"]), 0
        elif end < day(-3):
            status, sold = "completed", int(stock * r.uniform(0.45, 0.92))
        else:
            status, sold = "active", int(stock * r.uniform(0.15, 0.5))
        mid = f"MDE-{1000 + i:06d}"
        markdowns.append({
            "markdown_id": mid, "sku": prod["sku"], "markdown_depth_pct": depth, "start_date": start,
            "end_date": end, "status": status, "stock_at_start": stock, "units_sold": sold,
            "original_price_gbp": float(prod["retail_price_gbp"]), "review_reason": None,
            "created_at": start - D(days=7), "updated_at": min(start, day(0))})
        if sold:
            weeks = [start + D(days=7 * k) for k in range(60) if start + D(days=7 * k) <= min(end, day(0))]
            w = [1.0 / (1 + 0.35 * k) for k in range(len(weeks))]
            left = stock
            for k, (d0, wt) in enumerate(zip(weeks, w)):
                u = sold - sum(h["weekly_units_sold"] for h in md_hist if h["markdown_id"] == mid) if k == len(weeks) - 1 \
                    else int(sold * wt / sum(w))
                left -= u
                md_hist.append({"markdown_id": mid, "history_date": d0, "weekly_units_sold": u,
                                "weekly_revenue_gbp": round(u * float(prod["retail_price_gbp"]) * (1 - depth / 100), 2),
                                "remaining_stock": max(left, 0)})

    # ---- background price changes
    changes = []
    for i in range(36):
        cat = r.choice(NOISE_CATS)
        prod = r.choice(by_cat[cat])
        new = float(prod["retail_price_gbp"])
        pct = r.choice([-8, -5, -3, 3, 5, 8])
        old = round(new / (1 + pct / 100), 2)
        proposed = day(r.randint(-150, 60))
        if proposed > day(0):
            status = r.choice(["draft", "submitted", "approved", "scheduled"])
        else:
            status = r.choice(["active", "active", "active", "cancelled", "rolled_back"])
        changes.append({
            "pc_id": f"PC-{1000 + i:06d}", "sku": prod["sku"], "old_price_gbp": old, "new_price_gbp": new,
            "change_reason": r.choice(["Cost increase", "Competitive pressure", "Market alignment", "Margin recovery"]),
            "status": status, "cancel_reason": "Superseded" if status == "cancelled" else None,
            "proposed_date": proposed,
            "effective_date": proposed if status in ("active", "rolled_back") else None,
            "created_at": proposed - D(days=7), "updated_at": min(proposed, day(0)),
            "rolled_back_at": proposed + D(days=10) if status == "rolled_back" and proposed + D(days=10) <= day(0) else None})

    # ---- background price tests
    tests = []
    for i in range(5):
        cat = r.choice(NOISE_CATS)
        prod = r.choice(by_cat[cat])
        control = float(prod["retail_price_gbp"])
        chg = r.choice([-10, -5, 5, 10])
        start = day(r.randint(-90, 20))
        end = start + D(days=r.randint(28, 56))
        if end < day(-7):
            status = "completed"
            tv, cv = r.randint(500, 2000), r.randint(500, 2000)
            el = round((tv - cv) / cv / (chg / 100), 2)
        elif start > day(0):
            status, tv, cv, el = "planned", 0, 0, None
        else:
            status, tv, cv, el = "active", r.randint(100, 800), r.randint(100, 800), None
        tests.append({
            "test_id": f"PT-{1000 + i:06d}", "sku": prod["sku"], "test_price_gbp": round(control * (1 + chg / 100), 2),
            "control_price_gbp": control, "test_store_count": r.randint(5, 30), "control_store_count": r.randint(5, 30),
            "start_date": start, "end_date": end, "status": status, "test_volume": tv, "control_volume": cv,
            "elasticity_estimate": el, "created_at": start - D(days=5)})

    # ---- store promotion calendar for the background promotions
    sites = [f"ST{i:03d}" for i in range(1, 50)]
    calendar, seen = [], set()
    for p in promotions:
        if p["status"] in ("scheduled", "active", "completed") and p["end_date"] >= day(-60):
            for site in r.sample(sites, r.randint(5, 20)):
                key = (site, p["start_date"])
                if key not in seen:
                    seen.add(key)
                    calendar.append({"promotion_id": p["promotion_id"], "site_id": site, "start_date": p["start_date"],
                                     "end_date": p["end_date"], "category": p["category"],
                                     "promotion_type": p["promotion_type"]})

    return {
        "promotions": promotions, "markdown_events": markdowns, "markdown_history": md_hist,
        "price_changes": changes, "price_tests": tests, "elasticity_data": elasticity,
        "promotion_history": promo_hist, "price_positioning": positioning, "clearance_options": options,
        "promotion_calendar": calendar, "markdown_review_requests": [],
    }
