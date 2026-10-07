"""Generate data for ITSM system."""

def generate(g):
    """Generate incident tickets, change requests, faults, and monitoring data."""

    # System names and interfaces
    systems = ["WMS", "POS", "ERP", "Order API", "Stock Feed", "Payment Gateway", "Website", "AMR Fleet"]
    interfaces = [
        {"name": "Order API", "source": "Website", "target": "WMS", "msg_type": "order"},
        {"name": "Stock Feed", "source": "WMS", "target": "Website", "msg_type": "inventory"},
        {"name": "EDI Inbound", "source": "Supplier", "target": "WMS", "msg_type": "ASN"},
        {"name": "ERP Integration", "source": "WMS", "target": "ERP", "msg_type": "stock"},
    ]

    areas = ["warehouse", "checkout", "office", "loading_dock"]
    sites = ["DC1", "DC2", "DC3", "ST001", "ST100", "ST214"]
    error_types = ["checkout_error", "payment_gateway", "inventory_sync", "order_allocation", "wifi_disconnect"]

    tech = [e["employee_id"] for e in g.master("employees") if e["department"] == "Technology"]
    rng = g.rng
    sites_list = g.master("sites")

    def ts(days_back, hour=None, minute=None):
        """A timestamp days_back days before as_of."""
        h = rng.randint(7, 18) if hour is None else hour
        m = rng.randint(0, 59) if minute is None else minute
        return f"{g.days_ago(days_back).isoformat()} {h:02d}:{m:02d}:00"

    # Background incident tickets: resolved or in progress, none about the question stories
    inc_templates = [
        ("WMS", "WMS handheld login timeouts at {site}", "Operators at {site} report handheld sessions dropping after 20 minutes."),
        ("WMS", "Wave planner slow to release waves", "Wave release taking over 3 minutes at {site}; no data loss."),
        ("POS", "Till receipt printer offline at {site}", "Receipt printer on till 4 at {site} not responding after a restart."),
        ("ERP", "Month-end batch job overran", "Nightly ERP batch finished 90 minutes late; downstream reports delayed."),
        ("Payment Gateway", "Intermittent card declines", "A small share of card payments declined with a gateway code at {site}."),
        ("Website", "Product images slow to load", "Image CDN latency raised for some UK users; no errors."),
        ("AMR Fleet", "Robot charger fault at {site}", "Charging bay 3 at {site} not delivering power; robots rerouted."),
        ("Order API", "Elevated 5xx on order submission", "Short burst of 5xx responses from the order API; recovered by itself."),
    ]
    sites3 = ["DC1", "DC2", "DC3", "ST001", "ST100", "ST214"]
    teams = ["WMS Support", "Interface Team", "Store Systems", "Web Platform Team", "Infrastructure"]
    incident_tickets = []
    for i in range(36):
        sysn, title, desc = inc_templates[i % len(inc_templates)]
        site = sites3[rng.randrange(len(sites3))]
        raised_back = rng.randint(6, 85)
        resolved = rng.random() > 0.15
        res_back = max(0, raised_back - rng.randint(0, 3)) if resolved else None
        incident_tickets.append({
            "incident_id": f"INC-{4000 + i:06d}",
            "title": title.format(site=site),
            "description": desc.format(site=site),
            "status": rng.choice(["resolved", "closed"]) if resolved else rng.choice(["open", "investigating"]),
            "severity": rng.choices(["critical", "high", "medium", "low"], [1, 3, 5, 4])[0],
            "assigned_to": rng.choice(tech),
            "assigned_team": rng.choice(teams),
            "system_affected": sysn,
            "source_error_id": None,
            "raised_at": ts(raised_back, 9),
            "resolved_at": ts(res_back, 14) if resolved else None,
            "updated_at": ts(res_back if resolved else raised_back, 14 if resolved else 9),
        })

    # Background change requests (the story change requests are in seed/change_requests.csv)
    chg_templates = [
        ("WMS", "patch", "WMS 9.2 handheld label fix"), ("POS", "patch", "POS client security update"),
        ("ERP", "configuration", "ERP batch schedule change"), ("Website", "configuration", "CDN cache rule update"),
        ("AMR Fleet", "firmware", "AMR charger firmware update"), ("Integration", "configuration", "Interface retry settings"),
        ("Payment Gateway", "patch", "Gateway client library update"), ("Order API", "patch", "Order API dependency update"),
    ]
    change_requests = []
    for i in range(30):
        sysn, ctype, title = chg_templates[i % len(chg_templates)]
        created_back = rng.randint(10, 150)
        stage = rng.choices(["implemented", "approved", "submitted", "draft", "rejected"], [14, 5, 4, 5, 2])[0]
        submitted_back = created_back - rng.randint(1, 5)
        approved_back = submitted_back - rng.randint(2, 7)
        impl_back = approved_back - rng.randint(1, 10)
        if stage in ("implemented", "approved", "rejected") and approved_back < 1:
            approved_back, submitted_back, impl_back = 6, 11, 2
            created_back = max(created_back, 14)
        row = {"change_id": f"CHG-{5000 + i:06d}", "title": title, "description": f"{title} for {sysn}, standard change.",
               "change_type": ctype, "status": stage, "assigned_to": rng.choice(tech), "system_affected": sysn,
               "created_at": ts(created_back, 9), "planned_date": None, "submitted_at": None, "approved_at": None,
               "implemented_at": None}
        if stage != "draft":
            row["submitted_at"] = ts(submitted_back, 11)
        if stage in ("implemented", "approved", "rejected"):
            row["approved_at"] = ts(approved_back, 14)
        if stage == "implemented":
            row["implemented_at"] = ts(max(impl_back, 0), 20)
            row["planned_date"] = g.days_ago(max(impl_back, 0)).isoformat()
        else:
            row["planned_date"] = g.days_ago(-rng.randint(7, 60)).isoformat()
        row["updated_at"] = row["implemented_at"] or row["approved_at"] or row["submitted_at"] or row["created_at"]
        change_requests.append(row)

    # Background self-checkout fault tickets: a few per store, never at the five stores in the shrink story
    story_stores = {"ST150", "ST159", "ST165", "ST181", "ST183"}
    stores = [x["site_id"] for x in g.master("sites") if x["type"] == "store" and x["site_id"] not in story_stores]
    fault_types = [("payment failure", "Card reader on the unit declined every payment until restarted."),
                   ("display issue", "Touchscreen unresponsive in the lower third of the screen."),
                   ("scanning error", "Customer reported the scanner needed several attempts per item."),
                   ("software crash", "Unit rebooted mid-transaction and lost the basket.")]
    fault_tickets = []
    for i in range(16):
        site = stores[rng.randrange(len(stores))]
        raised_back = rng.randint(4, 29)
        fixed = rng.random() > 0.25
        ftype, fdesc = fault_types[rng.randrange(len(fault_types))]
        fault_tickets.append({
            "fault_id": f"FLT-{4000 + i:06d}",
            "site_id": site,
            "device_id": f"SCO-{site[2:]}-{rng.randint(1, 8):02d}",
            "fault_type": ftype,
            "description": fdesc,
            "status": "repaired" if fixed else rng.choice(["open", "investigating"]),
            "severity": rng.choices(["high", "medium", "low"], [1, 4, 5])[0],
            "raised_at": ts(raised_back, 9),
            "resolved_at": ts(max(raised_back - rng.randint(0, 2), 0), 16) if fixed else None,
            "updated_at": ts(max(raised_back - 1, 0), 16),
        })

    # Background website errors: small, mostly resolved (the story errors are in seed/site_errors.csv)
    err_templates = [("search_error", "/search", "Search suggestions timed out"),
                     ("login_error", "/account/login", "Login rejected a valid password reset token"),
                     ("basket_error", "/basket", "Basket total did not refresh after quantity change"),
                     ("search_error", "/category", "Category filter returned an empty page"),
                     ("login_error", "/account/login", "Social login redirect failed")]
    site_errors = []
    for i in range(18):
        etype, page, msg = err_templates[i % len(err_templates)]
        first_back = rng.randint(3, 29)
        last_back = max(first_back - rng.randint(0, 6), 1)
        st = rng.choices(["resolved", "ignored", "investigating"], [8, 4, 2])[0]
        n = rng.randint(6, 90)
        site_errors.append({
            "error_id": f"ERR-{4000 + i:06d}",
            "error_type": etype,
            "page": page,
            "device": rng.choice(["mobile", "desktop", "all"]),
            "error_message": msg,
            "error_count": n,
            "sessions_affected": int(n * rng.uniform(0.7, 0.95)),
            "first_seen": ts(first_back, 8),
            "last_seen": ts(last_back, 17),
            "status": st,
            "resolution": "Fixed in the next routine release" if st == "resolved" else ("Low impact, accepted" if st == "ignored" else None),
            "created_at": ts(first_back, 8),
            "updated_at": ts(last_back, 17),
        })

    # Generate security remediation tasks
    security_tasks = []
    for i in range(25):
        created_days = g.rng.randint(1, 60)
        created = g.days_ago(created_days)
        due = g.days_ago(g.rng.randint(-30, max(-1, created_days - 7)))

        completed = None
        if g.rng.random() > 0.5:
            completed = g.days_ago(g.rng.randint(0, max(0, created_days - 1)))

        security_tasks.append({
            "task_id": f"SEC-{900000 + i:06d}",
            "finding_id": f"VULN-{g.rng.randint(1, 200):03d}",
            "title": f"{g.rng.choice(['Patch vulnerability', 'Fix misconfiguration', 'Implement control', 'Review access'])}",
            "description": g.fake.sentence(nb_words=10),
            "risk_level": g.rng.choice(["critical", "high", "medium", "low"]),
            "status": "completed" if completed else g.rng.choice(["open", "in_progress"]),
            "assigned_to": g.pick(g.master("employees"), k=1)[0]["employee_id"],
            "due_date": due,
            "created_at": created,
            "updated_at": completed or created,
        })

    # Load tests, interfaces and peak history are hand-written in seed/ (load_test_runs, system_interfaces, interface_peak_load)
    load_test_runs, system_interfaces, interface_peak_load = [], [], []

    # WiFi load by area and hour for the last 14 days at the three UK DCs.
    # DC1 warehouse is busy and slow between 14:00 and 16:00 (robots reconnecting and charging); the others stay flat.
    import random
    wr = random.Random(20261005)  # own stream so the story numbers do not depend on other tables
    wifi_load = []
    n_wifi = 100000
    shape = {  # share of the daytime device load by hour
        **{h: 0.35 for h in range(0, 6)}, **{h: 0.8 for h in range(6, 22)}, **{h: 0.5 for h in range(22, 24)}}
    area_base = {"warehouse": 70, "loading_dock": 24, "office": 30}
    for site in ("DC1", "DC2", "DC3"):
        for area in ("warehouse", "loading_dock", "office"):
            for day in range(14):
                for hour in range(24):
                    load = shape[hour]
                    devices = area_base[area] * load * wr.uniform(0.93, 1.07)
                    util = 22 + 38 * load * wr.uniform(0.92, 1.08)
                    latency = 14 + 6 * load * wr.uniform(0.9, 1.1)
                    mbps = 190 - 40 * load * wr.uniform(0.9, 1.1)
                    loss = 0.25 + 0.25 * load * wr.uniform(0.8, 1.2)
                    if site == "DC1" and area == "warehouse" and hour in (14, 15):
                        devices *= 1.75 * wr.uniform(0.97, 1.03)
                        util = 84 * wr.uniform(0.97, 1.03)
                        latency = 46 * wr.uniform(0.93, 1.07)
                        mbps = 95 * wr.uniform(0.93, 1.07)
                        loss = 1.5 * wr.uniform(0.85, 1.15)
                    elif site == "DC1" and area == "warehouse" and hour in (13, 16):
                        devices *= 1.25
                        util = 62 * wr.uniform(0.97, 1.03)
                        latency = 26 * wr.uniform(0.95, 1.05)
                        mbps = 150 * wr.uniform(0.95, 1.05)
                    n_wifi += 1
                    wifi_load.append({
                        "measurement_id": f"WIF-{n_wifi:06d}",
                        "site_id": site, "area": area, "hour_of_day": hour,
                        "date_measured": g.days_ago(day).isoformat(),
                        "device_count": int(round(devices)),
                        "throughput_mbps": round(mbps, 1),
                        "latency_ms": round(latency, 1),
                        "signal_strength_dbm": round(wr.uniform(-62, -48), 0),
                        "channel_utilisation_pct": round(min(util, 97), 1),
                        "packet_loss_pct": round(loss, 2),
                    })

    # Generate WMS system performance
    wms_perf = []
    for site in g.pick(sites_list, k=4):
        for day_offset in range(30, 0, -1):
            measure_date = g.days_ago(day_offset)
            wms_perf.append({
                "perf_id": f"WMS-{g.rng.randint(900000, 999999)}",
                "site_id": site["site_id"],
                "measurement_date": measure_date,
                "avg_response_time_ms": g.rng.uniform(50, 500),
                "p95_response_time_ms": g.rng.uniform(200, 1000),
                "p99_response_time_ms": g.rng.uniform(500, 2000),
                "error_count": g.rng.randint(0, 50),
                "incident_count": g.rng.randint(0, 5),
                "throughput_orders_per_hour": g.rng.uniform(100, 1000),
                "status": g.rng.choice(["healthy", "degraded", "critical"]) if g.rng.random() < 0.1 else "healthy",
            })

    # Generate asset CMDB - use real assets from master
    asset_cmdb = []
    master_assets = g.master("assets")
    asset_sample = g.pick(master_assets, k=min(20, len(master_assets)))
    for i, asset in enumerate(asset_sample):
        asset_cmdb.append({
            "asset_entry_id": f"CMB-{900000 + i:06d}",
            "asset_id": asset["asset_id"],
            "asset_name": asset["name"],
            "asset_type": asset["asset_class"],
            "business_service": g.rng.choice(systems),
            "criticality": asset.get("criticality", "medium"),
            "owner_team": g.rng.choice(["WMS Team", "Platform Team", "Integration Team", "DevOps"]),
            "rto_minutes": g.rng.choice([15, 30, 60, 120, 240]),
            "rpo_minutes": g.rng.choice([5, 15, 30, 60]),
        })

    # Generate system dependencies
    system_deps = []
    dep_pairs = [
        ("WMS", "Database", "database"),
        ("WMS", "ERP", "API"),
        ("Website", "WMS", "API"),
        ("POS", "Payment Gateway", "API"),
        ("Order API", "WMS", "message queue"),
        ("Stock Feed", "Website", "file transfer"),
    ]
    for i, (source, target, dep_type) in enumerate(dep_pairs):
        system_deps.append({
            "dependency_id": f"DEP-{900000 + i:06d}",
            "source_system": source,
            "target_system": target,
            "dependency_type": dep_type,
            "criticality": g.rng.choice(["critical", "high", "medium"]),
            "rto_minutes": g.rng.choice([15, 30, 60, 120]),
            "rpo_minutes": g.rng.choice([5, 15, 30]),
            "recovery_tier": g.rng.randint(1, 3),
        })

    # Generate backup and recovery
    backup_recovery = []
    system_names = ["WMS Database", "ERP Database", "Website Database", "Order API", "Cache Cluster", "Message Queue"]
    for i, sys_name in enumerate(system_names):
        restore_tested = g.rng.random() > 0.2
        backup_recovery.append({
            "system_name": sys_name,
            "system_type": g.rng.choice(["database", "application", "file storage"]),
            "rto_minutes": g.rng.choice([15, 30, 60, 120, 240]),
            "rpo_minutes": g.rng.choice([5, 15, 30, 60]),
            "last_backup_date": g.days_ago(g.rng.randint(0, 7)),
            "last_backup_size_gb": g.rng.uniform(50, 1000),
            "last_restore_test_date": g.days_ago(g.rng.randint(0, 90)) if restore_tested else None,
            "last_restore_test_duration_minutes": g.rng.randint(30, 240) if restore_tested else None,
            "backup_status": g.rng.choice(["healthy", "at_risk", "failed"]) if g.rng.random() < 0.05 else "healthy",
            "restore_tested": restore_tested,
        })

    # Generate vendor software
    vendor_software = []
    vendors_software = [
        ("WMS System", "Blue Yonder", "9.2", "9.3", "3"),
        ("ERP System", "SAP", "4.7", "4.8", "2"),
        ("Database", "Oracle", "21c", "23c", "1"),
        ("Message Queue", "Apache Kafka", "3.5", "3.6", "0"),
        ("API Gateway", "Kong", "3.1", "3.2", "1"),
        ("Cache", "Redis", "7.0", "7.1", "0"),
    ]
    for i, (sw_name, vendor, version, latest_ver, issues) in enumerate(vendors_software):
        support_end = g.days_ago(g.rng.randint(-365, 0))
        vendor_software.append({
            "software_id": f"VSW-{900000 + i:06d}",
            "software_name": sw_name,
            "vendor_name": vendor,
            "installed_version": version,
            "system_or_location": g.rng.choice(["DC1", "DC2", "DC3", "HQ", "All"]),
            "installation_date": g.days_ago(g.rng.randint(365, 1095)),
            "support_end_date": support_end,
            "latest_available_version": latest_ver,
            "security_issues": int(issues),
            "criticality": "critical" if int(issues) > 2 else g.rng.choice(["high", "medium", "low"]),
        })

    # Model alert rules are hand-written in seed/model_alert_rules.csv
    model_alert_rules = []

    # Background pipeline steps for the pipelines without a story (stock_feed is in seed/data_pipeline.csv)
    data_pipeline = []
    pipelines = [
        ("demand_forecast", [("extract", 120, "Pulls weekly sales and stock history"), ("clean", 240, "Removes returns and outliers"),
                             ("feature_engineer", 450, "Builds lag and promo features"), ("train", 890, "Fits the forecast model"),
                             ("validate", 180, "Backtests against the last 8 weeks")]),
        ("sales_analytics", [("extract", 95, "Reads POS sales lines"), ("aggregate", 210, "Rolls up to store-week"),
                             ("calculate", 160, "Computes KPIs"), ("load", 70, "Writes to the warehouse")]),
    ]
    n_pip = 100000
    for pipeline_name, steps in pipelines:
        for order, (step, base, note) in enumerate(steps):
            n_pip += 1
            avg = round(base * g.rng.uniform(0.96, 1.05), 1)
            data_pipeline.append({
                "pipeline_step_id": f"PIP-{n_pip:06d}",
                "pipeline_name": pipeline_name,
                "step_name": step,
                "step_order": order + 1,
                "avg_duration_seconds": avg,
                "baseline_avg_seconds": float(base),
                "max_duration_seconds": round(avg * 1.6, 1),
                "min_duration_seconds": round(avg * 0.7, 1),
                "rows_processed": g.rng.randint(400000, 1500000),
                "last_run_date": g.days_ago(g.rng.randint(0, 1)).isoformat(),
                "success_rate_pct": round(g.rng.uniform(98, 99.9), 1),
                "notes": note,
            })

    # Background releases on other systems (story releases are in seed/releases_and_changes.csv)
    done = [c for c in change_requests if c["status"] == "implemented"]
    releases = []
    for i, c in enumerate(done[:8]):
        impl = str(c["implemented_at"])[:10]
        releases.append({
            "release_id": f"REL-{5000 + i:06d}",
            "release_name": c["title"],
            "system_affected": c["system_affected"],
            "release_date": impl,
            "change_description": c["description"],
            "change_request_ids": c["change_id"],
            "deployed_to": "production",
            "rollback_available": True,
            "status": "deployed",
        })

    return {
        "incident_tickets": incident_tickets,
        "change_requests": change_requests,
        "fault_tickets": fault_tickets,
        "site_errors": site_errors,
        "security_remediation_tasks": security_tasks,
        "load_test_runs": load_test_runs,
        "system_interfaces": system_interfaces,
        "interface_peak_load": interface_peak_load,
        "wifi_network_load": wifi_load,
        "wms_system_performance": wms_perf,
        "asset_cmdb": asset_cmdb,
        "system_dependencies": system_deps,
        "backup_and_recovery": backup_recovery,
        "vendor_software": vendor_software,
        "model_alert_rules": model_alert_rules,
        "data_pipeline": data_pipeline,
        "releases_and_changes": releases,
    }
