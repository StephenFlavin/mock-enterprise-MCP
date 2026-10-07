"""Marketplace data: listings, rejections, policies, fees, requirements and category trees.

Story: 340 listings rejected this week (5 seeded + 335 generated), grouped by error; German/French home-appliance
requirements (DE strictest); DE/FR commission rises and DE returns/video policies this quarter.
"""
from datetime import timedelta

MARKETS = [("MKT-DE", 0), ("MKT-FR", 13), ("MKT-UK", 26)]
LANG = {"MKT-DE": 0, "MKT-FR": 1, "MKT-UK": 2}

# (idx, parent idx, pim category, [DE name, FR name, UK name])
NODES = [
    (0, None, "home", ["Home & Living"]),
    (1, 0, "kitchen", ["Kitchen & Dining"]),
    (2, 1, "kitchen", ["Small Kitchen Appliances"]),
    (3, 1, "kitchen", ["Cookware"]),
    (4, 1, "kitchen", ["Drinkware"]),
    (5, 0, "bedding", ["Bedding & Bath"]),
    (6, 5, "bedding", ["Bedding"]),
    (7, 5, "bedding", ["Towels"]),
    (8, 0, "electrics", ["Electrics"]),
    (9, 8, "electrics", ["Smart Home"]),
    (10, 8, "electrics", ["Lighting"]),
    (11, 8, "electrics", ["Fans & Heating"]),
    (12, 0, "home", ["Storage & Organisation"]),
]
LOCAL = {  # German / French local names where they differ from the English name
    "MKT-DE": ["Heim & Wohnen", "Kueche", "Kleine Kuechengeraete", "Kochgeschirr", "Trinkgefaesse", "Bettwaren & Bad",
               "Bettwaesche", "Handtuecher", "Elektro", "Smart Home", "Beleuchtung", "Ventilatoren & Heizen", "Aufbewahrung"],
    "MKT-FR": ["Maison", "Cuisine", "Petit electromenager", "Batterie de cuisine", "Verres et tasses", "Linge de maison",
               "Literie", "Serviettes", "Electricite", "Maison connectee", "Eclairage", "Ventilateurs et chauffage", "Rangement"],
}
# master product category -> category node index
PRODUCT_NODE = {"Cookware": 3, "Drinkware": 4, "Small Appliances": 2, "Bedding": 6, "Towels": 7, "Smart Home": 9,
                "Lighting": 10, "Storage": 12, "Audio": 8, "Personal Care": 11}
APPLIANCE = 2  # seeded in full (content + listing requirements)


def cat_id(mkt_base, idx):
    return f"MKTCAT-{mkt_base + idx:06d}"


# rejection plan for this week: (code, text, field, fixable_in_bulk, listings, suggested fix)
PLAN = [
    ("MISSING_IMAGE", "Missing product images", "images", False, 66, "Needs photography or supplier images; cannot be fixed from PIM data"),
    ("INCOMPLETE_ATTRIBUTES", "Required attributes missing", "ean", True, 48, "Fill EAN from PIM in a bulk attribute file"),
    ("INCOMPLETE_ATTRIBUTES", "Required attributes missing", "country_of_origin", True, 34, "Fill country of origin from PIM in a bulk attribute file"),
    ("INCOMPLETE_ATTRIBUTES", "Required attributes missing", "weight", True, 19, "Fill weight from PIM in a bulk attribute file"),
    ("INCOMPLETE_ATTRIBUTES", "Required attributes missing", "material", True, 13, "Fill material from PIM in a bulk attribute file"),
    ("INCOMPLETE_TITLE", "Product title incomplete or too short", "title", True, 59, "Rebuild title as brand + product type + key feature + size/colour"),
    ("MISSING_DESCRIPTION", "Description missing or too short", "description", True, 35, "Load the PIM long description (minimum 100 characters)"),
    ("WRONG_CATEGORY", "Category does not match product type", "category_id", False, 20, "Review category mapping listing by listing"),
    ("BRAND_MISMATCH", "Brand name conflicts", "brand", False, 17, "Brand owner approval needed from the marketplace"),
    ("PRICE_MISMATCH", "Price outside acceptable range", "price", False, 14, "Pricing review needed"),
    ("DUPLICATE_LISTING", "Duplicate listing exists", "listing", False, 7, "Merge or delist the duplicate listing"),
    ("POLICY_VIOLATION", "Violates marketplace policy", "policy", False, 3, "Check policy notice and edit content"),
]
# extra reasons added to listings that already have a different primary reason
SECONDARY = [("MISSING_IMAGE", 14), ("INCOMPLETE_TITLE", 6), ("MISSING_DESCRIPTION", 9), ("INCOMPLETE_ATTRIBUTES:ean", 8)]

REQ_BASE = {  # pim category -> (attribute, mandatory) for generated categories
    "kitchen": [("brand", 1), ("ean", 1), ("weight", 1), ("dimensions", 1), ("material", 1), ("colour", 0), ("country_of_origin", 1)],
    "bedding": [("brand", 1), ("ean", 1), ("material", 1), ("care_instructions", 1), ("dimensions", 1), ("colour", 0), ("country_of_origin", 1)],
    "electrics": [("brand", 1), ("ean", 1), ("weight", 1), ("voltage_wattage", 1), ("warranty", 1), ("colour", 0), ("country_of_origin", 1)],
    "home": [("brand", 1), ("ean", 1), ("dimensions", 1), ("material", 0), ("colour", 0), ("country_of_origin", 1)],
}
REQ_FMT = {"brand": ("Max 50 chars, no special characters", "Philips"), "ean": ("13 digits", "5012345678900"),
           "weight": ("Number + unit in kg", "1.5 kg"), "dimensions": ("length x width x height cm", "30 x 25 x 20 cm"),
           "material": ("Primary materials, comma separated", "Stainless steel"), "colour": ("Max 30 chars", "Black"),
           "country_of_origin": ("ISO 3166 two-letter code", "CN"), "care_instructions": ("Free text, wash symbols", "Machine wash 40C"),
           "voltage_wattage": ("Volts and watts, e.g. 230V 2200W", "230V 2200W"), "warranty": ("Years or months", "2 years")}
PIM_ATTRS = {  # PIM attribute definitions per PIM category (no energy label, WEEE, repairability, UKCA, voltage ...)
    "home": ["brand", "dimensions", "colour", "material", "country_of_origin", "warranty", "sku", "ean", "weight"],
    "kitchen": ["brand", "weight", "dimensions", "colour", "material", "country_of_origin", "warranty", "sku", "ean"],
    "bedding": ["brand", "dimensions", "colour", "material", "care_instructions", "country_of_origin", "sku", "ean", "weight"],
    "electrics": ["brand", "weight", "dimensions", "colour", "country_of_origin", "warranty", "sku", "ean"],
}
PIM_DESC = {"brand": "Product brand name", "weight": "Product weight in kg", "dimensions": "Length x width x height in cm",
            "colour": "Product colour", "material": "Primary material composition", "country_of_origin": "ISO country code of origin",
            "warranty": "Warranty period and terms", "sku": "Internal SKU identifier", "ean": "European Article Number",
            "care_instructions": "Care and washing instructions"}


def generate(g):
    r = g.rng
    as_of = g.as_of

    # ---- categories
    categories = []
    for mkt, base in MARKETS:
        for idx, parent, pim, names in NODES:
            categories.append({
                "category_id": cat_id(base, idx), "marketplace_id": mkt,
                "parent_category_id": cat_id(base, parent) if parent is not None else None,
                "name": names[0], "local_name": LOCAL[mkt][idx] if mkt in LOCAL else names[0],
                "pim_category_match": pim,
            })
    base_of = dict(MARKETS)

    # ---- listings and rejections
    products = [p for p in g.master("products")
                if p["category"] in PRODUCT_NODE and p["sku"] not in ("K-1700", "PF-220")]
    pairs = [(p, m) for p in products for m, _ in MARKETS]
    r.shuffle(pairs)
    n_rej = 335
    n_old = 60
    n_other = 120
    listings, rejections = [], []

    def new_listing(p, mkt, status, rejected_at=None, rej_count=0, has_images=True, short_title=False, short_desc=False, attrs=None):
        lid = f"LST-{len(listings):06d}"
        base = base_of[mkt]
        node = PRODUCT_NODE[p["category"]]
        title = p["name"] if not short_title else p["name"].split()[0]
        sub = as_of - timedelta(days=r.randint(8, 120))
        listings.append({
            "listing_id": lid, "sku": p["sku"], "marketplace_id": mkt, "category_id": cat_id(base, node),
            "status": status, "title": title,
            "description_length": r.randint(0, 80) if short_desc else r.randint(150, 900),
            "has_images": has_images, "has_video": r.random() < 0.25,
            "attributes_complete": attrs if attrs is not None else r.randint(85, 100),
            "submitted_at": sub, "rejected_at": rejected_at, "rejection_count": rej_count,
            "updated_at": rejected_at or sub,
        })
        return lid

    # primary reason slots, shuffled
    slots = []
    for code, text, field, bulk, n, fix in PLAN:
        slots += [(code, text, field, bulk, fix)] * n
    r.shuffle(slots)
    plan_by_key = {f"{c}:{f}": (c, t, f, b, x) for c, t, f, b, _, x in PLAN for _ in [0]}
    reasons_of = []
    for i in range(n_rej):
        reasons_of.append([slots[i]])
    for key, n in SECONDARY:
        c = key.split(":")[0]
        pk = key if ":" in key else [k for k in plan_by_key if k.startswith(c + ":")][0]
        slot = plan_by_key[pk]
        done = 0
        while done < n:
            lst = reasons_of[r.randrange(n_rej)]
            if all(s[0] != c for s in lst):
                lst.append(slot)
                done += 1
    for i in range(n_rej):
        p, mkt = pairs[i]
        rs = reasons_of[i]
        codes = {s[0] for s in rs}
        when = as_of - timedelta(days=r.randint(0, 5), hours=r.randint(0, 23), minutes=r.randint(0, 59))
        lid = new_listing(p, mkt, "rejected", when, r.randint(1, 3), has_images="MISSING_IMAGE" not in codes,
                          short_title="INCOMPLETE_TITLE" in codes, short_desc="MISSING_DESCRIPTION" in codes,
                          attrs=r.randint(35, 70) if "INCOMPLETE_ATTRIBUTES" in codes else None)
        for code, text, field, bulk, fix in rs:
            rejections.append({"rejection_id": f"REJ-{len(rejections):06d}", "listing_id": lid, "sku": p["sku"],
                               "reason_code": code, "reason_text": text, "field_name": field, "rejected_at": when,
                               "is_fixable_in_bulk": bulk, "suggested_fix": fix})
    # older rejections (fixed since): not part of this week
    for i in range(n_rej, n_rej + n_old):
        p, mkt = pairs[i]
        when = as_of - timedelta(days=r.randint(14, 70), hours=r.randint(0, 23))
        lid = new_listing(p, mkt, "active", when, 1)
        code, text, field, bulk, _, fix = r.choice(PLAN[:8])
        rejections.append({"rejection_id": f"REJ-{len(rejections):06d}", "listing_id": lid, "sku": p["sku"],
                           "reason_code": code, "reason_text": text, "field_name": field, "rejected_at": when,
                           "is_fixable_in_bulk": bulk, "suggested_fix": fix})
    for i in range(n_rej + n_old, n_rej + n_old + n_other):
        p, mkt = pairs[i]
        new_listing(p, mkt, r.choices(["active", "draft", "in_review", "paused"], [70, 12, 12, 6])[0])

    # ---- requirements (appliance category is seeded in full)
    listing_reqs, content_reqs = [], []
    for mkt, base in MARKETS:
        strict = {"MKT-DE": 1.0, "MKT-FR": 0.7, "MKT-UK": 0.4}[mkt]
        for idx, parent, pim, names in NODES:
            if idx in (0, APPLIANCE):
                continue
            cid = cat_id(base, idx)
            for attr, mand in REQ_BASE[pim]:
                m = bool(mand) and not (mkt == "MKT-UK" and attr in ("country_of_origin", "dimensions"))
                fmt, ex = REQ_FMT[attr]
                listing_reqs.append({
                    "requirement_id": f"REQ-{len(listing_reqs):06d}", "marketplace_id": mkt, "category_id": cid,
                    "attribute_name": attr, "is_mandatory": m, "description": f"{attr.replace('_', ' ').capitalize()} for this category",
                    "format_rules": fmt, "examples": ex, "effective_date": as_of - timedelta(days=300), "policy_id": None})
            for ctype, req, mn, mx, mand in [
                ("title", "Brand, product type and key feature", 20 if mkt != "MKT-DE" else 30, 100 if mkt != "MKT-DE" else 150, True),
                ("description", "Full product details and benefits", 100 if mkt != "MKT-DE" else 150, 2000, True),
                ("images", f"At least {3 if mkt == 'MKT-UK' else 5} images, white background", 3 if mkt == "MKT-UK" else 5, 20, mkt != "MKT-UK"),
                ("attributes", "All mandatory attributes completed", 6, 50, True)]:
                content_reqs.append({
                    "content_req_id": f"CONT-{len(content_reqs):06d}", "marketplace_id": mkt, "category_id": cid,
                    "content_type": ctype, "requirement": req, "min_length": mn, "max_length": mx, "mandatory": mand,
                    "examples": None})

    # ---- fee schedule: DE 10 -> 12 from 65 days ago, FR 9 -> 11 from 51 days ago, UK flat 10.5
    fulfil = {"home": 1.75, "kitchen": 1.50, "bedding": 1.25, "electrics": 1.60}
    fees = []
    for mkt, base in MARKETS:
        old_c, new_c, new_days, old_fix, new_fix = {"MKT-DE": (10.0, 12.0, 65, 0.40, 0.50),
                                                    "MKT-FR": (9.0, 11.0, 51, 0.40, 0.50),
                                                    "MKT-UK": (10.5, 10.5, 200, 0.50, 0.50)}[mkt]
        for idx, parent, pim, names in NODES:
            cid = cat_id(base, idx)
            ful = fulfil[pim] + (0.10 if mkt != "MKT-UK" else 0)
            old_days = 240
            if mkt != "MKT-UK":
                fees.append({"fee_id": f"FEE-{len(fees):06d}", "marketplace_id": mkt,
                             "effective_date": as_of - timedelta(days=old_days), "category_id": cid, "pim_category": pim,
                             "commission_pct": old_c, "fixed_fee_gbp": old_fix, "fulfillment_fee_gbp": ful,
                             "previous_commission_pct": None})
            fees.append({"fee_id": f"FEE-{len(fees):06d}", "marketplace_id": mkt,
                         "effective_date": as_of - timedelta(days=new_days), "category_id": cid, "pim_category": pim,
                         "commission_pct": new_c, "fixed_fee_gbp": new_fix, "fulfillment_fee_gbp": ful,
                         "previous_commission_pct": old_c})

    # ---- PIM attribute definitions per PIM category
    pim_attrs = []
    for pim, attrs in PIM_ATTRS.items():
        for a in attrs:
            pim_attrs.append({
                "attribute_id": f"ATTR-{len(pim_attrs):06d}", "attribute_name": a, "pim_category": pim,
                "data_type": "number" if a == "weight" else "text",
                "is_mandatory": a in ("brand", "sku", "ean", "country_of_origin"), "description": PIM_DESC[a]})

    return {
        "marketplace_listings": listings,
        "listing_rejections": rejections,
        "marketplace_categories": categories,
        "marketplace_policies": [],
        "marketplace_fee_schedule": fees,
        "marketplace_listing_requirements": listing_reqs,
        "marketplace_content_requirements": content_reqs,
        "pim_attributes": pim_attrs,
    }
