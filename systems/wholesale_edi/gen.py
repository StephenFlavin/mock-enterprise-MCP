"""Generate wholesale EDI data: orders, messages, and account metrics."""
from datetime import datetime, time, timedelta


def generate(g):
    r = g.rng
    fake = g.fake

    # Get active wholesale and marketplace partners
    partners = [p for p in g.master("partners") if p["type"] in ("wholesale", "marketplace") and p["status"] == "active"]
    products = g.master("products")
    skus = [p["sku"] for p in products]

    # Generate wholesale orders (for last 60 days and some future)
    orders = []
    order_counter = 0
    for partner in partners[:20]:  # Focus on active ones
        # Generate 3-8 orders per partner
        for _ in range(r.randint(3, 8)):
            order_counter += 1
            order_date = g.as_of - timedelta(days=r.randint(1, 60))
            sku = r.choice(skus)
            qty_ordered = r.randint(50, 500)

            # Allocation decision: mostly full, some partial, very few none
            alloc_choice = r.choices(["full", "partial", "none"], [70, 25, 5])[0]
            qty_allocated = qty_ordered if alloc_choice == "full" else (qty_ordered // 2 if alloc_choice == "partial" else 0)

            # Pick status: most are picked, some short or damaged
            pick_choice = r.choices(["picked", "short", "damaged"], [80, 15, 5])[0]
            qty_picked = qty_allocated if pick_choice == "picked" else (qty_allocated * 90 // 100 if pick_choice == "short" else 0)

            # Ship status: most picked are shipped
            qty_shipped = qty_picked if r.random() < 0.9 else (qty_picked * 95 // 100)

            # Status and shortfall reason
            if qty_shipped == qty_ordered:
                status = "delivered"
                shortfall_reason = None
            elif qty_shipped > 0:
                status = "partial"
                shortfall_reason = r.choice(["stock", "quality", "carrier"])
            else:
                status = "failed"
                shortfall_reason = r.choice(["stock", "quality"])

            carrier_id = r.choice([c["carrier_id"] for c in g.master("carriers") if c["mode"] == "road"])

            orders.append({
                "order_id": f"WOL-{order_counter:06d}",
                "partner_id": partner["partner_id"],
                "sku": sku,
                "order_date": order_date,
                "qty_ordered": qty_ordered,
                "qty_allocated": qty_allocated,
                "qty_picked": qty_picked,
                "qty_shipped": qty_shipped,
                "status": status,
                "shortfall_reason": shortfall_reason,
                "allocation_decision": alloc_choice,
                "pick_status": pick_choice,
                "carrier_id": carrier_id,
                "updated_at": order_date + timedelta(days=r.randint(0, 7)),
            })

    # Generate EDI messages
    messages = []
    message_counter = 0
    message_types = ["PO_ACK", "ASN", "INVOICE", "SHIP_NOTICE", "RECEIPT"]

    for partner in partners[:20]:
        # Generate 10-30 messages per partner
        for _ in range(r.randint(10, 30)):
            message_counter += 1
            sent_at = g.as_of - timedelta(days=r.randint(0, 30))
            msg_type = r.choice(message_types)

            # Status: mostly success, some failed/reprocessing
            status_choice = r.choices(["success", "failed", "reprocessing", "pending"], [80, 10, 7, 3])[0]

            if status_choice == "success":
                error_code = None
                error_reason = None
            else:
                error_code = r.choice(["MAPPING_ERROR", "FORMAT_ERROR", "VALIDATION_ERROR", "TIMEOUT", "DUPLICATE"])
                error_reason = f"EDI {msg_type} processing error: {error_code}"

            retry_count = r.randint(0, 3) if status_choice in ("failed", "reprocessing") else 0

            messages.append({
                "message_id": f"EDI-{message_counter:06d}",
                "partner_id": partner["partner_id"],
                "message_type": msg_type,
                "direction": r.choice(["inbound", "outbound"]),
                "sent_at": sent_at,
                "status": status_choice,
                "error_code": error_code,
                "error_reason": error_reason,
                "retry_count": retry_count,
                "updated_at": sent_at + timedelta(hours=r.randint(0, 48)),
            })

    # Generate EDI partner records
    edi_partners = []
    for partner in partners[:20]:
        # Most partners support multiple message types
        supported_types = r.sample(message_types, k=r.randint(2, len(message_types)))
        last_msg = r.choice(messages) if messages else None
        last_msg_date = last_msg["sent_at"] if last_msg else g.as_of

        # Count recent errors (failed or reprocessing from last 7 days)
        recent_errors = sum(1 for m in messages
                           if m["partner_id"] == partner["partner_id"]
                           and m["status"] in ("failed", "reprocessing")
                           and (g.as_of - (m["sent_at"].date() if isinstance(m["sent_at"], datetime) else m["sent_at"])).days <= 7)

        # Connection status based on recent errors
        if recent_errors > 5:
            conn_status = "failed"
        elif recent_errors > 2:
            conn_status = "degraded"
        else:
            conn_status = "ok"

        edi_partners.append({
            "partner_id": partner["partner_id"],
            "message_types": ",".join(supported_types),
            "last_message_date": last_msg_date,
            "status": partner["status"],
            "recent_error_count": recent_errors,
            "connection_status": conn_status,
        })

    # Generate wholesale account metrics
    accounts = []
    for partner in partners[:20]:
        account_value = r.randint(100_000, 2_000_000)
        sell_through = r.randint(100, 1000)
        stock_on_hand = r.randint(500, 5000)
        coverage_pct = r.randint(60, 100)

        # Feed status: mostly active, some stale, rare missing
        feed_choice = r.choices(["active", "stale", "missing"], [85, 12, 3])[0]
        days_since_feed = r.randint(0, 14) if feed_choice == "active" else (r.randint(15, 60) if feed_choice == "stale" else r.randint(61, 180))
        last_feed = g.as_of - timedelta(days=days_since_feed)

        accounts.append({
            "partner_id": partner["partner_id"],
            "account_value_gbp": float(account_value),
            "sell_through_units_week": sell_through,
            "stock_on_hand_units": stock_on_hand,
            "data_feed_coverage_pct": float(coverage_pct),
            "data_feed_status": feed_choice,
            "last_feed_date": last_feed,
            "updated_at": g.as_of,
        })

    return {
        "wholesale_orders": orders,
        "edi_messages": messages,
        "edi_partners": edi_partners,
        "wholesale_accounts": accounts,
        "short_shipment_notices": [],  # Will be populated by insert tool
    }
