"""Background (noise) data for the risk system. Story rows live in seed/*.csv with RSK-9xxxxx style ids.

Noise is deliberately small, low-exposure and master-consistent: suppliers are matched to the country of the
event or alert, SKUs and styles come from master products, owners are real employees.
"""


def generate(g):
    rng = g.rng
    suppliers = [s for s in g.master("suppliers") if s["status"] == "active"]
    by_country = {}
    for s in suppliers:
        by_country.setdefault(s["country"], []).append(s)
    products = g.master("products")
    owners = [f"EMP-{i:05d}" for i in range(2, 10)]
    dcs = ["DC1", "DC2", "DC3", "DC4", "DC5"]

    def sup(country):
        return rng.choice(by_country[country])

    # ---- risk register: small background risks, mostly closed or low exposure ----
    register = []
    templates = [
        ("operational", "Stock count variances at {site} above tolerance after the autumn cycle count", "site"),
        ("operational", "Dock appointment overruns at {site} during inbound peaks", "site"),
        ("supply_chain", "Late deliveries from {name} ({sid}) on autumn replenishment orders", "sup"),
        ("supply_chain", "Quality rework cost at {name} ({sid}) above agreed tolerance", "sup"),
        ("financial", "Supplier price increase requests from {name} ({sid}) not yet negotiated", "sup"),
        ("financial", "Customs duty classification queries on recent imports", None),
        ("operational", "Forklift fleet ageing at {site}; higher breakdown rate", "site"),
        ("technology", "Legacy EDI link to {name} ({sid}) unsupported by the vendor", "sup"),
        ("regulatory", "Updated product labelling rules for small electricals", None),
        ("demand", "Returns rate on online dresses above forecast", None),
        ("supply_chain", "Single haulier for DC4 Venlo inbound during January", None),
        ("operational", "Pick accuracy dip at {site} after temporary staff intake", "site"),
        ("financial", "Late payment interest on disputed supplier invoices", None),
        ("regulatory", "Data retention rules for supplier audit evidence", None),
        ("climate", "Heat-related productivity loss at {site} next summer", "site"),
        ("operational", "Security tagging gaps on high-value electricals at {site}", "site"),
    ]
    statuses = ["active"] * 7 + ["mitigated"] * 3 + ["closed"] * 4 + ["archived"] * 2
    rng.shuffle(statuses)
    for i, (cat, tpl, kind) in enumerate(templates):
        s = rng.choice(suppliers)
        site = rng.choice(dcs)
        status = statuses[i]
        created = rng.randint(70, 420)
        row = {
            "risk_id": f"RSK-{i + 1:06d}",
            "risk_category": cat,
            "description": tpl.format(site=site, name=s["name"], sid=s["supplier_id"]),
            "owner_id": rng.choice(owners),
            "likelihood_pct": rng.randint(10, 35),
            "impact_gbp": float(rng.randint(20, 180) * 1000),
            "horizon_months": rng.choice([3, 6, 9, 12, 18, 24]),
            "affected_supplier_id": s["supplier_id"] if kind == "sup" else None,
            "affected_site_id": site if kind == "site" else None,
            "mitigation_plan": rng.choice(["Monitor monthly; no action needed beyond routine controls",
                                           "Agreed corrective action plan with owner",
                                           "Covered by existing insurance and contract terms"]),
            "status": status,
            "assumptions": "Business as usual conditions",
            "created_at": g.days_ago(created),
            "updated_at": g.days_ago(rng.randint(5, min(created, 60))),
            "archived_at": g.days_ago(rng.randint(5, 50)) if status == "archived" else None,
        }
        register.append(row)

    # ---- alert rules: non-story monitoring rules (old, inactive or outside the Asia story) ----
    alerts = []
    alert_defs = [
        ("country_risk", "TR", "info", "Turkey lira volatility and wage unrest", "Monitor Turkish lira swings and factory wage disputes", "Review pricing and payment terms with Turkish suppliers", 12),
        ("country_risk", "PT", "info", "Portugal national transport strike notice", "Strike notice by haulage unions affecting Leixoes port", "Check inbound ETAs for Portuguese POs", 20),
        ("country_risk", "MX", "info", "Mexico border crossing delays", "Border inspection delays on road freight to the US", "Reroute urgent loads", 30),
        ("country_risk", "CN", "info", "China port congestion at Shanghai (cleared)", "Congestion at Shanghai during golden week; since cleared", "Resume normal booking cadence", 120),
        ("country_risk", "IN", "info", "India monsoon delays at Nhava Sheva (seasonal, cleared)", "Seasonal rain delays at Nhava Sheva", "Resume normal booking cadence", 160),
        ("weather", "BD,VN", "warning", "Extreme weather in sourcing regions (superseded)", "General weather watch replaced by country-specific rules", "None", 210),
        ("supplier_risk", None, "warning", "Critical supplier financial warning", "Monitor credit rating of suppliers rated high or critical", "Prepare dual sourcing", 9),
        ("port_risk", None, "info", "Port congestion watch - UK ports", "Track dwell time at Felixstowe and Southampton", "Check inbound status", 14),
        ("financial", None, "info", "Exchange rate volatility threshold", "GBP/USD moves over 2% in a week", "Review hedge cover", 6),
        ("regulatory", None, "info", "Regulatory change watch", "New UK and EU product compliance notices", "Notify compliance team", 40),
        ("other", None, "info", "Supplier quality failure threshold", "Defect rate above 2% on inbound QC", "Notify quality team", 25),
    ]
    for i, (ttype, country, sev, name, desc, action, days) in enumerate(alert_defs):
        alerts.append({
            "rule_id": f"ARU-{i + 1:06d}",
            "rule_name": name,
            "trigger_type": ttype,
            "trigger_country": country,
            "trigger_supplier_id": rng.choice(suppliers)["supplier_id"] if ttype == "supplier_risk" else None,
            "severity_level": sev,
            "description": desc,
            "action_required": action,
            "active": not name.endswith("(superseded)"),
            "created_at": g.days_ago(days + rng.randint(30, 150)),
            "last_triggered_at": g.days_ago(days),
        })

    # ---- risk events: noisy, low-severity or already resolved ----
    events = []
    event_defs = [
        ("port_disruption", "UK", "Southampton", "Post-strike normalisation at UK ports; dwell times back near normal", "low", None, "Southampton", None, "resolved", 24),
        ("weather", "Philippines", None, "Tropical storm forms east of the Philippines; track away from our sourcing ports", "low", None, None, None, "monitoring", 9),
        ("financial", "Global", None, "Oil price swings of 3% this week; no change to freight surcharges yet", "low", None, None, None, "monitoring", 11),
        ("cyber", "UK", None, "Phishing campaign against logistics firms; no incident at our suppliers", "low", None, None, None, "monitoring", 12),
        ("regulatory", "EU", None, "Consultation on packaging labels; no deadline set", "low", None, None, None, "monitoring", 15),
        ("supplier_issue", "Turkey", "Mersin", "Short factory holiday at a Turkish supplier; orders unaffected", "low", "TR", "Mersin", None, "resolved", 21),
        ("geopolitical", "India", "Nhava Sheva", "Election-related road blockades in Gujarat lifted after two days", "low", "IN", "Nhava Sheva", None, "resolved", 33),
        ("weather", "China", "Shanghai", "Typhoon passes south of Shanghai; port closed for one day", "medium", "CN", "Shanghai", None, "resolved", 40),
        ("port_disruption", "Netherlands", "Rotterdam", "Strike at Rotterdam terminal ended after 48 hours", "medium", None, "Rotterdam", None, "resolved", 45),
        ("supplier_issue", "Portugal", "Leixoes", "Fire drill at Portuguese supplier site; no production lost", "low", "PT", "Leixoes", None, "resolved", 52),
    ]
    for i, (etype, loc, port, desc, sev, country, ports, lanes, status, days) in enumerate(event_defs):
        supplier_ids = None
        if country:
            supplier_ids = ",".join(sorted({sup(country)["supplier_id"] for _ in range(rng.randint(1, 2))}))
        events.append({
            "event_id": f"RVT-{i + 1:06d}",
            "event_type": etype,
            "location": loc,
            "description": desc,
            "severity": sev,
            "affected_suppliers": supplier_ids,
            "affected_ports": ports,
            "affected_lanes": lanes,
            "time_to_impact_days": rng.randint(20, 60) if status != "resolved" else 0,
            "revenue_at_risk_gbp": float(rng.randint(5, 35) * 1000) if status != "resolved" else float(rng.randint(10, 60) * 1000),
            "status": status,
            "first_detected_at": g.days_ago(days),
            "impact_felt_at": g.days_ago(days - 1) if status == "resolved" and sev == "medium" else None,
        })

    # ---- older disruption incidents with their assumptions ----
    incidents, assumptions = [], []
    old = [
        ("Sourcing office power cut in Hong Kong", "Two-day power failure at the Hong Kong sourcing office delayed PO confirmations",
         "Utility substation fault", 330, 3, 22000.0, 4000.0, "Backup power for the sourcing office"),
        ("UK haulier IT outage", "Haulier booking system outage delayed inbound collections at DC1 for four days",
         "Third-party system failure", 280, 4, 41000.0, 9000.0, "Manual booking fallback agreed with hauliers"),
    ]
    for i, (name, desc, cause, ago, dur, rev, cost, lesson) in enumerate(old):
        iid = f"DIS-{i + 1:06d}"
        started = g.days_ago(ago)
        incidents.append({
            "incident_id": iid, "incident_name": name, "description": desc, "root_cause": cause,
            "started_at": started, "ended_at": g.days_ago(ago - dur), "duration_days": dur,
            "revenue_impact_gbp": rev, "cost_impact_gbp": cost, "affected_suppliers": None, "affected_skus": None,
            "lessons_learned": lesson, "assumptions_wrong": "Assumed the fallback process was tested; it was not",
            "status": "closed",
        })
        assumptions.append({
            "incident_id": iid, "assumption_id": 1, "assumption_text": "Fallback process restores service within one day",
            "expected_value": "1 day", "actual_value": f"{dur} days", "expected_num": 1.0, "actual_num": float(dur),
            "unit": "days", "impact_of_error": "Orders waited for manual handling", "recorded_at": g.days_ago(ago - dur - 7),
        })

    # ---- guidance risks: resolved or mitigated background ----
    guidance = [
        {"guidance_risk_id": "GRK-000001", "risk_description": "Delayed autumn range launch resolved after supplier caught up",
         "guidance_range_gbp": "2026-Q3 revenue", "likelihood_pct": 10, "impact_gbp": 150000.0, "mitigation": "Range landed on time",
         "mitigable_this_quarter": True, "trigger_point": "Launch slips beyond week 36", "status": "resolved", "created_at": g.days_ago(140)},
        {"guidance_risk_id": "GRK-000002", "risk_description": "Card payment fee increase absorbed in budget",
         "guidance_range_gbp": "2026-Q4 EBITDA 5.28-6.24m", "likelihood_pct": 20, "impact_gbp": 90000.0, "mitigation": "Fee negotiated down; within budget",
         "mitigable_this_quarter": True, "trigger_point": "Fee increase above 5bps", "status": "mitigated", "created_at": g.days_ago(95)},
    ]

    # ---- single points of failure: small style-level background ----
    rev = {}
    for s in g.master("sales_weekly"):
        rev[s["sku"]] = rev.get(s["sku"], 0.0) + float(s["revenue_gbp"])
    style_rev, style_sup = {}, {}
    for p in products:
        style_rev[p["style_id"]] = style_rev.get(p["style_id"], 0.0) + rev.get(p["sku"], 0.0)
        style_sup[p["style_id"]] = p["supplier_id"]
    story_styles = {"STY-8766", "STY-5520"}
    cands = sorted(st for st, v in style_rev.items() if 40000 <= v <= 250000 and st not in story_styles and not st.startswith("STY-PF") and not st.startswith("STY-K"))
    spofs = []
    opts = [("Qualify a second factory for the style", 35000.0), ("Hold 4 weeks buffer stock", 22000.0),
            ("Agree capacity reservation clause", 12000.0), ("Dual source 30% of volume", 28000.0)]
    for i, st in enumerate(rng.sample(cands, 8)):
        opt = rng.choice(opts)
        spofs.append({
            "spof_id": f"SPF-{i + 1:06d}", "failure_type": "supplier",
            "description": f"Style {st} made only by {style_sup[st]}; no approved alternative",
            "critical_skus": st, "affected_supplier_id": style_sup[st], "affected_site_id": None, "affected_route": None,
            "revenue_dependent_gbp": round(style_rev[st], -3),
            "mitigation_options": opt[0], "option_cost_gbp": opt[1],
            "priority": rng.choice(["low", "low", "medium"]),
            "status": rng.choice(["identified", "planning", "mitigated"]),
            "created_at": g.days_ago(rng.randint(40, 300)),
        })

    # ---- opportunities: small or already closed ----
    opps = [
        ("Reuse returned cartons in DC3", "Reuse returns cartons for outbound online parcels", "cost_saving", 45000.0, 60, "realized", 200),
        ("Pilot store-to-door delivery", "Pilot same-day delivery from 10 stores", "revenue_growth", 120000.0, 20, "cancelled", 150),
        ("LED lighting at DC4", "Replace lighting at Venlo DC", "cost_saving", 60000.0, 70, "realized", 260),
    ]
    opportunities = []
    for i, (name, desc, cat, benefit, prob, status, ago) in enumerate(opps):
        opportunities.append({
            "opportunity_id": f"OPP-{i + 1:06d}", "opportunity_name": name, "description": desc, "category": cat,
            "potential_benefit_gbp": benefit, "probability_pct": prob, "expected_value_gbp": round(benefit * prob / 100.0),
            "owner_id": rng.choice(owners), "status": status, "created_at": g.days_ago(ago),
        })

    # ---- a few mitigation options for background risks ----
    mitigations = []
    active_noise = [r for r in register if r["status"] == "active"][:4]
    for i, r in enumerate(active_noise):
        mitigations.append({
            "mitigation_id": f"MIT-{i + 1:06d}", "related_risk_id": r["risk_id"],
            "option_name": "Routine control improvement", "option_description": "Tighten monthly checks and review with the owner",
            "cost_gbp": float(rng.randint(3, 15) * 1000), "residual_risk_pct": rng.choice([40, 50, 60]),
            "implementation_weeks": rng.randint(2, 8), "effectiveness": rng.choice(["low", "medium"]), "owner_id": r["owner_id"],
        })

    return {
        "risk_register": register,
        "risk_alert_rules": alerts,
        "risk_events": events,
        "risk_briefings": [],
        "risk_scenarios": [],
        "disruption_incidents": incidents,
        "risk_assumptions": assumptions,
        "guidance_risks": guidance,
        "single_points_of_failure": spofs,
        "cutover_risks": [],
        "risk_opportunities": opportunities,
        "risk_mitigation_options": mitigations,
    }
