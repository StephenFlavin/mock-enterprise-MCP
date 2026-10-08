"""What the eval runner needs from a harness (an agent loop that talks to MCP servers). Nothing harness-specific here."""
from datetime import date
from pathlib import Path

from ...spec import WORLD

# The whole system prompt the model under test sees. Deliberately no hints: nothing about tools, honesty or what to do when
# the tools can't answer; the model must decide for itself that it needs the tools. The persona line only says who the
# assistant is talking to (role and department from the persona docs, never their focus or questions).
SYSTEM_PROMPT = "You are an assistant at {company}. Today is {today}. {persona}"


def persona_line(task: dict) -> str:
    role = ((task.get("persona") or {}).get("role") or "").strip()
    if not role:
        return ""
    if len(role) > 1 and role[1].islower():  # "Warehouse manager" -> "warehouse manager"; keep "HR ...", "CFO"
        role = role[0].lower() + role[1:]
    dept = (task.get("domain") or "").strip()
    return f"You are talking to the {role}" + (f" in {dept}." if dept else ".")


def system_prompt(task: dict, today: date | None = None) -> str:
    return SYSTEM_PROMPT.format(company=WORLD["company"], today=(today or date.today()).isoformat(),
                                persona=persona_line(task)).strip()


_REGISTRY: dict[str, type] = {}


def register(cls):
    """Class decorator: make a Harness subclass selectable by its `name` (recipe `harness:` / `eval recipe --harness`)."""
    _REGISTRY[cls.name] = cls
    return cls


def available() -> list[str]:
    return sorted(_REGISTRY)


def get(name: str) -> "Harness":
    if name not in _REGISTRY:
        raise KeyError(f"unknown harness {name!r}; available: {', '.join(available())}")
    return _REGISTRY[name]()


class Harness:
    """One agent loop under test. The run folder is written for ONE harness (`write_task` at recipe time), and
    `eval run` always runs it with that harness."""
    name: str

    def write_task(self, task_dir: Path, task: dict, recipe: dict) -> None:
        """Write what the model sees and how to run it: prompt.json, mcp.json (URLs use the placeholder {PORT}), run.sh."""
        raise NotImplementedError

    def run_task(self, task_dir: Path, task: dict, port: int, model: str, opts: dict) -> dict:
        """Run every turn against the hub on `port`. Writes transcript.jsonl and answers.json in task_dir and returns the
        answers dict: {"turns": [{"text","usage","cost_usd","duration_ms","num_turns","error","started_at","finished_at"}],
        "error": str | None}. Must not raise for model/harness failures; record them under "error"."""
        raise NotImplementedError
