"""Treasury management system: cash forecasts, debt facilities, covenants, FX flows and hedging.

Cash forecasts, covenant projections, debt facilities, FX cash flows and hedge pricing are all derived here from
one set of constants so every tool tells the same story. Bank accounts, dividends, hedging outcomes/requests and
alerts are hand-written in seed/*.csv.
"""
from datetime import date, timedelta

START_CASH = 25_000_000.0          # sum of bank_accounts.available_balance_gbp (seed)
RCF_UNDRAWN = 35_000_000.0         # FAC-900002: 50m limit, 15m drawn
GROSS_DEBT_0 = 125_000_000.0       # term loan 60m + RCF 15m + bond 50m
NET_FINANCE_COST = 10_700_000.0    # annual interest incl. lease interest
EBITDA_NOW = 41_000_000.0          # LTM EBITDA at the last covenant test

# Weeks 1-13 are written out so the 13-week story is exact (GBP millions).
IN_13 = [8.4, 8.2, 8.3, 8.5, 8.6, 9.1, 12.0, 13.2, 14.5, 15.0, 10.0, 8.0, 7.8]
OUT_13 = [7.9, 8.3, 9.6, 10.4, 12.3, 8.9, 8.7, 9.0, 9.8, 10.6, 11.2, 9.2, 9.8]
DRIVERS_13 = {
    1: "Normal trading; autumn range receipts",
    3: "Autumn stock payments start to build",
    4: "Peak-season stock buy: weekly supplier payment runs step up",
    5: "Peak-season supplier payment run plus quarterly VAT payment of 3.1m",
    6: "Store refit capex of 1.5m and Friday supplier payment run; sales receipts soft before Black Friday",
    7: "Black Friday trading lifts receipts",
    8: "Black Friday and early Christmas receipts",
    9: "Peak Christmas receipts",
    10: "Term loan quarterly repayment of 2.0m; peak receipts",
    11: "Final dividend of 7.0m paid; receipts fall away after Christmas",
    12: "Post-Christmas trading; supplier payments for January stock",
    13: "January rent quarter-day and VAT-related payments; weak receipts",
}
# Calendar-month multipliers on a 8.3m inflow / 8.4m outflow weekly base, used after week 13.
SEAS_IN = {1: .95, 2: .98, 3: 1.02, 4: 1.0, 5: 1.03, 6: 1.02, 7: 1.03, 8: 1.0, 9: 1.01, 10: 1.03, 11: 1.30, 12: 1.55}
SEAS_OUT = {1: 1.02, 2: .96, 3: .98, 4: .97, 5: .97, 6: .99, 7: 1.0, 8: 1.02, 9: 1.08, 10: 1.12, 11: 1.18, 12: 1.25}

DIVIDEND_WEEKS = {11: 7_000_000.0, 37: 4_500_000.0, 63: 7_500_000.0}   # match seed/dividends.csv
DEBT_WEEKS = {w: 2_000_000.0 for w in range(10, 79, 13)}
VAT_WEEKS = [18, 31, 44, 57, 70]
CAPEX_WEEKS = list(range(14, 79, 8))

SCENARIOS = {
    # id: (scenario, forecast_id, inflow shortfall, outflow saving)
    "base": ("FOR-900001", 0.0, 0.0),
    "downside": ("FOR-900002", 0.04, 0.04),
    "upside": ("FOR-900003", -0.03, -0.015),
}
EBITDA_PATH = {
    "base": [41.4, 41.8, 42.2, 42.6, 43.0, 43.4],
    "downside": [40.2, 38.8, 38.0, 37.6, 37.6, 37.8],
    "upside": [42.0, 43.5, 45.0, 46.5, 47.5, 48.2],
}
TEST_DATES = [date(2026, 12, 31), date(2027, 3, 31), date(2027, 6, 30), date(2027, 9, 30), date(2027, 12, 31),
              date(2028, 3, 31)]

# USD / EUR payables and receivables by month (GBP), same figures the fx system reports as exposure.
FX_MONTHS = [date(2026, 11, 1), date(2026, 12, 1), date(2027, 1, 1), date(2027, 2, 1), date(2027, 3, 1),
             date(2027, 4, 1), date(2027, 5, 1), date(2027, 6, 1), date(2027, 7, 1), date(2027, 8, 1),
             date(2027, 9, 1), date(2027, 10, 1)]
USD_OUT = [12272000, 11648000, 13000000, 14352000, 15808000, 18200000, 14664000, 12688000, 11960000, 11336000, 11856000, 12480000]
USD_IN = [472000, 448000, 500000, 552000, 608000, 700000, 564000, 488000, 460000, 436000, 456000, 480000]
EUR_OUT = [2835000, 2700000, 3240000, 3510000, 3780000, 4050000, 3510000, 3105000, 2835000, 2700000, 2970000, 3105000]
EUR_IN = [735000, 700000, 840000, 910000, 980000, 1050000, 910000, 805000, 735000, 700000, 770000, 805000]
FX_DRIVER = {
    "USD": "Dollar-priced purchases from Asian suppliers; seasonal buying peaks in spring for autumn/winter range",
    "EUR": "Euro-priced purchases from EU suppliers net of euro store receipts (LE-IE, LE-NL, LE-DE)",
}
FX_RATE = {"USD": 1.27, "EUR": 1.18}


def _weekly(g, scenario):
    """Return the 78 weekly rows (dicts, money in GBP) for one scenario."""
    _, shortfall, saving = SCENARIOS[scenario]
    rows, cash, debt = [], START_CASH, GROSS_DEBT_0
    rng = g.rng if scenario == "base" else None
    jitter_cache = _weekly.cache
    for w in range(1, 79):
        d = g.as_of + timedelta(weeks=w)
        if w <= 13:
            inflow, outflow = IN_13[w - 1] * 1e6, OUT_13[w - 1] * 1e6
            capex = 1.5e6 if w == 6 else 0.0
            drv = DRIVERS_13.get(w, "")
        else:
            if scenario == "base":
                jitter_cache[w] = (rng.uniform(-0.25, 0.25) * 1e6, rng.uniform(-0.25, 0.25) * 1e6)
            ji, jo = jitter_cache[w]
            inflow = 8.95e6 * SEAS_IN[d.month] + ji
            outflow = 8.4e6 * SEAS_OUT[d.month] + jo
            capex = 1.5e6 if w in CAPEX_WEEKS else 0.0
            drv = ""
            if w in VAT_WEEKS:
                outflow += 3.1e6
                drv = "Quarterly VAT payment of 3.1m"
        # scenario shaping: receipts shortfall builds over 13 weeks, cost response starts after week 4
        inflow *= 1 - shortfall * min(1.0, w / 13)
        outflow *= 1 - saving * min(1.0, max(0, w - 4) / 13)
        div = DIVIDEND_WEEKS.get(w, 0.0)
        repay = DEBT_WEEKS.get(w, 0.0)
        if div and not drv:
            drv = "Dividend payment"
        if repay and not drv:
            drv = "Term loan quarterly repayment of 2.0m"
        if not drv:
            drv = "Normal trading"
        opening = cash
        closing = opening + inflow - outflow - capex - div - repay
        debt -= repay
        rows.append({
            "week_no": w, "forecast_date": d, "opening": opening, "inflow": inflow, "outflow": outflow,
            "capex": capex, "div": div, "repay": repay, "closing": closing, "debt": debt, "driver": drv,
        })
        cash = closing
    return rows


_weekly.cache = {}


def generate(g):
    _weekly.cache = {}
    cash_forecasts, weekly = [], {}
    for scenario in ("base", "downside", "upside"):
        fid = SCENARIOS[scenario][0]
        weekly[scenario] = _weekly(g, scenario)
        for r in weekly[scenario]:
            cash_forecasts.append({
                "forecast_id": fid, "scenario": scenario, "week_no": r["week_no"],
                "forecast_date": r["forecast_date"], "entity_id": "LE-UK", "currency": "GBP",
                "opening_balance_gbp": round(r["opening"], 2),
                "operating_inflows_gbp": round(r["inflow"], 2),
                "operating_outflows_gbp": round(r["outflow"], 2),
                "capex_gbp": round(r["capex"], 2), "dividend_payment_gbp": round(r["div"], 2),
                "debt_repayment_gbp": round(r["repay"], 2), "closing_balance_gbp": round(r["closing"], 2),
                "gross_debt_gbp": round(r["debt"], 2), "key_drivers": r["driver"],
                "created_at": g.as_of,
            })

    # Covenant projections at each quarter-end test date, per scenario.
    projections = []
    facs = {"FAC-900001": ("Net debt / EBITDA", "maximum", 3.0),
            "FAC-900002": ("EBITDA / net finance costs", "minimum", 2.5),
            "FAC-900003": ("Minimum cash balance (GBP m)", "minimum", 10.0)}
    for scenario, rows in weekly.items():
        prev = g.as_of
        for qi, td in enumerate(TEST_DATES):
            in_q = [r for r in rows if prev < r["forecast_date"] <= td + timedelta(days=6)]
            at_test = [r for r in rows if r["forecast_date"] <= td][-1]
            ebitda = EBITDA_PATH[scenario][qi] * 1e6
            net_debt = at_test["debt"] - at_test["closing"]
            min_cash = min(r["closing"] for r in in_q)
            vals = {
                "FAC-900001": (round(net_debt / ebitda, 2),
                               f"Net debt {net_debt / 1e6:.1f}m / LTM EBITDA {ebitda / 1e6:.1f}m"),
                "FAC-900002": (round(ebitda / NET_FINANCE_COST, 2),
                               f"LTM EBITDA {ebitda / 1e6:.1f}m / net finance costs {NET_FINANCE_COST / 1e6:.1f}m"),
                "FAC-900003": (round(min_cash / 1e6, 2), f"Lowest weekly cash balance in the quarter {min_cash / 1e6:.1f}m"),
            }
            for fac, (metric, ctype, limit) in facs.items():
                v, why = vals[fac]
                projections.append({
                    "facility_id": fac, "scenario": scenario, "test_date": td, "metric": metric,
                    "covenant_type": ctype, "covenant_limit": limit, "projected_value": v, "basis": why,
                })
            prev = td

    # Debt facilities (current position; covenants last tested at the end of September).
    lev = round((GROSS_DEBT_0 - START_CASH) / EBITDA_NOW, 2)
    icr = round(EBITDA_NOW / NET_FINANCE_COST, 2)
    cash_now = 21_600_000.0      # lowest weekly cash in the quarter just tested
    def facility(i, typ, lender, total, drawn, rate, start, mat, cov, actual, limit, kind):
        if kind == "maximum":
            head = round(100 * (limit - actual) / limit, 1)
        else:
            head = round(100 * (actual - limit) / actual, 1)
        return {
            "facility_id": f"FAC-90000{i}", "entity_id": "LE-UK", "facility_type": typ, "lender": lender,
            "currency": "GBP", "total_facility_gbp": total, "drawn_amount_gbp": drawn,
            "undrawn_amount_gbp": total - drawn, "start_date": start, "maturity_date": mat,
            "interest_rate_pct": rate, "financial_covenant": cov, "covenant_actual": actual,
            "covenant_limit": limit, "covenant_test_date": date(2026, 9, 30), "covenant_status": "compliant",
            "covenant_headroom_pct": head,
        }
    debt_facilities = [
        facility(1, "term_loan", "Barclays", 60e6, 60e6, 5.9, date(2023, 10, 5), date(2029, 10, 5),
                 "Leverage: net debt / EBITDA below 3.0x", lev, 3.0, "maximum"),
        facility(2, "revolving_credit", "HSBC", 50e6, 15e6, 5.6, date(2024, 3, 15), date(2029, 3, 15),
                 "Interest cover: EBITDA / net finance costs above 2.5x", icr, 2.5, "minimum"),
        facility(3, "bond", "Private placement noteholders", 50e6, 50e6, 3.8, date(2019, 6, 1), date(2032, 6, 1),
                 "Minimum cash balance above 10.0m (GBP m)", round(cash_now / 1e6, 2), 10.0, "minimum"),
    ]

    # Forecast cash flows by currency (non-sterling exposure), monthly for 12 months.
    fx_cash_flows = []
    for cur, outs, ins in (("USD", USD_OUT, USD_IN), ("EUR", EUR_OUT, EUR_IN)):
        for m, o, i in zip(FX_MONTHS, outs, ins):
            fx_cash_flows.append({
                "flow_month": m, "currency": cur, "inflows_gbp": float(i), "outflows_gbp": float(o),
                "base_rate": FX_RATE[cur], "driver": FX_DRIVER[cur],
            })

    # Hedge pricing sheet (matches the instrument quotes the fx system shows for GBP/USD and GBP/EUR).
    pricing = []
    fx_quotes = {
        "GBP/USD": {3: (1.2643, 0.06, 1.1, 0.12), 6: (1.2586, 0.09, 1.7, 0.2), 12: (1.2471, 0.14, 2.6, 0.32)},
        "GBP/EUR": {3: (1.1741, 0.06, 0.935, 0.12), 6: (1.1682, 0.09, 1.445, 0.2), 12: (1.1564, 0.14, 2.21, 0.32)},
    }
    spots = {"GBP/USD": 1.27, "GBP/EUR": 1.18}
    for pair, tenors in fx_quotes.items():
        for ten, (fwd, c_f, c_o, c_c) in tenors.items():
            for inst, cost, locked, band in (("forward", c_f, fwd, None), ("option", c_o, spots[pair], None),
                                             ("collar", c_c, fwd, 5.0)):
                pricing.append({
                    "pricing_id": f"PRC-{len(pricing) + 1:04d}", "underlying_type": "fx_forward",
                    "currency_pair": pair, "commodity": None, "instrument_type": inst, "tenor_months": ten,
                    "spot_rate_or_price": spots[pair], "locked_rate_or_price": locked, "cost_pct": cost,
                    "band_pct": band,
                })
    cotton = {3: (1.98, 1.0, 3.2, 0.4), 6: (2.0, 2.0, 5.1, 0.6), 12: (2.02, 3.1, 7.6, 1.1)}
    for ten, (fwd, c_f, c_o, c_c) in cotton.items():
        for inst, cost, locked, band in (("forward", c_f, fwd, None), ("option", c_o, 1.96, None),
                                         ("collar", c_c, fwd, 5.0)):
            pricing.append({
                "pricing_id": f"PRC-{len(pricing) + 1:04d}", "underlying_type": "commodity",
                "currency_pair": None, "commodity": "cotton", "instrument_type": inst, "tenor_months": ten,
                "spot_rate_or_price": 1.96, "locked_rate_or_price": locked, "cost_pct": cost, "band_pct": band,
            })

    return {
        "cash_forecasts": cash_forecasts,
        "covenant_projections": projections,
        "debt_facilities": debt_facilities,
        "fx_cash_flows": fx_cash_flows,
        "hedge_pricing": pricing,
        "bank_accounts": [],
        "dividends": [],
        "hedging_requests": [],
        "hedging_outcomes": [],
        "covenant_alerts": [],
    }
