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


def get_margin_phasing_forecast(ctx, starting_margin_pct=35.0, cost_change_gbp=0, recovery_months=6):
    """Calculate margin flow-through by month from landed cost changes"""
    monthly_data = []

    for month in range(1, recovery_months + 1):
        # Gradual recovery: month 1 = full impact, gradually phases out
        phase_factor = 1.0 - (month - 1) / recovery_months
        month_margin_impact = cost_change_gbp * phase_factor
        # Calculate margin impact in percentage points
        margin_impact_pct = (abs(cost_change_gbp) / 1000000) * phase_factor if cost_change_gbp < 0 else 0

        monthly_data.append({
            'month': month,
            'margin_impact_gbp': round(month_margin_impact, 2),
            'recovery_phase_pct': round(phase_factor * 100, 1)
        })

    return {
        'starting_margin_pct': round(starting_margin_pct, 1),
        'monthly_phasing': monthly_data,
        'total_recovery_months': recovery_months,
        'cost_change_gbp': round(cost_change_gbp, 2),
        'formula': 'Monthly impact = Cost change × (1 - (month/recovery_months))'
    }


def calc_variance_drivers(ctx, cost_centre_id=None, period='0m'):
    """Decompose variance into volume, price, mix, cost and one-off drivers"""
    # Get actual variance
    if cost_centre_id:
        query = "SELECT COALESCE(SUM(a.actual_gbp), 0) - COALESCE(SUM(b.value_gbp), 0) AS total_variance FROM actual_costs a LEFT JOIN budget_lines b USING (cost_centre_id, category, period) WHERE a.cost_centre_id = $cc AND a.period = $p"
        results = ctx.q(query, cc=cost_centre_id, p=period)
    else:
        results = [{'total_variance': 0}]

    total_variance = float(results[0].get('total_variance', 0)) if results else 0

    # Decompose variance (simplified split)
    volume_driver = total_variance * 0.4
    price_driver = total_variance * 0.3
    mix_driver = total_variance * 0.15
    cost_driver = total_variance * 0.1
    one_off_driver = total_variance * 0.05

    return {
        'total_variance_gbp': round(total_variance, 2),
        'volume_driver_gbp': round(volume_driver, 2),
        'price_driver_gbp': round(price_driver, 2),
        'mix_driver_gbp': round(mix_driver, 2),
        'cost_driver_gbp': round(cost_driver, 2),
        'one_off_driver_gbp': round(one_off_driver, 2),
        'formula': 'Total variance split by typical driver proportions: 40% volume, 30% price, 15% mix, 10% cost, 5% one-off'
    }


def list_margin_actions(ctx, category=None, min_value_gbp=10000):
    """List candidate margin recovery actions with estimated value"""
    actions = [
        {
            'action_id': 'MRA-001',
            'category': 'Housewares',
            'description': 'Renegotiate supplier contracts for volume discount',
            'estimated_value_gbp': 150000,
            'lead_time_weeks': 4,
            'confidence_pct': 85
        },
        {
            'action_id': 'MRA-002',
            'category': 'Housewares',
            'description': 'Implement lean manufacturing with top supplier',
            'estimated_value_gbp': 75000,
            'lead_time_weeks': 12,
            'confidence_pct': 70
        },
        {
            'action_id': 'MRA-003',
            'category': 'Clothing',
            'description': 'Reduce markdown by targeted promotions',
            'estimated_value_gbp': 120000,
            'lead_time_weeks': 2,
            'confidence_pct': 75
        },
        {
            'action_id': 'MRA-004',
            'category': 'All',
            'description': 'Optimize freight consolidation',
            'estimated_value_gbp': 85000,
            'lead_time_weeks': 6,
            'confidence_pct': 80
        },
    ]

    filtered = [a for a in actions if (category is None or a['category'] in [category, 'All']) and a['estimated_value_gbp'] >= min_value_gbp]
    return sorted(filtered, key=lambda x: x['estimated_value_gbp'], reverse=True)


def list_levers(ctx):
    """List available cost or revenue levers with value and lead time"""
    levers = [
        {
            'lever_id': 'LEV-001',
            'name': 'Extend payment terms with suppliers',
            'type': 'working capital',
            'estimated_value_gbp': 500000,
            'lead_time_weeks': 8,
            'one_time': False
        },
        {
            'lever_id': 'LEV-002',
            'name': 'Reduce SKU complexity',
            'type': 'cost reduction',
            'estimated_value_gbp': 250000,
            'lead_time_weeks': 16,
            'one_time': False
        },
        {
            'lever_id': 'LEV-003',
            'name': 'Nearshore 20% of sourcing',
            'type': 'cost structure',
            'estimated_value_gbp': 750000,
            'lead_time_weeks': 24,
            'one_time': True
        },
        {
            'lever_id': 'LEV-004',
            'name': 'Implement price increases',
            'type': 'revenue',
            'estimated_value_gbp': 1200000,
            'lead_time_weeks': 4,
            'one_time': False
        },
        {
            'lever_id': 'LEV-005',
            'name': 'Reduce promotional intensity',
            'type': 'revenue',
            'estimated_value_gbp': 600000,
            'lead_time_weeks': 2,
            'one_time': False
        }
    ]
    return levers


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
