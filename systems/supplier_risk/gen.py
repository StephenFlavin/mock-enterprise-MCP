"""Supplier risk data, derived from master suppliers/factories/products so nothing contradicts them.

Every supplier has a latent financial health `h` (0-100). Profile score, credit history, filings and
financial alerts are all derived from it, so the tools agree with each other. Hand-written stories live in
seed/*.csv and in the STORY_* tables below; the background generator skips those suppliers.
"""
from datetime import date, timedelta

# ---- stories -----------------------------------------------------------------------------------------------
# latent health, quarterly credit scores (newest first, 5 points) and filing shape for story suppliers
STORY_FIN = {
    "SUP-0053": dict(h=31, credit=[467, 520, 570, 615, 640], share=0.08, prior=(0.040, 0.055, 0.45, 1.6, 1.5)),
    "SUP-0055": dict(h=52, credit=[614, 630, 640, 650, 655], share=0.10),
    "SUP-0001": dict(h=66, credit=[712, 716, 710, 714, 709], share=0.10),
    "SUP-0072": dict(h=41, credit=[537, 575, 610, 650, 680], share=0.07, prior=(0.055, 0.060, 0.40, 1.1, 1.6)),
    "SUP-0035": dict(h=48, credit=[586, 620, 650, 690, 700], share=0.07, prior=(0.050, 0.070, 0.38, 1.2, 1.7)),
    "SUP-0036": dict(h=52, credit=[614, 640, 660, 690, 700], share=0.08, prior=(0.050, 0.085, 0.36, 1.2, 1.7)),
    "SUP-0038": dict(h=49, credit=[593, 600, 612, 622, 630], share=0.09, prior=(0.045, 0.070, 0.40, 1.4, 1.5)),
    "SUP-0028": dict(h=38, credit=[516, 560, 600, 640, 680], share=0.09, prior=(0.065, 0.065, 0.36, 1.4, 1.45)),
    "SUP-0065": dict(h=46, credit=[572, 600, 630, 650, 665], share=0.10, prior=(0.060, 0.080, 0.35, 1.2, 1.35)),
    "SUP-0011": dict(h=78, credit=[796, 790, 786, 780, 775], share=0.12, prior=(0.085, 0.14, 0.22, 0.62, 1.9)),
    "SUP-0014": dict(h=74, credit=[768, 765, 760, 758, 750], share=0.10, prior=(0.070, 0.12, 0.26, 0.75, 1.7)),
    "SUP-0033": dict(h=71, credit=[747, 745, 742, 738, 735], share=0.09, prior=(0.065, 0.13, 0.28, 0.80, 1.6)),
    "SUP-0023": dict(h=62, credit=[628, 641, 655, 662, 668], share=0.12),
    "SUP-0044": dict(h=80, credit=[810, 806, 800, 795, 790], share=0.10),
}
# latest filing: (profit margin, cash share, debt share, debt-to-equity, current ratio)
STORY_FILING = {
    "SUP-0053": (0.004, 0.025, 0.55, 2.9, 0.85),
    "SUP-0055": (0.022, 0.050, 0.40, 1.5, 1.25),
    "SUP-0001": (0.050, 0.090, 0.30, 0.9, 1.6),
    "SUP-0072": (0.012, 0.035, 0.52, 2.5, 0.95),
    "SUP-0035": (0.019, 0.045, 0.45, 2.1, 1.05),
    "SUP-0036": (0.022, 0.050, 0.42, 1.9, 1.10),
    "SUP-0038": (0.020, 0.048, 0.44, 1.9, 1.12),
    "SUP-0028": (0.017, 0.034, 0.40, 2.3, 0.92),
    "SUP-0065": (0.028, 0.048, 0.40, 1.8, 1.05),
    "SUP-0011": (0.095, 0.150, 0.20, 0.55, 2.1),
    "SUP-0014": (0.074, 0.120, 0.24, 0.70, 1.8),
    "SUP-0033": (0.067, 0.125, 0.26, 0.74, 1.7),
    "SUP-0023": (0.030, 0.060, 0.40, 1.4, 1.3),
    "SUP-0044": (0.090, 0.140, 0.20, 0.50, 2.2),
}
SOLE_SOURCE = {"SUP-0011": "Towels", "SUP-0014": "Scarves", "SUP-0028": "Footwear", "SUP-0033": "Fragrance",
               "SUP-0065": "Knitwear"}
CRIT_OVERRIDE = {"SUP-0053": "high", "SUP-0055": "medium", "SUP-0038": "high"}
WATCH = {}
# cyber rating / system access / security rating for the critical suppliers (poor ones are the "weakest three")
CYBER_STORY = {
    "SUP-0049": ("poor", "financial", "critical"), "SUP-0057": ("poor", "order_placement", "critical"),
    "SUP-0044": ("poor", "inventory", "critical"), "SUP-0036": ("fair", None, "medium"), "SUP-0072": ("fair", None, "medium"),
    "SUP-0035": ("good", None, "low"), "SUP-0011": ("good", None, "low"), "SUP-0014": ("good", None, "low"),
    "SUP-0028": ("fair", None, "medium"), "SUP-0033": ("good", None, "low"), "SUP-0065": ("fair", None, "medium"),
    "SUP-0023": ("fair", None, "medium"),
}
CYBER_FINDING = {
    "excellent": "No critical findings; MFA enforced, regular penetration testing",
    "good": "Minor patching delays; MFA in place for remote access",
    "fair": "Unpatched internet-facing services and weak password policy found",
    "poor": "Critical vulnerabilities exposed externally; no web application firewall; credentials seen in breach data",
}
# certificate overrides: (supplier, cert) -> (issued days ago, term days)
CERT_STORY = {
    ("SUP-0036", "OEKO-TEX"): (435, 365), ("SUP-0058", "OEKO-TEX"): (200, 365), ("SUP-0067", "OEKO-TEX"): (345, 365),
    ("SUP-0023", "BSCI"): (880, 730), ("SUP-0042", "OEKO-TEX"): (427, 365),
}
SEEDED_INSURANCE = {"SUP-0015"}
SEEDED_FACTORY_COMPLIANCE = {"FAC-0010", "FAC-0063", "FAC-0099"}
STORY_ALT_STYLES = {"STY-4012"}
SEEDED_ALERT_SUPPLIERS = {"SUP-0053", "SUP-0055", "SUP-0001", "SUP-0072", "SUP-0035", "SUP-0036", "SUP-0038",
                          "SUP-0028", "SUP-0065", "SUP-0046"}
ONBOARDING_STORY = {"SUP-0023", "SUP-0025", "SUP-0042", "SUP-0060"}
BANK_STORY = {"SUP-0023"}
REG_STORY = {"SUP-0023"}
RAW_STORY = {"SUP-0001", "SUP-0003", "SUP-0057", "SUP-0027", "SUP-0041", "SUP-0034"}

CERT_TERM = {"OEKO-TEX": 365, "GOTS": 365, "WRAP": 365, "BSCI": 730, "SEDEX": 730, "ISO9001": 1095, "ISO14001": 1095}
CERT_ISSUER = {"OEKO-TEX": "Hohenstein Institute (OEKO-TEX)", "GOTS": "Control Union Certifications",
               "WRAP": "WRAP Certification Body", "BSCI": "amfori BSCI", "SEDEX": "Sedex (SMETA audit)",
               "ISO9001": "BSI Group", "ISO14001": "SGS"}
BANKS = {"CN": "Bank of China", "VN": "Vietcombank", "TR": "Ziraat Bankasi", "IN": "State Bank of India",
         "BD": "Dutch-Bangla Bank", "IT": "Intesa Sanpaolo", "PT": "Banco Comercial Portugues", "MX": "BBVA Mexico",
         "GB": "Barclays UK", "FR": "BNP Paribas", "DE": "Deutsche Bank", "PL": "PKO Bank Polski"}
CITIES = {"CN": ["Dongguan", "Shaoxing", "Qingdao", "Ningbo"], "VN": ["Ho Chi Minh City", "Hai Phong", "Da Nang"],
          "TR": ["Istanbul", "Bursa", "Izmir"], "IN": ["Tiruppur", "Ludhiana", "Surat"], "BD": ["Dhaka", "Chattogram"],
          "IT": ["Prato", "Como", "Biella"], "PT": ["Porto", "Braga", "Guimaraes"], "MX": ["Puebla", "Leon"],
          "GB": ["Leicester", "Manchester"], "FR": ["Lyon", "Lille"], "DE": ["Stuttgart", "Mönchengladbach"],
          "PL": ["Lodz", "Poznan"]}
QUAL_BENCH = {  # country: (days, audit gbp, samples/testing gbp, admin gbp)
    "CN": (60, 3200, 5400, 1500), "VN": (75, 4200, 6500, 1500), "TR": (55, 3000, 4800, 1400), "IN": (70, 3900, 5200, 1500),
    "BD": (80, 4400, 6100, 1600), "IT": (40, 2400, 4200, 1200), "PT": (40, 2300, 4000, 1200), "MX": (65, 3600, 5000, 1500),
    "GB": (30, 1600, 3200, 1000), "FR": (35, 2100, 3900, 1200), "DE": (35, 2100, 3900, 1200), "PL": (40, 2000, 3800, 1200)}
CAPS = {"Womenswear": ["seam-sealing", "OEKO-TEX processing", "fast turnaround", "large batch"],
        "Menswear": ["tailoring", "OEKO-TEX processing", "fast turnaround", "large batch"],
        "Kids": ["GOTS cotton", "safety testing lab", "large batch", "fast turnaround"],
        "Home": ["non-stick coating", "stainless steel forming", "ceramic finishing", "large batch"],
        "Electricals": ["PCB assembly", "CE/UKCA testing", "injection moulding", "large batch"],
        "Beauty": ["filling and packing", "cosmetic GMP", "custom design", "large batch"],
        "Accessories": ["leather working", "metal fittings", "custom design", "fast turnaround"]}
ALERT_TEXT = {
    "quality": ["Defect rate above 3% on the last two inspections", "Late-stage rework found on final random inspection"],
    "delivery": ["Two shipments in the last quarter left more than a week late", "Capacity constraint reported by supplier"],
    "compliance": ["Overdue corrective action from the latest social audit", "Missing chemical test report for last season"],
    "security": ["External security scan found exposed services", "Supplier reported a phishing incident"],
    "regulatory": ["New customs documentation requirement not yet confirmed by supplier"],
    "financial": ["Credit score down over the last two quarters; payment terms being stretched",
                  "Late filing of annual accounts and falling liquidity"]}


def _band(score):
    return ("A_excellent" if score >= 780 else "B_good" if score >= 640 else "C_fair" if score >= 540
            else "D_poor" if score >= 440 else "E_very_poor")


def generate(g):
    r = g.rng
    sup = {s["supplier_id"]: s for s in g.master("suppliers")}
    facs = g.master("factories")
    prods = g.master("products")
    fac_by_sup, fac_by_id = {}, {f["factory_id"]: f for f in facs}
    for f in facs:
        fac_by_sup.setdefault(f["supplier_id"], []).append(f)
    live = [s for s in sup.values() if s["status"] != "exited"]
    spend = {k: float(v["annual_spend_gbp"] or 0) for k, v in sup.items()}
    top20 = set(sorted(spend, key=spend.get, reverse=True)[:20])

    # ---- latent health and criticality ----------------------------------------------------------------
    health = {}
    for s in live:
        sid = s["supplier_id"]
        if sid in STORY_FIN:
            health[sid] = STORY_FIN[sid]["h"]
        else:
            h = max(40, min(92, r.gauss(70, 9)))
            health[sid] = max(h, 64) if sid in top20 else h
    crit = {}
    for s in live:
        sid = s["supplier_id"]
        crit[sid] = ("critical" if spend[sid] >= 6.5e6 or sid in SOLE_SOURCE else "high" if spend[sid] >= 2.5e6
                     else "medium" if spend[sid] >= 1e6 else "low")
        crit[sid] = CRIT_OVERRIDE.get(sid, crit[sid])

    # ---- credit history (quarterly, newest first) ------------------------------------------------------
    credit, credit_latest = [], {}
    for s in live:
        sid = s["supplier_id"]
        if sid in STORY_FIN:
            scores = STORY_FIN[sid]["credit"]
        else:
            now = int(250 + 7 * health[sid] + r.uniform(-12, 12))
            drift = r.uniform(-14, 14)
            scores = [int(now - drift * i + r.uniform(-6, 6)) for i in range(5)]
            scores[0] = now
        credit_latest[sid] = scores[0]
        terms = int(s["payment_terms_days"] or 45)
        for i, sc in enumerate(scores):
            sc = max(300, min(950, sc))
            credit.append({
                "supplier_id": sid, "rating_date": g.days_ago(10 + r.randint(0, 6) + 91 * i),
                "credit_rating": _band(sc), "credit_score": sc,
                "days_payable_outstanding": terms + (0 if sc >= 640 else 12 if sc >= 540 else 25) + r.randint(-4, 4),
                "payment_default_count": 0 if sc >= 560 else 1 if sc >= 500 else 2 if sc >= 460 else 3})

    # ---- profiles ----------------------------------------------------------------------------------------
    sec_story = {}
    profiles = []
    for s in live:
        sid = s["supplier_id"]
        profiles.append({
            "supplier_id": sid, "criticality_rating": crit[sid], "financial_health_score": round(health[sid]),
            "security_risk_rating": None, "last_assessed_at": g.days_ago(r.randint(5, 80)),
            "watch_status": WATCH.get(sid, "none"), "watch_reason": "Credit score deteriorating; reviewing monthly" if WATCH.get(sid, "none") == "watch" else None,
            "updated_at": g.days_ago(r.randint(20, 120))})

    # ---- filings ---------------------------------------------------------------------------------------------
    filings = []
    for s in live:
        sid = s["supplier_id"]
        h = health[sid]
        st = STORY_FIN.get(sid, {})
        share = st.get("share", r.uniform(0.06, 0.25))
        rev = spend[sid] / share
        if sid in STORY_FILING:
            latest = STORY_FILING[sid]
            prior = st.get("prior") or tuple(latest)
        else:
            latest = ((h - 30) / 700.0 + r.uniform(-0.004, 0.004), 0.03 + h / 1400.0, max(0.12, 0.52 - h / 220.0),
                      max(0.3, 2.5 - h / 40.0), 0.7 + h / 55.0)
            d = r.uniform(-0.1, 0.1)
            prior = (latest[0] * (1 + d), latest[1] * (1 + d), latest[2] * (1 - d), latest[3] * (1 - d), latest[4] * (1 + d))
        for years, shape, scale in ((0, latest, 1.0), (1, prior, 1.0 if sid not in STORY_FILING else 1.0)):
            margin, cash, debt, de, cr = shape
            growth = 1.0 if years == 0 else (1.07 if sid in ("SUP-0053", "SUP-0028", "SUP-0065", "SUP-0072", "SUP-0035", "SUP-0036") else r.uniform(0.94, 1.04))
            revenue = rev * growth
            profit = revenue * margin
            equity = revenue * debt / de
            filings.append({
                "supplier_id": sid, "filing_date": g.days_ago(70 + r.randint(0, 120) + 365 * years),
                "filing_type": "annual accounts", "revenue_gbp": round(revenue), "profit_gbp": round(profit),
                "cash_gbp": round(revenue * cash), "debt_gbp": round(revenue * debt),
                "roe_pct": round(100 * profit / equity, 1), "debt_to_equity": round(de, 2), "current_ratio": round(cr, 2)})

    # ---- alerts ------------------------------------------------------------------------------------------------
    alerts, n = [], 0
    for s in live:
        sid = s["supplier_id"]
        if sid in SEEDED_ALERT_SUPPLIERS or sid in ONBOARDING_STORY or sid in STORY_FIN:
            continue
        mine = []
        if health[sid] < 58 and r.random() < 0.7:
            mine.append(("financial", "medium"))
        if r.random() < 0.18:
            mine.append((r.choice(["quality", "delivery", "compliance", "security", "regulatory"]), r.choice(["low", "medium"])))
        for typ, sev in mine:
            n += 1
            alerts.append({"alert_id": f"SRA-{n:06d}", "supplier_id": sid, "factory_id": None, "alert_type": typ,
                           "severity": sev, "description": r.choice(ALERT_TEXT[typ]),
                           "raised_at": g.days_ago(r.randint(8, 110)), "status": r.choices(["active", "resolved"], [65, 35])[0]})
    for f in facs:  # factories with a D audit rating carry a compliance alert for their supplier
        if f["audit_rating"] == "D" and f["status"] != "delisted" and f["factory_id"] not in ("FAC-0087",) \
                and f["supplier_id"] not in SEEDED_ALERT_SUPPLIERS and sup[f["supplier_id"]]["status"] != "exited":
            n += 1
            alerts.append({"alert_id": f"SRA-{n:06d}", "supplier_id": f["supplier_id"], "factory_id": f["factory_id"],
                           "alert_type": "compliance", "severity": "medium",
                           "description": "Factory rated D at last social audit; corrective action plan in progress",
                           "raised_at": g.days_ago(r.randint(20, 150)), "status": "active"})

    # ---- certifications (derived from the factories' certificates in master) -------------------------------
    certs = []
    for s in live:
        sid = s["supplier_id"]
        held = {}
        for f in fac_by_sup.get(sid, []):
            for c in (f["certifications"] or "").split(";"):
                if c:
                    held.setdefault(c, []).append(f["factory_id"])
        for c, fl in sorted(held.items()):
            term = CERT_TERM[c]
            if (sid, c) in CERT_STORY:
                ago, term = CERT_STORY[(sid, c)]
            elif r.random() < 0.06:
                ago = term + r.randint(15, 150)
            else:
                ago = r.randint(25, max(30, term - 40))
            issue = g.days_ago(ago)
            certs.append({"supplier_id": sid, "cert_type": c, "issuer": CERT_ISSUER[c], "issue_date": issue,
                          "expiry_date": issue + timedelta(days=term),
                          "scope": "Factories: " + ", ".join(sorted(fl))})

    # ---- insurance ---------------------------------------------------------------------------------------------
    insurance, pol = [], 0
    for s in live:
        sid = s["supplier_id"]
        if sid in SEEDED_INSURANCE:
            continue
        cover = 10e6 if spend[sid] >= 5e6 else 5e6 if spend[sid] >= 1e6 else 2e6
        types = ["General Liability", "Product Liability"] + r.sample(["Professional Indemnity", "Cyber", "Directors & Officers"], k=r.randint(0, 2))
        for t in types:
            pol += 1
            ago = r.randint(40, 320) if r.random() > 0.07 else r.randint(400, 470)
            issue = g.days_ago(ago)
            insurance.append({"supplier_id": sid, "policy_type": t, "provider": r.choice(["Allianz", "AXA XL", "Zurich", "Aviva", "Chubb", "Tokio Marine"]),
                              "policy_number": f"POL-{pol:06d}", "coverage_gbp": cover if t != "Cyber" else cover / 5,
                              "issue_date": issue, "expiry_date": issue + timedelta(days=365)})

    # ---- registration + bank -----------------------------------------------------------------------------------
    regs, bank = [], []
    for s in live:
        sid = s["supplier_id"]
        c = s["country"]
        onboarded = date.fromisoformat(s["onboarded_date"])
        if sid not in REG_STORY:
            regs.append({"supplier_id": sid, "legal_name": s["name"],
                         "registration_number": f"{c}-{r.randint(10_000_000, 99_999_999)}",
                         "registered_address": f"{r.randint(1, 240)} {r.choice(['Industrial Road', 'Textile Park', 'Export Zone', 'Mill Lane'])}, {r.choice(CITIES[c])}",
                         "registered_country": c, "incorporation_date": onboarded - timedelta(days=r.randint(900, 7000)),
                         "ultimate_owner": r.choice(["Founding family", "Listed parent company", "Private equity fund", "Founding family"]),
                         "tax_id": f"TAX-{r.randint(1_000_000, 9_999_999)}"})
        if sid in BANK_STORY:
            continue
        ok = r.random() > 0.12
        bank.append({"supplier_id": sid, "bank_name": BANKS[c], "account_holder": s["name"],
                     "account_number": f"{r.randint(10_000_000, 99_999_999)}{r.randint(1000, 9999)}",
                     "sort_code": f"{r.randint(10, 99)}-{r.randint(10, 99)}-{r.randint(10, 99)}", "bank_country": c,
                     "currency": s["currency"], "verified": ok, "last_verified_at": g.days_ago(r.randint(10, 300)) if ok else None})

    # ---- compliance records (supplier or factory level) ----------------------------------------------------------
    comp, n = [], 0
    texts = {"labour": ("Working hours and wages within policy", "Overtime above legal limit on 3 of the last 6 weeks"),
             "environmental": ("Effluent and waste handling within permit", "Wastewater test above permitted limit"),
             "safety": ("Fire safety and machinery guarding in order", "Blocked fire exit found at audit"),
             "tax_compliance": ("Tax filings up to date", "Late VAT return flagged by registry")}
    for s in live:
        sid = s["supplier_id"]
        if sid in STORY_FIN and sid != "SUP-0023" and health[sid] < 55:
            nc_rate = 0.0  # story suppliers' compliance record is only what the seeds say
        else:
            nc_rate = 0.05 if health[sid] >= 60 else 0.2
        if sid in ("SUP-0023", "SUP-0053"):
            nc_rate = 0.0
        for _ in range(r.randint(2, 4)):
            n += 1
            area = r.choice(list(texts))
            fac = r.choice(fac_by_sup[sid])["factory_id"] if fac_by_sup.get(sid) and area != "tax_compliance" else None
            if fac in SEEDED_FACTORY_COMPLIANCE:
                fac = None
            bad = r.random() < nc_rate
            exc = (not bad) and r.random() < 0.06
            comp.append({"record_id": f"CMP-{n:06d}", "supplier_id": sid, "factory_id": fac, "record_date": g.days_ago(r.randint(10, 360)),
                         "compliance_area": area, "finding": texts[area][1] if bad or exc else texts[area][0],
                         "status": "non_compliant" if bad else "exception" if exc else "compliant"})

    # ---- cyber + security risk ------------------------------------------------------------------------------------
    cyber, secur, sec_rating = [], [], {}
    for s in live:
        sid = s["supplier_id"]
        if sid in CYBER_STORY:
            rating, access, sec = CYBER_STORY[sid]
        else:
            rating = r.choices(["excellent", "good", "fair"], [24, 48, 28])[0]
            access = r.choice(["read_only", "inventory", "order_placement"]) if r.random() < 0.22 else None
            sec = {"poor": "high", "fair": "medium", "good": "low", "excellent": "low"}[rating]
        sec_rating[sid] = sec
        d = g.days_ago(r.randint(15, 170))
        cyber.append({"supplier_id": sid, "assessment_date": d, "rating": rating,
                      "assessment_source": r.choice(["SecurityScorecard", "BitSight", "Recorded Future", "Rapid7"]),
                      "findings": CYBER_FINDING[rating]})
        cyber.append({"supplier_id": sid, "assessment_date": d - timedelta(days=365),
                      "rating": rating if r.random() < 0.7 else r.choice(["good", "fair"]),
                      "assessment_source": "SecurityScorecard", "findings": "Prior-year external scan"})
        secur.append({"supplier_id": sid, "assessment_date": d + timedelta(days=r.randint(1, 10)), "rating": sec,
                      "system_access": access is not None, "access_level": access})
    for p in profiles:
        p["security_risk_rating"] = sec_rating[p["supplier_id"]]

    # ---- factories ---------------------------------------------------------------------------------------------------
    fprof = []
    for f in facs:
        score = {"A": 0, "B": 1, "C": 2, "D": 3}[f["audit_rating"]] + (1 if f["status"] == "conditional" else 0) \
            + (2 if f["status"] == "suspended" else 0) + (1 if f["status"] == "delisted" else 0)
        fprof.append({"factory_id": f["factory_id"], "risk_rating": "low" if score <= 1 else "medium" if score == 2 else "high" if score == 3 else "critical",
                      "last_assessed_at": f["last_audit_date"]})

    # ---- onboarding: history for suppliers onboarded since 2023 -------------------------------------------------------
    cases, items, case_n = [], [], 0
    controls = [("SOC-CTL-000001", 1), ("SOC-CTL-000002", 2), ("SOC-CTL-000003", 3), ("SOC-CTL-000004", 4),
                ("SOC-CTL-000005", 5), ("SOC-CTL-000006", 6)]
    ctl_desc = {1: "Verify company registration and legal status", 2: "Run sanctions list screening",
                3: "Check credit rating and financial health", 4: "Verify certifications and compliance",
                5: "Review management team", 6: "Assess environmental and labour practices"}
    for s in live:
        sid = s["supplier_id"]
        onboarded = date.fromisoformat(s["onboarded_date"])
        if s["status"] != "active" or onboarded < date(2023, 1, 1) or sid in ONBOARDING_STORY:
            continue
        case_n += 1
        days = int(QUAL_BENCH[s["country"]][0] * r.uniform(0.8, 1.3))
        created = onboarded - timedelta(days=days)
        cid = f"SOC-{case_n:06d}"
        cases.append({"case_id": cid, "supplier_id": sid, "status": "approved", "risk_rating": "high" if s["risk_rating"] == "critical" else s["risk_rating"],
                      "conditions": None, "created_at": created, "updated_at": onboarded, "completed_at": onboarded})
        for ctl, seq in controls:
            sub = created + timedelta(days=seq * days // 8)
            items.append({"case_id": cid, "item_id": str(seq), "control_id": ctl, "description": ctl_desc[seq],
                          "status": "approved", "due_date": created + timedelta(days=seq * days // 7), "submitted_at": sub})

    # ---- qualification benchmarks --------------------------------------------------------------------------------------
    bench = [{"country": c, "typical_days_to_qualify": d, "factory_audit_cost_gbp": a, "sample_testing_cost_gbp": t,
              "onboarding_admin_cost_gbp": m} for c, (d, a, t, m) in QUAL_BENCH.items()]

    # ---- alternative suppliers by master product category ----------------------------------------------------------------
    alt_s = []
    by_cat = {}
    for p in prods:
        by_cat.setdefault(p["category"], {"dept": p["department"], "sups": set()})["sups"].add(p["supplier_id"])
    barred = SEEDED_ALERT_SUPPLIERS | ONBOARDING_STORY | set(SOLE_SOURCE)
    for cat, info in sorted(by_cat.items()):
        if cat in SOLE_SOURCE.values():
            continue
        cands = [s for s in live if s["status"] == "active" and s["category_focus"] == info["dept"]
                 and s["supplier_id"] not in info["sups"] and s["supplier_id"] not in barred]
        cands.sort(key=lambda s: -float(s["otif_pct_12m"]))
        for tier, s in zip(["primary", "secondary", "tertiary"], cands[:3]):
            alt_s.append({"category": cat, "supplier_id": s["supplier_id"], "tier": tier,
                          "capability": r.choice(CAPS[info["dept"]])})

    # ---- alternative factories by SKU (all sizes of a style share their alternatives) ------------------------------------
    alt_f = []
    sole_pairs = {(sid, cat) for sid, cat in SOLE_SOURCE.items()}
    styles = {}
    for p in prods:
        styles.setdefault(p["style_id"], []).append(p)
    fac_ok = [f for f in facs if f["status"] in ("approved", "conditional")]
    for sty, plist in sorted(styles.items()):
        p0 = plist[0]
        if sty in STORY_ALT_STYLES or (p0["supplier_id"], p0["category"]) in sole_pairs:
            continue
        dept = p0["department"]
        cands = [f for f in fac_ok if sup[f["supplier_id"]]["category_focus"] == dept and f["factory_id"] != p0["factory_id"]
                 and f["supplier_id"] not in barred and sup[f["supplier_id"]]["status"] == "active"]
        for f in r.sample(cands, k=min(len(cands), r.randint(1, 2))):
            q = r.choices(["approved", "in_progress", "pending", "failed"], [58, 22, 14, 6])[0]
            if f["status"] == "conditional" and q == "approved":
                q = "in_progress"
            cost = 0 if q == "approved" else r.randint(35, 90) * 100
            for p in plist:
                alt_f.append({"sku": p["sku"], "factory_id": f["factory_id"], "approved": q == "approved", "qualification_status": q,
                              "unit_cost_delta_pct": round(r.gauss(2, 5), 1), "lead_time_delta_days": r.randint(-7, 14),
                              "qualification_cost_gbp": cost})

    # ---- raw materials -----------------------------------------------------------------------------------------------------
    mats = {"Womenswear": ["cotton", "polyester", "viscose"], "Menswear": ["cotton", "wool", "polyester"],
            "Kids": ["cotton", "polyester"], "Home": ["cotton", "stainless steel", "ceramic"],
            "Electricals": ["copper", "ABS plastic", "lithium"], "Beauty": ["plant oils", "glass", "aluminium"],
            "Accessories": ["leather", "zinc alloy", "silk"]}
    origin = {"CN": ("CN", ["Shandong", "Jiangsu", "Hubei"]), "VN": ("US", ["Texas", "Georgia"]), "TR": ("TR", ["Aegean", "Cukurova"]),
              "IN": ("IN", ["Gujarat", "Maharashtra"]), "BD": ("IN", ["Gujarat", "Telangana"]), "PT": ("EG", ["Nile Delta"]),
              "IT": ("EG", ["Nile Delta"]), "MX": ("US", ["Texas"]), "GB": ("GB", [""]), "FR": ("FR", [""]), "DE": ("DE", [""]), "PL": ("PL", [""])}
    raw = []
    for s in live:
        sid = s["supplier_id"]
        if sid in RAW_STORY:
            continue
        oc, regions = origin[s["country"]]
        for m in mats[s["category_focus"]][: r.randint(1, 2)]:
            o = oc if m in ("cotton", "wool", "silk", "leather", "viscose", "plant oils") else s["country"]
            raw.append({"supplier_id": sid, "raw_material": m, "origin_country": o, "origin_region": r.choice(regions) or None})

    # ---- logistics providers ---------------------------------------------------------------------------------------------------
    logi = []
    for c in g.master("carriers"):
        mode = c["mode"]
        cr = "critical" if mode in ("ocean", "forwarder") else "high" if mode in ("air", "rail") else "medium" if mode == "road" else "low"
        if c["carrier_id"] == "CAR-009":
            cr = "critical"
        cyb = "fair" if c["carrier_id"] in ("CAR-010", "CAR-006") else r.choices(["excellent", "good"], [40, 60])[0]
        access = mode in ("forwarder", "ocean", "parcel")
        logi.append({"carrier_id": c["carrier_id"], "criticality_rating": cr, "cyber_rating": cyb,
                     "assessment_date": g.days_ago(r.randint(30, 160)), "system_access": access,
                     "access_level": "shipment_data" if access else None})

    controls_rows = [{"control_id": c, "description": ctl_desc[i], "control_type": t, "sequence": i}
                     for (c, i), t in zip(controls, ["document review", "sanctions screening", "financial check",
                                                      "certification check", "document review", "document review"])]
    return {
        "supplier_profiles": profiles, "supplier_risk_alerts": alerts, "supplier_certifications": certs,
        "supplier_insurance": insurance, "supplier_bank_details": bank, "supplier_registrations": regs,
        "supplier_compliance_records": comp, "supplier_credit_data": credit, "supplier_cyber_security": cyber,
        "supplier_financial_filings": filings, "supplier_security_risk": secur, "factory_profiles": fprof,
        "onboarding_cases": cases, "onboarding_controls": controls_rows, "onboarding_items": items,
        "alternative_suppliers": alt_s, "alternative_factories": alt_f, "qualification_benchmarks": bench,
        "supplier_raw_materials": raw, "logistics_provider_risk": logi, "sole_source_designations": [],
        "security_questionnaires": [],
    }
