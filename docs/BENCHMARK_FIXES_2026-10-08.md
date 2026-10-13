# Benchmark fixes, 8 October 2026

Fixes from the audit of the Haiku scale-80 v2 judgements (track W1). One line each: what changed and why.

## Expected writes on the wrong turn (`mockmcp/eval/tasks.py`)

- Root cause 1: the approval regex never matched "once I confirm" (`confirmed?` needs "confirme") and matched "until it's"; fixed (`confirm(?:ed|s)?`, `until i\b`, "okayed").
- Root cause 2: any turn could own a write, so a main turn that asks nothing ("Why is the count for bay C-14 off?") won on shared nouns; now only turns that ask for an action, or name it as an instruction, can.
- Root cause 3: an ask held for the user's go-ahead stayed expected although no later turn gives it; now the best-matching ask decides: "..., but ask me first" holds its sentence, a leading "once I approve, ..." holds the rest of its sentence, a trailing "... once I confirm the figure" holds only its own ask.
- A held write moves to the first later turn that names it ("Only send the UK one for now") or says go ahead; a turn that swaps it ("cancel it rather than delaying it") does not approve it.
- A held write with no go-ahead is not expected; it goes to the new `writes.held` list (stopping to ask is right, doing it is acting before approval), and a write-only slice's facts are dropped, as are status facts ("blocked", reasons) of a held write.
- "Once it looks right" now sets `approval_needed` but is not a hold: the assistant checks and the same turn asks.
- "Prepare the journal for my approval" asks for the draft now (not held); "Flag where I'm short" reports rather than writes.
- Verbs of a write come from the clauses that name its ids (release is not a verb of a reassignment), "give" counts as reassign, "drop"/"cancel" as delete, "apply"/"correct"/"amend" as update; the Context paragraph is not used to place writes.
- Results: scn-01:4:Q1 recount at turn 3; scn-07:66:Q5 only the cancel at turn 3 (the delay is held); scn-08:71:Q3 delete and reassign at turn 4, approve and shift at turn 3; scn-09:83:Q1 reprocess held. 54 writes in 43 scenarios are now held; 228 of 441 scenarios still expect writes.

## Reference inputs not in the prompt (Rule C)

- New optional case fields, read by `tasks.py`: `scenario_context` (inputs the user states in the scenario's Context), `scenario_facts` (the facts a scenario requires; the rest stay on the slice as `dropped_facts`), `inputs_from` (systems the ref arguments stand for, used by missing_server traps).
- scn-03:29:Q3: the Context now gives SKU-100959 (outerwear), 2,000 units in stock, 120 a week, £102.99 and the event timing.
- scn-04:38:Q1: the Context now gives 40,000 units at £18.50 for the liability estimate.
- scn-03:24:Q3: the Context now gives 500,000 metal zips (ZIP_METAL) bought eight weeks early.
- scn-02:21:Q3: the lms facts 69.7 and 40 depend on an assumed 100,000 a week that contradicts the scenario's own forecast, so the scenario requires only 45 (agency quantity free under Rule B).
- scn-08:75:Q3 (and traps built on it, such as tempting-wholesale-retract): the Context now names MKT-DE, bedding, 20,000 units a quarter and £0.40 a unit.
- scn-07:62:Q8: the draft summary's facts (2.2%, 21.6%, OFF PLAN) are not required in the scenario; the month's figures are graded on the consolidation, budgeting and risk slices.
- tax_duty-07:67:Q3: 935,000 parcels stands for ecommerce data the scenario never states, so its facts are not required there (`scenario_facts: []`), and with `inputs_from: [ecommerce]` a missing-ecommerce trap marks them unreachable; scn-07:67:Q3 itself no longer yields a missing_server trap (nothing else is answerable without ecommerce).

## Unreachable ids

- scn-01:4:Q3: the Context says Priya is employee EMP-00136 (no Priya exists in master data; wms shows ids only).
- scn-08:71:Q3: the Context gives Dan's employee id (EMP-00014; store_ops only takes master ids and Dan has none in store_wfm) and names the approver (Shirley Stewart, EMP-00536) and the new Sunday shift times.
- scn-07:66:Q5: the Context names the non-critical run RUN-900002 (no loaded read tool lists payment runs).

## Trap fairness (`mockmcp/eval/traps.py`, `bench/traps.yaml`)

- missing_server traps drop from the unreachable facts any id or 5+ digit number that a loaded slice's reference call returns, and are not built when nothing truly missing is left; `validate` now flags such a fact (so `eval traps --check` catches it).
- trap-missing_server-06:60:Q1-mt: SUP-0079 / SUP-0057 (returned by costing) are no longer unreachable; only the capacities 400000 / 60000 are. The single-turn variant is not built: test_lab also returns the capacities. The trap is not in the regenerated bank (selection moved), but the builder and a test cover it.
- `_answer_leaks` did not apply here (it only checks lookalike asks that name an entity); the new check runs the loaded reference calls instead.
- Trap candidate filters treat held writes like expected ones, so scenarios with an unapproved write ask are not reused as read-only bases.
- Regenerated bank: 287 traps, `--check` clean; 105 traps were replaced (and 25 kept ones changed content) because the write fix changed the candidate pools and the generator draws with one sequential seeded RNG. Five authored traps whose base task is unchanged were refreshed to pick up the new turn text and reference.

## Debatable references

- slc-reviews-03:25:Q5: fact 4.05 changed to 4.04, what the tool returns.
- trap-out_of_scope-08:74 / scn-08:74:Q1: "last week" is now stated as Monday to Sunday in the web_analytics prompts and in the scenario's Context.
- scn-01:4:Q3: "release the counts" fixes no count; the case notes say releasing CCT-900101 is one acceptable way and any planned counts the answer prioritised are equally right (Rule B).
- scn-02:14:Q8: our cross-border DTC orders are exports, so the tax_duty case now prices the EU destination (7.44 duty, 1.56 extra VAT, 14.58 VAT after) instead of UK imports.

## Cross-system inconsistencies for GitHub issue #3 (data not changed)

- scn-04:36:Q4: the commodity top five contradicts the spend data.
- scn-02:21:Q3: the returns centre plans about 950 returns a week at peak, the demand forecast says 125,000 to 144,000 a week, and the lms case assumes 100,000.
- scn-02:14:Q5: the KB origin rule (65% of value) disagrees with customs (10% by weight); the reference uses the knitted (6110) rule for a woven blouse; the BOM says supplier_country CN while its notes say "Sourced in Vietnam".
- scn-04:36:Q2: Small Appliances facts against a context of "category Footwear".
- store_ops week_tasks assigns ST214 tasks to EMP-00011 to EMP-00014, who are HQ staff in master (EMP-00014 is a buyer); store_wfm lists ST214's real team (Dan Whitfield, Priya Nair) without employee ids.
- wms count tasks: EMP-00136 is Mark Davies in master, the persona's "Priya" exists nowhere.
- tax_duty-07:67:Q3 assumes 935,000 parcels a year into each of the UK and the EU; ecommerce's daily counts annualise to about 1.9 million (UK) and 945,000 (EU).
- ap holds payment runs (RUN-900001, RUN-900002) with no tool that lists them.

## Follow-ups (outside this track's files)

- Document `scenario_context`, `scenario_facts` and `inputs_from` in `bench/AUTHORING.md` and the format note in `mockmcp/bench.py`.
- Add `writes.held` and the slice fields `dropped_facts` / `held` to `mockmcp/eval/schema.py` and `docs/BENCHMARKING.md`.
- Make trap selection hash (seed, candidate id) instead of drawing from one RNG, so a bank change does not reshuffle unrelated traps.
- `tests/test_systems.py::test_system[itsm]` (01:10:Q5, 45.7) still fails in `mockmcp check`; known and date-dependent, untouched.

## Cross-system data fixes, round 4 (track F3, `systems/` only)

From the audit of the 30 tasks both Haiku and Sonnet failed (scale-80 v3). Data regenerated from `gen.py` and `seed/`; bench cases were not edited (the ones whose facts moved are listed under "Cases to re-validate" in the hand-off).

- integration vs wholesale_edi (09:83:Q1): the overnight PO_ACK failures now fall in the early hours of the world's today (data date plus `today_offset_days`), not two days earlier, and the PO_ACK map v1.1 go-live (CFG-900003, MAP-900003) is the evening before. integration now assigns failures per supplier exactly as wholesale_edi does: partner-side HTTP 500s come only from SUP-0004, SUP-0015 and SUP-0030 (3 partners, 4 each), not 11 partners. The two missing days of quiet integration traffic use their own random streams, so no other row moves.
- tax_duty vs customs de minimis (02:14:Q8): one story, a future change. customs now shows the EU 150 EUR (about £130) exemption in Germany, France and Ireland as still in force and due to go on 2027-07-01, and GB relief due to go on 2027-04-01 (the same dates as tax_duty), through the new `new_threshold_gbp` and `change_effective_date` columns. The US exemption (£630) was withdrawn on 2026-07-01 in both. tax_duty's EU, PL and CZ thresholds are now £130 (the EUR 150 in pounds, as customs has it), not £150; the £62 basket figures do not change.
- KB-900002 vs customs rules of origin (02:14:Q5): the KB article now gives the customs rule (manufacture from yarn, fabric knitted or woven in Vietnam or the UK, 10% by weight tolerance; ORG-910001/910002) instead of a 65% value-content rule.
- PLM vs costing for SKU-106328 (06:51:Q6): the PLM BOM main fabric is now MAT-POLYESTER-100 (100% polyester, 1.61 m, £5.21, SUP-0007), as costing has it, and the tech pack says polyester; the factory is FAC-0003 as in master. The PLM material library now holds MAT-POLYESTER-100, MAT-RPET-100 and MAT-RNYLON-100 at costing's prices. The cost_model quote QL-900017 says polyester shell instead of nylon.
- WMS lots (05:42:Q1-b): the pink blouse lots IMS holds at DCs are in WMS bins under the same lot numbers (BATCH-POL-PINK-007: 500 at DC2-B-16-04; BATCH-POL-PINK-004: 240 and BATCH-POL-PINK-005: 180 at DC4), split from the SKU's largest bin, with the same totals.
- costing actual cost (06:58:Q4, trap-vague-unitcost-kettle): `get_costed_vs_actual_cost_by_product` no longer shows the costed cost as the actual (variance 0) for a SKU with no supplier cost history. Actual, variance and margin are blank and `actual_cost_source` says why.

### Still open (for GitHub issue #3)

- IMS vs WMS bin contents at DC1: IMS places each SKU in one or two bins from its own pool, and WMS uses its own bin layout. SKU totals per DC agree, but bin contents do not. For example, DC1-F-13-04 holds 8 SKUs (14,843 units, £457,039.88) in IMS and one SKU (2,648 units, £237,155) in WMS; the same applies to DC1-B-21-02 and DC1-A-28-02. The fix is one bin layout shared through master data, or IMS DC1 rows built from the WMS layout. Either way the IMS count-priority ranking (ims-01:4:Q3) changes.
- ST214 staff ids: store_ops week tasks for ST214 go to EMP-00011 to EMP-00014 (HQ buyers in master). store_wfm's ST214 team (Dan Whitfield, Priya Nair and others) has no master employee ids. A fix needs ST214 staff in master `employees`, which moves every system that samples employees.
- demand vs returns: demand `get_return_forecast_by_week` gives about 100,000 to 144,000 returns a week (chain-wide, scaled to online units). returns (centre capacity and history) gives about 500 to 1,000 a week, and lms assumes 100,000. One of them needs a different scale or label, and the cases built on them need re-deriving.
- costing margin bridge FX: `get_margin_bridge_for_category` shows zero FX and supplier effects where fx (sterling down from 1.335 to 1.27) and landed_cost (Babywear FOB about 4.2% over costed) imply both. Babywear also has no supplier cost history in costing.
- Allocation vs IMS store sets (03:22:Q1): the 40 cancelled allocations and the 40 IMS stockout stores overlap in only 8 stores.
- PLM MAT-RNYLON-TRIAL (£5.40, pilot) and MAT-RNYLON-100 (£8.76) are two recycled nylons from the same supplier; the IMS shoe lots (BATCH-SHOE-001 to 004) are not in WMS bins.
