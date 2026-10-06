# Questions 03 · Planning and Inventory

AI-suited personas only (score 3+). Questions are written the way real users ask them: some vague, some precise; some short, some long; some narrow, some broad. Follow-ups show how a conversation could realistically continue, including clarifications, corrections and scope changes.

**Type tags:** `MONITOR` · `DIAGNOSE` · `FORECAST` · `DECIDE` · `RESEARCH`
**Shape tags (after the type):** specificity (`vague` / `partial` / `specific`) · scope (`narrow` / `wide`) · complexity (`simple` / `moderate` / `complex`)

---

## 22. Stock planner / replenishment analyst (AI score 3)

**Q1 · DIAGNOSE · specific · narrow · complex** Style 5520 stocked out in 40 stores for nine days last month even though the forecast looked fine. Reconstruct what happened: forecast by week, orders placed, supplier confirmations, receipts, DC stock and allocations to stores. Tell me whether it was a forecast miss, a late supplier or an allocation decision, what it cost us in sales, and which setting or process would have prevented it.
- ↳ How many of the 40 stores had stock at the DC level but didn't get it?
- ↳ What parameter change would you make, and what would it do to inventory?
- ↳ Once I agree the setting, update the safety stock on 5520 to what you'd recommend.

**Q2 · MONITOR · vague · wide · simple** I've just come back from two weeks off and the weekly stock report is a wall of numbers. What's about to run out? I mean across all SKUs over the next four weeks, ranked by margin and sales at risk, and I need to know which ones still have supply I can expedite before it's too late. Once I've picked, expedite the top five, but show me the requests before anything goes to suppliers.
- ↳ Which of those have supplier stock available now?
- ↳ Anything that looks like a system error rather than a real risk?
- ↳ Actually, only expedite the ones where the supplier has stock available now.

**Q3 · DECIDE · partial · wide · moderate** Review the reorder points and safety stock for the 200 fastest sellers. Which look too low or too high given demand variability and supplier lead times?
- ↳ What would the working capital change be?
- ↳ Which suppliers' lead times have changed since the parameters were set?
- ↳ Update the reorder points on the ones that are clearly too low, but leave the too-high ones for now.

**Q4 · DECIDE · specific · narrow · moderate** 14,000 units of a seasonal throw sit at the DC. Northern stores are selling out and southern ones are overstocked. Is a rebalance worth it? If it is, create the transfer.
- ↳ Transfer cost versus the sales we'd capture.
- ↳ How many selling weeks are left?
- ↳ Actually only the northern stores with less than a week of cover.

**Q5 · DIAGNOSE · vague · wide · moderate** Why is our out-of-stock rate up?
- ↳ 4% to 6.5% in a month.
- ↳ Split by category, supplier and DC.
- ↳ Which causes are one-offs and which will persist?

---

## 23. Demand planner (AI score 4)

**Q1 · DIAGNOSE · partial · narrow · moderate** Outerwear forecast bias was +18% last month. Decompose it by weather, promotion, pricing, store cluster and new launches.
- ↳ Was the weather effect something we could have seen coming?
- ↳ How should the model change?
- ↳ Is the same bias showing in other markets?

**Q2 · FORECAST · specific · narrow · complex** Forecast demand for the new recycled-polyester backpack range launching 12 January. Use sales of comparable bags, search trend data, the marketing plan (attached: Q1_marketing_plan.pdf) and the price positioning. Give me a base case and a range, weekly for the first 12 weeks, and tell me which early-sales signals in weeks 1 to 3 should trigger chasing or cancelling stock.
- ↳ Which comparable products did you weight most and why?
- ↳ How quickly can we tell if early sales are off track?
- ↳ Load the base case into the forecast and set an alert for the week 1 to 3 triggers.

**Q3 · RESEARCH · vague · wide · simple** What outside factors should I take into account for the winter forecast? UK and Germany, and tell me how big they were in previous years so I can turn the key ones into category adjustments.
- ↳ Which of those are already in the model?
- ↳ Which would you ignore?

**Q4 · DECIDE · specific · narrow · simple** What uplift should I assume for 25% off kitchenware in week 47?
- ↳ How much is cannibalisation versus incremental?
- ↳ What was the dip afterwards last time?
- ↳ Put that uplift into the week 47 forecast for kitchenware.

**Q5 · DIAGNOSE · vague · narrow · moderate** Did stockouts distort last quarter's history? Correct the history for the worst ones.
- ↳ Which items, and how many units of demand did we lose?
- ↳ How should I correct the history so the model doesn't under-forecast?
- ↳ Don't touch the items that were delisted.

**Q6 · FORECAST · vague · wide · moderate** If cost-of-living pressure gets worse in Q1, what happens to demand? Which categories hold up best, and how should I feed it into the S&OP discussion?
- ↳ How did we do in the last squeeze?
- ↳ What's a reasonable downside adjustment?
- ↳ Create the downside scenario in S&OP so we can discuss it.

---

## 24. Supply planner (AI score 3)

**Q1 · DIAGNOSE · specific · narrow · moderate** Supplier X has missed its confirmed ship date on 6 of the last 10 orders. Look at the order history, their capacity information and anything public about them. What's going on and is it getting worse?
- ↳ How much of next quarter's supply depends on them?
- ↳ What are the alternatives and their lead times?
- ↳ If it's getting worse, put a hold on new orders to them, but ask me before you do it.
- ↳ Set up a performance review with their account manager.

**Q2 · DECIDE · specific · narrow · complex** There's a 25,000-unit gap between demand and confirmed supply in week 44 on the core denim range. Options are expediting from the current mill, splitting with a second supplier, or shifting promotion timing. Compare them on cost, service level and risk using current capacity data and lead times, and tell me which suppliers actually have capacity right now. Once I've picked, raise the PO.
- ↳ What would each option cost per unit above plan?
- ↳ What if the second supplier needs two weeks to qualify?
- ↳ Actually, split it 60/40 rather than 50/50.
- ↳ Release the PO once finance has approved it.

**Q3 · RESEARCH · vague · wide · simple** Any shortages in zips and trims I should know about? It matters for Q1 production, so tell me which of our open orders use them and whether we should buy ahead.
- ↳ Which suppliers have already flagged delays?
- ↳ What's the cost of buying ahead?
- ↳ Place a buy-ahead order for the zips, once I've seen the cost.

**Q4 · FORECAST · partial · wide · moderate** Any fabric shortages coming?
- ↳ Which categories are most exposed?
- ↳ Which suppliers are most at risk?

**Q5 · DIAGNOSE · partial · wide · moderate** Suppliers' quoted lead times are consistently about 10 days shorter than what we actually get. Quantify the gap by supplier and what it does to stock and service. Then update the planning lead times for the worst offenders.
- ↳ Which suppliers have the worst gap?
- ↳ If we change the planning lead times, what happens to inventory?
- ↳ Leave the strategic suppliers as they are for now.

---

## 25. Merchandise planner (AI score 3)

**Q1 · DIAGNOSE · specific · narrow · moderate** Women's knitwear margin was 3.2 points below plan last month. Split it into price, cost, mix, markdown and shrink.
- ↳ Which of those were avoidable?
- ↳ What does the rest of the season look like if nothing changes?
- ↳ Which actions recover the most?

**Q2 · DECIDE · partial · wide · complex** We have £2.1m of open-to-buy for spring. Based on current trends, sell-through and risk, how should I split it across categories? Show an optimistic and a cautious case and how much I should hold back for in-season chases.
- ↳ What assumptions drive the difference between the two cases?
- ↳ Which category would you cut first if sales soften?
- ↳ Update the open-to-buy allocations to the cautious case and keep the reserve unallocated.

**Q3 · FORECAST · vague · wide · moderate** The autumn range is selling but not at the rate we planned, and I'm getting nervous about where we end the season. If current sell-through and markdown trends carry on, where do we land on closing stock and markdown cost? I'd like to know which lines are most at risk and what earlier markdowns would change. Cancel the open orders on the lines I should stop reordering, after checking with me.
- ↳ What would earlier markdowns do to margin?
- ↳ Which lines should I stop reordering now?
- ↳ Actually, keep the orders that are already in transit.

**Q4 · RESEARCH · vague · wide · simple** Where will we end the season on stock?
- ↳ Which gap is the best opportunity?
- ↳ What data is that based on?
- ↳ Flag the categories that will end heavy for an early markdown review.

**Q5 · DIAGNOSE · specific · narrow · moderate** Our new athleisure range is 20% behind plan on sell-through. Is it the product or how we bought and distributed it? Check price, availability, size curve, marketing and competitors.
- ↳ What would you change for the next buy?
- ↳ Which stores underperformed most?
- ↳ Move stock from the weakest stores to the strongest ones.

---

## 27. S&OP lead (AI score 4)

**Q1 · MONITOR · partial · wide · moderate** What changed in the demand, supply and finance assumptions since last month's S&OP, who changed them, and why? Send it to the attendees once I've approved it.
- ↳ Which changes have the biggest effect on revenue and inventory?
- ↳ Which are still disputed?
- ↳ Turn this into the pre-read.

**Q2 · DECIDE · specific · wide · complex** Compare three scenarios for Q4: (a) hold the current plan, (b) lift stock by 10% on key lines, (c) cut promotions in weeks 47 to 49. Show revenue, margin, service level and cash for each, state the main assumptions, and tell me which has the best risk-adjusted outcome and what would trigger a switch. I'll be presenting this to the exec at Thursday's S&OP.
- ↳ Which assumptions are weakest?
- ↳ What would scenario (b) do to cash if sales come in 5% under?
- ↳ Book 30 minutes with finance before Thursday and attach the scenarios.

**Q3 · FORECAST · vague · wide · moderate** What are the biggest risks to the next six months across demand, supply and cost? Give me the financial exposure of each and tell me which we can mitigate now.
- ↳ Which risks are correlated?
- ↳ Which would you escalate first?
- ↳ Log the top three in the risk register.

**Q4 · RESEARCH · vague · wide · simple** Any macro news we should reflect in next month's plan?
- ↳ How have similar retailers been affected?
- ↳ Which of it is already in the forecast?

**Q5 · DIAGNOSE · partial · narrow · moderate** New-product forecast accuracy has been poor for three S&OP cycles. Which assumptions are consistently wrong, and what process changes would fix it?
- ↳ Is it demand, timing or distribution assumptions?
- ↳ Which launches were worst?

**Q6 · DECIDE · partial · wide · moderate** Where should we set service level versus inventory for the top 10% of SKUs compared with the long tail?
- ↳ What does the evidence say about how customers respond to availability?
- ↳ Which segments would you protect?
- ↳ Update the service level targets for the top segment to what you suggest, once I agree.

---

## 28. Inventory optimisation analyst (AI score 3)

**Q1 · DECIDE · specific · wide · complex** Calculate safety stock for our 500 highest-value SKUs at a 97% service level using the last two years of demand and lead-time variability. Compare against current settings, show the working capital change by category, and flag SKUs where variability is unusually high and why. Once I've signed off, update the settings.
- ↳ What does it look like at 95% and 99%?
- ↳ Which SKUs should be excluded from statistical safety stock altogether?
- ↳ Apply the 97% setting only to the A items, not the rest.

**Q2 · DIAGNOSE · partial · narrow · moderate** We hold 120 days of cover on home textiles against a 75-day target. What's driving it?
- ↳ Minimum order quantities, forecast bias or delivery timing?
- ↳ Which SKUs make up 80% of the excess?
- ↳ Cancel the open POs on the SKUs driving the excess, but list them for me first.

**Q3 · FORECAST · vague · wide · moderate** What if lead times from Asia get two weeks longer? Which categories are most sensitive, and is it cheaper to hold more stock or accept lower availability?
- ↳ What's the working capital cost of the extra stock?
- ↳ Which categories would you protect first?

**Q4 · DECIDE · vague · wide · moderate** We carry a lot of stock for long-tail items that sell a few units a week, and I keep being asked whether we should hold some of it centrally, or make it to order instead. I haven't done the analysis. Which products should we hold centrally or make to order, what are the service and transport trade-offs, and what would it save?
- ↳ Which categories look most suitable?
- ↳ What would customers notice?
- ↳ Switch the best five candidates to make to order.

**Q5 · MONITOR · vague · narrow · simple** Where is our cash tied up in stock?
- ↳ By age, category and location.
- ↳ Which areas are above normal?
- ↳ Plan to release it?
- ↳ Create the stock release plan for the top three areas.

---

## 29. Markdown / clearance analyst (AI score 3)

**Q1 · DIAGNOSE · specific · narrow · simple** The 30% markdown on men's jackets didn't move stock. Why?
- ↳ Is what's left mostly broken size runs?
- ↳ What would a different depth have done?
- ↳ Take it to 40% on what's left, but check with me before it goes live.

**Q2 · DECIDE · specific · wide · complex** I have 40 aged lines (attached: aged_lines.xlsx). For each, recommend whether to mark down, move to outlet, bundle, donate or liquidate to maximise recovery, with the expected margin per option and the effect on full-price sales of similar items. Give me the top 10 by value first. Then create the markdown events for the ones you say to mark down.
- ↳ Which channels fit each group best?
- ↳ What happens to the plan if I only get one more price change?
- ↳ Create outlet transfers for the ones going to outlet.

**Q3 · FORECAST · partial · narrow · complex** What sell-through and margin do I get with 20% off in week 3 versus 40% in week 6?
- ↳ How reliable is the elasticity data for this category?
- ↳ What's the risk of training customers to wait?
- ↳ Schedule the better option as a markdown event for the jackets.

**Q4 · RESEARCH · vague · wide · simple** What are competitors doing on clearance right now? I'd like to see where we're out of line on depth and timing for similar categories.
- ↳ Which competitors are most aggressive?
- ↳ How are they communicating it?

**Q5 · DECIDE · vague · wide · simple** Where should I focus on old stock? Queue the markdowns for the top group.
- ↳ Everything older than 180 days, ranked by recovery potential.
- ↳ Which channel suits each group?
- ↳ Actually, delete the second event and send that group to outlet.

---

## 30. Planning systems analyst (AI score 3)

**Q1 · DIAGNOSE · specific · narrow · moderate** The system proposed an order of 12,000 units for an item that sells about 800 a week. Trace the calculation and find what caused it. Then cancel that proposal.
- ↳ Promotion flag, lead time, history spike or pack size?
- ↳ Which other items could have the same issue?
- ↳ Correct the planning parameter that caused it.

**Q2 · DIAGNOSE · partial · wide · complex** Which forecasts should I distrust?
- ↳ Did a configuration default change?
- ↳ Roll back or tune?
- ↳ Roll back the config change, but check with me before it's applied.

**Q3 · RESEARCH · vague · wide · simple** Our forecasts for new and intermittent items are always the weakest part of the process. What do other retailers use for those, does our vendor's platform support it, and what evidence is there that these methods produce real gains rather than just better-looking backtests?
- ↳ Which method would you try first?
- ↳ What would a pilot need?

**Q4 · DECIDE · partial · wide · moderate** For slow movers, should we forecast at store-SKU level or at cluster level? Compare accuracy and effort using our data.
- ↳ How would that change replenishment performance?
- ↳ What would the accuracy difference be?

**Q5 · FORECAST · specific · narrow · simple** What happens to accuracy if the history window goes from 52 to 26 weeks for fashion?
- ↳ Which categories would benefit and which wouldn't?
- ↳ Which categories would lose most?
- ↳ Set up the 26-week window as a test configuration for fashion.

---

## 31. Network planner (AI score 4)

**Q1 · DECIDE · specific · wide · complex** We're considering a second DC in the Midlands. Compare keeping a single DC at Northampton, a second owned DC in the Midlands, and a third-party partner on total cost, delivery times to stores and customers, and resilience over five years. State the main assumptions and which are most uncertain, give the break-even volume, and show how it changes if e-commerce reaches 40% of sales.
- ↳ What's the sensitivity to a 15% rent increase?
- ↳ What would the transition look like during peak?

**Q2 · FORECAST · vague · wide · moderate** What volumes should the network handle in 2030? Split by region and channel, and show what a growing e-commerce share does to it.
- ↳ How sensitive is it to adding a new market?
- ↳ What assumptions matter most?

**Q3 · RESEARCH · partial · narrow · moderate** Compare industrial property availability, rents, labour costs and incentives in the three shortlisted sites, and flag the main risks with each such as labour supply, transport links and planning.
- ↳ How are other retailers in the area doing?
- ↳ Which site would you drop first?
- ↳ Remove the weakest site from the shortlist.

**Q4 · DIAGNOSE · vague · wide · moderate** I think the network is less efficient than it should be but I can't point to exactly where. Can you look at cross-shipping, split orders, long hauls and underused sites and tell me where the biggest inefficiencies are, what fixing the top three would cost, and how much of it is about inventory placement rather than where the sites are?
- ↳ Which one would you fix first?
- ↳ How confident are you in the cost estimate?
- ↳ Create a project to deliver the top three fixes.

**Q5 · DECIDE · partial · narrow · complex** Should we close the small southern DC and consolidate? Build the business case including redundancy, transport and service impact. Send the draft to the CFO once I've reviewed it.
- ↳ What are the risks to peak resilience?
- ↳ What would a phased approach look like?

**Q6 · FORECAST · partial · wide · moderate** How resilient are we if one DC is offline for two weeks?
- ↳ How much extra inventory or capacity would cover it?
- ↳ Which DC is the single point of failure?
- ↳ Log it in the risk register and set an action to review buffer stock.
