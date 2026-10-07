"""Python helpers for the recall system."""


def incident_history(ctx, product_type=None, department=None, issue=None, sku=None, group_by=None, days=1460):
    group_by = group_by or ("case" if (sku or issue) else "product_type")
    params = {"pt": product_type, "dep": department, "iss": issue, "sku": sku, "days": int(days or 1460)}
    where = """
        WHERE ($pt IS NULL OR lower(p.category) = lower($pt))
          AND ($dep IS NULL OR lower(p.department) = lower($dep))
          AND ($iss IS NULL OR h.issue ILIKE '%' || $iss || '%')
          AND ($sku IS NULL OR h.sku = $sku)
          AND CAST(h.reported_at AS DATE) >= CAST($as_of AS DATE) - INTERVAL (CAST($days AS INT)) DAY"""
    cost = """(k.refunds_gbp + k.logistics_gbp + k.comms_gbp + k.legal_gbp + k.other_gbp)"""
    if group_by == "case":
        return ctx.q(f"""
            SELECT h.history_id, h.sku, p.category AS product_type, CAST(h.reported_at AS DATE) AS reported, h.issue, h.severity,
                   h.outcome, h.recall_id, h.units_sold, round({cost}, 0) AS recall_cost_gbp,
                   h.reputational_outcome, h.comms_lessons
            FROM incident_history h
            LEFT JOIN master.products p ON p.sku = h.sku
            LEFT JOIN recall_costs k ON k.recall_id = h.recall_id
            {where}
            ORDER BY h.reported_at DESC""", **params)
    return ctx.q(f"""
        SELECT p.category AS product_type, p.department, count(*) AS incidents,
               count(*) FILTER (WHERE h.severity IN ('severe', 'critical')) AS severe_or_critical,
               count(*) FILTER (WHERE h.outcome = 'recall') AS recalls,
               count(*) FILTER (WHERE h.outcome = 'withdrawal') AS withdrawals,
               mode(h.issue) AS most_common_issue,
               round(sum({cost}), 0) AS total_recall_cost_gbp,
               CAST(max(h.reported_at) AS DATE) AS latest_incident
        FROM incident_history h
        LEFT JOIN master.products p ON p.sku = h.sku
        LEFT JOIN recall_costs k ON k.recall_id = h.recall_id
        {where}
        GROUP BY p.category, p.department
        ORDER BY recalls DESC, incidents DESC, product_type""", **params)
