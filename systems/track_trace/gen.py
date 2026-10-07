"""Track and trace platform: disruptions, shipment tracking, port congestion, transit history.

Shipment tracking is derived one-to-one from the master inbound sea/air shipments (same ids, POs, ports, carriers
and status). Planned arrival is the master ETA; the tracker's predicted ETA adds a small delay for most shipments and
a clear, larger delay for the planted late shipments (LATE_DAYS)."""
from datetime import datetime, timedelta, date

ACTIVE = ("in_transit", "at_port", "customs_hold", "delayed")

# Planted late in-transit shipments: shipment -> days the predicted ETA is behind the planned arrival.
# Everything else stays at 4 days late or less, so these are the top of the late list.
LATE_DAYS = {
    "SHP-0000132": 11,  # INNSA -> GBFXT, PO-2026-004155 (forwarder: rolled once, OBK-900201)
    "SHP-0000102": 9,   # VNSGN -> GBLGP, PO-2026-004121 (store cover under two weeks)
    "SHP-0000300": 8,   # INNSA -> GBLGP, PO-2026-004352 (forwarder OBK-900202)
    "SHP-0000114": 7,   # INNSA -> GBFXT
    "SHP-0000126": 6,   # INNSA -> GBFXT
    "SHP-0000709": 5,   # VNSGN -> GBFXT
}

# (id, days_ago_reported, hour, event_type, region, severity, status, impact_days, resolved_days_ago, ports, description)
DISRUPTIONS = [
    ("DIS-900001", 1, 14, "congestion", "UK - Felixstowe", "critical", "active", 5, None, "GBFXT",
     "Severe congestion at Felixstowe: vessel queue over 40 ships and berth waits of 4 to 5 days"),
    ("DIS-900002", 2, 8, "weather", "Asia - South China Sea", "high", "active", 3, None, "CNSHA,CNNGB,CNYTN",
     "Typhoon warning in the South China Sea: sailings from Shanghai, Ningbo and Yantian are holding or rerouting"),
    ("DIS-900004", 3, 9, "labor_action", "Europe - Rotterdam", "high", "active", 4, None, "NLRTM",
     "Dockworker strike at Rotterdam: 48-hour stoppages announced, discharge rates down about 40 percent"),
    ("DIS-900005", 4, 11, "customs_hold", "UK - all ports", "high", "monitoring", 3, None, "GBFXT,GBSOU,GBLGP",
     "UK customs system outage causing a clearance backlog, holds of up to 3 days at UK container ports"),
    ("DIS-900006", 5, 10, "vessel_delay", "Asia - Europe loops", "medium", "active", 2, None, "CNSHA,CNYTN",
     "Blank sailings on two Asia-Europe loops: cargo rolled to the next sailing"),
    ("DIS-900007", 14, 8, "political", "Bangladesh - Chittagong", "critical", "active", 7, None, "BDCGP",
     "Political unrest and transport strikes around Chittagong, plus gas and power shortages: truck access to the "
     "port is restricted and gate-in is suspended on several days"),
    ("DIS-900008", 13, 15, "weather", "Vietnam - Ho Chi Minh City", "high", "monitoring", 4, None, "VNSGN",
     "Typhoon near Ho Chi Minh City: river channel closed intermittently, vessel departures slipping"),
    ("DIS-900009", 17, 9, "labor_action", "India - Nhava Sheva", "high", "active", 3, None, "INNSA",
     "Port strike notice at Nhava Sheva: container handling slowed, yard congestion building"),
    ("DIS-900010", 10, 13, "accident", "UK - Southampton", "medium", "active", 2, None, "GBSOU",
     "Container yard fire at Southampton: one terminal operating at reduced capacity"),
    ("DIS-900011", 20, 9, "customs_hold", "China - Yantian", "medium", "monitoring", 3, None, "CNYTN",
     "Export licence checks on electrical goods at Yantian slowing release of containers"),
    ("DIS-900012", 11, 14, "labor_action", "Germany - Hamburg", "low", "monitoring", 1, None, "DEHAM",
     "Short warning stoppage at Hamburg terminals, minor delays expected"),
    ("DIS-900013", 15, 16, "vessel_delay", "Mexico - Manzanillo", "low", "monitoring", 1, None, "MXZLO",
     "Vessel bunching at Manzanillo, short berthing delays"),
    # history, resolved: used to flag disrupted sailings in the transit history
    ("DIS-900020", 52, 8, "weather", "Asia - East China Sea", "high", "resolved", 4, 48, "CNSHA,CNNGB",
     "Typhoon closed Shanghai and Ningbo to vessel traffic for several days"),
    ("DIS-900021", 85, 9, "congestion", "UK - Felixstowe", "high", "resolved", 5, 77, "GBFXT",
     "Felixstowe terminal queue of 25 ships after a crane outage"),
    ("DIS-900022", 111, 7, "labor_action", "Germany - Hamburg", "medium", "resolved", 3, 108, "DEHAM,NLRTM",
     "Hamburg and Rotterdam dock strike, two days of stoppages"),
    ("DIS-900023", 36, 12, "weather", "Vietnam - Ho Chi Minh City", "medium", "resolved", 3, 33, "VNSGN",
     "Tropical storm closed Ho Chi Minh City port for 36 hours"),
    ("DIS-900024", 138, 8, "vessel_delay", "Asia - Europe via Cape", "high", "resolved", 5, 131, "CNSHA,CNNGB,CNYTN,VNSGN",
     "Asia-Europe sailings diverted via the Cape of Good Hope for security reasons, about a week added"),
    ("DIS-900025", 168, 10, "customs_hold", "UK - Southampton", "medium", "resolved", 3, 165, "GBSOU",
     "Customs clearance backlog at Southampton after a system migration"),
]

# Port dwell model: base average dwell hours and base vessel queue
PORTS = {
    "GBFXT": (34, 6), "GBSOU": (28, 4), "GBLGP": (26, 4), "NLRTM": (38, 6), "DEHAM": (32, 5),
    "CNSHA": (22, 7), "CNNGB": (22, 6), "CNYTN": (20, 5), "BDCGP": (46, 5), "VNSGN": (30, 5), "INNSA": (42, 6),
}
# (port, weeks_ago) -> (avg_dwell_hours, vessel_queue, note): the current stories, newest week is 0
PORT_STORY = {
    ("GBFXT", 4): (36, 9, ""), ("GBFXT", 3): (44, 14, "Queue building after crane downtime"),
    ("GBFXT", 2): (51, 22, "Berth waits lengthening"), ("GBFXT", 1): (58, 33, "Severe queue, see DIS-900001"),
    ("GBFXT", 0): (63, 41, "Severe congestion, vessel queue over 40 ships (DIS-900001)"),
    ("NLRTM", 7): (38, 6, ""), ("NLRTM", 6): (42, 7, ""), ("NLRTM", 5): (48, 9, ""), ("NLRTM", 4): (55, 11, ""),
    ("NLRTM", 3): (63, 14, "Yard density rising"), ("NLRTM", 2): (74, 18, "Discharge slowed by strike warnings"),
    ("NLRTM", 1): (85, 22, "Dockworker strike action, see DIS-900004"),
    ("NLRTM", 0): (94, 27, "48-hour strike stoppages (DIS-900004)"),
    ("CNSHA", 1): (30, 12, "Typhoon warning, sailings holding (DIS-900002)"),
    ("CNSHA", 0): (38, 16, "Typhoon disruption, vessels waiting at anchorage (DIS-900002)"),
    ("BDCGP", 2): (58, 8, "Gate-in restricted on strike days (DIS-900007)"),
    ("BDCGP", 1): (72, 11, "Unrest and truck strikes (DIS-900007)"),
    ("BDCGP", 0): (86, 14, "Port access restricted, gate-in suspended (DIS-900007)"),
}

# (origin, dest, service, planned_days, mean_delay_start, mean_delay_end, sd)
LANES = [
    ("CNSHA", "GBFXT", "FAL9", 28, 0.6, 2.8, 1.4),
    ("CNYTN", "GBFXT", "FAL7", 30, 0.6, 1.8, 1.6),
    ("CNNGB", "GBSOU", "AE5", 31, 0.5, 0.9, 1.4),
    ("CNSHA", "NLRTM", "AE1", 33, 0.8, 1.6, 1.8),
    ("VNSGN", "GBLGP", "SE2", 35, 0.6, 1.5, 1.7),
    ("INNSA", "GBFXT", "IX1", 24, 0.5, 2.2, 1.5),
    ("BDCGP", "GBFXT", "BX1", 34, 1.0, 2.6, 2.0),
]
OCEAN = ["CAR-005", "CAR-006", "CAR-007"]
CAR_EXTRA = {"CAR-006": 1.2}  # Pacific Star Shipping runs later than the others
CURRENT_BUFFER = {("CNSHA", "GBFXT", "FAL9"): 2.0}


def _quantile(vals, q):
    v = sorted(vals)
    pos = q * (len(v) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (pos - lo)


def generate(g):
    r = g.rng
    as_of = g.as_of
    now = datetime.combine(as_of, datetime.min.time()) + timedelta(hours=9)

    # ---------------------------------------------------------------- disruptions
    disruptions = []
    windows = []
    for did, d_ago, hour, etype, region, sev, status, impact, res_ago, ports, desc in DISRUPTIONS:
        rep = datetime.combine(g.days_ago(d_ago), datetime.min.time()) + timedelta(hours=hour, minutes=30)
        resolved = (datetime.combine(g.days_ago(res_ago), datetime.min.time()) + timedelta(hours=16)) if res_ago is not None else None
        updated = resolved or (now - timedelta(hours=r.randint(3, 36)))
        disruptions.append({
            "disruption_id": did, "reported_at": rep, "event_type": etype, "region": region, "severity": sev,
            "status": status, "description": desc, "estimated_impact_days": impact, "resolved_at": resolved,
            "updated_at": updated, "affected_ports": ports})
        windows.append((did, rep.date(), resolved.date() if resolved else as_of, set(ports.split(",")), impact, etype))

    # ---------------------------------------------------------------- shipment tracking
    pos = {p["po_id"]: p for p in g.master("purchase_orders")}
    shipment_tracking = []
    for s in g.master("shipments"):
        if s["mode"] not in ("sea", "air") or s["po_id"] not in pos:
            continue
        po = pos[s["po_id"]]
        status = s["status"]
        planned = date.fromisoformat(s["eta"])
        dep = date.fromisoformat(s["atd"] or s["etd"])
        actual = date.fromisoformat(s["ata"]) if s["ata"] else None
        acc = None
        if status == "delivered":
            if actual is None or actual < as_of - timedelta(days=120):
                continue
            predicted = actual - timedelta(days=r.choice([0, 0, 0, 1, 1, -1]))
            acc = (actual - predicted).days
        else:
            if status == "delayed":
                late = r.choice([1, 2, 2, 3])
            elif status == "booked":
                late = r.choice([0, 0, 0, 1])
            else:
                late = r.choice([0, 0, 0, 1, 1, 2])
            late = LATE_DAYS.get(s["shipment_id"], late)
            predicted = planned + timedelta(days=late)
            if status != "booked" and predicted <= as_of:
                predicted = as_of + timedelta(days=1)
            actual = None
        shipment_tracking.append({
            "shipment_id": s["shipment_id"], "po_id": s["po_id"], "carrier_id": s["carrier_id"], "mode": s["mode"],
            "origin_port": s["origin_port"], "dest_port": s["dest_port"], "dest_site_id": po["dest_site_id"],
            "departure_date": dep,
            "planned_arrival": planned, "predicted_eta": predicted, "actual_arrival": actual,
            "eta_accuracy_days": acc, "priority_flag": False, "status": status,
            "updated_at": now - timedelta(hours=r.randint(1, 60)),
        })

    # ---------------------------------------------------------------- shipment batches
    lines_by_po = {}
    for l in g.master("po_lines"):
        lines_by_po.setdefault(l["po_id"], []).append(l)
    shipment_batches = []
    n = 0
    for t in shipment_tracking:
        if t["status"] == "booked":
            continue
        if t["status"] == "delivered" and t["actual_arrival"] < as_of - timedelta(days=45):
            continue
        po = pos[t["po_id"]]
        for line in lines_by_po.get(t["po_id"], [])[:3]:
            sku = line["sku"]
            if sku == "PF-220":  # PF-220 batches are seeded (recall story)
                continue
            qty = int(line["qty_ordered"])
            parts = max(1, min(3, qty // 2500))
            mfg = t["departure_date"] - timedelta(days=r.randint(10, 25))
            for i in range(parts):
                n += 1
                units = qty // parts + (qty % parts if i == 0 else 0)
                bstatus = {"delivered": "delivered", "at_port": "at_port", "customs_hold": "at_port"}.get(t["status"], "in_transit")
                shipment_batches.append({
                    "batch_id": f"BAT-{n:06d}", "sku": sku, "shipment_id": t["shipment_id"],
                    "factory_id": po["factory_id"], "batch_number": f"BATCH-{sku.replace('-', '')}-{mfg:%y%m}-{chr(65 + i)}",
                    "units_shipped": units, "manufacturing_date": mfg, "status": bstatus, "updated_at": t["updated_at"]})

    # ---------------------------------------------------------------- port congestion (weekly, 27 weeks)
    port_congestion = []
    for port, (base_dwell, base_q) in PORTS.items():
        for k in range(26, -1, -1):
            d = g.days_ago(7 * k)
            if (port, k) in PORT_STORY:
                dwell, queue, note = PORT_STORY[(port, k)]
            else:
                dwell = base_dwell * (1 + r.gauss(0, 0.06))
                queue = max(1, round(base_q * (dwell / base_dwell) + r.gauss(0, 1.2)))
                note = ""
                for did, start, end, ports, impact, etype in windows:
                    if port in ports and start - timedelta(days=3) <= d <= end and end < as_of:
                        mult = 1 + min(0.9, impact * 0.12)
                        dwell *= mult
                        queue = round(queue * mult + 2)
                        note = f"{etype.replace('_', ' ').capitalize()} ({did})"
                        break
            dwell = round(dwell, 1)
            ratio = dwell / base_dwell
            lvl_d = 0 if ratio < 1.25 else 1 if ratio < 1.6 else 2 if ratio < 2.2 else 3
            lvl_q = 0 if queue < 10 else 1 if queue < 15 else 2 if queue < 30 else 3
            level = ["low", "medium", "high", "critical"][max(lvl_d, lvl_q)]
            port_congestion.append({
                "port_code": port, "measurement_date": d, "avg_dwell_hours": dwell,
                "max_dwell_hours": round(dwell * r.uniform(1.3, 1.8), 1), "vessel_queue_length": int(queue),
                "congestion_level": level, "notes": note})

    # ---------------------------------------------------------------- transit history (weekly sailings, delivered)
    transit_history = []
    per_lane = {}
    n_sail = 21
    for origin, dest, service, planned, m0, m1, sd in LANES:
        for i in range(n_sail):
            back = 35 + 7 * (n_sail - 1 - i)  # i=0 oldest, departure days ago
            dep = g.days_ago(back)
            carrier = OCEAN[i % 3]
            progress = i / (n_sail - 1)
            delay = r.gauss(m0 + (m1 - m0) * progress, sd) + CAR_EXTRA.get(carrier, 0)
            delay = max(delay, -2.0)
            arrival = dep + timedelta(days=planned)
            hit = None
            for did, start, end, ports, impact, etype in windows:
                if end < as_of and ((origin in ports and start <= dep <= end) or (dest in ports and start <= arrival <= end)):
                    hit = did
                    delay += impact * r.uniform(1.0, 1.6)
                    break
            delay = round(delay, 1)
            per_lane.setdefault((origin, dest, service), []).append(delay)
            transit_history.append({
                "origin_port": origin, "dest_port": dest, "carrier_id": carrier, "service": service,
                "transit_date": dep, "mode": "sea", "transit_time_days": round(planned + delay, 1),
                "planned_days": float(planned), "variance_pct": round(delay / planned * 100, 1),
                "disruption_id": hit})

    # ---------------------------------------------------------------- planning buffers
    planning_buffers = []
    for (origin, dest, service), delays in per_lane.items():
        p90 = max(_quantile(delays, 0.9), 0)
        within = sum(1 for x in delays if abs(x) <= 2) / len(delays)
        planning_buffers.append({
            "origin_port": origin, "dest_port": dest, "service": service,
            "current_buffer_days": CURRENT_BUFFER.get((origin, dest, service), r.choice([2.0, 3.0, 3.0, 4.0])),
            "recommended_buffer_days": round(p90, 1), "accuracy_score": round(within * 100, 1),
            "last_updated": now - timedelta(days=r.randint(20, 60))})

    return {
        "disruptions": disruptions, "shipment_tracking": shipment_tracking, "port_congestion": port_congestion,
        "transit_history": transit_history, "shipment_batches": shipment_batches, "planning_buffers": planning_buffers,
    }
