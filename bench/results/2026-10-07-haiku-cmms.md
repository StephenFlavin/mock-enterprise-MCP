# Bench: haiku, 2026-10-07

**14/15 slices pass.** Cost $0.21.

| system | pass | tools | args | grounded | facts |
|---|---|---|---|---|---|
| cmms | 14/15 | 14/15 | 15/15 | 15/15 | 15/15 |

## Failures

- `cmms-01:10:Q2-e`: missing tools ['list_work_orders_for_asset']. Called: get_shutdown_plan
