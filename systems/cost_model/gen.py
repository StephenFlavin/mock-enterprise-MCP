"""Generate cost model data: should-costs, cost reduction options, labour rates, and investment cases."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng

    # Get master data
    products = g.master("products")
    suppliers = g.master("suppliers")
    assets = g.master("assets")
    sites = g.master("sites")

    should_costs = []
    cost_reduction_options = []
    control_option_costs = []
    lifecycle_scenarios = []
    labour_rates = []
    quote_components = []
    cost_benchmarks = []
    investment_cases = []
    make_vs_buy = []

    # Generate should-costs for a sample of products
    # Focus on products mentioned in brief: K-1700 (kettle), PF-220 (portable fan)
    products_subset = [p for p in products if p["sku"] in ["K-1700", "PF-220"] or r.random() < 0.05][:15]

    for idx, prod in enumerate(products_subset):
        sku = prod["sku"]
        style_id = prod["style_id"]
        volume = r.choice([5000, 10000, 25000, 50000])

        # Generate cost breakdown
        material = round(r.uniform(0.5, 3.0), 2)  # GBP per unit
        labour = round(r.uniform(0.3, 1.5), 2)
        overhead = round(material * r.uniform(0.15, 0.35), 2)
        freight = round(r.uniform(0.1, 0.8), 2)
        tooling = round(r.uniform(0.05, 0.3), 2)
        margin = round((material + labour + overhead + freight + tooling) * r.uniform(0.10, 0.25), 2)
        total = material + labour + overhead + freight + tooling + margin

        region = r.choice(["Vietnam", "Bangladesh", "Turkey", "UK"])

        cost_id = f"SC-{idx:06d}"
        should_costs.append({
            "cost_id": cost_id,
            "sku": sku,
            "style_id": style_id,
            "volume_units": volume,
            "material_gbp": material,
            "labour_gbp": labour,
            "overhead_gbp": overhead,
            "freight_gbp": freight,
            "tooling_per_unit_gbp": tooling,
            "margin_gbp": margin,
            "total_gbp": total,
            "region": region,
            "notes": f"Benchmark: {volume} units, {region}",
            "created_at": g.as_of - timedelta(days=r.randint(1, 90))
        })

        # Generate cost reduction options for this SKU
        option_categories = ["material", "labour", "design", "packaging"]
        for opt_idx in range(r.randint(2, 4)):
            category = r.choice(option_categories)
            if category == "material":
                saving = round(r.uniform(0.10, 0.40), 2)
                title = f"Use lower-grade {r.choice(['material', 'component', 'plastic'])}"
            elif category == "labour":
                saving = round(r.uniform(0.05, 0.25), 2)
                title = f"Simplify {r.choice(['assembly', 'finishing', 'packaging'])} process"
            elif category == "design":
                saving = round(r.uniform(0.15, 0.50), 2)
                title = f"Reduce {r.choice(['number of components', 'finish complexity', 'weight'])}"
            else:
                saving = round(r.uniform(0.05, 0.20), 2)
                title = f"Change {r.choice(['packaging format', 'carton type', 'label finish'])}"

            saving_pct = round(saving / total * 100, 1)
            impl_cost = r.choice([0, r.randint(500, 5000)])
            customer_impact = r.choice(["none", "minor", "moderate"] + ["none"] * 2)  # Weight toward "none"

            cro_id = f"CRO-{len(cost_reduction_options):06d}"
            cost_reduction_options.append({
                "option_id": cro_id,
                "sku": sku,
                "title": title,
                "description": f"{title} could reduce unit cost by £{saving:.2f}",
                "saving_gbp_per_unit": saving,
                "saving_pct": saving_pct,
                "implementation_cost_gbp": impl_cost,
                "customer_impact": customer_impact,
                "status": r.choice(["proposed", "tested", "approved"]),
                "category": category
            })

    # Generate labour rates by country
    countries = [("VN", "Vietnam"), ("BD", "Bangladesh"), ("TR", "Turkey"), ("GB", "UK")]
    roles = ["sewing", "assembly", "finishing", "inspection", "supervision"]
    lr_idx = 0
    for country_code, country_name in countries:
        for role in roles:
            # Base rates vary by country and role
            if country_code == "GB":
                base_rate = r.uniform(12, 18)
            elif country_code == "TR":
                base_rate = r.uniform(4, 6)
            elif country_code == "BD":
                base_rate = r.uniform(1.5, 2.5)
            else:  # VN
                base_rate = r.uniform(2, 3.5)

            # Role multipliers
            if role == "supervision":
                multiplier = 1.8
            elif role == "inspection":
                multiplier = 1.3
            else:
                multiplier = 1.0

            hourly_rate = round(base_rate * multiplier, 2)

            labour_rates.append({
                "rate_id": f"LR-{lr_idx:06d}",
                "country": country_code,
                "role": role,
                "hourly_gbp": hourly_rate,
                "annual_hours": 1800,
                "trend_pct_annual": round(r.uniform(2, 6), 1),
                "date_from": g.as_of - timedelta(days=90),
                "date_to": g.as_of + timedelta(days=270)
            })
            lr_idx += 1

    # Generate control option costs (safety controls)
    control_types = ["pedestrian_exclusion", "proximity_sensor", "speed_limiter"]
    for idx, control_type in enumerate(control_types):
        # Costs vary by site size
        for size_sqft in [100000, 150000, 200000]:
            if control_type == "pedestrian_exclusion":
                capex = round(size_sqft * 0.08, 0)  # ~£8k-16k
                opex = round(capex * 0.08, 0)  # 8% of capex annually
                weeks = r.randint(4, 8)
                reduction_pct = r.uniform(40, 60)
            elif control_type == "proximity_sensor":
                capex = round(size_sqft * 0.05, 0)  # ~£5k-10k
                opex = round(capex * 0.12, 0)  # 12% opex
                weeks = r.randint(2, 4)
                reduction_pct = r.uniform(50, 70)
            else:  # speed_limiter
                capex = round(size_sqft * 0.03, 0)  # ~£3k-6k
                opex = round(capex * 0.10, 0)  # 10% opex
                weeks = r.randint(1, 3)
                reduction_pct = r.uniform(30, 50)

            control_option_costs.append({
                "control_id": f"CTL-{len(control_option_costs):06d}",
                "control_type": control_type,
                "site_size_sqft": size_sqft,
                "capex_gbp": capex,
                "annual_opex_gbp": opex,
                "installation_weeks": weeks,
                "incident_reduction_pct": round(reduction_pct, 1),
                "notes": f"Estimated for {control_type} at {size_sqft} sqft"
            })

    # Generate lifecycle cost scenarios for some assets
    dc_assets = [a for a in assets if a["site_id"].startswith("DC")][:5]
    for asset in dc_assets:
        asset_id = asset["asset_id"]
        # Three options: repair, overhaul, replace

        # Repair option
        lifecycle_scenarios.append({
            "scenario_id": f"LCS-{len(lifecycle_scenarios):06d}",
            "asset_id": asset_id,
            "option_type": "repair",
            "capex_gbp": 0,
            "annual_maintenance_gbp": round(r.uniform(500, 2000), 0),
            "expected_life_years": r.randint(2, 4),
            "downtime_risk_high_pct": r.uniform(30, 50),
            "residual_value_gbp": 0,
            "notes": "Continue with reactive/preventive maintenance"
        })

        # Overhaul option
        lifecycle_scenarios.append({
            "scenario_id": f"LCS-{len(lifecycle_scenarios):06d}",
            "asset_id": asset_id,
            "option_type": "overhaul",
            "capex_gbp": round(r.uniform(5000, 20000), 0),
            "annual_maintenance_gbp": round(r.uniform(300, 800), 0),
            "expected_life_years": r.randint(5, 7),
            "downtime_risk_high_pct": r.uniform(15, 30),
            "residual_value_gbp": round(r.uniform(1000, 5000), 0),
            "notes": "Major overhaul extends life and reduces downtime risk"
        })

        # Replace option
        lifecycle_scenarios.append({
            "scenario_id": f"LCS-{len(lifecycle_scenarios):06d}",
            "asset_id": asset_id,
            "option_type": "replace",
            "capex_gbp": round(float(asset.get("replacement_cost_gbp", 30000)), 0),
            "annual_maintenance_gbp": round(r.uniform(200, 600), 0),
            "expected_life_years": r.randint(7, 10),
            "downtime_risk_high_pct": r.uniform(5, 15),
            "residual_value_gbp": round(float(asset.get("replacement_cost_gbp", 30000)) * 0.1, 0),
            "notes": "New equipment with warranty and lower maintenance"
        })

    # Generate quote components for products (K-1700 specifically for brief)
    # Find K-1700 and create quotes from different suppliers
    k1700 = next((p for p in products if p["sku"] == "K-1700"), None)
    if k1700:
        sku = k1700["sku"]
        suppliers_sample = suppliers[:3]  # Use first 3 suppliers

        # Create benchmark and quote data
        benchmark_data = {
            "material": {"bp": 1.20, "low": 1.00, "high": 1.40},
            "labour": {"bp": 0.35, "low": 0.30, "high": 0.45},
            "overhead": {"bp": 0.25, "low": 0.20, "high": 0.35},
            "freight": {"bp": 0.15, "low": 0.10, "high": 0.25},
            "margin": {"bp": 0.30, "low": 0.25, "high": 0.40}
        }

        for comp_type, benchmarks in benchmark_data.items():
            for idx, supplier in enumerate(suppliers_sample):
                supplier_id = supplier["supplier_id"]

                # Generate quote that varies from benchmark
                variance_direction = r.choice([-1, 1])
                if variance_direction > 0:
                    variance_pct = round(r.uniform(0, 25), 1)
                else:
                    variance_pct = round(r.uniform(-15, 0), 1)

                quote_cost = benchmarks["bp"] * (1 + variance_pct / 100)

                quote_components.append({
                    "quote_line_id": f"QL-{len(quote_components):06d}",
                    "sku": sku,
                    "supplier_id": supplier_id,
                    "component_type": comp_type,
                    "component_desc": f"{comp_type.capitalize()} for 750ml bottle",
                    "cost_gbp_per_unit": round(quote_cost, 2),
                    "volume_units": 50000,
                    "benchmark_gbp_per_unit": benchmarks["bp"],
                    "variance_pct": variance_pct,
                    "comments": f"Quote dated {(g.as_of - timedelta(days=r.randint(7, 60))).strftime('%Y-%m-%d')}"
                })

        # Add benchmark records
        for comp_type, benchmarks in benchmark_data.items():
            cost_benchmarks.append({
                "benchmark_id": f"BM-{len(cost_benchmarks):06d}",
                "component_type": comp_type,
                "product_category": "Homeware",
                "region": "China",
                "description": f"{comp_type.capitalize()} cost for stainless steel bottles",
                "benchmark_gbp_per_unit": benchmarks["bp"],
                "low_gbp_per_unit": benchmarks["low"],
                "high_gbp_per_unit": benchmarks["high"],
                "source": "Market benchmark",
                "date_from": g.as_of - timedelta(days=90)
            })

    # Generate investment cases
    investment_cases.append({
        "case_id": "INV-900001",
        "title": "Nearshoring initiative",
        "description": "Move portion of sourcing from Asia to Turkey/Eastern Europe",
        "capex_gbp": 2500000,
        "annual_benefit_gbp": 800000,
        "implementation_years": 2.0,
        "evaluation_years": 5,
        "discount_rate_pct": 10.0,
        "tax_rate_pct": 19.0,
        "npv_gbp": 1850000,
        "irr_pct": 28.5,
        "payback_years": 3.2,
        "sensitivity_upside_pct": 20,
        "sensitivity_downside_pct": -15,
        "risk_rating": "medium",
        "dependencies": "Supplier capacity; tariff environment"
    })

    investment_cases.append({
        "case_id": "INV-900002",
        "title": "DC automation",
        "description": "Introduce sorter system at Northampton DC",
        "capex_gbp": 8500000,
        "annual_benefit_gbp": 1200000,
        "implementation_years": 1.5,
        "evaluation_years": 7,
        "discount_rate_pct": 10.0,
        "tax_rate_pct": 19.0,
        "npv_gbp": 3200000,
        "irr_pct": 15.2,
        "payback_years": 7.1,
        "sensitivity_upside_pct": 15,
        "sensitivity_downside_pct": -20,
        "risk_rating": "high",
        "dependencies": "Space availability; integration with existing systems"
    })

    # Generate make vs buy scenarios (seed data provides the story data)

    return {
        "should_costs": should_costs,
        "cost_reduction_options": cost_reduction_options,
        "control_option_costs": control_option_costs,
        "lifecycle_scenarios": lifecycle_scenarios,
        "labour_rates": labour_rates,
        "quote_components": quote_components,
        "cost_benchmarks": cost_benchmarks,
        "investment_cases": investment_cases,
        "make_vs_buy": make_vs_buy
    }
