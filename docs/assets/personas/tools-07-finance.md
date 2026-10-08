# Systems and MCP tools · 07 Finance

Maps every Finance question to the enterprise systems an agent must reach and the MCP tool methods it would call.
Tool names are entity-scoped and shared across all nine categories for benchmark consistency.
Personas and question numbers follow questions-07-finance.md exactly.

**Legend:** tools are listed in likely call order. Read tools use get_/list_/search_/calculate_/compare_/run_ ; write tools are marked ✎. `draft_` tools produce a document and are not writes.

---

## 61. Financial controller

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Decompose £1.8m September operating profit miss; draft board-credible commentary | ERP (General Ledger), Budgeting & Forecasting Tool, Consolidation & Reporting Tool, Cost Allocation Tool, Documents | `get_pl_extract_from_document`, `get_budget_vs_actual_variance`, `get_variance_drivers`, `list_one_off_journals`, `list_timing_items`, `run_analysis`, `draft_management_accounts_commentary`, `create_close_task` ✎ |
| Q2 | Trace £340k UK–Poland intercompany difference by transaction, currency, posting date | ERP (General Ledger), Consolidation & Reporting Tool, FX & Hedging Platform | `get_intercompany_balances`, `list_intercompany_transactions`, `search_unmatched_intercompany_items`, `get_fx_rates_for_period`, `draft_clearing_journals`, `create_journal_entry` ✎, `delete_draft_journal` ✎, `submit_journal_for_approval` ✎ |
| Q3 | Accounting for annual-volume supplier rebates: peer practice and audit challenge | Accounts Payable System, Knowledge Base / Policy Library, Web | `search_accounting_standards_guidance`, `search_peer_annual_reports`, `search_accounting_policy`, `list_supplier_rebate_agreements`, `get_rebate_accrual_history` |
| Q4 | What is still open at close: accruals and reconciliations? | Consolidation & Reporting Tool, ERP (General Ledger) | `list_open_close_tasks`, `list_open_accruals`, `list_unreconciled_accounts`, `send_close_task_reminder` ✎, `reassign_reconciliation` ✎ |
| Q5 | Freight cost in P&L £210k off logistics system: why? | ERP (General Ledger), Transport Management System (TMS), Accounts Payable System | `get_freight_cost_by_ledger_account`, `get_freight_cost_from_tms`, `compare_freight_ledger_to_tms`, `list_unaccrued_freight_invoices`, `list_miscoded_freight_invoices`, `update_invoice_gl_coding` ✎, `create_accrual_journal` ✎ |

## 62. FP&A analyst

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Explain 1.4-point gross margin fall by driver, structural or temporary, with actions | Costing & Margin Tool, Merchandise Financial Planning, Tax & Duty System, FX & Hedging Platform, Budgeting & Forecasting Tool | `get_gross_margin_bridge`, `get_markdown_and_shrink_rates`, `get_duty_cost_trend`, `get_fx_impact_on_cogs`, `get_full_year_outlook`, `list_margin_recovery_actions`, `run_analysis`, `create_cost_saving_initiative` ✎ |
| Q2 | Full-year revenue, margin, EBIT forecast: base, downside, upside, levers, CFO page | Budgeting & Forecasting Tool, Demand Planning System, Freight Rate Management System, Documents, Code Execution, Email & Calendar | `get_latest_forecast_version`, `get_forecast_drivers_and_assumptions`, `get_demand_forecast`, `get_freight_rate_forecast`, `create_forecast_scenario` ✎, `calculate_scenario_outcomes`, `list_mitigation_levers`, `delete_forecast_scenario` ✎, `send_email_to_recipient` ✎ |
| Q3 | Return on £12m Northampton automation: payback, IRR, risks, volume sensitivity | Project & Portfolio Management Tool, Demand Planning System, Cost Allocation Tool, Budgeting & Forecasting Tool | `get_capex_proposal`, `get_site_volume_forecast`, `get_site_operating_costs`, `calculate_investment_returns`, `calculate_sensitivity_analysis`, `submit_capex_case_for_review` ✎ |
| Q4 | How do we compare with listed peers on margin, growth, inventory turns? | Web, Consolidation & Reporting Tool | `search_peer_annual_reports`, `get_peer_financial_benchmarks`, `get_company_financial_kpis`, `run_analysis` |
| Q5 | Effect of 10% sterling fall against dollar on COGS, net of hedges | FX & Hedging Platform, ERP (General Ledger), Pricing & Promotion Engine, Budgeting & Forecasting Tool | `get_usd_cogs_exposure`, `get_fx_hedge_book`, `get_hedge_cover_ratio`, `calculate_fx_sensitivity`, `calculate_price_increase_to_offset_cost`, `create_forecast_scenario` ✎ |
| Q6 | Why did the July forecast miss Q3 actuals by 4%? | Budgeting & Forecasting Tool, Consolidation & Reporting Tool | `get_latest_forecast_version`, `compare_forecast_to_actuals`, `get_forecast_accuracy_by_line`, `get_forecast_drivers_and_assumptions` |
| Q7 | Which cost-saving initiatives to prioritise, with confidence and dependencies | Project & Portfolio Management Tool, Budgeting & Forecasting Tool | `list_cost_saving_initiatives`, `get_initiative_confidence_and_dependencies`, `run_analysis`, `update_initiative_status` ✎, `archive_cost_saving_initiative` ✎ |
| Q8 | Summarise this month for the leadership team | Consolidation & Reporting Tool, Risk Management System, Documents, Email & Calendar | `get_monthly_performance_summary`, `get_budget_vs_actual_variance`, `list_key_risks_and_opportunities`, `draft_leadership_summary`, `send_email_to_recipient` ✎ |

## 63. Supply chain finance analyst

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Decompose 7% landed cost rise on top 100 SKUs; controllable; margin flow-through | Landed Cost Calculator, Purchase Order System, FX & Hedging Platform, Tax & Duty System, Budgeting & Forecasting Tool, Supplier Portal | `list_top_skus_by_sales`, `get_landed_cost_by_sku`, `get_landed_cost_history`, `get_supplier_price_changes`, `get_freight_cost_by_sku`, `get_duty_and_insurance_by_sku`, `get_margin_phasing_forecast`, `send_supplier_price_query` ✎ |
| Q2 | Cost to serve by channel from FY26 actuals; unprofitable segments; free-returns test | Cost Allocation Tool, Costing & Margin Tool, Transport Management System (TMS), Returns Management System (RMS), Code Execution | `get_cost_to_serve_by_channel`, `get_warehouse_cost_pools`, `get_outbound_transport_cost_by_channel`, `get_returns_cost_by_channel`, `get_packaging_cost_by_channel`, `get_channel_revenue_and_margin`, `calculate_cost_to_serve_scenario`, `create_cost_allocation_scenario` ✎, `update_cost_allocation_driver` ✎ |
| Q3 | Cheaper to serve northern stores from main DC or regional cross-dock; peak effect | Network Design Tool, Transport Management System (TMS), Labour Management System (LMS), Inventory Management System (IMS) | `get_store_delivery_cost_by_route`, `get_dc_handling_rates`, `get_cross_dock_handling_rates`, `get_inventory_holding_cost`, `get_peak_volume_profile`, `calculate_network_cost_comparison` |
| Q4 | Are our logistics costs high versus retail peers; benchmark comparability | Cost Allocation Tool, Web | `get_logistics_cost_by_line`, `search_logistics_benchmarks`, `compare_cost_to_benchmark` |
| Q5 | Cost impact of switching main carrier and 3PL, including one-off transition costs | Freight Rate Management System, Sourcing / RFx Platform, Transport Management System (TMS), Code Execution | `get_carrier_contract_rates`, `get_carrier_bid_rates`, `get_3pl_proposal_costs`, `get_shipment_volumes_by_lane`, `calculate_transition_payback`, `create_rfx_event` ✎ |
| Q6 | Why did activity-based cost per e-commerce order rise from £6.20 to £7.10? | Cost Allocation Tool, E-commerce Platform | `get_ecom_cost_per_order`, `get_ecom_order_volumes_and_mix`, `run_rate_volume_mix_decomposition` |
| Q7 | Which small SKUs cost more to serve than they earn? | Cost Allocation Tool, Costing & Margin Tool, Range Planning & Assortment Tool | `get_sku_cost_to_serve`, `get_sku_sales_and_margin`, `list_loss_making_skus`, `create_sku_review_task` ✎ |
| Q8 | P&L if 20% of production moves nearshore | Costing & Margin Tool, Purchase Order System, Budgeting & Forecasting Tool, Merchandise Financial Planning | `get_production_volumes_by_origin`, `get_nearshore_cost_assumptions`, `get_latest_forecast_version`, `calculate_pl_scenario`, `calculate_transition_payback`, `create_forecast_scenario` ✎ |

## 65. AR/credit controller

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Hartley & Reed financial health and payment behaviour; change credit limit? | Accounts Receivable System, Web | `get_customer_account_summary`, `get_customer_payment_history`, `search_company_filings`, `get_credit_agency_report`, `search_company_news`, `calculate_credit_limit_recommendation`, `get_credit_insurance_cover`, `update_customer_credit_limit` ✎ |
| Q2 | £480k disputed invoice: reconstruct facts from dispute pack, position, draft response | Documents, Accounts Receivable System, Order Management System (OMS), Contract Management System, Email & Calendar | `get_dispute_documents`, `get_sales_order_and_invoice`, `get_delivery_notes_for_invoice`, `get_agreed_price_list`, `search_email_thread`, `draft_dispute_response`, `update_invoice_dispute_status` ✎, `send_email_to_recipient` ✎ |
| Q3 | Eight-week collections forecast by week; bad-debt provision; riskiest customers | Accounts Receivable System, ERP (General Ledger) | `get_open_receivables_ledger`, `get_historical_collection_patterns`, `calculate_collections_forecast`, `get_bad_debt_provision`, `calculate_expected_credit_loss`, `create_journal_entry` ✎ |
| Q4 | Who is overdue and getting worse? | Accounts Receivable System | `list_overdue_invoices`, `get_overdue_trend_by_customer`, `get_customer_exposure_summary`, `send_payment_reminder` ✎ |
| Q5 | Customer 75 days overdue: stop shipments? Legal steps and exposure | Accounts Receivable System, Order Management System (OMS), Contract Management System, Knowledge Base / Policy Library, Web | `get_customer_account_summary`, `get_open_orders_for_customer`, `get_credit_hold_policy`, `get_contract_payment_terms`, `search_debt_recovery_guidance`, `update_customer_credit_hold` ✎, `release_order_hold` ✎ |

## 66. Treasury / FX analyst

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Net currency exposure by month for 12 months; P&L at 5% and 10% moves | FX & Hedging Platform, Treasury Management System, ERP (General Ledger) | `get_forecast_cash_flows_by_currency`, `get_currency_exposure_forecast`, `get_hedge_cover_ratio`, `calculate_fx_sensitivity`, `calculate_hedge_gap`, `submit_hedge_trade_for_approval` ✎ |
| Q2 | Sterling outlook versus dollar and euro: consensus, forecast accuracy, risks | Web | `search_fx_consensus_forecasts`, `get_fx_forecast_accuracy_history`, `search_fx_market_news` |
| Q3 | Raise dollar hedge ratio from 60% to 80%? Cost, protection, instruments | FX & Hedging Platform, Treasury Management System, Knowledge Base / Policy Library | `get_hedging_policy`, `get_hedge_cover_ratio`, `get_hedge_instrument_pricing`, `calculate_hedge_scenarios`, `get_currency_exposure_forecast`, `submit_hedge_trade_for_approval` ✎ |
| Q4 | Why is the FX gain/loss line £1.1m off budget? | ERP (General Ledger), FX & Hedging Platform, Budgeting & Forecasting Tool | `get_fx_gain_loss_by_account`, `get_fx_budget_assumptions`, `get_realised_vs_unrealised_fx`, `get_hedge_effectiveness_report`, `create_journal_entry` ✎ |
| Q5 | Liquidity headroom over next 13 weeks and pinch points | Treasury Management System, Accounts Payable System, Accounts Receivable System | `get_13_week_cash_forecast`, `get_bank_balances`, `get_debt_facilities_and_headroom`, `update_payment_run_date` ✎, `cancel_payment_run` ✎ |

## 67. Tax and duty specialist

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Transfer pricing rules and documentation for UK, Polish, HK sourcing entities; exposure | Tax & Duty System, ERP (General Ledger), Knowledge Base / Policy Library, Web | `search_transfer_pricing_rules`, `search_tax_authority_guidance`, `get_transfer_pricing_policy`, `get_intercompany_sourcing_margins`, `list_transfer_pricing_documentation`, `calculate_transfer_pricing_exposure`, `create_tax_compliance_task` ✎ |
| Q2 | Effect of 10% Turkey tariff increase on duty cost; mitigation | Tax & Duty System, Customs & Trade Compliance System, Web | `get_import_volumes_by_origin`, `get_current_duty_rates`, `search_tariff_announcements`, `calculate_duty_impact_scenario`, `search_preferential_origin_rules` |
| Q3 | Latest EU and UK low-value parcel VAT and customs rules; online impact | Web, E-commerce Platform, Tax & Duty System | `search_vat_customs_regulations`, `get_parcel_volumes_by_destination`, `calculate_low_value_parcel_impact` |
| Q4 | Could drawback, first-sale or bonded warehouse cut duty; risk and saving | Tax & Duty System, Customs & Trade Compliance System, Warehouse Management System (WMS), Web | `get_duty_paid_by_entry`, `get_first_sale_candidates`, `get_bonded_warehouse_volumes`, `search_duty_relief_rules`, `calculate_duty_saving_estimate`, `create_duty_drawback_claim` ✎ |
| Q5 | Q3 VAT return £600k off expectation: which transactions? | Tax & Duty System, ERP (General Ledger) | `get_vat_return_summary`, `compare_vat_return_to_expectation`, `list_vat_transactions_by_entity`, `update_vat_code_on_transaction` ✎ |
| Q6 | Tax incentives for DC automation or renewable energy | Web, Fixed Asset Register, Tax & Duty System | `search_tax_incentives`, `get_planned_capex_by_type`, `calculate_incentive_value` |
| Q7 | Customs value treatment of supplier retrospective price adjustments | Purchase Order System, Customs & Trade Compliance System, Web | `get_retrospective_price_adjustments`, `search_customs_valuation_rulings`, `list_affected_customs_declarations`, `submit_customs_declaration_amendment` ✎ |
| Q8 | Recent rulings relevant to our classification and valuation positions | Customs & Trade Compliance System, Web | `list_classification_positions`, `search_classification_rulings`, `search_customs_valuation_rulings`, `submit_binding_ruling_application` ✎ |

## 68. Internal auditor

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Anomaly-test a year of POs and payments; score; top-10 tests; audit report | Documents, Accounts Payable System, Code Execution, Internal Audit System | `get_po_and_payment_data`, `list_vendor_master_changes`, `get_approval_limits`, `run_anomaly_tests_on_payments`, `run_analysis`, `draft_audit_findings_report`, `create_audit_case` ✎, `block_vendor_for_payment` ✎ |
| Q2 | Are stock counts, valuations and provisions at three DCs reliable? | Internal Audit System, Inventory Management System (IMS), ERP (General Ledger) | `get_stock_count_results`, `get_inventory_valuation_by_site`, `get_dc_control_test_results`, `get_prior_audit_findings` |
| Q3 | What should we audit next year; scope; unaudited areas | Internal Audit System, Risk Management System | `get_audit_universe_and_coverage`, `get_enterprise_risk_register`, `get_prior_audit_findings`, `get_internal_audit_resource_plan`, `create_audit_engagement` ✎ |
| Q4 | Good-practice supplier master and bank detail controls; compare with ours | Web, Accounts Payable System, Knowledge Base / Policy Library | `search_audit_good_practice`, `get_vendor_master_controls`, `list_bank_detail_change_requests`, `create_audit_action` ✎ |
| Q5 | Leeds shrink tripled: theft or process error? | Loss Prevention & Incident System, Inventory Management System (IMS), Point of Sale (POS), Store Workforce Management, CCTV / Exception Reporting | `get_store_shrink_by_period`, `list_stock_adjustments_for_store`, `list_pos_exceptions`, `get_store_staff_schedules`, `search_cctv_incident_logs`, `correlate_shrink_signals`, `create_loss_prevention_case` ✎ |
| Q6 | Were last year's audit actions actually fixed? | Internal Audit System | `list_audit_actions`, `get_action_evidence`, `search_control_test_results`, `update_audit_action_status` ✎ |

## 69. Inventory accountant

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Inventory value up £3.4m while units fell: cost, FX, mix, adjustments | ERP (General Ledger), Costing & Margin Tool, Inventory Management System (IMS), FX & Hedging Platform | `get_inventory_value_movement`, `get_inventory_units_by_category`, `get_standard_cost_updates`, `list_inventory_adjustments`, `run_analysis`, `create_journal_entry` ✎, `submit_journal_for_approval` ✎ |
| Q2 | Slow-moving and obsolete stock provision needed, versus last year | Inventory Management System (IMS), Merchandise Financial Planning, Costing & Margin Tool, ERP (General Ledger) | `get_stock_ageing`, `get_sell_through_rates`, `get_expected_recovery_rates`, `calculate_provision_requirement`, `get_slow_moving_provision`, `create_journal_entry` ✎, `submit_journal_for_approval` ✎ |
| Q3 | Where will year-end shrink and write-offs land; what would reduce it | ERP (General Ledger), Loss Prevention & Incident System, Code Execution | `get_shrink_and_writeoff_history`, `get_store_shrink_by_period`, `calculate_year_end_shrink_forecast`, `create_cycle_count_task` ✎ |
| Q4 | Net realisable value rules for seasonal stock; our policy; audit documentation | Web, Knowledge Base / Policy Library | `search_ias2_nrv_guidance`, `get_provisioning_policy` |
| Q5 | WMS stock value differs from ledger by £1.2m: why? | Warehouse Management System (WMS), ERP (General Ledger) | `get_wms_stock_valuation`, `get_ledger_inventory_balance`, `compare_wms_to_ledger`, `reverse_inventory_adjustment` ✎, `create_journal_entry` ✎ |

## 70. CFO / finance director

| Q | Question (abridged) | Systems required | MCP tool methods |
|---|---|---|---|
| Q1 | Allocate next £50m capital across six options; compare risk and return; board paper | Project & Portfolio Management Tool, Budgeting & Forecasting Tool, Strategy & Board Reporting Tool, Documents, Code Execution | `get_capital_project_proposals`, `get_capital_budget_and_hurdle_rates`, `get_strategic_plan_assumptions`, `calculate_investment_returns`, `calculate_sensitivity_analysis`, `draft_board_paper`, `create_board_agenda_item` ✎, `cancel_capex_proposal` ✎ |
| Q2 | Downside and upside scenario effect on covenants, cash, dividends over 18 months | Treasury Management System, Budgeting & Forecasting Tool, Demand Planning System | `get_cash_flow_forecast_18_months`, `get_debt_facilities_and_covenants`, `get_dividend_policy_and_schedule`, `get_demand_scenarios`, `calculate_covenant_headroom`, `create_covenant_alert` ✎ |
| Q3 | Top three analyst questions on inventory and supply chain costs; strong answers | Web, Consolidation & Reporting Tool | `search_analyst_commentary`, `get_inventory_and_supply_chain_cost_kpis`, `get_guidance_and_outlook` |
| Q4 | What drives sector margin pressure; cyclical or permanent; peer actions | Web, Consolidation & Reporting Tool | `search_sector_margin_analysis`, `search_peer_annual_reports`, `get_gross_margin_bridge`, `get_peer_financial_benchmarks` |
| Q5 | What could break guidance: top risks, likelihood, impact | Risk Management System, Consolidation & Reporting Tool, Budgeting & Forecasting Tool | `get_guidance_and_outlook`, `get_guidance_risk_register`, `get_full_year_outlook`, `list_mitigation_levers`, `create_risk_register_entry` ✎ |
| Q6 | Effect of peers' supply chain investments on margins and working capital | Web | `search_peer_supply_chain_investments`, `search_peer_annual_reports`, `get_peer_financial_benchmarks` |

## Tool catalogue for this category

| Tool | System | R/W | One-line description |
|---|---|---|---|
| `archive_cost_saving_initiative` | Project & Portfolio Management Tool | W | Archives an initiative so it leaves the active list |
| `block_vendor_for_payment` | Accounts Payable System | W | Places a payment block on a vendor |
| `calculate_collections_forecast` | Accounts Receivable System | R | Expected weekly cash collections with range |
| `calculate_cost_to_serve_scenario` | Cost Allocation Tool | R | Cost to serve under a changed policy or allocation |
| `calculate_covenant_headroom` | Treasury Management System | R | Covenant headroom under scenarios |
| `calculate_credit_limit_recommendation` | Accounts Receivable System | R | Recommended credit limit from score and exposure |
| `calculate_duty_impact_scenario` | Tax & Duty System | R | Duty cost under a changed tariff |
| `calculate_duty_saving_estimate` | Tax & Duty System | R | Estimated duty saving by relief option |
| `calculate_expected_credit_loss` | Accounts Receivable System | R | Expected credit loss by ageing bucket or customer |
| `calculate_fx_sensitivity` | FX & Hedging Platform | R | P&L impact of an FX move against hedge cover |
| `calculate_hedge_gap` | FX & Hedging Platform | R | Under- or over-hedged position by currency and month |
| `calculate_hedge_scenarios` | FX & Hedging Platform | R | Cost and protection under alternative hedge ratios |
| `calculate_incentive_value` | Tax & Duty System | R | Value of eligible incentives on planned spend |
| `calculate_investment_returns` | Budgeting & Forecasting Tool | R | Payback, NPV and IRR for an investment case |
| `calculate_low_value_parcel_impact` | Tax & Duty System | R | VAT and duty impact on low-value parcels |
| `calculate_network_cost_comparison` | Network Design Tool | R | Compare cost of alternative fulfilment routes |
| `calculate_pl_scenario` | Budgeting & Forecasting Tool | R | Full P&L under a scenario with changed sourcing mix |
| `calculate_price_increase_to_offset_cost` | Pricing & Promotion Engine | R | Price rise needed to offset a cost increase |
| `calculate_provision_requirement` | Code Execution | R | Provision required under policy rules |
| `calculate_scenario_outcomes` | Budgeting & Forecasting Tool | R | Calculate P&L outcomes for a scenario |
| `calculate_sensitivity_analysis` | Budgeting & Forecasting Tool | R | Sensitivity of returns to chosen variables |
| `calculate_transfer_pricing_exposure` | Tax & Duty System | R | Tax exposure if a mark-up is challenged |
| `calculate_transition_payback` | Code Execution | R | Payback including one-off transition costs |
| `calculate_year_end_shrink_forecast` | Code Execution | R | Year-end shrink projection with range |
| `cancel_capex_proposal` | Project & Portfolio Management Tool | W | Withdraws a proposal from the capital queue |
| `cancel_payment_run` | Accounts Payable System | W | Cancels a scheduled payment run |
| `compare_cost_to_benchmark` | Code Execution | R | Compare own cost lines to benchmark values |
| `compare_forecast_to_actuals` | Budgeting & Forecasting Tool | R | Compare a forecast version to actuals |
| `compare_freight_ledger_to_tms` | Transport Management System (TMS) | R | Reconcile freight ledger cost to TMS shipment cost |
| `compare_vat_return_to_expectation` | Tax & Duty System | R | Variance of VAT return to expectation by driver |
| `compare_wms_to_ledger` | ERP (General Ledger) | R | Reconcile WMS stock value to the ledger |
| `correlate_shrink_signals` | Code Execution | R | Correlate adjustments, exceptions and rosters |
| `create_accrual_journal` | ERP (General Ledger) | W | Creates an accrual journal with auto-reversal for a period |
| `create_audit_action` | Internal Audit System | W | Logs a remediation action with owner and due date |
| `create_audit_case` | Internal Audit System | W | Opens an investigation case for a finding |
| `create_audit_engagement` | Internal Audit System | W | Adds an engagement with scope to the audit plan |
| `create_board_agenda_item` | Strategy & Board Reporting Tool | W | Adds a paper to a board meeting agenda |
| `create_close_task` | Consolidation & Reporting Tool | W | Adds a task with owner and due date to the month-end close checklist |
| `create_cost_allocation_scenario` | Cost Allocation Tool | W | Saves a named allocation scenario with changed assumptions |
| `create_cost_saving_initiative` | Project & Portfolio Management Tool | W | Adds a new initiative with owner and estimated saving to the tracker |
| `create_covenant_alert` | Treasury Management System | W | Creates a threshold alert on covenant headroom |
| `create_cycle_count_task` | Inventory Management System (IMS) | W | Schedules a cycle count for a category or location |
| `create_duty_drawback_claim` | Customs & Trade Compliance System | W | Creates a draft duty drawback claim |
| `create_forecast_scenario` | Budgeting & Forecasting Tool | W | Create a named scenario with changed assumptions |
| `create_journal_entry` | ERP (General Ledger) | W | Creates a draft journal entry in the ledger, unposted |
| `create_loss_prevention_case` | Loss Prevention & Incident System | W | Opens a case for a store loss investigation |
| `create_rfx_event` | Sourcing / RFx Platform | W | Creates a tender event with invited bidders |
| `create_risk_register_entry` | Risk Management System | W | Adds a risk with owner and rating to the register |
| `create_sku_review_task` | Range Planning & Assortment Tool | W | Flags SKUs for range review with a reason and owner |
| `create_tax_compliance_task` | Tax & Duty System | W | Creates a compliance task with owner and due date |
| `delete_draft_journal` | ERP (General Ledger) | W | Deletes an unposted draft journal |
| `delete_forecast_scenario` | Budgeting & Forecasting Tool | W | Deletes a saved forecast scenario |
| `draft_audit_findings_report` | Documents | R | Draft findings in audit report format |
| `draft_board_paper` | Documents | R | Draft a board paper outline |
| `draft_clearing_journals` | ERP (General Ledger) | R | Draft journals to clear intercompany differences |
| `draft_dispute_response` | Documents | R | Draft a reply to a customer dispute |
| `draft_leadership_summary` | Documents | R | Draft a leadership summary document |
| `draft_management_accounts_commentary` | Documents | R | Draft variance commentary for the management accounts |
| `get_13_week_cash_forecast` | Treasury Management System | R | 13-week cash forecast with drivers |
| `get_3pl_proposal_costs` | Sourcing / RFx Platform | R | 3PL proposal pricing and transition cost items |
| `get_action_evidence` | Internal Audit System | R | Closure evidence attached to audit actions |
| `get_agreed_price_list` | Contract Management System | R | Agreed customer price list and terms |
| `get_approval_limits` | Knowledge Base / Policy Library | R | Approval limits and delegation of authority |
| `get_audit_universe_and_coverage` | Internal Audit System | R | Audit universe with last audit dates |
| `get_bad_debt_provision` | Accounts Receivable System | R | Current bad-debt provision and methodology |
| `get_bank_balances` | Treasury Management System | R | Current bank balances |
| `get_bonded_warehouse_volumes` | Warehouse Management System (WMS) | R | Stock suitable for bonded storage |
| `get_budget_vs_actual_variance` | Budgeting & Forecasting Tool | R | Actual versus budget by entity, category and period |
| `get_capex_proposal` | Project & Portfolio Management Tool | R | Capex proposal, costs and benefits case |
| `get_capital_budget_and_hurdle_rates` | Budgeting & Forecasting Tool | R | Capital budget, hurdle rate and risk adjustments |
| `get_capital_project_proposals` | Project & Portfolio Management Tool | R | Candidate capital projects and cases |
| `get_carrier_bid_rates` | Sourcing / RFx Platform | R | Rates quoted by prospective carriers or 3PLs |
| `get_carrier_contract_rates` | Freight Rate Management System | R | Current carrier contract rates |
| `get_cash_flow_forecast_18_months` | Treasury Management System | R | 18-month cash and debt forecast |
| `get_channel_revenue_and_margin` | Costing & Margin Tool | R | Revenue and margin by channel and segment |
| `get_company_financial_kpis` | Consolidation & Reporting Tool | R | Own margin, growth and inventory turn KPIs |
| `get_contract_payment_terms` | Contract Management System | R | Contract payment terms and remedies |
| `get_cost_to_serve_by_channel` | Cost Allocation Tool | R | Cost to serve by channel and cost type |
| `get_credit_agency_report` | Web | R | Credit agency score and report for a company |
| `get_credit_hold_policy` | Knowledge Base / Policy Library | R | Credit hold and shipment stop policy |
| `get_credit_insurance_cover` | Accounts Receivable System | R | Credit insurance policy cover for a customer |
| `get_cross_dock_handling_rates` | Labour Management System (LMS) | R | Handling cost per unit at a cross-dock |
| `get_currency_exposure_forecast` | FX & Hedging Platform | R | Net currency exposure by month |
| `get_current_duty_rates` | Tax & Duty System | R | Duty rates by tariff code and origin |
| `get_customer_account_summary` | Accounts Receivable System | R | Customer balance, limit, ageing and terms |
| `get_customer_exposure_summary` | Accounts Receivable System | R | Total exposure including unbilled orders |
| `get_customer_payment_history` | Accounts Receivable System | R | Payment behaviour and days-to-pay trend |
| `get_dc_control_test_results` | Internal Audit System | R | Control test results by site |
| `get_dc_handling_rates` | Labour Management System (LMS) | R | Handling cost per unit at a DC |
| `get_debt_facilities_and_covenants` | Treasury Management System | R | Facility terms and covenant tests |
| `get_debt_facilities_and_headroom` | Treasury Management System | R | Facility limits, drawn amounts and headroom |
| `get_delivery_notes_for_invoice` | Order Management System (OMS) | R | Delivery notes and proof of delivery for an order |
| `get_demand_forecast` | Demand Planning System | R | Demand forecast by category and period |
| `get_demand_scenarios` | Demand Planning System | R | Downside and upside demand scenarios |
| `get_dispute_documents` | Documents | R | Read documents from the attached dispute pack |
| `get_dividend_policy_and_schedule` | Treasury Management System | R | Dividend policy and planned payments |
| `get_duty_and_insurance_by_sku` | Tax & Duty System | R | Duty and insurance cost per SKU |
| `get_duty_cost_trend` | Tax & Duty System | R | Duty cost by product and origin over time |
| `get_duty_paid_by_entry` | Tax & Duty System | R | Duty paid by customs entry |
| `get_ecom_cost_per_order` | Cost Allocation Tool | R | Activity-based cost per e-commerce order by component |
| `get_ecom_order_volumes_and_mix` | E-commerce Platform | R | E-commerce order volumes and basket mix |
| `get_enterprise_risk_register` | Risk Management System | R | Principal risks and ratings |
| `get_expected_recovery_rates` | Costing & Margin Tool | R | Expected recovery on aged or clearance stock |
| `get_first_sale_candidates` | Customs & Trade Compliance System | R | Transactions eligible for first-sale valuation |
| `get_forecast_accuracy_by_line` | Budgeting & Forecasting Tool | R | Forecast versus actual by line and period |
| `get_forecast_cash_flows_by_currency` | Treasury Management System | R | Forecast cash flows by currency |
| `get_forecast_drivers_and_assumptions` | Budgeting & Forecasting Tool | R | Driver assumptions behind a forecast version |
| `get_freight_cost_by_ledger_account` | ERP (General Ledger) | R | Freight cost postings by account and period |
| `get_freight_cost_by_sku` | Transport Management System (TMS) | R | Freight cost allocated per SKU |
| `get_freight_cost_from_tms` | Transport Management System (TMS) | R | Freight cost per shipment from the transport system |
| `get_freight_rate_forecast` | Freight Rate Management System | R | Contract and spot freight rate outlook |
| `get_full_year_outlook` | Budgeting & Forecasting Tool | R | Latest full-year forecast for revenue, margin and EBIT |
| `get_fx_budget_assumptions` | Budgeting & Forecasting Tool | R | Budgeted FX rates and hedge assumptions |
| `get_fx_forecast_accuracy_history` | Web | R | Historical accuracy of FX forecasters |
| `get_fx_gain_loss_by_account` | ERP (General Ledger) | R | FX gain and loss postings by account |
| `get_fx_hedge_book` | FX & Hedging Platform | R | Open hedges by currency, rate and maturity |
| `get_fx_impact_on_cogs` | FX & Hedging Platform | R | COGS impact of FX movements net of hedges |
| `get_fx_rates_for_period` | FX & Hedging Platform | R | Historical FX rates for a currency pair and period |
| `get_gross_margin_bridge` | Costing & Margin Tool | R | Gross margin movement bridged by driver |
| `get_guidance_and_outlook` | Consolidation & Reporting Tool | R | Current guidance and outlook |
| `get_guidance_risk_register` | Risk Management System | R | Risks to guidance with likelihood and impact |
| `get_hedge_cover_ratio` | FX & Hedging Platform | R | Hedged percentage by currency and month |
| `get_hedge_effectiveness_report` | FX & Hedging Platform | R | Hedge accounting effectiveness results |
| `get_hedge_instrument_pricing` | FX & Hedging Platform | R | Forward, option and collar pricing |
| `get_hedging_policy` | Knowledge Base / Policy Library | R | Treasury hedging policy and limits |
| `get_historical_collection_patterns` | Accounts Receivable System | R | Historic collection timing by customer |
| `get_import_volumes_by_origin` | Tax & Duty System | R | Import value and volume by origin and tariff code |
| `get_initiative_confidence_and_dependencies` | Project & Portfolio Management Tool | R | Confidence rating and dependencies per initiative |
| `get_intercompany_balances` | ERP (General Ledger) | R | Intercompany balances between two entities |
| `get_intercompany_sourcing_margins` | ERP (General Ledger) | R | Sourcing entity margins and mark-ups |
| `get_internal_audit_resource_plan` | Internal Audit System | R | Audit team capacity and planned work |
| `get_inventory_and_supply_chain_cost_kpis` | Consolidation & Reporting Tool | R | Inventory and supply chain cost KPIs |
| `get_inventory_holding_cost` | Inventory Management System (IMS) | R | Inventory holding cost by location |
| `get_inventory_units_by_category` | Inventory Management System (IMS) | R | Units on hand by category |
| `get_inventory_valuation_by_site` | ERP (General Ledger) | R | Inventory valuation and provisions by site |
| `get_inventory_value_movement` | ERP (General Ledger) | R | Inventory value movement by month |
| `get_landed_cost_by_sku` | Landed Cost Calculator | R | Landed cost breakdown by SKU |
| `get_landed_cost_history` | Landed Cost Calculator | R | Landed cost components over time |
| `get_latest_forecast_version` | Budgeting & Forecasting Tool | R | Current forecast by line |
| `get_ledger_inventory_balance` | ERP (General Ledger) | R | Inventory ledger balance by account |
| `get_logistics_cost_by_line` | Cost Allocation Tool | R | Logistics cost lines as % of sales |
| `get_margin_phasing_forecast` | Budgeting & Forecasting Tool | R | Margin flow-through by month from landed cost changes |
| `get_markdown_and_shrink_rates` | Merchandise Financial Planning | R | Markdown and shrink rates by category and period |
| `get_monthly_performance_summary` | Consolidation & Reporting Tool | R | Monthly KPIs and P&L headlines |
| `get_nearshore_cost_assumptions` | Costing & Margin Tool | R | Unit cost, lead time and MOQ assumptions for nearshore sourcing |
| `get_open_orders_for_customer` | Order Management System (OMS) | R | Open and scheduled orders for a customer |
| `get_open_receivables_ledger` | Accounts Receivable System | R | Open receivables by customer and due date |
| `get_outbound_transport_cost_by_channel` | Transport Management System (TMS) | R | Outbound transport cost by channel |
| `get_overdue_trend_by_customer` | Accounts Receivable System | R | Overdue balance trend by customer |
| `get_packaging_cost_by_channel` | Packaging Design System | R | Packaging cost per order or unit by channel |
| `get_parcel_volumes_by_destination` | E-commerce Platform | R | Parcel counts and values by destination |
| `get_peak_volume_profile` | Demand Planning System | R | Peak period volume profile by region |
| `get_peer_financial_benchmarks` | Web | R | Peer margins, growth and inventory turns from filings |
| `get_pl_extract_from_document` | Documents | R | Parse the attached P&L extract into structured lines |
| `get_planned_capex_by_type` | Fixed Asset Register | R | Planned capex by asset class |
| `get_po_and_payment_data` | Documents | R | Read purchase order and payment file |
| `get_prior_audit_findings` | Internal Audit System | R | Previous audit findings by site and area |
| `get_production_volumes_by_origin` | Purchase Order System | R | Production volume by country of origin |
| `get_provisioning_policy` | Knowledge Base / Policy Library | R | Current stock provisioning policy |
| `get_realised_vs_unrealised_fx` | ERP (General Ledger) | R | Realised and unrealised FX split |
| `get_rebate_accrual_history` | Accounts Payable System | R | Rebate accruals and settlements to date |
| `get_retrospective_price_adjustments` | Purchase Order System | R | Supplier retrospective price adjustments |
| `get_returns_cost_by_channel` | Returns Management System (RMS) | R | Returns handling cost and volume by channel |
| `get_sales_order_and_invoice` | Accounts Receivable System | R | Order, invoice and price lines for an invoice |
| `get_sell_through_rates` | Merchandise Financial Planning | R | Sell-through rates by SKU and season |
| `get_shipment_volumes_by_lane` | Transport Management System (TMS) | R | Shipment volumes by lane and carrier |
| `get_shrink_and_writeoff_history` | ERP (General Ledger) | R | Shrink and write-off trend with prior-year pattern |
| `get_site_operating_costs` | Cost Allocation Tool | R | Operating cost base for a site |
| `get_site_volume_forecast` | Demand Planning System | R | Throughput volume forecast for a site |
| `get_sku_cost_to_serve` | Cost Allocation Tool | R | Cost to serve per SKU |
| `get_sku_sales_and_margin` | Costing & Margin Tool | R | Sales and margin per SKU |
| `get_slow_moving_provision` | ERP (General Ledger) | R | Provision balance and prior-year comparison |
| `get_standard_cost_updates` | Costing & Margin Tool | R | Standard cost changes and effective dates |
| `get_stock_ageing` | Inventory Management System (IMS) | R | Stock ageing by SKU and category |
| `get_stock_count_results` | Inventory Management System (IMS) | R | Stock count results and variances by DC |
| `get_store_delivery_cost_by_route` | Transport Management System (TMS) | R | Delivery cost per store by route and origin |
| `get_store_shrink_by_period` | Loss Prevention & Incident System | R | Shrink by store and period |
| `get_store_staff_schedules` | Store Workforce Management | R | Rostered staff by shift |
| `get_strategic_plan_assumptions` | Strategy & Board Reporting Tool | R | Strategic plan assumptions |
| `get_supplier_price_changes` | Purchase Order System | R | Supplier price changes by SKU |
| `get_transfer_pricing_policy` | Tax & Duty System | R | Group transfer pricing policy and mark-ups |
| `get_usd_cogs_exposure` | ERP (General Ledger) | R | USD-denominated cost of goods exposure |
| `get_variance_drivers` | Budgeting & Forecasting Tool | R | Variance split into volume, price, mix, cost and one-off drivers |
| `get_vat_return_summary` | Tax & Duty System | R | VAT return boxes versus prior period and expectation |
| `get_vendor_master_controls` | Accounts Payable System | R | Vendor master data controls and configuration |
| `get_warehouse_cost_pools` | Cost Allocation Tool | R | Warehouse cost pools and drivers |
| `get_wms_stock_valuation` | Warehouse Management System (WMS) | R | WMS stock quantity and value by SKU |
| `list_affected_customs_declarations` | Customs & Trade Compliance System | R | Declarations affected by a price adjustment |
| `list_audit_actions` | Internal Audit System | R | Audit actions with status and due dates |
| `list_bank_detail_change_requests` | Accounts Payable System | R | Bank detail change history and approvals |
| `list_classification_positions` | Customs & Trade Compliance System | R | Our tariff classifications and valuation positions |
| `list_cost_saving_initiatives` | Project & Portfolio Management Tool | R | Cost saving initiatives with owners and status |
| `list_intercompany_transactions` | ERP (General Ledger) | R | Intercompany postings by currency and posting date |
| `list_inventory_adjustments` | Inventory Management System (IMS) | R | Inventory adjustments and write-ons |
| `list_key_risks_and_opportunities` | Risk Management System | R | Risks and opportunities register entries |
| `list_loss_making_skus` | Costing & Margin Tool | R | SKUs with cost to serve above margin |
| `list_margin_recovery_actions` | Budgeting & Forecasting Tool | R | Candidate margin recovery actions with estimated value |
| `list_miscoded_freight_invoices` | Accounts Payable System | R | Freight invoices posted to unexpected accounts |
| `list_mitigation_levers` | Budgeting & Forecasting Tool | R | Available cost or revenue levers with value and lead time |
| `list_one_off_journals` | ERP (General Ledger) | R | Non-recurring and manual journals in a period |
| `list_open_accruals` | ERP (General Ledger) | R | Open accrual balances with age |
| `list_open_close_tasks` | Consolidation & Reporting Tool | R | Open items on the month-end close checklist |
| `list_overdue_invoices` | Accounts Receivable System | R | Overdue invoices by customer with ageing |
| `list_pos_exceptions` | Point of Sale (POS) | R | Voids, refunds and discounts by user and till |
| `list_stock_adjustments_for_store` | Inventory Management System (IMS) | R | Stock adjustments by store, user and time |
| `list_supplier_rebate_agreements` | Accounts Payable System | R | Rebate agreements and thresholds by supplier |
| `list_timing_items` | ERP (General Ledger) | R | Accruals, prepayments and phasing items that reverse in later periods |
| `list_top_skus_by_sales` | Costing & Margin Tool | R | Top SKUs ranked by sales |
| `list_transfer_pricing_documentation` | Tax & Duty System | R | Held transfer pricing files and local files |
| `list_unaccrued_freight_invoices` | Accounts Payable System | R | Freight invoices received but not accrued |
| `list_unreconciled_accounts` | ERP (General Ledger) | R | Balance sheet reconciliations not signed off, with age |
| `list_vat_transactions_by_entity` | Tax & Duty System | R | VAT postings by entity, code and period |
| `list_vendor_master_changes` | Accounts Payable System | R | New vendors and bank detail changes with dates |
| `reassign_reconciliation` | ERP (General Ledger) | W | Changes the preparer or reviewer of a balance sheet reconciliation |
| `release_order_hold` | Order Management System (OMS) | W | Releases a held order for fulfilment |
| `reverse_inventory_adjustment` | Inventory Management System (IMS) | W | Reverses a posted inventory adjustment |
| `run_analysis` | Code Execution | R | Run an agent-side analysis, calculation or chart in the sandbox |
| `run_anomaly_tests_on_payments` | Code Execution | R | Duplicate, split, round-sum and weekend posting tests |
| `run_rate_volume_mix_decomposition` | Code Execution | R | Split cost change into volume, mix and rate effects |
| `search_accounting_policy` | Knowledge Base / Policy Library | R | Search internal accounting policies and guidance |
| `search_accounting_standards_guidance` | Web | R | Search accounting standards and published guidance |
| `search_analyst_commentary` | Web | R | Analyst notes and results-call transcripts |
| `search_audit_good_practice` | Web | R | Good practice controls and audit guidance |
| `search_cctv_incident_logs` | CCTV / Exception Reporting | R | CCTV exception and incident log entries |
| `search_classification_rulings` | Web | R | Recent tariff classification and valuation rulings |
| `search_company_filings` | Web | R | Search public filings for a company |
| `search_company_news` | Web | R | Recent news on a company |
| `search_control_test_results` | Internal Audit System | R | Retest results for closed actions |
| `search_customs_valuation_rulings` | Web | R | Customs valuation rules and rulings |
| `search_debt_recovery_guidance` | Web | R | Legal steps for debt recovery |
| `search_duty_relief_rules` | Web | R | Drawback, first-sale and bonded rules |
| `search_email_thread` | Email & Calendar | R | Search emails on a customer dispute |
| `search_fx_consensus_forecasts` | Web | R | Bank and consensus FX forecasts |
| `search_fx_market_news` | Web | R | Market news affecting FX |
| `search_ias2_nrv_guidance` | Web | R | IAS 2 and NRV guidance for seasonal stock |
| `search_logistics_benchmarks` | Web | R | Retail logistics cost benchmarks and definitions |
| `search_peer_annual_reports` | Web | R | Search peer annual reports and disclosures |
| `search_peer_supply_chain_investments` | Web | R | Peer supply chain investment announcements and results |
| `search_preferential_origin_rules` | Customs & Trade Compliance System | R | Origin rules and preferential rates |
| `search_sector_margin_analysis` | Web | R | Sector reports on margin pressure |
| `search_tariff_announcements` | Web | R | Proposed tariff changes and trade news |
| `search_tax_authority_guidance` | Web | R | Tax authority guidance and rulings |
| `search_tax_incentives` | Web | R | Available capital allowances and incentives |
| `search_transfer_pricing_rules` | Web | R | Current OECD and local TP rules |
| `search_unmatched_intercompany_items` | Consolidation & Reporting Tool | R | Unmatched or one-sided intercompany items |
| `search_vat_customs_regulations` | Web | R | VAT and customs rules for low-value parcels |
| `send_close_task_reminder` | Consolidation & Reporting Tool | W | Sends a reminder to the owner of an open close task |
| `send_email_to_recipient` | Email & Calendar | W | Sends an email, with attachments, to named recipients |
| `send_payment_reminder` | Accounts Receivable System | W | Sends a dunning or chaser notice for overdue invoices |
| `send_supplier_price_query` | Supplier Portal | W | Sends a price-change query to a supplier through the portal |
| `submit_binding_ruling_application` | Customs & Trade Compliance System | W | Submits an application for a binding tariff or valuation ruling |
| `submit_capex_case_for_review` | Project & Portfolio Management Tool | W | Submits a capex case to the capex committee queue |
| `submit_customs_declaration_amendment` | Customs & Trade Compliance System | W | Files an amendment to a lodged customs declaration |
| `submit_hedge_trade_for_approval` | FX & Hedging Platform | W | Submits a proposed hedge trade for treasury approval |
| `submit_journal_for_approval` | ERP (General Ledger) | W | Sends a draft journal into the approval workflow for posting |
| `update_audit_action_status` | Internal Audit System | W | Changes an audit action's status, e.g. reopens it |
| `update_cost_allocation_driver` | Cost Allocation Tool | W | Changes the allocation driver for a cost pool |
| `update_customer_credit_hold` | Accounts Receivable System | W | Places or lifts a credit hold on a customer |
| `update_customer_credit_limit` | Accounts Receivable System | W | Changes a customer's credit limit |
| `update_initiative_status` | Project & Portfolio Management Tool | W | Changes the status of an initiative, e.g. to on hold |
| `update_invoice_dispute_status` | Accounts Receivable System | W | Marks an invoice as disputed or on dispute hold |
| `update_invoice_gl_coding` | Accounts Payable System | W | Changes the GL account or cost centre coded on a posted invoice |
| `update_payment_run_date` | Accounts Payable System | W | Moves a scheduled payment run to a new date |
| `update_vat_code_on_transaction` | Tax & Duty System | W | Corrects the VAT code on a posted transaction |
