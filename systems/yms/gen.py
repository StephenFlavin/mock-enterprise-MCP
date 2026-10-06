"""Background yard data: an inbound appointment for every PO due in the last 60 / next 14 days."""
from datetime import datetime, time, timedelta


def generate(g):
    r = g.rng
    hauliers = [c["carrier_id"] for c in g.master("carriers") if c["mode"] == "road"]
    appts, arrivals = [], []
    for po in g.master("purchase_orders"):
        due = datetime.fromisoformat(po["due_date"])
        days = (due.date() - g.as_of).days
        if not -60 <= days <= 14 or po["status"] in ("cancelled", "draft"):
            continue
        start = datetime.combine(due.date(), time(r.choice(range(5, 21)), r.choice([0, 30])))
        aid = f"APT-{len(appts) + 1:06d}"
        past = due.date() < g.as_of
        appts.append({"appointment_id": aid, "site_id": po["dest_site_id"], "po_id": po["po_id"],
                      "carrier_id": r.choice(hauliers), "door": f"D{r.randint(1, 24):02d}",
                      "slot_start": start, "slot_end": start + timedelta(minutes=90), "direction": "inbound",
                      "status": r.choices(["completed", "no_show"], [96, 4])[0] if past else "booked",
                      "updated_at": start - timedelta(days=3)})
        if past and appts[-1]["status"] == "completed":
            late = int(r.gauss(10, 25))
            arr = start + timedelta(minutes=late)
            dock = arr + timedelta(minutes=r.randint(10, 60))
            dep = dock + timedelta(minutes=r.randint(45, 150))
            arrivals.append({"arrival_id": f"ARR-{len(arrivals) + 1:06d}", "appointment_id": aid,
                             "site_id": po["dest_site_id"], "trailer_no": g.fake.license_plate(),
                             "arrived_at": arr, "docked_at": dock, "departed_at": dep, "minutes_late": late,
                             "dwell_minutes": int((dep - arr).total_seconds() // 60)})
    return {"dock_appointments": appts, "trailer_arrivals": arrivals}
