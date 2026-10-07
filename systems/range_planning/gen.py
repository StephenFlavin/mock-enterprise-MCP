"""Range planning data: strategic roles, category gaps, range plan, gap requests and review tasks."""
from datetime import timedelta

STORY_SKUS = {"K-1700", "PF-220", "SKU-101904", "SKU-103640", "SKU-101876"}
SEEDED_GAP_CATS = {"Small Appliances", "Audio", "Jewellery"}


def generate(g):
    r = g.rng
    products = g.master("products")
    employees = g.master("employees")
    buyer_ids = [e["employee_id"] for e in employees if e.get("department") == "Buying" and e.get("status") == "active"]

    roles = []
    for p in products:
        if p["status"] == "discontinued":
            continue
        r = g.rng_for("role", p["sku"])
        if p["status"] == "clearance":
            role = r.choices(["clearance", "seasonal", "core"], [80, 15, 5])[0]
        elif p["status"] == "new":
            role = r.choices(["growth", "experimental", "seasonal"], [55, 35, 10])[0]
        else:
            role = r.choices(["core", "growth", "seasonal", "experimental"], [55, 25, 15, 5])[0]
        roles.append({"sku": p["sku"], "strategic_role": role,
                      "rationale": {"core": "Everyday volume line for the category",
                                    "growth": "Building share; invest in range depth",
                                    "seasonal": "Peaks with the season; plan buy depth accordingly",
                                    "experimental": "Test line; judge on sell-through",
                                    "clearance": "Being sold through; no replenishment"}[role]})

    r = g.rng
    counts = {}
    for p in products:
        if p["status"] == "new":
            continue
        counts[p["category"]] = counts.get(p["category"], 0) + 1
    gaps = []
    cats = sorted(c for c in counts if c not in SEEDED_GAP_CATS)
    for i, cat in enumerate(r.sample(cats, 10)):
        comp = r.randint(2, 10)
        gaps.append({
            "gap_id": f"RGP-{i + 1:06d}", "category": cat, "segment": "All",
            "gap_description": f"Whole-category view of {cat}; competitors carry more SKUs at similar price points",
            "market_size_gbp": float(r.randint(200, 900) * 1_000_000),
            "market_growth_pct": round(r.uniform(-3, 9), 1),
            "opportunity_size_gbp": float(r.randint(15, 60) * 10_000),
            "est_margin_pct": round(r.uniform(28, 55), 1),
            "competitor_count": comp, "competitors": f"{comp} UK competitors",
            "product_count_current": counts[cat],
            "fill_feasibility": r.choice(["medium", "low"]),
            "created_at": g.as_of - timedelta(days=r.randint(14, 90)),
        })

    story_plan = {"K-1700", "PF-220", "SKU-101904", "SKU-103640", "SKU-101876"}
    pool = [p for p in products if p["sku"] not in story_plan and p["status"] not in ("discontinued", "new")]
    plan = []
    for i, p in enumerate(r.sample(pool, 20)):
        action = r.choices(["extend", "refresh", "reprice", "delete"], [40, 30, 20, 10])[0]
        status = r.choices(["draft", "approved", "in_progress", "completed"], [40, 25, 15, 20])[0]
        plan.append({
            "sku": p["sku"], "plan_id": f"PRP-{i + 1:06d}", "action": action, "status": status,
            "approved_by": r.choice(buyer_ids) if status != "draft" else None,
            "created_at": g.as_of - timedelta(days=r.randint(30, 120)),
            "updated_at": g.as_of - timedelta(days=r.randint(25, 29)),
        })

    requests = []
    for i in range(8):
        cat = r.choice(cats)
        requests.append({
            "request_id": f"RQR-{i + 1:06d}", "category": cat,
            "reason": f"Competitors carry {r.randint(2, 8)} more SKUs in {cat}",
            "status": r.choice(["approved", "rejected", "investigated", "submitted"]),
            "created_by": r.choice(buyer_ids),
            "created_at": g.as_of - timedelta(days=r.randint(30, 90)),
            "updated_at": g.as_of - timedelta(days=r.randint(20, 29)),
        })

    tasks = []
    reasons = ["Sales down year on year, margin declining", "Not aligned with strategic plan",
               "Clearance candidate; low velocity", "Performance below category benchmark"]
    for i, p in enumerate(r.sample(pool, 10)):
        status = r.choice(["open", "in_progress", "completed", "cancelled"])
        tasks.append({
            "task_id": f"RVW-{i + 1:06d}", "sku": p["sku"], "reason": r.choice(reasons),
            "owner": r.choice(buyer_ids), "status": status,
            "recommendation": r.choice(["delete", "refresh", "reprice", "investigate"]) if status == "completed" else None,
            "created_at": g.as_of - timedelta(days=r.randint(30, 90)),
            "updated_at": g.as_of - timedelta(days=r.randint(20, 29)),
        })

    return {"product_strategic_roles": roles, "range_gaps": gaps, "product_range_plan": plan,
            "range_gap_requests": requests, "sku_review_tasks": tasks}
