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
    table = {-6: 1.15, -5: 1.3, -4: 1.4, -3: 1.5, -2: 1.6, -1: 1.6, 0: 1.7, 1: 1.6, 2: 1.55, 3: 1.5, 4: 1.2,
             5: 0.9, 6: 1.0, 7: 1.0}
    return table.get(k, 1.0)


def monday(d):
    return d - timedelta(days=d.weekday())


def generate(g):
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
    # Only categories with sales in master carry demand history and forecasts (new master categories such as Backpacks,
    # Kitchenware and Toys hold launches without sales yet), so adding master products does not move the random stream.
    categories = sorted({p["category"] for p in products if p["sku"] in weekly})

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

    # Stockout story: SKU-101904 (style STY-5520) was out for 9 days in 40 stores last month (allocation shortfall,
    # DC held stock). Its forecast was fine: a steady trailing-average forecast, shortfall was supply side (see seed adjustments).

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
        r = g.rng_for("forecast", sku)   # per-SKU stream: new master products never shift other rows
        cat = prod[sku]["category"]
        hist = [u for (wk, u, _) in weekly[sku] if wk < this_monday][-8:]
        recent = sum(hist) / len(hist)
        for off in range(-10, 0):
            wk = this_monday + timedelta(weeks=off)
            a = actual.get((sku, wk))
            if a is None:
                continue
            if sku == "SKU-101904":
                prior = [u for (w2, u, _) in weekly[sku] if wk - timedelta(weeks=6) <= w2 < wk]
                ref = sum(prior) / len(prior)
                add_forecast(sku, wk, "base", ref * r.gauss(1.0, 0.03), wk - timedelta(days=28))
            else:
                add_forecast(sku, wk, "base", a * r.gauss(1.0, 0.10), wk - timedelta(days=28))
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
    r = g.rng_for("configs")
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
            r = g.rng_for("accuracy", cfg_id, cat)
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
        r = g.rng_for("errors", cat)
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
        r = g.rng_for("bias", cat)
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
        r = g.rng_for("outerwear_bias", market)
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
    r = g.rng_for("outerwear_errors")
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
        r = g.rng_for("early", p["sku"])
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
        r = g.rng_for("alert", p["sku"])
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
        r = g.rng_for("pipeline", p["sku"])
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
        r = g.rng_for("promo", cat)
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
    base_daily = 24500.0   # online units a day; master online sales are about 170,000 units a week (scaled x6.8 with the master)
    daily_orders = []
    r = g.rng_for("daily_orders")
    for day_offset in range(-400, 111):
        d = as_of + timedelta(days=day_offset)
        growth = 1.08 ** (day_offset / 365.0)
        mult = order_multiplier(d)
        for ch, cs in channel_share.items():
            for reg, rs in region_share.items():
                units = base_daily * growth * mult * cs * rs * r.gauss(1.0, 0.05)
                units = max(20, int(round(units)))
                asp = 72.0 * (0.92 if mult >= 1.9 else 1.0) * r.gauss(1.0, 0.03)
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
    network_weekly = 510000.0   # all-channel DC outbound units a week = master store + online sales (about 510,000)
    dc_flow_forecast = []
    r = g.rng_for("dc_flow")
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
    # Short-range scenario band on each week's outbound plan: the downside/upside range widens with the horizon
    # (3% plus 0.9 points a week, capped at 15%); past weeks carry no band. No random numbers are drawn.
    for row in dc_flow_forecast:
        ahead = (row["week_start"] - this_monday).days // 7
        band = 0.0 if ahead < 0 else min(0.03 + 0.009 * ahead, 0.15)
        row["outbound_low_units"] = int(round(row["outbound_units"] * (1 - band)))
        row["outbound_high_units"] = int(round(row["outbound_units"] * (1 + band)))

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
        r = g.rng_for("lane", lane)
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
    RETURNS_SCALE = 3.7   # returns follow online units, which are about 3.7x the level the profile was written for
    returns_forecast = []
    r = g.rng_for("returns")
    for i, base in enumerate(returns_profile):
        wk = this_monday + timedelta(weeks=i + 1)
        units = int(round(base * RETURNS_SCALE * r.gauss(1.0, 0.01), -1))
        band = 0.15 if base >= 27000 else 0.08
        returns_forecast.append({
            "returns_week": wk,
            "returns_units": units,
            "low_units": int(round(units * (1 - band), -1)),
            "high_units": int(round(units * (1 + band), -1)),
            "returns_value_gbp": int(round(units * 65.0, -2)),
            "driver": "Christmas gift returns and post-Christmas sale" if 11 <= i <= 15 else (
                "Black Friday and Cyber Week orders" if 6 <= i <= 10 else "Baseline returns run-rate"),
        })

    # ------------------------------------------------------------------------------------------
    # Overrides and demand history adjustments
    # ------------------------------------------------------------------------------------------
    forecast_overrides = []
    for cat in categories[:20]:
        week_start = this_monday + timedelta(weeks=1)
        r = g.rng_for("override", cat)
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
    story_adj_skus = {"PF-220", "K-1700", "SKU-100056", "SKU-100441", "SKU-100539", "SKU-101904"}   # their stockouts are in seed/
    for sku in skus[:50]:
        if sku in story_adj_skus:
            continue
        r = g.rng_for("history_adj", sku)
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


    # ------------------------------------------------------------------------------------------
    # Tidy-up of the generated rows above. These steps draw no random numbers, so every earlier
    # table (and every number the other questions rely on) is unchanged.
    # ------------------------------------------------------------------------------------------
    # Accuracy: fast-mover categories sit near 12% MAPE; slow movers near 22%; after the vendor upgrade reset the
    # outlier-capping default (about eight weeks ago) the promotional categories on CFG-000001 became much worse.
    change_cut = as_of - timedelta(weeks=7)
    bad_cats = {"Outerwear", "Knitwear", "Fragrance", "Footwear", "Dresses", "Lighting"}
    for a in forecast_accuracy:
        m, b = a["mape_pct"], a["bias_pct"]
        if a["config_id"] == "CFG-000003":
            a["mape_pct"] = round(22.4 + (m - 12) * 0.35, 1)
            a["bias_pct"] = round(2.0 + (b - 2) * 0.6, 1)
        elif a["config_id"] == "CFG-000001" and a["category"] in bad_cats and a["period_end"] >= change_cut:
            a["mape_pct"] = round(40 + (m - 12) * 0.5, 1)
            a["bias_pct"] = round(13 + (b - 2) * 0.6, 1)
        else:
            a["mape_pct"] = round(12 + (m - 12) * 0.35, 1)
            a["bias_pct"] = round(2.0 + (b - 2) * 0.6, 1)

    # Home textiles (Bedding, Towels) have been over-forecast for the last twelve weeks.
    textile_bias = {"Bedding": (14.0, "weather"), "Towels": (11.0, "promotion")}
    wiggle12 = [-2.0, 1.5, -1.0, 2.0, 0.5, -1.5, 1.0, -0.5, 2.0, -2.0, 0.0, 0.0]
    for bi in forecast_bias:
        if bi["category"] in textile_bias and bi["sku"] is None:
            k = (as_of - bi["period_end"]).days // 7
            bi["bias_pct"] = round(textile_bias[bi["category"]][0] + wiggle12[k - 1], 1)
            bi["primary_driver"] = textile_bias[bi["category"]][1]

    # Generated stockout adjustments are small; the big ones are the story rows in seed/.
    for adj in demand_history_adjustments:
        adj["units_lost"] = 20 + (adj["units_lost"] - 50) * 100 // 450

    # ------------------------------------------------------------------------------------------
    # Added for the planner stories (everything below draws random numbers after all earlier tables).
    # ------------------------------------------------------------------------------------------
    # Category totals from the SKU history above; used to build earlier years and the longer forecast.
    cat_totals = {}
    for h in demand_history:
        key = (h["category"], h["period_date"])
        cu = cat_totals.setdefault(key, [0, 0.0])
        cu[0] += h["units_sold"]
        cu[1] += h["revenue_gbp"]
    first_week = min(h["period_date"] for h in demand_history)

    # Delisted and newly launched items the stories name; their history comes straight from master sales.
    in_history = {h["sku"] for h in demand_history}
    for sku in ("SKU-100441", "SKU-100028"):
        if sku in weekly and sku not in in_history:
            for wk, units, rev in weekly[sku]:
                demand_history.append({
                    "history_id": f"DH-{len(demand_history) + 1:06d}", "sku": sku, "category": prod[sku]["category"],
                    "period_date": wk, "units_sold": units, "revenue_gbp": round(rev, 2), "demand_type": "actual",
                    "correction_reason": None, "updated_at": as_of})

    winter_cats = {"Outerwear", "Knitwear", "Scarves", "Bedding", "Towels", "Lighting", "Fragrance"}
    summer_cats = {"Dresses", "Blouses", "Shirts", "T-Shirts", "Tops", "Trousers", "Footwear", "Bags", "Jewellery",
                   "Drinkware"}
    season_tab = {
        "winter": [0.95, 0.80, 0.65, 0.55, 0.50, 0.45, 0.45, 0.55, 0.80, 1.00, 1.15, 1.25],
        "summer": [0.90, 1.00, 1.30, 1.45, 1.55, 1.55, 1.45, 1.30, 1.10, 1.00, 0.95, 1.05],
        "school": [0.90, 0.85, 0.90, 0.95, 0.95, 0.95, 1.10, 1.80, 1.50, 1.00, 0.95, 1.00],
        "steady": [1.05, 0.95, 0.95, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.05, 1.15],
    }

    def season_group(cat):
        return "winter" if cat in winter_cats else "summer" if cat in summer_cats else \
            "school" if cat == "Schoolwear" else "steady"

    def seasonal(cat, d):
        tab = season_tab[season_group(cat)]
        v0, v1 = tab[d.month - 1], tab[d.month % 12]
        return v0 + (v1 - v0) * min((d.day - 1) / 30.0, 1.0)

    # Category history for the two years before the SKU history starts, including the cost-of-living squeeze that
    # began 104 weeks ago and lasted 26 weeks (discretionary categories fell most; essentials held up).
    squeeze_pct = {
        "Outerwear": -7, "Knitwear": -6, "Babywear": 1.5, "Small Appliances": -10, "Footwear": -12, "Smart Home": -14,
        "Haircare": -2.5, "Trousers": -8, "Scarves": -10, "Schoolwear": 2.0, "Bodycare": -2, "Fragrance": -16,
        "Personal Care": 0.5, "Skincare": -3, "Nightwear": -4, "Dresses": -15, "Shirts": -7, "Jewellery": -19,
        "Blouses": -11, "Tops": -9, "Lighting": -11, "Audio": -13, "Storage": -6, "Towels": -2, "Cookware": -4,
        "Bedding": -5, "Bags": -14, "Drinkware": -3, "T-Shirts": -8}
    category_history = []
    first_weeks = [this_monday - timedelta(weeks=n) for n in range(26, 0, -1)]   # last 26 weeks set the run-rate
    for cat in categories:
        r = g.rng_for("category_history", cat)
        u8 = [cat_totals.get((cat, w), [0, 0.0]) for w in first_weeks]
        units8 = sum(x[0] for x in u8) / 26.0
        price8 = (sum(x[1] for x in u8) / max(1, sum(x[0] for x in u8))) or 30.0
        anchor = sum(seasonal(cat, w) for w in first_weeks) / 26.0
        for k in range(104, 0, -1):
            wk = first_week - timedelta(weeks=k)
            weeks_back = (this_monday - wk).days // 7
            if 79 <= weeks_back <= 104:
                p = 104 - weeks_back
                sf = min(1.0, (p + 1) / 4.0, (26 - p) / 4.0)
            elif 53 <= weeks_back <= 78:
                sf = 0.75 * (weeks_back - 52) / 26.0
            else:
                sf = 0.0
            yrs = (first_week - wk).days / 365.0
            units = units8 * seasonal(cat, wk) / anchor * (1.06 ** -(yrs + 0.5)) * (1 + squeeze_pct.get(cat, -6) / 100.0 * sf)
            units = max(1, int(round(units * r.gauss(1.0, 0.03))))
            price = price8 * (0.97 ** yrs) * (1 + 0.05 * sf)
            category_history.append({"category": cat, "period_date": wk, "units_sold": units,
                                     "revenue_gbp": round(units * price, 2)})

    # Category forecast, 52 weeks ahead: the SKU forecasts above for weeks 0-11, then seasonal extension.
    base_wk, up_wk, dn_wk = {}, {}, {}
    for f in forecasts:
        if f["forecast_week"] >= this_monday:
            tgt = {"base": base_wk, "upside": up_wk, "downside": dn_wk}[f["forecast_type"]]
            tgt[(f["category"], f["forecast_week"])] = tgt.get((f["category"], f["forecast_week"]), 0) + f["units_forecast"]
    category_forecasts = []
    for cat in categories:
        r = g.rng_for("category_forecast", cat)
        wks = [this_monday + timedelta(weeks=i) for i in range(52)]
        base4 = [base_wk.get((cat, w), 0) for w in wks[:4]]
        anchor = (sum(base4) / 4.0) / (sum(seasonal(cat, w) for w in wks[:4]) / 4.0)
        s_base = sum(base_wk.get((cat, w), 0) for w in wks[:12]) or 1
        ratio_up = sum(up_wk.get((cat, w), 0) for w in wks[:12]) / s_base
        ratio_dn = sum(dn_wk.get((cat, w), 0) for w in wks[:12]) / s_base
        for i, w in enumerate(wks):
            if i < 12:
                b, u, d = base_wk.get((cat, w), 0), up_wk.get((cat, w), 0), dn_wk.get((cat, w), 0)
            else:
                m = anchor * seasonal(cat, w) * (1 + 0.06 * i / 52.0) * r.gauss(1.0, 0.02)
                eb, eu, ed = base_wk.get((cat, w), 0), up_wk.get((cat, w), 0), dn_wk.get((cat, w), 0)
                b, u, d = m + eb, m * ratio_up + eu, m * ratio_dn + ed
            for ftype, val in (("base", b), ("upside", u), ("downside", d)):
                category_forecasts.append({"category": cat, "forecast_week": w, "forecast_type": ftype,
                                           "units_forecast": int(round(val))})

    # Weeks 52-77 (to 18 months ahead): same shape, drawn after everything above so earlier numbers do not move.
    for cat in categories:
        r = g.rng_for("category_forecast_ext", cat)
        wks0 = [this_monday + timedelta(weeks=i) for i in range(12)]
        base4 = [base_wk.get((cat, w), 0) for w in wks0[:4]]
        anchor = (sum(base4) / 4.0) / (sum(seasonal(cat, w) for w in wks0[:4]) / 4.0)
        s_base = sum(base_wk.get((cat, w), 0) for w in wks0) or 1
        ratio_up = sum(up_wk.get((cat, w), 0) for w in wks0) / s_base
        ratio_dn = sum(dn_wk.get((cat, w), 0) for w in wks0) / s_base
        for i in range(52, 78):
            w = this_monday + timedelta(weeks=i)
            m = anchor * seasonal(cat, w) * (1 + 0.06 * i / 52.0) * r.gauss(1.0, 0.02)
            for ftype, val in (("base", m), ("upside", m * ratio_up), ("downside", m * ratio_dn)):
                category_forecasts.append({"category": cat, "forecast_week": w, "forecast_type": ftype,
                                           "units_forecast": int(round(val))})

    # Slow movers: accuracy at store-SKU and cluster level (SKU-101897 matches the allocation story: 11.2% / 15.8%).
    slow_skus = ["SKU-101897", "SKU-102898", "SKU-106034", "SKU-102289", "SKU-104130", "SKU-104053", "SKU-105936",
                 "SKU-105985", "SKU-101414", "SKU-100049", "SKU-105054", "SKU-106083", "SKU-100882"]
    zs = [-0.9, 0.3, 0.7, -0.1]
    for sku in slow_skus:
        for level, mean, bias in (("store_sku", 12.6, 1.2), ("cluster", 17.1, 2.4)):
            for i, off in enumerate((-4, -3, -2, -1)):
                val = (11.2 if level == "store_sku" else 15.8) if sku == "SKU-101897" else mean + zs[i]
                period_end = as_of + timedelta(weeks=off)
                forecast_accuracy.append({
                    "accuracy_id": f"ACC-{len(forecast_accuracy) + 1:06d}", "config_id": "CFG-000003",
                    "period_start": period_end - timedelta(days=6), "period_end": period_end, "sku": sku,
                    "category": prod[sku]["category"], "forecast_level": level, "mape_pct": round(val, 1),
                    "bias_pct": bias, "rmse": 14 if level == "store_sku" else 22})
    # New-product launches (live accuracy of the comparable-product method, CFG-000004). Same launches as the S&OP
    # launch-assumption review (sop get_launch_assumptions_vs_actuals), worst first.
    launch_mape = {"SKU-100259": 56.0, "SKU-101645": 47.4, "SKU-101561": 47.0, "SKU-101057": 46.0, "SKU-101435": 44.0,
                   "SKU-100700": 38.0, "SKU-100847": 33.0, "SKU-100973": 6.0, "SKU-101750": 3.0}
    for sku, mean in launch_mape.items():
        for i, off in enumerate((-4, -3, -2, -1)):
            period_end = as_of + timedelta(weeks=off)
            forecast_accuracy.append({
                "accuracy_id": f"ACC-{len(forecast_accuracy) + 1:06d}", "config_id": "CFG-000004",
                "period_start": period_end - timedelta(days=6), "period_end": period_end, "sku": sku,
                "category": prod[sku]["category"], "forecast_level": "sku", "mape_pct": round(mean + zs[i] * 2, 1),
                "bias_pct": round(mean * 0.7, 1), "rmse": 40})

    # Seasonal bedding throw SKU-104963: forecast at the weekly rate of the inventory story (176 a week in the six
    # northern stores plus 100 a week in the six southern stores), on the seasonal curve peaking in the week of 23
    # November. Appended after the category forecasts and without history rows so no category total, price or other
    # figure moves; no random numbers are drawn.
    throw = "SKU-104963"
    if throw in weekly:
        for off in range(0, 16):
            wk = this_monday + timedelta(weeks=off)
            base = 276.0 * kettle_curve[off]
            for ftype, mult in (("base", 1.0), ("upside", 1.2), ("downside", 0.8)):
                add_forecast(throw, wk, ftype, base * mult, this_monday)

    # SKU-102961 (new Shirts line, no master sales yet): the planning system proposed a 12,000 unit order for it. Its
    # base forecast is flat at about 790 a week, the rate in the supply planning story, so no forecast or history
    # spike explains the order.
    if "SKU-102961" in prod:
        for off in range(0, 12):
            wk = this_monday + timedelta(weeks=off)
            base = 790.0 * (1.0 + 0.012 * math.sin(off * 1.4))
            for ftype, mult in (("base", 1.0), ("upside", 1.2), ("downside", 0.8)):
                add_forecast("SKU-102961", wk, ftype, base * mult, this_monday)

    # Backtests: holdout accuracy per configuration (new-product and slow-mover backtests look better than live).
    fashion = {"Dresses", "Blouses", "Tops", "Shirts", "T-Shirts", "Trousers", "Knitwear", "Outerwear", "Footwear",
               "Scarves", "Nightwear", "Jewellery"}
    cat_items = {}
    for sku in skus:
        cat_items[prod[sku]["category"]] = cat_items.get(prod[sku]["category"], 0) + 1
    forecast_backtests = []

    def add_bt(cfg, level, cat, mape, bias, items):
        forecast_backtests.append({
            "backtest_id": f"BT-{len(forecast_backtests) + 1:06d}", "config_id": cfg, "forecast_level": level,
            "category": cat, "period_start": as_of - timedelta(weeks=52), "period_end": as_of - timedelta(weeks=4),
            "mape_pct": round(mape, 1), "bias_pct": round(bias, 1), "items_backtested": items})

    window_gain = {"Knitwear": -2.6, "Outerwear": -2.2, "Dresses": -1.9, "Nightwear": -1.6, "Scarves": -1.3,
                   "T-Shirts": -1.1, "Blouses": -0.9, "Tops": -0.8, "Shirts": -0.6, "Footwear": -0.5,
                   "Jewellery": -0.3, "Trousers": 0.2}
    for i, cat in enumerate(categories):
        noise = ((i * 7) % 11 - 5) * 0.2
        # A 26-week window helps fashion categories (more with strong seasonality) and hurts stable ones.
        shift = window_gain[cat] if cat in fashion else 0.6 + ((i * 5) % 7) * 0.5 + i * 0.013
        add_bt("CFG-000001", "category", cat, 11.4 + noise, 1.1, cat_items.get(cat, 1))
        add_bt("CFG-000002", "category", cat, 11.4 + noise + shift, 0.9, cat_items.get(cat, 1))
        add_bt("CFG-000003", "category", cat, 20.4 + noise, 1.4, cat_items.get(cat, 1))
    add_bt("CFG-000003", "store_sku", None, 10.8, 0.9, 5200)
    add_bt("CFG-000003", "cluster", None, 14.6, 1.6, 5200)
    add_bt("CFG-000004", "sku", None, 18.4, 3.0, 24)

    # Forecast error by supplier lead time: error grows with the horizon the order has to be placed at, fastest for
    # fashion (trend and weather driven). Bands are four weeks wide and cover the lead times in the product master.
    lt_bands = [("0-4 weeks", 0, 28), ("5-8 weeks", 29, 56), ("9-12 weeks", 57, 84), ("13-16 weeks", 85, 112)]
    lt_slope = {"fashion": [0.92, 1.12, 1.50, 2.00], "other": [0.95, 1.00, 1.16, 1.32]}
    lt_outerwear = [12.4, 15.6, 20.6, 26.8]
    lt_count = {}
    for pr in products:
        if pr["status"] == "discontinued":
            continue
        days = int(pr["lead_time_days"])
        for b, (_, lo, hi) in enumerate(lt_bands):
            if lo <= days <= hi:
                lt_count[(pr["category"], b)] = lt_count.get((pr["category"], b), 0) + 1
    lead_time_accuracy = []
    for i, cat in enumerate(categories):
        seg = "fashion" if cat in fashion else "other"
        base = 11.4 + ((i * 7) % 11 - 5) * 0.2
        for b, (label, lo, hi) in enumerate(lt_bands):
            n = lt_count.get((cat, b), 0)
            if not n:
                continue
            mape = lt_outerwear[b] if cat == "Outerwear" else base * lt_slope[seg][b]
            lead_time_accuracy.append({
                "category": cat, "segment": seg, "lead_time_band": label, "lead_days_from": lo, "lead_days_to": hi,
                "mape_pct": round(mape, 1), "bias_pct": round(mape * 0.12, 1), "skus": n})

    # Pipeline: execution risk follows the status; the risk score is the mean of supply, demand and execution risk
    # (low 20, medium 50, high 80). The SS27 range is rebuilt from master styles that really launch next: Rust Lighting
    # (105-day lead time, supplier at 78% on-time, draft) and Black Fragrance (supplier at 78% on-time, volatile demand)
    # are the risky ones. Supply risk: high if lead time is 90+ days or supplier on-time-in-full is under 80%, medium if
    # the lead time is 45+ days or on-time-in-full is under 90%.
    pts = {"low": 20, "medium": 50, "high": 80}
    exec_by_status = {"draft": "high", "approved": "medium", "in_production": "low", "launched": "low"}
    ss27 = [  # pipeline_id, sku, supply, demand, status
        ("PL-000004", "SKU-102128", "medium", "medium", "approved"),
        ("PL-000005", "SKU-102135", "medium", "medium", "approved"),
        ("PL-000006", "SKU-102905", "low", "high", "approved"),
        ("PL-000007", "SKU-102912", "low", "high", "approved"),
        ("PL-000008", "SKU-105005", "high", "high", "draft"),
        ("PL-000009", "SKU-105012", "high", "high", "draft"),
        ("PL-000019", "SKU-105194", "medium", "low", "in_production"),
        ("PL-000020", "SKU-105201", "medium", "low", "in_production"),
        ("PL-000021", "SKU-105299", "high", "high", "approved"),
        ("PL-000028", "SKU-105306", "high", "high", "approved"),
        ("PL-000029", "SKU-105530", "low", "high", "draft"),
        ("PL-000030", "SKU-105537", "low", "high", "draft"),
    ]
    pl_by_id = {x["pipeline_id"]: x for x in pipeline_products}
    for pid, sku, sup, dem, status in ss27:
        pr = prod[sku]
        pl_by_id[pid].update({"sku": sku, "product_name": pr["name"], "launch_date": date.fromisoformat(pr["launch_date"]),
                              "season": pr["season"], "category": pr["category"], "supply_risk": sup,
                              "demand_risk": dem, "status": status})
    last26 = {this_monday - timedelta(weeks=n) for n in range(1, 27)}
    cat_units, cat_skus = {}, {}
    for h in demand_history:
        if h["period_date"] in last26:
            cat_units[h["category"]] = cat_units.get(h["category"], 0) + h["units_sold"]
            cat_skus.setdefault(h["category"], set()).add(h["sku"])
    for x in pipeline_products:
        x["execution_risk"] = exec_by_status[x["status"]]
        x["risk_score"] = round((pts[x["supply_risk"]] + pts[x["demand_risk"]] + pts[x["execution_risk"]]) / 3.0)
        c = "Bags" if x["category"] == "Backpacks" else x["category"]
        # planned steady-state weekly units: the average SKU in the category over the last 26 weeks
        x["planned_weekly_units"] = int(round(cat_units.get(c, 0) / 26.0 / max(1, len(cat_skus.get(c, ())))))

    # Forecast run effort: weekly production runs for the last 13 weeks, by configuration and level.
    forecast_run_metrics = []
    run_specs = [("CFG-000003", "store_sku", 306400, 95, 48.0, 12.4, 6.0),
                 ("CFG-000003", "cluster", 9800, 7, 3.6, 0.5, 1.5),
                 ("CFG-000001", "sku", 8200, 22, 9.5, 2.1, 4.0),
                 ("CFG-000004", "sku", 40, 2, 0.4, 0.1, 3.0)]
    for cfg, level, series, minutes, cost, gb, hours in run_specs:
        for off in range(-13, 0):
            forecast_run_metrics.append({
                "run_id": f"RUN-{len(forecast_run_metrics) + 1:06d}", "config_id": cfg, "forecast_level": level,
                "run_date": this_monday + timedelta(weeks=off), "series_count": series,
                "run_minutes": minutes, "compute_cost_gbp": cost, "data_volume_gb": gb, "planner_review_hours": hours})

    # Key wholesale accounts: expected orders from sell-through and stock (the same account positions the EDI feed
    # reports). Quarter orders = 13 weeks of sell-through plus the build to a four-week stock cover, less stock
    # already held. Later weeks run at sell-through. No random numbers are drawn here.
    key_accounts = {
        # partner: (sell-through units/week, stock on hand, feed coverage %, feed fresh)
        "PTN-001": (450, 2800, 95, True), "PTN-002": (620, 3500, 90, True), "PTN-003": (380, 2200, 85, False),
        "PTN-004": (540, 3100, 92, True), "PTN-005": (420, 2600, 88, True), "PTN-006": (280, 1800, 75, False),
        "PTN-007": (993, 1233, 71, True), "PTN-008": (565, 1285, 95, True), "PTN-009": (873, 4984, 85, True),
        "PTN-010": (950, 3375, 76, True),
    }
    target_cover_weeks = 4
    key_account_forecasts = []
    for ptn, (sell, stock, cov, fresh) in key_accounts.items():
        total = max(0, sell * (13 + target_cover_weeks) - stock)
        conf = "high" if (cov >= 90 and fresh) else ("medium" if cov >= 80 and fresh else "low")
        band = {"high": 0.08, "medium": 0.15, "low": 0.25}[conf]
        for wk in range(26):
            if wk < 13:
                units = total // 13 + (total % 13 if wk == 0 else 0)
            else:
                units = sell
            key_account_forecasts.append({
                "forecast_id": f"KAF-{len(key_account_forecasts) + 1:05d}",
                "partner_id": ptn,
                "week_start": this_monday + timedelta(weeks=wk),
                "units_forecast": units,
                "low_units": int(round(units * (1 - band))),
                "high_units": int(round(units * (1 + band))),
                "sell_through_units_week": sell,
                "stock_on_hand_units": stock,
                "feed_coverage_pct": cov,
                "data_confidence": conf,
            })

    # Merchandising groups: "toiletries" is how the business talks about the beauty care categories.
    category_groups = [{"group_name": "Toiletries", "category": c} for c in ("Bodycare", "Haircare", "Skincare")]

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
        "category_history": category_history,
        "category_forecasts": category_forecasts,
        "forecast_backtests": forecast_backtests,
        "lead_time_accuracy": lead_time_accuracy,
        "forecast_run_metrics": forecast_run_metrics,
        "key_account_forecasts": key_account_forecasts,
        "category_groups": category_groups,
    }
