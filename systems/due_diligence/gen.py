"""Generate due diligence data: cases, tasks, risk ratings, evidence, factory profiles, compliance gaps."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    suppliers = g.master("suppliers")
    factories = g.master("factories")
    employees = g.master("employees")

    cases = []
    tasks = []
    supplier_risks = []
    risk_evidence = []
    factory_profs = []
    mapping = []
    compliance_reqs = []
    compliance_evidence = []
    certs = []
    grievances = []
    country_indices = []
    sub_tiers = []
    ownership = []
    traceability = []
    tier_mapping = []
    mapping_gaps = []
    audit_findings = []
    corrective_actions = []
    regulatory = []
    adverse_media = []
    sanctions = []
    litigation = []
    supplier_doc_requirements = []
    company_registry = []

    # Country risk indices
    countries = ["IN", "BD", "CN", "PK", "VN", "TH", "KH", "MX", "TN", "ET"]
    for country in countries:
        country_indices.append({
            "country": country,
            "country_name": {"IN": "India", "BD": "Bangladesh", "CN": "China", "PK": "Pakistan",
                           "VN": "Vietnam", "TH": "Thailand", "KH": "Cambodia", "MX": "Mexico",
                           "TN": "Tunisia", "ET": "Ethiopia"}.get(country, country),
            "forced_labour_index": r.uniform(0.4, 0.9),
            "human_rights_score": r.uniform(20, 60),
            "legal_environment": r.uniform(30, 75),
            "enforcement_level": r.uniform(20, 70),
            "corruption_index": r.uniform(30, 75),
            "sourcing_volume_units": r.randint(50000, 500000),
            "updated_at": g.as_of - timedelta(days=r.randint(1, 90)),
        })

    # Generate supplier risk ratings and evidence
    for idx, supplier in enumerate(suppliers[:30]):
        supplier_id = supplier["supplier_id"]
        country = supplier.get("country", "IN")

        risk_level = r.choices(["low", "medium", "high", "critical"], [30, 40, 25, 5])[0]

        supplier_risks.append({
            "supplier_id": supplier_id,
            "forced_labour_risk": risk_level,
            "compliance_risk": r.choices(["low", "medium", "high", "critical"], [35, 35, 25, 5])[0],
            "financial_risk": r.choices(["low", "medium", "high"], [50, 35, 15])[0],
            "overall_risk": risk_level,
            "due_diligence_status": r.choices(["not_started", "in_progress", "complete", "escalated"], [20, 40, 30, 10])[0],
            "last_assessed_at": g.date_between(180, 0),
            "next_review_date": g.as_of + timedelta(days=r.randint(30, 180)),
            "updated_at": g.as_of - timedelta(days=r.randint(1, 60)),
        })

        # Generate risk evidence
        evidence_types = ["audit_finding", "worker_interview", "grievance_record", "media_report", "ngo_report"]
        categories = ["forced_labour", "child_labour", "health_safety", "wages_hours", "freedom_association"]
        for _ in range(r.randint(1, 4)):
            risk_evidence.append({
                "supplier_id": supplier_id,
                "evidence_id": f"EV-{idx:04d}-{r.randint(1,9999):04d}",
                "risk_category": r.choice(categories),
                "evidence_type": r.choice(evidence_types),
                "description": r.choice([
                    "Worker reported excessive overtime without compensation",
                    "No functional grievance mechanism found during audit",
                    "Wage calculations unclear and below minimum wage",
                    "Migrant workers unable to keep ID documents",
                    "Subcontracted workers at facility without agreement"
                ]),
                "risk_level": r.choices(["low", "medium", "high", "critical"], [20, 35, 35, 10])[0],
                "credibility": r.choices(["unverified", "partially_verified", "verified", "highly_verified"], [10, 20, 40, 30])[0],
                "source": r.choice(["Audit report", "NGO investigation", "Worker hotline", "News report", "Whistleblower"]),
                "found_at": g.date_between(180, 1),
                "updated_at": g.as_of - timedelta(days=r.randint(1, 60)),
            })

    # Generate due diligence cases
    case_id = 1
    for supplier in suppliers[:15]:
        num_cases = r.randint(0, 2)
        for _ in range(num_cases):
            assigned_emp = r.choice([e["employee_id"] for e in employees])
            cases.append({
                "case_id": f"CASE-{case_id:06d}",
                "case_type": r.choice(["allegation", "onboarding", "audit_finding", "periodic_review"]),
                "supplier_id": supplier["supplier_id"],
                "factory_id": r.choice([f["factory_id"] for f in factories if f["supplier_id"] == supplier["supplier_id"]])
                               if any(f["supplier_id"] == supplier["supplier_id"] for f in factories) else None,
                "description": r.choice([
                    "Forced labour allegation from Tamil Nadu mill",
                    "Underage workers found during audit",
                    "Excessive overtime and wage violations",
                    "No freedom of association provisions",
                    "Migrant workers subject to debt bondage"
                ]),
                "status": r.choices(["open", "investigating", "remediation", "closed"], [20, 40, 30, 10])[0],
                "risk_rating": r.choices(["low", "medium", "high", "critical"], [10, 25, 40, 25])[0],
                "created_at": g.date_between(180, 1),
                "assigned_to": assigned_emp,
                "updated_at": g.as_of - timedelta(days=r.randint(1, 90)),
            })
            case_id += 1

    # Generate tasks
    task_id = 1
    for case in cases[:20]:
        num_tasks = r.randint(1, 3)
        for _ in range(num_tasks):
            assigned_emp = r.choice([e["employee_id"] for e in employees])
            tasks.append({
                "task_id": f"TASK-{task_id:06d}",
                "case_id": case["case_id"],
                "description": r.choice([
                    "Map all sub-tier suppliers",
                    "Conduct factory audit",
                    "Collect worker interviews",
                    "Review compliance certifications",
                    "Develop remediation plan"
                ]),
                "task_type": r.choice(["mapping", "audit", "evidence_collection", "legal_review", "remediation_plan"]),
                "status": r.choices(["open", "in_progress", "completed", "blocked"], [30, 40, 20, 10])[0],
                "assigned_to": assigned_emp,
                "due_date": g.as_of + timedelta(days=r.randint(7, 90)),
                "created_at": case["created_at"],
                "updated_at": g.as_of - timedelta(days=r.randint(1, 60)),
            })
            task_id += 1

    # Generate factory profiles - use valid countries only
    valid_countries = ["IN", "BD", "CN", "PK", "VN", "TH", "KH", "MX", "TN", "ET"]
    for factory in factories[:30]:
        factory_profs.append({
            "factory_id": factory["factory_id"],
            "name": factory["name"],
            "supplier_id": factory["supplier_id"],
            "country": r.choice(valid_countries),  # Override with valid country
            "city": factory["city"],
            "latitude": float(factory.get("latitude", r.uniform(-30, 30))),
            "longitude": float(factory.get("longitude", r.uniform(-180, 180))),
            "product_types": r.choice(["Cotton yarn; woven cotton", "Synthetic fabric; dyed textiles", "Polyester threads", "Knitted garments"]),
            "capacity_units_month": factory["capacity_units_month"],
            "workers": factory["workers"],
            "certifications": r.choice(["SMETA; BSCI; ISO14001", "SA8000; FSC", "OEKO-TEX", "Fair Trade Certified"]),
            "last_audit_date": g.date_between(365, 1),
            "audit_rating": r.choices(["A", "B", "C", "D"], [40, 35, 20, 5])[0],
            "remediation_status": r.choices(["compliant", "in_remediation", "non_compliant"], [60, 30, 10])[0],
            "grievance_mechanism": r.choice([True, False]),
            "updated_at": g.as_of - timedelta(days=r.randint(1, 60)),
        })

    # Supply chain mapping (only for seeded factories)
    products = g.master("products")
    seeded_factory_ids = set(f["factory_id"] for f in factory_profs)
    for fac in factory_profs[:10]:
        # Use only a couple of products for mapping
        for product in r.sample(products, min(3, len(products))):
            mapping.append({
                "product_sku": product["sku"],
                "tier": 1,
                "factory_id": fac["factory_id"],
                "supplier_id": fac["supplier_id"],
                "mapped_at": g.date_between(180, 1),
                "mapping_status": r.choices(["mapped", "partially_mapped", "unmapped"], [70, 20, 10])[0],
                "material_flow": r.choice(["Raw cotton", "Yarn", "Woven fabric", "Dyed goods"]),
                "updated_at": g.as_of - timedelta(days=r.randint(1, 90)),
            })

    # Compliance requirements by jurisdiction
    jurisdictions = ["UK", "EU", "US", "CA"]
    regulations = {
        "UK": ["UK Modern Slavery Act 2015", "Environment Act 2021"],
        "EU": ["EU Due Diligence Directive", "CSDDD"],
        "US": ["US Uyghur Forced Labor Prevention Act", "Dodd-Frank Act"],
        "CA": ["Canadian Supply Chain Act"]
    }
    req_id = 1
    for jurisdiction in jurisdictions:
        for reg in regulations.get(jurisdiction, []):
            compliance_reqs.append({
                "requirement_id": f"REQ-{req_id:04d}",
                "jurisdiction": jurisdiction,
                "regulation": reg,
                "topic": r.choice(["forced_labour", "due_diligence", "supply_chain_transparency"]),
                "requirement_text": f"Must conduct due diligence and report on forced labour risks in {jurisdiction}",
                "applicability": "Companies with turnover > £36M or employees > 250",
                "effective_date": g.as_of - timedelta(days=r.randint(1, 365)),
                "penalties": "Up to £20M fine or 10% of revenue",
                "updated_at": g.as_of - timedelta(days=r.randint(1, 60)),
            })
            req_id += 1

    # Compliance evidence inventory
    for supplier in suppliers[:15]:
        for req in compliance_reqs[:10]:
            compliance_evidence.append({
                "supplier_id": supplier["supplier_id"],
                "requirement_id": req["requirement_id"],
                "evidence_held": r.choice([True, False]),
                "evidence_type": r.choice(["policy", "audit", "certification", "test", "document"]),
                "evidence_date": g.date_between(365, 1) if r.choice([True, False]) else None,
                "gap_description": "Missing audit report for last 2 years" if not r.choice([True, False]) else None,
                "priority": r.choices(["high", "medium", "low"], [20, 40, 40])[0],
                "updated_at": g.as_of - timedelta(days=r.randint(1, 60)),
            })

    # Chain of custody certificates
    cert_id = 1
    cert_types = ["recycled_content", "organic", "fair_trade", "sustainable", "conflict_mineral_free"]
    for supplier in suppliers[:20]:
        for _ in range(r.randint(0, 3)):
            certs.append({
                "cert_id": f"CERT-{cert_id:06d}",
                "supplier_id": supplier["supplier_id"],
                "cert_type": r.choice(cert_types),
                "issued_by": r.choice(["Control Union", "SGS", "TÜV SÜD", "Bureau Veritas", "Ecocert"]),
                "scope": r.choice(["Facility-wide", "Cotton only", "Recycled polyester", "All materials"]),
                "issued_date": g.date_between(365, 90),
                "expiry_date": g.as_of + timedelta(days=r.randint(1, 730)),
                "status": r.choices(["valid", "expired", "revoked"], [80, 15, 5])[0],
                "updated_at": g.as_of - timedelta(days=r.randint(1, 60)),
            })
            cert_id += 1

    # Worker grievances
    grievance_id = 1
    for factory in factories[:20]:
        for _ in range(r.randint(0, 3)):
            grievances.append({
                "grievance_id": f"GRV-{grievance_id:06d}",
                "factory_id": factory["factory_id"],
                "supplier_id": factory["supplier_id"],
                "grievance_date": g.date_between(180, 1),
                "category": r.choice(["wages", "hours", "safety", "discrimination", "freedom_association"]),
                "description": r.choice([
                    "Wages not paid on time",
                    "Excessive overtime without consent",
                    "Unsafe working conditions",
                    "Discriminatory treatment",
                    "Denial of union access"
                ]),
                "remediation_status": r.choices(["open", "investigating", "resolved", "closed"], [15, 35, 35, 15])[0],
                "resolution_notes": "Pending investigation" if r.choice([True, False]) else "Resolved through management discussion",
                "updated_at": g.as_of - timedelta(days=r.randint(1, 90)),
            })
            grievance_id += 1

    # Supplier sub-tier relationships - avoid duplicates
    seen_sub_tiers = set()
    for supplier in suppliers[:20]:
        # Link to random sub-tier suppliers, max 2 per supplier
        for sub_sup in r.sample(suppliers[:30], min(2, len(suppliers))):
            if sub_sup["supplier_id"] != supplier["supplier_id"]:
                key = (supplier["supplier_id"], sub_sup["supplier_id"])
                if key not in seen_sub_tiers:
                    seen_sub_tiers.add(key)
                    sub_tiers.append({
                        "supplier_id": supplier["supplier_id"],
                        "sub_tier_supplier_id": sub_sup["supplier_id"],
                        "factory_id": None,
                        "material_flow": r.choice(["Raw cotton", "Yarn", "Dyes", "Buttons"]),
                        "relationship_type": r.choice(["raw_material", "component", "contract_manufacturing"]),
                        "mapped_date": g.date_between(180, 1),
                        "updated_at": g.as_of - timedelta(days=r.randint(1, 90)),
                    })

    # Ownership structures - use valid countries only
    valid_countries = ["IN", "BD", "CN", "PK", "VN", "TH", "KH", "MX", "TN", "ET"]
    for supplier in suppliers[:20]:
        ownership.append({
            "entity_id": supplier["supplier_id"],
            "entity_type": "supplier",
            "entity_name": supplier["name"],
            "country": r.choice(valid_countries),  # Override with valid country
            "parent_entity_id": None,
            "beneficial_owner_name": supplier["name"],
            "beneficial_owner_country": r.choice(valid_countries),  # Override with valid country
            "ownership_structure_description": "Single family-owned entity" if r.choice([True, False]) else "Part of larger manufacturing group",
            "verified": r.choice([True, False]),
            "verification_source": "Company registry" if r.choice([True, False]) else "Audit disclosure",
            "verified_date": g.date_between(365, 1) if r.choice([True, False]) else None,
            "updated_at": g.as_of - timedelta(days=r.randint(1, 60)),
        })

    # Traceability evidence
    for supplier in suppliers[:20]:
        for _ in range(r.randint(0, 2)):
            traceability.append({
                "supplier_id": supplier["supplier_id"],
                "evidence_id": f"TR-{r.randint(1,99999):05d}",
                "evidence_type": r.choice(["blockchain_record", "batch_tracking", "lot_code", "inspection_cert"]),
                "material_or_product": r.choice(["Cotton", "Polyester", "Dyed fabric", "Finished garment"]),
                "origin": r.choice(["Tamil Nadu, India", "Bangladesh", "Vietnam", "Mexico"]),
                "confidence_level": r.choices(["low", "medium", "high", "very_high"], [10, 20, 40, 30])[0],
                "evidence_date": g.date_between(180, 1),
                "updated_at": g.as_of - timedelta(days=r.randint(1, 60)),
            })

    # Tier mapping by country
    for supplier in suppliers[:15]:
        for country in ["IN", "BD", "CN", "VN"]:
            tier_mapping.append({
                "supplier_id": supplier["supplier_id"],
                "country": country,
                "tier": 1,
                "factory_count": r.randint(1, 5),
                "worker_count": r.randint(100, 5000),
                "mapped_pct": r.randint(30, 100),
                "updated_at": g.as_of - timedelta(days=r.randint(1, 90)),
            })

    # Supply chain mapping gaps
    gap_id = 1
    for product in products[:10]:
        mapping_gaps.append({
            "gap_id": f"GAP-{gap_id:04d}",
            "product_category": product.get("category", "Textiles"),
            "tier_level": r.randint(2, 4),
            "country": r.choice(["IN", "BD", "VN", "PK"]),
            "unit_volume_annual": r.randint(10000, 100000),
            "gap_reason": r.choice(["Supplier not cooperative", "Remote location", "Subcontracting complexity"]),
            "remediation_plan": "Hire local mapper to conduct field visits and establish direct relationships",
            "priority": r.choices(["high", "medium", "low"], [30, 40, 30])[0],
            "updated_at": g.as_of - timedelta(days=r.randint(1, 90)),
        })
        gap_id += 1

    # Generate realistic audit findings
    finding_id = 1
    for factory in factories[:15]:
        for _ in range(r.randint(0, 2)):
            audit_findings.append({
                "finding_id": f"FND-{finding_id:06d}",
                "factory_id": factory["factory_id"],
                "supplier_id": factory["supplier_id"],
                "audit_date": g.date_between(365, 30),
                "category": r.choice(["forced_labour", "child_labour", "wages", "hours", "safety", "health"]),
                "severity": r.choices(["observation", "minor", "major", "critical"], [20, 30, 35, 15])[0],
                "description": r.choice([
                    "Absence of freely chosen employment agreements signed by workers",
                    "Incomplete wage records and undisclosed deductions",
                    "Excessive overtime exceeding legal limits without compensation",
                    "Poor ventilation and lack of PPE in dye house",
                    "Limited grievance mechanism access for migrant workers"
                ]),
                "remediation_required": r.choice([True, True, False]),
                "corrective_action_id": None,
                "updated_at": g.as_of - timedelta(days=r.randint(1, 60)),
            })
            finding_id += 1

    # Generate realistic corrective action plans
    action_id = 1
    for finding in audit_findings[:20]:
        if finding["remediation_required"]:
            corrective_actions.append({
                "action_id": f"ACT-{action_id:06d}",
                "factory_id": finding["factory_id"],
                "audit_finding_id": finding["finding_id"],
                "issue_description": finding["description"],
                "action_plan": r.choice([
                    "Implement transparent wage structure and provide worker training",
                    "Install air quality monitoring and upgrade ventilation systems",
                    "Establish independent grievance committee with worker representation",
                    "Conduct legal audit of employment contracts and overtime policies"
                ]),
                "responsible_party": r.choice([e["employee_id"] for e in employees]) if employees else "EMP-0001",
                "target_date": g.as_of + timedelta(days=r.randint(30, 180)),
                "status": r.choices(["not_started", "in_progress", "completed", "verification_pending"], [10, 40, 30, 20])[0],
                "verification_date": g.date_between(60, 0) if r.choice([True, False]) else None,
                "updated_at": g.as_of - timedelta(days=r.randint(1, 60)),
            })
            action_id += 1

    # Generate realistic regulatory database entries
    reg_id = 1
    for jurisdiction in ["UK", "EU", "US", "CA", "AU"]:
        regulations_by_jur = {
            "UK": ["Modern Slavery Act 2015", "Environment Act 2021", "Procurement Act 2023"],
            "EU": ["Corporate Sustainability Due Diligence Directive (CSDDD)", "Digital Product Passport Regulation", "Deforestation Regulation"],
            "US": ["Uyghur Forced Labor Prevention Act (UFLPA)", "Dodd-Frank 1502", "California SB-657"],
            "CA": ["Canadian Supply Chain Act", "Conflict Minerals Regulation"],
            "AU": ["Modern Slavery Act 2018"]
        }
        for reg_name in regulations_by_jur.get(jurisdiction, []):
            regulatory.append({
                "regulation_id": f"REG-{reg_id:06d}",
                "jurisdiction": jurisdiction,
                "regulation_name": reg_name,
                "topic": r.choice(["forced_labour", "due_diligence", "transparency", "environmental"]),
                "description": f"Comprehensive due diligence and reporting requirement for {reg_name}",
                "effective_date": g.as_of - timedelta(days=r.randint(30, 365)),
                "affected_scope": "Companies with turnover > £36M or 250+ employees" if jurisdiction == "UK" else "Large enterprises",
                "updated_at": g.as_of - timedelta(days=r.randint(1, 30)),
            })
            reg_id += 1

    # Generate realistic adverse media records
    media_id = 1
    for supplier in suppliers[:10]:
        for _ in range(r.randint(0, 2)):
            adverse_media.append({
                "entity_id": supplier["supplier_id"],
                "record_id": f"MED-{media_id:06d}",
                "entity_type": "supplier",
                "headline": r.choice([
                    f"Allegations of forced labour at {supplier['name']} facilities",
                    f"NGO report: wage theft at {supplier['name']} mills",
                    f"Environmental violations reported at {supplier['name']}",
                    f"Workers' rights concerns raised at {supplier['name']}"
                ]),
                "source": r.choice(["Reuters", "BBC", "NGO Watch", "Fair Labor Association", "Worker Rights Consortium", "Local news"]),
                "content": r.choice([
                    "Investigation found evidence of debt bondage arrangements for migrant workers",
                    "Audit revealed systematic underpayment and excessive overtime",
                    "Environmental discharges affecting nearby water sources",
                    "Workers report union harassment and restricted communication"
                ]),
                "published_date": g.date_between(180, 1),
                "severity": r.choices(["low", "medium", "high", "critical"], [15, 25, 40, 20])[0],
                "verified": r.choice([True, False]),
                "found_at": g.as_of - timedelta(days=r.randint(1, 30)),
                "updated_at": g.as_of - timedelta(days=r.randint(1, 30)),
            })
            media_id += 1

    # Generate realistic sanctions screening records
    screen_id = 1
    for entity in suppliers[:15]:
        screening_date = g.date_between(90, 1)
        sanctions.append({
            "entity_id": entity["supplier_id"],
            "screening_id": f"SCR-{screen_id:06d}",
            "entity_name": entity["name"],
            "screening_date": screening_date,
            "sanctions_list": r.choice(["OFAC", "UN", "UK", "EU", "Multiple"]),
            "match_status": r.choices(["no_match", "possible_match", "confirmed_match"], [90, 8, 2])[0],
            "description": "No sanctions matches found" if r.choice([True, True, True]) else "Entity appears on watchlist; requires escalation",
            "action_taken": "None" if r.choice([True, True, True]) else "Investigation initiated; payments suspended",
            "updated_at": g.as_of - timedelta(days=r.randint(1, 30)),
        })
        screen_id += 1

    # Generate realistic litigation records
    lit_id = 1
    for supplier in suppliers[:8]:
        for _ in range(r.randint(0, 2)):
            litigation.append({
                "entity_id": supplier["supplier_id"],
                "litigation_case_id": f"LIT-{lit_id:06d}",
                "entity_name": supplier["name"],
                "case_type": r.choice(["employment", "labour", "environmental", "commercial"]),
                "jurisdiction": r.choice(["India", "Bangladesh", "China", "Vietnam", "UK"]),
                "case_status": r.choices(["active", "settled", "dismissed", "appealed"], [30, 40, 20, 10])[0],
                "description": r.choice([
                    "Claim by workers for unpaid overtime and wage theft; amount sought £50,000",
                    "Environmental violation suit by local community; seeking remediation and damages",
                    "Wrongful termination claim by former employee union representative",
                    "Trade dispute and breach of contract claim from customer"
                ]),
                "outcome": "Settlement agreed; supplier to pay £25,000 and implement wage improvements" if r.choice([True, False]) else None,
                "case_date": g.date_between(365, 30),
                "updated_at": g.as_of - timedelta(days=r.randint(1, 60)),
            })
            lit_id += 1

    # Generate supplier document requirements
    doc_req_id = 1
    doc_types = ["Forced Labour Policy", "Audit Report", "Compliance Certificate", "Factory Registration", "Ownership Disclosure"]
    for supplier in suppliers[:20]:
        for jurisdiction in ["UK", "EU"]:
            for doc_type in r.sample(doc_types, min(2, len(doc_types))):
                due_date = g.as_of + timedelta(days=r.randint(7, 90))
                if g.rng.random() < 0.3:
                    due_date = g.as_of - timedelta(days=r.randint(1, 30))
                supplier_doc_requirements.append({
                    "doc_requirement_id": f"DREQ-{doc_req_id:06d}",
                    "supplier_id": supplier["supplier_id"],
                    "jurisdiction": jurisdiction,
                    "document_type": doc_type,
                    "description": f"Required evidence of {doc_type.lower()} for due diligence compliance",
                    "required_by_date": due_date,
                    "status": "received" if due_date < g.as_of else r.choices(["pending", "verified"], [70, 30])[0],
                    "updated_at": g.as_of - timedelta(days=r.randint(1, 30)),
                })
                doc_req_id += 1

    # Generate company registry data - use only valid countries from country_risk_indices
    valid_countries = ["IN", "BD", "CN", "PK", "VN", "TH", "KH", "MX", "TN", "ET"]
    for idx, entity in enumerate(suppliers[:20]):
        company_registry.append({
            "entity_id": entity["supplier_id"],
            "entity_name": entity["name"],
            "country": r.choice(valid_countries),
            "registration_number": f"REG-{entity['supplier_id'][-4:]}-{g.rng.randint(1000, 9999)}",
            "registry_source": r.choice(["National Company Registry", "Local Trade Office", "Chamber of Commerce"]),
            "legal_form": r.choice(["Private Limited Company", "Partnership", "Sole Proprietor", "Manufacturing Co-operative"]),
            "registration_date": g.date_between(3650, 365),
            "status": r.choices(["active", "active", "inactive", "suspended"], [85, 10, 3, 2])[0],
            "directors_info": f"Directors on file; beneficial owner verification status: {r.choice(['pending', 'verified', 'escalated'])}",
            "verified_date": g.date_between(365, 1) if r.choice([True, False]) else None,
            "updated_at": g.as_of - timedelta(days=r.randint(1, 30)),
        })

    return {
        "due_diligence_cases": cases,
        "due_diligence_tasks": tasks,
        "supplier_risk_ratings": supplier_risks,
        "risk_evidence": risk_evidence,
        "factory_profiles": factory_profs,
        "supply_chain_mapping": mapping,
        "compliance_requirements": compliance_reqs,
        "compliance_evidence_inventory": compliance_evidence,
        "chain_of_custody_certificates": certs,
        "worker_grievances": grievances,
        "country_risk_indices": country_indices,
        "supplier_sub_tier_relationships": sub_tiers,
        "ownership_structures": ownership,
        "supplier_traceability_evidence": traceability,
        "tier_mapping_by_country": tier_mapping,
        "supply_chain_mapping_gaps": mapping_gaps,
        "audit_findings": audit_findings,
        "corrective_action_plans": corrective_actions,
        "regulatory_database": regulatory,
        "adverse_media_records": adverse_media,
        "sanctions_screening_records": sanctions,
        "litigation_records": litigation,
        "supplier_document_requirements": supplier_doc_requirements,
        "company_registry": company_registry,
    }
