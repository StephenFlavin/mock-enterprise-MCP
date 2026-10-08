def search_contacts(ctx, issue_keyword=None, reason=None, category=None, date_from=None, group_by="none"):
    where = ["CAST(c.contact_date AS DATE) >= CAST($date_from AS DATE)", "CAST(c.contact_date AS DATE) <= CAST($as_of AS DATE)"]
    params = {"date_from": date_from or "-90d", "as_of": ctx.as_of}
    if issue_keyword:
        for i, w in enumerate(str(issue_keyword).split()):
            where.append(f"c.issue ILIKE $k{i}")
            params[f"k{i}"] = f"%{w}%"
    if reason:
        where.append("c.reason = $reason")
        params["reason"] = reason
    if category:
        where.append("p.category ILIKE $category")
        params["category"] = category
    base = ("FROM customer_service_contacts c LEFT JOIN master.products p ON p.sku = c.sku WHERE "
            + " AND ".join(where))
    group_by = group_by or "none"
    if group_by == "none":
        return ctx.q(f"""SELECT c.contact_id, c.contact_date, c.order_id, c.sku, p.name AS product_name, p.category,
                         c.reason, c.issue, c.data_error_type, c.contact_type, c.status, c.cost_gbp
                         {base} ORDER BY c.contact_date DESC""", **params)
    key = {"error_type": "c.data_error_type", "category": "p.category", "issue": "c.issue", "sku": "c.sku"}[group_by]
    extra = {"error_type": " AND c.data_error_type IS NOT NULL", "category": " AND c.sku IS NOT NULL",
             "sku": " AND c.sku IS NOT NULL", "issue": ""}[group_by]
    name = {"error_type": "data_error_type", "category": "category", "issue": "issue", "sku": "sku"}[group_by]
    return ctx.q(f"""SELECT {key} AS {name}, count(*) AS contacts,
                     count(*) FILTER (WHERE c.data_error_type IS NOT NULL) AS data_error_contacts,
                     count(DISTINCT c.order_id) AS orders,
                     round(sum(c.cost_gbp), 2) AS total_cost_gbp,
                     round(sum(c.cost_gbp) FILTER (WHERE c.data_error_type IS NOT NULL), 2) AS data_error_cost_gbp,
                     round(avg(c.cost_gbp), 2) AS avg_cost_gbp
                     {base}{extra} GROUP BY ALL ORDER BY total_cost_gbp DESC""", **params)
