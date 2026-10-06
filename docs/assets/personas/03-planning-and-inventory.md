# 03 · Planning and Inventory

Personas 22–31. Questions each role needs to answer to do their job.

**Question types:** `MONITOR` what is happening now · `DIAGNOSE` why it happened · `FORECAST` what will happen · `DECIDE` what to do · `RESEARCH` external or reference lookup

---

## 22. Stock planner / replenishment analyst
**Focus:** Keep the right stock in the right place; set reorder points and replenishment parameters.
**Tools/data:** Planning/replenishment system, stock and sales data, lead times, supplier open orders, store stock.

- `MONITOR` Which SKUs and locations are at risk of stockout in the next 2–4 weeks, and which are overstocked?
- `DIAGNOSE` Why did SKU X run out despite a forecast (forecast error, late supplier, wrong lead time, system parameter)?
- `DECIDE` What should the reorder point, order quantity and safety stock be for this item given its demand pattern and lead time?
- `DECIDE` Which stores should receive scarce stock first, and how should we rebalance between stores?
- `FORECAST` Given open orders and expected sales, what will the stock position be at week-end for key lines?

## 23. Demand planner
**Focus:** Produce an unbiased demand forecast including seasonality, promotions and launches.
**Tools/data:** Forecasting tool, sales history, promo calendar, pricing, weather, market and competitor data.

- `FORECAST` What is the expected demand by SKU, channel and region for the next 13 weeks and next season?
- `DIAGNOSE` Where and why was last period's forecast wrong (promo effect, weather, competitor action, stockouts masking demand)?
- `DECIDE` How much uplift should I assume for this promotion or launch, based on similar past events?
- `FORECAST` How will demand for a new product behave given comparable products and early sales signals?
- `RESEARCH` What external signals (macro trends, weather, events, social trends, competitor launches) should change the forecast?

## 24. Supply planner
**Focus:** Match supply to demand within capacity and lead-time constraints.
**Tools/data:** Supply planning system, supplier capacity, production schedules, open POs, inbound shipment data.

- `MONITOR` Where is there a gap between forecast demand and confirmed supply by week?
- `DECIDE` Which orders should be expedited, split, moved to another supplier, or deferred to close the gap?
- `DIAGNOSE` Why are suppliers missing confirmed delivery dates, and is capacity or material the constraint?
- `FORECAST` What will supplier capacity utilisation look like next quarter and where will we hit limits?
- `RESEARCH` What do suppliers' public notices, port conditions or material shortages say about upcoming risks to supply?

## 25. Merchandise planner
**Focus:** Plan range, buy budgets and open-to-buy to hit sales and margin targets.
**Tools/data:** Merchandise financial planning tools, sales and margin reports, range plans, buy plans, OTB reports.

- `MONITOR` How are sales, margin, stock and OTB tracking by department, category and season?
- `DECIDE` How should the remaining open-to-buy be allocated between categories, given trends and risk?
- `DIAGNOSE` Why is category margin or sell-through below plan (mix, pricing, markdowns, stock age, cost)?
- `FORECAST` What will be the end-of-season stock, sales and markdown requirement if current trends continue?
- `RESEARCH` Which categories or trends are growing in the market and should the range plan shift?

## 26. Allocator / distribution analyst
**Focus:** Split initial and in-season stock by store and channel.
**Tools/data:** Allocation system, store sales and stock, store clusters, size curves, capacity and display constraints.

- `DECIDE` How many units of each size/colour should each store get for the launch given store potential and capacity?
- `MONITOR` Which stores are selling out of key lines while others have excess?
- `DIAGNOSE` Why did allocation underperform in certain stores (wrong size curve, wrong cluster, late delivery)?
- `DECIDE` What is the best transfer or rebalancing plan, considering transfer cost and remaining selling time?
- `FORECAST` What will the sell-through by store be by end of season on current allocation?

## 27. S&OP lead
**Focus:** Run the monthly sales and operations planning process to a single consensus plan.
**Tools/data:** Planning outputs from demand, supply, finance; scenario tools; KPI packs; meeting decks.

- `MONITOR` What are the key gaps between demand, supply and financial plans this cycle, and by how much?
- `DECIDE` Which scenario (more stock, more capacity, change promotions, pricing) is the best trade-off of service, cost and cash?
- `DIAGNOSE` What assumptions changed since last cycle and who owns each decision?
- `FORECAST` What are the revenue, margin and inventory outcomes of each scenario?
- `RESEARCH` What market or macro events should be reflected in the plan?

## 28. Inventory optimisation analyst
**Focus:** Set safety stock and policies that balance service level and working capital.
**Tools/data:** Inventory optimisation tool, demand variability, lead time variability, cost and service data.

- `DECIDE` What safety stock minimises total cost for a target service level at each node?
- `DIAGNOSE` Which SKUs hold excess stock because of inflated parameters or lumpy ordering?
- `FORECAST` How would service level and inventory value change if lead time or variability changed?
- `DECIDE` Which items should be centralised, postponed or made-to-order to reduce stock?
- `MONITOR` What is current inventory by age, turn and days of cover, and where is the working capital trapped?

## 29. Markdown / clearance analyst
**Focus:** Time and size price reductions to clear stock at the best margin.
**Tools/data:** Markdown optimisation tool, sell-through data, price elasticity, stock age, competitor prices.

- `MONITOR` Which items have low sell-through or old stock and will miss the clearance deadline?
- `DECIDE` What depth and timing of markdown clears this item at the best margin?
- `FORECAST` What will sell-through and margin be under different markdown scenarios?
- `DIAGNOSE` Why did this markdown not work (price point, size broken, wrong stores, competitor price)?
- `DECIDE` Should we move, bundle, donate or liquidate stock instead of marking down further?

## 30. Planning systems analyst
**Focus:** Keep planning systems accurate and tuned.
**Tools/data:** Planning platform admin, forecast accuracy reports, master data, interface logs.

- `MONITOR` What is forecast accuracy and bias by category, horizon and model, and where has it degraded?
- `DIAGNOSE` Why does the system propose odd orders (bad lead time, wrong pack size, missing history, calendar error)?
- `DECIDE` Which model, parameters or hierarchy changes would improve accuracy?
- `FORECAST` What impact would a parameter or process change have before we roll it out?
- `RESEARCH` What do vendor releases and industry practice say about newer forecasting methods?

## 31. Network planner
**Focus:** Design the DC and flow network for cost, service and resilience.
**Tools/data:** Network modelling tools, volume and cost data, lease and labour cost data, customer location data.

- `DECIDE` How many nodes do we need, where, and what should flow through each (cost vs. delivery speed)?
- `FORECAST` What will volumes by region and channel be in 3–5 years and what capacity does that require?
- `DIAGNOSE` Where is the current network inefficient (cross-shipping, long hauls, underused sites)?
- `DECIDE` What is the business case for opening, closing, or re-purposing a site?
- `RESEARCH` What are property, labour, incentive and regulatory conditions in candidate locations?
