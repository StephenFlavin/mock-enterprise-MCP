# mock-enterprise-MCP

96 mock enterprise systems, each served as its own MCP server, for one fictional company: **Harbour & Vale Retail Group**, a UK homewares and fashion retailer with about £1.2bn revenue, five DCs, stores, e-commerce and a global supply chain.

Together the servers expose about 2,000 tools: WMS, TMS, ERP/GL, PO, procurement, quality, HR, pricing, POS and many more. They are backed by consistent, reproducible data, built so that real persona questions ("which inbound containers will miss their DC slot this week, and what does it cost us?") need several systems to answer.

On top of the servers sits a benchmark: **how well does a model find its way through MCP tools as more and more of them fill its context**, and does it stay honest and safe while doing it?

Site, with a getting-started guide and example reports: https://stephenflavin.github.io/mock-enterprise-MCP/

## Quick start

Requires Python ≥ 3.11.

```
pip install -e ".[dev]"
python -m mockmcp serve                      # every system at http://127.0.0.1:8800/<system>/mcp
python -m mockmcp profile 01 4               # MCP client config for one persona (file 01, persona 4)
python -m mockmcp run wms get_location_inventory_balance '{"location_id": "DC1-C-14"}'   # call one tool
```

Point any MCP client at a server URL, or paste the `profile` output into its config (e.g. Claude Code's `--mcp-config`).

## What's in the box

| | |
|---|---|
| `systems/<id>/` | One system: `system.yaml` (tables + tools), `gen.py` (data generator), `seed/` (hand-written story rows), `scenarios.yaml`, generated `data/*.csv` |
| `systems/_master/` | Shared master data (sites, products, suppliers, carriers, POs, sales, …) that every system reuses |
| `world.yaml` | Facts every system agrees on: company, calendar, DCs, currency, seed |
| `catalog/` | Tool catalogue derived from the persona docs |
| `docs/assets/personas/` | The personas and their questions (with follow-ups), the source of every tool and benchmark task |
| `bench/` | Benchmark ground truth (`cases/`), trap bank (`traps.yaml`), recipes (`recipes/`) |
| `mockmcp/` | Engine (YAML + CSV → DuckDB → MCP), hub, CLI, and the `eval` pipeline |
| `site/` | The docs site (Astro + Starlight), deployed to GitHub Pages from `main` |

**Data is reproducible.**
- `data/` is exactly what `gen.py` + `seed/` produce, which `python -m mockmcp check` verifies.
- Writes made through tools are ephemeral per process, so every run starts from the same state.
- The world moves with the real date in whole weeks, keeping weekdays, and its "today" is always the latest Wednesday: "yesterday", "last week" and "the last 30 days" give the same answers whatever day you run.

## Benchmarking LLMs

`python -m mockmcp eval` builds tasks from the persona questions and runs them against recording copies of the servers. The agent harness is pluggable; headless Claude Code is the one built so far, and another agent, an agent SDK or a direct model-API loop can be added as a harness ([how](docs/BENCHMARKING.md#9-extending); pull requests welcome). Each task is graded by deterministic checks plus a judge: an LLM judge (headless Claude Code, the one to use), or a decision-model judge (Jev or a local Cygnet over the System One API) that answers small closed questions combined in code. Decision-model judges were evaluated and are **unreliable per task** (they warn when used; see `docs/BENCHMARKING.md` section 5). The judge sees a lean payload (the conversation, the expected answer, what code found, the writes made; no trace) and only judges; diagnosis stays in code (`--judge-debug` hands it the full trace instead). `eval calibrate` measures a judge against existing verdicts.

Tasks include:
- **Scenarios:** a question plus its follow-ups, graded as one pass/fail.
- **Single-system lookups.**
- **Traps:** missing systems, unknown ids, out-of-scope asks, tempting unsafe actions, approval flows, injected instructions, false premises.

Reports lead with *why* tasks failed:
- wrong server or wrong tool
- fabrication (claims no tool supports)
- unsafe or unrequested writes
- honest failure
- the tasks that break as tools are added

```
python -m mockmcp eval recipe bench/recipes/scale-80.yaml --out runs/scale-80 --harness claude-code   # 80 questions x 5 tool budgets
python -m mockmcp eval run    runs/scale-80 --model haiku --workers 8
python -m mockmcp eval grade  runs/scale-80 --judge claude-code --judge-model sonnet
python -m mockmcp eval report runs/scale-80                                                          # runs/scale-80/report.md, summary.json, report.json
python -m mockmcp eval report runs/scale-80 --html                                                   # + charts/*.svg and report.html
python -m mockmcp eval compare runs/scale-80-haiku runs/scale-80-sonnet --html                       # two runs task by task: compare.md, compare.html
```

**Scale recipes nest.**
- `scale-80` ⊂ `scale-160` ⊂ `scale-320` ⊂ `scale-all`: same seed, same question mix.
- Every task runs at five tool budgets, from only the servers it needs up to ~200k tokens of tool definitions. A bigger budget only adds servers.

So a model's results on more questions or more tools can be compared question by question.

Other recipes:
- `bench/recipes/smoke.yaml`: a 6-task end-to-end check.
- `bench/recipes/traps-hard.yaml`: 30 hard traps.

Full guide, including how to evaluate a model: [docs/BENCHMARKING.md](docs/BENCHMARKING.md).

## Working on the repo

| Command | What it does |
|---|---|
| `python -m mockmcp check [<id>]` | Lint every system, run every tool's example and scenario, verify `data/` matches its generator. Must print `ok`. |
| `python -m mockmcp gen <id>` | Regenerate a system's `data/*.csv` after changing `gen.py` or `seed/` |
| `python -m mockmcp brief <id>` | A system's tools and every persona question that uses them |
| `python -m mockmcp bench <id>` | Run a model against one system's ground-truth cases |
| `python -m mockmcp eval traps --check` | Validate the trap bank |
| `python -m mockmcp eval arithmetic` | Regenerate `bench/arithmetic.yaml` (facts got by arithmetic; `--check` to verify) |
| `python -m pytest -q` | Tests (~8 min) |

Guides:
- [AGENTS.md](AGENTS.md): how to work in this repo, for people and coding agents.
- [docs/BUILDING_A_SYSTEM.md](docs/BUILDING_A_SYSTEM.md): the contract for building one system.
- [bench/AUTHORING.md](bench/AUTHORING.md): writing benchmark cases.
- [docs/PLAN.md](docs/PLAN.md): the original design.
- [docs/examples/](docs/examples/): real reports and comparisons, also browsable on the site.

## Licence

MIT; see [LICENSE](LICENSE).
