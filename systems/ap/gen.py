"""Accounts Payable data: vendors, invoices, payments, rebates, payment runs."""
from datetime import datetime, timedelta


def generate(g):
    """Generate AP data referencing master suppliers and POs."""
    r = g.rng

    vendors = []
    bank_detail_changes = []
    invoices = []
    invoice_lines = []
    rebate_agreements = []
    rebate_accruals = []
    payment_runs = []
    supplier_payments = []
    goods_receipt_invoice_variance = []
    air_freight_invoices = []

    # Create vendor master from suppliers
    suppliers = g.master("suppliers")
    pos = g.master("purchase_orders")
    carriers = [c for c in g.master("carriers") if c["mode"] in ["air", "forwarder"]]

    vendor_id = 1
    vendor_by_supplier = {}

    for supplier in suppliers[:50]:  # First 50 suppliers
        vendor_id_str = f"VND-{vendor_id:06d}"
        fraud_score = r.randint(5, 75)
        fraud_indicators = []

        if fraud_score > 50:
            fraud_indicators.append(r.choice([
                "new_vendor",
                "country_mismatch",
                "bank_country_mismatch",
                "high_invoice_frequency",
                "unusual_payment_terms",
                "duplicate_name_similarity"
            ]))

        vendor = {
            "vendor_id": vendor_id_str,
            "supplier_id": supplier["supplier_id"],
            "name": supplier["name"],
            "country": supplier["country"],
            "bank_country": supplier["country"] if r.random() < 0.9 else r.choice(["NL", "IE", "DE", "US"]),
            "tax_id": f"TAX-{r.randint(100000, 999999)}",
            "payment_terms_days": supplier.get("payment_terms_days", 30),
            "on_payment_hold": r.choice([False, False, False, True]),  # 25% on hold
            "hold_reason": r.choice(["fraud_investigation", "payment_dispute", "audit_hold", None]) if r.choice([False, False, False, True]) else None,
            "fraud_risk_score": fraud_score,
            "fraud_indicators": fraud_indicators,
            "control_approvals_required": 1 if fraud_score < 30 else 2 if fraud_score < 60 else 3,
            "updated_at": g.date_between(90, 0)
        }
        vendors.append(vendor)
        vendor_by_supplier[supplier["supplier_id"]] = vendor_id_str
        vendor_id += 1

    # Generate bank detail changes
    change_id = 1
    for vendor in vendors[:10]:  # 10% of vendors had bank changes
        change = {
            "change_id": f"BDC-{change_id:06d}",
            "vendor_id": vendor["vendor_id"],
            "old_bank_account": f"GB{r.randint(10, 99)}{r.randint(100000, 999999)}",
            "new_bank_account": f"GB{r.randint(10, 99)}{r.randint(100000, 999999)}",
            "old_bank_country": vendor["country"],
            "new_bank_country": r.choice([vendor["country"], "NL", "DE", "IE"]),
            "requested_date": g.date_between(180, 0),
            "requested_by": r.choice([e["employee_id"] for e in g.master("employees")]),
            "approval_status": r.choices(["approved", "pending"], [80, 20])[0],
            "approvals_count": r.randint(1, 3),
            "first_payment_date": g.date_between(30, 0) if r.random() < 0.7 else None,
            "updated_at": g.date_between(60, 0)
        }
        bank_detail_changes.append(change)
        change_id += 1

    # Generate invoices and invoice lines
    invoice_id = 1
    line_payment_runs = {}  # Track which payment run each invoice is in

    # 1. Supplier invoices (linked to POs)
    for po in pos[:40]:  # Create invoices for first 40 POs
        if po["supplier_id"] not in vendor_by_supplier:
            continue

        vendor_id_str = vendor_by_supplier[po["supplier_id"]]
        inv_date = g.date_between(90, 0)
        inv = {
            "invoice_id": f"INV-{invoice_id:06d}",
            "vendor_id": vendor_id_str,
            "supplier_id": po["supplier_id"],
            "invoice_type": "supplier",
            "invoice_number": f"SUP-{r.randint(1000, 9999)}",
            "invoice_date": inv_date,
            "received_date": inv_date + timedelta(days=r.randint(0, 5)),
            "amount_gbp": float(po["total_value"]) * r.uniform(0.95, 1.05),
            "po_id": po["po_id"],
            "three_way_match_status": r.choices(["matched", "variance"], [85, 15])[0],
            "gl_account": "5000",
            "cost_centre_id": r.choice([c["cost_centre_id"] for c in g.master("cost_centres")]),
            "accrued": True,
            "accrual_date": inv_date + timedelta(days=2),
            "payment_status": r.choices(["paid", "scheduled"], [70, 30])[0],
            "payment_run_id": None,
            "scheduled_payment_date": inv_date + timedelta(days=30) if r.random() < 0.3 else None,
            "actual_payment_date": inv_date + timedelta(days=r.randint(20, 60)) if r.random() < 0.7 else None,
            "dispute_reason": None,
            "created_date": inv_date,
            "updated_at": inv_date + timedelta(days=1)
        }
        invoices.append(inv)

        # Add invoice lines
        line_no = 1
        num_lines = r.randint(1, 4)
        for _ in range(num_lines):
            line = {
                "invoice_id": inv["invoice_id"],
                "line_no": line_no,
                "description": f"Goods per PO {po['po_id']}",
                "quantity": r.randint(10, 500),
                "unit_price_gbp": r.uniform(1, 100),
                "line_total_gbp": r.uniform(100, 5000),
                "charge_type": "goods",
                "contracted_rate_gbp": None,
                "variance_gbp": 0,
                "variance_pct": 0,
                "disputable": False
            }
            invoice_lines.append(line)
            line_no += 1

        invoice_id += 1

    # 2. Carrier invoices with rate variances
    for carrier in carriers[:5]:
        for _ in range(r.randint(2, 5)):
            inv_date = g.date_between(180, 0)
            line_count = r.randint(2, 8)

            inv = {
                "invoice_id": f"INV-{invoice_id:06d}",
                "vendor_id": vendor_by_supplier.get(carrier["carrier_id"], f"VND-{r.randint(1, 100):06d}"),
                "supplier_id": carrier["carrier_id"],
                "invoice_type": "carrier",
                "invoice_number": f"CAR-{r.randint(10000, 99999)}",
                "invoice_date": inv_date,
                "received_date": inv_date + timedelta(days=r.randint(0, 3)),
                "amount_gbp": r.uniform(500, 5000) * line_count,
                "po_id": None,
                "three_way_match_status": "pending",
                "gl_account": "5102",
                "cost_centre_id": r.choice([c["cost_centre_id"] for c in g.master("cost_centres")] if g.master("cost_centres") else ["CC-2201"]),
                "accrued": r.choice([True, True, False]),
                "accrual_date": inv_date + timedelta(days=3) if r.random() < 0.8 else None,
                "payment_status": r.choices(["open", "scheduled", "paid", "disputed"], [30, 20, 40, 10])[0],
                "payment_run_id": None,
                "scheduled_payment_date": inv_date + timedelta(days=14) if r.random() < 0.3 else None,
                "actual_payment_date": inv_date + timedelta(days=r.randint(5, 45)) if r.random() < 0.5 else None,
                "dispute_reason": "Rate variance" if r.random() < 0.15 else None,
                "created_date": inv_date,
                "updated_at": inv_date + timedelta(days=1)
            }
            invoices.append(inv)

            # Add carrier invoice lines with variances
            for line_no in range(1, line_count + 1):
                variance = r.uniform(-200, 300) if r.random() < 0.4 else 0
                line = {
                    "invoice_id": inv["invoice_id"],
                    "line_no": line_no,
                    "description": r.choice(["Standard freight", "Accessorial charge", "Fuel surcharge", "Weight variance", "Service fee"]),
                    "quantity": r.randint(1, 10),
                    "unit_price_gbp": r.uniform(50, 300),
                    "line_total_gbp": r.uniform(100, 1000),
                    "charge_type": r.choice(["freight", "surcharge", "accessorial", "weight_variance"]),
                    "contracted_rate_gbp": r.uniform(100, 1000),
                    "variance_gbp": variance,
                    "variance_pct": (variance / r.uniform(500, 2000) * 100) if variance != 0 else 0,
                    "disputable": variance > 50
                }
                invoice_lines.append(line)

            invoice_id += 1

    # 3. Air freight invoices
    air_inv_id = 1
    for _ in range(15):
        inv_date = g.date_between(120, 0)
        total_amount = r.uniform(5000, 50000)

        air_inv = {
            "invoice_id": f"FRT-{air_inv_id:06d}",
            "supplier_id": r.choice([c["carrier_id"] for c in carriers]),
            "invoice_date": inv_date,
            "amount_gbp": total_amount,
            "shipment_count": r.randint(1, 5),
            "air_reason": r.choices(
                ["demand_spike", "store_emergency", "supplier_late", "quality_issue", "cancelled_order"],
                [20, 25, 20, 20, 15]
            )[0],
            "avoidable": r.choice([True, True, False]),
            "avoidable_pct": r.randint(30, 100) if r.random() < 0.6 else 0,
            "chargeability": r.choices(["chargeable_to_supplier", "no_chargeable_position"], [60, 40])[0],
            "contract_rate_gbp": total_amount * 0.85 if r.random() < 0.7 else None,
            "overcharge_gbp": max(0, total_amount - (total_amount * 0.85)) if r.random() < 0.7 else 0,
            "status": r.choices(["open", "chargeable_drafted", "chargeback_sent"], [40, 35, 25])[0],
            "created_date": inv_date
        }
        air_freight_invoices.append(air_inv)
        air_inv_id += 1

    # Generate rebate agreements
    rebate_id = 1
    for supplier in suppliers[:15]:
        if r.random() < 0.7:
            agreement = {
                "agreement_id": f"RBA-{rebate_id:06d}",
                "supplier_id": supplier["supplier_id"],
                "rebate_type": r.choice(["volume", "cost_reduction", "quality_bonus"]),
                "threshold_amount_gbp": r.uniform(50000, 500000),
                "rebate_pct": r.uniform(0.5, 5),
                "rebate_amount_gbp": r.uniform(5000, 50000) if r.random() < 0.3 else 0,
                "effective_from": g.date_between(365, 0),
                "effective_to": g.date_between(0, 365),
                "status": r.choices(["active", "expired"], [80, 20])[0],
                "created_date": g.date_between(180, 0)
            }
            rebate_agreements.append(agreement)
            rebate_id += 1

            # Generate rebate accruals for active agreements
            if agreement["status"] == "active":
                for period in range(4):
                    accrual_period = f"FY2026-Q{period + 1}"
                    ytd_spend = r.uniform(100000, 1000000)
                    accrued = max(0, (ytd_spend - agreement["threshold_amount_gbp"]) * agreement["rebate_pct"] / 100) if ytd_spend > agreement["threshold_amount_gbp"] else 0

                    accrual = {
                        "accrual_id": f"ACR-{len(rebate_accruals) + 1:06d}",
                        "agreement_id": agreement["agreement_id"],
                        "supplier_id": supplier["supplier_id"],
                        "accrual_period": accrual_period,
                        "ytd_spend_gbp": ytd_spend,
                        "accrued_amount_gbp": accrued,
                        "settled_amount_gbp": accrued if r.random() < 0.5 else 0,
                        "accrual_date": g.date_between(90, 0),
                        "settlement_date": g.date_between(45, 0) if r.random() < 0.5 else None,
                        "status": r.choice(["accrued", "settled"])
                    }
                    rebate_accruals.append(accrual)

    # Generate payment runs
    run_id = 1
    for _ in range(8):
        run_date = g.date_between(60, 0)
        run_invoices = r.randint(5, 20)

        run = {
            "payment_run_id": f"RUN-{run_id:06d}",
            "run_date": run_date,
            "run_type": r.choices(["regular", "ad_hoc"], [80, 20])[0],
            "invoices_count": run_invoices,
            "total_amount_gbp": r.uniform(50000, 500000),
            "status": r.choices(["completed", "scheduled", "draft"], [60, 30, 10])[0],
            "created_date": run_date - timedelta(days=r.randint(1, 5)),
            "created_by": r.choice([e["employee_id"] for e in g.master("employees")]),
            "updated_at": run_date
        }
        payment_runs.append(run)
        run_id += 1

    # Generate supplier payments
    payment_id = 1
    for invoice in invoices[:40]:
        if invoice["actual_payment_date"]:
            payment = {
                "payment_id": f"PAY-{payment_id:06d}",
                "supplier_id": invoice["supplier_id"],
                "vendor_id": invoice["vendor_id"],
                "invoice_id": invoice["invoice_id"],
                "amount_gbp": invoice["amount_gbp"],
                "payment_date": invoice["actual_payment_date"],
                "payment_run_id": r.choice([run["payment_run_id"] for run in payment_runs]) if payment_runs else None,
                "days_to_pay": (invoice["actual_payment_date"] - invoice["invoice_date"]).days,
                "bank_account": f"GB{r.randint(10, 99)}{r.randint(100000, 999999)}"
            }
            supplier_payments.append(payment)
            payment_id += 1

    # Generate goods receipt vs invoice variances
    variance_id = 1
    for po in pos[:15]:
        if r.random() < 0.3:
            variance = {
                "variance_id": f"VAR-{variance_id:06d}",
                "po_id": po["po_id"],
                "invoice_id": f"INV-{r.randint(1, 40):06d}",
                "grn_quantity": r.randint(100, 1000),
                "invoice_quantity": r.randint(100, 1000),
                "quantity_variance": r.randint(-50, 50),
                "grn_amount_gbp": r.uniform(1000, 10000),
                "invoice_amount_gbp": r.uniform(1000, 10000),
                "amount_variance_gbp": r.uniform(-500, 500),
                "variance_type": r.choice(["quantity", "price", "both"]),
                "status": r.choices(["pending", "investigated", "resolved"], [40, 35, 25])[0],
                "created_date": g.date_between(90, 0)
            }
            goods_receipt_invoice_variance.append(variance)
            variance_id += 1

    return {
        "vendors": vendors,
        "bank_detail_changes": bank_detail_changes,
        "invoices": invoices,
        "invoice_lines": invoice_lines,
        "rebate_agreements": rebate_agreements,
        "rebate_accruals": rebate_accruals,
        "payment_runs": payment_runs,
        "supplier_payments": supplier_payments,
        "goods_receipt_invoice_variance": goods_receipt_invoice_variance,
        "air_freight_invoices": air_freight_invoices
    }
