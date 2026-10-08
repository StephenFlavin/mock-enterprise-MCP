# Bench: haiku, 2026-10-07

**10/14 slices pass.** Cost $0.24.

| system | pass | tools | args | grounded | facts |
|---|---|---|---|---|---|
| inv_opt | 10/14 | 13/14 | 14/14 | 13/14 | 11/14 |

## Failures

- `inv_opt-03:27:Q6-a`: invented ids ['SEG-003']. Called: get_sku_abc_classification
- `inv_opt-03:27:Q6-b`: missing tools ['calculate_service_level_target_options']; missing facts ['SEG-001', 'SEG-003']. Called: get_service_level_vs_inventory_curve, get_service_level_vs_inventory_curve
- `inv_opt-03:28:Q3-a`: missing facts ['13679.7']. Called: calculate_lead_time_sensitivity_by_category
- `inv_opt-03:28:Q4-a`: missing facts ['1126.78']. Called: calculate_centralised_stock_saving
