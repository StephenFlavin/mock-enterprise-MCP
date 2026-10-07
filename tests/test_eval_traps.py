"""Trap bank v2: tiers (simple/complex/multi_turn), missing_tool (absent/hidden), approval flows, hub tool hiding, recipe
budgets and sampling, judge payload and report (no model calls)."""
import copy
import json
from collections import Counter

import pytest
import yaml

from mockmcp.eval import features as F
from mockmcp.eval import grade, recipe, report
from mockmcp.eval import runner
from mockmcp.eval import tasks as T
from mockmcp.eval import traps as TR
from mockmcp.server import Engine

SHAPE = {"id", "kind", "question_id", "persona", "domain", "question_tags", "turns", "features", "strata", "servers",
         "tool_budget", "reference", "writes", "trap"}
TYPES = set(TR.TYPES)


@pytest.fixture(scope="module")
def bank():
    return T.build_bank()


@pytest.fixture(scope="module")
def built(bank):
    return TR.build(bank, [])


def of(built, ty=None, tier=None, variant=None):
    return [t for t in built if (not ty or t["trap"]["type"] == ty) and (not tier or t["trap"]["tier"] == tier)
            and (not variant or t["trap"]["variant"] == variant)]


# ---------- the bank as a whole ----------

def test_counts_and_validity(bank, built):
    by = Counter(t["trap"]["type"] for t in built)
    assert set(by) == TYPES and all(30 <= n <= 40 for n in by.values()), by
    assert 190 <= len(built) <= 215
    assert TR.validate(built, bank, counts=True) == []
    assert len({t["id"] for t in built}) == len(built)
    assert all(SHAPE <= set(t) and t["kind"] == "trap" for t in built)
    assert len({t["domain"] for t in built}) == 9  # spread over all domains
    for ty in TYPES:  # every type reaches every domain but at most one or two
        assert len({t["domain"] for t in of(built, ty)}) >= 8, ty


def test_tier_distribution(built):
    for ty in TYPES:
        n, tiers = len(of(built, ty)), Counter(t["trap"]["tier"] for t in of(built, ty))
        assert set(tiers) == {"simple", "complex", "multi_turn"}, (ty, tiers)
        assert tiers["multi_turn"] >= 0.3 * n and tiers["complex"] >= 0.3 * n, (ty, tiers)


def test_tier_semantics(built):
    for t in built:
        tr, n = t["trap"], len(t["turns"])
        assert 0 <= tr["trap_turn"] < n
        if tr["tier"] == "multi_turn":
            assert n >= 2 and tr["trap_turn"] >= 1
        else:
            assert tr["trap_turn"] == 0 and (n == 1 or tr["type"] == "approval_flow")
        if tr["tier"] == "complex":
            ans = {s["system"] for s in t["reference"]["slices"] if s.get("reachable", True)} or {s["system"] for s in t["reference"]["slices"]}
            assert len(ans) >= 2 or t["features"]["prompt_words"] >= 50
    assert any(len({s["system"] for s in t["reference"]["slices"] if s["reachable"]}) >= 3 for t in of(built, tier="complex"))  # some >= 3 systems


def test_multi_turn_has_real_earlier_turns(built):
    mts = of(built, tier="multi_turn")
    assert len(mts) >= 60
    for t in mts:
        k = t["trap"]["trap_turn"]
        early = [s for s in t["reference"]["slices"] if s["turn"] < k]
        assert early and all(s["reachable"] and s["ref"] and s["facts"] for s in early), t["id"]
        assert t["turns"][0]["source"] in ("question", "slice_prompt"), t["id"]  # a real turn, not authored trap text
        assert t["turns"][k]["text"] not in (t["turns"][0]["text"],)
        assert all(f in t["reference"]["answerable_facts"] for s in early for f in s["facts"])
    # at least one 3-turn conversation: a second real turn before the trap
    assert any(t["trap"]["trap_turn"] >= 2 for t in mts)


def test_reference_fact_split(built):
    for t in built:
        ref = t["reference"]
        assert set(map(repr, ref["answerable_facts"])) | set(map(repr, ref["unreachable_facts"])) == set(map(repr, ref["facts"]))
        assert not set(map(repr, ref["answerable_facts"])) & set(map(repr, ref["unreachable_facts"]))
    for t in of(built, "missing_server"):
        assert t["reference"]["unreachable_facts"]


def test_generate_is_deterministic(bank):
    a, b = TR.generate(bank), TR.generate(bank)
    assert a == b and a != TR.generate(bank, seed=TR.SEED + 1)


# ---------- the original four types ----------

def test_missing_server(bank, built):
    by_id = {t["id"]: t for t in bank}
    ms = of(built, "missing_server")
    for t in ms:
        (gone,), base = t["trap"]["missing_servers"], by_id[t["trap"]["base_task"]]
        assert gone in base["servers"]["required"] and gone not in t["servers"]["required"] and t["servers"]["required"]
        assert any(s["system"] == gone and not s["reachable"] for s in t["reference"]["slices"])  # the unreachable slice stays in the reference
        assert gone in " ".join(t["trap"]["unavailable_info"]) and TR._short_name(gone) in t["trap"]["reason"]
        assert t["writes"]["expected"] == []
    assert max(Counter(t["trap"]["missing_servers"][0] for t in ms).values()) <= 3


def test_missing_entity(bank, built):
    ents = of(built, "missing_entity")
    assert Counter(t["trap"]["tier"] for t in ents) == {"simple": 11, "complex": 11, "multi_turn": 12}
    for t in ents:
        (e,), k = t["trap"]["missing_entities"], t["trap"]["trap_turn"]
        assert e in t["turns"][k]["text"] and not TR.exists(e)
        assert not any(e in x["text"] for x in t["turns"][:k])


def test_exists_knows_real_ids():
    assert TR.exists("SKU-101575") and TR.exists("SUP-0072")
    assert not TR.exists("SKU-199999") and not TR.exists("PO-2026-999999")


def test_authored(bank, built):
    oos, bait = of(built, "out_of_scope"), of(built, "unsafe_bait")
    assert all(t["authored"] and t["servers"]["required"] for t in oos + bait)
    for t in bait:
        w = [k for (s, k), rw in TR._tools().items() if s in t["servers"]["required"] and rw == "W"]
        assert w and t["writes"]["expected"] == [] and any(x in t["trap"]["reason"] for x in w)
    assert sum(t["turns"][t["trap"]["trap_turn"]]["approval_needed"] for t in bait) >= 10  # "check first" variants
    assert {t["trap"]["base_task"] for t in bait} <= {b["id"] for b in bank}
    # complex/multi-turn out_of_scope keep a real answerable part
    for t in of(built, "out_of_scope"):
        assert bool(t["reference"]["slices"]) == (t["trap"]["tier"] != "simple")


# ---------- missing_tool ----------

def test_missing_tool_variants(built):
    mt = of(built, "missing_tool")
    assert Counter(t["trap"]["variant"] for t in mt) == {"absent": 18, "hidden": 18}
    for v in ("absent", "hidden"):
        assert Counter(t["trap"]["tier"] for t in of(built, "missing_tool", variant=v)) == {"simple": 6, "complex": 6, "multi_turn": 6}


def test_absent_claims_verified(built):
    for t in of(built, "missing_tool", variant="absent"):
        tr = t["trap"]
        assert tr["hidden_tools"] == [] and tr["fits_system"] in t["servers"]["required"]
        assert TR.conflicts(t["servers"]["required"], tr["job_terms"], tr["job_rw"]) == [], t["id"]  # no loaded tool does the job
        assert any("write tools" in u or "read-only" in u for u in tr["unavailable_info"])  # the system's tools are listed on the entry
    # sanity of the checker itself: a term that matches a real write tool is reported
    assert TR.conflicts(["mdm"], [r"^merge_"], "W") == ["mdm.merge_vendor_records"]
    assert TR.conflicts(["mdm"], [r"^merge_"], "R") == []


def test_hidden_tools_exist_and_are_needed(built):
    for t in of(built, "missing_tool", variant="hidden"):
        (h,) = t["trap"]["hidden_tools"]
        sid, tool = h.split(".")
        assert (sid, tool) in TR._tool_rows() and sid in t["servers"]["required"]
        assert any(s["system"] == sid and not s["reachable"] and [r["tool"] for r in s["ref"]] == [tool] for s in t["reference"]["slices"])
        assert TR._alternatives(sid, tool) == []
        assert t["trap"]["fits_system"] == sid and t["writes"]["expected"] == []


def test_hub_hides_tools():
    eng = Engine(["hse"], hide=["hse.create_corrective_action"])
    names = {t.name for t in eng.mcp_tools("hse")}
    assert "create_corrective_action" not in names and "list_incidents" in names
    assert len(names) == len(Engine(["hse"]).mcp_tools("hse")) - 1
    text, err = eng.call("hse", "create_corrective_action", {})
    assert err and "Unknown tool" in text
    ok, err2 = eng.call("hse", "list_incidents", {})
    assert not err2
    with pytest.raises(ValueError, match="unknown tool"):
        Engine(["hse"], hide=["hse.no_such_tool"])
    with pytest.raises(ValueError, match="unknown tool"):
        Engine(["hse"], hide=["wms.get_wave_configuration"])  # server not loaded


def test_hidden_call_is_still_recorded(tmp_path):
    eng = Engine(["hse"], record=str(tmp_path / "t.jsonl"), hide=["hse.create_corrective_action"])
    eng.call("hse", "create_corrective_action", {"owner": "x"})
    row = json.loads((tmp_path / "t.jsonl").read_text().splitlines()[0])
    assert row["tool"] == "create_corrective_action" and row["is_error"] and row["rw"] == "W"


def test_runner_passes_hidden_tools(monkeypatch, tmp_path):
    seen = {}

    class P:
        def poll(self):
            return None

    monkeypatch.setattr(runner.subprocess, "Popen", lambda cmd, **kw: seen.setdefault("cmd", cmd) and P())
    monkeypatch.setattr(runner.urllib.request, "urlopen", lambda *a, **k: type("R", (), {"read": lambda s: b""})())
    runner.start_hub(tmp_path, ["hse", "lms"], 1234, hide=["hse.create_corrective_action", "lms.x"])
    cmd = seen["cmd"]
    assert cmd[cmd.index("--hide-tools") + 1] == "hse.create_corrective_action,lms.x"
    seen.clear()
    runner.start_hub(tmp_path, ["hse"], 1234)
    assert "--hide-tools" not in seen["cmd"]


def test_recipe_tool_count_excludes_hidden(built):
    t = next(t for t in of(built, "missing_tool", variant="hidden") if t["trap"]["tier"] == "simple")
    (h,) = t["trap"]["hidden_tools"]
    sid, tool = h.split(".")
    sizes = recipe.measure()
    rec = recipe.resolve({"tools": {"budget": None}})
    shown = recipe.assign([t], rec, sizes, None)[0]
    plain = copy.deepcopy(t)
    plain["trap"]["hidden_tools"] = []
    full = recipe.assign([plain], rec, sizes, None)[0]
    assert shown["tool_budget"]["tools"] == full["tool_budget"]["tools"] - 1
    assert shown["tool_budget"]["tokens"] == full["tool_budget"]["tokens"] - sizes[sid]["per_tool"][tool]
    w = next(x for x in of(built, "missing_tool", variant="hidden")
             if TR._tool_rows()[tuple(x["trap"]["hidden_tools"][0].split("."))]["rw"] == "W" and x["trap"]["tier"] == "simple")
    wsid, wtool = w["trap"]["hidden_tools"][0].split(".")
    assert wtool in sizes[wsid]["write_tools"]
    assert wtool not in recipe.assign([w], rec, sizes, None)[0]["writes"]["write_tools_loaded"]


# ---------- approval flows ----------

def test_approval_metadata(built):
    ap = of(built, "approval_flow")
    assert Counter(t["trap"]["variant"] for t in ap) == {"never_approved": 8, "late_approval": 9, "narrower_scope": 9, "revoked": 8}
    for t in ap:
        a, k, n = t["trap"]["approval"], t["trap"]["trap_turn"], len(t["turns"])
        assert set(a) == {"variant", "allowed_from_turn", "scope", "revoked_at_turn"} and a["variant"] == t["trap"]["variant"]
        w = [w for s in t["servers"]["required"] for (sy, w), rw in TR._tools().items() if sy == s and rw == "W"]
        assert w, t["id"]  # write tools are loaded
        assert t["turns"][k]["approval_needed"] and t["turns"][k]["writes_requested"]
        exp = t["writes"]["expected"]
        if a["variant"] in ("never_approved", "revoked"):
            assert a["allowed_from_turn"] is None and exp == []
            assert (a["revoked_at_turn"] is not None) == (a["variant"] == "revoked")
            if a["revoked_at_turn"] is not None:
                assert k < a["revoked_at_turn"] < n
        else:
            assert k < a["allowed_from_turn"] < n and exp and all(e["turn"] == a["allowed_from_turn"] for e in exp)
            assert a["revoked_at_turn"] is None
            assert t["turns"][a["allowed_from_turn"]]["writes_requested"]
        if a["variant"] == "narrower_scope":
            prepared = sum(len(TR._w_refs(s)) for s in t["reference"]["slices"] if s["turn"] == k)
            assert a["scope"] and 0 < len(exp) < prepared
        else:
            assert a["scope"] is None
        for e in exp:
            assert TR._tools()[(e["system"], e["tool"])] == "W"


def test_approval_late_has_expected_write_only_after_approval(built):
    for t in of(built, "approval_flow", variant="late_approval"):
        a = t["trap"]["approval"]["allowed_from_turn"]
        assert a > t["trap"]["trap_turn"] and all(e["turn"] == a for e in t["writes"]["expected"])


# ---------- validator ----------

def test_regeneration_keeps_authored_edits(bank, built):
    edited = copy.deepcopy(built)
    mine = next(t for t in edited if t["trap"]["type"] == "unsafe_bait")
    mine["trap"]["reason"] += " EDITED BY HAND"
    again = TR.build(bank, edited)
    assert next(t for t in again if t["id"] == mine["id"])["trap"]["reason"].endswith("EDITED BY HAND")
    assert len(again) == len(built)
    extra = copy.deepcopy(mine)
    extra["id"] = "trap-unsafe_bait-extra"
    assert any(t["id"] == "trap-unsafe_bait-extra" for t in TR.build(bank, edited + [extra]))


def test_validate_catches_problems(bank, built):
    def probs(t, **edit):
        t = copy.deepcopy(t)
        for path, v in edit.items():
            node = t
            *ks, last = path.split("__")
            for k in ks:
                node = node[int(k)] if k.isdigit() else node[k]
            node[int(last) if last.isdigit() else last] = v
        return TR.validate([t], bank, counts=False)

    ent = next(t for t in of(built, "missing_entity", "simple"))
    real = "SKU-101575"
    bad = copy.deepcopy(ent)
    bad["trap"]["missing_entities"] = [real]
    bad["turns"][0]["text"] += f" {real}"
    assert any("exists in the data" in p for p in TR.validate([bad], bank))
    thin = copy.deepcopy(of(built, "out_of_scope", "simple")[0])
    thin["trap"]["reason"], thin["servers"]["required"] = "x", []
    assert len(TR.validate([thin], bank)) >= 2
    mt = of(built, "missing_server", "multi_turn")[0]
    assert any("trap_turn" in p for p in probs(mt, trap__trap_turn=0))                       # multi_turn needs a later trap turn
    unreach = copy.deepcopy(mt)
    for sl in unreach["reference"]["slices"]:
        sl["reachable"] = False
    assert any("earlier turn" in p for p in TR.validate([unreach], bank, counts=False))     # no answerable earlier turn left
    cx = of(built, "unsafe_bait", "complex")[0]
    assert any("complex" in p for p in probs(cx, turns__0__text="Short question.", reference__slices=[], servers__required=["qms"]))
    hid = of(built, "missing_tool", variant="hidden")[0]
    assert any("does not exist" in p for p in probs(hid, trap__hidden_tools=["hse.no_such_tool"]))
    assert any("not loaded" in p for p in probs(hid, trap__hidden_tools=["cctv.search_cctv_incident_logs"]))
    ab = next(t for t in of(built, "missing_tool", variant="absent") if t["trap"]["fits_system"] == "mdm")
    assert any("matches the job terms" in p for p in probs(ab, trap__job_terms=["^archive_", "^merge_"]))
    apr = of(built, "approval_flow", variant="late_approval")[0]
    assert any("approval metadata" in p for p in probs(apr, trap__approval__variant="revoked"))
    assert any("allowed_from_turn" in p for p in probs(apr, trap__approval__allowed_from_turn=0))
    # coverage: dropping every multi_turn trap of one type fails the per type x tier targets
    cut = [t for t in built if not (t["trap"]["type"] == "unsafe_bait" and t["trap"]["tier"] == "multi_turn")]
    assert any("unsafe_bait: only 0 multi_turn" in p for p in TR.coverage(cut))


# ---------- features, recipes, judge payload, report ----------

def test_features_and_mix_selectors(bank, built):
    loaded = T.load_traps()
    pre = F.merged_presets()
    f = [t["features"] for t in loaded]
    assert all("tier" in x and "trap_turn" in x and "variant" in x and "turns" in x for x in f)
    for expr, check in (("trap&multi_turn", lambda t: t["kind"] == "trap" and len(t["turns"]) >= 2),
                        ("trap_type=missing_tool", lambda t: t["trap"]["type"] == "missing_tool"),
                        ("tier=complex", lambda t: t["trap"]["tier"] == "complex"),
                        ("variant=hidden&tier=multi_turn", lambda t: t["trap"]["variant"] == "hidden" and t["trap"]["tier"] == "multi_turn"),
                        ("trap_turn>=1", lambda t: t["trap"]["trap_turn"] >= 1)):
        pred = F.compile_filter(expr, pre)
        got = {t["id"] for t in loaded if pred(t["features"])}
        assert got and got == {t["id"] for t in loaded if check(t)}, expr
    # multi_turn preset works for any kind
    scn = next(b for b in bank if b["kind"] == "scenario" and len(b["turns"]) >= 2)
    assert "multi_turn" in F.strata(scn)


def test_recipe_mix_over_trap_bank():
    rec = recipe.resolve({"kind": "trap", "tasks": 8, "seed": 3, "mix": {"trap&multi_turn": 3, "trap_type=missing_tool&tier=complex": 2,
                                                                       "trap_type=approval_flow&variant=revoked": 1}})
    tasks, counts, warns = recipe.sample(rec)
    assert len(tasks) == 8 and not warns
    assert counts["trap&multi_turn"]["drawn"] == 3 and counts["trap_type=missing_tool&tier=complex"]["drawn"] == 2
    assert len({t["id"] for t in tasks}) == 8
    assert sum(1 for t in tasks if t["trap"]["tier"] == "multi_turn") >= 3
    assert sum(1 for t in tasks if t["trap"]["type"] == "missing_tool" and t["trap"]["tier"] == "complex") >= 2
    # without a mix: balanced round-robin over all six types
    plain, _, _ = recipe.sample(recipe.resolve({"kind": "trap", "tasks": 12, "seed": 3}))
    assert {t["trap"]["type"] for t in plain} == TYPES


def test_judge_payload_has_all_trap_fields(built):
    t = next(t for t in built if t["trap"]["type"] == "approval_flow" and t["trap"]["tier"] == "multi_turn")
    p = grade.build_payload(t, [], {"turns": [{"text": "x"}]}, {}, [])
    tr = p["task"]["trap"]
    for k in ("tier", "trap_turn", "hidden_tools", "approval", "variant", "reason", "unavailable_info", "expected_behaviour", "fits_system", "job_terms"):
        assert k in tr
    assert p["task"]["reference"]["answerable_facts"] is not None and "turn" in p["task"]["reference"]["slices"][0]
    prompt = (T.ROOT / "mockmcp" / "eval" / "judge" / "prompt.md").read_text()
    for word in ("trap_turn", "allowed_from_turn", "revoked_at_turn", "hidden_tools", "acted_before_approval", "wrong_write", "narrower_scope"):
        assert word in prompt


def test_report_trap_tables(built):
    traps = []
    for i, t in enumerate(built[:60]):
        passed = i % 3 != 0
        traps.append({"task": t, "outcome": "pass" if passed else "hallucinated", "passed": passed})
    lines, data = report.trap_tables(traps)
    text = "\n".join(lines)
    assert "Trap outcomes by type and tier" in text and "Trap outcomes by type and trap turn" in text
    assert "later turn" in text and "turn 0" in text
    assert sum(v["n"] for v in data["by_type_tier"].values()) == 60 == sum(v["n"] for v in data["by_type_trap_turn"].values())


def test_bank_file_loads_and_matches(bank):
    """bench/traps.yaml is what `eval traps` writes: it validates, loads in the full Task shape and is up to date."""
    if not T.TRAPS.exists():
        pytest.skip("bench/traps.yaml not generated")
    data = yaml.safe_load(T.TRAPS.read_text())
    assert TR.validate(data, bank) == []
    loaded = T.load_traps()
    assert len(loaded) == len(data) >= 190
    assert all(SHAPE <= set(t) and t["strata"] and "trap" in t["strata"] for t in loaded)
    assert TR.build(bank, data) == sorted(data, key=lambda t: (t["trap"]["type"], t["id"]))
