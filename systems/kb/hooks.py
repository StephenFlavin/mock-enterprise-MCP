"""Keyword search over the knowledge base, KPI definitions and clause library.

Results are returned as plain text so the full article / clause wording is shown
(table output would cut long cells at 300 characters).
"""
import math
import re

_STOP = {"the", "and", "for", "with", "our", "are", "from", "that", "this", "what", "how", "any", "can",
         "does", "into", "about", "per", "vs", "versus", "his", "her", "their", "its", "was", "has", "have"}


def _words(query):
    ws = []
    for w in re.findall(r"[\w][\w.\-]*", (query or "").lower()):
        w = w.strip(".-")
        if len(w) >= 2 and w not in _STOP and w not in ws:
            ws.append(w)
    return ws


def _score(words, *texts):
    blob = " ".join(t or "" for t in texts).lower()
    def hit(w):
        if len(w) <= 3:  # short words (ip, ppe) must match whole words, not fragments of other words
            return re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", blob) is not None
        return w in blob or (len(w) > 4 and w.endswith("s") and w[:-1] in blob)
    return sum(1 for w in words if hit(w))


def _rank(rows, words, fields, title_field):
    """Keep rows matching at least half of the words (all of them when there are one or two), best first."""
    if not words:
        return rows
    need = max(1, math.ceil(len(words) * 0.6)) if len(words) > 2 else len(words)
    scored = []
    for r in rows:
        s = _score(words, *[str(r.get(f) or "") for f in fields])
        t = _score(words, str(r.get(title_field) or ""))
        if s >= need:
            scored.append((s, t, r))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    return [r for _, _, r in scored]


def _articles(ctx, query, category, status, limit):
    rows = ctx.q("""SELECT article_id, title, category, content, status, updated_at
                    FROM knowledge_base_articles
                    WHERE ($category IS NULL OR lower(category) = lower($category))
                      AND ($status IS NULL OR status = $status)
                    ORDER BY updated_at DESC""", category=category, status=status)
    hits = _rank(rows, _words(query), ["title", "content"], "title")
    if not hits:
        cats = sorted({r["category"] for r in rows})
        return ("No matching articles. Try fewer or different keywords"
                + (f", or drop the category filter (categories here: {', '.join(cats)})." if category else "."))
    shown = hits[: limit or 5]
    head = f"{len(shown)} article(s)" + (f" (of {len(hits)} matching; use limit= for more)" if len(hits) > len(shown) else "") + "."
    out = [head]
    for r in shown:
        out.append(f"\n[{r['article_id']}] {r['title']}\ncategory: {r['category']} | status: {r['status']} | updated: {str(r['updated_at'])[:10]}\n{r['content']}")
    return "\n".join(out)


def search_kb(ctx, query=None, category=None, status="published", limit=5):
    return _articles(ctx, query, category, status, limit)


def search_kpis(ctx, query=None, limit=8):
    rows = ctx.q("""SELECT kpi_id, kpi_name, definition, formula, data_source, unit, effective_date, version
                    FROM kpi_definitions WHERE effective_date <= CAST($as_of AS DATE) ORDER BY kpi_name""")
    hits = _rank(rows, _words(query), ["kpi_name", "definition", "formula", "data_source"], "kpi_name")
    if not hits:
        return "No matching KPI definitions. Try fewer or different keywords (e.g. cost, productivity, accuracy)."
    shown = hits[: limit or 8]
    out = [f"{len(shown)} KPI definition(s)" + (f" (of {len(hits)} matching)" if len(hits) > len(shown) else "") + "."]
    for r in shown:
        out.append(f"\n[{r['kpi_id']}] {r['kpi_name']} (unit: {r['unit']}, version {r['version']}, effective {str(r['effective_date'])[:10]})\n"
                   f"definition: {r['definition']}\nformula: {r['formula']}\ndata source: {r['data_source']}")
    return "\n".join(out)


def clause_library(ctx, query=None, clause_type=None, limit=20):
    rows = ctx.q("""SELECT clause_id, clause_name, clause_type, wording, effective_date, version
                    FROM standard_clauses
                    WHERE ($clause_type IS NULL OR lower(clause_type) = lower($clause_type))
                      AND effective_date <= CAST($as_of AS DATE)
                    ORDER BY clause_name""", clause_type=clause_type)
    hits = _rank(rows, _words(query), ["clause_name", "wording"], "clause_name")
    if not hits:
        return "No matching clauses. Try fewer keywords or omit them to list the whole library."
    shown = hits[: limit or 20]
    out = [f"{len(shown)} clause(s)" + (f" (of {len(hits)})" if len(hits) > len(shown) else "") + "."]
    for r in shown:
        out.append(f"\n[{r['clause_id']}] {r['clause_name']} ({r['clause_type']}, v{r['version']}, effective {str(r['effective_date'])[:10]})\n{r['wording']}")
    return "\n".join(out)
