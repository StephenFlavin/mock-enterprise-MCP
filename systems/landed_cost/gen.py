"""Landed cost data: per-PO-line cost breakdowns, freight rates, tariff rates, FX and sourcing scenarios.

Everything is derived from master POs / products so ids line up with other systems. Costs are deterministic per
SKU and lane (weight x rate per kg, duty from the tariff table) so a monthly trend is real, not mix noise:
sea/rail freight, insurance, handling and CN apparel duty all step up over the last four months (see freight_index).
"""
import math
from datetime import datetime, timedelta

# ---- cost model -------------------------------------------------------------------------------------------------
SEA_KG = {"CN": 1.9, "VN": 2.0, "BD": 2.2, "IN": 1.8, "MX": 2.4}
AIR_KG = {"CN": 4.6, "VN": 4.8, "BD": 5.2, "IN": 4.4}
ROAD_KG = {"TR": 0.55, "PT": 0.42, "IT": 0.38, "PL": 0.3, "DE": 0.28, "FR": 0.28, "GB": 0.14}
RAIL_KG = 0.8
LEAD = {"sea": {"CN": 38, "VN": 36, "BD": 42, "IN": 34, "MX": 30}, "air": 7, "rail": 24,
        "road": {"TR": 6, "PT": 4, "IT": 4, "PL": 3, "DE": 3, "FR": 3, "GB": 2}}

# duty % of FOB by origin and product group (UK global tariff simplified; EU/TR/MX/GB preferential = 0)
DUTY = {
    "apparel": {"CN": 12.0, "VN": 9.0, "BD": 0.0, "IN": 8.0},
    "footwear": {"CN": 8.0, "VN": 8.0, "IN": 8.0},
    "accessories": {"CN": 6.5, "VN": 3.0, "IN": 4.0},
    "home": {"CN": 8.0, "IN": 6.5},
    "electricals": {"CN": 3.7, "VN": 3.7},
}
CONTINGENCY = {"CN": 7.5, "VN": 5.0, "IN": 3.5, "BD": 2.0, "TR": 2.5, "MX": 2.0, "PT": 0.5, "IT": 0.5,
               "PL": 0.5, "DE": 0.5, "FR": 0.5, "GB": 0.0}
CN_APPAREL_STEP_DAYS = 45      # CN apparel duty +3 pts for orders placed in the last 45 days


def group_of(p):
    if p["category"] == "Footwear":
        return "footwear"
    return {"Womenswear": "apparel", "Menswear": "apparel", "Kids": "apparel", "Accessories": "accessories",
            "Home": "home", "Electricals": "electricals"}.get(p["department"], "beauty")


def duty_rate(p, origin, days_ago):
    g = group_of(p)
    rate = DUTY.get(g, {}).get(origin, 0.0)
    if g == "apparel" and origin == "CN" and days_ago <= CN_APPAREL_STEP_DAYS:
        rate += 3.0
    return rate


def freight_index(mode, days_ago):
    """Market rate index by order age: container rates ramp up over the last four months."""
    if mode in ("sea", "rail"):
        return 1.0 if days_ago > 120 else 1.4 if days_ago > 60 else 2.6 if days_ago > 30 else 3.0
    if mode == "air":
        return 1.0 if days_ago > 90 else 1.15
    return 1.0 if days_ago > 90 else 1.08


def kg_rate(mode, origin):
    if mode == "sea":
        return SEA_KG.get(origin, 0.9)
    if mode == "air":
        return AIR_KG.get(origin, 3.4)
    if mode == "rail":
        return RAIL_KG
    return ROAD_KG.get(origin, 0.4)


def lead_days(mode, origin, rng):
    base = LEAD[mode]
    base = base.get(origin, 10) if isinstance(base, dict) else base
    return max(1, base + rng.randint(-2, 3))


def generate(g):
    r = g.rng
    suppliers = {s["supplier_id"]: s for s in g.master("suppliers")}
    factories = {f["factory_id"]: f for f in g.master("factories")}
    products = {p["sku"]: p for p in g.master("products")}
    lines = {}
    for ln in g.master("po_lines"):
        lines.setdefault(ln["po_id"], []).append(ln)

    # ---- FX: smooth weekly series (GBP per unit of currency), sterling slightly weaker in the last 3 months ----
    fx_base = {"USD": 0.80, "EUR": 1.20, "CNY": 0.115, "INR": 0.0115, "VND": 0.000032}
    fx_rates_list, fx_spot = [], {}
    for cur, base in fx_base.items():
        for i in range(52):
            d = g.as_of - timedelta(days=i * 7)
            drift = 1.0 + 0.025 * max(0.0, 1 - i / 13.0)         # +2.5% GBP cost of foreign currency by today
            wobble = 1.0 + 0.004 * math.sin(i * 0.9)
            spot = base * drift * wobble
            fx_spot[(cur, i)] = spot
            fx_rates_list.append({"currency_pair": f"{cur}/GBP", "rate_date": d, "spot_rate": spot,
                                  "forward_30d": spot * 1.0025, "forward_90d": spot * 1.007, "forward_180d": spot * 1.014})

    def fx_on(cur, d):
        if cur == "GBP":
            return 1.0
        return fx_spot[(cur, max(0, min(51, round((g.as_of - d).days / 7))))]

    # ---- landed cost per PO line ----
    lc = []
    for po in g.master("purchase_orders"):
        po_date = datetime.fromisoformat(po["order_date"])
        days_ago = (g.as_of - po_date.date()).days
        if not 0 <= days_ago <= 180 or po["status"] in ("draft", "cancelled"):
            continue
        sup, fac = suppliers.get(po["supplier_id"]), factories.get(po["factory_id"])
        if not sup or not fac:
            continue
        origin, mode = fac["country"], po["mode"]
        for ln in lines.get(po["po_id"], []):
            p = products.get(ln["sku"])
            if not p:
                continue
            units, fob = int(ln["qty_ordered"]), float(ln["unit_cost"])
            weight = float(p["weight_kg"])
            freight = max(0.05, weight * kg_rate(mode, origin)) * freight_index(mode, days_ago) * r.uniform(0.97, 1.03)
            duty = fob * duty_rate(p, origin, days_ago) / 100.0
            ins_rate = 0.005 if days_ago > 60 else 0.0065
            insurance = (fob + freight) * ins_rate
            handling = (fob + freight) * 0.01 * (1.0 if days_ago > 60 else 1.2)
            lead = lead_days(mode, origin, r)
            holding = fob * (0.15 / 52.0) * max(1, lead // 7)
            landed = fob + freight + duty + insurance + handling + holding
            lc.append({
                "lc_id": f"LC-{len(lc) + 1:06d}", "po_id": po["po_id"], "sku": ln["sku"], "supplier_id": po["supplier_id"],
                "origin_country": origin, "units": units, "fob_unit_gbp": fob, "freight_unit_gbp": freight,
                "duty_unit_gbp": duty, "insurance_unit_gbp": insurance, "handling_unit_gbp": handling,
                "inventory_holding_unit_gbp": holding, "landed_cost_unit_gbp": landed, "total_landed_cost_gbp": landed * units,
                "fx_rate": fx_on(sup["currency"], po_date.date()), "mode": mode, "lead_time_days": lead, "updated_at": po_date,
            })

    # ---- tariff rates: one row per (product HS code, origin) with the current duty; CN apparel shows the recent step ----
    tariffs, seen = [], set()
    for p in g.master("products"):
        origin = p["country_of_origin"]
        key = (p["hs_code"], origin)
        if key in seen or origin == "GB":
            continue
        seen.add(key)
        base = DUTY.get(group_of(p), {}).get(origin, 0.0)
        cont = CONTINGENCY.get(origin, 1.0)
        note = ""
        if origin == "CN":
            note = "Additional tariff escalation under review; contingency recommended"
        elif origin == "VN" and p["category"] == "Footwear":
            note = "Proposed additional 15% tariff on footwear from Vietnam under review"
            cont = 7.5
        elif origin == "BD":
            note = "Duty-free (least developed country scheme)"
        elif origin in ("TR", "PT", "IT", "PL", "DE", "FR", "MX"):
            note = "Preferential origin: 0% under trade agreement"
        step = origin == "CN" and group_of(p) == "apparel"
        if step:
            tariffs.append({"tariff_id": f"TAR-{len(tariffs) + 1:06d}", "hs_code": p["hs_code"], "origin_country": origin,
                            "dest_country": "GB", "duty_rate_pct": base, "vat_rate_pct": 20.0,
                            "effective_from": g.as_of - timedelta(days=400),
                            "effective_to": g.as_of - timedelta(days=CN_APPAREL_STEP_DAYS + 1),
                            "contingency_pct": cont, "notes": "Superseded rate"})
        tariffs.append({"tariff_id": f"TAR-{len(tariffs) + 1:06d}", "hs_code": p["hs_code"], "origin_country": origin,
                        "dest_country": "GB", "duty_rate_pct": base + (3.0 if step else 0.0), "vat_rate_pct": 20.0,
                        "effective_from": g.as_of - timedelta(days=CN_APPAREL_STEP_DAYS if step else 400),
                        "effective_to": g.as_of + timedelta(days=365), "contingency_pct": cont, "notes": note})

    # ---- freight rates (background lanes; story lanes CNSHA->DC1 and BD->DC1 come from seed/freight_rates.csv) ----
    fr = []
    ocean, air = ["CAR-005", "CAR-006", "CAR-007"], ["CAR-008", "CAR-018"]
    lanes = [("CNNGB", "CN"), ("CNYTN", "CN"), ("VNSGN", "VN"), ("BDCGP", "BD"), ("INNSA", "IN")]
    for port, country in lanes:
        for dest in ("DC1", "DC2", "DC3"):
            if country == "BD" and dest == "DC1":
                continue
            for k, car in enumerate(ocean[:2]):
                cont = round(2600 * (1 + 0.08 * k) * r.uniform(0.9, 1.15) + (200 if dest != "DC1" else 0))
                fr.append({"rate_id": f"FR-{len(fr) + 1:06d}", "origin_port": port, "via_port": "GBFXT", "dest_port": "GBFXT",
                           "dest_site_id": dest, "origin_country": country,
                           "routing": f"Sea to Felixstowe, road to {dest}", "mode": "sea", "carrier_id": car,
                           "rate_per_kg_gbp": round(cont / 2600.0, 2), "rate_per_container_gbp": cont,
                           "port_charges_per_container_gbp": 310, "inland_per_container_gbp": 480 if dest == "DC1" else 560,
                           "min_qty": 0, "lead_time_days": LEAD["sea"][country], "effective_from": g.as_of - timedelta(days=60),
                           "effective_to": g.as_of + timedelta(days=120), "transit_days_p50": LEAD["sea"][country],
                           "transit_days_p95": LEAD["sea"][country] + 9, "reliability_pct": round(r.uniform(68, 84), 1)})
            fr.append({"rate_id": f"FR-{len(fr) + 1:06d}", "origin_port": port, "via_port": "", "dest_port": "GBLHR",
                       "dest_site_id": dest, "origin_country": country, "routing": f"Direct air to London Heathrow, road to {dest}",
                       "mode": "air", "carrier_id": air[0], "rate_per_kg_gbp": round(AIR_KG[country] * r.uniform(0.95, 1.1), 2),
                       "rate_per_container_gbp": 0, "port_charges_per_container_gbp": 0, "inland_per_container_gbp": 0,
                       "min_qty": 100, "lead_time_days": 4, "effective_from": g.as_of - timedelta(days=60),
                       "effective_to": g.as_of + timedelta(days=120), "transit_days_p50": 4, "transit_days_p95": 6,
                       "reliability_pct": round(r.uniform(90, 97), 1)})
    for port, country in (("TRMER", "TR"), ("PTLEI", "PT")):
        for dest in ("DC1", "DC2", "DC3"):
            fr.append({"rate_id": f"FR-{len(fr) + 1:06d}", "origin_port": port, "via_port": "", "dest_port": "GBDVR",
                       "dest_site_id": dest, "origin_country": country, "routing": f"Road/ferry via Dover to {dest}", "mode": "road",
                       "carrier_id": "CAR-004", "rate_per_kg_gbp": ROAD_KG[country],
                       "rate_per_container_gbp": 2100 if country == "PT" else 2900,
                       "port_charges_per_container_gbp": 0, "inland_per_container_gbp": 0, "min_qty": 0,
                       "lead_time_days": LEAD["road"][country], "effective_from": g.as_of - timedelta(days=60),
                       "effective_to": g.as_of + timedelta(days=120), "transit_days_p50": LEAD["road"][country],
                       "transit_days_p95": LEAD["road"][country] + 2, "reliability_pct": round(r.uniform(88, 96), 1)})

    # ---- background cost scenarios (story scenarios for SKU-103185 come from seed/cost_scenarios.csv) ----
    scen = []
    pool = [p for p in g.master("products") if p["country_of_origin"] in ("CN", "VN", "BD", "IN", "TR", "PT")
            and p["department"] in ("Womenswear", "Menswear", "Kids") and p["sku"] != "SKU-103185"]
    for p in r.sample(pool, 12):
        fob, origin = float(p["unit_cost_gbp"]), p["country_of_origin"]
        mode = "road" if origin in ("TR", "PT") else "sea"
        for units, disc in ((5000, 1.0), (20000, 0.95)):
            scen.append({"scenario_id": f"SC-{len(scen) + 1:06d}", "scenario_name": f"{origin} {mode} {units // 1000}k units",
                         "sku": p["sku"], "supplier_id": p["supplier_id"], "origin_country": origin, "dest_site_id": "DC1",
                         "units": units, "mode": mode, "fob_unit_gbp": round(fob * disc, 2),
                         "freight_unit_gbp": round(float(p["weight_kg"]) * kg_rate(mode, origin), 2),
                         "duty_rate_pct": DUTY.get(group_of(p), {}).get(origin, 0.0), "fx_rate": 1.0,
                         "insurance_pct": 0.5, "holding_cost_pct_pa": 15.0, "lead_time_days": LEAD[mode][origin],
                         "created_at": g.as_of - timedelta(days=r.randint(5, 60)), "created_by": "EMP-00001"})

    return {"landed_cost_summary": lc, "freight_rates": fr, "tariff_rates": tariffs, "fx_rates": fx_rates_list,
            "cost_scenarios": scen}
