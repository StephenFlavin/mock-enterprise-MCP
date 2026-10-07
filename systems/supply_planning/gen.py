"""Supply planning data: item planning parameters, order proposals, supply plans, gaps, supplier terms,
origin lead times, fabric and material requirements, space plans and component buy terms.

Weekly demand per SKU is on the same scale as the inventory system (network demand = DC stock / cover), so cover
figures agree between systems. Seed CSVs plant the question stories; everything else is quiet and internally
consistent (pack sizes sensible, quantities equal the planning formula, stock healthy).
"""
import math
import random
from collections import defaultdict
from datetime import timedelta

# Quoted vs actual supplier lead time in days (two-year view, same basis as the purchasing system).
SUPPLIER_LEAD = {
    "SUP-0001": (76.2, 76.6), "SUP-0002": (67, 80.6), "SUP-0003": (77.8, 73.6), "SUP-0004": (17.3, 30.1),
    "SUP-0005": (22.4, 30.2), "SUP-0006": (85, 74.2), "SUP-0007": (75, 31.3), "SUP-0008": (83.8, 77.8),
    "SUP-0010": (79.9, 82.6), "SUP-0011": (68.8, 81.9), "SUP-0012": (21, 31.9), "SUP-0013": (72.1, 82.1),
    "SUP-0014": (67, 32.1), "SUP-0015": (21, 30.6), "SUP-0016": (97.8, 67.7), "SUP-0017": (91.9, 86.4),
    "SUP-0018": (96.2, 74.7), "SUP-0020": (89.1, 75.4), "SUP-0021": (92.6, 82.6), "SUP-0022": (22.6, 32.4),
    "SUP-0023": (68.4, 79.7), "SUP-0024": (72.3, 89.9), "SUP-0025": (17.5, 31), "SUP-0026": (20.7, 30.2),
    "SUP-0027": (60.4, 79.2), "SUP-0028": (63.1, 76.2), "SUP-0030": (23.3, 30.7), "SUP-0031": (81, 69.7),
    "SUP-0032": (58.4, 74.2), "SUP-0033": (24.6, 32.4), "SUP-0034": (77, 76.3), "SUP-0035": (74.3, 72.6),
    "SUP-0036": (22.6, 31.5), "SUP-0037": (21, 29.4), "SUP-0038": (71.2, 82.5), "SUP-0039": (18.9, 30.4),
    "SUP-0040": (17.4, 29.9), "SUP-0041": (80.4, 81.1), "SUP-0042": (51.3, 30), "SUP-0043": (65.2, 80.6),
    "SUP-0044": (17.8, 29.8), "SUP-0045": (89.8, 76.7), "SUP-0046": (101.3, 72.2), "SUP-0047": (18.9, 31.6),
    "SUP-0048": (79.9, 87.4), "SUP-0049": (95.4, 32), "SUP-0050": (83.1, 84.3), "SUP-0051": (64.4, 84.4),
    "SUP-0052": (73.6, 91.1), "SUP-0053": (71.3, 73.1), "SUP-0054": (22.2, 30.3), "SUP-0055": (76.6, 78.6),
    "SUP-0056": (90, 86.5), "SUP-0057": (61.4, 70.6), "SUP-0058": (17.9, 29.6), "SUP-0059": (83.4, 76.4),
    "SUP-0060": (20.1, 31.2), "SUP-0061": (23.3, 29.1), "SUP-0062": (80.4, 78.3), "SUP-0063": (91.3, 85.6),
    "SUP-0064": (82.9, 78.4), "SUP-0065": (22.4, 31.7), "SUP-0066": (88.3, 80), "SUP-0067": (24.6, 29.9),
    "SUP-0068": (24.6, 29.9), "SUP-0069": (87.2, 80.5), "SUP-0070": (69.4, 30.1), "SUP-0071": (24.9, 30.1),
    "SUP-0072": (14, 30.4), "SUP-0073": (89.8, 76.5), "SUP-0074": (70.1, 72.9), "SUP-0075": (22.9, 29.6),
    "SUP-0076": (83, 75.4), "SUP-0077": (52.8, 70), "SUP-0078": (45, 75.9), "SUP-0079": (20.1, 29.4),
    "SUP-0080": (68.6, 79.3),
}

# Weekly network demand fixed to the inventory system's figures for the SKUs its stories are built on.
DEMAND_OVERRIDE = {
    # SUP-0068 (beauty, the largest packaging-type supplier): all its SKUs
    "SKU-104536": 5750.4, "SKU-101022": 45.6, "SKU-105390": 555.8, "SKU-104522": 125.2, "SKU-101967": 1921.0,
    "SKU-101960": 1037.4, "SKU-105397": 359.8, "SKU-101974": 35.9, "SKU-100252": 291.5, "SKU-100490": 850.0,
    "SKU-100245": 529.0, "SKU-104529": 509.8, "SKU-100182": 654.7, "SKU-100497": 396.7, "SKU-105383": 1264.7,
    "SKU-100175": 785.5, "SKU-100504": 396.1, "SKU-100189": 309.6, "SKU-101015": 15.5, "SKU-100238": 18.4,
    "SKU-101029": 14.9,
    # Vietnam-made lines with the lowest cover
    "SKU-101260": 2578.4, "SKU-102884": 3322.7, "SKU-105964": 664.3, "SKU-100280": 1889.1, "SKU-103521": 2300.2,
    "SKU-101722": 1097.4,
    # order proposal story and similar-issue items
    "SKU-102961": 789.5, "SKU-106251": 1521.0, "SKU-102352": 1388.6, "SKU-102338": 2187.9,
}
# Network available units (DCs and stores) the inventory system shows for the same SKUs.
STOCK_OVERRIDE = {
    "SKU-104536": 13801, "SKU-101022": 142, "SKU-105390": 2112, "SKU-104522": 576, "SKU-101967": 9990,
    "SKU-101960": 5913, "SKU-105397": 3269, "SKU-101974": 340, "SKU-100252": 2895, "SKU-100490": 8649,
    "SKU-100245": 5512, "SKU-104529": 5337, "SKU-100182": 8290, "SKU-100497": 5117, "SKU-105383": 16713,
    "SKU-100175": 10598, "SKU-100504": 5737, "SKU-100189": 4725, "SKU-101015": 3787, "SKU-100238": 8910,
    "SKU-101029": 8816,
    "SKU-101260": 4641, "SKU-102884": 7642, "SKU-105964": 1926, "SKU-100280": 6422, "SKU-103521": 9200,
    "SKU-101722": 5048,
    "SKU-102961": 5092, "SKU-106251": 10831, "SKU-102352": 10088, "SKU-102338": 12910,
}
# Long-tail make-to-order candidates: stay stocked until the planner switches them.
LONG_TAIL_CANDIDATES = {"SKU-101253", "SKU-105054", "SKU-101617", "SKU-102387", "SKU-103038"}

PACKS = [6, 12, 24, 50, 100, 250, 500, 1000, 2000]
APPAREL = ["Blouses", "Tops", "Dresses", "Knitwear", "Trousers", "Shirts", "Outerwear", "T-Shirts", "Nightwear",
           "Babywear", "Schoolwear", "Scarves"]

# Freight £/unit by origin country: (sea or road, air)
FREIGHT = {"CN": (1.10, 4.10), "BD": (1.30, 4.60), "VN": (1.25, 4.20), "IN": (1.20, 4.30), "TR": (0.70, 2.60),
           "PT": (0.45, 2.40), "PL": (0.40, 2.30), "IT": (0.45, 2.30), "FR": (0.40, 2.30), "DE": (0.40, 2.20),
           "MX": (1.05, 3.90), "GB": (0.25, 1.80), "NL": (0.35, 2.10), "US": (0.95, 3.80)}

# Origins: port, country, region, mode, transit days, variability days, £/unit
ORIGINS = [
    ("CNSHA", "CN", "Asia", "sea", 32, 5, 1.10), ("CNSHA", "CN", "Asia", "air", 6, 1, 4.10),
    ("CNNGB", "CN", "Asia", "sea", 33, 5, 1.10), ("CNYTN", "CN", "Asia", "sea", 35, 6, 1.10),
    ("CNYTN", "CN", "Asia", "air", 6, 1, 4.10), ("BDCGP", "BD", "Asia", "sea", 40, 8, 1.30),
    ("BDCGP", "BD", "Asia", "air", 7, 2, 4.60), ("VNSGN", "VN", "Asia", "sea", 35, 6, 1.25),
    ("VNSGN", "VN", "Asia", "air", 7, 2, 4.20), ("INNSA", "IN", "Asia", "sea", 30, 7, 1.20),
    ("INNSA", "IN", "Asia", "air", 6, 2, 4.30), ("TRMER", "TR", "Europe", "sea", 12, 3, 0.70),
    ("TRMER", "TR", "Europe", "air", 4, 1, 2.60), ("PTLEI", "PT", "Europe", "road", 4, 1, 0.45),
    ("PTLEI", "PT", "Europe", "sea", 6, 2, 0.35), ("DEHAM", "DE", "Europe", "road", 3, 1, 0.40),
    ("NLRTM", "NL", "Europe", "road", 2, 1, 0.35), ("USNYC", "US", "Americas", "sea", 14, 4, 0.95),
    ("USNYC", "US", "Americas", "air", 4, 1, 3.80), ("MXZLO", "MX", "Americas", "sea", 24, 5, 1.05),
    ("MXZLO", "MX", "Americas", "air", 5, 1, 3.90),
]
# Destination DC offsets in days by origin region: DC1, DC2, DC3, DC4 (Venlo)
DEST_OFFSET = {"Asia": {"DC1": 0, "DC2": 0, "DC3": 1, "DC4": 2},
               "Europe": {"DC1": 0, "DC2": 0, "DC3": 1, "DC4": -1},
               "Americas": {"DC1": 0, "DC2": 0, "DC3": 1, "DC4": 3}}

# Pallet positions by category in DC1 (matches the warehouse system's current occupancy) and their weekly growth.
DC1_POSITIONS = {
    "Small Appliances": 128, "Smart Home": 66, "Cookware": 28, "Outerwear": 58, "Audio": 23, "Bedding": 25,
    "Lighting": 27, "Personal Care": 25, "Towels": 27, "Drinkware": 8, "Fragrance": 25, "Blouses": 18,
    "Babywear": 43, "Bags": 27, "Footwear": 60, "Scarves": 27, "Schoolwear": 26, "Tops": 16, "Nightwear": 28,
    "Knitwear": 64, "Haircare": 55, "Storage": 41, "Dresses": 31, "Shirts": 35, "T-Shirts": 9, "Skincare": 29,
    "Jewellery": 30, "Bodycare": 28, "Trousers": 37,
}
DC1_GROWTH = {"Small Appliances": 5.0, "Smart Home": 3.3, "Cookware": 1.5, "Outerwear": 1.0, "Audio": 1.0,
              "Bedding": 1.0, "Lighting": 0.8, "Personal Care": 0.8, "Towels": 0.5, "Drinkware": 0.5, "Fragrance": 0.3}

# Calendar-month production index for leather (autumn/winter lines are cut Feb-May)
LEATHER_INDEX = [1.05, 1.30, 1.55, 1.60, 1.40, 1.00, 0.70, 0.65, 0.80, 0.85, 0.80, 0.75]
GENERAL_INDEX = [0.95, 1.05, 1.10, 1.10, 1.05, 1.00, 0.95, 0.95, 1.05, 1.10, 1.05, 0.95]


def generate(g):
    r = g.rng
    rd = random.Random(20261005)  # separate stream for the planning tables below

    products = g.master("products")
    pmap = {p["sku"]: p for p in products}
    suppliers = g.master("suppliers")
    smap = {s["supplier_id"]: s for s in suppliers}
    sites = [s for s in g.master("sites") if s["type"] == "dc"]
    dc_ids = [s["site_id"] for s in sites]

    # ---------- weekly demand per SKU ----------
    dc_avail = defaultdict(int)
    dc_onhand_cat = defaultdict(lambda: defaultdict(int))
    for d in g.master("dc_stock"):
        dc_avail[d["sku"]] += int(d["available"])
        if d["sku"] in pmap:
            dc_onhand_cat[d["site_id"]][pmap[d["sku"]]["category"]] += int(d["on_hand"])
    sales = defaultdict(list)
    for s in g.master("sales_weekly"):
        sales[s["sku"]].append((s["week_start"], int(s["store_units"]) + int(s["online_units"])))
    chain = {}
    for k, v in sales.items():
        v.sort()
        last = v[-8:]
        chain[k] = sum(x[1] for x in last) / len(last)

    demand = {}
    for p in products:
        sku = p["sku"]
        if sku in DEMAND_OVERRIDE:
            demand[sku] = DEMAND_OVERRIDE[sku]
        elif 0 < chain.get(sku, 0) <= 20:
            demand[sku] = round(chain[sku], 1)
        else:
            cover = rd.uniform(8.0, 14.0)
            demand[sku] = round(max(dc_avail.get(sku, 0) / cover, 5.0), 1)

    # ---------- supplier planning terms ----------
    sup_lead_by_cat = {}
    by_sup = defaultdict(list)
    for p in products:
        by_sup[p["supplier_id"]].append(p)
    terms = []
    for s in suppliers:
        sid = s["supplier_id"]
        prods = by_sup.get(sid, [])
        quoted_default = (sum(int(x["lead_time_days"]) for x in prods) / len(prods)) if prods else 45.0
        quoted, actual = SUPPLIER_LEAD.get(sid, (round(quoted_default, 1), round(quoted_default + 2.0, 1)))
        tier = s["tier"]
        rush = {"strategic": 3.0, "preferred": 4.0, "approved": 5.0, "probation": 7.5}.get(tier, 5.0)
        qual = {"strategic": 0, "preferred": 0, "approved": rd.choice([1, 2]), "probation": 4}.get(tier, 2)
        index = round(rd.uniform(0.97, 1.08), 2)
        if sid == "SUP-0008":
            index = 1.00
        if sid == "SUP-0036":
            index = 1.04
        if sid == "SUP-0044":
            index = 1.02
        sea, air = FREIGHT.get(s["country"], (0.6, 2.8))
        terms.append({
            "supplier_id": sid,
            "quoted_lead_days": quoted,
            "actual_avg_lead_days": actual,
            "planning_lead_days": int(round(quoted)),
            "price_index": index,
            "rush_premium_pct_per_week": rush,
            "setup_cost_gbp": rd.choice([2500, 3500, 4500, 6000, 8000]),
            "qualification_weeks": qual,
            "freight_sea_gbp_per_unit": sea,
            "freight_air_gbp_per_unit": air,
            "change_reason": None,
            "updated_at": g.days_ago(rd.randint(30, 200)),
        })

    # ---------- planning parameters ----------
    planning_params = []
    for i, p in enumerate(products):
        if p["status"] == "discontinued":
            continue
        sku = p["sku"]
        w = demand[sku]
        pack = max([x for x in PACKS if x <= max(6, 1.5 * w)] or [6])
        moq = int(p["moq"] or pack)
        lot = int(math.ceil(max(moq, pack) / pack) * pack)
        ss = {"A": 12.0, "B": 15.0, "C": 18.0}.get(p["abc_class"], 15.0)
        policy = "stocked"
        x = rd.random()
        if sku not in LONG_TAIL_CANDIDATES:
            if w <= 40 and p["abc_class"] == "C" and x < 0.08:
                policy = "make_to_order"
            elif p["abc_class"] == "A" and x < 0.06:
                policy = "dual_source"
        lead = int(p["lead_time_days"])
        planning_params.append({
            "planning_param_id": f"SPP-{i + 1:06d}",
            "sku": sku,
            "weekly_demand": w,
            "network_stock_units": STOCK_OVERRIDE.get(sku, dc_avail.get(sku, 0)),
            "lead_time_days": lead,
            "pack_size": pack,
            "lot_size": lot,
            "safety_stock_pct": ss,
            "sourcing_policy": policy,
            "reorder_point": int(round(w * (lead / 7.0 + 1) * (1 + ss / 100.0))),
            "updated_at": g.days_ago(rd.randint(10, 150)),
        })
    pp = {x["sku"]: x for x in planning_params}

    # ---------- order proposals (quantity follows the planning formula) ----------
    def proposal_row(pid, sku, status, reason, created_days, dest, issue=None):
        prm = pp[sku]
        w, lead, period = prm["weekly_demand"], prm["lead_time_days"], 4
        gross = int(round(w * (lead / 7.0 + period)))
        ssu = int(round(gross * prm["safety_stock_pct"] / 100.0))
        stock = prm["network_stock_units"]
        net = max(0, gross + ssu - stock)
        if net == 0:
            return None
        after_lot = max(net, prm["lot_size"])
        qty = int(math.ceil(after_lot / prm["pack_size"]) * prm["pack_size"])
        order_date = g.as_of + timedelta(days=rd.randint(-10, 14))
        return {
            "proposal_id": pid, "sku": sku, "supplier_id": pmap[sku]["supplier_id"], "dest_site_id": dest,
            "quantity": qty, "demand_period_weeks": period, "weekly_demand_used": w, "lead_time_days_used": lead,
            "pack_size_used": prm["pack_size"], "lot_size_used": prm["lot_size"],
            "safety_stock_pct_used": prm["safety_stock_pct"], "net_stock_used": stock,
            "promotion_uplift_pct": 0.0, "history_outliers_flagged": 0,
            "planned_order_date": order_date, "planned_delivery_date": order_date + timedelta(days=lead),
            "status": status, "conversion_reason": reason, "issue_detected": issue,
            "created_at": g.as_of - timedelta(days=created_days), "cancelled_at": None, "cancel_reason": None,
        }

    order_proposals = []
    pool = [p["sku"] for p in products if p["sku"] in pp and p["sku"] not in DEMAND_OVERRIDE and demand[p["sku"]] > 20]
    rd.shuffle(pool)
    for sku in pool:
        if len(order_proposals) >= 40:
            break
        row = proposal_row(f"ORP-{len(order_proposals) + 1:06d}", sku,
                           rd.choice(["draft", "draft", "draft", "approved", "converted"]),
                           rd.choice(["forecast_driven", "replenishment", "safety_stock"]),
                           rd.randint(1, 30), rd.choice(dc_ids))
        if row:
            order_proposals.append(row)

    # ---------- supply plans (rolling forecast / confirmed / stock) ----------
    supply_plans = []
    for sku_row in products[:80]:
        if sku_row["status"] == "discontinued":
            continue
        sku = sku_row["sku"]
        for week_offset in range(-4, 9):
            plan_date = g.as_of + timedelta(weeks=week_offset)
            week_str = plan_date.strftime("%Y-W%W")
            forecast = r.randint(300, 2500)
            confirmed = int(forecast * r.uniform(0.6, 1.1))
            planned = max(0, int(forecast * r.uniform(0.0, 0.5)))
            gap = forecast - confirmed - planned
            stock_oh = r.randint(100, 5000)
            stock_proj = max(0, stock_oh + confirmed + planned - forecast)
            safety = int(forecast * 0.15)
            supply_plans.append({
                "sku": sku, "plan_week": week_str, "forecast_units": forecast, "confirmed_supply": confirmed,
                "planned_inbound": planned, "gap": gap, "stock_on_hand": stock_oh, "stock_projected": stock_proj,
                "safety_stock": safety, "last_updated": g.as_of - timedelta(days=r.randint(0, 7)),
            })

    # ---------- supply / demand gaps: small ambient gaps; the question stories come from seed ----------
    monday = g.as_of - timedelta(days=g.as_of.weekday())
    supply_demand_gaps = []
    gap_pool = [p for p in products if p["status"] in ("active", "new") and p["category"] != "Trousers"]
    for p in rd.sample(gap_pool, 60):
        wk = monday + timedelta(weeks=rd.randint(0, 8))
        fc = int(max(40, demand[p["sku"]] * rd.uniform(0.9, 1.2)))
        gap_units = max(10, int(fc * rd.uniform(0.02, 0.15)))
        supply_demand_gaps.append({
            "gap_id": f"SDG-{len(supply_demand_gaps) + 1:06d}", "sku": p["sku"], "style_id": p["style_id"],
            "week_start": wk, "forecast_units": fc, "confirmed_units": fc - gap_units, "gap_units": gap_units,
            "category": p["category"],
            "gap_reason": rd.choice(["delayed_po", "forecast_spike", "supplier_delay", "promotion"]),
            "first_detected": g.as_of - timedelta(days=rd.randint(1, 21)),
            "last_updated": g.as_of - timedelta(days=rd.randint(0, 7)),
        })

    # ---------- supply requests ----------
    supply_requests = []
    for i, sku_row in enumerate(products[5:35]):
        sku = sku_row["sku"]
        if r.random() > 0.5:
            continue
        req_date = g.as_of + timedelta(days=r.randint(7, 42))
        supply_requests.append({
            "request_id": f"SRP-{len(supply_requests) + 1:06d}", "sku": sku,
            "site_id": r.choice(dc_ids), "quantity_requested": r.randint(1000, 10000),
            "requirement_date": req_date, "request_type": r.choice(["promotion", "replenishment", "safety_stock"]),
            "promotion_id": None, "status": r.choice(["draft", "submitted", "ordered"]),
            "submitted_at": g.as_of - timedelta(days=r.randint(1, 14)), "notes": None,
        })

    # ---------- lead times by origin ----------
    lead_time_origins = []
    n = 0
    for port, country, region, mode, days, var, rate in ORIGINS:
        for dc in ("DC1", "DC2", "DC3", "DC4"):
            n += 1
            lead_time_origins.append({
                "origin_id": f"LTO-{n:06d}", "origin_region": region, "origin_country": country,
                "origin_port": port, "dest_dc": dc,
                "transit_days": max(1, days + DEST_OFFSET[region][dc]),
                "transit_variability_days": var, "mode": mode,
                "rate_gbp_per_unit": round(rate * (1.15 if dc == "DC4" and region == "Asia" else 1.0), 2),
                "last_updated": g.days_ago(rd.randint(5, 40)),
            })

    # ---------- fabric requirements (healthy rows; shortages are seeded) ----------
    cat_suppliers = defaultdict(list)
    for s in suppliers:
        if s["status"] == "active" and s["category_focus"] in ("Womenswear", "Menswear", "Kids"):
            cat_suppliers[s["category_focus"]].append(s["supplier_id"])
    cat_focus = {"Blouses": "Womenswear", "Tops": "Womenswear", "Dresses": "Womenswear", "Knitwear": "Womenswear",
                 "Trousers": "Womenswear", "Shirts": "Menswear", "Outerwear": "Menswear", "T-Shirts": "Menswear",
                 "Nightwear": "Kids", "Babywear": "Kids", "Schoolwear": "Kids", "Scarves": "Womenswear"}
    materials = ["Cotton", "Polyester", "Wool", "Viscose", "Nylon", "Linen"]
    fabric_requirements = []
    for cat in APPAREL:
        for mat in rd.sample(materials, 2):
            monthly = rd.choice([3000, 4500, 6000, 8000, 11000, 15000])
            lead = rd.choice([6, 8, 10, 12])
            weekly = monthly / 4.33
            fabric_requirements.append({
                "category": cat, "material": mat, "annual_requirement_units": monthly * 12,
                "monthly_average_units": monthly, "supplier_id": rd.choice(cat_suppliers[cat_focus[cat]]),
                "lead_time_weeks": lead,
                "stock_on_hand": int(weekly * (lead + 3 + rd.uniform(1, 4))),
                "critical_threshold": int(weekly * 3),
            })

    # ---------- material requirements by month (from planned demand) ----------
    first = g.as_of.replace(day=1)
    months = []
    y, m = first.year, first.month
    for _ in range(18):
        months.append(first.replace(year=y, month=m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    wk_by_cat = defaultdict(float)
    for p in products:
        if p["status"] != "discontinued":
            wk_by_cat[p["category"]] += demand[p["sku"]]
    leather_base = (wk_by_cat["Footwear"] * 0.30 + wk_by_cat["Bags"] * 0.65) * 4.33
    apparel_wk = sum(wk_by_cat[c] for c in APPAREL)
    spec = {
        "leather": (leather_base, "m2", 16, "Footwear; Bags", LEATHER_INDEX),
        "fabric": (apparel_wk * 1.5 * 4.33, "m", 10, "Blouses; Tops; Dresses; Knitwear; Trousers; Shirts; Outerwear", GENERAL_INDEX),
        "zips": (apparel_wk * 0.6 * 4.33, "pcs", 12, "Trousers; Outerwear; Dresses; Schoolwear", GENERAL_INDEX),
        "trims": (apparel_wk * 2.0 * 4.33, "m", 6, "All apparel", GENERAL_INDEX),
    }
    material_requirements = []
    for mt, (base, unit, lead, drivers, idx) in spec.items():
        for d in months:
            qty = int(round(base * idx[d.month - 1] / 100.0) * 100)
            material_requirements.append({
                "material_type": mt, "month_start": d, "required_qty": qty, "unit": unit,
                "lead_time_weeks": lead, "driver_categories": drivers,
            })

    # ---------- space plans: baseline occupancy and weekly inbound / outbound by DC and category ----------
    loc_counts = defaultdict(int)
    for l in g.master("locations"):
        if l["status"] == "active" and l["location_type"] in ("reserve", "bulk_floor"):
            loc_counts[l["site_id"]] += 1
    cat_of = {p["sku"]: p["category"] for p in products}
    open_po = {}
    for po in g.master("purchase_orders"):
        if po["status"] in ("open", "confirmed", "shipped"):
            open_po[po["po_id"]] = po
    inbound_units = defaultdict(float)  # (site, category, week index) -> units
    for l in g.master("po_lines"):
        po = open_po.get(l["po_id"])
        if not po or l["sku"] not in cat_of:
            continue
        due = g.as_of.__class__.fromisoformat(po["due_date"])
        if (due - monday).days < 0:  # already due: assume received or stale
            continue
        wk = max(0, (due - monday).days // 7)
        if wk < 12:
            inbound_units[(po["dest_site_id"], cat_of[l["sku"]], wk)] += int(l["qty_ordered"])
    space_baseline, space_weekly = [], []
    for site in dc_ids:
        cap = loc_counts.get(site, 0)
        if not cap:
            continue
        onhand = dc_onhand_cat[site]
        if site == "DC1":
            pos = dict(DC1_POSITIONS)
        else:
            tot = sum(onhand.values()) or 1
            pos = {c: max(1, int(round(0.88 * cap * u / tot))) for c, u in onhand.items()}
        upp = max(1.0, sum(onhand.values()) / max(1, sum(pos.values())))
        for c, n_pos in pos.items():
            space_baseline.append({"site_id": site, "category": c, "positions_occupied": n_pos,
                                   "units_per_position": int(round(upp))})
            ins = [inbound_units.get((site, c, w), 0.0) / upp for w in range(12)]
            growth = DC1_GROWTH.get(c, 0.0) if site == "DC1" else 0.0
            out_per_week = max(0.0, sum(ins) / 12.0 - growth)
            for w in range(12):
                space_weekly.append({
                    "site_id": site, "week_start": monday + timedelta(weeks=w), "category": c,
                    "inbound_pallets": round(ins[w], 1), "outbound_pallets": round(out_per_week, 1),
                })

    # ---------- component buy terms (seed provides the story rows) ----------
    component_buy_terms = []

    return {
        "planning_parameters": planning_params,
        "order_proposals": order_proposals,
        "supply_plans": supply_plans,
        "supply_demand_gaps": supply_demand_gaps,
        "supply_requests": supply_requests,
        "supplier_planning_terms": terms,
        "lead_time_by_origin": lead_time_origins,
        "fabric_requirements": fabric_requirements,
        "material_requirements": material_requirements,
        "space_baseline": space_baseline,
        "space_forecast_weekly": space_weekly,
        "component_buy_terms": component_buy_terms,
    }
