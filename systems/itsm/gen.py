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

    # Generate incident tickets
    incident_tickets = []
    for i in range(50):
        days_ago_raised = g.rng.randint(1, 60)
        raised = g.days_ago(days_ago_raised)
        days_ago_resolved = g.rng.randint(0, days_ago_raised - 1) if g.rng.random() > 0.3 else None
        resolved = g.days_ago(days_ago_resolved) if days_ago_resolved is not None else None
        incident_tickets.append({
            "incident_id": f"INC-{900000 + i:06d}",
            "title": g.fake.sentence(nb_words=5),
            "description": g.fake.sentence(nb_words=12),
            "status": "resolved" if resolved else g.rng.choice(["open", "investigating"]),
            "severity": g.rng.choice(["critical", "high", "medium", "low"]),
            "assigned_to": g.pick(g.master("employees"), k=1)[0]["employee_id"],
            "system_affected": g.rng.choice(systems),
            "raised_at": raised,
            "resolved_at": resolved,
            "updated_at": resolved or raised,
        })

    # Generate change requests
    change_requests = []
    for i in range(40):
        days_ago_created = g.rng.randint(1, 90)
        created = g.days_ago(days_ago_created)
        planned = g.days_ago(g.rng.randint(-30, days_ago_created - 1))

        submitted = None
        submitted_days = g.rng.randint(days_ago_created - 1, 0) if g.rng.random() > 0.2 else None
        if submitted_days is not None:
            submitted = g.days_ago(submitted_days)

        approved = None
        if submitted and g.rng.random() > 0.3:
            approved = g.days_ago(g.rng.randint(min(submitted_days - 1, 0), 0)) if submitted_days > 0 else g.days_ago(0)

        implemented = None
        if approved and g.rng.random() > 0.4:
            impl_days = g.rng.randint(0, max(0, submitted_days - 1)) if submitted_days and submitted_days > 0 else 0
            implemented = g.days_ago(impl_days)

        status = "implemented" if implemented else ("approved" if approved else ("submitted" if submitted else "draft"))
        change_requests.append({
            "change_id": f"CHG-{900000 + i:06d}",
            "title": f"{g.rng.choice(['Security patch', 'Feature release', 'Configuration change', 'Firmware update', 'Bug fix'])} for {g.rng.choice(systems)}",
            "description": g.fake.sentence(nb_words=12),
            "change_type": g.rng.choice(["patch", "firmware", "configuration", "migration"]),
            "status": status,
            "assigned_to": g.pick(g.master("employees"), k=1)[0]["employee_id"],
            "system_affected": g.rng.choice(systems),
            "planned_date": planned,
            "submitted_at": submitted,
            "approved_at": approved,
            "implemented_at": implemented,
            "created_at": created,
            "updated_at": implemented or approved or submitted or created,
        })

    # Generate fault tickets
    fault_tickets = []
    sites_list = g.master("sites")
    for i in range(30):
        site = g.pick(sites_list, k=1)[0]
        days_ago_raised = g.rng.randint(1, 30)
        raised = g.days_ago(days_ago_raised)
        days_ago_resolved = g.rng.randint(0, days_ago_raised - 1) if g.rng.random() > 0.4 else None
        resolved = g.days_ago(days_ago_resolved) if days_ago_resolved is not None else None
        fault_tickets.append({
            "fault_id": f"FLT-{900000 + i:06d}",
            "site_id": site["site_id"],
            "device_id": f"SCO-{site['site_id'][-3:]}-{g.rng.randint(1, 10):02d}",
            "fault_type": g.rng.choice(["scanning error", "payment failure", "display issue", "software crash"]),
            "description": g.fake.sentence(nb_words=10),
            "status": "repaired" if resolved else g.rng.choice(["open", "investigating"]),
            "severity": g.rng.choice(["high", "medium", "low"]),
            "raised_at": raised,
            "resolved_at": resolved,
            "updated_at": resolved or raised,
        })

    # Generate site errors
    site_errors = []
    for i in range(40):
        first_days_ago = g.rng.randint(1, 30)
        first_seen = g.days_ago(first_days_ago)
        last_days_ago = g.rng.randint(0, first_days_ago - 1)
        last_seen = g.days_ago(last_days_ago)
        site_errors.append({
            "error_id": f"ERR-{900000 + i:06d}",
            "site_id": g.rng.choice(sites),
            "error_type": g.rng.choice(error_types),
            "error_message": g.fake.sentence(nb_words=8),
            "error_count": g.rng.randint(5, 500),
            "first_seen": first_seen,
            "last_seen": last_seen,
            "status": g.rng.choice(["active", "investigating", "resolved"]),
            "resolution": g.fake.sentence(nb_words=6) if g.rng.random() > 0.5 else None,
            "created_at": first_seen,
            "updated_at": last_seen,
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

    # Generate load test runs
    load_test_runs = []
    for i in range(20):
        interface = g.rng.choice(interfaces)
        scheduled_days = g.rng.randint(-90, -5)
        scheduled = g.days_ago(-scheduled_days)

        started = None
        if g.rng.random() > 0.3:
            started_days = g.rng.randint(0, -scheduled_days - 1) if -scheduled_days > 1 else 0
            started = g.days_ago(started_days)

        completed = None
        if started:
            comp_days = g.rng.randint(0, -scheduled_days - 1) if -scheduled_days > 1 else 0
            completed = g.days_ago(comp_days)

        status = "passed" if completed and g.rng.random() > 0.2 else ("failed" if completed else ("in_progress" if started else "scheduled"))
        load_test_runs.append({
            "test_run_id": f"LTR-{900000 + i:06d}",
            "interface_name": interface["name"],
            "test_type": g.rng.choice(["peak load", "stress", "endurance", "spike"]),
            "target_message_rate": g.rng.randint(1000, 10000),
            "peak_achieved": g.rng.randint(800, 10000),
            "avg_latency_ms": g.rng.uniform(10, 500),
            "max_latency_ms": g.rng.uniform(500, 2000),
            "errors": g.rng.randint(0, 50) if status in ["failed", "in_progress"] else g.rng.randint(0, 5),
            "status": status,
            "scheduled_at": scheduled,
            "started_at": started,
            "completed_at": completed,
            "notes": g.fake.sentence(nb_words=8) if completed else None,
        })

    # Generate system interfaces
    system_interfaces = []
    for i, interface in enumerate(interfaces * 2):
        headroom = g.rng.randint(10, 80)
        system_interfaces.append({
            "interface_id": f"INT-{900000 + i:06d}",
            "interface_name": interface["name"],
            "source_system": interface["source"],
            "target_system": interface["target"],
            "message_type": interface["msg_type"],
            "current_throughput_msgs_per_sec": g.rng.uniform(500, 5000),
            "rated_capacity_msgs_per_sec": g.rng.randint(8000, 15000),
            "headroom_pct": headroom,
            "last_measured": g.days_ago(g.rng.randint(0, 7)),
            "status": "degraded" if headroom < 20 else ("failing" if headroom < 5 else "operational"),
        })

    # Generate WiFi network load
    wifi_load = []
    for site in g.pick(sites_list, k=3):
        for area in areas:
            for hour in [6, 9, 12, 15, 18, 21]:
                for day_offset in range(0, -14, -1):
                    measure_date = g.days_ago(-day_offset)
                    wifi_load.append({
                        "measurement_id": f"WIF-{g.rng.randint(900000, 999999)}",
                        "site_id": site["site_id"],
                        "area": area,
                        "hour_of_day": hour,
                        "date_measured": measure_date,
                        "device_count": g.rng.randint(10, 200) if area != "warehouse" else g.rng.randint(5, 50),
                        "throughput_mbps": g.rng.uniform(10, 500),
                        "latency_ms": g.rng.uniform(5, 100),
                        "signal_strength_dbm": g.rng.uniform(-80, -40),
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

    # Generate asset CMDB
    asset_cmdb = []
    asset_types = ["database", "application server", "API", "cache", "message queue"]
    for i in range(20):
        asset_cmdb.append({
            "asset_entry_id": f"AST-{900000 + i:06d}",
            "asset_id": f"AST-{g.rng.choice(['DB', 'APP', 'API', 'MQ', 'CSH'])}-{g.rng.randint(1, 20):03d}",
            "asset_name": f"{g.rng.choice(['Primary', 'Secondary', 'Cache', 'Queue', 'API'])} {g.rng.choice(['Server', 'Database', 'Service'])}",
            "asset_type": g.rng.choice(asset_types),
            "business_service": g.rng.choice(systems),
            "criticality": g.rng.choice(["critical", "high", "medium", "low"]),
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
        ("WMS System", "Blue Yonder", "9.2", "3"),
        ("ERP System", "SAP", "4.7", "2"),
        ("Database", "Oracle", "21c", "1"),
        ("Message Queue", "Apache Kafka", "3.5", "0"),
        ("API Gateway", "Kong", "3.1", "1"),
        ("Cache", "Redis", "7.0", "0"),
    ]
    for i, (sw_name, vendor, version, issues) in enumerate(vendors_software):
        support_end = g.days_ago(g.rng.randint(-365, 0))
        vendor_software.append({
            "software_id": f"VSW-{900000 + i:06d}",
            "software_name": sw_name,
            "vendor_name": vendor,
            "installed_version": version,
            "system_or_location": g.rng.choice(["DC1", "DC2", "DC3", "HQ", "All"]),
            "installation_date": g.days_ago(g.rng.randint(365, 1095)),
            "support_end_date": support_end,
            "latest_available_version": f"{int(version.split('.')[0])}.{int(version.split('.')[1]) + 1}",
            "security_issues": int(issues),
            "criticality": "critical" if int(issues) > 2 else g.rng.choice(["high", "medium", "low"]),
        })

    # Generate model alert rules
    model_alert_rules = []
    models = ["demand_forecast", "pricing_optimization", "layout_optimizer", "fraud_detection"]
    rule_types = ["drift", "accuracy", "retraining"]
    for i, model in enumerate(models):
        for rule_type in rule_types:
            triggered = g.days_ago(g.rng.randint(0, 30)) if g.rng.random() > 0.5 else None
            model_alert_rules.append({
                "rule_id": f"ALR-{900000 + i * 3 + rule_types.index(rule_type):06d}",
                "model_name": model,
                "rule_type": rule_type,
                "threshold_value": g.rng.uniform(0.05, 0.20) if rule_type == "drift" else g.rng.uniform(0.85, 0.95),
                "threshold_metric": "PSI" if rule_type == "drift" else "MAE" if rule_type == "accuracy" else "days",
                "enabled": g.rng.random() > 0.1,
                "created_at": g.days_ago(g.rng.randint(30, 180)),
                "last_triggered": triggered,
                "noise_level": g.rng.choice(["low", "medium", "high"]),
            })

    # Generate data pipeline steps
    data_pipeline = []
    pipelines = [
        ("demand_forecast", ["extract", "clean", "feature_engineer", "train", "validate"]),
        ("stock_feed", ["fetch", "transform", "validate", "publish"]),
        ("sales_analytics", ["extract", "aggregate", "calculate", "load"]),
    ]
    for pipeline_name, steps in pipelines:
        for order, step in enumerate(steps):
            data_pipeline.append({
                "pipeline_step_id": f"PIP-{g.rng.randint(900000, 999999)}",
                "pipeline_name": pipeline_name,
                "step_name": step,
                "step_order": order + 1,
                "avg_duration_seconds": g.rng.uniform(10, 600),
                "max_duration_seconds": g.rng.uniform(600, 1800),
                "min_duration_seconds": g.rng.uniform(5, 60),
                "rows_processed": g.rng.randint(10000, 1000000),
                "last_run_date": g.days_ago(g.rng.randint(0, 1)),
                "success_rate_pct": g.rng.uniform(95, 100),
            })

    # Generate releases and changes
    releases = []
    for i in range(15):
        release_date = g.date_between(g.days_ago(90), g.days_ago(0))
        releases.append({
            "release_id": f"REL-{900000 + i:06d}",
            "release_name": f"v{g.rng.randint(1, 10)}.{g.rng.randint(0, 9)}.{g.rng.randint(0, 30)}",
            "system_affected": g.rng.choice(systems),
            "release_date": release_date,
            "change_description": g.fake.sentence(nb_words=12),
            "change_request_ids": f"CHG-{g.rng.randint(900000, 999999)}, CHG-{g.rng.randint(900000, 999999)}",
            "deployed_to": g.rng.choice(["production", "staging"]),
            "rollback_available": g.rng.random() > 0.2,
            "status": g.rng.choice(["deployed", "planned", "rolled_back"]),
        })

    return {
        "incident_tickets": incident_tickets,
        "change_requests": change_requests,
        "fault_tickets": fault_tickets,
        "site_errors": site_errors,
        "security_remediation_tasks": security_tasks,
        "load_test_runs": load_test_runs,
        "system_interfaces": system_interfaces,
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
