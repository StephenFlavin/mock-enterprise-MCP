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
    }
