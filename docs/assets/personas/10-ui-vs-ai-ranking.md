# 10 · UI vs AI: Where AI Actually Earns Its Place

Ranking of all 90 personas by how much of their question set genuinely needs AI, versus being served faster and more accurately by a conventional UI (handheld, dashboard, report, filter, workflow screen).

**Assumption:** the company already has standard enterprise tooling (WMS, TMS, ERP, planning system, BI dashboards, PIM, ticketing). If a tool is missing, AI value rises for that role.
**Caveat:** scores are judgement calls from the role descriptions and the 450 questions in files 01–09, not measured. Treat the bands as estimates to test, not facts.

---

## Scoring scale

| Score | Label | Meaning | Est. share of the role's questions that are AI-suited |
|---|---|---|---|
| 5 | AI-primary | Questions are open-ended, cross-source or about the outside world. The UI is just the data layer. | 75%+ |
| 4 | AI-heavy | Dashboards cover monitoring. AI covers diagnosis, research and scenarios. | 50–75% |
| 3 | Hybrid | Tools handle the routine. AI helps with exceptions and investigations. | 30–50% |
| 2 | UI-first | Screens and workflows cover nearly everything. AI only for occasional exceptions. | 10–30% |
| 1 | UI-only | Handheld, SOP or system prompt covers it. AI adds little. | <10% |

---

## What pushes a question towards AI

- It spans several systems or files (WMS adjustments + POS + receipts + supplier notes).
- The answer needs reading unstructured material (contracts, audit reports, regulations, emails, specs, news).
- It depends on external, changing information (tariffs, port congestion, regulation, commodity news, competitors).
- It is a "why?" with no known filter or report that answers it.
- The output is a synthesis, draft, comparison or scenario narrative, not a number.

## What pushes a question towards a UI

- It is a deterministic lookup (location, dimensions, stock on hand, order status, pick list).
- It needs real-time operational accuracy (dock schedule, live queue, tracking position).
- It is a transactional or approval workflow (match invoice, book slot, adjust stock).
- The filter or report already exists and the user knows it.
- A wrong number has immediate cost, so the system of record should answer, not a model.

**Hybrid pattern worth designing for:** the UI shows the number, AI explains it. Example: the store shrink report is a UI job; "why is shrink up in my store and what patterns sit behind the adjustments?" is an AI job.

---

## Ranking

Columns: **#** is the persona number from the original list (files 01–09).

### Tier 5: AI-primary (ranks 1–14)

| Rank | # | Persona | Score | Keep in a UI/tool | Where AI earns its place |
|---|---|---|---|---|---|
| 1 | 50 | Supply chain risk analyst | 5 | Supplier map, alert feeds | Linking events to exposed suppliers, impact scenarios, supplier financial health research |
| 2 | 46 | Ethical trade manager | 5 | Audit and grievance platform | Reading reports and news across tiers, risk triage, law and import-ban changes |
| 3 | 44 | Product safety/regulatory specialist | 5 | Test report store, substance lists | Market-by-market rule lookup, regulation change impact, failure root-cause tracing |
| 4 | 14 | Customs and trade compliance specialist | 5 | Declaration system, tariff database | Classification reasoning, tariff change impact, origin and agreement qualification |
| 5 | 38 | Contracts/legal counsel (commercial) | 5 | Contract repository | Clause comparison to template, risk spotting, legal change research |
| 6 | 67 | Tax and duty specialist | 5 | Tax filing systems | Rule research by country, transfer pricing logic, duty scenarios |
| 7 | 56 | Trend/insight analyst | 5 | Social and search dashboards | Synthesising trend signals, fad vs shift judgement, competitor moves |
| 8 | 34 | Sourcing manager (Europe/nearshore) | 5 | Supplier database, cost model | Finding suppliers, reshoring cost and lead time scenarios, market intel |
| 9 | 39 | Raw materials/commodities buyer | 5 | Price feeds, hedging tools | Explaining price drivers, supply disruption research, buy-timing scenarios |
| 10 | 60 | R&D materials scientist | 5 | Lab data systems | Literature and patent review, alternative material search, failure diagnosis |
| 11 | 32 | Category buyer | 5 | Quote and contract systems, sales reports | Cost breakdown challenge, benchmark research, supplier trade-off analysis |
| 12 | 45 | Sustainability manager | 5 | Carbon accounting tool | Hotspot analysis, lever comparison, standards and peer research |
| 13 | 63 | Supply chain finance analyst | 5 | Cost allocation model, ERP reports | Landed cost variance drivers, unprofitable-segment analysis, benchmarks |
| 14 | 62 | FP&A analyst | 5 | Planning tool, P&L models | Margin driver decomposition, scenario narratives, peer comparison |

### Tier 4: AI-heavy (ranks 15–42)

| Rank | # | Persona | Score | Keep in a UI/tool | Where AI earns its place |
|---|---|---|---|---|---|
| 15 | 80 | Franchise/international market manager | 4 | Partner performance dashboards | Local regulation and market research, range fit, stock-out diagnosis |
| 16 | 33 | Sourcing manager (Asia) | 4 | Production schedule tracker | Delay root causes, country risk and labour cost research, volume shift scenarios |
| 17 | 12 | Freight forwarder / ocean freight buyer | 4 | Rate platforms, booking portals | Rate driver explanation, capacity outlook, carrier notices and reliability analysis |
| 18 | 87 | Chief supply chain officer | 4 | Executive KPI dashboard | Structural inefficiency diagnosis, resilience scenarios, industry best practice |
| 19 | 81 | Data analyst (supply chain) | 4 | BI tool, SQL | Ad hoc analysis, metric reconciliation, drafting queries |
| 20 | 48 | ESG reporting analyst | 4 | ESG data platform | Framework requirement research, year-on-year variance explanation |
| 21 | 35 | Supplier relationship manager | 4 | Scorecards | Pattern diagnosis across performance, financial and news data |
| 22 | 41 | Supplier onboarding specialist | 4 | Onboarding workflow, KYC databases | Adverse media and ownership research, requirement lookup by country |
| 23 | 51 | New product developer (NPD) | 4 | PLM critical path | Competitor and material research, failure analysis, cost scenarios |
| 24 | 54 | Product manager (own brand) | 4 | Range performance reports | Underperformance diagnosis, whitespace research, pipeline outlook |
| 25 | 52 | Product designer | 4 | Design software | Trend and competitor research, attribute-to-performance analysis |
| 26 | 58 | Costing analyst | 4 | Costing templates | Quote challenge vs benchmark, landed cost scenarios |
| 27 | 77 | Pricing analyst | 4 | Pricing tool, price-scrape dashboards | Margin diagnosis, pass-through decisions, competitor move interpretation |
| 28 | 36 | Procurement analyst | 4 | Spend cube | Deviation diagnosis, savings opportunity hunting, benchmark research |
| 29 | 40 | Packaging buyer | 4 | Spec and quote systems | EPR/recyclability rules by country, damage root causes, total cost comparison |
| 30 | 49 | Circular economy lead | 4 | Returns and resale reports | Partner and technology research, programme business cases |
| 31 | 70 | CFO / finance director | 4 | Board pack, treasury | Capital allocation trade-offs, peer and investor research, scenarios |
| 32 | 88 | COO / operations director | 4 | Operational KPI packs | Site underperformance diagnosis, benchmarks, capacity outlook |
| 33 | 90 | Programme/transformation manager | 4 | Programme plan, RAID log | Blocker diagnosis, trade-off options, lessons from comparable programmes |
| 34 | 68 | Internal auditor | 4 | Audit tools, ERP reports | Anomaly and fraud pattern hunting, control good-practice research |
| 35 | 79 | Loss prevention officer | 4 | Incident and exception reports | Pattern analysis across incidents, adjustments and POS; crime trend research |
| 36 | 74 | E-commerce manager | 4 | Web analytics, order dashboards | Conversion drop diagnosis, delivery promise trade-offs, competitor offers |
| 37 | 20 | Carrier relationship manager | 4 | Scorecards, tender tools | Invoice-vs-contract dispute analysis, benchmark research |
| 38 | 27 | S&OP lead | 4 | Planning outputs, KPI pack | Assumption change tracking, scenario trade-offs, consensus narrative |
| 39 | 31 | Network planner | 4 | Network modelling tool | Location research, business case synthesis, inefficiency diagnosis |
| 40 | 23 | Demand planner | 4 | Forecasting tool | Forecast error diagnosis, external demand signals, promo/launch analogues |
| 41 | 82 | Data scientist | 4 | ML platform, code | Method research, drift diagnosis, coding help |
| 42 | 19 | Control tower analyst | 4 | Visibility platform, alerts | Cross-source delay diagnosis, external event impact, mitigation options |

### Tier 3: Hybrid (ranks 43–75)

| Rank | # | Persona | Score | Keep in a UI/tool | Where AI earns its place |
|---|---|---|---|---|---|
| 43 | 55 | Packaging designer | 3 | Dieline and design tools | Regulatory mark research, failure diagnosis, competitor packaging review |
| 44 | 25 | Merchandise planner | 3 | MFP and OTB reports | Margin/sell-through variance diagnosis, trend research |
| 45 | 47 | Recall/incident manager | 3 | Traceability and stock location queries | Regulator precedent research, impact estimate, comms drafting |
| 46 | 42 | QA technologist | 3 | Inspection and lab systems | Root-cause analysis across tests, standards lookup |
| 47 | 43 | Factory auditor | 3 | Audit platform, checklists | Systemic pattern spotting across reports, local law research |
| 48 | 73 | Regional/area manager | 3 | Store performance dashboards | Why one store lags its peers, local market research |
| 49 | 71 | Store manager | 3 | Sales, stock, rota, delivery screens | Shrink and adjustment pattern analysis, availability root causes |
| 50 | 4 | Inventory control/cycle counter | 3 | WMS stock and transaction history, count schedule | Variance explanation across transactions, systemic vs one-off error |
| 51 | 37 | Indirect procurement manager | 3 | Tender platform, contract expiry list | Alternative supplier and benchmark research, overspend diagnosis |
| 52 | 75 | Marketplace/wholesale account manager | 3 | CRM, EDI, seller dashboards | Short-order root causes, policy change research, allocation reasoning |
| 53 | 78 | Promotions/campaign planner | 3 | Promo calendar, stock status | Past promo post-mortems, competitor and seasonal context |
| 54 | 69 | Inventory accountant | 3 | Valuation and ageing reports | Valuation movement diagnosis, provision reasoning, accounting rule lookup |
| 55 | 61 | Financial controller | 3 | GL, close checklist, reconciliations | Variance explanation, standards research, unusual transaction treatment |
| 56 | 65 | AR/credit controller | 3 | AR ledger, ageing report | Customer financial health research, dispute analysis |
| 57 | 66 | Treasury/FX analyst | 3 | Treasury system, exposure reports | Market outlook research, hedging trade-offs |
| 58 | 22 | Stock planner/replenishment analyst | 3 | Replenishment system, stock-cover reports | Why SKU X stocked out, parameter reasonableness |
| 59 | 24 | Supply planner | 3 | Supply plan, open PO views | Supplier delay root cause, external supply risk |
| 60 | 28 | Inventory optimisation analyst | 3 | Optimisation tool | What-if narrative, excess stock diagnosis |
| 61 | 29 | Markdown/clearance analyst | 3 | Markdown optimiser | Why a markdown failed, alternatives to further price cuts |
| 62 | 30 | Planning systems analyst | 3 | Accuracy reports, system config | Odd-order diagnosis, vendor documentation and method research |
| 63 | 21 | Reverse logistics manager | 3 | Returns dashboards | Return driver analysis, regulation lookup |
| 64 | 16 | Last-mile delivery manager | 3 | Courier portals, delivery reports | Failed-delivery driver analysis, city regulation research |
| 65 | 11 | Transport planner | 3 | TMS and route optimiser | Cost variance diagnosis, disruption research on lanes |
| 66 | 13 | Air freight coordinator | 3 | Booking and tracking systems | Air-vs-delay trade-off, recurring-expedite root cause |
| 67 | 6 | Warehouse manager | 3 | WMS/LMS KPI dashboards | Cost-per-unit drivers, capacity decisions, benchmarks |
| 68 | 8 | WMS analyst | 3 | WMS admin, slotting tool | Stuck-order debugging, vendor docs lookup |
| 69 | 10 | Automation/robotics engineer | 3 | SCADA, CMMS | Fault pattern diagnosis, manual and release note lookup |
| 70 | 9 | Health & safety officer | 3 | Incident system, training records | Incident root-cause patterns, regulation lookup |
| 71 | 53 | Technical designer/garment technologist | 3 | Tech pack, fit notes | Fit issue patterns from returns, standards lookup |
| 72 | 59 | Product data/PIM specialist | 3 | PIM completeness reports | Listing rejection diagnosis, marketplace rule research |
| 73 | 83 | ERP/systems integrator | 3 | Integration monitor, interface logs | Failure diagnosis, partner spec lookup |
| 74 | 85 | Cybersecurity analyst | 3 | SIEM, scanners | Incident scoping, threat research, attack path reasoning |
| 75 | 89 | HR/workforce planner | 3 | HRIS, labour management | Turnover/absence drivers, labour market research |

### Tier 2: UI-first (ranks 76–86)

| Rank | # | Persona | Score | Keep in a UI/tool | Where AI earns its place |
|---|---|---|---|---|---|
| 76 | 26 | Allocator/distribution analyst | 2 | Allocation system | Post-mortem on underperforming allocation |
| 77 | 18 | Port/drayage coordinator | 2 | Port systems, free-time calendar, container tracking | Why a container is stuck, port conditions research |
| 78 | 17 | Fleet manager | 2 | Telematics, maintenance schedule | Fleet replacement business case, regulation research |
| 79 | 15 | Import/export documentation clerk | 2 | Document system, e-filing portals | Cross-document mismatch checks, country requirement lookup |
| 80 | 64 | Accounts payable clerk | 2 | AP matching and payment workflow | Explaining mismatches, spotting duplicate or fraud patterns |
| 81 | 76 | Customer service agent | 2 | Helpdesk, order tracking, returns portal | Policy and rights lookup, complex complaint root cause |
| 82 | 86 | Master data analyst | 2 | MDM tool, data quality reports | Conflicting-source resolution, standards lookup |
| 83 | 84 | IT service desk/support | 2 | Ticketing, knowledge base | Obscure error lookup, recurring issue patterns |
| 84 | 5 | Shift supervisor (DC) | 2 | Live LMS/WMS dashboards, rota | Shift productivity post-mortems |
| 85 | 3 | Goods-in/receiving clerk | 2 | Receiving screens, dock schedule | Recurring supplier or carrier problem patterns |
| 86 | 57 | Sample room coordinator | 2 | PLM sample tracker, courier tracking | Delay root cause, customs requirements for samples |

### Tier 1: UI-only (ranks 87–90)

| Rank | # | Persona | Score | Keep in a UI/tool | Where AI earns its place |
|---|---|---|---|---|---|
| 87 | 7 | Returns processing operative | 1 | Returns screen, grading guide | Little. Occasional category disposal rule lookup |
| 88 | 72 | Store replenishment/back-room associate | 1 | Handheld, manifests, planogram | Little. Rare unexplained stock-location puzzles |
| 89 | 2 | Forklift/MHE operator | 1 | Truck terminal, task queue, checklists | Essentially none |
| 90 | 1 | Warehouse picker/packer | 1 | Scanner, pick list, SOP | Essentially none |

---

## Generic cases that serve many roles (worth building once as AI patterns)

These recur across tiers 3–5. They are good candidates for shared, well-tested AI capabilities.

1. **Variance explanation.** "Why did X move vs plan / last period?" Seen in finance, planning, warehouse, store, procurement and logistics roles.
2. **Cross-source anomaly and pattern analysis.** Stock adjustments, invoices, incidents, returns, claims. Shrink analysis is the model case.
3. **Document and contract reading.** Supplier contracts, audit reports, specs, test reports, partner specifications, policies.
4. **External change monitoring.** Regulation, tariffs, port and carrier notices, commodity and market news, competitor moves, supplier financial health.
5. **Benchmark and market research.** Rates, wages, costs, prices, peer performance.
6. **Scenario and what-if narrative.** Tariff, FX, capacity, supplier-loss and demand scenarios, built on numbers from the existing models.
7. **Drafting and summarising.** Supplier comms, steering committee options, recall notices, customer replies, board narratives.
8. **Ad hoc data wrangling.** One-off questions that need joining exports from several systems when no report exists.

## Questions that should be routed to a tool, not AI

When the system of record answers it directly, AI Q&A is slower and riskier. Examples from the question sets:

| Question | Better answered by |
|---|---|
| What is my pick list and which items are priority? | WMS/handheld |
| Where is item X located? | WMS location lookup |
| What are the packaging dimensions, weight and stacking limit for this item? | Item master / WMS |
| Which trucks are due today and in what order? | Dock appointment schedule |
| Where is this shipment or container now? | Carrier or visibility tracking |
| Which invoices are unmatched or due for payment? | AP workflow queue |
| What is current inventory by age, location and value? | Inventory report |
| Which safety training or certificates are expiring? | HR/training system report |
| Which contracts are expiring in 6–12 months? | Contract repository filter |
| Which customers are overdue and by how much? | AR ageing report |
| How are KPIs tracking vs target today? | Dashboard |
| What is this customer's order status? | Order management system |

If an AI agent receives one of these, the ideal behaviour is to point to the right tool, or fetch the value from it, rather than reason about it.

## Implications for the benchmark

- **Weight question sets by tier.** Most AI-suited questions should come from tiers 5, 4 and 3. Tiers 1–2 need only a handful each.
- **Include "should not use AI" cases.** For tiers 1–2, and for the UI-style questions in the table above, include test cases where the correct behaviour is to route to a tool or decline to guess.
- **Test hybrid chains.** For tier 3, build questions that start from a known report and ask AI to explain or investigate it (UI number, then AI reasoning).
- **Check the extremes.** If a tier 1 persona scores highly on an AI benchmark, the persona or questions are probably unrealistic.
