"""Order Management System: orders, allocations and shipments for all channels.

Everything is built through one Builder so that the tables always agree: order totals are the sum of their
lines, shipment lines add up to line quantities, batch_sales are the sum of shipment lines.
Background volume: ~90 days of store replenishment and online orders, 26 weeks of key-account wholesale orders.
Story orders (ids ORD-9000xx) are planted by `plant_stories`; background ids are ORD-0xxxxx.
"""
from datetime import date, datetime, timedelta

STORY_SKUS = {"PF-220", "K-1700", "SKU-100035", "SKU-100007", "SKU-100014", "SKU-100021",
              "SKU-100448", "SKU-100455", "SKU-100028"}
HOT = "K-1700"

# local DC for a destination region (mirrors seed/dc_catchments.csv)
LOCAL = {"store": {"UK South": "DC1", "UK Midlands": "DC1", "UK North": "DC3", "Scotland": "DC3", "Ireland": "DC1",
                   "IE": "DC1", "EU Central": "DC4", "DE": "DC4", "NL": "DC4", "FR": "DC4", "US": "DC5"}}
LOCAL["wholesale"] = LOCAL["store"]
LOCAL["online"] = {**{r: "DC2" for r in ("UK South", "UK Midlands", "UK North", "Scotland", "Ireland", "IE")},
                   "EU Central": "DC4", "DE": "DC4", "NL": "DC4", "FR": "DC4", "US": "DC5"}

ONLINE_HOURS = [1, 1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 10, 8, 7, 6, 6, 7, 9, 11, 12, 10, 6, 3]
STORE_HOURS = [0] * 5 + [2, 8, 12, 12, 10, 6, 3, 2, 1] + [0] * 10
WHOLESALE_HOURS = [0] * 8 + [4, 8, 9, 8, 6, 7, 8, 7, 5, 3] + [0] * 6

# key wholesale accounts: orders per week (older 13 weeks, recent 13 weeks), share of lines short, share short
ACCOUNTS = {
    "CUS-000010": dict(older=1.6, recent=0.7, short_p=0.40, short_frac=0.30),   # worst fill, cutting orders
    "CUS-000022": dict(older=1.4, recent=1.5, short_p=0.04, short_frac=0.15),
    "CUS-000024": dict(older=1.2, recent=1.4, short_p=0.12, short_frac=0.20),
    "CUS-000026": dict(older=1.5, recent=1.0, short_p=0.22, short_frac=0.25),   # slipping
    "CUS-000031": dict(older=1.0, recent=1.2, short_p=0.15, short_frac=0.25),
    "CUS-000033": dict(older=1.3, recent=1.3, short_p=0.30, short_frac=0.28),
}

# weekly late rate of store orders by due-week (0 = current week). Falls from 98.5% to 95%.
LATE_RATE = {0: 3.7, 1: 3.5, 2: 3.4, 3: 2.3}
LATE_BASE = 1.5


def generate(g):
    r = g.rng
    b = Builder(g)
    products = [p for p in g.master("products") if p["status"] in ("active", "new")]
    pool = [p for p in products if p["sku"] not in STORY_SKUS]
    b.retail = {p["sku"]: float(p["retail_price_gbp"]) for p in g.master("products")}
    customers = {c["customer_id"]: c for c in g.master("customers")}
    b.cust = customers
    sites = [s for s in g.master("sites") if s["type"] == "store" and s["country"] == "GB"]
    b.sites = {s["site_id"]: s for s in g.master("sites")}
    online_pool = [c for c in customers.values() if int(c["customer_id"][4:]) >= 100]
    b.pool, b.sites_gb, b.online_pool = pool, sites, online_pool

    background_store(b)
    background_online(b)
    background_wholesale(b)
    plant_stories(b)
    return b.tables()


class Builder:
    def __init__(self, g):
        self.g, self.r = g, g.rng
        self.as_of = g.as_of
        self.orders, self.lines, self.decisions, self.ships, self.ship_lines = [], [], [], [], []
        self.n_order = self.n_ship = self.n_dec = 0
        self.rules = {"store": "AR-900101", "online": "AR-900101", "wholesale": "AR-900101"}

    # ---- helpers
    def batch(self, sku):
        return f"BATCH-{sku.replace('SKU-', '')}-{'A' if self.r.random() < 0.6 else 'B'}"

    def line(self, sku, qty, price=None, channel="store", batch=None, **kw):
        if price is None:
            price = round(self.retail[sku] * (1.0 if channel == "online" else 0.6), 2)
        return dict(sku=sku, qty=qty, price=price, batch=batch or self.batch(sku), **kw)

    def pick_lines(self, channel, qty_lo, qty_hi, n_lines=None, hot_p=0.0):
        n = n_lines or self.r.choice([1, 1, 2, 3])
        skus = [p["sku"] for p in self.r.sample(self.pool, n)]
        lines = [self.line(s, self.r.randint(qty_lo, qty_hi), channel=channel) for s in skus]
        if hot_p and self.r.random() < hot_p:
            q = self.r.randint(12, 36) if channel != "online" else self.r.randint(1, 3)
            lines.append(self.line(HOT, q, channel=channel))
        return lines

    def region(self, channel, site=None, customer=None):
        if site:
            return self.sites[site]["region"]
        return self.cust[customer]["region"]

    def country(self, site=None, customer=None):
        return self.sites[site]["country"] if site else self.cust[customer]["country"]

    # ---- the one place rows are made
    def add(self, *, oid=None, channel, customer="", site="", odt, lines, dc, due, status="allocated",
            shipments=None, priority="normal", hold=("none", ""), cross_reason="", alt_dc=None, oversold=None,
            cancelled=False):
        """shipments: list of dict(date, deliver(date|None), dc (opt), lines={idx: qty}, received (opt), signed (opt),
        reason (split reason, if more than one shipment)). Quantities per line must add up to qty shipped."""
        r = self.r
        if oid is None:
            self.n_order += 1
            oid = f"ORD-{self.n_order:06d}"
        shipments = shipments or []
        country = self.country(site or None, customer or None)
        oversold = oversold or {}
        shipped = {i: 0 for i in range(len(lines))}
        for s in shipments:
            for i, q in s["lines"].items():
                shipped[i] += q
        units = sum(l["qty"] for l in lines)
        value = round(sum(l["qty"] * l["price"] for l in lines), 2)
        if cancelled:
            ostatus = "cancelled"
        elif shipments:
            ostatus = "delivered" if all(s["deliver"] for s in shipments) else "shipped"
        else:
            ostatus = status
        for i, l in enumerate(lines):
            alloc = 0 if cancelled else l.get("alloc", l["qty"])
            alloc = max(alloc, shipped[i])
            l["alloc"] = alloc
            if cancelled:
                lst = "cancelled"
            elif shipped[i] > 0:
                lst = "shipped"
            elif alloc > 0:
                lst = "picked" if ostatus == "picked" else "allocated"
            else:
                lst = "pending"
            line_dc = l.get("dc") or dc
            self.lines.append(dict(order_id=oid, line_no=i + 1, sku=l["sku"], qty_ordered=l["qty"], qty_allocated=alloc,
                                   qty_shipped=shipped[i], unit_price_gbp=l["price"],
                                   allocation_source=line_dc if alloc > 0 else "", batch_id=l["batch"], status=lst))
            if alloc > 0 or i in oversold or cancelled and l.get("oversold"):
                self.n_dec += 1
                aisle = r.choice("ABCD")
                short = alloc < l["qty"]
                self.decisions.append(dict(
                    decision_id=f"AD-{self.n_dec:06d}", order_id=oid, line_no=i + 1, sku=l["sku"], qty_requested=l["qty"],
                    qty_allocated=alloc, source_dc=line_dc if alloc > 0 else "",
                    source_location=f"{line_dc}-{aisle}-{r.randint(1, 20):02d}-{r.randint(1, 4):02d}" if alloc > 0 else "",
                    batch_id=l["batch"], rule_id=l.get("rule") or self.rules[channel], oversold=short,
                    cross_ship_reason=cross_reason if (alloc > 0 and line_dc != LOCAL[channel].get(
                        self.region(channel, site or None, customer or None))) else "",
                    decided_at=odt + timedelta(minutes=r.randint(10, 90))))
        last = odt
        split = len(shipments) > 1
        for s in shipments:
            self.n_ship += 1
            sid = f"SHP-{self.n_ship:06d}"
            sdate = s["date"]
            sunits = sum(s["lines"].values())
            at = datetime.combine(sdate, datetime.min.time()) + timedelta(hours=r.randint(6, 18))
            last = max(last, at)
            deliver = s["deliver"]
            self.ships.append(dict(
                shipment_id=sid, order_id=oid, channel=channel, customer_id=customer, delivery_notes=f"DN-{self.n_ship:06d}",
                shipped_date=sdate, shipped_at=at, delivered_date=deliver or "", total_units=sunits, is_split=split,
                split_reason=s.get("reason", "") if split else "", status="delivered" if deliver else "in_transit",
                units_received=(s.get("received", sunits) if deliver else ""),
                pod_signed_by=(s.get("signed") or ("Store goods-in" if channel == "store" else
                                                   self.g.fake.name())) if deliver and channel != "online" else
                ("Left with neighbour/at door" if deliver else "")))
            for k, (i, q) in enumerate(sorted(s["lines"].items()), 1):
                if q <= 0:
                    continue
                self.ship_lines.append(dict(shipment_id=sid, line_no=k, order_line_no=i + 1, sku=lines[i]["sku"],
                                            qty_shipped=q, batch_id=lines[i]["batch"], country=country))
        self.orders.append(dict(
            order_id=oid, customer_id=customer, site_id=site, channel=channel, status=ostatus, order_date=odt.date(),
            order_time=odt, due_date=due, fulfil_dc=dc, hold_status=hold[0], hold_reason=hold[1], priority=priority,
            total_units=units, total_gbp=value, created_at=odt, updated_at=last + timedelta(minutes=r.randint(5, 600))))
        return oid

    def tables(self):
        agg = {}
        chan = {s["shipment_id"]: s for s in self.ships}
        for sl in self.ship_lines:
            s = chan[sl["shipment_id"]]
            k = (sl["batch_id"], s["channel"], sl["country"])
            a = agg.setdefault(k, dict(batch_id=sl["batch_id"], sku=sl["sku"], channel=s["channel"],
                                       country=sl["country"], units_sold=0, shipped_date=s["shipped_date"]))
            a["units_sold"] += sl["qty_shipped"]
            a["shipped_date"] = max(a["shipped_date"], s["shipped_date"])
        return {"orders": self.orders, "order_lines": self.lines, "allocation_decisions": self.decisions,
                "shipments": self.ships, "shipment_lines": self.ship_lines, "batch_sales": list(agg.values()),
                "allocation_rules": [], "dc_catchments": []}

    # ---- shipping plans
    def plan(self, lines, odate, delay=(1, 2), transit=(1, 2), split=None, due=None, late=0, dc=None, alt_dc=None,
             gap=(2, 3)):
        """Build the shipment list for an order placed on odate. late>0 = days delivered after due. Dates after as_of
        are not shipped/delivered yet. split = reason or None."""
        r = self.r
        sd = odate + timedelta(days=r.randint(*delay) if late == 0 else 3)
        dd = sd + timedelta(days=r.randint(*transit)) if late == 0 else due + timedelta(days=late)
        n = len(lines)
        if split and (n >= 2 or lines[0]["qty"] >= 2):
            if split == "location" and n >= 2:
                first = {0: lines[0]["qty"]}
                second = {i: lines[i]["qty"] for i in range(1, n)}
                for i in second:
                    lines[i]["dc"] = alt_dc
            elif n >= 2 and split != "stock":
                half = max(1, n // 2)
                first = {i: lines[i]["qty"] for i in range(half)}
                second = {i: lines[i]["qty"] for i in range(half, n)}
            else:
                first = {i: max(1, round(l["qty"] * 0.6)) if l["qty"] > 1 else l["qty"] for i, l in enumerate(lines)}
                second = {i: l["qty"] - first[i] for i, l in enumerate(lines) if l["qty"] - first[i] > 0}
                if not second:
                    first[0] = max(1, lines[0]["qty"] - 1)
                    second = {0: lines[0]["qty"] - first[0]}
            gap = r.randint(*gap)
            plan = [dict(date=sd, deliver=dd, lines=first, reason=split),
                    dict(date=sd + timedelta(days=gap), deliver=dd + timedelta(days=gap), lines=second, reason=split)]
        else:
            plan = [dict(date=sd, deliver=dd, lines={i: l["qty"] for i, l in enumerate(lines)})]
        for s in plan:
            if s["date"] > self.as_of:
                return []
            if s["deliver"] and s["deliver"] > self.as_of:
                s["deliver"] = None
        return plan


def monday(d):
    return d - timedelta(days=d.weekday())


def at(b, d, weights):
    h = b.r.choices(range(24), weights=weights)[0]
    return datetime.combine(d, datetime.min.time()) + timedelta(hours=h, minutes=b.r.randint(0, 59))


def other_dc(b, local):
    return b.r.choice([d for d in ("DC1", "DC2", "DC3") if d != local])


def background_store(b):
    """Store replenishment orders, 90 days. The late share rises over the last four weeks, driven by North-store
    orders fulfilled from DC1 (stock not at Leeds) since three weeks ago."""
    r, as_of = b.r, b.as_of
    planned = []
    for age in range(90, -1, -1):
        d = as_of - timedelta(days=age)
        hot_p = min(0.10, 0.04 + 0.01 * max(0, 5 - age // 7))
        for _ in range(r.randint(26, 34)):
            site = r.choice(b.sites_gb)["site_id"]
            region = b.sites[site]["region"]
            local = LOCAL["store"][region]
            dc, reason, story = local, "", False
            if region == "UK North" and age <= 21 and r.random() < 0.5:
                dc, reason, story = "DC1", "stock_not_at_local_dc", True
            elif r.random() < 0.035:
                dc = other_dc(b, local)
                reason = "local_dc_capacity" if r.random() < 0.7 else "stock_not_at_local_dc"
            lines = b.pick_lines("store", 6, 48, hot_p=hot_p)
            planned.append(dict(site=site, d=d, age=age, dc=dc, reason=reason, story=story, lines=lines,
                                due=d + timedelta(days=4), late=False))
    weeks = {}
    for p in planned:
        if p["due"] <= as_of:
            weeks.setdefault((monday(as_of) - monday(p["due"])).days // 7, []).append(p)
    for k, items in weeks.items():
        rate = LATE_RATE.get(k, LATE_BASE)
        n_late = round(len(items) * rate / 100)
        cand = [p for p in items if p["story"]] if k <= 3 else []
        r.shuffle(cand)
        chosen = cand[: round(n_late * 0.85)]
        rest = [p for p in items if p not in chosen]
        r.shuffle(rest)
        chosen += rest[: n_late - len(chosen)]
        for p in chosen:
            p["late"] = True
    for p in planned:
        odt = at(b, p["d"], STORE_HOURS)
        late_days = r.randint(1, 3) if p["late"] else 0
        stuck = p["late"] and p["age"] <= 8 and r.random() < 0.35      # late and still not delivered
        split = None
        if not p["late"] and r.random() < 0.03:
            split = r.choice(["stock", "location", "wave", "wave", "other"])
        alt = other_dc(b, p["dc"])
        shipments = [] if stuck else b.plan(p["lines"], p["d"], delay=(1, 1) if split else (1, 2),
                                            transit=(1, 1) if split else (1, 2), split=split, due=p["due"],
                                            late=late_days, alt_dc=alt, gap=(1, 1))
        if split == "location" and shipments:
            p["reason"] = p["reason"] or "stock_not_at_local_dc"
        status = "allocated" if p["age"] == 0 else "picked"
        b.add(channel="store", site=p["site"], odt=odt, lines=p["lines"], dc=p["dc"], due=p["due"], status=status,
              shipments=shipments, cross_reason=p["reason"] or ("local_dc_capacity" if split == "location" else ""))


def background_online(b):
    """Online orders, 90 days. Split rate climbs from 4% to 11%; stock-caused splits (K-1700 online cap) dominate
    lately. Oversells climb in the last two weeks (website stock feed lag)."""
    r, as_of = b.r, b.as_of
    for age in range(90, -1, -1):
        d = as_of - timedelta(days=age)
        split_p = 0.04 if age > 42 else 0.06 if age > 28 else 0.085 if age > 14 else 0.11
        stock_share = 0.25 if age > 42 else 0.55
        oversell_per_day = 0.3 if age > 30 else 1.0 if age > 14 else 3.0
        hot_p = min(0.16, 0.03 + 0.03 * max(0, 5 - age // 7))
        for _ in range(r.randint(18, 24)):
            cust = r.choice(b.online_pool)
            cid = cust["customer_id"]
            region = cust["region"]
            local = LOCAL["online"][region]
            odt = at(b, d, ONLINE_HOURS)
            dc, reason = local, ""
            if r.random() < 0.025 and local in ("DC1", "DC2", "DC3"):
                dc, reason = other_dc(b, local), "local_dc_capacity"
            do_split = r.random() < split_p
            cause = None
            if do_split:
                cause = r.choices(["stock", "location", "wave", "carrier"],
                                  [stock_share, (1 - stock_share) * 0.5, (1 - stock_share) * 0.3,
                                   (1 - stock_share) * 0.2])[0]
            lines = b.pick_lines("online", 1, 3, hot_p=hot_p)
            if do_split and cause == "stock" and age <= 42 and r.random() < 0.6 and not any(l["sku"] == HOT for l in lines):
                lines.append(b.line(HOT, r.randint(2, 4), channel="online"))
            if do_split and cause == "location" and len(lines) < 2:
                lines.append(b.line(r.choice(b.pool)["sku"], 1, channel="online"))
            if do_split and sum(l["qty"] for l in lines) < 2:
                lines[0]["qty"] = 2
            oversold = {}
            cancelled = False
            if r.random() < oversell_per_day / 20 and not do_split:
                i = r.randrange(len(lines))
                lines[i]["alloc"] = max(0, lines[i]["qty"] - r.randint(1, max(1, lines[i]["qty"])))
                oversold = {i: True}
                if len(lines) == 1 and r.random() < 0.45:
                    cancelled = True
                    lines[i]["oversold"] = True
            alt = other_dc(b, dc) if dc in ("DC1", "DC2", "DC3") else dc
            due = d + timedelta(days=3)
            shipments = []
            if not cancelled and age >= 1:
                for l in lines:
                    l["_q"] = l["qty"]
                shp_lines = [dict(l, qty=l.get("alloc", l["qty"])) for l in lines]
                shipments = b.plan(shp_lines, d, delay=(0, 1), transit=(1, 3), split=cause, due=due, alt_dc=alt)
                for l, s in zip(lines, shp_lines):
                    if "dc" in s:
                        l["dc"] = s["dc"]
            if cause == "location":
                reason = reason or "stock_not_at_local_dc"
            b.add(channel="online", customer=cid, odt=odt, lines=lines, dc=dc, due=due,
                  status="allocated" if age == 0 else "picked", shipments=shipments, cross_reason=reason,
                  oversold=oversold, cancelled=cancelled)


def background_wholesale(b):
    """Key-account wholesale orders: 26 weeks. Fill differs by account; some accounts are cutting orders."""
    r, as_of = b.r, b.as_of
    for cid, a in ACCOUNTS.items():
        cust = b.cust[cid]
        local = LOCAL["wholesale"][cust["region"]]
        for age_w in range(25, -1, -1):
            rate = a["recent"] if age_w < 13 else a["older"]
            n = int(rate) + (1 if r.random() < rate - int(rate) else 0)
            for _ in range(n):
                d = as_of - timedelta(days=age_w * 7 + r.randint(0, 6))
                if d > as_of:
                    continue
                age = (as_of - d).days
                odt = at(b, d, WHOLESALE_HOURS)
                lines = b.pick_lines("wholesale", 60, 400, n_lines=r.choice([2, 3]), hot_p=0.2)
                for l in lines:
                    if l["sku"] == HOT:
                        l["qty"] = r.randint(100, 300)
                    if r.random() < a["short_p"]:
                        l["short"] = max(1, round(l["qty"] * r.uniform(a["short_frac"] * 0.5, a["short_frac"] * 1.5)))
                due = d + timedelta(days=7)
                dc, reason = local, ""
                if r.random() < 0.06:
                    dc, reason = other_dc(b, local), "local_dc_capacity"
                for l in lines:
                    l["alloc"] = l["qty"] - l.get("short", 0)
                if age >= 6:
                    split = "location" if r.random() < 0.10 else None
                    shp = [dict(l, qty=l["alloc"]) for l in lines]
                    shipments = b.plan(shp, d, delay=(1, 3), transit=(1, 3), split=split, due=due,
                                       alt_dc=other_dc(b, dc))
                    for l, s in zip(lines, shp):
                        if "dc" in s:
                            l["dc"] = s["dc"]
                    status = "allocated"
                else:
                    shipments = []
                    status = "open" if age <= 2 else "allocated"
                    if status == "open":
                        for l in lines:
                            l.pop("alloc", None)
                b.add(channel="wholesale", customer=cid, odt=odt, lines=lines, dc=dc, due=due, status=status,
                      shipments=shipments, cross_reason=reason)


def ship(sd, dd, lines, **kw):
    return dict(date=sd, deliver=dd, lines=lines, **kw)


def plant_stories(b):
    """Named stories. Dates are relative to as_of (all shift to today at runtime)."""
    r, as_of = b.r, b.as_of
    D = lambda n: as_of - timedelta(days=n)
    T = lambda n, h=9, m=0: datetime.combine(D(n), datetime.min.time()) + timedelta(hours=h, minutes=m)

    # --- 01:6:Q5 late store orders still waiting, North stores served from DC1 (ids used by write cases)
    for n, (oid, site) in enumerate([("ORD-900001", "ST159"), ("ORD-900002", "ST150"), ("ORD-900003", "ST183")]):
        b.add(oid=oid, channel="store", site=site, odt=T(6 + n, 7, 30), lines=[b.line("SKU-100469", 24), b.line("SKU-100476", 18)],
              dc="DC1", due=D(2 + n), status="picked", cross_reason="stock_not_at_local_dc")

    # --- 05:47:Q1 / Q2 portable fan PF-220: affected batch A, other batch B
    A, B_ = "BATCH-PF220-2509-A", "BATCH-PF220-2508-B"
    stores = [s["site_id"] for s in b.sites_gb if s["region"] in ("UK South", "UK Midlands", "UK North")][:10]
    spec = [  # (batch, channel, customer/site, qty, days ago shipped)
        (A, "store", stores[0], 120, 34), (A, "store", stores[1], 120, 30), (A, "store", stores[2], 120, 27),
        (A, "store", stores[3], 120, 20), (A, "store", stores[4], 120, 13), (A, "store", stores[5], 120, 7),
        (B_, "store", stores[6], 100, 52), (B_, "store", stores[7], 100, 45), (B_, "store", stores[8], 100, 38),
        (B_, "store", stores[9], 100, 31),
        (A, "wholesale", "CUS-000015", 200, 25), (A, "wholesale", "CUS-000018", 300, 22),
        (A, "wholesale", "CUS-000007", 150, 15), (B_, "wholesale", "CUS-000032", 250, 40),
    ]
    for batch, ch, who, qty, ago in spec:
        site, cust = (who, "") if ch == "store" else ("", who)
        region = b.region(ch, site or None, cust or None)
        dc = LOCAL[ch][region]
        od = D(ago + 3)
        b.add(channel=ch, site=site, customer=cust, odt=datetime.combine(od, datetime.min.time()) + timedelta(hours=9),
              lines=[b.line("PF-220", qty, channel=ch, batch=batch, rule="AR-900004")], dc=dc, due=od + timedelta(days=7),
              shipments=[ship(D(ago), D(ago - 2), {0: qty})])
    online_a = [(D(a), c) for a, c in [(30, "CUS-000134"), (26, "CUS-000175"), (24, "CUS-000063"), (21, "CUS-000066"),
                                       (18, "CUS-000046"), (14, "CUS-000073"), (11, "CUS-000134"), (9, "CUS-000175"),
                                       (6, "CUS-000063")]]
    for k, (d, c) in enumerate(online_a):
        q = 1 + k % 3
        batch = A if k % 4 != 3 else B_
        dc = LOCAL["online"][b.cust[c]["region"]]
        b.add(channel="online", customer=c, odt=datetime.combine(d - timedelta(days=1), datetime.min.time()) + timedelta(hours=20),
              lines=[b.line("PF-220", q, channel="online", batch=batch, rule="AR-900004")], dc=dc, due=d + timedelta(days=3),
              shipments=[ship(d, d + timedelta(days=2), {0: q})])

    # --- 05:42:Q1 blush blouse, seven failing dye lots (SKU sizes 10/12/14); some stock still unshipped
    lots = [("BATCH-POL-PINK-001", "SKU-100007", 700, 700, 45), ("BATCH-POL-PINK-002", "SKU-100014", 650, 650, 38),
            ("BATCH-POL-PINK-003", "SKU-100021", 500, 500, 32), ("BATCH-POL-PINK-004", "SKU-100007", 800, 560, 25),
            ("BATCH-POL-PINK-005", "SKU-100014", 600, 420, 19), ("BATCH-POL-PINK-006", "SKU-100021", 450, 150, 12),
            ("BATCH-POL-PINK-007", "SKU-100007", 500, 0, 6)]
    for batch, sku, alloc_total, shipped, ago in lots:
        w_ship = int(shipped * 0.6)
        parts = [("wholesale", "CUS-000039", w_ship, True), ("store", stores[1], shipped - w_ship, True),
                 ("wholesale", "CUS-000039", alloc_total - shipped, False)]
        for ch, who, qty, is_shipped in parts:
            if qty <= 0:
                continue
            site, cust = (who, "") if ch == "store" else ("", who)
            region = b.region(ch, site or None, cust or None)
            od = D(ago + 2) if is_shipped else D(min(ago, 5))
            ships = [ship(D(ago), D(ago - 2), {0: qty})] if is_shipped else []
            b.add(channel=ch, site=site, customer=cust, odt=datetime.combine(od, datetime.min.time()) + timedelta(hours=10),
                  lines=[b.line(sku, qty, channel=ch, batch=batch)], dc=LOCAL[ch][region], due=od + timedelta(days=7),
                  status="allocated", shipments=ships)
    # DE lot export (batch 003) from Venlo
    b.add(channel="wholesale", customer="CUS-000018", odt=datetime.combine(D(34), datetime.min.time()) + timedelta(hours=11),
          lines=[b.line("SKU-100021", 200, channel="wholesale", batch="BATCH-POL-PINK-003")], dc="DC4", due=D(28),
          shipments=[ship(D(32), D(30), {0: 200})])

    # --- 07:65:Q2 disputed GBP 480k wholesale invoice: second delivery arrived 360 units short and damaged
    b.add(oid="ORD-900040", channel="wholesale", customer="CUS-000028", odt=T(40, 10), dc="DC3", due=D(26),
          lines=[b.line("SKU-100448", 4000, 60.0, "wholesale"), b.line("SKU-100455", 4000, 60.0, "wholesale")],
          shipments=[ship(D(31), D(29), {0: 4000, 1: 1000}, reason="location", signed="M. Hargreaves (goods-in)"),
                     ship(D(28), D(25), {1: 3000}, reason="location", received=2640,
                          signed="J. Patel, noted 360 units damaged/missing on pallet 4")])

    # --- 07:65:Q5 customer 75 days overdue: orders on credit hold, one urgent GBP 20k
    for oid, qty, price, prio, ago, sku in [("ORD-900050", 400, 50.0, "urgent", 2, "SKU-100469"),
                                            ("ORD-900051", 350, 90.0, "normal", 9, "SKU-100476"),
                                            ("ORD-900052", 260, 70.0, "normal", 16, "SKU-100483")]:
        b.add(oid=oid, channel="wholesale", customer="CUS-000016", odt=T(ago, 11), dc="DC1", due=D(ago - 7),
              lines=[b.line(sku, qty, price, "wholesale", alloc=0)], status="open", priority=prio,
              hold=("credit", "Account 75 days overdue, over credit limit"))
    b.add(channel="wholesale", customer="CUS-000016", odt=T(70, 11), dc="DC1", due=D(63),
          lines=[b.line("SKU-100469", 200, 50.0, "wholesale")], shipments=[ship(D(66), D(64), {0: 200})])

    # --- 08:75:Q2 8,000 scarves, three wholesale customers ordered 15,000
    for oid, cust, qty, ago in [("ORD-900060", "CUS-000036", 6000, 21), ("ORD-900061", "CUS-000037", 5000, 14),
                                ("ORD-900062", "CUS-000038", 4000, 7)]:
        b.add(oid=oid, channel="wholesale", customer=cust, odt=T(ago, 10), dc="DC1", due=D(ago - 21),
              lines=[b.line("SKU-100035", qty, 54.5, "wholesale", alloc=0)], status="open")

    # --- 08:75:Q1 CUS-000030: last four orders arrived short (two our fault, one lost by carrier, one not short)
    cu = "CUS-000030"
    b.add(oid="ORD-900070", channel="wholesale", customer=cu, odt=T(45, 9), dc="DC1", due=D(38),   # oversold at allocation
          lines=[b.line("SKU-100469", 800, 32.0, "wholesale", alloc=560), b.line("SKU-100476", 300, 32.0, "wholesale")],
          oversold={0: True}, shipments=[ship(D(42), D(40), {0: 560, 1: 300}, signed="Goods-in")])
    b.add(oid="ORD-900071", channel="wholesale", customer=cu, odt=T(32, 9), dc="DC1", due=D(25),   # lost by carrier
          lines=[b.line("SKU-100469", 600, 32.0, "wholesale")],
          shipments=[ship(D(29), None, {0: 600})])
    b.add(oid="ORD-900072", channel="wholesale", customer=cu, odt=T(20, 9), dc="DC1", due=D(13),   # allocated full, picked short
          lines=[b.line("SKU-100476", 500, 32.0, "wholesale"), b.line("SKU-100483", 200, 32.0, "wholesale")],
          shipments=[ship(D(17), D(15), {0: 450, 1: 200}, signed="Goods-in")])
    b.add(oid="ORD-900073", channel="wholesale", customer=cu, odt=T(9, 9), dc="DC1", due=D(2),    # fully shipped and received
          lines=[b.line("SKU-100469", 400, 32.0, "wholesale"), b.line("SKU-100483", 300, 32.0, "wholesale")],
          shipments=[ship(D(6), D(4), {0: 400, 1: 300}, signed="Goods-in")])
