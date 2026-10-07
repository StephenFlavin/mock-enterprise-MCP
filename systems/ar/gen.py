"""AR system: customer invoices, payments, credit accounts and collection patterns."""
from datetime import datetime, timedelta
import random


def generate(g):
    r = g.rng

    # Get master customers and orders
    master_customers = g.master("customers")
    master_orders = g.master("orders")

    # Generate customer accounts (one per customer)
    customer_accounts = []
    customer_stats = {}  # Track payment behavior by customer

    for cust in master_customers[:80]:  # Use first 80 customers
        cid = cust["customer_id"]
        credit_score = r.randint(45, 95)
        risk_rating = "critical" if credit_score < 50 else "high" if credit_score < 65 else "medium" if credit_score < 80 else "low"
        terms_days = r.choice([30, 45, 60])

        customer_accounts.append({
            "customer_id": cid,
            "credit_limit_gbp": r.choice([25000, 50000, 100000, 150000, 250000, 500000]),
            "credit_held": False,
            "credit_hold_reason": "",
            "current_balance_gbp": 0,  # Will update as we create invoices
            "payment_terms_days": terms_days,
            "credit_score": credit_score,
            "account_status": "active",
            "risk_rating": risk_rating,
            "average_dpo_days": terms_days + r.randint(-5, 15),  # Days to pay varies by customer
            "updated_at": g.as_of
        })
        customer_stats[cid] = {
            "dpo": terms_days + r.randint(-5, 15),
            "on_time_pct": 100 - r.randint(0, 40) if credit_score > 70 else 100 - r.randint(20, 60),
            "invoices_created": 0
        }

    # Generate invoices from orders
    invoices = []
    invoice_lines = []
    for order in master_orders:
        oid = order["order_id"]
        cid = order["customer_id"]

        # Only create invoices for orders from our generated customers
        if cid not in customer_stats:
            continue

        # Map order to invoice
        order_date = datetime.fromisoformat(order["order_date"])

        # Invoices typically 3-7 days after order
        inv_date = order_date + timedelta(days=r.randint(3, 7))

        # Due date based on customer terms
        terms = customer_stats[cid]["dpo"]
        due_date = inv_date + timedelta(days=terms)

        # Skip future invoices
        if inv_date.date() > g.as_of:
            continue

        inv_id = f"INV-2026-{len(invoices) + 1:06d}"
        amount = order["value_gbp"]

        # Determine payment status
        days_since_due = (g.as_of - due_date.date()).days

        if days_since_due < 0:  # Not yet due
            status = "open"
            paid = 0
        elif r.random() < customer_stats[cid]["on_time_pct"] / 100.0:  # Paid on time or early
            status = "paid"
            paid = amount
        elif days_since_due < 5:  # Borderline
            status = "open" if r.random() < 0.3 else "part_paid"
            paid = amount * r.uniform(0, 0.5) if status == "part_paid" else 0
        else:  # Overdue
            status = "overdue" if r.random() < 0.7 else "part_paid"
            paid = amount * r.uniform(0, 0.3) if status == "part_paid" else 0

        # Dispute some invoices
        dispute_status = "none"
        dispute_reason = ""
        if r.random() < 0.02:  # 2% disputed
            dispute_status = "disputed"
            dispute_reason = r.choice(["Pricing discrepancy", "Wrong delivery", "Quality issue", "Quantity mismatch"])

        invoices.append({
            "invoice_id": inv_id,
            "customer_id": cid,
            "order_id": oid,
            "invoice_date": inv_date.date(),
            "due_date": due_date.date(),
            "amount_gbp": round(amount, 2),
            "paid_amount_gbp": round(paid, 2),
            "status": status,
            "dispute_status": dispute_status,
            "dispute_reason": dispute_reason,
            "created_at": inv_date,
            "updated_at": g.as_of
        })

        customer_stats[cid]["invoices_created"] += 1

        # Generate invoice lines from order
        line_no = 1
        # Simple: one line per invoice (details would come from order)
        invoice_lines.append({
            "invoice_id": inv_id,
            "line_no": line_no,
            "sku": "SKU-INVOICE-001",  # Placeholder
            "description": f"Order {oid}",
            "qty": 1,
            "unit_price_gbp": amount,
            "line_total_gbp": amount
        })

    # Generate payment records
    payments = []
    for inv in invoices:
        if inv["status"] in ("paid", "part_paid"):
            # Create a payment record
            pay_id = f"PAY-2026-{len(payments) + 1:06d}"
            payment_date = inv["due_date"] + timedelta(days=r.randint(0, 10))

            payments.append({
                "payment_id": pay_id,
                "customer_id": inv["customer_id"],
                "invoice_id": inv["invoice_id"],
                "amount_gbp": round(inv["paid_amount_gbp"], 2),
                "payment_date": payment_date,
                "received_date": payment_date + timedelta(days=1),
                "payment_method": r.choice(["bank_transfer", "cheque", "direct_debit"]),
                "reference": g.fake.bothify(text="BACS-########"),
                "notes": ""
            })

    # Generate collection history (weekly/monthly patterns)
    collection_history = []
    for cid, stats in customer_stats.items():
        # Generate last 52 weeks of collection data
        for weeks_back in range(0, 52, 4):  # Every 4 weeks
            recorded_on = g.as_of - timedelta(weeks=weeks_back)

            # Simulate customer invoices in that period
            period_invoices = r.randint(2, 8)
            period_amount = period_invoices * r.uniform(5000, 50000)
            period_paid = period_amount * (stats["on_time_pct"] / 100.0) * r.uniform(0.8, 1.1)

            collection_history.append({
                "customer_id": cid,
                "recorded_on": recorded_on.date(),
                "invoices_in_period": period_invoices,
                "amount_invoiced_gbp": round(period_amount, 2),
                "amount_paid_gbp": round(period_paid, 2),
                "days_to_pay_avg": stats["dpo"],
                "on_time_pct": stats["on_time_pct"],
                "notes": ""
            })

    # Generate credit insurance policies
    credit_insurance = []
    for i, cust in enumerate(master_customers[:20]):  # First 20 customers may have insurance
        if r.random() < 0.3:  # 30% have insurance
            cid = cust["customer_id"]
            policy_id = f"INS-{len(credit_insurance) + 1:05d}"

            credit_insurance.append({
                "policy_id": policy_id,
                "customer_id": cid,
                "insurer": r.choice(["Atradius", "Coface", "AXA Credit Insurance", "Zurich"]),
                "cover_limit_gbp": r.choice([50000, 100000, 200000, 500000]),
                "cover_percentage_pct": r.choice([80, 90, 95]),
                "policy_start": (g.as_of - timedelta(days=r.randint(60, 365))).date(),
                "policy_end": (g.as_of + timedelta(days=r.randint(60, 365))).date(),
                "status": "active",
                "updated_at": g.as_of
            })

    # Generate bad debt provision (single current provision record)
    bad_debt_provisions = []

    # Calculate ECL by aging bucket
    ecl_0_30 = sum(max(0, (inv["amount_gbp"] - inv["paid_amount_gbp"]) * 0.02)
                   for inv in invoices if 0 <= (g.as_of - inv["due_date"]).days <= 30)
    ecl_31_60 = sum(max(0, (inv["amount_gbp"] - inv["paid_amount_gbp"]) * 0.05)
                    for inv in invoices if 30 < (g.as_of - inv["due_date"]).days <= 60)
    ecl_61_90 = sum(max(0, (inv["amount_gbp"] - inv["paid_amount_gbp"]) * 0.15)
                    for inv in invoices if 60 < (g.as_of - inv["due_date"]).days <= 90)
    ecl_over_90 = sum(max(0, (inv["amount_gbp"] - inv["paid_amount_gbp"]) * 0.35)
                      for inv in invoices if (g.as_of - inv["due_date"]).days > 90)

    total_ecl = ecl_0_30 + ecl_31_60 + ecl_61_90 + ecl_over_90

    bad_debt_provisions.append({
        "provision_id": "BDP-2026-00001",
        "as_of_date": g.as_of,
        "methodology": "ECL by ageing bucket: 0-30d=2%, 31-60d=5%, 61-90d=15%, 90+=35%",
        "amount_gbp": round(total_ecl, 2),
        "by_0_30_days_gbp": round(ecl_0_30, 2),
        "by_31_60_days_gbp": round(ecl_31_60, 2),
        "by_61_90_days_gbp": round(ecl_61_90, 2),
        "by_over_90_days_gbp": round(ecl_over_90, 2),
        "created_at": g.as_of
    })

    # Generate payment reminders (outbox)
    payment_reminders = []
    # Would be populated by send_payment_reminder tool calls

    # Update customer current balances
    for acc in customer_accounts:
        cid = acc["customer_id"]
        balance = sum(max(0, inv["amount_gbp"] - inv["paid_amount_gbp"])
                     for inv in invoices if inv["customer_id"] == cid and inv["status"] in ("open", "overdue", "part_paid"))
        acc["current_balance_gbp"] = round(balance, 2)

    return {
        "customer_accounts": customer_accounts,
        "invoices": invoices,
        "invoice_lines": invoice_lines,
        "payments": payments,
        "collection_history": collection_history,
        "credit_insurance": credit_insurance,
        "bad_debt_provisions": bad_debt_provisions,
        "payment_reminders": payment_reminders
    }
