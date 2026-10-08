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


def _d(v):
    from datetime import date
    return v if isinstance(v, date) else date.fromisoformat(str(v)[:10])


def run_programme_scenario(ctx, programme_name, scenario_type, parameter):
    """Re-plan the programme under a change scenario, from its milestones and migration resource plan."""
    from datetime import timedelta
    ms = ctx.q("""
        SELECT milestone_id, title, due_date, forecast_date, status, sequence
        FROM programme_milestones
        WHERE programme_name = $prog AND status != 'cancelled'
        ORDER BY sequence
    """, prog=programme_name)
    if not ms:
        return {"programme_name": programme_name, "error": "No plan milestones for this programme"}
    go_live = ms[-1]
    due, fc = _d(go_live["due_date"]), _d(go_live["forecast_date"] or go_live["due_date"])
    open_ms = [m for m in ms if m["status"] != "completed"]
    done = [m for m in ms if m["status"] == "completed"]
    start = _d(done[-1]["forecast_date"] or done[-1]["due_date"]) if done else _d(ms[0]["due_date"])
    critical_path = max((fc - start).days, 0)  # days left on the critical path to go-live
    ws = ctx.q("""
        SELECT coalesce(fte_required, 0) AS req, coalesce(fte_available, 0) AS avail,
               CASE WHEN planned_date IS NOT NULL AND forecast_date IS NOT NULL
                    THEN greatest(date_diff('day', planned_date, forecast_date), 0) ELSE 0 END AS behind
        FROM migration_workstreams
        WHERE programme_name = $prog AND status != 'completed'
    """, prog=programme_name)
    gap = round(sum(max(w["req"] - w["avail"], 0) for w in ws), 1)
    behind = max((w["behind"] for w in ws), default=0)
    avail_total = sum(w["avail"] for w in ws)
    try:
        x = float(str(parameter).rstrip("%"))
    except ValueError:
        return {"programme_name": programme_name, "error": f"parameter must be a number, got {parameter!r}"}

    if scenario_type == "date_slip":
        shift = int(round(x * 7))
        desc = f"Date slip of {x:g} weeks: every open milestone moves {shift} days."
    elif scenario_type == "scope_reduction":
        shift = -int(round(critical_path * x / 100))
        desc = f"Scope cut of {x:g}%: the {critical_path} days left on the critical path shrink by the same share."
    else:  # resource_change: FTE added (negative = removed)
        if x >= 0:
            frac = min(x / gap, 1.0) if gap > 0 else 0.0
            shift = -int(round(behind * frac))
            desc = (f"Adding {x:g} FTE against a gap of {gap:g} FTE recovers {-shift} of the {behind} days "
                    f"the migration is behind.")
        else:
            shift = int(round(critical_path * abs(x) / avail_total)) if avail_total else 0
            desc = f"Losing {abs(x):g} FTE of {avail_total:g} available adds {shift} days to the critical path."
    new_fc = fc + timedelta(days=shift)
    return {
        "programme_name": programme_name,
        "scenario_type": scenario_type,
        "parameter": parameter,
        "go_live_milestone": go_live["title"],
        "planned_go_live": str(due),
        "current_forecast_go_live": str(fc),
        "current_slip_days": (fc - due).days,
        "scenario_go_live": str(new_fc),
        "scenario_change_days": shift,
        "scenario_vs_plan_days": (new_fc - due).days,
        "milestones_affected": len(open_ms),
        "fte_gap_now": gap,
        "impact": desc,
        "recommendation": "Steering committee approval required for change",
    }
