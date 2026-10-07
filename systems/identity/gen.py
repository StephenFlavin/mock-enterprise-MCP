"""Background security data: alerts, vulnerabilities, auth logs, sessions, and third-party connections."""
from datetime import datetime, timedelta
import random


def generate(g):
    r = g.rng

    # Get some master data to reference
    suppliers = g.master("suppliers")[:10]
    assets = g.master("assets")[:15]
    employees = g.master("employees")[:20]
    sites = [s for s in g.master("sites") if s["type"] == "dc"][:5]

    alerts = []
    findings = []
    dispositions = []
    auth_logs = []
    sessions = []
    connections = []
    conn_controls = []
    conn_privileges = []
    unpatched = []
    incidents = []
    user_accounts = []

    # Alert type distribution (common types)
    alert_types = [
        ("failed_login_spike", "siem"),
        ("suspicious_data_access", "siem"),
        ("privilege_escalation", "endpoint"),
        ("malware_detected", "endpoint"),
        ("data_exfiltration", "network"),
        ("unusual_port_activity", "network"),
    ]

    # Generate security alerts (10-20 total)
    for i in range(r.randint(10, 20)):
        alert_type, source = r.choice(alert_types)
        severity_choices = ["low", "medium", "high", "critical"]
        severity = r.choices(severity_choices, [50, 35, 12, 3])[0]

        raised_at = g.fake.date_time_between_dates(
            datetime_start=datetime.combine(g.as_of, datetime.min.time()) - timedelta(days=7),
            datetime_end=datetime.combine(g.as_of, datetime.min.time())
        )

        asset = r.choice(assets) if r.random() > 0.3 else None
        user = r.choice(employees) if r.random() > 0.5 else None

        status_choices = ["open", "open", "open", "investigating", "resolved", "false_positive"]
        status = r.choice(status_choices)

        closed_at = None
        if status != "open":
            closed_at = raised_at + timedelta(hours=r.randint(1, 48))

        alerts.append({
            "alert_id": f"ALT-{len(alerts) + 1:06d}",
            "source_system": source,
            "alert_type": alert_type,
            "severity": severity,
            "asset_id": asset["asset_id"] if asset else None,
            "user_id": user["employee_id"] if user else None,
            "raised_at": raised_at,
            "description": f"Alert: {alert_type} from {source}",
            "status": status,
            "closed_at": closed_at,
            "disposition_reason": "False positive - routine activity" if status == "false_positive" else None,
            "updated_at": closed_at if closed_at else raised_at,
        })

    # Alert disposition history (for false positive rates)
    for alert_type, source in alert_types:
        false_pos = r.randint(10, 50)
        incidents = r.randint(5, 25)
        total = false_pos + incidents + r.randint(5, 20)

        dispositions.append({
            "disposition_id": f"DSP-{len(dispositions) + 1:06d}",
            "alert_type": alert_type,
            "source_system": source,
            "past_disposition": "false_positive",
            "count": false_pos,
            "percentage": round(100.0 * false_pos / total, 1),
            "last_occurrence_date": g.as_of - timedelta(days=r.randint(1, 60)),
        })

    # Generate vulnerability findings (15-30)
    cve_samples = [
        ("CVE-2024-1234", "Remote Code Execution in OpenSSH", 9.8, True, True),
        ("CVE-2024-5678", "SQL Injection in Database Driver", 8.7, True, False),
        ("CVE-2024-9012", "Privilege Escalation in Kernel", 8.1, False, False),
        ("CVE-2024-3456", "Buffer Overflow in Web Server", 7.5, True, False),
        ("CVE-2024-7890", "XXE in XML Parser", 7.2, False, False),
    ]

    for i in range(r.randint(15, 30)):
        cve, title, cvss, exposed, exploited = r.choice(cve_samples)

        asset = r.choice(assets)
        site = r.choice(sites)
        discovered = g.as_of - timedelta(days=r.randint(1, 90))
        patch_avail = discovered - timedelta(days=r.randint(5, 30)) if r.random() > 0.3 else None
        remediation = "unpatched" if patch_avail and r.random() > 0.7 else ("patch_available" if patch_avail else "unpatched")

        findings.append({
            "finding_id": f"VUL-{len(findings) + 1:06d}",
            "asset_id": asset["asset_id"],
            "site_id": site["site_id"],
            "cve_id": cve,
            "vulnerability_title": title,
            "cvss_score": cvss,
            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            "is_externally_exposed": exposed,
            "is_exploited_in_wild": exploited,
            "is_patched": remediation == "patched",
            "patch_available_since": patch_avail,
            "affected_software": "OpenSSH 7.4" if "OpenSSH" in title else "Database Driver 2.1",
            "current_version": "7.4p1",
            "patched_version": "8.0p1",
            "discovered_date": discovered,
            "last_scanned": g.as_of,
            "remediation_status": remediation,
            "updated_at": datetime.now(),
        })

    # Generate auth logs (50-100)
    systems = ["edi_portal", "vendor_portal", "payroll_system", "financial_system"]
    for i in range(r.randint(50, 100)):
        user = r.choice(employees)
        ts = g.fake.date_time_between_dates(
            datetime_start=datetime.combine(g.as_of, datetime.min.time()) - timedelta(days=7),
            datetime_end=datetime.combine(g.as_of, datetime.min.time())
        )

        result_choices = ["success", "success", "success", "failed", "mfa_required", "blocked"]
        result = r.choice(result_choices)

        auth_logs.append({
            "log_id": f"LOG-{len(auth_logs) + 1:06d}",
            "timestamp": ts,
            "user_id": user["employee_id"],
            "username": user["name"].lower().replace(" ", "."),
            "source_ip": f"203.0.113.{r.randint(1, 254)}",
            "source_location": r.choice(["London", "Manchester", "Birmingham", "Unknown"]),
            "authentication_method": r.choice(["password", "mfa", "sso"]),
            "result": result,
            "reason": "Invalid password" if result == "failed" else None,
            "system_accessed": r.choice(systems),
            "session_id": f"SES-{r.randint(100000, 999999)}",
            "updated_at": ts,
        })

    # Generate user sessions (20-40)
    for i in range(r.randint(20, 40)):
        user = r.choice(employees)
        start = g.fake.date_time_between_dates(
            datetime_start=datetime.combine(g.as_of, datetime.min.time()) - timedelta(days=7),
            datetime_end=datetime.combine(g.as_of, datetime.min.time())
        )
        duration_minutes = r.randint(5, 240)
        end = start + timedelta(minutes=duration_minutes)

        sessions.append({
            "session_id": f"SES-{len(sessions) + 1:06d}",
            "user_id": user["employee_id"],
            "username": user["name"].lower().replace(" ", "."),
            "user_type": "employee",
            "started_at": start,
            "ended_at": end,
            "source_ip": f"203.0.113.{r.randint(1, 254)}",
            "source_location": user.get("site_id", "London"),
            "system_accessed": r.choice(systems),
            "actions_count": r.randint(1, 50),
            "data_accessed_systems": "vendor_portal;edi_data",
            "data_viewed_records": "bank_details;po_lines",
            "is_suspicious": r.random() < 0.1,
            "block_reason": None,
        })

    # Generate third-party connections (8-12)
    for i, supplier in enumerate(suppliers[:r.randint(8, 12)]):
        connection_id = f"CON-{i + 1:06d}"

        connections.append({
            "connection_id": connection_id,
            "connection_name": supplier["name"],
            "connection_type": "supplier",
            "supplier_id": supplier["supplier_id"],
            "partner_id": None,
            "primary_purpose": "EDI and order management",
            "connection_established": g.as_of - timedelta(days=r.randint(30, 730)),
            "connection_status": r.choice(["active", "active", "active", "inactive"]),
            "risk_rating": r.choices(["low", "medium", "high", "critical"], [40, 35, 20, 5])[0],
            "data_scope": "po_lines;purchase_orders;shipments",
            "systems_accessed": "edi_portal;api_gateway",
            "privileged_access": r.random() < 0.2,
            "updated_at": datetime.now(),
        })

        # Add controls for this connection
        controls = [
            ("mfa", "Duo MFA", r.random() > 0.2),
            ("ip_allowlist", "IP restrict to 203.0.113.0/24", r.random() > 0.15),
            ("data_encryption", "TLS 1.3 for all connections", r.random() > 0.1),
            ("logging", "All API calls logged to SIEM", r.random() > 0.05),
        ]

        for ctrl_type, ctrl_name, enabled in controls:
            conn_controls.append({
                "connection_id": connection_id,
                "control_type": ctrl_type,
                "control_name": ctrl_name,
                "is_enabled": enabled,
                "enabled_date": g.as_of - timedelta(days=r.randint(30, 180)) if enabled else None,
                "audit_trail": enabled and r.random() > 0.3,
                "last_verified": g.as_of - timedelta(days=r.randint(1, 30)) if enabled else None,
                "effectiveness_rating": "high" if enabled else "low",
            })

        # Add access privileges
        systems = ["edi_portal", "api_gateway", "order_management"]
        for sys in r.sample(systems, r.randint(1, 2)):
            conn_privileges.append({
                "connection_id": connection_id,
                "system_id": sys,
                "privilege_level": r.choices(["read_only", "read_write", "admin"], [70, 25, 5])[0],
                "data_scope": "po_lines;shipments" if sys == "edi_portal" else "all",
                "scope_description": f"Access to {sys} for order management",
                "access_granted_date": g.as_of - timedelta(days=r.randint(30, 365)),
                "access_reviewed_date": g.as_of - timedelta(days=r.randint(1, 90)),
                "requires_approval_for": "data_export;payment_change",
                "audit_events_enabled": r.random() > 0.1,
            })

    # Generate unpatched systems (list of critical issues)
    for asset in assets[:r.randint(8, 12)]:
        site = r.choice(sites)

        for cve, title, cvss, exposed, exploited in r.sample(cve_samples, r.randint(1, 3)):
            unpatched.append({
                "system_id": asset["asset_id"],
                "system_name": asset["name"],
                "site_id": site["site_id"],
                "cve_id": cve,
                "vulnerability_title": title,
                "cvss_score": cvss,
                "is_externally_exposed": exposed,
                "patch_available": r.random() > 0.3,
                "days_unpatched": r.randint(5, 90),
                "business_criticality": asset.get("criticality", "medium"),
                "exploitability": r.choices(["low", "medium", "high"], [30, 40, 30])[0],
            })

    # Generate user accounts (20-30)
    for i, emp in enumerate(employees[:r.randint(20, min(30, len(employees)))]):
        user_accounts.append({
            "user_id": emp["employee_id"],
            "username": emp["name"].lower().replace(" ", "."),
            "user_type": "employee",
            "name": emp["name"],
            "status": r.choices(["active", "active", "active", "locked", "disabled"], [85, 10, 3, 2])[0],
            "locked_at": None,
            "lock_reason": None,
            "is_privileged": r.random() < 0.15,
            "mfa_enabled": r.random() > 0.2,
            "last_login": g.as_of - timedelta(days=r.randint(0, 7)),
            "failed_login_count": r.randint(0, 5),
            "created_at": datetime.now() - timedelta(days=r.randint(30, 730)),
            "updated_at": datetime.now(),
        })

    # Add some supplier user accounts
    for i, supplier in enumerate(suppliers[:r.randint(3, 5)]):
        user_accounts.append({
            "user_id": f"SUPP-{i + 1:05d}",
            "username": f"supplier{i+1}",
            "user_type": "supplier",
            "name": f"Supplier {supplier['name'][:20]} User",
            "status": r.choices(["active", "active", "locked"], [90, 5, 5])[0],
            "locked_at": None,
            "lock_reason": None,
            "is_privileged": False,
            "mfa_enabled": r.random() > 0.5,
            "last_login": g.as_of - timedelta(days=r.randint(0, 30)),
            "failed_login_count": r.randint(0, 3),
            "created_at": datetime.now() - timedelta(days=r.randint(30, 365)),
            "updated_at": datetime.now(),
        })

    return {
        "security_alerts": alerts,
        "vulnerability_scan_findings": findings,
        "alert_dispositions": dispositions,
        "auth_logs": auth_logs,
        "user_sessions": sessions,
        "third_party_connections": connections,
        "connection_controls": conn_controls,
        "connection_access_privileges": conn_privileges,
        "unpatched_systems": unpatched,
        "security_incidents": incidents,
        "user_accounts": user_accounts,
    }
