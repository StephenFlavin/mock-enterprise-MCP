# Systems and MCP tools · 06 Product Development and Design

For each question in the 06 Product Development and Design questions file, this lists the enterprise systems an AI agent must reach and the MCP tool methods it would likely call, in order.
Tool names are shared across all nine category files so they can be reused as a benchmark. Follow-up questions are covered by the main row unless they need an extra system.
Questions are abridged; see the questions file for full wording and follow-ups.

**Legend:** Q = question number within persona · Systems = canonical system names · Tools = MCP tool methods in likely call order · `draft_` tools produce a document and are not writes · ✎ marks a write or side-effect tool that changes a system or sends something (create, update, delete, archive, submit, send, reject); writes named in follow-ups are listed in the question's row.

## 51. New product developer

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Which spring launch products risk missing in-store date, and why? | Sampling & Development Tracker, PLM, Purchase Order System, Supplier Portal, Email & Calendar | `list_launch_products_by_season`, `get_critical_path_milestones_for_product`, `get_sample_approval_status_for_product`, `get_open_purchase_orders_for_product`, `get_supplier_milestone_updates`, `calculate_date_recovery_cost`, `draft_launch_meeting_update`, `send_supplier_milestone_chase` ✎ |
| Q2 | Compare three shortlisted factories for insulated lunch box on tooling, capability, lead time, compliance; risks of cheapest | Sourcing / RFx Platform, Documents, Factory Audit Platform, Supplier Onboarding & Risk System, Costing & Margin Tool, Quality Management System (QMS), Purchase Order System | `get_document_contents`, `get_rfq_responses_for_product`, `compare_factory_quotes`, `search_factory_audit_results`, `get_supplier_compliance_history`, `calculate_tooling_amortisation_per_unit`, `list_preproduction_sample_acceptance_criteria`, `create_purchase_order` ✎, `submit_purchase_order_for_approval` ✎, `delete_draft_purchase_order` ✎ |
| Q3 | Find competitor insulated lunch boxes: price, features, complaints, differentiation gaps, shareable comparison | Web, Competitor Price Monitoring Tool, Customer Reviews & Feedback Platform, Trend & Market Intelligence Platform, Email & Calendar | `search_web`, `search_competitor_products_by_category`, `get_competitor_price_history`, `search_customer_reviews_for_competitor_products`, `get_review_theme_summary`, `draft_competitor_comparison_table`, `send_competitor_comparison_email` ✎ |
| Q4 | Backpack sample failed zip pull strength again; likely causes? | Test Lab / LIMS, PLM, Sampling & Development Tracker, Supplier Portal, Knowledge Base / Policy Library | `get_test_results_for_sample`, `compare_test_results_across_sample_rounds`, `get_tech_pack_for_style`, `get_supplier_corrective_action_response`, `search_knowledge_base_for_failure_modes`, `create_supplier_corrective_action_request` ✎, `reject_sample_for_style` ✎ |
| Q5 | Unit cost and margin at 20k, 50k, 100k units; sensitivity; break-even | Costing & Margin Tool, Landed Cost Calculator, Commodity & Market Data Feed | `get_costing_sheet_for_product`, `calculate_unit_cost_at_volumes`, `calculate_margin_at_volumes`, `run_cost_sensitivity_analysis`, `calculate_break_even_volume`, `create_costing_version_for_product` ✎ |
| Q6 | New materials or techniques cutting cost or weight; proven versus experimental | Web, Trend & Market Intelligence Platform, PLM, Commodity & Market Data Feed, Product Compliance & Regulatory Database | `search_web`, `search_innovative_materials`, `get_material_readiness_level`, `search_approved_material_suppliers`, `calculate_unit_cost_impact_of_material_change`, `get_material_compliance_status` |

## 52. Product designer

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Key AW27 women's colour, material, silhouette trends and relevance to our customer | Trend & Market Intelligence Platform, Web, Customer Data Platform (CDP), Competitor Price Monitoring Tool, Documents, Digital Asset Management (DAM) | `search_trend_forecasts_by_season`, `get_trend_lifecycle_stage`, `get_customer_segment_profile`, `search_competitor_ranges_by_attribute`, `search_web`, `draft_mood_summary`, `create_mood_board_in_dam` ✎ |
| Q2 | Design attributes separating top 50 from bottom 50 products, adjusted for availability | Data Warehouse / Lakehouse, PLM, Inventory Management System (IMS), Range Planning & Assortment Tool | `list_products_ranked_by_sales_for_season`, `get_product_design_attributes`, `get_in_stock_rate_by_product_week`, `run_attribute_performance_analysis`, `calculate_statistical_confidence` |
| Q3 | Competitor sustainable materials: certified claims versus greenwashing, and our gap | Web, Product Compliance & Regulatory Database, Trend & Market Intelligence Platform | `search_web`, `search_competitor_sustainability_claims`, `search_material_certification_registry`, `compare_claims_to_certifications`, `get_own_material_certifications` |
| Q4 | Which of three fabrics suits new overshirt at target cost, look, durability, claims | PLM, Costing & Margin Tool, Test Lab / LIMS, Supplier Portal | `get_fabric_specs_from_materials_library`, `get_fabric_test_results`, `get_fabric_sustainability_certifications`, `get_target_cost_for_style`, `calculate_garment_cost_by_fabric`, `get_fabric_mill_lead_time_and_stock` |
| Q5 | What reviews and returns say about best-selling jeans | Customer Reviews & Feedback Platform, Returns Management System (RMS), PLM | `search_customer_reviews_for_product`, `get_review_theme_summary`, `get_return_reasons_for_product`, `get_returns_rate_by_size_and_fit`, `create_product_change_request` ✎ |
| Q6 | What 25 to 34 year olds want from outdoor clothing; UK versus Germany | Market Research Platform, Customer Data Platform (CDP), Web, Customer Reviews & Feedback Platform | `search_survey_results_by_segment`, `compare_survey_results_by_market`, `get_customer_segment_profile`, `search_customer_reviews_by_segment`, `list_products_by_attribute_in_category` |

## 53. Technical designer / garment technologist

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Size 14 trousers T-4410 too tight at hip: pattern or factory tolerance; grading change | Returns Management System (RMS), PLM, Quality Management System (QMS), Data Warehouse / Lakehouse | `get_return_reasons_for_style`, `get_size_spec_and_grade_rules_for_style`, `get_inspection_measurements_for_style`, `calculate_measurement_deviation_vs_tolerance`, `get_sales_by_size_for_style`, `calculate_units_affected_by_grade_change`, `update_grade_rules_for_style` ✎ |
| Q2 | Typical female body measurements in Germany, France and UK | Web, Market Research Platform, PLM | `search_web`, `search_anthropometric_survey_data`, `get_size_chart_for_range`, `compare_size_chart_to_body_measurements` |
| Q3 | Technical jacket sample misses seam strength and water resistance: causes from tech pack | PLM, Test Lab / LIMS, Sampling & Development Tracker, Supplier Portal, Knowledge Base / Policy Library | `get_tech_pack_for_style`, `get_sample_test_results`, `get_supplier_comments_on_sample`, `get_test_method_details`, `search_knowledge_base_for_failure_modes`, `compare_construction_to_test_requirements`, `send_sample_comments_to_supplier` ✎ |
| Q4 | What tolerance should we set for this knit? | Test Lab / LIMS, Quality Management System (QMS), Knowledge Base / Policy Library, Web, PLM | `get_shrinkage_test_results_for_fabric`, `get_factory_process_capability`, `search_knowledge_base_for_tolerance_standards`, `search_web`, `calculate_recommended_tolerance`, `update_tolerance_in_tech_pack` ✎ |
| Q5 | Which styles have open fit comments? | Sampling & Development Tracker, PLM, Supplier Portal | `list_styles_with_open_fit_comments`, `get_sample_deadlines_by_style`, `get_supplier_response_times`, `send_supplier_fit_comment_reminder` ✎ |

## 54. Product manager, own brand

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | K-1700 kettle ratings and sales falling eight weeks: main driver and first action | Customer Reviews & Feedback Platform, Returns Management System (RMS), Pricing & Promotion Engine, Inventory Management System (IMS), Competitor Price Monitoring Tool, Web, Quality Management System (QMS), Data Warehouse / Lakehouse | `get_sales_trend_for_sku`, `get_ratings_trend_for_sku`, `get_review_theme_summary`, `get_return_reasons_for_sku`, `get_price_change_history_for_sku`, `get_stock_availability_history_for_sku`, `search_competitor_launches`, `get_quality_defects_for_sku`, `run_analysis`, `calculate_fix_cost_and_lead_time_for_sku`, `create_quality_hold_for_sku` ✎ |
| Q2 | Which products to extend, refresh, reprice or delete | Data Warehouse / Lakehouse, Costing & Margin Tool, Range Planning & Assortment Tool, PLM | `list_product_performance_for_range`, `get_product_strategic_role`, `calculate_product_margin_contribution`, `run_analysis`, `calculate_range_action_impact`, `update_product_range_status` ✎, `archive_product_in_plm` ✎ |
| Q3 | Whitespace in small kitchen appliances: size and realistic opportunities | Market Research Platform, Web, Competitor Price Monitoring Tool, Range Planning & Assortment Tool, Costing & Margin Tool | `search_market_size_by_category`, `search_competitor_products_by_category`, `list_range_gaps_by_category`, `get_category_margin_benchmarks`, `search_web` |
| Q4 | Expected sales and margin from next season's pipeline and riskiest products | Demand Planning System, Range Planning & Assortment Tool, Costing & Margin Tool, Sampling & Development Tracker | `get_pipeline_products_for_season`, `get_demand_forecast_for_pipeline_product`, `get_costed_margin_for_product`, `get_launch_readiness_signals_for_product`, `calculate_pipeline_risk_score` |
| Q5 | Range performance versus plan: sales, margin, returns, ratings, outliers, review shortlist | BI & Dashboards Platform, Data Warehouse / Lakehouse, Customer Reviews & Feedback Platform, Returns Management System (RMS), Range Planning & Assortment Tool, Email & Calendar | `get_range_performance_vs_plan`, `get_margin_vs_plan_by_product`, `get_returns_rate_by_product`, `get_ratings_by_product`, `list_outliers_vs_plan`, `run_analysis`, `draft_range_review_shortlist`, `send_range_review_pre_read_email` ✎ |
| Q6 | Competitor price positions and product roadmaps in our categories | Competitor Price Monitoring Tool, Web, Trend & Market Intelligence Platform | `search_competitor_products_by_category`, `get_competitor_price_history`, `calculate_price_index_vs_competitors`, `get_own_product_prices_and_quality_scores`, `search_competitor_launch_announcements`, `search_web` |

## 55. Packaging designer

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Cosmetics packaging legal marks, recycling labels, warnings, languages for France, Germany, Italy | Product Compliance & Regulatory Database, Packaging Compliance & EPR System, Web, Knowledge Base / Policy Library, Project & Portfolio Management Tool | `search_cosmetics_labelling_requirements_by_country`, `get_recycling_label_rules_by_country`, `get_language_requirements_by_country`, `search_web`, `draft_artwork_compliance_checklist`, `create_artwork_task` ✎ |
| Q2 | Moulded-pulp trays crack in drop tests: design changes | Test Lab / LIMS, Packaging Design System, PLM, Knowledge Base / Policy Library, Costing & Margin Tool | `get_drop_test_reports_for_pack`, `get_pack_dimensions_and_specs`, `get_material_specs_for_pack`, `search_knowledge_base_for_failure_modes`, `run_analysis`, `calculate_unit_cost_of_pack_change` |
| Q3 | Rigid box versus flexible pouch on cost, protection, appeal, pallet fill, recyclability, total cost | Packaging Design System, Costing & Margin Tool, Freight Rate Management System, Packaging Compliance & EPR System, Returns Management System (RMS) | `get_packaging_option_specs`, `get_pack_cost_quotes`, `calculate_pallet_fill_for_pack`, `get_freight_rates_for_lane`, `get_damage_rate_by_pack_type`, `get_recyclability_assessment_for_pack`, `calculate_total_cost_per_unit_by_pack_option` |
| Q4 | Cost and pallet-fill effect of 10% smaller carton | Packaging Design System, Freight Rate Management System, Test Lab / LIMS, Costing & Margin Tool | `get_carton_specs`, `calculate_carton_cost_at_new_dimensions`, `calculate_pallet_fill_for_pack`, `calculate_freight_saving_per_container`, `get_drop_and_crush_test_results_for_carton`, `update_carton_dimensions_in_pack_spec` ✎ |
| Q5 | How best retailers do sustainable packaging; reported savings; fit for our mix | Web, Packaging Compliance & EPR System, Packaging Design System | `search_web`, `search_retailer_sustainability_reports`, `search_packaging_changes_with_reported_savings`, `get_own_packaging_portfolio`, `compare_packaging_changes_to_product_mix` |

## 56. Trend/insight analyst

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Fastest-growing home and lifestyle trends in UK, Germany, US: fads or structural; segments; note | Trend & Market Intelligence Platform, Web, Data Warehouse / Lakehouse, Customer Data Platform (CDP), Collaboration & Messaging (Slack/Teams) | `get_search_interest_by_term_and_market`, `get_social_mentions_trend`, `get_sales_by_category_and_market`, `get_trend_lifecycle_stage`, `get_customer_segment_profile`, `run_analysis`, `draft_insights_note`, `send_insights_note_to_channel` ✎ |
| Q2 | Search interest in quiet luxury falling: implications for premium basics | Trend & Market Intelligence Platform, Data Warehouse / Lakehouse, Web | `get_search_interest_by_term_and_market`, `get_social_mentions_trend`, `get_sales_by_category_and_market`, `search_trend_forecasts_by_season`, `get_trend_lifecycle_stage` |
| Q3 | Wellness and recovery: competitor and adjacent products, flops, credible brand fit | Web, Trend & Market Intelligence Platform, Customer Reviews & Feedback Platform, Competitor Price Monitoring Tool | `search_web`, `search_product_launches_by_trend`, `search_competitor_products_by_category`, `search_customer_reviews_for_competitor_products`, `get_customer_segment_profile` |
| Q4 | Pick three trends to act on for next year's home range with evidence and test plan | Trend & Market Intelligence Platform, Data Warehouse / Lakehouse, Range Planning & Assortment Tool, Sampling & Development Tracker, Customer Data Platform (CDP), Competitor Price Monitoring Tool | `get_search_interest_by_term_and_market`, `get_social_mentions_trend`, `get_sales_by_category_and_market`, `search_competitor_ranges_by_attribute`, `get_customer_segment_profile`, `get_standard_lead_times_by_category`, `calculate_minimum_test_order_volume`, `run_analysis`, `create_test_order_request` ✎ |
| Q5 | How long will oversized outerwear last; when to taper | Trend & Market Intelligence Platform, Data Warehouse / Lakehouse, Pricing & Promotion Engine | `get_search_interest_by_term_and_market`, `get_trend_lifecycle_stage`, `get_historical_silhouette_cycles`, `get_sales_by_category_and_market`, `get_markdown_rate_by_category`, `run_analysis` |
| Q6 | Consumer priorities under cost pressure by age and region, survey versus sales | Market Research Platform, Data Warehouse / Lakehouse, Web | `search_survey_results_by_segment`, `compare_survey_results_by_market`, `get_sales_by_category_and_market`, `search_web`, `run_analysis` |
| Q7 | Do search, social and sales agree on our top ten categories? | Trend & Market Intelligence Platform, Web Analytics Platform, Data Warehouse / Lakehouse, Inventory Management System (IMS), Range Planning & Assortment Tool | `get_search_interest_by_term_and_market`, `get_social_mentions_trend`, `get_sales_by_category_and_market`, `get_in_stock_rate_by_category`, `run_analysis`, `create_range_gap_request` ✎ |
| Q8 | Which markets pick up trends before the UK? | Trend & Market Intelligence Platform, Web | `search_web`, `get_search_interest_by_term_and_market`, `get_historical_trend_adoption_by_market`, `run_analysis` |

## 58. Costing analyst

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Break down padded jacket quote PDF, benchmark lines, build should-cost, buyer questions | Documents, Costing & Margin Tool, Cost Modelling Tool, Commodity & Market Data Feed, Purchase Order System, Email & Calendar | `get_document_contents`, `get_historical_costings_for_similar_styles`, `get_labour_rates_by_country`, `get_commodity_price_trend`, `calculate_should_cost_for_style`, `compare_quote_lines_to_benchmarks`, `draft_negotiation_questions_for_buyer`, `send_negotiation_questions_to_buyer` ✎ |
| Q2 | Landed cost by volume, origin, freight, FX, duty; cheapest route at 30,000 units | Landed Cost Calculator, Freight Rate Management System, FX & Hedging Platform, Tax & Duty System, Customs & Trade Compliance System, Costing & Margin Tool | `get_costing_sheet_for_product`, `get_freight_rates_for_lane`, `get_fx_forward_rates`, `get_duty_rate_by_hs_code_and_origin`, `calculate_landed_cost_by_scenario`, `compare_landed_cost_across_origins`, `run_cost_sensitivity_analysis`, `update_costing_sheet_for_product` ✎ |
| Q3 | Take 8% out of product cost; saving per option and customer visibility | Costing & Margin Tool, Cost Modelling Tool, PLM, Customer Reviews & Feedback Platform | `get_costing_sheet_for_product`, `get_bill_of_materials_for_product`, `list_cost_reduction_options`, `calculate_saving_per_cost_option`, `get_review_theme_summary`, `calculate_combined_saving_for_options` |
| Q4 | Actual versus costed prices last season: where margin was lost and why | Costing & Margin Tool, ERP (General Ledger), Purchase Order System, FX & Hedging Platform | `get_costed_vs_actual_cost_by_product`, `get_actual_landed_cost_by_purchase_order`, `get_fx_rate_history`, `calculate_margin_variance_by_driver`, `run_analysis`, `update_costed_price_for_product` ✎ |
| Q5 | Current labour, material, freight costs in Vietnam, Bangladesh, Turkey; trend and outlook | Web, Commodity & Market Data Feed, Cost Modelling Tool, Freight Rate Management System | `get_labour_rates_by_country`, `get_commodity_price_trend`, `get_freight_rates_for_lane`, `search_web` |
| Q6 | Costing new range if tariffs may change mid-season: contingency and risk allocation | Tax & Duty System, Customs & Trade Compliance System, Landed Cost Calculator, Contract Management System, Web | `get_duty_rate_by_hs_code_and_origin`, `search_tariff_change_announcements`, `calculate_landed_cost_by_scenario`, `get_supplier_contract_terms_on_tariff_risk`, `calculate_tariff_contingency_by_origin` |

## 59. Product data / PIM specialist

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | 340 marketplace listing rejections: group by error and bulk fix | Marketplace Seller Portal, Product Information Management (PIM) | `list_rejected_listings`, `get_rejection_reasons_by_listing`, `get_pim_attribute_completeness`, `run_analysis`, `draft_bulk_attribute_correction_file`, `update_pim_attributes_in_bulk` ✎, `submit_marketplace_listing_resubmission` ✎ |
| Q2 | German and French marketplace data requirements for home appliances versus our listings | Web, Marketplace Seller Portal, Product Information Management (PIM) | `search_marketplace_content_requirements`, `get_pim_attribute_completeness_by_category`, `compare_pim_attributes_to_marketplace_requirements`, `search_web` |
| Q3 | Best attribute and taxonomy structure for home, marketplace mapping, migration effort | Product Information Management (PIM), Master Data Management (MDM), Marketplace Seller Portal, Web | `get_pim_taxonomy_and_attributes`, `get_pim_attribute_completeness_by_category`, `search_marketplace_content_requirements`, `get_marketplace_category_tree`, `draft_attribute_taxonomy_proposal`, `calculate_migration_effort_for_taxonomy`, `create_pim_attribute_group` ✎ |
| Q4 | Which data errors cause returns or complaints, and their cost | Returns Management System (RMS), Customer Service Platform, Product Information Management (PIM), Customer Reviews & Feedback Platform | `get_return_reasons_by_product`, `search_customer_service_contacts_by_issue`, `get_pim_attributes_for_product`, `calculate_cost_of_returns_by_error_type`, `run_analysis` |
| Q5 | Which products lack compliance information for selling in Ireland? | Product Compliance & Regulatory Database, Product Information Management (PIM), Supplier Portal, Data Warehouse / Lakehouse | `list_products_missing_compliance_data_by_market`, `get_product_sales_rank`, `list_suppliers_with_missing_documents`, `send_supplier_document_request` ✎ |

## 60. R&D materials scientist

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | PFAS-free durable water repellent alternatives: performance, cost, regulation; trial two for AW27 | Web, Product Compliance & Regulatory Database, Test Lab / LIMS, Supplier Portal, Costing & Margin Tool, Documents | `search_scientific_literature`, `search_web`, `get_dwr_alternative_test_data`, `get_regulatory_status_by_substance_and_region`, `search_approved_material_suppliers`, `get_material_cost_per_metre`, `calculate_trial_cost_and_duration` |
| Q2 | Literature and patents on bio-based leather alternatives; players, weaknesses, freedom to operate | Web, Trend & Market Intelligence Platform, Documents | `search_scientific_literature`, `search_patent_database`, `get_patent_family_and_assignee`, `search_web`, `compare_patent_claims_to_own_design` |
| Q3 | Recycled-nylon trial fabric failed abrasion tests: compare data and suggest reasons | Test Lab / LIMS, PLM, Supplier Portal, Knowledge Base / Policy Library | `get_test_results_for_material`, `get_material_specs`, `compare_material_test_data_to_reference_fabrics`, `search_knowledge_base_for_failure_modes`, `get_yarn_and_construction_details`, `create_test_request` ✎ |
| Q4 | Can recycled material scale to 2 million metres a year in supply and cost? | Supplier Portal, Commodity & Market Data Feed, Cost Modelling Tool, Costing & Margin Tool | `get_supplier_capacity_for_material`, `get_feedstock_supply_outlook`, `search_approved_material_suppliers`, `calculate_material_cost_at_volume`, `run_analysis` |
| Q5 | Which candidate materials go to pilot: tests, cost, time, pass-fail criteria | PLM, Test Lab / LIMS, Costing & Margin Tool, Project & Portfolio Management Tool | `list_candidate_materials`, `get_test_results_for_material`, `get_standard_test_plan_for_material_type`, `calculate_trial_cost_and_duration`, `search_test_labs_and_pilot_partners`, `draft_pilot_pass_fail_criteria`, `create_pilot_project` ✎, `archive_candidate_material` ✎ |
| Q6 | Latest on microfibre shedding and what helps | Web, Product Compliance & Regulatory Database, Knowledge Base / Policy Library | `search_scientific_literature`, `search_web`, `search_upcoming_regulations_by_topic` |
| Q7 | What do we need to claim recycled content? | Product Compliance & Regulatory Database, Supply Chain Due Diligence Platform, Documents, Web, Product Information Management (PIM) | `search_recycled_content_claim_standards`, `get_supplier_chain_of_custody_certificates`, `list_product_claims`, `compare_claims_to_certificate_coverage`, `update_product_claim` ✎, `remove_product_claim` ✎ |
| Q8 | New finish passes lab tests but fails real-world wear trials: why? | Test Lab / LIMS, Knowledge Base / Policy Library, Customer Reviews & Feedback Platform, Returns Management System (RMS) | `get_lab_test_method_for_finish`, `get_wear_trial_results`, `compare_lab_test_to_wear_trial_conditions`, `search_knowledge_base_for_failure_modes`, `draft_revised_test_protocol` |

## Tool catalogue for this category

| Tool | System | R/W | One-line description |
|---|---|---|---|
| `archive_candidate_material` | PLM | W | Archives a candidate material so it is removed from the active pilot list. |
| `archive_product_in_plm` | PLM | W | Archives a product record so it drops out of active range planning. |
| `calculate_break_even_volume` | Costing & Margin Tool | R | Calculate break even volume. |
| `calculate_carton_cost_at_new_dimensions` | Packaging Design System | R | Calculate carton cost at new dimensions. |
| `calculate_combined_saving_for_options` | Cost Modelling Tool | R | Calculate combined saving for options. |
| `calculate_cost_of_returns_by_error_type` | Returns Management System (RMS) | R | Calculate cost of returns by error type. |
| `calculate_date_recovery_cost` | Costing & Margin Tool | R | Calculate date recovery cost. |
| `calculate_fix_cost_and_lead_time_for_sku` | Costing & Margin Tool | R | Calculate fix cost and lead time for sku. |
| `calculate_freight_saving_per_container` | Freight Rate Management System | R | Calculate freight saving per container. |
| `calculate_garment_cost_by_fabric` | Costing & Margin Tool | R | Calculate garment cost by fabric. |
| `calculate_landed_cost_by_scenario` | Landed Cost Calculator | R | Calculate landed cost by scenario. |
| `calculate_margin_at_volumes` | Costing & Margin Tool | R | Calculate margin at volumes. |
| `calculate_margin_variance_by_driver` | Costing & Margin Tool | R | Calculate margin variance by driver. |
| `calculate_material_cost_at_volume` | Costing & Margin Tool | R | Calculate material cost at volume. |
| `calculate_measurement_deviation_vs_tolerance` | Quality Management System (QMS) | R | Calculate measurement deviation vs tolerance. |
| `calculate_migration_effort_for_taxonomy` | Product Information Management (PIM) | R | Calculate migration effort for taxonomy. |
| `calculate_minimum_test_order_volume` | Range Planning & Assortment Tool | R | Calculate minimum test order volume. |
| `calculate_pallet_fill_for_pack` | Packaging Design System | R | Calculate pallet fill for pack. |
| `calculate_pipeline_risk_score` | Demand Planning System | R | Calculate pipeline risk score. |
| `calculate_price_index_vs_competitors` | Competitor Price Monitoring Tool | R | Calculate price index vs competitors. |
| `calculate_product_margin_contribution` | Costing & Margin Tool | R | Calculate product margin contribution. |
| `calculate_range_action_impact` | Range Planning & Assortment Tool | R | Calculate range action impact. |
| `calculate_recommended_tolerance` | Quality Management System (QMS) | R | Calculate recommended tolerance. |
| `calculate_saving_per_cost_option` | Cost Modelling Tool | R | Calculate saving per cost option. |
| `calculate_should_cost_for_style` | Cost Modelling Tool | R | Calculate should cost for style. |
| `calculate_statistical_confidence` | Code Execution | R | Calculate statistical confidence. |
| `calculate_tariff_contingency_by_origin` | Landed Cost Calculator | R | Calculate tariff contingency by origin. |
| `calculate_tooling_amortisation_per_unit` | Costing & Margin Tool | R | Calculate tooling amortisation per unit. |
| `calculate_total_cost_per_unit_by_pack_option` | Packaging Design System | R | Calculate total cost per unit by pack option. |
| `calculate_trial_cost_and_duration` | Costing & Margin Tool | R | Calculate trial cost and duration. |
| `calculate_unit_cost_at_volumes` | Costing & Margin Tool | R | Calculate unit cost at volumes. |
| `calculate_unit_cost_impact_of_material_change` | Costing & Margin Tool | R | Calculate unit cost impact of material change. |
| `calculate_unit_cost_of_pack_change` | Packaging Design System | R | Calculate unit cost of pack change. |
| `calculate_units_affected_by_grade_change` | Data Warehouse / Lakehouse | R | Calculate units affected by grade change. |
| `compare_claims_to_certificate_coverage` | Product Compliance & Regulatory Database | R | Compare claims to certificate coverage. |
| `compare_claims_to_certifications` | Product Compliance & Regulatory Database | R | Compare claims to certifications. |
| `compare_construction_to_test_requirements` | Test Lab / LIMS | R | Compare construction to test requirements. |
| `compare_factory_quotes` | Sourcing / RFx Platform | R | Compare factory quotes. |
| `compare_lab_test_to_wear_trial_conditions` | Test Lab / LIMS | R | Compare lab test to wear trial conditions. |
| `compare_landed_cost_across_origins` | Landed Cost Calculator | R | Compare landed cost across origins. |
| `compare_material_test_data_to_reference_fabrics` | Test Lab / LIMS | R | Compare material test data to reference fabrics. |
| `compare_packaging_changes_to_product_mix` | Web | R | Compare packaging changes to product mix. |
| `compare_patent_claims_to_own_design` | Web | R | Compare patent claims to own design. |
| `compare_pim_attributes_to_marketplace_requirements` | Marketplace Seller Portal | R | Compare pim attributes to marketplace requirements. |
| `compare_quote_lines_to_benchmarks` | Cost Modelling Tool | R | Compare quote lines to benchmarks. |
| `compare_size_chart_to_body_measurements` | Market Research Platform | R | Compare size chart to body measurements. |
| `compare_survey_results_by_market` | Market Research Platform | R | Compare survey results by market. |
| `compare_test_results_across_sample_rounds` | Test Lab / LIMS | R | Compare test results across sample rounds. |
| `create_artwork_task` | Project & Portfolio Management Tool | W | Creates an artwork task for the design agency with checklist attached. |
| `create_costing_version_for_product` | Costing & Margin Tool | W | Saves a new costing version for a product at given volumes. |
| `create_mood_board_in_dam` | Digital Asset Management (DAM) | W | Creates a shared mood board asset collection for the design team. |
| `create_pilot_project` | Project & Portfolio Management Tool | W | Creates a pilot project with tasks, budget and pass-fail criteria for a material. |
| `create_pim_attribute_group` | Product Information Management (PIM) | W | Creates a new attribute group in the PIM taxonomy. |
| `create_product_change_request` | PLM | W | Creates a change request on a product for the next version. |
| `create_purchase_order` | Purchase Order System | W | Creates a draft purchase order for a product and supplier. |
| `create_quality_hold_for_sku` | Quality Management System (QMS) | W | Places a quality hold on a SKU or batch pending investigation. |
| `create_range_gap_request` | Range Planning & Assortment Tool | W | Creates a range gap request for an under-supplied category. |
| `create_supplier_corrective_action_request` | Supplier Portal | W | Creates a corrective action request against a supplier for a failed sample or test. |
| `create_test_order_request` | Sampling & Development Tracker | W | Creates a small test-order request for a trend-led product. |
| `create_test_request` | Test Lab / LIMS | W | Creates a test request for a material or sample at the lab. |
| `delete_draft_purchase_order` | Purchase Order System | W | Deletes a draft purchase order that has not been approved. |
| `draft_artwork_compliance_checklist` | Packaging Compliance & EPR System | R | Draft artwork compliance checklist. |
| `draft_attribute_taxonomy_proposal` | Product Information Management (PIM) | R | Draft attribute taxonomy proposal. |
| `draft_bulk_attribute_correction_file` | Product Information Management (PIM) | R | Draft bulk attribute correction file. |
| `draft_competitor_comparison_table` | Competitor Price Monitoring Tool | R | Draft competitor comparison table. |
| `draft_insights_note` | Trend & Market Intelligence Platform | R | Draft insights note. |
| `draft_launch_meeting_update` | Sampling & Development Tracker | R | Draft launch meeting update. |
| `draft_mood_summary` | Trend & Market Intelligence Platform | R | Draft mood summary. |
| `draft_negotiation_questions_for_buyer` | Cost Modelling Tool | R | Draft negotiation questions for buyer. |
| `draft_pilot_pass_fail_criteria` | Project & Portfolio Management Tool | R | Draft pilot pass fail criteria. |
| `draft_range_review_shortlist` | Customer Reviews & Feedback Platform | R | Draft range review shortlist. |
| `draft_revised_test_protocol` | Test Lab / LIMS | R | Draft revised test protocol. |
| `get_actual_landed_cost_by_purchase_order` | Landed Cost Calculator | R | Return actual landed cost by purchase order. |
| `get_bill_of_materials_for_product` | PLM | R | Return bill of materials for product. |
| `get_carton_specs` | Packaging Design System | R | Return carton specs. |
| `get_category_margin_benchmarks` | Costing & Margin Tool | R | Return category margin benchmarks. |
| `get_commodity_price_trend` | Trend & Market Intelligence Platform | R | Return commodity price trend. |
| `get_competitor_price_history` | Competitor Price Monitoring Tool | R | Return competitor price history. |
| `get_costed_margin_for_product` | Costing & Margin Tool | R | Return costed margin for product. |
| `get_costed_vs_actual_cost_by_product` | Costing & Margin Tool | R | Return costed vs actual cost by product. |
| `get_costing_sheet_for_product` | Costing & Margin Tool | R | Return costing sheet for product. |
| `get_critical_path_milestones_for_product` | Sampling & Development Tracker | R | Return critical path milestones for product. |
| `get_customer_segment_profile` | Customer Data Platform (CDP) | R | Return customer segment profile. |
| `get_damage_rate_by_pack_type` | Returns Management System (RMS) | R | Return damage rate by pack type. |
| `get_demand_forecast_for_pipeline_product` | Demand Planning System | R | Return demand forecast for pipeline product. |
| `get_document_contents` | Documents | R | Return document contents. |
| `get_drop_and_crush_test_results_for_carton` | Test Lab / LIMS | R | Return drop and crush test results for carton. |
| `get_drop_test_reports_for_pack` | Test Lab / LIMS | R | Return drop test reports for pack. |
| `get_duty_rate_by_hs_code_and_origin` | Tax & Duty System | R | Return duty rate by hs code and origin. |
| `get_dwr_alternative_test_data` | Test Lab / LIMS | R | Return dwr alternative test data. |
| `get_fabric_mill_lead_time_and_stock` | Supplier Portal | R | Return fabric mill lead time and stock. |
| `get_fabric_specs_from_materials_library` | PLM | R | Return fabric specs from materials library. |
| `get_fabric_sustainability_certifications` | Product Compliance & Regulatory Database | R | Return fabric sustainability certifications. |
| `get_fabric_test_results` | Test Lab / LIMS | R | Return fabric test results. |
| `get_factory_process_capability` | Quality Management System (QMS) | R | Return factory process capability. |
| `get_feedstock_supply_outlook` | Commodity & Market Data Feed | R | Return feedstock supply outlook. |
| `get_freight_rates_for_lane` | Freight Rate Management System | R | Return freight rates for lane. |
| `get_fx_forward_rates` | FX & Hedging Platform | R | Return fx forward rates. |
| `get_fx_rate_history` | FX & Hedging Platform | R | Return fx rate history. |
| `get_historical_costings_for_similar_styles` | Costing & Margin Tool | R | Return historical costings for similar styles. |
| `get_historical_silhouette_cycles` | Trend & Market Intelligence Platform | R | Return historical silhouette cycles. |
| `get_historical_trend_adoption_by_market` | Trend & Market Intelligence Platform | R | Return historical trend adoption by market. |
| `get_in_stock_rate_by_category` | Inventory Management System (IMS) | R | Return in stock rate by category. |
| `get_in_stock_rate_by_product_week` | Inventory Management System (IMS) | R | Return in stock rate by product week. |
| `get_inspection_measurements_for_style` | Quality Management System (QMS) | R | Return inspection measurements for style. |
| `get_lab_test_method_for_finish` | Test Lab / LIMS | R | Return lab test method for finish. |
| `get_labour_rates_by_country` | Cost Modelling Tool | R | Return labour rates by country. |
| `get_language_requirements_by_country` | Product Compliance & Regulatory Database | R | Return language requirements by country. |
| `get_launch_readiness_signals_for_product` | Sampling & Development Tracker | R | Return launch readiness signals for product. |
| `get_margin_vs_plan_by_product` | BI & Dashboards Platform | R | Return margin vs plan by product. |
| `get_markdown_rate_by_category` | Pricing & Promotion Engine | R | Return markdown rate by category. |
| `get_marketplace_category_tree` | Marketplace Seller Portal | R | Return marketplace category tree. |
| `get_material_compliance_status` | Product Compliance & Regulatory Database | R | Return material compliance status. |
| `get_material_cost_per_metre` | Costing & Margin Tool | R | Return material cost per metre. |
| `get_material_readiness_level` | PLM | R | Return material readiness level. |
| `get_material_specs` | PLM | R | Return material specs. |
| `get_material_specs_for_pack` | Packaging Design System | R | Return material specs for pack. |
| `get_open_purchase_orders_for_product` | Purchase Order System | R | Return open purchase orders for product. |
| `get_own_material_certifications` | Product Compliance & Regulatory Database | R | Return own material certifications. |
| `get_own_packaging_portfolio` | Packaging Design System | R | Return own packaging portfolio. |
| `get_own_product_prices_and_quality_scores` | Pricing & Promotion Engine | R | Return own product prices and quality scores. |
| `get_pack_cost_quotes` | Packaging Design System | R | Return pack cost quotes. |
| `get_pack_dimensions_and_specs` | Packaging Design System | R | Return pack dimensions and specs. |
| `get_packaging_option_specs` | Packaging Design System | R | Return packaging option specs. |
| `get_patent_family_and_assignee` | Web | R | Return patent family and assignee. |
| `get_pim_attribute_completeness` | Product Information Management (PIM) | R | Return pim attribute completeness. |
| `get_pim_attribute_completeness_by_category` | Product Information Management (PIM) | R | Return pim attribute completeness by category. |
| `get_pim_attributes_for_product` | Product Information Management (PIM) | R | Return pim attributes for product. |
| `get_pim_taxonomy_and_attributes` | Product Information Management (PIM) | R | Return pim taxonomy and attributes. |
| `get_pipeline_products_for_season` | Demand Planning System | R | Return pipeline products for season. |
| `get_price_change_history_for_sku` | Pricing & Promotion Engine | R | Return price change history for sku. |
| `get_product_design_attributes` | PLM | R | Return product design attributes. |
| `get_product_sales_rank` | Data Warehouse / Lakehouse | R | Return product sales rank. |
| `get_product_strategic_role` | Range Planning & Assortment Tool | R | Return product strategic role. |
| `get_quality_defects_for_sku` | Quality Management System (QMS) | R | Return quality defects for sku. |
| `get_range_performance_vs_plan` | BI & Dashboards Platform | R | Return range performance vs plan. |
| `get_ratings_by_product` | Customer Reviews & Feedback Platform | R | Return ratings by product. |
| `get_ratings_trend_for_sku` | Customer Reviews & Feedback Platform | R | Return ratings trend for sku. |
| `get_recyclability_assessment_for_pack` | Packaging Compliance & EPR System | R | Return recyclability assessment for pack. |
| `get_recycling_label_rules_by_country` | Packaging Compliance & EPR System | R | Return recycling label rules by country. |
| `get_regulatory_status_by_substance_and_region` | Product Compliance & Regulatory Database | R | Return regulatory status by substance and region. |
| `get_rejection_reasons_by_listing` | Marketplace Seller Portal | R | Return rejection reasons by listing. |
| `get_return_reasons_by_product` | Returns Management System (RMS) | R | Return return reasons by product. |
| `get_return_reasons_for_product` | Returns Management System (RMS) | R | Return return reasons for product. |
| `get_return_reasons_for_sku` | Returns Management System (RMS) | R | Return return reasons for sku. |
| `get_return_reasons_for_style` | Returns Management System (RMS) | R | Return return reasons for style. |
| `get_returns_rate_by_product` | Returns Management System (RMS) | R | Return returns rate by product. |
| `get_returns_rate_by_size_and_fit` | Returns Management System (RMS) | R | Return returns rate by size and fit. |
| `get_review_theme_summary` | Customer Reviews & Feedback Platform | R | Return review theme summary. |
| `get_rfq_responses_for_product` | Sourcing / RFx Platform | R | Return rfq responses for product. |
| `get_sales_by_category_and_market` | Data Warehouse / Lakehouse | R | Return sales by category and market. |
| `get_sales_by_size_for_style` | Data Warehouse / Lakehouse | R | Return sales by size for style. |
| `get_sales_trend_for_sku` | Trend & Market Intelligence Platform | R | Return sales trend for sku. |
| `get_sample_approval_status_for_product` | Sampling & Development Tracker | R | Return sample approval status for product. |
| `get_sample_deadlines_by_style` | Sampling & Development Tracker | R | Return sample deadlines by style. |
| `get_sample_test_results` | Test Lab / LIMS | R | Return sample test results. |
| `get_search_interest_by_term_and_market` | Trend & Market Intelligence Platform | R | Return search interest by term and market. |
| `get_shrinkage_test_results_for_fabric` | Test Lab / LIMS | R | Return shrinkage test results for fabric. |
| `get_size_chart_for_range` | PLM | R | Return size chart for range. |
| `get_size_spec_and_grade_rules_for_style` | PLM | R | Return size spec and grade rules for style. |
| `get_social_mentions_trend` | Trend & Market Intelligence Platform | R | Return social mentions trend. |
| `get_standard_lead_times_by_category` | Sampling & Development Tracker | R | Return standard lead times by category. |
| `get_standard_test_plan_for_material_type` | Test Lab / LIMS | R | Return standard test plan for material type. |
| `get_stock_availability_history_for_sku` | Inventory Management System (IMS) | R | Return stock availability history for sku. |
| `get_supplier_capacity_for_material` | Supplier Portal | R | Return supplier capacity for material. |
| `get_supplier_chain_of_custody_certificates` | Supply Chain Due Diligence Platform | R | Return supplier chain of custody certificates. |
| `get_supplier_comments_on_sample` | Supplier Portal | R | Return supplier comments on sample. |
| `get_supplier_compliance_history` | Supplier Onboarding & Risk System | R | Return supplier compliance history. |
| `get_supplier_contract_terms_on_tariff_risk` | Contract Management System | R | Return supplier contract terms on tariff risk. |
| `get_supplier_corrective_action_response` | Supplier Portal | R | Return supplier corrective action response. |
| `get_supplier_milestone_updates` | Supplier Portal | R | Return supplier milestone updates. |
| `get_supplier_response_times` | Supplier Portal | R | Return supplier response times. |
| `get_target_cost_for_style` | Costing & Margin Tool | R | Return target cost for style. |
| `get_tech_pack_for_style` | Packaging Design System | R | Return tech pack for style. |
| `get_test_method_details` | Test Lab / LIMS | R | Return test method details. |
| `get_test_results_for_material` | Test Lab / LIMS | R | Return test results for material. |
| `get_test_results_for_sample` | Test Lab / LIMS | R | Return test results for sample. |
| `get_trend_lifecycle_stage` | Trend & Market Intelligence Platform | R | Return trend lifecycle stage. |
| `get_wear_trial_results` | Test Lab / LIMS | R | Return wear trial results. |
| `get_yarn_and_construction_details` | PLM | R | Return yarn and construction details. |
| `list_candidate_materials` | PLM | R | List candidate materials. |
| `list_cost_reduction_options` | Cost Modelling Tool | R | List cost reduction options. |
| `list_launch_products_by_season` | Sampling & Development Tracker | R | List launch products by season. |
| `list_outliers_vs_plan` | BI & Dashboards Platform | R | List outliers vs plan. |
| `list_preproduction_sample_acceptance_criteria` | Quality Management System (QMS) | R | List preproduction sample acceptance criteria. |
| `list_product_claims` | Product Information Management (PIM) | R | List product claims. |
| `list_product_performance_for_range` | Data Warehouse / Lakehouse | R | List product performance for range. |
| `list_products_by_attribute_in_category` | Product Information Management (PIM) | R | List products by attribute in category. |
| `list_products_missing_compliance_data_by_market` | Product Compliance & Regulatory Database | R | List products missing compliance data by market. |
| `list_products_ranked_by_sales_for_season` | Data Warehouse / Lakehouse | R | List products ranked by sales for season. |
| `list_range_gaps_by_category` | Range Planning & Assortment Tool | R | List range gaps by category. |
| `list_rejected_listings` | Marketplace Seller Portal | R | List rejected listings. |
| `list_styles_with_open_fit_comments` | Sampling & Development Tracker | R | List styles with open fit comments. |
| `list_suppliers_with_missing_documents` | Documents | R | List suppliers with missing documents. |
| `reject_sample_for_style` | Sampling & Development Tracker | W | Marks a sample round as rejected and requests a resubmission from the factory. |
| `remove_product_claim` | Product Information Management (PIM) | W | Removes a product claim from a listing in PIM. |
| `run_analysis` | Code Execution | R | Run an ad hoc analysis or chart in the code sandbox. |
| `run_attribute_performance_analysis` | Code Execution | R | Run attribute performance analysis. |
| `run_cost_sensitivity_analysis` | Code Execution | R | Run cost sensitivity analysis. |
| `search_anthropometric_survey_data` | Market Research Platform | R | Search for anthropometric survey data. |
| `search_approved_material_suppliers` | Supplier Portal | R | Search for approved material suppliers. |
| `search_competitor_launch_announcements` | Web | R | Search for competitor launch announcements. |
| `search_competitor_launches` | Web | R | Search for competitor launches. |
| `search_competitor_products_by_category` | Competitor Price Monitoring Tool | R | Search for competitor products by category. |
| `search_competitor_ranges_by_attribute` | Competitor Price Monitoring Tool | R | Search for competitor ranges by attribute. |
| `search_competitor_sustainability_claims` | Product Compliance & Regulatory Database | R | Search for competitor sustainability claims. |
| `search_cosmetics_labelling_requirements_by_country` | Product Compliance & Regulatory Database | R | Search for cosmetics labelling requirements by country. |
| `search_customer_reviews_by_segment` | Customer Reviews & Feedback Platform | R | Search for customer reviews by segment. |
| `search_customer_reviews_for_competitor_products` | Customer Reviews & Feedback Platform | R | Search for customer reviews for competitor products. |
| `search_customer_reviews_for_product` | Customer Reviews & Feedback Platform | R | Search for customer reviews for product. |
| `search_customer_service_contacts_by_issue` | Customer Service Platform | R | Search for customer service contacts by issue. |
| `search_factory_audit_results` | Factory Audit Platform | R | Search for factory audit results. |
| `search_innovative_materials` | Trend & Market Intelligence Platform | R | Search for innovative materials. |
| `search_knowledge_base_for_failure_modes` | Knowledge Base / Policy Library | R | Search for knowledge base for failure modes. |
| `search_knowledge_base_for_tolerance_standards` | Quality Management System (QMS) | R | Search for knowledge base for tolerance standards. |
| `search_market_size_by_category` | Market Research Platform | R | Search for market size by category. |
| `search_marketplace_content_requirements` | Marketplace Seller Portal | R | Search for marketplace content requirements. |
| `search_material_certification_registry` | Product Compliance & Regulatory Database | R | Search for material certification registry. |
| `search_packaging_changes_with_reported_savings` | Web | R | Search for packaging changes with reported savings. |
| `search_patent_database` | Web | R | Search for patent database. |
| `search_product_launches_by_trend` | Trend & Market Intelligence Platform | R | Search for product launches by trend. |
| `search_recycled_content_claim_standards` | Product Compliance & Regulatory Database | R | Search for recycled content claim standards. |
| `search_retailer_sustainability_reports` | Web | R | Search for retailer sustainability reports. |
| `search_scientific_literature` | Web | R | Search for scientific literature. |
| `search_survey_results_by_segment` | Market Research Platform | R | Search for survey results by segment. |
| `search_tariff_change_announcements` | Web | R | Search for tariff change announcements. |
| `search_test_labs_and_pilot_partners` | Project & Portfolio Management Tool | R | Search for test labs and pilot partners. |
| `search_trend_forecasts_by_season` | Trend & Market Intelligence Platform | R | Search for trend forecasts by season. |
| `search_upcoming_regulations_by_topic` | Product Compliance & Regulatory Database | R | Search for upcoming regulations by topic. |
| `search_web` | Web | R | Search for web. |
| `send_competitor_comparison_email` | Email & Calendar | W | Emails the competitor comparison to the buying team. |
| `send_insights_note_to_channel` | Collaboration & Messaging (Slack/Teams) | W | Posts the insights note to a team channel. |
| `send_negotiation_questions_to_buyer` | Email & Calendar | W | Emails the negotiation question list to the buyer. |
| `send_range_review_pre_read_email` | Email & Calendar | W | Sends the range review shortlist to the meeting attendees. |
| `send_sample_comments_to_supplier` | Supplier Portal | W | Sends revised construction comments on a sample to the supplier. |
| `send_supplier_document_request` | Supplier Portal | W | Sends a request to a supplier for missing compliance documents. |
| `send_supplier_fit_comment_reminder` | Supplier Portal | W | Sends a reminder to suppliers with unanswered fit comments. |
| `send_supplier_milestone_chase` | Supplier Portal | W | Sends a chaser message to the supplier on a late launch milestone. |
| `submit_marketplace_listing_resubmission` | Marketplace Seller Portal | W | Resubmits corrected listings to the marketplace for approval. |
| `submit_purchase_order_for_approval` | Purchase Order System | W | Submits a draft purchase order into the approval workflow. |
| `update_carton_dimensions_in_pack_spec` | Packaging Design System | W | Updates carton dimensions in the packaging specification. |
| `update_costed_price_for_product` | Costing & Margin Tool | W | Updates the costed price for a product for the next season. |
| `update_costing_sheet_for_product` | Costing & Margin Tool | W | Updates the active costing sheet for a product with the chosen scenario. |
| `update_grade_rules_for_style` | PLM | W | Updates the grading rules for a style in the tech pack. |
| `update_pim_attributes_in_bulk` | Product Information Management (PIM) | W | Applies a bulk correction file to product attributes in PIM. |
| `update_product_claim` | Product Information Management (PIM) | W | Updates the wording of a product claim in PIM. |
| `update_product_range_status` | Range Planning & Assortment Tool | W | Changes a product status in the range plan (extend, refresh, reprice, delete). |
| `update_tolerance_in_tech_pack` | PLM | W | Updates a measurement or shrinkage tolerance in the tech pack for a style. |
