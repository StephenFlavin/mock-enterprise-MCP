# Systems and MCP tools · 04 Procurement and Sourcing

For each question in the Procurement and Sourcing questions file, this lists the enterprise systems an AI agent must reach and the MCP tool methods it would call.
Tool names are shared across all nine categories so the benchmark stays consistent; the catalogue at the end defines each one.
Tools are listed in likely call order; follow-up questions reuse the same tools unless noted.

**Legend:** `get_`/`list_`/`search_`/`calculate_`/`compare_`/`run_` = read; `draft_` = produces a draft only (not a write); ✎ = write or side-effect tool. Write tools take effect only after the user has confirmed the action in conversation.


## 32. Category buyer

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Why is Supplier A £4.80 versus B £4.10 on the same bottle? Should-cost at 50k and questions | Documents, Cost Modelling Tool, Commodity & Market Data Feed, Contract Management System, Purchase Order System, Email & Calendar | `read_document_attachment`, `extract_quote_line_items`, `get_commodity_price_history`, `get_historical_unit_price_for_product`, `calculate_should_cost`, `compare_quotes_by_cost_component`, `get_contract_terms_for_supplier`, `send_supplier_query_email` ✎ |
| Q2 | 304 stainless price trend over 12 months and our bottle cost exposure | Commodity & Market Data Feed, Costing & Margin Tool | `get_commodity_price_history`, `get_commodity_price_forecast`, `get_material_cost_share_for_product`, `calculate_commodity_cost_exposure` |
| Q3 | Compare three bedding suppliers on landed cost, lead time, quality, compliance, capacity; who gets volume | Landed Cost Calculator, Supplier Relationship Management (SRM), Quality Management System (QMS), Factory Audit Platform, Supplier Portal, Documents, Sourcing / RFx Platform, Purchase Order System | `list_suppliers_for_category`, `calculate_landed_cost_by_supplier`, `get_supplier_lead_time_performance`, `get_supplier_quality_record`, `get_supplier_audit_status`, `get_supplier_capacity_commitments`, `run_analysis`, `draft_sourcing_recommendation`, `create_sourcing_award` ✎, `create_purchase_order` ✎, `cancel_purchase_order` ✎ |
| Q4 | Competitor prices for 750ml insulated bottle, implied target cost, product changes to get there | Competitor Price Monitoring Tool, Costing & Margin Tool, Product Lifecycle Management (PLM), Customer Reviews & Feedback Platform, Web | `search_competitor_prices_for_product`, `get_competitor_price_history`, `get_target_margin_for_category`, `calculate_target_cost`, `get_product_bom_and_cost_breakdown`, `search_customer_review_themes` |
| Q5 | Effect of inflation, FX and tariffs on housewares margin: three scenarios, exposed suppliers, levers | Budgeting & Forecasting Tool, FX & Hedging Platform, Tax & Duty System, Commodity & Market Data Feed, Spend Analytics Platform, Web | `get_category_margin_plan`, `get_fx_forward_curve`, `get_fx_hedge_cover_by_currency`, `get_tariff_rates_for_category_origin`, `get_supplier_spend_by_currency`, `search_web`, `calculate_margin_scenario`, `run_analysis`, `update_category_margin_plan` ✎ |
| Q6 | Any suppliers in trouble (delivery, quality, financial, news) and my reliance on top three | Supplier Onboarding & Risk System, Quality Management System (QMS), Purchase Order System, Spend Analytics Platform, Web | `list_suppliers_with_risk_alerts`, `get_supplier_on_time_delivery_trend`, `get_supplier_quality_incidents`, `get_supplier_financial_health_score`, `search_web`, `get_supplier_share_of_category_spend`, `create_supplier_issue_record` ✎ |
| Q7 | Two-page negotiation brief for annual review with largest cookware supplier | Supplier Relationship Management (SRM), Spend Analytics Platform, Contract Management System, Commodity & Market Data Feed, Sourcing / RFx Platform, Documents, Email & Calendar | `get_supplier_scorecard_history`, `get_supplier_share_of_wallet`, `list_alternative_suppliers_for_category`, `get_contract_terms_for_supplier`, `get_price_benchmark_for_category`, `get_payment_terms_benchmark`, `run_analysis`, `draft_negotiation_brief`, `create_calendar_event` ✎ |
| Q8 | Small appliances buying margin down 2.5 points: decompose by cost, FX, mix, supplier | Costing & Margin Tool, Purchase Order System, FX & Hedging Platform, Data Warehouse / Lakehouse, Supplier Relationship Management (SRM) | `get_buying_margin_by_category_period`, `get_purchase_price_variance_by_item`, `get_fx_rates_history`, `get_sales_mix_by_item`, `calculate_margin_bridge`, `calculate_renegotiation_recovery` |

## 33. Sourcing manager, Asia

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Factory F 10 to 14 days late five orders running: what is the cause? | Supplier Portal, Factory Audit Platform, Purchase Order System, Web | `get_order_delay_history_for_factory`, `get_factory_production_reports`, `get_factory_audit_findings`, `get_factory_material_inbound_status`, `search_web`, `list_alternative_factories_for_product`, `calculate_expedite_cost_options` |
| Q2 | Wage trends in Vietnam, Cambodia, Bangladesh and effect on 2027 FOB prices | Web, Costing & Margin Tool, Knowledge Base / Policy Library | `search_web`, `fetch_web_page`, `search_labour_dispute_news`, `get_fob_price_history_by_country`, `calculate_wage_impact_on_fob` |
| Q3 | Move 20% of denim (600k units) from Bangladesh to Vietnam? Cost, lead time, risk, transition | Costing & Margin Tool, Landed Cost Calculator, Tax & Duty System, Freight Rate Management System, Factory Audit Platform, Supplier Onboarding & Risk System, Sampling & Development Tracker | `get_volume_by_origin_region`, `calculate_landed_cost_by_origin`, `get_tariff_rates_for_category_origin`, `get_ocean_freight_rates_for_lane`, `search_factories_by_capability_and_country`, `get_supplier_audit_status`, `get_supplier_qualification_time_and_cost`, `get_factory_moq_terms`, `run_analysis`, `create_rfq` ✎ |
| Q4 | Which factories exceed 90% capacity in peak months? | Supplier Portal, Purchase Order System | `get_factory_capacity_utilisation`, `compare_capacity_utilisation_year_on_year`, `list_open_orders_at_factory`, `get_order_readiness_status`, `update_purchase_order_ship_date` ✎ |
| Q5 | Disruption risks in sourcing countries this season, exposed orders, contingency | Web, Risk Management System, Purchase Order System, Track & Trace Platform, Knowledge Base / Policy Library | `search_web`, `get_country_risk_alerts`, `list_open_orders_by_origin`, `get_order_shipment_status`, `search_knowledge_base_articles`, `create_risk_alert_rule` ✎ |
| Q6 | Diversify from southern China due to tariffs: lead time, cost, who takes volume | Costing & Margin Tool, Tax & Duty System, Freight Rate Management System, Network Design Tool, Supplier Onboarding & Risk System, Web | `get_volume_by_origin_region`, `get_tariff_scenario_rates`, `calculate_landed_cost_by_origin`, `get_transit_time_by_lane`, `run_network_scenario`, `search_factories_by_capability_and_country`, `get_supplier_qualification_time_and_cost`, `create_onboarding_case` ✎ |

## 34. Sourcing manager, Europe/nearshore

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Which top 50 basics could move to Portugal, Turkey, Morocco profitably; pilot three | Costing & Margin Tool, Demand Planning System, Data Warehouse / Lakehouse, Landed Cost Calculator, Supplier Relationship Management (SRM), Sourcing / RFx Platform | `list_top_products_by_sales_for_category`, `get_product_markdown_rate_history`, `get_forecast_error_by_lead_time`, `calculate_landed_cost_by_origin`, `search_factories_by_capability_and_country`, `calculate_markdown_breakeven`, `run_analysis`, `create_rfq` ✎ |
| Q2 | Find Portugal and Turkey makers of seam-sealed, OEKO-TEX outerwear at 30k units a season | Sourcing / RFx Platform, Supplier Onboarding & Risk System, Factory Audit Platform, Product Compliance & Regulatory Database, Web | `search_factories_by_capability_and_country`, `get_supplier_certifications`, `search_certification_registry`, `get_supplier_audit_status`, `search_customer_feedback_for_supplier`, `get_supplier_lead_time_and_moq`, `draft_supplier_shortlist_comparison`, `send_rfq_to_suppliers` ✎ |
| Q3 | Landed cost model for wool coat, Vietnam versus Portugal, with freight and lead-time sensitivities | Landed Cost Calculator, Tax & Duty System, FX & Hedging Platform, Freight Rate Management System, Demand Planning System, Costing & Margin Tool | `get_product_costing_for_style`, `get_freight_rate_for_lane`, `get_tariff_rates_for_category_origin`, `get_fx_forward_curve`, `get_inventory_holding_cost_rate`, `get_markdown_rate_by_lead_time`, `get_forecast_error_by_lead_time`, `calculate_landed_cost_by_origin`, `run_analysis` |
| Q4 | Morocco versus Turkey: incentives, labour, fabric availability, geopolitical and currency risk | Web, Knowledge Base / Policy Library, FX & Hedging Platform | `search_web`, `fetch_web_page`, `search_knowledge_base_articles`, `get_fx_rates_history`, `get_supplier_lead_time_performance` |
| Q5 | Why are nearshore quotes about 35% above expectation? | Sourcing / RFx Platform, Costing & Margin Tool, Documents | `get_rfq_responses_for_product`, `get_quote_cost_breakdown_by_component`, `get_target_cost_for_product`, `compare_quotes_by_cost_component`, `get_historic_quotes_by_origin`, `send_rfq_clarification_request` ✎ |
| Q6 | Nearshore pilot suppliers versus Asian on reaction time, quality, flexibility | Supplier Relationship Management (SRM), Quality Management System (QMS), Purchase Order System | `get_supplier_scorecard_comparison`, `get_supplier_reaction_time`, `get_supplier_quality_record`, `get_nearshore_pilot_orders`, `get_supplier_lead_time_performance` |
| Q7 | How much to commit to nearshore supplier for priority capacity; typical deal structures | Contract Management System, Demand Planning System, Knowledge Base / Policy Library, Web | `get_nearshore_spend_and_forecast_volume`, `get_demand_forecast_variability`, `calculate_commitment_risk_scenarios`, `search_web`, `search_knowledge_base_articles`, `get_standard_clause_library`, `create_contract_draft` ✎ |
| Q8 | Does nearshoring reduce exposure under the new EU due-diligence rules? | Supply Chain Due Diligence Platform, Product Compliance & Regulatory Database, Supplier Onboarding & Risk System, Web | `search_due_diligence_regulation_requirements`, `get_supplier_tier_mapping_by_country`, `get_supplier_due_diligence_status`, `list_required_supplier_documents`, `search_web` |

## 35. Supplier relationship manager

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Supplier S slipping on delivery and quality: underlying issue and our own late changes | Supplier Relationship Management (SRM), Quality Management System (QMS), Purchase Order System, Accounts Payable System, Web | `get_supplier_scorecard_history`, `get_supplier_quality_incidents`, `get_order_change_history_for_supplier`, `get_supplier_payment_performance`, `search_web`, `get_supplier_financial_health_score`, `run_analysis`, `draft_supplier_recovery_plan`, `create_supplier_improvement_plan` ✎, `update_supplier_status` ✎ |
| Q2 | Financial health of top 20 suppliers, red flags, and our exposure | Supplier Onboarding & Risk System, Spend Analytics Platform, Purchase Order System, Web | `list_top_suppliers_by_spend`, `get_supplier_financial_health_score`, `get_supplier_credit_rating`, `search_web`, `get_supplier_open_order_exposure`, `get_supplier_criticality_rating`, `update_supplier_risk_status` ✎ |
| Q3 | Too many suppliers: who to invest in, who to exit, criteria and savings | Spend Analytics Platform, Supplier Relationship Management (SRM), Supplier Onboarding & Risk System, Contract Management System | `get_supplier_spend_by_category`, `get_supplier_scorecard_history`, `get_supplier_criticality_rating`, `get_supplier_management_cost`, `calculate_supplier_segmentation_score`, `calculate_consolidation_savings`, `run_analysis`, `update_supplier_status` ✎ |
| Q4 | Impact of a six-week failure of our largest packaging supplier | Supply Planning System (MRP/DRP), Purchase Order System, Inventory Management System (IMS), Supplier Onboarding & Risk System | `get_supplier_supplied_items`, `get_inventory_cover_by_item`, `get_open_orders_for_supplier`, `calculate_supplier_disruption_impact`, `list_alternative_suppliers_for_category`, `get_supplier_qualification_time_and_cost` |
| Q5 | Q3 business review pack for Supplier T from scorecard and orders files | Documents, Supplier Relationship Management (SRM), Accounts Payable System, Purchase Order System, Supplier Portal, Email & Calendar | `read_document_attachment`, `get_supplier_scorecard_history`, `get_supplier_issues_log`, `get_forecast_accuracy_shared_with_supplier`, `get_supplier_payment_performance`, `run_analysis`, `draft_business_review_pack`, `send_business_review_pack_to_supplier` ✎, `create_calendar_event` ✎ |
| Q6 | Structure a joint improvement programme to cut a supplier's lead time 20% | Supplier Relationship Management (SRM), Knowledge Base / Policy Library, Web, Project & Portfolio Management Tool | `get_supplier_lead_time_breakdown`, `get_supplier_improvement_programme_history`, `search_knowledge_base_articles`, `search_web`, `draft_improvement_programme_plan`, `create_project_plan` ✎ |

## 36. Procurement analyst

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Preferred-supplier spend share fell from 82% to 74%: where is spend going? | Spend Analytics Platform, Contract Management System, Purchase Order System, Project & Portfolio Management Tool | `get_preferred_supplier_share_trend`, `list_spend_by_supplier_and_category`, `list_off_contract_purchase_orders`, `get_contract_coverage_by_category`, `calculate_price_variance_vs_contract`, `create_action_item` ✎ |
| Q2 | Largest savings from consolidation, renegotiation or spec change, with realistic ranges | Spend Analytics Platform, Contract Management System, Commodity & Market Data Feed, Sourcing / RFx Platform | `list_spend_by_supplier_and_category`, `get_supplier_fragmentation_by_category`, `get_price_benchmark_for_category`, `calculate_consolidation_savings`, `calculate_renegotiation_recovery`, `get_historic_savings_realisation_rates`, `run_analysis`, `create_savings_initiative` ✎ |
| Q3 | How much of last year's reported savings are actually in our prices? | Spend Analytics Platform, Purchase Order System, Accounts Payable System, ERP (General Ledger) | `list_reported_savings_initiatives`, `get_actual_price_paid_trend_by_item`, `calculate_realised_savings`, `compare_reported_vs_realised_savings`, `run_analysis`, `update_savings_tracker_entry` ✎ |
| Q4 | Are we paying above market in our top five categories? | Spend Analytics Platform, Commodity & Market Data Feed, Web | `list_top_categories_by_spend`, `get_price_benchmark_for_category`, `search_market_price_indices`, `compare_price_paid_to_benchmark` |
| Q5 | Find about 340 duplicate vendors by fuzzy match, combined spend, discount, fraud flags | Documents, Master Data Management (MDM), Spend Analytics Platform, Accounts Payable System, Supplier Onboarding & Risk System | `read_document_attachment`, `search_duplicate_vendor_candidates`, `get_vendor_bank_account_matches`, `get_vendor_spend_last_24_months`, `calculate_consolidation_savings`, `list_vendor_fraud_indicators`, `get_open_transactions_for_vendor`, `block_supplier_payments` ✎, `merge_vendor_records` ✎, `archive_duplicate_vendor` ✎ |
| Q6 | What supplier price increases to expect next year, who will push, how to prepare | Commodity & Market Data Feed, Spend Analytics Platform, Supplier Relationship Management (SRM), Web | `get_commodity_price_history`, `get_supplier_input_cost_mix`, `search_supplier_price_increase_notices`, `list_suppliers_by_price_increase_history`, `search_web`, `calculate_expected_price_increase_by_supplier` |

## 37. Indirect procurement manager

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Compare four warehouse cleaning bids with hidden costs, three-year total, recommendation | Documents, Sourcing / RFx Platform, Contract Management System, Supplier Onboarding & Risk System | `read_document_attachment`, `extract_bid_pricing_and_terms`, `compare_bids_by_criteria`, `calculate_three_year_total_cost`, `get_supplier_references`, `get_supplier_financial_health_score`, `draft_bid_recommendation`, `send_rfq_clarification_request` ✎ |
| Q2 | Typical cost of racking inspections and maintenance in the UK versus ours | Web, Spend Analytics Platform, Contract Management System | `search_web`, `search_market_price_benchmark_for_service`, `get_contract_price_for_service` |
| Q3 | Facilities spend 14% over budget: which suppliers, one-off versus recurring | ERP (General Ledger), Budgeting & Forecasting Tool, Accounts Payable System, Spend Analytics Platform, Project & Portfolio Management Tool | `get_budget_vs_actual_by_cost_centre`, `list_spend_by_supplier_and_category`, `get_accounts_payable_invoices_for_supplier`, `classify_spend_one_off_vs_recurring`, `create_action_item` ✎ |
| Q4 | Contracts expiring in next 12 months, tender needs, sourcing calendar | Contract Management System, Spend Analytics Platform, Email & Calendar | `list_contracts_expiring_within_period`, `get_contract_renewal_terms`, `get_contract_owner`, `list_spend_by_supplier_and_category`, `draft_sourcing_calendar`, `create_calendar_event` ✎, `create_contract_renewal_alert` ✎, `delete_calendar_event` ✎ |
| Q5 | Energy and packaging services cost next year, and should we fix prices? | Commodity & Market Data Feed, Contract Management System, Spend Analytics Platform, Web | `get_commodity_price_forecast`, `get_commodity_price_history`, `get_contract_terms_for_supplier`, `list_spend_by_supplier_and_category`, `search_web`, `calculate_fixed_vs_floating_cost_scenarios` |

## 38. Contracts/legal counsel, commercial

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Review supplier agreement against standard terms, rank deviations, exposure, redline email | Documents, Contract Management System, Knowledge Base / Policy Library, Web | `read_document_attachment`, `get_standard_terms_template`, `compare_contract_to_standard_terms`, `search_knowledge_base_articles`, `get_fallback_positions_playbook`, `calculate_liability_exposure`, `draft_redline_cover_email`, `send_redline_to_supplier` ✎ |
| Q2 | Current forced labour, due-diligence, product liability law in UK, EU, US and contract impact | Web, Supply Chain Due Diligence Platform, Knowledge Base / Policy Library, Contract Management System | `search_due_diligence_regulation_requirements`, `search_web`, `fetch_web_page`, `get_standard_clause_library`, `compare_clause_library_to_regulations`, `update_standard_clause` ✎ |
| Q3 | Is liability capped at order value reasonable for product safety; what counter | Contract Management System, Knowledge Base / Policy Library, Risk Management System, Web | `get_contract_liability_clause`, `search_knowledge_base_articles`, `search_web`, `get_insurance_requirements_policy`, `get_supplier_insurance_certificates`, `update_contract_negotiation_position` ✎ |
| Q4 | Top 30 contracts: price review, force majeure, termination clauses with notice periods | Contract Management System, Documents | `list_contracts_by_supplier_spend`, `search_contract_clauses`, `get_contract_notice_periods`, `calculate_contract_risk_ranking` |
| Q5 | IP exposure when suppliers co-develop products; weak contracts and mitigating terms | Contract Management System, Product Lifecycle Management (PLM), Knowledge Base / Policy Library, Supplier Relationship Management (SRM) | `list_co_development_projects`, `search_contract_clauses`, `get_standard_clause_library`, `get_supplier_spend_by_category` |
| Q6 | Supplier missed critical delivery: what remedies do we have? | Contract Management System, Purchase Order System, Supplier Relationship Management (SRM), Email & Calendar | `get_contract_remedies_clauses`, `get_purchase_order_delivery_status`, `get_order_delay_impact`, `get_supplier_scorecard_history`, `draft_breach_notice`, `create_contract_breach_record` ✎, `send_breach_notice` ✎ |
| Q7 | What contract renewals are coming up? | Contract Management System | `list_contracts_expiring_within_period`, `get_contract_notice_periods`, `list_contracts_with_non_standard_terms`, `create_contract_renewal_alert` ✎, `archive_contract_record` ✎ |
| Q8 | How courts treated force majeure over port closures and what it means for our clause | Web, Knowledge Base / Policy Library, Contract Management System | `search_case_law`, `search_web`, `get_standard_clause_library`, `search_knowledge_base_articles` |

## 39. Raw materials/commodities buyer

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Cotton, polyester, nylon, leather prices, drivers, 6 and 12 month outlook summary | Commodity & Market Data Feed, Web, Costing & Margin Tool, Documents | `get_commodity_price_history`, `get_commodity_price_forecast`, `search_commodity_news`, `get_material_cost_share_for_product`, `get_forecast_accuracy_history_for_commodity`, `draft_commodity_summary` |
| Q2 | Lock in 60% of next year's cotton (4,200 t) now or wait? | Commodity & Market Data Feed, Documents, Treasury Management System, FX & Hedging Platform, Purchase Order System, Demand Planning System | `get_commodity_price_forecast`, `get_commodity_seasonality`, `read_document_attachment`, `get_cash_position_forecast`, `get_open_commodity_commitments`, `get_historic_hedging_outcomes`, `get_hedging_instrument_quotes`, `get_demand_forecast_variability`, `calculate_hedge_scenarios`, `run_analysis`, `create_purchase_order` ✎, `submit_hedge_request` ✎ |
| Q3 | Fabric cost per metre up 9% with cotton up 4%: premiums, margins, freight, lag | Costing & Margin Tool, Commodity & Market Data Feed, Purchase Order System, Contract Management System, Freight Rate Management System, Email & Calendar | `get_fabric_cost_history_by_supplier`, `get_commodity_price_history`, `get_freight_rate_history`, `get_contract_terms_for_supplier`, `calculate_cost_variance_bridge`, `compare_supplier_pass_through_to_market`, `send_supplier_query_email` ✎ |
| Q4 | Effect of 20% polyester price rise on product cost and margin by category | Costing & Margin Tool, Commodity & Market Data Feed, Purchase Order System, Contract Management System | `list_products_by_material`, `get_material_cost_share_for_product`, `get_open_commodity_commitments`, `get_contract_terms_for_supplier`, `calculate_commodity_shock_impact_by_category` |
| Q5 | Cotton supply this season: weather, trade policy, harvest, origins our mills use | Web, Commodity & Market Data Feed, Supplier Portal, Spend Analytics Platform | `search_web`, `fetch_web_page`, `search_commodity_news`, `get_supplier_material_origin_mix`, `get_commodity_price_forecast` |
| Q6 | Recycled or alternative materials to replace virgin polyester: cost and supply outlook | Web, Product Lifecycle Management (PLM), Test Lab / LIMS, Commodity & Market Data Feed, Costing & Margin Tool | `search_web`, `search_alternative_material_suppliers`, `get_recycled_material_price_premium`, `get_material_supply_outlook`, `get_material_test_results` |
| Q7 | When should we buy leather for next autumn? | Commodity & Market Data Feed, Supply Planning System (MRP/DRP), Web | `get_commodity_price_history`, `get_commodity_seasonality`, `get_material_requirements_forecast`, `run_analysis`, `create_commodity_price_alert` ✎ |
| Q8 | Draft this week's commodity brief for buying team | Commodity & Market Data Feed, Web, Purchase Order System, Documents, Email & Calendar | `get_commodity_price_history`, `search_commodity_news`, `get_open_commodity_commitments`, `list_commodity_alert_thresholds`, `draft_commodity_brief`, `send_commodity_brief` ✎, `update_commodity_alert_threshold` ✎ |

## 40. Packaging buyer

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Corrugated versus moulded pulp versus recycled plastic: cost, damage, targets, capacity | Packaging Design System, Costing & Margin Tool, Quality Management System (QMS), Packaging Compliance & EPR System, Supplier Portal, Warehouse Management System (WMS), Sampling & Development Tracker | `get_packaging_spec_for_product`, `get_packaging_unit_cost_by_material`, `get_damage_rate_by_pack_type`, `calculate_pallet_fill_by_pack_spec`, `get_recycled_content_and_recyclability`, `get_packaging_targets_and_progress`, `search_packaging_suppliers_by_material`, `get_supplier_capacity_commitments`, `run_analysis`, `create_sample_request` ✎ |
| Q2 | EPR fees, recycled-content mandates, plastic taxes in UK, France, Germany, Spain | Packaging Compliance & EPR System, Packaging Design System, Web | `get_epr_fee_rates`, `search_packaging_regulations_by_country`, `get_packaging_weights_by_material_and_market`, `calculate_epr_cost_by_country`, `search_web` |
| Q3 | Glass breakage up 40%: claims, pack specs, supplier changes, carriers | Customer Service Platform, Packaging Design System, Carrier Portal, Test Lab / LIMS, Warehouse Management System (WMS) | `get_damage_claims_by_item`, `get_packaging_spec_change_history`, `get_carrier_damage_rates`, `get_warehouse_handling_damage_reports`, `get_drop_test_results`, `run_analysis`, `create_quality_investigation` ✎ |
| Q4 | Where are packaging prices going? Corrugated and film, extend or renegotiate | Commodity & Market Data Feed, Contract Management System, Purchase Order System, Web | `get_packaging_price_index_history`, `get_commodity_price_forecast`, `get_contract_terms_for_supplier`, `search_web`, `create_negotiation_case` ✎ |
| Q5 | Are we on track for packaging targets: gaps and fastest actions | Packaging Compliance & EPR System, Carbon & ESG Reporting Platform, Packaging Design System, Costing & Margin Tool, Project & Portfolio Management Tool | `get_packaging_targets_and_progress`, `get_recycled_content_and_recyclability`, `calculate_catch_up_options`, `get_packaging_unit_cost_by_material`, `create_action_item` ✎ |
| Q6 | What are the best retailers doing on e-commerce packaging? | Web, Customer Reviews & Feedback Platform, Packaging Design System | `search_web`, `fetch_web_page`, `get_current_ecommerce_pack_specs`, `search_customer_review_themes`, `get_damage_rate_by_pack_type` |

## 41. Supplier onboarding specialist

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Due diligence on Sunrise Pack Co. Ltd: ownership, sanctions, litigation, media, risk rating | Documents, Supply Chain Due Diligence Platform, Supplier Onboarding & Risk System, Product Compliance & Regulatory Database, Web | `read_document_attachment`, `search_company_registry`, `get_company_ownership_structure`, `run_sanctions_screening`, `search_litigation_records`, `search_adverse_media`, `get_supplier_certifications`, `get_supplier_financial_health_score`, `calculate_supplier_risk_rating`, `create_onboarding_case` ✎ |
| Q2 | Registrations and certifications a Korean cosmetics exporter needs for EU and UK | Web, Product Compliance & Regulatory Database, Knowledge Base / Policy Library | `search_cosmetics_regulatory_requirements`, `list_required_registrations_by_market`, `search_public_registries`, `fetch_web_page` |
| Q3 | Supplier bank account in a different country from registered address: risk indicator? | Supplier Onboarding & Risk System, Accounts Payable System, Web | `get_supplier_bank_details`, `get_supplier_registration_details`, `run_bank_account_verification`, `search_company_registry`, `get_company_ownership_structure`, `block_supplier_payments` ✎ |
| Q4 | Which onboarding cases are stuck, what is missing, draft reminder emails | Supplier Onboarding & Risk System, Purchase Order System, Email & Calendar | `list_onboarding_cases_by_status`, `get_onboarding_missing_items`, `list_purchase_orders_blocked_by_onboarding`, `draft_supplier_reminder_email`, `send_supplier_reminder_email` ✎ |
| Q5 | Is this supplier OK to onboard from attached file; conditions or audit needed? | Documents, Supplier Onboarding & Risk System, Knowledge Base / Policy Library, Factory Audit Platform | `read_document_attachment`, `get_onboarding_minimum_requirements`, `compare_onboarding_file_to_requirements`, `run_sanctions_screening`, `get_supplier_bank_details`, `list_audit_requirements_by_risk_tier`, `calculate_supplier_risk_rating`, `update_onboarding_case_conditions` ✎, `create_audit_request` ✎, `update_onboarding_case_status` ✎ |
| Q6 | Which supplier fraud schemes should onboarding catch? | Knowledge Base / Policy Library, Web, Supplier Onboarding & Risk System, Internal Audit System | `search_web`, `search_knowledge_base_articles`, `list_onboarding_controls`, `list_vendor_fraud_indicators`, `search_internal_fraud_cases`, `create_onboarding_control` ✎ |

## Tool catalogue for this category

| Tool | System | R/W | One-line description |
|---|---|---|---|
| `archive_contract_record` | Contract Management System | W | Archives an expired or unused contract record |
| `archive_duplicate_vendor` | Master Data Management (MDM) | W | Archives a duplicate vendor record after merge |
| `block_supplier_payments` | Accounts Payable System | W | Places a payment hold on a vendor |
| `calculate_catch_up_options` | Packaging Compliance & EPR System | R | Options and cost to close packaging target gaps |
| `calculate_commitment_risk_scenarios` | Contract Management System | R | Downside cost of volume commitments under demand scenarios |
| `calculate_commodity_cost_exposure` | Costing & Margin Tool | R | Product cost exposed to a commodity price move |
| `calculate_commodity_shock_impact_by_category` | Costing & Margin Tool | R | Cost and margin impact of a price shock by category |
| `calculate_consolidation_savings` | Spend Analytics Platform | R | Estimate savings from consolidating suppliers or vendors |
| `calculate_contract_risk_ranking` | Contract Management System | R | Rank contracts by clause-based risk score |
| `calculate_cost_variance_bridge` | Costing & Margin Tool | R | Bridge a cost change into market, premium, freight and lag |
| `calculate_epr_cost_by_country` | Packaging Compliance & EPR System | R | EPR and packaging tax cost by country for current packs |
| `calculate_expected_price_increase_by_supplier` | Spend Analytics Platform | R | Expected price rise by supplier from input costs |
| `calculate_expedite_cost_options` | Purchase Order System | R | Cost of air, split or expedite options for late orders |
| `calculate_fixed_vs_floating_cost_scenarios` | Commodity & Market Data Feed | R | Compare fixed versus floating price outcomes |
| `calculate_hedge_scenarios` | Treasury Management System | R | Cost and outcome of forward, option and wait strategies |
| `calculate_landed_cost_by_origin` | Landed Cost Calculator | R | Landed cost for a style by sourcing origin |
| `calculate_landed_cost_by_supplier` | Landed Cost Calculator | R | Landed cost per unit by supplier |
| `calculate_liability_exposure` | Contract Management System | R | Estimate liability under a limitation clause |
| `calculate_margin_bridge` | Costing & Margin Tool | R | Decompose margin change into cost, FX, mix and supplier |
| `calculate_margin_scenario` | Budgeting & Forecasting Tool | R | Margin under inflation, FX and tariff scenarios |
| `calculate_markdown_breakeven` | Costing & Margin Tool | R | Markdown reduction needed to offset a cost premium |
| `calculate_pallet_fill_by_pack_spec` | Warehouse Management System (WMS) | R | Units per pallet for a pack specification |
| `calculate_price_variance_vs_contract` | Spend Analytics Platform | R | Price paid versus contract price |
| `calculate_realised_savings` | Spend Analytics Platform | R | Savings visible in actual prices paid |
| `calculate_renegotiation_recovery` | Spend Analytics Platform | R | Recoverable value from renegotiation |
| `calculate_should_cost` | Cost Modelling Tool | R | Bottom-up should-cost at a given volume |
| `calculate_supplier_disruption_impact` | Supply Planning System (MRP/DRP) | R | Stock-out and sales impact of a supplier outage |
| `calculate_supplier_risk_rating` | Supplier Onboarding & Risk System | R | Composite risk rating with reasons |
| `calculate_supplier_segmentation_score` | Supplier Relationship Management (SRM) | R | Score suppliers for invest, maintain or exit |
| `calculate_target_cost` | Costing & Margin Tool | R | Target cost implied by price and margin goal |
| `calculate_three_year_total_cost` | Sourcing / RFx Platform | R | Total contract cost including hidden charges |
| `calculate_wage_impact_on_fob` | Costing & Margin Tool | R | FOB impact of wage changes by country |
| `cancel_purchase_order` | Purchase Order System | W | Cancels an open purchase order and releases the commitment |
| `classify_spend_one_off_vs_recurring` | Spend Analytics Platform | R | Tag spend as one-off or recurring |
| `compare_bids_by_criteria` | Sourcing / RFx Platform | R | Score bids against price and service criteria |
| `compare_capacity_utilisation_year_on_year` | Supplier Portal | R | Capacity utilisation versus prior year |
| `compare_clause_library_to_regulations` | Knowledge Base / Policy Library | R | Gap analysis of clauses against regulations |
| `compare_contract_to_standard_terms` | Contract Management System | R | Deviation list of a contract versus standard terms |
| `compare_onboarding_file_to_requirements` | Supplier Onboarding & Risk System | R | Check an onboarding file against minimum requirements |
| `compare_price_paid_to_benchmark` | Spend Analytics Platform | R | Price paid versus market benchmark |
| `compare_quotes_by_cost_component` | Cost Modelling Tool | R | Line-by-line comparison of quotes by cost component |
| `compare_reported_vs_realised_savings` | Spend Analytics Platform | R | Reported versus realised savings by initiative |
| `compare_supplier_pass_through_to_market` | Costing & Margin Tool | R | Supplier price moves versus market index moves |
| `create_action_item` | Project & Portfolio Management Tool | W | Creates an action assigned to a named owner with a due date |
| `create_audit_request` | Factory Audit Platform | W | Requests an audit of a supplier or factory |
| `create_calendar_event` | Email & Calendar | W | Creates a calendar event and invites attendees |
| `create_commodity_price_alert` | Commodity & Market Data Feed | W | Creates a price alert at a chosen level for a commodity |
| `create_contract_breach_record` | Contract Management System | W | Logs a breach or delay event against a contract |
| `create_contract_draft` | Contract Management System | W | Creates a draft agreement record from a template and chosen clauses |
| `create_contract_renewal_alert` | Contract Management System | W | Sets an alert ahead of a contract notice or renewal date |
| `create_negotiation_case` | Contract Management System | W | Opens a renegotiation case against a contract |
| `create_onboarding_case` | Supplier Onboarding & Risk System | W | Opens a new supplier onboarding or qualification case |
| `create_onboarding_control` | Supplier Onboarding & Risk System | W | Adds a control to the onboarding checklist |
| `create_project_plan` | Project & Portfolio Management Tool | W | Creates a project with milestones and owners |
| `create_purchase_order` | Purchase Order System | W | Creates a purchase order in draft or submitted state |
| `create_quality_investigation` | Quality Management System (QMS) | W | Opens a quality investigation on items or a supplier |
| `create_rfq` | Sourcing / RFx Platform | W | Creates a draft RFQ for chosen suppliers and a product |
| `create_risk_alert_rule` | Risk Management System | W | Creates a monitoring alert on a country or supplier risk trigger |
| `create_sample_request` | Sampling & Development Tracker | W | Raises a sample request to a supplier for a pack or product |
| `create_savings_initiative` | Spend Analytics Platform | W | Adds an initiative to the savings tracker |
| `create_sourcing_award` | Sourcing / RFx Platform | W | Records a supplier award and volume split for a category |
| `create_supplier_improvement_plan` | Supplier Relationship Management (SRM) | W | Opens a formal improvement plan with targets and dates for a supplier |
| `create_supplier_issue_record` | Supplier Relationship Management (SRM) | W | Logs an issue and owner against a supplier |
| `delete_calendar_event` | Email & Calendar | W | Removes a calendar event |
| `draft_bid_recommendation` | Documents | R | Draft bid recommendation for a steering group |
| `draft_breach_notice` | Documents | R | Draft formal notice of breach or delay |
| `draft_business_review_pack` | Documents | R | Draft supplier business review pack |
| `draft_commodity_brief` | Documents | R | Draft weekly commodity brief |
| `draft_commodity_summary` | Documents | R | Draft commodity summary for category buyers |
| `draft_improvement_programme_plan` | Documents | R | Draft joint improvement programme plan |
| `draft_negotiation_brief` | Documents | R | Draft two-page negotiation brief |
| `draft_redline_cover_email` | Email & Calendar | R | Draft redline cover email, not sent |
| `draft_sourcing_calendar` | Documents | R | Draft sourcing calendar from contract expiries |
| `draft_sourcing_recommendation` | Documents | R | Draft supplier award recommendation |
| `draft_supplier_recovery_plan` | Documents | R | Draft supplier recovery plan |
| `draft_supplier_reminder_email` | Email & Calendar | R | Draft chase email to supplier, not sent |
| `draft_supplier_shortlist_comparison` | Documents | R | Draft shortlist comparison table |
| `extract_bid_pricing_and_terms` | Documents | R | Extract prices and terms from bid files |
| `extract_quote_line_items` | Documents | R | Extract line items from supplier quotes |
| `fetch_web_page` | Web (public search/fetch) | R | Fetch and read a public web page |
| `get_accounts_payable_invoices_for_supplier` | Accounts Payable System | R | Invoices for a supplier over a period |
| `get_actual_price_paid_trend_by_item` | Purchase Order System | R | Actual unit price paid over time |
| `get_budget_vs_actual_by_cost_centre` | Budgeting & Forecasting Tool | R | Budget versus actual by cost centre |
| `get_buying_margin_by_category_period` | Costing & Margin Tool | R | Buying margin by category and period |
| `get_carrier_damage_rates` | Carrier Portal | R | Damage rate by carrier and lane |
| `get_cash_position_forecast` | Treasury Management System | R | Forecast cash position and headroom |
| `get_category_margin_plan` | Budgeting & Forecasting Tool | R | Planned margin by category |
| `get_commodity_price_forecast` | Commodity & Market Data Feed | R | Analyst price forecast for a commodity |
| `get_commodity_price_history` | Commodity & Market Data Feed | R | Historical commodity prices |
| `get_commodity_seasonality` | Commodity & Market Data Feed | R | Seasonal price pattern by month |
| `get_company_ownership_structure` | Supply Chain Due Diligence Platform | R | Ultimate beneficial ownership structure |
| `get_competitor_price_history` | Competitor Price Monitoring Tool | R | Competitor price history for a product |
| `get_contract_coverage_by_category` | Contract Management System | R | Share of category spend under contract |
| `get_contract_liability_clause` | Contract Management System | R | Liability and cap clauses of a contract |
| `get_contract_notice_periods` | Contract Management System | R | Notice periods by contract |
| `get_contract_owner` | Contract Management System | R | Business owner of a contract |
| `get_contract_price_for_service` | Contract Management System | R | Contracted price for a service |
| `get_contract_remedies_clauses` | Contract Management System | R | Remedies, delay and termination clauses |
| `get_contract_renewal_terms` | Contract Management System | R | Renewal and auto-renewal terms |
| `get_contract_terms_for_supplier` | Contract Management System | R | Price, term and review clauses for a supplier |
| `get_country_risk_alerts` | Risk Management System | R | Active risk alerts by sourcing country |
| `get_current_ecommerce_pack_specs` | Packaging Design System | R | Current e-commerce pack specifications |
| `get_damage_claims_by_item` | Customer Service Platform | R | Damage claims by item and period |
| `get_damage_rate_by_pack_type` | Quality Management System (QMS) | R | Damage rate by pack type |
| `get_demand_forecast_variability` | Demand Planning System | R | Forecast error and demand variability |
| `get_drop_test_results` | Test Lab / LIMS | R | Drop-test results for pack specs |
| `get_epr_fee_rates` | Packaging Compliance & EPR System | R | EPR fee rates by material and country |
| `get_fabric_cost_history_by_supplier` | Costing & Margin Tool | R | Fabric cost per metre by supplier over time |
| `get_factory_audit_findings` | Factory Audit Platform | R | Audit findings for a factory |
| `get_factory_capacity_utilisation` | Supplier Portal | R | Factory capacity utilisation by month |
| `get_factory_material_inbound_status` | Supplier Portal | R | Material inbound status at a factory |
| `get_factory_moq_terms` | Supplier Portal | R | Factory MOQ and commitment terms |
| `get_factory_production_reports` | Supplier Portal | R | Factory production reports |
| `get_fallback_positions_playbook` | Knowledge Base / Policy Library | R | Approved fallback positions by clause |
| `get_fob_price_history_by_country` | Costing & Margin Tool | R | FOB price history by origin country |
| `get_forecast_accuracy_history_for_commodity` | Commodity & Market Data Feed | R | Past accuracy of commodity forecasts |
| `get_forecast_accuracy_shared_with_supplier` | Supplier Portal | R | Accuracy of forecasts shared with a supplier |
| `get_forecast_error_by_lead_time` | Demand Planning System | R | Forecast error by lead time |
| `get_freight_rate_for_lane` | Freight Rate Management System | R | Current freight rate for a lane |
| `get_freight_rate_history` | Freight Rate Management System | R | Historical freight rates |
| `get_fx_forward_curve` | FX & Hedging Platform | R | Forward FX rates |
| `get_fx_hedge_cover_by_currency` | FX & Hedging Platform | R | Hedge cover by currency |
| `get_fx_rates_history` | FX & Hedging Platform | R | Historical FX rates |
| `get_hedging_instrument_quotes` | FX & Hedging Platform | R | Quotes for forwards and options |
| `get_historic_hedging_outcomes` | Treasury Management System | R | Outcomes of past hedging decisions |
| `get_historic_quotes_by_origin` | Sourcing / RFx Platform | R | Past quotes by origin |
| `get_historic_savings_realisation_rates` | Spend Analytics Platform | R | Past realisation rate by lever |
| `get_historical_unit_price_for_product` | Purchase Order System | R | Historical unit prices for a product |
| `get_insurance_requirements_policy` | Knowledge Base / Policy Library | R | Insurance requirements for suppliers |
| `get_inventory_cover_by_item` | Inventory Management System (IMS) | R | Weeks of cover by item |
| `get_inventory_holding_cost_rate` | Costing & Margin Tool | R | Inventory holding cost rate |
| `get_markdown_rate_by_lead_time` | Data Warehouse / Lakehouse | R | Markdown rate by lead-time band |
| `get_material_cost_share_for_product` | Costing & Margin Tool | R | Material share of product cost |
| `get_material_requirements_forecast` | Supply Planning System (MRP/DRP) | R | Forecast material requirements by month |
| `get_material_supply_outlook` | Commodity & Market Data Feed | R | Supply outlook for a material |
| `get_material_test_results` | Test Lab / LIMS | R | Test results for a material |
| `get_nearshore_pilot_orders` | Purchase Order System | R | Orders placed with nearshore pilot suppliers |
| `get_nearshore_spend_and_forecast_volume` | Spend Analytics Platform | R | Nearshore spend and planned volume |
| `get_ocean_freight_rates_for_lane` | Freight Rate Management System | R | Ocean freight rates by lane |
| `get_onboarding_minimum_requirements` | Knowledge Base / Policy Library | R | Minimum onboarding requirements by risk tier |
| `get_onboarding_missing_items` | Supplier Onboarding & Risk System | R | Missing items for an onboarding case |
| `get_open_commodity_commitments` | Purchase Order System | R | Open commodity purchase commitments |
| `get_open_orders_for_supplier` | Purchase Order System | R | Open orders for a supplier |
| `get_open_transactions_for_vendor` | Accounts Payable System | R | Open invoices and POs for a vendor |
| `get_order_change_history_for_supplier` | Purchase Order System | R | Order amendments by date and reason |
| `get_order_delay_history_for_factory` | Purchase Order System | R | Delivery delays by factory |
| `get_order_delay_impact` | Purchase Order System | R | Sales and stock impact of a late order |
| `get_order_readiness_status` | Supplier Portal | R | Production readiness of an order |
| `get_order_shipment_status` | Track & Trace Platform | R | Shipment status of an order |
| `get_packaging_price_index_history` | Commodity & Market Data Feed | R | Packaging price index history |
| `get_packaging_spec_change_history` | Packaging Design System | R | Pack spec change log |
| `get_packaging_spec_for_product` | Packaging Design System | R | Pack specification for a product |
| `get_packaging_targets_and_progress` | Packaging Compliance & EPR System | R | Packaging targets and progress |
| `get_packaging_unit_cost_by_material` | Costing & Margin Tool | R | Packaging unit cost by material |
| `get_packaging_weights_by_material_and_market` | Packaging Design System | R | Packaging weight by material and market |
| `get_payment_terms_benchmark` | Spend Analytics Platform | R | Payment terms benchmark |
| `get_preferred_supplier_share_trend` | Spend Analytics Platform | R | Preferred-supplier spend share over time |
| `get_price_benchmark_for_category` | Commodity & Market Data Feed | R | Market price benchmark for a category |
| `get_product_bom_and_cost_breakdown` | Product Lifecycle Management (PLM) | R | BOM and cost breakdown |
| `get_product_costing_for_style` | Costing & Margin Tool | R | Costing sheet for a style |
| `get_product_markdown_rate_history` | Data Warehouse / Lakehouse | R | Markdown rate history by product |
| `get_purchase_order_delivery_status` | Purchase Order System | R | Delivery status of a purchase order |
| `get_purchase_price_variance_by_item` | Purchase Order System | R | Purchase price variance by item |
| `get_quote_cost_breakdown_by_component` | Sourcing / RFx Platform | R | Quote cost breakdown by component |
| `get_recycled_content_and_recyclability` | Packaging Compliance & EPR System | R | Recycled content and recyclability by pack |
| `get_recycled_material_price_premium` | Commodity & Market Data Feed | R | Price premium of recycled materials |
| `get_rfq_responses_for_product` | Sourcing / RFx Platform | R | RFQ responses for a product |
| `get_sales_mix_by_item` | Data Warehouse / Lakehouse | R | Sales mix by item |
| `get_standard_clause_library` | Knowledge Base / Policy Library | R | Standard clause wording |
| `get_standard_terms_template` | Contract Management System | R | Standard terms template |
| `get_supplier_audit_status` | Factory Audit Platform | R | Audit status and score for a supplier |
| `get_supplier_bank_details` | Supplier Onboarding & Risk System | R | Supplier bank details |
| `get_supplier_capacity_commitments` | Supplier Portal | R | Supplier capacity and commitments |
| `get_supplier_certifications` | Supplier Onboarding & Risk System | R | Supplier certifications and expiries |
| `get_supplier_credit_rating` | Supplier Onboarding & Risk System | R | Credit rating for a supplier |
| `get_supplier_criticality_rating` | Supplier Onboarding & Risk System | R | Criticality rating for a supplier |
| `get_supplier_due_diligence_status` | Supply Chain Due Diligence Platform | R | Due-diligence status for a supplier |
| `get_supplier_financial_health_score` | Supplier Onboarding & Risk System | R | Financial health score |
| `get_supplier_fragmentation_by_category` | Spend Analytics Platform | R | Supplier count and tail spend by category |
| `get_supplier_improvement_programme_history` | Supplier Relationship Management (SRM) | R | Past improvement programmes and results |
| `get_supplier_input_cost_mix` | Spend Analytics Platform | R | Supplier input cost mix |
| `get_supplier_insurance_certificates` | Supplier Onboarding & Risk System | R | Supplier insurance certificates |
| `get_supplier_issues_log` | Supplier Relationship Management (SRM) | R | Issues log for a supplier |
| `get_supplier_lead_time_and_moq` | Supplier Portal | R | Lead time and MOQ for a supplier |
| `get_supplier_lead_time_breakdown` | Supplier Relationship Management (SRM) | R | Lead time by process stage |
| `get_supplier_lead_time_performance` | Supplier Relationship Management (SRM) | R | Lead time versus agreed |
| `get_supplier_management_cost` | Supplier Relationship Management (SRM) | R | Cost to manage a supplier |
| `get_supplier_material_origin_mix` | Supplier Portal | R | Origin mix of supplier materials |
| `get_supplier_on_time_delivery_trend` | Supplier Relationship Management (SRM) | R | On-time delivery trend |
| `get_supplier_open_order_exposure` | Purchase Order System | R | Open order value with a supplier |
| `get_supplier_payment_performance` | Accounts Payable System | R | Our payment timeliness to a supplier |
| `get_supplier_qualification_time_and_cost` | Supplier Onboarding & Risk System | R | Time and cost to qualify a supplier |
| `get_supplier_quality_incidents` | Quality Management System (QMS) | R | Quality incidents for a supplier |
| `get_supplier_quality_record` | Quality Management System (QMS) | R | Defect and inspection record |
| `get_supplier_reaction_time` | Supplier Relationship Management (SRM) | R | Supplier reaction time to changes |
| `get_supplier_references` | Sourcing / RFx Platform | R | Supplier references from bids |
| `get_supplier_registration_details` | Supplier Onboarding & Risk System | R | Registration details of a supplier |
| `get_supplier_scorecard_comparison` | Supplier Relationship Management (SRM) | R | Scorecards side by side |
| `get_supplier_scorecard_history` | Supplier Relationship Management (SRM) | R | Scorecard history for a supplier |
| `get_supplier_share_of_category_spend` | Spend Analytics Platform | R | Supplier share of category spend |
| `get_supplier_share_of_wallet` | Spend Analytics Platform | R | Our share of a supplier's volume |
| `get_supplier_spend_by_category` | Spend Analytics Platform | R | Supplier spend by category |
| `get_supplier_spend_by_currency` | Spend Analytics Platform | R | Supplier spend by currency |
| `get_supplier_supplied_items` | Purchase Order System | R | Items supplied by a supplier |
| `get_supplier_tier_mapping_by_country` | Supply Chain Due Diligence Platform | R | Tier-n supplier map by country |
| `get_target_cost_for_product` | Costing & Margin Tool | R | Target cost for a product |
| `get_target_margin_for_category` | Costing & Margin Tool | R | Target margin for a category |
| `get_tariff_rates_for_category_origin` | Tax & Duty System | R | Duty rates by category and origin |
| `get_tariff_scenario_rates` | Tax & Duty System | R | Scenario tariff rates |
| `get_transit_time_by_lane` | Freight Rate Management System | R | Transit time by lane |
| `get_vendor_bank_account_matches` | Master Data Management (MDM) | R | Vendors sharing bank accounts |
| `get_vendor_spend_last_24_months` | Spend Analytics Platform | R | Vendor spend over 24 months |
| `get_volume_by_origin_region` | Purchase Order System | R | Purchase volume by origin region |
| `get_warehouse_handling_damage_reports` | Warehouse Management System (WMS) | R | Handling damage reports |
| `list_alternative_factories_for_product` | Supplier Onboarding & Risk System | R | Approved alternative factories |
| `list_alternative_suppliers_for_category` | Supplier Onboarding & Risk System | R | Approved alternative suppliers |
| `list_audit_requirements_by_risk_tier` | Knowledge Base / Policy Library | R | Audit requirements by risk tier |
| `list_co_development_projects` | Product Lifecycle Management (PLM) | R | Co-development projects with suppliers |
| `list_commodity_alert_thresholds` | Commodity & Market Data Feed | R | Configured price alert thresholds |
| `list_contracts_by_supplier_spend` | Contract Management System | R | Contracts ranked by supplier spend |
| `list_contracts_expiring_within_period` | Contract Management System | R | Contracts expiring in a period |
| `list_contracts_with_non_standard_terms` | Contract Management System | R | Contracts flagged for non-standard terms |
| `list_off_contract_purchase_orders` | Purchase Order System | R | POs placed off contract |
| `list_onboarding_cases_by_status` | Supplier Onboarding & Risk System | R | Onboarding cases by status |
| `list_onboarding_controls` | Supplier Onboarding & Risk System | R | Controls in the onboarding process |
| `list_open_orders_at_factory` | Purchase Order System | R | Open orders at a factory |
| `list_open_orders_by_origin` | Purchase Order System | R | Open orders by origin country |
| `list_products_by_material` | Product Lifecycle Management (PLM) | R | Products using a material |
| `list_purchase_orders_blocked_by_onboarding` | Purchase Order System | R | POs blocked by onboarding |
| `list_reported_savings_initiatives` | Spend Analytics Platform | R | Reported savings initiatives |
| `list_required_registrations_by_market` | Product Compliance & Regulatory Database | R | Registrations required by market |
| `list_required_supplier_documents` | Supply Chain Due Diligence Platform | R | Documents required from suppliers |
| `list_spend_by_supplier_and_category` | Spend Analytics Platform | R | Spend by supplier and category |
| `list_suppliers_by_price_increase_history` | Spend Analytics Platform | R | Suppliers ranked by past increases |
| `list_suppliers_for_category` | Supplier Relationship Management (SRM) | R | Suppliers in a category |
| `list_suppliers_with_risk_alerts` | Supplier Onboarding & Risk System | R | Suppliers with active risk alerts |
| `list_top_categories_by_spend` | Spend Analytics Platform | R | Top categories by spend |
| `list_top_products_by_sales_for_category` | Data Warehouse / Lakehouse | R | Top products by sales |
| `list_top_suppliers_by_spend` | Spend Analytics Platform | R | Top suppliers by spend |
| `list_vendor_fraud_indicators` | Accounts Payable System | R | Fraud indicators on vendors |
| `merge_vendor_records` | Master Data Management (MDM) | W | Merges duplicate vendor records into a surviving master record |
| `read_document_attachment` | Documents | R | Read an attached file |
| `run_analysis` | Code Execution | R | Run analysis or charts in a sandbox |
| `run_bank_account_verification` | Supplier Onboarding & Risk System | R | Verify bank account against company |
| `run_network_scenario` | Network Design Tool | R | Run a sourcing network scenario |
| `run_sanctions_screening` | Supply Chain Due Diligence Platform | R | Screen entities against sanctions lists |
| `search_adverse_media` | Supply Chain Due Diligence Platform | R | Search adverse media on an entity |
| `search_alternative_material_suppliers` | Sourcing / RFx Platform | R | Find suppliers of alternative materials |
| `search_case_law` | Web (public search/fetch) | R | Search court decisions |
| `search_certification_registry` | Product Compliance & Regulatory Database | R | Verify certificates in public registries |
| `search_commodity_news` | Commodity & Market Data Feed | R | Commodity news and drivers |
| `search_company_registry` | Supply Chain Due Diligence Platform | R | Search company registries |
| `search_competitor_prices_for_product` | Competitor Price Monitoring Tool | R | Competitor prices for a comparable product |
| `search_contract_clauses` | Contract Management System | R | Search clauses across contracts |
| `search_cosmetics_regulatory_requirements` | Product Compliance & Regulatory Database | R | Cosmetics regulatory requirements |
| `search_customer_feedback_for_supplier` | Customer Reviews & Feedback Platform | R | Customer feedback tied to a supplier |
| `search_customer_review_themes` | Customer Reviews & Feedback Platform | R | Review themes by product |
| `search_due_diligence_regulation_requirements` | Supply Chain Due Diligence Platform | R | Due-diligence regulation requirements |
| `search_duplicate_vendor_candidates` | Master Data Management (MDM) | R | Fuzzy-match duplicate vendors |
| `search_factories_by_capability_and_country` | Sourcing / RFx Platform | R | Find factories by capability and country |
| `search_internal_fraud_cases` | Internal Audit System | R | Past internal fraud cases |
| `search_knowledge_base_articles` | Knowledge Base / Policy Library | R | Search policies and articles |
| `search_labour_dispute_news` | Web (public search/fetch) | R | Labour disputes and wage news |
| `search_litigation_records` | Supply Chain Due Diligence Platform | R | Litigation records for an entity |
| `search_market_price_benchmark_for_service` | Web (public search/fetch) | R | Public price benchmarks for services |
| `search_market_price_indices` | Commodity & Market Data Feed | R | Applicable market price indices |
| `search_packaging_regulations_by_country` | Packaging Compliance & EPR System | R | Packaging rules by country |
| `search_packaging_suppliers_by_material` | Sourcing / RFx Platform | R | Packaging suppliers by material |
| `search_public_registries` | Web (public search/fetch) | R | Search public regulatory registers |
| `search_supplier_price_increase_notices` | Supplier Portal | R | Price increase notices received |
| `search_web` | Web (public search/fetch) | R | General web search |
| `send_breach_notice` | Email & Calendar | W | Sends a formal breach or delay notice to the supplier |
| `send_business_review_pack_to_supplier` | Email & Calendar | W | Emails a business review pack to the supplier account contact |
| `send_commodity_brief` | Email & Calendar | W | Emails the commodity brief to the buying team |
| `send_redline_to_supplier` | Email & Calendar | W | Sends the redline and cover email to the supplier's legal contact |
| `send_rfq_clarification_request` | Sourcing / RFx Platform | W | Sends a clarification or re-quote request to bidders on an RFQ |
| `send_rfq_to_suppliers` | Sourcing / RFx Platform | W | Issues an RFQ to the selected suppliers |
| `send_supplier_query_email` | Email & Calendar | W | Sends a question list or query to a supplier contact from the user's mailbox |
| `send_supplier_reminder_email` | Email & Calendar | W | Sends a chase email to a supplier |
| `submit_hedge_request` | Treasury Management System | W | Submits a forward or hedge request for treasury approval |
| `update_category_margin_plan` | Budgeting & Forecasting Tool | W | Changes the planned margin for a category to a chosen scenario |
| `update_commodity_alert_threshold` | Commodity & Market Data Feed | W | Changes the threshold on an existing commodity alert |
| `update_contract_negotiation_position` | Contract Management System | W | Records the current negotiation position on a contract |
| `update_onboarding_case_conditions` | Supplier Onboarding & Risk System | W | Sets conditions on an onboarding case |
| `update_onboarding_case_status` | Supplier Onboarding & Risk System | W | Changes the status of an onboarding case (approved, conditional, rejected) |
| `update_purchase_order_ship_date` | Purchase Order System | W | Changes the requested ship or delivery date on a PO |
| `update_savings_tracker_entry` | Spend Analytics Platform | W | Corrects the reported value or status of a tracked saving |
| `update_standard_clause` | Knowledge Base / Policy Library | W | Changes the wording of a clause in the standard clause library |
| `update_supplier_risk_status` | Supplier Onboarding & Risk System | W | Sets a supplier's watch or risk status |
| `update_supplier_status` | Supplier Relationship Management (SRM) | W | Changes a supplier's relationship status (watch, planned exit, active) |
