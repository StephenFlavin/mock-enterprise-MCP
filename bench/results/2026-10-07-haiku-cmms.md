# Bench: haiku, 2026-10-07

**0/15 slices pass.** Cost $0.01.

| system | pass | tools | args | grounded | facts |
|---|---|---|---|---|---|
| cmms | 0/15 | 1/15 | 15/15 | 15/15 | 0/15 |

## Failures

- `cmms-01:10:Q1-a`: missing tools ['list_unplanned_stoppages']; missing facts ['Bearing failure', 'Motor bearing', 'Software glitch', 'Control board']. Called: nothing
- `cmms-01:10:Q1-b`: missing tools ['list_work_orders_for_asset']; missing facts ['Replace motor bearing assembly', ['1.25', '75 minutes', '1 hour 15'], '450', 'completed']. Called: nothing
- `cmms-01:10:Q1-c`: missing facts ['Shuttle motor bearing assembly', 'Shuttle oil seal kit', 'Shuttle drive sprocket assembly', '21', '14']. Called: get_spare_parts_stock, get_spare_parts_stock, get_spare_parts_stock
- `cmms-01:10:Q1-d`: missing tools ['get_unplanned_failure_cost']; missing facts ['1386', ['693', '£693']]. Called: nothing
- `cmms-01:10:Q1-e`: missing tools ['list_unplanned_stoppages']; missing facts ['Seal degradation', 'Mechanical wear', 'Lubrication failure', '4.3.0']. Called: nothing
- `cmms-01:10:Q2-a`: missing tools ['get_shutdown_plan']; missing facts ['16', '8500', 'approved', '13', '4']. Called: nothing
- `cmms-01:10:Q2-b`: missing tools ['list_asset_run_hours']; missing facts ['51230', 'poor', '5.2', 'degrading']. Called: nothing
- `cmms-01:10:Q2-c`: missing tools ['list_asset_run_hours']; missing facts [['AST-DC1-CNV-G01', 'Conveyor gearbox 1'], ['AST-DC1-CNV-M08', 'Conveyor drive motor 8'], 'poor']. Called: nothing
- `cmms-01:10:Q2-d`: missing tools ['get_unplanned_failure_cost']; missing facts [['1224', '1225'], ['533', '534'], ['690', '691']]. Called: nothing
- `cmms-01:10:Q2-e`: missing tools ['list_work_orders_for_asset']; missing facts ['Complete overhaul of sorter rollers and sensors', 'Replace sorter drive motor and gearbox', '2026-10-19']. Called: nothing
- `cmms-01:10:Q2-f`: missing tools ['create_work_order']; missing facts ['open', '2026-10-19']. Called: nothing
- `cmms-01:10:Q2-g`: missing tools ['cancel_work_order']; missing facts ['open', 'cancelled']. Called: nothing
- `cmms-01:10:Q4-a`: missing tools ['get_asset_maintenance_cost_history']; missing facts [['57967.8', '57968'], ['27394', '27395'], ['30573', '30574'], ['230.1', '230']]. Called: nothing
- `cmms-01:10:Q4-b`: missing tools ['list_unplanned_stoppages']; missing facts ['Lubrication failure', 'Mechanical wear', 'Sensor malfunction', 'Gearbox']. Called: nothing
- `cmms-01:10:Q4-c`: missing tools ['get_unplanned_failure_cost']; missing facts ['5325', '15.5', '1775']. Called: nothing
