"""Costing data: one costing per master SKU (cost and price copied from master), 4-week margin blocks for a
sample of SKUs per department/category, margin bridges that reconcile to those margins, recovery rates,
FOB history by origin and factory quotes. Story overrides are marked STORY."""
import math
import random
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
    "Bags": ("NYLON", "fabric", 0.9), "Footwear": ("LEATHER", "fabric", 0.85),
    "Schoolwear": ("POLYESTER", "fabric", 0.9), "Nightwear": ("POLYESTER", "fabric", 0.9),
}
for c in ["Trousers", "Shirts", "Tops", "T-Shirts", "Blouses", "Dresses", "Babywear", "Towels", "Bedding"]:
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
# STORY: shrink runs highest in small, high-value categories (plan shrink % of revenue), set after the random draws
SHRINK_STORY = {("Beauty", "Fragrance"): 2.6, ("Accessories", "Jewellery"): 2.2, ("Beauty", "Skincare"): 1.9, ("Electricals", "Audio"): 1.7}
# STORY: K-1700 (hot-selling kettle) sells online at a lower net margin (online promotions): extra online markdown points, offset in
# stores so the SKU's total net margin is unchanged
ONLINE_MD = {"K-1700": 5.0}
FORCED_SKUS = ["K-1700", "PF-220", "SKU-101897", "SKU-101904", "SKU-102590", "SKU-100637"]
STORY_COSTING = {  # sku -> overrides
    "SKU-103157": {"quantity_units": 2000, "weekly_demand_units": 333, "late_sales_lost_pct": 78, "notes": "Winter promo line, 6,000 units across the three sizes of STY-7731"},
    "SKU-103164": {"quantity_units": 2000, "weekly_demand_units": 333, "late_sales_lost_pct": 78, "notes": "Winter promo line, 6,000 units across the three sizes of STY-7731"},
    "SKU-103171": {"quantity_units": 2000, "weekly_demand_units": 334, "late_sales_lost_pct": 78, "notes": "Winter promo line, 6,000 units across the three sizes of STY-7731"},
}
# STORY: new 750ml insulated bottle (Drinkware SKU-106307, STY-9501, Supplier A SUP-0004), cost sheet totals the 4.80 quote
BOTTLE = "SKU-106307"
BOTTLE_LINES = [("metal", "304 stainless steel body and base (0.42 kg)", 1.38), ("plastics", "PP lid and silicone seal", 0.30),
                ("trimming", "Powder coat finish", 0.55), ("labour_cut", "Laser cutting", 0.30),
                ("labour_sew", "Welding and assembly", 0.60), ("labour_finish", "Polish and test", 0.30),
                ("packing", "Individual carton", 0.15), ("inbound_freight", "Inland freight to port", 0.25),
                ("tooling", "Tooling amortisation (14,000 over 50,000 units)", 0.28),
                ("overhead", "Overhead and supplier margin", 0.69)]
# STORY: SKU-103157 is on clearance, so it carries heavy markdown (plan markdown moves with it, so variance to plan is unchanged)
STORY_MD_OFFSET = {"SKU-101897": 1.0, "SKU-103157": 9.0, "SKU-103640": 24.0, "SKU-101876": 19.0,
                   "SKU-100077": 70.0, "SKU-100070": 66.6, "SKU-100063": 63.5, "SKU-100056": 61.7, "SKU-100049": 58.4}
EXTRA_SMALL = {"SKU-100063": 1000, "SKU-100056": 1500, "SKU-100049": 2000,
               "SKU-103640": 730, "SKU-101876": 4700}  # last two: the Tops delete candidates of the 06:54:Q2 range review (heavy markdown)  # annual units of the added low-volume lines
# STORY: target margins that make the pipeline and overshirt questions discoverable (no random draws, applied after the row is built)
TARGET_OVERRIDE = {"SKU-102310": 66.0, "SKU-100154": 58.5, "SKU-100161": 58.5, "SKU-100168": 58.5,
                   "SKU-106335": 78.0,   # SKU-106335 = the new overshirt (STY-9505): the linen option misses its target cost
                   "SKU-105005": 66.0}   # SKU-105005 = the riskiest SS27 pipeline item (demand PL-000008): thinnest margin against target
# fabric price per metre used to turn a cost-sheet fabric line into metres per garment
FABRIC_PRICE = {"COTTON": 6.9, "POLYESTER": 5.2, "WOOL": 12.3, "NYLON": 7.4}
# STORY: cotton fabric per metre up 9% (average) over six months while the cotton index rose 4%.
# (supplier, a SKU it supplies, price per metre six months ago, price rise %)
COTTON_STORY = [("SUP-0064", "SKU-100007", 6.20, 16.0), ("SUP-0001", "SKU-100070", 6.50, 13.0), ("SUP-0065", "SKU-100574", 6.40, 9.0),
                ("SUP-0043", "SKU-101624", 6.60, 4.0), ("SUP-0036", "SKU-100637", 6.30, 3.0)]
COTTON_INDEX_RISE = 4.0
# STORY: standard cost updates effective last month: sku -> (% step, cause)
STD_COST_STEP = {"SKU-100175": (11.0, "skincare formulation ingredient price rise"), "SKU-100112": (9.0, "aluminium housing price rise"),
                 "SKU-100224": (10.0, "polyester fabric price rise"), "SKU-100280": (8.0, "copper component price rise")}
# STORY: SS26 Womenswear knitwear (last season's range): supplier price rise % over the six months, by SKU
KNIT_RISE = {"SKU-104291": 12.0, "SKU-104298": 9.0, "SKU-104305": 5.0, "SKU-104879": 3.0, "SKU-104886": 2.0, "SKU-104893": -1.0}
# STORY: PFAS-free waterproofing alternatives live in seed/material_costs.csv
HOLD_PROFILE = {"Womenswear": (9.0, 5.0, 1.0, 7.0), "Menswear": (9.0, 5.0, 1.0, 6.0), "Kids": (9.0, 5.0, 1.0, 7.5),
                "Accessories": (9.0, 4.0, 1.2, 5.0), "Home": (9.0, 7.0, 1.0, 4.0), "Electricals": (9.0, 4.0, 1.5, 6.5), "Beauty": (9.0, 4.0, 1.0, 5.5)}
REPAIR = [  # category, repair cost, days, success %, work
    ("Small Appliances", 15.0, 5, 85.0, "Functional test, element or motor swap, minor parts"), ("Audio", 12.5, 3, 88.0, "Driver or battery replacement, testing"),
    ("Smart Home", 14.0, 4, 82.0, "Firmware reset, board swap, testing"), ("Personal Care", 9.5, 3, 90.0, "Battery and blade replacement, testing"),
    ("Lighting", 8.0, 3, 92.0, "Driver and lamp holder replacement"), ("Storage", 6.0, 4, 95.0, "Hinge and fitting replacement"),
    ("Cookware", 5.5, 4, 94.0, "Handle re-fix and re-polish"), ("Drinkware", 4.5, 4, 93.0, "Lid seal replacement, leak test"),
    ("Footwear", 11.0, 6, 80.0, "Resole and re-stitch"), ("Outerwear", 9.0, 7, 85.0, "Zip, seam seal and re-proofing"),
    ("Bags", 7.5, 6, 88.0, "Strap and zip repair"), ("Knitwear", 6.0, 7, 78.0, "Darning and re-shaping"),
]
PACKAGING = {  # category -> {material: (spec, cost, damage %, recyclability %, recycled content %)}; corrugated is the current pack
    "Small Appliances": {"Corrugated": ("Standard corrugated box with card inserts", 0.85, 2.0, 95.0, 70.0),
                         "Moulded pulp": ("Moulded pulp tray with card sleeve", 0.92, 1.5, 98.0, 95.0),
                         "Recycled plastic": ("Recycled PET clamshell", 0.78, 3.0, 85.0, 80.0)},
    "Cookware": {"Corrugated": ("Corrugated carton with dividers", 0.62, 2.5, 95.0, 65.0),
                 "Moulded pulp": ("Moulded pulp cradle with sleeve", 0.71, 1.9, 98.0, 92.0),
                 "Recycled plastic": ("Recycled PET blister", 0.58, 3.4, 85.0, 78.0)},
    "Lighting": {"Corrugated": ("Corrugated carton with foam-free inserts", 0.74, 3.1, 95.0, 68.0),
                 "Moulded pulp": ("Moulded pulp end caps with sleeve", 0.83, 2.2, 98.0, 94.0),
                 "Recycled plastic": ("Recycled PET tray and sleeve", 0.69, 4.0, 85.0, 75.0)},
}
RECYCLED = [  # material_type, commodity, recycled, virgin, unit, recycled cost, virgin cost, note
    ("fabric", "POLYESTER", "Recycled polyester (rPET) fabric", "Virgin polyester fabric", "metre", 5.50, 5.00, "GRS certification and bottle-flake supply drive the premium"),
    ("fabric", "COTTON", "Recycled cotton blend fabric", "Virgin cotton fabric", "metre", 7.80, 6.50, "Limited post-industrial cotton supply"),
    ("fabric", "NYLON", "Recycled nylon (regenerated) fabric", "Virgin nylon fabric", "metre", 8.90, 7.40, "Regenerated fishing-net yarn, certified"),
    ("packaging", "", "Recycled content corrugated board", "Virgin corrugated board", "unit", 0.92, 0.80, "Certified recycled content and sourcing cost"),
    ("plastic", "", "Recycled polypropylene components", "Virgin polypropylene components", "kg", 1.15, 1.00, "Food-grade and colour-matching processing"),
]


# master products added after the original build (STY-9501..9510): own per-SKU rng and no margin blocks, so adding
# them leaves every other SKU's generated numbers unchanged
ADDED_STYLES = {f"STY-95{n:02d}" for n in range(1, 11)}
# ...of which these have a costing sheet (750ml bottle, lunch box, padded jacket, overshirt); add a style here to cost another one
COSTED_ADDED = {"STY-9501", "STY-9502", "STY-9504", "STY-9505"}


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
    add_costings, add_sheets, add_exposures = [], [], []  # rows for ADDED_STYLES, appended after everything else is built
    exp_n = 1
    for p in products:
        sku, cat, dept = p["sku"], p["category"], p["department"]
        if p["style_id"] in ADDED_STYLES and p["style_id"] not in COSTED_ADDED:
            continue
        rr = random.Random(sku) if p["style_id"] in ADDED_STYLES else r
        total, retail = float(p["unit_cost_gbp"]), float(p["retail_price_gbp"])
        co = p["country_of_origin"]
        prof = list(PROFILES.get(cat) or DEPT_PROFILES.get(dept) or APPAREL)
        prof[1] *= LABOUR_MULT.get(co, 1.2)
        if co in NEAR:
            prof[3] *= 0.5
        prof = [x * rr.uniform(0.92, 1.08) for x in prof]
        sm = sum(prof)
        parts = [round(total * x / sm, 2) for x in prof]
        parts[2] = round(total - sum(parts) + parts[2], 2)
        mat, lab, ovh, frt, tool = parts
        lines = None
        if sku == BOTTLE:
            lines = BOTTLE_LINES
            mat, lab, frt, tool, ovh = 2.23, 1.20, 0.40, 0.28, 0.69
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
        qty = max(300, int(round(moq * rr.randint(2, 6), -2)))
        weekly = int(round(wk)) if wk else max(20, qty // 16)
        if p["style_id"] in ADDED_STYLES:
            weekly = 0  # not launched: no sales yet, so the demand-weighted totals other questions use are unchanged
        row = {
            "costing_id": f"CST-{sku}-V1", "style_id": p["style_id"], "sku": sku, "season": p["season"], "version": 1,
            "origin_country": co, "supplier_id": p["supplier_id"], "factory_id": p["factory_id"], "quantity_units": qty,
            "material_cost_gbp": mat, "labour_cost_gbp": lab, "overhead_cost_gbp": ovh, "freight_cost_gbp": frt,
            "tooling_cost_gbp": tool, "total_cost_gbp": total, "retail_price_gbp": retail, "gross_margin_gbp": gm,
            "gross_margin_pct": round(gm / retail * 100, 1), "target_margin_pct": round(TARGET_MARGIN.get(dept, 58) + rr.uniform(-1.5, 1.5), 1),
            "status": "obsolete" if p["status"] == "discontinued" else "active",
            "notes": f"{p['season']} costing at {qty} units", "category": cat, "department": dept,
            "weekly_demand_units": weekly, "late_sales_lost_pct": float(LOST_PCT.get(dept, 50)),
            "created_at": g.as_of - timedelta(days=rr.randint(30, 120)), "updated_at": g.as_of - timedelta(days=rr.randint(0, 30)),
        }
        row.update(STORY_COSTING.get(sku, {}))
        if sku in TARGET_OVERRIDE:
            row["target_margin_pct"] = TARGET_OVERRIDE[sku]
        if sku == BOTTLE:
            row["target_margin_pct"] = 58.0
            row["notes"] = "Stainless insulated bottle costing; steel body is the main cost"
        added = p["style_id"] in ADDED_STYLES
        (add_costings if added else costings).append(row)
        for i, (t, d, c) in enumerate(lines, 1):
            qty_, unit_, ucost_ = 1, "unit", c
            if t == "fabric" and c > 0:  # fabric is costed per metre: metres per garment = line cost / commodity price per metre
                fp = FABRIC_PRICE.get(COMMODITY.get(cat, ("",))[0], 6.5)
                qty_ = round(c / fp, 2)
                unit_, ucost_ = "metre", round(c / qty_, 3)
            (add_sheets if added else sheets).append({"costing_id": row["costing_id"], "line_no": i, "component_type": t, "description": d, "quantity": qty_,
                           "unit": unit_, "unit_cost_gbp": ucost_, "total_cost_gbp": c, "as_pct_of_total": round(c / total * 100, 1)})
        if cat in COMMODITY and row["status"] == "active":
            code, ctype, el = COMMODITY[cat]
            ln = next((x for x in lines if x[0] == ctype), None)
            if ln:
                (add_exposures if added else exposures).append({"exposure_id": f"EXP-{exp_n:06d}", "sku": sku, "category": cat, "commodity": code,
                                  "exposure_pct": round(ln[2] / total * 100, 1), "exposure_unit": "kg",
                                  "exposure_quantity": (0.42 if sku == BOTTLE else round(ln[2] / 17.0, 2)) if code == "SS304" else round(ln[2] / 9.0, 2),
                                  "elasticity": el, "date_from": g.as_of - timedelta(days=365)})
                exp_n += 1
    cost_by_sku = {c["sku"]: c for c in costings + add_costings}

    # ---- margin sample and blocks
    combos = defaultdict(list)
    for p in products:
        if p["style_id"] in ADDED_STYLES:
            continue
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
    plan_sh.update({k: v for k, v in SHRINK_STORY.items() if k in plan_sh})
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
                    cmd = ONLINE_MD.get(sku, 0) * ((1 if ch == "online" else -(1 - ss) / ss) if sku in ONLINE_MD else 0)
                    md_pct = plan_md[k] + off + cmd + vp[3] * -1 * f
                    sh_pct = plan_sh[k] + vp[4] * -1 * f
                    plan_net = base_gm - plan_md[k] - off - cmd - plan_sh[k]
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

    # STORY: low-volume clearance lines that earn a negative net margin per unit after deep markdown (flagged for range review).
    # SKU-100077 and SKU-100070 are already in the sample (STORY_MD_OFFSET); the other three are added here with their own Random
    # so the shared generator stream (and every other SKU's blocks) is unchanged.
    xr = random.Random(7731)
    for sku, annual in EXTRA_SMALL.items():
        p = by_sku[sku]
        k = (p["department"], p["category"])
        dept, cat = k
        vp = bridge[k]["vs_plan"]
        T_gross = vp[0] + vp[1] + vp[2]
        retail, cost = float(p["retail_price_gbp"]), float(p["unit_cost_gbp"])
        base_gm = (1 - cost / retail) * 100
        off = STORY_MD_OFFSET.get(sku, 0)
        ss = store_share.get(sku, 0.7)
        for j in range(NBLK):
            f = (j - 3) / 13.0
            sf = 1 + 0.25 * math.cos(2 * math.pi * (j % 13) / 13)
            noise = xr.uniform(0.95, 1.05) if 4 <= j <= 12 else 1.0
            start = as_of - timedelta(days=28 * (NBLK - j))
            for ch, share in (("store", ss), ("online", 1 - ss)):
                units = max(5, int(round(annual / 13.0 * share * sf * noise)))
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
        if p["style_id"] not in ADDED_STYLES:
            cat_cost[p["category"]].append(float(p["unit_cost_gbp"]))
    base_outlet = {"Womenswear": 46, "Menswear": 44, "Kids": 42, "Accessories": 40, "Home": 36, "Beauty": 30, "Electricals": 50}
    cat_mult = {"Knitwear": 1.15, "Towels": 0.75, "Bedding": 0.9, "Outerwear": 1.05}
    dec_o, dec_l = [1.0, 0.9, 0.78, 0.62], [1.0, 0.97, 0.92, 0.85]
    cat_dept = {p["category"]: p["department"] for p in products if p["style_id"] not in ADDED_STYLES}
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

    # ---- material costs (every 4 weeks, 7 points = six months)
    materials = [("MAT-POLYESTER-100", "100% polyester", "fabric", "metre", 5.2), ("MAT-WOOL-MERINO", "Merino wool", "fabric", "metre", 12.3),
                 ("MAT-NYLON-SPANDEX", "Nylon spandex blend", "fabric", "metre", 7.4),
                 ("MAT-PACKAGING-BOX", "Corrugated box", "packaging", "unit", 0.42), ("MAT-PACKAGING-PULP", "Moulded pulp", "packaging", "unit", 0.31),
                 ("MAT-DYES-CHEM", "Dyes and chemicals", "dyes_chemicals", "kg", 4.8)]
    sup_ids = [s["supplier_id"] for s in g.master("suppliers")[:10]]
    mats = []
    for mid_, nm, ty, unit, base in materials:
        sup = r.choice(sup_ids)
        for i in range(7):
            cost = base * (1 + r.gauss(0, 0.03))
            mats.append({"material_id": mid_, "material_name": nm, "material_type": ty, "supplier_id": sup, "unit": unit,
                         "cost_per_unit_gbp": round(cost, 3), "index_price_gbp": round(cost * r.uniform(0.97, 1.03), 3),
                         "currency_conversion": 1.0, "recorded_at": g.days_ago(28 * (6 - i)), "notes": ""})
    for sup, _sku, start, pct in COTTON_STORY:
        for i in range(7):
            mats.append({"material_id": "MAT-COTTON-10OZ", "material_name": "10oz cotton fabric", "material_type": "fabric", "supplier_id": sup,
                         "unit": "metre", "cost_per_unit_gbp": round(start * (1 + pct / 100 * i / 6), 3),
                         "index_price_gbp": round(4.80 * (1 + COTTON_INDEX_RISE / 100 * i / 6), 3), "currency_conversion": 1.0,
                         "recorded_at": g.days_ago(28 * (6 - i)), "notes": "Contract price per metre; index is the cotton price per metre equivalent"})

    # ---- supplier cost history: each SKU's own supplier, monthly, cost drifting with the market (one market path per commodity)
    paths = {"COTTON": [100 + COTTON_INDEX_RISE * i / 5 for i in range(6)]}

    def market_path(code):
        if code not in paths:
            m, p = 100.0, []
            for _ in range(6):
                m *= 1 + r.gauss(0.004, 0.01)
                p.append(round(m, 1))
            paths[code] = p
        return paths[code]

    story_sup = {s[0]: s for s in COTTON_STORY}
    hist, seen = [], set()
    story_skus = [cost_by_sku[s[1]] for s in COTTON_STORY]
    sample_skus = story_skus + [c for c in costings if c["status"] == "active"][:40] + [cost_by_sku[s] for s in ("K-1700", "PF-220")]
    for c in sample_skus:
        if c["sku"] in seen:
            continue
        seen.add(c["sku"])
        code = COMMODITY.get(c["category"], ("", "", 0))[0]
        mk = market_path(code) if code else None
        u = r.uniform(0.5, 0.95)
        own_walk, m = [], 100.0
        for _ in range(6):
            m *= 1 + r.gauss(0.004, 0.01)
            own_walk.append(round(m, 1))
        for i in range(6):
            market = mk[i] if mk else own_walk[i]
            if code == "COTTON" and c["supplier_id"] in story_sup:
                sup_idx = 100 + story_sup[c["supplier_id"]][3] * i / 5
            elif code == "COTTON":
                sup_idx = 100 + (market - 100) * u
            else:
                sup_idx = market * r.uniform(0.98, 1.02)
            if c["sku"] == "PF-220" and i >= 4:
                sup_idx = market * 1.03
            sup_idx = round(sup_idx, 1)
            q = c["total_cost_gbp"] * sup_idx / 100
            pdate = g.as_of - timedelta(days=30 * (5 - i))
            period = pdate.strftime("%Y-%m")
            pt = round((sup_idx - 100) / (market - 100) * 100, 1) if abs(market - 100) >= 0.5 else None
            hist.append({"supplier_id": c["supplier_id"], "sku": c["sku"], "period": period, "period_start": pdate.replace(day=1), "quoted_cost_gbp": round(q, 2),
                         "actual_cost_gbp": round(q * r.uniform(0.99, 1.02), 2), "index_price_gbp": market,
                         "market_price_index": market, "supplier_price_index": sup_idx, "pass_through_pct": pt, "notes": "", "commodity": code})

    # STORY: material standard cost updates effective last month (applied to that month and later); every other update is within +/-4%
    periods = sorted({h["period"] for h in hist})
    step_from = periods[-2]
    for h in hist:
        st = STD_COST_STEP.get(h["sku"])
        if st and h["period"] >= step_from:
            h["quoted_cost_gbp"] = round(h["quoted_cost_gbp"] * (1 + st[0] / 100), 2)
            h["actual_cost_gbp"] = round(h["actual_cost_gbp"] * (1 + st[0] / 100), 2)
            if h["period"] == step_from:
                h["notes"] = f"Standard cost updated: {st[1]}"
    # STORY: last season's (SS26) Womenswear knitwear range cost more than costed: SUP-0043 styles up 5-12% on yarn, SUP-0022 styles about flat.
    # Own Random so the shared generator stream (and every other table) is unchanged.
    sr = random.Random(5826)
    for sku, rise in KNIT_RISE.items():
        c = cost_by_sku[sku]
        mk = paths.get("WOOL") or [100.0] * 6
        for i in range(6):
            sup_idx = round(100 + rise * min(1.0, (i + 1) / 3), 1)
            q = c["total_cost_gbp"] * sup_idx / 100
            pdate = g.as_of - timedelta(days=30 * (5 - i))
            period = pdate.strftime("%Y-%m")
            pt = round((sup_idx - 100) / (mk[i] - 100) * 100, 1) if abs(mk[i] - 100) >= 0.5 else None
            hist.append({"supplier_id": c["supplier_id"], "sku": sku, "period": period, "period_start": pdate.replace(day=1), "quoted_cost_gbp": round(q, 2),
                         "actual_cost_gbp": round(q * sr.uniform(0.995, 1.005), 2), "index_price_gbp": mk[i],
                         "market_price_index": mk[i], "supplier_price_index": sup_idx, "pass_through_pct": pt, "notes": "", "commodity": "WOOL"})

    # STORY: homeware supplier costs rise about 2.6% over six months (cost is the largest driver of the 1.1 point margin fall).
    # Own Random so the shared generator stream is unchanged.
    hr = random.Random(7711)
    home_path = [100.0, 100.4, 100.9, 101.4, 102.0, 102.6]
    for (dept, cat), skus in sample.items():
        if dept != "Home":
            continue
        for sku in skus[:3]:
            if sku in seen or sku not in cost_by_sku:
                continue
            seen.add(sku)
            c = cost_by_sku[sku]
            for i in range(6):
                sup_idx = round(home_path[i] + hr.uniform(-0.1, 0.1), 1)
                q = c["total_cost_gbp"] * sup_idx / 100
                pdate = g.as_of - timedelta(days=30 * (5 - i))
                hist.append({"supplier_id": c["supplier_id"], "sku": sku, "period": pdate.strftime("%Y-%m"), "period_start": pdate.replace(day=1),
                             "quoted_cost_gbp": round(q, 2), "actual_cost_gbp": round(q * hr.uniform(0.995, 1.005), 2),
                             "index_price_gbp": 100.0, "market_price_index": 100.0, "supplier_price_index": sup_idx,
                             "pass_through_pct": None, "notes": "", "commodity": COMMODITY.get(cat, ("",))[0]})

    # ---- cost bridges (last six months, by commodity)
    bridges = []
    mat_of = {"COTTON": "MAT-COTTON-10OZ", "WOOL": "MAT-WOOL-MERINO", "POLYESTER": "MAT-POLYESTER-100", "NYLON": "MAT-NYLON-SPANDEX"}
    codes = sorted({v[0] for v in COMMODITY.values()})
    for n, code in enumerate(codes, 1):
        if code == "COTTON":
            tot, mk, prem, mill, frt, lag = 9.0, 4.0, 1.6, 1.4, 1.2, 0.8
            note = "Fabric cost per metre up 9% while the cotton index rose 4%: the rest is supplier premium, mill margin, freight and contract price lag."
        else:
            tot = round(r.uniform(2.0, 7.0), 1)
            mk, prem, mill, frt = round(tot * .55, 1), round(tot * .15, 1), round(tot * .1, 1), round(tot * .1, 1)
            lag = round(tot - mk - prem - mill - frt, 1)
            note = "Routine movement: mostly the market, small premium and freight effects."
        bridges.append({"bridge_id": f"BRG-{n:04d}", "commodity": code, "material_id": mat_of.get(code, ""), "period_start": g.days_ago(168),
                        "period_end": g.as_of, "total_change_pct": tot, "market_pct": mk, "premium_pct": prem, "mill_margin_pct": mill,
                        "freight_pct": frt, "lag_pct": lag, "notes": note})

    # ---- holding cost rates, repair costs, packaging options, recycled premiums
    holds, dept_of = [], {}
    for p in products:
        if p["style_id"] not in ADDED_STYLES:
            dept_of.setdefault(p["category"], p["department"])
    for cat, dept in sorted(dept_of.items()):
        cap, sto, ins, obs = HOLD_PROFILE.get(dept, (9.0, 5.0, 1.0, 6.0))
        if cat == "Outerwear":
            cap, sto, ins, obs = 9.0, 6.5, 1.2, 8.3
        else:
            sto, obs = round(sto + r.uniform(-0.5, 0.5), 1), round(obs + r.uniform(-0.8, 0.8), 1)
        holds.append({"rate_id": f"HLD-{len(holds) + 1:03d}", "category": cat, "capital_cost_pct": cap, "storage_handling_pct": sto, "insurance_pct": ins, "obsolescence_pct": obs,
                      "total_annual_pct": round(cap + sto + ins + obs, 1), "notes": "Annual cost of holding stock as % of inventory value"})
    for p in products:  # categories first seen on the added products: standard rates, no random draws
        if p["category"] not in dept_of:
            dept_of[p["category"]] = p["department"]
            cap, sto, ins, obs = HOLD_PROFILE.get(p["department"], (9.0, 5.0, 1.0, 6.0))
            holds.append({"rate_id": f"HLD-{len(holds) + 1:03d}", "category": p["category"], "capital_cost_pct": cap, "storage_handling_pct": sto,
                          "insurance_pct": ins, "obsolescence_pct": obs, "total_annual_pct": round(cap + sto + ins + obs, 1),
                          "notes": "Annual cost of holding stock as % of inventory value"})
    repairs = [{"repair_id": f"RPR-{i:03d}", "category": c, "repair_cost_gbp": rc, "avg_repair_days": d, "success_rate_pct": sr, "typical_repair_work": w, "notes": ""}
               for i, (c, rc, d, sr, w) in enumerate(REPAIR, 1)]
    pack, pn = [], 1
    for cat, opts in PACKAGING.items():
        for mat, (spec, cost, dmg, rec, rc) in opts.items():
            pack.append({"packaging_id": f"PKG-{pn:04d}", "category": cat, "material": mat, "spec": spec, "unit_cost_gbp": cost,
                         "damage_rate_pct": dmg, "recyclability_pct": rec, "recycled_content_pct": rc, "is_current": mat == "Corrugated",
                         "notes": "Current pack" if mat == "Corrugated" else ""})
            pn += 1
    recs = [{"premium_id": f"RCP-{i:03d}", "material_type": t, "commodity": cm, "recycled_material": rm, "virgin_material": vm, "unit": u,
             "recycled_cost_gbp": rcost, "virgin_cost_gbp": vcost, "notes": n} for i, (t, cm, rm, vm, u, rcost, vcost, n) in enumerate(RECYCLED, 1)]

    return {
        "product_costings": costings + add_costings, "material_costs": mats, "margin_analyses": margins, "cost_variance_drivers": drivers,
        "recovery_routes": [dict(zip(["route_id", "route_name", "description", "category_focus", "min_age_days", "max_age_days", "status"], x)) for x in routes],
        "recovery_rates": rates, "scenario_analyses": scen, "cost_sheet_details": sheets + add_sheets, "commodity_exposures": exposures + add_exposures,
        "supplier_cost_history": hist, "fob_price_history": fob, "origin_cost_quotes": quotes,
        "cost_bridges": bridges, "holding_cost_rates": holds, "repair_costs": repairs, "packaging_options": pack, "recycled_premiums": recs,
        "fix_options": [],  # STORY: seed/fix_options.csv
        "structure_costs": [],  # STORY: seed/structure_costs.csv
        "material_price_breaks": [],  # STORY: seed/material_price_breaks.csv
    }
