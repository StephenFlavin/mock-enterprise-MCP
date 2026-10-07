"""FX rates, hedges and exposure forecasts. Generate rates for GBP/USD, GBP/EUR and GBP/INR."""
from datetime import datetime, time, timedelta, date


def generate(g):
    r = g.rng
    fake = g.fake

    # Currency pairs and base rates
    currency_pairs = {
        "GBP/USD": 1.27,
        "GBP/EUR": 1.18,
        "GBP/INR": 104.5,
    }

    # Generate FX rate history (last 90 days + next 30 days)
    fx_rates = []
    for pair, base_rate in currency_pairs.items():
        for i in range(-90, 31):
            rate_date = g.as_of + timedelta(days=i)
            # Random walk with slight trend
            daily_move = r.gauss(0, 0.005)  # 0.5% volatility
            spot = base_rate + (base_rate * daily_move)
            bid = spot - 0.002
            ask = spot + 0.002
            volatility = abs(r.gauss(8, 2))  # 8% volatility
            fx_rates.append({
                "currency_pair": pair,
                "rate_date": rate_date,
                "spot_rate": round(spot, 4),
                "bid_rate": round(bid, 4),
                "ask_rate": round(ask, 4),
                "volatility_pct": round(volatility, 2),
            })

    # Generate forward rates (12 months forward)
    fx_forward_rates = []
    for pair, base_rate in currency_pairs.items():
        current_spot = base_rate
        for months in range(1, 13):
            forward_date = g.as_of + timedelta(days=months * 30)
            # Forward curve with term structure
            forward_rate = current_spot * (1 + 0.02 * months / 12)  # 2% annual premium/discount
            points = (forward_rate - current_spot) * 10000
            bid = forward_rate - 0.003
            ask = forward_rate + 0.003
            fx_forward_rates.append({
                "currency_pair": pair,
                "forward_date": forward_date,
                "forward_rate": round(forward_rate, 4),
                "points": round(points, 0),
                "bid_rate": round(bid, 4),
                "ask_rate": round(ask, 4),
            })

    # Generate open hedge positions
    hedge_positions = []
    hedge_data = [
        ("GBP/USD", 5000000, 75, "forward", 1.27, None, g.as_of + timedelta(days=90)),
        ("GBP/USD", 3000000, 50, "option", 1.28, 1.27, g.as_of + timedelta(days=60)),
        ("GBP/EUR", 2000000, 80, "forward", 1.18, None, g.as_of + timedelta(days=120)),
        ("GBP/INR", 1500000, 60, "collar", 104.5, 103.5, g.as_of + timedelta(days=90)),
    ]
    for i, (pair, exposure, ratio, instr, rate, strike, mat) in enumerate(hedge_data):
        eff = r.randint(75, 98)
        mt = round(exposure * ratio / 100.0, 2)
        notional = round(exposure * ratio / 100.0, 2)
        mark_to_market = round(notional * r.gauss(0.01, 0.02), 2)
        hedge_positions.append({
            "hedge_id": f"HDG-900{i+1:03d}",
            "currency_pair": pair,
            "exposure_amount": exposure,
            "hedge_amount": mt,
            "instrument_type": instr,
            "hedge_rate": rate,
            "strike_price": strike,
            "maturity_date": mat,
            "effectiveness_pct": eff,
            "status": "open",
            "notional_gbp": notional,
            "mark_to_market_gbp": mark_to_market,
            "created_at": g.as_of - timedelta(days=30),
            "matured_at": None,
        })

    # Generate currency exposure by month
    currency_exposure = []
    currencies = ["USD", "EUR", "INR"]
    for currency in currencies:
        for month in range(0, 13):
            # Calculate month by adding months properly
            year = g.as_of.year
            m = g.as_of.month + month
            if m > 12:
                year += m // 12
                m = m % 12
                if m == 0:
                    m = 12
                    year -= 1
            exposure_month = date(year, m, 1)

            # Base exposure varies by currency
            base_exposure = {"USD": 8000000, "EUR": 3000000, "INR": 2000000}[currency]
            payable = round(base_exposure * r.gauss(1.0, 0.1), 2)
            receivable = round(base_exposure * r.gauss(0.3, 0.05), 2)
            net = payable - receivable

            # Hedge coverage increases with time (prudent policy)
            hedge_pct = min(60 + month * 3, 95)

            pair = f"GBP/{currency}"
            base_rate = currency_pairs.get(pair, 1.0)

            currency_exposure.append({
                "currency": currency,
                "exposure_month": exposure_month,
                "payable_exposure_gbp": round(payable, 2),
                "receivable_exposure_gbp": round(receivable, 2),
                "net_exposure_gbp": round(net, 2),
                "hedge_coverage_pct": hedge_pct,
                "base_rate": base_rate,
                "forecast_status": "confirmed" if month < 3 else "forecast",
            })

    # Generate hedge instruments available for quoting
    hedge_instruments = []
    instr_id = 1
    for pair in currency_pairs.keys():
        for maturity in [1, 3, 6, 12]:
            for instr_type in ["forward", "option", "collar", "swap"]:
                price = currency_pairs[pair]
                cost = round(abs(r.gauss(0, 5000)), 2)  # Cost varies by instrument
                protection = r.randint(70, 100)
                hedge_instruments.append({
                    "instrument_id": f"INSTR-{instr_id:03d}",
                    "instrument_type": instr_type,
                    "currency_pair": pair,
                    "maturity_months": maturity,
                    "market_price": round(price, 4),
                    "bid_price": round(price - 0.003, 4),
                    "ask_price": round(price + 0.003, 4),
                    "cost_gbp": cost,
                    "protection_level_pct": protection,
                    "last_quoted_at": g.as_of,
                })
                instr_id += 1

    return {
        "fx_rates": fx_rates,
        "fx_forward_rates": fx_forward_rates,
        "hedge_positions": hedge_positions,
        "currency_exposure": currency_exposure,
        "hedge_instruments": hedge_instruments,
        "hedge_approval_queue": [],
    }
