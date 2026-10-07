"""Property & Footfall data: energy consumption, store footfall history and forecasts, catchment areas."""
from datetime import time, timedelta


def generate(g):
    r = g.rng

    # Get stores from master data - include enough stores to cover ST214
    all_stores = [s for s in g.master("sites") if s["type"] == "store"]
    stores = all_stores[:220]  # Include stores up to ST220 for coverage
    sites = [s for s in g.master("sites") if s["type"] in ("store", "dc")]  # All stores and DCs for energy

    energy = []
    footfall = []
    forecasts = []
    catchments = []

    # Energy consumption: weekly data for past 26 weeks (6 months) and next 4 weeks
    for site in sites[:100]:  # Cap at 100 sites for volume
        site_id = site["site_id"]
        # Generate weekly data from -26 weeks to +4 weeks
        for week_offset in range(-26, 5):
            week_start = g.as_of + timedelta(weeks=week_offset)
            week_end = week_start + timedelta(days=6)

            # Base consumption depends on site type
            if site["type"] == "dc":
                base_kwh = r.gauss(50000, 5000)  # DC uses more energy
            else:
                base_kwh = r.gauss(5000, 1000)  # Store uses less

            # Add seasonal variation
            month = week_start.month
            if month in (11, 12):  # Peak season (Nov-Dec)
                base_kwh *= 1.3
            elif month in (1, 2):  # Post-peak
                base_kwh *= 1.1

            kwh = max(1000, base_kwh + r.gauss(0, base_kwh * 0.1))
            cost = kwh * 0.18  # GBP per kWh

            energy.append({
                "consumption_id": f"ENG-{len(energy) + 1:06d}",
                "site_id": site_id,
                "period_start": week_start,
                "period_end": week_end,
                "energy_kwh": round(kwh, 1),
                "energy_cost_gbp": round(cost, 2),
                "measured_at": week_end + timedelta(days=1)
            })

    # Store footfall: daily hourly data for stores in past 60 days and forecast for next 7 days
    for store in stores:
        site_id = store["site_id"]

        # Historical footfall for past 60 days
        for day_offset in range(-60, 1):
            date = g.as_of + timedelta(days=day_offset)
            day_of_week = date.weekday()  # 0=Monday, 6=Sunday

            # Base footfall varies by day of week
            if day_of_week < 5:  # Mon-Fri
                daily_base = r.gauss(2000, 300)
            else:  # Sat-Sun
                daily_base = r.gauss(3500, 500)

            # Hourly variation
            for hour in range(9, 21):  # 9am to 8pm
                if hour in (9, 10):  # Morning ramp
                    hourly_pct = 0.4
                elif hour in (11, 12):  # Late morning
                    hourly_pct = 0.8
                elif hour in (13, 14):  # Lunch
                    hourly_pct = 1.0
                elif hour in (15, 16):  # Afternoon
                    hourly_pct = 0.9
                else:  # Evening
                    hourly_pct = 0.6

                footfall_count = max(50, int(daily_base * hourly_pct + r.gauss(0, daily_base * 0.15)))
                sales_per_visitor = r.gauss(12, 2)
                sales_gbp = footfall_count * sales_per_visitor

                footfall.append({
                    "footfall_id": f"FF-{len(footfall) + 1:06d}",
                    "site_id": site_id,
                    "date": date,
                    "hour": hour,
                    "footfall_count": footfall_count,
                    "sales_gbp": round(sales_gbp, 2),
                    "recorded_at": date
                })

        # Footfall forecast for next 7 days
        for day_offset in range(1, 8):
            date = g.as_of + timedelta(days=day_offset)
            day_of_week = date.weekday()

            if day_of_week < 5:
                daily_base = r.gauss(2000, 300)
            else:
                daily_base = r.gauss(3500, 500)

            for hour in range(9, 21):
                if hour in (9, 10):
                    hourly_pct = 0.4
                elif hour in (11, 12):
                    hourly_pct = 0.8
                elif hour in (13, 14):
                    hourly_pct = 1.0
                elif hour in (15, 16):
                    hourly_pct = 0.9
                else:
                    hourly_pct = 0.6

                forecast = max(50, int(daily_base * hourly_pct + r.gauss(0, daily_base * 0.1)))
                confidence = r.gauss(85, 5)  # 80-90% confidence

                forecasts.append({
                    "forecast_id": f"FFC-{len(forecasts) + 1:06d}",
                    "site_id": site_id,
                    "forecast_date": date,
                    "hour": hour,
                    "forecast_footfall_count": forecast,
                    "confidence_level": round(max(60, min(99, confidence)), 1),
                    "created_at": g.as_of
                })

    # Store catchment areas
    for i, store in enumerate(stores[:100]):  # Catchment for first 100 stores
        site_id = store["site_id"]

        # Each store has a catchment
        radius = r.gauss(3.5, 1.0)
        radius = max(1.5, min(8.0, radius))  # Clamp between 1.5 and 8 km

        # Population in catchment (rough estimate)
        population = int(r.gauss(45000, 15000))
        population = max(10000, population)

        # Competitor stores within catchment (if any)
        competitors = []
        for other_store in stores[:100]:
            if other_store["site_id"] != site_id:
                # Random chance of overlap
                if r.random() < 0.3:  # 30% chance of competitor in catchment
                    competitors.append(other_store["site_id"])

        overlap_pct = len(competitors) * 8.0  # Each competitor ~8% overlap
        overlap_pct = min(60.0, overlap_pct)

        catchments.append({
            "catchment_id": f"CAT-{len(catchments) + 1:06d}",
            "primary_store_id": site_id,
            "radius_km": round(radius, 1),
            "population": population,
            "competitor_stores": ", ".join(competitors) if competitors else "",
            "overlap_percentage": round(overlap_pct, 1),
            "updated_at": g.as_of
        })

    return {
        "energy_consumption": energy,
        "store_footfall": footfall,
        "footfall_forecast": forecasts,
        "store_catchment": catchments
    }
