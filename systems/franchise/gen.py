"""Franchise orders, stock positions, performance data and holds."""
from datetime import datetime, timedelta
import random


def generate(g):
    r = g.rng
    fake = g.fake

    # Get franchise partners from master
    franchise_partners = [p for p in g.master("partners") if p["type"] == "franchise"]
    products = g.master("products")

    # Determine core range - top-selling SKUs by velocity
    core_range_skus = set()
    product_by_abc = {}
    for p in products:
        if p["abc_class"] == "A":
            core_range_skus.add(p["sku"])
        product_by_abc[p["sku"]] = p

    orders = []
    order_lines = []
    partner_stock = []
    partner_perf = []
    holds = []

    # Generate orders and stock for each franchise partner
    for partner in franchise_partners:
        partner_id = partner["partner_id"]

        # Generate 3-8 orders per partner
        num_orders = r.randint(3, 8)
        for o in range(num_orders):
            days_ago = r.randint(-14, 90)  # Mix of future and past orders
            order_date_val = g.as_of + timedelta(days=days_ago)
            # Convert to datetime for time operations
            order_date = datetime.combine(order_date_val, datetime.min.time())
            order_id = f"FRO-{len(orders) + 1:06d}"

            # Pick random SKUs
            selected_skus = r.sample(products, r.randint(5, 15))
            total_units = 0
            total_value = 0.0

            for line_no, prod in enumerate(selected_skus, 1):
                sku = prod["sku"]
                is_core = sku in core_range_skus
                qty = r.randint(20, 500)
                total_units += qty
                unit_cost = float(prod["unit_cost_gbp"]) if prod["unit_cost_gbp"] else 0.0
                total_value += qty * unit_cost

                received = 0 if days_ago > -7 else r.randint(0, qty)
                hold_status = "none"

                order_lines.append({
                    "order_id": order_id,
                    "line_no": line_no,
                    "sku": sku,
                    "qty_ordered": qty,
                    "qty_received": received,
                    "hold_status": hold_status,
                    "is_core_range": is_core
                })

            status = "open" if days_ago > -7 else r.choices(["open", "shipped", "received"], [20, 40, 40])[0]
            expected_arrival = order_date + timedelta(days=r.randint(10, 30))

            orders.append({
                "order_id": order_id,
                "partner_id": partner_id,
                "order_date": order_date.date() if isinstance(order_date, datetime) else order_date,
                "expected_arrival_date": expected_arrival.date() if isinstance(expected_arrival, datetime) else expected_arrival,
                "status": status,
                "hold_reason": None,
                "total_units": total_units,
                "total_value_gbp": round(total_value, 2),
                "updated_at": order_date + timedelta(days=r.randint(0, 3))
            })

        # Generate stock positions
        for prod in r.sample(products, min(40, len(products))):
            sku = prod["sku"]
            is_core = sku in core_range_skus

            # Core range should have more realistic stock
            if is_core:
                on_hand = r.randint(50, 300)
                target = r.randint(100, 200)
            else:
                on_hand = r.randint(10, 200)
                target = r.randint(30, 100)

            available = max(0, on_hand - r.randint(0, on_hand // 3))
            allocated = on_hand - available

            partner_stock.append({
                "partner_id": partner_id,
                "sku": sku,
                "on_hand": on_hand,
                "available": available,
                "allocated": allocated,
                "target_stock": target,
                "is_core_range": is_core,
                "last_stock_check": (g.as_of - timedelta(days=r.randint(1, 14))).isoformat()
            })

        # Generate performance for last 3 months
        for month_offset in range(3):
            period_end = g.as_of.replace(day=1) - timedelta(days=1)
            for _ in range(month_offset):
                period_end = period_end.replace(day=1) - timedelta(days=1)

            sales_units = r.randint(500, 3000)
            sales_gbp = sales_units * r.randint(15, 50)
            margin_pct = r.randint(25, 45)
            margin_gbp = round(sales_gbp * margin_pct / 100, 2)

            compliance = r.randint(70, 98)
            stockouts = r.randint(0, 3) if compliance < 80 else r.randint(0, 1)
            overstock_value = r.randint(5000, 75000) if compliance < 85 else r.randint(0, 35000)
            intervention = compliance < 75 or overstock_value > 60000

            partner_perf.append({
                "partner_id": partner_id,
                "period_end": period_end,
                "sales_units": sales_units,
                "sales_gbp": sales_gbp,
                "margin_gbp": margin_gbp,
                "margin_pct": margin_pct,
                "compliance_score": compliance,
                "stockout_incidents": stockouts,
                "overstock_value_gbp": overstock_value,
                "intervention_needed": intervention
            })

    return {
        "franchise_orders": orders,
        "franchise_order_lines": order_lines,
        "partner_stock": partner_stock,
        "partner_performance": partner_perf,
        "performance_notices": [],
        "order_holds": []
    }
