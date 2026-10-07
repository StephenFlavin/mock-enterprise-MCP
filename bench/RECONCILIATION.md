# Open reconciliation items

Every system passes `check` and `bench --validate` and every question slice has a case. The items below are the
cross-system inconsistencies that remain. Each needs a design decision or is a legitimate difference between slices.

## Decisions taken
- **Scale.** Master is now a ~GBP 1.2bn business: sales volumes x6.8 (revenue ~GBP 1,201m), PO quantities x2.2
  (purchases ~GBP 447m ~ cost of goods), supplier annual spend derived from the last 12 months of POs. dc_stock is
  unchanged (~19 weeks cover); the online `orders` table and returns built on it are a sample, not every order.
- **Sorter.** AST-DC1-SRT installed 2014-10-06 (about 12 years old), via systems/_master/seed/assets.csv.
- **Corby workforce.** Left on DC2 (Daventry) stand-ins; the questions are answerable as is.
- **Reproducible bring-up / tear-down.** `data/` is exactly what gen.py + seed/ produce (`gen --verify`, run by
  `check`); generators use per-entity streams (`g.rng_for`) where master growth would shift rows and never read the
  wall clock; the write overlay is a per-process temp dir removed on exit (`MOCKMCP_STATE` to persist).

## Known small mismatches after the scale-up
- bi says ST144 is 8% ahead of plan; store_ops has it slightly behind. bi's non-story store totals differ from store_ops (no tool exposes them).
- store_wfm labour_costs.sales_value (~GBP 30k/week at ST214) is below store_ops (~GBP 76k/week); percentages agree.
- mfp open-to-buy (GBP 2.1m) and UK North period plan (GBP 6.9m) are small for a GBP 1.2bn business; prompts state them.
- inv_opt ranks SKU-101617 8th for centralisation, while supplier_portal lists it among the five make-to-order candidates.
- demand and supply_planning differ by 5 units on the haircare promotion shortfall (2,571 vs 2,566).
- esg priority score weights are 0.7 emissions / 0.1 spend / 0.2 readiness so the emissions story leads.

## Remaining id differences per question
A cross-system id check finds 42 question x entity-type differences (down from 100 before reconciliation).
Most are different slices of one question (e.g. a candidate list vs the chosen supplier).

## Known minor mismatches (by persona)
- p01: scale mismatch gl/lms (DC1 ~3.4m units/month) vs wms/demand from master (~65k units/week all DCs) - needs master/finance scale decision
- p01: sorter AST-DC1-SRT install 2018 vs ~12 yrs (master fix)
- p01: "two newest sites" = DC3/DC4 vs master DC6-8 (reworded)
- p01: agency early/late rates rate card vs lms; yms booking Tue vs PO due Mon; wifi itsm vs wcs
- p08: ims ST165 shrink story (EMP-00488) still used by 07:68:Q5 -> move to ST150 (ST150 adj rows INV-ADJ-900063..71 exist; don't duplicate)
- p08: ims top-20 availability list != ecommerce top sellers (tool change)
- p08: demand 2,148 vs supply_planning 2,200 extra units (method diff)
- p07: SCALE: master ~£176-191m sales/£210m purchases vs finance ~£1.2bn (demand vs budgeting, cost_allocation £3bn channel sales, returns/tms/ecommerce volumes, gl COGS)
- p07: treasury covenants (2.44x, £125m debt) vs EBITDA ~£126m
- p07: 62:Q1 costing bridge -1.09 vs question 1.4; markdown+shrink 0.17 vs mfp 0.77
- p07: 61:Q5 tms no miscoded vs ap/gl four; 63:Q1 landed_cost no duty change vs tax_duty 12->15%; 62:Q5 gl USD COGS vs fx exposure; 67:Q6 capex figures; gl FY27-08 static label
- p02: pallet network carrier not in master (CAR-001 stand-in); customs lithium fans HS8414 vs hero babywear; freight_rates 0.8kg vs master 0.53kg; announced rises exceed contract caps (intentional?)
- p02: tms air_freight.csv patched by script (gen.py has same logic but full regen drifts)
- p09: Corby workforce on DC2 (no DC6 employees in master; demand has no DC6); network roadmap naming differs (board/ppm/network_design); dependency direction; Turkey/Portugal nearshoring remains elsewhere; telematics £2.7m vs cost_model £2.9m; racking contracts by name not SUP-0090
- REPRO: several jobs patched data/*.csv directly (tms air_freight, data_warehouse, qms, reviews, ims) - a regen against current master would drift; consider regen-all + fact refresh as a final step, or accept data/ as source of truth
- p05: Vietnam 6-wk revenue risk/costing £1.06m vs supply_planning £3.8m; kpi circularity programme-wide vs pilots; recall 18,000 batch vs oms/ims units; factory_audit grades newer than master; PO-2026-006044 shipped (po) vs delivered (master)
- p03: supply_planning check 05:50:Q2 fails - new zero-stock master products show as first to run out in Vietnam closure output (filter status=new/launch>today)
- p03: demand scale: master sales ~33/wk SKU-104963 vs ims story 276/wk; biggest master sellers ~400/wk (no 800/wk item); "Corby Enterprise Park" shortlist vs DC6
- p06: recycled poly premium commodity 18% vs costing ~10%; padded-jacket benchmarks costing vs cost_model; jeans stand-in SKU-100637; data_warehouse sales vs master for SKU-103640/101876; landed_cost vs tax_duty tariff contingency; master lunch box supplier SUP-0004/FAC-0008 not on shortlist; SS27 master launch dates past
- p06: qms-04:34:Q6 '0.8' weekday-dependent (Sun)
- p04: vendor-duplicate story ids outside master differ (mdm/documents/spend/ap); Sunrise Pack prospect not in master (PSP-0001/SUP-0023); wool coat master CN vs Vietnam/Portugal comparison; contract vs quote terms (negotiation); indirect master spend 0
- remaining fails after recon: reviews 06:52:Q6 + 03:25:Q5 (weekday), ap 08:79:Q1, supply_planning 05:50:Q2 (new products in port-closure)
