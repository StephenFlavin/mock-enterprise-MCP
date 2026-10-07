"""Customer service data: WISMO contacts (missed-scan spike), glass damage claims, zip complaints, data-error contacts."""
from datetime import datetime, timedelta

WISMO_ISSUES = ["Missed scan", "Delayed delivery", "Tracking gap", "No tracking update", "Wrong tracking info"]
# WISMO per day ramps from 5/day (56+ days ago) to 8.5/day (yesterday): last 28 days are ~+30% on the 28 days before.
# Missed-scan share of WISMO ramps from 20% to ~42% and drives most of the rise.
WISMO_DAYS = 84
OTHER_MIX = [0.35, 0.20, 0.15, 0.10]  # delayed, tracking gap, no update, wrong info (share of non-missed-scan)
WEEKDAY_WEIGHT = [1.3, 1.1, 1.0, 1.0, 1.0, 0.8, 0.8]
CHANNELS = ["email", "chat", "phone"]
HANDLING = {"email": 4.2, "chat": 3.1, "phone": 7.8}

# Glass breakage claims: (sku, claims in days 1-30 ago, claims in days 31-60 ago, claims in days 61-90 ago). 14 vs 10 = +40%.
GLASS_ITEMS = [
    ("K-1700", 6, 3, 3),
    ("SKU-104123", 3, 2, 2),
    ("SKU-100532", 2, 2, 1),
    ("SKU-100091", 2, 1, 1),
    ("SKU-104795", 1, 2, 1),
]
GLASS_TYPES = ["Broken glass", "Broken glass", "Broken glass", "Cracked glass"]
OTHER_DAMAGE = ["Torn seams", "Water damage", "Dented packaging", "Crushed carton"]

# Zip strength complaints on trouser style STY-T-4410 (lot LOT-900016 is SKU-100651): (sku, days ago list, safety flags)
ZIP_COMPLAINTS = [
    ("SKU-100651", [78, 66, 52, 41, 33, 24, 17, 11, 7, 4, 2], {7: "slider", 2: "edge"}),
    ("SKU-100637", [70, 45, 21, 9], {9: "pinch"}),
    ("SKU-100644", [58, 26, 13], {}),
    ("SKU-101904", [47, 30, 15], {}),
    ("SKU-101911", [38], {}),
]
ZIP_TEXT = ["Zip broke after a few wears", "Zip slider came off the trousers", "Zip teeth separated on first use",
            "Zip stuck and would not move", "Zip pull snapped off", "Zip burst open when sitting down",
            "Zip failed after one wash", "Fly zip would not stay closed"]
SAFETY_TEXT = {"slider": "Zip slider snapped off with a sharp edge, cut my finger",
               "edge": "Zip burst open and the broken metal edge scratched my child's leg",
               "pinch": "Zip failed and jammed, pinched skin and caused a bleeding cut"}
OTHER_DEFECTS = [("Colour mismatch", "Colour not as shown on the website"), ("Fit issue", "Sizing runs much smaller than the chart"),
                 ("Material quality", "Fabric feels thin and has started pilling"), ("Stitching defect", "Seam came apart at the first wash")]

# Product data errors behind returns and complaints: (category, error type, count in last 90 days, issue text, preferred skus)
DATA_ERRORS = [
    ("Cookware", "compatibility", 34, "Compatibility wrong on listing: pan not suitable for induction hob",
     ["SKU-100805", "SKU-100812", "SKU-100819"]),
    ("Cookware", "dimensions", 16, "Dimensions wrong on listing: pan diameter smaller than stated", []),
    ("Cookware", "materials", 12, "Material not as described: not stainless steel as listed", []),
    ("Bedding", "dimensions", 22, "Dimensions wrong on listing: duvet size smaller than stated", []),
    ("Small Appliances", "compatibility", 14, "Compatibility wrong on listing: plug and voltage not as stated", []),
    ("Lighting", "compatibility", 10, "Compatibility wrong on listing: bulb fitting does not match", []),
    ("Outerwear", "materials", 12, "Material not as described: fabric content differs from listing", []),
    ("Footwear", "dimensions", 9, "Dimensions wrong on listing: size guide inaccurate", []),
]
RESOLUTION_FACTOR = {"compatibility": 0.55, "dimensions": 0.4, "materials": 0.25}


def generate(g):
    r = g.rng
    as_of = g.as_of
    products = g.master("products")
    by_sku = {p["sku"]: p for p in products}
    by_cat = {}
    for p in products:
        by_cat.setdefault(p["category"], []).append(p["sku"])
    apparel = [p["sku"] for p in products if p["category"] in
               ("Trousers", "Dresses", "Shirts", "Blouses", "Tops", "T-Shirts", "Outerwear", "Knitwear")]

    orders_by_date = {}
    for o in g.master("orders"):
        if o["status"] in ("cancelled", "placed", "picking"):
            continue
        orders_by_date.setdefault(o["order_date"], []).append(o["order_id"])

    def pick_order(dt):
        for _ in range(30):
            d = (dt - timedelta(days=r.randint(2, 12))).date().isoformat()
            if orders_by_date.get(d):
                return r.choice(orders_by_date[d])
        return r.choice(orders_by_date[sorted(orders_by_date)[-1]])

    def stamp(days_ago, hour_weights=True):
        d = datetime.combine(as_of - timedelta(days=days_ago), datetime.min.time())
        return d + timedelta(hours=r.randint(7, 21), minutes=r.randint(0, 59))

    contacts, claims, complaints = [], [], []
    n = {"c": 0, "s": 900000}

    def add_contact(dt, reason, issue, sku=None, order_id=None, error=None, cost_extra=0.0, story=False, ctype=None):
        if story:
            n["s"] += 1
            cid = f"CSC-{n['s']:06d}"
        else:
            n["c"] += 1
            cid = f"CSC-{n['c']:06d}"
        ctype = ctype or r.choices(CHANNELS, [0.5, 0.3, 0.2])[0]
        resp = round(r.uniform(0.5, 36), 1)
        age = (as_of - dt.date()).days
        status = "resolved" if age > 6 and r.random() < 0.95 else r.choices(["resolved", "open", "escalated"], [0.6, 0.3, 0.1])[0]
        resolved = dt + timedelta(hours=resp + r.uniform(1, 60)) if status == "resolved" else None
        cost = HANDLING[ctype] * r.uniform(0.85, 1.2) + cost_extra
        contacts.append({
            "contact_id": cid, "contact_date": dt, "order_id": order_id or pick_order(dt), "sku": sku, "reason": reason,
            "issue": issue, "data_error_type": error, "contact_type": ctype, "status": status,
            "response_time_hours": resp, "resolved_at": resolved, "cost_gbp": round(cost, 2)})
        return cid, contacts[-1]["order_id"]

    # ---- WISMO: smooth ramp, weekday-weighted, missed-scan share rising
    carry = 0.0
    acc = [0.0] * len(WISMO_ISSUES)
    for age in range(WISMO_DAYS, 0, -1):
        rate = 5.0 + 3.5 * max(0.0, (56 - age) / 55.0)
        carry += rate * WEEKDAY_WEIGHT[(as_of - timedelta(days=age)).weekday()] / 0.99
        count, carry = int(carry), carry - int(carry)
        ms = 0.20 + 0.22 * max(0.0, (56 - age) / 55.0)
        weights = [ms] + [(1 - ms) * x / sum(OTHER_MIX) for x in OTHER_MIX]
        for _ in range(count):  # stratified (low variance) allocation of issues
            for i, wt in enumerate(weights):
                acc[i] += wt
            k = max(range(len(acc)), key=lambda i: acc[i])
            acc[k] -= 1.0
            add_contact(stamp(age), "wismo", WISMO_ISSUES[k])

    # ---- general background contacts (not WISMO): returns, other
    for _ in range(70):
        add_contact(stamp(r.randint(1, 84)), "return", "Return inquiry")
    for _ in range(45):
        add_contact(stamp(r.randint(1, 84)), "other", r.choice(["Change delivery address", "Account query", "Promo code not applied", "Invoice request"]))

    # ---- damage claims: glass breakage up 40%, flat background of other damage
    def add_claim(days_ago, sku, dtype, story):
        dt = stamp(days_ago)
        p = by_sku[sku]
        cid, oid = add_contact(dt, "damage", "Item arrived damaged", sku=sku, story=story)
        amount = float(p["retail_price_gbp"]) * r.choice([1, 1, 1, 2])
        n["claim"] = n.get("claim", 0) + 1
        claims.append({
            "claim_id": f"CLM-{900000 + n['claim']:06d}" if story else f"CLM-{n['claim']:06d}",
            "order_id": oid, "contact_id": cid, "sku": sku, "item_name": p["name"], "damage_type": dtype,
            "claim_amount_gbp": round(amount, 2), "claim_date": dt,
            "status": "paid" if days_ago > 25 else r.choice(["new", "investigating", "approved", "paid"])})

    for sku, recent, prior, older in GLASS_ITEMS:
        for count, lo, hi in ((recent, 7, 24), (prior, 37, 54), (older, 63, 88)):
            for d in sorted(r.sample(range(lo, hi + 1), count)):
                add_claim(d, sku, r.choice(GLASS_TYPES), True)
    apparel_or_home = [s for s in apparel] + by_cat["Bedding"]
    for _ in range(55):
        add_claim(r.randint(1, 88), r.choice(apparel_or_home), r.choice(OTHER_DAMAGE), False)

    # ---- complaints
    def add_complaint(days_ago, sku, defect, text, severity, safety, story):
        dt = stamp(days_ago)
        cid, oid = add_contact(dt, "complaint", f"Product quality: {defect}", sku=sku, story=story)
        n["cmp"] = n.get("cmp", 0) + 1
        complaints.append({
            "complaint_id": f"CMP-{900000 + n['cmp']:06d}" if story else f"CMP-{n['cmp']:06d}",
            "complaint_date": dt, "order_id": oid, "contact_id": cid, "sku": sku, "defect_type": defect,
            "description": text, "severity": severity, "safety_related": safety,
            "status": "investigating" if days_ago < 30 else r.choice(["investigating", "resolved", "resolved"])})

    for sku, days, flags in ZIP_COMPLAINTS:
        for d in days:
            if d in flags:
                add_complaint(d, sku, "Zip strength", SAFETY_TEXT[flags[d]], "critical" if flags[d] != "pinch" else "high", True, True)
            else:
                add_complaint(d, sku, "Zip strength", r.choice(ZIP_TEXT), r.choice(["high", "high", "medium"]), False, True)
    for _ in range(46):
        defect, text = r.choice(OTHER_DEFECTS)
        add_complaint(r.randint(1, 88), r.choice(apparel), defect, text, r.choice(["low", "low", "medium", "high"]), False, False)

    # ---- product data errors behind returns / complaints
    for cat, error, count, issue, preferred in DATA_ERRORS:
        for _ in range(count):
            sku = r.choice(preferred) if preferred and r.random() < 0.6 else r.choice(by_cat[cat])
            price = float(by_sku[sku]["retail_price_gbp"])
            extra = price * RESOLUTION_FACTOR[error] * r.uniform(0.8, 1.2)
            add_contact(stamp(r.randint(3, 80)), "complaint" if error == "materials" else "return", issue,
                        sku=sku, error=error, cost_extra=extra, story=False)

    rules = []  # seeded in seed/notification_rules.csv
    return {"customer_service_contacts": contacts, "damage_claims": claims, "complaints": complaints,
            "notification_rules": rules}
