# mock-enterprise-MCP
An set of servers which mock enterprise scale tooling

## Benchmarking LLMs

`python -m mockmcp eval` measures how well a model navigates these tools as more and more of them fill its context: it builds tasks from the persona questions, runs them against recording copies of the servers (headless Claude Code today), and grades them with deterministic checks plus an LLM judge. Reports lead with failure categories: wrong server, hallucination, unsafe writes, honest failure and more.

```
python -m mockmcp eval recipe bench/recipes/smoke.yaml --out runs/smoke
python -m mockmcp eval run    runs/smoke --model haiku --workers 4
python -m mockmcp eval grade  runs/smoke --judge claude-code --judge-model sonnet
python -m mockmcp eval report runs/smoke
```

Full guide: [docs/BENCHMARKING.md](docs/BENCHMARKING.md).
