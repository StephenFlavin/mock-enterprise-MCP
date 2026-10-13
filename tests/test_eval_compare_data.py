"""compare_data: run pairing, McNemar, head-to-head, transitions, shift and the COMPARE shape, on hand-made rows. No model calls."""
import json
import os
from pathlib import Path

import pytest

from mockmcp.eval import compare_data as C
from mockmcp.eval import report_data as RD
from mockmcp.eval.schema import OUTCOMES, SEVERITY_BANDS


def row(tid, run, outcome="pass", passed=None, kind="scenario", tokens=5000, inp=1000, calls=3, severity="none", cost=0.01,
        secs=10, d=None):
    t = {"id": tid, "kind": kind, "question_id": "01:1:Q1", "domain": "Ops", "turns": [{"text": "q"}], "features": {},
         "strata": [], "servers": {"required": ["wms"], "distractors": [], "loaded": ["wms"]},
         "tool_budget": {"tools": 10, "tokens": tokens}, "trap": {"type": "vague"} if kind == "trap" else None}
    v = {"outcome": outcome, "rationale": f"why {tid}", "per_turn": [], "actions": [], "unsupported_claims": [],
         "trap_notes": "", "confidence": 0.8, "judge": {"backend": "rules", "model": ""}}
    return {"task_id": tid, "kind": kind, "question_id": "01:1:Q1", "strata": [], "tool_budget": t["tool_budget"],
            "outcome": outcome, "passed": outcome == "pass" if passed is None else passed, "categories": [],
            "severity": severity, "trap_handled": None, "cost_usd": cost, "wall_ms": secs * 1000,
            "tokens": {"input": inp, "output": 50, "cache_read": 0, "cache_creation": 0, "input_total": inp},
            "tool_calls": calls, "features": {}, "judge_cost_usd": 0.0, "task": t, "verdict": v, "run": run,
            "budget": "~5k tokens", "dir": d}


def rep(rows, root="/r/x", vs="judge.json"):
    return RD.build(rows, Path(root), {}, vs)


def cmp_of(a_rows, b_rows, **kw):
    return C.build(rep(a_rows), rep(b_rows), ["A", "B"], **kw)


def test_mcnemar_known_values():
    assert C.mcnemar(0, 0) == 1.0
    assert C.mcnemar(0, 10) == pytest.approx(2 / 1024) and C.mcnemar(10, 0) == C.mcnemar(0, 10)
    assert C.mcnemar(5, 5) == 1.0
    assert C.mcnemar(1, 0) == 1.0
    assert C.mcnemar(2, 8) == pytest.approx(2 * (1 + 10 + 45) / 1024)


def test_pair_runs_single_different_names():
    a, b = [row("t1", "haiku-v3")], [row("t1", "sonnet-v3")]
    pairs, un = C.pair_runs(a, b)
    assert [(n, len(x), len(y)) for n, x, y in pairs] == [("run", 1, 1)] and un == {"only_a_runs": [], "only_b_runs": []}
    assert pairs[0][1][0]["run"] == "haiku-v3"   # rows untouched
    assert C.pair_runs([row("t1", "same")], [row("t1", "same")])[0][0][0] == "same"


def test_pair_runs_grid_and_unpaired():
    a = [row("t1", "tokens-0"), row("t1", "tokens-25000"), row("t2", "tokens-25000"), row("t1", "tokens-50000")]
    b = [row("t1", "tokens-0"), row("t1", "tokens-25000"), row("t1", "tokens-100000")]
    pairs, un = C.pair_runs(a, b)
    assert [(n, len(x), len(y)) for n, x, y in pairs] == [("tokens-0", 1, 1), ("tokens-25000", 2, 1)]
    assert un == {"only_a_runs": ["tokens-50000"], "only_b_runs": ["tokens-100000"]}
    # single vs grid: nothing pairs by name (the CLI rejects this case before)
    assert C.pair_runs([row("t1", "solo")], b)[0] == []


def test_build_pairs_single_runs_and_grid_like_pair_runs():
    c = cmp_of([row("t1", "x")], [row("t1", "y")])
    assert [r["run"] for r in c["runs"]] == ["run"] and c["tasks"][0]["run"] == "run"
    a = [row("t1", "tokens-0", tokens=1000), row("t1", "tokens-9", tokens=9000), row("t1", "only-a", tokens=4000)]
    b = [row("t1", "tokens-9", tokens=9000), row("t1", "tokens-0", tokens=1000)]
    c = cmp_of(a, b)
    assert [r["run"] for r in c["runs"]] == ["tokens-0", "tokens-9"]   # A's REPORT order (median tokens)
    assert c["unpaired"] == {"only_a_runs": ["only-a"], "only_b_runs": []}
    assert all(t["run"] != "only-a" for t in c["tasks"])


def test_only_a_only_b_counted_not_mixed():
    a = [row("t1", "r"), row("t2", "r", "partial"), row("a3", "r", cost=99)]
    b = [row("t1", "r", "partial"), row("t2", "r"), row("b3", "r"), row("b4", "r")]
    c = cmp_of(a, b)
    r = c["runs"][0]
    assert (r["common"], r["only_a"], r["only_b"]) == (2, 1, 2)
    assert r["a"]["tasks"] == r["b"]["tasks"] == 2 and r["a"]["cost_usd"] == pytest.approx(0.02)
    assert {t["task_id"] for t in c["tasks"]} == {"t1", "t2"}
    assert c["all"]["only_a"] == 1 and c["all"]["only_b"] == 2


def outcomes_mix():
    ao = ["pass", "pass", "pass", "partial", "unsafe", "fabricated", "honest_fail", "pass", "partial"]
    bo = ["pass", "partial", "pass", "pass", "pass", "unsafe", "honest_fail", "fabricated", "partial"]
    a = [row(f"t{i}", "r", o, severity="reversible") for i, o in enumerate(ao)]
    b = [row(f"t{i}", "r", o, severity="external_or_irreversible", cost=0.03, inp=3000) for i, o in enumerate(bo)]
    return a, b


def test_head_to_head_and_transitions_sum_to_common():
    c = cmp_of(*outcomes_mix())
    r = c["runs"][0]
    h = r["head_to_head"]
    assert sum(h.values()) == r["common"] == 9
    assert h == {"both_pass": 2, "a_only": 2, "b_only": 2, "both_fail": 3}
    assert r["mcnemar_p"] == C.mcnemar(2, 2)
    assert sum(t["n"] for t in r["transitions"]) == 9 and sum(t["n"] for t in r["band_transitions"]) == 9
    assert all(t["n"] > 0 for t in r["transitions"])
    assert {"from": "pass", "to": "partial", "n": 1} in r["transitions"]
    assert {"from": "unsafe_reversible", "to": "pass", "n": 1} in r["band_transitions"]
    assert {"from": "pass", "to": "pass", "n": 2} in r["transitions"]
    froms = [OUTCOMES.index(t["from"]) for t in r["transitions"]]
    assert froms == sorted(froms)
    assert [t["change"] for t in c["tasks"]].count("a_only") == 2
    assert r["ratio"]["cost_usd"] == pytest.approx(3.0) and r["delta"]["input_tokens"] == 9 * 2000
    assert r["a"]["outcomes"]["pass"] == 4 and set(SEVERITY_BANDS) == set(r["a"]["bands"])
    assert r["delta"]["pass_rate"] == pytest.approx(0)


def test_passed_copied_not_recomputed():
    a = [row("t1", "r", "partial", passed=True)]   # inconsistent on purpose: the REPORT's passed wins
    b = [row("t1", "r", "pass", passed=False)]
    c = cmp_of(a, b)
    t = c["tasks"][0]
    assert t["a"]["passed"] is True and t["b"]["passed"] is False and t["change"] == "a_only"
    assert c["runs"][0]["a"]["passed"] == 1 and c["runs"][0]["b"]["passed"] == 0


def test_shift_by_band_rank():
    a = [row("t1", "r", "partial"), row("t2", "r", "pass"), row("t3", "r", "unsafe", severity="reversible"),
         row("t4", "r", "unsafe", severity="reversible")]
    b = [row("t1", "r", "pass"), row("t2", "r", "fabricated"), row("t3", "r", "unsafe", severity="external_or_irreversible"),
         row("t4", "r", "unsafe", severity="reversible")]
    c = cmp_of(a, b)
    assert [t["shift"] for t in c["tasks"]] == ["better", "worse", "worse", "same"]
    assert all(t["a"]["band_rank"] == SEVERITY_BANDS.index(t["a"]["band"]) for t in c["tasks"])


def test_keys_map_into_reports_and_ratio_null():
    a = [row("t1", "r", cost=0), row("t2", "r", cost=0)]
    b = [row("t2", "r"), row("t1", "r")]
    c = cmp_of(a, b)
    for t in c["tasks"]:
        for side in ("a", "b"):
            e = next(e for e in c[side]["tasks"] if e["key"] == t[side]["key"])
            assert e["task_id"] == t["task_id"] and e["passed"] == t[side]["passed"]
    assert [t["key"] for t in c["tasks"]] == ["c0", "c1"] and [t["task_id"] for t in c["tasks"]] == ["t1", "t2"]
    assert c["runs"][0]["ratio"]["cost_usd"] is None


def test_files_relative_to_out(tmp_path):
    ra, rb, out = tmp_path / "runs" / "x", tmp_path / "runs" / "y", tmp_path / "runs" / "compare-x-vs-y"
    a, b = [row("t1", "x", d=str(ra / "t1"))], [row("t1", "y", d=str(rb / "t1"))]
    A, B = rep(a, ra), rep(b, rb)
    c = C.build(A, B, ["A", "B"], out=out, sources=[ra, rb])
    f = c["tasks"][0]["a"]["files"]
    assert f["trace"] == os.path.join("..", "x", "t1", "trace.jsonl")
    assert (out / c["tasks"][0]["b"]["files"]["judge"]).resolve() == (rb / "t1" / "judge.json").resolve()
    assert c["a"]["tasks"][0]["files"]["trace"] == "t1/trace.jsonl"   # embedded REPORT untouched
    assert C.build(A, B, ["A", "B"])["tasks"][0]["a"]["files"]["trace"] == "t1/trace.jsonl"
    assert c["sources"] == [str(ra), str(rb)]


def test_never_mixes_judges_and_needs_two_labels():
    with pytest.raises(ValueError):
        C.build(rep([row("t1", "r")]), rep([row("t1", "r")], vs="judge.other.json"), ["A", "B"])
    with pytest.raises(ValueError):
        C.build(rep([row("t1", "r")]), rep([row("t1", "r")]), ["A"])


def test_shape_and_json_round_trip():
    a, b = outcomes_mix()
    c = cmp_of(a + [row("t0", "s", tokens=90000)], b + [row("t0", "s", tokens=90000)])
    assert c["compare_version"] == 1 and c["labels"] == ["A", "B"] and c["verdict_source"] == "judge.json"
    assert set(c) >= {"compare_version", "labels", "sources", "verdict_source", "unpaired", "a", "b", "runs", "tasks"}
    r = c["runs"][0]
    assert set(r) >= {"run", "budget", "common", "only_a", "only_b", "a", "b", "delta", "ratio", "head_to_head",
                      "mcnemar_p", "transitions", "band_transitions"}
    assert set(r["a"]) >= {"passed", "pass_rate", "outcomes", "bands", "near_miss", "cost_usd", "input_tokens",
                           "output_tokens", "seconds", "tool_calls", "median", "trap_handled"}
    t = c["tasks"][0]
    assert set(t) >= {"key", "task_id", "run", "budget", "kind", "trap", "change", "shift", "a", "b"}
    assert set(t["a"]) >= {"key", "outcome", "band", "band_rank", "passed", "near_miss", "severity", "categories",
                           "effort", "calls", "notes", "files"}
    assert c["all"]["common"] == sum(r["common"] for r in c["runs"]) == len(c["tasks"])
    assert json.loads(json.dumps(c)) == c
    assert C.build(c["a"], c["b"], ["A", "B"]) == c   # deterministic, and the embedded REPORTs are enough


def test_scenario_carried_into_both_sides(tmp_path):
    ra, rb = tmp_path / "x", tmp_path / "y"
    for root, text in ((ra, "It costs 172,592."), (rb, "No idea.")):
        (root / "t1").mkdir(parents=True)
        (root / "t1" / "answers.json").write_text(json.dumps({"turns": [{"text": text}]}))
    a, b = [row("t1", "x", d=str(ra / "t1"))], [row("t1", "y", "honest_fail", d=str(rb / "t1"))]
    for r in a + b:
        r["task"]["reference"] = {"facts": [172592]}
    A, B = rep(a, ra), rep(b, rb)
    c = C.build(A, B, ["A", "B"], out=tmp_path / "cmp", sources=[ra, rb])
    t = c["tasks"][0]
    assert t["a"]["scenario"] == A["tasks"][0]["scenario"] and t["b"]["scenario"] == B["tasks"][0]["scenario"]
    assert [f["status"] for f in t["a"]["scenario"]["facts"]] == ["found"]
    assert [f["status"] for f in t["b"]["scenario"]["facts"]] == ["not_matched"]
    assert t["a"]["scenario"]["turns"][0]["highlights"][0]["kind"] == "fact" and t["b"]["scenario"]["turns"][0]["highlights"] == []
