"""`cascade:<decision>+<llm>`: a decision-model judge decides what it can; the LLM judge takes the rest.

Escalates when the decision verdict is undecided (an uncertain or unanswered question would change the outcome or
trap_handled), when a question did not fit the backend's window, or when the backend failed after retries. The escalated
verdict is the LLM judge's, with the decision model's probabilities kept in `judge.decision` for calibration."""
from .base import Judge, _REGISTRY


class CascadeJudge(Judge):
    accepts_ctx = True

    def __init__(self, name: str, model: str | None = None, decision_model: str | None = None, base_url: str | None = None, **opts):
        spec = name.split(":", 1)[1]
        if "+" not in spec:
            raise KeyError(f"cascade judge needs 'cascade:<decision>+<llm>', got {name!r}")
        dname, lname = spec.split("+", 1)
        for n in (dname, lname):
            if n not in _REGISTRY:
                raise KeyError(f"unknown judge {n!r} in {name!r}; available: {sorted(_REGISTRY)}")
        self.name = name
        self.decision = _REGISTRY[dname](model=decision_model, base_url=base_url, **opts)
        self.llm = _REGISTRY[lname](**({"model": model} if model else {}), **opts)
        self.model = getattr(self.llm, "model", "")
        self.max_workers = getattr(self.decision, "max_workers", None)

    def _call(self, j, payload, ctx):
        return j.judge(payload, **ctx) if getattr(j, "accepts_ctx", False) else j.judge(payload)

    def judge(self, payload: dict, **ctx) -> dict:
        v = self._call(self.decision, payload, ctx)
        dj = v.get("judge") or {}
        if v.get("outcome") == "judge_failed":
            reason = "backend failed: " + str((dj.get("error") or {}).get("message") or v.get("rationale", ""))
        elif dj.get("unfittable"):
            reason = "unfittable: " + ", ".join(dj["unfittable"])
        elif dj.get("undecided"):
            reason = dj.get("undecided_reason") or "uncertain"
        else:
            v["judge"] = {**dj, "cascade": self.name, "escalated": None}
            return v
        lv = self._call(self.llm, payload, ctx)
        lj = lv.get("judge") or {}
        lv["judge"] = {**lj, "cascade": self.name, "escalated": reason, **({"warning": dj["warning"]} if dj.get("warning") else {}),
                       "cost_usd": round((lj.get("cost_usd") or 0) + (dj.get("cost_usd") or 0), 6),
                       "decision": {k: dj.get(k) for k in ("backend", "model", "model_reported", "precision", "cost_usd", "latency_ms",
                                                           "n_questions", "n_calls", "decisions", "uncertain", "unfittable", "error")}
                       | {"outcome": v.get("outcome"), "trap_handled": v.get("trap_handled")}}
        return lv
