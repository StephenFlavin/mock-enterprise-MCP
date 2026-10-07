"""Freight rates: spot and contract rates, rate cards, benchmarks, forecasts and surcharges.

Everything is deterministic and hand-designed around the persona questions; only small background noise
uses g.rng. All port codes are master ports (VNSGN, GBFXT, NLRTM ...), except USLAX and the Mediterranean
transhipment ports (ESVLC, GRPIR), which master data does not list.
"""
import math
import random
from datetime import date, timedelta


def generate(g):
    r = g.rng
    r2 = random.Random(20261)      # separate stream so later lanes do not move the older story data
    A = g.as_of

    def wk(n):          # n weeks before as_of
        return A - timedelta(weeks=n)

    def pct(a, b):      # % change from b to a
        return round((a / b - 1) * 100, 1) if b else None

    # ------------------------------------------------------------------ sea spot rates and history
    # 12 weekly points, oldest first (week 11 back ... this week), GBP per 40ft container
    sea_series = {
        "VNSGN-GBFXT": [1900, 1910, 1925, 1950, 1985, 2040, 2100, 2170, 2250, 2330, 2400, 2460],
        "VNSGN-NLRTM": [2000, 2010, 2030, 2050, 2090, 2140, 2200, 2260, 2330, 2400, 2450, 2500],
        "VNSGN-USLAX": [3250, 3240, 3200, 3180, 3150, 3120, 3100, 3080, 3040, 3010, 2980, 2950],
    }
    for lane, now, start in [("CNSHA-GBFXT", 2280, 2190), ("CNSHA-NLRTM", 2330, 2240),
                             ("BDCGP-GBFXT", 2520, 2450), ("CNSHA-USLAX", 3120, 3290),
                             ("CNYTN-GBFXT", 2310, 2210), ("INNSA-GBFXT", 2050, 2010), ("TRMER-GBFXT", 1420, 1390),
                             ("PTLEI-GBFXT", 780, 765), ("MXZLO-GBFXT", 3000, 2960)]:
        sea_series[lane] = [round(start + (now - start) * i / 11) for i in range(12)]
    sea_transit = {"VNSGN-GBFXT": 26, "VNSGN-NLRTM": 27, "VNSGN-USLAX": 34, "CNSHA-GBFXT": 31,
                   "CNSHA-NLRTM": 32, "BDCGP-GBFXT": 33, "CNSHA-USLAX": 18, "CNYTN-GBFXT": 29,
                   "INNSA-GBFXT": 25, "TRMER-GBFXT": 14, "PTLEI-GBFXT": 4, "MXZLO-GBFXT": 24}
    best_contract = {"VNSGN-GBFXT": 1750, "VNSGN-NLRTM": 1820, "VNSGN-USLAX": 3050, "CNSHA-GBFXT": 1650,
                     "CNSHA-NLRTM": 1700, "BDCGP-GBFXT": 2350, "CNSHA-USLAX": 2980}

    spot_rates, rate_history = [], []

    def add_spot(**kw):
        row = {"rate_id": f"RAT-{len(spot_rates) + 1:06d}", "min_weight_kg": None, "max_weight_kg": None,
               "period_label": "standard"}
        row.update(kw)
        spot_rates.append(row)

    # long history: older weeks follow a seasonal wave around the oldest story level
    full_hist = {}
    old_lanes = {"VNSGN-GBFXT", "VNSGN-NLRTM", "VNSGN-USLAX", "CNSHA-GBFXT", "CNSHA-NLRTM", "BDCGP-GBFXT", "CNSHA-USLAX"}
    for lane, pts in sea_series.items():
        phase = (sum(map(ord, lane)) % 7) / 7 * 2 * math.pi
        series = {w: pts[11 - w] for w in range(12)}            # week back -> rate
        rr = r if lane in old_lanes else r2
        for w in range(12, 64):
            wave = 0.10 * math.sin(2 * math.pi * w / 52 + phase)
            series[w] = round(pts[0] * (0.93 + wave) * (1 + rr.uniform(-0.012, 0.012)))
        full_hist[lane] = series
        for w in range(12):
            origin, dest = lane.split("-")
            add_spot(lane_id=lane, mode="sea", rate_date=wk(w), rate_gbp=float(series[w]),
                     unit="per 40ft container", origin=origin, destination=dest,
                     transit_days=sea_transit[lane], source="market data")
        for w in range(63, -1, -1):
            sp = series[w]
            ct = best_contract.get(lane)
            rate_history.append({
                "lane_id": lane, "rate_date": wk(w), "mode": "sea",
                "spot_rate_gbp": float(sp), "contract_rate_gbp": float(ct) if ct else None,
                "contract_rate_pct": round(ct / sp * 100, 1) if ct else None,
                "rate_change_week": pct(sp, series[w + 1]) if w + 1 in series else None,
                "rate_change_month": pct(sp, series[w + 4]) if w + 4 in series else None,
                "rate_change_year": pct(sp, series[w + 52]) if w + 52 in series else None,
            })

    # ------------------------------------------------------------------ road spot rates (peak by lane)
    # lane: (standard, black friday week, christmas week); per load, single drop
    road = {
        "DC3-ST148": (285, 355, 390), "DC3-ST150": (140, 175, 195), "DC3-ST151": (175, 220, 245),
        "DC3-ST200": (150, 190, 210), "DC1-ST101": (190, 235, 255), "DC1-ST050": (260, 310, 340),
        "DC1-ST214": (520, 640, 700), "DC1-ST215": (560, 690, 760),
    }
    road_days = {"DC3-ST148": 1, "DC3-ST150": 1, "DC3-ST151": 1, "DC3-ST200": 1, "DC1-ST101": 1,
                 "DC1-ST050": 1, "DC1-ST214": 2, "DC1-ST215": 2}
    for lane, (std, bf, xm) in road.items():
        o, d = lane.split("-")
        for lab, rate, when in (("standard", std, A), ("Black Friday week", bf, A + timedelta(weeks=7)),
                                ("Christmas week", xm, A + timedelta(weeks=11))):
            add_spot(lane_id=lane, mode="road", rate_date=when, rate_gbp=float(rate), unit="per load (single drop)",
                     origin=o, destination=d, transit_days=road_days[lane], period_label=lab,
                     source="carrier quote" if lab == "standard" else "forward spot quote")

    # ------------------------------------------------------------------ air rate cards
    bands = [(100, 999), (1000, 2999), (3000, 4999), (5000, 100000)]
    # (origin, dest, carrier): ([rate per band], peak premium per kg, transit days)
    air_cards = [
        ("DAC", "LHR", "CAR-008", [3.60, 3.20, 2.95, 2.75], 0.45, 4),
        ("DAC", "LHR", "CAR-018", [4.05, 3.65, 3.40, 3.20], 0.45, 3),
        ("SGN", "LHR", "CAR-008", [3.95, 3.55, 3.30, 3.10], 0.50, 5),
        ("SGN", "LHR", "CAR-018", [4.40, 4.00, 3.75, 3.55], 0.50, 3),
        ("PVG", "LHR", "CAR-008", [3.20, 2.90, 2.70, 2.60], 0.40, 3),
        ("IST", "LHR", "CAR-008", [2.30, 2.05, 1.90, 1.80], 0.30, 2),
        ("IST", "LHR", "CAR-018", [2.65, 2.40, 2.25, 2.10], 0.30, 1),
        ("DXB", "LHR", "CAR-008", [2.20, 1.95, 1.80, 1.70], 0.25, 2),
        ("DAC", "CDG", "CAR-008", [3.55, 3.15, 2.90, 2.70], 0.45, 4),
    ]
    air_quotes = []
    for o, d, car, rates, prem, days in air_cards:
        for (lo, hi), rt in zip(bands, rates):
            air_quotes.append({
                "quote_id": f"QTE-{len(air_quotes) + 1:06d}", "origin_airport": o, "destination_airport": d,
                "carrier_id": car, "min_weight_kg": lo, "max_weight_kg": hi, "rate_gbp_per_kg": rt,
                "peak_rate_gbp_per_kg": round(rt + prem, 2), "transit_days": days,
                "quote_date": A, "valid_until": A + timedelta(days=21), "status": "quoted",
                "notes": "Express courier service" if car == "CAR-018" else "Scheduled freighter / belly space",
            })
    lane_air = {}
    for o, d, car, rates, prem, days in air_cards:
        lane_air.setdefault((o, d), []).append(rates[1])
    for (o, d), rs in lane_air.items():
        add_spot(lane_id=f"{o}-{d}", mode="air", rate_date=A, rate_gbp=min(rs), unit="per kg", origin=o,
                 destination=d, min_weight_kg=1000, max_weight_kg=2999, transit_days=4, source="carrier quote")

    # sea-air through-rates (sea to the hub, then air)
    sea_air = [
        ("DAC", "LHR", "DXB", "CAR-009", 1.65, 100, 9, 2, 2, "Economy sea-air via Dubai; weekly feeder from Chittagong, cut-off 5 days before sailing"),
        ("DAC", "LHR", "DXB", "CAR-010", 2.10, 100, 6, 1, 3, "Express sea-air via Dubai; twice-weekly feeder, cut-off 3 days before sailing"),
        ("SGN", "LHR", "DXB", "CAR-009", 1.85, 100, 12, 2, 2, "Economy sea-air via Dubai; weekly sailing, cut-off 5 days before sailing"),
        ("SGN", "LHR", "DXB", "CAR-010", 2.35, 100, 9, 1, 3, "Express sea-air via Dubai; cut-off 4 days before sailing"),
    ]
    sea_air_routes = [{
        "route_id": f"SAR-{i + 1:06d}", "origin_airport": o, "destination_airport": d, "via_hub": hub,
        "carrier_id": car, "rate_gbp_per_kg": rt, "min_weight_kg": mn, "sea_days": sd, "hub_transfer_days": td,
        "air_days": ad, "total_transit_days": sd + td + ad, "valid_until": A + timedelta(days=21), "notes": note,
    } for i, (o, d, hub, car, rt, mn, sd, td, ad, note) in enumerate(sea_air)]

    # ------------------------------------------------------------------ air rate history (4-weekly, 72 weeks)
    # lowest 1,000-2,999 kg rate, now and 52 weeks ago
    air_hist_targets = {("DAC", "LHR"): (3.20, 2.94), ("SGN", "LHR"): (3.55, 3.93),
                        ("PVG", "LHR"): (2.90, 3.10), ("IST", "LHR"): (2.05, 1.98)}
    air_rate_history = []
    for (o, d), (now, ago) in air_hist_targets.items():
        slope = (now - ago) / 52
        for k in range(0, 19):
            w = 4 * k
            wave = 0.06 * math.sin(math.pi * (w % 52) / 52)
            air_rate_history.append({
                "origin_airport": o, "destination_airport": d, "rate_date": wk(w),
                "rate_gbp_per_kg": round(now - slope * w + wave * (1 if w else 0), 2),
            })

    # ------------------------------------------------------------------ contract rates
    contract_rates = []

    def add_contract(carrier, lane, mode, rf, rt, rate, unit, mn, mx, per, band, level=None, wmin=None, wmax=None, terms=""):
        contract_rates.append({
            "contract_rate_id": f"CRR-{900001 + len(contract_rates)}", "carrier_id": carrier, "lane_id": lane,
            "mode": mode, "rate_from": rf, "rate_to": rt, "rate_gbp": rate, "unit": unit,
            "min_volume_units": mn, "max_volume_units": mx, "volume_period": per, "volume_band": band,
            "service_level": level, "min_weight_kg": wmin, "max_weight_kg": wmax, "terms": terms, "status": "active",
        })

    d_ = lambda s: date.fromisoformat(s)
    sea_terms = "Rate per 40ft container, all-in of base freight; BAF and peak season surcharges billed as per carrier notice"
    for car, lane, rate, band, mn, mx in [
        ("CAR-007", "VNSGN-GBFXT", 1750, "large", 500, 5000), ("CAR-005", "VNSGN-GBFXT", 1820, "medium", 300, 2000),
        ("CAR-006", "VNSGN-GBFXT", 1880, "small", 100, 1000),
        ("CAR-007", "VNSGN-NLRTM", 1820, "large", 400, 4000), ("CAR-005", "VNSGN-NLRTM", 1890, "medium", 250, 1500),
        ("CAR-006", "VNSGN-USLAX", 3050, "large", 300, 3000), ("CAR-005", "VNSGN-USLAX", 3150, "medium", 150, 1500),
        ("CAR-007", "CNSHA-GBFXT", 1650, "large", 500, 5000), ("CAR-007", "CNSHA-NLRTM", 1700, "large", 400, 4000),
        ("CAR-005", "BDCGP-GBFXT", 2350, "medium", 100, 800),
    ]:
        add_contract(car, lane, "sea", wk(36), A + timedelta(weeks=26), float(rate), "per 40ft container",
                     mn, mx, "monthly", band, "FCL 40ft", terms=sea_terms)
    # road contracts (CAR-002 matches the contracts system rate card)
    road_terms = ("Fuel surcharge capped at 12% of base rate; tail lift 18 GBP per drop; waiting time 42 GBP per hour after "
                  "60 free minutes; redelivery 55 GBP; minimum charge 35 GBP; rate covers up to 750kg per pallet, "
                  "above that 1.25 x rate")
    load_terms = ("Fuel surcharge capped at 12% of base rate; waiting time 60 GBP per hour after 120 free minutes; "
                  "redelivery 120 GBP")
    add_contract("CAR-002", "DC1-NORTH", "road", d_("2025-02-04"), d_("2028-02-04"), 17.20, "per pallet",
                 None, None, None, None, "pallet", terms=road_terms)
    add_contract("CAR-002", "DC1-NORTH", "road", d_("2025-02-04"), d_("2028-02-04"), 645.0, "per load",
                 None, None, None, None, "full load", terms=load_terms)
    add_contract("CAR-001", "DC3-NORTH", "road", d_("2025-06-05"), d_("2028-06-05"), 16.40, "per pallet",
                 None, None, None, None, "pallet", terms="Fuel surcharge capped at 10% of base rate; tail lift 15 GBP per drop; waiting time 40 GBP per hour after 60 free minutes")
    # parcel contracts (service x weight band)
    parcel = {
        "standard": ("CAR-013", [(0, 1, 2.90), (1, 5, 4.05), (5, 20, 7.50)]),
        "express": ("CAR-012", [(0, 1, 5.10), (1, 5, 6.95), (5, 20, 11.05)]),
        "next-day": ("CAR-011", [(0, 1, 7.35), (1, 5, 9.55), (5, 20, 15.70)]),
    }
    bench_parcel = {
        "standard": [2.95, 4.10, 7.60], "express": [4.70, 6.40, 10.20], "next-day": [6.30, 8.20, 13.50],
    }
    for svc, (car, rows) in parcel.items():
        for lo, hi, rate in rows:
            add_contract(car, f"UK-{svc}", "parcel", wk(30), A + timedelta(weeks=40), rate, "per parcel",
                         None, None, None, None, svc, lo, hi,
                         "Fuel surcharge capped at 8% of base rate; peak surcharge applies 1 Nov to 24 Dec")

    # ------------------------------------------------------------------ market benchmarks
    market_benchmarks = []
    sea_bench = {
        "VNSGN-GBFXT": (1900, 1840, 1760), "VNSGN-NLRTM": (1980, 1880, 1830), "VNSGN-USLAX": (3200, 3050, 2980),
        "CNSHA-GBFXT": (1760, 1700, 1640), "CNSHA-NLRTM": (1820, 1760, 1700), "BDCGP-GBFXT": (2480, 2330, 2250),
    }
    for lane, vals in sea_bench.items():
        for band, p50 in zip(("small", "medium", "large"), vals):
            market_benchmarks.append({
                "benchmark_id": f"BEN-{len(market_benchmarks) + 1:06d}", "lane_id": lane, "mode": "sea",
                "volume_band": band, "benchmark_rate_gbp": float(p50), "data_points": 12 + r.randint(0, 9),
                "benchmark_date": A, "percentile_25_gbp": round(p50 * 0.93, 2), "percentile_50_gbp": float(p50),
                "percentile_75_gbp": round(p50 * 1.07, 2), "min_weight_kg": None, "max_weight_kg": None,
            })
    for svc, vals in bench_parcel.items():
        for (lo, hi), p50 in zip([(0, 1), (1, 5), (5, 20)], vals):
            market_benchmarks.append({
                "benchmark_id": f"BEN-{len(market_benchmarks) + 1:06d}", "lane_id": f"UK-{svc}", "mode": "parcel",
                "volume_band": "medium", "benchmark_rate_gbp": p50, "data_points": 25 + r.randint(0, 20),
                "benchmark_date": A, "percentile_25_gbp": round(p50 * 0.90, 2), "percentile_50_gbp": p50,
                "percentile_75_gbp": round(p50 * 1.10, 2), "min_weight_kg": lo, "max_weight_kg": hi,
            })

    # ------------------------------------------------------------------ surcharges
    sur = [
        ("CAR-007", "fuel", -5, 12, 125, None, "effective"),
        ("CAR-007", "congestion", 2, 11, 250, "VNSGN-NLRTM", "announced"),
        ("CAR-005", "peak season", 3, 10, 300, "VNSGN-GBFXT", "announced"),
        ("CAR-005", "peak season", 3, 10, 300, "VNSGN-NLRTM", "announced"),
        ("CAR-006", "war risk", -1, 25, 175, None, "effective"),
        ("CAR-006", "equipment", 4, 17, 80, "VNSGN-USLAX", "announced"),
    ]
    surcharges = [{
        "surcharge_id": f"SUR-{i + 1:06d}", "carrier_id": c, "surcharge_type": t,
        "start_date": A + timedelta(weeks=s), "end_date": A + timedelta(weeks=e), "amount_gbp": float(a),
        "applies_to_mode": "sea", "applies_to_lane": lane, "status": st,
    } for i, (c, t, s, e, a, lane, st) in enumerate(sur)]

    # ------------------------------------------------------------------ ocean + rail through-rates
    alt = []

    def add_alt(primary, via, sea_days, sea_rate, rail_days, rail_rate, haul, direct_days):
        o, d = primary.split("-")
        alt.append({
            "route_id": f"ALT-{len(alt) + 1:06d}", "primary_lane_id": primary, "origin_port": o,
            "primary_dest_port": d, "alternate_dest_port": via, "transit_days_primary": direct_days,
            "transit_days_alternate": sea_days, "rate_gbp_sea": float(sea_rate), "rate_gbp_rail": float(rail_rate),
            "total_transit_days": sea_days + rail_days, "cost_gbp": float(sea_rate + rail_rate), "status": "active",
            "rail_days": rail_days, "rail_carrier_id": "CAR-016", "final_destination": "DC1",
            "direct_haulage_to_dc_gbp": float(haul),
        })

    add_alt("VNSGN-GBFXT", "ESVLC", 28, 2380, 5, 640, 290, 26)
    add_alt("VNSGN-GBFXT", "GRPIR", 24, 2290, 8, 720, 290, 26)
    add_alt("VNSGN-NLRTM", "ESVLC", 28, 2380, 5, 640, 410, 27)
    add_alt("VNSGN-NLRTM", "GRPIR", 24, 2290, 8, 720, 410, 27)

    # ------------------------------------------------------------------ forecasts
    rate_forecast = []
    trends = {"VNSGN-GBFXT": ("rising", 0.015), "VNSGN-NLRTM": ("rising", 0.012),
              "VNSGN-USLAX": ("falling", -0.008), "CNSHA-GBFXT": ("stable", 0.0)}
    notes = {"rising": "Peak season demand, blank sailings", "falling": "Capacity returning", "stable": "Balanced market"}
    for lane, (tr, slope) in trends.items():
        base = sea_series[lane][-1]
        for k in range(1, 13):
            rate_forecast.append({
                "forecast_id": f"FRC-{len(rate_forecast) + 1:06d}", "lane_id": lane, "mode": "sea",
                "forecast_date": A + timedelta(weeks=k), "forecast_gbp": round(base * (1 + slope * k), 2),
                "confidence_pct": max(55, 85 - 2 * k), "trend": tr, "notes": notes[tr],
            })

    # ------------------------------------------------------------------ transit times
    transit_times = []
    for lane, sched, act, rel in [("VNSGN-GBFXT", 26, 27.5, 82.5), ("VNSGN-NLRTM", 27, 28.2, 80.0),
                                  ("VNSGN-USLAX", 34, 36.1, 75.0), ("CNSHA-GBFXT", 31, 33.0, 78.5),
                                  ("CNSHA-NLRTM", 32, 33.5, 77.0), ("BDCGP-GBFXT", 33, 35.2, 74.0),
                                  ("CNYTN-GBFXT", 29, 30.4, 79.0), ("INNSA-GBFXT", 25, 26.3, 80.5),
                                  ("TRMER-GBFXT", 14, 14.6, 88.0), ("PTLEI-GBFXT", 4, 4.2, 92.0),
                                  ("MXZLO-GBFXT", 24, 25.1, 84.0)]:
        o, d = lane.split("-")
        transit_times.append({"transit_id": f"TRN-{len(transit_times) + 1:06d}", "lane_id": lane, "mode": "sea",
                              "origin": o, "destination": d, "transit_days_scheduled": sched,
                              "transit_days_actual_avg": act, "reliability_pct": rel, "data_period": "last 12 weeks"})
    for lane, sched, act, rel in [("DAC-LHR", 4, 4.3, 90.0), ("SGN-LHR", 5, 5.2, 85.0), ("IST-LHR", 2, 2.1, 94.0)]:
        o, d = lane.split("-")
        transit_times.append({"transit_id": f"TRN-{len(transit_times) + 1:06d}", "lane_id": lane, "mode": "air",
                              "origin": o, "destination": d, "transit_days_scheduled": sched,
                              "transit_days_actual_avg": act, "reliability_pct": rel, "data_period": "last 12 weeks"})

    # ------------------------------------------------------------------ rate indices with Lunar New Year run-ups
    lny_weeks = {}       # weeks back (from as_of) of the Monday of Lunar New Year week
    for lny in ("2024-02-10", "2025-01-29", "2026-02-17"):
        lny_weeks[-((d_(lny) - A).days // 7)] = lny
    peak = {}           # run-up size by LNY week
    for (wb, lny), p in zip(sorted(lny_weeks.items(), reverse=True), (0.226, 0.17, 0.26)):
        peak[wb] = p
    rate_indices = []
    for name, base, drift in (("SCFI", 1000, 0.0015), ("WCI", 1900, 0.0015)):
        vals = {}
        for w in range(159, -1, -1):
            seasonal = 1 + 0.04 * math.sin(2 * math.pi * w / 52)
            v = base * (1 + drift * (159 - w)) * seasonal
            for wb, p in peak.items():
                k = w - wb                     # negative = after LNY week; k in 1..8 = run-up weeks before
                if 0 < k <= 8:
                    v *= 1 + p * (8 - k + 1) / 8
                elif k == 0:
                    v *= 1 + p
                elif -6 <= k < 0:
                    v *= 1 + p * (1 + k / 7)
            vals[w] = v * (1 + r.uniform(-0.008, 0.008))
        for w in range(159, -1, -1):
            ev = None
            for wb in peak:
                k = w - wb
                if k == 0:
                    ev = "Lunar New Year week"
                elif 0 < k <= 6:
                    ev = "Pre-Lunar New Year run-up"
            rate_indices.append({
                "index_name": name, "index_date": wk(w), "index_value": round(vals[w], 1),
                "week_change_pct": pct(vals[w], vals[w + 1]) if w + 1 in vals else None,
                "year_change_pct": pct(vals[w], vals[w + 52]) if w + 52 in vals else None,
                "mode": "sea", "event": ev,
            })

    # ------------------------------------------------------------------ contract vs spot booking volumes (40ft boxes per quarter)
    mix = {
        "VNSGN-GBFXT": [(0, 2300, 1700), (1, 2480, 1520), (2, 2640, 1360), (3, 2840, 1160), (4, 2720, 1280)],
        "VNSGN-NLRTM": [(0, 1700, 1300), (1, 1760, 1240), (2, 1800, 1200), (3, 2000, 1000), (4, 1900, 1100)],
        "VNSGN-USLAX": [(0, 1200, 800), (1, 1250, 750), (2, 1300, 700), (3, 1250, 750), (4, 1300, 700)],
        "CNSHA-GBFXT": [(0, 1500, 750), (1, 1520, 730), (2, 1540, 710), (3, 1600, 650), (4, 1560, 690)],
    }
    labels = ["current quarter", "last quarter", "two quarters ago", "three quarters ago", "four quarters ago"]
    booking_volumes = []
    for lane, rows in mix.items():
        for q, c, s in rows:
            t = c + s
            booking_volumes.append({
                "lane_id": lane, "booking_period": labels[q], "period_start": A - timedelta(weeks=13 * q),
                "contract_volume_units": c, "spot_volume_units": s, "total_volume_units": t,
                "contract_pct": round(c / t * 100, 1), "spot_pct": round(s / t * 100, 1),
            })

    # ------------------------------------------------------------------ parcel spot rates by postcode (next-day service planning)
    for origin, postcode, f in [("DC1", "SW1A", 1.15), ("DC1", "E1C", 1.12), ("DC1", "N1C", 1.10), ("DC2", "B1A", 1.0),
                                ("DC2", "M1A", 1.02), ("DC3", "LS1", 0.95)]:
        for svc, base, days in (("standard", 3.0, 3), ("express", 4.9, 2), ("next-day", 6.4, 1)):
            for lo, hi, m in ((0, 1, 1.0), (1, 5, 1.35), (5, 20, 2.3)):
                add_spot(lane_id=f"{origin}-{postcode}", mode="parcel", rate_date=A, rate_gbp=round(base * m * f, 2),
                         unit=svc, origin=origin, destination=postcode, min_weight_kg=lo, max_weight_kg=hi,
                         transit_days=days, source="carrier quote")

    # air/sea corridors with emissions from distance (same factors as the TMS: air 0.602, sea 0.016 kg CO2e per tonne-km)
    freight_emissions = []
    for o_air, o_port, km in (("DAC", "BDCGP", 8000), ("SGN", "VNSGN", 10000), ("PVG", "CNSHA", 9200),
                              ("IST", "TRMER", 3300)):
        freight_emissions.append({
            "corridor_id": f"{o_air}-LHR", "origin_airport": o_air, "origin_port": o_port,
            "destination_airport": "LHR", "destination_port": "GBFXT", "distance_km": km,
            "air_co2e_kg_per_kg": round(km * 0.602 / 1000, 3), "sea_co2e_kg_per_kg": round(km * 0.016 / 1000, 3),
            "sea_kg_per_container": 20000, "data_source": "distance x emission factor per tonne-km (air 0.602, sea 0.016)",
        })

    # ------------------------------------------------------------------ announced carrier rate increases and annual spend
    lane_contract_boxes = {}
    for row in booking_volumes:
        if row["booking_period"] != "four quarters ago":
            lane_contract_boxes[row["lane_id"]] = lane_contract_boxes.get(row["lane_id"], 0) + row["contract_volume_units"]
    lane_contract_boxes["CNSHA-NLRTM"] = 3000
    lane_contract_boxes["BDCGP-GBFXT"] = 600
    shares = {"VNSGN-GBFXT": {"CAR-007": .5, "CAR-005": .3, "CAR-006": .2},
              "VNSGN-NLRTM": {"CAR-007": .6, "CAR-005": .4}, "VNSGN-USLAX": {"CAR-006": .6, "CAR-005": .4},
              "CNSHA-GBFXT": {"CAR-007": 1.0}, "CNSHA-NLRTM": {"CAR-007": 1.0}, "BDCGP-GBFXT": {"CAR-005": 1.0}}
    sea_units, sea_cost = {}, {}
    for lane, sh in shares.items():
        for car, share in sh.items():
            rate = next(c["rate_gbp"] for c in contract_rates
                        if c["carrier_id"] == car and c["lane_id"] == lane and c["mode"] == "sea")
            boxes = lane_contract_boxes[lane] * share
            sea_units[car] = sea_units.get(car, 0) + boxes
            sea_cost[car] = sea_cost.get(car, 0) + boxes * rate
    spend_rows = []
    for car, pct, eff, note in (("CAR-007", 6.0, 12, "General rate increase notice for next year"),
                                ("CAR-005", 8.0, 12, "General rate increase plus Asia-Europe peak season pricing"),
                                ("CAR-006", 10.0, 12, "General rate increase; carrier signalling firm push on renewal")):
        boxes = round(sea_units[car])
        spend_rows.append((car, "sea", boxes, "40ft containers", round(sea_cost[car] / boxes, 2), pct, eff, note))
    spend_rows += [
        ("CAR-001", "road", 120000, "pallets", 16.40, 4.0, 4, "General rate increase 4% from November (notice ALR-900004)"),
        ("CAR-002", "road", 210000, "pallets", 17.20, 3.5, 12, "Annual review uplift on contract rate card"),
        ("CAR-008", "air", 120000, "kg", 3.25, 3.2, 2, "Q4 rate review, average 3.2% (notice ALR-900007)"),
        ("CAR-018", "air", 30000, "kg", 3.67, 4.5, 12, "Express courier tariff increase"),
        ("CAR-011", "parcel", 150000, "parcels", 9.55, 5.9, 12, "Annual tariff uplift"),
        ("CAR-012", "parcel", 420000, "parcels", 6.95, 4.8, 12, "Annual tariff uplift"),
        ("CAR-013", "parcel", 1100000, "parcels", 4.05, 4.2, 12, "Annual tariff uplift"),
    ]
    carrier_spend = [{
        "carrier_id": c, "mode": m, "annual_volume": float(v), "volume_unit": u, "avg_rate_gbp": float(rt),
        "baseline_annual_gbp": round(v * rt, 2), "announced_increase_pct": pc, "effective_from": A + timedelta(weeks=ew),
        "notice": nt,
    } for c, m, v, u, rt, pc, ew, nt in spend_rows]

    # ------------------------------------------------------------------ alternative load ports if the Ho Chi Minh City port closes
    port_diversions = [
        {"route_id": "DIV-000001", "closed_port": "VNSGN", "alternate_load_port": "VNCMT", "alternate_port_name": "Cai Mep",
         "destination_port": "GBFXT", "routing": "Barge or truck from Ho Chi Minh City to Cai Mep (about 80 km), then direct sailing",
         "positioning_cost_gbp": 240.0, "rate_premium_gbp": 0.0, "extra_transit_days": 1, "capacity_share_pct": 60,
         "status": "limited", "notes": "Deep-water terminal next to the closed port; absorbs about 60% of normal weekly volume"},
        {"route_id": "DIV-000002", "closed_port": "VNSGN", "alternate_load_port": "SGSIN", "alternate_port_name": "Singapore",
         "destination_port": "GBFXT", "routing": "Feeder from Cai Mep to Singapore, transhipped onto the mainline service",
         "positioning_cost_gbp": 330.0, "rate_premium_gbp": 150.0, "extra_transit_days": 5, "capacity_share_pct": 100,
         "status": "active", "notes": "Weekly feeder sailings; transhipment adds dwell time"},
        {"route_id": "DIV-000003", "closed_port": "VNSGN", "alternate_load_port": "VNHPH", "alternate_port_name": "Hai Phong",
         "destination_port": "GBFXT", "routing": "Coastal feeder or road from southern Vietnam to Hai Phong (about 1,700 km), then direct sailing",
         "positioning_cost_gbp": 590.0, "rate_premium_gbp": 60.0, "extra_transit_days": 6, "capacity_share_pct": 80,
         "status": "active", "notes": "Longest positioning leg; northern Vietnam factories are closer to this port"},
    ]

    return {
        "spot_rates": spot_rates, "contract_rates": contract_rates, "air_freight_quotes": air_quotes,
        "sea_air_routes": sea_air_routes, "air_rate_history": air_rate_history, "rate_history": rate_history,
        "market_benchmarks": market_benchmarks, "surcharges": surcharges, "alternate_ports": alt,
        "rate_forecast": rate_forecast, "transit_times": transit_times, "rate_indices": rate_indices,
        "booking_volumes": booking_volumes, "freight_emissions": freight_emissions,
        "carrier_spend": carrier_spend, "port_diversions": port_diversions,
    }
