"""PLM data: tech packs, BOMs, material library, batches, dye lots, specs, regulated categories.

Everything is derived from master products (one tech pack and BOM per SKU) so categories, suppliers and
factories always match master. Story SKUs are written by hand in seed/*.csv and skipped here where a seed
supplies all their rows.
"""
import json
import random

# SKUs whose BOM / fabric spec / batches are fully hand-written in seed/ (the generator leaves them alone)
STORY_SKUS = {
    "SKU-100952", "SKU-102968", "SKU-102590", "SKU-100007", "SKU-100014", "SKU-100021", "SKU-100301",
    "SKU-101813", "SKU-103199", "SKU-103745", "K-1700", "PF-220", "SKU-100847", "SKU-102905",
    "SKU-100574", "SKU-106307",
}
# other products that use the same lithium cell as PF-220 (MAT-LI-BATTERY, supplier SUP-0013, factory FAC-0027)
CELL_SKUS = {"SKU-100539", "SKU-100546", "SKU-103220", "SKU-104018"}
STORY_STYLES = {"STY-4595", "STY-6132", "STY-4012", "STY-5094", "STY-4171", "STY-5905"}
# styles whose size/colour siblings are also hand-written (BOM and tech pack in seed/)
SEEDED_STYLES = {"STY-4595", "STY-6132", "STY-4012", "STY-5905"}

# material id -> (name, fibre content, type, unit cost, unit, gsm, supplier)
# (the library itself is seeded; costs here only drive generated BOM lines)
FABRIC_COST = {
    "MAT-POL-100": 2.50, "MAT-COT-100": 3.20, "MAT-POL-COT-50": 2.85, "MAT-NYL-BLEND": 4.50, "MAT-VISCOSE": 3.00,
    "MAT-LINEN": 5.00, "MAT-WOOL": 6.00, "MAT-DENIM": 3.50, "MAT-PFAS-COATED": 5.50, "MAT-LINING": 2.00,
}
FIBRE = {
    "MAT-POL-100": "100% Polyester", "MAT-COT-100": "100% Cotton", "MAT-POL-COT-50": "50% Polyester 50% Cotton",
    "MAT-NYL-BLEND": "80% Nylon 20% Spandex", "MAT-VISCOSE": "100% Viscose", "MAT-LINEN": "100% Linen",
    "MAT-WOOL": "100% Wool", "MAT-DENIM": "95% Cotton 5% Elastane", "MAT-PFAS-COATED": "Polyester PFAS coated",
}
NAME = {
    "MAT-POL-100": "100% Polyester", "MAT-COT-100": "100% Cotton", "MAT-POL-COT-50": "50/50 Poly-Cotton",
    "MAT-NYL-BLEND": "80/20 Nylon/Spandex", "MAT-VISCOSE": "Viscose Rayon", "MAT-LINEN": "Linen",
    "MAT-WOOL": "Merino Wool", "MAT-DENIM": "Denim Fabric", "MAT-PFAS-COATED": "PFAS Waterproof Fabric",
    "MAT-LINING": "Lining Fabric", "MAT-POL-WADDING": "Polyester Wadding",
}
# category -> (fabric choices with weights, metres of fabric per garment, trims)
APPAREL = {
    "Blouses": ([("MAT-POL-100", 45), ("MAT-VISCOSE", 30), ("MAT-COT-100", 15), ("MAT-POL-COT-50", 10)], 1.6, ["MAT-BUTTON"]),
    "Dresses": ([("MAT-POL-100", 40), ("MAT-VISCOSE", 30), ("MAT-COT-100", 20), ("MAT-LINEN", 10)], 2.6, ["MAT-ZIPPER"]),
    "Tops": ([("MAT-COT-100", 40), ("MAT-POL-COT-50", 30), ("MAT-POL-100", 20), ("MAT-VISCOSE", 10)], 1.2, []),
    "Knitwear": ([("MAT-WOOL", 35), ("MAT-COT-100", 35), ("MAT-POL-100", 20), ("MAT-NYL-BLEND", 10)], 1.0, []),
    "Trousers": ([("MAT-COT-100", 30), ("MAT-DENIM", 30), ("MAT-POL-COT-50", 25), ("MAT-POL-100", 15)], 1.6, ["MAT-ZIPPER", "MAT-BUTTON"]),
    "Shirts": ([("MAT-COT-100", 50), ("MAT-POL-COT-50", 30), ("MAT-LINEN", 20)], 1.8, ["MAT-BUTTON"]),
    "T-Shirts": ([("MAT-COT-100", 70), ("MAT-POL-COT-50", 30)], 1.1, []),
    "Outerwear": ([("MAT-POL-100", 40), ("MAT-NYL-BLEND", 30), ("MAT-PFAS-COATED", 15), ("MAT-WOOL", 15)], 2.8, ["MAT-ZIPPER"]),
    "Babywear": ([("MAT-COT-100", 80), ("MAT-POL-COT-50", 20)], 0.8, ["MAT-ELASTIC"]),
    "Nightwear": ([("MAT-COT-100", 70), ("MAT-POL-COT-50", 30)], 1.4, ["MAT-ELASTIC"]),
    "Schoolwear": ([("MAT-POL-COT-50", 50), ("MAT-COT-100", 30), ("MAT-POL-100", 20)], 1.5, ["MAT-BUTTON"]),
    "Scarves": ([("MAT-WOOL", 30), ("MAT-VISCOSE", 40), ("MAT-POL-100", 30)], 1.0, []),
}
ATTRS = {
    "Blouses": ["easy-care", "relaxed fit", "button front", "breathable"],
    "Dresses": ["lined", "side zip", "midi length", "breathable"],
    "Tops": ["stretch", "crew neck", "breathable", "quick-dry"],
    "Knitwear": ["ribbed cuffs", "warm", "wash at 30C", "soft handle"],
    "Trousers": ["comfort fit", "stretch", "belt loops", "zip fly"],
    "Shirts": ["easy-iron", "regular fit", "button down"],
    "T-Shirts": ["soft handle", "crew neck", "pre-shrunk"],
    "Outerwear": ["water-resistant", "padded", "zip front", "hood"],
    "Babywear": ["soft", "nickel-free poppers", "easy dressing"],
    "Nightwear": ["soft", "elasticated waist", "easy-care"],
    "Schoolwear": ["hard-wearing", "easy-iron", "stain-resistant"],
    "Scarves": ["soft handle", "fringed", "lightweight"],
}
REGIONS = ["UK", "EU", "US", "AU"]


def _pick(r, options):
    total = sum(w for _, w in options)
    x = r.uniform(0, total)
    for item, w in options:
        x -= w
        if x <= 0:
            return item
    return options[-1][0]


def _line(sku, n, ctype, comp, cname, mname, sup, fac, qty, unit, cost, lead, notes=""):
    return {"sku": sku, "line_no": n, "component_type": ctype, "component_id": comp, "component_name": cname,
            "material_name": mname, "supplier_id": sup, "factory_id": fac, "quantity": qty, "unit": unit,
            "unit_cost_gbp": cost, "lead_time_days": lead, "notes": notes}


def generate(g):
    r = g.rng
    products = g.master("products")
    suppliers = {s["supplier_id"]: s for s in g.master("suppliers")}
    factories = g.master("factories")
    fac_by_sup = {}
    for f in factories:
        fac_by_sup.setdefault(f["supplier_id"], []).append(f["factory_id"])
    employees = [e["employee_id"] for e in g.master("employees")] or ["EMP-00001"]

    # library supplier per material (matches seed/material_library.csv)
    lib_sup = {"MAT-POL-100": "SUP-0064", "MAT-COT-100": "SUP-0018", "MAT-POL-COT-50": "SUP-0064", "MAT-NYL-BLEND": "SUP-0053",
               "MAT-VISCOSE": "SUP-0036", "MAT-LINEN": "SUP-0028", "MAT-WOOL": "SUP-0058", "MAT-DENIM": "SUP-0036",
               "MAT-PFAS-COATED": "SUP-0022", "MAT-LINING": "SUP-0053", "MAT-ZIPPER": "SUP-0053", "MAT-BUTTON": "SUP-0053",
               "MAT-ELASTIC": "SUP-0036", "MAT-LEATHER": "SUP-0049", "MAT-RUBBER-SOLE": "SUP-0014", "MAT-HARDWARE": "SUP-0007",
               "MAT-POL-WADDING": "SUP-0001", "MAT-LI-BATTERY": "SUP-0013", "MAT-SS": "SUP-0060", "MAT-PP-LID": "SUP-0060", "MAT-SILICONE": "SUP-0060",
               "MAT-GIFTBOX": "SUP-0060", "MAT-PLASTIC-BODY": "SUP-0013", "MAT-ELECTRONICS": "SUP-0013",
               "MAT-BATTERY": "SUP-0013", "MAT-MOTOR": "SUP-0013"}
    lib_cost = {"MAT-ZIPPER": 0.40, "MAT-BUTTON": 0.05, "MAT-ELASTIC": 0.60, "MAT-LEATHER": 18.0, "MAT-RUBBER-SOLE": 3.5,
                "MAT-HARDWARE": 2.5, "MAT-POL-WADDING": 1.10, "MAT-LI-BATTERY": 15.0, "MAT-SS": 16.9, "MAT-PP-LID": 1.55, "MAT-SILICONE": 0.75,
                "MAT-GIFTBOX": 0.85, "MAT-PLASTIC-BODY": 2.5, "MAT-ELECTRONICS": 12.0, "MAT-BATTERY": 8.5, "MAT-MOTOR": 5.0} | FABRIC_COST
    lib_name = NAME | {"MAT-ZIPPER": "Coil Zipper YKK", "MAT-BUTTON": "Polyester Button", "MAT-ELASTIC": "Elastic Waistband",
                       "MAT-LEATHER": "Leather", "MAT-RUBBER-SOLE": "Rubber Sole", "MAT-HARDWARE": "Metal Hardware",
                       "MAT-SS": "304 Stainless Steel", "MAT-PP-LID": "Polypropylene Lid", "MAT-SILICONE": "Silicone",
                       "MAT-GIFTBOX": "Gift Box", "MAT-PLASTIC-BODY": "ABS Plastic Body", "MAT-ELECTRONICS": "Electronics Module",
                       "MAT-BATTERY": "Rechargeable Battery", "MAT-MOTOR": "DC Motor",
                       "MAT-LI-BATTERY": "Lithium Battery Pack"}

    def fac_for(sup, default):
        f = fac_by_sup.get(sup)
        return r.choice(f) if f else default

    def mk(sku, n, ctype, mid, qty, unit, prod, notes="", cost_mult=None, name=None, fiber=None):
        base = lib_cost[mid]
        cost = round(base * (cost_mult or r.uniform(0.92, 1.25)), 2)
        sup = lib_sup[mid]
        return _line(sku, n, ctype, mid, name or lib_name[mid], fiber or FIBRE.get(mid, lib_name[mid]), sup,
                     fac_for(sup, prod["factory_id"]), qty, unit, cost, r.choice([14, 21, 30, 35, 45, 60]), notes)

    # ======== bill_of_materials ========
    boms, primary_fabric = [], {}
    for p in products:
        sku, dept, cat = p["sku"], p["department"], p["category"]
        if sku in STORY_SKUS or p["style_id"] in SEEDED_STYLES or dept == "Beauty":
            continue
        r = g.rng_for("bom", sku)
        lines = []
        if cat in APPAREL:
            fabrics, metres, trims = APPAREL[cat]
            scale = 0.6 if dept == "Kids" else 1.0
            fab = _pick(random.Random(p["style_id"]), fabrics)
            primary_fabric[sku] = fab
            n = 1
            lines.append(mk(sku, n, "fabric", fab, round(metres * scale * r.uniform(0.9, 1.15), 2), "m", p, "Main fabric"))
            if cat == "Outerwear":
                n += 1
                lines.append(mk(sku, n, "fabric", "MAT-LINING", round(2.0 * scale * r.uniform(0.9, 1.1), 2), "m", p, "Lining"))
                if fab in ("MAT-POL-100", "MAT-NYL-BLEND") and r.random() < 0.6:
                    n += 1
                    lines.append(mk(sku, n, "trim", "MAT-POL-WADDING", round(2.2 * scale, 2), "m", p, "Padding"))
            for t in trims:
                n += 1
                q = {"MAT-BUTTON": r.choice([4, 6, 8]), "MAT-ZIPPER": 1, "MAT-ELASTIC": round(0.1 * scale, 2)}[t]
                lines.append(mk(sku, n, "trim" if t != "MAT-ZIPPER" else "component", t, q, "pcs" if t != "MAT-ELASTIC" else "kg", p))
        elif cat == "Footwear":
            primary_fabric[sku] = "MAT-LEATHER"
            lines = [mk(sku, 1, "component", "MAT-LEATHER", 0.4, "kg", p, "Upper"),
                     mk(sku, 2, "component", "MAT-RUBBER-SOLE", 0.2, "kg", p, "Outsole")]
        elif cat == "Bags":
            primary_fabric[sku] = "MAT-LEATHER"
            lines = [mk(sku, 1, "component", "MAT-LEATHER", round(r.uniform(0.7, 1.1), 2), "kg", p, "Main body"),
                     mk(sku, 2, "component", "MAT-HARDWARE", 0.05, "kg", p, "Clasp and handles"),
                     mk(sku, 3, "component", "MAT-ZIPPER", 1, "pcs", p, "Internal zip")]
        elif cat in ("Jewellery",):
            lines = [mk(sku, 1, "component", "MAT-HARDWARE", 0.03, "kg", p, "Zinc alloy"),
                     mk(sku, 2, "packing", "MAT-GIFTBOX", 1, "pcs", p)]
        elif cat in ("Bedding", "Towels"):
            fab = _pick(r, [("MAT-COT-100", 70), ("MAT-POL-COT-50", 30)])
            if sku in ("SKU-104466", "SKU-100910"):  # 05:46:Q4 story SKUs: poly-cotton, Chinese fabric
                fab = "MAT-POL-COT-50"
            primary_fabric[sku] = fab
            lines = [mk(sku, 1, "fabric", fab, round(r.uniform(3.0, 6.0), 2), "m", p, "Main fabric")]
        elif cat in ("Drinkware", "Cookware"):
            lines = [mk(sku, 1, "component", "MAT-SS", 0.4, "kg", p, "Body"),
                     mk(sku, 2, "component", "MAT-PP-LID", 1, "pcs", p, "Lid"),
                     mk(sku, 3, "component", "MAT-SILICONE", 1, "pcs", p, "Seal"),
                     mk(sku, 4, "packing", "MAT-GIFTBOX", 1, "pcs", p)]
        elif dept == "Electricals" or cat in ("Lighting", "Storage"):
            lines = [mk(sku, 1, "component", "MAT-PLASTIC-BODY", 0.2, "kg", p, "Housing")]
            if cat != "Storage":
                lines.append(mk(sku, 2, "component", "MAT-ELECTRONICS", 1, "pcs", p, "Control board"))
            if p["hazmat"] == "li_ion_battery":
                if sku in CELL_SKUS:
                    lines.append(mk(sku, len(lines) + 1, "component", "MAT-LI-BATTERY", 1, "pcs", p, "Battery cell",
                                    fiber="Li-ion 2600mAh"))
                else:
                    lines.append(mk(sku, len(lines) + 1, "component", "MAT-BATTERY", 1, "pcs", p, "Li-ion cell, UN38.3 tested"))
            if cat in ("Small Appliances", "Personal Care"):
                lines.append(mk(sku, len(lines) + 1, "component", "MAT-MOTOR", 1, "pcs", p))
        # scale component prices so material cost is a believable share of the master unit cost
        raw = sum(ln["quantity"] * ln["unit_cost_gbp"] for ln in lines)
        if raw:
            share = r.uniform(0.3, 0.5)
            if cat == "Blouses":  # 04:39:Q4: Ochre blouse style STY-9345 is the most exposed to a polyester price rise
                share = {"SKU-106125": 0.47, "SKU-106132": 0.46, "SKU-106118": 0.45}.get(sku, min(share, 0.42))
            k = share * float(p["unit_cost_gbp"]) / raw
            for ln in lines:
                ln["unit_cost_gbp"] = round(ln["unit_cost_gbp"] * k, 3)
        for ln in lines:
            boms.append(ln)

    # ======== product_tech_pack (every master product) ========
    r = g.rng
    tech_packs = []
    for p in products:
        sku, cat = p["sku"], p["category"]
        r = g.rng_for("techpack", sku)
        mat = primary_fabric.get(sku)
        main = lib_name.get(mat, "Mixed materials") if mat else {"Drinkware": "Stainless steel", "Cookware": "Stainless steel",
                                                              "Jewellery": "Zinc alloy"}.get(cat, "Mixed materials")
        comp = FIBRE.get(mat, main) if mat else main
        attrs = ATTRS.get(cat, ["durable"])
        tech_packs.append({
            "sku": sku, "style_id": p["style_id"], "name": p["name"], "department": p["department"], "category": cat,
            "subcategory": p["subcategory"], "supplier_id": p["supplier_id"], "factory_id": p["factory_id"],
            "color": p["colour"], "main_material": main, "material_composition": comp,
            "design_attributes": json.dumps(r.sample(attrs, min(len(attrs), r.randint(1, 3)))),
            "lead_time_days": p["lead_time_days"], "status": p["status"],
            "created_at": g.days_ago(r.randint(60, 500)), "updated_at": g.days_ago(r.randint(0, 30)),
        })
    tp_by_sku = {t["sku"]: t for t in tech_packs}

    r = g.rng
    # last season (SS26) apparel: best sellers share easy-care features, worst sellers share fussy ones
    units = {}
    for w in g.master("sales_weekly"):
        units[w["sku"]] = units.get(w["sku"], 0) + float(w["store_units"]) + float(w["online_units"])
    ss26 = sorted((p["sku"] for p in products if p["season"] == "SS26" and p["department"] in ("Womenswear", "Menswear", "Kids")
                   and p["sku"] not in STORY_SKUS and p["style_id"] not in SEEDED_STYLES and units.get(p["sku"])),
                  key=lambda k: (-units[k], k))
    ss26_top, ss26_bottom = ss26[:25], ss26[-25:]
    for sku_list, add_attrs in ((ss26[:25], ["pockets", "machine washable"]), (ss26[-25:], ["dry clean only", "heavyweight"])):
        for sku in sku_list:
            cur = [a for a in json.loads(tp_by_sku[sku]["design_attributes"]) if a not in ("easy-care", "easy-iron")]
            tp_by_sku[sku]["design_attributes"] = json.dumps(cur[:2] + add_attrs)
    # 06:52:Q2: the apparel among the data_warehouse SS best sellers (top 10) and worst sellers (bottom 10) carry the same split of features
    DW_TOP_APPAREL = ["SKU-100644", "SKU-100637", "SKU-100651"]
    DW_BOTTOM_APPAREL = ["SKU-102310", "SKU-102296", "SKU-103283", "SKU-103297", "SKU-105481", "SKU-105761", "SKU-103143", "SKU-106013"]
    for sku_list, add_attrs in ((DW_TOP_APPAREL, ["pockets", "machine washable"]), (DW_BOTTOM_APPAREL, ["dry clean only", "heavyweight"])):
        for sku in sku_list:
            if sku in tp_by_sku:
                cur = [a for a in json.loads(tp_by_sku[sku]["design_attributes"]) if a not in ("easy-care", "easy-iron", "pockets", "machine washable", "dry clean only", "heavyweight")]
                tp_by_sku[sku]["design_attributes"] = json.dumps(cur[:2] + add_attrs)

    # ======== material_library: seeded ========
    # ======== material_batches and dye_lots (noise) ========
    users = {}
    new_skus = {p["sku"] for p in products if p["status"] == "new"}
    for sku, mat in sorted(primary_fabric.items()):
        if sku not in new_skus:
            users.setdefault(mat, []).append(sku)
    batches, dye_lots = [], []
    bn = dn = 0
    for mat in sorted(users):
        skus = users[mat]
        fabric = mat in FABRIC_COST
        sup = lib_sup[mat]
        r = g.rng_for("batches", mat)
        for j in range(r.randint(4, 8)):
            bn += 1
            bid = f"BATCH-{bn:05d}"
            dye_house = r.choice(["DYES-A", "DYES-B", "DYES-C"]) if fabric else None
            bdate = g.days_ago(r.randint(5, 150))
            failed = fabric and r.random() < 0.08
            batches.append({
                "batch_id": bid, "material_id": mat, "supplier_id": sup, "factory_id": fac_for(sup, factories[0]["factory_id"]),
                "batch_date": bdate, "quantity_kg": r.randint(800, 5000),
                "quantity_meters": r.randint(3000, 20000) if fabric else None, "color_lot": f"LOT-{r.randint(1000, 9999)}",
                "dye_house": dye_house, "test_status": "failed" if failed else "passed", "test_date": bdate,
                "traceability_notes": f"Routine batch from {suppliers[sup]['name']}",
                "used_in_skus": json.dumps(sorted(r.sample(skus, min(len(skus), r.randint(1, 4))))),
                "status": r.choice(["active", "active", "used", "archived"]), "created_at": bdate,
            })
            if fabric:
                dn += 1
                rub = r.choice([2, 3]) if failed else r.choice([4, 4, 5])
                dye_lots.append({
                    "dye_lot_id": f"DYE-{dn:06d}", "batch_id": bid, "fabric_material": mat, "mill_id": r.choice(["MIL-01", "MIL-02", "MIL-03", "MIL-04"]),
                    "dye_house": dye_house, "color_description": r.choice(["Navy", "Black", "Red", "Blue", "Green", "Grey", "White", "Ivory", "Sage"]),
                    "dye_date": bdate, "process_name": r.choice(["Continuous", "Exhaust", "Pad-batch", "Jig"]),
                    "process_chemicals": "Reactive dye, alkali, levelling agent", "process_changes": "Standard process" if not failed else "Dye bath temperature below target",
                    "temperature_c": r.randint(60, 100), "duration_minutes": r.randint(40, 180), "yield_pct": round(r.uniform(88, 98), 1),
                    "fastness_rubbing": str(rub), "fastness_washing": str(r.choice([4, 4, 5])),
                    "test_status": "failed" if failed else "passed", "notes": "Rubbing below grade 4" if failed else "",
                })

    # ======== fabric_specs (one per style, soft goods) ========
    r = g.rng
    fabric_specs, seen_style = [], set()
    for p in products:
        sty, sku = p["style_id"], p["sku"]
        if sty in seen_style or sty in STORY_STYLES or sku not in primary_fabric or primary_fabric[sku] not in FABRIC_COST:
            continue
        seen_style.add(sty)
        r = g.rng_for("fabspec", sty)
        mat = primary_fabric[sku]
        country = suppliers[lib_sup[mat]]["country"]
        fabric_specs.append({
            "fabric_spec_id": f"FAB-{len(fabric_specs) + 1:06d}", "material_id": mat, "style_id": sty,
            "fabric_name": f"{lib_name[mat]} for {p['subcategory']}", "fiber_content": FIBRE[mat],
            "weave": r.choice(["Plain", "Twill", "Jersey", "Sateen"]), "gsm": r.choice([90, 110, 130, 150, 180]),
            "width_cm": r.choice([140, 150, 160]), "mill_id": r.choice(["MIL-01", "MIL-02", "MIL-03", "MIL-04"]),
            "mill_country": country, "origin_country": country, "supplier_id": lib_sup[mat], "color": p["colour"],
            "shrinkage_pct": round(r.uniform(0.5, 3.0), 1), "tensile_strength": r.randint(300, 700), "tear_strength": r.randint(80, 250),
            "pilling_resistance": str(r.randint(3, 5)), "abrasion_cycles": r.randint(20000, 80000),
            "cost_per_meter_gbp": round(FABRIC_COST[mat] * r.uniform(0.95, 1.2), 2), "lead_time_days": r.randint(30, 90),
            "certifications": json.dumps(r.sample(["GOTS", "OEKO-TEX", "BSCI"], r.randint(0, 2))),
            "sustainability_score": r.randint(1, 5),
        })

    # ======== product_specifications (apparel: size chart, grade rules, tolerances) ========
    r = g.rng
    zip_skus = {b["sku"] for b in boms if b["component_id"] == "MAT-ZIPPER"}
    zip_nominal = {"Outerwear": 150, "Bags": 120}
    specs = []
    for p in products:
        sku, dept, cat = p["sku"], p["department"], p["category"]
        if dept not in ("Womenswear", "Menswear", "Kids") or cat == "Footwear" or cat == "Scarves":
            continue
        r = g.rng_for("spec", sku)
        sizes = {"Womenswear": ["8", "10", "12", "14", "16", "18"], "Menswear": ["XS", "S", "M", "L", "XL", "XXL"],
                 "Kids": ["3-4Y", "5-6Y", "7-8Y", "9-10Y"]}[dept]
        created, updated = g.days_ago(r.randint(60, 300)), g.days_ago(r.randint(0, 30))
        base = {"sku": sku, "spec_version": 1, "created_at": created, "updated_at": updated, "notes": ""}
        chest = [80 + 4 * i for i in range(len(sizes))]
        chart = {"sizes": sizes, "chest_cm": chest, "length_cm": [60 + 2 * i for i in range(len(sizes))]}
        points = ["chest", "waist", "length"]
        if dept == "Womenswear":  # UK women's chart: bust/waist/hip per size (steps widen above size 14)
            bust, waist, hip = [82, 86, 90, 94, 100, 106], [64, 68, 72, 76, 82, 88], [90, 94, 98, 102, 108, 114]
            chart = {"sizes": sizes, "bust_cm": bust, "waist_cm": waist, "hip_cm": hip, "length_cm": chart["length_cm"]}
            points = ["bust", "waist", "hip", "length"]
        # the trouser style T-4410 hand-writes its size chart and grade rules in seed/
        if p["style_id"] != "STY-T-4410":
            specs.append(base | {
                "spec_type": "size_chart", "spec_name": f"Size chart {p['style_id']}", "content": json.dumps(chart),
                "applicable_sizes": json.dumps(sizes), "applicable_fits": json.dumps(["regular"]),
                "measurement_points": json.dumps(points), "shrinkage_tolerances": None, "grade_definitions": None})
        if p["style_id"] != "STY-T-4410":
            specs.append(base | {
                "spec_type": "grade_rules", "spec_name": f"Grade rules {p['style_id']}",
                "content": json.dumps({"grade_step_cm": {"chest": 4, "length": 2}}),
                "applicable_sizes": json.dumps(sizes), "applicable_fits": json.dumps(["regular"]),
                "measurement_points": None, "shrinkage_tolerances": None,
                "grade_definitions": json.dumps({"A": {"tolerance_cm": 0.5}, "B": {"tolerance_cm": 1.0}})})
        pts = [{"point": "chest", "tolerance_cm": 1.0}, {"point": "length", "tolerance_cm": 1.5}]
        if sku in zip_skus:
            nominal = zip_nominal.get(cat, 100)
            pts.append({"point": "zip_strength", "nominal": nominal, "tolerance_pct": 5, "min": nominal * 0.95,
                        "max": nominal * 1.05, "unit": "N"})
        specs.append(base | {
            "spec_type": "tolerances", "spec_name": f"Tolerances {p['style_id']}", "content": None,
            "applicable_sizes": None, "applicable_fits": None, "measurement_points": json.dumps(pts),
            "shrinkage_tolerances": json.dumps({"wash": "-3%", "dry_clean": "-1%"}), "grade_definitions": None})

    # ======== product_regulated_categories ========
    r = g.rng
    regs = []

    def add(p, code, name, region, rules, status="compliant", test=False, note="", rng=None):
        regs.append({"sku": p["sku"], "category_id": f"REGCAT-{code}-{region}", "category_name": name, "region": region,
                     "regulations": json.dumps(rules), "compliance_status": status, "test_required": test,
                     "last_audit_date": g.days_ago((rng or r).randint(30, 400)),
                     "notes": note or ("Annual test report renewal due" if status == "review" else "")})

    planted = {"SKU-100847", "SKU-102779", "SKU-104039", "SKU-100868", "SKU-103136", "SKU-102590", "SKU-104123", "SKU-104795",
               "SKU-105551", "SKU-101813", "SKU-103199", "SKU-103745", "PF-220", "SKU-102905"}

    def status(p):
        return "review" if p["sku"] not in planted and r.random() < 0.04 else "compliant"

    sleep_rules = {"UK": ["BS 5722", "Nightwear (Safety) Regulations 1985"], "EU": ["EN 14878"], "US": ["16 CFR 1615", "16 CFR 1616"]}
    food_rules = {"UK": ["Retained Regulation (EC) 1935/2004"], "EU": ["Regulation (EC) 1935/2004", "Regulation (EU) 10/2011"],
                  "US": ["FDA 21 CFR 177"], "AU": ["Australia New Zealand Food Standards Code 3.2.1"]}
    batt_rules = {"UK": ["UKCA marking", "UN 38.3"], "EU": ["CE marking", "EU Battery Regulation 2023/1542"], "US": ["FCC Part 15", "UL 2054"]}
    for p in products:
        cat = p["category"]
        r = g.rng_for("reg", p["sku"])
        if cat == "Nightwear":
            for reg, rules in sleep_rules.items():
                add(p, "KIDSSLP", "kids_sleepwear", reg, rules, status(p), reg == "US")
        elif cat == "Drinkware":
            for reg in REGIONS:
                add(p, "FOODCON", "food_contact_materials", reg, food_rules[reg], status(p), reg in ("EU", "US"))
        if p["hazmat"] == "li_ion_battery":
            for reg, rules in batt_rules.items():
                add(p, "BATT", "battery_products", reg, rules, status(p), True)
        if cat in ("Bags", "Footwear"):
            for reg, rules in (("UK", ["UK REACH Annex XVII entry 47"]), ("EU", ["REACH Annex XVII entry 47 (chromium VI in leather, 3 mg/kg)"])):
                add(p, "CRVI", "leather_chromium_vi", reg, rules, "compliant", False)
        coated = primary_fabric.get(p["sku"]) == "MAT-PFAS-COATED"
        if cat == "Outerwear" and ((p["department"] != "Kids" and r.random() < 0.4) or coated):
            for reg, rules in (("UK", ["UK REACH PFAS restriction (proposed)"]), ("EU", ["EU universal PFAS restriction proposal"])):
                add(p, "PFAS", "waterproof_textiles", reg, rules, "review", True,
                    "PFAS coating to be replaced before the restriction applies" if coated else "Coating chemistry to be confirmed PFAS-free",
                    rng=random.Random(p["sku"]))

    # ======== legacy small tables ========
    r = g.rng
    legacy = products[:30]
    change_reqs = [{
        "change_request_id": f"CHG-{i:06d}", "sku": r.choice(legacy)["sku"],
        "change_type": r.choice(["material", "design", "size", "grade", "specification"]),
        "change_description": r.choice(["Improve fit at hip", "Switch to recycled trim", "Lengthen sleeve by 1cm", "Reinforce stitching at pocket"]),
        "reason": r.choice(["High return rate", "Cost reduction", "Customer feedback"]),
        "impact_assessment": json.dumps({"cost_impact": "Low", "timeline": "2 weeks"}), "requested_by": r.choice(employees),
        "requested_at": g.days_ago(r.randint(0, 60)), "status": r.choice(["open", "approved", "in_progress"]),
        "priority": r.choice(["low", "medium", "high"]), "target_implementation": g.days_ago(r.randint(-60, 30)),
        "notes": "", "updated_at": g.days_ago(r.randint(0, 30))} for i in range(10)]
    substances = [("CAS-000-1", "Polyester", "fabric", "Textiles"), ("CAS-000-2", "Lead", "trim", "RoHS"),
                  ("CAS-000-3", "Phthalates", "plastic", "Toys")]
    product_substances = []
    for i, p in enumerate(legacy):
        s = r.choice(substances)
        product_substances.append({"sku": p["sku"], "substance_id": s[0], "substance_name": s[1],
                                   "concentration_pct": round(r.uniform(0.1, 5.0), 2) if i % 3 == 0 else 0.0,
                                   "component": s[2], "regulation": s[3], "list_type": "monitored", "status": "active", "notes": ""})
    # restricted / candidate-list substances traced to BOM materials (separate rng: leaves other data unchanged)
    sr = random.Random("substances")
    story_sub = {"SKU-102905", "SKU-101813"}
    for b in boms:
        if b["component_id"] == "MAT-PFAS-COATED" and b["sku"] not in story_sub:
            for sid, nm, lo, hi in (("CAS-000-51", "Perfluorooctanoic acid", 0.05, 0.1), ("CAS-000-52", "Perfluorinated compounds", 0.1, 0.3)):
                product_substances.append({
                    "sku": b["sku"], "substance_id": sid, "substance_name": nm, "concentration_pct": round(sr.uniform(lo, hi), 2),
                    "component": "coating", "material_id": "MAT-PFAS-COATED", "regulation": "PFAS Regulation", "list_type": "restricted",
                    "status": "active", "notes": "Ban 2027"})
        elif b["component_id"] == "MAT-HARDWARE":
            product_substances.append({
                "sku": b["sku"], "substance_id": "CAS-7439-92-1", "substance_name": "Lead", "concentration_pct": round(sr.uniform(0.12, 0.45), 2),
                "component": "hardware", "material_id": "MAT-HARDWARE", "regulation": "REACH SVHC candidate list", "list_type": "candidate",
                "status": "active", "notes": "Zinc alloy hardware; above 0.1% reporting threshold"})
    cands = ["Recycled Polyester Blend", "Bio-based Nylon", "Mycelium Leather", "Algae Fiber", "Cork-Cotton Blend", "Lab-Grown Leather"]
    candidate_mats = [{
        "candidate_id": f"CAND-{i:06d}", "material_name": n, "material_type": r.choice(["fabric", "yarn", "component"]),
        "fiber_content": f"Trial composition for {n}", "supplier_id": r.choice(list(suppliers)),
        "readiness_level": r.choice(["experimental", "pilot", "proven"]), "test_status": r.choice(["planned", "in_progress", "completed", "passed"]),
        "cost_savings_pct": round(r.uniform(5, 25), 1), "weight_reduction_pct": round(r.uniform(0, 30), 1),
        "sustainability_benefit": "Reduced carbon footprint vs conventional", "pilot_date_start": g.days_ago(r.randint(30, 180)),
        "pilot_date_end": g.days_ago(r.randint(-60, 30)), "test_plan": json.dumps(["Tensile test", "Abrasion test"]),
        "test_results": "In progress", "notes": f"Trial material {i + 1}", "archived_at": None} for i, n in enumerate(cands)]

    return {
        "product_tech_pack": tech_packs, "bill_of_materials": boms, "material_library": [], "material_batches": batches,
        "dye_lots": dye_lots, "fabric_specs": fabric_specs, "product_specifications": specs,
        "candidate_materials": [], "co_development_projects": [], "product_change_requests": change_reqs,
        "product_substances": product_substances, "product_regulated_categories": regs,
    }
