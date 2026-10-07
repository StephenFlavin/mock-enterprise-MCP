"""What the eval runner needs from a harness (an agent loop that talks to MCP servers). Nothing harness-specific here."""
from pathlib import Path


class Harness:
    name: str

    def write_task(self, task_dir: Path, task: dict, recipe: dict) -> None:
        """Write what the model sees and how to run it: prompt.json, mcp.json (URLs use the placeholder {PORT}), run.sh."""
        raise NotImplementedError

    def run_task(self, task_dir: Path, task: dict, port: int, model: str, opts: dict) -> dict:
        """Run every turn against the hub on `port`. Writes transcript.jsonl and answers.json in task_dir and returns the
        answers dict: {"turns": [{"text","usage","cost_usd","duration_ms","num_turns","error","started_at","finished_at"}],
        "error": str | None}. Must not raise for model/harness failures; record them under "error"."""
        raise NotImplementedError
