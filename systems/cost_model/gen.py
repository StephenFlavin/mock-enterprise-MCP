"""Generate cost model background data: should-costs and options for random products, lifecycle options for DC
sorters and conveyors, and a few supplier quotes. Story rows (bottle, padded jacket, coat, K-1700, DC1 sorter,
labour rates, safety controls, investment and make-vs-buy cases) come from seed/*.csv."""
from datetime import timedelta

STORY_SKUS = {"K-1700", "PF-220", "SKU-106307", "SKU-103157", "SKU-102863"}
STORY_STYLES = {"STY-K-1700", "STY-PF-220", "STY-9501", "STY-7731"}
STORY_ASSETS = {"AST-DC1-SRT"}
REGIONS = {"CN": "China", "VN": "Vietnam", "BD": "Bangladesh", "TR": "Turkey", "PT": "Portugal", "IN": "India",
           "GB": "UK", "PK": "Pakistan", "MA": "Morocco"}


def generate(g):
    r = g.rng
    products = [p for p in g.master("products")
                if p["sku"] not in STORY_SKUS and p["style_id"] not in STORY_STYLES and p["status"] == "active"
                and float(p["unit_cost_gbp"] or 0) >= 8]
    suppliers = {s["supplier_id"]: s for s in g.master("suppliers")}
    assets = g.master("assets")

    should_costs, options, quotes = [], [], []
    chosen = r.sample(products, 14)
    for idx, prod in enumerate(chosen, start=1):
        unit_cost = float(prod["unit_cost_gbp"])
        total = round(unit_cost * r.uniform(0.9, 1.0), 2)
        share = {"material": r.uniform(0.52, 0.62), "labour": r.uniform(0.12, 0.18), "overhead": r.uniform(0.06, 0.09),
                 "freight": r.uniform(0.05, 0.09), "tooling": r.uniform(0.01, 0.03)}
        margin_share = r.uniform(0.08, 0.12)
        norm = sum(share.values()) + margin_share
        parts = {k: round(total * v / norm, 2) for k, v in share.items()}
        margin = round(total - sum(parts.values()), 2)
        volume = r.choice([5000, 10000, 25000, 50000])
        region = REGIONS.get(prod["country_of_origin"], prod["country_of_origin"])
        should_costs.append({
            "cost_id": f"SC-{idx:06d}", "sku": prod["sku"], "style_id": prod["style_id"], "volume_units": volume,
            "tooling_total_gbp": round(parts["tooling"] * volume, 0),
            "material_gbp": parts["material"], "labour_gbp": parts["labour"], "overhead_gbp": parts["overhead"],
            "freight_gbp": parts["freight"], "tooling_per_unit_gbp": parts["tooling"], "margin_gbp": margin,
            "total_gbp": total, "region": region, "notes": f"Baseline should-cost, {volume} units, {region}",
            "created_at": g.as_of - timedelta(days=r.randint(20, 120)),
        })
        for _ in range(r.randint(2, 3)):
            cat = r.choice(["material", "labour", "design", "packaging"])
            title = {
                "material": "Switch to a cheaper grade of " + r.choice(["trim", "component", "lining"]),
                "labour": "Simplify " + r.choice(["assembly", "finishing", "stitching"]) + " operations",
                "design": "Reduce " + r.choice(["component count", "finish complexity", "weight"]),
                "packaging": "Change " + r.choice(["carton type", "label finish", "inner packaging"]),
            }[cat]
            saving = round(total * r.uniform(0.012, 0.05), 2)
            options.append({
                "option_id": f"CRO-{len(options) + 1:06d}", "sku": prod["sku"], "title": title,
                "description": f"{title} to cut unit cost by about £{saving:.2f}",
                "saving_gbp_per_unit": saving, "saving_pct": round(saving / unit_cost * 100, 1),
                "implementation_cost_gbp": r.choice([0, 1000, 2500, 5000]),
                "customer_impact": r.choice(["none", "none", "minor", "moderate"]),
                "status": r.choice(["proposed", "tested", "approved"]), "category": cat,
            })
        # two competing quotes for the first few products
        if idx <= 4:
            sup_ids = [prod["supplier_id"]] + [s for s in r.sample(sorted(suppliers), 6) if s != prod["supplier_id"]][:1]
            for sid in sup_ids:
                skew = r.uniform(0.95, 1.12)
                for comp, key in (("material", "material"), ("labour", "labour"), ("overhead", "overhead"), ("freight", "freight")):
                    bm = parts[key]
                    cost = round(bm * skew * r.uniform(0.95, 1.08), 2)
                    quotes.append({
                        "quote_line_id": f"QL-{len(quotes) + 1:06d}", "sku": prod["sku"], "supplier_id": sid,
                        "component_type": comp, "component_desc": comp.capitalize(), "cost_gbp_per_unit": cost,
                        "volume_units": volume, "benchmark_gbp_per_unit": bm,
                        "variance_pct": round((cost / bm - 1) * 100, 1), "comments": "",
                    })

    lifecycle = []
    for a in assets:
        if a["asset_class"] not in ("sorter", "conveyor") or a["asset_id"] in STORY_ASSETS:
            continue
        repl = float(a["replacement_cost_gbp"])
        dt = round(repl * r.uniform(0.15, 0.25), -3)
        specs = [
            ("repair", 0, repl * 0.007, 0, r.randint(2, 3), r.uniform(25, 40), 0, "Keep running with reactive and preventive maintenance"),
            ("overhaul", repl * 0.22, repl * 0.004, 14, r.randint(6, 8), r.uniform(12, 20), repl * 0.02, "Major overhaul of drives, chains and controls"),
            ("replace", repl, repl * 0.004, 52, r.randint(14, 16), r.uniform(4, 8), repl * 0.1, "New equipment with warranty"),
        ]
        for opt, capex, maint, weeks, life, risk, resid, note in specs:
            lifecycle.append({
                "scenario_id": f"LCS-{len(lifecycle) + 1:06d}", "asset_id": a["asset_id"], "option_type": opt,
                "capex_gbp": round(capex, -2), "annual_maintenance_gbp": round(maint, -2),
                "implementation_weeks": weeks, "expected_life_years": life,
                "downtime_risk_high_pct": round(risk, 1), "downtime_cost_if_high_gbp": dt,
                "residual_value_gbp": round(resid, -2), "notes": note,
            })

    return {
        "should_costs": should_costs, "cost_reduction_options": options, "control_option_costs": [],
        "lifecycle_scenarios": lifecycle, "labour_rates": [], "quote_components": quotes,
        "cost_benchmarks": [], "investment_cases": [], "make_vs_buy": [],
    }
