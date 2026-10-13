"""Generate wholesale EDI data: background orders, EDI traffic, endpoints and account metrics.

Story rows (seed/*.csv): PTN-001's last four short orders (08:75:Q1), three open orders for SKU-100035 (08:75:Q2),
ten key accounts (08:75:Q4). The overnight PO_ACK incident (09:83:Q1: 200 failures, 171 mapping, 17 format,
12 partner-side, 38 suppliers) is generated here with fixed counts and ids EDI-900001..EDI-900200.
"""
from datetime import datetime, time, timedelta

STORY_PARTNERS = {"PTN-001", "PTN-002", "PTN-004", "PTN-005"}   # their orders are all in seed
STORY_SKUS = {"SKU-100469", "SKU-100476", "SKU-100483", "SKU-100035"}
KEY_ACCOUNTS = {f"PTN-{i:03d}" for i in range(1, 11)}            # accounts are all in seed
CATEGORY = {"MAPPING_ERROR": "mapping", "FORMAT_ERROR": "format", "VALIDATION_ERROR": "format",
            "TIMEOUT": "connectivity", "DUPLICATE": "other"}
PARTNER_TYPES = ["INVOICE", "SHIP_NOTICE", "RECEIPT"]
SUPPLIER_TYPES = ["PO_ACK", "ASN", "INVOICE"]


def generate(g):
    r = g.rng
    today = g.as_of
    all_partners = [p for p in g.master("partners") if p["type"] in ("wholesale", "marketplace")]
    active = [p for p in all_partners if p["status"] == "active"]
    skus = [p["sku"] for p in g.master("products") if p["sku"] not in STORY_SKUS]
    roads = [c["carrier_id"] for c in g.master("carriers") if c["mode"] == "road"]
    suppliers = g.master("suppliers")[:40]

    # ---- background wholesale orders (story partners and story SKUs are in seed)
    orders = []
    for partner in active:
        if partner["partner_id"] in STORY_PARTNERS:
            continue
        for _ in range(r.randint(3, 8)):
            order_date = today - timedelta(days=r.randint(1, 60))
            qty = r.randint(50, 500)
            alloc = r.choices(["full", "partial", "none"], [75, 22, 3])[0]
            qa = qty if alloc == "full" else (qty // 2 if alloc == "partial" else 0)
            pick = r.choices(["picked", "short", "damaged"], [80, 15, 5])[0]
            qp = qa if pick == "picked" else (qa * 90 // 100 if pick == "short" else qa * 95 // 100)
            qs = qp
            if qs == qty:
                status, reason = "delivered", None
            elif qs > 0:
                status, reason = "partial", ("stock" if alloc != "full" else r.choice(["quality", "other"]))
            else:
                status, reason = "failed", "stock"
            orders.append({
                "order_id": f"WOL-{len(orders) + 1:06d}", "partner_id": partner["partner_id"], "sku": r.choice(skus),
                "order_date": order_date, "qty_ordered": qty, "qty_allocated": qa, "qty_picked": qp,
                "qty_shipped": qs, "qty_delivered": qs, "status": status, "shortfall_reason": reason,
                "allocation_decision": alloc, "pick_status": pick, "carrier_id": r.choice(roads),
                "updated_at": order_date + timedelta(days=r.randint(1, 7)),
            })

    # ---- EDI endpoints
    endpoints = []
    for p in all_partners:
        endpoints.append({"endpoint_id": f"EP-{p['partner_id']}", "partner_id": p["partner_id"], "supplier_id": None,
                          "partner_type": p["type"], "kind_types": PARTNER_TYPES,
                          "status": {"active": "active", "on_hold": "suspended"}.get(p["status"], "inactive")})
    for i, s in enumerate(suppliers):
        types = ["PO_ACK", "INVOICE"] + (["ASN"] if i % 4 != 3 else [])
        endpoints.append({"endpoint_id": f"EP-{s['supplier_id']}", "partner_id": None, "supplier_id": s["supplier_id"],
                          "partner_type": "supplier", "kind_types": types,
                          "status": {"active": "active", "blocked": "suspended"}.get(s["status"], "inactive")})

    # ---- background EDI traffic; failures only older than 8 days so the overnight incident stands alone
    messages = []

    def add(ep, mt, sent_at, status, code=None, reason=None, retry=0, **extra):
        messages.append({
            "message_id": f"EDI-{len(messages) + 1:06d}", "partner_id": ep["partner_id"], "supplier_id": ep["supplier_id"],
            "message_type": mt, "direction": "inbound" if ep["supplier_id"] else r.choice(["inbound", "outbound"]),
            "sent_at": sent_at, "status": status, "error_code": code, "error_category": CATEGORY.get(code) if code else None,
            "error_reason": reason, "retry_count": retry, "retry_reason": None,
            "updated_at": sent_at + timedelta(hours=r.randint(0, 24)), **extra})

    for ep in endpoints:
        if ep["status"] != "active":
            continue
        types = ["PO_ACK", "ASN", "INVOICE"] if ep["supplier_id"] else PARTNER_TYPES
        types = [t for t in types if t in ep["kind_types"]]
        for _ in range(r.randint(10, 22)):
            sent = datetime.combine(today - timedelta(days=r.randint(0, 30)), time(r.randint(6, 18), r.randint(0, 59)))
            mt = r.choice(types)
            old = (today - sent.date()).days >= 8
            roll = r.random()
            if roll < 0.07 and old:
                code = r.choice(["MAPPING_ERROR", "FORMAT_ERROR", "VALIDATION_ERROR", "TIMEOUT", "DUPLICATE"])
                add(ep, mt, sent, "failed", code, f"EDI {mt} processing error: {code}", r.randint(0, 3))
            elif roll < 0.10 and old:
                code = r.choice(["MAPPING_ERROR", "FORMAT_ERROR", "TIMEOUT"])
                add(ep, mt, sent, "reprocessing", code, f"EDI {mt} processing error: {code}", r.randint(1, 3))
            elif roll < 0.12:
                add(ep, mt, sent, "pending")
            else:
                add(ep, mt, sent, "success")

    # ---- story 09:83:Q1: PO_ACK map v1.1 went live the evening before, 200 supplier acknowledgements fail overnight
    sup_eps = [e for e in endpoints if e["supplier_id"]]
    story_eps = sup_eps[:38]
    jobs = []
    for i in range(171):                                    # mapping: spread over all 38 suppliers
        jobs.append((story_eps[i % 38], "MAPPING_ERROR", "mapping",
                     "ACK_STATUS code not in PO_ACK map v1.1 code list (expected AC, AP or RJ)"))
    for i in range(17):                                     # format: 17 different suppliers
        jobs.append((story_eps[(i * 2) % 38], "FORMAT_ERROR", "format", "XML validation failed: invalid date format in DTM segment"))
    for i in range(12):                                     # partner-side: three suppliers whose endpoint returns HTTP 500
        jobs.append((story_eps[[3, 14, 29][i % 3]], "PARTNER_ERROR", "partner_side", "Partner endpoint returned HTTP 500"))
    r.shuffle(jobs)
    # overnight = the early hours of the world's today (data date + today_offset_days), the night after the evening go-live
    start = datetime.combine(today + timedelta(days=int(g.world.get("today_offset_days", 0))), time(1, 20))
    for i, (ep, code, cat, reason) in enumerate(jobs):
        sent = start + timedelta(seconds=int(i * (3.5 * 3600) / 200) + r.randint(0, 40))
        messages.append({
            "message_id": f"EDI-{900001 + i:06d}", "partner_id": None, "supplier_id": ep["supplier_id"],
            "message_type": "PO_ACK", "direction": "inbound", "sent_at": sent, "status": "failed", "error_code": code,
            "error_category": cat, "error_reason": reason, "retry_count": 0, "retry_reason": None,
            "updated_at": sent + timedelta(seconds=r.randint(5, 900))})
    for i in range(14):                                     # acknowledgements that still processed
        ep = r.choice(story_eps)
        sent = start + timedelta(seconds=r.randint(0, 3 * 3600 + 1800))
        messages.append({
            "message_id": f"EDI-{900201 + i:06d}", "partner_id": None, "supplier_id": ep["supplier_id"],
            "message_type": "PO_ACK", "direction": "inbound", "sent_at": sent, "status": "success", "retry_count": 0,
            "updated_at": sent + timedelta(seconds=r.randint(5, 900))})

    # ---- endpoint summary derived from the messages
    edi_partners = []
    for ep in endpoints:
        mine = [m for m in messages if m["partner_id"] == ep["partner_id"] and m["supplier_id"] == ep["supplier_id"]]
        recent = [m for m in mine if (today - m["sent_at"].date()).days <= 7]
        errors = [m for m in recent if m["status"] in ("failed", "reprocessing")]
        link = sum(1 for m in errors if m["error_category"] in ("partner_side", "connectivity"))
        edi_partners.append({
            "endpoint_id": ep["endpoint_id"], "partner_id": ep["partner_id"], "supplier_id": ep["supplier_id"],
            "partner_type": ep["partner_type"], "message_types": ",".join(ep["kind_types"]),
            "last_message_date": max((m["sent_at"] for m in mine), default=None), "status": ep["status"],
            "recent_error_count": len(errors),
            "connection_status": "failed" if link >= 3 else ("degraded" if link >= 1 else "ok")})

    # ---- accounts for non-key partners (key accounts are in seed)
    accounts = []
    for partner in active:
        if partner["partner_id"] in KEY_ACCOUNTS:
            continue
        feed = r.choices(["active", "stale", "missing"], [85, 12, 3])[0]
        days = r.randint(0, 6) if feed == "active" else (r.randint(15, 60) if feed == "stale" else r.randint(61, 180))
        accounts.append({
            "partner_id": partner["partner_id"], "account_value_gbp": float(r.randint(100_000, 600_000)),
            "sell_through_units_week": r.randint(100, 600), "stock_on_hand_units": r.randint(500, 3000),
            "data_feed_coverage_pct": float(r.randint(60, 100)), "data_feed_status": feed, "is_key_account": False,
            "last_feed_date": today - timedelta(days=days), "updated_at": today})

    return {"wholesale_orders": orders, "edi_messages": messages, "edi_partners": edi_partners,
            "wholesale_accounts": accounts, "short_shipment_notices": []}
