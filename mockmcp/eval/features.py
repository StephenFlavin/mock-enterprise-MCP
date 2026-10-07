"""Task features, strata presets and the mini filter language used by recipes.

    features(task) -> dict          measurable properties of a task
    PRESETS                         name -> predicate(features) -> bool   (overridable per recipe: presets: {name: "expr"})
    compile_filter(expr, presets)   -> predicate(features)
    strata(task, presets)           -> names of the presets the task matches

Filter language: terms joined by `&` (and), alternatives by ` or `; a term is `field<op>value` with op in
>= <= > < = != (a value may list alternatives: `domain=02|07`), a bare feature or preset name (`write`, `chained`),
or `!name`. Examples: `systems>=3`, `kind=slice&domain=02`, `complexity=complex or calls>=6`.
"""
import operator
import re

from .. import bench

OPS = {">=": operator.ge, "<=": operator.le, ">": operator.gt, "<": operator.lt, "=": operator.eq, "!=": operator.ne}
_TERM = re.compile(r"^\s*([A-Za-z_]\w*)\s*(>=|<=|!=|>|<|=)\s*(.+?)\s*$")
_WORDS = re.compile(r"\S+")


def _words(text: str) -> int:
    return len(_WORDS.findall(text))


def _chained(task: dict) -> bool:
    """A reference arg is an id that no turn mentions, so the model must find it in another call's output."""
    text = " ".join(t["text"] for t in task["turns"]).lower()
    for s in task["reference"]["slices"]:
        for r in s["ref"]:
            for v in r.get("args", {}).values():
                for x in (v if isinstance(v, list) else str(v).split(",")):
                    x = str(x).strip()
                    if bench._idlike(x) and x.lower() not in text:
                        return True
    return False


def features(task: dict) -> dict:
    sl = task["reference"]["slices"]
    tags, turns = task.get("question_tags") or {}, task["turns"]
    systems = task["servers"]["required"] or sorted({s["system"] for s in sl})
    return {
        "kind": task["kind"], "systems": len(systems), "system_ids": list(systems),
        "calls": sum(len(s["ref"]) for s in sl), "writes": len(task["writes"]["expected"]), "chained": _chained(task),
        "prompt_words": _words(turns[0]["text"]) if turns else 0, "total_words": sum(_words(t["text"]) for t in turns),
        "facts": len(task["reference"]["facts"]), "followups": max(len(turns) - 1, 0),
        "approval_needed": any(t["approval_needed"] for t in turns),
        "persona": ":".join(filter(None, [task["persona"].get("file"), task["persona"].get("no")])),
        "domain": task["persona"].get("file", ""), "question": task.get("question_id") or "",
        "type": tags.get("type", ""), "specificity": tags.get("specificity", ""), "scope": tags.get("scope", ""),
        "complexity": tags.get("complexity", ""), "trap_type": (task.get("trap") or {}).get("type", ""),
    }


PRESETS = {
    "simple": lambda f: f["systems"] == 1 and f["calls"] == 1 and f["writes"] == 0 and f["followups"] == 0,
    "short": lambda f: f["prompt_words"] <= 25,
    "long": lambda f: f["total_words"] >= 60 or f["followups"] >= 2,
    "multi_system": lambda f: f["systems"] >= 3,
    "complex": lambda f: (f["calls"] >= 4 or f["chained"]) and (f["systems"] >= 2 or f["writes"] >= 1),
    "write": lambda f: f["writes"] >= 1,
    "followups": lambda f: f["followups"] >= 1,
    "trap": lambda f: f["kind"] == "trap",
}


def _val(raw: str, have):
    if isinstance(have, bool):
        return raw.strip().lower() in ("1", "true", "yes", "y")
    if isinstance(have, (int, float)):
        return float(raw)
    return raw.strip().lower()


def _term(term: str, presets: dict):
    term = term.strip()
    if m := _TERM.match(term):
        field, op, raw = m.groups()
        alts = [a for a in raw.split("|")]

        def pred(f):
            if field == "system":
                have = [s.lower() for s in f["system_ids"]]
                hit = any(a.strip().lower() in have for a in alts)
                return hit if op == "=" else not hit
            if field not in f:
                raise KeyError(f"unknown feature '{field}' in filter term '{term}' (known: {sorted(f)})")
            have = f[field]
            key = have.lower() if isinstance(have, str) else have
            if op == "!=":
                return not any(key == _val(a, have) for a in alts)
            return any(OPS[op](key, _val(a, have)) for a in alts)
        return pred
    neg = term.startswith("!")
    name = term.lstrip("!").strip()

    def pred(f):
        if name in presets:
            v = presets[name](f)
        elif name in f:
            v = bool(f[name])
        else:
            raise KeyError(f"unknown preset or feature '{name}' (presets: {sorted(presets)})")
        return not v if neg else v
    return pred


def compile_filter(expr, presets: dict | None = None):
    """Predicate over a features dict for a filter expression, preset name, or callable (returned unchanged)."""
    if callable(expr):
        return expr
    presets = presets if presets is not None else PRESETS
    alts = [[_term(t, presets) for t in alt.split("&")] for alt in re.split(r"\s+or\s+", str(expr).strip())]
    return lambda f: any(all(p(f) for p in conj) for conj in alts)


def merged_presets(overrides: dict | None = None) -> dict:
    """Default PRESETS with recipe overrides ({name: 'filter expression'}) applied."""
    out = dict(PRESETS)
    for name, expr in (overrides or {}).items():
        out[name] = (lambda e: (lambda f: compile_filter(e, out)(f)))(expr)
    return out


def strata(task: dict, presets: dict | None = None) -> list[str]:
    f = task["features"] if task.get("features") else features(task)
    presets = presets or PRESETS
    return [n for n, p in presets.items() if p(f)]
