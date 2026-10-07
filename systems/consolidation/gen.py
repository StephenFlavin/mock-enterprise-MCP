"""Consolidation system: financial KPIs, guidance, close tasks and intercompany items."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng

    # Get master entities
    entities = g.master("legal_entities")
    entity_ids = [e["entity_id"] for e in entities]
    employees = g.master("employees")

    close_tasks = []
    financial_kpis = []
    guidance_and_outlook = []
    inventory_supply_chain_kpis = []
    monthly_performance = []
    intercompany_items = []
    close_task_reminders = []

    # Generate close tasks for the current month
    for entity in entities:
        entity_id = entity["entity_id"]
        # Create 5-8 close tasks per entity
        num_tasks = r.randint(5, 8)
        for i in range(num_tasks):
            owner = r.choice(employees)
            task_due = g.as_of + timedelta(days=r.randint(1, 15))
            status = r.choices(["open", "in_progress", "completed"], [0.5, 0.3, 0.2])[0]
            priority = r.choice(["low", "medium", "high", "urgent"])

            task_id = f"CT-{len(close_tasks) + 1:06d}"
            close_tasks.append({
                "task_id": task_id,
                "task_name": r.choice([
                    "Review revenue accruals",
                    "Reconcile balance sheet accounts",
                    "Verify FX revaluations",
                    "Complete intercompany reconciliation",
                    "Approve journal entries",
                    "Finalize accrued expenses",
                    "Reconcile bank accounts",
                    "Verify inventory balances",
                ]),
                "owner_id": owner["employee_id"],
                "due_date": task_due,
                "status": status,
                "entity_id": entity_id,
                "priority": priority,
                "created_at": g.as_of - timedelta(days=r.randint(1, 5)),
                "updated_at": g.as_of - timedelta(hours=r.randint(0, 48)),
                "notes": r.choice([None, "In progress", "Awaiting vendor response", "Completed pending approval"]),
            })

    # Generate financial KPIs for last 12 months
    for i in range(12):
        month_date = g.as_of - timedelta(days=30 * i)
        period = month_date.strftime("%Y-%m")
        for entity in entities:
            entity_id = entity["entity_id"]
            revenue = float(r.randint(5000000, 15000000))
            gp_pct = float(r.randint(35, 55))
            gross_profit = revenue * (gp_pct / 100)
            op_margin = float(r.randint(5, 20))
            operating_profit = revenue * (op_margin / 100)
            revenue_growth = float(r.randint(-10, 15))
            inventory_value = float(r.randint(1000000, 5000000))
            inventory_turn = float(r.randint(4, 12))
            ebitda = operating_profit * float(r.randint(120, 150)) / 100

            financial_kpis.append({
                "period": period,
                "entity_id": entity_id,
                "revenue_gbp": revenue,
                "gross_profit_gbp": gross_profit,
                "gross_margin_pct": gp_pct,
                "operating_profit_gbp": operating_profit,
                "operating_margin_pct": op_margin,
                "revenue_growth_pct": revenue_growth,
                "inventory_value_gbp": inventory_value,
                "inventory_turn": inventory_turn,
                "ebitda_gbp": ebitda,
            })

    # Generate current and future guidance
    current_guidance_date = g.as_of - timedelta(days=r.randint(10, 30))
    for q in range(1, 5):
        period_str = f"2026-Q{q}"
        go_id = f"GO-000{q}"
        revenue_base = float(r.randint(20000000, 30000000))

        guidance_and_outlook.append({
            "id": go_id,
            "period": period_str,
            "guidance_date": current_guidance_date,
            "guidance_revenue_low_gbp": revenue_base * 0.95,
            "guidance_revenue_high_gbp": revenue_base * 1.05,
            "guidance_ebitda_low_gbp": revenue_base * 0.08,
            "guidance_ebitda_high_gbp": revenue_base * 0.12,
            "guidance_status": "current" if q >= 4 else "superseded",
            "outlook_summary": r.choice([
                "Steady growth expected driven by seasonal demand",
                "Cost pressures offset by operational improvements",
                "Inventory management remains a focus area",
                "Strong momentum in core categories",
            ]),
        })

    # Generate inventory and supply chain KPIs for last 12 months
    for i in range(12):
        month_date = g.as_of - timedelta(days=30 * i)
        period = month_date.strftime("%Y-%m")
        for entity in entities:
            entity_id = entity["entity_id"]
            inventory_supply_chain_kpis.append({
                "period": period,
                "entity_id": entity_id,
                "average_inventory_gbp": float(r.randint(1000000, 5000000)),
                "inventory_turn": float(r.randint(4, 12)),
                "dc_operating_cost_pct": round(float(r.randint(5, 12)) / 100, 4) * 100,
                "freight_cost_pct": round(float(r.randint(2, 6)) / 100, 4) * 100,
                "supply_chain_cost_pct": round(float(r.randint(8, 18)) / 100, 4) * 100,
                "carrier_otif_pct": float(r.randint(92, 99)),
                "supplier_otif_pct": float(r.randint(85, 98)),
                "days_payable_outstanding": r.randint(30, 60),
            })

    # Generate monthly performance for last 12 months
    for i in range(12):
        month_date = g.as_of - timedelta(days=30 * i)
        period = month_date.strftime("%Y-%m")
        for entity in entities:
            entity_id = entity["entity_id"]
            revenue = float(r.randint(5000000, 15000000))
            budget_variance_pct = float(r.randint(-5, 8))
            revenue_budget_variance = revenue * (budget_variance_pct / 100)
            gp_pct = float(r.randint(35, 55))
            gross_profit = revenue * (gp_pct / 100)
            op_margin = float(r.randint(5, 20))
            operating_profit = revenue * (op_margin / 100)
            op_budget_variance = operating_profit * float(r.randint(-10, 15)) / 100

            monthly_performance.append({
                "period": period,
                "entity_id": entity_id,
                "revenue_gbp": revenue,
                "revenue_vs_budget_gbp": revenue_budget_variance,
                "revenue_vs_budget_pct": budget_variance_pct,
                "gross_profit_gbp": gross_profit,
                "gp_pct": gp_pct,
                "operating_profit_gbp": operating_profit,
                "op_vs_budget_gbp": op_budget_variance,
                "operating_margin_pct": op_margin,
                "notes": r.choice([None, "Favorable variances in core categories", "Cost pressures from logistics"]),
            })

    # Generate intercompany items for reconciliation
    if len(entities) > 1:
        for i in range(20):
            from_idx = r.randint(0, len(entities) - 2)
            to_idx = from_idx + 1
            amount = float(r.randint(100000, 2000000))
            tx_date = g.as_of - timedelta(days=r.randint(0, 90))
            posting_date = tx_date + timedelta(days=r.randint(0, 5))

            # Some unmatched, some matched, some partial
            status = r.choices(["unmatched", "matched", "partial"], [0.4, 0.5, 0.1])[0]
            variance = 0 if status == "matched" else float(r.randint(-50000, 50000))
            variance_reason = None if status == "matched" else r.choice(["timing", "FX variance", "missing invoice"])

            item_id = f"ICI-{len(intercompany_items) + 1:06d}"
            intercompany_items.append({
                "item_id": item_id,
                "entity_from_id": entities[from_idx]["entity_id"],
                "entity_to_id": entities[to_idx]["entity_id"],
                "transaction_amount_gbp": amount,
                "transaction_currency": "GBP",
                "transaction_date": tx_date,
                "posting_date": posting_date,
                "invoice_no": f"INV-{r.randint(100000, 999999)}",
                "matched_with_id": None,
                "match_status": status,
                "variance_gbp": variance,
                "variance_reason": variance_reason,
                "created_at": tx_date,
            })

    return {
        "close_tasks": close_tasks,
        "financial_kpis": financial_kpis,
        "guidance_and_outlook": guidance_and_outlook,
        "inventory_supply_chain_kpis": inventory_supply_chain_kpis,
        "monthly_performance": monthly_performance,
        "intercompany_items": intercompany_items,
        "close_task_reminders": close_task_reminders,
    }
