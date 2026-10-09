"""The panel judge: two LLM judges in parallel, an adjudicator only when they disagree (model calls stubbed)."""
import json

import pytest

from mockmcp.eval import judge as J
from mockmcp.eval.judge import claude_code as CC
from mockmcp.eval.judge.panel import PanelJudge

P = {"mode": "judge", "conversation": [{"turn": 0, "user": "What stopped line 3?", "assistant": "Bearing failure."}]}


def verdict(outcome, trap=None, why="x"):
    return {"outcome": outcome, "categories": [] if outcome == "pass" else ["incomplete"], "severity": "none",
            "per_turn": [], "unsupported_claims": [], "actions": [], "trap_handled": trap, "trap_notes": "",
            "rationale": why, "confidence": 0.8}


@pytest.fixture
def calls(monkeypatch):
    """Stub the claude subprocess: answers by model, records every prompt."""
    seen, answers = [], {}

    def run(self, prompt, schema):
        seen.append((self.model, prompt))
        v = answers[self.model] if not answers.get("adjudicating") or "# VERDICTS" not in prompt else answers["adjudicator"]
        return dict(v), {"cost_usd": {"sonnet": 0.07, "haiku": 0.004}[self.model], "duration_ms": 10, "models": [self.model]}
    monkeypatch.setattr(CC.ClaudeCodeJudge, "_run", run)
    return seen, answers


def test_panel_is_registered_and_takes_lead_plus_second():
    j = J.get("panel", model="sonnet+haiku")
    assert isinstance(j, PanelJudge) and j.lead.model == "sonnet" and j.second.model == "haiku" and j.second.detail


def test_agreement_keeps_the_lead_verdict_and_skips_the_adjudicator(calls):
    seen, answers = calls
    answers.update(sonnet=verdict("pass", why="lead"), haiku=verdict("pass", why="second"))
    v = PanelJudge().judge(P)
    assert v["rationale"] == "lead" and v["judge"]["agreed"] and not v["judge"]["adjudicated"]
    assert len(seen) == 2 and round(v["judge"]["cost_usd"], 3) == 0.074
    haiku_prompt = next(p for m, p in seen if m == "haiku")
    sonnet_prompt = next(p for m, p in seen if m == "sonnet")
    assert CC.DETAIL.read_text()[:40] in haiku_prompt and CC.DETAIL.read_text()[:40] not in sonnet_prompt


def test_disagreement_goes_to_the_adjudicator_with_both_verdicts(calls):
    seen, answers = calls
    answers.update(sonnet=verdict("pass", why="lead says pass"), haiku=verdict("partial", why="second says partial"),
                   adjudicating=True, adjudicator=verdict("partial", why="B right: the third factory is missing"))
    v = PanelJudge().judge(P)
    assert v["outcome"] == "partial" and v["judge"]["adjudicated"] and v["judge"]["sided_with"] == "B"
    adj = seen[-1][1]
    assert "# Adjudication" in adj and "lead says pass" in adj and "second says partial" in adj and "# PAYLOAD" in adj
    assert v["judge"]["lead_verdict"]["outcome"] == "pass" and round(v["judge"]["cost_usd"], 3) == 0.144


def test_a_trap_verdict_difference_alone_is_a_disagreement(calls):
    _, answers = calls
    answers.update(sonnet=verdict("pass", trap=True), haiku=verdict("pass", trap=False), adjudicating=True,
                   adjudicator=verdict("pass", trap=True))
    v = PanelJudge().judge(P)
    assert v["judge"]["adjudicated"] and v["judge"]["sided_with"] == "A"


def test_a_failed_judge_leaves_the_other_one_standing(calls):
    _, answers = calls
    answers.update(sonnet={"outcome": ""}, haiku=verdict("partial"))
    v = PanelJudge().judge(P)
    assert v["outcome"] == "partial" and v["judge"]["failed"] == ["lead"] and not v["judge"]["adjudicated"]
