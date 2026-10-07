"""Loss prevention data: weekly shrink per store, incident log, control programmes, high-risk list.

Background is deliberately quiet so the seeded stories stand out:
  * shrink_records: one row per store per week for 78 weeks, with a Nov/Dec peak and a gentle upward trend
    (so "this year vs last year" works). Story stores get their multipliers here (weeks ago -> k).
  * incidents: only a handful per store over 15 months; the Leeds stories live in seed/incidents.csv.
  * control_programs: per-store programmes whose cost and benefit follow one typical profile per control type.
"""
from datetime import datetime, timedelta

WEEKS = 78

# Weeks-ago index k (0 = latest Monday) -> multipliers for the stores in the Leeds stories.
# total = shrink multiplier, adj = stock adjustments, pos = POS exceptions, theft = theft share of shrink,
# err = process error share of shrink.
STORY = {
    # ST150: shrink tripled since mid-September, evening stockroom removals by a staff member
    "ST150": {k: dict(total=3.0, adj=4.0, pos=1.3, theft=0.72, err=0.14) for k in range(0, 4)},
    # ST159: till 2 void cluster, plus an organised group
    "ST159": {k: dict(total=1.7, adj=1.4, pos=3.5, theft=0.62, err=0.18) for k in range(0, 5)},
    # ST165: self-checkout bypass, rising week on week
    "ST165": {0: dict(total=1.8, adj=1.2, pos=1.8, theft=0.66, err=0.14), 1: dict(total=1.6, adj=1.2, pos=1.7, theft=0.66, err=0.14),
              2: dict(total=1.4, adj=1.1, pos=1.5, theft=0.64, err=0.15), 3: dict(total=1.2, adj=1.1, pos=1.3, theft=0.62, err=0.16)},
    # ST181: self-checkout scanner faults after a software push (process / system error)
    "ST181": {k: dict(total=1.5, adj=1.2, pos=1.8, theft=0.30, err=0.50) for k in range(0, 2)},
    # ST183: unauthorised refunds and self-checkout bypass
    "ST183": {0: dict(total=1.7, adj=1.2, pos=2.8, theft=0.62, err=0.16), 1: dict(total=1.6, adj=1.2, pos=2.6, theft=0.62, err=0.16),
              2: dict(total=1.5, adj=1.2, pos=2.4, theft=0.62, err=0.16)},
}

# SKUs used by the seeded stories: kept out of the random background so their histories stay clean.
STORY_SKUS = {
    "PF-220", "K-1700", "SKU-103661", "SKU-104732", "SKU-104746", "SKU-103668", "SKU-103675", "SKU-102170", "SKU-104739",
    "SKU-101834", "SKU-105845", "SKU-105341", "SKU-105159", "SKU-102338", "SKU-101085", "SKU-100623",
}

# Typical annual cost and annual shrink reduction (GBP) per store for each control type, with spread.
CONTROL_PROFILE = {
    "pos_rules": (1000, 1450, 0.12),
    "tagging": (2500, 3800, 0.15),
    "self_checkout_monitoring": (4000, 4400, 0.15),
    "training": (1500, 1200, 0.20),
    "layout": (5000, 2800, 0.15),
    "cctv": (8000, 2400, 0.20),
    "security_staff": (12000, 2600, 0.15),
    "staffing": (15000, 2200, 0.15),
}


def _season(d):
    if d.month == 12:
        return 1.4
    if d.month == 11:
        return 1.2
    if d.month == 1:
        return 1.15
    return 1.0


def generate(g):
    r = g.rng
    sites = [s for s in g.master("sites") if s["type"] == "store"]
    stores = [s["site_id"] for s in sites]
    managers = {e["site_id"]: e["employee_id"] for e in g.master("employees") if e["role"] == "Store Manager"}
    products = [p for p in g.master("products") if p["sku"] not in STORY_SKUS and p["status"] == "active"]
    cheap = [p for p in products if 3 <= float(p["unit_cost_gbp"] or 0) <= 60] or products

    # ---- shrink_records: weekly per store -------------------------------------------------------
    shrink_records = []
    for s in sites:
        sid = s["site_id"]
        size = min(1.8, max(0.35, float(s["sqft"] or 15000) / 18000.0))
        store_factor = size * r.uniform(0.85, 1.15)
        for k in range(WEEKS):
            d = g.as_of - timedelta(days=7 * k)
            trend = 1 + 0.10 * (WEEKS - 1 - k) / (WEEKS - 1)
            base = 1000.0 * store_factor * _season(d) * trend * r.uniform(0.88, 1.12)
            total = base
            adj_m = pos_m = 1.0
            theft_sh = r.uniform(0.38, 0.48)
            err_sh = r.uniform(0.28, 0.38)
            st = STORY.get(sid, {}).get(k)
            if st:
                total *= st["total"]
                adj_m, pos_m = st["adj"], st["pos"]
                theft_sh, err_sh = st["theft"], st["err"]
            dmg_sh = max(0.0, 1 - theft_sh - err_sh)
            shrink_records.append({
                "site_id": sid,
                "recorded_date": d,
                "shrink_gbp": round(total, 2),
                "adjustment_gbp": round(base * 0.25 * adj_m * r.uniform(0.9, 1.1), 2),
                "pos_exception_gbp": round(base * 0.16 * pos_m * r.uniform(0.9, 1.1), 2),
                "theft_estimated_gbp": round(total * theft_sh, 2),
                "damage_estimated_gbp": round(total * dmg_sh, 2),
                "error_estimated_gbp": round(total * err_sh, 2),
            })

    # ---- incidents: quiet background (story rows come from seed) ---------------------------------
    kinds = (["theft_external"] * 6 + ["damage"] * 6 + ["system_error"] * 2 + ["pos_void"] * 3 + ["audit_adjust"] * 2
             + ["theft_internal"])
    notes = {
        "theft_external": ("Opportunist theft", "Item removed from display; no CCTV match"),
        "theft_internal": ("Stock missing after staff handling", "Under review"),
        "damage": ("Damaged in store", "Handling damage"),
        "system_error": ("Till or self-checkout error", "Scan error corrected"),
        "pos_void": ("Void without sale", "Cashier error"),
        "audit_adjust": ("Stock count adjustment", "Count variance"),
    }
    incidents = []
    for sid in stores:
        for _ in range(r.randint(2, 9)):
            d = g.as_of - timedelta(days=r.randint(1, 450))
            t = r.choice(kinds)
            p = r.choice(cheap)
            cost = float(p["unit_cost_gbp"] or 0)
            units = r.randint(1, 4)
            value = round(units * cost, 2)
            incidents.append({
                "incident_id": f"INC-{len(incidents) + 1:06d}",
                "site_id": sid,
                "recorded_date": d,
                "incident_time": f"{r.randint(9, 19):02d}:{r.choice(['05', '20', '35', '50'])}",
                "incident_type": t,
                "sku": p["sku"],
                "units_involved": units,
                "value_gbp": value,
                "description": f"{notes[t][0]}: {p['name']}",
                "reported_by": managers.get(sid, ""),
                "root_cause": notes[t][1],
                "updated_at": datetime.combine(d, datetime.min.time()) + timedelta(hours=18),
            })

    # ---- control programmes ---------------------------------------------------------------------
    types = list(CONTROL_PROFILE)
    control_programs = []
    for sid in stores:
        n = r.choice([0, 1, 1, 2, 2, 3])
        for ct in r.sample(types, n):
            cost, red, sd = CONTROL_PROFILE[ct]
            status = r.choices(["active", "paused", "completed"], [0.86, 0.07, 0.07])[0]
            control_programs.append({
                "control_id": f"CTL-{len(control_programs) + 1:06d}",
                "site_id": sid,
                "control_type": ct,
                "start_date": g.as_of - timedelta(days=30 * r.randint(2, 24)),
                "annual_cost_gbp": round(cost * r.gauss(1, sd), 2),
                "shrink_reduction_gbp": round(red * r.gauss(1, sd * 1.3), 2),
                "status": status,
            })

    # ---- high-risk list: a modest set of electricals, mostly theft-driven -----------------------
    elec = [p["sku"] for p in products if p["department"] == "Electricals" and float(p["retail_price_gbp"] or 0) >= 100]
    pool = r.sample(elec, min(10, len(elec)))
    high_risk_products = []
    for sid in stores[:60]:
        for sku in r.sample(pool, 2):
            added = g.as_of - timedelta(days=r.randint(40, 330))
            high_risk_products.append({
                "hrp_id": f"HRP-{len(high_risk_products) + 1:06d}",
                "site_id": sid,
                "sku": sku,
                "added_date": added,
                "risk_level": r.choice(["medium", "high", "high"]),
                "protection_type": r.choice(["tagging", "tagging", "locked_case", "staff_supervised"]),
                "loss_driver": r.choice(["theft", "theft", "theft", "unknown"]),
                "notes": "",
                "status": "active",
                "reason": "",
                "updated_at": datetime.combine(added, datetime.min.time()) + timedelta(hours=9),
            })

    return {
        "shrink_records": shrink_records,
        "incidents": incidents,
        "control_programs": control_programs,
        "high_risk_products": high_risk_products,
        "loss_prevention_cases": [],
        "protection_options": [],
    }
