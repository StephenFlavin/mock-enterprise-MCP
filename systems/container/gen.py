"""Container visibility data, grounded in master sea shipments.

Every non-delivered master sea shipment becomes one or more 40ft containers (contents split from the
PO lines). The 140 containers on the vessel anchored outside Rotterdam are real Asia-to-UK shipments.
Port status, rail legs and option rates are hand-written in seed/*.csv; history (disruptions, transit
times, dwell, ETA predictions) is generated here with planted patterns.
"""
import math
from collections import defaultdict
from datetime import datetime, time, timedelta

STORY_VESSEL = "CONT-VESSEL-900001"
STORY_CONTAINERS = 140
FX = {"GBP": 1.0, "USD": 0.78, "EUR": 0.86}
ASIA_ORIGINS = ("CNSHA", "CNYTN", "CNNGB", "VNSGN")
STATUS_MAP = {"in_transit": "in_transit", "at_port": "at_port", "delayed": "delayed",
              "customs_hold": "at_port", "booked": "booked"}

SEA_PATHS = {
    "east": [(22.3, 114.2), (10.0, 110.5), (2.5, 101.5), (6.0, 80.0), (12.5, 52.0), (20.0, 38.5), (30.5, 32.5), (35.0, 18.0), (37.0, -7.0), (46.0, -6.0), (50.5, 1.5)],
    "south": [(18.9, 72.0), (12.5, 52.0), (20.0, 38.5), (30.5, 32.5), (35.0, 18.0), (37.0, -7.0), (46.0, -6.0), (50.5, 1.5)],
    "west": [(19.0, -104.5), (9.0, -79.5), (25.0, -70.0), (40.0, -40.0), (48.0, -12.0), (50.5, 1.5)],
}


def sea_position(origin, dest, frac):
    path = SEA_PATHS["south" if origin in ("INNSA", "BDCGP") else "west" if origin == "MXZLO" else "east"]
    if dest == "USNYC":
        path = path[:-2] + [(40.5, -73.5)] if origin == "MXZLO" else path[:-3] + [(45.0, -40.0), (40.5, -73.5)]
    pos = frac * (len(path) - 1)
    i = min(int(pos), len(path) - 2)
    t = pos - i
    lat = path[i][0] + (path[i + 1][0] - path[i][0]) * t
    lon = path[i][1] + (path[i + 1][1] - path[i][1]) * t
    return f"{abs(lat):.2f}{'N' if lat >= 0 else 'S'}, {abs(lon):.2f}{'E' if lon >= 0 else 'W'}"


def generate(g):
    r = g.rng
    today = datetime.combine(g.as_of, time(9, 0))

    def ago(days=0, hours=0):
        return today - timedelta(days=days, hours=hours)

    # ---------------------------------------------------------------- containers from master
    ships = sorted((s for s in g.master("shipments") if s["mode"] == "sea" and s["status"] != "delivered"),
                   key=lambda s: s["shipment_id"])
    pos = {p["po_id"]: p for p in g.master("purchase_orders")}
    po_lines = defaultdict(list)
    for ln in g.master("po_lines"):
        po_lines[ln["po_id"]].append(ln)

    n_cont = {s["shipment_id"]: max(1, math.ceil(float(s["teu"]) * 4)) for s in ships}

    # the 140 containers on the anchored vessel: earliest-sailed Asia->UK shipments, not booked
    story = {}
    cand = sorted((s for s in ships if s["origin_port"] in ASIA_ORIGINS and s["dest_port"].startswith("GB")
                   and s["status"] != "booked" and s["etd"] <= "2026-09-20"), key=lambda s: (s["etd"], s["shipment_id"]))
    left = STORY_CONTAINERS
    for s in cand:
        if left <= 0:
            break
        k = min(n_cont[s["shipment_id"]], left)
        n_cont[s["shipment_id"]] = k
        story[s["shipment_id"]] = k
        left -= k

    def transship_for(s):
        if s["shipment_id"] in story:
            return "NLRTM"
        if s["dest_port"].startswith("GB") and s["origin_port"] in ("INNSA", "BDCGP"):
            return "DEHAM"
        return None

    # vessels: story vessel + one per (origin, destination, transship) group of the rest
    groups = defaultdict(list)
    for s in ships:
        if s["status"] == "booked":
            continue
        key = STORY_VESSEL if s["shipment_id"] in story else (s["origin_port"], s["dest_port"], transship_for(s))
        groups[key].append(s)

    containers, contents, vessels = [], [], []
    vessel_names = ["Maersk Halden", "CMA CGM Vela", "Ever Gentle", "MSC Aurelia", "Cosco Pacific", "ONE Harmony",
                    "Hapag Elbe", "Yang Ming Unity", "OOCL Tianjin", "Wan Hai 312", "Evergreen Triton",
                    "ZIM Antwerp", "Hyundai Brave", "APL Singapura", "Seaspan Amazon", "Pacific Trader",
                    "Nordic Star", "Tasman Bridge", "Delta Voyager", "Coral Sun", "Atlantic Gull", "Bengal Pearl"]
    keys = [STORY_VESSEL] + sorted(k for k in groups if k != STORY_VESSEL)

    def expand(s, n):
        po = pos[s["po_id"]]
        fx = FX.get(po["currency"], 1.0)
        lines = po_lines[s["po_id"]]
        per = [[] for _ in range(n)]
        rx = g.rng_for("expand", s["shipment_id"])
        weights = [rx.uniform(0.4, 1.6) for _ in range(n)]
        for ln in lines:
            q = int(ln["qty_ordered"])
            shares = [max(1, int(q * w / sum(weights))) for w in weights]
            shares[0] += q - sum(shares)
            for i in range(n):
                per[i].append((ln["sku"], max(1, shares[i]), float(ln["unit_cost"]) * fx))
        return po, per

    for vi, key in enumerate(keys):
        members = groups.get(key, [])
        if not members:
            continue
        story_v = key == STORY_VESSEL
        vessel_id = STORY_VESSEL if story_v else f"CONT-VESSEL-{vi + 1:03d}"
        v_containers = []
        for s in members:
            po, per = expand(s, n_cont[s["shipment_id"]])
            transship = transship_for(s)
            lane = ("Asia-UK" if s["dest_port"].startswith("GB") and s["origin_port"] != "MXZLO"
                    else "Americas-UK" if s["dest_port"].startswith("GB")
                    else "Asia-US" if s["dest_port"] == "USNYC" else "Asia-Europe")
            status = "delayed" if story_v else STATUS_MAP[s["status"]]
            r = g.rng_for("container", s["shipment_id"])
            for lines in per:
                cid = f"CONT-{len(containers) + 1:06d}"
                value = 0.0
                for ln_no, (sku, qty, unit) in enumerate(lines, 1):
                    total = round(qty * unit, 2)
                    value += total
                    contents.append({"container_id": cid, "line_number": ln_no, "sku": sku, "quantity": qty,
                                     "unit_cost_gbp": round(unit, 2), "total_value_gbp": total})
                arrived = None
                if status == "at_port":
                    arrived = ago(days=r.randint(0, 3), hours=r.randint(0, 12))
                row = {"container_id": cid, "shipment_id": s["shipment_id"], "vessel_id": vessel_id,
                       "origin_port": s["origin_port"], "destination_port": s["dest_port"],
                       "next_port": transship or s["dest_port"], "route": lane, "transship_port": transship,
                       "container_type": "20ft" if value < 20000 and r.random() < 0.6 else "40ft", "status": status,
                       "actual_arrival": arrived, "destination_site_id": po["dest_site_id"],
                       "value_gbp": round(value, 2), "booking_date": po["order_date"],
                       "updated_at": ago(hours=r.randint(1, 36))}
                containers.append(row)
                v_containers.append(row)
        if story_v:
            vessels.append({"vessel_id": vessel_id, "name": "Asia Express 01", "carrier_id": "CAR-007",
                            "current_port": "NLRTM", "berth_status": "anchored",
                            "current_position": "51.98N, 3.95E", "eta_port": "NLRTM",
                            "eta_timestamp": ago(days=6, hours=1), "eta_berth_timestamp": None,
                            "anchored_since": ago(days=6, hours=1), "delay_days": 6.0,
                            "container_count": len(v_containers), "updated_at": ago(hours=2)})
            continue
        r = g.rng_for("vessel", vessel_id)
        etas = [datetime.fromisoformat(m["eta"]) + timedelta(hours=14) for m in members]
        eta = max(etas)
        at_port = sum(1 for c in v_containers if c["status"] == "at_port") * 2 > len(v_containers)
        dest = members[0]["dest_port"]
        port = transship_for(members[0]) or dest
        carrier = members[0]["carrier_id"]
        if carrier not in ("CAR-005", "CAR-006", "CAR-007"):
            carrier = ("CAR-005", "CAR-006", "CAR-007")[vi % 3]
        if at_port:
            eta = ago(days=r.randint(0, 2), hours=r.randint(0, 10))
            berth_eta = eta + timedelta(hours=r.randint(4, 10))
            position, here = "", port
        else:
            berth_eta = eta + timedelta(hours=r.randint(6, 20))
            etd = min(datetime.fromisoformat(m["etd"]) for m in members)
            frac = min(1.0, max(0.0, (today - etd) / max(timedelta(days=1), eta - etd)))
            position, here = sea_position(members[0]["origin_port"], dest, frac), "At Sea"
        vessels.append({"vessel_id": vessel_id, "name": vessel_names[vi % len(vessel_names)], "carrier_id": carrier,
                        "current_port": here, "berth_status": "at_berth" if at_port else "underway",
                        "current_position": position, "eta_port": port, "eta_timestamp": eta,
                        "eta_berth_timestamp": berth_eta, "anchored_since": None,
                        "delay_days": float(max(0, math.ceil((today - eta).total_seconds() / 86400))) if (eta < today and not at_port) else 0.0,
                        "container_count": len(v_containers), "updated_at": ago(hours=r.randint(1, 24))})

    # booked shipments: containers exist but are not yet on a vessel
    for s in ships:
        if s["status"] != "booked":
            continue
        po, per = expand(s, n_cont[s["shipment_id"]])
        lane = "Asia-UK" if s["dest_port"].startswith("GB") else "Asia-Europe"
        for lines in per:
            cid = f"CONT-{len(containers) + 1:06d}"
            value = 0.0
            for ln_no, (sku, qty, unit) in enumerate(lines, 1):
                total = round(qty * unit, 2)
                value += total
                contents.append({"container_id": cid, "line_number": ln_no, "sku": sku, "quantity": qty,
                                 "unit_cost_gbp": round(unit, 2), "total_value_gbp": total})
            containers.append({"container_id": cid, "shipment_id": s["shipment_id"], "vessel_id": None,
                               "origin_port": s["origin_port"], "destination_port": s["dest_port"],
                               "next_port": s["dest_port"], "route": lane, "transship_port": transship_for(s),
                               "container_type": "40ft", "status": "booked", "actual_arrival": None,
                               "destination_site_id": po["dest_site_id"], "value_gbp": round(value, 2),
                               "booking_date": po["order_date"], "updated_at": ago(days=1)})

    # ---------------------------------------------------------------- disruptions (history + current)
    disruptions, costs = [], []

    def disr(did, kind, port, region, start_days_ago, dur, n, desc, impact=None):
        start = g.as_of - timedelta(days=start_days_ago)
        disruptions.append({"disruption_id": did, "event_type": kind, "affected_port": port, "region": region,
                            "start_date": start, "end_date": start + timedelta(days=dur), "duration_days": dur,
                            "containers_affected": n, "description": desc, "lead_time_impact_days": impact})

    def cost(did, kind, n, per):
        costs.append({"cost_id": f"COST-{len(costs) + 1:06d}", "disruption_id": did, "cost_type": kind,
                      "cost_gbp": round(n * per, 2), "containers_affected": n, "cost_per_container_gbp": per})

    # past events (weather first: lead-time impact is planted in transit_history below)
    disr("DISR-000001", "weather", "CNYTN", "East Asia", 41, 4, 96, "Typhoon closed Yantian terminals; departures held", impact=5.5)
    disr("DISR-000002", "weather", "VNSGN", "Southeast Asia", 63, 6, 71, "Typhoon closed Ho Chi Minh City terminals", impact=6.0)
    disr("DISR-000003", "weather", "BDCGP", "South Asia", 110, 5, 58, "Cyclone halted Chittagong port operations", impact=5.0)
    disr("DISR-000004", "weather", "INNSA", "South Asia", 82, 7, 44, "Monsoon flooding cut road and rail access to Nhava Sheva", impact=4.0)
    disr("DISR-000005", "weather", "CNSHA", "East Asia", 150, 3, 84, "Typhoon suspended Shanghai Yangshan loading", impact=3.5)
    disr("DISR-000006", "weather", "NLRTM", "Northern Europe", 190, 2, 30, "Storm surge barrier closure at Rotterdam", impact=1.5)
    disr("DISR-000007", "strike", "DEHAM", "Northern Europe", 120, 3, 62, "Dockworker strike at Hamburg terminals")
    disr("DISR-000008", "strike", "NLRTM", "Northern Europe", 230, 5, 110, "Lashing crews strike at Rotterdam")
    disr("DISR-000009", "strike", "GBFXT", "UK", 300, 4, 75, "Felixstowe port workers strike")
    disr("DISR-000010", "closure", "VNSGN", "Southeast Asia", 175, 7, 98, "Terminal closed after quay crane collapse")
    disr("DISR-000011", "congestion", "NLRTM", "Northern Europe", 118, 12, 118, "Rotterdam berth congestion; vessels anchored up to five days")
    disr("DISR-000012", "congestion", "GBFXT", "UK", 200, 9, 64, "Felixstowe yard congestion after peak arrivals")
    disr("DISR-000013", "congestion", "DEHAM", "Northern Europe", 175, 8, 52, "Hamburg terminal congestion from Elbe low water")
    disr("DISR-000014", "geopolitical", "INNSA", "South Asia", 260, 40, 160, "Red Sea security diversions lengthened India-Europe sailings")
    disr("DISR-000015", "mechanical", "NLRTM", "Northern Europe", 95, 4, 40, "Quay crane failures reduced berth productivity")
    # current and scheduled events (end_date on or after today)
    disr("DISR-900001", "congestion", "NLRTM", "Northern Europe", 6, 20, 140,
         "Berth shortage and yard saturation; vessels anchored up to six days with no berth slot")
    disr("DISR-900002", "strike", "DEHAM", "Northern Europe", -4, 2, 36, "48-hour dockworker strike called by the union")
    disr("DISR-900003", "weather", "CNYTN", "East Asia", -4, 3, 22, "Typhoon forecast to make landfall; terminal closure expected")
    disr("DISR-900004", "geopolitical", "INNSA", "South Asia", 10, 40, 30, "Red Sea security advisory: carriers diverting round the Cape")

    # costs: DISR-000011 (Rotterdam congestion, the closest match to now) is the headline case
    for did, kind, n, per in [
        ("DISR-000011", "demurrage", 118, 540.0), ("DISR-000011", "detention", 118, 210.0),
        ("DISR-000011", "air_freight", 16, 4200.0), ("DISR-000011", "transshipment", 22, 780.0),
        ("DISR-000008", "demurrage", 110, 480.0), ("DISR-000008", "storage", 40, 260.0),
        ("DISR-000012", "demurrage", 64, 420.0), ("DISR-000012", "detention", 64, 180.0),
        ("DISR-000013", "demurrage", 52, 450.0), ("DISR-000013", "transshipment", 12, 820.0),
        ("DISR-000007", "demurrage", 62, 400.0), ("DISR-000007", "detention", 62, 150.0),
        ("DISR-000001", "demurrage", 96, 380.0), ("DISR-000001", "air_freight", 8, 3900.0),
        ("DISR-000002", "demurrage", 71, 410.0), ("DISR-000002", "detention", 71, 190.0),
        ("DISR-000010", "transshipment", 40, 860.0), ("DISR-000010", "demurrage", 98, 520.0),
        ("DISR-000014", "air_freight", 24, 4600.0), ("DISR-000014", "demurrage", 160, 300.0),
    ]:
        cost(did, kind, n, per)

    # ---------------------------------------------------------------- transit history
    origins = ["CNSHA", "CNYTN", "CNNGB", "VNSGN", "INNSA", "BDCGP"]
    # via port: (planned days, baseline delay, destination gateway, mode chain)
    via = {"NLRTM": (36, 1.4, "GBFXT", "sea+feeder"), "DEHAM": (37, 1.8, "GBFXT", "sea+feeder"),
           "ESVLC": (41, 1.0, "DIRFT", "sea+rail"), "GRPIR": (37, 1.9, "DIRFT", "sea+rail")}
    transit = []
    r = g.rng_for("transit_history")

    def add_transit(origin, vport, dep, delay, dwell):
        planned, _b, gw, chain = via[vport]
        actual = planned + delay
        transit.append({"route_code": "Asia-UK", "transit_id": f"TRN-{len(transit) + 1:06d}", "origin_port": origin,
                        "via_port": vport, "destination_port": gw, "mode_chain": chain,
                        "planned_transit_days": planned, "actual_transit_days": round(actual, 1),
                        "departure_date": dep, "arrival_date": dep + timedelta(days=round(actual)),
                        "delay_days": round(delay, 1), "port_dwell_hours": round(dwell, 1),
                        "containers_count": r.randint(12, 60)})

    for vport, (planned, base, gw, chain) in via.items():
        for origin in origins:
            for k in range(4):
                arrived_ago = r.randint(8, 175)
                late = arrived_ago < 56  # arrived in the last eight weeks: into the current congestion
                delay = max(0.0, r.gauss(base, 0.9))
                dwell = r.uniform(26, 50)
                if vport == "NLRTM":
                    delay += r.uniform(3.5, 6.5) if late else 0
                    dwell += r.uniform(35, 60) if late else 0
                if vport == "DEHAM" and late:
                    delay += r.uniform(1.0, 2.0)
                    dwell += r.uniform(8, 20)
                dep = g.as_of - timedelta(days=arrived_ago + round(planned + delay))
                add_transit(origin, vport, dep, delay, dwell)
    # weather events lengthen lead times for transits leaving the affected port during the event
    for d in disruptions:
        if d["lead_time_impact_days"]:
            p = d["affected_port"]
            for k in range(4):
                dep = d["start_date"] + timedelta(days=r.randint(0, d["duration_days"]))
                origin, vport = (p, r.choice(["NLRTM", "DEHAM"])) if p in origins else (r.choice(origins), "NLRTM")
                add_transit(origin, vport, dep, 2.0 + d["lead_time_impact_days"] + r.uniform(-0.8, 0.8), r.uniform(40, 70))

    # ---------------------------------------------------------------- port dwell history (weekly)
    dwell_base = {"NLRTM": 38, "DEHAM": 30, "GBFXT": 36, "GBSOU": 28, "GBLGP": 30, "CNSHA": 34, "CNNGB": 32,
                  "CNYTN": 30, "VNSGN": 30, "INNSA": 50, "BDCGP": 68, "MXZLO": 26, "USNYC": 30, "TRMER": 26,
                  "PTLEI": 22, "ESVLC": 22, "GRPIR": 26}
    dwell = []
    r = g.rng_for("port_dwell")
    weeks = g.weeks(26)
    for port, base in dwell_base.items():
        for i, wk in enumerate(weeks):
            h = base * r.uniform(0.9, 1.1)
            recent = i - 17  # last eight weeks
            if port == "NLRTM" and recent > 0:
                h += recent * 7.5
            if port == "DEHAM" and recent > 2:
                h += (recent - 2) * 4
            if port == "GBFXT" and recent > 3:
                h += (recent - 3) * 1.5
            h = round(h, 1)
            dwell.append({"port_code": port, "dwell_id": f"DWEL-{len(dwell) + 1:06d}", "arrival_date": wk,
                          "dwell_hours": h, "vessel_count": max(1, round(h / 12 + r.uniform(-1, 2))),
                          "congestion_status": "high" if h > 72 else "medium" if h > 48 else "low"})

    # ---------------------------------------------------------------- carrier ETA predictions
    # signed error = actual minus predicted (positive = arrived later than the carrier said)
    carriers = {"CAR-005": (4, 14, 38), "CAR-006": (38, 30, 30), "CAR-007": (14, 20, 34)}
    preds = []
    r = g.rng_for("eta_predictions")
    for cid, (bias, sd, voyages) in carriers.items():
        for v in range(voyages):
            arrive = ago(days=r.randint(3, 88))
            port = r.choices(["GBFXT", "GBSOU", "GBLGP"], [5, 3, 2])[0]
            for horizon in (14, 7, 3):
                scale = {14: 1.3, 7: 1.0, 3: 0.6}[horizon]
                err = r.gauss(bias * scale, sd * scale)
                predicted = arrive - timedelta(hours=err)
                preds.append({"prediction_id": f"ETA-{len(preds) + 1:06d}", "voyage_id": f"VOY-{cid[-3:]}{v + 1:03d}",
                              "carrier_id": cid, "route": "Asia-UK", "port_code": port,
                              "prediction_date": (arrive - timedelta(days=horizon)).date(),
                              "predicted_eta": predicted.replace(microsecond=0), "actual_eta": arrive,
                              "horizon_days": horizon, "eta_accuracy_hours": round(err, 1)})
    for v in range(14):
        arrive = ago(days=r.randint(3, 88))
        cid = r.choice(list(carriers))
        for horizon in (14, 7):
            err = r.gauss(6, 12)
            preds.append({"prediction_id": f"ETA-{len(preds) + 1:06d}", "voyage_id": f"VOY-{cid[-3:]}9{v + 1:02d}",
                          "carrier_id": cid, "route": "Asia-Europe", "port_code": "NLRTM",
                          "prediction_date": (arrive - timedelta(days=horizon)).date(),
                          "predicted_eta": (arrive - timedelta(hours=err)).replace(microsecond=0), "actual_eta": arrive,
                          "horizon_days": horizon, "eta_accuracy_hours": round(err, 1)})

    return {"vessels": vessels, "container_shipments": containers, "container_contents": contents,
            "transit_history": transit, "disruptions": disruptions, "disruption_costs": costs,
            "port_dwell_history": dwell, "eta_predictions": preds}
