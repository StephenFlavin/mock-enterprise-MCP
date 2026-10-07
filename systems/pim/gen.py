"""PIM data: taxonomy (attributes), attribute values for every product, claims. EPR fields and market rules are seeded."""
from datetime import timedelta

# (name, type, data_format, mandatory, canonical_name, marketplace_field, share of products holding a value)


def A(name, typ, fmt, mand=False, canon=None, mkt="", rate=0.9):
    return (name, typ, fmt, mand, canon or name, mkt, rate)


MAT = lambda rate=0.93, name="Material Composition": A(name, "text", "e.g. 100% cotton; Stainless steel", True, "Material Composition", "material", rate)
CARE = lambda rate=0.9, mand=True: A("Care Instructions", "text", "Machine wash 30C; Hand wash only", mand, "Care Instructions", "", rate)
WGT = lambda rate=0.9, name="Weight", mand=False: A(name, "numeric", "kg", mand, "Weight", "weight", rate)
COL = lambda rate=0.97, mand=False: A("Colour", "text", "Master colour name", mand, "Colour", "colour", rate)
DIM = lambda rate=0.72, name="Dimensions", mand=True: A(name, "text", "L x W x H in cm", mand, "Dimensions", "dimensions", rate)
WARR = lambda rate=0.6: A("Warranty", "numeric", "Years", False, "Warranty", "warranty", rate)

GARMENT = [MAT(), CARE(), WGT(), A("Fit", "text", "Slim; Regular; Oversized", False, "Fit", "", 0.8), COL()]

SPECS = {
    "Knitwear": [MAT(), CARE(), WGT(0.9, mand=True), A("Fit", "text", "Slim; Regular; Loose", False, "Fit", "", 0.8),
                 A("Sleeve Length", "text", "Short; 3/4; Long", False, rate=0.8), A("Neckline", "text", "Crew; V-neck; Turtleneck", False, rate=0.8),
                 A("Recycled Content %", "numeric", "Percentage recycled fibre", False, rate=0.35), COL()],
    "Outerwear": [MAT(), A("Fit", "text", "Slim; Regular; Oversized", True, "Fit", "", 0.9),
                  A("Length", "text", "Waist; Mid-thigh; Knee", False, rate=0.75), A("Waterproof", "boolean", "true or false", False, rate=0.88),
                  A("Lining", "text", "Fleece; Silk; Cotton", False, rate=0.7), A("Hood", "boolean", "true or false", False, rate=0.8),
                  A("Recycled Content %", "numeric", "Percentage recycled fibre", False, rate=0.4), CARE(0.88), COL()],
    "Dresses": GARMENT, "Blouses": GARMENT, "Tops": GARMENT, "Shirts": GARMENT, "T-Shirts": GARMENT,
    "Trousers": GARMENT,
    "Babywear": GARMENT + [A("Age Range", "text", "e.g. 3-6 months", True, rate=0.95), A("Safety Standard", "text", "e.g. BS EN 14682", False, rate=0.7)],
    "Schoolwear": GARMENT + [A("Age Range", "text", "e.g. 7-8 years", True, rate=0.95)],
    "Nightwear": GARMENT + [A("Age Range", "text", "e.g. 7-8 years", True, rate=0.95), A("Flame Retardancy", "text", "BS 5722 compliant", True, rate=0.78)],
    "Footwear": [MAT(), A("Size Guide", "text", "UK size to foot length in cm", True, "Dimensions", "dimensions", 0.7),
                 A("Sole Material", "text", "Rubber; EVA; Leather", False, rate=0.8), WGT(0.85), COL()],
    "Scarves": [MAT(), DIM(0.8, mand=False), WGT(0.85), CARE(0.85, False), COL()],
    "Bags": [MAT(), DIM(0.75), WGT(0.85), A("Closure", "text", "Zip; Magnetic; Drawstring", False, rate=0.8), COL()],
    "Jewellery": [MAT(), DIM(0.78, mand=False), WGT(0.85), A("Hallmark", "text", "e.g. 925", False, rate=0.6), COL()],
    "Haircare": [A("Ingredients", "text", "INCI list", True, rate=0.9), A("Volume (ml)", "numeric", "ml", True, "Capacity", "", 0.95),
                 A("Shelf Life", "text", "Months after opening", False, rate=0.8), A("Country of Origin", "text", "ISO 3166 code", False, "Country of Origin", "country_of_origin", 0.9)],
    "Bodycare": [A("Ingredients", "text", "INCI list", True, rate=0.9), A("Volume (ml)", "numeric", "ml", True, "Capacity", "", 0.95),
                 A("Shelf Life", "text", "Months after opening", False, rate=0.8), A("Country of Origin", "text", "ISO 3166 code", False, "Country of Origin", "country_of_origin", 0.9)],
    "Skincare": [A("Ingredients", "text", "INCI list", True, rate=0.9), A("Volume (ml)", "numeric", "ml", True, "Capacity", "", 0.95),
                 A("Shelf Life", "text", "Months after opening", False, rate=0.8), A("Skin Type", "text", "Dry; Oily; All", False, rate=0.8)],
    "Fragrance": [A("Ingredients", "text", "INCI list", True, rate=0.9), A("Volume (ml)", "numeric", "ml", True, "Capacity", "", 0.95),
                  A("Fragrance Family", "text", "Floral; Woody; Citrus", False, rate=0.85), A("Allergen Declaration", "text", "EU 26 allergens", True, rate=0.8)],
    "Small Appliances": [MAT(0.93), DIM(0.70), WGT(0.85, mand=True), COL(0.80, True),
                         A("Capacity", "numeric", "litres", False, "Capacity", "", 0.88),
                         A("Voltage & Wattage", "text", "e.g. 230V 2200W", True, "Voltage & Wattage", "voltage_wattage", 0.52),
                         A("Energy Rating", "enum", "A to G", True, "Energy Rating", "energy_label", 0.62),
                         A("WEEE Registration Number", "text", "DE + 8 digits", True, "WEEE Registration Number", "weee_registration_number", 0.45),
                         A("EAN", "text", "13 digits", True, "EAN", "ean", 0.78),
                         WARR(0.80), A("Instruction Language", "text", "e.g. English; German; French", False, "Instruction Language", "instructions_language", 0.7),
                         CARE(0.9, False)],
    "Smart Home": [MAT(0.9), DIM(0.75), WGT(0.85), A("Connectivity", "text", "Wi-Fi; Zigbee; Bluetooth", True, rate=0.88),
                   A("Voltage & Wattage", "text", "e.g. 230V 10W", True, "Voltage & Wattage", "voltage_wattage", 0.7), WARR(0.7), COL()],
    "Personal Care": [MAT(0.9), DIM(0.72), WGT(0.85), A("Voltage & Wattage", "text", "e.g. 5V 10W", True, "Voltage & Wattage", "voltage_wattage", 0.6),
                      A("Battery Type", "text", "Li-ion; AA; None", False, rate=0.85), A("EAN", "text", "13 digits", True, "EAN", "ean", 0.8), WARR(0.7)],
    "Audio": [MAT(0.9), DIM(0.75), WGT(0.85), A("Connectivity", "text", "Bluetooth; Wired", True, rate=0.9),
              A("Battery Life", "numeric", "hours", False, rate=0.7), WARR(0.7), COL()],
    # Home department: same concepts under different names and mandatory flags per category (the taxonomy mess).
    "Cookware": [MAT(0.93), DIM(0.70), A("Capacity", "numeric", "litres", False, "Capacity", "", 0.85),
                 A("Heat Source Compatibility", "enum", "Gas; Electric; Induction; All", True, "Compatibility", "", 0.90),
                 A("Dishwasher Safe", "boolean", "true or false", True, "Dishwasher Safe", "", 0.80), WARR(0.6), WGT(0.9)],
    "Drinkware": [MAT(0.9, "Material"), A("Capacity (ml)", "numeric", "ml", True, "Capacity", "", 0.92),
                  A("Height x Diameter", "text", "cm", False, "Dimensions", "dimensions", 0.55),
                  A("Dishwasher Safe", "boolean", "true or false", True, "Dishwasher Safe", "", 0.80), WGT(0.85)],
    "Bedding": [MAT(0.93), A("Thread Count", "numeric", "e.g. 400", False, rate=0.8),
                A("Size", "text", "Single; Double; King; Super King", True, "Dimensions", "dimensions", 0.66),
                CARE(0.88), WGT(0.8), COL(0.95)],
    "Towels": [MAT(0.9, "Fabric"), A("Size (cm)", "text", "cm", False, "Dimensions", "dimensions", 0.60),
               WGT(0.85, "Weight (gsm)"), CARE(0.9), COL(0.96)],
    "Storage": [MAT(0.88, "Materials"), DIM(0.58, "Dimensions (cm)"), A("Capacity", "numeric", "litres", False, "Capacity", "", 0.70),
                A("Weight Limit", "numeric", "kg", False, rate=0.6), COL(0.9)],
    "Lighting": [MAT(0.9), DIM(0.74), A("Bulb Fitting", "text", "E27; B22; GU10", True, "Compatibility", "", 0.64),
                 A("Voltage & Wattage", "text", "e.g. 230V 9W", True, "Voltage & Wattage", "voltage_wattage", 0.6),
                 A("Energy Rating", "enum", "A to G", False, "Energy Rating", "energy_label", 0.62), WARR(0.6)],
}
HOME = ["Cookware", "Drinkware", "Bedding", "Towels", "Storage", "Lighting"]

# Products whose listing data is wrong and drove returns/complaints (SKUs and error types match customer_service contacts).
# (sku, attribute name, wrong value, confidence, source)
DATA_ERRORS = (
    [(s, "Heat Source Compatibility", "All hobs incl. induction", 55, "marketplace") for s in
     ("SKU-100805", "SKU-100812", "SKU-100819", "SKU-103794", "SKU-105796", "SKU-105782", "SKU-102611", "SKU-103598", "SKU-102618")]
    + [(s, "Dimensions", "Pan diameter 28 cm", 52, "supplier") for s in
       ("SKU-102618", "SKU-103794", "SKU-105782", "SKU-105789", "SKU-102611", "SKU-100805", "SKU-103612", "SKU-103598")]
    + [(s, "Material Composition", "Stainless steel", 48, "supplier") for s in
       ("SKU-103605", "SKU-103794", "SKU-102625", "SKU-103598", "SKU-105782", "SKU-100805", "SKU-102618")]
    + [(s, "Size", "Double 200 x 200 cm", 50, "supplier") for s in
       ("SKU-104949", "SKU-100924", "SKU-104970", "SKU-105866", "SKU-104977", "SKU-104942", "SKU-103479", "SKU-103472", "SKU-105880")]
    + [(s, "Voltage & Wattage", "230V 2200W", 50, "marketplace") for s in
       ("SKU-105901", "SKU-101225", "SKU-102926", "SKU-105845", "SKU-101379")]
    + [(s, "Bulb Fitting", "E27", 45, "marketplace") for s in
       ("SKU-106174", "SKU-100119", "SKU-106160", "SKU-101141", "SKU-101155")]
)

MATERIALS = {
    "Cookware": ["Stainless steel", "Cast iron", "Aluminium non-stick", "Carbon steel"],
    "Drinkware": ["Glass", "Ceramic", "Stainless steel"],
    "Bedding": ["100% cotton", "Poly-cotton blend", "Linen"],
    "Towels": ["100% cotton", "Cotton-bamboo blend"],
    "Storage": ["Polypropylene", "Seagrass", "Steel", "Fabric"],
    "Lighting": ["Metal", "Glass", "Plastic"],
    "Small Appliances": ["Stainless steel", "Plastic", "Glass and stainless steel"],
}
GEN_MATERIALS = ["100% cotton", "80/20 poly-cotton", "Wool blend", "Polyester", "Linen blend", "Viscose", "Leather", "Acrylic"]


def _value(g, a, p):
    """Plausible value for attribute `a` (spec tuple) on product `p`."""
    r, name, cat = g.rng, a[0], p["category"]
    if name in ("Material Composition", "Material", "Fabric", "Materials"):
        return r.choice(MATERIALS.get(cat, GEN_MATERIALS))
    if name == "Care Instructions":
        return r.choice(["Machine wash 30C", "Machine wash 40C", "Hand wash only", "Dry clean only", "Wipe clean"])
    if name in ("Weight", "Weight (gsm)"):
        return str(r.randint(350, 650)) if "gsm" in name else p["weight_kg"]
    if name == "Colour":
        return p["colour"]
    if name in ("Dimensions", "Dimensions (cm)", "Size (cm)", "Height x Diameter", "Size Guide"):
        if name == "Size (cm)":
            return r.choice(["50 x 90", "70 x 130", "100 x 150"])
        return f"{r.randint(8, 60)} x {r.randint(8, 60)} x {r.randint(5, 40)} cm"
    if name == "Size":
        return r.choice(["Single", "Double", "King", "Super King"])
    if name in ("Capacity", "Capacity (ml)", "Volume (ml)"):
        if cat == "Small Appliances":
            return str(r.choice([0.6, 0.8, 1.0, 1.2, 1.2, 1.5, 1.7, 2.0]))
        if name == "Capacity (ml)":
            return str(r.choice([250, 300, 350, 400, 500]))
        return str(r.choice([30, 50, 100, 200, 250, 400])) if "ml" in name else str(r.choice([1.5, 2.0, 3.0, 4.5, 20, 30, 60]))
    if name == "Voltage & Wattage":
        if cat == "Small Appliances":
            return r.choice(["230V 2200W", "230V 1800W", "230V 1500W", "100-240V 1000W", "100-240V 800W"])
        return r.choice(["230V 9W", "230V 10W", "5V 10W", "230V 1000W"])
    if name == "Energy Rating":
        return r.choice(["A", "B", "C", "D", "E"])
    if name == "WEEE Registration Number":
        return f"DE{r.randint(10000000, 99999999)}"
    if name == "EAN":
        return f"50{r.randint(10**10, 10**11 - 1)}"
    if name == "Warranty":
        return str(r.choice([1, 2, 2, 3, 5]))
    if name == "Instruction Language":
        return r.choice(["English", "English; German", "English; German; French"])
    if name == "Heat Source Compatibility":
        return r.choices(["Gas", "Electric", "Induction", "All"], [0.2, 0.15, 0.25, 0.4])[0]
    if name == "Dishwasher Safe":
        return r.choice(["true", "false"])
    if name == "Fit":
        return r.choices(["Slim", "Regular", "Oversized"], [0.25, 0.5, 0.25])[0]
    if name in ("Waterproof", "Hood"):
        return "false" if name == "Waterproof" else r.choice(["true", "false"])
    if name == "Recycled Content %":
        return str(r.choice([0, 30, 50, 100]))
    if name == "Bulb Fitting":
        return r.choice(["E27", "B22", "GU10", "E14"])
    pools = {
        "Sleeve Length": ["Short", "3/4", "Long", "Sleeveless"], "Neckline": ["Crew", "V-neck", "Turtleneck"],
        "Length": ["Waist", "Mid-thigh", "Knee"], "Lining": ["Fleece", "Silk", "Cotton", "Unlined"],
        "Closure": ["Zip", "Magnetic", "Drawstring"], "Hallmark": ["925", "375", "None"],
        "Shelf Life": ["6 months", "12 months", "24 months"], "Skin Type": ["Dry", "Oily", "All skin types"],
        "Fragrance Family": ["Floral", "Woody", "Citrus", "Oriental"], "Allergen Declaration": ["Declared", "None declared"],
        "Battery Type": ["Li-ion", "AA", "None"], "Sole Material": ["Rubber", "EVA", "Leather"],
        "Safety Standard": ["BS EN 14682", "BS EN 71"], "Flame Retardancy": ["BS 5722 compliant"],
        "Ingredients": ["Aqua, glycerin, parfum", "Aqua, cetearyl alcohol, panthenol"], "Battery Life": ["4", "8", "12", "20"],
        "Weight Limit": ["50", "80", "120", "200"], "Country of Origin": ["CN", "PT", "TR", "IN", "GB"],
    }
    if name in pools:
        return r.choice(pools[name])
    if name == "Thread Count":
        return str(r.choice([200, 400, 600, 1000]))
    if name == "Age Range":
        return r.choice(["0-12 months", "1-3 years", "3-6 years", "7-10 years"])
    if name == "Connectivity":
        return r.choice(["Wi-Fi", "Bluetooth", "Zigbee", "Wired"])
    return f"{name} {r.randint(1, 9)}"


def generate(g):
    r = g.rng
    products = g.master("products")
    by_cat = {}
    for p in products:
        by_cat.setdefault(p["category"], []).append(p)
    categories = sorted(by_cat)

    attributes, attr_by = [], {}  # attr_by[(category, name)] -> (attribute_id, spec)
    n = 0
    for cat in categories:
        for a in SPECS[cat]:
            n += 1
            aid = f"ATTR-{n:03d}"
            attr_by[(cat, a[0])] = (aid, a)
            attributes.append({
                "attribute_id": aid, "name": a[0], "attribute_type": a[1], "category": cat, "data_format": a[2],
                "is_mandatory": a[3], "description": f"{a[0]} for {cat}", "status": "active",
                "canonical_name": a[4], "marketplace_field": a[5], "created_at": g.as_of - timedelta(days=r.randint(120, 400)),
            })
        if cat in HOME:  # proposed additions the marketplaces ask for that Home does not hold yet
            for pname, ptype, fmt, canon, mkt in (("Country of Origin", "text", "ISO 3166 code", "Country of Origin", "country_of_origin"),
                                                  ("EAN", "text", "13 digits", "EAN", "ean")):
                if (cat, pname) in attr_by or any(x[0] == pname for x in SPECS[cat]):
                    continue
                n += 1
                attributes.append({
                    "attribute_id": f"ATTR-{n:03d}", "name": pname, "attribute_type": ptype, "category": cat, "data_format": fmt,
                    "is_mandatory": True, "description": f"{pname} requested by marketplace feeds for {cat}", "status": "proposed",
                    "canonical_name": canon, "marketplace_field": mkt, "created_at": g.as_of - timedelta(days=r.randint(5, 40)),
                })

    groups = []
    for i, cat in enumerate(categories, 1):
        active = [a for a in attributes if a["category"] == cat and a["status"] == "active"]
        groups.append({"group_id": f"GRP-{i:03d}", "name": f"{cat.replace(' ', '')}_Core", "category": cat,
                       "description": f"Core attributes for {cat} products", "attribute_count": len(active),
                       "status": "active", "version": "1.0", "created_at": g.as_of - timedelta(days=r.randint(150, 420))})

    # Attribute values: every active/new/other product gets one row per attribute; missing ones are blank rows
    # so they can be corrected in bulk. Exact missing counts follow each attribute's rate.
    rows = {}
    err_keys = {(sku, name) for sku, name, *_ in DATA_ERRORS}
    for cat in categories:
        prods = by_cat[cat]
        live = [p for p in prods if p["status"] in ("active", "new")]
        for a in SPECS[cat]:
            aid = attr_by[(cat, a[0])][0]
            order = live[:]
            r.shuffle(order)
            order.sort(key=lambda p: (p["sku"], a[0]) in err_keys)  # error SKUs keep a (wrong) value
            missing = {p["sku"] for p in order[:round(len(live) * (1 - a[6]))]}
            missing |= {p["sku"] for p in prods if p["status"] not in ("active", "new") and r.random() > a[6]}
            for p in prods:
                upd = g.as_of - timedelta(days=r.randint(1, 90))
                src = r.choices(["supplier", "internal", "marketplace"], [0.4, 0.4, 0.2])[0]
                if p["sku"] in missing:
                    rows[(p["sku"], aid)] = {"sku": p["sku"], "attribute_id": aid, "value": None, "confidence": 0,
                                             "source": src, "last_updated": upd, "is_complete": False}
                else:
                    rows[(p["sku"], aid)] = {"sku": p["sku"], "attribute_id": aid, "value": _value(g, a, p),
                                             "confidence": r.randint(80, 98), "source": src, "last_updated": upd,
                                             "is_complete": r.random() < 0.95}

    def setv(sku, cat, name, value, conf=92, src="supplier", complete=True):
        aid = attr_by[(cat, name)][0]
        rows[(sku, aid)] = {"sku": sku, "attribute_id": aid, "value": value, "confidence": conf, "source": src,
                            "last_updated": g.as_of - timedelta(days=3), "is_complete": complete}

    cat_of = {p["sku"]: p["category"] for p in products}
    for sku, name, value, conf, src in DATA_ERRORS:
        setv(sku, cat_of[sku], name, value, conf, src, False)

    # Waterproof adult outerwear: only these eight products are waterproof.
    adult = sorted(p["sku"] for p in by_cat["Outerwear"] if p["department"] in ("Menswear", "Womenswear") and p["status"] in ("active", "new"))
    waterproof = adult[1::4][:8]
    for sku in waterproof:
        setv(sku, "Outerwear", "Waterproof", "true", 94, "supplier")
    for p in by_cat["Outerwear"]:
        if p["sku"] not in waterproof and rows[(p["sku"], attr_by[("Outerwear", "Waterproof")][0])]["value"] is not None:
            setv(p["sku"], "Outerwear", "Waterproof", "false", r.randint(80, 95), "supplier")

    # Recycled-content claim SKUs: attribute value agrees with the claim.
    for sku, pct in (("SKU-100154", "100"), ("SKU-100161", "100"), ("SKU-100427", "60")):
        setv(sku, "Outerwear", "Recycled Content %", pct)

    # Marketplace story: K-1700 kettle lacks voltage data; PF-220 fan has its EAN in PIM.
    setv("K-1700", "Small Appliances", "Capacity", "1.7")
    setv("K-1700", "Small Appliances", "Material Composition", "Glass and stainless steel")
    rows[("K-1700", attr_by[("Small Appliances", "Voltage & Wattage")][0])].update(value=None, confidence=0, is_complete=False)
    rows[("K-1700", attr_by[("Small Appliances", "WEEE Registration Number")][0])].update(value=None, confidence=0, is_complete=False)
    setv("PF-220", "Personal Care", "EAN", "5012345678900", 97, "internal")

    # Claims (noise): well-evidenced, so the seeded story claims are the ones that fall short.
    claims = []
    n_claim = 0
    claim_types = ["organic", "recycled_content", "fair_trade", "sustainable", "ecolabel"]
    certs = {"organic": "GOTS", "recycled_content": "GRS", "fair_trade": "Fair Trade", "sustainable": "OEKO-TEX", "ecolabel": "EU Ecolabel"}
    texts = {"organic": "GOTS certified organic cotton", "fair_trade": "Fair Trade certified", "sustainable": "Made with sustainable practices",
             "ecolabel": "EU Ecolabel certified"}
    story_skus = {"SKU-100154", "SKU-100161", "SKU-100427", "SKU-100700", "K-1700"}
    pool = [p for p in products if p["category"] in ("Knitwear", "Dresses", "Footwear", "Bags", "Scarves", "Towels", "Bedding", "Babywear", "Shirts")
            and p["status"] == "active" and p["sku"] not in story_skus]
    for i, p in enumerate(r.sample(pool, 36)):
        n_claim += 1
        ctype = "recycled_content" if i < 6 else r.choice([t for t in claim_types if t != "recycled_content"])
        pct = r.choice([30, 50, 70, 100]) if ctype == "recycled_content" else None
        pending = ctype != "recycled_content" and i % 12 == 7
        claims.append({
            "claim_id": f"CLM-{n_claim:06d}", "sku": p["sku"], "claim_type": ctype,
            "claim_text": f"Made with {pct}% recycled materials (GRS certified)" if pct else texts[ctype],
            "certification_type": certs[ctype], "has_evidence": not pending, "evidence_ref": None if pending else f"CERT-{r.randint(1000, 9999)}",
            "status": "pending_review" if pending else "active", "claimed_pct": pct, "certified_pct": pct if not pending and pct else None,
            "evidence_status": "none" if pending else "valid", "evidence_expires": None if pending else g.as_of + timedelta(days=r.randint(120, 500)),
            "removal_reason": None, "created_at": g.as_of - timedelta(days=r.randint(30, 200)), "updated_at": g.as_of - timedelta(days=r.randint(5, 60)),
        })

    return {"attributes": attributes, "attribute_groups": groups, "product_attributes": list(rows.values()),
            "product_claims": claims, "epr_data_fields": [], "market_fit_rules": []}
