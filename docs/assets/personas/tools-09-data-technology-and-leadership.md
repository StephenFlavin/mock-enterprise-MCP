# Systems and MCP tools · 09 Data, Technology and Leadership

For every question in the questions file for this category, this lists the enterprise systems an AI agent must reach and the MCP tool methods it would plausibly call, in likely call order.
Tool names are entity-scoped and consistent with the other eight categories; the tool catalogue at the end lists every tool used here.
Personas keep the numbering of the source questions file (84 and 86 are not present there).

**Legend:** Q = question number in the questions file · Systems use canonical names · tools are read-only unless marked ✎ (write or side effect) · `draft_` tools produce documents and are not writes.

## 81. Data analyst, supply chain

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | OTIF fell 94% to 89%: split by dimension, real or definition change, chart pack and send it | Data Warehouse / Lakehouse, BI & Dashboards Platform, Purchase Order System, Warehouse Management System (WMS), Transport Management System (TMS), Knowledge Base / Policy Library, Integration Platform / API Gateway, Code Execution, Email & Calendar | `get_otif_by_dimension`, `list_kpi_definition_changes`, `get_asn_feed_change_log`, `run_data_quality_checks`, `run_analysis`, `draft_chart_pack`, `send_email_with_attachment` ✎ |
| Q2 | Ops and finance inventory numbers differ: which is authoritative, reconcile differences | ERP (General Ledger), Inventory Management System (IMS), Data Warehouse / Lakehouse, Knowledge Base / Policy Library, Code Execution | `get_inventory_valuation_by_site`, `get_stock_position_by_site`, `compare_inventory_balances`, `list_inventory_adjustments_and_cutoffs`, `get_inventory_definition_policy`, `create_inventory_adjustment_journal` ✎ |
| Q3 | Likely range for next month's KPIs and which will miss target | Data Warehouse / Lakehouse, Executive KPI Scorecard, Demand Planning System, Code Execution | `get_kpi_targets`, `get_kpi_history`, `get_volume_forecast`, `calculate_kpi_forecast_range`, `calculate_forecast_backtest_error`, `update_kpi_alert_threshold` ✎ |
| Q4 | Best structure for a WMS, TMS and ERP cost-per-order model, with SQL | Data Warehouse / Lakehouse, Warehouse Management System (WMS), Transport Management System (TMS), ERP (General Ledger), Code Execution | `search_data_catalogue`, `get_table_schema`, `get_wms_labour_and_handling_cost_by_order`, `get_tms_freight_cost_by_shipment`, `get_erp_order_header_and_charges`, `run_sql_query`, `create_warehouse_view` ✎ |
| Q5 | Standard definition of perfect order rate | Web, Knowledge Base / Policy Library | `search_web`, `get_kpi_definition` |
| Q6 | Which data quality problems hurt reporting most, impact, and fix owners; raise tickets | Data Quality & Observability Tool, BI & Dashboards Platform, Master Data Management (MDM) | `list_data_quality_issues`, `get_data_quality_issue_impact`, `get_data_owner_for_dataset`, `get_issue_recurrence_history`, `create_data_quality_ticket` ✎, `reassign_data_quality_issue` ✎ |

## 82. Data scientist

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Best model and features for ocean transit variability; evaluation against carrier estimates | Track & Trace Platform, Carrier Portal, Data Warehouse / Lakehouse, ML Platform / Model Registry, Web | `get_ocean_transit_history_by_lane`, `get_carrier_eta_vs_actual_by_lane`, `get_port_congestion_history`, `list_feature_store_features`, `search_web` |
| Q2 | Demand model degrading three months: drift, pipeline change or behaviour shift; retrain needs | ML Platform / Model Registry, Data Quality & Observability Tool, Application Monitoring & ITSM, Demand Planning System, Data Warehouse / Lakehouse | `get_model_accuracy_history`, `get_feature_drift_report`, `list_pipeline_and_schema_changes`, `list_releases_and_change_requests`, `get_forecast_error_by_category`, `get_model_training_dataset_summary`, `run_analysis`, `submit_model_retraining_job` ✎ |
| Q3 | Uplift of the new model versus today's process, and its value | ML Platform / Model Registry, Demand Planning System, Inventory Management System (IMS), Project & Portfolio Management Tool, Code Execution | `get_model_backtest_results`, `get_current_process_forecast_accuracy`, `calculate_benefit_of_accuracy_uplift`, `get_project_cost_estimate` |
| Q4 | State-of-the-art new-product demand forecasting with little history; open-source options | Web, Data Warehouse / Lakehouse, Code Execution | `search_web`, `fetch_web_page`, `search_open_source_packages`, `get_new_product_launch_history`, `run_analysis` |
| Q5 | Are production models healthy? | ML Platform / Model Registry, Application Monitoring & ITSM, Data Quality & Observability Tool | `list_registered_models`, `get_model_health_summary`, `get_feature_drift_report`, `list_model_retraining_schedule`, `get_model_alert_rules`, `create_model_alert_rule` ✎, `delete_model_alert_rule` ✎ |
| Q6 | Feature engineering plan for PO-level supplier delay risk: leakage, validation, baseline | Purchase Order System, Warehouse Management System (WMS), Supplier Relationship Management (SRM), ERP (General Ledger), Track & Trace Platform, Web, ML Platform / Model Registry, Code Execution, Project & Portfolio Management Tool | `get_po_history_with_outcomes`, `get_asn_timeliness_history`, `get_supplier_scorecard_history`, `get_payment_history_by_supplier`, `get_port_congestion_history`, `get_weather_events_by_region`, `list_feature_store_features`, `calculate_baseline_delay_rate_by_supplier`, `run_analysis`, `create_project_task` ✎ |

## 83. ERP / systems integrator

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | 200 EDI PO acknowledgements failed overnight: find common cause; reprocess on confirmation | Wholesale / EDI Portal, Integration Platform / API Gateway, Application Monitoring & ITSM | `get_failed_edi_messages`, `get_edi_error_log_summary`, `list_recent_mapping_and_config_changes`, `get_edi_partner_status`, `submit_edi_message_reprocess` ✎ |
| Q2 | New supplier ASN spec: explain changes, map to WMS fields, gaps, change order | Documents, Integration Platform / API Gateway, Warehouse Management System (WMS), Wholesale / EDI Portal, Project & Portfolio Management Tool | `read_document`, `get_edi_map_for_message_type`, `get_wms_inbound_field_schema`, `compare_edi_spec_to_wms_fields`, `list_trading_partners_using_message_type`, `get_project_cost_estimate`, `create_change_request` ✎ |
| Q3 | EDI, API or file transfer for a new 3PL, and the risks | Integration Platform / API Gateway, Supplier Relationship Management (SRM), Knowledge Base / Policy Library, Web | `search_knowledge_base_articles`, `get_3pl_integration_capabilities`, `get_integration_run_cost_by_pattern`, `search_web` |
| Q4 | Will integrations cope with peak: closest to limits, first load test | Application Monitoring & ITSM, Integration Platform / API Gateway, Demand Planning System, Code Execution | `get_interface_throughput_and_capacity`, `get_peak_interface_load_history`, `get_volume_forecast`, `calculate_interface_headroom_at_peak`, `list_load_test_history`, `create_load_test_run` ✎ |
| Q5 | Why website stock updates are 20 minutes behind; fix if config | E-commerce Platform, Integration Platform / API Gateway, Inventory Management System (IMS), Application Monitoring & ITSM, Order Management System (OMS) | `get_stock_feed_latency`, `get_pipeline_step_timings`, `get_website_vs_wms_stock_variance`, `get_oversell_incidents`, `update_stock_feed_schedule` ✎ |

## 85. Cybersecurity analyst

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Rank alerts and scan results by business risk; action today versus false positives | Identity & Security Platform, Application Monitoring & ITSM, Knowledge Base / Policy Library, Web | `list_open_security_alerts`, `list_vulnerability_scan_findings`, `get_asset_business_criticality`, `get_known_exploited_vulnerabilities`, `get_alert_false_positive_history`, `calculate_business_risk_score`, `update_security_alert_status` ✎ |
| Q2 | Odd 03:12 supplier login touched EDI and bank details: real incident, actions, CISO summary; contain if real | Documents, Identity & Security Platform, Supplier Portal, Wholesale / EDI Portal, Master Data Management (MDM), Accounts Payable System, Web, Knowledge Base / Policy Library | `read_document`, `search_auth_logs`, `get_user_session_history`, `get_supplier_portal_access_log`, `list_vendor_bank_detail_changes`, `get_payment_runs_for_changed_vendors`, `get_ip_reputation`, `get_incident_response_playbook`, `draft_incident_summary`, `create_security_incident` ✎, `block_user_account` ✎, `block_vendor_payment` ✎ |
| Q3 | Highest-risk supplier and partner connections and risk-reducing controls | Integration Platform / API Gateway, Supplier Onboarding & Risk System, Identity & Security Platform, Knowledge Base / Policy Library | `list_third_party_connections`, `get_connection_access_privileges`, `get_supplier_security_risk_rating`, `list_controls_in_place_for_connection`, `search_knowledge_base_articles`, `create_security_remediation_task` ✎ |
| Q4 | Any exploited vulnerabilities in our WMS or EDI vendors | Web, Application Monitoring & ITSM | `search_security_advisories`, `get_known_exploited_vulnerabilities`, `get_vendor_software_inventory` |
| Q5 | Cost and recovery time of ransomware on warehouse systems | Application Monitoring & ITSM, Warehouse Management System (WMS), Order Management System (OMS), Identity & Security Platform, Web | `get_critical_system_dependencies`, `get_recovery_time_and_backup_status`, `get_daily_throughput_and_revenue_at_risk`, `get_unpatched_exposure_by_system`, `calculate_ransomware_downtime_cost`, `search_web` |

## 87. Chief supply chain officer

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | End-to-end performance briefing vs plan: top five issues, causes, quarter-fixable | Executive KPI Scorecard, BI & Dashboards Platform, Budgeting & Forecasting Tool, Inventory Management System (IMS), Risk Management System, Carbon & ESG Reporting Platform, Documents, Email & Calendar | `get_executive_scorecard`, `list_top_kpi_variances`, `get_budget_vs_actual_by_cost_centre`, `get_inventory_vs_plan`, `get_supply_risk_summary`, `get_emissions_vs_target`, `get_issue_root_causes`, `draft_executive_briefing`, `send_email` ✎ |
| Q2 | Three-year supply chain investments within £80m: return, risk, peers, sequenced roadmap | Strategy & Board Reporting Tool, Project & Portfolio Management Tool, Network Design Tool, Cost Modelling Tool, Budgeting & Forecasting Tool, Web, Documents | `list_strategic_initiatives`, `get_project_dependencies`, `run_network_design_scenario`, `calculate_investment_return`, `search_web`, `calculate_portfolio_under_budget_cap`, `draft_investment_roadmap`, `submit_investment_request` ✎ |
| Q3 | Resilience to major disruption, cost and scenario comparison | Risk Management System, Supplier Onboarding & Risk System, Network Design Tool, Code Execution | `list_disruption_scenarios`, `get_supplier_concentration_exposure`, `run_network_disruption_simulation`, `calculate_disruption_cost_impact`, `calculate_mitigation_return_per_pound` |
| Q4 | What are the best retailers doing in supply chain? | Web, Strategy & Board Reporting Tool | `search_web`, `fetch_web_page`, `get_company_strategic_priorities` |
| Q5 | Northampton DC cost per unit 18% above network: structural or fixable; start recovery initiative | Cost Allocation Tool, Labour Management System (LMS), Slotting & Layout Tool, Warehouse Management System (WMS), Code Execution | `get_dc_cost_per_unit_by_component`, `get_dc_labour_productivity`, `get_dc_layout_utilisation`, `get_dc_product_mix_and_volume`, `compare_dc_cost_to_network_average`, `create_improvement_initiative` ✎ |
| Q6 | How to organise supply chain for growth, with peer structures and transition risks | Web, HR Information System (HRIS), Strategy & Board Reporting Tool | `get_org_structure`, `search_web`, `fetch_web_page` |

## 88. COO / operations director

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Site performance on service, cost, safety, quality; largest underperformance and why | Executive KPI Scorecard, Warehouse Management System (WMS), Health & Safety System, Budgeting & Forecasting Tool, Email & Calendar | `get_site_scorecard`, `get_site_safety_incidents`, `get_site_quality_metrics`, `get_budget_vs_actual_by_cost_centre`, `get_issue_root_causes`, `create_calendar_event` ✎ |
| Q2 | Daventry productivity gap: layout, labour, systems or management; value of fixing | Labour Management System (LMS), Slotting & Layout Tool, Application Monitoring & ITSM, HR Information System (HRIS), Code Execution | `get_dc_labour_productivity`, `get_dc_layout_utilisation`, `get_wms_system_performance`, `get_site_management_structure`, `calculate_value_of_productivity_gap`, `create_improvement_initiative` ✎ |
| Q3 | Rank seven capex projects (£34m versus £22m): phasing, peak impact, portfolio; update tracker | Documents, Project & Portfolio Management Tool, Budgeting & Forecasting Tool, Demand Planning System, Risk Management System, Code Execution | `read_document`, `get_capex_project_business_cases`, `get_project_delivery_risk`, `calculate_peak_capacity_impact_by_project`, `run_portfolio_optimisation`, `draft_sponsor_challenge_brief`, `update_capex_project_status` ✎, `cancel_capex_project` ✎ |
| Q4 | Capacity and headcount needed for next peak and next year; biggest risk | Demand Planning System, Labour Management System (LMS), HR Information System (HRIS), Warehouse Management System (WMS), Recruitment / ATS | `get_volume_forecast`, `get_productivity_rates_by_site_and_role`, `get_current_headcount_by_site_and_skill`, `get_site_capacity_by_process`, `calculate_labour_requirement_by_site_week`, `calculate_capacity_gap_by_site`, `get_recruitment_lead_times`, `create_headcount_requisition` ✎ |
| Q5 | Where do we lead or lag on benchmarks? | Executive KPI Scorecard, Web | `get_kpi_actuals`, `search_industry_benchmarks`, `compare_kpis_to_benchmarks` |
| Q6 | In-source or outsource transport: five-year cost, control, risk, transition | Transport Management System (TMS), Fleet Telematics, Freight Rate Management System, Carrier Portal, Contract Management System, Cost Modelling Tool | `get_transport_spend_by_lane`, `get_fleet_operating_costs`, `get_market_rate_benchmarks`, `get_carrier_performance`, `get_contract_notice_periods`, `run_make_vs_buy_cost_model`, `calculate_five_year_tco_comparison` |

## 89. HR / workforce planner

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Peak headcount and skills by site and week, shortfall, recruit versus agency cost | Demand Planning System, Labour Management System (LMS), HR Information System (HRIS), Recruitment / ATS, Contract Management System, Code Execution | `get_volume_forecast`, `get_productivity_rates_by_site_and_role`, `get_current_headcount_by_site_and_skill`, `calculate_labour_requirement_by_site_week`, `get_recruitment_lead_times`, `get_recruitment_cost_per_hire`, `get_agency_rate_card`, `calculate_recruit_vs_agency_cost`, `create_job_requisition` ✎ |
| Q2 | Corby turnover 45% versus 28%: pay, shifts, management, commute, exit data | HR Information System (HRIS), Labour Management System (LMS), Web, Code Execution | `get_site_turnover_by_cohort`, `get_exit_interview_themes`, `get_pay_rates_vs_market`, `get_shift_pattern_and_overtime`, `get_site_management_structure`, `get_employee_commute_distances`, `run_analysis`, `create_pay_review_request` ✎ |
| Q3 | Warehouse labour market in our regions, pay comparison, upcoming employment law changes | Web, HR Information System (HRIS) | `get_regional_labour_market_data`, `get_pay_rates_vs_market`, `search_employment_law_changes`, `calculate_cost_of_pay_rise` |
| Q4 | Hire, agency, overtime or automate for peak? | Labour Management System (LMS), HR Information System (HRIS), Recruitment / ATS, Contract Management System, Project & Portfolio Management Tool | `get_cost_per_productive_hour_by_labour_type`, `get_quality_error_rate_by_labour_type`, `get_retention_by_labour_type`, `get_agency_rate_card`, `get_automation_option_cost_estimate`, `submit_agency_labour_request` ✎ |
| Q5 | Attrition, absence and time-to-hire by site and shift; worst spots and quickest fix; weekly report | HR Information System (HRIS), Recruitment / ATS, Labour Management System (LMS), BI & Dashboards Platform | `get_attrition_by_site_and_shift`, `get_absence_rate_by_site_and_shift`, `get_time_to_hire_by_site`, `list_recruitment_funnel_bottlenecks`, `get_exit_interview_themes`, `create_scheduled_report` ✎ |

## 90. Programme / transformation manager

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | ERP programme status on scope, time, budget, benefits; top risks, decisions, highlight report; send | Documents, Project & Portfolio Management Tool, Budgeting & Forecasting Tool, Email & Calendar | `read_document`, `list_raid_log_items`, `get_programme_plan_milestones`, `get_programme_budget_vs_actual`, `get_benefits_tracking`, `list_steering_committee_decisions_required`, `draft_highlight_report`, `send_email_with_attachment` ✎, `update_raid_log_item` ✎ |
| Q2 | Data migration three weeks behind: what is blocking it; raise blockers | Project & Portfolio Management Tool, Data Quality & Observability Tool, Master Data Management (MDM) | `get_migration_workstream_status`, `list_migration_defects_and_blockers`, `get_data_quality_scores_for_migration_objects`, `get_programme_resource_plan`, `create_raid_log_item` ✎, `reassign_programme_task` ✎ |
| Q3 | Scope, date, cost and resource trade-offs to recommend to steering committee | Project & Portfolio Management Tool, Budgeting & Forecasting Tool, Risk Management System, Code Execution | `get_programme_plan_milestones`, `get_programme_resource_plan`, `get_programme_budget_vs_actual`, `run_programme_scenario`, `calculate_option_cost_and_schedule_impact`, `create_change_request` ✎ |
| Q4 | Realistic completion date and cost versus dashboard; compare with typical overruns | Project & Portfolio Management Tool, Budgeting & Forecasting Tool, Data Quality & Observability Tool, Web, Code Execution | `get_programme_plan_milestones`, `get_burn_rate_history`, `get_migration_workstream_status`, `get_test_cycle_pass_rates`, `calculate_earned_value_forecast`, `search_programme_overrun_benchmarks`, `update_programme_status_rag` ✎ |
| Q5 | Lessons from similar retail ERP and WMS programmes | Web, Knowledge Base / Policy Library | `search_web`, `fetch_web_page`, `list_programme_lessons_learned` |
| Q6 | Cutover structure for new DC around peak: big bang, phased, parallel, rollback | Project & Portfolio Management Tool, Warehouse Management System (WMS), Demand Planning System, Risk Management System, Web | `get_cutover_plan`, `get_volume_forecast`, `list_cutover_risks`, `get_rollback_requirements`, `compare_cutover_options`, `search_web`, `delete_cutover_option` ✎, `create_programme_milestone` ✎ |

## Tool catalogue for this category

| Tool | System | R/W | One-line description |
|---|---|---|---|
| `block_user_account` | Identity & Security Platform | W | Locks a user account and revokes active sessions |
| `block_vendor_payment` | Accounts Payable System | W | Places a payment hold on a vendor |
| `calculate_baseline_delay_rate_by_supplier` | Code Execution | R | Simple baseline delay-rate benchmark per supplier |
| `calculate_benefit_of_accuracy_uplift` | Code Execution | R | Convert forecast accuracy gain into stock and service value |
| `calculate_business_risk_score` | Code Execution | R | Combine severity, exposure, exploitability and criticality |
| `calculate_capacity_gap_by_site` | Code Execution | R | Gap between required and available capacity by site and week |
| `calculate_cost_of_pay_rise` | Code Execution | R | Annual cost and expected retention effect of a pay change |
| `calculate_disruption_cost_impact` | Code Execution | R | Lost sales, expediting and recovery cost per scenario |
| `calculate_earned_value_forecast` | Code Execution | R | Earned-value estimate at completion and finish date |
| `calculate_five_year_tco_comparison` | Code Execution | R | Five-year total cost comparison by option |
| `calculate_forecast_backtest_error` | Code Execution | R | Backtest a forecast method against past periods and report error |
| `calculate_interface_headroom_at_peak` | Code Execution | R | Headroom per interface against forecast peak load |
| `calculate_investment_return` | Cost Modelling Tool | R | NPV, payback and sensitivity for an investment case |
| `calculate_kpi_forecast_range` | Code Execution | R | Project a KPI range (low/central/high) from history and volume forecast |
| `calculate_labour_requirement_by_site_week` | Code Execution | R | Required hours and heads from volume and productivity |
| `calculate_mitigation_return_per_pound` | Code Execution | R | Risk reduction per pound for each mitigation |
| `calculate_option_cost_and_schedule_impact` | Code Execution | R | Cost and schedule effect of each option |
| `calculate_peak_capacity_impact_by_project` | Code Execution | R | Peak capacity effect of funding or deferring each project |
| `calculate_portfolio_under_budget_cap` | Code Execution | R | Select and sequence projects within a budget envelope |
| `calculate_ransomware_downtime_cost` | Code Execution | R | Cost of downtime and manual workaround over a recovery period |
| `calculate_recruit_vs_agency_cost` | Code Execution | R | Compare cost of recruiting versus agency cover |
| `calculate_value_of_productivity_gap` | Code Execution | R | Annual value of closing a productivity gap |
| `cancel_capex_project` | Project & Portfolio Management Tool | W | Cancels a capex project and releases its budget |
| `compare_cutover_options` | Code Execution | R | Compare cutover approaches on risk, cost and duration |
| `compare_dc_cost_to_network_average` | Code Execution | R | Decompose a site's cost gap versus the network |
| `compare_edi_spec_to_wms_fields` | Code Execution | R | Map spec segments to target fields and list gaps |
| `compare_inventory_balances` | Data Warehouse / Lakehouse | R | Reconcile two inventory sources and itemise the differences |
| `compare_kpis_to_benchmarks` | Code Execution | R | Compare internal KPIs to benchmark ranges |
| `create_calendar_event` | Email & Calendar | W | Creates a calendar event and invites attendees |
| `create_change_request` | Application Monitoring & ITSM | W | Raises a change request for review and scheduling |
| `create_data_quality_ticket` | Data Quality & Observability Tool | W | Creates a ticket for a data quality issue |
| `create_headcount_requisition` | HR Information System (HRIS) | W | Creates a headcount requisition for a site and role |
| `create_improvement_initiative` | Project & Portfolio Management Tool | W | Creates an improvement initiative with owners and targets |
| `create_inventory_adjustment_journal` | ERP (General Ledger) | W | Posts a journal adjusting inventory valuation for an agreed reconciling difference |
| `create_job_requisition` | Recruitment / ATS | W | Opens a job requisition for recruitment |
| `create_load_test_run` | Application Monitoring & ITSM | W | Schedules a load test run against an interface |
| `create_model_alert_rule` | ML Platform / Model Registry | W | Adds a drift or accuracy alert rule to a model |
| `create_pay_review_request` | HR Information System (HRIS) | W | Logs a pay review request for a site or role group |
| `create_programme_milestone` | Project & Portfolio Management Tool | W | Adds a milestone to the programme plan |
| `create_project_task` | Project & Portfolio Management Tool | W | Adds a task to a project backlog |
| `create_raid_log_item` | Project & Portfolio Management Tool | W | Adds a risk, issue or dependency to the RAID log |
| `create_scheduled_report` | BI & Dashboards Platform | W | Schedules a recurring report to named recipients |
| `create_security_incident` | Identity & Security Platform | W | Opens a security incident record linked to alerts |
| `create_security_remediation_task` | Application Monitoring & ITSM | W | Creates a remediation task for a security finding |
| `create_warehouse_view` | Data Warehouse / Lakehouse | W | Creates a saved view in the warehouse from supplied SQL |
| `delete_cutover_option` | Project & Portfolio Management Tool | W | Removes an option from the cutover plan |
| `delete_model_alert_rule` | ML Platform / Model Registry | W | Removes an alert rule from a model |
| `draft_chart_pack` | Code Execution | R | Build a chart pack or slide draft from analysis outputs |
| `draft_executive_briefing` | Documents | R | Draft a briefing document from supplied findings |
| `draft_highlight_report` | Documents | R | Draft a programme highlight report |
| `draft_incident_summary` | Documents | R | Draft an incident summary for a named audience |
| `draft_investment_roadmap` | Documents | R | Draft a sequenced roadmap document |
| `draft_sponsor_challenge_brief` | Documents | R | Draft anticipated sponsor objections and responses |
| `fetch_web_page` | Web | R | Fetch and read a public web page |
| `get_3pl_integration_capabilities` | Supplier Relationship Management (SRM) | R | Integration methods a provider supports and supplied technical details |
| `get_absence_rate_by_site_and_shift` | HR Information System (HRIS) | R | Absence by site and shift |
| `get_agency_rate_card` | Contract Management System | R | Agency rates, mark-ups and notice terms |
| `get_alert_false_positive_history` | Identity & Security Platform | R | Past dispositions of similar alerts |
| `get_asn_feed_change_log` | Integration Platform / API Gateway | R | Change log and volume/completeness of the inbound ASN feed |
| `get_asn_timeliness_history` | Warehouse Management System (WMS) | R | ASN lead times and accuracy against receipts |
| `get_asset_business_criticality` | Application Monitoring & ITSM | R | Asset criticality and business service mapping from the CMDB |
| `get_attrition_by_site_and_shift` | HR Information System (HRIS) | R | Attrition by site and shift |
| `get_automation_option_cost_estimate` | Project & Portfolio Management Tool | R | Cost and lead time of automation options |
| `get_benefits_tracking` | Project & Portfolio Management Tool | R | Benefits realisation status |
| `get_budget_vs_actual_by_cost_centre` | Budgeting & Forecasting Tool | R | Spend against budget by cost centre |
| `get_burn_rate_history` | Budgeting & Forecasting Tool | R | Programme burn rate over time |
| `get_capex_project_business_cases` | Project & Portfolio Management Tool | R | Business cases for capex projects |
| `get_carrier_eta_vs_actual_by_lane` | Carrier Portal | R | Carrier-quoted ETAs versus actual arrivals by lane |
| `get_carrier_performance` | Carrier Portal | R | Carrier service and cost performance |
| `get_company_strategic_priorities` | Strategy & Board Reporting Tool | R | Strategic priorities and board-level targets |
| `get_connection_access_privileges` | Identity & Security Platform | R | Privileges and data scope of third-party accounts |
| `get_contract_notice_periods` | Contract Management System | R | Notice periods, exit terms and volume commitments |
| `get_cost_per_productive_hour_by_labour_type` | Labour Management System (LMS) | R | Cost per productive hour for permanent, agency and overtime labour |
| `get_critical_system_dependencies` | Application Monitoring & ITSM | R | Dependencies and recovery tiers of warehouse systems |
| `get_current_headcount_by_site_and_skill` | HR Information System (HRIS) | R | Current headcount and skills by site |
| `get_current_process_forecast_accuracy` | Demand Planning System | R | Accuracy of the existing forecasting process |
| `get_cutover_plan` | Project & Portfolio Management Tool | R | Cutover plan, freeze windows and dependencies |
| `get_daily_throughput_and_revenue_at_risk` | Order Management System (OMS) | R | Orders, units and revenue flowing through each system per day |
| `get_data_owner_for_dataset` | Master Data Management (MDM) | R | Data owner and steward for a dataset or domain |
| `get_data_quality_issue_impact` | BI & Dashboards Platform | R | Reports and KPIs affected by a data quality issue |
| `get_data_quality_scores_for_migration_objects` | Data Quality & Observability Tool | R | Quality scores of source data for migration objects |
| `get_dc_cost_per_unit_by_component` | Cost Allocation Tool | R | DC cost per unit split into labour, space, equipment and overhead |
| `get_dc_labour_productivity` | Labour Management System (LMS) | R | Units per labour hour by site and process |
| `get_dc_layout_utilisation` | Slotting & Layout Tool | R | Space utilisation and travel distance for a site |
| `get_dc_product_mix_and_volume` | Warehouse Management System (WMS) | R | Volume, profile and mix by site |
| `get_edi_error_log_summary` | Integration Platform / API Gateway | R | Aggregated error log by cause, map and partner |
| `get_edi_map_for_message_type` | Integration Platform / API Gateway | R | Current mapping for an EDI message type |
| `get_edi_partner_status` | Wholesale / EDI Portal | R | Connection status and recent activity of an EDI partner |
| `get_emissions_vs_target` | Carbon & ESG Reporting Platform | R | Emissions against reduction targets |
| `get_employee_commute_distances` | HR Information System (HRIS) | R | Home-to-site distances for employees |
| `get_erp_order_header_and_charges` | ERP (General Ledger) | R | Order headers, revenue and charges from the ERP |
| `get_executive_scorecard` | Executive KPI Scorecard | R | Headline KPIs against plan across domains |
| `get_exit_interview_themes` | HR Information System (HRIS) | R | Exit reasons and themes by site |
| `get_failed_edi_messages` | Wholesale / EDI Portal | R | Failed EDI messages with partner, type and error code |
| `get_feature_drift_report` | ML Platform / Model Registry | R | Input and prediction drift statistics for a model |
| `get_fleet_operating_costs` | Fleet Telematics | R | Fleet running costs, utilisation and age |
| `get_forecast_error_by_category` | Demand Planning System | R | Forecast error and bias by category and period |
| `get_incident_response_playbook` | Knowledge Base / Policy Library | R | Incident response and escalation procedures |
| `get_integration_run_cost_by_pattern` | Integration Platform / API Gateway | R | Run and support cost per integration pattern |
| `get_interface_throughput_and_capacity` | Application Monitoring & ITSM | R | Current throughput and rated capacity per interface |
| `get_inventory_definition_policy` | Knowledge Base / Policy Library | R | Policy definition of inventory ownership, status and valuation |
| `get_inventory_valuation_by_site` | ERP (General Ledger) | R | Inventory value and provisions by site from the ledger |
| `get_inventory_vs_plan` | Inventory Management System (IMS) | R | Inventory against plan and cover targets |
| `get_ip_reputation` | Web | R | Reputation and geolocation of an IP address |
| `get_issue_recurrence_history` | Data Quality & Observability Tool | R | How often an issue has reopened or recurred |
| `get_issue_root_causes` | Executive KPI Scorecard | R | Recorded causes of off-plan KPIs |
| `get_known_exploited_vulnerabilities` | Web | R | Public feed of vulnerabilities exploited in the wild |
| `get_kpi_actuals` | Executive KPI Scorecard | R | Actual KPI results over a period |
| `get_kpi_definition` | Knowledge Base / Policy Library | R | Internal definition and calculation of a named KPI |
| `get_kpi_history` | Data Warehouse / Lakehouse | R | Historical monthly and weekly KPI series |
| `get_kpi_targets` | Executive KPI Scorecard | R | Targets and thresholds for each KPI |
| `get_market_rate_benchmarks` | Freight Rate Management System | R | Market and contract rate benchmarks by lane |
| `get_migration_workstream_status` | Project & Portfolio Management Tool | R | Migration progress by object and cycle |
| `get_model_accuracy_history` | ML Platform / Model Registry | R | Accuracy metrics over time for a model, by segment |
| `get_model_alert_rules` | Application Monitoring & ITSM | R | Configured monitoring alerts and thresholds for models |
| `get_model_backtest_results` | ML Platform / Model Registry | R | Backtest results of a candidate model against current process |
| `get_model_health_summary` | ML Platform / Model Registry | R | Current accuracy, drift and data freshness per model |
| `get_model_training_dataset_summary` | ML Platform / Model Registry | R | Training data window, volume and coverage for a model |
| `get_new_product_launch_history` | Data Warehouse / Lakehouse | R | Past new-product launches with early-life demand |
| `get_ocean_transit_history_by_lane` | Track & Trace Platform | R | Historical ocean transit times by lane, carrier and service |
| `get_org_structure` | HR Information System (HRIS) | R | Organisation structure and headcount by function |
| `get_otif_by_dimension` | Data Warehouse / Lakehouse | R | OTIF actuals sliced by supplier, category, DC, weekday and inbound mode for a period |
| `get_oversell_incidents` | Order Management System (OMS) | R | Orders cancelled or short-shipped for stock reasons |
| `get_pay_rates_vs_market` | HR Information System (HRIS) | R | Pay rates by site against local market data |
| `get_payment_history_by_supplier` | ERP (General Ledger) | R | Payment terms and actual payment timing by supplier |
| `get_payment_runs_for_changed_vendors` | Accounts Payable System | R | Payments made or queued to vendors with changed bank details |
| `get_peak_interface_load_history` | Application Monitoring & ITSM | R | Message volumes and latency during previous peaks |
| `get_pipeline_step_timings` | Application Monitoring & ITSM | R | Timing of each step in a data pipeline |
| `get_po_history_with_outcomes` | Purchase Order System | R | PO history with promised, confirmed and actual receipt dates |
| `get_port_congestion_history` | Track & Trace Platform | R | Port dwell and congestion history |
| `get_productivity_rates_by_site_and_role` | Labour Management System (LMS) | R | Standard and actual productivity rates by site and role |
| `get_programme_budget_vs_actual` | Budgeting & Forecasting Tool | R | Programme spend versus budget and forecast |
| `get_programme_plan_milestones` | Project & Portfolio Management Tool | R | Plan, milestones and forecast dates |
| `get_programme_resource_plan` | Project & Portfolio Management Tool | R | Resource plan and availability by workstream |
| `get_project_cost_estimate` | Project & Portfolio Management Tool | R | Cost estimate and resource plan for a delivery project |
| `get_project_delivery_risk` | Project & Portfolio Management Tool | R | Delivery risk rating and issues per project |
| `get_project_dependencies` | Project & Portfolio Management Tool | R | Dependencies between projects and programmes |
| `get_quality_error_rate_by_labour_type` | Labour Management System (LMS) | R | Error rate by labour type |
| `get_recovery_time_and_backup_status` | Application Monitoring & ITSM | R | RTO/RPO targets and last backup and restore tests |
| `get_recruitment_cost_per_hire` | Recruitment / ATS | R | Cost per hire by role and channel |
| `get_recruitment_lead_times` | Recruitment / ATS | R | Time to hire and onboarding lead times by role |
| `get_regional_labour_market_data` | Web | R | Regional unemployment and vacancy data |
| `get_retention_by_labour_type` | HR Information System (HRIS) | R | Retention by hire route and labour type |
| `get_rollback_requirements` | Warehouse Management System (WMS) | R | Data and process requirements for rolling back a site |
| `get_shift_pattern_and_overtime` | Labour Management System (LMS) | R | Shift patterns and overtime hours by site |
| `get_site_capacity_by_process` | Warehouse Management System (WMS) | R | Rated capacity by site and process |
| `get_site_management_structure` | HR Information System (HRIS) | R | Management spans, vacancies and tenure at a site |
| `get_site_quality_metrics` | Executive KPI Scorecard | R | Quality metrics by site |
| `get_site_safety_incidents` | Health & Safety System | R | Incident and near-miss rates by site |
| `get_site_scorecard` | Executive KPI Scorecard | R | Service, cost, safety and quality results for each site |
| `get_site_turnover_by_cohort` | HR Information System (HRIS) | R | Turnover by site, tenure, shift and manager |
| `get_stock_feed_latency` | Integration Platform / API Gateway | R | End-to-end latency of the stock feed to the website |
| `get_stock_position_by_site` | Inventory Management System (IMS) | R | Operational stock units and value by site and status |
| `get_supplier_concentration_exposure` | Supplier Onboarding & Risk System | R | Spend and volume concentration by supplier and country |
| `get_supplier_portal_access_log` | Supplier Portal | R | Pages and records accessed in the supplier portal |
| `get_supplier_scorecard_history` | Supplier Relationship Management (SRM) | R | Supplier scorecard history by period |
| `get_supplier_security_risk_rating` | Supplier Onboarding & Risk System | R | Security and risk rating of a supplier |
| `get_supply_risk_summary` | Risk Management System | R | Top supply chain risks with ratings and mitigations |
| `get_table_schema` | Data Warehouse / Lakehouse | R | Columns, keys and grain of a table |
| `get_test_cycle_pass_rates` | Project & Portfolio Management Tool | R | Test execution and pass rates |
| `get_time_to_hire_by_site` | Recruitment / ATS | R | Time to hire by site and role |
| `get_tms_freight_cost_by_shipment` | Transport Management System (TMS) | R | Freight cost and shipment-to-order links per shipment |
| `get_transport_spend_by_lane` | Transport Management System (TMS) | R | Transport cost and volume by lane and mode |
| `get_unpatched_exposure_by_system` | Identity & Security Platform | R | Unpatched and externally exposed vulnerabilities per system |
| `get_user_session_history` | Identity & Security Platform | R | Sessions and actions taken by a user account |
| `get_vendor_software_inventory` | Application Monitoring & ITSM | R | Applications, versions and vendors in the CMDB |
| `get_volume_forecast` | Demand Planning System | R | Volume forecast by site, channel and week, including peak |
| `get_weather_events_by_region` | Web | R | Weather and severe-event data by region and date |
| `get_website_vs_wms_stock_variance` | Inventory Management System (IMS) | R | Differences between site-displayed and WMS stock |
| `get_wms_inbound_field_schema` | Warehouse Management System (WMS) | R | WMS inbound ASN and receipt data model |
| `get_wms_labour_and_handling_cost_by_order` | Warehouse Management System (WMS) | R | Pick, pack and handling cost drivers per order |
| `get_wms_system_performance` | Application Monitoring & ITSM | R | WMS response times and incident counts for a site |
| `list_controls_in_place_for_connection` | Identity & Security Platform | R | Existing controls such as MFA, IP allow-lists and logging |
| `list_cutover_risks` | Risk Management System | R | Cutover and go-live risks with ratings |
| `list_data_quality_issues` | Data Quality & Observability Tool | R | Open data quality issues with severity, dataset and age |
| `list_disruption_scenarios` | Risk Management System | R | Defined disruption scenarios with likelihood estimates |
| `list_feature_store_features` | ML Platform / Model Registry | R | Features available in the feature store with lineage and freshness |
| `list_inventory_adjustments_and_cutoffs` | Inventory Management System (IMS) | R | Adjustments, in-transit and period cut-off items affecting stock balances |
| `list_kpi_definition_changes` | Knowledge Base / Policy Library | R | Change history of KPI definitions and calculation rules |
| `list_load_test_history` | Application Monitoring & ITSM | R | Previous load tests and results |
| `list_migration_defects_and_blockers` | Project & Portfolio Management Tool | R | Open migration defects and blockers |
| `list_model_retraining_schedule` | ML Platform / Model Registry | R | Last and next retraining dates for each model |
| `list_open_security_alerts` | Identity & Security Platform | R | Open security alerts with severity and asset |
| `list_pipeline_and_schema_changes` | Data Quality & Observability Tool | R | Upstream pipeline, schema and source changes in a date range |
| `list_programme_lessons_learned` | Knowledge Base / Policy Library | R | Internal lessons-learned records from past programmes |
| `list_raid_log_items` | Project & Portfolio Management Tool | R | RAID items with status, owner and last action |
| `list_recent_mapping_and_config_changes` | Integration Platform / API Gateway | R | Recent changes to maps, certificates and endpoint configuration |
| `list_recruitment_funnel_bottlenecks` | Recruitment / ATS | R | Stage conversion and delay in the hiring funnel |
| `list_registered_models` | ML Platform / Model Registry | R | Production models with owner, version and status |
| `list_releases_and_change_requests` | Application Monitoring & ITSM | R | Releases and change records affecting systems in a date range |
| `list_steering_committee_decisions_required` | Project & Portfolio Management Tool | R | Open decisions awaiting steering committee |
| `list_strategic_initiatives` | Strategy & Board Reporting Tool | R | Approved and proposed strategic initiatives with owners |
| `list_third_party_connections` | Integration Platform / API Gateway | R | Supplier and partner connections with protocol and owner |
| `list_top_kpi_variances` | Executive KPI Scorecard | R | Largest adverse variances against plan |
| `list_trading_partners_using_message_type` | Wholesale / EDI Portal | R | Partners sending a given message type |
| `list_vendor_bank_detail_changes` | Master Data Management (MDM) | R | Changes to vendor bank details with user and timestamp |
| `list_vulnerability_scan_findings` | Identity & Security Platform | R | Scanner findings with CVSS, asset and age |
| `read_document` | Documents | R | Read an attached or shared file and return its content |
| `reassign_data_quality_issue` | Data Quality & Observability Tool | W | Changes the owner assigned to a data quality issue |
| `reassign_programme_task` | Project & Portfolio Management Tool | W | Changes the owner of a programme task |
| `run_analysis` | Code Execution | R | Execute Python/SQL analysis in a sandbox and return tables and charts |
| `run_data_quality_checks` | Data Quality & Observability Tool | R | Run completeness, timeliness and consistency checks on a dataset |
| `run_make_vs_buy_cost_model` | Cost Modelling Tool | R | Model in-house versus outsourced cost over a horizon |
| `run_network_design_scenario` | Network Design Tool | R | Model a network scenario for cost, service and capacity |
| `run_network_disruption_simulation` | Network Design Tool | R | Simulate loss of a node or lane on service and cost |
| `run_portfolio_optimisation` | Code Execution | R | Optimise a project portfolio for return within constraints |
| `run_programme_scenario` | Project & Portfolio Management Tool | R | Re-plan the programme under a scope, date or resource change |
| `run_sql_query` | Data Warehouse / Lakehouse | R | Run a read-only SQL query against the warehouse |
| `search_auth_logs` | Identity & Security Platform | R | Query authentication events by user, IP, time and result |
| `search_data_catalogue` | Data Warehouse / Lakehouse | R | Search the data catalogue for tables and fields |
| `search_employment_law_changes` | Web | R | Announced employment law changes |
| `search_industry_benchmarks` | Web | R | Public benchmarks for supply chain KPIs |
| `search_knowledge_base_articles` | Knowledge Base / Policy Library | R | Search policies, standards and runbooks |
| `search_open_source_packages` | Web | R | Search code repositories and package indexes for implementations |
| `search_programme_overrun_benchmarks` | Web | R | Published overrun rates for similar programmes |
| `search_security_advisories` | Web | R | Search vendor and CERT security advisories |
| `search_web` | Web | R | Search the public web |
| `send_email` | Email & Calendar | W | Sends an email to named recipients |
| `send_email_with_attachment` | Email & Calendar | W | Sends an email with attached files to named recipients |
| `submit_agency_labour_request` | Recruitment / ATS | W | Submits a request for agency labour by site, shift and dates |
| `submit_edi_message_reprocess` | Wholesale / EDI Portal | W | Resubmits failed EDI messages for processing |
| `submit_investment_request` | Project & Portfolio Management Tool | W | Submits a funding request for an initiative for approval |
| `submit_model_retraining_job` | ML Platform / Model Registry | W | Starts a retraining run for a registered model on a chosen dataset |
| `update_capex_project_status` | Project & Portfolio Management Tool | W | Sets the status or phasing of a capex project |
| `update_kpi_alert_threshold` | Executive KPI Scorecard | W | Changes the alert threshold on a KPI |
| `update_programme_status_rag` | Project & Portfolio Management Tool | W | Sets the RAG status of a programme |
| `update_raid_log_item` | Project & Portfolio Management Tool | W | Updates the status or details of a RAID log item |
| `update_security_alert_status` | Identity & Security Platform | W | Sets the status of a security alert, such as closed as false positive |
| `update_stock_feed_schedule` | Integration Platform / API Gateway | W | Changes the run frequency or batch setting of the stock feed |
