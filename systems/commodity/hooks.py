"""Python hooks for the commodity system."""


def calc_fixed_vs_floating(ctx, commodity_id, volume_units=1000000.0, period_months=12, current_price_gbp=None,
                           fixed_price_gbp=None):
    cid = commodity_id.upper()
    period_months = max(1, min(int(period_months or 12), 12))
    last = ctx.q("SELECT price_gbp_unit, unit_name FROM commodity_prices WHERE commodity_id = $c "
                 "ORDER BY price_date DESC LIMIT 1", c=cid)
    if not last:
        return f"No price data for commodity {cid}."
    unit = last[0]["unit_name"]
    cur = float(current_price_gbp) if current_price_gbp else float(last[0]["price_gbp_unit"])
    fixed = float(fixed_price_gbp) if fixed_price_gbp else cur
    fc = ctx.q("SELECT horizon_months AS h, forecast_price_gbp AS p FROM commodity_forecasts WHERE commodity_id = $c "
               "QUALIFY row_number() OVER (PARTITION BY horizon_months ORDER BY forecast_date DESC) = 1 "
               "ORDER BY horizon_months", c=cid)
    pts = [(0.0, cur)] + [(float(f["h"]), float(f["p"])) for f in fc]
    if len(pts) < 2:
        return f"No forecasts for commodity {cid}; cannot build a floating path."

    def at(m):  # forecast path value at month m, linear between published horizons (flat after the last)
        for (m0, p0), (m1, p1) in zip(pts, pts[1:]):
            if m0 <= m <= m1:
                return p0 + (p1 - p0) * (m - m0) / (m1 - m0)
        return pts[-1][1]

    knots = sorted({m for m, _ in pts if m < period_months} | {float(period_months)})
    area = sum((b - a) * (at(a) + at(b)) / 2 for a, b in zip(knots, knots[1:]))
    path_avg = area / period_months
    end_price = at(float(period_months))
    vol = float(volume_units)
    fixed_cost = fixed * vol
    rows = []
    for name, px, note in (
            ("Fixed price", fixed, "Locked for the whole period"),
            ("Floating, price stays at today's level", cur, "Market price unchanged"),
            ("Floating, analyst forecast path (average)", path_avg, "Average of the forecast path over the period"),
            ("Floating, forecast price at end of period", end_price, "Downside if the market sits at the end-of-period forecast")):
        cost = px * vol
        rows.append({"scenario": name, "commodity_id": cid, "unit": unit, "price_gbp": round(px, 5),
                     "volume_units": vol, "period_months": period_months, "total_cost_gbp": round(cost, 2),
                     "extra_cost_vs_fixed_gbp": round(cost - fixed_cost, 2), "notes": note,
                     "formula": "cost = price x volume; extra vs fixed = floating cost - fixed cost (positive means fixing saves money)"})
    return rows
