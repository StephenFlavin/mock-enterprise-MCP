"""The `arithmetic` feature: bench/arithmetic.yaml (facts an answer gets by arithmetic), the feature, preset and filter
terms over it, and that it never moves recipe sampling (no model calls)."""
import pytest

from mockmcp.eval import arithmetic as A
from mockmcp.eval import features as F
from mockmcp.eval import recipe as R
from mockmcp.eval import tasks as T

ROWS = "item,cost_gbp\nPallet racking repair,1240\nConveyor belt,2310\nSensor swap,575\n"


def _task(facts, case="x-01:1:Q1", trap=False):
    s = {"case_id": case, "system": "x", "ref": [], "facts": facts}
    ref = {"slices": [s], "facts": facts, **({"answerable_facts": facts[:1]} if trap else {})}
    return {"kind": "trap" if trap else "slice", "turns": [{"text": "q", "approval_needed": False}], "persona": {},
            "servers": {"required": ["x"]}, "writes": {"expected": []}, "reference": ref, "trap": {"type": "t"} if trap else None}


def test_a_sum_of_two_output_values_is_computed_and_a_verbatim_fact_is_not():
    two = "item,cost_gbp\nConveyor belt,2310\nSensor swap,575\n"
    assert A.classify("2885", [two], "What did the conveyor belt and the sensor swap cost in total?") == {"op": "sum", "stated": False}
    assert A.classify("2310", [two], "What did the conveyor belt cost?") is None
    assert A.classify("2,310", [two]) is None and A.classify("2310.4", [two]) is None   # spelling, not arithmetic
    assert A.classify("Conveyor belt", [two]) is None


def test_a_stated_total_of_listed_rows_counts_and_a_short_one_does_not():
    out = ROWS + "\ntotal_cost_gbp: 4125\n"
    assert A.classify("4125", [out], "What did repairs cost in total?") == {"op": "sum", "stated": True}
    assert A.classify("1240", [out], "What did the racking repair cost?") is None
    assert A.classify("19", ["item,n\na,7\nb,12\n\ntotal_n: 19\n"], "How many in total?") is None   # < 3 significant digits


def test_unknown_when_no_derivation_explains_a_missing_figure():
    assert A.classify("98765", [ROWS], "What is the figure?") == {"op": "unknown", "stated": False}


def test_feature_preset_and_filter_terms(monkeypatch):
    table = {"x-01:1:Q1": {repr("4125"): "sum", repr("0.42"): "ratio"}}
    monkeypatch.setattr(A, "load", lambda: table)
    t = _task(["4125", "0.42", "Conveyor belt"])
    f = F.features(t)
    assert f["arithmetic"] == 2 and f["arithmetic_ops"] == ["ratio", "sum"]
    assert "arithmetic" in F.strata(t)
    for expr, want in (("arithmetic", True), ("!arithmetic", False), ("arithmetic>=2", True), ("arithmetic>=3", False),
                       ("arithmetic_ops=sum", True), ("arithmetic_ops=mean|ratio", True), ("arithmetic_ops=mean", False),
                       ("arithmetic_ops!=mean", True), ("kind=slice&arithmetic", True)):
        assert F.compile_filter(expr)(f) is want, expr
    plain = F.features(_task(["Conveyor belt"]))
    assert plain["arithmetic"] == 0 and plain["arithmetic_ops"] == [] and F.compile_filter("!arithmetic")(plain)
    # a fact another case computes does not count; a trap counts only its answerable facts
    assert F.features(_task(["4125"], case="y-01:1:Q1"))["arithmetic"] == 0
    assert F.features(_task(["0.42", "4125"], trap=True))["arithmetic"] == 1


def test_scenario_counts_only_the_facts_it_requires(monkeypatch):
    bank = T.build_bank()
    scn = next(t for t in bank if t["kind"] == "scenario" and any(s.get("dropped_facts") for s in t["reference"]["slices"]))
    s = next(s for s in scn["reference"]["slices"] if s.get("dropped_facts"))
    monkeypatch.setattr(A, "load", lambda: {s["case_id"]: {repr(f): "sum" for f in s["dropped_facts"]}})
    assert F.features(scn)["arithmetic"] == 0
    monkeypatch.setattr(A, "load", lambda: {s["case_id"]: {repr(f): "sum" for f in s["facts"]}})
    assert F.features(scn)["arithmetic"] == len({repr(f) for f in s["facts"]} & {repr(f) for f in scn["reference"]["facts"]})


def test_file_is_sorted_and_current_for_a_sample_of_systems():
    """bench/arithmetic.yaml is what `eval arithmetic` writes (a sample here for speed; `eval arithmetic --check` checks all)."""
    import yaml
    if not A.FILE.exists():
        pytest.skip("bench/arithmetic.yaml not generated")
    data = yaml.safe_load(A.FILE.read_text()) or {}
    assert list(data) == sorted(data) and all(e["op"] in A.OPS for v in data.values() for e in v)
    systems = sorted({cid.split("-")[0] for cid in data})
    sample = systems[::4] + ["yms"]
    assert A.build(sample) == {k: v for k, v in data.items() if k.split("-")[0] in sample}
    assert A.dump(data) == A.FILE.read_text()


def test_the_feature_never_moves_sampling(monkeypatch):
    """Recipe cells and the ladder do not mention arithmetic, and sampling hashes (seed, id): the drawn tasks are the same
    whatever bench/arithmetic.yaml says."""
    r = R.resolve(R.ROOT / "bench" / "recipes" / "scale-80.yaml")
    real = [t["id"] for t in R.sample(r)[0]]
    monkeypatch.setattr(A, "load", lambda: {})
    assert [t["id"] for t in R.sample(r)[0]] == real
    mix = R.resolve({"kind": "any", "tasks": 20, "seed": 3, "mix": {"write": "25%"}})
    a = [t["id"] for t in R.sample(mix)[0]]
    monkeypatch.undo()
    assert [t["id"] for t in R.sample(mix)[0]] == a
