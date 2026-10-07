"""Cost allocation: DC cost components and pools, drivers, channel costs, e-com ABC cost, SKU cost to serve, benchmarks.

All money is annual FY26 actuals in GBP.  DC pools are the DC components; channel warehousing sums to the DC pools.
"""
from datetime import datetime

# site: (units handled, [labour, space, equipment, overhead] cost per unit, pallet spaces, fixed-cost share of each component)
DCS = {
    "DC1": (62_000_000, [0.44, 0.22, 0.26, 0.125], 41_000),   # Northampton: ~18% above network average
    "DC2": (54_000_000, [0.36, 0.16, 0.22, 0.10], 33_000),
    "DC3": (31_000_000, [0.33, 0.17, 0.19, 0.11], 21_000),
    "DC4": (24_000_000, [0.34, 0.15, 0.18, 0.10], 17_000),
    "DC5": (15_000_000, [0.31, 0.15, 0.17, 0.10], 11_000),
}
COMPONENTS = ["labour", "space", "equipment", "overhead"]
FIXED_PCT = {"labour": 15, "space": 90, "equipment": 70, "overhead": 60}
POOL_BASE = {"labour": "units", "space": "pallet_spaces", "equipment": "units", "overhead": "orders"}
NET_POOLS = [  # id, name, type, amount, base, volume the rate is per
    ("POOL-TRN-NET", "Network Transport", "transport", 144_000_000, "weight", 120_000_000),
    ("POOL-PKG-NET", "Network Packaging", "packaging", 16_500_000, "units", 136_000_000),
    ("POOL-RET-NET", "Network Returns", "returns", 63_000_000, "orders", 2_120_000),
]
# channel: orders, units, returned orders, returned items, sales, gross margin, warehousing, outbound transport, packaging
CHANNELS = {
    "store": (480_000, 98_000_000, 200_000, 2_800_000, 1_950_000_000, 1_053_000_000, 62_000_000, 48_000_000, 3_500_000),
    "online": (7_900_000, 19_000_000, 1_900_000, 4_200_000, 700_000_000, 217_000_000, 83_000_000, 88_000_000, 12_000_000),
    "wholesale": (9_000, 22_000_000, 20_000, 1_200_000, 350_000_000, 112_000_000, 19_000_000, 8_000_000, 1_000_000),
}
# 13-weekly cost periods (period end = Monday): orders, labour, system, transport, returns per order
ECOM = [
    (1_720_000, 1.80, 0.60, 2.80, 0.84),   # 6.04
    (1_790_000, 1.82, 0.60, 2.85, 0.85),   # 6.12
    (1_850_000, 1.85, 0.60, 2.90, 0.85),   # 6.20
    (2_000_000, 2.05, 0.62, 3.35, 1.08),   # 7.10
]
# story SKUs, written to seed/sku_costs.csv (small <=0.5 kg unless noted): units, warehousing, transport, handling cost per unit
STORY_SKUS = {
    "SKU-105761": (3200, 3.10, 3.20, 1.90),   # net -2.49 per unit
    "SKU-105768": (2600, 3.40, 3.30, 2.00),   # -2.99
    "SKU-105775": (1800, 3.90, 3.50, 2.20),   # -3.89
    "SKU-104816": (2400, 4.00, 3.60, 2.60),   # -1.86 (loses less than 2)
    "SKU-104830": (1500, 4.60, 3.90, 2.80),   # -2.96
    "SKU-104480": (1900, 3.00, 3.40, 2.30),   # -2.82
    "SKU-104494": (1100, 3.60, 3.60, 2.50),   # -3.82
    "SKU-102296": (2800, 1.90, 1.90, 1.10),   # medium (1.03 kg) loss-maker, -1.22
    "SKU-102303": (3600, 1.40, 1.30, 0.80),   # medium, profitable
}


def generate(g):
    r = g.rng
    as_of = g.as_of

    # ---- DC components, pools and drivers
    comps, pools, drivers = [], [], []
    for site, (units, cpus, spaces) in DCS.items():
        for ct, cpu in zip(COMPONENTS, cpus):
            total = round(units * cpu)
            comps.append({"site_id": site, "component_type": ct, "units_handled": units, "total_cost_gbp": total,
                          "fixed_cost_pct": FIXED_PCT[ct], "as_of_date": as_of})
            pid = f"POOL-{ct[:3].upper()}-{site}"
            pools.append({"pool_id": pid, "name": f"{site} {ct.title()}", "cost_type": ct, "site_id": site,
                          "current_amount_gbp": total, "updated_at": as_of})
            base = POOL_BASE[ct]
            vol = {"units": units, "pallet_spaces": spaces, "orders": units / 4.5}[base]
            drivers.append((pid, base, round(total / vol, 4)))
    for pid, name, ct, amt, base, vol in NET_POOLS:
        pools.append({"pool_id": pid, "name": name, "cost_type": ct, "site_id": None,
                      "current_amount_gbp": amt, "updated_at": as_of})
        drivers.append((pid, base, round(amt / vol, 4)))
    drivers = [{"driver_id": f"DRV-{i:06d}", "pool_id": p, "allocation_base": b, "rate_gbp_per_unit": rt,
                "status": "active", "updated_at": as_of} for i, (p, b, rt) in enumerate(drivers, 1)]

    # ---- scenarios
    scenarios = [
        {"scenario_id": "SCEN-000001", "scenario_name": "FY26 Actuals", "base_scenario_id": None,
         "assumptions": "Current allocation drivers, no changes to cost pools",
         "returns_change_pct": 0, "warehousing_change_pct": 0, "transport_change_pct": 0, "packaging_change_pct": 0,
         "returns_driver": None, "created_at": datetime.fromisoformat(f"{g.days_ago(30)} 09:00"), "created_by": "EMP-00085"},
        {"scenario_id": "SCEN-000002", "scenario_name": "Free Returns Removed", "base_scenario_id": "SCEN-000001",
         "assumptions": "Returns pool reduced 30% (free returns removed); other pools unchanged",
         "returns_change_pct": -30, "warehousing_change_pct": 0, "transport_change_pct": 0, "packaging_change_pct": 0,
         "returns_driver": None, "created_at": datetime.fromisoformat(f"{g.days_ago(7)} 14:30"), "created_by": "EMP-00085"},
    ]

    # ---- channels
    activity, ccosts = [], []
    for ch, (orders, units, ro, ri, sales, gm, wh, tr, pk) in CHANNELS.items():
        activity.append({"channel": ch, "orders": orders, "units": units, "returned_orders": ro, "returned_items": ri,
                         "sales_gbp": sales, "gross_margin_gbp": gm, "as_of_date": as_of})
        for ct, v in (("warehousing", wh), ("outbound_transport", tr), ("packaging", pk)):
            ccosts.append({"channel": ch, "cost_type": ct, "cost_gbp": v, "as_of_date": as_of})

    # ---- e-commerce activity-based cost, one row per 13-week period (latest ends at as_of)
    ecom = []
    for i, (orders, lab, sys_, trn, ret) in enumerate(ECOM):
        ecom.append({"cost_period": g.days_ago(91 * (len(ECOM) - 1 - i)), "orders_count": orders,
                     "labour_cost_gbp": round(orders * lab), "system_cost_gbp": round(orders * sys_),
                     "transport_cost_gbp": round(orders * trn), "returns_cost_gbp": round(orders * ret)})

    # ---- SKU cost to serve: story SKUs are in seed/sku_costs.csv; here only profitable background SKUs
    prods = [p for p in g.master("products") if p["status"] == "active" and p["sku"] not in STORY_SKUS]
    skus = []
    for p in g.pick(prods, 70):
        margin = float(p["retail_price_gbp"]) - float(p["unit_cost_gbp"])
        u = r.randint(3000, 90000)
        cpu = min(r.uniform(0.9, 3.2), margin * 0.55)          # always profitable
        w, t = r.uniform(0.35, 0.5), r.uniform(0.3, 0.4)
        h = 1 - w - t
        skus.append({"sku": p["sku"], "annual_units_sold": u, "warehousing_cost_gbp": round(u * cpu * w),
                     "transport_cost_gbp": round(u * cpu * t), "handling_cost_gbp": round(u * cpu * h),
                     "as_of_date": as_of})

    # ---- benchmarks (percent of sales)
    bm = [
        ("warehousing", 5.0, 4.2, "Retail Logistics Benchmark Survey", "medium",
         "Benchmark excludes DC overhead pools; ours includes them, so our figure is slightly overstated."),
        ("outbound_transport", 4.2, 3.5, "Retail Logistics Benchmark Survey", "high",
         "Both are outbound DC-to-store and DC-to-customer carriage; broadly like for like."),
        ("returns", 1.5, 1.0, "Retail Logistics Benchmark Survey", "low",
         "Benchmark counts net reverse-logistics cost after customer-paid returns; ours is gross of fees and includes free returns."),
        ("packaging", 0.9, 0.6, "Retail Logistics Benchmark Survey", "medium",
         "Benchmark covers consumer packaging only; ours also includes e-commerce mailers and dunnage."),
        ("total", 11.4, 9.5, "Retail Logistics Benchmark Survey", "medium",
         "Sum of the four lines; the benchmark total is stated on its own sample so it is not exactly the sum of line medians."),
    ]
    bench = [{"benchmark_id": f"BENCH-{i:06d}", "cost_line": ln, "industry_median_pct": med, "best_in_class_pct": best,
              "source": src, "comparability": comp, "definition_note": note, "as_of_date": as_of}
             for i, (ln, med, best, src, comp, note) in enumerate(bm, 1)]

    return {"cost_pools": pools, "allocation_drivers": drivers, "scenarios": scenarios,
            "cost_components_dc": comps, "channel_activity": activity, "channel_costs": ccosts,
            "ecom_costs": ecom, "sku_costs": skus, "logistics_benchmarks": bench}
