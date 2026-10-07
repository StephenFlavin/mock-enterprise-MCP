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
- Never name a tool. Never mention the database or columns.
- Master entities (SKU, supplier, site, asset, PO, carrier, employee) are given as **ids**: a real IMS or POS
  takes ids, not product names. Exception: systems that own a `search_*` tool (e.g. mdm `search_products`)
  get some cases that give a **name** so the lookup is tested.
- Scope it so there is one right answer: a site, an id, a period ("last 40 days", "last month").
- Write requests ("raise a requisition for…", "put the order on hold") are cases too.

## ref
The calls a good answer must make, with arguments. Only id-like argument values are graded
(right SKU, right site); dates and free text are not, so give them as you'd expect but don't worry.

## facts
2 to 5 things a correct answer MUST state, taken from the ref output, that the prompt directly asks for:
causes, components, statuses, quantities, totals, the top-ranked item. Not record ids the user didn't ask
about (STP-000007), not incidental columns. Use a list for equivalent forms: `[ "1,250", "1.25k" ]`.
Numbers are compared without commas and £ signs.

## notes (optional)
If the seeded story is weak (the planted rows drown in generated noise, a story value contradicts master
data, the tool can't answer the question's part at all), add `notes: "..."` to the case. Do not edit the
system's data, gen.py or system.yaml.
