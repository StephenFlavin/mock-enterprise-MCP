"""Generate realistic integration platform data: interfaces, EDI maps, connections, errors, feeds and costs."""
from datetime import datetime, timedelta, time


def generate(g):
    r = g.rng

    # Interface error records - some active, most resolved
    interface_errors = []
    error_interfaces = [
        ("ERP_to_WMS", "ERP", "WMS"),
        ("WMS_to_OMS", "WMS", "OMS"),
        ("ERP_to_GL", "ERP", "GL"),
        ("WMS_to_Website", "WMS", "Website"),
        ("ASN_Inbound", "Supplier", "WMS"),
    ]

    for i, (iface_name, src, dst) in enumerate(error_interfaces):
        for j in range(r.randint(2, 8)):
            occurred = g.date_between(45, 1)
            is_active = r.random() < 0.15
            error_errors = [
                "Timeout connecting to destination",
                "XML validation failed",
                "Field mapping mismatch",
                "Duplicate message id",
                "Database lock timeout",
                "Queue full - backlog building",
                "Authentication token expired",
                "Network unavailable"
            ]
            interface_errors.append({
                "error_id": f"ERR-{len(interface_errors) + 1:06d}",
                "interface_name": iface_name,
                "error_code": f"ERR{r.randint(1000, 9999)}",
                "error_message": r.choice(error_errors),
                "occurred_at": occurred,
                "source_system": src,
                "dest_system": dst,
                "message_count": r.randint(1, 500),
                "queue_depth": r.randint(0, 1000) if is_active else 0,
                "status": "active" if is_active else (r.choice(["resolved", "acknowledged"]) if r.random() < 0.8 else "active"),
                "resolved_at": occurred + timedelta(hours=r.randint(1, 24)) if not is_active and r.random() < 0.8 else None,
                "updated_at": occurred + timedelta(hours=r.randint(1, 72))
            })

    # EDI message records
    edi_messages = []
    edi_types = ["ASN", "PO_ACK", "INVOICE", "SHIPMENT", "GRN"]
    suppliers = g.master("suppliers")[:20]

    for i in range(r.randint(100, 200)):
        msg_type = r.choice(edi_types)
        sent_time = g.date_between(30, 0)
        status = r.choices(["sent", "received", "processed", "failed", "retrying"], [20, 30, 35, 10, 5])[0]
        edi_messages.append({
            "message_id": f"EDI-{len(edi_messages) + 1:06d}",
            "message_type": msg_type,
            "partner_id": r.choice([s["supplier_id"] for s in suppliers]),
            "supplier_id": r.choice([s["supplier_id"] for s in suppliers]),
            "sent_at": sent_time,
            "status": status,
            "error_details": "XML validation failed" if status == "failed" else ("Retrying due to timeout" if status == "retrying" else None),
            "line_count": r.randint(1, 500),
            "processing_time_seconds": r.gauss(2.5, 1.2) if status == "processed" else None,
            "updated_at": sent_time + timedelta(seconds=r.randint(1, 3600))
        })

    # EDI maps for different message types
    edi_maps = []
    for i, msg_type in enumerate(edi_types):
        for version_num in range(1, r.randint(2, 4)):
            edi_maps.append({
                "map_id": f"MAP-{len(edi_maps) + 1:06d}",
                "message_type": msg_type,
                "source_system": r.choice(["ERP", "WMS", "Supplier"]),
                "dest_system": r.choice(["WMS", "OMS", "GL", "Supplier"]),
                "version": f"{version_num}.0",
                "active": version_num == max(range(1, r.randint(2, 4))),
                "created_at": g.days_ago(180 - i * 20),
                "updated_at": g.days_ago(90 - i * 10),
                "change_log": f"Added field mapping for {msg_type}, fixed encoding issue" if version_num > 1 else None
            })

    # Configuration changes
    config_changes = []
    change_types_list = ["mapping", "certificate", "endpoint", "schedule", "other"]
    for i in range(r.randint(20, 40)):
        changed_when = g.date_between(60, 0)
        config_changes.append({
            "change_id": f"CFG-{len(config_changes) + 1:06d}",
            "change_type": r.choice(change_types_list),
            "interface_name": r.choice([iface[0] for iface in error_interfaces]),
            "changed_by": f"EMP-{r.randint(1000, 9999):05d}",
            "changed_at": changed_when,
            "description": r.choice([
                "Updated EDI message mapping for ASN segment packing data",
                "Renewed SSL certificate for secure endpoint",
                "Changed run frequency from hourly to 4-hourly",
                "Added new required field validation",
                "Updated partner endpoint URL"
            ]),
            "previous_value": "1.5.2" if r.random() < 0.5 else "hourly",
            "new_value": "2.0.0" if r.random() < 0.5 else "4-hourly",
            "status": r.choices(["deployed", "testing", "pending", "rolled_back"], [70, 15, 10, 5])[0],
            "updated_at": changed_when + timedelta(days=r.randint(1, 10))
        })

    # Third party connections
    third_party_connections = []
    partners = g.master("partners")
    suppliers_list = g.master("suppliers")
    carriers_list = g.master("carriers")
    connection_types_list = ["supplier", "partner", "carrier", "3pl", "api_consumer"]
    protocols_list = ["edi", "api", "sftp", "http", "webhook", "other"]
    employees = g.master("employees")

    # Supplier connections
    for sup in suppliers_list[:15]:
        third_party_connections.append({
            "connection_id": f"CON-{len(third_party_connections) + 1:06d}",
            "partner_name": sup["name"],
            "partner_id": sup["supplier_id"],
            "connection_type": "supplier",
            "protocol": r.choice(["edi", "api", "sftp"]),
            "endpoint_url": f"edi.{sup['name'].lower().replace(' ', '')}.com",
            "owner_id": r.choice([e["employee_id"] for e in employees])[:8],
            "authenticated": True,
            "privileged_access": r.random() < 0.2,
            "active": sup["status"] == "active",
            "established_at": sup.get("onboarded_date") or g.days_ago(365),
            "security_risk_rating": r.choices(["low", "medium", "high", "critical"], [50, 30, 15, 5])[0],
            "updated_at": g.days_ago(r.randint(0, 30))
        })

    # Partner connections
    for ptn in partners[:10]:
        third_party_connections.append({
            "connection_id": f"CON-{len(third_party_connections) + 1:06d}",
            "partner_name": ptn["name"],
            "partner_id": ptn["partner_id"],
            "connection_type": "partner",
            "protocol": r.choice(["api", "webhook", "sftp"]),
            "endpoint_url": f"api.{ptn['name'].lower().replace(' ', '')}.com",
            "owner_id": r.choice([e["employee_id"] for e in employees])[:8],
            "authenticated": True,
            "privileged_access": r.random() < 0.1,
            "active": ptn["status"] == "active",
            "established_at": ptn.get("since") or g.days_ago(730),
            "security_risk_rating": r.choices(["low", "medium", "high"], [60, 30, 10])[0],
            "updated_at": g.days_ago(r.randint(0, 30))
        })

    # Integration patterns
    integration_patterns = [
        ("EDI", "EDI", r.randint(15, 25)),
        ("REST_API", "api", r.randint(8, 15)),
        ("FILE_TRANSFER", "file_transfer", r.randint(5, 12)),
        ("WEBHOOK", "webhook", r.randint(3, 8)),
    ]

    patterns = []
    for name, ptype, conn_count in integration_patterns:
        patterns.append({
            "pattern_id": f"PAT-{len(patterns) + 1:06d}",
            "pattern_name": name,
            "pattern_type": ptype,
            "active_connections": conn_count,
            "description": f"{name} integration pattern for system-to-system communication",
            "updated_at": g.days_ago(r.randint(0, 60))
        })

    # Pattern run costs
    pattern_run_costs = []
    months_back = [-30 * i for i in range(3)]
    for month_offset in months_back:
        month_date = g.days_ago(-month_offset) if month_offset <= 0 else g.days_ago(month_offset)
        for pattern in patterns:
            pattern_run_costs.append({
                "cost_id": f"COS-{len(pattern_run_costs) + 1:06d}",
                "pattern_id": pattern["pattern_id"],
                "pattern_name": pattern["pattern_name"],
                "month": month_date.replace(day=1),
                "setup_cost_gbp": r.randint(500, 3000) if month_offset == -30 * 2 else 0,
                "run_cost_gbp": r.choice([150, 250, 350, 450, 550]) * pattern["active_connections"],
                "support_cost_gbp": r.choice([100, 200, 300, 400]) * pattern["active_connections"],
                "total_cost_gbp": (r.choice([150, 250, 350, 450, 550]) + r.choice([100, 200, 300, 400])) * pattern["active_connections"],
                "updated_at": g.days_ago(-month_offset + 5)
            })

    # Feed runs for stock feed
    feed_runs = []
    base_start = g.days_ago(14)
    for day_offset in range(14):
        run_date = base_start + timedelta(days=day_offset)
        for hour in range(0, 24, 4):  # Every 4 hours
            scheduled = run_date.replace(hour=hour, minute=0, second=0)
            delay_minutes = r.choice([0, 0, 0, 2, 5, 10, 15, 30])  # Most are on time
            started = scheduled + timedelta(minutes=delay_minutes)
            duration = r.gauss(45, 10)
            feed_runs.append({
                "run_id": f"RUN-{len(feed_runs) + 1:06d}",
                "feed_name": "stock_feed",
                "source_system": "WMS",
                "dest_system": "Website",
                "scheduled_time": scheduled,
                "started_at": started,
                "completed_at": started + timedelta(seconds=duration),
                "status": "completed" if r.random() < 0.95 else "failed",
                "records_processed": r.randint(5000, 15000),
                "duration_seconds": max(30, duration),
                "updated_at": scheduled + timedelta(hours=1)
            })

    # Stock reconciliation records
    stock_reconciliation = []
    products = g.master("products")[:50]
    sites = [s for s in g.master("sites") if s["type"] == "dc"]

    for i in range(r.randint(80, 150)):
        sku = r.choice(products)
        site = r.choice(sites)
        erp_qty = r.randint(100, 5000)
        diff = r.choice(list(range(-150, 151))) if r.random() < 0.3 else 0
        wms_qty = erp_qty + diff
        stock_reconciliation.append({
            "recon_id": f"REC-{len(stock_reconciliation) + 1:06d}",
            "sku": sku["sku"],
            "site_id": site["site_id"],
            "erp_balance": erp_qty,
            "wms_balance": wms_qty,
            "difference": diff,
            "difference_pct": (diff / erp_qty * 100) if erp_qty > 0 else 0,
            "created_at": g.date_between(g.days_ago(30), g.days_ago(0)),
            "status": r.choices(["new", "investigating", "resolved", "manual_adj"], [10, 20, 60, 10])[0],
            "updated_at": g.days_ago(r.randint(0, 30))
        })

    # Stock feed schedule
    stock_feed_schedule = [{
        "schedule_id": f"SCH-{len(stock_feed_schedule) + 1:06d}",
        "feed_name": "stock_feed",
        "run_frequency": "4-hourly",
        "run_time_utc": "00:00",
        "batch_size": 10000,
        "enabled": True,
        "created_at": g.days_ago(365),
        "updated_at": g.days_ago(7)
    }]

    # ASN feed metrics
    asn_feed_metrics = []
    for i in range(r.randint(25, 40)):
        measured_when = g.date_between(g.days_ago(60), g.days_ago(0))
        asn_feed_metrics.append({
            "metric_id": f"MET-{len(asn_feed_metrics) + 1:06d}",
            "measured_at": measured_when,
            "asn_messages_received": r.randint(15, 80),
            "asn_lines_received": r.randint(200, 2000),
            "lines_with_pallet_data": r.randint(100, 1500) if measured_when > g.days_ago(20) else r.randint(50, 500),
            "message_completeness_pct": r.gauss(97, 2) if measured_when > g.days_ago(20) else r.gauss(85, 10),
            "feed_status": "stable" if r.random() < 0.9 else "degraded",
            "changes": "Added pallet-level packing data support" if measured_when > g.days_ago(15) else None,
            "updated_at": measured_when + timedelta(hours=1)
        })

    return {
        "interface_errors": interface_errors,
        "edi_messages": edi_messages,
        "edi_maps": edi_maps,
        "config_changes": config_changes,
        "third_party_connections": third_party_connections,
        "integration_patterns": patterns,
        "pattern_run_costs": pattern_run_costs,
        "feed_runs": feed_runs,
        "stock_reconciliation": stock_reconciliation,
        "stock_feed_schedule": stock_feed_schedule,
        "asn_feed_metrics": asn_feed_metrics,
    }
