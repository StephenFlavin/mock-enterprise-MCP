"""Merchandise Financial Planning data: planned buys, weekly sell-through, OTB, forecasts, scenarios, market forecasts."""
from collections import defaultdict
from datetime import timedelta
import statistics

REGIONS = {  # master trading regions with a rough size factor (store count based)
    "UK South": 1.3, "UK North": 1.0, "UK Midlands": 0.9, "Scotland": 0.3,
    "Ireland": 0.25, "EU Central": 0.3, "US": 0.2,
}

# (department, category, base weekly plan units for the UK North-sized region, bias vs plan)
LINES = [
    ("Womenswear", "Dresses", 3000, 1.04), ("Womenswear", "Knitwear", 2600, None), ("Womenswear", "Blouses", 1500, 0.97),
    ("Womenswear", "Tops", 2200, 0.99), ("Womenswear", "Trousers", 2000, 1.00), ("Womenswear", "Outerwear", 1800, None),
    ("Menswear", "Knitwear", 1800, 0.96), ("Menswear", "Shirts", 2400, 1.02), ("Menswear", "Trousers", 2000, 0.99),
    ("Menswear", "Outerwear", 1600, 0.92), ("Menswear", "T-Shirts", 1700, 1.01),
    ("Kids", "Babywear", 2200, 1.00), ("Kids", "Schoolwear", 1900, 1.02), ("Kids", "Outerwear", 1000, 0.97),
    ("Accessories", "Footwear", 2400, 1.01), ("Accessories", "Bags", 900, 0.98), ("Accessories", "Scarves", 800, 0.97),
    ("Accessories", "Jewellery", 1000, 1.00),
    ("Home", "Bedding", 1300, 1.00), ("Home", "Towels", 1100, 0.99), ("Home", "Lighting", 700, 0.98),
    ("Electricals", "Small Appliances", 1200, 1.00),
]
# bands of weeks-ago (k=1 is the latest complete week): (k 1-4 = last fiscal period, k 5-8, k 9+)
STORY_BANDS = {
    ("Womenswear", "Knitwear"): (0.84, 0.93, 1.00),
    ("Womenswear", "Outerwear"): (0.76, 0.88, 0.97),
}
ATHLEISURE = {  # region -> sell-through vs plan for the new Athleisure range (launched 10 weeks ago)
    "UK North": 0.70, "Scotland": 0.72, "UK Midlands": 0.77, "UK South": 0.86,
    "Ireland": 0.79, "EU Central": 0.88, "US": 0.85,
}
SPRING_CATS = ["Dresses", "Tops", "Blouses", "Trousers", "Knitwear", "Outerwear", "Footwear", "Shirts"]
OTB_TOTAL = {"Dresses": 450000, "Tops": 220000, "Blouses": 140000, "Trousers": 260000,
             "Knitwear": 330000, "Outerwear": 190000, "Footwear": 330000, "Shirts": 180000}
# share of each category's budget held back as in-season reserve, per scenario
RESERVE = {
    "base": {c: 0.15 for c in SPRING_CATS},
    "optimistic": {"Dresses": .06, "Tops": .10, "Blouses": .10, "Trousers": .08, "Knitwear": .12, "Outerwear": .14,
                   "Footwear": .08, "Shirts": .08},
    "cautious": {"Dresses": .14, "Tops": .18, "Blouses": .20, "Trousers": .18, "Knitwear": .32, "Outerwear": .35,
                 "Footwear": .15, "Shirts": .14},
}
SCEN = {  # growth, sell-through, markdown, margin, assumptions
    "base": (0.0, 86.0, 11.5, 45.0, "Sales flat on last year; sell-through holds at current run-rate; markdown 11.5% of sales."),
    "optimistic": (5.0, 91.0, 9.0, 47.0, "Sales +5% on last year; autumn knitwear and outerwear weakness is a one-off (warm weather); markdown 9% of sales."),
    "cautious": (-4.0, 80.0, 14.0, 42.5, "Sales -4% on last year; knitwear and outerwear sell-through stays 10-15% behind plan; markdown 14% of sales."),
}


def generate(g):
    r = g.rng
    products = g.master("products")
    cal = {c["date"]: (int(c["fy_period"]), c["season"]) for c in g.master("calendar")}

    # ---- master-derived reference
    cat_info = defaultdict(lambda: defaultdict(list))
    price = defaultdict(list)
    dept_of = {}
    for p in products:
        cat_info[p["category"]][p["country_of_origin"]].append(float(p["unit_cost_gbp"]))
        price[(p["department"], p["category"])].append(float(p["retail_price_gbp"]))
        price[p["category"]].append(float(p["retail_price_gbp"]))
        dept_of.setdefault(p["category"], p["department"])
    avg_price = {k: sum(v) / len(v) for k, v in price.items()}

    # ---- planned buys (generated: every category x origin x season, 2026 and 2027; footwear 2027 is seeded)
    planned_buys = []
    for year in (2026, 2027):
        for cat, by_country in sorted(cat_info.items()):
            if cat == "Footwear" and year == 2027:
                continue
            for country, costs in sorted(by_country.items()):
                for season, period in (("SS", 2), ("AW", 7)):
                    units = r.randrange(2000, 16000, 500)
                    unit_cost = round(sum(costs) / len(costs) * r.uniform(1.12, 1.22), 2)
                    mark = avg_price[cat] / (sum(costs) / len(costs)) * r.uniform(0.97, 1.03)
                    planned_buys.append({
                        "planned_buy_id": f"PB-{len(planned_buys) + 1:06d}", "category": cat,
                        "country_of_origin": country, "buy_year": year, "fy_period": period, "season": season,
                        "planned_units": units, "planned_cost_gbp": round(units * unit_cost, 2),
                        "retail_value_gbp": round(units * unit_cost * mark, 2),
                        "status": r.choice(["received", "confirmed"]) if year == 2026 else r.choice(["draft", "approved"]),
                        "created_at": g.days_ago(r.randint(120, 300)), "updated_at": g.days_ago(r.randint(1, 60)),
                    })

    # ---- weekly sell-through vs plan (26 weeks, k=1 latest complete week)
    sell = []
    line_bias = {}
    for dept, cat, base, bias in LINES:
        line_bias[(dept, cat)] = bias if bias is not None else 1.0

    def add_sell(dept, cat, rng_name, region, k, plan, ratio):
        wk = g.as_of - timedelta(days=7 * k)
        fy_p, season = cal[wk.isoformat()]
        actual = int(round(plan * ratio))
        pp = avg_price[(dept, cat)]
        realise = 1 - 0.2 * max(0.0, 1 - ratio)
        sell.append({
            "sell_through_id": f"ST-{len(sell) + 1:06d}", "department": dept, "category": cat, "range_name": rng_name,
            "region": region, "week_start": wk, "fy_period": fy_p, "season": season,
            "planned_units": plan, "actual_units": actual,
            "planned_retail_gbp": round(plan * pp, 2), "actual_retail_gbp": round(actual * pp * realise, 2),
            "sell_through_pct": round(ratio * 100, 1),
        })

    for dept, cat, base, bias in LINES:
        for region, f in REGIONS.items():
            plan = max(100, int(round(base * f / 100.0)) * 100)
            rf = round(r.uniform(-0.03, 0.03), 2)
            for k in range(1, 27):
                if (dept, cat) in STORY_BANDS:
                    b = STORY_BANDS[(dept, cat)]
                    ratio = b[0] if k <= 4 else b[1] if k <= 8 else b[2]
                    ratio += rf / 2
                else:
                    ratio = bias + rf
                add_sell(dept, cat, "", region, k, plan, round(ratio, 2))
    for cat, base in (("Tops", 2500), ("Trousers", 1800)):
        for region, f in REGIONS.items():
            plan = max(100, int(round(base * f / 100.0)) * 100)
            for k in range(1, 11):
                add_sell("Womenswear", cat, "Athleisure", region, k, plan, ATHLEISURE[region])

    # ---- SKU-level season sell-through (master SKUs of finished / running seasons)
    sku_st = []
    cat_ratio = {"Tops": 0.58, "Footwear": 0.66, "Small Appliances": 0.74}
    for p in products:
        if p["season"] not in ("SS26", "AW26", "CORE"):
            continue
        cat = p["category"]
        weeks = 9 if p["season"] == "AW26" else 26
        recv = r.randrange(300, 3000, 50) if cat != "Small Appliances" else r.randrange(200, 1500, 50)
        if p["status"] in ("clearance", "discontinued"):
            ratio = r.uniform(0.30, 0.52)
        elif p["season"] == "SS26" and cat in cat_ratio:
            ratio = cat_ratio[cat] + r.uniform(-0.05, 0.05)
        elif p["season"] == "AW26":
            ratio = r.uniform(0.28, 0.45)   # 9 weeks into a 26-week season
        else:
            ratio = r.uniform(0.78, 0.96)
        sold = int(recv * ratio)
        sku_st.append({
            "sku": p["sku"], "category": cat, "season": p["season"], "received_units": recv, "units_sold": sold,
            "sell_through_pct": round(sold * 100.0 / recv, 1), "weeks_on_sale": weeks,
            "retail_sales_gbp": round(sold * float(p["retail_price_gbp"]) * 0.88, 2),
        })

    # ---- open to buy: prior and current seasons (spring 2027 is seeded)
    otb = []
    for year, season, status in ((2026, "SS", "closed"), (2026, "AW", "active")):
        for cat in SPRING_CATS:
            total = round(OTB_TOTAL[cat] * r.uniform(0.9, 1.15), -3)
            alloc = round(total * r.uniform(0.88, 0.97), -3)
            otb.append({
                "otb_id": f"OTB-{len(otb) + 1:06d}", "category": cat, "season": season, "buy_year": year,
                "total_budget_gbp": total, "allocated_gbp": alloc, "unallocated_gbp": total - alloc,
                "chase_reserve_gbp": round((total - alloc) * 0.6, -3), "status": status,
                "last_updated_at": g.days_ago(r.randint(20, 120)),
            })

    # ---- scenarios for spring 2027
    scenarios = []
    for stype in ("base", "optimistic", "cautious"):
        growth, st_pct, md, margin, text = SCEN[stype]
        for cat in SPRING_CATS:
            tot = OTB_TOTAL[cat]
            reserve = round(tot * RESERVE[stype][cat], -3)
            weak = cat in ("Knitwear", "Outerwear")
            adj = (-4 if stype == "cautious" else 2 if stype == "optimistic" else 0) if weak else 0
            scenarios.append({
                "scenario_id": f"SC-{900001 + len(scenarios)}", "scenario_name": f"{stype.title()} case",
                "category": cat, "season": "SS", "buy_year": 2027, "scenario_type": stype,
                "allocated_gbp": tot - reserve, "chase_reserve_gbp": reserve,
                "expected_sales_growth_pct": growth + (-6 if weak and stype == "cautious" else 0),
                "expected_sell_through_pct": round(st_pct + adj - (3 if weak else 0), 1),
                "markdown_assumption_pct": md + (3 if weak and stype != "optimistic" else 0),
                "expected_margin_pct": round(margin - (2.5 if weak and stype == "cautious" else 0), 1),
                "assumptions": text, "created_at": g.days_ago(9),
            })

    # ---- markdown and shrink rates: six 4-week blocks, k=1 latest (rates constant over the last three blocks)
    md_cats = ["Knitwear", "Outerwear", "Dresses", "Footwear", "Tops", "Trousers", "Shirts", "Blouses",
               "Small Appliances", "Fragrance", "Bags", "Bedding", "Babywear", "Lighting"]
    sales_w = dict(zip(md_cats, [11.0, 9.0, 8.5, 8.0, 6.5, 6.5, 5.5, 4.0, 7.5, 4.5, 3.0, 4.0, 5.0, 2.5]))
    ly = {"Knitwear": (10.0, 1.4), "Outerwear": (9.0, 1.5), "Dresses": (9.5, 1.3), "Footwear": (8.0, 1.2),
          "Tops": (9.0, 1.4), "Trousers": (8.5, 1.3), "Shirts": (8.0, 1.2), "Blouses": (9.0, 1.3),
          "Small Appliances": (7.0, 1.9), "Fragrance": (6.0, 2.3), "Bags": (7.5, 1.5), "Bedding": (10.5, 1.0),
          "Babywear": (9.0, 1.4), "Lighting": (8.0, 1.1)}
    delta = {"Knitwear": (1.6, 0.0), "Outerwear": (1.8, 0.0), "Dresses": (0.9, 0.0), "Footwear": (0.4, 0.0),
             "Tops": (0.3, 0.0), "Trousers": (0.1, 0.0), "Shirts": (0.0, 0.0), "Blouses": (0.2, 0.0),
             "Small Appliances": (0.0, 0.6), "Fragrance": (0.0, 0.7), "Bags": (0.1, 0.2), "Bedding": (0.2, 0.0),
             "Babywear": (0.0, 0.0), "Lighting": (0.0, 0.1)}
    notes = {"Knitwear": "Temporary: autumn knitwear overbought, early markdowns to clear",
             "Outerwear": "Temporary: warm September left outerwear behind plan, markdown to clear",
             "Dresses": "Temporary: summer dress clearance ran two weeks longer than planned",
             "Small Appliances": "Structural: store theft and unscanned items rising",
             "Fragrance": "Structural: store theft on high-value fragrance gift sets"}
    mdr = []
    for cat in md_cats:
        for k in range(1, 7):
            full = 1.0 if k <= 3 else 0.25
            start = g.as_of - timedelta(days=28 * k)
            fy_p, season = cal[start.isoformat()]
            ly_md, ly_sh = ly[cat]
            mdr.append({
                "rate_id": f"MR-{len(mdr) + 1:06d}", "category": cat, "period_start": start, "fy_period": fy_p,
                "season": season, "net_sales_gbp": round(sales_w[cat] * 100000 * (1 + 0.02 * (k % 3)), -2),
                "markdown_pct": round(ly_md + delta[cat][0] * full, 1), "shrink_pct": round(ly_sh + delta[cat][1] * full, 1),
                "ly_markdown_pct": ly_md, "ly_shrink_pct": ly_sh,
                "markdown_gbp_per_unit": round(avg_price[cat] * (ly_md + delta[cat][0] * full) / 100, 2),
                "write_off_gbp_per_unit": round(avg_price[cat] * (ly_sh + delta[cat][1] * full) / 100 * 0.6, 2),
                "basis": "actual", "driver_note": notes.get(cat, "In line with last year"),
                "recorded_at": start + timedelta(days=29),
            })

    # ---- period forecasts and regional sales forecasts (P8 final, P9 current, P10 draft)
    periods = [(8, "AW", "2026-09-01", "2026-09-30", "final", -1), (9, "AW", "2026-10-01", "2026-10-31", "published", 0),
               (10, "AW", "2026-11-01", "2026-11-30", "draft", 1)]
    plan_m = {"UK North": 6.9, "UK South": 9.8, "UK Midlands": 6.1, "Scotland": 1.7, "Ireland": 1.4,
              "EU Central": 2.0, "US": 1.2}
    var = {"UK North": {8: -5.1, 9: -6.2, 10: -5.4}, "UK South": {8: -1.2, 9: -1.8, 10: -1.5},
           "UK Midlands": {8: -2.0, 9: -2.5, 10: -2.2}, "Scotland": {8: 0.2, 9: 0.6, 10: 0.4},
           "Ireland": {8: 1.0, 9: 1.4, 10: 1.2}, "EU Central": {8: 2.6, 9: 3.1, 10: 2.8}, "US": {8: 2.1, 9: 2.4, 10: 2.2}}
    risk = {"UK North": "Autumn knitwear and outerwear 12-14% behind plan after a mild September; Saturday footfall soft in northern stores; promotional calendar does not start until mid November",
            "UK South": "Outerwear slightly behind plan; otherwise on track",
            "UK Midlands": "Knitwear behind plan; Black Friday week phasing uncertain"}
    cat_var = {"Knitwear": -14.0, "Outerwear": -12.0, "Dresses": -5.0, "Footwear": -2.0, "Tops": -1.0, "Trousers": -2.0,
               "Shirts": 0.5, "Blouses": -1.0, "Small Appliances": 1.0, "Fragrance": 2.0, "Bags": 0.0, "Bedding": 1.0,
               "Babywear": 1.0, "Lighting": 0.0}
    weights = dict(zip(md_cats, [10, 9, 6, 8, 7, 7, 6, 4, 9, 6, 4, 5, 6, 3]))
    wsum = sum(weights.values())
    period_fc, sales_fc = [], []
    for region, pm in plan_m.items():
        for fy_p, season, ps, pe, status, rel in periods:
            plan_v = pm * 1e6 * (1.0 if fy_p == 9 else 0.93 if fy_p == 8 else 1.12)
            tgt = var[region][fy_p]
            fcst_v = plan_v * (1 + tgt / 100)
            to_date = round(fcst_v * 0.15, -3) if fy_p == 9 else (round(fcst_v, -3) if fy_p == 8 else 0)
            fdate = g.days_ago(1 if fy_p != 8 else 7)
            period_fc.append({
                "period_forecast_id": f"PF-{len(period_fc) + 1:06d}", "region": region, "fy_period": fy_p,
                "period_start": ps, "period_end": pe, "forecast_date": fdate,
                "plan_value_gbp": round(plan_v, -3), "actual_to_date_gbp": to_date,
                "forecast_value_gbp": round(fcst_v, -3), "forecast_units": int(fcst_v / 38.5),
                "forecast_vs_plan_pct": round(tgt, 1),
                "forecast_vs_last_year_pct": round(tgt - 0.6, 1) if region == "UK North" else round(tgt + 0.3, 1),
                "key_risks": risk.get(region, "No material risks flagged") if fy_p != 8 else "Period closed",
                "status": status,
            })
            # category split of the same forecast
            scale = 1.0 if region == "UK North" else 0.15
            adj = tgt - sum(weights[c] / wsum * cat_var[c] * scale for c in md_cats)
            for c in md_cats:
                w = weights[c] / wsum
                cv = cat_var[c] * scale + adj
                cplan = plan_v * w
                base = cplan * (1 + cv / 100)
                units = lambda v: int(v / avg_price[c])
                sales_fc.append({
                    "forecast_id": f"FC-{len(sales_fc) + 1:06d}", "region": region, "category": c, "fy_period": fy_p,
                    "season": season, "period_start": ps, "period_end": pe, "plan_gbp": round(cplan, -2),
                    "pessimistic_units": units(base * 0.92), "pessimistic_gbp": round(base * 0.92, -2),
                    "base_forecast_units": units(base), "base_forecast_gbp": round(base, -2),
                    "optimistic_units": units(base * 1.05), "optimistic_gbp": round(base * 1.05, -2),
                    "forecast_date": fdate,
                })

    # ---- market (country) sales forecasts for expansion analysis
    markets = {  # market: (code, mature sales per store GBP m, opening stores per year, online share)
        "Spain": ("ES", 1.55, [4, 8, 12, 16, 20], 0.12), "Germany": ("DE", 1.9, [6, 12, 18, 24, 30], 0.18),
        "France": ("FR", 1.8, [5, 10, 15, 20, 25], 0.15), "Netherlands": ("NL", 1.7, [3, 6, 9, 12, 14], 0.20),
        "Portugal": ("PT", 1.25, [2, 4, 6, 8, 10], 0.10), "Italy": ("IT", 1.6, [4, 7, 11, 15, 19], 0.10),
    }
    ramp = [0.55, 0.78, 0.92, 1.0, 1.0]
    scen_p = {"base": (1.0, 1.0), "downside": (0.78, 0.75), "upside": (1.12, 1.15)}  # (store opening pace, sales density)
    mkt = []
    for market, (code, dens, stores, online) in markets.items():
        for sc, (pace, d) in scen_p.items():
            for y in range(5):
                n = max(1, round(stores[y] * pace))
                sales = n * dens * 1e6 * d * ramp[y] * (1 + online)
                gm = {"base": 44.0, "downside": 40.5, "upside": 45.5}[sc] - (3.0 if y == 0 else 0.0)
                mkt.append({
                    "market_forecast_id": f"MF-{len(mkt) + 1:06d}", "market": market, "country_code": code,
                    "scenario": sc, "year_no": y + 1, "stores_open": n, "sales_gbp": round(sales, -3),
                    "units": int(sales / 31.0), "gross_margin_pct": round(gm, 1),
                    "assumptions": (f"{n} stores trading, sales per mature store GBP {dens * d:.2f}m, "
                                    f"ramp-up {int(ramp[y] * 100)}% of mature, online {int(online * 100)}% on top of stores"),
                    "forecast_date": g.days_ago(14),
                })

    return {
        "planned_buys": planned_buys, "sell_through_data": sell, "sku_sell_through": sku_st, "open_to_buy": otb,
        "markdown_shrink_rates": mdr, "sales_forecasts": sales_fc, "otb_scenarios": scenarios,
        "period_forecasts": period_fc, "market_forecasts": mkt,
    }
