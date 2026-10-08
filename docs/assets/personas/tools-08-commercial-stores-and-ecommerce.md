# Systems and MCP tools · 08 Commercial, Stores and E-commerce

For each question in `questions-08-commercial-stores-and-ecommerce.md`, this file lists the enterprise systems an AI agent must reach and the MCP tool methods it would plausibly call.
Tool names follow the shared conventions so they are consistent across all nine categories; parameters are omitted.
Rows cover the main question only (Q1, Q2 and so on); follow-ups reuse the same systems unless noted.

**Legend:** read tools use `get_` / `list_` / `search_` / `calculate_` / `compare_` / `run_`; `draft_` tools produce a document without side effects; any write or side-effect tool (create / update / delete / cancel / send / approve / submit / reassign) carries a trailing ✎. Where a follow-up needs a write, its tool is listed in the main question's row.

## 71. Store manager

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Why is shrink so high? Analyse 12 weeks of adjustments by category, day, staff; compare peers; top three actions | Inventory Management System (IMS), Point of Sale (POS), Store Workforce Management, Loss Prevention & Incident System, Store Operations Platform | `get_stock_adjustments_for_store`, `get_shrink_by_category_for_store`, `get_pos_voids_and_refunds_for_store`, `get_staff_rota_for_store`, `compare_shrink_with_peer_stores`, `get_goods_receipt_discrepancies_for_store`, `run_analysis`, `create_store_action_plan_item` ✎, `create_cycle_count_task_for_store` ✎ |
| Q2 | Three best sellers have shelf gaps despite system stock; likely cause in our store? | Inventory Management System (IMS), Store Operations Platform, Point of Sale (POS) | `get_stock_on_hand_by_product_and_location`, `get_shelf_availability_exceptions_for_store`, `get_stock_adjustments_for_product`, `get_store_deliveries_for_product`, `get_hourly_sales_for_product`, `calculate_lost_sales_from_availability_gaps`, `create_cycle_count_task_for_store` ✎, `update_shelf_replenishment_priority_for_product` ✎ |
| Q3 | Build next week's staffing plan from footfall, deliveries, promos; flag gaps, Saturday sickness, what to cut | Store Workforce Management, Retail Property & Footfall System, Store Operations Platform, Pricing & Promotion Engine, Code Execution (analysis sandbox, charts) | `get_footfall_forecast_for_store`, `get_delivery_schedule_for_store`, `get_promotion_calendar_for_store`, `get_staff_availability_for_week`, `get_labour_standards_for_tasks`, `calculate_hourly_labour_requirement`, `get_task_list_for_store_week`, `run_analysis`, `approve_rota_for_store` ✎, `update_shift_for_employee` ✎, `reassign_task_to_employee` ✎, `delete_task_from_store_week` ✎ |
| Q4 | Anything local that will affect trade next month (events, roadworks, competitor openings)? | Web, Retail Property & Footfall System, Point of Sale (POS), Market Research Platform | `search_local_events_near_store`, `search_road_works_near_store`, `search_competitor_openings_near_store`, `get_footfall_history_for_store`, `get_sales_history_for_store_dates` |
| Q5 | Compare my store with cluster on shrink, availability, labour cost; rank; which gap first? | Store Operations Platform, Inventory Management System (IMS), Store Workforce Management, BI & Dashboards Platform | `get_store_cluster_members`, `compare_store_kpis_within_cluster`, `get_shrink_rate_by_store`, `get_availability_by_store`, `get_labour_cost_percentage_by_store` |

## 73. Regional / area manager

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Store 214 below target six months; compare with five peers; controllable factors; draft visit plan | Store Operations Platform, Store Workforce Management, Inventory Management System (IMS), Retail Property & Footfall System, Customer Reviews & Feedback Platform, Market Research Platform, Documents, Email & Calendar | `search_peer_stores_for_store`, `compare_store_kpis_with_peers`, `get_staffing_levels_for_store`, `get_availability_trend_for_store`, `get_local_competitor_activity_for_store`, `get_customer_feedback_for_store`, `get_stock_position_for_store`, `draft_store_visit_action_plan`, `create_calendar_event` ✎, `send_visit_agenda_to_store_manager` ✎ |
| Q2 | Which stores need attention across sales, margin, availability, shrink, labour; regional patterns? | BI & Dashboards Platform, Point of Sale (POS), Inventory Management System (IMS), Store Workforce Management, Loss Prevention & Incident System, Collaboration & Messaging | `get_store_performance_summary_for_region`, `list_stores_below_target`, `get_margin_by_store`, `get_availability_by_store`, `get_shrink_rate_by_store`, `get_labour_cost_percentage_by_store`, `run_analysis`, `create_store_visit_task` ✎, `send_message_to_store_managers` ✎ |
| Q3 | Rank stores for visits, investment and stock rebalancing next quarter | Store Operations Platform, Merchandise Financial Planning, Inventory Management System (IMS), Budgeting & Forecasting Tool, Code Execution (analysis sandbox, charts) | `list_stores_in_region`, `get_store_performance_summary_for_region`, `get_capital_investment_budget_for_region`, `get_stock_imbalance_by_store`, `calculate_store_priority_score`, `run_analysis`, `create_store_transfer_request` ✎ |
| Q4 | What will the region deliver this period? | Merchandise Financial Planning, Point of Sale (POS), Demand Planning System, Budgeting & Forecasting Tool | `get_period_sales_to_date_for_region`, `get_sales_forecast_for_region`, `get_plan_vs_actual_by_store`, `run_period_outturn_forecast`, `calculate_variance_drivers_by_store` |
| Q5 | Competitor openings, closures and promotions around my stores; what to do? | Competitor Price Monitoring Tool, Retail Property & Footfall System, Market Research Platform, Web | `search_competitor_openings_and_closures_near_stores`, `get_competitor_promotions_near_stores`, `get_store_catchment_overlap`, `search_news_for_competitor`, `get_sales_impact_of_past_competitor_openings` |

## 74. E-commerce manager

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Why did conversion fall 0.4 points last week; fixable factors; revenue lost? | Web Analytics Platform, E-commerce Platform, Order Management System (OMS), Pricing & Promotion Engine, Application Monitoring & ITSM, Inventory Management System (IMS) | `get_conversion_rate_by_device_and_day`, `get_traffic_mix_by_channel`, `get_availability_rate_for_top_products`, `get_delivery_promise_changes`, `get_price_changes_for_top_products`, `list_site_errors_for_period`, `calculate_lost_revenue_from_conversion_drop`, `run_analysis`, `update_delivery_promise_rule` ✎, `create_incident_ticket_for_site_error` ✎ |
| Q2 | Daily order volumes Black Friday to Christmas Eve; can DC and carriers cope; cut-off dates? | Demand Planning System, E-commerce Platform, Web Analytics Platform, Warehouse Management System (WMS), Labour Management System (LMS), Transport Management System (TMS), Carrier Portal | `get_daily_orders_history`, `get_marketing_plan_for_peak`, `get_traffic_forecast_for_peak`, `run_daily_order_volume_forecast`, `get_dc_daily_capacity`, `get_carrier_capacity_by_day`, `calculate_bottleneck_by_day`, `calculate_delivery_cutoff_dates`, `run_analysis`, `update_delivery_cutoff_dates_on_site` ✎, `send_capacity_request_to_carrier` ✎ |
| Q3 | Extend next-day delivery to more postcodes? Carrier capability, cost, conversion, margin impact | Transport Management System (TMS), Freight Rate Management System, E-commerce Platform, Web Analytics Platform, Costing & Margin Tool | `get_carrier_next_day_coverage_by_postcode`, `get_next_day_delivery_rates_by_postcode`, `get_conversion_by_delivery_option`, `get_orders_by_postcode_area`, `calculate_next_day_margin_impact`, `update_next_day_postcode_eligibility` ✎ |
| Q4 | Competitor delivery, returns, price and ratings for top 20 products; where are we disadvantaged? | Competitor Price Monitoring Tool, Customer Reviews & Feedback Platform, Web, E-commerce Platform | `get_top_products_by_sales`, `get_competitor_prices_for_products`, `search_competitor_delivery_and_returns_policies`, `get_competitor_ratings_for_products`, `compare_offer_vs_competitors` |
| Q5 | Why are partial and split deliveries up, and what do they cost? | Order Management System (OMS), Warehouse Management System (WMS), Transport Management System (TMS), Inventory Management System (IMS) | `get_split_shipment_rate_trend`, `list_split_orders_by_cause`, `get_stock_location_for_split_orders`, `get_allocation_rules`, `calculate_extra_shipping_cost_of_splits`, `update_allocation_rule` ✎ |
| Q6 | Split scarce hot item between online and stores; margin, experience, click-and-collect hold-back | Inventory Management System (IMS), Order Management System (OMS), E-commerce Platform, Costing & Margin Tool, Store Operations Platform | `get_stock_position_for_product_by_channel`, `get_channel_margin_for_product`, `get_sell_through_by_channel`, `get_click_and_collect_demand_for_product`, `get_inbound_purchase_orders_for_product`, `calculate_allocation_scenarios`, `update_channel_allocation_for_product` ✎, `create_stock_reservation_for_channel` ✎, `cancel_stock_reservation_for_channel` ✎ |

## 75. Marketplace / wholesale account manager

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Wholesale customer's last four orders short; investigate each, penalties, root cause, draft buyer response | Wholesale / EDI Portal, Inventory Management System (IMS), Order Management System (OMS), Warehouse Management System (WMS), Transport Management System (TMS), Contract Management System, Email & Calendar, Carrier Portal | `get_wholesale_orders_for_customer`, `get_stock_position_at_order_date`, `get_allocation_decision_for_order`, `get_pick_and_pack_record_for_order`, `get_carrier_delivery_record_for_order`, `get_penalty_terms_for_customer`, `calculate_short_shipment_penalties`, `draft_response_to_customer_buyer`, `send_email_to_customer_buyer` ✎, `create_carrier_claim` ✎ |
| Q2 | 8,000 units, three customers ordered 15,000; how to allocate? | Order Management System (OMS), Inventory Management System (IMS), Wholesale / EDI Portal, Contract Management System, Purchase Order System | `get_open_wholesale_orders_for_product`, `get_available_stock_for_product`, `get_inbound_purchase_orders_for_product`, `get_penalty_terms_for_customer`, `get_customer_account_value`, `calculate_allocation_scenarios`, `draft_short_shipment_message_to_customers`, `update_wholesale_order_allocation` ✎, `send_short_shipment_notice_to_customers` ✎ |
| Q3 | What has the marketplace changed this quarter on fees, returns, listings; margin effect? | Marketplace Seller Portal, Web, Costing & Margin Tool | `get_marketplace_policy_changes`, `get_marketplace_fee_schedule`, `get_marketplace_listing_requirements`, `search_marketplace_announcements`, `calculate_margin_impact_of_fee_changes` |
| Q4 | Expected key-account orders next quarter from sell-through and stock | Wholesale / EDI Portal, Demand Planning System, Order Management System (OMS) | `get_key_account_sell_through_and_stock`, `get_key_account_order_history`, `run_key_account_order_forecast`, `get_data_feed_coverage_by_account`, `run_analysis` |
| Q5 | Fill rate and on-time delivery by account | Order Management System (OMS), Wholesale / EDI Portal, Transport Management System (TMS), Contract Management System | `get_fill_rate_by_account`, `get_on_time_delivery_by_account`, `get_penalty_terms_for_customer`, `calculate_fine_exposure_by_account`, `create_penalty_dispute_for_account` ✎ |

## 77. Pricing analyst

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Where are prices out of line with competitors on top 200; sales cost; where could we lead? | Competitor Price Monitoring Tool, Pricing & Promotion Engine, Point of Sale (POS), Costing & Margin Tool | `get_top_products_by_sales`, `get_price_gaps_vs_competitors`, `get_price_elasticity_for_products`, `calculate_sales_lost_to_price_gaps`, `get_price_positioning_rules_for_category`, `run_analysis`, `create_price_change_request` ✎, `submit_price_change_for_approval` ✎ |
| Q2 | Effect of 5% price rise on small appliances on volume and margin; reliability; competitor reaction | Pricing & Promotion Engine, Point of Sale (POS), Costing & Margin Tool, Competitor Price Monitoring Tool, Code Execution (analysis sandbox, charts) | `get_price_elasticity_for_category`, `get_sales_and_margin_history_for_category`, `run_volume_and_margin_forecast_for_price_change`, `get_elasticity_confidence_intervals`, `get_competitor_price_response_history`, `run_analysis`, `create_price_test` ✎ |
| Q3 | Why did homeware margin fall 1.1 points? | Costing & Margin Tool, Pricing & Promotion Engine, Point of Sale (POS) | `get_margin_bridge_for_category`, `get_cost_price_changes_for_category`, `get_discounting_depth_for_category`, `get_sales_mix_shift_for_category`, `run_analysis` |
| Q4 | 6% tariff from 1 January: pass on, absorb or change product; model by price tier | Tax & Duty System, Landed Cost Calculator, Customs & Trade Compliance System, Pricing & Promotion Engine, Competitor Price Monitoring Tool, Product Lifecycle Management (PLM), Web, Code Execution (analysis sandbox, charts) | `get_tariff_rates_for_commodity_code`, `search_tariff_announcements`, `get_landed_cost_for_products`, `calculate_landed_cost_with_tariff`, `get_price_elasticity_for_category`, `get_competitor_response_to_past_cost_shocks`, `run_volume_and_margin_forecast_for_price_change`, `search_alternative_specifications_for_product`, `run_analysis`, `create_scheduled_price_change` ✎, `cancel_scheduled_price_change` ✎ |
| Q5 | What are competitors doing on price this month? | Competitor Price Monitoring Tool, Web | `get_competitor_price_changes_for_period`, `get_competitor_promotions_active`, `get_price_changes_on_our_top_sellers`, `get_competitor_price_history_for_product` |
| Q6 | Launch price for new product; margin and volume at candidate prices; test plan | Costing & Margin Tool, Pricing & Promotion Engine, Competitor Price Monitoring Tool, Demand Planning System | `get_product_cost_sheet`, `calculate_price_floor_from_cost`, `get_competitor_prices_for_similar_products`, `run_volume_and_margin_forecast_at_price_points`, `calculate_price_test_sample_size`, `create_price_test` ✎, `delete_draft_price_for_product` ✎ |

## 78. Promotions / campaign planner

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Why did weekend 20% off home event underperform: stock, creative, depth, timing, competitors? | Pricing & Promotion Engine, Point of Sale (POS), Inventory Management System (IMS), Competitor Price Monitoring Tool, Web Analytics Platform | `get_promotion_results_vs_plan`, `get_hero_item_availability_during_promotion`, `get_campaign_creative_performance`, `get_competitor_promotions_for_period`, `get_promotion_depth_and_timing_history`, `compare_promotion_with_past_events`, `run_analysis`, `cancel_promotion` ✎ |
| Q2 | Volume and supply for January 3-for-2 on toiletries; stock-out risk, cannibalisation | Demand Planning System, Pricing & Promotion Engine, Supply Planning System (MRP/DRP), Purchase Order System, Inventory Management System (IMS) | `get_past_promotion_uplift_by_mechanic`, `run_promotional_volume_forecast`, `get_cannibalisation_estimates_for_category`, `get_supply_plan_for_product`, `get_open_purchase_orders_for_product`, `calculate_stock_out_risk`, `create_supply_request_for_promotion` ✎ |
| Q3 | Which calendar promotions give best margin and traffic return; which to drop; supplier funding | Pricing & Promotion Engine, Merchandise Financial Planning, Contract Management System, Demand Planning System, Code Execution (analysis sandbox, charts) | `list_promotions_in_calendar`, `get_promotion_margin_and_traffic_return`, `get_cannibalisation_and_pull_forward_estimates`, `get_supplier_funding_terms_for_promotion`, `calculate_promotion_roi_ranking`, `run_analysis`, `delete_draft_promotion` ✎, `cancel_promotion` ✎ |
| Q4 | What are competitors planning for Black Friday? | Web, Competitor Price Monitoring Tool, Pricing & Promotion Engine, Trend & Market Intelligence Platform | `search_competitor_black_friday_plans`, `get_competitor_promotion_history_for_period`, `get_our_black_friday_results_last_year`, `get_seasonal_events_calendar` |
| Q5 | Is stock confirmed for every promotion in next six weeks? | Pricing & Promotion Engine, Inventory Management System (IMS), Purchase Order System, Supply Planning System (MRP/DRP) | `list_promotions_next_six_weeks`, `get_stock_confirmation_status_for_promotion`, `get_supplier_confirmed_delivery_dates`, `get_open_purchase_orders_for_product`, `calculate_stock_shortfall_for_promotion`, `update_promotion_start_date` ✎, `send_stock_confirmation_request_to_supplier` ✎ |

## 79. Loss prevention officer

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Combine adjustments, voids, refunds, rotas, incidents regionally; theft patterns; evidence; case summary | Inventory Management System (IMS), Point of Sale (POS), Store Workforce Management, Loss Prevention & Incident System, CCTV / Exception Reporting, Accounts Payable System, Email & Calendar | `get_stock_adjustments_for_region`, `get_pos_voids_and_refunds_for_region`, `get_staff_rota_for_stores`, `list_incidents_for_region`, `run_pos_exception_report`, `get_cctv_exception_events_for_store`, `get_goods_receipt_vs_invoice_discrepancies`, `run_analysis`, `draft_loss_prevention_case_summary`, `create_loss_prevention_case` ✎, `send_case_summary_to_area_manager` ✎ |
| Q2 | Which controls cut shrink most per pound: tagging, layout, staffing, security, system rules? | Loss Prevention & Incident System, Store Operations Platform, Knowledge Base / Policy Library, Web | `get_shrink_control_programmes`, `get_control_costs_and_results_by_store`, `search_shrink_control_research`, `compare_control_effectiveness`, `calculate_control_payback` |
| Q3 | Where will shrink end the year; what could a programme save? | Inventory Management System (IMS), Loss Prevention & Incident System, Budgeting & Forecasting Tool | `get_shrink_year_to_date_by_store`, `get_shrink_by_category`, `run_year_end_shrink_forecast`, `calculate_programme_savings`, `calculate_programme_payback` |
| Q4 | Current retail theft trends, laws, police initiatives in our locations; peer practice | Web, Loss Prevention & Incident System, Knowledge Base / Policy Library | `search_retail_theft_trends`, `search_retail_crime_legislation`, `search_police_retail_crime_initiatives`, `search_retailer_loss_prevention_practices`, `get_incident_counts_by_location` |
| Q5 | Self-checkout shrink up in five stores; why? | Point of Sale (POS), Inventory Management System (IMS), Loss Prevention & Incident System, Application Monitoring & ITSM, CCTV / Exception Reporting | `get_self_checkout_shrink_by_store`, `get_self_checkout_scan_exception_rates`, `list_self_checkout_fault_tickets`, `get_cctv_exception_events_for_store`, `calculate_intervention_cost_effectiveness`, `create_fault_ticket_for_self_checkout` ✎, `update_self_checkout_exception_rule` ✎ |
| Q6 | What are our highest-loss products? | Inventory Management System (IMS), Loss Prevention & Incident System, Point of Sale (POS) | `get_highest_loss_products`, `get_product_loss_by_cause`, `compare_product_loss_year_on_year`, `get_incident_records_for_product`, `calculate_protection_options_cost`, `update_high_risk_product_list` ✎, `remove_product_from_high_risk_list` ✎ |

## 80. Franchise / international market manager

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Market entry brief for Poland and Czechia: regulation, tariffs, labelling, consumers, margins, product changes | Web, Product Compliance & Regulatory Database, Customs & Trade Compliance System, Tax & Duty System, Market Research Platform, Product Lifecycle Management (PLM), Costing & Margin Tool, Documents, Project & Portfolio Management Tool | `search_market_entry_regulations`, `get_import_rules_and_tariffs_for_market`, `get_labelling_and_language_requirements`, `get_product_compliance_requirements_by_market`, `get_consumer_preferences_and_price_points`, `get_typical_retail_margins_for_market`, `get_products_requiring_modification`, `draft_market_entry_brief`, `create_market_entry_project` ✎ |
| Q2 | Dubai franchise out of stock on core lines, overstocked elsewhere: customs, ordering or lead time? | Franchise Management Portal, Inventory Management System (IMS), Customs & Trade Compliance System, Freight Forwarder Portal, Track & Trace Platform | `get_franchise_stock_position`, `get_franchise_order_history`, `get_customs_clearance_status_for_shipments`, `get_shipment_tracking_for_franchise`, `get_lead_time_to_destination`, `compare_core_range_cover_vs_forecast`, `update_franchise_order_hold` ✎, `update_shipment_priority_for_franchise_order` ✎ |
| Q3 | What should we sell in Japan: sizes, pack formats, competition; which products travel? | Market Research Platform, Trend & Market Intelligence Platform, Web, Product Information Management (PIM), Product Compliance & Regulatory Database | `get_market_size_and_pack_formats_for_country`, `search_local_competitors_in_market`, `get_product_attributes_for_range`, `get_product_compliance_requirements_by_market`, `compare_range_fit_to_market` |
| Q4 | Investment and sales expectations for expanding in Spain; assumptions, downside, break-even | Merchandise Financial Planning, Budgeting & Forecasting Tool, Market Research Platform, Costing & Margin Tool, Retail Property & Footfall System | `get_market_size_and_growth_for_country`, `get_comparable_market_launch_results`, `run_market_sales_forecast`, `calculate_investment_required`, `calculate_breakeven_period`, `run_analysis` |
| Q5 | How are our partners doing on sales, margin, stock, compliance? | Franchise Management Portal, Inventory Management System (IMS), Product Compliance & Regulatory Database, Email & Calendar | `get_franchise_partner_scorecard`, `get_partner_sales_and_margin`, `get_partner_stock_position`, `get_partner_compliance_status`, `list_partners_needing_intervention`, `send_partner_performance_notice` ✎, `create_calendar_event` ✎ |
| Q6 | Legal and tax: Mexico local subsidiary versus franchise partner; exit, liability, recommendation | Web, Documents, Tax & Duty System, Contract Management System, Knowledge Base / Policy Library | `search_mexico_corporate_and_liability_rules`, `get_tax_treatment_of_subsidiary_vs_franchise`, `get_existing_franchise_agreement_terms`, `get_internal_policy_on_market_entry_structures`, `calculate_structure_cost_comparison` |

## Tool catalogue for this category

| Tool | System | R/W | One-line description |
|---|---|---|---|
| `approve_rota_for_store` | Store Workforce Management | W | Approves a draft weekly rota and publishes it to staff. |
| `calculate_allocation_scenarios` | Order Management System (OMS) | R | Calculates allocation scenarios. |
| `calculate_bottleneck_by_day` | Transport Management System (TMS) | R | Calculates bottleneck by day. |
| `calculate_breakeven_period` | Budgeting & Forecasting Tool | R | Calculates breakeven period. |
| `calculate_control_payback` | Loss Prevention & Incident System | R | Calculates control payback. |
| `calculate_delivery_cutoff_dates` | Transport Management System (TMS) | R | Calculates delivery cutoff dates. |
| `calculate_extra_shipping_cost_of_splits` | Transport Management System (TMS) | R | Calculates extra shipping cost of splits. |
| `calculate_fine_exposure_by_account` | Contract Management System | R | Calculates fine exposure by account. |
| `calculate_hourly_labour_requirement` | Store Workforce Management | R | Calculates hourly labour requirement. |
| `calculate_intervention_cost_effectiveness` | Loss Prevention & Incident System | R | Calculates intervention cost effectiveness. |
| `calculate_investment_required` | Budgeting & Forecasting Tool | R | Calculates investment required. |
| `calculate_landed_cost_with_tariff` | Landed Cost Calculator | R | Calculates landed cost with tariff. |
| `calculate_lost_revenue_from_conversion_drop` | Web Analytics Platform | R | Calculates lost revenue from conversion drop. |
| `calculate_lost_sales_from_availability_gaps` | Inventory Management System (IMS) | R | Calculates lost sales from availability gaps. |
| `calculate_margin_impact_of_fee_changes` | Costing & Margin Tool | R | Calculates margin impact of fee changes. |
| `calculate_next_day_margin_impact` | Costing & Margin Tool | R | Calculates next day margin impact. |
| `calculate_price_floor_from_cost` | Costing & Margin Tool | R | Calculates price floor from cost. |
| `calculate_price_test_sample_size` | Pricing & Promotion Engine | R | Calculates price test sample size. |
| `calculate_programme_payback` | Budgeting & Forecasting Tool | R | Calculates programme payback. |
| `calculate_programme_savings` | Budgeting & Forecasting Tool | R | Calculates programme savings. |
| `calculate_promotion_roi_ranking` | Pricing & Promotion Engine | R | Calculates promotion roi ranking. |
| `calculate_protection_options_cost` | Loss Prevention & Incident System | R | Calculates protection options cost. |
| `calculate_sales_lost_to_price_gaps` | Pricing & Promotion Engine | R | Calculates sales lost to price gaps. |
| `calculate_short_shipment_penalties` | Contract Management System | R | Calculates short shipment penalties. |
| `calculate_stock_out_risk` | Demand Planning System | R | Calculates stock out risk. |
| `calculate_stock_shortfall_for_promotion` | Supply Planning System (MRP/DRP) | R | Calculates stock shortfall for promotion. |
| `calculate_store_priority_score` | BI & Dashboards Platform | R | Calculates store priority score. |
| `calculate_structure_cost_comparison` | Costing & Margin Tool | R | Calculates structure cost comparison. |
| `calculate_variance_drivers_by_store` | BI & Dashboards Platform | R | Calculates variance drivers by store. |
| `cancel_promotion` | Pricing & Promotion Engine | W | Cancels a planned promotion and releases its commitments. |
| `cancel_scheduled_price_change` | Pricing & Promotion Engine | W | Cancels a scheduled price change before it takes effect. |
| `cancel_stock_reservation_for_channel` | Inventory Management System (IMS) | W | Cancels a channel stock reservation and returns the units to free stock. |
| `compare_control_effectiveness` | Loss Prevention & Incident System | R | Compares control effectiveness. |
| `compare_core_range_cover_vs_forecast` | Franchise Management Portal | R | Compares core range cover vs forecast. |
| `compare_offer_vs_competitors` | Competitor Price Monitoring Tool | R | Compares offer vs competitors. |
| `compare_product_loss_year_on_year` | Inventory Management System (IMS) | R | Compares product loss year on year. |
| `compare_promotion_with_past_events` | Pricing & Promotion Engine | R | Compares promotion with past events. |
| `compare_range_fit_to_market` | Product Information Management (PIM) | R | Compares range fit to market. |
| `compare_shrink_with_peer_stores` | Inventory Management System (IMS) | R | Compares shrink with peer stores. |
| `compare_store_kpis_with_peers` | Store Operations Platform | R | Compares store kpis with peers. |
| `compare_store_kpis_within_cluster` | Store Operations Platform | R | Compares store kpis within cluster. |
| `create_calendar_event` | Email & Calendar | W | Creates a calendar event with attendees. |
| `create_carrier_claim` | Carrier Portal | W | Files a loss or damage claim against a carrier for an order. |
| `create_cycle_count_task_for_store` | Store Operations Platform | W | Creates a cycle-count task for named lines or a category in a store. |
| `create_fault_ticket_for_self_checkout` | Application Monitoring & ITSM | W | Raises a fault ticket for a self-checkout unit. |
| `create_incident_ticket_for_site_error` | Application Monitoring & ITSM | W | Raises an incident ticket for a site error. |
| `create_loss_prevention_case` | Loss Prevention & Incident System | W | Opens a formal loss prevention case with linked evidence. |
| `create_market_entry_project` | Project & Portfolio Management Tool | W | Creates a market entry project with workstreams. |
| `create_penalty_dispute_for_account` | Contract Management System | W | Lodges a dispute against a penalty charged to an account. |
| `create_price_change_request` | Pricing & Promotion Engine | W | Creates a draft price change request for products. |
| `create_price_test` | Pricing & Promotion Engine | W | Creates a price test with test and control cells. |
| `create_scheduled_price_change` | Pricing & Promotion Engine | W | Schedules an approved price change to take effect on a date. |
| `create_stock_reservation_for_channel` | Inventory Management System (IMS) | W | Reserves a quantity of a product for a channel such as click-and-collect. |
| `create_store_action_plan_item` | Store Operations Platform | W | Adds an owned, dated action to the store improvement plan. |
| `create_store_transfer_request` | Inventory Management System (IMS) | W | Raises a stock transfer request between two stores. |
| `create_store_visit_task` | Store Operations Platform | W | Adds a store visit to the area manager's visit schedule. |
| `create_supply_request_for_promotion` | Supply Planning System (MRP/DRP) | W | Raises a supply request for the stock a promotion needs. |
| `delete_draft_price_for_product` | Pricing & Promotion Engine | W | Deletes an unapproved draft price for a product. |
| `delete_draft_promotion` | Pricing & Promotion Engine | W | Deletes a promotion that is still in draft. |
| `delete_task_from_store_week` | Store Operations Platform | W | Removes a scheduled task from a store's week plan. |
| `draft_loss_prevention_case_summary` | Loss Prevention & Incident System | Draft | Drafts loss prevention case summary. |
| `draft_market_entry_brief` | Documents | Draft | Drafts market entry brief. |
| `draft_response_to_customer_buyer` | Wholesale / EDI Portal | Draft | Drafts response to customer buyer. |
| `draft_short_shipment_message_to_customers` | Wholesale / EDI Portal | Draft | Drafts short shipment message to customers. |
| `draft_store_visit_action_plan` | Documents | Draft | Drafts store visit action plan. |
| `get_allocation_decision_for_order` | Order Management System (OMS) | R | Retrieves allocation decision for order. |
| `get_allocation_rules` | Order Management System (OMS) | R | Retrieves allocation rules. |
| `get_availability_by_store` | Inventory Management System (IMS) | R | Retrieves availability by store. |
| `get_availability_rate_for_top_products` | Inventory Management System (IMS) | R | Retrieves availability rate for top products. |
| `get_availability_trend_for_store` | Inventory Management System (IMS) | R | Retrieves availability trend for store. |
| `get_available_stock_for_product` | Inventory Management System (IMS) | R | Retrieves available stock for product. |
| `get_campaign_creative_performance` | Web Analytics Platform | R | Retrieves campaign creative performance. |
| `get_cannibalisation_and_pull_forward_estimates` | Demand Planning System | R | Retrieves cannibalisation and pull forward estimates. |
| `get_cannibalisation_estimates_for_category` | Demand Planning System | R | Retrieves cannibalisation estimates for category. |
| `get_capital_investment_budget_for_region` | Budgeting & Forecasting Tool | R | Retrieves capital investment budget for region. |
| `get_carrier_capacity_by_day` | Carrier Portal | R | Retrieves carrier capacity by day. |
| `get_carrier_delivery_record_for_order` | Carrier Portal | R | Retrieves carrier delivery record for order. |
| `get_carrier_next_day_coverage_by_postcode` | Transport Management System (TMS) | R | Retrieves carrier next day coverage by postcode. |
| `get_cctv_exception_events_for_store` | CCTV / Exception Reporting | R | Retrieves cctv exception events for store. |
| `get_channel_margin_for_product` | Costing & Margin Tool | R | Retrieves channel margin for product. |
| `get_click_and_collect_demand_for_product` | Store Operations Platform | R | Retrieves click and collect demand for product. |
| `get_comparable_market_launch_results` | Market Research Platform | R | Retrieves comparable market launch results. |
| `get_competitor_price_changes_for_period` | Competitor Price Monitoring Tool | R | Retrieves competitor price changes for period. |
| `get_competitor_price_history_for_product` | Competitor Price Monitoring Tool | R | Retrieves competitor price history for product. |
| `get_competitor_price_response_history` | Competitor Price Monitoring Tool | R | Retrieves competitor price response history. |
| `get_competitor_prices_for_products` | Competitor Price Monitoring Tool | R | Retrieves competitor prices for products. |
| `get_competitor_prices_for_similar_products` | Competitor Price Monitoring Tool | R | Retrieves competitor prices for similar products. |
| `get_competitor_promotion_history_for_period` | Competitor Price Monitoring Tool | R | Retrieves competitor promotion history for period. |
| `get_competitor_promotions_active` | Competitor Price Monitoring Tool | R | Retrieves competitor promotions active. |
| `get_competitor_promotions_for_period` | Competitor Price Monitoring Tool | R | Retrieves competitor promotions for period. |
| `get_competitor_promotions_near_stores` | Competitor Price Monitoring Tool | R | Retrieves competitor promotions near stores. |
| `get_competitor_ratings_for_products` | Customer Reviews & Feedback Platform | R | Retrieves competitor ratings for products. |
| `get_competitor_response_to_past_cost_shocks` | Competitor Price Monitoring Tool | R | Retrieves competitor response to past cost shocks. |
| `get_consumer_preferences_and_price_points` | Market Research Platform | R | Retrieves consumer preferences and price points. |
| `get_control_costs_and_results_by_store` | Store Operations Platform | R | Retrieves control costs and results by store. |
| `get_conversion_by_delivery_option` | Web Analytics Platform | R | Retrieves conversion by delivery option. |
| `get_conversion_rate_by_device_and_day` | Web Analytics Platform | R | Retrieves conversion rate by device and day. |
| `get_cost_price_changes_for_category` | Costing & Margin Tool | R | Retrieves cost price changes for category. |
| `get_customer_account_value` | Wholesale / EDI Portal | R | Retrieves customer account value. |
| `get_customer_feedback_for_store` | Customer Reviews & Feedback Platform | R | Retrieves customer feedback for store. |
| `get_customs_clearance_status_for_shipments` | Customs & Trade Compliance System | R | Retrieves customs clearance status for shipments. |
| `get_daily_orders_history` | Demand Planning System | R | Retrieves daily orders history. |
| `get_data_feed_coverage_by_account` | Wholesale / EDI Portal | R | Retrieves data feed coverage by account. |
| `get_dc_daily_capacity` | Warehouse Management System (WMS) | R | Retrieves dc daily capacity. |
| `get_delivery_promise_changes` | E-commerce Platform | R | Retrieves delivery promise changes. |
| `get_delivery_schedule_for_store` | Store Operations Platform | R | Retrieves delivery schedule for store. |
| `get_discounting_depth_for_category` | Pricing & Promotion Engine | R | Retrieves discounting depth for category. |
| `get_elasticity_confidence_intervals` | Pricing & Promotion Engine | R | Retrieves elasticity confidence intervals. |
| `get_existing_franchise_agreement_terms` | Contract Management System | R | Retrieves existing franchise agreement terms. |
| `get_fill_rate_by_account` | Order Management System (OMS) | R | Retrieves fill rate by account. |
| `get_footfall_forecast_for_store` | Retail Property & Footfall System | R | Retrieves footfall forecast for store. |
| `get_footfall_history_for_store` | Retail Property & Footfall System | R | Retrieves footfall history for store. |
| `get_franchise_order_history` | Franchise Management Portal | R | Retrieves franchise order history. |
| `get_franchise_partner_scorecard` | Franchise Management Portal | R | Retrieves franchise partner scorecard. |
| `get_franchise_stock_position` | Inventory Management System (IMS) | R | Retrieves franchise stock position. |
| `get_goods_receipt_discrepancies_for_store` | Inventory Management System (IMS) | R | Retrieves goods receipt discrepancies for store. |
| `get_goods_receipt_vs_invoice_discrepancies` | Accounts Payable System | R | Retrieves goods receipt vs invoice discrepancies. |
| `get_hero_item_availability_during_promotion` | Inventory Management System (IMS) | R | Retrieves hero item availability during promotion. |
| `get_highest_loss_products` | Inventory Management System (IMS) | R | Retrieves highest loss products. |
| `get_hourly_sales_for_product` | Point of Sale (POS) | R | Retrieves hourly sales for product. |
| `get_import_rules_and_tariffs_for_market` | Tax & Duty System | R | Retrieves import rules and tariffs for market. |
| `get_inbound_purchase_orders_for_product` | Purchase Order System | R | Retrieves inbound purchase orders for product. |
| `get_incident_counts_by_location` | Loss Prevention & Incident System | R | Retrieves incident counts by location. |
| `get_incident_records_for_product` | Loss Prevention & Incident System | R | Retrieves incident records for product. |
| `get_internal_policy_on_market_entry_structures` | Knowledge Base / Policy Library | R | Retrieves internal policy on market entry structures. |
| `get_key_account_order_history` | Order Management System (OMS) | R | Retrieves key account order history. |
| `get_key_account_sell_through_and_stock` | Wholesale / EDI Portal | R | Retrieves key account sell through and stock. |
| `get_labelling_and_language_requirements` | Product Compliance & Regulatory Database | R | Retrieves labelling and language requirements. |
| `get_labour_cost_percentage_by_store` | Store Workforce Management | R | Retrieves labour cost percentage by store. |
| `get_labour_standards_for_tasks` | Store Workforce Management | R | Retrieves labour standards for tasks. |
| `get_landed_cost_for_products` | Landed Cost Calculator | R | Retrieves landed cost for products. |
| `get_lead_time_to_destination` | Customs & Trade Compliance System | R | Retrieves lead time to destination. |
| `get_local_competitor_activity_for_store` | Market Research Platform | R | Retrieves local competitor activity for store. |
| `get_margin_bridge_for_category` | Costing & Margin Tool | R | Retrieves margin bridge for category. |
| `get_margin_by_store` | BI & Dashboards Platform | R | Retrieves margin by store. |
| `get_market_size_and_growth_for_country` | Market Research Platform | R | Retrieves market size and growth for country. |
| `get_market_size_and_pack_formats_for_country` | Market Research Platform | R | Retrieves market size and pack formats for country. |
| `get_marketing_plan_for_peak` | E-commerce Platform | R | Retrieves marketing plan for peak. |
| `get_marketplace_fee_schedule` | Marketplace Seller Portal | R | Retrieves marketplace fee schedule. |
| `get_marketplace_listing_requirements` | Marketplace Seller Portal | R | Retrieves marketplace listing requirements. |
| `get_marketplace_policy_changes` | Marketplace Seller Portal | R | Retrieves marketplace policy changes. |
| `get_next_day_delivery_rates_by_postcode` | Freight Rate Management System | R | Retrieves next day delivery rates by postcode. |
| `get_on_time_delivery_by_account` | Transport Management System (TMS) | R | Retrieves on time delivery by account. |
| `get_open_purchase_orders_for_product` | Purchase Order System | R | Retrieves open purchase orders for product. |
| `get_open_wholesale_orders_for_product` | Order Management System (OMS) | R | Retrieves open wholesale orders for product. |
| `get_orders_by_postcode_area` | E-commerce Platform | R | Retrieves orders by postcode area. |
| `get_our_black_friday_results_last_year` | Pricing & Promotion Engine | R | Retrieves our black friday results last year. |
| `get_partner_compliance_status` | Franchise Management Portal | R | Retrieves partner compliance status. |
| `get_partner_sales_and_margin` | Franchise Management Portal | R | Retrieves partner sales and margin. |
| `get_partner_stock_position` | Franchise Management Portal | R | Retrieves partner stock position. |
| `get_past_promotion_uplift_by_mechanic` | Demand Planning System | R | Retrieves past promotion uplift by mechanic. |
| `get_penalty_terms_for_customer` | Contract Management System | R | Retrieves penalty terms for customer. |
| `get_period_sales_to_date_for_region` | Point of Sale (POS) | R | Retrieves period sales to date for region. |
| `get_pick_and_pack_record_for_order` | Warehouse Management System (WMS) | R | Retrieves pick and pack record for order. |
| `get_plan_vs_actual_by_store` | Store Operations Platform | R | Retrieves plan vs actual by store. |
| `get_pos_voids_and_refunds_for_region` | Point of Sale (POS) | R | Retrieves pos voids and refunds for region. |
| `get_pos_voids_and_refunds_for_store` | Point of Sale (POS) | R | Retrieves pos voids and refunds for store. |
| `get_price_changes_for_top_products` | E-commerce Platform | R | Retrieves price changes for top products. |
| `get_price_changes_on_our_top_sellers` | Competitor Price Monitoring Tool | R | Retrieves price changes on our top sellers. |
| `get_price_elasticity_for_category` | Pricing & Promotion Engine | R | Retrieves price elasticity for category. |
| `get_price_elasticity_for_products` | Pricing & Promotion Engine | R | Retrieves price elasticity for products. |
| `get_price_gaps_vs_competitors` | Competitor Price Monitoring Tool | R | Retrieves price gaps vs competitors. |
| `get_price_positioning_rules_for_category` | Pricing & Promotion Engine | R | Retrieves price positioning rules for category. |
| `get_product_attributes_for_range` | Product Information Management (PIM) | R | Retrieves product attributes for range. |
| `get_product_compliance_requirements_by_market` | Product Compliance & Regulatory Database | R | Retrieves product compliance requirements by market. |
| `get_product_cost_sheet` | Costing & Margin Tool | R | Retrieves product cost sheet. |
| `get_product_loss_by_cause` | Inventory Management System (IMS) | R | Retrieves product loss by cause. |
| `get_products_requiring_modification` | Costing & Margin Tool | R | Retrieves products requiring modification. |
| `get_promotion_calendar_for_store` | Pricing & Promotion Engine | R | Retrieves promotion calendar for store. |
| `get_promotion_depth_and_timing_history` | Pricing & Promotion Engine | R | Retrieves promotion depth and timing history. |
| `get_promotion_margin_and_traffic_return` | Pricing & Promotion Engine | R | Retrieves promotion margin and traffic return. |
| `get_promotion_results_vs_plan` | Pricing & Promotion Engine | R | Retrieves promotion results vs plan. |
| `get_sales_and_margin_history_for_category` | Point of Sale (POS) | R | Retrieves sales and margin history for category. |
| `get_sales_forecast_for_region` | Merchandise Financial Planning | R | Retrieves sales forecast for region. |
| `get_sales_history_for_store_dates` | Point of Sale (POS) | R | Retrieves sales history for store dates. |
| `get_sales_impact_of_past_competitor_openings` | Competitor Price Monitoring Tool | R | Retrieves sales impact of past competitor openings. |
| `get_sales_mix_shift_for_category` | Point of Sale (POS) | R | Retrieves sales mix shift for category. |
| `get_seasonal_events_calendar` | Trend & Market Intelligence Platform | R | Retrieves seasonal events calendar. |
| `get_self_checkout_scan_exception_rates` | Point of Sale (POS) | R | Retrieves self checkout scan exception rates. |
| `get_self_checkout_shrink_by_store` | Inventory Management System (IMS) | R | Retrieves self checkout shrink by store. |
| `get_sell_through_by_channel` | Order Management System (OMS) | R | Retrieves sell through by channel. |
| `get_shelf_availability_exceptions_for_store` | Store Operations Platform | R | Retrieves shelf availability exceptions for store. |
| `get_shipment_tracking_for_franchise` | Track & Trace Platform | R | Retrieves shipment tracking for franchise. |
| `get_shrink_by_category` | Inventory Management System (IMS) | R | Retrieves shrink by category. |
| `get_shrink_by_category_for_store` | Inventory Management System (IMS) | R | Retrieves shrink by category for store. |
| `get_shrink_control_programmes` | Store Operations Platform | R | Retrieves shrink control programmes. |
| `get_shrink_rate_by_store` | Inventory Management System (IMS) | R | Retrieves shrink rate by store. |
| `get_shrink_year_to_date_by_store` | Inventory Management System (IMS) | R | Retrieves shrink year to date by store. |
| `get_split_shipment_rate_trend` | Transport Management System (TMS) | R | Retrieves split shipment rate trend. |
| `get_staff_availability_for_week` | Store Workforce Management | R | Retrieves staff availability for week. |
| `get_staff_rota_for_store` | Store Workforce Management | R | Retrieves staff rota for store. |
| `get_staff_rota_for_stores` | Store Workforce Management | R | Retrieves staff rota for stores. |
| `get_staffing_levels_for_store` | Store Workforce Management | R | Retrieves staffing levels for store. |
| `get_stock_adjustments_for_product` | Inventory Management System (IMS) | R | Retrieves stock adjustments for product. |
| `get_stock_adjustments_for_region` | Inventory Management System (IMS) | R | Retrieves stock adjustments for region. |
| `get_stock_adjustments_for_store` | Inventory Management System (IMS) | R | Retrieves stock adjustments for store. |
| `get_stock_confirmation_status_for_promotion` | Inventory Management System (IMS) | R | Retrieves stock confirmation status for promotion. |
| `get_stock_imbalance_by_store` | Inventory Management System (IMS) | R | Retrieves stock imbalance by store. |
| `get_stock_location_for_split_orders` | Warehouse Management System (WMS) | R | Retrieves stock location for split orders. |
| `get_stock_on_hand_by_product_and_location` | Inventory Management System (IMS) | R | Retrieves stock on hand by product and location. |
| `get_stock_position_at_order_date` | Inventory Management System (IMS) | R | Retrieves stock position at order date. |
| `get_stock_position_for_product_by_channel` | Inventory Management System (IMS) | R | Retrieves stock position for product by channel. |
| `get_stock_position_for_store` | Inventory Management System (IMS) | R | Retrieves stock position for store. |
| `get_store_catchment_overlap` | Retail Property & Footfall System | R | Retrieves store catchment overlap. |
| `get_store_cluster_members` | Store Operations Platform | R | Retrieves store cluster members. |
| `get_store_deliveries_for_product` | Inventory Management System (IMS) | R | Retrieves store deliveries for product. |
| `get_store_performance_summary_for_region` | BI & Dashboards Platform | R | Retrieves store performance summary for region. |
| `get_supplier_confirmed_delivery_dates` | Purchase Order System | R | Retrieves supplier confirmed delivery dates. |
| `get_supplier_funding_terms_for_promotion` | Contract Management System | R | Retrieves supplier funding terms for promotion. |
| `get_supply_plan_for_product` | Supply Planning System (MRP/DRP) | R | Retrieves supply plan for product. |
| `get_tariff_rates_for_commodity_code` | Tax & Duty System | R | Retrieves tariff rates for commodity code. |
| `get_task_list_for_store_week` | Store Operations Platform | R | Retrieves task list for store week. |
| `get_tax_treatment_of_subsidiary_vs_franchise` | Tax & Duty System | R | Retrieves tax treatment of subsidiary vs franchise. |
| `get_top_products_by_sales` | E-commerce Platform | R | Retrieves top products by sales. |
| `get_traffic_forecast_for_peak` | Web Analytics Platform | R | Retrieves traffic forecast for peak. |
| `get_traffic_mix_by_channel` | Web Analytics Platform | R | Retrieves traffic mix by channel. |
| `get_typical_retail_margins_for_market` | Market Research Platform | R | Retrieves typical retail margins for market. |
| `get_wholesale_orders_for_customer` | Wholesale / EDI Portal | R | Retrieves wholesale orders for customer. |
| `list_incidents_for_region` | Loss Prevention & Incident System | R | Lists incidents for region. |
| `list_partners_needing_intervention` | Franchise Management Portal | R | Lists partners needing intervention. |
| `list_promotions_in_calendar` | Pricing & Promotion Engine | R | Lists promotions in calendar. |
| `list_promotions_next_six_weeks` | Pricing & Promotion Engine | R | Lists promotions next six weeks. |
| `list_self_checkout_fault_tickets` | Application Monitoring & ITSM | R | Lists self checkout fault tickets. |
| `list_site_errors_for_period` | Application Monitoring & ITSM | R | Lists site errors for period. |
| `list_split_orders_by_cause` | Order Management System (OMS) | R | Lists split orders by cause. |
| `list_stores_below_target` | BI & Dashboards Platform | R | Lists stores below target. |
| `list_stores_in_region` | Store Operations Platform | R | Lists stores in region. |
| `reassign_task_to_employee` | Store Operations Platform | W | Moves a scheduled store task to a different team member. |
| `remove_product_from_high_risk_list` | Loss Prevention & Incident System | W | Removes a product from the high-risk protection list. |
| `run_analysis` | Code Execution (analysis sandbox, charts) | R | Runs analysis. |
| `run_daily_order_volume_forecast` | Demand Planning System | R | Runs daily order volume forecast. |
| `run_key_account_order_forecast` | Demand Planning System | R | Runs key account order forecast. |
| `run_market_sales_forecast` | Merchandise Financial Planning | R | Runs market sales forecast. |
| `run_period_outturn_forecast` | Merchandise Financial Planning | R | Runs period outturn forecast. |
| `run_pos_exception_report` | Point of Sale (POS) | R | Runs pos exception report. |
| `run_promotional_volume_forecast` | Demand Planning System | R | Runs promotional volume forecast. |
| `run_volume_and_margin_forecast_at_price_points` | Pricing & Promotion Engine | R | Runs volume and margin forecast at price points. |
| `run_volume_and_margin_forecast_for_price_change` | Pricing & Promotion Engine | R | Runs volume and margin forecast for price change. |
| `run_year_end_shrink_forecast` | Budgeting & Forecasting Tool | R | Runs year end shrink forecast. |
| `search_alternative_specifications_for_product` | Product Lifecycle Management (PLM) | R | Searches for alternative specifications for product. |
| `search_competitor_black_friday_plans` | Web | R | Searches for competitor black friday plans. |
| `search_competitor_delivery_and_returns_policies` | Web | R | Searches for competitor delivery and returns policies. |
| `search_competitor_openings_and_closures_near_stores` | Competitor Price Monitoring Tool | R | Searches for competitor openings and closures near stores. |
| `search_competitor_openings_near_store` | Competitor Price Monitoring Tool | R | Searches for competitor openings near store. |
| `search_local_competitors_in_market` | Market Research Platform | R | Searches for local competitors in market. |
| `search_local_events_near_store` | Market Research Platform | R | Searches for local events near store. |
| `search_market_entry_regulations` | Web | R | Searches for market entry regulations. |
| `search_marketplace_announcements` | Web | R | Searches for marketplace announcements. |
| `search_mexico_corporate_and_liability_rules` | Web | R | Searches for mexico corporate and liability rules. |
| `search_news_for_competitor` | Web | R | Searches for news for competitor. |
| `search_peer_stores_for_store` | Store Operations Platform | R | Searches for peer stores for store. |
| `search_police_retail_crime_initiatives` | Web | R | Searches for police retail crime initiatives. |
| `search_retail_crime_legislation` | Web | R | Searches for retail crime legislation. |
| `search_retail_theft_trends` | Web | R | Searches for retail theft trends. |
| `search_retailer_loss_prevention_practices` | Web | R | Searches for retailer loss prevention practices. |
| `search_road_works_near_store` | Market Research Platform | R | Searches for road works near store. |
| `search_shrink_control_research` | Knowledge Base / Policy Library | R | Searches for shrink control research. |
| `search_tariff_announcements` | Web | R | Searches for tariff announcements. |
| `send_capacity_request_to_carrier` | Carrier Portal | W | Sends a request for extra carrier capacity on named dates. |
| `send_case_summary_to_area_manager` | Email & Calendar | W | Emails a case summary to the area manager. |
| `send_email_to_customer_buyer` | Email & Calendar | W | Sends an email to a customer's buyer. |
| `send_message_to_store_managers` | Collaboration & Messaging | W | Sends a message to named store managers. |
| `send_partner_performance_notice` | Franchise Management Portal | W | Sends a formal performance notice to a franchise partner. |
| `send_short_shipment_notice_to_customers` | Wholesale / EDI Portal | W | Sends a short-shipment notice to named wholesale customers. |
| `send_stock_confirmation_request_to_supplier` | Purchase Order System | W | Sends a supplier a request to confirm stock and delivery dates. |
| `send_visit_agenda_to_store_manager` | Email & Calendar | W | Sends a store visit agenda email to the store manager. |
| `submit_price_change_for_approval` | Pricing & Promotion Engine | W | Submits a draft price change into the approval workflow. |
| `update_allocation_rule` | Order Management System (OMS) | W | Edits a stock allocation or order-sourcing rule. |
| `update_channel_allocation_for_product` | Order Management System (OMS) | W | Changes the share of a product's stock allocated to each channel. |
| `update_delivery_cutoff_dates_on_site` | E-commerce Platform | W | Sets the peak-period delivery cut-off dates shown on the site. |
| `update_delivery_promise_rule` | E-commerce Platform | W | Changes the delivery promise or cut-off rule shown at checkout. |
| `update_franchise_order_hold` | Franchise Management Portal | W | Places or lifts a hold on a partner's order lines. |
| `update_high_risk_product_list` | Loss Prevention & Incident System | W | Adds products to the high-risk protection list. |
| `update_next_day_postcode_eligibility` | E-commerce Platform | W | Enables or disables next-day delivery for postcode areas. |
| `update_promotion_start_date` | Pricing & Promotion Engine | W | Moves the start and end dates of a planned promotion. |
| `update_self_checkout_exception_rule` | Point of Sale (POS) | W | Changes a self-checkout exception rule, such as weight tolerance. |
| `update_shelf_replenishment_priority_for_product` | Store Operations Platform | W | Raises a product's shelf replenishment priority so its gaps are filled first. |
| `update_shift_for_employee` | Store Workforce Management | W | Changes the day, start or end time of an employee's shift. |
| `update_shipment_priority_for_franchise_order` | Freight Forwarder Portal | W | Expedites or changes the priority of a franchise shipment. |
| `update_wholesale_order_allocation` | Order Management System (OMS) | W | Sets the allocated quantities on open wholesale orders. |
