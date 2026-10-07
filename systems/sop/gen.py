def generate(g):
    """S&OP platform: older-cycle plan baselines only; the current-cycle story rows live in seed/*.csv."""
    baselines = []
    history = [
        ("SOP-202608", "Q3 2026", 62100000, 33.5, 12400000, 94.0, 2650000, 17.5),
        ("SOP-202609", "Q3 2026", 62800000, 33.0, 12300000, 93.8, 2720000, 18.0),
    ]
    for i, (cycle, period, rev, margin, cash, sl, inv, promo) in enumerate(history, start=1):
        baselines.append({
            "baseline_id": f"SOP-B-{i:06d}",
            "sop_cycle": cycle,
            "forecast_period": period,
            "revenue_gbp": rev,
            "margin_pct": margin,
            "cash_flow_gbp": cash,
            "service_level_pct": sl,
            "inventory_units": inv,
            "promotional_intensity_pct": promo,
            "demand_assumption": "Demand +2% YoY; normal seasonality",
            "supply_assumption": "Asia inbound lead times 28 days; suppliers on track",
            "created_at": g.days_ago(70 - 28 * (i - 1)),
        })
    return {
        "sop_scenarios": [],
        "sop_scenario_assumptions": [],
        "assumption_changes": [],
        "scenario_runs": [],
        "plan_baseline": baselines,
        "new_product_launches": [],
        "external_assumptions": [],
        "disputed_assumptions": [],
    }
