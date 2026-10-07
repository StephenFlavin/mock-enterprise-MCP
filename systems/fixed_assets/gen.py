"""Background fixed asset data: depreciation schedules and capital expenditure plans."""
from datetime import datetime, timedelta


def generate(g):
    """Generate fixed asset register and planned capex."""
    r = g.rng

    # Get all DC assets for depreciation tracking
    all_assets = g.master("assets")
    dc_assets = [a for a in all_assets if a["site_id"].startswith("DC")]

    fixed_assets = []
    planned_capex = []

    # Generate fixed asset depreciation records for all DC assets
    for asset in dc_assets:
        asset_id = asset["asset_id"]
        # Acquisition dates: spread over the last 15 years
        # Install date from master is reference; assume acquisition ~1 month before
        install_date = datetime.fromisoformat(asset["install_date"]).date() if asset.get("install_date") else g.as_of - timedelta(days=365 * 5)
        acquisition_date = install_date - timedelta(days=r.randint(0, 30))

        # Calculate age in years
        years_held = (g.as_of - acquisition_date).days / 365.25

        # Different asset classes have different useful lives
        asset_class = asset.get("asset_class", "other")
        useful_life_map = {
            "shuttle": 10, "conveyor": 12, "sorter": 15, "motor": 8,
            "gearbox": 10, "sensor": 5, "forklift": 8, "reach_truck": 8,
            "dock_leveller": 12, "sprinkler": 20, "racking": 15, "charger": 7,
            "compressor": 10
        }
        useful_life = useful_life_map.get(asset_class, 10)

        # Acquisition cost: use replacement_cost_gbp or estimate
        replacement_cost = float(asset.get("replacement_cost_gbp", 0)) or r.uniform(15000, 250000)
        # Assume acquisition cost is 70-90% of current replacement cost (inflation)
        acquisition_cost = replacement_cost * r.uniform(0.7, 0.9)

        # Calculate depreciation (straight-line)
        depreciation_rate_pct = 100.0 / useful_life
        years_depreciated = min(years_held, useful_life)
        accumulated_depreciation = (acquisition_cost * depreciation_rate_pct / 100.0) * years_depreciated
        book_value = max(0, acquisition_cost - accumulated_depreciation)

        # Status
        if accumulated_depreciation >= acquisition_cost:
            status = "fully_depreciated"
        else:
            status = "in_service"

        # Residual value (typically 5-10% of acquisition cost)
        residual_value = acquisition_cost * r.uniform(0.05, 0.1)

        fa = {
            "asset_id": asset_id,
            "acquisition_date": acquisition_date,
            "acquisition_cost_gbp": round(acquisition_cost, 2),
            "useful_life_years": useful_life,
            "depreciation_method": "straight_line",
            "depreciation_rate_pct": round(depreciation_rate_pct, 2),
            "accumulated_depreciation_gbp": round(accumulated_depreciation, 2),
            "book_value_gbp": round(book_value, 2),
            "residual_value_gbp": round(residual_value, 2),
            "last_depreciation_calc_date": g.as_of,
            "status": status,
        }
        fixed_assets.append(fa)

    # Generate planned capex (mix of automation, renewable energy, maintenance)
    capex_id = 1

    # Automation/robotics projects (including sorter replacement scenarios)
    automation_projects = [
        {"desc": "Sorter system replacement - Northampton DC", "class": "sorter", "cost": 450000, "site": "DC1", "months": 6},
        {"desc": "Conveyor automation expansion - Daventry DC", "class": "conveyor", "cost": 320000, "site": "DC2", "months": 3},
        {"desc": "Shuttle system upgrade - Leeds DC", "class": "shuttle", "cost": 280000, "site": "DC3", "months": 4},
        {"desc": "Robotic picking system phase 1", "class": "other", "cost": 650000, "site": "DC1", "months": 9},
        {"desc": "Conveyor system modernization", "class": "conveyor", "cost": 180000, "site": "DC4", "months": 5},
    ]

    # Renewable energy / sustainability projects
    energy_projects = [
        {"desc": "Solar panel installation - rooftop 10kW", "class": "other", "cost": 85000, "site": "DC1", "months": 4},
        {"desc": "Battery storage system - energy smoothing", "class": "charger", "cost": 120000, "site": "DC2", "months": 3},
        {"desc": "LED lighting retrofit all DCs", "class": "other", "cost": 95000, "site": None, "months": 2},
        {"desc": "Renewable energy microgrids", "class": "other", "cost": 250000, "site": "DC1", "months": 8},
    ]

    # Maintenance/replacement projects
    maintenance_projects = [
        {"desc": "Forklift fleet upgrade - 15 units", "class": "forklift", "cost": 180000, "site": "DC1", "months": 3},
        {"desc": "Reach truck replacement", "class": "reach_truck", "cost": 95000, "site": "DC2", "months": 2},
        {"desc": "Dock leveller preventive replacement", "class": "dock_leveller", "cost": 65000, "site": "DC3", "months": 2},
        {"desc": "Compressor upgrade", "class": "compressor", "cost": 45000, "site": "DC4", "months": 1},
        {"desc": "Motor replacement programme", "class": "motor", "cost": 110000, "site": None, "months": 4},
        {"desc": "Gearbox maintenance overhaul", "class": "gearbox", "cost": 75000, "site": "DC5", "months": 3},
    ]

    all_projects = automation_projects + energy_projects + maintenance_projects

    for proj in all_projects:
        planned_date = g.as_of + timedelta(days=r.randint(30, 365))
        status_choices = ["planned", "planned", "approved", "approved", "in_progress"]
        status = r.choice(status_choices)

        capex = {
            "capex_id": f"CAPEX-{capex_id:06d}",
            "asset_class": proj["class"],
            "description": proj["desc"],
            "estimated_cost_gbp": proj["cost"],
            "planned_date": planned_date,
            "status": status,
            "source_of_funds": r.choices(["capex_budget", "lease", "grant", "self_funded"], [60, 15, 15, 10])[0],
            "site_id": proj["site"],
            "created_at": g.as_of - timedelta(days=r.randint(7, 90)),
        }
        planned_capex.append(capex)
        capex_id += 1

    return {
        "fixed_assets": fixed_assets,
        "planned_capex": planned_capex,
    }
