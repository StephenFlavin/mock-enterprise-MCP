"""Generate budgeting data: cost budgets and actuals, operating-profit variances, forecasts, scenarios,
margin plans, levers, programmes and investment cases.

Periods are stored as a date inside the month (the 14th) so they move with the data at runtime;
tools turn them into 2026-09 style labels."""
from datetime import date, timedelta
import math

DC_CCS = ["CC-2101", "CC-2102", "CC-2103", "CC-2104", "CC-2105"]
STORE_CCS = ["CC-2106", "CC-2107", "CC-2108", "CC-2109", "CC-2110", "CC-2111", "CC-2112"]
ECOM_CC = "CC-2123"
TRANSPORT_CC = "CC-2124"

EXPENSE_CATEGORIES = [
    ("Facilities", "utilities", "Electricity, gas and water"),
    ("Facilities", "maintenance", "Building and equipment repairs and maintenance"),
    ("Facilities", "cleaning", "Contract cleaning"),
    ("Facilities", "security", "Guarding and alarm monitoring"),
    ("Facilities", "rent & rates", "Rent, business rates and service charges"),
    ("Logistics", "air freight", "Inbound and expedited air freight"),
    ("Logistics", "road transport", "Road haulage and trunking"),
    ("Logistics", "packaging", "Cartons, polybags and pallets"),
    ("People", "staff", "Payroll, agency labour and benefits"),
    ("Technology", "systems", "Software, licences and hosting"),
]
FACILITIES = {"utilities", "maintenance", "cleaning", "security", "rent & rates"}


def add_months(y, m, n):
    t = y * 12 + (m - 1) + n
    return t // 12, t % 12 + 1


def mdate(y, m):
    return date(y, m, 14)


# ----- finance maths (same as hooks.py) -----
def _cashflows(capex, annual_benefit, years, build_months=0, delay_months=0):
    start = build_months + delay_months
    n = start + int(round(years * 12))
    flows = [-capex] + [0.0] * n
    for i in range(start + 1, n + 1):
        flows[i] = annual_benefit / 12.0
    return flows


def _npv(flows, rate):
    mr = (1 + rate) ** (1 / 12.0) - 1
    return sum(f / (1 + mr) ** i for i, f in enumerate(flows))


def _irr(flows):
    lo, hi = -0.9, 5.0
    if _npv(flows, lo) * _npv(flows, hi) > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if _npv(flows, lo) * _npv(flows, mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def _payback_months(flows):
    cum = 0.0
    for i, f in enumerate(flows):
        prev = cum
        cum += f
        if cum >= 0 and i > 0:
            return i - 1 + (-prev / f if f else 0)
    return None


def generate(g):
    r = g.rng
    as_of = g.as_of
    cy, cm = as_of.year, as_of.month
    ccs = [c["cost_centre_id"] for c in g.master("cost_centres")]

    # ---------------- expense categories ----------------
    expense_categories = [{"category_group": grp, "category": c, "description": d} for grp, c, d in EXPENSE_CATEGORIES]

    # ---------------- cost budgets and actuals ----------------
    # k = months relative to the current month: -12 (a year ago) .. -1 (last month, last closed) .. +3
    ks = list(range(-12, 4))
    budget_lines, actual_costs = [], []
    util_season = {1: 1.25, 2: 1.2, 3: 1.05, 4: 0.95, 5: 0.9, 6: 0.85, 7: 0.85, 8: 0.85, 9: 0.92, 10: 1.05, 11: 1.18, 12: 1.28}
    peak_season = {11: 1.12, 12: 1.2, 1: 0.95}

    def cats_for(cc):
        if cc in DC_CCS:
            return ["staff", "utilities", "maintenance", "cleaning", "security", "systems", "packaging"]
        if cc in STORE_CCS:
            return ["staff", "utilities", "maintenance", "cleaning", "security", "rent & rates"]
        if cc == ECOM_CC:
            return ["staff", "systems", "packaging"]
        if cc == TRANSPORT_CC:
            return ["staff", "systems", "air freight", "road transport"]
        return ["staff", "systems"]

    def base_amount(cc, cat):
        dc, st = cc in DC_CCS, cc in STORE_CCS
        rng = {
            ("staff", "dc"): (380, 620), ("staff", "st"): (90, 180), ("staff", "hq"): (120, 300),
            ("utilities", "dc"): (150, 230), ("utilities", "st"): (35, 70),
            ("maintenance", "dc"): (60, 110), ("maintenance", "st"): (18, 40),
            ("cleaning", "dc"): (28, 45), ("cleaning", "st"): (10, 20),
            ("security", "dc"): (22, 35), ("security", "st"): (8, 14),
            ("rent & rates", "st"): (55, 110),
            ("systems", "dc"): (25, 40), ("systems", "hq"): (20, 80),
            ("packaging", "dc"): (45, 80), ("packaging", "hq"): (60, 60),
        }
        kind = "dc" if dc else "st" if st else "hq"
        lo, hi = rng.get((cat, kind), (20, 60))
        return round(r.uniform(lo, hi) * 1000 / 500) * 500

    # explicit Transport cost centre air and road series (k = -12 .. -1)
    air_actual = [98, 162, 171, 91, 84, 88, 93, 95, 101, 126, 139, 148]
    air_budget = {-12: 100, -11: 150, -10: 150, -9: 95, -8: 95, -7: 95, -6: 95, -5: 95, -4: 100, -3: 100, -2: 100, -1: 100,
                  0: 100, 3: 95}   # Nov and Dec this year are covered by the peak line in seed/budget_lines.csv
    road_actual = [292, 318, 325, 284, 278, 286, 291, 296, 299, 302, 305, 308]
    road_budget = {-12: 290, -11: 300, -10: 300, -9: 285, -8: 285, -7: 285, -6: 290, -5: 290, -4: 295, -3: 295, -2: 295, -1: 295,
                   0: 300, 1: 305, 2: 305, 3: 290}

    # facilities story: (cc, category) -> recurring extra share of budget, one-offs {k: gbp}, note
    story = {
        ("CC-2101", "utilities"): (0.55, {}, "New energy supply contract from January, unit rates about a third higher"),
        ("CC-2103", "maintenance"): (0.40, {-7: 450000.0, -4: 180000.0},
                                     "Racking and conveyor repairs above plan; one-offs: bay A-C roof replacement and sprinkler repair"),
        ("CC-2105", "utilities"): (0.50, {}, "US summer demand charges and peak power tariff"),
        ("CC-2108", "rent & rates"): (0.12, {-5: 260000.0}, "Business rates revaluation; backdated charge booked as a one-off"),
        ("CC-2111", "cleaning"): (0.90, {}, "New cleaning contractor on higher day rates"),
    }
    ytd_k = [k for k in ks if k < 0 and add_months(cy, cm, k)[0] == cy]   # this calendar year, closed months

    cell_actual = {}   # (cc, cat, k) -> (budget, actual, one_off, note)
    for cc in ccs:
        for cat in cats_for(cc):
            base = base_amount(cc, cat) if cc != TRANSPORT_CC or cat in ("staff", "systems") else None
            for k in ks:
                y, m = add_months(cy, cm, k)
                if cc == TRANSPORT_CC and cat == "air freight":
                    if k not in air_budget:
                        continue
                    bud = air_budget[k] * 1000.0
                elif cc == TRANSPORT_CC and cat == "road transport":
                    bud = road_budget[k] * 1000.0
                else:
                    f = util_season[m] if cat == "utilities" else peak_season.get(m, 1.0) if cat in ("staff", "packaging") else 1.0
                    bud = round(base * f / 500) * 500.0
                bl = {"budget_line_id": f"BL-{len(budget_lines) + 1:06d}", "cost_centre_id": cc, "category": cat,
                      "period_date": mdate(y, m), "value_gbp": bud, "notes": "", "updated_at": as_of - timedelta(days=60)}
                budget_lines.append(bl)
                if k >= 0:
                    continue
                note, one_off = "", 0.0
                if cc == TRANSPORT_CC and cat == "air freight":
                    act = air_actual[k + 12] * 1000.0
                    if k >= -3:
                        note = "Late supplier production, more orders expedited by air"
                elif cc == TRANSPORT_CC and cat == "road transport":
                    act = road_actual[k + 12] * 1000.0
                elif (cc, cat) in story:
                    extra, ones, note = story[(cc, cat)]
                    act = bud * (1 + extra) * (1 + r.gauss(0, 0.012)) if k in ytd_k else bud * (1 + r.gauss(0.01, 0.02))
                    if k in ytd_k:
                        one_off = ones.get(k, 0.0)
                        act += one_off
                    else:
                        note = ""
                else:
                    act = bud * (1 + r.gauss(0.012, 0.025))
                    if cat not in FACILITIES and r.random() < 0.05:
                        one_off = round(act * r.choice([0.1, 0.15, 0.2]), 2)
                cell_actual[(cc, cat, k)] = [bud, act, one_off, note]

    # scale the non-story facilities cells so the year-to-date facilities overspend is 14.0% of budget
    fac = [(key, v) for key, v in cell_actual.items() if key[1] in FACILITIES and key[2] in ytd_k]
    tot_b = sum(v[0] for _, v in fac)
    story_keys = set(story)
    story_a = sum(v[1] for key, v in fac if (key[0], key[1]) in story_keys)
    other_a = sum(v[1] for key, v in fac if (key[0], key[1]) not in story_keys)
    delta = (1.14 * tot_b - story_a) / other_a - 1
    for key, v in cell_actual.items():
        if key[1] in FACILITIES and (key[0], key[1]) not in story_keys:
            v[1] *= (1 + delta)
    gen_info = {"facilities_budget_ytd": tot_b, "noise_shift_pct": delta * 100}
    for (cc, cat, k), (bud, act, one_off, note) in cell_actual.items():
        y, m = add_months(cy, cm, k)
        actual_costs.append({"cost_centre_id": cc, "category": cat, "period_date": mdate(y, m), "actual_gbp": round(act, 2),
                             "one_off_gbp": round(one_off, 2), "notes": note, "updated_at": as_of - timedelta(days=5)})

    # ---------------- operating profit by entity and category ----------------
    entities = {"LE-UK": 1.0, "LE-IE": 0.10, "LE-NL": 0.20, "LE-DE": 0.17, "LE-US": 0.20}
    depts = {"Womenswear": 1.3, "Menswear": 0.9, "Kids": 0.8, "Home": 1.1, "Electricals": 0.7, "Beauty": 0.6, "Accessories": 0.4}
    p_season = {1: 0.6, 2: 0.7, 3: 0.9, 4: 0.9, 5: 0.95, 6: 0.95, 7: 0.85, 8: 0.9, 9: 1.0, 10: 1.05, 11: 1.3, 12: 1.6}
    unit_budget = 860000.0
    # planted items for last month (the closed month) and this month so far
    planted = {
        -1: [
            ("LE-UK", "Home", "price", "permanent", -450000, True, "Price investment on small kitchen appliances after a competitor price match; margin rate down about 1 point"),
            ("LE-UK", "Womenswear", "volume", "timing", -350000, True, "Warm September delayed autumn knitwear sales; demand expected to catch up in October and November"),
            ("LE-UK", "Electricals", "cost", "permanent", -300000, True, "Landed cost up on Chinese-sourced electricals: weaker sterling and higher freight rates"),
            ("LE-UK", "Menswear", "mix", "permanent", -120000, True, "Sales mix moved to lower-margin basics"),
            ("LE-UK", "Kids", "one_off", "permanent", -200000, True, "Schoolwear stock write-off after a quality recall"),
            ("LE-UK", "Accessories", "volume", "permanent", 80000, True, "Strong back-to-school accessories demand"),
            ("LE-UK", "Beauty", "cost", "permanent", 50000, True, "Supplier volume rebate received"),
            ("LE-NL", "Home", "cost", "permanent", -140000, True, "Venlo DC outbound freight rates up on German lanes"),
            ("LE-NL", "Womenswear", "cost", "timing", -100000, True, "Autumn marketing spend phased earlier than budget; reverses in Q4"),
            ("LE-US", "Electricals", "price", "permanent", -250000, False, "No explanation received from the entity accountant yet"),
            ("LE-US", "Accessories", "cost", "permanent", -70000, False, "Unexplained cost variance, not yet investigated"),
            ("LE-IE", "Electricals", "price", "permanent", 50000, True, "Higher online selling prices after price harmonisation"),
        ],
        0: [
            ("LE-UK", "Womenswear", "volume", "timing", 140000, True, "Delayed autumn knitwear demand arriving"),
            ("LE-UK", "Home", "price", "permanent", -95000, True, "Continuing price match on small kitchen appliances"),
            ("LE-NL", "Home", "cost", "permanent", -35000, True, "Venlo DC outbound freight rates still above budget"),
            ("LE-US", "Electricals", "price", "permanent", -60000, False, "No explanation received from the entity accountant yet"),
        ],
    }
    explain = {
        "volume": ["Footfall and online traffic different from plan", "Seasonal demand timing", "Promotional uplift smaller than planned"],
        "price": ["Selling price mix against plan", "Competitor price matching on selected lines"],
        "mix": ["Mix shift between categories", "Channel mix moved towards online"],
        "cost": ["Landed cost movement on recent receipts", "Freight rate variance", "Supplier cost increase"],
        "one_off": ["One-off stock adjustment", "One-off supplier credit note"],
    }
    profit_lines, variance_items = [], []
    for k in range(-12, 1):
        y, m = add_months(cy, cm, k)
        frac = (as_of.day / 31.0) if k == 0 else 1.0
        for ent, escale in entities.items():
            for cat, w in depts.items():
                bud = round(unit_budget * escale * w * p_season[m] * frac / 1000) * 1000.0
                items = []
                if k in planted:
                    for (e, c, drv, nat, amt, ok, why) in planted[k]:
                        if e == ent and c == cat:
                            items.append((drv, nat, float(amt), ok, why))
                else:
                    for _ in range(r.choice([1, 1, 2])):
                        drv = r.choice(["volume", "price", "mix", "cost", "cost", "one_off"])
                        amt = round(bud * r.gauss(0, 0.03) / 1000) * 1000.0
                        if amt == 0:
                            continue
                        items.append((drv, r.choice(["permanent", "permanent", "permanent", "timing"]), amt, r.random() < 0.9,
                                      r.choice(explain[drv])))
                tot = sum(i[2] for i in items)
                profit_lines.append({"entity_id": ent, "category": cat, "period_date": mdate(y, m), "budget_profit_gbp": bud,
                                     "actual_profit_gbp": bud + tot, "basis": "month_to_date" if k == 0 else "full_month"})
                for drv, nat, amt, ok, why in items:
                    variance_items.append({"variance_item_id": f"VI-{len(variance_items) + 1:06d}", "entity_id": ent, "category": cat,
                                           "period_date": mdate(y, m), "driver": drv, "nature": nat, "amount_gbp": amt,
                                           "explained": ok, "explanation": why if ok or k in planted else "No explanation received"})

    # ---------------- forecast scenarios, versions, assumptions ----------------
    S = lambda i: f"FSC-{i:06d}"
    forecast_scenarios = [
        {"scenario_id": S(1), "name": "Base", "description": "Base case full-year forecast on current trends",
         "created_date": as_of - timedelta(days=90), "created_by": "EMP-00077",
         "assumptions": "Demand +2.5% year on year; freight rates +10% (contracted for peak); GBP/USD 1.27; markdown 9.4%; shrink 1.1%",
         "status": "active", "demand_change_pct": 0.0, "price_change_pct": 0.0, "freight_change_pct": 0.0, "fx_change_pct": 0.0, "nearshore_mix_pct": 0.0},
        {"scenario_id": S(2), "name": "Severe: weak sterling and tariffs", "description": "Margin planning case with high inflation, weak sterling and new tariffs",
         "created_date": as_of - timedelta(days=60), "created_by": "EMP-00077",
         "assumptions": "Cost inflation 5%; sterling 6% weaker against the dollar; tariffs +5%",
         "status": "active", "demand_change_pct": 0.0, "price_change_pct": 0.0, "freight_change_pct": 0.0, "fx_change_pct": 6.0, "nearshore_mix_pct": 0.0},
        {"scenario_id": S(3), "name": "Mild: easing inflation", "description": "Margin planning case with easing inflation and stable sterling",
         "created_date": as_of - timedelta(days=60), "created_by": "EMP-00077",
         "assumptions": "Cost inflation 2%; sterling stable; no new tariffs",
         "status": "active", "demand_change_pct": 0.0, "price_change_pct": 0.0, "freight_change_pct": 0.0, "fx_change_pct": 0.0, "nearshore_mix_pct": 0.0},
        {"scenario_id": S(4), "name": "FY27 Budget", "description": "Board-approved FY27 budget",
         "created_date": as_of - timedelta(days=240), "created_by": "EMP-00002",
         "assumptions": "Demand +3%; freight flat; GBP/USD 1.25; markdown 8.5%; shrink 1.0%",
         "status": "archived", "demand_change_pct": 0.0, "price_change_pct": 0.0, "freight_change_pct": 0.0, "fx_change_pct": 0.0, "nearshore_mix_pct": 0.0},
    ]

    def mon(days_ago):
        d = as_of - timedelta(days=days_ago)
        return d - timedelta(days=d.weekday())

    FV = lambda rev, gm, ebit, frt: dict(revenue_forecast_gbp=float(rev), gross_margin_pct=float(gm), ebit_forecast_gbp=float(ebit), freight_cost_gbp=float(frt))
    forecast_versions = [
        {"forecast_version_id": "FCST-01001", "forecast_date": as_of, "scenario_id": S(1), "forecast_type": "forecast",
         **FV(1224000000, 33.6, 68264000, 68500000),
         "notes": "FY27 full-year forecast after September close. Gross margin 1.4 points below budget (freight, FX and markdown); opex held below budget",
         "status": "current", "created_at": as_of},
        {"forecast_version_id": "FCST-00701", "forecast_date": mon(91), "scenario_id": S(1), "forecast_type": "forecast",
         **FV(1262000000, 34.8, 81500000, 62500000),
         "notes": "July forecast for FY27 (made at the start of Q3)", "status": "superseded", "created_at": mon(91)},
        {"forecast_version_id": "FCST-00401", "forecast_date": mon(182), "scenario_id": S(1), "forecast_type": "forecast",
         **FV(1275000000, 35.0, 85200000, 62000000),
         "notes": "April forecast for FY27", "status": "superseded", "created_at": mon(182)},
        {"forecast_version_id": "FCST-BUD27", "forecast_date": as_of - timedelta(days=240), "scenario_id": S(4), "forecast_type": "budget",
         **FV(1236000000, 35.0, 88000000, 62000000),
         "notes": "FY27 board-approved budget", "status": "superseded", "created_at": as_of - timedelta(days=240)},
    ]

    def assum(ver, rows):
        return [{"forecast_version_id": ver, "driver": d, "assumed_value": a, "actual_value": ac, "unit": u, "note": n}
                for d, a, ac, u, n in rows]

    forecast_assumptions = (
        assum("FCST-01001", [
            ("Demand growth vs last year", 2.5, None, "%", "Like-for-like units, store and online"),
            ("Average selling price change", 0.0, None, "%", "Before markdown"),
            ("Freight rate index change", 10.0, None, "%", "Air and ocean rates, as already contracted for peak"),
            ("GBP/USD rate", 1.27, None, "rate", "Budget rate 1.25; 60% of Q4 dollar need hedged"),
            ("Markdown rate", 9.4, None, "% of sales", "Higher clearance of autumn lines"),
            ("Shrink rate", 1.1, None, "% of sales", ""),
            ("Opex inflation", 3.0, None, "%", "Wage and energy"),
        ]) +
        assum("FCST-00701", [
            ("Demand growth vs last year", 2.5, -1.2, "%", "Q3 like-for-like units came in below last year, not above"),
            ("Average selling price change", 0.0, -0.5, "%", "Price matching in Home and Electricals"),
            ("Freight rate index change", 0.0, 15.0, "%", "Air freight used more than planned because of late supplier production"),
            ("GBP/USD rate", 1.28, 1.26, "rate", "Sterling weaker than assumed"),
            ("Markdown rate", 9.0, 9.6, "% of sales", "Extra clearance of summer lines"),
            ("Shrink rate", 1.1, 1.1, "% of sales", "As forecast"),
            ("Opex inflation", 3.0, 3.1, "%", "Close to forecast"),
        ]) +
        assum("FCST-00401", [
            ("Demand growth vs last year", 3.5, -1.2, "%", "Too optimistic"),
            ("Freight rate index change", 0.0, 15.0, "%", "Not anticipated"),
            ("GBP/USD rate", 1.30, 1.26, "rate", "Sterling weaker than assumed"),
            ("Markdown rate", 8.5, 9.6, "% of sales", ""),
        ])
    )

    # forecast versus actual, by month and quarter (period_date is mid-period)
    q3_mid = mdate(*add_months(cy, cm, -2)) + timedelta(days=1)      # the 15th of the middle month of last quarter
    months_q3 = {-3: mdate(*add_months(cy, cm, -3)), -2: mdate(*add_months(cy, cm, -2)), -1: mdate(*add_months(cy, cm, -1))}
    forecast_actuals = []

    def fa(ver, pdate, ptype, line, unit, f, a):
        forecast_actuals.append({"forecast_version_id": ver, "period_date": pdate, "period_type": ptype, "line_item": line,
                                 "unit": unit, "forecast_value": round(float(f), 2), "actual_value": round(float(a), 2)})

    # July forecast: Q3 revenue 321.0m forecast, 308.16m actual (-4.0%), driven by units
    q3 = {  # line: (forecast, actual, unit)
        "revenue": (321000000, 308160000, "GBP"),
        "units": (6420000, 6195300, "units"),
        "avg_selling_price": (50.0, 49.74, "GBP"),
        "gross_profit": (111708000, 106007040, "GBP"),
        "gross_margin_pct": (34.8, 34.4, "%"),
        "freight": (15900000, 18300000, "GBP"),
        "markdown": (28890000, 29583360, "GBP"),
        "opex": (85900000, 85400000, "GBP"),
        "ebit": (25808000, 20607040, "GBP"),
    }
    for line, (f, a, u) in q3.items():
        fa("FCST-00701", q3_mid, "quarter", line, u, f, a)
    monthly_rev = {-3: (104000000, 101500000), -2: (106000000, 103400000), -1: (111000000, 103260000)}
    monthly_units = {-3: (2080000, 2010000), -2: (2120000, 2062000), -1: (2220000, 2123300)}
    monthly_gp = {-3: (36192000, 34900000), -2: (36888000, 35630000), -1: (38628000, 35477040)}
    for k, d in months_q3.items():
        fa("FCST-00701", d, "month", "revenue", "GBP", *monthly_rev[k])
        fa("FCST-00701", d, "month", "units", "units", *monthly_units[k])
        fa("FCST-00701", d, "month", "gross_profit", "GBP", *monthly_gp[k])
    # April forecast: bigger miss
    fa("FCST-00401", q3_mid, "quarter", "revenue", "GBP", 330000000, 308160000)
    fa("FCST-00401", q3_mid, "quarter", "units", "units", 6600000, 6195300)
    fa("FCST-00401", q3_mid, "quarter", "gross_profit", "GBP", 115500000, 106007040)
    fa("FCST-00401", q3_mid, "quarter", "ebit", "GBP", 28600000, 20607040)

    # ---------------- margin plans ----------------
    plan_base = {"Housewares": 41.0, "Womenswear": 55.0, "Menswear": 52.0, "Kidswear": 50.0, "Electricals": 28.0}
    scen_assump = {S(1): (3.0, 2.0), S(2): (5.0, 6.0), S(3): (2.0, 0.0)}   # inflation %, FX cost impact %
    cat_tariff = {"Housewares": (1.5, 5.0, 0.0), "Womenswear": (1.0, 3.0, 0.0), "Menswear": (1.0, 3.0, 0.0),
                  "Kidswear": (0.8, 2.5, 0.0), "Electricals": (3.0, 8.0, 0.0)}   # tariff cost impact % in Base, Severe, Mild
    margin_plans = []
    for si, (sid_, (infl, fx)) in enumerate(scen_assump.items()):
        for cat, mg in plan_base.items():
            margin_plans.append({"scenario_id": sid_, "category": cat, "planned_margin_pct": mg, "inflation_assumption_pct": infl,
                                 "fx_impact_pct": fx,
                                 "fx_assumption": "Sterling 6% weaker against the dollar" if fx >= 6 else "Sterling about 2% weaker against the dollar" if fx else "Sterling stable against the dollar",
                                 "tariff_impact_pct": cat_tariff[cat][si],
                                 "notes": f"Next-season margin plan for {cat}, before inflation, FX and tariff pressure",
                                 "updated_at": as_of - timedelta(days=30)})

    # ---------------- margin actions and mitigation levers ----------------
    margin_actions = [
        ("MRA-0001", "All", "product cost", "Renegotiate FOB prices with the top 20 suppliers", 14200000, 12, 70),
        ("MRA-0002", "Womenswear", "markdown", "Cut markdown depth on autumn knitwear and outerwear", 9600000, 6, 75),
        ("MRA-0003", "All", "freight", "Move non-urgent air freight to sea and consolidate inbound loads", 6100000, 8, 80),
        ("MRA-0004", "All", "shrink", "Targeted shrink programme in the 40 worst stores", 5000000, 16, 65),
        ("MRA-0005", "Housewares", "price", "Reprice non-key-value lines by 2%", 4200000, 4, 80),
        ("MRA-0006", "All", "fx", "Extend dollar hedge cover from 60% to 80% for next season", 3400000, 3, 85),
        ("MRA-0007", "Electricals", "duty", "Use duty drawback and tariff engineering on electricals", 2400000, 10, 60),
        ("MRA-0008", "Menswear", "mix", "Shift mix towards higher-margin premium basics", 1800000, 14, 55),
    ]
    margin_actions = [{"action_id": a, "category": c, "driver": d, "description": t, "estimated_value_gbp": float(v),
                       "lead_time_weeks": lt, "confidence_pct": cf} for a, c, d, t, v, lt, cf in margin_actions]
    mitigation_levers = [
        ("LEV-0001", "Reduce promotional intensity and markdown depth", "revenue", 6500000, 2, False, "EBIT per year"),
        ("LEV-0002", "Hiring freeze and defer discretionary opex", "cost reduction", 9000000, 4, False, "EBIT per year"),
        ("LEV-0003", "Targeted price increases on non-key-value lines", "revenue", 12000000, 4, False, "EBIT per year"),
        ("LEV-0004", "Switch air freight to sea and consolidate loads", "cost reduction", 5200000, 8, False, "EBIT per year"),
        ("LEV-0005", "Supplier cost-down renegotiation", "cost reduction", 7800000, 12, False, "EBIT per year"),
        ("LEV-0006", "Nearshore 20% of sourcing", "cost structure", 8500000, 24, False, "EBIT per year once complete"),
        ("LEV-0007", "Extend supplier payment terms by 10 days", "working capital", 25000000, 8, True, "one-off cash"),
    ]
    mitigation_levers = [{"lever_id": a, "name": n, "lever_type": t, "estimated_value_gbp": float(v), "lead_time_weeks": lt,
                          "one_time": ot, "value_basis": vb} for a, n, t, v, lt, ot, vb in mitigation_levers]

    # ---------------- programmes (unchanged shape) ----------------
    programmes, programme_costs = [], []
    programme_types = ["cost_saving", "revenue", "capex", "transformation"]
    for i in range(8):
        prog_id = f"PGM-{i + 1:06d}"
        budget = r.choice([500000, 1000000, 2000000, 5000000])
        programmes.append({
            "programme_id": prog_id,
            "name": r.choice(["Margin Recovery", "Shrink Reduction", "DC Automation", "ERP Go-Live", "Nearshoring Pilot", "Omnichannel", "Analytics Platform", "Logistics Optimization"]),
            "description": "Key strategic initiative", "budget_gbp": budget,
            "start_date": as_of - timedelta(days=r.randint(30, 180)), "end_date": as_of + timedelta(days=r.randint(30, 365)),
            "status": r.choice(["approved", "in_progress", "completed"]), "type": programme_types[i % 4]})
        seen = set()
        for week in g.weeks(24):
            period_str = week.strftime("%Y-%m")
            if (prog_id, period_str) in seen:
                continue
            seen.add((prog_id, period_str))
            forecast = budget / 24 * r.gauss(1.0, 0.2)
            actual = forecast * r.gauss(1.0, 0.15) if week < as_of else 0
            programme_costs.append({"programme_id": prog_id, "period": period_str, "forecast_gbp": round(forecast, 2),
                                    "actual_gbp": round(max(0, actual), 2),
                                    "burn_rate_pct": round(actual / forecast * 100 if forecast > 0 else 0, 1),
                                    "updated_at": as_of - timedelta(days=5)})

    # ---------------- investment cases ----------------
    investment_cases = []
    choices = [("Daventry sortation upgrade", "DC2", 3000000), ("Leeds returns automation", "DC3", 2000000),
               ("Venlo pick-to-light", "DC4", 1000000), ("Columbus mezzanine expansion", "DC5", 5000000),
               ("E-commerce platform replatform", "HQ1", 5000000), ("Store refit programme", "ST214", 2000000),
               ("Daventry solar roof", "DC2", 1000000), ("Analytics platform", "HQ1", 500000)]
    for i, (title, site, capex) in enumerate(choices):
        saving = round(capex * r.uniform(0.18, 0.30), 2)
        flows = _cashflows(capex, saving, 7, build_months=6)
        irr = _irr(flows)
        investment_cases.append({
            "investment_case_id": f"INV-{i + 1:06d}", "title": title, "description": "Capital investment proposal", "site_id": site,
            "capex_gbp": float(capex), "annual_saving_gbp": saving, "annual_revenue_gbp": 0.0,
            "payback_period_months": round(_payback_months(flows) or 0, 1), "npv_gbp": round(_npv(flows, 0.10), 2),
            "irr_pct": round((irr or 0) * 100, 1), "status": r.choice(["proposal", "approved", "implemented"]),
            "created_date": as_of - timedelta(days=r.randint(30, 180)),
            "assumptions": "10% discount rate, 7-year horizon, 6-month build", "build_months": 6, "project_life_years": 7})
    flows = _cashflows(12000000, 3400000, 10, build_months=12)
    investment_cases.append({
        "investment_case_id": "INV-900001", "title": "Northampton DC automation", "description": "Automated storage and sortation at Northampton DC1",
        "site_id": "DC1", "capex_gbp": 12000000.0, "annual_saving_gbp": 3400000.0, "annual_revenue_gbp": 0.0,
        "payback_period_months": round(_payback_months(flows), 1), "npv_gbp": round(_npv(flows, 0.10), 2),
        "irr_pct": round(_irr(flows) * 100, 1), "status": "proposal", "created_date": as_of - timedelta(days=45),
        "assumptions": "Savings of £3.4m a year from labour and throughput once live; 12-month build; 10-year life; 10% discount rate",
        "build_months": 12, "project_life_years": 10})

    return {
        "expense_categories": expense_categories,
        "budget_lines": budget_lines,
        "actual_costs": actual_costs,
        "profit_lines": profit_lines,
        "variance_items": variance_items,
        "forecast_versions": forecast_versions,
        "forecast_scenarios": forecast_scenarios,
        "forecast_assumptions": forecast_assumptions,
        "forecast_actuals": forecast_actuals,
        "margin_plans": margin_plans,
        "margin_actions": margin_actions,
        "mitigation_levers": mitigation_levers,
        "programmes": programmes,
        "programme_costs": programme_costs,
        "investment_cases": investment_cases,
    }
