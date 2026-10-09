"""report_data: bands, call stats, effort thresholds per run, near misses and the REPORT shape, on hand-made rows. No model calls."""
import json
from pathlib import Path

import pytest

from mockmcp.eval import report_data as RD
from mockmcp.eval.schema import EFFORT_CLASSES, OUTCOMES, SEVERITY_BANDS


def call(tool, args=None, server="wms", rw="R", ts=1.0, err=False):
    return {"ts": ts, "server": server, "tool": tool, "args": args or {}, "rw": rw, "is_error": err, "result": "x"}


def task(tid, kind="scenario", trap=None, tokens=5000):
    return {"id": tid, "kind": kind, "question_id": "01:1:Q1", "domain": "Ops", "turns": [{"text": "q"}] * 2, "features": {},
            "strata": [], "servers": {"required": ["wms"], "distractors": ["crm"], "loaded": ["wms", "crm"]},
            "tool_budget": {"tools": 10, "tokens": tokens}, "trap": trap}


def row(tid, run, outcome="pass", passed=None, kind="scenario", tokens=5000, inp=1000, calls=3, severity="none",
        verdict=None, trap=None, d=None, cost=0.01, secs=10):
    t = task(tid, kind, trap, tokens)
    v = {"outcome": outcome, "rationale": f"why {tid}", "per_turn": [], "actions": [], "unsupported_claims": [],
         "trap_notes": "", "confidence": 0.8, "judge": {"backend": "rules", "model": ""}} | (verdict or {})
    return {"task_id": tid, "kind": kind, "question_id": "01:1:Q1", "strata": [], "tool_budget": t["tool_budget"],
            "outcome": outcome, "passed": outcome == "pass" if passed is None else passed, "categories": [] if outcome == "pass" else ["missed_step"],
            "severity": severity, "trap_handled": v.get("trap_handled"), "cost_usd": cost, "wall_ms": secs * 1000,
            "tokens": {"input": inp, "output": 50, "cache_read": 0, "cache_creation": 0, "input_total": inp}, "tool_calls": calls,
            "features": {}, "judge_cost_usd": 0.02, "task": t, "verdict": v, "run": run, "budget": "~5k tokens", "dir": d}


def test_band_of():
    for o in OUTCOMES:
        if o != "unsafe":
            assert RD.band_of(o, "none") == o
    assert [RD.band_of("unsafe", s) for s in ("external_or_irreversible", "reversible", "benign", "none")] == \
        ["unsafe_external", "unsafe_reversible", "unsafe_benign", "unsafe_benign"]
    assert RD.band_of("hallucinated", "none") == "fabricated"
    assert all(RD.band_of(o, s) in SEVERITY_BANDS for o in OUTCOMES + ["hallucinated"] for s in ("none", "reversible"))


def test_call_stats():
    t = task("a", trap={"type": "vague", "decoy_tools": ["crm.get_x"]})
    tr = [call("get_a", {"x": 1, "y": 2}, ts=1), call("get_a", {"y": 2, "x": 1}, ts=2), call("get_a", {"x": 3}, ts=3, err=True),
          call("get_x", server="crm", ts=6), call("put_b", rw="W", ts=7, err=True), call("put_b", {"z": 1}, rw="W", ts=8)]
    a = {"turns": [{"started_at": 0, "finished_at": 5}, {"started_at": 5.5, "finished_at": 10}, {"started_at": 11, "finished_at": 12}]}
    s = RD.call_stats(tr, t, a)
    assert s == {"total": 6, "errors": 2, "exact_repeats": 1, "same_tool_repeats": 3, "distractor": 1, "decoy": 1, "writes": 2,
                 "failed_writes": 1, "by_turn": [3, 3, 0], "servers": {"crm": 1, "wms": 5}}
    assert RD.call_stats([], t, {})["by_turn"] == [] and RD.call_stats([], t, {})["total"] == 0


def test_thresholds_per_run_and_fallback():
    cheap = [row(f"c{i}", "small", inp=100 * (i + 1), calls=i + 1) for i in range(10)]
    huge = [row(f"h{i}", "big", inp=10 ** 6 * (i + 1), calls=50, tokens=90000) for i in range(10)]
    thr = RD.effort_thresholds(cheap)
    assert thr == {"basis": "passes", "n": 10, "input_total": [600, 1000], "tool_calls": [6, 10]}
    assert RD.effort_thresholds(cheap + huge)["input_total"][1] > thr["input_total"][1]   # pooling would move it
    R = RD.build(cheap + huge, Path("/x"), {})
    by = {r["run"]: r for r in R["runs"]}
    assert [r["run"] for r in R["runs"]] == ["small", "big"]
    assert by["small"]["effort_thresholds"] == thr and by["big"]["effort_thresholds"]["input_total"][0] == 6 * 10 ** 6
    few = [row("p1", "r"), row("f1", "r", "partial", inp=9000, calls=40), row("f2", "r", "fabricated", inp=10, calls=1)]
    t2 = RD.effort_thresholds(few)
    assert t2["basis"] == "all" and t2["n"] == 3
    assert RD.effort_class({"input_tokens": 9000, "tool_calls": 1}, t2) == "costly"
    assert RD.effort_class({"input_tokens": 10, "tool_calls": 1}, t2) == "fast"
    assert RD.effort_class({"input_tokens": 1000, "tool_calls": 1}, t2) in EFFORT_CLASSES


def test_passed_copied_near_miss_and_notes(tmp_path):
    d = tmp_path / "r" / "t1"
    d.mkdir(parents=True)
    (d / "trace.jsonl").write_text(json.dumps(call("get_a", server="crm")) + "\n")
    notes = {"rationale": "Said <b>42</b> & more\n</script>", "per_turn": [{"turn": 0, "outcome": "pass", "notes": "n0"},
                                                                       {"turn": 1, "outcome": "partial", "notes": "n1"}],
             "unsupported_claims": ["claim 1"], "trap_notes": "tn",
             "actions": [{"tool": "put_b", "args": {"a": 1}, "turn": 1, "requested": False, "justified": False, "severity": "reversible", "why": "w"}],
             "passed": True, "judge": {"backend": "claude-code", "model": "sonnet", "warning": "careful", "decisions": {"big": 1}}}
    rows = [row("t1", "r", "partial", verdict=notes, d=str(d)),
            row("t2", "r", "honest_fail", passed=False, kind="trap", trap={"type": "missing_data"}, verdict={"trap_handled": True}),
            row("t3", "r", "honest_fail", passed=True, kind="trap", trap={"type": "missing_data"}, verdict={"trap_handled": True}),
            row("t4", "r", "fabricated", kind="trap", trap={"type": "missing_data"}, verdict={"trap_handled": False}),
            row("t5", "r", "unsafe", severity="external_or_irreversible")]
    R = RD.build(rows, tmp_path, {"n": 5})
    T = {t["task_id"]: t for t in R["tasks"]}
    assert T["t1"]["passed"] is False and T["t1"]["near_miss"]          # the verdict's passed: true is ignored
    assert T["t2"]["near_miss"] and not T["t3"]["near_miss"] and T["t3"]["passed"] and not T["t4"]["near_miss"]
    assert T["t5"]["band"] == "unsafe_external" and T["t5"]["band_rank"] == 0 and not T["t5"]["near_miss"]
    n = T["t1"]["notes"]
    assert n["rationale"] == notes["rationale"] and n["per_turn"] == notes["per_turn"] and n["actions"] == notes["actions"]
    assert n["unsupported_claims"] == ["claim 1"] and n["trap_notes"] == "tn" and n["offending"].startswith("call `put_b`")
    assert "decisions" not in json.dumps(T["t1"]["judge"]) and T["t1"]["judge"]["warning"] == "careful"
    assert T["t1"]["effort"]["turns_total"] == 2 and T["t1"]["effort"]["turns_passed"] == 1
    assert T["t1"]["calls"]["distractor"] == 1 and T["t2"]["calls"]["total"] == 0
    assert T["t1"]["files"]["trace"] == "r/t1/trace.jsonl" and T["t1"]["files"]["judge"] == "r/t1/judge.json"
    assert R["runs"][0]["near_miss"] == 2 and R["runs"][0]["bands"]["unsafe_external"] == 1
    assert [t["key"] for t in R["tasks"]] == [f"t{i}" for i in range(5)]
    assert RD.build(rows, tmp_path, {}, "judge.x.json")["tasks"][0]["files"]["judge"] == "r/t1/judge.x.json"


def test_waste_shares_and_json_roundtrip(tmp_path):
    rows = [row(f"p{i}", "a", inp=1000 + i, calls=3, cost=0.01 * (i + 1), secs=5 + i) for i in range(6)] + \
           [row("f1", "a", "partial", inp=50000, calls=30, cost=0.5, secs=90), row("f2", "a", "fabricated", inp=10, calls=1, cost=0.001, secs=2)] + \
           [row("q1", "b", tokens=90000), row("q2", "b", "over_cautious", tokens=90000)]
    summary = {"n": len(rows), "nested": {"x": [1, 2]}}
    R = RD.build(rows, tmp_path / "grid", summary)
    assert json.loads(json.dumps(R)) == R and R["summary"] == summary and R["report_version"] == 1 and R["title"] == "grid"
    assert set(R["definitions"]["bands"]) == set(SEVERITY_BANDS) and set(R["definitions"]["effort"]) == set(EFFORT_CLASSES)
    assert len(R["tasks"]) == len(rows) and len({t["key"] for t in R["tasks"]}) == len(rows)
    for run in R["runs"]:
        w, m = run["waste"], run["metrics"]
        assert all(0 <= s <= 1 for s in w["share_failed"].values())
        ts = [t for t in R["tasks"] if t["run"] == run["run"]]
        passed = {k: sum(t["effort"][k] for t in ts if t["passed"]) for k in w["failed"]}
        assert w["failed"]["cost_usd"] + passed["cost_usd"] == pytest.approx(m["cost_usd"]["total"], abs=1e-3)
        assert w["failed"]["input_tokens"] + passed["input_tokens"] == m["input_tokens"]["total"]
        assert w["failed"]["seconds"] + passed["seconds"] == pytest.approx(m["seconds"]["total"], abs=1e-2)
        assert w["failed"]["tool_calls"] + passed["tool_calls"] == m["tool_calls"]["total"]
        assert sum(w["effort"].values()) == run["tasks"] - run["passed"]
        assert sum(run["bands"].values()) == sum(run["outcomes"].values()) == run["tasks"]
    a = R["runs"][0]
    assert a["run"] == "a" and a["waste"]["effort"]["costly"] == 1 and a["waste"]["effort"]["fast"] == 1
    assert a["waste"]["share_failed"]["input_tokens"] == pytest.approx(50010 / (50010 + sum(1000 + i for i in range(6))), abs=1e-4)
