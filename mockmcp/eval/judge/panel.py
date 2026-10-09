"""`panel`: two LLM judges in parallel, a third call only when they disagree.

The lead (default sonnet, the plain prompt) and the second judge (default haiku, the prompt plus the step-by-step
appendix, prompt-detail.md) grade the same payload at once. When they agree on the outcome and on trap_handled, the lead's
verdict stands. When they differ, an adjudicator (default sonnet) gets the rules, the payload and both verdicts
(prompt-adjudicate.md) and decides each point from the evidence. Why: a review of disagreements between judges found the
answer is usually settled by checking the evidence point by point, which a single judge does not do for its own
blind spots; the cheap second judge mostly costs time, and the adjudicator runs only on the disagreements."""
import json
from concurrent.futures import ThreadPoolExecutor

from ..schema import modern
from .base import Judge, register
from .claude_code import ADJUDICATE, ClaudeCodeJudge, payload_block, prompt_for

SUMMARY_KEYS = ("outcome", "categories", "severity", "unsupported_claims", "actions", "trap_handled", "trap_notes",
                "rationale", "confidence")


def key(v: dict) -> tuple:
    """What the two judges must agree on: the outcome and, for traps, whether the trap was handled."""
    return modern(v.get("outcome") or ""), v.get("trap_handled")


@register
class PanelJudge(Judge):
    name = "panel"

    def __init__(self, model: str = "sonnet", second: str = "haiku", adjudicator: str | None = None, timeout: int = 900, **_):
        if "+" in (model or ""):   # --judge-model lead+second, e.g. sonnet+haiku
            model, second = model.split("+", 1)
        self.lead = ClaudeCodeJudge(model=model, timeout=timeout)
        self.second = ClaudeCodeJudge(model=second, timeout=timeout, detail=True)
        self.adj = ClaudeCodeJudge(model=adjudicator or model, timeout=timeout)
        self.model = f"{model}+{second}"

    def judge(self, payload: dict) -> dict:
        with ThreadPoolExecutor(2) as ex:
            a, b = ex.map(lambda j: j.judge(payload), (self.lead, self.second))
        cost = (a.get("judge") or {}).get("cost_usd", 0) + (b.get("judge") or {}).get("cost_usd", 0)
        summ = lambda v: {k: v.get(k) for k in SUMMARY_KEYS}
        meta = {"backend": self.name, "model": self.model, "lead": a.get("judge"), "second": b.get("judge"),
                "second_verdict": summ(b)}
        failed = [n for n, v in (("lead", a), ("second", b)) if v.get("outcome") == "judge_failed"]
        if failed or key(a) == key(b):
            final = b if failed == ["lead"] else a
            meta.update(agreed=not failed, adjudicated=False, failed=failed)
            return {**final, "judge": {**meta, "cost_usd": cost}}
        prompt = (prompt_for(payload.get("mode")) + "\n\n" + ADJUDICATE.read_text() + payload_block(payload)
                  + "\n# VERDICTS\n\n```json\n" + json.dumps({"judge_a": summ(a), "judge_b": summ(b)}, indent=1, default=str)
                  + "\n```\n\nReturn ONLY the final Verdict JSON object.\n")
        v, c, ms, m = self.adj.ask(prompt)
        if v.get("outcome") == "judge_failed":
            v = a   # the lead stands when the adjudicator fails
        sided = "A" if key(v) == key(a) else "B" if key(v) == key(b) else "neither"
        meta.update(agreed=False, adjudicated=True, sided_with=sided, lead_verdict=summ(a),
                    adjudicator={"model": self.adj.model, "cost_usd": c, "duration_ms": ms, "models_used": m.get("models") or []})
        return {**v, "judge": {**meta, "cost_usd": cost + c}}
