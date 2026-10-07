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
            "item_type": g.pick(["risk", "action", "issue", "dependency"]),
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

    # Generate cost saving initiatives (8-12)
    for i in range(1, 10):
        csi_id = f"CSI-{i:06d}"
        result["cost_saving_initiatives"].append({
            "initiative_id": csi_id,
            "title": g.fake.sentence(),
            "owner_id": pick_employee(),
            "status": g.pick(["draft", "active", "in_progress", "on_hold"]),
            "estimated_saving_gbp": round(g.rng.uniform(50000, 3000000), 0),
            "realized_saving_gbp": round(g.rng.uniform(10000, 500000), 0),
            "confidence_pct": g.rng.randint(30, 95),
            "category": g.pick(["procurement", "labour", "freight", "shrink", "markdown"]),
            "depends_on": None,
            "start_date": g.as_of,
            "target_date": (g.as_of + timedelta(days=g.rng.randint(30, 180))),
            "description": g.fake.sentence(),
            "created_at": g.as_of - timedelta(days=g.rng.randint(30, 90)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

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

    # Generate capex proposals (6-8)
    for i in range(1, 7):
        cap_id = f"CAP-{i:06d}"
        result["capex_proposals"].append({
            "proposal_id": cap_id,
            "title": g.fake.sentence(),
            "sponsor_id": pick_employee(),
            "status": g.pick(["draft", "submitted", "under_review", "approved"]),
            "capex_gbp": round(g.rng.uniform(500000, 15000000), 0),
            "payback_years": round(g.rng.uniform(1.5, 5.5), 1),
            "irr_pct": round(g.rng.uniform(8, 25), 1),
            "npv_gbp": round(g.rng.uniform(500000, 5000000), 0),
            "risk_rating": g.pick(["low", "medium", "high"]),
            "site_id": g.pick(dc_sites)["site_id"] if g.rng.random() > 0.4 else None,
            "business_case": g.fake.sentence(),
            "key_assumptions": g.fake.sentence(),
            "sensitivity_10pct": f"NPV reduces to £{round(g.rng.uniform(200000, 2000000), 0)}k",
            "submission_date": (g.as_of - timedelta(days=g.rng.randint(0, 30))) if g.rng.random() > 0.5 else None,
            "decision_date": None,
            "description": g.fake.sentence(),
            "created_at": g.as_of - timedelta(days=g.rng.randint(30, 90)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

    # Generate capex projects (4-6)
    capex_project_ids = []
    for i in range(1, 5):
        cxp_id = f"CXP-{i:06d}"
        capex_project_ids.append(cxp_id)
        start_date = g.as_of - timedelta(days=g.rng.randint(30, 60))
        end_date = g.as_of + timedelta(days=g.rng.randint(90, 270))
        result["capex_projects"].append({
            "capex_project_id": cxp_id,
            "title": g.fake.sentence(),
            "sponsor_id": pick_employee(),
            "status": g.pick(["planned", "active", "on_hold"]),
            "capex_gbp": round(g.rng.uniform(500000, 12000000), 0),
            "actual_spend_gbp": round(g.rng.uniform(100000, 2000000), 0),
            "planned_start": start_date,
            "planned_end": end_date,
            "forecast_end": (end_date + timedelta(days=g.rng.randint(0, 210))) if g.rng.random() > 0.7 else end_date,
            "payback_years": round(g.rng.uniform(2, 5), 1),
            "irr_pct": round(g.rng.uniform(10, 22), 1),
            "business_case": g.fake.sentence(),
            "phasing": None,
            "site_id": g.pick(dc_sites)["site_id"],
            "description": g.fake.sentence(),
            "created_at": g.as_of - timedelta(days=g.rng.randint(60, 120)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

    # Generate pilot projects (3-5)
    for i in range(1, 4):
        pil_id = f"PIL-{i:06d}"
        start_date = g.as_of - timedelta(days=g.rng.randint(0, 30))
        end_date = g.as_of + timedelta(days=g.rng.randint(30, 120))
        result["pilot_projects"].append({
            "pilot_id": pil_id,
            "title": g.fake.sentence(),
            "material_id": f"MAT-{g.rng.randint(100, 500):05d}",
            "owner_id": pick_employee(),
            "status": g.pick(["planning", "approved", "in_progress"]),
            "test_partner": g.fake.company(),
            "budget_gbp": round(g.rng.uniform(20000, 100000), 0),
            "actual_cost_gbp": round(g.rng.uniform(5000, 50000), 0),
            "planned_start": start_date,
            "planned_end": end_date,
            "actual_end": None,
            "pass_criteria": "Tensile strength >= 50MPa, Cost <= 15pence/unit, Recyclable",
            "result": g.pick(["pass", "fail", "inconclusive", "pending"]),
            "outcome": g.fake.sentence(),
            "created_at": g.as_of - timedelta(days=g.rng.randint(30, 60)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

    # Generate market entry projects (2-3)
    for i in range(1, 3):
        mep_id = f"MEP-{i:06d}"
        result["market_entry_projects"].append({
            "market_project_id": mep_id,
            "title": g.fake.sentence(),
            "countries": g.pick(["PL;CZ", "DE;AT", "FR;BE", "ES;PT"]),
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
            "source": g.pick(["04:36:Q1", "04:37:Q3", "04:40:Q5", "RAID-item"]),
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
            "agency": g.fake.company(),
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
            "programme_name": g.pick(["ERP", "Automation", "DC3", "Digital"]),
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

    # Generate automation options for each DC
    for i, site in enumerate(dc_sites[:4]):
        for j in range(1, 3):
            aut_id = f"AUT-{len(result['automation_options']) + 1:06d}"
            result["automation_options"].append({
                "option_id": aut_id,
                "site_id": site["site_id"],
                "title": g.pick(["Shuttle automation", "Conveyor upgrade", "Sorting automation"]),
                "description": g.fake.sentence(),
                "capex_gbp": round(g.rng.uniform(500000, 8000000), 0),
                "lead_time_weeks": g.rng.randint(12, 52),
                "payback_years": round(g.rng.uniform(2, 5), 1),
                "annual_saving_gbp": round(g.rng.uniform(100000, 1500000), 0),
                "created_at": g.as_of - timedelta(days=g.rng.randint(30, 60)),
                "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
            })

    # Generate steering decisions (6-8)
    for i in range(1, 7):
        dec_id = f"DEC-{i:06d}"
        result["steering_decisions"].append({
            "decision_id": dec_id,
            "programme_name": g.pick(["ERP", "Automation"]),
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
            "programme_name": g.pick(["ERP", "Automation"]),
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

    # Generate implementation projects (5-8)
    for i in range(1, 6):
        ipt_id = f"IPT-{i:06d}"
        result["implementation_projects"].append({
            "impl_project_id": ipt_id,
            "title": g.fake.sentence(),
            "system_name": g.pick(["ESG Platform", "Data Lake", "ML Model", "EDI Integration"]),
            "owner_id": pick_employee(),
            "cost_estimate_gbp": round(g.rng.uniform(200000, 2000000), 0),
            "timeline_weeks": g.rng.randint(8, 48),
            "scope": g.fake.sentence(),
            "deliverables": "System delivered, User training, Documentation",
            "risks": "Vendor delays, Resource availability",
            "resource_plan": "5 FTE required",
            "description": g.fake.sentence(),
            "created_at": g.as_of - timedelta(days=g.rng.randint(30, 60)),
            "updated_at": g.as_of - timedelta(days=g.rng.randint(0, 14)),
        })

    return result
