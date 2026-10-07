"""FX rates, forwards, hedge book, 12-month exposure and instrument pricing for treasury.

Currencies follow master data: supplier/PO currencies are USD and EUR (plus GBP), the Polish entity LE-PL trades in
PLN. TRY and MAD are only reference rates (Turkey / Morocco sourcing risk). Hedge cover in currency_exposure is derived
from the hedge book so the two tools always agree.
"""
from datetime import datetime, timedelta, date

# (days relative to as_of, rate) anchors; rates are linearly interpolated between them. Plateaus keep period-start
# values stable whatever weekday "today" is.
ANCHORS = {
    "GBP/USD": [(-400, 1.345), (-330, 1.345), (-300, 1.335), (-235, 1.335), (-160, 1.310), (-100, 1.285), (-65, 1.275), (0, 1.270)],
    "GBP/EUR": [(-400, 1.165), (-200, 1.170), (0, 1.180)],
    "GBP/PLN": [(-400, 4.95), (-80, 5.00), (-54, 5.00), (-5, 5.13), (0, 5.14)],
    "GBP/TRY": [(-400, 44.0), (-215, 50.0), (-170, 50.0), (0, 57.5)],
    "GBP/MAD": [(-400, 12.40), (-215, 12.50), (-170, 12.50), (0, 12.63)],
}
VOL = {"GBP/USD": 7.5, "GBP/EUR": 6.0, "GBP/PLN": 8.0, "GBP/TRY": 22.0, "GBP/MAD": 4.5}
DP = {"GBP/TRY": 3, "GBP/MAD": 4, "GBP/PLN": 4}
FWD_ANNUAL = {"GBP/USD": -0.018, "GBP/EUR": -0.020}   # forward discount per year (UK rates above USD/EUR rates)

# Next 12 months from the coming month: net exposure GBP m and target hedge cover % (USD month 6 is the planted gap)
USD_NET = [11.8, 11.2, 12.5, 13.8, 15.2, 17.5, 14.1, 12.2, 11.5, 10.9, 11.4, 12.0]
USD_COV = [85, 83, 80, 76, 70, 50, 55, 60, 56, 52, 46, 48]
EUR_NET = [2.1, 2.0, 2.4, 2.6, 2.8, 3.0, 2.6, 2.3, 2.1, 2.0, 2.2, 2.3]
EUR_COV = [84, 82, 80, 78, 74, 70, 66, 62, 58, 54, 50, 46]

COST_PCT = {  # premium / cost as % of notional by maturity months (1, 3, 6, 12)
    "forward": [0.04, 0.06, 0.09, 0.14],
    "option": [0.45, 1.10, 1.70, 2.60],
    "collar": [0.05, 0.12, 0.20, 0.32],
    "swap": [0.08, 0.10, 0.15, 0.22],
}
PROTECT = {"forward": 100, "option": 100, "collar": 85, "swap": 100}
TERMS = {
    "forward": "Locks the rate for the whole amount; no benefit if sterling strengthens.",
    "option": "Floor rate with premium; keeps the benefit if sterling strengthens.",
    "collar": "Rate protected inside a band (about 5%); gives up gains beyond the band, low or zero premium.",
    "swap": "Spot purchase reversed at maturity; locks the forward points, no benefit if sterling strengthens.",
}


def _month_start(d, k):
    m = d.month - 1 + k
    return date(d.year + m // 12, m % 12 + 1, 1)


def generate(g):
    r = g.rng
    a = g.as_of

    # ---- spot history (weekdays) ----
    def anchor_rate(pair, n):
        pts = ANCHORS[pair]
        for (d0, v0), (d1, v1) in zip(pts, pts[1:]):
            if d0 <= n <= d1:
                return v0 + (v1 - v0) * (n - d0) / (d1 - d0)
        return pts[-1][1]

    fx_rates, spot_on = [], {}
    for pair in ANCHORS:
        dp = DP.get(pair, 4)
        for n in range(-400, 1):
            d = a + timedelta(days=n)
            if d.weekday() >= 5:
                continue
            base = anchor_rate(pair, n)
            noise = 0 if n == 0 else r.gauss(0, 0.0012) * base
            spot = round(base + noise, dp)
            half = round(base * 0.0002, dp + 1)
            spot_on[(pair, d)] = spot
            fx_rates.append({"currency_pair": pair, "rate_date": d, "spot_rate": spot,
                             "bid_rate": round(spot - half, dp + 1), "ask_rate": round(spot + half, dp + 1),
                             "volatility_pct": round(abs(r.gauss(VOL[pair], VOL[pair] * 0.08)), 2)})

    def spot_at(pair, d):
        while (pair, d) not in spot_on:
            d -= timedelta(days=1)
        return spot_on[(pair, d)]

    def fwd(pair, months):
        return spot_on[(pair, a)] * (1 + FWD_ANNUAL[pair] * months / 12.0)

    # ---- forward curve ----
    fx_forward_rates = []
    for pair in FWD_ANNUAL:
        spot = spot_on[(pair, a)]
        for m in range(1, 13):
            f = fwd(pair, m)
            fx_forward_rates.append({"currency_pair": pair, "forward_date": a + timedelta(days=m * 30),
                                     "forward_rate": round(f, 4), "points": round((f - spot) * 10000, 0),
                                     "bid_rate": round(f - 0.003, 4), "ask_rate": round(f + 0.003, 4)})

    # ---- exposure and the hedge book that covers it ----
    book = [("USD", "GBP/USD", USD_NET, USD_COV), ("EUR", "GBP/EUR", EUR_NET, EUR_COV)]
    hedge_positions, currency_exposure = [], []
    hid = 1
    for cur, pair, nets, covs in book:
        for k in range(12):
            month = _month_start(a, k + 1)
            net = round(nets[k] * 1e6, 2)
            recv = round(net * (0.04 if cur == "USD" else 0.35), 2)
            pay = round(net + recv, 2)
            hedged_total = round(net * covs[k] / 100.0 / 50000) * 50000
            tranches = [("forward", hedged_total)]
            if cur == "USD" and k >= 4:
                opt = round(hedged_total * 0.3 / 50000) * 50000
                tranches = [("forward", hedged_total - opt), ("option", opt)]
            for instr, notional in tranches:
                if notional <= 0:
                    continue
                created = a - timedelta(days=8 + (hid * 11) % 75)
                tenor = (month + timedelta(days=14) - created).days / 365.0
                rate = round(spot_at(pair, created) * (1 + FWD_ANNUAL[pair] * tenor), 4)
                cur_fwd = fwd(pair, max(1, k + 1))
                mtm = round(notional * (rate / cur_fwd - 1), 2)
                hedge_positions.append({
                    "hedge_id": f"HDG-9{hid:03d}", "currency_pair": pair, "exposure_amount": net,
                    "hedge_amount": round(notional * rate, 2), "instrument_type": instr, "hedge_rate": rate,
                    "strike_price": round(rate - 0.01, 4) if instr == "option" else None,
                    "maturity_date": month + timedelta(days=14), "effectiveness_pct": 80 + (hid * 7) % 19,
                    "status": "open", "notional_gbp": float(notional), "mark_to_market_gbp": mtm,
                    "created_at": created, "matured_at": None})
                hid += 1
            hedged = sum(n for _, n in tranches)
            currency_exposure.append({
                "currency": cur, "exposure_month": month, "payable_exposure_gbp": pay,
                "receivable_exposure_gbp": recv, "net_exposure_gbp": net,
                "hedge_coverage_pct": round(hedged / net * 100.0, 1), "base_rate": spot_on[(pair, a)],
                "forecast_status": "confirmed" if k < 3 else "forecast"})

    # settled hedges from the last quarter (for effectiveness reporting)
    for i, (pair, notional, instr) in enumerate([("GBP/USD", 9000000, "forward"), ("GBP/USD", 6000000, "forward"),
                                                  ("GBP/EUR", 2000000, "forward"), ("GBP/USD", 3000000, "option")]):
        created = a - timedelta(days=85 - i * 4)
        mat = a - timedelta(days=22 - i * 5)
        rate = round(spot_at(pair, created) * (1 + FWD_ANNUAL[pair] * 0.25), 4)
        settle = spot_at(pair, mat)
        hedge_positions.append({
            "hedge_id": f"HDG-9{900 + i:03d}", "currency_pair": pair, "exposure_amount": float(notional) * 1.1,
            "hedge_amount": round(notional * rate, 2), "instrument_type": instr, "hedge_rate": rate,
            "strike_price": round(rate - 0.01, 4) if instr == "option" else None, "maturity_date": mat,
            "effectiveness_pct": 86 + i * 2, "status": "matured", "notional_gbp": float(notional),
            "mark_to_market_gbp": round(notional * (rate / settle - 1), 2), "created_at": created,
            "matured_at": datetime.combine(mat, datetime.min.time())})

    # ---- instruments ----
    hedge_instruments, iid = [], 1
    for pair in FWD_ANNUAL:
        scale = 1.0 if pair == "GBP/USD" else 0.85
        for mi, months in enumerate([1, 3, 6, 12]):
            price = round(fwd(pair, months), 4)
            for instr in COST_PCT:
                pct = round(COST_PCT[instr][mi] * (scale if instr == "option" else 1.0), 3)
                hedge_instruments.append({
                    "instrument_id": f"INSTR-{iid:03d}", "instrument_type": instr, "currency_pair": pair,
                    "maturity_months": months, "market_price": price,
                    "bid_price": round(price - 0.003, 4), "ask_price": round(price + 0.003, 4),
                    "cost_pct": pct, "cost_gbp": round(pct * 10000, 2), "protection_level_pct": PROTECT[instr],
                    "terms": TERMS[instr], "last_quoted_at": datetime.combine(a, datetime.min.time()).replace(hour=9, minute=30)})
                iid += 1

    return {"fx_rates": fx_rates, "fx_forward_rates": fx_forward_rates, "hedge_positions": hedge_positions,
            "currency_exposure": currency_exposure, "hedge_instruments": hedge_instruments,
            "hedge_approval_queue": []}
