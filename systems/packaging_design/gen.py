"""Background packaging data: pack specs, quotes, tech packs, e-commerce packs, weights and channel costs.

Story rows (PKS-9xxxxx, CTN-9xxxxx, ...) live in seed/*.csv. Generated noise only uses products that no story
touches, so a question about a story SKU finds exactly the planted rows.
"""
import math
from collections import defaultdict

STORY_SKUS = {
    "SKU-100532", "SKU-100658", "SKU-100091", "SKU-101904", "SKU-103164", "SKU-100112",
    "K-1700", "SKU-104123", "SKU-104795", "SKU-100539",
}
STORY_STYLES = {"STY-4012", "STY-7731", "STY-5520"}

MATERIALS = {  # key: (cost base GBP, recycled %, recyclable)
    "corrugated": (0.85, 70, True),
    "moulded_pulp": (0.92, 95, True),
    "recycled_plastic": (0.78, 80, True),
    "rigid_plastic": (1.20, 15, False),
    "kraft": (0.35, 60, True),
    "polybag": (0.12, 20, False),
}
BUYERS = ["EMP-00010", "EMP-00011", "EMP-00012", "EMP-00013"]
FRAGILE = {"Small Appliances", "Drinkware", "Lighting", "Cookware", "Fragrance", "Personal Care", "Audio", "Smart Home"}

# Company-wide FY26 packaging spend by channel, matching the cost-to-serve system (cost_allocation):
# (orders, units, packaging GBP, packing labour share %)
CHANNEL_TARGETS = {
    "stores": (480_000, 98_000_000, 3_500_000, 14.0),
    "online": (7_900_000, 19_000_000, 12_000_000, 36.0),
    "wholesale": (9_000, 22_000_000, 1_000_000, 6.0),
}


def pallet_units(h, w, d):
    """Units per 1200x1000 pallet stacked to 1800 mm (same maths as calculate_pallet_fill_for_pack)."""
    fp = max((1200 // w) * (1000 // d), (1200 // d) * (1000 // w))
    return int(fp * (1800 // h))


def generate(g):
    r = g.rng
    products = g.master("products")
    suppliers = [s["supplier_id"] for s in g.master("suppliers")][:20]
    story_cats = {"Small Appliances", "Drinkware", "Personal Care", "Lighting"}
    pool = sorted((p for p in products if p["sku"] not in STORY_SKUS and p["style_id"] not in STORY_STYLES
                   and p["category"] not in story_cats),
                  key=lambda p: p["sku"])
    noise = r.sample(pool, 60)

    pack_specs, pack_quotes, tech_packs, ecom_specs = [], [], [], []
    pack_changes, material_weights, pack_options, carton_specs, portfolio = [], [], [], [], []

    # ---- pack specs: pack type follows the product's pack type in master ----
    for i, p in enumerate(noise):
        spec_id = f"PKS-{i + 1:06d}"
        mp = p["pack_type"]
        if mp == "polybag":
            pack_type, material = "polybag", "polybag"
            h, w, d, wall = r.randint(250, 400), r.randint(200, 300), r.randint(10, 30), 0.05
            weight, pallet = round(r.uniform(6, 15), 1), r.randint(2500, 5000)
        elif mp == "hanging":
            pack_type, material = "hanging", "kraft"
            h, w, d, wall = r.randint(450, 700), r.randint(250, 400), r.randint(20, 60), 0.8
            weight, pallet = round(r.uniform(20, 45), 1), r.randint(300, 600)
        else:
            pack_type, material = r.choice([("carton", "corrugated")] * 6 + [("tray", "moulded_pulp")] * 2
                                           + [("rigid_box", "recycled_plastic"), ("rigid_box", "rigid_plastic")])
            h, w, d = r.randint(80, 300), r.randint(100, 300), r.randint(60, 200)
            wall = {"corrugated": 2.5, "moulded_pulp": 3.0, "recycled_plastic": 1.5, "rigid_plastic": 2.5}[material]
            wall = round(wall + r.choice([-0.5, 0, 0, 0.5]), 1)
            weight = round(2 * (h * w + h * d + w * d) / 100 * wall * r.uniform(0.012, 0.016), 1)
            pallet = pallet_units(h, w, d)
        base, rec, recyclable = MATERIALS[material]
        size = max(0.4, (h * w + h * d + w * d) / 60000) if pack_type not in ("polybag", "hanging") else 1.0
        cost = round(base * (0.55 + 0.45 * size) * r.uniform(0.92, 1.08), 2)
        pack_specs.append({
            "pack_spec_id": spec_id, "sku": p["sku"], "style_id": p["style_id"], "pack_type": pack_type,
            "material": material, "primary_supplier_id": r.choice(suppliers),
            "height_mm": h, "width_mm": w, "depth_mm": d, "wall_thickness_mm": wall, "weight_g": weight,
            "unit_cost_gbp": cost, "pallet_fill_units": pallet, "recycled_content_pct": rec,
            "recyclable": recyclable, "design_features": "", "status": r.choice(["active"] * 5 + ["testing"]),
            "created_at": g.days_ago(r.randint(60, 730)), "updated_at": g.days_ago(r.randint(5, 50)),
        })

    # ---- quotes (2-3 volume tiers per spec, first 30 specs) ----
    for spec in pack_specs[:30]:
        sup = r.choice(suppliers)
        for vol, disc in zip([100000, 200000, 400000][:r.randint(2, 3)], [1.0, 0.97, 0.94]):
            pack_quotes.append({
                "quote_id": f"QT-{len(pack_quotes) + 1:06d}", "pack_spec_id": spec["pack_spec_id"],
                "supplier_id": sup, "unit_cost_gbp": round(spec["unit_cost_gbp"] * disc * r.uniform(0.98, 1.04), 2),
                "volume_units": vol, "moq_units": vol // 10, "lead_time_days": r.randint(21, 60),
                "valid_from": g.days_ago(r.randint(0, 10)), "valid_until": g.days_ago(-r.randint(30, 90)),
                "notes": r.choice(["Standard quote", "Volume tier", "Trial offer", ""]),
            })

    # ---- tech packs: garment and bag styles only ----
    soft = [p for p in pool if p["department"] in ("Womenswear", "Menswear", "Kids") or p["category"] == "Bags"]
    seen = []
    for p in soft:
        if p["style_id"] not in seen:
            seen.append(p["style_id"])
    cat_of = {p["style_id"]: p["category"] for p in soft}
    for i, style_id in enumerate(r.sample(seen, 18)):
        cat = cat_of[style_id]
        seam = float(r.choice([60, 70, 75, 80, 90, 95]))
        outer = cat in ("Outerwear", "Schoolwear")
        zipped = cat in ("Outerwear", "Trousers", "Bags", "Schoolwear")
        zip_n = float(r.choice([100, 120, 140])) if zipped else None
        reqs = [f"Seam strength >= {int(seam)} N (TMT-0006)", "Colourfastness to rubbing grade >= 4 (TMT-0001)"]
        if zip_n:
            reqs.append(f"Zip pull strength >= {int(zip_n)} N (TMT-0005)")
        if outer:
            reqs.append("Hydrostatic head >= 1000 mm (TMT-0009)")
        tech_packs.append({
            "tech_pack_id": f"TP-{i + 1:06d}", "style_id": style_id,
            "construction_details": f"{cat}: lockstitch 11 stitches per inch, bar-tacks at stress points, "
                                    f"overlocked internal seams. Seam strength target {int(seam)} N.",
            "seam_strength_n": seam,
            "water_resistance_spec": "Hydrostatic head >= 1000 mm; seams taped" if outer else "Not required",
            "zip_pull_strength_n": zip_n, "test_requirements": "; ".join(reqs),
            "notes": "See construction drawings in the tech pack folder.", "status": "active",
            "updated_at": g.days_ago(r.randint(5, 80)),
        })

    # ---- e-commerce specs: fragile categories get cushioned cartons ----
    ecom_pool = [p for p in noise if p["pack_type"] == "carton"][:12] + [p for p in noise if p["pack_type"] != "carton"][:10]
    for i, p in enumerate(ecom_pool):
        fragile = p["category"] in FRAGILE
        if fragile:
            pt, pm = r.choice([("carton with padding", "air pillows"), ("carton with void fill", "kraft paper"),
                               ("rigid box", "bubble wrap")])
            cost, dmg = round(r.uniform(0.95, 1.9), 2), round(r.uniform(1.0, 2.6), 1)
        else:
            pt, pm = r.choice([("poly mailer", "none"), ("paper mailer", "tissue"), ("carton with tissue", "tissue")])
            cost, dmg = round(r.uniform(0.35, 0.95), 2), round(r.uniform(0.2, 1.0), 1)
        ecom_specs.append({
            "ecom_spec_id": f"EC-{i + 1:06d}", "sku": p["sku"], "pack_type": pt, "protective_material": pm,
            "unit_cost_gbp": cost, "packing_notes": f"Pack in {pt}; seal with branded tape.",
            "damage_rate_pct": dmg, "updated_at": g.days_ago(r.randint(3, 40)),
        })

    # ---- change history for noise specs only ----
    for spec in pack_specs[:15]:
        for _ in range(r.randint(1, 2)):
            ct = r.choice(["dimension", "material", "cost", "supplier", "thickness"])
            if ct == "dimension":
                old, new = f"{spec['height_mm'] + 10} mm high", f"{spec['height_mm']} mm high"
            elif ct == "thickness":
                old, new = f"{spec['wall_thickness_mm'] + 0.3:.1f} mm", f"{spec['wall_thickness_mm']:.1f} mm"
            elif ct == "supplier":
                old, new = r.choice(suppliers), spec["primary_supplier_id"]
            elif ct == "material":
                old, new = "previous board grade", spec["material"]
            else:
                old, new = f"{spec['unit_cost_gbp'] + 0.04:.2f}", f"{spec['unit_cost_gbp']:.2f}"
            pack_changes.append({
                "change_id": f"CHG-{len(pack_changes) + 1:06d}", "pack_spec_id": spec["pack_spec_id"],
                "change_type": ct, "old_value": old, "new_value": new,
                "reason": r.choice(["Annual price review", "Supplier consolidation", "Routine spec refresh", "Sustainability review"]),
                "changed_by": r.choice(BUYERS), "changed_at": g.days_ago(r.randint(3, 85)),
            })

    # ---- weights by market: same pack, same weight in each market, from the pack spec ----
    for spec in pack_specs:
        for market in ["UK", "FR", "DE", "ES"]:
            material_weights.append({
                "weight_record_id": f"WGT-{len(material_weights) + 1:06d}", "sku": spec["sku"],
                "material": spec["material"], "market_country": market, "weight_g": spec["weight_g"],
                "updated_at": g.days_ago(r.randint(5, 60)),
            })

    # ---- pack options: alternatives for a few noise specs ----
    for spec in pack_specs[:12]:
        for name, ptype, mat, mult, shelf, prot, rec in r.sample([
            ("rigid box", "rigid_box", "rigid_plastic", 1.5, "high", "high", "not recyclable"),
            ("flexible pouch", "pouch", "recycled_plastic", 0.7, "medium", "medium", "fully recyclable"),
            ("carton", "carton", "corrugated", 1.0, "medium", "medium", "fully recyclable"),
            ("moulded pulp tray", "tray", "moulded_pulp", 1.1, "medium", "medium", "fully recyclable"),
        ], 2):
            pack_options.append({
                "option_id": f"PKO-{len(pack_options) + 1:06d}", "sku": spec["sku"], "pack_spec_id": "",
                "option_name": name, "pack_type": ptype, "material": mat,
                "unit_cost_gbp": round(spec["unit_cost_gbp"] * mult, 2),
                "pallet_fill_units": max(50, int(spec["pallet_fill_units"] * (1.5 if ptype == "pouch" else 0.9))),
                "shelf_appeal": shelf, "protection_level": prot, "recyclability": rec, "notes": f"Alternative to current {spec['pack_type']}",
            })

    # ---- carton specs: from noise carton packs ----
    for spec in [s for s in pack_specs if s["pack_type"] in ("carton", "rigid_box")][:10]:
        carton_specs.append({
            "carton_id": f"CTN-{len(carton_specs) + 1:06d}", "pack_spec_id": spec["pack_spec_id"],
            "height_mm": spec["height_mm"], "width_mm": spec["width_mm"], "depth_mm": spec["depth_mm"],
            "wall_thickness_mm": spec["wall_thickness_mm"], "unit_cost_gbp": spec["unit_cost_gbp"],
            "pallet_units": spec["pallet_fill_units"], "crush_strength_kpa": round(r.uniform(45, 85), 1),
            "status": "active", "updated_at": g.days_ago(r.randint(5, 40)),
        })

    # ---- portfolio: noise SKUs with a pack type matching master ----
    notes = {
        "carton": ["Corrugated, about 70% recycled content.", "Single-material corrugated; recyclable kerbside.",
                   "Standard shipper carton; no plastic inserts."],
        "polybag": ["LDPE polybag, virgin plastic; candidate to move to recycled film.",
                    "Polybag with suffocation warning; 20% recycled film."],
        "hanging": ["Hanger plus kraft sleeve, 60% recycled paper.", "Hanging garment cover, recycled kraft."],
    }
    for i, p in enumerate(noise[:30]):
        portfolio.append({
            "portfolio_id": f"POR-{i + 1:06d}", "sku": p["sku"], "style_id": p["style_id"],
            "primary_pack_type": p["pack_type"],
            "alt_pack_types": {"carton": "tray; rigid_box", "polybag": "bag; paper mailer", "hanging": "polybag"}[p["pack_type"]],
            "sustainability_notes": r.choice(notes[p["pack_type"]]), "updated_at": g.days_ago(r.randint(5, 60)),
        })

    # ---- FY26 packaging cost by channel and SKU, scaled to the company totals above ----
    units = defaultdict(lambda: [0, 0])
    for row in g.master("sales_weekly"):
        units[row["sku"]][0] += int(row["store_units"])
        units[row["sku"]][1] += int(row["online_units"])
    cat = {p["sku"]: p["category"] for p in products}
    share = {"stores": {}, "online": {}, "wholesale": {}}
    for sku, (su, ou) in units.items():
        if sku not in cat:
            continue
        share["stores"][sku] = su
        share["online"][sku] = ou
        share["wholesale"][sku] = su
    channel_costs = []
    for ch, (orders_t, units_t, cost_t, labour) in CHANNEL_TARGETS.items():
        base = share[ch]
        tot = sum(base.values())
        # per-unit cost factor: fragile categories cost more to pack, apparel less
        wcost = {s: v * (1.35 if cat[s] in FRAGILE else 0.85) for s, v in base.items()}
        wtot = sum(wcost.values())
        for sku, v in base.items():
            sku_units = round(units_t * v / tot)
            sku_orders = max(1, round(orders_t * v / tot))
            total = round(cost_t * wcost[sku] / wtot, 2)
            if sku_units == 0:
                continue
            channel_costs.append({
                "channel_cost_id": f"CC-{len(channel_costs) + 1:06d}", "sku": sku, "channel": ch,
                "fiscal_year": "FY26", "orders": sku_orders, "units": sku_units,
                "cost_gbp_per_order": round(total / sku_orders, 2), "cost_gbp_per_unit": round(total / sku_units, 3),
                "packing_labour_pct": round(labour * r.uniform(0.85, 1.15), 1), "total_cost_gbp": total,
                "updated_at": g.days_ago(r.randint(5, 40)),
            })

    return {
        "pack_specs": pack_specs, "pack_materials": [], "pack_quotes": pack_quotes, "tech_packs": tech_packs,
        "ecommerce_specs": ecom_specs, "pack_change_history": pack_changes,
        "material_weights_by_market": material_weights, "pack_options": pack_options,
        "carton_specs": carton_specs, "channel_packaging_costs": channel_costs, "packaging_portfolio": portfolio,
    }
