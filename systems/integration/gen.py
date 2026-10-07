"""Integration platform data: interface errors, EDI traffic and maps, config changes, connections, feeds, costs and stock reconciliation.

Story rows (seed/*.csv and the blocks marked STORY below) are the ones the persona questions find; everything else is quiet background.
"""
import re
from datetime import datetime, time, timedelta

TECH = ["EMP-00095", "EMP-00096", "EMP-00097", "EMP-00098", "EMP-00099", "EMP-00100"]


def _dt(d, h=0, m=0, s=0):
    return datetime.combine(d, time(h, m, s))


def generate(g):
    r = g.rng
    today = g.as_of

    # ---- interface errors: sparse, benign, old background (the live incidents are in seed/interface_errors.csv)
    interfaces = [("ERP_to_WMS", "ERP", "WMS"), ("WMS_to_OMS", "WMS", "OMS"), ("ERP_to_GL", "ERP", "GL"),
                  ("WMS_to_Website", "WMS", "Website"), ("ASN_Inbound", "Supplier", "WMS")]
    noise = [("Timeout connecting to destination", "connectivity"), ("Authentication token expired", "auth"),
             ("Database lock timeout", "connectivity"), ("Network unavailable", "connectivity"),
             ("Duplicate message id", "duplicate")]
    interface_errors = []
    for back in range(250, 8, -1):
        if r.random() > 0.11:
            continue
        name, src, dst = r.choice(interfaces)
        msg, cat = r.choice(noise)
        at = _dt(today - timedelta(days=back), r.randint(1, 22), r.randint(0, 59))
        resolved = r.random() < 0.8
        interface_errors.append({
            "error_id": f"ERR-{len(interface_errors) + 1:06d}", "interface_name": name,
            "error_code": f"ERR{r.randint(1000, 3999)}", "error_message": msg, "occurred_at": at,
            "source_system": src, "dest_system": dst, "message_count": r.randint(1, 60), "queue_depth": 0,
            "status": "resolved" if resolved else "acknowledged",
            "resolved_at": at + timedelta(hours=r.randint(1, 8)) if resolved else None,
            "updated_at": at + timedelta(hours=r.randint(2, 24)), "category": cat,
        })

    # ---- EDI maps (ASN and PO_ACK maps are story rows in seed/edi_maps.csv)
    edi_maps = []
    other_maps = {"INVOICE": ("Supplier", "GL"), "SHIPMENT": ("Carrier", "WMS"), "GRN": ("WMS", "ERP")}
    map_id_for = {"ASN": "MAP-900001", "PO_ACK": "MAP-900003"}
    for i, (mt, (src, dst)) in enumerate(other_maps.items()):
        for ver in (1, 2):
            mid = f"MAP-{len(edi_maps) + 1:06d}"
            edi_maps.append({
                "map_id": mid, "message_type": mt, "source_system": src, "dest_system": dst, "version": f"1.{ver}",
                "active": ver == 2, "created_at": _dt(g.days_ago(300 - 40 * i - 90 * (2 - ver)), 9),
                "updated_at": _dt(g.days_ago(200 - 40 * i - 60 * (2 - ver)), 9),
                "change_log": f"v1.{ver}: standard {mt} mapping" + (", fixed date format handling" if ver == 2 else ""),
                "segments_mapped": "Header, party, line and quantity segments",
            })
            if ver == 2:
                map_id_for[mt] = mid

    # ---- EDI messages: steady traffic, then the overnight PO_ACK failures (STORY 09:83:Q1)
    suppliers = [s["supplier_id"] for s in g.master("suppliers")[:40]]
    types = ["ASN", "PO_ACK", "INVOICE", "SHIPMENT", "GRN"]
    weights = [30, 25, 20, 15, 10]
    bg_fail = [("partner_side", "Partner endpoint returned HTTP 500"), ("connectivity", "Timeout waiting for partner acknowledgement")]
    edi_messages = []

    def add_msg(mt, sup, at, status, cat=None, detail=None, lines=None):
        edi_messages.append({
            "message_id": f"EDI-{len(edi_messages) + 1:06d}", "message_type": mt, "supplier_id": sup, "sent_at": at,
            "status": status, "error_category": cat, "error_details": detail, "map_id": map_id_for[mt],
            "line_count": lines or r.randint(1, 120),
            "processing_time_seconds": round(max(0.4, r.gauss(2.5, 0.8)), 2) if status == "processed" else None,
            "updated_at": at + timedelta(seconds=r.randint(5, 900)),
        })

    for back in range(30, -1, -1):
        day = today - timedelta(days=back)
        n = 0 if day.weekday() >= 5 else r.randint(18, 28)
        for _ in range(n):
            mt = r.choices(types, weights)[0]
            at = _dt(day, r.randint(6, 18), r.randint(0, 59), r.randint(0, 59))
            if back == 0 and at.hour >= 9:
                continue
            if r.random() < 0.012:
                cat, detail = r.choice(bg_fail)
                add_msg(mt, r.choice(suppliers), at, "failed", cat, detail)
            else:
                add_msg(mt, r.choice(suppliers), at, "processed")
    # PO_ACK map v1.1 went live the evening before: suppliers' acknowledgements overnight
    night = today
    causes = ([("mapping", "Mapping error: ACK_STATUS code not in PO_ACK map v1.1 code list (expected AC, AP or RJ)")] * 171
              + [("format", "XML validation failed: invalid date format in DTM segment")] * 17
              + [("partner_side", "Partner endpoint returned HTTP 500")] * 12)
    r.shuffle(causes)
    story_sups = suppliers[:38]
    for i, (cat, detail) in enumerate(causes):
        at = _dt(night, 1, 20) + timedelta(seconds=int(i * (3 * 3600 + 30 * 60) / 200) + r.randint(0, 40))
        add_msg("PO_ACK", story_sups[i % len(story_sups)], at, "failed", cat, detail, lines=r.randint(5, 60))
        if cat == "partner_side":
            edi_messages[-1]["map_id"] = None
    for _ in range(14):
        at = _dt(night, 1, 20) + timedelta(seconds=r.randint(0, 3 * 3600 + 1800))
        add_msg("PO_ACK", r.choice(story_sups), at, "processed")

    # ---- config changes: only certificate/endpoint background; mapping and schedule changes are story rows in seed
    config_changes = []
    for _ in range(12):
        at = _dt(g.date_between(44, 2), r.randint(8, 17), r.randint(0, 59))
        cert = r.random() < 0.5
        config_changes.append({
            "change_id": f"CFG-{len(config_changes) + 1:06d}", "change_type": "certificate" if cert else "endpoint",
            "interface_name": r.choice(["ERP_to_GL", "ASN_Inbound", "WMS_to_Website", "WMS_to_OMS"]),
            "changed_by": r.choice(TECH), "changed_at": at,
            "description": "Renewed TLS certificate" if cert else "Updated partner endpoint URL",
            "previous_value": "expiring certificate" if cert else "previous endpoint",
            "new_value": "renewed for one year" if cert else "new endpoint",
            "status": "deployed", "updated_at": at + timedelta(hours=1),
        })

    # ---- third-party connections (STORY 09:85:Q3: the critical, privileged ones are the top risks)
    def slug(s):
        return re.sub(r"[^a-z0-9]+", "", s.lower())

    sup_master = {s["supplier_id"]: s for s in g.master("suppliers")}
    ptn_master = {p["partner_id"]: p for p in g.master("partners")}
    car_master = {c["carrier_id"]: c for c in g.master("carriers")}
    access_by_proto = {"edi": "EDI gateway (inbound documents)", "api": "API gateway (read only)",
                       "sftp": "SFTP drop folder (files only)", "webhook": "Webhook receiver", "http": "Web portal"}
    conns = []

    def add_conn(cid, name, ext, ctype, proto, owner, priv, active, since, risk, access, auth=True):
        conns.append({
            "connection_id": cid, "partner_name": name, "external_id": ext, "connection_type": ctype, "protocol": proto,
            "endpoint_url": f"{'edi' if proto == 'edi' else 'sftp' if proto == 'sftp' else 'api'}.{slug(name)}.com",
            "owner_id": owner, "authenticated": auth, "privileged_access": priv, "active": active,
            "established_at": since, "security_risk_rating": risk, "systems_accessed": access,
            "updated_at": _dt(g.days_ago(r.randint(1, 30)), 9),
        })

    for i, sup in enumerate(list(sup_master.values())[:15]):
        proto = r.choice(["edi", "edi", "api", "sftp"])
        add_conn(f"CON-{i + 1:06d}", sup["name"], sup["supplier_id"], "supplier", proto, r.choice(TECH),
                 sup["supplier_id"] == "SUP-0006", sup["status"] == "active", sup["onboarded_date"] or g.days_ago(365),
                 "low" if sup["supplier_id"] == "SUP-0006" else r.choices(["low", "medium"], [70, 30])[0], access_by_proto[proto])
    for j, ptn in enumerate(list(ptn_master.values())[:10]):
        proto = {"marketplace": "webhook", "franchise": "api"}.get(ptn["type"]) or r.choice(["edi", "edi", "sftp"])
        add_conn(f"CON-{16 + j:06d}", ptn["name"], ptn["partner_id"], "partner", proto, r.choice(TECH), False,
                 ptn["status"] == "active", ptn["since"], r.choices(["low", "medium"], [65, 35])[0], access_by_proto[proto])
    for cid, car in [("CON-000026", "CAR-001"), ("CON-000027", "CAR-002")]:
        c = car_master[car]
        add_conn(cid, c["name"], car, "carrier", "api", r.choice(TECH), False, True, g.days_ago(900), "medium",
                 "API gateway (read only)")
    # story rows
    def story(cid, ext, ctype, proto, owner, priv, since, risk, access, name=None):
        nm = name or (sup_master[ext]["name"] if ext in sup_master else ptn_master[ext]["name"])
        add_conn(cid, nm, ext, ctype, proto, owner, priv, True, since, risk, access)

    story("CON-900001", "SUP-0001", "supplier", "edi", "EMP-00095", False, "2024-03-15", "high", "EDI gateway and API gateway (read/write on PO lines, purchase orders, shipments)")
    story("CON-900002", "SUP-0002", "supplier", "api", "EMP-00096", False, "2023-06-20", "medium", "Logistics portal and API gateway (shipments, tracking)")
    story("CON-900003", "SUP-0003", "supplier", "api", "EMP-00097", True, "2025-01-10", "critical", "API gateway admin and data sync: customer data and inventory (direct system access)")
    story("CON-900004", "SUP-0004", "supplier", "sftp", "EMP-00098", False, "2022-11-05", "low", "Customs portal (documents)")
    story("CON-900005", "SUP-0005", "supplier", "edi", "EMP-00099", False, "2023-09-01", "medium", "EDI gateway (purchase orders)")
    story("CON-900006", "SUP-0049", "supplier", "sftp", "EMP-00100", True, "2021-05-17", "critical", "Direct SFTP write to the ERP inbound folder and supplier portal admin (direct system access)")
    story("CON-900007", "SUP-0044", "supplier", "api", "EMP-00097", True, "2022-02-08", "critical", "API gateway read/write: inventory, order placement and bank details (direct system access)")
    story("CON-900008", "SUP-0057", "supplier", "api", "EMP-00096", True, "2023-04-12", "high", "API gateway read/write: inventory and order placement")
    story("CON-900009", "PTN-009", "partner", "sftp", "EMP-00095", True, "2024-06-27", "high", "SFTP drop into the wholesale EDI folder (direct write)")
    story("CON-900010", "PTN-001", "partner", "edi", "EMP-00098", False, "2025-12-09", "medium", "EDI gateway (wholesale orders)")
    third_party_connections = conns

    # ---- integration patterns and what they cost (counts come from the connections above)
    proto_pattern = {"edi": "edi", "api": "api", "http": "api", "sftp": "file_transfer", "webhook": "webhook", "other": "other"}
    pat_def = [("EDI", "edi", 190, 150, 4500, "EDI integration (AS2/VAN) for document exchange with suppliers and partners"),
               ("REST_API", "api", 140, 110, 6500, "REST API integration for real-time data exchange"),
               ("FILE_TRANSFER", "file_transfer", 60, 70, 1800, "SFTP file transfer for batch data exchange"),
               ("WEBHOOK", "webhook", 80, 60, 2500, "Webhook integration for event-driven updates")]
    patterns, pattern_run_costs = [], []
    for name, ptype, run_rate, sup_rate, setup, desc in pat_def:
        cnt = sum(1 for c in conns if c["active"] and proto_pattern[c["protocol"]] == ptype)
        cnt = max(cnt, 1)
        pid = f"PAT-{len(patterns) + 1:06d}"
        patterns.append({"pattern_id": pid, "pattern_name": name, "pattern_type": ptype, "active_connections": cnt,
                         "description": desc, "updated_at": g.days_ago(20)})
        for m in range(4):
            f = 1 - 0.01 * m
            run, sup = round(run_rate * cnt * f), round(sup_rate * cnt * f)
            pattern_run_costs.append({
                "cost_id": f"COS-{len(pattern_run_costs) + 1:06d}", "pattern_id": pid, "pattern_name": name, "months_ago": m,
                "setup_cost_gbp": setup, "run_cost_gbp": run, "support_cost_gbp": sup, "total_cost_gbp": run + sup,
                "updated_at": g.days_ago(5 + 30 * m)})

    # ---- stock feed: runs every 5 min with a 1 min batch window until the schedule change (STORY 09:83:Q5), then every 15 min with a 15 min window
    change_at = _dt(today - timedelta(days=14), 20, 0)
    feed_runs = []
    t = _dt(today - timedelta(days=28), 0, 0)
    end = _dt(today, 8, 0)
    while t <= end:
        post = t >= change_at
        wait = 900 if post else 60
        dur = max(60, r.gauss(300 if post else 240, 25))
        start = t + timedelta(seconds=r.randint(0, 20))
        failed = r.random() < 0.012
        feed_runs.append({
            "run_id": f"RUN-{len(feed_runs) + 1:06d}", "feed_name": "stock_feed", "source_system": "WMS", "dest_system": "Website",
            "scheduled_time": t, "started_at": start, "completed_at": start + timedelta(seconds=dur),
            "status": "failed" if failed else "completed",
            "records_processed": 0 if failed else (r.randint(4000, 6500) if post else r.randint(250, 520)),
            "duration_seconds": round(dur, 1), "batch_wait_seconds": float(wait + r.randint(-20, 20)) if post else float(wait + r.randint(-6, 6)),
            "updated_at": start + timedelta(seconds=dur),
        })
        t += timedelta(minutes=15 if post else 5)
    stock_feed_schedule = [{
        "schedule_id": "SCH-000001", "feed_name": "stock_feed", "run_frequency": "every 15 minutes", "run_time_utc": "continuous",
        "batch_size": 20000, "enabled": True, "created_at": _dt(g.days_ago(400), 8), "updated_at": change_at,
    }]

    # ---- ASN feed: daily metrics; from the v1.4 change (STORY 09:81:Q1) the feed is ~8 h late and PO_ID completeness drops to ~92%
    asn_change = today - timedelta(days=27)
    asn_feed_metrics = []
    for back in range(60, -1, -1):
        day = today - timedelta(days=back)
        post = day >= asn_change
        msgs = r.randint(52, 80) if day.weekday() < 5 else r.randint(10, 25)
        lines = msgs * r.randint(14, 20)
        asn_feed_metrics.append({
            "metric_id": f"MET-{len(asn_feed_metrics) + 1:06d}", "measured_at": _dt(day, 8), "asn_messages_received": msgs,
            "asn_lines_received": lines, "lines_with_pallet_data": int(lines * r.uniform(0.04, 0.07)),
            "message_completeness_pct": round(r.uniform(90.8, 93.4) if post else r.uniform(98.4, 99.7), 1),
            "avg_arrival_delay_hours": round(r.uniform(7.6, 8.6) if post else r.uniform(0.3, 0.8), 1),
            "feed_status": "degraded" if post else "stable",
            "changes": ("ASN map v1.4 deployed: delivery moved from per-message to an 8-hourly batch; PO number read from header only (CFG-900001)"
                        if day == asn_change else None),
            "updated_at": _dt(day, 9),
        })

    # ---- stock reconciliation background: small, mostly settled count variances (the big story rows are in seed)
    dcs = [d for d in g.master("dc_stock") if int(d["on_hand"]) > 300]
    cost = {p["sku"]: float(p["unit_cost_gbp"]) for p in g.master("products")}
    stock_reconciliation = []
    for d in r.sample(dcs, 25):
        erp = int(d["on_hand"])
        diff = r.choice([-1, 1]) * r.randint(1, 30)
        at = _dt(today - timedelta(days=r.randint(2, 14)), r.randint(6, 16), r.randint(0, 59))
        stock_reconciliation.append({
            "recon_id": f"REC-{len(stock_reconciliation) + 1:06d}", "sku": d["sku"], "site_id": d["site_id"],
            "erp_balance": erp, "wms_balance": erp + diff, "difference": diff, "difference_pct": round(diff / erp * 100, 2),
            "value_gbp": round(abs(diff) * cost[d["sku"]], 2), "cause": "count_variance", "cause_type": "real",
            "note": "Cycle count variance after recount", "created_at": at,
            "status": r.choices(["resolved", "manual_adj", "investigating"], [60, 25, 15])[0], "updated_at": at + timedelta(days=1),
        })

    return {
        "interface_errors": interface_errors, "edi_messages": edi_messages, "edi_maps": edi_maps,
        "config_changes": config_changes, "third_party_connections": third_party_connections,
        "integration_patterns": patterns, "pattern_run_costs": pattern_run_costs, "feed_runs": feed_runs,
        "stock_reconciliation": stock_reconciliation, "stock_feed_schedule": stock_feed_schedule,
        "asn_feed_metrics": asn_feed_metrics,
    }
