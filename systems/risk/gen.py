def generate(g):
    """Generate realistic risk management data around the enterprise."""

    # Get suppliers for realistic risk generation
    suppliers = g.master("suppliers")
    employees = g.master("employees")
    sites = g.master("sites")
    skus = g.master("products")[:50]  # Sample

    rng = g.rng
    fake = g.fake

    # Risk register entries - diverse portfolio
    risk_register = []
    risk_ids = ["RSK-000001", "RSK-000002", "RSK-000003", "RSK-000004", "RSK-000005"]

    for i, risk_id in enumerate(risk_ids[:3]):
        risk_register.append({
            "risk_id": risk_id,
            "risk_category": ["supply_chain", "geopolitical", "financial"][i % 3],
            "description": [
                "Concentration in Vietnam sourcing - 40% of SKUs at risk if port closes",
                "Energy price volatility affecting production costs - current hedges expire Q1",
                "Single carrier dependency for European distribution"
            ][i],
            "owner_id": g.pick(employees)["employee_id"],
            "likelihood_pct": rng.randint(30, 85),
            "impact_gbp": float(rng.randint(200000, 2000000)),
            "exposure_gbp": 0,  # Will be calculated in SQL
            "rating": ["low", "medium", "high", "critical"][rng.randint(0, 3)],
            "affected_sku": g.pick(skus)["sku"] if rng.random() > 0.3 else None,
            "affected_supplier_id": g.pick(suppliers)["supplier_id"] if rng.random() > 0.2 else None,
            "affected_site_id": g.pick(sites)["site_id"] if rng.random() > 0.4 else None,
            "mitigation_plan": "Review and diversify sourcing; build buffer stock; negotiate contracts",
            "status": "active",
            "assumptions": "Assumes current geopolitical stability; assumes carrier capacity unchanged",
            "created_at": g.days_ago(rng.randint(30, 180)),
            "updated_at": g.days_ago(rng.randint(1, 30)),
            "archived_at": None,
        })

    # Add a mitigated risk
    risk_register.append({
        "risk_id": "RSK-000004",
        "risk_category": "operational",
        "description": "Warehouse management system integration delays - mitigated with phased rollout",
        "owner_id": g.pick(employees)["employee_id"],
        "likelihood_pct": 20,
        "impact_gbp": 150000,
        "exposure_gbp": 30000,
        "rating": "low",
        "affected_sku": None,
        "affected_supplier_id": None,
        "affected_site_id": "DC1",
        "mitigation_plan": "Implemented phased rollout plan with fallback procedures",
        "status": "mitigated",
        "assumptions": "Assumes IT team capacity; assumes vendor support available",
        "created_at": g.days_ago(120),
        "updated_at": g.days_ago(15),
        "archived_at": None,
    })

    # Risk alert rules
    alert_rules = []
    for i in range(8):
        alert_rules.append({
            "rule_id": f"ARU-{i+1:06d}",
            "rule_name": [
                "Vietnam geopolitical risk escalation",
                "Critical supplier financial warning",
                "Port disruption in Asia-Pacific",
                "Extreme weather in sourcing regions",
                "Regulatory compliance breach alerts",
                "Key carrier capacity constraint",
                "Exchange rate volatility threshold",
                "Supplier quality failure threshold"
            ][i],
            "trigger_type": ["country_risk", "supplier_risk", "port_risk", "weather", "regulatory", "carrier", "financial", "other"][i],
            "trigger_country": "VN" if i < 4 else None,
            "trigger_supplier_id": g.pick(suppliers)["supplier_id"] if i in [1, 6] else None,
            "severity_level": ["info", "warning", "critical"][rng.randint(0, 2)],
            "description": ["Watch Vietnam political developments", "Monitor supplier credit rating",
                           "Track port status", "Monitor weather forecasts", "Track new regulations",
                           "Monitor carrier capacity", "Track FX movements", "Track quality metrics"][i],
            "action_required": ["Review contingency plans", "Prepare dual sourcing", "Activate air freight",
                               "Accelerate shipments", "Review compliance", "Negotiate additional capacity",
                               "Adjust hedges", "Notify quality team"][i],
            "active": rng.random() > 0.2,
            "created_at": g.days_ago(rng.randint(30, 180)),
            "last_triggered_at": g.days_ago(rng.randint(1, 30)) if rng.random() > 0.4 else None,
        })

    # Risk events - current monitoring
    risk_events = []
    event_types = ["geopolitical", "weather", "port_disruption", "supplier_issue", "regulatory", "financial"]
    for i in range(12):
        detected = g.days_ago(rng.randint(1, 20))
        risk_events.append({
            "event_id": f"RVT-{i+1:06d}",
            "event_type": event_types[i % len(event_types)],
            "location": ["Vietnam", "South China Sea", "Port of Singapore", "Bangladesh", "Thailand"][rng.randint(0, 4)],
            "description": [
                "Typhoon season escalation - potential impact on port operations",
                "Supplier liquidity concerns reported in news",
                "Labor unrest at key port affecting throughput",
                "New export restrictions on electronics components",
                "Carrier rate hike announcement for Q4",
                "Political tensions affecting shipping lanes"
            ][i % 6],
            "severity": ["low", "medium", "high", "critical"][rng.randint(0, 3)],
            "affected_suppliers": ",".join([g.pick(suppliers)["supplier_id"] for _ in range(rng.randint(1, 3))]),
            "affected_ports": "Singapore,HCMC Port,Hai Phong" if i % 3 == 0 else None,
            "time_to_impact_days": rng.randint(3, 45),
            "revenue_at_risk_gbp": float(rng.randint(50000, 800000)),
            "status": ["emerging", "active", "monitoring"][rng.randint(0, 2)],
            "first_detected_at": detected,
            "impact_felt_at": g.days_ago(rng.randint(0, 10)) if rng.random() > 0.7 else None,
        })

    # Risk scenarios
    risk_scenarios = []
    scenario_names = [
        "Vietnam port closure - 6 weeks",
        "Major supplier bankruptcy",
        "Geopolitical escalation - shipping blocked",
        "Climate event - production facility damaged"
    ]
    for i, name in enumerate(scenario_names):
        risk_scenarios.append({
            "scenario_id": f"RSC-{i+1:06d}",
            "scenario_name": name,
            "description": [
                "Saigon port closed for 6 weeks due to typhoon or political event",
                "Major Vietnam supplier bankruptcy triggers supply interruption",
                "US-China tensions escalate, blocking shipping through Taiwan strait",
                "Flooding damages key Bangladesh production facility for 8 weeks"
            ][i],
            "trigger_event": ["Typhoon/political event", "Financial crisis", "Geopolitical escalation", "Extreme weather"][i],
            "likelihood_pct": [35, 15, 20, 25][i],
            "revenue_impact_gbp": float([750000, 500000, 1200000, 400000][i]),
            "margin_impact_pct": [8.5, 6.2, 12.0, 5.8][i],
            "affected_skus": "STY-5520,K-1700,PF-220" if i < 2 else "STY-7731",
            "mitigation_options": ["Air freight, alternate ports, buffer stock", "Dual source activation",
                                  "Reroute via alternate lanes", "Shift to secondary facilities"][i],
            "cost_to_mitigate_gbp": float([250000, 180000, 320000, 150000][i]),
            "payback_weeks": [12, 14, 16, 10][i],
            "created_at": g.days_ago(rng.randint(60, 180)),
            "created_by_id": g.pick(employees)["employee_id"],
        })

    # Disruption incidents - historical
    disruption_incidents = []
    for i in range(3):
        started = g.days_ago(rng.randint(30, 180))
        ended = g.days_ago(rng.randint(5, 25))
        disruption_incidents.append({
            "incident_id": f"DIS-{i+1:06d}",
            "incident_name": [
                "Port congestion at Singapore - March 2026",
                "Supplier quality issue - electronics batch recall",
                "Carrier capacity shortage - rate spike"
            ][i],
            "description": [
                "Unexpected port congestion caused 3-week dwell time for inbound container",
                "Defective component batch from Bangladesh supplier affected 2,500 units",
                "Major carrier cut capacity, doubled rates for Asia-Europe lanes"
            ][i],
            "root_cause": [
                "Understaffing at port due to labor disputes",
                "Quality control gap in supplier's new line",
                "Carrier vessel breakdown cascade effect"
            ][i],
            "started_at": started,
            "ended_at": ended,
            "duration_days": (started - ended).days,
            "revenue_impact_gbp": float([320000, 280000, 150000][i]),
            "cost_impact_gbp": float([85000, 120000, 200000][i]),
            "affected_suppliers": g.pick(suppliers)["supplier_id"] if i > 0 else None,
            "affected_skus": "K-1700" if i == 1 else None,
            "lessons_learned": [
                "Need real-time port visibility; consider port insurance",
                "Tighten supplier quality audits; require redundant testing",
                "Diversify carriers; negotiate long-term rate protection"
            ][i],
            "assumptions_wrong": [
                "Assumed port operates at normal capacity; actual: 30% reduction in throughput",
                "Assumed supplier's quality certifications meant zero defects; actual: needed tighter audits",
                "Assumed carrier capacity stable; actual: highly volatile during peak season"
            ][i],
            "status": "closed",
        })

    # Risk assumptions for the disruption incidents
    risk_assumptions = []
    for incident_idx, incident in enumerate(disruption_incidents):
        for j in range(3):
            risk_assumptions.append({
                "incident_id": incident["incident_id"],
                "assumption_id": j + 1,
                "assumption_text": [
                    "Port operates at 85-90% normal capacity during peak season",
                    "Supplier's ISO certifications guarantee <0.1% defect rate",
                    "Carrier maintains 15% capacity buffer year-round"
                ][j],
                "expected_value": ["85-90%", "<0.1% defect", "15% buffer"][j],
                "actual_value": ["50-60% capacity", "2.5% defect rate", "No buffer available"][j],
                "impact_of_error": [
                    "Delayed 8 containers, cascading into 18-day shipment delays",
                    "Cost £120k in rework + brand risk; lost 5% of month's revenue",
                    "Rates tripled for 3 weeks, added £200k unbudgeted cost"
                ][j],
                "recorded_at": g.days_ago(rng.randint(5, 20)),
            })

    # Guidance risks
    guidance_risks = []
    for i in range(4):
        guidance_risks.append({
            "guidance_risk_id": f"GRK-{i+1:06d}",
            "risk_description": [
                "Vietnam supply disruption could impact Q4 revenue guidance",
                "Energy cost volatility could reduce margin guidance by 50bps",
                "Supply chain delays could push inventory buildup into next year",
                "Tariff escalation scenarios could impact FY 2027 margin guidance"
            ][i],
            "guidance_range_gbp": ["850-880m", "870-910m", "890-920m", "900-950m"][i],
            "likelihood_pct": [40, 35, 25, 45][i],
            "impact_gbp": float([200000, 150000, 100000, 250000][i]),
            "mitigation": [
                "Activated contingency sourcing plan; prepared communication",
                "Hedging program in place; quarterly rebalancing",
                "Working with ops on acceleration plan; buffering capacity",
                "Monitoring tariff proposals; scenario analysis underway"
            ][i],
            "status": ["active", "mitigated", "active", "active"][i],
            "created_at": g.days_ago(rng.randint(45, 120)),
        })

    # Single points of failure
    single_points_of_failure = []
    spof_data = [
        {
            "failure_type": "supplier",
            "description": "Vietnam supplier (SUP-0001) sole source for Style 5520 - 35% of Q4 sales",
            "critical_skus": "STY-5520",
            "affected_supplier_id": "SUP-0001",
            "revenue_dependent_gbp": 450000,
            "mitigation_options": "Dual source with India supplier; 6-week lead time agreed",
            "option_cost_gbp": 35000,
            "priority": "critical"
        },
        {
            "failure_type": "route",
            "description": "70% of inbound via Suez Canal - blocked or congested cuts access",
            "critical_skus": "K-1700,PF-220",
            "revenue_dependent_gbp": 820000,
            "mitigation_options": "Activate Cape of Good Hope reroute; air freight for critical SKUs",
            "option_cost_gbp": 180000,
            "priority": "high"
        },
        {
            "failure_type": "facility",
            "description": "DC1 (Northampton) handles 45% of inbound - single facility point of failure",
            "revenue_dependent_gbp": 1200000,
            "mitigation_options": "Load balance to DC2 and DC3; pre-position buffer inventory",
            "option_cost_gbp": 95000,
            "priority": "high"
        },
        {
            "failure_type": "carrier",
            "description": "Carrier CAR-0042 handles 60% of Europe distribution",
            "revenue_dependent_gbp": 650000,
            "mitigation_options": "Contract with secondary carrier CAR-0043; negotiate standby capacity",
            "option_cost_gbp": 42000,
            "priority": "medium"
        }
    ]

    for i, data in enumerate(spof_data):
        single_points_of_failure.append({
            "spof_id": f"SPF-{i+1:06d}",
            "failure_type": data["failure_type"],
            "description": data["description"],
            "critical_skus": data.get("critical_skus"),
            "affected_supplier_id": data.get("affected_supplier_id"),
            "affected_route": "Suez Canal" if i == 1 else None,
            "revenue_dependent_gbp": data["revenue_dependent_gbp"],
            "mitigation_options": data["mitigation_options"],
            "option_cost_gbp": data["option_cost_gbp"],
            "priority": data["priority"],
            "status": ["identified", "planning"][rng.randint(0, 1)],
            "created_at": g.days_ago(rng.randint(30, 90)),
        })

    # Cutover risks
    cutover_risks = []
    for i in range(3):
        cutover_risks.append({
            "cutover_risk_id": f"CTO-{i+1:06d}",
            "project_name": ["WMS Migration Go-Live", "SAP S/4HANA Cutover", "Network Redesign Phase 2"][i],
            "risk_description": [
                "Inventory discrepancies discovered at cutover could delay go-live by 2 weeks",
                "Data migration validation incomplete; risk of corrupted master records",
                "New network paths not fully tested; risk of traffic congestion at cutover"
            ][i],
            "probability": ["medium", "high", "medium"][i],
            "business_impact": [
                "Delays operations, unable to process receipts/shipments for up to 2 weeks",
                "Could discover data issues post-cutover requiring emergency fixes",
                "Could cause service interruption affecting customer deliveries"
            ][i],
            "impact_severity": ["high", "critical", "medium"][i],
            "mitigation_steps": [
                "Completed inventory audit; parallel run in progress; rollback plan ready",
                "Incremental testing plan; parallel run for 1 week; data reconciliation daily",
                "Load testing at 150% peak; alternate routing configured; traffic monitoring 24/7"
            ][i],
            "owner_id": g.pick(employees)["employee_id"],
            "status": ["open", "mitigated", "resolved"][i],
            "created_at": g.days_ago(rng.randint(60, 180)),
        })

    # Risk opportunities
    risk_opportunities = []
    for i in range(5):
        risk_opportunities.append({
            "opportunity_id": f"OPP-{i+1:06d}",
            "opportunity_name": [
                "Nearshore sourcing in Morocco for Europe SKUs",
                "Supplier consolidation to gain volume discounts",
                "Predictive supply chain visibility platform",
                "Blockchain traceability for high-value items",
                "Route optimization using AI algorithms"
            ][i],
            "description": [
                "Move 25% of European SKUs to Morocco supplier; 30-day lead vs 60-day from Asia",
                "Reduce supplier base by 30%; negotiate better rates and terms",
                "Real-time end-to-end visibility could reduce safety stock by 15%",
                "Full traceability chain reduces fraud risk and enables premium pricing",
                "Machine learning route optimization saves 8-12% on logistics costs"
            ][i],
            "category": ["efficiency", "cost_saving", "risk_reduction", "revenue_growth", "cost_saving"][i],
            "potential_benefit_gbp": float([120000, 280000, 95000, 180000, 220000][i]),
            "probability_pct": [65, 45, 55, 35, 60][i],
            "expected_value_gbp": float([78000, 126000, 52250, 63000, 132000][i]),
            "owner_id": g.pick(employees)["employee_id"],
            "status": ["identified", "approved", "in_progress", "identified", "approved"][i],
            "created_at": g.days_ago(rng.randint(30, 150)),
        })

    # Risk mitigation options
    risk_mitigation_options = []
    mito_data = [
        {"risk": "RSK-000001", "name": "Activate Vietnam alternative supplier", "cost": 45000, "residual": 35},
        {"risk": "RSK-000001", "name": "Implement port visibility system", "cost": 28000, "residual": 25},
        {"risk": "RSK-000002", "name": "Extend energy hedging program", "cost": 15000, "residual": 40},
        {"risk": "RSK-000003", "name": "Contract with secondary carrier", "cost": 52000, "residual": 50},
    ]

    for i, data in enumerate(mito_data):
        risk_mitigation_options.append({
            "mitigation_id": f"MIT-{i+1:06d}",
            "related_risk_id": data["risk"],
            "option_name": data["name"],
            "option_description": f"Implement {data['name'].lower()} to reduce exposure",
            "cost_gbp": data["cost"],
            "residual_risk_pct": data["residual"],
            "implementation_weeks": rng.randint(2, 12),
            "effectiveness": ["medium", "high", "high", "very_high"][i],
            "owner_id": g.pick(employees)["employee_id"],
        })

    return {
        "risk_register": risk_register,
        "risk_alert_rules": alert_rules,
        "risk_events": risk_events,
        "risk_scenarios": risk_scenarios,
        "disruption_incidents": disruption_incidents,
        "risk_assumptions": risk_assumptions,
        "guidance_risks": guidance_risks,
        "single_points_of_failure": single_points_of_failure,
        "cutover_risks": cutover_risks,
        "risk_opportunities": risk_opportunities,
        "risk_mitigation_options": risk_mitigation_options,
    }
