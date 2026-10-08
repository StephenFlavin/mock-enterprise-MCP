"""Python hooks for the cost_model system."""
import math


def _cashflows(capex, benefit, impl_years, years, tax):
    n_build = max(1, math.ceil(impl_years))
    flows = []
    for t in range(1, years + 1):
        out = capex / n_build if t <= n_build else 0.0
        ramp = min(1.0, max(0.0, t - impl_years))
        flows.append(benefit * (1 - tax) * ramp - out)
    return flows


def _npv(flows, rate):
    return sum(f / (1 + rate) ** t for t, f in enumerate(flows, start=1))


def _irr(flows):
    lo, hi = -0.95, 10.0
    if _npv(flows, lo) * _npv(flows, hi) > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if _npv(flows, lo) * _npv(flows, mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def _payback(flows):
    cum = 0.0
    for t, f in enumerate(flows, start=1):
        if cum < 0 <= cum + f and f > 0:
            return t - 1 + (-cum) / f
        cum += f
    return None


def calc_investment_return(ctx, case_id=None, discount_rate_pct=None, benefit_change_pct=0.0):
    rows = ctx.q("SELECT * FROM investment_cases WHERE ($c IS NULL OR case_id = $c) ORDER BY case_id", c=case_id)
    if not rows:
        return "No investment case found."
    out = []
    for r in rows:
        capex = float(r["capex_gbp"])
        base_benefit = float(r["annual_benefit_gbp"]) * (1 + float(benefit_change_pct or 0) / 100)
        impl = float(r["implementation_years"])
        years = int(r["evaluation_years"])
        rate = float(discount_rate_pct if discount_rate_pct is not None else r["discount_rate_pct"]) / 100
        tax = float(r["tax_rate_pct"]) / 100
        up = float(r["sensitivity_upside_pct"]) / 100
        down = float(r["sensitivity_downside_pct"]) / 100
        flows = _cashflows(capex, base_benefit, impl, years, tax)
        npv = _npv(flows, rate)
        irr = _irr(flows)
        pb = _payback(flows)
        npv_up = _npv(_cashflows(capex, base_benefit * (1 + up), impl, years, tax), rate)
        npv_down = _npv(_cashflows(capex, base_benefit * (1 - down), impl, years, tax), rate)
        out.append({
            "case_id": r["case_id"], "title": r["title"], "description": r["description"],
            "capex_gbp": round(capex), "annual_benefit_gbp": round(base_benefit),
            "implementation_years": impl, "evaluation_years": years, "discount_rate_pct": round(rate * 100, 1),
            "npv_gbp": round(npv), "irr_pct": round(irr * 100, 1) if irr is not None else None,
            "payback_years_from_start": round(pb, 1) if pb is not None else None,
            "npv_per_pound_invested": round(npv / capex, 2),
            "npv_upside_gbp": round(npv_up), "npv_downside_gbp": round(npv_down),
            "upside_benefit_pct": round(up * 100), "downside_benefit_pct": round(down * 100),
            "risk_rating": r["risk_rating"], "dependencies": r["dependencies"],
            "formula": (f"NPV = sum over {years} years of (benefit x (1 - {tax * 100:.0f}% tax), starting after the "
                        f"{impl:g}-year build, less capex spread over the build) / (1 + {rate * 100:.0f}%)^year"),
        })
    out.sort(key=lambda d: -d["npv_gbp"])
    return out
