"""Generate pricing data: promotions, markdowns, price changes, elasticity."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    categories = ["kitchenware", "apparel", "home", "small_appliances", "garden", "outdoor"]
    skus = [prod["sku"] for prod in g.master("products")[:100]]

    promotions, markdown_events, price_changes, price_tests = [], [], [], []
    elasticity_data, promotion_history, markdown_history = [], [], []
    price_positioning, promotion_calendar = [], []

    # Helper to generate dates between days_ago and days_future
    def random_date(days_ago, days_future):
        offset = r.randint(-days_ago, days_future)
        return g.as_of + timedelta(days=offset)

    # Promotions: 10-15 active, completed, and planned ones
    for i in range(20):
        promo_id = f"PROMO-{1000 + i:06d}"
        category = r.choice(categories)
        start = random_date(60, 90)
        duration = r.randint(7, 21)
        end = start + timedelta(days=duration)

        days_past = (end - g.as_of).days
        if days_past < -14:
            status = r.choice(["completed", "cancelled"])
            actual_uplift = r.gauss(18, 8) if status == "completed" else r.gauss(5, 10)
            actual_margin = r.uniform(2000, 8000) if status == "completed" else r.uniform(500, 2000)
        elif days_past < 0:
            status = "active"
            actual_uplift = r.gauss(16, 6)
            actual_margin = r.uniform(3000, 7000)
        else:
            status = r.choice(["scheduled", "draft"])
            actual_uplift = None
            actual_margin = None

        planned_margin = r.uniform(2000, 8000)
        discount = r.choice([10, 15, 20, 25, 30])

        promotions.append({
            "promotion_id": promo_id,
            "category": category,
            "promotion_type": r.choice(["percentage_discount", "bundle", "bogo"]),
            "discount_depth_pct": discount,
            "start_date": start,
            "end_date": end,
            "status": status,
            "planned_uplift_pct": r.uniform(8, 25),
            "planned_margin_gbp": planned_margin,
            "actual_uplift_pct": actual_uplift,
            "actual_margin_gbp": actual_margin,
            "supplier_funded_pct": r.uniform(0, 50),
            "created_at": start - timedelta(days=7),
            "updated_at": start,
            "cancel_reason": "Demand lower than expected" if status == "cancelled" else None,
        })

    # Markdown events: 15-20
    for i in range(20):
        markdown_id = f"MDE-{1000 + i:06d}"
        sku = r.choice(skus)
        category = r.choice(categories)
        start = random_date(90, 60)
        duration = r.randint(7, 28)
        end = start + timedelta(days=duration)

        price = r.uniform(20, 120)
        cost = price * r.uniform(0.35, 0.55)
        stock = r.randint(200, 2000)

        days_past = (end - g.as_of).days
        if days_past < -7:
            status = "completed"
            units_sold = int(stock * r.uniform(0.6, 0.95))
        elif days_past < 0:
            status = "active"
            units_sold = int(stock * r.uniform(0.3, 0.7))
        else:
            status = r.choice(["scheduled", "draft"])
            units_sold = 0

        markdown_depth = r.choice([20, 30, 40, 50])
        markdown_price = price * (1 - markdown_depth / 100)
        margin = (markdown_price - cost) * units_sold if units_sold > 0 else 0

        markdown_events.append({
            "markdown_id": markdown_id,
            "sku": sku,
            "category": category,
            "markdown_depth_pct": markdown_depth,
            "start_date": start,
            "end_date": end,
            "status": status,
            "stock_at_start": stock,
            "units_sold": units_sold,
            "original_price_gbp": round(price, 2),
            "markdown_price_gbp": round(markdown_price, 2),
            "cost_gbp": round(cost, 2),
            "margin_gbp": round(margin, 2),
            "created_at": start - timedelta(days=3),
            "updated_at": start,
        })

    # Price changes: 10-15
    for i in range(15):
        pc_id = f"PC-{1000 + i:06d}"
        sku = r.choice(skus)
        category = r.choice(categories)
        old_price = r.uniform(15, 100)
        price_change = r.choice([-8, -5, -2, 2, 5, 8, 12])
        new_price = old_price * (1 + price_change / 100)

        proposed = random_date(30, 60)

        # Mix of statuses
        if r.random() < 0.3:
            status = r.choice(["draft", "submitted"])
            effective_date = None
        elif r.random() < 0.2:
            status = "cancelled"
            effective_date = None
        else:
            status = r.choice(["approved", "scheduled", "active"])
            effective_date = proposed if proposed <= g.as_of else None

        price_changes.append({
            "pc_id": pc_id,
            "sku": sku,
            "category": category,
            "old_price_gbp": round(old_price, 2),
            "new_price_gbp": round(new_price, 2),
            "price_change_pct": round(price_change, 1),
            "change_reason": r.choice(["Cost increase", "Promotional", "Market alignment", "Margin recovery"]),
            "status": status,
            "proposed_date": proposed,
            "effective_date": effective_date,
            "created_at": proposed - timedelta(days=5),
            "updated_at": proposed,
            "rolled_back_at": None,
        })

    # Price tests: 5-8
    for i in range(8):
        test_id = f"PT-{1000 + i:06d}"
        sku = r.choice(skus)

        control_price = r.uniform(15, 100)
        test_price_change = r.choice([-20, -15, -10, 10, 15, 20])
        test_price = control_price * (1 + test_price_change / 100)

        start = random_date(60, 30)
        duration = r.randint(21, 56)
        end = start + timedelta(days=duration)

        days_past = (end - g.as_of).days
        if days_past < -7:
            status = "completed"
            test_vol = r.randint(500, 2000)
            control_vol = r.randint(500, 2000)
            elasticity = (test_vol - control_vol) / control_vol / (test_price_change / 100) if control_vol > 0 else -1.5
        else:
            status = r.choice(["planned", "active"])
            test_vol = r.randint(100, 800) if status == "active" else 0
            control_vol = r.randint(100, 800) if status == "active" else 0
            elasticity = None

        price_tests.append({
            "test_id": test_id,
            "sku": sku,
            "test_price_gbp": round(test_price, 2),
            "control_price_gbp": round(control_price, 2),
            "test_store_count": r.randint(5, 30),
            "control_store_count": r.randint(5, 30),
            "start_date": start,
            "end_date": end,
            "status": status,
            "test_volume": test_vol,
            "control_volume": control_vol,
            "elasticity_estimate": round(elasticity, 2) if elasticity else None,
            "created_at": start - timedelta(days=5),
        })

    # Elasticity data: one per category
    for cat in categories:
        elasticity_data.append({
            "category": cat,
            "sku": None,
            "measure_date": g.as_of - timedelta(days=7),
            "elasticity_to_price": round(r.gauss(-1.3, 0.3), 2),
            "elasticity_to_income": round(r.gauss(-0.7, 0.2), 2),
            "elasticity_confidence_interval": round(r.uniform(0.15, 0.35), 2),
            "data_points": r.randint(30, 100),
            "last_updated": g.as_of - timedelta(days=7),
        })

    # Promotion history: daily records for active/recent promotions
    for promo in promotions[:10]:
        if promo["status"] in ("active", "completed"):
            for day_offset in range(0, (promo["end_date"] - promo["start_date"]).days, 7):
                hist_date = promo["start_date"] + timedelta(days=day_offset)
                if hist_date > g.as_of:
                    break
                promotion_history.append({
                    "promotion_id": promo["promotion_id"],
                    "history_date": hist_date,
                    "daily_sales_gbp": round(r.uniform(800, 3000), 2),
                    "units_sold": r.randint(80, 400),
                    "baseline_daily_sales_gbp": round(r.uniform(500, 1500), 2),
                    "uplift_gbp": round(r.uniform(300, 1500), 2),
                    "margin_gbp": round(r.uniform(200, 800), 2),
                    "stock_outs": r.randint(0, 3),
                })

    # Markdown history
    for md in markdown_events[:10]:
        if md["status"] in ("active", "completed"):
            for day_offset in range(0, (md["end_date"] - md["start_date"]).days, 2):
                hist_date = md["start_date"] + timedelta(days=day_offset)
                if hist_date > g.as_of:
                    break
                sold_today = r.randint(10, 100)
                markdown_history.append({
                    "markdown_id": md["markdown_id"],
                    "history_date": hist_date,
                    "daily_units_sold": sold_today,
                    "daily_revenue_gbp": round(sold_today * md["markdown_price_gbp"], 2),
                    "remaining_stock": max(0, md["stock_at_start"] - sold_today),
                    "cumulative_margin_gbp": round(sold_today * (md["markdown_price_gbp"] - md["cost_gbp"]), 2),
                })

    # Price positioning: one per category
    for cat in categories:
        price_positioning.append({
            "category": cat,
            "target_position": r.choice(["premium", "mid_market", "value"]),
            "min_price_pct_of_high": r.uniform(0.4, 0.6),
            "max_price_pct_of_high": r.uniform(0.8, 1.2),
            "markdown_policy_min_depth_pct": r.randint(15, 25),
            "markdown_policy_max_depth_pct": r.randint(40, 60),
            "updated_at": g.as_of - timedelta(days=30),
        })

    # Promotion calendar: current and upcoming
    sites = [f"ST{i:03d}" for i in range(1, 50)]
    seen_keys = set()
    for promo in promotions[:15]:
        if promo["start_date"] <= g.as_of + timedelta(days=90):
            for site in r.sample(sites, r.randint(5, 20)):
                key = (site, str(promo["start_date"]))
                if key not in seen_keys:
                    promotion_calendar.append({
                        "promotion_id": promo["promotion_id"],
                        "site_id": site,
                        "start_date": promo["start_date"],
                        "end_date": promo["end_date"],
                        "category": promo["category"],
                        "promotion_type": promo["promotion_type"],
                    })
                    seen_keys.add(key)

    return {
        "promotions": promotions,
        "markdown_events": markdown_events,
        "price_changes": price_changes,
        "price_tests": price_tests,
        "elasticity_data": elasticity_data,
        "promotion_history": promotion_history,
        "markdown_history": markdown_history,
        "price_positioning": price_positioning,
        "promotion_calendar": promotion_calendar,
    }
