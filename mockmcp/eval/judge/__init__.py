"""Judges turn a payload (everything about one task run) into a schema.Verdict. `judge.get(name, **opts)` picks one."""
from .base import Judge, RUBRIC, VERDICT_SCHEMA, get, register  # noqa: F401
from . import claude_code  # noqa: F401  (registers "claude-code")
