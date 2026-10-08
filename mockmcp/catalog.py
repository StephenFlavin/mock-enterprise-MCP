"""Build catalog/tools.csv from the persona docs and print per-system build briefs."""
import csv
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs/assets/personas"
CAT = ROOT / "catalog"

EXTERNAL = {"Web", "Web (public search/fetch)", "Code Execution", "Code Execution (analysis sandbox, charts)",
            "Email & Calendar", "Collaboration & Messaging (Slack/Teams)", "Collaboration & Messaging"}
ALIASES = {"PLM": "Product Lifecycle Management (PLM)"}


def systems() -> dict[str, dict]:
    return {r["id"]: r for r in csv.DictReader(open(CAT / "systems.csv"))}


def _name_to_id() -> dict[str, str]:
    return {r["name"]: i for i, r in systems().items()}


def _questions() -> dict[tuple, dict]:
    """(file_no, persona_no, 'Q1') -> {persona, text, followups}"""
    out = {}
    for f in sorted(DOCS.glob("questions-0*.md")):
        fno, persona, pname, cur = f.name[10:12], None, None, None
        for line in f.read_text().splitlines():
            if m := re.match(r"## (\d+)\. (.+?)(?: \(AI score \d\))?$", line):
                persona, pname = m.group(1), m.group(2)
            elif m := re.match(r"\*\*(Q\d+)\b[^*]*\*\*\s*(.*)", line):
                cur = out[(fno, persona, m.group(1))] = {"persona": pname, "text": m.group(2), "followups": []}
            elif cur and line.startswith("- ↳"):
                cur["followups"].append(line[3:].strip())
    return out


def _rows():
    """Yield question rows from the tools files: (file_no, persona_no, persona, q, abridged, systems, tools)."""
    for f in sorted(DOCS.glob("tools-0*.md")):
        fno, persona, pname = f.name[6:8], None, None
        for line in f.read_text().split("## Tool catalogue")[0].splitlines():
            if m := re.match(r"## (\d+)\. (.+)$", line):
                persona, pname = m.group(1), m.group(2)
            elif line.startswith("| Q"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                yield fno, persona, pname, cells[0], cells[1], cells[2], re.findall(r"`([a-z0-9_]+)`", cells[3])


def build() -> list[dict]:
    """Return catalogue rows: one per (tool, system). Tools catalogued under several systems appear in each."""
    n2i = _name_to_id()
    entries: dict[tuple, dict] = {}
    for f in sorted(DOCS.glob("tools-0*.md")):
        for line in f.read_text().split("## Tool catalogue")[1].splitlines():
            m = re.match(r"\|\s*`([a-z0-9_]+)`\s*\|\s*([^|]+?)\s*\|\s*([RW])\s*\|\s*(.*?)\s*\|", line)
            if not m:
                continue
            tool, sysname, rw, desc = m.groups()
            sysname = ALIASES.get(sysname, sysname)
            if sysname in EXTERNAL:
                continue
            entries.setdefault((tool, n2i[sysname]), {"tool": tool, "system": n2i[sysname], "rw": rw, "desc": desc})
    for r in csv.DictReader(open(CAT / "overrides.csv")):
        entries.setdefault((r["tool"], r["system"]), {k: r[k] for k in ("tool", "system", "rw", "desc")})
    used = defaultdict(set)
    for fno, pno, _, q, *_rest, tools in _rows():
        for t in tools:
            used[t].add(f"{fno}:{pno}:{q}")
    out = sorted(entries.values(), key=lambda e: (e["system"], e["tool"]))
    for e in out:
        e["used_by"] = ";".join(sorted(used[e["tool"]]))
    return out


def write():
    rows = build()
    with open(CAT / "tools.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["tool", "system", "rw", "desc", "used_by"])
        w.writeheader()
        w.writerows(rows)
    print(f"catalog/tools.csv: {len(rows)} tool entries across {len({r['system'] for r in rows})} systems")


def load() -> list[dict]:
    return list(csv.DictReader(open(CAT / "tools.csv")))


def tools_for(system_id: str) -> list[dict]:
    return [r for r in load() if r["system"] == system_id]


def brief(system_id: str) -> str:
    """Everything a builder needs about one system: its tools and every question row that uses them."""
    sysrow = systems()[system_id]
    mine = tools_for(system_id)
    names = {t["tool"] for t in mine}
    owner = defaultdict(list)
    for r in load():
        owner[r["tool"]].append(r["system"])
    qs = _questions()
    lines = [f"# Brief: {system_id} — {sysrow['name']}", "", f"## Tools to implement ({len(mine)})", "",
             "| tool | R/W | catalogue description |", "|---|---|---|"]
    lines += [f"| `{t['tool']}` | {t['rw']} | {t['desc']} |" for t in mine]
    lines += ["", "## Question rows that use these tools", "",
              "Each row shows the full question and follow-ups, then every tool the agent is expected to call, "
              "with its owning system. Tools marked ★ are yours. Seed data so that ★ tools return what the "
              "question needs (the specific entities, numbers and anomalies it mentions).", ""]
    for fno, pno, pname, q, abridged, sysnames, tools in _rows():
        if not names & set(tools):
            continue
        full = qs.get((fno, pno, q))
        lines.append(f"### {fno}:{pno}:{q} — {pname}")
        lines.append(full["text"] if full else abridged)
        for fu in (full or {}).get("followups", []):
            lines.append(f"  - ↳ {fu}")
        calls = [f"{'★' if t in names else ' '}{t} [{','.join(owner.get(t, ['external']))}]" for t in tools]
        lines.append("Calls: " + ", ".join(calls))
        lines.append("")
    return "\n".join(lines)


def profile(file_no: str, persona_no: str) -> list[str]:
    """System ids used by one persona's question rows."""
    owner = defaultdict(list)
    for r in load():
        owner[r["tool"]].append(r["system"])
    ids = set()
    for fno, pno, *_r, tools in _rows():
        if fno == file_no.zfill(2) and pno == persona_no:
            for t in tools:
                ids.update(owner.get(t, []))
    return sorted(ids)
