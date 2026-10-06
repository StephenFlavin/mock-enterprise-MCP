"""Python implementations for contract calculation tools."""

def calc_commitment_risk(ctx, contract_id, base_volume_units, pessimistic_volume_pct=70, unit_cost_gbp=1.0):
    """Calculate risk scenarios for volume commitments."""
    # Get contract terms
    rows = ctx.q(
        "SELECT * FROM contracts WHERE contract_id = $cid",
        cid=contract_id
    )
    if not rows:
        return {"error": "Contract not found"}

    contract = rows[0]

    # Calculate scenarios
    base_cost = base_volume_units * unit_cost_gbp
    pessimistic_units = int(base_volume_units * (pessimistic_volume_pct / 100))
    pessimistic_cost = pessimistic_units * unit_cost_gbp
    optimistic_units = base_volume_units + int(base_volume_units * 0.2)
    optimistic_cost = optimistic_units * unit_cost_gbp

    downside_risk = base_cost - pessimistic_cost
    upside_potential = optimistic_cost - base_cost

    return {
        "contract_id": contract_id,
        "party_id": contract["party_id"],
        "base_volume_units": base_volume_units,
        "base_cost_gbp": base_cost,
        "pessimistic_volume_units": pessimistic_units,
        "pessimistic_cost_gbp": pessimistic_cost,
        "pessimistic_volume_pct": pessimistic_volume_pct,
        "optimistic_volume_units": optimistic_units,
        "optimistic_cost_gbp": optimistic_cost,
        "downside_risk_gbp": downside_risk,
        "upside_potential_gbp": upside_potential,
        "formula": "downside_risk = base_cost - (base_volume * pessimistic_pct * unit_cost)"
    }
