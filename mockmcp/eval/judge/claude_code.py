"""Default judge: headless Claude Code with no tools, instructions from prompt.md, payload on stdin, Verdict via --json-schema."""
import json
import re
import subprocess
import tempfile
from pathlib import Path

from .base import VERDICT_SCHEMA, Judge, register

PROMPT = Path(__file__).with_name("prompt.md")


def parse_json(text: str) -> dict | None:
    """A single JSON object from model text: bare, fenced, or embedded in prose."""
    text = (text or "").strip()
    for cand in (text, re.sub(r"^```(?:json)?\s*|\s*```$", "", text)):
        try:
            v = json.loads(cand)
            if isinstance(v, dict):
                return v
        except ValueError:
            pass
    a, b = text.find("{"), text.rfind("}")
    if 0 <= a < b:
        try:
            v = json.loads(text[a:b + 1])
            return v if isinstance(v, dict) else None
        except ValueError:
            pass
    return None


@register
class ClaudeCodeJudge(Judge):
    name = "claude-code"

    def __init__(self, model: str = "opus", timeout: int = 900, **_):
        self.model, self.timeout = model, timeout

    def _run(self, prompt: str, schema: bool) -> tuple[dict | None, dict]:
        cmd = ["claude", "-p", "--model", self.model, "--tools", "", "--strict-mcp-config", "--setting-sources", "",
               "--output-format", "json", "--no-session-persistence"]
        if schema:
            cmd += ["--json-schema", json.dumps(VERDICT_SCHEMA)]
        with tempfile.TemporaryDirectory(prefix="judge-") as cwd:
            try:
                p = subprocess.run(cmd, input=prompt, cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
            except subprocess.TimeoutExpired:
                return None, {"error": "judge timeout"}
        try:
            env = json.loads(p.stdout)
        except ValueError:
            return None, {"error": f"judge output not JSON: {(p.stdout or p.stderr)[:300]}"}
        meta = {"cost_usd": env.get("total_cost_usd") or 0.0, "duration_ms": env.get("duration_ms") or 0,
                "models": list((env.get("modelUsage") or {}).keys())}
        v = env.get("structured_output")
        return (v if isinstance(v, dict) else parse_json(env.get("result") or "")), meta

    def judge(self, payload: dict) -> dict:
        prompt = (PROMPT.read_text() + "\n\n# PAYLOAD\n\n```json\n" + json.dumps(payload, indent=1, default=str) + "\n```\n"
                  "\nReturn ONLY the Verdict JSON object.\n")
        verdict, meta, cost, ms = None, {}, 0.0, 0
        for attempt in range(2):  # one retry on invalid / missing JSON
            verdict, meta = self._run(prompt, schema=attempt == 0)
            cost, ms = cost + meta.get("cost_usd", 0), ms + meta.get("duration_ms", 0)
            if verdict and verdict.get("outcome"):
                break
        verdict = verdict or {"outcome": "judge_failed", "categories": [], "severity": "none", "per_turn": [],
                              "unsupported_claims": [], "actions": [], "confidence": 0.0,
                              "rationale": f"judge failed: {meta.get('error', 'no valid verdict')}"}
        verdict["judge"] = {"backend": self.name, "model": self.model, "models_used": meta.get("models") or [],
                            "cost_usd": cost, "duration_ms": ms}
        return verdict
