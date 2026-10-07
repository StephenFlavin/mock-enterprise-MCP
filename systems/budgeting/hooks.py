"""Python functions for budgeting calculations"""
import math
from datetime import date


# ---------------- helpers ----------------

def _month_params(period_from, period_to):
    f = str(period_from)[:10] if period_from else None
    t = str(period_to)[:10] if period_to else f
    return f, t


def _cashflows(capex, annual_benefit, years, build_months=0, delay_months=0):
    """Monthly cash flows: capex at month 0, benefits start after the build (plus any slip)."""
    start = int(build_months) + int(delay_months)
    n = start + int(round(years * 12))
    flows = [-float(capex)] + [0.0] * n
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


def _case(ctx, investment_case_id):
    if not investment_case_id:
        return None
    rows = ctx.q("SELECT * FROM investment_cases WHERE investment_case_id = $i", i=investment_case_id)
    return rows[0] if rows else None


# ---------------- margin scenarios ----------------

def calc_margin_scenario(ctx, category, scenario_id=None, inflation_rate_pct=None, fx_impact_pct=None,
                         tariff_rate_pct=None, price_increase_pct=0.0):
    """Margin for a category under each planning scenario: cost inflation, FX and tariffs compound on cost of goods."""
    plans = ctx.q("""SELECT mp.*, fs.name AS scenario_name FROM margin_plans mp
                     LEFT JOIN forecast_scenarios fs ON fs.scenario_id = mp.scenario_id
                     WHERE lower(mp.category) = lower($c) AND ($s IS NULL OR mp.scenario_id = $s)
                     ORDER BY mp.scenario_id""", c=category, s=scenario_id)
    if not plans:
        cats = [r["category"] for r in ctx.q("SELECT DISTINCT category FROM margin_plans ORDER BY 1")]
        return f"No margin plan for category '{category}'. Categories with a plan: {', '.join(cats)}."
    custom = any(v is not None for v in (inflation_rate_pct, fx_impact_pct, tariff_rate_pct))
    if custom and scenario_id is None:
        plans = plans[:1]
    out = []
    price_up = float(price_increase_pct or 0)
    for p in plans:
        base = float(p["planned_margin_pct"])
        infl = float(p["inflation_assumption_pct"] if inflation_rate_pct is None else inflation_rate_pct)
        fx = float(p["fx_impact_pct"] if fx_impact_pct is None else fx_impact_pct)
        tar = float(p["tariff_impact_pct"] if tariff_rate_pct is None else tariff_rate_pct)
        cost0 = 100.0 - base                      # cost of goods per £100 of price
        cost1 = cost0 * (1 + infl / 100)
        cost2 = cost1 * (1 + fx / 100)
        cost3 = cost2 * (1 + tar / 100)
        price = 100.0 * (1 + price_up / 100)
        final = (price - cost3) / price * 100
        no_price = 100.0 - cost3
        out.append({
            "scenario_id": p["scenario_id"],
            "scenario_name": p["scenario_name"] + (" (custom shocks)" if custom and scenario_id is None else ""),
            "category": p["category"],
            "planned_margin_pct": round(base, 1),
            "inflation_pct": infl, "fx_cost_pct": fx, "tariff_pct": tar, "price_increase_pct": price_up,
            "inflation_impact_pts": round((100 - cost1) - base, 1),
            "fx_impact_pts": round((100 - cost2) - (100 - cost1), 1),
            "tariff_impact_pts": round((100 - cost3) - (100 - cost2), 1),
            "price_offset_pts": round(final - no_price, 1),
            "scenario_margin_pct": round(final, 1),
            "margin_change_pts": round(final - base, 1),
            "formula": "cost of goods = (100 - planned margin) x (1+inflation) x (1+FX) x (1+tariff); margin = (price - cost) / price",
        })
    return out


def calc_rate_impact(ctx, category, rate_increase_pct, current_spend_gbp=None, cost_centre_id=None, volume_assumption=1.0):
    """Annual budget impact of a rate increase on a spend category."""
    q = """SELECT SUM(actual_gbp) AS spend, count(DISTINCT date_trunc('month', period_date)) AS months FROM actual_costs
           WHERE lower(category) = lower($c) AND ($cc IS NULL OR cost_centre_id = $cc)
             AND date_trunc('month', period_date) >= date_trunc('month', CAST($as_of AS DATE)) - INTERVAL 12 MONTH
             AND date_trunc('month', period_date) < date_trunc('month', CAST($as_of AS DATE))"""
    qb = q.replace("SUM(actual_gbp)", "SUM(value_gbp)").replace("FROM actual_costs", "FROM budget_lines")
    basis = "supplied by caller"
    spend = current_spend_gbp
    if spend is None:
        row = ctx.q(q, c=category, cc=cost_centre_id)[0]
        if not row["spend"]:
            cats = [r["category"] for r in ctx.q("SELECT category FROM expense_categories ORDER BY category")]
            return f"No actual spend for category '{category}'. Categories: {', '.join(cats)}. Or pass current_spend_gbp."
        spend = float(row["spend"])
        basis = f"actual spend over the last {row['months']} months"
    bud = ctx.q(qb, c=category, cc=cost_centre_id)[0]["spend"]
    vol = float(volume_assumption if volume_assumption is not None else 1.0)
    new_spend = spend * vol * (1 + rate_increase_pct / 100)
    out = {
        "category": category,
        "cost_centre_id": cost_centre_id or "all",
        "spend_basis": basis,
        "current_annual_spend_gbp": round(spend, 2),
        "rate_increase_pct": rate_increase_pct,
        "volume_multiplier": vol,
        "annual_increase_gbp": round(new_spend - spend, 2),
        "new_annual_spend_gbp": round(new_spend, 2),
    }
    if bud:
        out["current_annual_budget_gbp"] = round(float(bud), 2)
        out["new_spend_vs_budget_gbp"] = round(new_spend - float(bud), 2)
    out["formula"] = "new spend = current spend x volume multiplier x (1 + rate increase %); increase = new spend - current spend"
    return out


# ---------------- operating profit variance ----------------

def _grouped(rows, keyfn):
    out = {}
    for r in rows:
        out.setdefault(keyfn(r), []).append(r)
    return out


def profit_variance(ctx, period_from=None, period_to=None, entity_id=None, category=None, group_by="entity"):
    """Operating profit actual versus budget by entity, category or month, with a total row."""
    f, t = _month_params(period_from, period_to)
    rows = ctx.q("""SELECT p.entity_id, le.name AS entity_name, p.category, strftime(date_trunc('month', p.period_date), '%Y-%m') AS period,
                           p.budget_profit_gbp AS b, p.actual_profit_gbp AS a, p.basis
                    FROM profit_lines p LEFT JOIN master.legal_entities le ON le.entity_id = p.entity_id
                    WHERE date_trunc('month', p.period_date) >= date_trunc('month', CAST($f AS DATE))
                      AND date_trunc('month', p.period_date) <= date_trunc('month', CAST($t AS DATE))
                      AND ($e IS NULL OR p.entity_id = $e) AND ($c IS NULL OR lower(p.category) = lower($c))""",
                 f=f, t=t, e=entity_id, c=category)
    if not rows:
        return "No profit lines for that period, entity or category."
    keys = {"entity": lambda r: (r["entity_id"], r["entity_name"], "ALL", "ALL"),
            "category": lambda r: ("ALL", None, r["category"], "ALL"),
            "entity_category": lambda r: (r["entity_id"], r["entity_name"], r["category"], "ALL"),
            "period": lambda r: ("ALL", None, "ALL", r["period"])}[group_by or "entity"]

    def line(k, rs):
        b, a = sum(x["b"] for x in rs), sum(x["a"] for x in rs)
        return {"entity_id": k[0], "entity_name": k[1], "category": k[2], "period": k[3],
                "budget_profit_gbp": round(b, 0), "actual_profit_gbp": round(a, 0), "variance_gbp": round(a - b, 0),
                "variance_pct": round((a - b) / b * 100, 1) if b else None,
                "basis": "month_to_date" if any(x["basis"] == "month_to_date" for x in rs) else "full_month"}

    groups = _grouped(rows, keys)
    out = sorted((line(k, rs) for k, rs in groups.items()), key=lambda x: (x["period"] if group_by == "period" else "", x["variance_gbp"]))
    if len(out) > 1:
        out.insert(0, line(("TOTAL", None, "ALL", "ALL"), rows))
    return out


def calc_variance_drivers(ctx, period_from=None, period_to=None, entity_id=None, category=None, group_by="driver"):
    """Operating profit variance by driver, permanent versus timing, explained versus unexplained."""
    f, t = _month_params(period_from, period_to)
    rows = ctx.q("""SELECT v.*, le.name AS entity_name, strftime(date_trunc('month', v.period_date), '%Y-%m') AS period
                    FROM variance_items v LEFT JOIN master.legal_entities le ON le.entity_id = v.entity_id
                    WHERE date_trunc('month', v.period_date) >= date_trunc('month', CAST($f AS DATE))
                      AND date_trunc('month', v.period_date) <= date_trunc('month', CAST($t AS DATE))
                      AND ($e IS NULL OR v.entity_id = $e) AND ($c IS NULL OR lower(v.category) = lower($c))""",
                 f=f, t=t, e=entity_id, c=category)
    if not rows:
        return "No variance items for that period, entity or category."
    if group_by == "item":
        rows.sort(key=lambda x: (x["explained"], -abs(x["amount_gbp"])))
        return [{"variance_item_id": r["variance_item_id"], "entity_id": r["entity_id"], "category": r["category"], "period": r["period"],
                 "driver": r["driver"], "nature": r["nature"], "amount_gbp": round(r["amount_gbp"], 0),
                 "explained": r["explained"], "explanation": r["explanation"]} for r in rows]
    key = {"driver": "driver", "entity": "entity_id", "category": "category"}[group_by or "driver"]

    def line(label, rs):
        tot = sum(x["amount_gbp"] for x in rs)
        return {key: label, "variance_gbp": round(tot, 0),
                "permanent_gbp": round(sum(x["amount_gbp"] for x in rs if x["nature"] == "permanent"), 0),
                "timing_gbp": round(sum(x["amount_gbp"] for x in rs if x["nature"] == "timing"), 0),
                "explained_gbp": round(sum(x["amount_gbp"] for x in rs if x["explained"]), 0),
                "unexplained_gbp": round(sum(x["amount_gbp"] for x in rs if not x["explained"]), 0),
                "items": len(rs)}

    groups = _grouped(rows, lambda r: r[key])
    out = sorted((line(k, rs) for k, rs in groups.items()), key=lambda x: x["variance_gbp"])
    out.insert(0, line("TOTAL", rows))
    return out


# ---------------- forecast scenarios ----------------

def calc_scenario_outcomes(ctx, forecast_version_id=None, scenario_id=None, demand_change_pct=None, price_change_pct=None,
                           freight_change_pct=None, cost_inflation_pct=0.0):
    """Full-year P&L under changed demand, price, freight and cost against a base forecast version."""
    if forecast_version_id:
        base = ctx.q("SELECT * FROM forecast_versions WHERE forecast_version_id = $v", v=forecast_version_id)
    else:
        base = ctx.q("""SELECT * FROM forecast_versions WHERE status = 'current' AND forecast_type = 'forecast'
                        ORDER BY forecast_date DESC, forecast_version_id DESC LIMIT 1""")
    if not base:
        return "No forecast version found to use as the base."
    base = base[0]
    sc = ctx.q("SELECT * FROM forecast_scenarios WHERE scenario_id = $s", s=scenario_id)[0] if scenario_id and ctx.q(
        "SELECT 1 FROM forecast_scenarios WHERE scenario_id = $s", s=scenario_id) else None

    def pick(arg, col):
        if arg is not None:
            return float(arg)
        return float(sc[col]) if sc and sc.get(col) not in (None, "") else 0.0

    d, p, fr = pick(demand_change_pct, "demand_change_pct"), pick(price_change_pct, "price_change_pct"), pick(freight_change_pct, "freight_change_pct")
    ci = float(cost_inflation_pct or 0)
    rev0 = float(base["revenue_forecast_gbp"])
    gp0 = rev0 * float(base["gross_margin_pct"]) / 100
    frt0 = float(base["freight_cost_gbp"] or 0)
    cogs_other0 = rev0 - gp0 - frt0
    opex0 = gp0 - float(base["ebit_forecast_gbp"])
    rev = rev0 * (1 + d / 100) * (1 + p / 100)
    other = cogs_other0 * (1 + d / 100) * (1 + ci / 100)
    frt = frt0 * (1 + d / 100) * (1 + fr / 100)
    gp = rev - other - frt
    opex = opex0 * (0.8 + 0.2 * (1 + d / 100))     # 20% of opex flexes with volume
    ebit = gp - opex
    ebit0 = float(base["ebit_forecast_gbp"])
    return {
        "base_forecast_version_id": base["forecast_version_id"],
        "scenario": sc["name"] if sc else "custom",
        "demand_change_pct": d, "price_change_pct": p, "freight_change_pct": fr, "cost_inflation_pct": ci,
        "base_revenue_gbp": round(rev0, 0), "base_gross_margin_pct": round(gp0 / rev0 * 100, 1), "base_ebit_gbp": round(ebit0, 0),
        "revenue_gbp": round(rev, 0),
        "gross_profit_gbp": round(gp, 0),
        "gross_margin_pct": round(gp / rev * 100, 1) if rev else 0,
        "freight_cost_gbp": round(frt, 0),
        "opex_gbp": round(opex, 0),
        "ebit_gbp": round(ebit, 0),
        "ebit_change_vs_base_gbp": round(ebit - ebit0, 0),
        "ebit_change_vs_base_pct": round((ebit - ebit0) / ebit0 * 100, 1) if ebit0 else None,
        "formula": "revenue = base x (1+demand) x (1+price); other COGS = base x (1+demand) x (1+cost inflation); freight = base x (1+demand) x (1+freight rate); opex flexes 20% with demand; EBIT = revenue - COGS - opex",
    }


# ---------------- investment returns ----------------

def calc_investment_returns(ctx, investment_case_id=None, capex_gbp=None, annual_saving_gbp=None, annual_revenue_gbp=None,
                            discount_rate_pct=10.0, project_life_years=None, delay_months=0):
    """Payback, NPV and IRR from monthly cash flows: capex up front, benefits after the build."""
    case = _case(ctx, investment_case_id)
    if investment_case_id and not case:
        return f"No investment case {investment_case_id}."
    capex = capex_gbp if capex_gbp is not None else (float(case["capex_gbp"]) if case else None)
    if capex is None:
        return "Give an investment_case_id or capex_gbp."
    saving = annual_saving_gbp if annual_saving_gbp is not None else (float(case["annual_saving_gbp"] or 0) if case else 0.0)
    revenue = annual_revenue_gbp if annual_revenue_gbp is not None else (float(case["annual_revenue_gbp"] or 0) if case else 0.0)
    life = project_life_years or (int(case["project_life_years"] or 5) if case else 5)
    build = int(case["build_months"] or 0) if case else 0
    benefit = saving + revenue
    flows = _cashflows(capex, benefit, life, build, delay_months or 0)
    pb = _payback_months(flows)
    irr = _irr(flows)
    return {
        "investment_case_id": investment_case_id or "",
        "title": case["title"] if case else "",
        "capex_gbp": round(capex, 0),
        "annual_benefit_gbp": round(benefit, 0),
        "build_months": build,
        "delay_months": int(delay_months or 0),
        "project_life_years": life,
        "discount_rate_pct": discount_rate_pct,
        "payback_years": round(pb / 12, 1) if pb is not None else None,
        "payback_months": round(pb, 0) if pb is not None else None,
        "npv_gbp": round(_npv(flows, discount_rate_pct / 100), 0),
        "irr_pct": round(irr * 100, 1) if irr is not None else None,
        "formula": "capex at month 0; benefit / 12 a month once built (build + delay months), for the project life; payback counted from first spend; NPV discounted monthly",
    }


def calc_sensitivity_analysis(ctx, investment_case_id=None, base_capex_gbp=None, base_annual_return_gbp=None,
                              sensitivity_variable="volume", variance_range_pct=20.0, discount_rate_pct=10.0):
    """Payback, NPV and IRR as one variable moves either side of the base case."""
    case = _case(ctx, investment_case_id)
    if investment_case_id and not case:
        return f"No investment case {investment_case_id}."
    capex = base_capex_gbp if base_capex_gbp is not None else (float(case["capex_gbp"]) if case else None)
    ret = base_annual_return_gbp if base_annual_return_gbp is not None else (
        float(case["annual_saving_gbp"] or 0) + float(case["annual_revenue_gbp"] or 0) if case else None)
    if capex is None or ret is None:
        return "Give an investment_case_id, or base_capex_gbp and base_annual_return_gbp."
    life = int(case["project_life_years"] or 5) if case else 5
    build = int(case["build_months"] or 0) if case else 0
    rng = float(variance_range_pct if variance_range_pct is not None else 20.0)
    steps = [-rng, -rng / 2, 0.0, rng / 2, rng]
    if sensitivity_variable == "delay":
        steps = [0.0, 3.0, 6.0, 9.0, 12.0]
    out = []
    for s in steps:
        cx, rt, dr, dl = capex, ret, discount_rate_pct, 0
        if sensitivity_variable in ("volume", "price"):
            rt = ret * (1 + s / 100)
            label = f"{s:+.0f}% {sensitivity_variable}"
        elif sensitivity_variable == "cost":
            cx = capex * (1 + s / 100)
            label = f"{s:+.0f}% capex"
        elif sensitivity_variable == "discount_rate":
            pts = s / 10.0
            dr = discount_rate_pct + pts
            label = f"{dr:.1f}% discount rate"
        else:
            dl = int(s)
            label = f"{dl} months delay"
        flows = _cashflows(cx, rt, life, build, dl)
        pb, irr = _payback_months(flows), _irr(flows)
        out.append({
            "investment_case_id": investment_case_id or "", "variable": sensitivity_variable, "case": label,
            "capex_gbp": round(cx, 0), "annual_benefit_gbp": round(rt, 0),
            "payback_years": round(pb / 12, 1) if pb is not None else None,
            "npv_gbp": round(_npv(flows, dr / 100), 0),
            "irr_pct": round(irr * 100, 1) if irr is not None else None,
        })
    out[len(out) // 2 if sensitivity_variable != "delay" else 0]["formula"] = (
        "monthly cash flows: capex at month 0, benefit/12 a month after the build, payback from first spend; NPV discounted monthly")
    return out


# ---------------- margin phasing ----------------

def get_margin_phasing_forecast(ctx, landed_cost_increase_pct, affected_cogs_share_pct=100.0, stock_cover_weeks=12.0,
                                months=6, price_recovery_pct=0.0):
    """Flow-through of a landed cost increase into margin by month, as stock bought at the old cost sells through."""
    base = ctx.q("""SELECT revenue_forecast_gbp AS rev, gross_margin_pct AS gm FROM forecast_versions
                    WHERE status = 'current' AND forecast_type = 'forecast' ORDER BY forecast_date DESC LIMIT 1""")
    if not base:
        return "No current forecast to take revenue and margin from."
    rev_m = float(base[0]["rev"]) / 12
    gm = float(base[0]["gm"])
    cogs_m = rev_m * (1 - gm / 100)
    affected = cogs_m * affected_cogs_share_pct / 100
    cover_m = max(float(stock_cover_weeks) / 4.345, 0.01)
    y, m0 = int(ctx.as_of[:4]), int(ctx.as_of[5:7])
    out, cum = [], 0.0
    for n in range(1, int(months) + 1):
        share = min(1.0, max(0.0, (n - 0.5) / cover_m))        # share of the month's sales at the new cost
        extra = affected * landed_cost_increase_pct / 100 * share
        recovered = extra * (price_recovery_pct or 0) / 100
        net = extra - recovered
        cum += net
        yy, mm = divmod(y * 12 + (m0 - 1) + (n - 1), 12)
        out.append({
            "month": f"{yy}-{mm + 1:02d}", "share_of_sales_at_new_cost_pct": round(share * 100, 0),
            "extra_cogs_gbp": round(extra, 0), "price_recovery_gbp": round(recovered, 0), "net_margin_hit_gbp": round(net, 0),
            "gross_margin_pct": round((rev_m - cogs_m - net) / rev_m * 100, 2),
            "margin_change_pts": round(-net / rev_m * 100, 2), "cumulative_hit_gbp": round(cum, 0)})
    out.append({"month": "Total", "share_of_sales_at_new_cost_pct": None, "extra_cogs_gbp": round(sum(o["extra_cogs_gbp"] for o in out), 0),
                "price_recovery_gbp": round(sum(o["price_recovery_gbp"] for o in out), 0), "net_margin_hit_gbp": round(cum, 0),
                "gross_margin_pct": round(sum(o["gross_margin_pct"] for o in out) / len(out), 2), "margin_change_pts": None,
                "cumulative_hit_gbp": round(cum, 0)})
    out[-1]["formula"] = ("monthly revenue and starting margin from the current forecast; share at new cost = (month - 0.5) / stock cover in months, capped at 100%; "
                          "hit = affected COGS x cost increase x share x (1 - price recovery)")
    return out


def calc_pl_scenario(ctx, scenario_id, base_revenue_gbp=1000000, volume_change_pct=0, price_change_pct=0, nearshore_mix_pct=0):
    """Calculate full P&L under a scenario with changed sourcing mix"""
    # Revenue impact
    volume_effect = base_revenue_gbp * (volume_change_pct / 100)
    price_effect = base_revenue_gbp * (price_change_pct / 100)
    adjusted_revenue = base_revenue_gbp + volume_effect + price_effect

    # Cost impact - nearshoring reduces cost
    base_cogs_pct = 60.0  # 60% of revenue
    base_cogs = base_revenue_gbp * (base_cogs_pct / 100)

    # Nearshoring saves ~5% of COGS but has transition cost
    nearshore_saving = base_cogs * (nearshore_mix_pct / 100) * 0.05
    transition_cost = nearshore_mix_pct * 50000  # £50k per 1% shift

    adjusted_cogs = base_cogs - nearshore_saving + transition_cost

    # Margin and EBIT
    gross_profit = adjusted_revenue - adjusted_cogs
    gross_margin_pct = (gross_profit / adjusted_revenue * 100) if adjusted_revenue > 0 else 0

    # Fixed opex is ~15% of base revenue
    fixed_opex = base_revenue_gbp * 0.15
    ebit = gross_profit - fixed_opex
    ebit_margin_pct = (ebit / adjusted_revenue * 100) if adjusted_revenue > 0 else 0

    return {
        'scenario_id': scenario_id,
        'revenue_gbp': round(adjusted_revenue, 2),
        'cogs_gbp': round(adjusted_cogs, 2),
        'gross_profit_gbp': round(gross_profit, 2),
        'gross_margin_pct': round(gross_margin_pct, 1),
        'opex_gbp': round(fixed_opex, 2),
        'ebit_gbp': round(ebit, 2),
        'ebit_margin_pct': round(ebit_margin_pct, 1),
        'volume_change_pct': volume_change_pct,
        'price_change_pct': price_change_pct,
        'nearshore_mix_pct': nearshore_mix_pct,
        'formula': 'revenue + (volume% + price%) impact; COGS reduced by nearshoring (5% saving); opex = 15% of base'
    }


def calc_breakeven(ctx, initial_investment_gbp, monthly_return_gbp=0, annual_return_gbp=0):
    """Calculate breakeven period for an investment"""
    # Convert to monthly
    if annual_return_gbp > 0:
        monthly_return = annual_return_gbp / 12
    else:
        monthly_return = monthly_return_gbp

    if monthly_return <= 0:
        breakeven_months = 999
    else:
        breakeven_months = initial_investment_gbp / monthly_return

    breakeven_years = breakeven_months / 12

    return {
        'initial_investment_gbp': round(initial_investment_gbp, 2),
        'monthly_return_gbp': round(monthly_return, 2),
        'annual_return_gbp': round(monthly_return * 12, 2),
        'breakeven_months': round(breakeven_months, 1),
        'breakeven_years': round(breakeven_years, 2),
        'formula': 'Breakeven = Initial investment / Monthly return'
    }


def calc_programme_payback(ctx, programme_id, investment_gbp, annual_benefit_gbp):
    """Calculate payback period for a cost-saving or revenue programme"""
    if annual_benefit_gbp <= 0:
        payback_years = 999
    else:
        payback_years = investment_gbp / annual_benefit_gbp

    payback_months = payback_years * 12

    return {
        'programme_id': programme_id,
        'investment_gbp': round(investment_gbp, 2),
        'annual_benefit_gbp': round(annual_benefit_gbp, 2),
        'payback_months': round(payback_months, 1),
        'payback_years': round(payback_years, 2),
        'formula': 'Payback = Investment / Annual benefit'
    }


def calc_programme_savings(ctx, programme_id, start_date=None):
    """Calculate total savings from a programme"""
    # Get programme data from database
    progs = ctx.q("SELECT * FROM programmes WHERE programme_id = $p", p=programme_id)
    if not progs:
        return {'error': f'Programme {programme_id} not found'}

    prog = progs[0]

    # Get programme costs
    costs = ctx.q("SELECT SUM(actual_gbp) AS total_actual, SUM(forecast_gbp) AS total_forecast FROM programme_costs WHERE programme_id = $p", p=programme_id)

    total_actual = float(costs[0].get('total_actual') or 0)
    total_forecast = float(costs[0].get('total_forecast') or 0)

    # Programme savings = budget - actual spend (for cost-saving programmes)
    if prog['type'] == 'cost_saving':
        savings = total_forecast - total_actual
    else:
        savings = total_actual  # Revenue realized

    return {
        'programme_id': programme_id,
        'programme_name': prog['name'],
        'programme_budget_gbp': round(float(prog['budget_gbp']), 2),
        'total_forecast_gbp': round(total_forecast, 2),
        'total_actual_gbp': round(total_actual, 2),
        'savings_gbp': round(savings, 2),
        'burn_rate_pct': round((total_actual / prog['budget_gbp'] * 100) if prog['budget_gbp'] > 0 else 0, 1),
        'formula': 'Savings = Forecast spend - Actual spend (cost programmes) or Actual - Forecast (revenue)'
    }


def calc_investment_required(ctx, target_gbp, roi_target_pct=30.0, payback_years=3.0):
    """Calculate investment required to achieve a target"""
    # Back-solve: capex = target / (ROI% / 100)
    # But also consider payback: annual_return = capex / payback_years
    # So: capex = target / (ROI% / 100) = annual_return * payback_years

    annual_return_needed = target_gbp
    capex_from_roi = target_gbp / (roi_target_pct / 100) if roi_target_pct > 0 else target_gbp
    capex_from_payback = annual_return_needed * payback_years

    # Use the higher of the two (more conservative)
    capex_required = max(capex_from_roi, capex_from_payback)

    # Calculate implied payback and ROI
    implied_payback = capex_required / annual_return_needed if annual_return_needed > 0 else 999
    implied_roi = (annual_return_needed / capex_required * 100) if capex_required > 0 else 0

    return {
        'target_gbp': round(target_gbp, 2),
        'roi_target_pct': roi_target_pct,
        'payback_target_years': round(payback_years, 1),
        'capex_required_gbp': round(capex_required, 2),
        'annual_return_required_gbp': round(annual_return_needed, 2),
        'implied_payback_years': round(implied_payback, 2),
        'implied_roi_pct': round(implied_roi, 1),
        'formula': 'Capex = max(Target / ROI%, Annual return × Payback years)'
    }


def forecast_shrink(ctx, ytd_shrink_pct, target_shrink_pct=1.5):
    """Forecast year-end shrink by store and category"""
    months_remaining = 12 - 10  # Assuming we're in October (month 10)

    # Trend: if YTD is above target, assume shrink continues or improves slightly
    if ytd_shrink_pct > target_shrink_pct:
        improvement_factor = 0.1  # 10% improvement in remaining months
        forecasted_ytd_shrink = ytd_shrink_pct * (1 - (improvement_factor * (months_remaining / 12)))
    else:
        forecasted_ytd_shrink = ytd_shrink_pct

    shrink_impact_gbp = 50000000 * (forecasted_ytd_shrink / 100)  # Assume £50m revenue base

    return {
        'ytd_shrink_pct': round(ytd_shrink_pct, 2),
        'target_shrink_pct': round(target_shrink_pct, 2),
        'forecasted_year_end_shrink_pct': round(forecasted_ytd_shrink, 2),
        'shrink_impact_gbp': round(shrink_impact_gbp, 2),
        'variance_vs_target_pct': round(forecasted_ytd_shrink - target_shrink_pct, 2),
        'mitigation_priority': 'high' if forecasted_ytd_shrink > target_shrink_pct * 1.5 else 'medium',
        'formula': 'Forecasted shrink = YTD × (1 - improvement%) based on performance trend'
    }
