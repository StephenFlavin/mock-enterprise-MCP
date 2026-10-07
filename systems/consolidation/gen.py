"""Consolidation system: entity P&L and KPIs, guidance, month-end close tasks and intercompany items.

The KPI tables are generated from one per-entity model (September 2026 figures below, trending back 12 months), so
financial_kpis, monthly_performance and inventory_supply_chain_kpis always agree. September operating profit by
entity matches the budgeting system (total £1.8m below budget). Story rows (close tasks, UK-PL intercompany,
guidance) are in seed/.
"""
from datetime import timedelta

# September (latest closed month) per entity. Operating profit and variance agree with budgeting's September view.
ENT = {
    "LE-UK": dict(rev=62_000_000, gm=33.0, op=3_698_000, op_var=-1_290_000, rev_var=-1_550_000, growth=2.1, turn=4.9,
                  py_gm=34.2, py_turn=5.2, py_opm=8.4, freight=6.0, dc=4.4, carrier=91.6, supplier=85.8, dpo=40,
                  note="Operating profit £1.29m below budget: peak air and ocean freight above budget, early markdowns on "
                       "knitwear and outerwear in a warm September, £310k autumn marketing phased early."),
    "LE-IE": dict(rev=5_500_000, gm=34.0, op=549_000, op_var=50_000, rev_var=80_000, growth=2.0, turn=5.4,
                  py_gm=34.3, py_turn=5.5, py_opm=9.6, freight=5.2, dc=3.9, carrier=93.4, supplier=88.0, dpo=44,
                  note="£50k ahead of budget on stronger Irish store trading."),
    "LE-NL": dict(rev=11_000_000, gm=34.5, op=758_000, op_var=-240_000, rev_var=-300_000, growth=3.8, turn=5.6,
                  py_gm=35.0, py_turn=5.7, py_opm=7.8, freight=5.5, dc=4.6, carrier=92.4, supplier=87.0, dpo=42,
                  note="£240k below budget: delayed inbound shipments and Venlo DC peak agency labour booked early (£85k phasing)."),
    "LE-DE": dict(rev=10_000_000, gm=35.0, op=848_000, op_var=0, rev_var=-120_000, growth=5.0, turn=5.8,
                  py_gm=35.2, py_turn=5.9, py_opm=8.7, freight=5.3, dc=4.1, carrier=93.0, supplier=88.5, dpo=43,
                  note="On budget: £60k supplier rebate timing shortfall offset by better category mix."),
    "LE-US": dict(rev=12_000_000, gm=36.0, op=678_000, op_var=-320_000, rev_var=-400_000, growth=4.5, turn=5.3,
                  py_gm=36.8, py_turn=5.5, py_opm=7.1, freight=6.3, dc=4.0, carrier=90.8, supplier=84.9, dpo=39,
                  note="£320k below budget: USD-denominated purchase costs and tariff-driven landed cost increases."),
}
SEASON = {1: 0.92, 2: 0.88, 3: 0.95, 4: 0.98, 5: 1.0, 6: 1.0, 7: 0.97, 8: 0.98, 9: 1.0, 10: 1.04, 11: 1.18, 12: 1.4}
OLD_NOTES = [None, None, "Trading in line with budget", "Favourable variances in core categories",
             "Freight costs ahead of budget", "Markdown pressure in seasonal ranges"]
TASK_ENTITIES = ["LE-UK", "LE-IE", "LE-NL", "LE-DE", "LE-US", "LE-HK", "LE-PL"]
FINANCE_STAFF = [f"EMP-{n:05d}" for n in range(77, 90)]
IC_PAIRS = [("LE-UK", "LE-IE", "EUR"), ("LE-IE", "LE-NL", "EUR"), ("LE-NL", "LE-DE", "EUR"), ("LE-DE", "LE-US", "USD")]
IC_REASONS = ["timing", "FX variance", "missing invoice"]


def _periods(as_of):
    y, m = (as_of.year, as_of.month - 1) if as_of.month > 1 else (as_of.year - 1, 12)
    out = []
    for i in range(12):  # latest closed month first
        out.append((y, m))
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    return out


def generate(g):
    r = g.rng
    kpis, monthly, sc, tasks, ics = [], [], [], [], []
    entities = [{k: e[k] for k in ("entity_id", "name", "country", "currency")} for e in g.master("legal_entities")]
    entities.append({"entity_id": "LE-PL", "name": "Harbour & Vale Polska Sp. z o.o.", "country": "PL", "currency": "PLN"})

    for i, (y, m) in enumerate(_periods(g.as_of)):
        period = f"{y}-{m:02d}"
        season = SEASON[m] / SEASON[9]
        for ent, e in ENT.items():
            noise = (lambda s: r.uniform(-s, s)) if i else (lambda s: 0.0)
            rev = round(e["rev"] * season * (1 - 0.004 * i) * (1 + noise(0.015)), -3)
            gm = round(e["gm"] + 0.1 * i + noise(0.2), 1)
            gp = round(rev * gm / 100)
            if i == 0:
                op, op_var, rev_var, note = e["op"], e["op_var"], e["rev_var"], e["note"]
                opm = round(op / rev * 100, 1)
            else:
                opm = round(e["op"] / e["rev"] * 100 + 0.12 * i + noise(0.25), 1)
                op = round(rev * opm / 100, -3)
                op_var = -round(op * 0.015, -3) if i == 1 else round(op * noise(0.04), -3)
                rev_var = round(rev * noise(0.02), -3)
                note = r.choice(OLD_NOTES)
            turn = round(e["turn"] + 0.05 * i + noise(0.08), 1)
            growth = round(e["growth"] + 0.1 * i + noise(1.0), 1)
            inv = round(rev * 12 * (1 - gm / 100) / turn, -3)
            dep = rev * 0.028
            kpis.append({
                "period": period, "entity_id": ent, "revenue_gbp": rev, "gross_profit_gbp": gp, "gross_margin_pct": gm,
                "operating_profit_gbp": op, "operating_margin_pct": opm, "revenue_growth_pct": growth,
                "inventory_value_gbp": inv, "inventory_turn": turn, "ebitda_gbp": round(op + dep, -3),
                "gross_margin_prior_year_pct": round(e["py_gm"] + noise(0.15), 1),
                "inventory_turn_prior_year": round(e["py_turn"] + noise(0.05), 1),
                "notes": ("Gross margin 1.2pts below last year on freight and markdowns; inventory turn slower than last year"
                          if i == 0 and ent == "LE-UK" else None),
            })
            monthly.append({
                "period": period, "entity_id": ent, "revenue_gbp": rev, "revenue_vs_budget_gbp": rev_var,
                "revenue_vs_budget_pct": round(rev_var / (rev - rev_var) * 100, 1), "gross_profit_gbp": gp, "gp_pct": gm,
                "operating_profit_gbp": op, "op_vs_budget_gbp": op_var, "operating_margin_pct": opm, "notes": note,
            })
            freight = round(e["freight"] - 0.12 * i + noise(0.05), 2)
            dc = round(e["dc"] - 0.04 * i + noise(0.04), 2)
            sc.append({
                "period": period, "entity_id": ent, "average_inventory_gbp": inv, "inventory_turn": turn,
                "dc_operating_cost_pct": dc, "freight_cost_pct": freight,
                "supply_chain_cost_pct": round(freight + dc + 1.4 + noise(0.05), 2),
                "carrier_otif_pct": round(e["carrier"] + 0.25 * i + noise(0.3), 1),
                "supplier_otif_pct": round(e["supplier"] + 0.3 * i + noise(0.4), 1),
                "days_payable_outstanding": round(e["dpo"] + 0.4 * i + noise(0.6)),
            })

    # Superseded earlier guidance (current guidance is seeded); the guidance for 2026-Q4 was issued lower this quarter
    guidance = [{
        "id": "GO-900003", "period": "2026-Q4", "guidance_date": g.as_of - timedelta(days=98),
        "guidance_revenue_low_gbp": 50_000_000, "guidance_revenue_high_gbp": 54_000_000,
        "guidance_ebitda_low_gbp": 5_900_000, "guidance_ebitda_high_gbp": 6_800_000, "guidance_status": "superseded",
        "outlook_summary": "Initial Q4 guidance before freight and gross margin pressure emerged in the summer.",
        "key_assumptions": "Freight at 5.2% of revenue; gross margin flat on last year.",
        "update_policy": "Reviewed at each quarterly results.",
    }]

    # Month-end close checklist noise (current close, due soon); the open-for-months and story tasks are in seed/
    for ent in TASK_ENTITIES:
        for _ in range(r.randint(2, 4)):
            tasks.append({
                "task_id": f"CT-{len(tasks) + 1:06d}",
                "task_name": r.choice(["Review revenue accruals", "Verify FX revaluations", "Complete intercompany reconciliation",
                                       "Approve journal entries", "Reconcile bank accounts", "Verify inventory balances"]),
                "owner_id": r.choice(FINANCE_STAFF), "due_date": g.as_of + timedelta(days=r.randint(1, 12)),
                "status": r.choices(["open", "in_progress", "completed"], [0.4, 0.3, 0.3])[0], "entity_id": ent,
                "priority": r.choice(["low", "medium", "medium", "high"]),
                "created_at": g.as_of - timedelta(days=r.randint(1, 5)),
                "updated_at": g.as_of - timedelta(hours=r.randint(0, 48)),
                "notes": r.choice([None, "In progress", "Awaiting supporting schedule"]),
            })

    # Intercompany noise between neighbouring entities (UK-PL and UK-NL stories are seeded); almost all matched
    for k in range(24):
        frm, to, ccy = r.choice(IC_PAIRS)
        amount = float(r.randint(20, 400) * 1000)
        tx = g.as_of - timedelta(days=r.randint(3, 85))
        unmatched = k in (3, 11, 19)
        var = float(r.randint(2, 15) * 1000) if unmatched else 0.0
        ics.append({
            "item_id": f"ICI-{k + 1:06d}", "entity_from_id": frm, "entity_to_id": to, "transaction_amount_gbp": amount,
            "transaction_currency": ccy, "transaction_date": tx, "posting_date": tx + timedelta(days=r.randint(0, 3)),
            "invoice_no": f"INV-{r.randint(700000, 799999)}", "match_status": "unmatched" if unmatched else "matched",
            "variance_gbp": var, "variance_reason": r.choice(IC_REASONS) if unmatched else None, "created_at": tx,
        })

    return {
        "entities": entities, "close_tasks": tasks, "financial_kpis": kpis, "guidance_and_outlook": guidance,
        "inventory_supply_chain_kpis": sc, "monthly_performance": monthly, "intercompany_items": ics,
        "close_task_reminders": [],
    }
