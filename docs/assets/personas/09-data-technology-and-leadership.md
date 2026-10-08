# 09 · Data, Technology and Leadership

Personas 81–90. Questions each role needs to answer to do their job.

**Question types:** `MONITOR` what is happening now · `DIAGNOSE` why it happened · `FORECAST` what will happen · `DECIDE` what to do · `RESEARCH` external or reference lookup

---

## 81. Data analyst (supply chain)
**Focus:** Dashboards and ad hoc analysis to answer operational questions.
**Tools/data:** SQL, BI tools, data warehouse, ERP/WMS/TMS extracts, spreadsheets.

- `MONITOR` What are the current values and trends of key supply chain KPIs (OTIF, inventory days, cost per unit, lead time)?
- `DIAGNOSE` Why did this metric move, and which dimension (supplier, lane, SKU, site) explains most of it?
- `DECIDE` Which data source is the authoritative one for this metric, and why do reports disagree?
- `FORECAST` What does the trend suggest for next month?
- `RESEARCH` What definitions or benchmarks should we use for this KPI?

## 82. Data scientist
**Focus:** Build forecasting, optimisation and anomaly models.
**Tools/data:** Python/R, ML platforms, feature stores, experiment tracking, historical data.

- `DECIDE` Which modelling approach fits this problem (demand, ETA, lead time, price, anomaly) and what features matter?
- `DIAGNOSE` Why did the model's accuracy degrade (drift, data change, new behaviour)?
- `FORECAST` What uplift does the model give versus the current process, and is it worth deploying?
- `RESEARCH` What methods and open-source tools are state of the art for this use case?
- `MONITOR` Are models performing as expected in production, and what is the data quality?

## 83. ERP / systems integrator
**Focus:** Connect systems: EDI, APIs and master data flows.
**Tools/data:** Integration platform, EDI messages, ERP configuration, interface logs, API documentation.

- `MONITOR` Which interfaces or EDI messages failed or are delayed, and what is the business impact?
- `DIAGNOSE` Why did this message fail (mapping, format, missing master data, partner change)?
- `DECIDE` What is the best way to integrate this new partner, system or process?
- `RESEARCH` What do the vendor and partner specifications say about this message or API?
- `FORECAST` What load and capacity will integrations need during peak?

## 84. IT service desk / support
**Focus:** Keep users working: access, outages and requests.
**Tools/data:** Ticketing system, knowledge base, identity management, monitoring tools, remote support tools.

- `MONITOR` What are the open tickets, their priority and SLA status, and is any outage affecting sites?
- `DIAGNOSE` Is this fault caused by user error, device, network, access rights, or a system outage?
- `DECIDE` What is the fix or workaround, and does this need escalation?
- `RESEARCH` What does the knowledge base or vendor documentation say about this error?
- `MONITOR` What recurring issues should be fixed permanently?

## 85. Cybersecurity analyst
**Focus:** Protect systems and data, including supplier and partner access.
**Tools/data:** SIEM, vulnerability scanners, threat intelligence, identity logs, third-party risk tools.

- `MONITOR` What alerts, anomalies and vulnerabilities need attention now, ranked by risk?
- `DIAGNOSE` Is this event a real incident, what is the scope, and how did it get in?
- `DECIDE` Which supplier and partner connections pose the highest risk and what controls are needed?
- `RESEARCH` What threats and vulnerabilities affect our software, vendors and sector at the moment?
- `FORECAST` What are the likely attack paths and business impact of a successful ransomware attack on our warehouses or ERP?

## 86. Master data analyst
**Focus:** Keep item, supplier and location data clean and consistent.
**Tools/data:** MDM/ERP master data tools, data quality reports, workflows, spreadsheets.

- `MONITOR` Which master data records are incomplete, duplicated or inconsistent, and what does this cost operationally?
- `DIAGNOSE` Why is this item failing in the WMS, TMS or planning (dimensions, weight, unit of measure, lead time)?
- `DECIDE` Which record is the correct one when sources conflict, and who owns it?
- `RESEARCH` What are the standards (GS1, classification) and rules for this attribute?
- `MONITOR` How is data quality improving and what are the largest remaining issues?

## 87. Chief supply chain officer
**Focus:** Supply chain strategy, resilience and cost-to-serve.
**Tools/data:** Executive dashboards, strategy models, board materials, supplier and partner leadership.

- `MONITOR` How is end-to-end supply chain performance on service, cost, inventory, risk and sustainability?
- `DECIDE` What are the strategic priorities and investments (nearshoring, automation, network, dual sourcing) for the next 3 years?
- `FORECAST` How resilient are we to major disruption and what would it cost us?
- `RESEARCH` What are best-in-class retailers and industry leaders doing in supply chain strategy and technology?
- `DIAGNOSE` Where are the biggest structural inefficiencies in the end-to-end chain?

## 88. COO / operations director
**Focus:** Network performance, capex and operational delivery.
**Tools/data:** Operational KPI packs, capex and project reports, site visits, vendor management.

- `MONITOR` How are all sites and operations performing against service, cost, safety and quality targets?
- `DIAGNOSE` What is causing the underperformance at specific sites or functions?
- `DECIDE` Which capex projects and operational changes should be approved, delayed or stopped?
- `FORECAST` What capacity, headcount and cost will we need for next peak and next year?
- `RESEARCH` How do our operations compare to industry benchmarks?

## 89. HR / workforce planner
**Focus:** Seasonal labour, agency staff and retention.
**Tools/data:** HRIS, labour management system, agency data, volume forecasts, recruitment pipeline.

- `FORECAST` How many people and which skills do we need by site and week, based on volume forecasts?
- `MONITOR` What are attrition, absence, agency use and time-to-hire by site?
- `DIAGNOSE` Why is turnover or absence high at a site (pay, shift pattern, management, location)?
- `DECIDE` Should we hire, use agency, offer overtime, or automate to meet peak demand?
- `RESEARCH` What are local wage rates, labour market conditions and employment law changes?

## 90. Programme / transformation manager
**Focus:** Deliver large change: ERP, automation, new DC.
**Tools/data:** Programme tools, RAID logs, budgets, vendor plans, stakeholder reports.

- `MONITOR` Is the programme on track for scope, schedule, budget and benefits, and what are the top risks and issues?
- `DIAGNOSE` Why is a workstream behind and what is blocking it?
- `DECIDE` Which trade-offs (scope, date, cost, resources) should we recommend to the steering committee?
- `FORECAST` What is the likely completion date and final cost at current progress?
- `RESEARCH` What lessons and benchmarks exist from comparable programmes and vendor implementations?
