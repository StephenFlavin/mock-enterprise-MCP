"""PPM system Python-based tools."""


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
