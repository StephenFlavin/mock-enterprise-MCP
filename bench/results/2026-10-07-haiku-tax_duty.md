# Bench: haiku, 2026-10-07

**16/17 slices pass.** Cost $0.28.

| system | pass | tools | args | grounded | facts |
|---|---|---|---|---|---|
| tax_duty | 16/17 | 17/17 | 17/17 | 17/17 | 16/17 |

## Failures

- `tax_duty-02:14:Q1`: missing facts [['was 10', 'from 10', '10% to 15%', 'previously 10']]. Called: get_current_duty_rates, calculate_duty_per_value
