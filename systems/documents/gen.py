"""Documents system: supplier compliance document requirements per market (background) plus planted Ireland gaps in seed."""

DOC_TYPES = ["test_report", "certificate", "labelling_approval", "declaration_of_conformity"]
MARKETS = ["Germany", "France", "Netherlands", "Ireland"]


def generate(g):
    prods = g.master("products")
    rows = []
    n = 0
    # per-SKU streams: adding master products never changes which SKUs are picked or their rows
    pool = sorted((p for p in prods if p["status"] != "new"), key=lambda p: p["sku"])
    picked = sorted(pool, key=lambda p: g.rng_for("docreq_pick", p["sku"]).random())[:350]
    for p in sorted(picked, key=lambda p: p["sku"]):
        r = g.rng_for("docreq", p["sku"])
        for market in r.sample(MARKETS, 2):
            dt = r.choice(DOC_TYPES)
            # Ireland gaps are planted in seed/supplier_documents.csv only; elsewhere about one in six is missing.
            missing = market != "Ireland" and r.random() < 0.17
            n += 1
            due = g.days_ago(-r.randint(10, 60))
            rows.append({
                "doc_req_id": f"SDR-{n:06d}",
                "supplier_id": p["supplier_id"],
                "sku": p["sku"],
                "market_country": market,
                "document_type": dt,
                "status": "missing" if missing else "received",
                "required_by": due,
                "received_at": "" if missing else g.days_ago(r.randint(5, 120)),
            })
    return {"supplier_documents": rows, "contract_register": [], "documents": []}
