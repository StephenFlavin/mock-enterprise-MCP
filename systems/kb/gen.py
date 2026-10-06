def generate(g):
    """Generate knowledge base data."""

    # Knowledge base articles - for testing create/archive
    articles = [
        {
            "article_id": "KB-000001",
            "title": "ERP-WMS stock reconciliation mismatch resolution",
            "category": "reconciliation",
            "content": "Timing differences between ERP cutoff and WMS receipt processing cause recurring £1m+ gaps. Root cause: WMS receives goods 1-3 days after ERP records inbound PO. Solution: move WMS cutoff to match ERP close window.",
            "status": "published",
            "created_at": g.fake.date_time_between(start_date="-180d", end_date="-30d"),
            "updated_at": g.fake.date_time_between(start_date="-30d", end_date="-5d"),
        },
        {
            "article_id": "KB-000002",
            "title": "WMS duplicate task creation after replenishment - patch 9.2.7",
            "category": "failure_mode",
            "content": "Known issue in WMS 9.2: duplicate replenishment tasks created if system receives two PO receipts in <5 second window. Fixed in patch 9.2.7. Workaround: increase event queue timeout from 1s to 5s in config.",
            "status": "published",
            "created_at": g.fake.date_time_between(start_date="-60d", end_date="-30d"),
            "updated_at": g.fake.date_time_between(start_date="-30d", end_date="-5d"),
        },
    ]

    # Policies - all the get_*_policy tools return from here
    policies = [
        {
            "policy_id": "POL-APPROVAL-001",
            "policy_type": "approval_limits",
            "policy_name": "Purchase Order and Payment Approval Limits",
            "content": "Approval limits by role and amount:\n- Store Manager: GBP 5,000\n- Warehouse Manager: GBP 10,000\n- Buyer: GBP 50,000\n- Category Manager: GBP 100,000\n- Director: GBP 500,000\n- CFO/CEO: unlimited\nAll orders over GBP 1,000 require 2 approvals. All supplier bank detail changes require Finance review.",
            "version": "2.1",
            "effective_date": g.days_ago(120),
            "updated_at": g.fake.date_time_between(start_date="-60d", end_date="-5d"),
        },
        {
            "policy_id": "POL-CREDIT-001",
            "policy_type": "credit_hold",
            "policy_name": "Customer Credit Hold Policy",
            "content": "Put customer on credit hold when:\n- Invoice >60 days overdue\n- Account balance >GBP 500k\n- DSO >90 days\nAction: stop shipments, escalate to Credit Controller, contact customer. Release after payment received or payment plan agreed.",
            "version": "1.3",
            "effective_date": g.days_ago(180),
            "updated_at": g.fake.date_time_between(start_date="-90d", end_date="-5d"),
        },
        {
            "policy_id": "POL-CORRECTIVE-001",
            "policy_type": "corrective_action",
            "policy_name": "Supplier Quality Corrective Action Policy",
            "content": "For quality non-conformances:\n1. High-risk defects (safety, functionality): Immediate hold on all POs. Require corrective action plan within 5 days.\n2. Medium-risk defects (cosmetic, minor): Limit POs to 50% of normal volume. Require action plan within 10 days.\n3. Low-risk defects (documentation): Monitor and notify supplier within 15 days.\nSuspend supplier if repeated issues (>3 in 12 months). Exit if corrective action not implemented within 30 days.",
            "version": "2.0",
            "effective_date": g.days_ago(365),
            "updated_at": g.fake.date_time_between(start_date="-90d", end_date="-5d"),
        },
        {
            "policy_id": "POL-HEDGE-001",
            "policy_type": "hedging",
            "policy_name": "Treasury Hedging Policy",
            "content": "Currency hedging limits:\n- USD exposure: hedge 50-80% of 12-month forecast. Max 100%.\n- EUR exposure: hedge 40-70% of 12-month forecast. Max 90%.\n- Other major currencies: hedge 40-60%. Max 80%.\nInstruments allowed: forward contracts, options (call spreads max). Forbid: speculative positions, exotic options.\nReview hedge ratios quarterly. Spot rates used for P&L; mark hedges at forward rates.",
            "version": "1.4",
            "effective_date": g.days_ago(240),
            "updated_at": g.fake.date_time_between(start_date="-60d", end_date="-5d"),
        },
        {
            "policy_id": "POL-INSURANCE-001",
            "policy_type": "insurance_requirements",
            "policy_name": "Supplier Insurance Requirements",
            "content": "All suppliers must maintain:\n- General Liability: min GBP 2m (high-risk) or GBP 500k (low-risk)\n- Product Liability: min GBP 5m (food/apparel) or GBP 1m (other)\n- Cyber Liability: min GBP 1m (if data access)\n- Cargo Insurance: min 110% of shipment value\n- All policies: evidence of coverage required at onboarding and annually",
            "version": "2.2",
            "effective_date": g.days_ago(120),
            "updated_at": g.fake.date_time_between(start_date="-60d", end_date="-5d"),
        },
        {
            "policy_id": "POL-ONBOARD-001",
            "policy_type": "onboarding_requirements",
            "policy_name": "Supplier Onboarding Minimum Requirements",
            "content": "Requirements by risk tier:\nHIGH-RISK (emerging markets, new sector, high spend):\n- Social and ethical audit (BSCI or equivalent) required before first order\n- Business registration and tax ID verification\n- Bank references (3 suppliers)\n- Insurance evidence (GL 2m+, PL 5m+)\n- Sanctions screening required\nMEDIUM-RISK (developed market, established sector):\n- Audit within 12 months of first order\n- Business registration verification\n- Bank references (2 suppliers)\n- Insurance evidence (GL 1m+, PL 2m+)\nLOW-RISK (existing supplier, low spend):\n- Basic compliance check\n- Insurance verification\n- Annual audit if spend >GBP 500k",
            "version": "1.5",
            "effective_date": g.days_ago(180),
            "updated_at": g.fake.date_time_between(start_date="-90d", end_date="-5d"),
        },
        {
            "policy_id": "POL-INVENTORY-001",
            "policy_type": "inventory_definition",
            "policy_name": "Inventory Ownership and Valuation Policy",
            "content": "Inventory ownership: Transfer of title at receipt into our DC (not in-transit). In-transit goods remain supplier's responsibility until gate-in.\nStatus definitions:\n- Available: ready for picking or sale\n- In-transit: on PO, not yet received\n- Reserved: allocated to open orders\n- Damaged: non-saleable, awaiting write-off approval\nValuation: FIFO method. Seasonal stock over 180 days old to be marked down 25% minimum per NRV rules.",
            "version": "2.0",
            "effective_date": g.days_ago(365),
            "updated_at": g.fake.date_time_between(start_date="-120d", end_date="-5d"),
        },
        {
            "policy_id": "POL-DUE-DILIGENCE-001",
            "policy_type": "due_diligence",
            "policy_name": "Due Diligence Policy on Allegations",
            "content": "When allegations of forced labour or serious violations arise:\n1. IMMEDIATE (within 24 hours): Escalate to General Counsel and Ethics Officer. Secure evidence.\n2. WITHIN 5 DAYS: Assess credibility (review original reporting, NGO corroboration, supply chain connection). Interview factory if credible.\n3. WITHIN 10 DAYS: Decide on hold/suspension/exit. Communicate decision to affected functions (Sourcing, Finance, Supply Chain).\nDo NOT communicate to media or public without Legal approval.\nDocument all steps and findings for regulatory response.",
            "version": "1.2",
            "effective_date": g.days_ago(240),
            "updated_at": g.fake.date_time_between(start_date="-90d", end_date="-5d"),
        },
        {
            "policy_id": "POL-FALLBACK-001",
            "policy_type": "fallback_positions",
            "policy_name": "Approved Fallback Positions by Clause",
            "content": "Liability caps:\n- Our position: No cap on product liability, safety claims. Cap at 2x annual order value for other claims.\n- First fallback: Cap at order value.\n- Red line: Will not accept cap <order value.\nIP Ownership:\n- Our position: We own all IP including improvements and know-how.\n- First fallback: Shared IP rights; we get license to use at no cost.\n- Red line: Will not accept supplier retaining exclusive rights.\nForce majeure:\n- Our position: Force majeure only for unforeseeable events; requires suspension, not termination.\n- First fallback: Allow termination if event lasts >90 days.\n- Red line: None; event must clear before resuming.",
            "version": "1.3",
            "effective_date": g.days_ago(180),
            "updated_at": g.fake.date_time_between(start_date="-60d", end_date="-5d"),
        },
        {
            "policy_id": "POL-INCIDENT-001",
            "policy_type": "incident_response",
            "policy_name": "Incident Response and Escalation Playbook",
            "content": "QUALITY INCIDENT:\n- Severity 1 (safety): Immediate hold, exec escalation, customer notification within 4 hours\n- Severity 2 (functionality): 24-hour response, manager escalation, customer notification within 24 hours\n- Severity 3 (cosmetic): 5-day response, team escalation\nSUPPLY CHAIN INCIDENT (geopolitical, transport, supplier failure):\n- Tier 1 (affects delivery <72 hours): Escalate to VP Supply Chain immediately\n- Tier 2 (affects delivery 3-7 days): Manager escalation, sourcing team response\n- Tier 3 (future impact): Monitor and document\nSECURITY INCIDENT:\n- CISO involvement mandatory. Supplier user account compromise: lock account, block payments, audit access logs.",
            "version": "1.4",
            "effective_date": g.days_ago(240),
            "updated_at": g.fake.date_time_between(start_date="-90d", end_date="-5d"),
        },
        {
            "policy_id": "POL-LEGAL-001",
            "policy_type": "legal_wording",
            "policy_name": "Legal Guidance on Admissions and Claims Wording",
            "content": "Avoid in customer communication, marketing, and internal documents:\n- 'Defect' or 'defective' (use 'does not meet spec' or 'variation')\n- 'We are responsible for...' (use 'The matter involves...')\n- Admitting causation without evidence ('caused by X' without testing)\n- Making comparative claims ('better than competitor') without substantiation\n- Sustainability claims ('eco-friendly', 'sustainable') without certification\nSAFE WORDING:\n- 'We are investigating the matter.'\n- 'Testing to date indicates...'\n- 'Meets ISO 14040 environmental standards.'\n- Always include: 'Pending further testing/investigation/legal review.'",
            "version": "1.5",
            "effective_date": g.days_ago(120),
            "updated_at": g.fake.date_time_between(start_date="-60d", end_date="-5d"),
        },
        {
            "policy_id": "POL-LOT-001",
            "policy_type": "lot_acceptance",
            "policy_name": "Lot Acceptance Quality and Release Policy",
            "content": "AQL (Acceptable Quality Level) by defect severity:\n- Critical (safety, function): AQL 0.65%, max 1 defect per 100 units sampled\n- Major (appearance >2cm, function <spec): AQL 1.5%, max 2 defects per 100 units\n- Minor (small appearance): AQL 2.5%, max 3 defects per 100 units\nRelease decision:\n- Results within AQL: Release for sale\n- 1 critical defect: Reject entire lot. Request rework or replacement.\n- >1 major defect: Conditional release at 20% price reduction if customer accepts\n- Sorted and reworked lots: Retest at 2x sample size. All critical defects must be zero.",
            "version": "1.2",
            "effective_date": g.days_ago(150),
            "updated_at": g.fake.date_time_between(start_date="-60d", end_date="-5d"),
        },
        {
            "policy_id": "POL-MARKET-001",
            "policy_type": "market_entry",
            "policy_name": "Internal Policy on Market Entry Structures",
            "content": "Market entry structures by region and spend:\nUK/EU (mature markets, <GBP 5m annual): Franchise or partnership preferred. Subsidiary if >GBP 50m spend or IP at risk.\nEmerging markets (China, India, SE Asia, <GBP 20m): Joint venture with local partner required. IP strictly protected. Exit clause mandatory.\nNearshore (Turkey, Morocco, Mexico, GBP 5-50m): Joint venture or subsidiary. Build IP gradually; don't over-rely on one partner.\nExit: Subsidiary - require 6-month notice, transfer of contracts and staff obligations. JV - buyout clause if partner underperforms.",
            "version": "1.1",
            "effective_date": g.days_ago(300),
            "updated_at": g.fake.date_time_between(start_date="-150d", end_date="-5d"),
        },
        {
            "policy_id": "POL-ASSURANCE-001",
            "policy_type": "assurance_requirements",
            "policy_name": "Assurance and Reporting Requirements",
            "content": "Assurance requirements for ESG and sustainability reporting:\nScope 1 & 2 Emissions: Annual independent third-party assurance (ISO 14064-3). Acceptable assurance providers: ISAE 3000 accredited bodies.\nScope 3 Emissions: Reasonable assurance required for supply chain emissions >50% of total. Data evidence: supplier questionnaires, shipment records, conversion factors from GHG Protocol.\nSupply Chain Disclosures: Annual audit of forced labour due diligence (legal obligation UK MSA 2015). Evidence: supplier audit reports, sanctions screening, grievance records.\nReporting Framework Compliance: All disclosures against TCFD, GRI, SASB standards require management review and sign-off.",
            "version": "1.2",
            "effective_date": g.days_ago(180),
            "updated_at": g.fake.date_time_between(start_date="-90d", end_date="-5d"),
        },
        {
            "policy_id": "POL-CODE-001",
            "policy_type": "supplier_code_of_conduct",
            "policy_name": "Supplier Code of Conduct - Wage and Hour Clauses",
            "content": "Mandatory clauses in supplier code of conduct:\nMINIMUM WAGES: Suppliers must pay at least local legal minimum wage or industry standard (whichever is higher) plus statutory benefits.\nWORKING HOURS: Maximum 48 hours per week normal working hours, max 60 hours including overtime. Overtime voluntary and fairly compensated (at least 1.5x regular rate).\nFREE TIME: Minimum one rest day per 7 days, plus statutory public holidays.\nCHILD LABOUR: No workers under 15 (or local school-leaving age). Under 18s not permitted in hazardous work.\nFORCED LABOUR: Zero tolerance. No wage deductions except legal requirements. All work voluntary.\nFREEDOM OF ASSOCIATION: Workers may join or form unions; suppliers must not interfere or discriminate.",
            "version": "2.1",
            "effective_date": g.days_ago(180),
            "updated_at": g.fake.date_time_between(start_date="-90d", end_date="-5d"),
        },
    ]

    # Policy items - for structured lookup (e.g., onboarding requirements by risk tier)
    policy_items = [
        {
            "item_id": "POL-ITEM-001",
            "policy_id": "POL-ONBOARD-001",
            "item_key": "risk_tier_high_audit",
            "item_value": "BSCI audit or equivalent required before first order",
            "description": "Social and ethical audit requirement for high-risk suppliers",
            "effective_date": g.days_ago(180),
            "updated_at": g.fake.date_time_between(start_date="-90d", end_date="-5d"),
        },
        {
            "item_id": "POL-ITEM-002",
            "policy_id": "POL-ONBOARD-001",
            "item_key": "risk_tier_high_insurance",
            "item_value": "GL 2m, PL 5m minimum",
            "description": "Insurance requirements for high-risk suppliers",
            "effective_date": g.days_ago(180),
            "updated_at": g.fake.date_time_between(start_date="-90d", end_date="-5d"),
        },
        {
            "item_id": "POL-ITEM-003",
            "policy_id": "POL-ONBOARD-001",
            "item_key": "risk_tier_medium_audit",
            "item_value": "Audit within 12 months of first order",
            "description": "Audit requirement for medium-risk suppliers",
            "effective_date": g.days_ago(180),
            "updated_at": g.fake.date_time_between(start_date="-90d", end_date="-5d"),
        },
        {
            "item_id": "POL-ITEM-004",
            "policy_id": "POL-ONBOARD-001",
            "item_key": "risk_tier_medium_insurance",
            "item_value": "GL 1m, PL 2m minimum",
            "description": "Insurance requirements for medium-risk suppliers",
            "effective_date": g.days_ago(180),
            "updated_at": g.fake.date_time_between(start_date="-90d", end_date="-5d"),
        },
        {
            "item_id": "POL-ITEM-005",
            "policy_id": "POL-ONBOARD-001",
            "item_key": "risk_tier_low_insurance",
            "item_value": "GL 500k, PL 1m minimum",
            "description": "Insurance requirements for low-risk suppliers",
            "effective_date": g.days_ago(180),
            "updated_at": g.fake.date_time_between(start_date="-90d", end_date="-5d"),
        },
    ]

    # KPI definitions
    kpi_definitions = [
        {
            "kpi_id": "KPI-OTIF-001",
            "kpi_name": "perfect order rate",
            "definition": "Percentage of orders that arrive in full, on-time, undamaged and with correct documentation.",
            "formula": "(Orders delivered on-time AND in-full AND no damage AND correct docs) / Total orders * 100",
            "data_source": "Order management system + delivery confirmation + damage reports",
            "unit": "percentage",
            "effective_date": g.days_ago(365),
            "version": "1.0",
        },
        {
            "kpi_id": "KPI-DSO-001",
            "kpi_name": "days sales outstanding",
            "definition": "Average number of days to collect payment after invoice. Measures credit and collection efficiency.",
            "formula": "(Average Accounts Receivable / Daily Revenue) where Daily Revenue = Annual Revenue / 365",
            "data_source": "Accounts receivable ledger + sales journal",
            "unit": "days",
            "effective_date": g.days_ago(240),
            "version": "1.1",
        },
        {
            "kpi_id": "KPI-NRV-001",
            "kpi_name": "net realisable value provision",
            "definition": "Percentage of seasonal stock >180 days old marked down per inventory valuation policy.",
            "formula": "Stock value marked down / Total stock value * 100 where age >180 days",
            "data_source": "Inventory management system + stock age analysis",
            "unit": "percentage",
            "effective_date": g.days_ago(180),
            "version": "1.0",
        },
    ]

    # KPI definition changes - for tracking history
    kpi_changes = [
        {
            "change_id": "KPI-CHG-001",
            "kpi_id": "KPI-OTIF-001",
            "changed_at": g.fake.date_time_between(start_date="-90d", end_date="-30d"),
            "old_definition": "On-time and in-full only",
            "new_definition": "On-time and in-full and no damage and correct docs",
            "change_reason": "Expanded to include damage and documentation accuracy after customer complaints",
        },
    ]

    # Audit requirements by risk tier
    audit_requirements = [
        {
            "requirement_id": "AUD-REQ-001",
            "risk_tier": "high",
            "audit_type": "social",
            "frequency": "annual",
            "standard": "BSCI",
            "scope": "Labour practices, wages, hours, child labour, forced labour",
        },
        {
            "requirement_id": "AUD-REQ-002",
            "risk_tier": "high",
            "audit_type": "quality",
            "frequency": "annual",
            "standard": "ISO 9001 or equivalent",
            "scope": "Quality management system, process controls, testing",
        },
        {
            "requirement_id": "AUD-REQ-003",
            "risk_tier": "medium",
            "audit_type": "social",
            "frequency": "triennial",
            "standard": "BSCI",
            "scope": "Labour practices, wages, hours, child labour, forced labour",
        },
        {
            "requirement_id": "AUD-REQ-004",
            "risk_tier": "low",
            "audit_type": "compliance",
            "frequency": "annual",
            "standard": "desk review",
            "scope": "Business registration, tax compliance, insurance",
        },
    ]

    # Lessons learned
    lessons = [
        {
            "lesson_id": "LES-001",
            "programme_type": "ERP",
            "lesson_description": "Initial go-live was delayed 4 months due to data quality issues not caught in testing. 30% of master data records had duplicates or missing fields.",
            "recommendation": "For future implementations, run 2 full data audit cycles 6 months before go-live. Assign dedicated data governance resource.",
            "date_learned": g.days_ago(500),
        },
        {
            "lesson_id": "LES-002",
            "programme_type": "WMS",
            "lesson_description": "Training completion was only 45% at go-live. Night shift teams skipped training. Errors doubled in first month.",
            "recommendation": "Require 100% training completion with signed attestation. Schedule training on each shift, not just day shift.",
            "date_learned": g.days_ago(400),
        },
    ]

    # Standard clauses
    clauses = [
        {
            "clause_id": "CLS-001",
            "clause_name": "Force Majeure",
            "clause_type": "supplier_agreement",
            "wording": "Neither party shall be liable for failure to perform under this agreement due to events beyond its reasonable control (war, natural disaster, government action). Performing party must: (a) suspend performance, not terminate; (b) notify other party within 48 hours; (c) resume performance within 30 days; (d) if suspension exceeds 90 days, either party may terminate without penalty. Force majeure does not include labour strikes, supplier's financial failure, or shipping delays.",
            "effective_date": g.days_ago(365),
            "version": "2.1",
        },
        {
            "clause_id": "CLS-002",
            "clause_name": "Limitation of Liability",
            "clause_type": "supplier_agreement",
            "wording": "Supplier's total liability to Buyer under this agreement shall not exceed the total amount paid by Buyer in the 12 months preceding the claim, except for: (a) indemnification for IP infringement; (b) product liability for death or personal injury; (c) data breach or loss of confidential information. In no event shall either party be liable for consequential, incidental, or punitive damages.",
            "effective_date": g.days_ago(300),
            "version": "1.8",
        },
        {
            "clause_id": "CLS-003",
            "clause_name": "Intellectual Property Ownership",
            "clause_type": "supplier_agreement",
            "wording": "Buyer owns all IP, including designs, improvements, know-how and derivative works created under this agreement. Supplier assigns all IP rights to Buyer upon creation. Supplier grants a royalty-free license to any pre-existing IP necessary to perform. Supplier warrants all deliverables do not infringe third-party IP.",
            "effective_date": g.days_ago(365),
            "version": "1.2",
        },
    ]

    return {
        "knowledge_base_articles": articles,
        "policies": policies,
        "policy_items": policy_items,
        "kpi_definitions": kpi_definitions,
        "kpi_definition_changes": kpi_changes,
        "audit_requirements": audit_requirements,
        "lessons_learned": lessons,
        "standard_clauses": clauses,
    }
