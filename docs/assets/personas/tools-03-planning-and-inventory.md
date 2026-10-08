# Systems and MCP tools · 03 Planning and Inventory

For each question in `questions-03-planning-and-inventory.md`, this file lists the enterprise systems an AI agent must reach and the MCP tool methods it would plausibly call, in order.
Personas and question numbers follow the questions file exactly. Follow-up prompts are covered by the same rows unless they need an additional system (noted in the row).
Tool names are shared across the nine categories; a full catalogue for this category is at the end.

**Legend:** ✎ = write or side-effect tool (requires confirmation); all other tools are read-only. `draft_` tools produce documents and are not writes.

## 22. Stock planner / replenishment analyst

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Style 5520 stocked out in 40 stores for nine days; reconstruct cause, cost and prevention | Demand Planning System, Purchase Order System, Supplier Portal, Warehouse Management System (WMS), Allocation & Replenishment System, Point of Sale (POS) | `get_forecast_by_week_for_product`, `get_purchase_orders_for_product`, `get_supplier_confirmations_for_order`, `get_goods_receipts_for_product`, `get_dc_stock_history_for_product`, `get_store_allocations_for_product`, `get_stockout_days_by_store`, `calculate_lost_sales_for_product`, `run_analysis`, `update_safety_stock_for_sku` ✎ |
| Q2 | Back from leave: which SKUs run out in four weeks, ranked by margin at risk, with expeditable supply; then expedite the top five | Inventory Management System (IMS), Supply Planning System (MRP/DRP), Costing & Margin Tool, Purchase Order System, Supplier Portal | `list_projected_stockouts`, `get_sku_margin_and_sales_at_risk`, `get_inbound_purchase_orders_for_product`, `get_supplier_available_stock`, `get_supplier_expedite_options`, `run_analysis`, `submit_expedite_request` ✎ |
| Q3 | Review reorder points and safety stock for 200 fastest sellers against variability and lead times | Inventory Management System (IMS), Demand Planning System, Purchase Order System, Inventory Optimisation Tool | `list_top_selling_skus`, `get_inventory_policy_parameters`, `get_demand_variability_by_sku`, `get_supplier_lead_time_actuals`, `calculate_safety_stock`, `compare_policy_to_recommended_parameters`, `calculate_working_capital_impact`, `update_reorder_point_for_sku` ✎, `update_safety_stock_for_sku` ✎ |
| Q4 | 14,000 seasonal throws at DC; north selling out, south overstocked; is a rebalance worth it?; if so, create the transfer | Warehouse Management System (WMS), Inventory Management System (IMS), Point of Sale (POS), Transport Management System (TMS), Allocation & Replenishment System | `get_dc_stock_for_product`, `get_store_stock_and_sales_by_region`, `get_forecast_by_week_for_product`, `calculate_transfer_cost`, `get_remaining_selling_weeks`, `calculate_rebalance_benefit`, `create_stock_transfer` ✎ |
| Q5 | Why is our out-of-stock rate up? | Inventory Management System (IMS), Point of Sale (POS), Purchase Order System, Warehouse Management System (WMS), BI & Dashboards Platform | `get_out_of_stock_rate_trend`, `get_out_of_stock_rate_by_dimension`, `list_stockout_root_causes`, `get_supplier_on_time_in_full`, `get_dc_inbound_delays`, `run_analysis` |

## 23. Demand planner

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Outerwear forecast bias +18% last month; decompose by weather, promo, price, cluster, launches | Demand Planning System, Pricing & Promotion Engine, Point of Sale (POS), Web | `get_forecast_bias_for_category`, `get_forecast_error_decomposition`, `get_promotion_calendar_for_category`, `get_price_changes_for_category`, `get_weather_history_and_forecast_archive`, `get_forecast_bias_by_market`, `run_analysis` |
| Q2 | Forecast new recycled-polyester backpack range weekly for 12 weeks, base case, range and triggers | Demand Planning System, Product Lifecycle Management (PLM), Web Analytics Platform, Trend & Market Intelligence Platform, Pricing & Promotion Engine, Documents | `search_comparable_products`, `get_sales_history_for_products`, `get_search_trend_data`, `read_document`, `get_price_positioning_for_product`, `run_new_product_forecast`, `calculate_early_sales_trigger_thresholds`, `create_forecast_override` ✎, `create_early_sales_alert` ✎ |
| Q3 | Which outside factors matter for UK and Germany winter forecast, and how big previously? | Web, Trend & Market Intelligence Platform, Demand Planning System, Commodity & Market Data Feed | `search_external_demand_drivers`, `get_weather_outlook_for_market`, `get_consumer_confidence_series`, `get_historic_driver_impact_on_category`, `list_forecast_model_external_regressors` |
| Q4 | What uplift for 25% off kitchenware in week 47? | Pricing & Promotion Engine, Demand Planning System, Point of Sale (POS) | `get_promotion_history_for_category`, `get_promotion_uplift_estimate`, `get_cannibalisation_estimate`, `get_post_promotion_dip_for_category`, `create_forecast_override` ✎ |
| Q5 | Did stockouts distort last quarter's history, and how to correct it?; correct the history for the worst items | Inventory Management System (IMS), Demand Planning System, Point of Sale (POS) | `get_stockout_periods_by_sku`, `calculate_lost_demand_for_sku`, `get_demand_history_for_sku`, `calculate_corrected_demand_history`, `update_demand_history_adjustments` ✎ |
| Q6 | If cost-of-living pressure worsens in Q1, what happens to demand by category? | Demand Planning System, Web, S&OP Platform, Market Research Platform | `get_category_demand_history_by_period`, `get_consumer_confidence_series`, `calculate_category_demand_elasticity_to_income`, `run_demand_scenario`, `search_economic_outlook`, `create_sop_scenario` ✎ |

## 24. Supply planner

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Supplier X missed confirmed ship dates on 6 of 10 orders; what's going on? | Purchase Order System, Supplier Portal, Supplier Onboarding & Risk System, Supply Planning System (MRP/DRP), Web | `get_purchase_order_history_for_supplier`, `get_supplier_ship_date_performance`, `get_supplier_capacity_report`, `search_supplier_news`, `get_supply_dependency_for_supplier`, `search_alternative_suppliers`, `create_supplier_performance_review` ✎, `block_supplier_for_new_orders` ✎ |
| Q2 | 25,000-unit gap in week 44 on denim: expedite, split supplier or shift promotion?; then raise the PO | Supply Planning System (MRP/DRP), Purchase Order System, Supplier Portal, Pricing & Promotion Engine, Costing & Margin Tool | `get_supply_demand_gap_for_product`, `get_supplier_available_capacity`, `get_supplier_lead_times`, `calculate_expedite_cost`, `calculate_split_sourcing_cost`, `get_promotion_calendar_for_category`, `compare_supply_gap_options`, `create_purchase_order` ✎, `release_purchase_order` ✎ |
| Q3 | Any zip and trim shortages affecting Q1 production; should we buy ahead? | Supply Planning System (MRP/DRP), Purchase Order System, Supplier Portal, Commodity & Market Data Feed, Web | `search_component_shortage_alerts`, `list_open_orders_using_component`, `get_supplier_delay_notices`, `get_component_price_trend`, `calculate_buy_ahead_cost`, `create_purchase_order` ✎ |
| Q4 | Any fabric shortages coming? | Supply Planning System (MRP/DRP), Supplier Portal, Commodity & Market Data Feed, Web | `search_material_shortage_alerts`, `get_fabric_requirements_by_category`, `get_supplier_capacity_report`, `search_supplier_news` |
| Q5 | Quoted lead times ~10 days shorter than actual; quantify by supplier and impact; then update planning lead times | Purchase Order System, Supply Planning System (MRP/DRP), Inventory Management System (IMS) | `get_quoted_vs_actual_lead_time_by_supplier`, `get_supplier_lead_time_actuals`, `calculate_lead_time_gap_inventory_impact`, `get_service_level_by_supplier`, `run_analysis`, `update_planning_lead_time_for_supplier` ✎ |

## 25. Merchandise planner

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Women's knitwear margin 3.2 points below plan; split by price, cost, mix, markdown, shrink | Costing & Margin Tool, Merchandise Financial Planning, Pricing & Promotion Engine, Inventory Management System (IMS) | `get_margin_variance_to_plan`, `get_margin_bridge_for_category`, `get_markdown_spend_by_category`, `get_shrink_by_category`, `get_sell_through_by_category`, `calculate_end_of_season_margin_projection`, `run_analysis` |
| Q2 | Split £2.1m spring open-to-buy across categories with optimistic and cautious cases | Merchandise Financial Planning, Range Planning & Assortment Tool, Trend & Market Intelligence Platform, Demand Planning System, Point of Sale (POS) | `get_open_to_buy_by_category`, `get_category_sell_through_trends`, `get_category_forecast`, `run_open_to_buy_scenario`, `calculate_in_season_chase_reserve`, `compare_buy_scenarios`, `update_open_to_buy_allocation` ✎ |
| Q3 | Autumn range selling slower than plan; closing stock and markdown cost, at-risk lines; cancel open orders on lines to stop | Point of Sale (POS), Inventory Management System (IMS), Merchandise Financial Planning, Pricing & Promotion Engine | `get_sell_through_vs_plan`, `get_projected_closing_stock`, `calculate_markdown_cost_projection`, `list_lines_at_risk_of_overstock`, `calculate_earlier_markdown_impact`, `list_open_orders_for_lines`, `cancel_open_purchase_order_line` ✎ |
| Q4 | Where will we end the season on stock? | Inventory Management System (IMS), Merchandise Financial Planning, Point of Sale (POS) | `get_projected_closing_stock`, `get_closing_stock_plan_gap_by_category`, `list_open_orders_for_lines`, `create_markdown_review_request` ✎ |
| Q5 | New athleisure range 20% behind plan on sell-through; product or buying and distribution? | Point of Sale (POS), Inventory Management System (IMS), Allocation & Replenishment System, Competitor Price Monitoring Tool, Web Analytics Platform, Customer Reviews & Feedback Platform, Warehouse Management System (WMS) | `get_sell_through_vs_plan`, `get_availability_by_size_and_store`, `get_size_curve_vs_sales`, `get_competitor_prices_for_range`, `get_marketing_activity_for_range`, `get_range_reviews_summary`, `get_store_sell_through_ranking`, `create_stock_transfer` ✎ |

## 27. S&OP lead

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | What changed in demand, supply and finance assumptions since last S&OP, who and why?; send once approved | S&OP Platform, Demand Planning System, Supply Planning System (MRP/DRP), Budgeting & Forecasting Tool, Documents, Email & Calendar | `get_assumption_changes_since_cycle`, `get_assumption_change_owner_and_reason`, `calculate_revenue_and_inventory_impact_of_changes`, `list_disputed_assumptions`, `draft_sop_pre_read`, `send_email` ✎ |
| Q2 | Compare three Q4 scenarios on revenue, margin, service, cash; recommend and set triggers | S&OP Platform, Demand Planning System, Supply Planning System (MRP/DRP), Pricing & Promotion Engine, Budgeting & Forecasting Tool, Treasury Management System, Email & Calendar | `get_current_plan_baseline`, `run_s_op_scenario`, `calculate_scenario_revenue_margin`, `calculate_scenario_service_level`, `calculate_scenario_cash_impact`, `compare_scenarios_risk_adjusted`, `get_scenario_assumptions`, `create_calendar_event` ✎ |
| Q3 | Biggest risks to next six months across demand, supply, cost with financial exposure | Risk Management System, S&OP Platform, Demand Planning System, Supplier Onboarding & Risk System, Commodity & Market Data Feed | `list_supply_chain_risks`, `calculate_risk_financial_exposure`, `get_risk_mitigation_options`, `get_commodity_cost_outlook`, `calculate_risk_correlation`, `run_analysis`, `create_risk_register_entry` ✎ |
| Q4 | Any macro news to reflect in next month's plan? | Web, Market Research Platform, Demand Planning System, S&OP Platform | `search_macro_economic_news`, `search_competitor_trading_updates`, `get_forecast_external_assumptions`, `compare_news_to_plan_assumptions` |
| Q5 | New-product forecast accuracy poor for three cycles; which assumptions are wrong? | Demand Planning System, S&OP Platform, Product Lifecycle Management (PLM), Allocation & Replenishment System, Point of Sale (POS) | `list_new_product_launches`, `get_new_product_forecast_accuracy`, `get_launch_assumptions_vs_actuals`, `get_forecast_error_decomposition`, `run_analysis` |
| Q6 | Service level versus inventory for top 10% SKUs and long tail; how do customers respond? | Inventory Optimisation Tool, Inventory Management System (IMS), Demand Planning System, Customer Data Platform (CDP), Web | `get_sku_abc_classification`, `get_service_level_vs_inventory_curve`, `calculate_service_level_target_options`, `get_availability_impact_on_sales`, `search_availability_research`, `get_customer_segment_exposure_to_stockouts`, `update_service_level_target_for_segment` ✎ |

## 28. Inventory optimisation analyst

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Safety stock for 500 highest-value SKUs at 97% service, vs current, with flags; then update the settings | Inventory Optimisation Tool, Inventory Management System (IMS), Demand Planning System, Purchase Order System | `list_highest_value_skus`, `get_demand_history_for_sku`, `get_supplier_lead_time_actuals`, `calculate_safety_stock`, `compare_policy_to_recommended_parameters`, `calculate_working_capital_impact`, `list_high_variability_skus`, `update_safety_stock_for_sku` ✎ |
| Q2 | 120 days cover on home textiles vs 75-day target; what's driving it? | Inventory Management System (IMS), Purchase Order System, Demand Planning System, Supplier Relationship Management (SRM) | `get_days_of_cover_by_category`, `get_excess_stock_drivers`, `get_minimum_order_quantities_for_category`, `get_forecast_bias_for_category`, `list_skus_by_excess_contribution`, `cancel_purchase_order` ✎ |
| Q3 | Asia lead times two weeks longer; which categories sensitive, hold stock or accept lower availability? | Inventory Optimisation Tool, Purchase Order System, Freight Forwarder Portal, Inventory Management System (IMS), Demand Planning System | `get_lead_times_by_origin`, `calculate_lead_time_sensitivity_by_category`, `calculate_safety_stock`, `calculate_working_capital_impact`, `compare_hold_stock_vs_accept_stockouts` |
| Q4 | Which long-tail products to hold centrally or make to order; trade-offs and savings? | Inventory Management System (IMS), Demand Planning System, Supplier Portal, Transport Management System (TMS), Network Design Tool, Supply Planning System (MRP/DRP) | `list_long_tail_skus`, `get_demand_pattern_for_sku`, `get_supplier_make_to_order_lead_times`, `calculate_centralised_stock_saving`, `calculate_transport_cost_impact`, `calculate_service_level_impact`, `update_sku_sourcing_policy` ✎ |
| Q5 | Where is our cash tied up in stock? | Inventory Management System (IMS), ERP (General Ledger), Warehouse Management System (WMS) | `get_inventory_value_by_dimension`, `get_inventory_ageing`, `compare_inventory_value_to_baseline`, `list_stock_release_options`, `create_stock_release_plan` ✎ |

## 29. Markdown / clearance analyst

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | 30% markdown on men's jackets didn't move stock; why? | Pricing & Promotion Engine, Inventory Management System (IMS), Point of Sale (POS), Competitor Price Monitoring Tool | `get_markdown_performance_for_product`, `get_size_run_breakage_for_product`, `get_competitor_prices_for_product`, `calculate_markdown_depth_scenario`, `update_markdown_price_for_product` ✎ |
| Q2 | 40 aged lines: markdown, outlet, bundle, donate or liquidate, ranked by value; then create the markdown events | Inventory Management System (IMS), Pricing & Promotion Engine, Costing & Margin Tool, Store Operations Platform, Documents, Warehouse Management System (WMS) | `read_spreadsheet_document`, `get_inventory_ageing_for_product`, `get_price_elasticity_for_product`, `calculate_clearance_option_recovery`, `get_full_price_cannibalisation_estimate`, `compare_clearance_options`, `rank_aged_lines_by_value`, `create_markdown_event` ✎, `create_stock_transfer` ✎ |
| Q3 | Sell-through and margin for 20% off in week 3 versus 40% in week 6 | Pricing & Promotion Engine, Demand Planning System, Costing & Margin Tool, Customer Data Platform (CDP) | `get_price_elasticity_for_category`, `calculate_markdown_sell_through_scenario`, `compare_markdown_scenarios`, `get_elasticity_confidence_for_category`, `get_customer_markdown_wait_behaviour`, `create_markdown_event` ✎ |
| Q4 | What are competitors doing on clearance now; where are we out of line? | Competitor Price Monitoring Tool, Web, Pricing & Promotion Engine | `get_competitor_clearance_prices`, `search_competitor_clearance_campaigns`, `get_our_markdown_depth_and_timing`, `compare_markdown_to_competitors` |
| Q5 | Where should I focus on old stock?; queue markdowns for the top group | Inventory Management System (IMS), Pricing & Promotion Engine, Costing & Margin Tool | `list_aged_stock_over_threshold`, `calculate_recovery_potential_for_lines`, `rank_aged_lines_by_value`, `get_channel_options_for_line`, `create_markdown_event` ✎, `delete_draft_markdown_event` ✎ |

## 30. Planning systems analyst

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | System proposed 12,000 units for item selling 800 a week; trace the calculation; then cancel the proposal | Supply Planning System (MRP/DRP), Allocation & Replenishment System, Demand Planning System, Master Data Management (MDM) | `get_order_proposal_calculation_trace`, `get_item_planning_parameters`, `get_demand_history_for_sku`, `get_promotion_flags_for_item`, `list_items_with_similar_parameter_issue`, `run_analysis`, `cancel_order_proposal` ✎, `update_item_planning_parameters` ✎ |
| Q2 | Which forecasts should I distrust? | Demand Planning System, Data Quality & Observability Tool, Application Monitoring & ITSM | `list_forecasts_by_error_and_bias`, `get_configuration_change_log`, `get_forecast_model_settings`, `compare_forecast_accuracy_before_after_change`, `calculate_rollback_vs_tune_impact`, `update_forecast_model_settings` ✎ |
| Q3 | What do retailers use for new and intermittent item forecasting; does our vendor support it? | Web, Demand Planning System, Documents, Knowledge Base / Policy Library | `search_forecasting_methods_research`, `search_retailer_case_studies`, `get_forecast_vendor_capabilities`, `get_current_forecast_method_for_item_type`, `get_backtest_vs_live_accuracy_evidence` |
| Q4 | Forecast slow movers at store-SKU or cluster level; compare accuracy and effort | Demand Planning System, Allocation & Replenishment System, Data Warehouse / Lakehouse | `list_slow_moving_skus`, `run_forecast_backtest`, `compare_forecast_accuracy_by_level`, `calculate_replenishment_impact`, `get_forecast_run_effort_metrics` |
| Q5 | Accuracy impact of cutting fashion history window from 52 to 26 weeks | Demand Planning System, Data Warehouse / Lakehouse | `run_forecast_backtest`, `compare_forecast_accuracy_by_history_window`, `get_forecast_accuracy_by_category`, `create_forecast_model_configuration` ✎ |

## 31. Network planner

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Compare single DC, second Midlands DC and 3PL on cost, service, resilience, five years | Network Design Tool, Transport Management System (TMS), Warehouse Management System (WMS), Retail Property & Footfall System, Budgeting & Forecasting Tool, Web | `get_network_baseline_costs`, `get_store_and_customer_delivery_volumes`, `run_network_scenario`, `calculate_network_total_cost`, `calculate_delivery_time_by_scenario`, `calculate_break_even_volume`, `run_sensitivity_analysis`, `get_industrial_rent_benchmarks` |
| Q2 | What volumes should the network handle in 2030 by region and channel? | Demand Planning System, Network Design Tool, Strategy & Board Reporting Tool, E-commerce Platform | `get_volume_history_by_region_and_channel`, `get_long_term_growth_plan`, `run_network_volume_forecast`, `run_sensitivity_analysis`, `get_ecommerce_share_forecast` |
| Q3 | Compare property, rents, labour and incentives across three shortlisted sites, with risks | Web, Retail Property & Footfall System, Network Design Tool, Knowledge Base / Policy Library | `get_site_shortlist`, `search_industrial_property_availability`, `get_labour_cost_and_supply_by_region`, `search_local_incentives`, `search_planning_and_transport_risks`, `search_retailer_activity_in_area`, `remove_site_from_shortlist` ✎ |
| Q4 | Where are the biggest network inefficiencies: cross-shipping, split orders, long hauls, idle sites? | Order Management System (OMS), Transport Management System (TMS), Warehouse Management System (WMS), Network Design Tool, Project & Portfolio Management Tool | `get_cross_shipping_rate`, `get_split_order_rate`, `get_long_haul_shipments`, `get_dc_utilisation`, `rank_network_inefficiencies`, `calculate_inefficiency_fix_cost`, `create_project` ✎ |
| Q5 | Should we close the small southern DC; build business case including redundancy; send to the CFO once reviewed | Network Design Tool, ERP (General Ledger), HR Information System (HRIS), Transport Management System (TMS), Warehouse Management System (WMS), Email & Calendar | `get_dc_cost_and_volume_profile`, `run_network_scenario`, `calculate_redundancy_cost`, `calculate_transport_cost_impact`, `calculate_service_impact`, `calculate_peak_capacity_risk`, `draft_business_case`, `send_email` ✎ |
| Q6 | How resilient are we if one DC is offline for two weeks? | Network Design Tool, Warehouse Management System (WMS), Inventory Management System (IMS), Transport Management System (TMS), Risk Management System | `run_dc_outage_scenario`, `calculate_dc_outage_service_impact`, `get_alternative_dc_capacity`, `calculate_buffer_stock_requirement`, `rank_dcs_by_single_point_of_failure_risk`, `create_risk_register_entry` ✎ |

## Tool catalogue for this category

| Tool | System | R/W | One-line description |
|---|---|---|---|
| `block_supplier_for_new_orders` | Supplier Relationship Management (SRM) | W | Places a hold on a supplier so no new purchase orders can be raised. |
| `calculate_break_even_volume` | Network Design Tool | R | Calculate break even volume. |
| `calculate_buffer_stock_requirement` | Network Design Tool | R | Calculate buffer stock requirement. |
| `calculate_buy_ahead_cost` | Supply Planning System (MRP/DRP) | R | Calculate buy ahead cost. |
| `calculate_category_demand_elasticity_to_income` | Pricing & Promotion Engine | R | Calculate category demand elasticity to income. |
| `calculate_centralised_stock_saving` | Inventory Optimisation Tool | R | Calculate centralised stock saving. |
| `calculate_clearance_option_recovery` | Pricing & Promotion Engine | R | Calculate clearance option recovery. |
| `calculate_corrected_demand_history` | Demand Planning System | R | Calculate corrected demand history. |
| `calculate_dc_outage_service_impact` | Network Design Tool | R | Calculate dc outage service impact. |
| `calculate_delivery_time_by_scenario` | Transport Management System (TMS) | R | Calculate delivery time by scenario. |
| `calculate_earlier_markdown_impact` | Pricing & Promotion Engine | R | Calculate earlier markdown impact. |
| `calculate_early_sales_trigger_thresholds` | Demand Planning System | R | Calculate early sales trigger thresholds. |
| `calculate_end_of_season_margin_projection` | Costing & Margin Tool | R | Calculate end of season margin projection. |
| `calculate_expedite_cost` | Supply Planning System (MRP/DRP) | R | Calculate expedite cost. |
| `calculate_in_season_chase_reserve` | Merchandise Financial Planning | R | Calculate in season chase reserve. |
| `calculate_inefficiency_fix_cost` | Network Design Tool | R | Calculate inefficiency fix cost. |
| `calculate_lead_time_gap_inventory_impact` | Supply Planning System (MRP/DRP) | R | Calculate lead time gap inventory impact. |
| `calculate_lead_time_sensitivity_by_category` | Inventory Optimisation Tool | R | Calculate lead time sensitivity by category. |
| `calculate_lost_demand_for_sku` | Demand Planning System | R | Calculate lost demand for sku. |
| `calculate_lost_sales_for_product` | Demand Planning System | R | Calculate lost sales for product. |
| `calculate_markdown_cost_projection` | Pricing & Promotion Engine | R | Calculate markdown cost projection. |
| `calculate_markdown_depth_scenario` | Pricing & Promotion Engine | R | Calculate markdown depth scenario. |
| `calculate_markdown_sell_through_scenario` | Pricing & Promotion Engine | R | Calculate markdown sell through scenario. |
| `calculate_network_total_cost` | Network Design Tool | R | Calculate network total cost. |
| `calculate_peak_capacity_risk` | Network Design Tool | R | Calculate peak capacity risk. |
| `calculate_rebalance_benefit` | Allocation & Replenishment System | R | Calculate rebalance benefit. |
| `calculate_recovery_potential_for_lines` | Costing & Margin Tool | R | Calculate recovery potential for lines. |
| `calculate_redundancy_cost` | Network Design Tool | R | Calculate redundancy cost. |
| `calculate_replenishment_impact` | Allocation & Replenishment System | R | Calculate replenishment impact. |
| `calculate_revenue_and_inventory_impact_of_changes` | Inventory Management System (IMS) | R | Calculate revenue and inventory impact of changes. |
| `calculate_risk_correlation` | Risk Management System | R | Calculate risk correlation. |
| `calculate_risk_financial_exposure` | Risk Management System | R | Calculate risk financial exposure. |
| `calculate_rollback_vs_tune_impact` | Demand Planning System | R | Calculate rollback vs tune impact. |
| `calculate_safety_stock` | Inventory Optimisation Tool | R | Calculate safety stock. |
| `calculate_scenario_cash_impact` | S&OP Platform | R | Calculate scenario cash impact. |
| `calculate_scenario_revenue_margin` | S&OP Platform | R | Calculate scenario revenue margin. |
| `calculate_scenario_service_level` | S&OP Platform | R | Calculate scenario service level. |
| `calculate_service_impact` | Network Design Tool | R | Calculate service impact. |
| `calculate_service_level_impact` | Inventory Optimisation Tool | R | Calculate service level impact. |
| `calculate_service_level_target_options` | Inventory Optimisation Tool | R | Calculate service level target options. |
| `calculate_split_sourcing_cost` | Supply Planning System (MRP/DRP) | R | Calculate split sourcing cost. |
| `calculate_transfer_cost` | Transport Management System (TMS) | R | Calculate transfer cost. |
| `calculate_transport_cost_impact` | Transport Management System (TMS) | R | Calculate transport cost impact. |
| `calculate_working_capital_impact` | Inventory Optimisation Tool | R | Calculate working capital impact. |
| `cancel_open_purchase_order_line` | Purchase Order System | W | Cancels individual open lines on a purchase order. |
| `cancel_order_proposal` | Supply Planning System (MRP/DRP) | W | Cancels a system-generated order proposal before conversion to a PO. |
| `cancel_purchase_order` | Purchase Order System | W | Cancels an open purchase order that has not yet shipped. |
| `compare_buy_scenarios` | Merchandise Financial Planning | R | Compare buy scenarios. |
| `compare_clearance_options` | Pricing & Promotion Engine | R | Compare clearance options. |
| `compare_forecast_accuracy_before_after_change` | Demand Planning System | R | Compare forecast accuracy before after change. |
| `compare_forecast_accuracy_by_history_window` | Demand Planning System | R | Compare forecast accuracy by history window. |
| `compare_forecast_accuracy_by_level` | Demand Planning System | R | Compare forecast accuracy by level. |
| `compare_hold_stock_vs_accept_stockouts` | Inventory Optimisation Tool | R | Compare hold stock vs accept stockouts. |
| `compare_inventory_value_to_baseline` | Inventory Management System (IMS) | R | Compare inventory value to baseline. |
| `compare_markdown_scenarios` | Pricing & Promotion Engine | R | Compare markdown scenarios. |
| `compare_markdown_to_competitors` | Competitor Price Monitoring Tool | R | Compare markdown to competitors. |
| `compare_news_to_plan_assumptions` | S&OP Platform | R | Compare news to plan assumptions. |
| `compare_policy_to_recommended_parameters` | Inventory Optimisation Tool | R | Compare policy to recommended parameters. |
| `compare_scenarios_risk_adjusted` | S&OP Platform | R | Compare scenarios risk adjusted. |
| `compare_supply_gap_options` | Supply Planning System (MRP/DRP) | R | Compare supply gap options. |
| `create_calendar_event` | Email & Calendar | W | Creates a calendar event and invites attendees. |
| `create_early_sales_alert` | Demand Planning System | W | Creates a monitoring alert that fires when early sales cross chase or cancel thresholds. |
| `create_forecast_model_configuration` | Demand Planning System | W | Creates a test forecast configuration, for example a different history window. |
| `create_forecast_override` | Demand Planning System | W | Adds a manual forecast override (uplift or base case) to given products and weeks. |
| `create_markdown_event` | Pricing & Promotion Engine | W | Creates a scheduled markdown event for selected lines. |
| `create_markdown_review_request` | Pricing & Promotion Engine | W | Creates a markdown review request for a category or line for the pricing team. |
| `create_project` | Project & Portfolio Management Tool | W | Creates a project with owner and tasks. |
| `create_purchase_order` | Purchase Order System | W | Creates a draft purchase order for a supplier, product and quantity. |
| `create_risk_register_entry` | Risk Management System | W | Adds a new risk, with owner and exposure, to the risk register. |
| `create_sop_scenario` | S&OP Platform | W | Saves a new named scenario with its assumptions in the S&OP cycle. |
| `create_stock_release_plan` | Inventory Management System (IMS) | W | Creates a plan of actions to release stock for selected areas. |
| `create_stock_transfer` | Warehouse Management System (WMS) | W | Creates a transfer order moving stock from one DC or store to another. |
| `create_supplier_performance_review` | Supplier Relationship Management (SRM) | W | Opens a supplier performance review record and schedules the review. |
| `delete_draft_markdown_event` | Pricing & Promotion Engine | W | Deletes a draft markdown event that has not gone live. |
| `draft_business_case` | Network Design Tool | R | Draft business case. |
| `draft_sop_pre_read` | S&OP Platform | R | Draft sop pre read. |
| `get_alternative_dc_capacity` | Network Design Tool | R | Retrieve alternative dc capacity. |
| `get_assumption_change_owner_and_reason` | S&OP Platform | R | Retrieve assumption change owner and reason. |
| `get_assumption_changes_since_cycle` | S&OP Platform | R | Retrieve assumption changes since cycle. |
| `get_availability_by_size_and_store` | Inventory Management System (IMS) | R | Retrieve availability by size and store. |
| `get_availability_impact_on_sales` | Point of Sale (POS) | R | Retrieve availability impact on sales. |
| `get_backtest_vs_live_accuracy_evidence` | Demand Planning System | R | Retrieve backtest vs live accuracy evidence. |
| `get_cannibalisation_estimate` | Pricing & Promotion Engine | R | Retrieve cannibalisation estimate. |
| `get_category_demand_history_by_period` | Demand Planning System | R | Retrieve category demand history by period. |
| `get_category_forecast` | Demand Planning System | R | Retrieve category forecast. |
| `get_category_sell_through_trends` | Merchandise Financial Planning | R | Retrieve category sell through trends. |
| `get_channel_options_for_line` | Store Operations Platform | R | Retrieve channel options for line. |
| `get_closing_stock_plan_gap_by_category` | Inventory Management System (IMS) | R | Retrieve closing stock plan gap by category. |
| `get_commodity_cost_outlook` | Commodity & Market Data Feed | R | Retrieve commodity cost outlook. |
| `get_competitor_clearance_prices` | Competitor Price Monitoring Tool | R | Retrieve competitor clearance prices. |
| `get_competitor_prices_for_product` | Competitor Price Monitoring Tool | R | Retrieve competitor prices for product. |
| `get_competitor_prices_for_range` | Competitor Price Monitoring Tool | R | Retrieve competitor prices for range. |
| `get_component_price_trend` | Commodity & Market Data Feed | R | Retrieve component price trend. |
| `get_configuration_change_log` | Demand Planning System | R | Retrieve configuration change log. |
| `get_consumer_confidence_series` | Web | R | Retrieve consumer confidence series. |
| `get_cross_shipping_rate` | Order Management System (OMS) | R | Retrieve cross shipping rate. |
| `get_current_forecast_method_for_item_type` | Demand Planning System | R | Retrieve current forecast method for item type. |
| `get_current_plan_baseline` | S&OP Platform | R | Retrieve current plan baseline. |
| `get_customer_markdown_wait_behaviour` | Customer Data Platform (CDP) | R | Retrieve customer markdown wait behaviour. |
| `get_customer_segment_exposure_to_stockouts` | Customer Data Platform (CDP) | R | Retrieve customer segment exposure to stockouts. |
| `get_days_of_cover_by_category` | Inventory Management System (IMS) | R | Retrieve days of cover by category. |
| `get_dc_cost_and_volume_profile` | Network Design Tool | R | Retrieve dc cost and volume profile. |
| `get_dc_inbound_delays` | Warehouse Management System (WMS) | R | Retrieve dc inbound delays. |
| `get_dc_stock_for_product` | Warehouse Management System (WMS) | R | Retrieve dc stock for product. |
| `get_dc_stock_history_for_product` | Warehouse Management System (WMS) | R | Retrieve dc stock history for product. |
| `get_dc_utilisation` | Warehouse Management System (WMS) | R | Retrieve dc utilisation. |
| `get_demand_history_for_sku` | Demand Planning System | R | Retrieve demand history for sku. |
| `get_demand_pattern_for_sku` | Inventory Optimisation Tool | R | Retrieve demand pattern for sku. |
| `get_demand_variability_by_sku` | Demand Planning System | R | Retrieve demand variability by sku. |
| `get_ecommerce_share_forecast` | Network Design Tool | R | Retrieve ecommerce share forecast. |
| `get_elasticity_confidence_for_category` | Pricing & Promotion Engine | R | Retrieve elasticity confidence for category. |
| `get_excess_stock_drivers` | Inventory Management System (IMS) | R | Retrieve excess stock drivers. |
| `get_fabric_requirements_by_category` | Supply Planning System (MRP/DRP) | R | Retrieve fabric requirements by category. |
| `get_forecast_accuracy_by_category` | Demand Planning System | R | Retrieve forecast accuracy by category. |
| `get_forecast_bias_by_market` | Demand Planning System | R | Retrieve forecast bias by market. |
| `get_forecast_bias_for_category` | Demand Planning System | R | Retrieve forecast bias for category. |
| `get_forecast_by_week_for_product` | Demand Planning System | R | Retrieve forecast by week for product. |
| `get_forecast_error_decomposition` | Demand Planning System | R | Retrieve forecast error decomposition. |
| `get_forecast_external_assumptions` | S&OP Platform | R | Retrieve forecast external assumptions. |
| `get_forecast_model_settings` | Demand Planning System | R | Retrieve forecast model settings. |
| `get_forecast_run_effort_metrics` | Demand Planning System | R | Retrieve forecast run effort metrics. |
| `get_forecast_vendor_capabilities` | Demand Planning System | R | Retrieve forecast vendor capabilities. |
| `get_full_price_cannibalisation_estimate` | Pricing & Promotion Engine | R | Retrieve full price cannibalisation estimate. |
| `get_goods_receipts_for_product` | Warehouse Management System (WMS) | R | Retrieve goods receipts for product. |
| `get_historic_driver_impact_on_category` | Demand Planning System | R | Retrieve historic driver impact on category. |
| `get_inbound_purchase_orders_for_product` | Purchase Order System | R | Retrieve inbound purchase orders for product. |
| `get_industrial_rent_benchmarks` | Web | R | Retrieve industrial rent benchmarks. |
| `get_inventory_ageing` | Inventory Management System (IMS) | R | Retrieve inventory ageing. |
| `get_inventory_ageing_for_product` | Inventory Management System (IMS) | R | Retrieve inventory ageing for product. |
| `get_inventory_policy_parameters` | Inventory Optimisation Tool | R | Retrieve inventory policy parameters. |
| `get_inventory_value_by_dimension` | Inventory Management System (IMS) | R | Retrieve inventory value by dimension. |
| `get_item_planning_parameters` | Supply Planning System (MRP/DRP) | R | Retrieve item planning parameters. |
| `get_labour_cost_and_supply_by_region` | Network Design Tool | R | Retrieve labour cost and supply by region. |
| `get_launch_assumptions_vs_actuals` | S&OP Platform | R | Retrieve launch assumptions vs actuals. |
| `get_lead_times_by_origin` | Supply Planning System (MRP/DRP) | R | Retrieve lead times by origin. |
| `get_long_haul_shipments` | Transport Management System (TMS) | R | Retrieve long haul shipments. |
| `get_long_term_growth_plan` | Network Design Tool | R | Retrieve long term growth plan. |
| `get_margin_bridge_for_category` | Costing & Margin Tool | R | Retrieve margin bridge for category. |
| `get_margin_variance_to_plan` | Costing & Margin Tool | R | Retrieve margin variance to plan. |
| `get_markdown_performance_for_product` | Pricing & Promotion Engine | R | Retrieve markdown performance for product. |
| `get_markdown_spend_by_category` | Pricing & Promotion Engine | R | Retrieve markdown spend by category. |
| `get_marketing_activity_for_range` | Web Analytics Platform | R | Retrieve marketing activity for range. |
| `get_minimum_order_quantities_for_category` | Purchase Order System | R | Retrieve minimum order quantities for category. |
| `get_network_baseline_costs` | Network Design Tool | R | Retrieve network baseline costs. |
| `get_new_product_forecast_accuracy` | Demand Planning System | R | Retrieve new product forecast accuracy. |
| `get_open_to_buy_by_category` | Merchandise Financial Planning | R | Retrieve open to buy by category. |
| `get_order_proposal_calculation_trace` | Supply Planning System (MRP/DRP) | R | Retrieve order proposal calculation trace. |
| `get_our_markdown_depth_and_timing` | Pricing & Promotion Engine | R | Retrieve our markdown depth and timing. |
| `get_out_of_stock_rate_by_dimension` | Inventory Management System (IMS) | R | Retrieve out of stock rate by dimension. |
| `get_out_of_stock_rate_trend` | Inventory Management System (IMS) | R | Retrieve out of stock rate trend. |
| `get_post_promotion_dip_for_category` | Pricing & Promotion Engine | R | Retrieve post promotion dip for category. |
| `get_price_changes_for_category` | Pricing & Promotion Engine | R | Retrieve price changes for category. |
| `get_price_elasticity_for_category` | Pricing & Promotion Engine | R | Retrieve price elasticity for category. |
| `get_price_elasticity_for_product` | Pricing & Promotion Engine | R | Retrieve price elasticity for product. |
| `get_price_positioning_for_product` | Pricing & Promotion Engine | R | Retrieve price positioning for product. |
| `get_projected_closing_stock` | Inventory Management System (IMS) | R | Retrieve projected closing stock. |
| `get_promotion_calendar_for_category` | Pricing & Promotion Engine | R | Retrieve promotion calendar for category. |
| `get_promotion_flags_for_item` | Pricing & Promotion Engine | R | Retrieve promotion flags for item. |
| `get_promotion_history_for_category` | Pricing & Promotion Engine | R | Retrieve promotion history for category. |
| `get_promotion_uplift_estimate` | Pricing & Promotion Engine | R | Retrieve promotion uplift estimate. |
| `get_purchase_order_history_for_supplier` | Purchase Order System | R | Retrieve purchase order history for supplier. |
| `get_purchase_orders_for_product` | Purchase Order System | R | Retrieve purchase orders for product. |
| `get_quoted_vs_actual_lead_time_by_supplier` | Purchase Order System | R | Retrieve quoted vs actual lead time by supplier. |
| `get_range_reviews_summary` | Customer Reviews & Feedback Platform | R | Retrieve range reviews summary. |
| `get_remaining_selling_weeks` | Inventory Management System (IMS) | R | Retrieve remaining selling weeks. |
| `get_risk_mitigation_options` | Risk Management System | R | Retrieve risk mitigation options. |
| `get_sales_history_for_products` | Demand Planning System | R | Retrieve sales history for products. |
| `get_scenario_assumptions` | S&OP Platform | R | Retrieve scenario assumptions. |
| `get_search_trend_data` | Web Analytics Platform | R | Retrieve search trend data. |
| `get_sell_through_by_category` | Merchandise Financial Planning | R | Retrieve sell through by category. |
| `get_sell_through_vs_plan` | Merchandise Financial Planning | R | Retrieve sell through vs plan. |
| `get_service_level_by_supplier` | Purchase Order System | R | Retrieve service level by supplier. |
| `get_service_level_vs_inventory_curve` | Inventory Optimisation Tool | R | Retrieve service level vs inventory curve. |
| `get_shrink_by_category` | Costing & Margin Tool | R | Retrieve shrink by category. |
| `get_site_shortlist` | Network Design Tool | R | Retrieve site shortlist. |
| `get_size_curve_vs_sales` | Point of Sale (POS) | R | Retrieve size curve vs sales. |
| `get_size_run_breakage_for_product` | Inventory Management System (IMS) | R | Retrieve size run breakage for product. |
| `get_sku_abc_classification` | Inventory Optimisation Tool | R | Retrieve sku abc classification. |
| `get_sku_margin_and_sales_at_risk` | Costing & Margin Tool | R | Retrieve sku margin and sales at risk. |
| `get_split_order_rate` | Order Management System (OMS) | R | Retrieve split order rate. |
| `get_stockout_days_by_store` | Inventory Management System (IMS) | R | Retrieve stockout days by store. |
| `get_stockout_periods_by_sku` | Inventory Management System (IMS) | R | Retrieve stockout periods by sku. |
| `get_store_allocations_for_product` | Allocation & Replenishment System | R | Retrieve store allocations for product. |
| `get_store_and_customer_delivery_volumes` | Network Design Tool | R | Retrieve store and customer delivery volumes. |
| `get_store_sell_through_ranking` | Point of Sale (POS) | R | Retrieve store sell through ranking. |
| `get_store_stock_and_sales_by_region` | Allocation & Replenishment System | R | Retrieve store stock and sales by region. |
| `get_supplier_available_capacity` | Supplier Portal | R | Retrieve supplier available capacity. |
| `get_supplier_available_stock` | Supplier Portal | R | Retrieve supplier available stock. |
| `get_supplier_capacity_report` | Supplier Portal | R | Retrieve supplier capacity report. |
| `get_supplier_confirmations_for_order` | Purchase Order System | R | Retrieve supplier confirmations for order. |
| `get_supplier_delay_notices` | Supplier Portal | R | Retrieve supplier delay notices. |
| `get_supplier_expedite_options` | Supplier Portal | R | Retrieve supplier expedite options. |
| `get_supplier_lead_time_actuals` | Purchase Order System | R | Retrieve supplier lead time actuals. |
| `get_supplier_lead_times` | Purchase Order System | R | Retrieve supplier lead times. |
| `get_supplier_make_to_order_lead_times` | Supplier Portal | R | Retrieve supplier make to order lead times. |
| `get_supplier_on_time_in_full` | Purchase Order System | R | Retrieve supplier on time in full. |
| `get_supplier_ship_date_performance` | Supplier Portal | R | Retrieve supplier ship date performance. |
| `get_supply_demand_gap_for_product` | Supply Planning System (MRP/DRP) | R | Retrieve supply demand gap for product. |
| `get_supply_dependency_for_supplier` | Supplier Portal | R | Retrieve supply dependency for supplier. |
| `get_volume_history_by_region_and_channel` | Network Design Tool | R | Retrieve volume history by region and channel. |
| `get_weather_history_and_forecast_archive` | Web | R | Retrieve weather history and forecast archive. |
| `get_weather_outlook_for_market` | Web | R | Retrieve weather outlook for market. |
| `list_aged_stock_over_threshold` | Inventory Management System (IMS) | R | List aged stock over threshold. |
| `list_disputed_assumptions` | S&OP Platform | R | List disputed assumptions. |
| `list_forecast_model_external_regressors` | Demand Planning System | R | List forecast model external regressors. |
| `list_forecasts_by_error_and_bias` | Demand Planning System | R | List forecasts by error and bias. |
| `list_high_variability_skus` | Inventory Optimisation Tool | R | List high variability skus. |
| `list_highest_value_skus` | Inventory Management System (IMS) | R | List highest value skus. |
| `list_items_with_similar_parameter_issue` | Supply Planning System (MRP/DRP) | R | List items with similar parameter issue. |
| `list_lines_at_risk_of_overstock` | Inventory Management System (IMS) | R | List lines at risk of overstock. |
| `list_long_tail_skus` | Inventory Management System (IMS) | R | List long tail skus. |
| `list_new_product_launches` | Demand Planning System | R | List new product launches. |
| `list_open_orders_for_lines` | Purchase Order System | R | List open orders for lines. |
| `list_open_orders_using_component` | Purchase Order System | R | List open orders using component. |
| `list_projected_stockouts` | Inventory Management System (IMS) | R | List projected stockouts. |
| `list_skus_by_excess_contribution` | Inventory Management System (IMS) | R | List skus by excess contribution. |
| `list_slow_moving_skus` | Inventory Management System (IMS) | R | List slow moving skus. |
| `list_stock_release_options` | Inventory Management System (IMS) | R | List stock release options. |
| `list_stockout_root_causes` | Inventory Management System (IMS) | R | List stockout root causes. |
| `list_supply_chain_risks` | Risk Management System | R | List supply chain risks. |
| `list_top_selling_skus` | Demand Planning System | R | List top selling skus. |
| `rank_aged_lines_by_value` | Code Execution | R | Rank aged lines by value. |
| `rank_dcs_by_single_point_of_failure_risk` | Code Execution | R | Rank dcs by single point of failure risk. |
| `rank_network_inefficiencies` | Code Execution | R | Rank network inefficiencies. |
| `read_document` | Documents | R | Read document. |
| `read_spreadsheet_document` | Documents | R | Read spreadsheet document. |
| `release_purchase_order` | Purchase Order System | W | Releases an approved draft purchase order to the supplier. |
| `remove_site_from_shortlist` | Network Design Tool | W | Removes a site from the network shortlist. |
| `run_analysis` | Code Execution | R | Run a modelled analysis. |
| `run_dc_outage_scenario` | Network Design Tool | R | Run a modelled dc outage scenario. |
| `run_demand_scenario` | Demand Planning System | R | Run a modelled demand scenario. |
| `run_forecast_backtest` | Demand Planning System | R | Run a modelled forecast backtest. |
| `run_network_scenario` | Network Design Tool | R | Run a modelled network scenario. |
| `run_network_volume_forecast` | Network Design Tool | R | Run a modelled network volume forecast. |
| `run_new_product_forecast` | Demand Planning System | R | Run a modelled new product forecast. |
| `run_open_to_buy_scenario` | Merchandise Financial Planning | R | Run a modelled open to buy scenario. |
| `run_s_op_scenario` | S&OP Platform | R | Run a modelled s op scenario. |
| `run_sensitivity_analysis` | Code Execution | R | Run a modelled sensitivity analysis. |
| `search_alternative_suppliers` | Supplier Portal | R | Search public sources for alternative suppliers. |
| `search_availability_research` | Web | R | Search public sources for availability research. |
| `search_comparable_products` | Demand Planning System | R | Search public sources for comparable products. |
| `search_competitor_clearance_campaigns` | Web | R | Search public sources for competitor clearance campaigns. |
| `search_competitor_trading_updates` | Web | R | Search public sources for competitor trading updates. |
| `search_component_shortage_alerts` | Web | R | Search public sources for component shortage alerts. |
| `search_economic_outlook` | Web | R | Search public sources for economic outlook. |
| `search_external_demand_drivers` | Web | R | Search public sources for external demand drivers. |
| `search_forecasting_methods_research` | Web | R | Search public sources for forecasting methods research. |
| `search_industrial_property_availability` | Web | R | Search public sources for industrial property availability. |
| `search_local_incentives` | Web | R | Search public sources for local incentives. |
| `search_macro_economic_news` | Web | R | Search public sources for macro economic news. |
| `search_material_shortage_alerts` | Web | R | Search public sources for material shortage alerts. |
| `search_planning_and_transport_risks` | Web | R | Search public sources for planning and transport risks. |
| `search_retailer_activity_in_area` | Web | R | Search public sources for retailer activity in area. |
| `search_retailer_case_studies` | Web | R | Search public sources for retailer case studies. |
| `search_supplier_news` | Web | R | Search public sources for supplier news. |
| `send_email` | Email & Calendar | W | Sends an email, with attachments, to named recipients. |
| `submit_expedite_request` | Supplier Portal | W | Sends a request to a supplier to bring forward delivery of open order lines. |
| `update_demand_history_adjustments` | Demand Planning System | W | Changes the corrections applied to demand history for stockout-distorted periods. |
| `update_forecast_model_settings` | Demand Planning System | W | Changes forecast model settings, including rolling back a configuration change. |
| `update_item_planning_parameters` | Supply Planning System (MRP/DRP) | W | Changes planning parameters (lead time, pack size, lot size) on an item. |
| `update_markdown_price_for_product` | Pricing & Promotion Engine | W | Changes the live markdown depth on a product. |
| `update_open_to_buy_allocation` | Merchandise Financial Planning | W | Changes open-to-buy budget allocated to categories, including the unallocated reserve. |
| `update_planning_lead_time_for_supplier` | Supply Planning System (MRP/DRP) | W | Changes the lead time used in planning for a supplier. |
| `update_reorder_point_for_sku` | Inventory Management System (IMS) | W | Changes the reorder point on a SKU so replenishment triggers earlier or later. |
| `update_safety_stock_for_sku` | Inventory Management System (IMS) | W | Changes the safety stock quantity held on a SKU (optionally by location). |
| `update_service_level_target_for_segment` | Inventory Optimisation Tool | W | Changes the target service level for an SKU segment. |
| `update_sku_sourcing_policy` | Supply Planning System (MRP/DRP) | W | Changes a SKU between stocked and make-to-order sourcing. |
