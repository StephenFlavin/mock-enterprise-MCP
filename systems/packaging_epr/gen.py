"""EPR and packaging compliance data: targets, registrations, fees, regulations."""
from datetime import timedelta


def generate(g):
    r = g.rng

    # Get sample SKUs and countries to work with
    products = g.master("products")[:50]  # Sample of products
    countries = ["GB", "DE", "FR", "NL", "ES", "IT"]
    epr_countries = ["DE", "FR", "NL", "BE", "ES", "IT"]
    materials = ["corrugated", "flexible_plastic", "moulded_pulp", "rigid_plastic", "paper", "cardboard"]

    # Generate packaging targets (with future deadlines)
    targets = []
    for i, prod in enumerate(products[:30]):
        sku = prod["sku"]
        for material in r.sample(materials, k=r.randint(1, 3)):
            for metric in ["recycled_content_pct", "recyclability_pct"]:
                tid = f"TGT-{len(targets) + 1:06d}"
                # deadline between 6-24 months in the future
                deadline_days_from_now = r.randint(180, 900)
                deadline = g.as_of + timedelta(days=deadline_days_from_now)
                current = r.randint(30, 75) if metric == "recycled_content_pct" else r.randint(60, 95)
                target = min(100, current + r.randint(10, 35))
                targets.append({
                    "target_id": tid,
                    "sku": sku,
                    "material": material,
                    "metric": metric,
                    "target_value": target,
                    "current_value": current,
                    "deadline": deadline,
                    "status": r.choices(["on_track", "at_risk", "off_track"], [70, 20, 10])[0],
                    "last_updated": g.as_of - timedelta(days=r.randint(7, 60))
                })

    # Generate EPR registrations
    registrations = []
    schemes = ["DSD (Germany)", "Fost Plus (Belgium)", "La Poubelle Verte (France)",
               "Nedvang (Netherlands)", "ECOEMBES (Spain)", "COREPLA (Italy)"]
    for i, country in enumerate(epr_countries):
        for scheme in r.sample(schemes, k=r.randint(1, 2)):
            rid = f"REG-{len(registrations) + 1:06d}"
            registrations.append({
                "registration_id": rid,
                "country": country,
                "scheme_name": scheme,
                "registration_number": f"REG-{country}-{i:04d}",
                "status": r.choices(["active", "pending", "suspended"], [85, 10, 5])[0],
                "registration_date": g.date_between(730, 90),  # between 90-730 days ago
                "category": r.choice(["packaging", "textiles", "batteries"])
            })

    # Generate EPR reporting obligations (with future deadlines)
    obligations = []
    for i, country in enumerate(epr_countries):
        for category in ["packaging", "textiles"]:
            oid = f"OBL-{len(obligations) + 1:06d}"
            # deadline 30-365 days from now
            deadline_days_from_now = r.randint(30, 365)
            deadline = g.as_of + timedelta(days=deadline_days_from_now)
            obligations.append({
                "obligation_id": oid,
                "country": country,
                "category": category,
                "data_required": "Packaging volumes by material; Recycled content %; Disposal route data; Supplier certifications",
                "deadline": deadline,
                "frequency": r.choice(["annual", "quarterly", "monthly"]),
                "penalty_gbp": r.choice([5000, 15000, 30000, 75000, 150000])
            })

    # Generate EPR fee schedules
    schedules = []
    for i, country in enumerate(epr_countries):
        for material in materials:
            sid = f"SCH-{len(schedules) + 1:06d}"
            base_fees = {"plastic": 450, "paper": 150, "glass": 100, "metal": 80, "corrugated": 120, "flexible_plastic": 520, "moulded_pulp": 180, "rigid_plastic": 480}
            fee = base_fees.get(material, 200) + r.randint(-50, 100)
            schedules.append({
                "schedule_id": sid,
                "country": country,
                "scheme_name": f"{country} EPR Scheme",
                "material": material,
                "fee_per_tonne_gbp": fee,
                "effective_from": g.as_of - timedelta(days=r.randint(30, 180)),
                "effective_to": None if r.random() > 0.3 else g.as_of + timedelta(days=r.randint(180, 730))
            })

    # Generate packaging regulations
    regulations = []
    reg_types = ["DSD (Germany)", "AGEC (France)", "Plastic Tax (UK)", "EPR Directive (EU)"]
    for i, country in enumerate(countries):
        for reg_type in r.sample(reg_types, k=r.randint(1, 3)):
            rid = f"REG-{len(regulations) + 1:06d}"
            has_recycled = r.random() > 0.4
            has_tax = r.random() > 0.6
            regulations.append({
                "regulation_id": rid,
                "country": country,
                "regulation_name": reg_type,
                "requirement": f"Packaging {reg_type} compliance required",
                "recycled_content_mandate_pct": r.randint(25, 50) if has_recycled else None,
                "plastic_tax_pct": r.choice([0, 10, 15, 20]) if has_tax else 0,
                "effective_from": g.as_of - timedelta(days=r.randint(0, 730)),
                "effective_to": None if r.random() > 0.5 else g.as_of + timedelta(days=r.randint(180, 1095)),
                "penalty_gbp": r.choice([10000, 25000, 50000, 100000])
            })

    # Generate recyclability assessments
    assessments = []
    pack_types = ["rigid_box", "flexible_pouch", "carton", "blister", "tube", "bag"]
    ratings = ["excellent", "good", "fair", "poor"]
    for i, prod in enumerate(products[:40]):
        sku = prod["sku"]
        for pack_type in r.sample(pack_types, k=r.randint(1, 2)):
            for material in r.sample(materials, k=1):
                aid = f"ASS-{len(assessments) + 1:06d}"
                recyclable_pct = r.randint(40, 100)
                recycled_pct = r.randint(0, min(60, recyclable_pct))
                assessments.append({
                    "assessment_id": aid,
                    "sku": sku,
                    "pack_type": pack_type,
                    "material": material[0],
                    "recyclability_pct": recyclable_pct,
                    "recycled_content_pct": recycled_pct,
                    "recyclability_rating": r.choice(ratings),
                    "notes": r.choice([None, "Contains non-recyclable laminate", "Single material - easily recyclable", "Mixed materials - partial recyclability"]) if r.random() > 0.7 else None,
                    "assessed_date": g.as_of - timedelta(days=r.randint(30, 180))
                })

    # Generate recycled content data
    recycled_content = []
    for i, prod in enumerate(products[:50]):
        sku = prod["sku"]
        for material in r.sample(materials, k=r.randint(1, 3)):
            recycled_pct = r.randint(0, 80)
            target_pct = min(100, recycled_pct + r.randint(5, 40))
            sup_id = prod.get("supplier_id", "SUP-0001")
            recycled_content.append({
                "sku": sku,
                "material": material,
                "recycled_content_pct": recycled_pct,
                "target_recycled_pct": target_pct,
                "supplier_id": sup_id,
                "cost_per_unit_gbp": round(r.uniform(0.15, 2.50), 2),
                "last_updated": g.as_of - timedelta(days=r.randint(7, 90))
            })

    # Generate recycling label rules
    label_rules = []
    categories = ["cosmetics", "home", "textiles", "electronics", "food", "beverages"]
    for i, country in enumerate(countries):
        for category in r.sample(categories, k=r.randint(2, 4)):
            rid = f"LBL-{len(label_rules) + 1:06d}"
            label_rules.append({
                "rule_id": rid,
                "country": country,
                "product_category": category,
                "requirement": f"Recycling and disposal instructions required in local language",
                "material_markings_required": r.choice([True, False]),
                "disposal_instructions_required": True,
                "language_requirements": country if country == "GB" else f"{country}, EN",
                "effective_from": g.as_of - timedelta(days=r.randint(90, 730))
            })

    # Generate EPR preparation tasks
    prep_tasks = []
    employees = g.master("employees")
    for i in range(8):
        tid = f"ERT-{len(prep_tasks) + 1:06d}"
        is_past = r.random() > 0.5
        # Due date: past dates if is_past, future dates otherwise
        days_offset = r.randint(-60, 90) if is_past else r.randint(1, 90)
        due_date = g.as_of + timedelta(days=days_offset)

        prep_tasks.append({
            "task_id": tid,
            "country": r.choice(epr_countries),
            "category": r.choice(["packaging", "textiles"]),
            "task_description": r.choice([
                "Verify all product data fields available in PIM",
                "Set up EPR registration",
                "Prepare supplier compliance questionnaire",
                "Test monthly reporting workflow",
                "Map recycling pathways by region",
                "Audit packaging material specifications",
                "Conduct regulatory gap analysis",
                "Train logistics team on new requirements"
            ]),
            "status": r.choices(["open", "in_progress", "completed", "cancelled"], [30, 35, 30, 5])[0],
            "due_date": due_date,
            "assigned_to": r.choice([e["employee_id"] for e in employees[:20]]) if employees else "EMP-01234",
            "cancel_reason": r.choice([None, "Out of scope", "Resource constraints", "Regulatory change"]) if r.random() > 0.8 else None,
            "created_at": g.as_of - timedelta(days=r.randint(30, 120)),
            "updated_at": g.as_of - timedelta(days=r.randint(1, 60))
        })

    # Generate packaging cost factors
    cost_factors = []
    for i, country in enumerate(countries):
        for material in r.sample(materials, k=r.randint(2, 4)):
            fid = f"FCT-{len(cost_factors) + 1:06d}"
            cost_factors.append({
                "factor_id": fid,
                "material": material,
                "country": country,
                "packaging_tax_rate_pct": r.choice([0, 10, 15, 20, 25]),
                "epr_contribution_pct": r.uniform(0.5, 5.0),
                "regulatory_cost_per_unit_gbp": round(r.uniform(0.05, 0.75), 3),
                "effective_from": g.as_of - timedelta(days=r.randint(0, 365))
            })

    return {
        "packaging_targets": targets,
        "epr_registrations": registrations,
        "epr_reporting_obligations": obligations,
        "epr_fee_schedules": schedules,
        "packaging_regulations": regulations,
        "recyclability_assessments": assessments,
        "recycled_content_data": recycled_content,
        "recycling_label_rules": label_rules,
        "epr_preparation_tasks": prep_tasks,
        "packaging_cost_factors": cost_factors
    }
