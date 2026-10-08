# Systems and MCP tools · 01 Warehouse and Distribution Centre

For each question in the questions file, this lists the enterprise systems that must be reached and the MCP tool methods an AI agent would call.
Tool names are shared across all nine categories so the benchmark stays consistent.
Only the AI-suited personas (score 3+) from the questions file are covered, and every question has a row.

**Legend:** `tool` = read-only call · `tool` ✎ = write or side-effect call · `draft_` tools produce a draft only and are not writes. Tools are listed in the order an agent would likely call them.

---

## 4. Inventory control/cycle counter

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Why is the stock count for bay C-14 so inaccurate? | Warehouse Management System (WMS), Inventory Management System (IMS) | `get_location_inventory_balance`, `list_cycle_count_results_for_location`, `get_stock_movements_for_location`, `list_inventory_adjustments_for_location`, `block_location` ✎, `create_cycle_count_task` ✎, `create_inventory_adjustment` ✎ |
| Q2 | Cluster Q3 adjustments over £500 by cause, zone, shift; rank process problems by value. | Warehouse Management System (WMS), Inventory Management System (IMS), Documents, Code Execution, Labour Management System (LMS), Slotting & Layout Tool | `read_document`, `list_inventory_adjustments`, `list_cycle_count_corrections`, `get_cause_code_definitions`, `run_analysis`, `get_shift_roster_by_date`, `list_new_starters_by_period`, `list_layout_changes`, `update_adjustment_cause_code` ✎, `approve_inventory_adjustment` ✎ |
| Q3 | Which locations to count first in three days: high value, inaccurate, not recent. | Warehouse Management System (WMS), Inventory Management System (IMS) | `list_locations_by_last_count_date`, `get_location_inventory_value`, `get_historical_count_accuracy_by_location`, `calculate_count_priority_score`, `draft_cycle_count_sheet`, `release_cycle_count_tasks` ✎, `cancel_cycle_count_task` ✎, `reassign_cycle_count_task` ✎ |
| Q4 | Receipts versus ASNs over eight weeks: supplier, carrier or our receiving causing variances? | Warehouse Management System (WMS), Purchase Order System, Transport Management System (TMS), Contract Management System, Supplier Portal | `list_goods_receipts`, `list_advance_shipping_notices`, `compare_receipts_to_asns`, `get_carrier_for_inbound_shipment`, `get_supplier_claim_terms`, `draft_supplier_variance_note`, `create_supplier_claim` ✎, `send_supplier_variance_note` ✎ |
| Q5 | Which zones will have the worst stock accuracy going into peak? | Warehouse Management System (WMS), Demand Planning System, Code Execution | `get_stock_accuracy_trend_by_zone`, `get_peak_inbound_forecast`, `run_analysis` |

---

## 6. Warehouse manager

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Cost per unit up 9% on August: split by cost type, find the driver. | ERP (General Ledger), Labour Management System (LMS), Warehouse Management System (WMS), Inventory Management System (IMS), Code Execution | `get_cost_centre_actuals`, `get_labour_hours_by_type`, `get_units_shipped_by_period`, `list_damage_write_offs`, `get_order_line_profile`, `run_analysis` |
| Q2 | Will we run out of pallet space this autumn, when, and why? | Warehouse Management System (WMS), Supply Planning System (MRP/DRP), Purchase Order System, Yard Management System (YMS) | `get_storage_capacity_by_zone`, `get_pallet_positions_by_category`, `list_inbound_purchase_orders_by_week`, `calculate_projected_space_utilisation`, `update_purchase_order_delivery_date` ✎, `cancel_inbound_appointment` ✎ |
| Q3 | Late shift versus overtime for 45 FTE peak gap: cost, productivity, fatigue, retention. | Labour Management System (LMS), Documents, ERP (General Ledger), Health & Safety System, HR Information System (HRIS), Web, Email & Calendar | `read_document`, `get_labour_productivity_by_shift`, `get_overtime_hours_by_shift`, `calculate_shift_option_cost`, `list_fatigue_related_incidents`, `get_attrition_by_shift_pattern`, `search_web`, `draft_recommendation_summary`, `send_email` ✎, `create_agency_labour_request` ✎ |
| Q4 | Benchmark our DC cost and productivity against other retail DCs; which measures compare? | Web, ERP (General Ledger), Labour Management System (LMS), Knowledge Base / Policy Library | `search_kpi_definitions`, `get_dc_cost_and_productivity_kpis`, `search_web`, `fetch_web_page`, `run_analysis` |
| Q5 | Store service level fell 98.5% to 95% in three weeks: where is it breaking? | Order Management System (OMS), Warehouse Management System (WMS), Labour Management System (LMS), Yard Management System (YMS), Transport Management System (TMS) | `get_store_service_level_trend`, `list_short_picks_by_stage`, `get_labour_productivity_by_shift`, `list_late_inbound_trailers`, `list_late_outbound_departures`, `list_recent_configuration_changes`, `update_order_priority` ✎ |

---

## 8. WMS analyst

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | 140 orders stuck in allocation failed since 6am: what do the affected SKUs share? | Warehouse Management System (WMS), Master Data Management (MDM), Integration Platform / API Gateway, Application Monitoring & ITSM | `list_orders_by_status`, `list_allocation_failure_reasons`, `get_sku_master_attributes`, `list_recent_configuration_changes`, `list_interface_errors`, `draft_incident_summary`, `retry_order_allocation` ✎, `create_incident_ticket` ✎ |
| Q2 | Why do ERP and WMS stock not agree (follow-ups cover re-slotting)? | ERP (General Ledger), Warehouse Management System (WMS), Integration Platform / API Gateway, Slotting & Layout Tool | `get_erp_stock_by_sku`, `get_wms_stock_by_sku`, `compare_erp_and_wms_stock`, `list_interface_errors`, `get_pick_affinity_pairs`, `calculate_reslotting_effort`, `create_incident_ticket` ✎ |
| Q3 | Is duplicate task creation after replenishment on WMS 9.2 a known bug? | Warehouse Management System (WMS), Web, Knowledge Base / Policy Library | `get_wms_version_and_patches`, `search_vendor_release_notes`, `list_replenishment_task_duplicates`, `search_internal_knowledge_base`, `create_change_request` ✎, `submit_change_request` ✎ |
| Q4 | Find where the £1.2m ERP-WMS stock gap comes from and whether it recurs. | ERP (General Ledger), Warehouse Management System (WMS), Integration Platform / API Gateway, Knowledge Base / Policy Library | `get_erp_stock_by_sku`, `get_wms_stock_by_sku`, `compare_erp_and_wms_stock`, `get_inventory_status_mapping`, `list_in_transit_documents`, `list_interface_errors`, `search_past_reconciliation_notes`, `draft_root_cause_report`, `create_knowledge_base_article` ✎, `archive_knowledge_base_article` ✎ |
| Q5 | Effect on pick rates and cut-offs of moving e-commerce from wave to continuous batching. | Warehouse Management System (WMS), Order Management System (OMS), Labour Management System (LMS), Transport Management System (TMS), Code Execution, Web | `get_order_profile_summary`, `get_pick_rates_by_method`, `get_wave_configuration`, `get_carrier_cutoff_schedule`, `run_analysis`, `search_web` |

---

## 9. Health & safety officer

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | What are our biggest safety risks across three DCs from 12 months of incidents? | Health & Safety System, Labour Management System (LMS), Code Execution | `list_incidents`, `get_exposure_hours_by_site`, `run_analysis`, `list_open_corrective_actions`, `update_corrective_action_status` ✎ |
| Q2 | UK requirements for electric reach truck charging areas, ventilation, fire separation, training; checklist. | Web, Health & Safety System, Knowledge Base / Policy Library, Project & Portfolio Management Tool | `search_uk_regulations`, `fetch_web_page`, `list_risk_assessments_by_site`, `draft_compliance_checklist`, `list_project_milestones_for_site`, `search_web`, `create_corrective_action` ✎ |
| Q3 | Link Q3 forklift-pedestrian near misses to layout and shift changes; find the driver. | Health & Safety System, Slotting & Layout Tool, Labour Management System (LMS) | `list_incidents`, `list_layout_changes`, `get_shift_roster_by_date`, `list_new_starters_by_period`, `get_incident_location_heatmap`, `run_analysis`, `create_corrective_action` ✎ |
| Q4 | Compare exclusion zones, proximity sensors, speed limiters on evidence and cost for our site. | Web, Health & Safety System, Slotting & Layout Tool, Cost Modelling Tool | `search_web`, `fetch_web_page`, `list_incidents`, `get_site_layout_summary`, `calculate_control_option_cost`, `compare_control_options` |
| Q5 | Any new warehouse safety rules in UK, Germany and Poland, including for agency workers? | Web, Health & Safety System, Labour Management System (LMS), Knowledge Base / Policy Library | `search_uk_regulations`, `search_web`, `fetch_web_page`, `list_site_jurisdictions`, `list_site_safety_procedures`, `list_agency_workers_by_site`, `create_corrective_action` ✎ |

---

## 10. Automation/robotics engineer

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Root causes of 14 shuttle stoppages last month, ranked by lost throughput. | Warehouse Control System (WCS), Maintenance Management System (CMMS), Warehouse Management System (WMS), Code Execution, Purchase Order System | `list_unplanned_stoppages`, `get_fault_log_entries`, `list_work_orders_for_asset`, `get_throughput_loss_for_stoppage`, `get_equipment_software_versions`, `get_spare_parts_stock`, `run_analysis`, `create_purchase_requisition` ✎ |
| Q2 | Which conveyor and sorter parts may fail before 1 November; cost, lead time? | Maintenance Management System (CMMS), Documents, Warehouse Control System (WCS), Supplier Portal, Code Execution | `read_document`, `list_asset_run_hours`, `list_work_orders_for_asset`, `get_fault_log_entries`, `get_unplanned_failure_cost`, `get_part_lead_time`, `get_shutdown_plan`, `run_analysis`, `create_work_order` ✎, `cancel_work_order` ✎ |
| Q3 | What is new in AMR firmware 4.7, and should we update before peak? | Web, Warehouse Control System (WCS), Knowledge Base / Policy Library, Health & Safety System, Application Monitoring & ITSM | `search_vendor_release_notes`, `get_amr_fleet_firmware_versions`, `search_internal_knowledge_base`, `get_safety_validation_records`, `create_change_request` ✎ |
| Q4 | Repair, overhaul or replace the 12-year-old sorter, including seven-year downtime risk. | Maintenance Management System (CMMS), Fixed Asset Register, Demand Planning System, Cost Modelling Tool, Web, Code Execution | `get_asset_maintenance_cost_history`, `list_unplanned_stoppages`, `get_asset_book_value`, `get_volume_forecast`, `calculate_lifecycle_cost_options`, `search_web`, `run_analysis` |
| Q5 | Why does robot throughput drop every afternoon? | Warehouse Control System (WCS), Warehouse Management System (WMS), Application Monitoring & ITSM, Code Execution | `get_robot_throughput_by_hour`, `get_fleet_charging_schedule`, `get_robot_traffic_congestion`, `get_wifi_network_load`, `get_order_mix_by_hour`, `run_analysis`, `update_fleet_charging_schedule` ✎ |

---

## Tool catalogue for this category

| Tool | System | R/W | One-line description |
|---|---|---|---|
| `approve_inventory_adjustment` | Inventory Management System (IMS) | W | Approve a pending adjustment so it posts to stock. |
| `archive_knowledge_base_article` | Knowledge Base / Policy Library | W | Archive a superseded article so it no longer appears in search. |
| `block_location` | Warehouse Management System (WMS) | W | Place a hold on a bin location so no picks or putaways are directed to it. |
| `calculate_control_option_cost` | Cost Modelling Tool | R | Estimate capex and opex for safety control options by site size. |
| `calculate_count_priority_score` | Warehouse Management System (WMS) | R | Rank locations for counting by value, accuracy history and recency. |
| `calculate_lifecycle_cost_options` | Cost Modelling Tool | R | Compare repair, overhaul and replace over a horizon. |
| `calculate_projected_space_utilisation` | Supply Planning System (MRP/DRP) | R | Project space utilisation by week from stock, inbound and outbound plans. |
| `calculate_reslotting_effort` | Slotting & Layout Tool | R | Estimate moves and labour for re-slotting, phased by zone. |
| `calculate_shift_option_cost` | ERP (General Ledger) | R | Total cost comparison of staffing options (premiums, agency fees, allowances). |
| `cancel_cycle_count_task` | Warehouse Management System (WMS) | W | Cancel a released cycle count task for a location. |
| `cancel_inbound_appointment` | Yard Management System (YMS) | W | Cancel a booked inbound dock appointment. |
| `cancel_work_order` | Maintenance Management System (CMMS) | W | Cancel a planned or open maintenance work order. |
| `compare_control_options` | Code Execution | R | Compare control options on evidence and cost. |
| `compare_erp_and_wms_stock` | Integration Platform / API Gateway | R | Reconcile ERP and WMS balances and surface differences. |
| `compare_receipts_to_asns` | Warehouse Management System (WMS) | R | Line-level variance between received quantity and ASN quantity. |
| `create_agency_labour_request` | Labour Management System (LMS) | W | Create a request to the agency for a number of operatives by shift and date range. |
| `create_change_request` | Application Monitoring & ITSM | W | Create a change request record for a patch, firmware or configuration change. |
| `create_corrective_action` | Health & Safety System | W | Create a corrective action with owner, site and due date. |
| `create_cycle_count_task` | Warehouse Management System (WMS) | W | Create a recount task for a single bin location. |
| `create_incident_ticket` | Application Monitoring & ITSM | W | Open an incident ticket and assign it to a support team. |
| `create_inventory_adjustment` | Inventory Management System (IMS) | W | Post a stock adjustment with cause code against a location and SKU. |
| `create_knowledge_base_article` | Knowledge Base / Policy Library | W | Publish a documented cause and fix to the knowledge base. |
| `create_purchase_requisition` | Purchase Order System | W | Create a requisition for spare parts or supplies for approval. |
| `create_supplier_claim` | Supplier Portal | W | Raise a short-shipment or damage claim against a supplier. |
| `create_work_order` | Maintenance Management System (CMMS) | W | Create a maintenance work order for an asset with planned date. |
| `draft_compliance_checklist` | Documents | R (draft) | Draft a walkable compliance checklist. |
| `draft_cycle_count_sheet` | Warehouse Management System (WMS) | R (draft) | Draft a printable count sheet for chosen locations without releasing tasks. |
| `draft_incident_summary` | Application Monitoring & ITSM | R (draft) | Draft an incident summary for operations. |
| `draft_recommendation_summary` | Documents | R (draft) | Draft a one-page recommendation or briefing. |
| `draft_root_cause_report` | Documents | R (draft) | Draft a root cause write-up for review. |
| `draft_supplier_variance_note` | Supplier Portal | R (draft) | Draft a variance summary note to a supplier manager. |
| `fetch_web_page` | Web | R | Fetch and read a public web page or PDF. |
| `get_amr_fleet_firmware_versions` | Warehouse Control System (WCS) | R | Firmware versions across the AMR fleet. |
| `get_asset_book_value` | Fixed Asset Register | R | Net book value and depreciation for an asset. |
| `get_asset_maintenance_cost_history` | Maintenance Management System (CMMS) | R | Maintenance cost history for an asset. |
| `get_attrition_by_shift_pattern` | HR Information System (HRIS) | R | Leaver and retention rates by shift pattern and employment type. |
| `get_carrier_cutoff_schedule` | Transport Management System (TMS) | R | Carrier collection times and order cut-offs. |
| `get_carrier_for_inbound_shipment` | Transport Management System (TMS) | R | Carrier, trailer and delivery details for an inbound shipment. |
| `get_cause_code_definitions` | Warehouse Management System (WMS) | R | Reference list of adjustment cause codes and their intended use. |
| `get_cost_centre_actuals` | ERP (General Ledger) | R | Actual costs by cost centre and account for a period. |
| `get_dc_cost_and_productivity_kpis` | ERP (General Ledger) | R | DC cost per unit and productivity KPIs for comparison. |
| `get_equipment_software_versions` | Warehouse Control System (WCS) | R | Controller and firmware versions per asset. |
| `get_erp_stock_by_sku` | ERP (General Ledger) | R | ERP stock balances by SKU and plant or storage location. |
| `get_exposure_hours_by_site` | Labour Management System (LMS) | R | Hours worked by site, shift and task for rate normalisation. |
| `get_fault_log_entries` | Warehouse Control System (WCS) | R | Equipment fault codes and events from the control system. |
| `get_fleet_charging_schedule` | Warehouse Control System (WCS) | R | Charging schedules and battery states. |
| `get_historical_count_accuracy_by_location` | Warehouse Management System (WMS) | R | Historical count accuracy by location or zone. |
| `get_incident_location_heatmap` | Health & Safety System | R | Incident counts by aisle, crossing point or area. |
| `get_inventory_status_mapping` | Warehouse Management System (WMS) | R | Mapping between WMS and ERP inventory statuses. |
| `get_labour_hours_by_type` | Labour Management System (LMS) | R | Labour hours split by permanent, overtime and agency. |
| `get_labour_productivity_by_shift` | Labour Management System (LMS) | R | Units per hour by shift, task and week. |
| `get_location_inventory_balance` | Warehouse Management System (WMS) | R | Current system stock by SKU, lot and status for a bin location. |
| `get_location_inventory_value` | Inventory Management System (IMS) | R | Stock value held in a location at standard cost. |
| `get_order_line_profile` | Warehouse Management System (WMS) | R | Order profile (units per order, single-unit share) by period. |
| `get_order_mix_by_hour` | Warehouse Management System (WMS) | R | Order mix by hour (lines per order, zone). |
| `get_order_profile_summary` | Order Management System (OMS) | R | Order arrival profile by hour, channel and lines per order. |
| `get_overtime_hours_by_shift` | Labour Management System (LMS) | R | Overtime hours and rates by shift and week. |
| `get_pallet_positions_by_category` | Warehouse Management System (WMS) | R | Pallet positions occupied by product category. |
| `get_part_lead_time` | Supplier Portal | R | Supplier lead time and price for a part. |
| `get_peak_inbound_forecast` | Demand Planning System | R | Forecast inbound and outbound volumes for the peak period. |
| `get_pick_affinity_pairs` | Warehouse Management System (WMS) | R | SKU pairs frequently picked together. |
| `get_pick_rates_by_method` | Labour Management System (LMS) | R | Pick rates by method (wave, batch, discrete) and zone. |
| `get_robot_throughput_by_hour` | Warehouse Control System (WCS) | R | Robot throughput by hour and zone. |
| `get_robot_traffic_congestion` | Warehouse Control System (WCS) | R | Traffic density, blockage and wait events by area. |
| `get_safety_validation_records` | Health & Safety System | R | Safety validation and sign-off records for automation. |
| `get_shift_roster_by_date` | Labour Management System (LMS) | R | Shift pattern and assigned operatives by date and shift. |
| `get_shutdown_plan` | Maintenance Management System (CMMS) | R | Planned shutdown scope, dates and capacity. |
| `get_site_layout_summary` | Slotting & Layout Tool | R | Site layout, aisle and crossing-point data. |
| `get_sku_master_attributes` | Master Data Management (MDM) | R | SKU attributes (dimensions, status, handling flags). |
| `get_spare_parts_stock` | Maintenance Management System (CMMS) | R | Spare parts on hand with reorder levels. |
| `get_stock_accuracy_trend_by_zone` | Warehouse Management System (WMS) | R | Quarterly stock accuracy by zone from cycle count history. |
| `get_stock_movements_for_location` | Warehouse Management System (WMS) | R | Movement history (receipts, putaways, picks, moves) for a location over a date range. |
| `get_storage_capacity_by_zone` | Warehouse Management System (WMS) | R | Pallet position capacity and occupancy by zone. |
| `get_store_service_level_trend` | Order Management System (OMS) | R | Store order service level by week, store and lane. |
| `get_supplier_claim_terms` | Contract Management System | R | Claim window and short-shipment terms from supplier contracts. |
| `get_throughput_loss_for_stoppage` | Warehouse Control System (WCS) | R | Throughput lost per stoppage. |
| `get_units_shipped_by_period` | Warehouse Management System (WMS) | R | Units, orders and lines shipped by period. |
| `get_unplanned_failure_cost` | Maintenance Management System (CMMS) | R | Historic cost and downtime of unplanned failures. |
| `get_volume_forecast` | Demand Planning System | R | Long-range volume forecast by scenario. |
| `get_wave_configuration` | Warehouse Management System (WMS) | R | Wave and release configuration and cut-off parameters. |
| `get_wifi_network_load` | Application Monitoring & ITSM | R | Wireless network load and latency by area and hour. |
| `get_wms_stock_by_sku` | Warehouse Management System (WMS) | R | WMS stock balances by SKU, status and location. |
| `get_wms_version_and_patches` | Warehouse Management System (WMS) | R | Installed WMS version and applied patches. |
| `list_advance_shipping_notices` | Purchase Order System | R | Supplier ASNs with advised quantities per PO line. |
| `list_agency_workers_by_site` | Labour Management System (LMS) | R | Agency headcount by site and agency. |
| `list_allocation_failure_reasons` | Warehouse Management System (WMS) | R | Allocation failure reason codes for orders. |
| `list_asset_run_hours` | Maintenance Management System (CMMS) | R | Run hours and condition readings by asset. |
| `list_cycle_count_corrections` | Warehouse Management System (WMS) | R | Cycle count corrections including reversal records and timestamps. |
| `list_cycle_count_results_for_location` | Warehouse Management System (WMS) | R | Past cycle count results and variances for a location. |
| `list_damage_write_offs` | Inventory Management System (IMS) | R | Damage write-offs and rework events with value. |
| `list_fatigue_related_incidents` | Health & Safety System | R | Incidents tagged to fatigue, long hours or night shifts. |
| `list_goods_receipts` | Warehouse Management System (WMS) | R | Goods receipts with received quantities, dock, user and carrier. |
| `list_in_transit_documents` | ERP (General Ledger) | R | Goods movements posted in one system and pending in the other. |
| `list_inbound_purchase_orders_by_week` | Purchase Order System | R | Open inbound POs by expected arrival week and category. |
| `list_incidents` | Health & Safety System | R | Incidents and near misses with type, severity, location, time and task. |
| `list_interface_errors` | Integration Platform / API Gateway | R | Interface messages, failures and queue backlogs between systems. |
| `list_inventory_adjustments` | Inventory Management System (IMS) | R | Inventory adjustments in a period with value, cause code, zone, user and timestamp. |
| `list_inventory_adjustments_for_location` | Inventory Management System (IMS) | R | Stock adjustments with cause codes posted against a location. |
| `list_late_inbound_trailers` | Yard Management System (YMS) | R | Trailer arrivals versus appointment, with dwell time. |
| `list_late_outbound_departures` | Transport Management System (TMS) | R | Late outbound departures by lane and store. |
| `list_layout_changes` | Slotting & Layout Tool | R | Layout and zone changes with effective dates. |
| `list_locations_by_last_count_date` | Warehouse Management System (WMS) | R | Locations with date of last cycle count. |
| `list_new_starters_by_period` | Labour Management System (LMS) | R | Operatives starting in a period with start date and training status. |
| `list_open_corrective_actions` | Health & Safety System | R | Open corrective actions and controls by site. |
| `list_orders_by_status` | Warehouse Management System (WMS) | R | Orders and lines in a given status with timestamps. |
| `list_project_milestones_for_site` | Project & Portfolio Management Tool | R | Rollout milestones and dates by site. |
| `list_recent_configuration_changes` | Warehouse Management System (WMS) | R | Configuration, release and parameter changes with dates. |
| `list_replenishment_task_duplicates` | Warehouse Management System (WMS) | R | Duplicate replenishment tasks and their creation context. |
| `list_risk_assessments_by_site` | Health & Safety System | R | Current risk assessments by site and activity. |
| `list_short_picks_by_stage` | Warehouse Management System (WMS) | R | Short picks, late waves and loading exceptions by process stage. |
| `list_site_jurisdictions` | Health & Safety System | R | Sites with country and applicable regimes. |
| `list_site_safety_procedures` | Health & Safety System | R | Current procedures and practices by site. |
| `list_unplanned_stoppages` | Maintenance Management System (CMMS) | R | Unplanned stoppages with duration, asset and cause. |
| `list_work_orders_for_asset` | Maintenance Management System (CMMS) | R | Work orders and repair history for an asset. |
| `read_document` | Documents | R | Read the contents of an attached or shared file (CSV, XLSX, PDF). |
| `reassign_cycle_count_task` | Warehouse Management System (WMS) | W | Reassign a count task to a different operative. |
| `release_cycle_count_tasks` | Warehouse Management System (WMS) | W | Release planned count tasks to operatives handheld devices. |
| `retry_order_allocation` | Warehouse Management System (WMS) | W | Re-run allocation for orders stuck in allocation failed. |
| `run_analysis` | Code Execution | R | Run agent-side analysis, grouping, statistics or charts on retrieved data. |
| `search_internal_knowledge_base` | Knowledge Base / Policy Library | R | Search internal runbooks, test plans and procedures. |
| `search_kpi_definitions` | Knowledge Base / Policy Library | R | Internal KPI definitions and calculation methods. |
| `search_past_reconciliation_notes` | Knowledge Base / Policy Library | R | Prior reconciliation write-ups and runbooks. |
| `search_uk_regulations` | Web | R | Search HSE and UK regulatory guidance. |
| `search_vendor_release_notes` | Web | R | Search vendor release notes, known issues and patch notices. |
| `search_web` | Web | R | Public web search (research, regulations, vendor and benchmark material). |
| `send_email` | Email & Calendar | W | Send an email to named recipients with optional attachment. |
| `send_supplier_variance_note` | Supplier Portal | W | Send an approved variance note to the supplier manager. |
| `submit_change_request` | Application Monitoring & ITSM | W | Submit a change request for approval at the change board. |
| `update_adjustment_cause_code` | Inventory Management System (IMS) | W | Change the cause code on an existing adjustment. |
| `update_corrective_action_status` | Health & Safety System | W | Close a corrective action or change its status or due date. |
| `update_fleet_charging_schedule` | Warehouse Control System (WCS) | W | Change the charging windows for the AMR fleet. |
| `update_order_priority` | Order Management System (OMS) | W | Raise or lower the priority of orders for wave release. |
| `update_purchase_order_delivery_date` | Purchase Order System | W | Change the requested delivery date on a PO line. |
