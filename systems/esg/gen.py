"""ESG data: FY26 emissions by scope/category/supplier/SKU, factor library, targets, initiatives, gaps, submissions."""
from datetime import date, timedelta

SCOPE2_YEARS = (2023, 2024, 2025, 2026)


def _months_back(d, n):
    y, m = d.year, d.month - n
    while m <= 0:
        y, m = y - 1, m + 12
    return date(y, m, 1)


def generate(g):
    r = g.rng
    A = g.as_of
    suppliers = g.master("suppliers")
    products = [p for p in g.master("products") if p.get("status") != "new"]   # new launches have no purchases yet
    sup_by = {s["supplier_id"]: s for s in suppliers}
    psup = sorted({p["supplier_id"] for p in products})

    # ------------------------------------------------------------------ emission factors
    F = {}          # key -> row
    order = []

    def ef(key, name, material, mode, value, unit, source, version, rating, vf, vt, region, unc):
        order.append(key)
        F[key] = dict(factor_id=f"EF-2026-{len(order):04d}", factor_name=name, material=material, transport_mode=mode,
                      kg_co2e_per_unit=value, unit=unit, source=source, version=version, data_quality_rating=rating,
                      valid_from=A - timedelta(days=vf), valid_to=A + timedelta(days=vt), region=region,
                      uncertainty_pct=unc)

    kgf = "kg CO2e per kg fibre"
    ef("poly_asia", "Polyester (virgin) fibre production, Asia", "polyester", None, 6.4, kgf, "Higg MSI", 2, "B", 250, 400, "Asia", 15)
    ef("poly_eu", "Polyester (virgin) fibre production, EU", "polyester", None, 5.1, kgf, "DEFRA", 2, "B", 250, 400, "EU", 15)
    ef("rpoly_asia", "Recycled polyester (rPET) fibre production, Asia", "recycled_polyester", None, 2.6, kgf, "supplier_data", 1, "D", 250, 400, "Asia", 45)
    ef("rpoly_eu", "Recycled polyester (rPET) fibre production, EU", "recycled_polyester", None, 2.3, kgf, "Textile Exchange LCA", 1, "C", 250, 400, "EU", 25)
    ef("cot_in", "Conventional cotton fibre production, India", "cotton", None, 5.9, kgf, "Cotton Inc LCA", 2, "B", 250, 400, "Asia", 20)
    ef("cot_cn", "Conventional cotton fibre production, China", "cotton", None, 6.5, kgf, "Higg MSI", 2, "C", 250, 400, "Asia", 30)
    ef("cot_tr", "Conventional cotton fibre production, Turkey", "cotton", None, 5.2, kgf, "DEFRA", 2, "B", 250, 400, "EU", 20)
    ef("ocot_in", "Organic cotton fibre production, India", "organic_cotton", None, 3.1, kgf, "Textile Exchange LCA", 1, "B", 250, 400, "Asia", 20)
    ef("ocot_tr", "Organic cotton fibre production, Turkey", "organic_cotton", None, 2.8, kgf, "supplier_data", 1, "C", 250, 400, "EU", 35)
    ef("nylon", "Nylon 6,6 fibre production, Asia", "nylon", None, 7.2, kgf, "Higg MSI", 1, "C", 250, 400, "Asia", 30)
    ef("wool_uk", "Wool fibre production, UK", "wool", None, 11.7, kgf, "DEFRA", 1, "C", 250, 400, "UK", 35)
    ef("eeio_app", "Apparel and accessories manufacturing, spend-based", "apparel_manufacturing", None, 0.42, "kg CO2e per GBP spend", "DEFRA EEIO", 3, "D", 250, 400, "Global", 60)
    ef("eeio_elec", "Electrical goods manufacturing, spend-based", "electronics", None, 0.38, "kg CO2e per GBP spend", "DEFRA EEIO", 3, "D", 250, 400, "Global", 60)
    ef("eeio_home", "Homewares manufacturing, spend-based", "homewares", None, 0.36, "kg CO2e per GBP spend", "DEFRA EEIO", 3, "D", 250, 400, "Global", 60)
    ef("eeio_beauty", "Beauty and personal care manufacturing, spend-based", "beauty", None, 0.30, "kg CO2e per GBP spend", "DEFRA EEIO", 3, "D", 250, 400, "Global", 60)
    ef("proc_primary", "Factory processing, supplier-reported (CDP / Higg FEM)", "processing", None, 0.0, "kg CO2e per unit (supplier-reported)", "supplier_data", 1, "B", 250, 400, "Global", 20)
    ef("proc_est", "Factory processing, spend-based estimate", "processing", None, 0.0, "kg CO2e per GBP spend", "DEFRA EEIO", 3, "D", 250, 400, "Global", 60)
    ef("freight_sea", "Sea freight, container average (GLEC)", "freight", "sea", 0.0085, "kg CO2e per tonne-km", "GLEC", 1, "B", 400, 400, "Global", 20)
    ef("freight_air", "Air freight, long haul (DEFRA)", "freight", "air", 0.55, "kg CO2e per tonne-km", "DEFRA", 1, "B", 400, 400, "Global", 20)
    ef("freight_road", "Road freight, HGV average laden (DEFRA)", "freight", "truck", 0.095, "kg CO2e per tonne-km", "DEFRA", 1, "A", 400, 400, "Global", 10)
    ef("last_mile", "Last-mile parcel delivery, carrier-reported", "delivery", "truck", 0.0, "kg CO2e per parcel (carrier-reported)", "supplier_data", 1, "B", 250, 400, "UK", 20)
    ef("use_phase", "Use-phase electricity of sold electricals, spend-based", "use_of_sold_products", None, 0.0, "kg CO2e per unit sold", "internal model", 1, "D", 250, 400, "UK", 60)
    ef("eol", "End-of-life treatment of textiles and electricals", "end_of_life", None, 0.0, "kg CO2e per tonne waste", "DEFRA", 1, "C", 250, 400, "UK", 40)
    ef("travel", "Business travel (air, rail, hotel), mixed", "travel", None, 0.0, "kg CO2e per trip", "DEFRA", 1, "B", 250, 400, "Global", 15)
    ef("commute", "Employee commuting, survey-based", "commuting", None, 0.0, "kg CO2e per employee-year", "DEFRA", 1, "D", 250, 400, "UK", 50)
    ef("diesel", "Diesel (fleet), per litre", "diesel", None, 2.51, "kg CO2e per litre", "DEFRA", 1, "A", 250, 400, "UK", 5)
    ef("natgas", "Natural gas (heating), per kWh", "natural_gas", None, 0.183, "kg CO2e per kWh", "DEFRA", 1, "A", 250, 400, "UK", 5)
    ef("r410a", "Refrigerant R410A leakage", "refrigerant", None, 2088.0, "kg CO2e per kg", "DEFRA", 1, "B", 250, 400, "Global", 20)
    # grid factors: 2025 version (valid to last year-end) and 2026 version
    GRID = {"GB": ("UK", 0.207, 0.193), "NL": ("Netherlands", 0.300, 0.288), "US": ("US (RFC East)", 0.370, 0.352),
            "PL": ("Poland", 0.660, 0.620), "DE": ("Germany", 0.380, 0.360), "HK": ("Hong Kong", 0.700, 0.680)}
    for cc, (nm, f25, f26) in GRID.items():
        ef(f"grid_{cc}_25", f"{nm} grid electricity, location-based (2025 factor set)", "electricity", None, f25, "kg CO2e per kWh",
           "IEA / DEFRA", 1, "A", 700, -280, "UK" if cc == "GB" else ("EU" if cc in ("NL", "PL", "DE") else "Global"), 5)
        ef(f"grid_{cc}_26", f"{nm} grid electricity, location-based (2026 factor set)", "electricity", None, f26, "kg CO2e per kWh",
           "IEA / DEFRA", 2, "A", 280, 450, "UK" if cc == "GB" else ("EU" if cc in ("NL", "PL", "DE") else "Global"), 5)
    ef("mkt_gb_26", "UK supplier-specific electricity, market-based (REGO-backed, partial)", "electricity", None, 0.1825, "kg CO2e per kWh",
       "supplier_data", 1, "B", 280, 450, "UK", 15)
    emission_factors = [F[k] for k in order]

    # ------------------------------------------------------------------ scope 2 history (per site)
    S2SITES = ["DC1", "DC2", "DC3", "DC4", "DC5", "DC6", "DC7", "DC8", "HQ1", "HK1"]
    SITE_CC = {"DC1": "GB", "DC2": "GB", "DC3": "GB", "DC4": "NL", "DC5": "US", "DC6": "GB", "DC7": "PL", "DC8": "DE",
               "HQ1": "GB", "HK1": "HK"}
    KWH25 = {"DC1": 13.8e6, "DC2": 10.9e6, "DC3": 6.4e6, "DC4": 4.9e6, "DC5": 3.7e6, "DC6": 4.4e6, "DC7": 4.0e6,
             "DC8": 3.0e6, "HQ1": 1.2e6, "HK1": 0.34e6}
    KWH_TREND = {2023: 1.03, 2024: 1.015, 2025: 1.0, 2026: 0.99}
    scope2_history = []
    for yr in SCOPE2_YEARS:
        for s in S2SITES:
            cc = SITE_CC[s]
            kwh = round(KWH25[s] * KWH_TREND[yr] * (1 + (r.random() - 0.5) * 0.01))
            grid = GRID[cc][2] if yr == 2026 else GRID[cc][1]
            gkey = f"grid_{cc}_26" if yr == 2026 else f"grid_{cc}_25"
            method, fac, fid, src, inb = "location_based", grid, F[gkey]["factor_id"], F[gkey]["source"], True
            bnd = "operational_control"
            note = ""
            if yr == 2026 and s in ("DC1", "DC2", "DC3"):
                method, fac, fid, src = "market_based", 0.1825, F["mkt_gb_26"]["factor_id"], "supplier_data (REGO-backed contract)"
                note = ("Switched from location-based to market-based this year after the REGO-backed supply contract "
                        "started; the location-based grid factor is shown alongside for comparison.")
            if yr == 2026 and s == "DC6":
                inb = False
                bnd = "excluded (3PL operational control)"
                note = ("Removed from the reporting boundary this year: operational control passed to the 3PL operator "
                        "and the site is now reported under its Scope 3 (downstream leased assets).")
            em = round(kwh * fac / 1000.0, 2) if inb else 0.0
            scope2_history.append({"year": yr, "site_id": s, "kwh_consumed": kwh, "emissions_tonnes_co2e": em,
                                   "factor_kg_per_kwh": fac, "grid_factor_kg_per_kwh": grid, "factor_source": src,
                                   "emission_factor_id": fid, "method": method, "boundary": bnd, "in_boundary": inb,
                                   "notes": note, "updated_at": A})
    s2_by_year = {}
    for h in scope2_history:
        s2_by_year[h["year"]] = s2_by_year.get(h["year"], 0) + h["emissions_tonnes_co2e"]

    # ------------------------------------------------------------------ emissions
    emissions = []
    cnt = [0]

    def add(scope, cat, ghg, stage, tonnes, measured, d, fid, notes, sku=None, sup=None, site=None):
        cnt[0] += 1
        emissions.append({"emission_id": f"EMS-{cnt[0]:06d}", "scope": scope, "category": cat, "ghg_category": ghg,
                          "value_chain_stage": stage, "sku": sku, "supplier_id": sup, "site_id": site,
                          "tonnes_co2e": round(tonnes, 2), "is_measured": measured, "measurement_date": d,
                          "fiscal_year": 2026, "emission_factor_id": fid, "notes": notes, "updated_at": A})

    mdates = [A - timedelta(days=15 + 30 * k) for k in range(12)]
    # Scope 1
    for site, cat, total, fkey, meas, note in [
        ("DC1", "fleet", 1200, "diesel", True, "Fleet fuel cards, litres x factor"),
        ("DC2", "fleet", 800, "diesel", True, "Fleet fuel cards, litres x factor"),
        ("DC3", "fleet", 600, "diesel", True, "Fleet fuel cards, litres x factor"),
        ("DC1", "gas_heating", 700, "natgas", True, "Gas meter reads"),
        ("DC2", "gas_heating", 450, "natgas", True, "Gas meter reads"),
        ("DC3", "gas_heating", 350, "natgas", True, "Gas meter reads"),
        ("HQ1", "gas_heating", 150, "natgas", True, "Gas meter reads")]:
        for d in mdates:
            add("1", cat, "Scope 1 direct", "own operations", total / 12 * (1 + (r.random() - 0.5) * 0.2), meas, d,
                F[fkey]["factor_id"], note, site=site)
    for d in [A - timedelta(days=45 + 90 * k) for k in range(4)]:
        add("1", "refrigerants", "Scope 1 direct", "own operations", 250 * (1 + (r.random() - 0.5) * 0.2), False, d,
            F["r410a"]["factor_id"], "Estimated leakage across store estate from top-up logs")
    # Scope 2 from history (2026)
    for h in scope2_history:
        if h["year"] == 2026 and h["in_boundary"]:
            for d in mdates:
                add("2", "purchased_electricity", "Scope 2 purchased electricity", "own operations",
                    h["emissions_tonnes_co2e"] / 12 * (1 + (r.random() - 0.5) * 0.1), h["site_id"] not in ("HK1", "HQ1"),
                    d, h["emission_factor_id"], f"Electricity at {h['site_id']} ({h['method']})", site=h["site_id"])

    # Scope 3: purchased goods (materials + processing) by SKU, half-yearly
    MULT = {"Knitwear": 1.9, "Outerwear": 1.8, "Footwear": 1.6, "Small Appliances": 1.4, "Smart Home": 1.2, "Bedding": 1.3,
            "Towels": 1.2, "Bags": 1.2, "Dresses": 1.0, "Jewellery": 0.5, "Haircare": 0.5, "Skincare": 0.5,
            "Fragrance": 0.5, "Bodycare": 0.5, "Lighting": 0.9, "Audio": 1.1, "Personal Care": 0.8}
    # story hotspots: their share of purchased-goods emissions is pinned (annual spend no longer makes them the biggest)
    HOT = {"SUP-0057": 0.1180, "SUP-0074": 0.0790, "SUP-0011": 0.0570, "SUP-0036": 0.0670, "SUP-0049": 0.0630, "SUP-0038": 0.0590, "SUP-0072": 0.0564}
    MATS = {"Knitwear": ["wool_uk", "cot_in", "poly_asia"], "Outerwear": ["poly_asia", "poly_eu", "nylon"],
            "Footwear": ["nylon", "poly_asia"], "Bags": ["nylon", "poly_asia"], "Backpacks": ["nylon"],
            "Scarves": ["poly_asia", "wool_uk"], "T-Shirts": ["cot_in", "cot_cn", "ocot_in"],
            "Tops": ["cot_in", "cot_tr", "rpoly_asia", "ocot_tr"], "Babywear": ["cot_in", "ocot_in", "cot_tr"],
            "Nightwear": ["cot_cn", "cot_tr"], "Shirts": ["cot_tr", "cot_cn"], "Schoolwear": ["poly_asia", "cot_in"],
            "Dresses": ["poly_eu", "poly_asia", "rpoly_eu"], "Blouses": ["poly_eu", "poly_asia"],
            "Trousers": ["cot_cn", "poly_asia"], "Bedding": ["cot_in", "cot_tr"], "Towels": ["cot_in", "cot_tr"]}
    DEPT_EEIO = {"Electricals": "eeio_elec", "Home": "eeio_home", "Beauty": "eeio_beauty"}
    MAT_TOTAL, TRANS_TOTAL = 52000.0, 13000.0
    skus_by_sup = {}
    for p in products:
        skus_by_sup.setdefault(p["supplier_id"], []).append(p)
    raw_sup = {}
    for sid in psup:
        pl = skus_by_sup[sid]
        mean_mult = sum(MULT.get(p["category"], 0.8) for p in pl) / len(pl)
        raw_sup[sid] = float(sup_by[sid]["annual_spend_gbp"]) / 1000.0 * mean_mult * (0.8 + 0.45 * g.rng_for("rawsup", sid).random())
    rest = sum(v for s_, v in raw_sup.items() if s_ not in HOT)
    for s_, share in HOT.items():
        raw_sup[s_] = share * rest / (1 - sum(HOT.values()))
    k = MAT_TOTAL / sum(raw_sup.values())
    tot_sup = {s: v * k for s, v in raw_sup.items()}
    # suppliers sending primary data (largest hotspots deliberately stay estimated)
    cand = [s for s in psup if s not in HOT]
    PRIMARY = {"SUP-0044", "SUP-0049"} | set(r.sample([s for s in cand if s not in ("SUP-0044", "SUP-0049")], 40))
    hd = [A - timedelta(days=60), A - timedelta(days=240)]
    for sid in psup:
        pl = skus_by_sup[sid]
        w = [MULT.get(p["category"], 0.8) * (0.7 + 0.6 * g.rng_for("skuw", p["sku"]).random()) for p in pl]
        sw = sum(w)
        for p, wi in zip(pl, w):
            share = tot_sup[sid] * wi / sw
            if p["department"] in DEPT_EEIO:
                mkey = DEPT_EEIO[p["department"]]
            elif p["category"] in MATS:
                mkey = g.rng_for("mat", p["sku"]).choice(MATS[p["category"]])
            else:
                mkey = "eeio_app"
            for d in hd:
                add("3", "materials", "Cat 1 Purchased goods: raw materials", "upstream", share * 0.65 / 2, False, d,
                    F[mkey]["factor_id"], "Spend/volume-based estimate with library fibre factor", sku=p["sku"], sup=sid)
                pm = sid in PRIMARY
                add("3", "processing", "Cat 1 Purchased goods: manufacturing", "upstream", share * 0.35 / 2, pm, d,
                    F["proc_primary" if pm else "proc_est"]["factor_id"],
                    "Supplier-reported factory energy data" if pm else "Spend-based estimate (no supplier data)",
                    sku=p["sku"], sup=sid)
    # inbound transport per supplier (Cat 4)
    far = {"CN", "VN", "IN", "BD", "MX"}
    raw_t = {s: tot_sup[s] * (1.6 if sup_by[s]["country"] in far else 0.6) for s in psup}
    kt = TRANS_TOTAL / sum(raw_t.values())
    for sid in psup:
        for d in hd:
            add("3", "inbound_transport", "Cat 4 Upstream transport", "upstream", raw_t[sid] * kt / 2, sid in PRIMARY, d,
                F["freight_sea"]["factor_id"], "Carrier-reported tonne-km x mode factor" if sid in PRIMARY else "Estimated from PO weight and default lane",
                sup=sid)
    indirect = [s["supplier_id"] for s in suppliers if s["supplier_type"] == "indirect"]
    for sid in indirect:
        for d in hd:
            add("3", "indirect_purchases", "Cat 1 Purchased goods: indirect", "upstream", 3400.0 / len(indirect) / 2 * (0.6 + 0.8 * g.rng_for("indirect", sid).random()),
                False, d, F["eeio_home"]["factor_id"], "Spend-based estimate", sup=sid)
    for cat, ghg, stage, total, meas, fkey, note in [
        ("outbound_delivery", "Cat 9 Downstream transport", "downstream", 4200, True, "last_mile", "Carrier-reported parcel emissions"),
        ("use_of_sold_products", "Cat 11 Use of sold products", "downstream", 8500, False, "use_phase", "Modelled lifetime electricity of sold electricals"),
        ("end_of_life", "Cat 12 End-of-life of sold products", "downstream", 2800, False, "eol", "Waste-stream assumptions"),
        ("business_travel", "Cat 6 Business travel", "upstream", 850, True, "travel", "Travel booking data"),
        ("employee_commuting", "Cat 7 Employee commuting", "upstream", 1500, False, "commute", "Annual staff survey, extrapolated")]:
        for d in [A - timedelta(days=45 + 90 * kk) for kk in range(4)]:
            add("3", cat, ghg, stage, total / 4 * (1 + (r.random() - 0.5) * 0.1), meas, d, F[fkey]["factor_id"], note)

    # pin the FY26 Scope 3 total at 86,135 t (quoted by documents) by scaling the indirect-purchases estimate
    SCOPE3_TOTAL = 86135.0
    ind_rows = [e for e in emissions if e["scope"] == "3" and e["category"] == "indirect_purchases"]
    other3 = sum(e["tonnes_co2e"] for e in emissions if e["scope"] == "3" and e["category"] != "indirect_purchases")
    ind_sum = sum(e["tonnes_co2e"] for e in ind_rows)
    for e in ind_rows:
        e["tonnes_co2e"] = round(e["tonnes_co2e"] * (SCOPE3_TOTAL - other3) / ind_sum, 2)
    ind_rows[-1]["tonnes_co2e"] = round(ind_rows[-1]["tonnes_co2e"] + SCOPE3_TOTAL - other3 - sum(e["tonnes_co2e"] for e in ind_rows), 2)

    # per-supplier FY26 scope 3 totals (for ranking)
    sup_t = {}
    for e in emissions:
        if e["scope"] == "3" and e["supplier_id"] in tot_sup:
            sup_t[e["supplier_id"]] = sup_t.get(e["supplier_id"], 0) + e["tonnes_co2e"]
    rank = sorted(sup_t, key=lambda s: -sup_t[s])
    scope3_total = sum(e["tonnes_co2e"] for e in emissions if e["scope"] == "3")
    scope3_meas = sum(e["tonnes_co2e"] for e in emissions if e["scope"] == "3" and e["is_measured"])
    s3_meas_pct = round(100 * scope3_meas / scope3_total)
    s1_total = sum(e["tonnes_co2e"] for e in emissions if e["scope"] == "1")
    s2_total = sum(e["tonnes_co2e"] for e in emissions if e["scope"] == "2")

    # ------------------------------------------------------------------ annual history (before FY26)
    annual = []
    s1 = {2020: 6200, 2021: 6050, 2022: 5950, 2023: 5850, 2024: 5700, 2025: 5600}
    s2 = {2020: 19000, 2021: 18300, 2022: 17200}
    s3 = {2020: 100000, 2021: 98200, 2022: 96000, 2023: 93500, 2024: 91200, 2025: 89000}
    for y in range(2020, 2026):
        annual.append({"year": y, "scope": "1", "tonnes_co2e": s1[y], "basis": "reported inventory"})
        annual.append({"year": y, "scope": "2", "tonnes_co2e": s2.get(y, round(s2_by_year.get(y, 0), 2)), "basis": "reported inventory"})
        annual.append({"year": y, "scope": "3", "tonnes_co2e": s3[y], "basis": "reported inventory (restated for FY26 boundary)" if y < 2025 else "reported inventory"})

    # ------------------------------------------------------------------ targets
    reduction_targets = [
        {"target_id": "TRG-000001", "scope": "1", "baseline_year": 2020, "baseline_tonnes_co2e": 6200, "target_year": 2030,
         "target_tonnes_co2e": 3596, "reduction_pct": 42.0, "pathway": "SBTi 1.5C", "status": "validated",
         "notes": "Near-term Scope 1 target validated by SBTi."},
        {"target_id": "TRG-000002", "scope": "2", "baseline_year": 2020, "baseline_tonnes_co2e": 19000, "target_year": 2030,
         "target_tonnes_co2e": 11020, "reduction_pct": 42.0, "pathway": "SBTi 1.5C", "status": "validated",
         "notes": "Near-term Scope 2 target (location-based) validated by SBTi."},
        {"target_id": "TRG-000003", "scope": "3", "baseline_year": 2020, "baseline_tonnes_co2e": 100000, "target_year": 2030,
         "target_tonnes_co2e": 70000, "reduction_pct": 30.0, "pathway": "SBTi well-below 2C", "status": "submitted",
         "notes": "Absolute Scope 3 target submitted to SBTi, not yet validated; 30% is below the 1.5C-aligned ambition and "
                  "coverage of primary supplier data is low."},
        {"target_id": "TRG-000004", "scope": "3", "baseline_year": 2020, "baseline_tonnes_co2e": 100000, "target_year": 2040,
         "target_tonnes_co2e": 10000, "reduction_pct": 90.0, "pathway": "Net Zero 2040", "status": "draft",
         "notes": "Long-term net-zero Scope 3 target, board approval pending."}]

    # ------------------------------------------------------------------ initiatives
    def ini(n, name, desc, scope, cat, sav, cost, sd, cd, status, feas, act=None):
        return {"initiative_id": f"INI-2026-{n:04d}", "name": name, "description": desc, "scope": str(scope), "category": cat,
                "expected_savings_tonnes": sav, "cost_gbp": cost, "start_date": A + timedelta(days=sd),
                "completion_date": A + timedelta(days=cd), "status": status, "feasibility_rating": feas,
                "actual_savings_tonnes": act, "created_at": A - timedelta(days=200), "updated_at": A - timedelta(days=20)}
    reduction_initiatives = [
        ini(1, "Solar PV on DC1 and DC2 roofs", "Rooftop solar on Northampton and Daventry DCs", 2, "renewable_energy", 1100, 3200000, -150, 120, "in_progress", "high"),
        ini(2, "LED and BMS upgrade, 60 stores", "Lighting and building management upgrade", 2, "energy_efficiency", 650, 1100000, -400, -60, "completed", "high", 610),
        ini(3, "Electrify DC1 yard shunters and fleet", "EV tractors and shunters at Northampton", 1, "logistics", 420, 2400000, -100, 300, "in_progress", "medium"),
        ini(4, "Refrigerant leak reduction and R410A phase-out", "Leak detection and replacement across stores", 1, "energy_efficiency", 180, 260000, 30, 330, "planned", "high"),
        ini(5, "Supplier renewable electricity, wave 1", "Five tier-1 mills move to renewable power", 3, "renewable_energy", 1250, 420000, -120, 240, "in_progress", "medium"),
        ini(6, "Recycled polyester for core tees and fleece", "Pilot of rPET on core basics", 3, "recycled_materials", 700, 690000, -90, 270, "in_progress", "medium"),
        ini(7, "Air to sea freight shift pilot (10%)", "Move 10% of Asia air volume to sea", 3, "logistics", 520, 60000, -150, 90, "in_progress", "high"),
        ini(8, "Low-carbon packaging redesign", "Lighter, recycled packaging for inbound cartons", 3, "packaging", 380, 310000, 60, 400, "planned", "medium"),
        ini(9, "Supplier engagement programme (CDP supply chain)", "Engage top suppliers to report primary data and set targets", 3, "supplier_engagement", 900, 150000, 30, 500, "planned", "low"),
        ini(10, "Organic cotton transition for denim", "Switch denim range to organic cotton", 3, "recycled_materials", 650, 880000, 90, 450, "planned", "low"),
        ini(11, "Electric last-mile delivery partners", "Shift parcel carriers to EV vans", 3, "logistics", 420, 500000, 45, 420, "planned", "medium"),
        ini(12, "Product take-back and resale", "In-store take-back pilot", 3, "circular", 260, 240000, -60, 200, "in_progress", "medium"),
    ]

    # ------------------------------------------------------------------ data gaps / tasks / platform / regulations
    def gap(n, metric, desc, mat, reg, cov, eff, pri, ident, close, status, req):
        return {"gap_id": f"GAP-{n:06d}", "metric": metric, "description": desc, "materiality_score": mat,
                "regulatory_impact": reg, "coverage_pct": cov, "effort_to_close": eff, "priority": pri,
                "identified_date": A - timedelta(days=ident), "target_close_date": A + timedelta(days=close),
                "status": status, "required_by": req, "created_at": A - timedelta(days=ident)}
    esg_data_gaps = [
        gap(1, "Scope3_supplier_emissions", "Only supplier-reported (primary) data counts as measured; the rest of purchased-goods Scope 3 is spend-based estimates",
            95, "high", s3_meas_pct, "hard", "critical", 150, 240, "open", "CSRD ESRS E1, UK SRS, SBTi"),
        gap(2, "Product_footprints", "No product-level LCA footprints for most SKUs; category averages used", 78, "medium", 6, "hard", "high", 140, 300, "open", "EU Green Claims, CSRD ESRS E5"),
        gap(3, "Supplier_energy_mix", "Renewable electricity share not reported by most tier-1 suppliers", 66, "medium", 22, "medium", "high", 120, 200, "in_progress", "SBTi, CSRD ESRS E1"),
        gap(4, "Fibre_origin_traceability", "Fibre origin and certification not captured for recycled and organic claims", 72, "medium", 40, "hard", "high", 130, 330, "open", "EU Green Claims"),
        gap(5, "Scope3_downstream_categories", "Use-phase and end-of-life figures rely on generic assumptions", 62, "medium", 35, "medium", "medium", 110, 270, "open", "CSRD ESRS E1"),
        gap(6, "Scope2_site_energy_data", "Half-hourly meter data missing for a few smaller sites", 70, "high", 91, "easy", "medium", 100, 60, "in_progress", "UK SRS, CSRD ESRS E1"),
        gap(7, "Refrigerant_leakage", "Leak logs incomplete for stores", 45, "low", 55, "medium", "medium", 90, 180, "open", "UK SRS"),
        gap(8, "Waste_and_water", "Site waste and water volumes only partly captured", 35, "low", 70, "easy", "low", 80, 150, "open", "CSRD ESRS E3, E5"),
    ]
    regulations = [
        {"regulation_id": "REG-UK-TCFD", "name": "UK climate-related financial disclosures (Companies Act TCFD)", "jurisdiction": "UK",
         "requirement_type": "carbon_disclosure", "description": "Mandatory climate disclosures for large UK companies, already in force.",
         "applies_to_us": True, "in_scope_reason": "UK parent exceeds the large-company thresholds", "effective_date": A - timedelta(days=400),
         "scopes_covered": "1,2,3", "data_required": "Scope 1-3 emissions, targets, transition plan, governance", "url": "https://www.legislation.gov.uk"},
        {"regulation_id": "REG-EU-CSRD", "name": "Corporate Sustainability Reporting Directive (ESRS)", "jurisdiction": "EU",
         "requirement_type": "carbon_disclosure", "description": "Double-materiality reporting under ESRS for large EU entities, with limited assurance.",
         "applies_to_us": True, "in_scope_reason": "EU subsidiaries (Venlo, Lodz, Frankfurt DCs) exceed size thresholds", "effective_date": A + timedelta(days=180),
         "scopes_covered": "1,2,3", "data_required": "Scope 3 by category with primary-data share, energy mix, targets, value-chain metrics",
         "url": "https://finance.ec.europa.eu"},
        {"regulation_id": "REG-UK-SRS", "name": "UK Sustainability Reporting Standards (ISSB-based)", "jurisdiction": "UK",
         "requirement_type": "climate_risk", "description": "ISSB S1/S2-based UK standards expected to replace TCFD-style reporting.",
         "applies_to_us": True, "in_scope_reason": "Large UK listed-equivalent group", "effective_date": A + timedelta(days=400),
         "scopes_covered": "1,2,3", "data_required": "Scope 1-3, scenario analysis, financed impacts, industry metrics", "url": "https://www.gov.uk"},
        {"regulation_id": "REG-EU-GREENCLAIMS", "name": "EU Green Claims Directive", "jurisdiction": "EU",
         "requirement_type": "claims", "description": "Substantiation and verification of environmental claims before use.",
         "applies_to_us": True, "in_scope_reason": "We market products with environmental claims into the EU", "effective_date": A + timedelta(days=300),
         "scopes_covered": "product", "data_required": "Product LCA evidence, certification, traceability", "url": "https://environment.ec.europa.eu"},
        {"regulation_id": "REG-EU-CSDDD", "name": "Corporate Sustainability Due Diligence Directive", "jurisdiction": "EU",
         "requirement_type": "due_diligence", "description": "Value-chain due diligence for very large EU companies.",
         "applies_to_us": False, "in_scope_reason": "Below the EU turnover and employee thresholds", "effective_date": A + timedelta(days=700),
         "scopes_covered": "3", "data_required": "Supplier due diligence records", "url": "https://commission.europa.eu"},
        {"regulation_id": "REG-US-CA-SB253", "name": "California Climate Corporate Data Accountability Act", "jurisdiction": "US",
         "requirement_type": "carbon_disclosure", "description": "Scope 1-3 reporting for large companies doing business in California.",
         "applies_to_us": False, "in_scope_reason": "No California operations; US DC is in Ohio", "effective_date": A + timedelta(days=500),
         "scopes_covered": "1,2,3", "data_required": "Scope 1-3 emissions with assurance", "url": "https://leginfo.legislature.ca.gov"},
    ]
    platform_modules = [
        {"module": "Carbon accounting", "scopes_supported": "Scope 1, 2, 3", "frameworks": "GHG Protocol, TCFD, SBTi tracking", "status": "live",
         "addon_quote_gbp": 0, "notes": "Inventory by scope and category; Scope 3 category 1 spend-based and supplier-specific methods."},
        {"module": "Supplier ESG data portal", "scopes_supported": "Scope 1, 2, 3", "frameworks": "CDP supply chain, SBTi", "status": "live",
         "addon_quote_gbp": 0, "notes": "Supplier questionnaires, submissions and quality scoring."},
        {"module": "Targets and reduction planning", "scopes_supported": "Scope 1, 2, 3", "frameworks": "SBTi", "status": "live",
         "addon_quote_gbp": 0, "notes": "Targets, pathways and initiative tracking."},
        {"module": "Claims substantiation register", "scopes_supported": "n/a", "frameworks": "ASA, CMA", "status": "live",
         "addon_quote_gbp": 0, "notes": "Claims, evidence and review status."},
        {"module": "CSRD / ESRS reporting", "scopes_supported": "Scope 1, 2, 3", "frameworks": "CSRD ESRS E1-E5", "status": "not_licensed",
         "addon_quote_gbp": 85000, "notes": "Vendor add-on licence: ESRS data points, double-materiality workflow, audit trail. Configuration project is costed separately (IPT-900001, about 6 months in total)."},
        {"module": "UK SRS / ISSB reporting", "scopes_supported": "Scope 1, 2, 3", "frameworks": "UK SRS, ISSB S1/S2", "status": "planned",
         "addon_quote_gbp": 40000, "notes": "On vendor roadmap, no committed release date; interim use TCFD template."},
        {"module": "Product LCA footprinting", "scopes_supported": "Scope 3", "frameworks": "EU Green Claims, PEF", "status": "not_available",
         "addon_quote_gbp": 0, "notes": "Not offered by the platform; needs a third-party LCA tool."},
    ]

    # ------------------------------------------------------------------ supplier submissions / requests / sbti
    top25 = list(rank[:25])
    # story slots in the FY26 round (slot sets PEND / OVERDUE / LOWQ below): SUP-0074 overdue, SUP-0038 overdue,
    # SUP-0011 and SUP-0049 low quality, SUP-0057 / SUP-0036 / SUP-0072 submitted.
    for sid_, slot_ in (("SUP-0057", 1), ("SUP-0074", 2), ("SUP-0011", 3), ("SUP-0038", 4), ("SUP-0036", 5),
                        ("SUP-0049", 6), ("SUP-0072", 8)):
        j_ = top25.index(sid_)
        top25[slot_ - 1], top25[j_] = top25[j_], top25[slot_ - 1]
    PEND = {2, 4, 7, 9, 12, 15, 18, 22}
    OVERDUE = {2, 4, 9, 15}
    LOWQ = {3, 6, 11, 14, 20}
    supplier_submissions, data_requests = [], []
    sub_by = {}
    for i, sid in enumerate(top25, 1):
        rs = g.rng_for("submission", sid)
        pend = i in PEND
        overdue = i in OVERDUE
        deadline = A - timedelta(days=12) if overdue else A + timedelta(days=14)
        reqd = A - timedelta(days=45) if overdue else A - timedelta(days=30)
        if pend:
            q, comp, status, subd, note = 0, 0, "pending", None, "No response received"
            s1_, s2_, s3_ = False, False, False
        else:
            lowq = i in LOWQ
            q = rs.randint(28, 46) if lowq else rs.randint(62, 93)
            comp = round(rs.uniform(35, 55) if lowq else rs.uniform(72, 98), 1)
            status = "under_review" if lowq else rs.choice(["received", "approved"])
            subd = A - timedelta(days=rs.randint(3, 20))
            note = "Low quality: Scope 3 missing, estimates not evidenced" if lowq else "Data received"
            s1_, s2_, s3_ = True, True, (not lowq) and rs.random() > 0.4
        sub_by[sid] = (comp if not pend else None)
        supplier_submissions.append({"submission_id": f"SUB-{i:06d}", "supplier_id": sid, "submission_date": subd,
                                     "deadline_date": deadline, "data_quality_score": q, "completeness_pct": comp,
                                     "has_scope1": s1_, "has_scope2": s2_, "has_scope3": s3_, "status": status,
                                     "notes": note, "updated_at": A - timedelta(days=2)})
        data_requests.append({"request_id": f"REQ-{i:06d}", "supplier_id": sid, "request_date": reqd, "deadline_date": deadline,
                              "scopes_requested": "1,2,3", "status": "overdue" if overdue else ("sent" if pend else "received"),
                              "notes": "Annual ESG data request (FY26 round)", "sent_at": reqd})

    # priority ranking (same formula as the tool) to place SBTi statuses
    maxt = max(sup_t.values())
    maxs = max(float(sup_by[s]["annual_spend_gbp"]) for s in sup_t)
    prio = {}
    for s, t in sup_t.items():
        rd = sub_by.get(s)
        prio[s] = 100 * (0.7 * t / maxt + 0.1 * float(sup_by[s]["annual_spend_gbp"]) / maxs + 0.2 * (rd if rd is not None else 20) / 100)
    prank = sorted(prio, key=lambda s: -prio[s])
    forced = {"SUP-0049": "targets_set", "SUP-0038": "targets_set", "SUP-0072": "committed"}
    supplier_sbti = []
    for sid in psup:
        rs = g.rng_for("sbti", sid)
        if sid in forced:
            st = forced[sid]
        elif sid in prank[:14]:
            st = "none"
        else:
            st = rs.choices(["none", "committed", "targets_set"], [70, 18, 12])[0]
        supplier_sbti.append({"supplier_id": sid, "sbti_status": st,
                              "target_ambition": "1.5C" if st == "targets_set" else ("committed" if st == "committed" else None),
                              "target_year": 2030 if st == "targets_set" else None,
                              "status_date": A - timedelta(days=rs.randint(60, 600)) if st != "none" else None,
                              "notes": "SBTi target validated" if st == "targets_set" else ("Commitment letter signed, targets due" if st == "committed" else "No SBTi commitment on record")})

    # ------------------------------------------------------------------ claims (unchanged story-free register)
    claims_text = [("Made from 100% recycled materials", "apparel"), ("Carbon neutral shipping", "all"),
                   ("Organic cotton sourced", "apparel"), ("Sustainable production certified", "apparel"),
                   ("Fair trade partner", "accessories"), ("Plastic-free packaging", "all"), ("Zero waste manufacturing", "footwear")]
    claims_register = []
    for i, (txt, cat) in enumerate(claims_text):
        claims_register.append({"claim_id": f"CLM-2026-{i + 1:04d}", "claim_text": txt, "product_category": cat,
                                "risk_level": ["medium", "high", "low", "high", "low", "medium", "high"][i],
                                "substantiation_available": i in (2, 4, 5), "evidence_path": f"files/claim_{i + 1}_evidence.pdf" if i in (2, 4, 5) else None,
                                "review_status": "pending" if i in (0, 1, 3, 6) else "approved", "reviewed_by": None,
                                "reviewed_date": None, "notes": "", "created_at": A - timedelta(days=60 + 15 * i),
                                "updated_at": A - timedelta(days=10)})

    # ------------------------------------------------------------------ transport lanes
    LANES = [  # lane, mode, origin, dest, corridor, km, base factor, monthly tonnes (7 months)
        # INNSA-GBFXT is the biggest Asia sea lane in tms (about 607 t in six months, 142 t of it still by air); CNSHA-GBFXT is about a third of it
        ("INNSA-GBFXT-SEA", "sea", "INNSA", "GBFXT", "Asia-Europe", 12100, 0.0085, [480, 500, 520, 640, 720, 780, 840]),
        ("VNSGN-GBFXT-SEA", "sea", "VNSGN", "GBFXT", "Asia-Europe", 17900, 0.0085, [260, 270, 280, 340, 390, 420, 450]),
        ("INNSA-GBSOU-SEA", "sea", "INNSA", "GBSOU", "Asia-Europe", 11900, 0.0085, [180, 190, 200, 240, 280, 300, 320]),
        ("BDCGP-GBFXT-SEA", "sea", "BDCGP", "GBFXT", "Asia-Europe", 12800, 0.0085, [150, 150, 160, 200, 230, 250, 270]),
        ("CNSHA-GBFXT-SEA", "sea", "CNSHA", "GBFXT", "Asia-Europe", 19600, 0.0085, [150, 155, 160, 200, 230, 250, 270]),
        ("INNSA-GBFXT-AIR", "air", "INNSA", "GBFXT", "Asia-Europe", 7500, 0.55, [120, 115, 110, 90, 70, 60, 50]),
        ("MXZLO-GBFXT-SEA", "sea", "MXZLO", "GBFXT", "Americas-Europe", 14000, 0.0085, [90, 95, 95, 100, 120, 130, 140]),
        ("TRMER-GBFXT-ROAD", "truck", "TRMER", "GBFXT", "Intra-Europe", 3600, 0.095, [900, 920, 910, 900, 880, 870, 860]),
        ("DEHAM-GBFXT-ROAD", "truck", "DEHAM", "GBFXT", "Intra-Europe", 900, 0.095, [600, 610, 590, 600, 610, 600, 590]),
    ]
    months = [_months_back(A, 7 - i) for i in range(7)]       # oldest first, ends last full month
    v1_start = _months_back(A, 10)
    v2_start = months[4]
    BAD = 0.0215
    transport_factors, transport_emissions = [], []
    for lane, mode, o, d, cor, km, fb, vols in LANES:
        transport_factors.append({"lane_id": lane, "period_start": v1_start, "transport_mode": mode, "origin": o, "destination": d,
                                  "corridor": cor, "factor_kg_per_tonne_km": round(fb * (1 + (r.random() - 0.5) * 0.04), 5),
                                  "factor_source": "DEFRA 2025", "version": 1, "status": "superseded", "notes": "Annual factor set", "updated_at": A - timedelta(days=100)})
        bad = mode == "sea"
        v2 = BAD if bad else round(fb * 1.02, 5)
        transport_factors.append({"lane_id": lane, "period_start": v2_start, "transport_mode": mode, "origin": o, "destination": d,
                                  "corridor": cor, "factor_kg_per_tonne_km": v2,
                                  "factor_source": "bulk import (GLEC)" if bad else "DEFRA 2026", "version": 2, "status": "active",
                                  "notes": ("Bulk factor import: container-ship factor per TEU-km loaded as per tonne-km (about 2.5x too high)" if bad else "Annual factor set"),
                                  "updated_at": A - timedelta(days=95)})
        for m, v in zip(months, vols):
            transport_emissions.append({"lane_id": lane, "month_start": m, "tonnes_shipped": v, "distance_km": km,
                                        "tonne_km": v * km, "updated_at": A - timedelta(days=5)})

    return {"emissions": emissions, "emissions_annual": annual, "emission_factors": emission_factors,
            "reduction_targets": reduction_targets, "reduction_initiatives": reduction_initiatives,
            "esg_data_gaps": esg_data_gaps, "esg_gap_tasks": [], "supplier_submissions": supplier_submissions,
            "claims_register": claims_register, "data_requests": data_requests, "scope2_history": scope2_history,
            "transport_factors": transport_factors, "transport_emissions": transport_emissions,
            "regulations": regulations, "platform_modules": platform_modules, "supplier_sbti": supplier_sbti}
