"""Purchase order system data: requisitions, amendments, blocks, price history, confirmations."""
from datetime import datetime, timedelta
import random


def generate(g):
    """Generate PO system data."""
    r = g.rng
    fake = g.fake
    sites = g.master("sites")
    products = g.master("products")
    suppliers = g.master("suppliers")
    employees = g.master("employees")
    purchase_orders = g.master("purchase_orders")
    po_lines = g.master("po_lines")

    requisitions = []
    amendments = []
    blocks = []
    price_history = []
    confirmations = []
    commitments = []
    asns = []
    asn_lines = []
    pilot_markers = []

    # Generate purchase requisitions (for spare parts and supplies)
    categories = ["Spare Parts", "Supplies", "Packaging", "Safety Equipment", "IT Equipment"]
    for i in range(50):
        site = r.choice(sites)
        req = {
            "req_id": f"REQ-{i + 1:06d}",
            "site_id": site["site_id"],
            "category": r.choice(categories),
            "description": f"Requisition for {fake.word()}",
            "qty": r.randint(1, 100),
            "unit_cost_gbp": round(r.uniform(10, 500), 2),
            "status": r.choices(["draft", "submitted", "approved", "rejected", "ordered", "received"],
                               [0.1, 0.2, 0.4, 0.05, 0.15, 0.1])[0],
            "requested_by": r.choice(employees)["employee_id"],
            "requested_at": g.fake.date_time_this_year(),
            "approved_by": r.choice(employees)["employee_id"] if r.random() > 0.3 else None,
            "approved_at": None,
            "related_po_id": None,
            "notes": r.choice([None, f"Urgent: {fake.sentence()}"]),
            "updated_at": g.fake.date_time_this_year(),
        }
        req["total_cost_gbp"] = req["qty"] * req["unit_cost_gbp"]
        requisitions.append(req)

    # Generate amendments to existing POs
    for po in r.sample(purchase_orders, min(30, len(purchase_orders))):
        if po["status"] not in ("open", "confirmed", "shipped"):
            continue
        num_amendments = r.randint(0, 2)
        for j in range(num_amendments):
            amd_types = ["delivery_date", "ship_date", "quantity", "price", "other"]
            amd_type = r.choices(amd_types, [0.4, 0.2, 0.2, 0.1, 0.1])[0]

            old_val = ""
            new_val = ""
            cost_impact = 0

            if amd_type == "delivery_date":
                old_date = datetime.fromisoformat(po["due_date"])
                new_date = old_date + timedelta(days=r.randint(-10, 10))
                old_val = po["due_date"]
                new_val = new_date.date().isoformat()
            elif amd_type == "ship_date":
                old_date = datetime.fromisoformat(po["ship_date"])
                new_date = old_date + timedelta(days=r.randint(-5, 5))
                old_val = po["ship_date"]
                new_val = new_date.date().isoformat()
            elif amd_type == "quantity":
                old_val = str(po["total_units"])
                old_units = int(po["total_units"])
                new_units = int(old_units * r.uniform(0.7, 1.0))
                new_val = str(new_units)
                cost_impact = (new_units - old_units) * (float(po["total_value"]) / max(old_units, 1))
            elif amd_type == "price":
                old_val = str(round(po["total_value"], 2))
                pct_change = r.choice([-0.05, -0.02, 0.02, 0.05])
                new_val = str(round(po["total_value"] * (1 + pct_change), 2))
                cost_impact = float(new_val) - po["total_value"]

            amd = {
                "amendment_id": f"AMD-{len(amendments) + 1:06d}",
                "po_id": po["po_id"],
                "line_no": None,
                "amendment_type": amd_type,
                "old_value": old_val,
                "new_value": new_val,
                "reason": r.choice(["Market demand change", "Supplier availability", "Cost reduction",
                                   "Quality issue", "Delivery delay", "Forecasting adjustment"]),
                "requested_by": r.choice(employees)["employee_id"],
                "requested_at": g.fake.date_time_this_year(),
                "approved_by": r.choice(employees)["employee_id"] if r.random() > 0.2 else None,
                "approved_at": None,
                "status": r.choices(["requested", "approved", "rejected", "implemented"],
                                  [0.2, 0.5, 0.1, 0.2])[0],
                "supplier_confirmed_at": None,
                "cost_impact_gbp": cost_impact,
                "updated_at": g.fake.date_time_this_year(),
            }
            amendments.append(amd)

    # Generate PO blocks
    for po in r.sample(purchase_orders, min(10, len(purchase_orders))):
        if po["status"] not in ("open", "confirmed"):
            continue
        block = {
            "block_id": f"BLK-{len(blocks) + 1:06d}",
            "po_id": po["po_id"],
            "block_type": r.choice(["supplier", "factory", "other"]),
            "block_reason": r.choice(["Due diligence review", "Quality hold", "Compliance check",
                                     "Forced labour risk", "Supplier capacity", "Payment pending"]),
            "blocked_by": r.choice(employees)["employee_id"],
            "blocked_at": g.fake.date_time_this_year(),
            "unblock_approval_required": r.random() > 0.5,
            "unblocked_by": None,
            "unblocked_at": None,
            "status": r.choices(["active", "released", "expired"], [0.6, 0.3, 0.1])[0],
            "notes": None,
            "updated_at": g.fake.date_time_this_year(),
        }
        blocks.append(block)

    # Generate price history for SKUs from POs
    sku_po_map = {}
    for pl in po_lines:
        sku = pl["sku"]
        if sku not in sku_po_map:
            sku_po_map[sku] = []
        sku_po_map[sku].append(pl)

    for sku, po_line_list in list(sku_po_map.items())[:40]:
        product = next((p for p in products if p["sku"] == sku), None)
        if not product:
            continue

        for occurrence, pl in enumerate(po_line_list[:3], 1):
            po = next((p for p in purchase_orders if p["po_id"] == pl["po_id"]), None)
            if not po:
                continue

            quoted_cost = float(pl["unit_cost"])
            variance = r.gauss(0, 0.08)  # 8% std dev
            actual_cost = quoted_cost * (1 + variance)

            ph = {
                "po_id": pl["po_id"],
                "line_no": pl["line_no"],
                "sku": sku,
                "occurrence": occurrence,
                "order_date": po["order_date"],
                "quoted_unit_cost_gbp": quoted_cost,
                "actual_unit_cost_gbp": max(0.01, actual_cost),
                "qty_ordered": int(pl["qty_ordered"]),
                "qty_received": int(pl["qty_received"]),
                "variance_pct": round((actual_cost - quoted_cost) / quoted_cost * 100, 1) if quoted_cost else 0,
                "supplier_id": po["supplier_id"],
                "invoice_date": (datetime.fromisoformat(po["order_date"]) + timedelta(days=r.randint(5, 20))).date().isoformat(),
                "received_date": None,
                "updated_at": g.fake.date_time_this_year(),
            }
            if po["status"] in ("received", "closed"):
                ph["received_date"] = (datetime.fromisoformat(po["due_date"]) + timedelta(days=r.randint(-5, 10))).date().isoformat()

            price_history.append(ph)

    # Generate supplier confirmations
    for po in r.sample(purchase_orders, min(25, len(purchase_orders))):
        if po["status"] not in ("open", "confirmed", "shipped"):
            continue

        cnf = {
            "confirmation_id": f"CNF-{len(confirmations) + 1:06d}",
            "po_id": po["po_id"],
            "supplier_id": po["supplier_id"],
            "confirmation_type": r.choice(["order", "shipment", "asn"]),
            "confirmed_ship_date": (datetime.fromisoformat(po["ship_date"]) + timedelta(days=r.randint(-3, 3))).date().isoformat(),
            "confirmed_delivery_date": (datetime.fromisoformat(po["due_date"]) + timedelta(days=r.randint(-5, 5))).date().isoformat(),
            "status": r.choices(["requested", "received", "superseded", "rejected"], [0.2, 0.6, 0.1, 0.1])[0],
            "requested_at": g.fake.date_time_this_year(),
            "received_at": g.fake.date_time_this_year() if r.random() > 0.3 else None,
            "notes": r.choice([None, "On track", "Slight delay expected"]),
            "updated_at": g.fake.date_time_this_year(),
        }
        confirmations.append(cnf)

    # Generate commodity commitments
    commodities = ["Cotton", "Polyester", "Steel", "Cardboard", "Plastic", "Rubber", "Leather", "Wood"]
    for supplier in r.sample(suppliers, min(15, len(suppliers))):
        for _ in range(r.randint(0, 2)):
            start = g.fake.date_this_year()
            end = (datetime.fromisoformat(start.isoformat()) + timedelta(days=r.randint(90, 365))).date()

            comm = {
                "commitment_id": f"COM-{len(commitments) + 1:06d}",
                "supplier_id": supplier["supplier_id"],
                "commodity": r.choice(commodities),
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "volume_units": r.randint(100, 10000),
                "volume_uom": r.choice(["tonnes", "meters", "units", "cartons"]),
                "price_gbp_per_unit": round(r.uniform(1, 100), 2),
                "used_to_date": r.randint(0, 5000),
                "status": r.choices(["active", "partially_used", "fulfilled", "expired"], [0.5, 0.3, 0.1, 0.1])[0],
                "notes": None,
                "updated_at": g.fake.date_time_this_year(),
            }
            comm["remaining_volume"] = comm["volume_units"] - comm["used_to_date"]
            commitments.append(comm)

    # Generate advance shipping notices
    for po in r.sample(purchase_orders, min(20, len(purchase_orders))):
        if po["status"] not in ("confirmed", "shipped", "received"):
            continue

        asn = {
            "asn_id": f"ASN-{len(asns) + 1:06d}",
            "po_id": po["po_id"],
            "supplier_id": po["supplier_id"],
            "asn_number": f"ASN-{fake.numerify('###')}",
            "shipment_id": None,
            "advised_at": g.fake.date_time_this_year(),
            "expected_delivery_date": (datetime.fromisoformat(po["due_date"]) + timedelta(days=r.randint(-3, 7))).date().isoformat(),
            "status": r.choices(["received", "delivered", "cancelled"], [0.3, 0.6, 0.1])[0],
            "updated_at": g.fake.date_time_this_year(),
        }
        asns.append(asn)

        # Add ASN line items
        po_line_subset = [pl for pl in po_lines if pl["po_id"] == po["po_id"]]
        for pl in po_line_subset[:r.randint(1, len(po_line_subset))]:
            asn_line = {
                "asn_id": asn["asn_id"],
                "line_no": len(asn_lines) + 1,
                "po_line_no": pl["line_no"],
                "sku": pl["sku"],
                "qty_advised": int(int(pl["qty_ordered"]) * r.uniform(0.9, 1.1)),
                "qty_received": 0,
                "batch_no": f"BATCH-{fake.numerify('###-###')}",
                "updated_at": g.fake.date_time_this_year(),
            }
            asn_lines.append(asn_line)

    # Generate nearshore pilot markers
    nearshore_suppliers = r.sample(suppliers, min(5, len(suppliers)))
    pilot_programs = ["Nearshore Pilot Q1", "Nearshore Expansion", "Central America Initiative"]

    for supplier in nearshore_suppliers:
        po_subset = [p for p in purchase_orders if p["supplier_id"] == supplier["supplier_id"]]
        for po in r.sample(po_subset, min(2, len(po_subset))):
            marker = {
                "marker_id": f"MRK-{len(pilot_markers) + 1:06d}",
                "po_id": po["po_id"],
                "supplier_id": supplier["supplier_id"],
                "pilot_program": r.choice(pilot_programs),
                "start_date": g.fake.date_this_year(),
                "status": r.choices(["active", "completed", "cancelled"], [0.6, 0.3, 0.1])[0],
                "notes": r.choice([None, "On track", "Performance monitoring"]),
                "updated_at": g.fake.date_time_this_year(),
            }
            pilot_markers.append(marker)

    return {
        "purchase_requisitions": requisitions,
        "po_amendments": amendments,
        "po_blocks": blocks,
        "po_price_history": price_history,
        "supplier_confirmations": confirmations,
        "commodity_commitments": commitments,
        "advance_shipping_notices": asns,
        "asn_line_items": asn_lines,
        "nearshore_pilot_markers": pilot_markers,
    }
