# Questions 09 · Data, Technology and Leadership

AI-suited personas only (score 3+). Questions are written the way real users ask them: some vague, some precise; some short, some long; some narrow, some broad. Follow-ups show how a conversation could realistically continue, including clarifications, corrections and scope changes.

**Type tags:** `MONITOR` · `DIAGNOSE` · `FORECAST` · `DECIDE` · `RESEARCH`
**Shape tags (after the type):** specificity (`vague` / `partial` / `specific`) · scope (`narrow` / `wide`) · complexity (`simple` / `moderate` / `complex`)

---

## 81. Data analyst, supply chain (AI score 4)

**Q1 · DIAGNOSE · specific · wide · complex** OTIF dropped from 94% to 89% last month. Break it down by supplier, category, DC, day of week and inbound mode, tell me whether the change is real or a measurement or definition change (check for any change to the OTIF calculation or ASN data in that period), and build a chart pack I can send to the ops director. Once I've approved it, email the pack to the ops director.
- ↳ Which two splits explain most of the drop?
- ↳ Add a slide on what we'd do about it.

**Q2 · DIAGNOSE · partial · narrow · moderate** Operations and finance report different inventory numbers. Which is authoritative and why do they differ? Reconcile the main differences.
- ↳ Which differences are timing and which are definitional?
- ↳ Which differences are definitional?
- ↳ Post a journal to correct the differences we agree are errors, but ask me before posting.

**Q3 · FORECAST · vague · wide · simple** What do next month's KPIs look like? Give me the likely range for each one and tell me which are most likely to miss target.
- ↳ Which are most sensitive to peak?
- ↳ How reliable has this method been?
- ↳ Tighten the alert thresholds on the KPIs most likely to miss.

**Q4 · DECIDE · specific · narrow · moderate** I need a model joining WMS, TMS and ERP data to calculate cost per order. What's the best structure? Write the SQL.
- ↳ How do I handle orders split across shipments?
- ↳ How should I handle split shipments?
- ↳ Publish the model as a view in the warehouse so the team can use it.

**Q5 · RESEARCH · vague · narrow · simple** What's the standard definition of perfect order rate?
- ↳ How does ours differ?
- ↳ What are typical benchmarks?

**Q6 · MONITOR · vague · wide · simple** What data quality problems hurt our reporting most? Tell me the business impact of each and who owns the fix. Raise tickets for the top three and assign them to the owners.
- ↳ Which can be fixed fastest?
- ↳ Which keep coming back?

---

## 82. Data scientist (AI score 4)

**Q1 · DECIDE · partial · narrow · complex** What modelling approach would best predict ocean transit time variability on our main lanes, and which features matter? How would we evaluate it against carrier estimates and what data would we need?
- ↳ How would we handle disruption events in the training data?
- ↳ Which features matter most?

**Q2 · DIAGNOSE · vague · narrow · moderate** The demand model has been getting worse for about three months and the planners have started to ignore it. Can you work out whether it's drift, a data pipeline change or a genuine shift in customer behaviour, and what we'd need to retrain it on to get the accuracy back?
- ↳ Which categories are worst hit?
- ↳ Was there a release or data change three months ago?
- ↳ Once I say go, start a retraining run on the cleaned data.

**Q3 · FORECAST · specific · narrow · moderate** What uplift would the new model give versus today's process, and what's it worth?
- ↳ What would it cost to deploy?
- ↳ What's the deployment cost?

**Q4 · RESEARCH · partial · wide · moderate** What are the state-of-the-art methods for forecasting new product demand with little history, and which have open-source implementations that suit our data?
- ↳ Which would you try first?
- ↳ Which would you try first?

**Q5 · MONITOR · vague · wide · simple** Are our production models OK?
- ↳ Which need retraining soonest?
- ↳ What alerts should we set?
- ↳ Set up drift alerts on any model that has none.
- ↳ Actually, remove the alert on the pricing model, it's too noisy.

**Q6 · DECIDE · specific · narrow · complex** Write a feature engineering plan for predicting supplier delay risk at PO level. Use what we hold (PO history, ASN data, supplier scorecards, port and weather feeds, payment history), list candidate features, leakage risks, which need new data, how we'd validate it before using it operationally, and a baseline to beat.
- ↳ Which three features do you expect to carry most signal?
- ↳ How would we explain a prediction to a buyer?
- ↳ Add tasks to the backlog for the new data feeds we'd need.

---

## 83. ERP / systems integrator (AI score 3)

**Q1 · DIAGNOSE · specific · narrow · simple** 200 EDI PO acknowledgements failed overnight. Analyse the error logs and find the common cause. Once I confirm, reprocess them.
- ↳ Mapping, format or partner-side?
- ↳ How do we reprocess safely?

**Q2 · RESEARCH · specific · narrow · moderate** The supplier's new EDI spec (attached: ASN_spec_v2.pdf) adds an ASN segment for pallet-level packing data. Explain what it changes, map it to our WMS inbound fields, list the gaps, and tell me what changes we need to make and in what order.
- ↳ Which changes are mandatory and which optional?
- ↳ Which fields are missing in the WMS?
- ↳ Raise change requests for the mandatory changes, in that order.

**Q3 · DECIDE · partial · narrow · moderate** What's the best way to integrate a new 3PL: EDI, API or file transfer? What are the risks?
- ↳ Which is cheapest to run?
- ↳ Which does the 3PL support?

**Q4 · FORECAST · vague · wide · moderate** Will integrations cope with peak? Tell me which interfaces are closest to their limits and what load test we should run first.
- ↳ Which one worries you most?
- ↳ What load did we hit last peak?
- ↳ Schedule that load test for the next quiet window.

**Q5 · DIAGNOSE · vague · narrow · simple** Why are website stock updates 20 minutes behind? If it's a config setting, change it, but ask me first.
- ↳ Which step in the pipeline adds the delay?
- ↳ What's the oversell risk while it persists?

---

## 85. Cybersecurity analyst (AI score 3)

**Q1 · MONITOR · vague · wide · moderate** What needs my attention this week? I've got a pile of alerts and vulnerability scan results and I can't tell what really matters. Rank them by real business risk, tell me which need action today, and which are probably false positives.
- ↳ Which one would you escalate?
- ↳ How did you judge business risk?
- ↳ Close the ones that are false positives.

**Q2 · DIAGNOSE · specific · narrow · complex** A supplier user account logged in from an unusual location at 03:12 and accessed the EDI portal and the vendor bank detail screen. Using the auth logs and access logs (attached: auth_logs.zip), work out whether this is a real incident, what it touched, whether any bank details changed, and what we should do now. Draft the incident summary for the CISO. If it's real, lock the account and hold any payments to changed bank details, but check with me before you do.
- ↳ Should we notify the supplier now or wait?
- ↳ What containment steps are safe to take immediately?

**Q3 · DECIDE · partial · wide · moderate** Which supplier and partner connections are the highest risk and what controls would reduce it?
- ↳ Which have privileged or direct system access?
- ↳ What's the quickest control to put in place for the top three?
- ↳ Raise remediation tasks for the top three.

**Q4 · RESEARCH · vague · wide · simple** Any vulnerabilities in our WMS or EDI vendors being exploited?
- ↳ Which of our versions are affected?
- ↳ Which versions are exposed?

**Q5 · FORECAST · specific · narrow · complex** What would ransomware on our warehouse systems cost us and how long would recovery take?
- ↳ Where are the weak points?
- ↳ Which systems are the weak points?

---

## 87. Chief supply chain officer (AI score 4)

**Q1 · MONITOR · vague · wide · moderate** How are we doing end to end? I'm going into the executive meeting and want a view across service, cost, inventory, risk and sustainability against plan, the top five issues, what's causing each, and which can be fixed in a quarter. Write it as a briefing.
- ↳ Which issue is most urgent?
- ↳ What's changed since last quarter?
- ↳ Send it to the CEO's office.

**Q2 · DECIDE · specific · wide · complex** What should our top supply chain investments be over the next three years: nearshoring, automation, network changes, dual sourcing or digital planning? For each, give the expected return, risk, dependencies and timing, compare with what leading retailers have done, and propose a sequenced roadmap within a total investment envelope of around £80m.
- ↳ What gets cut if the envelope drops to £50m?
- ↳ What's the biggest dependency across the roadmap?
- ↳ Submit the funding request for the first-wave projects once I've agreed the sequence.

**Q3 · FORECAST · partial · wide · complex** How resilient are we to a major disruption, and what would it cost? Compare scenarios.
- ↳ Which scenario would hurt most and how likely is it?
- ↳ Which investments would reduce exposure most per pound?

**Q4 · RESEARCH · vague · wide · simple** What are the best retailers doing in supply chain?
- ↳ What results have they achieved?
- ↳ What's relevant for us?

**Q5 · DIAGNOSE · specific · narrow · moderate** The Northampton DC cost per unit is 18% above the network average. Is that structural or fixable? Look at labour, layout, automation, product mix and volume. If it's fixable, set up a recovery initiative with named owners.
- ↳ What would fixing it be worth?
- ↳ Which part is out of our control?

**Q6 · DECIDE · vague · wide · simple** How should we organise supply chain for the next stage of growth? Show what comparable retailers' structures look like and the transition risks.
- ↳ Which structure suits our scale?
- ↳ What would we lose?

---

## 88. COO / operations director (AI score 4)

**Q1 · MONITOR · partial · wide · moderate** How are all sites performing against service, cost, safety and quality targets, and where is the largest underperformance? Why?
- ↳ Which sites should I visit?
- ↳ Why is it underperforming?
- ↳ Book visits to the two worst sites in my diary.

**Q2 · DIAGNOSE · specific · narrow · moderate** Productivity at Daventry is well below the other DCs. Is it layout, labour, systems or management? What would fixing it be worth?
- ↳ What would fixing it be worth?
- ↳ Which cause is easiest to fix?
- ↳ Create an improvement plan for Daventry and assign owners.

**Q3 · DECIDE · specific · wide · complex** We have seven capex projects on the table (attached: capex_FY27.xlsx) totalling £34m against a £22m envelope. Rank them by return and risk, say which can be phased or descoped, show the impact on peak readiness for each choice, and give me a recommended portfolio and the arguments I'll face from each sponsor. Once I approve the portfolio, update the capex tracker and put the descoped projects on hold.
- ↳ What does the portfolio look like at £18m?
- ↳ Which project's business case is weakest?
- ↳ Actually, cancel project 5 rather than phasing it.

**Q4 · FORECAST · vague · wide · moderate** What capacity and headcount do we need for next peak and next year? Use current volume forecasts and productivity, and tell me where we're most at risk of not having enough.
- ↳ Where's the biggest gap?
- ↳ When must we commit?
- ↳ Create requisitions for the first tranche of hires.

**Q5 · RESEARCH · vague · wide · simple** Where do we lead or lag on benchmarks?
- ↳ Which gaps are worth closing?
- ↳ Which gaps are worth closing?

**Q6 · DECIDE · vague · narrow · moderate** Should we in-source or outsource transport? Compare cost, control, flexibility and risk over five years, and tell me what the transition would involve.
- ↳ Which parts could we outsource first?
- ↳ What would we lose?

---

## 89. HR / workforce planner (AI score 3)

**Q1 · FORECAST · specific · wide · complex** How many people and which skills do we need by site and week for peak, based on the volume forecast and current productivity? How many are we short, by when, and what does it cost to recruit versus use agency?
- ↳ What's the latest date we can start recruiting?
- ↳ When must recruitment start?
- ↳ Open requisitions for the Corby shortfall first.

**Q2 · DIAGNOSE · specific · narrow · moderate** Turnover at Corby is 45% against 28% elsewhere. Look at pay, shifts, management, commute and exit data.
- ↳ What would reduce it fastest?
- ↳ Which factor is biggest?
- ↳ Log a pay review request for the Corby night shift.

**Q3 · RESEARCH · vague · wide · simple** What's the labour market like for warehouse hiring in our regions? How do our pay rates compare, and are any employment law changes coming?
- ↳ Which region is tightest?
- ↳ What would a 5% rise buy us?

**Q4 · DECIDE · partial · narrow · moderate** Hire, agency, overtime or automate for peak?
- ↳ What does each option cost per productive hour?
- ↳ What are the quality and retention differences?
- ↳ Request agency labour for the first four weeks of peak.

**Q5 · MONITOR · vague · wide · simple** Where are our people problems? I keep hearing complaints about turnover and absence from site managers but I haven't seen the numbers together. Show me attrition, absence and time-to-hire by site and shift, tell me where it's worst, and what would reduce time-to-hire fastest. Set it up as a weekly report to me.
- ↳ Which site is the outlier?
- ↳ Is it pay or management?

---

## 90. Programme / transformation manager (AI score 4)

**Q1 · MONITOR · specific · narrow · moderate** Is the ERP programme on track for scope, schedule, budget and benefits? Use the RAID log, plan and finance report (attached: erp_pack_Oct.zip) to list the top risks and issues with their status, which have most impact on go-live, what decisions are needed from the steering committee, and draft the highlight report. Send it to the steering committee once I've read it.
- ↳ Which risk has been open longest without an owner action?
- ↳ Which decisions are needed?
- ↳ Close the two risks that are now retired in the RAID log.

**Q2 · DIAGNOSE · specific · narrow · simple** Data migration is three weeks behind. What's blocking it? Raise the blockers with owners.
- ↳ What's the impact on the go-live date?
- ↳ What would it take to recover the time?

**Q3 · DECIDE · partial · wide · complex** What trade-offs among scope, date, cost and resources should we recommend to the steering committee? What are the consequences of each?
- ↳ Which trade-off would you avoid?
- ↳ What does each option cost?
- ↳ Log the chosen option as a change request.

**Q4 · FORECAST · vague · narrow · moderate** When will we really finish and what will it cost? The official date is still green on the dashboard but I don't believe it. Look at the plan, the actual burn rate and where we are on migration and testing, tell me what the realistic completion date and cost are, and how that compares with typical overruns.
- ↳ Which workstream drives the slip?
- ↳ What would recover the date?
- ↳ Set the dashboard status to amber.

**Q5 · RESEARCH · vague · wide · simple** What lessons are there from similar retail ERP and WMS programmes?
- ↳ What are the most common causes of failure?
- ↳ What did the successful ones do differently?

**Q6 · DECIDE · partial · narrow · complex** How should we structure cutover for the new DC to minimise risk during peak? Compare big bang, phased by region and parallel run, with rollback.
- ↳ Which option would you pick if go-live has to be before Black Friday?
- ↳ What would the rollback plan look like?
- ↳ Remove the parallel-run option from the plan.
- ↳ Add the rollback checkpoints as milestones.
