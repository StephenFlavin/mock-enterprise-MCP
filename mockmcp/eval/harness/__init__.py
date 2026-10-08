"""Harness registry. A harness is the agent loop under test (today: headless Claude Code). `get(name)` -> Harness instance,
`available()` -> registered names. Add one by subclassing `Harness` in a new module, decorating it with `@register` and
importing the module below; see docs/BENCHMARKING.md, "Extending"."""
from .base import Harness, available, get, register  # noqa: F401
from . import claude_code  # noqa: F401  (registers "claude-code")
