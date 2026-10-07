"""Network design system: scenarios, DC profiles, shortlist, volumes, forecasts, inefficiencies, outage assumptions."""
from datetime import timedelta

DAYS = 365  # operating days used to annualise daily volumes
PEAK_DAYS = 350  # days a year at peak operating rate (annual peak capacity)

# (site_id, label, fixed overhead, rent, labour, handling GBP/unit, transport GBP/unit, avg units/day, peak units/day, region, yoy growth %)
DC1 = ("DC1", "", 700000, 1500000, 3300000, 1.60, 2.20, 8000, 11000, "UK Midlands", 4.8)
DC2 = ("DC2", "", 500000, 1200000, 1900000, 1.95, 2.60, 3200, 4500, "UK Midlands", 6.5)
DC3 = ("DC3", "", 400000, 900000, 1400000, 1.75, 2.30, 2500, 3500, "UK North", 3.9)

SCENARIOS = [
    # id, name, description, type, dc_count, secondary, tertiary, stores days, customer days, redundancy, setup, months, ecom uplift per pt, profiles
    ("NS-000001", "Baseline: Keep Northampton as main DC",
     "Current network, no new capacity: Northampton (DC1) is the national DC, with Daventry (DC2) and Leeds (DC3) as satellites.",
     "baseline", 3, "DC2", "", 2.2, 2.9, 55.0, 0, 0, 1.0,
     [DC1, DC2, DC3]),
    ("NS-000002", "Second owned DC in the Midlands",
     "Build or lease a second owned Midlands DC (shortlist site Daventry Gateway Park) alongside Northampton; takes about 3,500 units a day off DC1 and DC2.",
     "owned_dc", 4, "DC2", "", 1.8, 2.4, 70.0, 6500000, 18, 0.6,
     [("DC1", "", 700000, 1500000, 3300000, 1.60, 2.00, 6500, 11000, "UK Midlands", 4.8),
      ("DC2", "", 500000, 1200000, 1900000, 1.95, 2.35, 2000, 4500, "UK Midlands", 6.5),
      ("DC3", "", 400000, 900000, 1400000, 1.75, 2.15, 1700, 3500, "UK North", 3.9),
      ("", "New owned Midlands DC", 600000, 1900000, 2600000, 1.50, 1.60, 3500, 5500, "UK Midlands", 0.0)]),
    ("NS-000003", "Third-party partner DC in the Midlands",
     "Keep the current network and add a third-party logistics partner for Midlands and North volume on a 5-year contract; no capex but higher unit handling fees.",
     "partner_dc", 4, "DC2", "", 2.0, 2.6, 62.0, 1400000, 6, 0.8,
     [("DC1", "", 700000, 1500000, 3300000, 1.60, 2.10, 7200, 11000, "UK Midlands", 4.8),
      ("DC2", "", 500000, 1200000, 1900000, 1.95, 2.45, 2600, 4500, "UK Midlands", 6.5),
      ("DC3", "", 400000, 900000, 1400000, 1.75, 2.25, 1900, 3500, "UK North", 3.9),
      ("", "Partner 3PL Midlands (contract)", 100000, 600000, 400000, 2.30, 2.00, 2000, 3200, "UK Midlands", 0.0)]),
    ("NS-000004", "Close DC2 and consolidate into DC1 and DC3",
     "Close the small southern-Midlands DC (Daventry, DC2) and absorb its volume into Northampton (DC1) and Leeds (DC3). Lower rent and labour, longer runs to southern stores, less resilience.",
     "consolidation", 2, "DC3", "", 2.5, 3.2, 38.0, 2800000, 9, 1.0,
     [("DC1", "", 750000, 1500000, 3900000, 1.58, 2.45, 10200, 11000, "UK Midlands", 4.8),
      ("DC3", "", 400000, 900000, 1600000, 1.72, 2.35, 3500, 4200, "UK North", 3.9)]),
]

SOURCING = [
    # id, name, description, type, lead days, cost change pct, origin region
    ("NS-000005", "Sourcing baseline: southern China",
     "Current inbound sourcing: Pearl River Delta factories shipped via Yantian and Shekou to the UK.",
     "baseline", 38.0, 0.0, "Southern China"),
    ("NS-000006", "Diversify to Vietnam and Cambodia",
     "Move tariff-exposed volume to Vietnam and Cambodia factories shipped via Cai Mep. Longer qualification and a premium on unit cost, partly offset by lower tariffs.",
     "sourcing_shift", 43.0, 5.5, "Vietnam and Cambodia"),
    ("NS-000007", "Diversify to India and Bangladesh",
     "Move tariff-exposed volume to India and Bangladesh factories shipped via Chittagong and Nhava Sheva. Cheapest labour, longest transit.",
     "sourcing_shift", 47.0, 3.2, "India and Bangladesh"),
    ("NS-000008", "Nearshore to Turkey and Portugal",
     "Move tariff-exposed volume to Turkey and Portugal factories delivered by road and short-sea. Fastest replenishment but a large unit cost premium.",
     "sourcing_shift", 14.0, 12.5, "Turkey and Portugal"),
]

CANDIDATES = [
    ("SC-900001", "Daventry Gateway Park", "UK Midlands", 1900000, 400000, 78.0, 84.0, 30.0,
     "Modern big-box on the M1/A5 corridor near existing Daventry operations. Strong labour pool but competes with several 3PLs for agency staff. Planning permission in place; highest rent of the three.",
     "Enterprise zone business rates relief (3 years); local authority recruitment grant of about 1,500 GBP per new hire."),
    ("SC-900002", "Corby Enterprise Park", "UK Midlands", 1500000, 380000, 62.0, 66.0, 48.0,
     "Cheaper rent and a ready-built unit, but thinner labour supply and A14/A43 congestion on the way to the M1. Planning needs a change-of-use variation.",
     "Enterprise zone business rates relief (5 years); capital grant up to 250,000 GBP for 150 or more jobs."),
    ("SC-900003", "Doncaster iPort", "UK North", 1700000, 450000, 70.0, 74.0, 72.0,
     "Rail-served site near the M18/A1(M) with good northern coverage. High planning risk: the green-belt boundary is contested and a judicial review is pending. Competes with two large retailers for labour.",
     "Freeport customs and tax benefits; skills fund contribution towards training."),
]

LABOUR = [
    ("LC-000001", "UK South", 28000, 2400, 22.0, 1200),
    ("LC-000002", "UK Midlands", 26500, 2800, 20.0, 1100),
    ("LC-000003", "UK North", 25000, 3200, 18.0, 1000),
    ("LC-000004", "Scotland", 25500, 1500, 17.0, 1000),
    ("LC-000005", "Ireland", 27500, 1800, 19.0, 1150),
    ("LC-000006", "EU Central", 21500, 4200, 24.0, 900),
]

# id, type, origin, dest, units/yr, current cost, saving, fix cost, lead days, status, root cause, confidence, +/- range pct
INEFFICIENCIES = [
    ("INE-900001", "cross_ship", "DC1", "ST201", 210000, 410000, 260000, 150000, 45, "identified", "inventory_placement", "medium", 20.0),
    ("INE-900002", "split_order", "DC2", "", 175000, 330000, 190000, 120000, 60, "identified", "inventory_placement", "high", 10.0),
    ("INE-900003", "long_haul", "DC1", "ST202", 150000, 360000, 175000, 640000, 120, "identified", "site_location", "low", 35.0),
    ("INE-900004", "underutilised", "DC3", "", 0, 300000, 95000, 300000, 90, "analysing", "site_location", "medium", 25.0),
    ("INE-900005", "cross_ship", "DC2", "ST141", 90000, 140000, 60000, 45000, 30, "identified", "inventory_placement", "high", 10.0),
    ("INE-900006", "split_order", "DC1", "", 70000, 110000, 25000, 30000, 30, "identified", "inventory_placement", "high", 10.0),
    ("INE-900007", "long_haul", "DC1", "ST221", 40000, 120000, 55000, 400000, 150, "scheduled", "site_location", "low", 40.0),
    ("INE-900008", "cross_ship", "DC3", "ST142", 60000, 95000, 70000, 40000, 30, "fixed", "inventory_placement", "high", 10.0),
]

# site, annual probability %, cause, expedite GBP/unit, margin GBP/unit, inventory cost GBP/unit, note
OUTAGE = [
    ("DC1", 3.0, "Major fire or WMS-wide outage", 2.80, 9.50, 14.0,
     "Northampton is the national DC: it holds the full range and replenishes every store."),
    ("DC2", 2.0, "Sortation system failure", 2.20, 9.50, 14.0,
     "Daventry is the e-commerce DC; stock is a subset of the range."),
    ("DC3", 2.0, "Flood or racking collapse", 2.20, 9.50, 14.0,
     "Leeds is the regional and returns DC for the North."),
]

# id, route, origin, via site, via label, dest region, handling, transport, inventory holding, fixed per week, peak handling uplift %, peak transport uplift %
ROUTES = [
    ("RC-900001", "direct_from_dc", "DC1", "", "", "UK North", 0.62, 1.35, 0.22, 0, 15.0, 40.0),
    ("RC-900002", "via_cross_dock", "DC1", "DC3", "Leeds cross-dock", "UK North", 0.95, 1.05, 0.31, 9000, 8.0, 10.0),
    ("RC-900003", "via_regional_hub", "DC1", "", "Doncaster partner hub", "UK North", 1.05, 1.10, 0.30, 14000, 12.0, 18.0),
    ("RC-900004", "direct_from_dc", "DC1", "", "", "Scotland", 0.62, 1.85, 0.25, 0, 15.0, 45.0),
    ("RC-900005", "via_cross_dock", "DC1", "", "Carlisle partner cross-dock", "Scotland", 0.98, 1.40, 0.34, 11000, 8.0, 12.0),
    ("RC-900006", "direct_from_dc", "DC1", "", "", "UK Midlands", 0.62, 0.95, 0.20, 0, 15.0, 30.0),
    ("RC-900007", "direct_from_dc", "DC1", "", "", "UK South", 0.62, 1.30, 0.22, 0, 15.0, 35.0),
    ("RC-900008", "direct_from_dc", "DC1", "", "", "Ireland", 0.62, 2.40, 0.28, 0, 15.0, 30.0),
]

REGIONS = [("UK South", 0.30), ("UK Midlands", 0.20), ("UK North", 0.22), ("Scotland", 0.06),
           ("Ireland", 0.06), ("EU Central", 0.16)]


def _profile_rows(sid, profiles, labels, n0):
    rows = []
    for i, (site, label, fixed, rent, labour, h, t, avg, peak, region, growth) in enumerate(profiles):
        rows.append({
            "profile_id": f"DCP-{n0 + i:06d}", "site_id": site, "site_label": labels.get(site, label) if site else label,
            "scenario_id": sid, "annual_fixed_cost_gbp": fixed, "annual_rent_gbp": rent, "annual_labour_cost_gbp": labour,
            "handling_cost_per_unit_gbp": h, "transport_cost_per_unit_gbp": t,
            "peak_capacity_units_day": peak, "avg_daily_volume_units": avg,
            "utilisation_pct": round(100.0 * avg / peak, 1), "yoy_volume_growth_pct": growth,
            "region": region, "created_at": "2026-09-01T09:00:00"})
    return rows


def generate(g):
    r = g.rng
    labels = {s["site_id"]: s["name"] for s in g.master("sites")}
    scenarios, profiles = [], []
    n0 = 1
    for (sid, name, desc, typ, dcs, sec, ter, ds, dcu, red, setup, months, uplift, profs) in SCENARIOS:
        vol = sum(p[7] for p in profs) * DAYS
        scenarios.append({
            "scenario_id": sid, "name": name, "description": desc, "dc_count": dcs,
            "primary_site_id": "DC1", "secondary_site_id": sec if sec else "", "tertiary_site_id": ter,
            "scenario_type": typ,
            "annual_handling_cost_gbp": round(sum(p[5] * p[7] * DAYS for p in profs)),
            "annual_transport_cost_gbp": round(sum(p[6] * p[7] * DAYS for p in profs)),
            "annual_rent_gbp": sum(p[3] for p in profs),
            "annual_labour_cost_gbp": sum(p[4] for p in profs),
            "annual_overhead_gbp": sum(p[2] for p in profs),
            "avg_delivery_days_stores": ds, "avg_delivery_days_customers": dcu,
            "peak_capacity_units": sum(p[8] for p in profs) * PEAK_DAYS,
            "redundancy_score": red, "one_off_setup_cost_gbp": setup, "implementation_months": months,
            "ecom_transport_uplift_pct": uplift,
            "inbound_lead_time_days": 38.0, "inbound_cost_change_pct": 0.0, "origin_region": "Southern China",
            "status": "active", "created_at": "2026-09-01T09:00:00"})
        profiles += _profile_rows(sid, profs, labels, n0)
        n0 += len(profs)
    base = scenarios[0]
    for (sid, name, desc, typ, lead, cost, origin) in SOURCING:
        s = dict(base)
        s.update({"scenario_id": sid, "name": name, "description": desc, "scenario_type": typ,
                  "one_off_setup_cost_gbp": 0, "implementation_months": 0 if typ == "baseline" else 12,
                  "inbound_lead_time_days": lead, "inbound_cost_change_pct": cost, "origin_region": origin})
        scenarios.append(s)

    site_candidates = [{
        "candidate_id": cid, "site_id": "", "name": name, "region": region, "status": "shortlist",
        "estimated_rent_gbp_pa": rent, "land_area_sqft": sqft, "labour_availability_score": lab,
        "transport_connectivity_score": tr, "planning_risk_score": plan, "notes": notes, "incentives": inc,
        "removed_reason": "", "removed_at": ""} for (cid, name, region, rent, sqft, lab, tr, plan, notes, inc) in CANDIDATES]
    site_candidates.append({
        "candidate_id": "SC-900004", "site_id": "", "name": "Coventry Gateway Business Park", "region": "UK Midlands",
        "status": "removed", "estimated_rent_gbp_pa": 1650000, "land_area_sqft": 300000, "labour_availability_score": 72.0,
        "transport_connectivity_score": 79.0, "planning_risk_score": 40.0,
        "notes": "Partner-led option, dropped earlier: too small for the volume.", "incentives": "",
        "removed_reason": "Lower capacity than Daventry, higher long-term cost.", "removed_at": "2026-07-13T10:00:00"})

    # Volume history: two years of weekly units by region and channel. Latest 52 weeks about 5.0M units, e-commerce about 22%.
    volume_history = []
    for weeks_back in range(104, -1, -1):
        period = g.as_of - timedelta(weeks=weeks_back)
        woy = period.isocalendar()[1]
        season = 1.0 + (0.35 if 46 <= woy <= 52 else 0.0) - (0.12 if woy in (1, 2, 3, 4, 5) else 0.0) + (0.10 if 22 <= woy <= 30 else 0.0)
        growth = 1.0 - 0.05 * weeks_back / 104.0
        ecom_share = 0.165 + 0.055 * (1 - weeks_back / 104.0)
        wholesale_share = 0.15
        total = 90000 * season * growth
        for region, w in REGIONS:
            for channel, share in (("stores", 1 - ecom_share - wholesale_share), ("ecommerce", ecom_share), ("wholesale", wholesale_share)):
                units = int(total * w * share * r.uniform(0.94, 1.06))
                volume_history.append({
                    "vol_id": f"VH-{len(volume_history) + 1:06d}", "period": period, "region": region,
                    "channel": channel, "units": units, "created_at": period.isoformat() + "T06:00:00"})

    growth_plans = [
        ("GP-000001", 2027, "Baseline growth: 5% volume, e-commerce share up 3 points", 5.0, 3.0, "Organic store network expansion", 0.0),
        ("GP-000002", 2028, "Accelerated growth: 7% volume, e-commerce share up 4 points, EU expansion", 7.0, 4.0,
         "New market: Poland and Czechia via DC4 Venlo", 8.0),
        ("GP-000003", 2029, "Mature growth: 5% volume, e-commerce share up 5 points", 5.0, 5.0, "Market consolidation", 0.0),
        ("GP-000004", 2030, "Strategic plan: 5% volume, e-commerce reaches 40% of sales", 5.0, 5.0, "Digital-first retail", 0.0),
    ]
    growth_plans = [{"plan_id": a, "year": b, "description": c, "assumed_total_growth_pct": d, "assumed_ecommerce_growth_pct": e,
                     "assumed_market_expansion": f, "market_volume_uplift_pct": u, "status": "active",
                     "created_at": "2026-09-01T09:00:00"} for (a, b, c, d, e, f, u) in growth_plans]

    # E-commerce share forecast: quarterly, 22% now rising to 40% in 16 quarters (2030).
    ecommerce_forecasts = []
    for q in range(0, 17):
        period = g.as_of + timedelta(days=91 * q)
        ecom = 22.0 + 18.0 * q / 16
        wholesale = round(15.0 - 2.0 * q / 16, 1)
        ecommerce_forecasts.append({
            "ecom_id": f"EF-{q + 1:06d}", "period": period, "ecommerce_share_pct": round(ecom, 1),
            "stores_share_pct": round(100 - ecom - wholesale, 1), "wholesale_share_pct": wholesale,
            "total_volume_units": int(5000000 / 4 * (1.055 ** (q / 4))), "created_at": "2026-09-01T09:00:00"})

    labour_cost_data = [{
        "labour_id": a, "region": b, "annual_cost_per_worker_gbp": c, "availability_workers": d, "turnover_pct": e,
        "training_cost_gbp": f, "record_date": g.as_of} for (a, b, c, d, e, f) in LABOUR]
    labour_cost_data.append({"labour_id": "LC-000007", "region": "UK Midlands", "annual_cost_per_worker_gbp": 25200,
                             "availability_workers": 3100, "turnover_pct": 19.0, "training_cost_gbp": 1050,
                             "record_date": g.days_ago(420)})

    inefficiencies = [{
        "ineff_id": a, "ineff_type": b, "origin_site": c, "dest_site": d, "impacted_units_annually": e,
        "current_cost_gbp": f, "potential_saving_gbp": s, "fix_cost_gbp": fx, "fix_lead_time_days": ld,
        "priority_rank": i + 1, "status": st, "root_cause": rc, "estimate_confidence": conf, "estimate_range_pct": rng,
        "created_at": "2026-09-01T09:00:00"}
        for i, (a, b, c, d, e, f, s, fx, ld, st, rc, conf, rng) in enumerate(INEFFICIENCIES)]

    outage_scenarios = [{
        "outage_id": f"OS-{i + 1:06d}", "primary_site_down": site, "annual_probability_pct": p, "likely_cause": cause,
        "expedite_cost_per_unit_gbp": ex, "margin_per_unit_gbp": m, "inventory_cost_per_unit_gbp": inv, "notes": note,
        "scenario_date": "2026-09-01T09:00:00"} for i, (site, p, cause, ex, m, inv, note) in enumerate(OUTAGE)]

    route_costs = [{
        "route_id": a, "route_type": b, "origin_site": c, "via_site": d, "via_label": e, "dest_region": f,
        "handling_gbp_per_unit": h, "transport_gbp_per_unit": t, "inventory_holding_gbp_per_unit": inv,
        "fixed_cost_gbp_per_week": fx, "peak_handling_uplift_pct": ph, "peak_transport_uplift_pct": pt}
        for (a, b, c, d, e, f, h, t, inv, fx, ph, pt) in ROUTES]

    return {
        "network_scenarios": scenarios, "dc_profiles": profiles, "site_candidates": site_candidates,
        "volume_history": volume_history, "growth_plans": growth_plans, "ecommerce_forecasts": ecommerce_forecasts,
        "labour_cost_data": labour_cost_data, "inefficiencies": inefficiencies, "outage_scenarios": outage_scenarios,
        "route_costs": route_costs,
    }
