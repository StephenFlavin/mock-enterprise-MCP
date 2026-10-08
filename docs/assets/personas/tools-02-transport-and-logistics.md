# Systems and MCP tools · 02 Transport and Logistics

For each question in the Transport and Logistics persona set, this file lists the enterprise systems that must be reached and the MCP tool methods an AI agent would call to answer it.
Tool names are entity-scoped and shared with the other categories so the benchmark stays consistent. Row numbers match the questions file.
Follow-up questions are covered by the main row unless they need an extra system.

**Legend:** `Q` = question number in the questions file · tools are listed in likely call order · ✎ marks a write or side-effect tool (drafts are `draft_` and are not writes).

## 11. Transport planner

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Any lane disruptions this week? | Transport Management System (TMS), Carrier Portal, Track & Trace Platform, Web | `get_lane_performance_summary`, `list_shipment_exceptions_by_lane`, `search_carrier_service_alerts`, `get_lane_fill_rate_trend`, `search_web`, `reassign_shipment_to_carrier` ✎ |
| Q2 | Northern region: current three carriers versus moving 40% to a pallet network; cost, OTP, contract terms | Transport Management System (TMS), Freight Rate Management System, Carrier Portal, Contract Management System, Documents | `read_document`, `get_load_volumes_by_lane`, `get_carrier_rate_card`, `get_pallet_network_rate_card`, `get_carrier_on_time_performance`, `get_contract_terms`, `calculate_lane_cost_scenario`, `draft_negotiation_brief`, `create_carrier_trial_allocation` ✎ |
| Q3 | What could disrupt main lanes before Christmas, and which shipments fall in those windows? | Web, Transport Management System (TMS), Track & Trace Platform | `search_web`, `fetch_web_page`, `list_planned_shipments_by_date_window`, `list_open_shipments_by_lane`, `run_analysis`, `update_shipment_routing` ✎ |
| Q4 | Black Friday and Christmas capacity needed by lane versus contracted; where exposed?; request extra capacity | Demand Planning System, Transport Management System (TMS), Contract Management System, Freight Rate Management System | `get_peak_volume_forecast_by_lane`, `get_contracted_capacity_by_lane`, `calculate_capacity_gap_by_lane`, `get_prior_peak_capacity_utilisation`, `get_spot_market_rates_by_lane`, `send_capacity_request_to_carrier` ✎ |
| Q5 | Routes planned at 94% utilisation but drivers run out of hours on M62 routes; why?; re-plan worst two | Transport Management System (TMS), Fleet Telematics | `get_route_plan_utilisation`, `list_routes_with_hours_breaches`, `get_driver_hours_compliance_by_route`, `get_planned_stop_time_assumptions`, `get_actual_stop_durations_by_route`, `run_analysis`, `update_route_plan` ✎, `update_planned_stop_time_assumption` ✎ |

## 12. Freight forwarder / ocean freight buyer

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Spot and contract 40ft rates from Ho Chi Minh to three ports, 12-week trend | Freight Rate Management System, Freight Forwarder Portal, Web | `get_spot_container_rates_by_lane`, `get_contract_container_rates_by_lane`, `get_rate_trend_by_lane`, `search_web` |
| Q2 | Carrier A contract expires January: renew, cut or switch? Compare B and C, draft tender terms | Freight Forwarder Portal, Carrier Portal, Container Visibility Platform, Contract Management System, Sourcing / RFx Platform | `get_carrier_schedule_reliability`, `get_roll_rate_by_carrier_and_lane`, `get_carrier_share_of_volume`, `get_contract_terms`, `compare_carrier_performance`, `run_analysis`, `draft_tender_criteria`, `create_tender_event` ✎, `send_tender_invitation` ✎ |
| Q3 | Will rates spike before Lunar New Year? | Freight Rate Management System, Commodity & Market Data Feed, Web | `get_rate_index_history`, `get_contract_vs_spot_mix`, `search_web` |
| Q4 | 18% of Asia-Europe bookings rolled; which carriers, ports and behaviours explain it? | Freight Forwarder Portal, Container Visibility Platform, Transport Management System (TMS) | `list_rolled_bookings`, `get_roll_rate_by_carrier_and_lane`, `get_booking_lead_time_vs_roll_outcome`, `get_port_congestion_status`, `get_demurrage_and_detention_for_bookings`, `get_air_freight_cost_for_rolled_bookings`, `run_analysis` |
| Q5 | Carrier blank sailings and surcharges for next two months; does it hit us?; move hit bookings | Freight Forwarder Portal, Carrier Portal, Freight Rate Management System, Web | `search_carrier_blank_sailing_notices`, `search_carrier_surcharge_announcements`, `list_planned_bookings`, `calculate_surcharge_impact_on_bookings`, `search_web`, `update_booking_sailing` ✎, `cancel_ocean_booking` ✎ |
| Q6 | Route Europe-bound boxes via Valencia or Piraeus plus rail instead of northern ports? | Freight Forwarder Portal, Freight Rate Management System, Container Visibility Platform, Track & Trace Platform, Landed Cost Calculator, Web | `get_historical_container_volumes_by_route`, `get_ocean_and_rail_rate_quote`, `get_port_congestion_status`, `get_rail_leg_reliability`, `get_transit_time_history_by_route`, `calculate_door_to_door_cost`, `search_web` |

## 13. Air freight coordinator

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Style 7731 three weeks late: is airfreighting 6,000 units worth it?; book if worthwhile | Purchase Order System, Demand Planning System, Freight Rate Management System, Costing & Margin Tool | `get_purchase_order_status_for_style`, `get_sales_forecast_for_style`, `get_air_freight_quote`, `get_style_unit_margin`, `calculate_lost_sales_if_delayed`, `calculate_air_vs_sea_margin_impact`, `create_air_freight_booking` ✎ |
| Q2 | £420k air spend last quarter: categorise by cause and supplier, how much avoidable? | Freight Forwarder Portal, Transport Management System (TMS), Purchase Order System, Contract Management System, Supplier Portal | `list_air_freight_invoices`, `get_air_shipment_reason_codes`, `get_air_spend_by_supplier`, `calculate_avoidable_air_spend`, `get_supplier_chargeback_clauses`, `run_analysis`, `send_supplier_chargeback_notice` ✎ |
| Q3 | Air rates out of Dhaka at the moment? | Freight Rate Management System, Freight Forwarder Portal, Web | `get_air_freight_rates_by_origin`, `get_air_rate_history`, `search_dangerous_goods_restrictions` |
| Q4 | Air freight budget for peak, based on current supplier delays and on-time record | Purchase Order System, Supplier Portal, Freight Rate Management System, Budgeting & Forecasting Tool | `list_open_purchase_orders_with_delay`, `get_supplier_on_time_delivery_history`, `get_historical_air_freight_spend`, `get_air_freight_rates_by_origin`, `calculate_expected_air_requirement`, `run_analysis`, `update_budget_line` ✎ |
| Q5 | 500 hero units, 12-day deadline: straight air, sea-air via Dubai or split; recommend, cut-offs; book once confirmed | Purchase Order System, Freight Forwarder Portal, Landed Cost Calculator, Customs & Trade Compliance System | `get_purchase_order_line_status`, `get_air_freight_quote`, `get_sea_air_routing_quote`, `calculate_landed_cost_per_unit`, `calculate_delivery_date_probability`, `check_dangerous_goods_restrictions`, `get_booking_cut_off_times`, `draft_forwarder_booking_request`, `create_air_freight_booking` ✎, `cancel_sea_freight_booking` ✎ |

## 14. Customs and trade compliance specialist

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Current duties and extra tariffs on HS 6110 from three countries into UK, EU, US; 12-month changes | Customs & Trade Compliance System, Tax & Duty System, Web | `get_tariff_rates_by_hs_code_and_country`, `get_additional_tariffs_and_trade_remedies`, `get_tariff_change_history`, `search_preferential_trade_agreements`, `get_required_origin_documents`, `calculate_duty_per_value`, `search_web` |
| Q2 | HS code for padded gilet with detachable fleece liner; rulings, duty difference, evidence to hold | Customs & Trade Compliance System, Product Lifecycle Management (PLM), Product Compliance & Regulatory Database, Web | `get_product_bill_of_materials`, `search_hs_codes`, `search_classification_rulings`, `get_tariff_rates_by_hs_code_and_country`, `calculate_duty_difference_between_codes`, `draft_classification_evidence_checklist`, `create_binding_ruling_application` ✎ |
| Q3 | Eleven shipments from one supplier held at customs; what do they have in common?; ask broker to amend open ones | Customs & Trade Compliance System, Purchase Order System, Tax & Duty System | `list_customs_holds_by_supplier`, `get_customs_declaration_details`, `get_customs_query_correspondence`, `list_historic_declarations_by_supplier`, `run_analysis`, `calculate_duty_reassessment_exposure`, `draft_corrective_action_plan`, `send_broker_amendment_request` ✎ |
| Q4 | Cost impact of a 15% Vietnam footwear tariff on 2027 buy by category, and mitigations | Merchandise Financial Planning, Customs & Trade Compliance System, Landed Cost Calculator, Costing & Margin Tool, Web | `get_planned_buy_by_category_and_country`, `get_tariff_rates_by_hs_code_and_country`, `calculate_tariff_cost_impact`, `get_factory_cost_quotes_by_country`, `calculate_landed_cost_per_unit`, `calculate_margin_recovery_from_price_change`, `search_web` |
| Q5 | Do we qualify for UK-Vietnam preferential rates? | Customs & Trade Compliance System, Product Lifecycle Management (PLM), Knowledge Base / Policy Library, Web | `search_preferential_trade_agreements`, `get_rules_of_origin_for_hs_code`, `get_product_bill_of_materials`, `get_fabric_origin_by_style`, `search_knowledge_base` |
| Q6 | Forced-labour import rules affecting cotton and polysilicon products; where could we be stopped? | Supply Chain Due Diligence Platform, Supplier Onboarding & Risk System, Customs & Trade Compliance System, Web, Purchase Order System | `search_web`, `list_suppliers_by_raw_material`, `get_forced_labour_risk_by_supplier`, `get_supplier_traceability_evidence`, `list_customs_detentions`, `block_purchase_orders_for_supplier` ✎ |
| Q7 | Would bonded warehouse or inward processing relief help on Ireland and EU re-exports? | Customs & Trade Compliance System, Tax & Duty System, Warehouse Management System (WMS), Web | `get_reexport_volumes_by_destination`, `search_bonded_warehouse_and_ipr_rules`, `get_customs_authorisation_conditions`, `calculate_duty_deferral_benefit`, `calculate_cash_flow_benefit`, `get_stock_movements_for_reexport_goods`, `create_customs_authorisation_application` ✎ |
| Q8 | How do de minimis changes affect cross-border DTC orders at £62 basket? | Customs & Trade Compliance System, E-commerce Platform, Tax & Duty System, Competitor Price Monitoring Tool, Web | `search_web`, `get_de_minimis_thresholds_by_country`, `get_cross_border_order_baskets`, `calculate_import_duty_and_vat_per_order`, `search_competitor_delivery_terms` |

## 16. Last-mile delivery manager

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | First-attempt delivery success fell from 93% to 88%; analyse by courier, region, product, option | Last-Mile Delivery Platform, Order Management System (OMS), Customer Service Platform | `get_first_attempt_success_trend`, `get_first_attempt_failures_by_dimension`, `list_failed_delivery_reasons`, `get_address_validation_failure_rate`, `list_worst_postcodes_by_failed_delivery`, `calculate_repeat_delivery_cost`, `run_analysis` |
| Q2 | Shift 20% of London volume from Courier A to B? Compare performance, design six-week trial | Last-Mile Delivery Platform, Carrier Portal, Contract Management System, Customer Service Platform, Web | `get_courier_scorecard`, `get_cost_per_drop_by_courier`, `get_damage_rate_by_courier`, `get_complaint_rate_by_courier`, `search_web`, `run_analysis`, `draft_courier_trial_plan`, `create_courier_allocation_rule` ✎, `update_courier_allocation_rule` ✎ |
| Q3 | Where will courier delays be worst in peak, and what capacity do we need by region? | Last-Mile Delivery Platform, Demand Planning System, Carrier Portal | `get_historical_peak_delivery_performance`, `list_worst_delivery_days`, `get_peak_order_volume_forecast_by_region`, `get_courier_capacity_commitments`, `calculate_courier_capacity_gap_by_region`, `get_courier_cut_off_times` |
| Q4 | New low-emission zone, parking and delivery-time rules in top 10 cities; effect on cost per drop | Web, Last-Mile Delivery Platform, Freight Rate Management System | `search_web`, `fetch_web_page`, `get_delivery_volumes_by_city`, `calculate_cost_per_drop_impact`, `search_competitor_delivery_practices` |
| Q5 | "Where is my order" contacts up about 30%; why?; enable proactive alerts | Customer Service Platform, Last-Mile Delivery Platform, Track & Trace Platform | `get_wismo_contact_trend`, `get_wismo_contacts_by_reason`, `list_orders_with_missed_scans`, `get_delivery_promise_accuracy`, `get_tracking_update_latency`, `calculate_notification_impact_estimate`, `update_notification_rule` ✎ |

## 19. Control tower analyst

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Which in-transit shipments will arrive late, by how much, and which SKUs could stock out? | Track & Trace Platform, Container Visibility Platform, Transport Management System (TMS), Inventory Management System (IMS), Demand Planning System | `list_in_transit_shipments`, `get_predicted_eta_vs_planned_arrival`, `list_skus_on_shipment`, `get_store_stock_cover_by_sku`, `calculate_stockout_risk`, `get_expected_lost_sales`, `get_dwell_time_by_node`, `list_mitigation_options`, `update_shipment_priority` ✎, `send_expedite_request_to_forwarder` ✎ |
| Q2 | Anything in next two weeks threatening vessels or key ports; which containers exposed? | Web, Container Visibility Platform, Track & Trace Platform | `search_web`, `fetch_web_page`, `list_vessels_and_containers_in_transit`, `get_port_status_and_congestion`, `get_container_value`, `get_historical_disruption_durations` |
| Q3 | Vessel anchored outside Rotterdam six days: wait, transship or fly; identify priority boxes, draft alert; send alert once approved | Container Visibility Platform, Freight Forwarder Portal, Inventory Management System (IMS), Allocation & Replenishment System, Collaboration & Messaging (Slack/Teams) | `get_vessel_position_and_status`, `list_containers_on_vessel`, `get_container_sku_contents`, `get_store_stock_cover_by_sku`, `get_transshipment_options`, `get_air_freight_quote`, `calculate_option_cost_and_service_impact`, `get_past_disruption_costs`, `draft_stakeholder_alert`, `send_stakeholder_alert` ✎ |
| Q4 | ETA accuracy on Asia-UK lane poor; compare predicted versus actual and find the cause | Track & Trace Platform, Container Visibility Platform, Transport Management System (TMS), Data Warehouse / Lakehouse | `get_predicted_vs_actual_arrivals_by_lane`, `get_carrier_eta_update_accuracy`, `get_port_dwell_time_history`, `get_inland_leg_transit_variance`, `run_analysis`, `calculate_planning_buffer_savings`, `update_planning_buffer_for_lane` ✎ |
| Q5 | Northern Europe port closure for two or four weeks: stock cover by category, stores hit first | Container Visibility Platform, Supply Planning System (MRP/DRP), Allocation & Replenishment System, Inventory Management System (IMS) | `list_inbound_containers_via_port`, `get_stock_cover_by_category_and_store`, `run_port_closure_scenario`, `calculate_stock_reallocation_plan`, `run_analysis` |
| Q6 | This week's top 10 disruptions; post to leadership channel | Track & Trace Platform, Container Visibility Platform, Risk Management System, Web, Collaboration & Messaging (Slack/Teams) | `list_active_disruptions`, `get_disruption_impact_on_shipments`, `list_new_disruptions_since`, `search_web`, `draft_leadership_briefing`, `send_channel_message` ✎ |

## 20. Carrier relationship manager

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | 12 months of carrier invoices versus contracted rates; overcharges and dispute letter; submit dispute once approved | Documents, Accounts Payable System, Contract Management System, Carrier Portal | `read_document`, `list_carrier_invoice_lines`, `get_carrier_contract_rates`, `compare_invoice_to_contract_rate`, `calculate_dispute_value_by_charge_type`, `get_contract_claim_time_limits`, `draft_dispute_letter`, `submit_carrier_invoice_dispute` ✎ |
| Q2 | Are our parcel rates competitive? | Freight Rate Management System, Transport Management System (TMS), Carrier Portal, Web | `get_parcel_rates_by_service`, `get_parcel_volumes_by_service`, `get_market_benchmark_rates`, `compare_rates_to_benchmark`, `search_web` |
| Q3 | Which carriers to award, reduce or exit in next tender, and why? | Transport Management System (TMS), Carrier Portal, Contract Management System, Freight Rate Management System | `get_carrier_scorecard`, `get_carrier_spend_and_volume`, `get_carrier_on_time_performance`, `get_carrier_claims_history`, `run_tender_award_scenario`, `calculate_scenario_cost_and_service`, `get_carrier_concentration_risk`, `remove_carrier_from_lane_allocation` ✎ |
| Q4 | Expected carrier rate increases next year and budget impact | Carrier Portal, Freight Rate Management System, Budgeting & Forecasting Tool, Web | `search_carrier_rate_increase_announcements`, `search_web`, `get_carrier_contract_rate_review_clauses`, `get_annual_carrier_spend_forecast`, `calculate_budget_impact_of_rate_increase` |
| Q5 | Carrier B damage claims doubled in Q3; why? | Carrier Portal, Warehouse Management System (WMS), Transport Management System (TMS), Contract Management System | `list_damage_claims_by_carrier`, `get_damage_claims_by_dimension`, `get_carrier_liability_terms`, `calculate_recoverable_claim_value`, `run_analysis`, `submit_carrier_damage_claim` ✎ |
| Q6 | Write tender scorecard criteria and weights based on what hurt us most; save as tender template | Transport Management System (TMS), Carrier Portal, Sourcing / RFx Platform, Knowledge Base / Policy Library | `list_carrier_incidents_for_period`, `get_carrier_service_failure_costs`, `search_knowledge_base`, `draft_tender_scorecard`, `get_carrier_scorecard`, `calculate_carrier_weighted_scores`, `create_tender_scorecard_template` ✎ |

## 21. Reverse logistics manager

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | How many returns next week, and what drives the top styles? | Returns Management System (RMS), Demand Planning System, Customer Reviews & Feedback Platform, Quality Management System (QMS) | `get_return_forecast_by_week`, `list_top_returned_styles`, `get_return_reasons_by_style`, `get_customer_feedback_themes_by_style`, `get_supplier_qa_results_by_style`, `calculate_return_reduction_savings`, `create_quality_review_request` ✎ |
| Q2 | Electronics accessories returns: restock, refurbish, liquidate or recycle; which route to change first | Returns Management System (RMS), Inventory Management System (IMS), Costing & Margin Tool, Packaging Compliance & EPR System, Web | `get_returns_grading_data`, `get_disposition_route_outcomes`, `get_handling_cost_by_disposition_route`, `get_return_item_age_profile`, `get_liquidator_recovery_rates`, `calculate_recovered_value_by_route`, `calculate_annual_disposition_change_value`, `run_analysis`, `update_disposition_rule` ✎, `delete_disposition_rule` ✎ |
| Q3 | January returns volume, returns centre capacity and agency staff needed; request agency staff | Returns Management System (RMS), Demand Planning System, Labour Management System (LMS), Warehouse Management System (WMS) | `get_return_forecast_by_week`, `get_historical_weekly_returns`, `get_returns_centre_capacity`, `get_labour_productivity_standards`, `calculate_returns_staffing_requirement`, `create_agency_labour_request` ✎ |
| Q4 | Returned goods and EPR rules in Germany, France, Netherlands; penalties and conflicts | Packaging Compliance & EPR System, Returns Management System (RMS), Knowledge Base / Policy Library, Web | `search_web`, `fetch_web_page`, `get_epr_registrations_by_country`, `list_epr_reporting_obligations`, `get_returns_handling_practices`, `search_knowledge_base` |
| Q5 | Should we charge for returns in some countries? Effect on returns, conversion, margin | E-commerce Platform, Order Management System (OMS), Returns Management System (RMS), Customer Data Platform (CDP), Web | `get_return_rates_by_market`, `get_conversion_and_basket_history_by_market`, `get_return_cost_per_order`, `get_customer_segment_return_behaviour`, `search_competitor_returns_policies`, `calculate_returns_charge_impact`, `draft_returns_charge_trial_plan`, `create_returns_charge_trial` ✎ |

## Tool catalogue for this category

| Tool | System | R/W | One-line description |
|---|---|---|---|
| `block_purchase_orders_for_supplier` | Purchase Order System | W | Places a hold on open purchase orders for a supplier |
| `calculate_air_vs_sea_margin_impact` | Costing & Margin Tool | R | Compares margin under air versus sea |
| `calculate_annual_disposition_change_value` | Returns Management System (RMS) | R | Annual value of disposition change |
| `calculate_avoidable_air_spend` | Accounts Payable System | R | Splits air spend into avoidable and unavoidable |
| `calculate_budget_impact_of_rate_increase` | Budgeting & Forecasting Tool | R | Budget impact of rate increases |
| `calculate_capacity_gap_by_lane` | Transport Management System (TMS) | R | Compares forecast demand with contracted capacity per lane |
| `calculate_carrier_weighted_scores` | Sourcing / RFx Platform | R | Weighted scores by carrier |
| `calculate_cash_flow_benefit` | Tax & Duty System | R | Cash flow benefit of a regime |
| `calculate_cost_per_drop_impact` | Last-Mile Delivery Platform | R | Cost per drop impact of rules |
| `calculate_courier_capacity_gap_by_region` | Last-Mile Delivery Platform | R | Courier capacity gap by region |
| `calculate_delivery_date_probability` | Freight Forwarder Portal | R | Probability of meeting a delivery date per routing option |
| `calculate_dispute_value_by_charge_type` | Accounts Payable System | R | Disputable value of invoice variances by charge category |
| `calculate_door_to_door_cost` | Landed Cost Calculator | R | Door-to-door cost for a routing option |
| `calculate_duty_deferral_benefit` | Tax & Duty System | R | Duty deferral benefit of a customs regime |
| `calculate_duty_difference_between_codes` | Tax & Duty System | R | Duty difference between HS codes |
| `calculate_duty_per_value` | Tax & Duty System | R | Duty per value of goods by route |
| `calculate_duty_reassessment_exposure` | Tax & Duty System | R | Exposure if past declarations are reassessed |
| `calculate_expected_air_requirement` | Supplier Portal | R | Expected air freight requirement from delays and OTD |
| `calculate_import_duty_and_vat_per_order` | Tax & Duty System | R | Duty and VAT per cross-border order |
| `calculate_landed_cost_per_unit` | Landed Cost Calculator | R | Landed cost per unit including freight and duty |
| `calculate_lane_cost_scenario` | Transport Management System (TMS) | R | Costs a lane or carrier mix scenario from volumes and rate cards |
| `calculate_lost_sales_if_delayed` | Costing & Margin Tool | R | Estimates sales lost if delivery is late |
| `calculate_margin_recovery_from_price_change` | Costing & Margin Tool | R | Margin recovered under price changes |
| `calculate_notification_impact_estimate` | Customer Service Platform | R | Contact reduction from proactive notifications |
| `calculate_option_cost_and_service_impact` | Container Visibility Platform | R | Cost and service impact of wait, transship or air options |
| `calculate_planning_buffer_savings` | Track & Trace Platform | R | Planning buffer saved by improved ETA accuracy |
| `calculate_recoverable_claim_value` | Contract Management System | R | Claim value recoverable under carrier liability terms |
| `calculate_recovered_value_by_route` | Costing & Margin Tool | R | Recovered value per disposition route |
| `calculate_repeat_delivery_cost` | Last-Mile Delivery Platform | R | Cost of repeat deliveries |
| `calculate_return_reduction_savings` | Returns Management System (RMS) | R | Savings from reducing returns |
| `calculate_returns_charge_impact` | Returns Management System (RMS) | R | Impact of returns charge |
| `calculate_returns_staffing_requirement` | Labour Management System (LMS) | R | Staffing requirement |
| `calculate_scenario_cost_and_service` | Transport Management System (TMS) | R | Calculates cost and service outcome of an allocation scenario |
| `calculate_stock_reallocation_plan` | Allocation & Replenishment System | R | Stock reallocation plan across network |
| `calculate_stockout_risk` | Inventory Management System (IMS) | R | Stockout risk for SKUs |
| `calculate_surcharge_impact_on_bookings` | Freight Rate Management System | R | Surcharge cost applied to planned bookings |
| `calculate_tariff_cost_impact` | Tax & Duty System | R | Cost impact of a tariff change |
| `cancel_ocean_booking` | Freight Forwarder Portal | W | Cancels an ocean freight booking with the carrier |
| `cancel_sea_freight_booking` | Freight Forwarder Portal | W | Cancels an existing sea freight booking on a PO |
| `check_dangerous_goods_restrictions` | Customs & Trade Compliance System | R | Dangerous-goods restrictions for a shipment |
| `compare_carrier_performance` | Carrier Portal | R | Compares carriers on reliability, rolls and cost |
| `compare_invoice_to_contract_rate` | Accounts Payable System | R | Compares invoice lines against contracted rates and flags variances |
| `compare_rates_to_benchmark` | Freight Rate Management System | R | Compares current rates with market benchmark |
| `create_agency_labour_request` | Labour Management System (LMS) | W | Creates an agency labour request for given weeks and headcount |
| `create_air_freight_booking` | Freight Forwarder Portal | W | Creates an air freight booking with the forwarder for a PO or style |
| `create_binding_ruling_application` | Customs & Trade Compliance System | W | Creates a binding tariff ruling application for a product |
| `create_carrier_trial_allocation` | Transport Management System (TMS) | W | Creates a trial allocation sending a share of selected lanes' volume to a named carrier |
| `create_courier_allocation_rule` | Last-Mile Delivery Platform | W | Creates a courier allocation rule splitting volume by postcode area |
| `create_customs_authorisation_application` | Customs & Trade Compliance System | W | Creates an application for a customs authorisation such as inward processing relief |
| `create_quality_review_request` | Quality Management System (QMS) | W | Creates a QA review request for named styles |
| `create_returns_charge_trial` | Returns Management System (RMS) | W | Creates a returns charge trial in selected markets |
| `create_tender_event` | Sourcing / RFx Platform | W | Creates a tender event with the approved criteria and lanes |
| `create_tender_scorecard_template` | Sourcing / RFx Platform | W | Creates a tender scorecard template with the agreed criteria and weights |
| `delete_disposition_rule` | Returns Management System (RMS) | W | Deletes a superseded disposition rule |
| `draft_classification_evidence_checklist` | Customs & Trade Compliance System | R | Drafts evidence checklist for a classification |
| `draft_corrective_action_plan` | Customs & Trade Compliance System | R | Drafts corrective action plan |
| `draft_courier_trial_plan` | Last-Mile Delivery Platform | R | Drafts courier trial plan |
| `draft_dispute_letter` | Accounts Payable System | R | Drafts a carrier invoice dispute letter |
| `draft_forwarder_booking_request` | Freight Forwarder Portal | R | Drafts a booking request for the forwarder |
| `draft_leadership_briefing` | Collaboration & Messaging (Slack/Teams) | R | Drafts leadership briefing |
| `draft_negotiation_brief` | Contract Management System | R | Drafts a carrier negotiation brief with terms to seek |
| `draft_returns_charge_trial_plan` | Returns Management System (RMS) | R | Drafts returns charge trial plan |
| `draft_stakeholder_alert` | Collaboration & Messaging (Slack/Teams) | R | Drafts stakeholder alert |
| `draft_tender_criteria` | Sourcing / RFx Platform | R | Drafts tender criteria |
| `draft_tender_scorecard` | Sourcing / RFx Platform | R | Drafts tender scorecard |
| `fetch_web_page` | Web | R | Fetches web page |
| `get_actual_stop_durations_by_route` | Fleet Telematics | R | Observed stop and unloading durations by route |
| `get_additional_tariffs_and_trade_remedies` | Customs & Trade Compliance System | R | Additional tariffs and trade remedies |
| `get_address_validation_failure_rate` | Last-Mile Delivery Platform | R | Address validation failures |
| `get_air_freight_cost_for_rolled_bookings` | Transport Management System (TMS) | R | Air freight cost incurred recovering rolled bookings |
| `get_air_freight_quote` | Freight Rate Management System | R | Air freight quote by origin, destination and weight |
| `get_air_freight_rates_by_origin` | Freight Rate Management System | R | Air rates per kg by origin airport |
| `get_air_rate_history` | Freight Rate Management System | R | Historic air rates by origin |
| `get_air_shipment_reason_codes` | Transport Management System (TMS) | R | Reason codes recorded for air-freight shipments |
| `get_air_spend_by_supplier` | Accounts Payable System | R | Air freight spend by supplier |
| `get_annual_carrier_spend_forecast` | Freight Rate Management System | R | Forecast carrier spend for the next year |
| `get_booking_cut_off_times` | Freight Forwarder Portal | R | Booking and cargo cut-off times |
| `get_booking_lead_time_vs_roll_outcome` | Freight Forwarder Portal | R | Booking lead time against roll outcome |
| `get_carrier_claims_history` | Transport Management System (TMS) | R | Damage and loss claims history by carrier |
| `get_carrier_concentration_risk` | Transport Management System (TMS) | R | Share of volume by carrier and dependency risk |
| `get_carrier_contract_rate_review_clauses` | Contract Management System | R | Rate review and surcharge clauses in carrier contracts |
| `get_carrier_contract_rates` | Contract Management System | R | Contracted carrier rates and accessorials |
| `get_carrier_eta_update_accuracy` | Container Visibility Platform | R | Accuracy of carrier ETA updates |
| `get_carrier_liability_terms` | Contract Management System | R | Carrier liability limits and claim terms |
| `get_carrier_on_time_performance` | Transport Management System (TMS) | R | On-time delivery performance by carrier, lane and period |
| `get_carrier_rate_card` | Carrier Portal | R | Carrier rate card by lane and service |
| `get_carrier_schedule_reliability` | Carrier Portal | R | Carrier schedule reliability by lane |
| `get_carrier_scorecard` | Transport Management System (TMS) | R | Carrier performance scorecard across service, cost and claims |
| `get_carrier_service_failure_costs` | Transport Management System (TMS) | R | Cost impact of carrier service failures |
| `get_carrier_share_of_volume` | Carrier Portal | R | Volume share by carrier |
| `get_carrier_spend_and_volume` | Transport Management System (TMS) | R | Carrier spend and volume over a period |
| `get_complaint_rate_by_courier` | Last-Mile Delivery Platform | R | Complaint rate by courier |
| `get_container_sku_contents` | Container Visibility Platform | R | SKU and quantity contents of a container |
| `get_container_value` | Container Visibility Platform | R | Goods value per container |
| `get_contract_claim_time_limits` | Contract Management System | R | Time limits for claims under each contract |
| `get_contract_container_rates_by_lane` | Freight Rate Management System | R | Contracted container rates by port pair |
| `get_contract_terms` | Contract Management System | R | Key terms and service levels of a contract |
| `get_contract_vs_spot_mix` | Freight Rate Management System | R | Share of volume on contract versus spot |
| `get_contracted_capacity_by_lane` | Transport Management System (TMS) | R | Contracted carrier capacity by lane and week |
| `get_conversion_and_basket_history_by_market` | E-commerce Platform | R | Conversion and basket history by market |
| `get_cost_per_drop_by_courier` | Last-Mile Delivery Platform | R | Cost per drop by courier |
| `get_courier_capacity_commitments` | Carrier Portal | R | Courier capacity commitments for peak by region |
| `get_courier_cut_off_times` | Carrier Portal | R | Courier collection and cut-off times |
| `get_courier_scorecard` | Last-Mile Delivery Platform | R | Courier performance scorecard |
| `get_cross_border_order_baskets` | E-commerce Platform | R | Cross-border order baskets and values |
| `get_customer_feedback_themes_by_style` | Customer Reviews & Feedback Platform | R | Feedback themes |
| `get_customer_segment_return_behaviour` | Customer Data Platform (CDP) | R | Segment return behaviour |
| `get_customs_authorisation_conditions` | Customs & Trade Compliance System | R | Conditions for customs authorisations |
| `get_customs_declaration_details` | Customs & Trade Compliance System | R | Declaration contents and codes |
| `get_customs_query_correspondence` | Customs & Trade Compliance System | R | Customs queries and responses |
| `get_damage_claims_by_dimension` | Carrier Portal | R | Claims broken down by depot, product, packaging and route |
| `get_damage_rate_by_courier` | Last-Mile Delivery Platform | R | Damage rate by courier |
| `get_de_minimis_thresholds_by_country` | Customs & Trade Compliance System | R | De minimis thresholds by country |
| `get_delivery_promise_accuracy` | Last-Mile Delivery Platform | R | Delivery promise accuracy |
| `get_delivery_volumes_by_city` | Last-Mile Delivery Platform | R | Delivery volumes by city |
| `get_demurrage_and_detention_for_bookings` | Freight Forwarder Portal | R | Demurrage and detention charges per booking |
| `get_disposition_route_outcomes` | Returns Management System (RMS) | R | Disposition route outcomes |
| `get_disruption_impact_on_shipments` | Track & Trace Platform | R | Disruption impact on shipments |
| `get_driver_hours_compliance_by_route` | Fleet Telematics | R | Driver hours and tachograph compliance by route |
| `get_dwell_time_by_node` | Transport Management System (TMS) | R | Dwell time at ports, hubs and depots |
| `get_epr_registrations_by_country` | Packaging Compliance & EPR System | R | EPR registrations |
| `get_expected_lost_sales` | Inventory Management System (IMS) | R | Expected lost sales |
| `get_fabric_origin_by_style` | Product Lifecycle Management (PLM) | R | Fabric origin by style |
| `get_factory_cost_quotes_by_country` | Costing & Margin Tool | R | Factory cost quotes by country |
| `get_first_attempt_failures_by_dimension` | Last-Mile Delivery Platform | R | Failures by courier, region, product, option |
| `get_first_attempt_success_trend` | Last-Mile Delivery Platform | R | First-attempt success trend |
| `get_forced_labour_risk_by_supplier` | Supply Chain Due Diligence Platform | R | Forced-labour risk by supplier |
| `get_handling_cost_by_disposition_route` | Returns Management System (RMS) | R | Handling cost by route |
| `get_historical_air_freight_spend` | Budgeting & Forecasting Tool | R | Historic air spend by period |
| `get_historical_container_volumes_by_route` | Freight Forwarder Portal | R | Container volumes by route |
| `get_historical_disruption_durations` | Container Visibility Platform | R | Durations of past comparable disruptions |
| `get_historical_peak_delivery_performance` | Last-Mile Delivery Platform | R | Past peak delivery performance |
| `get_historical_weekly_returns` | Returns Management System (RMS) | R | Weekly returns history |
| `get_inland_leg_transit_variance` | Transport Management System (TMS) | R | Variance of inland transit legs versus plan |
| `get_labour_productivity_standards` | Labour Management System (LMS) | R | Productivity standards |
| `get_lane_fill_rate_trend` | Transport Management System (TMS) | R | Fill-rate trend by lane over time |
| `get_lane_performance_summary` | Transport Management System (TMS) | R | Lane-level on-time, fill rate and cost summary for a period |
| `get_liquidator_recovery_rates` | Returns Management System (RMS) | R | Recovery rates offered by liquidators by product type |
| `get_load_volumes_by_lane` | Transport Management System (TMS) | R | Historic load volumes and delivery windows by lane |
| `get_market_benchmark_rates` | Freight Rate Management System | R | Benchmark market rates for comparable volumes |
| `get_ocean_and_rail_rate_quote` | Freight Rate Management System | R | Ocean plus rail through-rate options |
| `get_pallet_network_rate_card` | Carrier Portal | R | Pallet network rate card and published performance |
| `get_parcel_rates_by_service` | Freight Rate Management System | R | Parcel rates by service and weight band |
| `get_parcel_volumes_by_service` | Transport Management System (TMS) | R | Parcel volumes by carrier and service level |
| `get_past_disruption_costs` | Container Visibility Platform | R | Costs of previous disruptions |
| `get_peak_order_volume_forecast_by_region` | Demand Planning System | R | Peak order volume forecast by region |
| `get_peak_volume_forecast_by_lane` | Demand Planning System | R | Peak volume forecast by lane |
| `get_planned_buy_by_category_and_country` | Merchandise Financial Planning | R | Planned buy by category and country |
| `get_planned_stop_time_assumptions` | Transport Management System (TMS) | R | Stop-time and service-time assumptions used in route plans |
| `get_port_congestion_status` | Container Visibility Platform | R | Current port congestion and waiting times |
| `get_port_dwell_time_history` | Container Visibility Platform | R | Port dwell time history |
| `get_port_status_and_congestion` | Container Visibility Platform | R | Port status, closures and congestion |
| `get_predicted_eta_vs_planned_arrival` | Track & Trace Platform | R | Predicted ETA versus planned arrival |
| `get_predicted_vs_actual_arrivals_by_lane` | Transport Management System (TMS) | R | Predicted versus actual arrival times by lane |
| `get_prior_peak_capacity_utilisation` | Transport Management System (TMS) | R | Capacity used per lane in previous peak periods |
| `get_product_bill_of_materials` | Product Lifecycle Management (PLM) | R | Product materials and composition |
| `get_purchase_order_line_status` | Purchase Order System | R | PO line status and factory exit date |
| `get_purchase_order_status_for_style` | Purchase Order System | R | PO status and delay for a style |
| `get_rail_leg_reliability` | Container Visibility Platform | R | Reliability of rail legs |
| `get_rate_index_history` | Freight Rate Management System | R | Freight rate index history with year-on-year view |
| `get_rate_trend_by_lane` | Freight Rate Management System | R | Rate trend over recent weeks by lane |
| `get_reexport_volumes_by_destination` | Warehouse Management System (WMS) | R | Re-export volumes by destination |
| `get_required_origin_documents` | Customs & Trade Compliance System | R | Proof-of-origin documents required |
| `get_return_cost_per_order` | Returns Management System (RMS) | R | Return cost per order |
| `get_return_forecast_by_week` | Demand Planning System | R | Weekly returns forecast |
| `get_return_item_age_profile` | Returns Management System (RMS) | R | Age profile of returned items |
| `get_return_rates_by_market` | E-commerce Platform | R | Return rates by market |
| `get_return_reasons_by_style` | Returns Management System (RMS) | R | Return reasons by style |
| `get_returns_centre_capacity` | Returns Management System (RMS) | R | Returns centre capacity |
| `get_returns_grading_data` | Returns Management System (RMS) | R | Returns grading data |
| `get_returns_handling_practices` | Returns Management System (RMS) | R | Returns handling practices |
| `get_roll_rate_by_carrier_and_lane` | Carrier Portal | R | Booking roll rates by carrier and lane |
| `get_route_plan_utilisation` | Transport Management System (TMS) | R | Planned vehicle utilisation for routes |
| `get_rules_of_origin_for_hs_code` | Customs & Trade Compliance System | R | Rules of origin for an HS code |
| `get_sales_forecast_for_style` | Demand Planning System | R | Sales forecast for a style |
| `get_sea_air_routing_quote` | Freight Rate Management System | R | Sea-air routing quote and transit time |
| `get_spot_container_rates_by_lane` | Freight Rate Management System | R | Spot container rates by port pair |
| `get_spot_market_rates_by_lane` | Freight Rate Management System | R | Spot road freight rates by lane |
| `get_stock_cover_by_category_and_store` | Inventory Management System (IMS) | R | Stock cover by category and store |
| `get_stock_movements_for_reexport_goods` | Warehouse Management System (WMS) | R | Stock movements for re-exported goods |
| `get_store_stock_cover_by_sku` | Inventory Management System (IMS) | R | Store stock cover by SKU |
| `get_style_unit_margin` | Costing & Margin Tool | R | Unit margin for a style |
| `get_supplier_chargeback_clauses` | Contract Management System | R | Chargeback and penalty clauses in supplier contracts |
| `get_supplier_on_time_delivery_history` | Purchase Order System | R | Supplier delivery punctuality history |
| `get_supplier_qa_results_by_style` | Quality Management System (QMS) | R | Supplier QA results |
| `get_supplier_traceability_evidence` | Supply Chain Due Diligence Platform | R | Traceability evidence for suppliers |
| `get_tariff_change_history` | Customs & Trade Compliance System | R | Tariff changes over time |
| `get_tariff_rates_by_hs_code_and_country` | Customs & Trade Compliance System | R | Tariff rates by HS code and country pair |
| `get_tracking_update_latency` | Last-Mile Delivery Platform | R | Tracking update latency |
| `get_transit_time_history_by_route` | Container Visibility Platform | R | Historic transit times by route |
| `get_transshipment_options` | Freight Forwarder Portal | R | Transshipment and re-routing options |
| `get_vessel_position_and_status` | Container Visibility Platform | R | Vessel position, ETA and berth status |
| `get_wismo_contact_trend` | Customer Service Platform | R | Where-is-my-order contact trend |
| `get_wismo_contacts_by_reason` | Customer Service Platform | R | Contacts by reason |
| `list_active_disruptions` | Track & Trace Platform | R | Active disruptions |
| `list_air_freight_invoices` | Freight Forwarder Portal | R | Air freight invoices by period |
| `list_carrier_incidents_for_period` | Transport Management System (TMS) | R | Carrier service failures and incidents for a period |
| `list_carrier_invoice_lines` | Accounts Payable System | R | Carrier invoice line items |
| `list_containers_on_vessel` | Container Visibility Platform | R | Containers on a vessel |
| `list_customs_detentions` | Customs & Trade Compliance System | R | Border detentions and seizures |
| `list_customs_holds_by_supplier` | Customs & Trade Compliance System | R | Customs holds grouped by supplier |
| `list_damage_claims_by_carrier` | Carrier Portal | R | Damage claims filed per carrier |
| `list_epr_reporting_obligations` | Packaging Compliance & EPR System | R | EPR reporting obligations |
| `list_failed_delivery_reasons` | Last-Mile Delivery Platform | R | Failed delivery reasons |
| `list_historic_declarations_by_supplier` | Customs & Trade Compliance System | R | Historic declarations for a supplier |
| `list_in_transit_shipments` | Transport Management System (TMS) | R | Lists in-transit shipments with status and ETA |
| `list_inbound_containers_via_port` | Container Visibility Platform | R | Inbound containers routed via a port |
| `list_mitigation_options` | Inventory Management System (IMS) | R | Mitigation options |
| `list_new_disruptions_since` | Track & Trace Platform | R | New disruptions since a date |
| `list_open_purchase_orders_with_delay` | Purchase Order System | R | Open POs running late |
| `list_open_shipments_by_lane` | Transport Management System (TMS) | R | Open shipments grouped by lane |
| `list_orders_with_missed_scans` | Last-Mile Delivery Platform | R | Orders with missed scans |
| `list_planned_bookings` | Freight Forwarder Portal | R | Upcoming planned bookings |
| `list_planned_shipments_by_date_window` | Transport Management System (TMS) | R | Planned shipments with dates falling in a window |
| `list_rolled_bookings` | Freight Forwarder Portal | R | Lists rolled bookings with carrier and port |
| `list_routes_with_hours_breaches` | Transport Management System (TMS) | R | Routes where drivers breached or neared hours limits |
| `list_shipment_exceptions_by_lane` | Transport Management System (TMS) | R | Lists delayed, failed or exception shipments grouped by lane |
| `list_skus_on_shipment` | Inventory Management System (IMS) | R | SKUs on a shipment |
| `list_suppliers_by_raw_material` | Supplier Onboarding & Risk System | R | Suppliers by raw material |
| `list_top_returned_styles` | Returns Management System (RMS) | R | Top returned styles |
| `list_vessels_and_containers_in_transit` | Container Visibility Platform | R | Vessels and containers currently at sea |
| `list_worst_delivery_days` | Last-Mile Delivery Platform | R | Worst delivery days |
| `list_worst_postcodes_by_failed_delivery` | Last-Mile Delivery Platform | R | Worst postcodes by failed delivery |
| `read_document` | Documents | R | Reads attached document |
| `reassign_shipment_to_carrier` | Transport Management System (TMS) | W | Changes the assigned carrier on a planned or open shipment |
| `remove_carrier_from_lane_allocation` | Transport Management System (TMS) | W | Removes a carrier from a lane's allocation |
| `run_analysis` | Code Execution | R | Runs analysis |
| `run_port_closure_scenario` | Supply Planning System (MRP/DRP) | R | Runs a port closure scenario on supply plan |
| `run_tender_award_scenario` | Transport Management System (TMS) | R | Runs a tender volume-allocation scenario across carriers |
| `search_bonded_warehouse_and_ipr_rules` | Customs & Trade Compliance System | R | Bonded warehouse and inward processing relief rules and conditions |
| `search_carrier_blank_sailing_notices` | Carrier Portal | R | Carrier blank sailing announcements |
| `search_carrier_rate_increase_announcements` | Carrier Portal | R | Carrier rate-increase notices and general rate increases |
| `search_carrier_service_alerts` | Carrier Portal | R | Searches carrier service notices and disruption alerts |
| `search_carrier_surcharge_announcements` | Carrier Portal | R | Carrier surcharge announcements and effective dates |
| `search_classification_rulings` | Customs & Trade Compliance System | R | Binding classification rulings |
| `search_competitor_delivery_practices` | Competitor Price Monitoring Tool | R | Competitor delivery practices |
| `search_competitor_delivery_terms` | Competitor Price Monitoring Tool | R | Competitor delivery and duty terms |
| `search_competitor_returns_policies` | Competitor Price Monitoring Tool | R | Competitor returns charges and policies |
| `search_dangerous_goods_restrictions` | Customs & Trade Compliance System | R | Dangerous-goods restrictions for a lane |
| `search_hs_codes` | Customs & Trade Compliance System | R | Candidate HS codes for a product |
| `search_knowledge_base` | Knowledge Base / Policy Library | R | Searches internal policies and guides |
| `search_preferential_trade_agreements` | Customs & Trade Compliance System | R | Trade agreements and preferential eligibility |
| `search_web` | Web | R | Searches web |
| `send_broker_amendment_request` | Customs & Trade Compliance System | W | Sends the customs broker a request to amend open declarations |
| `send_capacity_request_to_carrier` | Carrier Portal | W | Sends a capacity request for given lanes and weeks to a carrier |
| `send_channel_message` | Collaboration & Messaging (Slack/Teams) | W | Posts a message to a named channel |
| `send_expedite_request_to_forwarder` | Freight Forwarder Portal | W | Sends the forwarder a request to expedite named shipments |
| `send_stakeholder_alert` | Collaboration & Messaging (Slack/Teams) | W | Sends the approved disruption alert to the stock and sales teams |
| `send_supplier_chargeback_notice` | Supplier Portal | W | Sends a chargeback notice to a supplier for avoidable air freight cost |
| `send_tender_invitation` | Sourcing / RFx Platform | W | Sends the tender invitation to selected carriers |
| `submit_carrier_damage_claim` | Carrier Portal | W | Files a damage claim with a carrier |
| `submit_carrier_invoice_dispute` | Carrier Portal | W | Submits a dispute of invoice lines to the carrier |
| `update_booking_sailing` | Freight Forwarder Portal | W | Moves an ocean booking to a different sailing |
| `update_budget_line` | Budgeting & Forecasting Tool | W | Changes the value of a budget line for a period |
| `update_courier_allocation_rule` | Last-Mile Delivery Platform | W | Changes the share or postcode scope of a courier allocation rule |
| `update_disposition_rule` | Returns Management System (RMS) | W | Changes the disposition route rule for a product group and item age |
| `update_notification_rule` | Customer Service Platform | W | Changes a proactive customer notification rule and its trigger |
| `update_planned_stop_time_assumption` | Transport Management System (TMS) | W | Changes the planned stop-time allowance used for a customer or drop |
| `update_planning_buffer_for_lane` | Transport Management System (TMS) | W | Changes the transit-time planning buffer for a lane |
| `update_route_plan` | Transport Management System (TMS) | W | Changes the stops, sequence or vehicle assignment in a route plan |
| `update_shipment_priority` | Track & Trace Platform | W | Changes the priority flag on a shipment |
| `update_shipment_routing` | Transport Management System (TMS) | W | Changes the routing, hold status or departure window of an open shipment |
