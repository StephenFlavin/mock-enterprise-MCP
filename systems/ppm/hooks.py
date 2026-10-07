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
