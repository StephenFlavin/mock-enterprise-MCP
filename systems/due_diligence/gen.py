"""Generate due diligence data: risk ratings, evidence, factory profiles, ownership, mapping, compliance gaps.

Master data is the source of truth for names, countries, factories and products. The planted stories are:
  * Xinjiang cotton / polysilicon exposure (SUP-0001, SUP-0003, SUP-0057, SUP-0027), all China, high/critical
  * Debt bondage at the Tamil Nadu spinning mill FAC-0035 (SUP-0018), which supplies yarn to four Indian suppliers
  * FAC-0003 (SUP-0002, Vietnam): forced labour and child labour grievances, small share of factory capacity
  * FAC-0087 (SUP-0046, India): audit D and adverse media on working conditions
  * Polish nearshore suppliers SUP-0040 / SUP-0054 / SUP-0068: tier one mapped, deeper tiers (Asian raw materials) not
  * Prospective supplier Sunrise Pack Co. Ltd (PSP-0001) with an opaque BVI shareholder and a Hong Kong parent
"""
from datetime import timedelta

COUNTRY_NAMES = {"IN": "India", "BD": "Bangladesh", "CN": "China", "VN": "Vietnam", "TR": "Turkey", "PT": "Portugal",
                 "IT": "Italy", "MX": "Mexico", "PL": "Poland", "DE": "Germany", "FR": "France", "GB": "United Kingdom", "KH": "Cambodia", "ID": "Indonesia", "HK": "Hong Kong", "VG": "British Virgin Islands"}
# forced_labour_index 0-1 (higher = worse), human rights 0-100 (higher = better), legal, enforcement, corruption
COUNTRY_INDEX = {"CN": (0.85, 18, 48, 55, 76), "BD": (0.78, 28, 45, 32, 76), "IN": (0.72, 35, 52, 38, 61),
                 "VN": (0.68, 40, 55, 45, 61), "TR": (0.52, 45, 58, 50, 54), "MX": (0.46, 42, 50, 40, 69),
                 "PL": (0.20, 74, 80, 72, 47), "PT": (0.18, 82, 85, 78, 38), "IT": (0.17, 80, 82, 75, 44),
                 "FR": (0.11, 88, 90, 85, 29), "DE": (0.10, 90, 93, 88, 21), "GB": (0.12, 86, 92, 88, 29),
                 "KH": (0.74, 30, 40, 35, 82), "ID": (0.55, 42, 50, 42, 66),
                 "HK": (0.30, 62, 70, 65, 24), "VG": (0.15, 80, 85, 75, 35)}
CENTRE = {"CN": (23.0, 113.5), "BD": (23.8, 90.4), "IN": (11.1, 77.3), "VN": (10.8, 106.7), "TR": (41.0, 28.9),
          "MX": (19.4, -99.1), "PL": (52.2, 21.0), "PT": (41.1, -8.6), "IT": (45.5, 9.2), "FR": (48.9, 2.4),
          "DE": (50.1, 8.7), "GB": (52.5, -1.9), "HK": (22.3, 114.2), "VG": (18.4, -64.6), "KH": (11.6, 104.9), "ID": (-6.2, 106.8)}
LEVEL = {"low": 0, "medium": 1, "high": 2, "critical": 3}
ROLE_LEVEL = ["low", "medium", "high", "critical"]

PLANTED_FL = {"SUP-0001": "critical", "SUP-0002": "critical", "SUP-0018": "critical", "SUP-0027": "critical",
              "SUP-0003": "high", "SUP-0057": "high", "SUP-0046": "high", "SUP-0008": "high", "SUP-0029": "high",
              "SUP-0055": "high", "SUP-0048": "high"}
PLANTED_STATUS = {"SUP-0001": "escalated", "SUP-0002": "escalated", "SUP-0018": "in_progress", "SUP-0027": "in_progress",
                  "SUP-0003": "in_progress", "SUP-0057": "not_started", "SUP-0046": "in_progress",
                  "SUP-0008": "in_progress", "SUP-0029": "not_started", "SUP-0055": "in_progress",
                  "SUP-0048": "not_started", "SUP-0040": "complete", "SUP-0054": "in_progress", "SUP-0068": "not_started"}

# (category, evidence_type, description, level, credibility, source, days_ago)
EVIDENCE = {
    "SUP-0001": [
        ("forced_labour", "document", "Cotton declared as sourced from Aksu, Xinjiang ginneries; no origin audit or lot-level tracing", "critical", "highly_verified", "Supplier raw material declaration", 40),
        ("wages_hours", "audit_finding", "Social audit found 60+ hour weeks and unpaid overtime at FAC-0001", "high", "verified", "Third-party social audit", 8),
        ("freedom_association", "worker_interview", "Workers report no independent union representation", "high", "partially_verified", "Worker interviews", 25),
        ("adverse_media", "media_report", "Press reports link the supplier's cotton to Xinjiang", "medium", "verified", "Reuters", 60)],
    "SUP-0002": [
        ("forced_labour", "audit_finding", "Debt bondage in recruitment: workers repaying labour agency fees at FAC-0003", "critical", "highly_verified", "Third-party social audit (FAC-0003)", 20),
        ("forced_labour", "worker_interview", "Migrant workers report passports held by the labour agent", "high", "verified", "Worker interviews", 18),
        ("child_labour", "audit_finding", "Underage workers identified in the sewing unit at FAC-0003", "critical", "verified", "Third-party social audit (FAC-0003)", 20),
        ("grievance_mechanism", "grievance_record", "Hotline reports of recruitment fees not reimbursed", "high", "verified", "Worker hotline", 15)],
    "SUP-0018": [
        ("forced_labour", "ngo_report", "NGO investigation alleges recruitment-fee debt bondage at spinning mill FAC-0035, Tamil Nadu", "critical", "verified", "Southern Workers Rights Forum", 35),
        ("forced_labour", "media_report", "Press article alleges debt bondage at the mill; mill declined to comment", "high", "partially_verified", "International Labour News Network", 21),
        ("wages_hours", "audit_finding", "Audit rating C: excessive overtime and incomplete wage records at FAC-0035", "high", "verified", "Third-party social audit", 120)],
    "SUP-0027": [
        ("forced_labour", "document", "Polysilicon declared from Xinjiang producers; no tracing beyond tier one", "critical", "highly_verified", "Supplier raw material declaration", 30),
        ("adverse_media", "media_report", "Industry report links Xinjiang polysilicon producers to state labour transfer programmes", "high", "verified", "Industry research", 90)],
    "SUP-0003": [
        ("forced_labour", "document", "Cotton declared from Xinjiang; mass-balance claim only, no lot-level tracing", "high", "verified", "Supplier raw material declaration", 50),
        ("wages_hours", "audit_finding", "Overtime above legal limits in peak season at FAC-0005", "medium", "verified", "Third-party social audit", 70)],
    "SUP-0057": [
        ("forced_labour", "document", "Cotton declared from Xinjiang; ginnery list not provided", "high", "verified", "Supplier raw material declaration", 45),
        ("wages_hours", "audit_finding", "Wage records incomplete at FAC-0107", "medium", "verified", "Third-party social audit", 80)],
    "SUP-0046": [
        ("wages_hours", "audit_finding", "Rated D at unannounced audit: forced overtime and unpaid wages at FAC-0087", "high", "verified", "Unannounced social audit", 18),
        ("forced_labour", "media_report", "Press reports of workers compelled to work overtime at FAC-0087", "high", "verified", "BBC", 20),
        ("forced_labour", "document", "Cotton yarn bought from mill FAC-0035, which is the subject of a debt bondage allegation", "medium", "unverified", "Sub-tier mapping", 21)],
    "SUP-0008": [("forced_labour", "audit_finding", "Recruitment fees charged to migrant workers", "high", "verified", "Third-party social audit", 55)],
    "SUP-0029": [("forced_labour", "worker_interview", "Workers report ID documents retained by dormitory managers", "high", "partially_verified", "Worker interviews", 65)],
    "SUP-0055": [("forced_labour", "audit_finding", "Contract workers without written agreements; recruitment fees charged", "high", "verified", "Third-party social audit", 75)],
    "SUP-0048": [("forced_labour", "ngo_report", "NGO report on withheld wages and restricted movement at supplier dormitories", "high", "partially_verified", "Labour rights NGO", 85)],
}

REQUIREMENTS = [
    ("REQ-0001", "UK", "UK Modern Slavery Act 2015 (section 54)", "forced_labour",
     "Publish an annual slavery and human trafficking statement, board-approved, describing steps taken to prevent forced labour in operations and supply chains.",
     "Commercial organisations with turnover of GBP 36m or more", "2015-10-29",
     "No fixed financial penalty; High Court injunction, unlimited fine for contempt, reputational damage"),
    ("REQ-0002", "UK", "UK Procurement Act 2023", "forced_labour",
     "Public buyers must exclude suppliers with modern slavery convictions or findings; bidders must be able to show supply chain controls.",
     "Companies bidding for UK public contracts", "2025-02-24", "Exclusion and debarment from public contracts"),
    ("REQ-0003", "UK", "UK Consumer Protection Act 1987", "product_liability",
     "Producers and importers are strictly liable for damage caused by a defective product, whether or not they were negligent.",
     "Producers, own-branders and importers into the UK", "1988-03-01",
     "Unlimited damages for death, personal injury and property damage; 10-year long-stop"),
    ("REQ-0004", "UK", "UK General Product Safety Regulations 2005", "product_liability",
     "Only place safe products on the market; keep traceability records and notify authorities of unsafe products.",
     "Producers and distributors of consumer products in the UK", "2005-10-01",
     "Criminal prosecution: unlimited fines and up to 12 months imprisonment; recall orders"),
    ("REQ-0005", "EU", "EU Corporate Sustainability Due Diligence Directive (CSDDD, 2024/1760)", "due_diligence",
     "Identify, prevent, mitigate and remedy adverse human rights and environmental impacts across the chain of activities; embed due diligence in policies, run a complaints procedure and monitor effectiveness.",
     "Very large EU and non-EU companies with EU turnover above the thresholds; phased in from 2028", "2024-07-25 (applies in phases from 2028)",
     "Fines of at least 5% of net worldwide turnover; civil liability for damages"),
    ("REQ-0006", "EU", "EU Forced Labour Regulation (2024/3015)", "forced_labour",
     "Products made with forced labour may not be placed on or exported from the EU market; authorities investigate on a risk basis and operators must be able to show the supply chain.",
     "All economic operators placing products on the EU market", "2024-12-13 (applies from December 2027)",
     "Withdrawal of products from the market, border detention and disposal; national penalties"),
    ("REQ-0007", "EU", "EU General Product Safety Regulation (2023/988)", "product_liability",
     "Economic operators must ensure products are safe, keep technical documentation and notify unsafe products through Safety Gate.",
     "Manufacturers, importers and distributors of consumer products in the EU", "2024-12-13",
     "Member State fines (up to 4% of annual turnover in several states); recalls and sales bans"),
    ("REQ-0008", "EU", "EU Product Liability Directive (2024/2853)", "product_liability",
     "Strict liability for defective products, now including software; courts can order disclosure of evidence and presume defect in complex cases.",
     "Manufacturers, importers and online platforms for products placed on the EU market after December 2026", "2024-12-08 (applies from December 2026)",
     "Compensation for death, injury, property damage and data loss; no liability cap"),
    ("REQ-0009", "US", "US Uyghur Forced Labor Prevention Act (UFLPA)", "forced_labour",
     "Rebuttable presumption that goods made wholly or partly in Xinjiang, or by listed entities, use forced labour; importers must show full supply chain tracing and clear evidence to obtain release.",
     "All importers of goods into the US", "2022-06-21",
     "Detention, exclusion or seizure of goods at the border; civil penalties"),
    ("REQ-0010", "US", "US Tariff Act section 307 (19 USC 1307)", "forced_labour",
     "Goods mined, produced or manufactured with forced labour are prohibited from entry; CBP issues withhold release orders and findings.",
     "All importers of goods into the US", "1930-06-17",
     "Detention, seizure and forfeiture of goods; civil penalties"),
    ("REQ-0011", "US", "California Transparency in Supply Chains Act (SB 657)", "supply_chain_transparency",
     "Disclose on the company website efforts to eradicate slavery and human trafficking: verification, audits, certification, internal accountability and training.",
     "Retailers and manufacturers doing business in California with worldwide revenue above USD 100m", "2012-01-01",
     "Injunctive relief by the California Attorney General; no fine"),
    ("REQ-0012", "US", "US state product liability law and Consumer Product Safety Act", "product_liability",
     "Strict product liability in tort for defective products; CPSA requires reporting of substantial product hazards to the CPSC within 24 hours.",
     "Manufacturers, importers, distributors and retailers selling in the US", "1972-10-27",
     "Compensatory and punitive damages; CPSC civil penalties above USD 100,000 per violation"),
    ("REQ-0013", "CA", "Canada Fighting Against Forced Labour and Child Labour in Supply Chains Act", "forced_labour",
     "File an annual report to the Minister describing steps taken to prevent and reduce the risk of forced and child labour in the supply chain.",
     "Entities listed in Canada, or doing business in Canada with assets above CAD 20m or 250 employees", "2024-01-01",
     "Fines of up to CAD 250,000 for failing to report or for false reports"),
    ("REQ-0014", "CA", "Canada Customs Tariff, tariff item 9897.00.00", "forced_labour",
     "Goods mined, manufactured or produced wholly or in part by forced labour cannot be imported into Canada.",
     "All importers of goods into Canada", "2020-07-01", "Detention and seizure of goods at the border"),
]
EVIDENCE_REQS = [r[0] for r in REQUIREMENTS if r[3] != "product_liability"]
GAP_TEXT = {
    "REQ-0001": "Slavery statement not reviewed against current supplier mapping",
    "REQ-0002": "No supply chain controls evidence prepared for public tenders",
    "REQ-0005": "Tier 2+ mapping and risk assessment incomplete for CSDDD",
    "REQ-0006": "No tracing evidence below tier one to show products are free of forced labour",
    "REQ-0009": "No origin audit; unclear whether inputs come from Xinjiang",
    "REQ-0010": "Tracing evidence below tier one not held",
    "REQ-0011": "Verification and audit disclosures out of date",
    "REQ-0013": "Supplier-level evidence for the annual report not collected",
    "REQ-0014": "No origin evidence to clear goods at the Canadian border",
}
EU_DOCS = ["Supplier Code of Conduct acknowledgement", "Ownership disclosure (UBO)", "Tier 2+ supplier list",
           "Social audit report (last 24 months)", "Grievance mechanism evidence", "Human rights policy"]
UK_DOCS = ["Modern Slavery statement", "Social audit report (last 24 months)"]
TIER3 = {"Womenswear": ["IN", "CN"], "Menswear": ["IN", "CN"], "Kids": ["IN", "BD"], "Home": ["IN", "CN"],
         "Beauty": ["CN", "IN"], "Electricals": ["CN", "VN"], "Accessories": ["IN", "CN"]}
MATERIAL = {"Womenswear": "Cotton", "Menswear": "Cotton", "Kids": "Cotton", "Home": "Cotton", "Beauty": "Packaging resin",
            "Electricals": "Copper", "Accessories": "Leather"}
PRODUCT_TYPES = {"Womenswear": "Knitted and woven garments", "Menswear": "Woven garments; outerwear", "Kids": "Kids apparel; nightwear",
                 "Home": "Home textiles; cotton fabric", "Beauty": "Beauty products and packaging", "Electricals": "Small electricals",
                 "Accessories": "Accessories; bags"}
MILL_DOWNSTREAM = {"SUP-0024": "Cotton yarn", "SUP-0046": "Knitted cotton fabric", "SUP-0043": "Cotton yarn", "SUP-0011": "Cotton yarn"}


def generate(g):
    r = g.rng
    asof = g.as_of
    d = lambda n: asof - timedelta(days=n)
    suppliers = [s for s in g.master("suppliers") if s["supplier_type"] == "product"]
    sup = {s["supplier_id"]: s for s in suppliers}
    factories = g.master("factories")
    fac_by_sup = {}
    for f in factories:
        fac_by_sup.setdefault(f["supplier_id"], []).append(f)
    products = g.master("products")
    employees = [e["employee_id"] for e in g.master("employees")[:60]]

    # ---- country risk indices
    units = {}
    sup_country = {s["supplier_id"]: s["country"] for s in g.master("suppliers")}
    for po in g.master("purchase_orders"):
        if po["status"] not in ("cancelled", "draft"):
            c = sup_country.get(po["supplier_id"])
            units[c] = units.get(c, 0) + int(po["total_units"])
    country_indices = []
    for c, (fl, hr, leg, enf, cor) in COUNTRY_INDEX.items():
        country_indices.append({"country": c, "country_name": COUNTRY_NAMES[c], "forced_labour_index": fl,
                                "human_rights_score": hr, "legal_environment": leg, "enforcement_level": enf,
                                "corruption_index": cor, "sourcing_volume_units": units.get(c, 0), "updated_at": d(30)})

    # ---- supplier risk ratings
    ratings, fl_of = [], {}
    for s in suppliers:
        sid, c = s["supplier_id"], s["country"]
        fl = PLANTED_FL.get(sid)
        if fl is None:
            fl = "medium" if r.random() < COUNTRY_INDEX[c][0] * 0.4 else "low"
        fl_of[sid] = fl
        fin = s["risk_rating"]
        comp = "high" if fl in ("high", "critical") else r.choices(["low", "medium"], [70, 30])[0]
        overall = ROLE_LEVEL[max(LEVEL[fl], LEVEL[comp], LEVEL[fin])]
        status = PLANTED_STATUS.get(sid) or r.choices(["complete", "in_progress", "not_started"], [60, 25, 15])[0]
        ratings.append({"supplier_id": sid, "forced_labour_risk": fl, "compliance_risk": comp, "financial_risk": fin,
                        "overall_risk": overall, "due_diligence_status": status, "last_assessed_at": d(r.randint(10, 150)),
                        "next_review_date": asof + timedelta(days=r.randint(30, 180)), "updated_at": d(r.randint(1, 30))})
    status_of = {x["supplier_id"]: x["due_diligence_status"] for x in ratings}

    # ---- risk evidence
    evidence = []
    for i, s in enumerate(suppliers, 1):
        sid = s["supplier_id"]
        rows = EVIDENCE.get(sid)
        if rows is None:
            rows = []
            for _ in range(r.randint(0, 2)):
                rows.append((r.choice(["health_safety", "wages_hours", "environmental", "grievance_mechanism"]),
                             r.choice(["audit_finding", "certification", "document"]),
                             r.choice(["Minor fire safety observation closed", "Wage slips reviewed with no issues",
                                       "Effluent testing within limits", "Grievance box in place and used"]),
                             r.choice(["low", "low", "medium"]), r.choice(["verified", "highly_verified"]),
                             r.choice(["Third-party social audit", "Certification body"]), r.randint(30, 300)))
        for n, (cat, et, desc, lvl, cred, src, ago) in enumerate(rows, 1):
            evidence.append({"supplier_id": sid, "evidence_id": f"EV-{sid[-4:]}-{n:02d}", "risk_category": cat,
                             "evidence_type": et, "description": desc, "risk_level": lvl, "credibility": cred,
                             "source": src, "found_at": d(ago), "updated_at": d(max(ago - 2, 0))})

    # ---- factory profiles (every master factory, attributes copied from master)
    profiles = []
    for f in factories:
        s = sup.get(f["supplier_id"])
        lat, lon = CENTRE[f["country"]]
        rating = f["audit_rating"]
        remed = {"D": "non_compliant", "C": "in_remediation"}.get(rating, "compliant")
        mech = r.random() < 0.88
        if f["factory_id"] in ("FAC-0003", "FAC-0087"):
            mech = False
        profiles.append({"factory_id": f["factory_id"], "name": f["name"], "supplier_id": f["supplier_id"],
                         "country": f["country"], "city": f["city"], "latitude": round(lat + r.uniform(-2, 2), 4),
                         "longitude": round(lon + r.uniform(-2, 2), 4),
                         "product_types": PRODUCT_TYPES.get(s["category_focus"], "Mixed") if s else "Mixed",
                         "capacity_units_month": int(f["capacity_units_month"]), "workers": int(f["workers"]),
                         "certifications": f["certifications"].replace(";", "; "), "last_audit_date": f["last_audit_date"],
                         "audit_rating": rating, "remediation_status": remed, "grievance_mechanism": mech,
                         "updated_at": d(r.randint(1, 30))})

    # ---- worker grievances
    grievances, gid = [], 1
    story_grv = [
        ("FAC-0003", 22, "forced_labour", "Workers report paying recruitment fees to a labour agent and still owing wages to repay it", "open", ""),
        ("FAC-0003", 19, "forced_labour", "Migrant workers say the agent holds their passports", "investigating", ""),
        ("FAC-0003", 16, "child_labour", "Hotline caller reports 15-year-olds working night shifts in the sewing unit", "open", ""),
        ("FAC-0003", 14, "hours", "Mandatory 70-hour weeks during peak with threats of dismissal", "open", ""),
        ("FAC-0003", 40, "wages", "Wage deductions for dormitory and meals not explained", "investigating", ""),
        ("FAC-0001", 25, "wages", "Overtime not paid on correct dates; unclear deductions", "investigating", ""),
        ("FAC-0001", 20, "freedom_association", "Worker denied access to the grievance hotline after raising overtime", "investigating", ""),
        ("FAC-0001", 33, "hours", "60+ hour weeks without rest day", "open", ""),
        ("FAC-0035", 30, "forced_labour", "Workers report recruitment fee advances deducted from wages until repaid", "open", ""),
        ("FAC-0035", 28, "freedom_association", "Workers say identity documents are kept by the recruiter", "investigating", ""),
        ("FAC-0087", 18, "hours", "Forced overtime; refusal leads to lost bonus", "open", ""),
        ("FAC-0087", 26, "wages", "Wages for two weeks unpaid", "investigating", ""),
    ]
    fac_sup = {f["factory_id"]: f["supplier_id"] for f in factories}
    for fid, ago, cat, desc, st, note in story_grv:
        grievances.append({"grievance_id": f"GRV-9{gid:05d}", "factory_id": fid, "supplier_id": fac_sup[fid],
                           "grievance_date": d(ago), "category": cat, "description": desc, "remediation_status": st,
                           "resolution_notes": note, "updated_at": d(max(ago - 3, 0))})
        gid += 1
    story_fac = {x[0] for x in story_grv}
    noise = [("wages", "Wages paid late by a few days"), ("hours", "Overtime above company policy in peak week"),
             ("safety", "Blocked aisle near cutting tables"), ("discrimination", "Complaint about shift allocation"),
             ("other", "Canteen food quality")]
    for f in factories:
        if f["factory_id"] in story_fac:
            continue
        for _ in range(r.choice([0, 0, 1, 1, 2])):
            cat, desc = r.choice(noise)
            st = r.choices(["open", "investigating", "resolved", "closed"], [10, 20, 40, 30])[0]
            ago = r.randint(20, 300)
            grievances.append({"grievance_id": f"GRV-{gid:06d}", "factory_id": f["factory_id"], "supplier_id": f["supplier_id"],
                               "grievance_date": d(ago), "category": cat, "description": desc, "remediation_status": st,
                               "resolution_notes": "Resolved through management discussion" if st in ("resolved", "closed") else "",
                               "updated_at": d(max(ago - 10, 0))})
            gid += 1

    # ---- mill and sub-tier relationships
    sub_tiers = []
    for down, flow in MILL_DOWNSTREAM.items():
        sub_tiers.append({"supplier_id": down, "sub_tier_supplier_id": "SUP-0018", "factory_id": "FAC-0035", "material_flow": flow,
                          "relationship_type": "raw_material", "mapped_date": d(r.randint(60, 200)), "updated_at": d(20)})
    seen = {(x["supplier_id"], x["sub_tier_supplier_id"]) for x in sub_tiers}
    for s in suppliers:
        if s["supplier_id"] in MILL_DOWNSTREAM or r.random() < 0.55:
            continue
        other = r.choice([x for x in suppliers if x["supplier_id"] != s["supplier_id"] and x["supplier_id"] != "SUP-0018"])
        if (s["supplier_id"], other["supplier_id"]) in seen:
            continue
        seen.add((s["supplier_id"], other["supplier_id"]))
        sub_tiers.append({"supplier_id": s["supplier_id"], "sub_tier_supplier_id": other["supplier_id"], "factory_id": "",
                          "material_flow": r.choice(["Yarn", "Trims", "Dyes", "Packaging", "Components"]),
                          "relationship_type": r.choice(["raw_material", "component", "contract_manufacturing", "outsourced_process"]),
                          "mapped_date": d(r.randint(60, 300)), "updated_at": d(r.randint(1, 60))})

    # ---- product supply chain map
    mapping = []
    mill_products = {x["supplier_id"] for x in sub_tiers if x["factory_id"] == "FAC-0035"}
    for p in products:
        sku, sid, cat = p["sku"], p["supplier_id"], p["department"]
        mapping.append({"product_sku": sku, "tier": 1, "node_id": p["factory_id"], "entity_name": next(
            (f["name"] for f in factories if f["factory_id"] == p["factory_id"]), ""), "country": p["country_of_origin"],
            "factory_id": p["factory_id"], "supplier_id": sid, "material_flow": "Finished goods", "mapping_status": "mapped",
            "mapped_at": d(r.randint(60, 300)), "updated_at": d(r.randint(1, 60))})
        if cat in ("Womenswear", "Menswear", "Kids", "Home"):
            if sid in mill_products:
                mapping.append({"product_sku": sku, "tier": 2, "node_id": "FAC-0035", "entity_name": "Jackson Knitting 35",
                                "country": "IN", "factory_id": "FAC-0035", "supplier_id": "SUP-0018", "material_flow": "Cotton yarn",
                                "mapping_status": "mapped", "mapped_at": d(40), "updated_at": d(20)})
            else:
                st = "partially_mapped" if r.random() < 0.35 else "unmapped"
                mapping.append({"product_sku": sku, "tier": 2, "node_id": f"T2-{sku}", "entity_name": "Fabric or yarn mill (name not held)",
                                "country": p["country_of_origin"], "factory_id": "", "supplier_id": "", "material_flow": "Fabric and yarn",
                                "mapping_status": st, "mapped_at": d(r.randint(60, 300)), "updated_at": d(r.randint(1, 60))})
            mapping.append({"product_sku": sku, "tier": 3, "node_id": f"T3-{sku}", "entity_name": "Fibre source (ginning or farm)",
                            "country": "", "factory_id": "", "supplier_id": "", "material_flow": "Raw cotton", "mapping_status": "unmapped",
                            "mapped_at": d(r.randint(60, 300)), "updated_at": d(r.randint(1, 60))})
    for row in mapping:
        if row["product_sku"] == "SKU-103808":
            if row["tier"] == 2:
                row.update({"entity_name": "Yarn spinner (name not disclosed)", "country": "CN", "mapping_status": "partially_mapped"})
            if row["tier"] == 3:
                row.update({"entity_name": "Cotton ginneries, Aksu, Xinjiang (declared by supplier, unconfirmed)", "country": "CN"})

    # ---- compliance requirements and evidence
    reqs = [{"requirement_id": a, "jurisdiction": b, "regulation": c, "topic": t, "requirement_text": text, "applicability": app,
             "effective_date": eff, "penalties": pen, "updated_at": d(30)} for a, b, c, t, text, app, eff, pen in REQUIREMENTS]
    inventory = []
    for s in suppliers:
        sid = s["supplier_id"]
        risk = LEVEL[fl_of[sid]]
        for rid in EVIDENCE_REQS:
            held = r.random() < (0.85 if risk == 0 else 0.6 if risk == 1 else 0.25)
            if sid == "SUP-0001":
                held = rid in ("REQ-0001", "REQ-0011")
            prio = "critical" if (not held and rid in ("REQ-0009", "REQ-0006") and risk >= 2) else \
                   ("high" if risk >= 2 else "medium" if risk == 1 else "low")
            inventory.append({"supplier_id": sid, "requirement_id": rid, "evidence_held": held,
                              "evidence_type": r.choice(["policy", "audit", "certification", "document"]) if held else "",
                              "evidence_date": d(r.randint(30, 400)) if held else "",
                              "gap_description": "" if held else GAP_TEXT[rid], "priority": prio, "updated_at": d(r.randint(1, 60))})
    for row in inventory:
        if row["supplier_id"] == "SUP-0001" and row["requirement_id"] == "REQ-0009":
            row["gap_description"] = "No Xinjiang origin audit; cotton declared from Aksu, Xinjiang with no lot-level tracing"
            row["priority"] = "critical"

    # ---- chain of custody certificates
    certs, cid = [], 1
    for s in suppliers[:20]:
        for _ in range(r.randint(0, 3)):
            expiry = asof + timedelta(days=r.randint(-200, 700))
            st = "expired" if expiry < asof else r.choices(["valid", "revoked", "suspended"], [92, 4, 4])[0]
            certs.append({"cert_id": f"CERT-{cid:06d}", "supplier_id": s["supplier_id"],
                          "cert_type": r.choice(["recycled_content", "organic", "fair_trade", "sustainable", "conflict_mineral_free"]),
                          "issued_by": r.choice(["Control Union", "SGS", "TUV SUD", "Bureau Veritas", "Ecocert"]),
                          "scope": r.choice(["Facility-wide", "Cotton only", "Recycled polyester", "All materials"]),
                          "issued_date": expiry - timedelta(days=730), "expiry_date": expiry, "status": st,
                          "updated_at": d(r.randint(1, 60))})
            cid += 1

    # ---- ownership (shareholder rows), registry, screening, litigation, media
    ownership, registry, sanctions, litigation, media = [], [], [], [], []

    def own(eid, etype, ename, country, sh, shc, pct, sht, ubo, ubo_c, verified, src, vdate, notes=""):
        ownership.append({"entity_id": eid, "entity_type": etype, "entity_name": ename, "country": country,
                          "shareholder_name": sh, "shareholder_country": shc, "ownership_pct": pct, "shareholder_type": sht,
                          "beneficial_owner_name": ubo, "beneficial_owner_country": ubo_c, "verified": verified,
                          "verification_source": src, "verified_date": vdate, "notes": notes})

    surnames = [s["name"].split()[0] for s in suppliers]
    for s in suppliers:
        sid, nm, c = s["supplier_id"], s["name"], s["country"]
        fam = nm.split()[0]
        if sid == "SUP-0003":
            own(sid, "supplier", nm, c, "Bishop Holdings (HK) Ltd", "HK", 70, "company", "", "", False, "", "",
                "Holding company with nominee directors; individuals behind it not disclosed")
            own(sid, "supplier", nm, c, "Wei Bishop", c, 30, "individual", "Wei Bishop", c, True, "Company registry", d(200))
        elif r.random() < 0.3:
            own(sid, "supplier", nm, c, f"{fam} Family Holdings Ltd", c, 100, "company", f"{fam} family", c, r.random() < 0.85,
                "Company registry", d(r.randint(60, 400)), "Holding company wholly owned by the founding family")
        else:
            own(sid, "supplier", nm, c, f"{fam} family", c, 60, "individual", f"{fam} family", c, True, "Company registry + audit disclosure", d(r.randint(60, 400)))
            own(sid, "supplier", nm, c, f"{r.choice(surnames)} Investments Ltd", c, 40, "company", "Disclosed in filings", c, True, "Company registry", d(r.randint(60, 400)))
        # registry
        regno = f"{c}-{sid[-4:]}-{r.randint(100000, 999999)}"
        registry.append({"entity_id": sid, "entity_name": nm, "country": c, "registration_number": regno,
                         "registry_source": "National company registry", "legal_form": nm.split()[-1] if nm.split()[-1] in ("Ltd", "Co", "JSC", "Group") else "Limited company",
                         "registered_address": f"{s['name'].split()[0]} Industrial Park, {COUNTRY_NAMES[c]}",
                         "registration_date": asof - timedelta(days=r.randint(1500, 7000)),
                         "status": r.choices(["active", "inactive"], [96, 4])[0],
                         "directors_info": f"{fam} family directors on file", "verified_date": d(r.randint(30, 400)), "updated_at": d(r.randint(1, 30))})
        # sanctions screening
        for n, lst in enumerate(["OFAC", "UN", "UK", "EU"], 1):
            sanctions.append({"entity_id": sid, "screening_id": f"SCR-{sid[-4:]}-{n}", "entity_type": "supplier", "entity_name": nm,
                              "screening_date": d(r.randint(20, 120)), "sanctions_list": lst, "match_status": "no_match",
                              "description": f"No match on the {lst} list", "action_taken": "None", "updated_at": d(r.randint(1, 20))})
        # litigation
        if r.random() < 0.12:
            litigation.append({"entity_id": sid, "litigation_case_id": f"LIT-{sid[-4:]}-1", "entity_name": nm,
                               "case_type": r.choice(["commercial", "employment", "environmental"]),
                               "jurisdiction": COUNTRY_NAMES[c], "case_status": r.choice(["settled", "dismissed", "concluded"]),
                               "description": r.choice(["Contract dispute with a customer over delivery", "Former employee claim for notice pay",
                                                        "Local authority notice on effluent discharge"]),
                               "outcome": "Settled without admission", "case_date": d(r.randint(200, 900)), "updated_at": d(r.randint(30, 200))})
    # Brown Textiles litigation story (labour, settled)
    litigation.append({"entity_id": "SUP-0001", "litigation_case_id": "LIT-900001", "entity_name": sup["SUP-0001"]["name"], "case_type": "labour",
                       "jurisdiction": "China", "case_status": "settled", "description": "Workers' claim for unpaid overtime and wage theft at FAC-0001",
                       "outcome": "Settlement agreed; supplier paid back wages", "case_date": d(400), "updated_at": d(300)})

    for f in factories:
        s = sup.get(f["supplier_id"])
        registry.append({"entity_id": f["factory_id"], "entity_name": f["name"], "country": f["country"],
                         "registration_number": f"{f['country']}-FAC-{f['factory_id'][-4:]}", "registry_source": "Local industrial registry",
                         "legal_form": "Manufacturing unit", "registered_address": f"{f['city']}, {COUNTRY_NAMES[f['country']]}",
                         "registration_date": asof - timedelta(days=r.randint(1500, 7000)), "status": "active",
                         "directors_info": f"Operated by {s['name'] if s else f['supplier_id']}", "verified_date": d(r.randint(30, 400)),
                         "updated_at": d(r.randint(1, 30))})

    # Prospective supplier Sunrise Pack Co. Ltd (not in master) and related entities
    registry += [
        {"entity_id": "PSP-0001", "entity_name": "Sunrise Pack Co. Ltd", "country": "CN", "registration_number": "91441900MA4UXYZ12K",
         "registry_source": "National Enterprise Credit Information Publicity System (SAMR)", "legal_form": "Limited liability company",
         "registered_address": "Building 6, Songshan Lake Industrial Park, Dongguan, Guangdong", "registration_date": asof - timedelta(days=3300),
         "status": "active", "directors_info": "Legal representative Li Jun; directors Li Jun, Zhang Min", "verified_date": d(25), "updated_at": d(25)},
        {"entity_id": "PSP-0002", "entity_name": "Sunrise Trading (HK) Limited", "country": "HK", "registration_number": "HK-2145877",
         "registry_source": "Hong Kong Companies Registry", "legal_form": "Private company limited by shares",
         "registered_address": "Unit 1203, Harbour Commercial Building, Kowloon, Hong Kong", "registration_date": asof - timedelta(days=2900),
         "status": "active", "directors_info": "Director Li Jun (same person as Sunrise Pack legal representative)", "verified_date": d(25), "updated_at": d(25)},
        {"entity_id": "PSP-0003", "entity_name": "Pearl River Holdings Ltd", "country": "VG", "registration_number": "VG-1893340",
         "registry_source": "BVI Registry of Corporate Affairs", "legal_form": "BVI business company",
         "registered_address": "Registered agent address, Road Town, Tortola, British Virgin Islands", "registration_date": asof - timedelta(days=1500),
         "status": "active", "directors_info": "Nominee directors supplied by registered agent; no public record of beneficial owners", "verified_date": d(25), "updated_at": d(25)}]
    own("PSP-0001", "prospect", "Sunrise Pack Co. Ltd", "CN", "Sunrise Trading (HK) Limited", "HK", 60, "company", "Li Jun", "CN", True,
        "Hong Kong Companies Registry", d(25), "Hong Kong parent; payment account is held in the name of this parent")
    own("PSP-0001", "prospect", "Sunrise Pack Co. Ltd", "CN", "Pearl River Holdings Ltd", "VG", 40, "company", "", "", False, "", "",
        "British Virgin Islands holding company; nominee directors; beneficial owner not disclosed")
    own("PSP-0002", "prospect", "Sunrise Trading (HK) Limited", "HK", "Li Jun", "CN", 100, "individual", "Li Jun", "CN", True, "Hong Kong Companies Registry", d(25))
    own("PSP-0003", "prospect", "Pearl River Holdings Ltd", "VG", "Nominee shareholder (registered agent)", "VG", 100, "company", "", "", False, "", "",
        "Shares held by a nominee for an undisclosed principal")
    for eid, nm in (("PSP-0001", "Sunrise Pack Co. Ltd"), ("PSP-0002", "Sunrise Trading (HK) Limited"), ("PSP-0003", "Pearl River Holdings Ltd")):
        for n, lst in enumerate(["OFAC", "UN", "UK", "EU"], 1):
            possible = eid == "PSP-0003" and lst == "UK"
            sanctions.append({"entity_id": eid, "screening_id": f"SCR-{eid[-4:]}-{n}", "entity_type": "prospect", "entity_name": nm,
                              "screening_date": d(3), "sanctions_list": lst, "match_status": "possible_match" if possible else "no_match",
                              "description": "Name similar to a UK-listed entity; beneficial owner not disclosed so the match cannot be cleared" if possible
                              else f"No match on the {lst} list", "action_taken": "Refer to compliance for manual review" if possible else "None",
                              "updated_at": d(3)})
    litigation += [
        {"entity_id": "PSP-0001", "litigation_case_id": "LIT-900002", "entity_name": "Sunrise Pack Co. Ltd", "case_type": "commercial",
         "jurisdiction": "China", "case_status": "settled", "description": "Customer contract dispute over late delivery of cosmetic cartons",
         "outcome": "Settled; supplier paid agreed compensation", "case_date": d(500), "updated_at": d(420)},
        {"entity_id": "PSP-0001", "litigation_case_id": "LIT-900003", "entity_name": "Sunrise Pack Co. Ltd", "case_type": "labour",
         "jurisdiction": "China", "case_status": "active", "description": "Labour arbitration claim by former workers over unpaid overtime",
         "outcome": "", "case_date": d(150), "updated_at": d(40)}]

    def med(n, eid, etype, ename, head, src, content, ago, sev, cred, ver):
        media.append({"entity_id": eid, "record_id": f"MED-9{n:05d}", "entity_type": etype, "entity_name": ename, "headline": head,
                      "source": src, "content": content, "published_date": d(ago), "severity": sev, "credibility": cred, "verified": ver,
                      "found_at": d(max(ago - 2, 0)), "updated_at": d(max(ago - 2, 0))})

    n = 1
    mill = "Jackson Knitting 35"
    med(n, "FAC-0035", "factory", mill, "Debt bondage alleged at Tamil Nadu spinning mill", "International Labour News Network",
        "Article based on interviews with 14 current and former workers alleges migrant workers are recruited through agents who advance fees then deduct repayments from wages; the mill declined to comment and the NGO report it cites is unpublished.", 21, "high", "medium", False); n += 1
    med(n, "FAC-0035", "factory", mill, "NGO investigation finds recruitment-fee debt bondage in Tiruppur-area spinning mills", "Southern Workers Rights Forum",
        "NGO field investigation found workers repaying recruitment advances through wage deductions and identity documents held by recruiters; findings consistent with the press article and with ILO indicators of forced labour.", 35, "critical", "high", True); n += 1
    med(n, "FAC-0035", "factory", mill, "ILO notes bonded labour risk in Tamil Nadu spinning mills", "ILO",
        "Sector-level report documenting recruitment debt in Tamil Nadu spinning mills; does not name this mill.", 160, "medium", "high", True); n += 1
    mill87 = "Khan Plant 87"
    med(n, "FAC-0087", "factory", mill87, "Workers describe forced overtime at Indian garment factory", "BBC",
        "Named workers say refusal to work overtime leads to lost bonuses and threats of dismissal; the factory supplies UK retailers.", 20, "high", "high", True); n += 1
    med(n, "FAC-0087", "factory", mill87, "Union claims unpaid wages at garment factory", "Local union bulletin",
        "Union bulletin claims two weeks of wages were withheld; no response from management and no independent verification.", 75, "medium", "medium", False); n += 1
    med(n, "FAC-0087", "factory", mill87, "Social media post alleges child workers at factory", "Social media post",
        "Anonymous post with no evidence or named source alleging child workers; not corroborated by audits.", 400, "low", "low", False); n += 1
    med(n, "SUP-0001", "supplier", sup["SUP-0001"]["name"], "Retailers' cotton traced to Xinjiang ginneries", "Reuters",
        "Investigation traced cotton in several apparel supply chains to Aksu ginneries in Xinjiang; Brown Textiles named among suppliers.", 60, "high", "high", True); n += 1
    med(n, "SUP-0027", "supplier", sup["SUP-0027"]["name"], "Xinjiang polysilicon link to electricals makers", "Industry research",
        "Report links Xinjiang polysilicon producers to consumer electricals supply chains; Arnold Industries listed as a buyer.", 90, "high", "medium", True); n += 1
    med(n, "SUP-0002", "supplier", sup["SUP-0002"]["name"], "Debt bondage claims at Vietnamese garment factory", "Fair Labor Association",
        "Association report on recruitment fees at FAC-0003, supplier Harris Manufacturing.", 25, "high", "high", True); n += 1
    med(n, "PSP-0001", "prospect", "Sunrise Pack Co. Ltd", "Dongguan packaging maker fined over wastewater discharge", "Dongguan Daily",
        "Local regulator fined Sunrise Pack Co. Ltd for exceeding wastewater discharge limits at its print plant; the company said it has fixed the treatment plant.", 87, "medium", "medium", True); n += 1
    med(n, "PSP-0001", "prospect", "Sunrise Pack Co. Ltd", "Forum post alleges unpaid overtime at Sunrise Pack", "Anonymous forum post",
        "Anonymous post claims workers were not paid overtime; no named source and no corroboration.", 45, "low", "low", False); n += 1
    med(n, "PSP-0003", "prospect", "Pearl River Holdings Ltd", "BVI shell companies used to hide Chinese manufacturers' owners", "Offshore leaks reporting",
        "Reporting on BVI holding companies with nominee directors used by Guangdong manufacturers; Pearl River Holdings is named in the dataset but without allegations.", 110, "low", "medium", False); n += 1
    med(n, "SUP-0028", "supplier", sup["SUP-0028"]["name"], "Savage Products reported to be missing payments to lenders", "Trade finance press",
        "Trade finance press reports Savage Products has delayed repayments to two lenders and is seeking to renegotiate its credit facilities; the company has not commented.", 30, "high", "medium", False); n += 1
    med(n, "SUP-0065", "supplier", sup["SUP-0065"]["name"], "Smith Products cuts shifts as merino orders fall", "Textile industry weekly",
        "Industry weekly reports Smith Products has cut shifts at its knitting plant and delayed supplier payments after a fall in orders; management says it expects recovery.", 50, "medium", "medium", True); n += 1
    for s in suppliers:
        if s["supplier_id"] in ("SUP-0001", "SUP-0027", "SUP-0002") or r.random() > 0.08:
            continue
        med(n, s["supplier_id"], "supplier", s["name"], f"Environmental complaint near {s['name'].split()[0]} site", "Local news",
            "Local complaint about noise and discharge; regulator inspection found no breach.", r.randint(40, 170), "low", "medium", True); n += 1

    # ---- traceability evidence
    trace = []

    def tr(sid, i, et, mat, origin, conf, ago, notes=""):
        trace.append({"supplier_id": sid, "evidence_id": f"TR-{sid[-4:]}-{i:02d}", "evidence_type": et, "material_or_product": mat,
                      "origin": origin, "confidence_level": conf, "evidence_date": d(ago), "notes": notes, "updated_at": d(max(ago - 1, 0))})

    tr("SUP-0001", 1, "document_trail", "Cotton", "Xinjiang, China", "low", 40, "Supplier declaration only; no ginnery lot codes or isotope testing")
    tr("SUP-0001", 2, "test_result", "Polyester", "Zhejiang, China", "high", 90, "Chip origin certificates held")
    tr("SUP-0003", 1, "document_trail", "Cotton", "Xinjiang, China", "low", 50, "Mass-balance claim; no tracing beyond tier one")
    tr("SUP-0057", 1, "batch_tracking", "Cotton", "Xinjiang, China", "medium", 45, "Batch records to ginnery cluster; ginnery names withheld")
    tr("SUP-0057", 2, "lot_code", "Viscose", "Shandong, China", "high", 100, "")
    tr("SUP-0027", 1, "document_trail", "Polysilicon", "Xinjiang, China", "low", 30, "Declared from Xinjiang producers; no tracing beyond tier one")
    tr("SUP-0027", 2, "lot_code", "Copper", "Jiangxi, China", "high", 120, "")
    tr("SUP-0041", 1, "lot_code", "Polysilicon", "Sichuan, China", "high", 80, "Producer named and audited")
    tr("SUP-0034", 1, "lot_code", "Polysilicon", "Jiangsu, China", "high", 85, "Producer named and audited")
    tr("SUP-0018", 1, "batch_tracking", "Cotton yarn", "Tamil Nadu, India", "medium", 60, "Spun at own mill FAC-0035")
    planted_t = {x["supplier_id"] for x in trace}
    for s in suppliers:
        if s["supplier_id"] in planted_t or r.random() < 0.5:
            continue
        tr(s["supplier_id"], 1, r.choice(["lot_code", "batch_tracking", "inspection_cert"]), MATERIAL[s["category_focus"]],
           COUNTRY_NAMES[s["country"]] if s["country"] not in ("CN",) else "Zhejiang, China", r.choices(["medium", "high", "very_high"], [20, 50, 30])[0], r.randint(30, 200))

    # ---- tier mapping by country
    tier_rows = []
    for s in suppliers:
        sid, c, cat = s["supplier_id"], s["country"], s["category_focus"]
        facs = fac_by_sup.get(sid, [])
        tier_rows.append({"supplier_id": sid, "country": c, "tier": 1, "factory_count": len(facs),
                          "worker_count": sum(int(f["workers"]) for f in facs), "mapped_pct": 100, "updated_at": d(r.randint(1, 60))})
        near = {"PL": "DE", "PT": "IT", "IT": "FR", "DE": "PL", "FR": "DE", "GB": "FR", "TR": "IT", "MX": "MX"}.get(c, c)
        tier_rows.append({"supplier_id": sid, "country": c, "tier": 2, "factory_count": r.randint(1, 4), "worker_count": r.randint(150, 2500),
                          "mapped_pct": r.randint(70, 95), "updated_at": d(r.randint(1, 60))})
        if near != c:
            tier_rows.append({"supplier_id": sid, "country": near, "tier": 2, "factory_count": r.randint(1, 3), "worker_count": r.randint(100, 900),
                              "mapped_pct": r.randint(60, 90), "updated_at": d(r.randint(1, 60))})
        for oc in TIER3[cat]:
            tier_rows.append({"supplier_id": sid, "country": oc, "tier": 3, "factory_count": r.randint(2, 8), "worker_count": r.randint(300, 4000),
                              "mapped_pct": r.randint(15, 55), "updated_at": d(r.randint(1, 60))})
    fixed = {("SUP-0040", "PL", 2): 92, ("SUP-0040", "CN", 3): 30, ("SUP-0040", "IN", 3): 25,
             ("SUP-0054", "PL", 2): 85, ("SUP-0054", "CN", 3): 20, ("SUP-0054", "IN", 3): 15,
             ("SUP-0068", "PL", 2): 78, ("SUP-0068", "CN", 3): 10, ("SUP-0068", "IN", 3): 10,
             ("SUP-0001", "CN", 3): 15, ("SUP-0001", "IN", 3): 40}
    for row in tier_rows:
        k = (row["supplier_id"], row["country"], row["tier"])
        if k in fixed:
            row["mapped_pct"] = fixed[k]
    for row in tier_rows:  # a nearshore supplier's tier-2 partner in Germany
        if row["supplier_id"] in ("SUP-0040", "SUP-0054", "SUP-0068") and row["country"] == "DE":
            row["mapped_pct"] = 80

    # ---- mapping gaps
    gaps = [
        ("GAP-0001", "Cotton textiles", 3, "CN", "Xinjiang", 240000, "Cotton origin declared only at supplier level; no ginnery or lot-level tracing", "Commission cotton origin audit and isotope testing; require ginnery lists from SUP-0001, SUP-0003 and SUP-0057", "high", 85000),
        ("GAP-0002", "Cotton textiles", 2, "CN", "Guangdong and Zhejiang", 150000, "Spinning and weaving mills not named by suppliers", "Require named tier 2 mill lists with site visits", "high", 40000),
        ("GAP-0003", "Polysilicon electricals", 3, "CN", "Xinjiang", 60000, "Polysilicon producer not disclosed by SUP-0027", "Require producer names and chain-of-custody evidence", "high", 55000),
        ("GAP-0004", "Cotton textiles", 2, "IN", "Tamil Nadu", 120000, "Spinning mills and labour agents not mapped", "Map spinning mills and recruiters; include FAC-0035 in field verification", "high", 30000),
        ("GAP-0005", "Cotton textiles", 3, "IN", "Gujarat and Maharashtra", 70000, "Ginneries and traders unknown", "Engage cotton trader to map ginneries", "medium", 28000),
        ("GAP-0006", "Dyed textiles", 2, "BD", "Dhaka and Chattogram", 60000, "Dye houses subcontracted without notice", "Commission mapping audit of the top 5 dyers", "medium", 18000),
        ("GAP-0007", "Garments", 2, "VN", "Ho Chi Minh City", 45000, "Subcontracted sewing units", "Unannounced visits to identify subcontractors", "medium", 18000),
        ("GAP-0008", "Polyester fabrics", 3, "CN", "Zhejiang", 85000, "Chip and polymer producers not mapped", "Collect polymer producer certificates", "medium", 35000),
        ("GAP-0009", "Beauty packaging", 3, "CN", "Guangdong", 30000, "Packaging resin sources unknown", "Request resin supplier declarations", "low", 12000),
        ("GAP-0010", "Accessories", 2, "TR", "Istanbul", 25000, "Leather tanneries not named", "Request tannery list", "low", 9000)]
    gap_rows = [{"gap_id": a, "product_category": b, "tier_level": t, "country": c, "region": reg, "unit_volume_annual": u, "gap_reason": gr,
                 "remediation_plan": rp, "priority": pr, "est_cost_gbp": cost, "updated_at": d(r.randint(5, 40))}
                for a, b, t, c, reg, u, gr, rp, pr, cost in gaps]

    # ---- supplier documents
    docs, did = [], 1
    for s in suppliers:
        sid = s["supplier_id"]
        st = status_of[sid]
        for jur, names in (("EU", EU_DOCS), ("UK", UK_DOCS)):
            for k, name in enumerate(names):
                if st == "complete":
                    status = "verified" if r.random() < 0.85 else "received"
                elif st == "in_progress":
                    status = r.choice(["verified", "received", "pending", "pending"])
                else:
                    status = "pending"
                if sid == "SUP-0040" and name in ("Tier 2+ supplier list", "Grievance mechanism evidence"):
                    status = "pending"
                due = asof + timedelta(days=r.randint(14, 90)) if status == "pending" else asof - timedelta(days=r.randint(5, 90))
                docs.append({"doc_requirement_id": f"DREQ-{did:06d}", "supplier_id": sid, "jurisdiction": jur, "document_type": name,
                             "description": f"{name} needed to evidence due diligence under {'EU CSDDD' if jur == 'EU' else 'UK Modern Slavery Act'}",
                             "required_by_date": due, "status": status, "updated_at": d(r.randint(1, 30))})
                did += 1

    # ---- cases and tasks
    cases = [
        ("CASE-900001", "audit_finding", "SUP-0002", "FAC-0003", "Critical audit findings: debt bondage in recruitment and underage workers", "investigating", "critical", 20),
        ("CASE-900002", "periodic_review", "SUP-0001", "FAC-0001", "Xinjiang cotton origin tracing and UFLPA readiness", "open", "high", 30),
        ("CASE-900003", "periodic_review", "SUP-0003", "", "Xinjiang cotton origin and opaque ownership", "open", "high", 28),
        ("CASE-900004", "audit_finding", "SUP-0046", "FAC-0087", "Audit rating D and adverse media on working conditions", "open", "high", 17)]
    case_rows = [{"case_id": a, "case_type": b, "supplier_id": c, "factory_id": f, "description": desc, "status": st, "risk_rating": rr,
                  "created_at": d(ago), "assigned_to": f"EMP-0000{(i % 5) + 1}", "updated_at": d(max(ago - 5, 0))}
                 for i, (a, b, c, f, desc, st, rr, ago) in enumerate(cases)]
    tasks = [
        ("TASK-900001", "CASE-900002", "SUP-0001", "CN", "Obtain ginnery list and lot-level tracing for Xinjiang cotton", "evidence_collection", "in_progress", 14),
        ("TASK-900002", "CASE-900002", "SUP-0001", "CN", "Commission cotton origin audit", "audit", "open", 28),
        ("TASK-900003", "CASE-900001", "SUP-0002", "VN", "Develop remediation plan for recruitment fees at FAC-0003", "remediation_plan", "open", 21),
        ("TASK-900004", "CASE-900003", "SUP-0003", "CN", "Obtain beneficial ownership declaration", "legal_review", "open", 14)]
    task_rows = [{"task_id": a, "case_id": b, "supplier_id": c, "country": co, "description": desc, "task_type": tt, "status": st,
                  "assigned_to": f"EMP-0000{(i % 5) + 1}", "due_date": asof + timedelta(days=due), "created_at": d(10), "updated_at": d(2)}
                 for i, (a, b, c, co, desc, tt, st, due) in enumerate(tasks)]

    return {
        "due_diligence_cases": case_rows, "due_diligence_tasks": task_rows, "supplier_risk_ratings": ratings,
        "risk_evidence": evidence, "factory_profiles": profiles, "supply_chain_mapping": mapping,
        "compliance_requirements": reqs, "compliance_evidence_inventory": inventory, "chain_of_custody_certificates": certs,
        "worker_grievances": grievances, "country_risk_indices": country_indices, "supplier_sub_tier_relationships": sub_tiers,
        "ownership_structures": ownership, "supplier_traceability_evidence": trace, "tier_mapping_by_country": tier_rows,
        "supply_chain_mapping_gaps": gap_rows, "adverse_media_records": media, "sanctions_screening_records": sanctions,
        "litigation_records": litigation, "supplier_document_requirements": docs, "company_registry": registry,
    }
