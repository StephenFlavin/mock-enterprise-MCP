# AGENTS.md

Guidance for coding agents and people working in this repo. Read it before changing anything; the linked docs hold the detail.

## What this repo is

1. **96 mock enterprise systems.** Each is one MCP server, defined declaratively: `systems/<id>/system.yaml` plus generated CSV data, served by one engine (`mockmcp/`, YAML + CSV → DuckDB → MCP).
2. **A benchmark built on the persona questions** (`docs/assets/personas/`). It sits on top: ground truth in `bench/`, pipeline in `mockmcp/eval/`.

The servers exist to make the benchmark realistic and *fair*.

## Verify your work

| You changed | Run | Must show |
|---|---|---|
| a system (`systems/<id>/`) | `python -m mockmcp gen <id>` then `python -m mockmcp check <id>` | `ok   <id>` |
| master data, `world.yaml`, the engine | `python -m mockmcp check` (all systems) | no failures |
| `bench/cases/` | `python -m mockmcp check` + `python -m pytest -q tests/test_eval_recipe.py` | pass |
| the trap bank or `trap_seeds.py` | `python -m mockmcp eval traps` then `python -m mockmcp eval traps --check` | exit 0, no problems |
| `mockmcp/eval/` | `python -m pytest -q tests/test_eval_*.py` | pass |
| anything, before you finish | `python -m pytest -q` (~8 min) | pass |

Known flaky test: `tests/test_systems.py::test_system[itsm]` (scenario 01:10:Q5 expects `45.7`). It is date-dependent and fails without any local changes too. Don't "fix" it by loosening the check; fix the data or the scenario if you touch it.

## Invariants (easy to break, expensive to notice)

- **`data/*.csv` is generated, never hand-edited.**
  - It must equal `gen.py` + `seed/` output; `check` runs `gen --verify`.
  - Generators must not read the clock: `datetime.now`, `date.today`, `time.time` and Faker relative dates are linted out.
  - Use `Gen.rng_for(*key)` for per-entity randomness so adding rows doesn't reshuffle existing ones.
- **Master ids are shared.**
  - Sites, products, suppliers, carriers, POs and so on live in `systems/_master/`; systems reuse them, never invent their own.
  - Changing master data can shift stories in many systems: run the full `check` and fix every system it breaks.
- **One world.** Company facts, the calendar (FY starts 1 Feb) and DCs come from `world.yaml`. The world is re-anchored to the real date in whole weeks at load time (`spec.set_today`), so tools always speak relative to "today".
- **Writes are ephemeral.** Tool writes go to a per-process temp overlay (`MOCKMCP_STATE` persists it; `python -m mockmcp reset` clears it). Never commit `state/`.
- **Cross-system consistency.** The same fact (a supplier's spend, a shipment's ETA) must agree in every system that shows it. Known gaps are tracked in GitHub issue #3. When you fix a figure, search the other systems for it.

## Benchmark integrity

Treat these as hard rules; the benchmark's credibility depends on them.

- **Ground truth comes from tool output, never from memory.**
  - A case's facts in `bench/cases/<id>.yaml` must be produced by its reference calls (`bench/AUTHORING.md`).
  - If data changes, re-validate the cases that use it.
- **A trap must be fair.** The model only sees its loaded tools, so a trap can only demand what a careful model could see. Before adding or changing a trap:
  - The "missing" answer must not be reachable from any loaded system. For lookalikes, `validate` scans the data and `also_missing` keeps legitimate sources unloaded.
  - The loaded data must not contradict the expected answer.
  - Scripted follow-ups must say what they approve, since they can't react to the model.
  - `eval traps --check` must pass.
- **When every model fails a task the same way, suspect the benchmark first.** Read the trace before blaming the model. This repo has found flawed traps that way twice. Fix the bank, don't tune the judge to the model.
- **Nesting and determinism.**
  - Scale recipes (`bench/recipes/scale*.yaml`) share one seeded ladder. Never edit one scale-N file independently; change `scale.yaml`.
  - Sampling and distractor placement hash (seed, task id). Keep it that way so runs stay comparable when the bank grows.
- **Don't leak answers into prompts.** Task prompts, system prompts and tool descriptions must not hint at traps or grading.
- **`passed` is computed by the pipeline from the outcome, never trusted from the judge.** Judges return verdicts; `grade.finish` decides.

## Where things live

| Path | What | Change it by |
|---|---|---|
| `systems/<id>/` | one system | `docs/BUILDING_A_SYSTEM.md` (the full contract; `systems/yms/` is the reference) |
| `systems/_master/` | shared master data + its generator | edit `gen.py` / `seed/`, regenerate, full `check` |
| `catalog/` | tool catalogue from the persona docs | `python -m mockmcp catalog` |
| `bench/cases/` | ground truth per system | `bench/AUTHORING.md` |
| `bench/traps.yaml` | trap bank (generated + `authored: true` entries) | `mockmcp/eval/trap_seeds.py` / `traps.py`, then `eval traps` |
| `bench/recipes/` | benchmark recipes | copy `example.yaml`; check with `eval recipe --dry-run` |
| `mockmcp/eval/` | recipe → run → grade → report | `docs/BENCHMARKING.md` (§9 Extending) |
| `mockmcp/eval/harness/` | agent harnesses (claude-code) | subclass `Harness`, `@register` |
| `mockmcp/eval/judge/` | judges: claude-code + `prompt.md` (lean judge payload, the default: judge, don't diagnose) / `prompt-debug.md` (full payload, `--judge-debug`; keep the two in step); decision models over System One (`system_one.py` backends jev / jev-openrouter / jev-llmgateway / cygnet, `decompose.py` questions + combine); `cascade:<a>+<b>` | subclass `Judge`, `@register`; add a backend as a profile in `system_one.PROFILES`; check with `eval calibrate` |
| `runs/` | benchmark output | git-ignored; never commit |

## Running models costs money: ask first

`eval run`, `eval grade` (with a judge), `eval calibrate` and `mockmcp bench` call real models (decision-model judges call a paid API too, unless it is a local Cygnet). Typical costs:

| Run | Approximate cost |
|---|---|
| Haiku on 80 tasks at one budget | ~$3 |
| Sonnet judge for those 80 tasks | ~$10 |
| Opus on 30 hard traps | ~$70 |
| A full five-budget scale run | 5× those |

Don't start model runs beyond a single-task smoke check unless the person asked for them. Prefer `--dry-run`, `--only`, `--limit` and `grade --no-judge` while developing. Report cost alongside results.

## Conventions

- Python ≥ 3.11, standard library + the deps in `pyproject.toml`. No new dependencies without a reason.
- Match the surrounding code: dense, small functions, comments only where the *why* isn't obvious, docstrings on public functions.
- Plain JSON-able dicts across the eval pipeline (`mockmcp/eval/schema.py` is the contract). Add fields; don't rename them. Run folders must stay readable by other tools.
- Every random choice takes a seed. Every new eval option goes in `recipe.DEFAULTS`, `bench/recipes/example.yaml` and `docs/BENCHMARKING.md`.
- Tests cover behaviour that would silently skew results (nesting, determinism, trap fairness, grading rules), not just happy paths.
- Docs: UK English, plain words, numbers with units. Keep `README.md`, `docs/BENCHMARKING.md` and this file in step with the code you change.
- Don't put model identifiers in code comments, commit messages or docs except where a model is configuration (defaults, examples).

## Git

- Work on a branch; small commits with a body that says *why*.
- Never commit `runs/`, `state/`, `bench/results/*.jsonl` or credentials.
- Open follow-ups as GitHub issues rather than TODO files.
