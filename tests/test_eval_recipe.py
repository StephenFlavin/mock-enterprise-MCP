"""Task bank, features/filters and the recipe builder (no model calls; tool sizes faked for speed)."""
import collections
import json

import pytest
import yaml

from mockmcp import bench
from mockmcp.eval import features as F
from mockmcp.eval import recipe as R
from mockmcp.eval import tasks as T


@pytest.fixture(scope="module")
def bank():
    return T.build_bank()


@pytest.fixture
def sizes(monkeypatch):
    from mockmcp import catalog
    n = {}
    for r in catalog.load():
        n[r["system"]] = n.get(r["system"], 0) + 1
    fake = {s: {"tools": k, "tokens": k * 100, "write_tools": []} for s, k in n.items()}
    monkeypatch.setattr(R, "measure", lambda out_dir=None: fake)
    return fake


def read(d):
    return [json.loads(x) for x in (d / "tasks.jsonl").read_text().splitlines()]


def test_bank_sizes(bank):
    cases = [c for f in bench.CASES.glob("*.yaml") for c in yaml.safe_load(f.read_text()) or []]
    qids = {c["question"] for c in cases} & set(T.questions())
    assert sum(t["kind"] == "slice" for t in bank) == len(cases) == 1657
    assert sum(t["kind"] == "scenario" for t in bank) == len(qids)
    assert len({t["id"] for t in bank}) == len(bank)


def test_scenarios_are_complete(bank):
    for t in (t for t in bank if t["kind"] == "scenario"):
        assert t["turns"] and t["turns"][0]["source"] == "question"
        assert t["reference"]["facts"] and t["reference"]["slices"]
        assert t["persona"]["role"] and t["domain"] and t["question_tags"]["complexity"]
        assert all(w["turn"] < len(t["turns"]) for w in t["writes"]["expected"])
        assert t["servers"]["required"] == sorted({s["system"] for s in t["reference"]["slices"]})
    s = next(t for t in bank if t["id"] == "scn-02:11:Q3")
    # "Hold the three most exposed loads and reroute them, but check with me first." and no later go-ahead: held, not expected
    assert not s["writes"]["expected"] and [w["turn"] for w in s["writes"]["held"]] == [3, 3, 3]
    assert s["turns"][3]["approval_needed"] and s["turns"][3]["writes_requested"]


def _writes(t):
    return sorted((w["system"] + "." + w["tool"], w["turn"]) for w in t["writes"]["expected"])


def test_write_turns_follow_the_asking_turn(bank):
    """Expected writes sit on the turn that asks for them (or approves them), never on a turn that asks for nothing, and a
    write asked for "once I confirm" / "but ask me first" with no later go-ahead is held, not expected."""
    b = {t["id"]: t for t in bank}
    # the main turn only asks why the count is off; the recount is asked for with the hold in turn 3 (only the correction waits)
    assert _writes(b["scn-01:4:Q1"]) == [("ims.create_cycle_count_task", 3), ("wms.block_location", 3),
                                         ("wms.create_cycle_count_task", 3)]
    assert not b["scn-01:4:Q1"]["turns"][0]["writes_requested"] and b["scn-01:4:Q1"]["turns"][3]["approval_needed"]
    # "delay the non-critical payment run, but ask me first" is never approved; turn 3 asks to cancel instead
    t = b["scn-07:66:Q5"]
    assert _writes(t) == [("ap.cancel_payment_run", 3)] and t["turns"][0]["approval_needed"]
    assert [(w["tool"], w["turn"]) for w in t["writes"]["held"]] == [("update_payment_run_date", 0)]
    # "Flag where I'm short" reports; the rota approval is asked in turn 3, the task changes in turn 4
    t = b["scn-08:71:Q3"]
    assert not t["turns"][0]["writes_requested"] and t["turns"][3]["approval_needed"]
    assert _writes(t) == [("store_ops.delete_task_from_store_week", 4), ("store_ops.reassign_task_to_employee", 4),
                          ("store_wfm.approve_rota_for_store", 3), ("store_wfm.update_shift_for_employee", 3)]
    # "Once I confirm, reprocess them." and the confirmation never comes: nothing expected, its write facts dropped
    t = b["scn-09:83:Q1"]
    assert t["turns"][0]["approval_needed"] and not t["writes"]["expected"]
    assert [w["tool"] for w in t["writes"]["held"]] == ["submit_edi_message_reprocess"]
    assert "Mapping corrected" not in str(t["reference"]["facts"])
    # turns whose verb is not a write verb but which name the action as an instruction ("make the test request", "outline it
    # as a board paper for the board agenda") are the only expected-write turns that do not read as asking for an action
    named = {"scn-06:56:Q4", "scn-07:70:Q1"}
    for t in (t for t in bank if t["kind"] == "scenario" and t["id"] not in named):
        asks = {i for i, x in enumerate(t["turns"]) if x["writes_requested"]}
        assert all(w["turn"] in asks for w in t["writes"]["expected"]) or not asks, t["id"]


def test_held_and_conditional_turn_flags():
    held = ["Once I confirm, reprocess them.", "Delay the run, but ask me first.", "Pull them forward once I've okayed the list.",
            "Submit it once I sign off.", "Send the note once I've approved it."]
    assert all(T.turn(x, "followup")["approval_needed"] for x in held)
    assert all(T.HOLD.search(x) for x in held)
    assert T.turn("Once it looks right, approve the rota.", "followup")["approval_needed"]
    assert not T.HOLD.search("Once it looks right, approve the rota.")  # the assistant checks; the same turn asks
    assert not T.HOLD.search("Prepare the journal for my approval.") and not T.HOLD.search("Hold the bay until it's recounted.")
    assert not T.turn("Flag where I'm short or over by hour.", "followup")["writes_requested"]
    assert T.turn("Only send the UK one for now.", "followup")["writes_requested"]


def test_slice_writes_turn_zero(bank):
    w = [t for t in bank if t["kind"] == "slice" and t["writes"]["expected"]]
    assert w and all(x["turn"] == 0 for t in w for x in t["writes"]["expected"])


def test_turn_flags():
    assert T.turn("Hold the loads, but check with me first.", "followup")["approval_needed"]
    assert T.turn("Reassign the two worst-hit loads to the backup carrier.", "followup")["writes_requested"]
    assert not T.turn("Which lanes lost the most fill rate?", "followup")["writes_requested"]
    assert not T.turn("Send me a summary.", "followup")["writes_requested"]


def test_filters_and_presets(bank):
    f = {t["id"]: t["features"] for t in bank}
    p = F.merged_presets()
    one = next(t for t in bank if t["kind"] == "slice" and p["simple"](t["features"]))
    assert F.features(one) == one["features"] and one["features"]["calls"] == 1
    assert F.compile_filter("kind=slice&systems>=1")(f[one["id"]])
    assert F.compile_filter("domain=01|%s" % one["persona"]["file"])(f[one["id"]])
    assert not F.compile_filter("kind=scenario or writes>=1")(f[one["id"]]) or one["features"]["writes"] >= 1
    assert F.compile_filter("simple&!write")(f[one["id"]]) == p["simple"](f[one["id"]])
    assert F.merged_presets({"short": "prompt_words<=5"})["short"](f[one["id"]]) == (f[one["id"]]["prompt_words"] <= 5)
    with pytest.raises(KeyError):
        F.compile_filter("nonsense>=3")(f[one["id"]])


def test_deterministic(tmp_path, sizes):
    rec = {"name": "d", "seed": 3, "kind": "any", "tasks": 20, "mix": {"simple": "30%", "write": "20%"}, "traps": 0,
           "tools": {"budget": {"tokens": 4000}, "distractors": "random", "position": "random"}}
    R.build(rec, tmp_path / "a"), R.build(rec, tmp_path / "b"), R.build({**rec, "seed": 4}, tmp_path / "c")
    a, b, c = (read(tmp_path / x) for x in "abc")
    assert a == b and a != c and len(a) == 20


def test_mix_quotas(tmp_path, sizes):
    rec = {"seed": 1, "kind": "scenario", "tasks": 20, "mix": {"multi_system": "25%", "write": "25%", "followups": 0.25}}
    plan = R.build(rec, tmp_path)
    cnt = plan["counts"]
    assert [cnt[k]["drawn"] for k in ("multi_system", "write", "followups")] == [5, 5, 5]
    assert cnt["natural"]["drawn"] == 5 and len(read(tmp_path)) == 20
    tasks = read(tmp_path)
    assert sum("multi_system" in t["strata"] for t in tasks) >= 5 and sum("write" in t["strata"] for t in tasks) >= 5


def test_short_stratum_warns_or_fails(tmp_path, sizes):
    rec = {"seed": 1, "kind": "scenario", "tasks": 40, "mix": {"systems>=6": 40}}
    plan = R.build(rec, tmp_path / "w")
    assert plan["warnings"] and len(read(tmp_path / "w")) == 40
    with pytest.raises(ValueError):
        R.build({**rec, "strict": True}, tmp_path / "s")


def test_followups_none(tmp_path, sizes):
    R.build({"seed": 1, "kind": "scenario", "tasks": 10, "followups": "none"}, tmp_path)
    assert all(len(t["turns"]) == 1 and t["features"]["followups"] == 0 for t in read(tmp_path))
    R.build({"seed": 1, "kind": "scenario", "tasks": 10, "followups": "first_n:1"}, tmp_path / "n")
    assert all(len(t["turns"]) <= 2 for t in read(tmp_path / "n"))


@pytest.mark.parametrize("strategy", ["random", "adjacent", "persona"])
@pytest.mark.parametrize("budget", [{"tokens": 3000}, {"tools": 90}, {"servers": 6}])
def test_budget_reached_within_one_server(tmp_path, sizes, strategy, budget):
    R.build({"seed": 2, "kind": "scenario", "tasks": 10,
             "tools": {"budget": budget, "distractors": strategy, "position": "middle"}}, tmp_path)
    (unit, limit), = budget.items()
    for t in read(tmp_path):
        tb, dist, loaded = t["tool_budget"], t["servers"]["distractors"], t["servers"]["loaded"]
        assert set(t["servers"]["required"]) <= set(loaded) and tb["target"] == budget
        if dist:
            last = 1 if unit == "servers" else sizes[dist[-1]][unit]
            assert tb[unit] >= limit > tb[unit] - last  # crossed by the last distractor only
        else:
            assert tb[unit] >= limit  # the required servers alone already fill it


def test_budget_crossing_server_is_last(sizes):
    req = ["tms"]
    order = [s for s in sizes if s != "tms"]
    for lim in (1, sizes["tms"]["tokens"] + 1, 5000, 20000):
        d = R._select(req, order, {"tokens": lim}, sizes)
        total = sizes["tms"]["tokens"] + sum(sizes[s]["tokens"] for s in d)
        assert total >= lim or d == order
        assert not d or total - sizes[d[-1]]["tokens"] < lim


def test_grid_is_nested_and_comparable(tmp_path, sizes):
    rec = {"seed": 5, "kind": "scenario", "tasks": 8, "tools": {"budget": {"tokens": [2000, 8000, 30000]}, "distractors": "adjacent"}}
    plan = R.build(rec, tmp_path)
    assert set(plan["runs"]) == {"tokens-2000", "tokens-8000", "tokens-30000"}
    runs = {k: read(tmp_path / k) for k in plan["runs"]}
    ids = [[t["id"] for t in v] for v in runs.values()]
    assert ids[0] == ids[1] == ids[2]
    for lo, hi in (("tokens-2000", "tokens-8000"), ("tokens-8000", "tokens-30000")):
        for a, b in zip(runs[lo], runs[hi]):
            assert set(a["servers"]["loaded"]) <= set(b["servers"]["loaded"])
    assert json.loads((tmp_path / "manifest.json").read_text())["subruns"] == list(plan["runs"])
    assert (tmp_path / "tokens-2000" / "recipe.yaml").exists()


def test_position_and_shared(tmp_path, sizes):
    base = {"seed": 2, "kind": "scenario", "tasks": 6, "tools": {"budget": {"servers": 8}, "distractors": "random"}}
    for pos in ("first", "last"):
        R.build({**base, "tools": {**base["tools"], "position": pos}}, tmp_path / pos)
        for t in read(tmp_path / pos):
            n, loaded = len(t["servers"]["required"]), t["servers"]["loaded"]
            assert set(loaded[:n] if pos == "first" else loaded[-n:]) == set(t["servers"]["required"])
    R.build({**base, "tools": {**base["tools"], "toolset": "shared"}}, tmp_path / "sh")
    loads = {tuple(t["servers"]["loaded"]) for t in read(tmp_path / "sh")}
    assert len(loads) == 1


def test_distractors_none_and_adjacent_prefers_cousins(sizes):
    g = R.Graph()
    import random
    cands = [s for s in sizes if s != "tms"]
    assert g.order("none", {"tms"}, "02", cands, random.Random(1)) == []
    top = g.order("adjacent", {"tms"}, "02", cands, random.Random(1))[:5]
    assert sum(g.cooc["tms"][s] for s in top) > 0 and g.cooc["tms"][top[0]] >= g.cooc["tms"][top[-1]]


def test_traps_drawn_and_missing_server_removed(tmp_path, sizes, monkeypatch):
    def trap(i, ty, **kw):
        return {"id": f"trap-{ty}-{i}", "turns": ["What is the status of lane DC9-ST999?"],
                "trap": {"type": ty, "reason": "r", "missing_servers": kw.get("missing", []), "missing_entities": [],
                         "unavailable_info": [], "expected_behaviour": "say so", "base_task": None},
                "servers": {"required": ["tms", "carrier_portal"]}}
    f = tmp_path / "traps.yaml"
    f.write_text(yaml.safe_dump([trap(i, ty, missing=["tms"] if ty == "missing_server" else [])
                                 for i in range(3) for ty in ("missing_server", "out_of_scope")]))
    monkeypatch.setattr(T, "TRAPS", f)
    plan = R.build({"seed": 1, "kind": "scenario", "tasks": 10, "traps": "40%", "tools": {"budget": {"servers": 5}}}, tmp_path / "o")
    got = [t for t in read(tmp_path / "o") if t["kind"] == "trap"]
    assert len(got) == 4 and {t["trap"]["type"] for t in got} == {"missing_server", "out_of_scope"}
    assert all("tms" not in t["servers"]["loaded"] for t in got if t["trap"]["type"] == "missing_server")
    assert all("tms" in t["servers"]["loaded"] for t in got if t["trap"]["type"] == "out_of_scope")
    assert all("trap" in t["strata"] for t in got) and not plan["warnings"]


# ---------- ladder (nested scale recipes) ----------

def _ladder(n, **kw):
    from mockmcp.eval import recipe as R
    r = R.resolve(R.load(R.ROOT / "bench/recipes/scale.yaml") | {"tasks": n} | kw)
    return R, r, R.sample(r)[0]


def test_scale_recipes_nest_and_are_deterministic():
    R, _, small = _ladder(80)
    _, _, mid = _ladder(160)
    _, _, again = _ladder(80)
    ids = lambda ts: {t["id"] for t in ts}
    assert len(small) == 80 and len(mid) == 160
    assert ids(small) < ids(mid)
    assert [t["id"] for t in small] == [t["id"] for t in again]
    # every scale-N file is the base with only tasks/name changed
    for n in ("80", "160", "320", "all"):
        r = R.load(R.ROOT / f"bench/recipes/scale-{n}.yaml")
        assert r["tasks"] == (n if n == "all" else int(n)) and r["ladder"] == R.load(R.ROOT / "bench/recipes/scale.yaml")["ladder"]


def test_ladder_prefix_keeps_the_mix_and_spreads_domains():
    _, r, small = _ladder(80)
    cells = collections.Counter(t["features"]["ladder_cell"] for t in small)
    w = r["ladder"]
    for c, weight in w.items():
        assert abs(cells[c] - 80 * weight / sum(w.values())) <= 1, (c, cells[c])
    assert len({t["domain"] for t in small if t["kind"] != "trap"}) >= 8
    slices = [t["question_id"] for t in small if t["kind"] == "slice"]
    assert len(slices) == len(set(slices))  # one slice per persona question


def test_seed_changes_the_ladder():
    _, _, a = _ladder(80)
    _, _, b = _ladder(80, seed=2)
    assert {t["id"] for t in a} != {t["id"] for t in b}


def test_budget_grid_nests_distractors_and_keeps_their_order():
    R, r, small = _ladder(80)
    sizes = R.measure()
    runs = [R.assign(small[:20], r, sizes, b) for b in R.budgets(r)]
    for lo, hi in zip(runs, runs[1:]):
        for a, b in zip(lo, hi):
            assert a["id"] == b["id"]
            assert set(a["servers"]["distractors"]) <= set(b["servers"]["distractors"])
            assert a["tool_budget"]["tokens"] <= b["tool_budget"]["tokens"]
            common = [s for s in b["servers"]["loaded"] if s in a["servers"]["loaded"]]
            assert common == a["servers"]["loaded"]  # added servers slot in; the existing order is kept
