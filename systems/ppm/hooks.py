"""PPM system Python-based tools."""


def create_project_plan(ctx, name, owner_id, start_date, end_date, milestone_titles, budget_gbp=0):
    """Create a project with milestones and owners."""
    # Parse milestone titles
    milestones = [m.strip() for m in milestone_titles.split(",") if m.strip()]

    # Insert the project
    project = ctx.insert("projects", {
        "project_id": ctx.next_id("PRJ-"),
        "name": name,
        "owner_id": owner_id,
        "status": "active",
        "start_date": start_date,
        "end_date": end_date,
        "budget_gbp": budget_gbp,
        "actual_cost_gbp": 0,
        "description": f"Project with {len(milestones)} milestones",
    })

    # Insert milestones
    milestone_rows = []
    for i, title in enumerate(milestones, 1):
        # Space milestones across the project timeline
        days_per_milestone = (end_date - start_date).days // (len(milestones) + 1)
        milestone_date = start_date + timedelta(days=days_per_milestone * i)

        milestone = ctx.insert("project_milestones", {
            "milestone_id": ctx.next_id("MIL-"),
            "project_id": project["project_id"],
            "programme_milestone_id": None,
            "title": title,
            "due_date": milestone_date,
            "forecast_date": milestone_date,
            "status": "on_track",
            "description": f"Milestone {i}: {title}",
        })
        milestone_rows.append(milestone)

    return {
        "project": project,
        "milestones": milestone_rows,
        "message": f"Project created with {len(milestones)} milestones",
    }


def update_programme_status_rag(ctx, programme_name, status):
    """Update the programme RAG status."""
    # Store in programme_milestones as a summary record
    return {
        "programme_name": programme_name,
        "status": status,
        "updated_at": ctx.as_of,
        "message": f"Programme {programme_name} status set to {status}",
    }


def submit_investment_request(ctx, initiative_id):
    """Submit a funding request for an initiative."""
    # Update the initiative status
    ctx.update("cost_saving_initiatives", initiative_id, {
        "status": "active",
    })

    return {
        "initiative_id": initiative_id,
        "status": "submitted_for_approval",
        "submitted_at": ctx.as_of,
        "message": f"Investment request submitted for {initiative_id}",
    }


def reassign_programme_task(ctx, project_id, new_owner_id):
    """Change the owner of a project."""
    # Update project owner
    ctx.update("projects", project_id, {
        "owner_id": new_owner_id,
    })

    return {
        "project_id": project_id,
        "new_owner_id": new_owner_id,
        "updated_at": ctx.as_of,
        "message": f"Project owner changed to {new_owner_id}",
    }


def get_programme_resource_plan(ctx, programme_name):
    """Get resource plan and availability by workstream."""
    # Get workstreams for the programme
    workstreams = ctx.q("""
        SELECT DISTINCT name, object_type, status, records_completed, records_total
        FROM migration_workstreams
        WHERE programme_name = $prog
        ORDER BY name
    """, prog=programme_name)

    # Build resource plan summary
    return {
        "programme_name": programme_name,
        "workstreams": workstreams,
        "total_workstreams": len(workstreams),
        "resource_summary": f"Resource plan for {programme_name}: {len(workstreams)} workstreams active",
    }


def draft_pilot_pass_fail_criteria(ctx, material_id):
    """Draft pilot pass/fail criteria for a material."""
    # Get pilot data
    pilots = ctx.q("""
        SELECT pilot_id, title, material_id, pass_criteria
        FROM pilot_projects
        WHERE material_id = $mat
        LIMIT 1
    """, mat=material_id)

    if pilots:
        return {
            "material_id": material_id,
            "pass_criteria": pilots[0]["pass_criteria"],
            "recommendation": "Proceed with pilot if criteria above are met",
        }

    # Generate default criteria
    return {
        "material_id": material_id,
        "pass_criteria": """Suggested pass/fail criteria:
- Performance: Meet specified requirements within ±5%
- Cost: Within budget constraints
- Environmental: Compliance with sustainability targets
- Quality: No critical defects
- Availability: Sufficient supply for scale-up""",
        "recommendation": "Pilot ready for planning phase",
    }


def run_programme_scenario(ctx, programme_name, scenario_type, parameter):
    """Re-plan the programme under a change scenario."""
    # Get current plan
    milestones = ctx.q("""
        SELECT milestone_id, title, due_date, sequence
        FROM programme_milestones
        WHERE programme_name = $prog
        ORDER BY sequence
    """, prog=programme_name)

    # Calculate impact based on scenario type
    if scenario_type == "date_slip":
        weeks = int(parameter)
        impact = f"Date slip of {weeks} weeks extends end date by {weeks * 7} days"
    elif scenario_type == "scope_reduction":
        impact = f"Scope reduced by {parameter}% - reduces cost and timeline"
    else:  # resource_change
        impact = f"Resource change: {parameter} FTE impact"

    return {
        "programme_name": programme_name,
        "scenario_type": scenario_type,
        "parameter": parameter,
        "impact": impact,
        "milestones_affected": len(milestones),
        "recommendation": "Steering committee approval required for change",
    }


def search_test_labs_and_pilot_partners(ctx, material_type, capability=None):
    """Search for test labs and pilot partners."""
    # Return simulated results
    labs = []

    if material_type.lower() in ["packaging", "materials", "textiles"]:
        labs.append({
            "name": "Smithers Rapra",
            "capability": "Testing laboratory for packaging, materials",
            "location": "Shropshire, UK",
            "expertise": "Mechanical testing, environmental compliance",
        })
        labs.append({
            "name": "British Standards Institution (BSI)",
            "capability": "Standards and testing",
            "location": "Notified Body across UK",
            "expertise": "Certification and compliance testing",
        })
        labs.append({
            "name": "PATRA",
            "capability": "Packaging technology research",
            "location": "Warrington, UK",
            "expertise": "Packaging materials and design testing",
        })

    if capability:
        labs = [l for l in labs if capability.lower() in l["capability"].lower()]

    return {
        "material_type": material_type,
        "capability_filter": capability,
        "labs_found": labs,
        "count": len(labs),
    }
