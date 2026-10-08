# mock-enterprise-MCP
An set of servers which mock enterprise scale tooling

## Benchmarking LLMs

`python -m mockmcp eval` measures how well a model navigates these tools as more and more of them fill its context: it builds tasks from the persona questions, runs them against recording copies of the servers (headless Claude Code today), and grades them with deterministic checks plus an LLM judge. Reports lead with failure categories: wrong server, hallucination, unsafe writes, honest failure and more.

```
python -m mockmcp eval recipe bench/recipes/scale-80.yaml --out runs/scale-80   # 80 questions x 4 tool budgets
python -m mockmcp eval run    runs/scale-80 --model haiku --workers 6
python -m mockmcp eval grade  runs/scale-80 --judge claude-code --judge-model sonnet
python -m mockmcp eval report runs/scale-80
```

Scale recipes nest: `scale-80` ⊂ `scale-160` ⊂ `scale-320` ⊂ `scale-all` (same seed, same mix), so a model's results on more questions or more tools can be compared question by question. `bench/recipes/smoke.yaml` is a 6-task end-to-end check.

Full guide: [docs/BENCHMARKING.md](docs/BENCHMARKING.md).
