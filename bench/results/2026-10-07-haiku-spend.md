# Bench: haiku, 2026-10-07

**6/17 slices pass.** Cost $0.26.

| system | pass | tools | args | grounded | facts |
|---|---|---|---|---|---|
| spend | 6/17 | 13/17 | 17/17 | 17/17 | 9/17 |

## Failures

- `spend-04:32:Q7`: missing facts ['22474000']. Called: calculate_price_variance_vs_contract, get_supplier_share_of_wallet, get_payment_terms_benchmark
- `spend-04:32:Q8`: missing facts ['154871']. Called: calculate_price_variance_vs_contract, list_top_suppliers_by_spend, calculate_renegotiation_recovery, calculate_renegotiation_recovery, calculate_renegotiation_recovery, calculate_renegotiation_recovery, calculate_renegotiation_recovery, calculate_renegotiation_recovery
- `spend-04:34:Q7`: missing facts ['33169']. Called: get_nearshore_spend_and_forecast_volume
- `spend-04:36:Q1`: missing tools ['list_spend_by_supplier_and_category']. Called: get_preferred_supplier_share_trend, calculate_price_variance_vs_contract, get_spend_by_supplier
- `spend-04:36:Q2`: missing facts ['3056334', '152817', '366760']. Called: get_supplier_fragmentation_by_category, calculate_consolidation_savings, get_historic_savings_realisation_rates
- `spend-04:36:Q3`: missing facts ['1270000', '658000']. Called: compare_reported_vs_realised_savings, calculate_realised_savings
- `spend-04:36:Q4`: missing facts ['8.6']. Called: list_top_categories_by_spend, compare_price_paid_to_benchmark, compare_price_paid_to_benchmark, compare_price_paid_to_benchmark, compare_price_paid_to_benchmark, compare_price_paid_to_benchmark
- `spend-04:36:Q5`: missing facts ['1714451', '1453000']. Called: get_vendor_spend_last_24_months, get_vendor_spend_last_24_months, list_spend_by_supplier_and_category, list_spend_by_supplier_and_category, calculate_consolidation_savings
- `spend-04:36:Q6`: missing tools ['get_supplier_input_cost_mix']. Called: calculate_expected_price_increase_by_supplier, list_suppliers_by_price_increase_history
- `spend-04:37:Q3`: missing tools ['list_spend_by_supplier_and_category']. Called: list_top_suppliers_by_spend, classify_spend_one_off_vs_recurring, classify_spend_one_off_vs_recurring, classify_spend_one_off_vs_recurring
- `spend-04:37:Q5`: missing tools ['get_spend_by_supplier', 'get_spend_by_supplier']; missing facts ['600000']. Called: list_spend_by_supplier_and_category, list_spend_by_supplier_and_category
