"""Treasury management system: cash forecasts, debt facilities, covenants and hedging."""
from datetime import datetime, timedelta
import math


def generate(g):
    r = g.rng
    entities = g.master("legal_entities")

    # Generate cash forecasts for next 26 weeks (13-week rolling + 13-week look-ahead)
    cash_forecasts = []
    for week_offset in range(1, 27):
        forecast_date = g.as_of + timedelta(weeks=week_offset)
        # Base balance grows slightly over time with seasonal patterns
        opening = 25000000 + (week_offset * 50000) + r.randint(-2000000, 2000000)
        # Operating inflows (weekly sales receipts, typically GBP-based)
        inflows = 8000000 + r.randint(-1000000, 1500000)
        # Operating outflows (payables, weekly opex)
        outflows = 7000000 + r.randint(-800000, 1200000)
        # Capex every 4-8 weeks
        capex = 1500000 if (week_offset % 6 == 0) else 0
        # Dividends every 26 weeks
        dividend = 5000000 if (week_offset == 13) else 0
        # Debt repayment quarterly
        repayment = 2000000 if (week_offset % 13 == 0) else 0

        closing = opening + inflows - outflows - capex - dividend - repayment

        cash_forecasts.append({
            "forecast_id": f"FOR-{len(cash_forecasts) + 1:06d}",
            "forecast_date": forecast_date,
            "week_no": week_offset,
            "currency": "GBP",
            "opening_balance_gbp": round(opening, 2),
            "operating_inflows_gbp": round(inflows, 2),
            "operating_outflows_gbp": round(outflows, 2),
            "capex_gbp": round(capex, 2),
            "dividend_payment_gbp": round(dividend, 2),
            "debt_repayment_gbp": round(repayment, 2),
            "closing_balance_gbp": round(closing, 2),
            "created_at": g.as_of
        })

    # Generate bank accounts across entities
    bank_accounts = []
    banks = ["Barclays", "HSBC", "NatWest", "Santander", "Deutsche Bank"]
    for i, entity in enumerate(entities[:3]):  # LE-UK, LE-EU, LE-US
        for j in range(2):  # 2 accounts per entity
            account_type = "operating" if j == 0 else "investment"
            facility_limit = 50000000 if account_type == "operating" else 30000000
            available = facility_limit * r.uniform(0.4, 0.8)

            bank_accounts.append({
                "account_id": f"ACC-{len(bank_accounts) + 1:06d}",
                "entity_id": entity["entity_id"],
                "account_type": account_type,
                "currency": entity["currency"],
                "available_balance_gbp": round(available, 2),
                "held_balance_gbp": round(facility_limit * 0.1, 2),
                "facility_limit_gbp": round(facility_limit, 2),
                "bank_name": r.choice(banks),
                "last_updated": g.as_of
            })

    # Generate debt facilities with covenants
    debt_facilities = []
    facility_types = ["term_loan", "revolving_credit", "bond"]
    facilities_data = [
        {"type": "term_loan", "total": 100000000, "drawn": 75000000, "rate": 4.5, "months": 36},
        {"type": "revolving_credit", "total": 50000000, "drawn": 25000000, "rate": 5.0, "months": 60},
        {"type": "bond", "total": 150000000, "drawn": 150000000, "rate": 3.8, "months": 120},
    ]

    for i, fac_data in enumerate(facilities_data):
        start = g.as_of - timedelta(days=365)
        maturity = g.as_of + timedelta(days=fac_data["months"] * 30)
        # Covenant headroom: distance from breach (higher is better)
        headroom = r.uniform(20, 50)

        debt_facilities.append({
            "facility_id": f"FAC-{len(debt_facilities) + 1:06d}",
            "entity_id": "LE-UK",
            "facility_type": fac_data["type"],
            "lender": r.choice(["Barclays", "HSBC", "Bank of America", "Citigroup"]),
            "currency": "GBP",
            "total_facility_gbp": round(fac_data["total"], 2),
            "drawn_amount_gbp": round(fac_data["drawn"], 2),
            "undrawn_amount_gbp": round(fac_data["total"] - fac_data["drawn"], 2),
            "start_date": start,
            "maturity_date": maturity,
            "interest_rate_pct": fac_data["rate"],
            "financial_covenant": "Leverage ratio < 3.0x" if i == 0 else ("Interest coverage > 2.0x" if i == 1 else "Min cash > £15m"),
            "covenant_test_date": g.as_of - timedelta(days=30),
            "covenant_status": "compliant",
            "covenant_headroom_pct": round(headroom, 1)
        })

    # Generate dividend policy and schedule
    dividends = []
    div_schedule = [
        {"type": "interim", "months": 6, "payout": 30},
        {"type": "final", "months": 12, "payout": 50},
    ]

    for div_type_data in div_schedule:
        payment_date = g.as_of + timedelta(days=div_type_data["months"] * 30)
        amount = 50000000 * (div_type_data["payout"] / 100)

        dividends.append({
            "dividend_id": f"DIV-{len(dividends) + 1:06d}",
            "entity_id": "LE-UK",
            "policy_type": div_type_data["type"],
            "payment_date": payment_date,
            "amount_gbp": round(amount, 2),
            "status": "planned" if payment_date > g.as_of else "paid",
            "payout_ratio_pct": div_type_data["payout"],
            "notes": "Subject to covenant compliance and Board approval"
        })

    # Generate hedging outcomes (past decisions)
    hedging_outcomes = []
    outcomes_data = [
        {"type": "fx_forward", "pair": "GBP/USD", "notional": 5000000, "entry": 1.27, "exit": 1.29},
        {"type": "fx_forward", "pair": "GBP/EUR", "notional": 3000000, "entry": 1.18, "exit": 1.17},
        {"type": "commodity", "commodity": "cotton", "notional": 1000000, "entry": 0.75, "exit": 0.78},
        {"type": "interest_rate", "pair": None, "notional": 50000000, "entry": 5.2, "exit": 5.0},
    ]

    for i, out_data in enumerate(outcomes_data):
        decision_date = g.as_of - timedelta(days=r.randint(60, 300))
        settlement = decision_date + timedelta(days=r.randint(30, 180))

        # Calculate realistic P&L
        if out_data["type"] == "fx_forward":
            gain_loss = (out_data["exit"] - out_data["entry"]) * out_data["notional"]
        elif out_data["type"] == "commodity":
            gain_loss = (out_data["exit"] - out_data["entry"]) * out_data["notional"] * 1000
        else:  # interest_rate
            gain_loss = (out_data["exit"] - out_data["entry"]) * out_data["notional"] * 0.1

        strategy_comment = "Forward better than spot" if gain_loss > 0 else "Spot better than forward"

        hedging_outcomes.append({
            "outcome_id": f"HOU-{len(hedging_outcomes) + 1:06d}",
            "hedge_request_id": None,
            "decision_date": decision_date,
            "underlying_type": out_data["type"],
            "currency_pair": out_data.get("pair"),
            "commodity": out_data.get("commodity"),
            "notional_amount": out_data["notional"],
            "hedge_ratio_pct": 60 + r.randint(-10, 10),
            "entry_rate_or_price": out_data["entry"],
            "exit_rate_or_price": out_data["exit"],
            "settlement_date": settlement,
            "realised_gain_loss_gbp": round(gain_loss, 2),
            "strategy_vs_spot": strategy_comment,
            "comments": f"Executed {out_data['type']} hedge for risk mitigation"
        })

    # Generate covenant alerts (mostly empty, but a few active)
    covenant_alerts = []
    if len(debt_facilities) > 0:
        # Create an alert on the first facility
        covenant_alerts.append({
            "alert_id": f"ALT-{len(covenant_alerts) + 1:06d}",
            "facility_id": debt_facilities[0]["facility_id"],
            "alert_type": "headroom_threshold",
            "threshold_pct": 15.0,
            "current_headroom_pct": debt_facilities[0]["covenant_headroom_pct"],
            "status": "active",
            "created_date": g.as_of - timedelta(days=30),
            "triggered_date": None,
            "actions_taken": None
        })

    # Hedging requests (mostly empty for background)
    hedging_requests = []

    return {
        "cash_forecasts": cash_forecasts,
        "bank_accounts": bank_accounts,
        "debt_facilities": debt_facilities,
        "dividends": dividends,
        "hedging_requests": hedging_requests,
        "hedging_outcomes": hedging_outcomes,
        "covenant_alerts": covenant_alerts
    }
