def generate(g):
    """Generate S&OP platform data with realistic scenarios, assumptions, and financial impacts."""

    scenarios = []
    assumptions = []
    changes = []
    runs = []
    baselines = []
    launches = []
    external_assumptions = []
    disputed = []

    # Generate baseline data for multiple S&OP cycles
    cycles = ["SOP-202608", "SOP-202609", "SOP-202610"]
    periods = {
        "SOP-202608": "Q3 2026",
        "SOP-202609": "Q3 2026",
        "SOP-202610": "Q4 2026"
    }

    employees = g.master("employees")
    emp_ids = [e["employee_id"] for e in employees[:20]]

    # Create baseline plans for each cycle
    for i, cycle in enumerate(cycles):
        baseline_id = f"SOP-B-{i+1:06d}"
        period = periods[cycle]

        # Revenue and margin vary slightly by cycle
        base_revenue = 45000000 + (i * 500000)  # 45-46.5M GBP
        base_margin = 32 + (i * 0.5)  # 32-33%
        base_cash = base_revenue * (base_margin / 100) * 0.6  # Assuming 60% cash conversion

        baselines.append({
            "baseline_id": baseline_id,
            "sop_cycle": cycle,
            "forecast_period": period,
            "revenue_gbp": round(base_revenue, 0),
            "margin_pct": round(base_margin, 1),
            "cash_flow_gbp": round(base_cash, 0),
            "service_level_pct": 94.5,
            "inventory_units": 2800000,
            "promotional_intensity_pct": 18.5,
            "demand_assumption": "Modest growth 2% YoY, normal seasonality",
            "supply_assumption": "Normal lead times, all suppliers on track",
            "created_at": g.date_between(100 - i * 7, 70 - i * 7),
        })

    # Create scenarios for current cycle (2026-10)
    current_cycle = "SOP-202610"
    scenario_configs = [
        {"type": "baseline", "name": "Hold Current Plan", "desc": "Continue current execution plan", "revenue_adj": 0, "margin_adj": 0, "cash_adj": 0},
        {"type": "upside", "name": "Strong Holiday Demand", "desc": "Consumer confidence holds, promotional lift works", "revenue_adj": 6, "margin_adj": 1.5, "cash_adj": 8},
        {"type": "downside", "name": "Cost-of-Living Squeeze", "desc": "Demand down 5%, promotional intensity up 8 pts", "revenue_adj": -5, "margin_adj": -1.8, "cash_adj": -12},
        {"type": "test", "name": "Lift Stock +10%", "desc": "Hold stock on key lines to protect service", "revenue_adj": 0, "margin_adj": -0.5, "cash_adj": -3},
    ]

    for idx, cfg in enumerate(scenario_configs):
        scenario_id = f"SOP-S-{900001 + idx}"
        scenarios.append({
            "scenario_id": scenario_id,
            "name": cfg["name"],
            "sop_cycle": current_cycle,
            "scenario_type": cfg["type"],
            "created_by": g.pick(emp_ids),
            "created_at": g.date_between(28, 21),
            "description": cfg["desc"],
            "status": "approved" if cfg["type"] == "baseline" else "submitted",
            "updated_at": g.date_between(14, 7),
        })

        # Create a scenario run for each scenario
        run_id = f"SOP-R-{900001 + idx}"
        base_revenue = 45500000
        base_margin = 32.5
        base_cash = base_revenue * (base_margin / 100) * 0.6

        scenario_revenue = base_revenue * (1 + cfg["revenue_adj"] / 100)
        scenario_margin = base_margin + cfg["margin_adj"]
        scenario_cash = scenario_revenue * (scenario_margin / 100) * 0.6 * (1 + cfg["cash_adj"] / 100)

        risks = []
        if cfg["type"] == "downside":
            risks = ["high consumer pressure", "promotional intensity +8pts"]
        elif cfg["type"] == "upside":
            risks = ["holiday shopping uncertain"]
        else:
            risks = ["normal execution risk"]

        runs.append({
            "run_id": run_id,
            "scenario_id": scenario_id,
            "sop_cycle": current_cycle,
            "run_date": g.date_between(14, 7),
            "forecast_period": "Q4 2026",
            "base_revenue_gbp": round(base_revenue, 0),
            "scenario_revenue_gbp": round(scenario_revenue, 0),
            "scenario_revenue_variance_pct": round(cfg["revenue_adj"], 1),
            "base_margin_pct": round(base_margin, 1),
            "scenario_margin_pct": round(scenario_margin, 1),
            "scenario_margin_variance_pct": round(cfg["margin_adj"], 1),
            "scenario_cash_flow_gbp": round(scenario_cash, 0),
            "service_level_pct": 94.5 + (cfg["revenue_adj"] * 0.2),  # Lower demand -> better service
            "inventory_units": 2800000 + (cfg["cash_adj"] * 50000),
            "inventory_value_gbp": (2800000 + (cfg["cash_adj"] * 50000)) * 12,
            "key_risks": "; ".join(risks),
            "mitigation_actions": "Weekly sync with supply chain" if cfg["type"] == "downside" else "Standard review cycle",
            "trigger_for_switch": "If weekly sales fall 3% below trend" if cfg["type"] == "downside" else "Watch consumer confidence indices",
            "created_at": g.date_between(14, 7),
        })

    # Create assumptions for each scenario
    assumption_categories = ["demand", "supply", "finance", "macro", "channel"]

    for scenario_idx, scenario in enumerate(scenarios):
        # 5-8 assumptions per scenario
        num_assumptions = g.rng.randint(5, 8)
        for ass_idx in range(num_assumptions):
            assumption_id = f"SOP-A-{900000 + scenario_idx * 100 + ass_idx + 1}"
            category = assumption_categories[g.rng.randint(0, len(assumption_categories)-1)]

            is_disputed = scenario["scenario_type"] == "downside" and ass_idx == 0  # First downside assumption disputed

            assumptions.append({
                "assumption_id": assumption_id,
                "scenario_id": scenario["scenario_id"],
                "category": category,
                "description": f"{category.title()} assumption for {scenario['name']}",
                "assumption_value": f"See scenario {scenario['scenario_id']}",
                "basis": f"Based on Q3 actuals and market trends",
                "is_disputed": is_disputed,
                "dispute_reason": "Demand elasticity overstated" if is_disputed else "",
                "owner_id": g.pick(emp_ids),
                "created_at": scenario["created_at"],
            })

            if is_disputed:
                dispute_id = f"SOP-D-{900000 + scenario_idx}"
                disputed.append({
                    "dispute_id": dispute_id,
                    "assumption_id": assumption_id,
                    "sop_cycle": current_cycle,
                    "raised_by": g.pick(emp_ids),
                    "reason": "Elasticity assumption needs revision based on H1 promotional response",
                    "alternative_value": "Demand down 3% instead of 5%",
                    "raised_at": g.date_between(10, 5),
                    "resolution": "To be discussed at S&OP exec meeting",
                    "resolved_at": "",
                })

    # Generate assumption changes between cycles
    change_categories = ["demand", "supply", "finance", "macro"]
    for cycle_idx in range(1, len(cycles)):
        num_changes = g.rng.randint(4, 8)
        for ch_idx in range(num_changes):
            change_id = f"SOP-C-{900000 + cycle_idx * 100 + ch_idx}"
            category = change_categories[g.rng.randint(0, len(change_categories)-1)]

            revenue_impact = g.rng.uniform(-2000000, 2000000)

            changes.append({
                "change_id": change_id,
                "sop_cycle": cycles[cycle_idx],
                "prior_cycle": cycles[cycle_idx - 1],
                "category": category,
                "description": f"{category.title()} assumption updated",
                "prior_assumption": "From previous cycle",
                "new_assumption": "Updated based on recent actuals",
                "owner_id": g.pick(emp_ids),
                "reason": f"{category} data from last 4 weeks shows new trend",
                "revenue_impact_gbp": round(revenue_impact, 0),
                "inventory_impact_units": g.rng.randint(-200000, 200000),
                "changed_at": g.date_between(70 - cycle_idx * 7, 60 - cycle_idx * 7),
            })

    # Generate new product launches
    products = g.master("products")[:30]
    for launch_idx in range(8):
        launch_id = f"SOP-L-{900001 + launch_idx}"
        product = g.pick(products)

        assumed_demand = g.rng.randint(100000, 500000)
        actual_demand = int(assumed_demand * g.rng.uniform(0.7, 1.3))
        accuracy = round((actual_demand / assumed_demand) * 100, 1)

        launches.append({
            "launch_id": launch_id,
            "sop_cycle": "SOP-202609",
            "sku": product["sku"],
            "style_id": product["style_id"],
            "launch_date": g.date_between(90, 30),
            "demand_assumption_units": assumed_demand,
            "actual_demand_units": actual_demand,
            "demand_assumption_accuracy_pct": accuracy,
            "timing_assumption_days": 21,
            "actual_timing_days": g.rng.randint(14, 28),
            "distribution_assumption_pct": 85,
            "actual_distribution_pct": g.rng.uniform(75, 95),
            "retail_price_gbp": float(product.get("retail_price_gbp", 25)),
            "notes": "High street channels gained share vs. expected" if accuracy > 110 else "Slower ramp than expected",
        })

    # Generate external macro assumptions
    macro_topics = [
        ("gdp_growth", "UK GDP growth", "Expected 1.5% growth", "Office for National Statistics", "medium"),
        ("inflation", "Inflation forecast", "Expected 2.8% YoY", "Bank of England", "high"),
        ("consumer_confidence", "Consumer confidence index", "Expected +5% vs Q2", "GfK Consumer Confidence", "medium"),
        ("employment", "Employment rate", "Expected 4.2%", "ONS Labour Force Survey", "high"),
        ("interest_rate", "Bank of England base rate", "Expected 4.5% by year-end", "BoE MPC guidance", "high"),
        ("competitor_action", "Competitor pricing activity", "High street competitors cutting 5-10%", "Retail analyst consensus", "low"),
        ("supply_disruption", "Supply chain disruption risk", "Asia capacity tight Q4", "Supplier feedback", "medium"),
    ]

    for idx, (category, desc, value, source, confidence) in enumerate(macro_topics):
        ext_id = f"SOP-E-{900001 + idx}"
        external_assumptions.append({
            "ext_assumption_id": ext_id,
            "sop_cycle": current_cycle,
            "category": category,
            "description": desc,
            "assumed_value": value,
            "source": source,
            "confidence_level": confidence,
            "impact_on_demand": f"Affects {category} elasticity" if category != "supply_disruption" else "May limit fulfillment capability",
            "impact_on_supply": "May increase lead times" if category == "supply_disruption" else "Minimal direct impact",
            "news_exposure_date": g.date_between(30, 3),
            "already_in_forecast": g.rng.choice([True, False]),
            "created_at": g.date_between(21, 14),
        })

    return {
        "sop_scenarios": scenarios,
        "sop_scenario_assumptions": assumptions,
        "assumption_changes": changes,
        "scenario_runs": runs,
        "plan_baseline": baselines,
        "new_product_launches": launches,
        "external_assumptions": external_assumptions,
        "disputed_assumptions": disputed,
    }
