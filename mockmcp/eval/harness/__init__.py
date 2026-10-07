"""Harness registry: `get("claude-code")` -> Harness instance."""
from .base import Harness


def get(name: str) -> Harness:
    if name == "claude-code":
        from .claude_code import ClaudeCode
        return ClaudeCode()
    raise KeyError(f"unknown harness {name!r}; available: claude-code")
