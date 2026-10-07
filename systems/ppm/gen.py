"""PPM system data generation."""
from datetime import timedelta


def generate(g):
    """Generate realistic PPM data."""

    # Get master employees for realistic people
    employees = g.master("employees")
    sites = g.master("sites")

    # Pick realistic employees for project/programme roles
    def pick_employee():
        return g.pick(employees)["employee_id"]

    # Initialize all tables
    result = {
        "projects": [],
        "project_tasks": [],
        "project_milestones": [],
        "raid_log_items": [],
        "cost_saving_initiatives": [],
        "improvement_initiatives": [],
        "capex_proposals": [],
        "capex_projects": [],
        "pilot_projects": [],
        "market_entry_projects": [],
        "action_items": [],
        "artwork_tasks": [],
        "programme_milestones": [],
        "cutover_options": [],
        "automation_options": [],
        "steering_decisions": [],
        "benefits_tracking": [],
        "migration_workstreams": [],
        "test_cycles": [],
        "implementation_projects": [],
        "programmes": [],
        "test_labs": [],
        "pilot_criteria": [],
    }

    # Generate projects (10-15)
    project_ids = []
    for i in range(1, 12):
        owner = pick_employee()
        project_id = f"PRJ-{i:06d}"
        project_ids.append(project_id)

        start_date = g.as_of - timedelta(days=g.rng.randint(30, 60))
        end_date = g.as_of + timedelta(days=g.rng.randint(60, 150))

        result["projects"].append({
            "project_id": project_id,
            "name": g.fake.catch_phrase(),
            "owner_id": owner,
            "status": g.pick(["draft", "active", "on_hold"]),
            "start_date": start_date,
            "end_date": end_date,
            "budget_gbp": round(g.rng.uniform(250000, 5000000), 0),
            "actual_cost_gbp": round(g.rng.uniform(50000, 1000000), 0),
            "description": g.fake.sentence(),
            "created_at": g.as_of - timedelta(days=g.rng.randint(30, 90)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

        # Create 3-5 tasks per project
        for j in range(1, g.rng.randint(3, 6)):
            task_id = f"TSK-{len(result['project_tasks']) + 1:06d}"
            result["project_tasks"].append({
                "task_id": task_id,
                "project_id": project_id,
                "title": g.fake.sentence(),
                "assigned_to": pick_employee(),
                "status": g.pick(["open", "in_progress", "completed"]),
                "due_date": (g.as_of + timedelta(days=g.rng.randint(14, 90))),
                "priority": g.pick(["low", "medium", "high", "urgent"]),
                "description": g.fake.sentence(),
                "created_at": g.as_of - timedelta(days=g.rng.randint(30, 60)),
                "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
            })

        # Create 2-4 milestones per project
        for j in range(1, g.rng.randint(2, 5)):
            milestone_id = f"MIL-{len(result['project_milestones']) + 1:06d}"
            due_date = g.as_of + timedelta(days=g.rng.randint(14, 150))
            forecast_date = due_date + timedelta(days=g.rng.randint(0, 56)) if g.rng.random() > 0.7 else due_date
            result["project_milestones"].append({
                "milestone_id": milestone_id,
                "project_id": project_id,
                "programme_milestone_id": None,
                "title": g.fake.sentence(),
                "due_date": due_date,
                "forecast_date": forecast_date,
                "status": g.pick(["on_track", "at_risk"]),
                "description": g.fake.sentence(),
                "created_at": g.as_of - timedelta(days=g.rng.randint(30, 60)),
                "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
            })

    # Generate RAID log items (15-20)
    for i in range(1, 18):
        raid_id = f"RSD-{i:06d}"
        result["raid_log_items"].append({
            "raid_id": raid_id,
            "project_id": g.pick(project_ids) if g.rng.random() > 0.3 else None,
            "item_type": g.pick(["risk", "action", "issue"]),  # dependencies are hand-written in seed/raid_log_items.csv
            "title": g.fake.sentence(),
            "owner_id": pick_employee(),
            "status": g.pick(["open", "in_progress", "on_hold"]),
            "impact": g.pick(["low", "medium", "high", "critical"]),
            "probability": g.pick(["low", "medium", "high"]),
            "mitigation_action": g.fake.sentence(),
            "target_resolution_date": (g.as_of + timedelta(days=g.rng.randint(14, 90))),
            "resolved_date": None,
            "description": g.fake.sentence(),
            "created_at": g.as_of - timedelta(days=g.rng.randint(30, 60)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

    # Cost saving initiatives: all rows are hand-written in seed/cost_saving_initiatives.csv
    # (a prioritisation story needs meaningful titles, confidences and dependencies, not noise).

    # Generate improvement initiatives (6-8)
    dc_sites = [s for s in sites if s["type"] == "dc"]
    for i in range(1, 7):
        imp_id = f"IMP-{i:06d}"
        site = g.pick(dc_sites)
        result["improvement_initiatives"].append({
            "improvement_id": imp_id,
            "title": f"{site['name']} {g.fake.catch_phrase()}",
            "owner_id": pick_employee(),
            "status": g.pick(["draft", "active", "in_progress"]),
            "site_id": site["site_id"],
            "target_metric": g.pick(["labour productivity", "cost per unit", "quality", "safety", "speed"]),
            "current_value": round(g.rng.uniform(60, 95), 1),
            "target_value": round(g.rng.uniform(95, 110), 1),
            "unit": g.pick(["units/hour", "%", "incidents", "days"]),
            "team_members": None,
            "start_date": g.as_of,
            "target_date": (g.as_of + timedelta(days=g.rng.randint(60, 180))),
            "description": g.fake.sentence(),
            "created_at": g.as_of - timedelta(days=g.rng.randint(30, 90)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

    # Capital queue for the CFO's "next GBP 50m" question: six candidate options, all submitted.
    # (CAP-900001, the Northampton automation case, is a draft in seed/capex_proposals.csv.)
    proposals = [
        ("New regional DC in the North West", None, 22000000, 6.2, 11.4, 4100000, "high",
         "Adds 400k sq ft of regional capacity to relieve Northampton and Daventry",
         "Volume growth 6% a year; 15-month build; land secured at current price",
         "NPV falls to about GBP 0.4m and payback stretches to 8 years under a 10% revenue miss"),
        ("Store refit programme, 60 stores", None, 9500000, 4.1, 17.2, 5200000, "low",
         "Refit 60 high-street and retail-park stores to the new format",
         "Like-for-like sales uplift of 6% in refitted stores; 4-week closure per store",
         "NPV falls to about GBP 3.1m under a 10% revenue miss; payback 5.0 years"),
        ("E-commerce platform and fulfilment capacity", None, 8000000, 3.4, 21.5, 7100000, "medium",
         "Replace the checkout and payments platform and add pick capacity for online orders",
         "Online share of sales reaches 28% in two years; conversion up 0.4 points",
         "NPV falls to about GBP 4.6m under a 10% revenue miss; payback 4.2 years"),
        ("Nearshoring: Turkey and Portugal supplier hubs", None, 7500000, 3.9, 16.8, 4400000, "medium",
         "Move 15% of apparel and home volume to nearshore suppliers to cut lead time by 5 weeks",
         "Landed cost within 3% of Far East; 20 suppliers qualified in 18 months",
         "NPV falls to about GBP 2.8m under a 10% revenue miss; payback 4.8 years"),
        ("New markets: Poland and Czechia launch", None, 6500000, 5.4, 12.6, 1900000, "high",
         "Launch the home range online and in 12 concession stores in Poland and Czechia",
         "Brand awareness builds slowly; 35% gross margin after duties; no local entity needed in year one",
         "NPV turns negative at about GBP -0.6m under a 10% revenue miss; payback 7.1 years"),
        ("Network automation: Daventry and Leeds DCs", None, 11000000, 4.4, 14.9, 3600000, "medium",
         "Goods-to-person picking at Daventry and Leeds to cut labour cost per unit",
         "Labour saving of GBP 2.4m a year from month 15; 12-month build",
         "NPV falls to about GBP 2.0m under a 10% revenue miss; payback 5.3 years"),
    ]
    for i, (cap_title, cap_site, capex, payback, irr, npv, risk, case, assumptions, sens) in enumerate(proposals, 1):
        result["capex_proposals"].append({
            "proposal_id": f"CAP-{i:06d}",
            "title": cap_title,
            "sponsor_id": pick_employee(),
            "status": "submitted",
            "capex_gbp": capex,
            "payback_years": payback,
            "irr_pct": irr,
            "npv_gbp": npv,
            "risk_rating": risk,
            "site_id": cap_site,
            "business_case": case,
            "key_assumptions": assumptions,
            "sensitivity_10pct": sens,
            "submission_date": g.as_of - timedelta(days=g.rng.randint(3, 25)),
            "decision_date": None,
            "description": case,
            "created_at": g.as_of - timedelta(days=g.rng.randint(30, 90)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

    # FY27 capex tracker: seven active projects totalling GBP 34.0m (the COO's envelope question).
    # Each has a delivery project (PRJ-9000xx in seed/projects.csv) whose RAID items give its delivery risk.
    capex_project_ids = []
    capex_projects = [
        ("Daventry DC mezzanine pick floor", "DC2", 5500000, 3.4, 18.2, "PRJ-900031",
         "Adds 90k sq ft of pick floor; peak readiness for e-commerce orders", 2.9),
        ("Leeds DC returns processing upgrade", "DC3", 4200000, 2.9, 21.0, "PRJ-900032",
         "Doubles returns throughput before peak; strongest return in the portfolio", 1.1),
        ("Venlo DC racking extension", "DC4", 3000000, 3.8, 16.5, "PRJ-900033",
         "Adds 6,000 pallet positions for EU peak stock", 0.4),
        ("Columbus DC dock door expansion", "DC5", 2800000, 5.2, 12.1, "PRJ-900034",
         "Six extra dock doors for US inbound; modest return", 0.0),
        ("Northampton yard and gatehouse reconfiguration", "DC1", 3500000, 6.6, 9.4, "PRJ-900035",
         "Reconfigure the yard and gatehouse to cut trailer queues; weakest business case, payback beyond six years", 0.0),
        ("Daventry sortation conveyor upgrade", "DC2", 7000000, 4.1, 15.3, "PRJ-900036",
         "Replace the end-of-life sorter; needed for peak capacity", 3.8),
        ("Northampton WMS and RF scanner replacement", "DC1", 8000000, 4.5, 14.0, "PRJ-900037",
         "Replace RF scanners and upgrade the WMS client; can be phased by zone", 0.0),
    ]
    for i, (cxp_title, cxp_site, capex, payback, irr, delivery, case, spent) in enumerate(capex_projects, 1):
        cxp_id = f"CXP-{i:06d}"
        capex_project_ids.append(cxp_id)
        start_date = (g.as_of - timedelta(days=g.rng.randint(30, 60))) if spent else (g.as_of + timedelta(days=g.rng.randint(14, 70)))
        end_date = start_date + timedelta(days=g.rng.randint(240, 330))
        result["capex_projects"].append({
            "capex_project_id": cxp_id,
            "title": cxp_title,
            "sponsor_id": pick_employee(),
            "status": "active",
            "capex_gbp": capex,
            "actual_spend_gbp": round(spent * 100000, 0),
            "planned_start": start_date,
            "planned_end": end_date,
            "forecast_end": end_date,
            "payback_years": payback,
            "irr_pct": irr,
            "delivery_project_id": delivery,
            "business_case": f"FY27 capex tracker line {i}",
            "phasing": None,
            "site_id": cxp_site,
            "description": case,
            "created_at": g.as_of - timedelta(days=g.rng.randint(60, 120)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

    # Pilot projects, test labs and pilot criteria: hand-written in seed/ (pilot_projects, test_labs, pilot_criteria).

    # Generate market entry projects (2-3)
    for i in range(1, 3):
        mep_id = f"MEP-{i:06d}"
        result["market_entry_projects"].append({
            "market_project_id": mep_id,
            "title": g.fake.sentence(),
            "countries": g.pick(["DE;AT", "FR;BE", "ES;PT"]),
            "owner_id": pick_employee(),
            "status": g.pick(["planning", "approved"]),
            "scope": g.pick(["Home range", "Fashion", "Gifts"]),
            "planned_launch": (g.as_of + timedelta(days=g.rng.randint(120, 360))),
            "budget_gbp": round(g.rng.uniform(1000000, 8000000), 0),
            "workstreams": "Regulatory compliance,Supply chain,Local partnerships",
            "description": g.fake.sentence(),
            "created_at": g.as_of - timedelta(days=g.rng.randint(30, 90)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

    # Generate action items (15-20)
    for i in range(1, 17):
        act_id = f"ACT-{i:06d}"
        result["action_items"].append({
            "action_id": act_id,
            "title": g.fake.sentence(),
            "owner_id": pick_employee(),
            "status": g.pick(["open", "in_progress", "completed"]),
            "priority": g.pick(["low", "medium", "high", "urgent"]),
            "due_date": (g.as_of + timedelta(days=g.rng.randint(7, 60))),
            "source": g.pick(["Steering committee", "RAID item", "Monthly review"]),
            "category": g.pick(["budget", "compliance", "performance", "risk"]),
            "description": g.fake.sentence(),
            "created_at": g.as_of - timedelta(days=g.rng.randint(30, 60)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

    # Generate artwork tasks (3-5)
    for i in range(1, 4):
        awk_id = f"AWK-{i:06d}"
        result["artwork_tasks"].append({
            "task_id": awk_id,
            "title": f"Packaging design - {g.fake.word()}",
            "owner_id": pick_employee(),
            "status": g.pick(["draft", "assigned", "in_progress"]),
            "agency": g.pick(["Brightside Creative", "Harlow & Finch Design"]),
            "countries": g.pick(["GB", "GB,IE", "DE,AT"]),
            "product_category": g.pick(["homewares", "toys", "gifts"]),
            "due_date": (g.as_of + timedelta(days=g.rng.randint(30, 90))),
            "checklist": "Legal marks\nRecycling labels\nLanguage requirements\nWarnings\nNutrition format",
            "deliverables": "3 layout options",
            "requirements": "EU compliance, local language, sustainability",
            "description": g.fake.sentence(),
            "created_at": g.as_of - timedelta(days=g.rng.randint(30, 60)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

    # Generate programme milestones (15-20)
    for i in range(1, 16):
        prm_id = f"PRM-{i:06d}"
        result["programme_milestones"].append({
            "milestone_id": prm_id,
            "programme_name": g.pick(["Automation", "DC3", "Digital"]),  # ERP milestones are in seed/
            "title": g.fake.sentence(),
            "sequence": i,
            "due_date": (g.as_of + timedelta(days=g.rng.randint(30, 300))),
            "forecast_date": (g.as_of + timedelta(days=g.rng.randint(30, 300))),
            "status": g.pick(["planned", "on_track", "at_risk"]),
            "dependencies": None,
            "description": g.fake.sentence(),
            "created_at": g.as_of - timedelta(days=g.rng.randint(30, 90)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

    # Generate cutover options (4-6)
    programmes = ["ERP", "Automation", "DC3"]
    for prog in programmes:
        for opt in ["Big bang", "Phased by region", "Parallel run"]:
            cut_id = f"CUT-{len(result['cutover_options']) + 1:06d}"
            result["cutover_options"].append({
                "option_id": cut_id,
                "programme_name": prog,
                "option_name": opt,
                "status": "active",
                "description": g.fake.sentence(),
                "risk_level": g.pick(["low", "medium", "high"]),
                "estimated_duration_days": g.rng.randint(7, 60),
                "requires_parallel_run": opt == "Parallel run",
                "rollback_feasible": opt != "Big bang" or g.rng.random() > 0.5,
                "created_at": g.as_of - timedelta(days=g.rng.randint(30, 90)),
                "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
            })

    # Automation options per DC (what could be live before peak, and what could not).
    automation = {
        "DC1": [("Pick-to-light zone for fast movers", "Pick-to-light on the 2,000 fastest lines; no building work", 900000, 10, 2.1, 430000),
                ("Conveyor and sortation upgrade", "New sorter induction and lane extension for outbound parcels", 1800000, 14, 2.8, 640000),
                ("Shuttle goods-to-person automation", "Automated shuttle storage and goods-to-person picking; the GBP 12m capex case", 12000000, 52, 4.0, 3000000)],
        "DC2": [("Goods-to-person pick stations", "Six pick stations fed by the existing conveyor", 4500000, 30, 3.6, 1250000),
                ("Pack-bench automation", "Automated carton erecting and labelling at pack benches", 1100000, 12, 2.4, 460000)],
        "DC3": [("Returns sortation automation", "Automated returns induction and sortation", 3200000, 24, 3.3, 970000),
                ("Pallet shuttle racking", "Shuttle racking for slow-moving pallet stock", 2100000, 20, 4.2, 500000)],
        "DC4": [("Pick-to-light zone", "Pick-to-light for EU fast movers", 700000, 9, 2.5, 280000),
                ("Autonomous mobile robots for picking", "Collaborative picking robots for the e-commerce zone", 2600000, 26, 3.9, 670000)],
        "DC5": [("Dock scheduling and yard automation", "Automated gate and dock appointment system", 600000, 11, 3.0, 200000),
                ("Conveyor extension", "Extend outbound conveyor to two new dock doors", 1500000, 16, 3.5, 430000)],
    }
    for site_id, options in automation.items():
        for aut_title, aut_desc, capex, lead, payback, saving in options:
            aut_id = f"AUT-{len(result['automation_options']) + 1:06d}"
            result["automation_options"].append({
                "option_id": aut_id,
                "site_id": site_id,
                "title": aut_title,
                "description": aut_desc,
                "capex_gbp": capex,
                "lead_time_weeks": lead,
                "payback_years": payback,
                "annual_saving_gbp": saving,
                "created_at": g.as_of - timedelta(days=g.rng.randint(30, 60)),
                "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
            })

    # Generate steering decisions (6-8)
    for i in range(1, 7):
        dec_id = f"DEC-{i:06d}"
        result["steering_decisions"].append({
            "decision_id": dec_id,
            "programme_name": g.pick(["Automation", "Digital"]),  # ERP decisions are in seed/
            "title": g.fake.sentence(),
            "status": g.pick(["pending", "approved", "deferred"]),
            "due_date": (g.as_of + timedelta(days=g.rng.randint(7, 30))),
            "options": "Option A, Option B, Option C",
            "recommendation": "Option B recommended",
            "decision": None,
            "rationale": None,
            "owner_id": pick_employee(),
            "description": g.fake.sentence(),
            "created_at": g.as_of - timedelta(days=g.rng.randint(30, 60)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

    # Generate benefits tracking (10-15)
    for i in range(1, 12):
        ben_id = f"BEN-{i:06d}"
        result["benefits_tracking"].append({
            "benefit_id": ben_id,
            "initiative_id": f"CSI-{g.rng.randint(1, 9):06d}",
            "title": g.fake.sentence(),
            "benefit_type": g.pick(["financial", "operational", "strategic"]),
            "planned_gbp": round(g.rng.uniform(100000, 3000000), 0),
            "realized_gbp": round(g.rng.uniform(10000, 500000), 0),
            "realization_date": (g.as_of + timedelta(days=g.rng.randint(60, 180))),
            "forecast_date": (g.as_of + timedelta(days=g.rng.randint(60, 180))),
            "status": g.pick(["on_track", "at_risk"]),
            "owner_id": pick_employee(),
            "description": g.fake.sentence(),
            "created_at": g.as_of - timedelta(days=g.rng.randint(30, 60)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

    # Generate migration workstreams (12-15)
    for i in range(1, 12):
        mws_id = f"MWS-{i:06d}"
        result["migration_workstreams"].append({
            "workstream_id": mws_id,
            "programme_name": "Automation",  # ERP migration workstreams are in seed/
            "name": g.fake.sentence(),
            "object_type": g.pick(["Customer master", "Supplier master", "Purchase orders", "Sales orders", "Inventory"]),
            "status": g.pick(["planning", "extracting", "transforming", "validating", "loading"]),
            "cycle": g.rng.randint(1, 3),
            "planned_date": (g.as_of + timedelta(days=g.rng.randint(30, 150))),
            "actual_date": None,
            "records_total": g.rng.randint(10000, 500000),
            "records_completed": g.rng.randint(1000, 300000),
            "data_quality_pct": g.rng.randint(70, 98),
            "issues_count": g.rng.randint(0, 15),
            "created_at": g.as_of - timedelta(days=g.rng.randint(30, 60)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

    # Generate test cycles (8-10)
    for i in range(1, 8):
        tyc_id = f"TYC-{i:06d}"
        start_date = g.as_of - timedelta(days=g.rng.randint(0, 30))
        end_date = g.as_of + timedelta(days=g.rng.randint(30, 120))
        result["test_cycles"].append({
            "cycle_id": tyc_id,
            "programme_name": g.pick(["ERP", "Automation"]),
            "cycle_name": g.pick(["UAT Cycle 1", "UAT Cycle 2", "SIT Cycle 1", "Regression"]),
            "status": g.pick(["planning", "active", "completed"]),
            "scheduled_start": start_date,
            "scheduled_end": end_date,
            "actual_start": start_date if g.rng.random() > 0.5 else None,
            "actual_end": None,
            "total_tests": g.rng.randint(100, 500),
            "tests_passed": g.rng.randint(50, 400),
            "tests_failed": g.rng.randint(5, 50),
            "tests_blocked": g.rng.randint(0, 20),
            "pass_rate_pct": round(g.rng.uniform(70, 98), 1),
            "description": g.fake.sentence(),
            "created_at": g.as_of - timedelta(days=g.rng.randint(30, 60)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

    # Implementation projects (reporting systems): hand-written in seed/implementation_projects.csv.

    # Generate programmes (3-4)
    programme_names = ["ERP", "Automation", "DC3", "Digital"]
    for prog_name in programme_names:
        result["programmes"].append({
            "programme_name": prog_name,
            "rag_status": g.pick(["red", "amber", "green"]) if prog_name != "ERP" else "red",  # ERP is behind: migration slip
            "owner_id": pick_employee(),
            "description": g.fake.sentence(),
            "created_at": g.as_of - timedelta(days=g.rng.randint(60, 120)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

    return result
