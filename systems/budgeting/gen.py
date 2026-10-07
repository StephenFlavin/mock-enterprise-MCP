"""Generate budgeting data: budget lines, actuals, forecasts, scenarios, programmes, investment cases."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    fake = g.fake
    as_of = g.as_of

    # Cost centres from master
    cost_centres = g.master("cost_centres")

    budget_lines = []
    actual_costs = []
    forecast_versions = []
    forecast_scenarios = []
    margin_plans = []
    programmes = []
    programme_costs = []
    investment_cases = []
    forecast_actuals = []

    # Generate budget lines and actuals for last 6 months + current month
    categories = ['air freight', 'road transport', 'staff', 'utilities', 'systems', 'packaging']

    # Get unique month periods from last 26 weeks
    seen_periods = set()
    for period_date in g.weeks(26):
        period_str = period_date.strftime('%Y-%m')
        seen_periods.add(period_str)

    periods = sorted(list(seen_periods))

    # Track generated actual costs to avoid duplicates
    actual_costs_keys = set()

    for period_str in periods:
        for cc in cost_centres[:20]:  # Sample of cost centres
            cc_id = cc['cost_centre_id']
            for category in categories:
                # Budget line
                base_budget = r.choice([10000, 25000, 50000, 75000, 100000, 150000])
                bl_id = f"BL-{len(budget_lines) + 1:06d}"
                budget_lines.append({
                    'budget_line_id': bl_id,
                    'cost_centre_id': cc_id,
                    'category': category,
                    'period': period_str,
                    'value_gbp': base_budget,
                    'notes': f"{category} for {cc_id}",
                    'updated_at': as_of - timedelta(days=30)
                })

                # Actual costs (75% of periods have actuals)
                key = (cc_id, category, period_str)
                if key not in actual_costs_keys and r.random() < 0.75:
                    actual = base_budget * r.gauss(1.0, 0.15)  # ±15% variance
                    one_off = actual * r.choice([0, 0, 0, 0.1, 0.2, 0.3])  # Some have one-off component
                    actual_costs.append({
                        'cost_centre_id': cc_id,
                        'category': category,
                        'period': period_str,
                        'actual_gbp': round(actual, 2),
                        'one_off_gbp': round(one_off, 2),
                        'updated_at': as_of - timedelta(days=25)
                    })
                    actual_costs_keys.add(key)

    # Generate forecast versions and scenarios
    base_scenarios = [
        {'name': 'Base', 'desc': 'Base case forecast with current trends'},
        {'name': 'Downside', 'desc': 'Demand down 5%, freight up 20%'},
        {'name': 'Upside', 'desc': 'Demand up 3%, freight flat'},
    ]

    for i, scenario_data in enumerate(base_scenarios):
        scenario_id = f"FSC-{i + 1:06d}"
        forecast_scenarios.append({
            'scenario_id': scenario_id,
            'name': scenario_data['name'],
            'description': scenario_data['desc'],
            'created_date': as_of - timedelta(days=7 * i),
            'created_by': 'EMP-00001',
            'assumptions': f"Volume: {r.choice(['-5%', 'flat', '+3%'])}; Freight: {r.choice(['+20%', 'flat', '-5%'])}; FX GBP/USD: 1.27",
            'status': 'active' if i < 2 else 'archived'
        })

        # Forecast version for this scenario
        revenue = 50000000 + r.gauss(0, 5000000)
        margin_pct = 35 + r.gauss(0, 2)
        fcst_id = f"FCST-{as_of.strftime('%Y-%m')}-{i + 1:03d}"
        forecast_versions.append({
            'forecast_version_id': fcst_id,
            'forecast_date': as_of,
            'scenario_id': scenario_id,
            'revenue_forecast_gbp': round(revenue, 2),
            'gross_margin_pct': round(margin_pct, 1),
            'ebit_forecast_gbp': round((revenue * margin_pct / 100) - 10000000, 2),
            'notes': f"Forecast for {scenario_data['name'].lower()} scenario",
            'status': 'current' if i == 0 else 'superseded',
            'created_at': as_of - timedelta(days=i)
        })

        # Margin plans by category
        for category in ['Housewares', 'Womenswear', 'Menswear', 'Kidswear']:
            base_margin = r.choice([35.0, 38.0, 40.0, 42.0])
            margin_plans.append({
                'scenario_id': scenario_id,
                'category': category,
                'planned_margin_pct': round(base_margin + i - 1, 1),
                'inflation_assumption_pct': 2.5,
                'fx_assumption': 'GBP/USD 1.27',
                'tariff_impact_pct': 1.0 + i,
                'notes': f"Margin plan for {category} under {scenario_data['name']}",
                'updated_at': as_of - timedelta(days=i)
            })

    # Generate programmes
    programme_types = ['cost_saving', 'revenue', 'capex', 'transformation']
    for i in range(8):
        prog_id = f"PGM-{i + 1:06d}"
        ptype = programme_types[i % len(programme_types)]
        budget = r.choice([500000, 1000000, 2000000, 5000000])
        programmes.append({
            'programme_id': prog_id,
            'name': r.choice(['Margin Recovery', 'Shrink Reduction', 'DC Automation', 'ERP Go-Live', 'Nearshoring Pilot', 'Omnichannel', 'Analytics Platform', 'Logistics Optimization']),
            'description': 'Key strategic initiative',
            'budget_gbp': budget,
            'start_date': as_of - timedelta(days=r.randint(30, 180)),
            'end_date': as_of + timedelta(days=r.randint(30, 365)),
            'status': r.choice(['approved', 'in_progress', 'completed']),
            'type': ptype
        })

        # Programme costs by period (track keys to avoid duplicates)
        prog_cost_keys = set()
        for week in g.weeks(24):
            period_str = week.strftime('%Y-%m')
            key = (prog_id, period_str)
            if key not in prog_cost_keys:
                forecast = budget / 24 * r.gauss(1.0, 0.2)
                actual = forecast * r.gauss(1.0, 0.15) if week < as_of else 0
                programme_costs.append({
                    'programme_id': prog_id,
                    'period': period_str,
                    'forecast_gbp': round(forecast, 2),
                    'actual_gbp': round(max(0, actual), 2),
                    'burn_rate_pct': round(actual / forecast * 100 if forecast > 0 else 0, 1),
                    'updated_at': as_of - timedelta(days=5)
                })
                prog_cost_keys.add(key)

    # Generate investment cases
    for i in range(10):
        inv_id = f"INV-{i + 1:06d}"
        capex = r.choice([500000, 1000000, 2000000, 5000000, 10000000])
        annual_saving = capex * r.uniform(0.15, 0.30)
        payback = capex / annual_saving if annual_saving > 0 else 999

        investment_cases.append({
            'investment_case_id': inv_id,
            'title': r.choice(['DC Automation', 'Northampton Refurbishment', 'Nearshoring Expansion', 'E-commerce Platform', 'Warehouse Robotics', 'Analytics Platform', 'Logistics System', 'Store Refit Program']),
            'description': 'Capital investment opportunity',
            'site_id': r.choice(['DC1', 'DC2', 'DC3', 'ST001', 'ST214']),
            'capex_gbp': capex,
            'annual_saving_gbp': round(annual_saving, 2),
            'annual_revenue_gbp': r.choice([0, 500000, 1000000, 2000000]),
            'payback_period_months': round(payback * 12, 1),
            'npv_gbp': round(capex / payback * 5 - capex, 2),  # Simple NPV proxy
            'irr_pct': round((annual_saving / capex) * 100, 1),
            'status': r.choice(['proposal', 'approved', 'implemented']),
            'created_date': as_of - timedelta(days=r.randint(30, 180)),
            'assumptions': 'Conservative: 10% discount rate, 5-year horizon'
        })

    # Generate forecast actuals for comparison
    line_items = ['revenue', 'cogs', 'gross_profit', 'air_freight', 'road_freight', 'margin_pct', 'ebit']
    for fcst in forecast_versions[:2]:  # For current and previous forecast only
        for period in ['2026-Q3', '2026-09', '2026-08']:
            for line in line_items:
                if line == 'revenue':
                    forecast_val = 12500000
                    actual_val = 12250000 + r.gauss(0, 500000)
                elif line == 'cogs':
                    forecast_val = 8125000
                    actual_val = 8200000 + r.gauss(0, 300000)
                elif line == 'gross_profit':
                    forecast_val = 4375000
                    actual_val = 4050000 + r.gauss(0, 300000)
                elif line == 'air_freight':
                    forecast_val = 125000
                    actual_val = 145000 + r.gauss(0, 20000)
                elif line == 'road_freight':
                    forecast_val = 312000
                    actual_val = 320000 + r.gauss(0, 30000)
                elif line == 'margin_pct':
                    forecast_val = 35.0
                    actual_val = 33.0 + r.gauss(0, 1.5)
                else:  # ebit
                    forecast_val = 2187500
                    actual_val = 2025000 + r.gauss(0, 250000)

                variance = actual_val - forecast_val
                variance_pct = (variance / forecast_val * 100) if forecast_val != 0 else 0

                forecast_actuals.append({
                    'forecast_version_id': fcst['forecast_version_id'],
                    'period': period,
                    'line_item': line,
                    'forecast_value_gbp': round(forecast_val, 2),
                    'actual_value_gbp': round(actual_val, 2),
                    'variance_gbp': round(variance, 2),
                    'variance_pct': round(variance_pct, 1)
                })

    return {
        'budget_lines': budget_lines,
        'actual_costs': actual_costs,
        'forecast_versions': forecast_versions,
        'forecast_scenarios': forecast_scenarios,
        'margin_plans': margin_plans,
        'programmes': programmes,
        'programme_costs': programme_costs,
        'investment_cases': investment_cases,
        'forecast_actuals': forecast_actuals
    }
