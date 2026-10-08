# Questions 01 · Warehouse and Distribution Centre

AI-suited personas only (score 3+). Questions are written the way real users ask them: some vague, some precise; some short, some long; some narrow, some broad. Follow-ups show how a conversation could realistically continue, including clarifications, corrections and scope changes.

**Type tags:** `MONITOR` · `DIAGNOSE` · `FORECAST` · `DECIDE` · `RESEARCH`
**Shape tags (after the type):** specificity (`vague` / `partial` / `specific`) · scope (`narrow` / `wide`) · complexity (`simple` / `moderate` / `complex`)

---

## 4. Inventory control/cycle counter (AI score 3)

**Q1 · DIAGNOSE · vague · narrow · simple** Why is the count for bay C-14 so off?
- ↳ Tuesday's count against the system. Look at the last 90 days of movements.
- ↳ Is it one SKU or several?
- ↳ Put a hold on the bay until it's recounted, and if it's a system error, correct it once I confirm the figure.

**Q2 · DIAGNOSE · specific · wide · complex** Using the WMS adjustment export for 1 July to 30 September (attached: adj_Q3.csv), group all adjustments over £500 by cause code, location zone, shift and day of week. Exclude cycle-count corrections that were reversed within 48 hours. Then tell me whether any clusters point to a process problem (a particular shift, a receiving dock, a zone) rather than random error, and rank the clusters by value so I know what to investigate first.
- ↳ Which cause code is being used as a catch-all?
- ↳ Do the clusters line up with new starters or the August layout change?
- ↳ Give me a one-page summary for the ops meeting.
- ↳ Re-code the catch-all adjustments to the right cause once you're sure, and approve the ones under £50 that are clearly fine.

**Q3 · DECIDE · partial · narrow · moderate** I've got three days of counting capacity this week. Which locations should I count first? High value and historically inaccurate, but skip anything counted in the last month. Then release the counts to the handhelds.
- ↳ Can you give me that as a printable count sheet?
- ↳ What accuracy would I expect to find in each zone?
- ↳ Actually, drop zone D and give its counts to Priya instead.

**Q4 · DIAGNOSE · partial · wide · complex** Compare goods receipts to supplier ASNs for the last 8 weeks. Is one supplier or carrier responsible for most of our negative variances, and is it short-shipping or our own receiving?
- ↳ What's the claimable value and are any claims still inside the window?
- ↳ Draft a note for the supplier manager.
- ↳ Raise claims for the ones still inside the window and send the note once I've approved it.

**Q5 · FORECAST · vague · wide · moderate** Where will stock accuracy be worst going into peak? I'm thinking by zone, using the last few quarters of cycle count results, so I know where to put the extra counting time.
- ↳ What would extra counting before peak actually buy us?
- ↳ Which zones can I leave alone?

---

## 6. Warehouse manager (AI score 3)

**Q1 · DIAGNOSE · partial · narrow · moderate** Cost per unit shipped went up 9% in September versus August. Split that into labour, overtime, agency, damages, rework, energy and rent and tell me what drove most of it.
- ↳ Was labour volume mix (more single-unit orders) or lower productivity?
- ↳ How does it compare with last September?
- ↳ What would it take to get back to the August level?

**Q2 · FORECAST · vague · wide · moderate** Will we run out of space this autumn?
- ↳ Pallet positions, whole building.
- ↳ When, and by how much?
- ↳ Which categories are driving it?
- ↳ Push back the two lowest-priority inbound POs by a week, and cancel next Tuesday's bookings for them.

**Q3 · DECIDE · specific · narrow · complex** We're deciding between adding a late shift (22:00 to 06:00) for eight weeks or paying overtime on the two existing shifts to cover peak. The headcount gap is about 45 FTE from 3 November to 28 December. Compare the two on total cost, productivity in units per hour, safety risk from fatigue, and likely retention impact. Use the September labour data and the agency rate card (attached: labour_Sep.xlsx, agency_rates.pdf) and flag any assumption you can't support. I need a one-page recommendation for the operations director by Thursday.
- ↳ What does the evidence say about error rates with extended overtime?
- ↳ How many agency staff could we realistically recruit locally at our rates?
- ↳ Rework it as three bullets I can say out loud in the meeting.
- ↳ Send the recommendation to the operations director, and once we pick an option, request the agency labour for it.

**Q4 · RESEARCH · vague · wide · simple** How do we stack up against other retail DCs on cost and productivity? I'm not sure which measures are comparable with ours, so tell me how you'd even compare.
- ↳ Which of our gaps is worth real money?
- ↳ Where does the benchmark come from and how reliable is it?

**Q5 · DIAGNOSE · specific · narrow · moderate** Store service level fell from 98.5% to 95% over the last three weeks. Combine WMS, inbound and labour data and tell me where the process is breaking.
- ↳ Picking, loading, or late trailers?
- ↳ Which stores or lanes took the hit?
- ↳ What changed three weeks ago?
- ↳ Bump the priority of the late store orders so they go out on tonight's wave.

---

## 8. WMS analyst (AI score 3)

**Q1 · DIAGNOSE · specific · narrow · simple** 140 orders have been stuck in "allocation failed" since 6am. What do the affected SKUs have in common? Fix what you safely can and retry the allocation.
- ↳ Data issue, configuration change or interface failure?
- ↳ What's the safest fix during live operations?
- ↳ Write the incident summary for ops.
- ↳ Open the incident ticket for the interface team.

**Q2 · DECIDE · partial · wide · complex** Why don't ERP and WMS stock agree?
- ↳ How long would the re-slotting take and can it be done in phases?
- ↳ Which SKUs are picked together often enough to sit side by side?
- ↳ Raise a ticket for the interface fix you'd recommend.

**Q3 · RESEARCH · specific · narrow · simple** We're on WMS version 9.2 and getting duplicate task creation after replenishment. Is that a known bug in the release notes, and is there a patch or workaround?
- ↳ Which patch includes the fix and what else does it change?
- ↳ What should we test before applying it?
- ↳ Raise the change request for the patch and submit it for the next CAB.

**Q4 · DIAGNOSE · vague · wide · moderate** ERP and WMS don't agree on stock again. This happens every few months and each time someone spends a day chasing it down and nobody writes it up. Finance is asking about a £1.2m gap as of last night. Can you work out where the difference comes from this time, and whether it's something we keep doing to ourselves?
- ↳ Timing, status mapping or real discrepancies?
- ↳ Which items make up most of it?
- ↳ Write up the cause and publish it to the knowledge base so it's documented this time.
- ↳ Archive the old reconciliation note this replaces.

**Q5 · FORECAST · partial · wide · complex** What would happen to pick rates and order cut-off times if we moved e-commerce from wave picking to continuous batching, given our current order profile? Include the configuration changes we'd need.
- ↳ What have other retailers reported from the same change?
- ↳ Which orders would lose out under batching?

---

## 9. Health & safety officer (AI score 3)

**Q1 · DIAGNOSE · vague · wide · moderate** What are our biggest safety risks right now? I'd like to see it across all three DCs, using the last 12 months of incidents and near misses, rather than just the headline numbers.
- ↳ Any patterns by time of day, task or equipment?
- ↳ Which three controls would cut the most risk?
- ↳ Close the corrective actions that are already done, and move the due date on the overdue ones to month end.

**Q2 · RESEARCH · specific · narrow · moderate** We're rolling out electric reach trucks at our two newest sites in January. What do current UK regulations and good-practice guidance require for battery charging areas, ventilation, fire separation and operator training? Turn it into a checklist the site managers can walk, flag where our existing risk assessments will need to change, and assign an action to each site manager for those gaps.
- ↳ Have there been recent incidents in similar warehouses we should learn from?
- ↳ Which items can we realistically complete before January?
- ↳ Actually, only assign them for the two newest sites.

**Q3 · DIAGNOSE · partial · narrow · moderate** Forklift–pedestrian near misses went up in Q3. Link them to layout changes and shift data and tell me what's driving it, and raise corrective actions for the hotspots.
- ↳ Did it coincide with the peak labour intake?
- ↳ Which aisles or crossing points are the hotspots?
- ↳ Hold off on the actions for aisle 7, it's being relaid.

**Q4 · DECIDE · partial · wide · complex** Compare pedestrian exclusion zones, proximity sensors and speed limiters for cutting forklift incidents. What does the evidence say, and roughly what would each cost for a site our size?
- ↳ What would a phased rollout look like?
- ↳ How would we measure whether it worked?

**Q5 · RESEARCH · vague · wide · simple** Any new warehouse safety rules we should know about?
- ↳ UK, Germany and Poland.
- ↳ Do any of them apply to agency workers?
- ↳ Which of our current practices wouldn't meet them?
- ↳ Log a corrective action for each gap in Germany only.

---

## 10. Automation/robotics engineer (AI score 3)

**Q1 · DIAGNOSE · partial · narrow · moderate** Our shuttle system had 14 unplanned stoppages last month. Using the fault logs and maintenance records, what are the common root causes, ranked by lost throughput?
- ↳ Is any failure tied to a specific aisle, shuttle or software version?
- ↳ Which could have been predicted from sensor data?
- ↳ What spares should we hold to cut downtime?
- ↳ Raise a purchase requisition for the top three spares.

**Q2 · FORECAST · specific · wide · complex** Based on run hours, fault history and the CMMS records for the conveyor network and the sorter (attached: cmms_export.xlsx), which motors, gearboxes and sensors are most likely to fail before 1 November? For each, give a rough failure likelihood, the cost of an unplanned failure versus planned replacement, the lead time for the part, and whether it can be done in the planned shutdown on 19 October. Raise work orders for the ones that fit.
- ↳ Which of these have the longest part lead times?
- ↳ Put it in a table sorted by risk times cost.
- ↳ Actually, cancel the gearbox work order, we'll replace it later.

**Q3 · RESEARCH · specific · narrow · simple** What's new in AMR firmware 4.7, and should we update before peak?
- ↳ What's the rollback process if it goes wrong?
- ↳ Does anything in the notes affect our safety validation?
- ↳ Create a change request for the update, targeting the first week of November.

**Q4 · DECIDE · vague · wide · moderate** The old sorter keeps costing more to maintain and the engineers say it's nearly 12 years old. Operations keep asking whether we should carry on fixing it, do a major overhaul, or just replace it, and I don't have a good answer. Can you help me think it through, including what happens to downtime risk over the next seven years?
- ↳ What would replacement realistically cost and how long would it take?
- ↳ How does the answer change if volumes grow 20%?

**Q5 · DIAGNOSE · vague · narrow · simple** Robot throughput drops every afternoon. Why?
- ↳ About 15% between 2 and 4pm.
- ↳ Is it WiFi load, charging schedules, traffic congestion or order mix?
- ↳ What experiment would confirm it?
- ↳ Move the charging window to 6 to 8pm for the test, once I say go.
