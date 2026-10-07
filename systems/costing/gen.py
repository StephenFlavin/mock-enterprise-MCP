"""Costing data: one costing per master SKU (cost and price copied from master), 4-week margin blocks for a
sample of SKUs per department/category, margin bridges that reconcile to those margins, recovery rates,
FOB history by origin and factory quotes. Story overrides are marked STORY."""
import math
from collections import defaultdict
from datetime import timedelta

NBLK = 17  # 4-week blocks, j=16 is the latest complete block; block j-13 is exactly 52 weeks before block j

# material share, labour, overhead, freight, tooling (% of landed cost) by category
PROFILES = {
    "Footwear": (52, 20, 8, 13, 7), "Drinkware": (57, 8, 9, 14, 12), "Cookware": (55, 10, 9, 16, 10),
    "Storage": (55, 10, 9, 16, 10), "Lighting": (55, 10, 9, 16, 10), "Jewellery": (60, 14, 8, 12, 6),
    "Scarves": (60, 14, 8, 12, 6), "Bags": (60, 14, 8, 12, 6), "Towels": (62, 12, 8, 14, 4),
    "Bedding": (62, 12, 8, 14, 4), "Haircare": (45, 6, 12, 15, 2), "Skincare": (45, 6, 12, 15, 2),
    "Bodycare": (45, 6, 12, 15, 2), "Fragrance": (45, 6, 12, 15, 2),
}
DEPT_PROFILES = {"Electricals": (60, 8, 9, 13, 10), "Beauty": (45, 6, 12, 15, 2)}
APPAREL = (58, 18, 8, 12, 4)
LABOUR_MULT = {"VN": 1.0, "CN": 1.15, "IN": 0.9, "BD": 0.8, "TR": 1.5, "PT": 2.2, "IT": 2.6, "PL": 1.9,
               "MX": 1.4, "GB": 3.0, "FR": 3.0, "DE": 3.2}
NEAR = {"PT", "IT", "PL", "TR", "GB", "FR", "DE"}
# category -> material split [(component_type, share, description)]
MAT = {
    "Footwear": [("fabric", .55, "Upper material"), ("other_material", .30, "Sole unit"), ("trimming", .15, "Laces and trims")],
    "Drinkware": [("metal", .62, "Stainless steel body"), ("plastics", .20, "Lid and seal"), ("trimming", .18, "Finish and insulation")],
    "Cookware": [("metal", .62, "Stainless steel body"), ("plastics", .20, "Handles and lids"), ("trimming", .18, "Coating and finish")],
    "Jewellery": [("metal", .8, "Metal and plating"), ("trimming", .2, "Stones and findings")],
    "Lighting": [("metal", .4, "Metal housing"), ("plastics", .4, "Diffuser and plastics"), ("trimming", .2, "Wiring and fittings")],
    "Storage": [("metal", .4, "Metal frame"), ("plastics", .4, "Moulded plastics"), ("trimming", .2, "Fittings")],
}
DEPT_MAT = {
    "Electricals": [("electronics", .45, "Electronics and PCB"), ("metal", .25, "Metal parts"), ("plastics", .30, "Housing")],
    "Beauty": [("other_material", .8, "Formulation and filling"), ("trimming", .2, "Primary packaging")],
}
DEFAULT_MAT = [("fabric", .7, "Main fabric"), ("trimming", .3, "Trims and notions")]
COMMODITY = {  # category -> (commodity code, component_type that carries it, elasticity)
    "Drinkware": ("SS304", "metal", 0.85), "Cookware": ("SS304", "metal", 0.85), "Small Appliances": ("COPPER", "metal", 0.8),
    "Smart Home": ("COPPER", "metal", 0.8), "Audio": ("COPPER", "metal", 0.8), "Personal Care": ("COPPER", "metal", 0.8),
    "Lighting": ("ALUMINIUM", "metal", 0.8), "Storage": ("ALUMINIUM", "metal", 0.8),
    "Knitwear": ("WOOL", "fabric", 0.9), "Scarves": ("WOOL", "fabric", 0.9), "Outerwear": ("POLYESTER", "fabric", 0.9),
    "Bags": ("POLYESTER", "fabric", 0.9), "Footwear": ("LEATHER", "fabric", 0.85),
}
for c in ["Trousers", "Shirts", "Tops", "T-Shirts", "Blouses", "Dresses", "Nightwear", "Babywear", "Schoolwear", "Towels", "Bedding"]:
    COMMODITY[c] = ("COTTON", "fabric", 0.9)
LOST_PCT = {"Womenswear": 70, "Menswear": 65, "Kids": 60, "Accessories": 55, "Home": 40, "Electricals": 45, "Beauty": 30}
TARGET_MARGIN = {"Womenswear": 62, "Menswear": 60, "Kids": 58, "Accessories": 60, "Home": 58, "Electricals": 55, "Beauty": 65}
PLAN_MD = {"Womenswear": 11, "Menswear": 9, "Kids": 8, "Accessories": 7, "Home": 6, "Beauty": 4, "Electricals": 3.5}
PLAN_SH = {"Womenswear": 0.9, "Menswear": 0.9, "Kids": 0.8, "Accessories": 1.2, "Home": 0.5, "Beauty": 1.4, "Electricals": 0.9}

# STORY: planted margin bridges (all in points of revenue)
# vs_plan: price, cost, mix, markdown, shrink      yoy: cost, fx, mix, supplier
STORY_BRIDGE = {
    ("Womenswear", "Knitwear"): {
        "vs_plan": (-0.6, -1.1, -0.3, -0.9, -0.3), "yoy": (-0.9, -0.5, -0.3, -0.3),
        "note_vs_plan": "Cost: yarn price rise on autumn buys. Price: promotional price cuts on core knits. Mix: shift to lower-margin lines. "
                        "Markdown: late clearance of leftover chunky knits, avoidable with earlier action. Shrink: stockroom losses on small items.",
        "note_yoy": "Yarn cost and FX on USD-priced wool blends drive most of the fall."},
    ("Electricals", "Small Appliances"): {
        "vs_plan": (-0.4, -1.4, -0.7, -0.3, -0.1), "yoy": (-1.0, -0.7, -0.3, -0.5),
        "note_vs_plan": "Component cost rises and mix shift to entry price points.",
        "note_yoy": "Buying margin down 2.5 points year on year: factory cost increases 1.0, USD/CNY FX 0.7, mix 0.3, supplier price creep 0.5."},
}
FORCED_SKUS = ["K-1700", "PF-220", "SKU-101897", "SKU-101904", "SKU-102590", "SKU-100637"]
STORY_COSTING = {  # sku -> overrides
    "SKU-103157": {"quantity_units": 2000, "weekly_demand_units": 333, "late_sales_lost_pct": 78, "notes": "Winter promo line, 6,000 units across the three sizes of STY-7731"},
    "SKU-103164": {"quantity_units": 2000, "weekly_demand_units": 333, "late_sales_lost_pct": 78, "notes": "Winter promo line, 6,000 units across the three sizes of STY-7731"},
    "SKU-103171": {"quantity_units": 2000, "weekly_demand_units": 334, "late_sales_lost_pct": 78, "notes": "Winter promo line, 6,000 units across the three sizes of STY-7731"},
}
# STORY: 750ml insulated bottle stand-in (Drinkware SKU-102590), cost sheet totals 20.82
BOTTLE = "SKU-102590"
BOTTLE_LINES = [("metal", "304 stainless steel body and base (0.42 kg)", 7.10), ("plastics", "PP lid and silicone seal", 2.30),
                ("trimming", "Powder coat and vacuum insulation", 2.40), ("labour_cut", "Laser cutting", 0.50),
                ("labour_sew", "Welding and assembly", 0.95), ("labour_finish", "Polish and test", 0.45),
                ("packing", "Gift box", 0.85), ("inbound_freight", "Inbound freight", 2.35), ("tooling", "Tooling amortisation", 1.95),
                ("overhead", "Overhead allocation", 1.97)]
STORY_MD_OFFSET = {"SKU-101897": 1.0}


def generate(g):
    r = g.rng
    products = g.master("products")
    sales = g.master("sales_weekly")
    as_of = g.as_of
    by_sku = {p["sku"]: p for p in products}

    # master sales rates per SKU
    last = max(s["week_start"] for s in sales)
    agg = defaultdict(lambda: [0.0, 0.0, 0.0, 0])
    for s in sales:
        a = agg[s["sku"]]
        if s["week_start"] > (as_of - timedelta(days=56)).isoformat():
            a[0] += float(s["store_units"]) + float(s["online_units"])
            a[2] += float(s["store_units"])
            a[3] += 1
        a[1] += float(s["revenue_gbp"])
    wk_units, store_share, rev52 = {}, {}, {}
    for sku, a in agg.items():
        rev52[sku] = a[1]
        if a[3]:
            wk_units[sku] = a[0] / a[3]
            store_share[sku] = a[2] / a[0] if a[0] else 0.7

    # ---- product_costings + cost sheets + commodity exposures
    costings, sheets, exposures = [], [], []
    exp_n = 1
    for p in products:
        sku, cat, dept = p["sku"], p["category"], p["department"]
        total, retail = float(p["unit_cost_gbp"]), float(p["retail_price_gbp"])
        co = p["country_of_origin"]
        prof = list(PROFILES.get(cat) or DEPT_PROFILES.get(dept) or APPAREL)
        prof[1] *= LABOUR_MULT.get(co, 1.2)
        if co in NEAR:
            prof[3] *= 0.5
        prof = [x * r.uniform(0.92, 1.08) for x in prof]
        sm = sum(prof)
        parts = [round(total * x / sm, 2) for x in prof]
        parts[2] = round(total - sum(parts) + parts[2], 2)
        mat, lab, ovh, frt, tool = parts
        lines = None
        if sku == BOTTLE:
            lines = BOTTLE_LINES
            mat, lab, frt, tool, ovh = 11.80, 1.90, 3.20, 1.95, 1.97
        else:
            mats = MAT.get(cat) or DEPT_MAT.get(dept) or DEFAULT_MAT
            lines = [(t, f"{d}", round(mat * sh, 2)) for t, sh, d in mats]
            lines[0] = (lines[0][0], lines[0][1], round(mat - sum(x[2] for x in lines[1:]), 2))
            lines += [("labour_cut", "Cutting labour", round(lab * .25, 2)), ("labour_sew", "Sewing and assembly labour", round(lab * .55, 2)),
                      ("labour_finish", "Finishing labour", round(lab - round(lab * .25, 2) - round(lab * .55, 2), 2)),
                      ("packing", "Packaging", round(frt * .25, 2)), ("inbound_freight", "Inbound freight", round(frt - round(frt * .25, 2), 2)),
                      ("tooling", "Tooling amortisation", tool), ("overhead", "Overhead allocation", ovh)]
        gm = round(retail - total, 2)
        wk = wk_units.get(sku)
        moq = int(p["moq"] or 500)
        qty = max(300, int(round(moq * r.randint(2, 6), -2)))
        weekly = int(round(wk)) if wk else max(20, qty // 16)
        row = {
            "costing_id": f"CST-{sku}-V1", "style_id": p["style_id"], "sku": sku, "season": p["season"], "version": 1,
            "origin_country": co, "supplier_id": p["supplier_id"], "factory_id": p["factory_id"], "quantity_units": qty,
            "material_cost_gbp": mat, "labour_cost_gbp": lab, "overhead_cost_gbp": ovh, "freight_cost_gbp": frt,
            "tooling_cost_gbp": tool, "total_cost_gbp": total, "retail_price_gbp": retail, "gross_margin_gbp": gm,
            "gross_margin_pct": round(gm / retail * 100, 1), "target_margin_pct": round(TARGET_MARGIN.get(dept, 58) + r.uniform(-1.5, 1.5), 1),
            "status": "obsolete" if p["status"] == "discontinued" else "active",
            "notes": f"{p['season']} costing at {qty} units", "category": cat, "department": dept,
            "weekly_demand_units": weekly, "late_sales_lost_pct": float(LOST_PCT.get(dept, 50)),
            "created_at": g.as_of - timedelta(days=r.randint(30, 120)), "updated_at": g.as_of - timedelta(days=r.randint(0, 30)),
        }
        row.update(STORY_COSTING.get(sku, {}))
        if sku == BOTTLE:
            row["target_margin_pct"] = 58.0
            row["notes"] = "Stainless insulated bottle costing; steel body is the main cost"
        costings.append(row)
        for i, (t, d, c) in enumerate(lines, 1):
            sheets.append({"costing_id": row["costing_id"], "line_no": i, "component_type": t, "description": d, "quantity": 1,
                           "unit": "unit", "unit_cost_gbp": c, "total_cost_gbp": c, "as_pct_of_total": round(c / total * 100, 1)})
        if cat in COMMODITY and row["status"] == "active":
            code, ctype, el = COMMODITY[cat]
            ln = next((x for x in lines if x[0] == ctype), None)
            if ln:
                exposures.append({"exposure_id": f"EXP-{exp_n:06d}", "sku": sku, "category": cat, "commodity": code,
                                  "exposure_pct": round(ln[2] / total * 100, 1), "exposure_unit": "kg",
                                  "exposure_quantity": round(ln[2] / 17.0, 2) if code == "SS304" else round(ln[2] / 9.0, 2),
                                  "elasticity": el, "date_from": g.as_of - timedelta(days=365)})
                exp_n += 1
    cost_by_sku = {c["sku"]: c for c in costings}

    # ---- margin sample and blocks
    combos = defaultdict(list)
    for p in products:
        combos[(p["department"], p["category"])].append(p["sku"])
    sample = {}
    for k, skus in combos.items():
        ranked = sorted(skus, key=lambda s: (-rev52.get(s, 0), s))
        pick = ranked[:8]
        pick += [s for s in FORCED_SKUS if s in skus and s not in pick]
        sample[k] = pick

    bridge = {}  # (dept, cat) -> dict of drivers
    for k in sample:
        if k in STORY_BRIDGE:
            bridge[k] = STORY_BRIDGE[k]
            continue
        a = [round(-r.uniform(0.0, 0.5), 1) for _ in range(3)]
        md, sh = round(r.uniform(-0.5, 0.2), 1), round(r.uniform(-0.2, 0.1), 1)
        tg = round(a[0] + a[1] + a[2], 1)
        w = [r.uniform(0.2, 1) for _ in range(4)]
        y = [round(tg * x / sum(w), 1) for x in w[:3]]
        y.append(round(tg - sum(y), 1))
        bridge[k] = {"vs_plan": (a[0], a[1], a[2], md, sh), "yoy": tuple(y),
                     "note_vs_plan": "Routine variance to plan.", "note_yoy": "Routine year on year movement."}

    margins, mid = [], 1
    plan_md = {k: PLAN_MD.get(k[0], 6) + r.uniform(-1, 1) for k in sample}
    plan_sh = {k: PLAN_SH.get(k[0], 0.9) + r.uniform(-0.2, 0.2) for k in sample}
    for k, skus in sample.items():
        dept, cat = k
        vp, yy = bridge[k]["vs_plan"], bridge[k]["yoy"]
        T_gross = vp[0] + vp[1] + vp[2]      # gross margin hit, points
        for sku in skus:
            p = by_sku[sku]
            retail, cost = float(p["retail_price_gbp"]), float(p["unit_cost_gbp"])
            base_gm = (1 - cost / retail) * 100
            off = STORY_MD_OFFSET.get(sku, 0)
            ss = store_share.get(sku, 0.7)
            wk = wk_units.get(sku) or 60.0
            for j in range(NBLK):
                f = (j - 3) / 13.0
                sf = 1 + 0.25 * math.cos(2 * math.pi * (j % 13) / 13)
                noise = r.uniform(0.95, 1.05) if 4 <= j <= 12 else 1.0
                start = as_of - timedelta(days=28 * (NBLK - j))
                for ch, share in (("store", ss), ("online", 1 - ss)):
                    units = max(5, int(round(wk * 4 * share * sf * noise)))
                    rev = units * retail
                    gm_pct = base_gm + T_gross * f
                    md_pct = plan_md[k] + off + vp[3] * -1 * f
                    sh_pct = plan_sh[k] + vp[4] * -1 * f
                    plan_net = base_gm - plan_md[k] - off - plan_sh[k]
                    net_pct = gm_pct - md_pct - sh_pct
                    margins.append({
                        "margin_id": f"MAR-{mid:06d}", "style_id": p["style_id"], "sku": sku, "category": cat,
                        "period": f"P-{16 - j}", "channel": ch, "volume_units": units, "revenue_gbp": round(rev, 2),
                        "cost_of_goods_gbp": round(rev * (1 - gm_pct / 100), 2), "gross_margin_gbp": round(rev * gm_pct / 100, 2),
                        "gross_margin_pct": round(gm_pct, 2), "markdown_gbp": round(rev * md_pct / 100, 2),
                        "net_margin_gbp": round(rev * net_pct / 100, 2), "net_margin_pct": round(net_pct, 2),
                        "plan_margin_pct": round(plan_net, 3), "variance_pct": round(net_pct - plan_net, 2),
                        "analysed_at": start + timedelta(days=27), "department": dept, "period_start": start,
                        "shrink_gbp": round(rev * sh_pct / 100, 2)})
                    mid += 1

    # ---- cost variance drivers (reconcile to the margin blocks above)
    drivers, vid = [], 1
    for k, b in bridge.items():
        dept, cat = k
        vp, yy = b["vs_plan"], b["yoy"]
        for j in range(11, NBLK):
            f = (j - 3) / 13.0
            start = as_of - timedelta(days=28 * (NBLK - j))
            v = [round(x * f, 2) for x in vp]
            drivers.append({"variance_id": f"VAR-{vid:06d}", "style_id": "", "category": cat, "period": f"P-{16 - j}",
                            "total_variance_pct": round(sum(v), 2), "cost_driver_pct": v[1], "fx_driver_pct": 0.0, "mix_driver_pct": v[2],
                            "supplier_driver_pct": 0.0, "markdown_driver_pct": v[3], "other_driver_pct": 0.0, "notes": b["note_vs_plan"],
                            "analysed_at": start + timedelta(days=28), "department": dept, "period_start": start, "basis": "vs_plan",
                            "price_driver_pct": v[0], "shrink_driver_pct": v[4]})
            vid += 1
        for j in (15, 16):
            start = as_of - timedelta(days=28 * (NBLK - j))
            sc = 1.0
            v = [round(x * sc, 2) for x in yy]
            drivers.append({"variance_id": f"VAR-{vid:06d}", "style_id": "", "category": cat, "period": f"P-{16 - j}",
                            "total_variance_pct": round(sum(v), 2), "cost_driver_pct": v[0], "fx_driver_pct": v[1], "mix_driver_pct": v[2],
                            "supplier_driver_pct": v[3], "markdown_driver_pct": 0.0, "other_driver_pct": 0.0, "notes": b["note_yoy"],
                            "analysed_at": start + timedelta(days=28), "department": dept, "period_start": start, "basis": "yoy",
                            "price_driver_pct": 0.0, "shrink_driver_pct": 0.0})
            vid += 1

    # ---- recovery routes and rates
    routes = [
        ("ROU-RESTOCK", "Restocking", "Return to saleable stock at full price", "Electronics", 0, 60, "active"),
        ("ROU-REFURBISH", "Refurbishing", "Refurbish and resell as grade B", "Electronics", 0, 180, "active"),
        ("ROU-OUTLET", "Outlet", "Sell through outlet stores and sites at a discount", "Apparel", 31, 3650, "active"),
        ("ROU-LIQUIDATION", "Liquidation", "Sell in bulk to a liquidator", "General", 61, 3650, "active"),
        ("ROU-RECYCLING", "Recycling", "Recycle materials", "General", 180, 3650, "active"),
    ]
    bands = [("0-30d", 0, 30), ("31-60d", 31, 60), ("61-180d", 61, 180), ("180d+", 181, 3650)]
    rates = []

    def rate(route, cat, band, pct, handling, days, risk, vol, stype, cost):
        b = next(x for x in bands if x[0] == band)
        rates.append({"route_id": route, "category": cat, "age_band": band, "recovery_rate_pct": pct, "handling_cost_gbp": handling,
                      "time_to_realise_days": days, "risk_rating": risk, "volume_last_6m": vol,
                      "last_updated": g.as_of - timedelta(days=r.randint(1, 30)), "stock_type": stype,
                      "band_min_days": b[1], "band_max_days": b[2], "avg_unit_cost_gbp": cost})

    # STORY: returned electronics accessories (chargers, cables, earbuds)
    E = "Electronics accessories"
    story = {
        "ROU-RESTOCK": [(92, .60, 5, "low", 1400), (80, .80, 10, "low", 760), (38, .90, 25, "medium", 640), (15, 1.20, 40, "high", 210)],
        "ROU-REFURBISH": [(78, 3.20, 28, "medium", 150), (74, 3.20, 30, "medium", 220), (55, 3.40, 35, "medium", 380), (25, 3.60, 50, "high", 90)],
        "ROU-LIQUIDATION": [(38, 1.40, 21, "medium", 120), (40, 1.40, 21, "medium", 200), (58, 1.50, 14, "medium", 130), (32, 1.80, 20, "high", 120)],
        "ROU-RECYCLING": [(6, .40, 40, "low", 40), (6, .40, 40, "low", 60), (6, .40, 40, "low", 60), (8, .40, 45, "low", 300)],
    }
    for rid, vals in story.items():
        for (band, _, _), v in zip(bands, vals):
            rate(rid, E, band, float(v[0]), v[1], v[2], v[3], v[4], "returns", 20.0)

    cat_cost = defaultdict(list)
    for p in products:
        cat_cost[p["category"]].append(float(p["unit_cost_gbp"]))
    base_outlet = {"Womenswear": 46, "Menswear": 44, "Kids": 42, "Accessories": 40, "Home": 36, "Beauty": 30, "Electricals": 50}
    cat_mult = {"Knitwear": 1.15, "Towels": 0.75, "Bedding": 0.9, "Outerwear": 1.05}
    dec_o, dec_l = [1.0, 0.9, 0.78, 0.62], [1.0, 0.97, 0.92, 0.85]
    cat_dept = {p["category"]: p["department"] for p in products}
    for cat, dept in sorted(cat_dept.items()):
        cm = cat_mult.get(cat, r.uniform(0.9, 1.1))
        cost = round(sum(cat_cost[cat]) / len(cat_cost[cat]), 2)
        size = len(cat_cost[cat])
        for i, (band, _, _) in enumerate(bands):
            po = base_outlet.get(dept, 40) * cm * dec_o[i]
            rate("ROU-OUTLET", cat, band, round(po, 1), round(r.uniform(1.2, 2.0), 2), r.randint(25, 55), "low" if i < 2 else "medium", int(size * r.uniform(8, 20)), "aged_stock", cost)
            rate("ROU-LIQUIDATION", cat, band, round(base_outlet.get(dept, 40) * cm * 0.55 * dec_l[i], 1), round(r.uniform(0.5, 1.0), 2), r.randint(10, 25), "medium" if i < 3 else "high", int(size * r.uniform(4, 12)), "aged_stock", cost)
            rate("ROU-RECYCLING", cat, band, round(r.uniform(5, 9), 1), round(r.uniform(0.3, 0.6), 2), r.randint(35, 60), "low", int(size * r.uniform(1, 5)), "aged_stock", cost)

    # ---- FOB history by origin (latest block = average of live costings)
    by_c = defaultdict(list)
    for c in costings:
        if c["status"] == "active":
            by_c[c["origin_country"]].append(c)
    growth_lab = {"VN": 0.09, "BD": 0.11, "KH": 0.065, "CN": 0.05, "IN": 0.06, "TR": 0.12}
    growth_mat = {"VN": 0.01, "BD": 0.015, "KH": 0.01}
    fob = []
    latest = {}
    for co, cs in by_c.items():
        n = len(cs)
        latest[co] = (sum(c["material_cost_gbp"] for c in cs) / n, sum(c["labour_cost_gbp"] for c in cs) / n,
                      sum(c["overhead_cost_gbp"] + c["tooling_cost_gbp"] for c in cs) / n, n, "ordered")
    if "VN" in latest:
        m, l, o, n, _ = latest["VN"]
        latest["KH"] = (m * 0.97, l * 0.88, o, 6, "quoted")
    for co, (m, l, o, n, basis) in latest.items():
        gl, gmat = growth_lab.get(co, 0.03), growth_mat.get(co, 0.015)
        for j in range(NBLK):
            k = (NBLK - 1 - j) / 13.0
            lab, mat = l / (1 + gl * k), m / (1 + gmat * k)
            tot = lab + mat + o
            fob.append({"origin_country": co, "period_start": as_of - timedelta(days=28 * (NBLK - j)), "avg_fob_cost_gbp": round(tot, 2),
                        "avg_labour_cost_gbp": round(lab, 2), "avg_material_cost_gbp": round(mat, 2),
                        "labour_share_pct": round(lab / tot * 100, 1), "basis": basis, "sku_count": n})

    # ---- origin cost quotes
    quotes, qn = [], 1
    grp = defaultdict(list)
    for c in costings:
        if c["status"] == "active":
            grp[(c["origin_country"], c["category"], c["factory_id"], c["supplier_id"])].append(c)
    lead = {p["sku"]: int(p["lead_time_days"] or 60) for p in products}
    for (co, cat, fac, sup), cs in sorted(grp.items()):
        n = len(cs)
        quotes.append({"quote_id": f"QTE-{qn:06d}", "origin_country": co, "category": cat, "factory_id": fac, "supplier_id": sup,
                       "quote_status": "current",
                       "fob_cost_gbp": round(sum(c["material_cost_gbp"] + c["labour_cost_gbp"] + c["overhead_cost_gbp"] + c["tooling_cost_gbp"] for c in cs) / n, 2),
                       "freight_cost_gbp": round(sum(c["freight_cost_gbp"] for c in cs) / n, 2),
                       "lead_time_days": int(sum(lead[c["sku"]] for c in cs) / n), "style_count": len({c["style_id"] for c in cs}),
                       "quoted_at": g.as_of - timedelta(days=r.randint(10, 60)), "notes": "Live costed factory"})
        qn += 1
    vn = [q for q in quotes if q["origin_country"] == "VN" and q["category"] == "Footwear"]
    if vn:
        avg_f = sum(q["fob_cost_gbp"] for q in vn) / len(vn)
        avg_fr = sum(q["freight_cost_gbp"] for q in vn) / len(vn)
        for mult, nm in ((1.045, "Prospective factory, Central Java"), (1.06, "Prospective factory, Banten"), (1.03, "Prospective factory, East Java")):
            quotes.append({"quote_id": f"QTE-{qn:06d}", "origin_country": "ID", "category": "Footwear", "factory_id": "", "supplier_id": "",
                           "quote_status": "prospective", "fob_cost_gbp": round(avg_f * mult, 2), "freight_cost_gbp": round(avg_fr + 0.25, 2),
                           "lead_time_days": 95, "style_count": 4, "quoted_at": g.as_of - timedelta(days=21),
                           "notes": f"{nm}, RFQ quote, not yet onboarded"})
            qn += 1

    # ---- scenarios
    scen = []
    types = ["freight_mode", "volume", "material_cost"]
    names = {"freight_mode": "Air vs sea shipping", "volume": "Higher order volume for scale", "material_cost": "Material cost increase"}
    emp = [e["employee_id"] for e in g.master("employees")[:20]]
    sid = 1
    for c in costings[:30] + [cost_by_sku[s] for s in STORY_COSTING]:
        for t in types:
            ci = round(r.uniform(-0.5, 2.0), 2)
            scen.append({"scenario_id": f"SCN-{sid:06d}", "scenario_name": names[t], "base_costing_id": c["costing_id"], "scenario_type": t,
                         "assumption_detail": f"Scenario: {t}", "cost_impact_gbp": ci, "margin_impact_gbp": -ci,
                         "margin_impact_pct": round(-ci / c["retail_price_gbp"] * 100, 1), "volume_impact": r.randint(-300, 1200),
                         "financial_impact_gbp": round(ci * c["quantity_units"], 2), "created_by": r.choice(emp),
                         "created_at": g.as_of - timedelta(days=r.randint(0, 30))})
            sid += 1

    # ---- material costs (weekly, 12 weeks)
    materials = [("MAT-COTTON-10OZ", "10oz cotton fabric", "fabric", "metre", 6.5), ("MAT-POLYESTER-100", "100% polyester", "fabric", "metre", 5.2),
                 ("MAT-WOOL-MERINO", "Merino wool", "fabric", "metre", 12.3), ("MAT-NYLON-SPANDEX", "Nylon spandex blend", "fabric", "metre", 7.4),
                 ("MAT-PACKAGING-BOX", "Corrugated box", "packaging", "unit", 0.42), ("MAT-PACKAGING-PULP", "Moulded pulp", "packaging", "unit", 0.31),
                 ("MAT-DYES-CHEM", "Dyes and chemicals", "dyes_chemicals", "kg", 4.8)]
    sup_ids = [s["supplier_id"] for s in g.master("suppliers")[:10]]
    mats = []
    for mid_, nm, ty, unit, base in materials:
        sup = r.choice(sup_ids)
        for w in range(12):
            cost = base * (1 + r.gauss(0, 0.03))
            mats.append({"material_id": mid_, "material_name": nm, "material_type": ty, "supplier_id": sup, "unit": unit,
                         "cost_per_unit_gbp": round(cost, 3), "index_price_gbp": round(cost * r.uniform(0.97, 1.03), 3),
                         "currency_conversion": 1.0, "recorded_at": g.days_ago(w * 7), "notes": ""})

    # ---- supplier cost history: each SKU's own supplier, monthly, cost drifting with the market
    hist = []
    sample_skus = [c for c in costings if c["status"] == "active"][:40] + [cost_by_sku[s] for s in ("K-1700", "PF-220")]
    for c in sample_skus:
        market = 100.0
        for i in range(6):
            market *= 1 + r.gauss(0.004, 0.01)
            sup_idx = market * (1.03 if c["sku"] == "PF-220" and i >= 4 else r.uniform(0.98, 1.02))
            q = c["total_cost_gbp"] * market / 100
            period = (g.as_of - timedelta(days=30 * (5 - i))).strftime("%Y-%m")
            hist.append({"supplier_id": c["supplier_id"], "sku": c["sku"], "period": period, "quoted_cost_gbp": round(q, 2),
                         "actual_cost_gbp": round(q * r.uniform(0.99, 1.02), 2), "index_price_gbp": round(market, 1),
                         "market_price_index": round(market, 1), "supplier_price_index": round(sup_idx, 1),
                         "pass_through_pct": round(sup_idx / market * 100, 1), "notes": ""})

    return {
        "product_costings": costings, "material_costs": mats, "margin_analyses": margins, "cost_variance_drivers": drivers,
        "recovery_routes": [dict(zip(["route_id", "route_name", "description", "category_focus", "min_age_days", "max_age_days", "status"], x)) for x in routes],
        "recovery_rates": rates, "scenario_analyses": scen, "cost_sheet_details": sheets, "commodity_exposures": exposures,
        "supplier_cost_history": hist, "fob_price_history": fob, "origin_cost_quotes": quotes,
    }
