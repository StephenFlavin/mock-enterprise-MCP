"""Quality management data: production lots, inspections, incidents, holds, CARs, factory scorecards, pack damage.

Layout of the data
  * Story rows (planted, ids 91xxxx) are written by the helpers below and by seed/*.csv (ids 9000xx).
  * Generated background (ids 0xxxxx) only covers suppliers and factories that no story uses, so the story
    suppliers/factories/styles/pack types return exactly what the planted rows say.
"""
from datetime import datetime, timedelta

MULT = [0.85, 1.15, 1.0, 0.9, 1.1, 1.05, 0.95]

# Suppliers whose quality record is a planted story (all their factories are kept free of generated noise).
STORY_SUPPLIERS = {
    "SUP-0039", "SUP-0004", "SUP-0011",            # bedding shortlist (04:32:Q3)
    "SUP-0040", "SUP-0044", "SUP-0058",            # nearshore pilot suppliers (04:34:Q6)
    "SUP-0001", "SUP-0002", "SUP-0003",            # Asian comparators; SUP-0001 also style 5520 (02:21:Q1)
    "SUP-0053", "SUP-0055",                        # suppliers in trouble (04:32:Q6, 04:35:Q1)
    "SUP-0013", "SUP-0036", "SUP-0022",            # PF-220 / K-1700, style T-4410, style 7731
    "SUP-0064", "SUP-0042",                        # pink polyester blouse (05:42:Q1), shoe soles
    "SUP-0046", "SUP-0057", "SUP-0073",            # worst-audited factories FAC-0087/0107/0137 (05:42:Q4)
}
STYLES_WITH_REVIEWS = {"STY-5520", "STY-7731", "STY-T-4410", "STY-PF-220", "STY-K-1700"}

# Stock the WMS shows in quarantine at DC1/DC3 because of a quality hold (01:8:Q4): (sku, site, units)
HOLD_WAVE = [
    ("SKU-103507", "DC1", 867), ("SKU-100819", "DC3", 2939), ("SKU-101687", "DC1", 1027), ("SKU-104690", "DC3", 2757),
    ("SKU-104270", "DC1", 663), ("SKU-104053", "DC3", 2842), ("SKU-102723", "DC1", 876), ("SKU-103661", "DC3", 1752),
    ("SKU-101715", "DC1", 1058), ("SKU-101750", "DC3", 2879), ("SKU-103080", "DC1", 671), ("SKU-104284", "DC3", 2650),
    ("SKU-101869", "DC1", 696), ("SKU-106069", "DC3", 2496), ("SKU-102338", "DC1", 165),
]

# Scorecard trajectories: factory -> (defect% first week, defect% last week, critical first, critical last, on-time first, on-time last)
SCORECARD_STORY = {
    "FAC-0087": (3.4, 10.2, 0, 3, 89, 72),     # worst audit grade D, worsening
    "FAC-0107": (3.0, 8.6, 0, 2, 90, 76),
    "FAC-0137": (2.8, 7.8, 0, 2, 91, 78),
    "FAC-0002": (4.8, 5.1, 1, 1, 86, 84),      # known but stable problem (style 5520 zips)
    "FAC-0027": (4.7, 5.0, 1, 1, 85, 83),      # PF-220 / K-1700
    "FAC-0099": (3.4, 5.0, 0, 1, 88, 80),      # SUP-0053 slipping
    "FAC-0100": (3.0, 4.4, 0, 1, 88, 81),
    "FAC-0103": (3.0, 5.2, 0, 1, 90, 84),      # SUP-0055 safety test failures
    "FAC-0010": (2.8, 3.0, 0, 0, 92, 91), "FAC-0075": (1.2, 1.1, 0, 0, 96, 97), "FAC-0022": (4.6, 5.3, 0, 1, 86, 84),
}


def generate(g):
    r = g.rng
    as_of = g.as_of
    products = g.master("products")
    pby = {p["sku"]: p for p in products}
    factories = {f["factory_id"]: f for f in g.master("factories")}

    def ts(days_ago, hour=9, minute=0):
        return datetime.combine(as_of - timedelta(days=days_ago), datetime.min.time()) + timedelta(hours=hour, minutes=minute)

    def skus(fac, cat=None):
        return [p["sku"] for p in products if p["factory_id"] == fac and (cat is None or p["category"] == cat)]

    story_fac = {fid for fid, f in factories.items() if f["supplier_id"] in STORY_SUPPLIERS}
    story_skus = {p["sku"] for p in products if p["factory_id"] in story_fac or p["supplier_id"] in STORY_SUPPLIERS}

    lots, inspections, measurements, incidents, holds = [], [], [], [], []
    investigations, cars, scorecards, pack_damage, reviews = [], [], [], [], []
    n = {"lot": 0, "ins": 0, "msr": 0, "inc": 0, "hld": 0}

    def new_lot(sku, fac, days_ago, qty=None, batch=None, po=None):
        n["lot"] += 1
        lot = {
            "lot_id": f"LOT-{910000 + n['lot']}", "sku": sku, "batch_id": batch, "factory_id": fac, "po_id": po,
            "qty_produced": qty or r.randint(400, 2000), "produced_at": (as_of - timedelta(days=days_ago)),
            "status": "in_inspection", "lot_disposition": "pending",
            "created_at": ts(days_ago, 8), "updated_at": ts(max(days_ago - 5, 0), 10),
        }
        lots.append(lot)
        return lot

    def add_inspection(lot, itype, units, defects, days_ago, key=None):
        n["ins"] += 1
        pct = 100.0 * defects / units
        result = "pass" if pct <= 3.0 else ("conditional" if pct <= 5.5 else "fail")
        ins = {
            "inspection_id": f"INS-{910000 + n['ins']}", "lot_id": lot["lot_id"], "factory_id": lot["factory_id"],
            "inspection_type": itype, "units_inspected": units, "defects_found": defects, "pass_fail": result,
            "scheduled_at": ts(days_ago + 1, 9), "inspected_at": ts(days_ago, 13, r.randint(0, 59)),
            "created_at": ts(days_ago, 13, 30), "notes": None,
        }
        inspections.append(ins)
        return ins

    def program(fac, sku_list, count, rate, start, end, off=0):
        """`count` lots from `start` to `end` days ago, each with an inline and a final inspection near `rate` % defects."""
        out = []
        for i in range(count):
            d = start - round(i * (start - end) / max(count - 1, 1))
            lot = new_lot(sku_list[i % len(sku_list)], fac, d)
            m = MULT[(i + off) % len(MULT)]
            u1 = r.randint(60, 100)
            add_inspection(lot, "inline", u1, round(u1 * rate / 100 * MULT[(i + off + 3) % len(MULT)]), max(d - 1, 1))
            u2 = r.randint(120, 200)
            fin = add_inspection(lot, "final", u2, round(u2 * rate / 100 * m), max(d - 3, 1))
            if fin["pass_fail"] == "pass":
                lot["status"], lot["lot_disposition"] = ("released", "release") if d > 6 else ("in_inspection", "pending")
            elif fin["pass_fail"] == "conditional":
                lot["status"], lot["lot_disposition"] = ("reworked", "rework") if d > 20 else ("in_inspection", "pending")
            else:
                lot["status"], lot["lot_disposition"] = ("rejected", "reject") if d > 30 else ("in_inspection", "pending")
            out.append(lot)
        return out

    def incident(sku, fac, desc, sev, status, days_ago):
        n["inc"] += 1
        cand = [l for l in lots if l["sku"] == sku and l["factory_id"] == fac and (as_of - l["produced_at"]).days >= days_ago]
        lot = min(cand, key=lambda l: (as_of - l["produced_at"]).days - days_ago) if cand else None
        row = {"incident_id": f"INC-{910000 + n['inc']}", "sku": sku, "factory_id": fac, "lot_id": lot["lot_id"] if lot else None,
               "issue_description": desc, "severity": sev, "status": status, "created_at": ts(days_ago, 11),
               "updated_at": ts(max(days_ago - r.randint(1, 6), 0), 15)}
        incidents.append(row)
        return row

    # ---- 04:32:Q3 bedding shortlist: SUP-0039 clean, SUP-0004 middling, SUP-0011 poor ------------------------------------
    bed = {f: skus(f, "Bedding") for f in ("FAC-0075", "FAC-0010", "FAC-0022")}
    program("FAC-0075", bed["FAC-0075"], 8, 1.1, 80, 8)
    program("FAC-0010", bed["FAC-0010"], 6, 2.9, 78, 10, 2)
    program("FAC-0009", skus("FAC-0009", "Cookware"), 3, 3.4, 60, 12, 1)
    program("FAC-0022", bed["FAC-0022"], 6, 5.2, 78, 9, 4)
    incident(bed["FAC-0075"][0], "FAC-0075", "Care label printed with wrong wash temperature", "low", "closed", 55)
    incident(bed["FAC-0010"][0], "FAC-0010", "Duvet cover seam slippage above AQL limit", "medium", "resolved", 49)
    incident(bed["FAC-0010"][1], "FAC-0010", "Pillow filling weight under specification", "high", "investigating", 21)
    incident(bed["FAC-0022"][0], "FAC-0022", "Fabric weight below specification on duvet set", "medium", "closed", 68)
    incident(bed["FAC-0022"][1], "FAC-0022", "Seam failures on duvet covers at final inspection", "high", "investigating", 40)
    incident(bed["FAC-0022"][0], "FAC-0022", "Colour migration on first wash", "medium", "open", 25)
    incident(bed["FAC-0022"][2], "FAC-0022", "Flame-retardant treatment test failure on bedding batch", "critical", "open", 14)

    # ---- 04:34:Q6 nearshore pilot suppliers vs Asian comparators ---------------------------------------------------------
    program("FAC-0076", skus("FAC-0076"), 4, 0.8, 80, 9, 1)
    program("FAC-0077", skus("FAC-0077"), 4, 0.8, 76, 7, 3)
    program("FAC-0084", skus("FAC-0084"), 8, 1.5, 80, 6, 2)
    program("FAC-0110", skus("FAC-0110"), 8, 2.4, 80, 6, 5)
    incident(skus("FAC-0084")[0], "FAC-0084", "Button thread colour mismatch on shirts", "low", "closed", 33)
    incident(skus("FAC-0110")[0], "FAC-0110", "Skipped stitches on hems of outerwear", "medium", "resolved", 29)
    program("FAC-0001", skus("FAC-0001"), 6, 2.6, 80, 8, 3)
    program("FAC-0003", skus("FAC-0003"), 8, 3.3, 80, 6, 0)
    program("FAC-0005", skus("FAC-0005"), 5, 3.6, 78, 8, 2)
    program("FAC-0006", skus("FAC-0006"), 4, 4.3, 70, 10, 4)
    incident(skus("FAC-0001")[0], "FAC-0001", "Pilling above grade 3 after abrasion test", "low", "closed", 52)
    incident(skus("FAC-0003")[0], "FAC-0003", "Zip slider misalignment on outerwear", "medium", "resolved", 44)
    incident(skus("FAC-0005")[0], "FAC-0005", "Press-stud pull strength below safety limit on babywear", "high", "investigating", 19)
    incident(skus("FAC-0006")[0], "FAC-0006", "Flammability label missing on nightwear", "medium", "closed", 47)

    # ---- 04:32:Q6 / 04:35:Q1 suppliers in trouble ------------------------------------------------------------------------
    # SUP-0053 (Supplier S): defects up from ~2.3% two quarters ago to ~5.4% this quarter, incidents 2 -> 5
    program("FAC-0099", skus("FAC-0099"), 5, 2.4, 170, 100, 1)
    program("FAC-0100", skus("FAC-0100"), 4, 2.2, 165, 96, 3)
    program("FAC-0099", skus("FAC-0099"), 6, 5.6, 84, 6, 2)
    program("FAC-0100", skus("FAC-0100"), 5, 5.1, 80, 8, 0)
    incident(skus("FAC-0099")[0], "FAC-0099", "Glass tumbler wall thickness variation", "medium", "resolved", 150)
    incident(skus("FAC-0100")[0], "FAC-0100", "Lamp base wobble at final inspection", "medium", "resolved", 120)
    incident(skus("FAC-0099")[1], "FAC-0099", "Glass cracks found at receiving inspection", "high", "investigating", 38)
    incident(skus("FAC-0099")[2], "FAC-0099", "Decoration print rubs off in dishwasher test", "medium", "open", 28)
    incident(skus("FAC-0100")[0], "FAC-0100", "Electrical insulation test failure on table lamps", "high", "open", 20)
    incident(skus("FAC-0100")[1], "FAC-0100", "Plug pin dimensions out of tolerance", "medium", "open", 11)
    incident(skus("FAC-0099")[0], "FAC-0099", "Mug handles detaching under load", "medium", "open", 6)
    # SUP-0055: three smart-home controller batches failed electrical safety testing this quarter
    sh = ["SKU-103661", "SKU-103668", "SKU-103675"]
    for i, (sku, d, rate) in enumerate(zip(sh, (62, 41, 19), (9.0, 8.4, 9.6))):
        lot = new_lot(sku, "FAC-0103", d)
        add_inspection(lot, "inline", 80, round(80 * rate / 100), d - 1)
        add_inspection(lot, "final", 150, round(150 * rate / 100), d - 3)
        lot["status"], lot["lot_disposition"] = ("rejected", "reject") if i < 2 else ("in_inspection", "pending")
    program("FAC-0103", skus("FAC-0103", "Audio") + skus("FAC-0103", "Small Appliances"), 5, 2.4, 80, 10, 2)
    program("FAC-0102", skus("FAC-0102"), 4, 2.0, 76, 12, 5)
    incident("SKU-103661", "FAC-0103", "Smart-home controller batch failed electrical safety test (insulation resistance)", "critical", "investigating", 62)
    incident("SKU-103668", "FAC-0103", "Smart-home controller batch failed electrical safety test (earth continuity)", "high", "investigating", 41)
    incident("SKU-103675", "FAC-0103", "Smart-home controller batch failed electrical safety test (temperature rise)", "high", "open", 19)

    # ---- 02:21:Q1 supplier QA by style: 5520 poor (zips), 7731 clean, T-4410 so-so, PF-220 / K-1700 poor ------------------
    program("FAC-0002", ["SKU-101897", "SKU-101904", "SKU-101911"], 6, 6.5, 82, 8, 1)
    incident("SKU-101897", "FAC-0002", "Zip puller detachment on size 10 dresses", "medium", "open", 12)
    program("FAC-0042", ["SKU-103157", "SKU-103164", "SKU-103171"], 5, 1.3, 80, 10, 2)
    program("FAC-0072", ["SKU-100637", "SKU-100644", "SKU-100651"], 5, 2.8, 80, 12, 4)
    program("FAC-0027", ["PF-220"], 4, 5.0, 80, 12, 3)
    program("FAC-0027", ["K-1700"], 4, 4.2, 78, 10, 0)
    program("FAC-0081", ["SKU-100301", "SKU-100308", "SKU-100315"], 3, 2.6, 75, 14, 1)

    # ---- 05:42:Q1 earlier pink lots on the old recipe passed (the seven failing lots are in seed/) -------------------------
    for i, (batch, sku, d, grade) in enumerate([("BATCH-POL-PINK-P01", "SKU-100007", 84, 4.0), ("BATCH-POL-PINK-P02", "SKU-100014", 77, 5.0)]):
        lot = new_lot(sku, "FAC-0121", d, qty=1000 + 100 * i, batch=batch)
        ins = add_inspection(lot, "final", 120, 3, d - 4)
        lot["status"], lot["lot_disposition"] = "released", "release"
        n["msr"] += 1
        measurements.append({"measurement_id": f"MSR-{910000 + n['msr']}", "inspection_id": ins["inspection_id"], "lot_id": lot["lot_id"],
                             "measurement_type": "colourfastness_to_rubbing", "actual_value": grade, "spec_value": 4.0,
                             "tolerance_lower": 4.0, "tolerance_upper": 5.0, "unit": "grade", "pass": True, "created_at": ins["inspected_at"]})

    # ---- 05:42:Q4 worst-audited factories: weekly final inspections with a rising defect rate ----------------------------
    for fac, sku_list, (d0, d1, *_rest) in (("FAC-0087", skus("FAC-0087"), SCORECARD_STORY["FAC-0087"]),
                                            ("FAC-0107", skus("FAC-0107"), SCORECARD_STORY["FAC-0107"]),
                                            ("FAC-0137", skus("FAC-0137"), SCORECARD_STORY["FAC-0137"])):
        for k in range(6):
            d = 40 - k * 7
            rate = d0 + (d1 - d0) * (12 - (d // 7)) / 12
            lot = new_lot(sku_list[k % len(sku_list)], fac, d)
            u = r.randint(130, 190)
            fin = add_inspection(lot, "final", u, round(u * rate / 100), max(d - 3, 1))
            lot["status"], lot["lot_disposition"] = ("released", "release") if fin["pass_fail"] == "pass" else ("in_inspection", "pending")

    # ---- 01:8:Q4 quality holds behind the WMS quarantine stock; two earlier hold waves show it recurs ----------------------
    def hold(sku, site, qty, days_ago, status, incident_id, released_after=None):
        n["hld"] += 1
        holds.append({"hold_id": f"HLD-{910000 + n['hld']}", "sku": sku, "lot_id": None, "site_id": site, "qty_held": qty,
                      "hold_reason": f"Inbound stock at {site} held pending QA release after receipt sample check",
                      "status": status, "related_incident_id": incident_id, "created_at": ts(days_ago, 9, r.randint(0, 40)),
                      "released_at": ts(max(days_ago - released_after, 0), 14) if released_after else None,
                      "updated_at": ts(max(days_ago - (released_after or 1), 0), 14)})

    for d, count, rel in ((3, None, None), (63, 7, 12), (130, 6, 9)):
        n["inc"] += 1
        inc_id = f"INC-{910000 + n['inc']}"
        incidents.append({"incident_id": inc_id, "sku": None, "factory_id": None, "lot_id": None,
                          "issue_description": f"Bulk quality hold: inbound stock at DC1 and DC3 held pending QA release after receipt sample check",
                          "severity": "medium", "status": "investigating" if rel is None else "closed",
                          "created_at": ts(d, 8), "updated_at": ts(d - (rel or 1), 16)})
        if rel is None:
            for sku, site, qty in HOLD_WAVE:
                hold(sku, site, qty, d, "active", inc_id)
        else:
            pool = [p for p in products if p["sku"] not in story_skus and p["category"] not in ("Small Appliances",)]
            for p in r.sample(pool, count):
                hold(p["sku"], r.choice(["DC1", "DC3"]), r.randint(300, 1800), d, "released", inc_id, rel)

    # ---- Background: other factories only ----------------------------------------------------------------------------------
    pos = g.master("purchase_orders")
    pol = g.master("po_lines")
    po_by_sku = {}
    for l in pol:
        po_by_sku.setdefault(l["sku"], []).append(l["po_id"])
    po_info = {p["po_id"]: p for p in pos}
    noise_pool = [p for p in products if p["factory_id"] not in story_fac and p["sku"] not in story_skus
                  and p["category"] != "Small Appliances" and p["status"] in ("active", "new")]
    n_noise_inc = 0
    noise_lots = []
    for p in r.sample(noise_pool, 110):
        d = r.randint(5, 85)
        pos_ok = [x for x in po_by_sku.get(p["sku"], []) if po_info[x]["factory_id"] == p["factory_id"]
                  and po_info[x]["status"] in ("shipped", "received", "closed", "confirmed")]
        n["lot"] += 1
        lot = {"lot_id": f"LOT-{n['lot'] + 20000:06d}", "sku": p["sku"], "batch_id": None, "factory_id": p["factory_id"],
               "po_id": r.choice(pos_ok) if pos_ok else None, "qty_produced": r.randint(300, 2500),
               "produced_at": as_of - timedelta(days=d), "status": "in_inspection", "lot_disposition": "pending",
               "created_at": ts(d, 8), "updated_at": ts(max(d - 6, 0), 10)}
        lots.append(lot)
        noise_lots.append(lot)
        for itype, off in (("inline", 1), ("final", 3)):
            if itype == "final" and r.random() < 0.12:
                continue
            units = r.randint(50, 200)
            pct = max(0.0, r.gauss(2.0, 1.6))
            n["ins"] += 1
            defects = int(units * pct / 100)
            res = "pass" if 100.0 * defects / units <= 3.0 else ("conditional" if 100.0 * defects / units <= 5.5 else "fail")
            if res != "pass" and itype == "final" and r.random() < 0.5:
                res = "fail"
            inspections.append({"inspection_id": f"INS-{n['ins'] + 20000:06d}", "lot_id": lot["lot_id"], "factory_id": lot["factory_id"],
                                "inspection_type": itype, "units_inspected": units, "defects_found": defects, "pass_fail": res,
                                "scheduled_at": ts(max(d - off, 1) + 1, 9), "inspected_at": ts(max(d - off, 1), 13, r.randint(0, 59)),
                                "created_at": ts(max(d - off, 1), 14), "notes": None})
            if itype == "final":
                lot["status"], lot["lot_disposition"] = {"pass": ("released", "release"), "conditional": ("reworked", "rework"),
                                                         "fail": ("rejected", "reject")}[res] if d > 14 else ("in_inspection", "pending")
    issue_types = ["Defect rate above AQL at final inspection", "Colour shade variation between batches", "Seam strength below requirement",
                   "Measurements out of tolerance", "Visible staining on finished goods", "Packaging carton damaged on receipt",
                   "Label placement incorrect", "Shrinkage beyond specification after wash"]
    fails = [i for i in inspections if i["inspection_id"].startswith("INS-02") and i["pass_fail"] == "fail"]
    for ins in r.sample(fails, min(len(fails), 14)):
        lot = next(l for l in noise_lots if l["lot_id"] == ins["lot_id"])
        n_noise_inc += 1
        created = ins["inspected_at"]
        incidents.append({"incident_id": f"INC-{n_noise_inc + 20000:06d}", "sku": lot["sku"], "factory_id": lot["factory_id"],
                          "lot_id": lot["lot_id"], "issue_description": r.choice(issue_types),
                          "severity": r.choices(["low", "medium", "high"], [30, 55, 15])[0],
                          "status": r.choices(["open", "investigating", "resolved", "closed"], [20, 25, 25, 30])[0],
                          "created_at": created, "updated_at": created + timedelta(days=r.randint(1, 7))})
    noise_inc = [i for i in incidents if i["incident_id"].startswith("INC-02")]
    for k, inc in enumerate(noise_inc):
        if k % 3 == 0:  # background holds are historic only (released), so story holds are the only active ones
            hold(inc["sku"], r.choice(["DC1", "DC3", "DC4"]), r.randint(40, 400), (as_of - inc["created_at"].date()).days, "released",
                 inc["incident_id"], r.randint(2, 10))
            holds[-1]["lot_id"] = inc["lot_id"]
            holds[-1]["hold_reason"] = f"Quality hold pending investigation: {inc['issue_description']}"
        if k % 4 == 0:
            inv = len(investigations) + 1
            investigations.append({"investigation_id": f"INV-{inv + 20000:06d}", "related_incident_id": inc["incident_id"], "sku": inc["sku"],
                                   "supplier_id": factories[inc["factory_id"]]["supplier_id"],
                                   "scope": f"Root cause of: {inc['issue_description']}", "status": r.choice(["open", "in_progress", "closed"]),
                                   "findings": r.choice(["Root cause analysis in progress", "Process variation at supplier factory"]),
                                   "created_at": inc["created_at"], "updated_at": inc["created_at"] + timedelta(days=r.randint(2, 12))})
        if k % 5 == 0:
            cid = len(cars) + 1
            sent = r.random() < 0.8
            cars.append({"car_id": f"CAR-{cid + 20000:06d}", "supplier_id": factories[inc["factory_id"]]["supplier_id"], "factory_id": inc["factory_id"],
                         "sku": inc["sku"], "issue_description": inc["issue_description"],
                         "requested_action": r.choice(["Audit process controls and submit corrective measures", "Increase inspection frequency until trend reverses",
                                                       "Provide material test certificates and root cause analysis"]),
                         "status": r.choice(["sent", "acknowledged", "in_progress", "closed"]) if sent else "draft",
                         "created_at": inc["created_at"], "sent_on": inc["created_at"] + timedelta(days=2) if sent else None,
                         "due_date": (inc["created_at"] + timedelta(days=16)).date(), "updated_at": inc["updated_at"]})

    # ---- Factory scorecards (weekly, current week included) ------------------------------------------------------------------
    weeks = g.weeks(12) + [as_of - timedelta(days=as_of.weekday())]
    sc_n = 0
    for fid, f in factories.items():
        if f["status"] == "delisted":
            continue
        if fid in SCORECARD_STORY:
            d0, d1, c0, c1, o0, o1 = SCORECARD_STORY[fid]
        else:
            base = r.uniform(0.9, 3.4)
            d0, d1 = base, base + r.uniform(-0.4, 0.4)
            c0 = c1 = 1 if r.random() < 0.07 else 0
            o0 = r.uniform(84, 97)
            o1 = o0 + r.uniform(-3, 3)
        for i, wk in enumerate(weeks):
            t = i / (len(weeks) - 1)
            defect = max(0.2, d0 + (d1 - d0) * t + r.gauss(0, 0.25))
            crit = round(c0 + (c1 - c0) * t) if fid in SCORECARD_STORY and c1 != c0 else (c0 if r.random() > 0.15 else 0)
            otd = min(99.5, max(55, o0 + (o1 - o0) * t + r.gauss(0, 1.2)))
            units = r.randint(220, 640)
            found = round(units * defect / 100)
            defect_pct = round(100.0 * found / units, 1)
            sc_n += 1
            scorecards.append({
                "scorecard_id": f"SCD-{sc_n:06d}", "factory_id": fid, "period": wk, "total_units_inspected": units,
                "defects_found": found, "defect_rate_pct": defect_pct, "pass_rate_pct": round(max(40.0, 100 - 6.5 * defect_pct), 1),
                "critical_defects": crit, "on_time_delivery_pct": round(otd, 1),
                "risk_score": round(min(100.0, 6 * defect_pct + 9 * crit + 0.3 * (100 - otd)), 1),
                "created_at": datetime.combine(wk, datetime.min.time()) + timedelta(days=7, hours=8),
            })

    # ---- Pack damage by week (store / ecommerce) ------------------------------------------------------------------------------
    dmg_n = 0

    def damage(sku, pack, channel, wk, shipped, rate, dtype):
        nonlocal dmg_n
        dmg_n += 1
        damaged = round(shipped * rate / 100)
        pack_damage.append({"damage_id": f"DMG-{dmg_n + 100000}", "sku": sku, "pack_type": pack, "channel": channel, "period": wk,
                            "units_shipped": shipped, "units_damaged": damaged,
                            "damage_rate_pct": round(100.0 * damaged / shipped, 2), "damage_type": dtype,
                            "created_at": datetime.combine(wk, datetime.min.time()) + timedelta(days=7, hours=8)})

    dweeks = g.weeks(12)
    # 04:40:Q1 small-appliance packaging trial: corrugated (current) 2.0%, moulded pulp 1.5%, recycled plastic 3.0%
    for sku in ("K-1700", "SKU-100532", "SKU-100539", "SKU-100546"):
        for i, wk in enumerate(dweeks):
            for pack, ship, rate, dtype in (("corrugated", r.randint(850, 1200), 2.0, "crushed"),
                                            ("moulded_pulp", r.randint(160, 240), 1.5, "cracked"),
                                            ("recycled_plastic", r.randint(200, 300), 3.0, "punctured")):
                damage(sku, pack, "store", wk, ship, max(0.2, rate + MULT[(i + len(sku)) % 7] - 1.0 + r.gauss(0, 0.25)), dtype)
    # 04:40:Q6 e-commerce parcels: poly mailers worst, rigid boxes best
    for skus_, pack, rate, dtype, ship in ((["SKU-102548", "SKU-102555", "SKU-103808"], "polybag", 6.8, "torn", (700, 1100)),
                                           (["SKU-104795", "SKU-104802", "SKU-100994"], "carton", 2.1, "crushed", (900, 1400)),
                                           (["SKU-100259", "SKU-100266"], "padded_mailer", 3.4, "leaking", (500, 800)),
                                           (["SKU-101414", "SKU-101421"], "rigid_box", 0.5, "dented", (300, 500))):
        for sku in skus_:
            for i, wk in enumerate(dweeks):
                damage(sku, pack, "ecommerce", wk, r.randint(*ship), max(0.1, rate + (MULT[(i + len(sku) + 2) % 7] - 1.0) * 2 + r.gauss(0, 0.3)), dtype)
    # background store-channel damage on other products
    for p in r.sample([p for p in noise_pool if p["category"] not in ("Drinkware",)], 30):
        pack = p["pack_type"]
        base = {"polybag": 4.5, "carton": 2.0, "hanging": 2.8}.get(pack, 2.0)
        for wk in dweeks:
            damage(p["sku"], pack, "store", wk, r.randint(200, 1500), max(0.1, base + r.gauss(0, 1.0)), r.choice(["crushed", "torn", "water_damaged"]))

    # ---- QA review requests (background, styles with a story excluded) -------------------------------------------------------
    styles = sorted({p["style_id"] for p in noise_pool} - STYLES_WITH_REVIEWS)
    for k, style in enumerate(r.sample(styles, 6)):
        reviews.append({"review_id": f"REV-{k + 1 + 20000:06d}", "style_id": style, "review_type": r.choice(["fit", "durability", "appearance"]),
                        "status": r.choice(["open", "in_progress", "closed"]), "reason": "Routine quality review",
                        "findings": r.choice(["Review in progress", "No significant quality issues detected"]),
                        "created_at": ts(r.randint(5, 40), 10), "updated_at": ts(r.randint(0, 4), 10)})

    # ---- Measurements for a sample of background inspections --------------------------------------------------------------------
    sample = [i for i in inspections if i["inspection_id"].startswith("INS-02") and i["defects_found"] > 0]
    for ins in r.sample(sample, min(len(sample), 25)):
        mtype = r.choice(["chest_width", "inseam", "weight", "shrinkage", "length"])
        spec = round(r.uniform(40, 120), 1)
        tol = round(spec * 0.04, 1)
        actual = round(spec + r.gauss(0, tol * 0.7), 1)
        n["msr"] += 1
        measurements.append({"measurement_id": f"MSR-{n['msr'] + 20000:06d}", "inspection_id": ins["inspection_id"], "lot_id": ins["lot_id"],
                             "measurement_type": mtype, "actual_value": actual, "spec_value": spec, "tolerance_lower": round(spec - tol, 1),
                             "tolerance_upper": round(spec + tol, 1), "unit": "cm" if mtype != "weight" else "g",
                             "pass": abs(actual - spec) <= tol, "created_at": ins["inspected_at"]})

    return {
        "production_lots": lots,
        "quality_inspections": inspections,
        "inspection_measurements": measurements,
        "quality_incidents": incidents,
        "quality_holds": holds,
        "quality_investigations": investigations,
        "supplier_corrective_actions": cars,
        "supplier_notifications": [],
        "factory_quality_scorecards": scorecards,
        "pack_damage_tracking": pack_damage,
        "quality_reviews": reviews,
    }
