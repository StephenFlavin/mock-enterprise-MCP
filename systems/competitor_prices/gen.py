"""Competitor pricing and promotion data: weekly prices for 200+ competitor SKUs across 6 competitors."""
from datetime import timedelta


def generate(g):
    r = g.rng

    # Define competitor roster
    competitors_data = [
        {"competitor_id": "CMPD-001", "name": "HomeShop Direct", "format": "online", "country": "GB", "region": "UK", "data_source": "web_scrape"},
        {"competitor_id": "CMPD-002", "name": "John Lewis", "format": "high_street", "country": "GB", "region": "UK", "data_source": "manual"},
        {"competitor_id": "CMPD-003", "name": "Carrefour", "format": "hypermarket", "country": "FR", "region": "EU Central", "data_source": "agency"},
        {"competitor_id": "CMPD-004", "name": "Mitre10", "format": "online", "country": "AU", "region": "Asia-Pacific", "data_source": "web_scrape"},
        {"competitor_id": "CMPD-005", "name": "Argos", "format": "online", "country": "GB", "region": "UK", "data_source": "manual"},
        {"competitor_id": "CMPD-006", "name": "Currys", "format": "electronics", "country": "GB", "region": "UK", "data_source": "web_scrape"},
    ]

    competitors = [
        {**cd, "last_updated": g.as_of, "coverage_status": "active"}
        for cd in competitors_data
    ]

    # Product categories and sample competitor products
    product_categories = [
        ("Insulated bottles", ["Vacuum flask 750ml", "Thermal bottle 600ml", "Insulated water bottle"]),
        ("Kettles", ["1.7L electric kettle", "2.0L kettle", "Stainless steel kettle"]),
        ("Small appliances", ["Toaster 2-slice", "Blender", "Coffee maker"]),
        ("Men's jackets", ["Leather jacket", "Wool coat", "Puffer jacket"]),
    ]

    competitor_products = []
    competitor_product_map = {}  # Track products for price/promo generation

    product_id_counter = 0
    for category, products in product_categories:
        for product_name in products:
            for comp in competitors:
                product_id_counter += 1
                cp_id = f"CMPD-{comp['competitor_id'].split('-')[1]}-{product_id_counter:04d}"

                # Try to match to our SKU
                matched_sku = None
                matched = False
                if "kettle" in product_name.lower():
                    matched_sku = "K-1700"
                    matched = True
                elif "bottle" in product_name.lower():
                    matched_sku = "PF-220"
                    matched = True

                competitor_products.append({
                    "competitor_product_id": cp_id,
                    "competitor_id": comp["competitor_id"],
                    "sku": matched_sku,
                    "their_sku": f"{comp['competitor_id'].split('-')[1]}-SKU-{product_id_counter:05d}",
                    "their_name": product_name,
                    "category": category,
                    "brand": r.choice(["Own brand", "Premium", "Value"]),
                    "features": r.choice([
                        "Durable, keeps drinks cold for 24 hours, double-walled insulated",
                        "Lightweight and portable",
                        "BPA-free materials, food-grade, insulated",
                        "Easy to clean, ergonomic handle",
                        "Eco-friendly design, sustainable materials",
                        "Thermal insulation technology",
                        "Premium insulation, leak-proof design",
                    ]),
                    "matched_product": matched,
                })

                competitor_product_map[cp_id] = {
                    "competitor_id": comp["competitor_id"],
                    "category": category,
                    "sku": matched_sku,
                }

    # Generate weekly price history for last 90 days
    competitor_prices = []
    price_counter = 0

    for cp in competitor_products:
        cp_id = cp["competitor_product_id"]
        comp_id = cp["competitor_id"]

        # Base price varies by category and competitor
        base_price = r.uniform(15, 150)
        if "kettle" in cp["category"].lower():
            base_price = r.uniform(20, 60)
        elif "bottle" in cp["category"].lower():
            base_price = r.uniform(25, 80)
        elif "jacket" in cp["category"].lower():
            base_price = r.uniform(50, 200)

        # Generate weekly prices for last 13 weeks
        for week_offset in range(13, 0, -1):
            price_date = g.weeks(1)[0] - timedelta(weeks=week_offset)

            # Add some price variation week to week
            price = base_price + r.gauss(0, base_price * 0.05)
            price = max(price * 0.7, round(price, 2))  # Ensure positive, round

            promotion_type = "none"
            discount_pct = 0.0
            promotion_desc = ""
            in_clearance = False
            data_quality = r.choices(["confirmed", "estimated"], [90, 10])[0]

            # Occasional promotions (20% chance any week)
            if r.random() < 0.2:
                promo_choice = r.choice(["percentage", "clearance"])
                if promo_choice == "percentage":
                    promotion_type = "percentage"
                    discount_pct = r.choice([10, 15, 20, 25, 30])
                    price = price * (1 - discount_pct / 100)
                    promotion_desc = f"{discount_pct}% off"
                else:
                    in_clearance = True
                    promotion_type = "clearance"
                    discount_pct = r.choice([30, 40, 50, 60])
                    price = price * (1 - discount_pct / 100)
                    promotion_desc = "Clearance sale"

            price_counter += 1
            competitor_prices.append({
                "competitor_product_id": cp_id,
                "competitor_id": comp_id,
                "sku": cp["sku"],
                "price_date": price_date,
                "price_gbp": round(price, 2),
                "promotion_type": promotion_type,
                "discount_pct": discount_pct,
                "promotion_desc": promotion_desc,
                "in_clearance": in_clearance,
                "data_quality": data_quality,
            })

    # Generate promotions data
    competitor_promotions = []
    promo_counter = 0

    for cp in competitor_products:
        cp_id = cp["competitor_product_id"]
        comp_id = cp["competitor_id"]

        # Random promotions over the 90-day window
        if r.random() < 0.3:  # 30% of products have at least one promotion
            promo_start = g.as_of - timedelta(days=r.randint(5, 80))
            duration = r.randint(7, 30)
            promo_end = promo_start + timedelta(days=duration)

            promo_type = r.choice(["percentage", "clearance", "seasonal", "bundle"])
            discount_pct = 0
            discount_gbp = 0

            if promo_type == "percentage":
                discount_pct = r.choice([10, 15, 20, 25])
            elif promo_type == "clearance":
                discount_pct = r.choice([30, 50, 60])

            promo_counter += 1
            competitor_promotions.append({
                "promotion_id": f"PRMO-{promo_counter:06d}",
                "competitor_id": comp_id,
                "competitor_product_id": cp_id,
                "sku": cp["sku"],
                "promo_start": promo_start,
                "promo_end": promo_end,
                "promo_type": promo_type,
                "discount_pct": discount_pct,
                "discount_gbp": discount_gbp,
                "promo_description": f"{promo_type.capitalize()} promotion",
                "duration_days": duration,
                "status": "completed" if promo_end < g.as_of else ("active" if promo_start <= g.as_of else "planned"),
            })

    # Generate competitor stores (UK stores only for simplicity)
    competitor_stores = []
    store_counter = 0

    # Define UK regions and major stores
    uk_stores_per_competitor = {
        "CMPD-001": 0,  # HomeShop Direct - online only
        "CMPD-002": 8,  # John Lewis
        "CMPD-003": 0,  # Carrefour - EU
        "CMPD-004": 0,  # Mitre10 - Asia-Pacific
        "CMPD-005": 15,  # Argos
        "CMPD-006": 12,  # Currys
    }

    uk_store_locations = ["ST001", "ST214", "ST002", "ST003", "ST004", "ST005", "ST010", "ST050",
                          "ST100", "ST150", "ST200", "ST210", "ST212", "ST215", "ST220"]

    for comp in competitors:
        comp_id = comp["competitor_id"]
        num_stores = uk_stores_per_competitor.get(comp_id, 0)

        for i in range(num_stores):
            store_counter += 1
            site_id = uk_store_locations[i % len(uk_store_locations)]

            # Some stores opened/closed recently
            opening_date = g.as_of - timedelta(days=r.randint(30, 1000))
            closed_date = None
            status = "open"

            if r.random() < 0.1:  # 10% of stores closed
                closed_date = g.as_of - timedelta(days=r.randint(1, 100))
                status = "closed"

            competitor_stores.append({
                "store_id": f"CSTD-{comp_id.split('-')[1]}-{store_counter:04d}",
                "competitor_id": comp_id,
                "site_id": site_id,  # Our store location
                "opening_date": opening_date,
                "closing_date": closed_date,
                "status": status,
                "store_format": comp["format"],
            })

    # Generate competitor returns policies
    competitor_returns_policies = []
    for comp in competitors:
        comp_id = comp["competitor_id"]

        # Different policies for different competitors
        if comp["name"] in ["John Lewis", "Carrefour"]:
            returns_free = True
            restocking_fee_pct = 0
            return_window_days = 90
        elif comp["name"] == "Argos":
            returns_free = False
            restocking_fee_pct = 3
            return_window_days = 60
        elif comp["name"] in ["HomeShop Direct", "Currys"]:
            returns_free = False
            restocking_fee_pct = 5
            return_window_days = 30
        else:
            returns_free = r.choice([True, False])
            restocking_fee_pct = r.choice([0, 3, 5, 8])
            return_window_days = r.choice([30, 60, 90])

        competitor_returns_policies.append({
            "policy_id": f"RPOL-{len(competitor_returns_policies) + 1:02d}",
            "competitor_id": comp_id,
            "competitor_name": comp["name"],
            "returns_free": returns_free,
            "restocking_fee_gbp": 0 if returns_free else r.choice([2.99, 3.99, 4.99, 5.99]),
            "restocking_fee_pct": restocking_fee_pct,
            "return_window_days": return_window_days,
            "policy_description": f"{'Free' if returns_free else 'Charged'} returns within {return_window_days} days",
            "last_updated": g.as_of,
        })

    # Generate competitor delivery practices
    competitor_delivery_practices = []
    for comp in competitors:
        comp_id = comp["competitor_id"]

        # Delivery zones and practices vary
        delivery_zones = r.choice([
            "UK mainland only",
            "UK + Scotland",
            "UK + EU",
            "Worldwide",
        ])

        min_order_gbp = r.choice([0, 5, 10, 20, 25])
        free_delivery_threshold = r.choice([15, 20, 25, 30, 40, 50])

        competitor_delivery_practices.append({
            "practice_id": f"DLVR-{len(competitor_delivery_practices) + 1:02d}",
            "competitor_id": comp_id,
            "competitor_name": comp["name"],
            "delivery_zones": delivery_zones,
            "min_order_gbp": min_order_gbp,
            "free_delivery_threshold_gbp": free_delivery_threshold,
            "standard_delivery_days": r.choice([3, 5, 7]),
            "express_delivery_available": r.choice([True, False]),
            "saturday_delivery": r.choice([True, False]),
            "de_minimis_threshold_eur": r.choice([150, 200, 250, 300]),
            "vat_reverse_charge": r.choice([True, False]),
            "last_updated": g.as_of,
        })

    return {
        "competitors": competitors,
        "competitor_products": competitor_products,
        "competitor_prices": competitor_prices,
        "competitor_promotions": competitor_promotions,
        "competitor_stores": competitor_stores,
        "competitor_returns_policies": competitor_returns_policies,
        "competitor_delivery_practices": competitor_delivery_practices,
    }
