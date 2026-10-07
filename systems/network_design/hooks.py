"""Network design calculation hooks."""


def calc_network_total_cost(ctx, scenario_id, annual_volume_units):
    """Calculate total network cost for a scenario at given volume."""
    scenario = ctx.q(
        "SELECT annual_handling_cost_gbp, annual_transport_cost_gbp, annual_rent_gbp, annual_labour_cost_gbp, name "
        "FROM network_scenarios WHERE scenario_id = $sid",
        sid=scenario_id,
    )
    if not scenario:
        return {"error": f"Scenario {scenario_id} not found"}

    s = scenario[0]
    handling = s["annual_handling_cost_gbp"]
    transport = s["annual_transport_cost_gbp"]
    rent = s["annual_rent_gbp"]
    labour = s["annual_labour_cost_gbp"]

    # Scale transport and handling costs with volume (rent and labour are semi-fixed)
    base_volume = 5000000
    volume_factor = annual_volume_units / base_volume
    handling_scaled = handling * volume_factor
    transport_scaled = transport * volume_factor
    labour_scaled = labour * (0.6 + 0.4 * volume_factor)  # Semi-variable

    total = handling_scaled + transport_scaled + rent + labour_scaled
    cost_per_unit = total / annual_volume_units if annual_volume_units > 0 else 0

    return {
        "scenario_id": scenario_id,
        "scenario_name": s["name"],
        "annual_volume_units": annual_volume_units,
        "handling_cost_gbp": round(handling_scaled, 0),
        "transport_cost_gbp": round(transport_scaled, 0),
        "rent_fixed_gbp": rent,
        "labour_cost_gbp": round(labour_scaled, 0),
        "total_network_cost_gbp": round(total, 0),
        "cost_per_unit_gbp": round(cost_per_unit, 2),
        "formula": "handling (scaled) + transport (scaled) + rent (fixed) + labour (semi-fixed)",
    }


def calc_break_even_volume(ctx, baseline_scenario_id, alternative_scenario_id):
    """Calculate break-even volume where alternative scenario becomes cheaper."""
    baseline = ctx.q(
        "SELECT * FROM network_scenarios WHERE scenario_id = $sid",
        sid=baseline_scenario_id,
    )
    alternative = ctx.q(
        "SELECT * FROM network_scenarios WHERE scenario_id = $sid",
        sid=alternative_scenario_id,
    )

    if not baseline or not alternative:
        return {"error": "Scenario not found"}

    b = baseline[0]
    a = alternative[0]

    # Simple break-even: when total costs are equal
    # Baseline: b_fixed + b_var * v = Alternative: a_fixed + a_var * v
    # v = (a_fixed - b_fixed) / (b_var - a_var)

    b_fixed = b["annual_rent_gbp"] + 1000000  # base fixed overhead
    b_var = (b["annual_handling_cost_gbp"] + b["annual_transport_cost_gbp"]) / 5000000

    a_fixed = a["annual_rent_gbp"] + 1000000
    a_var = (a["annual_handling_cost_gbp"] + a["annual_transport_cost_gbp"]) / 5000000

    if b_var == a_var:
        return {"break_even_volume_units": 0, "note": "Same variable costs"}

    break_even = (a_fixed - b_fixed) / (b_var - a_var)
    break_even = max(0, break_even)

    return {
        "baseline_scenario": b["name"],
        "alternative_scenario": a["name"],
        "break_even_volume_units": int(break_even),
        "baseline_cheaper_below": break_even < 5000000,
        "formula": "(alt_fixed - base_fixed) / (base_var - alt_var)",
    }


def calc_service_impact(ctx, scenario_id, current_avg_days):
    """Calculate change in service level (delivery days)."""
    scenario = ctx.q(
        "SELECT avg_delivery_days_stores, avg_delivery_days_customers, name "
        "FROM network_scenarios WHERE scenario_id = $sid",
        sid=scenario_id,
    )
    if not scenario:
        return {"error": f"Scenario {scenario_id} not found"}

    s = scenario[0]
    store_impact = s["avg_delivery_days_stores"] - current_avg_days
    customer_impact = s["avg_delivery_days_customers"] - current_avg_days

    return {
        "scenario_id": scenario_id,
        "scenario_name": s["name"],
        "current_avg_delivery_days": current_avg_days,
        "new_avg_delivery_days_stores": round(s["avg_delivery_days_stores"], 1),
        "new_avg_delivery_days_customers": round(s["avg_delivery_days_customers"], 1),
        "impact_stores_days": round(store_impact, 1),
        "impact_customers_days": round(customer_impact, 1),
        "improvement": store_impact < 0,
        "formula": "new_delivery_time - current_delivery_time",
    }


def calc_redundancy_cost(ctx, scenario_id, target_redundancy_score):
    """Cost to add redundancy to reach target score."""
    scenario = ctx.q(
        "SELECT redundancy_score, annual_rent_gbp, annual_labour_cost_gbp "
        "FROM network_scenarios WHERE scenario_id = $sid",
        sid=scenario_id,
    )
    if not scenario:
        return {"error": f"Scenario {scenario_id} not found"}

    s = scenario[0]
    current_score = s["redundancy_score"]
    gap = target_redundancy_score - current_score

    if gap <= 0:
        redundancy_investment = 0
    else:
        # Cost to add redundancy: buffer inventory + extra capacity + dual sourcing
        buffer_inventory_cost = 500000 * (gap / 100)  # Scale with gap
        extra_capacity_cost = 800000 * (gap / 100)
        dual_source_cost = 300000 * (gap / 100)
        redundancy_investment = buffer_inventory_cost + extra_capacity_cost + dual_source_cost

    annual_cost = redundancy_investment * 0.15  # Assume 15% annual cost of capital

    return {
        "scenario_id": scenario_id,
        "current_redundancy_score": current_score,
        "target_redundancy_score": target_redundancy_score,
        "score_gap": gap,
        "one_time_investment_gbp": round(redundancy_investment, 0),
        "annual_cost_gbp": round(annual_cost, 0),
        "formula": "gap * (buffer_inventory_cost + extra_capacity_cost + dual_source_cost) * 15%",
    }


def calc_peak_capacity_risk(ctx, scenario_id, peak_volume_uplift_pct):
    """Assess peak capacity risk."""
    profiles = ctx.q(
        "SELECT site_id, peak_capacity_units_day, avg_daily_volume_units "
        "FROM dc_profiles WHERE scenario_id = $sid",
        sid=scenario_id,
    )
    if not profiles:
        return {"error": f"No profiles for scenario {scenario_id}"}

    total_peak_capacity = sum(p["peak_capacity_units_day"] for p in profiles)
    total_avg_volume = sum(p["avg_daily_volume_units"] for p in profiles)
    peak_volume = total_avg_volume * (1 + peak_volume_uplift_pct / 100)

    at_risk = peak_volume > total_peak_capacity
    spare = total_peak_capacity - peak_volume
    risk_score = 100 * max(0, peak_volume - total_peak_capacity) / total_peak_capacity

    return {
        "scenario_id": scenario_id,
        "current_peak_capacity_units_day": total_peak_capacity,
        "current_avg_volume_units_day": total_avg_volume,
        "assumed_peak_uplift_pct": peak_volume_uplift_pct,
        "peak_volume_units_day": int(peak_volume),
        "spare_capacity_units_day": int(spare),
        "at_risk": at_risk,
        "risk_score_0_100": round(risk_score, 1),
        "recommendation": "Invest in capacity" if risk_score > 20 else "Capacity adequate",
    }


def calc_outage_service_impact(ctx, down_site, outage_days):
    """Calculate service impact if a DC is offline."""
    # Get volume from down site
    down_volume = ctx.q(
        "SELECT SUM(avg_daily_volume_units) AS total FROM dc_profiles WHERE site_id = $site",
        site=down_site,
    )
    # Get total network volume
    network_volume = ctx.q("SELECT SUM(avg_daily_volume_units) AS total FROM dc_profiles")

    if not down_volume or not network_volume:
        return {"error": "Volume data not found"}

    down_pct = (down_volume[0].get("total") or 0) / (network_volume[0].get("total") or 1) * 100
    # Service impact: some % can be redirected, but there's latency and overflow
    service_impact = down_pct * 0.75  # 75% of lost volume impacts service

    return {
        "down_site": down_site,
        "outage_days": outage_days,
        "volume_at_risk_pct": round(down_pct, 1),
        "service_level_impact_pct": round(service_impact, 1),
        "orders_at_risk": int(service_impact * 50000 / 100),  # Assume 50k orders/day
        "estimated_lost_revenue_gbp": int(service_impact * 500000),  # Assume avg £500k/% impact
        "formula": "down_site_volume_pct * 0.75 (redirection efficiency)",
    }


def calc_buffer_stock(ctx, down_site, outage_days, target_service_pct):
    """Calculate buffer inventory needed to cover outage."""
    # Get daily volume from down site
    down_profile = ctx.q(
        "SELECT avg_daily_volume_units FROM dc_profiles WHERE site_id = $site LIMIT 1",
        site=down_site,
    )
    if not down_profile:
        return {"error": f"No profile for {down_site}"}

    daily_volume = down_profile[0]["avg_daily_volume_units"]
    # Buffer = days * daily_volume * service_cushion
    service_cushion = target_service_pct / 100
    buffer_units = outage_days * daily_volume * service_cushion

    # Inventory holding cost: £2 per unit per year
    holding_cost_annual = buffer_units * 2
    total_investment = buffer_units * 15  # Assume £15 per unit acquisition cost

    return {
        "down_site": down_site,
        "outage_days": outage_days,
        "target_service_pct": target_service_pct,
        "daily_volume_units": daily_volume,
        "buffer_inventory_units": int(buffer_units),
        "one_time_cost_gbp": int(total_investment),
        "annual_holding_cost_gbp": int(holding_cost_annual),
        "formula": "outage_days * daily_volume * (target_service_pct / 100)",
    }


def calc_route_cost_comparison(ctx, origin_site, dest_site):
    """Compare costs: direct from DC vs cross-dock vs regional hub."""
    dc_profile = ctx.q(
        "SELECT transport_cost_per_unit_gbp, handling_cost_per_unit_gbp "
        "FROM dc_profiles WHERE site_id = $site LIMIT 1",
        site=origin_site,
    )
    if not dc_profile:
        return {"error": f"Profile not found for {origin_site}"}

    direct_cost_per_unit = dc_profile[0]["transport_cost_per_unit_gbp"]
    direct_cost_per_unit += dc_profile[0]["handling_cost_per_unit_gbp"]

    # Cross-dock costs (lower handling, multiple transport legs)
    cross_dock_cost = (direct_cost_per_unit * 0.85) + 0.15  # 15% less overall but £0.15 cross-dock fee

    # Regional hub (higher transport initially, lower last-mile)
    hub_cost = (direct_cost_per_unit * 1.1) - 0.20  # 10% more but £0.20 savings last-mile

    return {
        "origin_site": origin_site,
        "destination_site": dest_site,
        "direct_from_dc_gbp_per_unit": round(direct_cost_per_unit, 2),
        "via_cross_dock_gbp_per_unit": round(cross_dock_cost, 2),
        "via_regional_hub_gbp_per_unit": round(hub_cost, 2),
        "cheapest_route": "cross_dock" if cross_dock_cost < min(direct_cost_per_unit, hub_cost) else (
            "regional_hub" if hub_cost < direct_cost_per_unit else "direct"
        ),
        "formula": "direct: transport + handling; cross_dock: 85% of direct + £0.15 fee; hub: 110% - £0.20",
    }


def run_disruption_sim(ctx, failing_node, lane_blocked):
    """Simulate disruption impact."""
    # Get profiles
    profiles = ctx.q("SELECT site_id, avg_daily_volume_units FROM dc_profiles")
    if not profiles:
        return {"error": "No network data"}

    total_volume = sum(p["avg_daily_volume_units"] for p in profiles)
    failing = next((p for p in profiles if p["site_id"] == failing_node), None)

    if not failing:
        return {"error": f"Node {failing_node} not found"}

    if lane_blocked:
        # Single lane blocked: 60% of node volume impacted
        impact_pct = (failing["avg_daily_volume_units"] * 0.6) / total_volume * 100
        disruption_days = 7
    else:
        # Node down: 100% of node volume impacted
        impact_pct = (failing["avg_daily_volume_units"] / total_volume) * 100
        disruption_days = 14

    extra_cost = impact_pct * 10000  # £10k per % impact

    return {
        "failing_node": failing_node,
        "disruption_type": "lane_blocked" if lane_blocked else "node_offline",
        "estimated_duration_days": disruption_days,
        "volume_at_risk_pct": round(impact_pct, 1),
        "estimated_recovery_cost_gbp": int(extra_cost),
        "service_impact_pct": round(impact_pct * 0.7, 1),  # 70% of volume impact = service impact
        "formula": "node_volume / total_volume * (0.6 if lane_blocked else 1.0) * 100",
    }
