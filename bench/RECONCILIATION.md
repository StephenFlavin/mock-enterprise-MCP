# Open reconciliation items

Every system passes `check` and `bench --validate` and every question slice has a case. The items below are the
cross-system inconsistencies that remain. Each needs a design decision or is a legitimate difference between slices.

## Decisions needed
- **Scale.** Master has about £180m sales and £210m purchases a year, with per-SKU sales up to about 400/week. The finance
  systems (budgeting, gl, cost_allocation, consolidation, treasury) assume about £1.2bn revenue. Several operational
  stories are seeded above the master rates. The choice is to scale master sales up (every generated volume shifts) or
  to scale finance down.
- **Sorter age.** Questions say DC1's sorter AST-DC1-SRT is about 12 years old. Master installs it in 2018.
- **Corby workforce.** Corby is DC6, but master has no DC6 employees, so the hris and lms Corby stories run on DC2.
  Store staff exist only in store_wfm (STF ids), because master has one manager per store.
- **Data reproducibility.** Some `data/*.csv` files were patched directly to avoid generator drift (tms air_freight,
  data_warehouse, qms, reviews, ims). `data/` is the source of truth. Regenerating a system against the current master
  shifts some facts.

## Remaining id differences per question
A cross-system id check finds 40 question x entity-type differences remain (down from 100).
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
