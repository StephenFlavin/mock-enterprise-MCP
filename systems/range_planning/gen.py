"""Range planning data: strategic roles, range gaps, and background tasks."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    products = g.master("products")

    # Assign strategic roles to products
    strategic_roles = []
    categories = set()
    for p in products:
        if p.get("status") in ("discontinued", "new"):
            continue
        role = r.choices(["core", "growth", "seasonal", "experimental", "clearance"],
                        [50, 25, 15, 7, 3])[0]
        strategic_roles.append({
            "sku": p["sku"],
            "strategic_role": role
        })
        categories.add(p.get("category", "Misc"))

    # Generate range gaps for main categories
    range_gaps = []
    gap_categories = list(categories)[:15]  # Focus on 15 main categories
    for i, cat in enumerate(gap_categories):
        size = r.randint(50000, 500000)
        competitors = r.randint(2, 12)
        products_in_cat = sum(1 for p in products if p.get("category") == cat)
        range_gaps.append({
            "gap_id": f"RGP-{i + 1:06d}",
            "category": cat,
            "gap_description": f"Under-supplied in {cat}; competitors have 30-50% more SKUs",
            "opportunity_size_gbp": float(size),
            "competitor_count": competitors,
            "product_count_current": products_in_cat,
            "created_at": g.as_of - timedelta(days=r.randint(14, 90))
        })

    # Generate some draft range plans
    product_range_plan = []
    for i in range(25):
        p = r.choice(products)
        action = r.choices(["extend", "refresh", "reprice", "delete"], [40, 35, 20, 5])[0]
        status = r.choices(["draft", "approved", "in_progress"], [50, 35, 15])[0]
        approved_by = r.choice(["EMP-00111", "EMP-00123", "EMP-00456", None])
        product_range_plan.append({
            "plan_id": f"PRP-{i + 1:06d}",
            "sku": p["sku"],
            "action": action,
            "status": status,
            "approved_by": approved_by if status in ("approved", "in_progress") else None,
            "created_at": g.as_of - timedelta(days=r.randint(1, 60)),
            "updated_at": g.as_of - timedelta(days=r.randint(0, 20))
        })

    # Generate range gap requests
    range_gap_requests = []
    for i in range(10):
        status = r.choices(["submitted", "approved", "rejected", "investigated"], [30, 40, 20, 10])[0]
        category = r.choice(gap_categories)
        range_gap_requests.append({
            "request_id": f"RQR-{i + 1:06d}",
            "category": category,
            "reason": f"High market interest; {r.randint(2, 8)} competitor SKUs; estimated £{r.randint(50, 500)}k opportunity",
            "status": status,
            "created_by": r.choice(["EMP-00123", "EMP-00456", "EMP-00789", "EMP-01234"]),
            "created_at": g.as_of - timedelta(days=r.randint(1, 45)),
            "updated_at": g.as_of - timedelta(days=r.randint(0, 20))
        })

    # Generate SKU review tasks
    sku_review_tasks = []
    for i in range(12):
        p = r.choice(products)
        reasons = [
            "Costs more to serve than revenue earned",
            "Sales down 50% YoY, margin declining",
            "Not aligned with strategic plan",
            "Clearance candidate; low velocity",
            "Performance below category benchmark"
        ]
        status = r.choices(["open", "in_progress", "completed", "cancelled"], [40, 30, 20, 10])[0]
        sku_review_tasks.append({
            "task_id": f"RVW-{i + 1:06d}",
            "sku": p["sku"],
            "reason": r.choice(reasons),
            "owner": r.choice(["EMP-00789", "EMP-01234", "EMP-01567", "EMP-02000"]),
            "status": status,
            "recommendation": r.choice(["delete", "refresh", "reprice", "investigate"]) if status == "completed" else None,
            "created_at": g.as_of - timedelta(days=r.randint(1, 60)),
            "updated_at": g.as_of - timedelta(days=r.randint(0, 30))
        })

    return {
        "product_strategic_roles": strategic_roles,
        "range_gaps": range_gaps,
        "product_range_plan": product_range_plan,
        "range_gap_requests": range_gap_requests,
        "sku_review_tasks": sku_review_tasks
    }
