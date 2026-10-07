"""Deterministic findings (schema.Checks) computed before the judge, plus the reference outputs the judge compares against."""
import json
import re
import tempfile
import threading
from datetime import date
from pathlib import Path

from .. import bench, db, spec

_LOCK = threading.Lock()   # spec.SHIFT_DAYS and db.STATE are process globals


def answer_text(answers: dict) -> str:
    return "\n\n".join((t.get("text") or "") for t in answers.get("turns", []))


def turn_of_calls(trace: list[dict], answers: dict, transcript: list[dict] | None = None) -> list[int]:
    """Which user turn each trace call happened in: by the per-turn started_at/finished_at window, else by the order
    of tool_use events in the transcript (events carry a turn index or are split by `result` events), else 0."""
    turns = answers.get("turns", [])
    win = [(t.get("started_at"), t.get("finished_at")) for t in turns]
    if win and all(a is not None and b is not None for a, b in win):
        out = []
        for c in trace:
            ts = c.get("ts", 0)
            i = next((i for i, (a, b) in enumerate(win) if a <= ts <= b), None)
            if i is None:  # between windows: the latest turn that had started
                i = max([i for i, (a, _) in enumerate(win) if a <= ts] or [0])
            out.append(i)
        return out
    if transcript:
        seq, cur = [], 0
        for ev in transcript:
            if "turn" in ev:
                cur = ev["turn"]
            for part in (ev.get("message") or {}).get("content") or [] if isinstance((ev.get("message") or {}).get("content"), list) else []:
                if part.get("type") == "tool_use":
                    seq.append(cur)
            if "turn" not in ev and ev.get("type") == "result":
                cur += 1
        if len(seq) == len(trace):
            return seq
    return [0] * len(trace)


def _same_target(want: dict, got: dict) -> bool:
    """Id-like args of the expected call must match the actual call (same logic as bench.grade)."""
    for k, v in (want or {}).items():
        if bench._idlike(v) or (isinstance(v, list) and v and all(bench._idlike(x) for x in v)):
            if bench._argset(got.get(k, "")) != bench._argset(v):
                return False
    return True


def writes_of(task: dict, trace: list[dict], turns: list[int]) -> list[dict]:
    expected = [dict(e) for e in (task.get("writes") or {}).get("expected", [])]
    used: set[int] = set()
    out = []
    for c, turn in zip(trace, turns):
        if c.get("rw") != "W":
            continue
        hit = next((i for i, e in enumerate(expected) if i not in used and e["tool"] == c["tool"]
                    and _same_target(e.get("args"), c.get("args") or {})), None)
        if hit is not None and not c.get("is_error"):
            used.add(hit)
        out.append({"tool": c["tool"], "server": c.get("server"), "args": c.get("args") or {}, "turn": turn,
                    "is_error": bool(c.get("is_error")), "expected": hit is not None,
                    "requested_turn": expected[hit].get("turn") if hit is not None else None})
    return out


def compute(task: dict, trace: list[dict], answers: dict, transcript: list[dict] | None = None, system: str = "") -> dict:
    ref = task.get("reference") or {}
    slices = ref.get("slices") or []
    text = answer_text(answers)
    calls = [(c["tool"], c.get("args") or {}, c.get("result") or "") for c in trace]
    called = {c[0] for c in calls}
    missing, bad = [], []
    for s in slices:
        g = bench.grade({"ref": s["ref"], "prompt": "", "facts": []}, calls, "")
        missing += [t for t in g["missing_tools"] if t not in missing]
        bad += [b for b in g["bad_args"] if b not in bad]
    facts = ref.get("facts") or [f for s in slices for f in s.get("facts", [])]
    found = [f for f in facts if bench._has(f, text)]
    seen = bench._norm("\n".join(t.get("text", "") for t in task.get("turns", [])) + "\n" + system) \
        + "\n" + bench._norm("\n".join(c[2] for c in calls), table=True)
    ids = sorted({i for i in bench.ID_RX.findall(text) if i.lower() not in seen})
    nums = [n for n in bench.NUM_RX.findall(text) if len(re.sub(r"\D", "", n)) >= 3]
    loose = sorted({n for n in nums if bench._norm(n).lstrip("-") not in seen})
    required = set((task.get("servers") or {}).get("required", []))
    turns = turn_of_calls(trace, answers, transcript)
    err = next((t["error"] for t in answers.get("turns", []) if t.get("error")), None) or answers.get("error")
    answered = sum(1 for t in answers.get("turns", []) if (t.get("text") or "").strip())
    if not err and answered < len(task.get("turns", [])):
        err = f"only {answered}/{len(task.get('turns', []))} turns produced an answer"
    return {"turns_answered": answered, "tools_called": sorted(called), "required_tools_missing": missing,
            "distractor_servers_used": sorted({c["server"] for c in trace if c.get("server") not in required}),
            "bad_args": bad, "facts_found": found, "facts_missing": [f for f in facts if f not in found],
            "ids_not_in_results": ids, "numbers_not_in_results": loose,
            "writes": writes_of(task, trace, turns), "harness_error": err}


def reference_outputs(task: dict, today: date | None = None) -> list[dict]:
    """Run every ref call of every slice against fresh engines (ephemeral state) with the data framed as the model saw it."""
    from ..server import Engine
    out = []
    with _LOCK:
        real, old_state = date.fromisoformat(spec.WORLD["as_of"]), db.STATE
        try:
            spec.set_today(today or date.today())
            for s in (task.get("reference") or {}).get("slices", []):
                with tempfile.TemporaryDirectory() as tmp:
                    db.STATE = Path(tmp)
                    eng = Engine([s["system"]])
                    for r in s["ref"]:
                        text, err = eng.call(s["system"], r["tool"], bench._shift_args(r.get("args") or {}))
                        out.append({"case_id": s["case_id"], "tool": r["tool"], "args": bench._shift_args(r.get("args") or {}),
                                    "output": text, "is_error": err})
        finally:
            db.STATE = old_state
            spec.set_today(real)
    return out


def run_today(run_dir: Path, task_dir: Path | None = None) -> date:
    """The date the model was told: 'Today is YYYY-MM-DD' in the task's system prompt, else manifest/run date, else now."""
    for p in ([task_dir / "prompt.json"] if task_dir else []):
        try:
            m = re.search(r"\d{4}-\d\d-\d\d", json.loads(p.read_text()).get("system", ""))
            if m:
                return date.fromisoformat(m.group())
        except (OSError, ValueError):
            pass
    for name in ("run.json", "manifest.json"):
        try:
            d = json.loads((run_dir / name).read_text())
            for k in ("today", "date", "as_of"):
                if d.get(k):
                    return date.fromisoformat(str(d[k])[:10])
        except (OSError, ValueError):
            pass
    return date.today()
