"""Marketplace data: listings, rejections, policies, fees, requirements and category trees."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    fake = g.fake

    # Marketplaces we care about
    marketplaces = [
        {"marketplace_id": "MKT-DE", "name": "German Marketplace", "country": "DE"},
        {"marketplace_id": "MKT-FR", "name": "French Marketplace", "country": "FR"},
        {"marketplace_id": "MKT-UK", "name": "UK Marketplace", "country": "GB"},
    ]

    # PIM categories and their marketplace mappings
    pim_cats = ["home", "kitchen", "bedding", "electrics"]

    # Get some real SKUs from master
    skus = [p["sku"] for p in g.master("products")[:300]]

    listings = []
    rejections = []
    categories = []
    policies = []
    fee_schedule = []
    listing_requirements = []
    content_requirements = []
    pim_attributes = []

    # 1. Create marketplace categories
    cat_count = 0
    for mkt in marketplaces:
        for pim_cat in pim_cats:
            parent_id = None
            for level in range(3):
                cat_id = f"MKTCAT-{cat_count:06d}"
                cat_count += 1
                categories.append({
                    "category_id": cat_id,
                    "marketplace_id": mkt["marketplace_id"],
                    "parent_category_id": parent_id,
                    "name": f"{pim_cat.title()} - Level {level}",
                    "local_name": f"{pim_cat.title()} (L{level})" if level > 0 else pim_cat.title(),
                    "pim_category_match": pim_cat if level == 0 else None,
                })
                if level == 0:
                    parent_id = cat_id

    # 2. Create marketplace listings
    list_id = 0
    rejected_reason_codes = [
        ("MISSING_IMAGE", "Missing product images", "images", False),
        ("INCOMPLETE_TITLE", "Product title incomplete or too short", "title", True),
        ("MISSING_DESCRIPTION", "Description missing or too short", "description", True),
        ("WRONG_CATEGORY", "Category does not match product type", "category_id", False),
        ("INCOMPLETE_ATTRIBUTES", "Required attributes missing", "attributes", False),
        ("BRAND_MISMATCH", "Brand name conflicts", "brand", False),
        ("POLICY_VIOLATION", "Violates marketplace policy", None, False),
        ("DUPLICATE_LISTING", "Duplicate listing exists", None, False),
        ("PRICE_MISMATCH", "Price outside acceptable range", "price", False),
    ]

    for i, sku in enumerate(skus[:400]):  # 400 listings
        mkt = r.choice(marketplaces)
        cat = r.choice([c for c in categories if c["marketplace_id"] == mkt["marketplace_id"]])

        # Determine if rejected (340 rejections, 60 listings)
        is_rejected = r.random() < (340 / 400)

        listing_id = f"LST-{list_id:06d}"
        list_id += 1

        # Date when rejected (within last 7 days)
        rejected_date = None
        if is_rejected:
            days_back = r.randint(0, 6)
            rejected_date = g.as_of - timedelta(days=days_back, hours=r.randint(0, 23), minutes=r.randint(0, 59))

        submitted_date = g.as_of - timedelta(days=r.randint(1, 30))

        rej_count = 0
        if is_rejected:
            rej_count = r.randint(1, 4)

        listings.append({
            "listing_id": listing_id,
            "sku": sku,
            "marketplace_id": mkt["marketplace_id"],
            "category_id": cat["category_id"],
            "status": "rejected" if is_rejected else r.choices(["active", "draft", "in_review"], [60, 20, 20])[0],
            "title": f"Product {sku}" + (r.choice([" - Premium", " - Standard", " Set"]) if r.random() < 0.3 else ""),
            "description_length": r.randint(50, 500) if not is_rejected else r.randint(0, 100),
            "has_images": False if is_rejected and r.random() < 0.5 else True,
            "has_video": r.random() < 0.2,
            "attributes_complete": 50 if is_rejected else r.randint(80, 100),
            "submitted_at": submitted_date,
            "rejected_at": rejected_date,
            "rejection_count": rej_count,
            "updated_at": rejected_date or submitted_date,
        })

        # Add rejection reasons for rejected listings
        if is_rejected:
            reasons_applied = set()
            num_reasons = r.randint(1, 3)
            for _ in range(num_reasons):
                code, text, field, bulk_fixable = r.choice(rejected_reason_codes)
                if code not in reasons_applied:
                    reasons_applied.add(code)
                    rej_id = f"REJ-{len(rejections):06d}"
                    rejections.append({
                        "rejection_id": rej_id,
                        "listing_id": listing_id,
                        "sku": sku,
                        "reason_code": code,
                        "reason_text": text,
                        "field_name": field,
                        "rejected_at": rejected_date,
                        "is_fixable_in_bulk": bulk_fixable,
                    })

    # 3. Create marketplace policies
    policy_types = ["commission_fee", "returns", "listing_requirements", "seller_agreement", "other"]
    for i in range(8):
        policy_id = f"POL-{i:06d}"
        mkt = r.choice(marketplaces)
        policy_type = r.choice(policy_types)
        days_ago = r.randint(1, 90)

        if policy_type == "commission_fee":
            desc = f"Commission changed from 10% to 12% for {r.choice(['home', 'kitchen', 'bedding'])} category"
            impact = "Reduces margins by 2% on affected categories"
        elif policy_type == "returns":
            desc = "Extended return window from 30 to 60 days"
            impact = "Increases reverse logistics costs"
        else:
            desc = f"New {policy_type.replace('_', ' ')} policy effective"
            impact = "Review required for compliance"

        policies.append({
            "policy_id": policy_id,
            "marketplace_id": mkt["marketplace_id"],
            "policy_type": policy_type,
            "effective_date": g.as_of - timedelta(days=days_ago),
            "description": desc,
            "impact_summary": impact,
            "previous_policy": "See marketplace announcements" if policy_type == "commission_fee" else None,
            "announced_at": g.as_of - timedelta(days=days_ago + r.randint(1, 14)),
        })

    # 4. Create marketplace fee schedules
    fee_id = 0
    for mkt in marketplaces:
        for cat in categories:
            if cat["marketplace_id"] == mkt["marketplace_id"]:
                commission = r.uniform(8, 15)
                prev_commission = commission - r.uniform(-2, 2)

                for d in range(2):  # Current and historical
                    fee_id_str = f"FEE-{fee_id:06d}"
                    fee_id += 1

                    fee_schedule.append({
                        "fee_id": fee_id_str,
                        "marketplace_id": mkt["marketplace_id"],
                        "effective_date": g.as_of - timedelta(days=30*d),
                        "category_id": cat["category_id"],
                        "pim_category": cat["pim_category_match"],
                        "commission_pct": round(commission, 2),
                        "fixed_fee_gbp": 0.50 if d == 0 else 0.40,
                        "fulfillment_fee_gbp": round(r.uniform(0.5, 2.0), 2),
                        "previous_commission_pct": round(prev_commission, 2) if d == 0 else None,
                    })

    # 5. Create listing requirements
    req_attrs = ["brand", "weight", "dimensions", "colour", "material", "care_instructions",
                 "warranty", "country_of_origin", "sku", "ean"]
    req_id = 0
    for cat in categories[:20]:  # Sample for brevity
        for attr in r.sample(req_attrs, r.randint(5, 8)):
            req_id_str = f"REQ-{req_id:06d}"
            req_id += 1
            listing_requirements.append({
                "requirement_id": req_id_str,
                "marketplace_id": cat["marketplace_id"],
                "category_id": cat["category_id"],
                "attribute_name": attr,
                "is_mandatory": r.random() < 0.7,
                "description": f"Product {attr} is required for compliance",
                "format_rules": f"Max 50 chars, alphanumeric" if attr != "weight" else "Format: number + unit",
                "examples": "Cotton, Silk" if attr == "material" else "42 x 30 x 15 cm",
            })

    # 6. Create content requirements
    content_types = ["title", "description", "images", "video", "attributes", "SEO"]
    cont_id = 0
    for cat in categories[:15]:
        for ctype in r.sample(content_types, r.randint(3, 5)):
            cont_id_str = f"CONT-{cont_id:06d}"
            cont_id += 1

            if ctype == "title":
                min_len, max_len = 20, 100
                req = "Descriptive, include brand and key features"
            elif ctype == "description":
                min_len, max_len = 100, 2000
                req = "Full product details, benefits, specifications"
            elif ctype == "images":
                min_len, max_len = 3, 20
                req = f"Minimum {min_len} images, white background, 1200x1200px"
            elif ctype == "video":
                min_len, max_len = 1, 1
                req = "Product demonstration, max 2 minutes"
            elif ctype == "attributes":
                min_len, max_len = 10, 50
                req = "All mandatory attributes completed"
            else:  # SEO
                min_len, max_len = 10, 160
                req = "Include keywords, optimal length for search"

            content_requirements.append({
                "content_req_id": cont_id_str,
                "marketplace_id": cat["marketplace_id"],
                "category_id": cat["category_id"],
                "content_type": ctype,
                "requirement": req,
                "min_length": min_len,
                "max_length": max_len,
                "mandatory": r.random() < 0.8,
                "examples": "Sony WH-1000XM5 Wireless Headphones" if ctype == "title" else "Premium audio quality...",
            })

    # 7. Create PIM attributes
    for i, attr_name in enumerate(req_attrs):
        pim_attributes.append({
            "attribute_id": f"ATTR-{i:06d}",
            "attribute_name": attr_name,
            "pim_category": r.choice(pim_cats),
            "data_type": r.choice(["text", "number", "enum", "date", "image"]),
            "is_mandatory": r.random() < 0.5,
            "description": f"PIM attribute for {attr_name}",
        })

    return {
        "marketplace_listings": listings,
        "listing_rejections": rejections,
        "marketplace_categories": categories,
        "marketplace_policies": policies,
        "marketplace_fee_schedule": fee_schedule,
        "marketplace_listing_requirements": listing_requirements,
        "marketplace_content_requirements": content_requirements,
        "pim_attributes": pim_attributes,
    }
