"""Python hooks for loss prevention calculations."""


def calc_control_payback(ctx, control_id):
    """Calculate payback period for a control program."""
    rows = ctx.q(
        "SELECT annual_cost_gbp, shrink_reduction_gbp FROM control_programs WHERE control_id = $c",
        c=control_id
    )

    if not rows:
        return {"error": f"Control {control_id} not found"}

    control = rows[0]
    cost = float(control["annual_cost_gbp"])
    reduction = float(control["shrink_reduction_gbp"])

    if reduction <= 0:
        return {
            "control_id": control_id,
            "annual_cost_gbp": cost,
            "annual_shrink_reduction_gbp": reduction,
            "payback_years": None,
            "note": "No positive shrink reduction recorded",
            "formula": "payback_years = annual_cost / annual_shrink_reduction"
        }

    payback_years = round(cost / reduction, 2)

    return {
        "control_id": control_id,
        "annual_cost_gbp": cost,
        "annual_shrink_reduction_gbp": reduction,
        "payback_years": payback_years,
        "formula": "payback_years = annual_cost / annual_shrink_reduction"
    }
