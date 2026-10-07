"""Compliance database: background noise only. Story rows live in seed/*.csv."""
from datetime import timedelta

STORY_SKUS = {"SKU-102590", "SKU-104123", "SKU-104795", "SKU-105551", "SKU-106356", "PF-220", "SKU-100847", "SKU-102779",
              "SKU-104039", "SKU-100868", "SKU-103136", "SKU-101813", "SKU-103199", "SKU-103745", "SKU-102905", "K-1700",
              "SKU-100875", "SKU-100882", "SKU-101456", "SKU-101463", "SKU-100385", "SKU-100259", "SKU-100154", "SKU-100427",
              "SKU-100700"}
# suppliers whose certificates are planted in seed/ (kept out of the generated noise)
STORY_SUPPLIERS = {"SUP-0001", "SUP-0002", "SUP-0036", "SUP-0044", "SUP-0052", "SUP-0058", "SUP-0067", "SUP-0077"}
CATEGORY_MAP = {"Nightwear": "kids_sleepwear", "Drinkware": "childrens_drinkware", "Outerwear": "waterproof_outerwear",
                "Skincare": "cosmetics", "Bodycare": "cosmetics", "Haircare": "cosmetics", "Fragrance": "cosmetics",
                "Bags": "leather_goods", "Small Appliances": "electrical_appliances"}


def generate(g):
    r = g.rng
    products = [p for p in g.master("products") if p["sku"] not in STORY_SKUS]
    suppliers = g.master("suppliers")

    # other regulations we track (footwear, jewellery, packaging, lighting): active, past effective dates
    others = [
        ("UK Footwear Labelling Regulations 1995", "UK", "footwear", "labelling of materials in footwear", "medium", "active"),
        ("EU Nickel Release Restriction (REACH entry 27)", "EU", "jewellery", "nickel release from jewellery and metal accessories", "medium", "active"),
        ("EU Packaging and Packaging Waste Regulation", "EU", "packaging", "recyclability and recycled content of packaging", "medium", "active"),
        ("UK Plastic Packaging Tax rules", "UK", "packaging", "recycled content threshold for plastic packaging", "low", "active"),
        ("US Prop 65 Chemical Warnings", "US", "all", "California chemical exposure warnings", "medium", "active"),
        ("EU Energy Labelling for lighting (superseded)", "EU", "lighting", "energy label scale for light sources", "low", "superseded"),
    ]
    regulations, reqs = [], []
    for i, (title, mk, scope, desc, imp, status) in enumerate(others, 1):
        rid = f"REG-{i:06d}"
        eff = g.days_ago(r.randint(400, 3000))
        regulations.append({"regulation_id": rid, "title": title, "description": desc, "market": mk, "product_scope": scope,
                            "effective_date": eff, "impact_level": imp, "status": status, "keywords": f"{scope} {desc}",
                            "required_action": "Keep documentation current", "created_at": g.days_ago(r.randint(200, 400)),
                            "updated_at": g.days_ago(r.randint(0, 60))})
        reqs.append({"req_id": f"REQ-{i:06d}", "regulation_id": rid, "market": mk, "product_category": scope,
                     "requirement_type": r.choice(["labelling", "documentation", "material"]), "topic": "general",
                     "standard": title, "description": f"Comply with {title}", "applies_to": scope})

    status_rows = []
    for p in r.sample(products, 60):
        cat = CATEGORY_MAP.get(p["category"], "general_goods")
        for mk in ("UK", "EU"):
            s = r.choices(["compliant", "under_review"], weights=[93, 7])[0]
            missing = r.choice(["test_report", "certificate", "labelling_approval"]) if s != "compliant" else None
            if mk == "EU":  # EU gaps are all planted in seed/ so the list for EU/Ireland is exactly the story
                s, missing = "compliant", None
            status_rows.append({"sku": p["sku"], "market": mk, "product_category": cat, "compliance_status": s,
                                "missing_data_type": missing, "required_by": g.days_ago(-r.randint(30, 150)) if missing else None,
                                "notes": f"Awaiting {missing}" if missing else "Tracked", "updated_at": g.days_ago(r.randint(0, 40))})

    issues = []
    for i, p in enumerate(r.sample(products, 8), 1):
        issues.append({"issue_id": f"ISS-{i:06d}", "sku": p["sku"], "market": r.choice(["UK", "EU", "US"]),
                       "issue_type": r.choice(["labelling_gap", "certification_missing", "spec_non_compliance"]),
                       "description": f"Routine compliance follow-up for {p['name']}", "priority": r.choice(["low", "medium"]),
                       "status": r.choice(["open", "resolved", "resolved"]), "created_at": g.days_ago(r.randint(20, 120)),
                       "updated_at": g.days_ago(r.randint(0, 20))})

    tasks = []
    for i, reg in enumerate(regulations[:3], 1):
        tasks.append({"task_id": f"TSK-{i:06d}", "regulation_id": reg["regulation_id"], "title": f"Annual review of {reg['title']}",
                      "description": "Confirm documentation is current", "task_type": "documentation",
                      "status": r.choice(["completed", "in_progress"]), "due_date": g.days_ago(-r.randint(10, 120)),
                      "created_at": g.days_ago(r.randint(30, 90)), "updated_at": g.days_ago(r.randint(0, 30))})

    certs, registry = [], []
    for i, sup in enumerate(r.sample([s for s in suppliers if s["country"] not in ("PT", "TR") and s["supplier_id"] not in STORY_SUPPLIERS], 10), 1):
        num = f"OT-26-{4000000 + i * 37}"
        exp = g.days_ago(-r.randint(90, 600))
        certs.append({"cert_id": f"CRT-{i:06d}", "certificate_number": num, "certification_type": r.choice(["oeko_tex", "gots", "bluesign"]),
                      "holder_type": "supplier", "holder_name": sup["name"], "supplier_id": sup["supplier_id"],
                      "material": r.choice(["cotton", "polyester", "wool"]), "issue_date": g.days_ago(r.randint(200, 500)),
                      "expiry_date": exp, "verified_in_registry": True, "registry_checked_at": g.days_ago(r.randint(5, 60)), "status": "active"})
        registry.append({"registry_entry_id": f"CRG-{i:06d}", "certificate_number": num, "certification_type": certs[-1]["certification_type"],
                         "holder_name": sup["name"], "holder_country": sup["country"], "issued_date": certs[-1]["issue_date"], "expiry_date": exp,
                         "registry_url": f"https://registry.example.org/verify/{num}", "is_valid": True, "status": "valid",
                         "last_checked": g.days_ago(r.randint(5, 60))})
    return {"regulations": regulations, "regulatory_requirements": reqs, "product_compliance_status": status_rows,
            "compliance_issues": issues, "compliance_tasks": tasks, "material_certifications": certs,
            "labelling_requirements": [], "substance_restrictions": [], "sustainability_claims": [],
            "certification_registry": registry, "regulated_categories": [], "countries": [], "regulatory_notifications": [],
            "alternative_materials": [], "material_substances": []}
