"""Compliance database: regulations, requirements, certifications, and compliance tracking."""
from datetime import timedelta


def generate(g):
    """Generate compliance data for regulations, certifications, and labelling requirements."""
    r = g.rng
    fake = g.fake

    # Get sample products and suppliers from master
    products = g.master("products")[:30]  # Use first 30 products as sample
    suppliers = g.master("suppliers")[:20]  # Use first 20 suppliers

    regulations = []
    regulatory_requirements = []
    product_compliance_status = []
    compliance_issues = []
    compliance_tasks = []
    material_certifications = []
    labelling_requirements = []
    substance_restrictions = []
    sustainability_claims = []
    certification_registry = []

    # Create regulations for different markets and product categories
    reg_data = [
        # UK regulations
        ("Textiles Labelling", "UK", "apparel", "labelling, composition declaration",
         g.days_ago(-180), g.days_ago(-180), "active", "medium"),
        ("Consumer Rights Act", "UK", "all", "product safety documentation, recalls",
         g.days_ago(-730), g.days_ago(-730), "active", "high"),
        ("REACH Registration Update 2027", "UK", "all", "substance registration",
         g.days_ago(180), g.days_ago(180), "upcoming", "high"),

        # EU regulations
        ("OEKO-TEX Textiles", "EU", "textiles", "certification, chemical testing",
         g.days_ago(-365), g.days_ago(-365), "active", "medium"),
        ("EU Ecolabel", "EU", "apparel", "environmental certification",
         g.days_ago(-180), g.days_ago(-180), "active", "low"),
        ("PFAS Restrictions Phase 1", "EU", "waterproof_outerwear", "PFAS content limits",
         g.days_ago(200), g.days_ago(200), "upcoming", "critical"),
        ("Microplastics Ban Textiles", "EU", "all_textiles", "microfibre shedding limits",
         g.days_ago(350), g.days_ago(350), "upcoming", "high"),

        # US regulations
        ("Consumer Product Safety", "US", "all", "testing, CPSC certification",
         g.days_ago(-730), g.days_ago(-730), "active", "high"),
        ("California Prop 65", "US", "all", "chemical warnings",
         g.days_ago(-1460), g.days_ago(-1460), "active", "medium"),

        # AU regulations
        ("Australian Consumer Law", "AU", "all", "product safety, labelling",
         g.days_ago(-730), g.days_ago(-730), "active", "medium"),
    ]

    for idx, (title, market, scope, description, eff_date, trans_end, status, impact) in enumerate(reg_data):
        reg_id = f"REG-{idx+1:06d}"
        regulations.append({
            "regulation_id": reg_id,
            "title": title,
            "description": description,
            "market": market,
            "product_scope": scope,
            "effective_date": eff_date,
            "transitional_period_end": eff_date + timedelta(days=180) if status == "upcoming" else None,
            "impact_level": impact,
            "status": status,
            "created_at": g.days_ago(r.randint(30, 90)),
            "updated_at": g.days_ago(r.randint(0, 30)),
        })

    # Create regulatory requirements for each regulation
    req_types = ["labelling", "testing", "certification", "performance", "material", "documentation"]
    for reg in regulations:
        for req_type in r.sample(req_types, k=r.randint(1, 3)):
            req_id = f"REQ-{len(regulatory_requirements)+1:06d}"
            req_desc = {
                "labelling": f"Must include {reg['market']} language and content warnings",
                "testing": f"Requires third-party testing for {reg['product_scope']}",
                "certification": f"OEKO-TEX or equivalent certification required",
                "performance": f"Must meet {reg['market']} durability and flammability standards",
                "material": f"Restricted substances check for {reg['product_scope']}",
                "documentation": f"Compliance documentation and supply chain traceability",
            }[req_type]
            regulatory_requirements.append({
                "req_id": req_id,
                "regulation_id": reg["regulation_id"],
                "market": reg["market"],
                "product_category": "water_bottles" if "bottle" in reg["product_scope"] else "apparel",
                "requirement_type": req_type,
                "description": req_desc,
                "applies_to": reg["product_scope"],
            })

    # Create product compliance status
    for product in products[:15]:
        for market in ["UK", "EU", "US", "AU"]:
            status_choice = r.choices(
                ["compliant", "under_review", "non_compliant"],
                weights=[70, 20, 10]
            )[0]
            missing = None
            if status_choice in ["under_review", "non_compliant"]:
                missing = r.choice(["test_report", "certificate", "labelling_approval", "material_declaration"])

            product_compliance_status.append({
                "sku": product["sku"],
                "market": market,
                "compliance_status": status_choice,
                "missing_data_type": missing,
                "required_by": g.days_ago(r.randint(-90, 90)) if missing else None,
                "notes": f"Tracked for {market} market" if status_choice == "compliant" else
                         f"Awaiting {missing}" if missing else None,
                "updated_at": g.days_ago(r.randint(0, 30)),
            })

    # Create compliance issues
    for idx in range(r.randint(5, 15)):
        issue_id = f"ISS-{idx+1:06d}"
        product = r.choice(products[:15])
        compliance_issues.append({
            "issue_id": issue_id,
            "sku": product["sku"],
            "market": r.choice(["UK", "EU", "US"]),
            "issue_type": r.choice(["labelling_gap", "testing_failure", "certification_missing",
                                    "spec_non_compliance", "ingredient_issue"]),
            "description": f"Compliance issue for {product['name']}",
            "priority": r.choice(["critical", "high", "medium", "low"]),
            "status": r.choice(["open", "under_review", "resolved"]),
            "created_at": g.days_ago(r.randint(0, 60)),
            "resolved_at": g.days_ago(r.randint(0, 30)) if r.random() > 0.3 else None,
            "updated_at": g.days_ago(r.randint(0, 30)),
        })

    # Create compliance tasks
    for idx, reg in enumerate(regulations[:5]):
        task_id = f"TSK-{idx+1:06d}"
        compliance_tasks.append({
            "task_id": task_id,
            "regulation_id": reg["regulation_id"],
            "title": f"Address {reg['title']} requirements",
            "description": f"Complete compliance actions for {reg['title']} in {reg['market']}",
            "task_type": r.choice(["testing", "documentation", "supplier_request", "design_change",
                                    "labelling_update", "certification"]),
            "status": r.choice(["open", "in_progress", "completed"]),
            "due_date": reg["effective_date"] - timedelta(days=30),
            "assigned_to": None,
            "estimated_cost_gbp": r.randint(5000, 50000) if r.random() > 0.5 else None,
            "created_at": g.days_ago(r.randint(30, 90)),
            "updated_at": g.days_ago(r.randint(0, 30)),
        })

    # Create material certifications
    cert_types = ["oeko_tex", "gots", "fair_trade", "b_corp", "eu_ecolabel", "cradle_to_cradle", "bluesign"]
    for idx in range(r.randint(8, 15)):
        cert_id = f"CRT-{idx+1:06d}"
        holder_type = r.choice(["supplier", "factory", "own_product", "material"])
        supplier = r.choice(suppliers) if holder_type == "supplier" else None
        product = r.choice(products[:15]) if holder_type == "own_product" else None

        material_certifications.append({
            "cert_id": cert_id,
            "certificate_number": f"{r.choice(['OT', 'GT', 'FT'])}-26-{fake.numerify('########')}",
            "certification_type": r.choice(cert_types),
            "holder_type": holder_type,
            "holder_name": supplier["name"] if supplier else (product["name"] if product else fake.company()),
            "supplier_id": supplier["supplier_id"] if supplier else None,
            "sku": product["sku"] if product else None,
            "material": r.choice(["cotton", "polyester", "wool", "silk", "linen"]) if holder_type == "material" else None,
            "issue_date": g.days_ago(r.randint(30, 365)),
            "expiry_date": g.days_ago(r.randint(-365, 365)),
            "verified_in_registry": r.choice([True, False]),
            "registry_checked_at": g.days_ago(r.randint(0, 60)),
            "status": r.choice(["active", "pending"]),
        })

    # Create labelling requirements by market
    categories = [
        ("legal_marks", "UK", "Must display CE mark or UKCA mark"),
        ("content_declaration", "UK", "Fiber composition and percentages"),
        ("warnings", "UK", "Choking hazard warnings for items < 5cm"),
        ("legal_marks", "EU", "Must display CE mark"),
        ("content_declaration", "EU", "Fiber composition and percentages"),
        ("warnings", "EU", "Choking hazard warnings; language must be EU language"),
        ("allergens", "EU", "Must declare common allergens"),
        ("recycling", "EU", "Recycling symbol and material type code"),
        ("legal_marks", "US", "CPSC certification mark"),
        ("warnings", "US", "Age warnings for children's products"),
        ("origin", "AU", "Country of origin marking"),
        ("warnings", "AU", "Australian consumer warnings"),
    ]

    for cat, market, text in categories:
        label_req_id = f"LBL-{len(labelling_requirements)+1:06d}"
        labelling_requirements.append({
            "label_req_id": label_req_id,
            "market": market,
            "language": "en" if market in ["UK", "US", "AU"] else r.choice(["en", "de", "fr", "it"]),
            "requirement_category": cat,
            "requirement_text": text,
            "product_scope": r.choice(["apparel", "textiles", "cosmetics", "electronics"]),
            "mandatory": r.choice([True, True, False]),
            "minimum_font_size_pt": 8 if "legal" in cat else None,
        })

    # Create substance restrictions
    substances = [
        ("PFAS", "durable water repellent", "EU", "phase_out", g.days_ago(180), True),
        ("Chromium VI", "leather tanning", "EU", "banned", g.days_ago(-365), True),
        ("Formaldehyde", "textiles", "EU", "restricted", g.days_ago(-365), True),
        ("Azo Dyes", "textiles", "UK", "restricted", g.days_ago(-365), False),
        ("Lead", "all products", "US", "banned", g.days_ago(-730), True),
        ("Phthalates", "plastics", "EU", "restricted", g.days_ago(-365), True),
    ]

    for idx, (name, use, market, res_type, eff_date, alt_avail) in enumerate(substances):
        substance_id = f"SUB-{idx+1:06d}"
        substance_restrictions.append({
            "substance_id": substance_id,
            "substance_name": name,
            "common_name": name,
            "restriction_type": res_type,
            "market": market,
            "applies_to": use,
            "effective_date": eff_date,
            "ban_date": eff_date + timedelta(days=180) if res_type == "phase_out" else None,
            "typical_use": use,
            "alternative_available": alt_avail,
        })

    # Create sustainability claims
    for idx in range(r.randint(6, 12)):
        claim_id = f"CLA-{idx+1:06d}"
        subject = r.choice(["own_product", "competitor_product", "supplier_brand", "material"])
        subject_id = r.choice(products)["name"] if subject in ["own_product", "competitor_product"] else fake.company()

        sustainability_claims.append({
            "claim_id": claim_id,
            "subject_type": subject,
            "subject_id": subject_id,
            "claim_text": r.choice([
                "Made from 100% recycled materials",
                "GOTS certified organic cotton",
                "Carbon neutral production",
                "Fair trade certified",
                "Zero waste manufacturing",
            ]),
            "claim_type": r.choice(["recycled_content", "sustainable_sourced", "carbon_neutral",
                                     "water_saved", "animal_welfare"]),
            "certification_backing": r.choice(["GOTS", "Fair Trade", "B Corp", None]),
            "certification_verified": r.choice([True, False]),
            "confidence_level": r.choice(["verified", "likely", "unclear", "dubious"]),
            "sources": f"Website, {subject_id}",
            "updated_at": g.days_ago(r.randint(0, 60)),
        })

    # Create certification registry entries
    for cert in material_certifications[:8]:
        registry_entry_id = f"REG-{len(certification_registry)+1:06d}"
        certification_registry.append({
            "registry_entry_id": registry_entry_id,
            "certificate_number": cert["certificate_number"],
            "certification_type": cert["certification_type"],
            "holder_name": cert["holder_name"],
            "issued_date": cert["issue_date"],
            "expiry_date": cert["expiry_date"],
            "registry_url": f"https://registry.example.com/{cert['certification_type']}/{cert['certificate_number']}",
            "is_valid": cert["status"] == "active" and cert["expiry_date"] > g.as_of,
            "last_checked": g.days_ago(r.randint(0, 60)),
        })

    return {
        "regulations": regulations,
        "regulatory_requirements": regulatory_requirements,
        "product_compliance_status": product_compliance_status,
        "compliance_issues": compliance_issues,
        "compliance_tasks": compliance_tasks,
        "material_certifications": material_certifications,
        "labelling_requirements": labelling_requirements,
        "substance_restrictions": substance_restrictions,
        "sustainability_claims": sustainability_claims,
        "certification_registry": certification_registry,
    }
