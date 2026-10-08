"""Background security data: alert history, scanner noise, auth logs, sessions and user accounts.

Story rows (this week's alerts, the supplier-account incident, the third-party connections, the unpatched
warehouse systems and the false-positive history) live in seed/*.csv. This file only adds believable background.
"""
from datetime import datetime, timedelta

CITY_BY_COUNTRY = {"CN": "Shanghai", "VN": "Ho Chi Minh City", "TR": "Istanbul", "IN": "Chennai", "PT": "Porto"}

# Same CVE -> same title/score everywhere (scan findings, unpatched systems).
LOW_CVES = [
    ("CVE-2024-4410", "Weak TLS cipher suites enabled", 5.9),
    ("CVE-2024-4421", "Cross-site scripting in admin console", 6.1),
    ("CVE-2024-4437", "Directory listing exposed on management UI", 5.3),
    ("CVE-2024-4452", "Denial of service in embedded web server", 6.5),
]


def _at(day, hour, minute=0):
    return datetime.combine(day, datetime.min.time()) + timedelta(hours=hour, minutes=minute)


def generate(g):
    r = g.rng
    sites = {s["site_id"]: s for s in g.master("sites")}
    employees = [e for e in g.master("employees") if e["status"] == "active"]
    suppliers = g.master("suppliers")
    assets = g.master("assets")

    # Staff pool: DC logistics staff plus technology staff (story users EMP-00109, EMP-00112, EMP-00115 included).
    pool = []
    for site, n in (("DC1", 12), ("DC2", 6), ("DC3", 4), ("HQ1", 4)):
        want = [e for e in employees if e["site_id"] == site and (site != "HQ1" or e["department"] == "Technology")]
        pool += want[:n]
    for must in ("EMP-00109", "EMP-00112", "EMP-00115"):
        if must not in {e["employee_id"] for e in pool}:
            pool += [e for e in employees if e["employee_id"] == must]

    def uname(e):
        return e["name"].lower().replace("dr ", "").replace("ms ", "").replace(" ", ".")

    # ---- alert history (closed) plus a few low-severity open alerts this week ---------------------
    alert_types = [("failed_login_spike", "siem"), ("suspicious_data_access", "siem"),
                   ("privilege_escalation", "endpoint"), ("malware_detected", "endpoint"),
                   ("data_exfiltration", "network"), ("unusual_port_activity", "network")]
    dc_assets = [a for a in assets if a["site_id"] in ("DC1", "DC2", "DC3") and ("-MHE-" in a["asset_id"] or "-CMP" in a["asset_id"])]
    alerts = []
    for i in range(18):
        t, src = r.choice(alert_types)
        raised = _at(g.days_ago(r.randint(9, 70)), r.randint(0, 23), r.randint(0, 59))
        status = r.choices(["resolved", "false_positive"], [4, 6])[0]
        closed = raised + timedelta(hours=r.randint(1, 36))
        alerts.append({
            "alert_id": f"ALT-{len(alerts) + 1:06d}", "source_system": src, "alert_type": t,
            "severity": r.choices(["low", "medium", "high"], [45, 40, 15])[0],
            "asset_id": r.choice(dc_assets)["asset_id"] if r.random() < 0.6 else None,
            "user_id": r.choice(pool)["employee_id"] if r.random() < 0.6 else None,
            "raised_at": raised, "description": f"{t.replace('_', ' ').capitalize()} reported by {src}",
            "status": status, "closed_at": closed,
            "disposition_reason": "Expected activity, no action needed" if status == "false_positive" else "Reviewed and remediated",
            "updated_at": closed})
    for i in range(3):  # low-severity open noise this week
        t, src = r.choice(alert_types[:2] + alert_types[5:])
        raised = _at(g.days_ago(r.randint(1, 5)), r.randint(6, 20), r.randint(0, 59))
        alerts.append({
            "alert_id": f"ALT-{len(alerts) + 1:06d}", "source_system": src, "alert_type": t, "severity": "low",
            "asset_id": None, "user_id": r.choice(pool)["employee_id"], "raised_at": raised,
            "description": f"{t.replace('_', ' ').capitalize()} reported by {src} (low confidence)",
            "status": "open", "closed_at": None, "disposition_reason": None, "updated_at": raised})

    # ---- scan findings: medium-score background on non-critical equipment -------------------------
    findings = []
    for i in range(10):
        a = r.choice(dc_assets)
        cve, title, cvss = r.choice(LOW_CVES)
        disc = g.days_ago(r.randint(5, 80))
        patch_since = disc - timedelta(days=r.randint(3, 20))
        status = r.choice(["unpatched", "patch_available", "patch_available", "patched"])
        findings.append({
            "finding_id": f"VUL-{len(findings) + 1:06d}", "asset_id": a["asset_id"], "site_id": a["site_id"],
            "cve_id": cve, "vulnerability_title": title, "cvss_score": cvss,
            "cvss_vector": "CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:L/I:L/A:N",
            "is_externally_exposed": False, "is_exploited_in_wild": False, "is_patched": status == "patched",
            "patch_available_since": patch_since, "affected_software": "Embedded firmware",
            "current_version": "3.2", "patched_version": "3.4", "discovered_date": disc,
            "last_scanned": g.days_ago(r.randint(0, 3)), "remediation_status": status,
            "updated_at": _at(g.as_of, 6)})

    # ---- accounts ---------------------------------------------------------------------------------
    accounts = []
    last_login = {}
    sup_users = []
    for i, s in enumerate(suppliers[:4]):
        sup_users.append((f"SUPP-{i + 1:05d}", f"supplier-user-{i + 1}", s))

    # ---- auth logs and sessions: employees ---------------------------------------------------------
    emp_systems = ["wms", "edi_portal", "financial_system", "payroll_system"]
    records = {"wms": "stock;orders", "edi_portal": "po_lines;shipments",
               "financial_system": "budget_data;reports", "payroll_system": "payroll_summary"}
    logs, sessions = [], []

    def add_login(uid, username, ip, loc, method, system, ts, ok=True, reason=None, utype="employee",
                  actions=None, viewed=None, minutes=None, suspicious=False):
        sid = None
        if ok:
            sid = f"SES-{len(sessions) + 1:06d}"
            end = ts + timedelta(minutes=minutes or r.randint(10, 120))
            sessions.append({
                "session_id": sid, "user_id": uid, "username": username, "user_type": utype,
                "started_at": ts, "ended_at": end, "source_ip": ip, "source_location": loc,
                "system_accessed": system, "actions_count": actions or r.randint(3, 40),
                "data_accessed_systems": system, "data_viewed_records": viewed or records.get(system, "reports"),
                "is_suspicious": suspicious, "block_reason": None})
            last_login[uid] = max(last_login.get(uid, ts), ts)
        logs.append({
            "log_id": f"LOG-{len(logs) + 1:06d}", "timestamp": ts, "user_id": uid, "username": username,
            "source_ip": ip, "source_location": loc, "authentication_method": method,
            "result": "success" if ok else "failed", "reason": reason, "system_accessed": system,
            "session_id": sid, "updated_at": ts})

    ips = {}
    for e in pool:
        ips[e["employee_id"]] = f"203.0.113.{r.randint(10, 250)}"
    for i in range(45):
        e = r.choice(pool)
        day = g.days_ago(r.randint(0, 13))
        if day.weekday() >= 5:
            continue
        ts = _at(day, r.randint(6, 17), r.randint(0, 59))
        loc = sites[e["site_id"]]["city"]
        ok = r.random() > 0.08
        add_login(e["employee_id"], uname(e), ips[e["employee_id"]], loc, r.choice(["sso", "mfa", "mfa"]),
                  r.choice(emp_systems), ts, ok, None if ok else "Invalid password")

    # ---- supplier users: ordinary daytime logins from their own country ----------------------------
    for uid, uname_, s in sup_users:
        city = CITY_BY_COUNTRY.get(s["country"], "Shanghai")
        ip = f"198.51.100.{20 + int(uid[-2:])}"
        for back in (1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12):
            day = g.days_ago(back + 2)
            if day.weekday() >= 5:
                continue
            ts = _at(day, 8 + int(uid[-1]) % 3, r.randint(0, 50))
            add_login(uid, uname_, ip, city, "password", "edi_portal", ts, True, utype="supplier",
                      actions=r.randint(4, 15), viewed="po_lines;shipments", minutes=r.randint(10, 35))

    # ---- user accounts ------------------------------------------------------------------------------
    for e in pool:
        accounts.append({
            "user_id": e["employee_id"], "username": uname(e), "user_type": "employee", "supplier_id": None,
            "name": e["name"], "status": "active", "locked_at": None, "lock_reason": None,
            "is_privileged": e["department"] == "Technology", "mfa_enabled": r.random() > 0.1,
            "last_login": last_login.get(e["employee_id"]), "failed_login_count": r.randint(0, 2),
            "created_at": _at(g.days_ago(r.randint(200, 1500)), 9), "updated_at": _at(g.as_of, 6)})
    for uid, uname_, s in sup_users:
        accounts.append({
            "user_id": uid, "username": uname_, "user_type": "supplier", "supplier_id": s["supplier_id"],
            "name": f"{s['name']} portal user", "status": "active", "locked_at": None, "lock_reason": None,
            "is_privileged": False, "mfa_enabled": uid != "SUPP-00001", "last_login": last_login.get(uid),
            "failed_login_count": 0, "created_at": _at(g.days_ago(r.randint(200, 900)), 9),
            "updated_at": _at(g.as_of, 6)})

    # ---- unpatched systems: low-criticality background (all below the default CVSS 7.0 cut) ---------
    unpatched = []
    for sysid, name, site in (("SYS-LBL", "Label printing server", "DC3"), ("SYS-KIOSK", "Staff kiosk service", "DC2"),
                              ("SYS-BADGE", "Badge reader controller", "DC1"), ("SYS-DOCK", "Dock booking display", "DC1")):
        for cve, title, cvss in r.sample(LOW_CVES, 2):
            unpatched.append({
                "system_id": sysid, "system_name": name, "site_id": site, "cve_id": cve,
                "vulnerability_title": title, "cvss_score": cvss, "is_externally_exposed": False,
                "patch_available": True, "days_unpatched": r.randint(10, 120),
                "business_criticality": "low", "exploitability": "low"})

    return {
        "security_alerts": alerts,
        "vulnerability_scan_findings": findings,
        "alert_dispositions": [],       # seed/alert_dispositions.csv
        "auth_logs": logs,
        "user_sessions": sessions,
        "third_party_connections": [],  # seed: ids match integration's CON-9000xx connections
        "connection_controls": [],
        "connection_access_privileges": [],
        "unpatched_systems": unpatched,
        "security_incidents": [],
        "user_accounts": accounts,
    }
