"""Generate trend data: search interest, social mentions, sales trends, commodity prices and forecasts."""
from datetime import datetime, timedelta, time


def generate(g):
    r = g.rng
    fake = g.fake

    # Trends
    trends = [
        {"trend_id": "TRD-000001", "name": "Quiet Luxury", "category": "Womenswear", "region": "UK",
         "lifecycle_stage": "declining", "started_date": "2023-06-15", "peak_date": "2026-03-01",
         "forecast_end_date": "2027-06-01", "description": "Premium understated aesthetics and quality-focused basics", "updated_at": g.as_of},
        {"trend_id": "TRD-000002", "name": "Oversized Outerwear", "category": "Womenswear", "region": "UK",
         "lifecycle_stage": "peak", "started_date": "2024-09-01", "peak_date": "2026-11-01",
         "forecast_end_date": "2027-06-01", "description": "Oversized silhouettes in coats and jackets", "updated_at": g.as_of},
        {"trend_id": "TRD-000003", "name": "Wellness & Recovery", "category": "Home", "region": "UK",
         "lifecycle_stage": "growing", "started_date": "2025-01-01", "peak_date": "2027-06-01",
         "forecast_end_date": "2028-01-01", "description": "Health-focused home products and wellness categories", "updated_at": g.as_of},
        {"trend_id": "TRD-000004", "name": "Sustainable Materials", "category": "General", "region": "UK",
         "lifecycle_stage": "growing", "started_date": "2022-06-01", "peak_date": "2028-01-01",
         "forecast_end_date": "2030-01-01", "description": "Recycled and eco-friendly materials", "updated_at": g.as_of},
    ]

    # Market search interest
    search_interest = []
    terms = ["quiet luxury", "oversized outerwear", "wellness recovery", "sustainable fashion"]
    markets = ["UK", "US", "Germany"]

    for term in terms:
        for market in markets:
            for week_ago in range(52, -1, -1):
                week_end = g.as_of - timedelta(days=week_ago * 7)
                # Create a trend - declining for quiet luxury, growing for oversized, etc
                if "quiet" in term:
                    base = max(20, 80 - (week_ago // 4))  # declining
                elif "oversized" in term:
                    base = min(80, 30 + (week_ago // 4))  # growing/peak
                elif "wellness" in term:
                    base = min(85, 20 + (week_ago // 3))  # growing
                else:
                    base = 50  # sustainable - steady

                vol = max(10, min(95, base + r.randint(-15, 15)))
                direction = "rising" if week_ago > 0 and vol > (base + r.randint(-10, 10)) else "falling" if week_ago > 0 and vol < (base - r.randint(-10, 10)) else "stable"

                search_interest.append({
                    "term": term, "market": market, "week_ending": week_end,
                    "search_volume": vol, "trend_direction": direction, "updated_at": g.as_of
                })

    # Social mentions
    social_mentions = []
    for term in ["oversized outerwear", "wellness recovery", "quiet luxury", "sustainable fashion"]:
        for market in markets:
            for week_ago in range(26, -1, -1):
                week_end = g.as_of - timedelta(days=week_ago * 7)
                if "oversized" in term:
                    mention_count = r.randint(800, 2500)
                    sentiment = r.randint(55, 75)
                elif "wellness" in term:
                    mention_count = r.randint(500, 1500)
                    sentiment = r.randint(60, 80)
                elif "quiet" in term:
                    mention_count = r.randint(300, 1000)
                    sentiment = r.randint(50, 70)
                else:
                    mention_count = r.randint(400, 1200)
                    sentiment = r.randint(65, 85)

                social_mentions.append({
                    "term": term, "market": market, "week_ending": week_end,
                    "mention_count": mention_count, "sentiment_pct_positive": sentiment, "updated_at": g.as_of
                })

    # SKU sales trends
    sku_sales_trends = []
    test_skus = ["K-1700", "PF-220"]  # Kettle and fan from the brief
    for sku in test_skus:
        for week_ago in range(26, -1, -1):
            week_end = g.as_of - timedelta(days=week_ago * 7)
            # K-1700 declining for 8 weeks
            if sku == "K-1700" and week_ago <= 8:
                units = r.randint(150, 250)
                rating = r.uniform(3.2, 3.8)
                return_rate = r.uniform(5.5, 8.5)
            elif sku == "K-1700":
                units = r.randint(280, 380)
                rating = r.uniform(4.0, 4.5)
                return_rate = r.uniform(2.0, 3.5)
            else:
                units = r.randint(100, 200)
                rating = r.uniform(4.0, 4.7)
                return_rate = r.uniform(1.5, 2.5)

            revenue = units * r.uniform(18, 35)
            sku_sales_trends.append({
                "sku": sku, "week_ending": week_end, "units_sold": units,
                "revenue_gbp": round(revenue, 2), "avg_rating": round(rating, 1),
                "return_rate_pct": round(return_rate, 1), "updated_at": g.as_of
            })

    # Commodity prices
    commodity_prices = []
    commodities = ["cotton", "polyester", "steel", "nickel"]
    for commodity in commodities:
        base_price = {"cotton": 2.5, "polyester": 1.8, "steel": 450, "nickel": 8.5}.get(commodity, 2.0)
        for days_ago in range(365, -1, -1):
            date = g.as_of - timedelta(days=days_ago)
            # Add some trend - cotton and polyester rising, steel stable
            if commodity in ["cotton", "polyester"]:
                price = base_price * (1 + (days_ago / 365) * 0.15)  # 15% rise over year
            else:
                price = base_price * (0.97 + (days_ago / 365) * 0.06)  # stable to slight rise

            price += r.uniform(-price * 0.05, price * 0.05)  # ±5% noise

            commodity_prices.append({
                "commodity": commodity, "date": date, "price_per_unit": round(price, 2),
                "currency": "GBP" if commodity == "steel" else "USD",  # Simplified
                "source": "Market data", "updated_at": g.as_of
            })

    # Silhouette cycles
    silhouette_cycles = [
        {"silhouette_id": "SIL-000001", "silhouette_name": "Oversized", "category": "Outerwear",
         "first_peak_year": 2008, "first_cycle_duration_months": 18,
         "second_peak_year": 2026, "second_cycle_duration_months": 14, "notes": "90s return; oversized silhouettes popular"},
        {"silhouette_id": "SIL-000002", "silhouette_name": "Fitted", "category": "General",
         "first_peak_year": 2015, "first_cycle_duration_months": 24,
         "second_peak_year": 0, "second_cycle_duration_months": 0, "notes": "Body-conscious silhouettes"},
        {"silhouette_id": "SIL-000003", "silhouette_name": "Maxi", "category": "Womenswear",
         "first_peak_year": 2012, "first_cycle_duration_months": 20,
         "second_peak_year": 2024, "second_cycle_duration_months": 18, "notes": "Long flowing silhouettes"},
    ]

    # Trend adoption
    trend_adoption = [
        {"trend_id": "TRD-000001", "market": "UK", "adoption_start_date": "2023-06-15", "adoption_stage": "mainstream", "market_share_pct": 18.5},
        {"trend_id": "TRD-000001", "market": "US", "adoption_start_date": "2023-09-01", "adoption_stage": "mainstream", "market_share_pct": 22.3},
        {"trend_id": "TRD-000001", "market": "Germany", "adoption_start_date": "2023-08-15", "adoption_stage": "mainstream", "market_share_pct": 19.7},
        {"trend_id": "TRD-000002", "market": "UK", "adoption_start_date": "2024-09-01", "adoption_stage": "mainstream", "market_share_pct": 28.9},
        {"trend_id": "TRD-000002", "market": "US", "adoption_start_date": "2024-08-15", "adoption_stage": "early_adopter", "market_share_pct": 15.2},
        {"trend_id": "TRD-000002", "market": "Germany", "adoption_start_date": "2024-10-01", "adoption_stage": "early_adopter", "market_share_pct": 12.1},
        {"trend_id": "TRD-000003", "market": "UK", "adoption_start_date": "2025-01-15", "adoption_stage": "early_adopter", "market_share_pct": 8.3},
        {"trend_id": "TRD-000003", "market": "US", "adoption_start_date": "2025-02-01", "adoption_stage": "early_adopter", "market_share_pct": 6.1},
    ]

    # Product launches
    product_launches = [
        {"launch_id": "LCH-000001", "sku": "SKU-999001", "competitor_id": "Zara", "trend_id": "TRD-000002",
         "launch_date": "2025-08-15", "category": "Womenswear", "success_metric": "success", "failure_reason": ""},
        {"launch_id": "LCH-000002", "sku": "SKU-999002", "competitor_id": "H&M", "trend_id": "TRD-000001",
         "launch_date": "2025-06-01", "category": "Womenswear", "success_metric": "failure", "failure_reason": "Market saturation; timing too late"},
        {"launch_id": "LCH-000003", "sku": "SKU-999003", "competitor_id": "COS", "trend_id": "TRD-000003",
         "launch_date": "2025-11-01", "category": "Home", "success_metric": "moderate", "failure_reason": ""},
        {"launch_id": "LCH-000004", "sku": "SKU-999004", "competitor_id": "Uniqlo", "trend_id": "TRD-000002",
         "launch_date": "2026-01-15", "category": "Womenswear", "success_metric": "success", "failure_reason": ""},
    ]

    # Competitor risk disclosures
    competitor_risk_disclosures = [
        {"disclosure_id": "CRD-000001", "competitor_id": "Inditex (Zara parent)", "risk_type": "geopolitical",
         "disclosure_date": "2026-08-01", "risk_description": "Supply chain exposure to Middle East tensions",
         "adjustment_action": "Diversifying sourcing away from high-risk regions", "impact_level": "high"},
        {"disclosure_id": "CRD-000002", "competitor_id": "H&M", "risk_type": "climate",
         "disclosure_date": "2026-09-15", "risk_description": "Water scarcity in key cotton-producing regions",
         "adjustment_action": "Shifting to synthetic and recycled materials", "impact_level": "medium"},
        {"disclosure_id": "CRD-000003", "competitor_id": "Fast Retailing (Uniqlo)", "risk_type": "regulatory",
         "disclosure_date": "2026-07-20", "risk_description": "EU CSDDD compliance requirements",
         "adjustment_action": "Enhanced supply chain transparency and audit programs", "impact_level": "high"},
        {"disclosure_id": "CRD-000004", "competitor_id": "Kering (Gucci parent)", "risk_type": "supply_chain",
         "disclosure_date": "2026-08-30", "risk_description": "Luxury leather supply tightness",
         "adjustment_action": "Investing in lab-grown leather R&D", "impact_level": "medium"},
    ]

    # Innovative materials
    innovative_materials = [
        {"material_id": "MTL-000001", "material_name": "Recycled Polyester", "material_category": "Sustainable",
         "readiness_level": "mature", "primary_use": "General apparel", "supplier_examples": "Repreve, Avantem",
         "cost_vs_standard_pct": -2.5, "performance_benefits": "Reduced carbon footprint, same performance as virgin polyester",
         "compliance_impact": "Qualifies for sustainable labelling in most regions"},
        {"material_id": "MTL-000002", "material_name": "Lab-Grown Leather", "material_category": "Technical",
         "readiness_level": "pilot", "primary_use": "Premium footwear and accessories", "supplier_examples": "VitroLabs, Modern Meadow",
         "cost_vs_standard_pct": 45.0, "performance_benefits": "No animal welfare issues, customizable properties",
         "compliance_impact": "New regulatory framework emerging in EU"},
        {"material_id": "MTL-000003", "material_name": "Mycelium Leather", "material_category": "Sustainable",
         "readiness_level": "experimental", "primary_use": "Accessories and experimental pieces", "supplier_examples": "Bolt Threads",
         "cost_vs_standard_pct": 85.0, "performance_benefits": "Fully biodegradable, mushroom-based",
         "compliance_impact": "Positive for circular economy claims"},
        {"material_id": "MTL-000004", "material_name": "Performance Recycled Nylon", "material_category": "Performance",
         "readiness_level": "volume_proven", "primary_use": "Active and outerwear", "supplier_examples": "ECONYL, Repreve",
         "cost_vs_standard_pct": 5.5, "performance_benefits": "Lighter weight, enhanced durability, water-resistant",
         "compliance_impact": "Well-established in market"},
    ]

    # Seasonal events
    seasonal_events = [
        {"event_id": "EVT-000001", "event_name": "Black Friday & Cyber Monday", "event_type": "Shopping",
         "market": "UK", "start_date": "2026-11-23", "end_date": "2026-11-30", "sales_lift_pct": 280.0},
        {"event_id": "EVT-000002", "event_name": "Boxing Day Sale", "event_type": "Shopping",
         "market": "UK", "start_date": "2026-12-26", "end_date": "2027-01-07", "sales_lift_pct": 320.0},
        {"event_id": "EVT-000003", "event_name": "Black Friday & Cyber Monday", "event_type": "Shopping",
         "market": "US", "start_date": "2026-11-27", "end_date": "2026-12-02", "sales_lift_pct": 350.0},
        {"event_id": "EVT-000004", "event_name": "Christmas Season", "event_type": "Holiday",
         "market": "UK", "start_date": "2026-11-01", "end_date": "2026-12-23", "sales_lift_pct": 450.0},
        {"event_id": "EVT-000005", "event_name": "Spring Sale", "event_type": "Shopping",
         "market": "Germany", "start_date": "2027-03-01", "end_date": "2027-03-15", "sales_lift_pct": 150.0},
    ]

    # Trend forecasts
    trend_forecasts = [
        {"forecast_id": "FCT-000001", "trend_id": "TRD-000002", "season": "AW27", "market": "UK",
         "forecast_text": "Oversized silhouettes continue to dominate but with more structured variations. Peak expected Q4 2026.", "confidence_level": "high"},
        {"forecast_id": "FCT-000002", "trend_id": "TRD-000002", "season": "AW27", "market": "US",
         "forecast_text": "Delayed adoption vs UK. Growing rapidly through Q4. Expect mainstream adoption by SS27.", "confidence_level": "high"},
        {"forecast_id": "FCT-000003", "trend_id": "TRD-000001", "season": "AW27", "market": "UK",
         "forecast_text": "Quiet luxury entering decline phase. Expect shift toward maximalism and bold statements.", "confidence_level": "medium"},
        {"forecast_id": "FCT-000004", "trend_id": "TRD-000003", "season": "AW27", "market": "UK",
         "forecast_text": "Wellness and recovery category strong through holiday season. Expect sustained growth into SS27.", "confidence_level": "high"},
        {"forecast_id": "FCT-000005", "trend_id": "TRD-000002", "season": "SS27", "market": "UK",
         "forecast_text": "Oversized silhouettes peak in autumn 2026, begin decline in early 2027. Fitted alternatives emerging.", "confidence_level": "medium"},
    ]

    return {
        "trends": trends,
        "market_search_interest": search_interest,
        "social_mentions": social_mentions,
        "sku_sales_trends": sku_sales_trends,
        "commodity_prices": commodity_prices,
        "silhouette_cycles": silhouette_cycles,
        "trend_adoption": trend_adoption,
        "product_launches": product_launches,
        "competitor_risk_disclosures": competitor_risk_disclosures,
        "innovative_materials": innovative_materials,
        "seasonal_events": seasonal_events,
        "trend_forecasts": trend_forecasts
    }
