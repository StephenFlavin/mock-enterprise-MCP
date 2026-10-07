"""Demand planning system: forecasts, demand history, accuracy metrics, overrides, peak volumes, returns."""
import math
from datetime import date, datetime, timedelta

# ---------------------------------------------------------------------------------------------
# Peak calendar. Black Friday is the day after US Thanksgiving (4th Thursday of November).
# ---------------------------------------------------------------------------------------------


def black_friday(year):
    nov1 = date(year, 11, 1)
    first_thu = nov1 + timedelta(days=(3 - nov1.weekday()) % 7)
    return first_thu + timedelta(days=21 + 1)


def order_multiplier(d):
    """Order volume relative to a normal day, by distance from the relevant Black Friday."""
    bf = black_friday(d.year)
    if d < bf - timedelta(days=60):
        bf = black_friday(d.year - 1)
    k = (d - bf).days
    if k < -7:
        m = 1.0
    elif k < 0:
        m = 1.25
    elif k == 0:
        m = 3.2
    elif k == 1:
        m = 2.3
    elif k == 2:
        m = 2.1
    elif k == 3:
        m = 2.9
    elif k <= 9:
        m = 1.7
    elif k <= 16:
        m = 1.9
    elif k <= 23:
        m = 2.2
    elif k <= 26:
        m = 2.0
    elif k == 27:
        m = 1.0
    elif k <= 29:
        m = 0.15
    elif k <= 34:
        m = 0.9
    elif k <= 45:
        m = 1.5
    elif k <= 60:
        m = 1.1
    else:
        m = 1.0
    if k < 0 or k > 3:  # weekends are busier outside the peak days
        if k not in (27, 28, 29) and d.weekday() >= 5:
            m *= 1.2
    return m


def inbound_multiplier(week_monday):
    """Inbound (receipts) builds ahead of Black Friday and falls away through December."""
    bf = black_friday(week_monday.year)
    if week_monday < bf - timedelta(days=60):
        bf = black_friday(week_monday.year - 1)
    bf_week = bf - timedelta(days=bf.weekday())
    k = (week_monday - bf_week).days // 7
    table = {-6: 1.2, -5: 1.45, -4: 1.6, -3: 1.7, -2: 1.65, -1: 1.45, 0: 1.2, 1: 1.0, 2: 0.9, 3: 0.85, 4: 0.8,
             5: 0.7, 6: 0.9, 7: 1.0}
    return table.get(k, 1.0)


def monday(d):
    return d - timedelta(days=d.weekday())


def generate(g):
    r = g.rng
    as_of = g.as_of
    this_monday = monday(as_of)

    products = g.master("products")
    prod = {p["sku"]: p for p in products}
    sales = g.master("sales_weekly")
    sites = g.master("sites")

    # ------------------------------------------------------------------------------------------
    # SKU universe: the fastest sellers in master sales plus the SKUs the stories are about.
    # ------------------------------------------------------------------------------------------
    units_52w = {}
    weekly = {}
    for s in sales:
        u = int(s["store_units"]) + int(s["online_units"])
        units_52w[s["sku"]] = units_52w.get(s["sku"], 0) + u
        weekly.setdefault(s["sku"], []).append((date.fromisoformat(s["week_start"]), u, float(s["revenue_gbp"])))
    for v in weekly.values():
        v.sort()

    must = ["PF-220", "K-1700", "SKU-100056", "SKU-101897", "SKU-101904", "SKU-101911"]
    must += [p["sku"] for p in products if p["category"] == "Bags"]
    ranked = [s for s, _ in sorted(units_52w.items(), key=lambda x: (-x[1], x[0]))]
    skus = []
    for s in must + ranked[:300]:
        if s in weekly and s not in skus:
            skus.append(s)
    categories = sorted({p["category"] for p in products})

    # ------------------------------------------------------------------------------------------
    # Demand history: weekly units and revenue from master sales (store + online).
    # ------------------------------------------------------------------------------------------
    demand_history = []
    for sku in skus:
        cat = prod[sku]["category"]
        for wk, units, rev in weekly[sku]:
            demand_history.append({
                "history_id": f"DH-{len(demand_history) + 1:06d}",
                "sku": sku,
                "category": cat,
                "period_date": wk,
                "units_sold": units,
                "revenue_gbp": round(rev, 2),
                "demand_type": "actual",
                "correction_reason": None,
                "updated_at": as_of,
            })
    actual = {(h["sku"], h["period_date"]): h["units_sold"] for h in demand_history}

    # Stockout story: SKU-101904 (style STY-5520) out in 40 stores for 9 days last month (allocation shortfall,
    # DC held stock). The forecast was fine: it tracked underlying demand (sales plus lost units).
    lost_by_week = {
        ("SKU-101904", this_monday - timedelta(weeks=4)): 190,
        ("SKU-101904", this_monday - timedelta(weeks=3)): 114,
    }

    # ------------------------------------------------------------------------------------------
    # Forecasts: last 10 weeks (base, as made 4 weeks earlier) and the next 12 weeks (base/upside/downside).
    # ------------------------------------------------------------------------------------------
    forecasts = []

    def add_forecast(sku, wk, ftype, units, created):
        forecasts.append({
            "forecast_id": f"FC-{len(forecasts) + 1:06d}",
            "config_id": "CFG-000001" if units > 100 else "CFG-000003",
            "sku": sku,
            "category": prod[sku]["category"],
            "forecast_week": wk,
            "units_forecast": max(0, int(round(units))),
            "forecast_type": ftype,
            "created_at": created,
        })

    def week_factor(wk, cat):
        days = [order_multiplier(wk + timedelta(days=i)) for i in range(7)]
        m = sum(days) / 7.0
        winter = cat in ("Outerwear", "Knitwear", "Scarves", "Bedding", "Towels", "Lighting", "Fragrance")
        return 1 + (0.45 if winter else 0.25) * (m - 1)

    kettle_curve = [1.00, 1.02, 1.05, 1.10, 1.18, 1.30, 1.45, 1.70, 1.55, 1.40, 1.35, 1.10, 0.85, 0.80, 0.75, 0.70]
    for sku in skus:
        cat = prod[sku]["category"]
        hist = [u for (wk, u, _) in weekly[sku] if wk < this_monday][-8:]
        recent = sum(hist) / len(hist)
        for off in range(-10, 0):
            wk = this_monday + timedelta(weeks=off)
            a = actual.get((sku, wk))
            if a is None:
                continue
            under = a + lost_by_week.get((sku, wk), 0)
            sd = 0.03 if sku == "SKU-101904" else 0.10
            add_forecast(sku, wk, "base", under * r.gauss(1.0, sd), wk - timedelta(days=28))
        horizon = 16 if sku == "K-1700" else 12
        for off in range(0, horizon):
            wk = this_monday + timedelta(weeks=off)
            if sku == "K-1700":
                base = recent * kettle_curve[off]
            else:
                base = recent * week_factor(wk, cat) * r.gauss(1.0, 0.05)
            for ftype, mult in (("base", 1.0), ("upside", 1.2), ("downside", 0.8)):
                add_forecast(sku, wk, ftype, base * mult * (1.0 if ftype == "base" else r.gauss(1.0, 0.02)),
                             this_monday)

    # Style STY-7731 (Sage outerwear, key winter promo line, launches mid-November): weekly style demand.
    style_week_units = [900, 2600, 2300, 2100, 2400, 1500, 900, 1100, 800, 650, 500]
    sizes = {"SKU-103157": 0.30, "SKU-103164": 0.40, "SKU-103171": 0.30}
    launch_week = this_monday + timedelta(weeks=6)
    for i, total in enumerate(style_week_units):
        wk = launch_week + timedelta(weeks=i)
        for sku, share in sizes.items():
            base = total * share
            for ftype, mult in (("base", 1.0), ("upside", 1.2), ("downside", 0.8)):
                add_forecast(sku, wk, ftype, base * mult, this_monday)

    # ------------------------------------------------------------------------------------------
    # Forecast configurations
    # ------------------------------------------------------------------------------------------
    forecast_configs = []
    configs = [
        ("CFG-000001", "52-week baseline", 52, "exponential_smoothing", "fast_mover", "active"),
        ("CFG-000002", "26-week fashion", 26, "exponential_smoothing", "fast_mover", "test"),
        ("CFG-000003", "104-week slow movers", 104, "moving_average", "slow_mover", "active"),
        ("CFG-000004", "New product benchmark", 0, "comparable_products", "new_product", "active"),
    ]
    for cfg_id, name, window, method, item_type, status in configs:
        forecast_configs.append({
            "config_id": cfg_id,
            "config_name": name,
            "history_window_weeks": window,
            "method_type": method,
            "item_type": item_type,
            "status": status,
            "created_at": as_of - timedelta(days=r.randint(30, 180)),
            "notes": f"Configuration for {item_type} using {method}",
        })

    # ------------------------------------------------------------------------------------------
    # Forecast accuracy
    # ------------------------------------------------------------------------------------------
    forecast_accuracy = []
    for cfg_id in ["CFG-000001", "CFG-000002", "CFG-000003"]:
        for cat in categories[:30]:
            for week_offset in range(-12, 0):
                period_end = as_of + timedelta(weeks=week_offset)
                forecast_accuracy.append({
                    "accuracy_id": f"ACC-{len(forecast_accuracy) + 1:06d}",
                    "config_id": cfg_id,
                    "period_start": period_end - timedelta(days=6),
                    "period_end": period_end,
                    "sku": None,
                    "category": cat,
                    "forecast_level": "category",
                    "mape_pct": round(r.gauss(12, 8), 1),
                    "bias_pct": round(r.gauss(2, 5), 1),
                    "rmse": r.randint(50, 200),
                })

    # ------------------------------------------------------------------------------------------
    # Forecast errors (decomposition by driver) and bias by market. Outerwear is planted below.
    # ------------------------------------------------------------------------------------------
    forecast_errors = []
    error_drivers = ["weather", "promotion", "pricing", "new_launch", "store_cluster"]
    for cat in categories[:40]:
        if cat == "Outerwear":
            continue
        for week_offset in range(-12, 0):
            period_end = as_of + timedelta(weeks=week_offset)
            for driver in r.sample(error_drivers, k=r.randint(1, 3)):
                forecast_errors.append({
                    "error_id": f"ERR-{len(forecast_errors) + 1:06d}",
                    "sku": None,
                    "category": cat,
                    "period_start": period_end - timedelta(days=6),
                    "period_end": period_end,
                    "error_driver": driver,
                    "error_units": r.randint(-200, 200),
                    "error_pct": round(r.gauss(0, 5), 1),
                    "explanation": f"{driver} impact on {cat}",
                })

    markets = ["UK North", "UK South", "UK Midlands", "Scotland", "Ireland", "EU Central"]
    forecast_bias = []
    for cat in categories[:30]:
        if cat == "Outerwear":
            continue
        for market in r.sample(markets, k=r.randint(2, 4)):
            for week_offset in range(-12, 0):
                period_end = as_of + timedelta(weeks=week_offset)
                forecast_bias.append({
                    "bias_id": f"BI-{len(forecast_bias) + 1:06d}",
                    "sku": None,
                    "category": cat,
                    "market": market,
                    "period_start": period_end - timedelta(days=6),
                    "period_end": period_end,
                    "bias_pct": round(r.gauss(5, 12), 1),
                    "primary_driver": r.choice(["promotion", "weather", "pricing"]),
                })

    # Outerwear: forecast bias +18% over the last four weeks, mostly weather. UK markets over-forecast; Ireland a little;
    # EU Central barely. Earlier weeks were close to neutral.
    outer_units = {}
    for sku_ in prod:
        if prod[sku_]["category"] == "Outerwear":
            for wk, u, _ in weekly.get(sku_, []):
                outer_units[wk] = outer_units.get(wk, 0) + u
    last4 = [this_monday - timedelta(weeks=n) for n in (4, 3, 2, 1)]
    market_mean = {"UK North": 24.0, "UK South": 21.0, "UK Midlands": 20.0, "Scotland": 26.0, "Ireland": 12.0,
                   "EU Central": 5.0}
    wiggle = [-1.5, 0.5, 1.5, -0.5]
    market_driver = {"UK North": "weather", "UK South": "weather", "UK Midlands": "weather", "Scotland": "weather",
                     "Ireland": "promotion", "EU Central": "pricing"}

    def add_bias(market, wk, pct, driver):
        forecast_bias.append({
            "bias_id": f"BI-{len(forecast_bias) + 1:06d}",
            "sku": None,
            "category": "Outerwear",
            "market": market,
            "period_start": wk,
            "period_end": wk + timedelta(days=6),
            "bias_pct": round(pct, 1),
            "primary_driver": driver,
        })

    for market, mean in market_mean.items():
        for i, wk in enumerate(last4):
            add_bias(market, wk, mean + wiggle[i], market_driver[market])
        for n in range(5, 14):
            add_bias(market, this_monday - timedelta(weeks=n), r.gauss(2.0, 2.0), "promotion")

    driver_pts = {"weather": 9.0, "promotion": 4.0, "pricing": 2.0, "store_cluster": 1.8, "new_launch": 1.2}
    driver_wiggle = [[-0.4, 0.2, 0.3, -0.1], [0.3, -0.2, -0.1, 0.0], [0.1, -0.1, 0.1, -0.1],
                     [-0.1, 0.1, 0.0, 0.0], [0.0, 0.1, -0.1, 0.0]]
    explanation = {
        "weather": "Unseasonably warm September; cold-weather outerwear demand did not start. The August seasonal "
                   "outlook already pointed to a warm autumn and the model has no weather input.",
        "promotion": "Early-autumn outerwear promotion was shortened after the forecast was frozen, but its uplift "
                     "stayed in the baseline.",
        "pricing": "Price increase on core parkas not reflected in price elasticity.",
        "store_cluster": "Northern and Scottish store clusters were forecast on last year's early cold snap.",
        "new_launch": "Autumn launch styles ramped slower than the comparable launches used in the forecast.",
    }
    for i, wk in enumerate(last4):
        actual_units = outer_units.get(wk, 5800)
        for j, (driver, pts) in enumerate(driver_pts.items()):
            p = pts + driver_wiggle[j][i]
            forecast_errors.append({
                "error_id": f"ERR-{len(forecast_errors) + 1:06d}",
                "sku": None,
                "category": "Outerwear",
                "period_start": wk,
                "period_end": wk + timedelta(days=6),
                "error_driver": driver,
                "error_units": int(round(actual_units * p / 100.0)),
                "error_pct": round(p, 1),
                "explanation": explanation[driver],
            })
    for n in range(5, 14):
        wk = this_monday - timedelta(weeks=n)
        for driver in r.sample(error_drivers, k=2):
            forecast_errors.append({
                "error_id": f"ERR-{len(forecast_errors) + 1:06d}",
                "sku": None,
                "category": "Outerwear",
                "period_start": wk,
                "period_end": wk + timedelta(days=6),
                "error_driver": driver,
                "error_units": r.randint(-80, 120),
                "error_pct": round(r.gauss(0.6, 0.5), 1),
                "explanation": f"{driver} impact on Outerwear",
            })

    # ------------------------------------------------------------------------------------------
    # Early sales / alerts / pipeline / promotions
    # ------------------------------------------------------------------------------------------
    early_sales_data = []
    early_sales_alerts = []
    new_products = [p for p in products if p["status"] == "new"][:30]
    for p in new_products:
        launch_date = datetime.fromisoformat(p["launch_date"]).date() if p.get("launch_date") else as_of
        for week_offset in range(1, 6):
            week_date = launch_date + timedelta(weeks=week_offset - 1)
            if week_date > as_of:
                break
            forecast_units = r.randint(100, 800)
            actual_units = max(0, int(forecast_units * r.gauss(0.9, 0.3)))
            early_sales_data.append({
                "sales_id": f"ES-{len(early_sales_data) + 1:06d}",
                "sku": p["sku"],
                "product_name": p["name"],
                "launch_date": launch_date,
                "week_in_launch": week_offset,
                "units_sold": actual_units,
                "units_forecast": forecast_units,
                "velocity_index": round(actual_units / forecast_units, 2) if forecast_units > 0 else 0,
            })
    for p in new_products[:10]:
        early_sales_alerts.append({
            "alert_id": f"ALR-{len(early_sales_alerts) + 1:06d}",
            "sku": p["sku"],
            "alert_type": r.choice(["chase", "cancel"]),
            "trigger_threshold_pct": r.choice([40, 50, 60, 70]),
            "status": r.choice(["active", "inactive"]),
            "created_at": as_of - timedelta(days=r.randint(7, 30)),
        })

    pipeline_products = []
    for p in products[300:330]:
        pipeline_products.append({
            "pipeline_id": f"PL-{len(pipeline_products) + 1:06d}",
            "sku": p["sku"],
            "product_name": p["name"],
            "launch_date": as_of + timedelta(days=r.randint(0, 120)),
            "season": p.get("season") or f"AW{as_of.year % 100}",
            "category": p["category"],
            "supply_risk": r.choice(["low", "medium", "high"]),
            "demand_risk": r.choice(["low", "medium", "high"]),
            "risk_score": round(r.gauss(45, 20), 0),
            "status": r.choice(["draft", "approved", "in_production"]),
        })

    promotion_effects = []
    for cat in categories[:50]:
        for promo_offset in range(-52, 0, 4):
            promo_start = as_of + timedelta(weeks=promo_offset)
            uplift = r.randint(20, 80)
            promotion_effects.append({
                "promo_id": f"PRM-{len(promotion_effects) + 1:06d}",
                "sku": None,
                "category": cat,
                "promo_mechanic": r.choice(["percentage_off", "bundle", "buy_one_get_one"]),
                "period_start": promo_start,
                "period_end": promo_start + timedelta(days=6),
                "uplift_pct": round(uplift, 1),
                "cannibalisation_pct": round(uplift * r.uniform(0.3, 0.6), 1),
                "pull_forward_pct": round(uplift * r.uniform(0.2, 0.4), 1),
            })

    # ------------------------------------------------------------------------------------------
    # Daily orders: actual for the past 400 days (two peaks), forecast for the next 110 days.
    # Online orders in units; Black Friday to Christmas is the peak.
    # ------------------------------------------------------------------------------------------
    channel_share = {"web": 0.55, "app": 0.18, "click_collect": 0.15, "marketplace": 0.12}
    region_share = {"UK South": 0.30, "UK North": 0.22, "UK Midlands": 0.17, "Scotland": 0.08, "Ireland": 0.07,
                    "EU Central": 0.16}
    base_daily = 9500.0
    daily_orders = []
    for day_offset in range(-400, 111):
        d = as_of + timedelta(days=day_offset)
        growth = 1.08 ** (day_offset / 365.0)
        mult = order_multiplier(d)
        for ch, cs in channel_share.items():
            for reg, rs in region_share.items():
                units = base_daily * growth * mult * cs * rs * r.gauss(1.0, 0.05)
                units = max(20, int(round(units)))
                asp = 31.0 * (0.92 if mult >= 1.9 else 1.0) * r.gauss(1.0, 0.03)
                daily_orders.append({
                    "order_date": d,
                    "channel": ch,
                    "region": reg,
                    "units": units,
                    "value_gbp": round(units * asp, 2),
                })

    # ------------------------------------------------------------------------------------------
    # DC inbound/outbound flow (all channels incl. store replenishment), weekly by DC.
    # ------------------------------------------------------------------------------------------
    dc_share = {"DC1": 0.38, "DC2": 0.22, "DC3": 0.20, "DC4": 0.12, "DC5": 0.08}
    dc_region = {s["site_id"]: s["region"] for s in sites if s["type"] == "dc"}
    network_weekly = 170000.0
    dc_flow_forecast = []
    for off in range(-8, 15):
        wk = this_monday + timedelta(weeks=off)
        out_mult = sum(order_multiplier(wk + timedelta(days=i)) for i in range(7)) / 7.0
        in_mult = inbound_multiplier(wk)
        growth = 1.08 ** (off * 7 / 365.0)
        for dc, share in dc_share.items():
            dc_flow_forecast.append({
                "week_start": wk,
                "site_id": dc,
                "region": dc_region[dc],
                "inbound_units": int(network_weekly * share * growth * in_mult * r.gauss(1.0, 0.02)),
                "outbound_units": int(network_weekly * share * growth * (1 + 0.8 * (out_mult - 1)) * r.gauss(1.0, 0.02)),
            })

    # ------------------------------------------------------------------------------------------
    # Lane volume forecast (DC to store lanes as used by transport), weekly across the peak.
    # ------------------------------------------------------------------------------------------
    uk = [x for x in sites if x["type"] == "store" and x["country"] == "GB"]
    region_of = {x["site_id"]: x["region"] for x in uk}
    story_avg = {"DC1-ST215": 755, "DC1-ST150": 685, "DC1-ST207": 681, "DC1-ST214": 672, "DC1-ST151": 654,
                 "DC1-ST148": 582}
    lanes = [f"DC1-{x['site_id']}" for i, x in enumerate(uk) if i % 3 == 0]
    lanes += [f"DC3-{x['site_id']}" for x in uk if x["region"] in ("UK North", "Scotland")]
    lanes = [ln for ln in lanes if ln not in story_avg]
    lanes += sorted(story_avg)
    peak_profile = {-1: 0.80, 0: 1.30, 1: 1.20, 2: 1.10, 3: 1.25, 4: 1.15, 5: 0.65}
    profile_mean = sum(peak_profile[k] for k in range(0, 5)) / 5.0
    labels = {-1: "pre_peak", 0: "black_friday_week", 1: "cyber_week", 2: "december_week_1", 3: "december_week_2",
              4: "christmas_week", 5: "post_christmas"}
    bf = black_friday(as_of.year)
    bf_week = bf - timedelta(days=bf.weekday())
    lane_volume_forecast = []
    for lane in lanes:
        origin, dest = lane.split("-")
        avg = story_avg.get(lane)
        if avg is None:
            avg = r.randint(10, 45)
        for k in range(-1, 6):
            wk = bf_week + timedelta(weeks=k)
            pallets = int(round(avg * peak_profile[k] / profile_mean * r.gauss(1.0, 0.02)))
            lane_volume_forecast.append({
                "lane": lane,
                "week_start": wk,
                "origin_site_id": origin,
                "dest_site_id": dest,
                "region": region_of.get(dest),
                "week_label": labels[k],
                "pallets_forecast": pallets,
                "units_forecast": pallets * r.randint(175, 205),
            })

    # ------------------------------------------------------------------------------------------
    # Long-range volume (quarterly outbound units by DC and scenario, eight years).
    # ------------------------------------------------------------------------------------------
    scen_growth = {"base": 0.035, "upside": 0.07, "downside": -0.01}
    season = [1.28, 0.92, 0.88, 0.92]
    long_range_volume = []
    for q in range(32):
        qstart = this_monday + timedelta(weeks=13 * q)
        for dc, share in dc_share.items():
            for scen, gr in scen_growth.items():
                units = network_weekly * share * 13 * season[q % 4] * (1 + gr) ** (q / 4.0)
                long_range_volume.append({
                    "period_start": qstart,
                    "site_id": dc,
                    "scenario": scen,
                    "units_forecast": int(round(units, -2)),
                    "annual_growth_pct": round(gr * 100, 1),
                })

    # ------------------------------------------------------------------------------------------
    # Returns forecast (weekly, all channels, units arriving at the returns centre).
    # ------------------------------------------------------------------------------------------
    returns_profile = [11900, 12200, 12000, 12400, 13000, 14000, 15500, 18500, 17000, 16000, 15000, 19500, 29500,
                       34000, 27000, 20500, 16500, 14000, 12800, 12400, 12200, 12000, 11800, 11800, 11700, 11700]
    # profile index 0 is the week starting next Monday. Week of 11 January is index 13 (peak).
    returns_forecast = []
    for i, base in enumerate(returns_profile):
        wk = this_monday + timedelta(weeks=i + 1)
        units = int(round(base * r.gauss(1.0, 0.01), -1))
        band = 0.15 if base >= 27000 else 0.08
        returns_forecast.append({
            "week_start": wk,
            "returns_units": units,
            "low_units": int(round(units * (1 - band), -1)),
            "high_units": int(round(units * (1 + band), -1)),
            "returns_value_gbp": int(round(units * 34.0, -2)),
            "driver": "Christmas gift returns and post-Christmas sale" if 11 <= i <= 15 else (
                "Black Friday and Cyber Week orders" if 6 <= i <= 10 else "Baseline returns run-rate"),
        })

    # ------------------------------------------------------------------------------------------
    # Overrides and demand history adjustments
    # ------------------------------------------------------------------------------------------
    forecast_overrides = []
    for cat in categories[:20]:
        week_start = this_monday + timedelta(weeks=1)
        forecast_overrides.append({
            "override_id": f"OVR-{len(forecast_overrides) + 1:06d}",
            "sku": None,
            "category": cat,
            "week_start": week_start,
            "week_end": week_start + timedelta(days=6),
            "override_pct": r.choice([10, 15, 20, 25, -10, -15]),
            "override_units": None,
            "override_type": r.choice(["uplift", "downside"]),
            "reason": r.choice(["Promotion planned", "Seasonal adjustment", "Market event"]),
            "created_at": as_of,
        })

    demand_history_adjustments = []
    for sku in skus[:50]:
        if r.random() < 0.3:
            period_start = as_of - timedelta(weeks=r.randint(4, 26))
            days = r.randint(1, 4) * 7
            demand_history_adjustments.append({
                "adjustment_id": f"ADJ-{len(demand_history_adjustments) + 1:06d}",
                "sku": sku,
                "period_start": period_start,
                "period_end": period_start + timedelta(days=days),
                "stockout_cause": r.choice(["supply delay", "DC allocation", "forecast miss"]),
                "units_lost": r.randint(50, 500),
                "correction_method": "use average of pre/post",
                "stockout_days": days,
                "stores_affected": None,
            })

    return {
        "demand_history": demand_history,
        "forecasts": forecasts,
        "forecast_configs": forecast_configs,
        "forecast_accuracy": forecast_accuracy,
        "forecast_errors": forecast_errors,
        "forecast_bias": forecast_bias,
        "early_sales_data": early_sales_data,
        "early_sales_alerts": early_sales_alerts,
        "pipeline_products": pipeline_products,
        "promotion_effects": promotion_effects,
        "daily_orders": daily_orders,
        "dc_flow_forecast": dc_flow_forecast,
        "lane_volume_forecast": lane_volume_forecast,
        "long_range_volume": long_range_volume,
        "returns_forecast": returns_forecast,
        "forecast_overrides": forecast_overrides,
        "demand_history_adjustments": demand_history_adjustments,
    }
