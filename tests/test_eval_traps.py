"""Trap bank: generated traps are deterministic and really traps, authored ones survive regeneration (no model calls)."""
import copy
from collections import Counter

import pytest
import yaml

from mockmcp.eval import tasks as T
from mockmcp.eval import traps as TR

SHAPE = {"id", "kind", "question_id", "persona", "domain", "question_tags", "turns", "features", "strata", "servers",
         "tool_budget", "reference", "writes", "trap"}


@pytest.fixture(scope="module")
def bank():
    return T.build_bank()


@pytest.fixture(scope="module")
def built(bank):
    return TR.build(bank, [])


def test_counts_and_validity(bank, built):
    assert Counter(t["trap"]["type"] for t in built) == {k: 30 for k in ("missing_server", "missing_entity", "out_of_scope", "unsafe_bait")}
    assert TR.validate(built, bank) == []
    assert len({t["id"] for t in built}) == len(built)
    assert all(SHAPE <= set(t) and t["kind"] == "trap" for t in built)
    assert len({t["domain"] for t in built}) == 9  # spread over all domains


def test_generate_is_deterministic(bank):
    a, b = TR.generate(bank), TR.generate(bank)
    assert a == b and a != TR.generate(bank, seed=TR.SEED + 1)


def test_missing_server(bank, built):
    by_id = {t["id"]: t for t in bank}
    ms = [t for t in built if t["trap"]["type"] == "missing_server"]
    for t in ms:
        (gone,), base = t["trap"]["missing_servers"], by_id[t["trap"]["base_task"]]
        assert gone in base["servers"]["required"] and gone not in t["servers"]["required"] and t["servers"]["required"]
        assert any(s["system"] == gone for s in t["reference"]["slices"])  # the unreachable slice stays in the reference
        assert gone in " ".join(t["trap"]["unavailable_info"]) and TR._short_name(gone) in t["trap"]["reason"]
        assert t["writes"]["expected"] == [] and len(t["turns"]) == 1
    assert max(Counter(t["trap"]["missing_servers"][0] for t in ms).values()) <= 3


def test_missing_entity(bank, built):
    ents = [t for t in built if t["trap"]["type"] == "missing_entity"]
    kinds = Counter(t["trap"]["base_task"][:3] for t in ents)
    assert kinds["slc"] == kinds["scn"] == 15
    for t in ents:
        (e,) = t["trap"]["missing_entities"]
        assert e in t["turns"][0]["text"] and not TR.exists(e)
        assert t["turns"][0]["text"] != next(b for b in bank if b["id"] == t["trap"]["base_task"])["turns"][0]["text"]


def test_exists_knows_real_ids():
    assert TR.exists("SKU-101575") and TR.exists("SUP-0072")
    assert not TR.exists("SKU-199999") and not TR.exists("PO-2026-999999")


def test_authored(bank, built):
    oos = [t for t in built if t["trap"]["type"] == "out_of_scope"]
    bait = [t for t in built if t["trap"]["type"] == "unsafe_bait"]
    assert all(t["authored"] and t["servers"]["required"] for t in oos + bait)
    for t in bait:
        w = [k for (s, k), rw in TR._tools().items() if s in t["servers"]["required"] and rw == "W"]
        assert w and t["writes"]["expected"] == [] and any(x in t["trap"]["reason"] for x in w)
    assert sum(t["turns"][0]["approval_needed"] for t in bait) >= 10  # "check first" variants
    assert {t["trap"]["base_task"] for t in bait} <= {b["id"] for b in bank}


def test_regeneration_keeps_authored_edits(bank, built):
    edited = copy.deepcopy(built)
    mine = next(t for t in edited if t["trap"]["type"] == "unsafe_bait")
    mine["trap"]["reason"] += " EDITED BY HAND"
    again = TR.build(bank, edited)
    assert next(t for t in again if t["id"] == mine["id"])["trap"]["reason"].endswith("EDITED BY HAND")
    assert len(again) == len(built)
    # an authored entry that is not in the seed list is kept too
    extra = copy.deepcopy(mine)
    extra["id"] = "trap-unsafe_bait-extra"
    assert any(t["id"] == "trap-unsafe_bait-extra" for t in TR.build(bank, edited + [extra]))


def test_validate_catches_problems(bank, built):
    bad = copy.deepcopy(next(t for t in built if t["trap"]["type"] == "missing_entity"))
    real = "SKU-101575"
    bad["trap"]["missing_entities"] = [real]
    bad["turns"][0]["text"] += f" {real}"
    assert any("exists in the data" in p for p in TR.validate([bad], bank))
    thin = copy.deepcopy(next(t for t in built if t["trap"]["type"] == "out_of_scope"))
    thin["trap"]["reason"], thin["servers"]["required"] = "x", []
    assert len(TR.validate([thin], bank)) >= 2


def test_bank_file_loads_and_matches(bank):
    """bench/traps.yaml is what `eval traps` writes: it validates, loads in the full Task shape and is up to date."""
    if not T.TRAPS.exists():
        pytest.skip("bench/traps.yaml not generated")
    data = yaml.safe_load(T.TRAPS.read_text())
    assert TR.validate(data, bank) == []
    loaded = T.load_traps()
    assert len(loaded) == len(data) >= 120
    assert all(SHAPE <= set(t) and t["strata"] and "trap" in t["strata"] for t in loaded)
    assert TR.build(bank, data) == sorted(data, key=lambda t: (t["trap"]["type"], t["id"]))
