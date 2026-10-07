"""Web analytics data: search trends, traffic, conversion, marketing, creatives, resale funnel and peak forecast.

Story anchors (data time, as_of = Monday 2026-10-05):
  * 08:74:Q1  conversion fell ~0.4 pts in the week 28 Sep - 4 Oct vs the week before: mobile checkout broke
               (3-D Secure, from 30 Sep), a small drop everywhere from 29 Sep (London delivery promise relaxed,
               gateway timeouts) and a mix shift to low-intent paid/social traffic.
  * 08:74:Q3  next-day lifts conversion most in LS1, G1, L1, NG1, M1, B1, S1, NE1, CF1, LE1.
  * 08:74:Q2  daily peak forecast Black Friday (27 Nov) to Christmas Eve.
  * 05:49:Q4  resale page views fell by more than half while step conversion stayed healthy (awareness problem).
  * 03:23:Q2  search for backpacks / recycled polyester climbing.
"""
from datetime import timedelta

CHANNELS = ["organic", "paid", "direct", "social", "email", "referral"]
DEVICES = ["mobile", "desktop", "tablet"]

# sessions per day by channel (UK web, all devices)
BASE_SESSIONS = {"organic": 29000, "paid": 16500, "direct": 12000, "social": 6500, "email": 5500, "referral": 2500}
DEVICE_SPLIT = {
    "organic": (0.62, 0.33, 0.05), "paid": (0.66, 0.29, 0.05), "direct": (0.50, 0.43, 0.07),
    "social": (0.78, 0.18, 0.04), "email": (0.55, 0.40, 0.05), "referral": (0.52, 0.42, 0.06),
}
# conversion rate (%) by channel for mobile, desktop, tablet before the incident
BASE_CONV = {
    "organic": (2.2, 3.5, 2.7), "paid": (1.7, 2.9, 2.2), "direct": (3.0, 4.6, 3.5),
    "social": (0.9, 1.5, 1.1), "email": (3.8, 5.4, 4.2), "referral": (1.5, 2.5, 1.9),
}
AOV = {"mobile": 44.0, "desktop": 54.0, "tablet": 50.0}
DOW_SESSIONS = [1.00, 0.97, 0.95, 0.97, 1.00, 1.05, 1.12]  # Mon..Sun


def _traffic(g):
    r = g.rng
    rows = []
    for days_ago in range(35, 0, -1):  # 28 Aug .. 4 Oct (data stops yesterday)
        d = g.days_ago(days_ago)
        for ch in CHANNELS:
            ch_mult = 1.0
            if d >= g.days_ago(7) and ch == "paid":
                ch_mult = 1.28      # new prospecting campaign from Mon 28 Sep
            if d >= g.days_ago(7) and ch == "social":
                ch_mult = 1.15
            for i, dev in enumerate(DEVICES):
                sessions = BASE_SESSIONS[ch] * DEVICE_SPLIT[ch][i] * DOW_SESSIONS[d.weekday()] * ch_mult
                sessions = int(sessions * r.uniform(0.95, 1.05))
                rate = BASE_CONV[ch][i] / 100.0
                # incident multipliers
                if d >= g.days_ago(6):      # Tue 29 Sep: promise relaxed in four London areas + gateway timeouts
                    rate *= 0.95 if dev == "desktop" else (0.96 if dev == "mobile" else 0.96)
                if dev == "mobile":
                    if d == g.days_ago(5):  # Wed 30 Sep: error starts 17:40
                        rate *= 0.88
                    elif d >= g.days_ago(4):  # Thu 1 Oct onward
                        rate *= 0.72
                rate *= r.uniform(0.97, 1.03)
                orders = int(round(sessions * rate))
                revenue = round(orders * AOV[dev] * r.uniform(0.97, 1.03), 2)
                rows.append({"date": d, "channel": ch, "device": dev, "sessions": sessions,
                             "conversions": orders, "revenue_gbp": revenue})
    return rows


# postcode area -> (relative weight, std conv %, next-day lift in pts, next-day live?)
AREAS = {
    "M1": (223, 2.6, 0.78, True), "B1": (187, 2.5, 0.72, True), "SW1": (155, 2.9, 0.30, True),
    "LS1": (125, 2.4, 1.10, False), "SE1": (108, 2.8, 0.28, True), "G1": (103, 2.3, 1.00, False),
    "E1": (98, 2.8, 0.25, True), "N1": (91, 2.8, 0.22, True), "L1": (80, 2.3, 0.92, False),
    "W1": (73, 3.0, 0.20, True), "NW1": (54, 2.7, 0.18, True), "EH1": (52, 2.6, 0.15, False),
    "BS1": (43, 2.7, 0.12, True), "NG1": (37, 2.4, 0.85, False), "CF1": (37, 2.3, 0.55, False),
    "S1": (29, 2.3, 0.66, False), "NE1": (23, 2.2, 0.60, False), "LE1": (22, 2.4, 0.50, False),
    "EC1": (16, 3.1, 0.10, True), "WC1": (15, 3.0, 0.06, True),
}


def _delivery(g):
    r = g.rng
    rows = []
    for days_ago in range(60, 0, -1):
        d = g.days_ago(days_ago)
        for area, (w, std, lift, live) in AREAS.items():
            area_sessions = w * 8 * DOW_SESSIONS[d.weekday()]
            nd_share = 0.30 if live else 0.12     # not-live areas: next-day shown to a pilot cell only
            for opt in ("standard", "next_day"):
                sessions = int(area_sessions * (nd_share if opt == "next_day" else 1 - nd_share) * r.uniform(0.95, 1.05))
                rate = std + (lift if opt == "next_day" else 0.0)
                rate *= r.uniform(0.98, 1.02)
                orders = int(round(sessions * rate / 100))
                aov = 51.0 if opt == "next_day" else 48.0
                rows.append({"date": d, "postcode_area": area, "delivery_option": opt, "sessions": sessions,
                             "orders": orders, "conversion_rate": round(100.0 * orders / max(sessions, 1), 2),
                             "revenue_gbp": round(orders * aov * r.uniform(0.98, 1.02), 2)})
    return rows


MONTH_PROFILE = {  # seasonal multipliers for generic and backpack-like terms
    1: 1.15, 2: 0.95, 3: 0.95, 4: 1.0, 5: 1.0, 6: 1.05, 7: 1.2, 8: 1.45, 9: 1.1, 10: 0.9, 11: 0.95, 12: 1.25,
}


def _searches(g):
    r = g.rng
    rows = []
    n = 1
    # (term, category, baseline weekly volume, seasonal strength 0..1)
    generic = [
        ("rucksack", "Bags", 5200, 1.0), ("athleisure", "Womenswear", 9000, 0.3),
        ("yoga pants", "Womenswear", 12000, 0.4), ("home decor", "Home", 18000, 0.5),
        ("bedding", "Home", 15000, 0.6), ("sustainable fashion", "Womenswear", 7000, 0.1),
        ("eco-friendly", "All", 11000, 0.1), ("laptop bag", "Bags", 6500, 0.8),
    ]
    story = {  # weeks_ago 6..0 explicit ramp
        "backpack": [12000, 12800, 14000, 16500, 18200, 20100, 22000],
        "recycled polyester": [8500, 9200, 9900, 11000, 13500, 15000, 16800],
        "recycled polyester backpack": [1100, 1400, 1900, 2400, 3000, 3500, 3900],
    }
    # earlier weeks for story terms: seasonal baseline
    story_base = {"backpack": (11500, 1.0, "Bags"), "recycled polyester": (4200, 0.1, "Bags"),
                  "recycled polyester backpack": (800, 0.3, "Bags")}
    prev = {}
    for k in range(51, -1, -1):
        d = g.days_ago(7 * k)
        for term, cat, base, strength in generic:
            seas = 1 + (MONTH_PROFILE[d.month] - 1) * strength
            vol = int(base * seas * r.uniform(0.94, 1.06))
            rows.append(_trend_row(n, term, d, vol, cat, prev))
            n += 1
        for term, (base, strength, cat) in story_base.items():
            if k <= 6:
                vol = story[term][6 - k]
            else:
                seas = 1 + (MONTH_PROFILE[d.month] - 1) * strength
                vol = int(base * seas * r.uniform(0.95, 1.05))
                # late summer back-to-school bump already faded by early September for the backpack term
                if term == "backpack" and d.month in (8,):
                    vol = int(vol * 1.0)
            rows.append(_trend_row(n, term, d, vol, cat, prev))
            n += 1
    return rows


def _trend_row(n, term, d, vol, cat, prev):
    hist = prev.setdefault(term, [])
    ref = sum(hist[-4:]) / len(hist[-4:]) if hist else vol
    direction = "up" if vol > ref * 1.05 else ("down" if vol < ref * 0.95 else "stable")
    hist.append(vol)
    return {"trend_id": f"ST-{n:06d}", "search_term": term, "date": d, "volume": max(500, vol),
            "trend_direction": direction, "category": cat}


MARKETING = [  # range_id, campaign name, channel, ctr, click->conv, aov
    ("STY-5520", "Dresses Autumn Edit", "email", 0.07, 0.030, 41.0),
    ("STY-5520", "Dresses Autumn Edit", "paid", 0.018, 0.016, 41.0),
    ("STY-7731", "Outerwear Preview", "social", 0.014, 0.012, 77.0),
    ("STY-7731", "Outerwear Preview", "email", 0.065, 0.028, 77.0),
    ("STY-T-4410", "Smart Trouser Push", "paid", 0.02, 0.018, 101.0),
    ("STY-T-4410", "Smart Trouser Push", "organic", 0.025, 0.022, 101.0),
    ("PF-220", "Portable Fan Clearance", "paid", 0.022, 0.02, 78.0),
    ("PF-220", "Portable Fan Clearance", "social", 0.012, 0.01, 78.0),
    ("K-1700", "Kettle Autumn Deals", "email", 0.07, 0.034, 35.0),
    ("K-1700", "Kettle Autumn Deals", "paid", 0.02, 0.019, 35.0),
]


def _marketing(g):
    r = g.rng
    rows = []
    for i, (rng_id, name, ch, ctr, cr, aov) in enumerate(MARKETING, start=1):
        start = g.days_ago(r.randint(20, 75))
        end = start + timedelta(days=r.randint(7, 21))
        impressions = r.randint(80000, 400000)
        clicks = int(impressions * ctr * r.uniform(0.9, 1.1))
        conv = int(clicks * cr * r.uniform(0.9, 1.1))
        rev = round(conv * aov, 2)
        spend = round({"paid": 0.45, "social": 0.4, "email": 0.02, "organic": 0.0}[ch] * clicks * r.uniform(0.9, 1.1), 2)
        rows.append({"activity_id": f"MA-{i:06d}", "range_id": rng_id, "campaign_name": name, "channel": ch,
                     "start_date": start, "end_date": end, "impressions": impressions, "clicks": clicks,
                     "conversions": conv, "revenue_gbp": rev, "spend_gbp": spend, "status": "completed"})
    return rows


def _creatives(g):
    """Generated creatives for the generated campaigns (the event stories are in seed/campaign_creatives.csv)."""
    r = g.rng
    rows = []
    cid = 1
    seen = []
    for _rng, name, _ch, ctr, cr, aov in MARKETING:
        if name in seen:
            continue
        seen.append(name)
        start = g.days_ago(r.randint(25, 70))
        for ctype in ("image", "video", "text", "carousel"):
            for variant in ("variant_a", "variant_b"):
                impressions = r.randint(20000, 90000)
                clicks = int(impressions * ctr * r.uniform(0.7, 1.3))
                conv = int(clicks * cr * r.uniform(0.7, 1.3))
                rows.append({"creative_id": f"CC-{cid:06d}", "campaign_name": name, "creative_type": ctype,
                             "test_variant": variant, "start_date": start, "end_date": start + timedelta(days=14),
                             "impressions": impressions, "clicks": clicks, "conversions": conv,
                             "revenue_gbp": round(conv * aov, 2), "engagement_rate_pct": round(r.uniform(2.0, 6.0), 2)})
                cid += 1
    return rows


VIEWS = [9100, 8900, 8700, 8500, 8200, 7900, 7200, 6500, 5800, 4950, 4200, 3900, 3800]  # 13 weeks ago .. last week


def _resale(g):
    r = g.rng
    rows = []
    for idx, k in enumerate(range(13, 0, -1)):
        d = g.days_ago(7 * k)
        views = VIEWS[idx]
        adds = int(views * 0.24 * r.uniform(0.97, 1.03))
        checkout = int(adds * 0.62 * r.uniform(0.97, 1.03))
        purchase = int(checkout * 0.71 * r.uniform(0.97, 1.03))
        listed = int(2600 - idx * 20 + r.randint(-30, 30))
        sold = int(purchase * 1.08)
        gmv = round(sold * 34.0 * r.uniform(0.97, 1.03), 2)
        for stage, users, tx_f in (("views", views, 1.5), ("item_added", adds, 1.3),
                                   ("checkout", checkout, 1.0), ("purchase", purchase, 1.0)):
            last = stage == "purchase"
            rows.append({"date": d, "funnel_stage": stage, "user_count": users,
                         "transaction_count": int(users * tx_f),
                         "items_listed": listed if last else 0, "items_sold": sold if last else 0,
                         "gmv_gbp": gmv if last else 0.0})
    return rows


def _forecast(g):
    """Daily traffic forecast Black Friday (Fri 27 Nov) to Christmas Eve, by channel."""
    r = g.rng
    bf = g.as_of.replace(month=11, day=27)
    xmas_eve = g.as_of.replace(month=12, day=24)
    base_day = {ch: v for ch, v in BASE_SESSIONS.items()}
    # day multipliers vs a normal day; traffic is sessions
    special = {(11, 27): 2.9, (11, 28): 2.2, (11, 29): 1.9, (11, 30): 2.6, (12, 1): 1.6, (12, 2): 1.4,
               (12, 14): 2.0, (12, 15): 2.0, (12, 16): 2.2, (12, 17): 2.4, (12, 18): 2.6, (12, 19): 2.7,
               (12, 20): 2.5, (12, 21): 2.4, (12, 22): 2.2, (12, 23): 1.9, (12, 24): 1.1}
    ch_boost = {"organic": 1.0, "paid": 1.1, "direct": 1.0, "social": 1.05, "email": 1.4, "referral": 0.9}
    rows = []
    d = bf
    while d <= xmas_eve:
        mult = special.get((d.month, d.day))
        if mult is None:
            mult = 1.35 + (0.08 if d.weekday() >= 5 else 0.0) + r.uniform(-0.04, 0.04)
        conv = 0.034 if (d.month, d.day) in ((11, 27), (11, 30)) else (0.031 if d.month == 12 and d.day >= 14 else 0.028)
        if (d.month, d.day) == (12, 24):
            conv = 0.022
        for ch in CHANNELS:
            sessions = int(base_day[ch] * mult * (1 + (ch_boost[ch] - 1) * (mult - 1) / 1.5) * r.uniform(0.98, 1.02))
            orders = int(sessions * conv * (1.18 if ch == "email" else 0.85 if ch == "social" else 1.0))
            aov = 52.0 if d.month == 12 else 55.0
            rows.append({"date": d, "channel": ch, "forecast_volume": sessions, "forecast_orders": orders,
                         "forecast_revenue_gbp": round(orders * aov, 2),
                         "confidence_pct": round(88 - (d - bf).days * 0.35 + r.uniform(-1.5, 1.5), 1)})
        d += timedelta(days=1)
    return rows


def generate(g):
    return {
        "search_trends": _searches(g),
        "traffic_by_channel": _traffic(g),
        "conversion_metrics": _delivery(g),
        "marketing_activities": _marketing(g),
        "campaign_creatives": _creatives(g),
        "resale_funnel": _resale(g),
        "traffic_forecast": _forecast(g),
    }
