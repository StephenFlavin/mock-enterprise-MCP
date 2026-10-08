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
               "redirect", "shift", "unblock", "bring", "rebalance", "prioritise", "prioritize", "rename", "reprice", "markdown", "re-price", "lock", "unlock", "escalate", "allocate", "split", "reroute",
               "delay", "postpone", "defer", "recount", "fix", "retry", "rerun", "re-run", "drop"}
FILLERS = r"(?:then|and|also|please|actually|only|ok(?:ay)?|so|if so|if it is|if not|if they are|if needed|next|finally|afterwards|" \
          r"after that|now|just|go ahead and|can you|could you|would you|i'd like you to|i want you to|you should|you can)"
# HOLD: the action waits for a LATER go-ahead from the user ("once I confirm", "ask me first"). Writes asked for under it are
# expected only if a later turn gives that go-ahead.
HOLD = re.compile(
    r"check with me|ask me (?:first|before)|run (?:it|that|this) (?:by|past) me|confirm with me|let me (?:approve|confirm|see)|"
    r"(?:once|when|after|if) (?:i've|i have|i|that's|that is|it's|it is|this is|they're|they are|we've|we have)\s*"
    r"(?:agree[ds]?|approve[ds]?|signed|sign|confirm(?:ed|s)?|ok(?:ay)?(?:ed|'d)?|happy|decided)\b|before you|don't [^.?]*?until|"
    r"do not [^.?]*?until|until i\b|with my (?:approval|sign-off|ok)|(?<!for )my (?:approval|sign-off)|wait for my|need my (?:approval|ok)|"
    r"if i (?:approve|agree|say so)|once (?:that|it|this) is (?:agreed|approved|signed off)", re.I)
# CHECK: the action is conditional on a check the assistant makes ("once it looks right"); the same turn asks for it.
CHECK = re.compile(r"\b(?:once|when|if|after) (?:it|that|this|they|the \w+|everything|all) (?:looks?|seems?|is|are) "
                   r"(?:right|ok|okay|good|fine|correct|in order)\b", re.I)
# FOR_ME: "prepare the journal for my approval" asks for the draft now; the approval is a later, separate step.
FOR_ME = re.compile(r"for my (?:approval|sign-off|review)", re.I)
APPROVAL = re.compile("|".join(x.pattern for x in (HOLD, CHECK, FOR_ME)), re.I)
GO = re.compile(r"\b(?:go ahead|confirmed|approved|i confirm|i approve|yes,? (?:do|go|please)|do it|proceed|you can now|"
                r"green light|sign(?:ed)? off|that's fine,? (?:do|go))\b", re.I)
_CLAUSE = re.compile(r"[.?!;:,]|\band\b|\bthen\b|\bbut\b|\bonce\b|\bafter\b|\bif\b", re.I)
_SENTENCE, _AND = re.compile(r"[.?!;]+\s*"), re.compile(r",?\s+\b(?:and(?:\s+then)?|then)\b[\s,]+", re.I)
_WH = {"where", "what", "which", "whether", "when", "how", "who"}  # "flag where I'm short" reports, it does not write


def writes_requested(text: str) -> bool:
    """True when some clause of the text starts with an action verb ('Reassign the two worst', 'then raise a PO')."""
    for clause in _CLAUSE.split(text):
        c = clause.strip().lower()
        c = re.sub(rf"^(?:{FILLERS}\s+)+", "", c)
        w = c.split()
        if not w:
            continue
        if w[0] in WRITE_VERBS and not (len(w) > 1 and (w[1] in ("me", "us") and w[0] in ("send", "email", "tell", "ask")
                                                        or w[0] == "flag" and w[1] in _WH)):
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
    """question id -> its RefSlices (bench cases), in file order. Two optional case fields shape the scenario built from the
    persona question (the slice task always uses the case's own prompt and facts):
        scenario_context: inputs the slice prompt gives that the persona question does not (assumed volumes, a unit value),
                          said by the user in the scenario's Context paragraph
        scenario_facts:   the facts a scenario answer must state, when some case facts depend on inputs the scenario never
                          gives (Rule C: a fact the user's turns cannot lead to is not required); the others are kept on the
                          scenario's slice as dropped_facts
    and one for traps:
        inputs_from:      systems whose data the ref arguments stand for (a volume the prompt states that another system
                          holds); a missing_server trap without one of them marks this slice unreachable too
        turn_facts:       {turn: [facts]}, which scenario turn asks for a fact where the words cannot tell (fact_turns)"""
    out: dict[str, list[dict]] = {}
    for f in sorted(bench.CASES.glob("*.yaml")):
        for c in yaml.safe_load(f.read_text()) or []:
            s = {"case_id": c["id"], "system": f.stem, "prompt": " ".join(c["prompt"].split()),
                 "ref": [{"tool": r["tool"], "args": r.get("args") or {}} for r in c["ref"]],
                 "facts": c.get("facts") or [], "notes": (" ".join(c["notes"].split()) if c.get("notes") else None)}
            s.update({k: " ".join(c[k].split()) if k == "scenario_context" else c[k]
                      for k in ("scenario_context", "scenario_facts", "inputs_from", "turn_facts") if c.get(k) is not None})
            out.setdefault(c["question"], []).append(s)
    return out


def _dedupe(items: list) -> list:
    seen, out = set(), []
    for x in items:
        k = repr(x)
        if k not in seen:
            seen.add(k), out.append(x)
    return out


_SYN = {"delete": ["delete", "remove", "drop", "cancel"], "send": ["send", "notify", "ask", "tell", "email", "issue", "chargeback", "request"],
        "create": ["create", "raise", "set", "open", "book", "place", "trial", "log", "add", "issue", "order"],
        "reassign": ["reassign", "move", "switch", "swap", "give", "hand"], "update": ["update", "increase", "change", "set", "adjust", "apply", "correct", "amend", "reroute", "replan", "re-plan", "hold"],
        "hold": ["hold", "block", "freeze", "pause", "stop"], "cancel": ["cancel", "stop", "withdraw"],
        "block": ["block", "hold", "freeze"], "submit": ["submit", "file", "dispute", "raise"], "merge": ["merge"],
        "archive": ["archive", "close", "remove"], "approve": ["approve", "release"], "issue": ["issue", "send", "tender"],
        "reserve": ["reserve", "hold", "ring-fence"]}
_WORD = re.compile(r"[a-z][a-z-]{2,}")


def _action_words(call: dict, slice_: dict) -> tuple[set, set, set]:
    """(verbs, prompt words, object stems) that describe a write: the tool verb and the slice prompt's action verbs with
    their synonyms, the slice prompt's content words, and the tool name's object words (close_task -> task). When the call's
    ids appear in the prompt, only the clauses naming them lend their verbs ("Release CCT-900101 ... then drop the aisle D
    counts by reassigning CCT-900105": release is not a verb of the reassignment)."""
    verb = call["tool"].split("_")[0]
    verbs = set(_SYN.get(verb, [verb]))
    lead = [(w[0] if w and w[0] in WRITE_VERBS else None, c) for c in _CLAUSE.split(slice_["prompt"])
            for w in [re.sub(rf"^(?:{FILLERS}\s+)+", "", c.strip().lower()).split()]]
    ids = [str(v) for v in call.get("args", {}).values() if isinstance(v, str) and bench._idlike(v)]
    mine = set()
    for i, (_, c) in enumerate(lead):
        if any(x in c for x in ids):  # the clause naming the call's id, or the nearest one before it with a verb
            mine.add(next((j for j in range(i, -1, -1) if lead[j][0]), i))
    acts = [i for i, (v, _) in enumerate(lead) if v]
    own = [i for i in acts if lead[i][0] in verbs]
    text = slice_["prompt"]
    if own and len(own) < len(acts):  # "Put a hold on bin X ..., and create a recount task for that bin": the clause led by
        mine = set(own)               # the call's own verb is its ask, and only that ask's words describe it
        text = " ".join(c for i in own for c in [lead[k][1] for k in range(i, next((j for j in acts if j > i), len(lead)))])
    for i, (v, _) in enumerate(lead):
        if v and (i in mine or not mine):
            verbs |= set(_SYN.get(v, [v]))
    pw = {w[:6] for w in _WORD.findall(text.lower()) if w not in STOP and len(w) > 3}
    objs = {w[:6] for w in call["tool"].split("_")[1:] if len(w) > 2 and w not in STOP}
    return verbs, pw, objs


def _match(text: str, verbs: set, pw: set, objs: set) -> float:
    words = set(_WORD.findall(text.lower()))
    stems = {w[:6] for w in words}
    return 2 * len(verbs & words) + min(len(pw & stems) * 0.5, 2) + 1.5 * len(objs & stems)


def _parts(text: str) -> list[tuple[str, bool]]:
    """The asks in `text` (sentences, split at "and"/"then" where the hold is local), each with whether it waits for a later
    go-ahead. "..., but ask me first" holds its whole sentence; a leading "once I approve, create it and put the POs on hold"
    holds the rest of its sentence; a trailing "correct it once I confirm the figure" holds only its own ask."""
    out = []
    for sent in (s for s in _SENTENCE.split(text) if s.strip()):
        m = HOLD.search(sent)
        if m and not re.match(r"(?:once|when|after|if|until)\b", m.group(0), re.I):
            out.append((sent, True))
            continue
        carry = False
        for part in (p for p in _AND.split(sent) if p.strip()):
            m = HOLD.search(part)
            out.append((part, bool(carry or m)))
            carry = carry or bool(m and not part[:m.start()].strip(" ,"))
    return out


def _held(text: str, verbs: set, pw: set, objs: set) -> bool:
    """Does the ask in `text` that best matches this action wait for a later go-ahead? In "Put a hold on the bay, and correct
    it once I confirm the figure" the hold is asked for now and only the correction waits. Asks that use one of the action's
    verbs come first, so a scene-setting sentence full of the same nouns does not hide "correct it, but ask me first"."""
    parts = _parts(text)
    verbal = [(p, h) for p, h in parts if verbs & set(_WORD.findall(p.lower()))]
    scored = [(_match(p, verbs, pw, objs), held) for p, held in verbal or parts]
    top = max((sc for sc, _ in scored), default=0)
    if top <= 0:
        return bool(scored) and all(h for _, h in scored)
    return any(h for sc, h in scored if sc == top)


_IMPERATIVE = WRITE_VERBS | {"compare", "outline", "draft", "build", "write", "give", "show", "list", "summarise", "summarize",
                             "make", "produce", "turn", "use"}


def _names_object(text: str, objs: set) -> bool:
    """An instruction (not a question or a statement of fact) naming two of the tool's object words: "Actually, make the test
    request for the second trend instead", "Compare ..., and outline it as a board paper for the board agenda"."""
    for s in re.split(r"(?<=[.?!])\s+", text):
        w = re.sub(rf"^(?:{FILLERS}\W+)+", "", s.strip().lower()).split()
        if w and w[0] in _IMPERATIVE and not s.rstrip().endswith("?") and len(objs & {x[:6] for x in _WORD.findall(s.lower())}) >= 2:
            return True
    return False


def _leads(text: str, verbs: set) -> bool:
    """Some clause of the text starts with one of these verbs: "Hold 20% for click-and-collect" asks for the hold, "whether
    we could hold some back" only wonders about it."""
    return any((w := re.sub(rf"^(?:{FILLERS}\s+)+", "", c.strip().lower()).split()) and w[0] in verbs for c in _CLAUSE.split(text))


def _turn_for_write(call: dict, slice_: dict, turns: list[dict]) -> tuple[int | None, str | None]:
    """Which turn requested this write: the turn whose text best matches the action (tool verb + slice prompt words), among
    the turns that ask for an action at all. When that ask waits for the user's go-ahead ("ask me first", "once I confirm"),
    the write belongs to the first later turn that gives it (names the action, or says "go ahead"/"confirmed"), unless that
    turn swaps the action for another ("cancel it rather than delaying it"). No go-ahead: the write is not expected
    (stopping to ask is the right behaviour): returns -1 - (the turn that asked), so the caller can keep it as held. No turn
    that names the action at all (the slice prompt asks for it, the scenario's turns never do): None, not expected."""
    verbs, pw, objs = _action_words(call, slice_)
    own = set(_SYN.get(call["tool"].split("_")[0], [call["tool"].split("_")[0]]))
    scores = []
    for i, t in enumerate(turns):
        score = _match(t["text"], verbs, pw, objs) + (1 if t["writes_requested"] else 0)
        if i == 0:
            score += 0.5  # main turn wins ties and near-ties
        scores.append(score)
    asks = [i for i, t in enumerate(turns) if t["writes_requested"]]
    # a turn that asks for no action ("Why is the count for bay C-14 off?") did not ask for this write, unless it names the
    # action itself (one of its verbs, or two of the tool's object words: "outline it as a board paper for the board agenda")
    named = [i for i, t in enumerate(turns) if _leads(t["text"], verbs) or _names_object(t["text"], objs)]
    cand = sorted(set(asks + named)) or list(range(len(turns)))
    best = max(cand, key=lambda i: (scores[i], -i))
    # the first turn that asks for it with one of its verbs, when the best match only mentions it ("Hold 20% for
    # click-and-collect", then "Actually, release the click-and-collect hold after day three"): doing it when first asked
    # is not early
    if not _leads(turns[best]["text"], verbs):
        best = min([i for i in asks if i < best and scores[i] >= 2.5 and _leads(turns[i]["text"], verbs)], default=best)
    note = None
    if scores[best] < 2.5:
        # a weak match still counts when the turn asks for an action and shares a word with the ask ("Put a hold on the bay
        # until it's recounted" for "Schedule a recount of location DC1-C-14-02"), the first such turn; none: no turn asks
        # for the write (scn-07:69:Q5 only ever asks why), so it is not expected, and doing it is unrequested
        weak = [i for i in asks if scores[i] >= 1.5]
        if not weak:
            return None, f"write {call['tool']} not expected: no turn asks for it (no turn text matches the action)"
        best = min(weak)
        note = f"write {call['tool']} attached to turn {best} on a weak match (the turn asks for an action and shares the ask's words)"
    elif best > 0 and not turns[0]["writes_requested"] or best > 0 and scores[best] - scores[0] >= 2:
        note = f"write {call['tool']} attached to follow-up turn {best} by matching the action to its text"
    held, at = _held(turns[best]["text"], verbs, pw, objs), best
    for j in range(best + 1, len(turns)):
        t = turns[j]
        words = set(_WORD.findall(t["text"].lower()))
        stems = {w[:6] for w in words}
        swapped = re.search(r"\b(?:rather than|instead of)\b", t["text"], re.I) and not verbs & words
        # it names the action: the tool's own verb plus its object or the slice's words, a short "Only send the UK one", or
        # two of the tool's object words ("make the test request for the second trend instead")
        named = _names_object(t["text"], objs)
        names = own & words and (_match(t["text"], set(), pw, objs) >= 0.5 or len(t["text"].split()) <= 12) or named
        if not held and names and _held(t["text"], verbs, pw, objs):  # "Only update it once I've signed off the volume"
            held, at = True, j
        elif held and (t["writes_requested"] or named and "?" not in t["text"]) and not swapped and not HOLD.search(t["text"]) and (names or GO.search(t["text"])):
            return j, f"write {call['tool']} asked for in turn {at} subject to the user's go-ahead, given in turn {j}"
    if not held:
        return best, note
    return -1 - at, (f"write {call['tool']} not expected: turn {at} asks for it only after the user's go-ahead, which no later "
                     f"turn gives, so stopping to ask is right")


_HOLD_WORDS = {"blocked", "block", "hold", "held", "on hold", "payment hold", "on_hold"}


def _describes_held(fact, held: list[dict], expected: list[dict]) -> bool:
    """A fact that only states the effect of a held write (a status or reason it sets, or "blocked"/"payment hold" for a hold),
    which a correct answer that stops to ask cannot state as done. Ids and numbers stay: the reads find them."""
    def norm(v):
        s = str(v).strip().lower().replace("_", " ").replace(",", "")
        try:
            return float(s)
        except ValueError:
            return s
    forms = {norm(f) for f in (fact if isinstance(fact, list) else [fact])}
    vals = lambda ws: {norm(v) for w in ws for v in w["args"].values() if isinstance(v, str) and not bench._idlike(v)
                       and isinstance(norm(v), str)}
    holds = any(w["tool"].split("_")[0] in ("block", "hold") for w in held)
    return bool(forms & (vals(held) - vals(expected))) or holds and bool(forms & {norm(x) for x in _HOLD_WORDS})


# ---------- Rule C review: slice facts the scenario's turns may never ask for ----------

_LABEL_NOISE = set("gbp pct id code no num number per avg average total count name qty value rate amount units unit level "
                   "flag status type is has days day date at week weeks month months year current new old score".split())
_SUFFIX = re.compile(r"(?:ies|es|s|ing|ed|ly|al)$")
UNASKED_COVERAGE = 0.2  # an ask sharing less than this share of its words with the scenario's turns is the slice's own


def _stems(text: str) -> set:
    return {_SUFFIX.sub("", w)[:5] for w in re.findall(r"[a-z]{2,}", text.lower()) if w not in STOP}


def _locate(eng, sid: str, refs: list, facts: list) -> dict:
    """{repr(fact): [(tool, column), ...]}: where each fact sits in the output of these reference calls on engine `eng`
    (column '' for text output)."""
    from .. import args as A
    from ..kinds import RUNNERS
    found = {repr(f): [] for f in facts}
    for r in refs:
        tool = eng.tools.get((sid, r["tool"]))
        if not tool:
            continue
        s, a = eng.systems[sid], eng.args[(sid, r["tool"])]
        try:
            vals, _ = A.prepare(eng.db, s, eng.master, tool, a, bench._shift_args(r.get("args") or {}))
            rows = RUNNERS[tool.kind](eng, s, tool, a, vals)[0]
        except Exception:
            continue
        for f in facts:
            hit = lambda v: bench._has(f, str(v), True) or bench._has(f, str(v))
            if isinstance(rows, str):
                found[repr(f)] += [(r["tool"], "")] if hit(rows) else []
            else:
                found[repr(f)] += [(r["tool"], col) for col in dict.fromkeys(
                    k for row in rows or [] for k, v in dict(row).items() if v is not None and hit(v))]
    return found


def _fact_columns(cases: dict) -> dict:
    """{system: {case ids}} -> {case id: {repr(fact): [(tool, column), ...]}}: where each fact of these cases sits in its
    reference output (column '' for text output). Runs the reference calls like bench --validate: writes go to a throwaway
    state, and a case after a write starts from a clean one."""
    import tempfile
    from pathlib import Path
    from .. import db
    from ..server import Engine
    out, old, tmp = {}, db.STATE, tempfile.TemporaryDirectory()
    try:
        for sid, ids in sorted(cases.items()):
            eng = None
            for c in (c for c in bench.load(sid) if c["id"] in ids):
                if eng is None:
                    db.STATE = Path(tempfile.mkdtemp(dir=tmp.name))
                    eng = Engine([sid])
                out[c["id"]] = _locate(eng, sid, c["ref"], c["facts"])
                if any(t.writes for r in c["ref"] if (t := eng.tools.get((sid, r["tool"])))):
                    eng = None
    finally:
        db.STATE = old
        tmp.cleanup()
    return out


@functools.lru_cache(maxsize=None)
def _read_engine(sid: str):
    from ..server import Engine
    return Engine([sid])


@functools.lru_cache(maxsize=None)
def _read_columns(sid: str, refs_json: str, facts_json: str) -> dict:
    """_locate for a read-only slice, on one cached engine per system (reads change nothing, so engines are shared)."""
    import json
    return _locate(_read_engine(sid), sid, json.loads(refs_json), json.loads(facts_json))


# ---------- which turn of a scenario asks for each fact ----------

_ASK_STOP = _stems("them they there here be been being do does did done have has had will would can could should may might much "
                  "many give tell show let get need want know look see one ones")  # stems that tie any ask to any turn
_SENT_SPLIT = re.compile(r"(?<=[.?!;:])\s+")
_CLAUSE_SPLIT = re.compile(r"(?<=[.?!;:])\s+|,?\s+(?:and|but)\s+(?=(?:what|which|how|where|when|who|whether|why)\b)", re.I)


def _turn_words(t: dict) -> tuple[list, list]:
    """(stems of what each turn asks, text that may name a fact per turn). The Context paragraph of turn 0 only resolves
    names, so it counts for naming a fact but not for matching an ask."""
    q = questions().get(t["question_id"]) or {"text": t["turns"][0]["text"], "followups": [x["text"] for x in t["turns"][1:]]}
    asked = [q["text"]] + list(q["followups"])
    return [_ask_stems(x) for x in asked], [t["turns"][0]["text"]] + asked[1:]


def _ask_stems(text: str) -> set:
    return {w for w in _stems(text) if w not in _ASK_STOP}


def _ask_turns(asks: list, tstems: list) -> list[set]:
    """Per ask: the turn(s) whose words cover the largest share of it (at least UNASKED_COVERAGE), plus any turn most of
    whose words (two or more) the ask uses ("Air rates out of Dhaka at the moment?" in "current air freight rates per kg ...
    from Dhaka (DAC) and from Ho Chi Minh City ...")."""
    out = []
    for a in asks:
        st = _ask_stems(a)
        sc = [len(st & ts) / len(st) for ts in tstems]
        top = max(sc)
        out.append(({i for i, x in enumerate(sc) if x == top} if top >= UNASKED_COVERAGE else set())
                   | ({0} if sc[0] >= UNASKED_COVERAGE else set())
                   | {i for i, ts in enumerate(tstems) if len(st & ts) >= 2 and len(st & ts) / len(ts) >= 0.5})
    return out


def fact_turns(t: dict) -> dict:
    """{case id: {repr(fact): sorted turn indices, or None when no turn can be told}} for the read slices of scenario `t`:
    which of its turns ask for each fact. A trap that keeps only some turns of a scenario requires only the facts those turns
    ask for (Rule C): "What would protect them at least cost?" (turn 3) asks for the cheapest protection's cost, turn 0
    ("What are our highest-loss products?") does not.

    The slice prompt is cut into asks twice, into sentences and into clauses ("..., and what would be the cheapest way to
    protect it?"), and each ask goes to its turns (_ask_turns). A fact belongs to the asks that name it or use its words or
    its reference columns' words (cost_per_pound_prevented -> cost, pound), else those using its tool's words; failing
    that, to the turns that use those words, else to every turn the slice's asks go to. The two cuts often disagree (a
    clause "and what materials are they using?" reads like the main question, its sentence is about competitors' ranges):
    the turns both agree on win, else either. A turn that names the fact's value asks for it too. A case can pin facts to
    turns with `turn_facts` ({turn: [facts]}) where the words cannot tell (a December row is "last year's peak").
    Lexical: None (keep the fact) when nothing matches. Runs the slices' reference calls (cached per system)."""
    import json
    key = json.dumps([t.get("question_id"), [x["text"] for x in t["turns"]],
                      [[s["case_id"], s["prompt"], s["facts"], s["ref"], s.get("turn_facts")] for s in t["reference"]["slices"]]],
                     sort_keys=True, default=str)
    if key not in _FACT_TURNS:
        _FACT_TURNS[key] = _fact_turns(t)
    return copy.deepcopy(_FACT_TURNS[key])


_FACT_TURNS: dict = {}


def _fact_turns(t: dict) -> dict:
    import json
    tstems, named = _turn_words(t)
    words = lambda ws: _stems(" ".join(w for w in ws if w not in _LABEL_NOISE))
    out = {}
    for s in t["reference"]["slices"]:
        if not s["facts"] or any(_is_write(s["system"], r["tool"]) for r in s["ref"]):
            continue
        cuts = []
        for rx in (_SENT_SPLIT, _CLAUSE_SPLIT):
            asks = [a for a in rx.split(s["prompt"]) if a and _ask_stems(a)]
            cuts.append((asks, _ask_turns(asks, tstems)))
        cols = _read_columns(s["system"], json.dumps(s["ref"], sort_keys=True), json.dumps(s["facts"]))
        pinned: dict = {}
        for k, fs in (s.get("turn_facts") or {}).items():
            for f in fs:
                pinned.setdefault(repr(f), set()).add(int(k))
        m = out[s["case_id"]] = {}
        for f in s["facts"]:
            if repr(f) in pinned:
                m[repr(f)] = sorted(pinned[repr(f)])
                continue
            forms = f if isinstance(f, list) else [f]
            locs = cols.get(repr(f), [])
            lab = set().union(words([w for v in forms if not bench._idlike(v) and not re.fullmatch(r"-?[\d.,]+", str(v))
                                     for w in re.split(r"[\s_]+", str(v).lower())]),
                              *(words(c.split("_")) for _, c in locs if c))
            tool = set().union(set(), *(words(tl.split("_")[1:]) for tl, _ in locs))
            views = []
            for asks, aturns in cuts:
                linked = ([i for i, a in enumerate(asks) if _ask_stems(a) & lab or any(bench._has(v, a) for v in forms)]
                          or [i for i, a in enumerate(asks) if _ask_stems(a) & tool])
                views.append(set().union(set(), *(aturns[i] for i in linked))
                             or {i for i, ts in enumerate(tstems) if ts & (lab | tool)} or set().union(*aturns))
            turns = (views[0] & views[1]) or (views[0] | views[1])
            turns |= {i for i, x in enumerate(named) if any(not re.fullmatch(r"-?[\d.,]+", str(v)) and bench._has(v, x) for v in forms)}
            m[repr(f)] = sorted(turns) or None
    return out


def unasked_facts(qids=None) -> list[dict]:
    """Facts a scenario would require only because its slice prompt asks for them (Rule C). A scenario takes the union of its
    slices' facts, but a slice prompt often asks more than the persona question ("Which single write-off was the highest
    value?", "on which till?"). A fact is flagged when its value is not named in any turn, neither its reference columns'
    words (cost_per_unit_pence -> cost) nor its tool's object words occur in the turns, and every sentence of the slice
    prompt that uses those column words is the slice's own (shares under UNASKED_COVERAGE of its words with the turns).
    Lexical, so a review list rather than a filter: a flagged case gets an explicit `scenario_facts` that decides what the
    scenario asks, and tests/test_eval_recipe.py keeps this list empty. Slices with an explicit `scenario_facts` and held
    write slices are skipped. Runs the reference calls of the slices that have an ask of their own (about a minute)."""
    split = lambda p: [a for a in re.split(r"(?<=[.?!;:])\s+", p) if a.strip()]
    qs, out, todo = questions(), [], []
    for t in _bank():
        if t["kind"] != "scenario" or qids is not None and t["question_id"] not in qids:
            continue
        q = qs[t["question_id"]]
        turns = " ".join([q["text"]] + q["followups"])
        ts = _stems(turns)
        for s in t["reference"]["slices"]:
            own = [a for a in split(s["prompt"]) if (st := _stems(a)) and len(st & ts) / len(st) < UNASKED_COVERAGE]
            if own and s["facts"] and "dropped_facts" not in s and not s.get("held") and not s.get("unasked"):
                todo.append((t["question_id"], s, turns, own))
    cases: dict = {}
    for _, s, _, _ in todo:
        cases.setdefault(s["system"], set()).add(s["case_id"])
    cols = _fact_columns(cases)
    for qid, s, turns, own in todo:
        ts, shared = _stems(turns), [a for a in split(s["prompt"]) if a not in own]
        for f in s["facts"]:
            if any(not re.fullmatch(r"-?[\d.,]+", str(x)) and bench._has(x, turns) for x in (f if isinstance(f, list) else [f])):
                continue  # a turn names it
            locs = cols.get(s["case_id"], {}).get(repr(f), [])
            words = lambda ws: _stems(" ".join(w for w in ws if w not in _LABEL_NOISE))
            lab = set().union(set(), *(words(c.split("_")) for _, c in locs if c))
            tool = set().union(set(), *(words(t.split("_")[1:]) for t, _ in locs))
            asks = [a for a in own if _stems(a) & lab]
            if asks and not (lab | tool) & ts and not any(_stems(a) & lab for a in shared):
                out.append({"question_id": qid, "case_id": s["case_id"], "fact": f,
                            "columns": sorted({c for _, c in locs if c}), "asked_by": asks})
    return out


def _scenario(qid: str, q: dict, slices: list[dict]) -> dict:
    given = " ".join(s["scenario_context"] for s in slices if s.get("scenario_context"))
    slices = [{**{k: v for k, v in s.items() if k not in ("scenario_context", "scenario_facts")},
               "facts": s["scenario_facts"], "dropped_facts": [f for f in s["facts"] if f not in s["scenario_facts"]]}
              if "scenario_facts" in s else {k: v for k, v in s.items() if k != "scenario_context"} for s in slices]
    ctx = context_paragraph(q["text"], slices, q["tags"].get("type", ""))
    ctx = (ctx + " " + given if ctx else "Context: " + given) if given else ctx
    main = q["text"] + (("\n\n" + ctx) if ctx else "")
    turns = [turn(main, "question")] + [turn(f, "followup") for f in q["followups"]]
    turns[0]["writes_requested"] = writes_requested(q["text"])
    asked = [{**turns[0], "text": q["text"]}] + turns[1:]  # what the user asks; the Context paragraph only resolves names
    expected, held, unasked, notes, out = [], [], [], [s["notes"] for s in slices if s["notes"]], []
    for s in slices:
        mine = []
        for r in s["ref"]:
            if _is_write(s["system"], r["tool"]):
                t, note = _turn_for_write(r, s, asked)
                if t is None:
                    unasked.append({"tool": r["tool"], "args": r["args"], "system": s["system"]}), mine.append(None)
                else:
                    w = {"tool": r["tool"], "args": r["args"], "turn": t if t >= 0 else -1 - t, "system": s["system"]}
                    (expected if t >= 0 else held).append(w), mine.append(t >= 0)
                if note and note not in notes:
                    notes.append(note)
        if mine and not any(mine) and all(_is_write(s["system"], r["tool"]) for r in s["ref"]):
            # a write slice nobody approves (or asks for): its facts describe the write, not an answer
            s = {**s, "facts": [], **({"held": True} if False in mine else {"unasked": True})}
        elif mine and not all(mine):
            s = {**s, "facts": [f for f in s["facts"] if not _describes_held(f, held + unasked, expected)]}
        out.append(s)
    t = _task(f"scn-{qid}", "scenario", qid, q, turns, out, expected, notes)
    t["writes"]["held"] = held  # asked for subject to a go-ahead that never comes: doing it is acting before approval
    t["writes"]["unasked"] = unasked  # in a slice prompt but asked for by no turn of the scenario: doing it is unrequested
    return t


def _slice(qid: str, q: dict, s: dict) -> dict:
    s = {k: v for k, v in s.items() if k not in ("scenario_context", "scenario_facts", "inputs_from", "turn_facts")}
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
         "writes": {"expected": expected, "held": [], "unasked": [], "write_tools_loaded": []}, "trap": None}
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
        t.setdefault("writes", {}), t["writes"].setdefault("expected", []), t["writes"].setdefault("write_tools_loaded", []), t["writes"].setdefault("held", [])
        t.setdefault("servers", {}), t["servers"].setdefault("required", sorted({s["system"] for s in t["reference"]["slices"]}))
        t["servers"].setdefault("distractors", []), t["servers"].setdefault("loaded", [])
        t.setdefault("tool_budget", {})
        t["features"] = features(t)
        t["strata"] = strata(t)
        out.append(t)
    return out
