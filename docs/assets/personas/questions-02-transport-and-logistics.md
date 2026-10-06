# Questions 02 · Transport and Logistics

AI-suited personas only (score 3+). Questions are written the way real users ask them: some vague, some precise; some short, some long; some narrow, some broad. Follow-ups show how a conversation could realistically continue, including clarifications, corrections and scope changes.

**Type tags:** `MONITOR` · `DIAGNOSE` · `FORECAST` · `DECIDE` · `RESEARCH`
**Shape tags (after the type):** specificity (`vague` / `partial` / `specific`) · scope (`narrow` / `wide`) · complexity (`simple` / `moderate` / `complex`)

---

## 11. Transport planner (AI score 3)

**Q1 · DIAGNOSE · partial · wide · moderate** Any lane disruptions this week?
- ↳ How much is fuel surcharge versus genuine rate increase?
- ↳ Which lanes lost the most fill rate?
- ↳ What would consolidating the three weakest lanes save?
- ↳ Reassign the two worst-hit loads to the backup carrier.

**Q2 · DECIDE · specific · narrow · complex** For the northern region (Leeds, Manchester, Newcastle and Glasgow drops), compare staying with our current three carriers against moving 40% of volume to a pallet network. Use last quarter's volumes and delivery windows (attached: north_loads_Q3.csv) and the carrier rate cards. I need total cost, expected on-time performance from their published numbers, and the contract terms we'd have to negotiate. Keep it to two pages.
- ↳ What does the pallet network's published performance look like at peak?
- ↳ If we trial it, which lanes should go first?
- ↳ Once I've signed it off, set the trial up as an allocation on the first lanes.

**Q3 · RESEARCH · vague · wide · simple** Anything likely to disrupt our main lanes before Christmas? I'm thinking strikes, road closures, border queues and driver shortages, and I'd like to know which of our shipments fall in those windows.
- ↳ What contingency should I line up?
- ↳ Which lanes are most exposed?
- ↳ Hold the three most exposed loads and reroute them, but check with me first.

**Q4 · FORECAST · partial · wide · moderate** How much transport capacity will we need for Black Friday and Christmas weeks by lane, and where are we exposed compared with what's contracted? Once I've agreed the numbers, ask the carriers for the extra capacity where we're short.
- ↳ What does it cost to secure the gap early versus on the spot market?
- ↳ Which lanes are most exposed?
- ↳ Only for the north region.

**Q5 · DIAGNOSE · specific · narrow · simple** Route plans say 94% utilisation but drivers keep running out of hours on the M62 routes. Why? Then re-plan the two worst.
- ↳ Unloading time, traffic or unrealistic stop-time assumptions?
- ↳ Which routes should I re-plan first?
- ↳ Increase the stop-time allowance at the slowest drops too.

---

## 12. Freight forwarder / ocean freight buyer (AI score 4)

**Q1 · RESEARCH · specific · narrow · simple** Current spot and contract rates for 40ft containers from Ho Chi Minh to Felixstowe, Rotterdam and Los Angeles, and the trend over the last 12 weeks?
- ↳ What's driving the movement?
- ↳ How do spot rates compare with our contract?
- ↳ What does the market expect for the next 8 weeks?

**Q2 · DECIDE · partial · wide · complex** Our contract with Carrier A expires in January. Using their schedule reliability and roll rates on our lanes over the last year, should we renew, cut their share or switch? Compare them with Carriers B and C, then draft the tender criteria and the reliability and rate terms we should ask for.
- ↳ What share would you give each if we kept all three?
- ↳ What penalties for rolled bookings are realistic to ask for?
- ↳ Issue the tender to B and C once I've approved the criteria.

**Q3 · FORECAST · vague · wide · moderate** Will rates spike before Lunar New Year?
- ↳ How did the last three years play out?
- ↳ How much should we fix on contract versus leave to spot?

**Q4 · DIAGNOSE · specific · narrow · moderate** 18% of our Asia–Europe bookings were rolled last quarter. Which carriers, ports and booking behaviours explain it, and would booking earlier or splitting bookings have helped?
- ↳ What did it cost us including demurrage and air freight?
- ↳ Which carriers rolled us most often?

**Q5 · RESEARCH · vague · wide · simple** What are the carriers up to on blank sailings and surcharges for the next couple of months, and does it hit us? Move the bookings that are hit.
- ↳ Cost impact on our planned volumes.
- ↳ Which bookings should move?
- ↳ Actually, cancel the Rotterdam one instead of moving it.

**Q6 · DECIDE · partial · narrow · complex** Northern European port congestion is bad and people are talking about rail from the Med. Is it worth routing some Europe-bound boxes via Valencia or Piraeus plus rail instead? Compare door-to-door cost, transit time and reliability for our typical 40ft garment containers into the Northampton DC.
- ↳ How reliable is the rail leg in practice?
- ↳ What volume would make it worthwhile?

---

## 13. Air freight coordinator (AI score 3)

**Q1 · DECIDE · specific · narrow · moderate** Style 7731 is three weeks late and it's a key winter promo line. Is airfreighting 6,000 units worth it against the sales we'd lose? If it is, book it, but ask me before you commit.
- ↳ What if we only air 3,000?
- ↳ Can we cut the cost by splitting between two airlines or consolidating?

**Q2 · DIAGNOSE · partial · wide · moderate** We spent £420k on air freight last quarter. Categorise it by cause and by supplier and tell me how much was avoidable.
- ↳ Which suppliers account for most of the avoidable spend?
- ↳ What would chargebacks look like under our contracts?
- ↳ Send chargeback notices to the top three suppliers once I approve.

**Q3 · RESEARCH · vague · narrow · simple** Air rates out of Dhaka at the moment?
- ↳ And Ho Chi Minh, both to London.
- ↳ How does that compare with last year?
- ↳ Any restrictions on batteries?

**Q4 · FORECAST · vague · wide · moderate** How much air freight should I budget for peak? Production is running late at a few suppliers, so base it on current delays and their on-time record rather than last year.
- ↳ What if delays improve by 20%?
- ↳ Which suppliers drive most of the number?
- ↳ Update the peak air freight budget line to that figure.

**Q5 · DECIDE · specific · narrow · complex** I've got 500 units of a hero product stuck behind a late factory exit with a delivery deadline in 12 days. Compare straight air from Dhaka, sea-air via Dubai and splitting the order, on landed cost per unit, risk of missing the date and any customs or dangerous-goods issues. Give me a recommendation and the booking cut-offs I need to hit. Once I confirm the option, book it.
- ↳ What are the risks with the Dubai transfer?
- ↳ Draft the booking request for the forwarder.
- ↳ Actually, cancel the sea booking we already hold on that PO.

---

## 14. Customs and trade compliance specialist (AI score 5)

**Q1 · RESEARCH · specific · wide · moderate** What are the current duty rates and any additional tariffs on cotton knit tops (HS 6110) from Vietnam, Bangladesh and Turkey into the UK, EU and US, and what has changed in the last 12 months?
- ↳ Which routes qualify for preferential rates and what proof of origin do we need?
- ↳ Show the duty difference per £10,000 of goods for each country.
- ↳ Anything announced for the next six months?

**Q2 · DECIDE · specific · narrow · complex** We're launching a padded gilet with a detachable fleece liner: shell 100% polyester, liner 100% polyester knit, sold as one item. What HS code applies, and what are the arguments for the two most likely classifications? Look for binding rulings on similar garments in the UK and EU, quantify the duty difference between the two codes at our expected 80,000 units, and tell me what evidence to hold in case customs challenges it.
- ↳ Does it change if the liner is sold separately as well?
- ↳ Is it worth applying for a binding ruling?
- ↳ If so, start the binding ruling application.

**Q3 · DIAGNOSE · partial · narrow · moderate** Eleven shipments from the same supplier were held at customs in the last two months. Review the declarations and tell me what they have in common. Then ask the broker to correct any that are still open.
- ↳ Is it classification, valuation or origin evidence?
- ↳ What's our financial exposure if past shipments get reassessed?
- ↳ Draft a corrective action plan for the supplier and the broker.

**Q4 · FORECAST · partial · wide · complex** If a proposed 15% tariff on footwear from Vietnam goes ahead, what's the cost impact on our 2027 buy by category and what could we do about it?
- ↳ How would shifting some volume to Indonesia change cost after tariffs and freight?
- ↳ How much margin could we recover through price?

**Q5 · RESEARCH · vague · wide · simple** Do we qualify for UK–Vietnam preferential rates?
- ↳ Garments, fabric from China, cut and sewn in Vietnam.
- ↳ What would need to change to qualify?
- ↳ What evidence do we need and who issues it?

**Q6 · RESEARCH · vague · wide · simple** Any forced-labour import rules we need to worry about? We buy a lot of cotton and some polysilicon-based products, so I need to know where we could get stopped at the border.
- ↳ Which of our suppliers are exposed?
- ↳ What does a detention actually look like in practice?
- ↳ Put the high-risk suppliers' open POs on hold, but check with me first.

**Q7 · DECIDE · partial · narrow · moderate** Could a bonded warehouse or inward processing relief help on goods we re-export to Ireland and the EU? Compare duty and cash-flow benefits with the admin burden.
- ↳ What volumes would make it worthwhile?
- ↳ What are the conditions and audit risks?
- ↳ Start the IPR authorisation application if it stacks up.

**Q8 · RESEARCH · specific · narrow · simple** How do the de minimis changes hit our cross-border direct-to-consumer orders at an average £62 basket?
- ↳ Extra duty and VAT per order.
- ↳ What are competitors doing?

---

## 16. Last-mile delivery manager (AI score 3)

**Q1 · DIAGNOSE · partial · wide · moderate** First-attempt delivery success fell from 93% to 88% over two months. Analyse by courier, region, product and delivery option and tell me what changed.
- ↳ Address quality, customer availability or courier performance?
- ↳ Which postcodes are worst?
- ↳ What would fixing the top two causes save in repeat deliveries and contacts?

**Q2 · DECIDE · specific · narrow · complex** Should we shift 20% of London volume from Courier A to Courier B? Compare six months of on-time performance, damage rate, cost per drop and complaint rate for each, plus anything public on Courier B's peak capacity and track record. If yes, design a six-week trial with clear success criteria and exit conditions.
- ↳ Which postcodes should the trial cover?
- ↳ What would make us stop early?
- ↳ Once I approve, set the trial up in the allocation rules.
- ↳ Actually, only the north London postcodes.

**Q3 · FORECAST · vague · wide · moderate** Where are we most likely to see courier delays in peak? Use the last two peaks if that's helpful, and tell me what courier capacity we'd need by region.
- ↳ How bad were the worst days last year?
- ↳ Should any cut-off times change?

**Q4 · RESEARCH · partial · wide · moderate** What new low-emission zone, parking and delivery-time rules are coming in our top 10 UK and EU cities, and what do they do to cost per drop?
- ↳ How are other retailers adapting?
- ↳ Which cities are hardest hit?

**Q5 · DIAGNOSE · vague · narrow · simple** "Where is my order" contacts are up. Why? And turn on proactive delay alerts for orders with a missed scan.
- ↳ About 30% up on last month.
- ↳ Late scans, missed delivery promises or poor tracking updates?
- ↳ Would better proactive notifications cut them?

---

## 19. Control tower analyst (AI score 4)

**Q1 · DIAGNOSE · partial · wide · complex** Which in-transit shipments are likely to arrive late, by how many days, and which SKUs on them could stock out in stores?
- ↳ Rank by lost sales risk.
- ↳ Where in the chain is the delay building up?
- ↳ What mitigation exists for the top five?
- ↳ Flag the top five as priority and ask the forwarder to expedite them.

**Q2 · RESEARCH · vague · wide · simple** Anything in the next two weeks that could hit our vessels or key ports? Weather, strikes, closures, anything geopolitical. Tell me which of our containers are exposed.
- ↳ How long might the delay be, based on similar past events?
- ↳ Which are the highest-value boxes?

**Q3 · DECIDE · specific · narrow · complex** The vessel carrying 140 of our containers has been anchored outside Rotterdam for six days with no berth ETA. Compare waiting, transshipping at another port and flying the most urgent stock. Use container-level SKU and store-cover data to identify the priority boxes, estimate cost and service impact for each option, draft the alert to the stock and sales teams and, once I approve it, send it.
- ↳ What did it cost the last time we faced something similar?
- ↳ Which stores run out first if we wait?

**Q4 · DIAGNOSE · partial · narrow · moderate** ETA accuracy on the Asia–UK lane is poor. Compare predicted versus actual arrivals and find where the predictions go wrong.
- ↳ Carrier data, port dwell or the inland leg?
- ↳ How much would better estimates improve planning?
- ↳ Update the planning buffer for that lane to match.

**Q5 · FORECAST · specific · wide · complex** If the northern Europe port closure runs two weeks, what happens to stock cover by category and which stores are hit first? And what if it runs four?
- ↳ What's the best reallocation of stock across the network?
- ↳ Which stores are hit first?

**Q6 · MONITOR · vague · wide · simple** Give me this week's top 10 disruptions, then post it to the leadership channel.
- ↳ With the impact on us, ranked by severity.
- ↳ Which are new since last week?
- ↳ Turn it into a briefing for the leadership meeting.

---

## 20. Carrier relationship manager (AI score 4)

**Q1 · DIAGNOSE · specific · wide · complex** Compare 12 months of carrier invoices (attached: carrier_invoices_FY26.csv) against contracted rates. Where are we being overcharged — surcharges, accessorials, weight disputes, wrong service level — and what's the total value? Separate legitimate charges from ones we can dispute, then draft the dispute letter for the largest one and, once I approve it, submit the dispute.
- ↳ Which charge categories account for most of it?
- ↳ How far back can we claim under each contract?

**Q2 · RESEARCH · vague · wide · simple** Are our parcel rates competitive?
- ↳ For our volumes and service levels.
- ↳ Which services are most above market?
- ↳ What leverage do we have in negotiation?

**Q3 · DECIDE · partial · wide · complex** Based on performance data, which carriers should we award, reduce or exit in the next tender, and why?
- ↳ How do cost and service change under that plan?
- ↳ What's the risk of depending on fewer carriers?
- ↳ For the carriers we exit, remove them from those lanes' allocation once I sign off.

**Q4 · FORECAST · vague · wide · moderate** What rate increases are coming from carriers next year? Use their announcements and market news, and tell me what it does to the budget.
- ↳ How could we offset it?
- ↳ Which carriers are most likely to push hardest?

**Q5 · DIAGNOSE · specific · narrow · simple** Carrier B's damage claims doubled in Q3. Why?
- ↳ Specific depots, product types, packaging or routes?
- ↳ How much is recoverable under their liability terms?
- ↳ File claims for the recoverable ones.

**Q6 · DECIDE · partial · narrow · moderate** Write the scorecard criteria and weights for our next carrier tender, based on what has hurt us most in the last 12 months, and save it as the template for the tender.
- ↳ How would each current carrier score?
- ↳ What minimum thresholds should disqualify bidders?

---

## 21. Reverse logistics manager (AI score 3)

**Q1 · DIAGNOSE · partial · narrow · moderate** How many returns are we getting next week?
- ↳ Does the feedback point to sizing, quality or expectation?
- ↳ What would fixing the top five styles save?
- ↳ What did supplier QA data say about those styles?
- ↳ Open a QA review on the top five styles.

**Q2 · DECIDE · specific · wide · complex** For returned electronics accessories (chargers, cables, earbuds), compare restocking, refurbishing, selling to a liquidator and recycling on recovered value, handling cost, time to sell and brand risk. Use the last six months of returns grading data and show which disposition route we should change first, and how the answer shifts for items older than 60 days.
- ↳ What would the change be worth over a year?
- ↳ Which route would pay back fastest?
- ↳ Change the 60+ day route to liquidation and retire the old rule.

**Q3 · FORECAST · vague · wide · simple** How many returns will we get in January? I need to know what capacity we need in the returns centre and roughly how many agency staff that means. Then request the agency staff.
- ↳ What did last year's weekly pattern look like?
- ↳ How sure are you about the peak week?

**Q4 · RESEARCH · vague · wide · moderate** What are the rules on returned goods and EPR in Germany, France and the Netherlands? Include penalties and whether any of our current practices might conflict.
- ↳ What reporting do we have to submit?
- ↳ Which country is the strictest?

**Q5 · DECIDE · partial · wide · complex** Should we start charging for returns in some countries? Estimate the effect on return rates, conversion and margin from our data and what competitors have done.
- ↳ Which customer segments would be most affected?
- ↳ How would we trial it?
- ↳ Set the trial up in two markets once I've signed it off.
