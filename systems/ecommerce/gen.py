"""E-commerce orders, delivery promises, marketing plans, and price changes."""
from datetime import datetime, timedelta


def generate(g):
    """Generate e-commerce data: orders, volumes, marketing, pricing and delivery rules."""
    r = g.rng
    fake = g.fake

    # Get products and customers from master
    products = g.master("products")[:100]  # Use first 100 products
    customers = g.master("customers")[:200]  # Use first 200 customers

    # Market regions
    markets = ["UK", "DE", "FR", "US", "NL", "BE", "ES"]
    uk_postcodes = ["SW1", "SE1", "E1", "N1", "NW1", "W1", "M1", "B1", "LS1", "EH1", "G1", "CF1"]

    ecommerce_orders = []
    order_daily_volumes = []
    market_metrics = []
    peak_marketing_plans = []
    price_changes = []
    resale_listings = []
    parcel_volumes = []
    delivery_rules = []

    # Generate delivery rules for UK postcode areas
    rule_id = 1
    for postcode_area in uk_postcodes:
        next_day_enabled = r.choice([True, True, False])  # Bias toward enabled
        delivery_rules.append({
            "rule_id": f"DLR-{rule_id:06d}",
            "postcode_area": postcode_area,
            "delivery_promise": r.choice(["next-day", "standard", "2-3 days"]),
            "next_day_enabled": next_day_enabled,
            "cutoff_date": g.as_of + timedelta(days=r.randint(7, 21)),
            "cutoff_time": r.choice(["12:00", "14:00", "16:00"]),
            "status": "active",
            "updated_at": g.as_of,
        })
        rule_id += 1

    # Generate marketing plans for peak season
    plan_id = 1
    for market in markets[:3]:  # Plans for UK, DE, FR
        for i in range(r.randint(2, 3)):
            start = g.as_of + timedelta(days=r.randint(30, 90))
            plan = {
                "plan_id": f"MKT-{plan_id:06d}",
                "region": market,
                "campaign_name": f"{market} Peak {g.as_of.year} - Campaign {i+1}",
                "start_date": start,
                "end_date": start + timedelta(days=r.randint(14, 42)),
                "budget_gbp": r.randint(50000, 500000),
                "expected_uplift_pct": r.uniform(5, 30),
                "channels": r.choice(["social,display,email", "display,email", "social,email,seo"]),
                "target_segment": r.choice(["new_customers", "loyal", "lapsed", "high_value"]),
                "status": r.choice(["planned", "active"]),
            }
            peak_marketing_plans.append(plan)
            plan_id += 1

    # Generate price changes for top products
    price_change_id = 1
    for i, prod in enumerate(products[:40]):
        for _ in range(r.randint(1, 3)):
            date = g.date_between(90, 1)
            old_price = float(prod.get("retail_price_gbp", 29.99))
            change_pct = r.uniform(-25, 15)
            new_price = old_price * (1 + change_pct / 100)
            price_changes.append({
                "sku": prod["sku"],
                "changed_at": date,
                "old_price_gbp": round(old_price, 2),
                "new_price_gbp": round(new_price, 2),
                "change_pct": round(change_pct, 1),
                "reason": r.choice(["Promotion", "Seasonal", "Competitor match", "Clearance", "New season"]),
            })
            price_change_id += 1

    # Generate resale listings for some products
    listing_id = 1
    for prod in products[:30]:
        for _ in range(r.randint(1, 2)):
            new_price = float(prod.get("retail_price_gbp", 29.99))
            discount = r.randint(10, 60)
            resale_price = new_price * (1 - discount / 100)
            resale_listings.append({
                "listing_id": f"RSL-{listing_id:06d}",
                "sku": prod["sku"],
                "new_price_gbp": round(new_price, 2),
                "resale_price_gbp": round(resale_price, 2),
                "discount_pct": discount,
                "condition": r.choice(["like_new", "good", "fair", "poor"]),
                "listed_date": g.date_between(60, 1),
                "sold": r.choice([True, False, False]),
                "views": r.randint(5, 500),
            })
            listing_id += 1

    # Generate market metrics (conversion, return rates)
    for market in markets:
        is_cross_border = market != "UK"
        base_conversion = 2.5 if not is_cross_border else 1.5
        base_return = 15 if not is_cross_border else 12
        market_metrics.append({
            "region": market,
            "conversion_rate_pct": round(base_conversion + r.uniform(-0.5, 0.5), 2),
            "return_rate_pct": round(base_return + r.uniform(-2, 2), 1),
            "avg_basket_gbp": round(45 + r.uniform(-10, 20), 2) if not is_cross_border else round(62, 2),
            "is_cross_border": is_cross_border,
            "measured_at": g.as_of,
        })

    # Generate daily order volumes
    for market in markets:
        base_orders = 2000 if market == "UK" else r.randint(200, 600)
        for i in range(60):  # Last 60 days
            date = g.days_ago(i)
            daily_orders = int(base_orders * r.uniform(0.8, 1.2))
            daily_units = int(daily_orders * r.uniform(1.2, 1.8))
            daily_value = daily_orders * r.uniform(40, 80)
            order_daily_volumes.append({
                "region": market,
                "date": date,
                "units": daily_units,
                "orders": daily_orders,
                "value_gbp": round(daily_value, 2),
                "avg_basket_gbp": round(daily_value / daily_orders, 2),
            })

    # Generate ecommerce orders (last 120 days)
    order_id = 1
    for i in range(90):
        days_ago = i
        date = g.days_ago(days_ago)

        # Determine market
        market = r.choices(markets, [50, 15, 15, 10, 5, 3, 2])[0]
        postcode_area = r.choice(uk_postcodes) if market == "UK" else None
        region = market

        # Generate 1-5 orders per day per market
        for _ in range(r.randint(1, 5)):
            customer = r.choice(customers)
            product = r.choice(products)
            units = r.randint(1, 3)
            basket_value = units * float(product.get("retail_price_gbp", 29.99)) * r.uniform(0.8, 1.1)

            # Cross-border orders have average £62 basket
            if region != "UK":
                basket_value = r.gauss(62, 10)

            status = r.choices(["delivered", "returned", "cancelled"], [75, 18, 7])[0]
            returned = status == "returned"
            delivery_date = date + timedelta(days=r.randint(1, 7)) if status in ["delivered", "returned"] else None

            ecommerce_orders.append({
                "order_id": f"ECO-{date.year}-{order_id:07d}",
                "customer_id": customer["customer_id"],
                "sku": product["sku"],
                "order_date": date,
                "channel": r.choice(["web", "app", "marketplace"]),
                "region": region,
                "postcode_area": postcode_area,
                "basket_value_gbp": round(max(basket_value, 10), 2),
                "units": units,
                "delivery_promise": r.choice(["next-day", "standard", "2-3 days"]),
                "status": status,
                "returned": returned,
                "delivery_date": delivery_date,
                "updated_at": date,
            })
            order_id += 1

    # Generate parcel volumes by destination
    for country in ["GB", "DE", "FR", "US", "NL", "BE", "ES"]:
        for i in range(60):
            date = g.days_ago(i)
            base_parcels = 5000 if country == "GB" else r.randint(200, 1000)
            daily_parcels = int(base_parcels * r.uniform(0.8, 1.2))
            daily_value = daily_parcels * r.uniform(30, 80)
            parcel_volumes.append({
                "destination_country": country,
                "date": date,
                "parcels": daily_parcels,
                "value_gbp": round(daily_value, 2),
                "avg_parcel_value_gbp": round(daily_value / daily_parcels, 2),
            })

    return {
        "ecommerce_orders": ecommerce_orders,
        "order_daily_volumes": order_daily_volumes,
        "market_metrics": market_metrics,
        "peak_marketing_plans": peak_marketing_plans,
        "price_changes": price_changes,
        "resale_listings": resale_listings,
        "parcel_volumes": parcel_volumes,
        "delivery_rules": delivery_rules,
    }
