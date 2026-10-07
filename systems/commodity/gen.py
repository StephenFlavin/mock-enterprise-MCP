"""Generate commodity price data, forecasts, indices, and market news."""
from datetime import datetime, timedelta
import math


def generate(g):
    r = g.rng

    # Commodities tracked
    commodities = ["COTTON", "POLYESTER", "NYLON", "LEATHER", "SS304", "ENERGY_ELEC", "PKG_CORR", "PKG_FILM"]

    prices, forecasts, alerts, seasonality = [], [], [], []
    news, indices, components, supply_outlook = [], [], [], []
    packaging_idx, cost_outlook, recycled_prem, forecast_acc = [], [], [], []

    # 1. Generate commodity prices (last 365 days)
    for commodity in commodities:
        base_price = {"COTTON": 1.95, "POLYESTER": 0.95, "NYLON": 1.20, "LEATHER": 44.50,
                      "SS304": 2850, "ENERGY_ELEC": 0.165, "PKG_CORR": 0.025, "PKG_FILM": 0.008}.get(commodity, 1.0)
        unit = {"COTTON": "tonne", "POLYESTER": "kg", "NYLON": "kg", "LEATHER": "kg",
                "SS304": "tonne", "ENERGY_ELEC": "kWh", "PKG_CORR": "sqm", "PKG_FILM": "kg"}.get(commodity, "unit")

        # Generate price series with trend
        current_date = g.as_of - timedelta(days=365)
        trend = r.uniform(-0.15, 0.15)
        volatility = {"COTTON": 0.08, "POLYESTER": 0.06, "NYLON": 0.05, "LEATHER": 0.07,
                      "SS304": 0.10, "ENERGY_ELEC": 0.12, "PKG_CORR": 0.04, "PKG_FILM": 0.05}.get(commodity, 0.05)

        for i in range(365):
            date = current_date + timedelta(days=i)
            # Trend + noise + seasonal
            seasonal = 0.05 * math.sin(2 * math.pi * i / 365)
            noise = r.gauss(0, volatility)
            price_move = (trend / 365) + seasonal + noise
            price = base_price * (1 + price_move)
            price = max(price * 0.5, price)  # Don't go negative

            prices.append({
                "commodity_id": commodity,
                "price_date": date.date(),
                "price_gbp_unit": round(price, 4),
                "source": r.choice(["LME", "ICE", "Market Feed", "Bloomberg"]),
                "unit_name": unit
            })
            base_price = price

    # 2. Generate forecasts
    for commodity in commodities:
        base_price = float([p["price_gbp_unit"] for p in prices if p["commodity_id"] == commodity][-1])
        for horizon in [3, 6, 12]:
            # Simple trend-based forecast
            trend_direction = r.choice([1, -1])
            forecast_price = base_price * (1 + 0.02 * trend_direction * (horizon / 6))

            forecasts.append({
                "forecast_id": f"FOR-{len(forecasts) + 1:06d}",
                "commodity_id": commodity,
                "forecast_date": g.as_of,
                "forecast_price_gbp": round(forecast_price, 4),
                "confidence_level": r.choice(["low", "medium", "high"]),
                "horizon_months": horizon,
                "analyst_note": r.choice([
                    "Supported by supply tightness",
                    "Demand expected to ease",
                    "Geopolitical risk premium",
                    "Cost push from energy",
                    "Seasonal factors"
                ])
            })

    # 3. Generate seasonality patterns
    for commodity in commodities:
        for month in range(1, 13):
            # Typical seasonal patterns
            if commodity == "COTTON":
                pattern = [90, 88, 92, 98, 105, 110, 115, 108, 95, 92, 90, 88]
            elif commodity == "LEATHER":
                pattern = [100, 102, 105, 108, 110, 108, 105, 103, 100, 98, 96, 95]
            else:
                pattern = [100] * 12

            idx = month - 1
            seasonality.append({
                "commodity_id": commodity,
                "month": month,
                "avg_price_index": float(pattern[idx]),
                "typical_high_pct": float(pattern[idx] + r.randint(2, 8)),
                "typical_low_pct": float(pattern[idx] - r.randint(2, 8))
            })

    # 4. Generate market news
    news_templates = [
        ("Supply disruption in {region}", "supply", "{commodity} supply from {region} disrupted due to transport issues. Expected impact: +{pct}% cost."),
        ("Weather impact on {commodity} crop", "weather", "Adverse weather in major producing region affecting crop yields. Prices expected to rise."),
        ("Trade policy update", "trade", "New tariffs on {commodity} imports effective next month. Domestic sourcing may be more competitive."),
        ("Strong demand signal", "demand", "Buyer demand for {commodity} increasing ahead of Q4. Market tightness expected."),
        ("Geopolitical tensions", "geopolitical", "Tensions in {region} may disrupt {commodity} supply chains. Risk premium evident in prices."),
    ]

    for i in range(len(commodities) * 2):
        commodity = r.choice(commodities)
        template_idx = i % len(news_templates)
        title, category, summary_tmpl = news_templates[template_idx]

        region = r.choice(["India", "Brazil", "Vietnam", "Turkey", "USA", "China"])
        pct = r.randint(2, 15)

        news.append({
            "news_id": f"NEWS-{len(news) + 1:06d}",
            "commodity_id": commodity,
            "published_at": g.as_of - timedelta(days=r.randint(0, 30)),
            "title": title.format(region=region, commodity=commodity, pct=pct),
            "summary": summary_tmpl.format(commodity=commodity, region=region, pct=pct),
            "category": category
        })

    # 5. Generate market indices
    index_categories = ["textiles", "metals", "energy", "packaging"]
    for category in index_categories:
        for i in range(60):
            date = g.as_of - timedelta(days=i*7)
            base_idx = {"textiles": 250, "metals": 180, "energy": 85, "packaging": 145}.get(category, 100)
            idx_val = base_idx * (1 + r.gauss(0, 0.05))

            indices.append({
                "index_id": f"IDX-{category.upper()}-{i:03d}",
                "index_name": f"{category.title()} Price Index",
                "category": category,
                "base_date": g.as_of - timedelta(days=365),
                "index_value": round(idx_val, 1),
                "index_date": date.date()
            })

    # 6. Generate component prices (zips, trims)
    components_list = [
        ("ZIP_PLASTIC", "Plastic zips per 100 units", "per 100 units", 2.50),
        ("ZIP_METAL", "Metal zips per 100 units", "per 100 units", 4.75),
        ("TRIM_WOVEN", "Woven trim per metre", "per metre", 0.85),
        ("TRIM_ELASTIC", "Elastic trim per metre", "per metre", 0.45),
        ("BUTTON_PLASTIC", "Plastic buttons per 100", "per 100", 1.20),
    ]

    for comp_id, comp_name, unit, base_px in components_list:
        current_date = g.as_of - timedelta(days=180)
        current_price = base_px
        for i in range(26):  # 6 months weekly
            date = current_date + timedelta(days=i*7)
            current_price = current_price * (1 + r.gauss(0, 0.03))

            components.append({
                "component_id": comp_id,
                "component_name": comp_name,
                "price_date": date.date(),
                "price_gbp": round(current_price, 4),
                "unit_desc": unit
            })

    # 7. Generate supply outlook
    materials = ["COTTON", "NYLON", "POLYESTER", "LEATHER", "RECYCLED_POLY", "SS304"]
    for material in materials:
        supply_outlook.append({
            "outlook_id": f"SUP-{len(supply_outlook) + 1:06d}",
            "material_id": material,
            "outlook_date": g.as_of,
            "supply_level": r.choice(["abundant", "adequate", "tight", "critical"]),
            "reasoning": r.choice([
                "Strong supply from multiple sources; no constraints expected",
                "Normal seasonal patterns; adequate stock expected",
                "Supply tight due to production capacity limits",
                "Critical shortage expected; recommend early buying"
            ])
        })

    # 8. Generate packaging indices
    for i in range(100):
        date = g.as_of - timedelta(days=i*3.65)
        corrugated_base = 145.5
        film_base = 98.2

        packaging_idx.append({
            "index_date": date.date(),
            "corrugated_index": round(corrugated_base * (1 + r.gauss(0, 0.04)), 1),
            "film_index": round(film_base * (1 + r.gauss(0, 0.03)), 1)
        })

    # 9. Generate cost outlooks
    for commodity in commodities:
        base_price = float([p["price_gbp_unit"] for p in prices if p["commodity_id"] == commodity][-1])
        for days_ahead in [30, 60, 90]:
            outlook_price = base_price * (1 + r.gauss(0, 0.05))
            cost_outlook.append({
                "outlook_id": f"OUT-{len(cost_outlook) + 1:06d}",
                "commodity_id": commodity,
                "outlook_date": (g.as_of + timedelta(days=days_ahead)).date() if days_ahead > 0 else g.as_of.date(),
                "expected_cost_gbp": round(outlook_price, 4),
                "reasoning": r.choice([
                    "Forecast based on current market trends",
                    "Adjusted for seasonal factors",
                    "Risk premium included for supply uncertainty",
                    "Based on analyst consensus"
                ])
            })

    # 10. Generate recycled material premiums
    recycled_pairs = [("RECYCLED_POLY", "POLYESTER"), ("RECYCLED_COTTON", "COTTON"), ("RECYCLED_NYLON", "NYLON")]
    for recycled, virgin in recycled_pairs:
        for i in range(12):
            date = g.as_of - timedelta(days=i*30)
            recycled_prem.append({
                "material_id": recycled,
                "virgin_material_id": virgin,
                "premium_date": date.date(),
                "premium_pct": round(r.uniform(8, 25), 1),
                "reasoning": r.choice([
                    "Supply constraint for recycled material",
                    "Quality premium for certified recycled",
                    "Market premium for sustainability",
                    "Collection and processing costs"
                ])
            })

    # 11. Generate forecast accuracy history
    for commodity in commodities:
        for i in range(10):
            forecast_price = float(r.uniform(0.8, 1.2)) * float([p["price_gbp_unit"] for p in prices if p["commodity_id"] == commodity][-1])
            actual_price = forecast_price * (1 + r.gauss(0, 0.05))
            accuracy = max(0, 100 - abs((forecast_price - actual_price) / actual_price * 100) * 0.5)

            forecast_acc.append({
                "forecast_id": f"FOR-{len(forecast_acc) + 1:06d}",
                "commodity_id": commodity,
                "forecast_date": g.as_of - timedelta(days=i*60),
                "forecast_price_gbp": round(forecast_price, 4),
                "actual_date": (g.as_of - timedelta(days=i*60) + timedelta(days=30)).date(),
                "actual_price_gbp": round(actual_price, 4),
                "accuracy_pct": round(accuracy, 1)
            })

    return {
        "commodity_prices": prices,
        "commodity_forecasts": forecasts,
        "seasonality_patterns": seasonality,
        "market_news": news,
        "market_indices": indices,
        "component_prices": components,
        "material_supply_outlooks": supply_outlook,
        "packaging_indices": packaging_idx,
        "commodity_cost_outlooks": cost_outlook,
        "recycled_material_premiums": recycled_prem,
        "forecast_accuracy": forecast_acc,
        "price_alerts": [],  # Filled by seed data
    }
