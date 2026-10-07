"""Generate commodity price data, forecasts, indices, and market news.

Story data (anchored price paths, forecasts, outlooks, indices, benchmarks, components) is deterministic so that
facts such as "cotton +4% in 13 weeks" or "metal zips +17.9%" hold exactly; noise only fills the weeks between anchors.
Series are weekly (whole weeks back from as_of) so they move cleanly with the runtime date shift.
"""
from datetime import timedelta


def _path(anchors, weeks, rng, vol, nd):
    """Weekly price path: linear between anchor weeks (weeks-ago -> price), small noise off-anchor."""
    pts = sorted(anchors.items())
    out = {}
    for w in range(weeks):
        for (w0, p0), (w1, p1) in zip(pts, pts[1:]):
            if w0 <= w <= w1:
                base = p0 + (p1 - p0) * (w - w0) / (w1 - w0)
                break
        else:
            base = pts[-1][1]
        if w in anchors:
            out[w] = round(anchors[w], nd)
        else:
            out[w] = round(base * (1 + rng.gauss(0, vol)), nd)
    return out


# commodity -> (unit, source, decimals, weekly noise, {weeks_ago: price})
PRICES = {
    "COTTON": ("kg", "ICE", 3, 0.008, {0: 1.96, 13: 1.885, 26: 1.87, 39: 1.84, 52: 1.80, 65: 1.76, 79: 1.72}),
    "POLYESTER": ("kg", "Market Feed", 3, 0.006, {0: 0.96, 13: 0.945, 26: 0.93, 39: 0.915, 52: 0.90, 65: 0.89, 79: 0.88}),
    "NYLON": ("kg", "Market Feed", 3, 0.006, {0: 1.22, 13: 1.19, 26: 1.17, 39: 1.15, 52: 1.13, 65: 1.12, 79: 1.10}),
    "LEATHER": ("kg", "Market Feed", 2, 0.007, {0: 45.0, 13: 44.0, 26: 44.8, 39: 45.6, 52: 46.2, 65: 46.8, 79: 47.0}),
    "SS304": ("tonne", "LME", 0, 0.008, {0: 2880, 13: 2750, 26: 2700, 39: 2600, 52: 2550, 65: 2500, 79: 2480}),
    "ENERGY_ELEC": ("kWh", "Bloomberg", 4, 0.012, {0: 0.165, 13: 0.155, 26: 0.150, 39: 0.144, 52: 0.138, 65: 0.134, 79: 0.132}),
    "PKG_CORR": ("sqm", "Market Feed", 4, 0.006, {0: 0.026, 13: 0.0235, 26: 0.024, 39: 0.0232, 52: 0.0225, 65: 0.022, 79: 0.0218}),
    "PKG_FILM": ("kg", "Market Feed", 4, 0.008, {0: 0.0090, 13: 0.0083, 26: 0.0080, 39: 0.0079, 52: 0.0078, 65: 0.0077, 79: 0.0076}),
}

# forecast accuracy: commodity -> (bias, sd) of forecast error as a fraction of the actual price
ACCURACY = {"COTTON": (-0.02, 0.025), "POLYESTER": (0.005, 0.02), "NYLON": (0.01, 0.025), "LEATHER": (0.01, 0.05),
            "SS304": (-0.015, 0.03), "ENERGY_ELEC": (-0.03, 0.05), "PKG_CORR": (-0.01, 0.025), "PKG_FILM": (-0.01, 0.03)}

# components: id -> (name, unit, price 13 weeks ago, price now, curve exponent, price noise)
COMPONENTS = {
    "ZIP_PLASTIC": ("Plastic zips per 100 units", "per 100 units", 2.50, 2.74, 1.3),
    "ZIP_METAL": ("Metal zips per 100 units", "per 100 units", 4.75, 5.60, 1.6),
    "TRIM_WOVEN": ("Woven trim per metre", "per metre", 0.85, 0.86, 1.0),
    "TRIM_ELASTIC": ("Elastic trim per metre", "per metre", 0.45, 0.45, 1.0),
    "BUTTON_PLASTIC": ("Plastic buttons per 100", "per 100", 1.20, 1.21, 1.0),
}

BACKGROUND_NEWS = {
    "COTTON": [("Cotton acreage estimates trimmed", "Planted area estimates trimmed for the new season; stocks-to-use ratio edging lower.", "supply")],
    "POLYESTER": [("Paraxylene margins firm", "Feedstock margins firm as Asian crackers run at reduced rates; polyester chip offers edging up.", "supply")],
    "NYLON": [("Caprolactam plant maintenance", "Scheduled maintenance at a major caprolactam plant tightens nylon 6 chip availability for several weeks.", "supply")],
    "LEATHER": [("Hide supply steady", "Slaughter volumes steady in Europe; raw hide prices flat, tanners hold finished leather offers.", "supply")],
    "SS304": [("Nickel surcharge unchanged", "Mills left the nickel alloy surcharge unchanged for the month; 304 coil lead times stable at 6-8 weeks.", "supply")],
    "ENERGY_ELEC": [("Forward power curve steepens", "Winter baseload contracts trade above the summer strip as gas storage refills slowly.", "demand")],
    "PKG_CORR": [("Containerboard mills announce increase", "Several mills have announced a price increase on containerboard grades effective next quarter.", "supply")],
    "PKG_FILM": [("Polyethylene resin offers firm", "Resin producers hold offers firm after summer outages; film converters are passing on increases.", "supply")],
}


def generate(g):
    r = g.rng
    commodities = list(PRICES)

    # 1. weekly prices, 80 weeks of history, ending at as_of
    prices, series = [], {}
    for c, (unit, source, nd, vol, anchors) in PRICES.items():
        path = _path(anchors, 80, r, vol, nd)
        series[c] = path
        for w in range(79, -1, -1):
            prices.append({"commodity_id": c, "price_date": g.as_of - timedelta(days=7 * w),
                           "price_gbp_unit": path[w], "source": source, "unit_name": unit})

    # 2. background news (older than the default search window; current stories are in seed/market_news.csv)
    news = []
    for c in commodities:
        for title, summary, cat in BACKGROUND_NEWS[c]:
            news.append({"news_id": f"NEWS-{len(news) + 1:06d}", "commodity_id": c,
                         "published_at": g.as_of - timedelta(days=r.randint(45, 75)),
                         "title": title, "summary": summary, "category": cat})

    # 3. seasonality: avg_price_index (100 = annual average); high/low are signed % vs the annual average
    patterns = {
        "COTTON": [90, 89, 92, 98, 105, 110, 115, 108, 96, 92, 88, 86],
        "LEATHER": [100, 102, 105, 108, 110, 108, 105, 103, 100, 98, 96, 95],
        "ENERGY_ELEC": [115, 112, 105, 95, 85, 80, 82, 85, 90, 100, 110, 120],
        "SS304": [100, 102, 105, 108, 110, 108, 105, 103, 100, 98, 96, 95],
        "POLYESTER": [100, 100, 101, 102, 103, 102, 101, 101, 100, 100, 99, 99],
        "NYLON": [100, 101, 102, 103, 104, 103, 102, 101, 100, 99, 99, 98],
        "PKG_CORR": [100, 101, 102, 103, 104, 103, 102, 101, 100, 100, 101, 102],
        "PKG_FILM": [100, 100, 101, 102, 103, 102, 101, 100, 100, 100, 101, 101],
    }
    seasonality = []
    for c in commodities:
        for m in range(1, 13):
            idx = patterns[c][m - 1]
            seasonality.append({"commodity_id": c, "month": m, "avg_price_index": float(idx),
                                "typical_high_pct": float(idx - 100 + 3), "typical_low_pct": float(idx - 100 - 3)})

    # 4. component prices: weekly for 40 weeks, flat with noise before 13 weeks ago, then the planted move
    components = []
    for cid, (name, unit, p13, p0, expo) in COMPONENTS.items():
        for w in range(39, -1, -1):
            if w >= 13:
                px = p13 * (1 + r.gauss(0, 0.004)) if w != 13 else p13
            else:
                px = p13 + (p0 - p13) * ((13 - w) / 13) ** expo
            components.append({"component_id": cid, "component_name": name,
                               "price_date": g.as_of - timedelta(days=7 * w), "price_gbp": round(px, 2), "unit_desc": unit})

    supply_outlook, packaging_idx, recycled_prem = [], [], []

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
            "index_date": date,
            "corrugated_index": round(corrugated_base * (1 + r.gauss(0, 0.04)), 1),
            "film_index": round(film_base * (1 + r.gauss(0, 0.03)), 1)
        })


    # 10. Generate recycled material premiums
    recycled_pairs = [("RECYCLED_POLY", "POLYESTER"), ("RECYCLED_COTTON", "COTTON"), ("RECYCLED_NYLON", "NYLON")]
    for recycled, virgin in recycled_pairs:
        for i in range(12):
            date = g.as_of - timedelta(days=i*30)
            recycled_prem.append({
                "material_id": recycled,
                "virgin_material_id": virgin,
                "premium_date": date,
                "premium_pct": round(r.uniform(8, 25), 1),
                "reasoning": r.choice([
                    "Supply constraint for recycled material",
                    "Quality premium for certified recycled",
                    "Market premium for sustainability",
                    "Collection and processing costs"
                ])
            })


    # 5. forecast accuracy: past 3- and 6-month forecasts scored against the weekly actuals
    forecast_acc = []
    for c in commodities:
        bias, sd = ACCURACY[c]
        for horizon, weeks, origins in ((3, 13, (13, 26, 39, 52, 65)), (6, 26, (26, 39, 52, 65))):
            for a in origins:
                actual = series[c][a - weeks]
                forecast = actual * (1 + bias + r.gauss(0, sd))
                acc = max(0.0, 100 - abs(forecast - actual) / actual * 100)
                forecast_acc.append({
                    "forecast_id": f"FOR-ACC-{len(forecast_acc) + 1:04d}", "commodity_id": c,
                    "forecast_date": g.as_of - timedelta(days=7 * a), "horizon_months": horizon,
                    "forecast_price_gbp": round(forecast, PRICES[c][2] + 1),
                    "actual_date": g.as_of - timedelta(days=7 * (a - weeks)),
                    "actual_price_gbp": actual, "accuracy_pct": round(acc, 1)})

    return {
        "commodity_prices": prices,
        "commodity_forecasts": [],         # seed/commodity_forecasts.csv
        "seasonality_patterns": seasonality,
        "market_news": news,
        "market_indices": [],              # seed/market_indices.csv
        "category_benchmarks": [],         # seed/category_benchmarks.csv
        "components": [],                  # seed/components.csv
        "component_prices": components,
        "material_supply_outlooks": supply_outlook,
        "packaging_indices": packaging_idx,
        "commodity_cost_outlooks": [],     # seed/commodity_cost_outlooks.csv
        "recycled_material_premiums": recycled_prem,
        "forecast_accuracy": forecast_acc,
        "price_alerts": [],  # Filled by seed data
    }
