# Mock Enterprise MCP: Implementation Plan

**Status:** Phase 0 built (engine, catalogue, master data, `yms` reference). The per-system build contract is
`docs/BUILDING_A_SYSTEM.md`. The changes below, made during implementation, supersede the sections they mention.

## 0. Changes made during implementation

- **Duplicate tools are kept, not resolved (supersedes §11 table 1).** A tool catalogued under two systems is built in
  both, as real enterprise estates overlap. `catalog/tools.csv` therefore has 2,017 rows: 2,008 unique tools plus
  9 duplicates. Only the 10 uncatalogued `draft_*` tools are assigned, in `catalog/overrides.csv`.
- **Larger master "spine" (extends §5.2).** Master holds the ids that several systems must agree on: sites, DC bin
  locations, DC equipment assets, products, suppliers, factories, carriers, ports, employees, cost centres, legal
  entities, partners, customers, customer orders, purchase orders and lines, inbound shipments, 52 weeks of sales
  and DC stock. Builders must reuse these ids and never edit master. Each master section has its own random seed,
  so adding data never reshuffles existing ids.
- **Scenarios live inside each system (replaces §7.3 scenario cards).** Each system has `systems/<id>/scenarios.yaml`
  with one entry per question that uses its tools, each holding the planted story and checks
  (tool + args + expected substrings). Builders work in parallel, so there are no shared scenario files. Cross-system
  consistency comes from master ids.
- **Catalogue tooling lives in the package.** `mockmcp/catalog.py` replaces `scripts/catalog.py`. CLI:
  `python -m mockmcp {serve, stdio, check, gen, run, brief, profile, catalog, reset}`. `brief <id>` gives a builder the
  system's tools plus the full text of every question that uses them.
- **Write-capable master.** Write tools can target `master.<table>` (for example, PO delivery date changes), so a
  change made in one system is seen by all of them.
- **Measured memory:** about 110 MB RSS for 96 systems × 20 tools once loaded, rising to about 200 MB after a round
  of queries. The 300 MB budget is kept.
- **Builds are done by Haiku subagents**, one per system, following `docs/BUILDING_A_SYSTEM.md`. Acceptance is
  `python -m mockmcp check <id>` plus a whole-catalogue smoke test, not code review.
**Source of truth:** `docs/assets/personas/` (personas, questions, tool catalogues).

## 1. Goal and scope

Build one MCP server for each enterprise system named in the persona tool catalogues. All servers share one fictional retail and global supply chain company and one mock dataset, so an AI agent can answer the persona questions by calling several systems in turn, just as it would in a real company.

| | Count | Notes |
|---|--:|---|
| Systems (MCP servers) | **96** | After merging `PLM` into `Product Lifecycle Management (PLM)` |
| Tools in scope | **2,008** | 1,998 from the catalogues, plus 10 `draft_*` tools that the question rows use but no catalogue lists (see §11) |
| Read tools | 1,702 | `get_`, `list_`, `search_`, `calculate_`, `compare_`, `run_`, `rank_`, `draft_` |
| Write tools (✎) | 306 | `create_`, `update_`, `cancel_`, `block_`, `approve_`, `send_`, `submit_`, and similar |
| Question rows covered | 520 | Across the 9 `tools-NN` files |

**Out of scope (external tools):** Web, Code Execution, Email & Calendar, and Collaboration & Messaging (Slack/Teams). Together they hold 162 tools, including `search_web`, `run_analysis`, `send_email` and `get_weather_*`. Questions that rely on them can only be partly answered. The agent is expected to do its own analysis in place of `run_analysis`.

**Third-party data feeds stay in scope** (Commodity & Market Data, Competitor Price Monitoring, Trend & Market Intelligence, Market Research). In a real enterprise these are licensed internal systems, not the open web.

**Tool names are the contract.** Names and read/write type come exactly from the catalogues so that the persona files can be used as a benchmark. The plan never renames a tool.

---

## 2. Key decisions

| Decision | Choice | Why |
|---|---|---|
| Language | **Python 3.12** | Smallest amount of code for this job: the official MCP SDK, DuckDB and YAML are all mature. Rust would save memory but needs several times more code per tool. |
| MCP library | Official `mcp` SDK, **low-level `Server`** API | Tools come from YAML, not from decorated Python functions, so a single generic `list_tools` / `call_tool` pair serves every system. `FastMCP` would need one Python function per tool. |
| Data store | **CSV files queried by DuckDB** | DuckDB treats CSVs as SQL tables with no import step and low memory. It is popular and runs in-process with no server. |
| Writes | **Append-only CSV overlay** | Writes add rows to `state/<system>/<table>.csv`. Seed data is never changed, and a reset just deletes `state/`. |
| Process model | **One "hub" process hosting all 96 servers**, each at its own URL (`http://127.0.0.1:8800/<id>/mcp`) | Each system is still a separate MCP server to the client. One Python process with one DuckDB connection costs a few hundred MB in total, where 96 separate processes would cost GBs. |
| Fallback transport | `python -m mockmcp stdio <id>` | For clients that only support stdio. It runs the same code with a different transport. |
| Tool definitions | **Declarative YAML for each system**, with a Python escape hatch | About 90% of tools become 5–15 lines of YAML. Only real calculations need Python. |
| Mock data | **Seeded generator for bulk data, plus hand-written seed rows** for the specific situations the questions describe | Bulk data is reproducible, and the question stories can be found exactly where the questions say they are. |
| Clock | Fixed **`AS_OF` date** in `world.yaml` | "Last 90 days", "this autumn" and "Q3" always mean the same thing, so tests stay deterministic. |

### Runtime dependencies (kept deliberately small)

- `mcp` (brings `pydantic`, `starlette`, `uvicorn`)
- `duckdb`
- `pyyaml`
- `jinja2` (for `draft_*` templates)

### Dev/gen-only dependencies

- `faker` (realistic names and addresses)
- `pytest`

### Memory budget (to be checked in Phase 0)

- Hub process, all 96 systems loaded and idle: **≤ 300 MB RSS**.
- DuckDB is capped with `SET memory_limit='256MB'; SET threads=2`.
- CSVs are read on demand by views, not loaded into RAM.
- Data size target: ≤ 5 MB of CSV per system and ≤ 150 MB overall.

---

## 3. How it works

```
 LLM client ──HTTP──► hub (uvicorn, 1 process)
                       ├── /ims/mcp ─► Server("ims")  ┐
                       ├── /wms/mcp ─► Server("wms")  │  generic list_tools / call_tool
                       └── … 96 mounts                ┘  driven by systems/<id>/system.yaml
                                     │
                                     ▼
                       DuckDB (1 in-memory connection)
                       schema per system: views over CSV
                       ├── master.*   → systems/_master/data/*.csv
                       ├── ims.*      → systems/ims/data/*.csv ∪ state/ims/*.csv
                       └── …
```

1. **Startup.** The hub reads `world.yaml` and every `systems/*/system.yaml`, then validates them with pydantic models. For each table it creates a DuckDB view in that system's schema (details in §5). It then builds one low-level MCP `Server` per system and mounts it at `/<id>/mcp` using `StreamableHTTPSessionManager(stateless=True, json_response=True)`. Stateless mode keeps no per-session memory. All the session managers run under one combined Starlette lifespan.
2. **`list_tools`** returns the tool list for the system, built once at startup from YAML: name, description, JSON Schema for the inputs, and MCP `annotations` (`readOnlyHint`, `destructiveHint`, `idempotentHint`) taken from the catalogue's R/W type.
3. **`call_tool`** does five things in order:
   1. Validates and normalises the arguments (§6.3).
   2. Dispatches on the tool's `kind` (§4.2).
   3. Runs the SQL on a fresh DuckDB cursor in a worker thread. The `search_path` is set to `<id>,master` so the system can only see its own tables plus shared master data.
   4. Formats the result compactly (§6.4).
   5. Returns `TextContent`, with `isError=true` and a recovery hint when something fails.
4. **Isolation between systems.** A system's SQL can only read its own schema and `master`. `mockmcp check` enforces this by rejecting any `<other_id>.` reference. Agents therefore have to call several systems to join data, which is the behaviour the benchmark is testing.

---

## 4. Repository layout and the per-system pattern

```
pyproject.toml
world.yaml                     # company facts, AS_OF date, currency, ID formats, row budgets
mockmcp/                       # the engine — target ≤ 600 lines total
  __main__.py                  # CLI: serve | stdio <id> | check [<id>] | gen [<id>] | reset [<id>] | catalog [--system <id>] | profile <persona>
  spec.py                      # pydantic models for system.yaml + loader
  db.py                        # DuckDB connection, view creation, overlay writes
  kinds.py                     # one small function per tool kind
  args.py                      # JSON Schema generation, coercion, ID resolution
  fmt.py                       # compact result formatting
  server.py                    # low-level Server factory, hub app, stdio runner
  genlib.py                    # shared generator helpers (seeded RNG, master lookups, write_csv, overlay seeds)
systems/
  _master/                     # shared entities (not an MCP server)
    gen.py  seed/*.csv  data/*.csv
  ims/
    system.yaml                # tables + tools (the only file most tools need)
    gen.py                     # bulk data generator for this system
    seed/*.csv                 # hand-written rows: scenario stories + reference data
    data/*.csv                 # committed output of gen.py ∪ seed (what the server reads)
    files/                     # optional long text (documents, policies, contracts) as .md/.csv
    hooks.py                   # optional; only for kind: py tools
  wms/ …                       # identical shape for all 96 systems
scenarios/
  01-p04-q1.md                 # one card per question (§7.3)
scripts/
  catalog.py                   # persona docs → catalog/tools.csv (run when the docs change)
catalog/
  tools.csv                    # generated from the persona docs: tool, system_id, rw, desc, used_by
  overrides.csv                # hand decisions: conflicts, uncatalogued tools
tests/
  test_catalog.py              # every in-scope tool implemented exactly once, R/W matches
  test_tools.py                # every tool runs with its example args
  test_scenarios.py            # every scenario card's assertions pass
state/                         # gitignored write overlay
```

Every system has **the same five artefacts**: `system.yaml`, `gen.py`, `seed/`, `data/`, and optionally `hooks.py` / `files/`. Nothing system-specific lives in the engine.

### 4.1 `system.yaml` shape

```yaml
id: wms
name: Warehouse Management System (WMS)
instructions: >          # ≤ 3 sentences; sent as MCP server instructions
  Bin-level stock, tasks and receipts for our 4 DCs. Locations look like DC1-C-14-02
  (site-aisle-bay-level). Today is {AS_OF}. Money is GBP.

tables:
  locations:
    key: location_id
    cols:
      location_id: {type: str, desc: "Bin, e.g. DC1-C-14-02", ref: true}
      site_id:     {type: str, desc: "DC, e.g. DC1"}
      zone:        {type: enum, values: [ambient, chilled, mezzanine, bulk]}
      status:      {type: enum, values: [active, blocked, damaged]}
      max_weight_kg: {type: float}
  stock_movements:
    key: movement_id
    cols: {movement_id: {type: str}, location_id: {type: str}, sku: {type: str},
           qty: {type: int}, moved_at: {type: timestamp}, type: {type: enum, values: [pick, putaway, replen, adjust]}}

tools:
  - name: get_stock_movements_for_location
    desc: Stock movements in one bin, newest first. Use to explain count differences.
    kind: select
    from: stock_movements
    filters:
      location_id: {required: true}
      sku: {}
      date_from: {col: moved_at, op: ">=", default: "-90d"}
      type: {}
    order: moved_at desc
    example: {location_id: DC1-C-14-02}

  - name: block_location
    desc: Put a hold on a bin so no picks or putaways go to it. Returns the updated bin.
    kind: update
    table: locations
    key_arg: location_id
    set: {status: blocked}
    args: {reason: {type: str, required: true, desc: "Why the bin is held"}}
    example: {location_id: DC1-C-14-02, reason: recount}
```

Column definitions do double duty. They give DuckDB explicit CSV types (no auto-detection surprises), and they supply argument types and descriptions to any tool that filters on the column. Write each description once and reuse it everywhere.

### 4.2 Tool kinds (the only patterns allowed)

| Kind | Used for | What the YAML gives | What the engine does |
|---|---|---|---|
| `select` | Most `get_` / `list_` / `search_` tools | `from`, `filters`, optional `columns`, `order`, `limit` | Builds parameterised SQL. Filter args take their types from the column definitions. `op: like` turns into case-insensitive `ILIKE '%…%'` for `search_` tools. |
| `sql` | Aggregates, `calculate_`, `compare_`, `rank_`, grouped `get_..._by_...` | `args` + a SQL string using `$arg` params | Binds named params, filling unspecified optional args with `NULL`. The usual idiom is `($x IS NULL OR col = $x)`. |
| `insert` | `create_`, `send_`, `submit_`, `raise_` | `table`, `args` → columns, `defaults` (e.g. `status: open`), `id_prefix` | Builds an ID such as `CC-` plus a sequence number, fills `created_at = AS_OF`, appends a row to the overlay, and returns the new record. |
| `update` | `update_`, `cancel_`, `block_`, `approve_`, `archive_`, `reassign_`, `release_`, `remove_`, `delete_` (soft) | `table`, `key_arg`, `set` (fixed values) and/or args mapped to columns | Reads the current row, merges in the changes, appends the merged row to the overlay, and returns the before and after values of the changed fields. |
| `draft` | `draft_*` (read-only, never writes) | `sql` (context query, may be several) + Jinja2 `template` | Fills the template from the query results and returns the text. |
| `py` | The few calculations SQL cannot express cleanly | `args` + `fn: hooks.calc_x` | Calls `fn(db, args, world)`, which must return rows (a list of dicts) or text. |

**Target mix for each system:** `py` under 10% of its tools. Anything that can be written as SQL is written as SQL.

`send_*` and `submit_*` tools are in-system writes, not external messaging. For example, `send_rfq_to_suppliers` inserts into `sourcing.rfq_invitations`, and `submit_price_change_for_approval` inserts into `pricing.approvals`. Each system that has them gets an `outbox` or `requests` table.

---

## 5. Data design

### 5.1 The fictional company (`world.yaml`)

All of this lives in one file so every generator and the server instructions agree on the facts:

- **Name:** a fictional UK-headquartered retail group with a global supply chain. Never a real company.
- **Base currency and dates:** GBP base currency. `AS_OF: 2026-10-05`. Financial year runs Feb–Jan on a 4-4-5 retail calendar. Peak is Nov–Dec.
- **Network:** 4 DCs (UK ×2, EU ×1, US ×1), about 120 stores, an e-commerce site, a marketplace channel, wholesale and franchise partners.
- **Sourcing:** about 80 suppliers and about 150 factories across CN, BD, VN, IN, TR, PT and MX. About 15 carriers and forwarders. Ports at Felixstowe, Southampton, Rotterdam, Shanghai, Chittagong and others.
- **Product range:** about 1,500 SKUs across apparel, home, beauty and electricals, so the hazmat, battery and chemical-compliance questions have something to apply to.
- **ID formats:** one prefix per entity, e.g. `SKU-100234`, `PO-2026-004512`, `SUP-0042`, `FAC-0107`, `ST-045`, `DC1`, bins `DC1-C-14-02`, `ASN-…`, `GR-…`.
- **Row budgets:** for example, at most 50k rows per table, weekly granularity for long histories, and daily granularity only for the last 120 days. This keeps memory and disk use low.

The exact values are settled in Phase 0 by scanning the questions for named entities such as bay C-14, "August", "Q3" and named countries.

### 5.2 Master data (`systems/_master`)

Master data is shared and read-only: products, suppliers, factories, sites, carriers, employees (only those the questions need), cost centres, the retail calendar and currencies. Every system can see it through the `master` schema. System tables use master keys as foreign keys, which is what keeps the systems consistent with each other.

### 5.3 Views and the write overlay

Each table becomes one DuckDB view:

```sql
CREATE VIEW ims.adjustments AS
SELECT * EXCLUDE (_seq, _op) FROM (
  SELECT *, 0 AS _seq, 'base' AS _op FROM read_csv('systems/ims/data/adjustments.csv', header=true, columns={...})
  UNION ALL BY NAME
  SELECT * FROM read_csv('state/ims/adjustments.csv', header=true, columns={..., _seq:'BIGINT', _op:'VARCHAR'})
)
QUALIFY row_number() OVER (PARTITION BY adjustment_id ORDER BY _seq DESC) = 1
  AND _op <> 'delete';
```

- **Overlay files.** At startup the engine creates header-only overlay files, so a view never refers to a missing file.
- **Appends.** Rows are appended with Python's `csv` module, under one `asyncio.Lock` per table. `_seq` comes from `time.time_ns()`.
- **Visibility.** Views re-read the CSVs on every query, so a write is visible to the next call with no cache to invalidate.
- **Reset.** `mockmcp reset [<id>]` deletes the `state/` files.

### 5.4 Generated vs hand-written data

**`gen.py`** (one per system) has the same signature everywhere: `generate(g: Gen) -> dict[str, list[dict]]`. `Gen` gives it a seeded `random.Random`, `Faker`, the `world` settings, master data lookups and date helpers relative to `AS_OF`. The generator produces realistic background volume plus normal noise.

**`seed/<table>.csv`** holds the hand-written rows, which come in two sorts:
- **Reference data** such as cause codes, SOP text, policy articles, contract clauses and regulation summaries.
- **Story rows** for the scenario cards.

`mockmcp gen <id>` runs the generator, then overlays the seed rows: a seed row replaces any generated row with the same key, and new keys are added. It writes the result to `data/*.csv`, which is committed. Committing the output means:
- servers start without a generation step;
- data changes show up as reviewable diffs;
- a cheap LLM evaluation is reproducible.

**Long text** (documents, KB articles, audit reports, contracts) lives in `files/*.md`. Each system has an index table with columns `doc_id, title, type, tags, path, …`. `read_document` returns the file's contents. `search_*` tools run `ILIKE` keyword matching on title, tags and body, ranked by the number of matching terms. No search extension is needed, so DuckDB does not have to download anything. "Attached" files in the questions, such as `adj_Q3.csv`, live under `systems/documents/files/`.

Text that is too much to write by hand, such as 40 KB articles or 30 contracts, can be drafted once with an LLM while authoring, then reviewed and committed as data. It is never generated at runtime.

---

## 6. Tuning for a cheap/fast LLM

A small model fails mainly in five ways: it picks the wrong tool among similar ones, gets argument formats wrong, drowns in long outputs, gives up after an error, and repeats writes. Each rule below addresses one of these, and the engine enforces it so that every system behaves the same way.

### 6.1 Tool lists

- **Short descriptions.** 8–25 words, saying what the tool returns first and then when to use it. Example: "Stock movements in one bin, newest first. Use to explain count differences." `mockmcp check` fails any description over 30 words.
- **Telling apart similar tools.** When two tools in a system have similar names (for example `get_shrink_by_category` and `get_shrink_by_store`), each description says "Not for X — use Y". `check` lists pairs of names in the same system that share three or more words and have no "use" hint.
- **Flat arguments.** Only scalars and lists of scalars, never nested objects. At most 6 arguments, preferably 1–2 of them required. Every argument has a one-line description with an example value.
- **Enums.** Wherever the set of values is closed, it is an enum, so the model sees the allowed values in the schema.
- **Short server instructions.** At most 3 sentences: what the system covers, its ID formats, and the `AS_OF` date and currency.
- **Per-persona profiles.** `mockmcp profile 4` prints an MCP client config containing only the systems that persona's question rows use (derived from `catalog/tools.csv`). A cheap model then sees around 8 servers instead of 96. An optional second step is a `?persona=4` URL parameter that filters `list_tools` down to the tools that persona uses. This should be built only if tool-selection accuracy on the larger systems (IMS has 87 tools) proves to be a problem.

### 6.2 Defaults

- **Date defaults.** Date ranges default to sensible windows relative to `AS_OF`, such as `-90d` or `this_quarter`, so "why is the count off?" works with just a location ID.
- **Ordering.** List tools are sorted with the most useful rows first: by value descending, by recency, or by severity.
- **Row limits.** `limit` defaults to 20 and is capped at 200.

### 6.3 Forgiving input (in `args.py`, applied to every tool)

- **Case and spacing.** IDs and enums are case-insensitive and whitespace-trimmed: `dc1-c-14` and `C-14` resolve when they are unambiguous.
- **`ref: true` columns accept an ID or a name.** "Acme Textiles" resolves to `SUP-0042`. If nothing matches exactly, `difflib.get_close_matches` finds the nearest values. One strong match is used, and the output says so (`note: matched "Acme Textile Ltd" (SUP-0042)`). Several matches produce an error listing the top 3.
- **Dates.** `2026-08`, `2026-08-14`, `Q3`, `FY26 P7`, `last 30 days` and `yesterday` are normalised against `AS_OF` by one small parser.
- **Numbers.** `"£500"` and `"1,200"` are coerced to numbers.

### 6.4 Compact output (in `fmt.py`)

- **One record:** `key: value` lines.
- **Several records:** CSV with a header row. This takes roughly half the tokens of JSON objects, and small models read it well.
- **Summary line first,** for example: `12 of 340 rows (sorted by value desc). Narrow with zone= or date_from=.` A truncated result always names the filters that would narrow it.
- **Number formatting.** Numbers are rounded to 2 decimal places, money columns carry their currency in the column name (`value_gbp`), and nulls print as empty.
- **Calculations show their working.** `calculate_*` tools return the result, the inputs used and a one-line formula, so the model can explain its answer without recomputing.

### 6.5 Errors

- **Returned, not raised.** Every error is a normal tool result with `isError=true`, a plain sentence and a next step. For example: `Unknown location "C14". Closest: DC1-C-14-01, DC1-C-14-02. Or call list_locations with zone=…`
- **Never a stack trace.** Nothing is logged to stdout either, because stdout is the transport in stdio mode.

### 6.6 Writes

- **Annotations.** Write tools carry `readOnlyHint=false` and `destructiveHint` (true for cancel, delete, block and archive), so the client can ask a human to confirm, as the ✎ legend expects.
- **Idempotent inserts.** If the same tool is called with identical arguments within the same session window, it returns the row that already exists, with the note `already created`, instead of writing a duplicate. This guards against small models retrying.
- **Clear confirmation.** A write returns `Done.` plus the record as it now stands (or its before and after values), so the model does not need to read it back.

---

## 7. Process for building each system

"Built in its entirety" means every catalogued tool for that system works on realistic data, and every question that touches the system can be answered from it.

### 7.1 Steps (the same for all 96 systems)

1. **Collect.** `mockmcp catalog --system <id>` lists the system's tools (from `catalog/tools.csv`) and every question row that uses them, with the full question text and follow-ups from the `questions-NN` files.
2. **Model the tables.** Design the smallest set of tables (usually 3–10) that can answer every tool. Reuse master keys. Write the `tables:` block.
3. **Write scenario cards** (or extend existing ones) for each question that touches this system (§7.3).
4. **Write `gen.py`** for background volume, keeping within the row budget.
5. **Hand-write `seed/` rows** for the stories in the scenario cards, plus reference data and `files/` text.
6. **Write `tools:`**, using the cheapest kind that works (`select` → `sql` → `draft` → `py`). Every tool gets an `example`.
7. **Generate and check.** Run `mockmcp gen <id>` and `mockmcp check <id>` (schema, lint, isolation and catalogue coverage), then `pytest -k <id>`.
8. **Exercise with a cheap model.** Run the system's questions through a cheap model with the persona profile loaded, and fix any tool descriptions or data that caused it to stumble.

### 7.2 Definition of done (for each system)

- [ ] Every catalogue tool for this system is implemented, with R/W matching the catalogue.
- [ ] `check` passes: description and argument lint, no cross-schema SQL, every `ref` resolves.
- [ ] Every tool returns a non-empty, non-error result for its `example`.
- [ ] Every write tool, after `reset`, writes once, shows up in the matching read tool, and is idempotent when retried.
- [ ] Every scenario assertion involving this system passes.
- [ ] `data/` is within the row budget, and the hub's memory stays within budget with the system loaded.

### 7.3 Scenario cards (`scenarios/<file>-p<persona>-q<n>.md`)

One card per question row. Cards are short and become tests. Worked example:

```markdown
# 01-p04-q1 · Inventory control · "Why is the count for bay C-14 so off?"
Systems: wms, ims
Story: DC1 bay C-14 has 3 count variances in 90 days, all on SKU-100877. Cause: on 2026-08-12 a
layout change moved SKU-100877's pick face from C-14-02 to C-15-01, but 2 replen tasks
still put stock into C-14-02 (old slot) — system shows 0, physical shows 48.
Seed rows: wms/locations (C-14-01..04), wms/stock_movements (MV-9001..9014),
           ims/cycle_count_results (CC-7781..7783), ims/adjustments (ADJ-55120..55122)
Assertions:
- wms.get_stock_movements_for_location {location_id: DC1-C-14-02} contains "SKU-100877" and "replen"
- ims.list_cycle_count_results_for_location {location_id: DC1-C-14-02} rows >= 3
- wms.block_location {location_id: DC1-C-14-02, reason: recount} then wms.get_location... contains "blocked"
```

`tests/test_scenarios.py` parses the **Assertions** block from each card. That gives you:
- a regression suite;
- a guarantee that each question's story can actually be found.

The cards also double as the answer key for evaluating cheap models later.

When a story spans several systems, as most do, the card lists the seed rows for each system involved. When those systems are built later, they pick up their part of the card. Cross-system IDs are fixed in the card up front, so they always match.

---

## 8. Build phases

### Phase 0: Foundation (no systems yet)

- [ ] `pyproject.toml` (uv), dependencies as listed in §2.
- [ ] `scripts/catalog.py`: parses `docs/assets/personas/tools-*.md` into `catalog/tools.csv`, normalises system names to the ids in §10, applies `catalog/overrides.csv`, and drops the external systems. It also records `used_by` (persona and question) for each tool, which feeds `profile`.
- [ ] Engine modules from §4: spec, db/overlay, kinds, args, fmt, server (hub and stdio), CLI.
- [ ] `world.yaml` and `systems/_master` (generator and seed).
- [ ] The three test files, parametrised over all systems.
- [ ] **Spike to check the memory claim:** a hub with 96 dummy systems × 20 `select` tools. Measure RSS when idle and under 10 concurrent calls. If it is over budget, the first fallback is sharing the per-system `Server` objects' tool lists more lazily. Separate processes are the last resort.
- [ ] Build one reference system end to end (`yms`, 2 tools) to prove the pattern before scaling up.

### Phases 1–9: Build the waves

One system at a time, following §7. Waves are ordered so that systems owning heavily used data come first and stories can be built on them.

| Phase | Wave | Systems | Tools |
|---|---|--:|--:|
| 1 | Warehouse, inventory, knowledge | 10 | 261 |
| 2 | Procurement and supplier | 9 | 282 |
| 3 | Transport and trade | 11 | 263 |
| 4 | Planning | 8 | 167 |
| 5 | Commercial, stores and e-commerce | 18 | 290 |
| 6 | Product, quality and costing | 15 | 323 |
| 7 | Finance | 10 | 165 |
| 8 | Risk and ESG | 3 | 85 |
| 9 | Data, tech, leadership, HR and PPM | 12 | 162 |

Systems within a wave are independent once their scenario cards exist, so they can be built in parallel.

### Phase 10: Hardening

- [ ] Run every question row against a cheap model with persona profiles. Track tool-selection accuracy and task success for each system, and fix the worst descriptions first.
- [ ] Optional `?persona=` tool filtering, if the data in the step above supports it.
- [ ] Final memory and latency check on all 96 systems.

---

## 9. Estimated code footprint

| Part | Size |
|---|---|
| Engine (`mockmcp/`) | ~500–600 lines of Python, written once |
| Generators | ~50–150 lines per system; `_master` ~200 |
| `hooks.py` | Only where needed; ~0–80 lines per system |
| `system.yaml` | ~5–15 lines per tool. This is data, not logic, and is the bulk of the repo. |
| Tests | 3 files, ~150 lines in total, driven entirely by data |

There is nothing per-system in the engine, no per-tool Python by default, and no per-system test code.

---

## 10. System inventory and build waves

Tool counts are from the catalogues, excluding external tools, and use each tool's first catalogued owner. They will shift by ±1 once the §11 overrides are applied. The 10 tools not in any catalogue (§11) are added in Phase 0.

**Wave 1** (10 systems, 261 tools)

| id | System | Tools | R | W |
|---|---|--:|--:|--:|
| `ims` | Inventory Management System (IMS) | 87 | 76 | 11 |
| `wms` | Warehouse Management System (WMS) | 53 | 46 | 7 |
| `wcs` | Warehouse Control System (WCS) | 8 | 7 | 1 |
| `yms` | Yard Management System (YMS) | 2 | 1 | 1 |
| `slotting` | Slotting & Layout Tool | 4 | 4 | 0 |
| `lms` | Labour Management System (LMS) | 18 | 17 | 1 |
| `cmms` | Maintenance Management System (CMMS) | 9 | 7 | 2 |
| `hse` | Health & Safety System | 11 | 9 | 2 |
| `kb` | Knowledge Base / Policy Library | 38 | 35 | 3 |
| `documents` | Documents | 31 | 31 | 0 |

**Wave 2** (9 systems, 282 tools)

| id | System | Tools | R | W |
|---|---|--:|--:|--:|
| `po` | Purchase Order System | 57 | 45 | 12 |
| `supplier_portal` | Supplier Portal | 45 | 36 | 9 |
| `srm` | Supplier Relationship Management (SRM) | 24 | 16 | 8 |
| `supplier_risk` | Supplier Onboarding & Risk System | 40 | 33 | 7 |
| `sourcing` | Sourcing / RFx Platform | 23 | 15 | 8 |
| `contracts` | Contract Management System | 42 | 35 | 7 |
| `spend` | Spend Analytics Platform | 27 | 25 | 2 |
| `mdm` | Master Data Management (MDM) | 7 | 5 | 2 |
| `commodity` | Commodity & Market Data Feed | 17 | 15 | 2 |

**Wave 3** (11 systems, 263 tools)

| id | System | Tools | R | W |
|---|---|--:|--:|--:|
| `tms` | Transport Management System (TMS) | 61 | 54 | 7 |
| `carrier_portal` | Carrier Portal | 23 | 19 | 4 |
| `freight_rates` | Freight Rate Management System | 28 | 28 | 0 |
| `forwarder` | Freight Forwarder Portal | 16 | 10 | 6 |
| `container` | Container Visibility Platform | 20 | 20 | 0 |
| `track_trace` | Track & Trace Platform | 11 | 10 | 1 |
| `last_mile` | Last-Mile Delivery Platform | 21 | 19 | 2 |
| `telematics` | Fleet Telematics | 3 | 3 | 0 |
| `customs` | Customs & Trade Compliance System | 34 | 28 | 6 |
| `tax_duty` | Tax & Duty System | 30 | 28 | 2 |
| `landed_cost` | Landed Cost Calculator | 12 | 12 | 0 |

**Wave 4** (8 systems, 167 tools)

| id | System | Tools | R | W |
|---|---|--:|--:|--:|
| `demand` | Demand Planning System | 65 | 60 | 5 |
| `supply_planning` | Supply Planning System (MRP/DRP) | 24 | 19 | 5 |
| `inv_opt` | Inventory Optimisation Tool | 14 | 13 | 1 |
| `allocation` | Allocation & Replenishment System | 5 | 5 | 0 |
| `sop` | S&OP Platform | 15 | 14 | 1 |
| `mfp` | Merchandise Financial Planning | 14 | 13 | 1 |
| `range_planning` | Range Planning & Assortment Tool | 7 | 4 | 3 |
| `network_design` | Network Design Tool | 25 | 24 | 1 |

**Wave 5** (18 systems, 290 tools)

| id | System | Tools | R | W |
|---|---|--:|--:|--:|
| `pos` | Point of Sale (POS) | 14 | 13 | 1 |
| `oms` | Order Management System (OMS) | 24 | 19 | 5 |
| `ecommerce` | E-commerce Platform | 14 | 11 | 3 |
| `pricing` | Pricing & Promotion Engine | 57 | 44 | 13 |
| `competitor_prices` | Competitor Price Monitoring Tool | 29 | 29 | 0 |
| `marketplace` | Marketplace Seller Portal | 9 | 8 | 1 |
| `wholesale_edi` | Wholesale / EDI Portal | 9 | 7 | 2 |
| `franchise` | Franchise Management Portal | 9 | 7 | 2 |
| `store_ops` | Store Operations Platform | 22 | 16 | 6 |
| `store_wfm` | Store Workforce Management | 10 | 8 | 2 |
| `loss_prevention` | Loss Prevention & Incident System | 11 | 8 | 3 |
| `cctv` | CCTV / Exception Reporting | 2 | 2 | 0 |
| `returns` | Returns Management System (RMS) | 31 | 27 | 4 |
| `customer_service` | Customer Service Platform | 7 | 6 | 1 |
| `reviews` | Customer Reviews & Feedback Platform | 14 | 14 | 0 |
| `cdp` | Customer Data Platform (CDP) | 5 | 5 | 0 |
| `web_analytics` | Web Analytics Platform | 9 | 9 | 0 |
| `property` | Retail Property & Footfall System | 5 | 5 | 0 |

**Wave 6** (15 systems, 323 tools)

| id | System | Tools | R | W |
|---|---|--:|--:|--:|
| `plm` | Product Lifecycle Management (PLM) | 34 | 28 | 6 |
| `pim` | Product Information Management (PIM) | 16 | 12 | 4 |
| `dam` | Digital Asset Management (DAM) | 1 | 0 | 1 |
| `sampling` | Sampling & Development Tracker | 11 | 8 | 3 |
| `packaging_design` | Packaging Design System | 17 | 16 | 1 |
| `test_lab` | Test Lab / LIMS | 25 | 23 | 2 |
| `qms` | Quality Management System (QMS) | 27 | 18 | 9 |
| `factory_audit` | Factory Audit Platform | 15 | 10 | 5 |
| `compliance_db` | Product Compliance & Regulatory Database | 35 | 32 | 3 |
| `packaging_epr` | Packaging Compliance & EPR System | 17 | 15 | 2 |
| `recall` | Incident & Recall Management System | 13 | 8 | 5 |
| `costing` | Costing & Margin Tool | 72 | 69 | 3 |
| `cost_model` | Cost Modelling Tool | 13 | 13 | 0 |
| `trend` | Trend & Market Intelligence Platform | 14 | 14 | 0 |
| `market_research` | Market Research Platform | 15 | 15 | 0 |

**Wave 7** (10 systems, 165 tools)

| id | System | Tools | R | W |
|---|---|--:|--:|--:|
| `gl` | ERP (General Ledger) | 33 | 27 | 6 |
| `ap` | Accounts Payable System | 25 | 19 | 6 |
| `ar` | Accounts Receivable System | 17 | 13 | 4 |
| `budgeting` | Budgeting & Forecasting Tool | 33 | 29 | 4 |
| `consolidation` | Consolidation & Reporting Tool | 8 | 6 | 2 |
| `cost_allocation` | Cost Allocation Tool | 10 | 8 | 2 |
| `treasury` | Treasury Management System | 13 | 11 | 2 |
| `fx` | FX & Hedging Platform | 16 | 15 | 1 |
| `fixed_assets` | Fixed Asset Register | 2 | 2 | 0 |
| `internal_audit` | Internal Audit System | 13 | 9 | 4 |

**Wave 8** (3 systems, 85 tools)

| id | System | Tools | R | W |
|---|---|--:|--:|--:|
| `risk` | Risk Management System | 24 | 19 | 5 |
| `due_diligence` | Supply Chain Due Diligence Platform | 27 | 25 | 2 |
| `esg` | Carbon & ESG Reporting Platform | 34 | 29 | 5 |

**Wave 9** (12 systems, 162 tools)

| id | System | Tools | R | W |
|---|---|--:|--:|--:|
| `ppm` | Project & Portfolio Management Tool | 45 | 23 | 22 |
| `itsm` | Application Monitoring & ITSM | 21 | 14 | 7 |
| `integration` | Integration Platform / API Gateway | 10 | 9 | 1 |
| `identity` | Identity & Security Platform | 11 | 8 | 3 |
| `ml_platform` | ML Platform / Model Registry | 11 | 8 | 3 |
| `data_warehouse` | Data Warehouse / Lakehouse | 18 | 17 | 1 |
| `data_quality` | Data Quality & Observability Tool | 7 | 5 | 2 |
| `bi` | BI & Dashboards Platform | 10 | 9 | 1 |
| `kpi` | Executive KPI Scorecard | 10 | 9 | 1 |
| `board` | Strategy & Board Reporting Tool | 4 | 3 | 1 |
| `hris` | HR Information System (HRIS) | 13 | 11 | 2 |
| `ats` | Recruitment / ATS | 6 | 4 | 2 |

---

## 11. Catalogue issues to resolve in Phase 0 (`catalog/overrides.csv`)

**Tools catalogued under two systems.** The rule: the owner is the system holding the tool's primary entity, so there is exactly one owner. Suggested owners:

| Tool | Catalogued under | Suggested owner |
|---|---|---|
| `create_cycle_count_task` | IMS, WMS | `wms` (count tasks are warehouse tasks; the results land in IMS) |
| `draft_corrective_action_plan` | Factory Audit, Customs | `factory_audit` |
| `draft_negotiation_brief` | Contracts, Documents | `contracts` |
| `get_carrier_contract_rates` | Contracts, Freight Rates | `freight_rates` |
| `calculate_break_even_volume` | Costing, Network Design | `costing` |
| `get_shrink_by_category` | IMS, Costing | `ims` |
| `calculate_hedge_scenarios` | Treasury, FX & Hedging | `fx` |
| `get_damage_rate_by_pack_type` | QMS, Returns | `returns` |
| `create_supplier_corrective_action_request` | QMS, Supplier Portal | `qms` |
| `search_classification_rulings` | Customs, Web | `customs` (internal rulings library) |

**Tools used in question rows but missing from every catalogue.** Assign each to the system of its row's main entity:

| Tool | Suggested owner |
|---|---|
| `draft_cycle_count_sheet` | `wms` |
| `draft_supplier_variance_note` | `supplier_portal` |
| `draft_root_cause_report` | `qms` |
| `draft_short_shipment_message_to_customers` | `oms` |
| `draft_loss_prevention_case_summary` | `loss_prevention` |
| `draft_store_visit_action_plan` | `store_ops` |
| `draft_compliance_checklist` | `compliance_db` |
| `draft_response_to_customer_buyer` | `wholesale_edi` |
| `draft_market_entry_brief` | `documents` |
| `draft_recommendation_summary` | `documents` |

**Name normalisation.** `PLM` becomes `plm`. The `Web` / `Web (public search/fetch)` and `Code Execution` variants are merged and then excluded.

---

## 12. Risks and mitigations

| Risk | Mitigation |
|---|---|
| About 2,000 tools is a lot of YAML to author | The `select` kind and reusable column definitions keep most tools to about 6 lines. Waves can be built in parallel. Lint catches mistakes early. |
| Large systems (IMS 87, Costing 72, Demand 65) overwhelm a small model | Per-persona profiles, then optional `?persona=` tool filtering. Descriptions that say which neighbouring tool to use instead. |
| Questions about `calculate_*` tools need believable logic | Use simple, documented formulas (shown in the output), and plant data so the answer is clear-cut. Realism comes from the data, not from complex models. |
| Stories drift apart across systems | Scenario cards fix the cross-system IDs before any system is built, and tests assert them. |
| CSV overlay grows over a long evaluation run | `reset` between runs. Overlays are small, typically fewer than 1,000 rows. |
| DuckDB re-reads CSVs on every query | The files are small (≤ 5 MB each), so a query takes milliseconds. If a hot table proves slow, cache only the base CSV as a DuckDB table and keep the overlay as a live read. |
