"""PPM system Python-based tools."""


def get_programme_resource_plan(ctx, programme_name):
    """Resource plan and availability by workstream: FTE needed vs assigned, with the gap."""
    rows = ctx.q("""
        SELECT workstream_id, name AS workstream, object_type, owner_id AS lead_id, status,
               fte_required, fte_available,
               round(coalesce(fte_required, 0) - coalesce(fte_available, 0), 1) AS fte_gap,
               blocker
        FROM migration_workstreams
        WHERE programme_name = $prog AND status != 'completed'
        ORDER BY fte_gap DESC, workstream_id
    """, prog=programme_name)
    total_req = round(sum(r["fte_required"] or 0 for r in rows), 1)
    total_avail = round(sum(r["fte_available"] or 0 for r in rows), 1)
    for r in rows:
        r["programme_fte_required"] = total_req
        r["programme_fte_available"] = total_avail
        r["programme_fte_gap"] = round(total_req - total_avail, 1)
    return rows


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
