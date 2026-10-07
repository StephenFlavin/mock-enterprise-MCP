"""AR system: wholesale customer invoices, payments, credit accounts and collection patterns.

Wholesale customers are master customers CUS-000001..CUS-000045 (master has no wholesale segment).
Each customer has a payment profile: good, steady_late or worsening (pays later and later).
Story customers are written by hand below: CUS-000034 (Hartley & Reed Ltd, Q1), CUS-000028 (disputed GBP 480k invoice, Q2),
CUS-000016 (75 days overdue, Q5).
"""
from datetime import datetime, timedelta

POOL = [f"CUS-{n:06d}" for n in range(1, 46)]
WORSENING = {"CUS-000016": 60, "CUS-000034": 33, "CUS-000010": 48, "CUS-000033": 40, "CUS-000026": 44,
             "CUS-000038": 36, "CUS-000007": 52, "CUS-000019": 38, "CUS-000041": 46, "CUS-000044": 42}
STEADY = {"CUS-000022", "CUS-000030", "CUS-000037", "CUS-000003", "CUS-000014", "CUS-000031", "CUS-000036"}
STORY = {"CUS-000016", "CUS-000034", "CUS-000028"}
TERMS = {"CUS-000016": 30, "CUS-000028": 30, "CUS-000034": 60}
SCORE = {"CUS-000016": 38, "CUS-000034": 58, "CUS-000028": 82}
LIMIT = {"CUS-000016": 100000, "CUS-000034": 250000, "CUS-000028": 750000}
RATES = [(30, 0.02), (60, 0.05), (90, 0.15), (10 ** 6, 0.35)]


def _ts(d, h=9):
    return datetime(d.year, d.month, d.day, h, 0, 0)


def generate(g):
    r = g.rng
    as_of = g.as_of
    D = lambda s: datetime.strptime(s, "%Y-%m-%d").date()
    products = [p for p in g.master("products") if p["status"] == "active"]

    profile, terms, lateness_now = {}, {}, {}
    for cid in POOL:
        profile[cid] = "worsening" if cid in WORSENING else "steady_late" if cid in STEADY else "good"
        terms[cid] = TERMS.get(cid, r.choice([30, 30, 45, 60]))
        lateness_now[cid] = WORSENING.get(cid, 8 if cid in STEADY else -1)

    def late(cid, days_ago):
        """Expected days paid after due date for an invoice that fell due `days_ago` days ago."""
        if profile[cid] == "worsening":
            return -2 + (lateness_now[cid] + 2) * max(0.0, 1 - days_ago / 330)
        return lateness_now[cid]

    invoices, lines, payments = [], [], []

    def add_invoice(cid, inv_id, order_id, inv_date, amount, pays, dispute=("none", ""), sku_lines=None):
        """pays = list of (date, amount) payments already received (all <= as_of)."""
        due = inv_date + timedelta(days=terms[cid])
        paid = round(sum(a for _, a in pays), 2)
        if paid >= amount - 0.005:
            status = "paid"
        elif paid > 0:
            status = "part_paid"
        elif due < as_of:
            status = "overdue"
        else:
            status = "open"
        invoices.append({"invoice_id": inv_id, "customer_id": cid, "order_id": order_id, "invoice_date": inv_date,
                         "due_date": due, "amount_gbp": round(amount, 2), "paid_amount_gbp": paid, "status": status,
                         "dispute_status": dispute[0], "dispute_reason": dispute[1], "created_at": _ts(inv_date),
                         "updated_at": _ts(pays[-1][0], 14) if pays else _ts(inv_date)})
        if sku_lines is None:
            k = 1 if amount < 40000 else 2
            sku_lines, remaining = [], round(amount, 2)
            for i in range(k):
                p = r.choice(products)
                price = round(float(p["unit_cost_gbp"]) * r.uniform(1.6, 2.2), 2)
                qty = max(1, round((amount / k) / price))
                total = round(qty * price, 2) if i < k - 1 else remaining
                if i == k - 1:
                    price = round(total / qty, 2)
                remaining = round(remaining - total, 2)
                sku_lines.append((p["sku"], p["name"], qty, price, total))
        for n, (sku, desc, qty, price, total) in enumerate(sku_lines, 1):
            lines.append({"invoice_id": inv_id, "line_no": n, "sku": sku, "description": desc, "qty": qty,
                          "unit_price_gbp": price, "line_total_gbp": total})
        for d, a in pays:
            payments.append({"payment_id": f"PAY-2026-{len(payments) + 1:06d}", "customer_id": cid, "invoice_id": inv_id,
                             "amount_gbp": round(a, 2), "payment_date": d, "received_date": d + timedelta(days=1)
                             if d < as_of else d, "payment_method": r.choice(["bank_transfer", "bank_transfer", "direct_debit", "cheque"]),
                             "reference": f"BACS-{r.randint(10 ** 7, 10 ** 8 - 1)}", "notes": ""})

    # ---- generated invoices for non-story customers
    seq = 0
    for cid in POOL:
        if cid in STORY:
            continue
        prof = profile[cid]
        step = 14 if prof == "worsening" else 24
        amt_lo, amt_hi = {"worsening": (40000, 140000), "steady_late": (20000, 70000), "good": (8000, 60000)}[prof]
        day = 175 - r.randint(0, 8)
        while day >= 6:
            inv_date = as_of - timedelta(days=day)
            due = inv_date + timedelta(days=terms[cid])
            amount = round(r.uniform(amt_lo, amt_hi), 2)
            lag = late(cid, (as_of - due).days) + r.uniform(-3, 3)
            pay_date = max(inv_date + timedelta(days=3), due + timedelta(days=round(lag)))
            seq += 1
            pays = []
            if pay_date <= as_of:
                pays = [(pay_date, amount)]
            elif prof == "worsening" and r.random() < 0.3 and due + timedelta(days=6) <= as_of:
                pays = [(due + timedelta(days=6), round(amount * r.choice([0.3, 0.4, 0.5]), 2))]
            add_invoice(cid, f"INV-2026-{seq:06d}", "", inv_date, amount, pays)
            day -= step + r.randint(-3, 3)

    # ---- story invoices
    add_i = add_invoice
    # Q5: CUS-000016, oldest unpaid invoice 75 days overdue, 30 day terms
    add_i("CUS-000016", "INV-2026-000901", "", D("2026-04-20"), 45000, [(D("2026-06-18"), 45000)])
    add_i("CUS-000016", "INV-2026-000902", "", D("2026-05-25"), 38000, [(D("2026-08-05"), 38000)])
    add_i("CUS-000016", "INV-2026-000903", "", D("2026-06-22"), 62400, [])      # due 2026-07-22 = 75 days overdue
    add_i("CUS-000016", "INV-2026-000904", "", D("2026-07-17"), 28600, [])      # 50 days overdue
    add_i("CUS-000016", "INV-2026-000905", "", D("2026-08-24"), 21000, [])      # 12 days overdue
    # Q1: Hartley & Reed Ltd = CUS-000034, 60 day terms, paying later each time
    add_i("CUS-000034", "INV-2026-000911", "", D("2026-01-05"), 80000, [(D("2026-03-10"), 80000)])   # 4 days late
    add_i("CUS-000034", "INV-2026-000912", "", D("2026-03-02"), 76000, [(D("2026-05-14"), 76000)])   # 13 days late
    add_i("CUS-000034", "INV-2026-000913", "", D("2026-04-27"), 88000, [(D("2026-07-21"), 88000)])   # 25 days late
    add_i("CUS-000034", "INV-2026-000914", "", D("2026-07-06"), 95000, [])      # due 2026-09-04, 31 days overdue
    add_i("CUS-000034", "INV-2026-000915", "", D("2026-08-03"), 70000, [])      # due 2026-10-02, 3 days overdue
    add_i("CUS-000034", "INV-2026-000916", "", D("2026-09-07"), 52000, [])      # not yet due
    # Q2: CUS-000028 disputes invoice INV-2026-009876: 8,000 units at GBP 60 = 480k, 360 units short delivered
    add_i("CUS-000028", "INV-2026-000921", "", D("2026-06-01"), 120000, [(D("2026-06-29"), 120000)])
    add_i("CUS-000028", "INV-2026-000922", "", D("2026-07-06"), 150000, [(D("2026-08-04"), 150000)])
    add_i("CUS-000028", "INV-2026-009876", "ORD-900040", D("2026-08-17"), 480000, [],
          dispute=("disputed", "Customer says 360 of the 8,000 units invoiced were not delivered; asks for credit at the agreed price"),
          sku_lines=[("SKU-100448", "Wholesale lot A", 4000, 60.0, 240000.0), ("SKU-100455", "Wholesale lot B", 4000, 60.0, 240000.0)])

    # ---- accounts
    unpaid = {}
    for inv in invoices:
        unpaid[inv["customer_id"]] = unpaid.get(inv["customer_id"], 0) + inv["amount_gbp"] - inv["paid_amount_gbp"]
    accounts = []
    for cid in POOL:
        prof = profile[cid]
        score = SCORE.get(cid) or (r.randint(38, 60) if prof == "worsening" else r.randint(62, 72) if prof == "steady_late" else r.randint(72, 93))
        rating = "critical" if score < 50 else "high" if score < 65 else "medium" if score < 80 else "low"
        bal = round(unpaid.get(cid, 0), 2)
        limit = LIMIT.get(cid) or max(25000, int(round(bal * r.uniform(1.05, 1.5) / 25000.0) * 25000), 50000)
        accounts.append({"customer_id": cid, "credit_limit_gbp": limit, "credit_held": False, "credit_hold_reason": "",
                         "current_balance_gbp": bal, "payment_terms_days": terms[cid], "credit_score": score,
                         "account_status": "active", "risk_rating": rating,
                         "average_dpo_days": round(terms[cid] + max(0, late(cid, 0)) + (r.uniform(-1, 1) if cid not in STORY else 0), 1),
                         "updated_at": _ts(as_of)})

    # ---- collection history: every 4 weeks for 24 months
    history = []
    for cid in POOL:
        prof = profile[cid]
        base = {"worsening": 90000, "steady_late": 45000, "good": 30000}[prof] * r.uniform(0.8, 1.3)
        for wk in range(0, 104, 4):
            d_ago = wk * 7
            mu = late(cid, d_ago)
            dtp = round(terms[cid] + mu + r.uniform(-2, 2), 1)
            on_time = round(min(100, max(5, 100 - 2.4 * max(0, mu) - r.uniform(0, 6))), 1) if mu > 0 else round(r.uniform(94, 100), 1)
            n = r.randint(2, 4)
            inv_amt = round(base * n * r.uniform(0.85, 1.15), 2)
            paid_amt = round(inv_amt * min(1.0, (on_time / 100) * 0.5 + 0.55) * r.uniform(0.95, 1.0), 2)
            history.append({"customer_id": cid, "recorded_on": as_of - timedelta(days=d_ago), "invoices_in_period": n,
                            "amount_invoiced_gbp": inv_amt, "amount_paid_gbp": paid_amt, "days_to_pay_avg": dtp,
                            "on_time_pct": on_time, "notes": ""})

    # ---- credit insurance
    insurance = [
        {"policy_id": "INS-00001", "customer_id": "CUS-000034", "insurer": "Atradius", "cover_limit_gbp": 200000,
         "cover_percentage_pct": 90, "policy_start": as_of - timedelta(days=290), "policy_end": as_of + timedelta(days=75),
         "status": "active", "updated_at": _ts(as_of)},
        {"policy_id": "INS-00002", "customer_id": "CUS-000016", "insurer": "Coface", "cover_limit_gbp": 75000,
         "cover_percentage_pct": 80, "policy_start": as_of - timedelta(days=200), "policy_end": as_of + timedelta(days=165),
         "status": "active", "updated_at": _ts(as_of)},
        {"policy_id": "INS-00003", "customer_id": "CUS-000028", "insurer": "Zurich", "cover_limit_gbp": 500000,
         "cover_percentage_pct": 90, "policy_start": as_of - timedelta(days=120), "policy_end": as_of + timedelta(days=245),
         "status": "active", "updated_at": _ts(as_of)},
        {"policy_id": "INS-00004", "customer_id": "CUS-000010", "insurer": "Euler Hermes", "cover_limit_gbp": 150000,
         "cover_percentage_pct": 85, "policy_start": as_of - timedelta(days=400), "policy_end": as_of - timedelta(days=35),
         "status": "expired", "updated_at": _ts(as_of)},
    ]
    for i, cid in enumerate(["CUS-000022", "CUS-000030", "CUS-000033", "CUS-000038", "CUS-000041"], 5):
        insurance.append({"policy_id": f"INS-{i:05d}", "customer_id": cid, "insurer": r.choice(["Atradius", "Coface", "Zurich"]),
                          "cover_limit_gbp": r.choice([100000, 150000, 250000]), "cover_percentage_pct": r.choice([80, 90]),
                          "policy_start": as_of - timedelta(days=r.randint(60, 300)), "policy_end": as_of + timedelta(days=r.randint(60, 300)),
                          "status": "active", "updated_at": _ts(as_of)})

    # ---- bad-debt provision: booked at last quarter end, lower than the ECL on today's ledger
    def ecl_buckets(at):
        b = [0.0, 0.0, 0.0, 0.0]
        for inv in invoices:
            bal = inv["amount_gbp"] - inv["paid_amount_gbp"]
            if bal <= 0 or inv["dispute_status"] == "written_off":
                continue
            od = (at - inv["due_date"]).days
            for i, (cap, rate) in enumerate(RATES):
                if od <= cap:
                    b[i] += bal * rate
                    break
        return b
    cur = ecl_buckets(as_of)
    booked = [round(x * 0.62, 2) for x in cur]
    prev = [round(x * 0.55, 2) for x in cur]
    qe = as_of - timedelta(days=91)
    meth = "ECL by ageing bucket on open ledger: 0-30d (incl. not yet due) 2%, 31-60d 5%, 61-90d 15%, 90+ 35%"
    provisions = [
        {"provision_id": "BDP-2026-00001", "as_of_date": qe - timedelta(days=91), "methodology": meth, "amount_gbp": round(sum(prev), 2),
         "by_0_30_days_gbp": prev[0], "by_31_60_days_gbp": prev[1], "by_61_90_days_gbp": prev[2], "by_over_90_days_gbp": prev[3],
         "created_at": _ts(qe - timedelta(days=91), 16)},
        {"provision_id": "BDP-2026-00002", "as_of_date": qe, "methodology": meth, "amount_gbp": round(sum(booked), 2),
         "by_0_30_days_gbp": booked[0], "by_31_60_days_gbp": booked[1], "by_61_90_days_gbp": booked[2], "by_over_90_days_gbp": booked[3],
         "created_at": _ts(qe, 16)},
    ]

    reminders = [{"reminder_id": "DUN-000001", "customer_id": "CUS-000016", "invoice_id": "INV-2026-000903",
                  "reminder_type": "first_notice", "message": "Invoice INV-2026-000903 for GBP 62,400 is overdue. Please arrange payment.",
                  "sent_date": as_of - timedelta(days=40), "status": "sent", "created_at": _ts(as_of - timedelta(days=40), 10)}]

    return {"customer_accounts": accounts, "invoices": invoices, "invoice_lines": lines, "payments": payments,
            "collection_history": history, "credit_insurance": insurance, "bad_debt_provisions": provisions,
            "payment_reminders": reminders}
