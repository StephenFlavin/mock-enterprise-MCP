"""`mockmcp bench`: can one server, alone, answer its slice of a persona question?

A case (bench/cases/<id>.yaml) is one question slice for one server:
    - id: cmms-01:10:Q1           # unique
      question: "01:10:Q1"        # catalogue question it comes from
      prompt: "..."               # the user's ask, with ids already resolved (no tool names)
      ref:                        # the calls a good answer makes; id-like args must match
        - {tool: list_unplanned_stoppages, args: {asset_id: AST-DC2-SHT-03, date_from: -40d}}
      facts: ["Bearing failure", [920, "£920"]]   # must appear in the answer (a list = any one of); validated against ref output

`bench --validate` runs the ref calls and checks every fact is in their output (no model involved).
`bench` runs a model (default haiku) through headless Claude Code with ONLY that server over stdio, then grades:
    tools     every ref tool was called
    args      ...with the same id-like argument values (right SKU, right site)
    grounded  every id in the answer appears in the prompt or in a tool result (no invented ids)
    facts     every fact appears in the answer
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import yaml

from . import db, spec
from .spec import ROOT, WORLD

CASES = ROOT / "bench" / "cases"
RESULTS = ROOT / "bench" / "results"
ID_RX = re.compile(r"\b[A-Z][A-Z0-9]{1,5}(?:-[A-Z0-9]+)*-\d[\w-]*\b|\b[A-Z]{1,3}\d{2,}\b")
DATE_IN_PROMPT = re.compile(r"\b20\d\d-\d\d-\d\d\b|\b\d{1,2}(st|nd|rd|th)? (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b"
                            r"|\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(st|nd|rd|th)?\b")
NUM_RX = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?")
SYSTEM = ("You are an assistant at {company}. Today is {today}. You can only use the tools provided. "
          "Answer from tool results only; if the tools cannot answer part of the request, say so plainly.")


def _norm(s: str, table: bool = False) -> str:
    """table=True for tool output (CSV: every comma separates fields); prose drops thousands separators."""
    s = str(s).replace(",", " ") if table else re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", str(s))
    s = s.replace("£", "").lower()
    return re.sub(r"[_*]+", " ", s)


def _forms(fact) -> list[str]:
    """A fact and its equivalent spellings: an ISO date also matches '10 November', 'Nov 10', '10/11/2026'."""
    f = str(fact)
    if m := re.fullmatch(r"(\d{4})-(\d\d)-(\d\d)", f):
        # facts are written in data time; the data moves to today in whole weeks at runtime
        d = date(*map(int, m.groups())) + timedelta(days=spec.SHIFT_DAYS)
        f = d.isoformat()
        return [f, f"{d.day} {d:%B}", f"{d.day} {d:%b}", f"{d:%B} {d.day}", f"{d:%b} {d.day}", f"{d.day}/{d.month}/{d.year}",
                f"{d.day:02d}/{d.month:02d}/{d.year}"]
    return [f]


SCALE = {"k": 1e3, "thousand": 1e3, "m": 1e6, "mn": 1e6, "million": 1e6, "bn": 1e9, "billion": 1e9}


def _numbers(t: str) -> list[tuple[float, float]]:
    """(value, rounding tolerance) for each number; '22.5m' -> (22500000, 50000), '1,270' was already de-comma'd."""
    out = []
    for m in re.finditer(r"(?<![\w.])(-?\d+(?:\.(\d+))?)\s?(k|thousand|mn|m|million|bn|billion)?\b", t):
        mult = SCALE.get(m.group(3) or "", 1)
        dp = len(m.group(2) or "")
        out.append((float(m.group(1)) * mult, 0.5 * 10 ** -dp * mult if mult > 1 else 0))
    return out


def _has(fact, text: str, table: bool = False) -> bool:
    opts = [x for o in (fact if isinstance(fact, list) else [fact]) for x in _forms(o)]
    t = _norm(text, table)
    nums = None
    for o in opts:
        o = _norm(o)
        if not re.fullmatch(r"-?\d+(\.\d+)?", o):
            if o in t:
                return True
        else:  # numbers match within the fact's own rounding or 0.5%
            nums = nums if nums is not None else _numbers(t)
            f, dp = float(o), len(o.split(".")[1]) if "." in o else 0
            tol = max(0.5 * 10 ** -dp, abs(f) * 0.005)
            if any(abs(abs(n) - abs(f)) <= max(tol, ntol) for n, ntol in nums):
                return True
    return False


def load(sid: str) -> list[dict]:
    f = CASES / f"{sid}.yaml"
    return yaml.safe_load(f.read_text()) or [] if f.exists() else []


def _idlike(v) -> bool:
    return isinstance(v, str) and bool(ID_RX.fullmatch(v.strip()))


# ---------- validation (no model) ----------

def validate(sid: str, days: int = 7) -> list[str]:
    """Validate as if today were each of the next `days` days: data moves in whole weeks but 'today' moves daily,
    so a fact that depends on where a rolling window ends ('last 30 days') must hold on every weekday."""
    real = date.fromisoformat(WORLD["as_of"])
    out: list[str] = []
    try:
        for off in range(days):
            spec.set_today(real + timedelta(days=off))
            tag = "" if off == 0 else f" [only when today is {real + timedelta(days=off):%a} {real + timedelta(days=off)}]"
            out += [x + tag for x in _validate_once(sid) if x not in out and not any(o.startswith(x) for o in out)]
    finally:
        spec.set_today(real)
    return out


def _shift_args(args: dict) -> dict:
    """Ref args are written in data time like facts: move ISO dates with the data."""
    def mv(v):
        if isinstance(v, str) and re.fullmatch(r"\d{4}-\d\d-\d\d", v.strip()):
            return (date.fromisoformat(v.strip()) + timedelta(days=spec.SHIFT_DAYS)).isoformat()
        return [mv(x) for x in v] if isinstance(v, list) else v
    return {k: mv(v) for k, v in args.items()}


def _validate_once(sid: str) -> list[str]:
    from .server import Engine
    p, seen = [], set()
    with tempfile.TemporaryDirectory() as tmp:
        old, db.STATE = db.STATE, Path(tmp)
        try:
            eng = Engine([sid])
            names = {t.name for t in eng.systems[sid].tools}
            for c in load(sid):
                cid = c.get("id", "?")
                if cid in seen:
                    p.append(f"{cid}: duplicate id")
                seen.add(cid)
                if not c.get("ref") or not c.get("facts") or not c.get("prompt"):
                    p.append(f"{cid}: needs prompt, ref and facts")
                    continue
                if DATE_IN_PROMPT.search(c["prompt"]):
                    p.append(f"{cid}: prompt has an absolute date; use relative periods (last 40 days, next week) since data moves with today")
                if any(n in c["prompt"] for n in names):
                    p.append(f"{cid}: prompt names a tool; ask in the user's words")
                out = ""
                for r in c["ref"]:
                    if r["tool"] not in names:
                        p.append(f"{cid}: ref tool {r['tool']} is not in {sid}")
                        continue
                    text, err = eng.call(sid, r["tool"], _shift_args(r.get("args") or {}))
                    if err:
                        p.append(f"{cid}: ref {r['tool']} errored: {text[:150]}")
                    out += "\n" + text
                p += [f"{cid}: fact {f!r} not in ref output" for f in c["facts"] if not (_has(f, out, table=True) or _has(f, out))]
        finally:
            db.STATE = old
    return p


# ---------- model run ----------

def _transcript(stream: str):
    """(calls [(tool, input, output)], answer, meta) from claude stream-json output."""
    calls, pending, answer, meta = [], {}, "", {}
    for line in stream.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        msg = ev.get("message") or {}
        for part in msg.get("content") or [] if isinstance(msg.get("content"), list) else []:
            if part.get("type") == "tool_use":
                pending[part["id"]] = [part["name"].split("__")[-1], part.get("input") or {}, ""]
                calls.append(pending[part["id"]])
            elif part.get("type") == "tool_result" and part.get("tool_use_id") in pending:
                content = part.get("content")
                if isinstance(content, list):
                    content = "\n".join(x.get("text", "") for x in content if isinstance(x, dict))
                pending[part["tool_use_id"]][2] = str(content or "")
        if ev.get("type") == "result":
            answer = ev.get("result") or ""
            meta = {k: ev.get(k) for k in ("num_turns", "total_cost_usd", "is_error")}
            meta["models"] = list((ev.get("modelUsage") or {}).keys())
    return calls, answer, meta


def _argset(v) -> frozenset:
    """An argument value as a set of lower-case items, so CAR-003, ["car-003"] and "CAR-003, CAR-004" compare sensibly."""
    items = v if isinstance(v, list) else re.split(r"\s*[,;]\s*", str(v))
    return frozenset(str(x).strip().lower() for x in items if str(x).strip())


def grade(case: dict, calls, answer: str) -> dict:
    called = {}
    for name, args, _ in calls:
        called.setdefault(name, []).append({k: _argset(v) for k, v in args.items()})
    miss_tools = [r["tool"] for r in case["ref"] if r["tool"] not in called]
    bad_args = []
    for r in case["ref"]:
        want = {k: _argset(v) for k, v in (r.get("args") or {}).items()
                if _idlike(v) or (isinstance(v, list) and v and all(_idlike(x) for x in v))}
        if r["tool"] in called and want and not any(all(a.get(k) == v for k, v in want.items()) for a in called[r["tool"]]):
            bad_args.append(f"{r['tool']} {dict((k, sorted(v)) for k, v in want.items())}")
    seen = _norm(case["prompt"]) + "\n" + _norm("\n".join(o for *_, o in calls), table=True)
    invented = sorted({i for i in ID_RX.findall(answer) if i.lower() not in seen})
    nums = [n for n in NUM_RX.findall(answer) if len(re.sub(r"\D", "", n)) >= 3]
    loose = [n for n in nums if _norm(n).lstrip("-") not in seen]
    missing = [f for f in case["facts"] if not _has(f, answer)]
    checks = {"tools": not miss_tools, "args": not bad_args, "grounded": not invented, "facts": not missing}
    return {"pass": all(checks.values()), "checks": checks, "missing_tools": miss_tools, "bad_args": bad_args,
            "invented_ids": invented, "missing_facts": missing,
            "numbers_not_in_tool_output": f"{len(loose)}/{len(nums)}"}


def run_case(sid: str, case: dict, model: str, timeout: int = 300) -> dict:
    work = Path(tempfile.mkdtemp(prefix="bench-"))
    try:
        cfg = {"mcpServers": {sid: {"type": "stdio", "command": sys.executable, "args": ["-m", "mockmcp", "stdio", sid],
                                    "env": {"MOCKMCP_STATE": str(work / "state"), "PYTHONPATH": str(ROOT)}}}}
        (work / "mcp.json").write_text(json.dumps(cfg))
        cmd = ["claude", "-p", case["prompt"], "--model", model, "--mcp-config", str(work / "mcp.json"),
               "--strict-mcp-config", "--tools", "", "--allowedTools", f"mcp__{sid}", "--setting-sources", "",
               "--output-format", "stream-json", "--verbose", "--max-turns", "15",
               "--append-system-prompt", SYSTEM.format(company=WORLD["company"], today=date.today().isoformat())]
        try:
            out = subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=timeout).stdout
        except subprocess.TimeoutExpired as e:
            out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        calls, answer, meta = _transcript(out)
        res = grade(case, calls, answer) if answer else {"pass": False, "checks": {}, "error": "no answer (timeout or crash)"}
        return {"id": case["id"], "system": sid, **res, **meta,
                "calls": [{"tool": n, "args": a} for n, a, _ in calls], "answer": answer}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def run(sids: list[str], model: str = "haiku", workers: int = 6, only: str | None = None) -> Path:
    jobs = [(s, c) for s in sids for c in load(s) if not only or only in c["id"]]
    stamp = f"{date.today().isoformat()}-{model}-" + ("all" if len(sids) > 3 else "+".join(sids))  # parallel runs don't collide
    out = RESULTS / f"{stamp}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    results = []
    with ThreadPoolExecutor(workers) as ex, open(out, "w") as fh:
        for r in ex.map(lambda j: run_case(j[0], j[1], model), jobs):
            results.append(r)
            fh.write(json.dumps(r) + "\n")
            fh.flush()
            print(f"{'PASS' if r['pass'] else 'FAIL'}  {r['id']}  {' '.join(k for k, v in r.get('checks', {}).items() if not v) or r.get('error', '')}",
                  flush=True)
    (RESULTS / f"{stamp}.md").write_text(report(results, model))
    print(report(results, model))
    return out


def report(results: list[dict], model: str) -> str:
    lines = [f"# Bench: {model}, {date.today().isoformat()}", "",
             f"**{sum(r['pass'] for r in results)}/{len(results)} slices pass.** "
             f"Cost ${sum(r.get('total_cost_usd') or 0 for r in results):.2f}.", "",
             "| system | pass | tools | args | grounded | facts |", "|---|---|---|---|---|---|"]
    for sid in sorted({r["system"] for r in results}):
        rs = [r for r in results if r["system"] == sid]
        col = lambda k: f"{sum(r.get('checks', {}).get(k, False) for r in rs)}/{len(rs)}"
        lines.append(f"| {sid} | {sum(r['pass'] for r in rs)}/{len(rs)} | {col('tools')} | {col('args')} | {col('grounded')} | {col('facts')} |")
    fails = [r for r in results if not r["pass"]]
    if fails:
        lines += ["", "## Failures", ""]
        for r in fails:
            why = r.get("error") or "; ".join(x for x in [
                r.get("missing_tools") and f"missing tools {r['missing_tools']}",
                r.get("bad_args") and f"wrong args {r['bad_args']}",
                r.get("invented_ids") and f"invented ids {r['invented_ids']}",
                r.get("missing_facts") and f"missing facts {r['missing_facts']}"] if x)
            lines.append(f"- `{r['id']}`: {why}. Called: {', '.join(c['tool'] for c in r['calls']) or 'nothing'}")
    return "\n".join(lines) + "\n"


def coverage() -> dict[str, tuple[set, set]]:
    """system -> (questions that use it, questions with a case). The data-exists bar: every slice has a validated case."""
    need: dict[str, set] = {}
    for r in _catalog_rows():
        for q in r["used_by"].split(";"):
            if q:
                need.setdefault(r["system"], set()).add(q)
    return {sid: (qs, {str(c.get("question")) for c in load(sid)} & qs) for sid, qs in need.items()}


def _catalog_rows():
    import csv
    with open(ROOT / "catalog" / "tools.csv", newline="") as fh:
        return list(csv.DictReader(fh))

