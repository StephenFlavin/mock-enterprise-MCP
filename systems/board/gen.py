"""Generate strategic priorities, initiatives, and assumptions for board-level planning."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng

    # Strategic Priorities
    priorities = [
        {
            "priority_id": "PRI-000001",
            "name": "Market Expansion",
            "description": "Expand into new geographic markets",
            "category": "market_expansion",
            "target_outcome": "15% revenue growth from new markets",
            "financial_target_gbp": 45000000,
            "timeframe": "FY27-FY29",
            "status": "active",
            "updated_at": g.as_of - timedelta(days=30)
        },
        {
            "priority_id": "PRI-000002",
            "name": "Supply Chain Resilience",
            "description": "Build dual sourcing and nearshoring capabilities",
            "category": "risk_mitigation",
            "target_outcome": "Reduce single-source risk to <5% of SKUs",
            "financial_target_gbp": 80000000,
            "timeframe": "FY27-FY28",
            "status": "active",
            "updated_at": g.as_of - timedelta(days=15)
        },
        {
            "priority_id": "PRI-000003",
            "name": "Automation & Efficiency",
            "description": "Automate logistics and warehouse operations",
            "category": "efficiency",
            "target_outcome": "20% cost reduction in warehouse operations",
            "financial_target_gbp": 60000000,
            "timeframe": "FY27-FY29",
            "status": "active",
            "updated_at": g.as_of - timedelta(days=10)
        },
        {
            "priority_id": "PRI-000004",
            "name": "Digital Transformation",
            "description": "Modernize IT infrastructure and analytics",
            "category": "transformation",
            "target_outcome": "Real-time visibility and AI-driven decisions",
            "financial_target_gbp": 25000000,
            "timeframe": "FY27-FY28",
            "status": "active",
            "updated_at": g.as_of - timedelta(days=5)
        },
        {
            "priority_id": "PRI-000005",
            "name": "Sustainable Operations",
            "description": "Achieve carbon neutrality across supply chain",
            "category": "risk_mitigation",
            "target_outcome": "Net-zero carbon by 2030",
            "financial_target_gbp": 35000000,
            "timeframe": "FY27-FY30",
            "status": "active",
            "updated_at": g.as_of - timedelta(days=8)
        },
    ]

    # Strategic Plan Assumptions
    assumptions = [
        {
            "assumption_id": "ASSUM-000001",
            "assumption_category": "revenue",
            "description": "Total revenue growth (baseline)",
            "base_value": 5.0,
            "value_unit": "%",
            "confidence_level": "high",
            "sensitivity_to_change_pct": 1.2,
            "rationale": "Conservative estimate based on market trends and historical performance",
            "updated_at": g.as_of - timedelta(days=30)
        },
        {
            "assumption_id": "ASSUM-000002",
            "assumption_category": "revenue",
            "description": "E-commerce channel growth (above store)",
            "base_value": 12.0,
            "value_unit": "%",
            "confidence_level": "medium",
            "sensitivity_to_change_pct": 0.8,
            "rationale": "Digital continues to grow but at moderating rate",
            "updated_at": g.as_of - timedelta(days=25)
        },
        {
            "assumption_id": "ASSUM-000003",
            "assumption_category": "inflation",
            "description": "General CPI inflation rate",
            "base_value": 3.5,
            "value_unit": "%",
            "confidence_level": "medium",
            "sensitivity_to_change_pct": 0.7,
            "rationale": "Bank of England base case mid-2026",
            "updated_at": g.as_of - timedelta(days=20)
        },
        {
            "assumption_id": "ASSUM-000004",
            "assumption_category": "cost",
            "description": "Labor cost inflation",
            "base_value": 4.5,
            "value_unit": "%",
            "confidence_level": "medium",
            "sensitivity_to_change_pct": 1.0,
            "rationale": "Wage pressure in logistics and retail sectors",
            "updated_at": g.as_of - timedelta(days=18)
        },
        {
            "assumption_id": "ASSUM-000005",
            "assumption_category": "cost",
            "description": "Freight rate inflation",
            "base_value": 2.0,
            "value_unit": "%",
            "confidence_level": "low",
            "sensitivity_to_change_pct": 1.5,
            "rationale": "Volatile; based on recent carrier feedback",
            "updated_at": g.as_of - timedelta(days=15)
        },
        {
            "assumption_id": "ASSUM-000006",
            "assumption_category": "economic",
            "description": "GDP growth assumption",
            "base_value": 2.1,
            "value_unit": "%",
            "confidence_level": "high",
            "sensitivity_to_change_pct": 0.9,
            "rationale": "OBR forecast October 2026",
            "updated_at": g.as_of - timedelta(days=12)
        },
        {
            "assumption_id": "ASSUM-000007",
            "assumption_category": "market",
            "description": "Market share in existing markets",
            "base_value": 0.2,
            "value_unit": "%",
            "confidence_level": "medium",
            "sensitivity_to_change_pct": 1.1,
            "rationale": "Retailer competitive intensity remains high",
            "updated_at": g.as_of - timedelta(days=10)
        },
        {
            "assumption_id": "ASSUM-000008",
            "assumption_category": "technology",
            "description": "Automation ROI improvement factor",
            "base_value": 15.0,
            "value_unit": "%",
            "confidence_level": "medium",
            "sensitivity_to_change_pct": 1.3,
            "rationale": "Based on peer benchmarks; assumes successful implementation",
            "updated_at": g.as_of - timedelta(days=8)
        },
    ]

    # Strategic Initiatives (background data)
    initiatives = [
        {
            "initiative_id": "INIT-000001",
            "name": "Northampton DC Automation Phase 2",
            "description": "Expand automated storage and sorting at DC1",
            "category": "automation",
            "owner_id": "EMP-000045",
            "status": "approved",
            "expected_return_gbp": 18000000,
            "required_investment_gbp": 35000000,
            "risk_level": "medium",
            "timeline_months": 24,
            "dependencies": "Supplier selection, site preparation",
            "payback_period_years": 2.1,
            "updated_at": g.as_of - timedelta(days=45)
        },
        {
            "initiative_id": "INIT-000002",
            "name": "Nearshoring Pilot - Eastern Europe",
            "description": "Test manufacturing in Poland and Czech Republic",
            "category": "sourcing",
            "owner_id": "EMP-000062",
            "status": "proposed",
            "expected_return_gbp": 22000000,
            "required_investment_gbp": 28000000,
            "risk_level": "high",
            "timeline_months": 18,
            "dependencies": "Factory audits, vendor setup, logistics redesign",
            "payback_period_years": 1.8,
            "updated_at": g.as_of - timedelta(days=35)
        },
        {
            "initiative_id": "INIT-000003",
            "name": "Store Refit Program Phase 3",
            "description": "Modernize 50 stores with new POS and visual merchandising",
            "category": "retail_experience",
            "owner_id": "EMP-000071",
            "status": "approved",
            "expected_return_gbp": 12000000,
            "required_investment_gbp": 25000000,
            "risk_level": "low",
            "timeline_months": 20,
            "dependencies": "Budget approval, store selection",
            "payback_period_years": 2.5,
            "updated_at": g.as_of - timedelta(days=28)
        },
        {
            "initiative_id": "INIT-000004",
            "name": "Network Consolidation - Ireland",
            "description": "Close 2 small DCs and route via central hub",
            "category": "network_redesign",
            "owner_id": "EMP-000045",
            "status": "proposed",
            "expected_return_gbp": 8000000,
            "required_investment_gbp": 12000000,
            "risk_level": "medium",
            "timeline_months": 12,
            "dependencies": "Stakeholder agreement, regulatory approval",
            "payback_period_years": 1.6,
            "updated_at": g.as_of - timedelta(days=32)
        },
        {
            "initiative_id": "INIT-000005",
            "name": "US Market Entry",
            "description": "Establish distribution and retail footprint in United States",
            "category": "market_entry",
            "owner_id": "EMP-000088",
            "status": "proposed",
            "expected_return_gbp": 45000000,
            "required_investment_gbp": 50000000,
            "risk_level": "high",
            "timeline_months": 36,
            "dependencies": "Board approval, regulatory setup, brand positioning",
            "payback_period_years": 4.2,
            "updated_at": g.as_of - timedelta(days=42)
        },
        {
            "initiative_id": "INIT-000006",
            "name": "Digital Analytics Platform",
            "description": "Implement enterprise analytics and AI for demand forecasting",
            "category": "digital",
            "owner_id": "EMP-000093",
            "status": "approved",
            "expected_return_gbp": 9000000,
            "required_investment_gbp": 16000000,
            "risk_level": "medium",
            "timeline_months": 14,
            "dependencies": "Data governance, talent acquisition",
            "payback_period_years": 1.9,
            "updated_at": g.as_of - timedelta(days=22)
        },
        {
            "initiative_id": "INIT-000007",
            "name": "Dual Sourcing Program - Top 20 SKUs",
            "description": "Establish second sources for high-volume products",
            "category": "sourcing",
            "owner_id": "EMP-000062",
            "status": "approved",
            "expected_return_gbp": 5000000,
            "required_investment_gbp": 8000000,
            "risk_level": "low",
            "timeline_months": 9,
            "dependencies": "Vendor qualification",
            "payback_period_years": 1.7,
            "updated_at": g.as_of - timedelta(days=20)
        },
    ]

    return {
        "strategic_priorities": priorities,
        "strategic_initiatives": initiatives,
        "strategic_plan_assumptions": assumptions,
        "board_agenda_items": []
    }
