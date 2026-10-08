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
