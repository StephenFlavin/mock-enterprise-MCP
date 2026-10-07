"""PLM data: product tech packs, BOMs, material specs, batches and specifications."""
import json
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    fake = g.fake

    # Common materials and components
    materials = [
        {"id": "MAT-POL-100", "name": "100% Polyester", "type": "fabric", "gsm": 120, "mill": "MIL-01", "cost": 2.50},
        {"id": "MAT-COT-100", "name": "100% Cotton", "type": "fabric", "gsm": 140, "mill": "MIL-02", "cost": 3.20},
        {"id": "MAT-POL-COT-50", "name": "50/50 Poly-Cotton", "type": "fabric", "gsm": 130, "mill": "MIL-01", "cost": 2.85},
        {"id": "MAT-NYL-BLEND", "name": "80/20 Nylon/Spandex", "type": "fabric", "gsm": 80, "mill": "MIL-03", "cost": 4.50},
        {"id": "MAT-VISCOSE", "name": "Viscose Rayon", "type": "fabric", "gsm": 110, "mill": "MIL-02", "cost": 3.00},
        {"id": "MAT-LINEN", "name": "Linen", "type": "fabric", "gsm": 150, "mill": "MIL-04", "cost": 5.00},
        {"id": "MAT-WOOL", "name": "Merino Wool", "type": "fabric", "gsm": 200, "mill": "MIL-05", "cost": 6.00},
        {"id": "MAT-SPANDEX", "name": "Elastane/Spandex 5%", "type": "trim", "cost": 0.15},
        {"id": "MAT-ZIPPER", "name": "Coil Zipper YKK", "type": "component", "cost": 0.40},
        {"id": "MAT-BUTTON", "name": "Polyester Button", "type": "component", "cost": 0.05},
    ]

    # Common mills and dye houses
    mills = ["MIL-01", "MIL-02", "MIL-03", "MIL-04", "MIL-05"]
    dye_houses = ["DYES-A", "DYES-B", "DYES-C"]

    # Get products from master
    products = g.master("products")[:60]  # Use first 60 products
    suppliers = g.master("suppliers")[:20]
    factories = g.master("factories")[:15]

    # ======== product_tech_pack ========
    tech_packs = []
    for prod in products:
        sku = prod["sku"]
        # Pick 1-3 materials for composition
        mat_count = r.randint(1, 3)
        composition_parts = []
        for _ in range(mat_count):
            mat = r.choice(materials[:7])  # Use fabric materials
            pct = r.randint(20, 100)
            composition_parts.append(f"{pct}% {mat['name']}")

        design_attrs = ["breathable", "stretch", "water-resistant", "quick-dry", "anti-microbial", "UV protection"]
        selected_attrs = [design_attrs[i] for i in r.sample(range(len(design_attrs)), r.randint(1, 3))]

        tp = {
            "sku": sku,
            "style_id": prod["style_id"],
            "name": prod["name"],
            "department": prod["department"],
            "category": prod["category"],
            "subcategory": prod["subcategory"],
            "supplier_id": prod["supplier_id"],
            "factory_id": prod["factory_id"],
            "color": prod["colour"],
            "main_material": r.choice(materials[:7])["name"],
            "material_composition": ", ".join(composition_parts),
            "design_attributes": json.dumps(selected_attrs),
            "lead_time_days": prod["lead_time_days"],
            "status": prod["status"],
            "created_at": g.days_ago(r.randint(30, 500)),
            "updated_at": g.days_ago(r.randint(0, 30)),
        }
        tech_packs.append(tp)

    # ======== bill_of_materials ========
    boms = []
    for prod in products:
        sku = prod["sku"]
        # 2-5 line items per product
        line_count = r.randint(2, 5)
        for line_no in range(1, line_count + 1):
            mat = r.choice(materials)
            comp_supplier = r.choice(suppliers)
            comp_factory = r.choice(factories)

            quantity = r.randint(1, 5) if mat["type"] == "component" else r.uniform(0.5, 3.0)
            unit = "pcs" if mat["type"] == "component" else ("m" if "fabric" in mat["type"].lower() else "kg")

            bom = {
                "sku": sku,
                "line_no": line_no,
                "component_type": mat["type"] if mat["type"] in ["fabric", "trim", "component", "packing"] else "component",
                "component_id": mat["id"],
                "component_name": mat["name"],
                "material_name": mat["name"],
                "supplier_id": comp_supplier["supplier_id"],
                "factory_id": comp_factory["factory_id"],
                "quantity": quantity,
                "unit": unit,
                "unit_cost_gbp": mat["cost"],
                "lead_time_days": comp_supplier["payment_terms_days"],
                "notes": "",
            }
            boms.append(bom)

    # ======== material_library ========
    lib_materials = []
    for i, mat in enumerate(materials):
        supplier = r.choice(suppliers)
        mill_id = r.choice(mills) if mat["type"] == "fabric" else None

        lib_mat = {
            "material_id": mat["id"],
            "name": mat["name"],
            "material_type": mat["type"],
            "fiber_content": mat["name"],
            "mill_id": mill_id,
            "supplier_id": supplier["supplier_id"],
            "gsm": mat.get("gsm"),
            "weight_kg_per_meter": None,
            "width_cm": 150 if mat["type"] == "fabric" else None,
            "color": r.choice(["black", "white", "navy", "red", "blue", "grey"]),
            "certifications": json.dumps(r.sample(["GOTS", "OEKO-TEX", "BSCI"], r.randint(1, 2))),
            "sustainability_score": r.randint(1, 5),
            "compliance_status": r.choice(["approved", "approved", "under_review"]),
            "readiness_level": "production",
            "unit_cost_gbp": mat["cost"],
            "lead_time_days": r.randint(14, 90),
            "stock_kg": r.randint(500, 5000),
            "created_at": g.days_ago(r.randint(30, 300)),
        }
        lib_materials.append(lib_mat)

    # ======== material_batches ========
    batches = []
    for i, mat in enumerate(lib_materials):
        # 3-8 batches per material
        batch_count = r.randint(3, 8)
        for j in range(batch_count):
            supplier = r.choice(suppliers)
            mill = mat["mill_id"] or r.choice(mills)

            batch = {
                "batch_id": f"BATCH-{i:03d}{j:02d}",
                "material_id": mat["material_id"],
                "supplier_id": supplier["supplier_id"],
                "factory_id": r.choice(factories)["factory_id"],
                "batch_date": g.days_ago(r.randint(1, 180)),
                "quantity_kg": r.randint(500, 5000),
                "quantity_meters": r.randint(1000, 10000) if mat["material_type"] == "fabric" else None,
                "color_lot": f"LOT-{r.randint(1000, 9999)}",
                "dye_house": r.choice(dye_houses) if mat["material_type"] == "fabric" else None,
                "test_status": r.choice(["passed", "passed", "passed", "failed"]),
                "test_date": g.days_ago(r.randint(0, 30)),
                "traceability_notes": f"Batch {j+1} from {supplier['name']}",
                "used_in_skus": json.dumps([p["sku"] for p in r.sample(products, r.randint(1, 5))]),
                "status": "active",
                "created_at": g.days_ago(r.randint(1, 180)),
            }
            batches.append(batch)

    # ======== dye_lots ========
    dye_lots = []
    batch_count = 0
    for batch in batches:
        if batch.get("dye_house"):  # Only fabric batches
            dye_lot = {
                "dye_lot_id": f"DYE-{batch_count:06d}",
                "batch_id": batch["batch_id"],
                "fabric_material": batch["material_id"],
                "mill_id": r.choice(mills),
                "dye_house": batch["dye_house"],
                "color_description": r.choice(["Navy", "Black", "Red", "Blue", "Green", "Grey", "White"]),
                "dye_date": batch["batch_date"],
                "process_name": r.choice(["Continuous", "Exhaust", "Pad-batch", "Jig"]),
                "process_chemicals": json.dumps(["Acid dye", "Alkali", "Levelling agent"]),
                "process_changes": "",
                "temperature_c": r.randint(60, 100),
                "duration_minutes": r.randint(30, 180),
                "yield_pct": r.uniform(85, 99),
                "fastness_rubbing": str(r.randint(3, 5)),
                "fastness_washing": str(r.randint(3, 5)),
                "test_status": r.choice(["passed", "passed", "passed", "failed"]),
                "notes": "",
            }
            dye_lots.append(dye_lot)
            batch_count += 1

    # ======== fabric_specs ========
    fabric_specs = []
    styles = g.master("products")
    for i, style in enumerate(styles[:40]):
        fabric_spec = {
            "fabric_spec_id": f"FAB-{i:06d}",
            "material_id": r.choice(lib_materials)["material_id"],
            "style_id": style["style_id"],
            "fabric_name": f"{style['name']} Fabric",
            "fiber_content": r.choice(["100% Polyester", "100% Cotton", "80/20 Poly-Cotton", "50/50 Nylon-Spandex"]),
            "weave": r.choice(["Plain", "Twill", "Sateen", "Jersey", "Fleece"]),
            "gsm": r.randint(80, 250),
            "width_cm": r.choice([140, 150, 160]),
            "mill_id": r.choice(mills),
            "mill_country": r.choice(["IN", "BD", "PK", "CN", "VN"]),
            "origin_country": r.choice(["IN", "BD", "PK", "CN", "VN"]),
            "supplier_id": r.choice(suppliers)["supplier_id"],
            "color": style["colour"],
            "shrinkage_pct": r.uniform(0.5, 3.0),
            "tensile_strength": r.randint(200, 800),
            "tear_strength": r.randint(50, 300),
            "pilling_resistance": str(r.randint(3, 5)),
            "abrasion_cycles": r.randint(10000, 100000),
            "cost_per_meter_gbp": r.uniform(1.5, 8.0),
            "lead_time_days": r.randint(30, 120),
            "certifications": json.dumps(r.sample(["GOTS", "OEKO-TEX", "BSCI"], r.randint(0, 2))),
            "sustainability_score": r.randint(1, 5),
        }
        fabric_specs.append(fabric_spec)

    # ======== product_specifications ========
    product_specs = []
    for prod in products[:30]:
        # Size chart for each product
        sizes = ["XS", "S", "M", "L", "XL", "XXL"]
        size_chart = {
            "sku": prod["sku"],
            "spec_type": "size_chart",
            "spec_name": f"Size chart for {prod['sku']}",
            "spec_version": 1,
            "content": json.dumps({
                "sizes": sizes,
                "measurements": {"chest_cm": [76, 81, 86, 91, 97, 102], "length_cm": [60, 63, 66, 69, 72, 75]}
            }),
            "applicable_sizes": json.dumps(sizes),
            "applicable_fits": json.dumps(["regular", "slim", "oversized"]),
            "measurement_points": json.dumps(["chest", "waist", "length", "sleeve"]),
            "shrinkage_tolerances": None,
            "grade_definitions": None,
            "notes": "",
            "created_at": g.days_ago(r.randint(30, 300)),
            "updated_at": g.days_ago(r.randint(0, 30)),
        }
        product_specs.append(size_chart)

        # Grade rules
        grade_rules = {
            "sku": prod["sku"],
            "spec_type": "grade_rules",
            "spec_name": f"Grade rules for {prod['sku']}",
            "spec_version": 1,
            "content": json.dumps({"grade_A": "0-3mm", "grade_B": "3-5mm"}),
            "applicable_sizes": json.dumps(sizes),
            "applicable_fits": json.dumps(["regular"]),
            "measurement_points": None,
            "shrinkage_tolerances": None,
            "grade_definitions": json.dumps({"A": "Premium", "B": "Standard", "C": "Secondary"}),
            "notes": "",
            "created_at": g.days_ago(r.randint(30, 300)),
            "updated_at": g.days_ago(r.randint(0, 30)),
        }
        product_specs.append(grade_rules)

    # ======== candidate_materials ========
    candidate_mats = []
    experimental_mats = [
        "Recycled Polyester Blend", "Bio-based Nylon", "Mycelium Leather",
        "Algae Fiber", "Cork-Cotton Blend", "Lab-Grown Leather"
    ]
    for i, mat_name in enumerate(experimental_mats):
        candidate = {
            "candidate_id": f"CAND-{i:06d}",
            "material_name": mat_name,
            "material_type": r.choice(["fabric", "yarn", "component"]),
            "fiber_content": f"Trial composition for {mat_name}",
            "supplier_id": r.choice(suppliers)["supplier_id"],
            "readiness_level": r.choice(["experimental", "pilot", "proven"]),
            "test_status": r.choice(["planned", "in_progress", "completed", "passed"]),
            "cost_savings_pct": r.uniform(5, 25),
            "weight_reduction_pct": r.uniform(0, 30),
            "sustainability_benefit": f"Reduced carbon footprint vs conventional",
            "pilot_date_start": g.days_ago(r.randint(30, 180)),
            "pilot_date_end": g.days_ago(r.randint(0, 30)),
            "test_plan": json.dumps(["Tensile test", "Abrasion test", "Shrinkage test"]),
            "test_results": json.dumps({"status": "in progress", "next_checkpoint": "2 weeks"}),
            "notes": f"Trial material {i+1}",
            "archived_at": None,
        }
        candidate_mats.append(candidate)

    # ======== co_development_projects ========
    codev_projects = []
    for i in range(5):
        project = {
            "project_id": f"CODEV-{i:06d}",
            "project_name": f"Co-dev Project {i+1}",
            "supplier_id": r.choice(suppliers)["supplier_id"],
            "factory_id": r.choice(factories)["factory_id"],
            "category": r.choice(["Womenswear", "Menswear", "Home"]),
            "scope": f"Develop new {r.choice(['material', 'process', 'component'])}",
            "status": r.choice(["planning", "active", "completed"]),
            "start_date": g.days_ago(r.randint(30, 300)),
            "target_date": g.days_ago(r.randint(-60, 200)),
            "actual_completion": None if r.choice([True, False]) else g.days_ago(r.randint(0, 100)),
            "investment_gbp": r.randint(10000, 100000),
            "cost_savings_gbp": r.randint(0, 50000),
            "target_cost_reduction_pct": r.uniform(5, 20),
            "materials_developed": json.dumps([f"Material {j+1}" for j in range(r.randint(1, 3))]),
            "ip_ownership": "Shared",
            "notes": f"Project {i+1} notes",
        }
        codev_projects.append(project)

    # ======== product_change_requests ========
    change_reqs = []
    for i in range(10):
        change_req = {
            "change_request_id": f"CHG-{i:06d}",
            "sku": r.choice(products)["sku"],
            "change_type": r.choice(["material", "design", "size", "grade", "specification"]),
            "change_description": "Improve fit for size 14 hip area",
            "reason": "High return rate",
            "impact_assessment": json.dumps({"cost_impact": "Low", "timeline": "2 weeks"}),
            "requested_by": "EMP-001",
            "requested_at": g.days_ago(r.randint(0, 60)),
            "status": r.choice(["open", "approved", "in_progress"]),
            "priority": r.choice(["low", "medium", "high"]),
            "target_implementation": g.days_ago(r.randint(-30, 60)),
            "notes": "Change request details",
            "updated_at": g.days_ago(r.randint(0, 30)),
        }
        change_reqs.append(change_req)

    # ======== product_substances ========
    product_substances = []
    substances = [
        ("CAS-000-1", "Polyester", "fabric", "Textiles"),
        ("CAS-000-2", "Lead", "trim", "RoHS"),
        ("CAS-000-3", "Phthalates", "plastic", "Toys"),
    ]
    for i, prod in enumerate(products[:30]):
        subst = r.choice(substances)
        ps = {
            "sku": prod["sku"],
            "substance_id": subst[0],
            "substance_name": subst[1],
            "concentration_pct": r.uniform(0.1, 5.0) if i % 3 == 0 else 0.0,
            "component": subst[2],
            "regulation": subst[3],
            "list_type": "monitored",
            "status": "active",
            "notes": "",
        }
        product_substances.append(ps)

    # ======== product_regulated_categories ========
    product_reg_cats = []
    categories = [
        ("Kids Sleepwear", "UK", ["BS 5722"]),
        ("Toys", "EU", ["CE 2009/48/EC"]),
        ("Electronics", "US", ["FCC"]),
    ]
    for i, prod in enumerate(products[:20]):
        cat = r.choice(categories)
        prc = {
            "sku": prod["sku"],
            "category_id": f"REGCAT-{i:03d}",
            "category_name": cat[0],
            "region": cat[1],
            "regulations": json.dumps(cat[2]),
            "compliance_status": r.choice(["compliant", "review"]),
            "test_required": r.choice([True, False]),
            "last_audit_date": g.days_ago(r.randint(30, 365)),
            "notes": "",
        }
        product_reg_cats.append(prc)

    return {
        "product_tech_pack": tech_packs,
        "bill_of_materials": boms,
        "material_library": lib_materials,
        "material_batches": batches,
        "dye_lots": dye_lots,
        "fabric_specs": fabric_specs,
        "product_specifications": product_specs,
        "candidate_materials": candidate_mats,
        "co_development_projects": codev_projects,
        "product_change_requests": change_reqs,
        "product_substances": product_substances,
        "product_regulated_categories": product_reg_cats,
    }
