"""Store workforce data: colleagues, rotas, shifts, availability, labour standards and weekly labour cost.

Stories planted here (all relative to the data as-of Monday):
* ST214 (Glasgow Retail Park): Friday deliveries are received single-handed by an agency worker, Monday
  14:00-16:00 is covered by one person, the Assistant Manager post is vacant, labour cost is the highest in
  cluster B. Next week's rota is a draft (ROT-900001) with a short Saturday evening and a long weekday morning.
* ST150 (Leeds Shopping Centre): the stock assistant works 08:00-16:00 every weekday, so nobody rostered is
  in the stockroom at 20:00 when the evening removals happen; the two closers are other colleagues.
* ST159 (Leeds Retail Park): the store manager is the only person on the tills on Thursday afternoons.
* Labour cost %: ST150 14.4, ST143 12.1, ST142 11.5 are the outliers in UK North (norm about 10.2).
"""
import math
from datetime import datetime, time, timedelta

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def hm(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def hours_of(start, end):
    return (hm(end) - hm(start)) / 60.0


def generate(g):
    r = g.rng
    mon0 = g.as_of - timedelta(days=g.as_of.weekday())

    def wk(n):
        return mon0 + timedelta(weeks=n)

    def ts(d, h=8, m=0):
        return datetime.combine(d, time(h, m))

    sites = {s["site_id"]: s for s in g.master("sites") if s["type"] == "store"}
    managers = {e["site_id"]: e for e in g.master("employees") if e["role"] == "Store Manager" and e["site_id"] in sites}

    staff, by_site = [], {}

    def add_staff(site, name, role, hours, status="active", emp="", sid=None):
        row = {"staff_id": sid or f"STF-{len(staff) + 1:06d}", "site_id": site, "employee_id": emp, "name": name,
               "role": role, "status": status, "contract_hours": hours}
        staff.append(row)
        by_site.setdefault(site, []).append(row)
        return row

    def person():
        return f"{g.fake.first_name()} {g.fake.last_name()}"

    # ---------- story stores: explicit staff ----------
    s214 = {}
    for key, name, role, hrs, status, emp in [
        ("shi", managers["ST214"]["name"], "Store Manager", 40, "active", "EMP-00536"),
        ("ais", "Aisha Khan", "Team Leader", 37.5, "active", ""),
        ("pri", "Priya Nair", "Sales Assistant", 30, "active", ""),
        ("dan", "Dan Whitfield", "Stock Assistant", 32, "active", ""),
        ("tom", "Tom Gallagher", "Sales Assistant", 37.5, "active", ""),
        ("ell", "Ellie Brooks", "Sales Assistant", 20, "active", ""),
        ("cal", "Callum Reid", "Stock Assistant", 20, "agency", ""),
        ("mha", "Mhairi Campbell", "Sales Assistant", 30, "active", ""),
        ("jac", "Jack Murray", "Sales Assistant", 30, "active", ""),
        ("fio", "Fiona Gray", "Sales Assistant", 16, "active", ""),
        ("mar", "Marc Taylor", "Cover Manager", 0, "cover", "EMP-00529"),
        ("vac", "Vacant - Assistant Manager", "Assistant Manager", 37.5, "vacant", ""),
    ]:
        s214[key] = add_staff("ST214", name, role, hrs, status, emp, sid=f"STF-9000{len(s214) + 1:02d}")

    s150 = {}
    for key, name, role, hrs, emp in [
        ("jam", managers["ST150"]["name"], "Store Manager", 40, "EMP-00472"),
        ("lia", "Liam Pearson", "Stock Assistant", 37.5, ""),
        ("chl", "Chloe Barnes", "Team Leader", 37.5, ""),
        ("rhy", "Rhys Edwards", "Sales Assistant", 32, ""),
        ("omr", "Omar Siddiq", "Sales Assistant", 30, ""),
        ("han", "Hannah Ward", "Sales Assistant", 20, ""),
    ]:
        s150[key] = add_staff("ST150", name, role, hrs, "active", emp, sid=f"STF-9100{len(s150) + 1:02d}")

    # ---------- every other store: generic establishment ----------
    peers = {"ST206", "ST209", "ST202", "ST210"}  # closest retail parks to ST214 (same format, region, size)
    for sid, s in sites.items():
        if sid in by_site:
            continue
        sqft = int(s["sqft"])
        m = managers.get(sid)
        add_staff(sid, m["name"] if m else person(), "Store Manager", 40, "active", m["employee_id"] if m else "")
        if sid in peers or r.random() < 0.85:
            add_staff(sid, person(), "Assistant Manager", 37.5)
        for _ in range(2 if (sid in peers or sqft > 20000) else 1):
            add_staff(sid, person(), "Team Leader", 37.5)
        n_sa = (6 if sid in peers else 4 + sqft // 9000)
        for _ in range(n_sa):
            add_staff(sid, person(), "Sales Assistant", r.choice([16, 20, 24, 30, 30, 37.5]),
                      "agency" if (sid not in peers and r.random() < 0.05) else "active")
        for _ in range(2 if sid in peers else r.choice([1, 1, 2])):
            add_staff(sid, person(), "Stock Assistant", r.choice([30, 37.5]))
    # peers differ from ST214: a full establishment with an Assistant Manager and no agency or cover

    # ---------- rotas ----------
    rotas, shifts = [], []

    def new_rota(site, week, status, rota_id=None):
        past = week <= mon0
        mgr = managers.get(site)
        row = {"rota_id": rota_id or f"ROT-{len(rotas) + 1:06d}", "site_id": site, "week_start": week, "status": status,
               "approved_by": mgr["employee_id"] if (mgr and status != "draft") else "",
               "approved_at": ts(week - timedelta(days=4), 9) if status != "draft" else "",
               "updated_at": ts(week - timedelta(days=5 if past else 2), 8)}
        rotas.append(row)
        return row

    def add_shifts(rota, spec, fixed_ids=False):
        for i, (st, day, a, b, task) in enumerate(spec):
            shifts.append({
                "shift_id": f"SFT-9000{i + 1:02d}" if fixed_ids else f"SFT-{len(shifts) + 1:06d}",
                "rota_id": rota["rota_id"], "staff_id": st["staff_id"],
                "shift_date": rota["week_start"] + timedelta(days=day), "start_time": a, "end_time": b,
                "task_category": task, "status": "scheduled", "updated_at": rota["updated_at"]})

    # ST214 weekly pattern (staff key, weekday 0=Mon, start, end, task)
    t214 = [
        ("ais", 0, "09:00", "17:00", "till"), ("mha", 0, "09:00", "14:00", "till"), ("ell", 0, "09:00", "13:00", "shelf"),
        ("dan", 0, "09:00", "14:00", "stock"), ("jac", 0, "16:00", "21:00", "till"), ("fio", 0, "17:00", "21:00", "shelf"),
        ("dan", 1, "06:00", "14:00", "receiving"), ("pri", 1, "06:00", "14:00", "receiving"), ("shi", 1, "08:30", "17:00", "management"),
        ("mha", 1, "09:00", "15:00", "shelf"), ("ell", 1, "12:00", "17:00", "till"), ("tom", 1, "12:00", "21:00", "till"),
        ("jac", 1, "13:00", "21:00", "till"),
        ("shi", 2, "08:30", "17:00", "management"), ("ais", 2, "09:00", "17:00", "till"), ("pri", 2, "09:00", "17:00", "shelf"),
        ("ell", 2, "09:00", "14:00", "shelf"), ("tom", 2, "13:00", "21:00", "till"), ("fio", 2, "16:00", "21:00", "till"),
        ("mar", 2, "13:00", "21:00", "till"),
        ("shi", 3, "08:30", "17:00", "management"), ("ais", 3, "09:00", "17:00", "till"), ("dan", 3, "09:00", "17:00", "stock"),
        ("mha", 3, "09:00", "15:00", "shelf"), ("tom", 3, "12:00", "21:00", "shelf"), ("jac", 3, "13:00", "21:00", "till"),
        ("pri", 3, "13:00", "21:00", "till"),
        ("cal", 4, "06:00", "12:00", "receiving"), ("shi", 4, "08:30", "17:00", "management"), ("ais", 4, "09:00", "17:00", "till"),
        ("pri", 4, "09:00", "17:00", "shelf"), ("mha", 4, "09:00", "15:00", "till"), ("tom", 4, "12:00", "21:00", "till"),
        ("jac", 4, "13:00", "21:00", "till"), ("fio", 4, "16:00", "21:00", "till"),
        ("shi", 5, "08:30", "17:00", "management"), ("ais", 5, "09:00", "17:00", "till"), ("pri", 5, "09:00", "17:00", "shelf"),
        ("dan", 5, "09:00", "17:00", "stock"), ("ell", 5, "09:00", "15:00", "till"), ("tom", 5, "12:00", "21:00", "till"),
        ("mar", 5, "13:00", "21:00", "till"),
        ("mha", 6, "09:00", "17:00", "till"), ("jac", 6, "09:00", "17:00", "till"), ("cal", 6, "09:00", "17:00", "shelf"),
        ("fio", 6, "12:00", "21:00", "till"), ("ell", 6, "12:00", "18:00", "shelf"),
    ]
    spec214 = [(s214[k], d, a, b, t) for k, d, a, b, t in t214]
    hours214 = sum(hours_of(a, b) for _, _, a, b, _ in spec214)

    # ST150 weekly pattern: the stock assistant (lia) finishes at 16:00 every weekday; closers are chl, rhy, omr
    t150 = []
    for d in range(5):
        t150.append(("jam", d, "08:30", "16:30", "management"))
        t150.append(("lia", d, "08:00", "16:00", "stock"))
    for d, who in [(0, ("chl", "omr")), (1, ("chl", "rhy")), (2, ("rhy", "omr")), (3, ("chl", "rhy")), (4, ("chl", "rhy")),
                   (5, ("chl", "omr"))]:
        for w in who:
            t150.append((w, d, "12:00", "20:00", "till"))
    t150 += [("han", 5, "09:00", "15:00", "till"), ("han", 6, "11:00", "17:00", "till"), ("omr", 6, "11:00", "17:00", "shelf")]
    spec150 = [(s150[k], d, a, b, t) for k, d, a, b, t in t150]
    hours150 = sum(hours_of(a, b) for _, _, a, b, _ in spec150)

    # 20 UK North stores get full rotas (the Leeds stores first); ST214 and ST150 are the planted ones
    north = sorted(i for i, s in sites.items() if s["region"] == "UK North")
    leeds = [i for i in north if sites[i]["city"] == "Leeds"]
    near = [i for i in north if i in ("ST141", "ST142", "ST143", "ST144", "ST145")]
    rest = [i for i in north if i not in leeds + near]
    rota_stores = [i for i in (leeds + near + rest) if i != "ST150"][:20]

    def generic_spec(site):
        close = 20 if sites[site]["format"] in ("shopping_centre", "high_street") else 21
        end = f"{close:02d}:00"
        spec = []
        for s in by_site[site]:
            if s["status"] not in ("active", "agency"):
                continue
            role = s["role"]
            if role == "Store Manager":
                for d in sorted(r.sample(range(6), 5)):
                    spec.append((s, d, "08:30", "17:00", "management"))
            elif role == "Assistant Manager":
                for d in sorted(r.sample(range(7), 4)):
                    spec.append((s, d, "12:00", end, "management"))
            elif role == "Team Leader":
                for d in sorted(r.sample(range(6), 5)):
                    a, b = r.choice([("09:00", "17:00"), ("12:00", end)])
                    spec.append((s, d, a, b, "till"))
            elif role == "Stock Assistant":
                for d in sorted(r.sample(range(7), 4)):
                    if d in (1, 4):
                        spec.append((s, d, "06:00", "14:00", "receiving"))
                    else:
                        spec.append((s, d, "09:00", "17:00", "stock"))
            else:
                k = 3 if s["contract_hours"] <= 20 else 4 if s["contract_hours"] <= 30 else 5
                for d in sorted(r.sample(range(7), k)):
                    a, b = r.choice([("09:00", "15:00"), ("09:00", "17:00"), ("12:00", end), ("16:00", end), ("13:00", end)])
                    spec.append((s, d, a, b, r.choice(["till", "till", "shelf"])))
        return spec

    def st159_override(spec):
        cam = next(s for s in by_site["ST159"] if s["role"] == "Store Manager")
        out = []
        for x in spec:
            s, d, a, b, t = x
            if d == 3 and (s is cam or (t == "till" and a < "16:00" and b > "14:00")):
                continue
            out.append(x)
        out.append((cam, 3, "12:00", "18:00", "till"))
        return out

    for site in ["ST214", "ST150"] + rota_stores:
        weeks = range(-13, 2) if site in ("ST214", "ST150") else range(-8, 2)
        for n in weeks:
            week = wk(n)
            if site == "ST214" and n == 1:
                rota = new_rota(site, week, "draft", "ROT-900001")
                add_shifts(rota, spec214, fixed_ids=True)
                continue
            status = "archived" if n < -8 else ("published" if n <= 0 else "approved")
            rota = new_rota(site, week, status)
            if site == "ST214":
                add_shifts(rota, spec214)
            elif site == "ST150":
                add_shifts(rota, spec150)
            else:
                spec = generic_spec(site)
                if site == "ST159":
                    spec = st159_override(spec)
                add_shifts(rota, spec)

    # a few shifts changed after publication in past weeks (swaps), at random generic stores
    for sh in r.sample([x for x in shifts if not x["shift_id"].startswith("SFT-9") and x["shift_date"] < mon0], 40):
        sh["status"] = "swapped"

    # ---------- availability ----------
    availability = []
    for site in ["ST214", "ST150"] + rota_stores:
        for s in by_site[site]:
            if s["status"] not in ("active", "agency"):
                continue
            for n in (-1, 0, 1, 2):
                week = wk(n)
                flags = [True] * 7
                note = ""
                if site == "ST214" and n == 1:
                    if s["staff_id"] == s214["jac"]["staff_id"]:
                        flags[2], note = False, "Appointment Wednesday"
                    if s["staff_id"] == s214["fio"]["staff_id"]:
                        flags[3], note = False, "Second job Thursday"
                elif r.random() < 0.25:
                    d = r.randrange(7)
                    flags[d] = False
                    note = r.choice(["Requested time off", "Sick leave", "Annual leave", "Childcare"])
                availability.append({
                    "availability_id": f"AVL-{len(availability) + 1:06d}", "staff_id": s["staff_id"], "week_start": week,
                    "monday_available": flags[0], "tuesday_available": flags[1], "wednesday_available": flags[2],
                    "thursday_available": flags[3], "friday_available": flags[4], "saturday_available": flags[5],
                    "sunday_available": flags[6], "notes": note, "updated_at": ts(week - timedelta(days=7), 8)})

    # ---------- labour standards ----------
    stamp = datetime(2026, 1, 1, 9, 0)
    standards = [
        ("receiving", "Unload, check and put away a delivery", 2.0, "per delivery", 0),
        ("shelf", "Replenish shelves from the stockroom", 1.0, "per 1000 units", 1),
        ("till", "Till operation and customer service", 1.0, "per shift hour", 0),
        ("stock", "Stock count and stock checking", 3.0, "per count", 6),
        ("checkout", "Self-checkout assistance", 1.0, "per shift hour", 0),
        ("relabel", "Price relabelling for promotions or markdowns", 0.5, "per 100 items", 2),
        ("cleaning", "Store cleaning and maintenance", 2.0, "per shift", 1),
        ("management", "Rota, cash office and admin", 1.0, "per day", 1),
    ]
    std_rows = [{"standard_id": f"STD-{i + 1:06d}", "task_category": t, "description": d, "standard_hours": h,
                 "unit_of_measure": u, "max_defer_days": df, "status": "active", "updated_at": stamp}
                for i, (t, d, h, u, df) in enumerate(standards)]

    # ---------- weekly labour cost for every store, last 13 weeks ----------
    month_pct = {  # (Jul, Aug, Sep) labour cost %; BI and store_ops quote the same level for these stores
        "ST150": (14.2, 14.4, 14.4), "ST141": (10.1, 10.2, 10.1), "ST142": (10.4, 10.8, 11.5), "ST143": (10.8, 11.2, 12.1),
        "ST144": (9.3, 9.3, 9.1), "ST145": (10.2, 10.1, 10.3), "ST001": (12.3, 12.3, 12.0), "ST006": (12.8, 12.8, 12.5),
        "ST008": (14.0, 14.2, 13.2), "ST206": (12.0, 11.9, 11.9), "ST209": (12.4, 12.3, 12.3), "ST202": (11.8, 11.8, 11.7),
        "ST210": (12.1, 12.0, 12.0),
    }
    pct214 = [15.3, 15.2, 15.1, 15.2, 15.1, 15.0, 14.9, 15.0, 15.0, 14.6, 14.5, 14.5, 14.4]
    region_mean = {"UK North": 10.2, "UK South": 11.2, "UK Midlands": 11.5, "Scotland": 12.2, "Ireland": 12.8,
                   "EU Central": 12.5, "US": 12.0}
    region_rate = {"Ireland": 1.1, "EU Central": 1.2, "US": 1.25}
    base_pct = {}
    for sid, s in sites.items():
        mean = region_mean.get(s["region"], 11.5)
        v = r.uniform(9.5, 10.8) if s["region"] == "UK North" else r.uniform(mean - 1.0, mean + 0.9)
        base_pct[sid] = round(v, 1)
    costs = []
    for n in range(-13, 0):
        week = wk(n)
        mi = {7: 0, 8: 1, 9: 2}.get(week.month, 2)
        for sid, s in sites.items():
            rate = round(12.9 * region_rate.get(s["region"], 1.0) + r.uniform(-0.25, 0.25), 2)
            if sid == "ST214":
                pct, hours = pct214[n + 13], hours214 + r.choice([-4, 0, 0, 4])
            elif sid == "ST150":
                pct, hours = month_pct[sid][mi] + r.uniform(-0.05, 0.05), hours150 + r.choice([-4, 0, 0, 4])
            else:
                pct = (month_pct[sid][mi] if sid in month_pct else base_pct[sid]) + r.uniform(-0.15, 0.15)
                hours = None
            if hours is None:  # paid hours follow the establishment (with overtime), sales follow from the labour %
                hours = sum(x["contract_hours"] for x in by_site[sid] if x["status"] in ("active", "agency")) * r.uniform(0.97, 1.07)
            cost = hours * rate
            sales = cost / pct * 100
            costs.append({"site_id": sid, "week_start": week, "total_hours": round(hours, 1),
                          "total_labour_cost_gbp": round(cost, 2), "average_hourly_rate_gbp": rate,
                          "sales_value_gbp": round(sales, 2), "labour_cost_pct": round(cost / sales * 100, 1),
                          "updated_at": ts(week + timedelta(days=7), 9)})

    return {"store_staff": staff, "staff_rotas": rotas, "rota_shifts": shifts, "labour_standards": std_rows,
            "staff_availability": availability, "labour_costs": costs}
