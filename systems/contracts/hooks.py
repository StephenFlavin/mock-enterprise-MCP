"""Python implementations for contract calculation tools."""
import json


def calc_commitment_risk(ctx, base_volume_units, unit_cost_gbp, contract_id=None, supplier_id=None,
                         commitment_pct=None, pessimistic_volume_pct=70):
    """Downside cost of committing to a volume, under demand scenarios, using the contract's take-or-pay terms."""
    if not contract_id and not supplier_id:
        return "Give contract_id or supplier_id so the commitment terms can be read."
    if contract_id:
        rows = ctx.q("SELECT contract_id, party_id, status FROM contracts WHERE contract_id = $c", c=contract_id)
    else:
        rows = ctx.q("SELECT contract_id, party_id, status FROM contracts WHERE party_id = $s AND contract_type = 'supplier' "
                     "AND status IN ('active', 'draft') ORDER BY end_date DESC", s=supplier_id)
    if not rows:
        return f"No contract found for {contract_id or supplier_id}."
    contract = rows[0]

    clause = ctx.q("SELECT content FROM contract_clauses WHERE contract_id = $c AND clause_type = 'volume_commitment'",
                   c=contract["contract_id"])
    terms = json.loads(clause[0]["content"]) if clause else {}
    contract_commit = terms.get("min_annual_commitment_pct")
    take_or_pay = float(terms.get("take_or_pay_pct", 100))
    commit = float(commitment_pct if commitment_pct is not None else (contract_commit if contract_commit is not None else 100))

    committed_units = round(base_volume_units * commit / 100)
    scenarios = [("upside", 120), ("forecast", 100), ("soft", 85), ("pessimistic", pessimistic_volume_pct)]
    out = []
    for name, pct in scenarios:
        demand = round(base_volume_units * pct / 100)
        shortfall = max(0, committed_units - demand)
        out.append({
            "contract_id": contract["contract_id"],
            "supplier_id": contract["party_id"],
            "scenario": name,
            "demand_pct_of_forecast": pct,
            "demand_units": demand,
            "commitment_pct": commit,
            "committed_units": committed_units,
            "shortfall_units": shortfall,
            "take_or_pay_pct": take_or_pay,
            "unit_cost_gbp": unit_cost_gbp,
            "downside_cost_gbp": round(shortfall * unit_cost_gbp * take_or_pay / 100, 2),
            "capacity_reserved_pct": terms.get("capacity_reserved_pct"),
            "formula": "downside = max(0, committed_units - demand_units) * unit_cost * take_or_pay_pct / 100",
        })
    return out
