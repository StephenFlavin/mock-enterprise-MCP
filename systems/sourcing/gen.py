"""Sourcing data: story rows live in seed/*.csv; gen.py adds historical RFQ noise, a capability line
for every other factory and some unrelated material and pack suppliers."""
import csv
from datetime import timedelta
from pathlib import Path

SEED = Path(__file__).parent / "seed"
STORY_CATEGORIES = {"Outerwear", "Bedding", "Trousers", "Dresses"}
ORIGIN_PRICE = {"CN": 0.85, "VN": 0.90, "IN": 0.88, "BD": 0.82, "TR": 1.05, "PT": 1.25, "IT": 1.30, "MX": 1.05,
                "PL": 1.15, "FR": 1.35, "DE": 1.40, "GB": 1.45}
ORIGIN_LEAD = {"CN": 90, "VN": 75, "IN": 80, "BD": 85, "TR": 30, "PT": 25, "IT": 28, "MX": 40, "PL": 30, "FR": 30,
               "DE": 28, "GB": 21}
GENERIC_CAPABILITY = {"Womenswear": "woven dresses and blouses", "Menswear": "woven shirts and trousers",
                      "Kids": "kidswear cut-and-sew", "Home": "home textiles", "Accessories": "accessories and soft goods",
                      "Electricals": "electrical assembly", "Beauty": "beauty fill and pack"}


def _seed_keys(name, col):
    with open(SEED / f"{name}.csv", newline="") as fh:
        return {r[col] for r in csv.DictReader(fh)}


def generate(g):
    r = g.rng
    products = [p for p in g.master("products") if p["status"] == "active" and p["category"] not in STORY_CATEGORIES]
    factories = [f for f in g.master("factories") if f["status"] == "approved"]
    suppliers = {s["supplier_id"]: s for s in g.master("suppliers")}
    fac_by_id = {f["factory_id"]: f for f in g.master("factories")}

    # Historical RFQs on unrelated SKUs (price history by origin)
    rfqs, responses = [], []
    n_resp = 0
    for i in range(1, 46):
        p = r.choice(products)
        created = g.date_between(700, 120)
        qty = r.choice([3000, 5000, 8000, 12000, 20000, 30000])
        base = float(p["unit_cost_gbp"])
        rid = f"RFQ-{i:06d}"
        picks = [fac_by_id[p["factory_id"]]] + r.sample(factories, 2)
        status = r.choice(["awarded", "awarded", "evaluated", "cancelled"])
        rfqs.append({"rfq_id": rid, "product_name": p["name"], "sku": p["sku"], "required_qty": qty,
                     "destination_site_id": r.choice(["DC1", "DC2", "DC3"]),
                     "required_date": created + timedelta(days=150),
                     "expected_unit_cost_gbp": round(base, 2), "specification": f"Seasonal buy of {p['name']}",
                     "invited_supplier_ids": ",".join(f["supplier_id"] for f in picks), "status": status,
                     "created_at": created, "issued_at": created + timedelta(days=2),
                     "updated_at": created + timedelta(days=30)})
        for j, f in enumerate(picks):
            n_resp += 1
            factor = ORIGIN_PRICE[f["country"]] if j else r.uniform(0.97, 1.05)
            unit = round(base * factor * r.uniform(0.95, 1.06), 2)
            sub = created + timedelta(days=r.randint(10, 20))
            responses.append({
                "response_id": f"RFR-{n_resp:06d}", "rfq_id": rid, "supplier_id": f["supplier_id"],
                "factory_id": f["factory_id"], "status": "accepted" if (j == 0 and status == "awarded") else "rejected",
                "unit_cost_gbp": unit, "total_cost_gbp": round(unit * qty, 2),
                "lead_time_days": ORIGIN_LEAD[f["country"]] + r.randint(-5, 10),
                "minimum_order_qty": r.choice([300, 500, 1000, 2000]), "tooling_cost_gbp": 0,
                "payment_terms": f"{suppliers[f['supplier_id']]['payment_terms_days']} net",
                "quality_certification": f["certifications"], "compliance_score": r.randint(70, 95),
                "capacity_units_available": r.choice([20000, 40000, 60000, 100000]),
                "capability_notes": "", "submitted_at": sub, "notes": "", "updated_at": sub})

    # One capability line for every factory the stories do not describe
    story_factories = _seed_keys("factory_capabilities", "factory_id")
    caps = []
    for f in g.master("factories"):
        if f["factory_id"] in story_factories:
            continue
        cat = suppliers[f["supplier_id"]]["category_focus"]
        monthly = int(f["capacity_units_month"])
        caps.append({"factory_id": f["factory_id"], "capability": GENERIC_CAPABILITY[cat],
                     "line_capacity_units_season": int(round(monthly * 3 * r.uniform(0.25, 0.5), -3)), "notes": ""})

    # Unrelated cotton and pack suppliers (never polyester or the story pack materials)
    story_sup = _seed_keys("supplier_materials", "supplier_id")
    others = [s for s in g.master("suppliers") if s["supplier_id"] not in story_sup and s["status"] == "active"]
    mats = []
    for s in r.sample(others, 6):
        mat, prem = r.choice([("organic cotton (GOTS)", 22.0), ("recycled cotton (post-industrial)", 24.0)])
        mats.append({"supplier_id": s["supplier_id"], "material": mat,
                     "material_class": "alternative_fibre", "recycled_content_pct": 50 if "recycled" in mat else 0,
                     "certification": "GOTS", "price_premium_vs_virgin_pct": prem, "lead_time_days": r.choice([30, 45, 60]),
                     "available_capacity": r.choice([200, 400, 800]), "capacity_unit": "tonnes", "notes": "Cotton, not a polyester substitute"})
    for s in r.sample([x for x in others if x["supplier_id"] not in {m["supplier_id"] for m in mats}], 5):
        mats.append({"supplier_id": s["supplier_id"], "material": r.choice(["polybag (LDPE)", "hanger", "tissue paper"]),
                     "material_class": "packaging", "recycled_content_pct": r.choice([0, 30, 50]), "certification": "",
                     "price_premium_vs_virgin_pct": "", "lead_time_days": r.choice([14, 21, 28]),
                     "available_capacity": r.choice([500000, 1000000, 2000000]), "capacity_unit": "packs", "notes": ""})

    return {"rfq": rfqs, "rfq_responses": responses, "quote_cost_components": [], "rfx_events": [],
            "rfx_responses": [], "rfx_response_scores": [], "bid_references": [],
            "tender_scorecard_templates": [], "scorecard_criteria": [], "sourcing_awards": [],
            "rfq_clarifications": [], "factory_capabilities": caps, "supplier_materials": mats}
