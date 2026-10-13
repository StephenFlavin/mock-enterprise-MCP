# Writing bench cases

A case tests whether ONE server, loaded alone, lets a small model answer its slice of a persona question.
Cases live in `bench/cases/<system>.yaml`; the format is at the top of `mockmcp/bench.py`.
Example: `bench/cases/cmms.yaml`.

## Steps
1. `python3 -m mockmcp brief <system>` lists the system's tools and the questions that use them (★ = this system's tools).
2. For each question, write one case for this system's part. Explore with
   `python3 -m mockmcp run <system> <tool> '{"arg": "value"}'` to find what the data really says.
3. `python3 -m mockmcp bench --validate <system>` must print `ok`. Do NOT run the model bench.

## The prompt
- The persona's ask, cut down to what THIS server can answer, in the words a user would type.
- Stay faithful to the question: same places, products, periods and problem. If the question is about Leeds,
  the case is about Leeds. Never move a case to wherever the data happens to have a story; if the data
  can't answer the question, that is a server problem (fix it, or record it in `notes`).
- Never name a tool. Never mention the database or columns.
- Master entities (SKU, supplier, site, asset, PO, carrier, employee) are given as **ids**: a real IMS or POS
  takes ids, not product names. Exception: systems that own a `search_*` tool (e.g. mdm `search_products`)
  get some cases that give a **name** so the lookup is tested.
- Scope it so there is one right answer: a site, an id, a period ("last 40 days", "last month").
- No absolute dates in prompts ("19 October", "2026-09-08"): the data moves to today in whole weeks at runtime.
  Say "in about two weeks", "last month". Facts may contain ISO dates; the grader shifts them.
- Write requests ("raise a requisition for…", "put the order on hold") are cases too.

## ref
The calls a good answer must make, with arguments. Only id-like argument values are graded
(right SKU, right site); dates and free text are not, so give them as you'd expect but don't worry.

## facts
2 to 5 things a correct answer MUST state, taken from the ref output, that the prompt directly asks for:
causes, components, statuses, quantities, totals, the top-ranked item. Not record ids the user didn't ask
about (STP-000007), not incidental columns, not column names, not raw codes a person wouldn't say
(`TR`, `ecommerce_dc`): use the words a good answer would use, or a list of forms (`["Turkey", "TR"]`).
For a write, the facts are what the user asked to change (the new date, the quantity), not the stored status.
Numbers are compared without commas and £ signs; dates match ISO or "10 November"; `_` matches a space.

## notes (optional)
If the seeded story is weak (the planted rows drown in generated noise, a story value contradicts master
data, the tool can't answer the question's part at all), add `notes: "..."` to the case. Do not edit the
system's data, gen.py or system.yaml.

## scenario_facts (optional)
The persona question's scenario requires the union of its cases' facts. When your prompt asks for more than the
question and its follow-ups do (a single highest item, a per-store figure, an input the scenario never gives), add
`scenario_facts: [...]` with only the facts the scenario's turns ask for (`[]` for none) and a comment saying why.
`python -m pytest -q tests/test_eval_recipe.py -k unasked` flags cases that look like this; review each one and
set `scenario_facts` (to the full `facts` if the scenario does ask for them). Never drop a fact a turn asks for.

## turn_facts (optional)
A trap built on a scenario's first turn(s) requires only the facts those turns ask for. `tasks.fact_turns()` works
out which turn asks for each fact from the words of the slice prompt, the turns and the fact's reference columns.
Where the words cannot tell (the December row of a monthly history is "last year's peak", which only a follow-up asks
about), pin the facts to the turns that ask for them, counting the question as turn 0 and its follow-ups from 1:
`turn_facts: {1: [88.2, 2.63]}`, with a comment saying why. A pinned fact belongs only to the turns listed.
