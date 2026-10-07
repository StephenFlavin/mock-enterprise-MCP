"""The task bank: every benchmark task that can be built from the validated bench cases and the persona questions.
Bench cases whose `question` is not a persona question (the mdm "lookup" cases) become slice tasks without a scenario.

    build_bank()   -> slice tasks (one per bench case) + scenario tasks (one per question with >= 1 case)
    load_traps()   -> trap tasks from bench/traps.yaml (written by `eval traps`, already in the Task shape)

Deterministic: no randomness, no model calls. Task shape: see schema.py.
"""
import copy
import csv
import functools
import re

import yaml

from .. import bench
from ..catalog import CAT, DOCS

ROOT = bench.ROOT
TRAPS = ROOT / "bench" / "traps.yaml"

# ---------- persona questions ----------

QRX = re.compile(r"\*\*(Q\d+) · (\w+) · (\w+) · (\w+) · (\w+)\*\*\s*(.*)")


@functools.lru_cache(maxsize=1)
def questions() -> dict[str, dict]:
    """'02:11:Q4' -> {persona: {file, no, role}, domain, tags: {type, specificity, scope, complexity}, text, followups}"""
    out = {}
    for f in sorted(DOCS.glob("questions-0*.md")):
        fno, title, persona, cur = f.name[10:12], "", None, None
        for line in f.read_text().splitlines():
            if m := re.match(r"# Questions \d+ · (.+)$", line):
                title = m.group(1).strip()
            elif m := re.match(r"## (\d+)\. (.+?)(?: \(AI score \d\))?$", line):
                persona = {"file": fno, "no": m.group(1), "role": m.group(2).strip()}
            elif (m := QRX.match(line)) and persona:
                q, typ, spec, scope, cx = m.groups()[:5]
                cur = out[f"{fno}:{persona['no']}:{q}"] = {
                    "persona": dict(persona), "domain": title, "followups": [], "text": m.group(6).strip(),
                    "tags": {"type": typ, "specificity": spec, "scope": scope, "complexity": cx}}
            elif cur and line.startswith("- ↳"):
                cur["followups"].append(line[3:].strip())
    return out


# ---------- what a turn asks for ----------

WRITE_VERBS = {"send", "create", "raise", "cancel", "hold", "reassign", "update", "set", "notify", "approve", "issue",
               "book", "place", "order", "block", "merge", "archive", "submit", "reroute", "re-route", "replan", "re-plan",
               "move", "increase", "decrease", "reduce", "change", "assign", "schedule", "log", "open", "close", "file",
               "request", "reserve", "freeze", "release", "escalate", "transfer", "rebook", "re-book", "pause", "stop",
               "flag", "add", "record", "amend", "extend", "reallocate", "reorder", "re-order", "ask", "tell", "email",
               "raise", "switch", "swap", "remove", "delete", "publish", "enrol", "enroll", "trigger", "start", "launch",
               "initiate", "commit", "confirm", "authorise", "authorize", "put", "mark", "tag", "route", "dispatch",
               "expedite", "recall", "withdraw", "reject", "accept", "sign", "pay", "refund", "adjust", "correct",
               "roll", "post", "prepare", "reclassify", "tighten", "loosen", "cut", "lower", "reverse", "reprocess", "resubmit",
               "resend", "chase", "remind", "bump", "turn", "save", "take", "pull", "suspend", "push", "enable", "disable", "activate", "deactivate", "apply",
               "redirect", "shift", "unblock", "bring", "rebalance", "prioritise", "prioritize", "rename", "reprice", "markdown", "re-price", "lock", "unlock", "escalate", "allocate", "split", "reroute"}
FILLERS = r"(?:then|and|also|please|actually|ok(?:ay)?|so|if so|if it is|if not|if they are|if needed|next|finally|afterwards|" \
          r"after that|now|just|go ahead and|can you|could you|would you|i'd like you to|i want you to|you should|you can)"
APPROVAL = re.compile(
    r"check with me|ask me (?:first|before)|run (?:it|that|this) (?:by|past) me|confirm with me|let me (?:approve|confirm|see)|"
    r"(?:once|when|after|if) (?:i've|i have|i|that's|that is|it's|it is|this is|they're|they are|we've|we have)\s*"
    r"(?:agreed|agree|approved?|signed|sign|confirmed?|ok|okay|happy|decided)|before you|don't [^.?]*?until|do not [^.?]*?until|"
    r"until i|with my (?:approval|sign-off|ok)|my (?:approval|sign-off)|wait for my|need my (?:approval|ok)|"
    r"if i (?:approve|agree|say so)|once (?:that|it|this) is (?:agreed|approved|signed off)", re.I)
_CLAUSE = re.compile(r"[.?!;:,]|\band\b|\bthen\b|\bbut\b|\bonce\b|\bafter\b|\bif\b", re.I)


def writes_requested(text: str) -> bool:
    """True when some clause of the text starts with an action verb ('Reassign the two worst', 'then raise a PO')."""
    for clause in _CLAUSE.split(text):
        c = clause.strip().lower()
        c = re.sub(rf"^(?:{FILLERS}\s+)+", "", c)
        w = c.split()
        if not w:
            continue
        if w[0] in WRITE_VERBS and not (len(w) > 1 and w[1] in ("me", "us") and w[0] in ("send", "email", "tell", "ask")):
            return True
        if w[0] in ("get", "have") and len(w) > 3 and re.search(r"\b(to|send|raise|create)\b", c):
            return True
    return bool(re.search(r"\bask (?:the |our |all )?(?:\w+ )?(?:carriers?|suppliers?|vendors?)\b", text, re.I))


def turn(text: str, source: str) -> dict:
    return {"text": text, "source": source, "writes_requested": writes_requested(text),
            "approval_needed": bool(APPROVAL.search(text))}


# ---------- context paragraph: what the slice prompts pin down ----------

STOP = set("the a an and or of to for on in with from by at is are was were as this that these those it its our your their "
           "my we us you me i if when then than also only into onto over under per each every all any some new old same "
           "other which what who whom whose how not no".split())
LABEL_KEYS = {"category", "region", "brand", "department", "country", "lane", "product_group", "channel", "carrier", "supplier"}
PERIOD = re.compile(r"\b(?:last|past|previous|next)\s+\d+\s+(?:days?|weeks?|months?|quarters?|years?)\b", re.I)
ENT = re.compile(r"\b[A-Z]{2}\d-[A-Z]{2}\d{2,}\b|" + bench.ID_RX.pattern)  # lanes like DC1-ST215, then bench ids


def _entities(prompt: str, known: str) -> list[tuple]:
    """Id-like entities of a slice prompt that the question text does not mention, with their label and trailing name:
    'lane DC1-ST215 (Dundee)', 'Carrier A (CAR-010)', 'ST214 Glasgow Retail Park'."""
    out = []
    for m in ENT.finditer(prompt):
        ident, start, end = m.group(0), m.start(), m.end()
        if ident in known:
            continue
        before, after = prompt[:start], prompt[end:]
        label = ""
        if before.endswith("("):
            if lm := re.search(r"\b([A-Z][a-z]+(?: [A-Z])?)\s*\($", before):
                label, ident = lm.group(1), f"({ident})"
        elif lm := re.search(r"(?:^|(?<=[\s,(]))([A-Za-z][\w'’-]*)\s+$", before):
            w = lm.group(1)
            if w.lower() not in STOP and not w.lower().endswith(("ed", "ing")) and not re.search(r"(?:^|[.?!]\s+)" + re.escape(w) + r"\s+$", before):
                label = w
                if pm := re.search(r"(?:^|[,;(]\s*|\s)([A-Z][a-z]+)\s+" + re.escape(w) + r"\s+$", before):
                    if not re.search(r"(?:^|[.?!]\s+)" + re.escape(pm.group(1)) + r"\s+" + re.escape(w) + r"\s+$", before):
                        label = f"{pm.group(1)} {w}"
        tail = ""
        if tm := re.match(r"\s*\(([^()\d]{2,40})\)", after):
            tail = f" ({tm.group(1)})"
        elif tm := re.match(r"((?:\s+[A-Z][\w'’&-]*){1,4})", after):
            tail = tm.group(1)
        out.append((m.group(0), (f"{label} {ident}{tail}").strip()))
    return out


def context_paragraph(qtext: str, slices: list[dict], qtype: str = "") -> str:
    """'Context: ...' resolving what the question leaves implicit (ids, sites, categories, period) from the slice prompts."""
    known = qtext  # ids already in the question need no restating
    seen, items = set(), []
    reads = [s for s in slices if not any(_is_write(s["system"], r["tool"]) for r in s["ref"])]
    slices = reads or slices  # write slices name what the follow-ups resolve ("the three worst loads"), so they stay out
    for s in slices:
        prompt = " ".join(s["prompt"].split())
        found = _entities(prompt, known)
        for r in s["ref"]:
            for k, v in r.get("args", {}).items():
                if k in LABEL_KEYS and isinstance(v, str) and not bench._idlike(v) and v in prompt and v not in known:
                    found.append((v, f"{k.replace('_', ' ')} {v}"))
        for key, e in found:
            if key.lower() not in seen:
                seen.add(key.lower()), items.append(e)
    parts = []
    if items:
        parts.append("I'm asking about " + (", ".join(items[:-1]) + " and " + items[-1] if len(items) > 1 else items[0]))
    if qtype != "RESEARCH" and not PERIOD.search(qtext):
        periods = [p.lower() for s in slices for p in PERIOD.findall(s["prompt"])]
        if periods:
            parts.append("unless I say otherwise, look at the " + max(set(periods), key=lambda p: (periods.count(p), p)))
    return "Context: " + "; ".join(parts) + "." if parts else ""


# ---------- bank ----------

@functools.lru_cache(maxsize=1)
def _write_tools() -> dict:
    rw = {}
    for r in csv.DictReader(open(CAT / "tools.csv")):
        rw[(r["system"], r["tool"])] = r["rw"]
        rw.setdefault(r["tool"], r["rw"])
    return rw


def _is_write(system: str, tool: str) -> bool:
    rw = _write_tools()
    return rw.get((system, tool), rw.get(tool)) == "W"


@functools.lru_cache(maxsize=1)
def _slices() -> dict[str, list[dict]]:
    """question id -> its RefSlices (bench cases), in file order."""
    out: dict[str, list[dict]] = {}
    for f in sorted(bench.CASES.glob("*.yaml")):
        for c in yaml.safe_load(f.read_text()) or []:
            out.setdefault(c["question"], []).append({
                "case_id": c["id"], "system": f.stem, "prompt": " ".join(c["prompt"].split()),
                "ref": [{"tool": r["tool"], "args": r.get("args") or {}} for r in c["ref"]],
                "facts": c.get("facts") or [], "notes": (" ".join(c["notes"].split()) if c.get("notes") else None)})
    return out


def _dedupe(items: list) -> list:
    seen, out = set(), []
    for x in items:
        k = repr(x)
        if k not in seen:
            seen.add(k), out.append(x)
    return out


_SYN = {"send": ["send", "notify", "ask", "tell", "email", "issue", "chargeback", "request"],
        "create": ["create", "raise", "set", "open", "book", "place", "trial", "log", "add", "issue", "order"],
        "reassign": ["reassign", "move", "switch", "swap"], "update": ["update", "increase", "change", "set", "adjust", "reroute", "replan", "re-plan", "hold"],
        "hold": ["hold", "block", "freeze", "pause", "stop"], "cancel": ["cancel", "stop", "withdraw"],
        "block": ["block", "hold", "freeze"], "submit": ["submit", "file", "dispute", "raise"], "merge": ["merge"],
        "archive": ["archive", "close", "remove"], "approve": ["approve", "release"], "issue": ["issue", "send", "tender"]}
_WORD = re.compile(r"[a-z][a-z-]{2,}")


def _turn_for_write(call: dict, slice_: dict, turns: list[dict]) -> tuple[int, str | None]:
    """Which turn requested this write: the turn whose text best matches the action (tool verb + slice prompt words)."""
    verb = call["tool"].split("_")[0]
    verbs = set(_SYN.get(verb, [verb]))
    for clause in _CLAUSE.split(slice_["prompt"]):
        w = re.sub(rf"^(?:{FILLERS}\s+)+", "", clause.strip().lower()).split()
        if w and w[0] in WRITE_VERBS:
            verbs |= set(_SYN.get(w[0], [w[0]]))
    pw = {w for w in _WORD.findall(slice_["prompt"].lower()) if w not in STOP and len(w) > 3}
    scores = []
    for i, t in enumerate(turns):
        words = set(_WORD.findall(t["text"].lower()))
        stems = {w[:6] for w in words}
        score = 2 * len(verbs & words) + min(len({w[:6] for w in pw} & stems) * 0.5, 2) + (1 if t["writes_requested"] else 0)
        if i == 0:
            score += 0.5  # main turn wins ties and near-ties
        scores.append(score)
    best = max(range(len(turns)), key=lambda i: (scores[i], -i))
    note = None
    if scores[best] < 2.5:
        wr = [i for i, t in enumerate(turns) if t["writes_requested"]]
        best = wr[0] if wr else 0
        note = f"write {call['tool']} attached to turn {best} by default (no turn text matches the action clearly)"
    elif best > 0 and not turns[0]["writes_requested"] or best > 0 and scores[best] - scores[0] >= 2:
        note = f"write {call['tool']} attached to follow-up turn {best} by matching the action to its text"
    return best, note


def _scenario(qid: str, q: dict, slices: list[dict]) -> dict:
    ctx = context_paragraph(q["text"], slices, q["tags"].get("type", ""))
    main = q["text"] + (("\n\n" + ctx) if ctx else "")
    turns = [turn(main, "question")] + [turn(f, "followup") for f in q["followups"]]
    turns[0]["writes_requested"] = writes_requested(q["text"])
    expected, notes = [], [s["notes"] for s in slices if s["notes"]]
    for s in slices:
        for r in s["ref"]:
            if _is_write(s["system"], r["tool"]):
                t, note = _turn_for_write(r, s, turns)
                expected.append({"tool": r["tool"], "args": r["args"], "turn": t, "system": s["system"]})
                if note and note not in notes:
                    notes.append(note)
    return _task(f"scn-{qid}", "scenario", qid, q, turns, slices, expected, notes)


def _slice(qid: str, q: dict, s: dict) -> dict:
    expected = [{"tool": r["tool"], "args": r["args"], "turn": 0, "system": s["system"]}
                for r in s["ref"] if _is_write(s["system"], r["tool"])]
    return _task(f"slc-{s['case_id']}", "slice", qid, q, [turn(s["prompt"], "slice_prompt")], [s], expected,
                 [s["notes"]] if s["notes"] else [])


def _task(tid, kind, qid, q, turns, slices, expected, notes) -> dict:
    from .features import features, strata
    t = {"id": tid, "kind": kind, "question_id": qid, "persona": dict(q["persona"]), "domain": q["domain"],
         "question_tags": dict(q["tags"]), "turns": turns, "features": {}, "strata": [],
         "servers": {"required": sorted({s["system"] for s in slices}), "distractors": [], "loaded": []},
         "tool_budget": {},
         "reference": {"slices": copy.deepcopy(slices), "facts": _dedupe([f for s in slices for f in s["facts"]]),
                       "notes": notes},
         "writes": {"expected": expected, "write_tools_loaded": []}, "trap": None}
    t["features"] = features(t)
    t["strata"] = strata(t)
    return t


@functools.lru_cache(maxsize=1)
def _bank() -> tuple:
    qs, sl, out = questions(), _slices(), []
    generic = {"persona": {}, "domain": "", "tags": {}, "text": "", "followups": []}  # cases not tied to a persona question
    for qid in sorted(sl):
        out += [_slice(qid, qs.get(qid, generic), s) for s in sl[qid]]
    for qid in sorted(sl):
        if qid in qs:
            out.append(_scenario(qid, qs[qid], sl[qid]))
    return tuple(out)


def build_bank() -> list[dict]:
    """Every possible task: 1,657 slice tasks (one per bench case) then one scenario task per question with cases."""
    return copy.deepcopy(list(_bank()))


def load_traps() -> list[dict]:
    """Trap tasks from bench/traps.yaml (list of Task dicts, or {traps: [...]}); [] when the file is absent.
    Missing fields are filled so every trap has the full Task shape."""
    from .features import features, strata
    if not TRAPS.exists():
        return []
    data = yaml.safe_load(TRAPS.read_text()) or []
    data = data.get("traps", []) if isinstance(data, dict) else data
    out = []
    for t in data:
        t = dict(t)
        t["kind"] = "trap"
        t["turns"] = [x if isinstance(x, dict) else turn(str(x), "trap") for x in t.get("turns", [])]
        for t_ in t["turns"]:
            t_.setdefault("source", "trap"), t_.setdefault("writes_requested", writes_requested(t_["text"]))
            t_.setdefault("approval_needed", bool(APPROVAL.search(t_["text"])))
        t.setdefault("question_id", None), t.setdefault("persona", {}), t.setdefault("domain", ""), t.setdefault("question_tags", {})
        base = t.get("trap", {}).get("base_task") if t.get("trap") else None
        if base and base in {b["id"] for b in _bank()}:
            b = next(b for b in _bank() if b["id"] == base)
            for k in ("question_id", "persona", "domain", "question_tags"):
                if not t[k]:
                    t[k] = copy.deepcopy(b[k])
        t.setdefault("reference", {}), t["reference"].setdefault("slices", []), t["reference"].setdefault("facts", [])
        t["reference"].setdefault("notes", [])
        t.setdefault("writes", {}), t["writes"].setdefault("expected", []), t["writes"].setdefault("write_tools_loaded", [])
        t.setdefault("servers", {}), t["servers"].setdefault("required", sorted({s["system"] for s in t["reference"]["slices"]}))
        t["servers"].setdefault("distractors", []), t["servers"].setdefault("loaded", [])
        t.setdefault("tool_budget", {})
        t["features"] = features(t)
        t["strata"] = strata(t)
        out.append(t)
    return out
