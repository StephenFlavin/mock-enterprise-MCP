"""Python hooks for loss prevention calculations."""

FORMULA = "payback_months = 12 x annual cost / annual shrink reduction"


def _row(label, cost, reduction, n):
    cost, reduction = float(cost or 0), float(reduction or 0)
    out = {
        "control": label,
        "programmes": n,
        "annual_cost_gbp": round(cost, 2),
        "annual_shrink_reduction_gbp": round(reduction, 2),
        "net_annual_benefit_gbp": round(reduction - cost, 2),
        "formula": FORMULA,
    }
    if reduction > 0:
        out["payback_months"] = round(12 * cost / reduction, 1)
        out["payback_years"] = round(cost / reduction, 2)
        out["verdict"] = "pays back within a year" if cost <= reduction else "does not pay back within a year"
    else:
        out["payback_months"] = None
        out["payback_years"] = None
        out["verdict"] = "no shrink reduction recorded"
    return out


def calc_control_payback(ctx, control_id=None, control_type=None, site_id=None):
    """One programme by id, or the average of active programmes per control type (optionally for one store)."""
    if control_id:
        rows = ctx.q("SELECT control_id, site_id, control_type, annual_cost_gbp, shrink_reduction_gbp "
                     "FROM control_programs WHERE control_id = $c", c=control_id)
        if not rows:
            return {"error": f"Control {control_id} not found"}
        r = rows[0]
        out = _row(f"{r['control_id']} ({r['control_type']} at {r['site_id']})", r["annual_cost_gbp"], r["shrink_reduction_gbp"], 1)
        return [out]
    rows = ctx.q("SELECT control_type, count(*) AS n, avg(annual_cost_gbp) AS cost, avg(shrink_reduction_gbp) AS red "
                 "FROM control_programs WHERE status = 'active' AND ($t IS NULL OR control_type = $t) "
                 "AND ($s IS NULL OR site_id = $s) GROUP BY control_type", t=control_type, s=site_id)
    out = [_row(r["control_type"], r["cost"], r["red"], r["n"]) for r in rows]
    out.sort(key=lambda x: (x["payback_months"] is None, x["payback_months"] or 0))
    return out or {"error": "No matching active control programmes"}
