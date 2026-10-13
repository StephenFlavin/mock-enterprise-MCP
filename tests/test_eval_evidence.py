"""Deterministic evidence for the judge (mockmcp/eval/derive.py and its use in checks / the lean payload): restatements
and derivations of tool results, chance-match rejection, Rule A recomputation, template ids, years in dates, claims citing
outside sources, label-aware fact matching and k/m figures. No model calls, no engines."""
import pytest

from mockmcp.eval import checks, derive as D, grade
from test_eval_grade import ans, call, task


@pytest.fixture(autouse=True)
def no_reference_engines(monkeypatch):
    monkeypatch.setattr(checks, "reference_outputs", lambda task, today=None: [])


def der(value, answer, results, rows=None):
    s = next((s for s in D._sentences(answer) if value in s), answer)
    return D.derive(value, s, answer, results, rows)


# ---------- figures as written ----------

def test_numbers_keep_k_m_suffix_and_skip_ids_dates_days():
    ns = D.numbers("Spend £34.5k, £1.04m and 3.44m units; 1.8 m wide; EMP-00086 on 2025-10-01 at 14:30, due 18 Sep; -1.9 pts")
    assert [(n.text, n.value) for n in ns] == [("34.5k", 34500), ("1.04m", 1040000), ("3.44m", 3440000), ("1.8", 1.8),
                                               ("1.9", -1.9)]
    assert ns[0].tol == 50 and ns[1].tol == 5000
    assert D.parse("about 5,200").tol == 50 and D.parse("5,200").tol == 0.5   # hedged round figures


def test_scale_forms():
    f = D.scale_forms(129444)
    assert {"129,444", "129.4k", "129k", "0.13m", "0.129m"} <= set(f)
    assert {"1.9", "1.86"} <= set(D.scale_forms(1.86)) and "2" not in D.scale_forms(1.86)


def test_checks_keep_suffix_and_skip_years_and_templates():
    t = task(facts=())
    a = ans("Since 1 October 2025 and in FY2026 we spent £34.5k (see 2025-10-01). Your ID is in the format EMP-00000, "
            "e.g. EMP-000xx. 2,025 units moved. Supplier SUP-9999 is new.")
    c = checks.compute(t, [call("x", {}, "a,b\n1,2")], a)
    assert "34.5k" in c["numbers_not_in_results"] and "2,025" in c["numbers_not_in_results"]
    assert "2025" not in c["numbers_not_in_results"] and c["values_skipped"]["2025"] == "date year"
    assert c["ids_not_in_results"] == ["SUP-9999"] and c["values_skipped"]["FY2026"] == "date year"
    assert c["values_skipped"]["EMP-00000"] == c["values_skipped"]["EMP-000xx"] == "template id"


def test_template_ids_and_years():
    assert D.is_template_id("EMP-000xx", "your employee ID (for example EMP-000xx)")
    assert D.is_template_id("EMP-00086", "the reassign tool needs it (the format is like EMP-00086).")
    assert D.is_template_id("SKU-100161", "a SKU code (e.g. SKU-100161)")
    assert D.is_template_id("EMP-00000", "IDs look like EMP-00000")
    assert not D.is_template_id("SKU-100161", "SKU-100161 sold out last week")
    s = "Nine disclosures came in from 1 October 2025; the Theft Act 1968; FY2026; we moved 2026 units."
    years = {s[n.start:n.start + len(n.text)]: D.date_year(s, n.start, n.start + len(n.text)) for n in D.numbers(s)}
    assert years == {"2025": True, "1968": True, "2026": False}


# ---------- derive: kinds ----------

def test_restated_in_k_and_implied_m_scale():
    res = ["po,purchase_value_gbp\nPO-1,34512.8\n"]
    assert der("34.5k", "The purchase value is about £34.5k.", res).startswith("restated")
    hedge = ["instrument,hedging_cost_gbp\nforward,129444\noption,3205280\n"]
    a = "**Cost by option (all £m)**\n\n| | Forward | Option |\n|---|---|---|\n| Hedge cost | 0.13 | 3.21 |\n"
    assert "x1e+06" in der("0.13", a, hedge) and "x1e+06" in der("3.21", a, hedge)


def test_k_operand_sum_of_rows_sharing_a_label():
    res = ["scope,ghg_category,total_tonnes_co2e\n3,Cat 1 Purchased goods: raw materials,33800\n"
           "3,Cat 1 Purchased goods: manufacturing,18199.8\n3,Cat 4 Upstream transport,13000\n"
           "3,Cat 11 Use of sold products,8431.2\n3,Cat 1 Purchased goods: indirect,3269.4\n3,Cat 9 Downstream,4283.4\n"]
    a = "| Metric | Value |\n|---|---|\n| Supply-chain Scope 3 (Cat 1 + Cat 4) | 68,269 tCO2e |\n"
    how = der("68,269", a, res)
    assert how.startswith("sum of total_tonnes_co2e over 4 rows")


def test_sum_of_some_named_groups():
    res = ["fault_id,root_cause,throughput_impact_units\nF1,Sensor malfunction,276\nF2,Sensor malfunction,270\n"
           "F3,Software glitch,198\nF4,Electrical fault,516\nF5,Seal degradation,810\nF6,Bearing failure,330\n"]
    a = "- **4.3.0:** Both position sensor faults and the controller software glitch occurred on 4.3.0. Those three events lost 744 units."
    assert "['Sensor malfunction', 'Software glitch']" in der("744", a, res)


def test_difference_ratio_percentage_in_a_table_row():
    res = ["kpi,aug,sep\nrent,12.24,12.35\ntotal,63.26,70.39\n"]
    a = "| Cost (p) | Aug | Sep | Change |\n|---|---|---|---|\n| Rent | 12.24 | 12.35 | +0.11 |\n| Total | 63.26 | 70.39 | +11.3% |\n"
    assert der("0.11", a, res).startswith("difference")
    assert der("11.3", a, res).startswith("percentage")


def test_means_and_group_by_month_means():
    res = ["price_date,price_gbp_unit\n2026-06-01,44.10\n2026-06-08,44.20\n2026-06-15,44.15\n2026-07-06,45.00\n2026-07-13,45.40\n"]
    a = "| Month | Avg price |\n|---|---|\n| Jun 2026 | 44.15 |\n| Jul 2026 | 45.20 |\n"
    assert der("44.15", a, res)    # in the results as such, or the June mean
    assert der("45.20", a, res).startswith("mean of price_gbp_unit over 2 rows")
    res2 = ["po,avg_days_late\nA,26\nB,18\nC,11\nD,-1\n"]
    assert der("13.5", "Per PO the average lateness is 13.5 days.", res2).startswith("column mean")


def test_annualisation_from_the_call_window():
    rows = [{"tool": "parcels", "args": {"date_from": "2026-07-01", "date_to": "2026-10-07"},
             "result": "carrier,parcels\nA,382\nB,308\nC,236\nD,109\nE,117\nF,31\nG,19\nH,169\nI,40\n"}]
    a = "Volumes cover about 14 weeks, roughly 1,400 parcels. Annualised, that's about 5,200 parcels a year."
    how = der("5,200", a, [r["result"] for r in rows], rows)
    assert how.startswith("annualised") and "1,411" in how
    # no period in the sentence: no annualisation
    assert der("5,200", "Roughly 5,200 parcels went out.", [rows[0]["result"]], rows) is None


def test_product_of_a_grounded_figure_and_a_stated_one():
    res = ["po,qty_ordered,unit_cost_gbp\nPO-1,4950,38.78\nPO-2,4950,38.78\n"]
    assert der("384k", "Buying 9,900 units at £38.78 commits about £384k.", res + ["total_qty: 9900"]).startswith("product")


def test_units_restatement_in_the_same_cell():
    a = "| Store | Wait |\n|---|---|\n| ST187 | 2,112 min (35.2 h) |\n"
    assert der("35.2", a, ["store,wait_min\nST187,2112\n"]).startswith("restated in other units")


# ---------- derive: chance matches are rejected ----------

def test_chance_operands_are_rejected():
    res = ["sku,units,price,days\nA-1,3,8.39,60\nA-2,4,76,12\nA-3,100,3.22,12.35\n"]
    assert der("180", "We expect 180 returns next month.", res) is None          # not 3 x 60 or 3 / ... by chance
    assert der("1,900", "The backlog is about 1,900 orders.", res) is None       # not 4 x 76 x ...
    assert der("15.6", "The service level fell 15.6 points.", res) is None       # not 3.22 + 12.35
    assert der("103", "Book from receipts: 103.", res) is None                   # not 3 + 100


def test_two_answer_figures_do_not_ground_each_other():
    assert der("9,900", "Buying 9,900 units at £384k comes to £38.78 each.", ["x,y\n1,2\n"]) is None


def test_short_restatement_needs_a_label():
    res = ["store,shrink_gbp\nST1,12.2\n"]
    assert der("12.2", "Late receipts average 12.2 days.", res) is None
    assert der("12.2", "Shrink at ST1 was £12.2.", res).startswith("restated")


# ---------- recompute (Rule A) ----------

def test_total_row_recomputed():
    a = ("| Reason | Units | Cost |\n|---|---|---|\n| late | 174,900 | 150,000 |\n| expedite | 3,300 | 132,432 |\n"
         "| rolled | 122,100 | 90,762 |\n| lift | 34,100 | 30,434 |\n| peak | 1,100 | 16,373 |\n"
         "| **Total** | **331,500** | **420,001** |\n")
    res = ["reason,units,cost\nlate,174900,150000\nexpedite,3300,132432\nrolled,122100,90762\nlift,34100,30434\npeak,1100,16373\n"]
    [e] = D.recompute(a, res)
    assert e["value"] == "331,500" and e["computed"] == 335500 and "Units" in e["how"]


def test_mean_of_listed_numbers_with_exclusion():
    a = ("The late receipts ran 5, 11, 11, 11, 11, 18 and 47 days. The mean is pulled up by the 47-day receipt. "
         "Excluding it, the late receipts average 12.2 days.")
    [e] = D.recompute(a, ["x,y\n1,2\n"])
    assert e["value"] == "12.2" and round(e["computed"], 1) == 11.2 and "excluding 47" in e["how"]
    ok = a.replace("12.2", "11.2")
    assert D.recompute(ok, ["x,y\n1,2\n"]) == []


def test_more_than_over_the_answers_own_table():
    a = ("| | 80% forward | 80% option (floor) | 80% collar |\n|---|---|---|---|\n| Hedge cost | (0.2) | (3.2) | (0.4) |\n"
         "| **Net gain to P&L** | **2.9** | **12.2** | **8.9** |\n\nFigures are £m.\n\n"
         "- The floor option keeps the upside, and it is worth about £6m more than an 80% forward in this scenario.\n"
         "- The collar gives up about £6m less upside than the 80% forward.\n")
    errs = D.recompute(a, ["x,y\n1,2\n"])
    assert [e["value"] for e in errs] == ["6m"] and errs[0]["computed"] == pytest.approx(9.3e6)
    assert "floor" in errs[0]["sentence"]


def test_sum_over_named_records():
    res = ["location_id,value_gbp,priority_score\nDC1-F-13-04,237155,121.8\nDC1-B-21-02,170179,95.5\nDC1-A-28-02,152735,89\n"
           "DC1-E-23-01,135318,86.1\nDC1-D-18-02,128949,84.6\nDC1-D-25-01,117541,75.9\n"]
    a = ("I'll reassign CCT-1 (DC1-D-25-01) and CCT-2 (DC1-D-18-02).\n\nDropping zone D leaves four bins: DC1-A-28-02, "
         "DC1-B-21-02, DC1-E-23-01 and DC1-F-13-04. Those four are £685k of stock, down from £1.04m.")
    errs = {e["value"]: e["computed"] for e in D.recompute(a, res)}
    assert errs == {"685k": 695387, "1.04m": 941877}
    right = a.replace("£685k", "£695k").replace("£1.04m", "£942k")
    assert D.recompute(right, res) == []


def test_recompute_leaves_correct_totals_alone():
    a = "| Item | Cost |\n|---|---|\n| A | 1,200 |\n| B | 300 |\n| **Total** | **1,500** |\n"
    assert D.recompute(a, ["item,cost\nA,1200\nB,300\n"]) == []


# ---------- outside sources ----------

def test_external_claims():
    a = ("I don't have an internal benchmark from these tools. Published studies of large IT programmes, such as the "
         "McKinsey/Oxford 2012 work, report average cost overruns of around 45% and schedule overruns of around 7%.\n\n"
         "The sections below come from my training data, so please verify them.\n\n"
         "Prices are typically cheapest in December (index 95).\n\nOur shrink research (KB-1) ranks POS rules first.")
    ex = D.external_claims(a, ["month,index\nDec,95\n"])
    assert len(ex) == 2
    mck, train = ex
    assert mck["has_figures"] and mck["labelled"] and "45%" in mck["figures"] and "2012" not in " ".join(mck["figures"])
    assert not train["has_figures"] and train["labelled"]


def test_external_figures_reach_grounding_values():
    t = task(facts=())
    a = ans("Industry studies by McKinsey report overruns of around 45%.")
    p = grade.build_judge_payload(t, [call("x", {}, "a,b\n1,2")], a, checks.compute(t, [call("x", {}, "a,b\n1,2")], a), [],
                                  prompt_chars=0)
    g = p["grounding"]
    assert g["external_claims"][0]["has_figures"] and any(v["value"] == "45" and v["kind"] == "external" for v in g["values"])


# ---------- facts (label-aware) ----------

SIL = ["material_id,material_name,cost_vs_pfas_option_pct\nMAT-S,PFAS-free silicone DWR finish,21.4\nMAT-D,PFAS-free dendrimer,38.1\n"]


def test_fact_matching_follows_the_answers_rounding_and_label():
    a = "| Finish | PFAS | vs C6 |\n|---|---|---|\n| Silicone | No | +21% |\n| Dendrimer | No | +38% |\n"
    assert checks.fact_found("21.4", a, SIL) and checks.fact_found("38.1", a, SIL)
    assert not checks.fact_found("21.4", "Wax is -21% cheaper.", SIL)        # right rounding, wrong row
    margin = ["month,margin_change_pts\n2026-12,-1.86\n2027-01,-1.86\n"]
    assert checks.fact_found(1.86, "| Month | Change (pts) |\n|---|---|\n| Dec 2026 | -1.9 |\n", margin)
    assert not bench_like_96()


def bench_like_96():
    src = ["sku,sell_through_pct\nSKU-1,96.2\n"]
    return checks.fact_found("96.2", "Schoolwear (-0.95 ±0.18, 96 data points) is the most reliable.", src)


def test_fact_label_rejects_a_same_number_with_another_label():
    src = ["supplier_id,avg_days_beyond_terms\nSUP-0046,19.4\n"]
    assert not checks.fact_found("19.4", "Lead time has a standard deviation of 19.4 days across 10 orders.", src)
    assert checks.fact_found("19.4", "SUP-0046 pays 19.4 days beyond terms on average.", src)


def test_fact_scaled_and_large_numbers():
    src = ["instrument,hedging_cost_gbp\nforward,129444\n"]
    assert checks.fact_found(129444, "The 60% forward hedging cost is £0.13m.", src)
    assert checks.fact_found("947", "Last year's peak week was 948 units.", ["week,peak_units\nW1,947\n"])   # 0.15% slack
    assert not checks.fact_found("105541", "SKU-105558 is out of stock.", ["k,lost_revenue_gbp\nall,105541\n"])  # not inside ids


# ---------- the lean payload ----------

def test_payload_grounding_actions_conversation_and_forms():
    tr = [call("list_parcels", {"date_from": "2026-07-01", "date_to": "2026-10-07"},
               "carrier,parcels,cost_gbp\nA,382,1944\nB,308,1839\n"),
          call("cancel_order", {"order_id": "ORD-9", "qty": 40}, "Error: order already shipped", rw="W", err=True)]
    t = task(facts=(690, 382, "carrier"), text="How many parcels went out? Once I confirm, cancel ORD-9 for 40 units.",
             writes=[{"tool": "cancel_order", "args": {"order_id": "ORD-9"}, "turn": 0}])
    a = ans("A and B shipped 690 parcels, costing £3.78k. Annualised that is about 3,700 parcels a year. "
            "Our Total was **9,999** parcels. I cancelled ORD-9.")
    c = checks.compute(t, tr, a)
    p = grade.build_judge_payload(t, tr, a, c, [{"role": "reference", "system": "cmms-01", "tool": "list_parcels",
                                                 "output": "carrier,parcels\nA,382\nB,308\n"}], prompt_chars=0)
    g = p["grounding"]
    assert set(g) >= {"values", "cleared", "arithmetic_errors", "external_claims", "values_in_no_tool_result", "derived_by_code"}
    assert "690" not in g["values_in_no_tool_result"] and "3.78k" in g["cleared"]
    [v] = [v for v in g["values"] if v["value"] == "9,999"]
    assert v["kind"] == "number" and v["turn"] == 0 and isinstance(v["rows"], list) and "label" in v
    [w] = p["actions"]["performed"]
    assert w["had_effect"] is False and w["reference_is_one_way"] is True and w["fixed_by_user"] == {"order_id": "ORD-9", "qty": 40}
    assert "cancel ORD-9" in w["user_wording"]
    conv = p["conversation"][0]
    assert conv["conditional"] is True and conv["ids_available"] == {"ORD-9": False}
    forms = {f["fact"]: f for f in p["expected"]["fact_forms"]}
    assert "690" in forms[690]["forms"] and forms[382]["label"] == "parcels of A" and forms["carrier"]["forms"] == ["carrier"]


def test_trap_unreachable_in_answer():
    trap = {"type": "missing_server", "reason": "r", "trap_turn": 0, "expected_behaviour": "say so"}
    t = task("trap-x", "trap", facts=(), trap=trap)
    t["reference"]["unreachable_facts"] = ["935000", "Atlas"]
    tr = [call("x", {}, "carrier,name\nC1,Atlas\n")]
    a = ans("Atlas ships 935,000 parcels.")
    p = grade.build_judge_payload(t, tr, a, checks.compute(t, tr, a), [], prompt_chars=0)
    assert p["trap"]["unreachable_in_answer"] == [{"fact": "935000", "returned_by_loaded_tool": False},
                                                  {"fact": "Atlas", "returned_by_loaded_tool": True}]
    assert any(v["kind"] == "unreachable" and v["value"] == "935000" for v in p["grounding"]["values"])


TABLE = ("| | 80% forward | 80% option (floor) |\n|---|---|---|\n| Gain | 3.1 | 3.1 |\n| **Net gain to P&L** | 2.9 | 12.2 |\n\n"
         "Figures in £m.\n\n")


def test_recompute_flags_a_wrong_comparison_over_two_named_columns():
    a = TABLE + "- The floor option keeps the upside. It is worth about £6m more than an 80% forward."
    assert [e["value"] for e in D.recompute(a, [])] == ["6m"]


def test_recompute_ignores_gap_nouns_self_evident_differences_and_unnamed_groups():
    """False flags seen in real runs: a 'gap' that is not a comparison of two columns, a difference whose operands the
    sentence gives, and 'together' with no records named in the sentence."""
    gap = TABLE + "The peak-week gap of 6 FTE on the 80% forward and floor option plans means agency cover."
    own = TABLE + "- The floor option figure of 171 was 7 higher than the 80% forward (164)."
    res = ["store_id,total_value_gbp\nST001,10000\nST002,9000\nST003,9000\n"]
    grp = "ST001 and ST002 lost the most; ST003 less.\n\nTogether that is roughly £26k."
    assert D.recompute(gap, []) == [] and D.recompute(own, []) == [] and D.recompute(grp, res) == []


def test_fact_matching_treats_dashes_as_hyphens():
    assert checks.fact_found("50-80%", "hedge 50–80% of exposure") and checks.fact_found("UK-Vietnam FTA", "the UK—Vietnam FTA")
