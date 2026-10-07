"""Property & Footfall data: weekly energy, daily/hourly store footfall, hourly forecasts, competitor catchments."""
import random
from datetime import date, datetime, timedelta

HOURS = list(range(9, 21))
HOUR_SHAPE = [0.4, 0.4, 0.8, 0.8, 1.0, 1.0, 0.9, 0.9, 0.6, 0.6, 0.6, 0.6]
DOW = [0.9, 0.9, 0.95, 1.0, 1.15, 1.7, 1.25]  # Mon..Sun
FORMAT_F = {"high_street": 1.1, "shopping_centre": 1.05, "retail_park": 1.0, "outlet": 0.95}

# Annual kWh last year per DC (matches the esg system's scope 2 history).
DC_KWH = {"DC1": 13.8e6, "DC2": 10.9e6, "DC3": 6.4e6, "DC4": 4.9e6, "DC5": 3.7e6}
DC6_KWH = 4.5e6  # DC6 Corby 3PL overflow: 911 t Scope 2 in esg last year at about 0.2 t/MWh; own rng so the other data does not move
KWH_YOY = 0.99  # real electricity use is only about 1% lower than the prior 12 months

HOURLY_STORES = ["ST214", "ST001", "ST002", "ST003", "ST008", "ST010", "ST020", "ST050", "ST150", "ST159", "ST207", "ST208"]
LONG_STORE = "ST214"
LONG_DAYS = 158   # ST214 history from early May, covers the June roadworks, July festival, August match
SHORT_DAYS = 56

COMPETITORS = [("CMPD-001", "HomeShop Direct"), ("CMPD-002", "John Lewis"), ("CMPD-004", "Currys"),
               ("CMPD-005", "Argos"), ("CMPD-006", "JD Sports")]


def _effect(site, d):
    """Multiplier on a day's footfall from local events (ST214 story)."""
    if site != LONG_STORE:
        return 1.0
    m = 1.0
    if date(2026, 6, 1) <= d <= date(2026, 6, 20):
        m *= 0.92   # roadworks on the adjacent street
    if d == date(2026, 7, 18):
        m *= 1.30   # summer music festival
    if d == date(2026, 8, 8):
        m *= 0.80   # home football match, parking
    if d >= date(2026, 9, 14):
        m *= 0.93   # JD Sports opens 300 m away
    if d >= date(2026, 9, 15):
        m *= 0.96   # parking area access roadworks
    if d >= date(2026, 10, 1):
        m *= 0.95   # main access road roadworks
    return m


def _split(total, weights, rng, jitter=0.08):
    w = [x * (1 + rng.uniform(-jitter, jitter)) for x in weights]
    s = sum(w)
    parts = [int(total * x / s) for x in w]
    parts[parts.index(max(parts))] += total - sum(parts)
    return parts


def generate(g):
    r = g.rng
    A = g.as_of
    sites = g.master("sites")
    stores = [s for s in sites if s["type"] == "store"]

    # ------------------------------------------------------------------ energy (weekly, 108 weeks)
    energy = []
    monday = A - timedelta(days=A.weekday())
    energy_sites = [(s["site_id"], DC_KWH[s["site_id"]] / 52.0) for s in sites if s["site_id"] in DC_KWH]
    for s in stores[:60]:
        energy_sites.append((s["site_id"], int(s["sqft"]) * 0.26))
    for site_id, base in energy_sites:
        site_f = 1 + r.uniform(-0.04, 0.04)
        for wk in range(-108, 0):
            ws = monday + timedelta(weeks=wk)
            season = 1.0 + 0.18 * (1 if ws.month in (12, 1, 2) else 0) - 0.08 * (1 if ws.month in (6, 7, 8) else 0)
            yoy = KWH_YOY if wk >= -52 else 1.0
            kwh = base * site_f * season * yoy * (1 + r.gauss(0, 0.012))
            energy.append({
                "consumption_id": f"ENG-{len(energy) + 1:06d}", "site_id": site_id,
                "period_start": ws, "period_end": ws + timedelta(days=6),
                "energy_kwh": round(kwh, 1), "energy_cost_gbp": round(kwh * 0.18, 2),
                "measured_at": datetime.combine(ws + timedelta(days=7), datetime.min.time()),
            })

    if any(x["site_id"] == "DC6" for x in sites):  # Corby 3PL overflow DC (esg Scope 2: removed from the reporting boundary this year)
        r6 = random.Random("property-dc6")
        site_f = 1 + r6.uniform(-0.04, 0.04)
        for wk in range(-108, 0):
            ws = monday + timedelta(weeks=wk)
            season = 1.0 + 0.18 * (1 if ws.month in (12, 1, 2) else 0) - 0.08 * (1 if ws.month in (6, 7, 8) else 0)
            yoy = KWH_YOY if wk >= -52 else 1.0
            kwh = DC6_KWH / 52.0 * site_f * season * yoy * (1 + r6.gauss(0, 0.012))
            energy.append({
                "consumption_id": f"ENG-{len(energy) + 1:06d}", "site_id": "DC6",
                "period_start": ws, "period_end": ws + timedelta(days=6),
                "energy_kwh": round(kwh, 1), "energy_cost_gbp": round(kwh * 0.18, 2),
                "measured_at": datetime.combine(ws + timedelta(days=7), datetime.min.time()),
            })

    # ------------------------------------------------------------------ footfall daily (all stores) + hourly (a subset)
    daily, hourly, forecasts = [], [], []
    for s in stores:
        sid = s["site_id"]
        base = int(s["sqft"]) * 0.12 * FORMAT_F.get(s["format"], 1.0) * r.uniform(0.95, 1.05)
        spv0 = r.uniform(13.0, 15.5)
        ndays = LONG_DAYS if sid == LONG_STORE else SHORT_DAYS
        for k in range(ndays - 1, -1, -1):
            d = A - timedelta(days=k)
            ff = int(base * DOW[d.weekday()] * _effect(sid, d) * (1 + r.gauss(0, 0.04)))
            sales = round(ff * spv0 * (1 + r.gauss(0, 0.03)), 2)
            daily.append({"site_id": sid, "date": d, "footfall_count": ff, "sales_gbp": sales})
            if sid in HOURLY_STORES and (sid == LONG_STORE or k < 28):
                counts = _split(ff, HOUR_SHAPE, r)
                w = [c * (1 + r.uniform(-0.05, 0.05)) for c in counts]
                sw = sum(w)
                sal = [round(sales * x / sw, 2) for x in w]
                sal[sal.index(max(sal))] = round(sales - sum(sal) + max(sal), 2)
                for h, c, sv in zip(HOURS, counts, sal):
                    hourly.append({"footfall_id": f"FF-{len(hourly) + 1:06d}", "site_id": sid, "date": d, "hour": h,
                                   "footfall_count": c, "sales_gbp": sv,
                                   "recorded_at": datetime.combine(d, datetime.min.time()) + timedelta(hours=h + 1)})
        if sid in HOURLY_STORES:
            for k in range(1, 22):
                d = A + timedelta(days=k)
                m = _effect(sid, d)
                if sid == LONG_STORE:
                    # promotions in the pricing calendar lift trade: knitwear 3-20 Oct, bedding 9-18 Oct
                    if date(2026, 10, 3) <= d <= date(2026, 10, 20):
                        m *= 1.05
                    if date(2026, 10, 9) <= d <= date(2026, 10, 18):
                        m *= 1.04
                    if d > date(2026, 10, 15):
                        m /= 0.96   # parking roadworks end 15 Oct
                    if d > date(2026, 10, 31):
                        m /= 0.95   # access road roadworks end 31 Oct
                day_total = base * DOW[d.weekday()] * m
                conf0 = 93 - 0.7 * k
                for h, wgt in zip(HOURS, HOUR_SHAPE):
                    fc = int(day_total * wgt / sum(HOUR_SHAPE) * (1 + r.gauss(0, 0.03)))
                    forecasts.append({"forecast_id": f"FFC-{len(forecasts) + 1:06d}", "site_id": sid, "forecast_date": d,
                                      "hour": h, "forecast_footfall_count": fc,
                                      "confidence_level": round(max(60, min(98, conf0 + r.gauss(0, 1.5))), 1),
                                      "created_at": datetime.combine(A, datetime.min.time()) + timedelta(hours=6)})

    # ------------------------------------------------------------------ catchments with competitor overlap
    planted = {
        "ST214": [("CMPD-002", "open", 0.45, 18.0), ("CMPD-006", "open", 0.3, 12.0),
                  ("CMPD-005", "open", 0.7, 6.0), ("CMPD-004", "closed", 0.9, 0.0)],
        "ST208": [("CMPD-002", "open", 0.6, 14.0)],
        "ST207": [("CMPD-005", "closed", 0.8, 0.0)],
    }
    names = dict(COMPETITORS)
    catchments = []
    for s in stores:
        sid = s["site_id"]
        fmt = s["format"]
        radius = round(max(1.5, min(8.0, r.gauss(4.5 if fmt == "retail_park" else 2.8, 0.8))), 1)
        pop = max(12000, int(r.gauss(52000 if fmt != "outlet" else 40000, 12000)) // 500 * 500)
        if sid in planted:
            rows = planted[sid]
        else:
            n = r.choice([0, 1, 1, 2, 2, 3])
            rows = [(c, "open", round(r.uniform(0.4, 3.0), 1), round(r.uniform(2, 9), 1))
                    for c, _ in r.sample(COMPETITORS, n)]
        for cid, st, dist, ov in rows:
            catchments.append({"catchment_id": f"CAT-{len(catchments) + 1:06d}", "site_id": sid, "competitor_id": cid,
                               "competitor_name": names[cid], "competitor_status": st, "distance_km": dist,
                               "radius_km": radius, "population": pop, "overlap_percentage": ov,
                               "updated_at": datetime.combine(A, datetime.min.time())})

    return {"energy_consumption": energy, "store_footfall_daily": daily, "store_footfall": hourly,
            "footfall_forecast": forecasts, "store_catchment": catchments}
