# Example outputs

Real output of `eval report` and `eval compare` on the scale-160 recipe: 160 tasks at five tool budgets (~14k, ~31k, ~56k, ~105k and ~203k tokens of tool definitions), 800 tasks per run, graded by the claude-code judge (Sonnet).

| Folder | What | Made by |
|---|---|---|
| `haiku/` | Haiku, tool search off | `eval report runs/ts-off --html` |
| `haiku-toolsearch/` | Haiku, tool search on | `eval report runs/ts-on --html` |
| `sonnet/` | Sonnet, tool search off | `eval report runs/s160-sonnet --html` |
| `haiku-vs-haiku-toolsearch/` | tool search off vs on | `eval compare runs/ts-off runs/ts-on --html` |
| `haiku-vs-sonnet/` | Haiku vs Sonnet | `eval compare runs/ts-off runs/s160-sonnet --html` |

Each folder holds:

- `report.html` / `compare.html`: the interactive page. Download it and open it in a browser; it works offline and carries every task's answer, highlights and verdict for the task drawer. GitHub shows it as source.
- `report.md` / `compare.md`: the same results as Markdown.
- `charts/` (and `charts-a/`, `charts-b/` for comparisons): the SVG charts, usable on their own.
- `report.json.gz` / `compare.json.gz`: the machine-readable report (`gunzip` it).
- `answers.tar.gz` (single runs): every task's `answers.json` and `trace.jsonl` (the tool calls). Extract it in the run's folder (`tar xzf answers.tar.gz`) and the per-task links in the page open the raw files; comparison pages link into the two run folders next to them.

The pages link to `checks.json` and `judge.json` too; those stay in the git-ignored `runs/` folders, and their content is already in `report.json`.

Costs and findings are in the pull request that added these files (#7).
