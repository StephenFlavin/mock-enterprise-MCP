"""Background packaging data: pack specs, materials, quotes and tech packs."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    fake = g.fake

    # Get products and styles from master
    products = g.master("products")[:50]  # Take first 50 for volume
    styles = list({p["style_id"] for p in products})[:30]
    suppliers = [s["supplier_id"] for s in g.master("suppliers")][:20]

    # Define material types and their properties
    materials_info = {
        "corrugated": {"name": "Corrugated Cardboard", "base_cost": 0.45, "recycled_pct": 40, "recyclable": True},
        "moulded_pulp": {"name": "Moulded Pulp", "base_cost": 0.60, "recycled_pct": 80, "recyclable": True},
        "recycled_plastic": {"name": "Recycled Plastic", "base_cost": 0.85, "recycled_pct": 100, "recyclable": True},
        "rigid_plastic": {"name": "Rigid Plastic", "base_cost": 1.20, "recycled_pct": 15, "recyclable": False},
        "kraft": {"name": "Kraft Paper", "base_cost": 0.35, "recycled_pct": 60, "recyclable": True},
        "polybag": {"name": "Polybag", "base_cost": 0.15, "recycled_pct": 20, "recyclable": False},
    }

    pack_specs, pack_materials, pack_quotes, tech_packs, ecom_specs = [], [], [], [], []
    pack_changes, material_weights, pack_options, carton_specs, channel_costs, portfolio = [], [], [], [], [], []

    # Create material specs
    for i, (mat_key, mat_info) in enumerate(materials_info.items()):
        mat_id = f"MAT-{i + 1:06d}"
        pack_materials.append({
            "material_id": mat_id,
            "material_name": mat_info["name"],
            "supplier_id": r.choice(suppliers),
            "base_weight_gbp": r.uniform(5, 25),
            "recycled_content_pct": mat_info["recycled_pct"],
            "unit_cost_gbp": round(mat_info["base_cost"], 2),
            "standard_volume": 100000,
            "lead_time_days": r.randint(14, 60),
            "status": "active"
        })

    # Create pack specs for products
    materials_list = list(materials_info.keys())
    pack_types_list = ["carton", "pouch", "rigid_box", "tray", "moulded_pulp", "bag", "polybag"]

    for i, product in enumerate(products):
        spec_id = f"PKS-{i + 1:06d}"
        material = r.choice(materials_list)
        mat_info = materials_info[material]
        pack_type = r.choice(pack_types_list)

        # Vary cost based on material and size
        base_cost = mat_info["base_cost"]
        unit_cost = round(base_cost * r.uniform(0.9, 1.3), 2)

        pallet_fill = r.randint(100, 800)

        pack_specs.append({
            "pack_spec_id": spec_id,
            "sku": product["sku"],
            "style_id": product["style_id"],
            "pack_type": pack_type,
            "material": material,
            "primary_supplier_id": r.choice(suppliers),
            "height_mm": r.randint(50, 300),
            "width_mm": r.randint(50, 300),
            "depth_mm": r.randint(30, 200),
            "wall_thickness_mm": round(r.uniform(1, 5), 1),
            "weight_gbp": round(r.uniform(5, 100), 1),
            "unit_cost_gbp": unit_cost,
            "pallet_fill_units": pallet_fill,
            "recycled_content_pct": mat_info["recycled_pct"],
            "recyclable": mat_info["recyclable"],
            "status": r.choice(["active", "active", "active", "testing"]),
            "created_at": g.days_ago(r.randint(30, 730)),
            "updated_at": g.days_ago(r.randint(0, 30))
        })

    # Create pack quotes (3-5 per spec)
    for i, spec in enumerate(pack_specs[:30]):  # Just first 30 for quotes
        for q in range(r.randint(2, 4)):
            quote_id = f"QT-{len(pack_quotes) + 1:06d}"
            supplier_id = r.choice(suppliers)
            cost = round(spec["unit_cost_gbp"] * r.uniform(0.95, 1.10), 2)
            volume = r.choice([100000, 200000, 400000, 500000])

            pack_quotes.append({
                "quote_id": quote_id,
                "pack_spec_id": spec["pack_spec_id"],
                "supplier_id": supplier_id,
                "unit_cost_gbp": cost,
                "volume_units": volume,
                "moq_units": volume // 10,
                "lead_time_days": r.randint(14, 60),
                "valid_from": g.days_ago(r.randint(0, 10)),
                "valid_until": g.days_ago(-r.randint(30, 90)),
                "notes": r.choice(["Standard quote", "Volume discount", "Trial offer", ""])
            })

    # Create tech packs for some styles
    for i, style_id in enumerate(styles[:20]):
        tech_pack_id = f"TP-{i + 1:06d}"

        seam_strength = round(r.uniform(20, 100), 1)
        construction = f"Double-stitched with reinforced seams at stress points. Target seam strength {seam_strength}N."

        tech_packs.append({
            "tech_pack_id": tech_pack_id,
            "style_id": style_id,
            "construction_details": construction,
            "seam_strength_n": seam_strength,
            "water_resistance_spec": r.choice(["IP54", "IP65", "IP67", "Not waterproof"]),
            "zip_pull_strength_n": round(r.uniform(50, 150), 1) if "backpack" in style_id.lower() or r.random() > 0.7 else None,
            "test_requirements": "Drop test: 1m; Crush test: 50kg; Seam test: 80N min",
            "notes": "See attached construction drawings for detail specs",
            "status": "active",
            "updated_at": g.days_ago(r.randint(0, 60))
        })

    # Create e-commerce specs
    for i, product in enumerate(products[:25]):
        ecom_spec_id = f"EC-{i + 1:06d}"

        ecom_specs.append({
            "ecom_spec_id": ecom_spec_id,
            "sku": product["sku"],
            "pack_type": r.choice(["carton with padding", "poly mailer", "rigid box", "bubble wrap"]),
            "protective_material": r.choice(["air pillows", "kraft paper", "bubble wrap", "expanded foam", "tissue"]),
            "unit_cost_gbp": round(r.uniform(0.8, 2.5), 2),
            "packing_notes": f"Wrap in {r.choice(['kraft paper', 'bubble wrap'])}. Use large enough box.",
            "damage_rate_pct": round(r.uniform(0.5, 3.5), 1),
            "updated_at": g.days_ago(r.randint(0, 30))
        })

    # Create pack changes
    for i, spec in enumerate(pack_specs[:15]):
        for c in range(r.randint(1, 3)):
            change_id = f"CHG-{len(pack_changes) + 1:06d}"
            change_type = r.choice(["dimension", "material", "cost", "supplier", "thickness"])
            old_val = f"Previous: {r.randint(100, 300)}mm" if change_type == "dimension" else f"Was {round(r.uniform(0.3, 1.5), 2)}"
            new_val = f"New: {r.randint(100, 300)}mm" if change_type == "dimension" else f"Now {round(r.uniform(0.3, 1.5), 2)}"

            pack_changes.append({
                "change_id": change_id,
                "pack_spec_id": spec["pack_spec_id"],
                "change_type": change_type,
                "old_value": old_val,
                "new_value": new_val,
                "reason": r.choice(["Cost optimization", "Supplier change", "Quality improvement", "Sustainability", "Testing"]),
                "changed_by": "EMP-00123",
                "changed_at": g.days_ago(r.randint(1, 90))
            })

    # Create material weights by market
    for i, product in enumerate(products[:20]):
        for market in ["UK", "FR", "DE", "ES"]:
            weight_id = f"WGT-{len(material_weights) + 1:06d}"

            material_weights.append({
                "weight_record_id": weight_id,
                "sku": product["sku"],
                "material": r.choice(list(materials_info.keys())),
                "market_country": market,
                "weight_gbp": round(r.uniform(5, 100), 1),
                "updated_at": g.days_ago(r.randint(0, 60))
            })

    # Create pack options (alternatives)
    for i, product in enumerate(products[:15]):
        base_pack_id = f"PKS-{i + 1:06d}"
        for opt in range(r.randint(1, 3)):
            option_id = f"PKO-{len(pack_options) + 1:06d}"
            option_name = r.choice(["rigid box", "flexible pouch", "carton", "moulded pulp", "paper bag"])

            pack_options.append({
                "option_id": option_id,
                "product_id": product["sku"],
                "option_name": option_name,
                "pack_type": option_name,
                "material": r.choice(list(materials_info.keys())),
                "unit_cost_gbp": round(r.uniform(0.3, 2.0), 2),
                "pallet_fill_units": r.randint(100, 600),
                "shelf_appeal": r.choice(["high", "medium", "low"]),
                "protection_level": r.choice(["high", "medium", "low"]),
                "recyclability": r.choice(["fully recyclable", "partially recyclable", "not recyclable"]),
                "notes": f"Alternative to {option_name}"
            })

    # Create carton specs
    for i, spec in enumerate(pack_specs[:20]):
        if spec["pack_type"] in ["carton", "rigid_box"]:
            carton_id = f"CTN-{len(carton_specs) + 1:06d}"

            carton_specs.append({
                "carton_id": carton_id,
                "pack_spec_id": spec["pack_spec_id"],
                "height_mm": spec["height_mm"],
                "width_mm": spec["width_mm"],
                "depth_mm": spec["depth_mm"],
                "wall_thickness_mm": spec["wall_thickness_mm"],
                "unit_cost_gbp": spec["unit_cost_gbp"],
                "pallet_units": spec["pallet_fill_units"],
                "crush_strength_kpa": round(r.uniform(20, 100), 1),
                "status": "active",
                "updated_at": g.days_ago(r.randint(0, 30))
            })

    # Create channel costs
    for i, product in enumerate(products[:25]):
        for channel in ["stores", "online", "wholesale"]:
            channel_cost_id = f"CC-{len(channel_costs) + 1:06d}"

            cost_per_order = round(r.uniform(0.5, 3.0), 2)
            cost_per_unit = round(cost_per_order / r.randint(5, 30), 2)

            channel_costs.append({
                "channel_cost_id": channel_cost_id,
                "sku": product["sku"],
                "channel": channel,
                "cost_gbp_per_order": cost_per_order,
                "cost_gbp_per_unit": cost_per_unit,
                "packing_labour_pct": round(r.uniform(10, 40), 1),
                "updated_at": g.days_ago(r.randint(0, 30))
            })

    # Create packaging portfolio
    for i, product in enumerate(products[:30]):
        portfolio_id = f"POR-{i + 1:06d}"

        portfolio.append({
            "portfolio_id": portfolio_id,
            "sku": product["sku"],
            "style_id": product["style_id"],
            "primary_pack_type": r.choice(pack_types_list),
            "alt_pack_types": ", ".join(r.sample(pack_types_list, k=2)),
            "sustainability_notes": r.choice([
                "75% recycled content, fully recyclable",
                "Minimal material use",
                "Compostable protective materials",
                "Refillable container option available",
                "Uses virgin plastic (priority for replacement)"
            ]),
            "updated_at": g.days_ago(r.randint(0, 60))
        })

    return {
        "pack_specs": pack_specs,
        "pack_materials": pack_materials,
        "pack_quotes": pack_quotes,
        "tech_packs": tech_packs,
        "ecommerce_specs": ecom_specs,
        "pack_change_history": pack_changes,
        "material_weights_by_market": material_weights,
        "pack_options": pack_options,
        "carton_specs": carton_specs,
        "channel_packaging_costs": channel_costs,
        "packaging_portfolio": portfolio
    }
