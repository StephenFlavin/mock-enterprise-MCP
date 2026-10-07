"""Background forwarder data, derived from master shipments and POs so ids, carriers, ports and dates line up.

Story built into the data (all relative to the data as-of date):
- Last quarter's Asia-Europe ocean bookings: 18% were rolled. Pacific Star (CAR-006) and Oceanic (CAR-005) roll most,
  bookings made under 14 days ahead roll far more often, and so do bigger (3+ container) bookings and Rotterdam calls.
- Demurrage/detention concentrates on the rolled bookings.
- Planned bookings for the next weeks are generated from future sea POs, kept clear of the announced blank sailings
  (those few hit bookings are hand-seeded in seed/ocean_bookings.csv).
Rows in a few narrow date bands are skipped on purpose so that rolling windows ("last 90 days") never cut through
a cluster of rows when the data is moved forward to today.
"""
from datetime import date, datetime, timedelta
import math

ASIA = {"CNSHA", "CNNGB", "CNYTN", "VNSGN", "INNSA", "BDCGP"}
EUROPE = {"GBFXT", "GBSOU", "GBLGP", "NLRTM", "DEHAM"}
COUNTRY_PORTS = {"CN": ["CNSHA", "CNNGB", "CNYTN"], "VN": ["VNSGN"], "IN": ["INNSA"], "BD": ["BDCGP"]}
PORT_COST = {"CNSHA": 6700, "CNNGB": 6600, "CNYTN": 6500, "VNSGN": 6900, "INNSA": 6300, "BDCGP": 7800}
CARRIER_ROLL = {"CAR-006": 3.2, "CAR-005": 2.4, "CAR-007": 0.8, "CAR-009": 0.5, "CAR-010": 0.4}
GAPS = [(-91, -83), (-181, -173), (-361, -353), (59, 70)]   # day offsets from as-of left empty on purpose
BLANKS = [("CAR-005", "NLRTM", 12), ("CAR-006", "DEHAM", 19), ("CAR-007", "NLRTM", 33), ("CAR-005", "GBFXT", 26)]
AIRPORT = {"CNSHA": "PVG", "CNNGB": "NGB", "CNYTN": "SZX", "VNSGN": "SGN", "INNSA": "BOM", "BDCGP": "DAC", "MXZLO": "MEX"}
STORY_FROM = -82            # roll story window starts here (days from as-of)
TARGET_ROLL_RATE = 0.18

# Air invoices (mirrors the airline invoices AP holds for the same quarter: GBP 420,000 over 11 invoices).
# invoice, carrier, supplier, invoice date, amount, shipments, reason
AIR_INVOICES = [
    ("INV-900001", "CAR-008", "SUP-0012", "2026-09-18", 52000, 6, "supplier_late"),
    ("INV-900002", "CAR-008", "SUP-0012", "2026-08-21", 38000, 4, "supplier_late"),
    ("INV-900003", "CAR-009", "SUP-0015", "2026-09-04", 35000, 5, "supplier_late"),
    ("INV-900004", "CAR-010", "SUP-0008", "2026-08-07", 25000, 3, "supplier_late"),
    ("INV-900005", "CAR-018", "SUP-0015", "2026-08-28", 24000, 3, "quality_issue"),
    ("INV-900006", "CAR-008", "SUP-0003", "2026-09-11", 16000, 2, "quality_issue"),
    ("INV-900007", "CAR-018", "SUP-0021", "2026-08-14", 20000, 2, "cancelled_order"),
    ("INV-900008", "CAR-009", "SUP-0003", "2026-09-25", 60000, 7, "demand_spike"),
    ("INV-900009", "CAR-010", "SUP-0021", "2026-08-30", 60000, 8, "demand_spike"),
    ("INV-900010", "CAR-008", "SUP-0003", "2026-09-22", 52000, 6, "store_emergency"),
    ("INV-900011", "CAR-018", "SUP-0021", "2026-09-08", 38000, 5, "store_emergency"),
]


def _d(s):
    return date.fromisoformat(s[:10]) if s else None


def generate(g):
    r = g.rng
    A = g.as_of

    def off(d):
        return (d - A).days

    def gapped(d):
        o = off(d)
        return any(a <= o <= b for a, b in GAPS)

    pos = {p["po_id"]: p for p in g.master("purchase_orders")}
    sup = {s["supplier_id"]: s for s in g.master("suppliers")}
    seed_pos = {"PO-2026-004155", "PO-2026-004352", "PO-2026-004122", "PO-2026-004066", "PO-2026-005728", "PO-2026-005511", "PO-2026-005784", "PO-2026-005024"}

    def containers(po):
        return max(1, min(6, round(int(po["total_units"]) / 3500)))

    def lead_days():
        x = r.random()
        return r.randint(6, 13) if x < 0.24 else r.randint(14, 27) if x < 0.62 else r.randint(28, 49)

    def collides(carrier, dest, sail):
        return any(c == carrier and d == dest and abs(off(sail) - o) <= 10 for c, d, o in BLANKS)

    # ---------------------------------------------------------------- bookings from master sea shipments
    base = []
    for s in sorted(g.master("shipments"), key=lambda s: (s["etd"], s["shipment_id"])):
        if s["mode"] != "sea" or s["origin_port"] not in ASIA or s["dest_port"] not in EUROPE or s["po_id"] in seed_pos:
            continue
        atd, etd = _d(s["atd"]), _d(s["etd"])
        sail = atd if atd and atd <= A else etd
        if off(sail) < -380 or gapped(sail):
            continue
        po = pos[s["po_id"]]
        status = {"delivered": "delivered", "booked": "booked"}.get(s["status"], "in_transit")
        base.append({"s": s, "po": po, "sail": sail, "status": status, "n": containers(po), "lead": lead_days()})

    # who rolls: exactly 18% of the story window, weighted by carrier, lead time, size and port
    story = [b for b in base if b["status"] != "booked" and off(b["sail"]) >= STORY_FROM]
    k = round(TARGET_ROLL_RATE * len(story))

    def weight(b):
        w = CARRIER_ROLL.get(b["s"]["carrier_id"], 1.0)
        w *= 5.0 if b["lead"] < 14 else 1.2 if b["lead"] < 28 else 0.35
        w *= 2.6 if b["n"] >= 3 else 1.0
        w *= 4.0 if b["s"]["dest_port"] == "NLRTM" else 1.0
        w *= 1.8 if b["s"]["origin_port"] in ("CNSHA", "CNYTN") else 1.0
        return w

    ranked = sorted(story, key=lambda b: -(math.log(weight(b)) + r.gauss(0, 0.45)))
    rolled = {id(b) for b in ranked[:k]}
    for b in base:
        b["rolls"] = 0
        if id(b) in rolled:
            b["rolls"] = 2 if r.random() < 0.15 else 1
        elif b["status"] != "booked" and off(b["sail"]) < -91 and r.random() < 0.07:
            b["rolls"] = 1

    def reason(b):
        s = b["s"]
        if b["lead"] < 14:
            return ("Overbooked vessel: late booking bumped by earlier bookings" if r.random() < 0.75
                    else "Equipment shortage: no 40ft containers at origin depot")
        if s["dest_port"] == "NLRTM":
            return "Rotterdam call omitted: port congestion, cargo rolled to next sailing"
        if s["origin_port"] in ("CNSHA", "CNYTN"):
            return "Origin terminal congestion: missed vessel cut-off at " + ("Shanghai" if s["origin_port"] == "CNSHA" else "Yantian")
        return "Blank sailing: carrier cancelled the sailing" if r.random() < 0.5 else "Space allocation changed by carrier"

    bookings, charges, events = [], [], []
    for b in base:
        s, po = b["s"], b["po"]
        n = len(bookings) + 1
        sail = b["sail"]
        orig = sail - timedelta(days=7 * b["rolls"])
        eta = _d(s["eta"])
        row = {
            "booking_id": f"OBK-{n:06d}", "po_id": s["po_id"], "shipment_id": s["shipment_id"], "carrier_id": s["carrier_id"],
            "origin_port": s["origin_port"], "dest_port": s["dest_port"],
            "booking_date": orig - timedelta(days=b["lead"]), "original_sailing": orig, "planned_sailing": sail,
            "cut_off_days": r.randint(2, 4), "transit_days": max(1, (eta - _d(s["etd"])).days),
            "actual_departure": sail if b["status"] in ("in_transit", "delivered") and sail <= A else None,
            "actual_arrival": _d(s["ata"]) if b["status"] == "delivered" and s["ata"] else None,
            "container_count": b["n"], "booking_status": b["status"], "roll_count": b["rolls"],
            "roll_reason": reason(b) if b["rolls"] else None, "priority": "normal",
            "cost_gbp": round(b["n"] * PORT_COST[s["origin_port"]] * r.uniform(0.93, 1.07), 2),
            "updated_at": datetime.combine(min(sail, A), datetime.min.time()) + timedelta(hours=9),
        }
        bookings.append(row)

        # demurrage / detention: far more likely on rolled bookings
        arr = row["actual_arrival"]
        if arr:
            p = 0.07
            if b["rolls"]:
                p = 0.9
            if r.random() < p:
                days = r.randint(2, 7) if b["rolls"] else r.randint(1, 4)
                cdate = arr + timedelta(days=r.randint(3, 8))
                if cdate <= A and not gapped(cdate):
                    kind = "demurrage" if r.random() < 0.65 else "detention"
                    why = ("Port congestion at discharge: dwell beyond free time" if kind == "demurrage" and s["dest_port"] == "NLRTM"
                           else "Container stored beyond free period at discharge port" if kind == "demurrage"
                           else "Empty container returned late after delivery")
                    if b["rolls"] and kind == "demurrage":
                        why = "Late arrival after roll: unplanned dwell beyond free time at discharge"
                    charges.append({
                        "charge_id": f"CHG-{len(charges) + 1:06d}", "booking_id": row["booking_id"], "charge_type": kind,
                        "charge_date": cdate, "amount_gbp": round(row["container_count"] * days * r.uniform(95, 145), 2),
                        "days_or_units": days, "port_id": s["dest_port"], "description": why})

        # a few expedite requests on delayed cargo
        if s["status"] == "delayed" and r.random() < 0.3:
            events.append({
                "event_id": f"EVT-{len(events) + 1:06d}", "booking_id": row["booking_id"],
                "event_type": "expedite_request", "reason": r.choice(["Store stockout risk", "Promotional window closing"]),
                "status": "acknowledged", "created_at": datetime.combine(A, datetime.min.time()) - timedelta(days=r.randint(6, 12), hours=-10)})

    # ---------------------------------------------------------------- planned bookings from future sea POs
    shipped_pos = {s["po_id"] for s in g.master("shipments")}
    for po in sorted(pos.values(), key=lambda p: (p["ship_date"], p["po_id"])):
        if po["mode"] != "sea" or po["status"] not in ("open", "confirmed") or po["po_id"] in shipped_pos or po["po_id"] in seed_pos:
            continue
        country = sup[po["supplier_id"]]["country"]
        ship = _d(po["ship_date"])
        if country not in COUNTRY_PORTS or not 8 <= off(ship) <= 38 or r.random() > 0.55:
            continue
        sail = ship + timedelta(days=r.randint(2, 5))
        origin = r.choice(COUNTRY_PORTS[country])
        dest = r.choices(["GBFXT", "GBSOU", "GBLGP", "NLRTM"], [0.55, 0.25, 0.12, 0.08])[0]
        carrier = r.choice(list(CARRIER_ROLL))
        while collides(carrier, dest, sail):
            carrier = r.choice(["CAR-009", "CAR-010"])
        n = containers(po)
        bookings.append({
            "booking_id": f"OBK-{len(bookings) + 1:06d}", "po_id": po["po_id"], "carrier_id": carrier,
            "origin_port": origin, "dest_port": dest, "booking_date": A - timedelta(days=r.randint(0, 9)),
            "original_sailing": sail, "planned_sailing": sail, "cut_off_days": r.randint(2, 4), "transit_days": r.randint(30, 40),
            "container_count": n, "booking_status": "booked", "roll_count": 0, "priority": "normal",
            "cost_gbp": round(n * PORT_COST[origin] * r.uniform(0.93, 1.07), 2),
            "updated_at": datetime.combine(A, datetime.min.time()) + timedelta(hours=9)})

    # ---------------------------------------------------------------- air bookings from master air shipments
    air = []
    for s in sorted(g.master("shipments"), key=lambda s: (s["etd"], s["shipment_id"])):
        if s["mode"] != "air" or s["origin_port"] not in AIRPORT or not -120 <= off(_d(s["etd"])) <= 10:
            continue
        po = pos[s["po_id"]]
        etd, status = _d(s["etd"]), {"delivered": "delivered", "booked": "booked"}.get(s["status"], "departed")
        units = max(200, min(int(po["total_units"]), r.choice([300, 500, 800, 1000, 1500, 2000])))
        dest = "AMS" if s["dest_port"] == "NLRTM" else "LHR"
        air.append({
            "booking_id": f"ABK-{len(air) + 1:06d}", "po_id": s["po_id"], "carrier_id": s["carrier_id"],
            "origin_airport": AIRPORT[s["origin_port"]], "dest_airport": dest,
            "booking_date": etd - timedelta(days=r.randint(2, 6)), "planned_departure": etd,
            "planned_arrival": _d(s["eta"]), "actual_departure": _d(s["atd"]) if status != "booked" else None,
            "actual_arrival": _d(s["ata"]) if status == "delivered" and s["ata"] else None,
            "units": units, "booking_status": status, "cost_gbp": round(units * r.uniform(4.5, 9.0), 2),
            "updated_at": datetime.combine(min(etd, A), datetime.min.time())})

    # ---------------------------------------------------------------- older air invoices (before the last quarter)
    invoices = []
    suppliers = ["SUP-0003", "SUP-0008", "SUP-0012", "SUP-0015", "SUP-0021"]
    reasons = ["supplier_late", "supplier_late", "quality_issue", "demand_spike", "store_emergency", "cancelled_order"]
    for i in range(16):
        end = A - timedelta(days=r.randint(112, 370))
        if gapped(end):
            continue
        start = end - timedelta(days=21)
        if gapped(start):
            continue
        amount = round(r.uniform(9000, 38000), -2)
        invoices.append({
            "invoice_id": f"INV-{len(invoices) + 1:06d}", "carrier_id": r.choice(["CAR-008", "CAR-009", "CAR-010", "CAR-018"]),
            "period_start": start, "period_end": end, "shipment_count": r.randint(2, 7),
            "total_units": int(amount / r.uniform(8.5, 11) // 10 * 10), "total_cost_gbp": amount,
            "reason_code": r.choice(reasons), "supplier_id": r.choice(suppliers), "created_date": end})

    return {"ocean_bookings": bookings, "air_freight_bookings": air, "air_freight_invoices": invoices,
            "booking_events": events, "demurrage_detention": charges, "routing_options": []}
