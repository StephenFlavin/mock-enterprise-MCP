"""Purchase order system data: requisitions, amendments, holds, approvals, price history, confirmations, ASNs.

Everything is derived from master purchase orders / lines / shipments so the PO system agrees with them.
All dates are relative to g.as_of (never the wall clock), so the output is deterministic.
Story rows (late orders, slipped ship dates, late changes, retrospective price adjustments) live in seed/*.csv;
the generator leaves the story POs / suppliers alone so seed and background never contradict each other.
"""
from datetime import date, datetime, timedelta

# Suppliers / POs whose confirmations, amendments and holds are written by hand in seed/*.csv.
STORY_SUPPLIERS = {"SUP-0070", "SUP-0027", "SUP-0045", "SUP-0076", "SUP-0022", "SUP-0034"}
STORY_FACTORIES = {"FAC-0104", "FAC-0021"}
STORY_POS = {"PO-2026-004072", "PO-2026-004312", "PO-2026-004062", "PO-2026-005154", "PO-2026-004663"}
NEARSHORE = ["SUP-0044", "SUP-0058", "SUP-0079", "SUP-0040", "SUP-0039"]
OPEN = ("open", "confirmed", "shipped")
DONE = ("received", "closed")


def d(s):
    return date.fromisoformat(s[:10]) if s else None


def ts(day, rng, lo=8, hi=17):
    return f"{day.isoformat()} {rng.randint(lo, hi):02d}:{rng.choice([0, 15, 30, 45]):02d}:00"


def generate(g):
    r = g.rng
    as_of = g.as_of
    sites = [s for s in g.master("sites") if s["type"] in ("dc", "store")]
    employees = g.master("employees")
    buyers = [e["employee_id"] for e in employees if e["role"] == "Buyer"]
    approvers = [e["employee_id"] for e in employees if e["role"] in ("Category Manager", "Sourcing Manager")]
    keepers = [e["employee_id"] for e in employees if e["role"] in ("Warehouse Manager", "Shift Manager")]
    suppliers = {s["supplier_id"]: s for s in g.master("suppliers")}
    products = {p["sku"]: p for p in g.master("products")}
    pos = g.master("purchase_orders")
    po_by_id = {p["po_id"]: p for p in pos}
    lines = {}
    for ln in g.master("po_lines"):
        lines.setdefault(ln["po_id"], []).append(ln)
    ship = {s["po_id"]: s for s in g.master("shipments")}

    # ---------------------------------------------------------------- requisitions
    items = {
        "Spare Parts": ["Conveyor roller bearing", "Shuttle drive belt", "Safety light curtain sensor", "Pallet truck wheel set",
                        "Dock leveller hydraulic hose", "Scanner battery pack"],
        "Supplies": ["Stretch wrap rolls", "Thermal label rolls", "Pallet strapping", "Cable ties pack", "Cleaning supplies"],
        "Packaging": ["Flat-pack cartons", "Void-fill paper", "Polybag 300x400", "Tamper-evident tape"],
        "Safety Equipment": ["Hi-vis vests", "Safety boots (pair)", "First-aid refill kit", "Cut-resistant gloves"],
        "IT Equipment": ["Handheld scanner", "Label printer", "Rugged tablet", "Wi-Fi access point"],
    }
    reqs = []
    for i in range(48):
        cat = r.choice(list(items))
        site = r.choice(sites)
        status = r.choices(["draft", "submitted", "approved", "rejected", "ordered", "received"], [1, 2, 4, 1, 1.5, 1])[0]
        asked = as_of - timedelta(days=r.randint(2, 150))
        decided = asked + timedelta(days=r.randint(1, 6))
        decided = min(decided, as_of)
        done = status in ("approved", "ordered", "received")
        reqs.append({
            "req_id": f"REQ-{i + 1:06d}", "site_id": site["site_id"], "category": cat, "description": r.choice(items[cat]),
            "qty": r.choice([2, 4, 5, 10, 12, 20, 25, 50]), "unit_cost_gbp": round(r.uniform(6, 480), 2),
            "priority": r.choices(["low", "medium", "high", "urgent"], [2, 5, 2, 1])[0], "status": status,
            "requested_by": r.choice(keepers + buyers), "requested_at": ts(asked, r),
            "approved_by": r.choice(approvers) if done or status == "rejected" else None,
            "approved_at": ts(decided, r) if done or status == "rejected" else None,
            "related_po_id": None, "notes": r.choice([None, None, "Needed before peak", "Replaces worn part"]),
            "updated_at": ts(max(decided, asked), r)})

    # ---------------------------------------------------------------- amendments (consistent with master final values)
    amendments = []
    reasons = {
        "delivery_date": ["Supplier capacity", "Fabric delayed at mill", "Port congestion", "Our request: promotion moved"],
        "ship_date": ["Supplier capacity", "Production delayed", "Our request: re-phased delivery"],
        "quantity": ["Forecast revision", "Market demand change", "Supplier material shortage"],
        "price": ["Raw material increase", "Volume discount applied", "Currency adjustment"],
    }
    pool = [p for p in pos if p["status"] in OPEN + DONE and p["supplier_id"] not in STORY_SUPPLIERS
            and p["factory_id"] not in STORY_FACTORIES and p["po_id"] not in STORY_POS]
    for po in r.sample(pool, 90):
        atype = r.choices(["delivery_date", "ship_date", "quantity", "price"], [4, 2, 2, 1])[0]
        order_d, ship_d, due_d = d(po["order_date"]), d(po["ship_date"]), d(po["due_date"])
        asked = order_d + timedelta(days=r.randint(3, max(4, (ship_d - order_d).days - 2)))
        asked = min(asked, as_of)
        status = r.choices(["implemented", "approved", "rejected", "requested"], [6, 2, 1, 1])[0]
        if atype == "delivery_date":
            shift = r.randint(3, 21)
            old, new = (due_d - timedelta(days=shift), due_d) if status in ("implemented", "approved") else (due_d, due_d + timedelta(days=shift))
            old, new, impact = old.isoformat(), new.isoformat(), 0
        elif atype == "ship_date":
            shift = r.randint(2, 14)
            old, new = (ship_d - timedelta(days=shift), ship_d) if status in ("implemented", "approved") else (ship_d, ship_d + timedelta(days=shift))
            old, new, impact = old.isoformat(), new.isoformat(), 0
        elif atype == "quantity":
            units = int(po["total_units"])
            other = int(units * r.choice([0.8, 0.9, 1.1, 1.2]) // 500 * 500) or 500
            old, new = (other, units) if status in ("implemented", "approved") else (units, other)
            val = float(po["total_value"])
            impact = round((new - old) * val / max(units, 1), 2)
            old, new = str(old), str(new)
        else:
            val = float(po["total_value"])
            pct = r.choice([-0.03, -0.02, 0.02, 0.03])
            old, new = (round(val / (1 + pct), 2), round(val, 2)) if status in ("implemented", "approved") else (round(val, 2), round(val * (1 + pct), 2))
            impact, old, new = round(new - old, 2), str(old), str(new)
        amendments.append({
            "amendment_id": f"AMD-{len(amendments) + 1:06d}", "po_id": po["po_id"], "line_no": None, "amendment_type": atype,
            "old_value": old, "new_value": new, "reason": r.choice(reasons[atype]),
            "requested_by": r.choice(buyers), "requested_at": ts(asked, r),
            "approved_by": r.choice(approvers) if status != "requested" else None,
            "approved_at": ts(asked + timedelta(days=1), r) if status != "requested" else None,
            "status": status,
            "supplier_confirmed_at": ts(asked + timedelta(days=2), r) if status == "implemented" else None,
            "cost_impact_gbp": impact, "updated_at": ts(asked + timedelta(days=2), r)})

    # ---------------------------------------------------------------- holds (background: a few quality / compliance holds)
    blocks = []
    candidates = [p for p in pos if p["status"] in ("open", "confirmed") and p["supplier_id"] not in STORY_SUPPLIERS
                  and p["factory_id"] not in STORY_FACTORIES and suppliers[p["supplier_id"]]["status"] == "active"]
    for po in r.sample(candidates, 4):
        when = as_of - timedelta(days=r.randint(5, 40))
        released = r.random() < 0.4
        blocks.append({
            "block_id": f"BLK-{len(blocks) + 1:06d}", "po_id": po["po_id"], "supplier_id": po["supplier_id"],
            "factory_id": po["factory_id"], "block_type": "other",
            "block_reason": r.choice(["Quality hold - inspection pending", "Payment pending", "Pricing query with supplier"]),
            "blocked_by": r.choice(buyers), "blocked_at": ts(when, r), "unblock_approval_required": False,
            "unblocked_by": r.choice(buyers) if released else None,
            "unblocked_at": ts(when + timedelta(days=r.randint(2, 9)), r) if released else None,
            "status": "released" if released else "active", "notes": None, "updated_at": ts(when, r)})

    # ---------------------------------------------------------------- price history: one row per PO line placed
    # quoted = the unit price on the PO line (master); actual = invoiced unit price. Most variances are noise.
    placed = [p for p in pos if p["status"] in OPEN + DONE]
    drift = {"SUP-0017", "SUP-0053", "SUP-0073", "SUP-0077", "SUP-0080"}      # suppliers pushing prices up this year
    appliance_sup = {p["supplier_id"] for p in products.values() if p["category"] == "Small Appliances"}
    rows_by_sku = {}
    for po in placed:
        for ln in lines.get(po["po_id"], []):
            rows_by_sku.setdefault(ln["sku"], []).append((po, ln))
    reversal_skus = sorted(s for s, v in rows_by_sku.items() if len(v) >= 8)[3:9]
    price_history = []
    for sku, items_ in rows_by_sku.items():
        items_.sort(key=lambda x: (x[0]["order_date"], x[0]["po_id"]))
        for occ, (po, ln) in enumerate(items_, 1):
            quoted = float(ln["unit_cost"])
            age = (as_of - d(po["order_date"])).days
            var = r.gauss(0, 0.004)
            if po["supplier_id"] in drift and age <= 270:
                var += 0.10 * (1 - age / 270)                       # ramps from 0 to about +10%
            elif po["supplier_id"] in appliance_sup and age <= 180:
                var += 0.025
            if sku in reversal_skus:
                var += -0.06 if 90 <= age <= 240 else 0.0           # a saving that was later given back
            actual = round(quoted * (1 + var), 4)
            done = po["status"] in DONE
            arrived = d(ship[po["po_id"]]["ata"]) if done and po["po_id"] in ship and ship[po["po_id"]]["ata"] else None
            price_history.append({
                "po_id": po["po_id"], "line_no": int(ln["line_no"]), "sku": sku, "occurrence": occ, "order_date": po["order_date"],
                "quoted_unit_cost": round(quoted, 4), "actual_unit_cost": actual, "currency": po["currency"],
                "qty_ordered": int(ln["qty_ordered"]), "qty_received": int(ln["qty_received"]),
                "variance_pct": round((actual - quoted) / quoted * 100, 2) if quoted else 0.0,
                "supplier_id": po["supplier_id"],
                "invoice_date": (arrived + timedelta(days=r.randint(3, 20))).isoformat() if arrived and arrived + timedelta(days=3) <= as_of else None,
                "received_date": arrived.isoformat() if arrived else None, "updated_at": ts(min(as_of, d(po["order_date"]) + timedelta(days=30)), r)})

    # ---------------------------------------------------------------- confirmations (open orders get an order confirmation)
    confirmations = []
    for po in pos:
        if po["status"] not in OPEN or po["supplier_id"] in STORY_SUPPLIERS or po["po_id"] in STORY_POS:
            continue
        if r.random() > 0.55:
            continue
        due_d, ship_d, order_d = d(po["due_date"]), d(po["ship_date"]), d(po["order_date"])
        asked = min(order_d + timedelta(days=1), as_of)
        got = r.random() < 0.85
        slip = r.choices([0, 2, 5, 9], [70, 15, 10, 5])[0]
        confirmations.append({
            "confirmation_id": f"CNF-{len(confirmations) + 1:06d}", "po_id": po["po_id"], "supplier_id": po["supplier_id"],
            "confirmation_type": "order",
            "confirmed_ship_date": (ship_d + timedelta(days=slip)).isoformat() if got else None,
            "confirmed_delivery_date": (due_d + timedelta(days=slip)).isoformat() if got else None,
            "status": "received" if got else "requested", "requested_at": ts(asked, r),
            "received_at": ts(min(asked + timedelta(days=r.randint(1, 4)), as_of), r) if got else None,
            "notes": ("Slight delay at factory" if slip else "On track") if got else None, "updated_at": ts(min(asked + timedelta(days=3), as_of), r)})

    # ---------------------------------------------------------------- commodity commitments
    commodity_for = {"Womenswear": ["Cotton", "Polyester"], "Menswear": ["Cotton", "Polyester"], "Kids": ["Cotton", "Polyester"],
                     "Accessories": ["Leather", "Polyester"], "Home": ["Cotton", "Steel", "Plastic"],
                     "Electricals": ["Plastic", "Steel", "Copper"], "Beauty": ["Plastic", "Cardboard"]}
    uom = {"Cotton": "tonnes", "Polyester": "tonnes", "Steel": "tonnes", "Plastic": "tonnes", "Leather": "tonnes",
           "Copper": "tonnes", "Cardboard": "tonnes"}
    base_price = {"Cotton": 1650, "Polyester": 1050, "Steel": 640, "Plastic": 1180, "Leather": 3900, "Copper": 7600, "Cardboard": 520}
    commitments = []
    sup_list = sorted(suppliers.values(), key=lambda s: s["supplier_id"])
    for sup in r.sample([s for s in sup_list if s["status"] == "active"], 22):
        commodity = r.choice(commodity_for[sup["category_focus"]])
        start = as_of - timedelta(days=r.randint(30, 300))
        end = start + timedelta(days=r.choice([180, 270, 365]))
        vol = r.choice([200, 400, 800, 1200, 2000, 3000])
        used = int(vol * r.choice([0, 0.15, 0.3, 0.5, 0.7, 1.0]))
        if used >= vol:
            status = "fulfilled"
        elif end < as_of:
            status = "expired"
        elif used == 0:
            status = "active"
        else:
            status = "partially_used"
        commitments.append({
            "commitment_id": f"COM-{len(commitments) + 1:06d}", "supplier_id": sup["supplier_id"], "commodity": commodity,
            "start_date": start.isoformat(), "end_date": end.isoformat(), "volume_units": vol, "volume_uom": uom[commodity],
            "price_gbp_per_unit": round(base_price[commodity] * r.uniform(0.92, 1.08), 2), "used_to_date": used,
            "remaining_volume": vol - used, "status": status, "notes": None, "updated_at": ts(min(as_of, start + timedelta(days=60)), r)})

    # ---------------------------------------------------------------- ASNs: one per PO delivered in the last 12 weeks, plus shipped POs
    asns, asn_lines = [], []
    for po in pos:
        arrived = d(ship[po["po_id"]]["ata"]) if po["po_id"] in ship and ship[po["po_id"]]["ata"] else None
        recent_done = po["status"] in DONE and arrived and (as_of - arrived).days <= 84
        if not (recent_done or po["status"] == "shipped"):
            continue
        sh = ship.get(po["po_id"])
        shipped_on = d(sh["atd"]) if sh and sh["atd"] else d(po["ship_date"])
        asn_id = f"ASN-{len(asns) + 1:06d}"
        asns.append({
            "asn_id": asn_id, "po_id": po["po_id"], "supplier_id": po["supplier_id"], "asn_number": f"{po['supplier_id'][-4:]}-{r.randint(10000, 99999)}",
            "shipment_id": sh["shipment_id"] if sh else None, "advised_at": ts(min(shipped_on, as_of), r),
            "expected_delivery_date": (d(sh["eta"]) if sh and sh["eta"] else d(po["due_date"])).isoformat(),
            "status": "delivered" if po["status"] in DONE else "received", "updated_at": ts(min(shipped_on + timedelta(days=1), as_of), r)})
        for n, ln in enumerate(lines.get(po["po_id"], []), 1):
            ordered, got = int(ln["qty_ordered"]), int(ln["qty_received"])
            short = got < ordered
            if po["status"] not in DONE:
                advised = ordered
            elif short and po["supplier_id"] == "SUP-0034":
                advised = ordered                                   # supplier advised the full quantity but it did not arrive
            elif short:
                advised = got                                       # supplier honestly advised the short quantity
            elif r.random() < 0.03:
                advised = got + max(1, int(got * 0.02))             # the odd receiving discrepancy against a correct ASN
            else:
                advised = got
            asn_lines.append({
                "asn_id": asn_id, "line_no": n, "po_line_no": int(ln["line_no"]), "sku": ln["sku"], "qty_advised": advised,
                "qty_received": got if po["status"] in DONE else 0, "batch_no": f"B{r.randint(100, 999)}-{r.randint(100, 999)}",
                "updated_at": ts(min(as_of, shipped_on + timedelta(days=2)), r)})

    # ---------------------------------------------------------------- nearshore pilot markers
    markers = []
    for sid in NEARSHORE:
        mine = sorted((p for p in pos if p["supplier_id"] == sid and p["status"] in OPEN + DONE), key=lambda p: p["order_date"])[-3:]
        for po in mine:
            started = d(po["order_date"])
            markers.append({
                "marker_id": f"MRK-{len(markers) + 1:06d}", "po_id": po["po_id"], "supplier_id": sid,
                "pilot_program": {"PT": "Portugal Nearshore Pilot", "PL": "Poland Nearshore Pilot", "TR": "Turkey Nearshore Pilot"}[suppliers[sid]["country"]],
                "start_date": started.isoformat(), "status": "active" if po["status"] in OPEN else "completed",
                "notes": r.choice([None, "Short-lead replenishment trial", "Quick-response capsule"]), "updated_at": ts(min(as_of, started + timedelta(days=5)), r)})

    # ---------------------------------------------------------------- approvals for some draft POs
    approvals = []
    for po in [p for p in pos if p["status"] == "draft"][:20]:
        if r.random() < 0.35:
            when = max(d(po["order_date"]) - timedelta(days=r.randint(0, 3)), as_of - timedelta(days=20))
            approvals.append({
                "approval_id": f"APR-{len(approvals) + 1:06d}", "po_id": po["po_id"], "status": "submitted",
                "submitted_by": r.choice(buyers), "submitted_at": ts(min(when, as_of), r), "decided_by": None, "decided_at": None,
                "notes": None, "updated_at": ts(min(when, as_of), r)})

    return {"purchase_requisitions": reqs, "po_amendments": amendments, "po_blocks": blocks, "po_price_history": price_history,
            "supplier_confirmations": confirmations, "commodity_commitments": commitments, "advance_shipping_notices": asns,
            "asn_line_items": asn_lines, "nearshore_pilot_markers": markers, "po_approvals": approvals}
