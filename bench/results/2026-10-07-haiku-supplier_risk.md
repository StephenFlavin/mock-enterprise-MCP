# Bench: haiku, 2026-10-07

**20/22 slices pass.** Cost $0.27.

| system | pass | tools | args | grounded | facts |
|---|---|---|---|---|---|
| supplier_risk | 20/22 | 22/22 | 22/22 | 22/22 | 20/22 |

## Failures

- `supplier_risk-04:35:Q1`: missing facts ['liquidity']. Called: get_supplier_financial_health_score, get_supplier_risk_alerts, get_supplier_compliance_history
- `supplier_risk-05:43:Q3-write`: missing facts ['rated D']. Called: get_supplier_risk_alerts, create_supplier_risk_alert
