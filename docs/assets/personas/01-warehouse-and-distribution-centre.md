# 01 · Warehouse and Distribution Centre

Personas 1–10. Questions each role needs to answer to do their job.

**Question types:** `MONITOR` what is happening now · `DIAGNOSE` why it happened · `FORECAST` what will happen · `DECIDE` what to do · `RESEARCH` external or reference lookup

---

## 1. Warehouse picker/packer
**Focus:** Fulfil orders accurately and on time; handle exceptions and damaged goods.
**Tools/data:** Handheld scanner, WMS pick lists, label printer, SOP/work instructions.

- `MONITOR` What is my pick list for this wave and which items are highest priority (same-day, premium service)?
- `MONITOR` Where is item X located, and is there a faster pick path through my zone?
- `DIAGNOSE` The bin is empty but the system says stock exists. Where else could it be (overflow, adjacent slot, replenishment pending)?
- `DECIDE` This item is damaged. Do I repack, quarantine, or raise an exception, and what is the procedure for this product type?
- `RESEARCH` What are the packing and labelling requirements for this item (fragile, hazmat, batteries, liquids, export destination)?

## 2. Forklift/MHE operator
**Focus:** Move pallets safely; execute put-away and replenishment tasks.
**Tools/data:** Truck-mounted terminal, WMS task queue, rack location maps, equipment checklists.

- `MONITOR` Which replenishment tasks are most urgent because a pick face is about to run out?
- `DIAGNOSE` Why can't I put this pallet in its assigned location (occupied, wrong height, blocked, damaged rack)?
- `DECIDE` Where is the next-best location for this pallet given weight, height and product family rules?
- `MONITOR` Is my truck due for inspection, battery change or maintenance, and has the pre-use checklist been completed?
- `RESEARCH` What are the weight and stacking limits for this pallet type in this rack bay?

## 3. Goods-in/receiving clerk
**Focus:** Check inbound deliveries against POs and ASNs; get stock available quickly.
**Tools/data:** WMS receiving, ASN/PO data, dock appointment system, carrier paperwork.

- `MONITOR` Which trucks are due today, in what order, and which contain priority or promo stock?
- `DIAGNOSE` Quantity received does not match the ASN/PO. Is it a short-ship, an over-ship, a substitution, or a supplier labelling error?
- `DECIDE` Do I accept, reject or hold this delivery (damage, wrong item, expired shelf life, missing documentation)?
- `DIAGNOSE` Which supplier or carrier keeps delivering late, damaged or short, and what is the pattern?
- `RESEARCH` What are the contractual receiving tolerances and claims deadlines for this supplier?

## 4. Inventory control/cycle counter
**Focus:** Keep system stock equal to physical stock; investigate discrepancies.
**Tools/data:** WMS stock and transaction history, count schedules, adjustment reports, ERP.

- `MONITOR` Which locations or SKUs are due for a count, and which are highest value or highest risk?
- `DIAGNOSE` What transactions (picks, moves, adjustments, receipts) explain this variance for SKU X?
- `DIAGNOSE` Is a variance one-off human error, or a systematic process or system fault (e.g. unit-of-measure mismatch)?
- `DECIDE` Should this variance be adjusted, recounted, or escalated for investigation (shrink, theft, supplier short-ship)?
- `FORECAST` Which areas are likely to show high inaccuracy next quarter based on historic patterns?

## 5. Shift supervisor (DC)
**Focus:** Allocate labour, hit throughput targets, keep people safe.
**Tools/data:** Labour management system, WMS dashboards, order cut-off times, attendance and incident logs.

- `MONITOR` Are we on track to ship all orders before carrier cut-off, and where are the bottlenecks (pick, pack, load)?
- `DECIDE` How should I reallocate people across zones to clear the backlog given today's skills and absences?
- `FORECAST` What volume is coming in the next 4 hours and do I need overtime or agency labour?
- `DIAGNOSE` Why was productivity (units/hour) lower than target on this shift, and by team or process?
- `MONITOR` What safety incidents or near-misses occurred on this shift and what follow-up is outstanding?

## 6. Warehouse manager
**Focus:** Cost per unit, capacity, service levels, people and compliance.
**Tools/data:** WMS/LMS reporting, P&L, capacity models, 3PL/carrier scorecards, HR data.

- `MONITOR` How are we performing against KPIs (OTIF, order accuracy, cost per order, dock-to-stock time, utilisation)?
- `FORECAST` Will we run out of storage or labour capacity during peak, and when?
- `DIAGNOSE` Why did cost per unit rise month on month (labour, overtime, damages, rework, rent, energy)?
- `DECIDE` Should we add a shift, extend a lease, bring in temporary space, or move volume to another site?
- `RESEARCH` What are comparable benchmark costs, wage rates and productivity for similar sites in this region?

## 7. Returns processing operative
**Focus:** Inspect, grade and route returned items quickly to maximise recovered value.
**Tools/data:** Returns module in WMS/OMS, grading guidelines, RMA data, refurbishment queue.

- `DECIDE` What grade is this item (resell as new, open-box, refurbish, liquidate, recycle, destroy)?
- `MONITOR` Which returns are oldest and at risk of missing refund SLAs?
- `DIAGNOSE` Why is this return reason code common for this product (fit, quality, damage in transit, wrong item sent)?
- `DECIDE` Does this item have to be quarantined for safety, hygiene or regulatory reasons?
- `RESEARCH` What are the grading and disposal rules for this category in this country (e.g. electronics, cosmetics, textiles)?

## 8. Warehouse systems (WMS) analyst
**Focus:** Configure and optimise the WMS; slotting, rules and integrations.
**Tools/data:** WMS admin, SQL/BI tools, interface logs, slotting tools, process maps.

- `DIAGNOSE` Why are orders stuck in a status (allocation failure, interface error, missing master data)?
- `DECIDE` How should SKUs be re-slotted to reduce travel time based on velocity, cube and affinity?
- `FORECAST` What would happen to pick rates if we changed batching or wave rules?
- `MONITOR` Are interfaces between WMS, ERP, TMS and e-commerce running without error or delay?
- `RESEARCH` What features, patches or vendor best practices exist for this problem in our WMS version?

## 9. Health & safety officer
**Focus:** Prevent injuries; ensure legal compliance and audit readiness.
**Tools/data:** Incident reporting system, risk assessments, training records, inspection checklists, regulations.

- `MONITOR` What incidents, near misses and unsafe conditions have been reported, and by area, shift and type?
- `DIAGNOSE` What are the root causes and common contributing factors across recent incidents?
- `MONITOR` Whose safety training or equipment certification is expiring or overdue?
- `DECIDE` What controls should we introduce (layout, equipment, training) to reduce the highest risks?
- `RESEARCH` What do current regulations and codes of practice require for this activity or site type in this jurisdiction?

## 10. Automation/robotics engineer
**Focus:** Keep AS/RS, conveyors and robots running; improve reliability and throughput.
**Tools/data:** PLC/SCADA data, maintenance system (CMMS), fault logs, vendor manuals, spare parts inventory.

- `MONITOR` What is current uptime, throughput and fault rate for each system or machine?
- `DIAGNOSE` What are the root causes of recurring stoppages (jams, sensor faults, software errors)?
- `FORECAST` Which components are likely to fail soon based on wear, run hours and fault trends?
- `DECIDE` Is it better to repair, replace or upgrade this equipment, and what is the payback?
- `RESEARCH` What do vendor documentation, firmware release notes and other operators say about this fault or upgrade?
