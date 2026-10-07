"""Shared master/spine data. Every system's generator reads these via g.master(table)."""
from datetime import date, timedelta

DEPTS = {
    "Womenswear": ["Dresses", "Tops", "Knitwear", "Trousers", "Outerwear", "Blouses"],
    "Menswear": ["Shirts", "Knitwear", "Trousers", "Outerwear", "T-Shirts"],
    "Kids": ["Schoolwear", "Babywear", "Outerwear", "Nightwear"],
    "Home": ["Bedding", "Towels", "Cookware", "Drinkware", "Lighting", "Storage"],
    "Beauty": ["Skincare", "Fragrance", "Haircare", "Bodycare"],
    "Electricals": ["Small Appliances", "Personal Care", "Audio", "Smart Home"],
    "Accessories": ["Bags", "Footwear", "Jewellery", "Scarves"],
}
ORIGINS = {"Womenswear": ["CN", "BD", "VN", "TR", "IN"], "Menswear": ["BD", "CN", "VN", "TR", "PT"],
           "Kids": ["BD", "CN", "IN"], "Home": ["CN", "IN", "PT", "TR"], "Beauty": ["GB", "FR", "DE", "PL"],
           "Electricals": ["CN", "VN", "MX"], "Accessories": ["CN", "IN", "VN", "IT"]}
HS = {"Womenswear": "6204", "Menswear": "6203", "Kids": "6209", "Home": "6302", "Beauty": "3304",
      "Electricals": "8516", "Accessories": "4202"}
COLOURS = ["Black", "Navy", "Ivory", "Sage", "Rust", "Grey Marl", "Blush", "Ochre", "Denim", "White"]
PORTS = [("GBFXT", "Felixstowe", "GB", "Europe"), ("GBSOU", "Southampton", "GB", "Europe"),
         ("GBLGP", "London Gateway", "GB", "Europe"), ("NLRTM", "Rotterdam", "NL", "Europe"),
         ("DEHAM", "Hamburg", "DE", "Europe"), ("CNSHA", "Shanghai", "CN", "Asia"), ("CNNGB", "Ningbo", "CN", "Asia"),
         ("CNYTN", "Yantian", "CN", "Asia"), ("BDCGP", "Chittagong", "BD", "Asia"),
         ("VNSGN", "Ho Chi Minh City", "VN", "Asia"), ("INNSA", "Nhava Sheva", "IN", "Asia"),
         ("TRMER", "Mersin", "TR", "Europe"), ("PTLEI", "Leixoes", "PT", "Europe"),
         ("USNYC", "New York/New Jersey", "US", "Americas"), ("MXZLO", "Manzanillo", "MX", "Americas")]
ORIGIN_PORT = {"CN": ["CNSHA", "CNNGB", "CNYTN"], "BD": ["BDCGP"], "VN": ["VNSGN"], "IN": ["INNSA"],
               "TR": ["TRMER"], "PT": ["PTLEI"], "MX": ["MXZLO"], "IT": ["NLRTM"], "GB": ["GBFXT"],
               "FR": ["NLRTM"], "DE": ["DEHAM"], "PL": ["DEHAM"]}
UK_TOWNS = {
    "UK South": ["Reading", "Guildford", "Brighton", "Southampton", "Portsmouth", "Oxford", "Bristol", "Bath", "Exeter", "Canterbury", "Croydon", "Kingston", "Bromley", "Watford", "Cambridge", "Chelmsford", "Basingstoke", "Bournemouth", "Swindon", "Milton Keynes"],
    "UK Midlands": ["Birmingham", "Leicester", "Nottingham", "Derby", "Coventry", "Wolverhampton", "Northampton", "Solihull", "Stoke-on-Trent", "Worcester", "Lincoln", "Peterborough"],
    "UK North": ["Leeds", "Manchester", "Liverpool", "Sheffield", "Newcastle", "York", "Harrogate", "Chester", "Preston", "Hull", "Bradford", "Durham", "Stockport", "Warrington"],
    "Scotland": ["Glasgow", "Edinburgh", "Aberdeen", "Dundee", "Inverness", "Stirling"]}
DC_PORT = {"DC1": "GBFXT", "DC2": "GBSOU", "DC3": "GBLGP", "DC4": "NLRTM", "DC5": "USNYC"}


def generate(g):
    r, as_of = g.rng, g.as_of
    out = {}

    def section(n):
        """Independent random stream per section, so adding data in one section never reshuffles another."""
        r.seed(g.world["seed"] * 1000 + n)
        g.fake.seed_instance(g.world["seed"] * 1000 + n)

    # calendar FY26..FY28 (Feb 2025 - Jan 2028)
    cal, d = [], date(2025, 2, 1)
    while d <= date(2028, 1, 31):
        fy_start = date(d.year if d.month >= 2 else d.year - 1, 2, 1)
        cal.append({"date": d, "fy": f"FY{(fy_start.year + 1) % 100:02d}",
                    "fy_period": (d.month - 2) % 12 + 1, "fy_week": (d - fy_start).days // 7 + 1,
                    "cal_quarter": f"{d.year}-Q{(d.month - 1) // 3 + 1}",
                    "season": "SS" if 2 <= d.month <= 7 else "AW",
                    "is_peak": (d.month == 11 and d.day >= 15) or d.month == 12})
        d += timedelta(1)
    out["calendar"] = cal

    out["legal_entities"] = [
        {"entity_id": "LE-UK", "name": "Harbour & Vale Retail Ltd", "country": "GB", "currency": "GBP"},
        {"entity_id": "LE-IE", "name": "Harbour & Vale Ireland Ltd", "country": "IE", "currency": "EUR"},
        {"entity_id": "LE-NL", "name": "Harbour & Vale Europe BV", "country": "NL", "currency": "EUR"},
        {"entity_id": "LE-DE", "name": "Harbour & Vale GmbH", "country": "DE", "currency": "EUR"},
        {"entity_id": "LE-US", "name": "Harbour & Vale Inc", "country": "US", "currency": "USD"},
        {"entity_id": "LE-HK", "name": "Harbour & Vale Sourcing (HK) Ltd", "country": "HK", "currency": "HKD"}]

    section(1)
    # sites
    sites = [
        {"site_id": "DC1", "name": "Northampton DC", "type": "dc", "format": "national_dc", "country": "GB", "region": "UK Midlands", "city": "Northampton", "entity_id": "LE-UK", "sqft": 850000},
        {"site_id": "DC2", "name": "Daventry DC", "type": "dc", "format": "ecommerce_dc", "country": "GB", "region": "UK Midlands", "city": "Daventry", "entity_id": "LE-UK", "sqft": 620000},
        {"site_id": "DC3", "name": "Leeds DC", "type": "dc", "format": "regional_and_returns_dc", "country": "GB", "region": "UK North", "city": "Leeds", "entity_id": "LE-UK", "sqft": 410000},
        {"site_id": "DC4", "name": "Venlo DC", "type": "dc", "format": "eu_dc", "country": "NL", "region": "EU Central", "city": "Venlo", "entity_id": "LE-NL", "sqft": 380000},
        {"site_id": "DC5", "name": "Columbus DC", "type": "dc", "format": "us_dc", "country": "US", "region": "US", "city": "Columbus", "entity_id": "LE-US", "sqft": 260000},
        {"site_id": "HQ1", "name": "London Head Office", "type": "office", "format": "office", "country": "GB", "region": "UK South", "city": "London", "entity_id": "LE-UK", "sqft": 90000},
        {"site_id": "HK1", "name": "Hong Kong Sourcing Office", "type": "office", "format": "office", "country": "HK", "region": "Asia", "city": "Hong Kong", "entity_id": "LE-HK", "sqft": 12000}]
    for s in sites:
        s |= {"cluster": "", "opened_date": date(2004 + r.randint(0, 15), r.randint(1, 12), 1), "status": "open"}
    regions = ([("GB", "UK South", "LE-UK")] * 85 + [("GB", "UK Midlands", "LE-UK")] * 55 + [("GB", "UK North", "LE-UK")] * 60
               + [("GB", "Scotland", "LE-UK")] * 15 + [("IE", "Ireland", "LE-IE")] * 12 + [("DE", "EU Central", "LE-DE")] * 10
               + [("NL", "EU Central", "LE-NL")] * 8 + [("US", "US", "LE-US")] * 10)
    seen_names = {}
    for i, (c, reg, ent) in enumerate(regions, 1):
        fmt = r.choices(["high_street", "retail_park", "shopping_centre", "outlet", "travel"], [35, 30, 20, 8, 7])[0]
        sqft = {"high_street": 12000, "retail_park": 25000, "shopping_centre": 18000, "outlet": 15000, "travel": 2500}[fmt]
        sqft = int(sqft * r.uniform(0.6, 1.6))
        city = (r.choice(UK_TOWNS[reg]) if c == "GB" else r.choice({"IE": ["Dublin", "Cork", "Galway", "Limerick"], "DE": ["Düsseldorf", "Cologne", "Hamburg", "Berlin", "Munich"], "NL": ["Utrecht", "Amsterdam", "Rotterdam", "Eindhoven"], "US": ["Columbus", "Chicago", "Boston", "Philadelphia"]}[c]))
        nm = f"{city} {fmt.replace('_', ' ').title()}"
        seen_names[nm] = seen_names.get(nm, 0) + 1
        nm += f" {seen_names[nm]}" if seen_names[nm] > 1 else ""
        sites.append({"site_id": f"ST{i:03d}", "name": nm, "type": "store",
                      "format": fmt, "country": c, "region": reg, "city": city,
                      "cluster": "A" if sqft > 26000 else "B" if sqft > 16000 else "C" if sqft > 8000 else "D",
                      "entity_id": ent, "opened_date": g.date_between(7000, 200), "sqft": sqft,
                      "status": r.choices(["open", "refit", "closed"], [95, 3, 2])[0]})
    out["sites"] = sites
    stores = [s for s in sites if s["type"] == "store"]

    section(2)
    # DC bin locations (aisle-bay-level)
    locs = []
    for dc, aisles, bays in (("DC1", "ABCDEFGHJKLM", 30), ("DC2", "ABCDEFGHJK", 24), ("DC3", "ABCDEFGH", 20),
                             ("DC4", "ABCDEFG", 20), ("DC5", "ABCDE", 16)):
        for ai, a in enumerate(aisles):
            zone = "bulk" if ai >= len(aisles) - 2 else "hazmat" if a == "H" else "mezzanine" if a in "JK" else "pick" if ai < 4 else "reserve"
            if dc == "DC3" and a == "G":
                zone = "returns"
            for b in range(1, bays + 1):
                for lv in range(1, 5):
                    pf = zone == "pick" and lv <= 2
                    locs.append({"location_id": f"{dc}-{a}-{b:02d}-{lv:02d}", "site_id": dc, "zone": zone, "aisle": a,
                                 "bay": b, "level": lv,
                                 "location_type": "pick_face" if pf else "bulk_floor" if zone == "bulk" else "reserve",
                                 "max_weight_kg": 1000.0 if lv == 1 else 750.0 if lv == 2 else 500.0,
                                 "max_height_cm": 180 if lv == 1 else 150, "status": r.choices(["active", "blocked", "damaged", "inactive"], [96, 2, 1, 1])[0]})
    out["locations"] = locs

    section(3)
    # DC equipment: automation in DC1/DC2, MHE everywhere
    assets = []

    def asset(aid, name, site, cls, parent="", loc="", mfr="", model="", sw="", cost=0.0, crit="medium"):
        assets.append({"asset_id": aid, "name": name, "site_id": site, "asset_class": cls, "parent_asset_id": parent,
                       "location": loc, "manufacturer": mfr, "model": model, "install_date": g.date_between(3600, 300),
                       "software_version": sw, "replacement_cost_gbp": round(cost * r.uniform(0.85, 1.15), -1),
                       "criticality": crit, "status": r.choices(["in_service", "degraded"], [92, 8])[0]})
    asset("AST-DC2-SHT", "Daventry shuttle system", "DC2", "shuttle", mfr="Knapp", model="OSR Shuttle", sw="4.2.1", cost=4200000, crit="high")
    for i in range(1, 17):
        asset(f"AST-DC2-SHT-{i:02d}", f"Shuttle aisle {i}", "DC2", "shuttle", "AST-DC2-SHT", f"shuttle aisle {i}", "Knapp", "OSR-S2",
              r.choice(["4.2.1", "4.2.1", "4.3.0"]), 95000, "high")
    for dc, ncv in (("DC1", 12), ("DC2", 18), ("DC3", 6)):
        asset(f"AST-{dc}-CNV", f"{dc} conveyor network", dc, "conveyor", mfr="Interroll", model="RollerDrive", cost=1800000, crit="high")
        asset(f"AST-{dc}-SRT", f"{dc} tilt-tray sorter", dc, "sorter", mfr="Vanderlande", model="POSISORTER", sw="7.1", cost=2500000, crit="high")
        for i in range(1, ncv + 1):
            asset(f"AST-{dc}-CNV-M{i:02d}", f"Conveyor drive motor {i}", dc, "motor", f"AST-{dc}-CNV", f"conveyor section {i}", "SEW", "DRN90", cost=2400)
            asset(f"AST-{dc}-CNV-G{i:02d}", f"Conveyor gearbox {i}", dc, "gearbox", f"AST-{dc}-CNV", f"conveyor section {i}", "SEW", "R57", cost=3100)
            asset(f"AST-{dc}-CNV-S{i:02d}", f"Photo-eye sensor {i}", dc, "sensor", f"AST-{dc}-CNV", f"conveyor section {i}", "Sick", "WL12", cost=180, crit="low")
    for dc, n in (("DC1", 24), ("DC2", 14), ("DC3", 12), ("DC4", 10), ("DC5", 6)):
        for i in range(1, n + 1):
            cls = "reach_truck" if i % 3 == 0 else "forklift"
            asset(f"AST-{dc}-MHE-{i:02d}", f"{cls.replace('_', ' ').title()} {i}", dc, cls, loc="MHE fleet",
                  mfr=r.choice(["Linde", "Jungheinrich", "Toyota"]), model="R16" if cls == "reach_truck" else "E30", cost=38000)
        for i in range(1, 9):
            asset(f"AST-{dc}-DKL-{i:02d}", f"Dock leveller door {i}", dc, "dock_leveller", loc=f"door D{i:02d}", mfr="Hormann", cost=9000, crit="low")
        asset(f"AST-{dc}-SPR", f"{dc} sprinkler system", dc, "sprinkler", mfr="Tyco", cost=600000, crit="high")
        asset(f"AST-{dc}-CMP", f"{dc} air compressor", dc, "compressor", mfr="Atlas Copco", cost=45000)
    out["assets"] = assets

    section(4)
    # suppliers + factories
    suppliers, factories = [], []
    dept_list = list(DEPTS)
    for i in range(1, 81):
        dept = dept_list[(i - 1) % len(dept_list)]
        c = r.choice(ORIGINS[dept])
        name = f"{g.fake.last_name()} {r.choice(['Textiles', 'Garments', 'Manufacturing', 'Industries', 'Homewares', 'Trading', 'Apparel', 'Products'])} {r.choice(['Ltd', 'Co', 'Group', 'Pvt Ltd', 'JSC', 'A.S.'])}"
        suppliers.append({"supplier_id": f"SUP-{i:04d}", "name": name, "country": c, "category_focus": dept,
                          "tier": r.choices(["strategic", "preferred", "approved", "probation"], [15, 35, 42, 8])[0],
                          "status": r.choices(["active", "onboarding", "blocked", "exited"], [88, 5, 3, 4])[0],
                          "payment_terms_days": r.choice([30, 45, 60, 60, 90]), "currency": "GBP" if c == "GB" else "EUR" if c in ("PT", "IT", "FR", "DE") else "USD",
                          "incoterm": r.choice(["FOB", "FOB", "FCA", "EXW", "DDP"]), "onboarded_date": g.date_between(4000, 60),
                          "annual_spend_gbp": round(r.lognormvariate(14.2, 0.9), -3), "otif_pct_12m": round(r.uniform(78, 99), 1),
                          "risk_rating": r.choices(["low", "medium", "high", "critical"], [45, 38, 14, 3])[0], "account_manager_id": ""})
        for _ in range(r.choice([1, 2, 2, 3])):
            fid = f"FAC-{len(factories) + 1:04d}"
            factories.append({"factory_id": fid, "name": f"{g.fake.last_name()} {r.choice(['Mill', 'Factory', 'Works', 'Plant', 'Knitting', 'Dyehouse'])} {len(factories) + 1}",
                              "supplier_id": f"SUP-{i:04d}", "country": c, "city": g.fake.city(),
                              "capacity_units_month": r.randint(20, 400) * 1000, "workers": r.randint(80, 3000),
                              "certifications": ";".join(r.sample(["BSCI", "SEDEX", "OEKO-TEX", "GOTS", "ISO9001", "WRAP", "ISO14001"], r.randint(1, 3))),
                              "last_audit_date": g.date_between(700, 5), "audit_rating": r.choices("ABCD", [30, 45, 20, 5])[0],
                              "status": r.choices(["approved", "conditional", "suspended", "delisted"], [80, 14, 4, 2])[0]})
    out["suppliers"], out["factories"] = suppliers, factories
    fac_by_sup = {}
    for f in factories:
        fac_by_sup.setdefault(f["supplier_id"], []).append(f)

    section(5)
    # products: ~300 styles, 3 SKUs each
    products, style_no = [], 4000
    special = {5520: ("Womenswear", "Dresses"), 7731: ("Womenswear", "Outerwear"), 4410: ("Womenswear", "Trousers")}
    for i in range(300):
        style_no += r.randint(5, 18)
        if i in (90, 150, 30):
            style_no = {90: 5520, 150: 7731, 30: 4410}[i]
        dept, cat = special.get(style_no) or (None, None)
        dept = dept or r.choice(dept_list)
        cat = cat or r.choice(DEPTS[dept])
        sup = r.choice([s for s in suppliers if s["category_focus"] == dept and s["status"] != "exited"])
        fac = r.choice(fac_by_sup[sup["supplier_id"]])
        style = f"STY-T-{style_no}" if style_no == 4410 else f"STY-{style_no}"
        cost = round(r.uniform(2, 45) if dept not in ("Electricals",) else r.uniform(8, 90), 2)
        season = "AW26" if style_no in special else r.choice(["SS26", "AW26", "AW26", "SS27", "CORE"])
        price = round(cost * r.uniform(2.4, 4.2)) - 0.01
        hs = HS[dept] + str(r.randint(1000, 9999))
        lead = r.choice([45, 60, 75, 90, 105]) if sup["country"] not in ("GB", "PT", "TR", "PL", "DE", "FR") else r.choice([14, 21, 28])
        moq = r.choice([300, 500, 1000, 2000])
        weight = round(r.uniform(0.1, 1.2) if dept not in ("Home", "Electricals") else r.uniform(0.4, 4.5), 2)
        abc = r.choices("ABC", [20, 30, 50])[0] if style_no not in special else "A"
        launch = g.date_between(500, -60)
        sizes = ["10", "12", "14"] if dept == "Womenswear" else ["S", "M", "L"] if dept == "Menswear" else ["3-4Y", "5-6Y", "7-8Y"] if dept == "Kids" else ["ONE"]
        cols_ = r.sample(COLOURS, 1 if len(sizes) == 3 else 3)
        variants = [(c, s) for c in cols_ for s in sizes][:3]
        for c, s in variants:
            n = len(products) + 1
            products.append({"sku": f"SKU-{100000 + n * 7:06d}", "style_id": style, "name": f"{c} {cat.rstrip('s')} {s}".replace("ONE", "").strip(),
                             "department": dept, "category": cat, "subcategory": cat, "colour": c, "size": s, "season": season,
                             "brand": "Harbour & Vale" if r.random() < 0.8 else r.choice(["Vale Home", "H&V Studio", "Harbour Kids"]),
                             "supplier_id": sup["supplier_id"], "factory_id": fac["factory_id"], "country_of_origin": sup["country"],
                             "hs_code": hs, "unit_cost_gbp": cost,
                             "retail_price_gbp": price, "launch_date": launch,
                             "status": "new" if launch > as_of - timedelta(30) else r.choices(["active", "clearance", "discontinued"], [85, 10, 5])[0],
                             "abc_class": abc,
                             "hazmat": "li_ion_battery" if dept == "Electricals" and r.random() < 0.6 else "flammable_liquid" if cat == "Fragrance" else "aerosol" if cat == "Haircare" and r.random() < 0.5 else "none",
                             "pack_type": "hanging" if dept in ("Womenswear", "Menswear") and cat in ("Dresses", "Outerwear", "Shirts") else "carton" if dept in ("Home", "Electricals") else "polybag",
                             "weight_kg": weight,
                             "lead_time_days": lead,
                             "moq": moq})
    # legacy SKUs named in the questions
    for sku, name, dept, cat in (("PF-220", "Portable Rechargeable Desk Fan", "Electricals", "Personal Care"), ("K-1700", "1.7L Glass Kettle", "Electricals", "Small Appliances")):
        p = dict(r.choice([x for x in products if x["department"] == dept]))
        products.append(p | {"sku": sku, "style_id": f"STY-{sku}", "name": name, "category": cat, "subcategory": cat, "size": "ONE", "abc_class": "A", "status": "active", "hazmat": "li_ion_battery" if sku == "PF-220" else "none", "launch_date": g.days_ago(400)})
    out["products"] = products

    section(6)
    out["carriers"] = [{"carrier_id": f"CAR-{i:03d}", "name": n, "mode": m, "scope": s, "country": c,
                        "contract_end": g.date_between(-30, -700)} for i, (n, m, s, c) in enumerate([
        ("Northline Haulage", "road", "UK domestic", "GB"), ("Midshires Transport", "road", "UK domestic", "GB"),
        ("Pennine Freight", "road", "UK domestic", "GB"), ("EuroLink Trucking", "road", "EU", "NL"),
        ("Oceanic Container Line", "ocean", "global", "DK"), ("Pacific Star Shipping", "ocean", "global", "SG"),
        ("Meridian Ocean Lines", "ocean", "global", "CH"), ("SkyBridge Air Cargo", "air", "global", "GB"),
        ("Globex Forwarding", "forwarder", "global", "DE"), ("Atlas Logistics Partners", "forwarder", "global", "HK"),
        ("SwiftParcel", "parcel", "UK domestic", "GB"), ("ParcelPoint Express", "parcel", "UK and EU", "GB"),
        ("DoorStep Couriers", "parcel", "UK domestic", "GB"), ("ContinentalPost", "parcel", "EU", "DE"),
        ("Liberty Freight US", "road", "US domestic", "US"), ("Transalpine Rail Cargo", "rail", "Asia-Europe", "PL"),
        ("Harbour Shuttle", "road", "UK port drayage", "GB"), ("AeroFast Couriers", "air", "global", "US")], 1)]
    out["ports"] = [{"port_code": c, "name": n, "country": k, "region": rg} for c, n, k, rg in PORTS]

    section(7)
    # employees
    emps, n = [], 0

    def emp(role, dept, site, shift="office", mgr=""):
        nonlocal n
        n += 1
        e = {"employee_id": f"EMP-{n:05d}", "name": g.fake.name(), "role": role, "department": dept, "site_id": site,
             "shift": shift, "start_date": g.date_between(5000, 0), "manager_id": mgr,
             "status": r.choices(["active", "leaver", "agency"], [90, 4, 6])[0] if shift != "office" else "active"}
        emps.append(e)
        return e["employee_id"]
    ceo = emp("Chief Executive Officer", "Executive", "HQ1")
    for role, dept in (("Chief Financial Officer", "Finance"), ("Chief Operating Officer", "Operations"),
                       ("Supply Chain Director", "Supply Chain"), ("Commercial Director", "Commercial"),
                       ("Chief Information Officer", "Technology"), ("Chief People Officer", "People"),
                       ("Sourcing Director", "Sourcing"), ("Head of Sustainability", "Sustainability")):
        emp(role, dept, "HQ1", mgr=ceo)
    for role, dept, k in (("Buyer", "Buying", 14), ("Merchandiser", "Merchandising", 12), ("Demand Planner", "Planning", 8),
                          ("Supply Planner", "Planning", 6), ("Category Manager", "Commercial", 7), ("Sourcing Manager", "Sourcing", 6),
                          ("QA Technologist", "Quality", 6), ("Product Developer", "Product", 8), ("Financial Analyst", "Finance", 8),
                          ("Management Accountant", "Finance", 5), ("Transport Planner", "Logistics", 5), ("Data Analyst", "Technology", 6),
                          ("Compliance Manager", "Legal & Compliance", 4), ("Sustainability Analyst", "Sustainability", 3)):
        for _ in range(k):
            emp(role, dept, "HQ1" if r.random() < 0.85 else "HK1", mgr="EMP-00002")
    for dc in ("DC1", "DC2", "DC3", "DC4", "DC5"):
        gm = emp("Warehouse Manager", "Logistics", dc)
        size = {"DC1": 70, "DC2": 55, "DC3": 35, "DC4": 25, "DC5": 15}[dc]
        for shift in ("early", "late", "night"):
            sm = emp("Shift Manager", "Logistics", dc, shift, gm)
            for _ in range(size // 3):
                emp(r.choice(["Picker/Packer", "Picker/Packer", "Forklift Operator", "Goods-in Clerk", "Inventory Controller", "Despatch Operative"]),
                    "Logistics", dc, shift, sm)
    for s in stores:
        emp("Store Manager", "Stores", s["site_id"], "days")
    out["employees"] = emps
    buyers = [e["employee_id"] for e in emps if e["role"] == "Buyer"]
    sm_by = [e["employee_id"] for e in emps if e["role"] == "Sourcing Manager"]
    for s in suppliers:
        s["account_manager_id"] = r.choice(sm_by)

    section(8)
    ccs = []
    for i, (nm, fn, site) in enumerate([(f"{s['name']} Operations", "Logistics", s["site_id"]) for s in sites if s["type"] == "dc"]
                                       + [(f"{reg} Stores", "Stores", "") for reg in ("UK South", "UK Midlands", "UK North", "Scotland", "Ireland", "EU Central", "US")]
                                       + [(f, f, "HQ1") for f in ("Buying", "Merchandising", "Planning", "Sourcing", "Quality", "Product Development", "Finance", "Technology", "People", "Marketing", "E-commerce", "Transport", "Sustainability", "Legal", "Executive")], 1):
        ccs.append({"cost_centre_id": f"CC-{2100 + i}", "name": nm, "function": fn, "site_id": site,
                    "entity_id": next((s["entity_id"] for s in sites if s["site_id"] == site), "LE-UK"),
                    "owner_id": r.choice(emps[:9])["employee_id"]})
    out["cost_centres"] = ccs

    section(9)
    out["partners"] = [{"partner_id": f"PTN-{i:03d}", "name": n, "type": t, "country": c, "since": g.date_between(3000, 100),
                        "status": r.choices(["active", "on_hold", "ended"], [85, 10, 5])[0]} for i, (n, t, c) in enumerate(
        [(f"{g.fake.company()} Department Stores", "wholesale", r.choice(["GB", "IE", "DE", "FR", "NL"])) for _ in range(10)]
        + [(f"{g.fake.last_name()} Retail Franchise", "franchise", c) for c in ("AE", "SA", "QA", "KW", "IN", "CY", "MT", "IS")]
        + [("Amazon UK", "marketplace", "GB"), ("Zalando", "marketplace", "DE"), ("ASOS Marketplace", "marketplace", "GB"),
           ("eBay UK", "marketplace", "GB"), ("OnBuy", "marketplace", "GB")], 1)]

    section(10)
    customers = []
    for i in range(1, 3001):
        c = r.choices(["GB", "IE", "DE", "NL", "FR", "US"], [80, 6, 5, 3, 3, 3])[0]
        customers.append({"customer_id": f"CUS-{i:06d}", "segment": r.choices(["loyal", "new", "lapsed", "high_value", "occasional"], [25, 15, 20, 8, 32])[0],
                          "region": r.choice(["UK South", "UK Midlands", "UK North", "Scotland"]) if c == "GB" else c, "country": c,
                          "joined_date": g.date_between(3000, 0), "loyalty_tier": r.choices(["none", "silver", "gold", "platinum"], [50, 30, 15, 5])[0]})
    out["customers"] = customers

    section(11)
    orders = []
    for day in range(120, 0, -1):
        dt = as_of - timedelta(day)
        for _ in range(r.randint(90, 150) + (40 if dt.weekday() == 6 else 0)):
            cu = r.choice(customers)
            ch = r.choices(["web", "app", "click_collect", "marketplace"], [45, 30, 18, 7])[0]
            units = r.choices([1, 2, 3, 4, 6], [40, 30, 15, 10, 5])[0]
            status = "delivered" if day > 7 else r.choice(["placed", "picking", "shipped", "delivered"])
            status = r.choices([status, "cancelled", "returned", "part_returned"], [80, 3, 9, 8])[0] if day > 7 else status
            orders.append({"order_id": f"ORD-{dt.year}-{len(orders) + 100001:07d}", "customer_id": cu["customer_id"], "order_date": dt,
                           "channel": ch, "fulfil_site_id": "DC4" if cu["country"] in ("DE", "NL", "FR") else "DC5" if cu["country"] == "US" else ("DC2" if ch != "click_collect" else "DC1"),
                           "country": cu["country"], "units": units, "value_gbp": round(units * r.uniform(12, 48), 2),
                           "delivery_service": "collect" if ch == "click_collect" else r.choices(["standard", "next_day", "same_day"], [65, 30, 5])[0],
                           "status": status})
    out["orders"] = orders

    section(12)
    # purchase orders, lines, shipments (last ~18 months plus forward orders)
    pos, lines, ships = [], [], []
    by_sup = {}
    for p in products:
        by_sup.setdefault(p["supplier_id"], []).append(p)
    sups = [s for s in suppliers if s["supplier_id"] in by_sup]
    for i in range(1, 2201):
        s = r.choice(sups)
        od = g.date_between(540, -20)
        far = s["country"] not in ("GB", "PT", "TR", "PL", "DE", "FR", "IT")
        mode = (r.choices(["sea", "air", "rail"], [86, 10, 4])[0] if far else "road")
        lead = r.randint(60, 110) if mode == "sea" else r.randint(20, 40)
        ship_d = od + timedelta(lead - (35 if mode == "sea" else 5))
        due = od + timedelta(lead)
        dest = r.choices(["DC1", "DC2", "DC3", "DC4", "DC5"], [45, 25, 12, 12, 6])[0]
        if due < as_of - timedelta(30):
            st = r.choices(["closed", "received", "cancelled"], [80, 15, 5])[0]
        elif due < as_of:
            st = r.choice(["received", "shipped", "shipped"])
        elif ship_d < as_of:
            st = "shipped"
        elif od <= as_of:
            st = r.choice(["open", "confirmed", "confirmed"])
        else:
            st = "draft"
        po = f"PO-{od.year}-{i + 4000:06d}"
        cur = s["currency"]
        fx = {"GBP": 1, "EUR": 1.17, "USD": 1.27}[cur]
        tu, tv = 0, 0.0
        for ln, p in enumerate(r.sample(by_sup[s["supplier_id"]], min(len(by_sup[s["supplier_id"]]), r.randint(1, 5))), 1):
            q = r.choice([500, 1000, 1500, 2000, 3000, 5000])
            rec = q if st in ("closed", "received") else 0
            if st in ("closed", "received") and r.random() < 0.12:
                rec = int(q * r.uniform(0.85, 1.03))
            uc = round(p["unit_cost_gbp"] * fx * 0.82, 2)
            lines.append({"po_id": po, "line_no": ln, "sku": p["sku"], "qty_ordered": q, "unit_cost": uc, "qty_received": rec})
            tu, tv = tu + q, tv + q * uc
        pos.append({"po_id": po, "supplier_id": s["supplier_id"], "factory_id": r.choice(fac_by_sup[s["supplier_id"]])["factory_id"],
                    "order_date": od, "ship_date": ship_d, "due_date": due, "dest_site_id": dest, "mode": mode,
                    "incoterm": s["incoterm"], "currency": cur, "season": r.choice(["SS26", "AW26", "SS27"]), "total_units": tu,
                    "total_value": round(tv, 2), "buyer_id": r.choice(buyers), "status": st})
        if st in ("shipped", "received", "closed") or (st == "confirmed" and ship_d < as_of + timedelta(10)):
            op = r.choice(ORIGIN_PORT.get(s["country"], ["CNSHA"]))
            transit = {"sea": r.randint(28, 42), "air": r.randint(3, 6), "rail": r.randint(18, 24), "road": r.randint(2, 5)}[mode]
            etd = ship_d
            eta = etd + timedelta(transit)
            atd = etd + timedelta(r.choice([0, 0, 1, 2, 4])) if etd <= as_of else None
            late = r.random() < 0.18
            ata = (eta + timedelta(r.randint(3, 14) if late else r.randint(-1, 2))) if atd and eta < as_of - timedelta(3) else None
            sst = "delivered" if ata else ("booked" if not atd else ("delayed" if late else r.choice(["in_transit", "in_transit", "at_port", "customs_hold"])))
            ships.append({"shipment_id": f"SHP-{len(ships) + 1:07d}", "po_id": po,
                          "carrier_id": r.choice(["CAR-005", "CAR-006", "CAR-007", "CAR-009", "CAR-010"]) if mode == "sea" else "CAR-008" if mode == "air" else "CAR-016" if mode == "rail" else "CAR-004",
                          "mode": mode, "origin_port": op, "dest_port": DC_PORT[dest], "container_no": f"{r.choice(['MSKU', 'OOLU', 'CMAU', 'HLXU'])}{r.randint(1000000, 9999999)}" if mode == "sea" else "",
                          "teu": round(tu / 4500, 1) if mode == "sea" else 0.0, "etd": etd, "atd": atd, "eta": eta, "ata": ata, "status": sst})
    out["purchase_orders"], out["po_lines"], out["shipments"] = pos, lines, ships

    section(13)
    # weekly sales, last 52 weeks
    sales = []
    for p in products:
        base = {"A": 260, "B": 90, "C": 25}[p["abc_class"]] * r.uniform(0.6, 1.4)
        for wk in g.weeks(52):
            if wk < p["launch_date"] - timedelta(7):
                continue
            seas = 1.8 if wk.month in (11, 12) else 0.8 if wk.month in (1, 2) else 1.0
            u = max(0, int(r.gauss(base * seas, base * 0.25)))
            on = int(u * r.uniform(0.25, 0.45))
            md = p["retail_price_gbp"] * r.uniform(0.0, 0.3) if p["status"] == "clearance" or wk.month in (1, 7) else 0
            asp = p["retail_price_gbp"] - md
            sales.append({"sku": p["sku"], "week_start": wk, "store_units": u - on, "online_units": on,
                          "revenue_gbp": round(u * asp / 1.2, 2), "avg_price_gbp": round(asp, 2), "markdown_gbp": round(md * u, 2)})
    out["sales_weekly"] = sales

    section(14)
    stock = []
    for p in products:
        for dc in r.sample(["DC1", "DC2", "DC3", "DC4", "DC5"], r.randint(1, 4)):
            oh = r.randint(0, 6000) if p["status"] != "discontinued" else r.randint(0, 200)
            al = int(oh * r.uniform(0, 0.4))
            stock.append({"sku": p["sku"], "site_id": dc, "on_hand": oh, "allocated": al, "available": oh - al,
                          "on_order": r.choice([0, 0, 1000, 2000, 5000]), "stock_value_gbp": round(oh * p["unit_cost_gbp"], 2)})
    out["dc_stock"] = stock
    return out
