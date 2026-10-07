"""Network design system: scenarios, DCs, sites, volumes, forecasts and inefficiencies."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng

    # Network scenarios: baseline single DC, dual owned, partner-led
    scenarios = [
        {
            "scenario_id": "NS-000001",
            "name": "Baseline: Single DC at Northampton",
            "description": "Current state: single DC at Northampton handling all UK",
            "dc_count": 1,
            "primary_site_id": "DC1",
            "secondary_site_id": None,
            "tertiary_site_id": None,
            "scenario_type": "baseline",
            "annual_handling_cost_gbp": 8500000,
            "annual_transport_cost_gbp": 12000000,
            "annual_rent_gbp": 2400000,
            "annual_labour_cost_gbp": 5600000,
            "avg_delivery_days_stores": 2.5,
            "avg_delivery_days_customers": 3.2,
            "peak_capacity_units": 3500000,
            "redundancy_score": 20.0,
            "status": "active",
            "created_at": g.fake.iso8601(),
        },
        {
            "scenario_id": "NS-000002",
            "name": "Dual Owned: Northampton + Midlands",
            "description": "Add second DC in Midlands (e.g. Daventry area) for split load",
            "dc_count": 2,
            "primary_site_id": "DC1",
            "secondary_site_id": "DC2",
            "tertiary_site_id": None,
            "scenario_type": "owned_dc",
            "annual_handling_cost_gbp": 9200000,
            "annual_transport_cost_gbp": 10800000,
            "annual_rent_gbp": 3600000,
            "annual_labour_cost_gbp": 7200000,
            "avg_delivery_days_stores": 1.8,
            "avg_delivery_days_customers": 2.4,
            "peak_capacity_units": 5200000,
            "redundancy_score": 65.0,
            "status": "active",
            "created_at": g.fake.iso8601(),
        },
        {
            "scenario_id": "NS-000003",
            "name": "Hybrid: Northampton + Partner 3PL in Midlands",
            "description": "Keep Northampton, use third-party partner logistics for Midlands/North",
            "dc_count": 2,
            "primary_site_id": "DC1",
            "secondary_site_id": None,
            "tertiary_site_id": "PTN-0012",
            "scenario_type": "partner_dc",
            "annual_handling_cost_gbp": 8100000,
            "annual_transport_cost_gbp": 11200000,
            "annual_rent_gbp": 2400000,
            "annual_labour_cost_gbp": 4800000,
            "avg_delivery_days_stores": 2.1,
            "avg_delivery_days_customers": 2.8,
            "peak_capacity_units": 4800000,
            "redundancy_score": 55.0,
            "status": "active",
            "created_at": g.fake.iso8601(),
        },
    ]

    # DC profiles for each scenario
    dc_profiles = [
        {
            "profile_id": "DCP-000001",
            "site_id": "DC1",
            "scenario_id": "NS-000001",
            "annual_fixed_cost_gbp": 1200000,
            "annual_rent_gbp": 2400000,
            "annual_labour_cost_gbp": 5600000,
            "handling_cost_per_unit_gbp": 0.85,
            "transport_cost_per_unit_gbp": 1.20,
            "peak_capacity_units_day": 9600,
            "avg_daily_volume_units": 7500,
            "utilisation_pct": 78.1,
            "region": "Midlands",
            "created_at": g.fake.iso8601(),
        },
        {
            "profile_id": "DCP-000002",
            "site_id": "DC1",
            "scenario_id": "NS-000002",
            "annual_fixed_cost_gbp": 1100000,
            "annual_rent_gbp": 1800000,
            "annual_labour_cost_gbp": 3600000,
            "handling_cost_per_unit_gbp": 0.82,
            "transport_cost_per_unit_gbp": 1.10,
            "peak_capacity_units_day": 7200,
            "avg_daily_volume_units": 5200,
            "utilisation_pct": 72.2,
            "region": "Midlands",
            "created_at": g.fake.iso8601(),
        },
        {
            "profile_id": "DCP-000003",
            "site_id": "DC2",
            "scenario_id": "NS-000002",
            "annual_fixed_cost_gbp": 980000,
            "annual_rent_gbp": 1800000,
            "annual_labour_cost_gbp": 3600000,
            "handling_cost_per_unit_gbp": 0.80,
            "transport_cost_per_unit_gbp": 0.95,
            "peak_capacity_units_day": 7200,
            "avg_daily_volume_units": 5000,
            "utilisation_pct": 69.4,
            "region": "Midlands",
            "created_at": g.fake.iso8601(),
        },
        {
            "profile_id": "DCP-000004",
            "site_id": "DC1",
            "scenario_id": "NS-000003",
            "annual_fixed_cost_gbp": 1200000,
            "annual_rent_gbp": 2400000,
            "annual_labour_cost_gbp": 4800000,
            "handling_cost_per_unit_gbp": 0.81,
            "transport_cost_per_unit_gbp": 1.12,
            "peak_capacity_units_day": 8400,
            "avg_daily_volume_units": 6500,
            "utilisation_pct": 77.4,
            "region": "Midlands",
            "created_at": g.fake.iso8601(),
        },
    ]

    # Site candidates for shortlist
    site_candidates = [
        {
            "candidate_id": "SC-000001",
            "site_id": "DC2",
            "name": "Daventry South (ex Wincanton)",
            "region": "Midlands",
            "status": "shortlist",
            "estimated_rent_gbp_pa": 1800000,
            "land_area_sqft": 430000,
            "labour_availability_score": 75.0,
            "transport_connectivity_score": 82.0,
            "planning_risk_score": 25.0,
            "notes": "Existing industrial site, good road access to M1/M6, proven labour pool. Minor planning complexity.",
            "removed_reason": None,
            "removed_at": None,
        },
        {
            "candidate_id": "SC-000002",
            "site_id": "DC3",
            "name": "Leeds South (new build possible)",
            "region": "Yorkshire",
            "status": "shortlist",
            "estimated_rent_gbp_pa": 1500000,
            "land_area_sqft": 450000,
            "labour_availability_score": 68.0,
            "transport_connectivity_score": 78.0,
            "planning_risk_score": 55.0,
            "notes": "Greenfield opportunity, strong logistics cluster forming. Higher planning uncertainty.",
            "removed_reason": None,
            "removed_at": None,
        },
        {
            "candidate_id": "SC-000003",
            "site_id": None,
            "name": "Coventry Business Park (leasehold partnership)",
            "region": "Midlands",
            "status": "removed",
            "estimated_rent_gbp_pa": 1650000,
            "land_area_sqft": 380000,
            "labour_availability_score": 72.0,
            "transport_connectivity_score": 79.0,
            "planning_risk_score": 40.0,
            "notes": "Partner-led DC opportunity, good connectivity. Shorter-term commitment.",
            "removed_reason": "Lower capacity than Daventry, higher long-term cost.",
            "removed_at": g.fake.iso8601(),
        },
    ]

    # Volume history: 24 months back, by region and channel
    volume_history = []
    regions = ["UK North", "UK South", "UK Midlands", "Ireland", "EU Central"]
    channels = ["stores", "ecommerce", "wholesale"]
    for weeks_back in range(104, -1, -1):  # 2 years of weekly data
        period = g.as_of - timedelta(weeks=weeks_back)
        for region in regions:
            # Stores
            base_store_units = r.randint(8000, 15000)
            volume_history.append({
                "vol_id": f"VH-{len(volume_history) + 1:06d}",
                "period": period,
                "region": region,
                "channel": "stores",
                "units": base_store_units,
                "created_at": g.fake.iso8601(),
            })
            # Ecommerce (growing trend)
            weeks_fraction = weeks_back / 104.0
            ecom_units = int(3000 + weeks_fraction * 2000 + r.randint(-500, 500))
            volume_history.append({
                "vol_id": f"VH-{len(volume_history) + 1:06d}",
                "period": period,
                "region": region,
                "channel": "ecommerce",
                "units": max(1000, ecom_units),
                "created_at": g.fake.iso8601(),
            })
            # Wholesale
            wholesale_units = r.randint(2000, 5000)
            volume_history.append({
                "vol_id": f"VH-{len(volume_history) + 1:06d}",
                "period": period,
                "region": region,
                "channel": "wholesale",
                "units": wholesale_units,
                "created_at": g.fake.iso8601(),
            })

    # Growth plans for 2027-2030
    growth_plans = [
        {
            "plan_id": "GP-000001",
            "year": 2027,
            "description": "Baseline growth: 5% volume CAGR, e-commerce to 28%",
            "assumed_total_growth_pct": 5.0,
            "assumed_ecommerce_growth_pct": 3.0,
            "assumed_market_expansion": "Organic store network expansion",
            "status": "active",
            "created_at": g.fake.iso8601(),
        },
        {
            "plan_id": "GP-000002",
            "year": 2028,
            "description": "Accelerated growth: 7% volume, e-commerce to 32%",
            "assumed_total_growth_pct": 7.0,
            "assumed_ecommerce_growth_pct": 4.0,
            "assumed_market_expansion": "International expansion (EU)",
            "status": "active",
            "created_at": g.fake.iso8601(),
        },
        {
            "plan_id": "GP-000003",
            "year": 2029,
            "description": "Mature growth: 5% volume, e-commerce to 36%",
            "assumed_total_growth_pct": 5.0,
            "assumed_ecommerce_growth_pct": 4.0,
            "assumed_market_expansion": "Market consolidation",
            "status": "active",
            "created_at": g.fake.iso8601(),
        },
        {
            "plan_id": "GP-000004",
            "year": 2030,
            "description": "Strategic plan: 5% volume, e-commerce to 40%",
            "assumed_total_growth_pct": 5.0,
            "assumed_ecommerce_growth_pct": 4.0,
            "assumed_market_expansion": "Digital-first retail",
            "status": "active",
            "created_at": g.fake.iso8601(),
        },
    ]

    # Ecommerce forecasts
    ecommerce_forecasts = []
    for months_ahead in range(0, 37, 3):  # Quarterly for 3 years
        period = g.as_of + timedelta(days=months_ahead * 30)
        ecom_share = 22 + (months_ahead / 36 * 18)  # Growing from 22% to 40%
        store_share = 65 - (months_ahead / 36 * 18)
        wholesale_share = 100 - ecom_share - store_share
        total_units = 2500000 + (months_ahead / 36 * 500000)
        ecommerce_forecasts.append({
            "ecom_id": f"EF-{len(ecommerce_forecasts) + 1:06d}",
            "period": period,
            "ecommerce_share_pct": round(ecom_share, 1),
            "stores_share_pct": round(store_share, 1),
            "wholesale_share_pct": round(wholesale_share, 1),
            "total_volume_units": int(total_units),
            "created_at": g.fake.iso8601(),
        })

    # Labour cost data by region
    labour_cost_data = [
        {
            "labour_id": "LC-000001",
            "region": "UK South",
            "annual_cost_per_worker_gbp": 28000,
            "availability_workers": 2400,
            "turnover_pct": 22.0,
            "training_cost_gbp": 1200,
            "record_date": g.as_of,
        },
        {
            "labour_id": "LC-000002",
            "region": "UK Midlands",
            "annual_cost_per_worker_gbp": 26500,
            "availability_workers": 2800,
            "turnover_pct": 20.0,
            "training_cost_gbp": 1100,
            "record_date": g.as_of,
        },
        {
            "labour_id": "LC-000003",
            "region": "UK North",
            "annual_cost_per_worker_gbp": 25000,
            "availability_workers": 3200,
            "turnover_pct": 18.0,
            "training_cost_gbp": 1000,
            "record_date": g.as_of,
        },
        {
            "labour_id": "LC-000004",
            "region": "Ireland",
            "annual_cost_per_worker_gbp": 27500,
            "availability_workers": 1800,
            "turnover_pct": 19.0,
            "training_cost_gbp": 1150,
            "record_date": g.as_of,
        },
    ]

    # Inefficiencies identified
    inefficiencies = [
        {
            "ineff_id": "INE-000001",
            "ineff_type": "cross_ship",
            "origin_site": "DC1",
            "dest_site": "DC2",
            "impacted_units_annually": 120000,
            "current_cost_gbp": 145000,
            "potential_saving_gbp": 85000,
            "fix_cost_gbp": 180000,
            "fix_lead_time_days": 45,
            "priority_rank": 1,
            "status": "identified",
            "created_at": g.fake.iso8601(),
        },
        {
            "ineff_id": "INE-000002",
            "ineff_type": "split_order",
            "origin_site": "DC1",
            "dest_site": "ST105",
            "impacted_units_annually": 85000,
            "current_cost_gbp": 98000,
            "potential_saving_gbp": 52000,
            "fix_cost_gbp": 120000,
            "fix_lead_time_days": 60,
            "priority_rank": 2,
            "status": "identified",
            "created_at": g.fake.iso8601(),
        },
        {
            "ineff_id": "INE-000003",
            "ineff_type": "long_haul",
            "origin_site": "DC1",
            "dest_site": "ST245",
            "impacted_units_annually": 65000,
            "current_cost_gbp": 112000,
            "potential_saving_gbp": 68000,
            "fix_cost_gbp": 95000,
            "fix_lead_time_days": 30,
            "priority_rank": 3,
            "status": "identified",
            "created_at": g.fake.iso8601(),
        },
    ]

    # Outage scenarios: what if DC1 goes down for 7, 14, 21 days
    outage_scenarios = [
        {
            "outage_id": "OS-000001",
            "primary_site_down": "DC1",
            "outage_days": 7,
            "service_impact_pct": 8.5,
            "cost_of_mitigation_gbp": 245000,
            "extra_inventory_units": 45000,
            "alternative_capacity_site": "DC2",
            "alternative_capacity_available": 2200,
            "scenario_date": g.fake.iso8601(),
        },
        {
            "outage_id": "OS-000002",
            "primary_site_down": "DC1",
            "outage_days": 14,
            "service_impact_pct": 15.2,
            "cost_of_mitigation_gbp": 520000,
            "extra_inventory_units": 95000,
            "alternative_capacity_site": "DC2",
            "alternative_capacity_available": 2200,
            "scenario_date": g.fake.iso8601(),
        },
        {
            "outage_id": "OS-000003",
            "primary_site_down": "DC1",
            "outage_days": 21,
            "service_impact_pct": 22.8,
            "cost_of_mitigation_gbp": 820000,
            "extra_inventory_units": 150000,
            "alternative_capacity_site": "DC2",
            "alternative_capacity_available": 2200,
            "scenario_date": g.fake.iso8601(),
        },
    ]

    return {
        "network_scenarios": scenarios,
        "dc_profiles": dc_profiles,
        "site_candidates": site_candidates,
        "volume_history": volume_history,
        "growth_plans": growth_plans,
        "ecommerce_forecasts": ecommerce_forecasts,
        "labour_cost_data": labour_cost_data,
        "inefficiencies": inefficiencies,
        "outage_scenarios": outage_scenarios,
    }
