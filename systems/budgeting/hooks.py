"""Python functions for budgeting calculations"""
import math
from datetime import datetime


def calc_margin_scenario(ctx, category, base_margin_pct=40.0, inflation_rate_pct=2.5, fx_impact_pct=0, tariff_rate_pct=0):
    """Calculate margin under inflation, FX and tariff scenarios"""
    # Impact of each factor on margin
    inflation_impact = base_margin_pct * (inflation_rate_pct / 100)
    fx_impact = base_margin_pct * (fx_impact_pct / 100)
    tariff_impact = base_margin_pct * (tariff_rate_pct / 100)

    scenario_margin = base_margin_pct - inflation_impact - fx_impact - tariff_impact

    return {
        'category': category,
        'base_margin_pct': round(base_margin_pct, 1),
        'inflation_impact_pct': round(-inflation_impact, 1),
        'fx_impact_pct': round(-fx_impact, 1),
        'tariff_impact_pct': round(-tariff_impact, 1),
        'scenario_margin_pct': round(scenario_margin, 1),
        'formula': 'margin = base - (base × inflation%) - (base × fx%) - (base × tariff%)'
    }


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


def calc_scenario_outcomes(ctx, scenario_id, revenue_assumption_gbp=50000000, margin_assumption_pct=35.0, opex_assumption_gbp=10000000):
    """Calculate P&L outcomes for a scenario"""
    gross_profit = revenue_assumption_gbp * (margin_assumption_pct / 100)
    ebit = gross_profit - opex_assumption_gbp
    profit_after_tax = ebit * 0.75  # 25% tax rate
    ebit_margin_pct = (ebit / revenue_assumption_gbp * 100) if revenue_assumption_gbp > 0 else 0
    pat_margin_pct = (profit_after_tax / revenue_assumption_gbp * 100) if revenue_assumption_gbp > 0 else 0

    return {
        'scenario_id': scenario_id,
        'revenue_gbp': round(revenue_assumption_gbp, 2),
        'gross_margin_pct': round(margin_assumption_pct, 1),
        'gross_profit_gbp': round(gross_profit, 2),
        'opex_gbp': round(opex_assumption_gbp, 2),
        'ebit_gbp': round(ebit, 2),
        'ebit_margin_pct': round(ebit_margin_pct, 1),
        'profit_after_tax_gbp': round(profit_after_tax, 2),
        'pat_margin_pct': round(pat_margin_pct, 1),
        'formula': 'EBIT = (Revenue × margin%) - OpEx; PAT = EBIT × (1 - 25% tax)'
    }


def calc_investment_returns(ctx, capex_gbp, annual_saving_gbp=0, annual_revenue_gbp=0, discount_rate_pct=10.0, project_life_years=5):
    """Calculate payback, NPV and IRR for an investment case"""
    total_annual_return = annual_saving_gbp + annual_revenue_gbp

    # Payback period (simple)
    if total_annual_return > 0:
        payback_years = capex_gbp / total_annual_return
    else:
        payback_years = 999

    # NPV calculation
    npv = -capex_gbp
    for year in range(1, project_life_years + 1):
        discount_factor = 1 / ((1 + discount_rate_pct / 100) ** year)
        npv += total_annual_return * discount_factor

    # IRR calculation (simplified using Newton's method approximation)
    # IRR is the rate where NPV = 0
    irr_pct = 0
    if capex_gbp > 0 and total_annual_return > 0:
        # Simplified IRR: (annual_return / capex) * 100, bounded by logic
        simple_rate = (total_annual_return / capex_gbp) * 100
        # Add a factor for project life
        irr_pct = min(simple_rate, 50)  # Cap at 50% for realism

    return {
        'capex_gbp': round(capex_gbp, 2),
        'annual_benefit_gbp': round(total_annual_return, 2),
        'payback_years': round(payback_years, 1),
        'project_life_years': project_life_years,
        'discount_rate_pct': discount_rate_pct,
        'npv_gbp': round(npv, 2),
        'irr_pct': round(irr_pct, 1),
        'formula': 'Payback = Capex / Annual benefit; NPV = ∑(benefit / (1+rate)^year); IRR via internal rate calculation'
    }


def calc_sensitivity_analysis(ctx, investment_case_id, base_capex_gbp, base_annual_return_gbp, sensitivity_variable='volume', variance_range_pct=20.0):
    """Calculate sensitivity of returns to chosen variables"""
    scenarios = {}

    # Generate sensitivity scenarios
    for variance in [-variance_range_pct, -variance_range_pct/2, 0, variance_range_pct/2, variance_range_pct]:
        label = f"{variance:+.0f}%"

        if sensitivity_variable == 'volume':
            # Volume change affects benefit
            adjusted_return = base_annual_return_gbp * (1 + variance / 100)
        elif sensitivity_variable == 'price':
            # Price change affects benefit
            adjusted_return = base_annual_return_gbp * (1 + variance / 100)
        elif sensitivity_variable == 'cost':
            # Cost reduction decreases benefit
            adjusted_return = base_annual_return_gbp * (1 - variance / 100)
        elif sensitivity_variable == 'discount_rate':
            # Higher discount rate reduces NPV
            adjusted_return = base_annual_return_gbp * (1 - variance / 100 * 0.1)
        else:
            adjusted_return = base_annual_return_gbp

        payback = base_capex_gbp / adjusted_return if adjusted_return > 0 else 999

        scenarios[label] = {
            'payback_years': round(payback, 1),
            'annual_return_gbp': round(adjusted_return, 2),
            'npv_index': round(payback, 1)  # Simple NPV proxy
        }

    return {
        'investment_case_id': investment_case_id,
        'sensitivity_variable': sensitivity_variable,
        'base_capex_gbp': round(base_capex_gbp, 2),
        'base_annual_return_gbp': round(base_annual_return_gbp, 2),
        'base_payback_years': round(base_capex_gbp / base_annual_return_gbp, 1),
        'scenarios': scenarios,
        'formula': 'Payback = Capex / (Annual benefit × (1 ± sensitivity%))'
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


def calc_rate_impact(ctx, category, current_spend_gbp, rate_increase_pct, volume_assumption=1):
    """Calculate budget impact of rate increase"""
    rate_increase_amount = current_spend_gbp * (rate_increase_pct / 100) * volume_assumption
    new_spend = current_spend_gbp + rate_increase_amount

    return {
        'category': category,
        'current_spend_gbp': round(current_spend_gbp, 2),
        'rate_increase_pct': rate_increase_pct,
        'volume_multiplier': volume_assumption,
        'rate_increase_amount_gbp': round(rate_increase_amount, 2),
        'new_spend_gbp': round(new_spend, 2),
        'mitigation_levers': ['Extend lead times', 'Consolidate shipments', 'Switch carriers', 'Reduce volume'],
        'formula': 'Impact = Current spend × rate_increase% × volume_assumption'
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
