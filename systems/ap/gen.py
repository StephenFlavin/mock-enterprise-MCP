"""Accounts Payable data: vendors, invoices, payments, rebates, payment runs.

Deterministic stories (all dates are in data time and move to today at runtime):
  - air freight: ~GBP 420k in the last 90 days, mostly supplier-late and demand spikes
  - carrier CAR-002: 12 four-weekly invoices with disputable overcharges (surcharge, accessorial, weight, service level)
  - freight cost: GBP 208,822 invoiced but not accrued (CAR-001/002/006/008) plus four miscoded freight invoices
  - payment performance: SUP-0053 pays on time; SUP-0012 is paid late by us
  - facilities: SUP-0014 / SUP-0026 / SUP-0067 monthly invoices, SUP-0067 with three one-off project invoices
  - goods receipt vs invoice: SUP-0020 over-invoiced on five POs; SUP-0001 bank changed to India the day before the as-of date
  - vendor fraud: VND-000023 bank in HK, VND-000048 shared bank account + bank change before a payment, etc.
  - rebates: SUP-0001 / SUP-0015 / SUP-0008 volume agreements, SUP-0008 over-accrued last year
Everything else is light, clean background noise.
"""
import zlib
from datetime import date, timedelta

# supplier id -> overrides for the vendor master (score, indicators, bank country, tax id)
OVR = {
    "SUP-0001": dict(score=66, ind=["recent_bank_change", "bank_country_mismatch"], bank="IN"),
    "SUP-0023": dict(score=82, ind=["bank_country_mismatch", "unverified_bank_account"], bank="HK"),
    "SUP-0027": dict(score=55, ind=["unusual_payment_terms"]),
    "SUP-0034": dict(score=64, ind=["new_vendor", "duplicate_name_similarity"], tax="TAX-518430"),
    "SUP-0045": dict(score=52, ind=["high_invoice_frequency"]),
    "SUP-0048": dict(score=88, ind=["shared_bank_account", "recent_bank_change", "payment_after_bank_change"], bank="SG"),
    "SUP-0060": dict(score=76, ind=["new_vendor", "payment_within_days_of_creation", "po_box_address"]),
    "SUP-0062": dict(score=57, ind=["duplicate_name_similarity", "duplicate_tax_id"], tax="TAX-518430"),
    "SUP-0071": dict(score=71, ind=["round_sum_invoices", "recent_bank_change"], bank="NL"),
}
STORY_SUPPLIERS = {"SUP-0001", "SUP-0012", "SUP-0053", "SUP-0014", "SUP-0026", "SUP-0067", "SUP-0034", "SUP-0060",
                   "SUP-0048", "SUP-0071", "SUP-0023", "SUP-0008", "SUP-0015", "SUP-0003", "SUP-0021"}


def _acct(vendor_id, country="GB"):
    n = zlib.crc32(vendor_id.encode())
    return f"{country}{n % 90 + 10}{(n // 7) % 900000000 + 100000000}"


def generate(g):
    r = g.rng
    A = g.as_of
    D = g.days_ago
    suppliers = g.master("suppliers")
    carriers = g.master("carriers")
    pos = g.master("purchase_orders")
    employees = [e["employee_id"] for e in g.master("employees")]
    ccs = {c["cost_centre_id"] for c in g.master("cost_centres")}
    sup = {s["supplier_id"]: s for s in suppliers}
    iso = date.fromisoformat

    vendors, bank_changes, invoices, lines = [], [], [], []
    payments, runs, grn, air = [], [], [], []
    agreements, accruals = [], []

    # ------------------------------------------------------------------ vendors
    vid_of = {}
    for s in suppliers:
        sid = s["supplier_id"]
        vid = f"VND-{int(sid[4:]):06d}"
        vid_of[sid] = vid
        o = OVR.get(sid, {})
        score = o.get("score", r.randint(4, 38))
        hold, reason = False, None
        if s["status"] == "blocked":
            hold, reason = True, "supplier_blocked"
        elif s["status"] == "exited":
            hold, reason = True, "supplier_exited"
        created = iso(s["onboarded_date"])
        vendors.append({
            "vendor_id": vid, "supplier_id": sid, "carrier_id": None, "name": s["name"], "country": s["country"],
            "bank_country": o.get("bank", s["country"]), "tax_id": o.get("tax", f"TAX-{r.randint(100000, 999999)}"),
            "payment_terms_days": int(s["payment_terms_days"]), "on_payment_hold": hold, "hold_reason": reason,
            "hold_date": D(60) if hold else None, "fraud_risk_score": score, "fraud_indicators": o.get("ind", []),
            "control_approvals_required": 1 if score < 30 else 2 if score < 60 else 3,
            "created_date": created, "updated_at": g.date_between(120, 20),
        })
    cvid = {}
    for c in carriers:
        n = int(c["carrier_id"][4:])
        vid = f"VND-{100 + n:06d}"
        cvid[c["carrier_id"]] = vid
        vendors.append({
            "vendor_id": vid, "supplier_id": None, "carrier_id": c["carrier_id"], "name": c["name"], "country": c["country"],
            "bank_country": c["country"], "tax_id": f"TAX-{r.randint(100000, 999999)}", "payment_terms_days": 30,
            "on_payment_hold": False, "hold_reason": None, "hold_date": None, "fraud_risk_score": r.randint(4, 25),
            "fraud_indicators": [], "control_approvals_required": 1, "created_date": date(2022, 1, 10),
            "updated_at": g.date_between(120, 20),
        })
    vendor = {v["vendor_id"]: v for v in vendors}

    # ------------------------------------------------------------------ helpers
    seq = {"inv": 0}
    run_ids_past = []

    def add_invoice(inv_id=None, vid=None, supplier=None, carrier=None, itype="supplier", number=None, inv_date=None,
                    amount=0.0, po_id=None, match="matched", gl="5000", cc=None, accrued=True, desc=None,
                    pay_days=None, dispute=None):
        if inv_id is None:
            seq["inv"] += 1
            inv_id = f"INV-{seq['inv']:06d}"
        vid = vid or (vid_of[supplier] if supplier else cvid[carrier])
        terms = vendor[vid]["payment_terms_days"]
        inv = {
            "invoice_id": inv_id, "vendor_id": vid, "supplier_id": supplier, "carrier_id": carrier, "invoice_type": itype,
            "invoice_number": number or f"{vid[-3:]}-{inv_id[-6:]}", "invoice_date": inv_date,
            "received_date": inv_date + timedelta(days=r.randint(0, 3)), "amount_gbp": round(amount, 2), "po_id": po_id,
            "three_way_match_status": match, "gl_account": gl, "cost_centre_id": cc, "accrued": accrued,
            "accrual_date": inv_date + timedelta(days=3) if accrued else None, "payment_status": "open",
            "payment_run_id": None, "scheduled_payment_date": inv_date + timedelta(days=terms), "actual_payment_date": None,
            "dispute_reason": dispute, "description": desc, "created_date": inv_date, "updated_at": inv_date + timedelta(days=1),
        }
        if dispute:
            inv["payment_status"] = "disputed"
        if pay_days is not None:
            pay = inv_date + timedelta(days=pay_days)
            assert pay <= A, (inv_id, pay)
            inv["payment_status"] = "paid"
            inv["actual_payment_date"] = pay
            inv["scheduled_payment_date"] = None
            run = r.choice(run_ids_past) if run_ids_past else None
            payments.append({
                "payment_id": f"PAY-{len(payments) + 1:06d}", "supplier_id": supplier, "vendor_id": vid, "invoice_id": inv_id,
                "amount_gbp": round(amount, 2), "payment_date": pay, "payment_run_id": run, "days_to_pay": pay_days,
                "bank_account": _acct(vid),
            })
        invoices.append(inv)
        return inv

    # ------------------------------------------------------------------ payment runs
    friday = A + timedelta(days=(4 - A.weekday()) % 7)  # this week's Friday
    for i in range(13, 0, -1):
        d = friday - timedelta(weeks=i)
        rid = f"RUN-{14 - i:06d}"
        run_ids_past.append(rid)
        runs.append({"payment_run_id": rid, "run_date": d, "run_type": "regular", "invoices_count": r.randint(9, 24),
                     "total_amount_gbp": round(r.uniform(180000, 620000), 2), "status": "completed", "cancellation_reason": None,
                     "created_date": d - timedelta(days=3), "created_by": r.choice(employees), "updated_at": d})
    future = [("RUN-900001", friday, "regular", 31, 1640000.0),
              ("RUN-900002", friday + timedelta(weeks=1), "ad_hoc", 12, 420000.0)]
    for k in range(2, 13):
        future.append((f"RUN-9001{k:02d}", friday + timedelta(weeks=k), "regular", r.randint(14, 30),
                       round(r.uniform(450000, 900000), 2)))
    for rid, d, typ, n, tot in future:
        runs.append({"payment_run_id": rid, "run_date": d, "run_type": typ, "invoices_count": n, "total_amount_gbp": tot,
                     "status": "scheduled", "cancellation_reason": None, "created_date": D(4), "created_by": "EMP-00003",
                     "updated_at": D(4)})

    # ------------------------------------------------------------------ air freight (last quarter ~ GBP 420k)
    air_rows = [  # id, supplier (cause), airline/forwarder, days ago, amount, shipments, reason, avoidable %, chargeability
        (1, "SUP-0012", "CAR-008", 17, 52000, 6, "supplier_late", 100, "chargeable_to_supplier"),
        (2, "SUP-0012", "CAR-008", 45, 38000, 4, "supplier_late", 100, "chargeable_to_supplier"),
        (3, "SUP-0015", "CAR-009", 31, 35000, 5, "supplier_late", 100, "chargeable_to_supplier"),
        (4, "SUP-0008", "CAR-010", 59, 25000, 3, "supplier_late", 100, "chargeable_to_supplier"),
        (5, "SUP-0015", "CAR-018", 38, 24000, 3, "quality_issue", 100, "chargeable_to_supplier"),
        (6, "SUP-0003", "CAR-008", 24, 16000, 2, "quality_issue", 100, "chargeable_to_supplier"),
        (7, "SUP-0021", "CAR-018", 52, 20000, 2, "cancelled_order", 100, "no_chargeable_position"),
        (8, "SUP-0003", "CAR-009", 10, 60000, 7, "demand_spike", 30, "no_chargeable_position"),
        (9, "SUP-0021", "CAR-010", 36, 60000, 8, "demand_spike", 30, "no_chargeable_position"),
        (10, "SUP-0003", "CAR-008", 13, 52000, 6, "store_emergency", 0, "no_chargeable_position"),
        (11, "SUP-0021", "CAR-018", 27, 38000, 5, "store_emergency", 0, "no_chargeable_position"),
    ]
    for n, s, c, days, amt, ships, reason, pct, chg in air_rows:
        chargeable = chg == "chargeable_to_supplier"
        air.append({
            "invoice_id": f"FRT-9{n:05d}", "supplier_id": s, "carrier_id": c, "invoice_date": D(days), "amount_gbp": float(amt),
            "shipment_count": ships, "air_reason": reason, "avoidable": pct > 0, "avoidable_pct": float(pct),
            "chargeability": chg, "contract_rate_gbp": round(amt / ships, 2), "overcharge_gbp": 0.0,
            "status": "chargeable_drafted" if chargeable and days < 30 else "open", "created_date": D(days)})
    suppliers_air = ["SUP-0003", "SUP-0008", "SUP-0012", "SUP-0015", "SUP-0021"]
    for i in range(1, 9):  # older history, outside the last 90 days
        days = r.randint(125, 340)
        amt = round(r.uniform(9000, 42000), -2)
        ships = r.randint(2, 7)
        reason = r.choice(["supplier_late", "demand_spike", "store_emergency", "quality_issue"])
        pct = {"supplier_late": 100, "quality_issue": 100, "demand_spike": 30, "store_emergency": 0}[reason]
        air.append({
            "invoice_id": f"FRT-{i:06d}", "supplier_id": r.choice(suppliers_air), "carrier_id": r.choice(["CAR-008", "CAR-009", "CAR-010", "CAR-018"]),
            "invoice_date": D(days), "amount_gbp": amt, "shipment_count": ships, "air_reason": reason,
            "avoidable": pct > 0, "avoidable_pct": float(pct),
            "chargeability": "chargeable_to_supplier" if reason in ("supplier_late", "quality_issue") else "no_chargeable_position",
            "contract_rate_gbp": round(amt / ships, 2), "overcharge_gbp": 0.0, "status": "closed", "created_date": D(days)})

    # ------------------------------------------------------------------ carrier invoices with lines
    def carrier_invoice(carrier, days, over, total=None, accrued=True, tag="CAR", cc="CC-2124", dispute=None, gl="5102"):
        """Four-line-plus carrier invoice; `over` = overcharge per category (billed above contract)."""
        s_over, a_over, w_over, v_over = (over.get(k, 0.0) for k in ("surcharge", "accessorial", "weight_variance", "service_level"))
        delta = over.get("rounding", 0.0)
        fixed = 900 + s_over + 1200 + a_over + 1500 + w_over + 2000 + v_over + delta
        if total:
            base = round((total - fixed) / 1.065, 2)
            fuel = round(total - fixed - base, 2)
        else:
            base = over["base"]
            fuel = round(base * 0.065, 2)
        inv_date = D(days)
        inv = add_invoice(carrier=carrier, itype="carrier", number=f"{tag}-{r.randint(10000, 99999)}", inv_date=inv_date,
                          amount=0, match="pending", gl=gl, cc=cc, accrued=accrued, dispute=dispute,
                          pay_days=None if (days < 45 or dispute) else min(days - 5, r.randint(24, 34)),
                          desc="Four-weekly carrier invoice")
        spec = [
            ("Linehaul freight", "freight", base, base, 0.0),
            ("Fuel surcharge (contract index)", "surcharge", fuel + delta, fuel, delta),
            ("Peak / residential surcharge", "surcharge", 900 + s_over, 900, s_over),
            ("Accessorials (tail-lift, waiting time)", "accessorial", 1200 + a_over, 1200, a_over),
            ("Weight adjustment (billed vs actual weight)", "weight_variance", 1500 + w_over, 1500, w_over),
            ("Service level premium (contract = standard)", "service_level", 2000 + v_over, 2000, v_over),
        ]
        tot = 0.0
        for i, (d, ct, billed, contracted, var) in enumerate(spec, 1):
            var = round(billed - contracted, 2)
            tot += billed
            lines.append({"invoice_id": inv["invoice_id"], "line_no": i, "description": d, "quantity": 1.0,
                          "unit_price_gbp": round(billed, 2), "line_total_gbp": round(billed, 2), "charge_type": ct,
                          "contracted_rate_gbp": round(contracted, 2), "variance_gbp": var,
                          "variance_pct": round(var * 100 / contracted, 1) if contracted else 0.0, "disputable": var > 25})
        inv["amount_gbp"] = round(tot, 2)
        if inv["actual_payment_date"]:
            payments[-1]["amount_gbp"] = inv["amount_gbp"]
        return inv

    # CAR-002 Midshires Transport: twelve four-weekly invoices, overcharges by category
    s_o = [0, 1450, 0, 0, 1820, 960, 0, 1730, 0, 0, 1280, 0]
    a_o = [620, 0, 540, 0, 0, 710, 480, 0, 0, 590, 0, 830]
    w_o = [0, 2340, 0, 1860, 0, 0, 2610, 0, 1950, 0, 2275, 0]
    v_o = [0, 0, 3120, 0, 0, 4180, 0, 0, 0, 3560, 0, 0]
    rounding = [4.5, -3.2, 7.8, 0.0, -6.1, 2.4, 9.3, -4.8, 1.2, 5.6, -2.7, 8.1]
    for k in range(12):
        over = {"surcharge": s_o[k], "accessorial": a_o[k], "weight_variance": w_o[k], "service_level": v_o[k],
                "rounding": rounding[k], "base": 41000 + 1150 * ((k * 5) % 7)}
        carrier_invoice("CAR-002", 8 + 28 * k, over, total=59896.0 if k == 0 else None, accrued=k != 0, tag="MID")
    # CAR-001 Northline: Aug surcharge not in contract (GBP 1,250.50); latest invoice unaccrued (63,254)
    for k in range(6):
        over = {"surcharge": 1250.5 if k == 2 else 0.0, "rounding": [2.1, -1.4, 3.3, 0.9, -2.2, 1.7][k], "base": 36000 + 900 * k}
        carrier_invoice("CAR-001", 8 + 28 * k, over, total=63254.0 if k == 0 else None, accrued=k != 0, tag="NLH", cc="CC-2124")
    # CAR-003 Pennine: incorrect service level charged (GBP 450.25) a few weeks ago
    for k in range(6):
        over = {"service_level": 450.25 if k == 1 else 0.0, "rounding": [1.3, -2.0, 0.6, 2.9, -1.1, 0.4][k], "base": 52000 + 1300 * k}
        carrier_invoice("CAR-003", 12 + 28 * k, over, accrued=True, tag="PEN", cc="CC-2124")

    # freight (air / ocean) invoices received but not accrued: CAR-008 66,981 and CAR-006 18,691
    for carrier, items in (("CAR-008", [(20, 28300.0), (13, 21450.0), (6, 17231.0)]), ("CAR-006", [(18, 11200.0), (9, 7491.0)])):
        for days, amt in items:
            add_invoice(carrier=carrier, itype="freight", number=f"FRT-{r.randint(100000, 999999)}", inv_date=D(days), amount=amt,
                        match="pending", gl="5105" if carrier == "CAR-008" else "5100", cc="CC-2124", accrued=False,
                        desc="Freight forwarding invoice")
    # miscoded freight invoices (accrued, but on the wrong account or without a cost centre)
    for inv_id, carrier, itype, days, amt, gl, cc in (
            ("INV-902001", "CAR-004", "carrier", 34, 18400.0, "5000", "CC-2104"),
            ("INV-902002", "CAR-016", "freight", 41, 9750.0, "6100", "CC-2124"),
            ("INV-902003", "CAR-003", "carrier", 29, 4860.0, "5102", None),
            ("INV-902004", "CAR-017", "carrier", 47, 6120.0, "4000", "CC-2124")):
        add_invoice(inv_id=inv_id, carrier=carrier, itype=itype, number=f"{carrier[-3:]}-{r.randint(10000, 99999)}",
                    inv_date=D(days), amount=amt, match="pending", gl=gl, cc=cc, accrued=True, desc="Freight invoice")
    # clean background freight invoices
    for carrier, gl, itype in (("CAR-005", "5100", "freight"), ("CAR-007", "5100", "freight"), ("CAR-009", "5105", "freight"),
                               ("CAR-004", "5102", "carrier"), ("CAR-011", "5102", "carrier"), ("CAR-012", "5102", "carrier"),
                               ("CAR-018", "5105", "freight"), ("CAR-010", "5105", "freight")):
        days = r.randint(15, 80)
        add_invoice(carrier=carrier, itype=itype, number=f"{carrier[-3:]}-{r.randint(10000, 99999)}", inv_date=D(days),
                    amount=round(r.uniform(3000, 22000), 2), match="pending", gl=gl, cc="CC-2124", accrued=True,
                    desc="Freight invoice", pay_days=min(days - 3, r.randint(22, 35)) if days > 30 else None)

    # ------------------------------------------------------------------ facilities suppliers
    month_dates = []
    y, m = 2025, 10
    for _ in range(12):
        month_dates.append(date(y, m, 15))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    fm14 = {2: 100279, 3: 101124, 4: 97577, 5: 97918, 6: 101263, 7: 111412, 8: 103632, 9: 102224}
    fm26 = [34119, 32567, 32681, 33684, 32582, 34087, 34411, 33742, 32485, 33899, 32908, 32833]
    fm67 = [18597, 19880, 19398, 18034, 20603, 20103, 19420, 19120, 18860, 20195, 18194, 17983]
    for i, d in enumerate(month_dates):
        for sid, amt, cc, prefix in (("SUP-0026", fm26[i], "CC-2102", "SW"), ("SUP-0067", fm67[i], "CC-2101", "DV"),
                                     ("SUP-0014", fm14.get(d.month) if d.year == 2026 else None, "CC-2101", "GL")):
            if not amt:
                continue
            terms = int(sup[sid]["payment_terms_days"])
            age = (A - d).days
            pay = terms - r.randint(0, 4) if age > terms + 3 else None
            add_invoice(supplier=sid, number=f"{prefix}-{d:%y%m}-{r.randint(100, 999)}", inv_date=d, amount=float(amt), gl="6410",
                        cc=cc, match="matched", desc="Monthly facilities management service", pay_days=pay)
    for stage, (d, amt) in enumerate([(date(2026, 4, 15), 287437.0), (date(2026, 5, 15), 259839.0), (date(2026, 6, 15), 179737.0)], 1):
        add_invoice(supplier="SUP-0067", number=f"DV-RF-{stage:02d}", inv_date=d, amount=amt, gl="6450", cc="CC-2101",
                    match="matched", desc=f"Warehouse roof replacement stage {stage} of 3 (one-off project)", pay_days=28 + stage)

    # ------------------------------------------------------------------ supplier payment performance
    # SUP-0053 (60-day terms): paid inside terms except once. SUP-0012 (30-day terms): we pay late and it is getting worse.
    p53 = [330, 300, 270, 240, 210, 180, 150, 120, 90, 60, 35, 14]
    a53 = [182000, 176500, 191200, 168400, 205000, 188300, 179900, 196700, 171200, 183600, 160800, 174500]
    d53 = [54, 57, 52, 59, 56, 49, 63, 55, 58, 57]
    for i, days in enumerate(p53):
        add_invoice(supplier="SUP-0053", inv_date=D(days), amount=float(a53[i]), gl="5000", cc="CC-2113", match="matched",
                    desc="Goods invoice", pay_days=d53[i] if i < 10 else None)
    p12 = [350, 322, 294, 266, 238, 210, 182, 154, 126, 98, 70, 56, 18, 9]
    a12 = [21500, 18900, 24300, 19800, 22700, 20400, 23100, 25800, 21900, 26500, 24100, 13800, 27400, 22600]
    d12 = [26, 28, 29, 30, 33, 35, 34, 41, 46, 52, 58]
    for i, days in enumerate(p12):
        add_invoice(supplier="SUP-0012", inv_date=D(days), amount=float(a12[i]), gl="5000", cc="CC-2113", match="matched",
                    desc="Goods invoice", pay_days=d12[i] if i < 11 else None)

    # ------------------------------------------------------------------ new vendors, bank changes, fraud-pattern payments
    bdc = [  # id, supplier, requested days ago, old country, new country, approvals, status, first payment days after
        ("BDC-900002", "SUP-0048", 21, "VN", "SG", 1, "approved", 2),
        ("BDC-900003", "SUP-0071", 40, "TR", "NL", 1, "approved", 3),
        ("BDC-900004", "SUP-0004", 150, "TR", "TR", 2, "approved", 38),
        ("BDC-900005", "SUP-0010", 95, "CN", "CN", 2, "approved", 27),
        ("BDC-900006", "SUP-0016", 62, "PT", "PT", 1, "approved", 33),
    ]
    for cid, sid, days, oldc, newc, appr, status, fp in bdc:
        vid = vid_of[sid]
        if cid in ("BDC-900004", "BDC-900005", "BDC-900006"):
            appr = vendor[vid]["control_approvals_required"]
            add_invoice(supplier=sid, inv_date=D(days - fp + 10), amount=round(r.uniform(8000, 30000), 2), gl="5000", cc="CC-2113",
                        match="matched", desc="Goods invoice", pay_days=10)
        bank_changes.append({
            "change_id": cid, "vendor_id": vid, "old_bank_account": _acct(vid, oldc), "new_bank_account": _acct(vid + "n", newc),
            "old_bank_country": oldc, "new_bank_country": newc, "requested_date": D(days), "requested_by": r.choice(employees),
            "approval_status": status, "approvals_count": appr, "first_payment_date": D(days - fp), "updated_at": D(days)})
    # payments made to the changed accounts
    for sid, days, amt, newc, vid_s in (("SUP-0048", 19, 38400.0, "SG", "BDC-900002"), ("SUP-0071", 37, 29950.0, "NL", "BDC-900003")):
        vid = vid_of[sid]
        inv = add_invoice(supplier=sid, inv_date=D(days + 3), amount=amt, gl="5000", cc="CC-2113", match="pending",
                          desc="Goods invoice (no PO)", pay_days=3)
        payments[-1]["bank_account"] = _acct(vid + "n", newc)
    # new vendors paid within days of creation
    for sid, create_gap, amt in (("SUP-0060", 2, 61500.0), ("SUP-0034", 2, 74200.0)):
        inv = add_invoice(supplier=sid, inv_date=iso(sup[sid]["onboarded_date"]) + timedelta(days=create_gap), amount=amt,
                          gl="5000", cc="CC-2116", match="pending", desc="Goods invoice (no PO)", pay_days=3 if sid == "SUP-0034" else 5)
    # open invoices on the lookalike / fraud-pattern vendors (what is blocked if they are held)
    add_invoice(supplier="SUP-0048", inv_date=D(11), amount=41200.0, gl="5000", cc="CC-2113", match="pending",
                desc="Goods invoice (no PO)")
    add_invoice(supplier="SUP-0048", inv_date=D(5), amount=18750.0, gl="5000", cc="CC-2113", match="pending",
                desc="Goods invoice (no PO)")
    add_invoice(supplier="SUP-0062", inv_date=D(26), amount=37600.0, gl="5000", cc="CC-2113", match="pending",
                desc="Goods invoice", po_id=None)

    # ------------------------------------------------------------------ rebates
    def agreement(aid, sid, typ, thr, pct, fixed, frm, to, status):
        agreements.append({"agreement_id": aid, "supplier_id": sid, "rebate_type": typ, "threshold_amount_gbp": float(thr),
                           "rebate_pct": float(pct), "rebate_amount_gbp": float(fixed), "effective_from": frm, "effective_to": to,
                           "status": status, "created_date": frm - timedelta(days=20)})

    def accrual(aid, sid, period, ytd, accrued, settled, adate, sdate, status):
        accruals.append({"accrual_id": f"ACR-{len(accruals) + 1:06d}", "agreement_id": aid, "supplier_id": sid,
                         "accrual_period": period, "ytd_spend_gbp": float(ytd), "accrued_amount_gbp": float(accrued),
                         "settled_amount_gbp": float(settled), "accrual_date": adate, "settlement_date": sdate, "status": status})

    fy26a, fy26b = date(2025, 2, 1), date(2026, 1, 31)
    fy27a, fy27b = date(2026, 2, 1), date(2027, 1, 31)
    agreement("RBA-900011", "SUP-0001", "volume", 900000, 2.0, 0, fy26a, fy26b, "expired")
    agreement("RBA-900001", "SUP-0001", "volume", 1000000, 2.5, 0, fy27a, fy27b, "active")
    agreement("RBA-900002", "SUP-0015", "volume", 3000000, 1.5, 0, fy27a, fy27b, "active")
    agreement("RBA-900012", "SUP-0008", "volume", 1800000, 3.0, 0, fy26a, fy26b, "expired")
    agreement("RBA-900003", "SUP-0008", "volume", 1800000, 3.0, 0, fy27a, fy27b, "active")
    agreement("RBA-900004", "SUP-0003", "quality_bonus", 0, 0, 15000, fy27a, fy27b, "active")
    agreement("RBA-900005", "SUP-0021", "cost_reduction", 0, 0, 8000, fy27a, fy27b, "active")
    # previous year: SUP-0001 settled in line; SUP-0008 accrued on a 2.2m forecast but bought 2.05m, settled 7,500
    accrual("RBA-900011", "SUP-0001", "FY26-Q3", 810000, 0, 0, date(2025, 11, 10), None, "accrued")
    accrual("RBA-900011", "SUP-0001", "FY26-Q4", 1085000, 3700, 3700, date(2026, 2, 10), date(2026, 3, 12), "settled")
    accrual("RBA-900012", "SUP-0008", "FY26-Q2", 1010000, 0, 0, date(2025, 8, 12), None, "accrued")
    accrual("RBA-900012", "SUP-0008", "FY26-Q3", 1540000, 12000, 0, date(2025, 11, 10), None, "accrued")
    accrual("RBA-900012", "SUP-0008", "FY26-Q4", 2050000, 12000, 7500, date(2026, 2, 10), date(2026, 3, 18), "settled")
    # current year (FY27 = Feb 2026 - Jan 2027): accrued on forecast annual spend, pro rata to spend to date
    accrual("RBA-900001", "SUP-0001", "FY27-Q1", 280000, 891.9, 0, date(2026, 5, 11), None, "accrued")
    accrual("RBA-900001", "SUP-0001", "FY27-Q2", 590000, 1879.2, 0, date(2026, 8, 10), None, "accrued")
    accrual("RBA-900002", "SUP-0015", "FY27-Q1", 820000, 1554.7, 0, date(2026, 5, 11), None, "accrued")
    accrual("RBA-900002", "SUP-0015", "FY27-Q2", 1720000, 3261.0, 0, date(2026, 8, 10), None, "accrued")
    accrual("RBA-900003", "SUP-0008", "FY27-Q1", 450000, 0, 0, date(2026, 5, 11), None, "accrued")
    accrual("RBA-900003", "SUP-0008", "FY27-Q2", 960000, 6000, 0, date(2026, 8, 10), None, "accrued")
    accrual("RBA-900004", "SUP-0003", "FY27-Q1", 410000, 3750, 0, date(2026, 5, 11), None, "accrued")
    accrual("RBA-900004", "SUP-0003", "FY27-Q2", 880000, 7500, 0, date(2026, 8, 10), None, "accrued")
    accrual("RBA-900005", "SUP-0021", "FY27-Q2", 760000, 4000, 0, date(2026, 8, 10), None, "accrued")

    # ------------------------------------------------------------------ background supplier invoices linked to master POs
    eligible_sup = {s["supplier_id"] for s in suppliers
                    if s["status"] == "active" and s["onboarded_date"] < "2025-06-01" and s["supplier_id"] not in STORY_SUPPLIERS
                    and s["supplier_id"] not in OVR}
    cands = [p for p in pos if p["supplier_id"] in eligible_sup and p["status"] in ("closed", "received", "shipped")
             and (A - timedelta(days=150)).isoformat() <= p["order_date"] <= (A - timedelta(days=20)).isoformat()]
    noise = r.sample(cands, min(40, len(cands)))
    noise.sort(key=lambda p: p["po_id"])
    bad = 0
    for p in noise:
        od = iso(p["order_date"])
        inv_date = min(A - timedelta(days=6), od + timedelta(days=r.randint(25, 60)))
        terms = int(sup[p["supplier_id"]]["payment_terms_days"])
        age = (A - inv_date).days
        match = "variance" if bad < 8 and r.random() < 0.3 else "matched"
        bad += match == "variance"
        add_invoice(supplier=p["supplier_id"], inv_date=inv_date, amount=float(p["total_value"]) * r.uniform(0.97, 1.03),
                    po_id=p["po_id"], match=match, gl="5000", cc="CC-2113", desc="Goods invoice",
                    pay_days=terms + r.randint(-6, 6) if age > terms + 8 else None)
    # supplier fraud signal (loss prevention): SUP-0020 invoices more units than were received on five POs
    # in the last ~4 months, every time; everyone else only has small, mixed quantity differences
    STORY_GRN = "SUP-0020"
    taken = {i["po_id"] for i in invoices if i["po_id"]}
    story_pos = [p for p in pos if p["supplier_id"] == STORY_GRN and p["status"] in ("closed", "received")
                 and p["po_id"] not in taken
                 and (A - timedelta(days=150)).isoformat() <= p["order_date"] <= (A - timedelta(days=50)).isoformat()]
    story_pos.sort(key=lambda p: p["po_id"])
    story_pos = story_pos[:5]
    assert len(story_pos) == 5
    story_over = [260, 300, 220, 280, 240]
    story_inv = {}
    for p, over in zip(story_pos, story_over):
        od = iso(p["order_date"])
        inv_date = min(A - timedelta(days=6), od + timedelta(days=r.randint(25, 45)))
        age = (A - inv_date).days
        units = int(p["total_units"])
        up = float(p["total_value"]) / units
        inv = add_invoice(supplier=STORY_GRN, inv_date=inv_date, amount=(units + over) * up, po_id=p["po_id"], match="variance",
                          gl="5000", cc="CC-2113", desc="Goods invoice", pay_days=62 if age > 70 else None)
        story_inv[p["po_id"]] = (inv, units, over, up)
    n = 0
    for po_id, (inv, units, over, up) in story_inv.items():
        n += 1
        grn_amt = round(units * up, 2)
        inv_amt = round((units + over) * up, 2)
        grn.append({"variance_id": f"VAR-9{n:05d}", "po_id": po_id, "invoice_id": inv["invoice_id"], "grn_quantity": units,
                    "invoice_quantity": units + over, "quantity_variance": over, "grn_amount_gbp": grn_amt,
                    "invoice_amount_gbp": inv_amt, "amount_variance_gbp": round(inv_amt - grn_amt, 2),
                    "variance_type": "quantity", "status": "pending" if n > 2 else "investigated",
                    "created_date": inv["invoice_date"] + timedelta(days=5)})
    for n, inv in enumerate([i for i in invoices if i["three_way_match_status"] == "variance" and i["po_id"]
                             and i["supplier_id"] != STORY_GRN][:6], 1):
        po = next(p for p in pos if p["po_id"] == inv["po_id"])
        units = int(po["total_units"])
        qv = r.choice([-25, -20, 20, 20, -40, 25])
        up = float(po["total_value"]) / units
        grn_amt = round(units * up, 2)
        inv_amt = round((units + qv) * up, 2)
        grn.append({"variance_id": f"VAR-{n:06d}", "po_id": inv["po_id"], "invoice_id": inv["invoice_id"], "grn_quantity": units,
                    "invoice_quantity": units + qv, "quantity_variance": qv, "grn_amount_gbp": grn_amt, "invoice_amount_gbp": inv_amt,
                    "amount_variance_gbp": round(inv_amt - grn_amt, 2), "variance_type": "quantity",
                    "status": r.choice(["pending", "investigated", "resolved", "resolved"]),
                    "created_date": inv["invoice_date"] + timedelta(days=5)})

    return {
        "vendors": vendors, "bank_detail_changes": bank_changes, "invoices": invoices, "invoice_lines": lines,
        "rebate_agreements": agreements, "rebate_accruals": accruals, "payment_runs": runs, "supplier_payments": payments,
        "goods_receipt_invoice_variance": grn, "air_freight_invoices": air,
    }
