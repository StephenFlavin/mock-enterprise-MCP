"""Freight rates: spot rates, contract rates, benchmarks, forecasts and surcharges."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng

    # Common ports and airports
    sea_lanes = [
        ("VNHCM", "GBFXT"), ("VNHCM", "NLRTM"), ("VNHCM", "USLAX"),
        ("CNSHA", "GBFXT"), ("CNSHA", "NLRTM"), ("CNSHA", "USLAX"),
        ("BDDAC", "GBFXT"), ("BDDAC", "USLAX"), ("SGSIN", "GBFXT"),
    ]

    air_lanes = [
        ("DAC", "LHR"), ("DAC", "CDG"), ("DAC", "AMS"),
        ("VNHCM", "LHR"), ("VNHCM", "CDG"), ("BKK", "LHR"),
        ("CNSHA", "LHR"), ("DXB", "LHR"),
    ]

    road_lanes = [
        ("DC1", "ST214"), ("DC2", "ST101"), ("DC3", "ST255"),
        ("DC1", "ST050"), ("DC2", "ST200"),
    ]

    parcel_postcodes = [
        ("DC1", "SW1A"), ("DC1", "E1C"), ("DC1", "N1C"),
        ("DC2", "B1A"), ("DC2", "C5A"), ("DC3", "LS1"),
    ]

    carriers_sea = [c["carrier_id"] for c in g.master("carriers") if c["mode"] == "ocean"]
    carriers_air = [c["carrier_id"] for c in g.master("carriers") if c["mode"] == "air"]

    # Generate spot rates
    spot_rates = []
    rate_history = []

    for origin, dest in sea_lanes:
        lane_id = f"{origin}-{dest}"
        base_rate = r.uniform(1200, 3000)

        # Generate weekly spot rates for 12 weeks + 4 weeks forward
        for weeks_back in range(-4, 16):
            rate_date = g.as_of + timedelta(weeks=weeks_back)
            # Add realistic noise
            noise = r.gauss(0, base_rate * 0.05)
            rate = max(base_rate * r.uniform(0.8, 1.2) + noise, 800)
            spot_rates.append({
                "rate_id": f"RAT-{len(spot_rates) + 1:06d}",
                "lane_id": lane_id,
                "mode": "sea",
                "rate_date": rate_date,
                "rate_gbp": round(rate, 2),
                "unit": "per 40ft container",
                "origin": origin,
                "destination": dest,
                "min_weight_kg": None,
                "max_weight_kg": None,
                "transit_days": r.randint(25, 35),
                "source": "market data"
            })

    # Generate air rates
    for origin, dest in air_lanes:
        # Multiple quotes per lane
        for quote_num in range(r.randint(3, 5)):
            carrier = r.choice(carriers_air)
            rate_per_kg = r.uniform(1.5, 5.0)
            spot_rates.append({
                "rate_id": f"RAT-{len(spot_rates) + 1:06d}",
                "lane_id": f"{origin}-{dest}",
                "mode": "air",
                "rate_date": g.as_of,
                "rate_gbp": round(rate_per_kg, 2),
                "unit": "per kg",
                "origin": origin,
                "destination": dest,
                "min_weight_kg": 100,
                "max_weight_kg": 100000,
                "transit_days": r.randint(3, 7),
                "source": "carrier quote"
            })

    # Generate road rates
    for origin, dest in road_lanes:
        lane_id = f"{origin}-{dest}"
        for weeks_back in range(-1, 5):
            rate_date = g.as_of + timedelta(weeks=weeks_back)
            rate = r.uniform(150, 500)
            spot_rates.append({
                "rate_id": f"RAT-{len(spot_rates) + 1:06d}",
                "lane_id": lane_id,
                "mode": "road",
                "rate_date": rate_date,
                "rate_gbp": round(rate, 2),
                "unit": "per drop",
                "origin": origin,
                "destination": dest,
                "min_weight_kg": None,
                "max_weight_kg": None,
                "transit_days": 1,
                "source": "carrier quote"
            })

    # Generate parcel rates
    for origin, postcode in parcel_postcodes:
        lane_id = f"{origin}-{postcode}"
        for service in ["standard", "express", "next-day"]:
            for weight_band in [(0, 1), (1, 5), (5, 20)]:
                rate_date = g.as_of
                if service == "standard":
                    rate = r.uniform(5, 15)
                    transit_days = 3
                elif service == "express":
                    rate = r.uniform(12, 25)
                    transit_days = 2
                else:  # next-day
                    rate = r.uniform(20, 40)
                    transit_days = 1
                spot_rates.append({
                    "rate_id": f"RAT-{len(spot_rates) + 1:06d}",
                    "lane_id": lane_id,
                    "mode": "parcel",
                    "rate_date": rate_date,
                    "rate_gbp": round(rate, 2),
                    "unit": f"{service}",
                    "origin": origin,
                    "destination": postcode,
                    "min_weight_kg": weight_band[0],
                    "max_weight_kg": weight_band[1],
                    "transit_days": transit_days,
                    "source": "carrier quote"
                })

    # Generate contract rates
    contract_rates = []
    for origin, dest in sea_lanes[:3]:  # Only top lanes
        lane_id = f"{origin}-{dest}"
        carrier = r.choice(carriers_sea)
        base_rate = r.uniform(1000, 2500)
        contract_rates.append({
            "contract_rate_id": f"CTR-{len(contract_rates) + 1:06d}",
            "carrier_id": carrier,
            "lane_id": lane_id,
            "mode": "sea",
            "rate_from": (g.as_of - timedelta(days=r.randint(30, 180))),
            "rate_to": (g.as_of + timedelta(days=r.randint(180, 365))),
            "rate_gbp": round(base_rate, 2),
            "unit": "per 40ft container",
            "min_volume_units": r.choice([500, 1000, 2000, 5000]),
            "max_volume_units": r.choice([2000, 5000, 10000, 20000]),
            "volume_period": "monthly",
            "volume_band": r.choice(["small", "medium", "large"]),
            "status": "active"
        })

    # Generate air freight quotes
    air_freight_quotes = []
    for origin, dest in air_lanes:
        for carrier in r.sample(carriers_air, min(3, len(carriers_air))):
            rate_per_kg = r.uniform(1.5, 5.0)
            weight = r.choice([1000, 2000, 5000, 10000])
            air_freight_quotes.append({
                "quote_id": f"QTE-{len(air_freight_quotes) + 1:06d}",
                "origin_airport": origin,
                "destination_airport": dest,
                "weight_kg": weight,
                "rate_gbp_per_kg": round(rate_per_kg, 2),
                "total_gbp": round(rate_per_kg * weight, 2),
                "transit_days": r.randint(3, 7),
                "carrier_id": carrier,
                "quote_date": g.as_of,
                "valid_until": (g.as_of + timedelta(days=r.randint(7, 30))),
                "status": r.choice(["quoted", "accepted"]),
                "notes": ""
            })

    # Generate rate history
    for origin, dest in sea_lanes[:4]:
        lane_id = f"{origin}-{dest}"
        for weeks_back in range(52, 0, -1):
            rate_date = g.as_of - timedelta(weeks=weeks_back)
            spot_rate = r.uniform(1000, 3000)
            contract_rate = spot_rate * r.uniform(0.85, 0.95)

            # Previous week for comparison
            prev_spot = r.uniform(1000, 3000)
            rate_history.append({
                "lane_id": lane_id,
                "rate_date": rate_date,
                "mode": "sea",
                "spot_rate_gbp": round(spot_rate, 2),
                "contract_rate_gbp": round(contract_rate, 2),
                "contract_rate_pct": round((contract_rate / spot_rate) * 100, 1),
                "rate_change_week": round(((spot_rate - prev_spot) / prev_spot) * 100, 1),
                "rate_change_month": round(r.uniform(-5, 10), 1),
                "rate_change_year": round(r.uniform(-15, 20), 1)
            })

    # Generate market benchmarks
    market_benchmarks = []
    for origin, dest in sea_lanes:
        lane_id = f"{origin}-{dest}"
        base_rate = r.uniform(1200, 3000)
        for volume_band in ["small", "medium", "large"]:
            benchmark = base_rate * r.uniform(0.95, 1.05)
            market_benchmarks.append({
                "benchmark_id": f"BEN-{len(market_benchmarks) + 1:06d}",
                "lane_id": lane_id,
                "mode": "sea",
                "volume_band": volume_band,
                "benchmark_rate_gbp": round(benchmark, 2),
                "data_points": r.randint(5, 20),
                "benchmark_date": g.as_of,
                "percentile_25_gbp": round(benchmark * 0.9, 2),
                "percentile_50_gbp": round(benchmark, 2),
                "percentile_75_gbp": round(benchmark * 1.1, 2)
            })

    # Generate surcharges
    surcharges = []
    surcharge_types = ["fuel", "congestion", "security", "equipment", "port", "war risk"]
    for carrier in r.sample(carriers_sea, min(3, len(carriers_sea))):
        for _ in range(r.randint(1, 3)):
            surcharges.append({
                "surcharge_id": f"SUR-{len(surcharges) + 1:06d}",
                "carrier_id": carrier,
                "surcharge_type": r.choice(surcharge_types),
                "start_date": g.as_of - timedelta(days=r.randint(0, 60)),
                "end_date": g.as_of + timedelta(days=r.randint(30, 120)),
                "amount_gbp": round(r.uniform(50, 500), 2),
                "applies_to_mode": "sea",
                "applies_to_lane": r.choice([None, r.choice([f"{o}-{d}" for o, d in sea_lanes[:3]])]),
                "status": "effective"
            })

    # Generate alternate port options
    alternate_ports = []
    for i, (origin, dest) in enumerate(sea_lanes[:3]):
        alternate_ports.append({
            "route_id": f"ALT-{len(alternate_ports) + 1:06d}",
            "primary_lane_id": f"{origin}-{dest}",
            "origin_port": origin,
            "primary_dest_port": dest,
            "alternate_dest_port": "NLRTM" if dest == "GBFXT" else "GBFXT",
            "transit_days_primary": r.randint(25, 35),
            "transit_days_alternate": r.randint(25, 35),
            "rate_gbp_sea": round(r.uniform(1200, 2800), 2),
            "rate_gbp_rail": round(r.uniform(300, 600), 2),
            "total_transit_days": r.randint(30, 40),
            "cost_gbp": round(r.uniform(1500, 3400), 2),
            "status": "active"
        })

    # Generate rate forecasts
    rate_forecast = []
    for origin, dest in sea_lanes[:4]:
        lane_id = f"{origin}-{dest}"
        base_rate = r.uniform(1200, 3000)
        trend = r.choice(["rising", "stable", "falling"])

        for weeks_forward in range(1, 13):
            if trend == "rising":
                forecast = base_rate * (1 + 0.02 * weeks_forward)
            elif trend == "falling":
                forecast = base_rate * (1 - 0.02 * weeks_forward)
            else:
                forecast = base_rate * r.uniform(0.98, 1.02)

            rate_forecast.append({
                "forecast_id": f"FRC-{len(rate_forecast) + 1:06d}",
                "lane_id": lane_id,
                "mode": "sea",
                "forecast_date": g.as_of + timedelta(weeks=weeks_forward),
                "forecast_gbp": round(forecast, 2),
                "confidence_pct": r.randint(60, 85),
                "trend": trend,
                "notes": r.choice(["Strong demand", "Supply constraints", "Seasonal peak", "Low capacity"])
            })

    # Generate transit times
    transit_times = []
    for origin, dest in sea_lanes:
        lane_id = f"{origin}-{dest}"
        transit_times.append({
            "transit_id": f"TRN-{len(transit_times) + 1:06d}",
            "lane_id": lane_id,
            "mode": "sea",
            "origin": origin,
            "destination": dest,
            "transit_days_scheduled": r.randint(25, 35),
            "transit_days_actual_avg": round(r.uniform(25, 38), 1),
            "reliability_pct": round(r.uniform(75, 95), 1),
            "data_period": "last 12 weeks"
        })

    # Generate rate indices
    rate_indices = []
    index_names = ["SCFI", "WCI", "TAC Index"]
    for index in index_names:
        base_value = r.choice([800, 1000, 1200])
        for weeks_back in range(52, -1, -1):
            index_date = g.as_of - timedelta(weeks=weeks_back)
            noise = r.gauss(0, base_value * 0.05)
            value = max(base_value * r.uniform(0.8, 1.2) + noise, 500)
            rate_indices.append({
                "index_name": index,
                "index_date": index_date,
                "index_value": round(value, 1),
                "week_change_pct": round(r.uniform(-5, 5), 1),
                "year_change_pct": round(r.uniform(-20, 30), 1),
                "mode": "sea"
            })

    # Generate booking volumes
    booking_volumes = []
    periods = ["2026-Q4", "2026-Q1", "2026-Q2"]
    for origin, dest in sea_lanes[:5]:
        lane_id = f"{origin}-{dest}"
        for period in periods:
            total = r.randint(1000, 5000)
            contract_pct = r.randint(40, 80)
            contract_vol = int(total * contract_pct / 100)
            booking_volumes.append({
                "lane_id": lane_id,
                "booking_period": period,
                "contract_volume_units": contract_vol,
                "spot_volume_units": total - contract_vol,
                "total_volume_units": total,
                "contract_pct": round(contract_pct, 1),
                "spot_pct": round(100 - contract_pct, 1)
            })

    # Generate freight emissions
    freight_emissions = []
    freight_emissions.append({
        "lane_id": "sea",
        "shipment_type": "sea",
        "mode": "40ft container",
        "weight_kg": 20000,
        "emissions_co2e_kg": 2500,
        "emissions_co2e_per_kg": 0.125,
        "data_source": "industry standard"
    })
    freight_emissions.append({
        "lane_id": "air",
        "shipment_type": "air",
        "mode": "typical cargo",
        "weight_kg": 5000,
        "emissions_co2e_kg": 5000,
        "emissions_co2e_per_kg": 1.0,
        "data_source": "industry standard"
    })

    return {
        "spot_rates": spot_rates,
        "contract_rates": contract_rates,
        "air_freight_quotes": air_freight_quotes,
        "rate_history": rate_history,
        "market_benchmarks": market_benchmarks,
        "surcharges": surcharges,
        "alternate_ports": alternate_ports,
        "rate_forecast": rate_forecast,
        "transit_times": transit_times,
        "rate_indices": rate_indices,
        "booking_volumes": booking_volumes,
        "freight_emissions": freight_emissions
    }
