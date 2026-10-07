"""PIM data: attributes, product attribute values, claims, and EPR data fields."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    fake = g.fake

    # Get products by category to populate attributes
    products = g.master("products")
    categories = sorted(set(p["category"] for p in products))

    # Create attributes for each category
    attributes = []
    attr_id_counter = 1
    category_attributes = {}

    attribute_specs = {
        "Womenswear": [
            ("Material Composition", "text", "80/20 cotton-poly blend, 100% silk, etc"),
            ("Care Instructions", "text", "Machine wash 30C, dry clean only, etc"),
            ("Size Fit", "text", "Runs small, true to size, runs large"),
            ("Weight", "numeric", "grams per unit"),
            ("Colour Range", "list", "Multiple sizes and colours available"),
            ("Seam Type", "text", "French seam, flat lock, standard"),
        ],
        "Home": [
            ("Material Composition", "text", "100% cotton, poly blend, ceramic"),
            ("Dimensions", "text", "Length x width x height in cm"),
            ("Capacity", "numeric", "litres or kg"),
            ("Energy Rating", "enum", "A++, A+, A, B, C"),
            ("Water Usage", "numeric", "litres per cycle"),
            ("Weight", "numeric", "kg"),
            ("Care Instructions", "text", "Dishwasher safe, hand wash only"),
            ("Warranty", "numeric", "Years coverage"),
        ],
        "Bedding": [
            ("Material Composition", "text", "100% Egyptian cotton, polyester mix"),
            ("Thread Count", "numeric", "400TC, 600TC, 1000TC"),
            ("Dimensions", "text", "Single, Double, King, Super King"),
            ("Care Instructions", "text", "Machine wash 40C"),
            ("Weight", "numeric", "kg per set"),
            ("Colour", "enum", "White, natural, cream, grey"),
        ],
        "Furniture": [
            ("Material Composition", "text", "Oak frame, upholstered in linen"),
            ("Dimensions", "text", "L x W x H in cm"),
            ("Assembly Required", "boolean", "Yes or No"),
            ("Weight Capacity", "numeric", "kg"),
            ("Care Instructions", "text", "Wipe clean, spot clean upholstery"),
            ("Warranty", "numeric", "Years"),
        ],
    }

    for category in categories:
        if category in attribute_specs:
            specs = attribute_specs[category]
        else:
            # Default attributes for other categories
            specs = [
                ("Material Composition", "text", "Material mix"),
                ("Dimensions", "text", "Size specifications"),
                ("Weight", "numeric", "kg"),
                ("Care Instructions", "text", "Care details"),
            ]

        cat_attrs = []
        for attr_name, attr_type, data_format in specs:
            attr_id = f"ATTR-{attr_id_counter:03d}"
            attributes.append({
                "attribute_id": attr_id,
                "name": attr_name,
                "attribute_type": attr_type,
                "category": category,
                "data_format": data_format,
                "is_mandatory": attr_name in ["Material Composition", "Dimensions", "Care Instructions"],
                "description": f"{attr_name} for {category}",
                "status": "active",
                "created_at": g.as_of - timedelta(days=r.randint(30, 365))
            })
            cat_attrs.append(attr_id)
            attr_id_counter += 1

        category_attributes[category] = cat_attrs

    # Create attribute groups (taxonomy)
    attribute_groups = []
    grp_id_counter = 1
    for category in categories[:5]:  # Create groups for main categories
        attrs_in_cat = category_attributes.get(category, [])
        if attrs_in_cat:
            group_id = f"GRP-{grp_id_counter:03d}"
            attribute_groups.append({
                "group_id": group_id,
                "name": f"{category}_Core",
                "category": category,
                "description": f"Core attributes for {category} products",
                "attribute_count": len(attrs_in_cat),
                "status": "active",
                "version": "1.0",
                "created_at": g.as_of - timedelta(days=r.randint(60, 180))
            })
            grp_id_counter += 1

    # Create product attributes (values for products)
    product_attributes = []

    for product in products[:300]:  # Limit to first 300 products
        sku = product["sku"]
        category = product["category"]
        attrs = category_attributes.get(category, [])

        # Some products have incomplete data (realistic)
        completeness = r.choice([0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0])

        for attr_id in attrs:
            if r.random() < completeness:
                # Generate plausible attribute values
                if "Material" in [a["name"] for a in attributes if a["attribute_id"] == attr_id]:
                    materials = ["100% cotton", "80/20 poly-cotton", "100% silk", "Linen blend", "Synthetic"]
                    value = r.choice(materials)
                elif "Dimension" in [a["name"] for a in attributes if a["attribute_id"] == attr_id]:
                    value = f"{r.randint(20, 200)} x {r.randint(20, 200)} cm"
                elif "Weight" in [a["name"] for a in attributes if a["attribute_id"] == attr_id]:
                    value = str(r.randint(100, 5000))
                elif "Care" in [a["name"] for a in attributes if a["attribute_id"] == attr_id]:
                    cares = ["Machine wash 30C", "Hand wash only", "Dry clean only", "Machine wash 40C"]
                    value = r.choice(cares)
                else:
                    value = f"Value_{r.randint(1, 100)}"

                product_attributes.append({
                    "sku": sku,
                    "attribute_id": attr_id,
                    "value": value,
                    "confidence": r.randint(75, 100),
                    "source": r.choices(["supplier", "internal", "marketplace"], [0.4, 0.4, 0.2])[0],
                    "last_updated": g.as_of - timedelta(days=r.randint(1, 90)),
                    "is_complete": True if r.random() < 0.9 else False
                })

    # Create product claims
    product_claims = []
    claim_id_counter = 1
    claim_types = ["organic", "recycled_content", "fair_trade", "sustainable", "ecolabel"]

    for product in products[:200]:  # Claims for first 200 products
        if r.random() < 0.3:  # 30% of products have claims
            sku = product["sku"]
            claim_type = r.choice(claim_types)
            claim_id = f"CLM-{claim_id_counter:06d}"

            claim_texts = {
                "organic": "GOTS certified organic",
                "recycled_content": "Contains 50% recycled materials",
                "fair_trade": "Fair Trade certified",
                "sustainable": "Made with sustainable practices",
                "ecolabel": "EU Ecolabel certified"
            }

            product_claims.append({
                "claim_id": claim_id,
                "sku": sku,
                "claim_type": claim_type,
                "claim_text": claim_texts[claim_type],
                "certification_type": r.choice(["GOTS", "OEKO-TEX", "FSC", "Fair Trade", "BLUESIGN"]),
                "has_evidence": r.choices([True, False], [0.7, 0.3])[0],
                "evidence_ref": f"CERT-{r.randint(1000, 9999)}" if r.random() < 0.7 else None,
                "status": r.choices(["active", "pending_review", "insufficient_evidence"], [0.8, 0.15, 0.05])[0],
                "created_at": g.as_of - timedelta(days=r.randint(1, 180)),
                "updated_at": g.as_of - timedelta(days=r.randint(1, 60))
            })
            claim_id_counter += 1

    # Create EPR data fields (which EPR data we collect)
    epr_data_fields = []
    epr_field_counter = 1

    epr_specs = [
        ("Unit Weight", "Textiles", "numeric", "Weight in grams for EPR reporting", "kg"),
        ("Material Composition", "Textiles", "text", "Percentage breakdown by material", ""),
        ("Recyclability", "Textiles", "enum", "Is product recyclable", ""),
        ("Pack Material Weight", "Home", "numeric", "Packaging weight for EPR", "kg"),
        ("Product Lifespan", "Home", "numeric", "Expected years in use", "years"),
        ("Repair Service Available", "Home", "boolean", "Can product be repaired", ""),
        ("Recycled Content %", "Womenswear", "numeric", "Percentage of recycled input", "%"),
        ("Biodegradability", "Bedding", "boolean", "Is product biodegradable", ""),
        ("Certification Details", "Furniture", "text", "Relevant certifications held", ""),
    ]

    for field_name, category, data_type, description, unit in epr_specs:
        field_id = f"EPR-{epr_field_counter:03d}"

        # Coverage varies by category
        coverage = r.randint(40, 100) if r.random() < 0.7 else r.randint(20, 50)

        epr_data_fields.append({
            "field_id": field_id,
            "field_name": field_name,
            "category": category,
            "data_type": data_type,
            "description": description,
            "is_held": coverage >= 50,
            "coverage_pct": coverage,
            "unit": unit,
            "created_at": g.as_of - timedelta(days=r.randint(30, 365))
        })
        epr_field_counter += 1

    return {
        "attributes": attributes,
        "attribute_groups": attribute_groups,
        "product_attributes": product_attributes,
        "product_claims": product_claims,
        "epr_data_fields": epr_data_fields
    }
