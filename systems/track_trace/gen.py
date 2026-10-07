"""Track and trace platform: disruptions, shipment tracking, port congestion, transit history."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng

    # Get ocean carriers and ports from master
    ocean_carriers = [c["carrier_id"] for c in g.master("carriers") if c["mode"] in ("ocean", "forwarder")]
    all_ports = [p["port_code"] for p in g.master("ports")]
    asia_ports = ["CNSHA", "CNNGB", "CNYTN"]
    uk_ports = ["GBFXT", "GBSOU", "GBLGP"]
    eu_ports = ["NLRTM", "DEHAM", "PTLEI"]

    disruptions = []
    shipment_tracking = []
    port_congestion = []
    transit_history = []
    shipment_batches = []
    planning_buffers = []

    # Disruptions: some active, some historical
    disruption_events = [
        ("weather", "Asia", "Typhoon season delays in South China Sea", 2),
        ("congestion", "GBFXT", "High vessel queue at Felixstowe terminal", 3),
        ("labor_action", "EU Central", "Port worker strikes in Rotterdam", 1),
        ("customs_hold", "GBFXT", "UK customs processing delays", 2),
        ("port_closure", "JPYOK", "Typhoon warning closure of Tokyo Bay", 4),
    ]

    for i, (event_type, region, desc, impact) in enumerate(disruption_events, 1):
        days_ago = r.randint(1, 21)
        reported_at = g.days_ago(days_ago)
        is_active = days_ago <= 7
        status = r.choices(["active", "monitoring", "resolved"], [50, 30, 20])[0] if is_active else "resolved"

        disruptions.append({
            "disruption_id": f"DIS-{i:06d}",
            "reported_at": reported_at,
            "event_type": event_type,
            "region": region,
            "severity": r.choices(["low", "medium", "high", "critical"], [10, 30, 40, 20])[0],
            "status": status,
            "description": desc,
            "estimated_impact_days": impact,
            "resolved_at": reported_at + timedelta(days=impact) if status == "resolved" else None,
            "updated_at": reported_at + timedelta(days=max(1, impact - 1))
        })

    # Shipment tracking: one per ocean/air PO
    pos = g.master("purchase_orders")
    shipment_idx = 0
    for po in pos:
        if po["mode"] not in ("sea", "air") or po["status"] in ("cancelled", "draft"):
            continue
        shipment_idx += 1

        po_id = po["po_id"]
        dest_dc = po["dest_site_id"]
        mode = po["mode"]
        due_date = datetime.fromisoformat(po["due_date"]).date()

        # Determine ports
        if mode == "sea":
            origin = r.choice(asia_ports)
            dest = r.choice(uk_ports + eu_ports)
        else:
            origin = r.choice(asia_ports)
            dest = r.choice(uk_ports)

        # Calculate planned vs predicted
        carrier = r.choice(ocean_carriers)
        planned_days = r.randint(28, 45) if mode == "sea" else r.randint(2, 4)
        planned_arrival = due_date

        # Generate predicted ETA with some variance
        days_now = (datetime.now().date() - g.as_of).days
        eta_variance = r.gauss(0, 3)  # days of variance
        predicted_eta = due_date + timedelta(days=eta_variance)

        # Determine status based on timing
        if due_date < g.as_of:
            status = r.choices(["delivered", "delayed"], [80, 20])[0]
            actual = due_date + timedelta(days=max(0, int(eta_variance)))
            eta_acc = int((actual - due_date).days)
        elif (due_date - g.as_of).days <= 7:
            status = r.choices(["in_transit", "at_port"], [70, 30])[0]
            actual = None
            eta_acc = None
        else:
            status = r.choices(["booked", "in_transit"], [60, 40])[0]
            actual = None
            eta_acc = None

        shipment_tracking.append({
            "shipment_id": f"SHP-{shipment_idx:07d}",
            "po_id": po_id,
            "carrier_id": carrier,
            "mode": mode,
            "origin_port": origin,
            "dest_port": dest,
            "dest_site_id": dest_dc,
            "planned_arrival": planned_arrival,
            "predicted_eta": predicted_eta,
            "actual_arrival": actual,
            "eta_accuracy_days": eta_acc,
            "priority_flag": False,
            "status": status,
            "updated_at": datetime.now() - timedelta(hours=r.randint(1, 72))
        })

    # Port congestion history
    for port in uk_ports + eu_ports + asia_ports:
        for days_back in range(90, -1, -7):  # Weekly data for last 90 days
            meas_date = g.days_ago(days_back)

            # Realistic variance: some ports more congested
            base_dwell = 48 if port == "GBFXT" else (36 if port in eu_ports else 24)
            congestion_level = r.choices(["low", "medium", "high", "critical"], [20, 40, 30, 10])[0]

            dwell_variance = {"low": 0.8, "medium": 1.0, "high": 1.5, "critical": 2.0}[congestion_level]
            avg_dwell = base_dwell * dwell_variance

            port_congestion.append({
                "port_code": port,
                "measurement_date": meas_date,
                "avg_dwell_hours": round(avg_dwell, 1),
                "max_dwell_hours": round(avg_dwell * r.uniform(1.2, 1.8), 1),
                "vessel_queue_length": int(r.gauss(5, 2) * (1.5 if congestion_level in ("high", "critical") else 1)),
                "congestion_level": congestion_level,
                "notes": ""
            })

    # Transit history: actual lane performance
    lanes = [
        ("SGSIN", "GBFXT", "FAL7"),
        ("CNSHA", "GBFXT", "FAL9"),
        ("HKHKG", "NLRTM", "EC7"),
        ("SGSIN", "NLRTM", "FAL7"),
    ]

    for origin, dest, service in lanes:
        carriers_for_lane = [c["carrier_id"] for c in g.master("carriers") if c["mode"] in ("ocean", "forwarder")]

        for days_back in range(180, -1, -14):  # Bi-weekly data for 6 months
            transit_date = g.days_ago(days_back)
            carrier = r.choice(carriers_for_lane)

            # Planned transit time depends on route
            if origin in asia_ports and dest in uk_ports:
                planned = 28
            elif origin in asia_ports and dest in eu_ports:
                planned = 26
            else:
                planned = 20

            # Actual variance
            variance_pct = r.gauss(2, 8)  # percentage variance
            actual_days = planned * (1 + variance_pct / 100)

            transit_history.append({
                "origin_port": origin,
                "dest_port": dest,
                "carrier_id": carrier,
                "service": service,
                "transit_date": transit_date,
                "mode": "sea",
                "transit_time_days": round(actual_days, 1),
                "planned_days": float(planned),
                "variance_pct": round(variance_pct, 1)
            })

    # Shipment batches: one or more per shipment
    for i, ship in enumerate(shipment_tracking[:min(len(shipment_tracking), 50)]):
        po_id = ship["po_id"]
        po = next((p for p in pos if p["po_id"] == po_id), None)

        if not po:
            continue

        # Get SKUs from this PO
        po_lines = [l for l in g.master("po_lines") if l["po_id"] == po_id]

        for line_idx, line in enumerate(po_lines[:3]):  # Limit batches per shipment
            sku = line["sku"]
            batch_idx = i * 10 + line_idx + 1

            qty_ordered = int(line["qty_ordered"])
            batches_in_shipment = max(1, qty_ordered // 500)
            for batch_num in range(batches_in_shipment):
                batch_units = qty_ordered // batches_in_shipment
                mfg_date = datetime.fromisoformat(po["order_date"]).date() + timedelta(days=r.randint(7, 21))

                shipment_batches.append({
                    "batch_id": f"BAT-{batch_idx * 100 + batch_num:06d}",
                    "sku": sku,
                    "shipment_id": ship["shipment_id"],
                    "factory_id": po.get("factory_id", "FAC-0001"),
                    "batch_number": f"MFG-{mfg_date.strftime('%Y%m%d')}-{batch_num:03d}",
                    "units_shipped": batch_units,
                    "manufacturing_date": mfg_date,
                    "status": ship["status"] if ship["status"] in ("in_transit", "at_port", "delivered") else "in_transit",
                    "updated_at": ship["updated_at"]
                })

    # Planning buffers: standard lanes
    for origin, dest, service in lanes:
        planning_buffers.append({
            "origin_port": origin,
            "dest_port": dest,
            "service": service,
            "current_buffer_days": 14.0,
            "recommended_buffer_days": 16.5,
            "accuracy_score": 78.5,
            "last_updated": datetime.now()
        })

    return {
        "disruptions": disruptions,
        "shipment_tracking": shipment_tracking,
        "port_congestion": port_congestion,
        "transit_history": transit_history,
        "shipment_batches": shipment_batches,
        "planning_buffers": planning_buffers
    }
