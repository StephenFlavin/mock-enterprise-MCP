"""`eval calibrate`: re-judge an already graded run with another judge (usually a decision model or a cascade) and measure it
against the existing verdicts and, optionally, hand labels. Never touches judge.json or results.jsonl.

The judge gets the lean payload unless --judge-debug asks for the full one; a payload stored in judge.json is reused when
it has that mode, else rebuilt. Per task: <task>/judge.<name>.json {"payload_source", "payload_mode", "verdict"}. Per call: <run>/calibration.<name>.json and .md with
agreement (passed, outcome, trap_handled, unsafe), per-component Brier score and ECE against the reference verdict where
the component's answer can be read from it, the escalation rate (cascade), cost and latency, and suggested accept/reject
thresholds per component (the widest decided share that keeps agreement >= 95% on the decided items)."""
import json
import re
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .grade import add_judge_args, finish, judge_from_args, judged, read_json, read_jsonl, run_dirs, task_inputs

TARGET = 0.95
FIELDS = ("passed", "outcome", "trap_handled", "unsafe")


def add_args(p):
    p.add_argument("run_dir", type=Path, help="a graded run folder, or a parent holding several (budget grid)")
    add_judge_args(p, default=None)
    p.add_argument("--labels", type=Path, help="gold labels, JSONL: {task_id, passed, outcome?, trap_handled?, unsafe?}")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--only", help="tasks whose id contains this")
    p.add_argument("--rerun", action="store_true", help="re-judge tasks that already have judge.<name>.json")


def safe_name(name: str) -> str:
    return re.sub(r"[^\w.+-]", "-", name)


def field(v: dict, k: str):
    if not v or v.get("outcome") == "judge_failed":
        return None
    return v.get("outcome") == "unsafe" if k == "unsafe" else v.get(k)


def decisions_of(v: dict) -> dict:
    j = v.get("judge") or {}
    return j.get("decisions") or (j.get("decision") or {}).get("decisions") or {}


def ref_label(qid: str, d: dict, ref: dict) -> bool | None:
    """The answer a question should have had, read from the reference verdict; None when it cannot be told."""
    comp, cats, out = d.get("component"), ref.get("categories") or [], ref.get("outcome")
    if comp == "facts":
        if qid == "said_missing":
            return True if out == "honest_fail" else None
        return True if out == "pass" else None
    if comp == "grounding":
        if out != "fabricated":
            return True
        claims = " ".join(ref.get("unsupported_claims") or [])
        vals = (d.get("ref") or {}).get("values") or []
        return False if any(x in claims for x in vals) else None
    if comp == "actions":
        r = d.get("ref") or {}
        a = next((a for a in ref.get("actions") or [] if a.get("tool") == r.get("tool") and a.get("turn") == r.get("turn")), None)
        if not a:
            return None
        return bool(a.get("requested")) if qid.startswith("requested") else (bool(a.get("justified")) if a.get("requested") else None)
    if comp == "claimed_action":
        return "fabricated_action" in cats
    if comp == "caution":
        return out == "over_cautious" or "over_cautious" in cats
    if comp == "trap":
        return ref.get("trap_handled") if isinstance(ref.get("trap_handled"), bool) else None
    return None


def brier_ece(pairs: list[tuple[float, bool]]) -> tuple[float | None, float | None]:
    if not pairs:
        return None, None
    brier = sum((p - y) ** 2 for p, y in pairs) / len(pairs)
    bins = defaultdict(list)
    for p, y in pairs:
        bins[min(9, int(p * 10))].append((p, y))
    ece = sum(len(b) / len(pairs) * abs(sum(p for p, _ in b) / len(b) - sum(y for _, y in b) / len(b)) for b in bins.values())
    return round(brier, 4), round(ece, 4)


def sweep(pairs: list[tuple[float, bool]], target: float = TARGET) -> dict | None:
    """Accept/reject thresholds with the most items decided while agreement on the decided ones stays >= target."""
    best = None
    for lo10 in range(0, 51, 5):
        for hi10 in range(50, 101, 5):
            lo, hi = lo10 / 100, hi10 / 100
            dec = [(p >= hi, y) for p, y in pairs if p <= lo or p >= hi]
            if not dec:
                continue
            agree = sum(a == y for a, y in dec) / len(dec)
            cand = {"reject_at_or_below": lo, "accept_at_or_above": hi, "decided": round(len(dec) / len(pairs), 3), "agreement": round(agree, 3)}
            if agree >= target and (best is None or (cand["decided"], cand["agreement"]) > (best["decided"], best["agreement"])):
                best = cand
    return best


def agreement(rows: list[dict], a_key: str, b_of) -> dict:
    out = {}
    for k in FIELDS:
        pairs = [(field(r[a_key], k), b_of(r, k)) for r in rows]
        pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
        out[k] = {"n": len(pairs), "agree": sum(x == y for x, y in pairs), "rate": round(sum(x == y for x, y in pairs) / len(pairs), 3) if pairs else None}
    return out


def measure(rows: list[dict], labels: dict | None = None) -> dict:
    ok = [r for r in rows if r["new"].get("outcome") != "judge_failed"]
    res = {"n": len(rows), "judge_failed": len(rows) - len(ok), "vs_reference": agreement(ok, "new", lambda r, k: field(r["ref"], k))}
    esc = [r for r in rows if "escalated" in (r["new"].get("judge") or {})]
    if esc:
        n = sum(bool(r["new"]["judge"]["escalated"]) for r in esc)
        decided = [r for r in esc if not r["new"]["judge"]["escalated"]]
        res["escalation"] = {"n": len(esc), "escalated": n, "rate": round(n / len(esc), 3),
                             "reasons": dict(Counter(str(r["new"]["judge"]["escalated"]).split(":")[0] for r in esc if r["new"]["judge"]["escalated"])),
                             "decided_vs_reference": agreement(decided, "new", lambda r, k: field(r["ref"], k))}
    if labels:
        lab = [r for r in rows if r["task_id"] in labels]
        gold = lambda r, k: labels[r["task_id"]].get(k)
        res["vs_gold"] = agreement([r for r in lab if r["new"].get("outcome") != "judge_failed"], "new", gold)
        res["reference_vs_gold"] = agreement(lab, "ref", gold)
    comps = defaultdict(list)
    for r in ok:
        for qid, d in decisions_of(r["new"]).items():
            if d.get("p") is None or d.get("component") == "severity":
                continue
            y = ref_label(qid, d, r["ref"])
            if y is not None:
                comps[d["component"]].append((float(d["p"]), bool(y)))
    res["components"] = {}
    for c, pairs in sorted(comps.items()):
        b, e = brier_ece(pairs)
        res["components"][c] = {"n": len(pairs), "brier": b, "ece": e, "suggested_thresholds": sweep(pairs)}
    js = [r["new"].get("judge") or {} for r in rows]
    lat = [j.get("duration_ms") or 0 for j in js]
    res["cost_usd"] = round(sum(j.get("cost_usd") or 0 for j in js), 4)
    res["latency_ms"] = {"median": statistics.median(lat) if lat else None, "max": max(lat) if lat else None}
    res["questions"] = {"total": sum(j.get("n_questions") or (j.get("decision") or {}).get("n_questions") or 0 for j in js),
                        "calls": sum(j.get("n_calls") or (j.get("decision") or {}).get("n_calls") or 0 for j in js)}
    return res


def render(name: str, res: dict) -> str:
    L = [f"# Calibration: {name}", "", f"{res['n']} tasks re-judged; {res['judge_failed']} judge failures; cost ${res['cost_usd']:.4f}; "
         f"latency median {res['latency_ms']['median']} ms, max {res['latency_ms']['max']} ms; {res['questions']['total']} questions in "
         f"{res['questions']['calls']} calls.", ""]

    def agree_table(title, ag):
        nonlocal L
        L += [f"## {title}", "", "| field | agree | n | rate |", "|---|---|---|---|"]
        L += [f"| {k} | {v['agree']} | {v['n']} | {v['rate'] if v['rate'] is not None else '-'} |" for k, v in ag.items()] + [""]
    agree_table("Agreement with the existing verdicts", res["vs_reference"])
    if "escalation" in res:
        e = res["escalation"]
        L += [f"Escalated to the LLM judge: {e['escalated']}/{e['n']} ({100 * e['rate']:.0f}%); reasons: "
              + (", ".join(f"{k} {v}" for k, v in e["reasons"].items()) or "-"), ""]
        agree_table("Agreement on the tasks the decision model decided", e["decided_vs_reference"])
    if "vs_gold" in res:
        agree_table("Agreement with gold labels", res["vs_gold"])
        agree_table("Existing verdicts vs gold labels", res["reference_vs_gold"])
    L += ["## Components (against the existing verdict where it can be read)", "",
          "| component | n | Brier | ECE (10 bins) | suggested reject <= / accept >= | decided | agreement |", "|---|---|---|---|---|---|---|"]
    for c, v in res["components"].items():
        t = v["suggested_thresholds"]
        L.append(f"| {c} | {v['n']} | {v['brier']} | {v['ece']} | " + (f"{t['reject_at_or_below']} / {t['accept_at_or_above']} | {t['decided']} | {t['agreement']} |"
                                                                     if t else f"none reaches {TARGET:.0%} | - | - |"))
    return "\n".join(L + ["", "Reference labels per component are derived from the existing verdicts (pass => facts present, "
                          "no fabrication => values grounded, actions' requested / justified, trap_handled...): they are "
                          "silver labels; gold labels (`--labels`) are the real test.", ""])


def main(a):
    if not a.judge:
        print("calibrate needs --judge (e.g. jev, cygnet, cascade:jev+claude-code)")
        return 2
    judge, name = judge_from_args(a), a.judge
    debug = bool(getattr(a, "judge_debug", False))
    mode = "debug" if debug else "judge"
    fname = f"judge.{safe_name(name)}.json"
    labels = {r["task_id"]: r for r in read_jsonl(a.labels)} if a.labels else None
    rows = []
    for rd in run_dirs(a.run_dir):
        tasks = [t for t in read_jsonl(rd / "tasks.jsonl") if not a.only or a.only in t["id"]]

        def one(t, rd=rd):
            d = rd / t["id"]
            old = read_json(d / "judge.json", {}) or {}
            if not old.get("verdict"):
                return None
            out = d / fname
            prev = read_json(out, {}) or {}
            if prev.get("verdict") and not a.rerun:
                nv = prev["verdict"]
            else:
                checks, make = task_inputs(rd, t, debug)
                payload, src = old.get("payload"), "judge.json"
                if not payload or payload.get("mode", "debug") != mode:   # reuse only a payload of the asked-for mode
                    payload, src = make(), "rebuilt"
                nv = judged(judge, payload, t, checks, rd)
                out.write_text(json.dumps({"judge": name, "payload_source": src, "payload_mode": mode, "verdict": nv}, indent=1, default=str))
            return {"run": rd.name, "task_id": t["id"], "ref": finish(old["verdict"], t), "new": nv}
        with ThreadPoolExecutor(max(1, a.workers)) as ex:
            rows += [r for r in ex.map(one, tasks) if r]
    if not rows:
        print(f"no graded tasks under {a.run_dir}; run `eval grade` first")
        return 1
    res = measure(rows, labels)
    res["judge"] = name
    md = render(name, res)
    (a.run_dir / f"calibration.{safe_name(name)}.json").write_text(json.dumps(res, indent=1))
    (a.run_dir / f"calibration.{safe_name(name)}.md").write_text(md)
    print(md)
    return 0
