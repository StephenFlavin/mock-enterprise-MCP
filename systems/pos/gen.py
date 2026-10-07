"""Generate POS transaction data, exceptions and self-checkout rules."""
from datetime import datetime, timedelta, time
import random


def generate(g):
    """Generate sales transactions, POS exceptions and self-checkout rules."""
    r = g.rng

    # Get reference data
    stores = [s for s in g.master("sites") if s["type"] == "store"][:100]  # Limit to 100 stores
    products = g.master("products")[:300]  # Sample products
    employees = [e for e in g.master("employees") if e["site_id"] in [st["site_id"] for st in stores]]

    sales_txns = []
    exceptions = []
    rules = []

    # Generate sales transactions (hourly grain for last 8 weeks, sample stores)
    txn_id = 1
    sample_stores = r.sample(stores, min(len(stores), 30))  # Only 30 stores

    for day_offset in range(-56, 0):  # Last 8 weeks
        day = g.as_of + timedelta(days=day_offset)

        for store in sample_stores:
            # 2-3 transaction batches per store per day
            for _ in range(r.randint(2, 3)):
                hour = r.randint(8, 20)
                txn_time = datetime.combine(day, time(hour, r.randint(0, 59)))

                # 1-2 items per transaction
                for _ in range(r.randint(1, 2)):
                    product = r.choice(products)
                    qty = r.randint(1, 2)
                    retail_price = float(product["retail_price_gbp"] or 50)
                    unit_cost = float(product["unit_cost_gbp"] or 20)

                    # Slight discounting (5-10% off)
                    discount = retail_price * r.uniform(0.95, 1.0)
                    revenue = qty * discount
                    margin = qty * (discount - unit_cost)

                    # Availability tends toward high
                    avail = int(r.choice([100] * 70 + [95] * 20 + [80] * 7 + [50] * 2 + [30] * 1))

                    sizes = ["XS", "S", "M", "L", "XL", "XXL", "One Size", ""]

                    sales_txns.append({
                        "transaction_id": f"TXN-{txn_id:06d}",
                        "store_id": store["site_id"],
                        "sku": product["sku"],
                        "quantity": qty,
                        "revenue_gbp": round(revenue, 2),
                        "margin_gbp": round(margin, 2),
                        "transaction_time": txn_time,
                        "availability_pct": avail,
                        "size": r.choice(sizes),
                        "channel": r.choices(["store", "self_checkout"], [85, 15])[0],
                    })
                    txn_id += 1

    # Generate POS exceptions (voids, refunds, discounts, scan errors)
    exc_id = 1
    for day_offset in range(-42, 0):  # Last 6 weeks
        day = g.as_of + timedelta(days=day_offset)

        for store in sample_stores[:20]:  # Only 20 stores with exceptions
            store_emps = [e for e in employees if e["site_id"] == store["site_id"]]
            if not store_emps:
                store_emps = employees[:5]

            # 1-3 exceptions per store per day
            for _ in range(r.randint(1, 3)):
                hour = r.randint(8, 20)
                exc_time = datetime.combine(day, time(hour, r.randint(0, 59)))

                exc_type = r.choices(
                    ["void", "refund", "discount", "scan_exception"],
                    [25, 35, 30, 10]
                )[0]

                amount = round(r.uniform(5, 150), 2)
                till = f"T{r.randint(1, 20):02d}"
                emp = r.choice(store_emps)

                product = r.choice(products)
                reason_map = {
                    "void": ["wrong till", "duplicate", "customer request", "operator error"],
                    "refund": ["damaged", "wrong item", "customer satisfaction", "fit issue"],
                    "discount": ["price match", "loyalty", "floor burn", "promotion"],
                    "scan_exception": ["unexpected item", "weight mismatch", "age verification"],
                }
                reason = r.choice(reason_map.get(exc_type, ["other"]))

                exceptions.append({
                    "exception_id": f"EXC-{exc_id:06d}",
                    "store_id": store["site_id"],
                    "till_id": till,
                    "employee_id": emp["employee_id"],
                    "exception_type": exc_type,
                    "sku": product["sku"] if r.random() > 0.3 else "",
                    "amount_gbp": amount,
                    "quantity": r.randint(1, 5) if exc_type != "discount" else 0,
                    "reason": reason,
                    "exception_time": exc_time,
                    "region": store.get("region", "UK North"),
                })
                exc_id += 1

    # Generate self-checkout rules (chain-wide and store-level)
    rule_id = 1
    rule_types = ["weight_tolerance", "unexpected_item", "age_verification"]

    # Chain-wide rules
    for rule_type in rule_types:
        threshold = 0.5 if rule_type == "weight_tolerance" else 0.1 if rule_type == "unexpected_item" else 1.0
        rules.append({
            "rule_id": f"SCR-{rule_id:06d}",
            "store_id": "",  # Chain-wide
            "rule_name": f"Chain-wide {rule_type}",
            "rule_type": rule_type,
            "threshold_value": threshold,
            "threshold_unit": "kg" if rule_type == "weight_tolerance" else "percent",
            "status": "active",
            "scan_exception_rate_pct": round(r.uniform(0.5, 3.0), 2),
            "updated_at": datetime.combine(g.as_of - timedelta(days=r.randint(1, 30)), time(9, 0)),
        })
        rule_id += 1

    # Store-level rules
    for store in sample_stores[:40]:  # 40 stores with rules
        for rule_type in rule_types:
            if r.random() < 0.6:  # 60% chance of store-specific rule
                threshold = r.uniform(0.3, 0.8) if rule_type == "weight_tolerance" else r.uniform(0.05, 0.2)
                status = r.choices(["active", "paused", "archived"], [70, 20, 10])[0]
                rules.append({
                    "rule_id": f"SCR-{rule_id:06d}",
                    "store_id": store["site_id"],
                    "rule_name": f"{store['name']} {rule_type}",
                    "rule_type": rule_type,
                    "threshold_value": threshold,
                    "threshold_unit": "kg" if rule_type == "weight_tolerance" else "percent",
                    "status": status,
                    "scan_exception_rate_pct": round(r.uniform(0.3, 5.0), 2),
                    "updated_at": datetime.combine(g.as_of - timedelta(days=r.randint(1, 60)), time(9, 0)),
                })
                rule_id += 1

    return {
        "sales_transactions": sales_txns,
        "pos_exceptions": exceptions,
        "self_checkout_rules": rules,
    }
