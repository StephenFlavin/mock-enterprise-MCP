"""Network design calculation hooks."""

BASELINE = "NS-000001"
SEMI_FIXED_LABOUR = 0.6  # share of labour that does not move with volume
DAYS = 365


# ---------- shared helpers ----------

def _scenario(ctx, sid):
    rows = ctx.q("SELECT * FROM network_scenarios WHERE scenario_id = $sid", sid=sid)
    return rows[0] if rows else None


def _base_volume(ctx, sid):
    r = ctx.q("SELECT sum(avg_daily_volume_units) AS d FROM dc_profiles WHERE scenario_id = $sid", sid=sid)
    d = (r[0]["d"] if r else None) or ctx.q(
        "SELECT sum(avg_daily_volume_units) AS d FROM dc_profiles WHERE scenario_id = $sid", sid=BASELINE)[0]["d"]
    return float(d) * DAYS


def _today_ecom_share(ctx):
    r = ctx.q("SELECT ecommerce_share_pct AS s FROM ecommerce_forecasts ORDER BY period LIMIT 1")
    return float(r[0]["s"]) if r else 22.0


def _annual_cost(s, vf, share, base_share, rent_inc):
    """Cost model: handling and transport scale with volume; rent and overhead are fixed; labour is semi-fixed;
    transport rises with e-commerce share above today's share."""
    t_mult = 1 + (s["ecom_transport_uplift_pct"] or 0) / 100.0 * max(0.0, share - base_share)
    handling = s["annual_handling_cost_gbp"] * vf
    transport = s["annual_transport_cost_gbp"] * vf * t_mult
    rent = s["annual_rent_gbp"] * (1 + rent_inc / 100.0)
    overhead = s["annual_overhead_gbp"]
    labour = s["annual_labour_cost_gbp"] * (SEMI_FIXED_LABOUR + (1 - SEMI_FIXED_LABOUR) * vf)
    return {"handling": handling, "transport": transport, "rent": rent, "overhead": overhead, "labour": labour,
            "total": handling + transport + rent + overhead + labour}


def _net(ctx, sid=BASELINE):
    return ctx.q(
        "SELECT d.site_id, COALESCE(s.name, d.site_label) AS name, d.peak_capacity_units_day AS peak, "
        "d.avg_daily_volume_units AS avg FROM dc_profiles d LEFT JOIN master.sites s ON d.site_id = s.site_id "
        "WHERE d.scenario_id = $sid AND COALESCE(d.site_id, '') <> ''", sid=sid)


def _outage(ctx, site, days, lane_factor=1.0):
    net = _net(ctx)
    site = str(site).strip().upper()
    down = next((n for n in net if n["site_id"] == site), None)
    if not down:
        return {"error": f"{site} is not in the modelled UK network. Use one of: " + ", ".join(n["site_id"] for n in net)}
    a = ctx.q("SELECT * FROM outage_scenarios WHERE primary_site_down = $s", s=site)
    a = a[0] if a else {"annual_probability_pct": 0, "expedite_cost_per_unit_gbp": 2.5, "margin_per_unit_gbp": 9.5,
                        "inventory_cost_per_unit_gbp": 14.0, "likely_cause": ""}
    others = [n for n in net if n["site_id"] != site]
    spare = sum(max(0, n["peak"] - n["avg"]) for n in others)
    total_daily = sum(n["avg"] for n in net)
    lost = down["avg"] * lane_factor
    redirected = min(lost, spare)
    unserved = lost - redirected
    best = max(others, key=lambda n: n["peak"] - n["avg"]) if others else None
    cost = redirected * days * a["expedite_cost_per_unit_gbp"] + unserved * days * a["margin_per_unit_gbp"]
    return {"site": site, "name": down["name"], "days": days, "total_daily": total_daily, "down_daily": down["avg"],
            "lost_daily": lost, "spare": spare, "redirected_daily": redirected, "unserved_daily": unserved,
            "service_impact_pct": 100.0 * unserved / total_daily, "volume_at_risk_pct": 100.0 * lost / total_daily,
            "unserved_units": unserved * days, "redirected_units": redirected * days, "cost": cost, "best": best,
            "a": a, "others": others}


# ---------- cost and break-even ----------

def calc_network_total_cost(ctx, scenario_id, annual_volume_units=None, years=5, ecommerce_share_pct=22.0,
                            rent_increase_pct=0.0, volume_growth_pct_pa=0.0):
    """Total network cost for a scenario at a given volume, e-commerce share and rent change."""
    s = _scenario(ctx, scenario_id)
    if not s:
        return {"error": f"Scenario {scenario_id} not found"}
    base_vol = _base_volume(ctx, scenario_id)
    vol = float(annual_volume_units or base_vol)
    base_share = _today_ecom_share(ctx)
    years = max(1, int(years or 5))
    total = 0.0
    y1 = None
    for y in range(years):
        v = vol * (1 + (volume_growth_pct_pa or 0) / 100.0) ** y
        c = _annual_cost(s, v / base_vol, ecommerce_share_pct, base_share, rent_increase_pct or 0.0)
        if y == 0:
            y1 = c
        total += c["total"]
    setup = s["one_off_setup_cost_gbp"] or 0
    return {
        "scenario_id": scenario_id, "scenario_name": s["name"], "annual_volume_units_year1": round(vol),
        "ecommerce_share_pct": ecommerce_share_pct, "rent_increase_pct": rent_increase_pct,
        "year1_handling_cost_gbp": round(y1["handling"]), "year1_transport_cost_gbp": round(y1["transport"]),
        "year1_rent_gbp": round(y1["rent"]), "year1_labour_cost_gbp": round(y1["labour"]),
        "year1_overhead_gbp": round(y1["overhead"]), "year1_total_cost_gbp": round(y1["total"]),
        "cost_per_unit_gbp": round(y1["total"] / vol, 2),
        "years": years, "operating_cost_over_period_gbp": round(total), "one_off_setup_cost_gbp": round(setup),
        "total_cost_over_period_gbp": round(total + setup),
        "assumptions": "volume growth %s%% a year; today's e-commerce share %s%%, transport rises %s%% per extra point of share; "
                       "rent and overhead fixed, labour 60%% fixed; no discounting" % (volume_growth_pct_pa, round(base_share, 1), s["ecom_transport_uplift_pct"]),
        "formula": "handling*vf + transport*vf*(1+uplift*extra share) + rent*(1+rent rise) + overhead + labour*(0.6+0.4*vf), summed over years, plus setup",
    }


def _fixed_var(ctx, s, share, base_share, amortise_years=5):
    base_vol = _base_volume(ctx, s["scenario_id"])
    t_mult = 1 + (s["ecom_transport_uplift_pct"] or 0) / 100.0 * max(0.0, share - base_share)
    fixed = (s["annual_rent_gbp"] + s["annual_overhead_gbp"] + SEMI_FIXED_LABOUR * s["annual_labour_cost_gbp"]
             + (s["one_off_setup_cost_gbp"] or 0) / amortise_years)
    var = (s["annual_handling_cost_gbp"] + s["annual_transport_cost_gbp"] * t_mult
           + (1 - SEMI_FIXED_LABOUR) * s["annual_labour_cost_gbp"]) / base_vol
    return fixed, var


def calc_break_even_volume(ctx, baseline_scenario_id=None, alternative_scenario_id=None, ecommerce_share_pct=22.0,
                           fixed_cost_gbp=None, unit_price_gbp=None, unit_variable_cost_gbp=None):
    """Break-even volume between two network scenarios, or a product break-even."""
    if fixed_cost_gbp is not None and unit_price_gbp is not None and unit_variable_cost_gbp is not None:
        margin = unit_price_gbp - unit_variable_cost_gbp
        if margin <= 0:
            return {"error": "Price must be above variable cost per unit to break even"}
        be = fixed_cost_gbp / margin
        return {"mode": "product", "fixed_cost_gbp": fixed_cost_gbp, "unit_price_gbp": unit_price_gbp,
                "unit_variable_cost_gbp": unit_variable_cost_gbp, "contribution_per_unit_gbp": round(margin, 2),
                "break_even_volume_units": int(-(-be // 1)), "formula": "fixed cost / (price - variable cost per unit)"}
    if not baseline_scenario_id or not alternative_scenario_id:
        return {"error": "Give baseline_scenario_id and alternative_scenario_id, or fixed_cost_gbp, unit_price_gbp and unit_variable_cost_gbp"}
    b, a = _scenario(ctx, baseline_scenario_id), _scenario(ctx, alternative_scenario_id)
    if not b or not a:
        return {"error": "Scenario not found"}
    base_share = _today_ecom_share(ctx)
    bf, bv = _fixed_var(ctx, b, ecommerce_share_pct, base_share)
    af, av = _fixed_var(ctx, a, ecommerce_share_pct, base_share)
    base_vol = _base_volume(ctx, baseline_scenario_id)
    out = {"baseline_scenario": b["name"], "alternative_scenario": a["name"],
           "ecommerce_share_pct": ecommerce_share_pct, "current_volume_units": round(base_vol),
           "baseline_fixed_cost_gbp": round(bf), "baseline_cost_per_unit_gbp": round(bv, 3),
           "alternative_fixed_cost_gbp": round(af), "alternative_cost_per_unit_gbp": round(av, 3)}
    if abs(bv - av) < 1e-9:
        out["note"] = "Same variable cost per unit: no break-even"
        return out
    be = (af - bf) / (bv - av)
    if be <= 0:
        out["break_even_volume_units"] = None
        out["note"] = ("Alternative is cheaper at every volume" if af <= bf else "Baseline is cheaper at every volume")
    else:
        out["break_even_volume_units"] = int(be)
        out["alternative_cheaper_above_break_even"] = av < bv
        out["alternative_cheaper_at_current_volume"] = (af + av * base_vol) < (bf + bv * base_vol)
        out["note"] = ("Alternative is cheaper above this volume" if av < bv else "Alternative is cheaper below this volume")
    out["formula"] = ("annual cost = fixed + variable per unit * volume; fixed = rent + overhead + 60% labour + setup/5 years; "
                      "break-even = (alt fixed - base fixed) / (base var - alt var)")
    return out


# ---------- service, redundancy, peak ----------

def calc_service_impact(ctx, scenario_id, baseline_scenario_id=BASELINE, current_avg_days=None):
    """Change in delivery days and redundancy versus the baseline."""
    s = _scenario(ctx, scenario_id)
    b = _scenario(ctx, baseline_scenario_id or BASELINE)
    if not s or not b:
        return {"error": "Scenario not found"}
    cs = cc = current_avg_days
    if current_avg_days is None:
        cs, cc = b["avg_delivery_days_stores"], b["avg_delivery_days_customers"]
    ds = s["avg_delivery_days_stores"] - cs
    dc = s["avg_delivery_days_customers"] - cc
    return {
        "scenario_id": scenario_id, "scenario_name": s["name"], "compared_with": b["name"],
        "current_store_days": cs, "new_store_days": s["avg_delivery_days_stores"], "change_store_days": round(ds, 1),
        "change_store_pct": round(100 * ds / cs, 1),
        "current_customer_days": cc, "new_customer_days": s["avg_delivery_days_customers"], "change_customer_days": round(dc, 1),
        "change_customer_pct": round(100 * dc / cc, 1),
        "redundancy_score_change": round(s["redundancy_score"] - b["redundancy_score"], 1),
        "service": "improves" if ds < 0 else ("worsens" if ds > 0 else "unchanged"),
        "formula": "proposed delivery days - current delivery days",
    }


def calc_redundancy_cost(ctx, scenario_id, target_redundancy_score=80.0):
    """Cost of adding redundancy to reach a target score."""
    s = _scenario(ctx, scenario_id)
    if not s:
        return {"error": f"Scenario {scenario_id} not found"}
    prof = ctx.q("SELECT sum(avg_daily_volume_units) AS d, sum(peak_capacity_units_day) AS p FROM dc_profiles WHERE scenario_id = $sid", sid=scenario_id)
    daily = float((prof[0]["d"] or 0)) if prof else 0.0
    peak = float((prof[0]["p"] or 0)) if prof else 0.0
    cur = s["redundancy_score"]
    gap = max(0.0, target_redundancy_score - cur)
    unit_cost = ctx.q("SELECT avg(inventory_cost_per_unit_gbp) AS c FROM outage_scenarios")[0]["c"] or 14.0
    buffer_units = daily * 14 * gap / 100.0
    buffer_cost = buffer_units * unit_cost
    capacity_cost = peak * gap / 100.0 * 120.0
    dual_cost = 300000 * gap / 100.0
    one_off = buffer_cost + capacity_cost + dual_cost
    annual = buffer_cost * 0.22 + capacity_cost * 0.10 + dual_cost * 0.15
    return {
        "scenario_id": scenario_id, "scenario_name": s["name"], "current_redundancy_score": cur,
        "target_redundancy_score": target_redundancy_score, "score_gap": round(gap, 1),
        "buffer_stock_units": round(buffer_units), "buffer_stock_cost_gbp": round(buffer_cost),
        "extra_capacity_cost_gbp": round(capacity_cost), "dual_sourcing_cost_gbp": round(dual_cost),
        "one_time_investment_gbp": round(one_off), "annual_cost_gbp": round(annual),
        "formula": "gap/100 x (14 days of volume x unit cost + peak daily capacity x 120 GBP + 300k dual sourcing); annual = 22% holding on stock, 10% on capacity, 15% on dual sourcing",
    }


def calc_peak_capacity_risk(ctx, scenario_id, peak_volume_uplift_pct=25.0):
    """Peak capacity risk for a scenario."""
    profiles = ctx.q("SELECT site_id, site_label, peak_capacity_units_day AS peak, avg_daily_volume_units AS avg "
                     "FROM dc_profiles WHERE scenario_id = $sid", sid=scenario_id)
    if not profiles:
        return {"error": f"No DC profiles for scenario {scenario_id}"}
    cap = sum(p["peak"] for p in profiles)
    avg = sum(p["avg"] for p in profiles)
    peak_vol = avg * (1 + peak_volume_uplift_pct / 100.0)
    spare = cap - peak_vol
    at_risk = peak_vol > cap
    shortfall_pct = 100.0 * max(0.0, peak_vol - cap) / cap
    max_uplift = 100.0 * (cap / avg - 1)
    if at_risk:
        rec = "Capacity shortfall at peak: add temporary or partner capacity, or keep a DC open, before consolidating"
    elif spare / cap < 0.05:
        rec = "Very thin headroom at peak: any slippage or DC disruption breaks service"
    else:
        rec = "Capacity adequate at this peak"
    return {
        "scenario_id": scenario_id, "dcs": ", ".join(p["site_id"] or p["site_label"] for p in profiles),
        "peak_capacity_units_day": cap, "avg_volume_units_day": avg,
        "assumed_peak_uplift_pct": peak_volume_uplift_pct, "peak_volume_units_day": round(peak_vol),
        "spare_capacity_units_day": round(spare), "shortfall_pct_of_capacity": round(shortfall_pct, 1),
        "max_peak_uplift_before_shortfall_pct": round(max_uplift, 1), "at_risk": at_risk, "recommendation": rec,
        "formula": "peak volume = average daily volume x (1 + uplift); spare = peak capacity - peak volume",
    }


# ---------- outages ----------

def run_outage_scenario(ctx, down_site, outage_days=14):
    """Model one DC offline for N days."""
    o = _outage(ctx, down_site, outage_days)
    if "error" in o:
        return o
    best = o["best"]
    return {
        "down_site": o["site"], "name": o["name"], "outage_days": outage_days,
        "daily_volume_lost_units": o["lost_daily"], "network_daily_volume_units": o["total_daily"],
        "spare_capacity_elsewhere_units_day": o["spare"], "redirected_units_day": round(o["redirected_daily"]),
        "unserved_units_day": round(o["unserved_daily"]), "units_unserved_total": round(o["unserved_units"]),
        "service_impact_pct": round(o["service_impact_pct"], 1),
        "best_alternative_site": best["site_id"] if best else None,
        "best_alternative_spare_units_day": (best["peak"] - best["avg"]) if best else 0,
        "cost_of_outage_gbp": round(o["cost"]),
        "formula": "unserved = daily volume lost - spare capacity at other DCs; cost = redirected units x expedite cost + unserved units x lost margin",
    }


def calc_outage_service_impact(ctx, down_site, outage_days=14):
    """Service impact if a DC is offline."""
    o = _outage(ctx, down_site, outage_days)
    if "error" in o:
        return o
    m = ctx.q("SELECT avg(units) AS upo, sum(value_gbp) / sum(units) AS price FROM master.orders")[0]
    upo, price = float(m["upo"]), float(m["price"])
    orders_day = o["total_daily"] / upo
    at_risk_day = o["unserved_daily"] / upo
    return {
        "down_site": o["site"], "outage_days": outage_days,
        "volume_at_risk_pct": round(o["volume_at_risk_pct"], 1),
        "share_of_orders_at_risk_pct": round(o["service_impact_pct"], 1),
        "orders_at_risk_per_day": round(at_risk_day), "orders_at_risk_total": round(at_risk_day * outage_days),
        "orders_rerouted_per_day": round(o["redirected_daily"] / upo),
        "extra_delivery_days_rerouted_orders": 1.0,
        "estimated_lost_revenue_gbp": round(o["unserved_units"] * price),
        "assumptions": "%.1f units per order and GBP %.2f revenue per unit from recent orders; re-routed orders arrive 1 day later" % (upo, price),
        "formula": "unserved units = lost daily volume - spare capacity at other DCs; orders = units / units per order",
    }


def calc_buffer_stock(ctx, down_site, outage_days=14, target_service_pct=95.0):
    """Buffer inventory and extra capacity needed to cover an outage."""
    o = _outage(ctx, down_site, outage_days)
    if "error" in o:
        return o
    cover = target_service_pct / 100.0
    buffer_units = o["unserved_daily"] * outage_days * cover
    unit_cost = o["a"]["inventory_cost_per_unit_gbp"]
    cost = buffer_units * unit_cost
    return {
        "down_site": o["site"], "outage_days": outage_days, "target_service_pct": target_service_pct,
        "daily_volume_lost_units": o["lost_daily"], "spare_capacity_elsewhere_units_day": o["spare"],
        "unserved_units_day": round(o["unserved_daily"]),
        "buffer_inventory_units": round(buffer_units), "one_time_cost_gbp": round(cost),
        "annual_holding_cost_gbp": round(cost * 0.22),
        "alternative_extra_capacity_units_day": round(o["unserved_daily"] * cover),
        "formula": "buffer = (lost daily volume - spare capacity elsewhere) x days x target service; cost = units x unit cost; holding 22% a year",
    }


def run_disruption_sim(ctx, failing_node=None, lane_blocked=False, duration_days=14):
    """Simulate losing a node or lane; compare all DCs when no node is given."""
    net = _net(ctx)
    nodes = [str(failing_node).strip().upper()] if failing_node else [n["site_id"] for n in net]
    out = []
    for site in nodes:
        o = _outage(ctx, site, duration_days, 0.6 if lane_blocked else 1.0)
        if "error" in o:
            return o
        p = o["a"]["annual_probability_pct"]
        out.append({
            "failing_node": site, "name": o["name"],
            "disruption_type": "lane_blocked" if lane_blocked else "node_offline",
            "duration_days": duration_days, "volume_at_risk_pct": round(o["volume_at_risk_pct"], 1),
            "units_unserved": round(o["unserved_units"]), "service_impact_pct": round(o["service_impact_pct"], 1),
            "disruption_cost_gbp": round(o["cost"]), "annual_probability_pct": p,
            "expected_annual_loss_gbp": round(o["cost"] * p / 100.0), "likely_cause": o["a"]["likely_cause"],
        })
    out.sort(key=lambda r: -r["disruption_cost_gbp"])
    for i, r in enumerate(out):
        r["rank_by_cost"] = i + 1
    return out


# ---------- routes ----------

def calc_route_cost_comparison(ctx, origin_site, dest_site, weekly_volume_units=40000, peak_volume_uplift_pct=40.0):
    """Cost per unit of each route from a DC to a store's region, normal and peak."""
    st = ctx.q("SELECT site_id, name, region FROM master.sites WHERE site_id = $s", s=str(dest_site).strip().upper())
    if not st:
        return {"error": f"Destination {dest_site} is not a known site id (use a store id such as ST141)"}
    region = st[0]["region"]
    origin = str(origin_site).strip().upper()
    routes = ctx.q("SELECT * FROM route_costs WHERE origin_site = $o AND dest_region = $r ORDER BY route_id", o=origin, r=region)
    if not routes:
        return {"error": f"No route costs from {origin} to {region}"}
    vol = float(weekly_volume_units)
    pvol = vol * (1 + peak_volume_uplift_pct / 100.0)
    direct = next((r for r in routes if r["route_type"] == "direct_from_dc"), None)
    rows = []
    for r in routes:
        var = r["handling_gbp_per_unit"] + r["transport_gbp_per_unit"] + r["inventory_holding_gbp_per_unit"]
        pvar = (r["handling_gbp_per_unit"] * (1 + r["peak_handling_uplift_pct"] / 100.0)
                + r["transport_gbp_per_unit"] * (1 + r["peak_transport_uplift_pct"] / 100.0) + r["inventory_holding_gbp_per_unit"])
        normal = var + r["fixed_cost_gbp_per_week"] / vol
        peak = pvar + r["fixed_cost_gbp_per_week"] / pvol
        row = {"route_type": r["route_type"], "via": r["via_label"] or "", "origin_site": origin, "dest_store": st[0]["site_id"],
               "dest_region": region, "handling_gbp_per_unit": r["handling_gbp_per_unit"],
               "transport_gbp_per_unit": r["transport_gbp_per_unit"],
               "inventory_holding_gbp_per_unit": r["inventory_holding_gbp_per_unit"],
               "fixed_cost_gbp_per_week": r["fixed_cost_gbp_per_week"], "weekly_volume_units": round(vol),
               "normal_total_gbp_per_unit": round(normal, 2), "peak_total_gbp_per_unit": round(peak, 2),
               "peak_handling_uplift_pct": r["peak_handling_uplift_pct"], "peak_transport_uplift_pct": r["peak_transport_uplift_pct"]}
        if direct and r is not direct:
            dvar = direct["handling_gbp_per_unit"] + direct["transport_gbp_per_unit"] + direct["inventory_holding_gbp_per_unit"]
            dpvar = (direct["handling_gbp_per_unit"] * (1 + direct["peak_handling_uplift_pct"] / 100.0)
                     + direct["transport_gbp_per_unit"] * (1 + direct["peak_transport_uplift_pct"] / 100.0)
                     + direct["inventory_holding_gbp_per_unit"])
            row["breakeven_weekly_volume_normal"] = round(r["fixed_cost_gbp_per_week"] / (dvar - var)) if dvar > var else None
            row["breakeven_weekly_volume_peak"] = round(r["fixed_cost_gbp_per_week"] / (dpvar - pvar)) if dpvar > pvar else None
        rows.append(row)
    cn = min(rows, key=lambda x: x["normal_total_gbp_per_unit"])["route_type"]
    cp = min(rows, key=lambda x: x["peak_total_gbp_per_unit"])["route_type"]
    for row in rows:
        row["cheapest_normal"] = cn
        row["cheapest_at_peak"] = cp
        row["formula"] = ("handling + transport + inventory holding + fixed weekly cost / weekly volume; peak applies the handling and "
                          "transport uplifts and %s%% more volume" % peak_volume_uplift_pct)
    return rows


# ---------- volume forecast ----------

def run_volume_forecast(ctx, growth_rate_pct=5.0, ecommerce_penetration_pct=40.0, target_year=2030, new_market_uplift_pct=0.0):
    """Forecast annual volume by region and channel for a target year."""
    base = ctx.q("SELECT region, channel, sum(units) AS u FROM volume_history "
                 "WHERE period > CAST($as_of AS DATE) - INTERVAL 365 DAY GROUP BY region, channel")
    if not base:
        return {"error": "No volume history"}
    this_year = int(str(ctx.as_of)[:4])
    n = max(0, int(target_year) - this_year)
    total_base = sum(b["u"] for b in base)
    ecom_base = sum(b["u"] for b in base if b["channel"] == "ecommerce")
    whole_base = sum(b["u"] for b in base if b["channel"] == "wholesale")
    w0 = whole_base / total_base
    e1 = ecommerce_penetration_pct / 100.0
    shares = {"ecommerce": e1, "wholesale": w0, "stores": max(0.0, 1 - e1 - w0)}
    grown = total_base * (1 + growth_rate_pct / 100.0) ** n
    region_w = {}
    for b in base:
        region_w[b["region"]] = region_w.get(b["region"], 0) + b["u"] / total_base
    out = []
    totals = {"stores": 0, "ecommerce": 0, "wholesale": 0}
    for region in sorted(region_w):
        reg_total = grown * region_w[region]
        if region == "EU Central":
            reg_total *= 1 + new_market_uplift_pct / 100.0
        for ch in ("stores", "ecommerce", "wholesale"):
            f = reg_total * shares[ch]
            totals[ch] += f
            bu = next((b["u"] for b in base if b["region"] == region and b["channel"] == ch), 0)
            out.append({"region": region, "channel": ch, "base_units_last_12m": bu, "forecast_units": round(f),
                        "target_year": target_year})
    grand = sum(totals.values())
    for ch in ("stores", "ecommerce", "wholesale"):
        out.append({"region": "ALL REGIONS", "channel": ch, "base_units_last_12m": sum(b["u"] for b in base if b["channel"] == ch),
                    "forecast_units": round(totals[ch]), "target_year": target_year})
    out.append({"region": "ALL REGIONS", "channel": "TOTAL", "base_units_last_12m": total_base, "forecast_units": round(grand),
                "target_year": target_year, "assumptions": "growth %s%% a year for %d years; e-commerce %s%% of volume (today %.1f%%); "
                "new market uplift %s%% on EU Central; wholesale share held at %.1f%%; regional mix held at last 12 months"
                % (growth_rate_pct, n, ecommerce_penetration_pct, 100 * ecom_base / total_base, new_market_uplift_pct, 100 * w0),
                "formula": "forecast = last 12 months x (1+growth)^years, split by target channel shares and today's regional mix"})
    return out
