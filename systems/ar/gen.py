"""AR system: wholesale customer invoices, payments, credit accounts, collection history.

Accounts are 32 wholesale accounts (master partners with type wholesale: the key accounts PTN-001..PTN-010 used by oms, wholesale_edi and
contracts, plus PTN-025..PTN-047). `wholesale` lists them in the order the generator draws random numbers (do not reorder).
Everything is derived from one invoice/payment list so balances, ageing, history and provisions agree.
Planted stories (days are relative to as_of):
  Q1 PTN-025 "Hartley & Reed Ltd": days-to-pay drifting up, score 58, limit 250k, insurance cover 150k
  Q2 PTN-041: invoice INV-2026-900040 for 480k (8,000 units at 60) disputed, second delivery 360 units short
  Q3 portfolio ledger, ECL above the booked provision
  Q4 ten accounts with overdue balances that grew over the last 60 days; PTN-007 is a big overdue that shrank
  Q5 PTN-032: oldest invoice 75 days overdue, balance over its limit, not yet on hold
"""
from datetime import datetime, timedelta


def generate(g):
    r = g.rng
    A = g.as_of

    def d(n):
        return A - timedelta(days=n)

    products = [p for p in g.master("products")
                if p["status"] == "active" and 15 <= float(p["retail_price_gbp"]) <= 130]
    rich = [p for p in products if float(p["retail_price_gbp"]) >= 55]

    # slot order = the original draw order, so story numbers stay put; ids are the master wholesale partners
    wholesale = [f"PTN-{n:03d}" for n in (3, 6, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 7, 38, 10, 39, 25, 40, 41, 42, 1, 8, 43, 9, 44, 45,
                                          2, 4, 5, 46, 47)]
    rank = {c: i for i, c in enumerate(wholesale)}

    # planted accounts: unpaid invoices as (amount, due_days_ago); negative = not yet due
    P = {
        "PTN-006": dict(limit=300000, score=52, over=[(85000, 75), (62000, 50), (71000, 22)], open=[(38000, -8)], ins=(200000, 90)),
        "PTN-025": dict(limit=250000, score=58, over=[(64000, 40), (58000, 18), (46000, 5)], open=[(22000, -10), (29000, -24)],
                           ins=(150000, 90), drift=24),
        "PTN-009": dict(limit=200000, score=55, over=[(54000, 66), (47000, 35), (38000, 9)], open=[(25000, -15)]),
        "PTN-034": dict(limit=150000, score=49, over=[(44000, 52), (52000, 21), (31000, 6)], open=[(18000, -12)]),
        "PTN-031": dict(limit=150000, score=51, over=[(40000, 64), (36000, 33), (29000, 12)], open=[]),
        "PTN-043": dict(limit=150000, score=60, over=[(61000, 47), (33000, 20)], open=[(20000, -20)]),
        "PTN-002": dict(limit=120000, score=59, over=[(38000, 50), (30000, 20), (22000, 10)], open=[(16000, -14)]),
        "PTN-046": dict(limit=120000, score=57, over=[(35000, 52), (28000, 20), (24000, 8)], open=[(15000, -18)]),
        "PTN-001": dict(limit=120000, score=53, over=[(30000, 61), (26000, 31), (25000, 3)], open=[(12000, -22)]),
        "PTN-032": dict(limit=60000, score=41, over=[(61000, 75), (10000, 34)], open=[], orders=["", "ORD-004880"]),
    }
    TERMS = 30
    DECOY = "PTN-007"      # large overdue 30-60 days ago, paid since
    DISPUTE = "PTN-041"   # the 480k disputed invoice

    invoices, lines, payments = [], [], []
    acct = {}

    def pick_unit(retail):
        return min((25.0, 40.0, 50.0), key=lambda u: abs(u - retail * 0.45))

    def add(cid, age, terms, amount_lines, paid_days_ago=None, frac=1.0, inv_id=None, order_id="",
            dispute="none", reason="", planted=False):
        inv_date = d(age)
        due = inv_date + timedelta(days=terms)
        amount = round(sum(l[3] * l[4] for l in amount_lines), 2)
        paid = 0.0
        if paid_days_ago is not None:
            paid = round(amount * frac, 2)
            status = "paid" if frac >= 1 else "part_paid"
        else:
            status = "open" if due >= A else "overdue"
        inv = dict(invoice_id=inv_id, customer_id=cid, sales_order_ref=order_id, invoice_date=inv_date, due_date=due,
                   amount_gbp=amount, paid_amount_gbp=paid, status=status, dispute_status=dispute,
                   dispute_reason=reason, created_at=datetime.combine(inv_date, datetime.min.time()) + timedelta(hours=10),
                   updated_at=datetime.combine(d(paid_days_ago) if paid_days_ago is not None else inv_date,
                                               datetime.min.time()) + timedelta(hours=10),
                   _lines=amount_lines, _p=planted)
        invoices.append(inv)
        if paid_days_ago is not None:
            pd = d(paid_days_ago)
            payments.append(dict(_pd=pd, customer_id=cid, invoice_id=None, _inv=inv, amount_gbp=paid, payment_date=pd,
                                 received_date=pd + timedelta(days=1 if pd.weekday() < 4 else 0),
                                 payment_method=r.choice(["bank_transfer", "bank_transfer", "bank_transfer", "direct_debit", "cheque"]),
                                 reference="", notes="Part payment" if frac < 1 else ""))
        return inv

    def planted_lines(amount):
        p = r.choice(rich)
        u = pick_unit(float(p["retail_price_gbp"]))
        return [(p["sku"], p["name"], 0, int(amount / u), u)]

    def noise_lines(target):
        out = []
        k = r.choice([1, 1, 2, 3])
        for _ in range(k):
            p = r.choice(products)
            unit = round(float(p["retail_price_gbp"]) * r.uniform(0.38, 0.5), 2)
            qty = max(1, round(target / k / unit))
            out.append((p["sku"], p["name"], 0, qty, unit))
        return out

    # ---- history + planted invoices
    for cid in wholesale:
        pl = P.get(cid)
        if pl:
            terms, score, size, cls = TERMS, pl["score"], 30000, "slowing"
            oldest = max(due + TERMS for _, due in pl["over"])
            stop = oldest + 20
            drift = pl.get("drift", 18)
            limit = pl["limit"]
        elif cid == DECOY:
            terms, score, size, cls, drift = TERMS, 71, 30000, "reliable", 0
            stop, limit = 118, 400000
        elif cid == DISPUTE:
            terms, score, size, cls, drift = TERMS, 78, 40000, "reliable", 0
            stop, limit = 56, 600000
        else:
            terms = r.choice([30, 30, 45, 60])
            cls = r.choices(["reliable", "mixed", "slow"], [0.6, 0.25, 0.15])[0]
            size = r.choice([8000, 12000, 20000, 28000]) if cls != "slow" else r.choice([6000, 9000, 14000])
            score = r.randint(70, 92) if cls == "reliable" else r.randint(62, 76) if cls == "mixed" else r.randint(55, 66)
            limit = r.choice([50000, 100000, 150000, 250000])
            while limit < 4 * size:
                limit *= 2
            stop, drift = 4, 0
        acct[cid] = dict(terms=terms, score=score, limit=limit, ins=pl.get("ins") if pl else None)
        age = r.randint(735, 750)
        while age > stop:
            if cls == "reliable":
                delay = r.randint(-9, 0) if r.random() > 0.06 else r.randint(1, 5)
            elif cls == "mixed":
                delay = r.randint(-6, 9)
            elif cls == "slow":
                delay = r.randint(2, 18)
            else:
                delay = r.randint(-8, 0) if r.random() > 0.08 else r.randint(1, 4)
            delay += int(drift * max(0.0, 1 - age / 360.0))
            amt = size * r.uniform(0.6, 1.5)
            pay_ago = age - terms - delay
            paid_ago = pay_ago if pay_ago >= 0 else None
            if paid_ago is None and age - terms < 0:  # not yet due and unpaid: fine
                pass
            dsp, rsn = "none", ""
            if paid_ago is not None and r.random() < 0.015:
                dsp, rsn = "resolved", r.choice(["Pricing discrepancy", "Wrong delivery", "Quantity mismatch"])
            add(cid, age, terms, noise_lines(amt), paid_ago, dispute=dsp, reason=rsn)
            age -= r.randint(14, 28)
        if pl:
            for k, (amt, due) in enumerate(pl["over"]):
                oid = pl.get("orders", [""] * 9)[k] if "orders" in pl else ""
                add(cid, due + TERMS, TERMS, planted_lines(amt), None, order_id=oid, planted=True)
            for amt, due in pl["open"]:
                add(cid, due + TERMS, TERMS, planted_lines(amt), None, planted=True)
        if cid == DECOY:
            for amt, due, paid_ago in [(120000, 80, 21), (90000, 66, 14)]:
                add(cid, due + TERMS, TERMS, planted_lines(amt), paid_ago, planted=True)
            add(cid, 6 + TERMS, TERMS, planted_lines(12000), None, planted=True)
            for amt, due in [(30000, -12), (26000, -25)]:
                add(cid, due + TERMS, TERMS, planted_lines(amt), None, planted=True)
        if cid == DISPUTE:
            add(cid, 24, 30, [("SKU-100448", "Denim Blouse 10", 0, 4000, 60.0), ("SKU-100455", "Denim Blouse 12", 0, 4000, 60.0)],
                None, inv_id="INV-2026-900040", order_id="ORD-900040", dispute="disputed",
                reason="Customer withholding payment: second delivery of 3,000 units signed for 2,640 only (360 damaged or missing)")
            add(cid, 55, 30, noise_lines(36000), 20)
            add(cid, 18, 30, noise_lines(28000), None)

    # ---- ids and child rows
    invoices.sort(key=lambda i: (i["invoice_date"], rank[i["customer_id"]]))
    n = 0
    p_n = 900100
    for inv in invoices:
        if not inv["invoice_id"]:
            if inv["_p"]:
                p_n += 1
                inv["invoice_id"] = f"INV-{inv['invoice_date'].year}-{p_n:06d}"
            else:
                n += 1
                inv["invoice_id"] = f"INV-{inv['invoice_date'].year}-{n:06d}"
    for inv in invoices:
        inv.pop("_p")
        for k, (sku, desc, _, qty, unit) in enumerate(inv.pop("_lines"), 1):
            lines.append(dict(invoice_id=inv["invoice_id"], line_no=k, sku=sku, description=desc, qty=qty,
                              unit_price_gbp=unit, line_total_gbp=round(qty * unit, 2)))
    for p in payments:
        p["invoice_id"] = p.pop("_inv")["invoice_id"]
    by_id = {i["invoice_id"]: i for i in invoices}
    payments.sort(key=lambda p: (p["payment_date"], rank[p["customer_id"]]))
    cnt = {}
    for p in payments:
        y = p["payment_date"].year
        cnt[y] = cnt.get(y, 0) + 1
        p["payment_id"] = f"PAY-{y}-{cnt[y]:06d}"
        p["reference"] = f"BACS-{p['payment_date']:%Y%m%d}-{r.randint(1000, 9999)}"
        p.pop("_pd")

    # ---- accounts
    inv_of = {}
    for inv in invoices:
        inv_of.setdefault(inv["customer_id"], []).append(inv)
    pay_of = {}
    for p in payments:
        pay_of.setdefault(p["customer_id"], []).append(p)
    accounts = []
    for cid in wholesale:
        a = acct[cid]
        bal = sum(i["amount_gbp"] - i["paid_amount_gbp"] for i in inv_of.get(cid, [])
                  if i["status"] in ("open", "overdue", "part_paid"))
        dtp = [(p["payment_date"] - by_id[p["invoice_id"]]["invoice_date"]).days for p in pay_of.get(cid, [])
               if p["payment_date"] >= d(180)]
        s = a["score"]
        accounts.append(dict(
            customer_id=cid, credit_limit_gbp=a["limit"], credit_held=False, credit_hold_reason="",
            current_balance_gbp=round(bal, 2), payment_terms_days=a["terms"], credit_score=s,
            account_status="active",
            risk_rating="critical" if s < 50 else "high" if s < 65 else "medium" if s < 80 else "low",
            average_dpo_days=round(sum(dtp) / len(dtp), 1) if dtp else a["terms"],
            updated_at=datetime.combine(A, datetime.min.time()) + timedelta(hours=9)))

    # ---- collection history: 4-week windows over 24 months, from real payments
    history = []
    for cid in wholesale:
        for k in range(0, 26):
            end = d(28 * k)
            start = end - timedelta(days=27)
            ps = [p for p in pay_of.get(cid, []) if start <= p["payment_date"] <= end]
            if not ps:
                continue
            invs = [by_id[p["invoice_id"]] for p in ps]
            ontime = sum(1 for p, i in zip(ps, invs) if p["payment_date"] <= i["due_date"])
            history.append(dict(
                customer_id=cid, recorded_on=end, invoices_in_period=len(ps),
                amount_invoiced_gbp=round(sum(i["amount_gbp"] for i in invs), 2),
                amount_paid_gbp=round(sum(p["amount_gbp"] for p in ps), 2),
                days_to_pay_avg=round(sum((p["payment_date"] - i["invoice_date"]).days for p, i in zip(ps, invs)) / len(ps), 1),
                on_time_pct=round(100.0 * ontime / len(ps), 1), notes=""))

    # ---- credit insurance
    insurance = []
    insured = {cid: a["ins"] for cid, a in acct.items() if a["ins"]}
    noise = [c for c in wholesale if c not in P and c not in (DECOY, DISPUTE)]
    for cid in r.sample(noise, 6):
        insured[cid] = (r.choice([50000, 100000, 200000]), r.choice([80, 90, 95]))
    for k, (cid, (cover, pct)) in enumerate(sorted(insured.items(), key=lambda kv: rank[kv[0]]), 1):
        start = d(r.randint(120, 330))
        if cid == "PTN-025":
            start, end = d(300), d(-70)
        else:
            end = start + timedelta(days=365)
        insurance.append(dict(
            policy_id=f"INS-{k:05d}", customer_id=cid,
            insurer="Atradius" if cid == "PTN-025" else r.choice(["Atradius", "Coface", "AXA Credit Insurance", "Zurich"]),
            cover_limit_gbp=cover, cover_percentage_pct=pct, policy_start=start, policy_end=end, status="active",
            updated_at=datetime.combine(A, datetime.min.time()) + timedelta(hours=9)))

    # ---- bad debt provision: booked a month ago, below today's expected credit loss
    def ecl_buckets(at):
        out = [0.0, 0.0, 0.0, 0.0]
        for i in invoices:
            if i["invoice_date"] > at or i["status"] == "written_off":
                continue
            paid = sum(p["amount_gbp"] for p in pay_of.get(i["customer_id"], [])
                       if p["invoice_id"] == i["invoice_id"] and p["payment_date"] <= at)
            bal = i["amount_gbp"] - paid
            if bal <= 0:
                continue
            dpd = (at - i["due_date"]).days
            b = 0 if dpd <= 30 else 1 if dpd <= 60 else 2 if dpd <= 90 else 3
            out[b] += bal * (0.02, 0.05, 0.15, 0.35)[b]
        return out

    provisions = []
    for k, (back, frac) in enumerate([(32, 0.62), (63, 0.55), (94, 0.5)]):
        at = d(back)
        e = ecl_buckets(at)
        bk = [round(x * frac, -2) for x in e]
        provisions.append(dict(
            provision_id=f"BDP-{at.year}-{900003 - k:05d}", as_of_date=at,
            methodology="ECL by ageing bucket: 0-30d=2%, 31-60d=5%, 61-90d=15%, 90+=35%, booked at "
                        f"{int(frac * 100)}% of modelled loss (management overlay pending)",
            amount_gbp=sum(bk), by_0_30_days_gbp=bk[0], by_31_60_days_gbp=bk[1], by_61_90_days_gbp=bk[2],
            by_over_90_days_gbp=bk[3], created_at=datetime.combine(at, datetime.min.time()) + timedelta(hours=16, minutes=30)))

    # ---- earlier chasers on the planted overdue invoices
    reminders = []
    rn = 0
    kinds = ["first_notice", "second_notice", "final_notice"]
    for cid, pl in P.items():
        for k, (amt, due) in enumerate(pl["over"]):
            inv = next(i for i in inv_of[cid] if i["due_date"] == d(due) and i["amount_gbp"] == float(amt))
            for j, kind in enumerate(kinds):
                sent_ago = due - 7 - 21 * j
                if sent_ago < 1 or (j and due < 30):
                    continue
                rn += 1
                sd = d(sent_ago)
                reminders.append(dict(
                    reminder_id=f"DUN-2026-{rn:06d}", customer_id=cid, invoice_id=inv["invoice_id"], reminder_type=kind,
                    message="",
                    sent_date=sd, status="sent" if j == 0 else "acknowledged",
                    created_at=datetime.combine(sd, datetime.min.time()) + timedelta(hours=9)))
    for rem in reminders:
        inv = by_id[rem["invoice_id"]]
        days = (rem["sent_date"] - inv["due_date"]).days
        rem["message"] = (f"Invoice {inv['invoice_id']} for £{inv['amount_gbp']:,.0f} was due on {inv['due_date']:%d %B %Y} "
                          f"and is {days} days overdue. Please arrange payment.")

    for inv in invoices:
        if not inv["dispute_reason"]:
            inv["dispute_reason"] = ""
    return {
        "customer_accounts": accounts, "invoices": invoices, "invoice_lines": lines, "payments": payments,
        "collection_history": history, "credit_insurance": insurance, "bad_debt_provisions": provisions,
        "payment_reminders": reminders,
    }
