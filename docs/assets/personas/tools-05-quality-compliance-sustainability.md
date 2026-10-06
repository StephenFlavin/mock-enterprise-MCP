# Systems and MCP tools · 05 Quality, Compliance and Sustainability

For every question in the Quality, Compliance and Sustainability personas file, this lists the enterprise systems that must be reached and the MCP tool methods an AI agent would call, in likely call order.
Tool names are entity-scoped and shared across all nine category files so the benchmark stays consistent; parameters are omitted.
Follow-up questions have no rows; where one needs an extra system, it is folded into the parent row.

**Legend:** `read tools` use get_ / list_ / search_ / calculate_ / compare_ / run_; `draft_` tools produce documents and are not writes; write or side-effect tools are marked ✎. Web = public search/fetch; Documents = attached or shared files; Code Execution = analysis sandbox.


## 42. QA technologist

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Seven polyester blouse lots failed rubbing colourfastness: common factors, units shipped, supplier corrective actions | Test Lab / LIMS, Quality Management System (QMS), Product Lifecycle Management (PLM), Inventory Management System (IMS), Order Management System (OMS), Documents | `get_document_contents`, `search_test_results_by_failure_mode`, `get_production_lot_details`, `get_dye_lot_and_process_changes_for_lots`, `run_analysis`, `get_shipped_units_by_lot`, `draft_supplier_corrective_action_request`, `update_inventory_hold_status` ✎, `create_supplier_corrective_action_request` ✎, `send_supplier_corrective_action_request` ✎ |
| Q2 | Lot fails only zip strength by 4%: release, rework or reject? | Test Lab / LIMS, Quality Management System (QMS), Customer Service Platform, Knowledge Base / Policy Library | `get_lot_test_results`, `get_product_specification_tolerances`, `get_lot_acceptance_policy`, `search_complaints_by_defect_type`, `update_lot_disposition` ✎, `send_supplier_notification` ✎, `create_retest_request` ✎ |
| Q3 | Kids' sleepwear flammability rules in UK, EU and US, plus our affected products | Product Compliance & Regulatory Database, Web, Product Lifecycle Management (PLM) | `search_regulations_by_product_type`, `get_regulatory_requirements_by_market`, `search_web`, `compare_requirements_across_markets`, `list_products_by_regulated_category` |
| Q4 | Which factories are most likely to cause quality problems next season? | Quality Management System (QMS), Factory Audit Platform, Test Lab / LIMS, Purchase Order System | `list_factory_quality_scorecards`, `get_factory_defect_rate_trend`, `get_factory_audit_scores`, `get_open_purchase_orders_by_factory`, `calculate_factory_quality_risk_score`, `run_analysis`, `create_inspection_booking` ✎ |
| Q5 | Shoe sole separation complaints rising: combine returns, reviews, factory and batch data | Returns Management System (RMS), Customer Reviews & Feedback Platform, Quality Management System (QMS), Product Lifecycle Management (PLM), Inventory Management System (IMS) | `get_returns_by_reason_code`, `search_review_text_by_topic`, `get_factory_defect_inspection_results`, `get_material_batches_for_product`, `run_analysis`, `update_inventory_hold_status` ✎, `create_quality_incident` ✎ |

## 43. Factory auditor

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Review three Factory K audit reports for repeat or systemic issues, reopened findings and next focus | Factory Audit Platform, Documents, Supply Chain Due Diligence Platform | `get_document_contents`, `list_audit_reports_for_factory`, `get_audit_findings_for_factory`, `compare_audit_findings_across_audits`, `get_corrective_action_status`, `draft_next_audit_focus_plan`, `update_audit_finding_status` ✎ |
| Q2 | Current minimum wage and overtime rules in Gujarat and Tamil Nadu, and recent changes | Web, Knowledge Base / Policy Library | `search_labour_law_by_state`, `search_web`, `fetch_web_page`, `get_supplier_code_of_conduct_clauses` |
| Q3 | News about this factory: credibility and what to ask it | Web, Supply Chain Due Diligence Platform, Supplier Onboarding & Risk System | `get_factory_profile`, `search_adverse_media_for_entity`, `search_ngo_and_union_reports`, `get_supplier_risk_alerts`, `create_supplier_risk_alert` ✎ |
| Q4 | Pass, corrective action or suspend orders based on findings; draft the action plan | Factory Audit Platform, Purchase Order System, Knowledge Base / Policy Library, Supplier Onboarding & Risk System | `get_audit_findings_for_factory`, `get_corrective_action_policy`, `get_open_purchase_orders_by_factory`, `get_factory_risk_rating`, `draft_corrective_action_plan`, `create_corrective_action_plan` ✎, `block_purchase_orders_for_factory` ✎ |
| Q5 | Which factories have overdue critical findings? | Factory Audit Platform, Purchase Order System | `list_overdue_critical_findings`, `get_factory_risk_rating`, `get_open_purchase_orders_by_factory`, `send_corrective_action_reminder` ✎, `update_corrective_action_due_date` ✎ |

## 44. Product safety / regulatory specialist

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Children's insulated bottle requirements across UK, EU, US, Australia; flag non-compliant current bottles | Product Compliance & Regulatory Database, Web, Documents, Product Lifecycle Management (PLM), Test Lab / LIMS | `get_document_contents`, `search_regulations_by_product_type`, `get_regulatory_requirements_by_market`, `compare_requirements_across_markets`, `get_product_specifications`, `compare_product_specs_to_requirements`, `get_testing_cost_and_lead_time`, `create_test_request` ✎ |
| Q2 | Leather bag failed chromium VI: trace tannery, batches, other products using same leather | Test Lab / LIMS, Product Lifecycle Management (PLM), Quality Management System (QMS), Inventory Management System (IMS), Product Compliance & Regulatory Database | `get_test_report_details`, `get_bill_of_materials_with_suppliers`, `get_material_batch_traceability`, `list_products_using_material`, `get_regulatory_reporting_obligations`, `draft_supplier_notification`, `create_quality_incident` ✎, `update_inventory_hold_status` ✎, `send_supplier_notification` ✎ |
| Q3 | Regulation changes coming in the next 18 months, ranked by impact and deadline | Product Compliance & Regulatory Database, Web, Product Lifecycle Management (PLM) | `list_upcoming_regulatory_changes`, `get_regulation_deadlines`, `list_products_by_regulated_category`, `calculate_regulation_impact_score`, `search_web`, `create_compliance_task` ✎ |
| Q4 | Impact of new PFAS restrictions on waterproof outerwear and alternatives | Product Compliance & Regulatory Database, Product Lifecycle Management (PLM), Web, Costing & Margin Tool, Test Lab / LIMS | `search_regulations_by_product_type`, `get_regulation_deadlines`, `list_products_using_substance`, `search_alternative_materials`, `get_material_cost_and_performance_data` |
| Q5 | Does our new battery smart bottle need extra EU and UK certification? | Product Compliance & Regulatory Database, Product Lifecycle Management (PLM), Web, Test Lab / LIMS | `get_product_specifications`, `get_regulatory_requirements_by_market`, `get_testing_cost_and_lead_time`, `search_notified_bodies`, `create_test_request` ✎ |
| Q6 | What triggers toy and kids' product recalls, enforcement trends, how to reduce our risk | Web, Incident & Recall Management System, Product Lifecycle Management (PLM) | `search_recall_notices`, `search_web`, `get_internal_incident_history`, `list_products_by_regulated_category` |
| Q7 | Check 12 label images against German and French requirements | Documents, Product Compliance & Regulatory Database, Product Lifecycle Management (PLM) | `get_document_contents`, `extract_label_text_from_images`, `get_labelling_requirements_by_market`, `compare_label_to_requirements`, `get_product_specifications`, `create_compliance_issue` ✎, `update_compliance_issue_status` ✎ |
| Q8 | Any of our materials on restricted or candidate substance lists? | Product Compliance & Regulatory Database, Product Lifecycle Management (PLM), Supplier Portal | `search_restricted_substance_lists`, `get_substance_list_matches_for_materials`, `list_products_using_substance`, `get_bill_of_materials_with_suppliers`, `search_alternative_materials`, `update_material_compliance_status` ✎ |

## 45. Sustainability manager

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Break annual emissions total down by category, supplier and value chain stage with data confidence | Carbon & ESG Reporting Platform, Supplier Portal, Spend Analytics Platform, Code Execution | `get_emissions_by_scope_and_category`, `get_emissions_by_product_category`, `get_emissions_by_supplier`, `get_emissions_data_quality_flags`, `run_analysis` |
| Q2 | Compare three Scope 3 levers by tonnes saved, cost, feasibility and timing | Carbon & ESG Reporting Platform, Documents, Transport Management System (TMS), Freight Rate Management System, Costing & Margin Tool, Supplier Portal, Code Execution | `get_document_contents`, `get_emissions_by_supplier`, `get_air_freight_volumes_and_emissions`, `compare_air_sea_freight_cost_and_emissions`, `get_recycled_material_cost_premium`, `get_supplier_renewable_energy_status`, `calculate_abatement_cost_per_tonne`, `run_analysis`, `create_sustainability_initiative` ✎ |
| Q3 | Will we meet the 2030 Scope 3 target, what is the gap, what closes it | Carbon & ESG Reporting Platform, Supplier Portal, Code Execution | `get_emissions_reduction_targets`, `get_emissions_history_by_year`, `get_planned_reduction_initiatives`, `get_supplier_emissions_commitments`, `calculate_emissions_trajectory_gap`, `run_analysis` |
| Q4 | SBTi retail Scope 3 requirements, peer comparison, data needed | Web, Carbon & ESG Reporting Platform | `search_web`, `fetch_web_page`, `search_peer_sustainability_disclosures`, `get_emissions_reduction_targets`, `get_emissions_data_coverage` |
| Q5 | Footprint of recycled versus virgin polyester and organic versus conventional cotton | Carbon & ESG Reporting Platform, Web | `search_emission_factors_by_material`, `get_emission_factor_data_quality`, `search_web` |
| Q6 | Transport emissions intensity rose after shift to sea: data issue or real? | Carbon & ESG Reporting Platform, Transport Management System (TMS), Code Execution | `get_transport_emissions_intensity_trend`, `get_shipments_by_lane_and_mode`, `get_emission_factors_applied_to_transport`, `run_analysis`, `update_transport_emission_factor_for_lane` ✎ |
| Q7 | Which suppliers to prioritise for emissions engagement | Carbon & ESG Reporting Platform, Spend Analytics Platform, Supplier Relationship Management (SRM) | `get_emissions_by_supplier`, `get_spend_by_supplier`, `get_supplier_engagement_status`, `get_supplier_science_based_target_status`, `calculate_supplier_engagement_priority_score`, `create_supplier_engagement_plan` ✎, `send_supplier_engagement_invitation` ✎, `remove_supplier_from_engagement_programme` ✎ |
| Q8 | Results and cost-effectiveness of retailers' supplier decarbonisation programmes | Web, Knowledge Base / Policy Library, Code Execution | `search_web`, `fetch_web_page`, `search_peer_sustainability_disclosures`, `run_analysis` |

## 46. Ethical trade manager

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Where is forced-labour risk highest, with evidence and sub-tier mapping gaps | Supply Chain Due Diligence Platform, Supplier Onboarding & Risk System, Factory Audit Platform, Web | `list_suppliers_by_forced_labour_risk`, `get_supplier_risk_evidence`, `get_supply_chain_map_for_product`, `get_supply_chain_mapping_gaps`, `get_country_risk_indices`, `create_due_diligence_task` ✎ |
| Q2 | Credibility of debt bondage allegation at a Tamil Nadu spinning mill, our exposure, escalation note | Documents, Web, Supply Chain Due Diligence Platform, Factory Audit Platform, Purchase Order System, Email & Calendar | `get_document_contents`, `fetch_web_page`, `search_ngo_and_union_reports`, `search_adverse_media_for_entity`, `get_supplier_sub_tier_relationships`, `get_audit_findings_for_factory`, `get_due_diligence_policy_obligations`, `draft_escalation_note`, `create_due_diligence_case` ✎, `send_escalation_note` ✎ |
| Q3 | After audit: remediate, suspend or exit, and protect workers if leaving | Factory Audit Platform, Supply Chain Due Diligence Platform, Purchase Order System, Knowledge Base / Policy Library, Web | `get_audit_findings_for_factory`, `get_corrective_action_status`, `get_worker_grievance_records`, `calculate_supplier_share_of_factory_capacity`, `get_responsible_exit_policy`, `search_web`, `create_corrective_action_plan` ✎, `block_purchase_orders_for_factory` ✎ |
| Q4 | Latest forced-labour import and due-diligence laws in EU, UK, US, Canada; what we must prove | Web, Product Compliance & Regulatory Database, Customs & Trade Compliance System, Supply Chain Due Diligence Platform | `search_due_diligence_regulations`, `search_web`, `get_import_volumes_by_hs_code_and_origin`, `list_products_by_origin_country_and_material`, `get_evidence_inventory_for_due_diligence`, `draft_compliance_gap_list`, `create_due_diligence_task` ✎ |
| Q5 | What grievance and audit data say about top 10 riskiest factories | Factory Audit Platform, Supply Chain Due Diligence Platform, Supplier Onboarding & Risk System, Code Execution | `list_suppliers_by_forced_labour_risk`, `get_worker_grievance_records`, `get_audit_findings_for_factory`, `run_analysis` |
| Q6 | Impact if cotton from a high-risk region is blocked at the border | Customs & Trade Compliance System, Purchase Order System, Supply Planning System (MRP/DRP), Web | `get_import_volumes_by_hs_code_and_origin`, `get_open_purchase_orders_by_material_origin`, `search_import_detention_orders`, `search_alternative_cotton_sources`, `calculate_volume_share_by_origin` |
| Q7 | Which cotton traceability tools work, how effective, cost | Web, Supply Chain Due Diligence Platform, Supplier Portal | `search_web`, `fetch_web_page`, `get_supplier_base_profile_by_country`, `get_supply_chain_mapping_gaps` |
| Q8 | What NGOs flagged this year in our sectors and countries | Web, Supply Chain Due Diligence Platform, Supplier Onboarding & Risk System | `search_ngo_and_union_reports`, `search_web`, `list_suppliers_by_country_and_sector`, `get_supplier_risk_alerts`, `create_supplier_risk_alert` ✎ |

## 47. Recall/incident manager

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Overheating fan battery SKU PF-220: batch, factory, cell supplier, units and locations | Incident & Recall Management System, Product Lifecycle Management (PLM), Inventory Management System (IMS), Warehouse Management System (WMS), Order Management System (OMS), Track & Trace Platform | `get_incident_report`, `get_product_batch_and_factory_for_sku`, `get_bill_of_materials_with_suppliers`, `list_products_using_component`, `get_units_sold_by_batch`, `get_stock_by_location_for_batch`, `get_in_transit_stock_for_batch`, `create_recall_case` ✎, `update_inventory_hold_status` ✎ |
| Q2 | Withdrawal or recall, who to notify per country and when; draft notification | Incident & Recall Management System, Product Compliance & Regulatory Database, Knowledge Base / Policy Library | `get_incident_report`, `get_recall_vs_withdrawal_criteria`, `get_countries_where_batch_sold`, `get_regulatory_notification_requirements_by_country`, `draft_regulatory_notification`, `send_regulatory_notification` ✎ |
| Q3 | Similar battery incidents elsewhere: costs, reputation, good communication | Web, Incident & Recall Management System | `search_recall_notices`, `search_web`, `fetch_web_page`, `get_internal_incident_history` |
| Q4 | All-in cost of recalling 18,000 units | Incident & Recall Management System, Inventory Management System (IMS), Order Management System (OMS), ERP (General Ledger), Costing & Margin Tool | `get_stock_by_location_for_batch`, `get_unit_cost_and_retail_price`, `get_historical_recall_costs`, `calculate_recall_cost_estimate`, `run_analysis`, `update_recall_case_cost_estimate` ✎ |
| Q5 | Draft customer notice, store instructions, press statement and flag wording risk | Incident & Recall Management System, Knowledge Base / Policy Library, Product Compliance & Regulatory Database, Documents | `get_incident_report`, `get_recall_communication_templates`, `get_legal_wording_guidelines`, `draft_customer_recall_notice`, `draft_store_instructions`, `draft_press_statement`, `send_store_instructions` ✎, `delete_draft_press_statement` ✎ |

## 48. ESG reporting analyst

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | What's our biggest ESG data gap? | Carbon & ESG Reporting Platform, Knowledge Base / Policy Library | `get_esg_data_coverage_by_metric`, `list_in_scope_reporting_regulations`, `get_reporting_framework_requirements`, `calculate_esg_data_gap_materiality`, `create_esg_data_gap_task` ✎ |
| Q2 | Scope 2 fell 15%: real or method/boundary change? | Carbon & ESG Reporting Platform, Retail Property & Footfall System, Internal Audit System, Code Execution | `get_scope2_emissions_by_period`, `get_energy_consumption_by_site`, `get_scope2_method_and_boundary_changes`, `get_emission_factors_applied`, `calculate_scope2_reconciliation`, `get_assurance_findings` |
| Q3 | Metrics, boundaries, assurance evidence and peer disclosure for supply chain emissions | Carbon & ESG Reporting Platform, Web, Spend Analytics Platform, Knowledge Base / Policy Library | `get_reporting_framework_requirements`, `search_peer_sustainability_disclosures`, `get_emissions_data_coverage`, `get_supplier_data_evidence_status`, `get_assurance_requirements` |
| Q4 | Who hasn't sent ESG data, which are low quality, draft chasers | Carbon & ESG Reporting Platform, Supplier Portal, Spend Analytics Platform, Email & Calendar | `list_supplier_esg_submissions`, `get_submission_data_quality_scores`, `get_spend_by_supplier`, `get_data_request_deadline`, `draft_supplier_chaser_email`, `send_supplier_chaser_email` ✎ |
| Q5 | Systems, data and cost needed for upcoming reporting rules | Carbon & ESG Reporting Platform, Web, Project & Portfolio Management Tool | `list_in_scope_reporting_regulations`, `get_reporting_framework_requirements`, `get_esg_platform_capabilities`, `get_esg_data_coverage_by_metric`, `search_web`, `get_implementation_cost_estimates` |
| Q6 | Greenwashing enforcement cases versus our marketing claims; claims review checklist | Web, Documents, Carbon & ESG Reporting Platform, Knowledge Base / Policy Library | `search_greenwashing_enforcement_cases`, `search_web`, `get_document_contents`, `get_substantiation_evidence_for_claim`, `draft_claims_review_checklist`, `create_claims_review_ticket` ✎, `update_claim_review_status` ✎ |

## 49. Circular economy lead

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Which categories suit take-back, resale or repair, and what a pilot looks like | Returns Management System (RMS), Costing & Margin Tool, Transport Management System (TMS), Order Management System (OMS), Code Execution | `get_returns_condition_grading_by_category`, `get_resale_value_estimates_by_category`, `get_repair_cost_by_category`, `get_reverse_logistics_cost_by_category`, `run_analysis`, `draft_pilot_plan`, `create_circularity_pilot` ✎ |
| Q2 | Who can recycle poly-cotton blends at scale: capacity, cost, maturity | Web, Product Lifecycle Management (PLM) | `search_textile_recyclers`, `search_web`, `fetch_web_page`, `get_blended_fabric_volumes_by_category`, `search_peer_circularity_programmes` |
| Q3 | Cost, volume and carbon benefit of UK-wide in-store take-back | Store Operations Platform, Retail Property & Footfall System, Carbon & ESG Reporting Platform, Transport Management System (TMS), Code Execution | `get_store_footfall_and_sales_by_store`, `get_take_back_pilot_results`, `get_store_backroom_space_constraints`, `get_reverse_logistics_cost_by_category`, `calculate_take_back_programme_cost`, `calculate_avoided_emissions_from_reuse` |
| Q4 | Why aren't customers using our resale programme? | Customer Reviews & Feedback Platform, E-commerce Platform, Web Analytics Platform, Market Research Platform | `get_resale_programme_funnel_metrics`, `search_survey_responses_by_topic`, `get_customer_segment_participation`, `get_resale_listing_price_vs_new_price` |
| Q5 | Collected, reused, repaired, recycled this year and value recovered | Returns Management System (RMS), ERP (General Ledger), Executive KPI Scorecard | `get_circularity_volumes_by_outcome`, `get_recovered_value_by_channel`, `get_handling_cost_by_channel`, `get_circularity_targets`, `calculate_year_on_year_change` |
| Q6 | EPR fee exposure for textiles in UK, France, Netherlands and data readiness | Packaging Compliance & EPR System, Documents, Web, Product Lifecycle Management (PLM), Product Information Management (PIM), Code Execution | `get_document_contents`, `search_epr_scheme_fee_schedules`, `get_epr_reporting_requirements`, `get_available_epr_reporting_data_fields`, `calculate_epr_fee_exposure`, `search_web`, `draft_epr_preparation_plan`, `create_epr_preparation_task` ✎, `cancel_epr_preparation_task` ✎ |

## 50. Supply chain risk analyst

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Current world-event exposure by supplier, port and lane; weekly risk briefing | Risk Management System, Supplier Onboarding & Risk System, Container Visibility Platform, Demand Planning System, Web, Email & Calendar | `get_risk_events_feed`, `search_web`, `list_suppliers_in_affected_regions`, `list_shipments_through_affected_ports`, `get_revenue_dependency_by_supplier`, `calculate_time_to_impact`, `get_prior_week_risk_briefing`, `draft_weekly_risk_briefing`, `send_weekly_risk_briefing` ✎ |
| Q2 | Six-week southern Vietnam port closure: revenue, margin, stock-outs, mitigations | Supply Planning System (MRP/DRP), Inventory Management System (IMS), Purchase Order System, Container Visibility Platform, Freight Rate Management System, Costing & Margin Tool | `list_shipments_through_port`, `get_stock_cover_by_sku`, `get_open_purchase_orders_by_supplier_and_sku`, `get_in_transit_inventory_by_sku`, `get_sku_margin_and_revenue`, `get_alternate_port_options_and_rates`, `get_air_freight_rates`, `get_alternative_factory_capacity`, `calculate_port_closure_impact_scenarios`, `create_risk_scenario` ✎ |
| Q3 | Financial health of five sole-source suppliers | Supplier Onboarding & Risk System, Web, Spend Analytics Platform | `list_sole_source_suppliers`, `get_supplier_financial_filings`, `get_supplier_credit_scores`, `search_adverse_media_for_entity`, `calculate_supplier_failure_cost`, `create_supplier_risk_alert` ✎ |
| Q4 | Single points of failure and which to mitigate by dual sourcing, buffer or contract | Risk Management System, Supplier Relationship Management (SRM), Supply Planning System (MRP/DRP), Contract Management System, Costing & Margin Tool | `list_single_points_of_failure`, `get_supplier_concentration_by_category`, `get_contract_terms_for_supplier`, `get_dual_sourcing_cost_estimate`, `calculate_buffer_stock_cost`, `run_analysis`, `create_risk_register_entry` ✎ |
| Q5 | Which risks matter most over the next three years? | Web, Risk Management System, Trend & Market Intelligence Platform | `search_web`, `fetch_web_page`, `get_risk_register_entries`, `get_supplier_country_exposure`, `search_competitor_risk_disclosures` |
| Q6 | Real impacts of last month's disruption, wrong assumptions, update risk register | Risk Management System, Container Visibility Platform, Transport Management System (TMS), Purchase Order System | `get_disruption_incident_timeline`, `get_actual_delay_and_cost_impact`, `get_risk_register_entries`, `compare_risk_assumptions_to_actuals`, `update_risk_register_entry` ✎, `archive_risk_register_entry` ✎ |
| Q7 | Where will peak-season weather hit production? | Web, Supplier Onboarding & Risk System, Container Visibility Platform, Risk Management System | `get_weather_hazard_forecast`, `list_suppliers_in_affected_regions`, `get_port_exposure_by_region`, `get_historical_weather_disruption_lead_times`, `create_risk_alert_rule` ✎ |
| Q8 | Recent cyber incidents at sector suppliers or logistics providers and our exposed partners | Web, Supplier Onboarding & Risk System, Risk Management System | `search_cyber_incident_reports`, `search_web`, `list_critical_suppliers_and_logistics_providers`, `get_supplier_cyber_security_ratings`, `draft_supplier_security_questions`, `send_supplier_security_questionnaire` ✎ |

## Tool catalogue for this category

| Tool | System | R/W | One-line description |
|---|---|---|---|
| `archive_risk_register_entry` | Risk Management System | W | Archive a closed risk register entry |
| `block_purchase_orders_for_factory` | Purchase Order System | W | Place a hold on open POs for a factory |
| `calculate_abatement_cost_per_tonne` | Carbon & ESG Reporting Platform | R | Cost per tonne CO2e abated for a reduction lever |
| `calculate_avoided_emissions_from_reuse` | Carbon & ESG Reporting Platform | R | Emissions avoided by reuse or resale versus new production |
| `calculate_buffer_stock_cost` | Supply Planning System (MRP/DRP) | R | Holding cost of a proposed safety stock buffer |
| `calculate_emissions_trajectory_gap` | Carbon & ESG Reporting Platform | R | Gap between projected emissions and a target pathway |
| `calculate_epr_fee_exposure` | Packaging Compliance & EPR System | R | Estimated EPR fees by country and product category from volumes |
| `calculate_esg_data_gap_materiality` | Carbon & ESG Reporting Platform | R | Rank ESG data gaps by materiality and reporting impact |
| `calculate_factory_quality_risk_score` | Quality Management System (QMS) | R | Composite quality risk score per factory |
| `calculate_port_closure_impact_scenarios` | Supply Planning System (MRP/DRP) | R | Revenue, margin and stock-out impact for port closure durations |
| `calculate_recall_cost_estimate` | Incident & Recall Management System | R | All-in recall cost by scenario (logistics, refunds, comms, legal) |
| `calculate_regulation_impact_score` | Product Compliance & Regulatory Database | R | Score regulation impact by affected products and deadline |
| `calculate_scope2_reconciliation` | Carbon & ESG Reporting Platform | R | Year-on-year Scope 2 bridge (activity, factor, boundary, method) |
| `calculate_supplier_engagement_priority_score` | Carbon & ESG Reporting Platform | R | Priority score combining emissions, spend and readiness |
| `calculate_supplier_failure_cost` | Supplier Onboarding & Risk System | R | Estimated cost to the business of a supplier failure |
| `calculate_supplier_share_of_factory_capacity` | Supply Chain Due Diligence Platform | R | Our share of a factory's capacity, as a leverage indicator |
| `calculate_take_back_programme_cost` | Store Operations Platform | R | Cost and volume model for store take-back rollout |
| `calculate_time_to_impact` | Risk Management System | R | Estimated time before a risk event affects supply or sales |
| `calculate_volume_share_by_origin` | Customs & Trade Compliance System | R | Share of import volume by material origin region |
| `calculate_year_on_year_change` | Executive KPI Scorecard | R | Change versus prior year and target for a KPI |
| `cancel_epr_preparation_task` | Packaging Compliance & EPR System | W | Cancel an EPR readiness task |
| `compare_air_sea_freight_cost_and_emissions` | Freight Rate Management System | R | Cost and emissions of shifting volume between air and sea |
| `compare_audit_findings_across_audits` | Factory Audit Platform | R | Repeat and reopened findings across successive audits |
| `compare_label_to_requirements` | Product Compliance & Regulatory Database | R | Gap list between extracted label text and market requirements |
| `compare_product_specs_to_requirements` | Product Compliance & Regulatory Database | R | Flag products whose specs fail market requirements |
| `compare_requirements_across_markets` | Product Compliance & Regulatory Database | R | Side-by-side requirements across UK, EU, US and other markets |
| `compare_risk_assumptions_to_actuals` | Risk Management System | R | Compare register assumptions with observed disruption outcomes |
| `create_circularity_pilot` | Returns Management System (RMS) | W | Create a take-back, resale or repair pilot record |
| `create_claims_review_ticket` | Carbon & ESG Reporting Platform | W | Raise a review ticket for a sustainability claim |
| `create_compliance_issue` | Product Compliance & Regulatory Database | W | Log a compliance issue against a product |
| `create_compliance_task` | Product Compliance & Regulatory Database | W | Create a compliance action task for a regulation change |
| `create_corrective_action_plan` | Factory Audit Platform | W | Create a corrective action plan record against a factory |
| `create_due_diligence_case` | Supply Chain Due Diligence Platform | W | Open an ethical trade case for an allegation |
| `create_due_diligence_task` | Supply Chain Due Diligence Platform | W | Create and assign a due diligence or mapping task |
| `create_epr_preparation_task` | Packaging Compliance & EPR System | W | Create an EPR readiness task for a country |
| `create_esg_data_gap_task` | Carbon & ESG Reporting Platform | W | Create a task to close an ESG data gap |
| `create_inspection_booking` | Quality Management System (QMS) | W | Book an additional inspection at a factory |
| `create_quality_incident` | Quality Management System (QMS) | W | Open a quality incident record |
| `create_recall_case` | Incident & Recall Management System | W | Open a recall case for an incident |
| `create_retest_request` | Test Lab / LIMS | W | Create a retest request for a lot |
| `create_risk_alert_rule` | Risk Management System | W | Create an alert rule for regions or events |
| `create_risk_register_entry` | Risk Management System | W | Add a new entry to the risk register |
| `create_risk_scenario` | Risk Management System | W | Save a scenario analysis as a risk scenario record |
| `create_supplier_corrective_action_request` | Quality Management System (QMS) | W | Create a corrective action request record against a supplier |
| `create_supplier_engagement_plan` | Supplier Relationship Management (SRM) | W | Add suppliers to the emissions engagement programme |
| `create_supplier_risk_alert` | Supplier Onboarding & Risk System | W | Create a risk alert or watchlist entry for a supplier or factory |
| `create_sustainability_initiative` | Carbon & ESG Reporting Platform | W | Create a reduction initiative record |
| `create_test_request` | Test Lab / LIMS | W | Create a test booking request with a lab |
| `delete_draft_press_statement` | Incident & Recall Management System | W | Delete a draft press statement |
| `draft_claims_review_checklist` | Knowledge Base / Policy Library | R | Draft a sustainability claims review checklist |
| `draft_compliance_gap_list` | Supply Chain Due Diligence Platform | R | Draft gap list of evidence versus legal requirements |
| `draft_corrective_action_plan` | Factory Audit Platform | R | Draft corrective action plan with timelines and owners |
| `draft_customer_recall_notice` | Incident & Recall Management System | R | Draft customer-facing recall notice from template |
| `draft_epr_preparation_plan` | Packaging Compliance & EPR System | R | Draft six-month EPR readiness plan |
| `draft_escalation_note` | Supply Chain Due Diligence Platform | R | Draft internal escalation note for an ethical trade allegation |
| `draft_next_audit_focus_plan` | Factory Audit Platform | R | Draft focus areas for the next audit |
| `draft_pilot_plan` | Returns Management System (RMS) | R | Draft pilot design for take-back, resale or repair |
| `draft_press_statement` | Incident & Recall Management System | R | Draft press statement from recall facts |
| `draft_regulatory_notification` | Incident & Recall Management System | R | Draft regulator notification per country format |
| `draft_store_instructions` | Incident & Recall Management System | R | Draft store pull-and-quarantine instructions |
| `draft_supplier_chaser_email` | Supplier Portal | R | Draft chaser emails for missing or poor ESG data |
| `draft_supplier_corrective_action_request` | Quality Management System (QMS) | R | Draft supplier corrective action request |
| `draft_supplier_notification` | Quality Management System (QMS) | R | Draft notification to affected suppliers |
| `draft_supplier_security_questions` | Supplier Onboarding & Risk System | R | Draft cyber security questions for partners |
| `draft_weekly_risk_briefing` | Risk Management System | R | Draft weekly risk briefing document |
| `extract_label_text_from_images` | Documents | R | OCR text and symbols from label images |
| `fetch_web_page` | Web | R | Fetch and read a public web page |
| `get_actual_delay_and_cost_impact` | Transport Management System (TMS) | R | Observed delay and extra cost from a disruption |
| `get_air_freight_rates` | Freight Rate Management System | R | Current air freight rates by lane |
| `get_air_freight_volumes_and_emissions` | Transport Management System (TMS) | R | Air freight volumes and emissions by lane |
| `get_alternate_port_options_and_rates` | Freight Rate Management System | R | Alternative ports with rates and transit times |
| `get_alternative_factory_capacity` | Supplier Relationship Management (SRM) | R | Spare capacity at alternative factories |
| `get_assurance_findings` | Internal Audit System | R | Prior assurance and audit findings on ESG data |
| `get_assurance_requirements` | Knowledge Base / Policy Library | R | Assurance standard requirements for disclosures |
| `get_audit_findings_for_factory` | Factory Audit Platform | R | Findings by severity and status for a factory |
| `get_available_epr_reporting_data_fields` | Product Information Management (PIM) | R | Which EPR data fields we hold (weights, materials, recyclability) |
| `get_bill_of_materials_with_suppliers` | Product Lifecycle Management (PLM) | R | BOM with component and material suppliers |
| `get_blended_fabric_volumes_by_category` | Product Lifecycle Management (PLM) | R | Volumes of blended fabrics by category |
| `get_circularity_targets` | Executive KPI Scorecard | R | Circularity targets by channel |
| `get_circularity_volumes_by_outcome` | Returns Management System (RMS) | R | Units collected, reused, repaired, recycled |
| `get_contract_terms_for_supplier` | Contract Management System | R | Exit, volume and substitution terms for a supplier |
| `get_corrective_action_policy` | Knowledge Base / Policy Library | R | Policy on corrective action and order suspension |
| `get_corrective_action_status` | Factory Audit Platform | R | Status and ageing of corrective actions |
| `get_countries_where_batch_sold` | Order Management System (OMS) | R | Markets where a batch was sold |
| `get_country_risk_indices` | Supply Chain Due Diligence Platform | R | Forced labour and human rights indices by country |
| `get_customer_segment_participation` | Customer Data Platform (CDP) | R | Resale participation by customer segment |
| `get_data_request_deadline` | Carbon & ESG Reporting Platform | R | Supplier data request deadlines |
| `get_disruption_incident_timeline` | Risk Management System | R | Timeline of a past disruption |
| `get_document_contents` | Documents | R | Read an attached or shared file or archive |
| `get_dual_sourcing_cost_estimate` | Supplier Relationship Management (SRM) | R | Cost and lead time to qualify a second source |
| `get_due_diligence_policy_obligations` | Knowledge Base / Policy Library | R | Internal and legal obligations on allegations |
| `get_dye_lot_and_process_changes_for_lots` | Product Lifecycle Management (PLM) | R | Dye lot, mill, dye house and process changes |
| `get_emission_factor_data_quality` | Carbon & ESG Reporting Platform | R | Quality and source rating of an emission factor |
| `get_emission_factors_applied` | Carbon & ESG Reporting Platform | R | Emission factors used and their versions |
| `get_emission_factors_applied_to_transport` | Carbon & ESG Reporting Platform | R | Transport emission factors by mode and period |
| `get_emissions_by_product_category` | Carbon & ESG Reporting Platform | R | Emissions split by product category |
| `get_emissions_by_scope_and_category` | Carbon & ESG Reporting Platform | R | Emissions by scope and GHG category |
| `get_emissions_by_supplier` | Carbon & ESG Reporting Platform | R | Emissions attributed to each supplier, measured or estimated |
| `get_emissions_data_coverage` | Carbon & ESG Reporting Platform | R | Share of emissions backed by primary data |
| `get_emissions_data_quality_flags` | Carbon & ESG Reporting Platform | R | Measured versus estimated flags |
| `get_emissions_history_by_year` | Carbon & ESG Reporting Platform | R | Emissions by year against baseline |
| `get_emissions_reduction_targets` | Carbon & ESG Reporting Platform | R | Targets and baselines |
| `get_energy_consumption_by_site` | Retail Property & Footfall System | R | Energy use by site and period |
| `get_epr_reporting_requirements` | Packaging Compliance & EPR System | R | Required EPR data and deadlines by country |
| `get_esg_data_coverage_by_metric` | Carbon & ESG Reporting Platform | R | Data completeness by ESG metric |
| `get_esg_platform_capabilities` | Carbon & ESG Reporting Platform | R | Modules and reporting frameworks the platform supports |
| `get_evidence_inventory_for_due_diligence` | Supply Chain Due Diligence Platform | R | Evidence held per due diligence requirement |
| `get_factory_audit_scores` | Factory Audit Platform | R | Latest audit scores by factory |
| `get_factory_defect_inspection_results` | Quality Management System (QMS) | R | Inline and final inspection results by factory |
| `get_factory_defect_rate_trend` | Quality Management System (QMS) | R | Defect rate trend by factory |
| `get_factory_profile` | Supply Chain Due Diligence Platform | R | Factory ownership, location, workforce and products |
| `get_factory_risk_rating` | Supplier Onboarding & Risk System | R | Current risk rating for a factory |
| `get_handling_cost_by_channel` | ERP (General Ledger) | R | Handling cost by recovery channel |
| `get_historical_recall_costs` | Incident & Recall Management System | R | Costs of past recalls |
| `get_historical_weather_disruption_lead_times` | Container Visibility Platform | R | Past lead-time impact of weather events |
| `get_implementation_cost_estimates` | Project & Portfolio Management Tool | R | Cost and timeline of reporting system projects |
| `get_import_volumes_by_hs_code_and_origin` | Customs & Trade Compliance System | R | Import volumes by HS code and origin |
| `get_in_transit_inventory_by_sku` | Container Visibility Platform | R | In-transit quantities by SKU and ETA |
| `get_in_transit_stock_for_batch` | Track & Trace Platform | R | In-transit units for a batch |
| `get_incident_report` | Incident & Recall Management System | R | Incident details and customer report |
| `get_internal_incident_history` | Incident & Recall Management System | R | Past internal incidents by product type |
| `get_labelling_requirements_by_market` | Product Compliance & Regulatory Database | R | Label content rules by market |
| `get_legal_wording_guidelines` | Knowledge Base / Policy Library | R | Legal guidance on admissions and claims wording |
| `get_lot_acceptance_policy` | Knowledge Base / Policy Library | R | AQL and release policy for lots |
| `get_lot_test_results` | Test Lab / LIMS | R | Test results for a lot |
| `get_material_batch_traceability` | Product Lifecycle Management (PLM) | R | Upstream and downstream batch traceability |
| `get_material_batches_for_product` | Product Lifecycle Management (PLM) | R | Material batches used by a product |
| `get_material_cost_and_performance_data` | Costing & Margin Tool | R | Cost and performance of materials |
| `get_open_purchase_orders_by_factory` | Purchase Order System | R | Open POs and delivery dates by factory |
| `get_open_purchase_orders_by_material_origin` | Purchase Order System | R | Open POs by material origin |
| `get_open_purchase_orders_by_supplier_and_sku` | Purchase Order System | R | Open POs by supplier and SKU |
| `get_planned_reduction_initiatives` | Carbon & ESG Reporting Platform | R | Planned initiatives and expected savings |
| `get_port_exposure_by_region` | Container Visibility Platform | R | Port volumes by region |
| `get_prior_week_risk_briefing` | Risk Management System | R | Last week's risk briefing for comparison |
| `get_product_batch_and_factory_for_sku` | Product Lifecycle Management (PLM) | R | Batches, factory and production dates for a SKU |
| `get_product_specification_tolerances` | Product Lifecycle Management (PLM) | R | Spec tolerances for a product |
| `get_product_specifications` | Product Lifecycle Management (PLM) | R | Product specification and materials |
| `get_production_lot_details` | Quality Management System (QMS) | R | Lot, factory and production details |
| `get_recall_communication_templates` | Knowledge Base / Policy Library | R | Approved recall communication templates |
| `get_recall_vs_withdrawal_criteria` | Knowledge Base / Policy Library | R | Criteria separating recall from withdrawal |
| `get_recovered_value_by_channel` | ERP (General Ledger) | R | Value recovered by channel |
| `get_recycled_material_cost_premium` | Costing & Margin Tool | R | Cost premium of recycled versus virgin materials |
| `get_regulation_deadlines` | Product Compliance & Regulatory Database | R | Effective dates and transitional periods |
| `get_regulatory_notification_requirements_by_country` | Product Compliance & Regulatory Database | R | Who to notify, in what format and by when |
| `get_regulatory_reporting_obligations` | Product Compliance & Regulatory Database | R | Duty to report test failures to regulators |
| `get_regulatory_requirements_by_market` | Product Compliance & Regulatory Database | R | Requirements for a product type in a market |
| `get_repair_cost_by_category` | Costing & Margin Tool | R | Repair cost by category |
| `get_reporting_framework_requirements` | Knowledge Base / Policy Library | R | Disclosure requirements by framework |
| `get_resale_listing_price_vs_new_price` | E-commerce Platform | R | Resale prices relative to new |
| `get_resale_programme_funnel_metrics` | Web Analytics Platform | R | Funnel metrics for the resale programme |
| `get_resale_value_estimates_by_category` | Costing & Margin Tool | R | Expected resale value by category |
| `get_responsible_exit_policy` | Knowledge Base / Policy Library | R | Responsible exit policy and worker protection steps |
| `get_returns_by_reason_code` | Returns Management System (RMS) | R | Returns by reason code and product |
| `get_returns_condition_grading_by_category` | Returns Management System (RMS) | R | Condition grades on return by category |
| `get_revenue_dependency_by_supplier` | Demand Planning System | R | Revenue dependent on each supplier |
| `get_reverse_logistics_cost_by_category` | Transport Management System (TMS) | R | Reverse logistics cost by category |
| `get_risk_events_feed` | Risk Management System | R | Current monitored risk events |
| `get_risk_register_entries` | Risk Management System | R | Risk register entries and assumptions |
| `get_scope2_emissions_by_period` | Carbon & ESG Reporting Platform | R | Scope 2 by period and method |
| `get_scope2_method_and_boundary_changes` | Carbon & ESG Reporting Platform | R | Methodology and boundary change log |
| `get_shipments_by_lane_and_mode` | Transport Management System (TMS) | R | Shipments by lane and mode |
| `get_shipped_units_by_lot` | Order Management System (OMS) | R | Units shipped and sold by lot |
| `get_sku_margin_and_revenue` | Costing & Margin Tool | R | Revenue and margin by SKU |
| `get_spend_by_supplier` | Spend Analytics Platform | R | Spend by supplier and category |
| `get_stock_by_location_for_batch` | Inventory Management System (IMS) | R | Stock by store, DC and location for a batch |
| `get_stock_cover_by_sku` | Inventory Management System (IMS) | R | Stock cover in weeks by SKU |
| `get_store_backroom_space_constraints` | Store Operations Platform | R | Back-of-house space by store |
| `get_store_footfall_and_sales_by_store` | Retail Property & Footfall System | R | Footfall and sales by store |
| `get_submission_data_quality_scores` | Carbon & ESG Reporting Platform | R | Quality score of supplier submissions |
| `get_substance_list_matches_for_materials` | Product Compliance & Regulatory Database | R | Materials matching restricted or candidate lists |
| `get_substantiation_evidence_for_claim` | Carbon & ESG Reporting Platform | R | Evidence held for a sustainability claim |
| `get_supplier_base_profile_by_country` | Supplier Portal | R | Supplier base profile by country and tier |
| `get_supplier_code_of_conduct_clauses` | Knowledge Base / Policy Library | R | Wage and hours clauses in our code of conduct |
| `get_supplier_concentration_by_category` | Supplier Relationship Management (SRM) | R | Concentration by category |
| `get_supplier_country_exposure` | Supplier Onboarding & Risk System | R | Supplier exposure by country |
| `get_supplier_credit_scores` | Supplier Onboarding & Risk System | R | Credit scores and trends |
| `get_supplier_cyber_security_ratings` | Supplier Onboarding & Risk System | R | External cyber security ratings |
| `get_supplier_data_evidence_status` | Supplier Portal | R | Evidence status for supplier-supplied data |
| `get_supplier_emissions_commitments` | Supplier Portal | R | Supplier reduction commitments |
| `get_supplier_engagement_status` | Supplier Relationship Management (SRM) | R | Engagement history on emissions |
| `get_supplier_financial_filings` | Supplier Onboarding & Risk System | R | Filed accounts and key ratios |
| `get_supplier_renewable_energy_status` | Supplier Portal | R | Renewable electricity use |
| `get_supplier_risk_alerts` | Supplier Onboarding & Risk System | R | Active risk alerts per supplier |
| `get_supplier_risk_evidence` | Supply Chain Due Diligence Platform | R | Evidence behind each risk rating |
| `get_supplier_science_based_target_status` | Carbon & ESG Reporting Platform | R | SBTi commitment status |
| `get_supplier_sub_tier_relationships` | Supply Chain Due Diligence Platform | R | Mill and sub-tier links to our suppliers |
| `get_supply_chain_map_for_product` | Supply Chain Due Diligence Platform | R | Mapped tiers for a product |
| `get_supply_chain_mapping_gaps` | Supply Chain Due Diligence Platform | R | Unmapped tiers by region and product |
| `get_take_back_pilot_results` | Store Operations Platform | R | Results of take-back pilots |
| `get_test_report_details` | Test Lab / LIMS | R | Full test report |
| `get_testing_cost_and_lead_time` | Test Lab / LIMS | R | Cost and turnaround of tests |
| `get_transport_emissions_intensity_trend` | Carbon & ESG Reporting Platform | R | Intensity trend by mode and lane |
| `get_unit_cost_and_retail_price` | Costing & Margin Tool | R | Unit cost and price by SKU |
| `get_units_sold_by_batch` | Order Management System (OMS) | R | Units sold by batch and channel |
| `get_weather_hazard_forecast` | Web | R | Seasonal and event weather hazard forecasts |
| `get_worker_grievance_records` | Supply Chain Due Diligence Platform | R | Grievance hotline and worker voice records |
| `list_audit_reports_for_factory` | Factory Audit Platform | R | Audit reports for a factory |
| `list_critical_suppliers_and_logistics_providers` | Supplier Onboarding & Risk System | R | Suppliers and logistics providers by criticality |
| `list_factory_quality_scorecards` | Quality Management System (QMS) | R | Quality scorecards by factory |
| `list_in_scope_reporting_regulations` | Carbon & ESG Reporting Platform | R | Reporting rules applicable to us |
| `list_overdue_critical_findings` | Factory Audit Platform | R | Overdue critical findings by factory |
| `list_products_by_origin_country_and_material` | Product Lifecycle Management (PLM) | R | Products by material and origin |
| `list_products_by_regulated_category` | Product Lifecycle Management (PLM) | R | Products by regulated category |
| `list_products_using_component` | Product Lifecycle Management (PLM) | R | Products using the same component |
| `list_products_using_material` | Product Lifecycle Management (PLM) | R | Products using a material or supplier lot |
| `list_products_using_substance` | Product Lifecycle Management (PLM) | R | Products containing a substance |
| `list_shipments_through_affected_ports` | Container Visibility Platform | R | Shipments routing through affected ports |
| `list_shipments_through_port` | Container Visibility Platform | R | Shipments routing through a port |
| `list_single_points_of_failure` | Risk Management System | R | Single-source and single-route dependencies |
| `list_sole_source_suppliers` | Supplier Onboarding & Risk System | R | Sole-source suppliers |
| `list_supplier_esg_submissions` | Supplier Portal | R | ESG submissions by supplier and status |
| `list_suppliers_by_country_and_sector` | Supplier Onboarding & Risk System | R | Suppliers by country and sector |
| `list_suppliers_by_forced_labour_risk` | Supply Chain Due Diligence Platform | R | Suppliers ranked by forced labour risk |
| `list_suppliers_in_affected_regions` | Supplier Onboarding & Risk System | R | Suppliers in affected regions |
| `list_upcoming_regulatory_changes` | Product Compliance & Regulatory Database | R | Pending regulation changes |
| `remove_supplier_from_engagement_programme` | Supplier Relationship Management (SRM) | W | Remove a supplier from the engagement programme |
| `run_analysis` | Code Execution | R | Run analysis, join datasets or build a chart |
| `search_adverse_media_for_entity` | Supply Chain Due Diligence Platform | R | Adverse media on a named entity |
| `search_alternative_cotton_sources` | Web | R | Alternative cotton origins and suppliers |
| `search_alternative_materials` | Product Compliance & Regulatory Database | R | Compliant alternative materials |
| `search_competitor_risk_disclosures` | Trend & Market Intelligence Platform | R | Competitor risk disclosures and actions |
| `search_complaints_by_defect_type` | Customer Service Platform | R | Complaints by defect type |
| `search_cyber_incident_reports` | Web | R | Public cyber incident reports |
| `search_due_diligence_regulations` | Web | R | Forced labour and due diligence laws by jurisdiction |
| `search_emission_factors_by_material` | Carbon & ESG Reporting Platform | R | Emission factors by material |
| `search_epr_scheme_fee_schedules` | Packaging Compliance & EPR System | R | EPR fee schedules by scheme |
| `search_greenwashing_enforcement_cases` | Web | R | Greenwashing rulings and enforcement |
| `search_import_detention_orders` | Web | R | Customs detention orders and findings |
| `search_labour_law_by_state` | Web | R | State wage and overtime rules |
| `search_ngo_and_union_reports` | Web | R | NGO and union reports |
| `search_notified_bodies` | Web | R | Notified bodies and approved bodies |
| `search_peer_circularity_programmes` | Web | R | Peer circularity programmes |
| `search_peer_sustainability_disclosures` | Web | R | Peer sustainability disclosures |
| `search_recall_notices` | Web | R | Public recall databases |
| `search_regulations_by_product_type` | Product Compliance & Regulatory Database | R | Regulations for a product type |
| `search_restricted_substance_lists` | Product Compliance & Regulatory Database | R | Restricted and candidate substance lists |
| `search_review_text_by_topic` | Customer Reviews & Feedback Platform | R | Review text for a topic |
| `search_survey_responses_by_topic` | Market Research Platform | R | Survey responses on a topic |
| `search_test_results_by_failure_mode` | Test Lab / LIMS | R | Test results by failure mode |
| `search_textile_recyclers` | Web | R | Textile recyclers and capacity |
| `search_web` | Web | R | General web search |
| `send_corrective_action_reminder` | Factory Audit Platform | W | Send an overdue corrective action reminder to a factory |
| `send_escalation_note` | Email & Calendar | W | Send an escalation note to named recipients |
| `send_regulatory_notification` | Incident & Recall Management System | W | Submit a regulator notification for a recall or withdrawal |
| `send_store_instructions` | Incident & Recall Management System | W | Publish pull-and-quarantine instructions to stores |
| `send_supplier_chaser_email` | Email & Calendar | W | Send chaser emails to suppliers |
| `send_supplier_corrective_action_request` | Quality Management System (QMS) | W | Send a corrective action request to the supplier |
| `send_supplier_engagement_invitation` | Supplier Relationship Management (SRM) | W | Send an emissions engagement invitation to a supplier |
| `send_supplier_notification` | Quality Management System (QMS) | W | Send a quality notification to a supplier |
| `send_supplier_security_questionnaire` | Supplier Onboarding & Risk System | W | Send a cyber security questionnaire to a supplier |
| `send_weekly_risk_briefing` | Email & Calendar | W | Send the weekly risk briefing to a distribution list |
| `update_audit_finding_status` | Factory Audit Platform | W | Change the status or classification of an audit finding |
| `update_claim_review_status` | Carbon & ESG Reporting Platform | W | Mark a claim as approved, amend or drop |
| `update_compliance_issue_status` | Product Compliance & Regulatory Database | W | Change the status of a logged compliance issue |
| `update_corrective_action_due_date` | Factory Audit Platform | W | Change the due date of a corrective action |
| `update_inventory_hold_status` | Inventory Management System (IMS) | W | Place or release stock holds |
| `update_lot_disposition` | Quality Management System (QMS) | W | Set release, rework or reject |
| `update_material_compliance_status` | Product Lifecycle Management (PLM) | W | Flag a material as under review or restricted |
| `update_recall_case_cost_estimate` | Incident & Recall Management System | W | Record or change the cost estimate on a recall case |
| `update_risk_register_entry` | Risk Management System | W | Update a risk register entry |
| `update_transport_emission_factor_for_lane` | Carbon & ESG Reporting Platform | W | Correct the emission factor applied to a lane or mode |
