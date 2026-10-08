"""Deterministic evidence about the figures in an answer, for the judge payload (grade.grounding_of) and the checks.

derive():      is a figure in no tool result a restatement (rounding, units, k/m scale) or a derivation (sums of rows that
               share a label, differences, ratios, percentages, means, group-by means, annualisation, products) of tool
               results or of the answer's own figures? Returns how, with the operands, or None.
recompute():   figures the answer derives from numbers it lists (Total rows, stated sums and means, "X more than Y" over its
               own table, sums over the records it names) that are WRONG beyond rounding (Rule A).
is_template_id(), date_year(), scale_forms(), external_claims(), fact_labels() / fact_matches(): helpers for checks.

Operands must be plausible: on the same answer row, sentence or paragraph, or on tool-result rows that share a label with
the figure's context; chance matches among hundreds of unrelated numbers do not count. Eval-only: bench.py keeps its own
matcher for case validation."""
import csv
import itertools
import re
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache

from .. import bench

SCALE = {"k": 1e3, "thousand": 1e3, "m": 1e6, "mn": 1e6, "million": 1e6, "bn": 1e9, "billion": 1e9}
# a figure in prose: currency, sign, thousands-grouped or plain digits, an attached k/m/bn (or a spaced word), percent
NUM = re.compile(r"(?<![\w.])(?<![A-Za-z]-)(?P<cur>[£$€])?(?P<neg>[-−](?=[£$€]?\d))?(?P<cur2>[£$€])?"
                 r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?(?!\d)|\d+(?:\.\d+)?)"
                 r"(?:(?P<suf>k|m|bn|mn)\b|\s(?P<word>thousand|million|billion)\b)?(?P<pct>\s?%)?")
ISO_DATE = re.compile(r"\b\d{4}-\d\d(?:-\d\d)?(?:[ T]\d\d:\d\d(?::\d\d)?)?\b")
TIME = re.compile(r"\b\d{1,2}:\d\d\b")
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
MONTH_RX = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
HEDGE = re.compile(r"(?:about|around|roughly|approximately|approx\.?|nearly|almost|some|~|≈|c\.|circa|just (?:over|under))\s*[£$€]?$", re.I)
STOP = set("""the and for with from that this those these than then into onto over under per are was were has have had not
but its our your their they them which what when where who whom how all any each every one two three four five six seven
eight nine ten about around roughly approx some more less most least also only just very can will would could should may
might must been being does did doing done out off yes true false none null new old same other another both such via
total sum overall average mean figure figures value values number numbers count rate amount data row rows table tool
result results gbp pct percent id name type status date days day week weeks month months year years""".split())
GENERIC = {"cost", "costs", "spend", "units", "unit", "qty", "quantity", "price", "change", "share", "level", "score"}
LABEL_GENERIC = {"units", "unit", "qty", "quantity", "level", "score", "change"}   # too common to tie a figure to a column
TEMPLATE_CUE = re.compile(r"(?:e\.?g\.?|for example|for instance|format(?:ted)?(?: is| like| as)?|like|such as|i\.e\.|"
                          r"placeholder|pattern|template|looks like|in the form)\W{0,4}(?:\w+\W{1,3}){0,2}$", re.I)
WEAK_EXTERNAL = re.compile(r"\b(?:typical(?:ly)?|usually|generally|commonly|as a rule|rule of thumb|in most cases)\b", re.I)
EXTERNAL_CUE = re.compile(
    r"\b(?:stud(?:y|ies)|surveys?|according to|industry (?:average|benchmark|norm|standard|data|figure|rule)s?|"
    r"published (?:stud|research|data|figure|benchmark|source|report|evidence|analys)\w*|research(?:ers)?|academic|"
    r"literature|widely (?:cited|reported)|"
    r"(?:market|industry|sector|analyst|government|official) (?:report|statistic|data|estimate)s?|"
    r"general knowledge|training data|from memory|my knowledge|outside (?:the|these|our) (?:tools|data|systems)|"
    r"McKinsey|Gartner|Deloitte|PwC|KPMG|Forrester|BCG|Bain|Accenture|Oxford|Harvard|MIT|ONS|OECD|World Bank|IMF|"
    r"WTO|Statista|Nielsen|IDC|Eurostat|BRC|British Retail Consortium|Home Office|Bank of England|IPCC)\b", re.I)
EXTERNAL_LABEL = re.compile(
    r"\b(?:verify|verified|check (?:it|this|that|them|these)|please check|general knowledge|training data|from memory|"
    r"not (?:from|in) (?:the|our|these) (?:tools|data|systems)|no (?:internal|external) (?:benchmark|data)|"
    r"I (?:don't|do not|can't|cannot) (?:have|confirm|verify)|outside (?:the|these|our) (?:tools|data|systems)|"
    r"may be out of date|unverified|background)\b", re.I)
TOTAL_ROW = re.compile(r"^\W*(?:grand\s+)?(?:total|sum|overall|all\b|net\b|combined)", re.I)
MEAN_ROW = re.compile(r"^\W*(?:average|mean|avg)\b", re.I)


# ---------- numbers ----------

@dataclass
class Num:
    """A figure as written: value (scaled by its k/m suffix), rounding tolerance, decimals, significant digits."""
    text: str
    value: float
    tol: float
    dp: int
    mult: float
    pct: bool
    sig: int
    hedged: bool
    start: int
    end: int
    suffix: str = ""


def _sig(digits: str, integer: bool) -> int:
    d = digits.lstrip("0")
    return len(d.rstrip("0") if integer else d) or 1


DAY_MONTH = re.compile(r"\b\d{1,2}(?:st|nd|rd|th)?(?=\s+" + MONTH_RX + r"\b)|(?<=\b" + "(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
                       + r"\s)\d{1,2}(?:st|nd|rd|th)?\b(?![,.]?\d)(?!\s?%)", re.I)


def _skip_spans(text: str) -> list[tuple[int, int]]:
    """Spans whose digits are not figures: ids, ISO dates, times, the day in '18 Sep' / 'Sep 18'."""
    return [m.span() for rx in (bench.ID_RX, ISO_DATE, TIME, DAY_MONTH) for m in rx.finditer(text)]



def numbers(text: str) -> list[Num]:
    """Every figure in a text (prose or answer), outside ids, ISO dates and times."""
    skip = _skip_spans(text)
    out = []
    for m in NUM.finditer(text):
        if any(a <= m.start("num") < b for a, b in skip):
            continue
        raw = m.group("num")
        plain = raw.replace(",", "")
        suf = (m.group("suf") or m.group("word") or "").lower()
        mult = SCALE.get(suf, 1.0)
        dp = len(plain.split(".")[1]) if "." in plain else 0
        neg = bool(m.group("neg"))
        val = float(plain) * mult * (-1 if neg else 1)
        hedged = bool(HEDGE.search(text[max(0, m.start() - 22):m.start()]))
        tol = 0.5 * 10 ** -dp * mult
        if hedged and dp == 0 and mult == 1 and len(plain) >= 3:
            tz = min(len(plain) - len(plain.rstrip("0")), 3)
            tol = max(tol, 0.5 * 10 ** tz)
        end = m.end("word") if m.group("word") else m.end("suf") if m.group("suf") else m.end("num")
        out.append(Num(raw + (m.group("suf") or ""), val, tol, dp, mult, bool(m.group("pct")),
                       _sig(plain.replace(".", ""), dp == 0), hedged, m.start(), end, suf))
    return out


def parse(value: str) -> Num | None:
    ns = numbers(str(value))
    return ns[0] if ns else None


def scale_forms(n) -> list[str]:
    """Spellings of a figure at other scales and roundings: 129444 -> 129,444, 129.4k, 129k, 0.13m, 0.129m."""
    try:
        x = float(str(n).replace(",", ""))
    except ValueError:
        return [str(n)]
    a, out = abs(x), []
    sign = "-" if x < 0 else ""
    out.append(f"{x:,.0f}" if x == int(x) else f"{x:,}")
    if a >= 1e3:
        out += [f"{sign}{a / 1e3:,.1f}k", f"{sign}{a / 1e3:,.0f}k"]
    if a >= 1e5:
        out += [f"{sign}{a / 1e6:,.2f}m", f"{sign}{a / 1e6:,.1f}m"]
        if a < 1e6:
            out.append(f"{sign}{a / 1e6:,.3f}m")
    if a >= 1e8:
        out += [f"{sign}{a / 1e9:,.2f}bn"]
    if x != int(x):
        s = str(abs(x)).split(".")[1]
        for d in range(len(s) - 1, -1, -1):
            r = f"{x:.{d}f}"
            if _sig(r.replace("-", "").replace(".", ""), d == 0) >= 2:
                out.append(r)
    return [f for f in dict.fromkeys(out) if not re.fullmatch(r"-?0(\.0+)?[km]?", f)]


# ---------- dates, years, template ids, outside sources ----------

def date_year(text: str, start: int, end: int) -> bool:
    """Is the 4-digit number at text[start:end] a year inside a date ('1 October 2025', 'Oct 2025', '2025-10-01',
    'FY2026', 'in 2026', '(2023)')?"""
    tok = text[start:end]
    if not re.fullmatch(r"(?:19[5-9]\d|20[0-4]\d)", tok):
        return False
    before, after = text[max(0, start - 16):start].lower(), text[end:end + 6]
    if re.search(MONTH_RX + r"\.?,?\s*(?:\d{1,2}(?:st|nd|rd|th)?,?\s*)?$", before):
        return True
    if re.match(r"-\d\d", after) or re.search(r"\d\d?[/.]\d\d?[/.]$", before):
        return True
    if re.search(r"(?:\bfy|\bcy|\bq[1-4]|\bh[12]|\bin|\bsince|\bby|\bduring|\buntil|\bthrough|\bfrom|\bto|\bof|\bfor|"
                 r"\byear|\bbefore|\bafter|\bend|\bstart|\bearly|\blate|\bmid|\bthe)[\s-]*$", before):
        return True
    if re.search(r"(?:\bacts?|\bplan|\bdirective|\bregulations?|\bbill|\border|\bstandard|\bstrategy|\bframework|"
                 r"\bconvention|\bcensus|\bbudget|\bedition|\bversion|'s|’s|/\w+)\s*$", before):
        return True
    return bool(re.search(r"\(\s*$", before) and re.match(r"\s*\)", after))


def is_template_id(token: str, context: str = "") -> bool:
    """An id written as an example or format, not as a claim: 'e.g. EMP-000xx', 'format EMP-00000', 'like EMP-00086'."""
    t = str(token)
    tail = re.sub(r"^[A-Za-z]+-?", "", t)
    if re.search(r"x{2,}|X{2,}|#{2,}|n{3,}|N{3,}|_{2,}|\?{2,}", t) or (re.fullmatch(r"[0\-]+", tail) and len(tail) >= 3):
        return True
    i = context.find(t)
    before = context[max(0, i - 40):i] if i >= 0 else context[-40:]
    return bool(TEMPLATE_CUE.search(before))


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z(*\-•\d£$])|\n+", text or "") if s.strip()]


def external_claims(text: str, results: list[str] | None = None) -> list[dict]:
    """Sentences that cite outside sources or knowledge: {sentence, has_figures, labelled, figures}. Figures: any size
    ('45%' counts), not years, not figures a tool result gives (when `results` are passed); labelled: the sentence or
    its paragraph marks it as outside background to verify. 'Typically' / 'usually' count only with such a figure."""
    seen = None
    if results is not None:   # 'typically' sentences: a figure a tool result gives exactly is the data's, not outside
        ev = _evidence(tuple(results), ())
        seen = lambda n: bool(_near(ev, n.value, 1e-9)) or (n.pct and bool(_near(ev, n.value / 100, 1e-9)))
    out = []
    for para in re.split(r"\n\s*\n|\n(?=\s*[-*•\d]+[.)]?\s)", text or ""):
        sents = _sentences(para)
        lab_para = bool(EXTERNAL_LABEL.search(para))
        for s in sents:
            strong = EXTERNAL_CUE.search(s)
            if not strong and not WEAK_EXTERNAL.search(s):
                continue
            if strong and re.search(r"\bour (?:\w+ )?(?:research|stud|survey)", s, re.I):
                strong = None
            figs = [n for n in numbers(s) if not _year_like(s, n) and not date_year(s, n.start, n.start + len(n.text))
                    and not (seen and not strong and seen(n))]
            if not strong and not figs:
                continue
            out.append({"sentence": s, "has_figures": bool(figs), "labelled": lab_para or bool(EXTERNAL_LABEL.search(s)),
                        "figures": [n.text + ("%" if n.pct else "") for n in figs]})
    return out


# ---------- tokens and labels ----------

def _stem(w: str) -> str:
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def tokens(s: str) -> set[str]:
    """Label words of a text: lower-case stems of 3+ letters (no stopwords), word+number pairs ('cat#1'), months as
    YYYY-MM ('Jun 2026', '2026-06-15' -> '2026-06')."""
    s = str(s or "")
    low = s.lower()
    out = {_stem(w) for w in re.findall(r"[a-z][a-z0-9]{2,}", low) if w not in STOP}
    out |= {f"{a}#{b}" for a, b in re.findall(r"\b([a-z]{2,})[\s_-]?(\d{1,3})\b", low) if a not in STOP}
    out |= {f"{y}-{mo}" for y, mo in re.findall(r"\b(20\d\d)-(\d\d)\b", low)}
    out |= {"m:" + MONTHS[int(mo) - 1] for mo in re.findall(r"\b20\d\d-(\d\d)\b", low) if 1 <= int(mo) <= 12}
    out |= {"m:" + m[:3] for m in re.findall(r"\b" + MONTH_RX + r"\b", low)}
    for m in re.finditer(r"\b(" + MONTH_RX + r")\.?\s*(?:\d{1,2}(?:st|nd|rd|th)?,?\s*)?'?(20\d\d|\d\d)\b", low):
        y = m.group(2) if len(m.group(2)) == 4 else "20" + m.group(2)
        out.add(f"{y}-{MONTHS.index(m.group(1)[:3]) + 1:02d}")
    out |= {i.lower() for i in bench.ID_RX.findall(s)}
    return out


# ---------- tool results ----------

@dataclass
class RTable:
    call: int
    header: list
    rows: list
    vals: list          # per row, per column: float | None
    numeric: list       # column indexes that are numeric
    keys: list          # column indexes that are labels (text)
    tok: list = field(default_factory=list)   # per row, per key column: tokens


@dataclass
class RNum:
    value: float
    call: int
    line: str
    col: str
    table: int = -1
    row: int = -1


@dataclass
class Evidence:
    tables: list
    nums: list
    args: list          # per call: its args
    index: list         # sorted (abs value, i into nums)


def _cell_num(c: str) -> float | None:
    c = c.strip()
    if re.fullmatch(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", c):
        return float(c)
    return None


def _header_at(lines: list[str]) -> int | None:
    for i, ln in enumerate(lines[:3]):
        cells = next(csv.reader([ln]), [])
        if len(cells) >= 2 and all(re.fullmatch(r"[A-Za-z_][\w ]*", c.strip() or "_") for c in cells):
            return i
    return None


@lru_cache(maxsize=64)
def _evidence(results: tuple, args: tuple) -> Evidence:
    tables, nums = [], []
    for ci, text in enumerate(results):
        lines = (text or "").splitlines()
        h = _header_at(lines)
        done = set()
        if h is not None:
            header = next(csv.reader([lines[h]]))
            rows = [r for r in csv.reader(lines[h + 1:]) if len(r) >= len(header) - 1 and len(r) <= len(header) + 1]
            if rows:
                vals = [[_cell_num(c) for c in r[:len(header)]] + [None] * (len(header) - len(r)) for r in rows]
                numeric = [j for j in range(len(header)) if sum(v[j] is not None for v in vals) >= max(1, 0.6 * len(rows))]
                keyc = [j for j in range(len(header)) if j not in numeric and any(len(r) > j and r[j].strip() and len(r[j]) <= 80 for r in rows)]
                t = RTable(ci, header, rows, vals, numeric, keyc)
                t.tok = [{j: tokens(r[j]) | {r[j].strip().lower()} for j in keyc if j < len(r)} for r in rows]
                ti = len(tables)
                tables.append(t)
                for ri, (r, v) in enumerate(zip(rows, vals)):
                    line = ",".join(r)
                    done.add(line)
                    for j, x in enumerate(v):
                        if x is not None:
                            nums.append(RNum(x, ci, line, header[j], ti, ri))
                        elif j < len(r) and len(r[j]) > 12:   # numbers inside a text cell
                            nums += [RNum(n.value, ci, line, header[j] + " " + r[j][max(0, n.start - 40):n.start], ti, ri)
                                     for n in numbers(r[j])]
        for ln in lines:
            if ln in done or ",".join(next(csv.reader([ln]), [])) in done:
                continue
            key = ln.split(":", 1)[0] if ":" in ln[:60] else ""
            nums += [RNum(n.value, ci, ln, key or ln[max(0, n.start - 40):n.start]) for n in numbers(ln)]
    idx = sorted((abs(n.value), i) for i, n in enumerate(nums))
    return Evidence(tables, nums, list(args), idx)


def evidence(results: list[str], rows: list[dict] | None = None) -> Evidence:
    args = tuple(repr(sorted((r.get("args") or {}).items())) for r in rows) if rows and len(rows) == len(results) else ()
    ev = _evidence(tuple(results), args)
    if rows and len(rows) == len(results):
        ev.args = [r.get("args") or {} for r in rows]
    return ev


def _near(ev: Evidence, target: float, tol: float) -> list[RNum]:
    import bisect
    a = abs(target)
    lo = bisect.bisect_left(ev.index, (a - tol - 1e-9, -1))
    out = []
    for k in range(lo, len(ev.index)):
        v, i = ev.index[k]
        if v > a + tol + 1e-9:
            break
        out.append(ev.nums[i])
    return out


# ---------- answer context ----------

@dataclass
class MdTable:
    start: int
    header: list
    rows: list          # (line index, cells)
    caption: str
    after: str


@dataclass
class Ctx:
    num: Num
    sentence: str
    line: str
    para: str
    turn_text: str
    table: MdTable | None = None
    row: list | None = None
    col: int = -1
    scale: float = 1.0          # implied by a '£m' / '(k)' header or caption
    words: set = field(default_factory=set)       # label words of the sentence / table row + column header
    para_words: set = field(default_factory=set)
    label: str = ""


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def md_tables(text: str) -> list[MdTable]:
    lines = (text or "").splitlines()
    out, i = [], 0
    while i < len(lines):
        if lines[i].strip().startswith("|"):
            j = i
            while j < len(lines) and lines[j].strip().startswith("|"):
                j += 1
            block = [(k, _cells(lines[k])) for k in range(i, j)]
            body = [(k, c) for k, c in block[1:] if not all(re.fullmatch(r":?-{2,}:?", x or "--") for x in c)]
            cap = next((lines[k] for k in range(i - 1, max(-1, i - 4), -1) if lines[k].strip()), "")
            aft = " ".join(lines[k] for k in range(j, min(len(lines), j + 3)) if lines[k].strip())
            out.append(MdTable(i, block[0][1], body, cap, aft))
            i = j
        else:
            i += 1
    return out


def _implied_scale(*texts: str) -> float:
    t = " ".join(texts).lower()
    if re.search(r"£\s?m\b|\(m\)|\bin £?millions?\b|£\s?mn\b|\bm£|figures are £m|all £m|\(£m\)|£m\)", t):
        return 1e6
    if re.search(r"£\s?k\b|\(k\)|£\s?000|£'000|\bin thousands\b|\(£k\)|£k\)", t):
        return 1e3
    return 1.0


def _num_val(cell: str) -> float | None:
    c = cell.replace("*", "").replace("≈", "").replace("~", "").strip()
    m = re.fullmatch(r"\(([£$€]?[\d,]+(?:\.\d+)?)\)\s*[km]?", c)
    if m:
        n = parse(m.group(1))
        return -n.value if n else None
    ns = numbers(c)
    return ns[0].value if len(ns) == 1 and len(ns[0].text) + 3 >= len(re.sub(r"[£$€%+\s]", "", c)) else None


def context(value: str, sentence: str, answer: str) -> Ctx | None:
    """Where `value` sits in the answer: its Num, sentence, line, paragraph, table row and column, implied scale, labels."""
    answer = answer or sentence or ""
    pos = answer.find(sentence) if sentence else -1
    want = str(value)
    base = pos if pos >= 0 else 0
    region = answer[base:base + len(sentence)] if pos >= 0 else answer
    n = next((x for x in numbers(region) if x.text == want or x.text.rstrip("kmbn") == want or
              re.sub(r"[^\d.]", "", x.text) == re.sub(r"[^\d.]", "", want)), None)
    if n is None:
        return None
    start = base + n.start
    n = Num(**{**n.__dict__, "start": start, "end": base + n.end})
    ls = answer.rfind("\n", 0, start) + 1
    le = answer.find("\n", start)
    line = answer[ls:le if le >= 0 else len(answer)]
    pa = answer.rfind("\n\n", 0, start)
    pb = answer.find("\n\n", start)
    para = answer[pa + 2 if pa >= 0 else 0:pb if pb >= 0 else len(answer)]
    sent = sentence if pos >= 0 else next((s for s in _sentences(line) if want in s), line)
    cx = Ctx(n, sent, line, para, answer)
    line_no = answer.count("\n", 0, start)
    for t in md_tables(answer):
        for k, cells in t.rows:
            if k == line_no:
                cx.table, cx.row = t, cells
                off = start - ls
                acc = line.find("|") + 1 if line.lstrip().startswith("|") else 0
                for ci, c in enumerate(line.strip().strip("|").split("|")):
                    seg_start = line.find(c, acc)
                    if seg_start <= off <= seg_start + len(c):
                        cx.col = ci
                        break
                    acc = seg_start + len(c)
    if cx.table:
        hdr = cx.table.header[cx.col] if 0 <= cx.col < len(cx.table.header) else ""
        cx.scale = _implied_scale(hdr, cx.table.caption, cx.table.after, cx.row[0] if cx.row else "")
        cx.words = tokens(" ".join(cx.row[:1]) + " " + hdr + " " + cx.table.caption)
        cx.label = f"{cx.row[0] if cx.row else ''} / {hdr}".strip(" /")
    else:
        cx.words = tokens(sent)
        before = re.sub(r"[*_|]", " ", answer[max(ls, start - 60):start])
        cx.label = " ".join(re.findall(r"[A-Za-z][\w'%-]*", before)[-6:])
    cx.para_words = tokens(para) | cx.words
    return cx


# ---------- matching rows of tool results to a context ----------

def _matched_rows(ev: Evidence, words: set, text: str) -> list[tuple[int, int, list[int]]]:
    """(table, key column, rows) whose key cell is named in the context: an id or the whole cell in the text, or a token
    distinctive in that column (in at most half of its rows)."""
    low = (text or "").lower()
    out = []
    for ti, t in enumerate(ev.tables):
        n = len(t.rows)
        for j in t.keys:
            freq: dict = {}
            for tk in t.tok:
                for w in tk.get(j, ()):
                    freq[w] = freq.get(w, 0) + 1
            lim = max(1, n // 2) if n > 2 else 1
            hit = []
            for ri, tk in enumerate(t.tok):
                cell = t.rows[ri][j].strip().lower() if j < len(t.rows[ri]) else ""
                if not cell:
                    continue
                if len(cell) >= 3 and re.search(r"(?<![\w-])" + re.escape(cell) + r"(?![\w-])", low):
                    hit.append(ri)
                elif len(cell) == 2 and cell.isalpha() and re.search(r"\b" + cell.upper() + r"\b", text or ""):
                    hit.append(ri)   # a two-letter code written in capitals ('DE, FR, NL')
                elif len(cell) <= 40 and any(w in words and not w.startswith("m:") and freq.get(w, 0) <= lim and w not in GENERIC and not re.fullmatch(r"20\d\d", w)
                         for w in tk.get(j, ())):
                    hit.append(ri)
            if hit and len(hit) < n or (hit and n <= 3):
                out.append((ti, j, hit))
    return out


def _constant(t: RTable, c: int) -> bool:
    """A column that repeats one figure on every row (a total broadcast to each row): never summed over rows."""
    vs = {r[c] for r in t.vals if r[c] is not None}
    return len(vs) == 1 and len(t.rows) > 1


def _prefix_overlap(a: set, b: set) -> bool:
    """Two label words share a stem: a common prefix of 4+ letters that is all but at most two letters of the shorter
    word ('overpay' / 'overpayment', 'hedge' / 'hedging'; not 'forward' / 'forecast')."""
    def stem_match(x, y):
        k = 0
        while k < min(len(x), len(y)) and x[k] == y[k]:
            k += 1
        return k >= 4 and k >= min(len(x), len(y)) - 2
    return any(stem_match(x, y) for x in a for y in b if "#" not in x + y and x.isalpha() and y.isalpha())


def _col_words(t: RTable, j: int) -> set:
    return tokens(t.header[j].replace("_", " "))


def _plausible(rn: RNum, cx: Ctx, ev: Evidence) -> bool:
    """A result number may stand for a short (or scaled) figure only if its column (or the words before it on a
    key: value line) shares a label word with the figure's line, table row, column header or caption, or its row is
    named on that line (an id or name), or the row shares two distinctive words with it."""
    lab = tokens(rn.col.replace("_", " ")) - LABEL_GENERIC
    w = cx.words | tokens(cx.line)
    if lab & w or _prefix_overlap(lab, w):
        return True
    if rn.table < 0:
        return False
    t, low = ev.tables[rn.table], cx.line.lower()
    row = t.rows[rn.row]
    if any(3 <= len(c := row[j].strip().lower()) <= 40 and not re.fullmatch(r"[\d.\-: ]+", c)
           and re.search(r"(?<![\w-])" + re.escape(c) + r"(?![\w-])", low) for j in t.keys if j < len(row)):
        return True
    rw = {x for j in t.keys if j < len(row) for x in tokens(row[j])} - GENERIC
    return len({x for x in rw & w if len(x) >= 4 and "#" not in x}) >= 2


# ---------- derive ----------

def _targets(cx: Ctx) -> list[tuple[float, float, str]]:
    """(value, tolerance, note) to look for: as written, at an implied £m/£k scale, a percentage as a fraction."""
    n = cx.num
    out = [(n.value, n.tol, "")]
    if not n.suffix and cx.scale > 1:
        out.append((n.value * cx.scale, n.tol * cx.scale, f" at x{cx.scale:g} (table in {'£m' if cx.scale == 1e6 else '£k'})"))
    if n.pct and n.value not in (0, 100):
        out.append((n.value / 100, n.tol / 100, " as a fraction"))
    return out


def _ok(x: float, target: float, tol: float) -> bool:
    return abs(abs(x) - abs(target)) <= tol + 1e-9


def _fmt(x: float) -> str:
    return f"{x:,.4g}" if abs(x) < 1000 else f"{x:,.0f}"


def _window(ev: Evidence, call: int, cx: Ctx) -> list[tuple[float, str]]:
    """Annualisation factors from the call's date window (date_from/to, period_start/end, days/weeks/months) and the
    'N weeks / months / days' the context names."""
    out, a = [], ev.args[call] if 0 <= call < len(ev.args) else {}
    ds = [str(v) for k, v in a.items() if re.search(r"(from|start|_to|end|until|since)", k) and re.fullmatch(r"\d{4}-\d\d-\d\d", str(v))]
    if len(ds) >= 1:
        d0 = min(date.fromisoformat(d) for d in ds)
        d1 = max(date.fromisoformat(d) for d in ds) if len(ds) > 1 else None
        if d1 and d1 > d0:
            days = (d1 - d0).days + 1
            out.append((365 / days, f"x365/{days} days"))
            if days >= 7:
                out.append((52 / round(days / 7), f"x52/{round(days / 7)} weeks"))
            if days >= 28:
                out.append((12 / round(days / 30.44), f"x12/{round(days / 30.44)} months"))
    for k, v in a.items():
        if isinstance(v, (int, float)) and v > 0:
            if "week" in k:
                out.append((52 / v, f"x52/{v:g} weeks"))
            elif "month" in k:
                out.append((12 / v, f"x12/{v:g} months"))
            elif "day" in k:
                out.append((365 / v, f"x365/{v:g} days"))
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(weeks?|months?|days?)\b", cx.para, re.I):
        k, u = float(m.group(1)), m.group(2).lower()
        if k > 0:
            out.append(({"w": 52, "m": 12, "d": 365}[u[0]] / k, f"x{ {'w': 52, 'm': 12, 'd': 365}[u[0]] }/{k:g} {u}"))
    return out


GENERIC_FACTORS = [(52, "x52 (weekly to annual)"), (12, "x12 (monthly to annual)"), (365, "x365 (daily to annual)"),
                   (1 / 52, "/52 (annual to weekly)"), (1 / 12, "/12 (annual to monthly)")]
PERIOD_CUE = re.compile(r"\b(?:annual(?:ly|ised|ized)?|a year|per year|per annum|yearly|full[- ]year|12[- ]months?|each year|"
                        r"every year|a (?:week|month|day)|per (?:week|month|day)|weekly|monthly|daily|run[- ]rate)\b", re.I)


def _factors(ev: Evidence, cx: Ctx, call: int | None = None) -> list[tuple[float, str]]:
    """Annualisation factors, only when the figure's sentence (or line) speaks of a period: the call's date window
    (or every call's, with no call), the periods the paragraph names, then x52 / x12 / x365 and back."""
    if not PERIOD_CUE.search(cx.sentence) and not (cx.table and PERIOD_CUE.search(cx.line + " " + cx.table.caption)):
        return []
    win = _window(ev, call, cx) if call is not None else _window_any(ev, cx)
    return [(f, why) for f, why in win + GENERIC_FACTORS if not 0.9 < f < 1.1]


def derive(value: str, sentence: str, answer_text: str, results: list[str], rows: list[dict] | None = None) -> str | None:
    """How a figure in the answer that is in no tool result can be restated or derived from the tool results or the
    answer's own figures, naming the operands; None when no plausible derivation is found. `rows`: the trace calls
    (parallel to `results`) whose date-window args annualisation uses."""
    cx = context(value, sentence, answer_text)
    if cx is None:
        return None
    ev = evidence(results, rows)
    targets = _targets(cx)
    n = cx.num
    short = n.sig <= 3

    # 1. restated: rounding, units, scale
    for tv, tol, note in targets:
        for rn in _near(ev, tv, tol):
            if (not short and not note) or _plausible(rn, cx, ev):
                return f"restated{note}: {_fmt(rn.value)} ({rn.col.strip()[:40]}, call {rn.call})"

    # 1b. the same figure stated elsewhere in the answer, more precisely, where it is a tool-result figure
    for m in numbers(answer_text):
        if m.start == n.start or m.sig <= n.sig or m.pct != n.pct:
            continue
        for tv, tol, note in targets:
            if _ok(m.value, tv, tol) and (rn := next(iter(_near(ev, m.value, m.tol)), None)):
                return f"restated{note}: '{m.text}' stated elsewhere in the answer ({rn.col.strip()[:40]}, call {rn.call})"

    # 2. rows the context names: one row, or the sum / mean of k rows sharing a label (group-by), in a column whose
    # label the figure's line uses (a long figure needs no label)
    lw = cx.words | tokens(cx.line)
    scopes = [(cx.words, cx.sentence if not cx.table else cx.line)]
    if not cx.table:
        scopes.append((tokens(cx.line), cx.line))
    scopes.append((cx.para_words, cx.para))
    for scope_words, scope_text in scopes:
        for ti, j, hit in _matched_rows(ev, scope_words, scope_text):
            t = ev.tables[ti]
            for c in t.numeric:
                vs = [t.vals[r][c] for r in hit if t.vals[r][c] is not None]
                if not vs or (len(vs) >= 2 and _constant(t, c)):
                    continue
                labs = sorted({t.rows[r][j] for r in hit})
                desc = f"{t.header[c]} over {len(vs)} rows with {t.header[j]} in {labs[:4]}{'...' if len(labs) > 4 else ''}"
                cw = _col_words(t, c) - LABEL_GENERIC
                col_ok = bool(cw & lw) or _prefix_overlap(cw, lw)
                for tv, tol, note in targets:
                    if not (col_ok or (n.sig >= 4 and not note)):
                        continue
                    if len(vs) >= 2 and _ok(sum(vs), tv, tol):
                        return f"sum{note} of {desc} (call {t.call}) = {_fmt(sum(vs))}"
                    if len(vs) >= 2 and _ok(sum(vs) / len(vs), tv, tol + 0.002 * abs(tv)):
                        return f"mean{note} of {desc} (call {t.call}) = {_fmt(sum(vs) / len(vs))}"
                    for f, why in _factors(ev, cx, t.call) if col_ok else ():
                        if _ok(sum(vs) * f, tv, tol + 0.01 * abs(tv)):
                            return f"annualised{note}: {_fmt(sum(vs))} ({desc}) {why} = {_fmt(sum(vs) * f)}"
                # some of the named groups ('the sensor faults and the software glitch'): sums over 2-6 label
                # groups, only in a column whose own label the context uses
                groups: dict = {}
                for r in hit:
                    if t.vals[r][c] is not None:
                        groups.setdefault(t.rows[r][j], []).append(t.vals[r][c])
                if not 2 <= len(groups) <= 6 or not ((_col_words(t, c) - GENERIC) & scope_words or
                                                     _prefix_overlap(_col_words(t, c), scope_words)):
                    continue
                keys = sorted(groups)
                for k in range(1, len(keys)):
                    for combo in itertools.combinations(keys, k):
                        xs = [x for g in combo for x in groups[g]]
                        if len(xs) < 2:
                            continue
                        for tv, tol, note in targets:
                            if _ok(sum(xs), tv, tol):
                                return f"sum{note} of {t.header[c]} over the rows with {t.header[j]} in {list(combo)} (call {t.call}) = {_fmt(sum(xs))}"

    # 3. a whole column of a result table: total, mean, annualised total (label must match unless the figure is long)
    for t in ev.tables:
        for c in t.numeric:
            vs = [r[c] for r in t.vals if r[c] is not None]
            if len(vs) < 2 or _constant(t, c):
                continue
            cl = _col_words(t, c) - LABEL_GENERIC
            lab_ok = not short or bool(cl & (cx.words | cx.para_words)) or _prefix_overlap(cl, cx.words | cx.para_words)
            if not lab_ok:
                continue
            s = sum(vs)
            cw = _col_words(t, c) - LABEL_GENERIC
            for tv, tol, note in targets:
                if _ok(s, tv, tol):
                    return f"column total{note} of {t.header[c]} ({len(vs)} rows, call {t.call}) = {_fmt(s)}"
                if _ok(s / len(vs), tv, tol + 0.002 * abs(tv)):
                    return f"column mean{note} of {t.header[c]} ({len(vs)} rows, call {t.call}) = {_fmt(s / len(vs))}"
                for f, why in _factors(ev, cx, t.call) if (cw & lw or _prefix_overlap(cw, lw)) else ():
                    if _ok(s * f, tv, tol + 0.01 * abs(tv)):
                        return f"annualised{note}: column total of {t.header[c]} {_fmt(s)} (call {t.call}) {why} = {_fmt(s * f)}"

    # 4. the answer's own figures: same table row / sentence / column (sums, differences, ratios, %, means, products)
    local = _local_operands(cx)
    how = _arith(local, [], cx, targets, allow_sums=True, ev=ev)
    if how:
        return how

    # 5. pairs of an answer figure and a figure on a result row the context names (or two on the same row), the
    # row's figure in a column whose label the context uses
    rowops, lw = [], cx.words | tokens(cx.line)
    for ti, j, hit in _matched_rows(ev, cx.words, cx.sentence if not cx.table else cx.line)[:6]:
        t = ev.tables[ti]
        for r in hit[:8]:
            rowops += [(t.vals[r][c], f"{t.header[c]} of {t.rows[r][j]}", (ti, r)) for c in t.numeric
                       if t.vals[r][c] is not None and ((_col_words(t, c) - GENERIC) & lw or _prefix_overlap(_col_words(t, c), lw))]
    if short and n.sig <= 2:
        rowops = []
    if not short or local:
        how = _arith(local, rowops[:60], cx, targets, allow_sums=False, ev=ev)
        if how:
            return how

    # 6. annualisation of a sentence / row figure or a named row's figure
    for x, desc, _ in local + rowops[:40]:
        for f, why in _factors(ev, cx):
            for tv, tol, note in targets:
                if x and _ok(x * f, tv, tol + 0.01 * abs(tv)) and abs(x) != abs(tv):
                    return f"annualised{note}: {_fmt(x)} ({desc}) {why} = {_fmt(x * f)}"
    return None


def _window_any(ev: Evidence, cx: Ctx) -> list:
    out = []
    for c in range(len(ev.args)):
        out += _window(ev, c, cx)
    seen, res = set(), []
    for f, why in out:
        if why not in seen:
            seen.add(why)
            res.append((f, why))
    return res[:12]


def _local_operands(cx: Ctx) -> list[tuple[float, str, tuple]]:
    """Answer figures next to the value: its table row, its sentence (or line), and its table column."""
    out, own = [], (cx.num.start, cx.num.end)
    if cx.table and cx.row:
        for ci, c in enumerate(cx.row):
            if ci != cx.col and (v := _num_val(c)) is not None:
                hdr = cx.table.header[ci] if ci < len(cx.table.header) else f"col {ci}"
                out.append((v, f"'{c}' ({hdr})", ("row", ci)))
            elif ci == cx.col:   # other figures in the value's own cell ('2,112 min (35.2 h)')
                own_cell = [x for x in numbers(c) if not (x.value == cx.num.value and x.text == cx.num.text)]
                out += [(x.value, f"'{x.text}' (same cell)", ("cell", x.start)) for x in own_cell]
    else:
        base = cx.turn_text.find(cx.sentence)
        for x in numbers(cx.sentence):
            if base >= 0 and (base + x.start, base + x.end) == own or (base < 0 and x.text == cx.num.text):
                continue
            if date_year(cx.sentence, x.start, x.start + len(x.text)):
                continue
            out.append((x.value, f"'{x.text}{'%' if x.pct else ''}' (same sentence)", ("sent", x.start)))
    return out


UNIT_FACTORS = [(1 / 60, "/60 (minutes to hours)"), (60, "x60 (hours to minutes)"), (1 / 24, "/24 (hours to days)"),
                (1 / 1000, "/1000 (k, kg to t)"), (1000, "x1000"), (1 / 100, "/100 (pence to £)"), (100, "x100 (£ to pence)"),
                (1 / 7, "/7 (per week to per day)"), (7, "x7 (per day to per week)")]


def _arith(local, rowops, cx: Ctx, targets, allow_sums: bool, ev: Evidence | None = None) -> str | None:
    """Sums of 2-5 local figures (each no bigger than the value), means of 3+, other units of a local figure, and
    pairwise difference, ratio, percentage, percentage change and product: a pair of local figures needs one that a
    tool result gives; a local figure with a result-row figure needs the local one in a result; or two figures of one
    result row (two answer figures that only derive from each other clear nothing)."""
    ops = [o for o in local if o[0] is not None]
    g = (lambda a: bool(_near(ev, a, 0.005 + 0.005 * abs(a)))) if ev is not None else (lambda a: True)
    if allow_sums and 2 <= len(ops) <= 12:
        pos = [o for o in ops if o[0] > 0]
        for tv, tol, note in targets:
            t2 = tol + 0.002 * abs(tv)
            small = [o for o in pos if o[0] <= abs(tv) * 1.0001 and o[0] >= 0.02 * abs(tv)]
            for k in range(2, min(5, len(small)) + 1):
                for combo in itertools.combinations(small, k):
                    if _ok(sum(o[0] for o in combo), tv, t2):
                        return f"sum{note} of {' + '.join(o[1] for o in combo)}"
            if len(ops) >= 3 and _ok(sum(o[0] for o in ops) / len(ops), tv, t2):
                return f"mean{note} of {', '.join(o[1] for o in ops)}"
    for a, da, _ in ops:
        for f, unit in UNIT_FACTORS:
            for tv, tol, note in targets:
                if a and abs(a) != abs(tv) and _ok(a * f, tv, tol + 0.002 * abs(tv)):
                    return f"restated in other units{note}: {da} {unit} = {_fmt(a * f)}"
    vs = {abs(tv) for tv, _, _ in targets}
    pool = [(a, d, s, True) for a, d, s in ops if abs(a) not in vs] + [(a, d, s, False) for a, d, s in rowops if abs(a) not in vs]
    for i, (a, da, sa, la) in enumerate(pool):
        for b, db, sb, lb in pool[i + 1:]:
            if not (la or lb or (sa == sb)):
                continue
            if not (la or lb) and (isinstance(sa, tuple) and isinstance(sb, tuple) and sa != sb):
                continue
            if (la and lb and not (g(a) or g(b))) or (la != lb and not g(a if la else b)):
                continue
            for tv, tol, note in targets:
                t2 = tol + 0.002 * abs(tv)
                cands = []
                if min(abs(a), abs(b)) >= 0.05 * abs(tv):
                    cands += [(a + b, "+"), (a - b, "-"), (b - a, "-r")]
                if a not in (0, 1) and b not in (0, 1):
                    cands += [(a * b, "x")]
                if b and abs(b) not in (1, 100):
                    cands += [(a / b, "/"), (100 * a / b, "% of"), (100 * (a - b) / b, "% change from")]
                if a and abs(a) not in (1, 100):
                    cands += [(b / a, "/r"), (100 * b / a, "% of r"), (100 * (b - a) / a, "% change from r")]
                for x, op in cands:
                    if _ok(x, tv, t2):
                        l, r = (db, da) if op.endswith("r") else (da, db)
                        op = op.rstrip("r").strip()
                        return f"{'difference' if op == '-' else 'sum' if op == '+' else 'product' if op == 'x' else 'ratio' if op == '/' else 'percentage'}{note}: {l} {op} {r} = {_fmt(x)}"
    return None


# ---------- recompute (Rule A) ----------

def _restated(ev: Evidence, n: Num) -> bool:
    return any(True for _ in _near(ev, n.value, n.tol))


def recompute(answer_text: str, results: list[str]) -> list[dict]:
    """Figures the answer derives from numbers it states or names that are wrong beyond rounding:
    a Total / Average row of an answer table against its body rows; a stated total or mean against the numbers listed
    in the same sentence ('5, 11, 11 and 47 ... average 12.2'), also with one listed number excluded when the sentence
    says so; 'X more / less than Y' against two columns (or rows) of the answer's own table; and a figure close to the
    sum of a column over the records the paragraph or turn names. Each: {value, sentence, computed, how}."""
    ev = _evidence(tuple(results), ())
    out, seen = [], set()

    def add(n_text, sentence, computed, how):
        if n_text not in seen:
            seen.add(n_text)
            out.append({"value": n_text, "sentence": sentence.strip()[:300], "computed": round(computed, 4), "how": how})

    tables = md_tables(answer_text)
    lines = answer_text.splitlines()
    # R1: total / average rows
    for t in tables:
        body, tot = [], []
        for k, cells in t.rows:
            (tot if TOTAL_ROW.match(cells[0].replace("*", "")) or MEAN_ROW.match(cells[0].replace("*", "")) else body).append((k, cells))
        for k, cells in tot:
            mean = bool(MEAN_ROW.match(cells[0].replace("*", "")))
            for ci in range(1, len(cells)):
                hdr = t.header[ci] if ci < len(t.header) else ""
                if "%" in cells[ci] or "%" in hdr or re.search(r"\b(rate|share|pct|percent|avg|average|mean|per)\b", hdr, re.I):
                    continue
                v = _num_val(cells[ci])
                col = [_num_val(c[ci]) for _, c in body if ci < len(c)]
                col = [x for x in col if x is not None]
                if v is None or len(col) < 2 or any("%" in c[ci] for _, c in body if ci < len(c)):
                    continue
                ns = numbers(cells[ci].replace("*", ""))
                if not ns or _restated(ev, ns[0]):
                    continue
                want = sum(col) / len(col) if mean else sum(col)
                tol = ns[0].tol * (1 if ns[0].mult == 1 else 1) + 0.5 * 10 ** -max(
                    [len(re.sub(r"[^\d.]", "", c[ci]).split(".")[1]) if "." in c[ci] else 0 for _, c in body if ci < len(c)] or [0]) * len(col)
                if abs(abs(v) - abs(want)) > max(tol, 0.001 * abs(want)):
                    add(ns[0].text, lines[k], want, f"{'mean' if mean else 'sum'} of the {len(col)} '{hdr}' rows above = {_fmt(want)}")
    # R2: stated totals / means over listed numbers
    for para in re.split(r"\n\s*\n|\n(?=\s*[-*•])", answer_text):
        sents = _sentences(para)
        lists = []
        for s in sents:
            m = re.search(r"((?:-?[£$]?\d[\d,]*(?:\.\d+)?%?\s*(?:,|and|\+)\s*){2,}-?[£$]?\d[\d,]*(?:\.\d+)?%?)", s)
            if m:
                lists.append([x.value for x in numbers(m.group(1))])
        if not lists:
            continue
        for s in sents:
            kw = re.search(r"\b(average|mean|avg|total|sum|in all|altogether|combined)\b", s, re.I)
            if not kw:
                continue
            is_mean = kw.group(1).lower() in ("average", "mean", "avg")
            for n in numbers(s):
                if n.pct or _restated(ev, n) or date_year(s, n.start, n.start + len(n.text)):
                    continue
                if n.start < kw.start() - 60 or n.start > kw.end() + 40:
                    continue
                for L in lists:
                    if len(L) < 3 or n.value in L:
                        continue
                    cands = [(sum(L) / len(L) if is_mean else sum(L), "all listed")]
                    if re.search(r"\bexclud|\bwithout\b|\bleaving out\b|\bexcept\b", s, re.I):
                        for x in sorted(set(L)):
                            rest = list(L)
                            rest.remove(x)
                            cands.append((sum(rest) / len(rest) if is_mean else sum(rest), f"excluding {x:g}"))
                    tol = n.tol + 0.002 * abs(n.value)
                    if any(_ok(c, n.value, tol) for c, _ in cands):
                        continue
                    best = min(cands, key=lambda c: abs(c[0] - n.value))
                    if abs(best[0] - n.value) <= 0.25 * abs(best[0]):
                        add(n.text, s, best[0], f"{'mean' if is_mean else 'sum'} of {', '.join(f'{x:g}' for x in L)} ({best[1]}) = {_fmt(best[0])}")
    # R3: "X more / less than Y" over two columns or rows of the answer's own table
    for t in tables:
        hdr_tok = [tokens(h) for h in t.header]
        row_tok = [tokens(c[0]) for _, c in t.rows]
        for k in range(len(lines)):
            ln = lines[k]
            if ln.strip().startswith("|") or not re.search(r"\b(more|less|higher|lower|cheaper|dearer|greater|smaller)\s+(?:upside\s+|downside\s+)?than\b|\bdifference\b|\bgap\b", ln, re.I):
                continue
            lw = tokens(ln)
            for s in _sentences(ln):
                if not re.search(r"\b(more|less|higher|lower|cheaper|dearer|greater|smaller)\b.{0,30}\bthan\b|\bdifference\b|\bgap\b", s, re.I):
                    continue
                for n in numbers(s):
                    if n.pct or not (n.suffix or t.caption or t.after):
                        continue
                    if not re.search(r"(?:more|less|higher|lower|cheaper|dearer|greater|smaller|difference|gap)", s[n.end:n.end + 40] + s[max(0, n.start - 30):n.start], re.I):
                        continue
                    cols = [i for i in range(1, len(t.header)) if hdr_tok[i] and hdr_tok[i] <= lw]
                    if len(cols) == 2:
                        scale = _implied_scale(t.caption, t.after, " ".join(t.header))
                        target = n.value / scale if n.suffix and scale > 1 else n.value
                        tol = (n.tol / scale if n.suffix and scale > 1 else n.tol) + 0.05 * abs(target) + 0.1
                        diffs = []
                        for _, c in t.rows:
                            a, b = (_num_val(c[i]) if i < len(c) else None for i in cols)
                            if a is not None and b is not None:
                                diffs.append((abs(a - b), c[0]))
                        if diffs and not any(abs(d - abs(target)) <= tol for d, _ in diffs):
                            pick = next((d for d in diffs[::-1] if TOTAL_ROW.match(d[1].replace("*", ""))), diffs[-1])
                            add(n.text, s, pick[0] * (scale if n.suffix and scale > 1 else 1),
                                f"'{t.header[cols[0]]}' vs '{t.header[cols[1]]}' in the answer's table: differences "
                                f"{', '.join(f'{d:g} ({r[:30]})' for d, r in diffs[:6])}; none is {n.text}")
    # R4: a figure the sentence gives for the records the paragraph names ('Those four are £685k'), near but not at the
    # sum of a result column over them; a figure it is compared with ('down from £1.04m') against all records the turn names
    turn_ids = {i.lower() for i in bench.ID_RX.findall(answer_text)}
    for para in re.split(r"\n\s*\n", answer_text):
        if para.strip().startswith("|"):
            continue
        p_ids = {i.lower() for i in bench.ID_RX.findall(para)}
        if len(p_ids) < 2:
            continue
        for s in _sentences(para):
            cue = GROUP_CUE.search(s)
            if not cue:
                continue
            cnt = cue.group("n")
            if cnt and (WORDNUM.get(cnt.lower()) or (int(cnt) if cnt.isdigit() else 0)) != len(p_ids):
                continue
            for n in numbers(s):
                if n.pct or n.sig < 2 or abs(n.value) < 100 or _restated(ev, n) or _year_like(s, n):
                    continue
                ids = turn_ids if re.search(r"(?:down|up|fell|rose|from|previously|was|before)\W+(?:from\W+)?[£$€]?$",
                                            s[max(0, n.start - 16):n.start], re.I) else p_ids
                if ids is turn_ids and not turn_ids > p_ids:
                    continue
                if derive(n.text, s, answer_text, results) is not None:
                    continue
                best = _near_sum(ev, ids, n)
                if best:
                    add(n.text, s, best[0], best[1])
    return out


GROUP_CUE = re.compile(r"\b(?:those|these|the|all|its|their|both)\s+(?P<n>two|three|four|five|six|seven|eight|nine|ten|"
                       r"\d+)\b|\b(?:together|combined|in total|between them|altogether|in all)\b", re.I)
WORDNUM = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten".split())}


def _year_like(s: str, n: Num) -> bool:
    return n.mult == 1 and not n.pct and n.dp == 0 and bool(re.fullmatch(r"(?:19[5-9]\d|20[0-4]\d)", n.text))


def _near_sum(ev: Evidence, ids: set, n: Num) -> tuple[float, str] | None:
    """The column sum over the rows of one result table keyed by `ids` that is within 20% of the figure but not within
    its rounding (a wrong total of named records)."""
    best = None
    for t in ev.tables:
        for j in t.keys:
            rows = {}
            for ri, r in enumerate(t.rows):
                cell = r[j].strip().lower() if j < len(r) else ""
                if cell in ids and cell not in rows:
                    rows[cell] = ri
            if len(rows) < 2:
                continue
            for c in t.numeric:
                vs = [t.vals[ri][c] for ri in rows.values() if t.vals[ri][c] is not None]
                if len(vs) < 2 or _constant(t, c) or re.search(r"pct|percent|rate|share|score|avg|mean|index|days|rank", t.header[c], re.I):
                    continue
                s = sum(vs)
                if _ok(s, n.value, n.tol + 0.002 * abs(n.value)):
                    return None
                if abs(s - abs(n.value)) <= 0.2 * abs(s):
                    d = abs(s - abs(n.value)) / abs(s)
                    if best is None or d < best[2]:
                        best = (s, f"sum of {t.header[c]} over the {len(vs)} named rows {sorted(rows)[:6]} (call {t.call}) = {_fmt(s)}", d)
    return best[:2] if best else None


# ---------- facts (eval-only, label-aware) ----------

def fact_labels(fact, results: list[str]) -> list[set]:
    """Label words of each place a numeric fact appears in the results: its column header and row keys. Empty when
    it appears in more than 3 columns (a small number found everywhere has no label to check)."""
    try:
        f = float(str(fact).replace(",", ""))
    except ValueError:
        return []
    ev = _evidence(tuple(results), ())
    dp = len(str(fact).split(".")[1]) if "." in str(fact) else 0
    out = []
    for rn in _near(ev, f, 0.5 * 10 ** -dp):
        w = tokens(rn.col.replace("_", " "))
        if rn.table >= 0:
            t, row = ev.tables[rn.table], ev.tables[rn.table].rows[rn.row]
            w |= {x for j in t.keys if j < len(row) and len(row[j]) <= 40 for x in tokens(row[j])}
        w = {x for x in w - LABEL_GENERIC if not re.fullmatch(r"\d{4}-\d\d", x)}
        out.append(w)
    cols = {rn.col for rn in _near(ev, f, 0.5 * 10 ** -dp)}
    return out if len(cols) <= 3 else []


def fact_label_text(fact, results: list[str]) -> str:
    """The words the results use for a numeric fact: its column and the row's first label cells ('cost_vs_pfas_option_pct
    of MAT-DWR-SILICONE, PFAS-free silicone DWR finish'), or the text before it on a key: value line."""
    fn = _fact_num(fact)
    if not fn:
        return ""
    ev = _evidence(tuple(results), ())
    for rn in _near(ev, fn[0], 0.5 * 10 ** -fn[1]):
        if rn.table >= 0:
            t = ev.tables[rn.table]
            keys = [t.rows[rn.row][j] for j in t.keys[:3] if j < len(t.rows[rn.row]) and t.rows[rn.row][j].strip()]
            return f"{rn.col} of {', '.join(k[:40] for k in keys)}"[:120]
        return rn.col.strip()[:80]
    return ""


def _fact_num(fact) -> tuple[float, int, int] | None:
    s = str(fact).strip().replace(",", "")
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", s):
        return None
    dp = len(s.split(".")[1]) if "." in s else 0
    return float(s), dp, _sig(s.lstrip("-").replace(".", ""), dp == 0)


def fact_matches(fact, text: str, labels: list[set] | None = None) -> bool:
    """Is a reference fact stated in the answer? Text facts (and dates, in all their spellings) as bench does; numbers
    within the answer's own rounding (21% for 21.4, -1.9 for 1.86, 0.13m for 129,444), and for a number of 3 or fewer
    significant digits a label of the fact (column or row words) within its line or table row, when labels are known."""
    opts = fact if isinstance(fact, list) else [fact]
    for o in opts:
        fn = _fact_num(o)
        if fn is None:
            if bench._has(o, text):
                return True
            continue
        f, fdp, fsig = fn
        lines = (text or "").splitlines()
        tabs = md_tables(text)
        for li, ln in enumerate(lines):
            for n in numbers(ln):
                if f == 0 or n.value == 0:
                    continue
                tol = max(n.tol, 0.5 * 10 ** -fdp) + (0.0015 * abs(f) if abs(f) >= 100 else 0) + 1e-9
                if n.pct and abs(f) <= 1 and not _ok(n.value, f, tol):
                    if not _ok(n.value / 100, f, n.tol / 100 + 1e-9):
                        continue
                elif not _ok(n.value, f, tol):
                    continue
                if n.dp < fdp and n.mult == 1 and n.sig < 2:
                    continue
                if fsig > 3 or not labels:
                    if fsig <= 3 and not labels and n.dp < fdp:
                        continue   # no label to check: a coarser rounding of a short fact is not enough
                    return True
                ctx, cap = ln, ""
                for t in tabs:   # a table row: the row and the figure's column header (the caption only at full precision)
                    if any(k == li for k, _ in t.rows):
                        cells = _cells(ln)
                        ci = next((i for i, c in enumerate(cells) if n.text in c), -1)
                        ctx += " " + (t.header[ci] if 0 <= ci < len(t.header) else "")
                        cap = t.caption
                w = tokens(ctx) | (tokens(cap) if n.dp >= fdp else set())
                if any(lab & w or _prefix_overlap(lab, w) for lab in labels if lab):
                    return True
    return False
