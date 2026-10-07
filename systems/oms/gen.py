"""Order Management System: orders, allocations, and shipments for all channels."""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng

    # Get master data
    products = g.master("products")
    customers = g.master("customers")
    orders_master = g.master("orders")
    sites = g.master("sites")

    # Generate base tables
    orders = []
    order_lines = []
    allocation_decisions = []
    shipments = []
    shipment_lines = []
    batch_sales = []
    allocation_rules = []

    # Create default allocation rules
    rule_id = 1
    for channel in ["store", "online", "wholesale"]:
        for product in r.sample(products, min(5, len(products))):
            # Pick a random customer or use first one
            cust = r.choice(customers)
            allocation_rules.append({
                "rule_id": f"AR-{rule_id:06d}",
                "product_sku": product["sku"],
                "channel": channel,
                "customer_id": cust["customer_id"],
                "store_pct": 40 if channel == "store" else 30 if channel == "online" else 30,
                "online_pct": 35 if channel == "online" else 30 if channel == "store" else 35,
                "wholesale_pct": 25 if channel == "wholesale" else 40 if channel == "online" else 35,
                "description": f"Default allocation for {product['sku']} in {channel}",
                "status": "active",
                "updated_at": g.as_of
            })
            rule_id += 1

    # Generate orders from master orders (recent 60 days)
    order_id = 1
    shipment_id = 1
    batch_id = 1
    decision_id = 1

    for master_order in orders_master[:100]:  # Sample of orders
        order_date = datetime.fromisoformat(master_order["order_date"])
        days_from_now = (order_date.date() - g.as_of).days

        if not -60 <= days_from_now <= 14:
            continue

        # Determine channel and customer
        channel = r.choice(["store", "online", "wholesale"])
        cust_sample = r.sample(customers, 1)[0]

        oid = f"ORD-{order_id:06d}"
        order_id += 1

        # Determine status based on date
        if days_from_now < -30:
            status = r.choice(["shipped", "delivered", "cancelled"])
        elif days_from_now < 0:
            status = r.choice(["allocated", "picked", "shipped"])
        else:
            status = r.choice(["open", "allocated"])

        hold_status = "none"
        hold_reason = ""
        if status == "open" and r.random() < 0.05:
            hold_status = "credit"
            hold_reason = "Credit limit exceeded"

        priority = "normal"
        if r.random() < 0.1:
            priority = r.choice(["low", "high", "urgent"])

        total_units = r.randint(10, 200)
        total_gbp = round(total_units * r.uniform(10, 500), 2)

        ot = order_date + timedelta(hours=r.randint(0, 23), minutes=r.randint(0, 59))

        orders.append({
            "order_id": oid,
            "customer_id": cust_sample["customer_id"],
            "channel": channel,
            "status": status,
            "order_date": order_date.date(),
            "order_time": ot,
            "hold_status": hold_status,
            "hold_reason": hold_reason,
            "priority": priority,
            "total_units": total_units,
            "total_gbp": total_gbp,
            "created_at": ot,
            "updated_at": ot + timedelta(minutes=r.randint(0, 1440))
        })

        # Add order lines
        num_lines = r.randint(1, 4)
        product_sample = r.sample(products, min(num_lines, len(products)))

        for line_no, product in enumerate(product_sample, 1):
            qty_ordered = r.randint(5, 100)
            qty_allocated = qty_ordered if status != "open" else r.randint(int(qty_ordered * 0.5), qty_ordered)
            qty_shipped = qty_allocated if status in ["shipped", "delivered"] else 0

            order_lines.append({
                "order_id": oid,
                "line_no": line_no,
                "sku": product["sku"],
                "qty_ordered": qty_ordered,
                "qty_allocated": qty_allocated,
                "qty_shipped": qty_shipped,
                "unit_price_gbp": round(float(product["retail_price_gbp"]) * 0.6, 2),
                "allocation_source": r.choice(["DC1", "DC2", "DC3"]) if status != "open" else "",
                "batch_id": f"BAT-{batch_id:06d}" if status != "open" else "",
                "status": "shipped" if status in ["shipped", "delivered"] else status
            })
            batch_id += 1

        # Add allocation decisions for allocated/shipped orders
        if status in ["allocated", "picked", "shipped", "delivered"]:
            for line_no, product in enumerate(product_sample, 1):
                ol = order_lines[len(order_lines) - num_lines + line_no - 1]
                decision_id_str = f"AD-{decision_id:06d}"
                decision_id += 1

                allocation_decisions.append({
                    "decision_id": decision_id_str,
                    "order_id": oid,
                    "line_no": line_no,
                    "sku": product["sku"],
                    "qty_requested": ol["qty_ordered"],
                    "qty_allocated": ol["qty_allocated"],
                    "source_dc": ol["allocation_source"],
                    "source_location": f"{ol['allocation_source']}-{r.choice(['A', 'B', 'C', 'D'])}-{r.randint(1, 20):02d}-{r.randint(1, 4)}",
                    "batch_id": ol["batch_id"],
                    "rule_id": f"AR-{r.randint(1, min(rule_id - 1, 100)):06d}",
                    "oversold": r.random() < 0.05,
                    "decided_at": ot + timedelta(minutes=r.randint(10, 120))
                })

        # Add shipments for delivered/shipped orders
        if status in ["shipped", "delivered"]:
            # Determine if split
            is_split = r.random() < 0.2
            split_reason = "none"
            if is_split:
                split_reason = r.choice(["stock", "location", "wave"])

            ship_count = 2 if is_split else 1
            for ship_num in range(ship_count):
                sid = f"SHP-{shipment_id:06d}"
                shipment_id += 1

                ship_date = order_date + timedelta(days=r.randint(1, 7))
                ship_time = datetime.combine(ship_date.date(), datetime.min.time()) + timedelta(hours=r.randint(6, 18))
                deliver_date = ship_date + timedelta(days=r.randint(1, 5)) if status == "delivered" else None

                shipments.append({
                    "shipment_id": sid,
                    "order_id": oid,
                    "channel": channel,
                    "customer_id": cust_sample["customer_id"],
                    "delivery_notes": f"DN-{ship_num:03d}",
                    "shipped_date": ship_date.date(),
                    "shipped_at": ship_time,
                    "delivered_date": deliver_date,
                    "total_units": total_units // ship_count if is_split else total_units,
                    "is_split": is_split,
                    "split_reason": split_reason,
                    "status": "delivered" if status == "delivered" else "shipped"
                })

                # Add shipment lines
                for line_no, product in enumerate(product_sample, 1):
                    ol = order_lines[len(order_lines) - num_lines + line_no - 1]
                    qty_in_shipment = ol["qty_shipped"] // ship_count if is_split else ol["qty_shipped"]

                    shipment_lines.append({
                        "shipment_id": sid,
                        "line_no": line_no,
                        "order_line_no": line_no,
                        "sku": product["sku"],
                        "qty_shipped": qty_in_shipment,
                        "batch_id": ol["batch_id"],
                        "country": "GB" if channel == "store" else r.choice(["GB", "IE", "DE", "FR", "NL"])
                    })

                    # Add to batch_sales
                    bs_key = (ol["batch_id"], product["sku"], channel, shipment_lines[-1]["country"])
                    batch_sales.append({
                        "batch_id": ol["batch_id"],
                        "sku": product["sku"],
                        "channel": channel,
                        "country": shipment_lines[-1]["country"],
                        "units_sold": qty_in_shipment,
                        "shipped_date": ship_date.date()
                    })

    return {
        "orders": orders,
        "order_lines": order_lines,
        "allocation_rules": allocation_rules,
        "allocation_decisions": allocation_decisions,
        "shipments": shipments,
        "shipment_lines": shipment_lines,
        "batch_sales": batch_sales
    }
